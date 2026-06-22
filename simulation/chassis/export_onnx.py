"""Export a trained PPO policy to ONNX for onnxruntime on Pi-M.

The deployed function must be self-contained: raw observation in, motor command
out. VecNormalize lives in the training env, not the policy, so its observation
mean/variance are baked into the exported graph here. The result takes a raw
9-vector observation and returns the deterministic [left, right] action, clipped
to [-1, 1] exactly as SB3 `predict(deterministic=True)` would.

    python3 export_onnx.py --run locomotion_v1
    # -> policies/locomotion_v1.onnx  (repo-root /policies)
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import torch
import torch.nn as nn

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import VecNormalize

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.normpath(os.path.join(_HERE, "..", ".."))


class DeployPolicy(nn.Module):
    """raw obs -> normalise (frozen VecNormalize stats) -> actor MLP -> clip."""

    def __init__(self, policy, obs_mean, obs_var, clip_obs=10.0, eps=1e-8):
        super().__init__()
        self.policy = policy
        self.register_buffer("mean", torch.as_tensor(obs_mean, dtype=torch.float32))
        self.register_buffer("var", torch.as_tensor(obs_var, dtype=torch.float32))
        self.clip_obs = float(clip_obs)
        self.eps = float(eps)

    def forward(self, obs: torch.Tensor) -> torch.Tensor:
        norm = (obs - self.mean) / torch.sqrt(self.var + self.eps)
        norm = torch.clamp(norm, -self.clip_obs, self.clip_obs)
        latent_pi = self.policy.mlp_extractor.forward_actor(norm)
        action = self.policy.action_net(latent_pi)
        return torch.clamp(action, -1.0, 1.0)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="locomotion_v1", help="run/model name under runs/")
    ap.add_argument("--out", default=None, help="output .onnx path")
    args = ap.parse_args()

    run_dir = os.path.join(_HERE, "runs", args.run)
    model_path = os.path.join(run_dir, "model.zip")
    vecnorm_path = os.path.join(run_dir, "vecnormalize.pkl")
    out_path = args.out or os.path.join(_REPO, "policies", f"{args.run}.onnx")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    model = PPO.load(model_path, device="cpu")
    vec = VecNormalize.load(vecnorm_path, venv=None) if os.path.exists(vecnorm_path) else None
    obs_dim = model.observation_space.shape[0]
    if vec is not None and vec.norm_obs:
        mean, var = vec.obs_rms.mean, vec.obs_rms.var
    else:
        mean, var = np.zeros(obs_dim), np.ones(obs_dim)

    policy = model.policy.eval()
    wrapper = DeployPolicy(policy, mean, var).eval()

    dummy = torch.zeros(1, obs_dim, dtype=torch.float32)
    torch.onnx.export(
        wrapper, dummy, out_path,
        input_names=["observation"], output_names=["action"],
        dynamic_axes={"observation": {0: "batch"}, "action": {0: "batch"}},
        opset_version=17,
    )
    print(f"exported -> {out_path}")

    # verify: onnxruntime output matches the torch wrapper on random raw obs
    import onnxruntime as ort
    sess = ort.InferenceSession(out_path, providers=["CPUExecutionProvider"])
    rng = np.random.default_rng(0)
    obs = rng.normal(size=(64, obs_dim)).astype(np.float32)
    with torch.no_grad():
        ref = wrapper(torch.as_tensor(obs)).numpy()
    got = sess.run(["action"], {"observation": obs})[0]
    max_err = float(np.max(np.abs(ref - got)))
    print(f"onnxruntime vs torch max abs err: {max_err:.2e}  ({'OK' if max_err < 1e-5 else 'MISMATCH'})")
    print(f"action range over random obs: [{got.min():.3f}, {got.max():.3f}]")


if __name__ == "__main__":
    main()
