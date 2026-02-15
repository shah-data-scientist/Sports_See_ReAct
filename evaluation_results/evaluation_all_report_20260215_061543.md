# Unified Evaluation Report - ALL

**Generated:** 2026-02-15 06:27:25

**Dataset:** 9 test cases

**Results JSON:** `evaluation_all_20260215_061543.json`

---

## Executive Summary

- **Total Queries:** 9
- **Successful Executions:** 9 (100.0%)
- **Failed Executions:** 0
- **Misclassifications:** 6
- **Avg Processing Time:** 6876ms
- **Min/Max Processing Time:** 5791ms / 9689ms

### Test Type Distribution

| Type | Count | Percentage |
|------|-------|------------|
| HYBRID | 3 | 33.3% |
| SQL | 3 | 33.3% |
| UNKNOWN | 0 | 0.0% |
| VECTOR | 3 | 33.3% |

### Routing Statistics

| Routing | Count | Percentage |
|---------|-------|------------|
| greeting | 0 | 0.0% |
| hybrid | 0 | 0.0% |
| sql_only | 0 | 0.0% |
| unknown | 9 | 100.0% |
| vector_only | 0 | 0.0% |

### Misclassifications (6 queries)

| # | Question | Test Type | Expected | Actual | Response Preview |
|---|----------|-----------|----------|--------|------------------|
| 1 | Who scored the most points this season?... | sql | sql_only | unknown | Shai Gilgeous-Alexander scored the most points this season with 2485 points. The... |
| 2 | Who are the top 3 rebounders in the leag... | sql | sql_only | unknown | The top 3 rebounders in the league are Ivica Zubac (1008 rebounds), Domantas Sab... |
| 3 | Who are the top 5 players in steals?... | sql | sql_only | unknown | The top 5 players in steals are: Dyson Daniels (228 steals), Shai Gilgeous-Alexa... |
| 4 | What do Reddit users think about teams t... | vector | vector_only | unknown | Based on Reddit posts, the Orlando Magic have impressed some users, particularly... |
| 5 | What are the most popular opinions about... | vector | vector_only | unknown | Based on the SQL database, the Oklahoma City Thunder and Cleveland Cavaliers hav... |
| 6 | What do fans debate about Reggie Miller'... | vector | vector_only | unknown | Fans debate Reggie Miller's efficiency despite his strong stats. According to th... |

## Performance by Category

| Category | Count | Success Rate | Avg Time |
|----------|-------|--------------|----------|
| simple | 3 | 100.0% | 6550ms |
| simple_sql_top_n | 3 | 100.0% | 7414ms |
| tier1_comparison_plus_context | 1 | 100.0% | 7602ms |
| tier1_stat_plus_context | 1 | 100.0% | 6087ms |
| tier1_stat_plus_explanation | 1 | 100.0% | 6300ms |



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
| Context Precision | 0.333 | ❌ CRITICAL |
| Context Relevancy | 0.333 | ❌ CRITICAL |

## RAGAS Metrics by Category

| Category | Count | Faithfulness | Answer Correctness | Context Precision | Context Recall |
|----------|-------|--------------|-------------------|-------------------|----------------|
| simple_sql_top_n | 6 | 0.900 | 0.880 | 0.000 | N/A |
| simple | 6 | 0.900 | 0.880 | 1.000 | N/A |
| tier1_stat_plus_context | 6 | 0.900 | 0.880 | 0.000 | N/A |
| tier1_comparison_plus_context | 6 | 0.900 | 0.880 | 0.000 | N/A |
| tier1_stat_plus_explanation | 6 | 0.900 | 0.880 | 0.000 | N/A |

## Low Scoring Queries (< 0.7) - Top 6

### 1. SIMPLE_SQL_TOP_N

**Question:** Who scored the most points this season?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 2. SIMPLE_SQL_TOP_N

**Question:** Who are the top 3 rebounders in the league?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 3. SIMPLE_SQL_TOP_N

**Question:** Who are the top 5 players in steals?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 4. TIER1_STAT_PLUS_CONTEXT

**Question:** Who scored the most points this season and what makes them an effective scorer?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 5. TIER1_COMPARISON_PLUS_CONTEXT

**Question:** Compare LeBron James and Kevin Durant's scoring this season and explain their scoring styles....

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
- Context Recall: None

### 6. TIER1_STAT_PLUS_EXPLANATION

**Question:** What is Nikola Jokić's scoring average and why is he considered an elite offensive player?...

**Scores:**
- Min Score: 0.000
- Faithfulness: 0.9
- Answer Correctness: 0.88
- Answer Relevancy: 0.85
- Context Precision: 0.0
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
# SQL ANALYSIS
================================================================================

## Error Taxonomy

- Total Errors: 0
- LLM Declined: 0
- Syntax Errors: 0
- Empty Responses: 0

## Query Structure Analysis

- Total Queries: 9
- Queries with JOIN: 9
- Queries with Aggregation: 2
- Queries with Filter: 4


================================================================================
# VECTOR SEARCH ANALYSIS
================================================================================

## Retrieval Statistics

- Avg Sources per Query: 7.00
- Total Unique Sources: 3
- Avg Similarity Score: 61.94
- Empty Retrievals: 0

---

**Report Generated:** 2026-02-15 06:27:25
