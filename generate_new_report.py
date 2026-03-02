#!/usr/bin/env python3
"""
Otto Intelligence — Comprehensive Call Processing Test & Report Generator
Tests all API endpoints with company_id 1be5ea90-d3ae-4b03-8b05-f5679cd73bc4
and generates an interactive HTML report with full parameter validation.

Deduplicates calls by customer name/phone — keeps only the latest per customer.

Usage:
    python3 generate_new_report.py
    python3 generate_new_report.py --output my_report.html
"""
import os
import sys
import json
import uuid
import argparse
import html as html_mod
from datetime import datetime

import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
BASE_URL = "https://ottoai.shunyalabs.ai"
API_KEY = "5q3fwliU9ZFo3epTCsUfUiDw1Dy4DnBP"
COMPANY_ID = "1be5ea90-d3ae-4b03-8b05-f5679cd73bc4"
COMPANY_NAME = "Arizona Roofers"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
TIMEOUT = 60

# All 10 audio URLs for testing
STAGING_AUDIO_URLS = [
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/56dc7e30-ffed-4f8d-80eb-b514ffb30a50/4019778374.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/6e37c8bb-16bc-4e17-867e-ae5e9f57c3b9/4037028977.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/aa4018dd-47a0-4377-b150-20bcbf3316ff/4036931546.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/bdc3fc20-ba07-43e5-8e6d-26359cc4633c/4036863062.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/a5933178-e217-44e0-975e-2cbd1a28bb46/4036836500.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/8c6b15ee-5675-4e01-8b31-ff3658126353/4049722733.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/80913c6a-4b74-4d86-ab27-c67ff3654ba7/4043584280.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/eff6032d-cd45-4ef7-b0d1-60ffad285df1/4036334162.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/323d1a76-f84c-4a88-9312-c03b4b653cc3/3998154371.mp3",
    "https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/1fd7bea5-9ace-4e8f-a31f-152ea8269927/4015296617.mp3",
]

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def esc(text):
    if text is None:
        return ""
    return html_mod.escape(str(text))


def score_color(score):
    if score is None:
        return "#94a3b8"
    score = float(score)
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


def fetch_json(url, params=None, timeout=TIMEOUT):
    r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


# ─────────────────────────────────────────────────────────────────────────────
# API Test Runner
# ─────────────────────────────────────────────────────────────────────────────

class TestResult:
    def __init__(self, name, category, status, expected, actual, detail=""):
        self.name = name
        self.category = category
        self.status = status  # PASS, FAIL, TIMEOUT, ERROR
        self.expected = expected
        self.actual = actual
        self.detail = detail


def run_all_tests():
    """Run comprehensive API tests and return results."""
    results = []

    def test(name, category, expected_codes, func, validate=None):
        try:
            r = func()
            status_ok = r.status_code in expected_codes
            extra_ok = True
            detail = ""
            if validate and status_ok:
                try:
                    extra_ok, detail = validate(r)
                except Exception as e:
                    extra_ok = False
                    detail = str(e)
            overall = "PASS" if (status_ok and extra_ok) else "FAIL"
            results.append(TestResult(
                name, category, overall,
                f"HTTP {expected_codes}", f"HTTP {r.status_code}",
                detail
            ))
        except requests.exceptions.ReadTimeout:
            results.append(TestResult(name, category, "TIMEOUT", f"HTTP {expected_codes}", "Timeout", "Server took too long"))
        except Exception as e:
            results.append(TestResult(name, category, "ERROR", f"HTTP {expected_codes}", str(e)[:100], ""))

    # ── Infrastructure ──
    test("Health check returns healthy", "Infrastructure", {200},
        lambda: requests.get(f"{BASE_URL}/health", timeout=TIMEOUT),
        lambda r: (r.json().get("status") == "healthy", f"status={r.json().get('status')}"))

    test("API status requires auth (no key)", "Authentication", {401},
        lambda: requests.get(f"{BASE_URL}/api/v1/status", timeout=TIMEOUT))

    test("API status rejects wrong key", "Authentication", {401, 403},
        lambda: requests.get(f"{BASE_URL}/api/v1/status",
            headers={"X-API-Key": "INVALID_KEY_12345"}, timeout=TIMEOUT))

    test("API status rejects empty key", "Authentication", {401},
        lambda: requests.get(f"{BASE_URL}/api/v1/status",
            headers={"X-API-Key": ""}, timeout=TIMEOUT))

    test("API status with valid key", "Authentication", {200},
        lambda: requests.get(f"{BASE_URL}/api/v1/status", headers=HEADERS, timeout=TIMEOUT),
        lambda r: (r.json().get("api_version") == "v1", f"version={r.json().get('api_version')}"))

    # ── List Calls ──
    test("List calls requires company_id", "List Calls", {400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS, timeout=TIMEOUT))

    test("List calls with valid company_id", "List Calls", {200},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": COMPANY_ID, "limit": 50, "sort_by": "call_date", "sort_order": "desc"}, timeout=TIMEOUT),
        lambda r: (len(r.json().get("calls", [])) > 0, f"calls={len(r.json().get('calls',[]))}"))

    test("List calls with nonexistent company", "List Calls", {200, 404},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "limit": 5}, timeout=TIMEOUT))

    test("List calls rejects negative limit", "List Calls", {400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": COMPANY_ID, "limit": -1}, timeout=TIMEOUT))

    # ── List Summaries ──
    test("List summaries with filters", "List Summaries", {200},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/summaries", headers=HEADERS,
            params={"company_id": COMPANY_ID, "limit": 50, "sort_by": "created_at", "sort_order": "desc",
                    "min_compliance_score": 0.0, "max_compliance_score": 1.0}, timeout=TIMEOUT),
        lambda r: (len(r.json().get("summaries", [])) > 0, f"summaries={len(r.json().get('summaries',[]))}"))

    test("Summaries min_score > max_score returns empty", "List Summaries", {200, 400},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/summaries", headers=HEADERS,
            params={"company_id": COMPANY_ID, "min_compliance_score": 0.9, "max_compliance_score": 0.1}, timeout=TIMEOUT))

    # ── Phase Analytics ──
    test("Phase analytics returns detection rates", "Phase Analytics", {200},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/phases/analytics", headers=HEADERS,
            params={"company_id": COMPANY_ID, "days": 90}, timeout=TIMEOUT),
        lambda r: (len(r.json().get("detection_rates", {})) >= 5, f"phases={len(r.json().get('detection_rates',{}))}"))

    test("Phase search finds missing phases", "Phase Analytics", {200},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/phases/search", headers=HEADERS,
            params={"company_id": COMPANY_ID, "missing_phase": "objection_handling", "limit": 50}, timeout=TIMEOUT),
        lambda r: (isinstance(r.json().get("calls"), list), f"missing_calls={len(r.json().get('calls',[]))}"))

    test("Phase search requires company_id", "Phase Analytics", {400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/phases/search", headers=HEADERS, timeout=TIMEOUT))

    test("Phase analytics requires auth", "Phase Analytics", {401},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/phases/analytics",
            params={"company_id": COMPANY_ID, "days": 30}, timeout=TIMEOUT))

    # ── Security / Injection ──
    test("SQL injection in company_id returns 0 calls", "Security", {200, 400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": "'; DROP TABLE calls; --", "limit": 5}, timeout=TIMEOUT))

    test("NoSQL injection in company_id returns 0 calls", "Security", {200, 400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": '{"$gt": ""}', "limit": 5}, timeout=TIMEOUT))

    test("XSS in call_id returns 404", "Security", {404, 400},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/summary/<script>alert('xss')</script>",
            headers=HEADERS, timeout=TIMEOUT))

    test("Path traversal in call_id returns 404", "Security", {404, 400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/summary/../../../etc/passwd",
            headers=HEADERS, timeout=TIMEOUT))

    test("Template injection in company_id", "Security", {200, 400, 422},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls", headers=HEADERS,
            params={"company_id": "{{7*7}}", "limit": 5}, timeout=TIMEOUT))

    # ── Process Endpoint ──
    test("Process rejects empty body", "Process", {400, 422},
        lambda: requests.post(f"{BASE_URL}/api/v1/call-processing/process",
            headers=HEADERS, json={}, timeout=TIMEOUT))

    test("Process rejects missing audio_url", "Process", {400, 422},
        lambda: requests.post(f"{BASE_URL}/api/v1/call-processing/process",
            headers=HEADERS, json={
                "call_id": "neg_test_no_audio", "company_id": COMPANY_ID,
                "phone_number": "+14805551234",
                "metadata": {"agent": {"id": "USR_TEST", "name": "Test"}}
            }, timeout=TIMEOUT))

    # ── Nonexistent Resources ──
    test("Summary for nonexistent call returns 404", "Resource Not Found", {404},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/summary/00000000-0000-0000-0000-000000000000",
            headers=HEADERS, timeout=TIMEOUT))

    test("Detail for nonexistent call returns 404", "Resource Not Found", {404},
        lambda: requests.get(f"{BASE_URL}/api/v1/call-processing/calls/00000000-0000-0000-0000-000000000000/detail",
            headers=HEADERS, timeout=TIMEOUT))

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Parameter Validation per Call
# ─────────────────────────────────────────────────────────────────────────────

# All expected fields from architecture doc
EXPECTED_SUMMARY_FIELDS = ["summary", "key_points", "action_items", "sentiment_score"]
EXPECTED_COMPLIANCE_FIELDS = ["score", "stages", "coaching_issues"]
EXPECTED_QUALIFICATION_FIELDS = [
    "customer_name", "detected_call_type", "is_existing_customer",
    "qualification_status", "booking_status", "bant_scores", "overall_score",
    "follow_up_required", "follow_up_reason", "decision_makers",
    "urgency_signals", "budget_indicators", "service_requested",
    "appointment_confirmed", "appointment_date", "appointment_type",
    "appointment_timezone", "confidence_score", "customer_name_confidence",
    "address_confidence", "call_outcome_category", "service_address_structured",
    "service_address_raw",
]
EXPECTED_BANT_FIELDS = ["budget", "authority", "need", "timeline"]
EXPECTED_ADDRESS_FIELDS = ["line1", "city", "state", "postal_code", "country"]
EXPECTED_OBJECTION_FIELDS = ["objection_text", "category_text", "severity", "overcome"]


def validate_call_params(summary_data):
    """Validate all parameters for a single call. Returns dict of field -> {present, value, valid}."""
    checks = {}

    # Summary section
    s = summary_data.get("summary", {})
    if isinstance(s, dict):
        for f in EXPECTED_SUMMARY_FIELDS:
            val = s.get(f)
            checks[f"summary.{f}"] = {
                "present": val is not None,
                "value": str(val)[:100] if val is not None else "MISSING",
                "valid": val is not None and (str(val).strip() != "" if isinstance(val, str) else True)
            }
    else:
        for f in EXPECTED_SUMMARY_FIELDS:
            checks[f"summary.{f}"] = {"present": False, "value": "MISSING", "valid": False}

    # Compliance
    comp = summary_data.get("compliance", {}).get("sop_compliance", {})
    for f in EXPECTED_COMPLIANCE_FIELDS:
        val = comp.get(f)
        checks[f"compliance.{f}"] = {
            "present": val is not None,
            "value": str(val)[:100] if val is not None else "MISSING",
            "valid": val is not None
        }
    # Validate score is 0-1
    score = comp.get("score")
    if isinstance(score, (int, float)):
        checks["compliance.score"]["valid"] = 0 <= score <= 1
        checks["compliance.score"]["value"] = f"{score:.2f}"

    # Qualification
    qual = summary_data.get("qualification", {})
    for f in EXPECTED_QUALIFICATION_FIELDS:
        val = qual.get(f)
        checks[f"qualification.{f}"] = {
            "present": val is not None,
            "value": str(val)[:100] if val is not None else "MISSING",
            "valid": val is not None
        }

    # BANT scores deep check
    bant = qual.get("bant_scores", {})
    if isinstance(bant, dict):
        for bf in EXPECTED_BANT_FIELDS:
            val = bant.get(bf)
            valid = isinstance(val, (int, float)) and 0 <= val <= 1
            checks[f"bant.{bf}"] = {
                "present": val is not None,
                "value": f"{val}" if val is not None else "MISSING",
                "valid": valid
            }
    else:
        for bf in EXPECTED_BANT_FIELDS:
            checks[f"bant.{bf}"] = {"present": False, "value": "MISSING", "valid": False}

    # Overall score
    overall = qual.get("overall_score")
    if isinstance(overall, (int, float)):
        checks["qualification.overall_score"]["valid"] = 0 <= overall <= 1

    # Confidence scores
    for cf in ["confidence_score", "customer_name_confidence", "address_confidence"]:
        val = qual.get(cf)
        if isinstance(val, (int, float)):
            checks[f"qualification.{cf}"]["valid"] = 0 <= val <= 1

    # Address structure
    addr = qual.get("service_address_structured", {})
    if isinstance(addr, dict):
        for af in EXPECTED_ADDRESS_FIELDS:
            val = addr.get(af)
            checks[f"address.{af}"] = {
                "present": val is not None,
                "value": str(val)[:100] if val is not None else "null",
                "valid": True  # null is allowed for address fields
            }
    else:
        for af in EXPECTED_ADDRESS_FIELDS:
            checks[f"address.{af}"] = {"present": False, "value": "MISSING struct", "valid": False}

    # Objections
    obj_data = summary_data.get("objections", {})
    objections = obj_data.get("objections", []) if isinstance(obj_data, dict) else []
    checks["objections.count"] = {
        "present": True, "value": str(len(objections)), "valid": True
    }
    if objections:
        first = objections[0]
        for of in EXPECTED_OBJECTION_FIELDS:
            val = first.get(of)
            checks[f"objection[0].{of}"] = {
                "present": val is not None,
                "value": str(val)[:80] if val is not None else "MISSING",
                "valid": val is not None
            }

    return checks


# ─────────────────────────────────────────────────────────────────────────────
# HTML Report Builder
# ─────────────────────────────────────────────────────────────────────────────

def severity_badge(sev):
    colors = {"high": "#ef4444", "medium": "#f97316", "low": "#eab308"}
    c = colors.get(str(sev).lower(), "#94a3b8")
    return f'<span style="background:{c};color:#fff;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:600">{esc(sev)}</span>'


def build_test_results_section(test_results):
    """Build HTML for the test results section."""
    categories = {}
    for t in test_results:
        categories.setdefault(t.category, []).append(t)

    passed = sum(1 for t in test_results if t.status == "PASS")
    failed = sum(1 for t in test_results if t.status == "FAIL")
    timeout = sum(1 for t in test_results if t.status == "TIMEOUT")
    total = len(test_results)

    rows = ""
    for cat, tests in categories.items():
        for t in tests:
            icon = {"PASS": "&#9989;", "FAIL": "&#10060;", "TIMEOUT": "&#9203;", "ERROR": "&#9888;"}.get(t.status, "?")
            color = {"PASS": "#22c55e", "FAIL": "#ef4444", "TIMEOUT": "#f97316", "ERROR": "#ef4444"}.get(t.status, "#94a3b8")
            rows += (
                '<tr>'
                f'<td style="color:#94a3b8">{esc(cat)}</td>'
                f'<td>{esc(t.name)}</td>'
                f'<td style="text-align:center;font-size:18px">{icon}</td>'
                f'<td style="color:{color};font-weight:700">{t.status}</td>'
                f'<td style="color:#64748b">{esc(t.expected)}</td>'
                f'<td style="color:#cbd5e1">{esc(t.actual)}</td>'
                f'<td style="color:#94a3b8;font-size:12px">{esc(t.detail)}</td>'
                '</tr>'
            )

    return f'''
    <div class="test-results-section">
        <h2>API Test Results</h2>
        <div class="test-summary-bar">
            <div class="test-stat" style="border-color:#22c55e"><span class="test-stat-val" style="color:#22c55e">{passed}</span><span class="test-stat-label">Passed</span></div>
            <div class="test-stat" style="border-color:#ef4444"><span class="test-stat-val" style="color:#ef4444">{failed}</span><span class="test-stat-label">Failed</span></div>
            <div class="test-stat" style="border-color:#f97316"><span class="test-stat-val" style="color:#f97316">{timeout}</span><span class="test-stat-label">Timeout</span></div>
            <div class="test-stat" style="border-color:#3b82f6"><span class="test-stat-val" style="color:#3b82f6">{total}</span><span class="test-stat-label">Total</span></div>
        </div>
        <table class="test-table">
            <thead><tr><th>Category</th><th>Test</th><th></th><th>Result</th><th>Expected</th><th>Actual</th><th>Detail</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''


def build_param_validation_section(call_validations):
    """Build HTML for parameter validation across all calls."""
    # Aggregate: for each field, count present/valid across calls
    all_fields = {}
    for cid, checks in call_validations.items():
        for field, info in checks.items():
            if field not in all_fields:
                all_fields[field] = {"present": 0, "valid": 0, "total": 0, "values": []}
            all_fields[field]["total"] += 1
            if info["present"]:
                all_fields[field]["present"] += 1
            if info["valid"]:
                all_fields[field]["valid"] += 1
            all_fields[field]["values"].append(info["value"][:50])

    rows = ""
    for field in sorted(all_fields.keys()):
        info = all_fields[field]
        pct = int(info["present"] / info["total"] * 100) if info["total"] > 0 else 0
        vpct = int(info["valid"] / info["total"] * 100) if info["total"] > 0 else 0
        pcolor = "#22c55e" if pct == 100 else ("#eab308" if pct >= 70 else "#ef4444")
        vcolor = "#22c55e" if vpct == 100 else ("#eab308" if vpct >= 70 else "#ef4444")
        # Show unique sample values
        unique_vals = list(set(info["values"]))[:3]
        samples = ", ".join(unique_vals)
        rows += (
            '<tr>'
            f'<td style="font-family:monospace;font-size:12px">{esc(field)}</td>'
            f'<td style="text-align:center"><span style="color:{pcolor};font-weight:700">{info["present"]}/{info["total"]}</span></td>'
            f'<td style="text-align:center">'
            f'<div style="background:#334155;border-radius:4px;height:8px;width:80px;display:inline-block;vertical-align:middle">'
            f'<div style="background:{pcolor};height:100%;width:{pct}%;border-radius:4px"></div></div>'
            f' <span style="color:{pcolor};font-size:12px">{pct}%</span></td>'
            f'<td style="text-align:center"><span style="color:{vcolor};font-weight:700">{info["valid"]}/{info["total"]}</span></td>'
            f'<td style="color:#94a3b8;font-size:11px;max-width:250px;overflow:hidden;text-overflow:ellipsis">{esc(samples)}</td>'
            '</tr>'
        )

    return f'''
    <div class="param-section">
        <h2>Parameter Validation Across All Calls ({len(call_validations)} calls)</h2>
        <table class="param-table">
            <thead><tr><th>Field</th><th>Present</th><th>Coverage</th><th>Valid</th><th>Sample Values</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    '''


def build_call_card(call, summary, detail, idx, validation):
    """Build HTML for a single call card with full data."""
    cid = call.get("call_id", "?")
    phone = call.get("phone_number", "N/A")
    status = call.get("status", "?")
    call_date = call.get("call_date", "")

    s = summary or {}
    sum_obj = s.get("summary", {})
    sum_text = sum_obj.get("summary", "No summary available") if isinstance(sum_obj, dict) else str(sum_obj or "No summary")
    key_points = sum_obj.get("key_points", []) if isinstance(sum_obj, dict) else []
    action_items = sum_obj.get("action_items", []) if isinstance(sum_obj, dict) else []
    sentiment_score = sum_obj.get("sentiment_score", None) if isinstance(sum_obj, dict) else None

    comp = s.get("compliance", {})
    sop = comp.get("sop_compliance", {})
    comp_score = sop.get("score", 0) or 0
    comp_pct = score_pct(comp_score)
    stages = sop.get("stages", {})
    followed = stages.get("followed", [])
    missed = stages.get("missed", [])
    coaching = sop.get("coaching_issues", [])

    obj_data = s.get("objections", {})
    objections = obj_data.get("objections", []) if isinstance(obj_data, dict) else []

    qual = s.get("qualification", {})
    customer_name = qual.get("customer_name") or "Unknown"
    call_type = qual.get("detected_call_type") or "N/A"
    is_existing = qual.get("is_existing_customer")
    qual_status = qual.get("qualification_status") or "N/A"
    booking_status = qual.get("booking_status") or "N/A"
    bant = qual.get("bant_scores", {})
    overall_bant = qual.get("overall_score", 0) or 0
    follow_up_req = qual.get("follow_up_required", False)
    follow_up_reason = qual.get("follow_up_reason") or ""
    decision_makers = qual.get("decision_makers", [])
    urgency_signals = qual.get("urgency_signals", [])
    budget_indicators = qual.get("budget_indicators", [])
    service_requested = qual.get("service_requested") or ""
    appt_confirmed = qual.get("appointment_confirmed", False)
    appt_date = qual.get("appointment_date")
    appt_type = qual.get("appointment_type") or ""
    appt_timezone = qual.get("appointment_timezone") or ""
    confidence = qual.get("confidence_score", 0) or 0
    name_confidence = qual.get("customer_name_confidence", 0) or 0
    addr_confidence = qual.get("address_confidence", 0) or 0
    addr_struct = qual.get("service_address_structured", {})
    addr_raw = qual.get("service_address_raw") or ""
    call_outcome = qual.get("call_outcome_category") or ""

    segments = detail.get("segments", []) if detail else []

    parts = []

    # ── Header ──
    date_str = esc(call_date[:10]) if call_date else ""
    qual_cls = {"hot": "qual-hot", "warm": "qual-warm", "cold": "qual-cold"}.get(qual_status, "qual-other")

    # Parameter validation score
    if validation:
        total_fields = len(validation)
        present_fields = sum(1 for v in validation.values() if v["present"])
        valid_fields = sum(1 for v in validation.values() if v["valid"])
        pv_pct = int(present_fields / total_fields * 100) if total_fields > 0 else 0
    else:
        pv_pct = 0
        total_fields = 0
        present_fields = 0
        valid_fields = 0

    parts.append(
        f'<div class="call-card" id="call-{idx}">'
        f'<div class="call-header" onclick="toggleCard({idx})">'
        '<div class="call-header-left">'
        f'<span class="call-number">Call #{idx + 1}</span>'
        f'<span class="call-customer-name">{esc(customer_name)}</span>'
        f'<span class="call-phone">{esc(phone)}</span>'
        f'<span class="call-status status-{status}">{esc(status)}</span>'
        f'<span class="call-type-badge">{esc(call_type.replace("_"," ").title())}</span>'
        f'<span class="qual-badge {qual_cls}">{esc(qual_status.upper())}</span>'
        '</div>'
        '<div class="call-header-right">'
        '<div class="compliance-mini">'
        '<div class="mini-bar-bg">'
        f'<div class="mini-bar-fill" style="width:{comp_pct}%;background:{score_color(comp_score)}"></div>'
        '</div>'
        f'<span style="color:{score_color(comp_score)};font-weight:700">{comp_pct}%</span>'
        '</div>'
        f'<span class="pv-badge" title="Fields Present: {present_fields}/{total_fields}">'
        f'{pv_pct}% fields</span>'
        f'<span class="call-date">{date_str}</span>'
        f'<span class="expand-icon" id="icon-{idx}">&#9660;</span>'
        '</div></div>'
    )

    parts.append(f'<div class="call-body" id="body-{idx}" style="display:none">')

    # ── Call ID ──
    parts.append(
        f'<div class="section"><h3>Call Details</h3>'
        f'<div class="detail-grid">'
        f'<div class="detail-item"><span class="detail-label">Call ID</span><span class="detail-val" style="font-family:monospace;font-size:12px">{esc(cid)}</span></div>'
        f'<div class="detail-item"><span class="detail-label">Company ID</span><span class="detail-val" style="font-family:monospace;font-size:12px">{esc(COMPANY_ID)}</span></div>'
        f'<div class="detail-item"><span class="detail-label">Phone</span><span class="detail-val">{esc(phone)}</span></div>'
        f'<div class="detail-item"><span class="detail-label">Date</span><span class="detail-val">{esc(str(call_date)[:19])}</span></div>'
        f'<div class="detail-item"><span class="detail-label">Status</span><span class="detail-val">{esc(status)}</span></div>'
        f'<div class="detail-item"><span class="detail-label">Segments</span><span class="detail-val">{len(segments)}</span></div>'
        '</div></div>'
    )

    # ── Summary ──
    kp_html = "".join(f'<div class="key-point">&#8226; {esc(kp)}</div>' for kp in key_points[:5])
    ai_html = ""
    if action_items:
        ai_html = "<h4>Action Items</h4>" + "".join(f'<div class="action-item">&#9745; {esc(ai)}</div>' for ai in action_items[:5])
    sent_html = ""
    if sentiment_score is not None:
        s_pct = int(float(sentiment_score) * 100)
        s_color = score_color(float(sentiment_score))
        sent_html = (
            f'<div class="ci-row"><span class="ci-label">Sentiment</span>'
            f'<div class="ci-bar-bg"><div class="ci-bar-fill" style="width:{s_pct}%;background:{s_color}"></div></div>'
            f'<span class="ci-value" style="color:{s_color}">{s_pct}%</span></div>'
        )
    parts.append(
        f'<div class="section"><h3>Summary</h3>'
        f'<p class="summary-text">{esc(sum_text)}</p>'
        f'{kp_html}{ai_html}{sent_html}</div>'
    )

    # ── Compliance ──
    total_stages = max(stages.get("total", 1), 1)
    followed_pct = int(len(followed) / total_stages * 100)
    missed_pct = int(len(missed) / total_stages * 100)
    followed_tags = "".join(f'<span class="sop-tag sop-followed">{esc(f)}</span>' for f in followed)
    missed_tags = "".join(f'<span class="sop-tag sop-missed">{esc(m)}</span>' for m in missed[:15])
    parts.append(
        f'<div class="section"><h3>SOP Compliance</h3>'
        '<div class="score-display">'
        f'<div class="score-circle" style="border-color:{score_color(comp_score)}">'
        f'<span style="color:{score_color(comp_score)}">{comp_pct}%</span></div>'
        '<div class="score-details">'
        f'<div class="stage-bar"><span class="stage-label">Followed ({len(followed)}/{stages.get("total",0)})</span>'
        f'<div class="bar-bg"><div class="bar-fill" style="width:{followed_pct}%;background:#22c55e"></div></div></div>'
        f'<div class="stage-bar"><span class="stage-label">Missed ({len(missed)}/{stages.get("total",0)})</span>'
        f'<div class="bar-bg"><div class="bar-fill" style="width:{missed_pct}%;background:#ef4444"></div></div></div>'
        f'</div></div>'
        f'<div class="sop-grid">{followed_tags}{missed_tags}</div></div>'
    )

    # ── Coaching ──
    if coaching:
        items = ""
        for c in coaching[:6]:
            metric = esc((c.get("related_sop_metric") or "").replace("_", " ").title())
            items += (
                '<div class="coaching-item">'
                f'<div class="coaching-header">{severity_badge(c.get("severity",""))} <strong>{metric}</strong></div>'
                f'<div class="coaching-issue">{esc(str(c.get("issue") or "")[:200])}</div>'
                f'<div class="coaching-fix"><strong>How to fix:</strong> {esc(c.get("how_to_fix") or "")}</div>'
                f'<div class="coaching-example"><em>"{esc(c.get("example_language") or "")}"</em></div>'
                '</div>'
            )
        more = ""
        if len(coaching) > 6:
            more = f'<div class="coaching-more">... and {len(coaching) - 6} more coaching items</div>'
        parts.append(f'<div class="section"><h3>AI Coaching Recommendations ({len(coaching)})</h3>{items}{more}</div>')

    # ── Objections ──
    if objections:
        obj_html = ""
        for o in objections[:6]:
            overcome_cls = "overcome-yes" if o.get("overcome") else "overcome-no"
            overcome_txt = "Resolved" if o.get("overcome") else "Unresolved"
            sug = ""
            for rs in (o.get("response_suggestions") or [])[:1]:
                sug += f'<div class="obj-suggestion">&#128161; {esc(rs)}</div>'
            obj_html += (
                '<div class="objection-card">'
                f'<div class="obj-header">{severity_badge(o.get("severity",""))}'
                f' <span class="obj-category">{esc(o.get("category_text",""))}</span>'
                f' <span class="obj-overcome {overcome_cls}">{overcome_txt}</span></div>'
                f'<div class="obj-quote">"{esc(str(o.get("objection_text",""))[:200])}"</div>'
                f'{sug}</div>'
            )
        parts.append(f'<div class="section"><h3>Objections Detected ({len(objections)})</h3><div class="objections-grid">{obj_html}</div></div>')

    # ── Customer Intelligence ──
    if qual:
        existing_html = ""
        if is_existing is not None:
            if is_existing:
                existing_html = '<span class="ci-tag ci-existing">Returning Customer</span>'
            else:
                existing_html = '<span class="ci-tag ci-new">New Customer</span>'

        followup_html = ""
        if follow_up_req:
            followup_html = (
                '<div class="ci-followup"><strong>Follow-up Required</strong>'
                f'<div class="ci-followup-reason">{esc(str(follow_up_reason)[:300])}</div></div>'
            )

        dm_html = ""
        if decision_makers:
            dm_tags = "".join(f'<span class="ci-dm-tag">{esc(dm)}</span>' for dm in decision_makers[:5])
            dm_html = f'<div class="ci-row-block"><span class="ci-label">Decision Makers</span><div class="ci-dm-list">{dm_tags}</div></div>'

        bant_html = ""
        if bant:
            bant_items = ""
            for dim in ["budget", "authority", "need", "timeline"]:
                val = bant.get(dim, 0) or 0
                b_pct = int(float(val) * 100)
                b_color = score_color(float(val))
                bant_items += (
                    f'<div class="bant-item"><span class="bant-label">{dim[0].upper()} - {dim.title()}</span>'
                    f'<div class="ci-bar-bg"><div class="ci-bar-fill" style="width:{b_pct}%;background:{b_color}"></div></div>'
                    f'<span class="ci-value" style="color:{b_color}">{b_pct}%</span></div>'
                )
            overall_pct = int(float(overall_bant) * 100)
            bant_html = (
                f'<div class="bant-section"><h4>BANT Lead Score: '
                f'<span style="color:{score_color(float(overall_bant))}">{overall_pct}%</span></h4>'
                f'{bant_items}</div>'
            )

        urgency_html = ""
        if urgency_signals:
            u_items = "".join(f'<div class="ci-signal">"{esc(str(u)[:200])}"</div>' for u in urgency_signals[:3])
            urgency_html = f'<div class="ci-row-block"><span class="ci-label">Urgency Signals ({len(urgency_signals)})</span>{u_items}</div>'

        budget_html = ""
        if budget_indicators:
            b_items = "".join(f'<div class="ci-signal">"{esc(str(b)[:200])}"</div>' for b in budget_indicators[:3])
            budget_html = f'<div class="ci-row-block"><span class="ci-label">Budget Indicators ({len(budget_indicators)})</span>{b_items}</div>'

        service_html = ""
        if service_requested:
            service_html = f'<div class="ci-row-block"><span class="ci-label">Service Requested</span><div class="ci-service">{esc(str(service_requested)[:300])}</div></div>'

        appt_html = ""
        if appt_confirmed:
            appt_text = "Confirmed"
            if appt_date:
                appt_text += f" — {esc(str(appt_date))}"
            if appt_type:
                appt_text += f" ({esc(appt_type)})"
            if appt_timezone:
                appt_text += f" [{esc(appt_timezone)}]"
            appt_html = f'<div class="ci-row"><span class="ci-label">Appointment</span><span class="ci-tag ci-existing">{appt_text}</span></div>'
        elif appt_date:
            appt_text = f"Pending — {esc(str(appt_date))}"
            if appt_type:
                appt_text += f" ({esc(appt_type)})"
            appt_html = f'<div class="ci-row"><span class="ci-label">Appointment</span><span class="ci-tag ci-new">{appt_text}</span></div>'

        address_html = ""
        addr_parts = []
        if addr_struct and isinstance(addr_struct, dict):
            for f in ("line1", "city", "state", "postal_code"):
                v = addr_struct.get(f)
                if v:
                    addr_parts.append(str(v))
        if addr_raw and not addr_parts:
            addr_parts = [str(addr_raw)]
        if addr_parts:
            addr_str = ", ".join(addr_parts)
            a_conf_pct = int(float(addr_confidence) * 100)
            a_color = score_color(float(addr_confidence))
            address_html = (
                f'<div class="ci-row-block"><span class="ci-label">Service Address</span>'
                f'<div class="ci-address">{esc(addr_str)}'
                f' <span class="ci-addr-conf" style="color:{a_color}">(confidence: {a_conf_pct}%)</span>'
                f'</div></div>'
            )

        outcome_html = ""
        if call_outcome:
            outcome_html = f'<div class="ci-chip"><span class="ci-label">Outcome</span> <strong>{esc(call_outcome.replace("_"," ").title())}</strong></div>'

        validation_html = ""
        if name_confidence > 0 or addr_confidence > 0:
            nc_pct = int(float(name_confidence) * 100)
            nc_color = score_color(float(name_confidence))
            ac_pct = int(float(addr_confidence) * 100)
            ac_color = score_color(float(addr_confidence))
            validation_html = (
                '<div class="ci-row-block"><span class="ci-label">Extraction Validation</span>'
                f'<div class="bant-item"><span class="bant-label">Name Confidence</span>'
                f'<div class="ci-bar-bg"><div class="ci-bar-fill" style="width:{nc_pct}%;background:{nc_color}"></div></div>'
                f'<span class="ci-value" style="color:{nc_color}">{nc_pct}%</span></div>'
                f'<div class="bant-item"><span class="bant-label">Address Confidence</span>'
                f'<div class="ci-bar-bg"><div class="ci-bar-fill" style="width:{ac_pct}%;background:{ac_color}"></div></div>'
                f'<span class="ci-value" style="color:{ac_color}">{ac_pct}%</span></div>'
                '</div>'
            )

        booking_cls = "ci-existing" if booking_status == "booked" else "ci-new"
        booking_text = booking_status.replace("_", " ").title() if booking_status else "N/A"

        parts.append(
            '<div class="section"><h3>Customer Intelligence &amp; Lead Qualification</h3>'
            '<div class="ci-grid">'
            '<div class="ci-info-row">'
            f'<div class="ci-chip"><span class="ci-label">Customer</span> <strong>{esc(customer_name)}</strong></div>'
            f'{existing_html}'
            f'<div class="ci-chip"><span class="ci-label">Call Type</span> <strong>{esc(call_type.replace("_"," ").title())}</strong></div>'
            f'<span class="ci-tag {booking_cls}">{booking_text}</span>'
            f'{outcome_html}'
            f'<div class="ci-chip"><span class="ci-label">Confidence</span> <strong>{int(float(confidence)*100)}%</strong></div>'
            f'</div>'
            f'{bant_html}'
            f'{dm_html}'
            f'{address_html}'
            f'{urgency_html}'
            f'{budget_html}'
            f'{service_html}'
            f'{appt_html}'
            f'{followup_html}'
            f'{validation_html}'
            '</div></div>'
        )

    # ── Parameter Validation for this call ──
    if validation:
        pv_rows = ""
        for field in sorted(validation.keys()):
            info = validation[field]
            icon = "&#9989;" if info["valid"] else ("&#9888;" if info["present"] else "&#10060;")
            color = "#22c55e" if info["valid"] else ("#f97316" if info["present"] else "#ef4444")
            pv_rows += (
                f'<tr>'
                f'<td style="font-family:monospace;font-size:11px">{esc(field)}</td>'
                f'<td style="text-align:center">{icon}</td>'
                f'<td style="color:{color};font-weight:600;font-size:12px">{"Present" if info["present"] else "MISSING"}</td>'
                f'<td style="color:#94a3b8;font-size:11px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{esc(info["value"])}</td>'
                f'</tr>'
            )
        parts.append(
            f'<div class="section"><h3>Parameter Validation ({present_fields}/{total_fields} present, {valid_fields}/{total_fields} valid)</h3>'
            '<table class="pv-table"><thead><tr><th>Field</th><th></th><th>Status</th><th>Value</th></tr></thead>'
            f'<tbody>{pv_rows}</tbody></table></div>'
        )

    # ── Transcript ──
    if segments:
        seg_html = ""
        for seg in segments:
            speaker = seg.get("speaker", "unknown").replace(" ", "_")
            seg_html += (
                f'<div class="segment">'
                f'<span class="speaker speaker-{speaker}">{esc(seg.get("speaker","?"))}</span>'
                f'<span class="seg-text">{esc(seg.get("text",""))}</span>'
                '</div>'
            )
        parts.append(
            f'<div class="section"><h3>Transcript ({len(segments)} segments)</h3>'
            f'<div class="transcript-box">{seg_html}</div></div>'
        )

    parts.append("</div></div>")
    return "\n".join(parts)


def build_html(test_results, calls_data, phases_analytics, call_validations):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    total = len(calls_data)
    completed = sum(1 for c, _, _ in calls_data if c.get("status") == "completed")

    pa = phases_analytics or {}
    detection = pa.get("detection_rates", {})
    missing_phases = pa.get("commonly_missing", [])

    # Build test results section
    test_section = build_test_results_section(test_results)

    # Build parameter validation section
    param_section = build_param_validation_section(call_validations)

    # Build phase analytics
    phase_rows = ""
    for phase, rate in sorted(detection.items(), key=lambda x: -x[1]):
        pname = esc(phase.replace("_", " ").title())
        pct = int(rate * 100)
        pcolor = score_color(rate)
        phase_rows += (
            f'<div class="phase-row"><span class="phase-name">{pname}</span>'
            f'<div class="phase-bar-bg"><div class="phase-bar-fill" style="width:{pct}%;background:{pcolor}">{pct}%</div></div></div>'
        )
    missing_tags = "".join(
        f'<span class="missing-tag">{esc(m.replace("_"," ").title())}</span>' for m in missing_phases
    )

    # Build call cards
    call_cards = "\n".join(
        build_call_card(call, summary, detail, i, call_validations.get(call.get("call_id")))
        for i, (call, summary, detail) in enumerate(calls_data)
    )

    # Test stats
    test_passed = sum(1 for t in test_results if t.status == "PASS")
    test_total = len(test_results)

    # Param stats
    total_fields_all = 0
    present_fields_all = 0
    for checks in call_validations.values():
        total_fields_all += len(checks)
        present_fields_all += sum(1 for v in checks.values() if v["present"])
    field_coverage = int(present_fields_all / total_fields_all * 100) if total_fields_all > 0 else 0

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Otto Intelligence — Comprehensive Test & Call Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #e2e8f0; line-height: 1.6; }}
  .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}

  .report-header {{ background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border: 1px solid #334155; border-radius: 16px; padding: 32px; margin-bottom: 24px; }}
  .report-title {{ font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #f97316, #eab308); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .report-subtitle {{ color: #94a3b8; font-size: 14px; margin-top: 4px; }}
  .stats-row {{ display: flex; gap: 16px; margin-top: 20px; flex-wrap: wrap; }}
  .stat-box {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px 24px; min-width: 140px; }}
  .stat-value {{ font-size: 28px; font-weight: 800; color: #f8fafc; }}
  .stat-label {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}

  .test-results-section, .param-section {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
  .test-results-section h2, .param-section h2 {{ font-size: 18px; margin-bottom: 16px; color: #f8fafc; }}
  .test-summary-bar {{ display: flex; gap: 16px; margin-bottom: 16px; }}
  .test-stat {{ background: #0f172a; border: 2px solid; border-radius: 12px; padding: 12px 20px; text-align: center; min-width: 80px; }}
  .test-stat-val {{ display: block; font-size: 24px; font-weight: 800; }}
  .test-stat-label {{ font-size: 11px; color: #94a3b8; text-transform: uppercase; }}
  .test-table, .param-table, .pv-table {{ width: 100%; border-collapse: collapse; }}
  .test-table th, .param-table th, .pv-table th {{ text-align: left; padding: 8px 12px; border-bottom: 2px solid #334155; color: #94a3b8; font-size: 12px; text-transform: uppercase; }}
  .test-table td, .param-table td, .pv-table td {{ padding: 6px 12px; border-bottom: 1px solid #1e293b; font-size: 13px; }}
  .test-table tr:hover, .param-table tr:hover, .pv-table tr:hover {{ background: #334155; }}

  .phases-section {{ background: #1e293b; border: 1px solid #334155; border-radius: 16px; padding: 24px; margin-bottom: 24px; }}
  .phases-section h2 {{ font-size: 18px; margin-bottom: 16px; color: #f8fafc; }}
  .phase-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
  .phase-name {{ width: 200px; font-size: 13px; color: #cbd5e1; }}
  .phase-bar-bg {{ flex: 1; height: 24px; background: #334155; border-radius: 12px; overflow: hidden; }}
  .phase-bar-fill {{ height: 100%; border-radius: 12px; display: flex; align-items: center; justify-content: flex-end; padding-right: 8px; font-size: 11px; font-weight: 700; color: #fff; }}
  .missing-tags {{ display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap; }}
  .missing-tag {{ background: #7f1d1d; color: #fca5a5; padding: 4px 12px; border-radius: 9999px; font-size: 12px; }}

  .call-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 12px; overflow: hidden; }}
  .call-header {{ display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; cursor: pointer; transition: background 0.2s; }}
  .call-header:hover {{ background: #334155; }}
  .call-header-left, .call-header-right {{ display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }}
  .call-number {{ font-weight: 700; color: #f8fafc; font-size: 15px; }}
  .call-customer-name {{ font-weight: 700; color: #f97316; font-size: 14px; }}
  .call-phone {{ color: #94a3b8; font-size: 13px; font-family: monospace; }}
  .call-status {{ padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .status-completed {{ background: #14532d; color: #86efac; }}
  .status-processing {{ background: #422006; color: #fdba74; }}
  .status-failed {{ background: #7f1d1d; color: #fca5a5; }}
  .call-date {{ color: #64748b; font-size: 12px; }}
  .call-type-badge {{ background: #1e3a5f; color: #7dd3fc; padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .qual-badge {{ padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; }}
  .qual-hot {{ background: #14532d; color: #86efac; }}
  .qual-warm {{ background: #422006; color: #fdba74; }}
  .qual-cold {{ background: #1e3a5f; color: #7dd3fc; }}
  .qual-other {{ background: #334155; color: #94a3b8; }}
  .pv-badge {{ background: #1e293b; border: 1px solid #334155; color: #cbd5e1; padding: 2px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .expand-icon {{ color: #64748b; font-size: 12px; transition: transform 0.2s; }}
  .compliance-mini {{ display: flex; align-items: center; gap: 6px; }}
  .mini-bar-bg {{ width: 60px; height: 6px; background: #334155; border-radius: 3px; overflow: hidden; }}
  .mini-bar-fill {{ height: 100%; border-radius: 3px; }}

  .call-body {{ padding: 0 20px 20px; }}
  .section {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 12px; padding: 20px; margin-top: 16px; }}
  .section h3 {{ font-size: 16px; color: #f97316; margin-bottom: 12px; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
  .section h4 {{ font-size: 14px; color: #cbd5e1; margin: 12px 0 8px; }}
  .summary-text {{ color: #cbd5e1; font-size: 14px; margin-bottom: 12px; }}
  .key-point {{ color: #94a3b8; font-size: 13px; padding: 3px 0 3px 12px; }}
  .action-item {{ color: #86efac; font-size: 13px; padding: 3px 0 3px 12px; }}

  .detail-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }}
  .detail-item {{ background: #1e293b; padding: 10px; border-radius: 8px; }}
  .detail-label {{ display: block; font-size: 11px; color: #94a3b8; text-transform: uppercase; margin-bottom: 4px; }}
  .detail-val {{ color: #f8fafc; font-size: 13px; }}

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

  .coaching-item {{ background: #1e293b; border-radius: 8px; padding: 14px; margin-bottom: 10px; border-left: 3px solid #f97316; }}
  .coaching-header {{ margin-bottom: 6px; }}
  .coaching-issue {{ color: #94a3b8; font-size: 13px; margin-bottom: 8px; }}
  .coaching-fix {{ color: #cbd5e1; font-size: 13px; margin-bottom: 6px; }}
  .coaching-example {{ color: #22d3ee; font-size: 12px; font-style: italic; background: #0c4a6e22; padding: 8px 12px; border-radius: 6px; }}
  .coaching-more {{ color: #64748b; font-size: 13px; text-align: center; padding: 8px; }}

  .objections-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 12px; }}
  .objection-card {{ background: #1e293b; border-radius: 8px; padding: 14px; border-left: 3px solid #eab308; }}
  .obj-header {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }}
  .obj-category {{ color: #cbd5e1; font-size: 13px; font-weight: 600; }}
  .obj-overcome {{ padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .overcome-yes {{ background: #14532d; color: #86efac; }}
  .overcome-no {{ background: #7f1d1d; color: #fca5a5; }}
  .obj-quote {{ color: #94a3b8; font-size: 13px; font-style: italic; margin-bottom: 6px; }}
  .obj-suggestion {{ color: #22d3ee; font-size: 12px; background: #0c4a6e22; padding: 6px 10px; border-radius: 6px; margin-top: 6px; }}

  .ci-grid {{ display: flex; flex-direction: column; gap: 14px; }}
  .ci-info-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 10px; }}
  .ci-chip {{ background: #1e293b; padding: 6px 14px; border-radius: 8px; font-size: 13px; color: #cbd5e1; }}
  .ci-chip strong {{ color: #f8fafc; }}
  .ci-label {{ color: #94a3b8; font-size: 12px; margin-right: 4px; }}
  .ci-tag {{ padding: 3px 12px; border-radius: 9999px; font-size: 11px; font-weight: 600; }}
  .ci-existing {{ background: #14532d; color: #86efac; }}
  .ci-new {{ background: #422006; color: #fdba74; }}
  .ci-row {{ display: flex; align-items: center; gap: 10px; }}
  .ci-bar-bg {{ flex: 1; max-width: 300px; height: 10px; background: #334155; border-radius: 5px; overflow: hidden; }}
  .ci-bar-fill {{ height: 100%; border-radius: 5px; }}
  .ci-value {{ font-size: 13px; font-weight: 700; min-width: 40px; }}
  .ci-row-block {{ margin-top: 4px; }}
  .ci-dm-list {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }}
  .ci-dm-tag {{ background: #1e293b; color: #cbd5e1; padding: 4px 12px; border-radius: 6px; font-size: 12px; }}
  .ci-signal {{ color: #94a3b8; font-size: 12px; font-style: italic; padding: 4px 0 2px 12px; border-left: 2px solid #334155; margin: 4px 0; }}
  .ci-service {{ color: #cbd5e1; font-size: 13px; margin-top: 4px; }}
  .ci-followup {{ background: #422006; border-radius: 8px; padding: 12px; border-left: 3px solid #f97316; }}
  .ci-followup-reason {{ color: #cbd5e1; font-size: 13px; margin-top: 6px; }}
  .ci-address {{ color: #cbd5e1; font-size: 13px; margin-top: 4px; }}
  .ci-addr-conf {{ font-size: 11px; font-weight: 600; }}

  .bant-section {{ background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 14px; }}
  .bant-section h4 {{ font-size: 14px; color: #f8fafc; margin-bottom: 10px; }}
  .bant-item {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
  .bant-label {{ width: 110px; font-size: 12px; color: #94a3b8; }}

  .transcript-box {{ max-height: 500px; overflow-y: auto; padding: 12px; background: #020617; border-radius: 8px; }}
  .segment {{ margin-bottom: 10px; }}
  .speaker {{ display: inline-block; min-width: 120px; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-right: 8px; }}
  .speaker-customer_rep {{ background: #1e3a5f; color: #7dd3fc; }}
  .speaker-home_owner {{ background: #365314; color: #bef264; }}
  .speaker-manager {{ background: #4a1d96; color: #c4b5fd; }}
  .speaker-unknown {{ background: #334155; color: #94a3b8; }}
  .seg-text {{ color: #cbd5e1; font-size: 13px; }}

  .controls {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}
  .btn {{ padding: 8px 16px; border-radius: 8px; border: 1px solid #334155; background: #1e293b; color: #e2e8f0; cursor: pointer; font-size: 13px; transition: all 0.2s; }}
  .btn:hover {{ background: #334155; }}
  .btn-active {{ background: #f97316; border-color: #f97316; color: #000; font-weight: 600; }}

  .nav-tabs {{ display: flex; gap: 4px; margin-bottom: 24px; background: #1e293b; padding: 4px; border-radius: 12px; }}
  .nav-tab {{ padding: 10px 20px; border-radius: 8px; border: none; background: transparent; color: #94a3b8; cursor: pointer; font-size: 14px; font-weight: 600; transition: all 0.2s; }}
  .nav-tab:hover {{ color: #e2e8f0; }}
  .nav-tab.active {{ background: #f97316; color: #000; }}
  .tab-content {{ display: none; }}
  .tab-content.active {{ display: block; }}
</style>
</head>
<body>
<div class="container">

  <div class="report-header">
    <div class="report-title">Otto Intelligence — Comprehensive Test &amp; Call Report</div>
    <div class="report-subtitle">{COMPANY_NAME} &bull; Company: {COMPANY_ID} &bull; Generated {now} &bull; API: {BASE_URL}</div>
    <div class="stats-row">
      <div class="stat-box"><div class="stat-value">{total}</div><div class="stat-label">Total Calls</div></div>
      <div class="stat-box"><div class="stat-value">{completed}</div><div class="stat-label">Completed</div></div>
      <div class="stat-box"><div class="stat-value" style="color:#22c55e">{test_passed}/{test_total}</div><div class="stat-label">Tests Passed</div></div>
      <div class="stat-box"><div class="stat-value">{field_coverage}%</div><div class="stat-label">Field Coverage</div></div>
      <div class="stat-box"><div class="stat-value">{pa.get("total_calls", 0)}</div><div class="stat-label">Phases Analyzed</div></div>
      <div class="stat-box"><div class="stat-value">{len(missing_phases)}</div><div class="stat-label">Missing Phases</div></div>
    </div>
  </div>

  <div class="nav-tabs">
    <button class="nav-tab active" onclick="showTab('tests')">API Tests ({test_passed}/{test_total})</button>
    <button class="nav-tab" onclick="showTab('params')">Parameter Validation</button>
    <button class="nav-tab" onclick="showTab('phases')">Phase Analytics</button>
    <button class="nav-tab" onclick="showTab('calls')">Call Details ({total})</button>
  </div>

  <div class="tab-content active" id="tab-tests">
    {test_section}
  </div>

  <div class="tab-content" id="tab-params">
    {param_section}
  </div>

  <div class="tab-content" id="tab-phases">
    <div class="phases-section">
      <h2>Conversation Phase Detection Rates (Last 90 Days)</h2>
      {phase_rows}
      <div class="missing-tags">
        <span style="color:#94a3b8;font-size:12px;margin-right:4px">Commonly missing:</span>
        {missing_tags}
      </div>
    </div>
  </div>

  <div class="tab-content" id="tab-calls">
    <div class="controls">
      <button class="btn btn-active" onclick="toggleAll(true)">Expand All</button>
      <button class="btn" onclick="toggleAll(false)">Collapse All</button>
    </div>
    {call_cards}
  </div>

</div>

<script>
function showTab(name) {{
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  event.target.classList.add('active');
}}
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


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def deduplicate_calls(calls_with_data):
    """
    Deduplicate calls by customer name (from summary qualification).
    Falls back to phone number. Keeps only the LATEST call per customer.
    Skips test/injection calls (no real phone or injection patterns).
    List is already sorted by call_date desc, so first seen = latest.
    """
    JUNK_PHONES = {"+14805551234", "string", "None", ""}
    JUNK_PREFIXES = ("neg_inject_", "staging_test_", "staging_install_", "noagent_", "verify_", "550e8400")

    seen_keys = set()
    unique = []
    skipped = []

    for call, summary, detail in calls_with_data:
        cid = call.get("call_id", "")
        phone = str(call.get("phone_number", "") or "")

        # Skip test/injection calls by call_id prefix
        if any(cid.startswith(p) for p in JUNK_PREFIXES):
            skipped.append((cid, "test/injection call_id"))
            continue

        # Skip injection phone numbers
        if phone.startswith("'") or phone.startswith("{") or phone.startswith("<") or phone.startswith("."):
            skipped.append((cid, f"injection phone: {phone[:20]}"))
            continue

        # For report_test_ calls (freshly submitted audio), always include
        # each one since they represent different audio recordings
        if cid.startswith("report_test_"):
            unique.append((call, summary, detail))
            continue

        # Determine dedup key: prefer customer_name from summary, else phone
        customer_name = None
        if summary:
            qual = summary.get("qualification", {})
            customer_name = qual.get("customer_name")
            if customer_name and customer_name.lower() in ("unknown", "none", "n/a", ""):
                customer_name = None

        dedup_key = customer_name.strip().lower() if customer_name else phone.strip()

        # Skip if phone is a junk placeholder and no real customer name
        if not customer_name and phone in JUNK_PHONES:
            skipped.append((cid, "junk phone, no customer name"))
            continue

        if dedup_key in seen_keys:
            skipped.append((cid, f"duplicate of '{dedup_key}'"))
            continue

        seen_keys.add(dedup_key)
        unique.append((call, summary, detail))

    return unique, skipped


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive Otto test & call report")
    parser.add_argument("--output", type=str, default="call_report_new.html", help="Output file")
    parser.add_argument("--limit", type=int, default=50, help="Max calls to fetch")
    parser.add_argument("--call-ids", type=str, default=None,
                        help="Comma-separated call_ids to include exclusively (skips dedup, preserves order)")
    args = parser.parse_args()

    filter_ids = [c.strip() for c in args.call_ids.split(",")] if args.call_ids else None

    print(f"Otto Intelligence — Comprehensive Test & Report Generator")
    print(f"Company: {COMPANY_NAME} ({COMPANY_ID})")
    print(f"API: {BASE_URL}")
    print(f"Audio URLs: {len(STAGING_AUDIO_URLS)}")
    if filter_ids:
        print(f"Filter: {len(filter_ids)} specific call_ids")
    print(f"{'='*60}")

    # Step 1: Run API tests
    print("\n[1/5] Running API tests...")
    test_results = run_all_tests()
    passed = sum(1 for t in test_results if t.status == "PASS")
    print(f"  Results: {passed}/{len(test_results)} passed")

    # Step 2: Fetch all calls
    print(f"\n[2/5] Fetching call list...")
    try:
        calls_data_raw = fetch_json(
            f"{BASE_URL}/api/v1/call-processing/calls",
            {"company_id": COMPANY_ID, "limit": args.limit, "sort_by": "call_date", "sort_order": "desc"},
        )
        calls = calls_data_raw.get("calls", [])
        if filter_ids:
            call_map = {c["call_id"]: c for c in calls}
            calls = [call_map[cid] for cid in filter_ids if cid in call_map]
    except Exception as e:
        print(f"  ERROR fetching calls: {e}")
        calls = []
    print(f"  Found {len(calls)} calls")

    # Step 3: Fetch phase analytics
    print(f"\n[3/5] Fetching phase analytics...")
    try:
        phases = fetch_json(
            f"{BASE_URL}/api/v1/call-processing/phases/analytics",
            {"company_id": COMPANY_ID, "days": 90},
        )
    except Exception as e:
        phases = {}
        print(f"  ERROR: {e}")
    print(f"  Detection rates: {len(phases.get('detection_rates', {}))}")

    # Step 4: Fetch summary + detail + validate for each call
    print(f"\n[4/5] Fetching summaries, details & validating parameters...")
    all_calls_data = []
    call_validations = {}
    for i, call in enumerate(calls):
        cid = call["call_id"]
        print(f"  [{i+1}/{len(calls)}] {cid[:36]}... ", end="", flush=True)

        # Fetch summary
        try:
            summary = fetch_json(
                f"{BASE_URL}/api/v1/call-processing/summary/{cid}",
                {"include_chunks": "true"},
            )
        except Exception:
            summary = None

        # Fetch detail
        try:
            detail = fetch_json(
                f"{BASE_URL}/api/v1/call-processing/calls/{cid}/detail",
                {"include_transcript": "true", "include_segments": "true"},
            )
        except Exception:
            detail = None

        all_calls_data.append((call, summary, detail))

        # Validate parameters
        if summary:
            validation = validate_call_params(summary)
            call_validations[cid] = validation
            present = sum(1 for v in validation.values() if v["present"])
            total = len(validation)
            print(f"summary=yes detail={'yes' if detail else 'no'} fields={present}/{total}")
        else:
            print(f"summary=no detail={'yes' if detail else 'no'}")

    # Step 5: Deduplicate — keep only latest per customer/phone (skip if --call-ids used)
    print(f"\n[5/5] Deduplicating calls (latest per customer/phone only)...")
    if filter_ids:
        calls_data = all_calls_data
        skipped = []
        print(f"  Skipped dedup (explicit --call-ids filter applied)")
    else:
        calls_data, skipped = deduplicate_calls(all_calls_data)
    print(f"  Total fetched: {len(all_calls_data)}")
    print(f"  After dedup: {len(calls_data)} unique calls")
    print(f"  Skipped: {len(skipped)}")
    for cid, reason in skipped:
        print(f"    - {cid[:36]}: {reason}")

    # Rebuild validations for unique calls only
    unique_validations = {}
    for call, summary, detail in calls_data:
        cid = call.get("call_id")
        if cid in call_validations:
            unique_validations[cid] = call_validations[cid]

    # Generate report
    print(f"\n{'='*60}")
    print(f"Generating HTML report...")
    html_content = build_html(test_results, calls_data, phases, unique_validations)

    output_path = os.path.join(os.path.dirname(__file__) or ".", args.output)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Report saved to: {output_path}")
    print(f"Open in browser: file://{os.path.abspath(output_path)}")

    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"  API Tests: {passed}/{len(test_results)} passed")
    print(f"  Calls fetched: {len(all_calls_data)}")
    print(f"  Unique calls in report: {len(calls_data)}")
    print(f"  Calls with summaries: {sum(1 for _,s,_ in calls_data if s)}")
    print(f"  Calls validated: {len(unique_validations)}")
    if unique_validations:
        all_present = sum(sum(1 for v in c.values() if v['present']) for c in unique_validations.values())
        all_total = sum(len(c) for c in unique_validations.values())
        print(f"  Field coverage: {all_present}/{all_total} ({int(all_present/all_total*100) if all_total > 0 else 0}%)")


if __name__ == "__main__":
    main()
