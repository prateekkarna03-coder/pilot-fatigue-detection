import cv2
import time
import logging
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.camera.capture import CameraStream
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker
from fatigue_cv.features.eye import calculate_eye_ears
from fatigue_cv.features.mouth import calculate_mar
from fatigue_cv.features.head_pose import calculate_head_pose
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.tracker import TemporalTracker
from fatigue_cv.prediction.model import FatiguePredictor
from fatigue_cv.prediction.buffer import PredictionBuffer

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
    
    # ML Setup
    model_path = r"E:\UTA-RLDD\models\fatigue_final.joblib"
    predictor = FatiguePredictor(model_path=model_path)
    buffer = PredictionBuffer(window_duration=10.0)

    logging.info("Starting webcam demo with Live ML Inference...")
    if not camera.open():
        logging.error("Could not initialize camera.")
        detector.close()
        return

    try:
        last_diagnostic_print = 0.0
        
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
                left_ear, right_ear = calculate_eye_ears(raw_landmarks)
                ear = (left_ear + right_ear) / 2.0
                mar = calculate_mar(raw_landmarks)
                pitch, yaw, roll = calculate_head_pose(raw_landmarks, w, h)
                
                features = FeaturesResult(
                    ear=ear, mar=mar, pitch=pitch, yaw=yaw, roll=roll,
                    left_ear=left_ear, right_ear=right_ear
                )
                
                cv2.putText(frame, f"EAR: {features.ear:.3f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"MAR: {features.mar:.3f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Pitch: {features.pitch:.1f}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Yaw: {features.yaw:.1f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Roll: {features.roll:.1f}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                cv2.putText(frame, "No face detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                
            metrics = tracker.update(features, current_time)
            
            # Buffer rolling predictions
            buffer.add(current_time, features, metrics)
            
            prediction_text = "Buffering..."
            prediction_color = (200, 200, 200)
            
            try:
                aggregated_input = buffer.get_aggregated_input()
                prediction = predictor.predict(aggregated_input)
                
                prediction_text = f"Fatigue: {prediction.fatigue_state} (KSS {prediction.kss_label})"
                if prediction.kss_label == 0:
                    prediction_color = (0, 255, 0)
                elif prediction.kss_label == 5:
                    prediction_color = (0, 165, 255) # Orange
                else:
                    prediction_color = (0, 0, 255) # Red
                    
                # Display probability breakdown safely
                y_offset = 150
                for kss, prob in prediction.class_probabilities.items():
                    cv2.putText(frame, f"KSS {kss}: {prob:.2f}", (320, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                    y_offset += 25
                    
            except ValueError as ve:
                prediction_text = f"Wait: No Face Data"
            except Exception as e:
                logging.error(f"ML Pipeline Failure: {e}")
                prediction_text = "ML ERROR"
                prediction_color = (0, 0, 255)
            
            # Draw temporal info
            cv2.putText(frame, f"Blinks: {metrics.total_blinks} ({metrics.blink_rate_per_minute:.1f}/min)", (320, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Yawns: {metrics.total_yawns} ({metrics.yawn_rate_per_minute:.1f}/min)", (320, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            cv2.putText(frame, f"Clos dur: {metrics.current_closure_duration:.2f}s", (320, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255) if metrics.is_prolonged_closure else (255, 255, 0), 2)
            cv2.putText(frame, prediction_text, (320, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, prediction_color, 2)
            
            cv2.imshow("Webcam Demo", frame)
            
            # Print physical diagnostic telemetry safely decoupled from ML features (3 fps throttle)
            if settings.diagnostic_mode and metrics.diagnostic_data and (current_time - last_diagnostic_print > 0.33):
                d = metrics.diagnostic_data
                print("\n--- [DIAGNOSTIC ACTIVE] ---")
                print(f"Timestamp: {d['timestamp']:.3f} | Total Blinks: {d['total_blinks']}")
                print(f"EAR (Raw): {d['raw_ear']:.4f} | Baseline EAR: {d['baseline_ear']:.4f}")
                print(f"Close Threshold: {d['close_threshold']:.4f} | Open Threshold: {d.get('open_threshold')}")
                print(f"Pitch: {d['pitch']:.2f} | Yaw: {d['yaw']:.2f} | Valid Frame: {d['is_valid_blink_frame']}")
                print(f"State: {d['eye_state']} | Clo_Start: {d['closure_start_ts']:.3f} | Dur: {d['current_closure_duration']:.2f}s | Blink Emitted: {d['blink_event_emitted']}")
                last_diagnostic_print = current_time
            
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
