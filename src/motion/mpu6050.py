"""MPU-6050 IMU driver for Pi-M (Phase 02, Task 2).

Reads the MPU-6050 (BOM section 3, I2C 0x68) over I2C and fuses accelerometer +
gyroscope with a complementary filter to produce roll/pitch; yaw_rate is the
gyro z-axis passed straight through (no magnetometer -- yaw is rate-only, see
simulation/chassis/TUNING.md "Observation reconstruction on Pi-M"). Feeds
MotionState (motion.locomotion_policy) via motion.main._read_motion_state().

Axis convention: assumes the IMU is mounted with its X axis forward, Y axis
left, Z axis up -- matching the sim body frame in simulation/chassis/env.py
(consistent with the roll/pitch sign convention MotionState expects). This is
an assumption, not a measurement; confirm on the bench during Task 6 physical
integration and correct with the invert_accel/invert_gyro flags (or swap the
accel_roll/accel_pitch axis pairing below) if the physical mounting differs --
log any correction in simulation/chassis/TUNING.md next to the motor-lead and
encoder-channel notes from Task 1, the same "fix in hardware/config, not a
retrain" pattern.

Hardware access sits behind a small I2C backend so the fusion math is
unit-testable without a Pi (see tests/test_mpu6050.py). The real backend
imports smbus2 lazily, so this module imports cleanly off-target.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("johnny5.motion.mpu6050")

# --- Registers / constants (MPU-6050 datasheet + register map) ---
MPU6050_ADDR = 0x68            # BOM.md section 3 / GPIO map: I2C1 (GPIO2/3)
REG_PWR_MGMT_1 = 0x6B
REG_WHO_AM_I = 0x75
REG_ACCEL_XOUT_H = 0x3B        # 6 bytes: ax_h ax_l ay_h ay_l az_h az_l
REG_GYRO_XOUT_H = 0x43         # 6 bytes: gx_h gx_l gy_h gy_l gz_h gz_l
WHO_AM_I_EXPECTED = 0x68

# Power-on defaults: +-2g accel, +-250 dps gyro (we never touch CONFIG/
# GYRO_CONFIG/ACCEL_CONFIG, so these sensitivities hold).
ACCEL_SENS_LSB_PER_G = 16384.0
GYRO_SENS_LSB_PER_DPS = 131.0
G_TO_MPS2 = 9.80665

# Complementary filter: heavily trust the gyro integral over the short term
# (drift-free), bleed toward the accel tilt estimate over the long term (bias-
# free but noisy under acceleration). 0.98 is the standard starting point for
# a ~50 Hz loop; retune here (not in main.py) if bench data says otherwise.
DEFAULT_ALPHA = 0.98
# Reject a fused update if dt is stale/garbage (first read, scheduler hiccup) --
# fall back to the accel-only tilt estimate instead of integrating over a big gap.
MAX_VALID_DT_S = 1.0


def _s16(hi: int, lo: int) -> int:
    """Big-endian two's-complement 16-bit register pair -> signed int."""
    val = (hi << 8) | lo
    return val - 0x10000 if val >= 0x8000 else val


@dataclass
class ImuSample:
    """One raw fused-unit reading, body frame (X forward, Y left, Z up)."""
    accel_x: float  # m/s^2
    accel_y: float
    accel_z: float
    gyro_x: float    # rad/s
    gyro_y: float
    gyro_z: float


# --------------------------------------------------------------------------- #
# I2C backend abstraction (swappable for tests)                               #
# --------------------------------------------------------------------------- #
class I2CBackend(Protocol):
    def read_block(self, addr: int, reg: int, length: int) -> bytes: ...
    def write_byte(self, addr: int, reg: int, value: int) -> None: ...
    def close(self) -> None: ...


class Smbus2Backend:
    """Real I2C backend via smbus2. Bus 1 is Pi-M's I2C1 (GPIO2/3, BOM GPIO map)."""

    def __init__(self, bus_num: int = 1) -> None:
        import smbus2  # lazy: keeps off-target import clean
        self._bus = smbus2.SMBus(bus_num)

    def read_block(self, addr: int, reg: int, length: int) -> bytes:
        return bytes(self._bus.read_i2c_block_data(addr, reg, length))

    def write_byte(self, addr: int, reg: int, value: int) -> None:
        self._bus.write_byte_data(addr, reg, value)

    def close(self) -> None:
        try:
            self._bus.close()
        except Exception:  # pragma: no cover - best-effort teardown
            pass


# --------------------------------------------------------------------------- #
# Driver                                                                      #
# --------------------------------------------------------------------------- #
class MPU6050:
    """MPU-6050 reader: raw registers -> fused (roll, pitch, yaw_rate).

    read() is stateful (it integrates the gyro across calls using wall-clock
    dt), so call it once per motion-loop tick -- not re-entrantly / concurrently.
    """

    def __init__(
        self,
        backend: I2CBackend | None = None,
        address: int = MPU6050_ADDR,
        alpha: float = DEFAULT_ALPHA,
        invert_accel: tuple[int, int, int] = (1, 1, 1),
        invert_gyro: tuple[int, int, int] = (1, 1, 1),
        skip_wake: bool = False,
    ) -> None:
        self._backend = backend or Smbus2Backend()
        self._addr = address
        self._alpha = alpha
        self._sa = invert_accel
        self._sg = invert_gyro
        self._roll = 0.0
        self._pitch = 0.0
        self._last_t: float | None = None
        if not skip_wake:
            # MPU-6050 boots into sleep mode (PWR_MGMT_1 bit 6 set) -- clear it.
            self._backend.write_byte(self._addr, REG_PWR_MGMT_1, 0x00)
        logger.info("MPU6050 init at 0x%02X (alpha=%.3f)", self._addr, self._alpha)

    def read_raw(self) -> ImuSample:
        """One register read -> physical units, no filtering."""
        a = self._backend.read_block(self._addr, REG_ACCEL_XOUT_H, 6)
        g = self._backend.read_block(self._addr, REG_GYRO_XOUT_H, 6)
        ax = _s16(a[0], a[1]) / ACCEL_SENS_LSB_PER_G * G_TO_MPS2 * self._sa[0]
        ay = _s16(a[2], a[3]) / ACCEL_SENS_LSB_PER_G * G_TO_MPS2 * self._sa[1]
        az = _s16(a[4], a[5]) / ACCEL_SENS_LSB_PER_G * G_TO_MPS2 * self._sa[2]
        gx = math.radians(_s16(g[0], g[1]) / GYRO_SENS_LSB_PER_DPS) * self._sg[0]
        gy = math.radians(_s16(g[2], g[3]) / GYRO_SENS_LSB_PER_DPS) * self._sg[1]
        gz = math.radians(_s16(g[4], g[5]) / GYRO_SENS_LSB_PER_DPS) * self._sg[2]
        return ImuSample(ax, ay, az, gx, gy, gz)

    def read(self, now: float | None = None) -> tuple[float, float, float]:
        """Returns (roll, pitch, yaw_rate) in radians / rad-s.

        roll/pitch: complementary-filtered fusion of accel tilt + integrated
        gyro rate. yaw_rate: gyro z, unfiltered (rate-only, no absolute heading
        -- see module docstring).
        """
        now = now if now is not None else time.monotonic()
        s = self.read_raw()
        accel_roll = math.atan2(s.accel_y, s.accel_z)
        accel_pitch = math.atan2(-s.accel_x, math.hypot(s.accel_y, s.accel_z))

        dt = (now - self._last_t) if self._last_t is not None else None
        if dt is None or dt <= 0.0 or dt > MAX_VALID_DT_S:
            # First call, or a stale/garbage gap -- trust the accel-only
            # estimate rather than integrating gyro over an unknown interval.
            self._roll, self._pitch = accel_roll, accel_pitch
        else:
            a = self._alpha
            self._roll = a * (self._roll + s.gyro_x * dt) + (1.0 - a) * accel_roll
            self._pitch = a * (self._pitch + s.gyro_y * dt) + (1.0 - a) * accel_pitch
        self._last_t = now
        return self._roll, self._pitch, s.gyro_z

    def reset_fusion(self) -> None:
        """Drop the integrated roll/pitch estimate (e.g. after a long stall)."""
        self._roll = self._pitch = 0.0
        self._last_t = None

    def close(self) -> None:
        self._backend.close()

    def __enter__(self) -> "MPU6050":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
