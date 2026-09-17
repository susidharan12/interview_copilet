# Development Plan — Milestones & Phases

## Milestone 1: Foundation (Phase 1 — Current)

### 1.1 Architecture Documentation
- System architecture document
- Data model definitions
- API contracts
- WebSocket protocol
- AI pipeline design
- RAG pipeline design
- Sandbox architecture
- Evaluation strategy

### 1.2 Repository Structure
- Monorepo layout (backend / frontend / native / infra / docs)
- Backend Python project (pyproject.toml, alembic, app package)
- Frontend Vite + React + TypeScript project
- Native Rust/Tauri scaffold
- Infrastructure (Docker, docker-compose)
- .env.example, .gitignore

### 1.3 Database Schema (PostgreSQL + pgvector)
- users, profiles, documents, document_chunks, embeddings
- job_profiles, interview_sessions, interview_turns
- questions, answers, retrieval_traces, coding_runs
- feedback, settings
- Proper indexes, foreign keys, pgvector columns

### 1.4 Backend Skeleton
- FastAPI application with lifespan management
- Config via pydantic-settings
- Async SQLAlchemy + asyncpg engine
- Redis connection pool
- Alembic migration system
- Security (JWT auth, password hashing)
- Telemetry stub (OpenTelemetry)
- Pydantic schemas for all endpoints

### 1.5 API Routes (Stub Implementations)
- POST /sessions, GET /sessions/{id}, PATCH /sessions/{id}
- POST /documents, POST /documents/ingest
- POST /search
- POST /questions/classify
- POST /answers/generate
- POST /code/execute
- POST /feedback
- GET /profile, PUT /profile
- GET /job-profile, POST /job-profile
- WebSocket /ws/interview/{session_id}

### 1.6 WebSocket Infrastructure
- Connection management (auth, session binding)
- Event protocol (typed messages in both directions)
- Pipeline status streaming
- Partial answer streaming
- Error broadcasting

### 1.7 Core Services (Skeleton + Interfaces)
- InterviewPipeline orchestrator
- TranscriptionService (protocol + OpenAI + mock)
- QuestionDetector (rule-based segmentation)
- QuestionClassifier (structured output)
- RAGPipeline (hybrid retrieval with mock providers)
- ConversationMemory (L1/L2/L3 rolling context)
- ModelRouter (simple/complex routing)
- AnswerValidator
- AnswerComposer (mode-dependent formatting)
- Specialized engines (technical, scenario, coding, behavioral)

### 1.8 Frontend Skeleton
- Vite + React + TypeScript
- Zustand store (session, transcript, answer, status)
- WebSocket client with reconnection
- Core UI components (StatusBar, Transcript, Question, Answer, Sources, Coding)
- Overlay mode
- Settings panel
- Profile panel

### 1.9 Native Scaffold (Rust/Tauri)
- Tauri project structure
- Command stubs (mic, screen, shortcuts)
- Build configuration

### 1.10 Infrastructure
- docker-compose (PostgreSQL + pgvector, Redis)
- Backend Dockerfile
- Dev scripts

### 1.11 Tests
- Backend: classification, pipeline, retrieval, API
- Frontend: TypeScript compilation, build verification

---

## Milestone 2: RAG System (Phase 2)
- BM25 retrieval with proper tokenization
- Vector retrieval with pgvector
- Reciprocal Rank Fusion
- Reranking integration
- Metadata filtering
- Chunking strategies per document type
- Retrieval quality evaluation
- Retrieval trace storage

## Milestone 3: Knowledge Base (Phase 3)
- Document upload and processing
- Resume parsing and indexing
- Job description parsing
- Project documentation ingestion
- Knowledge profile management
- User/project metadata extraction
- Verified vs general vs reasoned information tagging

## Milestone 4: Conversation Memory (Phase 4)
- Rolling conversation summaries
- Topic tracking
- Follow-up question understanding
- Technology/topic extraction from conversation
- Context budget management
- Correction tracking

## Milestone 5: Question Classification (Phase 5)
- Structured output classification
- Technology detection
- Difficulty estimation
- Multi-class with confidence
- Follow-up detection
- Classification evaluation

## Milestone 6: Scenario Engine (Phase 6)
- Situation/assumption/risk analysis
- Investigation/root-cause framework
- Mitigation/solution pipeline
- Trade-off analysis
- Interview-ready formatting

## Milestone 7: Coding Engine (Phase 7)
- Code generation pipeline
- Docker sandbox execution
- Multi-language support (Java, Kotlin, Python, JS, TS, C++, SQL)
- Test case generation
- Complexity analysis
- Auto-fix loop

## Milestone 8: Screen Intelligence (Phase 8)
- Screen capture integration (Tauri)
- Frame sampling + change detection
- OCR pipeline
- Vision processing
- Relevant region extraction

## Milestone 9: Model Routing (Phase 9)
- Complexity analysis for routing decisions
- Fast vs reasoning model selection
- Cost tracking per model
- Fallback chains
- Latency-aware routing

## Milestone 10: Validation (Phase 10)
- Factual consistency checking
- Resume consistency checking
- Conversation consistency
- Unsupported claim detection
- Confidence scoring

## Milestone 11: Observability (Phase 11)
- OpenTelemetry integration
- Pipeline latency metrics
- Retrieval hit rate tracking
- Answer quality metrics
- Dashboard (Prometheus + Grafana)

## Milestone 12: Production (Phase 12)
- Security hardening
- Rate limiting
- Data retention enforcement
- Load testing
- Deployment automation
- Monitoring + alerting
- Evaluation suite execution
