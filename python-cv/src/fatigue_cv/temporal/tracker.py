from typing import Optional
import collections
import statistics
from ..features.types import FeaturesResult
from .types import TemporalMetrics
from ..config.settings import TemporalSettings

class TemporalTracker:
    def __init__(self, settings: TemporalSettings):
        self.settings = settings
        
        self.eyes_closed = False
        self.eyes_closed_start_time = 0.0
        self.blink_candidate_valid = False
        self.closure_pose: Optional[tuple[float, float, float]] = None
        self.total_blinks = 0
        self.blink_timestamps: collections.deque[float] = collections.deque()
        
        self.mouth_open = False
        self.yawn_start_time = 0.0
        self.yawn_candidate_valid = False
        self.last_yawn_end_time = 0.0
        self.total_yawns = 0
        self.yawn_timestamps: collections.deque[float] = collections.deque()
        
        self.left_ear_history: collections.deque[tuple[float, float]] = collections.deque()
        self.right_ear_history: collections.deque[tuple[float, float]] = collections.deque()
        self.short_term_ear: collections.deque[float] = collections.deque(maxlen=3) # Smoothing buffer
        self.left_closed_history: collections.deque[bool] = collections.deque(maxlen=2)
        self.right_closed_history: collections.deque[bool] = collections.deque(maxlen=2)
        self.left_open_history: collections.deque[bool] = collections.deque(maxlen=2)
        self.right_open_history: collections.deque[bool] = collections.deque(maxlen=2)
        self.last_face_time = 0.0
        
        self.prev_pitch: Optional[float] = None
        self.prev_yaw: Optional[float] = None
        self.prev_roll: Optional[float] = None

    def _angular_diff(self, current: float, previous: Optional[float]) -> float:
        if previous is None:
            return 0.0
        diff = (current - previous + 180) % 360 - 180
        return abs(diff)

    def update(self, features: Optional[FeaturesResult], current_time: float) -> TemporalMetrics:
        # Clean up old timestamps outside window
        while self.blink_timestamps and (current_time - self.blink_timestamps[0] > self.settings.window_size):
            self.blink_timestamps.popleft()
        while self.yawn_timestamps and (current_time - self.yawn_timestamps[0] > self.settings.window_size):
            self.yawn_timestamps.popleft()

        if not features:
            if current_time - self.last_face_time > getattr(self.settings, 'missing_grace_period', 0.5):
                self.eyes_closed = False
                self.eyes_closed_start_time = 0.0
                self.blink_candidate_valid = False
                self.closure_pose = None
                
                self.mouth_open = False
                self.yawn_start_time = 0.0
                self.yawn_candidate_valid = False
                
                self.short_term_ear.clear()
                self.left_closed_history.clear()
                self.right_closed_history.clear()
                self.left_open_history.clear()
                self.right_open_history.clear()
                
            current_closure = (current_time - self.eyes_closed_start_time) if self.eyes_closed else 0.0
            
            return TemporalMetrics(
                total_blinks=self.total_blinks,
                blink_rate_per_minute=self._calculate_rate(len(self.blink_timestamps)),
                current_closure_duration=current_closure,
                is_prolonged_closure=current_closure >= self.settings.prolonged_closure_time if self.eyes_closed else False,
                
                total_yawns=self.total_yawns,
                yawn_rate_per_minute=self._calculate_rate(len(self.yawn_timestamps)),
                is_yawning=getattr(self, 'yawn_candidate_valid', False),
                
                smooth_pitch=self.prev_pitch or 0.0,
                smooth_yaw=self.prev_yaw or 0.0,
                smooth_roll=self.prev_roll or 0.0
            )

        self.last_face_time = current_time
        previous_pose = (self.prev_pitch, self.prev_yaw, self.prev_roll)
        self.prev_pitch = features.pitch
        self.prev_yaw = features.yaw
        self.prev_roll = features.roll
        pose_change_threshold = getattr(self.settings, 'pose_change_threshold', 15.0)
        
        # 3. Smooth short-term EAR noise safely
        self.short_term_ear.append(features.ear)
        smoothed_ear = sum(self.short_term_ear) / len(self.short_term_ear)

        left_ear = features.left_ear if features.left_ear is not None else features.ear
        right_ear = features.right_ear if features.right_ear is not None else features.ear
        bilateral_data = features.left_ear is not None and features.right_ear is not None

        # 4. Personal per-eye open-eye baselines from valid open-eye frames
        baseline_window = getattr(self.settings, 'dynamic_baseline_time', 10.0)
        while self.left_ear_history and (current_time - self.left_ear_history[0][0] > baseline_window):
            self.left_ear_history.popleft()
        while self.right_ear_history and (current_time - self.right_ear_history[0][0] > baseline_window):
            self.right_ear_history.popleft()
            
        left_baseline_ear = (
            statistics.median_low(ear for _, ear in self.left_ear_history)
            if self.left_ear_history else left_ear
        )
        right_baseline_ear = (
            statistics.median_low(ear for _, ear in self.right_ear_history)
            if self.right_ear_history else right_ear
        )
        
        left_close_threshold = left_baseline_ear * getattr(self.settings, 'ear_drop_ratio', 0.75)
        right_close_threshold = right_baseline_ear * getattr(self.settings, 'ear_drop_ratio', 0.75)
        left_open_threshold = left_baseline_ear * getattr(self.settings, 'ear_open_ratio', 0.85)
        right_open_threshold = right_baseline_ear * getattr(self.settings, 'ear_open_ratio', 0.85)

        if bilateral_data:
            self.left_closed_history.append(left_ear < left_close_threshold)
            self.right_closed_history.append(right_ear < right_close_threshold)
            self.left_open_history.append(left_ear >= left_open_threshold)
            self.right_open_history.append(right_ear >= right_open_threshold)
            bilateral_closed = (
                any(self.left_closed_history) and any(self.right_closed_history)
            )
            bilateral_open = (
                any(self.left_open_history) and any(self.right_open_history)
            )
        else:
            baseline_ear = (
                statistics.median_low(ear for _, ear in self.left_ear_history)
                if self.left_ear_history else smoothed_ear
            )
            ear_close_threshold = baseline_ear * getattr(self.settings, 'ear_drop_ratio', 0.75)
            ear_open_threshold = baseline_ear * getattr(self.settings, 'ear_open_ratio', 0.85)
            bilateral_closed = smoothed_ear < ear_close_threshold
            bilateral_open = smoothed_ear >= ear_open_threshold

        current_closure_duration = 0.0
        is_prolonged = False
        blink_event_emitted = False

        if self.eyes_closed:
            # Enforce closure length
            current_closure_duration = current_time - self.eyes_closed_start_time
            
            if self.closure_pose is not None:
                pose_change = max(
                    self._angular_diff(self.prev_pitch, self.closure_pose[0]),
                    self._angular_diff(self.prev_yaw, self.closure_pose[1]),
                    self._angular_diff(self.prev_roll, self.closure_pose[2]),
                )
                if pose_change > getattr(self.settings, 'pose_change_threshold', 15.0):
                    self.blink_candidate_valid = False

            eyes_open = bilateral_open
            if eyes_open:
                self.eyes_closed = False
                
                valid_min = getattr(self.settings, 'blink_min_duration', 0.05)
                valid_max = getattr(self.settings, 'blink_max_duration', 0.6)
                
                if (
                    valid_min <= current_closure_duration <= valid_max
                    and self.blink_candidate_valid
                ):
                    self.blink_timestamps.append(current_time)
                    self.total_blinks += 1
                    blink_event_emitted = True
                
                self.eyes_closed_start_time = 0.0
                self.blink_candidate_valid = False
                self.closure_pose = None
                current_closure_duration = 0.0
            else:
                if current_closure_duration >= self.settings.prolonged_closure_time:
                    is_prolonged = True
        else:
            eyes_closed = bilateral_closed
            if eyes_closed:
                self.eyes_closed = True
                self.eyes_closed_start_time = current_time
                self.left_open_history.clear()
                self.right_open_history.clear()
                pose_changed_into_closure = (
                    previous_pose[0] is not None
                    and max(
                        self._angular_diff(self.prev_pitch, previous_pose[0]),
                        self._angular_diff(self.prev_yaw, previous_pose[1]),
                        self._angular_diff(self.prev_roll, previous_pose[2]),
                    ) > pose_change_threshold
                )
                self.blink_candidate_valid = not pose_changed_into_closure
                self.closure_pose = (self.prev_pitch, self.prev_yaw, self.prev_roll)

        if not self.eyes_closed:
            self.left_ear_history.append((current_time, left_ear))
            self.right_ear_history.append((current_time, right_ear))

        diagnostic = {
            "timestamp": current_time,
            "raw_ear": features.ear,
            "baseline_ear": (left_baseline_ear + right_baseline_ear) / 2.0,
            "left_baseline_ear": left_baseline_ear,
            "right_baseline_ear": right_baseline_ear,
            "close_threshold": (left_close_threshold + right_close_threshold) / 2.0,
            "open_threshold": (left_open_threshold + right_open_threshold) / 2.0,
            "pitch": features.pitch,
            "yaw": features.yaw,
            "is_valid_blink_frame": self.blink_candidate_valid,
            "eye_state": "CLOSED" if self.eyes_closed else "OPEN",
            "closure_start_ts": self.eyes_closed_start_time,
            "current_closure_duration": current_closure_duration,
            "blink_event_emitted": blink_event_emitted,
            "total_blinks": self.total_blinks
        }

        # Mouth logic
        is_currently_yawning = features.mar > self.settings.mar_threshold
        
        if is_currently_yawning:
            if not self.mouth_open:
                if current_time - self.last_yawn_end_time >= self.settings.yawn_cooldown:
                    self.mouth_open = True
                    self.yawn_start_time = current_time
            else:
                if current_time - self.yawn_start_time >= self.settings.yawn_min_duration:
                    self.yawn_candidate_valid = True
        else:
            if self.mouth_open:
                if self.yawn_candidate_valid:
                    self.total_yawns += 1
                    self.yawn_timestamps.append(current_time)
                    self.last_yawn_end_time = current_time
                self.mouth_open = False
                self.yawn_candidate_valid = False

        return TemporalMetrics(
            total_blinks=self.total_blinks,
            blink_rate_per_minute=self._calculate_rate(len(self.blink_timestamps)),
            current_closure_duration=current_closure_duration,
            is_prolonged_closure=is_prolonged,
            
            total_yawns=self.total_yawns,
            yawn_rate_per_minute=self._calculate_rate(len(self.yawn_timestamps)),
            is_yawning=self.yawn_candidate_valid,
            
            smooth_pitch=self.prev_pitch,
            smooth_yaw=self.prev_yaw,
            smooth_roll=self.prev_roll,
            diagnostic_data=diagnostic
        )
        
    def _calculate_rate(self, count: int) -> float:
        if self.settings.window_size <= 0:
            return 0.0
        return (count / self.settings.window_size) * 60.0
