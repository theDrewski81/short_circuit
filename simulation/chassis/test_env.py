"""Stability + sanity checks for JohnnyChassisEnv before any training."""
from __future__ import annotations
import numpy as np
from env import JohnnyChassisEnv, V_MAX, W_MAX

def random_rollouts(n_ep=20, seed=0):
    env = JohnnyChassisEnv()
    rng = np.random.default_rng(seed)
    bad = 0; rewards=[]; max_speed=0.0; max_tilt=0.0; terms=0
    for ep in range(n_ep):
        o,_ = env.reset(seed=int(rng.integers(1e9)))
        ep_r=0.0
        for t in range(env._max_steps):
            a = rng.uniform(-1,1,size=2).astype(np.float32)
            o,r,term,trunc,info = env.step(a)
            ep_r+=r
            if not np.all(np.isfinite(o)) or not np.all(np.isfinite(env.data.qpos)) or not np.all(np.isfinite(env.data.qvel)):
                bad+=1; break
            max_speed=max(max_speed, abs(info['v_fwd']))
            max_tilt=max(max_tilt, abs(o[3]), abs(o[4]))
            if term: terms+=1; break
            if trunc: break
        rewards.append(ep_r)
    print(f"random: {n_ep} eps | NaN/inf eps={bad} | tip-terminations={terms}")
    print(f"        mean ep reward={np.mean(rewards):.1f} | max|vfwd|={max_speed:.3f} m/s | max tilt={np.degrees(max_tilt):.1f} deg")
    return bad==0

def scripted_controller(v_cmd, w_cmd):
    # crude differential feed-forward: normalise command to wheel effort
    base = v_cmd / V_MAX
    diff = w_cmd / W_MAX
    return np.clip(np.array([base - diff, base + diff], dtype=np.float32), -1, 1)

def scripted_rollouts(n_ep=12, seed=1):
    env = JohnnyChassisEnv()
    rng = np.random.default_rng(seed)
    rewards=[]; tracking=[]
    for ep in range(n_ep):
        o,_ = env.reset(seed=int(rng.integers(1e9)))
        vc,wc = env._command
        ep_r=0.0; vfwds=[]; yaws=[]
        for t in range(env._max_steps):
            a = scripted_controller(vc,wc)
            o,r,term,trunc,info = env.step(a)
            ep_r+=r; vfwds.append(info['v_fwd']); yaws.append(info['yaw_rate'])
            if term or trunc: break
        rewards.append(ep_r)
        tracking.append((vc, np.mean(vfwds[-100:]), wc, np.mean(yaws[-100:])))
    print(f"scripted: mean ep reward={np.mean(rewards):.1f} (should exceed random)")
    print("  sample command vs achieved (v_cmd, v_ach, w_cmd, w_ach):")
    for vc,va,wc,wa in tracking[:6]:
        print(f"    v {vc:+.3f} -> {va:+.3f} m/s   w {wc:+.3f} -> {wa:+.3f} rad/s")
    return np.mean(rewards)

if __name__ == "__main__":
    ok = random_rollouts()
    sr = scripted_rollouts()
    print("\nSTABILITY:", "PASS" if ok else "FAIL")
