# Evaluation Strategy

## Overview

Continuous evaluation of the interview copilot across retrieval quality, answer correctness, coding accuracy, and latency targets.

## Evaluation Dimensions

### 1. Retrieval Quality
- **Recall@5, @10, @20**: Are relevant chunks retrieved?
- **MRR**: Mean Reciprocal Rank
- **NDCG@10**: Normalized Discounted Cumulative Gain
- **Answer attribution rate**: % of answer claims backed by retrieval

### 2. Answer Correctness
- **Factual accuracy**: Against known-answer ground truth
- **Citation accuracy**: Are referenced sources real and relevant?
- **Resume consistency**: No fabricated project details
- **Completeness**: Does the answer address all parts of the question?

### 3. Question Classification
- **Precision/Recall/F1** per category
- **Overall accuracy**
- **Technology detection accuracy**
- **Difficulty rating correlation** (with human ratings)

### 4. Coding
- **Pass rate**: Generated code passes test cases
- **Correctness**: Output matches expected for given inputs
- **Complexity**: Matches stated time/space complexity
- **Fix rate**: How often auto-fix resolves initial errors

### 5. Latency (target)
| Metric | Target |
|--------|--------|
| Partial transcription | < 500ms |
| Question detection | < 200ms |
| Classification | < 500ms |
| First retrieval | < 1000ms |
| First token (answer) | < 2000ms |
| Full answer | < 5000ms |
| Code generation | < 10000ms |
| Code execution | < 15000ms |

### 6. Pipeline
- **End-to-end latency**: Question detected → Answer streamed
- **Pipeline success rate**: % completing without errors
- **Fallback rate**: % requiring model fallback

## Evaluation Dataset Format

```json
{
  "id": "eval-001",
  "category": "technical",
  "question": "Explain the difference between HashMap and ConcurrentHashMap in Java.",
  "expected_keywords": ["thread safety", "concurrent access", "locking", "performance"],
  "technology": "java",
  "difficulty": "medium",
  "source_context": ["doc-123", "doc-456"],
  "evaluation_criteria": {
    "must_mention": ["thread safety", "concurrent modification"],
    "should_mention": ["locking strategies", "performance trade-offs"],
    "code_example_expected": true
  }
}
```

## Automated Evaluation

```python
# Pseudo-evaluation harness
def evaluate_rag(dataset):
    for item in dataset:
        chunks = rag_pipeline.retrieve(item["question"])
        recall = compute_recall(chunks, item["source_context"])
        mrr = compute_mrr(chunks, item["source_context"])
        yield {"recall": recall, "mrr": mrr}

def evaluate_classification(dataset):
    for item in dataset:
        result = classifier.classify(item["question"])
        yield compare(result, item["expected_category"])

def evaluate_coding(dataset):
    for item in dataset:
        solution = coding_engine.generate(item["question"])
        test_results = sandbox.execute(solution, item["test_cases"])
        yield test_results
```

## Manual Evaluation

- Weekly review of 20 random Q&A pairs
- Rubric: 1-5 scale for accuracy, completeness, clarity
- Track regression across model updates
- A/B test new retrieval strategies

## Continuous Monitoring

- Prometheus metrics for all latency targets
- Grafana dashboards for pipeline health
- Alert on: latency spikes, error rate > 1%, retrieval recall drop
- Weekly automated eval run → report
