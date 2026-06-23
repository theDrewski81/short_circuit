"""Motion loop entry point for Pi-M.

Phase 01 scope: loop structure only. Hardware init, MQTT wiring, and intent
execution are stubs that later phases (02 locomotion, 03 manipulation)
populate. The loop must never block on Pi-V or the home lab -- all stubs
below are designed to be non-blocking once implemented.
"""

from __future__ import annotations

import logging
import time

from motion.offline_fallback import OfflineFallbackStateMachine, State

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("johnny5.motion.main")

LOOP_RATE_HZ = 50  # 20ms tick -- profile sustainability on Pi Zero 2 W in Phase 02


def initialize_hardware() -> None:
    """Stub. Phase 02/03 will init H-bridge, servos, ToF, IMU, LED ring."""
    logger.info("initialize_hardware: stub (no-op in Phase 01)")


def initialize_mqtt():
    """Stub. Returns an MQTT client handle once implemented."""
    logger.info("initialize_mqtt: stub (no-op in Phase 01)")
    return None


def get_latest_intent(mqtt_client, state_machine: OfflineFallbackStateMachine):
    """Stub. Reads latest retained johnny5/intent message, if any.
    Must not block waiting for a new message -- returns None if nothing new.
    """
    return None


def execute_intent(intent) -> None:
    """Dispatch an intent to actuation.

    Phase 02 locomotion seam -- becomes active once MotorDriver lands (Task 1,
    gated on bench hardware). The pieces it wires together already exist:
    `motion.locomotion_policy.LocomotionPolicy` (ONNX runner) and the observation
    builder; only the MotorDriver output stage and the `_read_motion_state()`
    sensor read (IMU fusion + encoder odometry, see simulation/chassis/TUNING.md)
    remain. Intended flow:

        from motion.locomotion_policy import (
            LocomotionPolicy, MotionState, command_from_intent)
        # one-time in initialize_hardware():
        #   _policy = LocomotionPolicy("policies/locomotion_v3.onnx")
        #   _motor_driver = MotorDriver(...)
        if intent is not None and intent.get("action") in ("move", "turn", "arc"):
            v_cmd, w_cmd = command_from_intent(intent["action"], intent.get("params"))
            state = _read_motion_state()          # MPU-6050 fusion + encoders
            left, right = _policy.step(state, (v_cmd, w_cmd))
            _motor_driver.set_speed(left, right)  # [-1, 1] -> PWM duty + direction
            return

    Manipulation (arm_pose / head_pose) is dispatched from here in Phase 03.
    """
    if intent is not None:
        logger.debug("execute_intent: stub received intent=%s", intent)


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

        if state_machine.state == State.ONLINE:
            intent = get_latest_intent(mqtt_client, state_machine)
            execute_intent(intent)
        # OFFLINE / RECOVERING: output.stop_treads and output.hold_servos
        # signal the hardware layer to hold; Phase 02/03 wire that up.

        publish_status(mqtt_client, state_machine)

        elapsed = time.monotonic() - tick_start
        time.sleep(max(0.0, (1.0 / LOOP_RATE_HZ) - elapsed))


if __name__ == "__main__":
    main()
