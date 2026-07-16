# Inter-Pi Communication Protocol

Transport: MQTT via Mosquitto broker hosted on the home lab (Proxmox container). Both Pis are clients of the broker -- no direct Pi-to-Pi sockets.

Broker address and credentials are supplied via environment variables, not hardcoded:

```
MQTT_BROKER_HOST=<home-lab-ip>
MQTT_BROKER_PORT=1883
MQTT_USERNAME=<set on broker deploy>
MQTT_PASSWORD=<set on broker deploy>
```

This document is the contract between Pi-M and Pi-V code. Update it if any schema changes.

---

## Topics

### `johnny5/intent`

Direction: Pi-V → Pi-M
QoS: 1
Retained: false

Current behavior intent, published whenever Pi-V's agent loop produces a new decision.

```json
{
  "timestamp": "2026-06-19T14:32:01.123Z",
  "intent_id": "uuid4",
  "action": "move | turn | arc | arm_pose | head_pose | idle | speak",
  "params": {},
  "priority": "normal | urgent"
}
```

`params` shape depends on `action`. Locomotion actions (`move`, `turn`, `arc`, `idle`) are defined below as of Phase 02 Task 2 -- they match `command_from_intent()` in `src/motion/locomotion_policy.py` exactly; that function is the authoritative implementation, this table is the contract. `arm_pose` / `head_pose` params land in Phase 03; `speak` params land in Phase 04. Pi-M does not block waiting for this topic -- it reads the latest retained value at each tick and no-ops if nothing new has arrived.

**Locomotion `params` (Phase 02):**

| `action` | `params` | Meaning |
|---|---|---|
| `move` | `{"speed": -1.0..1.0}` | Straight-line command. `speed` scales to `v_cmd = speed * V_MAX` (m/s); `w_cmd = 0`. Positive = forward, negative = reverse. |
| `turn` | `{"rate": -1.0..1.0}` | Turn-in-place command. `rate` scales to `w_cmd = rate * W_MAX` (rad/s); `v_cmd = 0`. **Positive = CCW / left turn**, negative = CW / right turn. |
| `arc` | `{"speed": -1.0..1.0, "rate": -1.0..1.0}` | Combined forward/turn. Both fields scale as above and are applied together. Missing fields default to `0.0`. |
| `idle` | `{}` (ignored) | Explicit hold-still: `command_from_intent()` maps this to `(v_cmd, w_cmd) = (0, 0)`. Note: `src/motion/main.py`'s `execute_intent()` currently dispatches only `move`/`turn`/`arc` through the policy -- an `idle` intent is a locomotion no-op for that tick, not a forced stop (the offline fallback state machine, not intent-level idle, is what forces treads to stop). |

`speed` and `rate` are clamped to `[-1, 1]` before scaling; out-of-range values are silently clamped, not rejected. `V_MAX` (0.28 m/s) and `W_MAX` (0.30 rad/s) are defined in `src/motion/locomotion_policy.py` and must stay in lock-step with `simulation/chassis/env.py` -- if either changes, the policy needs retraining/re-export, not just a constant edit.

### `johnny5/status`

Direction: Pi-M → Pi-V
QoS: 0
Retained: true

Motion state, servo positions, ToF reading. Published once per motion loop tick or on a throttled interval (TBD Phase 02, to avoid saturating the broker at 50Hz).

```json
{
  "timestamp": "2026-06-19T14:32:01.143Z",
  "state": "ONLINE | OFFLINE | RECOVERING",
  "tread_pwm": [0, 0],
  "servo_positions": {
    "shoulder_left": 0,
    "shoulder_right": 0,
    "head": 0
  },
  "tof_mm": 0,
  "imu": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0}
}
```

### `johnny5/offline`

Direction: Pi-V → Pi-M
QoS: 1
Retained: true (so Pi-M sees the current value immediately on reconnect/restart)

Boolean online/offline signal, published by Pi-V when it detects the LiteLLM endpoint is unreachable or has recovered.

```json
{
  "offline": true,
  "timestamp": "2026-06-19T14:32:01.000Z",
  "reason": "endpoint_unreachable | timeout | manual"
}
```

### `johnny5/heartbeat/motion`

Direction: Pi-M → broker
QoS: 0
Retained: true

```json
{"timestamp": "2026-06-19T14:32:01.000Z"}
```

Published every motion loop tick or on a throttled interval. Pi-V uses absence of a heartbeat for >30s as one trigger for `ONLINE -> OFFLINE` (per the offline fallback state machine spec, though that transition is actually evaluated on Pi-M from its own loop timing, not from this topic -- this topic is for external/Pi-V-side liveness checks and `check_health.sh`).

### `johnny5/heartbeat/vision`

Direction: Pi-V → broker
QoS: 0
Retained: true

```json
{"timestamp": "2026-06-19T14:32:01.000Z"}
```

Same shape and purpose as `johnny5/heartbeat/motion`, mirrored for Pi-V.

---

## Notes

- All timestamps are ISO 8601 UTC.
- `intent_id` lets Pi-M log which intent was last successfully executed, useful for debugging latency and for the `RECOVERING -> ONLINE` transition (first valid intent received).
- Schema was intentionally minimal for Phase 01. Phase 02 (this document) finalized the locomotion `action`/`params` enum (`move`/`turn`/`arc`/`idle`, see the table above) and added `arc` to the enum. `arm_pose`/`head_pose` params remain TBD, to land with Phase 03 manipulation; `speak` params remain TBD, to land with Phase 04 cognition -- update this document when they do.
