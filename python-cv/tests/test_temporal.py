import pytest
from fatigue_cv.temporal.tracker import TemporalTracker
from fatigue_cv.config.settings import TemporalSettings
from fatigue_cv.features.types import FeaturesResult

@pytest.fixture
def base_settings():
    return TemporalSettings(
        ear_threshold=0.25,
        mar_threshold=0.5,
        prolonged_closure_time=3.0,
        window_size=60.0,
        yawn_min_duration=2.0,
        yawn_cooldown=1.0
    )

def _feat(ear=0.3, mar=0.1):
    return FeaturesResult(ear=ear, mar=mar, pitch=0.0, yaw=0.0, roll=0.0)

def test_blink_rates_and_totals(base_settings):
    # Short window testing
    sets = TemporalSettings(ear_threshold=0.25, mar_threshold=0.5, prolonged_closure_time=3.0, window_size=5.0, yawn_min_duration=2.0, yawn_cooldown=1.0)
    tracker = TemporalTracker(sets)
    
    # Blink 1
    tracker.update(_feat(ear=0.2), 1.0)
    m1 = tracker.update(_feat(ear=0.3), 1.1)
    
    # Blink 2
    tracker.update(_feat(ear=0.2), 2.0)
    m2 = tracker.update(_feat(ear=0.3), 2.1)
    
    assert m2.total_blinks == 2
    assert m2.blink_rate_per_minute == (2 / 5.0) * 60
    
    # Wait until Blink 1 expires from window (time 6.2, > 1.1 + 5.0)
    m3 = tracker.update(_feat(ear=0.3), 6.5)
    assert m3.total_blinks == 2 # never decreases
    assert m3.blink_rate_per_minute == (1 / 5.0) * 60 # only blink 2 is inside 5.0s window (since 2.1 > 6.5 - 5.0)
    
    # Wait until Blink 2 expires (time > 7.1)
    m4 = tracker.update(_feat(ear=0.3), 8.0)
    assert m4.total_blinks == 2
    assert m4.blink_rate_per_minute == 0.0

def test_yawn_talking_does_not_count(base_settings):
    tracker = TemporalTracker(base_settings)
    # Open mouth (talking momentarily)
    m1 = tracker.update(_feat(mar=0.6), 1.0)
    m2 = tracker.update(_feat(mar=0.6), 1.5) # duration 0.5s < 2.0s
    assert m2.is_yawning is False
    assert m2.total_yawns == 0
    
    # Close mouth
    m3 = tracker.update(_feat(mar=0.1), 1.6)
    assert m3.total_yawns == 0

def test_yawn_sustained_counts_once(base_settings):
    tracker = TemporalTracker(base_settings)
    
    tracker.update(_feat(mar=0.6), 1.0)
    m = tracker.update(_feat(mar=0.6), 3.1) # 2.1s elapsed >= 2.0s
    assert m.is_yawning is True
    assert m.total_yawns == 0 # not finished yet
    
    # Keeps yawning
    m2 = tracker.update(_feat(mar=0.6), 5.0)
    assert m2.total_yawns == 0
    
    # Close mouth, finishes yawn
    m3 = tracker.update(_feat(mar=0.1), 5.1)
    assert m3.is_yawning is False
    assert m3.total_yawns == 1

def test_yawn_cooldown_prevents_duplicate(base_settings):
    tracker = TemporalTracker(base_settings)
    
    tracker.update(_feat(mar=0.6), 1.0)
    tracker.update(_feat(mar=0.6), 3.1) # yawn valid
    m1 = tracker.update(_feat(mar=0.1), 3.2) # closed, total_yawns = 1
    assert m1.total_yawns == 1
    
    # Immediately open mouth again at 3.3 (0.1s later < cooldown 1.0)
    tracker.update(_feat(mar=0.6), 3.3)
    # Sustain for 2.0s
    tracker.update(_feat(mar=0.6), 5.4)
    # Close
    m2 = tracker.update(_feat(mar=0.1), 5.5)
    
    # Second yawn was ignored entirely due to cooldown blocking the state transition initially
    # Actually wait: at 3.3 it was ignored, but what happens at 3.4, 3.5... it will keep failing to start if cooldown enforces 'not mouth_open' requirement safely.
    # Ah, if mouth is opened at 3.3, current_time - last (0.1) < cooldown.
    # So mouth_open remains False! Even at 5.4, since mouth_open is False, it will attempt to transition. At 5.4, 5.4 - 3.2 > 1.0, so it WILL transition to True at 5.4.
    # Then it needs ANOTHER 2.0s to complete. Since we close at 5.5, it did not reach duration.
    # Result should be exactly 1.
    assert m2.total_yawns == 1

def test_no_face_clears_duration(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.2), 1.0)
    tracker.update(_feat(ear=0.2), 1.5)
    
    # Face lost
    m = tracker.update(None, 2.0)
    assert m.current_closure_duration == 0.0
    assert m.is_prolonged_closure is False
    assert m.total_blinks == 0
