import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from fatigue_cv.run_batch_extraction import find_kss_videos, process_batch

def test_find_kss_videos(tmp_path):
    # Setup dummy video files
    subj_dir = tmp_path / "02"
    subj_dir.mkdir()
    
    (subj_dir / "0.mov").touch()
    (subj_dir / "5.MOV").touch()
    (subj_dir / "10.mov").touch()
    (subj_dir / "random.txt").touch()
    
    videos = find_kss_videos(str(subj_dir))
    
    assert len(videos) == 3
    
    # Check paths and mapped labels
    assert (str(subj_dir / "0.mov"), "02", 0) in videos
    assert (str(subj_dir / "5.MOV"), "02", 5) in videos
    assert (str(subj_dir / "10.mov"), "02", 10) in videos

def test_batch_process_resumes_safely(tmp_path):
    base_dir = tmp_path / "Fold1_part1"
    base_dir.mkdir()
    
    out_dir = tmp_path / "extracted-features"
    out_dir.mkdir()
    
    # Mock data directories
    for subj in ["02", "03", "04", "05", "06"]: # Including 06 to prove it gets ignored
        d = base_dir / subj
        d.mkdir()
        (d / "0.mov").touch()
        (d / "5.mov").touch()
        (d / "10.mov").touch()
        
    # Simulate that Subject 02 has already been fully processed
    (out_dir / "subject_02_features_v2.csv").touch()
    (out_dir / "subject_02_windows.csv").touch()
    
    # Simulate that Subject 03 has features but no windows
    (out_dir / "subject_03_features_v2.csv").touch()
    
    with patch('fatigue_cv.run_batch_extraction.DatasetExtractor') as ExtractorMock, \
         patch('fatigue_cv.run_batch_extraction.create_windows') as WindowsMock:
             
        mock_extractor_inst = MagicMock()
        ExtractorMock.return_value = mock_extractor_inst
        
        # Test default subjects included
        subjects = ["02", "03", "04", "05"] # Explicitly omits 06 by default constraint
        
        process_batch(base_dir=str(base_dir), out_dir=str(out_dir), subjects_to_include=subjects)
        
        # Extractor Mock should NOT have been called for 02 (resumed) or 03 (features exist)
        # It should ONLY be called for 04 and 05
        assert mock_extractor_inst.extract_and_save.call_count == 2
        
        # Check extraction calls directly
        calls = mock_extractor_inst.extract_and_save.call_args_list
        called_feats = [c[0][1] for c in calls]
        assert str(out_dir / "subject_04_features_v2.csv") in called_feats
        assert str(out_dir / "subject_05_features_v2.csv") in called_feats
        
        # Windows Mock should be called ONLY for 03, because the Mock Extractor doesn't physically write files for 04/05
        assert WindowsMock.call_count == 1
        win_calls = WindowsMock.call_args_list
        called_wins = [c[0][1] for c in win_calls]
        assert str(out_dir / "subject_03_windows.csv") in called_wins
