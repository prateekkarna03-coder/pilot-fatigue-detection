# c:\Users\prate\Desktop\Semester\5 Sem\Ai\Project\pilot-fatigue-system\python-cv\src\fatigue_cv\dataset_extractor.py
import cv2
import csv
import logging
import os
from typing import List, Dict, Any, Tuple
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker
from fatigue_cv.features.eye import calculate_ear, calculate_eye_ears
from fatigue_cv.features.mouth import calculate_mar
from fatigue_cv.features.head_pose import calculate_head_pose
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.tracker import TemporalTracker

logging.basicConfig(level=logging.INFO)

KSS_MAPPING = {
    0: "Alert",
    5: "Low Vigilant",
    10: "Drowsy"
}

class DatasetExtractor:
    def __init__(self, model_path: str = "models/face_landmarker.task"):
        self.settings = AppSettings()
        # Ensure we point to the correct model path if needed
        self.settings.detection.model_path = model_path
        
        self.detector = MediaPipeFaceLandmarker(
            model_path=self.settings.detection.model_path,
            min_detection_confidence=self.settings.detection.min_face_detection_confidence,
            min_presence_confidence=self.settings.detection.min_face_presence_confidence
        )

    def process_video(self, video_path: str, subject_id: str, kss_label: int):
        video_name = os.path.basename(video_path)
        class_name = KSS_MAPPING.get(kss_label, "Unknown")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logging.error(f"Cannot open video {video_path}")
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps == 0 or fps != fps: # Handle nan or 0 fps
            fps = 30.0

        # Create a fresh tracker for each video so metrics don't leak between videos
        tracker = TemporalTracker(self.settings.temporal)
        
        frame_number = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            timestamp = frame_number / fps
            raw_landmarks = self.detector.process(frame)
            
            features = None
            if raw_landmarks:
                h, w, _ = frame.shape
                ear = calculate_ear(raw_landmarks)
                left_ear, right_ear = calculate_eye_ears(raw_landmarks)
                mar = calculate_mar(raw_landmarks)
                pitch, yaw, roll = calculate_head_pose(raw_landmarks, w, h)
                
                features = FeaturesResult(
                    ear=ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll,
                    left_ear=left_ear, right_ear=right_ear
                )
            
            # temporal tracks metrics over time, even when features is None, 
            # so we always update the tracker with current timestamp
            metrics = tracker.update(features, timestamp)
            
            row = {
                "subject_id": subject_id,
                "video_name": video_name,
                "kss_label": kss_label,
                "class_name": class_name,
                "frame_number": frame_number,
                "timestamp": timestamp,
                "ear": features.ear if features else None,
                "mar": features.mar if features else None,
                "pitch": metrics.smooth_pitch,
                "yaw": metrics.smooth_yaw,
                "roll": metrics.smooth_roll,
                "total_blinks": metrics.total_blinks,
                "blink_rate_per_minute": metrics.blink_rate_per_minute,
                "current_closure_duration": metrics.current_closure_duration,
                "is_prolonged_closure": metrics.is_prolonged_closure,
                "total_yawns": metrics.total_yawns,
                "yawn_rate_per_minute": metrics.yawn_rate_per_minute,
                "is_yawning": metrics.is_yawning
            }
            yield row
            frame_number += 1
                
        cap.release()

    def extract_and_save(self, video_configs: List[Tuple[str, str, int]], output_csv: str):
        # video_configs: list of (video_path, subject_id, kss_label)
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        
        fieldnames = [
            "subject_id", "video_name", "kss_label", "class_name", 
            "frame_number", "timestamp", "ear", "mar", "pitch", "yaw", "roll",
            "total_blinks", "blink_rate_per_minute", "current_closure_duration", 
            "is_prolonged_closure", "total_yawns", "yawn_rate_per_minute", "is_yawning"
        ]
        
        with open(output_csv, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for video_path, subject_id, kss_label in video_configs:
                logging.info(f"Starting extraction for {video_path}")
                frames_processed = 0
                for row in self.process_video(video_path, subject_id, kss_label):
                    writer.writerow(row)
                    frames_processed += 1
                    
                    if frames_processed % 1000 == 0:
                        f.flush()
                        logging.info(f"Processed {frames_processed} frames for {os.path.basename(video_path)} and flushed to disk")

                logging.info(f"Completed {video_path}, extracted {frames_processed} frames.")

    def close(self):
        self.detector.close()
