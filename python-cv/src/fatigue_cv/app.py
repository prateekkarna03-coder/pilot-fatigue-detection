import cv2
import logging
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.camera.capture import CameraStream
from fatigue_cv.detection.face_landmarker import MediaPipeFaceLandmarker

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

    logging.info("Starting webcam demo with Face Landmarks...")
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
            
            # Process frame for landmarks
            landmarks = detector.process(frame)
            
            if landmarks:
                # Optionally draw a few landmarks to verify MediaPipe works
                h, w, _ = frame.shape
                # Drawing just a few key points, e.g. nose tip (1)
                for pt in landmarks.points[::20]: # skip points to reduce clutter
                    x = int(pt.x * w)
                    y = int(pt.y * h)
                    cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)
            
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
