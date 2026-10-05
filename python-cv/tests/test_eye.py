import pytest
from fatigue_cv.detection.types import FaceLandmarks, Point3D
from fatigue_cv.features.eye import calculate_ear

def test_calculate_ear():
    # Stub test
    landmarks = FaceLandmarks(points=[Point3D(0,0,0)])
    ear = calculate_ear(landmarks)
    assert ear == 0.25
