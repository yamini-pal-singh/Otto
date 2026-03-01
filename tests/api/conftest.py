"""Pytest fixtures for Otto API tests."""
import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

OTTO_API_BASE_URL = os.getenv("OTTO_API_BASE_URL", "https://ottoai.shunyalabs.ai")
OTTO_API_KEY = os.getenv("OTTO_API_KEY", "")


@pytest.fixture(scope="session")
def api_base_url():
    return OTTO_API_BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api_headers():
    return {"X-API-Key": OTTO_API_KEY, "Content-Type": "application/json"}


@pytest.fixture(scope="session")
def api_available(api_base_url, api_headers):
    """Skip API tests if backend is not configured or unreachable."""
    if not OTTO_API_KEY:
        pytest.skip("OTTO_API_KEY not set - skipping API tests")
    try:
        r = requests.get(f"{api_base_url}/health", timeout=5)
        if r.status_code != 200:
            pytest.skip("Otto API health check failed")
    except requests.RequestException:
        pytest.skip("Otto API unreachable - skipping API tests")
