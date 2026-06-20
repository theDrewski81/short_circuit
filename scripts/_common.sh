#!/usr/bin/env bash
# Shared config for deployment/ssh scripts. Source, do not execute directly.
# Override any of these via environment before invoking a script, e.g.:
#   JOHNNY5_USER=pi ./scripts/deploy_motion.sh

set -euo pipefail

# Static IPs (set on each Pi via nmcli, see INITIATING_PROMPT.md decision log).
# .local mDNS hostnames were unreliable from the dev side, so static IPs are
# the default here rather than johnny5-motion.local / johnny5-vision.local.
JOHNNY5_MOTION_HOST="${JOHNNY5_MOTION_HOST:-192.168.1.217}"
JOHNNY5_VISION_HOST="${JOHNNY5_VISION_HOST:-192.168.1.218}"
JOHNNY5_USER="${JOHNNY5_USER:-administrator}"
JOHNNY5_REMOTE_PATH="${JOHNNY5_REMOTE_PATH:-~/johnny5}"
