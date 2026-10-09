#!/usr/bin/env python3
"""
One-time migration: pull current state from the Google Apps Script endpoint
(the SAME endpoint index.html uses today) and load it into the new FastAPI +
Postgres backend.

Run this LAST, right before cutover — the closer to switching SCRIPT_URL,
the less chance of a sale happening in the gap between migration and cutover.

Usage:
    pip install requests
    python3 migrate_from_sheet.py
"""
import requests
import sys

SHEET_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbyGNEoKRKWrkyeegdAfJfXNbqxJ5Juq_ibuoQ2MYnHl3rK-bdl5_0Wwxdw595y9ONL4/exec"
API_BASE = "https://store-api.sarwora.com"
WRITE_TOKEN = "siddhnathmahadevkijay"   # must match WRITE_TOKEN in api/.env

def main():
    print("Fetching current state from Google Sheet backend...")
    r = requests.get(SHEET_SCRIPT_URL, timeout=30)
    r.raise_for_status()
    state = r.json()

    print(f"  products:  {len(state.get('products', []))}")
    print(f"  sales:     {len(state.get('sales', []))}")
    print(f"  purchases: {len(state.get('purchases', []))}")
    print(f"  expenses:  {len(state.get('expenses', []))}")

    confirm = input("\nThis will write the above into the new backend. Continue? [y/N] ")
    if confirm.strip().lower() != "y":
        print("Aborted — nothing written.")
        sys.exit(0)

    print("Writing to the new API...")
    resp = requests.post(
        f"{API_BASE}/sync",
        json={"token": WRITE_TOKEN, "state": state},
        headers={"Content-Type": "application/json"},
        timeout=60,
    )
    result = resp.json()
    if result.get("ok"):
        print("Migration complete.")
    else:
        print("Migration FAILED:", result.get("error"))
        sys.exit(1)

    print("\nVerifying...")
    check = requests.get(f"{API_BASE}/state", timeout=30).json()
    for key in ("products", "sales", "purchases", "expenses"):
        before, after = len(state.get(key, [])), len(check.get(key, []))
        status = "OK" if before == after else "MISMATCH"
        print(f"  {key}: sent {before}, now in backend {after}  [{status}]")

if __name__ == "__main__":
    main()
