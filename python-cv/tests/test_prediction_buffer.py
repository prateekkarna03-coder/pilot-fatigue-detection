import pytest
from fatigue_cv.prediction.buffer import PredictionBuffer
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.types import TemporalMetrics
from fatigue_cv.prediction.types import PredictionInput

def test_prediction_buffer_lifecycle():
    buffer = PredictionBuffer(window_duration=10.0)
    
    # 1. Test Empty Aggregation throws exactly ValueError
    with pytest.raises(ValueError, match="no valid face tracking data"):
        buffer.get_aggregated_input()
        
    feat = FeaturesResult(
        ear=0.3,
        mar=0.1,
        pitch=0.0,
        yaw=0.0,
        roll=0.0
    )
    metrics = TemporalMetrics(
        total_blinks=0, current_closure_duration=0, blink_rate_per_minute=10.0,
        total_yawns=0, yawn_rate_per_minute=0.0, is_prolonged_closure=False,
        is_yawning=False
    )
    
    # 2. Add elements and check aggregates
    buffer.add(10.0, feat, metrics)
    buffer.add(15.0, feat, metrics)
    
    agg = buffer.get_aggregated_input()
    assert isinstance(agg, PredictionInput)
    assert agg.ear_mean == 0.3
    assert agg.blink_rate_max == 10.0
    assert agg.pitch_std == 0.0 # 2 equal items = stdev 0.0
    
    # 3. Test Eviction
    buffer.add(26.0, feat, metrics) # 26.0 causes items < 16.0 to be evicted!
    # Expected behavior: Time 10.0 and 15.0 are evicted. Only 26.0 remains.
    assert len(buffer._buffer) == 1
    assert buffer._buffer[0]["timestamp"] == 26.0
    
    # 4. Test Missing Faces (None features)
    buffer.add(28.0, None, metrics)
    assert len(buffer._buffer) == 2
    
    # Aggregation safely skips the None
    agg2 = buffer.get_aggregated_input()
    assert agg2.ear_mean == 0.3 # from the 26.0 timestamp only!
    
def test_insufficient_window_handling():
    # If buffer only contains None (face constantly missing)
    buffer = PredictionBuffer()
    metrics = TemporalMetrics(
        total_blinks=0, current_closure_duration=0, blink_rate_per_minute=10.0,
        total_yawns=0, yawn_rate_per_minute=0.0, is_prolonged_closure=False,
        is_yawning=False
    )
    buffer.add(1.0, None, metrics)
    buffer.add(2.0, None, metrics)
    with pytest.raises(ValueError):
        buffer.get_aggregated_input()
