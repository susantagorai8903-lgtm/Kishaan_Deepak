"""
app/__init__.py
---------------
Flask application factory.

Usage
-----
    from app import create_app
    app = create_app()

Design principles
~~~~~~~~~~~~~~~~~
* Models are loaded **once** inside ``create_app`` via ``model_store.load_all()``.
* CORS is restricted to the origins listed in ``config.ALLOWED_ORIGINS``.
* Every Blueprint registers under a clean URL prefix.
* The factory pattern makes the app easy to test (pass in config overrides).
"""

import os

from flask import Flask, render_template
from flask_cors import CORS

import config
from app.logger import logger
from app.models_loader import model_store
from app.routes.chat_routes import chat_bp
from app.routes.disease_routes import disease_bp
from app.routes.health_routes import health_bp
from app.routes.yield_routes import yield_bp


def create_app() -> Flask:
    """
    Create, configure, and return the Flask application instance.

    Returns
    -------
    Flask
        A fully wired-up Flask application ready to serve requests.
    """
    # ── Ensure required directories exist ────────────────────────────────────
    for directory in (config.UPLOAD_FOLDER, config.LOG_DIR, config.MODELS_DIR):
        os.makedirs(directory, exist_ok=True)

    # ── Flask instance ────────────────────────────────────────────────────────
    app = Flask(
        __name__,
        template_folder=os.path.join(config.BASE_DIR, "templates"),
        static_folder=os.path.join(config.BASE_DIR, "static"),
    )

    app.config["SECRET_KEY"]          = config.SECRET_KEY
    app.config["UPLOAD_FOLDER"]       = config.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"]  = config.MAX_UPLOAD_BYTES

    # ── CORS — restricted to configured origins ───────────────────────────────
    CORS(app, origins=config.ALLOWED_ORIGINS)
    logger.info("CORS enabled for origins: %s", config.ALLOWED_ORIGINS)

    # ── Register Blueprints ───────────────────────────────────────────────────
    app.register_blueprint(yield_bp)
    app.register_blueprint(disease_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    logger.info("All Blueprints registered.")

    # ── Front-end catch-all ───────────────────────────────────────────────────
    @app.route("/")
    def index():
        """Serve the single-page front-end."""
        return render_template("index.html")

    # ── Request lifecycle logging ─────────────────────────────────────────────
    @app.before_request
    def log_request():
        from flask import request
        logger.info("→ %s %s", request.method, request.path)

    @app.after_request
    def log_response(response):
        from flask import request
        logger.info("← %s %s  [%d]", request.method, request.path, response.status_code)
        return response

    # ── Global error handlers ─────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(exc):
        from flask import jsonify
        return jsonify({"error": "Endpoint not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(exc):
        from flask import jsonify
        return jsonify({"error": "HTTP method not allowed for this endpoint."}), 405

    @app.errorhandler(413)
    def request_entity_too_large(exc):
        from flask import jsonify
        max_mb = config.MAX_UPLOAD_BYTES / (1024 * 1024)
        return jsonify({"error": f"Upload exceeds the {max_mb:.0f} MB size limit."}), 413

    @app.errorhandler(500)
    def internal_error(exc):
        from flask import jsonify
        logger.exception("Unhandled 500 error: %s", exc)
        return jsonify({"error": "An unexpected server error occurred."}), 500

    # ── Load ML models once ───────────────────────────────────────────────────
    model_store.load_all()

    logger.info(
        "Application ready — yield_model: %s | disease_model: %s",
        model_store.status()["yield_model"],
        model_store.status()["disease_model"],
    )

    return app
