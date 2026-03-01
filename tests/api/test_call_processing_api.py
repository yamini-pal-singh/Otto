"""
API tests for Otto Call Processing (CSR pipeline).
Data and expectations from project_docs/Updated_Otto_API_Documentation.md.
"""
import pytest
import requests

from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    INVALID_COMPANY_ID_NOT_UUID,
    PROCESS_PAYLOAD_MINIMAL,
    PROCESS_PAYLOAD_MISSING_AGENT,
    PROCESS_PAYLOAD_CSR,
    JOB_STATUS_VALUES,
    LIST_CALLS_PARAMS,
    LIST_SUMMARIES_PARAMS,
    SUMMARY_INCLUDE_CHUNKS,
    DETAIL_PARAMS,
    REAL_CALL_ID,
    SAMPLE_JOB_ID,
    PHASES_SEARCH_PARAMS,
    PHASES_ANALYTICS_PARAMS,
)


@pytest.mark.usefixtures("api_available")
class TestCallProcessingAPI:
    """Call processing pipeline API tests (CSR-relevant)."""

    def test_health(self, api_base_url):
        r = requests.get(f"{api_base_url}/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("status") == "healthy"
        assert "service" in data

    def test_api_status_requires_auth(self, api_base_url):
        r = requests.get(f"{api_base_url}/api/v1/status", timeout=10)
        assert r.status_code == 401

    def test_api_status_with_key(self, api_base_url, api_headers):
        r = requests.get(f"{api_base_url}/api/v1/status", headers=api_headers, timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data.get("api_version") == "v1"
        cp_status = data.get("features", {}).get("call_processing")
        assert cp_status in ("active", "pending_implementation"), f"Unexpected call_processing status: {cp_status}"

    def test_list_calls_requires_company_id(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code in (400, 422)

    def test_list_calls_with_valid_uuid_company_id(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={k: v for k, v in LIST_CALLS_PARAMS.items() if k in ("company_id", "limit", "sort_by", "sort_order")},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("company_id") == STAGING_COMPANY_ID
        assert "calls" in data
        assert "total" in data
        assert isinstance(data["calls"], list)
        assert data.get("limit") == LIST_CALLS_PARAMS["limit"]

    def test_list_calls_with_invalid_company_id_uuid(self, api_base_url, api_headers):
        """API may reject with 400/422 or return 200 with empty results for non-UUID company_id."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": INVALID_COMPANY_ID_NOT_UUID, "limit": 5},
            timeout=10,
        )
        if r.status_code in (400, 422):
            data = r.json()
            assert "detail" in data
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data.get("calls"), list)
            assert data.get("total", 0) == 0

    def test_list_summaries_with_doc_params(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summaries",
            headers=api_headers,
            params={k: v for k, v in LIST_SUMMARIES_PARAMS.items() if k in ("company_id", "limit", "offset", "sort_by", "sort_order")},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert data.get("company_id") == STAGING_COMPANY_ID
        assert "summaries" in data
        assert "total" in data
        assert isinstance(data["summaries"], list)
        assert data.get("limit") == LIST_SUMMARIES_PARAMS["limit"]

    def test_process_accepts_minimal_valid_payload_with_agent(self, api_base_url, api_headers):
        """Process requires metadata.agent.id and metadata.agent.name (per API doc)."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_MINIMAL,
            timeout=15,
        )
        assert r.status_code in (202, 409), f"Unexpected {r.status_code}: {r.text}"
        if r.status_code == 202:
            data = r.json()
            assert "job_id" in data
            assert data.get("call_id") == PROCESS_PAYLOAD_MINIMAL["call_id"]
            assert data.get("status") in ("queued", "processing")
            assert "status_url" in data

    def test_process_rejects_invalid_company_id_uuid(self, api_base_url, api_headers):
        payload = {**PROCESS_PAYLOAD_MINIMAL, "company_id": INVALID_COMPANY_ID_NOT_UUID}
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=payload,
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422, got {r.status_code}: {r.text}"
        data = r.json()
        assert "detail" in data

    def test_process_accepts_or_rejects_missing_agent_metadata(self, api_base_url, api_headers):
        """API may reject missing agent metadata (400) or accept gracefully (202/409)."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_MISSING_AGENT,
            timeout=15,
        )
        if r.status_code in (400, 422):
            data = r.json()
            assert "detail" in data
        else:
            # API accepts payload without agent metadata
            assert r.status_code in (202, 409), f"Unexpected {r.status_code}: {r.text}"

    def test_status_endpoint_structure(self, api_base_url, api_headers):
        """Status returns job_id, status in (queued|processing|completed|failed), progress."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/status/{SAMPLE_JOB_ID}",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            assert "job_id" in data
            assert data["status"] in JOB_STATUS_VALUES
            assert "progress" in data
            progress = data["progress"]
            assert "percent" in progress
            assert "current_step" in progress
            assert "steps_completed" in progress

    def test_summary_by_call_id_accepts_include_chunks(self, api_base_url, api_headers):
        """Fetch summary for a real completed call and validate response structure."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/{REAL_CALL_ID}",
            headers=api_headers,
            params=SUMMARY_INCLUDE_CHUNKS,
            timeout=10,
        )
        assert r.status_code == 200, f"Expected 200 for real call_id, got {r.status_code}"
        data = r.json()
        assert data.get("call_id") == REAL_CALL_ID
        assert data.get("company_id") == STAGING_COMPANY_ID
        assert "summary" in data
        assert "compliance" in data
        assert "qualification" in data
        assert "objections" in data

    def test_call_detail_structure(self, api_base_url, api_headers):
        """Fetch detail for a real completed call and validate transcript/segments."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls/{REAL_CALL_ID}/detail",
            headers=api_headers,
            params=DETAIL_PARAMS,
            timeout=10,
        )
        assert r.status_code == 200, f"Expected 200 for real call_id, got {r.status_code}"
        data = r.json()
        assert data.get("call_id") == REAL_CALL_ID
        assert data.get("company_id") == STAGING_COMPANY_ID
        assert "status" in data
        assert "rep_role" in data
        # Real completed call should have transcript and segments
        assert data.get("transcript") is not None
        assert isinstance(data["transcript"], str)
        assert len(data["transcript"]) > 0
        assert data.get("segments") is not None
        assert isinstance(data["segments"], list)
        assert len(data["segments"]) > 0
        for seg in data["segments"]:
            assert "speaker" in seg
            assert "text" in seg

    def test_phases_search_requires_company_id(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/search",
            headers=api_headers,
            params={"limit": 10},
            timeout=10,
        )
        assert r.status_code in (400, 422)

    def test_phases_search_with_company_id(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/search",
            headers=api_headers,
            params={k: PHASES_SEARCH_PARAMS[k] for k in ("company_id", "limit")},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "company_id" in data
        assert "calls" in data or "total" in data

    def test_phases_analytics_with_company_id(self, api_base_url, api_headers):
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/analytics",
            headers=api_headers,
            params={k: PHASES_ANALYTICS_PARAMS[k] for k in ("company_id", "days")},
            timeout=10,
        )
        assert r.status_code == 200
        data = r.json()
        assert "company_id" in data
        # API returns: total_calls, avg_time_per_phase, detection_rates, commonly_missing
        assert (
            "total_calls" in data
            or "total_calls_analyzed" in data
            or "phase_distribution" in data
            or "detection_rates" in data
        )
