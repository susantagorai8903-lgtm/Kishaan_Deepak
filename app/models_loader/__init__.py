"""
app/models_loader/__init__.py
------------------------------
Exports the singleton model-loader so callers use:
    from app.models_loader import model_store
"""

from .loader import model_store

__all__ = ["model_store"]
