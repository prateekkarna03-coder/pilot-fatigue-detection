import logging
import os
import time
import joblib
from typing import Mapping, Optional
from .types import PredictionInput, PredictionOutput

logger = logging.getLogger(__name__)

FEATURE_NAMES = (
    "ear_mean", "ear_min", "mar_mean", "mar_max",
    "blink_rate_mean", "blink_rate_max", "yawn_rate_mean", "yawn_rate_max",
    "closure_duration_max", "pitch_median", "pitch_std",
    "yaw_median", "yaw_std", "roll_median", "roll_std",
)
KSS_CLASSES = (0, 5, 10)


def prediction_features(features: PredictionInput) -> dict[str, float]:
    return {
        name: float(getattr(features, name))
        for name in FEATURE_NAMES
    }


def map_probabilities(classes: list[int], probabilities: list[float]) -> dict[int, float]:
    mapped = {kss: 0.0 for kss in KSS_CLASSES}
    for cls, probability in zip(classes, probabilities):
        if cls in mapped:
            mapped[cls] = float(probability)
    return mapped


def format_prediction_diagnostic(
    features: Mapping[str, float],
    probabilities: Mapping[int, float],
    predicted_class: int,
) -> str:
    feature_text = ", ".join(
        f"{name}={features[name]:.4f}" for name in FEATURE_NAMES
    )
    probability_text = ", ".join(
        f"KSS {kss}={probabilities.get(kss, 0.0):.4f}" for kss in KSS_CLASSES
    )
    ranked = sorted(
        ((float(probabilities.get(kss, 0.0)), kss) for kss in KSS_CLASSES),
        reverse=True,
    )
    top_probability, top_class = ranked[0]
    margin = top_probability - ranked[1][0]
    return (
        "Prediction diagnostics | "
        f"features=[{feature_text}] | "
        f"probabilities=[{probability_text}] | "
        f"predicted_kss={predicted_class} | "
        f"top_kss={top_class} | top_probability={top_probability:.4f} | "
        f"top_margin={margin:.4f}"
    )


class FatiguePredictor:
    """
    Facade for the ML fatigue prediction model.
    Currently stubbed out until real training is performed.
    """
    def __init__(self, model_path: Optional[str] = None, diagnostic_interval_seconds: float = 1.0):
        self.model_path = model_path
        self.diagnostic_interval_seconds = diagnostic_interval_seconds
        self._last_diagnostic_log = 0.0
        self._model_loaded = False
        self._load_model()
        
    def _load_model(self) -> None:
        """
        Loads the scikit-learn pipeline (.pkl/.joblib) if it exists.
        Currently just logs that we are running in stub mode if no model exists.
        """
        if self.model_path and os.path.exists(self.model_path):
            self._pipeline = joblib.load(self.model_path)
            logger.info(f"Loaded ML model from {self.model_path}")
            self._model_loaded = True
        else:
            logger.warning("No valid model_path provided or file not found. Running ML in stub mode.")
            self._model_loaded = False
            
    def predict(self, features: PredictionInput) -> PredictionOutput:
        """
        Evaluates the input features and returns a fatigue prediction.
        
        Args:
            features: The combined CV and temporal features.
            
        Returns:
            PredictionOutput containing binary classification and probability score.
        """
        kss_map = {0: "Alert", 5: "Low Vigilant", 10: "Drowsy"}
        
        if not self._model_loaded:
            # Stub mode: return a dummy safe baseline
            return PredictionOutput(
                kss_label=0,
                fatigue_state=kss_map[0],
                class_probabilities={0: 1.0, 5: 0.0, 10: 0.0}
            )
            
        try:
            feature_values = prediction_features(features)
            X = [[feature_values[name] for name in FEATURE_NAMES]]
            
            # Predict
            pred_class = int(self._pipeline.predict(X)[0])
            probas = self._pipeline.predict_proba(X)[0]
            
            # Map probabilities safely based on model classes_
            prob_dict = map_probabilities(
                [int(cls) for cls in self._pipeline.classes_],
                [float(probability) for probability in probas],
            )
            now = time.monotonic()
            if now - self._last_diagnostic_log >= self.diagnostic_interval_seconds:
                logger.info(
                    format_prediction_diagnostic(feature_values, prob_dict, pred_class)
                )
                self._last_diagnostic_log = now
                
            return PredictionOutput(
                kss_label=pred_class,
                fatigue_state=kss_map.get(pred_class, "Unknown"),
                class_probabilities=prob_dict
            )
        except Exception as e:
            logger.error(f"Failed to run model prediction: {e}")
            return PredictionOutput(
                kss_label=0,
                fatigue_state=kss_map[0],
                class_probabilities={0: 1.0, 5: 0.0, 10: 0.0}
            )
