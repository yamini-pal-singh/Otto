# Otto AI Intelligence Service - Architecture Documentation

**Status:** ✅ Complete
**Version:** 5.1 (Independent Microservice)
**Date:** February 24, 2026
**Implementation:** FastAPI + APScheduler (No Celery)

> **Last Updated:** February 2026 - Added Conditional Prompt Enrichment (Task 4): dynamic tenant context, SOP rubric injection, Milvus RAG for objection responses, objection baseline calibration, and Ask Otto cross-source enrichment.

---

## 📚 Documentation Index

This folder contains the complete architecture documentation for the Otto AI Intelligence Service, redesigned as an independent microservice with comprehensive REST APIs.

### Core Feature Documents

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md](./ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md)** | Enhanced Call Processing Pipeline with APIs (FastAPI BackgroundTasks) |
| **[ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md](./ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md)** | Weekly Insights Engine with APScheduler (in-process scheduling) |
| **[ARCHITECTURE_FEATURE_3_ASK_OTTO.md](./ARCHITECTURE_FEATURE_3_ASK_OTTO.md)** | Ask Otto Chat Enhancement with dual-source routing (PostgreSQL + MongoDB + Milvus RAG) |
| **[ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md](./ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md)** | SOP Document Ingestion & Dynamic Metrics Engine |

### Advanced Analytics Documents (New!)

| Document | Description |
|----------|-------------|
| **[ARCHITECTURE_FEATURE_5-9_NEW_FEATURES.md](./ARCHITECTURE_FEATURE_5-9_NEW_FEATURES.md)** | Features 5-9: BANT Lead Scoring, SOP Versioning, Coaching Impact, Agent Progression, Phase Detection |

### Supporting Documents

| Document | Description |
|----------|-------------|
| **[Updated_Otto_API_Documentation.md](./Updated_Otto_API_Documentation.md)** | Complete API documentation with cURL examples |
| **[ENUMS_INVENTORY_BY_SERVICE.md](./ENUMS_INVENTORY_BY_SERVICE.md)** | Comprehensive enum definitions |
| **[payload.json](./payload.json)** | Expected JSON output structure |
| **[llm_calls.txt](./llm_calls.txt)** | LLM call specifications |
| **[mongoDB-schema.txt](./mongoDB-schema.txt)** | MongoDB collection schemas |
| **[sqlDB-schema.txt](./sqlDB-schema.txt)** | PostgreSQL analytics database schema |

---

## 🎯 Quick Start

### For Stakeholders
1. Start with this README for high-level architecture
2. Review technology stack and deployment strategy
3. Check cost estimates and timeline

### For Developers
1. Read this README first for an overview
2. Deep dive into specific features:
   - **[Feature 1](./ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md)** for call processing
   - **[Feature 2](./ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md)** for insights
   - **[Feature 3](./ARCHITECTURE_FEATURE_3_ASK_OTTO.md)** for conversational AI
   - **[Feature 4](./ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md)** for SOP management
   - **[Features 5-9](./ARCHITECTURE_FEATURE_5-9_NEW_FEATURES.md)** for advanced analytics
3. Reference **[ENUMS_INVENTORY_BY_SERVICE.md](./ENUMS_INVENTORY_BY_SERVICE.md)** for data structures
4. Use **[Updated_Otto_API_Documentation.md](./Updated_Otto_API_Documentation.md)** for API testing

### For DevOps/Infrastructure
1. Review this README for deployment architecture
2. Check MongoDB, Redis, PostgreSQL, and Milvus Zilliz requirements
3. Review monitoring and observability section

---

## 🏗️ Architecture Highlights

### Key Changes from Original

| Aspect | Original (Embedded) | New (Microservice) |
|--------|---------------------|-------------------|
| **Database** | PostgreSQL | MongoDB (primary) + PostgreSQL (analytics) |
| **Cache** | PostgreSQL | Redis (Upstash SSL) |
| **Vector Store** | Self-hosted Milvus | Milvus Zilliz Cloud |
| **Job Processing** | Celery workers | FastAPI BackgroundTasks |
| **Scheduling** | Celery Beat (external) | APScheduler (in-process) |
| **Embeddings** | OpenAI API | HuggingFace (local, all-MiniLM-L6-v2) |
| **LLM** | Various | GROQ (llama-3.3-70b-versatile) |
| **Integration** | Embedded in monolith | REST APIs |
| **Deployment** | Monolithic | Single containerized process |
| **Port** | 8000 | 8000 (configurable via API_PORT) |

### Technology Stack

```
┌──────────────────────────────────────────────────┐
│         FastAPI REST API (Port 8000)              │
│       + APScheduler (in-process)                  │
├──────────────────────────────────────────────────┤
│  MongoDB   │  Redis   │  Milvus Zilliz │ PostgreSQL│
│ (Documents)│ (Cache)  │  (Vectors)     │(Analytics)│
├──────────────────────────────────────────────────┤
│        FastAPI BackgroundTasks (Async)             │
├──────────────────────────────────────────────────┤
│  GROQ LLM  │ HuggingFace │      S3/Local          │
│(llama-3.3) │ (Embeddings)│     (Files)            │
└──────────────────────────────────────────────────┘

Key: Single process architecture, no Celery
     PostgreSQL optional — used by Ask Otto for analytics queries
```

---

## 📋 Feature Summary

### Feature 1: Enhanced Call Processing Pipeline

**APIs:**
- `POST /api/v1/call-processing/process` - Submit call for processing
- `GET /api/v1/call-processing/status/{job_id}` - Check status
- `GET /api/v1/call-processing/summary/{call_id}` - Get structured summary
- `GET /api/v1/call-processing/chunks/{call_id}` - Get chunk summaries
- `POST /api/v1/call-processing/retry/{job_id}` - Retry failed job
- `GET /api/v1/call-processing/calls/{call_id}/phases` - Get conversation phases
- `GET /api/v1/call-processing/phases/search` - Search calls by phase patterns
- `GET /api/v1/call-processing/phases/analytics` - Company-wide phase analytics
- `GET /api/v1/call-processing/summaries` - List call summaries with filters
- `GET /api/v1/call-processing/calls` - List calls with filters
- `GET /api/v1/call-processing/calls/{call_id}/detail` - Get full call detail

**Capabilities:**
- Audio → Transcription → Dynamic Chunking
- **Parallel Extraction Architecture** (4 specialized extractors)
- **Hybrid Diarization** (LLM + API timestamp alignment)
- Chunk-level + Overall JSON summaries
- RAG indexing in Milvus (local HuggingFace embeddings)
- **Self-Consistency Objection Detection** (7-stage pipeline: 4 parallel perspectives + verification agent)
- FastAPI BackgroundTasks for async processing
- **BANT Lead Scoring** with full breakdown
- **Conversation Phase Detection v1.2** (hybrid alignment)
- **Customer Intelligence** (existing customer detection, call type)
- **Tenant Configuration** integration
- **Conditional Prompt Enrichment** (dynamic tenant context, SOP rubrics, Milvus RAG for objection responses, objection baselines)

**Performance:** < 120s end-to-end processing

### Feature 2: Weekly Insights Engine

**APIs:**
- `POST /api/v1/insights/generate` - Trigger generation (cron-called)
- `GET /api/v1/insights/status/{job_id}` - Check generation status
- `GET /api/v1/insights/company/{company_id}/current` - Get company insights
- `GET /api/v1/insights/customers` - Get customer insights
- `GET /api/v1/insights/objections/{company_id}` - Get objection insights
- `GET /api/v1/insights/leads` - Get leads with filtering
- `GET /api/v1/insights/leads/distribution` - Lead score distribution
- `GET /api/v1/insights/leads/{customer_id}/history` - Lead score history
- `GET /api/v1/insights/agents/{rep_id}/progression` - Agent progression
- `GET /api/v1/insights/agents/{rep_id}/peer-comparison` - Peer comparison (on-demand)
- `GET /api/v1/insights/agents/summary` - Manager dashboard

**Capabilities:**
- Company-wide analytics with insight headings
- Per-customer insights with engagement scoring
- Objection trend analysis with best responses
- Week-over-week comparisons
- **Lead Scoring Endpoints** (filtering, distribution, history)
- APScheduler for automatic weekly generation (Sunday 00:00 UTC)
- **Agent Progression Tracking** (trend, anomaly detection)
- **Peer Comparison** (on-demand percentile ranking)

**Performance:** < 30 minutes for all companies

### Feature 3: Ask Otto Chat Enhancement

**APIs:**
- `POST /api/v1/ask-otto/conversations` - Create conversation
- `POST /api/v1/ask-otto/conversations/{id}/messages` - Send message
- `GET /api/v1/ask-otto/conversations/{id}/messages` - Get history
- `GET /api/v1/ask-otto/conversations/{id}` - Get conversation details
- `DELETE /api/v1/ask-otto/conversations/{id}` - Delete conversation

**Capabilities:**
- Multi-turn conversation memory (dual-write MongoDB + Redis)
- **13-Intent Classification** with dual-source data routing
- **Dual-Source Data Routing**: PostgreSQL (analytics: rep performance, booking trends, objections, leads) + MongoDB (coaching, weekly insights, coach effectiveness)
- RAG semantic search (multi-corpus: calls, chunks, SOP documents)
- Customer context resolution (name, phone, location)
- **SOP Integration** (automatic query detection and search)
- **Cross-Source Enrichment** (coaching data for rep queries, Milvus call history for customers, objection call examples, tenant context)
- Source attribution with confidence scores
- Follow-up suggestions (rule-based, intent-specific)
- Local HuggingFace embeddings (cached in Redis)
- 24-hour conversation expiry

**Performance:** < 3s response time (p95)

### Feature 4: SOP Document Ingestion

**APIs:**
- `POST /api/v1/sop/documents/upload` - Upload SOP (file or URL)
- `GET /api/v1/sop/documents/status/{job_id}` - Check processing status
- `GET /api/v1/sop/metrics/{company_id}` - Get active metrics
- `GET /api/v1/sop/documents/{sop_id}` - Get document details
- `GET /api/v1/sop/documents` - List company SOPs
- `PATCH /api/v1/sop/documents/{sop_id}/status` - Update status
- `DELETE /api/v1/sop/documents/{sop_id}` - Delete document
- `POST /api/v1/sop/documents/{sop_id}/versions` - Upload new version
- `GET /api/v1/sop/documents/{sop_id}/versions` - Get version history
- `GET /api/v1/sop/documents/{sop_id}/versions/{v}` - Get specific version
- `POST /api/v1/sop/documents/{sop_id}/reanalyze` - Re-analyze calls
- `GET /api/v1/sop/reanalysis/{job_id}` - Get re-analysis status

**Capabilities:**
- PDF/Word document ingestion (file upload or URL)
- LLM-based SOP validation with keyword fallback
- Dynamic metric extraction (rolling across chunks)
- Call evaluation against SOP (per-chunk with aggregation)
- **Single Active SOP Rule** (one per company/role)
- **Version Control** (auto-increment, scheduled activation)
- **Historical Re-Analysis** (14-day default lookback)
- **Duplicate Detection** (file hash comparison)
- RAG indexing of SOP content + metrics

**Performance:** < 5 minutes for 50-page document

### Feature 7: Coaching Impact Measurement

**APIs:**
- `POST /api/v1/coaching/sessions` - Create coaching session (auto-baseline)
- `GET /api/v1/coaching/sessions/{session_id}` - Get session details
- `GET /api/v1/coaching/sessions` - List sessions (filtered)
- `GET /api/v1/coaching/sessions/{session_id}/impact` - Get impact report
- `PATCH /api/v1/coaching/sessions/{session_id}/status` - Update status/extend
- `GET /api/v1/coaching/coaches/{coach_id}/effectiveness` - Coach effectiveness
- `GET /api/v1/coaching/roi` - Company-wide ROI

**Capabilities:**
- Automatic baseline calculation (last 5 calls, outlier removal)
- Follow-up impact measurement (14-day default)
- Target tracking per focus area
- Coach effectiveness scoring (90-day window)
- Skill-level effectiveness analysis
- **Session Extension** (7 days if insufficient calls)
- **Focus Area Mapping** (BANT, compliance, objection handling, etc.)
- **Background Jobs** (daily follow-up check, weekly effectiveness)

**Performance:** < 5s impact calculation

### Tenant Configuration (Cross-Cutting Feature)

**APIs:**
- `POST /api/v1/tenant-config/` - Create tenant configuration
- `GET /api/v1/tenant-config/{company_id}` - Get configuration
- `PUT /api/v1/tenant-config/{company_id}` - Update configuration
- `DELETE /api/v1/tenant-config/{company_id}` - Delete configuration
- `GET /api/v1/tenant-config/{company_id}/sops` - List SOP associations
- `POST /api/v1/tenant-config/{company_id}/sops/{role}` - Associate SOP
- `POST /api/v1/tenant-config/{company_id}/rules` - Add qualification rule
- `POST /api/v1/tenant-config/{company_id}/services` - Add service configuration

**Capabilities:**
- Per-company qualification thresholds (hot/warm/cold)
- Service prioritization with wait times
- Custom qualification rules (condition-based scoring)
- Role-specific SOP associations
- Urgency detection patterns
- Budget indicators
- Service keywords mapping
- Business hours configuration

**Usage:** Applied during call processing to customize extraction and scoring per tenant. Tenant context dynamically replaces hardcoded industry context in all 5 extractors (summary, compliance, objection, qualification, summary) and provides company awareness to Ask Otto.

---

## 🔑 Key Design Decisions

### 1. MongoDB as Primary Database
- **Why:** Flexible schema for evolving JSON structures
- **Benefit:** No migrations for new fields, perfect for LLM outputs
- **Trade-off:** Less rigid constraints vs PostgreSQL

### 2. PostgreSQL for Analytics (Optional)
- **Why:** Ask Otto dual-source routing needs structured analytics data (rep performance, booking trends, leads)
- **Benefit:** SQL aggregations for analytical queries; enables data-driven responses in Ask Otto
- **Trade-off:** Optional dependency — Ask Otto analytics queries gracefully disabled when PostgreSQL not configured
- **Connection:** asyncpg async pool (2-10 connections, configurable)

### 3. Redis for Fast Access
- **Why:** Sub-millisecond reads for hot data
- **Benefit:** Job status, cache, session storage
- **Trade-off:** Additional service to manage (using Upstash SSL)

### 4. Milvus Zilliz Cloud
- **Why:** Managed vector database, no ops overhead
- **Benefit:** Auto-scaling, backups, monitoring included
- **Trade-off:** Vendor lock-in vs self-hosted

### 5. APScheduler for Scheduled Jobs
- **Why:** In-process scheduling, no separate Beat process
- **Benefit:** Simple deployment, automatic start/stop with app
- **Trade-off:** Single instance only (no distributed scheduling)

### 6. FastAPI BackgroundTasks Instead of Celery
- **Why:** Simpler architecture, fewer dependencies
- **Benefit:** Single process deployment, easier debugging
- **Trade-off:** No distributed task queue (suitable for current scale)

### 7. Local HuggingFace Embeddings
- **Why:** Free, fast, no API rate limits
- **Benefit:** Zero embedding cost, sub-second generation
- **Trade-off:** Slightly lower quality than OpenAI (acceptable for RAG)

---

## 📊 Performance Targets

| Metric | Target | Feature |
|--------|--------|---------|
| Call processing (E2E) | < 120s | Feature 1 |
| API response time | < 500ms | All |
| RAG search latency | < 300ms | Feature 3 |
| Weekly insights generation | < 30 min | Feature 2 |
| Ask Otto response time | < 3s | Feature 3 |
| SOP document processing | < 5 min | Feature 4 |
| Lead score calculation | < 100ms | Feature 5 |
| SOP version switch | < 5s | Feature 6 |
| Coaching impact measurement | < 5s | Feature 7 |
| Agent progression (8 weeks) | < 3s | Feature 8 |
| Phase detection (LLM) | < 10s | Feature 9 |
| Concurrent requests | 1000 RPS | All |

---

## 💰 Cost Estimate

| Component | Monthly Cost (USD) |
|-----------|-------------------|
| MongoDB Atlas (M10) | $60 |
| Redis Cloud (Upstash) | $30 |
| Milvus Zilliz (2GB vectors) | $100 |
| AWS S3 (100GB) | $3 |
| PostgreSQL (optional analytics) | $0-50 |
| Compute (Single container, 4GB RAM) | $50 |
| LLM APIs (GROQ) | $200 |
| Transcription (Shunya/AssemblyAI) | $100 |
| **Total** | **~$543-593/month** |

*Estimates for small-medium workload, scales with usage*
*Significant cost savings from local embeddings (no OpenAI embedding costs)*

---

## ⏱️ Development Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1: Infrastructure | 1 week | DB setup, Docker compose |
| Phase 2: Feature 1 | 3 weeks | Call pipeline APIs |
| Phase 3: Feature 2 | 2 weeks | Insights engine APIs |
| Phase 4: Feature 3 | 3 weeks | Ask Otto APIs |
| Phase 5: Feature 4 | 2 weeks | SOP ingestion APIs |
| Phase 6: Features 5-9 | 3 weeks | Advanced analytics (Lead Scoring, Versioning, Coaching, Progression, Phases) |
| Phase 7: Testing | 2 weeks | Load testing, optimization |
| Phase 8: Deployment | 1 week | Production deployment |
| **Total** | **17 weeks** | **Full service** |

**Current Status:** ✅ All phases complete!

---

## 🔒 Security & Compliance

- **Authentication:** Single API key (simple & secure)
- **Data Isolation:** MongoDB company_id filtering, Milvus partitions
- **Encryption:** HTTPS/TLS in transit, at-rest encryption enabled
- **PII Handling:** Phone numbers hashed in logs
- **Audit Logging:** All API calls logged with request ID

---

## 📈 Monitoring & Observability

- **Metrics:** Prometheus (latency, errors, queue depth)
- **Logging:** Structured JSON logs
- **Tracing:** OpenTelemetry (end-to-end request tracking)
- **Alerting:** Error rate > 5%, queue depth > 1000

---

## 🚀 Getting Started with Implementation

### Step 1: Review Architecture
```bash
# Read documents in this order:
1. ARCHITECTURE_README.md (this file)
2. ARCHITECTURE_FEATURE_1_CALL_PIPELINE.md
3. ARCHITECTURE_FEATURE_2_INSIGHTS_ENGINE.md
4. ARCHITECTURE_FEATURE_3_ASK_OTTO.md
5. ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md
6. ARCHITECTURE_FEATURE_5-9_NEW_FEATURES.md
```

### Step 2: Set Up Development Environment
```bash
# Clone repository
git clone <repo_url>
cd otto-intelligence

# Set up MongoDB, Redis, Milvus (Docker Compose)
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp env.example .env
# Edit .env with your API keys
```

### Step 3: Start Building
```bash
# Recommended implementation order:
1. Feature 1: Call Processing Pipeline (core functionality) ✅ COMPLETE
2. Feature 3: Ask Otto (depends on Feature 1 for data) ✅ COMPLETE
3. Feature 4: SOP Document Ingestion (extends Features 1 & 3) ✅ COMPLETE
4. Feature 2: Insights Engine (depends on all features) ✅ COMPLETE
5. Feature 5: BANT Lead Scoring (extends Feature 1) ✅ COMPLETE
6. Feature 6: SOP Version Control (extends Feature 4) ✅ COMPLETE
7. Feature 7: Coaching Impact Measurement (uses Feature 1 data) ✅ COMPLETE
8. Feature 8: Agent Progression (extends Feature 2) ✅ COMPLETE
9. Feature 9: Conversation Phase Detection (extends Feature 1) ✅ COMPLETE
```

---

## 📞 Support & Questions

For questions about this architecture:
1. Check the detailed feature documents
2. Review `docs/ENUMS_INVENTORY_BY_SERVICE.md` for data structures
3. See `payload.json` for expected output format
4. Contact architecture team

---

## ✅ Documentation Status

### Core Features
- [x] Overview document complete
- [x] Feature 1 architecture complete (Call Processing Pipeline)
- [x] Feature 2 architecture complete (Weekly Insights Engine)
- [x] Feature 3 architecture complete (Ask Otto Chat)
- [x] Feature 4 architecture complete (SOP Document Ingestion)

### Advanced Analytics (v2.0)
- [x] Feature 5 architecture complete (BANT Lead Scoring)
- [x] Feature 6 architecture complete (SOP Version Control)
- [x] Feature 7 architecture complete (Coaching Impact Measurement)
- [x] Feature 8 architecture complete (Agent Progression Tracking)
- [x] Feature 9 architecture complete (Conversation Phase Detection)

### Supporting Documentation
- [x] API endpoints documented (50+ endpoints)
- [x] Database schemas defined (15+ MongoDB collections + PostgreSQL analytics)
- [x] Redis patterns documented
- [x] Performance targets set
- [x] Cost estimates provided
- [x] Timeline established
- [x] API documentation complete (Updated_Otto_API_Documentation.md)
- [x] **All features implemented and tested!**

**✅ v5.1 Implementation Complete! All Documentation Updated!**

---

## 📝 Document Changelog

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-24 | 5.1 | Added Conditional Prompt Enrichment: dynamic tenant context, SOP rubrics, Milvus RAG for objections, objection baselines, Ask Otto cross-source enrichment |
| 2026-02-04 | 5.0 | Updated all feature documents with current implementation details |
| 2026-01-28 | 4.0 | Added Features 5-9 architecture documentation |
| 2026-01-09 | 3.1 | Updated with actual implementation details (FastAPI BackgroundTasks, APScheduler, local embeddings) |
| 2026-01-08 | 3.0 | Complete microservice architecture redesign |
| 2026-01-07 | 2.0 | Original embedded architecture (STAKEHOLDER_ARCHITECTURE_OVERVIEW.md) |

### v5.1 Update Summary — Conditional Prompt Enrichment

| Enrichment | Description |
|------------|-------------|
| **Dynamic Tenant Context** | Replaces hardcoded `HOME_SERVICES_CONTEXT` with per-company context from `TenantConfiguration` across all 5 extractors |
| **SOP Rubric Injection** | Injects 4-tier evaluation rubrics (Excellent/Good/Needs Improvement/Poor) into compliance coaching for low-scoring metrics |
| **SOP Document RAG** | Milvus RAG search fetches company SOP scripts to populate `response_suggestions` in objection extraction |
| **Objection Baselines** | MongoDB `weekly_insights` objection data calibrates severity in classification (Stage 3a) |
| **Ask Otto Dual-Source Routing** | 13-intent classification with PostgreSQL (analytics) + MongoDB (coaching/insights) data routing |
| **Ask Otto Cross-Source** | 4 cross-enrichments: coaching→rep_performance, Milvus→customer_lookup, Milvus→objection_analysis, tenant→all intents |

### v5.0 Update Summary

| Document | Key Updates |
|----------|-------------|
| **Feature 1** | Parallel extraction, hybrid diarization v1.2, multi-stage objection detection |
| **Feature 2** | Lead scoring endpoints, insight headings, agent progression |
| **Feature 3** | 13-intent classification, dual-source routing (PostgreSQL + MongoDB), cross-source enrichment, dual-write caching |
| **Feature 4** | URL-based upload, single active SOP rule, version control |
| **Features 5-9** | Focus area mapping, coaching background jobs, implementation highlights |

