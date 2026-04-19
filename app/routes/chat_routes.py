"""
app/routes/chat_routes.py
--------------------------
Flask Blueprint for the AI chatbot streaming endpoint.
"""

from flask import Blueprint, Response, jsonify, request, stream_with_context

from app.logger import logger
from app.services import chat_service
from app.utils.validators import is_non_empty_string

chat_bp = Blueprint("chat", __name__, url_prefix="/api")


@chat_bp.route("/chat", methods=["POST"])
def chat():
    """
    POST /api/chat
    --------------
    Stream an AI assistant reply using Groq.

    Request body (JSON)
    ~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {
            "messages": [
                {"role": "user",      "content": "What causes leaf blast?"},
                {"role": "assistant", "content": "Leaf blast is caused by ..."},
                {"role": "user",      "content": "How do I treat it?"}
            ]
        }

    Response 200
    ~~~~~~~~~~~~
    Plain-text streaming response (``text/plain``).
    Each chunk is a fragment of the assistant's reply.

    Response 400 — bad request
    ~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "No messages provided."}

    Response 500 — upstream error
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    .. code-block:: json

        {"error": "Chat failed.", "details": "..."}
    """
    data     = request.get_json(silent=True) or {}
    messages = data.get("messages", [])

    # ── Validation ────────────────────────────────────────────────────────────
    if not messages:
        return jsonify({"error": "No messages provided."}), 400

    for msg in messages:
        if msg.get("role") not in ("user", "assistant"):
            return jsonify({"error": "Each message must have role 'user' or 'assistant'."}), 400
        if not is_non_empty_string(msg.get("content")):
            return jsonify({"error": "Each message must have non-empty 'content'."}), 400

    logger.info("POST /api/chat  message_count=%d", len(messages))

    # ── Stream response ───────────────────────────────────────────────────────
    try:
        completion = chat_service.stream_chat(messages)

        def generate():
            for chunk in completion:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        return Response(
            stream_with_context(generate()),
            mimetype="text/plain",
            headers={"X-Accel-Buffering": "no"},
        )

    except RuntimeError as exc:
        # GROQ_API_KEY not configured
        logger.error("Chat service misconfigured: %s", exc)
        return jsonify({"error": str(exc)}), 503

    except Exception as exc:
        logger.exception("Chat failed: %s", exc)
        return jsonify({"error": "Chat failed.", "details": str(exc)}), 500
