"""
app.py
------
Application entry point.

Run with:
    python app.py                  (development)
    gunicorn "app:flask_app"       (production)

The actual application is assembled by the factory in app/__init__.py.
This file only imports, builds, and optionally starts the dev server.
"""

import config
from app import create_app
from app.logger import logger

flask_app = create_app()

if __name__ == "__main__":
    logger.info(
        "Starting Kishaan Deepak — Crop Intelligence Platform  "
        "host=%s  port=%d  debug=%s",
        config.HOST, config.PORT, config.DEBUG,
    )
    flask_app.run(
        host  = config.HOST,
        port  = config.PORT,
        debug = config.DEBUG,
    )
