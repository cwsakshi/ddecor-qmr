"""
app.py
──────
D Decor — Quality Management & Reporting System
Production-grade Streamlit application.

Run:  streamlit run app.py
"""

import os
import io
from datetime import datetime

import pandas as pd
import streamlit as st

from data_loader import (
    COMPLAINT_TYPES,
    DEPARTMENTS,
    DEMO_USERS,
    add_row_to_csv,
    complaint_timeline,
    department_scorecard,
    load_alarm_log,
    load_all_big_customers,
    load_big_customers,
    log_alarm,
    make_excel_bytes,
    save_big_customers,
    weekly_report_stats,
    load_common,
)
from email_sender import (
    build_alarm_email,
    build_report_email,
    send_email,
)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="D Decor | QMR System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── GLOBAL CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── reset & base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
.main { background: #f4f6fa !important; }
.block-container { padding: 1.5rem 2rem 2rem !important; }

/* ── sidebar ── */
[data-testid="stSidebar"] {
  background: #0d1b38 !important;
  border-right: 1px solid #1e3a6e;
}
[data-testid="stSidebar"] * { color: #c8d8f0 !important; }
[data-testid="stSidebar"] .sidebar-brand {
  font-size: 1.1rem; font-weight: 700; color: white !important;
  letter-spacing: -0.01em;
}
[data-testid="stSidebar"] hr { border-color: #1e3a6e !important; }
[data-testid="stSidebar"] .stRadio label {
  font-size: 0.87rem !important; padding: 6px 0 !important;
}
[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] {
  border-radius: 6px; padding: 2px 8px;
}

/* ── page header ── */
.page-header {
  background: linear-gradient(135deg, #0d1b38 0%, #1B4F8A 100%);
  color: white; padding: 22px 28px; border-radius: 12px;
  margin-bottom: 22px; box-shadow: 0 4px 20px rgba(27,79,138,0.25);
}
.page-header h1 { margin: 0; font-size: 1.45rem; font-weight: 700; }
.page-header p  { margin: 5px 0 0; font-size: 0.83rem; opacity: 0.78; }

/* ── section titles ── */
.section-title {
  font-size: 0.95rem; font-weight: 700; color: #0d1b38;
  padding-bottom: 8px; border-bottom: 2px solid #e2e8f0;
  margin: 18px 0 14px;
}

/* ── KPI metric cards ── */
div[data-testid="metric-container"] {
  background: white; border-radius: 10px; padding: 14px 16px !important;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* ── alarm cards ── */
.alarm-card {
  background: white; border-radius: 10px; border-left: 5px solid #dc3545;
  padding: 12px 16px; margin-bottom: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.alarm-card:hover { box-shadow: 0 3px 12px rgba(220,53,69,0.12); }
.alarm-card.amber { border-left-color: #f59e0b; }
.alarm-card.blue  { border-left-color: #3b82f6; }
.alarm-title        { font-weight: 600; color: #dc3545; font-size: 0.87rem; }
.alarm-title.amber  { color: #b45309; }
.alarm-detail       { font-size: 0.77rem; color: #64748b; margin-top: 3px; }

/* ── dept segment cards ── */
.seg-card {
  background: white; border-radius: 10px; padding: 14px;
  border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  margin-bottom: 8px;
}

/* ── scorecard bar ── */
.score-bar-wrap {
  background: #e2e8f0; border-radius: 99px; height: 8px;
  overflow: hidden; margin: 6px 0 2px;
}
.score-bar-fill {
  height: 100%; border-radius: 99px;
  transition: width 0.5s ease;
}

/* ── timeline ── */
.timeline-step {
  display: flex; align-items: flex-start; gap: 12px;
  margin-bottom: 16px;
}
.timeline-dot {
  width: 14px; height: 14px; border-radius: 50%;
  flex-shrink: 0; margin-top: 3px;
}
.timeline-line {
  width: 2px; height: 28px; background: #e2e8f0;
  margin-left: 6px; flex-shrink: 0;
}

/* ── form error / success ── */
.form-error {
  background: #fff5f5; border: 1px solid #fecaca; border-left: 4px solid #dc3545;
  padding: 10px 14px; border-radius: 8px; color: #991b1b;
  font-size: 0.85rem; margin: 8px 0;
}
.form-success {
  background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #10b981;
  padding: 10px 14px; border-radius: 8px; color: #065f46;
  font-size: 0.85rem; margin: 8px 0;
}

/* ── login card ── */
.login-card {
  max-width: 420px; margin: 80px auto; background: white;
  border-radius: 16px; padding: 40px 36px;
  box-shadow: 0 8px 40px rgba(13,27,56,0.14);
}

/* ── badge ── */
.badge-red {
  background: #dc3545; color: white; font-size: 0.72rem;
  font-weight: 700; padding: 2px 8px; border-radius: 99px;
  display: inline-block; margin-left: 6px;
}

/* ── table styling ── */
[data-testid="stDataFrame"] { border-radius: 10px !important; overflow: hidden; }

/* ── notification toast ── */
.toast-success {
  position: fixed; bottom: 28px; right: 28px;
  background: #10b981; color: white; padding: 12px 20px;
  border-radius: 10px; font-size: 0.87rem; font-weight: 600;
  box-shadow: 0 4px 20px rgba(16,185,129,0.35);
  z-index: 9999; animation: fadeInUp 0.3s ease;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* ── responsive ── */
@media (max-width: 768px) {
  .block-container { padding: 1rem !important; }
  .page-header { padding: 16px 18px; }
  .page-header h1 { font-size: 1.1rem; }
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALISATION
# ══════════════════════════════════════════════════════════════════════════════

def _init_session():
    """Initialise all session-state keys on first run."""
    defaults = {
        "logged_in":   False,
        "username":    "",
        "show_toast":  False,
        "toast_msg":   "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════

def show_login():
    """Render a clean login page. Returns True if login is successful."""
    # Centre the card with columns
    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        st.markdown("""
        <div class="login-card">
          <div style="text-align:center;margin-bottom:28px;">
            <div style="font-size:2.4rem;">🏭</div>
            <div style="font-size:1.35rem;font-weight:700;color:#0d1b38;margin-top:6px;">
              D Decor
            </div>
            <div style="font-size:0.85rem;color:#64748b;margin-top:4px;">
              Quality Management & Reporting System
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        login_btn = st.button("🔐 Sign In", use_container_width=True, type="primary")

        if login_btn:
            if username in DEMO_USERS and DEMO_USERS[username] == password:
                st.session_state["logged_in"] = True
                st.session_state["username"]  = username
                st.rerun()
            else:
                st.markdown(
                    '<div class="form-error">❌ Invalid username or password. '
                    'Please try again.</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            "<div style='text-align:center;margin-top:18px;font-size:0.75rem;"
            "color:#94a3b8;'>Demo credentials — admin / ddecor2024</div>",
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING  (cached so CSV is only read once per session)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=120, show_spinner=False)
def _load_all():
    """Load and return (common_df, big_customers_dict, big_dfs_dict)."""
    big_customers = load_big_customers()
    common        = load_common()
    big_dfs       = load_all_big_customers(big_customers)
    return common, big_customers, big_dfs


# ══════════════════════════════════════════════════════════════════════════════
# SHARED HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _excel_download_btn(df: pd.DataFrame, filename: str, label: str = "📥 Export Excel"):
    """Render a styled Excel download button for any DataFrame."""
    try:
        xls = make_excel_bytes(df)
        st.download_button(
            label    = label,
            data     = xls,
            file_name= filename,
            mime     = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except Exception as e:
        st.error(f"Export failed: {e}")


def _display_table(df: pd.DataFrame, height: int = 400):
    """Render a sortable dataframe with consistent styling."""
    st.dataframe(df.reset_index(drop=True), use_container_width=True, height=height)


def _score_color(score: int) -> str:
    """Return a hex colour based on quality score band."""
    if score >= 75:
        return "#10b981"   # green
    elif score >= 50:
        return "#f59e0b"   # amber
    return "#dc3545"       # red


def _score_bar(score: int) -> str:
    """Return HTML for a visual score progress bar."""
    color = _score_color(score)
    return f"""
    <div class="score-bar-wrap">
      <div class="score-bar-fill" style="width:{score}%;background:{color};"></div>
    </div>
    <div style="font-size:0.72rem;color:#94a3b8;">{score}/100</div>"""


def _toast(msg: str):
    """Show a success toast that auto-disappears via JS timeout."""
    st.markdown(f"""
    <div class="toast-success" id="qmr-toast">{msg}</div>
    <script>
      setTimeout(() => {{
        const t = document.getElementById('qmr-toast');
        if (t) t.style.display = 'none';
      }}, 3000);
    </script>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def _render_sidebar(active_alarms: int) -> str:
    """
    Render the sidebar navigation.
    Returns the selected view string.
    """
    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">🏭 D Decor</div>'
            '<div style="font-size:0.78rem;color:#8aa5c8;margin-bottom:4px;">'
            'Quality Management & Reporting</div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Alarm badge on sidebar
        badge_html = (
            f'<span class="badge-red">{active_alarms}</span>'
            if active_alarms > 0 else ""
        )
        st.markdown(
            f'<div style="font-size:0.78rem;color:#8aa5c8;padding-bottom:6px;">'
            f'Active Alarms {badge_html}</div>',
            unsafe_allow_html=True,
        )

        view = st.radio(
            "Navigation",
            [
                "📊  Overview",
                "📋  All Complaints",
                "➕  Add Complaint",
                "📈  Quality Dashboard",
                "📧  Email & Reports",
                "⚙️  Settings",
                "🔔  Alarm Log",
            ],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.caption(f"👤 {st.session_state['username']}")
        st.caption(f"🕒 {datetime.now().strftime('%d %b %Y %H:%M')}")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    return view


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def view_overview(common, all_big):
    """Render the Overview page with KPIs, alarms, and dept summary."""
    st.markdown(
        '<div class="page-header">'
        '<h1>📊 Overview</h1>'
        '<p>Live complaint tracking, active alarms and department status</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    # ── KPI row ───────────────────────────────────────────────────────────────
    total   = len(common) + len(all_big)
    crit    = int(common["Critical"].sum()) + (int(all_big["Critical"].sum()) if len(all_big) else 0)
    rej     = int(common["Is Rejected"].sum()) + (int(all_big["Is Rejected"].sum()) if len(all_big) else 0)
    ov      = int(common["Overdue 48h"].sum()) + (int(all_big["Overdue 48h"].sum()) if len(all_big) else 0)
    rep     = int(common["Is Repeat"].sum()) + (int(all_big["Is Repeat"].sum()) if len(all_big) else 0)
    closed  = int((common["QA decision"].str.lower() == "closed").sum())
    pending = int((common["QA decision"].str.lower() == "pending").sum())

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    c1.metric("📦 Total",        total)
    c2.metric("🔴 Critical",     crit,  delta=f"-{crit} to resolve" if crit else None, delta_color="inverse")
    c3.metric("❌ Rejected",     rej)
    c4.metric("⏰ Overdue 48h",  ov,    delta=f"needs action" if ov else None, delta_color="inverse")
    c5.metric("🔁 Repeats",      rep)
    c6.metric("✅ Closed",       closed)
    c7.metric("⏳ Pending",      pending)

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns(2)

    # ── Active Alarms ─────────────────────────────────────────────────────────
    with left:
        st.markdown('<div class="section-title">🔴 Active Alarms</div>', unsafe_allow_html=True)
        any_alarm = False

        for _, r in common[common["Overdue 48h"]].head(4).iterrows():
            any_alarm = True
            st.markdown(f"""<div class="alarm-card">
              <div class="alarm-title">⏰ 48h No Action — {r["Name"]}</div>
              <div class="alarm-detail">{r["Complaint Description"]} | {r["Dept"]} | {r["Days Open"]} days open</div>
            </div>""", unsafe_allow_html=True)

        if len(all_big):
            for _, r in all_big[all_big["Overdue 48h"]].head(2).iterrows():
                any_alarm = True
                st.markdown(f"""<div class="alarm-card">
                  <div class="alarm-title">⏰ 48h No Action — {r.get("Name","Big Customer")}</div>
                  <div class="alarm-detail">{r["Complaint Description"]} | {r["Dept"]} | {r["Days Open"]} days open</div>
                </div>""", unsafe_allow_html=True)

        for _, r in common[common["Is Rejected"]].head(3).iterrows():
            any_alarm = True
            st.markdown(f"""<div class="alarm-card">
              <div class="alarm-title">❌ Rejected — {r["Name"]}</div>
              <div class="alarm-detail">{r["Complaint Description"]} | {r["Dept"]}</div>
            </div>""", unsafe_allow_html=True)

        for _, r in (common[common["Is Repeat"]]
                     .drop_duplicates(["Name","Complaint Description"])
                     .head(3).iterrows()):
            any_alarm = True
            st.markdown(f"""<div class="alarm-card amber">
              <div class="alarm-title amber">🔁 Repeated {r["Repeat Count"]}× — {r["Name"]}</div>
              <div class="alarm-detail">{r["Complaint Description"]} | {r["Dept"]}</div>
            </div>""", unsafe_allow_html=True)

        if not any_alarm:
            st.success("✅ No active alarms — all complaints are within SLA")

    # ── Department Summary ────────────────────────────────────────────────────
    with right:
        st.markdown('<div class="section-title">📂 Department Summary</div>', unsafe_allow_html=True)

        all_df = pd.concat([
            common[["Dept","Complaint Description","Critical","QA decision"]],
            all_big[["Dept","Complaint Description","Critical","QA decision"]] if len(all_big) else pd.DataFrame()
        ])

        for dept in sorted(all_df["Dept"].dropna().unique()):
            seg    = all_df[all_df["Dept"] == dept]
            crit_s = int(seg["Critical"].sum())
            top    = seg["Complaint Description"].value_counts().idxmax() if len(seg) else "—"
            color  = "#dc3545" if crit_s > 0 else "#10b981"
            badge  = f"🔴 {crit_s} critical" if crit_s else "✅ All clear"
            st.markdown(f"""<div class="seg-card">
              <div style="display:flex;justify-content:space-between;align-items:center;">
                <div>
                  <div style="font-weight:600;color:#64748b;font-size:0.78rem;text-transform:uppercase;">{dept}</div>
                  <div style="font-size:1.8rem;font-weight:700;color:#0d1b38;line-height:1.3;">{len(seg)}</div>
                  <div style="font-size:0.76rem;color:#64748b;">Top: {top}</div>
                </div>
                <div style="font-size:0.78rem;color:{color};font-weight:700;">{badge}</div>
              </div>
            </div>""", unsafe_allow_html=True)

    # ── Critical Complaints Table ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-title">⚠️ Critical Complaint List</div>', unsafe_allow_html=True)

    try:
        cols = ["Sr no","Name","Complaint Register Date","Complaint Description","Dept","QA decision","Days Open"]
        safe_cols = [c for c in cols if c in common.columns]
        crit_mask = common["Critical"] if "Critical" in common.columns else pd.Series([True]*len(common))
        crit_df = common[crit_mask][safe_cols].copy() if safe_cols else pd.DataFrame()
        if len(all_big) and "Critical" in all_big.columns:
            safe_big = [c for c in cols if c in all_big.columns]
            crit_big = all_big[all_big["Critical"]][safe_big].copy()
            crit_df  = pd.concat([crit_df, crit_big], ignore_index=True)
        if not crit_df.empty and "Complaint Register Date" in crit_df.columns:
            crit_df["Complaint Register Date"] = pd.to_datetime(crit_df["Complaint Register Date"], errors="coerce").dt.strftime("%d %b %Y")
        if not crit_df.empty:
            _display_table(crit_df, height=300)
            col_xls, _ = st.columns([1, 5])
            with col_xls:
                _excel_download_btn(crit_df, f"DDecor_Critical_{datetime.now().strftime('%d%b%Y')}.xlsx")
        else:
            st.info("No critical complaints found.")
    except Exception as e:
        st.warning(f"Critical list error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 2 — ALL COMPLAINTS
# ══════════════════════════════════════════════════════════════════════════════

def view_all_complaints(common, big_dfs):
    """Render the All Complaints tab view with filters and export."""
    st.markdown(
        '<div class="page-header">'
        '<h1>📋 All Complaints</h1>'
        '<p>Common and big-customer complaints — filterable, sortable, exportable</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    tab_names = ["📁 Common Complaints"] + [f"⭐ {c}" for c in big_dfs.keys()]
    tabs = st.tabs(tab_names)

    def _show_complaint_tab(df: pd.DataFrame, tab_key: str):
        """Render filters, metrics, dept cards and table for one complaints tab."""
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            with c1:
                dept_opts = sorted(df["Dept"].dropna().unique().tolist())
                dept_f    = st.multiselect("Department", dept_opts, key=f"dept_{tab_key}")
            with c2:
                qa_opts = sorted(df["QA decision"].dropna().unique().tolist())
                qa_f    = st.multiselect("QA Decision", qa_opts, key=f"qa_{tab_key}")
            with c3:
                date_range = st.date_input("Date Range", value=(), key=f"dr_{tab_key}")
            with c4:
                st.markdown("<br>", unsafe_allow_html=True)
                crit_f = st.checkbox("Critical Only", key=f"crit_{tab_key}")

        d = df.copy()
        if dept_f:  d = d[d["Dept"].isin(dept_f)]
        if qa_f:    d = d[d["QA decision"].isin(qa_f)]
        if crit_f:  d = d[d["Critical"] == True]
        if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
            start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
            d = d[(d["Complaint Register Date"] >= start) & (d["Complaint Register Date"] <= end)]

        # Metrics row
        mc1,mc2,mc3,mc4,mc5 = st.columns(5)
        mc1.metric("Total",        len(d))
        mc2.metric("❌ Rejected",  int(d["Is Rejected"].sum()))
        mc3.metric("⏰ Overdue",   int(d["Overdue 48h"].sum()))
        mc4.metric("🔁 Repeats",   int(d["Is Repeat"].sum()))
        mc5.metric("✅ Accepted",  int((d["QA decision"].str.lower()=="accepted").sum()))

        st.markdown("<br>", unsafe_allow_html=True)

        # Dept segment cards
        depts = sorted(d["Dept"].dropna().unique())
        if depts:
            seg_cols = st.columns(min(len(depts), 5))
            for i, dept in enumerate(depts):
                seg    = d[d["Dept"] == dept]
                crit_s = int(seg["Critical"].sum())
                top    = seg["Complaint Description"].value_counts().idxmax() if len(seg) else "—"
                color  = "#dc3545" if crit_s > 0 else "#10b981"
                with seg_cols[i % 5]:
                    st.markdown(f"""<div class="seg-card" style="border-top:3px solid {color};">
                      <div style="font-size:0.72rem;font-weight:600;color:#64748b;text-transform:uppercase;">{dept}</div>
                      <div style="font-size:1.8rem;font-weight:700;color:{color};">{len(seg)}</div>
                      <div style="font-size:0.74rem;color:#64748b;">{top}</div>
                      {"<div style='font-size:0.72rem;color:#dc3545;font-weight:600;'>"+str(crit_s)+" critical</div>" if crit_s else ""}
                    </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        display_cols = [
            "Sr no","Name","Complaint Register Date","Complaint Description",
            "Dept","QA decision","Days Open","Is Repeat","Overdue 48h"
        ]
        disp = d[[c for c in display_cols if c in d.columns]].copy()
        disp["Complaint Register Date"] = pd.to_datetime(disp["Complaint Register Date"]).dt.strftime("%d %b %Y")
        disp["Is Repeat"]   = disp["Is Repeat"].map({True: "🔁 Yes", False: "No"})
        disp["Overdue 48h"] = disp["Overdue 48h"].map({True: "🔴 Yes", False: "No"})

        _display_table(disp)
        _excel_download_btn(
            disp, f"DDecor_Complaints_{tab_key}_{datetime.now().strftime('%d%b%Y')}.xlsx"
        )

        # ── Complaint Timeline expander ───────────────────────────────────────
        st.markdown("---")
        with st.expander("🕐 View Complaint Status Timeline"):
            if len(d) == 0:
                st.info("No complaints match the current filter.")
                return

            sr_options = d["Sr no"].astype(str).tolist()
            selected_sr = st.selectbox("Select Complaint Sr No", sr_options, key=f"tl_{tab_key}")
            sel_row = d[d["Sr no"].astype(str) == selected_sr]
            if len(sel_row):
                row = sel_row.iloc[0]
                stages = complaint_timeline(row)
                st.markdown(f"**Customer:** {row.get('Name','')} &nbsp;|&nbsp; "
                            f"**Complaint:** {row.get('Complaint Description','')} &nbsp;|&nbsp; "
                            f"**Days Open:** {row.get('Days Open','')}d")
                st.markdown("<br>", unsafe_allow_html=True)

                for i, stage in enumerate(stages):
                    dot_color = stage["color"] if stage["done"] else "#cbd5e1"
                    st.markdown(f"""
                    <div class="timeline-step">
                      <div>
                        <div class="timeline-dot" style="background:{dot_color};
                          {'box-shadow:0 0 0 3px '+stage['color']+'33;' if stage['done'] else ''}"></div>
                        {"<div class='timeline-line'></div>" if i < len(stages)-1 else ""}
                      </div>
                      <div>
                        <div style="font-weight:600;font-size:0.87rem;color:{'#0d1b38' if stage['done'] else '#94a3b8'};">
                          {stage['stage']}
                        </div>
                        <div style="font-size:0.78rem;color:#64748b;">{stage['date']}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    with tabs[0]:
        _show_complaint_tab(common, "common")

    for i, (cname, cdf) in enumerate(big_dfs.items()):
        with tabs[i + 1]:
            _show_complaint_tab(cdf, f"big_{i}")


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 3 — ADD NEW COMPLAINT
# ══════════════════════════════════════════════════════════════════════════════

def view_add_complaint(big_customers):
    """Render the Add New Complaint form with full validation."""
    st.markdown(
        '<div class="page-header">'
        '<h1>➕ Register New Complaint</h1>'
        '<p>Fill in complaint details — saves to correct file automatically</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    complaint_type = st.radio(
        "Complaint Type",
        ["📁 Common Complaint"] + [f"⭐ {c}" for c in big_customers.keys()],
        horizontal=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("complaint_form", clear_on_submit=True):
        st.markdown("#### 🏢 Customer & Order Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            country       = st.text_input("Country Code", placeholder="IN / FR / BE")
            customer_code = st.text_input("Customer Code", placeholder="20000516")
        with col2:
            customer_name = st.text_input("Customer Name *", placeholder="Company name")
            order_no      = st.text_input("Order Number", placeholder="441008548")
        with col3:
            invoice    = st.text_input("Invoice Number", placeholder="838015879")
            billing_dt = st.date_input("Billing Date")

        st.markdown("#### 🧵 Product Details")
        col4, col5, col6 = st.columns(3)
        with col4:
            item_desc = st.text_input("Item Description *", placeholder="FABRIC-140-FR")
            material  = st.text_input("Material Code", placeholder="F-354300-140-0001")
        with col5:
            batch    = st.text_input("Batch Number", placeholder="X05100218")
            grey_lot = st.text_input("Grey Lot No", placeholder="1505787")
        with col6:
            del_qty   = st.number_input("Delivery Qty (m)", min_value=0, value=0)
            net_price = st.number_input("Net Price", min_value=0.0, value=0.0)

        st.markdown("#### 📝 Complaint Details")
        col7, col8, col9 = st.columns(3)
        with col7:
            complaint_sel = st.selectbox("Complaint Description *", COMPLAINT_TYPES)
            complaint_desc = (
                st.text_input("Specify complaint", placeholder="Describe the issue")
                if complaint_sel == "Other (specify)" else complaint_sel
            )
        with col8:
            dept_sel = st.selectbox("Department *", DEPARTMENTS)
            dept = (
                st.text_input("Specify department", placeholder="Department name")
                if dept_sel == "Other (specify)" else dept_sel
            )
        with col9:
            register_date = st.date_input("Register Date", value=datetime.now())

        submitted = st.form_submit_button("💾 Register Complaint", use_container_width=True, type="primary")

    # ── Validation ────────────────────────────────────────────────────────────
    if submitted:
        errors = []
        if not customer_name.strip():
            errors.append("Customer Name is required.")
        if not item_desc.strip():
            errors.append("Item Description is required.")
        if not complaint_desc or complaint_desc.strip() == "":
            errors.append("Complaint Description is required.")
        if not dept or dept.strip() == "":
            errors.append("Department is required.")

        if errors:
            for e in errors:
                st.markdown(f'<div class="form-error">❌ {e}</div>', unsafe_allow_html=True)
            return

        # ── Build row and save ────────────────────────────────────────────────
        new_row = {
            "Complaint Register Date": register_date.strftime("%m/%d/%Y"),
            "Country": country, "Code": customer_code, "Name": customer_name,
            "Billing Dt": billing_dt.strftime("%m/%d/%Y"),
            "Item Description": item_desc, "Material": material,
            "Order": order_no, "Invoice": invoice, "Batch": batch,
            "Grey Lotno": grey_lot, "Del Qty": del_qty, "Net Price": net_price,
            "Complaint Description": complaint_desc, "Dept": dept,
            "QA decision": None, "Route cause Analysis": None, "Corrective action": None,
        }

        try:
            if complaint_type == "📁 Common Complaint":
                df_ex  = pd.read_csv("common_complaints_dummy.csv")
                new_row["Sr no"] = int(df_ex["Sr no"].max()) + 1
                ref = (f"CC/{country}/{customer_name[:10].replace(' ','_')}"
                       f"/PD/{register_date.strftime('%d%m%Y')}/{new_row['Sr no']}")
                new_row["Complaint reference no."] = ref
                add_row_to_csv("common_complaints_dummy.csv", new_row)
                _toast(f"✅ Registered — Ref: {ref}")
                st.success(f"✅ Complaint registered successfully! Ref: **{ref}**")
            else:
                cname = complaint_type.replace("⭐ ", "")
                cfile = big_customers.get(cname, "")
                if cfile and os.path.exists(cfile):
                    df_ex  = pd.read_csv(cfile)
                    sr_col = "SRNO" if "SRNO" in df_ex.columns else "Sr no"
                    last   = (df_ex[sr_col].astype(str)
                                           .str.extract(r"(\d+)")[0]
                                           .astype(float).max())
                    new_sr = f"B{int(last)+1}"
                    new_row["SRNO"]       = new_sr
                    new_row["Sr no"]      = new_sr
                    new_row["CTG RECD DATE"] = register_date.strftime("%m/%d/%Y")
                    ref = (f"CC/BE/{cname[:10].replace(' ','_')}"
                           f"/PD/{register_date.strftime('%d%m%Y')}/{new_sr}")
                    new_row["Complaint reference no."] = ref
                    add_row_to_csv(cfile, new_row)
                    _toast(f"✅ Registered for {cname} — Ref: {ref}")
                    st.success(f"✅ Registered for **{cname}** — Ref: **{ref}**")
                else:
                    st.markdown(
                        '<div class="form-error">❌ Big customer file not found. Check Settings.</div>',
                        unsafe_allow_html=True,
                    )
                    return

            st.cache_data.clear()

        except Exception as exc:
            st.markdown(
                f'<div class="form-error">❌ Save failed: {exc}</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 4 — QUALITY DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

def view_quality_dashboard(common, big_dfs):
    """Render the Quality Dashboard with scorecards and breakdowns."""
    st.markdown(
        '<div class="page-header">'
        '<h1>📈 Quality Dashboard</h1>'
        '<p>Scorecards, department breakdowns and complaint-type analysis</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    all_data = pd.concat([common] + list(big_dfs.values())) if big_dfs else common.copy()

    total    = len(all_data)
    accepted = int((all_data["QA decision"].str.lower() == "accepted").sum())
    rejected = int((all_data["QA decision"].str.lower() == "rejected").sum())
    closed   = int((all_data["QA decision"].str.lower() == "closed").sum())
    pending  = int((all_data["QA decision"].str.lower() == "pending").sum())
    resolved = accepted + closed
    acc_rate = round(accepted / total * 100) if total else 0
    rej_rate = round(rejected / total * 100) if total else 0
    avg_days = round(all_data["Days Open"].mean(), 1) if total else 0
    res_rate = round(resolved / total * 100) if total else 0

    c1,c2,c3,c4,c5 = st.columns(5)
    c1.metric("✅ Acceptance Rate",  f"{acc_rate}%",  f"{accepted} accepted")
    c2.metric("❌ Rejection Rate",   f"{rej_rate}%",  f"{rejected} rejected")
    c3.metric("⏱️ Avg Days Open",   f"{avg_days}d")
    c4.metric("📦 Resolution Rate", f"{res_rate}%",  f"{resolved} resolved")
    c5.metric("🔄 Pending",         pending)

    st.markdown("---")

    # ── Department Scorecard ──────────────────────────────────────────────────
    st.markdown('<div class="section-title">🏆 Department Quality Scorecard</div>', unsafe_allow_html=True)
    sc_df = department_scorecard(all_data)

    # Visual scorecard cards
    n_cols = min(len(sc_df), 4)
    if n_cols:
        card_cols = st.columns(n_cols)
        for i, (_, row) in enumerate(sc_df.iterrows()):
            score  = row["Score /100"]
            color  = _score_color(score)
            with card_cols[i % n_cols]:
                st.markdown(f"""
                <div class="seg-card" style="border-top:4px solid {color};text-align:center;padding:18px 12px;">
                  <div style="font-size:0.75rem;font-weight:600;color:#64748b;
                    text-transform:uppercase;margin-bottom:8px;">{row['Department']}</div>
                  <div style="font-size:2.2rem;font-weight:800;color:{color};">{score}</div>
                  {_score_bar(score)}
                  <div style="font-size:0.72rem;color:#64748b;margin-top:6px;">{row['Band']}</div>
                  <div style="font-size:0.72rem;color:#94a3b8;margin-top:4px;">
                    {row['Total']} complaints | {row['Overdue 48h']} overdue
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    _display_table(sc_df, height=280)
    _excel_download_btn(sc_df, f"DDecor_Scorecard_{datetime.now().strftime('%d%b%Y')}.xlsx")

    st.markdown("---")

    # ── Customer Quality Breakdown ────────────────────────────────────────────
    st.markdown('<div class="section-title">👥 Customer Quality Summary</div>', unsafe_allow_html=True)
    cust_rows = []
    for cust in sorted(all_data["Name"].dropna().unique()):
        seg = all_data[all_data["Name"] == cust]
        total_c = len(seg)
        acc_c   = int((seg["QA decision"].str.lower() == "accepted").sum())
        rej_c   = int((seg["QA decision"].str.lower() == "rejected").sum())
        rep_c   = int(seg["Is Repeat"].sum())
        ov_c    = int(seg["Overdue 48h"].sum())
        acc_pct = round(acc_c / total_c * 100) if total_c else 0
        top     = seg["Complaint Description"].value_counts().idxmax() if total_c else "—"
        cust_rows.append({
            "Customer":          cust,
            "Total Complaints":  total_c,
            "Accepted":          acc_c,
            "Rejected":          rej_c,
            "Repeats":           rep_c,
            "Overdue 48h":       ov_c,
            "Acceptance %":      f"{acc_pct}%",
            "Top Complaint":     top,
        })
    cust_df = pd.DataFrame(cust_rows).sort_values("Total Complaints", ascending=False)
    _display_table(cust_df.reset_index(drop=True), height=300)
    _excel_download_btn(cust_df, f"DDecor_CustomerQuality_{datetime.now().strftime('%d%b%Y')}.xlsx")

    st.markdown("---")

    # ── Complaint Type Analysis ───────────────────────────────────────────────
    st.markdown('<div class="section-title">🔍 Complaint Type Analysis</div>', unsafe_allow_html=True)
    comp_rows = []
    for comp in all_data["Complaint Description"].dropna().unique():
        seg  = all_data[all_data["Complaint Description"] == comp]
        total_c = len(seg)
        rej_c   = int((seg["QA decision"].str.lower() == "rejected").sum())
        rep_c   = int(seg["Is Repeat"].sum())
        ov_c    = int(seg["Overdue 48h"].sum())
        risk    = ("🔴 High"   if rej_c > 2 or rep_c > 3
                   else "🟡 Medium" if rep_c > 1
                   else "🟢 Low")
        comp_rows.append({
            "Complaint Type": comp,
            "Total":          total_c,
            "Rejected":       rej_c,
            "Repeats":        rep_c,
            "Overdue 48h":    ov_c,
            "Risk Level":     risk,
        })
    comp_df = pd.DataFrame(comp_rows).sort_values("Total", ascending=False)
    _display_table(comp_df.reset_index(drop=True), height=280)
    _excel_download_btn(comp_df, f"DDecor_ComplaintTypes_{datetime.now().strftime('%d%b%Y')}.xlsx")


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 5 — EMAIL & REPORTS
# ══════════════════════════════════════════════════════════════════════════════

def view_email_reports(common, big_dfs):
    """Render the Email & Reports page with preview and send functionality."""
    st.markdown(
        '<div class="page-header">'
        '<h1>📧 Email & Reports</h1>'
        '<p>Send targeted quality reports with Excel attachments via Gmail</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_form, col_prev = st.columns([1, 1])

    with col_form:
        st.markdown("**📨 Email Settings**")
        sender_email = st.text_input("Your Gmail", placeholder="your@gmail.com")
        sender_pass  = st.text_input("Gmail App Password", type="password")
        recipients   = st.text_area("Recipients (one per line)",
                            placeholder="qa.head@ddecor.com\nmanager@ddecor.com")

        st.markdown("---")
        st.markdown("**📋 Report Settings**")
        report_type = st.selectbox("Report Type", [
            "Weekly Summary Report",
            "🔴 Critical Issues Alarm",
            "❌ Rejected Complaints",
            "⏰ Overdue 48h Reminder",
            "🔁 Repeat Complaints Alert",
            "📈 Quality Report — By Department",
            "📈 Quality Report — By Customer",
            "📈 Quality Report — By Complaint Type",
        ])

        data_source = st.multiselect(
            "Include Data From",
            options=["Common Complaints"] + list(big_dfs.keys()),
            default=["Common Complaints"],
        )

        # Optional sub-filters for quality reports
        qual_filter = []
        if "Quality Report" in report_type:
            st.markdown("**🔧 Quality Report Filters**")
            if "Department" in report_type:
                qual_filter = st.multiselect(
                    "Select Departments",
                    options=sorted(common["Dept"].dropna().unique().tolist()),
                    key="dept_qual_filter",
                )
            elif "Customer" in report_type:
                qual_filter = st.multiselect(
                    "Select Customers",
                    options=sorted(common["Name"].dropna().unique().tolist()),
                    key="cust_qual_filter",
                )
            elif "Complaint Type" in report_type:
                qual_filter = st.multiselect(
                    "Select Complaint Types",
                    options=sorted(common["Complaint Description"].dropna().unique().tolist()),
                    key="comp_qual_filter",
                )

        attach_excel = st.checkbox("Attach Excel file", True)
        preview_btn  = st.button("👁️ Preview Email",    use_container_width=True)
        send_btn     = st.button("📤 Send Now",          use_container_width=True, type="primary")

    # ── Build report dataset ──────────────────────────────────────────────────
    dfs_to_include = []
    if "Common Complaints" in data_source:
        dfs_to_include.append(common)
    for cn in big_dfs:
        if cn in data_source:
            dfs_to_include.append(big_dfs[cn])
    report_df = pd.concat(dfs_to_include) if dfs_to_include else common.copy()

    # Apply report-type filter
    if "Critical"   in report_type: send_df = report_df[report_df["Critical"]]
    elif "Rejected"  in report_type: send_df = report_df[report_df["Is Rejected"]]
    elif "Overdue"   in report_type: send_df = report_df[report_df["Overdue 48h"]]
    elif "Repeat"    in report_type: send_df = report_df[report_df["Is Repeat"]]
    elif "Department" in report_type:
        send_df = report_df[report_df["Dept"].isin(qual_filter)] if qual_filter else report_df
    elif "Customer"  in report_type:
        send_df = report_df[report_df["Name"].isin(qual_filter)] if qual_filter else report_df
    elif "Complaint Type" in report_type:
        send_df = report_df[report_df["Complaint Description"].isin(qual_filter)] if qual_filter else report_df
    else:
        send_df = report_df

    # Build subject line
    subject_map = {
        "Critical":      "🔴 Critical Complaints Alert",
        "Rejected":      "❌ Rejected Complaints",
        "Overdue":       "⏰ Overdue 48h Reminder",
        "Repeat":        "🔁 Repeat Complaints Alert",
        "Department":    "📈 Quality Report — Department",
        "Customer":      "📈 Quality Report — Customer",
        "Complaint Type":"📈 Quality Report — Complaint Type",
    }
    subj_prefix = next((v for k, v in subject_map.items() if k in report_type), "D Decor Weekly Summary")
    subject = f"{subj_prefix} | D Decor | {datetime.now().strftime('%d %b %Y')}"

    # Build HTML body
    weekly_stats = weekly_report_stats(send_df) if "Weekly" in report_type else None
    body_html    = build_report_email(report_type, send_df, weekly_stats)

    # ── Preview ───────────────────────────────────────────────────────────────
    with col_prev:
        if preview_btn:
            st.markdown(f"**Subject:** {subject}")
            st.markdown(f"**To:** {recipients[:80]}{'…' if len(recipients)>80 else ''}")
            st.markdown(f"**Rows in report:** {len(send_df)}")
            st.components.v1.html(body_html, height=560, scrolling=True)

    # ── Send ──────────────────────────────────────────────────────────────────
    if send_btn:
        if not sender_email or not sender_pass or not recipients.strip():
            st.markdown(
                '<div class="form-error">❌ Please fill in sender email, password and at least one recipient.</div>',
                unsafe_allow_html=True,
            )
            return

        rcpt = [r.strip() for r in recipients.strip().split("\n") if r.strip()]
        try:
            excel_bytes = None
            if attach_excel:
                safe_cols = [c for c in [
                    "Name","Complaint Description","Dept","QA decision",
                    "Days Open","Corrective action"
                ] if c in send_df.columns]
                excel_bytes = make_excel_bytes(send_df[safe_cols].copy())

            send_email(
                sender_email, sender_pass, rcpt, subject, body_html,
                excel_bytes=excel_bytes,
                excel_filename=f"DDecor_{datetime.now().strftime('%d%b%Y')}.xlsx",
            )
            _toast(f"✅ Email sent to {len(rcpt)} recipient(s)")
            st.success(f"✅ Email sent successfully to {len(rcpt)} recipient(s)!")

        except smtplib.SMTPAuthenticationError:
            st.markdown(
                '<div class="form-error">❌ Gmail authentication failed. '
                'Use an <strong>App Password</strong> — Google Account → Security → App Passwords.</div>',
                unsafe_allow_html=True,
            )
        except Exception as exc:
            st.markdown(
                f'<div class="form-error">❌ Email failed: {exc}</div>',
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 6 — SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

def view_settings(big_customers):
    """Render the Settings page for big customer management."""
    st.markdown(
        '<div class="page-header">'
        '<h1>⚙️ Settings</h1>'
        '<p>Manage big customers, alarm rules and system configuration</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">⭐ Big Customer Management</div>', unsafe_allow_html=True)

    for cname, cfile in list(big_customers.items()):
        c1, c2, c3 = st.columns([3, 3, 1])
        c1.markdown(f"**{cname}**")
        c2.markdown(f"`{cfile}`  {'✅ File exists' if os.path.exists(cfile) else '❌ File not found'}")
        with c3:
            if st.button("Remove", key=f"rm_{cname}"):
                del big_customers[cname]
                save_big_customers(big_customers)
                st.cache_data.clear()
                st.rerun()

    st.markdown("---")
    st.markdown("**➕ Add New Big Customer:**")
    nc1, nc2, nc3 = st.columns([3, 3, 1])
    with nc1:
        new_cn = st.text_input("Customer Name", placeholder="ARTE INTERNATIONAL")
    with nc2:
        new_cf = st.text_input("CSV File Name", placeholder="arte_complaints.csv")
    with nc3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary"):
            if new_cn and new_cf:
                big_customers[new_cn] = new_cf
                save_big_customers(big_customers)
                st.cache_data.clear()
                st.success(f"✅ {new_cn} added!")
                st.rerun()
            else:
                st.markdown(
                    '<div class="form-error">❌ Both customer name and filename are required.</div>',
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown('<div class="section-title">⏰ Alarm Rules</div>', unsafe_allow_html=True)
    st.info("""
**Active alarm rules:**
- 🔴 **Critical** — Complaint rejected by QA
- ⏰ **Overdue** — No corrective action within 48 hours
- 🔁 **Repeat** — Same customer + same complaint type more than once

Auto-alarm background process logs all sent alarms to `alarm_log.csv`.
Run `python alarm_system.py` to start the background scheduler.
    """)

    st.markdown('<div class="section-title">🔐 Demo Credentials</div>', unsafe_allow_html=True)
    creds_df = pd.DataFrame([
        {"Username": u, "Role": ("Admin" if u == "admin" else "QA Head" if "qa" in u else "Manager")}
        for u in DEMO_USERS.keys()
    ])
    st.dataframe(creds_df, use_container_width=False)
    st.caption("Passwords are not displayed for security. Edit DEMO_USERS in data_loader.py to change them.")


# ══════════════════════════════════════════════════════════════════════════════
# VIEW 7 — ALARM LOG
# ══════════════════════════════════════════════════════════════════════════════

def view_alarm_log():
    """Render the Alarm Log page showing all historical alarm sends."""
    st.markdown(
        '<div class="page-header">'
        '<h1>🔔 Alarm Log</h1>'
        '<p>Complete history of all automated alarm emails sent</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    alarm_df = load_alarm_log()

    if len(alarm_df) == 0:
        st.info("No alarms have been sent yet. The alarm log will populate once the auto-alarm system fires.")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Alarms Sent",     len(alarm_df))
    c2.metric("Departments Alerted",   alarm_df["Department"].nunique() if len(alarm_df) else 0)
    c3.metric("Complaints Covered",    int(alarm_df["Count"].sum()) if len(alarm_df) else 0)

    st.markdown("<br>", unsafe_allow_html=True)
    _display_table(alarm_df, height=400)
    _excel_download_btn(alarm_df, f"DDecor_AlarmLog_{datetime.now().strftime('%d%b%Y')}.xlsx")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

# We need smtplib in view_email_reports — import at top was left to module level
import smtplib  # noqa: E402 — already at top of module via email_sender

def main():
    """Main application controller."""

    # ── Login gate ────────────────────────────────────────────────────────────
    if not st.session_state["logged_in"]:
        show_login()
        return

    # ── Load data (cached) ────────────────────────────────────────────────────
    with st.spinner("Loading data…"):
        common, big_customers, big_dfs = _load_all()

    # Merge all big customer dataframes for combined views
    all_big = pd.concat(list(big_dfs.values())) if big_dfs else pd.DataFrame()

    # Count active alarms for sidebar badge
    active_alarms = (
        int(common["Critical"].sum()) +
        (int(all_big["Critical"].sum()) if len(all_big) else 0)
    )

    # ── Sidebar + routing ─────────────────────────────────────────────────────
    view = _render_sidebar(active_alarms)

    if   "Overview"         in view: view_overview(common, all_big)
    elif "All Complaints"   in view: view_all_complaints(common, big_dfs)
    elif "Add Complaint"    in view: view_add_complaint(big_customers)
    elif "Quality Dashboard"in view: view_quality_dashboard(common, big_dfs)
    elif "Email"            in view: view_email_reports(common, big_dfs)
    elif "Settings"         in view: view_settings(big_customers)
    elif "Alarm Log"        in view: view_alarm_log()


if __name__ == "__main__":
    main()
