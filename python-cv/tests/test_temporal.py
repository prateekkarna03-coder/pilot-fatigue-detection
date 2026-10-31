import pytest
from fatigue_cv.temporal.tracker import TemporalTracker
from fatigue_cv.config.settings import TemporalSettings
from fatigue_cv.features.types import FeaturesResult

@pytest.fixture
def base_settings():
    return TemporalSettings(
        ear_drop_ratio=0.75,
        mar_threshold=0.35, # updated threshold
        prolonged_closure_time=3.0,
        window_size=60.0,
        yawn_min_duration=2.0,
        yawn_cooldown=1.0,
        dynamic_baseline_time=10.0,
        missing_grace_period=0.5
    )

def _feat(ear=0.3, mar=0.1, pitch=0.0, yaw=0.0, roll=0.0, left_ear=None, right_ear=None):
    return FeaturesResult(
        ear=ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll,
        left_ear=left_ear, right_ear=right_ear
    )

def test_blink_rates_and_totals(base_settings):
    # Short window testing
    sets = TemporalSettings(mar_threshold=0.35, prolonged_closure_time=3.0, window_size=5.0, yawn_min_duration=2.0, yawn_cooldown=1.0, missing_grace_period=0.5, dynamic_baseline_time=10.0, ear_drop_ratio=0.75)
    tracker = TemporalTracker(sets)
    
    # Establish baseline
    tracker.update(_feat(ear=0.3), 0.5)
    
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2) # Smooth buffer filled
    
    # Blink 1
    tracker.update(_feat(ear=0.1), 1.3)
    tracker.update(_feat(ear=0.1), 1.4) 
    tracker.update(_feat(ear=0.1), 1.5) # fully closed
    tracker.update(_feat(ear=0.3), 1.6)
    tracker.update(_feat(ear=0.3), 1.7)
    m1 = tracker.update(_feat(ear=0.3), 1.8) # fully open (blink 1)
    
    # Blink 2
    tracker.update(_feat(ear=0.1), 2.3)
    tracker.update(_feat(ear=0.1), 2.4)
    tracker.update(_feat(ear=0.1), 2.5) # fully closed
    tracker.update(_feat(ear=0.3), 2.6)
    tracker.update(_feat(ear=0.3), 2.7)
    m2 = tracker.update(_feat(ear=0.3), 2.8) # fully open (blink 2)
    
    assert m2.total_blinks == 2
    assert m2.blink_rate_per_minute == (2 / 5.0) * 60
    
    # Wait until Blink 1 expires from window (time 6.8, > 1.8 + 5.0)
    m3 = tracker.update(_feat(ear=0.3), 6.9)
    assert m3.total_blinks == 2 # never decreases
    assert m3.blink_rate_per_minute == (1 / 5.0) * 60 # only blink 2 is inside 5.0s window (since 2.8 > 6.9 - 5.0)
    
    # Wait until Blink 2 expires (time > 7.8)
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

def test_no_face_grace_period(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 0.9)
    tracker.update(_feat(ear=0.1), 1.0) # closed
    tracker.update(_feat(ear=0.1), 1.2) # closed duration 0.2
    
    # Face lost for 0.4s (within 0.5s Grace Period)
    m = tracker.update(None, 1.6)
    assert m.current_closure_duration == 1.6 - 1.0 # 0.6s
    assert tracker.eyes_closed is True
    
    # Face lost for 0.6s total (1.2 -> 1.8), clears state
    m2 = tracker.update(None, 1.8)
    assert m2.current_closure_duration == 0.0
    assert tracker.eyes_closed is False


# --- NEW EXACT STATE MACHINE COMPLIANCE TESTS ---

def test_normal_open_eyes_zero_blinks(base_settings):
    # normal open eyes -> 0 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    m = tracker.update(_feat(ear=0.3), 1.2)
    assert m.total_blinks == 0

def test_one_clean_short_cycle(base_settings):
    # one clean short close->open cycle -> exactly 1 blink
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2) # Smooth buffer filled
    
    # Close
    tracker.update(_feat(ear=0.1), 1.3)
    tracker.update(_feat(ear=0.1), 1.4)
    tracker.update(_feat(ear=0.1), 1.5) # Closed firmly
    
    # Open
    tracker.update(_feat(ear=0.3), 1.6)
    tracker.update(_feat(ear=0.3), 1.7)
    m = tracker.update(_feat(ear=0.3), 1.8)
    assert m.total_blinks == 1

def test_three_separate_clean_cycles(base_settings):
    # three separate clean close->open cycles -> exactly 3 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    times = [1.3, 2.3, 3.3]
    for t in times:
        tracker.update(_feat(ear=0.1), t)
        tracker.update(_feat(ear=0.1), t+0.1)
        tracker.update(_feat(ear=0.1), t+0.2)
        
        tracker.update(_feat(ear=0.3), t+0.3)
        tracker.update(_feat(ear=0.3), t+0.4)
        m = tracker.update(_feat(ear=0.3), t+0.5)
        
    assert m.total_blinks == 3

def test_one_long_closure_zero_blinks(base_settings):
    # one long closure -> exactly 0 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Close for 2 seconds
    for i in range(20):
        m = tracker.update(_feat(ear=0.1), 1.3 + i*0.1)
        
    assert m.total_blinks == 0
    
def test_long_closure_followed_by_reopening(base_settings):
    # long closure followed by reopening -> exactly 0 blinks and prolonged_closure recorded
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Close for 4 seconds (> 3.0 prolonged threshold, > 0.6 max blink)
    for i in range(40):
        tracker.update(_feat(ear=0.1), 1.3 + i*0.1)
        
    m_closed = tracker.update(_feat(ear=0.1), 5.3) # Before open
    assert m_closed.is_prolonged_closure is True
    
    # Reopen
    tracker.update(_feat(ear=0.3), 5.4)
    tracker.update(_feat(ear=0.3), 5.5)
    m = tracker.update(_feat(ear=0.3), 5.6)
    
    assert m.total_blinks == 0

def test_ear_noise_around_open_threshold(base_settings):
    # EAR noise around the open threshold -> 0 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Open EAR drops slightly but stays above closure threshold, effectively noise
    # close threshold is 0.3 * 0.75 = 0.225
    tracker.update(_feat(ear=0.25), 1.3)
    tracker.update(_feat(ear=0.31), 1.4)
    tracker.update(_feat(ear=0.26), 1.5)
    m = tracker.update(_feat(ear=0.3), 1.6)
    assert m.total_blinks == 0

def test_looking_downward_with_open_eyes(base_settings):
    # looking downward with open eyes -> 0 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Look down (pitch < -15), EAR geometry breaks and drops artificially
    tracker.update(FeaturesResult(ear=0.1, mar=0.1, pitch=-25.0, yaw=0.0, roll=0.0), 1.3)
    tracker.update(FeaturesResult(ear=0.1, mar=0.1, pitch=-25.0, yaw=0.0, roll=0.0), 1.4)
    tracker.update(FeaturesResult(ear=0.1, mar=0.1, pitch=-25.0, yaw=0.0, roll=0.0), 1.5)
    
    # Look back up
    tracker.update(_feat(ear=0.3), 1.6)
    tracker.update(_feat(ear=0.3), 1.7)
    m = tracker.update(_feat(ear=0.3), 1.8)
    
    assert m.total_blinks == 0

def test_looking_upward_with_open_eyes(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Upward (pitch > 15) usually doesn't trigger closure logic anyway unless EAR drops, but shouldn't trigger
    tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=25.0, yaw=0.0, roll=0.0), 1.3)
    tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=25.0, yaw=0.0, roll=0.0), 1.4)
    m = tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=25.0, yaw=0.0, roll=0.0), 1.5)
    assert m.total_blinks == 0

def test_head_turning_with_open_eyes(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=0.0, yaw=30.0, roll=0.0), 1.3)
    tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=0.0, yaw=30.0, roll=0.0), 1.4)
    m = tracker.update(FeaturesResult(ear=0.26, mar=0.1, pitch=0.0, yaw=30.0, roll=0.0), 1.5)
    assert m.total_blinks == 0

def test_missing_face_during_open_period(base_settings):
    # missing-face frames during an open period -> 0 blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Missing face
    tracker.update(None, 1.3)
    tracker.update(None, 1.4)
    m = tracker.update(None, 1.5)
    assert m.total_blinks == 0

def test_missing_face_frames_during_closure_no_repeated_blinks(base_settings):
    # missing-face frames during a closure -> must not create repeated blinks
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.2)
    
    # Close
    tracker.update(_feat(ear=0.1), 1.3)
    tracker.update(_feat(ear=0.1), 1.4)
    tracker.update(_feat(ear=0.1), 1.5)
    
    # Lose face
    tracker.update(None, 1.6)
    tracker.update(None, 1.7)
    
    # Timeout grace period (0.5s limit)
    tracker.update(None, 2.5) 
    
    # Face back open
    tracker.update(_feat(ear=0.3), 2.6)
    tracker.update(_feat(ear=0.3), 2.7)
    m = tracker.update(_feat(ear=0.3), 2.8)
    
    # Because grace period expired, state reset to False SILENTLY without emitting a blink via state machine checks
    assert m.total_blinks == 0

def test_reopening_after_closure_at_most_one_blink(base_settings):
    # reopening after a closure must produce at most one blink event
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(ear=0.3), 1.0)
    tracker.update(_feat(ear=0.3), 1.1)
    tracker.update(_feat(ear=0.3), 1.3)
    
    # Close
    tracker.update(_feat(ear=0.1), 1.4)
    tracker.update(_feat(ear=0.1), 1.5)
    tracker.update(_feat(ear=0.1), 1.6)
    
    # Open slowly (noise on the way up)
    tracker.update(_feat(ear=0.2), 1.7)
    tracker.update(_feat(ear=0.29), 1.8) # Crosses threshold and triggers blink!
    tracker.update(_feat(ear=0.20), 1.9) # Drops back below (doesn't trigger new transition because doesn't drop below Close threshold mapping natively in smoothed)
    tracker.update(_feat(ear=0.3), 2.0)
    tracker.update(_feat(ear=0.3), 2.1)
    
    m = tracker.update(_feat(ear=0.3), 2.2)
    assert m.total_blinks == 1

def test_head_roll_with_bilateral_ear_variation_does_not_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.0)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.1)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.2)

    tracker.update(_feat(0.1, roll=20.0, left_ear=0.1, right_ear=0.1), 1.3)
    tracker.update(_feat(0.1, roll=20.0, left_ear=0.1, right_ear=0.1), 1.4)
    m = tracker.update(_feat(0.3, roll=20.0, left_ear=0.3, right_ear=0.3), 1.5)
    assert m.total_blinks == 0

def test_head_yaw_with_bilateral_ear_variation_does_not_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.0)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.1)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.2)

    tracker.update(_feat(0.1, yaw=20.0, left_ear=0.1, right_ear=0.1), 1.3)
    tracker.update(_feat(0.1, yaw=20.0, left_ear=0.1, right_ear=0.1), 1.4)
    m = tracker.update(_feat(0.3, yaw=20.0, left_ear=0.3, right_ear=0.3), 1.5)
    assert m.total_blinks == 0

def test_asymmetric_one_eye_drop_does_not_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.0)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.1)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.2)

    tracker.update(_feat(0.2, left_ear=0.1, right_ear=0.3), 1.3)
    tracker.update(_feat(0.2, left_ear=0.1, right_ear=0.3), 1.4)
    m = tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.5)
    assert m.total_blinks == 0

def test_head_movement_then_ear_recovery_does_not_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.0)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.1)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.2)

    tracker.update(_feat(0.1, yaw=20.0, left_ear=0.1, right_ear=0.1), 1.3)
    tracker.update(_feat(0.1, yaw=20.0, left_ear=0.1, right_ear=0.1), 1.4)
    tracker.update(_feat(0.1, yaw=0.0, left_ear=0.1, right_ear=0.1), 1.5)
    m = tracker.update(_feat(0.3, yaw=0.0, left_ear=0.3, right_ear=0.3), 1.6)
    assert m.total_blinks == 0

def test_one_eye_crossing_one_frame_later_still_counts_one_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    for t in (1.0, 1.1, 1.2):
        tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), t)

    tracker.update(_feat(0.2, left_ear=0.1, right_ear=0.3), 1.3)
    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.4)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.5)
    m = tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.6)
    assert m.total_blinks == 1

def test_brief_one_eye_noise_during_blink_still_counts_one_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    for t in (1.0, 1.1, 1.2):
        tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), t)

    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.3)
    tracker.update(_feat(0.2, left_ear=0.1, right_ear=0.3), 1.4)
    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.5)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.6)
    m = tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.7)
    assert m.total_blinks == 1

def test_asymmetric_sustained_closure_does_not_blink(base_settings):
    tracker = TemporalTracker(base_settings)
    for t in (1.0, 1.1, 1.2):
        tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), t)

    for i in range(10):
        m = tracker.update(
            _feat(0.2, left_ear=0.1, right_ear=0.3),
            1.3 + i * 0.1,
        )
    assert m.total_blinks == 0

def test_open_eyes_recover_from_closed_state(base_settings):
    tracker = TemporalTracker(base_settings)
    for t in (1.0, 1.1, 1.2):
        tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), t)

    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.3)
    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.4)
    m = tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.5)
    assert m.diagnostic_data["eye_state"] == "OPEN"

def test_single_high_ear_spike_does_not_raise_reopening_threshold(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.0)
    tracker.update(_feat(0.8, left_ear=0.8, right_ear=0.8), 1.1)
    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.2)
    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.3)
    m = tracker.update(_feat(0.3, left_ear=0.3, right_ear=0.3), 1.4)
    assert m.diagnostic_data["eye_state"] == "OPEN"

def test_left_and_right_eyes_use_separate_open_baselines(base_settings):
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.25, left_ear=0.2, right_ear=0.3), 1.0)
    tracker.update(_feat(0.25, left_ear=0.2, right_ear=0.3), 1.1)
    tracker.update(_feat(0.25, left_ear=0.2, right_ear=0.3), 1.2)

    tracker.update(_feat(0.1, left_ear=0.1, right_ear=0.1), 1.3)
    m = tracker.update(_feat(0.25, left_ear=0.2, right_ear=0.3), 1.4)
    assert m.diagnostic_data["eye_state"] == "OPEN"
    assert m.diagnostic_data["left_baseline_ear"] < m.diagnostic_data["right_baseline_ear"]

def test_tracker_angle_bounds_never_drift(base_settings):
    # Regression test for unbounded 360 degree accumulation
    # Angles should remain bounded in [-180, 180] strictly
    tracker = TemporalTracker(base_settings)
    
    # Neutral pose
    m = tracker.update(_feat(0.3, pitch=0.0, yaw=0.0, roll=0.0), 1.0)
    assert m.smooth_pitch == 0.0
    assert m.smooth_yaw == 0.0
    
    # Positive transition
    m = tracker.update(_feat(0.3, pitch=170.0, yaw=170.0, roll=170.0), 1.1)
    assert m.smooth_pitch == 170.0
    
    # Over the boundary to negative
    m = tracker.update(_feat(0.3, pitch=-170.0, yaw=-175.0, roll=-179.0), 1.2)
    assert m.smooth_pitch == -170.0
    assert m.smooth_yaw == -175.0
    
    # Repeated transitions across the boundary
    for i in range(10):
        m = tracker.update(_feat(0.3, pitch=175.0, yaw=-175.0, roll=30.0), 1.3 + i*0.2)
        assert -180 <= m.smooth_pitch <= 180
        m = tracker.update(_feat(0.3, pitch=-175.0, yaw=175.0, roll=-30.0), 1.4 + i*0.2)
        assert -180 <= m.smooth_pitch <= 180
        assert -180 <= m.smooth_yaw <= 180
        
    # The actual saved values should also strictly be bounded to the raw input range
    assert -180 <= tracker.prev_pitch <= 180
    assert -180 <= tracker.prev_yaw <= 180
    assert -180 <= tracker.prev_roll <= 180

def test_tracker_angular_diff_preserves_blink_thresholds(base_settings):
    tracker = TemporalTracker(base_settings)
    
    # Establish open eyes and pose (need 3 frames to fill EAR smoothing buffer)
    tracker.update(_feat(0.3, pitch=170.0, yaw=0.0, roll=0.0), 1.0)
    tracker.update(_feat(0.3, pitch=170.0, yaw=0.0, roll=0.0), 1.1)
    tracker.update(_feat(0.3, pitch=170.0, yaw=0.0, roll=0.0), 1.2)
    
    # Start closing eyes, but keep pose steady so we enter closure successfully
    tracker.update(_feat(0.1, pitch=170.0, yaw=0.0, roll=0.0), 1.3)
    tracker.update(_feat(0.1, pitch=170.0, yaw=0.0, roll=0.0), 1.4)
    
    # Now that we are closed, jump the pose across boundary: 170 -> -170
    tracker.update(_feat(0.1, pitch=-170.0, yaw=0.0, roll=0.0), 1.5)
    assert tracker.blink_candidate_valid is False
    
    # Start over
    tracker = TemporalTracker(base_settings)
    tracker.update(_feat(0.3, pitch=175.0, yaw=0.0, roll=0.0), 1.0)
    tracker.update(_feat(0.3, pitch=175.0, yaw=0.0, roll=0.0), 1.1)
    tracker.update(_feat(0.3, pitch=175.0, yaw=0.0, roll=0.0), 1.2)
    
    # Start closing eyes
    tracker.update(_feat(0.1, pitch=175.0, yaw=0.0, roll=0.0), 1.3)
    tracker.update(_feat(0.1, pitch=175.0, yaw=0.0, roll=0.0), 1.4)
    # Jump by 10 degrees (+175 -> -175 = 10)
    tracker.update(_feat(0.1, pitch=-175.0, yaw=0.0, roll=0.0), 1.5)
    assert tracker.blink_candidate_valid is True
