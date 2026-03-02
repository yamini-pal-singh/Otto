# Otto Intelligence — Architecture & Data Flow Guide

> **Audience:** Stakeholders, QA, Developers
> **Last Updated:** March 2026
> **Staging Company:** Arizona Roofers (`1be5ea90-d3ae-4b03-8b05-f5679cd73bc4`)

---

## 1. System Overview

Otto Intelligence converts raw phone call recordings into structured business intelligence — summaries, compliance scores, objection detection, lead qualification, and AI coaching recommendations.

```
                         OTTO INTELLIGENCE PLATFORM
 ┌─────────────────────────────────────────────────────────────────┐
 │                                                                 │
 │   Phone Call Audio (S3)                                         │
 │        │                                                        │
 │        ▼                                                        │
 │   ┌─────────────────────────────────────────────────────┐       │
 │   │           FastAPI REST API (Port 8000)              │       │
 │   │         + APScheduler (in-process jobs)             │       │
 │   └──────────────────────┬──────────────────────────────┘       │
 │                          │                                      │
 │        ┌─────────────────┼─────────────────┐                    │
 │        ▼                 ▼                 ▼                    │
 │   ┌─────────┐     ┌──────────┐     ┌──────────────┐            │
 │   │ MongoDB │     │  Redis   │     │Milvus Zilliz │            │
 │   │(Primary)│     │ (Cache)  │     │  (Vectors)   │            │
 │   └─────────┘     └──────────┘     └──────────────┘            │
 │        │                                                        │
 │        ▼                                                        │
 │   ┌─────────────────────────────────────────────────────┐       │
 │   │  GROQ LLM (llama-3.3-70b)  │  HuggingFace Embed.  │       │
 │   └─────────────────────────────────────────────────────┘       │
 │                                                                 │
 └─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Component          | Technology                          | Purpose                                |
|--------------------|-------------------------------------|----------------------------------------|
| **API Server**     | FastAPI (Python)                    | REST API, async request handling       |
| **Primary DB**     | MongoDB                             | Call records, summaries, SOP docs      |
| **Cache**          | Redis                               | Job status, tenant config, sessions    |
| **Vector DB**      | Milvus Zilliz Cloud                 | Semantic search, RAG retrieval         |
| **Analytics DB**   | PostgreSQL (optional)               | Structured analytics for Ask Otto      |
| **LLM**           | GROQ (llama-3.3-70b-versatile)     | Extraction, summarization, diarization |
| **Embeddings**     | HuggingFace (all-MiniLM-L6-v2)    | 384-dim vectors, local (free)          |
| **Audio Storage**  | AWS S3 (ap-southeast-2 / Sydney)   | Call recordings (MP3)                  |
| **Task Scheduler** | APScheduler (in-process)            | Weekly insights generation             |

---

## 3. Call Processing Pipeline (Step by Step)

When a call is submitted via `POST /api/v1/call-processing/process`, the following pipeline executes:

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │                     CALL PROCESSING PIPELINE                        │
 │                                                                      │
 │  Step 1 ─── Initialize (5%)                                         │
 │  │           Load tenant config from MongoDB                        │
 │  │           Validate company settings + qualification rules        │
 │  │                                                                   │
 │  Step 2 ─── Download Audio (10%)                                    │
 │  │           Fetch MP3 from S3 / HTTP / local                       │
 │  │           Temporary storage for processing                       │
 │  │                                                                   │
 │  Step 3 ─── Transcribe + Diarize (20%)                              │
 │  │           Provider: Shunya API (primary) / AssemblyAI (fallback) │
 │  │           LLM-based speaker labeling:                            │
 │  │             SPEAKER_00/01 → customer_rep / home_owner            │
 │  │           Output: labeled segments + timestamped segments        │
 │  │                                                                   │
 │  Step 4 ─── Dynamic Chunking (40%)                                  │
 │  │           Semantic speaker-aware chunking                        │
 │  │           Max chunk: 120K tokens, 200-token overlap              │
 │  │                                                                   │
 │  Step 5 ─── Customer Context Enrichment (45%)                       │
 │  │           Lookup phone number → customer history in MongoDB      │
 │  │           Detect call type: fresh_sales / follow_up / confirm    │
 │  │           + Tenant config + objection baselines + SOP rubric     │
 │  │                                                                   │
 │  Step 6 ─── 4 PARALLEL AI EXTRACTORS (50%)                         │
 │  │           ┌──────────────┐  ┌───────────────┐                    │
 │  │           │   Summary    │  │  Compliance   │                    │
 │  │           │ (3-call LLM) │  │ (SOP metrics) │                    │
 │  │           └──────────────┘  └───────────────┘                    │
 │  │           ┌──────────────┐  ┌───────────────┐                    │
 │  │           │  Objections  │  │ Qualification │                    │
 │  │           │(7-stage pipe)│  │ (BANT 4-call) │                    │
 │  │           └──────────────┘  └───────────────┘                    │
 │  │                                                                   │
 │  Step 7 ─── Post-Processing (55%)                                   │
 │  │           Apply tenant qualification rules                       │
 │  │           Merge customer history, BANT score adjustment          │
 │  │           Lead score calculation                                 │
 │  │                                                                   │
 │  Step 8 ─── RAG Indexing (70%)                                      │
 │  │           Generate embeddings (HuggingFace, batch_size=32)       │
 │  │           Store in Milvus with metadata                          │
 │  │                                                                   │
 │  Step 9 ─── Database Storage (90%)                                  │
 │  │           calls → MongoDB (transcript, segments, metadata)       │
 │  │           call_summaries → MongoDB (all extracted intelligence)   │
 │  │           chunk_summaries → MongoDB (per-chunk analysis)         │
 │  │                                                                   │
 │  Step 10 ── Phase Detection (95%)                                   │
 │              Detect: greeting → discovery → qualification →         │
 │              objection_handling → closing → post_close              │
 │              Quality scores + flow score + missing phases           │
 └──────────────────────────────────────────────────────────────────────┘
```

---

## 4. AI Extractor Details

### 4.1 Summary Extractor
- **Pipeline:** 3 sequential LLM calls per chunk
- **Outputs:** Summary text, key points, action items, next steps, pending actions
- **Context:** Uses tenant-specific industry terms

### 4.2 Compliance Extractor (SOP Scoring)
- Evaluates calls against the company's active SOP document
- **21 dynamic metrics** (e.g., greeting, needs assessment, price presentation, closing)
- Produces: overall score (0-1), followed stages, missed stages
- Generates **coaching issues** with severity, how to fix, and example language

### 4.3 Objection Extractor (7-Stage Self-Consistency Pipeline)
```
Stage 1-2 : 4x parallel extraction (broad / strict / subtle / rep-centric)
Stage 3a  : Classification with baseline severity calibration
Stage 3b  : Overcome detection with transcript anchoring
Stage 4   : Confidence calibration
Stage 5   : Verify + Augment (anti-hallucination)
Stage 6   : Finalize with SOP response suggestions (Milvus RAG)
```
- **Output per objection:** category, severity, overcome status, transcript quote, response suggestions

### 4.4 Qualification Extractor (BANT Lead Scoring)
- **4 sequential LLM calls:**
  1. Core BANT (Budget, Authority, Need, Timeline) + booking status
  2. Appointment details and scheduling
  3. Customer intelligence (address, demographics, existing customer)
  4. Property details (roof type, HOA, solar, pets)
- **Lead Score:** Hot / Warm / Cold based on BANT breakdown

---

## 5. MongoDB — Primary Database

MongoDB stores all processed data. The API reads from these collections to serve results.

### Core Collections

```
┌─────────────────────────────────────────────────────────────────┐
│ COLLECTION: calls                                               │
│  Fields: call_id, company_id, phone_number, audio_url,          │
│          transcript (full text), segments (speaker-labeled),     │
│          status, duration, call_date, rep_role                   │
│  Indexes: call_id (unique), company_id, phone_number, status    │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: call_summaries                                      │
│  Fields: call_id, company_id                                    │
│  Nested:                                                        │
│    summary    → {summary, key_points, action_items}             │
│    compliance → {sop_compliance: {score, stages, coaching}}     │
│    objections → [{category, severity, overcome, suggestions}]   │
│    qualification → {bant_score, lead_score, booking_status}     │
│  Links to Milvus via milvus_id for RAG search                  │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: chunk_summaries                                     │
│  Per-chunk analysis for long calls (120K token max per chunk)   │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: sop_documents                                       │
│  SOP metadata, versioning, metrics (one active per company/role)│
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: weekly_insights                                     │
│  Generated every Sunday 00:00 UTC by APScheduler                │
│  Company analytics, per-customer insights, objection trends     │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: customers                                           │
│  Customer profiles, fuzzy search (name/phone/location)          │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: ask_otto_messages                                   │
│  Multi-turn conversation history for Ask Otto chat              │
│  Dual-write: MongoDB (primary) + Redis (30-min cache)           │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: coaching_sessions                                   │
│  Coaching records with baseline/follow-up metrics               │
├─────────────────────────────────────────────────────────────────┤
│ COLLECTION: tenant_configurations                               │
│  Per-company: qualification thresholds, service keywords,       │
│  urgency patterns, business hours (5-min Redis cache)           │
└─────────────────────────────────────────────────────────────────┘
```

### Important: MongoDB is Inside the Backend
Our test suite does **not** connect to MongoDB directly. The database lives inside the Otto backend at `ottoai.shunyalabs.ai`. We communicate with it through the REST API using the API key.

---

## 6. Redis Caching Strategy

| Cache Key Pattern                  | TTL       | Purpose                              |
|------------------------------------|-----------|--------------------------------------|
| `job:{job_id}:status`             | 24 hours  | Job progress tracking                |
| `processing_lock:{call_id}`       | 1 hour    | Prevent duplicate processing         |
| `conversation:{id}:context`       | 30 min    | Ask Otto conversation history        |
| `embedding:{model}:{hash}`        | 1 hour    | Embedding cache for RAG queries      |
| `tenant_config:{company_id}`      | 5 min     | Company config (fast reads)          |

---

## 7. Milvus Vector Store (Semantic Search)

- **Collection:** `otto_intelligence_v1`
- **Embedding Model:** HuggingFace `all-MiniLM-L6-v2` (384 dimensions, free)
- **Index Type:** HNSW (M=64, efConstruction=256, COSINE similarity)
- **Partitioned by:** `tenant_id` (company_id) for data isolation

**Stored Vectors:**
- Call summaries with metadata (sentiment, qualification, booking status)
- Chunk summaries for long calls
- SOP content for response suggestions

**Used By:**
- Ask Otto (semantic search across all call data)
- Objection Extractor (SOP-based response suggestions)
- Cross-source enrichment in Ask Otto queries

---

## 8. How Our Test Suite Connects

```
┌──────────────────────────────────────────────────────────────┐
│                    OUR TEST REPO                             │
│                                                              │
│  .env file:                                                  │
│    OTTO_API_BASE_URL = https://ottoai.shunyalabs.ai          │
│    OTTO_API_KEY      = 5q3fwl...BnBP                         │
│                                                              │
│  ┌────────────────────────┐  ┌────────────────────────┐      │
│  │  API Tests             │  │  ASR/STT Tests         │      │
│  │  (pytest)              │  │  (pytest)              │      │
│  │                        │  │                        │      │
│  │ Tests 19 API endpoints │  │ Tests word error rate  │      │
│  │ against real staging   │  │ of ASR transcription   │      │
│  │ data                   │  │                        │      │
│  └───────────┬────────────┘  └───────────┬────────────┘      │
│              │                           │                   │
└──────────────┼───────────────────────────┼───────────────────┘
               │                           │
               ▼                           ▼
       ┌──────────────┐            ┌──────────────┐
       │  Otto API    │            │  Otto API    │
       │  (REST)      │            │  (REST)      │
       │              │            │              │
       │  Reads from: │            │  Reads from: │
       │  MongoDB     │            │  MongoDB     │
       │  Redis       │            │              │
       │  Milvus      │            │              │
       └──────────────┘            └──────────────┘
```

---

## 9. Report Generator Data Flow

The `generate_report.py` script fetches already-processed data and renders it as HTML:

```
generate_report.py
    │
    ├── Step 1: GET /api/v1/call-processing/calls
    │           ?company_id=91ecfcb9...&limit=50
    │           → Returns 23 call records (id, phone, status, date)
    │
    ├── Step 2: For EACH call_id:
    │   ├── GET /api/v1/call-processing/summary/{call_id}
    │   │       → summary, compliance (21 SOP metrics), objections, qualification
    │   │
    │   └── GET /api/v1/call-processing/calls/{call_id}/detail
    │           → full transcript, speaker-labeled segments
    │
    ├── Step 3: GET /api/v1/call-processing/phases/analytics
    │           → Phase detection rates, commonly missing phases
    │
    └── Step 4: Render interactive HTML report
                → Expandable call cards with all data visualized
```

---

## 10. Staging Data Inventory

| Data Point               | Value                                              |
|--------------------------|----------------------------------------------------|
| **Company**              | Arizona Roofers                                    |
| **Company ID**           | `1be5ea90-d3ae-4b03-8b05-f5679cd73bc4`            |
| **Agent**                | Anthony (`anthony@arizonaroofers.com`)              |
| **Total Calls**          | 23                                                 |
| **Calls with Summaries** | 22                                                 |
| **Calls with Transcripts**| 23                                                |
| **Audio Source**         | S3 (ap-southeast-2 / Sydney)                       |
| **API Endpoint**         | `https://ottoai.shunyalabs.ai`                    |
| **Web App**              | `https://stage.app.gomotto.com`                    |

### Sample Audio URLs (Real Recordings)
```
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/56dc7e30-.../4019778374.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/6e37c8bb-.../4037028977.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/aa4018dd-.../4036931546.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/bdc3fc20-.../4036863062.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/a5933178-.../4036836500.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/8c6b15ee-.../4049722733.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/80913c6a-.../4043584280.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/eff6032d-.../4036334162.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/323d1a76-.../3998154371.mp3
https://ottoaudio.s3.ap-southeast-2.amazonaws.com/recordings/1fd7bea5-.../4015296617.mp3
```

---

## 11. Key Design Decisions

| Decision                        | Why                                            |
|---------------------------------|------------------------------------------------|
| MongoDB as primary DB           | Flexible schema for evolving JSON structures   |
| PostgreSQL optional             | Only needed for Ask Otto structured analytics  |
| Redis caching layer             | Sub-millisecond reads for hot data             |
| Milvus Zilliz (managed)         | No ops overhead for vector search              |
| APScheduler (in-process)        | Simple single-process deployment               |
| FastAPI BackgroundTasks          | Simpler than Celery for async processing       |
| Local HuggingFace embeddings    | Free, fast, no API rate limits                 |
| GROQ LLM (llama-3.3-70b)       | Fast inference, cost-effective                 |
| 7-stage objection pipeline      | Self-consistency prevents hallucination        |
| Multi-tenant by company_id      | All collections isolated per company           |

---

## 12. Detailed Architecture Documentation

For deeper technical details, see:

| Document | Location | Content |
|----------|----------|---------|
| Architecture Overview | `project_docs/ARCHITECTURE_README.md` | Tech stack, cost, timeline |
| Call Pipeline (Feature 1) | `project_docs/ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md` | Audio processing, extraction |
| Insights Engine (Feature 2) | `project_docs/ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md` | Weekly insights, scheduler |
| Ask Otto (Feature 3) | `project_docs/ARCHITECTURE_FEATURE_3_ASK_OTTO.md` | Conversational AI, routing |
| Document Ingestion (Feature 4) | `project_docs/ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md` | SOP upload, versioning |
| New Features (5-9) | `project_docs/ARCHITECTURE_FEATURE_5-9_NEW_FEATURES.md` | Lead scoring, coaching |
| API Reference | `project_docs/Updated_Otto_API_Documentation.md` | 50+ endpoints |
| Test Report | `STAKEHOLDER_TEST_REPORT.md` | Test coverage, results |
| Visual Report | `call_report.html` | Interactive call data |
