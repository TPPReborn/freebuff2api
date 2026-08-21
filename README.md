# 🚀 Freebuff2API (Codebuff OpenAI & Anthropic API Gateway)

Freebuff2API adalah gateway API berkinerja tinggi yang mengubah akun Codebuff/Freebuff menjadi endpoint yang **100% kompatibel dengan OpenAI API (`/v1/chat/completions`) dan Anthropic API (`/v1/messages`)**. 

Mendukung **2 Mode Deployment**:
1. **Direct Cloudflare Workers (Serverless / Tanpa Relay)**: Deploy langsung seluruh gateway ke Cloudflare Workers tanpa butuh VPS dan tanpa butuh relay tambahan (karena sudah otomatis jalan di Cloudflare US Edge).
2. **Self-Hosted VPS / Docker + US Relay**: Menjalankan server di VPS/Docker lokal dengan Cloudflare Worker Relay sebagai proxy egress US.

---

## 🌟 Fitur Utama

- 🔄 **OpenAI & Anthropic Compatible**: Dukungan endpoint `/v1/chat/completions`, `/v1/models`, `/v1/responses`, dan `/v1/messages`.
- ⚡ **Full Streaming Support**: Server-Sent Events (SSE) stream real-time dengan delta reasoning tokens.
- ☁️ **Direct Cloudflare Workers Support**: Bisa di-deploy langsung ke Cloudflare Workers (serverless, gratis, tanpa butuh relay atau VPS).
- 🛡️ **Cloudflare US Relay Proxy**: Untuk deployment VPS/Docker agar IP VPS tersamarkan dan terhindar dari geo-blocking.
- 🔄 **Multi-Relay Load Balancer**: Dukungan multi-relay Cloudflare Workers dengan mekanisme rotasi dan automatic failover.
- 👥 **Multi-Account Pool & Rotation**: Load-balancing akun secara otomatis, smart session reuse, dan isolasi akun.
- ⏱️ **Smart 429 Rate Limit Guard**: Mendeteksi waktu reset (`retryAfterMs` / `resetsAt` / `Retry-After`) dari upstream, langsung menempatkan akun ke masa cooldown tanpa spamming pembuatan session baru.
- 🤖 **Automated Playwright Harvester**: Script otomatisasi login Google (Gmail & Google Workspace for Education) untuk memanen `authToken` dan `accessTier: full`.
- 🐳 **Docker & Docker Compose Ready**: Siap dijalankan langsung di VPS manapun dengan isolasi container.

---

## 📐 Pilihan Arsitektur

### Opsi A: Direct Cloudflare Workers (Serverless — Tanpa VPS / Tanpa Relay Eksternal)
```
[Client / Cursor / NextChat] ──► [Cloudflare Worker: freebuff2api] ──► [Codebuff Upstream]
                                 (Handle OpenAI/Anthropic, Pool Token,
                                  Session Cache, Direct US Egress)
```

### Opsi B: Self-Hosted VPS / Docker + US Relay Proxy
```
[Client] ──► [VPS / Docker: freebuff2api:8787] ──► [CF Worker Relay] ──► [Codebuff Upstream]
             (Local Credentials Pool)               (US Egress Proxy)
```

---

## 📋 Daftar Isi

1. [Opsi 1: Deploy Langsung ke Cloudflare Workers (Direct / Serverless)](#opsi-1-deploy-langsung-ke-cloudflare-workers-direct--serverless)
2. [Opsi 2: Deploy Menggunakan Docker / VPS + Relay](#opsi-2-deploy-menggunakan-docker--vps--relay)
3. [Cara Panen Akun & Token (Harvesting)](#3-cara-panen-akun--token-harvesting)
4. [Contoh Pemanggilan API](#4-contoh-pemanggilan-api)
5. [Daftar Model yang Didukung](#5-daftar-model-yang-didukung)

---

## Opsi 1: Deploy Langsung ke Cloudflare Workers (Direct / Serverless)

Mode ini adalah cara paling mudah, cepat, dan **tidak membutuhkan VPS atau relay terpisah**. Gateway API langsung berjalan di jaringan edge Cloudflare.

### Langkah Deploy:

1. Clone repository:
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
   
   # Isi authToken hasil panen (bisa 1 atau banyak token dipisah newline):
   FREEBUFF_TOKEN = """
   token_akun_1
   token_akun_2
   token_akun_3
   """
   ```

3. Deploy ke Cloudflare:
   ```bash
   CLOUDFLARE_API_TOKEN="your-cf-token" npx wrangler deploy
   ```

4. Selesai! Endpoint Anda sekarang siap digunakan:
   `https://freebuff2api.<your-subdomain>.workers.dev/v1/chat/completions`

---

## Opsi 2: Deploy Menggunakan Docker / VPS + Relay

Gunakan opsi ini jika Anda ingin mengelola token di server lokal/VPS via file JSON credentials.

### Langkah 1: Deploy Relay US (Cloudflare)
```bash
cd relay
CLOUDFLARE_API_TOKEN="your-cf-token" npx wrangler deploy --name freebuff-relay-us
```

### Langkah 2: Jalankan Server via Docker Compose
1. Tempatkan file JSON token di `./credentials/` (misal: `acc1.json`, `acc2.json`).
2. Jalankan docker compose:
   ```bash
   docker compose up -d --build
   ```
3. Endpoint API aktif di: `http://<ip-vps>:8787/v1/chat/completions`

---

## 3. Cara Panen Akun & Token (Harvesting)

Freebuff2API menyertakan script harvester otomatis berbasis **Playwright** yang dapat menangani:
- Google Sign-In standar
- Google Workspace for Education (Speedbump Terms of Service & "I understand" prompt)
- OAuth Consent Page ("Izinkan / Allow")
- CLI code polling dan penyimpanan JSON otomatis.

### Cara Menggunakan Harvester:

1. Siapkan file akun `accounts.txt` dengan format `email|password` per baris:
   ```text
   user1@dewaa.id|Password123##
   user2@dewaa.id|Password123##
   ```

2. Install dependencies python:
   ```bash
   cd tools
   pip install -r requirements.txt
   playwright install chromium
   ```

3. Jalankan automated harvester:
   ```bash
   python3 harvest_accounts.py --file accounts.txt --out ../credentials
   ```

4. Cek validitas dan status `accessTier: full` akun:
   ```bash
   python3 check_accounts.py --relay https://freebuff-relay-us.your-subdomain.workers.dev
   ```

---

## 4. Contoh Pemanggilan API

### A. OpenAI Format (`/v1/chat/completions`)

```bash
curl https://freebuff2api.your-subdomain.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer freebuff-default-key" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [
      {"role": "user", "content": "Halo! Siapa kamu?"}
    ],
    "stream": false
  }'
```

### B. Streaming Response (SSE)

```bash
curl https://freebuff2api.your-subdomain.workers.dev/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer freebuff-default-key" \
  -d '{
    "model": "deepseek/deepseek-v4-flash",
    "messages": [
      {"role": "user", "content": "Tuliskan puisi pendek tentang alam"}
    ],
    "stream": true
  }'
```

### C. Anthropic Format (`/v1/messages`)

```bash
curl https://freebuff2api.your-subdomain.workers.dev/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: freebuff-default-key" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "messages": [
      {"role": "user", "content": "Hello Claude!"}
    ],
    "max_tokens": 1024
  }'
```

---

## 5. Daftar Model yang Didukung

- `deepseek/deepseek-v4-flash` *(Default, sangat cepat & hemat kuota)*
- `deepseek/deepseek-chat`
- `deepseek/deepseek-reasoner`
- `claude-3-5-sonnet-20241022` / `anthropic/claude-3.5-sonnet`
- `claude-3-5-haiku-20241022`
- `gpt-4o` / `openai/gpt-4o`
- `gpt-4o-mini`
- `qwen/qwen-2.5-coder-32b-instruct`

---

## 🛡️ License

MIT License © 2026 [TPPReborn](https://github.com/TPPReborn)
