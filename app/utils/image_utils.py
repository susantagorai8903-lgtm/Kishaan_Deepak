"""
app/utils/image_utils.py
-------------------------
Helpers for safe image I/O and pre-processing.
All functions are pure (no Flask) so they are easy to test.
"""

from __future__ import annotations

import base64
import uuid
import os

import cv2
import numpy as np
from skimage.feature import hog
from werkzeug.utils import secure_filename

import config
from app.logger import logger


# ── Secure file path generation ───────────────────────────────────────────────

def make_safe_upload_path(original_filename: str) -> str:
    """
    Build a collision-safe, sanitised file path inside UPLOAD_FOLDER.

    A UUID prefix is prepended to the sanitised original name so two
    simultaneous uploads of "leaf.jpg" do not overwrite each other.

    Parameters
    ----------
    original_filename : str
        The filename as provided by the user.

    Returns
    -------
    str
        Absolute path suitable for saving the upload.
    """
    safe_name = secure_filename(original_filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    return os.path.join(config.UPLOAD_FOLDER, unique_name)


# ── Image reading ─────────────────────────────────────────────────────────────

def read_image_from_path(path: str) -> np.ndarray | None:
    """
    Read an image from *path* using OpenCV.

    Returns the image array on success, ``None`` if OpenCV cannot decode
    the file (e.g. corrupted or truncated upload).

    Parameters
    ----------
    path : str
        Absolute path to the saved upload.
    """
    img = cv2.imread(path)
    if img is None:
        logger.warning("cv2.imread returned None for path: %s", path)
    return img


# ── Pre-processing ────────────────────────────────────────────────────────────

def preprocess_image(img: np.ndarray) -> np.ndarray:
    """
    Resize the image to ``IMG_TARGET_SIZE`` (defined in config).

    The model was trained on 128×128 BGR images, so we keep BGR here.

    Parameters
    ----------
    img : np.ndarray
        Raw BGR image as returned by ``cv2.imread``.

    Returns
    -------
    np.ndarray
        Resized BGR image.
    """
    return cv2.resize(img, config.IMG_TARGET_SIZE)


# ── HOG feature extraction ────────────────────────────────────────────────────

def extract_hog_features(img: np.ndarray) -> np.ndarray:
    """
    Extract HOG feature vector from a BGR image.

    The HOG parameters here **must** match those used during training
    (see ``paddy-disease-classification.py`` and ``config.py``).

    Parameters
    ----------
    img : np.ndarray
        BGR image (any size — will be resized internally).

    Returns
    -------
    np.ndarray
        1-D HOG feature vector.
    """
    resized = preprocess_image(img)
    gray    = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    features = hog(
        gray,
        orientations   = config.HOG_ORIENTATIONS,
        pixels_per_cell= config.HOG_PIXELS_PER_CELL,
        cells_per_block = config.HOG_CELLS_PER_BLOCK,
        block_norm      = config.HOG_BLOCK_NORM,
    )
    return features


# ── Base64 encoding for API response ─────────────────────────────────────────

def encode_image_base64(path: str) -> tuple[str, str]:
    """
    Read a saved image file and return its base64-encoded data URI components.

    Parameters
    ----------
    path : str
        Absolute path to the image file.

    Returns
    -------
    (mime_type, base64_data) : tuple[str, str]
        *mime_type* is e.g. ``"image/jpeg"``.
        *base64_data* is the raw base64 string (without the ``data:`` prefix).
    """
    ext  = path.rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"

    with open(path, "rb") as fh:
        data = base64.b64encode(fh.read()).decode("utf-8")

    return mime, data
