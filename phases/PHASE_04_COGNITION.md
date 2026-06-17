# Phase 04 — Cognition

## Objective

Implement the full LLM agent loop on Pi-V: camera capture pipeline, voice input processing, intent generation, LED expressiveness, and the Johnny 5 personality. At the gate, the robot responds to spoken input with coordinated motion, speech, and LED expression, with the LLM reasoning about its environment from camera-captured context.

---

## Gate Condition

**The robot detects a voice prompt, transcribes it, reasons with the LLM using current camera context, and produces a coordinated response: verbal reply via speaker, motion intent to Pi-M, and LED state reflecting the interaction. All of this completes in under 4 seconds from end of voice prompt under normal home lab network conditions.**

---

## Context

Manipulation (Phase 03) is complete. Locomotion and servo control are functional. The motion loop on Pi-M consumes intent messages from Pi-V and drives all actuators. The LiteLLM client on Pi-V is operational (from Phase 01).

This phase is primarily Pi-V work. Pi-M receives intent updates from Pi-V as before; the motion loop does not change in this phase.

The 4-second response latency target is intentional. It covers: voice activity detection (~100ms) + transcription (~500ms local or API) + LLM inference (variable, target <2s round-trip to home lab) + TTS synthesis (~300ms) + audio output start. This is a perception latency budget, not a motion control latency budget; motion continues executing the previous intent during LLM processing.

---

## Tasks

### 1. Voice Input Pipeline

Implement in `src/vision/voice_input.py`.

**Voice Activity Detection (VAD):** Use `silero-vad` (PyTorch model, very small, runs on Pi Zero 2 W CPU in real time) or `webrtcvad` (no model required, faster, less accurate). VAD runs continuously on the microphone stream and triggers the transcription pipeline when speech is detected.

**Transcription:** Two options:
- Local: `whisper.cpp` with a tiny or base model. The Pi Zero 2 W can run `whisper.cpp` at ~1–2x real-time for short utterances (under 10 seconds) on the `tiny` model. Acceptable for V1.
- Remote: Send audio to the home lab (a Whisper API endpoint or a Whisper instance on the RTX 3080). Faster, offloads Pi CPU, but adds network dependency.

Recommendation: remote transcription via home lab for Phase 04 (consistent with the overall architecture of using home lab compute). Document the home lab Whisper endpoint in `.env`.

The voice pipeline publishes transcribed text to `johnny5/voice_input` on the MQTT broker. The LLM agent loop subscribes to this topic as one of its triggers.

### 2. Camera Capture Pipeline

Implement in `src/vision/camera.py`.

Camera capture is event-driven. The pipeline does not stream continuously to the LLM. It captures a frame when triggered and passes it to the LLM agent.

Triggers (in order of priority):
1. Voice input received (always capture a frame to give the LLM scene context)
2. Pi-M publishes proximity alert (VL53L1X reading below threshold)
3. Elapsed interval (every 30 seconds if no other trigger, for ambient awareness)
4. Pi-M publishes motion stop (robot has just stopped moving)

Camera interface:
```python
class Camera:
    def capture(self) -> bytes:
        """Capture a single frame and return as JPEG bytes."""

    def capture_with_metadata(self) -> dict:
        """Returns {'image': bytes, 'timestamp': float, 'trigger': str}"""
```

Use `libcamera` via the `picamera2` library (the modern interface for Pi cameras on Bookworm/Pi OS Lite 64-bit). Do not use the legacy `picamera` library.

Image preprocessing before sending to LLM: resize to 640×480 or 1280×720 (balance between context quality and token cost). Encode as JPEG at 85% quality. Do not send raw 8MP frames.

### 3. LLM Agent Loop

Implement in `src/vision/agent.py`. This is the core of the cognition system.

The agent loop runs asynchronously on Pi-V and is event-driven (not polling at a fixed tick rate).

```python
class JohnnyFiveAgent:
    def __init__(self, llm_client, mqtt_client, camera):
        self.conversation_history = []  # bounded length, rolling window
        ...

    async def on_trigger(self, trigger: str, voice_text: str | None = None) -> None:
        """Called when any trigger fires."""
        image = await self.camera.capture_async()
        response = await self.llm_client.query(
            messages=self._build_messages(trigger, voice_text),
            image=image
        )
        self._process_response(response)

    def _build_messages(self, trigger: str, voice_text: str | None) -> list:
        """Assemble the message list including system prompt, history, current context."""
        ...

    def _process_response(self, response: str) -> None:
        """Parse response, publish intent to Pi-M, synthesize and play speech."""
        ...
```

Conversation history is a rolling window (last N exchanges, where N is tunable). This gives the robot short-term memory of the interaction without unbounded context growth.

Response parsing: the LLM response must include both a verbal reply and a structured action block. Define a response format in the system prompt:

```
Respond in this exact format:
SPEAK: <what you say aloud>
ACTION: <JSON locomotion and behavior intent>
EXPRESSION: <LED state name>

Example:
SPEAK: Hello! I'm happy to meet you.
ACTION: {"locomotion": {"left": 0.0, "right": 0.0}, "arm_behavior": "WAVE", "head_behavior": "SCAN"}
EXPRESSION: HAPPY
```

Parse the `ACTION` block as JSON and publish to `johnny5/intent`. Parse `SPEAK` and send to TTS. Parse `EXPRESSION` and publish to a new topic `johnny5/led_state`.

### 4. Johnny 5 Personality — System Prompt

The system prompt is the single most impactful element for making this robot feel like Johnny 5. It lives in `src/vision/prompts/system.txt` and is loaded at agent startup.

Key elements:
- Identity: Johnny 5, a curious and enthusiastic robot who delights in learning and interaction
- Voice: energetic, slightly staccato, uses occasional robot-themed expressions; references "input" and "reading" rather than "seeing"
- Behavior: always expressive, never flat; chooses motion to match mood; physically gestures when speaking
- Constraints: responses are brief (the robot speaks in short bursts, not paragraphs); always includes an ACTION; always includes an EXPRESSION
- Context awareness: the robot can see its environment via camera and comments on what it perceives
- Safety: does not attempt to move toward people who have not indicated willingness to interact; stops treads before reaching obstacles

The system prompt must be tunable without code changes (it's a text file, not a hardcoded string). Iteration on the prompt is expected throughout Phase 04 and Phase 05.

### 5. Text-to-Speech Output

Implement in `src/vision/tts.py`.

Options:
- Remote TTS via home lab (preferred): send text to a TTS API or a home lab TTS service (Kokoro, Coqui TTS, or an API endpoint on the LiteLLM proxy). Lower latency than local synthesis on Pi Zero 2 W.
- Local TTS via `espeak-ng` or `pico2wave`: runs on Pi, no network dependency, robotic voice quality (which is actually aesthetically appropriate for Johnny 5).

Recommendation: use `espeak-ng` as the local fallback (deliberately robotic, fits the character, offline-capable) and remote TTS as the primary. Toggle via configuration. In offline mode, `espeak-ng` keeps the robot vocal.

Audio playback via the MAX98357A amplifier using `aplay` or `pygame.mixer`.

### 6. LED Expressiveness

Implement in `src/motion/led_controller.py` on Pi-M. Pi-M subscribes to `johnny5/led_state` and drives the WS2812B ring accordingly.

Define LED states:
- `IDLE`: slow blue breathing
- `LISTENING`: fast white pulse
- `THINKING`: spinning yellow
- `HAPPY`: bright green flash
- `CURIOUS`: slow cyan pulse
- `ALERT`: fast red flash
- `OFFLINE`: slow amber pulse (from Phase 01 fallback)
- `SPEAKING`: white with brightness modulated to audio amplitude (if audio output is on Pi-M; skip if on Pi-V)

Each state is defined as a named animation pattern. Patterns are parameterized (color, speed, brightness) and can be adjusted without code changes via a `led_states.yaml` config file.

Use the `rpi_ws281x` library. Root is required for GPIO access to the WS2812B; the motion loop must run as root or with appropriate permissions.

### 7. End-to-End Integration Test

Run the full cognition loop manually before declaring Phase 04 complete:

1. Start all services on both Pis.
2. Walk up to the robot and say "Hello, Johnny."
3. Verify: VAD detects voice, transcription completes, LLM queries with camera frame, response arrives, robot speaks reply, motion intent is published to Pi-M, arm/head behavior executes, LED state changes.
4. Measure total latency from end of utterance to first audio output.
5. Test the offline behavior: disconnect home lab, speak to the robot, confirm it responds with `espeak-ng` fallback and OFFLINE LED state.

---

## Known Constraints

Pi Zero 2 W has limited RAM (512MB). The Pi-V runs: MQTT client, camera pipeline, VAD, LLM client, TTS client, and agent loop concurrently. Profile memory usage during the integration test. If headroom is tight, move the VAD model to be loaded on-demand rather than kept resident.

The `picamera2` library has changed significantly between OS versions. Confirm the installed version matches Pi OS Lite 64-bit (Bookworm). Some APIs differ between Bullseye and Bookworm.

---

## Recommended Session Start

Confirm the home lab Whisper endpoint and TTS endpoint (if using remote) before writing code. Then begin with the voice pipeline (Task 1) and camera pipeline (Task 2), since they are the inputs to the agent loop. Write the system prompt (Task 4) early -- it informs how the response parser in Task 3 is designed.
