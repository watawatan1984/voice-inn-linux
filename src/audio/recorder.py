import threading
import os
import time
import tempfile
import logging

try:
    from rust_core import PyAudioRecorder
except ImportError:
    # Fallback or error if not compiled
    logging.error("Failed to import rust_core. Make sure to build with maturin.")
    raise

from src.core.config import config_manager
from src.core.const import SAMPLE_RATE

# Assuming Rust uses default device SR which is typically 44100 or 48000 on modern OS?
# For PoC we use hardcoded guessed SR for duration calc if Rust doesn't return it.
# Ideally Rust should return used SR.
# But existing vad.py logic expects duration.
class AudioRecorder:
    def __init__(self):
        self._native_recorder = PyAudioRecorder()
        self._recording_path = None
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self.is_recording = False
        self.on_auto_stop = None
        self.sample_rate = SAMPLE_RATE # Default fallback

    def start(self, max_seconds=60, on_auto_stop=None):
        if self.is_recording:
            return

        self.cleanup()
        self.on_auto_stop = on_auto_stop
        
        # Temp file creation
        # Rust expects a path string
        tf = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        self._recording_path = tf.name
        tf.close()

        input_device = config_manager.settings.get("audio", {}).get("input_device") # Index or Name (Legacy)
        
        # Rust backend expects index (int) or None.
        if isinstance(input_device, str):
            # Legacy config might have string name. Fallback to default.
            # Ideally we should lookup index by name via rust_core.get_input_devices()
            logging.warning("Device name provided in config, but Rust backend expects index. Using default device.")
            input_device = None
        elif not isinstance(input_device, int) and input_device is not None:
             input_device = None
        
        try:
            # Rust returns the actual sample rate used
            sr = self._native_recorder.start(self._recording_path, input_device)
            if sr > 0:
                self.sample_rate = sr
            logging.info(f"Recording started with sample rate: {self.sample_rate}")
            
            self.is_recording = True
            
            # Start monitor thread for auto-stop
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(max_seconds,),
                daemon=True
            )
            self._monitor_thread.start()
            
        except Exception as e:
            logging.error(f"Failed to start recording (Rust): {e}")
            self.cleanup()
            raise RuntimeError(f"Failed to start recording: {e}")

    def _monitor_loop(self, max_seconds):
        start_time = time.time()
        while not self._stop_event.is_set():
            if time.time() - start_time >= max_seconds:
                # Time limit reached
                if self.is_recording:
                    # Notify via callback
                    if self.on_auto_stop:
                        self.on_auto_stop()
                break
            time.sleep(0.1)

    def stop(self):
        if not self.is_recording:
            return None
            
        self.is_recording = False
        self._stop_event.set()
        
        try:
            self._native_recorder.stop()
        except Exception as e:
            logging.error(f"Error calling native stop: {e}")

        if self._monitor_thread and self._monitor_thread.is_alive():
            # Wait a bit? No need, we set event.
            pass
            
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
        try:
            # Rust returns (peak, rms, samples)
            peak, rms, samples = self._native_recorder.get_stats()
            
            # Calculate duration using actual sample rate
            duration = samples / self.sample_rate if self.sample_rate > 0 else 0.0
            
            return {
                "peak": peak,
                "avg_rms": rms,
                "duration": duration
            }
        except Exception:
            return {"peak": 0.0, "avg_rms": 0.0, "duration": 0.0}

    def is_silence(self, energy_threshold=None, peak_threshold=None, min_duration=None):
        """
        Check if the current recording is silent using Rust-side VAD logic.
        If thresholds are not provided, they are loaded from config.
        """
        if energy_threshold is None:
            energy_threshold = config_manager.settings.get("audio", {}).get("vad_energy_threshold", 0.005)
        if peak_threshold is None:
            peak_threshold = config_manager.settings.get("audio", {}).get("vad_peak_threshold", 0.02)
        if min_duration is None:
             min_duration = config_manager.settings.get("audio", {}).get("min_duration", 0.2)

        try:
            return self._native_recorder.is_silence(energy_threshold, peak_threshold, float(min_duration))
        except Exception as e:
            logging.error(f"VAD check failed: {e}")
            return False
