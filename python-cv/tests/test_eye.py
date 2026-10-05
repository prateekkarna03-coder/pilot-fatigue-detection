import pytest
from fatigue_cv.features.eye import calculate_ear
from fatigue_cv.detection.types import FaceLandmarks, Point3D

def _generate_synthetic_points(x_offset=0.0):
    points = [Point3D(0.0, 0.0, 0.0) for _ in range(478)]
    # Left eye mapping
    # LEFT_EYE = [362, 385, 387, 263, 373, 380]
    points[362] = Point3D(0.1 + x_offset, 0.5, 0.0) # p1
    points[385] = Point3D(0.15 + x_offset, 0.45, 0.0) # p2
    points[387] = Point3D(0.2 + x_offset, 0.45, 0.0) # p3
    points[263] = Point3D(0.25 + x_offset, 0.5, 0.0) # p4
    points[373] = Point3D(0.2 + x_offset, 0.55, 0.0) # p5
    points[380] = Point3D(0.15 + x_offset, 0.55, 0.0) # p6
    return points

def test_calculate_ear_closed():
    points = _generate_synthetic_points()
    # Close both eyes by making vertical diff 0
    # Left
    points[385].y = 0.5
    points[387].y = 0.5
    points[373].y = 0.5
    points[380].y = 0.5
    
    # Right
    # RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    
    points[33] = Point3D(0.8, 0.5, 0.0)
    points[160] = Point3D(0.75, 0.5, 0.0)
    points[158] = Point3D(0.7, 0.5, 0.0)
    points[133] = Point3D(0.65, 0.5, 0.0)
    points[153] = Point3D(0.7, 0.5, 0.0)
    points[144] = Point3D(0.75, 0.5, 0.0)
    
    landmarks = FaceLandmarks(points=points)
    ear = calculate_ear(landmarks)
    assert pytest.approx(ear, 0.001) == 0.0

def test_calculate_ear_open():
    points = _generate_synthetic_points()
    # Right eye open
    points[33]  = Point3D(0.8, 0.5, 0.0)
    points[160] = Point3D(0.75, 0.45, 0.0)
    points[158] = Point3D(0.7, 0.45, 0.0)
    points[133] = Point3D(0.65, 0.5, 0.0)
    points[153] = Point3D(0.7, 0.55, 0.0)
    points[144] = Point3D(0.75, 0.55, 0.0)
    
    landmarks = FaceLandmarks(points=points)
    ear = calculate_ear(landmarks)
    # v1 = 0.1, v2 = 0.1, h = 0.15 -> ear = 0.2 / 0.3 = 0.666 per eye
    assert ear > 0.5

def test_calculate_ear_no_landmarks():
    assert calculate_ear(None) == 0.0
    assert calculate_ear(FaceLandmarks(points=[])) == 0.0
