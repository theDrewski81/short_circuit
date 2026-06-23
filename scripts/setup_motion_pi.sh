#!/usr/bin/env bash
# Pi-M (Motion Pi) provisioning for Johnny 5 -- Phase 02 locomotion stack.
# Target: Raspberry Pi Zero 2 W, Raspberry Pi OS Lite 64-bit (Bookworm, aarch64).
# Idempotent-ish; safe to re-run. Run as the normal 'pi' user (uses sudo as needed).
#
#   bash scripts/setup_motion_pi.sh
#
# Known Constraint (Phase 02): ONNX Runtime must be the aarch64 build. On 64-bit
# Raspberry Pi OS, `pip install onnxruntime` pulls a working aarch64 wheel
# (piwheels mirror). The 32-bit OS has NO official wheel -- if `import onnxruntime`
# fails, confirm `uname -m` is aarch64 (64-bit OS), not armv7l.

set -euo pipefail

VENV="${JOHNNY5_VENV:-$HOME/johnny5/venv}"

echo "== arch check =="
ARCH="$(uname -m)"
echo "uname -m = $ARCH"
if [ "$ARCH" != "aarch64" ]; then
  echo "WARNING: expected aarch64 (64-bit Raspberry Pi OS). onnxruntime has no" >&2
  echo "         official wheel for $ARCH; reflash with the 64-bit OS Lite image." >&2
fi

echo "== system packages =="
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev i2c-tools libatlas-base-dev

echo "== enable I2C (MPU-6050 0x68, VL53L1X 0x29, ADS1115 0x48) =="
sudo raspi-config nonint do_i2c 0
# Serial bus servos (Phase 03) live on the UART; left disabled here.

echo "== python venv at $VENV =="
mkdir -p "$(dirname "$VENV")"
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip

echo "== motion stack =="
# onnxruntime  : locomotion policy inference (LocomotionPolicy)
# numpy        : observation assembly
# smbus2       : MPU-6050 / ADS1115 over I2C
# gpiozero+lgpio: H-bridge PWM/dir + quadrature encoders on Bookworm
# paho-mqtt    : johnny5/intent + status (PROTOCOL.md)
pip install onnxruntime numpy smbus2 gpiozero lgpio paho-mqtt

echo "== verify onnxruntime (aarch64) =="
python - <<'PY'
import onnxruntime as ort, numpy as np
print("onnxruntime", ort.__version__, "providers:", ort.get_available_providers())
PY

cat <<EOF

== done ==
venv:        $VENV   (activate: source "$VENV/bin/activate")
next:        copy policies/locomotion_v3.onnx to the Pi, then
             python3 scripts/test_locomotion_policy.py --model <path-to>.onnx
thermal:     the Pi Zero 2 W throttles under sustained load -- fit a heatsink and
             watch 'vcgencmd measure_temp' during the physical integration test.
EOF
