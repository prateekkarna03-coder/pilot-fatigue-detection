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
    ear_threshold: float = 0.25 # below is closed
    mar_threshold: float = 0.5  # above is yawning
    prolonged_closure_time: float = 3.0 # seconds
    window_size: float = 60.0 # seconds to track history
    yawn_min_duration: float = 2.0 # minimum duration to be a yawn
    yawn_cooldown: float = 1.0 # time after yawn to ignore new ones

@dataclass
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    detection: DetectionSettings = field(default_factory=DetectionSettings)
    temporal: TemporalSettings = field(default_factory=TemporalSettings)
