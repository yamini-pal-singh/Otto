# Otto (gomotto) – Test Cases

Staging: **https://stage.app.gomotto.com/sign-in**
Focus: **CSR** stage first; Sales Rep, Voice Agent, and Ask Otto stages are scoped for later.

---

## 1. CSR Stage (Current Focus)

### 1.1 Call processing API (backend for CSR)

| ID | Description | Type | Steps | Expected |
|----|-------------|------|--------|----------|
| TC-CSR-011 | Health check | API | GET `/health` | 200, `status: healthy` |
| TC-CSR-012 | API status requires auth | API | GET `/api/v1/status` without key | 401 |
| TC-CSR-013 | API status with key | API | GET `/api/v1/status` with `X-API-Key` | 200, `call_processing: active` |
| TC-CSR-014 | List calls requires company_id | API | GET `/api/v1/call-processing/calls` without company_id | 400/422 |
| TC-CSR-015 | List calls with company_id | API | GET with valid UUID company_id, limit=5 | 200, `calls` array, `total` |
| TC-CSR-016 | List summaries with filters | API | GET summaries with company_id, sort | 200, `summaries` array |

### 1.2 ASR / STT (transcription)

| ID | Description | Type | Steps | Expected |
|----|-------------|------|--------|----------|
| TC-CSR-017 | Process endpoint accepts valid payload | API | POST process with call_id, company_id, audio_url, etc. | 202 Accepted (or 400 if validation fails) |
| TC-CSR-018 | Status endpoint returns valid structure | API | GET status/{job_id} | 200 with job_id, status (or 404) |
| TC-CSR-019 | Call detail with transcript | API | GET calls/{call_id}/detail?include_transcript=true | 200 with call_id; transcript string if present |
| TC-CSR-020 | WER under threshold (optional) | API/ASR | Submit sample audio; compare transcript to reference | WER ≤ 15% (enable when reference transcripts available) |

---

## 2. Sales Rep Stage (Planned)

| ID | Description | Type | Notes |
|----|-------------|------|--------|
| TC-SR-003 | Lead scoring / BANT visibility | API | Insights API, lead endpoints |

---

## 3. Voice Agent Stage (Planned)

| ID | Description | Type | Notes |
|----|-------------|------|--------|
| TC-VA-002 | Real-time STT/ASR round-trip | API | Audio in → transcript/summary out |
| TC-VA-003 | Latency and accuracy metrics | API/ASR | Use call-processing pipeline |

---

## 4. Ask Otto Stage (Planned)

| ID | Description | Type | Notes |
|----|-------------|------|--------|
| TC-AO-002 | Create conversation | API | POST conversations |
| TC-AO-003 | Send message and get response | API | Message round-trip |
| TC-AO-004 | Intent routing / RAG responses | API | Per ARCHITECTURE_FEATURE_3 |

---

## Frameworks & tools

| Area | Framework / tool | Purpose |
|------|-------------------|--------|
| API | **pytest** + **requests** | Call processing, insights, list calls/summaries |
| ASR/STT | **pytest** + **jiwer** (optional) | Transcription contract tests; WER when reference transcripts exist |

---

## Running tests

- **API:** `pip install -r requirements-dev.txt && pytest tests/api -v`
- **ASR/STT:** `pytest tests/asr_stt -v`

See **tests/README.md** for env vars (`.env` from `.env.example`) and more options.
