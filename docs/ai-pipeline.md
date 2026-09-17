# AI Pipeline — Design Document

## Overview

The AI pipeline is the core processing engine. It transforms raw audio/screen input into validated, interview-ready answers. Every stage is async, observable, and designed for streaming.

## Pipeline Architecture

```
Input Stream (Audio + Screen)
    │
    ▼
┌─────────────────┐
│  InputProcessor  │ ← VAD, frame sampling, OCR
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ QuestionDetector │ ← Rolling window, boundary detection
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ QuestionClassifier   │ ← Structured output, category + metadata
└────────┬─────────────┘
         │
         ▼
┌──────────────────┐
│   ModelRouter    │ ← Simple/Complex/Coding classification
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│  RAG   │ │Memory  │ ← Parallel retrieval + context assembly
└───┬────┘ └───┬────┘
    └────┬─────┘
         ▼
┌─────────────────┐
│  EngineSelector  │ ← Route to specialized engine
└────────┬────────┘
         │
    ┌────┼────┬────────┐
    ▼    ▼    ▼        ▼
┌──────┐┌──────┐┌──────┐┌──────┐
│ Tech ││Scenar││Coding││Behav │
└──┬───┘└──┬───┘└──┬───┘└──┬───┘
   └───────┴───────┴───────┘
              │
              ▼
      ┌───────────────┐
      │  Validator    │ ← Factuality, consistency, resume match
      └───────┬───────┘
              │
              ▼
      ┌───────────────┐
      │   Composer    │ ← Mode-dependent formatting
      └───────┬───────┘
              │
              ▼
      Stream to Client
```

## Stage Details

### 1. InputProcessor
- Receives raw audio chunks (PCM 16kHz mono)
- Voice Activity Detection to identify speech segments
- Optional: receives screen frames, applies change detection, OCR
- Emits: speech segments, screen context

### 2. QuestionDetector
- Maintains rolling window of recent transcript
- Detects question boundaries via:
  - Explicit question markers ("what", "how", "can you", "tell me about")
  - Pause-based segmentation (>1.5s silence after statement)
  - Interviewer voice identification (when available)
  - Syntactic completeness detection
- Emits: question_text, is_complete, confidence

### 3. QuestionClassifier
- Uses structured output (JSON schema) with LLM
- Classifies: category, technology, difficulty, routing hints
- Categories: technical, coding, debugging, system_design, architecture, scenario, behavioral, project, resume, SQL, follow_up, clarification, unknown
- Emits: classification with confidence scores

### 4. ModelRouter
- Analyzes classification to select appropriate model
- Simple factual → fast model (gpt-4.1-nano)
- Complex reasoning/scenario → reasoning model (gpt-4.1)
- Coding → reasoning model + sandbox validation
- Cost-aware: doesn't use expensive model unnecessarily
- Emits: selected_model, routing_reason

### 5. RAG Pipeline (parallel with Memory)
- Query normalization
- Metadata filtering (technology, document, project, source)
- BM25 lexical retrieval
- Vector semantic retrieval (pgvector)
- Reciprocal Rank Fusion
- Cross-encoder reranking
- Budget-aware context selection (token budget)
- Emits: ranked_chunks with scores and sources

### 6. ConversationMemory
- L1: Current question context
- L2: Rolling conversation summary (last N turns)
- L3: User profile + knowledge base facts
- Token budget management via rolling summaries
- Emits: conversation_context

### 7. EngineSelector + Engines
- Routes to: TechnicalEngine, ScenarioEngine, CodingEngine, BehavioralEngine
- Each engine has specialized prompt templates
- Each engine produces structured output
- Engines receive: question, classification, context (RAG + memory), mode

### 8. Validator
- Factual consistency (answer vs retrieved context)
- Resume consistency (claims vs user profile)
- Conversation consistency (no contradictions with prior answers)
- Unsupported claim detection
- Confidence scoring
- Emits: validation_result, qualified_claims, warnings

### 9. Composer
- Formats answer based on mode:
  - Quick: Direct answer, 1-2 sentences
  - Interview: Direct + explanation + example
  - Senior: Architecture/trade-offs/production considerations
  - Coding: Approach + code + complexity + edge cases
  - Scenario: Situation + investigation + solution + prevention
- Adds source citations when available
- Emits: formatted answer (streamed token by token)
