import time
from typing import Dict, Any
from .config.settings import AppSettings
from .camera.capture import CameraStream
from .detection.face_landmarker import MediaPipeFaceLandmarker
from .features import eye, mouth, head_pose
from .transport.stdout import StdoutTransport

class App:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.camera = CameraStream(
            device_id=settings.camera.device_id,
            width=settings.camera.width,
            height=settings.camera.height
        )
        self.detector = MediaPipeFaceLandmarker(
            min_detection_confidence=settings.detection.min_face_detection_confidence,
            min_presence_confidence=settings.detection.min_face_presence_confidence
        )
        self.transport = StdoutTransport()

    def run(self):
        if not self.camera.open():
            self.transport.send({"error": "Failed to open camera stream."})
            return

        try:
            # For testing the pipeline briefly rather than infinite loop
            # Replace loop condition for real usage
            # while True:
            for _ in range(5):
                frame = self.camera.read_frame()
                if frame is None:
                    continue

                landmarks = self.detector.process(frame)
                payload: Dict[str, Any] = {"timestamp": time.time(), "face_found": False}
                
                if landmarks:
                    payload["face_found"] = True
                    payload["ear"] = eye.calculate_ear(landmarks)
                    payload["mar"] = mouth.calculate_mar(landmarks)
                    payload["head_pose"] = head_pose.calculate_head_pose(landmarks)

                self.transport.send(payload)
                time.sleep(0.03)

        finally:
            self.camera.close()

if __name__ == "__main__":
    app_instance = App(AppSettings())
    app_instance.run()
