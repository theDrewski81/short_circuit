"""Gymnasium environment for the Johnny 5 tread chassis (command-conditioned).

A single policy learns every Phase 02 behaviour -- drive forward/backward, turn
in place left/right, arc-turn, and hold still -- by receiving the desired
(forward speed, yaw rate) command as part of its observation. This generalises
better than one policy per behaviour and matches the deployment story: the
high-level intent (direction + magnitude) is the command, the policy outputs
left/right motor effort.

Control runs at 50 Hz (CONTROL_DT), matching the Pi-M motion-loop tick. Each
control step advances the 500 Hz MuJoCo physics by FRAME_SKIP substeps.
"""

from __future__ import annotations

import os

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as exc:  # pragma: no cover
    raise ImportError("gymnasium is required: pip install gymnasium") from exc

import mujoco

_HERE = os.path.dirname(os.path.abspath(__file__))
_MODEL = os.path.join(_HERE, "johnny5_chassis.xml")

# Command envelope (physically reachable on this chassis -- see TUNING.md).
V_MAX = 0.28          # m/s  forward/backward command ceiling (cap ~0.30)
W_MAX = 0.30          # rad/s yaw command ceiling (in-place skid-steer max ~0.34)
NO_LOAD_WHEEL = 12.9  # rad/s, for normalising encoder-velocity observations

CONTROL_DT = 0.02     # 50 Hz control
PHYSICS_DT = 0.002    # must match the MJCF <option timestep>
FRAME_SKIP = int(round(CONTROL_DT / PHYSICS_DT))

TIP_LIMIT = 0.8       # rad (~46 deg) roll/pitch -> episode terminates (tipped)
EPISODE_SECONDS = 8.0


def _quat_to_rpy(q: np.ndarray) -> tuple[float, float, float]:
    """MuJoCo (w, x, y, z) quaternion -> roll, pitch, yaw in radians."""
    w, x, y, z = q
    roll = np.arctan2(2 * (w * x + y * z), 1 - 2 * (x * x + y * y))
    pitch = np.arcsin(np.clip(2 * (w * y - z * x), -1.0, 1.0))
    yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
    return float(roll), float(pitch), float(yaw)


class JohnnyChassisEnv(gym.Env):
    """Differential-drive tread chassis. Action = [left, right] motor effort in [-1, 1]."""

    metadata = {"render_modes": ["rgb_array"], "render_fps": 50}

    def __init__(
        self,
        *,
        # reward weights (overridable from config.yaml in train.py)
        w_vel: float = 1.0,
        w_yaw: float = 1.0,
        w_energy: float = 0.01,
        w_stability: float = 0.5,
        w_lateral: float = 0.2,
        k_vel: float = 50.0,
        k_yaw: float = 30.0,
        command_hold: bool = True,
        render_mode: str | None = None,
    ):
        super().__init__()
        self.model = mujoco.MjModel.from_xml_path(_MODEL)
        self.data = mujoco.MjData(self.model)
        self.render_mode = render_mode

        # left/right command -> the two wheels on each side
        self._act = {
            n: mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, n)
            for n in ("motor_rl", "motor_fl", "motor_rr", "motor_fr")
        }
        self._left_acts = (self._act["motor_rl"], self._act["motor_fl"])
        self._right_acts = (self._act["motor_rr"], self._act["motor_fr"])

        self.w_vel, self.w_yaw = w_vel, w_yaw
        self.w_energy, self.w_stability, self.w_lateral = w_energy, w_stability, w_lateral
        self.k_vel, self.k_yaw = k_vel, k_yaw
        self.command_hold = command_hold

        self._max_steps = int(round(EPISODE_SECONDS / CONTROL_DT))
        self._step_count = 0
        self._command = np.zeros(2, dtype=np.float32)  # [v_cmd, w_cmd]

        # obs: v_fwd, v_lat, yaw_rate, roll, pitch, wl, wr, v_cmd, w_cmd (all normalised-ish)
        high = np.full(9, np.inf, dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(2,), dtype=np.float32)

    # -- sensor helpers --------------------------------------------------
    def _sensor(self, name: str) -> np.ndarray:
        return self.data.sensor(name).data

    def _sample_command(self, rng: np.random.Generator) -> np.ndarray:
        mode = rng.choice(["forward", "backward", "spin_left", "spin_right", "arc", "stop"])
        v, w = 0.0, 0.0
        if mode == "forward":
            v = rng.uniform(0.4, 1.0) * V_MAX
        elif mode == "backward":
            v = -rng.uniform(0.4, 1.0) * V_MAX
        elif mode == "spin_left":
            w = rng.uniform(0.5, 1.0) * W_MAX
        elif mode == "spin_right":
            w = -rng.uniform(0.5, 1.0) * W_MAX
        elif mode == "arc":
            v = rng.choice([-1, 1]) * rng.uniform(0.3, 0.7) * V_MAX
            w = rng.choice([-1, 1]) * rng.uniform(0.3, 0.7) * W_MAX
        return np.array([v, w], dtype=np.float32)

    def _obs(self) -> np.ndarray:
        v_world = self._sensor("trunk_linvel")          # world-frame linear velocity
        _, _, yaw = _quat_to_rpy(self._sensor("trunk_quat"))
        # rotate world velocity into the body frame to get forward / lateral
        cy, sy = np.cos(yaw), np.sin(yaw)
        v_fwd = cy * v_world[0] + sy * v_world[1]
        v_lat = -sy * v_world[0] + cy * v_world[1]
        yaw_rate = self._sensor("imu_gyro")[2]
        roll, pitch, _ = _quat_to_rpy(self._sensor("trunk_quat"))
        wl = self._sensor("enc_rl_vel")[0]
        wr = self._sensor("enc_rr_vel")[0]
        v_cmd, w_cmd = self._command
        return np.array([
            v_fwd / V_MAX, v_lat / V_MAX, yaw_rate / W_MAX,
            roll, pitch,
            wl / NO_LOAD_WHEEL, wr / NO_LOAD_WHEEL,
            v_cmd / V_MAX, w_cmd / W_MAX,
        ], dtype=np.float32)

    # -- gym API ---------------------------------------------------------
    def reset(self, *, seed: int | None = None, options: dict | None = None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        # small random initial heading so the policy can't memorise a fixed frame
        yaw0 = self.np_random.uniform(-np.pi, np.pi)
        self.data.qpos[3:7] = [np.cos(yaw0 / 2), 0, 0, np.sin(yaw0 / 2)]
        mujoco.mj_forward(self.model, self.data)
        self._command = self._sample_command(self.np_random)
        self._step_count = 0
        return self._obs(), {}

    def step(self, action: np.ndarray):
        action = np.clip(action, -1.0, 1.0).astype(np.float64)
        for a in self._left_acts:
            self.data.ctrl[a] = action[0]
        for a in self._right_acts:
            self.data.ctrl[a] = action[1]
        for _ in range(FRAME_SKIP):
            mujoco.mj_step(self.model, self.data)
        self._step_count += 1

        obs = self._obs()
        v_fwd = obs[0] * V_MAX
        v_lat = obs[1] * V_MAX
        yaw_rate = obs[2] * W_MAX
        roll, pitch = float(obs[3]), float(obs[4])
        v_cmd, w_cmd = self._command

        r_vel = self.w_vel * np.exp(-self.k_vel * (v_fwd - v_cmd) ** 2)
        r_yaw = self.w_yaw * np.exp(-self.k_yaw * (yaw_rate - w_cmd) ** 2)
        r_energy = self.w_energy * float(np.mean(action ** 2))
        r_stab = self.w_stability * (roll * roll + pitch * pitch)
        r_lat = self.w_lateral * (v_lat * v_lat)
        reward = r_vel + r_yaw - r_energy - r_stab - r_lat

        terminated = abs(roll) > TIP_LIMIT or abs(pitch) > TIP_LIMIT
        if terminated:
            reward -= 10.0
        truncated = self._step_count >= self._max_steps

        # optionally switch command mid-episode to train transitions
        if self.command_hold is False and self._step_count % 150 == 0:
            self._command = self._sample_command(self.np_random)

        info = {
            "v_cmd": float(v_cmd), "w_cmd": float(w_cmd),
            "v_fwd": float(v_fwd), "yaw_rate": float(yaw_rate),
            "r_vel": float(r_vel), "r_yaw": float(r_yaw),
        }
        return obs, float(reward), bool(terminated), bool(truncated), info


if __name__ == "__main__":
    env = JohnnyChassisEnv()
    o, _ = env.reset(seed=0)
    print("obs dim:", o.shape, "action dim:", env.action_space.shape)
