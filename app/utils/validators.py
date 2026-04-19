"""
app/utils/validators.py
------------------------
Pure functions for validating user-supplied input.
No Flask imports here so these can be unit-tested in isolation.
"""

from __future__ import annotations

import mimetypes
import os
from typing import Any

import config


# ── File upload validation ────────────────────────────────────────────────────

def allowed_image_extension(filename: str) -> bool:
    """Return True if *filename* has one of the permitted image extensions."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in config.ALLOWED_IMAGE_EXTENSIONS


def validate_upload_file(file_storage) -> tuple[bool, str]:
    """
    Validate a Werkzeug ``FileStorage`` object.

    Checks
    ------
    1. Filename is not empty.
    2. Extension is in the allow-list.
    3. MIME type is in the allow-list.
    4. Content length does not exceed ``MAX_UPLOAD_BYTES``.

    Returns
    -------
    (True, "")          — file is valid.
    (False, "reason")   — file is invalid, reason describes the problem.
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file was selected."

    if not allowed_image_extension(file_storage.filename):
        allowed = ", ".join(sorted(config.ALLOWED_IMAGE_EXTENSIONS)).upper()
        return False, f"File type not allowed. Permitted types: {allowed}."

    # MIME check via Content-Type header or guessed from extension
    mime = file_storage.content_type or ""
    if not mime:
        guessed, _ = mimetypes.guess_type(file_storage.filename)
        mime = guessed or ""

    if mime not in config.ALLOWED_MIME_TYPES:
        return False, f"MIME type '{mime}' is not permitted for image uploads."

    # Size guard — read the stream position to estimate size
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)          # rewind for later use

    max_mb = config.MAX_UPLOAD_BYTES / (1024 * 1024)
    if size > config.MAX_UPLOAD_BYTES:
        return False, f"File exceeds the {max_mb:.0f} MB size limit."

    return True, ""


# ── Yield-prediction input validation ────────────────────────────────────────

def validate_yield_payload(data: dict[str, Any]) -> tuple[bool, str | dict]:
    """
    Validate the JSON body for the crop-yield prediction endpoint.

    Returns
    -------
    (True,  clean_dict)  — all fields present, numeric fields coerced to float.
    (False, error_msg)   — validation failed, error_msg is a string.
    """
    # 1. Required-field presence
    missing = [f for f in config.YIELD_REQUIRED_FIELDS if f not in data or str(data[f]).strip() == ""]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}."

    clean: dict[str, Any] = {}

    # 2. String fields — strip whitespace
    for key in ("crop_type", "region", "soil_type"):
        value = str(data[key]).strip()
        if not value:
            return False, f"Field '{key}' must not be blank."
        clean[key] = value

    # 3. Numeric fields — type-coerce + range check
    constraints = config.YIELD_NUMERIC_CONSTRAINTS
    for key, bounds in constraints.items():
        try:
            val = float(data[key])
        except (ValueError, TypeError):
            return False, f"Field '{key}' must be a number."

        lo, hi = bounds["min"], bounds["max"]
        if not (lo <= val <= hi):
            return False, f"Field '{key}' must be between {lo} and {hi} (got {val})."

        clean[key] = val

    return True, clean


# ── Generic helpers ───────────────────────────────────────────────────────────

def is_non_empty_string(value: Any) -> bool:
    """Return True if *value* is a non-empty string after stripping."""
    return isinstance(value, str) and bool(value.strip())
