#!/usr/bin/env python3
"""
Inspect credentials files and query Codebuff status via US relay proxy.
Checks: token validity, accessTier, rateLimits, and current status.
"""

import glob
import json
import os
import sys
import argparse
import urllib.request
import urllib.error

def check_account(token, relay_url):
    req_url = relay_url.rstrip('/')
    req = urllib.request.Request(req_url, headers={
        "Authorization": f"Bearer {token}",
        "x-relay-target": "https://codebuff.com",
        "x-relay-path": "/api/v1/freebuff/session",
        "x-freebuff-include-unused-rate-limits": "true"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', errors='ignore')
        return e.code, body
    except Exception as e:
        return 0, str(e)

def main():
    parser = argparse.ArgumentParser(description="Check account tokens against Codebuff API.")
    parser.add_argument("--dir", "-d", default=os.path.join(os.path.dirname(__file__), '../credentials'), help="Path to credentials directory")
    parser.add_argument("--relay", "-r", default="https://freebuff-relay-us.irvan-fbe.workers.dev", help="Relay Worker URL")
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.dir, "*.json")))
    if not files:
        print(f"No credential JSON files found in {args.dir}")
        sys.exit(0)

    print(f"Found {len(files)} credential file(s). Testing via {args.relay}...\n")
    print(f"{'EMAIL':<28} | {'ACCESSTIER':<12} | {'STATUS':<10} | {'DETAILS'}")
    print("=" * 80)

    valid_cnt = 0
    for f in files:
        with open(f) as fp:
            data = json.load(fp)
        email = data.get("email", os.path.basename(f))
        token = data.get("authToken")

        if not token:
            print(f"{email:<28} | {'MISSING':<12} | {'ERROR':<10} | No authToken in json")
            continue

        status_code, res = check_account(token, args.relay)
        if status_code == 200 and isinstance(res, dict):
            valid_cnt += 1
            tier = res.get("accessTier", "standard")
            status = res.get("status", "ready")
            rl = res.get("rateLimit", {})
            pool = rl.get("poolLabel", "")
            limit = rl.get("limit", "")
            details = f"Pool: {pool}, Limit: {limit}" if pool else "OK"
            print(f"{email:<28} | {tier:<12} | {status:<10} | {details}")
        else:
            err_msg = str(res)[:40] if res else f"HTTP {status_code}"
            print(f"{email:<28} | {'FAILED':<12} | {str(status_code):<10} | {err_msg}")

    print("=" * 80)
    print(f"SUMMARY: {valid_cnt}/{len(files)} accounts active and valid.")

if __name__ == '__main__':
    main()
