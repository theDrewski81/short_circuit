# Drive Electronics Bringup — TB6612FNG + N20 Encoder Motors (Pi-M)

Reference for Phase 02 Task 1 (`MotorDriver`) wiring and bench bringup. Pairs with
the `BOM.md` GPIO pin map and power budget. Goal: bring up the two drive motors on
the bench (wheels free, **not** on the chassis/treads) with correct direction,
speed, braking, encoder feedback, and a fail-safe standby interlock.

## Hardware

| Part | Detail |
|---|---|
| Drive motor ×2 | Pololu #5219 — 150:1 Micro Metal Gearmotor HPCB 12V, 12 CPR encoder, side connector |
| Driver | Pololu #713 — TB6612FNG dual H-bridge carrier (VM 4.5–13.5 V, VCC 2.7–5.5 V, 1 A cont. / 3 A peak per ch) |
| Motor rail (VM) | Battery-direct 2S LiPo, ~7.4 V nom (8.4 V full) — within TB6612 range; 1000 µF across VM |
| Logic rail (VCC) | 3.3 V from Pi-M (so all logic + encoder outputs are 3.3 V, GPIO-safe) |
| Encoder | 12 CPR on the motor shaft × 150.58 gearbox ≈ **1807 counts / output rev** (quadrature) |

## Wiring — Pi-M (BCM) ↔ TB6612FNG ↔ motors

| TB6612 pin | Pi-M GPIO | Notes |
|---|---|---|
| PWMA | GPIO 12 | hardware PWM0 — motor A (left) speed |
| AIN1 | GPIO 5 | motor A direction |
| AIN2 | GPIO 6 | motor A direction |
| PWMB | GPIO 13 | hardware PWM1 — motor B (right) speed |
| BIN1 | GPIO 16 | motor B direction |
| BIN2 | GPIO 26 | motor B direction |
| STBY | GPIO 20 | **pulled LOW on boot → motors OFF**; drive HIGH to enable |
| VCC | 3.3 V | logic |
| VM | battery + (after fuse/switch) | motor supply, ~7.4 V |
| GND | common | star ground: Pi ↔ TB6612 ↔ battery |
| AO1/AO2 | motor A leads | swap if A runs backwards |
| BO1/BO2 | motor B leads | swap if B runs backwards |

| Encoder | Pi-M GPIO | Notes |
|---|---|---|
| M1 A / B | GPIO 17 / 27 | left motor quadrature |
| M2 A / B | GPIO 22 / 23 | right motor quadrature |
| Encoder VCC / GND | 3.3 V / common | keeps A/B outputs at 3.3 V |

## TB6612FNG control contract (per channel; STBY must be HIGH to run)

| IN1 | IN2 | PWM | Result |
|---|---|---|---|
| H | L | duty | **CW / forward** (speed ∝ duty) |
| L | H | duty | **CCW / reverse** (speed ∝ duty) |
| H | H | x | **short brake** (terminals shorted) |
| L | L | x | **stop / coast** (outputs high-Z) |
| x | x | x (STBY=L) | **standby — all outputs off** |

Note: with a direction set, **PWM=0 is a short brake, not a coast**. True coast is
`IN1=L, IN2=L`. This drives the API:

- `set_speed(left, right)` — sign → direction pins, `abs()` → PWM duty (0–1 → 0–100 %).
  `0.0` → coast (`IN1=L, IN2=L`).
- `stop()` — coast both (`IN1=L, IN2=L`), PWM 0.
- `brake()` — short brake both (`IN1=H, IN2=H`); faster stop than coast.
- Enable/disable — STBY HIGH to run; pull LOW on shutdown / offline fallback.

"Forward" = robot drives forward. Confirm each motor's direction on the bench and
record any per-side lead/pin swap (this is the sim's "motor asymmetry" item — log it
in `simulation/chassis/TUNING.md`).

## PWM

Use **hardware PWM** on GPIO 12/13 (PWM0/PWM1) — software PWM jitters and wastes CPU
on the loop. `gpiozero` with the `lgpio` pin factory (installed by
`scripts/setup_motion_pi.sh`) or `pigpio` both give stable hardware PWM. Frequency
~**20 kHz** (above audible, well under the TB6612 100 kHz max).

## Encoders

12 CPR × 150.58:1 ≈ 1807 counts/output-rev. Decode quadrature with interrupt/callback
counting (`gpiozero.RotaryEncoder` or `pigpio` edge callbacks) — never poll in the
loop. `EncoderReader` publishes signed left/right tick counts to the motion loop;
the sign must match motor "forward". Used in Phase 02 for closed-loop checks and in
Phase 05 for odometry. (Forward velocity for the policy obs is derived from these —
see `TUNING.md`.)

## Bench bringup procedure (`scripts/test_motors.py`)

Motors on the bench, **wheels free, robot not on treads, nothing in the pinch path.**

1. Power logic only (Pi 3.3 V), VM off → confirm STBY reads LOW and outputs are dead.
2. Power VM (fused, 7.4 V). Run the timed sequence: forward 2 s → stop 0.5 s →
   backward 2 s → stop 0.5 s → turn left 1 s → turn right 1 s.
3. Verify per motor: correct direction each phase, speed scales with duty, encoder
   counts increment with the correct sign, coast vs brake behave differently.
4. Verify the STBY interlock: with STBY LOW, `set_speed` does nothing.
5. Sanity-check current: ~0.4 A/motor running, ~2 A stall (BOM); watch for hot driver.

## Safety

- Inline fuse (7.5 A, BOM) on VM; master switch after fuse.
- TB6612 has reverse-protection on **VM only**, not VCC — double-check VCC polarity.
- STBY LOW on boot/crash is the primary fail-safe; `MotorDriver` and the offline
  fallback must both drive treads to stop (coast or brake) and can pull STBY LOW.
- Keep fingers clear of sprockets/treads; bench-test before chassis assembly.

## Task 1 success criteria

`set_speed` / `stop` / `brake` produce correct directions on both motors; PWM duty
scales speed; encoders count with correct sign; STBY interlock holds motors off until
enabled; `scripts/test_motors.py` runs the sequence cleanly on the bench.
