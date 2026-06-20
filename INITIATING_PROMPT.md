# Initiating Prompt

Read `CLAUDE.md`. Then read the active phase coordinator in `/phases/`. Follow all instructions in both documents.

## Current Phase

Phase 01 — Infrastructure & Repository (`phases/PHASE_01_INFRASTRUCTURE.md`)

## Status

Repo scaffolding, PROTOCOL.md, offline fallback state machine, motion loop skeleton, and deployment scripts in progress. See the most recent decision log (below or in session handoff) for specifics completed and open items.

## Open Questions Blocking Full Gate

- LiteLLM API key and target model string -- unconfirmed. Endpoint URL is now known. `llm_client.py` still stubbed pending key mint and vision-model selection.
- SSH key auth for the Pis -- deferred (see decision log below). Both Pis currently use password auth.
- `.env` secrets management (local per-Pi vs. Agentic OS secrets manager) -- unresolved (no preference given).

## Decision Log

(Most recent session first. Append new entries above old ones.)

### 2026-06-20 (cont'd -- Pi OS setup, networking)

- Both Pis flashed with Raspberry Pi OS Lite 64-bit (Trixie / `VERSION_CODENAME=trixie`), username `administrator` on both. `scripts/_common.sh` default `JOHNNY5_USER` updated from `pi` to `administrator` to match.
- SSH key auth attempted first via Raspberry Pi Imager's public-key field, but failed two ways in sequence: (1) hostname resolution -- `johnny5-motion` without `.local` doesn't resolve via mDNS from Andrew's client, needed `.local` suffix or direct IP; (2) once on IP, Devolutions RDM threw "entry's public key doesn't match the server's key" -- this is an SSH *host key* mismatch (RDM had a stale cached host fingerprint for that IP/entry from before reflashing), not a client auth-key problem. Rather than debug RDM's host-key cache, both cards were reflashed with password auth only. **Key-based auth is deferred, not abandoned** -- revisit later, and when doing so, clear/reset the host key entry in RDM first to avoid repeating the same false error.
- Static IPs assigned: `johnny5-motion` = `192.168.1.217`, `johnny5-vision` = `192.168.1.218`, both inside Andrew's router reservation block (outside the DHCP pool, so no collision risk). Configured via `nmcli connection modify <profile> ipv4.method manual ...` rather than router-side DHCP reservation (Andrew's explicit choice) or legacy `/etc/dhcpcd.conf` (dhcpcd is inactive on this OS version -- NetworkManager is the active backend, fronted by netplan -- connection profiles are named `netplan-wlan0-SuskNet` / `netplan-eth0`). Confirmed static IPs survive reboot.
  - Caveat noted but not yet hit: profiles are netplan-managed (`netplan-` prefix), so a future `netplan apply` or netplan YAML edit could theoretically regenerate/overwrite the NetworkManager profile and revert the static IP. Not a problem unless netplan config is touched again -- flag if static IPs mysteriously revert.
- `scripts/_common.sh` defaults switched from `johnny5-motion.local` / `johnny5-vision.local` to the static IPs directly (`192.168.1.217` / `192.168.1.218`), since `.local` mDNS resolution was unreliable from Andrew's dev machine during the SSH troubleshooting above.

### 2026-06-20 (cont'd -- johnny5-motion interface setup)

- `johnny5-motion`: ran `apt update/upgrade` and installed `python3-pip python3-venv git i2c-tools`. Enabled I2C + SPI via `raspi-config`; confirmed `/dev/i2c-1` and `/dev/i2c-2` present, `i2cdetect -y 1` runs clean (empty grid expected -- no sensors wired yet).
- Serial port: disabled login shell over serial, enabled serial port hardware via `raspi-config`. Added `dtoverlay=disable-bt` to `/boot/firmware/config.txt` (Trixie moved this from `/boot/config.txt`).
  - First attempt failed silently: piped `echo "dtoverlay=disable-bt" | sudo tee -a ...` as an instruction, but the literal command string got typed into the file as text rather than executed, so the overlay never loaded. `/dev/serial0` was symlinked to `ttyS0` (mini-UART -- baud drift risk under CPU freq scaling, bad for Feetech servo comms) instead of the PL011 hardware UART. Caught via `dmesg | grep tty` showing both `ttyAMA1` (registered, unused) and `ttyS0` (in use) plus a live Bluetooth RFCOMM entry.
  - Fixed by editing `/boot/firmware/config.txt` directly (`sudo nano`) and adding the bare `dtoverlay=disable-bt` line. After reboot, confirmed `/dev/serial0 -> ttyAMA0`, Bluetooth/RFCOMM gone from `dmesg`. **Lesson: don't pipe shell commands as instructions into a file edit -- edit the file directly.** Apply the same direct-edit approach when doing this on `johnny5-vision`.
- `johnny5-motion` interface setup (task 2, Pi-M-specific portion) complete. Next: Python venv + repo clone on `johnny5-motion`, then repeat OS/interface setup on `johnny5-vision` (camera enable instead of serial/UART).

### 2026-06-20 (cont'd -- Mosquitto live, moving to Pi OS setup)

- Mosquitto LXC (`sn-mosquitto`, host `ms1`, IP `192.168.1.227`) is deployed, authenticated, and verified end-to-end: `mosquitto_pub` from `sn-mosquitto` received by `mosquitto_sub` on `ms1` over the LAN. Broker piece of the Phase 01 gate is closed.
  - Hit and fixed two deploy snags, both folded into `scripts/deploy_mosquitto_lxc.md`: (1) duplicate `persistence`/`persistence_location` between the default `mosquitto.conf` and `johnny5.conf` -- removed from the latter; (2) `mosquitto.service` exit 13 on start -- caused by `/etc/mosquitto/passwd` never actually being created by the earlier `mosquitto_passwd -c` step. Recreated it and fixed ownership (`root:mosquitto`, `640`).
  - `.env` MQTT values for both Pis: `MQTT_BROKER_HOST=192.168.1.227`, `MQTT_BROKER_PORT=1883`, `MQTT_USERNAME=johnny5`, password as set during passwd creation.
- LiteLLM API key mint + vision model selection explicitly deferred -- not blocking the next step. Tagged as an item to return to once Pi-side work reaches the point of testing `llm_client.py` (`test_llm_client.py` must run on Pi-V, which requires the Pis to be flashed first).
- Andrew has both Pi Zero 2 W units in hand but unflashed. Next focus: Phase 01 task 2 (Pi OS setup) -- flash Raspberry Pi OS Lite 64-bit on both, configure hostnames (`johnny5-motion`, `johnny5-vision`), SSH, WiFi, then per-Pi package/interface setup.

### 2026-06-20

- LiteLLM endpoint confirmed: `http://192.168.1.223:4000/v1`. Set in `.env.example`. Reused from the existing Agentic OS LiteLLM server -- no second server stood up, per CLAUDE.md ("Johnny 5 is a consumer of that infrastructure").
- Johnny 5 will use a separate LiteLLM virtual API key from Agentic OS, for usage/cost isolation. Key not yet minted -- `.env.example` still has `<key>` placeholder.
- Vision model string still unselected -- `.env.example` placeholder is `<vision-model-name>`. Must be vision-capable for camera queries.
- RabbitMQ (existing home-lab server) considered as broker but rejected in favor of a fresh Mosquitto deploy -- RabbitMQ lacks native retained-message semantics, which the `johnny5/offline` and heartbeat topics rely on, and would have required re-implementing that behavior in application code.
- Mosquitto deploy target: Proxmox LXC container (not Docker), per user preference. Runbook written at `scripts/deploy_mosquitto_lxc.md` -- manual steps, not an executable script, since cluster node names/storage pools aren't accessible from this session.
- Reviewed prior session's scaffolding (`src/motion/offline_fallback.py`, `src/vision/llm_client.py`, `src/motion/main.py`, `src/shared/PROTOCOL.md`, deployment scripts, tests): all consistent with phase doc spec. `tests/test_offline_fallback.py` -- 8/8 passing, covers all three state transitions plus the never-raises guarantee.
- Created top-level `README.md` (Phase 01 task 1 deliverable -- was missing).
- Did not touch uncommitted changes under `mechanical/` and `phases/PHASE_00`/`PHASE_06` found in working tree -- out of Phase 01 scope, flagged to user for separate handling.
