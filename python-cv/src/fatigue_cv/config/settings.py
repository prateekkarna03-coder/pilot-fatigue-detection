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

@dataclass
class AppSettings:
    camera: CameraSettings = field(default_factory=CameraSettings)
    detection: DetectionSettings = field(default_factory=DetectionSettings)
