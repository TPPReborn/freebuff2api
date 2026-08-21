#!/data/data/com.termux/files/usr/bin/bash
# Install script for Freebuff2API on Termux / Android
set -e

echo "=== Freebuff2API Termux Setup ==="

# 1. Update & install dependencies
pkg update -y
pkg install -y nodejs git

# 2. Clone repo if not in directory
if [ ! -f "server.js" ]; then
  if [ -d "freebuff2api" ]; then
    cd freebuff2api
  else
    git clone https://github.com/TPPReborn/freebuff2api.git
    cd freebuff2api
  fi
fi

# 3. Create credentials directory
mkdir -p credentials

echo ""
echo "Setup selesai!"
echo "Cara menjalankan:"
echo "  1. Buat file .env atau export variabel:"
echo "     export PORT=8787"
echo "     export API_KEY=freebuff-default-key"
echo "     export RELAY_URL=https://freebuff-relay-us.irvan-fbe.workers.dev"
echo "  2. Taruh file credential json di folder ./credentials/"
echo "  3. Jalankan: npm start atau ./start.sh"
