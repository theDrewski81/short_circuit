#!/usr/bin/env python3
"""Bench bringup for the tread drive (Phase 02, Task 1).

Wheels FREE, robot NOT on treads, nothing in the pinch path. Runs the
docs/HARDWARE_drive_bringup.md sequence so you can confirm, per motor: correct
direction each phase, speed scaling with duty, encoder counts incrementing with
the correct sign, coast vs brake behaving differently, and the STBY interlock.

    python3 scripts/test_motors.py                 # default 0.6 duty, encoders on
    python3 scripts/test_motors.py --speed 0.8
    python3 scripts/test_motors.py --no-encoders   # if encoders not wired yet

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


def _phase(driver, enc, label: str, left: float, right: float, secs: float) -> None:
    print(f"\n>> {label}: set_speed(left={left:+.2f}, right={right:+.2f}) for {secs:.1f}s")
    driver.set_speed(left, right)
    time.sleep(secs)
    print(f"   encoders: {_fmt_enc(enc)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="TB6612 tread drive bench test")
    ap.add_argument("--speed", type=float, default=0.6,
                    help="duty magnitude 0..1 for the sequence (default 0.6)")
    ap.add_argument("--no-encoders", action="store_true",
                    help="skip EncoderReader (use if encoders are not wired)")
    args = ap.parse_args()
    spd = max(0.0, min(1.0, args.speed))

    print("=== Johnny 5 tread drive bench test ===")
    print("SAFETY: wheels free, robot off the treads, fingers clear of sprockets.")

    enc = None if args.no_encoders else EncoderReader()
    driver = MotorDriver()
    try:
        # Step 1 -- STBY interlock: with the driver disabled, set_speed must do nothing.
        print("\n[1] STBY interlock (driver disabled): commanding full speed -- "
              "motors must NOT move.")
        driver.set_speed(1.0, 1.0)
        time.sleep(1.0)
        print(f"    encoders (expect ~no change): {_fmt_enc(enc)}")

        # Step 2 -- enable, then the timed sequence.
        print("\n[2] Enabling driver (STBY high). Power VM now if not already.")
        driver.enable()
        if enc is not None:
            enc.reset()

        _phase(driver, enc, "forward", spd, spd, 2.0)
        print("\n>> stop (coast)"); driver.stop(); time.sleep(0.5)
        _phase(driver, enc, "backward", -spd, -spd, 2.0)
        print("\n>> stop (coast)"); driver.stop(); time.sleep(0.5)
        _phase(driver, enc, "turn left (in place, CCW)", -spd, spd, 1.0)
        _phase(driver, enc, "turn right (in place, CW)", spd, -spd, 1.0)

        # Step 3 -- coast vs brake, back to back from the same speed.
        print("\n[3] coast vs brake from forward:")
        driver.set_speed(spd, spd); time.sleep(1.0)
        driver.stop();  print("    coast issued"); time.sleep(1.0)
        driver.set_speed(spd, spd); time.sleep(1.0)
        driver.brake(); print("    brake issued (should stop noticeably faster)")
        time.sleep(1.0)

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
