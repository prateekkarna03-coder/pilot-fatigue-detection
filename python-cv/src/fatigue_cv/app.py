import cv2
import os
import time
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.camera.capture import CameraStream
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker
from fatigue_cv.features.eye import calculate_eye_ears
from fatigue_cv.features.mouth import calculate_mar
from fatigue_cv.features.head_pose import calculate_head_pose
from fatigue_cv.features.types import FeaturesResult
from fatigue_cv.temporal.tracker import TemporalTracker
from fatigue_cv.temporal.types import TemporalMetrics
from fatigue_cv.prediction.model import FatiguePredictor
from fatigue_cv.prediction.buffer import PredictionBuffer
from fatigue_cv.prediction.types import PredictionOutput
from fatigue_cv.transport.ws import WebSocketTransport, CameraFrameTransport
logging.basicConfig(level=logging.INFO)

def kss_to_fatigue_score(kss_label: int) -> float:
    """Convert the model's 0/5/10 KSS class to the dashboard's 0-100 scale."""
    return round((kss_label / 10.0) * 100, 1)

def should_dispatch_telemetry(
    last_dispatch_time: Optional[float],
    current_time: float,
    interval_seconds: float = 1.0,
) -> bool:
    """Determines whether enough time has elapsed to send the next telemetry sample."""
    if last_dispatch_time is None or last_dispatch_time < 0.0:
        return True
    return (current_time - last_dispatch_time) >= interval_seconds

def build_telemetry_payload(
    session_id: str,
    sequence: int,
    timestamp: str,
    prediction: PredictionOutput,
    features: Optional[FeaturesResult],
    metrics: TemporalMetrics,
) -> dict[str, Any]:
    """Constructs the standard telemetry payload dictionary for WS dispatch."""
    return {
        "sessionId": session_id,
        "sequence": sequence,
        "timestamp": timestamp,
        # The model's KSS classes are 0, 5, and 10. This is the
        # normalized model output shown by the dashboard.
        "fatigueScore": kss_to_fatigue_score(prediction.kss_label),
        "eyeClosurePercent": round(max(0, (0.35 - features.ear) * 400), 1) if features else 0,
        "blinkRatePerMin": metrics.blink_rate_per_minute,
        "yawnCount": metrics.total_yawns,
        "headPoseDeviation": round(abs(features.pitch) + abs(features.yaw) + abs(features.roll), 1) if features else 0,
        "alertsTriggered": 0,
        "kss": prediction.kss_label,
        "state": prediction.fatigue_state,
    }

def main():
    settings = AppSettings()
    telemetry_interval_seconds = float(
        os.environ.get("TELEMETRY_INTERVAL_SECONDS", settings.telemetry_interval_seconds)
    )
    
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
    session_id = os.environ.get("MONITORING_SESSION_ID")
    if not session_id:
        logging.error("MONITORING_SESSION_ID is missing; refusing to publish telemetry.")
        detector.close()
        return
    transport = WebSocketTransport("ws://localhost:3000/ws?role=publisher")
    frame_transport = CameraFrameTransport("ws://localhost:3000/ws?role=frame-publisher")

    logging.info("Starting webcam demo with Live ML Inference...")
    if not camera.open():
        logging.error("Could not initialize camera.")
        detector.close()
        frame_transport.close()
        return

    window_name = "Pilot Fatigue Monitor"
    native_window_available = True
    native_window_created = False
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, settings.camera.width, settings.camera.height)
        native_window_created = True
        logging.info("Native OpenCV webcam window opened.")
    except cv2.error as error:
        native_window_available = False
        logging.error("Native OpenCV webcam window is unavailable: %s", error)

    try:
        last_diagnostic_print = 0.0
        last_frame_publish = 0.0
        last_telemetry_publish: Optional[float] = None
        telemetry_sequence = 0
        
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
                
                if should_dispatch_telemetry(last_telemetry_publish, current_time, telemetry_interval_seconds):
                    telemetry_sequence += 1
                    telemetry_timestamp = datetime.now(timezone.utc).isoformat()
                    transport.send(build_telemetry_payload(
                        session_id=session_id,
                        sequence=telemetry_sequence,
                        timestamp=telemetry_timestamp,
                        prediction=prediction,
                        features=features,
                        metrics=metrics,
                    ))
                    last_telemetry_publish = current_time
                
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
            
            # Camera frames are streamed to the dashboard over a separate,
            # lightweight binary transport. No desktop OpenCV window is used.
            if current_time - last_frame_publish >= 0.1:
                frame_transport.send(frame)
                last_frame_publish = current_time

            if native_window_available:
                try:
                    cv2.imshow(window_name, frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        logging.info("Webcam window requested monitoring shutdown.")
                        break
                except cv2.error as error:
                    native_window_available = False
                    logging.error("Native OpenCV webcam window became unavailable: %s", error)
            
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
            
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.error(f"Error during webcam capture: {e}")
    finally:
        transport.close()
        frame_transport.close()
        logging.info("Releasing resources and destroying windows.")
        camera.close()
        detector.close()
        if native_window_created:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
