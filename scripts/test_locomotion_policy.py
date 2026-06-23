"""Validation for the LocomotionPolicy runner (Phase 02, Task 5).

Loads the deployed ONNX policy, runs 100 inference steps to report latency and
output range, and checks that canonical commands produce the correct motor
directions. Run on the dev box for a smoke check and ON THE PI to measure the
real per-step latency against the < 5 ms target.

    python3 scripts/test_locomotion_policy.py                 # newest policies/locomotion_*.onnx
    python3 scripts/test_locomotion_policy.py --model path.onnx
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, ".."))
sys.path.insert(0, os.path.join(_REPO, "src"))

from motion.locomotion_policy import (  # noqa: E402
    LocomotionPolicy, MotionState, command_from_intent, V_MAX, W_MAX,
)

LATENCY_TARGET_MS = 5.0  # per-step budget on the Pi Zero 2 W (20 ms tick @ 50 Hz)


def _newest_policy() -> str:
    cands = sorted(glob.glob(os.path.join(_REPO, "policies", "locomotion_*.onnx")))
    if not cands:
        raise FileNotFoundError("no policies/locomotion_*.onnx found; pass --model")
    return cands[-1]


def latency_and_range(pol: LocomotionPolicy, n: int = 100, seed: int = 0):
    rng = np.random.default_rng(seed)
    pol.step(MotionState(), (0.0, 0.0))  # warm up (first run pays graph init)
    lats, outs = [], []
    for _ in range(n):
        st = MotionState(
            roll=float(rng.uniform(-0.3, 0.3)), pitch=float(rng.uniform(-0.3, 0.3)),
            yaw_rate=float(rng.uniform(-W_MAX, W_MAX)),
            forward_velocity=float(rng.uniform(-V_MAX, V_MAX)),
            lateral_velocity=float(rng.uniform(-0.05, 0.05)),
            wheel_speed_left=float(rng.uniform(-12.9, 12.9)),
            wheel_speed_right=float(rng.uniform(-12.9, 12.9)),
        )
        cmd = (float(rng.uniform(-V_MAX, V_MAX)), float(rng.uniform(-W_MAX, W_MAX)))
        t0 = time.perf_counter()
        l, r = pol.step(st, cmd)
        lats.append((time.perf_counter() - t0) * 1000.0)
        outs.append((l, r))
    lats = np.array(lats); outs = np.array(outs)
    finite = bool(np.all(np.isfinite(outs)))
    in_range = bool(np.all(np.abs(outs) <= 1.0 + 1e-6))
    print(f"latency over {n} steps: mean {lats.mean():.3f} ms | p50 {np.percentile(lats,50):.3f} | "
          f"p95 {np.percentile(lats,95):.3f} | max {lats.max():.3f} ms")
    print(f"output range: left [{outs[:,0].min():+.2f}, {outs[:,0].max():+.2f}]  "
          f"right [{outs[:,1].min():+.2f}, {outs[:,1].max():+.2f}]  finite={finite} in[-1,1]={in_range}")
    note = "PASS" if lats.mean() < LATENCY_TARGET_MS else f"OVER {LATENCY_TARGET_MS} ms (Pi target; x86 dev box differs)"
    print(f"latency vs {LATENCY_TARGET_MS} ms target: {note}")
    return finite and in_range


def direction_checks(pol: LocomotionPolicy):
    st = MotionState()  # at rest
    def cmd(a, p): return pol.step(st, command_from_intent(a, p))
    fwd = cmd("move", {"speed": 1.0})
    back = cmd("move", {"speed": -1.0})
    spinL = cmd("turn", {"rate": 1.0})
    spinR = cmd("turn", {"rate": -1.0})
    stop = cmd("idle", {})
    print("\ncommand-direction checks (left, right):")
    for name, (l, r) in [("forward", fwd), ("backward", back), ("spin-left", spinL),
                         ("spin-right", spinR), ("stop", stop)]:
        print(f"  {name:11s} -> ({l:+.2f}, {r:+.2f})")
    ok = (
        fwd[0] > 0.3 and fwd[1] > 0.3 and
        back[0] < -0.3 and back[1] < -0.3 and
        spinL[0] < spinL[1] and          # left wheel slower/reverse vs right -> CCW
        spinR[0] > spinR[1] and          # mirror -> CW
        abs(stop[0]) < 0.3 and abs(stop[1]) < 0.3
    )
    print("direction checks:", "PASS" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None)
    ap.add_argument("-n", type=int, default=100)
    args = ap.parse_args()
    model = args.model or _newest_policy()
    print(f"policy: {model}")
    pol = LocomotionPolicy(model)
    ok1 = latency_and_range(pol, n=args.n)
    ok2 = direction_checks(pol)
    print("\nRESULT:", "PASS" if (ok1 and ok2) else "FAIL")
    sys.exit(0 if (ok1 and ok2) else 1)
