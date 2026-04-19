"""
app/routes/disease_routes.py
-----------------------------
Flask Blueprint for the paddy-disease detection API endpoints.

Responsibilities
~~~~~~~~~~~~~~~~
* Parse and validate file uploads (extension, MIME, size).
* Save the upload to a temporary location, run inference, then delete it.
* Return structured JSON responses.

All ML logic lives in ``app.services.disease_service``.
All image I/O helpers live in ``app.utils.image_utils``.
"""

import os

from flask import Blueprint, jsonify, request

from app.logger import logger
from app.services import disease_service
from app.utils.image_utils import (
    encode_image_base64,
    make_safe_upload_path,
    read_image_from_path,
)
from app.utils.validators import validate_upload_file

disease_bp = Blueprint("disease", __name__, url_prefix="/api/disease")


@disease_bp.route("/classes", methods=["GET"])
def disease_classes():
    """
    GET /api/disease/classes
    ------------------------
    Return the disease class names the model was trained on.

    Response 200
    ~~~~~~~~~~~~
    .. code-block:: json

        {"classes": ["Bacterial Leaf Blight", "Brown Spot", ...]}

    Response 503 — model not loaded
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "Disease label encoder is not available. ..."}
    """
    try:
        classes = disease_service.get_disease_classes()
        return jsonify({"classes": classes}), 200
    except RuntimeError as exc:
        logger.error("Disease classes unavailable: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        logger.exception("Unexpected error in disease_classes: %s", exc)
        return jsonify({"error": "Could not retrieve disease classes."}), 500


@disease_bp.route("/predict", methods=["POST"])
def disease_predict():
    """
    POST /api/disease/predict
    -------------------------
    Classify the disease in an uploaded paddy-leaf image.

    Request
    ~~~~~~~
    Multipart form-data with a single ``file`` field containing a PNG or JPEG.

    Response 200
    ~~~~~~~~~~~~
    .. code-block:: json

        {
            "success": true,
            "disease": "Brown Spot",
            "confidence": 87.43,
            "all_predictions": {
                "Bacterial Leaf Blight": 3.12,
                "Brown Spot": 87.43,
                "..."
            },
            "image": "data:image/jpeg;base64,/9j/4AAQ..."
        }

    Response 400 — invalid upload
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "File type not allowed. Permitted types: JPEG, JPG, PNG."}

    Response 503 — model not available
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "Disease model is not available. ..."}
    """
    # ── 1. Validate upload ────────────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"error": "No file field found in the request."}), 400

    file = request.files["file"]
    ok, reason = validate_upload_file(file)
    if not ok:
        logger.warning("Disease predict upload rejected: %s", reason)
        return jsonify({"error": reason}), 400

    logger.info("POST /api/disease/predict  filename=%s", file.filename)

    # ── 2. Save upload temporarily ────────────────────────────────────────────
    save_path = make_safe_upload_path(file.filename)
    try:
        file.save(save_path)
    except Exception as exc:
        logger.exception("Failed to save upload to %s: %s", save_path, exc)
        return jsonify({"error": "Could not save the uploaded file."}), 500

    # ── 3. Read image ─────────────────────────────────────────────────────────
    img = read_image_from_path(save_path)
    if img is None:
        _safe_remove(save_path)
        return jsonify({"error": "The uploaded file could not be read as an image. It may be corrupted."}), 400

    # ── 4. Run inference ──────────────────────────────────────────────────────
    try:
        result = disease_service.predict_disease(img)
    except RuntimeError as exc:
        _safe_remove(save_path)
        logger.error("Disease model unavailable: %s", exc)
        return jsonify({"error": str(exc)}), 503
    except Exception as exc:
        _safe_remove(save_path)
        logger.exception("Disease prediction failed: %s", exc)
        return jsonify({"error": "Prediction failed.  Check server logs for details."}), 500

    # ── 5. Encode image for preview ───────────────────────────────────────────
    try:
        mime, b64_data = encode_image_base64(save_path)
        image_data_uri = f"data:{mime};base64,{b64_data}"
    except Exception as exc:
        logger.warning("Could not base64-encode image for preview: %s", exc)
        image_data_uri = None
    finally:
        _safe_remove(save_path)

    return jsonify({
        "success":         True,
        "disease":         result["disease"],
        "confidence":      result["confidence"],
        "all_predictions": result["all_predictions"],
        "image":           image_data_uri,
    }), 200


# ── Helpers ───────────────────────────────────────────────────────────────────

def _safe_remove(path: str) -> None:
    """Delete *path* silently — used to clean up temp uploads."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception as exc:
        logger.warning("Could not remove temp file %s: %s", path, exc)
