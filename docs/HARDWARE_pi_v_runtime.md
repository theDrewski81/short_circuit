# Pi-V Runtime Environment – the box, the camera, the dependency file, and the audio gap

What is known about Pi-V, the vision unit, and where each fact comes from. Pairs with
`docs/HARDWARE_pi_m_runtime.md`, which does the same for the motion unit, and with
`docs/HARDWARE_power_harness.md`, which covers Pi-V's wiring rather than its software.

**This document is weaker evidence than its Pi-M counterpart, and the difference matters.**
Every fact in `docs/HARDWARE_pi_m_runtime.md` was learned at the Task 1 bench bringup on
2026-07-12, on the hardware. Nothing here was. Pi-V has had no equivalent bringup session
and no agent session can reach `192.168.1.218`, so every claim below is traced to the
repository file that states it, and everything the repository does not state is marked as
not stated rather than filled in. Where this document and the Pi disagree, the Pi wins and
this document is wrong.

## The box

| | | Source |
|---|---|---|
| Host | `johnny5-vision`, `192.168.1.218` (static) | `phases/PHASE_01_INFRASTRUCTURE.md` task 2; `PROJECT_STATE.md` section 9, 2026-06-20; `scripts/_common.sh` |
| OS | Raspberry Pi OS Lite 64-bit, Trixie | `PROJECT_STATE.md` section 9, 2026-06-20 ("Both Pis on Raspberry Pi OS Lite 64-bit (Trixie)") |
| Login user | `administrator` | same entry; `scripts/_common.sh` default |
| System Python | **Not recorded for Pi-V.** See below. | — |
| venv | `~/johnny5-env` | `phases/PHASE_01_INFRASTRUCTURE.md` task 2 |
| Repo checkout | `~/johnny5` | `phases/PHASE_01_INFRASTRUCTURE.md` task 2; `scripts/_common.sh` `JOHNNY5_REMOTE_PATH` |
| LiteLLM virtual key alias | `johnny5-vision` on the AOS proxy | `PROJECT_STATE.md` section 9, 2026-06-22 |

**The system Python version is an inference, not a record.** `docs/HARDWARE_pi_m_runtime.md`
records Python 3.13 on Pi-M, and `PROJECT_STATE.md` puts both Pis on the same Trixie 64-bit
image, so 3.13 is what should be expected on Pi-V. No repository file states it, and nobody
has checked. Treat it as expected, not known. It is not academic: the Trixie plus Python 3.13
combination is exactly what makes `pip install lgpio` impossible on Pi-M, and any Pi-V package
with the same wheel problem would fail the same way.

**The static IP is NetworkManager-managed and could revert.** It was set with `nmcli` inside
the router's reservation block because dhcpcd is inactive on this OS version, and the profiles
are netplan-managed, so a future `netplan apply` could regenerate them. Recorded at S05 on
2026-06-20 and repeated here because the failure looks like a dead Pi rather than a
configuration change.

## Nothing provisions Pi-V

`scripts/setup_motion_pi.sh` provisions Pi-M: apt packages, I2C, the `pwm-2chan` overlay, the
udev rule, the venv with `--system-site-packages`, `pip install -r`, and a verification block
that prints the resolved path of each GPIO-side import. **There is no `setup_vision_pi.sh`, and
no other script provisions Pi-V.** The gap is real and is not a naming difference.

What does exist for Pi-V is deployment and access, which is a different job:

- `scripts/deploy_vision.sh` rsyncs `src/vision/` and `src/shared/` to the Pi and then runs
  `sudo systemctl restart johnny5-vision`. Its own comment says the service name and management
  are TBD and that the restart assumes a unit that may not exist; the restart is tolerated with
  `|| echo` rather than being fatal. **No systemd unit file for `johnny5-vision` exists in the
  repository.** `scripts/deploy_motion.sh` carries the identical caveat for `johnny5-motion`, so
  the TBD service is symmetric and is not part of the provisioning asymmetry.
- `scripts/ssh_vision.sh` is an SSH wrapper over the same `_common.sh` defaults.
- `scripts/check_health.sh` queries `johnny5/heartbeat/vision` on the broker at
  `MQTT_BROKER_HOST` and reports liveness. It runs from the development machine, not the Pi.

The provisioning steps that were actually performed on Pi-V exist only as prose in
`phases/PHASE_01_INFRASTRUCTURE.md` task 2: `apt install python3-pip python3-venv git
i2c-tools`, `raspi-config` for the camera, `python3 -m venv ~/johnny5-env`, and a clone into
`~/johnny5`. They were run by hand at S05 on 2026-06-20 and have never been captured in a
script, so re-provisioning or replacing Pi-V today means re-reading that task list and
repeating it manually. Whether that gap is worth closing with a `setup_vision_pi.sh` is an open
question raised by this document, not a decision it takes.

## The camera

The camera is the 8 MP 1080p CSI module on the head, one of two owned, connected by ribbon
rather than by GPIO (`BOM.md` section 7 and its Pi-V GPIO map).

Enablement, verbatim from `phases/PHASE_01_INFRASTRUCTURE.md` task 2: enable the camera
interface via `raspi-config`, then confirm the camera is detected with `libcamera-hello`. That
is the whole of the recorded enablement step, and there is no record in the repository of it
having been run or of what it printed.

**Two capture interfaces appear in the repository and they are not the same one.**
`scripts/whats_this_color.py`, the only program here that actually captures a frame, shells out
to `rpicam-still -o <path> --immediate -t 1000 -n`. `phases/PHASE_04_COGNITION.md` task 2
specifies `picamera2` for the real capture pipeline, explicitly rejects the legacy `picamera`
library, and warns that `picamera2` APIs differ between OS versions. That phase document names
Bookworm while this box runs Trixie, so its version caution applies to itself: the
`picamera2` version present on a Trixie image has not been confirmed against what Phase 04
assumes. Neither `picamera2` nor `rpicam-apps` is declared in any requirements file; both are
OS-supplied on Raspberry Pi OS images, and neither presence has been checked here.

## Dependencies are declared in `src/vision/requirements-vision.txt`

That file is the single dependency declaration for Pi-V, created by S18 against O8 and sited
beside the code it serves on the `simulation/chassis/requirements-train.txt` precedent. It
pins `httpx==0.28.1` and `python-dotenv==1.2.3` exactly rather than by range, and its header
explains why: a two-package runtime on a Pi Zero 2 W is not worth a silent minor bump in the
HTTP client.

```
pip install -r src/vision/requirements-vision.txt
```

It covers `src/vision/llm_client.py` plus the two Pi-V bench scripts that drive it,
`scripts/test_llm_client.py` and `scripts/whats_this_color.py`; everything else those three
modules import is standard library. `llm_client.py` imports `httpx` only, and `python-dotenv`
is imported by the two scripts. **The pins are current PyPI releases as of 2026-08-25 and have
not been verified against Pi-V**; the file says so itself, and if a `pip install -r` on the Pi
disagrees with a working install, the Pi wins and the file is corrected to match it.

What the file does not cover is everything Phase 04 adds. The camera library, the VAD model,
the transcription client, the TTS path, the MQTT client and the WS2812B driver for the mouth
array are all named in `phases/PHASE_04_COGNITION.md` and declared nowhere. That is expected
for unwritten code and is noted so the file is not mistaken for a complete Pi-V runtime.

## Configuration comes from `.env`

`.env` is gitignored on both Pis; `.env.example` at the repository root is the committed
template and carries the confirmed values and their rationale. The Pi-V half of it is the
LiteLLM client block and the shared MQTT block.

`LITELLM_ENDPOINT` is the existing Agentic OS proxy at `http://192.168.1.223:4000/v1`, reused
rather than rebuilt. `LITELLM_MODEL` is `vision-batch`, which routes to `llava:7b` on the
CPU-only Ollama node ms3 at `192.168.1.225`, chosen so vision inference does not contend with
desktop GPU work. `LITELLM_TIMEOUT` is **60.0**, not the 8.0 that `LiteLLMConfig` defaults to
in code: llava on a CPU node takes 15 to 40 seconds per image and longer on a cold load, and
the 8.0 s placeholder from the Phase 01 task list would have abandoned every call before the
model answered. `LiteLLMConfig.from_env()` raises on a missing endpoint, key or model rather
than falling back to a default, on the reasoning that a wrong endpoint is worse than a loud
failure.

The MQTT block points at the Mosquitto LXC `sn-mosquitto` at `192.168.1.227:1883`, confirmed
live 2026-06-20.

## Audio does not work yet, and the overlay that would fix it is unwritten

All audio is on Pi-V: the INMP441 I²S MEMS microphone and the MAX98357A I²S class-D amplifier
share one I²S bus, consolidated here at S01 on 2026-06-17 specifically to free Pi-M's I²S. On
the Pi-V header that is BCLK on GPIO18, LRCLK on GPIO19, mic data in on GPIO20 and amplifier
data out on GPIO21 (`BOM.md` Pi-V GPIO map, and the `SIG_I2S_*` nets in
`docs/HARDWARE_power_harness.md`).

**Two codecs on one bus need a device-tree overlay that has never been written.** The stock
`max98357a` and `googlevoicehat` overlays conflict; what is required is a custom combined
`simple-audio-card` overlay with one CPU DAI and two codec DAIs. This is **O1** in
`PROJECT_STATE.md` section 7, open since 2026-06-17, owned by a worker session and due in
Phase 04. It is referenced in `BOM.md`, in `phases/PHASE_00_HARDWARE.md`, and on the power
harness schematic, and until now it has been recorded only in prose with no home.

**This file is that home.** When the overlay is written, it belongs in this document, in the
form Pi-M's `pwm-2chan` section takes: the exact `/boot/firmware/config.txt` line, why each
argument is load-bearing, what the failure looks like without it, and the one command that
proves it loaded after a reboot. **It is deliberately not attempted here.** Writing a
device-tree overlay for two codecs that no session can test on the hardware they run on would
be a gate met against an unbuilt artifact, which this project has already done once and
recorded the lesson for. It stays Phase 04 work, to be done with the mic and amplifier wired
and a Pi in front of whoever is doing it. Half-duplex turn-taking with the mic gated during
playback is the intended behaviour, also Phase 04; there is no acoustic echo cancellation in
V1.

## Hardware PWM on Pi-V is unrecorded

`BOM.md` assigns the 1 W navigation light to Pi-V GPIO13 as a hardware PWM output driving a
MOSFET gate, and `docs/HARDWARE_power_harness.md` carries the same on `SIG_NAV_PWM`. Pi-M
needed an explicit `dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4` line and a reboot before
`/sys/class/pwm` was populated at all. **No equivalent line is recorded anywhere for Pi-V**,
and whether one is needed there, and whether it can coexist with the I²S assignment on the same
header, is not answered by any file in this repository. Flagged rather than guessed; it belongs
with the O1 audio work, since both are `config.txt` questions on the same box.

## The Pi-V header, for reference

From `BOM.md`'s Pi-V GPIO pin map. 40-pin header, 3.3 V logic.

| Function | GPIO (BCM) | Notes |
|---|---|---|
| CSI camera | (ribbon) | Not GPIO |
| I²S BCLK / LRCLK | 18 / 19 | PCM clock / frame-sync, shared by mic and amplifier |
| I²S DIN (mic SD) | 20 | INMP441 into the Pi |
| I²S DOUT (amp DIN) | 21 | Pi into the MAX98357A |
| WS2812B mouth array | 10 | SPI0 MOSI, via a 74AHCT125 level shifter |
| Navigation light | 13 | Hardware PWM to a MOSFET gate |

Inter-Pi messaging runs over the WiFi LAN via the broker; no GPIO cross-link is reserved.

## What in this document is unverified

Stated once, in one place, so it cannot be missed:

- **Everything about the running state of Pi-V.** No agent session can reach `192.168.1.218`,
  and Pi-V has had no bench bringup session of the kind that produced the Pi-M document. The
  host, OS, user, venv path and checkout path are all as configured at S05 on 2026-06-20 and
  as the deployment scripts assume, not as observed since.
- **The system Python version**, which no file records for Pi-V.
- **The camera enablement step**, which is a documented instruction with no record of its
  having been run or of `libcamera-hello` succeeding.
- **The dependency pins**, which are PyPI releases as of 2026-08-25 and have never met the Pi.
- **The presence of `picamera2` or `rpicam-apps`**, and their versions on a Trixie image.

The way to close all of these at once is a Pi-V bringup session with the box in hand, the way
2026-07-12 closed them for Pi-M. Until then this document records what the repository knows,
which is not the same as what is true.
