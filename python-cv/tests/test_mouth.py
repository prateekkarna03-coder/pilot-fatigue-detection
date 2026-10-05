import pytest
from fatigue_cv.features.mouth import calculate_mar
from fatigue_cv.detection.types import FaceLandmarks, Point3D

def _generate_synthetic_points():
    points = [Point3D(0.0, 0.0, 0.0) for _ in range(478)]
    # Horizontal: 61, 291
    # Vertical: 13, 14
    points[61] = Point3D(0.3, 0.7, 0.0)
    points[291] = Point3D(0.7, 0.7, 0.0)
    points[13] = Point3D(0.5, 0.65, 0.0)
    points[14] = Point3D(0.5, 0.75, 0.0)
    return points

def test_calculate_mar_open():
    points = _generate_synthetic_points()
    landmarks = FaceLandmarks(points=points)
    mar = calculate_mar(landmarks)
    # h = 0.4, v = 0.1 => 0.25
    assert pytest.approx(mar, 0.01) == 0.25

def test_calculate_mar_closed():
    points = _generate_synthetic_points()
    points[13] = Point3D(0.5, 0.7, 0.0)
    points[14] = Point3D(0.5, 0.7, 0.0)
    landmarks = FaceLandmarks(points=points)
    mar = calculate_mar(landmarks)
    assert pytest.approx(mar, 0.001) == 0.0

def test_calculate_mar_no_landmarks():
    assert calculate_mar(None) == 0.0
    assert calculate_mar(FaceLandmarks(points=[])) == 0.0
