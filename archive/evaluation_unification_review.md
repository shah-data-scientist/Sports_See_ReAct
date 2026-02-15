# Evaluation Unification Review & Field Analysis
## Generated: 2026-02-15

---

## PART 1: Special Treatment Review

### ✅ ACCEPTABLE Special Treatment (Validation & Filtering Only)

#### 1. **unified_model.py - UnifiedTestCase.is_valid()** (Lines 162-177)
```python
if self.test_type == TestType.SQL:
    if not self.expected_sql:
        issues.append("SQL test missing expected_sql")
    if not self.ground_truth_data:
        issues.append("SQL test missing ground_truth_data")
elif self.test_type == TestType.VECTOR:
    if not self.ground_truth:
        issues.append("Vector test missing ground_truth")
elif self.test_type == TestType.HYBRID:
    if not self.expected_sql:
        issues.append("Hybrid test missing expected_sql")
    if not self.ground_truth:
        issues.append("Hybrid test missing ground_truth")
```

**Purpose**: Validation logic to ensure test cases have required fields
**Recommendation**: **REMOVE** - All test cases should have the SAME validation. A test case is distinguished by which fields are populated (None vs value), not by different validation rules.

**Proposed Change**:
```python
def is_valid(self) -> tuple[bool, list[str]]:
    """Validate test case has required fields."""
    issues = []

    # Common required fields for ALL test types
    if not self.question:
        issues.append("question is required")
    if not self.test_type:
        issues.append("test_type is required")
    if not self.ground_truth_answer:
        issues.append("ground_truth_answer is required")

    # No special treatment - all fields are optional, type is just a label
    return len(issues) == 0, issues
```

#### 2. **run_evaluation.py - Expected Routing Determination** (Lines 267-274)
```python
if case_type == "sql":
    expected_routing = "sql_only"
elif case_type == "vector":
    expected_routing = "vector_only"
elif case_type == "hybrid":
    expected_routing = "hybrid"
```

**Purpose**: Determine expected routing for misclassification detection
**Recommendation**: **KEEP** - This is necessary for routing validation against the query classifier. It's not "special treatment" but rather mapping test_type to expected routing behavior.

#### 3. **verify_ground_truth.py - Filtering** (Lines 337, 364-365)
```python
vector_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.VECTOR]
sql_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.SQL]
hybrid_cases = [tc for tc in ALL_TEST_CASES if tc.test_type == TestType.HYBRID]
```

**Purpose**: Filter test cases for separate verification (SQL/Hybrid against DB, Vector via prompt)
**Recommendation**: **KEEP** - This is filtering for different verification methods, not processing logic.

#### 4. **quality_analysis.py - Auto-Detection** (Lines 1216-1248)
```python
has_sql = any(r.get("generated_sql") for r in results)
has_ragas = any(r.get("ragas_metrics") for r in results)
has_routing = any(r.get("routing") for r in results)

if has_sql:
    # Run SQL-specific analyses
if has_ragas or any(r.get("sources") for r in results):
    # Run Vector-specific analyses
if has_routing:
    # Run routing analysis
```

**Purpose**: Auto-detect which analyses to run based on available data
**Recommendation**: **KEEP** - This is the RIGHT pattern! It checks what data exists, not what test_type is. This is data-driven, not type-driven.

---

## PART 2: Field Analysis & Recommendations

### A. UnifiedTestCase Fields (Consolidated Test Cases)

Total fields: **17**

#### Common Fields (Always present)
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `question` | str | ✅ YES | **KEEP** | Core field - the query being tested |
| `test_type` | TestType | ✅ YES | **KEEP** | Labels the test type (SQL/VECTOR/HYBRID) |
| `category` | str \| None | ⚠️ Optional | **KEEP** | Useful for grouping/analysis (e.g., "simple_sql_top_n") |
| `ground_truth_answer` | str \| None | ⚠️ Optional | **MAKE REQUIRED** | Should be required for ALL test types |

#### SQL-Related Fields (populated for SQL & Hybrid, None for Vector)
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `expected_sql` | str \| None | SQL/Hybrid only | **KEEP** | Necessary for SQL validation |
| `ground_truth_data` | dict \| list \| None | SQL/Hybrid only | **KEEP** | Expected DB results for verification |
| `query_type` | QueryType \| None | SQL/Hybrid only | **QUESTIONABLE** | Overlaps with test_type? |

**Analysis of query_type**:
- Current values: SQL_ONLY, CONTEXTUAL_ONLY, HYBRID
- This seems to overlap with test_type (SQL, VECTOR, HYBRID)
- **Recommendation**: **REMOVE** - Redundant with test_type

**Examples showing redundancy**:
```python
# Example 1: SQL test
UnifiedTestCase(
    question="Who scored most points?",
    test_type=TestType.SQL,      # ← Says it's SQL
    query_type=QueryType.SQL_ONLY,  # ← Redundant!
    expected_sql="SELECT...",
    ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485}
)

# Example 2: Vector test
UnifiedTestCase(
    question="What are fans' opinions on efficiency?",
    test_type=TestType.VECTOR,           # ← Says it's Vector
    query_type=QueryType.CONTEXTUAL_ONLY,  # ← Redundant!
    ground_truth="Should retrieve Reddit 3.pdf..."
)

# Example 3: Hybrid test
UnifiedTestCase(
    question="Who is the best three-point shooter and why?",
    test_type=TestType.HYBRID,    # ← Says it's Hybrid
    query_type=QueryType.HYBRID,  # ← Redundant!
    expected_sql="SELECT...",
    ground_truth="Should retrieve Reddit discussions..."
)
```

**Proposed**: Remove query_type entirely - test_type already conveys this information.

#### Vector-Related Fields (populated for VECTOR & Hybrid, None for SQL)
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `ground_truth` | str \| None | VECTOR/Hybrid only | **KEEP** | Describes expected contextual retrieval |
| `min_vector_sources` | int | Default: 0 | **KEEP** | Expected minimum sources (e.g., 2-5) |
| `expected_source_types` | list[str] \| None | Optional | **KEEP** | e.g., ['Reddit 1.pdf', 'glossary'] |
| `min_similarity_score` | float | Default: 0.5 | **CONSIDER REMOVING** | Rarely used, hard to maintain |

**Example of min_similarity_score usage**:
```python
# Current
UnifiedTestCase(
    question="What is TS%?",
    test_type=TestType.VECTOR,
    ground_truth="Should retrieve glossary with 85-95% similarity",
    min_similarity_score=0.85  # ← This is redundant with ground_truth description
)
```
**Recommendation**: **REMOVE min_similarity_score** - Already described in ground_truth field

#### Optional Metadata Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `conversation_thread` | list \| None | Optional | **KEEP** | For conversational follow-up queries |
| `description` | str \| None | Optional | **MERGE** | Merge into notes |
| `tags` | list[str] \| None | Optional | **REMOVE** | Never used |
| `difficulty` | str | Default: "medium" | **REMOVE** | Never used |
| `notes` | str \| None | Optional | **KEEP** | Useful for edge cases |

**Example of unused fields**:
```python
# Current
UnifiedTestCase(
    question="Who scored most points?",
    tags=["top_n", "player_stats"],  # ← Never queried
    difficulty="easy",                # ← Never used in evaluation
    description="Simple top N query",  # ← Redundant with question + notes
    notes="Should handle ties correctly"  # ← Actually useful!
)
```

**Recommendation**:
- **REMOVE**: tags, difficulty
- **MERGE**: description → notes (just use notes for all additional context)

---

### B. UnifiedEvaluationResult Fields (Evaluation Results)

Total fields: **22**

#### Common Fields (Always present)
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `question` | str | ✅ YES | **KEEP** | The evaluated question |
| `test_type` | str | ✅ YES | **KEEP** | "sql", "vector", or "hybrid" |
| `category` | str | ✅ YES | **KEEP** | Test category |
| `success` | bool | ✅ YES | **KEEP** | Evaluation succeeded (no errors) |
| `response` | str \| None | Optional | **KEEP** | LLM's final answer |
| `processing_time_ms` | float | Default: 0.0 | **KEEP** | Performance tracking |
| `timestamp` | str \| None | Optional | **KEEP** | ISO timestamp |
| `notes` | str \| None | Optional | **KEEP** | Observations |

#### Routing Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `expected_routing` | str \| None | Optional | **KEEP** | Expected routing (sql_only, vector_only, hybrid) |
| `actual_routing` | str \| None | Optional | **KEEP** | Actual routing determined by system |
| `routing` | str \| None | Computed | **KEEP** | Alias for actual_routing (backward compat) |
| `is_misclassified` | bool | Default: False | **KEEP** | Whether routing was incorrect |

#### SQL Result Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `generated_sql` | str \| None | Optional | **KEEP** | SQL query generated |
| `sql_results` | list[dict] \| dict \| None | Optional | **KEEP** | Actual DB results |
| `visualization` | dict \| None | Optional | **KEEP** | Plotly chart data |

#### Vector Result Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `sources` | list[dict] | Default: [] | **KEEP** | Retrieved chunks |
| `sources_count` | int | Default: 0 | **KEEP** | Number of sources |
| `ragas_metrics` | dict \| None | Optional | **KEEP** | Faithfulness, relevancy, etc. |

#### Ground Truth Fields (for validation)
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `ground_truth` | str \| None | Optional | **KEEP** | Expected contextual info (Vector) |
| `ground_truth_answer` | str \| None | Optional | **KEEP** | Expected final answer |
| `ground_truth_data` | dict \| list \| None | Optional | **KEEP** | Expected SQL results |

#### Conversation Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `conversation_id` | str \| None | Optional | **KEEP** | For multi-turn tests |
| `turn_number` | int | Default: 1 | **KEEP** | Turn within conversation |

#### Error Fields
| Field | Type | Required? | Recommendation | Notes |
|-------|------|-----------|----------------|-------|
| `error` | str \| None | Optional | **KEEP** | Error message if failed |

---

## PART 3: Summary of Recommendations

### Fields to REMOVE (7 total)

#### From UnifiedTestCase:
1. **query_type** - Redundant with test_type
2. **min_similarity_score** - Redundant with ground_truth description
3. **tags** - Never used
4. **difficulty** - Never used
5. **description** - Merge into notes

#### From UnifiedEvaluationResult:
- None! All result fields are actively used

### Fields to MAKE REQUIRED (1 total)

#### From UnifiedTestCase:
1. **ground_truth_answer** - Should be required for ALL test types (not optional)

### Validation Logic to CHANGE (1 location)

#### unified_model.py - UnifiedTestCase.is_valid():
**BEFORE**: Type-specific validation (different rules for SQL/VECTOR/HYBRID)
**AFTER**: Unified validation (same rules for all types)

```python
# AFTER (proposed)
def is_valid(self) -> tuple[bool, list[str]]:
    """Validate test case has required common fields."""
    issues = []

    if not self.question:
        issues.append("question is required")
    if not self.test_type:
        issues.append("test_type is required")
    if not self.ground_truth_answer:
        issues.append("ground_truth_answer is required for all test types")

    return len(issues) == 0, issues
```

---

## PART 4: Before/After Comparison

### BEFORE: Different validation per type
```python
# SQL test - MUST have expected_sql and ground_truth_data
# Vector test - MUST have ground_truth
# Hybrid test - MUST have both

# This creates special treatment!
```

### AFTER: Same validation for all
```python
# ALL tests - MUST have question, test_type, ground_truth_answer
# Other fields are OPTIONAL and populated based on what makes sense

# No special treatment - just data!
```

### Example Test Cases After Cleanup

```python
# SQL test case - AFTER
UnifiedTestCase(
    question="Who scored the most points?",
    test_type=TestType.SQL,
    category="simple_sql_top_n",

    # SQL fields (populated)
    expected_sql="SELECT p.name, ps.pts FROM ...",
    ground_truth_data={"name": "Shai Gilgeous-Alexander", "pts": 2485},

    # Vector fields (None - not applicable)
    ground_truth=None,
    min_vector_sources=0,
    expected_source_types=None,

    # Answer (required for all)
    ground_truth_answer="Shai Gilgeous-Alexander scored the most points with 2485 PTS.",

    # Optional metadata
    notes="Should handle ties by showing all players with max points"
)

# Vector test case - AFTER
UnifiedTestCase(
    question="What do fans think about playoff teams?",
    test_type=TestType.VECTOR,
    category="simple_contextual",

    # SQL fields (None - not applicable)
    expected_sql=None,
    ground_truth_data=None,

    # Vector fields (populated)
    ground_truth="Should retrieve Reddit 1.pdf: 'Who are teams...' by u/MannerSuperb (31 upvotes). Expected teams: Magic, Pacers, Timberwolves. 2-5 chunks with 75-85% similarity.",
    min_vector_sources=2,
    expected_source_types=["Reddit 1.pdf"],

    # Answer (required for all)
    ground_truth_answer="Fans are impressed by the Magic (Paolo Banchero, Franz Wagner), Indiana Pacers, and Minnesota Timberwolves (Anthony Edwards) for exceeding expectations.",

    # Optional metadata
    notes=None
)

# Hybrid test case - AFTER
UnifiedTestCase(
    question="Who is the best three-point shooter and why is he effective?",
    test_type=TestType.HYBRID,
    category="biographical_with_context",

    # SQL fields (populated)
    expected_sql="SELECT p.name, ps.three_pct, ps.three_pa FROM ...",
    ground_truth_data={"name": "Seth Curry", "three_pct": 44.3, "three_pa": 245},

    # Vector fields (populated)
    ground_truth="Should retrieve Reddit 3.pdf discussing shooter efficiency metrics, TS%, and volume considerations. 3-5 chunks with 70-80% similarity.",
    min_vector_sources=3,
    expected_source_types=["Reddit 3.pdf"],

    # Answer (required for all)
    ground_truth_answer="Seth Curry is the best three-point shooter with 44.3% on 245 attempts. He's effective because of his high percentage on qualifying volume, exemplifying efficient scoring.",

    # Optional metadata
    notes="Tests ability to combine statistical data with contextual understanding of efficiency"
)
```

---

## PART 5: Impact Assessment

### Code Changes Required:
1. **unified_model.py**:
   - Remove fields: query_type, min_similarity_score, tags, difficulty, description
   - Update is_valid() to remove type-specific logic
   - Make ground_truth_answer required in validation

2. **consolidated_test_cases.py**:
   - Regenerate with removed fields
   - Ensure all test cases have ground_truth_answer

3. **Scripts** (add_explicit_none_values.py, migrate_to_unified_model.py):
   - Update to reflect new field list

### Benefits:
- **Simpler codebase**: No type-specific validation logic
- **Easier to understand**: A test case is just data, type is just a label
- **More maintainable**: No need to update validation when adding new test types
- **Consistent**: All test cases follow same rules

### Risks:
- **Migration effort**: Need to regenerate consolidated_test_cases.py
- **Existing data**: Need to ensure all test cases have ground_truth_answer filled

---

## PART 6: Action Plan

1. ✅ Review this document
2. ⬜ Approve field removals and changes
3. ⬜ Update unified_model.py
4. ⬜ Regenerate consolidated_test_cases.py
5. ⬜ Run verification scripts to ensure no breakage
6. ⬜ Commit all changes

---

**END OF REVIEW**
