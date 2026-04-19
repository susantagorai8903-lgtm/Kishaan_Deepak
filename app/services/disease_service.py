"""
app/services/disease_service.py
--------------------------------
Business logic for paddy-disease detection.

Receives a raw NumPy image array, returns a structured prediction dict.
No Flask, no HTTP concerns — purely ML inference + result formatting.
"""

from __future__ import annotations

import numpy as np

from app.logger import logger
from app.models_loader import model_store
from app.utils.image_utils import extract_hog_features


def get_disease_classes() -> list[str]:
    """
    Return the list of disease class names the model was trained on.

    Returns
    -------
    list[str]
        e.g. ``["Bacterial Leaf Blight", "Brown Spot", ...]``

    Raises
    ------
    RuntimeError
        If the disease encoder is not loaded.
    """
    encoder = model_store.disease_encoder  # raises if not available
    return encoder.classes_.tolist()


def predict_disease(img: np.ndarray) -> dict:
    """
    Predict the paddy disease present in *img*.

    Steps
    -----
    1. Extract HOG features from the image.
    2. Run the HOG feature vector through the Logistic Regression pipeline.
    3. Decode the numeric label back to a human-readable class name.
    4. Compute per-class confidence scores.

    Parameters
    ----------
    img : np.ndarray
        BGR image array as returned by ``cv2.imread``.
        The image is resized internally — caller does not need to pre-resize.

    Returns
    -------
    dict with keys:
        ``disease``        — predicted class name (str)
        ``confidence``     — top-class probability in % (float, 2 dp)
        ``all_predictions``— dict mapping each class → probability % (float)

    Raises
    ------
    RuntimeError
        Propagated from ``model_store`` if either the model or encoder is absent.
    """
    model   = model_store.disease_model    # raises if absent
    encoder = model_store.disease_encoder  # raises if absent

    features         = extract_hog_features(img)
    pred_encoded     = model.predict([features])[0]
    probabilities    = model.predict_proba([features])[0]
    disease_label    = encoder.inverse_transform([pred_encoded])[0]
    confidence_pct   = float(max(probabilities) * 100)

    all_predictions = {
        cls: round(float(p * 100), 2)
        for cls, p in zip(encoder.classes_, probabilities)
    }

    logger.info(
        "Disease prediction: label=%s confidence=%.2f%%",
        disease_label, confidence_pct,
    )

    return {
        "disease":         disease_label,
        "confidence":      round(confidence_pct, 2),
        "all_predictions": all_predictions,
    }
