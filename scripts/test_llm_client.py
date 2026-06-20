#!/usr/bin/env python3
"""Smoke test for the LiteLLM client. Phase 01 gate condition: confirms Pi-V
can reach the home lab LiteLLM endpoint and get a response back.

Usage: python3 scripts/test_llm_client.py
Requires .env populated with LITELLM_ENDPOINT / LITELLM_API_KEY / LITELLM_MODEL.
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from vision.llm_client import LiteLLMClient, LiteLLMConfig  # noqa: E402


async def main() -> None:
    load_dotenv()
    config = LiteLLMConfig.from_env()
    client = LiteLLMClient(config)

    prompt = "Respond with exactly one short sentence confirming you received this message."
    print(f"Querying {config.endpoint} (model={config.model})...")

    start = time.monotonic()
    try:
        result = await client.query([{"role": "user", "content": prompt}])
    finally:
        await client.aclose()

    latency = time.monotonic() - start
    print(f"Response ({latency:.2f}s): {result}")


if __name__ == "__main__":
    asyncio.run(main())
