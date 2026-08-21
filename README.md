# 🚀 Freebuff2API (Codebuff OpenAI & Anthropic API Gateway)

Freebuff2API adalah gateway API berkinerja tinggi yang mengubah akun Codebuff/Freebuff menjadi endpoint yang **100% kompatibel dengan OpenAI API (`/v1/chat/completions`) dan Anthropic API (`/v1/messages`)**. 

Mendukung **2 Mode Deployment**:
1. **Direct Cloudflare Workers (Serverless / Tanpa Relay)**: Deploy langsung seluruh gateway ke Cloudflare Workers tanpa butuh VPS dan tanpa butuh relay tambahan (karena sudah otomatis jalan di Cloudflare US Edge).
2. **Self-Hosted VPS / Docker + US Relay**: Menjalankan server di VPS/Docker lokal dengan Cloudflare Worker Relay sebagai proxy egress US.

---

## 🌟 Fitur Utama

- 🔄 **OpenAI & Anthropic Compatible**: Dukungan endpoint `/v1/chat/completions`, `/v1/models`, `/v1/responses`, dan `/v1/messages`.
- ⚡ **Full Streaming Support**: Server-Sent Events (SSE) stream real-time dengan delta reasoning tokens.
- 🔀 **9Router Ready**: Sangat mudah dihubungkan ke [9Router](https://github.com/TPPReborn/9router) sebagai custom provider.
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
[Client / 9Router / Cursor] ──► [Cloudflare Worker: freebuff2api] ──► [Codebuff Upstream]
                                (Handle OpenAI/Anthropic, Pool Token,
                                 Session Cache, Direct US Egress)
```

### Opsi B: Self-Hosted VPS / Docker + US Relay Proxy
```
[Client / 9Router] ──► [VPS / Docker: freebuff2api:8787] ──► [CF Worker Relay] ──► [Codebuff Upstream]
                       (Local Credentials Pool)               (US Egress Proxy)
```

---

## 📋 Daftar Isi

1. [Opsi 1: Deploy Langsung ke Cloudflare Workers (Direct / Serverless)](#opsi-1-deploy-langsung-ke-cloudflare-workers-direct--serverless)
2. [Opsi 2: Deploy Menggunakan Docker / VPS + Relay](#opsi-2-deploy-menggunakan-docker--vps--relay)
3. [Cara Panen Akun & Token (Harvesting)](#3-cara-panen-akun--token-harvesting)
4. [Cara Sambungkan ke 9Router](#4-cara-sambungkan-ke-9router)
5. [Contoh Pemanggilan API](#5-contoh-pemanggilan-api)
6. [Daftar Model yang Didukung](#6-daftar-model-yang-didukung)

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

## 4. Cara Sambungkan ke 9Router

[9Router](https://github.com/TPPReborn/9router) adalah AI multi-provider router. Anda bisa menambahkan Freebuff2API sebagai custom provider di 9Router dengan dua cara:

### Cara A: Melalui GUI Web UI 9Router

1. Buka Web UI 9Router (misal: `http://localhost:20128`).
2. Masuk ke menu **Providers** -> Klik **Add Provider**.
3. Pilih **OpenAI Compatible**:
   - **Provider Name**: `Freebuff`
   - **Base URL**: 
     - Jika VPS/Docker: `http://127.0.0.1:8787/v1`
     - Jika Cloudflare Worker: `https://freebuff2api.<your-subdomain>.workers.dev/v1`
   - **API Key**: `freebuff-default-key` (sesuai yang diset di env/wrangler)
   - **Prefix**: `fb`
4. Di bagian **Models**, tambahkan model-model berikut:
   - `deepseek/deepseek-v4-flash`
   - `claude-3-5-sonnet-20241022`
   - `gpt-4o`
5. Simpan. Model sekarang bisa diakses melalui 9Router dengan format: `fb/deepseek/deepseek-v4-flash`.

---

### Cara B: Otomatis via Script SQLite 9Router

Jika Anda mengelola 9Router di server/VPS, Anda bisa mendaftarkan Freebuff2API langsung ke database 9Router (`~/.9router/db/data.sqlite`):

```python
import sqlite3, uuid, json

DB_PATH = "/root/.9router/db/data.sqlite"
db = sqlite3.connect(DB_PATH)

# 1. Daftarkan Provider Node
node_id = "openai-compatible-chat-" + uuid.uuid4().hex[:24]
node_data = {
    "prefix": "fb",
    "apiType": "chat",
    "baseUrl": "http://127.0.0.1:8787/v1" # atau URL Worker Cloudflare
}
db.execute("""
INSERT INTO providerNodes(id, type, name, data, createdAt, updatedAt)
VALUES (?, 'openai-compatible', 'Freebuff', ?, datetime('now'), datetime('now'))
""", (node_id, json.dumps(node_data)))

# 2. Daftarkan Connection / API Key
conn_id = "conn-" + uuid.uuid4().hex[:24]
conn_data = {
    "apiKey": "freebuff-default-key",
    "testStatus": "ok",
    "providerSpecificData": {}
}
db.execute("""
INSERT INTO providerConnections(id, provider, authType, name, priority, isActive, data, createdAt, updatedAt)
VALUES (?, ?, 'apikey', 'Default Key', 1, 1, ?, datetime('now'), datetime('now'))
""", (conn_id, node_id, json.dumps(conn_data)))

# 3. (Opsional) Buat Model Combo Alias
combos = [
    ("deepseek-v4-flash", ["fb/deepseek/deepseek-v4-flash"]),
    ("freebuff-claude", ["fb/claude-3-5-sonnet-20241022"])
]
for name, models in combos:
    combo_id = "combo-" + uuid.uuid4().hex[:24]
    db.execute("""
    INSERT OR REPLACE INTO combos(id, name, kind, models, createdAt, updatedAt)
    VALUES (?, ?, '', ?, datetime('now'), datetime('now'))
    """, (combo_id, name, json.dumps(models)))

db.commit()
db.close()
print("Berhasil menyambungkan Freebuff2API ke 9Router!")
```

---

## 5. Contoh Pemanggilan API

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
