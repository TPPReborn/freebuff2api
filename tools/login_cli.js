#!/usr/bin/env node
/**
 * Zero-dependency CLI Login for Freebuff / Codebuff (Termux & Native Friendly)
 * Works out of the box in Node.js on Termux Android, Windows, Mac, and Linux!
 * Automatically syncs token to credentials/*.json and wrangler.toml
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { exec } = require('child_process');
const { syncWrangler } = require('./sync_wrangler');

const CRED_DIR = path.resolve(__dirname, '../credentials');
const WRANGLER_PATH = path.resolve(__dirname, '../wrangler.toml');

function genFingerprint() {
  return 'codebuff-cli-' + crypto.randomBytes(4).toString('hex');
}

function requestJson(url, options = {}) {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const req = https.request({
      hostname: parsed.hostname,
      port: 443,
      path: parsed.pathname + parsed.search,
      method: options.method || 'GET',
      headers: {
        'User-Agent': 'codebuff-cli/1.0.685',
        'x-freebuff-sdk-version': '0.0.141',
        'x-freebuff-client-type': 'cli',
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    }, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(data) });
        } catch (e) {
          resolve({ status: res.statusCode, data: null });
        }
      });
    });
    req.on('error', reject);
    if (options.body) req.write(JSON.stringify(options.body));
    req.end();
  });
}

function openBrowser(url) {
  const cmd = process.platform === 'android' || fs.existsSync('/data/data/com.termux')
    ? `termux-open-url "${url}"`
    : process.platform === 'darwin'
      ? `open "${url}"`
      : process.platform === 'win32'
        ? `start "${url}"`
        : `xdg-open "${url}"`;
  exec(cmd, () => {});
}

async function main() {
  const args = process.argv.slice(2);
  const autoDeploy = args.includes('--deploy') || args.includes('-d');

  if (!fs.existsSync(CRED_DIR)) fs.mkdirSync(CRED_DIR, { recursive: true });

  const fp = genFingerprint();
  console.log('==========================================');
  console.log('🔑 Freebuff CLI Login (Termux & Native)');
  console.log('==========================================');
  console.log('Menghubungkan ke Codebuff API...');

  try {
    const codeRes = await requestJson('https://www.codebuff.com/api/auth/cli/code', {
      method: 'POST',
      body: { fingerprintId: fp }
    });

    if (codeRes.status !== 200 || !codeRes.data) {
      console.log('❌ Gagal mendapatkan URL login:', codeRes.data);
      return;
    }

    const { loginUrl, fingerprintHash, expiresAt } = codeRes.data;

    console.log('\nSilakan buka link berikut di browser HP / Laptop Anda:\n');
    console.log(`👉 ${loginUrl}\n`);

    openBrowser(loginUrl);
    console.log('⏳ Menunggu login di browser (tekan Ctrl+C untuk batal)...');

    const startTime = Date.now();
    while (Date.now() - startTime < 600000) { // 10 menit
      const qs = new URLSearchParams({
        fingerprintId: fp,
        fingerprintHash,
        expiresAt: String(expiresAt)
      }).toString();

      const pollRes = await requestJson(`https://www.codebuff.com/api/auth/cli/status?${qs}`);
      if (pollRes.status === 200 && pollRes.data && pollRes.data.user) {
        const user = pollRes.data.user;
        const token = user.authToken;
        const email = user.email || 'user';
        const name = user.name || 'User';

        if (token) {
          const safeName = email.split('@')[0].replace(/\./g, '_');
          const outFile = path.join(CRED_DIR, `${safeName}.json`);
          fs.writeFileSync(outFile, JSON.stringify({
            authToken: token,
            email,
            user,
            savedAt: new Date().toISOString()
          }, null, 2));

          console.log('\n==========================================');
          console.log('✅ LOGIN BERHASIL!');
          console.log(`👤 Nama : ${name}`);
          console.log(`📧 Email: ${email}`);
          console.log(`🔑 Token: ${token.slice(0, 16)}... (tersimpan di credentials/${safeName}.json)`);
          console.log('==========================================');

          // Otomatis sinkronkan ke wrangler.toml
          syncWrangler(autoDeploy);
          return;
        }
      }

      await new Promise((r) => setTimeout(r, 2000));
    }

    console.log('\n❌ Waktu login habis (timeout).');
  } catch (e) {
    console.error('❌ Error:', e.message || e);
  }
}

main();
