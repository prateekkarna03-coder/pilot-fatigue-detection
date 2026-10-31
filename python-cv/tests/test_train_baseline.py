import pytest
import os
import tempfile
import pandas as pd
import joblib
from fatigue_cv.prediction.train_baseline import train_baseline

def test_train_baseline_pipeline():
    # 1. Create a dummy dataset
    data = {
        "video_name": ["V1", "V1", "V2", "V3"],
        "kss_label": [0, 0, 5, 10],
        "ear_mean": [0.2, 0.25, 0.15, 0.1],
        "ear_min": [0.1, 0.1, 0.05, 0.0],
        "mar_mean": [0.05, 0.05, 0.2, 0.3],
        "mar_max": [0.1, 0.1, 0.3, 0.4],
        "blink_rate_mean": [10, 12, 20, 30],
        "blink_rate_max": [15, 15, 25, 40],
        "yawn_rate_mean": [0, 0, 1, 3],
        "yawn_rate_max": [0, 0, 2, 4],
        "closure_duration_max": [0, 0, 1.5, 3.0],
        "pitch_median": [0, 0, 5, 10],
        "pitch_std": [1, 1, 2, 3],
        "yaw_median": [0, 0, 5, 10],
        "yaw_std": [1, 1, 2, 3],
        "roll_median": [0, 0, 5, 10],
        "roll_std": [1, 1, 2, 3]
    }
    
    # Introduce a missing value (imputation test)
    data["ear_mean"][1] = None
    
    df = pd.DataFrame(data)
    
    with tempfile.NamedTemporaryFile(suffix=".csv", mode='w', delete=False, newline='') as f_csv, \
         tempfile.NamedTemporaryFile(suffix=".joblib", mode='w', delete=False) as f_model, \
         tempfile.NamedTemporaryFile(suffix=".txt", mode='w', delete=False) as f_report:
         
        csv_path = f_csv.name
        model_path = f_model.name
        report_path = f_report.name
        
    df.to_csv(csv_path, index=False)
    
    try:
        # 2. Run the baseline training
        # This will test data loading, missing value imputation, model fitting, and validation boundaries.
        train_baseline(dataset_path=csv_path, model_out_path=model_path, report_out_path=report_path)
        
        # 3. Verify Model existence and type
        assert os.path.exists(model_path)
        pipeline = joblib.load(model_path)
        assert hasattr(pipeline, "predict")
        assert "imputer" in pipeline.named_steps
        assert "classifier" in pipeline.named_steps
        
        # 4. Verify report existence
        assert os.path.exists(report_path)
        with open(report_path, 'r') as f:
            content = f.read()
            assert "ACADEMIC BASELINE VALIDATION" in content
            assert "Train windows" in content
            
    finally:
        if os.path.exists(csv_path): os.remove(csv_path)
        if os.path.exists(model_path): os.remove(model_path)
        if os.path.exists(report_path): os.remove(report_path)
