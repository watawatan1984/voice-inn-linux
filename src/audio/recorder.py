import sounddevice as sd
import numpy as np
import wave
import tempfile
import threading
import logging
import os
import shutil

from src.core.config import config_manager
from src.core.utils import deep_merge_dict

SAMPLE_RATE = 16000

def get_candidate_input_samplerates(device, preferred_sr: int):
    cands = []
    def _add(sr):
        try:
            sr_i = int(round(float(sr)))
            if sr_i > 0 and sr_i not in cands:
                cands.append(sr_i)
        except Exception:
            pass

    try:
        info = sd.query_devices(device, kind='input') if device is not None else sd.query_devices(kind='input')
        if isinstance(info, dict):
            _add(info.get('default_samplerate'))
    except Exception:
        pass

    _add(preferred_sr)
    for sr in (48000, 44100, 32000, 24000, 22050, 16000):
        _add(sr)

    if not cands:
        cands = [preferred_sr]
    return cands

def open_input_stream_with_fallback(*, device, channels: int, callback, preferred_sr: int):
    last_err = None
    for sr in get_candidate_input_samplerates(device, preferred_sr):
        try:
            stream = sd.InputStream(samplerate=sr, channels=channels, device=device, callback=callback)
            return stream, int(sr)
        except Exception as e:
            last_err = e
            continue
    raise last_err or RuntimeError("Failed to open input stream")

class AudioRecorder:
    def __init__(self):
        self._recording_path = None
        self._wave_writer = None
        self._recording_lock = threading.Lock()
        self.stream = None
        self.fs = SAMPLE_RATE
        
        # Stats
        self.audio_peak = 0.0
        self.audio_power_sum = 0.0
        self.audio_power_count = 0
        self.frames_written = 0
        self.max_frames = 0
        
        self.is_recording = False
        self.auto_stop_sent = False
        self.on_auto_stop = None # Callback function

    def start(self, max_seconds=60, on_auto_stop=None):
        if self.is_recording:
            return
            
        self.cleanup()
        self.on_auto_stop = on_auto_stop
        
        settings = config_manager.settings.get("audio", {})
        device = settings.get("input_device")
        
        self.fs = SAMPLE_RATE
        self.max_frames = int(self.fs * max_seconds) # Will be updated after stream open if fs changes
        
        self.audio_peak = 0.0
        self.audio_power_sum = 0.0
        self.audio_power_count = 0
        self.frames_written = 0
        self.auto_stop_sent = False
        
        def callback(indata, frames, time, status):
            gain_db = float(config_manager.settings.get("audio", {}).get("input_gain_db", 0.0))
            gain = float(10 ** (gain_db / 20.0))
            
            try:
                with self._recording_lock:
                    w = self._wave_writer
                    if not w:
                        return
                    audio = np.asarray(indata, dtype=np.float32)
                    audio = np.clip(audio * gain, -1.0, 1.0)
                    
                    # Energy calc
                    try:
                        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
                        if peak > self.audio_peak:
                            self.audio_peak = peak
                        ss = float(np.sum(audio * audio))
                        n = int(audio.size)
                        if n > 0:
                            self.audio_power_sum += ss
                            self.audio_power_count += n
                    except Exception:
                        pass
                        
                    pcm = (audio * 32767).astype(np.int16)
                    w.writeframesraw(pcm.tobytes())
                    self.frames_written += int(frames)
                    
                    if self.max_frames and self.frames_written >= self.max_frames and not self.auto_stop_sent:
                        self.auto_stop_sent = True
                        if self.on_auto_stop:
                            # Use a thread-safe flag or expect callback to be safe.
                            # Calling simple lambda which emits signal is safe in Qt if queued.
                            self.on_auto_stop()
            except Exception:
                pass

        try:
            self.stream, sr = open_input_stream_with_fallback(
                device=device,
                channels=1,
                callback=callback,
                preferred_sr=SAMPLE_RATE
            )
            self.fs = int(sr)
            self.max_frames = int(self.fs * max_seconds)
            
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self._recording_path = tmp.name
            tmp.close()
            
            self._wave_writer = wave.open(self._recording_path, "wb")
            self._wave_writer.setnchannels(1)
            self._wave_writer.setsampwidth(2)
            self._wave_writer.setframerate(self.fs)
            
            self.stream.start()
            self.is_recording = True
        except Exception as e:
            logging.error(f"Failed to start recording: {e}")
            self.cleanup()
            raise RuntimeError("Failed to start recording") from e

    def stop(self):
        if not self.is_recording:
            return None
        self.is_recording = False
        
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
            
        with self._recording_lock:
            if self._wave_writer:
                try:
                    self._wave_writer.close()
                except Exception:
                    pass
                self._wave_writer = None
        
        return self._recording_path

    def cleanup(self):
        self.stop()
        if self._recording_path and os.path.exists(self._recording_path):
            try:
                os.remove(self._recording_path)
            except Exception:
                pass
        self._recording_path = None

    def get_stats(self):
        with self._recording_lock:
            peak = self.audio_peak
            s = self.audio_power_sum
            c = self.audio_power_count
            fw = self.frames_written
        
        avg_rms = 0.0
        if c > 0:
            avg_rms = float(np.sqrt(s / float(c)))
        return {
            "peak": peak,
            "avg_rms": avg_rms,
            "duration": fw / self.fs if self.fs else 0
        }
