"""
Integration tests using staging SOP + audio data.
Company: 91ecfcb9-fc40-4792-ba47-65b273cec204 | SOP: Intake Calls | 4 audio URLs.
"""
import pytest
import requests
import uuid

from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    STAGING_AUDIO_URLS,
    staging_process_payload,
    SOP_URL,
    SOP_ID,
)


@pytest.mark.usefixtures("api_available")
class TestStagingCompany:
    """Tests using staging company_id (real data)."""

    def test_list_calls_staging_company(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 10},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["company_id"] == STAGING_COMPANY_ID
        assert "calls" in data
        assert "total" in data

    def test_list_summaries_staging_company(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summaries",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 10},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data["company_id"] == STAGING_COMPANY_ID
        assert "summaries" in data
        assert "total" in data


@pytest.mark.usefixtures("api_available")
class TestStagingAudioProcess:
    """Submit one staging audio URL for processing (unique call_id each run)."""

    def test_process_one_staging_audio(self, api_base_url, api_headers):
        audio_url = STAGING_AUDIO_URLS[0]
        call_id = f"staging_test_{uuid.uuid4().hex[:12]}"
        payload = staging_process_payload(call_id=call_id, audio_url=audio_url)
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=payload,
            timeout=15,
        )
        assert r.status_code == 202, f"Unexpected {r.status_code}: {r.text}"
        data = r.json()
        assert data.get("call_id") == call_id
        assert data.get("status") in ("queued", "processing")
        assert "job_id" in data
        assert "status_url" in data
