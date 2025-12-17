class SimpleVAD:
    def __init__(self, energy_threshold=0.005, peak_threshold=0.02, min_duration=0.2):
        self.energy_threshold = energy_threshold
        self.peak_threshold = peak_threshold
        self.min_duration = min_duration

    def is_silence(self, stats):
        # stats from recorder
        peak = stats.get("peak", 0.0)
        avg_rms = stats.get("avg_rms", 0.0)
        duration = stats.get("duration", 0.0)
        
        too_short = duration < self.min_duration
        is_quiet = (peak < self.peak_threshold and avg_rms < self.energy_threshold)
        
        return too_short or is_quiet
