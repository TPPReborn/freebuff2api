# 🚀 Freebuff2API (Codebuff OpenAI & Anthropic API Gateway)

Freebuff2API adalah gateway API berkinerja tinggi yang mengubah akun Codebuff/Freebuff menjadi endpoint yang **100% kompatibel dengan OpenAI API (`/v1/chat/completions`) dan Anthropic API (`/v1/messages`)**. 

Dilengkapi dengan arsitektur **Multi-Account Auto Rotation**, **Cloudflare Worker US Relay Proxy**, **Smart 429 Cooldown & Rate Limit Guard**, serta **Automated Token Harvester**.

---

## 🌟 Fitur Utama

- 🔄 **OpenAI & Anthropic Compatible**: Dukungan endpoint `/v1/chat/completions`, `/v1/models`, `/v1/responses`, dan `/v1/messages`.
- ⚡ **Full Streaming Support**: Server-Sent Events (SSE) stream real-time dengan delta reasoning tokens.
- 🛡️ **Cloudflare US Relay Proxy**: Menyamarkan IP VPS/Server dan menyuntikkan signature header Codebuff CLI secara otomatis agar tidak terkena ban geo-blocking/country block.
- 🔄 **Multi-Relay Load Balancer**: Dukungan multi-relay Cloudflare Workers dengan mekanisme rotasi dan automatic failover.
- 👥 **Multi-Account Pool & Rotation**: Load-balancing akun secara otomatis, smart session reuse, dan isolasi akun.
- ⏱️ **Smart 429 Rate Limit Guard**: Mendeteksi waktu reset (`retryAfterMs` / `resetsAt` / `Retry-After`) dari upstream, langsung menempatkan akun ke masa cooldown tanpa spamming pembuatan session baru.
- 🤖 **Automated Playwright Harvester**: Script otomatisasi login Google (Gmail & Google Workspace for Education) untuk memanen `authToken` dan `accessTier: full`.
- 🐳 **Docker & Docker Compose Ready**: Siap dijalankan langsung di VPS manapun dengan isolasi container.

---

## 📐 Arsitektur Sistem

```
[Client / Cursor / NextChat / Cline]
                 │
                 ▼  (Bearer freebuff-default-key)
      ┌─────────────────────┐
      │  Freebuff2API Host  │  (Port 8787 / Docker)
      │  (Node.js Gateway)  │
      └──────────┬──────────┘
                 │
                 ├──► [Multi-Account Credential Pool] (credentials/*.json)
                 │    ├── Smart Session Cache (`sessCache`)
                 │    └── Auto-Cooldown on 429 (`parseCooldown`)
                 │
                 ▼  (Round-robin / Failover)
      ┌───────────────────────────────────────────────┐
      │  Cloudflare Worker US Relay Proxy             │
      │  - freebuff-relay-us.workers.dev             │
      │  - freebuff-relay-us2.workers.dev            │
      │  (Strip CF headers, spoof UA, inject CLI SDK) │
      └──────────────────────┬────────────────────────┘
                             │
                             ▼  (US Egress IP)
               ┌───────────────────────────┐
               │   Codebuff Upstream API   │
               │   (codebuff.com/api/v1)   │
               └───────────────────────────┘
```

---

## 📋 Daftar Isi

1. [Cara Deploy Cloudflare Worker Relay](#1-deploy-cloudflare-worker-relay)
2. [Cara Panen Akun & Token (Harvesting)](#2-panen-akun--token-harvesting)
3. [Menjalankan Server dengan Docker](#3-menjalankan-server-dengan-docker)
4. [Menjalankan Server Manual (Node.js)](#4-menjalankan-server-manual-nodejs)
5. [Contoh Pemanggilan API](#5-contoh-pemanggilan-api)
6. [Daftar Model yang Didukung](#6-daftar-model-yang-didukung)

---

## 1. Deploy Cloudflare Worker Relay

Relay worker bertindak sebagai reverse proxy yang berjalan di Cloudflare edge network (US colo) untuk memastikan semua request ke Codebuff berasal dari IP US dan memiliki header CLI yang valid.

### Langkah Deploy:

1. Masuk ke direktori relay:
   ```bash
   cd relay
   ```

2. Pastikan `wrangler` sudah terpasang:
   ```bash
   npm install -g wrangler
   ```

3. Deploy relay pertama:
   ```bash
   CLOUDFLARE_API_TOKEN="your-cf-token" wrangler deploy --name freebuff-relay-us
   ```

4. *(Opsional)* Deploy relay kedua untuk multi-relay redundancy:
   ```bash
   CLOUDFLARE_API_TOKEN="your-cf-token" wrangler deploy --name freebuff-relay-us2
   ```

---

## 2. Panen Akun & Token (Harvesting)

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

4. Cek validitas dan status `accessTier` akun:
   ```bash
   python3 check_accounts.py --relay https://freebuff-relay-us.your-subdomain.workers.dev
   ```

---

## 3. Menjalankan Server dengan Docker

### Menggunakan Docker Compose (Direkomendasikan):

1. Pastikan file credential sudah ada di folder `./credentials/*.json`.
2. Edit file `docker-compose.yml` untuk menyesuaikan URL relay dan API key:
   ```yaml
   version: '3.8'
   services:
     freebuff2api:
       build: .
       container_name: freebuff2api
       restart: unless-stopped
       ports:
         - "8787:8787"
       environment:
         - PORT=8787
         - API_KEY=freebuff-default-key
         - RELAY_URL=https://freebuff-relay-us.workers.dev,https://freebuff-relay-us2.workers.dev
         - FREEBUFF_DEBUG=false
       volumes:
         - ./credentials:/app/credentials
   ```

3. Jalankan container:
   ```bash
   docker compose up -d --build
   ```

4. Cek log server:
   ```bash
   docker compose logs -f
   ```

---

## 4. Menjalankan Server Manual (Node.js)

1. Pastikan Node.js v18+ terinstall:
   ```bash
   node -v
   ```

2. Jalankan server:
   ```bash
   export PORT=8787
   export API_KEY="freebuff-default-key"
   export RELAY_URL="https://freebuff-relay-us.workers.dev,https://freebuff-relay-us2.workers.dev"
   export FREEBUFF_CRED_DIR="./credentials"

   node server.js
   ```

---

## 5. Contoh Pemanggilan API

### A. OpenAI Format (`/v1/chat/completions`)

```bash
curl http://localhost:8787/v1/chat/completions \
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

### B. Streaming Response

```bash
curl http://localhost:8787/v1/chat/completions \
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
curl http://localhost:8787/v1/messages \
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

## 6. Daftar Model yang Didukung

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
