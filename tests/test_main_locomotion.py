"""Sandbox unit tests for the Phase 02 Task 2 execute_intent()/_read_motion_state()
seam and offline-fallback coordination in src/motion/main.py.

No Pi required: MotorDriver/LocomotionPolicy/MPU6050/EncoderReader are swapped
for lightweight fakes via the injectable MotionHardware bundle, so these assert
the wiring logic (dispatch, observation assembly, enable/disable coordination)
that scripts/test_motors.py + the Task 6 physical integration test then confirm
against real silicon. Runnable either way:

    python3 -m pytest tests/test_main_locomotion.py
    python3 tests/test_main_locomotion.py            # no pytest needed
"""

import math
import os
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from motion.main import (  # noqa: E402
    MotionHardware, WHEEL_RADIUS_M, _apply_fallback_output, _read_motion_state,
    execute_intent,
)
from motion.offline_fallback import FallbackOutput  # noqa: E402


# --------------------------------------------------------------------------- #
# Fakes                                                                       #
# --------------------------------------------------------------------------- #
class FakeMotorDriver:
    def __init__(self):
        self.enabled = False
        self.enable_calls = 0
        self.disable_calls = 0
        self.speeds = []

    def enable(self):
        self.enabled = True
        self.enable_calls += 1

    def disable(self):
        self.enabled = False
        self.disable_calls += 1

    def set_speed(self, left, right):
        self.speeds.append((left, right))


class FakePolicy:
    def __init__(self, ret=(0.4, 0.6)):
        self.ret = ret
        self.calls = []

    def step(self, state, command):
        self.calls.append((state, command))
        return self.ret


class FakeImu:
    def __init__(self, roll=0.0, pitch=0.0, yaw_rate=0.0):
        self.roll, self.pitch, self.yaw_rate = roll, pitch, yaw_rate
        self.read_calls = 0

    def read(self):
        self.read_calls += 1
        return self.roll, self.pitch, self.yaw_rate


@dataclass
class FakeEncSample:
    speed_left: float
    speed_right: float


class FakeEncoders:
    def __init__(self, speed_left=0.0, speed_right=0.0):
        self._sample = FakeEncSample(speed_left, speed_right)

    def read(self):
        return self._sample


def _mk_hw(**kw):
    return MotionHardware(
        motor_driver=kw.get("motor_driver", FakeMotorDriver()),
        policy=kw.get("policy", FakePolicy()),
        imu=kw.get("imu", FakeImu()),
        encoders=kw.get("encoders", FakeEncoders()),
    )


# --------------------------------------------------------------------------- #
# _read_motion_state                                                          #
# --------------------------------------------------------------------------- #
def test_read_motion_state_maps_imu_and_encoders():
    hw = _mk_hw(
        imu=FakeImu(roll=0.1, pitch=-0.2, yaw_rate=0.3),
        encoders=FakeEncoders(speed_left=4.0, speed_right=6.0),
    )
    state = _read_motion_state(hw)
    assert math.isclose(state.roll, 0.1)
    assert math.isclose(state.pitch, -0.2)
    assert math.isclose(state.yaw_rate, 0.3)
    assert math.isclose(state.wheel_speed_left, 4.0)
    assert math.isclose(state.wheel_speed_right, 6.0)
    assert math.isclose(state.lateral_velocity, 0.0)


def test_read_motion_state_forward_velocity_is_mean_wheel_speed_times_radius():
    hw = _mk_hw(encoders=FakeEncoders(speed_left=10.0, speed_right=10.0))
    state = _read_motion_state(hw)
    assert math.isclose(state.forward_velocity, 10.0 * WHEEL_RADIUS_M)


def test_read_motion_state_averages_asymmetric_wheel_speeds():
    hw = _mk_hw(encoders=FakeEncoders(speed_left=8.0, speed_right=12.0))
    state = _read_motion_state(hw)
    assert math.isclose(state.forward_velocity, 10.0 * WHEEL_RADIUS_M)


# --------------------------------------------------------------------------- #
# execute_intent                                                              #
# --------------------------------------------------------------------------- #
def test_execute_intent_move_drives_policy_output_to_motors():
    hw = _mk_hw(policy=FakePolicy(ret=(0.4, 0.6)))
    execute_intent({"action": "move", "params": {"speed": 1.0}}, hw)
    assert hw.motor_driver.speeds == [(0.4, 0.6)]
    assert len(hw.policy.calls) == 1
    _, command = hw.policy.calls[0]
    assert command[0] > 0.0 and command[1] == 0.0  # move -> v only


def test_execute_intent_turn_passes_rate_as_w_only():
    hw = _mk_hw()
    execute_intent({"action": "turn", "params": {"rate": 1.0}}, hw)
    _, command = hw.policy.calls[0]
    assert command[0] == 0.0 and command[1] > 0.0


def test_execute_intent_arc_passes_both():
    hw = _mk_hw()
    execute_intent({"action": "arc", "params": {"speed": 0.5, "rate": -0.5}}, hw)
    _, command = hw.policy.calls[0]
    assert command[0] > 0.0 and command[1] < 0.0


def test_execute_intent_idle_does_not_touch_policy_or_motors():
    hw = _mk_hw()
    execute_intent({"action": "idle", "params": {}}, hw)
    assert hw.policy.calls == []
    assert hw.motor_driver.speeds == []


def test_execute_intent_unknown_action_is_noop():
    hw = _mk_hw()
    execute_intent({"action": "speak", "params": {"text": "hi"}}, hw)
    assert hw.policy.calls == []
    assert hw.motor_driver.speeds == []


def test_execute_intent_none_is_noop():
    hw = _mk_hw()
    execute_intent(None, hw)  # must not raise
    assert hw.policy.calls == []


def test_execute_intent_reads_fresh_motion_state_each_call():
    hw = _mk_hw()
    execute_intent({"action": "move", "params": {"speed": 1.0}}, hw)
    assert hw.imu.read_calls == 1


def test_execute_intent_drops_intent_when_hardware_missing():
    hw = MotionHardware()  # everything None -- pre-initialize_hardware() state
    execute_intent({"action": "move", "params": {"speed": 1.0}}, hw)  # must not raise


# --------------------------------------------------------------------------- #
# _apply_fallback_output                                                      #
# --------------------------------------------------------------------------- #
_ONLINE_OUT = FallbackOutput(stop_treads=False, hold_servos=False, led_pattern="normal")
_OFFLINE_OUT = FallbackOutput(stop_treads=True, hold_servos=True, led_pattern="offline_amber_pulse")


def test_online_enables_disabled_driver():
    hw = _mk_hw()
    assert hw.motor_driver.enabled is False
    _apply_fallback_output(_ONLINE_OUT, hw)
    assert hw.motor_driver.enabled is True
    assert hw.motor_driver.enable_calls == 1


def test_online_is_idempotent_when_already_enabled():
    hw = _mk_hw()
    hw.motor_driver.enable()
    _apply_fallback_output(_ONLINE_OUT, hw)
    assert hw.motor_driver.enable_calls == 1  # not called again


def test_offline_disables_enabled_driver():
    hw = _mk_hw()
    hw.motor_driver.enable()
    _apply_fallback_output(_OFFLINE_OUT, hw)
    assert hw.motor_driver.enabled is False
    assert hw.motor_driver.disable_calls == 1


def test_offline_is_idempotent_when_already_disabled():
    hw = _mk_hw()
    hw.motor_driver.enable()
    _apply_fallback_output(_OFFLINE_OUT, hw)
    assert hw.motor_driver.disable_calls == 1
    _apply_fallback_output(_OFFLINE_OUT, hw)
    assert hw.motor_driver.disable_calls == 1  # not called again


def test_apply_fallback_output_noop_without_driver():
    hw = MotionHardware()
    _apply_fallback_output(_OFFLINE_OUT, hw)  # must not raise


# --------------------------------------------------------------------------- #
# Loop-level coordination: mirrors main()'s per-tick sequence                 #
# --------------------------------------------------------------------------- #
def test_online_to_offline_transition_stops_treads_before_next_intent():
    """Simulates two ticks: ONLINE with a move intent, then OFFLINE. Confirms
    the driver is disabled the same tick fallback engages, independent of
    whatever execute_intent() would have computed (it isn't even called while
    non-ONLINE, matching main()'s `if state_machine.state == State.ONLINE`)."""
    hw = _mk_hw()

    _apply_fallback_output(_ONLINE_OUT, hw)
    execute_intent({"action": "move", "params": {"speed": 1.0}}, hw)
    assert hw.motor_driver.enabled is True
    assert hw.motor_driver.speeds == [(0.4, 0.6)]

    _apply_fallback_output(_OFFLINE_OUT, hw)
    # main() does not call execute_intent() while non-ONLINE -- simulated here
    # by simply not calling it again.
    assert hw.motor_driver.enabled is False
    assert hw.motor_driver.disable_calls == 1


def _run_all():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
