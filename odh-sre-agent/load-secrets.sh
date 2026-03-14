#!/usr/bin/env bash
set -euo pipefail

# Ensure Bitwarden is unlocked
if [ -z "${BW_SESSION:-}" ]; then
  export BW_SESSION=$(bw unlock --raw)
fi

export ANTHROPIC_API_KEY=$(bw get password "anthropic-api-key")

exec "$@"
