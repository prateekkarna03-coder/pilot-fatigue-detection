from typing import Optional
import collections
from ..features.types import FeaturesResult
from .types import TemporalMetrics
from ..config.settings import TemporalSettings

class TemporalTracker:
    def __init__(self, settings: TemporalSettings):
        self.settings = settings
        
        self.eyes_closed = False
        self.eyes_closed_start_time = 0.0
        self.total_blinks = 0
        self.blink_timestamps: collections.deque[float] = collections.deque()
        
        self.mouth_open = False
        self.yawn_start_time = 0.0
        self.yawn_candidate_valid = False
        self.last_yawn_end_time = 0.0
        self.total_yawns = 0
        self.yawn_timestamps: collections.deque[float] = collections.deque()

    def update(self, features: Optional[FeaturesResult], current_time: float) -> TemporalMetrics:
        # Clean up old timestamps outside window
        while self.blink_timestamps and (current_time - self.blink_timestamps[0] > self.settings.window_size):
            self.blink_timestamps.popleft()
        while self.yawn_timestamps and (current_time - self.yawn_timestamps[0] > self.settings.window_size):
            self.yawn_timestamps.popleft()

        if not features:
            self.eyes_closed = False
            self.eyes_closed_start_time = 0.0
            
            self.mouth_open = False
            self.yawn_start_time = 0.0
            self.yawn_candidate_valid = False
            
            return TemporalMetrics(
                total_blinks=self.total_blinks,
                blink_rate_per_minute=self._calculate_rate(len(self.blink_timestamps)),
                current_closure_duration=0.0,
                is_prolonged_closure=False,
                
                total_yawns=self.total_yawns,
                yawn_rate_per_minute=self._calculate_rate(len(self.yawn_timestamps)),
                is_yawning=False
            )

        # Eye logic
        is_currently_closed = features.ear < self.settings.ear_threshold
        current_closure_duration = 0.0
        is_prolonged = False

        if is_currently_closed:
            if not self.eyes_closed: # State transition to closed
                self.eyes_closed = True
                self.eyes_closed_start_time = current_time
            else:
                current_closure_duration = current_time - self.eyes_closed_start_time
                if current_closure_duration >= self.settings.prolonged_closure_time:
                    is_prolonged = True
        else:
            if self.eyes_closed: # State transition to open (blink completed)
                self.eyes_closed = False
                self.blink_timestamps.append(current_time)
                self.total_blinks += 1
                self.eyes_closed_start_time = 0.0

        # Mouth logic
        is_currently_yawning = features.mar > self.settings.mar_threshold
        
        if is_currently_yawning:
            if not self.mouth_open:
                if current_time - self.last_yawn_end_time >= self.settings.yawn_cooldown:
                    self.mouth_open = True
                    self.yawn_start_time = current_time
            else:
                if current_time - self.yawn_start_time >= self.settings.yawn_min_duration:
                    self.yawn_candidate_valid = True
        else:
            if self.mouth_open:
                if self.yawn_candidate_valid:
                    self.total_yawns += 1
                    self.yawn_timestamps.append(current_time)
                    self.last_yawn_end_time = current_time
                self.mouth_open = False
                self.yawn_candidate_valid = False

        return TemporalMetrics(
            total_blinks=self.total_blinks,
            blink_rate_per_minute=self._calculate_rate(len(self.blink_timestamps)),
            current_closure_duration=current_closure_duration,
            is_prolonged_closure=is_prolonged,
            
            total_yawns=self.total_yawns,
            yawn_rate_per_minute=self._calculate_rate(len(self.yawn_timestamps)),
            is_yawning=self.yawn_candidate_valid
        )
        
    def _calculate_rate(self, count: int) -> float:
        if self.settings.window_size <= 0:
            return 0.0
        return (count / self.settings.window_size) * 60.0
