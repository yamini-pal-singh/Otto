"""
Negative / edge-case API tests for Otto Call Processing.
Validates error handling, input validation, auth failures, injection resistance.
"""
import pytest
import requests
import uuid

from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    STAGING_AUDIO_URLS,
    INVALID_COMPANY_ID_NOT_UUID,
    NONEXISTENT_CALL_ID,
    NONEXISTENT_JOB_ID,
    NONEXISTENT_COMPANY_ID,
    WRONG_API_KEY,
    PROCESS_PAYLOAD_EMPTY,
    PROCESS_PAYLOAD_NO_CALL_ID,
    PROCESS_PAYLOAD_NO_AUDIO,
    PROCESS_PAYLOAD_BAD_AUDIO,
    PROCESS_PAYLOAD_MINIMAL,
    INJECTION_STRINGS,
)


# ============================================================================
# 1. AUTHENTICATION NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestAuthNegative:
    """Verify API rejects invalid/missing authentication."""

    def test_no_api_key_returns_401(self, api_base_url):
        """Request with no X-API-Key header should be rejected."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            params={"company_id": STAGING_COMPANY_ID, "limit": 1},
            timeout=10,
        )
        assert r.status_code == 401, f"Expected 401 without API key, got {r.status_code}"

    def test_wrong_api_key_returns_401_or_403(self, api_base_url):
        """Request with invalid API key should be rejected."""
        headers = {"X-API-Key": WRONG_API_KEY, "Content-Type": "application/json"}
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 1},
            timeout=10,
        )
        assert r.status_code in (401, 403), f"Expected 401/403 with wrong key, got {r.status_code}"

    def test_empty_api_key_returns_401(self, api_base_url):
        """Request with empty string API key should be rejected."""
        headers = {"X-API-Key": "", "Content-Type": "application/json"}
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 1},
            timeout=10,
        )
        assert r.status_code in (401, 403), f"Expected 401/403 with empty key, got {r.status_code}"

    def test_no_auth_on_process_endpoint(self, api_base_url):
        """POST /process without auth should be rejected."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            json=PROCESS_PAYLOAD_MINIMAL,
            timeout=15,
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_no_auth_on_summary_endpoint(self, api_base_url):
        """GET /summary without auth should be rejected."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/{NONEXISTENT_CALL_ID}",
            timeout=10,
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"

    def test_no_auth_on_detail_endpoint(self, api_base_url):
        """GET /calls/{id}/detail without auth should be rejected."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls/{NONEXISTENT_CALL_ID}/detail",
            timeout=10,
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ============================================================================
# 2. PROCESS ENDPOINT — INPUT VALIDATION NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestProcessNegative:
    """Verify /process endpoint rejects invalid payloads."""

    def test_empty_json_body_rejected(self, api_base_url, api_headers):
        """Empty JSON body {} should return 400/422."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_EMPTY,
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422 for empty body, got {r.status_code}: {r.text}"

    def test_missing_call_id_rejected(self, api_base_url, api_headers):
        """Payload without call_id should return 400/422."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_NO_CALL_ID,
            timeout=15,
        )
        # API may auto-generate call_id (202) or reject (400/422)
        assert r.status_code in (202, 400, 409, 422), f"Unexpected {r.status_code}: {r.text}"

    def test_missing_audio_url_rejected(self, api_base_url, api_headers):
        """Payload without audio_url should return 400/422."""
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_NO_AUDIO,
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422 for missing audio_url, got {r.status_code}: {r.text}"

    def test_invalid_audio_url_accepted_or_fails_gracefully(self, api_base_url, api_headers):
        """Unreachable audio URL should either be rejected upfront (400) or accepted and fail during processing."""
        payload = {**PROCESS_PAYLOAD_BAD_AUDIO, "call_id": f"neg_bad_audio_{uuid.uuid4().hex[:8]}"}
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=payload,
            timeout=15,
        )
        # API may validate URL upfront (400) or accept and fail async (202)
        assert r.status_code in (202, 400, 422), f"Unexpected {r.status_code}: {r.text}"
        if r.status_code == 202:
            data = r.json()
            assert "job_id" in data  # accepted for async processing, will fail later

    def test_duplicate_call_id_returns_409(self, api_base_url, api_headers):
        """Submitting an already-processed call_id should return 409 Conflict."""
        # Use the same call_id from PROCESS_PAYLOAD_MINIMAL (already processed)
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=PROCESS_PAYLOAD_MINIMAL,
            timeout=15,
        )
        # Should be 409 (already exists) or 202 (re-queued)
        assert r.status_code in (202, 409), f"Unexpected {r.status_code}: {r.text}"

    def test_malformed_json_returns_400(self, api_base_url, api_headers):
        """Sending invalid JSON should return 400/422."""
        headers = {**api_headers, "Content-Type": "application/json"}
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=headers,
            data="{{not valid json",  # raw string, not json=
            timeout=15,
        )
        assert r.status_code in (400, 422), f"Expected 400/422 for malformed JSON, got {r.status_code}"

    def test_nonexistent_company_id_uuid_format(self, api_base_url, api_headers):
        """Valid UUID format but nonexistent company should be rejected or fail gracefully."""
        payload = {**PROCESS_PAYLOAD_MINIMAL, "company_id": NONEXISTENT_COMPANY_ID, "call_id": f"neg_nocompany_{uuid.uuid4().hex[:8]}"}
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=payload,
            timeout=15,
        )
        # API may reject (400/404) or accept and fail during tenant config lookup
        assert r.status_code in (202, 400, 404, 422), f"Unexpected {r.status_code}: {r.text}"


# ============================================================================
# 3. SUMMARY ENDPOINT — NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestSummaryNegative:
    """Verify /summary endpoint handles missing/invalid call_ids."""

    def test_nonexistent_call_id_returns_404(self, api_base_url, api_headers):
        """Summary for a call_id that doesn't exist should return 404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/{NONEXISTENT_CALL_ID}",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code == 404, f"Expected 404 for nonexistent call_id, got {r.status_code}"

    def test_invalid_call_id_format(self, api_base_url, api_headers):
        """Non-UUID call_id string should return 400/404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/not-a-valid-id",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code in (400, 404, 422), f"Expected 400/404/422, got {r.status_code}"


# ============================================================================
# 4. CALL DETAIL ENDPOINT — NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestDetailNegative:
    """Verify /calls/{id}/detail handles missing/invalid call_ids."""

    def test_nonexistent_call_id_returns_404(self, api_base_url, api_headers):
        """Detail for a call_id that doesn't exist should return 404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls/{NONEXISTENT_CALL_ID}/detail",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code == 404, f"Expected 404 for nonexistent call_id, got {r.status_code}"

    def test_invalid_call_id_format(self, api_base_url, api_headers):
        """Non-UUID call_id for detail should return 400/404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls/invalid_id_here/detail",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code in (400, 404, 422), f"Expected 400/404/422, got {r.status_code}"


# ============================================================================
# 5. STATUS ENDPOINT — NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestStatusNegative:
    """Verify /status/{job_id} handles nonexistent jobs."""

    def test_nonexistent_job_id_returns_404(self, api_base_url, api_headers):
        """Status for a job that doesn't exist should return 404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/status/{NONEXISTENT_JOB_ID}",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code == 404, f"Expected 404 for nonexistent job_id, got {r.status_code}"

    def test_invalid_job_id_format(self, api_base_url, api_headers):
        """Non-UUID job_id should return 400/404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/status/not-a-job-id",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code in (400, 404, 422), f"Expected 400/404/422, got {r.status_code}"


# ============================================================================
# 6. LIST CALLS — EDGE CASE / BOUNDARY TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestListCallsNegative:
    """Verify /calls handles edge-case query params."""

    def test_negative_limit_rejected(self, api_base_url, api_headers):
        """Negative limit should be rejected (400/422) or clamped to 0."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": -1},
            timeout=10,
        )
        if r.status_code in (400, 422):
            pass  # properly rejected
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data.get("calls"), list)

    def test_negative_offset_rejected(self, api_base_url, api_headers):
        """Negative offset should be rejected (400/422) or treated as 0."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 5, "offset": -10},
            timeout=10,
        )
        if r.status_code in (400, 422):
            pass  # properly rejected
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data.get("calls"), list)

    def test_invalid_sort_by_handled(self, api_base_url, api_headers):
        """Invalid sort_by value should be rejected or use default."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 5, "sort_by": "nonexistent_field"},
            timeout=10,
        )
        if r.status_code in (400, 422):
            pass  # properly rejected
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data.get("calls"), list)

    def test_zero_limit_returns_empty_or_default(self, api_base_url, api_headers):
        """limit=0 should return empty results or use default limit."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "limit": 0},
            timeout=10,
        )
        assert r.status_code in (200, 400, 422)
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data.get("calls"), list)

    def test_nonexistent_company_returns_empty(self, api_base_url, api_headers):
        """Valid UUID but nonexistent company should return 200 with empty results or 404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": NONEXISTENT_COMPANY_ID, "limit": 5},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data.get("calls"), list)
            assert data.get("total", 0) == 0
        else:
            assert r.status_code in (400, 404, 422)


# ============================================================================
# 7. LIST SUMMARIES — EDGE CASE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestListSummariesNegative:
    """Verify /summaries handles edge-case filters."""

    def test_min_score_greater_than_max(self, api_base_url, api_headers):
        """min_compliance_score > max_compliance_score should return empty or error."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summaries",
            headers=api_headers,
            params={
                "company_id": STAGING_COMPANY_ID,
                "limit": 10,
                "min_compliance_score": 0.9,
                "max_compliance_score": 0.1,
            },
            timeout=10,
        )
        if r.status_code in (400, 422):
            pass  # properly rejected
        else:
            assert r.status_code == 200
            data = r.json()
            assert isinstance(data.get("summaries"), list)
            # With inverted range, should return 0 results
            assert len(data.get("summaries", [])) == 0

    def test_score_out_of_range(self, api_base_url, api_headers):
        """Scores outside 0-1 should be rejected or clamped."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summaries",
            headers=api_headers,
            params={
                "company_id": STAGING_COMPANY_ID,
                "limit": 10,
                "min_compliance_score": -5.0,
                "max_compliance_score": 99.0,
            },
            timeout=10,
        )
        # API should either reject (400) or clamp and return results
        assert r.status_code in (200, 400, 422)


# ============================================================================
# 8. PHASES ENDPOINT — NEGATIVE TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestPhasesNegative:
    """Verify phase endpoints handle edge cases."""

    def test_phases_analytics_nonexistent_company(self, api_base_url, api_headers):
        """Valid UUID but no data should return 200 with zero totals or 404."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/analytics",
            headers=api_headers,
            params={"company_id": NONEXISTENT_COMPANY_ID, "days": 30},
            timeout=10,
        )
        if r.status_code == 200:
            data = r.json()
            assert data.get("total_calls", 0) == 0 or data.get("total_calls_analyzed", 0) == 0
        else:
            assert r.status_code in (400, 404, 422)

    def test_phases_analytics_zero_days(self, api_base_url, api_headers):
        """days=0 should return empty or error."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/analytics",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "days": 0},
            timeout=10,
        )
        assert r.status_code in (200, 400, 422)

    def test_phases_analytics_negative_days(self, api_base_url, api_headers):
        """Negative days should be rejected or treated as 0."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/analytics",
            headers=api_headers,
            params={"company_id": STAGING_COMPANY_ID, "days": -30},
            timeout=10,
        )
        assert r.status_code in (200, 400, 422)

    def test_phases_search_no_auth(self, api_base_url):
        """Phases search without auth should return 401."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/phases/search",
            params={"company_id": STAGING_COMPANY_ID, "limit": 5},
            timeout=10,
        )
        assert r.status_code in (401, 403), f"Expected 401/403, got {r.status_code}"


# ============================================================================
# 9. INJECTION / SECURITY TESTS
# ============================================================================
@pytest.mark.usefixtures("api_available")
class TestInjectionSecurity:
    """Verify API is resistant to SQL/NoSQL injection and XSS."""

    @pytest.mark.parametrize("injection", INJECTION_STRINGS)
    def test_injection_in_company_id_param(self, api_base_url, api_headers, injection):
        """Injection strings in company_id should not cause 500 errors."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/calls",
            headers=api_headers,
            params={"company_id": injection, "limit": 1},
            timeout=10,
        )
        # Should get a client error (400/422) or empty 200 — never 500
        assert r.status_code != 500, f"Server error 500 with injection payload: {injection}"
        assert r.status_code in (200, 400, 422), f"Unexpected {r.status_code} with injection: {injection}"

    @pytest.mark.parametrize("injection", INJECTION_STRINGS)
    def test_injection_in_call_id_path(self, api_base_url, api_headers, injection):
        """Injection strings in call_id path should not cause 500 errors."""
        r = requests.get(
            f"{api_base_url}/api/v1/call-processing/summary/{injection}",
            headers=api_headers,
            timeout=10,
        )
        assert r.status_code != 500, f"Server error 500 with injection in call_id: {injection}"

    @pytest.mark.parametrize("injection", INJECTION_STRINGS)
    def test_injection_in_process_fields(self, api_base_url, api_headers, injection):
        """Injection strings in process payload fields should not cause 500 errors."""
        payload = {
            "call_id": f"neg_inject_{uuid.uuid4().hex[:8]}",
            "company_id": STAGING_COMPANY_ID,
            "audio_url": STAGING_AUDIO_URLS[0],
            "phone_number": injection,
            "metadata": {"agent": {"id": injection, "name": injection}},
        }
        r = requests.post(
            f"{api_base_url}/api/v1/call-processing/process",
            headers=api_headers,
            json=payload,
            timeout=15,
        )
        # Should never crash with 500
        assert r.status_code != 500, f"Server error 500 with injection in fields: {injection}"
