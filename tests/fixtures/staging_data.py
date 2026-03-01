"""
Staging SOP + audio test data (single place for imports).
SOP: Intake Calls PDF | Company: Arizona Roofers (staging) | 4 audio recordings.
"""
from tests.api.call_processing_data import (
    STAGING_COMPANY_ID,
    STAGING_AUDIO_URLS,
    STAGING_AUDIO_URLS as AUDIO_URLS,  # alias
    SOP_URL,
    SOP_ID,
    staging_process_payload,
)

__all__ = [
    "STAGING_COMPANY_ID",
    "STAGING_AUDIO_URLS",
    "AUDIO_URLS",
    "SOP_URL",
    "SOP_ID",
    "staging_process_payload",
]
