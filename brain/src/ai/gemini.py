"""
Gemini Service Abstraction for DreamWeave.
Isolates Gemini API calls behind a clean interface.
Handles SDK calls, fallbacks, model selection, and sanitized error handling.
"""

import json
import logging
import urllib.request
from typing import Optional
from fastapi import HTTPException, status
from brain.src import config

logger = logging.getLogger("dreamweave.ai.gemini")


def generate_gemini_response(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: Optional[str] = None
) -> str:
    """
    Generate an AI text response using the Gemini API.
    Uses the configured model (defaulting to GEMINI_MODEL) and GEMINI_API_KEY.
    """
    api_key = config.GEMINI_API_KEY
    if not api_key:
        logger.warning("Gemini API request attempted without GEMINI_API_KEY set.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gemini API service is not configured. Please set GEMINI_API_KEY in environment."
        )

    target_model = model or config.GEMINI_MODEL or "gemini-1.5-flash"

    # 1. Try official google-genai SDK first
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        config_args = {}
        if system_instruction:
            config_args["system_instruction"] = system_instruction

        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_args) if config_args else None
        )
        if response and hasattr(response, "text") and response.text:
            return response.text.strip()
    except Exception as sdk_err:
        logger.debug(f"google-genai SDK call error/fallback ({sdk_err}). Trying REST endpoint...")

    # 2. Try REST API endpoint via urllib
    try:
        model_name = target_model.replace("models/", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        payload_parts = []
        if system_instruction:
            payload_parts.append({"text": f"System: {system_instruction}\n\n"})
        payload_parts.append({"text": prompt})

        payload = {"contents": [{"parts": payload_parts}]}

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=30) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            candidates = res_data.get('candidates', [])
            if candidates and 'content' in candidates[0] and 'parts' in candidates[0]['content']:
                return candidates[0]['content']['parts'][0]['text'].strip()

    except Exception as http_err:
        logger.error(f"Gemini REST API request failed: {type(http_err).__name__} - {http_err}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate response from Gemini AI service. Please try again later."
        )

    raise HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail="Empty response received from Gemini AI service."
    )
