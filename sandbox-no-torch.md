---
name: sandbox-no-torch
description: "Cowork sandbox can't install PyTorch/SB3; ML training runs on the home lab"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 96ed427c-693a-499e-93b3-192875b51b0f
---

In the Johnny 5 Cowork sandbox, PyTorch and Stable-Baselines3 cannot be installed: the network proxy 403-blocks the PyTorch CPU wheel index (download.pytorch.org) and stalls the large CUDA wheels from PyPI (cudnn download hangs, pip cache stays static). The default PyPI `torch` is the CUDA build and hard-fails import without the nvidia libs (`libcublasLt.so not found`).

What DOES install fine via pip (`--break-system-packages`): mujoco, gymnasium, numpy, onnx, onnxruntime, pyyaml.

Implication: any PPO/RL training that needs torch must run on Andrew's home lab (RTX 3080), not in the sandbox. To de-risk a training pipeline in-sandbox without torch, use a numpy-only check — e.g. a CEM trainer over a small MLP to confirm the env/reward is learnable, plus hand-built ONNX (via onnx.helper) verified on onnxruntime for the deployment path. See [[johnny5-phase02-locomotion]].
