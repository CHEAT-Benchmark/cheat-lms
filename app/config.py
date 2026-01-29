import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ASSESSMENTS_DIR = BASE_DIR / "assessments"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cheat-lms-dev-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATA_DIR / 'lms.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TELEMETRY_ENABLED = True
    TELEMETRY_LOG_FILE = DATA_DIR / "telemetry.jsonl"
    BEHAVIORAL_TELEMETRY_FILE = DATA_DIR / "behavioral_telemetry.jsonl"

    # Session cookie settings for tunnel/external access compatibility
    SESSION_COOKIE_SAMESITE = "None"  # Allow cookies through tunnel
    SESSION_COOKIE_SECURE = True  # Required when SameSite=None (tunnel uses HTTPS)
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "None"
    REMEMBER_COOKIE_SECURE = True
