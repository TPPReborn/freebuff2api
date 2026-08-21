#!/usr/bin/env python3
"""
Freebuff / Codebuff Token Harvester
Automates Google OAuth login (both standard Gmail and Google Workspace accounts),
handles speedbump/terms screens, consents, and polls the Codebuff API for authTokens.
"""

import asyncio
import os
import sys
import json
import time
import argparse
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

try:
    import requests
except ImportError:
    requests = None

CRED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../credentials'))

def gen_fingerprint():
    import uuid
    return f"fp_{uuid.uuid4().hex[:16]}"

def _http_cli_code(fingerprint_id):
    import urllib.request
    url = "https://codebuff.com/api/auth/cli/code"
    data = json.dumps({"fingerprintId": fingerprint_id}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def _http_cli_status(fingerprint_id, fp_hash, expires_at):
    import urllib.request, urllib.parse
    qs = urllib.parse.urlencode({
        "fingerprintId": fingerprint_id,
        "fingerprintHash": fp_hash,
        "expiresAt": expires_at
    })
    url = f"https://codebuff.com/api/auth/cli/status?{qs}"
    req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

async def harvest_single(p, email, password, index, total, cred_dir):
    print(f"\n[{index}/{total}] Harvesting: {email}...", flush=True)

    fp = gen_fingerprint()
    try:
        status, data = _http_cli_code(fp)
    except Exception as e:
        print(f"  [{email}] Failed to get cli code: {e}", flush=True)
        return False

    login_url = data["loginUrl"]
    fp_hash = data["fingerprintHash"]
    expires = data["expiresAt"]

    browser = await p.chromium.launch(
        headless=True,
        args=[
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-blink-features=AutomationControlled'
        ]
    )
    context = await browser.new_context(
        viewport={'width': 1280, 'height': 800},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    )
    page = await context.new_page()
    stealth = Stealth()
    await stealth.apply_stealth_async(page)

    try:
        await page.goto(login_url, wait_until='networkidle', timeout=30000)
        await page.wait_for_timeout(2000)

        # 1. Click "Continue with Google"
        g_btn = await page.wait_for_selector('button:has-text("Continue with Google"), button:has-text("Google")', timeout=10000)
        await g_btn.click()
        await page.wait_for_timeout(3000)

        # 2. Enter Email
        email_inp = await page.wait_for_selector('input#identifierId, input[name="identifier"], input[type="email"]', timeout=15000)
        await email_inp.fill(email)
        next_btn = await page.query_selector('#identifierNext, button:has-text("Next")')
        if next_btn:
            await next_btn.click()
        else:
            await page.keyboard.press('Enter')
        await page.wait_for_timeout(4000)

        # 3. Enter Password
        pwd_inp = await page.wait_for_selector('input[name="Passwd"], input[name="password"], input[type="password"]', timeout=20000)
        await pwd_inp.fill(password)
        pwd_next = await page.query_selector('#passwordNext, button:has-text("Next")')
        if pwd_next:
            await pwd_next.click()
        else:
            await page.keyboard.press('Enter')
        await page.wait_for_timeout(4000)

        # 4. Handle Speedbump / Workspace Terms / Consent Loop
        for _ in range(6):
            await page.wait_for_timeout(3000)
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                clicked = await page.evaluate('''(function(){
                    var els = Array.from(document.querySelectorAll('button, div[role="button"], a, input[type="button"]'));
                    for (var el of els) {
                        var t = (el.innerText || el.value || '').trim().toLowerCase();
                        if (t.includes('i understand') || t.includes('accept') || t.includes('saya mengerti') || 
                            t.includes('continue') || t.includes('allow') || t.includes('izinkan') || 
                            t.includes('next') || t.includes('setuju')) {
                            el.click();
                            return t;
                        }
                    }
                    return null;
                })()''')
                if clicked:
                    print(f"  [{email}] Handled prompt: '{clicked}'", flush=True)
            except Exception:
                pass

        # 5. Polling for Auth Token
        print(f"  [{email}] Polling token...", flush=True)
        for _ in range(25):
            try:
                st, res = _http_cli_status(fp, fp_hash, expires)
                if st == 200 and res and res.get('user'):
                    user = res['user']
                    token = user.get('authToken')
                    if token:
                        safe_name = email.split('@')[0]
                        out_path = os.path.join(cred_dir, f"{safe_name}.json")
                        with open(out_path, 'w') as f:
                            json.dump({
                                "authToken": token,
                                "email": email,
                                "user": user,
                                "updatedAt": time.strftime("%Y-%m-%d %H:%M:%S")
                            }, f, indent=2)
                        print(f"  [SUCCESS] {email} -> Token saved to {out_path}", flush=True)
                        return True
            except Exception:
                pass
            await asyncio.sleep(3)

        print(f"  [FAILED] {email} -> Poll timeout", flush=True)
        return False
    except Exception as e:
        print(f"  [ERROR] {email} -> {e}", flush=True)
        return False
    finally:
        await browser.close()

async def main():
    parser = argparse.ArgumentParser(description="Harvest Freebuff/Codebuff authTokens automatically.")
    parser.add_argument("--file", "-f", default="accounts.txt", help="Path to accounts file (format: email|password per line)")
    parser.add_argument("--out", "-o", default=CRED_DIR, help="Directory to save credentials json")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: Accounts file '{args.file}' not found.")
        print("Create a file with format: email|password per line")
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    lines = [l.strip() for l in open(args.file) if l.strip() and '|' in l and not l.startswith('#')]
    total = len(lines)
    print(f"Loaded {total} accounts to harvest.")

    success = 0
    async with async_playwright() as p:
        for idx, line in enumerate(lines, 1):
            email, pwd = line.split('|', 1)
            ok = await harvest_single(p, email, pwd, idx, total, args.out)
            if ok:
                success += 1
            if idx < total:
                print("  Cooldown 5s before next account...", flush=True)
                await asyncio.sleep(5)

    print(f"\n==========================================")
    print(f"HARVEST COMPLETE: {success}/{total} accounts successfully saved.")
    print(f"==========================================")

if __name__ == '__main__':
    asyncio.run(main())
