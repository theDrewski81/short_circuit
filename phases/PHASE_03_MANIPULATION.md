# Phase 03 — Manipulation

## Objective

Integrate the Feetech serial bus servos for both shoulder joints and the head rotation axis. Implement position and load telemetry. Extend the MuJoCo simulation to include arms and head. Train and deploy arm and head motion policies. At the gate, all three servos respond correctly to commanded positions with position and load feedback flowing into the motion loop.

---

## Gate Condition

**Left shoulder, right shoulder, and head rotation servos respond to commanded positions. Position and load feedback from each servo is reading correctly in the motion loop. Basic expressive arm and head behaviors (at minimum: home position, wave, attention/tracking) execute on command.**

---

## Context

Locomotion (Phase 02) is complete. The robot drives and turns via trained policy. The motion loop is running at target tick rate on Pi-M.

The Feetech SCS0009 (or selected equivalent) is a half-duplex UART serial bus servo. All servos share one data bus on a single UART port on Pi-M (`/dev/serial0`, same port used in GrowBot). The serial protocol is proprietary Feetech/SCServo; a Python library exists (`pip install SCServo`). Key implementation notes from GrowBot: the SCS0009 uses big-endian byte order for 2-byte reads/writes; assign unique IDs to each servo before installation (all ship as ID 1); the half-duplex line requires a 1kΩ resistor between TX (GPIO14) and the data bus.

This phase expands the simulation model established in Phase 02 but does not replace it. The locomotion policy continues to run in the motion loop alongside the new servo control stack.

Future expansion: elbow servos are in scope for a later iteration. The servo bus and ID scheme must accommodate at least 2 additional servos (IDs 4 and 5) without rework.

---

## Tasks

### 1. Servo ID Assignment

Before any software work, physically assign unique IDs to the three servos. This requires connecting one servo at a time to the bus and writing its ID register.

ID assignment:
- Servo 1: Left shoulder
- Servo 2: Right shoulder  
- Servo 3: Head rotation
- (Reserved for future) Servo 4: Left elbow, Servo 5: Right elbow

Use the Feetech SCServo Python library or the setup utility from GrowBot's `setup/` directory to write IDs. Confirm each ID reads back correctly before moving to the next servo. Document the pinout of the SCS0009 connector (GND / VCC / DATA order) -- GrowBot notes this can be surprising.

### 2. Serial Bus Driver

Implement the servo interface in `src/motion/servo_driver.py`.

```python
class ServoDriver:
    def __init__(self, port: str = '/dev/serial0', baudrate: int = 1_000_000):
        ...

    def set_position(self, servo_id: int, position: int, speed: int = 500) -> None:
        """
        position: 0–4095 (SCS0009 is 4096-step, ~0.088° per step)
        speed: step/sec, lower = slower/gentler
        """

    def get_state(self, servo_id: int) -> dict:
        """
        Returns: {'position': int, 'speed': int, 'load': int, 'temperature': int}
        """

    def set_torque_limit(self, servo_id: int, limit: int) -> None:
        """limit: 0–1000 (1000 = 100%)"""

    def stop(self, servo_id: int) -> None:
        """Disable torque on the servo (hold position via friction)."""
```

Set torque limits on all servos to 70% maximum on initialization, consistent with GrowBot's recommendation to stay within the power budget.

Define position constants for each servo's home position, minimum, and maximum travel in `src/shared/servo_constants.py`. These constants are used by both the servo driver and the policy runner.

### 3. Servo Telemetry in Motion Loop

Extend the motion loop to poll servo state at each tick and include it in the status message published to `johnny5/status`. Poll all three servos per tick; at 50Hz this is 150 reads/sec on the serial bus. Confirm this is within the 1Mbps bus bandwidth (it is, with margin) and does not cause loop jitter.

Add load monitoring: if any servo reports load > 85% for more than 10 consecutive ticks, log a warning and optionally command the servo to back off. This prevents stall-induced heat buildup.

### 4. MuJoCo Simulation Extension

Extend the chassis simulation from Phase 02 to include arms and head in `simulation/full_body/`.

The full-body MJCF model adds:
- Left and right arm assemblies: upper arm body, shoulder joint (revolute, 1 DOF each in V1)
- Head assembly: head body, neck joint (revolute, 1 DOF, yaw axis)
- Approximate mass and inertia values for printed PLA parts (estimate from FreeCAD, ~1.2 g/cm³ for PLA)
- Joint limits matching the physical servo range and chassis clearance

The arm and head joints are actuated by position targets (position servo model), not torque, matching how the physical Feetech servos are commanded.

The locomotion policy from Phase 02 continues to run on the base body in the simulation. Arm and head policies are layered on top. Confirm the full-body model remains physically stable with the locomotion policy active.

### 5. Arm and Head Behavior Policies

Define at least three arm behaviors and one head behavior for Phase 03. These are the foundation for the expressiveness layer in Phase 04.

**Arm behaviors:**

- `HOME`: both arms at a natural resting position at the robot's sides
- `WAVE`: right arm raises to shoulder height and rotates in a waving motion (looped)
- `REACH`: both arms extend forward (as if reaching toward something)

**Head behavior:**

- `SCAN`: head slowly rotates left and right, covering the full range of motion, on a timed cycle

These behaviors can be implemented as:
1. Trained policies from simulation (preferred for natural motion)
2. Scripted keyframe sequences (faster to implement, less natural)

For Phase 03, scripted keyframe sequences are acceptable for arm and head behaviors. Phase 04 and Phase 05 can upgrade to trained policies as complexity warrants. Keyframe sequences go in `src/motion/behaviors/` as separate Python modules.

Behavior invocation is via the intent message. Extend the intent schema in `PROTOCOL.md`:
```json
{
  "locomotion": { ... },
  "arm_behavior": "WAVE",
  "head_behavior": "SCAN"
}
```

Behaviors run concurrently with locomotion. The motion loop executes all active behaviors at each tick.

### 6. Physical Validation

With servos installed in the chassis:

1. Verify all three servos move to home position on startup without collisions.
2. Send each behavior via MQTT from the home lab and confirm execution.
3. Confirm load telemetry reads correctly (manually resist a servo and watch load values climb).
4. Confirm temperature monitoring reads correctly.
5. Stress test: run WAVE behavior continuously for 5 minutes and confirm no thermal or load warnings.
6. Verify offline fallback still functions: disconnect home lab, confirm servos hold position (do not go limp), LED ring indicates offline state.

---

## Known Constraints

The SCS0009 UART bus and the Pi-M UART used for serial0 must not conflict with other uses. Confirm `dtoverlay=disable-bt` is active (set in Phase 01) and that no other process opens `/dev/serial0` during operation.

Arm range of motion in the printed chassis must clear the tread assembly in all positions. Validate this in FreeCAD before printing arm parts. If collisions exist, update the position constants in `servo_constants.py` to enforce safe limits in software as well.

---

## Recommended Session Start

Pull up `BOM.md` to confirm the specific servo model. Then open GrowBot's `setup/` directory for reference on servo ID assignment and bus wiring. Begin with Task 1 (physical ID assignment) since it blocks all software work.
