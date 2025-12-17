import sys
import os
import time

# Ensure src is in path
sys.path.append(os.getcwd())

from src.audio.recorder import AudioRecorder
import rust_core

def main():
    print("=== Rust Feature Verification ===")
    
    # 1. Device List
    print("\n1. Listing Devices (Rust)...")
    try:
        devices = rust_core.get_input_devices()
        print(f"Found {len(devices)} devices:")
        for name, idx in devices:
            print(f"  [{idx}] {name}")
    except Exception as e:
        print(f"FAILED to list devices: {e}")
        return

    # 2. Recording with VAD Check
    print("\n2. Testing Recording & VAD...")
    rec = AudioRecorder()
    
    # Ensure we have thresholds
    vad_energy = 0.005
    vad_peak = 0.02
    min_dur = 2.0
    
    print("Starting recording (3 seconds)... Please make some noise or stay silent.")
    try:
        rec.start(max_seconds=5)
        print(f"Sample Rate: {rec.sample_rate} Hz (Detected by Rust)")
    except Exception as e:
        print(f"Failed to start: {e}")
        return

    time.sleep(3)
    
    stats = rec.get_stats()
    print(f"Stats: {stats}")
    
    is_silent = rec.is_silence(energy_threshold=vad_energy, peak_threshold=vad_peak, min_duration=min_dur)
    print(f"Is Silence? {is_silent} (Thresholds: E={vad_energy}, P={vad_peak}, D={min_dur})")
    
    path = rec.stop()
    print(f"Recording saved at: {path}")
    
    if path and os.path.exists(path):
        os.remove(path)
        print("File cleaned up.")
    
    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    main()
