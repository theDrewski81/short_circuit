# Johnny 5 — Tread Chassis Simulation (Phase 02)

Chassis-only MuJoCo environment for training the locomotion policy. Arms and
head are out of scope here (added in Phase 03); their mass rides on the chassis
as a lumped trunk inertia.

## Files

| File | Role |
|---|---|
| `params.py` | SI-unit parameter bridge. Reads `mechanical/freecad/params.csv` (CAD source of truth) and declares the non-CAD modelling constants (motor torque, friction, mass split, CoM height) with their basis. |
| `build_mjcf.py` | Generates `johnny5_chassis.xml` from `params.py`. Re-run after any params change. |
| `johnny5_chassis.xml` | Generated MJCF. **Do not hand-edit** — change `params.py`/`params.csv` and regenerate. |
| `env.py` | Gymnasium environment `JohnnyChassisEnv` (command-conditioned). |
| `test_env.py` | Pre-training stability + sanity checks (random + scripted rollouts). |
| `TUNING.md` | Sim-vs-reality assumptions to confirm on the bench (Phase 02 Task 6). |

Regenerate the model:

```bash
python3 simulation/chassis/build_mjcf.py
```

## Modelling assumptions

**Treads → four driven wheels.** Each tread is two cylinders (front + rear,
spanning the 120 mm wheelbase) rather than a deformable belt. Deformable track
contact is expensive and numerically fragile, and the policy only needs the
left/right-speed → body-motion mapping. A *single* wheel per side collapses the
fore-aft contact patch to a point, and the tall robot nose-dives; front + rear
wheels restore the support polygon. The real belt couples the front idler to the
rear sprocket, so both turn at track speed — hence all four wheels are driven, in
left/right pairs (the env writes one command to each side's two wheels).

**DC motor → torque actuator + damping droop.** Each wheel is a torque source
(`gear` = stall torque / 2) with joint damping `b = stall / (2·no_load)`. The
factor of two splits one physical motor's torque-speed line across its two
wheels, so the per-side behaviour matches one brushed motor: full command settles
the side near its no-load speed (~0.30 m/s) instead of accelerating without
bound. Stall 0.25 N·m and no-load 12.9 rad/s are datasheet figures scaled from
12 V to the 7.4 V battery-direct rail — **confirm on the bench** (TUNING.md).

**Skid-steer turn resistance is real, not a bug.** Contacts use `condim=3`
(slide friction only). Turning comes from lateral skid of four wheels spread over
the wheelbase, so in-place yaw is resistance-limited. Measured envelope on the
default floor: forward cap ~0.30 m/s, in-place yaw cap ~0.34 rad/s. The env
command ranges (`V_MAX=0.28`, `W_MAX=0.30`) sit just inside these.

**Rear caster → rigid low-friction sphere.** The physical part is a sprung,
swivelling trailing caster; for locomotion it is a rigid low-friction support
sphere placed half the nominal trail behind the rear track edge, giving the same
rearward tip support without joint-tuning fragility.

**Trunk inertia → solid-box proxy.** Mass 1.197 kg at CoM height 0.110 m, with a
box inertia using the tub footprint and an effective height of 0.18 m to account
for the torso/head/arm mass riding above the (collision-only) tub.

## Environment

`JohnnyChassisEnv` — command-conditioned, one policy for all behaviours.

- **Control rate:** 50 Hz (matches the Pi-M motion-loop tick); 10 physics
  substeps per control step at 500 Hz.
- **Action:** `[left, right]` motor effort in `[-1, 1]`, each applied to that
  side's two wheels.
- **Observation (9):** body-frame forward/lateral velocity, yaw rate, roll,
  pitch, left/right encoder velocity, and the command `[v_cmd, w_cmd]`.
- **Command modes:** forward, backward, spin-left, spin-right, arc, stop —
  sampled per episode to cover the four Phase 02 behaviours plus hold.
- **Reward:** `w_vel·exp(-k·(v−v_cmd)²) + w_yaw·exp(-k·(ψ̇−w_cmd)²)
  − energy − stability(roll²+pitch²) − lateral-skid`. Tip-over
  (|roll| or |pitch| > 0.8 rad) terminates with a penalty. Weights are
  constructor kwargs, set from `config.yaml` in training (Task 4).

## Pre-training check

```bash
python3 simulation/chassis/test_env.py
```

Confirms physics stability (no NaN/inf, no spurious tip-overs under random
actions) and that a scripted differential controller out-scores random control —
i.e. the reward is trackable — before committing GPU time to training.
