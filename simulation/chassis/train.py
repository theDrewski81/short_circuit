"""PPO locomotion training for the Johnny 5 tread chassis.

Trains a single command-conditioned policy (forward / backward / turn-in-place /
arc / stop) on the home-lab GPU. The Pi Zero 2 W never runs training -- it loads
the exported ONNX policy (see export_onnx.py).

    # full run (home lab)
    python3 train.py --config config.yaml
    # quick local smoke test (CPU, ~50k steps)
    python3 train.py --smoke

Outputs under <run_dir>/<model_name>/:
    model.zip            final PPO model
    best/best_model.zip  best model by eval reward
    vecnormalize.pkl     observation-normalisation stats (needed for ONNX export)
    checkpoints/         periodic snapshots
    tb/                  TensorBoard logs
"""

from __future__ import annotations

import argparse
import os

import yaml

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, EvalCallback
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv, VecNormalize

from env import JohnnyChassisEnv

_HERE = os.path.dirname(os.path.abspath(__file__))


def make_env(reward_cfg: dict, command_hold: bool, seed: int):
    def _init():
        env = JohnnyChassisEnv(command_hold=command_hold, **reward_cfg)
        env.reset(seed=seed)
        return env
    return _init


def build_vecenv(cfg: dict, n_envs: int, seed: int, subproc: bool):
    reward_cfg = cfg["env"]["reward"]
    hold = cfg["env"]["command_hold"]
    fns = [make_env(reward_cfg, hold, seed + i) for i in range(n_envs)]
    venv = SubprocVecEnv(fns) if (subproc and n_envs > 1) else DummyVecEnv(fns)
    return VecNormalize(
        venv,
        norm_obs=cfg["train"]["normalize_obs"],
        norm_reward=cfg["train"]["normalize_reward"],
        clip_obs=10.0,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=os.path.join(_HERE, "config.yaml"))
    ap.add_argument("--timesteps", type=int, default=None, help="override total_timesteps")
    ap.add_argument("--n-envs", type=int, default=None, help="override env.n_envs")
    ap.add_argument("--device", default=None, help="override train.device")
    ap.add_argument("--run-name", default=None, help="override paths.model_name")
    ap.add_argument("--no-subproc", action="store_true", help="use DummyVecEnv (debug)")
    ap.add_argument("--smoke", action="store_true", help="tiny CPU run to validate the pipeline")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config))
    p, t = cfg["ppo"], cfg["train"]

    if args.smoke:
        cfg["env"]["n_envs"] = 4
        t["total_timesteps"] = 50_000
        t["eval_freq"] = 10_000
        t["checkpoint_freq"] = 25_000
        t["device"] = "cpu"
        p["batch_size"] = 2048  # 4 envs * 2048 steps = 8192 buffer

    n_envs = args.n_envs or cfg["env"]["n_envs"]
    total_timesteps = args.timesteps or t["total_timesteps"]
    device = args.device or t["device"]
    model_name = args.run_name or cfg["paths"]["model_name"]
    seed = t["seed"]

    out = os.path.join(_HERE, cfg["paths"]["run_dir"], model_name)
    os.makedirs(out, exist_ok=True)

    train_env = build_vecenv(cfg, n_envs, seed, subproc=not args.no_subproc)
    eval_env = build_vecenv(cfg, 1, seed + 9999, subproc=False)
    eval_env.training = False
    eval_env.norm_reward = False

    eval_cb = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(out, "best"),
        log_path=os.path.join(out, "eval"),
        eval_freq=max(t["eval_freq"] // n_envs, 1),
        n_eval_episodes=t["n_eval_episodes"],
        deterministic=True,
    )
    ckpt_cb = CheckpointCallback(
        save_freq=max(t["checkpoint_freq"] // n_envs, 1),
        save_path=os.path.join(out, "checkpoints"),
        name_prefix="ppo",
    )

    model = PPO(
        "MlpPolicy",
        train_env,
        policy_kwargs=dict(net_arch=p["net_arch"]),
        learning_rate=p["learning_rate"],
        n_steps=p["n_steps"],
        batch_size=p["batch_size"],
        n_epochs=p["n_epochs"],
        gamma=p["gamma"],
        gae_lambda=p["gae_lambda"],
        clip_range=p["clip_range"],
        ent_coef=p["ent_coef"],
        vf_coef=p["vf_coef"],
        max_grad_norm=p["max_grad_norm"],
        tensorboard_log=os.path.join(out, "tb"),
        device=device,
        seed=seed,
        verbose=1,
    )

    model.learn(total_timesteps=total_timesteps, callback=[eval_cb, ckpt_cb], progress_bar=False)

    model.save(os.path.join(out, "model"))
    train_env.save(os.path.join(out, "vecnormalize.pkl"))
    print(f"\nsaved model -> {os.path.join(out, 'model.zip')}")
    print(f"saved vecnormalize -> {os.path.join(out, 'vecnormalize.pkl')}")
    print("next: python3 export_onnx.py --run", model_name)


if __name__ == "__main__":
    main()
