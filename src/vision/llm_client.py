"""LiteLLM client for Pi-V.

STUB: LiteLLM proxy endpoint URL, auth method, and model string are unconfirmed
(see INITIATING_PROMPT.md open questions). Config below reads from environment
but will fail closed (raise on missing config) rather than silently using bad
defaults, since a wrong endpoint is worse than a loud failure here.

Async, non-blocking relative to the Pi-M motion loop -- this module has no
knowledge of the motion loop and must never be awaited from it directly.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

import httpx

logger = logging.getLogger("johnny5.vision.llm_client")


@dataclass
class LiteLLMConfig:
    endpoint: str
    api_key: str
    model: str
    timeout: float = 8.0

    @classmethod
    def from_env(cls) -> "LiteLLMConfig":
        endpoint = os.environ.get("LITELLM_ENDPOINT")
        api_key = os.environ.get("LITELLM_API_KEY")
        model = os.environ.get("LITELLM_MODEL")
        timeout = float(os.environ.get("LITELLM_TIMEOUT", "8.0"))

        missing = [
            name
            for name, val in (
                ("LITELLM_ENDPOINT", endpoint),
                ("LITELLM_API_KEY", api_key),
                ("LITELLM_MODEL", model),
            )
            if not val
        ]
        if missing:
            raise RuntimeError(
                f"Missing required LiteLLM config: {', '.join(missing)}. "
                "Set these in .env -- see .env.example. "
                "Endpoint/auth/model are an open question for Phase 01 (see INITIATING_PROMPT.md)."
            )

        return cls(endpoint=endpoint, api_key=api_key, model=model, timeout=timeout)


class OfflineSignal:
    """Minimal interface the client uses to publish offline state to MQTT.

    Real implementation (Mosquitto publish to johnny5/offline) lands when the
    MQTT client module is built. Injected here so llm_client.py has no direct
    MQTT dependency and is independently testable.
    """

    def publish_offline(self, offline: bool, reason: str) -> None:
        raise NotImplementedError


class LiteLLMClient:
    def __init__(self, config: LiteLLMConfig, offline_signal: OfflineSignal | None = None):
        self._config = config
        self._offline_signal = offline_signal
        self._client = httpx.AsyncClient(
            base_url=config.endpoint,
            headers={"Authorization": f"Bearer {config.api_key}"},
            timeout=config.timeout,
        )

    async def query(self, messages: list[dict], image: bytes | None = None) -> str:
        """Send a chat completion request. Raises on timeout or transport error
        rather than retrying silently -- caller decides fallback behavior.
        """
        payload = {"model": self._config.model, "messages": messages}
        if image is not None:
            # Vision-capable model required; exact multimodal payload shape
            # depends on which model gets selected (open question).
            raise NotImplementedError(
                "Image payload encoding pending model selection -- see open questions."
            )

        start = time.monotonic()
        try:
            response = await self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
        except httpx.TimeoutException:
            latency = time.monotonic() - start
            logger.warning("LiteLLM call timed out after %.2fs", latency)
            if self._offline_signal:
                self._offline_signal.publish_offline(True, "timeout")
            raise
        except httpx.HTTPError as exc:
            latency = time.monotonic() - start
            logger.warning("LiteLLM call failed after %.2fs: %s", latency, exc)
            if self._offline_signal:
                self._offline_signal.publish_offline(True, "endpoint_unreachable")
            raise

        latency = time.monotonic() - start
        data = response.json()
        usage = data.get("usage", {})
        logger.info(
            "LiteLLM call ok: latency=%.2fs prompt_tokens=%s completion_tokens=%s",
            latency,
            usage.get("prompt_tokens"),
            usage.get("completion_tokens"),
        )
        if self._offline_signal:
            self._offline_signal.publish_offline(False, "")

        return data["choices"][0]["message"]["content"]

    async def aclose(self) -> None:
        await self._client.aclose()
