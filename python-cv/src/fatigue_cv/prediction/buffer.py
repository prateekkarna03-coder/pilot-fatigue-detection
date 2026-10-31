import statistics
from collections import deque
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.types import TemporalMetrics
from fatigue_cv.prediction.types import PredictionInput

class PredictionBuffer:
    """
    Maintains a rolling temporal window (e.g., 10 seconds) of features
    and safely aggregates them into a PredictionInput vector for the ML model.
    """
    def __init__(self, window_duration: float = 10.0):
        self.window_duration = window_duration
        self._buffer = deque()
        
    def add(self, timestamp: float, features: FeaturesResult, metrics: TemporalMetrics):
        """
        Adds a single frame's raw and temporal metrics to the buffer.
        If features is None (no face), it still records the timestamp to maintain temporal width,
        but stores None for physiological features.
        """
        self._buffer.append({
            "timestamp": timestamp,
            "features": features,
            "metrics": metrics
        })
        self._evict_old(timestamp)
        
    def _evict_old(self, current_timestamp: float):
        """Removes elements that fall outside the rolling window duration."""
        cutoff_time = current_timestamp - self.window_duration
        while self._buffer and self._buffer[0]["timestamp"] < cutoff_time:
            self._buffer.popleft()
            
    def get_aggregated_input(self) -> PredictionInput:
        """
        Calculates means, medians, maxs, and stds across the current buffer.
        Returns a PredictionInput strictly conforming to the 15 ML features.
        Raises ValueError if the window is completely empty of valid faces.
        """
        valid_items = [b for b in self._buffer if b["features"] is not None]
        
        if not valid_items:
            raise ValueError("Buffer contains no valid face tracking data to aggregate.")
            
        ears = [b["features"].ear for b in valid_items]
        mars = [b["features"].mar for b in valid_items]
        pitches = [b["features"].pitch for b in valid_items]
        yaws = [b["features"].yaw for b in valid_items]
        rolls = [b["features"].roll for b in valid_items]
        
        # Temporal metrics are expected to persist even without face features, 
        # but we tie them to valid frames for aggregation consistency.
        blink_rates = [b["metrics"].blink_rate_per_minute for b in valid_items]
        yawn_rates = [b["metrics"].yawn_rate_per_minute for b in valid_items]
        closures = [b["metrics"].current_closure_duration for b in valid_items]
        
        def safe_mean(vals): return statistics.mean(vals)
        def safe_median(vals): return statistics.median(vals)
        def safe_max(vals): return max(vals)
        def safe_min(vals): return min(vals)
        def safe_std(vals): return statistics.stdev(vals) if len(vals) > 1 else 0.0
        
        return PredictionInput(
            ear_mean=safe_mean(ears),
            ear_min=safe_min(ears),
            mar_mean=safe_mean(mars),
            mar_max=safe_max(mars),
            blink_rate_mean=safe_mean(blink_rates),
            blink_rate_max=safe_max(blink_rates),
            yawn_rate_mean=safe_mean(yawn_rates),
            yawn_rate_max=safe_max(yawn_rates),
            closure_duration_max=safe_max(closures),
            pitch_median=safe_median(pitches),
            pitch_std=safe_std(pitches),
            yaw_median=safe_median(yaws),
            yaw_std=safe_std(yaws),
            roll_median=safe_median(rolls),
            roll_std=safe_std(rolls)
        )
