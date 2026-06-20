# Johnny 5

A playful, Johnny 5-inspired (*Short Circuit*, 1986) autonomous robot. Tread-driven
locomotion, two articulated arms, a rotating head, voice I/O, and visual perception.
An LLM handles reasoning and communication; ML-trained motor policies handle motion
control.

Full project brief: [`CLAUDE.md`](./CLAUDE.md).

## Architecture

Two Raspberry Pi Zero 2 W units with distinct roles, communicating over MQTT via a
Mosquitto broker on the home lab.

- **Pi-M (Motion)** — fixed-rate motor control loop, tread drive, arm/head servos,
  ToF + IMU sensing, LED status ring. Never blocks on the network.
- **Pi-V (Vision)** — camera capture, voice input, and the LLM agent loop. Calls out
  to a home lab LiteLLM proxy and pushes intent updates to Pi-M.

LLM inference runs on existing home lab infrastructure (RTX 3080 / Proxmox cluster)
via LiteLLM — no dedicated serving layer for this project. Motion policies are
trained in MuJoCo on the home lab and deployed to Pi-M as ONNX.

See `src/shared/PROTOCOL.md` for the Pi-M ↔ Pi-V message contract.

## Repository Layout

```
mechanical/   FreeCAD source + STL exports
phases/       Per-phase coordinator documents
src/          motion/ (Pi-M), vision/ (Pi-V), shared/ (message contracts)
simulation/   MuJoCo models and training code
policies/     Trained policy exports (ONNX)
scripts/      Setup, deployment, and maintenance scripts
```

## Status

Currently in **Phase 01 — Infrastructure & Repository**. See
[`phases/PHASE_01_INFRASTRUCTURE.md`](./phases/PHASE_01_INFRASTRUCTURE.md) for
gate conditions and [`INITIATING_PROMPT.md`](./INITIATING_PROMPT.md) for the
current session handoff state.
