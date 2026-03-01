# Otto Intelligence — Test Gaps & Untestable Features

> **Purpose:** Documents features described in the architecture docs that cannot currently be tested through the staging API.
> **Last Updated:** March 2026
> **Staging API:** `https://ottoai.shunyalabs.ai`

---

## 1. Property Details Extraction (NOT IN API RESPONSE)

**Architecture Reference:** `ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` — Qualification Extractor, Call 4

The architecture doc describes a 4th LLM call in the Qualification Extractor that extracts home-services-specific property details. These fields are **not present** in any of the 23 staging call summaries.

| Field | Described In Architecture | Present in API? | Tested? |
|-------|--------------------------|-----------------|---------|
| `roof_type` | Yes — roof type and material | **No** | xfail |
| `roof_age` | Yes — age/condition of roof | **No** | xfail |
| `hoa_status` | Yes — HOA membership | **No** | xfail |
| `pets_on_property` | Yes — pets present (safety) | **No** | xfail |
| `solar_panels` | Yes — solar installation | **No** | xfail |
| `access_notes` | Yes — property access info | **No** | xfail |

**Test Status:** 6 tests written in `test_customer_intelligence.py` and marked `@pytest.mark.xfail`. They will:
- Pass silently (as `xfail`) while the API doesn't return these fields
- Automatically start passing (as `xpass`) when the backend adds them — alerting us to update assertions

**Possible Explanations:**
1. Extractor Call 4 is not yet deployed to staging
2. Fields are extracted but stored separately (not exposed via `/summary` endpoint)
3. Calls in staging don't discuss property details (fields omitted when null)
4. Feature is behind a tenant configuration flag not enabled for Arizona Roofers

**Action Required:** Confirm with the backend team whether:
- These fields should appear in the `/summary` response
- A separate API endpoint exposes property details
- A tenant config flag needs to be enabled

---

## 2. Enhanced Validation (INTERNAL PIPELINE — NOT EXTERNALLY TESTABLE)

**Architecture Reference:** `ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` — Post-Processing

The pipeline includes several validation steps that happen internally during processing. We can only verify their side-effects, not the validation logic itself.

### 2.1 Customer Name Validation (Partially Testable)

| Aspect | Testable? | How |
|--------|-----------|-----|
| `customer_name_confidence` returned | **Yes** | Tested — values 0.6-1.0 across calls |
| Prevents rep/customer name confusion | **No** | Internal LLM logic, no error flag in response |
| Name confidence < threshold triggers re-extraction | **No** | Internal retry logic |

**What we can verify:** The `customer_name_confidence` field exists and falls in 0.0-1.0 range. We observe realistic confidence values (e.g., 0.6 for names hard to parse from audio, 1.0 for clearly stated names).

### 2.2 Follow-up Reason Validation (Partially Testable)

| Aspect | Testable? | How |
|--------|-----------|-----|
| `follow_up_reason` populated when `follow_up_required=true` | **Yes** | Tested |
| Anti-hallucination check on reason text | **No** | Internal LLM self-check |
| Reason anchored to transcript evidence | **No** | Would need transcript + reason cross-reference |

### 2.3 Action Item Validation (Partially Testable)

| Aspect | Testable? | How |
|--------|-----------|-----|
| `action_items` list returned in summary | **Yes** | Tested (list presence) |
| Hallucinated actions removed | **No** | Internal validation logic |
| Actions cross-referenced with transcript | **No** | Would need semantic matching |

### 2.4 JSON Schema Validation with Retry Logic (Not Testable)

| Aspect | Testable? | How |
|--------|-----------|-----|
| Response follows JSON schema | **Partially** | We validate field types/ranges |
| Retry on malformed LLM output | **No** | Internal pipeline retry logic |
| Schema version tracking | **No** | Not exposed in API |

---

## 3. Conditional Prompt Enrichment (INTERNAL PIPELINE)

**Architecture Reference:** `ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` — Step 5.5

| Feature | Testable? | Notes |
|---------|-----------|-------|
| Tenant configuration injection | **No** | Internal; we see effects in qualification thresholds |
| Objection baseline calibration from weekly_insights | **No** | Internal severity calibration |
| SOP rubric injection for compliance | **Indirectly** | We test SOP compliance scores, but can't verify rubric injection |
| Milvus RAG for response suggestions | **Indirectly** | We see `response_suggestions` in objections data |

---

## 4. Hybrid Diarization (INTERNAL PIPELINE)

**Architecture Reference:** `ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` — Step 3

| Feature | Testable? | Notes |
|---------|-----------|-------|
| LLM vs API diarization mode selection | **No** | Internal strategy decision |
| Speaker label accuracy | **Indirectly** | We verify segments have `speaker` field with valid values |
| Timestamp alignment | **No** | Would need original audio + timestamps to verify |
| Diarization fallback when primary fails | **No** | Internal failover logic |

**What we can verify:** Every segment has a `speaker` field and `text` field. Speaker labels are consistent (`customer_rep`, `home_owner`).

---

## 5. RAG Indexing (PARTIALLY TESTABLE)

**Architecture Reference:** `ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` — Step 8

| Feature | Testable? | Notes |
|---------|-----------|-------|
| Embeddings generated for call summaries | **No** | Internal to Milvus |
| Milvus collection populated | **No** | No direct Milvus API access |
| Embedding cache in Redis | **No** | No Redis access |
| Search results quality | **Indirectly** | Only via Ask Otto (Feature 3) |

---

## 6. Weekly Insights Engine (FEATURE 2 — LIMITED TESTING)

**Architecture Reference:** `ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md`

| Feature | Testable? | Notes |
|---------|-----------|-------|
| Scheduled generation (Sunday 00:00 UTC) | **No** | APScheduler internal |
| Manual trigger endpoint | **Potentially** | `POST /api/v1/insights/generate` — not tested to avoid side effects |
| Insights used for objection baselines | **No** | Internal enrichment |
| Coach effectiveness scoring | **No** | No coaching session data in staging |

---

## 7. Summary of Test Coverage

```
 FEATURE                              COVERAGE    STATUS
 ──────────────────────────────────────────────────────────
 Call Processing Pipeline              ████████░░  ~80%   Positive + Negative tests
 Customer Intelligence (Qualification) ████████░░  ~80%   18 tests, address/appt added
 SOP Compliance & Coaching             ████████░░  ~80%   Score, stages, coaching items
 Objection Detection                   ███████░░░  ~70%   Categories, severity, overcome
 Property Details (Call 4)             ░░░░░░░░░░   0%    NOT IN API — 6 xfail tests
 Enhanced Validation                   ███░░░░░░░  ~30%   Confidence scores only
 Diarization / Transcription           ██████░░░░  ~60%   Segments + ASR/WER tests
 Phase Detection                       ████████░░  ~80%   Search + analytics endpoints
 RAG / Vector Search                   ░░░░░░░░░░   0%    No direct access
 Weekly Insights                       ░░░░░░░░░░   0%    No safe test trigger
 Authentication & Security             ██████████  100%   6 auth + 15 injection tests
 Negative / Edge Cases                 ██████████  100%   45 tests across all endpoints
```

---

## 8. Recommendations

### Immediate (Can Do Now)
1. **Ask backend team** about property details fields — are they deployed? Behind a flag?
2. **Add transcript cross-referencing tests** — verify that `follow_up_reason` quotes appear in transcript text
3. **Test Ask Otto endpoints** if available — would validate RAG indexing indirectly

### Requires Backend Changes
4. **Expose validation metadata** — add `validation_retries`, `schema_version` to response
5. **Add property details to `/summary`** — or create a separate `/property-details/{call_id}` endpoint
6. **Expose diarization method** — add `diarization_mode` (llm/api) to call detail response

### Requires Infrastructure Access
7. **MongoDB direct queries** — verify document structure matches API output
8. **Redis cache inspection** — verify TTLs and cache hit rates
9. **Milvus collection stats** — verify embedding count matches call count
