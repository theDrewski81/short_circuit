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

## Bench bringup results — Task 1 drive integration (2026-07-12)

First power-on of the TB6612 + N20 encoder motors on the bench (wheels free).
Driver, hardware PWM, STBY interlock, coast/brake, and both encoders verified
with `scripts/test_motors.py`. Two per-side corrections, both fixed **in
hardware**, so `MotorDriver`/`EncoderReader` stay at `invert_*=False`:

- **Left motor ran backwards** → swapped its output leads to RED→**AO2**,
  BLK→**AO1** (was RED→AO1/BLK→AO2). This is the "Motor asymmetry" gap above,
  resolved by a lead swap rather than a per-side gain.
- **Right encoder counted backwards on forward** → swapped that motor's encoder
  channels to **YEL→GPIO23, WHT→GPIO22** (A/B were reversed). Left encoder was
  already correct.

Side assignment **locked: LEFT = channel A, RIGHT = channel B.**
Post-fix run: forward → both encoders positive (L +984 / R +980, within ~0.4%),
backward → both negative, CCW → L−/R+, CW → L+/R−. Motors track closely.

- **Encoder counts/output-rev recalibrated (affects the wheel-speed obs
  channels, Task 6).** Measured counts run ~4x below the `1807` (raw 4x-quadrature)
  figure because `gpiozero.RotaryEncoder` decodes full-step (1x): effective
  ~**452 counts/output-rev** (3 cycles/motor-rev × 150.58). `COUNTS_PER_OUTPUT_REV`
  updated 1807 → 451.74 provisionally; confirm empirically with
  `scripts/test_motors.py --calibrate` and set the exact value. If counts are also
  *missed* at speed (callback latency on the single-core Pi Zero 2 W), the
  low-speed calibration won't reveal it — watch obs-vs-commanded speed in Task 6.

## Encoder calibration — Task 6a (2026-08-10)

**Result: 450.6 counts/output-rev measured, left/right spread 0.4%.
`COUNTS_PER_OUTPUT_REV` stays at 451.74.**

The measurement confirms the derived constant rather than replacing it. 451.74
is fixed by integer quantities (3 quadrature cycles/motor-rev × 150.58 gearbox,
both from tooth and pole counts), whereas the measured figure carries
tap-timing noise; the 0.25% gap between them is that noise, not a physical
difference, so adopting 450.6 would trade an exactly-derived value for a
noisier estimate of the same thing. What the measurement does settle is the
question it was designed for: `gpiozero.RotaryEncoder` decodes **1x, not 4x**,
killing the ~1807 candidate. That alternative would have been a factor-of-four
error in both wheel-speed obs channels and in all odometry.

**Method changed — the hand-rotation procedure originally specified for Task 6a
is impossible.** The 150.58:1 N20 gearbox is not backdrivable at the output
shaft: the wheel does not turn by hand, and the force required would split the
gearcase before the shaft moved usefully. This was confirmed mechanical rather
than electrical by detaching the motor from the TB6612 completely and finding
it still locked, ruling out the short-brake state (IN1=H, IN2=H) that floating
pins can leave behind once `MotorDriver.close()` releases them. Note that
`--calibrate` therefore now **runs the motors** — wheels must be free and the
robot off the treads before invoking it.

The replacement is a powered measurement: one wheel at a time at low duty
(`--calib-duty`, default 0.25), tapping Enter at each pass of a mark on the
wheel, with the script least-squares-fitting encoder count against revolution
index over `--revs` passes. The slope is counts/output-rev. Fitting the slope
rather than dividing total counts by revolutions is what makes this usable by
hand: a constant human reaction lag displaces the intercept and leaves the
slope unchanged, so the result depends on the taps being consistent, not fast.

**Carried forward:** this was measured at ~0.25 duty, so the missed-count risk
noted in the Task 1 entry above is still open. Low-speed calibration cannot
reveal counts dropped at speed through callback latency on the single-core Pi
Zero 2 W. Compare observed against commanded wheel speed during Task 6b, where
the robot runs at real drive speeds for the first time.
