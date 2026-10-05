import cv2
from typing import Optional
import numpy as np
import logging

class CameraStream:
    def __init__(self, device_id: int = 0, width: int = 640, height: int = 480, fps: int = 30):
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None

    def open(self) -> bool:
        """Initialize the video capture and validate hardware state."""
        self.cap = cv2.VideoCapture(self.device_id)
        if not self.cap.isOpened():
            logging.error(f"Failed to open camera device {self.device_id}")
            self.cap = None
            return False
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from the active capture stream."""
        if self.cap is None:
            return None
            
        success, frame = self.cap.read()
        if not success:
            return None
            
        return frame

    def close(self) -> None:
        """Release hardware resources safely."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
