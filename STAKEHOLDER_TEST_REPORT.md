# Otto Intelligence — Call Processing Pipeline & Test Coverage Report

> **Version:** 5.1 | **Date:** March 2026 | **Company:** Arizona Roofers (Staging)
> **API:** https://ottoai.shunyalabs.ai | **UI:** https://stage.app.gomotto.com

---

## 1. What Does Otto Call Processing Do?

Otto takes a **raw phone call recording** and transforms it into **structured business intelligence** — automatically.

```
  ┌──────────┐     ┌──────────────────────────────────────────────────┐     ┌──────────────┐
  │          │     │          OTTO INTELLIGENCE ENGINE                │     │              │
  │  Phone   │     │                                                  │     │  Actionable  │
  │  Call    ───────▶  Audio ─▶ Transcript ─▶ Analysis ─▶ Insights  ───────▶  Business    │
  │  (MP3)   │     │                                                  │     │  Data        │
  │          │     │          ⏱ < 120 seconds end-to-end              │     │              │
  └──────────┘     └──────────────────────────────────────────────────┘     └──────────────┘
```

### What You Get From Each Call:

| Output               | What It Tells You                                        |
|----------------------|----------------------------------------------------------|
| **Transcript**       | Full text of the conversation with speaker labels        |
| **Summary**          | Key topics, customer sentiment, action items             |
| **Compliance Score** | How well the agent followed the company SOP (0-100%)     |
| **Lead Score (BANT)**| Budget, Authority, Need, Timeline — lead quality (0-100) |
| **Objections**       | What the customer pushed back on and if it was resolved  |
| **Conversation Phases** | Opening → Discovery → Pitch → Objection → Close      |
| **Coaching Hints**   | AI-generated tips for agent improvement                  |

---

## 2. End-to-End Pipeline Flow

```
                          OTTO CALL PROCESSING PIPELINE
  ═══════════════════════════════════════════════════════════════════

  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 1: SUBMIT                                                │
  │  CSR uploads call or system auto-sends audio URL               │
  │  POST /api/v1/call-processing/process                          │
  │                                                                 │
  │  Inputs:  audio_url, company_id, agent info, phone number      │
  │  Returns: job_id + status_url (for tracking)                   │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 2: TRANSCRIPTION (ASR/STT)                               │
  │  Audio ──▶ Text with Speaker Labels                            │
  │                                                                 │
  │  ┌─────────┐    ┌──────────────────────────────────────┐       │
  │  │  MP3    │───▶│  "Hi, this is Anthony from Arizona   │       │
  │  │  Audio  │    │   Roofers. How can I help you today?" │       │
  │  │  File   │    │  [Speaker: Agent | 0:00 - 0:05]      │       │
  │  └─────────┘    └──────────────────────────────────────┘       │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 3: SMART CHUNKING                                        │
  │  Break transcript into meaningful conversation segments         │
  │                                                                 │
  │  Chunk 1: Greeting + Intro       [0:00 - 0:45]                │
  │  Chunk 2: Problem Discovery      [0:45 - 3:20]                │
  │  Chunk 3: Solution Pitch         [3:20 - 5:10]                │
  │  Chunk 4: Objection Handling     [5:10 - 6:45]                │
  │  Chunk 5: Closing                [6:45 - 7:30]                │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 4: PARALLEL AI ANALYSIS (on each chunk simultaneously)   │
  │                                                                 │
  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────┐│
  │  │  📝 Summary  │  │  ✅ SOP      │  │  ⚠️ Object-│  │ 🎯   ││
  │  │  Extractor   │  │  Compliance  │  │  ion Detect │  │ BANT ││
  │  │              │  │  Checker     │  │  (7-stage)  │  │ Lead ││
  │  │  Key points  │  │  Score each  │  │  Find push- │  │Score ││
  │  │  & actions   │  │  SOP metric  │  │  backs &    │  │      ││
  │  │              │  │  (0-100%)    │  │  if resolved │  │ B/A/ ││
  │  │              │  │              │  │             │  │ N/T  ││
  │  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  └──┬───┘│
  │         │                 │                  │            │    │
  │         └────────────┬────┴──────────────────┴────────────┘    │
  │                      │                                         │
  └──────────────────────┼─────────────────────────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 5: AGGREGATE & STORE                                     │
  │                                                                 │
  │  Chunk results ──▶ Call-level scores ──▶ MongoDB + Redis       │
  │                                                                 │
  │  Final Output:                                                  │
  │  ┌───────────────────────────────────────────────────────────┐ │
  │  │ Summary:     "Customer called about roof leak repair..."  │ │
  │  │ Compliance:  87% (SOP adherence)                          │ │
  │  │ Lead Score:  72/100 (BANT: B=80 A=60 N=85 T=65)         │ │
  │  │ Objections:  1 found (pricing) — resolved ✓              │ │
  │  │ Phases:      Greeting ✓  Discovery ✓  Close ✓           │ │
  │  │ Coaching:    "Spend more time on qualification phase"     │ │
  │  └───────────────────────────────────────────────────────────┘ │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │  STEP 6: AVAILABLE VIA API & CSR DASHBOARD                     │
  │                                                                 │
  │  API Endpoints:                CSR Dashboard (gomotto.com):    │
  │  GET /summary/{call_id}       Pipeline Kanban Board            │
  │  GET /calls/{call_id}/detail  Lead Insights                    │
  │  GET /phases/analytics        Call Log                         │
  │  GET /calls?company_id=...    Sale Insights                    │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack (What Powers It)

```
  ┌─────────────────────────────────────────────────────────┐
  │                   OTTO INTELLIGENCE                     │
  ├─────────────────────────────────────────────────────────┤
  │                                                         │
  │   ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
  │   │ FastAPI  │  │  GROQ    │  │  ASR / STT        │   │
  │   │ REST API │  │  LLM     │  │  (Audio→Text)     │   │
  │   │ + Jobs   │  │  llama   │  │  AssemblyAI       │   │
  │   └──────────┘  │  3.3-70b │  └───────────────────┘   │
  │                  └──────────┘                           │
  │   ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
  │   │ MongoDB  │  │  Redis   │  │  Milvus (Zilliz)  │   │
  │   │ Primary  │  │  Cache   │  │  Vector Search     │   │
  │   │ Storage  │  │  + Jobs  │  │  (RAG/Embeddings)  │   │
  │   └──────────┘  └──────────┘  └───────────────────┘   │
  │                                                         │
  │   Embeddings: HuggingFace all-MiniLM-L6-v2 (local)    │
  └─────────────────────────────────────────────────────────┘
```

---

## 4. What We Test & How (Test Coverage Map)

### 4a. API Tests — 19 Tests (All Real Staging Data)

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                        API TEST COVERAGE                               │
  │                Company: Arizona Roofers (Staging)                       │
  │                20 real calls │ 19 summaries │ 4 audio files            │
  ├─────────────────────────────────────────────────────────────────────────┤
  │                                                                         │
  │  ── INFRASTRUCTURE (2 tests) ──────────────────────────────────────    │
  │  ✅ Health check (service=healthy, MongoDB/Redis/Milvus connected)     │
  │  ✅ API status with key (version=v1, features listed)                  │
  │                                                                         │
  │  ── AUTHENTICATION (2 tests) ──────────────────────────────────────    │
  │  ✅ Requests without API key → 401 Unauthorized                        │
  │  ✅ Requests without company_id → 400/422 rejected                     │
  │                                                                         │
  │  ── CALL LISTING (3 tests) ────────────────────────────────────────    │
  │  ✅ List calls with staging company → 20 calls returned                │
  │  ✅ List calls with invalid company_id → 0 results (graceful)          │
  │  ✅ List summaries with filters → 19 summaries returned                │
  │                                                                         │
  │  ── CALL PROCESSING / SUBMISSION (3 tests) ────────────────────────    │
  │  ✅ Submit real audio (S3 URL) → 202 Accepted, job_id returned         │
  │  ✅ Submit with invalid company_id → 422 rejected (Pydantic)           │
  │  ✅ Submit without agent metadata → 202 (accepted gracefully)          │
  │                                                                         │
  │  ── RESPONSE STRUCTURE VALIDATION (3 tests, REAL DATA) ───────────    │
  │  ✅ Summary: call_id, company_id, summary, compliance,                 │
  │     qualification, objections — all present for real call               │
  │  ✅ Detail: transcript (non-empty), 39 segments with speaker+text      │
  │  ✅ Status endpoint: job_id, status, progress structure                 │
  │                                                                         │
  │  ── CONVERSATION PHASES (3 tests) ─────────────────────────────────    │
  │  ✅ Phase search requires company_id → 400/422                         │
  │  ✅ Phase search returns matching calls (19 calls analyzed)             │
  │  ✅ Phase analytics: detection_rates, commonly_missing phases           │
  │                                                                         │
  │  ── STAGING INTEGRATION (3 tests, REAL AUDIO) ────────────────────    │
  │  ✅ List calls for staging company → real data verified                 │
  │  ✅ List summaries for staging company → real data verified             │
  │  ✅ Process real audio (Arizona Roofers MP3) → queued successfully      │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

### 4b. ASR / Transcription Tests — 5 Tests

```
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                      ASR / STT TEST COVERAGE                           │
  ├─────────────────────────────────────────────────────────────────────────┤
  │                                                                         │
  │  ✅ Process endpoint accepts valid audio payload                        │
  │  ✅ CSR payload structure validated                                     │
  │  ✅ Status endpoint returns valid job structure                         │
  │  ✅ Call detail returns transcript + segments                           │
  │  ⏭️  WER (Word Error Rate) test — skipped (needs reference transcripts) │
  │                                                                         │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Test Results Summary (Latest Run)

```
  ╔═══════════════════════════════════════════════════════════════╗
  ║                    OVERALL: 24 TESTS                         ║
  ║                                                               ║
  ║   ┌─────────────┬──────────┬────────┬─────────┬───────────┐  ║
  ║   │ Suite       │ Total    │ Passed │ Skipped │ Failed    │  ║
  ║   ├─────────────┼──────────┼────────┼─────────┼───────────┤  ║
  ║   │ API         │   19     │  ✅ 19 │    0    │    0      │  ║
  ║   │ ASR/STT     │    5     │  ✅  4 │  ⏭️  1  │    0      │  ║
  ║   ├─────────────┼──────────┼────────┼─────────┼───────────┤  ║
  ║   │ TOTAL       │   24     │  ✅ 23 │  ⏭️  1  │  ❌  0    │  ║
  ║   └─────────────┴──────────┴────────┴─────────┴───────────┘  ║
  ║                                                               ║
  ║   Real staging data: ✅  |  Fake/sample data: ❌ None        ║
  ║   All tests use Arizona Roofers staging environment           ║
  ╚═══════════════════════════════════════════════════════════════╝
```

---

## 6. Real Staging Data Used In Tests

| Data Point         | Value                                              |
|--------------------|----------------------------------------------------|
| **Company**        | Arizona Roofers                                    |
| **Company ID**     | `1be5ea90-d3ae-4b03-8b05-f5679cd73bc4`             |
| **Agent**          | Anthony (anthony@arizonaroofers.com)               |
| **Calls in System**| 20 processed calls                                 |
| **Summaries**      | 19 completed summaries                             |
| **Audio Files**    | 4 real MP3 recordings (S3)                         |
| **Real Call ID**   | `d4ced470-3ec4-4e8b-a705-a1600611b36b` (completed) |
| **Transcript**     | Full text with 39 speaker segments                 |
| **SOP Document**   | Intake Calls SOP (PDF)                             |

### Phase Detection Stats (Live from Analytics API):

```
  Phase              Detection Rate    Status
  ─────────────────────────────────────────────
  Greeting           100.0%            ██████████ Excellent
  Problem Discovery  100.0%            ██████████ Excellent
  Post-Close         100.0%            ██████████ Excellent
  Qualification       94.7%            █████████░ Good
  Closing             94.7%            █████████░ Good
  Objection Handling   78.9%           ███████░░░ Needs Improvement

  Commonly Missing: objection_handling, qualification, closing
```

---

## 7. What's Not Yet Tested (Gaps)

| Gap                            | Why                                         | Impact   |
|--------------------------------|---------------------------------------------|----------|
| WER (Word Error Rate)          | Needs reference transcripts for comparison  | Low      |
| SOP Upload/Ingestion API       | Not in current test scope                   | Medium   |
| Ask Otto (Chat AI)             | Feature 3 — separate test suite needed      | Medium   |
| Weekly Insights Engine         | Feature 2 — needs APScheduler trigger       | Low      |
| Webhook Callbacks              | Not configured in staging                   | Low      |
| Multi-call Summary (3-call)    | Needs 3+ calls from same customer           | Low      |
| Lead Insights / Call Log pages | No UI test coverage currently               | Medium   |

---

## 8. How To Run Tests

```bash
# All API tests (real staging data)
python3 -m pytest tests/api -v

# ASR/Transcription tests
python3 -m pytest tests/asr_stt -v
```

---

*Generated from live API verification against Otto Intelligence staging environment.*
