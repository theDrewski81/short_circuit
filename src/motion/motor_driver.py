"""Motor driver + encoder reader for Pi-M (Phase 02, Task 1).

Drives the two tread motors through a TB6612FNG dual H-bridge (BOM section 1) and
reads the N20 quadrature encoders. Speed (PWMA/PWMB, GPIO 12/13) uses the Pi's
kernel hardware-PWM peripheral via `rpi-hardware-pwm` (requires
`dtoverlay=pwm-2chan` in /boot/firmware/config.txt); the direction and STBY lines
and the encoders use gpiozero on the lgpio pin factory. Hardware-timed PWM keeps
the 20 kHz carrier glitch-free and off the CPU -- which matters inside the 50 Hz
motion loop on the single-core Pi Zero 2 W (lgpio's own PWM is software-timed).

TB6612FNG control contract (docs/HARDWARE_drive_bringup.md), per channel, STBY HIGH:

    IN1 IN2 PWM   result
    H   L   duty  forward (speed proportional to duty)
    L   H   duty  reverse
    H   H    x    short brake (terminals shorted)
    L   L    x    coast (outputs high-Z)

With a direction set, PWM=0 is a short brake, NOT a coast -- true coast is
IN1=L, IN2=L. STBY LOW forces all outputs off and is the boot/crash/offline
fail-safe. STBY is held LOW at construction; nothing drives until enable().

Hardware access sits behind a small backend so the control logic is unit-testable
without a Pi (see tests/test_motor_driver.py). The real backend imports gpiozero
and rpi-hardware-pwm lazily, so this module imports cleanly off-target.
"""

from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger("johnny5.motion.motor_driver")

# --- Pin map (Pi-M, BCM) -- BOM.md GPIO map + docs/HARDWARE_drive_bringup.md ---
PWM_FREQ_HZ = 20_000          # above audible, well under the TB6612 100 kHz max
PWM_CHIP = 0                  # Pi Zero 2 W (BCM2837): pwmchip0. (Pi 5 would be 2.)


@dataclass(frozen=True)
class MotorPins:
    pwm_channel: int          # kernel PWM channel: 0 -> GPIO12 (A), 1 -> GPIO13 (B)
    in1: int                  # direction pin (BCM)
    in2: int                  # direction pin (BCM)


LEFT_PINS = MotorPins(pwm_channel=0, in1=5, in2=6)      # motor A: PWMA/AIN1/AIN2
RIGHT_PINS = MotorPins(pwm_channel=1, in1=16, in2=26)   # motor B: PWMB/BIN1/BIN2
STBY_PIN = 20

ENC_LEFT_A, ENC_LEFT_B = 17, 27
ENC_RIGHT_A, ENC_RIGHT_B = 22, 23
COUNTS_PER_OUTPUT_REV = 1807.0   # 12 CPR x 150.58 gearbox, quadrature


# --------------------------------------------------------------------------- #
# Hardware backend abstraction (swappable for tests)                          #
# --------------------------------------------------------------------------- #
class DigitalOut(Protocol):
    def set(self, high: bool) -> None: ...
    def close(self) -> None: ...


class PwmOut(Protocol):
    def duty(self, percent: float) -> None: ...   # clamp + apply 0..100 % duty
    def close(self) -> None: ...


class GpioBackend(Protocol):
    def digital_out(self, bcm: int, initial_high: bool = False) -> DigitalOut: ...
    def pwm_out(self, channel: int, freq_hz: int) -> PwmOut: ...


class _GzDigitalOut:
    def __init__(self, dev) -> None:
        self._dev = dev

    def set(self, high: bool) -> None:
        self._dev.on() if high else self._dev.off()

    def close(self) -> None:
        self._dev.close()


class _HwPwmOut:
    def __init__(self, pwm) -> None:
        self._pwm = pwm

    def duty(self, percent: float) -> None:
        self._pwm.change_duty_cycle(max(0.0, min(100.0, float(percent))))

    def close(self) -> None:
        try:
            self._pwm.stop()
        except Exception:  # pragma: no cover - best-effort teardown
            pass


class RealGpioBackend:
    """gpiozero (lgpio) direction/STBY lines + rpi-hardware-pwm speed channels."""

    def __init__(self, pwm_chip: int = PWM_CHIP) -> None:
        self._pwm_chip = pwm_chip
        # Pin the lgpio factory explicitly. gpiozero 2.x defaults to it on
        # Trixie/Bookworm, but being explicit stops a silent fall-back to a
        # degraded factory (e.g. RPi.GPIO, which is broken on these kernels).
        try:
            from gpiozero import Device
            from gpiozero.pins.lgpio import LGPIOFactory
            if not isinstance(Device.pin_factory, LGPIOFactory):
                Device.pin_factory = LGPIOFactory()
        except Exception:  # pragma: no cover - host dependent
            logger.warning("lgpio pin factory unavailable; using gpiozero default")

    def digital_out(self, bcm: int, initial_high: bool = False) -> DigitalOut:
        from gpiozero import DigitalOutputDevice
        return _GzDigitalOut(DigitalOutputDevice(bcm, initial_value=initial_high))

    def pwm_out(self, channel: int, freq_hz: int) -> PwmOut:
        from rpi_hardware_pwm import HardwarePWM
        pwm = HardwarePWM(pwm_channel=channel, hz=freq_hz, chip=self._pwm_chip)
        pwm.start(0.0)
        return _HwPwmOut(pwm)


# --------------------------------------------------------------------------- #
# Motor driver                                                                #
# --------------------------------------------------------------------------- #
class MotorDriver:
    """Normalised tread drive over a TB6612FNG.

    set_speed(left, right): -1.0 (full reverse) .. +1.0 (full forward), 0.0 = stop.
    Sign selects direction (IN1/IN2); magnitude sets PWM duty. 0.0 coasts. The
    interface is H-bridge-agnostic; only the internals are TB6612-specific.

    invert_left / invert_right flip a side in software when a motor is wired
    backwards. Prefer swapping the motor leads on the bench (AO1/AO2 or BO1/BO2)
    and log whichever you use in simulation/chassis/TUNING.md.
    """

    def __init__(
        self,
        backend: GpioBackend | None = None,
        left: MotorPins = LEFT_PINS,
        right: MotorPins = RIGHT_PINS,
        stby: int = STBY_PIN,
        pwm_freq_hz: int = PWM_FREQ_HZ,
        invert_left: bool = False,
        invert_right: bool = False,
    ) -> None:
        self._backend = backend or RealGpioBackend()
        self._invert = {"left": invert_left, "right": invert_right}
        # STBY LOW at construction -> motors off until enable() (fail-safe).
        self._stby = self._backend.digital_out(stby, initial_high=False)
        self._enabled = False
        self._chan: dict[str, dict] = {}
        for name, pins in (("left", left), ("right", right)):
            self._chan[name] = {
                "in1": self._backend.digital_out(pins.in1, initial_high=False),
                "in2": self._backend.digital_out(pins.in2, initial_high=False),
                "pwm": self._backend.pwm_out(pins.pwm_channel, pwm_freq_hz),
            }
        self._coast_channel("left")
        self._coast_channel("right")
        logger.info("MotorDriver init: disabled, STBY low, outputs coasting")

    # --- enable / disable (STBY interlock) ---
    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        """Drive STBY HIGH so set_speed/brake take effect."""
        self._stby.set(True)
        self._enabled = True
        logger.info("MotorDriver enabled (STBY high)")

    def disable(self) -> None:
        """Coast, then pull STBY LOW. Used on shutdown and offline fallback."""
        self.stop()
        self._stby.set(False)
        self._enabled = False
        logger.info("MotorDriver disabled (STBY low)")

    # --- motion ---
    def set_speed(self, left: float, right: float) -> None:
        """left, right in [-1, 1]. No-op while disabled (STBY interlock)."""
        if not self._enabled:
            logger.debug("set_speed ignored: driver disabled (STBY low)")
            return
        self._set_channel("left", left)
        self._set_channel("right", right)

    def stop(self) -> None:
        """Coast both motors (IN1=L, IN2=L, PWM 0)."""
        self._coast_channel("left")
        self._coast_channel("right")

    def brake(self) -> None:
        """Short-brake both motors (IN1=H, IN2=H). Faster stop than coast."""
        self._brake_channel("left")
        self._brake_channel("right")

    # --- teardown ---
    def close(self) -> None:
        try:
            self.disable()
        finally:
            for ch in self._chan.values():
                for line in ch.values():
                    line.close()
            self._stby.close()

    def __enter__(self) -> "MotorDriver":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- internals ---
    def _set_channel(self, name: str, value: float) -> None:
        value = max(-1.0, min(1.0, float(value)))
        if self._invert[name]:
            value = -value
        if value == 0.0:
            self._coast_channel(name)
            return
        forward = value > 0.0
        ch = self._chan[name]
        ch["in1"].set(forward)        # H/L forward, L/H reverse
        ch["in2"].set(not forward)
        ch["pwm"].duty(abs(value) * 100.0)

    def _coast_channel(self, name: str) -> None:
        ch = self._chan[name]
        ch["in1"].set(False)
        ch["in2"].set(False)
        ch["pwm"].duty(0.0)

    def _brake_channel(self, name: str) -> None:
        ch = self._chan[name]
        ch["in1"].set(True)
        ch["in2"].set(True)
        ch["pwm"].duty(0.0)           # duty is don't-care in short brake


# --------------------------------------------------------------------------- #
# Encoders                                                                    #
# --------------------------------------------------------------------------- #
def counts_to_rad_s(
    delta_counts: float, dt_s: float, counts_per_rev: float = COUNTS_PER_OUTPUT_REV
) -> float:
    """Signed wheel speed (rad/s) from a quadrature tick delta over dt seconds."""
    if dt_s <= 0.0:
        return 0.0
    return (delta_counts / counts_per_rev) * (2.0 * math.pi) / dt_s


@dataclass
class EncoderSample:
    ticks_left: int        # signed cumulative counts
    ticks_right: int
    speed_left: float      # rad/s, signed, since the previous read()
    speed_right: float


class EncoderReader:
    """Callback-driven quadrature counter for both drive encoders.

    Counting is interrupt/callback based (gpiozero.RotaryEncoder on the lgpio
    factory) -- never polled in the motion loop. read() snapshots cumulative
    signed counts and the rad/s rate derived from the delta since the previous
    read(). The count sign must match motor "forward"; flip a side with
    invert_left/right and log it in simulation/chassis/TUNING.md next to any
    motor lead swap. Encoder feeds forward velocity for the policy obs (Phase 02)
    and odometry (Phase 05).
    """

    def __init__(
        self,
        a_left: int = ENC_LEFT_A,
        b_left: int = ENC_LEFT_B,
        a_right: int = ENC_RIGHT_A,
        b_right: int = ENC_RIGHT_B,
        invert_left: bool = False,
        invert_right: bool = False,
        counts_per_rev: float = COUNTS_PER_OUTPUT_REV,
    ) -> None:
        from gpiozero import RotaryEncoder  # lazy: keeps off-target import clean
        self._counts_per_rev = counts_per_rev
        self._sign_left = -1 if invert_left else 1
        self._sign_right = -1 if invert_right else 1
        # max_steps=0 -> unbounded cumulative count (no wrap).
        self._enc_left = RotaryEncoder(a_left, b_left, max_steps=0)
        self._enc_right = RotaryEncoder(a_right, b_right, max_steps=0)
        self._last_t = time.monotonic()
        self._last_left = 0
        self._last_right = 0

    @property
    def ticks_left(self) -> int:
        return self._sign_left * self._enc_left.steps

    @property
    def ticks_right(self) -> int:
        return self._sign_right * self._enc_right.steps

    def read(self) -> EncoderSample:
        """Snapshot counts + rad/s since the previous read()."""
        now = time.monotonic()
        dt = now - self._last_t
        left = self.ticks_left
        right = self.ticks_right
        speed_left = counts_to_rad_s(left - self._last_left, dt, self._counts_per_rev)
        speed_right = counts_to_rad_s(right - self._last_right, dt, self._counts_per_rev)
        self._last_t, self._last_left, self._last_right = now, left, right
        return EncoderSample(left, right, speed_left, speed_right)

    def reset(self) -> None:
        self._enc_left.steps = 0
        self._enc_right.steps = 0
        self._last_left = self._last_right = 0
        self._last_t = time.monotonic()

    def close(self) -> None:
        self._enc_left.close()
        self._enc_right.close()

    def __enter__(self) -> "EncoderReader":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
