# Otto (gomotto) Test Suite

Test suite for **CSR** stage of Otto, with E2E (Playwright), API (pytest), and ASR/STT tests.

## Required

| To run | Required |
|--------|----------|
| **E2E (Playwright)** | Node.js, npm → `npm install` and `npx playwright install`. A `.env` with `SIGN_IN_EMAIL` and `SIGN_IN_PASSWORD` (or use defaults in `tests/fixtures/auth.ts`). |
| **API / ASR tests** | Python 3, `pip install -r requirements-dev.txt`. A `.env` with **`OTTO_API_KEY`** (and optionally `OTTO_API_BASE_URL`). Without the key, API/ASR tests are **skipped**. |

Copy `.env.example` to `.env` and set `OTTO_API_KEY` for API tests. No other env vars are required for the tests to run (or skip gracefully).

## Staging & credentials

- **Staging URL:** https://stage.app.gomotto.com
- **Sign-in:** `/sign-in`
- **Credentials:** Set in `.env` (copy from `.env.example`):
  - `SIGN_IN_EMAIL`
  - `SIGN_IN_PASSWORD`

## Running tests

### E2E (Playwright)

```bash
npm install
npx playwright install
npm run test:e2e
```

- **With UI:** `npm run test:e2e:ui`
- **Headed browser:** `npm run test:e2e:headed`
- **Single file:** `npx playwright test tests/e2e/csr-login-and-pipeline.spec.ts`

### API tests (pytest)

Requires `OTTO_API_BASE_URL` and `OTTO_API_KEY` in `.env` for live API. If not set, API tests are skipped.

```bash
pip install -r requirements-dev.txt
npm run test:api
# or
pytest tests/api -v
```

### ASR/STT tests (pytest)

Same env as API. Includes transcription endpoint contract tests and optional WER checks.

```bash
pip install -r requirements-dev.txt
npm run test:asr
# or
pytest tests/asr_stt -v
```

## Staging test data (SOP + audio)

Real data used for integration and call-processing tests:

| Item | Value |
|------|--------|
| **Company ID** | `91ecfcb9-fc40-4792-ba47-65b273cec204` |
| **SOP ID** | `sop_4312acde8e78` |
| **SOP URL** | [Intake Calls PDF](https://otto-documents-staging.s3.ap-southeast-2.amazonaws.com/user-onboarding-docs/anthony@arizonaroofers.com_Intake_Calls_(3)_(1).pdf.pdf) |
| **Audio URLs** | 4 MP3 recordings in `tests/api/call_processing_data.py` → `STAGING_AUDIO_URLS` |

- **List calls/summaries** by `STAGING_COMPANY_ID` in `tests/api/test_staging_integration.py`.
- **Process one staging audio** (unique `call_id` per run) in `test_process_one_staging_audio`.

Data is defined in **`tests/api/call_processing_data.py`** (`STAGING_*`, `SOP_*`, `staging_process_payload()`).

To **install** this data into the Otto backend (upload SOP + submit 4 audio recordings for processing):

```bash
pip install -r requirements-dev.txt   # if not already
python3 scripts/install_staging_data.py
```

Requires `.env` with `OTTO_API_KEY`. The script uploads the Intake Calls SOP via URL and submits all four staging audio URLs; jobs run asynchronously on the server.

## Test cases summary

See **[TEST_CASES.md](../TEST_CASES.md)** for the full list of test cases (CSR focus, with placeholders for Sales Rep, Voice Agent, Ask Otto).
