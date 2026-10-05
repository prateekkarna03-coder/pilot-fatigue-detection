from dataclasses import dataclass

@dataclass
class CameraSettings:
    device_id: int = 0
    width: int = 640
    height: int = 480

@dataclass
class DetectionSettings:
    min_face_detection_confidence: float = 0.5
    min_face_presence_confidence: float = 0.5

@dataclass
class AppSettings:
    camera: CameraSettings = CameraSettings()
    detection: DetectionSettings = DetectionSettings()
