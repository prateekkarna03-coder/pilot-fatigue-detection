import pytest
import os
import csv
from unittest.mock import patch, MagicMock
from fatigue_cv.dataset_extractor import DatasetExtractor
import tempfile
import numpy as np
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.detection.types import FaceLandmarks, Point3D

@pytest.fixture
def mock_cv2():
    with patch('fatigue_cv.dataset_extractor.cv2') as mock_cv2:
        yield mock_cv2

@pytest.fixture
def mock_detector():
    with patch('fatigue_cv.dataset_extractor.MediaPipeFaceLandmarker') as mock_landmarker:
        instance = mock_landmarker.return_value
        yield instance

def test_extraction_process_video(mock_cv2, mock_detector):
    # Setup mock video capture
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.get.return_value = 30.0 # FPS
    
    # Simulate 3 frames
    frames = [
        (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        (True, np.zeros((480, 640, 3), dtype=np.uint8)),
        (False, None) # EOF
    ]
    mock_cap.read.side_effect = frames
    mock_cv2.VideoCapture.return_value = mock_cap

    # Setup mock detector to return dummy landmarks
    points = [Point3D(x=0.5, y=0.5, z=0.0) for _ in range(478)]
    dummy_landmarks = FaceLandmarks(points=points)
    mock_detector.process.return_value = dummy_landmarks
    
    # We patch calculate_ear, mar, and head_pose to return predictable values since 
    # we just passed zero-ed out landmarks
    with patch('fatigue_cv.dataset_extractor.calculate_ear', return_value=0.3), \
         patch('fatigue_cv.dataset_extractor.calculate_mar', return_value=0.1), \
         patch('fatigue_cv.dataset_extractor.calculate_head_pose', return_value=(0.0, 0.0, 0.0)):
        
        extractor = DatasetExtractor()
        results = list(extractor.process_video("fake/0.mov", "01", 0))
        
        assert len(results) == 3
        
        row_0 = results[0]
        assert row_0["subject_id"] == "01"
        assert row_0["video_name"] == "0.mov"
        assert row_0["kss_label"] == 0
        assert row_0["class_name"] == "Alert"
        assert row_0["frame_number"] == 0
        assert row_0["ear"] == 0.3
        assert row_0["mar"] == 0.1
        assert "total_blinks" in row_0
        
        row_2 = results[2]
        assert row_2["frame_number"] == 2
        
def test_extract_and_save(mock_cv2, mock_detector):
    # Setup mock process_video to just return a couple records
    fake_rows = [
        {"subject_id": "01", "video_name": "0.mov", "kss_label": 0, "class_name": "Alert", "frame_number": 0, "timestamp": 0.0, "ear": 0.35, "mar": 0.05, "pitch": 0.0, "yaw": 0.0, "roll": 0.0, "total_blinks": 0, "blink_rate_per_minute": 0.0, "current_closure_duration": 0.0, "is_prolonged_closure": False, "total_yawns": 0, "yawn_rate_per_minute": 0.0, "is_yawning": False},
        {"subject_id": "01", "video_name": "0.mov", "kss_label": 0, "class_name": "Alert", "frame_number": 1, "timestamp": 0.033, "ear": 0.35, "mar": 0.05, "pitch": 0.0, "yaw": 0.0, "roll": 0.0, "total_blinks": 0, "blink_rate_per_minute": 0.0, "current_closure_duration": 0.0, "is_prolonged_closure": False, "total_yawns": 0, "yawn_rate_per_minute": 0.0, "is_yawning": False},
    ]

    extractor = DatasetExtractor()
    with patch.object(extractor, 'process_video', return_value=fake_rows):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".csv") as tmp:
            tmp_path = tmp.name
        
        try:
            videos_to_process = [("fake/0.mov", "01", 0)]
            extractor.extract_and_save(videos_to_process, tmp_path)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]["video_name"] == "0.mov"
                assert rows[0]["kss_label"] == "0" # CSV parses as string
                assert rows[0]["class_name"] == "Alert"
                assert rows[0]["is_yawning"] == "False"
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

def test_tracker_resets_between_videos(mock_cv2, mock_detector):
    # Verify that processing multiple videos instantiates a fresh tracker
    fake_rows = [{"frame_number": 0}]
    extractor = DatasetExtractor()
    
    with patch('fatigue_cv.dataset_extractor.TemporalTracker') as mock_tracker_class:
        mock_tracker_class.return_value.update.return_value = MagicMock()
        
        # Simulate video processing yielding 1 row
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2.VideoCapture.return_value = mock_cap
        
        with patch.object(extractor, 'detector') as mock_det:
            # First video
            mock_cap.read.side_effect = [(True, np.zeros((10, 10, 3))), (False, None)]
            list(extractor.process_video("fake/0.mov", "01", 0))
            assert mock_tracker_class.call_count == 1
            
            # Second video
            mock_cap.read.side_effect = [(True, np.zeros((10, 10, 3))), (False, None)]
            list(extractor.process_video("fake/5.mov", "01", 5))
            assert mock_tracker_class.call_count == 2
