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
    python3 scripts/test_motors.py --calibrate     # encoder counts/rev (POWERED)

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


def _fit_counts_per_rev(counts: list[int]) -> float:
    """Least-squares slope of encoder count against revolution index.

    Fitting the slope rather than dividing total counts by revolutions makes the
    result immune to a constant human reaction lag: a fixed offset applied to
    every sample moves the intercept, not the slope.
    """
    n = len(counts)
    xbar = (n - 1) / 2.0
    ybar = sum(counts) / float(n)
    sxx = sum((i - xbar) ** 2 for i in range(n))
    sxy = sum((i - xbar) * (c - ybar) for i, c in enumerate(counts))
    return sxy / sxx


def run_calibration(revs: int, duty: float) -> int:
    """Powered encoder calibration -- one wheel at a time, driver ENABLED.

    The 150.58:1 N20 gearbox is not backdrivable at the output shaft (forcing it
    strips gears or splits the gearcase), so counts/output-rev is measured under
    power instead: mark one point on the wheel, run it slowly, and tap Enter each
    time the mark passes a fixed reference. The fitted slope is counts per output
    revolution, which is what COUNTS_PER_OUTPUT_REV in motion/motor_driver.py
    needs -- notably it settles whether gpiozero is decoding 1x (~452) or 4x
    (~1807) for this encoder.
    """
    from motion.motor_driver import COUNTS_PER_OUTPUT_REV
    print("=== Encoder counts/rev calibration (POWERED) ===")
    print("SAFETY: robot off the treads, both wheels free to spin, fingers clear.")
    print("Do NOT hand-rotate the output shaft -- the gearbox is not backdrivable.")
    print(f"\nMark one point on each wheel and pick a fixed reference to judge it")
    print(f"against. Each wheel runs at duty {duty:.2f} for {revs} revolutions.")

    enc = EncoderReader()
    driver = MotorDriver()
    results: dict[str, float] = {}
    try:
        driver.enable()
        for side, speeds, read_ticks in (
            ("LEFT", (duty, 0.0), lambda: enc.ticks_left),
            ("RIGHT", (0.0, duty), lambda: enc.ticks_right),
        ):
            input(f"\n[{side}] Press Enter to start this wheel...")
            enc.reset()
            driver.set_speed(*speeds)
            # Spin-up is non-linear; let it settle before the first sample so the
            # transient sits outside the fitted range.
            time.sleep(1.0)
            print(f"[{side}] running -- tap Enter at each mark pass "
                  f"({revs + 1} taps, starting with the next one).")
            counts: list[int] = []
            for i in range(revs + 1):
                input()
                counts.append(read_ticks())
                print(f"    rev {i}/{revs}: {counts[-1]:+d} counts")
            driver.stop()

            deltas = [counts[j + 1] - counts[j] for j in range(len(counts) - 1)]
            cpr = _fit_counts_per_rev(counts)
            if abs(cpr) < 1.0:
                print(f"[{side}] FAILED: counts barely moved. Either the wheel did "
                      f"not turn or this encoder channel is not reading.")
                continue
            if cpr < 0:
                print(f"[{side}] note: counts fell while driving forward -- encoder "
                      f"sign is inverted on this side.")
            results[side] = abs(cpr)
            print(f"[{side}] fit = {abs(cpr):.1f} counts/output-rev "
                  f"(per-rev deltas {min(deltas):+d}..{max(deltas):+d})")
    except KeyboardInterrupt:
        print("\n[ABORT] Ctrl-C -- stopping.")
        return 130
    finally:
        driver.close()      # disable() + release pins (STBY low)
        enc.close()

    if len(results) == 2:
        avg = sum(results.values()) / 2.0
        spread = abs(results["LEFT"] - results["RIGHT"]) / avg * 100.0
        print(f"\nMeasured avg = {avg:.1f} counts/output-rev "
              f"(current constant {COUNTS_PER_OUTPUT_REV:.1f}, "
              f"left/right spread {spread:.1f}%).")
        if spread > 5.0:
            print("Spread above 5% suggests a miscounted pass -- re-run before "
                  "trusting this.")
        print("Set COUNTS_PER_OUTPUT_REV in src/motion/motor_driver.py to the "
              "measured value, and log it in simulation/chassis/TUNING.md.")
    else:
        print("\nBoth sides did not produce a usable fit -- nothing to apply.")
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
                    help="powered encoder counts/output-rev calibration "
                         "(runs the motors; wheels must be free)")
    ap.add_argument("--revs", type=int, default=20,
                    help="marked wheel passes to sample per side during "
                         "--calibrate (default 20)")
    ap.add_argument("--calib-duty", type=float, default=0.25,
                    help="duty magnitude used during --calibrate (default 0.25); "
                         "low enough to track the mark, high enough not to stall")
    args = ap.parse_args()
    if args.calibrate:
        if args.revs < 2:
            # The slope needs at least two points, and a two-point fit is just
            # a difference -- the lag immunity only shows up over many revs.
            ap.error("--revs must be at least 2 (use 15-25 for a usable fit)")
        if not 0.0 < args.calib_duty <= 1.0:
            ap.error("--calib-duty must be in (0, 1]")
        return run_calibration(args.revs, args.calib_duty)
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
