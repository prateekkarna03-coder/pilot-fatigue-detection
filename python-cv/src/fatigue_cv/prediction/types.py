from dataclasses import dataclass

@dataclass
class PredictionInput:
    """Input features vector for the fatigue ML model (window-aggregated)."""
    ear_mean: float
    ear_min: float
    mar_mean: float
    mar_max: float
    blink_rate_mean: float
    blink_rate_max: float
    yawn_rate_mean: float
    yawn_rate_max: float
    closure_duration_max: float
    pitch_median: float
    pitch_std: float
    yaw_median: float
    yaw_std: float
    roll_median: float
    roll_std: float

@dataclass
class PredictionOutput:
    """Output typed result from the fatigue ML model."""
    kss_label: int
    fatigue_state: str
    class_probabilities: dict[int, float]
