# Chassis Sim — Tuning & Sim-vs-Reality Log

Assumptions baked into the simulation that must be confirmed against hardware
during the Phase 02 physical integration test (Task 6). Record measured values
and any sim adjustments here as they are made.

| Quantity | Sim value | Basis | Confirm by | Status |
|---|---|---|---|---|
| Motor stall torque | 0.25 N·m / motor | Pololu 150:1 HPCB ~0.41 N·m @12 V, scaled to 7.4 V | Bench stall test (current × Kt, or lever + scale) | open |
| Motor no-load speed | 12.9 rad/s (~0.30 m/s) | ~200 rpm @12 V scaled to 7.4 V | No-load wheel RPM on the bench | open |
| Ground friction (slide) | 1.0 | Hardwood/tile default | Drive on target floor; compare slip/accel | open |
| Wheel/track friction (slide) | 1.2 | TPU 90A lug estimate | Measure no-slip tractive limit | open |
| Trunk CoM height | 0.110 m | Mass-weighted estimate from components.csv | FreeCAD CoM report or balance test | open |
| Trunk effective inertia height | 0.18 m | Box-proxy modelling constant | Optional: bifilar/measured yaw inertia | open |
| In-place yaw cap | ~0.34 rad/s | Sim measurement, condim=3 skid | Measure real spin rate | open |

## Known sim → reality gaps to watch

- **Motor asymmetry.** Sim treats both sides identically. Real gearmotors differ;
  expect a straight-line drift to correct (bias term or per-side gain in the
  deployment shim, not necessarily a retrain).
- **Track compliance & slip.** Rigid wheels approximate a compliant TPU belt.
  If real turns are easier/harder than sim, adjust `WHEEL_FRICTION` slide and/or
  bump contacts to `condim=4` to add torsional friction.
- **Caster scrub.** The rigid sphere does not swivel; if the real swivelling
  caster changes turn dynamics noticeably, model the trailing arm explicitly.

## Observation reconstruction on Pi-M (Task 5)

The policy consumes a 9-element observation. In sim these come from MuJoCo
ground-truth sensors; on Pi-M each must be reconstructed from real hardware and
fed to `locomotion_v1.onnx` in the **same order and units** (`env.py` `_obs()`
is the authoritative layout).

| Obs channel | Sim source | Pi-M source |
|---|---|---|
| forward velocity | `framelinvel` (body x) | encoder odometry: mean drive-wheel speed × wheel radius |
| lateral velocity | `framelinvel` (body y) | not directly measurable — set ~0 (small during skid turns); candidate sim-to-real gap |
| yaw rate | `gyro` z | MPU-6050 gyro z, directly |
| roll, pitch | `framequat` | MPU-6050 accel+gyro **fusion** (see note) |
| left/right wheel speed | `jointvel` (rear wheels) | quadrature encoders (GPIO 17/27, 22/23), counts → rad/s |
| command (v, w) | episode command | intent from the motion loop (Pi-V → Pi-M) |

**Roll/pitch come from IMU fusion — this is the accelerometer's job.** The
MPU-6050 (BOM §3, I²C 0x68) is a 6-axis IMU: 3-axis accelerometer + 3-axis gyro.
Roll and pitch are obtained by fusing the accelerometer's gravity vector (the
absolute tilt reference) with the gyro's angular rate (drift-free over the short
term); the gyro alone drifts and the accelerometer alone is noisy under
acceleration. Use a complementary filter or the MPU-6050's onboard DMP. **No
separate accelerometer is needed — it is already inside the IMU.**

**No magnetometer → no absolute heading.** The MPU-6050 has no magnetometer, so
yaw is gyro-integrated and drifts. That is fine for Phase 02 because the policy
uses yaw *rate* only, never absolute heading. If a later phase needs
heading-hold or map-relative navigation, upgrade to a 9-axis IMU (ICM-20948 /
MPU-9250).
