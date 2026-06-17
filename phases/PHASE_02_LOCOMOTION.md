# Phase 02 — Locomotion

## Objective

Implement tread locomotion on Pi-M: hardware driver integration, basic commanded motion, MuJoCo simulation environment for the tread chassis, locomotion policy training, and deployment of a trained policy to the Pi. At the gate, the physical robot drives forward, backward, and turns on command via a trained policy receiving intent from the motion loop.

---

## Gate Condition

**The robot drives forward, backward, and executes left and right turns on command. Motion is governed by a trained policy deployed from the simulation environment, not hand-coded PWM values. The offline fallback (Phase 01) continues to function correctly when the tread control stack is active.**

---

## Context

Infrastructure (Phase 01) is complete. Both Pis are communicating, the LiteLLM client is operational, and the offline fallback state machine is running in the motion loop skeleton. The motion loop tick rate is established.

The selected motors, H-bridge driver, and tread system are known from Phase 00. Reference those BOM selections throughout this phase -- do not assume specific components here.

The GrowBot reference uses Feetech SCS0009 serial bus servos for locomotion (bipedal). Johnny 5 uses DC motors + H-bridge for treads, which is a fundamentally different actuation model. The GrowBot training approach (small motor policies from offline rollouts, deployed as compact models) is directly applicable; the simulation model is different.

---

## Tasks

### 1. H-Bridge Driver Integration

Implement the motor driver interface on Pi-M in `src/motion/motor_driver.py`.

The driver must expose a clean interface regardless of which H-bridge was selected in Phase 00:
```python
class MotorDriver:
    def set_speed(self, left: float, right: float) -> None:
        """
        left, right: -1.0 (full reverse) to +1.0 (full forward), 0.0 = stop
        """
    def stop(self) -> None:
        """Hard stop both motors."""
    def brake(self) -> None:
        """Active brake (shorts motor terminals, faster stop than coast)."""
```

Internal implementation maps the normalized speed values to PWM duty cycle on the appropriate GPIO pins. Use the `RPi.GPIO` library or `gpiozero` -- note which is used in comments.

If encoders are present (see Phase 00 BOM decision): implement a separate `EncoderReader` class that publishes left/right tick counts to the motion loop. Encoder feedback is used in Phase 02 for closed-loop speed control and in Phase 05 for odometry.

Test harness: `scripts/test_motors.py` -- a standalone script that runs a timed sequence (forward 2s, stop 0.5s, backward 2s, stop 0.5s, turn left 1s, turn right 1s) and confirms motor response. Run this test on the bench before connecting treads to the chassis.

### 2. Basic Commanded Motion

Integrate `MotorDriver` into the motion loop in `src/motion/main.py`.

Extend `execute_intent()` to parse locomotion commands from the intent message and call `MotorDriver.set_speed()`. The intent message schema (from Phase 01 `PROTOCOL.md`) must include a locomotion field -- update the schema document if it does not.

Initial locomotion intent format:
```json
{
  "locomotion": {
    "left": 0.5,
    "right": 0.5
  }
}
```

This direct speed control is the baseline. The trained policy (Task 4) will replace this with higher-level commands (e.g., `"move_forward"`, `"turn_left_30"`) that the policy translates to speed outputs.

### 3. MuJoCo Simulation Environment

Build the Johnny 5 tread chassis simulation in `simulation/chassis/`.

The MuJoCo MJCF model must reflect the actual physical dimensions from Phase 00 (use the FreeCAD measurements). Key elements:
- Tread chassis body with correct mass distribution and moment of inertia
- Two drive wheels (or track contact geometry)
- Ground plane with appropriate friction coefficients for the expected floor surface (hardwood/tile by default)
- Actuators representing the left and right motors with torque limits matching the selected motors

Do not model the arms or head in this phase. The simulation is chassis-only. Arm and head MJCF models are added in Phase 03.

Environment wrapper in `simulation/chassis/env.py`: a Gymnasium-compatible environment that wraps the MuJoCo model. Observations: motor velocities, chassis orientation (from IMU equivalent), optional encoder ticks. Actions: left and right motor torque targets in [-1, 1].

Reward shaping for locomotion:
- Forward velocity reward (primary): encourages moving in the commanded direction
- Heading stability reward: penalizes excessive yaw when driving straight
- Energy penalty: small coefficient against high motor torques (encourages efficient gait)
- Stability penalty: penalizes excessive roll or pitch

Test the simulation environment with a random policy before training to confirm physics stability.

### 4. Locomotion Policy Training

Train on the home lab (RTX 3080 or Proxmox cluster). The Pi Zero 2 W does not run training.

Algorithm recommendation: **PPO (Proximal Policy Optimization)** via Stable-Baselines3 or CleanRL. PPO is well-suited to continuous control, robust to hyperparameter variation, and produces compact policies. Use a small MLP architecture (2–3 hidden layers, 64–128 units) to keep the deployed model fast on the Pi.

Training scripts in `simulation/chassis/train.py`. Training configuration in `simulation/chassis/config.yaml` (learning rate, batch size, total timesteps, evaluation interval).

Train for at least the following behaviors:
- Drive straight forward at commanded speed
- Drive straight backward at commanded speed
- Turn in place (left and right)
- Arc turn (combined forward + turn)

Each behavior can be a separate training run with a behavior-specific reward, or trained jointly with a command-conditioning approach. Command-conditioned policy is preferred for generalization: the policy receives the desired command as part of its observation and learns to execute all behaviors from a single model.

Export the trained policy to ONNX: `policies/locomotion_v1.onnx`.

### 5. Policy Deployment to Pi-M

Implement the policy inference runner on Pi-M in `src/motion/locomotion_policy.py`.

```python
class LocomotionPolicy:
    def __init__(self, model_path: str):
        # Load ONNX model with onnxruntime
        ...

    def step(self, observation: dict) -> tuple[float, float]:
        """
        Returns (left_speed, right_speed) in [-1, 1].
        observation: current IMU state, command, optional encoder ticks
        """
```

Use `onnxruntime` (install on Pi via pip). Verify inference latency on the Pi Zero 2 W -- target under 5ms per step to fit within the 20ms motion loop tick at 50Hz. If latency is too high, reduce model size or lower the tick rate.

The policy runner replaces direct speed commands in `execute_intent()`: high-level intent (direction, speed magnitude) goes in, motor speeds come out.

Validation test: `scripts/test_locomotion_policy.py` -- load the policy, run 100 inference steps with dummy observations, report mean latency and output range.

### 6. Physical Integration Test

With the trained policy deployed and the chassis assembled:

1. Place robot on a flat surface with clear space in all directions.
2. Connect to Pi-M via SSH.
3. Send test intents manually via MQTT publish from the home lab.
4. Verify: forward motion is straight, backward motion is straight, turns execute in the correct direction, stop command results in immediate halt.
5. Verify offline fallback: disconnect the home lab WiFi, confirm robot stops and LED ring changes state, reconnect, confirm recovery.

Document any physical tuning required (friction coefficients in simulation don't match reality, motor asymmetry, etc.) in `simulation/chassis/TUNING.md`.

---

## Known Constraints

The Pi Zero 2 W has a single-core thermal ceiling under sustained load. If the motion loop plus policy inference heats the chip, add a heatsink. Monitor CPU temperature during the physical integration test with `vcgencmd measure_temp`.

ONNX Runtime ARM builds may require compilation from source or a specific wheel for the Pi Zero architecture (ARMv8 / aarch64). Confirm this during Task 5 and document the installation path in `scripts/setup_motion_pi.sh`.

---

## Recommended Session Start

Confirm which H-bridge driver and motor type were selected in Phase 00. Pull up the BOM.md. Open `src/motion/motor_driver.py` and begin with the hardware interface, then move to simulation.
