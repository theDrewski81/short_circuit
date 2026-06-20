#!/usr/bin/env bash
# Rsync src/vision and src/shared to Pi-V, restart the vision service.
# Run from the development machine, not from the Pis.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/_common.sh

echo "Deploying vision + shared code to ${JOHNNY5_USER}@${JOHNNY5_VISION_HOST}..."

rsync -avz --delete \
  src/vision/ "${JOHNNY5_USER}@${JOHNNY5_VISION_HOST}:${JOHNNY5_REMOTE_PATH}/src/vision/"
rsync -avz --delete \
  src/shared/ "${JOHNNY5_USER}@${JOHNNY5_VISION_HOST}:${JOHNNY5_REMOTE_PATH}/src/shared/"

# Service name/management (systemd unit vs. manual) is TBD -- this assumes a
# systemd unit named johnny5-vision exists. Adjust once the service is defined.
ssh "${JOHNNY5_USER}@${JOHNNY5_VISION_HOST}" "sudo systemctl restart johnny5-vision" \
  || echo "Restart failed or service not yet defined -- check manually."

echo "Done."
