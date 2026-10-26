"""Central configuration for the local webcam proctoring application.

Secrets are read from a private local `.env` file or environment variables.
All optional integrations remain local/offline unless explicitly configured.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return default if value is None else value.strip()


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name: str, default: int) -> int:
    try:
        return int(float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return int(default)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _secret(name: str) -> str:
    value = _env_str(name)
    if value.lower().startswith(("your_", "paste_", "<")):
        return ""
    return value


# Optional Telegram alerts
TELEGRAM_BOT_TOKEN = _secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = _secret("TELEGRAM_CHAT_ID")
ALERT_COOLDOWN_SECONDS = _env_float("ALERT_COOLDOWN_SECONDS", 5.0)

# Optional email: use an SMTP app password, not your normal account password.
SMTP_HOST = _env_str("SMTP_HOST")
SMTP_PORT = _env_int("SMTP_PORT", 587)
SMTP_USERNAME = _secret("SMTP_USERNAME")
SMTP_PASSWORD = _secret("SMTP_PASSWORD")
ALERT_FROM_EMAIL = _env_str("ALERT_FROM_EMAIL")
ADMIN_EMAIL = _env_str("ADMIN_EMAIL")
SMTP_USE_SSL = _env_bool("SMTP_USE_SSL", False)
SMTP_STARTTLS = _env_bool("SMTP_STARTTLS", True)

# Webcam and display
CAMERA_INDEX = _env_int("CAMERA_INDEX", 0)
FRAME_WIDTH = _env_int("FRAME_WIDTH", 640)
FRAME_HEIGHT = _env_int("FRAME_HEIGHT", 480)
FLIP_FRAME = _env_bool("FLIP_FRAME", False)
SHOW_WINDOW = _env_bool("SHOW_WINDOW", True)

# Face detection back-end: auto | legacy | tasks | haar
FACE_BACKEND = _env_str("FACE_BACKEND", "auto").lower()
MAX_FACES = _env_int("MAX_FACES", 4)
FACE_LANDMARKER_MODEL_PATH = Path(_env_str(
    "FACE_LANDMARKER_MODEL_PATH", str(BASE_DIR / "models" / "face_landmarker.task")
))
FACE_LANDMARKER_MODEL_URL = _env_str(
    "FACE_LANDMARKER_MODEL_URL",
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
)

# Phone detection (COCO cell-phone object class via OpenCV DNN)
PHONE_DETECTION_ENABLED = _env_bool("PHONE_DETECTION_ENABLED", True)
PHONE_CONFIDENCE = _env_float("PHONE_CONFIDENCE", 0.35)
PHONE_CONFIRM_SECONDS = _env_float("PHONE_CONFIRM_SECONDS", 0.35)
PHONE_MODEL_DIR = Path(_env_str("PHONE_MODEL_DIR", str(BASE_DIR / "models")))

# Proctoring rules
LOOK_AWAY_SECONDS = _env_float("LOOK_AWAY_SECONDS", 2.0)
NO_FACE_SECONDS = _env_float("NO_FACE_SECONDS", 1.0)
MULTI_FACE_SECONDS = _env_float("MULTI_FACE_SECONDS", 0.5)
YAW_THRESHOLD_DEG = _env_float("YAW_THRESHOLD_DEG", 25.0)
PITCH_THRESHOLD_DEG = _env_float("PITCH_THRESHOLD_DEG", 18.0)
MIRROR_DIRECTIONS = _env_bool("MIRROR_DIRECTIONS", False)
CALIBRATION_FRAMES = _env_int("CALIBRATION_FRAMES", 30)
MOTION_WINDOW_SECONDS = _env_float("MOTION_WINDOW_SECONDS", 2.0)
MOTION_RANGE_DEG = _env_float("MOTION_RANGE_DEG", 45.0)
TALKING_MAR_STD = _env_float("TALKING_MAR_STD", 0.03)
EYES_CLOSED_SECONDS = _env_float("EYES_CLOSED_SECONDS", 1.5)
ALERT_ON_SUSPICIOUS_MOVEMENT = _env_bool("ALERT_ON_SUSPICIOUS_MOVEMENT", False)
SUSPICIOUS_SECONDS = _env_float("SUSPICIOUS_SECONDS", 3.0)

# Output
LOG_INTERVAL_SECONDS = _env_float("LOG_INTERVAL_SECONDS", 1.0)
SNAPSHOT_DIR = Path(_env_str("SNAPSHOT_DIR", str(BASE_DIR / "snapshots")))
DATABASE_PATH = Path(_env_str("DATABASE_PATH", str(BASE_DIR / "events.sqlite3")))
