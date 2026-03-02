"""
Call Processing API test data from Updated_Otto_API_Documentation.md.
Base URL: https://ottoai.shunyalabs.ai
"""

# Base URL (override via OTTO_API_BASE_URL env)
DEFAULT_BASE_URL = "https://ottoai.shunyalabs.ai"

# ---------------------------------------------------------------------------
# Staging company (real data) — used across all tests
# ---------------------------------------------------------------------------
STAGING_COMPANY_ID = "1be5ea90-d3ae-4b03-8b05-f5679cd73bc4"

# Alias kept for backward compatibility in imports
VALID_COMPANY_ID = STAGING_COMPANY_ID

# Real audio recordings (MP3) for call processing tests
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

# Example call_id for new submissions (flexible: UUID or any string)
SAMPLE_CALL_ID = "550e8400-e29b-41d4-a716-446655440000"

# Real call_id from staging (completed, has summary/detail/transcript)
REAL_CALL_ID = "d4ced470-3ec4-4e8b-a705-a1600611b36b"

# Job ID format (UUID) - system generated; use for status/retry
SAMPLE_JOB_ID = "550e8400-e29b-41d4-a716-446655440000"

# Required for POST /api/v1/call-processing/process
# metadata.agent.id and metadata.agent.name are REQUIRED (or legacy rep_id/rep_name)
PROCESS_PAYLOAD_MINIMAL = {
    "call_id": SAMPLE_CALL_ID,
    "company_id": STAGING_COMPANY_ID,
    "audio_url": STAGING_AUDIO_URLS[0],
    "phone_number": "+14805551234",
    "rep_role": "customer_rep",
    "metadata": {
        "agent": {
            "id": "USR_ANTHONY_ARIZONA",
            "name": "Anthony",
            "email": "anthony@arizonaroofers.com",
        }
    },
}

PROCESS_PAYLOAD_CSR = {
    "call_id": "550e8400-e29b-41d4-a716-446655440001",
    "company_id": STAGING_COMPANY_ID,
    "audio_url": STAGING_AUDIO_URLS[1],
    "phone_number": "+14805551234",
    "rep_role": "customer_rep",
    "metadata": {
        "agent": {
            "id": "USR_ANTHONY_ARIZONA",
            "name": "Anthony",
            "email": "anthony@arizonaroofers.com",
        }
    },
}

# Invalid payloads for validation tests
INVALID_COMPANY_ID_NOT_UUID = "acme_roofing"
PROCESS_PAYLOAD_MISSING_AGENT = {
    "call_id": SAMPLE_CALL_ID,
    "company_id": STAGING_COMPANY_ID,
    "audio_url": STAGING_AUDIO_URLS[0],
    "phone_number": "+14805551234",
    "metadata": {},
}

# Status response: allowed status values
JOB_STATUS_VALUES = ("queued", "processing", "completed", "failed")

# List calls query params (from doc 2.10)
LIST_CALLS_PARAMS = {
    "company_id": STAGING_COMPANY_ID,
    "limit": 50,
    "offset": 0,
    "sort_by": "call_date",  # call_date | created_at | duration
    "sort_order": "desc",    # asc | desc
}

# List summaries query params (from doc 2.9)
LIST_SUMMARIES_PARAMS = {
    "company_id": STAGING_COMPANY_ID,
    "limit": 20,
    "offset": 0,
    "sort_by": "created_at",      # created_at | compliance_score
    "sort_order": "desc",         # asc | desc
    "min_compliance_score": 0.0,
    "max_compliance_score": 1.0,
}

# Get summary query params
SUMMARY_INCLUDE_CHUNKS = {"include_chunks": "true"}

# Get call detail query params (from doc 2.11)
DETAIL_PARAMS = {
    "include_transcript": "true",
    "include_segments": "true",
}

# Phase search (2.7)
PHASES_SEARCH_PARAMS = {
    "company_id": STAGING_COMPANY_ID,
    "missing_phase": "closing",
    "limit": 50,
    "offset": 0,
}

# Phase analytics (2.8)
PHASES_ANALYTICS_PARAMS = {
    "company_id": STAGING_COMPANY_ID,
    "days": 30,
}

# ---------------------------------------------------------------------------
# Negative / edge-case test data
# ---------------------------------------------------------------------------
NONEXISTENT_CALL_ID = "00000000-0000-0000-0000-000000000000"
NONEXISTENT_JOB_ID = "00000000-0000-0000-0000-000000000000"
NONEXISTENT_COMPANY_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
WRONG_API_KEY = "INVALID_KEY_12345678"
INVALID_AUDIO_URL = "https://example.com/nonexistent_audio.mp3"

# Empty body for process endpoint
PROCESS_PAYLOAD_EMPTY = {}

# Missing call_id
PROCESS_PAYLOAD_NO_CALL_ID = {
    "company_id": STAGING_COMPANY_ID,
    "audio_url": STAGING_AUDIO_URLS[0],
    "phone_number": "+14805551234",
    "metadata": {"agent": {"id": "USR_TEST", "name": "Test"}},
}

# Missing audio_url
PROCESS_PAYLOAD_NO_AUDIO = {
    "call_id": "neg_test_no_audio_001",
    "company_id": STAGING_COMPANY_ID,
    "phone_number": "+14805551234",
    "metadata": {"agent": {"id": "USR_TEST", "name": "Test"}},
}

# Invalid audio URL (unreachable)
PROCESS_PAYLOAD_BAD_AUDIO = {
    "call_id": "neg_test_bad_audio_001",
    "company_id": STAGING_COMPANY_ID,
    "audio_url": INVALID_AUDIO_URL,
    "phone_number": "+14805551234",
    "metadata": {"agent": {"id": "USR_TEST", "name": "Test"}},
}

# SQL/NoSQL injection payloads
INJECTION_STRINGS = [
    "'; DROP TABLE calls; --",
    '{"$gt": ""}',
    "<script>alert('xss')</script>",
    "{{7*7}}",
    "../../../etc/passwd",
]

# ---------------------------------------------------------------------------
# SOP document (Intake Calls - user onboarding)
# ---------------------------------------------------------------------------
SOP_URL = "https://otto-documents-staging.s3.ap-southeast-2.amazonaws.com/user-onboarding-docs/anthony@arizonaroofers.com_Intake_Calls_(3)_(1).pdf.pdf"
SOP_ID = "sop_4312acde8e78"


def staging_process_payload(call_id: str, audio_url: str, phone_number: str = "+14805551234") -> dict:
    """Build process payload for staging company + given audio. Use unique call_id per run."""
    return {
        "call_id": call_id,
        "company_id": STAGING_COMPANY_ID,
        "audio_url": audio_url,
        "phone_number": phone_number,
        "rep_role": "customer_rep",
        "metadata": {
            "agent": {
                "id": "USR_ANTHONY_ARIZONA",
                "name": "Anthony",
                "email": "anthony@arizonaroofers.com",
            }
        },
    }
