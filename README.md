# 🚀 Freebuff2API (Codebuff OpenAI & Anthropic API Gateway)

Freebuff2API adalah gateway API berkinerja tinggi yang mengubah akun Codebuff/Freebuff menjadi endpoint yang **100% kompatibel dengan OpenAI API (`/v1/chat/completions`) dan Anthropic API (`/v1/messages`)**.

Mendukung **3 Mode Deployment**:
1. ☁️ **Cloudflare Workers (Wrangler / Serverless)**: Tanpa VPS, tanpa relay, deploy langsung ke Cloudflare US edge.
2. 🐳 **Docker / Docker Compose**: Siap pakai untuk server/VPS dengan container isolation.
3. 📱 **Native Node.js & Termux (Android)**: Tanpa Docker, ringan, dan bisa dijalankan langsung di HP Android via Termux atau VPS minim RAM.

---

## 🌟 Fitur Utama

- 🔄 **OpenAI & Anthropic Compatible**: Dukungan endpoint `/v1/chat/completions`, `/v1/models`, `/v1/responses`, dan `/v1/messages`.
- 👁️ **Full Vision / Multimodal Support**: Support input gambar (Base64 & URL gambar) pada model seperti `deepseek/deepseek-v4-flash`.
- ⚡ **Full Streaming Support**: Server-Sent Events (SSE) stream real-time dengan delta reasoning tokens.
- 🔀 **9Router Ready**: Terintegrasi mulus dengan [9Router](https://github.com/TPPReborn/9router) sebagai custom provider.
- 🛡️ **Anti-Detection Mimic**: Meniru signature CLI resmi (`codebuff-cli/1.0.685`, SDK `0.0.141`, `client-type: cli`) dan membersihkan header proxy agar tidak terdeteksi WAF.
- 🔄 **Multi-Relay Load Balancer**: Dukungan multi-relay Cloudflare Workers dengan rotasi otomatis dan failover.
- 👥 **Multi-Account Pool**: Load-balancing akun secara otomatis dengan isolasi session dan reuse cache.
- ⏱️ **Smart 429 Rate Limit Guard**: Otomatis membaca waktu reset (`retryAfterMs` / `resetsAt`) dan jeda akun tanpa spamming session.
- 🤖 **Automated Playwright Harvester**: Auto-login akun Google / Google Workspace for Education + auto-sync ke Wrangler/Docker.

---

## 📐 Pilihan Arsitektur

### Opsi A: Direct Cloudflare Workers (Serverless — Tanpa VPS / Tanpa Relay Eksternal)
```
[Client / 9Router / Cursor] ──► [Cloudflare Worker: freebuff2api] ──► [Codebuff Upstream]
                                (Handle OpenAI/Anthropic, Pool Token,
                                 Session Cache, Direct US Egress)
```

### Opsi B: Self-Hosted (Docker / Native Linux / Termux Android) + US Relay
```
[Client / 9Router] ──► [Local Server: 8787] ──► [CF Worker Relay] ──► [Codebuff Upstream]
                       (Docker / Termux / VPS)   (US Egress Proxy)
```

---

## 📋 Daftar Isi

1. [Opsi 1: Deploy Langsung ke Cloudflare Workers (Wrangler / Serverless)](#opsi-1-deploy-langsung-ke-cloudflare-workers-wrangler--serverless)
2. [Opsi 2: Deploy Menggunakan Docker Compose (VPS / Server)](#opsi-2-deploy-menggunakan-docker-compose-vps--server)
3. [Opsi 3: Deploy Native di Linux / Termux Android](#opsi-3-deploy-native-di-linux--termux-android)
4. [Cara Cek Status & AccessTier Akun](#4-cara-cek-status--accesstier-akun)
5. [Cara Panen Akun & Token (Harvesting)](#5-cara-panen-akun--token-harvesting)
6. [Cara Sambungkan ke 9Router](#6-cara-sambungkan-ke-9router)
7. [Contoh Pemanggilan API](#7-contoh-pemanggilan-api)
8. [Daftar Model yang Didukung](#8-daftar-model-yang-didukung)

---

## Opsi 1: Deploy Langsung ke Cloudflare Workers (Wrangler / Serverless)

Mode paling praktis tanpa butuh server/VPS dan tanpa perlu relay terpisah.

1. Clone repo:
   ```bash
   git clone https://github.com/TPPReborn/freebuff2api.git
   cd freebuff2api
   ```

2. Edit `wrangler.toml`:
   ```toml
   name = "freebuff2api"
   main = "worker.js"
   compatibility_date = "2024-01-01"

   [vars]
   API_KEY = "freebuff-default-key"
   FREEBUFF_DEBUG = "false"
   RELAY_URL = "" # Biarkan kosong karena worker sudah berada di Cloudflare US Edge!
   
   # Isi authToken hasil panen:
   FREEBUFF_TOKEN = """
   token_akun_1
   token_akun_2
   """
   ```

3. Deploy ke Cloudflare:
   ```bash
   CLOUDFLARE_API_TOKEN="your-cf-token" npx wrangler deploy
   ```

4. Endpoint siap digunakan:
   - Chat: `https://freebuff2api.<your-subdomain>.workers.dev/v1/chat/completions`
   - Cek Status Akun: `https://freebuff2api.<your-subdomain>.workers.dev/v1/accounts`

---

## Opsi 2: Deploy Menggunakan Docker Compose (VPS / Server)

1. Deploy relay Cloudflare (untuk bypass geo-block jika VPS di luar US):
   ```bash
   cd relay
   CLOUDFLARE_API_TOKEN="your-cf-token" npx wrangler deploy --name freebuff-relay-us
   cd ..
   ```

2. Tempatkan file JSON token di `./credentials/` (misal: `acc1.json`, `acc2.json`).

3. Jalankan container:
   ```bash
   docker compose up -d --build
   ```

4. Endpoint API aktif di: `http://<ip-vps>:8787/v1/chat/completions`

---

## Opsi 3: Deploy Native di Linux / Termux Android

Mode ini sangat ringan dan bisa dijalankan langsung di smartphone Android via **Termux** atau di VPS tanpa Docker.

### A. Di Termux (Android):

1. Buka Termux dan jalankan one-line installer:
   ```bash
   pkg update -y && pkg install -y git nodejs
   git clone https://github.com/TPPReborn/freebuff2api.git
   cd freebuff2api
   chmod +x start.sh termux-install.sh
   ```

2. Salin file environment:
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` jika ingin mengganti PORT, API_KEY, atau RELAY_URL)*

3. Masukkan file JSON token ke folder `./credentials/` (atau buat file `acc1.json` yang berisi `{"authToken": "token_anda"}`).

4. Jalankan gateway:
   ```bash
   ./start.sh
   ```
   Server aktif di `http://localhost:8787` (bisa diakses oleh aplikasi lokal Android, Cursor, atau NextChat).

---

### B. Di Linux Native / VPS (Tanpa Docker):

```bash
git clone https://github.com/TPPReborn/freebuff2api.git
cd freebuff2api
cp .env.example .env
npm start
```

---

## 4. Cara Cek Status & AccessTier Akun

Freebuff2API menyediakan endpoint bawaan untuk melihat status seluruh akun, `accessTier` (`full` / `standard`), dan kuota pool:

```bash
curl http://localhost:8787/v1/accounts \
  -H "Authorization: Bearer freebuff-default-key"
```

**Contoh Response JSON:**
```json
{
  "summary": {
    "total_accounts": 10,
    "full_tier_accounts": 10,
    "active_rate_limited": 0
  },
  "accounts": [
    {
      "slot": "1/10",
      "token": "76b8300d...e9c6",
      "accessTier": "full",
      "status": "active",
      "pool": "Premium",
      "rateLimit": {
        "model": "deepseek/deepseek-v4-flash",
        "limit": 5,
        "pool": "premium"
      },
      "inCooldown": false,
      "cooldownRemainingSeconds": 0
    }
  ]
}
```

---

## 5. Cara Login & Panen Akun (Token Harvesting)

Freebuff2API menyediakan **2 Cara Login / Ambil Token**:

### Cara A: Login Ringan di Termux / Native (Tanpa Playwright / Zero Dependencies)

Sangat cocok untuk pengguna **Termux Android** atau VPS tanpa browser GUI:

```bash
# Menggunakan Node.js langsung (Bawaan repo):
npm run login

# Atau menggunakan Python:
python3 tools/login_cli.py
```

**Alur Kerja:**
1. Script menampilkan link login dan otomatis membuka browser di HP Anda (via `termux-open-url`).
2. Anda cukup klik **Continue with Google** dan login seperti biasa di Chrome HP.
3. Begitu selesai di browser, script di Termux langsung menangkap `authToken` dan menyimpannya ke `credentials/<email>.json`.

---

### Cara B: Automated Playwright Harvester (Multi-Akun Batch)

Cocok untuk VPS / Komputer dengan banyak akun:

1. Siapkan file akun `accounts.txt` dengan format `email|password` per baris:
   ```text
   user1@dewaa.id|Password123##
   user2@dewaa.id|Password123##
   ```

2. Jalankan automated harvester sesuai kebutuhan:

   **A. Simpan ke JSON credentials:**
   ```bash
   python3 tools/harvest_accounts.py --file accounts.txt --out ./credentials
   ```

   **B. Auto-Sync ke Cloudflare Workers (Wrangler):**
   ```bash
   # Otomatis update FREEBUFF_TOKEN di wrangler.toml & deploy langsung ke Cloudflare:
   python3 tools/harvest_accounts.py --file accounts.txt --deploy-wrangler
   ```

   **C. Auto-Reload Docker Container:**
   ```bash
   # Otomatis restart container Docker setelah selesai panen:
   python3 tools/harvest_accounts.py --file accounts.txt --reload-docker
   ```

---

## 6. Cara Sambungkan ke 9Router

Freebuff2API dapat didaftarkan sebagai custom provider di [9Router](https://github.com/TPPReborn/9router):

### Melalui Web UI 9Router:
1. Buka dashboard 9Router -> Menu **Providers** -> **Add Provider**.
2. Pilih **OpenAI Compatible**:
   - **Provider Name**: `Freebuff`
   - **Base URL**: `http://127.0.0.1:8787/v1` (atau URL Cloudflare Worker)
   - **API Key**: `freebuff-default-key`
   - **Prefix**: `fbv`
3. Tambahkan model: `deepseek/deepseek-v4-flash`, `deepseek/deepseek-v4-pro`, dll.
4. Model sekarang bisa diakses di 9Router via `fbv/deepseek/deepseek-v4-flash` (support text + vision multimodal).

---

## 7. Contoh Pemanggilan API

### A. OpenAI Chat Format (`/v1/chat/completions`)
```bash
curl http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer freebuff-default-key" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [{"role": "user", "content": "Halo! Siapa kamu?"}]
  }'
```

### B. Vision / Multimodal (Kirim Gambar)
```bash
curl http://localhost:8787/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer freebuff-default-key" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Jelaskan gambar ini"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}}
      ]
    }]
  }'
```

---

## 8. Daftar Model yang Didukung

- `deepseek/deepseek-v4-flash` *(Default, sangat cepat, vision support, kuota besar)*
- `deepseek/deepseek-v4-pro` *(Heavy reasoning)*
- `openai/gpt-5.6-luna`
- `minimax/minimax-m3`
- `crof/kimi-k3-eco`
- `mimo/mimo-v2.5`

---

## 🛡️ License

MIT License © 2026 [TPPReborn](https://github.com/TPPReborn)
