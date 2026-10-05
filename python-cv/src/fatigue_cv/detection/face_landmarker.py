import mediapipe as mp
import numpy as np
from typing import Optional
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from .types import Point3D, FaceLandmarks

class MediaPipeFaceLandmarker:
    def __init__(self, min_detection_confidence: float = 0.5, min_presence_confidence: float = 0.5):
        # We use the old mediapipe FaceMesh API or the new Tasks API.
        # Given limitations of downloading models in real-time, we'll use the legacy solutions API which bundles models for ease of use in Step 5A.
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_presence_confidence
        )

    def process(self, frame: np.ndarray) -> Optional[FaceLandmarks]:
        # Convert BGR to RGB
        # MediaPipe requires RGB
        # We won't convert here if we assume it's done outside, but let's do it safely.
        # Actually cv2.cvtColor requires cv2, let's just assume BGR input.
        import cv2
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # To improve performance, mark image as not writeable
        rgb_frame.flags.writeable = False
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None
            
        landmarks = results.multi_face_landmarks[0]
        points = [Point3D(x=lm.x, y=lm.y, z=lm.z) for lm in landmarks.landmark]
        
        return FaceLandmarks(points=points)
