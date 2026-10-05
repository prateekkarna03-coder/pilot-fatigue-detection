import pytest
from fatigue_cv.detection.types import FaceLandmarks, Point3D
from fatigue_cv.features.mouth import calculate_mar

def test_calculate_mar():
    # Stub test
    landmarks = FaceLandmarks(points=[Point3D(0,0,0)])
    mar = calculate_mar(landmarks)
    assert mar == 0.1
