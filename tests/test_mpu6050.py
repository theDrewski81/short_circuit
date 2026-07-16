"""Sandbox unit tests for the MPU-6050 driver (Phase 02, Task 2).

No Pi/I2C required: MPU6050 is driven through a fake I2C backend that returns
canned register bytes, so these assert the register decode + complementary
filter math. Runnable either way:

    python3 -m pytest tests/test_mpu6050.py
    python3 tests/test_mpu6050.py            # no pytest needed
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from motion.mpu6050 import (  # noqa: E402
    MPU6050, REG_ACCEL_XOUT_H, REG_GYRO_XOUT_H, REG_PWR_MGMT_1,
    ACCEL_SENS_LSB_PER_G, GYRO_SENS_LSB_PER_DPS, G_TO_MPS2, _s16,
)


def _enc16(val: int) -> tuple[int, int]:
    """signed int -> (hi, lo) big-endian register bytes, inverse of _s16."""
    if val < 0:
        val += 0x10000
    return (val >> 8) & 0xFF, val & 0xFF


class FakeI2C:
    """Records writes; serves accel/gyro blocks from settable raw counts."""

    def __init__(self):
        self.writes = []
        self.closed = False
        # raw LSB counts, order ax,ay,az,gx,gy,gz -- default: level, at rest
        # az = +1g so a level board reads accel_z = +9.80665 m/s^2.
        self.raw = [0, 0, int(ACCEL_SENS_LSB_PER_G), 0, 0, 0]

    def set_raw_physical(self, ax_g=0.0, ay_g=0.0, az_g=1.0, gx_dps=0.0, gy_dps=0.0, gz_dps=0.0):
        self.raw = [
            int(ax_g * ACCEL_SENS_LSB_PER_G), int(ay_g * ACCEL_SENS_LSB_PER_G),
            int(az_g * ACCEL_SENS_LSB_PER_G),
            int(gx_dps * GYRO_SENS_LSB_PER_DPS), int(gy_dps * GYRO_SENS_LSB_PER_DPS),
            int(gz_dps * GYRO_SENS_LSB_PER_DPS),
        ]

    def read_block(self, addr, reg, length):
        assert length == 6
        if reg == REG_ACCEL_XOUT_H:
            vals = self.raw[0:3]
        elif reg == REG_GYRO_XOUT_H:
            vals = self.raw[3:6]
        else:
            raise ValueError(f"unexpected reg {reg:#x}")
        out = []
        for v in vals:
            hi, lo = _enc16(v)
            out += [hi, lo]
        return bytes(out)

    def write_byte(self, addr, reg, value):
        self.writes.append((addr, reg, value))

    def close(self):
        self.closed = True


def _mk(**kw):
    be = FakeI2C()
    imu = MPU6050(backend=be, **kw)
    return be, imu


def test_wakes_from_sleep_on_init():
    be, imu = _mk()
    assert (MPU6050.__init__.__defaults__ is not None) or True  # smoke
    assert be.writes == [(0x68, REG_PWR_MGMT_1, 0x00)]


def test_skip_wake_suppresses_write():
    be, imu = _mk(skip_wake=True)
    assert be.writes == []


def test_s16_roundtrip():
    for v in (0, 1, -1, 16383, -16384, 32767, -32768):
        hi, lo = _enc16(v)
        assert _s16(hi, lo) == v


def test_level_at_rest_reads_zero_roll_pitch():
    be, imu = _mk()
    be.set_raw_physical(az_g=1.0)  # level: gravity entirely on Z
    roll, pitch, yaw_rate = imu.read(now=0.0)
    assert math.isclose(roll, 0.0, abs_tol=1e-6)
    assert math.isclose(pitch, 0.0, abs_tol=1e-6)
    assert yaw_rate == 0.0


def test_first_call_trusts_accel_only():
    be, imu = _mk()
    be.set_raw_physical(ax_g=0.0, ay_g=1.0, az_g=0.0)  # rolled 90 deg
    roll, pitch, _ = imu.read(now=0.0)
    assert math.isclose(roll, math.pi / 2, abs_tol=1e-3)


def test_gyro_z_passthrough_unfiltered():
    be, imu = _mk()
    be.set_raw_physical(gz_dps=90.0)
    _, _, yaw_rate = imu.read(now=0.0)
    assert math.isclose(yaw_rate, math.radians(90.0), rel_tol=1e-3)


def test_stale_dt_falls_back_to_accel_only():
    be, imu = _mk(alpha=0.98)
    be.set_raw_physical(az_g=1.0)
    imu.read(now=0.0)
    # Simulate a big gap (> MAX_VALID_DT_S) with a large integrated gyro rate
    # that would blow up the estimate if wrongly integrated.
    be.set_raw_physical(ax_g=0.0, ay_g=0.0, az_g=1.0, gx_dps=500.0)
    roll, pitch, _ = imu.read(now=5.0)
    # accel says level -> roll/pitch should reset near zero, not have
    # integrated 500 dps * 5s of garbage.
    assert math.isclose(roll, 0.0, abs_tol=1e-6)


def test_complementary_filter_blends_gyro_and_accel():
    be, imu = _mk(alpha=0.98)
    be.set_raw_physical(az_g=1.0)
    imu.read(now=0.0)  # seed at 0
    # Constant gyro-x rate for a short dt, accel still says level (0 roll).
    be.set_raw_physical(az_g=1.0, gx_dps=math.degrees(1.0))  # 1 rad/s
    roll, _, _ = imu.read(now=0.1)
    # Expected: mostly gyro-integrated (0.98 * (0 + 1*0.1)) + a sliver of accel.
    expected = 0.98 * (0.0 + 1.0 * 0.1) + 0.02 * 0.0
    assert math.isclose(roll, expected, rel_tol=1e-3)


def test_reset_fusion_clears_state():
    be, imu = _mk()
    be.set_raw_physical(ay_g=1.0, az_g=0.0)
    imu.read(now=0.0)
    imu.reset_fusion()
    be.set_raw_physical(az_g=1.0)
    roll, pitch, _ = imu.read(now=100.0)  # far-future now, no stale-dt blowup
    assert math.isclose(roll, 0.0, abs_tol=1e-6)


def test_invert_gyro_flips_sign():
    be, imu = _mk(invert_gyro=(1, 1, -1))
    be.set_raw_physical(gz_dps=45.0)
    _, _, yaw_rate = imu.read(now=0.0)
    assert yaw_rate < 0.0


def test_close_closes_backend():
    be, imu = _mk()
    imu.close()
    assert be.closed is True


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
