from dataclasses import dataclass, field

@dataclass
class CameraSettings:
    device_id: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30

@dataclass
class DetectionSettings:
    min_face_detection_confidence: float = 0.5
    min_face_presence_confidence: float = 0.5
    model_path: str = "models/face_landmarker.task"

@dataclass
class TemporalSettings:
    ear_drop_ratio: float = 0.75 # ratio of baseline ear to be considered closed
    ear_open_ratio: float = 0.85 # ratio of baseline ear to be considered open
    blink_max_duration: float = 0.6 # seconds, above this is not a blink
    blink_min_duration: float = 0.05 # seconds, below this is noise
    mar_threshold: float = 0.35  # above is yawning
    prolonged_closure_time: float = 3.0 # seconds
    window_size: float = 60.0 # seconds to track history
    yawn_min_duration: float = 2.0 # minimum duration to be a yawn
    yawn_cooldown: float = 1.0 # time after yawn to ignore new ones
    dynamic_baseline_time: float = 10.0 # seconds to track max EAR baseline
    missing_grace_period: float = 0.5 # seconds to retain state without face
    pose_change_threshold: float = 15.0 # degrees of change that invalidates a blink candidate

@dataclass
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    detection: DetectionSettings = field(default_factory=DetectionSettings)
    temporal: TemporalSettings = field(default_factory=TemporalSettings)
    diagnostic_mode: bool = True
    telemetry_interval_seconds: float = 1.0
