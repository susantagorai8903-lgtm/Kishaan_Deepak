"""
app/routes/yield_routes.py
---------------------------
Flask Blueprint for the crop-yield API endpoints.

All input validation is delegated to ``app.utils.validators``.
All business logic is delegated to ``app.services.yield_service``.
This file only handles HTTP: parsing requests, calling services,
and shaping JSON responses.
"""

from flask import Blueprint, jsonify, request

from app.logger import logger
from app.services import yield_service
from app.utils.validators import validate_yield_payload

yield_bp = Blueprint("yield", __name__, url_prefix="/api/yield")


@yield_bp.route("/options", methods=["GET"])
def yield_options():
    """
    GET /api/yield/options
    ----------------------
    Return the unique crop-type, region, and soil-type values read from the
    training CSV.  Used to populate dropdowns in the front-end form.

    Response 200
    ~~~~~~~~~~~~
    .. code-block:: json

        {
            "crop_type": ["Maize", "Rice", ...],
            "region":    ["North", "South", ...],
            "soil_type": ["Clay", "Loamy", ...]
        }
    """
    try:
        options = yield_service.get_yield_options()
        return jsonify(options), 200
    except Exception as exc:
        logger.exception("Unexpected error in yield_options: %s", exc)
        return jsonify({"error": "Could not load dropdown options."}), 500


@yield_bp.route("/predict", methods=["POST"])
def yield_predict():
    """
    POST /api/yield/predict
    -----------------------
    Predict crop yield for a set of agronomic inputs.

    Request body (JSON or form-data)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {
            "crop_type":        "Rice",
            "region":           "South",
            "temperature_c":    28.5,
            "rainfall_mm":      1200,
            "humidity_percent": 75,
            "soil_type":        "Clay"
        }

    Response 200
    ~~~~~~~~~~~~
    .. code-block:: json

        {"prediction_tonnes_per_hectare": 4.2318}

    Response 400 — validation error
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "Missing required fields: crop_type, region."}

    Response 503 — model not available
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "Yield model is not available.  ..."}
    """
    data = request.get_json(silent=True) or request.form.to_dict()
    logger.info("POST /api/yield/predict  payload_keys=%s", list(data.keys()))

    # ── Validation ────────────────────────────────────────────────────────────
    ok, result = validate_yield_payload(data)
    if not ok:
        logger.warning("Yield predict validation failed: %s", result)
        return jsonify({"error": result}), 400

    clean_data = result  # dict with coerced types

    # ── Prediction ────────────────────────────────────────────────────────────
    try:
        prediction = yield_service.predict_yield(clean_data)
        return jsonify(prediction), 200

    except RuntimeError as exc:
        # Model not loaded
        logger.error("Yield model unavailable: %s", exc)
        return jsonify({"error": str(exc)}), 503

    except Exception as exc:
        logger.exception("Yield prediction failed: %s", exc)
        return jsonify({"error": "Prediction failed.  Check server logs for details."}), 500
