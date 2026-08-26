# Pi-M Runtime Environment — venv, GPIO packages, hardware PWM

What `scripts/setup_motion_pi.sh` provisions on Pi-M and, more usefully, the three
things about that box which are not obvious from reading the script. Pairs with
`docs/HARDWARE_drive_bringup.md`, which covers the wiring rather than the software.

Every fact here was learned at the Task 1 bench bringup on 2026-07-12 and lived
until 2026-08-25 only in a loose project-memory note at the repository root, which
is why `setup_motion_pi.sh` went on carrying an install line the bench had already
proved could not work. **None of it has been re-verified since 2026-07-12**, and no
agent session can reach Pi-M to try. Where this document and the Pi disagree, the Pi
wins and this document is wrong.

## The box

| | |
|---|---|
| Host | `johnny5-motion`, `192.168.1.217` (static) |
| OS | Raspberry Pi OS Lite 64-bit, Trixie, aarch64 |
| Login user | `administrator` |
| System Python | 3.13 |
| venv | `~/johnny5-env` |

## The venv is `~/johnny5-env`

Not `~/johnny5/venv`. `setup_motion_pi.sh` defaulted `JOHNNY5_VENV` to the latter
until 2026-08-25, so re-running it built a second venv beside the working one
instead of updating it. The default now matches the Pi. `JOHNNY5_VENV` still
overrides it for anyone provisioning a different box.

```
source ~/johnny5-env/bin/activate
```

## gpiozero and lgpio come from apt, not pip

`pip install lgpio` cannot succeed on this platform. Trixie ships Python 3.13, there
is no cp313 wheel on the piwheels mirror, and the sdist falls back to compiling
against a system `-llgpio` that a stock image does not have. Installing `swig` does
not change the outcome; the missing piece is the library, not the binding generator.

The route that works, and what `setup_motion_pi.sh` now does:

```
sudo apt-get install -y python3-gpiozero python3-lgpio
```

then create the venv with `--system-site-packages`, or set
`include-system-site-packages = true` in `~/johnny5-env/pyvenv.cfg` if it already
exists, so the venv can see them. The script does both, repairing an existing
`pyvenv.cfg` in place — Pi-M's own venv predates the fix and needs the repair rather
than the flag.

Everything else in the motion stack is still pip, from
`src/motion/requirements-motion.txt`: `onnxruntime`, `numpy`, `smbus2`,
`rpi-hardware-pwm`, `paho-mqtt`. That file is the single list; the script reads it.

`import gpiozero` resolving to a path under `/usr/lib/python3/dist-packages` is the
check that the system-site-packages link is live. The script prints the resolved
path of each of the three GPIO-side modules at the end of its run for exactly that
reason.

## Hardware PWM needs the overlay and a reboot

`/sys/class/pwm` is empty — not wrong, empty — until this line is in
`/boot/firmware/config.txt` and the Pi has been rebooted:

```
dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4
```

The `pin=`/`pin2=` arguments are load-bearing. The stock `pwm-2chan` overlay puts
PWM0 and PWM1 on GPIO18 and GPIO19; the BOM puts motor PWMA and PWMB on GPIO12 and
GPIO13, and `func=4` selects ALT0 on those pins. Without the arguments the peripheral
comes up on pins nothing is wired to, and the failure looks like dead motors rather
than like a configuration error.

After the reboot, `ls /sys/class/pwm` shows `pwmchip0` with `npwm=2`.
`src/motion/motor_driver.py` drives chip 0.

## The udev rule was not needed on this box

`setup_motion_pi.sh` installs `/etc/udev/rules.d/99-pwm.rules` and adds the login
user to `gpio` so that PWM sysfs is writable without sudo. On Pi-M as built this was
never exercised: GPIO access through gpiozero and lgpio worked with no extra
permissions and no PWM sysfs permission error was hit at the 2026-07-12 bringup. The
rule is kept because a fresh or differently configured image may still need it, but
if it ever misbehaves, it is removable on this hardware without breaking the bench
test.
