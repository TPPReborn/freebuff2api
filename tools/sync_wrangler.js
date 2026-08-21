#!/usr/bin/env node
/**
 * Sync all tokens from credentials/*.json into wrangler.toml
 * Usage: node tools/sync_wrangler.js [--deploy]
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CRED_DIR = path.resolve(__dirname, '../credentials');
const WRANGLER_PATH = path.resolve(__dirname, '../wrangler.toml');

function syncWrangler(deploy = false) {
  if (!fs.existsSync(WRANGLER_PATH)) {
    console.log(`❌ ${WRANGLER_PATH} tidak ditemukan.`);
    return;
  }

  if (!fs.existsSync(CRED_DIR)) {
    console.log(`❌ Folder ${CRED_DIR} tidak ditemukan.`);
    return;
  }

  const files = fs.readdirSync(CRED_DIR).filter(f => f.endsWith('.json'));
  const tokens = [];

  for (const f of files) {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(CRED_DIR, f), 'utf8'));
      if (data.authToken) tokens.push(data.authToken.trim());
    } catch (e) {}
  }

  if (tokens.length === 0) {
    console.log('⚠️ Tidak ada token yang ditemukan di folder credentials.');
    return;
  }

  console.log(`🔄 Menyinkronkan ${tokens.length} token ke wrangler.toml...`);
  let content = fs.readFileSync(WRANGLER_PATH, 'utf8');

  const tokensFormatted = '"""\n' + tokens.join('\n') + '\n"""';
  const pattern = /FREEBUFF_TOKEN\s*=\s*(?:"""[\s\S]*?"""|"[^"]*")/g;
  const newEntry = `FREEBUFF_TOKEN = ${tokensFormatted}`;

  if (pattern.test(content)) {
    content = content.replace(pattern, newEntry);
  } else {
    content += `\nFREEBUFF_TOKEN = ${tokensFormatted}\n`;
  }

  fs.writeFileSync(WRANGLER_PATH, content, 'utf8');
  console.log('✅ wrangler.toml berhasil di-update dengan token terbaru!');

  if (deploy) {
    console.log('\n🚀 Menjalankan wrangler deploy ke Cloudflare Workers...');
    try {
      execSync('npx wrangler deploy', {
        cwd: path.dirname(WRANGLER_PATH),
        stdio: 'inherit'
      });
      console.log('✅ Cloudflare Worker berhasil di-deploy!');
    } catch (e) {
      console.error('❌ Gagal deploy via wrangler:', e.message);
    }
  }
}

const args = process.argv.slice(2);
const shouldDeploy = args.includes('--deploy') || args.includes('-d');
syncWrangler(shouldDeploy);

module.exports = { syncWrangler };
