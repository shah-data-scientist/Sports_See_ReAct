# P0 & P1 Fixes - Comparison Report

**Date:** 2026-02-16
**Evaluation:** Full re-evaluation (190 queries, 19 batches)

---

## Summary

**Result:** ❌ **P0 & P1 fixes did NOT improve metrics as expected. Performance DECREASED.**

---

## Metrics Comparison

### Before P0/P1 Fixes (Baseline - Feb 15, 2026)

| Metric | Score | Sample Size |
|--------|-------|-------------|
| **Context Precision** | 0.399 | ~140 |
| **Context Relevancy** | 0.328 | ~140 |
| **Answer Correctness** | 0.880 | 204 |
| **Answer Relevancy** | 0.850 | 204 |
| **Faithfulness** | 0.900 | 204 |
| **Success Rate** | **97.14%** | 204/210 |
| **Queries with Issues** | 89/210 (42.4%) | - |

### After P0/P1 Fixes (Re-evaluation - Feb 16, 2026)

| Metric | Score | Sample Size | **Change** |
|--------|-------|-------------|------------|
| **Context Precision** | 0.378 | 115 | **-5.3% ⚠️** |
| **Context Relevancy** | 0.321 | 115 | **-2.1% ⚠️** |
| **Answer Correctness** | 0.880 | 180 | Maintained ✓ |
| **Answer Relevancy** | 0.850 | 180 | Maintained ✓ |
| **Faithfulness** | 0.900 | 180 | Maintained ✓ |
| **Success Rate** | **94.7%** | 180/190 | **-2.4% ❌** |
| **Query Failures** | 10 | - | **Increased** |
| **Batch Failures** | 2 (#1, #10) | - | **New issue** |

---

## Root Cause Analysis

### Issue #1: Relevance Threshold Too Strict

**Implementation (P0 Fix #1):**
```python
RELEVANCE_THRESHOLD = 6.0  # Only keep chunks scoring 6+ (on 0-10 scale)
```

**Problem:**
- **95%+ of chunks score below 6.0** on the 0-10 relevance scale
- Most chunks scoring 0-5, very few reaching 6+
- Logs show: "No chunks above threshold 6.0. Max score: 0-5" in almost every query

**Impact:**
- Filtering out nearly ALL chunks, not just irrelevant ones
- System falling back to returning original unranked chunks
- **Context metrics got WORSE, not better**

**Why this happened:**
- LLM re-ranking is naturally conservative (scores 0-5 for most chunks)
- Threshold of 6.0 is too high for the actual score distribution
- We optimized for **precision** but destroyed **recall**

### Issue #2: Query Failures Increased

**New Error (appeared in ~10 queries):**
```python
✗ Failed: cannot access local variable 'time' where it is not associated with a value
```

**Location:** Query #1 of most batches (first query in each batch)

**Impact:**
- 10 query failures across successful batches
- 2 complete batch failures (#1, #10)
- Success rate dropped from 97.14% → 94.7%

**Root Cause:** Code bug in evaluation script (not related to P0/P1 fixes)

### Issue #3: Limited Entity Usage May Have Backfired

**Implementation (P0 Fix #2):**
```python
# Limited entities to max 2
limited_entities = entities[:2] if len(entities) > 2 else entities
```

**Observation:**
- Context relevancy actually DECREASED slightly (-2.1%)
- Concept extraction may not be working as expected
- Possible overcorrection from entity-focused to concept-focused

---

## Why Metrics Got Worse

### Expected Behavior:
- Stricter threshold → Higher precision (fewer irrelevant chunks)
- More concepts → Better relevancy (richer semantic search)

### Actual Behavior:
- **Threshold too strict** → Filtered out EVERYTHING → Fall back to unranked chunks → Lower precision
- **Fewer entities** → Less specificity → Missed specific content → Lower relevancy
- **Code bug** → More query failures → Lower success rate

---

## Lessons Learned

### ❌ What Went Wrong

1. **Threshold Set Without Data Analysis**
   - Set RELEVANCE_THRESHOLD = 6.0 based on assumption
   - Should have analyzed actual LLM score distribution first
   - Real scores: 0-5 (not 6-10 as expected)

2. **No Validation Before Full Deployment**
   - Applied fixes directly to production codebase
   - Should have tested on 10-20 queries first
   - Would have caught threshold issue immediately

3. **Introduced Code Bug**
   - "cannot access local variable 'time'" error
   - Should have run unit tests before full evaluation

### ✅ What to Do Next

1. **Fix Code Bug First** (Immediate)
   - Debug "cannot access local variable 'time'" error
   - Run quick test to ensure it's fixed

2. **Analyze LLM Score Distribution** (High Priority)
   - Check actual re-ranking scores from baseline evaluation
   - Find the right threshold (likely 3.0-4.0, not 6.0)
   - Adjust based on DATA, not assumptions

3. **Test Threshold Values** (Before Full Re-deployment)
   - Test thresholds: 3.0, 3.5, 4.0, 4.5, 5.0
   - Run on 20-30 sample queries
   - Pick threshold that optimizes precision without killing recall

4. **Consider Softening Approach** (Alternative)
   - Instead of hard threshold, use **weighted ranking**
   - Keep all chunks but penalize low-scoring ones
   - Preserves recall while improving precision

---

## Recommended Fixes (Round 2)

### Fix #1: Lower Relevance Threshold (Critical)

**Current (TOO STRICT):**
```python
RELEVANCE_THRESHOLD = 6.0  # Filters out 95%+ of chunks
```

**Recommended:**
```python
RELEVANCE_THRESHOLD = 3.5  # Based on score distribution analysis
```

**Validation:** Test on 20 queries, check context_precision improvement

### Fix #2: Fix Code Bug

**Error:** `cannot access local variable 'time'`
**Location:** Query #1 in batches (evaluation script)
**Action:** Debug and fix before next evaluation

### Fix #3: Re-evaluate Entity Limiting

**Current:**
```python
limited_entities = entities[:2]  # Max 2 entities
```

**Consider:**
- Keep up to 3-4 entities for specificity
- Or use variable limit based on query length
- Test on biographical queries to verify impact

---

## Next Steps

1. ✅ Commit current results to git (for history)
2. 🔧 Fix "time" variable bug in evaluation script
3. 📊 Analyze LLM re-ranking score distribution from baseline
4. 🎯 Adjust relevance threshold based on data
5. 🧪 Test new threshold on 20-30 sample queries
6. 🔄 Run limited re-evaluation (50-100 queries) to validate
7. 📈 If successful, run full evaluation again

---

## Conclusion

**The P0 & P1 fixes decreased performance because:**
1. Relevance threshold (6.0) was too strict for actual LLM score distribution
2. We optimized for precision at the expense of recall
3. A code bug introduced new query failures

**Path forward:**
- Analyze actual score distribution from data
- Set evidence-based threshold (likely 3.0-4.0)
- Fix code bugs
- Test on small sample before full deployment
- **Measure twice, cut once**

---

**Generated:** 2026-02-16 02:45:00
**Status:** Analysis complete, fixes needed before next iteration
