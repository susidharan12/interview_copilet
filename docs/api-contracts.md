# API Contracts

## Authentication

All endpoints require `Authorization: Bearer {jwt_token}` except health check.

## Sessions

### POST /sessions
Create a new interview session.

**Request:**
```json
{
  "job_profile_id": "uuid",
  "mode": "interview",
  "settings": {
    "enable_screen_capture": false,
    "answer_mode": "interview",
    "language": "en"
  }
}
```

**Response 201:**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "job_profile_id": "uuid",
  "status": "active",
  "mode": "interview",
  "settings": {...},
  "created_at": "ISO8601"
}
```

### GET /sessions/{id}
**Response 200:** Full session object with turns summary.

### PATCH /sessions/{id}
Update session status/settings.

---

## Documents

### POST /documents
Upload a document.

**Request (multipart/form-data):**
- `file`: Binary file (pdf, md, txt, docx, json)
- `document_type`: resume | project | notes | technical | other
- `tags`: comma-separated technology tags
- `project_name`: optional project association

**Response 201:**
```json
{
  "id": "uuid",
  "filename": "resume.pdf",
  "document_type": "resume",
  "status": "processing",
  "chunk_count": 0,
  "created_at": "ISO8601"
}
```

### POST /documents/ingest
Trigger ingestion pipeline for a document.

---

## Search

### POST /search
Hybrid search across user's knowledge base.

**Request:**
```json
{
  "query": "How did you implement caching in Project X?",
  "filters": {
    "technology": ["redis", "python"],
    "document_type": ["project", "technical"],
    "project": "project-x"
  },
  "top_k": 10
}
```

**Response 200:**
```json
{
  "results": [
    {
      "chunk_id": "uuid",
      "content": "...",
      "score": 0.92,
      "source": {
        "document_id": "uuid",
        "filename": "architecture.md",
        "section": "caching"
      },
      "metadata": {
        "technology": ["redis", "python"],
        "project": "project-x"
      }
    }
  ],
  "query_id": "uuid",
  "latency_ms": 340
}
```

---

## Classification

### POST /questions/classify
**Request:**
```json
{
  "question_text": "How would you design a rate limiter for a distributed system?",
  "context": {
    "previous_questions": [],
    "technologies_discussed": []
  }
}
```

**Response 200:**
```json
{
  "category": "system_design",
  "technology": "distributed-systems",
  "difficulty": "hard",
  "requires_retrieval": true,
  "requires_reasoning": true,
  "requires_code_execution": false,
  "requires_screen_context": false,
  "confidence": 0.95
}
```

---

## Answers

### POST /answers/generate
**Request:**
```json
{
  "session_id": "uuid",
  "question_id": "uuid",
  "question_text": "Explain the CAP theorem",
  "classification": { ... },
  "mode": "interview",
  "stream": true
}
```

**Response 200 (streaming):**
Server-Sent Events or WebSocket with `answer.delta` / `answer.done`.

---

## Coding

### POST /code/execute
**Request:**
```json
{
  "language": "python",
  "code": "def two_sum(nums, target): ...",
  "test_cases": [
    {"input": "nums=[2,7,11,15], target=9", "expected": "[0,1]"}
  ],
  "timeout_seconds": 10
}
```

**Response 200:**
```json
{
  "execution_id": "uuid",
  "success": true,
  "exit_code": 0,
  "stdout": "5 tests passed",
  "stderr": "",
  "execution_time_ms": 1523,
  "test_results": {
    "total": 5,
    "passed": 5,
    "failed": 0
  }
}
```

---

## Feedback

### POST /feedback
**Request:**
```json
{
  "answer_id": "uuid",
  "rating": 4,
  "comment": "Good explanation but could include more examples",
  "tags": ["needs_example"]
}
```

---

## Profile

### GET /profile
**Response 200:**
```json
{
  "user_id": "uuid",
  "name": "John Doe",
  "resume_summary": "...",
  "skills": ["python", "kubernetes", ...],
  "projects": [...],
  "experience_years": 5,
  "target_role": "senior-backend"
}
```

### PUT /profile
Update profile information.

---

## Job Profile

### GET /job-profile
**Response 200:**
```json
{
  "id": "uuid",
  "company": "Tech Corp",
  "role": "Senior Backend Engineer",
  "requirements": [...],
  "technologies": [...],
  "notes": "..."
}
```

### POST /job-profile
Create/update job profile.
