"""Optional phone detection, local event persistence, and SMTP notifications."""
from __future__ import annotations

import queue
import smtplib
import sqlite3
import threading
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
import requests

import config


@dataclass
class PhoneDetection:
    bbox: Tuple[int, int, int, int]
    confidence: float


class EventDatabase:
    """Store alert events and snapshot paths in a local SQLite database."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(self.path), timeout=10) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                kind TEXT NOT NULL,
                message TEXT NOT NULL,
                suspicion REAL NOT NULL,
                valence REAL NOT NULL,
                snapshot_path TEXT
            )""")
            db.commit()

    def record(self, timestamp: str, kind: str, message: str, suspicion: float,
               valence: float, snapshot_path: Optional[str]) -> None:
        with sqlite3.connect(str(self.path), timeout=10) as db:
            db.execute(
                "INSERT INTO events(timestamp, kind, message, suspicion, valence, snapshot_path) VALUES (?, ?, ?, ?, ?, ?)",
                (timestamp, kind, message, float(suspicion), float(valence), snapshot_path),
            )
            db.commit()


class EmailNotifier:
    """Send opt-in event email in a worker thread so the camera loop stays responsive."""

    def __init__(self) -> None:
        self.host = config.SMTP_HOST
        self.port = config.SMTP_PORT
        self.username = config.SMTP_USERNAME
        self.password = config.SMTP_PASSWORD
        self.sender = config.ALERT_FROM_EMAIL or self.username
        self.recipient = config.ADMIN_EMAIL
        self.use_ssl = config.SMTP_USE_SSL
        self.starttls = config.SMTP_STARTTLS
        self.enabled = bool(self.host and self.port and self.sender and self.recipient)
        self._queue: queue.Queue = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._log = None

    def start(self, logger) -> None:
        self._log = logger
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._worker, name="email-alerts", daemon=True)
        self._thread.start()
        logger.ok(f"Email alerts enabled for admin address {self.recipient}.")

    def send_event(self, *, timestamp: str, kind: str, message: str, suspicion: float,
                   valence: float, snapshot_path: Optional[str]) -> None:
        if self.enabled:
            self._queue.put((timestamp, kind, message, suspicion, valence, snapshot_path))

    def stop(self) -> None:
        if self._thread is not None:
            self._queue.put(None)
            self._thread.join(timeout=20)
            self._thread = None

    def _worker(self) -> None:
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                timestamp, kind, message, suspicion, valence, snapshot_path = item
                self._send(timestamp, kind, message, suspicion, valence, snapshot_path)
            finally:
                self._queue.task_done()

    def _send(self, timestamp: str, kind: str, message: str, suspicion: float,
              valence: float, snapshot_path: Optional[str]) -> None:
        mail = EmailMessage()
        mail["Subject"] = f"Possible proctoring policy event: {kind.replace('_', ' ').lower()}"
        mail["From"] = self.sender
        mail["To"] = self.recipient
        mail.set_content(
            "A possible policy event was detected. This automated signal is not a final determination.\n\n"
            f"Time: {timestamp}\nEvent: {message}\nSuspicion heuristic: {suspicion:.0f}/100\n"
            f"Valence heuristic: {valence:+.2f}\n"
            "Please review the evidence and follow your institution's process."
        )
        if snapshot_path:
            try:
                path = Path(snapshot_path)
                if path.is_file():
                    mail.add_attachment(path.read_bytes(), maintype="image", subtype="jpeg", filename=path.name)
            except OSError as exc:
                self._log.warn(f"Could not attach alert snapshot to email: {exc}")
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.host, self.port, timeout=15) as smtp:
                    if self.username:
                        smtp.login(self.username, self.password)
                    smtp.send_message(mail)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
                    smtp.ehlo()
                    if self.starttls:
                        smtp.starttls()
                        smtp.ehlo()
                    if self.username:
                        smtp.login(self.username, self.password)
                    smtp.send_message(mail)
            self._log.ok(f"Email alert delivered for: {message}")
        except (OSError, smtplib.SMTPException) as exc:
            self._log.error(f"Email alert failed: {exc}")


class PhoneDetector:
    """Detect the COCO 'cell phone' class with a small YOLOv4-tiny OpenCV DNN."""

    PHONE_CLASS_ID = 67
    INPUT_SIZE = (416, 416)
    WEIGHTS_URL = "https://github.com/AlexeyAB/darknet/releases/download/yolov4/yolov4-tiny.weights"
    CONFIG_URL = "https://raw.githubusercontent.com/AlexeyAB/darknet/master/cfg/yolov4-tiny.cfg"

    def __init__(self, logger) -> None:
        self.logger = logger
        self.net = None
        self.output_layers: List[str] = []
        self.confidence_threshold = config.PHONE_CONFIDENCE
        self.enabled = config.PHONE_DETECTION_ENABLED
        if not self.enabled:
            logger.info("Phone detection is disabled by configuration.")
            return
        weights = config.PHONE_MODEL_DIR / "yolov4-tiny.weights"
        model_cfg = config.PHONE_MODEL_DIR / "yolov4-tiny.cfg"
        try:
            self._ensure_file(weights, self.WEIGHTS_URL, 10_000_000)
            self._ensure_file(model_cfg, self.CONFIG_URL, 1_000)
            self.net = cv2.dnn.readNetFromDarknet(str(model_cfg), str(weights))
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
            layer_names = self.net.getLayerNames()
            self.output_layers = [layer_names[int(i) - 1] for i in self.net.getUnconnectedOutLayers().flatten()]
            logger.ok("Phone detector ready (COCO cell-phone class).")
        except Exception as exc:  # model download/load failures must not disable face monitoring
            self.net = None
            logger.warn(f"Phone detection unavailable; face monitoring will continue: {exc}")

    @staticmethod
    def _ensure_file(path: Path, url: str, min_bytes: int) -> None:
        if path.is_file() and path.stat().st_size >= min_bytes:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        try:
            with requests.get(url, stream=True, timeout=(15, 180)) as response:
                response.raise_for_status()
                with temporary.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
            if temporary.stat().st_size < min_bytes:
                raise RuntimeError(f"downloaded model file is too small: {path.name}")
            temporary.replace(path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def detect(self, frame: np.ndarray) -> List[PhoneDetection]:
        if self.net is None:
            return []
        height, width = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(frame, 1.0 / 255.0, self.INPUT_SIZE, swapRB=True, crop=False)
        self.net.setInput(blob)
        outputs = self.net.forward(self.output_layers)
        boxes: List[List[int]] = []
        scores: List[float] = []
        for output in outputs:
            for row in output:
                if row.shape[0] <= self.PHONE_CLASS_ID + 5:
                    continue
                score = float(row[4]) * float(row[5 + self.PHONE_CLASS_ID])
                if score < self.confidence_threshold:
                    continue
                center_x, center_y = float(row[0]) * width, float(row[1]) * height
                box_w, box_h = float(row[2]) * width, float(row[3]) * height
                x, y = int(center_x - box_w / 2), int(center_y - box_h / 2)
                boxes.append([x, y, int(box_w), int(box_h)])
                scores.append(score)
        if not boxes:
            return []
        kept = cv2.dnn.NMSBoxes(boxes, scores, self.confidence_threshold, 0.4)
        detections: List[PhoneDetection] = []
        for index in np.asarray(kept).reshape(-1):
            x, y, box_w, box_h = boxes[int(index)]
            detections.append(PhoneDetection(
                bbox=(max(0, x), max(0, y), min(width - 1, x + box_w), min(height - 1, y + box_h)),
                confidence=scores[int(index)],
            ))
        return detections
