"""Sandbox unit tests for the TB6612FNG control contract (Phase 02, Task 1).

No Pi required: MotorDriver is driven through a recording fake backend, so these
assert the direction-pin / PWM-duty / STBY-interlock logic that the bench test
(scripts/test_motors.py) then confirms against real silicon. Runnable either way:

    python3 -m pytest tests/test_motor_driver.py
    python3 tests/test_motor_driver.py            # no pytest needed
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from motion.motor_driver import (  # noqa: E402
    MotorDriver, LEFT_PINS, RIGHT_PINS, STBY_PIN,
    counts_to_rad_s, COUNTS_PER_OUTPUT_REV,
)


class FakeDigital:
    def __init__(self, high=False):
        self.high = high
        self.closed = False

    def set(self, high):
        self.high = bool(high)

    def close(self):
        self.closed = True


class FakePwm:
    def __init__(self):
        self.duty_pct = 0.0
        self.closed = False

    def duty(self, percent):
        self.duty_pct = float(percent)

    def close(self):
        self.closed = True


class FakeBackend:
    """Records every pin/PWM the driver creates, keyed by BCM / channel."""

    def __init__(self):
        self.digitals = {}
        self.pwms = {}

    def digital_out(self, bcm, initial_high=False):
        d = FakeDigital(initial_high)
        self.digitals[bcm] = d
        return d

    def pwm_out(self, channel, freq_hz):
        p = FakePwm()
        self.pwms[channel] = p
        return p


def _mk(**kw):
    be = FakeBackend()
    drv = MotorDriver(backend=be, **kw)
    return be, drv


def _left(be):
    return be.digitals[LEFT_PINS.in1], be.digitals[LEFT_PINS.in2], be.pwms[LEFT_PINS.pwm_channel]


def _right(be):
    return be.digitals[RIGHT_PINS.in1], be.digitals[RIGHT_PINS.in2], be.pwms[RIGHT_PINS.pwm_channel]


def test_starts_disabled_and_coasting():
    be, drv = _mk()
    assert drv.enabled is False
    assert be.digitals[STBY_PIN].high is False          # STBY low at construction
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is False   # coast
        assert pwm.duty_pct == 0.0


def test_stby_interlock_blocks_motion_when_disabled():
    be, drv = _mk()
    drv.set_speed(1.0, 1.0)                               # disabled -> no-op
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is False
        assert pwm.duty_pct == 0.0
    assert be.digitals[STBY_PIN].high is False


def test_forward_sets_in1_high_and_scales_duty():
    be, drv = _mk()
    drv.enable()
    assert be.digitals[STBY_PIN].high is True
    drv.set_speed(0.5, 0.5)
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is True and in2.high is False     # H/L = forward
        assert math.isclose(pwm.duty_pct, 50.0)


def test_reverse_sets_in2_high():
    be, drv = _mk()
    drv.enable()
    drv.set_speed(-0.75, -0.75)
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is True     # L/H = reverse
        assert math.isclose(pwm.duty_pct, 75.0)


def test_zero_is_coast_not_brake():
    be, drv = _mk()
    drv.enable()
    drv.set_speed(0.6, 0.6)
    drv.set_speed(0.0, 0.0)                               # 0.0 must coast
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is False
        assert pwm.duty_pct == 0.0


def test_brake_shorts_both_terminals():
    be, drv = _mk()
    drv.enable()
    drv.brake()
    for in1, in2, _pwm in (_left(be), _right(be)):
        assert in1.high is True and in2.high is True       # H/H = short brake


def test_stop_coasts():
    be, drv = _mk()
    drv.enable()
    drv.set_speed(0.6, 0.6)
    drv.stop()
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is False
        assert pwm.duty_pct == 0.0


def test_speed_is_clamped():
    be, drv = _mk()
    drv.enable()
    drv.set_speed(2.0, -2.0)                              # out of range
    l1, l2, lp = _left(be)
    r1, r2, rp = _right(be)
    assert l1.high is True and l2.high is False and math.isclose(lp.duty_pct, 100.0)
    assert r1.high is False and r2.high is True and math.isclose(rp.duty_pct, 100.0)


def test_invert_left_flips_direction():
    be, drv = _mk(invert_left=True)
    drv.enable()
    drv.set_speed(0.5, 0.5)
    l1, l2, _ = _left(be)
    r1, r2, _ = _right(be)
    assert l1.high is False and l2.high is True            # left inverted -> reverse pins
    assert r1.high is True and r2.high is False            # right unaffected


def test_disable_coasts_and_pulls_stby_low():
    be, drv = _mk()
    drv.enable()
    drv.set_speed(0.8, 0.8)
    drv.disable()
    assert drv.enabled is False
    assert be.digitals[STBY_PIN].high is False
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.high is False and in2.high is False
        assert pwm.duty_pct == 0.0


def test_close_releases_all_lines():
    be, drv = _mk()
    drv.close()
    assert be.digitals[STBY_PIN].closed is True
    for in1, in2, pwm in (_left(be), _right(be)):
        assert in1.closed and in2.closed and pwm.closed


def test_counts_to_rad_s():
    # one full output rev in 1 s -> 2*pi rad/s
    assert math.isclose(counts_to_rad_s(COUNTS_PER_OUTPUT_REV, 1.0), 2.0 * math.pi)
    # sign is preserved
    assert counts_to_rad_s(-COUNTS_PER_OUTPUT_REV, 1.0) < 0.0
    # non-positive dt is safe
    assert counts_to_rad_s(100.0, 0.0) == 0.0
    assert counts_to_rad_s(100.0, -1.0) == 0.0


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
