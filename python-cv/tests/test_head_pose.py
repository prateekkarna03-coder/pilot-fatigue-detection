import pytest
import cv2
import numpy as np
from fatigue_cv.features.head_pose import calculate_head_pose, FACE_INDICES, FACE_3D
from fatigue_cv.detection.types import FaceLandmarks, Point3D

def _simulate_landmarks(pitch_deg: float, yaw_deg: float, roll_deg: float) -> FaceLandmarks:
    """Helper to generate perfectly projected 2D landmarks for a target pose."""
    p = np.radians(pitch_deg)
    y = np.radians(yaw_deg)
    r = np.radians(roll_deg)
    
    # Tait-Bryan Angles (Z-Y-X)
    Rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]], dtype=np.float64)
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]], dtype=np.float64)
    Rz = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]], dtype=np.float64)
    R = Rz @ Ry @ Rx
    
    rvec, _ = cv2.Rodrigues(R)
    tvec = np.array([[0.0], [0.0], [2000.0]], dtype=np.float64)
    
    img_w, img_h = 1, 1
    focal_length = 1.0
    cam_matrix = np.array([
        [focal_length, 0, img_w / 2.0],
        [0, focal_length, img_h / 2.0],
        [0, 0, 1]
    ], dtype=np.float64)
    
    points_2d, _ = cv2.projectPoints(FACE_3D, rvec, tvec, cam_matrix, np.zeros((4, 1), dtype=np.float64))
    
    points = [Point3D(0.0, 0.0, 0.0) for _ in range(478)]
    for i, idx in enumerate(FACE_INDICES):
        points[idx] = Point3D(points_2d[i][0][0], points_2d[i][0][1], 0.0)
        
    return FaceLandmarks(points=points)

def test_calculate_head_pose_straight():
    # Straight face -> near zero angles
    landmarks = _simulate_landmarks(0.0, 0.0, 0.0)
    pitch, yaw, roll = calculate_head_pose(landmarks)
    
    assert abs(pitch) < 1e-4
    assert abs(yaw) < 1e-4
    assert abs(roll) < 1e-4

@pytest.mark.parametrize("target_pitch, target_yaw, target_roll", [
    (30.0, 0.0, 0.0),
    (-30.0, 0.0, 0.0),
    (0.0, -45.0, 0.0),
    (0.0, 45.0, 0.0),
    (0.0, 0.0, 20.0),
    (0.0, 0.0, -20.0),
    (15.0, -20.0, 10.0),
    (-50.0, -24.0, -77.0) # The specific combination observed failing previously
])
def test_calculate_head_pose_rotations(target_pitch, target_yaw, target_roll):
    landmarks = _simulate_landmarks(target_pitch, target_yaw, target_roll)
    pitch, yaw, roll = calculate_head_pose(landmarks)
    
    # Verify angles stay mathematically bounded and produce the expected signs.
    # Note: Because of OpenCV's PnP geometric solving process matching 2D to 3D, 
    # it won't be perfectly zero-error, but the signs and rough magnitudes must correlate.
    # OpenCV's solvePnP might yield an alternative representation if ambiguity exists, 
    # but for small realistic angles <= 50deg it should faithfully reproduce the continuous angle.
    assert np.sign(pitch) == np.sign(target_pitch) or target_pitch == 0.0
    assert np.sign(yaw) == np.sign(target_yaw) or target_yaw == 0.0
    assert np.sign(roll) == np.sign(target_roll) or target_roll == 0.0
    
    # Assert values are strictly properly bounded, never yielding 300+ wrapper angles
    assert -180.0 <= pitch <= 180.0
    assert -180.0 <= yaw <= 180.0
    assert -180.0 <= roll <= 180.0
    
    # Validate it didn't collapse into a ~180 phase flip which jumps by 180 degrees.
    assert abs(pitch - target_pitch) < 5.0
    assert abs(yaw - target_yaw) < 5.0
    assert abs(roll - target_roll) < 5.0

def test_calculate_head_pose_no_landmarks():
    assert calculate_head_pose(None) == (0.0, 0.0, 0.0)
    assert calculate_head_pose(FaceLandmarks(points=[])) == (0.0, 0.0, 0.0)
