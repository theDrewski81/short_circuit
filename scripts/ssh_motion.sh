#!/usr/bin/env bash
# Convenience SSH wrapper for Pi-M.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/_common.sh

exec ssh "${JOHNNY5_USER}@${JOHNNY5_MOTION_HOST}" "$@"
