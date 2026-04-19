"""
config.py
---------
Centralised configuration for the Kishaan Deepak application.
All tuneable constants and environment-variable bindings live here so that
no magic numbers are scattered across the codebase.
"""

import os
from dotenv import load_dotenv

# Load .env from the project root (parent of this file)
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


# ── Directory layout ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODELS_DIR      = os.path.join(BASE_DIR, "models")
UPLOAD_FOLDER   = os.path.join(BASE_DIR, "uploads")
DATA_DIR        = os.path.join(BASE_DIR, "data")
DATASET_DIR     = os.path.join(BASE_DIR, "dataset")   # for retraining
LOG_DIR         = os.path.join(BASE_DIR, "logs")

# ── Model file paths ──────────────────────────────────────────────────────────
YIELD_MODEL_PATH   = os.path.join(MODELS_DIR, "crop_yield_model.joblib")
DISEASE_MODEL_PATH = os.path.join(MODELS_DIR, "paddy_disease_model.pkl")
DATA_CSV           = os.path.join(DATA_DIR,   "indian_crop_climate_data.csv")

# ── File-upload security ──────────────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS: set[str] = {"png", "jpg", "jpeg"}
ALLOWED_MIME_TYPES: set[str]       = {"image/png", "image/jpeg", "image/jpg"}
# 5 MB — reasonable for a leaf-disease photo
MAX_UPLOAD_BYTES: int              = 5 * 1024 * 1024

# ── Image pre-processing ──────────────────────────────────────────────────────
IMG_TARGET_SIZE: tuple[int, int]   = (128, 128)

# ── HOG parameters (must match training) ─────────────────────────────────────
HOG_ORIENTATIONS    = 9
HOG_PIXELS_PER_CELL = (8, 8)
HOG_CELLS_PER_BLOCK = (2, 2)
HOG_BLOCK_NORM      = "L2-Hys"

# ── Yield-prediction field constraints ───────────────────────────────────────
YIELD_NUMERIC_CONSTRAINTS: dict[str, dict] = {
    "temperature_c":    {"min": -10.0,  "max": 60.0},
    "rainfall_mm":      {"min":   0.0,  "max": 5000.0},
    "humidity_percent": {"min":   0.0,  "max": 100.0},
}
YIELD_REQUIRED_FIELDS: list[str] = [
    "crop_type", "region", "temperature_c",
    "rainfall_mm", "humidity_percent", "soil_type",
]

# ── CORS ──────────────────────────────────────────────────────────────────────
# Comma-separated origins in .env, e.g. ALLOWED_ORIGINS=http://localhost:3000,https://myfarm.app
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5000")
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ── Flask ─────────────────────────────────────────────────────────────────────
SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
DEBUG: bool     = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
HOST: str       = os.environ.get("FLASK_HOST", "0.0.0.0")
PORT: int       = int(os.environ.get("FLASK_PORT", "5000"))

# ── External API keys ─────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.environ.get("GROQ_API_KEY", "")

# ── Groq / LLM ────────────────────────────────────────────────────────────────
GROQ_MODEL      = "groq/compound"
GROQ_MAX_TOKENS = 512
GROQ_TEMPERATURE = 0.7

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str  = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FILE: str   = os.path.join(LOG_DIR, "app.log")
