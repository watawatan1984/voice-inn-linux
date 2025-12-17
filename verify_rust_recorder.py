import sys
import os
import time

# Ensure src is in path
sys.path.append(os.getcwd())

from src.audio.recorder import AudioRecorder

def main():
    print("Initializing AudioRecorder...")
    rec = AudioRecorder()
    
    print("Starting recording (2 seconds)...")
    try:
        rec.start(max_seconds=5)
    except Exception as e:
        print(f"Failed to start: {e}")
        return

    time.sleep(2)
    
    print("Getting stats...")
    stats = rec.get_stats()
    print(f"Stats: {stats}")
    
    # Check if stats are somewhat valid
    if stats['duration'] <= 0:
        print("Warning: Duration is 0 or less.")
    
    print("Stopping recording...")
    path = rec.stop()
    print(f"Recording saved at: {path}")
    
    if path and os.path.exists(path):
        size = os.path.getsize(path)
        print(f"File size: {size} bytes")
        os.remove(path)
        if size > 44: # WAV header size
            print("SUCCESS: File verification passed.")
        else:
            print("FAILURE: File is too small (header only?).")
    else:
        print("FAILURE: File not found.")

if __name__ == "__main__":
    main()
