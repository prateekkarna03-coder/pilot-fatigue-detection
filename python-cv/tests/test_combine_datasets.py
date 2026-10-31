import pytest
import os
import tempfile
import pandas as pd
from fatigue_cv.prediction.combine_datasets import combine_and_validate

def test_combine_and_validate_success():
    # Setup mock independent window files
    headers = ['subject_id', 'video_name', 'kss_label', 'window_id', 'ear_mean']
    
    # 01
    df1 = pd.DataFrame([
        [1, '0.mov', 0, 0, 0.25],
        [1, '5.mov', 5, 0, 0.20],
        [1, '10.mov', 10, 0, 0.15]
    ], columns=headers)
    
    # 02
    df2 = pd.DataFrame([
        [2, '0.mov', 0, 0, 0.26],
        [2, '5.mov', 5, 0, 0.21],
        [2, '10.mov', 10, 0, 0.16]
    ], columns=headers)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        df1.to_csv(os.path.join(tmpdir, "subject_01_windows.csv"), index=False)
        df2.to_csv(os.path.join(tmpdir, "subject_02_windows.csv"), index=False)
        
        out_path = os.path.join(tmpdir, "all.csv")
        
        # Test 1: Validation succeeds cleanly
        metrics = combine_and_validate(base_dir=tmpdir, output_file=out_path, subjects=["01", "02"])
        
        assert metrics['total_rows'] == 6
        assert metrics['duplicate_count'] == 0
        assert metrics['schema_valid'] is True
        
        result_df = pd.read_csv(out_path)
        assert len(result_df) == 6

def test_combine_schema_mismatch():
    with tempfile.TemporaryDirectory() as tmpdir:
        df1 = pd.DataFrame([[1, 2]], columns=['A', 'B'])
        df2 = pd.DataFrame([[1, 2]], columns=['A', 'C']) # Mismatch
        
        df1.to_csv(os.path.join(tmpdir, "subject_01_windows.csv"), index=False)
        df2.to_csv(os.path.join(tmpdir, "subject_02_windows.csv"), index=False)
        
        with pytest.raises(ValueError, match="Schema mismatch"):
            combine_and_validate(base_dir=tmpdir, output_file=os.path.join(tmpdir, "out.csv"), subjects=["01", "02"])

def test_combine_missing_kss_class():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Subject misses class 10
        df1 = pd.DataFrame([
            [1, '0.mov', 0, 0],
            [1, '5.mov', 5, 0]
        ], columns=['subject_id', 'video_name', 'kss_label', 'window_id'])
        
        df1.to_csv(os.path.join(tmpdir, "subject_01_windows.csv"), index=False)
        
        with pytest.raises(ValueError, match="does not have all KSS classes"):
            combine_and_validate(base_dir=tmpdir, output_file=os.path.join(tmpdir, "out.csv"), subjects=["01"])

def test_combine_duplicates():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Same subject/video/window combo multiple times
        df1 = pd.DataFrame([
            [1, '0.mov', 0, 0, 0.25],
            [1, '0.mov', 0, 0, 0.20], # Duplicate window!
            [1, '5.mov', 5, 0, 0.15],
            [1, '10.mov', 10, 0, 0.10]
        ], columns=['subject_id', 'video_name', 'kss_label', 'window_id', 'ear_mean'])
        
        df1.to_csv(os.path.join(tmpdir, "subject_01_windows.csv"), index=False)
        
        with pytest.raises(ValueError, match="Found 1 duplicate window"):
            combine_and_validate(base_dir=tmpdir, output_file=os.path.join(tmpdir, "out.csv"), subjects=["01"])
