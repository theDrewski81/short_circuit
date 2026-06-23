"""Locomotion policy inference runner for Pi-M (Phase 02, Task 5).

Loads the ONNX policy exported from the MuJoCo training (policies/locomotion_*.onnx)
and turns a high-level command plus the current sensor state into left/right motor
effort in [-1, 1]. Runs inside the 50 Hz motion loop; target < 5 ms per step on the
Pi Zero 2 W so it fits inside the 20 ms tick.

The observation vector MUST match the layout, order, and normalisation produced by
the training env's `JohnnyChassisEnv._obs()` (simulation/chassis/env.py); the ONNX
already bakes in the VecNormalize running stats, so we feed the same pre-normalised
9-vector the env produced. See simulation/chassis/TUNING.md
("Observation reconstruction on Pi-M") for the sensor-to-channel mapping.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np

# --- Normalisation constants. MUST stay in lock-step with simulation/chassis/env.py.
# If env.py changes V_MAX / W_MAX / NO_LOAD_WHEEL, retrain+re-export AND update these.
V_MAX = 0.28          # m/s  forward/backward command + velocity scale
W_MAX = 0.30          # rad/s yaw command + yaw-rate scale
NO_LOAD_WHEEL = 12.9  # rad/s wheel-speed (encoder) scale
OBS_DIM = 9
ACT_DIM = 2


@dataclass
class MotionState:
    """Current chassis sensor state, in SI units, body frame.

    forward_velocity / lateral_velocity are BODY-frame (x = forward, y = left),
    matching the env's post-rotation velocities. On hardware: forward_velocity
    from encoder odometry (mean drive-wheel speed x wheel radius), lateral_velocity
    ~0 (not directly measurable -- see TUNING.md). roll/pitch from MPU-6050
    accel+gyro fusion; yaw_rate from the gyro z axis; wheel speeds from the
    rear-left/right quadrature encoders.
    """
    roll: float = 0.0
    pitch: float = 0.0
    yaw_rate: float = 0.0
    forward_velocity: float = 0.0
    lateral_velocity: float = 0.0
    wheel_speed_left: float = 0.0
    wheel_speed_right: float = 0.0


def command_from_intent(action: str, params: dict | None) -> tuple[float, float]:
    """Map a johnny5/intent (action, params) to a (v_cmd, w_cmd) command in SI units.

    PROVISIONAL -- the per-action params schema is finalised in src/shared/PROTOCOL.md
    as Phase 02 lands. Conventions used here:
      move : params{"speed": -1..1}            -> v_cmd = speed * V_MAX, w_cmd = 0
      turn : params{"rate": -1..1}             -> w_cmd = rate  * W_MAX, v_cmd = 0
             (rate > 0 = left/CCW)
      arc  : params{"speed": .., "rate": ..}   -> both
      idle / anything else                     -> (0, 0)  (hold still)
    Values are clamped to the reachable envelope.
    """
    params = params or {}
    v = w = 0.0
    if action in ("move", "arc"):
        v = float(params.get("speed", 0.0)) * V_MAX
    if action in ("turn", "arc"):
        w = float(params.get("rate", 0.0)) * W_MAX
    v = max(-V_MAX, min(V_MAX, v))
    w = max(-W_MAX, min(W_MAX, w))
    return v, w


class LocomotionPolicy:
    """ONNX locomotion policy: (command + sensor state) -> (left, right) in [-1, 1]."""

    def __init__(self, model_path: str, intra_op_threads: int = 1, providers=None):
        import onnxruntime as ort  # imported here so the module loads without ort present

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"policy not found: {model_path}")

        opts = ort.SessionOptions()
        # Tiny MLP: a single intra-op thread minimises latency and avoids thread-pool
        # spin-up cost on the Pi's modest cores. Tune if profiling says otherwise.
        opts.intra_op_num_threads = max(1, int(intra_op_threads))
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

        self.session = ort.InferenceSession(
            model_path, sess_options=opts, providers=providers or ["CPUExecutionProvider"]
        )
        self.model_path = model_path
        self._in = self.session.get_inputs()[0].name
        self._out = self.session.get_outputs()[0].name

        in_shape = self.session.get_inputs()[0].shape
        out_shape = self.session.get_outputs()[0].shape
        if in_shape[-1] != OBS_DIM or out_shape[-1] != ACT_DIM:
            raise ValueError(
                f"policy IO mismatch: input {in_shape} (expect [*, {OBS_DIM}]), "
                f"output {out_shape} (expect [*, {ACT_DIM}])"
            )
        self._buf = np.zeros((1, OBS_DIM), dtype=np.float32)

    def build_observation(self, state: MotionState, command: tuple[float, float]) -> np.ndarray:
        """Assemble the (1, 9) float32 observation in env._obs() order/normalisation."""
        v_cmd, w_cmd = command
        b = self._buf
        b[0, 0] = state.forward_velocity / V_MAX
        b[0, 1] = state.lateral_velocity / V_MAX
        b[0, 2] = state.yaw_rate / W_MAX
        b[0, 3] = state.roll
        b[0, 4] = state.pitch
        b[0, 5] = state.wheel_speed_left / NO_LOAD_WHEEL
        b[0, 6] = state.wheel_speed_right / NO_LOAD_WHEEL
        b[0, 7] = v_cmd / V_MAX
        b[0, 8] = w_cmd / W_MAX
        return b

    def step(self, state: MotionState, command: tuple[float, float]) -> tuple[float, float]:
        """Run one inference. Returns (left, right) motor effort in [-1, 1]."""
        obs = self.build_observation(state, command)
        action = self.session.run([self._out], {self._in: obs})[0][0]
        left = float(np.clip(action[0], -1.0, 1.0))
        right = float(np.clip(action[1], -1.0, 1.0))
        return left, right


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("model", help="path to a locomotion_*.onnx policy")
    args = ap.parse_args()
    pol = LocomotionPolicy(args.model)
    l, r = pol.step(MotionState(), command_from_intent("move", {"speed": 1.0}))
    print(f"loaded {args.model}; full-forward -> left={l:.3f} right={r:.3f}")
