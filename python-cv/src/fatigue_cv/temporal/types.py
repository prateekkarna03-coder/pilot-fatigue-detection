from dataclasses import dataclass

@dataclass
class TemporalMetrics:
    total_blinks: int
    blink_rate_per_minute: float
    current_closure_duration: float
    is_prolonged_closure: bool
    
    total_yawns: int
    yawn_rate_per_minute: float
    is_yawning: bool
