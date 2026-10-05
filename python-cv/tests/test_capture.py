import pytest
from unittest.mock import patch, MagicMock
import numpy as np
from fatigue_cv.camera.capture import CameraStream
import cv2

@pytest.fixture
def capture_stream():
    return CameraStream(device_id=0, width=640, height=480, fps=30)

@patch("fatigue_cv.camera.capture.cv2.VideoCapture")
def test_open_success(mock_videocapture, capture_stream):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_videocapture.return_value = mock_cap
    
    assert capture_stream.open() is True
    # Verify settings are applied
    mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 640)
    mock_cap.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    mock_cap.set.assert_any_call(cv2.CAP_PROP_FPS, 30)

@patch("fatigue_cv.camera.capture.cv2.VideoCapture")
def test_open_failure(mock_videocapture, capture_stream):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_videocapture.return_value = mock_cap
    
    assert capture_stream.open() is False

def test_read_frame_without_open(capture_stream):
    assert capture_stream.read_frame() is None

@patch("fatigue_cv.camera.capture.cv2.VideoCapture")
def test_read_frame_success(mock_videocapture, capture_stream):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, fake_frame)
    mock_videocapture.return_value = mock_cap
    
    capture_stream.open()
    frame = capture_stream.read_frame()
    
    assert frame is not None
    assert frame.shape == (480, 640, 3)

@patch("fatigue_cv.camera.capture.cv2.VideoCapture")
def test_read_frame_failure(mock_videocapture, capture_stream):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (False, None)
    mock_videocapture.return_value = mock_cap
    
    capture_stream.open()
    frame = capture_stream.read_frame()
    
    assert frame is None

@patch("fatigue_cv.camera.capture.cv2.VideoCapture")
def test_close(mock_videocapture, capture_stream):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_videocapture.return_value = mock_cap
    
    capture_stream.open()
    capture_stream.close()
    
    mock_cap.release.assert_called_once()
    assert capture_stream.cap is None
