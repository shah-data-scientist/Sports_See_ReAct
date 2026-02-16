# Unified Evaluation Report - VECTOR

**Generated:** 2026-02-16 23:50:18

**Dataset:** 4 test cases

**Results JSON:** `evaluation_vector_20260216_234636.json`

---

## Executive Summary

- **Total Queries:** 4
- **Successful Executions:** 4 (100.0%)
- **Failed Executions:** 0
- **Misclassifications:** 4
- **Avg Processing Time:** 4434ms
- **Min/Max Processing Time:** 2256ms / 7312ms

### Test Type Distribution

| Type | Count | Percentage |
|------|-------|------------|
| HYBRID | 0 | 0.0% |
| SQL | 0 | 0.0% |
| UNKNOWN | 0 | 0.0% |
| VECTOR | 4 | 100.0% |

### Routing Statistics

| Routing | Count | Percentage |
|---------|-------|------------|
| greeting | 0 | 0.0% |
| hybrid | 0 | 0.0% |
| sql_only | 0 | 0.0% |
| unknown | 4 | 100.0% |
| vector_only | 0 | 0.0% |

### Misclassifications (4 queries)

| # | Question | Test Type | Expected | Actual | Response Preview |
|---|----------|-----------|----------|--------|------------------|
| 1 | What do Reddit users think about teams t... | vector | vector_only | unknown | Reddit users have been impressed by several teams in the playoffs, according to ... |
| 2 | Which NBA teams didn't have home court a... | vector | vector_only | unknown | According to Reddit user ADE, no NBA team in the modern era has made the Finals ... |
| 3 | According to basketball discussions, wha... | vector | vector_only | unknown | According to Reddit discussions, Reggie Miller is considered the most efficient ... |
| 4 | What does zone defense mean?... | vector | vector_only | unknown | I am sorry, but I don't have enough information on this topic to provide you wit... |

## Performance by Category

| Category | Count | Success Rate | Avg Time |
|----------|-------|--------------|----------|
| complex | 1 | 100.0% | 3347ms |
| simple | 3 | 100.0% | 4796ms |



================================================================================
# RAGAS METRICS ANALYSIS
================================================================================

## Overall RAGAS Metrics

| Metric | Score | Interpretation |
|--------|-------|----------------|
| Faithfulness | 0.900 | ✅ EXCELLENT |
| Answer Relevancy | 0.850 | ⚠️  GOOD |
| Answer Semantic Similarity | 0.900 | ✅ EXCELLENT |
| Answer Correctness ⭐ BEST | 0.880 | ⚠️  GOOD |
| Context Precision | 0.661 | ⚠️  WARNING |
| Context Relevancy | 0.607 | ⚠️  WARNING |

## RAGAS Metrics by Category

| Category | Count | Faithfulness | Answer Correctness | Context Precision | Context Recall |
|----------|-------|--------------|-------------------|-------------------|----------------|
| simple | 6 | 0.900 | 0.880 | 0.548 | N/A |
| complex | 6 | 0.900 | 0.880 | 1.000 | N/A |

## Low Scoring Queries (< 0.7) - Top 2

### 1. SIMPLE

**Question:** What does zone defense mean?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 2. SIMPLE

**Question:** Which NBA teams didn't have home court advantage in finals according to discussions?...

**Scores:**
- Min Score: 0.429
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.6428571428571429
- Context Recall: None


================================================================================
# RAGAS METRICS - NUCLEAR EXPLANATIONS
================================================================================

## Faithfulness

```
FAITHFULNESS (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Does the answer contradict the retrieved sources?
HOW: (Supported claims) / (Total claims)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - No hallucination detected
⚠️  0.7-0.9: GOOD - Minor hallucination, mostly grounded
⚠️  0.5-0.7: WARNING - Moderate hallucination detected
❌ 0.0-0.5: CRITICAL - High hallucination, answer not trustworthy

EXAMPLE:
Question: "Who scored the most points?"
Sources: [{"text": "Shai scored 2485 points"}]
Answer: "Shai scored 2485 points and won MVP"

Claims:
1. "Shai scored 2485 points" ✅ Supported
2. "Shai won MVP" ❌ NOT in sources (hallucination)

Faithfulness = 1/2 = 0.5 (50% hallucinated)

USE FOR: Detect hallucination, ensure answer grounded in data
```

## Answer Relevancy

```
ANSWER RELEVANCY (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Does the answer actually address the question?
HOW: Avg similarity of generated questions to original
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Answer is on-topic and focused
⚠️  0.7-0.9: GOOD - Answer is relevant with minor drift
⚠️  0.5-0.7: WARNING - Answer is somewhat off-topic
❌ 0.0-0.5: CRITICAL - Answer doesn't address question

EXAMPLE:
Question: "Who scored the most points?"
Answer: "Shai Gilgeous-Alexander scored 2485 points."

Generated questions from answer:
1. "Who is the leading scorer?" (similarity: 0.95)
2. "How many points did Shai score?" (similarity: 0.85)
3. "What are the scoring stats?" (similarity: 0.80)

Answer Relevancy = (0.95 + 0.85 + 0.80) / 3 = 0.87

USE FOR: Detect off-topic answers, ensure LLM understood question
```

## Answer Semantic Similarity

```
ANSWER SEMANTIC SIMILARITY (Answer Quality - Uses ground_truth_answer)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: How semantically similar is answer to expected answer?
HOW: Cosine similarity between embeddings
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Nearly identical meaning
⚠️  0.7-0.9: GOOD - Similar meaning, different wording
⚠️  0.5-0.7: WARNING - Related but different information
❌ 0.0-0.5: CRITICAL - Completely different meaning

EXAMPLE:
Ground Truth: "Shai scored the most points with 2485 PTS."
Actual Answer: "Shai Gilgeous-Alexander is the leading scorer with 2,485 points."

Semantic Similarity = 0.92 (same meaning, slightly different wording)

USE FOR: Check if answer conveys same information (allows paraphrasing)
```

## Answer Correctness

```
ANSWER CORRECTNESS (Answer Quality - Uses ground_truth_answer) ⭐ BEST OVERALL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Combined semantic similarity + factual correctness
HOW: 0.5 * Semantic Similarity + 0.5 * Factual F1
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Answer is correct
⚠️  0.7-0.9: GOOD - Mostly correct with minor issues
⚠️  0.5-0.7: WARNING - Partially correct, missing key facts
❌ 0.0-0.5: CRITICAL - Answer is incorrect

EXAMPLE:
Ground Truth: "Shai scored 2485 points, leading the league."
Actual Answer: "Shai Gilgeous-Alexander scored 2485 points."

Semantic Similarity: 0.90
Factual Overlap:
- TP: "Shai", "2485 points" ✅
- FN: "leading league" ❌ (missing)
F1 = 2*2 / (2*2 + 0 + 1) = 0.80

Answer Correctness = 0.5*0.90 + 0.5*0.80 = 0.85

USE FOR: PRIMARY METRIC for overall answer quality (best single metric)
```

## Context Precision

```
CONTEXT PRECISION (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Are relevant chunks ranked higher than irrelevant chunks?
HOW: Precision@K averaged across positions
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - Relevant chunks ranked first
⚠️  0.7-0.9: GOOD - Most relevant chunks near top
⚠️  0.5-0.7: WARNING - Relevant chunks mixed with irrelevant
❌ 0.0-0.5: CRITICAL - Relevant chunks ranked too low

EXAMPLE:
Ground Truth Vector: "Should retrieve Reddit 3.pdf about efficiency"

Retrieved chunks (in order):
1. Reddit 3.pdf, page 2 (efficiency) ✅ Relevant
2. Reddit 1.pdf, page 1 (GOAT debate) ❌ Irrelevant
3. Reddit 3.pdf, page 5 (efficiency) ✅ Relevant
4. News article (unrelated) ❌ Irrelevant

Precision@1 = 1/1 = 1.0
Precision@2 = 1/2 = 0.5
Precision@3 = 2/3 = 0.67
Precision@4 = 2/4 = 0.5

Context Precision = (1.0 + 0.5 + 0.67 + 0.5) / 4 = 0.67

USE FOR: Optimize retrieval ranking
NOTE: SKIPPED for SQL-only queries (no vector search)
```

## Context Recall

```
CONTEXT RECALL (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: Were all required chunks retrieved?
HOW: (Retrieved required) / (Total required)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - All required chunks retrieved
⚠️  0.7-0.9: GOOD - Most required chunks retrieved
⚠️  0.5-0.7: WARNING - Missing some required chunks
❌ 0.0-0.5: CRITICAL - Missing most required chunks

EXAMPLE:
Ground Truth Vector: "Should retrieve Reddit 3.pdf discussing efficiency,
                      specifically mentioning Reggie Miller with 115 TS%"

Required chunks:
1. Reddit 3.pdf about efficiency ✅ Retrieved
2. Mention of Reggie Miller ✅ Retrieved
3. 115 TS% statistic ❌ NOT retrieved

Context Recall = 2/3 = 0.67 (67% of required info retrieved)

USE FOR: Check if retrieval is missing key information
NOTE: SKIPPED for SQL-only queries (no vector search)
```

## Context Relevancy

```
CONTEXT RELEVANCY (Retrieval Quality - Uses ground_truth_vector)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT: What fraction of retrieved chunks are actually relevant?
HOW: (Relevant sentences) / (Total sentences)
RANGE: 0.0 to 1.0 (higher is better)

INTERPRETATION:
✅ 0.9-1.0: EXCELLENT - No noise, all chunks relevant
⚠️  0.7-0.9: GOOD - Low noise, mostly relevant
⚠️  0.5-0.7: WARNING - Moderate noise, half irrelevant
❌ 0.0-0.5: CRITICAL - High noise, mostly irrelevant

EXAMPLE:
Question: "What do fans think about efficiency?"

Retrieved chunks:
1. "Fans believe Reggie Miller is most efficient with 115 TS%" ✅ Relevant
2. "Miller played for the Pacers" ❌ Irrelevant (not about efficiency)
3. "Efficiency is measured by TS%" ✅ Relevant
4. "LeBron is the GOAT" ❌ Irrelevant (off-topic)

Context Relevancy = 2/4 = 0.5 (50% relevant)

USE FOR: Detect noisy retrieval (too much irrelevant content)
NOTE: SKIPPED for SQL-only queries (no vector search)
```


================================================================================
# VECTOR SEARCH ANALYSIS
================================================================================

## Retrieval Statistics

- Avg Sources per Query: 7.50
- Total Unique Sources: 5
- Avg Similarity Score: 65.58
- Empty Retrievals: 0

---

**Report Generated:** 2026-02-16 23:50:18
