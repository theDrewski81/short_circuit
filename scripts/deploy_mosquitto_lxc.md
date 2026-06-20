# Mosquitto Broker — Proxmox LXC Deployment

Run these on the Proxmox host (not from a Pi or the dev machine). Adjust
`<node>`, `<vmid>`, and storage pool to match your cluster.

## 1. Create the container

```bash
pct create <vmid> local:vztmpl/debian-12-standard_12.*_amd64.tar.zst \
  --hostname johnny5-mqtt \
  --cores 1 --memory 256 --swap 256 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --rootfs local-lvm:4 \
  --unprivileged 1 \
  --features nesting=0
pct start <vmid>
```

256MB RAM / 1 core / 4GB disk is generous for Mosquitto at this message
volume. Adjust to fit your cluster's available headroom.

## 2. Install Mosquitto

```bash
pct exec <vmid> -- bash -c "apt update && apt install -y mosquitto mosquitto-clients"
```

## 3. Configure auth (no anonymous access)

```bash
pct exec <vmid> -- bash -c "mosquitto_passwd -c /etc/mosquitto/passwd johnny5"
# prompts for a password -- this becomes MQTT_PASSWORD in .env
```

`/etc/mosquitto/conf.d/johnny5.conf`:

```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
persistence true
persistence_location /var/lib/mosquitto/
```

```bash
pct exec <vmid> -- systemctl restart mosquitto
pct exec <vmid> -- systemctl enable mosquitto
```

## 4. Confirm reachable from the LAN

From the dev machine:

```bash
mosquitto_pub -h <lxc-ip> -p 1883 -u johnny5 -P <password> -t johnny5/test -m "hello"
mosquitto_sub -h <lxc-ip> -p 1883 -u johnny5 -P <password> -t johnny5/test -C 1
```

## 5. Update `.env` on both Pis

```
MQTT_BROKER_HOST=<lxc-ip>
MQTT_BROKER_PORT=1883
MQTT_USERNAME=johnny5
MQTT_PASSWORD=<password set in step 3>
```

## Notes

- Single user (`johnny5`) shared by both Pis is sufficient for Phase 01 --
  topic-level ACLs can be added later if needed (e.g. restricting Pi-M to
  publish-only on `johnny5/status`).
- `persistence true` ensures retained messages (`johnny5/offline`,
  `johnny5/heartbeat/*`) survive a broker restart.
- No TLS configured -- traffic is plaintext on the LAN. Acceptable for a
  bench/home-lab setup; revisit if the broker is ever exposed beyond the LAN.
