#!/usr/bin/env bash
# Shared config for deployment/ssh scripts. Source, do not execute directly.
# Override any of these via environment before invoking a script, e.g.:
#   JOHNNY5_USER=pi ./scripts/deploy_motion.sh

set -euo pipefail

JOHNNY5_MOTION_HOST="${JOHNNY5_MOTION_HOST:-johnny5-motion.local}"
JOHNNY5_VISION_HOST="${JOHNNY5_VISION_HOST:-johnny5-vision.local}"
JOHNNY5_USER="${JOHNNY5_USER:-pi}"
JOHNNY5_REMOTE_PATH="${JOHNNY5_REMOTE_PATH:-~/johnny5}"
