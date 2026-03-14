#!/usr/bin/env bash
set -euo pipefail

# Ensure Bitwarden is unlocked
if [ -z "${BW_SESSION:-}" ]; then
  export BW_SESSION=$(bw unlock --raw)
fi

export ANTHROPIC_API_KEY=$(bw get password "anthropic-api-key")
export GOOGLE_APPLICATION_CREDENTIALS=$(bw get password "google-vision-credentials-path")
export GOOGLE_MAPS_API_KEY=$(bw get password "google-maps-api-key")

exec "$@"
