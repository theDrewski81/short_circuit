# Training Runbook — Johnny 5 Locomotion Policy (Native Windows, CPU)

Step-by-step guide to train the Phase 02 locomotion policy on the RTX 3080
**desktop**, running natively on Windows with **CPU only**. We use CPU on
purpose: the policy is a tiny 2×64 MLP, so the GPU gives no real speed-up and
the CPU↔GPU round-trip can even slow it down — and skipping CUDA/cuDNN removes
the most failure-prone part of the setup. The 3080 stays free for your LLM
routing.

Throughput here is bound by MuJoCo physics stepping across CPU cores, so the
plan is: one clean virtual environment, then **four staged runs** (each one
proves the layer below it works) before the full 3-million-step job.

**Conventions in this guide**
- All commands are for **PowerShell**. Open it as your normal user (admin not
  required).
- Paths contain spaces, so they are always quoted. Copy them whole.
- After most steps there is an **Expect:** line — if you see that, move on; if
  not, jump to Troubleshooting at the bottom.
- The project lives at
  `C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5`. The training
  code is in its `simulation\chassis` subfolder.

Estimated hands-on time: ~15 minutes of setup, then the full run is unattended
(~15–45 minutes depending on core count).

---

## Step 1 — Install Python 3.12

If you already have Python 3.11 or 3.12, skip to Step 2 (check with `py -0p`).

1. Download the **Windows installer (64-bit)** for Python 3.12 from
   <https://www.python.org/downloads/windows/>. Use python.org, **not** the
   Microsoft Store build (the Store build sandboxes paths and breaks venvs).
2. Run it. On the first screen tick **“Add python.exe to PATH”**, then
   **Install Now**.
3. Open a **new** PowerShell window and confirm:

   ```powershell
   py -3.12 --version
   ```

   **Expect:** `Python 3.12.x`

---

## Step 2 — Create the virtual environment (OUTSIDE the Nextcloud folder)

Put the venv **outside the Nextcloud-synced filesystem** so its ~1–2 GB of
packages never sync to the cloud. The target path `C:\Johnny5\` is a plain local
folder — it is **not** under `...\Nextcloud\...`, and that is intentional.

```powershell
py -3.12 -m venv C:\Johnny5\train-venv
```

> Do **not** create the venv inside the project folder (the one under
> `...\Nextcloud\...`), or Nextcloud will try to sync the whole toolchain.

Activate it:

```powershell
& C:\Johnny5\train-venv\Scripts\Activate.ps1
```

**Expect:** your prompt is now prefixed with `(train-venv)`.

> If you get a red error about scripts being disabled, run this once in the
> same window, then re-run the activate line:
>
> ```powershell
> Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
> ```

Upgrade pip inside the venv:

```powershell
python -m pip install --upgrade pip
```

---

## Step 3 — Install the training dependencies

Keep the venv active (you should still see `(train-venv)`), then:

```powershell
pip install -r "C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5\simulation\chassis\requirements-train.txt"
```

This pulls MuJoCo, Gymnasium, Stable-Baselines3, the **CPU** build of PyTorch,
ONNX/onnxruntime, and TensorBoard. It downloads a few hundred MB and takes a
couple of minutes.

**Expect:** a final `Successfully installed ...` line with no red errors.

---

## Step 4 — Verify the install

```powershell
python -c "import torch, stable_baselines3, gymnasium, mujoco, onnxruntime; print('torch', torch.__version__, '| cuda', torch.cuda.is_available()); print('sb3', stable_baselines3.__version__, '| gym', gymnasium.__version__, '| mujoco', mujoco.__version__)"
```

**Expect:** versions print, and **`cuda False`** — that confirms the CPU build
(this is intended, not a problem).

---

## Step 5 — Move into the training folder (INSIDE the Nextcloud folder)

The training code lives **inside the Nextcloud-synced project** — this is the
opposite of the venv in Step 2. The `simulation\chassis` directory is under
`...\Nextcloud\...`, which is correct: the code stays synced and version-
controlled there. Every command from here runs from that directory:

```powershell
cd "C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5\simulation\chassis"
```

> Quick orientation: **venv → `C:\Johnny5\` (outside Nextcloud)**; **code +
> training runs → `...\Nextcloud\...\simulation\chassis` (inside Nextcloud)**.

---

## Step 6 — Stage 1: torch-free environment check

This runs the same numpy-only check used to validate the env in the sandbox. It
proves MuJoCo physics and the reward are healthy before SB3 is involved.

```powershell
python cem_smoke.py
```

**Expect (last lines):**
- `LEARNABILITY: ... PASS`
- `ONNX ROUND-TRIP: ... PASS`

It finishes in well under a minute.

---

## Step 7 — Stage 2: single-process smoke train

A tiny 50k-step PPO run in **one process** (`--no-subproc`). This validates the
full Stable-Baselines3 path with the least that can go wrong.

```powershell
python train.py --smoke --no-subproc
```

**Expect:** SB3 prints a rollout/training table, then
`saved model -> ...runs\locomotion_v1\model.zip`. Takes ~1–2 minutes.

---

## Step 8 — Stage 3: multi-process smoke train

Same tiny run, but now using `SubprocVecEnv` (multiple worker processes). This
specifically validates Windows multiprocessing before the long run.

```powershell
python train.py --smoke
```

**Expect:** same successful finish. If this hangs or errors where Step 7
succeeded, it is a Windows multiprocessing issue — see Troubleshooting; you can
fall back to `--no-subproc` for the full run (slower but reliable).

---

## Step 9 — Find your physical core count

```powershell
(Get-CimInstance Win32_Processor).NumberOfCores
```

Note this number (e.g. `8`). Use an **even** number for `--n-envs`; if the
result is odd, drop it by one (the config’s batch size assumes an even env
count).

---

## Step 10 — Stage 4: the full training run

Replace `<cores>` with the number from Step 9:

```powershell
python train.py --config config.yaml --n-envs <cores> --device cpu
```

This trains the real policy for 3,000,000 steps (the default in `config.yaml`)
across all four behaviours plus stop. Leave it running.

**Expect:**
- A live table where `rollout/ep_rew_mean` trends **upward** over time.
- Periodic `Eval num_timesteps=...` lines (every ~50k steps).
- At the end:
  `saved model -> ...runs\locomotion_v1\model.zip` and
  `saved vecnormalize -> ...runs\locomotion_v1\vecnormalize.pkl`.

Runtime is roughly 15–45 minutes depending on core count.

> **Tip:** to re-run without overwriting the previous result, add
> `--run-name locomotion_v2` (output goes to `runs\locomotion_v2`).

---

## Step 11 — (Optional) Watch progress live

In a **second** PowerShell window, activate the same venv and launch
TensorBoard:

```powershell
& C:\Johnny5\train-venv\Scripts\Activate.ps1
cd "C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5\simulation\chassis"
tensorboard --logdir runs
```

Open the printed URL (usually <http://localhost:6006>). Watch
`rollout/ep_rew_mean` and `eval/mean_reward` climb.

---

## Step 12 — Export the policy to ONNX

After training finishes:

```powershell
python export_onnx.py --run locomotion_v1
```

This bakes the observation-normalisation stats into the graph and writes the
deployable file.

**Expect:**
- `exported -> ...\policies\locomotion_v1.onnx`
- `onnxruntime vs torch max abs err: ...e-0x  (OK)`
- `action range over random obs: [-1.000, 1.000]` (roughly)

The `policies\locomotion_v1.onnx` file is the artifact that gets deployed to
Pi-M in Task 5.

---

## Step 13 — Hand-off / commit (you, not the agent)

`runs\` is git-ignored (training output is disposable); the policy file and any
doc changes are what get committed.

```powershell
cd "C:\Users\apsus\Nextcloud\Documents\VS Code\Johnny5\Johnny 5"
git add policies/locomotion_v1.onnx simulation/chassis CLAUDE.md
git commit -m "sim: train locomotion policy v1 and export to ONNX"
git push
```

(If `git add` complains about `runs/`, it is correctly ignored — nothing to do.)

---

## Troubleshooting (common Windows snags)

**`Activate.ps1 cannot be loaded because running scripts is disabled`**
Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that window,
then re-run the activate command. (Process scope only affects that window.)

**`py` is not recognised**
Python isn’t on PATH. Re-run the installer and tick “Add python.exe to PATH”, or
use the full path to `python.exe`. As a fallback, `python` may work in place of
`py -3.12`.

**pip starts downloading huge `nvidia-*` / CUDA packages**
You somehow got the CUDA build. Force CPU:
```powershell
pip uninstall -y torch
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

**`train.py --smoke` (Step 8) hangs or errors but Step 7 worked**
A Windows `spawn` multiprocessing issue. Always launch as `python train.py ...`
(never paste the code into an interactive Python prompt). If it persists, run the
full job with `--no-subproc` — single process, slower, but rock-solid.

**A Gymnasium / Stable-Baselines3 version conflict on import**
Pin the known-good pair, then retry:
```powershell
pip install "stable-baselines3==2.4.0" "gymnasium==1.0.0"
```

**`numpy` 2.x error from a dependency**
```powershell
pip install "numpy<3"
```

**Paths fail / “cannot find path”**
A quote is missing. Every path with spaces (`VS Code`, `Johnny 5`) must be in
double quotes.

---

## Appendix — what gets created, and where

Inside `simulation\chassis\runs\locomotion_v1\` (git-ignored, not synced-critical):
- `model.zip` — final PPO model
- `best\best_model.zip` — best model by evaluation reward
- `vecnormalize.pkl` — observation-normalisation stats (needed for ONNX export)
- `checkpoints\` — periodic snapshots
- `tb\` — TensorBoard logs

At the repo root:
- `policies\locomotion_v1.onnx` — **the deployable policy** for Pi-M (Task 5)

The virtual environment lives at `C:\Johnny5\train-venv\` — outside the project,
so it never syncs. Delete that folder to remove the whole toolchain later.
