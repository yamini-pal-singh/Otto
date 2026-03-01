"""Fixtures for ASR/STT (transcription) tests."""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

OTTO_API_BASE_URL = os.getenv("OTTO_API_BASE_URL", "https://ottoai.shunyalabs.ai")
OTTO_API_KEY = os.getenv("OTTO_API_KEY", "")


@pytest.fixture(scope="session")
def asr_api_base_url():
    return OTTO_API_BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def asr_api_headers():
    return {"X-API-Key": OTTO_API_KEY, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def asr_api_available(asr_api_base_url, asr_api_headers):
    if not OTTO_API_KEY:
        pytest.skip("OTTO_API_KEY not set - skipping ASR/STT API tests")
    try:
        r = requests.get(f"{asr_api_base_url}/health", timeout=5)
        if r.status_code != 200:
            pytest.skip("Otto API health check failed")
    except requests.RequestException:
        pytest.skip("Otto API unreachable")
    return True
