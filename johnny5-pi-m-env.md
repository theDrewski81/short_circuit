---
name: johnny5-pi-m-env
description: Johnny 5 Pi-M (johnny5-motion) Python env + hardware-PWM setup gotchas
metadata: 
  node_type: memory
  type: reference
  originSessionId: cfc35631-7180-4413-a925-71c0f9a57201
---

Pi-M (`johnny5-motion`, 192.168.1.217) runtime setup, learned the hard way during Task 1 bench bringup (2026-07-12). Non-obvious, not fully captured in the repo:

- **venv lives at `~/johnny5-env`**, NOT `~/johnny5/venv` (the `setup_motion_pi.sh` default). Activate: `source ~/johnny5-env/bin/activate`. Re-run the setup script with `JOHNNY5_VENV=~/johnny5-env` or it builds a second venv.
- **lgpio can't pip-build on Trixie / Python 3.13** — no piwheels wheel for cp313, and the sdist links against `-llgpio` (system lib not present) even with `swig` installed. Fix used: `sudo apt install python3-gpiozero python3-lgpio`, then set `include-system-site-packages = true` in `~/johnny5-env/pyvenv.cfg` so the venv sees them. `rpi-hardware-pwm` and the pure-Python bits still come from pip.
- **Hardware PWM needs the overlay + reboot.** `/sys/class/pwm` is empty until `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4` is in `/boot/firmware/config.txt` (the `pin=12/13,func=4` part forces PWM onto GPIO12/13; default overlay uses 18/19). After reboot, `pwmchip0` with `npwm=2` appears; `motor_driver.py` uses chip 0.
- GPIO access via gpiozero/lgpio worked without extra permissions; no PWM sysfs permission error hit in practice (udev rule in the setup script was not needed on this box).

Pi-M is on Raspberry Pi OS Lite 64-bit Trixie, user `administrator`. See [[johnny5-phase02-locomotion]].
