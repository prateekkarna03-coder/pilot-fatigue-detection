import cv2
import logging
from fatigue_cv.config.settings import AppSettings
from fatigue_cv.camera.capture import CameraStream

logging.basicConfig(level=logging.INFO)

def main():
    settings = AppSettings()
    
    # Initialize camera using settings
    camera = CameraStream(
        device_id=settings.camera.device_id,
        width=settings.camera.width,
        height=settings.camera.height,
        fps=settings.camera.fps
    )

    logging.info("Starting webcam demo...")
    if not camera.open():
        logging.error("Could not initialize camera.")
        return

    try:
        while True:
            frame = camera.read_frame()
            if frame is None:
                logging.warning("Failed to grab frame.")
                break
            
            # Display live frames using OpenCV
            cv2.imshow("Webcam Demo", frame)
            
            # Exit when user presses 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logging.info("Quit signal received.")
                break
    except KeyboardInterrupt:
        logging.info("Interrupted by user.")
    except Exception as e:
        logging.error(f"Error during webcam capture: {e}")
    finally:
        logging.info("Releasing camera and destroying windows.")
        camera.close()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
