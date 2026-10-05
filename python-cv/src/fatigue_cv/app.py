import cv2
import time
import logging
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.camera.capture import CameraStream
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker
from fatigue_cv.features.eye import calculate_ear
from fatigue_cv.features.mouth import calculate_mar
from fatigue_cv.features.head_pose import calculate_head_pose
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.tracker import TemporalTracker

logging.basicConfig(level=logging.INFO)

def main():
    settings = AppSettings()
    
    detector = MediaPipeFaceLandmarker(
        model_path=settings.detection.model_path,
        min_detection_confidence=settings.detection.min_face_detection_confidence,
        min_presence_confidence=settings.detection.min_face_presence_confidence
    )
    
    camera = CameraStream(
        device_id=settings.camera.device_id,
        width=settings.camera.width,
        height=settings.camera.height,
        fps=settings.camera.fps
    )
    
    tracker = TemporalTracker(settings.temporal)

    logging.info("Starting webcam demo with Temporal Features...")
    if not camera.open():
        logging.error("Could not initialize camera.")
        detector.close()
        return

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                logging.warning("Failed to grab frame.")
                break
            
            raw_landmarks = detector.process(frame)
            current_time = time.time()
            features = None
            
            if raw_landmarks:
                h, w, _ = frame.shape
                ear = calculate_ear(raw_landmarks)
                mar = calculate_mar(raw_landmarks)
                pitch, yaw, roll = calculate_head_pose(raw_landmarks, w, h)
                
                features = FeaturesResult(ear=ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll)
                
                cv2.putText(frame, f"EAR: {features.ear:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"MAR: {features.mar:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Pitch: {features.pitch:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Yaw: {features.yaw:.1f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Roll: {features.roll:.1f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
            metrics = tracker.update(features, current_time)
            
            # Draw temporal info
            cv2.putText(frame, f"Blinks: {metrics.total_blinks} ({metrics.blink_rate_per_minute:.1f}/min)", (320, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Yawns: {metrics.total_yawns} ({metrics.yawn_rate_per_minute:.1f}/min)", (320, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Clos dur: {metrics.current_closure_duration:.2f}s", (320, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255) if metrics.is_prolonged_closure else (255, 255, 0), 2)
            
            cv2.imshow("Webcam Demo", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Quit signal received.")
                break
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.error(f"Error during webcam capture: {e}")
    finally:
        logging.info("Releasing resources and destroying windows.")
        camera.close()
        detector.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
