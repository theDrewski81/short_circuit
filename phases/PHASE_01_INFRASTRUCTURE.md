# Phase 01 — Infrastructure & Repository

## Objective

Stand up the GitHub repository, configure both Pis, establish inter-Pi communication, connect to the home lab LiteLLM endpoint, and implement the offline fallback state machine. No motion control or cognition code is written in this phase, but every software system that later code depends on must be operational at the gate.

---

## Gate Condition

**Both Pis communicate bidirectionally with each other. Pi-V successfully calls the home lab LiteLLM endpoint and receives a response. The offline fallback engages correctly when the endpoint is unreachable and clears correctly when it reconnects.**

---

## Context

The BOM is finalized (Phase 00 gate met). Hardware is on order or in hand but assembly is not required to begin this phase. Pi-M and Pi-V can be tested on the bench with bench power and direct WiFi.

The home lab runs an existing LiteLLM proxy from Andrew's Agentic OS project. Johnny 5 is a client of that proxy -- no new inference infrastructure is stood up. Confirm the proxy endpoint URL, authentication method, and model routing before writing any client code.

The Pi Zero 2 W is quad-core ARM Cortex-A53, 512MB RAM, WiFi/BT. Raspberry Pi OS Lite 64-bit is the target OS for both units. The Pi has no display output in production use.

---

## Tasks

### 1. GitHub Repository

Create the `johnny5` repository. Initialize with:

```
/
├── CLAUDE.md
├── INITIATING_PROMPT.md
├── BOM.md                    (from Phase 00)
├── .gitignore
├── README.md
├── mechanical/
│   ├── freecad/              (FreeCAD source files)
│   └── stl/                  (print-ready STL exports)
├── phases/
│   ├── PHASE_00_HARDWARE.md
│   ├── PHASE_01_INFRASTRUCTURE.md
│   ├── PHASE_02_LOCOMOTION.md
│   ├── PHASE_03_MANIPULATION.md
│   ├── PHASE_04_COGNITION.md
│   └── PHASE_05_INTEGRATION.md
├── src/
│   ├── motion/               (Pi-M code)
│   ├── vision/               (Pi-V code)
│   └── shared/               (message contracts, shared utilities)
├── simulation/               (MuJoCo models and training code)
├── policies/                 (trained policy exports, ONNX files)
└── scripts/                  (setup, deployment, maintenance scripts)
```

`.gitignore` should cover: Python `__pycache__`, `.env` files, virtual environments, large binary model files (use Git LFS or exclude and document separately), OS files (`.DS_Store`, `Thumbs.db`).

Add a `README.md` with project description, architecture overview, and link to `CLAUDE.md`.

Branch protection on `main`: require PR for merge, squash merge only.

### 2. Pi OS Setup

Both Pis: Raspberry Pi OS Lite 64-bit. Flash with Raspberry Pi Imager. During imaging, configure:
- Hostname: `johnny5-motion` (Pi-M) and `johnny5-vision` (Pi-V)
- SSH enabled
- WiFi credentials (home lab network)
- User: set a consistent username across both units

Post-flash initial setup for each Pi:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv git i2c-tools
sudo raspi-config   # enable I2C, SPI, camera (Pi-V), serial port (Pi-M), disable serial console
```

For Pi-M specifically: enable the UART serial port for servo communication (same as GrowBot: `dtoverlay=disable-bt` in `/boot/config.txt`, disable serial login in `raspi-config` but leave port enabled). Servos will appear on `/dev/serial0`.

For Pi-V specifically: enable camera interface via `raspi-config`. Confirm camera detected with `libcamera-hello`.

Python virtual environment setup on each Pi:
```bash
python3 -m venv ~/johnny5-env
source ~/johnny5-env/bin/activate
pip install --upgrade pip
```

Clone the repo on both Pis under `~/johnny5/`.

### 3. Inter-Pi Communication Protocol

Select and implement the message queue between Pi-M and Pi-V.

**Recommended: MQTT via Mosquitto broker hosted on the home lab.** This avoids direct Pi-to-Pi socket management, survives brief WiFi hiccups with retained messages, and integrates naturally with the home lab's existing infrastructure. Both Pis publish and subscribe to topics on the broker.

Topic structure:
```
johnny5/intent          Pi-V → Pi-M: current behavior intent (JSON)
johnny5/status          Pi-M → Pi-V: motion state, servo positions, ToF reading (JSON)
johnny5/offline         Pi-V → Pi-M: online/offline signal (boolean retained)
johnny5/heartbeat/motion   Pi-M → broker: liveness (timestamp)
johnny5/heartbeat/vision   Pi-V → broker: liveness (timestamp)
```

If the home lab already runs a Mosquitto broker (from Agentic OS or other projects), connect to it. If not, stand one up on Proxmox as a lightweight container -- Mosquitto is trivial to deploy.

**Alternative: ZeroMQ with push/pull sockets.** Direct Pi-to-Pi, no broker dependency. More fragile across WiFi, but eliminates broker as a single point of failure. Use if MQTT feels heavyweight for the application.

Document the chosen protocol in `src/shared/PROTOCOL.md`. Define the JSON schema for each message type with field names, types, and valid values. This document is the contract between Pi-M and Pi-V code and must be updated if the schema changes.

### 4. LiteLLM Client

Implement the LiteLLM client on Pi-V in `src/vision/llm_client.py`.

Configuration via environment variables (`.env` file, not committed):
```
LITELLM_ENDPOINT=http://<home-lab-ip>:<port>/v1
LITELLM_API_KEY=<key>
LITELLM_MODEL=<model-string>
LITELLM_TIMEOUT=8.0
```

The client must:
- Make async HTTP calls (use `httpx` or `aiohttp` -- not blocking `requests`)
- Enforce the configured timeout strictly (LLM calls that exceed timeout are logged and abandoned, not waited on)
- Publish offline signal to MQTT when the endpoint is unreachable
- Log all calls with timestamp, token counts, and latency
- Expose a simple interface: `async def query(messages: list, image: bytes | None = None) -> str`

Test harness: a standalone script `scripts/test_llm_client.py` that calls the endpoint with a fixed prompt and prints the response and latency. This is the smoke test for Phase 01 gate.

### 5. Offline Fallback State Machine

Implement on Pi-M in `src/motion/offline_fallback.py`.

States:
- `ONLINE`: normal operation, consuming intent updates from Pi-V
- `OFFLINE`: LiteLLM unreachable; conservative behavior active
- `RECOVERING`: endpoint has reconnected; waiting for first valid intent before resuming

Transitions:
- `ONLINE → OFFLINE`: Pi-V publishes `offline=True` to `johnny5/offline` OR Pi-M has not received a Pi-V heartbeat for 30 seconds
- `OFFLINE → RECOVERING`: Pi-V publishes `offline=False`
- `RECOVERING → ONLINE`: Pi-M receives a valid intent message from Pi-V

Fallback behavior in `OFFLINE` state:
- Stop treads immediately (set motor PWM to 0)
- Hold current servo positions (do not command movement)
- Set LED ring to a distinct offline color pattern (e.g., slow amber pulse)
- Log entry into offline state with timestamp

The state machine must be instantiated and polled at every motion loop tick. It must not raise exceptions on state transitions; it logs errors and holds the last stable state.

Unit tests for the state machine go in `tests/test_offline_fallback.py`. Cover all three transitions and the behavioral outputs of each state.

### 6. Motion Loop Skeleton

Implement the bare motion loop on Pi-M in `src/motion/main.py`. This is not a full implementation -- it is the loop structure that later phases populate.

```python
# Pseudostructure -- not final code
LOOP_RATE_HZ = 50  # 20ms tick

def main():
    initialize_hardware()
    initialize_mqtt()
    state_machine = OfflineFallbackStateMachine()

    while True:
        tick_start = time.monotonic()

        state_machine.update()

        if state_machine.state == State.ONLINE:
            intent = get_latest_intent()
            execute_intent(intent)

        publish_status()

        elapsed = time.monotonic() - tick_start
        time.sleep(max(0, (1 / LOOP_RATE_HZ) - elapsed))
```

The loop rate (50Hz recommended as a starting point) should be a configurable constant. Verify the Pi Zero 2 W can sustain the target rate with full peripheral polling added in later phases -- profile it in Phase 02.

### 7. Deployment Scripts

Write the following scripts in `scripts/`:

`deploy_motion.sh`: rsync `src/motion/` and `src/shared/` to Pi-M, restart the motion service.  
`deploy_vision.sh`: rsync `src/vision/` and `src/shared/` to Pi-V, restart the vision service.  
`ssh_motion.sh` and `ssh_vision.sh`: convenience wrappers to SSH into each Pi by hostname.  
`check_health.sh`: query both Pi heartbeat topics from the home lab and report liveness.

These run from the development machine (home lab or workstation), not from the Pis themselves.

---

## Recommended Session Start

Confirm the LiteLLM proxy endpoint URL and authentication method before opening any code files. Then work top-down through the task list: repo structure, OS setup, MQTT broker, LiteLLM client, fallback state machine, motion loop skeleton, deployment scripts.

---

## Open Questions for This Phase

- Is a Mosquitto broker already running on the home lab, or does one need to be deployed?
- What model should the LiteLLM client target by default for Johnny 5? (Vision-capable model required for camera queries.)
- Preferred SSH key distribution method for the Pis?
- Should the `.env` file be managed via a secrets manager from the Agentic OS, or kept locally on each Pi?
