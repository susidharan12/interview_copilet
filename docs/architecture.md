# Interview Copilot — System Architecture

## Overview

A production-quality desktop AI interview copilot built as a modular, observable, streaming-first system. The application processes interviews in real-time: capturing audio and screen content, detecting questions, retrieving relevant knowledge, and streaming concise answers — all without blocking the UI.

## High-Level Architecture

```
                    INTERVIEW AI DESKTOP APP
                    ┌─────────────────────┐
                    │   Tauri (Rust) Shell │
                    │  ┌─────────────────┐ │
                    │  │ React + TS UI   │ │
                    │  │ Zustand State   │ │
                    │  │ WebSocket Client│ │
                    │  └────────┬────────┘ │
                    │  Capture: │ Mic/Screen│
                    └───────────┼───────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │    FastAPI Backend   │
                    │    (Python + ASGI)   │
                    ├─────────────────────┤
                    │  REST + WebSocket    │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
          ┌────────────┐ ┌──────────┐ ┌──────────┐
          │ PostgreSQL │ │  Redis   │ │  Docker  │
          │ + pgvector │ │ (cache/  │ │ Sandbox  │
          │            │ │  queue)  │ │          │
          └────────────┘ └──────────┘ └──────────┘
```

## Service Architecture

```
                    Interview Pipeline
                         │
                   ┌─────┴─────┐
                   │   Router  │
                   └─────┬─────┘
                         │
       ┌─────────────────┼─────────────────┐
       │                 │                 │
       ▼                 ▼                 ▼
    Knowledge         Reasoning          Coding
     Engine             Engine           Engine
       │                 │                 │
       ▼                 ▼                 ▼
     RAG              Scenario          Sandbox
     │                  │                 │
     └─────────────────┼─────────────────┘
                       ▼
                 Validation
                       │
                       ▼
                Answer Composer
                       │
                       ▼
                  Stream to UI
```

## Processing Pipeline

```
Audio/Screen Input
  → Input Processing (VAD, OCR, frame sampling)
    → Question Detection (segmentation + boundary)
      → Question Classification (structured output)
        → Context Retrieval (hybrid BM25 + vector + RRF + rerank)
          → Model Routing (simple vs complex)
            → Engine Selection (technical/scenario/coding/behavioral)
              → Reasoning + Generation
                → Validation (factuality, consistency, resume match)
                  → Answer Composition (mode-dependent)
                    → WebSocket Streaming to UI
```

## Core Design Principles

1. **Never block UI** — All processing is async; UI stays responsive
2. **Streaming-first** — Partial results stream immediately via WebSocket
3. **Modular services** — Each engine is independent, testable, replaceable
4. **Observable** — Every pipeline step emits metrics/traces
5. **Fail-safe** — Graceful degradation; unknown answers over hallucination
6. **Context-aware** — Rolling conversation memory across L1/L2/L3 levels

## Technology Layers

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Desktop Shell | Tauri + Rust | Native capture, shortcuts, overlay |
| UI | React + TypeScript + Zustand | Real-time interface |
| API | FastAPI + WebSocket | REST endpoints + streaming |
| Pipeline | Python async services | Orchestration + AI |
| Database | PostgreSQL + pgvector | Persistent storage + vectors |
| Cache | Redis | Session state + caching |
| Sandbox | Docker containers | Code execution isolation |
| AI | OpenAI APIs | Transcription, LLM, embeddings |
| Observability | OpenTelemetry | Metrics + tracing |

## Module Boundaries

```
backend/app/
├── core/           # Infrastructure: config, security, DB, Redis, telemetry
├── models/         # SQLAlchemy ORM models
├── schemas/        # Pydantic request/response schemas
├── api/            # FastAPI routes + dependency injection
├── services/
│   ├── pipeline.py          # InterviewPipeline orchestrator
│   ├── transcription/       # VAD, streaming ASR (OpenAI realtime)
│   ├── detection.py         # Question boundary detection
│   ├── classification.py    # Question classification (structured output)
│   ├── retrieval/           # Hybrid RAG: BM25 + vector + RRF + rerank
│   ├── memory.py            # Conversation memory (L1/L2/L3)
│   ├── router.py            # Model routing logic
│   ├── validation.py        # Answer validation + factuality check
│   ├── composer.py          # Answer composition per mode
│   ├── knowledge.py         # Document ingestion + user profile
│   └── engines/             # Specialized answer engines
│       ├── technical.py
│       ├── scenario.py
│       ├── coding.py
│       └── behavioral.py
├── workers/        # Background tasks (ingestion, indexing)
└── eval/           # Evaluation harness + datasets
```

## Data Flow Summary

1. **Ingestion (offline):** User uploads resume, projects, notes → chunk → embed → store in pgvector
2. **Capture (realtime):** Tauri captures mic audio + optional screen frames → sends over WebSocket
3. **Transcription:** Backend streams audio to OpenAI → returns partial/final transcripts
4. **Detection:** Rolling window analysis identifies question boundaries
5. **Classification:** Structured output determines category, technology, difficulty, routing needs
6. **Retrieval:** Parallel BM25 + vector search → RRF fusion → reranking → context selection
7. **Routing:** Simple questions → fast model; complex → reasoning model; coding → reasoning + sandbox
8. **Engine:** Specialized engine produces answer based on category
9. **Validation:** Cross-check against retrieved context, resume, conversation history
10. **Composition:** Format answer based on selected mode (quick/interview/senior/coding/scenario)
11. **Streaming:** WebSocket streams answer tokens to UI incrementally

## Security Model

- JWT authentication for API access
- API keys never exposed to frontend (all AI calls server-side)
- Docker sandbox isolation for code execution
- Data retention policies for audio/transcripts
- Tenant isolation via user_id scoping on all queries
- Rate limiting per user/session
