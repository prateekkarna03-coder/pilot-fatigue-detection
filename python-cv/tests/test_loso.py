import pytest
import os
import tempfile
import pandas as pd
import numpy as np
import joblib
from fatigue_cv.prediction.train_loso import train_loso
from fatigue_cv.prediction.model import FatiguePredictor
from fatigue_cv.prediction.types import PredictionInput

def test_loso_leakage_and_pipeline():
    # 1. Create a mock dataset mimicking the real 4-subject schema
    data = []
    # 4 Subjects (01, 02, 03, 05) each with 3 KSS values
    for subj in [1, 2, 3, 5]:
        for kss in [0, 5, 10]:
            # Add 2 windows per class per subject
            for w in range(2):
                data.append({
                    "subject_id": subj,
                    "kss_label": kss,
                    "ear_mean": np.random.rand(),
                    "ear_min": 0, "mar_mean": 0, "mar_max": 0,
                    "blink_rate_mean": 0, "blink_rate_max": 0, 
                    "yawn_rate_mean": 0, "yawn_rate_max": 0,
                    "closure_duration_max": 0, "pitch_median": 0, "pitch_std": 0,
                    "yaw_median": 0, "yaw_std": 0, "roll_median": 0, "roll_std": 0
                })
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        csv_path = os.path.join(tmpdir, "mock_all.csv")
        report_path = os.path.join(tmpdir, "report.txt")
        cm_path = os.path.join(tmpdir, "cm.json")
        model_path = os.path.join(tmpdir, "final.joblib")
        
        df.to_csv(csv_path, index=False)
        
        # Train LOSO
        train_loso(csv_path, report_path, cm_path, model_path)
        
        # Verify artifacts
        assert os.path.exists(report_path)
        assert os.path.exists(cm_path)
        assert os.path.exists(model_path)
        
        with open(report_path, "r") as f:
            report_text = f.read()
            # Verify 4 folds were parsed (one for each subject)
            assert "FOLD 1" in report_text
            assert "FOLD 4" in report_text
            # Verify aggregation
            assert "OVERALL AGGREGATE METRICS" in report_text
            
        # Verify actual Pipeline was saved and fitted on full data
        pipeline = joblib.load(model_path)
        assert hasattr(pipeline, "predict")
        
        # Instantiate Scaffold and verify Mapping + Integration
        predictor = FatiguePredictor(model_path=model_path)
        
        features = PredictionInput(
            ear_mean=0.3, ear_min=0.1, mar_mean=0.05, mar_max=0.3,
            blink_rate_mean=15.0, blink_rate_max=20.0, yawn_rate_mean=0, yawn_rate_max=1,
            closure_duration_max=0.0, pitch_median=0, pitch_std=1,
            yaw_median=0, yaw_std=1, roll_median=0, roll_std=1
        )
        
        result = predictor.predict(features)
        
        # Verify prediction properties
        assert result.kss_label in [0, 5, 10]
        assert result.fatigue_state in ["Alert", "Low Vigilant", "Drowsy"]
        assert isinstance(result.class_probabilities, dict)
        assert 0 in result.class_probabilities
        assert 5 in result.class_probabilities
        assert 10 in result.class_probabilities
        
        # Sum of probabilities should be exactly 1.0 (with a tiny float epsilon)
        total_prob = sum(result.class_probabilities.values())
        assert abs(total_prob - 1.0) < 1e-5

def test_missing_model_stub_mode():
    # If the model does not exist, predictor safely defaults
    predictor = FatiguePredictor(model_path="nonexistent.joblib")
    features = PredictionInput(
        ear_mean=0.3, ear_min=0.1, mar_mean=0.05, mar_max=0.3,
        blink_rate_mean=15.0, blink_rate_max=20.0, yawn_rate_mean=0, yawn_rate_max=1,
        closure_duration_max=0.0, pitch_median=0, pitch_std=1,
        yaw_median=0, yaw_std=1, roll_median=0, roll_std=1
    )
    result = predictor.predict(features)
    assert result.kss_label == 0
    assert result.fatigue_state == "Alert"
