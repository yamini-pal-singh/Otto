#!/usr/bin/env python3
"""
Otto Intelligence — Call Processing Report Generator
Fetches real data from staging API and generates an interactive HTML report.

Usage:
    python3 generate_report.py              # all calls (up to 20)
    python3 generate_report.py --limit 5    # first 5 calls
    python3 generate_report.py --call-id <UUID>  # single call
"""
import os
import sys
import json
import argparse
import html as html_mod
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("OTTO_API_BASE_URL", "https://ottoai.shunyalabs.ai").rstrip("/")
API_KEY = os.getenv("OTTO_API_KEY", "")
COMPANY_ID = "91ecfcb9-fc40-4792-ba47-65b273cec204"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def fetch_json(url, params=None):
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_calls(limit=20):
    data = fetch_json(
        f"{BASE_URL}/api/v1/call-processing/calls",
        {"company_id": COMPANY_ID, "limit": limit, "sort_by": "call_date", "sort_order": "desc"},
    )
    return data.get("calls", [])


def fetch_summary(call_id):
    try:
        return fetch_json(
            f"{BASE_URL}/api/v1/call-processing/summary/{call_id}",
            {"include_chunks": "true"},
        )
    except Exception:
        return None


def fetch_detail(call_id):
    try:
        return fetch_json(
            f"{BASE_URL}/api/v1/call-processing/calls/{call_id}/detail",
            {"include_transcript": "true", "include_segments": "true"},
        )
    except Exception:
        return None


def fetch_phases_analytics():
    try:
        return fetch_json(
            f"{BASE_URL}/api/v1/call-processing/phases/analytics",
            {"company_id": COMPANY_ID, "days": 90},
        )
    except Exception:
        return None


def esc(text):
    """HTML-escape text."""
    if text is None:
        return ""
    return html_mod.escape(str(text))


def score_color(score):
    """Return CSS color for a 0-1 score."""
    if score >= 0.8:
        return "#22c55e"
    if score >= 0.6:
        return "#eab308"
    if score >= 0.4:
        return "#f97316"
    return "#ef4444"


def score_pct(score):
    if score is None:
        return 0
    if isinstance(score, (int, float)):
        return int(score * 100) if score <= 1 else int(score)
    return 0


def severity_badge(sev):
    colors = {"high": "#ef4444", "medium": "#f97316", "low": "#eab308"}
    c = colors.get(str(sev).lower(), "#94a3b8")
    return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:600">{esc(sev)}</span>'


def _render_coaching_item(c):
    metric = esc(c.get("related_sop_metric", "").replace("_", " ").title())
    return (
        '<div class="coaching-item">'
        '<div class="coaching-header">' + severity_badge(c.get("severity", "")) + " <strong>" + metric + "</strong></div>"
        '<div class="coaching-issue">' + esc(c.get("issue", "")[:200]) + "</div>"
        '<div class="coaching-fix"><strong>How to fix:</strong> ' + esc(c.get("how_to_fix", "")) + "</div>"
        '<div class="coaching-example"><em>"' + esc(c.get("example_language", "")) + '"</em></div>'
        "</div>"
    )


def _render_objection(o):
    overcome_cls = "overcome-yes" if o.get("overcome") else "overcome-no"
    overcome_txt = "Resolved" if o.get("overcome") else "Unresolved"
    sub = ""
    if o.get("sub_objection"):
        sub = '<div class="obj-sub">' + esc(o.get("sub_objection", "")) + "</div>"
    suggestions = "".join(
        '<div class="obj-suggestion">&#128161; ' + esc(rs) + "</div>"
        for rs in (o.get("response_suggestions") or [])[:1]
    )
    return (
        '<div class="objection-card">'
        '<div class="obj-header">'
        + severity_badge(o.get("severity", ""))
        + ' <span class="obj-category">' + esc(o.get("category_text", "")) + "</span>"
        + ' <span class="obj-overcome ' + overcome_cls + '">' + overcome_txt + "</span>"
        + "</div>"
        + '<div class="obj-quote">"' + esc(str(o.get("objection_text", ""))[:200]) + '"</div>'
        + sub + suggestions + "</div>"
    )


def _render_segment(seg):
    speaker = seg.get("speaker", "unknown").replace(" ", "_")
    return (
        '<div class="segment">'
        '<span class="speaker speaker-' + speaker + '">' + esc(seg.get("speaker", "?")) + "</span>"
        '<span class="seg-text">' + esc(seg.get("text", "")) + "</span>"
        "</div>"
    )


def build_call_card(call, summary, detail, idx):
    """Build HTML for a single call card."""
    phone = call.get("phone_number", "N/A")
    status = call.get("status", "?")
    call_date = call.get("call_date", "")

    # Summary data
    s = summary or {}
    sum_obj = s.get("summary", {})
    sum_text = sum_obj.get("summary", "No summary available") if isinstance(sum_obj, dict) else str(sum_obj or "No summary")
    key_points = sum_obj.get("key_points", []) if isinstance(sum_obj, dict) else []
    action_items = sum_obj.get("action_items", []) if isinstance(sum_obj, dict) else []

    # Compliance
    comp = s.get("compliance", {})
    sop = comp.get("sop_compliance", {})
    comp_score = sop.get("score", 0) or 0
    comp_pct = score_pct(comp_score)
    stages = sop.get("stages", {})
    followed = stages.get("followed", [])
    missed = stages.get("missed", [])
    coaching = sop.get("coaching_issues", [])

    # Objections
    obj_data = s.get("objections", {})
    objections = obj_data.get("objections", []) if isinstance(obj_data, dict) else []

    # Qualification
    qual = s.get("qualification", {})

    # Transcript segments
    segments = detail.get("segments", []) if detail else []

    # --- Build sections ---
    parts = []

    # Header
    date_str = esc(call_date[:10]) if call_date else ""
    parts.append(
        '<div class="call-card" id="call-' + str(idx) + '">'
        '<div class="call-header" onclick="toggleCard(' + str(idx) + ')">'
        '<div class="call-header-left">'
        '<span class="call-number">Call #' + str(idx + 1) + "</span>"
        '<span class="call-phone">' + esc(phone) + "</span>"
        '<span class="call-status status-' + status + '">' + esc(status) + "</span>"
        "</div>"
        '<div class="call-header-right">'
        '<div class="compliance-mini">'
        '<div class="mini-bar-bg">'
        '<div class="mini-bar-fill" style="width:' + str(comp_pct) + "%;background:" + score_color(comp_score) + '"></div>'
        "</div>"
        '<span style="color:' + score_color(comp_score) + ';font-weight:700">' + str(comp_pct) + "%</span>"
        "</div>"
        '<span class="call-date">' + date_str + "</span>"
        '<span class="expand-icon" id="icon-' + str(idx) + '">&#9660;</span>'
        "</div></div>"
    )

    parts.append('<div class="call-body" id="body-' + str(idx) + '" style="display:none">')

    # Summary section
    kp_html = "".join('<div class="key-point">&#8226; ' + esc(kp) + "</div>" for kp in key_points[:5])
    ai_html = ""
    if action_items:
        ai_html = "<h4>Action Items</h4>" + "".join('<div class="action-item">&#9745; ' + esc(ai) + "</div>" for ai in action_items[:5])
    parts.append(
        '<div class="section"><h3>Summary</h3>'
        '<p class="summary-text">' + esc(sum_text) + "</p>"
        + kp_html + ai_html + "</div>"
    )

    # Compliance section
    total_stages = max(stages.get("total", 1), 1)
    followed_pct = int(len(followed) / total_stages * 100)
    missed_pct = int(len(missed) / total_stages * 100)
    followed_tags = "".join('<span class="sop-tag sop-followed">' + esc(f) + "</span>" for f in followed)
    missed_tags = "".join('<span class="sop-tag sop-missed">' + esc(m) + "</span>" for m in missed[:10])
    if len(missed) > 10:
        missed_tags += '<span class="sop-tag sop-missed">+' + str(len(missed) - 10) + " more...</span>"
    parts.append(
        '<div class="section"><h3>SOP Compliance</h3>'
        '<div class="score-display">'
        '<div class="score-circle" style="border-color:' + score_color(comp_score) + '">'
        '<span style="color:' + score_color(comp_score) + '">' + str(comp_pct) + "%</span></div>"
        '<div class="score-details">'
        '<div class="stage-bar"><span class="stage-label">Followed (' + str(len(followed)) + "/" + str(stages.get("total", 0)) + ")</span>"
        '<div class="bar-bg"><div class="bar-fill" style="width:' + str(followed_pct) + '%;background:#22c55e"></div></div></div>'
        '<div class="stage-bar"><span class="stage-label">Missed (' + str(len(missed)) + "/" + str(stages.get("total", 0)) + ")</span>"
        '<div class="bar-bg"><div class="bar-fill" style="width:' + str(missed_pct) + '%;background:#ef4444"></div></div></div>'
        "</div></div>"
        '<div class="sop-grid">' + followed_tags + missed_tags + "</div></div>"
    )

    # Coaching section
    if coaching:
        items_html = "".join(_render_coaching_item(c) for c in coaching[:6])
        more = ""
        if len(coaching) > 6:
            more = '<div class="coaching-more">... and ' + str(len(coaching) - 6) + " more coaching items</div>"
        parts.append(
            '<div class="section"><h3>AI Coaching Recommendations (' + str(len(coaching)) + ")</h3>"
            + items_html + more + "</div>"
        )

    # Objections section
    if objections:
        obj_html = "".join(_render_objection(o) for o in objections[:6])
        parts.append(
            '<div class="section"><h3>Objections Detected (' + str(len(objections)) + ")</h3>"
            '<div class="objections-grid">' + obj_html + "</div></div>"
        )

    # Qualification section
    if qual:
        parts.append(
            '<div class="section"><h3>Lead Qualification</h3>'
            '<pre class="json-block">' + esc(json.dumps(qual, indent=2, default=str)[:1500]) + "</pre></div>"
        )

    # Transcript section
    if segments:
        seg_html = "".join(_render_segment(seg) for seg in segments)
        parts.append(
            '<div class="section"><h3>Transcript (' + str(len(segments)) + " segments)</h3>"
            '<div class="transcript-box">' + seg_html + "</div></div>"
        )

    parts.append("</div></div>")  # close call-body + call-card
    return "\n".join(parts)


def build_html(calls_data, phases_analytics):
    """Build the complete HTML report."""
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(calls_data)
    completed = sum(1 for c, _, _ in calls_data if c.get("status") == "completed")

    # Phase analytics
    pa = phases_analytics or {}
    detection = pa.get("detection_rates", {})
    missing = pa.get("commonly_missing", [])

    call_cards = "\n".join(
        build_call_card(call, summary, detail, i)
        for i, (call, summary, detail) in enumerate(calls_data)
    )

    # Pre-build phase rows and missing tags (avoid nested f-strings)
    phase_rows = ""
    for phase, rate in sorted(detection.items(), key=lambda x: -x[1]):
        pname = esc(phase.replace("_", " ").title())
        pct = int(rate * 100)
        pcolor = score_color(rate)
        phase_rows += (
            '<div class="phase-row"><span class="phase-name">' + pname + "</span>"
            '<div class="phase-bar-bg"><div class="phase-bar-fill" style="width:'
            + str(pct) + "%;background:" + pcolor + '">' + str(pct) + "%</div></div></div>"
        )
    missing_tags = "".join(
        '<span class="missing-tag">' + esc(m.replace("_", " ").title()) + "</span>"
        for m in missing
    )

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Otto Intelligence — Call Processing Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}

  /* Header */
  .report-header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 16px; padding: 32px; margin-bottom: 24px; }}
  .report-title {{ font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #f97316, #eab308); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .report-subtitle {{ color: #94a3b8; font-size: 14px; margin-top: 4px; }}
  .stats-row {{ display: flex; gap: 16px; margin-top: 20px; flex-wrap: wrap; }}
  .stat-box {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px 24px; min-width: 150px; }}
  .stat-value {{ font-size: 28px; font-weight: 800; color: #f8fafc; }}
  .stat-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}

  /* Phase Analytics */
  .phases-section {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
  .phases-section h2 {{ font-size: 18px; margin-bottom: 16px; color: #f8fafc; }}
  .phase-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .phase-name {{ width: 180px; font-size: 13px; color: #cbd5e1; }}
  .phase-bar-bg {{ flex: 1; height: 24px; background: #334155; border-radius: 12px; overflow: hidden; }}
  .phase-bar-fill {{ height: 100%; border-radius: 12px; transition: width 0.5s; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; font-size: 11px; font-weight: 700; color: #fff; }}
  .missing-tags {{ display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }}
  .missing-tag {{ background: #7f1d1d; color: #fca5a5; padding: 4px 12px; border-radius: 9999px; font-size: 12px; }}

  /* Call Cards */
  .call-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 12px; overflow: hidden; }}
  .call-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; cursor: pointer; transition: background 0.2s; }}
  .call-header:hover {{ background: #334155; }}
  .call-header-left, .call-header-right {{ display: flex; align-items: center; gap: 12px; }}
  .call-number {{ font-weight: 700; color: #f8fafc; font-size: 15px; }}
  .call-phone {{ color: #94a3b8; font-size: 13px; font-family: monospace; }}
  .call-status {{ padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .status-completed {{ background: #14532d; color: #86efac; }}
  .status-processing {{ background: #422006; color: #fdba74; }}
  .status-failed {{ background: #7f1d1d; color: #fca5a5; }}
  .call-date {{ color: #64748b; font-size: 12px; }}
  .expand-icon {{ color: #64748b; font-size: 12px; transition: transform 0.2s; }}
  .compliance-mini {{ display: flex; align-items: center; gap: 6px; }}
  .mini-bar-bg {{ width: 60px; height: 6px; background: #334155; border-radius: 3px; overflow: hidden; }}
  .mini-bar-fill {{ height: 100%; border-radius: 3px; }}

  /* Call Body */
  .call-body {{ padding: 0 20px 20px; }}
  .section {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-top: 16px; }}
  .section h3 {{ font-size: 16px; color: #f97316; margin-bottom: 12px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  .section h4 {{ font-size: 14px; color: #cbd5e1; margin: 12px 0 8px; }}
  .summary-text {{ color: #cbd5e1; font-size: 14px; margin-bottom: 12px; }}
  .key-point {{ color: #94a3b8; font-size: 13px; padding: 3px 0; padding-left: 12px; }}
  .action-item {{ color: #86efac; font-size: 13px; padding: 3px 0; padding-left: 12px; }}

  /* Compliance */
  .score-display {{ display: flex; align-items: center; gap: 24px; margin-bottom: 16px; }}
  .score-circle {{ width: 80px; height: 80px; border-radius: 50%; border: 4px solid; display: flex; align-items: center; justify-content: center; font-size: 24px; font-weight: 800; flex-shrink: 0; }}
  .score-details {{ flex: 1; }}
  .stage-bar {{ margin-bottom: 8px; }}
  .stage-label {{ font-size: 12px; color: #94a3b8; }}
  .bar-bg {{ height: 8px; background: #334155; border-radius: 4px; overflow: hidden; margin-top: 4px; }}
  .bar-fill {{ height: 100%; border-radius: 4px; }}
  .sop-grid {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }}
  .sop-tag {{ padding: 3px 10px; border-radius: 6px; font-size: 11px; }}
  .sop-followed {{ background: #14532d; color: #86efac; }}
  .sop-missed {{ background: #7f1d1d; color: #fca5a5; }}

  /* Coaching */
  .coaching-item {{ background: #1e293b; border-radius: 8px; padding: 14px; margin-bottom: 10px; border-left: 3px solid #f97316; }}
  .coaching-header {{ margin-bottom: 6px; }}
  .coaching-issue {{ color: #94a3b8; font-size: 13px; margin-bottom: 8px; }}
  .coaching-fix {{ color: #cbd5e1; font-size: 13px; margin-bottom: 6px; }}
  .coaching-example {{ color: #22d3ee; font-size: 12px; font-style: italic; background: #0c4a6e22; padding: 8px 12px; border-radius: 6px; }}
  .coaching-more {{ color: #64748b; font-size: 13px; text-align: center; padding: 8px; }}

  /* Objections */
  .objections-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 12px; }}
  .objection-card {{ background: #1e293b; border-radius: 8px; padding: 14px; border-left: 3px solid #eab308; }}
  .obj-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
  .obj-category {{ color: #cbd5e1; font-size: 13px; font-weight: 600; }}
  .obj-overcome {{ padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .overcome-yes {{ background: #14532d; color: #86efac; }}
  .overcome-no {{ background: #7f1d1d; color: #fca5a5; }}
  .obj-quote {{ color: #94a3b8; font-size: 13px; font-style: italic; margin-bottom: 6px; }}
  .obj-sub {{ color: #64748b; font-size: 12px; margin-bottom: 6px; }}
  .obj-suggestion {{ color: #22d3ee; font-size: 12px; background: #0c4a6e22; padding: 6px 10px; border-radius: 6px; margin-top: 6px; }}

  /* Transcript */
  .transcript-box {{ max-height: 500px; overflow-y: auto; padding: 12px; background: #020617; border-radius: 8px; }}
  .segment {{ margin-bottom: 10px; }}
  .speaker {{ display: inline-block; min-width: 120px; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-right: 8px; }}
  .speaker-customer_rep {{ background: #1e3a5f; color: #7dd3fc; }}
  .speaker-home_owner {{ background: #365314; color: #bef264; }}
  .speaker-unknown {{ background: #334155; color: #94a3b8; }}
  .seg-text {{ color: #cbd5e1; font-size: 13px; }}

  /* JSON */
  .json-block {{ background: #020617; color: #94a3b8; padding: 12px; border-radius: 8px; font-size: 12px; overflow-x: auto; max-height: 300px; overflow-y: auto; white-space: pre-wrap; }}

  /* Controls */
  .controls {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .btn {{ padding: 8px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; cursor: pointer; font-size: 13px; transition: all 0.2s; }}
  .btn:hover {{ background: #334155; }}
  .btn-active {{ background: #f97316; border-color: #f97316; color: #000; font-weight: 600; }}
</style>
</head>
<body>
<div class="container">

  <!-- HEADER -->
  <div class="report-header">
    <div class="report-title">Otto Intelligence — Call Processing Report</div>
    <div class="report-subtitle">Arizona Roofers (Staging) &bull; Generated {now} &bull; Company: {COMPANY_ID}</div>
    <div class="stats-row">
      <div class="stat-box"><div class="stat-value">{total}</div><div class="stat-label">Total Calls</div></div>
      <div class="stat-box"><div class="stat-value">{completed}</div><div class="stat-label">Completed</div></div>
      <div class="stat-box"><div class="stat-value">{pa.get("total_calls", 0)}</div><div class="stat-label">Phases Analyzed</div></div>
      <div class="stat-box"><div class="stat-value">{len(missing)}</div><div class="stat-label">Common Missing Phases</div></div>
    </div>
  </div>

  <!-- PHASE ANALYTICS -->
  <div class="phases-section">
    <h2>Conversation Phase Detection Rates (Last 90 Days)</h2>
    {phase_rows}
    <div class="missing-tags">
      <span style="color:#94a3b8;font-size:12px;margin-right:4px">Commonly missing:</span>
      {missing_tags}
    </div>
  </div>

  <!-- CONTROLS -->
  <div class="controls">
    <button class="btn btn-active" onclick="toggleAll(true)">Expand All</button>
    <button class="btn" onclick="toggleAll(false)">Collapse All</button>
  </div>

  <!-- CALL CARDS -->
  {call_cards}

</div>

<script>
function toggleCard(idx) {{
  const body = document.getElementById("body-" + idx);
  const icon = document.getElementById("icon-" + idx);
  if (body.style.display === "none") {{
    body.style.display = "block";
    icon.innerHTML = "&#9650;";
  }} else {{
    body.style.display = "none";
    icon.innerHTML = "&#9660;";
  }}
}}
function toggleAll(show) {{
  document.querySelectorAll(".call-body").forEach(el => el.style.display = show ? "block" : "none");
  document.querySelectorAll(".expand-icon").forEach(el => el.innerHTML = show ? "&#9650;" : "&#9660;");
  document.querySelectorAll(".controls .btn").forEach((b, i) => {{
    b.classList.toggle("btn-active", show ? i === 0 : i === 1);
  }});
}}
</script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Otto call processing HTML report")
    parser.add_argument("--limit", type=int, default=20, help="Max calls to fetch (default: 20)")
    parser.add_argument("--call-id", type=str, help="Fetch a single call by ID")
    parser.add_argument("--output", type=str, default="call_report.html", help="Output file (default: call_report.html)")
    args = parser.parse_args()

    if not API_KEY:
        print("ERROR: OTTO_API_KEY not set in .env")
        sys.exit(1)

    print(f"Fetching data from {BASE_URL}...")

    # Fetch calls
    if args.call_id:
        calls = [{"call_id": args.call_id, "status": "completed", "phone_number": "?"}]
    else:
        print(f"  Fetching call list (limit={args.limit})...")
        calls = fetch_calls(args.limit)
        print(f"  Found {len(calls)} calls")

    # Fetch phase analytics
    print("  Fetching phase analytics...")
    phases = fetch_phases_analytics()

    # Fetch summary + detail for each call
    calls_data = []
    for i, call in enumerate(calls):
        cid = call["call_id"]
        print(f"  [{i+1}/{len(calls)}] Fetching {cid[:12]}... ", end="", flush=True)
        summary = fetch_summary(cid)
        detail = fetch_detail(cid)
        calls_data.append((call, summary, detail))
        has_summary = "summary" in (summary or {})
        has_transcript = bool((detail or {}).get("transcript"))
        print(f"summary={'yes' if has_summary else 'no'} transcript={'yes' if has_transcript else 'no'}")

    # Generate report
    print(f"\nGenerating HTML report...")
    html_content = build_html(calls_data, phases)

    output_path = os.path.join(os.path.dirname(__file__) or ".", args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Report saved to: {output_path}")
    print(f"Open in browser: file://{os.path.abspath(output_path)}")


if __name__ == "__main__":
    main()
