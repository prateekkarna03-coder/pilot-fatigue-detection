from ..detection.types import FaceLandmarks
from typing import Tuple

def calculate_head_pose(landmarks: FaceLandmarks) -> Tuple[float, float, float]:
    """Calculate pitch, yaw, roll from landmarks."""
    return (0.0, 0.0, 0.0) # stub return
