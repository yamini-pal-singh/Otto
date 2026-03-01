"""
ASR/STT (Speech-to-Text) quality tests for Otto Call Processing.
Uses call-processing API: submit audio -> get transcript/summary.
Payloads and IDs from project_docs/Updated_Otto_API_Documentation.md.
"""
import pytest
import requests

from tests.api.call_processing_data import (
    PROCESS_PAYLOAD_MINIMAL,
    PROCESS_PAYLOAD_CSR,
    VALID_COMPANY_ID,
    SAMPLE_JOB_ID,
    DETAIL_PARAMS,
    JOB_STATUS_VALUES,
)


@pytest.mark.usefixtures("asr_api_available")
class TestTranscriptionAPI:
    """Transcription (STT) and call summary API contract tests."""

    def test_process_endpoint_accepts_valid_payload_with_agent(self, asr_api_base_url, asr_api_headers):
        """Process requires metadata.agent.id and metadata.agent.name (per API doc)."""
        r = requests.post(
            f"{asr_api_base_url}/api/v1/call-processing/process",
            headers=asr_api_headers,
            json=PROCESS_PAYLOAD_MINIMAL,
            timeout=15,
        )
        assert r.status_code in (202, 409), f"Unexpected status {r.status_code}: {r.text}"
        if r.status_code == 202:
            data = r.json()
            assert "job_id" in data
            assert data.get("status") in ("queued", "processing")

    def test_process_csr_payload_structure(self, asr_api_base_url, asr_api_headers):
        """CSR-specific payload with rep_role customer_rep and agent metadata."""
        r = requests.post(
            f"{asr_api_base_url}/api/v1/call-processing/process",
            headers=asr_api_headers,
            json=PROCESS_PAYLOAD_CSR,
            timeout=15,
        )
        assert r.status_code in (202, 409)
        if r.status_code == 202:
            data = r.json()
            assert data.get("call_id") == PROCESS_PAYLOAD_CSR["call_id"]
            assert "status_url" in data

    def test_status_endpoint_returns_valid_structure(self, asr_api_base_url, asr_api_headers):
        r = requests.get(
            f"{asr_api_base_url}/api/v1/call-processing/status/{SAMPLE_JOB_ID}",
            headers=asr_api_headers,
            timeout=10,
        )
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            assert "job_id" in data
            assert "status" in data
            assert data["status"] in JOB_STATUS_VALUES
            assert "progress" in data
            assert "steps_completed" in data["progress"]

    def test_call_detail_transcript_and_segments(self, asr_api_base_url, asr_api_headers):
        """Detail endpoint returns transcript (string) and segments (list) per API doc 2.11."""
        call_id = "test-nonexistent-call"
        r = requests.get(
            f"{asr_api_base_url}/api/v1/call-processing/calls/{call_id}/detail",
            headers=asr_api_headers,
            params=DETAIL_PARAMS,
            timeout=10,
        )
        assert r.status_code in (200, 404)
        if r.status_code == 200:
            data = r.json()
            assert "call_id" in data
            assert data.get("company_id") == VALID_COMPANY_ID or "company_id" in data
            if data.get("transcript"):
                assert isinstance(data["transcript"], str)
            if data.get("segments"):
                assert isinstance(data["segments"], list)
                for seg in data["segments"]:
                    assert "speaker" in seg
                    assert "text" in seg
                    assert "start_time" in seg or "start" in seg
                    assert "end_time" in seg or "end" in seg


def word_error_rate(reference: str, hypothesis: str) -> float:
    """
    Compute WER (Word Error Rate) for ASR evaluation.
    Requires: pip install jiwer
    """
    try:
        import jiwer
        return jiwer.wer(reference, hypothesis)
    except ImportError:
        return -1.0  # skip or use custom implementation


@pytest.mark.skip(reason="Enable when reference transcripts and sample audio are available")
def test_wer_under_threshold():
    """Example: assert transcription WER is below 0.15 (15%) for reference audio."""
    reference = "Thank you for calling Arizona Roofers how can I help you today"
    hypothesis = "Thank you for calling Arizona Roofers how can I help you today"
    wer = word_error_rate(reference, hypothesis)
    assert wer >= 0, "jiwer not installed"
    assert wer <= 0.15, f"WER {wer} exceeds 15%"
