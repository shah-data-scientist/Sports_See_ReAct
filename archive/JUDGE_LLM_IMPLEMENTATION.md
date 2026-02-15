# Judge LLM Implementation - Dynamic Ground Truth Generation

## Date: 2026-02-15

## Overview

Implemented a **Judge LLM** pattern for dynamic ground truth answer generation during evaluation. Instead of pre-written expected answers in test cases, the judge LLM generates what the answer SHOULD be based on ground truth data/vector, then compares it with the actual LLM response.

---

## Key Changes

### 1. Field Renames and Removals

#### In `UnifiedTestCase`:
- ✅ **RENAMED**: `ground_truth` → `ground_truth_vector`
  - Reason: Clarity - distinguishes vector expectations from other ground truth fields
  - Example: `ground_truth_vector="Should retrieve Reddit discussions about efficiency..."`

- ✅ **REMOVED**: `ground_truth_answer` field
  - Reason: Will be generated dynamically by judge LLM during evaluation
  - Impact: All 206 test cases no longer have pre-written answers

#### In `UnifiedEvaluationResult`:
- ✅ **UPDATED**: `ground_truth_vector` (renamed from `ground_truth`)
- ✅ **UPDATED**: `ground_truth_answer` (now dynamically generated, not from test case)

### 2. Validation Changes

#### Before:
```python
def is_valid(self) -> tuple[bool, list[str]]:
    issues = []
    if not self.question:
        issues.append("question is required")
    if not self.test_type:
        issues.append("test_type is required")
    if not self.ground_truth_answer:  # ❌ REQUIRED
        issues.append("ground_truth_answer is required for all test types")
    return len(issues) == 0, issues
```

#### After:
```python
def is_valid(self) -> tuple[bool, list[str]]:
    issues = []
    if not self.question:
        issues.append("question is required")
    if not self.test_type:
        issues.append("test_type is required")
    # ground_truth_answer NO LONGER REQUIRED ✅
    # It will be generated dynamically by judge LLM
    return len(issues) == 0, issues
```

---

## Judge LLM Implementation

### Location: `src/evaluation/evaluator.py`

### Function: `_generate_ground_truth_answer(test_case: UnifiedTestCase) -> str`

**Purpose**: Generate expected answer using judge LLM based on ground truth data/vector

**Key Design Decisions**:
1. **Uses SAME prompt as main LLM** - Replicates `ReActAgent._build_combined_prompt()` (lines 182-236 in `src/agents/react_agent.py`)
2. **Same model** - Uses `gemini-2.0-flash` (same as main LLM)
3. **Same temperature** - Uses `0.1` (same as main LLM)
4. **Consistent evaluation** - Both judge and main LLM use identical logic/rules

### Prompt Structure (Judge LLM):
```python
"""You are an NBA statistics assistant. You have been provided with results from TWO sources:

1. SQL DATABASE (factual statistics - THIS IS YOUR SOURCE OF TRUTH FOR NUMBERS)
2. VECTOR SEARCH (contextual information, opinions, analysis)

CRITICAL RULES:
1. SQL results are ALWAYS the source of truth for statistics, scores, numbers
2. If SQL has the answer, use it (you may ignore vector if irrelevant)
3. If SQL and vector conflict on factual stats, TRUST SQL
4. Use vector results for context, opinions, "why/how" questions, background info
5. Combine both intelligently when both add value
6. If both sources are empty or irrelevant, say you don't have enough information

USER QUESTION:
{test_case.question}

SQL DATABASE RESULTS (FACTUAL STATS):
{test_case.ground_truth_data}  # From test case

VECTOR SEARCH RESULTS (CONTEXT & OPINIONS):
{test_case.ground_truth_vector}  # From test case

Based on the above information, provide a complete, accurate answer to the user's question.

Your answer:"""
```

### Evaluation Flow:

#### Before (Pre-written answers):
```
Test Case → [Execute LLM] → Compare with pre-written ground_truth_answer
```

#### After (Judge LLM):
```
Test Case → [Judge LLM generates expected answer] → [Execute actual LLM] → Compare answers
            ↑                                         ↓
            Uses ground_truth_data + ground_truth_vector
```

### Example Execution:

**Test Case** (SQL-only):
```python
UnifiedTestCase(
    question="Who scored the most points?",
    test_type=TestType.SQL,
    ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},
    ground_truth_vector=None,  # No vector expectations for SQL-only
)
```

**Step 1 - Judge LLM generates expected answer**:
```
Input to Judge LLM:
  - SQL: {"name": "Shai Gilgeous-Alexander", "pts": 2485}
  - Vector: No results

Output from Judge LLM:
  "Shai Gilgeous-Alexander scored the most points with 2485 PTS."
```

**Step 2 - Actual LLM executes**:
```
Input to Actual LLM:
  - User query: "Who scored the most points?"
  - SQL tool executes: SELECT ... ORDER BY pts DESC LIMIT 1
  - Vector tool executes: search("most points")

Output from Actual LLM:
  "Shai Gilgeous-Alexander scored the most points this season with 2,485 points."
```

**Step 3 - Comparison**:
```
Expected (Judge): "Shai Gilgeous-Alexander scored the most points with 2485 PTS."
Actual (LLM):     "Shai Gilgeous-Alexander scored the most points this season with 2,485 points."

RAGAS Evaluation:
  - Faithfulness: Check if actual answer contradicts expected
  - Answer Relevancy: Check if actual answer addresses the question
  - Context Precision/Recall: Check if correct sources were used
```

---

## Benefits

### 1. **Consistency**
- Judge LLM and main LLM use **identical prompt logic**
- Fair comparison: both follow same rules for combining SQL + Vector
- No bias from pre-written answers that might not match current LLM behavior

### 2. **Maintainability**
- Change prompt once → affects both judge and main LLM
- No need to manually write/update 206 ground truth answers
- Easier to adapt to new LLM models (just change model name)

### 3. **Robustness**
- Judge sees exact same data as main LLM would see (ground truth data/vector)
- Realistic expectations: judge generates answer from available data, not idealized pre-written text
- Handles edge cases: if data is insufficient, judge says so (same as main LLM should)

### 4. **Flexibility**
- Easy to experiment with different prompts
- Can adjust temperature/model for judge independently
- Can generate multiple expected answers for comparison (ensemble judging)

---

## Migration Impact

### Test Cases (206 total)
- ✅ **80 SQL cases**: Removed `ground_truth_answer`, kept `ground_truth_data`
- ✅ **75 Vector cases**: Removed `ground_truth_answer`, renamed `ground_truth` → `ground_truth_vector`
- ✅ **51 Hybrid cases**: Removed `ground_truth_answer`, renamed `ground_truth` → `ground_truth_vector`, kept `ground_truth_data`

### Example Before/After:

**BEFORE** (SQL test case):
```python
UnifiedTestCase(
    question="Who scored the most points?",
    test_type=TestType.SQL,
    expected_sql="SELECT...",
    ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},
    ground_truth=None,  # Old field name
    ground_truth_answer="Shai scored the most points with 2485 PTS.",  # Pre-written ❌
)
```

**AFTER** (SQL test case):
```python
UnifiedTestCase(
    question="Who scored the most points?",
    test_type=TestType.SQL,
    expected_sql="SELECT...",
    ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},
    ground_truth_vector=None,  # Renamed ✅
    # ground_truth_answer REMOVED - will be generated by judge LLM ✅
)
```

**BEFORE** (Vector test case):
```python
UnifiedTestCase(
    question="What do fans think about efficiency?",
    test_type=TestType.VECTOR,
    expected_sql=None,
    ground_truth_data=None,
    ground_truth="Should retrieve Reddit 3.pdf discussing efficiency...",  # Old field name
    ground_truth_answer="Fans believe Reggie Miller is the most efficient...",  # Pre-written ❌
)
```

**AFTER** (Vector test case):
```python
UnifiedTestCase(
    question="What do fans think about efficiency?",
    test_type=TestType.VECTOR,
    expected_sql=None,
    ground_truth_data=None,
    ground_truth_vector="Should retrieve Reddit 3.pdf discussing efficiency...",  # Renamed ✅
    # ground_truth_answer REMOVED - will be generated by judge LLM ✅
)
```

---

## Code Changes Summary

### Files Modified:

1. **`src/evaluation/models.py`** (509 lines)
   - Renamed `ground_truth` → `ground_truth_vector` (5 occurrences)
   - Removed `ground_truth_answer` from UnifiedTestCase
   - Updated `is_valid()` validation (no longer requires ground_truth_answer)
   - Updated helper methods (`has_vector_expectations`, `get_missing_fields`)
   - Updated migration functions
   - Updated UnifiedEvaluationResult.to_dict() and from_dict()

2. **`src/evaluation/test_data.py`** (2,287 → 1,888 lines, -17%)
   - Regenerated all 206 test cases
   - All use `ground_truth_vector` (not `ground_truth`)
   - All removed `ground_truth_answer` field

3. **`src/evaluation/evaluator.py`** (580 → 660 lines, +14%)
   - Added `_generate_ground_truth_answer()` function (67 lines)
   - Updated evaluation loop to call judge LLM before each test
   - Updated result recording to use dynamically generated `ground_truth_answer`
   - Updated UnifiedEvaluationResult field mapping

4. **`scripts/regenerate_with_renamed_fields.py`** (NEW, 103 lines)
   - Script to regenerate test cases with new field names
   - Handles backward compatibility during migration

---

## Testing

### Manual Test (SQL case):
```bash
cd "c:\Users\shahu\Documents\OneDrive\OPEN CLASSROOMS\PROJET 10\Sports_See_ReAct"

# Test judge LLM on first SQL case
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

from src.evaluation.consolidated_test_cases import ALL_TEST_CASES
from src.evaluation.evaluator import _generate_ground_truth_answer

# Get first SQL test case
sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type.value == 'sql']
test_case = sql_cases[0]

print(f'Question: {test_case.question}')
print(f'Ground Truth Data: {test_case.ground_truth_data}')
print()

# Generate expected answer
answer = _generate_ground_truth_answer(test_case)
print(f'Judge LLM Answer: {answer}')
"
```

### Run Full Evaluation:
```bash
# Run SQL evaluation with judge LLM
poetry run python -m src.evaluation.evaluator --type sql

# Run Vector evaluation with judge LLM
poetry run python -m src.evaluation.evaluator --type vector

# Run Hybrid evaluation with judge LLM
poetry run python -m src.evaluation.evaluator --type hybrid

# Run ALL evaluations (206 test cases)
poetry run python -m src.evaluation.evaluator --type all
```

---

## Expected Results

### Judge LLM Behavior:

**SQL-only case**:
- Judge sees: `ground_truth_data` (SQL results)
- Judge generates answer from SQL data only
- Should match format: "{name} scored {pts} points"

**Vector-only case**:
- Judge sees: `ground_truth_vector` (expected context)
- Judge generates answer from vector context
- Should summarize opinions/context from expected sources

**Hybrid case**:
- Judge sees: Both `ground_truth_data` AND `ground_truth_vector`
- Judge combines both sources (SQL + Vector)
- Should integrate stats with context

---

## Future Enhancements

1. **Ensemble Judging**: Generate multiple expected answers with different temperatures, compare actual answer against all
2. **Judge LLM Metrics**: Track judge LLM performance (does it generate reasonable answers?)
3. **Self-Consistency**: Compare judge answers across multiple runs to ensure stability
4. **Temperature Experiments**: Test if judge should use same temperature (0.1) or different (0.0 for more deterministic)
5. **Model Variations**: Test if using a different judge model (e.g., Opus) provides better evaluation

---

## Rollback Plan (if needed)

If judge LLM causes issues:
1. Restore pre-written answers: `git revert 563f39d`
2. Add back `ground_truth_answer` field to UnifiedTestCase
3. Rename `ground_truth_vector` back to `ground_truth`
4. Regenerate test cases with old field names

---

## Conclusion

Successfully implemented **Judge LLM** pattern for dynamic ground truth generation. All 206 test cases migrated. Evaluation now uses consistent prompt logic for both judge and main LLM, ensuring fair and maintainable evaluation.

**Commit**: `563f39d` - "Implement dynamic ground truth generation with judge LLM"

**Status**: ✅ **COMPLETE**
