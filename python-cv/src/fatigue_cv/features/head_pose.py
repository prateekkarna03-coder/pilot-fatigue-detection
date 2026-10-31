from ..detection.types import FaceLandmarks
from typing import Tuple
import numpy as np
import cv2

# OpenCV generic 3D face model: +X right, +Y down, +Z forward
FACE_3D = np.array([
    (0.0, 0.0, 0.0),             # Nose tip 1
    (0.0, 330.0, 65.0),          # Chin 152
    (-225.0, -170.0, 135.0),     # Right eye corner 33 (left on image)
    (225.0, -170.0, 135.0),      # Left eye corner 263 (right on image)
    (-150.0, 150.0, 125.0),      # Right mouth corner 61
    (150.0, 150.0, 125.0)        # Left mouth corner 291
], dtype=np.float64)

FACE_INDICES = [1, 152, 33, 263, 61, 291]

def calculate_head_pose(landmarks: FaceLandmarks, img_w: int = 1, img_h: int = 1) -> Tuple[float, float, float]:
    """Calculate pitch, yaw, roll from landmarks."""
    if not landmarks or len(landmarks.points) < 478:
        return (0.0, 0.0, 0.0)
        
    focal_length = float(img_w)
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2.0],
        [0, focal_length, img_h / 2.0],
        [0, 0, 1]
    ], dtype=np.float64)
    
    dist_coeffs = np.zeros((4, 1), dtype=np.float64)
    
    image_points = np.array([
        (landmarks.points[idx].x * img_w, landmarks.points[idx].y * img_h)
        for idx in FACE_INDICES
    ], dtype=np.float64)
    
    success, rotation_vec, _ = cv2.solvePnP(
        FACE_3D, image_points, cam_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    
    if not success:
        return (0.0, 0.0, 0.0)
        
    rmat, _ = cv2.Rodrigues(rotation_vec)
    
    sy = np.sqrt(rmat[0, 0] * rmat[0, 0] + rmat[1, 0] * rmat[1, 0])
    singular = sy < 1e-6
    
    if not singular:
        pitch = float(np.degrees(np.arctan2(rmat[2, 1], rmat[2, 2])))
        yaw = float(np.degrees(np.arctan2(-rmat[2, 0], sy)))
        roll = float(np.degrees(np.arctan2(rmat[1, 0], rmat[0, 0])))
    else:
        pitch = float(np.degrees(np.arctan2(-rmat[1, 2], rmat[1, 1])))
        yaw = float(np.degrees(np.arctan2(-rmat[2, 0], sy)))
        roll = 0.0
        
    return pitch, yaw, roll
