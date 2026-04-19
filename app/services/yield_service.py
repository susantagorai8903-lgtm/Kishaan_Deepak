"""
app/services/yield_service.py
------------------------------
Business logic for crop-yield prediction.

This module is completely independent of Flask — it receives plain Python
objects and returns plain Python dicts.  That keeps it easy to test and
reuse outside a web context.
"""

from __future__ import annotations

import pandas as pd

from app.logger import logger
from app.models_loader import model_store


def get_yield_options() -> dict:
    """
    Read the training CSV and return unique sorted dropdown values for the
    crop-type, region, and soil-type fields.

    Returns
    -------
    dict
        ``{"crop_type": [...], "region": [...], "soil_type": [...]}``
        Any column that is absent in the CSV will have an empty list.
    """
    import config  # local to avoid circular imports at module level

    result: dict[str, list] = {"crop_type": [], "region": [], "soil_type": []}

    try:
        df = pd.read_csv(config.DATA_CSV)
        for col in result:
            if col in df.columns:
                result[col] = sorted(
                    {str(v).strip() for v in df[col].dropna() if str(v).strip()},
                    key=str.lower,
                )
        logger.debug("Yield options loaded from CSV (%d rows).", len(df))
    except FileNotFoundError:
        logger.warning("Data CSV not found at %s.  Returning empty options.", config.DATA_CSV)
    except Exception as exc:
        logger.error("Unexpected error reading CSV: %s", exc)

    return result


def predict_yield(clean_data: dict) -> dict:
    """
    Run the crop-yield model on pre-validated, pre-coerced input data.

    Parameters
    ----------
    clean_data : dict
        Must contain all keys from ``config.YIELD_REQUIRED_FIELDS``,
        with numeric fields already cast to float.

    Returns
    -------
    dict
        ``{"prediction_tonnes_per_hectare": <float>}``

    Raises
    ------
    RuntimeError
        Propagated from ``model_store.yield_model`` if the model is absent.
    ValueError
        If the model pipeline raises an unexpected error.
    """
    model = model_store.yield_model   # raises RuntimeError if not loaded

    # Build a single-row DataFrame matching the column names expected by the pipeline
    row = {
        "crop_type":        clean_data["crop_type"],
        "region":           clean_data["region"],
        "temperature_c":    clean_data["temperature_c"],
        "rainfall_mm":      clean_data["rainfall_mm"],
        "humidity_percent": clean_data["humidity_percent"],
        "soil_type":        clean_data["soil_type"],
    }
    X = pd.DataFrame([row])

    # Some legacy model variants use 'humidity' instead of 'humidity_percent'
    if "humidity" not in X.columns:
        X = X.rename(columns={"humidity_percent": "humidity"})
    if "percent" not in X.columns:
        X["percent"] = 0.0

    prediction = float(model.predict(X)[0])
    logger.info(
        "Yield prediction: crop=%s region=%s → %.4f t/ha",
        clean_data["crop_type"], clean_data["region"], prediction,
    )
    return {"prediction_tonnes_per_hectare": round(prediction, 4)}
