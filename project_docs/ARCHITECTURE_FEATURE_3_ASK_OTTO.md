# Feature 3: Ask Otto Chat Enhancement API

**Version:** 5.1
**Date:** February 24, 2026
**Service:** Independent Microservice Architecture
**Implementation:** FastAPI + 13-Intent Classification + Dual-Source Data Routing + Local Embeddings

> **Last Updated:** February 2026 - Added **Dual-Source Data Routing** (PostgreSQL analytics + MongoDB insights), **13-intent classification**, **Cross-Source Enrichment** (coaching data for rep_performance, Milvus call history for customer_lookup, objection call examples for objection_analysis, tenant context for company awareness), and new `analytics_data_service.py` / `mongodb_insights_service.py` services.

---

## Overview

Ask Otto is an enhanced conversational AI system that provides intelligent Q&A capabilities with:
- **Multi-turn conversation history** stored in MongoDB with Redis caching
- **13-intent classification** for precise query routing
- **Dual-source data routing**: PostgreSQL (rep performance, booking trends, leads, objections) + MongoDB (coaching sessions, weekly insights, coach effectiveness)
- **RAG integration** with Milvus Zilliz Cloud for semantic search
- **Customer context** retrieval from MongoDB by phone number or name
- **Multi-source data fusion** from calls, summaries, chunks, SOP documents, analytics, and coaching records
- **Local HuggingFace embeddings** for fast, cost-effective semantic search

**Implementation Status**: ✅ **Fully Implemented** - Uses GROQ for LLM (llama-3.3-70b-versatile) and local Sentence Transformers for embeddings. PostgreSQL analytics optional (gracefully disabled when not configured).

### Key Enhancements (v5.1)

| Enhancement | Description |
|-------------|-------------|
| **13-Intent Classification** | LLM-based query classification into 13 intent categories for precise routing |
| **Dual-Source Data Routing** | PostgreSQL for analytics (rep leaderboards, booking trends, leads) + MongoDB for coaching/insights |
| **SOP Integration** | Automatic SOP query detection and corpus search |
| **Cross-Source Enrichment** | Intent-specific data fusion from MongoDB coaching, Milvus call summaries, and tenant config |
| **Dual-Write Caching** | MongoDB + Redis for high availability |
| **Customer Context** | Recent calls summary, qualification tracking |
| **Response Metadata** | Tracks response_time_ms, rag_results_count |
| **Follow-up Suggestions** | Rule-based, intent-specific suggestions |

### Architecture Note

The implementation uses a **sequential pipeline with 13-intent classification and dual-source data routing** (class is still called `LangGraphService` for historical reasons):

```
Query Classification (13 intents) → Data Routing:
  ├─ PostgreSQL Analytics (rep_performance, booking_trends, leads, etc.)
  ├─ MongoDB Insights (coaching_history, weekly_performance, etc.)
  ├─ Milvus RAG (SOP content, call/chunk summaries)
  ├─ Customer Context (MongoDB fuzzy lookup)
  └─ Cross-Source Enrichment (coaching, Milvus history, tenant context)
→ Response Synthesis (data-aware formatting) → Source Extraction → Follow-ups
```

This provides precise data routing based on query intent. PostgreSQL handles analytical queries (aggregate stats, leaderboards) while MongoDB provides coaching/insight enrichment data. The **cross-source enrichment** step conditionally adds supplementary data from other sources based on the detected intent.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ASK OTTO CHAT ENHANCEMENT - API FLOW                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    CLIENT (Dashboard / Otto Backend)                 │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │    POST /api/v1/ask-otto/conversations                               │   │
│  │                                                                      │   │
│  │    Request: Create New Conversation                                  │   │
│  │    {                                                                 │   │
│  │      "company_id": "acme_roofing",                                   │   │
│  │      "user_id": "user_123",                                          │   │
│  │      "metadata": {                                                   │   │
│  │        "source": "dashboard",                                        │   │
│  │        "user_name": "Manager John"                                   │   │
│  │      }                                                               │   │
│  │    }                                                                 │   │
│  │                                                                      │   │
│  │    Response (201 Created):                                           │   │
│  │    {                                                                 │   │
│  │      "conversation_id": "conv_abc123",                               │   │
│  │      "company_id": "acme_roofing",                                   │   │
│  │      "user_id": "user_123",                                          │   │
│  │      "created_at": "2026-01-08T10:30:00Z",                           │   │
│  │      "message_count": 0                                              │   │
│  │    }                                                                 │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │    POST /api/v1/ask-otto/conversations/{id}/messages                 │   │
│  │                                                                      │   │
│  │    Request: Send Message                                             │   │
│  │    {                                                                 │   │
│  │      "message": "What did Kevin from Arizona say about roof leak?",  │   │
│  │      "context": {                                                    │   │
│  │        "include_customer_context": true,                             │   │
│  │        "max_rag_results": 5                                          │   │
│  │      }                                                               │   │
│  │    }                                                                 │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              STEP 1: LOAD CONVERSATION CONTEXT                       │   │
│  │                                                                      │   │
│  │  Redis Cache Check:                                                  │   │
│  │  Key: conversation:{conv_id}:context                                 │   │
│  │                                                                      │   │
│  │  Cache Miss → MongoDB Query:                                         │   │
│  │  db.ask_otto_messages.find({                                         │   │
│  │    conversation_id: "conv_abc123"                                    │   │
│  │  }).sort({ created_at: -1 }).limit(10)                               │   │
│  │                                                                      │   │
│  │  Result: Last 5 Q&A pairs (sliding window)                           │   │
│  │  [                                                                   │   │
│  │    {role: "user", content: "Previous question 1"},                   │   │
│  │    {role: "assistant", content: "Previous answer 1"},                │   │
│  │    ...                                                               │   │
│  │  ]                                                                   │   │
│  │                                                                      │   │
│  │  Cache in Redis (TTL: 30 minutes)                                    │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │            STEP 2: LANGGRAPH AGENT ORCHESTRATION                     │   │
│  │                                                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  NODE 1: CLASSIFY & EXTRACT                                     │  │   │
│  │  │                                                                 │  │   │
│  │  │  LLM analyzes query and extracts:                               │  │   │
│  │  │  • Intent: "query_customer_call"                                │  │   │
│  │  │  • Entities:                                                    │  │   │
│  │  │    - customer_name: "Kevin"                                     │  │   │
│  │  │    - location: "Arizona"                                        │  │   │
│  │  │    - topic: "roof leak"                                         │  │   │
│  │  │    - phone_number: null (not detected)                          │  │   │
│  │  │  • Requires:                                                    │  │   │
│  │  │    - Customer context: YES                                      │  │   │
│  │  │    - RAG search: YES                                            │  │   │
│  │  │    - Analytics: NO                                              │  │   │
│  │  │    - CRM: NO                                                    │  │   │
│  │  └─────────────────────────────┬───────────────────────────────────┘  │   │
│  │                                │                                      │   │
│  │                                ▼                                      │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │  NODE 2: ROUTER                                                 │  │   │
│  │  │                                                                 │  │   │
│  │  │  Based on classification, route to tools:                       │  │   │
│  │  │  → customer_context_tool (for Kevin + Arizona)                  │  │   │
│  │  │  → rag_search_tool (for "roof leak")                            │  │   │
│  │  └─────────────────────────────┬───────────────────────────────────┘  │   │
│  └────────────────────────────────┼──────────────────────────────────────┘   │
│                                   │                                         │
│                 ┌─────────────────┴─────────────────┐                       │
│                 │ PARALLEL TOOL EXECUTION            │                       │
│                 │                                    │                       │
│                 ▼                                    ▼                       │
│  ┌──────────────────────────┐         ┌──────────────────────────┐          │
│  │  TOOL 1:                 │         │  TOOL 2:                 │          │
│  │  CUSTOMER CONTEXT        │         │  RAG MULTI-SOURCE        │          │
│  │                          │         │  SEARCH                  │          │
│  │  1. Fuzzy name match     │         │                          │          │
│  │     "Kevin" + "Arizona"  │         │  1. Generate embedding   │          │
│  │                          │         │     for query            │          │
│  │  MongoDB Query:          │         │                          │          │
│  │  db.customers.find({     │         │  2. Milvus search:       │          │
│  │    company_id: "...",    │         │     Filter:              │          │
│  │    $text: {              │         │     • tenant_id          │          │
│  │      $search: "Kevin"    │         │     • corpus_type IN     │          │
│  │    },                    │         │       ["call_summary",   │          │
│  │    $or: [                │         │        "chunk_summary"]  │          │
│  │      {phone: ~/^.*AZ/},  │         │     Top K: 5             │          │
│  │      {address: ~/Arizona/}]       │         │                          │          │
│  │  })                      │         │  3. Retrieve:            │          │
│  │                          │         │     • Summary JSON       │          │
│  │  Result:                 │         │     • Call metadata      │          │
│  │  {                       │         │     • Customer phone     │          │
│  │    customer_id: "...",   │         │                          │          │
│  │    name: "Kevin",        │         │  Result:                 │          │
│  │    phone: "+14805551234",│         │  [                       │          │
│  │    address: "Arizona",   │         │    {                     │          │
│  │    total_calls: 5,       │         │      call_id: "5002",    │          │
│  │    last_call: "...",     │         │      score: 0.92,        │          │
│  │    status: "warm"        │         │      summary: {...},     │          │
│  │  }                       │         │      phone: "+1480..."   │          │
│  │                          │         │    },                    │          │
│  │  2. Fetch call history:  │         │    ...                   │          │
│  │  db.calls.find({         │         │  ]                       │          │
│  │    customer_id: "...",   │         │                          │          │
│  │    company_id: "..."     │         │  4. Load full summaries  │          │
│  │  }).sort({               │         │     from MongoDB:        │          │
│  │    call_date: -1         │         │     db.call_summaries    │          │
│  │  }).limit(5)             │         │     .find({              │          │
│  │                          │         │       call_id: {$in: []} │          │
│  │  3. Cache result:        │         │     })                   │          │
│  │  Redis TTL: 5 min        │         │                          │          │
│  └─────────┬────────────────┘         └─────────┬────────────────┘          │
│            │                                    │                            │
│            └────────────────┬───────────────────┘                            │
│                             │                                                │
│                             ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                  NODE 3: CONTEXT MERGER                              │   │
│  │                                                                      │   │
│  │  Merge all retrieved data into unified context:                     │   │
│  │                                                                      │   │
│  │  Context Object:                                                     │   │
│  │  {                                                                   │   │
│  │    "customer_profile": {                                             │   │
│  │      "name": "Kevin",                                                │   │
│  │      "phone": "+14805551234",                                        │   │
│  │      "location": "Arizona",                                          │   │
│  │      "status": "warm",                                               │   │
│  │      "total_calls": 5,                                               │   │
│  │      "last_call_date": "2026-01-08"                                  │   │
│  │    },                                                                │   │
│  │    "call_summaries": [                                               │   │
│  │      {                                                               │   │
│  │        "call_id": "5002",                                            │   │
│  │        "date": "2026-01-08",                                         │   │
│  │        "summary": "Kevin called about leaking flat roof...",         │   │
│  │        "key_points": [...],                                          │   │
│  │        "objections": [                                               │   │
│  │          {                                                           │   │
│  │            "category": "Timing",                                     │   │
│  │            "text": "7 to 9 weeks is too long"                        │   │
│  │          }                                                           │   │
│  │        ],                                                            │   │
│  │        "qualification": {...}                                        │   │
│  │      }                                                               │   │
│  │    ],                                                                │   │
│  │    "conversation_history": [                                         │   │
│  │      {role: "user", content: "Previous Q"},                          │   │
│  │      {role: "assistant", content: "Previous A"}                      │   │
│  │    ]                                                                 │   │
│  │  }                                                                   │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │              NODE 4: RESPONSE SYNTHESIZER                            │   │
│  │                                                                      │   │
│  │  LLM generates response with:                                        │   │
│  │  • Full context from merger                                          │   │
│  │  • Conversation history                                              │   │
│  │  • Instructions to cite sources                                      │   │
│  │  • Instructions for follow-up suggestions                            │   │
│  │                                                                      │   │
│  │  Prompt Template:                                                    │   │
│  │  """                                                                 │   │
│  │  You are Otto, an AI sales assistant.                                │   │
│  │                                                                      │   │
│  │  Conversation History:                                               │   │
│  │  {conversation_history}                                              │   │
│  │                                                                      │   │
│  │  Retrieved Context:                                                  │   │
│  │  {merged_context}                                                    │   │
│  │                                                                      │   │
│  │  User Question:                                                      │   │
│  │  {user_message}                                                      │   │
│  │                                                                      │   │
│  │  Instructions:                                                       │   │
│  │  1. Answer based ONLY on retrieved context                           │   │
│  │  2. Cite specific call IDs as sources                                │   │
│  │  3. If info not found, say "I don't have that information"           │   │
│  │  4. Suggest 2-3 relevant follow-up questions                         │   │
│  │  """                                                                 │   │
│  │                                                                      │   │
│  │  LLM Response:                                                       │   │
│  │  "Kevin from Arizona called about a leaking flat roof over his       │   │
│  │  patio (Call #5002). The roof was built in 2006. He was concerned    │   │
│  │  about the 7-9 week timeline for repairs. Travis suggested he        │   │
│  │  consider hiring a local roofing handyman for faster service."       │   │
│  │                                                                      │   │
│  │  Extract Sources:                                                    │   │
│  │  - Call #5002 mentioned in response → Add to sources                 │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   STEP 3: STORE & RESPOND                            │   │
│  │                                                                      │   │
│  │  1. Store user message in MongoDB:                                   │   │
│  │     db.ask_otto_messages.insertOne({                                 │   │
│  │       conversation_id: "conv_abc123",                                │   │
│  │       role: "user",                                                  │   │
│  │       content: "What did Kevin...",                                  │   │
│  │       created_at: ISODate(...)                                       │   │
│  │     })                                                               │   │
│  │                                                                      │   │
│  │  2. Store assistant response in MongoDB:                             │   │
│  │     db.ask_otto_messages.insertOne({                                 │   │
│  │       conversation_id: "conv_abc123",                                │   │
│  │       role: "assistant",                                             │   │
│  │       content: "Kevin from Arizona...",                              │   │
│  │       sources: [                                                     │   │
│  │         {type: "call_summary", call_id: "5002", confidence: 0.95}    │   │
│  │       ],                                                             │   │
│  │       metadata: {                                                    │   │
│  │         customer_id: "cust_123",                                     │   │
│  │         tokens_used: 850                                             │   │
│  │       },                                                             │   │
│  │       created_at: ISODate(...)                                       │   │
│  │     })                                                               │   │
│  │                                                                      │   │
│  │  3. Update conversation context in Redis (sliding window)            │   │
│  │                                                                      │   │
│  │  4. Return API response                                              │   │
│  └────────────────────────────────┬────────────────────────────────────┘   │
│                                   │                                         │
│                                   ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        API RESPONSE                                  │   │
│  │                                                                      │   │
│  │  Response (200 OK):                                                  │   │
│  │  {                                                                   │   │
│  │    "conversation_id": "conv_abc123",                                 │   │
│  │    "message_id": "msg_xyz789",                                       │   │
│  │    "answer": "Kevin from Arizona called about a leaking flat roof...",│  │
│  │    "sources": [                                                      │   │
│  │      {                                                               │   │
│  │        "type": "call_summary",                                       │   │
│  │        "call_id": "5002",                                            │   │
│  │        "date": "2026-01-08",                                         │   │
│  │        "confidence": 0.95,                                           │   │
│  │        "url": "/api/v1/call-processing/summary/5002"                 │   │
│  │      }                                                               │   │
│  │    ],                                                                │   │
│  │    "customer_context": {                                             │   │
│  │      "customer_id": "cust_123",                                      │   │
│  │      "name": "Kevin",                                                │   │
│  │      "phone": "+14805551234"                                         │   │
│  │    },                                                                │   │
│  │    "suggested_follow_ups": [                                         │   │
│  │      "What objections did Kevin raise?",                             │   │
│  │      "Did Kevin book an appointment?",                               │   │
│  │      "What was Kevin's qualification status?"                        │   │
│  │    ],                                                                │   │
│  │    "created_at": "2026-01-08T10:30:25Z",                             │   │
│  │    "tokens_used": 850                                                │   │
│  │  }                                                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Create Conversation

**Endpoint:** `POST /api/v1/ask-otto/conversations`

**Description:** Create a new conversation session.

**Request Headers:**
```http
X-API-Key: {api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "company_id": "acme_roofing",
  "user_id": "user_123",
  "metadata": {
    "source": "dashboard",
    "user_name": "Manager John",
    "department": "sales"
  }
}
```

**Response (201 Created):**
```json
{
  "conversation_id": "conv_abc123def456",
  "company_id": "acme_roofing",
  "user_id": "user_123",
  "created_at": "2026-01-08T10:30:00Z",
  "message_count": 0,
  "expires_at": "2026-01-09T10:30:00Z"
}
```

---

### 2. Send Message

**Endpoint:** `POST /api/v1/ask-otto/conversations/{conversation_id}/messages`

**Description:** Send a message to Ask Otto and receive an AI-generated response.

**Request Headers:**
```http
X-API-Key: {api_key}
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "What did Kevin from Arizona say about the roof leak timeline?",
  "context": {
    "include_customer_context": true,
    "include_call_history": true,
    "max_rag_results": 5,
    "search_filters": {
      "date_range": {
        "start": "2026-01-01",
        "end": "2026-01-08"
      },
      "qualification_status": ["warm", "hot"]
    }
  },
  "options": {
    "stream": false,
    "include_sources": true,
    "suggest_follow_ups": true
  }
}
```

**Response (200 OK):**
```json
{
  "conversation_id": "conv_abc123def456",
  "message_id": "msg_xyz789abc123",
  "answer": "Kevin from Arizona called about a leaking flat roof over his patio (Call #5002). The roof was built in 2006 and had solar panels installed, but the leak is not related to the solar installation. Kevin was concerned about the 7-9 week timeline for repairs. Travis, the customer rep, informed him that this was the soonest they could complete the repair due to high volume. Travis suggested Kevin consider hiring a local roofing handyman if he needed the issue resolved sooner.",
  "sources": [
    {
      "type": "call_summary",
      "call_id": "5002",
      "date": "2026-01-08T10:15:00Z",
      "confidence": 0.95,
      "excerpt": "Kevin called about leaking flat roof...",
      "url": "/api/v1/call-processing/summary/5002"
    },
    {
      "type": "chunk_summary",
      "chunk_id": "c_5002_2",
      "call_id": "5002",
      "confidence": 0.88,
      "excerpt": "7-9 week timeline discussion...",
      "url": "/api/v1/call-processing/chunks/5002"
    }
  ],
  "customer_context": {
    "customer_id": "cust_123",
    "name": "Kevin",
    "phone": "+14805551234",
    "location": "Arizona",
    "qualification_status": "warm",
    "total_calls": 5,
    "last_call_date": "2026-01-08"
  },
  "suggested_follow_ups": [
    "What objections did Kevin raise?",
    "Did Kevin book an appointment?",
    "What was Kevin's qualification status?",
    "Has Travis followed up with Kevin?"
  ],
  "metadata": {
    "tokens_used": 850,
    "response_time_ms": 1250,
    "rag_results_count": 2,
    "customer_context_found": true
  },
  "created_at": "2026-01-08T10:30:25Z"
}
```

---

### 3. Get Conversation History

**Endpoint:** `GET /api/v1/ask-otto/conversations/{conversation_id}/messages`

**Description:** Retrieve conversation message history.

**Request Headers:**
```http
X-API-Key: {api_key}
```

**Query Parameters:**
- `limit` (optional): Maximum messages to return (default 50, max 200)
- `before` (optional): Return messages before this message_id (pagination)

**Response (200 OK):**
```json
{
  "conversation_id": "conv_abc123def456",
  "messages": [
    {
      "message_id": "msg_001",
      "role": "user",
      "content": "What calls did we have this week?",
      "created_at": "2026-01-08T10:25:00Z"
    },
    {
      "message_id": "msg_002",
      "role": "assistant",
      "content": "This week, you had 145 total calls...",
      "sources": [...],
      "created_at": "2026-01-08T10:25:15Z"
    },
    {
      "message_id": "msg_003",
      "role": "user",
      "content": "What did Kevin from Arizona say about the roof leak timeline?",
      "created_at": "2026-01-08T10:30:20Z"
    },
    {
      "message_id": "msg_004",
      "role": "assistant",
      "content": "Kevin from Arizona called about a leaking flat roof...",
      "sources": [...],
      "created_at": "2026-01-08T10:30:25Z"
    }
  ],
  "total_messages": 4,
  "has_more": false
}
```

---

### 4. Delete Conversation

**Endpoint:** `DELETE /api/v1/ask-otto/conversations/{conversation_id}`

**Description:** Delete a conversation and all its messages.

**Request Headers:**
```http
X-API-Key: {api_key}
```

**Response (204 No Content)**

---

### 5. Get Conversation Details

**Endpoint:** `GET /api/v1/ask-otto/conversations/{conversation_id}`

**Description:** Get conversation metadata without messages.

**Response (200 OK):**
```json
{
  "conversation_id": "conv_abc123def456",
  "company_id": "acme_roofing",
  "user_id": "user_123",
  "created_at": "2026-01-08T10:30:00Z",
  "updated_at": "2026-01-08T10:35:00Z",
  "message_count": 4,
  "expires_at": "2026-01-09T10:30:00Z",
  "metadata": {
    "source": "dashboard",
    "user_name": "Manager John"
  }
}
```

---

## MongoDB Collections

### Collection: `ask_otto_conversations`

```javascript
{
  _id: ObjectId("..."),
  conversation_id: "conv_abc123def456",
  company_id: "acme_roofing",
  user_id: "user_123",
  created_at: ISODate("2026-01-08T10:30:00Z"),
  updated_at: ISODate("2026-01-08T10:35:00Z"),
  expires_at: ISODate("2026-01-09T10:30:00Z"),
  message_count: 4,
  metadata: {
    source: "dashboard",
    user_name: "Manager John",
    department: "sales"
  }
}
```

**Indexes:**
- `conversation_id` (unique)
- `{company_id: 1, user_id: 1, created_at: -1}`
- `expires_at` (TTL index, auto-delete after expiry)

---

### Collection: `ask_otto_messages`

```javascript
{
  _id: ObjectId("..."),
  message_id: "msg_xyz789abc123",
  conversation_id: "conv_abc123def456",
  role: "assistant",  // "user" | "assistant"
  content: "Kevin from Arizona called about a leaking flat roof...",
  sources: [
    {
      type: "call_summary",
      call_id: "5002",
      confidence: 0.95,
      url: "/api/v1/call-processing/summary/5002"
    }
  ],
  customer_context: {
    customer_id: "cust_123",
    name: "Kevin",
    phone: "+14805551234"
  },
  metadata: {
    tokens_used: 850,
    response_time_ms: 1250,
    rag_results_count: 2
  },
  created_at: ISODate("2026-01-08T10:30:25Z")
}
```

**Indexes:**
- `message_id` (unique)
- `{conversation_id: 1, created_at: 1}`
- `{conversation_id: 1, role: 1}`

---

## Redis Cache Structure

### Dual-Write Caching Pattern

The implementation uses a **dual-write pattern** for high availability:

```
┌─────────────┐      ┌─────────────┐
│  Write      │ ───► │  MongoDB    │ (Source of truth)
│  Operation  │      └─────────────┘
│             │      ┌─────────────┐
│             │ ───► │   Redis     │ (Cache)
└─────────────┘      └─────────────┘

┌─────────────┐      ┌─────────────┐
│  Read       │ ───► │   Redis     │ (Cache hit)
│  Operation  │      └──────┬──────┘
│             │             │ miss
│             │      ┌──────▼──────┐
│             │      │  MongoDB    │ ──► Repopulate cache
└─────────────┘      └─────────────┘
```

### Conversation Cache

```
Key: ask_otto:conversation:{conversation_id}
Value: {
  "conversation_id": "conv_abc123",
  "company_id": "acme_roofing",
  "user_id": "user_123",
  "created_at": "2026-01-08T10:30:00Z",
  "message_count": 4
}
TTL: 3600 seconds (1 hour)
```

### Conversation History Cache

```
Key: ask_otto:history:{conversation_id}
Value: [
  {"role": "user", "content": "..."},
  {"role": "assistant", "content": "..."},
  ...  // Last 10 messages (sliding window)
]
TTL: 300 seconds (5 minutes)
```

### Embedding Cache

```
Key: embedding:{model_name}:{md5_hash}
Value: [0.123, 0.456, ...]  // 384-dimension vector
TTL: 3600 seconds (1 hour)
```

### Cache Invalidation

- **Conversation cache**: Invalidated on message add (deleted, rebuilt on next read)
- **History cache**: Appended on new messages, keeps last 10
- **Embedding cache**: No invalidation (content-addressable)

---

## Orchestration Implementation

### Dual-Source Pipeline (LangGraphService)

The implementation uses a **13-intent classification pipeline with dual-source data routing** to PostgreSQL (analytics) and MongoDB (coaching/insights), plus Milvus RAG for knowledge queries:

```python
# app/services/ask_otto/langgraph_service.py

# Intent categories that route to PostgreSQL analytics
ANALYTICS_INTENTS = {
    "rep_performance", "booking_trends", "objection_analysis",
    "lead_pipeline", "pending_actions", "call_search",
    "appointment_stats", "call_outcomes",
}

# Intent categories that route to MongoDB insights
MONGO_INTENTS = {
    "coaching_history", "weekly_performance",
    "objection_analysis",   # dual-source: PG + Mongo
    "customer_lookup",       # existing customer + Mongo enrichment
}


class LangGraphService:
    """
    Orchestration service for Ask Otto with 13-intent classification
    and dual-source data routing (PostgreSQL + MongoDB).

    Pipeline:
    1. Classify query → intent + entities (LLM)
    2a. Route to PostgreSQL analytics (for data-driven intents)
    2b. Route to MongoDB insights (for coaching/performance intents)
    2c. RAG search via Milvus (for SOP/knowledge queries)
    2d. SOP metrics lookup (conditional)
    2e. Customer context lookup (conditional)
    2f. Cross-source enrichments (coaching, Milvus history, tenant context)
    3. Synthesize response with data-aware formatting (LLM)
    4. Extract sources
    5. Generate intent-specific follow-ups
    """

    def __init__(self):
        self.rag_service = get_rag_search_service()
        self.customer_service = get_customer_context_service()
        self.analytics_service = get_analytics_data_service()  # PostgreSQL
        self.model = get_active_model()
        self.client = get_llm_client()
```

### 13 Intent Categories

| Intent | Data Source | Description |
|--------|------------|-------------|
| `rep_performance` | PostgreSQL | Rep leaderboards, individual rep stats |
| `booking_trends` | PostgreSQL | Booking rate over time, week-over-week |
| `objection_analysis` | PostgreSQL + MongoDB | Objection counts + coaching enrichment |
| `lead_pipeline` | PostgreSQL | Lead status, deal pipeline |
| `pending_actions` | PostgreSQL | Follow-ups, action items, overdue tasks |
| `call_search` | PostgreSQL | Search calls by criteria (rep, date, outcome) |
| `appointment_stats` | PostgreSQL | Appointment confirmation rates |
| `call_outcomes` | PostgreSQL | Call outcome distribution |
| `coaching_history` | MongoDB | Coaching sessions, coach effectiveness |
| `weekly_performance` | MongoDB | Weekly insights, trending metrics |
| `customer_lookup` | MongoDB + Milvus | Customer info with call history enrichment |
| `sop_guidance` | Milvus RAG | SOP content, procedures, metrics |
| `general` | Milvus RAG | General knowledge queries |

### Data Source Services

| Service | Source | Purpose |
|---------|--------|---------|
| `AnalyticsDataService` | PostgreSQL | Pre-built parameterized SQL queries for rep stats, bookings, leads, appointments |
| `MongoInsightsService` | MongoDB | Coaching sessions, coach effectiveness, weekly insights, customer insights |
| `RAGSearchService` | Milvus | Semantic search across call summaries, chunk summaries, SOP documents |
| `CustomerContextService` | MongoDB | Fuzzy customer lookup by name/phone/location |

### SOP Query Detection

```python
def _is_sop_related_query(self, message: str, intent: str) -> bool:
    """
    Keyword-based detection for SOP-related queries.
    Also triggered when intent is 'sop_guidance'.
    """
    if intent == "sop_guidance":
        return True
    sop_keywords = [
        "sop", "procedure", "guideline", "protocol", "process",
        "how should", "what should", "best practice", "standard",
        "metric", "evaluation", "compliance", "performance"
    ]
    message_lower = message.lower()
    return any(kw in message_lower for kw in sop_keywords)
```

---

## Cross-Source Enrichment (v4.1)

After the primary data gathering (RAG search, customer context, analytics), Ask Otto conditionally enriches the context with supplementary data from other sources based on the detected intent. Each enrichment is independently guarded with try/except and only adds context when data exists.

### Enrichment Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CROSS-SOURCE ENRICHMENT (Step 2f)                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Intent: rep_performance + entities.rep_name                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6A: COACHING CROSS-ENRICHMENT                                      │   │
│  │  Source: MongoDB coaching_sessions (MongoInsightsService)            │   │
│  │  Query:  get_coaching_sessions(company_id, rep_name, limit=3)       │   │
│  │  → context["coaching_enrichment"]                                   │   │
│  │  Impact: Rep performance queries now include coaching session data   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Intent: customer_lookup + entities.phone_number                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6B: CUSTOMER MILVUS CALL HISTORY                                   │   │
│  │  Source: Milvus call_summary corpus (RAGService)                    │   │
│  │  Query:  rag.search("customer calls {name}", corpus=[CALL_SUMMARY]) │   │
│  │  → context["customer_call_history"]                                 │   │
│  │  Impact: Customer lookups now include past call summary context     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  Intent: objection_analysis                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6C: OBJECTION CALL EXAMPLES                                        │   │
│  │  Source: Milvus call_summary + chunk_summary (RAGService)           │   │
│  │  Query:  rag.search("objection handling {topic}",                   │   │
│  │          corpus=[CALL_SUMMARY, CHUNK_SUMMARY], limit=3)             │   │
│  │  → context["objection_call_examples"]                               │   │
│  │  Impact: Objection queries cite specific call handling examples     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  All intents (unconditional)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  6D: TENANT CONTEXT                                                 │   │
│  │  Source: MongoDB tenant_configurations (TenantConfigService, 5min)  │   │
│  │  Query:  tenant_service.get_config(company_id)                      │   │
│  │  → context["company_context"] = {service_types, company_name}       │   │
│  │  Impact: Ask Otto knows the company's service types and name        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Enrichment Summary

| ID | Enrichment | Trigger | Data Source | Token Impact |
|----|------------|---------|-------------|--------------|
| 6A | Coaching cross-enrichment | `intent == "rep_performance"` AND `rep_name` present | MongoDB `coaching_sessions` | ~200-500 tokens |
| 6B | Customer Milvus history | `intent == "customer_lookup"` AND `phone_number` present | Milvus `call_summary` | ~300-800 tokens |
| 6C | Objection call examples | `intent == "objection_analysis"` | Milvus `call_summary` + `chunk_summary` | ~300-800 tokens |
| 6D | Tenant company context | Always (when tenant config exists) | MongoDB `tenant_configurations` (cached 5min) | ~50-100 tokens |

### Synthesis Integration

The cross-enrichment data is rendered into the response synthesis prompt:

```
--- REP COACHING HISTORY ---         (if coaching_enrichment present)
[JSON: recent coaching sessions for this rep]

--- PAST CALL SUMMARIES ---          (if customer_call_history present)
1. [Call {doc_id}] {text_content[:400]}

--- SPECIFIC CALL EXAMPLES ---       (if objection_call_examples present)
1. [Call {doc_id}] {text_content[:400]}

--- COMPANY INFO ---                 (if company_context present)
Company: {company_name}
Services: {service_types}
```

---

## RAG Search Strategy

### Multi-Corpus Search

```python
def multi_source_rag_search(query: str, company_id: str, max_results: int = 5):
    """
    Search across multiple corpus types with priority weighting.
    """
    # Generate embedding using local HuggingFace Sentence Transformers
    embedding = embedding_service.get_embedding(query)  # Local model, fast
    
    # Search Milvus with corpus type priority
    results = []
    
    # Priority 1: Call summaries (highest relevance)
    call_summaries = milvus.search(
        collection_name="otto_intelligence_v1",
        data=[embedding],
        filter=f"tenant_id == '{company_id}' && corpus_type == 'call_summary'",
        limit=3,
        output_fields=["doc_id", "text_content", "summary_json", "customer_phone"]
    )
    results.extend([(r, "call_summary", r.score) for r in call_summaries[0]])
    
    # Priority 2: Chunk summaries
    chunk_summaries = milvus.search(
        collection_name="otto_intelligence_v1",
        data=[embedding],
        filter=f"tenant_id == '{company_id}' && corpus_type == 'chunk_summary'",
        limit=2,
        output_fields=["doc_id", "chunk_id", "text_content", "summary_json"]
    )
    results.extend([(r, "chunk_summary", r.score) for r in chunk_summaries[0]])
    
    # Priority 3: FAQ documents
    faq_docs = milvus.search(
        collection_name="otto_intelligence_v1",
        data=[embedding],
        filter=f"tenant_id == '{company_id}' && corpus_type == 'faq'",
        limit=1,
        output_fields=["doc_id", "text_content"]
    )
    results.extend([(r, "faq", r.score) for r in faq_docs[0]])
    
    # Sort by score and return top K
    results.sort(key=lambda x: x[2], reverse=True)
    return results[:max_results]
```

---

## Customer Context Resolution

### Fuzzy Matching Algorithm

```python
def resolve_customer_by_name_and_location(
    name: str,
    location: Optional[str],
    company_id: str
) -> Optional[Dict]:
    """
    Resolve customer using fuzzy name matching + location hints.
    """
    # Check Redis cache first
    cache_key = f"customer_fuzzy:{company_id}:{name}:{location}"
    cached = redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # MongoDB query with text search + location filter
    query = {
        "company_id": company_id,
        "$text": {"$search": name}
    }
    
    if location:
        query["$or"] = [
            {"address": {"$regex": location, "$options": "i"}},
            {"state": location},
            {"city": location}
        ]
    
    # Find best match
    customers = db.customers.find(query).limit(5)
    
    if not customers:
        return None
    
    # Rank by text score + location match
    best_match = max(
        customers,
        key=lambda c: fuzzy_score(c["name"], name) +
                     (0.3 if location_matches(c, location) else 0)
    )
    
    # Cache result
    redis.setex(cache_key, 300, json.dumps(best_match))
    
    return best_match
```

---

## Performance Optimizations

### 1. Intent-Based Data Routing
- Only queries relevant data sources based on classified intent (not all sources for every query)
- PostgreSQL analytics only queried for data-driven intents, MongoDB only for coaching/insight intents

### 2. Conversation Context Caching
- Cache last 10 messages in Redis (30-minute TTL)
- Avoid MongoDB query on every request
- Invalidate on new message

### 3. RAG Query Caching
- Cache semantic search results by query hash
- 5-minute TTL (balance freshness vs speed)
- Invalidate on new call processing

### 4. Customer Context Caching
- Cache customer lookups by phone (5-minute TTL)
- Pre-warm cache for active customers
- Background refresh for frequently accessed customers

### 5. Embedding Caching
- Cache embeddings for common queries
- Reuse embeddings across similar queries
- Store in Redis with 1-hour TTL

---

## Success Metrics

| Metric | Target | Monitoring |
|--------|--------|------------|
| Response time (p95) | < 3s | HTTP middleware timer |
| RAG search latency | < 300ms | Milvus client timer |
| Customer context resolution | < 200ms | Service-level timer |
| Context cache hit rate | > 70% | Redis cache stats |
| Answer relevance score | > 0.85 | User feedback / LLM eval |
| Source citation accuracy | > 90% | Manual audit sample |

---

## CRM Placeholder Design

### Future Integration Interface

```python
class CRMIntegrationService:
    """
    Placeholder for future CRM integrations.
    
    Supported CRMs (planned):
    - Salesforce
    - HubSpot
    - Pipedrive
    - Custom CRM via webhook
    """
    
    async def get_customer_by_phone(
        self,
        phone: str,
        company_id: str
    ) -> Optional[Dict]:
        """
        Fetch customer from external CRM.
        
        Returns:
            {
                "crm_id": "SF_123456",
                "name": "Kevin",
                "email": "kevin@example.com",
                "status": "warm",
                "owner": "sales_rep_id",
                "last_activity": "2026-01-08",
                "custom_fields": {...}
            }
        """
        raise NotImplementedError("CRM integration not yet implemented")
    
    async def sync_call_summary(
        self,
        call_id: str,
        crm_customer_id: str,
        summary: Dict
    ) -> bool:
        """
        Push call summary to CRM as activity/note.
        """
        raise NotImplementedError("CRM integration not yet implemented")
```

### Configuration

```python
# Environment variables for CRM
CRM_PROVIDER = "none"  # "salesforce" | "hubspot" | "pipedrive" | "webhook" | "none"
CRM_API_KEY = ""
CRM_API_URL = ""
CRM_WEBHOOK_SECRET = ""
```

---

## Summary (v5.1)

### Architecture Highlights

| Component | Implementation |
|-----------|---------------|
| **Orchestration** | 13-intent classification with dual-source data routing |
| **Analytics Data** | PostgreSQL via `AnalyticsDataService` (optional, graceful fallback) |
| **Insights Data** | MongoDB via `MongoInsightsService` (coaching, weekly insights) |
| **RAG Search** | Multi-corpus (calls, chunks, SOP documents) via Milvus |
| **Cross-Source Enrichment** | Intent-specific data from MongoDB coaching, Milvus call history, tenant config |
| **LLM** | GROQ llama-3.3-70b-versatile (multi-provider) |
| **Embeddings** | Local HuggingFace (cached in Redis) |
| **Storage** | MongoDB (truth) + Redis (cache) dual-write |
| **Caching** | Conversation 1h, history 5min, embeddings 1h, tenant config 5min |

### Key Differences from Original Documentation

1. **Dual-Source Routing**: Routes to PostgreSQL (analytics) or MongoDB (coaching/insights) based on 13-intent classification
2. **13 Intent Categories**: rep_performance, booking_trends, objection_analysis, lead_pipeline, pending_actions, call_search, appointment_stats, call_outcomes, coaching_history, weekly_performance, customer_lookup, sop_guidance, general
3. **PostgreSQL Analytics**: New `AnalyticsDataService` with parameterized SQL queries for rep stats, bookings, leads, appointments
4. **MongoDB Insights**: New `MongoInsightsService` for coaching sessions, coach effectiveness, weekly insights
5. **SOP Integration**: Full SOP document/metric/criteria search
6. **Cross-Source Enrichment**: Intent-specific supplementary data (coaching for rep queries, Milvus for customer/objection queries, tenant context for all)
7. **Dual-Write Pattern**: MongoDB + Redis simultaneously
8. **Response Metadata**: Tracks response_time_ms, rag_results_count
9. **Follow-ups**: Rule-based, intent-specific (not LLM-based)
10. **24-hour Expiry**: Conversations auto-expire

### File Structure

```
app/
├── api/v1/
│   └── ask_otto.py                    # API endpoints (5 endpoints)
│
├── services/ask_otto/
│   ├── __init__.py
│   ├── conversation_service.py        # Conversation + message storage
│   ├── customer_context_service.py    # Customer lookup + history
│   ├── langgraph_service.py           # Sequential pipeline orchestration + cross-source enrichment
│   ├── analytics_data_service.py      # PostgreSQL analytics data access
│   ├── mongodb_insights_service.py    # MongoDB insights + coaching session access
│   ├── rag_search_service.py          # Multi-corpus RAG wrapper
│   └── graph/
│       └── __init__.py                # (Placeholder, not used)
│
├── models/
│   └── conversation.py                # MongoDB models
│
└── schemas/
    └── ask_otto.py                    # Pydantic request/response
```

---

**Next:** [Feature 4: SOP Document Ingestion](./ARCHITECTURE_FEATURE_4_DOCUMENT_INGESTION.md)