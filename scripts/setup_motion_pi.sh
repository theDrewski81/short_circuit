#!/usr/bin/env bash
# Pi-M (Motion Pi) provisioning for Johnny 5 -- Phase 02 locomotion stack.
# Target: Raspberry Pi Zero 2 W, Raspberry Pi OS Lite 64-bit (Trixie, aarch64).
# Idempotent-ish; safe to re-run. Run as the normal login user (uses sudo as needed).
#
#   bash scripts/setup_motion_pi.sh
#   sudo reboot          # REQUIRED once: loads the pwm-2chan overlay (see below)
#
# Known Constraint (Phase 02): ONNX Runtime must be the aarch64 build. On 64-bit
# Raspberry Pi OS, `pip install onnxruntime` pulls a working aarch64 wheel
# (piwheels mirror). A 32-bit OS has NO official wheel -- if `import onnxruntime`
# fails, confirm `uname -m` is aarch64 (64-bit OS), not armv7l.

set -euo pipefail

VENV="${JOHNNY5_VENV:-$HOME/johnny5/venv}"
CONFIG_TXT="/boot/firmware/config.txt"     # Trixie/Bookworm location (not /boot/config.txt)
# Hardware PWM on the MOTOR pins. The default pwm-2chan overlay maps PWM0/1 to
# GPIO18/19; the BOM puts motor PWMA/PWMB on GPIO12/13, so force those pins
# (GPIO12=PWM0, GPIO13=PWM1, both ALT0 -> func=4). Without this, hardware PWM
# would appear on the wrong pins.
PWM_OVERLAY='dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4'

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

echo "== enable hardware PWM on GPIO12/13 (motor PWMA/PWMB) =="
if ! grep -qF "$PWM_OVERLAY" "$CONFIG_TXT"; then
  # Direct append from the script (NOT typed into an editor) -- this is the safe
  # form of the Phase 01 'don't pipe commands into a file edit' lesson.
  echo "$PWM_OVERLAY" | sudo tee -a "$CONFIG_TXT" >/dev/null
  echo "added to $CONFIG_TXT: $PWM_OVERLAY  (reboot required to take effect)"
else
  echo "already present in $CONFIG_TXT"
fi

echo "== allow non-root access to /sys/class/pwm (rpi-hardware-pwm) =="
# Without this, exporting/driving the PWM channels needs sudo. udev rule + gpio
# group membership lets the venv user run scripts/test_motors.py directly.
sudo tee /etc/udev/rules.d/99-pwm.rules >/dev/null <<'RULE'
SUBSYSTEM=="pwm*", PROGRAM="/bin/sh -c '\
chown -R root:gpio /sys/class/pwm 2>/dev/null; chmod -R 770 /sys/class/pwm 2>/dev/null;\
chown -R root:gpio /sys/devices/platform/*.pwm/pwm/pwmchip* 2>/dev/null;\
chmod -R 770 /sys/devices/platform/*.pwm/pwm/pwmchip* 2>/dev/null'"
RULE
sudo usermod -aG gpio "$USER" || true
sudo udevadm control --reload-rules || true

echo "== python venv at $VENV =="
mkdir -p "$(dirname "$VENV")"
[ -d "$VENV" ] || python3 -m venv "$VENV"
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip

echo "== motion stack =="
# onnxruntime    : locomotion policy inference (LocomotionPolicy)
# numpy          : observation assembly
# smbus2         : MPU-6050 / ADS1115 over I2C
# gpiozero+lgpio : H-bridge direction/STBY lines + quadrature encoders
# rpi-hardware-pwm: kernel hardware-PWM peripheral on GPIO12/13 (motor speed)
# paho-mqtt      : johnny5/intent + status (PROTOCOL.md)
pip install onnxruntime numpy smbus2 gpiozero lgpio rpi-hardware-pwm paho-mqtt

echo "== verify onnxruntime (aarch64) =="
python - <<'PY'
import onnxruntime as ort
print("onnxruntime", ort.__version__, "providers:", ort.get_available_providers())
PY

cat <<EOF

== done ==
venv:        $VENV   (activate: source "$VENV/bin/activate")
REBOOT NOW:  sudo reboot   -- required to load the pwm-2chan overlay.
verify PWM:  after reboot, 'ls /sys/class/pwm' should show pwmchip0 with 2 channels.
bench test:  python3 scripts/test_motors.py   (wheels free, robot off the treads)
policy:      copy policies/locomotion_v3.onnx to the Pi, then
             python3 scripts/test_locomotion_policy.py --model <path-to>.onnx
thermal:     the Pi Zero 2 W throttles under sustained load -- fit a heatsink and
             watch 'vcgencmd measure_temp' during the physical integration test.
EOF
