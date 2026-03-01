#!/usr/bin/env python3
"""
Upload staging SOP and submit 4 audio recordings for processing (install data into Otto).
Requires: .env with OTTO_API_KEY (and optionally OTTO_API_BASE_URL).
"""
import os
import sys
import uuid

import requests
from dotenv import load_dotenv

# Add repo root so we can import from tests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    STAGING_AUDIO_URLS,
    SOP_URL,
    staging_process_payload,
)

BASE_URL = os.getenv("OTTO_API_BASE_URL", "https://ottoai.shunyalabs.ai").rstrip("/")
API_KEY = os.getenv("OTTO_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}


def upload_sop():
    """Upload Intake Calls SOP via file_url (multipart/form-data)."""
    url = f"{BASE_URL}/api/v1/sop/documents/upload"
    # multipart/form-data: file_url, company_id, sop_name, target_role
    files = {
        "file_url": (None, SOP_URL),
        "company_id": (None, STAGING_COMPANY_ID),
        "sop_name": (None, "Intake Calls"),
        "target_role": (None, "customer_rep"),
    }
    r = requests.post(url, headers=HEADERS, files=files, timeout=60)
    if r.status_code not in (200, 202):
        print(f"SOP upload failed: {r.status_code} {r.text}")
        return None
    data = r.json()
    print(f"SOP upload: job_id={data.get('job_id')} status={data.get('status')}")
    return data.get("job_id")


def submit_calls():
    """Submit all 4 staging audio URLs for call processing."""
    results = []
    for i, audio_url in enumerate(STAGING_AUDIO_URLS):
        call_id = f"staging_install_{uuid.uuid4().hex[:12]}"
        payload = staging_process_payload(call_id=call_id, audio_url=audio_url)
        try:
            r = requests.post(
                f"{BASE_URL}/api/v1/call-processing/process",
                headers={**HEADERS, "Content-Type": "application/json"},
                json=payload,
                timeout=45,
            )
        except requests.exceptions.Timeout:
            print(f"  Call {i+1} timeout (server may still process)")
            results.append({"call_id": call_id, "error": "timeout"})
            continue
        except requests.exceptions.RequestException as e:
            print(f"  Call {i+1} error: {e}")
            results.append({"call_id": call_id, "error": str(e)})
            continue
        if r.status_code not in (202, 409):
            print(f"  Call {i+1} failed: {r.status_code} {r.text[:200]}")
            results.append({"call_id": call_id, "status_code": r.status_code})
            continue
        data = r.json()
        results.append({"call_id": call_id, "job_id": data.get("job_id"), "status": data.get("status")})
        print(f"  Call {i+1}: call_id={call_id} job_id={data.get('job_id')} status={data.get('status')}")
    return results


def main():
    if not API_KEY:
        print("OTTO_API_KEY not set in .env. Exiting.")
        sys.exit(1)
    print("Installing staging data...")
    print("1. Uploading SOP (Intake Calls)...")
    upload_sop()
    print("2. Submitting 4 audio recordings for processing...")
    submit_calls()
    print("Done.")


if __name__ == "__main__":
    main()
