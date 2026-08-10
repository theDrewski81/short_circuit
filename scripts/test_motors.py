#!/usr/bin/env python3
"""Bench bringup for the tread drive (Phase 02, Task 1).

Wheels FREE, robot NOT on treads, nothing in the pinch path. Runs the
docs/HARDWARE_drive_bringup.md sequence so you can confirm, per motor: correct
direction each phase, speed scaling with duty, encoder counts incrementing with
the correct sign, coast vs brake behaving differently, and the STBY interlock.

    python3 scripts/test_motors.py                 # default 0.6 duty, encoders on
    python3 scripts/test_motors.py --speed 0.8
    python3 scripts/test_motors.py --no-encoders   # if encoders not wired yet
    python3 scripts/test_motors.py --dwell 10      # 10x longer phases, easier to watch
    python3 scripts/test_motors.py --calibrate     # encoder counts/rev (motors OFF)

Bring VM up only after logic (per the doc): step 1 confirms STBY reads low and
the interlock holds before any motor can move.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_REPO, "src"))

from motion.motor_driver import MotorDriver, EncoderReader  # noqa: E402


def _fmt_enc(enc) -> str:
    if enc is None:
        return "(encoders off)"
    s = enc.read()
    return (
        f"L={s.ticks_left:+6d} ({s.speed_left:+5.1f} rad/s)  "
        f"R={s.ticks_right:+6d} ({s.speed_right:+5.1f} rad/s)"
    )


def _phase(driver, enc, label: str, left: float, right: float, secs: float,
           dwell: float = 1.0) -> None:
    secs *= dwell
    print(f"\n>> {label}: set_speed(left={left:+.2f}, right={right:+.2f}) for {secs:.1f}s")
    driver.set_speed(left, right)
    time.sleep(secs)
    print(f"   encoders: {_fmt_enc(enc)}")


def run_calibration(revs: float) -> int:
    """Hand-rotation encoder calibration -- motors stay OFF (no MotorDriver).

    Rotate each wheel exactly `revs` output revolutions by hand; prints the
    measured counts/output-rev so COUNTS_PER_OUTPUT_REV in motion/motor_driver.py
    can be set to the true value for this encoder and gpiozero's decoding mode.
    """
    from motion.motor_driver import COUNTS_PER_OUTPUT_REV
    print("=== Encoder counts/rev calibration (motors OFF, supply can stay off) ===")
    print(f"Rotate each wheel {revs:g} full output revolutions by hand when prompted.")
    enc = EncoderReader()
    results = {}
    try:
        for side, read_ticks in (("LEFT", lambda: enc.ticks_left),
                                 ("RIGHT", lambda: enc.ticks_right)):
            input(f"\n[{side}] Press Enter, then rotate the {side} wheel "
                  f"{revs:g} revs FORWARD...")
            enc.reset()
            input(f"[{side}] ...finished rotating? Press Enter to read.")
            counts = abs(read_ticks())
            cpr = counts / revs if revs else 0.0
            results[side] = cpr
            print(f"[{side}] {counts} counts / {revs:g} rev = {cpr:.1f} counts/output-rev")
    finally:
        enc.close()
    if len(results) == 2:
        avg = sum(results.values()) / 2.0
        print(f"\nMeasured avg = {avg:.1f} counts/output-rev "
              f"(current constant {COUNTS_PER_OUTPUT_REV:.1f}).")
        print("Set COUNTS_PER_OUTPUT_REV in src/motion/motor_driver.py to the measured value.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="TB6612 tread drive bench test")
    ap.add_argument("--speed", type=float, default=0.6,
                    help="duty magnitude 0..1 for the sequence (default 0.6)")
    ap.add_argument("--no-encoders", action="store_true",
                    help="skip EncoderReader (use if encoders are not wired)")
    ap.add_argument("--dwell", type=float, default=1.0,
                    help="multiplier on every phase/settle duration (default 1.0); "
                         "raise it to watch each phase longer on the bench")
    ap.add_argument("--calibrate", action="store_true",
                    help="encoder counts/output-rev calibration (motors stay OFF)")
    ap.add_argument("--revs", type=float, default=10.0,
                    help="output revolutions to hand-rotate during --calibrate")
    args = ap.parse_args()
    if args.calibrate:
        return run_calibration(args.revs)
    if args.dwell <= 0.0:
        # A zero/negative dwell would collapse the sequence into back-to-back
        # direction reversals with no settle time, which stresses the gearbox
        # and makes the encoder readings meaningless.
        ap.error("--dwell must be greater than 0")
    dwell = args.dwell
    spd = max(0.0, min(1.0, args.speed))

    def nap(secs: float) -> None:
        time.sleep(secs * dwell)

    print("=== Johnny 5 tread drive bench test ===")
    print("SAFETY: wheels free, robot off the treads, fingers clear of sprockets.")

    enc = None if args.no_encoders else EncoderReader()
    driver = MotorDriver()
    try:
        # Step 1 -- STBY interlock: with the driver disabled, set_speed must do nothing.
        print("\n[1] STBY interlock (driver disabled): commanding full speed -- "
              "motors must NOT move.")
        driver.set_speed(1.0, 1.0)
        nap(1.0)
        print(f"    encoders (expect ~no change): {_fmt_enc(enc)}")

        # Step 2 -- enable, then the timed sequence.
        print("\n[2] Enabling driver (STBY high). Power VM now if not already.")
        driver.enable()
        if enc is not None:
            enc.reset()

        _phase(driver, enc, "forward", spd, spd, 2.0, dwell)
        print("\n>> stop (coast)"); driver.stop(); nap(0.5)
        _phase(driver, enc, "backward", -spd, -spd, 2.0, dwell)
        print("\n>> stop (coast)"); driver.stop(); nap(0.5)
        _phase(driver, enc, "turn left (in place, CCW)", -spd, spd, 1.0, dwell)
        _phase(driver, enc, "turn right (in place, CW)", spd, -spd, 1.0, dwell)

        # Step 3 -- coast vs brake, back to back from the same speed.
        print("\n[3] coast vs brake from forward:")
        driver.set_speed(spd, spd); nap(1.0)
        driver.stop();  print("    coast issued"); nap(1.0)
        driver.set_speed(spd, spd); nap(1.0)
        driver.brake(); print("    brake issued (should stop noticeably faster)")
        nap(1.0)

        print("\n[OK] sequence complete. Verify against docs/HARDWARE_drive_bringup.md:")
        print("  - each motor turned the right way each phase")
        print("  - encoder signs matched 'forward' (flip invert_* / swap leads if not)")
        print("  - brake stopped faster than coast")
        return 0
    except KeyboardInterrupt:
        print("\n[ABORT] Ctrl-C -- stopping.")
        return 130
    finally:
        driver.close()      # disable() + release pins (STBY low)
        if enc is not None:
            enc.close()


if __name__ == "__main__":
    raise SystemExit(main())
