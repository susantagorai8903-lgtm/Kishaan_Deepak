"""
app/services/chat_service.py
-----------------------------
Thin wrapper around the Groq client.

Keeping the Groq initialisation and system-prompt here (rather than in the
route) means the route only deals with HTTP concerns, and this module only
deals with LLM communication.
"""

from __future__ import annotations

from groq import Groq

import config
from app.logger import logger


# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Kishaan Deepak's AI agricultural assistant — a friendly, expert support bot for an AI-powered crop intelligence platform built for Indian farmers.

Your platform has two core tools:
1. **Crop Yield Prediction** — predicts output (tonnes/hectare) based on crop type, region, temperature, rainfall, humidity, and soil type.
2. **Paddy Disease Detection** — classifies paddy leaf diseases from uploaded images using HOG features + Logistic Regression (10 disease classes).

You help users with:
- How to use the platform (yield prediction, disease detection)
- Understanding predictions and results
- Agricultural advice: crop selection, soil health, irrigation, fertilizers, pest management
- Interpreting weather and climate impact on crops
- Indian regional farming practices and seasons (Kharif, Rabi, Zaid)
- Common paddy diseases: Bacterial Leaf Blight, Brown Spot, Leaf Blast, Neck Blast, Sheath Blight, etc.
- General farming tips for rice, wheat, maize, pulses, sugarcane, cotton, and other Indian crops

Guidelines:
- Be concise, warm, and practical — farmers need actionable advice
- Use simple language; avoid jargon unless explaining a technical term
- When mentioning diseases, always include symptoms and basic treatment
- For yield questions, suggest which inputs matter most
- If asked something outside agriculture/this platform, politely redirect
- Respond in the same language the user writes in (English or Hindi/Hinglish is fine)
- Keep responses under 200 words unless a detailed explanation is truly needed
"""


# ── Groq client (created once per process) ───────────────────────────────────

def _make_groq_client() -> Groq:
    if not config.GROQ_API_KEY:
        logger.warning("GROQ_API_KEY is not set.  Chat endpoint will be unavailable.")
    return Groq(api_key=config.GROQ_API_KEY)


_groq_client: Groq = _make_groq_client()


# ── Public API ────────────────────────────────────────────────────────────────

def stream_chat(messages: list[dict]) -> object:
    """
    Open a streaming completion with the Groq API.

    Parameters
    ----------
    messages : list[dict]
        Conversation history in the format ``[{"role": "user", "content": "..."}]``.
        The system prompt is prepended automatically.

    Returns
    -------
    Groq streaming completion iterator.
    Each chunk exposes ``chunk.choices[0].delta.content``.

    Raises
    ------
    groq.APIError (or subclasses)
        Propagated directly so the route can return a 500 response with detail.
    """
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured.  Set it in .env to enable chat.")

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    completion = _groq_client.chat.completions.create(
        model       = config.GROQ_MODEL,
        messages    = full_messages,
        max_tokens  = config.GROQ_MAX_TOKENS,
        temperature = config.GROQ_TEMPERATURE,
        stream      = True,
    )

    logger.debug("Groq streaming chat started (%d message(s) in context).", len(messages))
    return completion
