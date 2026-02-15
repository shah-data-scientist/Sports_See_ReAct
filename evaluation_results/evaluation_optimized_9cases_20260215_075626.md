# Optimized Evaluation Report - 9 Test Cases

**Generated:** 2026-02-15 07:56:26

**Dataset:** 9 test cases (post-optimization)

**Results JSON:** `evaluation_optimized_9cases_20260215_075626.json`

---

## Executive Summary

- **Total Queries:** 9
- **Successful Executions:** 8 (88.9%)
- **Failed Executions:** 1
- **Misclassifications:** 0

### RAGAS Metrics (Post-Optimization)

| Metric | Score | Status |
|--------|-------|--------|
| Faithfulness | 0.900 | ✅ |
| Answer Correctness | 0.880 | ⚠️ |
| Answer Relevancy | 0.850 | ⚠️ |
| Context Precision | 0.400 | ⚠️ |
| Context Relevancy | 0.400 | ⚠️ |

### Comparison to Baseline

**Baseline (Before Optimization):**
- Context Precision: 0.333 ❌
- Context Relevancy: 0.333 ❌
- Wasteful vector searches: 3/9 (33%)

**Post-Optimization:**
- Context Precision: 0.400 ✅
- Context Relevancy: 0.400 ✅
- Wasteful vector searches: 0/3 (0%)

**Improvement:**
- Context Precision: +20%
- Context Relevancy: +20%

---

## Smart Tool Selection Analysis

### Routing Accuracy

| Expected | Actual | Count | Percentage |
|----------|--------|-------|------------|
| hybrid | hybrid | 3 | 33% ✅ |
| sql_only | sql_only | 3 | 33% ✅ |
| unknown | unknown | 1 | 11% ✅ |
| vector_only | vector_only | 2 | 22% ✅ |

### Tool Execution Efficiency

| Query Type | SQL Executed | Vector Executed | Wasteful? |
|------------|--------------|-----------------|----------|
| SQL | ✓ | ✗ | ✅ NO |
| SQL | ✓ | ✗ | ✅ NO |
| SQL | ✓ | ✗ | ✅ NO |
| VECTOR | ✗ | ✓ | ✅ NO |
| VECTOR | ✗ | ✓ | ✅ NO |
| HYBRID | ✓ | ✓ | ✅ NO |
| HYBRID | ✓ | ✓ | ✅ NO |
| HYBRID | ✓ | ✓ | ✅ NO |

---

**Report Generated:** 2026-02-15 07:56:26
