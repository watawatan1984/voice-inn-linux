use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use hound::WavWriter;
use parking_lot::Mutex;
use std::sync::Arc;
use std::sync::atomic::{AtomicBool, Ordering};
use std::thread;

pub fn get_input_devices_list() -> Result<Vec<(String, u32)>, String> {
    let host = cpal::default_host();
    let devices = host.input_devices().map_err(|e| e.to_string())?;
    
    let mut list = Vec::new();
    // cpal doesn't guarantee index stability across runs easily without persistent handle,
    // but for simple UI selection, we rely on iteration order assuming it matches between get and open calls
    // if performed in short succession.
    // Ideally we should return name and let caller match by name, but duplicate names exist.
    // We will return (Name, Index) tuple.
    for (index, device) in devices.enumerate() {
        if let Ok(name) = device.name() {
             list.push((name, index as u32));
        }
    }
    Ok(list)
}

/// 録音中に保持する統計情報
#[derive(Clone, Default)]
pub struct AudioStats {
    pub peak: f32,
    pub rms_sum: f32,
    pub rms_count: usize,
    pub samples_written: usize,
}

/// 録音状態を管理する構造体
pub struct RecorderState {
    pub writer: Option<WavWriter<std::io::BufWriter<std::fs::File>>>,
    pub stats: AudioStats,
}

#[derive(Clone, Copy)]
pub struct VadConfig {
    pub energy_threshold: f32,
    pub peak_threshold: f32,
    pub min_duration: f32,
}

impl Default for VadConfig {
    fn default() -> Self {
        Self {
            energy_threshold: 0.005,
            peak_threshold: 0.02,
            min_duration: 0.2,
        }
    }
}

/// メインのレコーダー構造体
pub struct AudioRecorder {
    is_recording: Arc<AtomicBool>,
    state: Arc<Mutex<RecorderState>>,
    // 録音スレッドを停止させるための仕組みが必要だが、
    // cpalのstreamはDrop時に停止するため、Streamを保持する形にする
    stream: Option<cpal::Stream>,
    sample_rate: u32,
}

impl AudioRecorder {
    pub fn new() -> Self {
        Self {
            is_recording: Arc::new(AtomicBool::new(false)),
            state: Arc::new(Mutex::new(RecorderState {
                writer: None,
                stats: AudioStats::default(),
            })),
            stream: None,
            sample_rate: 0,
        }
    }

    pub fn start(&mut self, file_path: String, input_device_index: Option<usize>) -> Result<u32, String> {
        if self.is_recording.load(Ordering::SeqCst) {
            return Ok(0);
        }

        let host = cpal::default_host();
        
        // デバイス選択 logic
        let device = if let Some(index) = input_device_index {
            let mut devices = host.input_devices().map_err(|e| e.to_string())?;
            devices.nth(index).ok_or_else(|| "Device not found by index".to_string())?
        } else {
            host.default_input_device()
                .ok_or_else(|| "No input device available".to_string())?
        };

        // サポートされている設定から最適なものを探す (48k > 44.1k > 16k)
        let mut supported_configs_range = device.supported_input_configs()
            .map_err(|e| e.to_string())?;
            
        // 優先度順にトライ
        let preferred_rates = [48000, 44100, 16000];
        let mut selected_config = None;
        let mut selected_sample_rate = cpal::SampleRate(44100);

        // Collect configs to avoid consuming iterator if we need multiple passes?
        // supported_input_configs returns iterator.
        // Let's just create a valid config manually if supported.
        
        let supported_configs: Vec<_> = supported_configs_range.collect();

        for &rate in &preferred_rates {
            let sr = cpal::SampleRate(rate);
            for r in &supported_configs {
                if r.min_sample_rate() <= sr && r.max_sample_rate() >= sr {
                    selected_config = Some(r.with_sample_rate(sr));
                    selected_sample_rate = sr;
                    break;
                }
            }
            if selected_config.is_some() { break; }
        }

        // Default fallback if no preferred rate found
        let config = if let Some(c) = selected_config {
             c
        } else {
             // Use default
             device.default_input_config().map_err(|e| e.to_string())?.into()
        };
        
        // 実際のサンプルレートを取得
        let sample_rate = config.sample_rate().0;
        let stream_config: cpal::StreamConfig = config.into();

        // WAV writer の準備
        let spec = hound::WavSpec {
            channels: stream_config.channels,
            sample_rate: sample_rate,
            bits_per_sample: 16,
            sample_format: hound::SampleFormat::Int,
        };
        
        let writer = WavWriter::create(&file_path, spec)
            .map_err(|e| e.to_string())?;

        // 状態のリセット
        {
            let mut state = self.state.lock();
            state.writer = Some(writer);
            state.stats = AudioStats::default();
        }
        
        let state_clone = self.state.clone();
        let err_fn = |err| eprintln!("an error occurred on stream: {}", err);
        
        let stream = device.build_input_stream(
            &stream_config,
            move |data: &[f32], _: &_| {
                process_audio_input(data, &state_clone);
            },
            err_fn,
            None 
        ).map_err(|e| e.to_string())?;

        stream.play().map_err(|e| e.to_string())?;
        
        self.stream = Some(stream);
        self.sample_rate = sample_rate;
        self.is_recording.store(true, Ordering::SeqCst);
        
        Ok(sample_rate)
    }

    pub fn stop(&mut self) {
        if !self.is_recording.load(Ordering::SeqCst) {
            return;
        }
        
        // StreamをDropすることで停止
        self.stream = None;
        self.is_recording.store(false, Ordering::SeqCst);
        
        // Writerをフラッシュして閉じる
        let mut state = self.state.lock();
        if let Some(w) = state.writer.take() {
            let _ = w.finalize();
        }
    }
    
    pub fn get_stats(&self) -> (f32, f32, f32) {
        let state = self.state.lock();
        let s = &state.stats;
        
        let mut avg_rms = 0.0;
        if s.rms_count > 0 {
            avg_rms = (s.rms_sum / s.rms_count as f32).sqrt();
        }
        
        // duration (samples / sample_rate) は外からsample_rateを知る必要があるので
        // ここでは samples などを返すか、呼び出し側で管理するか
        // とりあえず samples_written を返す
        (s.peak, avg_rms, s.samples_written as f32) // samples as float
    }

    pub fn is_silence(&self, config: &VadConfig) -> bool {
        let state = self.state.lock();
        let s = &state.stats;
        
        let mut avg_rms = 0.0;
        if s.rms_count > 0 {
            avg_rms = (s.rms_sum / s.rms_count as f32).sqrt();
        }
        
        let duration = if self.sample_rate > 0 {
            s.samples_written as f32 / self.sample_rate as f32
        } else {
            0.0
        };

        let too_short = duration < config.min_duration;
        let is_quiet = s.peak < config.peak_threshold && avg_rms < config.energy_threshold;
        
        too_short || is_quiet
    }
}

fn process_audio_input(data: &[f32], state: &Arc<Mutex<RecorderState>>) {
    if data.is_empty() { return; }
    
    // RMSとPeakの計算
    let mut max_val = 0.0f32;
    let mut sum_sq = 0.0f32;
    
    for &sample in data {
        let abs_val = sample.abs();
        if abs_val > max_val {
            max_val = abs_val;
        }
        sum_sq += sample * sample;
    }
    
    // PCM (i16) への変換準備
    let pcm_samples: Vec<i16> = data.iter()
        .map(|&s| endpoint_scale(s))
        .collect();

    let mut state_guard = state.lock();
    
    // 統計更新
    if max_val > state_guard.stats.peak {
        state_guard.stats.peak = max_val;
    }
    state_guard.stats.rms_sum += sum_sq;
    state_guard.stats.rms_count += data.len();
    state_guard.stats.samples_written += data.len();
    
    // 書き出し
    if let Some(writer) = &mut state_guard.writer {
        for s in pcm_samples {
            let _ = writer.write_sample(s);
        }
    }
}

fn endpoint_scale(sample: f32) -> i16 {
    let s = sample.clamp(-1.0, 1.0);
    if s >= 0.0 {
        (s * 32767.0) as i16
    } else {
        (s * 32768.0) as i16
    }
}
