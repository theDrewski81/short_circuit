# Johnny 5 — Project Master Brief

## Identity

**Project:** Johnny 5  
**Owner:** Andrew (solo)  
**Concept:** A playful, Johnny 5-inspired (Short Circuit, 1986) autonomous robot. Tread-driven locomotion, two articulated arms, rotating head, voice I/O, and visual perception. LLM handles reasoning and communication; ML-trained motor policies handle motion control. Reference architecture is the GrowBot project (britcruise9/GrowBot), significantly expanded in form factor and capability.

---

## System Architecture

### Edge Layer

Two Raspberry Pi Zero 2 W units with distinct roles. They communicate with each other via a local message queue (protocol finalized in Phase 01). Neither Pi handles LLM inference directly.

**Pi-M (Motion Pi)**  
Runs the motor control loop at a fixed tick rate, independent of LLM round-trip latency. Responsible for all physical actuation and near-field sensing.

- DC motors via H-bridge driver (tread locomotion)
- Feetech serial bus servos (left shoulder, right shoulder, head rotation)
- VL53L1X time-of-flight sensor (close-range obstacle detection, I²C)
- MPU-6050 IMU (orientation, I²C)
- WS2812B LED ring (emotional/status expressiveness)
- MAX98357A I²S amplifier + speaker (audio output -- assignment TBD Phase 01)
- SPST power switch

Motion loop runs continuously. LLM intent updates arrive asynchronously from Pi-V and are consumed at loop tick. The loop never blocks waiting for Pi-V or the home lab.

**Pi-V (Vision Pi)**  
Handles all network-dependent work. Runs the LLM agent loop, manages camera capture, processes voice input, detects offline state, and pushes intent updates to Pi-M.

- 8MP 1080p CSI camera (event-triggered capture, not continuous streaming)
- INMP441 I²S microphone (voice input)
- Audio output (assignment TBD Phase 01 -- may share speaker with Pi-M or have dedicated)

Vision queries to the LLM are event-triggered. Meaningful triggers: motion stop, proximity alert from Pi-M, voice input detected, elapsed interval threshold. Continuous frame streaming is not used; it saturates WiFi and the inference backend.

### Inference Layer

LLM inference runs on the existing home lab infrastructure: RTX 3080 desktop (primary interactive node) or Proxmox cluster (async batch), routed through the existing LiteLLM proxy from the Agentic OS project. Johnny 5 is a consumer of that infrastructure. No separate serving layer is stood up for this project.

LLM comms are fully async and non-blocking relative to the Pi-M motion loop. The intent message contract between Pi-V and Pi-M is defined in Phase 01.

### Offline Resilience

Target: survive network outages up to 5 minutes without failure or loss of physical safety.

Mechanism: Pi-V detects LiteLLM endpoint unreachable → sends offline signal to Pi-M via message queue → Pi-M enters conservative fallback mode: stop treads, hold servo positions, set LED ring to offline-state color pattern → on reconnect, Pi-V signals Pi-M → resume from idle or last valid intent state.

Fallback must be functional before any cognition code is written. It is a Phase 01 gate condition.

### Simulation

Motion policy training runs on the home lab, not on the Pi. MuJoCo (MJCF format) is used for the simulation environment, consistent with the GrowBot reference. Trained policies are compiled to a compact deployable format (ONNX preferred) and transferred to the relevant Pi for inference at runtime.

---

## Hardware Inventory (Andrew Currently Owns)

| Item | Qty | Notes |
|---|---|---|
| Raspberry Pi Zero 2 W | 2 | Each with microSD card, pre-soldered GPIO headers, 8MP 1080p CSI camera |
| Creality Ender 3 Pro | 1 | Parts production; 220×220×250mm build volume |
| FreeCAD 1.1.1 | — | Mechanical design; parametric modeling |
| RTX 3080 workstation (128GB RAM) | 1 | Primary inference node for home lab |
| Proxmox cluster (5 nodes, 24TB NAS) | 1 | Orchestration and async batch processing |

Hardware not yet selected (Phase 00 scope): DC motors, H-bridge driver, tread system, arm/head servos, VL53L1X ToF sensor, IMU, audio components, battery and power management.

---

## Tech Stack (Locked In)

| Layer | Technology |
|---|---|
| Edge compute | Raspberry Pi Zero 2 W (×2), Raspberry Pi OS Lite 64-bit |
| Mechanical design | FreeCAD 1.1.1 |
| Parts production | Creality Ender 3 Pro (PLA or PETG) |
| Simulation | MuJoCo (MJCF format), home lab |
| Policy deployment format | ONNX (preferred) |
| Inference routing | Home lab LiteLLM proxy (Agentic OS infrastructure) |
| Primary language | Python |
| Version control | GitHub (repo: `short_circuit`) |

---

## Git Workflow

`main` is always deployable. All work occurs on branches.

**Branch naming:**
- `phase/00-hardware`, `phase/01-infra`, etc. for phase-level work
- `feat/short-description` for features within a phase
- `fix/short-description` for bug fixes
- `sim/short-description` for simulation and training work
- `docs/short-description` for documentation

**Commits:** Conventional Commits format. Allowed types: `feat`, `fix`, `docs`, `chore`, `test`, `sim`, `hw` (hardware design files). Examples:
- `feat: add VL53L1X driver and polling loop`
- `sim: add shoulder servo MJCF model`
- `hw: update arm FreeCAD parametric model`

**Merging:** Squash merge to `main` via PR. No merge commits on `main`. Linear history enforced.

**Tagging:** Tag `main` at each phase gate: `v0.0` through `v5.0`. Iteration tags within a phase use minor version: `v2.1`, `v2.2`, etc.

---

## Phase Structure

| Phase | Name | Gate Condition |
|---|---|---|
| 00 | Hardware Design & BOM | BOM finalized and approved; body design baselined in FreeCAD |
| 01 | Infrastructure & Repository | Both Pis communicate with each other and with home lab LiteLLM; offline fallback functional |
| 02 | Locomotion | Robot drives forward, backward, and turns on command via trained policy |
| 03 | Manipulation | Arms and head respond to commanded positions with servo position/load feedback |
| 04 | Cognition | Robot responds to voice input with coordinated motion and speech |
| 05 | Integration & Hardening | Full stack stable; offline resilience tested; performance profiled |

Each phase has a dedicated coordinator document in `/phases/`.

---

## Key Design Decisions

**Two Pis, split roles.** Motion control has hard timing requirements; LLM comms are inherently latency-variable. Separating them ensures the motion loop is never blocked by network conditions.

**Single camera + ToF sensor over stereo vision.** The Pi Zero 2 W has one CSI port. Stereo depth perception requires a multiplexer (Arducam), adding complexity and latency for modest gain at tread-robot operating scales. VL53L1X on Pi-M handles close-range obstacle detection with sub-millisecond response. The 8MP camera on Pi-V handles visual reasoning queries. Stereo is deferred to a future phase if warranted.

**LLM comms event-triggered, not continuous.** Continuous frame streaming would saturate the home network and inference backend. Triggers are meaningful state changes, not frame rate.

**Feetech SCS0009-family serial bus servos for arms and head.** Consistent with GrowBot reference architecture. Serial bus reduces wiring versus independent PWM servos. Position and load feedback from each servo enables data collection for ML training from real hardware.

**Home lab inference, not cloud.** Reduces per-call cost, keeps data local, avoids cloud dependency for operation. Offline fallback covers gap periods.

**MuJoCo for simulation.** Free, well-supported, used in the GrowBot reference. Training on home lab hardware; compact policy deployment to Pi.

---

## Session Configuration

Per-phase model and effort level recommendations. These are defaults -- escalate to a higher-capability model mid-session if a task proves more complex than anticipated.

| Phase | Model | Thinking | Effort | Rationale |
|---|---|---|---|---|
| 00 | Opus | Extended | High | Hardware selection balances multiple competing constraints across power, torque, form factor, cost, and printability. Extended Thinking carries the analytical load; High effort is sufficient. |
| 01 | Sonnet | Standard | Medium | Well-defined infrastructure tasks with clear reference material and no novel architecture decisions. Thoroughness here means correct execution, not deep reasoning. |
| 02 | Opus | Extended | Extra | Highest technical stakes in the project. Simulation design and reward shaping mistakes compound through training and surface late. Warrants Extra over High. |
| 03 | Sonnet | Standard | Medium | Serial bus servo integration is well-documented via GrowBot reference. Tasks are specific and constrained. Same logic as Phase 01. |
| 04 | Opus | Extended | Extra | Most architecturally complex phase. Agent loop concurrency, failure mode design, and system prompt engineering all benefit from thorough treatment. |
| 05 | Sonnet | Extended | High | Integration debugging involves ambiguous failure modes; Extended Thinking adds genuine value there. Behavioral tuning and documentation do not warrant Extra. |

Max effort is not recommended for any phase in this project. These are engineering problems with established techniques, not novel research. Extra is the ceiling.

Within a phase, it is acceptable to drop to Sonnet and Medium effort for routine implementation tasks (boilerplate, config files, deployment scripts) even if the phase default is Opus and Extra. The phase recommendation reflects the configuration suited to the hardest task in that phase, not every task.

---

## Token Discipline

These rules apply in every session regardless of phase or model.

**Before generating output:** Outline the approach in two to three sentences and wait for confirmation before writing code, creating files, or producing multi-section documents. Exception: single-function utilities and scripts under 30 lines may be produced directly.

**Ambiguity:** One targeted question, then wait. Make a recommendation rather than listing options and asking which to choose. The human responds with a correction or confirms -- do not pre-generate multiple paths.

**In-session:** No status narration between tasks. No restating of the task before executing it. No preamble before code blocks beyond a single identifying sentence.

**Documents in context:** Do not repeat or summarize content from CLAUDE.md or the active phase file. Reference by section name only.

**Alternatives:** Do not produce multiple implementation alternatives unless explicitly asked. Implement the recommended approach and adjust based on feedback.

**Context window:** When the session context is long and the current task is reaching a natural boundary, flag it and suggest closing the session. Provide the decision log and a pre-filled initiating prompt for the next session rather than continuing in a bloated context.

**Session close:** Produce a decision log -- a compact list of decisions made this session and their rationale. Do not recap work done. The log is the handoff artifact for the next session's initiating prompt.

---

## Style & Operating Preferences

Tone is direct. No preamble phrases, no hedging. Prose over bullets in explanations and documents unless a list is structurally necessary. En-dashes for ranges; no em-dashes in prose. No unsolicited professional advice disclaimers in technical contexts. Code comments are functional and specific -- they explain why, not what. When ambiguity exists, ask one targeted question rather than making an assumption and proceeding.
