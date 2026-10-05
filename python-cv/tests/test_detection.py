import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker
from fatigue_cv.detection.types import FaceLandmarks, Point3D

@pytest.fixture
def landmarker():
    with patch("fatigue_cv.detection.face_landmarker.vision.FaceLandmarker.create_from_options") as mock_create:
        with patch("fatigue_cv.detection.face_landmarker.os.path.exists", return_value=True):
            yield MediaPipeFaceLandmarker()

def test_process_no_faces(landmarker):
    mock_results = MagicMock()
    mock_results.face_landmarks = []
    landmarker.landmarker.detect.return_value = mock_results
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = landmarker.process(frame)
    
    assert result is None

def test_process_with_face(landmarker):
    mock_results = MagicMock()
    mock_landmark = MagicMock()
    mock_landmark.x = 0.5
    mock_landmark.y = 0.6
    mock_landmark.z = 0.1
    
    mock_results.face_landmarks = [[mock_landmark]]
    landmarker.landmarker.detect.return_value = mock_results
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    result = landmarker.process(frame)
    
    assert result is not None
    assert isinstance(result, FaceLandmarks)
    assert len(result.points) == 1
    
    pt = result.points[0]
    assert pt.x == 0.5
    assert pt.y == 0.6
    assert pt.z == 0.1

def test_close(landmarker):
    landmarker.close()
    landmarker.landmarker.close.assert_called_once()
