#!/usr/bin/env bash
# Pi-M (Motion Pi) provisioning for Johnny 5 -- Phase 02 locomotion stack.
# Target: Raspberry Pi Zero 2 W, Raspberry Pi OS Lite 64-bit (Trixie, aarch64).
# Idempotent-ish; safe to re-run. Run as the normal login user (uses sudo as needed).
#
#   bash scripts/setup_motion_pi.sh
#   sudo reboot          # REQUIRED once: loads the pwm-2chan overlay (see below)
#
# Must be run from inside a checkout: the pip stage reads
# src/motion/requirements-motion.txt, resolved relative to this script.
#
# Known Constraint (Phase 02): ONNX Runtime must be the aarch64 build. On 64-bit
# Raspberry Pi OS, `pip install onnxruntime` pulls a working aarch64 wheel
# (piwheels mirror). A 32-bit OS has NO official wheel -- if `import onnxruntime`
# fails, confirm `uname -m` is aarch64 (64-bit OS), not armv7l.
#
# Known Constraint (Trixie / Python 3.13): gpiozero and lgpio come from apt, NOT
# from pip. `pip install lgpio` cannot build here -- there is no cp313 piwheel and
# the sdist links against a system `-llgpio` that is not installed (swig present
# does not help). They are installed below with apt and reached from the venv via
# include-system-site-packages. See docs/HARDWARE_pi_m_runtime.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
REQUIREMENTS="$REPO_ROOT/src/motion/requirements-motion.txt"

# The venv that exists on Pi-M is ~/johnny5-env (built 2026-07-12 at Task 1
# bringup). This default matches it; the previous default ($HOME/johnny5/venv)
# did not, so a re-run silently built a second venv beside the working one.
VENV="${JOHNNY5_VENV:-$HOME/johnny5-env}"
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

if [ ! -f "$REQUIREMENTS" ]; then
  echo "ERROR: $REQUIREMENTS not found." >&2
  echo "       Run this script from a Johnny 5 checkout (bash scripts/setup_motion_pi.sh)." >&2
  exit 1
fi

echo "== system packages =="
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip python3-dev i2c-tools libatlas-base-dev
# gpiozero + lgpio are apt-only on this platform (see the Trixie constraint above).
# python3-lgpio brings the compiled extension AND the liblgpio shared object that
# the pip sdist fails to find.
sudo apt-get install -y python3-gpiozero python3-lgpio

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
# Not needed on Pi-M as built -- the 2026-07-12 bringup hit no PWM sysfs
# permission error -- but harmless and kept for a fresh or differently
# configured image.
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
# --system-site-packages is load-bearing: the apt gpiozero and lgpio above are
# only importable from the venv through it.
[ -d "$VENV" ] || python3 -m venv --system-site-packages "$VENV"
# Repair a venv built before this was required (Pi-M's ~/johnny5-env was).
if grep -q '^include-system-site-packages *= *false' "$VENV/pyvenv.cfg"; then
  sed -i 's/^include-system-site-packages *= *false/include-system-site-packages = true/' "$VENV/pyvenv.cfg"
  echo "set include-system-site-packages = true in $VENV/pyvenv.cfg"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip

echo "== motion stack =="
# The pip-installable half of the runtime. gpiozero and lgpio are deliberately
# absent -- they came from apt above. See src/motion/requirements-motion.txt for
# what each package is for.
pip install -r "$REQUIREMENTS"

echo "== verify runtime imports =="
python - <<'PY'
import onnxruntime as ort
print("onnxruntime", ort.__version__, "providers:", ort.get_available_providers())

# gpiozero and lgpio are the apt-installed half, reached through
# include-system-site-packages; rpi_hardware_pwm came from pip. The printed paths
# say which is which -- an apt package resolves under /usr/lib/python3/dist-packages.
# If gpiozero or lgpio fails to import, the venv is not seeing system site-packages
# and the H-bridge and encoder backends would fail at bench time instead of here.
import gpiozero, lgpio, rpi_hardware_pwm
for m in (gpiozero, lgpio, rpi_hardware_pwm):
    print(m.__name__, "->", getattr(m, "__file__", "(builtin)"))
PY

cat <<EOF

== done ==
venv:        $VENV   (activate: source "$VENV/bin/activate")
REBOOT NOW:  sudo reboot   -- required to load the pwm-2chan overlay.
verify PWM:  after reboot, 'ls /sys/class/pwm' should show pwmchip0 with 2 channels
             (npwm=2). motor_driver.py drives chip 0.
bench test:  python3 scripts/test_motors.py   (wheels free, robot off the treads)
policy:      copy policies/locomotion_v3.onnx to the Pi, then
             python3 scripts/test_locomotion_policy.py --model <path-to>.onnx
thermal:     the Pi Zero 2 W throttles under sustained load -- fit a heatsink and
             watch 'vcgencmd measure_temp' during the physical integration test.
EOF
