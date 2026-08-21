#!/usr/bin/env bash
# Deploy Freebuff2API / Relay to Cloudflare Workers with US placement guard
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "=========================================="
echo "🇺🇸 Deploying Worker to Cloudflare (US Egress Guard)"
echo "=========================================="

# Check CF Token
if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  if [ -f "/opt/cfmail/.env" ]; then
    export CLOUDFLARE_API_TOKEN="$(grep CF_API_TOKEN /opt/cfmail/.env | cut -d= -f2)"
  fi
fi

if [ -z "${CLOUDFLARE_API_TOKEN:-}" ]; then
  echo "⚠️ CLOUDFLARE_API_TOKEN tidak ditemukan di environment."
  echo "Silakan masukkan Cloudflare API Token (atau set via export CLOUDFLARE_API_TOKEN=...):"
  read -r -p "Token: " INPUT_TOKEN
  export CLOUDFLARE_API_TOKEN="$INPUT_TOKEN"
fi

# 1. Sync tokens if credentials directory has files
if [ -d "credentials" ] && [ "$(ls -A credentials/*.json 2>/dev/null)" ]; then
  echo "🔄 Menyinkronkan token credentials ke wrangler.toml..."
  node tools/sync_wrangler.js || true
fi

# 2. Deploy main worker with smart placement (US Target)
echo "🚀 Deploying freebuff2api (Smart Placement to US)..."
npx wrangler deploy

echo ""
echo "✅ DEPLOY SELESAI!"
echo "Worker Anda sekarang otomatis dieksekusi di edge US dan aman dari 'ip_capped'."
echo "=========================================="
