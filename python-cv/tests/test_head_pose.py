import pytest
from fatigue_cv.features.head_pose import calculate_head_pose
from fatigue_cv.detection.types import FaceLandmarks, Point3D

def test_calculate_head_pose_straight():
    points = [Point3D(0.0, 0.0, 0.0) for _ in range(478)]
    # Scale synthetic coordinates perfectly proportionately to FACE_3D for 0-tilt solve
    points[1] = Point3D(0.5, 0.5, 0.0) # Nose
    points[152] = Point3D(0.5, 0.83, 0.0) # Chin (match 330)
    points[33] = Point3D(0.275, 0.33, 0.0) # Subject Right eye
    points[263] = Point3D(0.725, 0.33, 0.0) # Subject Left eye
    points[61] = Point3D(0.35, 0.65, 0.0) # Subject Right mouth
    points[291] = Point3D(0.65, 0.65, 0.0) # Subject Left mouth
    
    landmarks = FaceLandmarks(points=points)
    pitch, yaw, roll = calculate_head_pose(landmarks)
    
    # Should be near zero for a straight face, no flipped axis inversions!
    assert abs(pitch) < 15.0
    assert abs(yaw) < 15.0
    assert abs(roll) < 15.0

def test_calculate_head_pose_no_landmarks():
    assert calculate_head_pose(None) == (0.0, 0.0, 0.0)
    assert calculate_head_pose(FaceLandmarks(points=[])) == (0.0, 0.0, 0.0)
