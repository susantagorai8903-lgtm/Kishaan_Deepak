"""
app/routes/health_routes.py
----------------------------
Simple health-check endpoint used by load balancers, uptime monitors,
and the front-end to know which models are ready.
"""

from flask import Blueprint, jsonify

from app.logger import logger
from app.models_loader import model_store

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health():
    """
    GET /api/health
    ---------------
    Return the current status of the application and its ML models.

    Response 200
    ~~~~~~~~~~~~
    .. code-block:: json

        {
            "status": "ok",
            "yield_model":   "loaded",
            "disease_model": "not_loaded"
        }
    """
    status = model_store.status()
    logger.debug("Health check requested: %s", status)
    return jsonify({"status": "ok", **status}), 200
