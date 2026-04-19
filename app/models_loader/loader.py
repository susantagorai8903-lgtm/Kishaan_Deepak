"""
app/models_loader/loader.py
----------------------------
Singleton that loads every ML model once at application start-up and
exposes them through a simple interface.

Design decisions
~~~~~~~~~~~~~~~~
* Models are loaded eagerly on import so we fail fast if a file is missing.
* Each getter raises ``RuntimeError`` (not returns None) so callers get a
  clear 503 response rather than a cryptic AttributeError later.
* The module is intentionally free of Flask so it can be used in tests or
  scripts without an application context.
"""

import os
import joblib

import config
from app.logger import logger


class _ModelStore:
    """Holds references to all trained model artefacts."""

    def __init__(self) -> None:
        self._yield_model    = None   # sklearn Pipeline
        self._disease_model  = None   # sklearn Pipeline (HOG → LogisticRegression)
        self._disease_encoder = None  # LabelEncoder

    # ── Loaders ───────────────────────────────────────────────────────────────

    def load_all(self) -> None:
        """Load every model.  Called once from the Flask application factory."""
        self._load_yield_model()
        self._load_disease_model()

    def _load_yield_model(self) -> None:
        """Load the crop-yield regression pipeline from disk."""
        path = config.YIELD_MODEL_PATH
        if not os.path.exists(path):
            logger.warning("Yield model not found at %s — prediction disabled.", path)
            return
        try:
            self._yield_model = joblib.load(path)
            logger.info("Crop-yield model loaded from %s", path)
        except Exception as exc:
            logger.error("Failed to load yield model: %s", exc)

    def _load_disease_model(self) -> None:
        """Load the paddy-disease pipeline and label-encoder from disk."""
        path = config.DISEASE_MODEL_PATH
        if not os.path.exists(path):
            logger.warning(
                "Disease model not found at %s — detection disabled.  "
                "Train with paddy-disease-classification.py first.",
                path,
            )
            return
        try:
            self._disease_model, self._disease_encoder = joblib.load(path)
            logger.info("Paddy-disease model loaded from %s", path)
        except Exception as exc:
            logger.error("Failed to load disease model: %s", exc)

    # ── Getters ───────────────────────────────────────────────────────────────

    @property
    def yield_model(self):
        """
        Returns the loaded crop-yield sklearn Pipeline.

        Raises
        ------
        RuntimeError
            If the model was not found or failed to load at startup.
        """
        if self._yield_model is None:
            raise RuntimeError(
                "Yield model is not available.  "
                "Ensure models/crop_yield_model.joblib exists and restart the server."
            )
        return self._yield_model

    @property
    def disease_model(self):
        """
        Returns the loaded paddy-disease sklearn Pipeline.

        Raises
        ------
        RuntimeError
            If the model was not found or failed to load at startup.
        """
        if self._disease_model is None:
            raise RuntimeError(
                "Disease model is not available.  "
                "Train with paddy-disease-classification.py, then restart the server."
            )
        return self._disease_model

    @property
    def disease_encoder(self):
        """
        Returns the LabelEncoder paired with the disease model.

        Raises
        ------
        RuntimeError
            If the model was not found or failed to load at startup.
        """
        if self._disease_encoder is None:
            raise RuntimeError(
                "Disease label encoder is not available.  "
                "Train the disease model first."
            )
        return self._disease_encoder

    # ── Status helper ─────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Return a plain-dict summary for the /api/health endpoint."""
        return {
            "yield_model":    "loaded" if self._yield_model    is not None else "not_loaded",
            "disease_model":  "loaded" if self._disease_model  is not None else "not_loaded",
        }


# Module-level singleton — imported by routes and services
model_store = _ModelStore()
