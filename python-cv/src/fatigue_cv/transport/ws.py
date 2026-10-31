import json
import logging
import threading
import time
from typing import Dict, Any
import cv2
from websocket import create_connection
from .base import Transport

logger = logging.getLogger(__name__)

class WebSocketTransport(Transport):
    def __init__(self, url: str = "ws://localhost:3000/ws?role=publisher"):
        self.url = url
        self.ws = None
        self.connect()

    def connect(self):
        try:
            self.ws = create_connection(self.url, timeout=2)
            logger.info(f"Connected to {self.url}")
        except Exception as e:
            logger.error(f"WebSocket connect fail: {e}")
            self.ws = None

    def send(self, payload: Dict[str, Any]) -> None:
        if not self.ws:
            self.connect()
            
        if self.ws:
            try:
                self.ws.send(json.dumps(payload))
            except Exception as e:
                logger.error(f"WebSocket send fail: {e}. Dropping connection.")
                try:
                    self.ws.close()
                except Exception:
                    logger.debug("WebSocket close after send failure failed.", exc_info=True)
                self.ws = None

    def close(self) -> None:
        if self.ws:
            self.ws.close()
            self.ws = None


class CameraFrameTransport:
    """Publishes JPEG frames on a separate socket from JSON telemetry."""

    def __init__(self, url: str = "ws://localhost:3000/ws?role=frame-publisher"):
        self.url = url
        self.ws = None
        self._condition = threading.Condition()
        self._latest_frame = None
        self._closed = False
        self._sender_thread = threading.Thread(
            target=self._send_latest_frames,
            name="camera-frame-sender",
            daemon=True,
        )
        self._sender_thread.start()

    def connect(self):
        try:
            self.ws = create_connection(self.url, timeout=2)
            logger.info("Connected to camera frame transport.")
        except Exception as e:
            logger.error(f"Camera frame transport connect failed: {e}")
            self.ws = None

    def send(self, frame) -> None:
        """Replace the pending frame; never queue stale previews."""
        with self._condition:
            self._latest_frame = frame.copy()
            self._condition.notify()

    def _send_latest_frames(self) -> None:
        next_frame_at = 0.0
        while True:
            with self._condition:
                while self._latest_frame is None and not self._closed:
                    self._condition.wait()
                if self._closed:
                    return
                frame = self._latest_frame
                self._latest_frame = None

            now = time.monotonic()
            if now < next_frame_at:
                time.sleep(next_frame_at - now)

            try:
                preview = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
                encoded, jpeg_buffer = cv2.imencode(
                    ".jpg", preview, [int(cv2.IMWRITE_JPEG_QUALITY), 70]
                )
                if not encoded:
                    continue
                if not self.ws:
                    self.connect()
                if self.ws:
                    self.ws.send(jpeg_buffer.tobytes(), opcode=2)
                    next_frame_at = time.monotonic() + 0.1
            except Exception as e:
                logger.error(f"Camera frame send failed: {e}. Dropping connection.")
                try:
                    if self.ws:
                        self.ws.close()
                except Exception:
                    logger.debug("Camera frame close after send failure failed.", exc_info=True)
                self.ws = None

    def close(self) -> None:
        with self._condition:
            self._closed = True
            self._latest_frame = None
            self._condition.notify_all()
        if self.ws:
            self.ws.close()
            self.ws = None
        self._sender_thread.join(timeout=2)
