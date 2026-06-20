# Initiating Prompt

Read `CLAUDE.md`. Then read the active phase coordinator in `/phases/`. Follow all instructions in both documents.

## Current Phase

Phase 01 — Infrastructure & Repository (`phases/PHASE_01_INFRASTRUCTURE.md`)

## Status

Repo scaffolding, PROTOCOL.md, offline fallback state machine, motion loop skeleton, and deployment scripts in progress. See the most recent decision log (below or in session handoff) for specifics completed and open items.

## Open Questions Blocking Full Gate

- LiteLLM API key and target model string -- unconfirmed. Endpoint URL is now known. `llm_client.py` still stubbed pending key mint and vision-model selection.
- SSH key distribution method for the Pis -- unresolved (no preference given).
- `.env` secrets management (local per-Pi vs. Agentic OS secrets manager) -- unresolved (no preference given).

## Decision Log

(Most recent session first. Append new entries above old ones.)

### 2026-06-20

- LiteLLM endpoint confirmed: `http://192.168.1.223:4000/v1`. Set in `.env.example`. Reused from the existing Agentic OS LiteLLM server -- no second server stood up, per CLAUDE.md ("Johnny 5 is a consumer of that infrastructure").
- Johnny 5 will use a separate LiteLLM virtual API key from Agentic OS, for usage/cost isolation. Key not yet minted -- `.env.example` still has `<key>` placeholder.
- Vision model string still unselected -- `.env.example` placeholder is `<vision-model-name>`. Must be vision-capable for camera queries.
- RabbitMQ (existing home-lab server) considered as broker but rejected in favor of a fresh Mosquitto deploy -- RabbitMQ lacks native retained-message semantics, which the `johnny5/offline` and heartbeat topics rely on, and would have required re-implementing that behavior in application code.
- Mosquitto deploy target: Proxmox LXC container (not Docker), per user preference. Runbook written at `scripts/deploy_mosquitto_lxc.md` -- manual steps, not an executable script, since cluster node names/storage pools aren't accessible from this session.
- Reviewed prior session's scaffolding (`src/motion/offline_fallback.py`, `src/vision/llm_client.py`, `src/motion/main.py`, `src/shared/PROTOCOL.md`, deployment scripts, tests): all consistent with phase doc spec. `tests/test_offline_fallback.py` -- 8/8 passing, covers all three state transitions plus the never-raises guarantee.
- Created top-level `README.md` (Phase 01 task 1 deliverable -- was missing).
- Did not touch uncommitted changes under `mechanical/` and `phases/PHASE_00`/`PHASE_06` found in working tree -- out of Phase 01 scope, flagged to user for separate handling.
