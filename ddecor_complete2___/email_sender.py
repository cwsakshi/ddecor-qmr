from typing import Optional, List, Tuple
"""
email_sender.py
───────────────
Corporate email templates for the D Decor QMR system.
All templates follow Fortune 500 email design standards.
Inline CSS only — renders correctly in Gmail, Outlook and mobile.
"""

import smtplib
import io
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

import pandas as pd


# ── SHARED DESIGN TOKENS ──────────────────────────────────────────────────────
_NAVY       = "#0f2044"
_BLUE       = "#1B4F8A"
_RED        = "#C0392B"
_RED_LIGHT  = "#FDECEA"
_AMBER      = "#B7770D"
_AMBER_LIGHT= "#FEF9EC"
_GREEN      = "#1A7A4A"
_GREEN_LIGHT= "#EAFAF1"
_GREY_BG    = "#F4F6F9"
_BORDER     = "#E2E8F0"
_TEXT_MAIN  = "#1A202C"
_TEXT_SUB   = "#4A5568"
_TEXT_MUTED = "#94A3B8"
_WHITE      = "#FFFFFF"


# ── SHARED LAYOUT WRAPPERS ────────────────────────────────────────────────────

def _outer_wrapper(content: str) -> str:
    """Wrap content in the standard email outer shell."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>D Decor Quality Management</title>
</head>
<body style="margin:0;padding:0;background:{_GREY_BG};
             font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:{_GREY_BG};padding:32px 16px;">
    <tr><td align="center">
      <table width="640" cellpadding="0" cellspacing="0"
             style="max-width:640px;width:100%;background:{_WHITE};
                    border-radius:12px;overflow:hidden;
                    box-shadow:0 4px 24px rgba(0,0,0,0.10);">
        {content}
      </table>
      {_outer_footer()}
    </td></tr>
  </table>
</body>
</html>"""


def _outer_footer() -> str:
    return f"""
    <p style="margin:20px 0 0;font-size:11px;color:{_TEXT_MUTED};text-align:center;
              line-height:1.6;">
      © {datetime.now().year} D Decor — Quality Management &amp; Reporting System<br>
      This is an automated message. Please do not reply directly to this email.<br>
      <span style="color:{_BORDER};">─────────────────────────────────</span><br>
      <em>This email and any attachments are confidential and intended solely
      for the addressee. If you have received this in error, please notify
      the sender immediately.</em>
    </p>"""


def _logo_bar(accent: str = _NAVY) -> str:
    """Top logo / brand bar."""
    return f"""
    <tr>
      <td style="background:{accent};padding:0;">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="padding:18px 28px;">
              <span style="font-size:13px;font-weight:700;
                           color:{_WHITE};letter-spacing:0.12em;
                           text-transform:uppercase;">D&nbsp;DECOR</span>
              <span style="font-size:11px;color:rgba(255,255,255,0.55);
                           margin-left:10px;letter-spacing:0.06em;">
                QUALITY MANAGEMENT &amp; REPORTING
              </span>
            </td>
            <td align="right" style="padding:18px 28px;">
              <span style="font-size:11px;color:rgba(255,255,255,0.55);">
                {datetime.now().strftime("%d %B %Y")}
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>"""


def _hero_banner(title: str, subtitle: str,
                 accent: str = _NAVY, icon: str = "") -> str:
    return f"""
    <tr>
      <td style="background:linear-gradient(135deg,{accent} 0%,{_BLUE} 100%);
                 padding:32px 28px;">
        <p style="margin:0 0 6px;font-size:11px;color:rgba(255,255,255,0.60);
                  text-transform:uppercase;letter-spacing:0.10em;">
          D Decor &nbsp;·&nbsp; Quality Report
        </p>
        <h1 style="margin:0;font-size:22px;font-weight:700;color:{_WHITE};
                   line-height:1.25;">
          {icon}&nbsp;{title}
        </h1>
        <p style="margin:8px 0 0;font-size:13px;color:rgba(255,255,255,0.75);
                  line-height:1.5;">{subtitle}</p>
      </td>
    </tr>"""


def _divider() -> str:
    return f"""
    <tr><td style="padding:0 28px;">
      <hr style="border:none;border-top:1px solid {_BORDER};margin:0;"/>
    </td></tr>"""


def _section_heading(text: str) -> str:
    return f"""
    <tr><td style="padding:24px 28px 8px;">
      <p style="margin:0;font-size:11px;font-weight:700;
                color:{_TEXT_SUB};text-transform:uppercase;
                letter-spacing:0.10em;">{text}</p>
    </td></tr>"""


def _kpi_row(items: List[tuple]) -> str:
    """items = [(label, value, value_color), ...]"""
    cells = ""
    for label, value, color in items:
        cells += f"""
        <td align="center" style="padding:18px 12px;
              border-right:1px solid {_BORDER};">
          <p style="margin:0;font-size:28px;font-weight:700;color:{color};
                    line-height:1;">{value}</p>
          <p style="margin:5px 0 0;font-size:10px;font-weight:600;
                    color:{_TEXT_SUB};text-transform:uppercase;
                    letter-spacing:0.08em;">{label}</p>
        </td>"""
    # Remove last border
    cells = cells.rsplit('border-right:1px solid', 1)
    cells = 'border-right:none;'.join(cells) if len(cells) > 1 else ''.join(cells)
    return f"""
    <tr><td style="padding:0 0 4px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid {_BORDER};border-radius:8px;
                    overflow:hidden;margin:0 28px;width:calc(100% - 56px);">
        <tr style="background:{_WHITE};">{cells}</tr>
      </table>
    </td></tr>"""


def _complaint_table(df: pd.DataFrame, max_rows: int = 12) -> str:
    """Render a styled complaint table."""
    rows_html = ""
    for i, (_, r) in enumerate(df.head(max_rows).iterrows()):
        if r.get("Is Rejected") or r.get("Overdue 48h"):
            row_bg = _RED_LIGHT
        elif r.get("Is Repeat"):
            row_bg = _AMBER_LIGHT
        else:
            row_bg = _WHITE if i % 2 == 0 else "#F8FAFC"

        qa   = str(r.get("QA decision", "")).strip().title()
        days = r.get("Days Open", "")
        days_color = _RED if isinstance(days, (int, float)) and days > 5 else _TEXT_MAIN

        qa_badge_color = (_GREEN_LIGHT, _GREEN) if qa.lower() in ("accepted","closed") else \
                         (_RED_LIGHT,   _RED)   if qa.lower() == "rejected"            else \
                         (_AMBER_LIGHT, _AMBER)

        rows_html += f"""
        <tr style="background:{row_bg};">
          <td style="padding:9px 12px;border-bottom:1px solid {_BORDER};
                     font-size:12px;color:{_TEXT_MAIN};font-weight:500;">
            {r.get('Name','—')}</td>
          <td style="padding:9px 12px;border-bottom:1px solid {_BORDER};
                     font-size:12px;color:{_TEXT_SUB};">
            {r.get('Complaint Description','—')}</td>
          <td style="padding:9px 12px;border-bottom:1px solid {_BORDER};
                     font-size:12px;color:{_TEXT_SUB};">
            {r.get('Dept','—')}</td>
          <td style="padding:9px 12px;border-bottom:1px solid {_BORDER};">
            <span style="background:{qa_badge_color[0]};color:{qa_badge_color[1]};
                         font-size:10px;font-weight:700;padding:2px 8px;
                         border-radius:10px;text-transform:uppercase;
                         letter-spacing:0.04em;">{qa or "Pending"}</span>
          </td>
          <td style="padding:9px 12px;border-bottom:1px solid {_BORDER};
                     font-size:12px;font-weight:700;color:{days_color};
                     text-align:right;">{days}d</td>
        </tr>"""

    overflow = ""
    if len(df) > max_rows:
        overflow = f"""
        <tr><td colspan="5" style="padding:10px 12px;font-size:11px;
                                    color:{_TEXT_MUTED};font-style:italic;
                                    background:#F8FAFC;">
          + {len(df) - max_rows} additional complaints in the attached Excel file.
        </td></tr>"""

    return f"""
    <tr><td style="padding:4px 28px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid {_BORDER};border-radius:8px;overflow:hidden;
                    font-family:'Segoe UI',Helvetica,Arial,sans-serif;">
        <tr style="background:{_NAVY};">
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Customer</th>
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Complaint</th>
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Department</th>
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Status</th>
          <th style="padding:10px 12px;text-align:right;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Days</th>
        </tr>
        {rows_html}
        {overflow}
      </table>
    </td></tr>"""


def _inline_footer(note: str = "") -> str:
    default = ("This is an automated report generated by the D Decor Quality Management System. "
               "For queries, please contact the Quality Management team.")
    return f"""
    <tr><td style="padding:16px 28px 28px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="background:#F8FAFC;border-left:3px solid {_BORDER};
                    border-radius:0 6px 6px 0;">
        <tr><td style="padding:12px 16px;">
          <p style="margin:0;font-size:11px;color:{_TEXT_MUTED};line-height:1.6;">
            {note or default}
          </p>
        </td></tr>
      </table>
    </td></tr>"""


# ── TEMPLATE 1 — WEEKLY SUMMARY REPORT ───────────────────────────────────────

def _weekly_top5(stats: dict) -> str:
    top5 = stats.get("top5_issues", pd.DataFrame())
    if top5.empty:
        return ""
    rows = ""
    for rank, (_, r) in enumerate(top5.iterrows(), 1):
        complaint = r.iloc[0]
        count     = r.iloc[1]
        bar_width = max(10, int((count / max(top5.iloc[:,1])) * 160))
        rows += f"""
        <tr>
          <td style="padding:8px 12px;font-size:12px;color:{_TEXT_MAIN};
                     font-weight:600;width:24px;">#{rank}</td>
          <td style="padding:8px 12px;font-size:12px;color:{_TEXT_SUB};">
            {complaint}</td>
          <td style="padding:8px 12px;text-align:right;">
            <span style="display:inline-block;background:{_RED};height:10px;
                         width:{bar_width}px;border-radius:2px;
                         vertical-align:middle;margin-right:8px;"></span>
            <span style="font-size:12px;font-weight:700;color:{_RED};">{count}</span>
          </td>
        </tr>"""
    return f"""
    <tr><td style="padding:4px 28px 16px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid {_BORDER};border-radius:8px;overflow:hidden;">
        <tr style="background:{_GREY_BG};">
          <th colspan="3" style="padding:10px 12px;text-align:left;font-size:10px;
                                  font-weight:700;color:{_TEXT_SUB};
                                  text-transform:uppercase;letter-spacing:0.08em;">
            Rank &nbsp;·&nbsp; Complaint Type &nbsp;·&nbsp; Volume
          </th>
        </tr>
        {rows}
      </table>
    </td></tr>"""


def _weekly_tables(stats: dict) -> str:
    top3 = stats.get("top3_customers", pd.DataFrame())
    worst = stats.get("worst_departments", pd.DataFrame())

    cust_rows = ""
    for i, (_, r) in enumerate(top3.iterrows()):
        bg = _WHITE if i % 2 == 0 else "#F8FAFC"
        cust_rows += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 12px;font-size:12px;color:{_TEXT_MAIN};">
            {r.get('Name','')}</td>
          <td style="padding:8px 12px;font-size:12px;font-weight:700;
                     color:{_AMBER};text-align:right;">
            {r.get('Complaints','')}</td>
        </tr>"""

    dept_rows = ""
    for i, (_, r) in enumerate(worst.iterrows()):
        bg = _WHITE if i % 2 == 0 else "#F8FAFC"
        dept_rows += f"""
        <tr style="background:{bg};">
          <td style="padding:8px 12px;font-size:12px;color:{_TEXT_MAIN};">
            {r.get('Dept','')}</td>
          <td style="padding:8px 12px;font-size:12px;font-weight:700;
                     color:{_RED};text-align:right;">
            {r.get('Rejections','')}</td>
        </tr>"""

    return f"""
    <tr><td style="padding:4px 28px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
          <td style="width:48%;vertical-align:top;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid {_BORDER};border-radius:8px;overflow:hidden;">
              <tr style="background:{_GREY_BG};">
                <th colspan="2" style="padding:10px 12px;text-align:left;font-size:10px;
                                       font-weight:700;color:{_TEXT_SUB};
                                       text-transform:uppercase;letter-spacing:0.08em;">
                  Top Customers by Volume
                </th>
              </tr>
              {cust_rows}
            </table>
          </td>
          <td style="width:4%;"></td>
          <td style="width:48%;vertical-align:top;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border:1px solid {_BORDER};border-radius:8px;overflow:hidden;">
              <tr style="background:{_GREY_BG};">
                <th colspan="2" style="padding:10px 12px;text-align:left;font-size:10px;
                                       font-weight:700;color:{_TEXT_SUB};
                                       text-transform:uppercase;letter-spacing:0.08em;">
                  Depts — Highest Rejections
                </th>
              </tr>
              {dept_rows}
            </table>
          </td>
        </tr>
      </table>
    </td></tr>"""


# ── PUBLIC EMAIL BUILDERS ─────────────────────────────────────────────────────

def build_report_email(
    report_type: str,
    send_df: pd.DataFrame,
    weekly_stats: Optional[dict] = None,
) -> str:
    today   = datetime.now().strftime("%d %B %Y")
    period  = f"Report Period · {today}"
    total   = len(send_df)
    crit    = int(send_df["Critical"].sum())    if "Critical"    in send_df.columns else 0
    rej     = int(send_df["Is Rejected"].sum()) if "Is Rejected" in send_df.columns else 0
    ov      = int(send_df["Overdue 48h"].sum()) if "Overdue 48h" in send_df.columns else 0

    clean   = (report_type.replace("📈 ","").replace("🔴 ","").replace("❌ ","")
                           .replace("⏰ ","").replace("🔁 ",""))

    if "Critical" in report_type or "Alarm" in report_type:
        accent, icon = _RED, "⚠"
    elif "Overdue" in report_type:
        accent, icon = "#B7770D", "⏰"
    elif "Reject" in report_type:
        accent, icon = "#7B2D2D", "✕"
    elif "Repeat" in report_type:
        accent, icon = "#4A2D82", "↺"
    else:
        accent, icon = _NAVY, "◈"

    kpi = _kpi_row([
        ("Total Complaints", total, _NAVY),
        ("Critical",         crit,  _RED),
        ("Rejected",         rej,   _RED),
        ("Overdue 48h",      ov,    _AMBER),
    ])

    inner = f"""
    {_logo_bar(accent)}
    {_hero_banner(clean, period, accent, icon)}
    {_divider()}
    {_section_heading("Summary Metrics")}
    {kpi}"""

    if "Weekly" in report_type and weekly_stats:
        inner += f"""
    {_divider()}
    {_section_heading("Top 5 Complaint Types — This Period")}
    {_weekly_top5(weekly_stats)}
    {_divider()}
    {_section_heading("Customer & Department Performance")}
    {_weekly_tables(weekly_stats)}"""

    inner += f"""
    {_divider()}
    {_section_heading("Complaint Details")}
    {_complaint_table(send_df)}
    {_inline_footer()}"""

    return _outer_wrapper(inner)


# ── TEMPLATE 2 — OVERDUE 48h ALARM ───────────────────────────────────────────

def build_alarm_email(dept: str, complaints_df: pd.DataFrame) -> str:
    today  = datetime.now().strftime("%d %B %Y · %H:%M")
    count  = len(complaints_df)
    s_pl   = "s" if count > 1 else ""

    rows_html = ""
    for i, (_, r) in enumerate(complaints_df.iterrows()):
        bg  = _WHITE if i % 2 == 0 else "#FDF5F5"
        reg = (pd.to_datetime(r.get("Complaint Register Date",""), errors="coerce")
               .strftime("%d %b %Y")
               if pd.notna(r.get("Complaint Register Date")) else "—")
        days = r.get("Days Open", "")
        rows_html += f"""
        <tr style="background:{bg};">
          <td style="padding:9px 12px;border-bottom:1px solid #FECACA;
                     font-size:12px;color:{_TEXT_MAIN};font-weight:500;">
            {r.get('Name','—')}</td>
          <td style="padding:9px 12px;border-bottom:1px solid #FECACA;
                     font-size:12px;color:{_TEXT_SUB};">
            {r.get('Complaint Description','—')}</td>
          <td style="padding:9px 12px;border-bottom:1px solid #FECACA;
                     font-size:12px;color:{_TEXT_SUB};">
            {reg}</td>
          <td style="padding:9px 12px;border-bottom:1px solid #FECACA;
                     text-align:right;">
            <span style="background:{_RED_LIGHT};color:{_RED};font-size:11px;
                         font-weight:700;padding:2px 9px;border-radius:10px;">
              {days} days
            </span>
          </td>
        </tr>"""

    inner = f"""
    {_logo_bar(_RED)}
    <tr>
      <td style="background:linear-gradient(135deg,#7B1111,{_RED});padding:32px 28px;">
        <p style="margin:0 0 4px;font-size:11px;color:rgba(255,255,255,0.60);
                  text-transform:uppercase;letter-spacing:0.10em;">
          Automated Quality Alarm · {today}
        </p>
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:{_WHITE};">
          ⏰ &nbsp;Overdue Complaint Alarm
        </h1>
        <p style="margin:0;font-size:13px;color:rgba(255,255,255,0.80);">
          Department: &nbsp;<strong>{dept}</strong>
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:24px 28px 8px;">
        <table width="100%" cellpadding="0" cellspacing="0"
               style="background:{_RED_LIGHT};border-left:4px solid {_RED};
                      border-radius:0 8px 8px 0;">
          <tr><td style="padding:14px 18px;">
            <p style="margin:0;font-size:14px;font-weight:700;color:{_RED};">
              {count} complaint{s_pl} in <em>{dept}</em> require immediate action.
            </p>
            <p style="margin:6px 0 0;font-size:12px;color:#7B2D2D;line-height:1.5;">
              These complaints have not received any corrective action within
              the required <strong>48-hour</strong> window. Please review and
              update the complaint register immediately.
            </p>
          </td></tr>
        </table>
      </td>
    </tr>
    {_section_heading("Overdue Complaints — Requiring Immediate Action")}
    <tr><td style="padding:4px 28px 20px;">
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border:1px solid #FECACA;border-radius:8px;overflow:hidden;">
        <tr style="background:{_RED};">
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Customer</th>
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Complaint</th>
          <th style="padding:10px 12px;text-align:left;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Registered</th>
          <th style="padding:10px 12px;text-align:right;font-size:10px;
                     font-weight:700;color:{_WHITE};text-transform:uppercase;
                     letter-spacing:0.08em;">Days Open</th>
        </tr>
        {rows_html}
      </table>
    </td></tr>
    {_inline_footer("Please log into the D Decor QMR Dashboard and take corrective "
                    "action immediately. Unresolved complaints will be escalated to "
                    "senior management after 72 hours.")}"""

    return _outer_wrapper(inner)


# ── SMTP SEND ─────────────────────────────────────────────────────────────────

def send_email(
    sender_email: str,
    sender_password: str,
    recipients: List[str],
    subject: str,
    html_body: str,
    excel_bytes: Optional[bytes] = None,
    excel_filename: str = "DDecor_Report.xlsx",
) -> None:
    """
    Send an HTML email via Gmail SMTP SSL.
    Attaches an Excel file if excel_bytes is provided.
    Raises Exception on failure — caller handles it.
    """
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = sender_email
    msg["To"]      = ", ".join(recipients)
    msg.attach(MIMEText(html_body, "html"))

    if excel_bytes:
        att = MIMEApplication(excel_bytes, _subtype="xlsx")
        att["Content-Disposition"] = f'attachment; filename="{excel_filename}"'
        msg.attach(att)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipients, msg.as_string())
