import pytest
from fatigue_cv.prediction.types import PredictionInput, PredictionOutput
from fatigue_cv.prediction.model import (
    FEATURE_NAMES,
    FatiguePredictor,
    format_prediction_diagnostic,
    map_probabilities,
    prediction_features,
)

def test_prediction_input_creation():
    """Test that the prediction input dataclass stores values correctly."""
    features = PredictionInput(
        ear_mean=0.25, ear_min=0.1, mar_mean=0.05, mar_max=0.1,
        blink_rate_mean=15.0, blink_rate_max=15.0, yawn_rate_mean=0.0, yawn_rate_max=0.0,
        closure_duration_max=0.1, pitch_median=5.0, pitch_std=0.5,
        yaw_median=-2.0, yaw_std=0.5, roll_median=0.5, roll_std=0.1
    )
    assert features.ear_mean == 0.25
    assert features.closure_duration_max == 0.1

def test_fatigue_predictor_stub_mode():
    """Test that the predictor falls back to a safe stub when no model is available."""
    # Initialize without a real model path
    predictor = FatiguePredictor(model_path="non_existent_model.pkl")
    
    features = PredictionInput(
        ear_mean=0.20, ear_min=0.1, mar_mean=0.6, mar_max=0.6,
        blink_rate_mean=20.0, blink_rate_max=20.0, yawn_rate_mean=2.0, yawn_rate_max=2.0,
        closure_duration_max=2.5, pitch_median=0.0, pitch_std=0.0,
        yaw_median=0.0, yaw_std=0.0, roll_median=0.0, roll_std=0.0
    )
    result = predictor.predict(features)
    
    # Should safely return a non-fatigued PredictionOutput based on the KSS mapping logic
    assert result.kss_label == 0
    assert result.fatigue_state == "Alert"
    assert 0 in result.class_probabilities

def test_predictor_extreme_values():
    """Test that the predictor interface doesn't crash on extreme input limits."""
    predictor = FatiguePredictor()
    
    extreme_features = PredictionInput(
        ear_mean=999.9, ear_min=999.9, mar_mean=-999.9, mar_max=999.9,
        blink_rate_mean=999.9, blink_rate_max=999.9, yawn_rate_mean=999.9, yawn_rate_max=999.9,
        closure_duration_max=9999.9, pitch_median=1000.0, pitch_std=100.0,
        yaw_median=-1000.0, yaw_std=100.0, roll_median=float('inf'), roll_std=100.0
    )
    
    # Just asserting it computes without exception
    result = predictor.predict(extreme_features)
    assert result is not None


def test_prediction_features_preserve_training_order():
    features = PredictionInput(
        ear_mean=1, ear_min=2, mar_mean=3, mar_max=4,
        blink_rate_mean=5, blink_rate_max=6, yawn_rate_mean=7, yawn_rate_max=8,
        closure_duration_max=9, pitch_median=10, pitch_std=11,
        yaw_median=12, yaw_std=13, roll_median=14, roll_std=15,
    )

    assert list(prediction_features(features)) == list(FEATURE_NAMES)
    assert list(prediction_features(features).values()) == list(range(1, 16))


def test_probability_mapping_always_reports_expected_kss_classes():
    probabilities = map_probabilities([10, 0], [0.7, 0.3])

    assert probabilities == {0: 0.3, 5: 0.0, 10: 0.7}


def test_prediction_diagnostic_contains_features_probabilities_and_margin():
    features = {name: float(index) for index, name in enumerate(FEATURE_NAMES)}
    diagnostic = format_prediction_diagnostic(
        features,
        {0: 0.1, 5: 0.35, 10: 0.55},
        predicted_class=10,
    )

    assert "Prediction diagnostics" in diagnostic
    assert "ear_mean=0.0000" in diagnostic
    assert "roll_std=14.0000" in diagnostic
    assert "KSS 0=0.1000" in diagnostic
    assert "KSS 5=0.3500" in diagnostic
    assert "KSS 10=0.5500" in diagnostic
    assert "predicted_kss=10" in diagnostic
    assert "top_probability=0.5500" in diagnostic
    assert "top_margin=0.2000" in diagnostic
