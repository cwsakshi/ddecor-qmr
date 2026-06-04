"""
data_loader.py
──────────────
Centralised data loading and processing for the D Decor QMR system.
All CSV reads, computed columns, and helper I/O live here so the UI
files stay thin and readable.
"""

import os
import json
import io
import pandas as pd
from datetime import datetime

# ── PATH HELPER ───────────────────────────────────────────────────────────────
# Ensures CSV files are always found regardless of server working directory
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def _path(filename: str) -> str:
    """Return absolute path to a file in the same folder as data_loader.py."""
    if os.path.isabs(filename):
        return filename
    return os.path.join(_BASE_DIR, filename)


# ── CONSTANTS ─────────────────────────────────────────────────────────────────

BIG_CUSTOMERS_FILE = "big_customers_config.json"
ALARM_LOG_FILE     = "alarm_log.csv"
ALERTED_FILE       = "alerted_complaints.json"

COMPLAINT_TYPES = [
    "Multiple defects", "Faceside out", "Appearance change",
    "Rubbing Fastness issue", "Pilling issue", "Shade variation",
    "Weight deviation", "Shrinkage after washing",
    "Contamination yarn", "Pressure marks", "Holes", "Other (specify)"
]

DEPARTMENTS = [
    "QA", "Packing", "Yarn process", "fabric dyeing",
    "Fabric testing lab", "Yarn dyeing", "Yarn", "Other (specify)"
]

# Demo login credentials (hardcoded for demo only)
DEMO_USERS = {
    "admin":   "ddecor2024",
    "qa_head": "quality123",
    "manager": "manager@123",
}


# ── BIG CUSTOMER CONFIG ───────────────────────────────────────────────────────

def load_big_customers() -> dict:
    """Load the big_customers_config.json mapping {customer_name: csv_filepath}."""
    if os.path.exists(_path(BIG_CUSTOMERS_FILE)):
        with open(_path(BIG_CUSTOMERS_FILE)) as f:
            return json.load(f)
    default = {"BRU TEXTILES NV": "bru_textiles_dummy.csv"}
    with open(_path(BIG_CUSTOMERS_FILE), "w") as f:
        json.dump(default, f)
    return default


def save_big_customers(data: dict) -> None:
    """Persist the big customer config dict back to JSON."""
    with open(_path(BIG_CUSTOMERS_FILE), "w") as f:
        json.dump(data, f, indent=2)


# ── SHARED COMPUTED COLUMNS ───────────────────────────────────────────────────

def _add_computed_columns(df: pd.DataFrame, name_fallback: str = "") -> pd.DataFrame:
    """
    Add all derived boolean/metric columns that the UI depends on.
    Called by both load_common() and load_big_customer() to avoid duplication.
    """
    if "Name" not in df.columns or df["Name"].isna().all():
        df["Name"] = name_fallback

    # Normalise QA decision
    df["QA decision"] = df["QA decision"].fillna("Pending").str.strip().str.title()

    # Days since complaint was registered
    df["Days Open"] = (
        (datetime.now() - df["Complaint Register Date"])
        .dt.days.fillna(0)
        .astype(int)
    )

    # Alarm triggers
    df["No Action"]   = df["Corrective action"].isna() & ~df["QA decision"].str.lower().isin(["closed", "accepted"])
    df["Overdue 48h"] = df["No Action"] & (df["Days Open"] >= 2)
    df["Is Rejected"] = df["QA decision"].str.lower() == "rejected"

    # Repeat complaint detection (same customer + same description > 1 time)
    df["Repeat Count"] = df.groupby(["Name", "Complaint Description"])["Complaint Description"].transform("count")
    df["Is Repeat"]    = df["Repeat Count"] > 1

    # Master critical flag
    df["Critical"] = df["Is Rejected"] | df["Overdue 48h"] | df["Is Repeat"]

    return df


# ── LOADERS ───────────────────────────────────────────────────────────────────

def load_common() -> pd.DataFrame:
    """
    Load and process common_complaints_dummy.csv.
    Returns a fully-enriched DataFrame ready for display/analysis.
    """
    try:
        df = pd.read_csv(_path("common_complaints_dummy.csv"))
        df["Complaint Register Date"] = pd.to_datetime(df["Complaint Register Date"], errors="coerce")
        df["Source"] = "Common"

        # Corrective action column may be missing in some exports
        if "Corrective action" not in df.columns:
            df["Corrective action"] = None

        df = _add_computed_columns(df)
        return df
    except Exception as e:
        # Return empty dataframe with expected schema on error
        return _empty_complaint_df()


def load_big_customer(filepath: str, customer_name: str = "") -> pd.DataFrame:
    """
    Load and process a big-customer CSV.
    Handles column-name variations between different customer exports.
    """
    try:
        df = pd.read_csv(_path(filepath))

        # ── normalise date ──
        date_col = "CTG RECD DATE" if "CTG RECD DATE" in df.columns else df.columns[2]
        df["Complaint Register Date"] = pd.to_datetime(df[date_col], errors="coerce")

        # ── normalise qa decision ──
        qa_col = next((c for c in df.columns if c.lower() == "qa decision"), None)
        df["QA decision"] = df[qa_col].fillna("Pending") if qa_col else "Pending"

        # ── normalise complaint description ──
        comp_col = next((c for c in df.columns if "complaint" in c.lower() and "desc" in c.lower()), None)
        if comp_col is None and "Complian" in df.columns:
            comp_col = "Complian"
        df["Complaint Description"] = df[comp_col] if comp_col else ""

        # ── normalise department ──
        dept_col = "Dept" if "Dept" in df.columns else None
        df["Dept"] = df[dept_col] if dept_col else "Unknown"

        # ── normalise corrective action ──
        act_col = next((c for c in df.columns if "corrective" in c.lower()), None)
        df["Corrective action"] = df[act_col] if act_col else None

        # ── normalise Sr no ──
        if "Sr no" not in df.columns:
            sr_col = "SRNO" if "SRNO" in df.columns else df.columns[0]
            df["Sr no"] = df[sr_col]

        df["Source"] = "Big Customer"
        df = _add_computed_columns(df, name_fallback=customer_name)
        return df
    except Exception:
        return _empty_complaint_df()


def load_all_big_customers(big_customers: dict) -> dict:
    """
    Load every big-customer file listed in the config.
    Returns {customer_name: DataFrame}.
    """
    result = {}
    for cname, cfile in big_customers.items():
        if os.path.exists(_path(cfile)):
            result[cname] = load_big_customer(cfile, customer_name=cname)
    return result


def _empty_complaint_df() -> pd.DataFrame:
    """Return an empty DataFrame with expected columns to prevent KeyErrors downstream."""
    cols = [
        "Sr no", "Complaint reference no.", "Complaint Register Date",
        "Country", "Code", "Name", "Item Description", "Order", "Invoice",
        "Del Qty", "Net Price", "Complaint Description", "Dept",
        "QA decision", "Route cause Analysis", "Corrective action",
        "Days Open", "No Action", "Overdue 48h", "Is Rejected",
        "Repeat Count", "Is Repeat", "Critical", "Source"
    ]
    return pd.DataFrame(columns=cols)


# ── QUALITY SCORECARD ─────────────────────────────────────────────────────────

def compute_quality_score(df: pd.DataFrame) -> int:
    """
    Compute a quality score 0–100 for a group of complaints.

    Formula:
        acceptance_rate  × 0.50   (50 pts max)
      + (1 - overdue_rate) × 0.30   (30 pts max)
      + (1 - repeat_rate)  × 0.20   (20 pts max)
    """
    total = len(df)
    if total == 0:
        return 100  # no complaints = perfect score

    accepted     = int((df["QA decision"].str.lower() == "accepted").sum())
    overdue      = int(df["Overdue 48h"].sum())
    repeats      = int(df["Is Repeat"].sum())

    acc_rate     = accepted / total
    overdue_rate = overdue  / total
    repeat_rate  = repeats  / total

    score = (acc_rate * 50) + ((1 - overdue_rate) * 30) + ((1 - repeat_rate) * 20)
    return max(0, min(100, round(score)))


def department_scorecard(all_data: pd.DataFrame) -> pd.DataFrame:
    """
    Build a per-department quality scorecard DataFrame with score out of 100.
    """
    rows = []
    for dept in sorted(all_data["Dept"].dropna().unique()):
        seg       = all_data[all_data["Dept"] == dept]
        total     = len(seg)
        accepted  = int((seg["QA decision"].str.lower() == "accepted").sum())
        rejected  = int((seg["QA decision"].str.lower() == "rejected").sum())
        overdue   = int(seg["Overdue 48h"].sum())
        repeats   = int(seg["Is Repeat"].sum())
        score     = compute_quality_score(seg)
        top_issue = seg["Complaint Description"].value_counts().idxmax() if total else "—"

        # Score badge text and colour
        if score >= 75:
            band = "🟢 Good"
        elif score >= 50:
            band = "🟡 Average"
        else:
            band = "🔴 Poor"

        rows.append({
            "Department":     dept,
            "Score /100":     score,
            "Band":           band,
            "Total":          total,
            "Accepted":       accepted,
            "Rejected":       rejected,
            "Overdue 48h":    overdue,
            "Repeats":        repeats,
            "Top Issue":      top_issue,
        })
    return pd.DataFrame(rows).sort_values("Score /100", ascending=True)


# ── WEEKLY REPORT HELPERS ─────────────────────────────────────────────────────

def weekly_report_stats(all_data: pd.DataFrame) -> dict:
    """
    Compute stats needed for the weekly summary email/report section.
    Returns a dict with top5_issues, top3_customers, worst_departments.
    """
    top5_issues = (
        all_data["Complaint Description"]
        .value_counts()
        .head(5)
        .reset_index()
        .rename(columns={"index": "Complaint", "count": "Count", "Complaint Description": "Complaint"})
    )

    top3_customers = (
        all_data.groupby("Name")
        .size()
        .reset_index(name="Complaints")
        .sort_values("Complaints", ascending=False)
        .head(3)
    )

    dept_rej = (
        all_data[all_data["Is Rejected"]]
        .groupby("Dept")
        .size()
        .reset_index(name="Rejections")
        .sort_values("Rejections", ascending=False)
        .head(3)
    )

    return {
        "top5_issues":       top5_issues,
        "top3_customers":    top3_customers,
        "worst_departments": dept_rej,
    }


# ── ALARM LOG ─────────────────────────────────────────────────────────────────

def log_alarm(department: str, count: int, email_sent_to: str) -> None:
    """
    Append a row to alarm_log.csv recording when an alarm was sent.
    Creates the file with headers if it does not exist yet.
    """
    row = {
        "Timestamp":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Department":   department,
        "Count":        count,
        "Email Sent To": email_sent_to,
    }
    if os.path.exists(_path(ALARM_LOG_FILE)):
        df = pd.read_csv(_path(ALARM_LOG_FILE))
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    else:
        df = pd.DataFrame([row])
    df.to_csv(_path(ALARM_LOG_FILE), index=False)


def load_alarm_log() -> pd.DataFrame:
    """Load the alarm log CSV, returning empty DataFrame if not found."""
    try:
        if os.path.exists(_path(ALARM_LOG_FILE)):
            return pd.read_csv(_path(ALARM_LOG_FILE))
        return pd.DataFrame(columns=["Timestamp", "Department", "Count", "Email Sent To"])
    except Exception:
        return pd.DataFrame(columns=["Timestamp", "Department", "Count", "Email Sent To"])


# ── COMPLAINT TIMELINE ────────────────────────────────────────────────────────

def complaint_timeline(row: pd.Series) -> list[dict]:
    """
    Given a complaint row, return an ordered list of timeline stages
    with elapsed-days information for the status timeline view.
    """
    reg_date = pd.to_datetime(row.get("Complaint Register Date"), errors="coerce")
    now      = datetime.now()
    stages   = []

    # Stage 1 — Registered (always present)
    stages.append({
        "stage":    "Registered",
        "date":     reg_date.strftime("%d %b %Y") if pd.notna(reg_date) else "—",
        "days_ago": (now - reg_date).days if pd.notna(reg_date) else None,
        "done":     True,
        "color":    "#3b82f6",
    })

    # Stage 2 — Corrective Action taken
    action = row.get("Corrective action") or row.get("Route cause Analysis")
    has_action = pd.notna(action) and str(action).strip() not in ("", "nan")
    stages.append({
        "stage": "Corrective Action",
        "date":  str(action)[:40] if has_action else "Pending",
        "done":  has_action,
        "color": "#10b981" if has_action else "#f59e0b",
    })

    # Stage 3 — QA Decision
    qa_dec = str(row.get("QA decision", "Pending")).strip()
    qa_done = qa_dec.lower() not in ("pending", "nan", "")
    stages.append({
        "stage": "QA Decision",
        "date":  qa_dec,
        "done":  qa_done,
        "color": "#10b981" if qa_dec.lower() in ("accepted", "closed") else (
                 "#dc3545" if qa_dec.lower() == "rejected" else "#f59e0b"),
    })

    # Stage 4 — Closed
    is_closed = qa_dec.lower() in ("closed", "accepted")
    stages.append({
        "stage": "Closed / Resolved",
        "date":  "Resolved" if is_closed else "Open",
        "done":  is_closed,
        "color": "#10b981" if is_closed else "#94a3b8",
    })

    return stages


# ── FILE I/O HELPERS ─────────────────────────────────────────────────────────

def add_row_to_csv(filepath: str, new_row: dict) -> None:
    """Append a single dict as a new row to an existing CSV file."""
    df = pd.read_csv(_path(filepath))
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(_path(filepath), index=False)


def make_excel_bytes(df: pd.DataFrame, sheet_name: str = "Complaints") -> bytes:
    """
    Serialise a DataFrame to a styled .xlsx file in memory.
    Returns raw bytes for st.download_button.
    """
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        wb = writer.book
        ws = writer.sheets[sheet_name]

        hdr_fmt = wb.add_format({
            "bold": True, "bg_color": "#0f2044",
            "font_color": "white", "border": 1, "text_wrap": True,
        })
        alt_fmt = wb.add_format({"bg_color": "#f0f4ff"})

        for ci, col in enumerate(df.columns):
            ws.write(0, ci, col, hdr_fmt)
            col_width = max(len(str(col)) + 4, 14)
            ws.set_column(ci, ci, col_width)

        # Alternate row shading
        for ri in range(1, len(df) + 1):
            if ri % 2 == 0:
                ws.set_row(ri, None, alt_fmt)

    buf.seek(0)
    return buf.read()
