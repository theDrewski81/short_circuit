#!/usr/bin/env bash
# Query both Pi heartbeat topics from the home lab broker and report liveness.
# Requires mosquitto_sub (mosquitto-clients package) on the development machine.
set -euo pipefail
cd "$(dirname "$0")/.."

: "${MQTT_BROKER_HOST:?Set MQTT_BROKER_HOST (see .env.example)}"
MQTT_BROKER_PORT="${MQTT_BROKER_PORT:-1883}"
TIMEOUT_S="${TIMEOUT_S:-5}"

check_topic() {
  local topic="$1"
  local label="$2"
  local result
  result=$(timeout "${TIMEOUT_S}" mosquitto_sub \
    -h "${MQTT_BROKER_HOST}" -p "${MQTT_BROKER_PORT}" \
    ${MQTT_USERNAME:+-u "$MQTT_USERNAME"} ${MQTT_PASSWORD:+-P "$MQTT_PASSWORD"} \
    -t "${topic}" -C 1 2>/dev/null) || true

  if [[ -n "${result}" ]]; then
    echo "${label}: alive -- ${result}"
  else
    echo "${label}: NO RESPONSE within ${TIMEOUT_S}s"
  fi
}

check_topic "johnny5/heartbeat/motion" "Pi-M"
check_topic "johnny5/heartbeat/vision" "Pi-V"
