#!/usr/bin/env python3
"""
Lightweight CLI Login for Freebuff / Codebuff (Termux & Native Friendly)
No Playwright, No Selenium, No Chromium required!
Works via standard HTTP polling and browser callback.
"""

import urllib.request
import urllib.parse
import json
import time
import os
import sys
import uuid
import subprocess

CRED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../credentials'))

def gen_fingerprint():
    return f"codebuff-cli-{uuid.uuid4().hex[:8]}"

def get_cli_code(fp):
    url = "https://www.codebuff.com/api/auth/cli/code"
    data = json.dumps({"fingerprintId": fp}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "User-Agent": "codebuff-cli/1.0.685",
        "x-freebuff-sdk-version": "0.0.141",
        "x-freebuff-client-type": "cli"
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode('utf-8'))

def poll_status(fp, fp_hash, expires_at):
    qs = urllib.parse.urlencode({
        "fingerprintId": fp,
        "fingerprintHash": fp_hash,
        "expiresAt": expires_at
    })
    url = f"https://www.codebuff.com/api/auth/cli/status?{qs}"
    req = urllib.request.Request(url, headers={
        "Content-Type": "application/json",
        "User-Agent": "codebuff-cli/1.0.685",
        "x-freebuff-sdk-version": "0.0.141",
        "x-freebuff-client-type": "cli"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except Exception:
        return 0, None

def open_url(url):
    """Try to open browser in Termux / Linux / Mac / Windows"""
    try:
        if subprocess.call(["which", "termux-open-url"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            subprocess.Popen(["termux-open-url", url])
            return True
        elif subprocess.call(["which", "xdg-open"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0:
            subprocess.Popen(["xdg-open", url])
            return True
    except Exception:
        pass
    return False

def main():
    os.makedirs(CRED_DIR, exist_ok=True)
    fp = gen_fingerprint()

    print("==========================================")
    print("🔑 Freebuff CLI Login (Termux / Lightweight)")
    print("==========================================")
    print("Menghubungkan ke Codebuff API...")

    try:
        code_data = get_cli_code(fp)
    except Exception as e:
        print(f"❌ Gagal mendapatkan URL login: {e}")
        sys.exit(1)

    login_url = code_data["loginUrl"]
    fp_hash = code_data["fingerprintHash"]
    expires_at = code_data["expiresAt"]

    print("\nSilakan buka link berikut di browser HP / Laptop Anda:\n")
    print(f"👉 {login_url}\n")

    # Auto open in Termux / OS if supported
    opened = open_url(login_url)
    if opened:
        print("🌐 Browser otomatis terbuka di HP...")

    print("⏳ Menunggu Anda login di browser (tekan Ctrl+C untuk batal)...")

    start_time = time.time()
    while time.time() - start_time < 600: # 10 menit timeout
        st, res = poll_status(fp, fp_hash, expires_at)
        if st == 200 and res and res.get('user'):
            user = res['user']
            token = user.get('authToken')
            email = user.get('email', 'unknown_user')
            name = user.get('name', 'User')

            if token:
                safe_name = email.split('@')[0].replace('.', '_')
                out_file = os.path.join(CRED_DIR, f"{safe_name}.json")
                with open(out_file, 'w') as f:
                    json.dump({
                        "authToken": token,
                        "email": email,
                        "user": user,
                        "savedAt": time.strftime("%Y-%m-%d %H:%M:%S")
                    }, f, indent=2)

                print("\n==========================================")
                print("✅ LOGIN BERHASIL!")
                print(f"👤 Nama : {name}")
                print(f"📧 Email: {email}")
                print(f"🔑 Token: {token[:16]}... (tersimpan di {out_file})")
                print("==========================================")
                return

        time.sleep(2)

    print("\n❌ Waktu login habis (timeout). Silakan ulangi.")

if __name__ == '__main__':
    main()
