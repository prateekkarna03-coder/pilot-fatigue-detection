from fatigue_cv.app import (
    kss_to_fatigue_score,
    should_dispatch_telemetry,
    build_telemetry_payload,
)
from fatigue_cv.prediction.types import PredictionOutput
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.types import TemporalMetrics


def test_kss_zero_maps_to_zero_score():
    assert kss_to_fatigue_score(0) == 0


def test_kss_five_maps_to_moderate_score():
    assert kss_to_fatigue_score(5) == 50


def test_kss_ten_maps_to_critical_score():
    assert kss_to_fatigue_score(10) == 100


def test_should_dispatch_telemetry_initial_call():
    """Initial dispatch must be allowed immediately when last_dispatch_time is 0.0."""
    assert should_dispatch_telemetry(last_dispatch_time=0.0, current_time=100.0, interval_seconds=1.0) is True


def test_should_dispatch_telemetry_suppresses_rapid_frames():
    """At 30 FPS (~33ms intervals), subsequent calls within the 1-second window must be suppressed."""
    last_dispatch = 100.0
    for frame_idx in range(1, 30):
        current_time = 100.0 + (frame_idx * 0.033)
        assert should_dispatch_telemetry(last_dispatch, current_time, interval_seconds=1.0) is False


def test_should_dispatch_telemetry_allows_after_interval():
    """After 1.0 second has elapsed, telemetry dispatch must be allowed."""
    last_dispatch = 100.0
    assert should_dispatch_telemetry(last_dispatch, current_time=101.0, interval_seconds=1.0) is True
    assert should_dispatch_telemetry(last_dispatch, current_time=101.5, interval_seconds=1.0) is True


def test_should_dispatch_telemetry_configurable_interval():
    """Custom intervals (e.g. 0.5s or 2.0s) must be strictly respected."""
    last_dispatch = 50.0
    # 0.5s interval
    assert should_dispatch_telemetry(last_dispatch, current_time=50.3, interval_seconds=0.5) is False
    assert should_dispatch_telemetry(last_dispatch, current_time=50.5, interval_seconds=0.5) is True

    # 2.0s interval
    assert should_dispatch_telemetry(last_dispatch, current_time=51.5, interval_seconds=2.0) is False
    assert should_dispatch_telemetry(last_dispatch, current_time=52.0, interval_seconds=2.0) is True


def test_simulated_30fps_stream_rate_limits_to_1hz():
    """Simulates a 30 FPS camera feed over 2 seconds (61 frames total at 1/30s spacing).
    Verifies that while all 61 frames process, telemetry only dispatches at ~1 Hz (3 times: t=0, t=1.0, t=2.0).
    """
    dispatched_timestamps = []
    last_dispatch = None
    interval = 1.0

    # 61 frames from t=0.0s to t=2.0s at 30 FPS
    for frame_num in range(61):
        t = round(frame_num * (1.0 / 30.0), 4)
        if should_dispatch_telemetry(last_dispatch, t, interval_seconds=interval):
            dispatched_timestamps.append(t)
            last_dispatch = t

    assert len(dispatched_timestamps) == 3
    assert dispatched_timestamps[0] == 0.0
    assert 0.99 <= dispatched_timestamps[1] <= 1.05
    assert 1.99 <= dispatched_timestamps[2] <= 2.05


def test_build_telemetry_payload_structure():
    """Verifies that the constructed payload includes all expected fields with valid data types."""
    prediction = PredictionOutput(
        kss_label=5,
        fatigue_state="Fatigued",
        class_probabilities={0: 0.1, 5: 0.8, 10: 0.1},
    )
    features = FeaturesResult(
        ear=0.28,
        mar=0.15,
        pitch=2.5,
        yaw=-1.2,
        roll=0.3,
        left_ear=0.28,
        right_ear=0.28,
    )
    metrics = TemporalMetrics(
        total_blinks=12,
        blink_rate_per_minute=14.5,
        total_yawns=1,
        yawn_rate_per_minute=0.5,
        is_yawning=False,
        current_closure_duration=0.0,
        is_prolonged_closure=False,
    )

    payload = build_telemetry_payload(
        session_id="test-session-123",
        sequence=42,
        timestamp="2026-10-11T12:00:00Z",
        prediction=prediction,
        features=features,
        metrics=metrics,
    )

    assert payload["sessionId"] == "test-session-123"
    assert payload["sequence"] == 42
    assert payload["timestamp"] == "2026-10-11T12:00:00Z"
    assert payload["fatigueScore"] == 50.0
    assert payload["kss"] == 5
    assert payload["state"] == "Fatigued"
    assert payload["blinkRatePerMin"] == 14.5
    assert payload["yawnCount"] == 1
    assert payload["headPoseDeviation"] == 4.0
    assert payload["eyeClosurePercent"] == 28.0
    assert payload["alertsTriggered"] == 0
