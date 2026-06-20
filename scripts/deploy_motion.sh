#!/usr/bin/env bash
# Rsync src/motion and src/shared to Pi-M, restart the motion service.
# Run from the development machine, not from the Pis.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/_common.sh

echo "Deploying motion + shared code to ${JOHNNY5_USER}@${JOHNNY5_MOTION_HOST}..."

rsync -avz --delete \
  src/motion/ "${JOHNNY5_USER}@${JOHNNY5_MOTION_HOST}:${JOHNNY5_REMOTE_PATH}/src/motion/"
rsync -avz --delete \
  src/shared/ "${JOHNNY5_USER}@${JOHNNY5_MOTION_HOST}:${JOHNNY5_REMOTE_PATH}/src/shared/"

# Service name/management (systemd unit vs. manual) is TBD -- this assumes a
# systemd unit named johnny5-motion exists. Adjust once the service is defined.
ssh "${JOHNNY5_USER}@${JOHNNY5_MOTION_HOST}" "sudo systemctl restart johnny5-motion" \
  || echo "Restart failed or service not yet defined -- check manually."

echo "Done."
