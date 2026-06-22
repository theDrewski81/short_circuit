#!/usr/bin/env python3
"""One-off diagnostic: capture a still from the Pi-V camera and ask the
vision-capable LiteLLM model what color is in frame.

Not part of tracked Phase 01/04 deliverables -- a standalone hardware/vision
confidence check using what's already wired up (camera + LiteLLM client).
Calls the LiteLLM HTTP API directly rather than llm_client.py, since that
module's image path is still a stub pending Phase 04 work.

Usage (on johnny5-vision, with .env populated):
    python3 scripts/whats_this_color.py
"""

import base64
import os
import subprocess
import sys
import tempfile

import httpx
from dotenv import load_dotenv

load_dotenv()

ENDPOINT = os.environ["LITELLM_ENDPOINT"]
API_KEY = os.environ["LITELLM_API_KEY"]
MODEL = os.environ["LITELLM_MODEL"]
TIMEOUT = float(os.environ.get("LITELLM_TIMEOUT", "60.0"))


def capture_still() -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        path = f.name
    try:
        subprocess.run(
            ["rpicam-still", "-o", path, "--immediate", "-t", "1000", "-n"],
            check=True,
            capture_output=True,
        )
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.unlink(path)


def ask_color(image_bytes: bytes) -> str:
    b64 = base64.b64encode(image_bytes).decode("ascii")
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What color is the dominant color in this image? Answer in one word."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            }
        ],
    }
    with httpx.Client(base_url=ENDPOINT, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=TIMEOUT) as client:
        response = client.post("/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def main() -> None:
    print("Capturing still...")
    image_bytes = capture_still()
    print(f"Captured {len(image_bytes)} bytes. Querying {MODEL}...")
    answer = ask_color(image_bytes)
    print(f"Answer: {answer.strip()}")


if __name__ == "__main__":
    sys.exit(main())
