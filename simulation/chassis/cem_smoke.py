"""Torch-free smoke test of the locomotion pipeline.

SB3/PyTorch cannot be installed in this sandbox (the proxy blocks the CPU wheel
index and stalls the CUDA wheels), so the real PPO run happens on the home lab.
This still validates the two things that matter before committing GPU time:

  1. The env + reward are LEARNABLE -- a small MLP trained by CEM (cross-entropy
     method, gradient-free, numpy-only) climbs well above the random baseline.
  2. The ONNX DEPLOYMENT path works -- the trained MLP is exported to an ONNX
     graph with the exact Pi contract (raw obs in -> [-1,1] action out, obs
     normalisation baked in), and onnxruntime reproduces the numpy forward and
     runs fast.

The production policy is a 2x64 MLP (config.yaml); this smoke net is 1x16 so CEM
converges in seconds. Architecture aside, the IO contract and runtime are identical.
"""
from __future__ import annotations
import os, time, numpy as np
from env import JohnnyChassisEnv

IN, H, OUT = 9, 16, 2
rng = np.random.default_rng(0)

def unpack(theta):
    i = 0
    W1 = theta[i:i+IN*H].reshape(IN, H); i += IN*H
    b1 = theta[i:i+H]; i += H
    W2 = theta[i:i+H*OUT].reshape(H, OUT); i += H*OUT
    b2 = theta[i:i+OUT]; i += OUT
    return W1, b1, W2, b2

NPARAMS = IN*H + H + H*OUT + OUT

def policy_action(theta, obs):
    W1, b1, W2, b2 = unpack(theta)
    h = np.tanh(obs @ W1 + b1)
    return np.tanh(h @ W2 + b2)

def episode_return(env, theta, seed):
    o, _ = env.reset(seed=seed)
    total = 0.0
    for _ in range(env._max_steps):
        a = policy_action(theta, o).astype(np.float32)
        o, r, term, trunc, _ = env.step(a)
        total += r
        if term or trunc:
            break
    return total

def evaluate(env, theta, seeds):
    return float(np.mean([episode_return(env, theta, s) for s in seeds]))

def cem(env, iters=7, pop=18, elite=5, sigma0=0.6, eval_seeds=(1,2,3,4)):
    mu = np.zeros(NPARAMS); sigma = np.full(NPARAMS, sigma0)
    base = evaluate(env, mu, eval_seeds)
    print(f"baseline (zero policy) mean return over {len(eval_seeds)} cmds: {base:.1f}", flush=True)
    best_theta, best_score = mu.copy(), base
    for it in range(iters):
        samples = mu + sigma * rng.standard_normal((pop, NPARAMS))
        scores = np.array([evaluate(env, s, eval_seeds) for s in samples])
        idx = scores.argsort()[::-1][:elite]
        elites = samples[idx]
        mu = elites.mean(axis=0)
        sigma = elites.std(axis=0) + 1e-3
        it_best = scores[idx[0]]
        if it_best > best_score:
            best_score, best_theta = it_best, samples[idx[0]].copy()
        print(f"  iter {it+1}/{iters}: elite-best={it_best:.1f}  pop-mean={scores.mean():.1f}", flush=True)
    return best_theta, base, best_score

def export_onnx(theta, path, obs_mean, obs_std):
    import onnx
    from onnx import helper, TensorProto, numpy_helper as nh
    W1, b1, W2, b2 = unpack(theta)
    inits = [
        nh.from_array(obs_mean.astype(np.float32), "mean"),
        nh.from_array(obs_std.astype(np.float32), "std"),
        nh.from_array(W1.astype(np.float32), "W1"), nh.from_array(b1.astype(np.float32), "b1"),
        nh.from_array(W2.astype(np.float32), "W2"), nh.from_array(b2.astype(np.float32), "b2"),
        nh.from_array(np.array(-10, np.float32), "lo10"), nh.from_array(np.array(10, np.float32), "hi10"),
    ]
    n = [
        helper.make_node("Sub", ["observation", "mean"], ["c"]),
        helper.make_node("Div", ["c", "std"], ["n0"]),
        helper.make_node("Clip", ["n0", "lo10", "hi10"], ["n"]),
        helper.make_node("Gemm", ["n", "W1", "b1"], ["z1"]),
        helper.make_node("Tanh", ["z1"], ["h1"]),
        helper.make_node("Gemm", ["h1", "W2", "b2"], ["z2"]),
        helper.make_node("Tanh", ["z2"], ["action"]),
    ]
    g = helper.make_graph(n, "j5_locomotion_smoke", [
        helper.make_tensor_value_info("observation", TensorProto.FLOAT, ["batch", IN])],
        [helper.make_tensor_value_info("action", TensorProto.FLOAT, ["batch", OUT])], inits)
    m = helper.make_model(g, opset_imports=[helper.make_opsetid("", 17)])
    m.ir_version = 10
    onnx.checker.check_model(m)
    onnx.save(m, path)

if __name__ == "__main__":
    env = JohnnyChassisEnv(); env._max_steps = 150
    t0 = time.time()
    theta, base, best = cem(env)
    rand_seeds = (101, 202, 303, 404)
    rand_score = np.mean([episode_return(env, rng.standard_normal(NPARAMS)*0.6, s) for s in rand_seeds])
    print(f"\nLEARNABILITY: random-init MLP {rand_score:.1f}  ->  CEM-trained {best:.1f}  "
          f"({'PASS' if best > rand_score + 30 else 'WEAK'})  [{time.time()-t0:.0f}s]", flush=True)

    out_dir = os.path.join(os.path.dirname(__file__), "smoke_run"); os.makedirs(out_dir, exist_ok=True)
    np.save(os.path.join(out_dir, "smoke_policy.npy"), theta)
    onnx_path = os.path.join(out_dir, "locomotion_smoke.onnx")
    mean = np.zeros(IN, np.float32); std = np.ones(IN, np.float32)  # env obs already ~normalised
    export_onnx(theta, onnx_path, mean, std)

    import onnxruntime as ort
    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    obs = rng.standard_normal((128, IN)).astype(np.float32)
    ref = np.stack([policy_action(theta, o) for o in obs]).astype(np.float32)
    got = sess.run(["action"], {"observation": obs})[0]
    err = float(np.max(np.abs(ref - got)))
    # single-sample latency
    one = obs[:1]; N = 2000; tl = time.time()
    for _ in range(N): sess.run(["action"], {"observation": one})
    lat_ms = (time.time() - tl) / N * 1000
    print(f"ONNX ROUND-TRIP: onnxruntime vs numpy max abs err {err:.2e}  "
          f"({'PASS' if err < 1e-5 else 'FAIL'})")
    print(f"ONNX inference latency (x86 sandbox, single obs): {lat_ms:.3f} ms/step  "
          f"action range [{got.min():.2f},{got.max():.2f}]")
    print(f"saved: {onnx_path}")
