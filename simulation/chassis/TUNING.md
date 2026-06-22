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
