"""Motion loop entry point for Pi-M.

Phase 01 built the loop skeleton and the offline fallback state machine.
Phase 02 Task 2 activates the locomotion seam that Tasks 1/3-5 left staged:
MotorDriver (Task 1, H-bridge + encoders) and LocomotionPolicy (Task 5, ONNX
runner) are wired into execute_intent(); _read_motion_state() builds the
policy's MotionState from the MPU-6050 (this task) fused with EncoderReader
odometry. Manipulation dispatch (arm_pose / head_pose) is added in Phase 03.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass

from motion.locomotion_policy import LocomotionPolicy, MotionState, command_from_intent
from motion.motor_driver import EncoderReader, MotorDriver
from motion.mpu6050 import MPU6050
from motion.offline_fallback import OfflineFallbackStateMachine, State

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("johnny5.motion.main")

LOOP_RATE_HZ = 50  # 20ms tick -- profile sustainability on Pi Zero 2 W in Phase 02

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", ".."))
POLICY_PATH = os.path.join(_REPO, "policies", "locomotion_v3.onnx")

# Sprocket pitch radius + track thickness (mechanical/freecad/params.csv:
# sprocket_pitch_dia=40mm / 2 + track_thickness=3.5mm). Same CSV source as
# simulation/chassis/params.py's wheel_radius -- if that geometry changes,
# update this alongside it (and re-check the V_MAX/W_MAX-vs-wheel-speed
# relationship the policy was trained against).
WHEEL_RADIUS_M = 0.0235

# Locomotion actions execute_intent() dispatches through the policy. "idle" is
# intentionally excluded here (matches the seam as documented/staged in Task
# 5) -- it is a valid command_from_intent() input (-> hold-still (0,0)) for
# testing/future use, but execute_intent() currently only drives the motors on
# an explicit move/turn/arc; an idle intent is a no-op for locomotion this tick.
_LOCOMOTION_ACTIONS = ("move", "turn", "arc")


@dataclass
class MotionHardware:
    """Task 1/2 hardware handles, built once by initialize_hardware().

    Held as an injectable bundle (not bare module globals) so execute_intent(),
    _read_motion_state(), and _apply_fallback_output() are unit-testable with
    fakes in the sandbox -- see tests/test_main_locomotion.py. Real hardware
    construction (gpiozero, rpi-hardware-pwm, smbus2, onnxruntime) happens
    lazily inside each component's own __init__, only when
    initialize_hardware() actually runs -- this module imports cleanly
    off-target.
    """

    motor_driver: "MotorDriver | None" = None
    policy: "LocomotionPolicy | None" = None
    imu: "MPU6050 | None" = None
    encoders: "EncoderReader | None" = None


_hw = MotionHardware()


def initialize_hardware(hw: MotionHardware | None = None) -> MotionHardware:
    """Construct MotorDriver, LocomotionPolicy, MPU6050, EncoderReader.

    MotorDriver is constructed disabled (STBY low -- its own fail-safe
    default); main()'s loop enables/disables it each tick from the offline
    fallback state via _apply_fallback_output(), it is never force-enabled
    here. Pass an explicit `hw` (pre-built with fakes) to bypass real hardware
    construction -- used by tests, not by main().
    """
    global _hw
    hw = hw or MotionHardware(
        motor_driver=MotorDriver(),
        policy=LocomotionPolicy(POLICY_PATH),
        imu=MPU6050(),
        encoders=EncoderReader(),
    )
    _hw = hw
    logger.info(
        "initialize_hardware: MotorDriver + LocomotionPolicy + MPU6050 + "
        "EncoderReader ready (disabled until ONLINE)"
    )
    return hw


def initialize_mqtt():
    """Stub. Returns an MQTT client handle once implemented."""
    logger.info("initialize_mqtt: stub (no-op in Phase 01/02)")
    return None


def get_latest_intent(mqtt_client, state_machine: OfflineFallbackStateMachine):
    """Stub. Reads latest retained johnny5/intent message, if any.
    Must not block waiting for a new message -- returns None if nothing new.
    """
    return None


def _read_motion_state(hw: MotionHardware | None = None) -> MotionState:
    """Build a MotionState from live sensors for this tick.

    Sensor -> channel map (simulation/chassis/TUNING.md "Observation
    reconstruction on Pi-M"):
      roll, pitch, yaw_rate   <- MPU-6050 accel+gyro complementary filter (motion.mpu6050)
      wheel_speed_left/right  <- EncoderReader.read(), rad/s
      forward_velocity        <- mean drive-wheel speed * WHEEL_RADIUS_M (encoder odometry)
      lateral_velocity        <- not directly measurable, held at 0.0 (documented sim-to-real gap)
    """
    hw = hw or _hw
    roll, pitch, yaw_rate = hw.imu.read()
    enc = hw.encoders.read()
    forward_velocity = 0.5 * (enc.speed_left + enc.speed_right) * WHEEL_RADIUS_M
    return MotionState(
        roll=roll,
        pitch=pitch,
        yaw_rate=yaw_rate,
        forward_velocity=forward_velocity,
        lateral_velocity=0.0,
        wheel_speed_left=enc.speed_left,
        wheel_speed_right=enc.speed_right,
    )


def execute_intent(intent, hw: MotionHardware | None = None) -> None:
    """Dispatch an intent to actuation via the trained locomotion policy.

    intent -> command_from_intent -> LocomotionPolicy.step(state, cmd) ->
    MotorDriver.set_speed. hw defaults to the module-level handles built by
    initialize_hardware(); pass an explicit MotionHardware (with fakes) to
    unit-test this without a Pi.

    Manipulation (arm_pose / head_pose) is dispatched from here in Phase 03.
    """
    hw = hw or _hw
    if intent is None:
        return
    action = intent.get("action")
    if action not in _LOCOMOTION_ACTIONS:
        logger.debug("execute_intent: no locomotion action in intent=%s", intent)
        return
    if hw.motor_driver is None or hw.policy is None or hw.imu is None or hw.encoders is None:
        logger.warning("execute_intent: hardware not initialized, dropping intent")
        return
    v_cmd, w_cmd = command_from_intent(action, intent.get("params"))
    state = _read_motion_state(hw)
    left, right = hw.policy.step(state, (v_cmd, w_cmd))
    hw.motor_driver.set_speed(left, right)


def _apply_fallback_output(output, hw: MotionHardware | None = None) -> None:
    """Coordinate MotorDriver enable state with the offline fallback machine.

    ONLINE (stop_treads=False): ensure the driver is enabled so execute_intent()
    can drive it this tick. OFFLINE/RECOVERING (stop_treads=True): disable() --
    coasts both motors, then pulls STBY low (MotorDriver.disable()'s own
    fail-safe sequence). This runs every tick, before execute_intent() is even
    considered, so a driver that's mid-motion when the link drops is stopped
    the same tick the state machine notices, not on the next intent.
    """
    hw = hw or _hw
    if hw.motor_driver is None:
        return
    if output.stop_treads:
        if hw.motor_driver.enabled:
            hw.motor_driver.disable()
    elif not hw.motor_driver.enabled:
        hw.motor_driver.enable()


def publish_status(mqtt_client, state_machine: OfflineFallbackStateMachine) -> None:
    """Stub. Will publish johnny5/status with servo positions, ToF, IMU."""
    pass


def main() -> None:
    initialize_hardware()
    mqtt_client = initialize_mqtt()
    state_machine = OfflineFallbackStateMachine()

    logger.info("Motion loop starting at %d Hz", LOOP_RATE_HZ)

    while True:
        tick_start = time.monotonic()

        output = state_machine.update()
        _apply_fallback_output(output)

        if state_machine.state == State.ONLINE:
            intent = get_latest_intent(mqtt_client, state_machine)
            execute_intent(intent)
        # OFFLINE / RECOVERING: _apply_fallback_output() above already stopped
        # treads + pulled STBY low. Holding servos is Phase 03 scope.

        publish_status(mqtt_client, state_machine)

        elapsed = time.monotonic() - tick_start
        time.sleep(max(0.0, (1.0 / LOOP_RATE_HZ) - elapsed))


if __name__ == "__main__":
    main()
