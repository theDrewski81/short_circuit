# Initiating Prompt

Read `CLAUDE.md`. Then read the active phase coordinator in `/phases/`. Follow all instructions in both documents.

## Current Phase

Phase 02 — Locomotion (`phases/PHASE_02_LOCOMOTION.md`). **Next task: Task 6b — Floor Integration Test, currently blocked** on mechanical work (motors must be chassis-mounted and drive wiring off breadboard). Tasks 1, 2, 3, 4, 5 and 6a are complete.

Progress so far — the sim/policy track (Tasks 3–5) is complete:

- **Task 3** — chassis MuJoCo env in `simulation/chassis/` (CAD-locked params bridge, generated MJCF, command-conditioned Gymnasium env). Stable under random + scripted policies.
- **Task 4** — PPO trained on the desktop (CPU); best of 3 seeds exported to `policies/locomotion_v3.onnx`. Scaffold: `train.py`, `config.yaml`, `export_onnx.py`, `cem_smoke.py`, `simulation/chassis/TRAINING_WINDOWS.md`.
- **Task 5** — `src/motion/locomotion_policy.py` (ONNX runner; validated 0.02 ms/step on x86, correct command directions), `scripts/test_locomotion_policy.py`, `scripts/setup_motion_pi.sh`, and a documented `execute_intent()` seam in `src/motion/main.py` (inactive until `MotorDriver` exists).

Remaining for the gate: **Task 6b** only (floor integration: drive on the floor, live offline-fallback test, log sim-vs-real deltas in `simulation/chassis/TUNING.md` -- **blocked** until motors are chassis-mounted and drive wiring is off breadboard). Tasks 1, 2 and 6a are complete (see decision log).

**Recommended config for Task 6b: Sonnet, Standard thinking, Medium effort.** The remaining work is bench/floor procedure and tuning-log capture against code that already exists, not new architecture. Escalate to Opus if the sim-to-real deltas turn out large enough to require revisiting the policy or the reward shaping.

## Phase 01 Closure Summary (gate met 2026-06-22)

All three gate clauses satisfied:

1. **Both Pis communicate bidirectionally** -- verified via real MQTT pub/sub round-trip through the Mosquitto broker, `johnny5-motion` -> `sn-mosquitto` -> `johnny5-vision`, using each Pi's actual `.env` credentials (not just broker-to-host as in earlier testing).
2. **Pi-V successfully calls LiteLLM and receives a response** -- `scripts/test_llm_client.py` on `johnny5-vision`, 8.94s round trip, real response from `vision-batch` (llava:7b).
3. **Offline fallback engages/clears correctly** -- verified as unit-tested pure logic (8/8 passing in `tests/test_offline_fallback.py`, covering all three state transitions plus the never-raises guarantee). **Caveat:** this has not been exercised live against the real LiteLLM endpoint going down, since `src/motion/main.py`'s MQTT/intent wiring is still a Phase 01 stub by design ("no motion control or cognition code is written in this phase"). The phase doc's own design intent was for the state machine to be independently testable without hardware/network -- it was built that way and passes -- so this is treated as satisfying the gate. A live engage/clear test against the real endpoint is deferred to Phase 02, once `main.py` is no longer stubbed and there's an actual loop to observe reacting.

Tag `v1.0` on `main` per CLAUDE.md's phase-gate tagging convention -- not yet done, do this before/when starting Phase 02 work.

Carried-forward non-blockers (not gate conditions, just open items):

## Open Questions (non-blocking, carried forward)

- SSH key auth for the Pis -- deferred. Both Pis currently use password auth via Devolutions RDM. Revisit: clear RDM's cached host key for the IP/entry first (caused a false "public key doesn't match" error last attempt) before retrying key-based auth.
- `.env` secrets management (local per-Pi vs. Agentic OS secrets manager) -- unresolved, no preference given yet.

## Decision Log

(Most recent session first. Append new entries above old ones.)

### 2026-08-10 -- Task 6a complete; calibration method corrected

- **The 150.58:1 N20 gearbox is not backdrivable at the output shaft.** This
  supersedes the 2026-07-16 entry below, which described 6a as a hand-rotation
  test with motors off. It is not: the wheel will not turn by hand, and the
  force needed to move it would split the gearcase before the shaft moved a
  useful amount. Confirmed mechanical rather than electrical by detaching the
  motor from the TB6612 entirely and finding it still locked, which rules out
  the short-brake state (IN1=H, IN2=H) that floating pins can leave behind
  after `MotorDriver.close()` releases them.
- **`--calibrate` rewritten as a powered measurement.** One wheel at a time at
  low duty with the driver enabled; Andrew taps Enter at each pass of a mark on
  the wheel; the script least-squares-fits encoder count against revolution
  index. Fitting the slope rather than dividing total counts by revolutions is
  the point -- a constant human reaction lag moves the intercept and leaves the
  slope untouched, so the result does not depend on Andrew's reflexes being
  fast, only on them being consistent.
- **Result: 450.6 counts/output-rev, left/right spread 0.4%.** This confirms
  rather than replaces the derived constant. `COUNTS_PER_OUTPUT_REV` stays at
  **451.74** (= 3 quadrature cycles/motor-rev x 150.58 gearbox), because that
  figure is fixed by integer tooth and pole counts while the measurement
  carries tap-timing noise; the 0.25% gap is noise, not a physical difference.
  What the measurement actually settled is the question it was designed for --
  `gpiozero.RotaryEncoder` is decoding **1x, not 4x**, so the alternative
  candidate of ~1807 is dead. A 4x decode would have been a factor-of-four
  error in every downstream speed and odometry figure.
- **`--dwell` added to `scripts/test_motors.py`**: uniform multiplier on every
  sleep in the bench sequence, replacing the ad-hoc long durations that had been
  edited directly into the Pi's working copy and were blocking `git pull`.
- **Motor retention cap designed -- the reason the motors were still loose.**
  `build_chassis.py` modelled each cradle as an open-top drop-in slot "retained
  by a cap" (line 75) that was never built: no cap solid, no export, no
  `motor_cap_v1.stl`, and no fastener provision in the cradle. The 16 mm cradle
  left 2 mm of material either side of the 12 mm slot, too thin to tap M2, so
  the cap could not simply be added on top -- the cradle had to change with it.
  `cradle_w` now derives from `motor_cap_screw_cc + boss_od` (27 mm) and carries
  four tapped M2 columns per side; `motor_cap()` exports `motor_cap_v1.stl`, one
  symmetric part printed twice. The plate is held `motor_cap_clamp_gap` above the
  cradle top so the screws preload the motor into the bore rather than bottoming
  the plate out first, and the saddle is cut at nominal motor radius so it grips.
  Also fixed alongside: the drop-in slot was exactly `motor_dia` wide, zero
  clearance against a 12 mm motor, and now carries the same `motor_fit_clear` as
  the bore. Four new checks in `preview/validate.py` guard the derived geometry
  (columns clear the slot, screws land on the cradle top, cradle stays inside the
  rear wall, saddle grips); 24/24 pass. **The tub geometry changed, so
  `chassis_tub_v1.stl` needs regenerating and reprinting.** Geometry was verified
  arithmetically only -- FreeCAD is not available in the agent sandbox, so the
  `freecadcmd` run and a look at the solid are Andrew's.

### 2026-07-16 -- Task 1/2 landed; Task 6 split on mechanical blocker

- **Task 1 (`MotorDriver`) confirmed complete** and **Task 2 activated**: real
  `_read_motion_state()` on Pi-M via a new `src/motion/mpu6050.py` (accel+gyro
  complementary filter for roll/pitch, gyro-z passthrough for yaw_rate;
  I2C-backend-abstracted so it's unit-testable without a Pi) fused with
  `EncoderReader` odometry (`WHEEL_RADIUS_M = 0.0235` m, derived from
  `mechanical/freecad/params.csv` sprocket_pitch_dia/2 + track_thickness --
  CAD-derived, not bench-confirmed). `execute_intent()` in `src/motion/main.py`
  activated exactly per the seam staged in Task 5: hardware bundled into an
  injectable `MotionHardware` dataclass (motor_driver/policy/imu/encoders) so
  tests swap in fakes instead of touching GPIO/I2C/onnxruntime; MotorDriver
  enable/disable now runs every tick, coordinated with the offline fallback
  state (`_apply_fallback_output()`), independent of whether `execute_intent()`
  is even called. `idle` is intentionally excluded from the locomotion dispatch
  set (`move`/`turn`/`arc` only) -- it's a valid `command_from_intent()` input
  but a no-op for `execute_intent()` this tick; forced stop-on-disconnect comes
  from the fallback state machine, not intent-level idle. `src/shared/PROTOCOL.md`
  finalized the `move`/`turn`/`arc`/`idle` params schema to match
  `command_from_intent()` exactly and added `arc` to the action enum. 48/48
  sandbox tests pass (17 new).
- **Nextcloud mount truncation hit again** (see `sandbox-no-torch`/cloud-mount
  memory) -- the Edit tool silently truncated `tests/test_main_locomotion.py`
  mid-file; caught by a `SyntaxError` on the next test run, fixed by rewriting
  in `/tmp` and `cp`-ing over instead of editing the mounted copy directly.
  Reinforces: author in `/tmp`, `cp` to the repo, md5-verify -- for edits too,
  not just new files.
- **Task 6 split into 6a/6b** after Andrew flagged the motors are still loose
  and wired via breadboard. 6a (encoder calibration, `--calibrate`) is a
  stationary hand-rotation bench test -- motors stay OFF, only needs the
  encoder signal wiring to hold contact while stationary, so it's unaffected
  by the current build state and can run now. 6b (floor driving + live
  offline-fallback test) is blocked: loose motors have no rigid tread contact
  geometry (so "drives straight" isn't measurable), and breadboard jumpers are
  expected to work loose under tread vibration -- doing 6b now risks chasing a
  connection fault instead of a real bug. `phases/PHASE_02_LOCOMOTION.md`
  updated with the split and its rationale.

### 2026-06-26 -- Phase 02 sim + policy track (Tasks 3–5 complete)

- **Chassis sim (Task 3):** treads modelled as **four driven wheels** (front+rear per side spanning the wheelbase), NOT a deformable belt — a single wheel/side collapses the fore-aft contact patch and the tall robot nose-dives. DC motor = torque actuator (`gear = stall/2` per wheel) + joint `damping = stall/(2·no_load)` for brushed-motor torque-speed droop. Geometry is locked to `mechanical/freecad/params.csv` via `simulation/chassis/params.py`; the MJCF is generated by `build_mjcf.py` — **do not hand-edit `johnny5_chassis.xml`**. Measured envelope: ~0.30 m/s forward, ~0.34 rad/s in-place yaw (skid-steer resistance-limited); env caps V_MAX 0.28, W_MAX 0.30.
- **Training (Task 4):** SB3 PPO, 2×64 MLP, command-conditioned (forward/back/turn/arc/stop). **CPU-only on the desktop** — the net is too small to benefit from the 3080, and CPU skips CUDA setup. **PyTorch/SB3 cannot be installed in the Cowork sandbox** (proxy blocks the CPU wheel index, stalls CUDA wheels), so training is a desktop step; `cem_smoke.py` is the torch-free in-sandbox check. Andrew ran 3 seeds (~15 min each), exported the best → `policies/locomotion_v3.onnx`.
- **Two export bugs fixed** in `export_onnx.py`: `VecNormalize.load(venv=None)` crashes (it needs a live venv) → read the saved stats with a direct `pickle.load`; newer PyTorch defaults to the dynamo ONNX exporter (needs `onnxscript`) → forced `dynamo=False` (TorchScript). Added a `--best` flag (export `best/best_model.zip`).
- **Policy runner (Task 5):** `LocomotionPolicy` turns command + sensor state into (left,right) in [-1,1]. The 9-element observation MUST match `env._obs()` order/normalization exactly (the ONNX bakes in VecNormalize); the sensor-to-channel map is in `simulation/chassis/TUNING.md` ("Observation reconstruction on Pi-M"). Validated against `locomotion_v3.onnx`.
- **Accelerometer question:** no new part — the BOM **MPU-6050 is a 6-axis IMU** (3-axis accel + 3-axis gyro). Roll/pitch on Pi-M come from accel+gyro fusion; no magnetometer, so yaw is rate-only (fine for locomotion). Captured in `TUNING.md`.
- **Process:** the agent **may now create/switch branches** (commit/push/merge/tag stay with Andrew) — `CLAUDE.md` "Agent boundaries" updated. Sandbox git is unreliable on the Nextcloud mount and Write-tool edits there can land truncated — author in `/tmp` and `cp`, verify by md5. Phase work branch: `sim/chassis-env`.
- **BOM Section 1 pricing flag:** drive motors are ~$32.45 ea (Pololu #5219) vs the BOM's implied ~$23 ea — Section 1 runs ~$25 over (~$96 delivered to 98042, single Pololu order + cables clears the $75 free-ship threshold; bearings from Amazon). Worth updating the BOM / cost ceiling.

### 2026-06-22 -- Phase 01 gate closed

- LiteLLM virtual key minted on the AOS proxy (`sk-ft-osuRqKu2Eldav3HgAVw`, alias `johnny5-vision`, unrestricted). Required standing up DB-backed key management on the proxy (new Postgres DB on sn-pg-aos) -- previously config-file-only with no key store. Full writeup in `litellm_key_mgmt_vision_summary.md` (AOS-side session).
- Vision model: `vision-batch` alias -> `llava:7b` on ms3 (192.168.1.225), a CPU-only Ollama node chosen so vision inference doesn't contend with desktop GPU work. Expect 15-40s/image, longer on cold load -- `.env.example` `LITELLM_TIMEOUT` raised from the 8.0s placeholder to 60.0s accordingly (the old default would have aborted every call before the model responded).
- `.env.example` fully filled in: LiteLLM endpoint/key/model, MQTT broker host/user (password left as placeholder, correctly -- it's the one genuinely secret value).
- `scripts/test_llm_client.py` run on `johnny5-vision`: passed, 8.94s round trip, real response from `vision-batch`.
- MQTT round-trip verified Pi-to-Pi (not just ms1<->sn-mosquitto as before): `mosquitto_pub` from `johnny5-motion` received by `mosquitto_sub` on `johnny5-vision`, both using `.env` credentials. `mosquitto-clients` installed on both Pis for this.
- **Phase 01 gate condition met in full.** Ready to move to Phase 02 (Locomotion) when Andrew is ready -- per CLAUDE.md session config table, Phase 02 recommends Opus, Extended Thinking, Extra effort (highest stakes phase, simulation/reward-shaping mistakes compound and surface late).

### 2026-06-20 (cont'd -- Pi OS setup, networking)

- Both Pis flashed with Raspberry Pi OS Lite 64-bit (Trixie / `VERSION_CODENAME=trixie`), username `administrator` on both. `scripts/_common.sh` default `JOHNNY5_USER` updated from `pi` to `administrator` to match.
- SSH key auth attempted first via Raspberry Pi Imager's public-key field, but failed two ways in sequence: (1) hostname resolution -- `johnny5-motion` without `.local` doesn't resolve via mDNS from Andrew's client, needed `.local` suffix or direct IP; (2) once on IP, Devolutions RDM threw "entry's public key doesn't match the server's key" -- this is an SSH *host key* mismatch (RDM had a stale cached host fingerprint for that IP/entry from before reflashing), not a client auth-key problem. Rather than debug RDM's host-key cache, both cards were reflashed with password auth only. **Key-based auth is deferred, not abandoned** -- revisit later, and when doing so, clear/reset the host key entry in RDM first to avoid repeating the same false error.
- Static IPs assigned: `johnny5-motion` = `192.168.1.217`, `johnny5-vision` = `192.168.1.218`, both inside Andrew's router reservation block (outside the DHCP pool, so no collision risk). Configured via `nmcli connection modify <profile> ipv4.method manual ...` rather than router-side DHCP reservation (Andrew's explicit choice) or legacy `/etc/dhcpcd.conf` (dhcpcd is inactive on this OS version -- NetworkManager is the active backend, fronted by netplan -- connection profiles are named `netplan-wlan0-SuskNet` / `netplan-eth0`). Confirmed static IPs survive reboot.
  - Caveat noted but not yet hit: profiles are netplan-managed (`netplan-` prefix), so a future `netplan apply` or netplan YAML edit could theoretically regenerate/overwrite the NetworkManager profile and revert the static IP. Not a problem unless netplan config is touched again -- flag if static IPs mysteriously revert.
- `scripts/_common.sh` defaults switched from `johnny5-motion.local` / `johnny5-vision.local` to the static IPs directly (`192.168.1.217` / `192.168.1.218`), since `.local` mDNS resolution was unreliable from Andrew's dev machine during the SSH troubleshooting above.

### 2026-06-20 (cont'd -- johnny5-motion interface setup)

- `johnny5-motion`: ran `apt update/upgrade` and installed `python3-pip python3-venv git i2c-tools`. Enabled I2C + SPI via `raspi-config`; confirmed `/dev/i2c-1` and `/dev/i2c-2` present, `i2cdetect -y 1` runs clean (empty grid expected -- no sensors wired yet).
- Serial port: disabled login shell over serial, enabled serial port hardware via `raspi-config`. Added `dtoverlay=disable-bt` to `/boot/firmware/config.txt` (Trixie moved this from `/boot/config.txt`).
  - First attempt failed silently: piped `echo "dtoverlay=disable-bt" | sudo tee -a ...` as an instruction, but the literal command string got typed into the file as text rather than executed, so the overlay never loaded. `/dev/serial0` was symlinked to `ttyS0` (mini-UART -- baud drift risk under CPU freq scaling, bad for Feetech servo comms) instead of the PL011 hardware UART. Caught via `dmesg | grep tty` showing both `ttyAMA1` (registered, unused) and `ttyS0` (in use) plus a live Bluetooth RFCOMM entry.
  - Fixed by editing `/boot/firmware/config.txt` directly (`sudo nano`) and adding the bare `dtoverlay=disable-bt` line. After reboot, confirmed `/dev/serial0 -> ttyAMA0`, Bluetooth/RFCOMM gone from `dmesg`. **Lesson: don't pipe shell commands as instructions into a file edit -- edit the file directly.** Apply the same direct-edit approach when doing this on `johnny5-vision`.
- `johnny5-motion` interface setup (task 2, Pi-M-specific portion) complete. Next: Python venv + repo clone on `johnny5-motion`, then repeat OS/interface setup on `johnny5-vision` (camera enable instead of serial/UART).

### 2026-06-20 (cont'd -- Mosquitto live, moving to Pi OS setup)

- Mosquitto LXC (`sn-mosquitto`, host `ms1`, IP `192.168.1.227`) is deployed, authenticated, and verified end-to-end: `mosquitto_pub` from `sn-mosquitto` received by `mosquitto_sub` on `ms1` over the LAN. Broker piece of the Phase 01 gate is closed.
  - Hit and fixed two deploy snags, both folded into `scripts/deploy_mosquitto_lxc.md`: (1) duplicate `persistence`/`persistence_location` between the default `mosquitto.conf` and `johnny5.conf` -- removed from the latter; (2) `mosquitto.service` exit 13 on start -- caused by `/etc/mosquitto/passwd` never actually being created by the earlier `mosquitto_passwd -c` step. Recreated it and fixed ownership (`root:mosquitto`, `640`).
  - `.env` MQTT values for both Pis: `MQTT_BROKER_HOST=192.168.1.227`, `MQTT_BROKER_PORT=1883`, `MQTT_USERNAME=johnny5`, password as set during passwd creation.
- LiteLLM API key mint + vision model selection explicitly deferred -- not blocking the next step. Tagged as an item to return to once Pi-side work reaches the point of testing `llm_client.py` (`test_llm_client.py` must run on Pi-V, which requires the Pis to be flashed first).
- Andrew has both Pi Zero 2 W units in hand but unflashed. Next focus: Phase 01 task 2 (Pi OS setup) -- flash Raspberry Pi OS Lite 64-bit on both, configure hostnames (`johnny5-motion`, `johnny5-vision`), SSH, WiFi, then per-Pi package/interface setup.

### 2026-06-20

- LiteLLM endpoint confirmed: `http://192.168.1.223:4000/v1`. Set in `.env.example`. Reused from the existing Agentic OS LiteLLM server -- no second server stood up, per CLAUDE.md ("Johnny 5 is a consumer of that infrastructure").
- Johnny 5 will use a separate LiteLLM virtual API key from Agentic OS, for usage/cost isolation. Key not yet minted -- `.env.example` still has `<key>` placeholder.
- Vision model string still unselected -- `.env.example` placeholder is `<vision-model-name>`. Must be vision-capable for camera queries.
- RabbitMQ (existing home-lab server) considered as broker but rejected in favor of a fresh Mosquitto deploy -- RabbitMQ lacks native retained-message semantics, which the `johnny5/offline` and heartbeat topics rely on, and would have required re-implementing that behavior in application code.
- Mosquitto deploy target: Proxmox LXC container (not Docker), per user preference. Runbook written at `scripts/deploy_mosquitto_lxc.md` -- manual steps, not an executable script, since cluster node names/storage pools aren't accessible from this session.
- Reviewed prior session's scaffolding (`src/motion/offline_fallback.py`, `src/vision/llm_client.py`, `src/motion/main.py`, `src/shared/PROTOCOL.md`, deployment scripts, tests): all consistent with phase doc spec. `tests/test_offline_fallback.py` -- 8/8 passing, covers all three state transitions plus the never-raises guarantee.
- Created top-level `README.md` (Phase 01 task 1 deliverable -- was missing).
- Did not touch uncommitted changes under `mechanical/` and `phases/PHASE_00`/`PHASE_06` found in working tree -- out of Phase 01 scope, flagged to user for separate handling.
