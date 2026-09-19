"""Thin wrapper around the OpenRouter chat-completions API with the resilience A11 requires:
timeout, bounded retry with backoff, and a typed failure the caller can degrade on instead of
crashing.

Also provides the determinism A5 requires ("run the same ticket twice, the decision does not
change"): the model is called at temperature=0, and responses are additionally cached on disk
keyed by the exact prompt content, so a repeated call for the same ticket returns the identical
recorded response rather than a fresh, independently-sampled one. This was found necessary
empirically on Day 3 -- a 20-ticket classification re-run at default temperature produced a
different accuracy figure and different individual predictions than the first run, which would
fail A5's literal test procedure if classification sat inside the "same ticket twice" boundary.
Caching also conserves the free-tier allowance during development, per the Build Spec's own
guidance.
"""
from __future__ import annotations

import hashlib
import json
import time
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

from src import config

logger = logging.getLogger(__name__)

_CACHE_PATH = Path("./storage/llm_cache.json")
_cache: Optional[dict] = None


class ProviderUnavailable(Exception):
    """Raised when the model provider cannot be reached after retries, or rate-limits us."""


@dataclass
class LLMResponse:
    text: str
    raw: dict


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        if _CACHE_PATH.exists():
            try:
                _cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            except Exception:
                _cache = {}
        else:
            _cache = {}
    return _cache


def _save_cache() -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(_cache, indent=2), encoding="utf-8")


def _cache_key(system_prompt: str, user_prompt: str) -> str:
    digest = hashlib.sha256((config.MODEL_NAME + "||" + system_prompt + "||" + user_prompt).encode("utf-8"))
    return digest.hexdigest()


def _post(messages: list[dict], timeout: float, max_tokens: int = 800) -> requests.Response:
    return requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENROUTER_API_KEY}"},
        json={
            "model": config.MODEL_NAME,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0,
            "seed": 0,
        },
        timeout=timeout,
    )


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    timeout: float = 20.0,
    max_retries: int = 2,
    backoff_seconds: float = 1.5,
    use_cache: bool = True,
) -> LLMResponse:
    """Call the model provider with a system+user message pair.

    Retries on timeout and on HTTP 429/5xx, with exponential backoff, up to max_retries times.
    Raises ProviderUnavailable if it still fails -- callers are expected to catch this and
    degrade (e.g. route to escalate) rather than let the process crash (A11).

    Deterministic and cached by default (see module docstring) -- pass use_cache=False to force
    a fresh call.
    """
    if not config.OPENROUTER_API_KEY:
        raise ProviderUnavailable("OPENROUTER_API_KEY is not set")

    cache = _load_cache()
    key = _cache_key(system_prompt, user_prompt)
    if use_cache and key in cache:
        return LLMResponse(text=cache[key], raw={"cached": True})

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    last_error: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            resp = _post(messages, timeout=timeout)
        except requests.exceptions.Timeout as exc:
            last_error = exc
            logger.warning("LLM call timed out (attempt %s/%s)", attempt + 1, max_retries + 1)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            logger.warning("LLM call failed (attempt %s/%s): %s", attempt + 1, max_retries + 1, exc)
        else:
            if resp.status_code == 200:
                data = resp.json()
                text = data["choices"][0]["message"]["content"]
                if use_cache:
                    cache[key] = text
                    _save_cache()
                return LLMResponse(text=text, raw=data)
            if resp.status_code in (429, 500, 502, 503, 504):
                last_error = ProviderUnavailable(f"HTTP {resp.status_code}: {resp.text[:200]}")
                logger.warning("LLM call got %s (attempt %s/%s)", resp.status_code, attempt + 1, max_retries + 1)
            else:
                # Non-retryable client error (e.g. 401 bad key) -- fail fast, don't retry
                raise ProviderUnavailable(f"HTTP {resp.status_code}: {resp.text[:200]}")

        if attempt < max_retries:
            time.sleep(backoff_seconds * (2**attempt))

    raise ProviderUnavailable(str(last_error))


def parse_json_response(text: str) -> dict:
    """LLMs sometimes wrap JSON in prose or code fences despite instructions -- extract it."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object found in model output: {text[:200]!r}")
    return json.loads(text[start : end + 1])
