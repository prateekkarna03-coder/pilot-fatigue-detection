import pytest
from fatigue_cv.detection.types import FaceLandmarks, Point3D
from fatigue_cv.features.head_pose import calculate_head_pose

def test_calculate_head_pose():
    # Stub test
    landmarks = FaceLandmarks(points=[Point3D(0,0,0)])
    pose = calculate_head_pose(landmarks)
    assert pose == (0.0, 0.0, 0.0)
