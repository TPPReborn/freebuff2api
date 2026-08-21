#!/usr/bin/env bash
# Startup script for Native Linux / MacOS / Termux
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Load .env if exists
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

export PORT="${PORT:-8787}"
export API_KEY="${API_KEY:-freebuff-default-key}"
export FREEBUFF_DEBUG="${FREEBUFF_DEBUG:-false}"
export FREEBUFF_CRED_DIR="${FREEBUFF_CRED_DIR:-./credentials}"

# If RELAY_URL not set, default to US relay
export RELAY_URL="${RELAY_URL:-https://freebuff-relay-us.irvan-fbe.workers.dev/,https://freebuff-relay-us2.irvan-fbe.workers.dev/}"

mkdir -p "$FREEBUFF_CRED_DIR"

echo "=========================================="
echo "🚀 Starting Freebuff2API (Native Mode)"
echo "Port       : $PORT"
echo "API Key    : $API_KEY"
echo "Relay      : $RELAY_URL"
echo "Credentials: $FREEBUFF_CRED_DIR"
echo "=========================================="

exec node server.js
