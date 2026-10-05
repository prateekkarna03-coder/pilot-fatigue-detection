import mediapipe as mp
import numpy as np
import cv2
import os
import urllib.request
import logging
from typing import Optional
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from .types import Point3D, FaceLandmarks

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

class MediaPipeFaceLandmarker:
    def __init__(self, 
                 model_path: str = "models/face_landmarker.task",
                 min_detection_confidence: float = 0.5, 
                 min_presence_confidence: float = 0.5):
        
        self.model_path = model_path
        self._ensure_model_exists()

        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=min_detection_confidence,
            min_face_presence_confidence=min_presence_confidence
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)

    def _ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            logging.info(f"Downloading MediaPipe model to {self.model_path}...")
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            try:
                urllib.request.urlretrieve(MODEL_URL, self.model_path)
                logging.info("Download complete.")
            except Exception as e:
                logging.error(f"Failed to download MediaPipe model: {e}")
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def process(self, frame: np.ndarray) -> Optional[FaceLandmarks]:
        # Convert BGR to RGB as required by MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        results = self.landmarker.detect(mp_image)
        
        if not results.face_landmarks:
            return None
            
        landmarks = results.face_landmarks[0]
        points = [Point3D(x=lm.x, y=lm.y, z=lm.z) for lm in landmarks]
        
        return FaceLandmarks(points=points)

    def close(self):
        """Release MediaPipe resources"""
        if hasattr(self, 'landmarker') and self.landmarker is not None:
            self.landmarker.close()
