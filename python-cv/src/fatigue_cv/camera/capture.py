import cv2
from typing import Optional
import numpy as np

class CameraStream:
    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            return False
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        if not self.cap:
            return None
        success, frame = self.cap.read()
        if not success:
            return None
        return frame

    def close(self) -> None:
        if self.cap:
            self.cap.release()
            self.cap = None
