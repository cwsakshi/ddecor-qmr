from typing import Optional, List, Dict, Set
"""
alarm_system.py
───────────────
Background auto-alarm runner for the D Decor QMR system.
Checks for overdue complaints every 10 minutes and fires department emails.
Logs every alarm sent to alarm_log.csv via data_loader.log_alarm().

Run standalone:  python alarm_system.py
"""

import os
import json
import time
import schedule
from datetime import datetime

import pandas as pd

from data_loader import (
    load_common,
    load_big_customers,
    load_big_customer,
    log_alarm,
    ALERTED_FILE,
)
from email_sender import build_alarm_email, send_email


# ── CONFIGURATION ─────────────────────────────────────────────────────────────
# Department → email mapping. Replace with real addresses in production.
DEPT_EMAILS: Dict[str, str] = {
    "QA":                 "thesakshisinghhh@gmail.com",
    "Packing":            "thesakshisinghhh@gmail.com",
    "Yarn process":       "thesakshisinghhh@gmail.com",
    "fabric dyeing":      "thesakshisinghhh@gmail.com",
    "Fabric testing lab": "thesakshisinghhh@gmail.com",
    "Yarn dyeing":        "thesakshisinghhh@gmail.com",
    "Yarn":               "thesakshisinghhh@gmail.com",
    "Other":              "thesakshisinghhh@gmail.com",
}

# Fill in before running the background alarm process
SENDER_EMAIL    = "thesakshisinghhh@gmail.com"
SENDER_PASSWORD = "yfni jlai tmal xaou"


# ── ALERTED TRACKER ───────────────────────────────────────────────────────────

def load_alerted() -> set:
    """Load the set of complaint IDs that have already been alerted today."""
    if os.path.exists(ALERTED_FILE):
        with open(ALERTED_FILE) as f:
            return set(json.load(f))
    return set()


def save_alerted(alerted: set) -> None:
    """Persist the alerted complaint IDs to JSON."""
    with open(ALERTED_FILE, "w") as f:
        json.dump(list(alerted), f)


def _complaint_id(row: pd.Series) -> str:
    """Build a unique string key for a complaint row to track de-duplication."""
    return (
        f"{row.get('Name', '')}|"
        f"{row.get('Complaint Description', '')}|"
        f"{row.get('Days Open', '')}"
    )


# ── MAIN ALARM RUNNER ─────────────────────────────────────────────────────────

def run_alarm_check() -> None:
    """
    Main alarm check function called every 10 minutes by the scheduler.
    Steps:
      1. Load all data sources.
      2. Find overdue (48h+) complaints with no corrective action.
      3. Group by department.
      4. Send one email per department (skip already-alerted groups).
      5. Log every alarm sent to alarm_log.csv.
    """
    print(f"\n[{datetime.now().strftime('%d %b %Y %H:%M')}] Running alarm check…")

    alerted     = load_alerted()
    new_alerted: set = set()

    # ── load all data ──────────────────────────────────────────────────────────
    dfs = []

    common = load_common()
    if len(common):
        dfs.append(common)

    big_customers = load_big_customers()
    for cname, cfile in big_customers.items():
        if os.path.exists(cfile):
            bc_df = load_big_customer(cfile, customer_name=cname)
            if len(bc_df):
                dfs.append(bc_df)

    if not dfs:
        print("  No data files found. Skipping.")
        return

    all_data = pd.concat(dfs, ignore_index=True)
    overdue  = all_data[all_data["Overdue 48h"] == True].copy()

    if len(overdue) == 0:
        print("  ✅ No overdue complaints. No alarms needed.")
        return

    print(f"  Found {len(overdue)} overdue complaints. Checking departments…")

    # ── send per-department alarms ─────────────────────────────────────────────
    for dept, group in overdue.groupby("Dept"):
        # Build unique IDs for this group
        complaint_ids = {_complaint_id(r) for _, r in group.iterrows()}

        # Skip if every complaint in this batch was already alerted
        if complaint_ids.issubset(alerted):
            print(f"  ⏭  {dept} — already alerted, skipping.")
            continue

        dept_email = DEPT_EMAILS.get(dept, DEPT_EMAILS["Other"])

        try:
            html = build_alarm_email(dept, group)
            subj = (
                f"⏰ ALARM: {len(group)} Overdue Complaint"
                f"{'s' if len(group) > 1 else ''} — {dept} | D Decor"
            )
            send_email(SENDER_EMAIL, SENDER_PASSWORD, [dept_email], subj, html)
            log_alarm(dept, len(group), dept_email)
            new_alerted.update(complaint_ids)
            print(f"  ✅ Alarm sent → {dept_email} for {dept} ({len(group)} complaints)")
        except Exception as exc:
            print(f"  ❌ Failed to send alarm for {dept}: {exc}")

    alerted.update(new_alerted)
    save_alerted(alerted)
    print(f"  Done. {len(new_alerted)} new complaint IDs marked alerted.")


# ── ENTRY POINT ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 52)
    print("D Decor — Auto Alarm System")
    print("Checking every 10 minutes for overdue complaints")
    print("Logs written to alarm_log.csv")
    print("=" * 52)

    # Run immediately on start, then on schedule
    run_alarm_check()
    schedule.every(10).minutes.do(run_alarm_check)

    while True:
        schedule.run_pending()
        time.sleep(60)
