# Sports_See Refactoring Proposal

**Date**: 2026-02-13
**Author**: Claude Code Analysis
**Project Version**: 1.0.0
**Status**: Proposal (Not Yet Implemented)

---

## Executive Summary

This document outlines recommended refactorings for the Sports_See RAG chatbot project. The codebase is already well-structured following Clean Architecture principles with 78.5% test coverage and 171 passing tests. These refactorings are **optimizations for maintainability**, not critical fixes.

**Key Metrics**:
- Overall Test Coverage: 78.5%
- Total Tests: 171 (all passing)
- Architecture: Clean (API → Services → Repositories → Models)
- Current Status: Production-ready

---

## Table of Contents

1. [High-Priority Refactorings](#high-priority-refactorings)
2. [Medium-Priority Refactorings](#medium-priority-refactorings)
3. [Low-Priority Refactorings](#low-priority-refactorings)
4. [What NOT to Refactor](#what-not-to-refactor)
5. [Implementation Roadmap](#implementation-roadmap)
6. [Risk Assessment](#risk-assessment)

---

## High-Priority Refactorings

### 1. Extract Query Classifier Responsibilities ⭐⭐⭐

**Priority**: High
**Impact**: High
**Effort**: Medium (4-6 hours)
**ROI**: High

#### Current Issue

`src/services/query_classifier.py` has grown to 600+ lines with multiple responsibilities:
- Query type classification (STATISTICAL/CONTEXTUAL/HYBRID)
- Greeting detection
- Biographical detection
- Complexity estimation
- Category classification
- Max expansion computation

This violates the Single Responsibility Principle and makes the class difficult to maintain, test, and extend.

#### Proposed Solution

Extract into separate focused classes under a new module structure:

```
src/services/query_analysis/
├── __init__.py
├── query_classifier.py        # Main orchestrator (routing logic only)
├── greeting_detector.py       # Greeting detection logic
├── biographical_analyzer.py   # Biographical query detection
├── complexity_estimator.py    # Query complexity scoring
├── category_classifier.py     # Query category classification
├── pattern_groups.py          # Pattern group constants
└── types.py                   # Shared types (QueryType, ClassificationResult)
```

#### Implementation Details

**1. greeting_detector.py**
```python
"""
FILE: greeting_detector.py
STATUS: Proposed
RESPONSIBILITY: Detect pure standalone greetings
LAST MAJOR UPDATE: TBD
MAINTAINER: TBD
"""

class GreetingDetector:
    """Detects pure standalone greetings with strict 6-layer exclusion."""

    def is_greeting(self, query: str) -> bool:
        """
        Detect if query is a PURE greeting with NO other content.

        Returns True only for standalone greetings like:
        - "hi", "hello", "hey", "thanks", "goodbye"
        - "good morning", "how are you"
        - "hi there", "hello everyone"

        Returns False for mixed queries like:
        - "hi, who are the top 5 scorers?"
        - "hello, can you help me?"
        """
        # Move current _is_greeting() logic here
        pass
```

**2. biographical_analyzer.py**
```python
class BiographicalAnalyzer:
    """Detects biographical queries about players/teams."""

    def is_biographical(self, query: str) -> bool:
        """
        Detect if query asks for player/team biographical information.

        Examples:
        - "Who is LeBron?" → True
        - "Tell me about Michael Jordan" → True
        - "Who are the top scorers?" → False
        """
        # Move current _is_biographical() logic here
        pass
```

**3. complexity_estimator.py**
```python
class ComplexityEstimator:
    """Estimates query complexity for adaptive K selection."""

    def estimate_complexity(self, query: str) -> int:
        """
        Calculate complexity score and map to K value.

        Returns:
            3: Simple queries (single lookup)
            5: Moderate queries (comparisons)
            7: Complex queries (multi-step analysis)
            9: Very complex queries (deep analysis)
        """
        # Move current _estimate_question_complexity() logic here
        pass
```

**4. category_classifier.py**
```python
class CategoryClassifier:
    """Classifies query quality for expansion strategy."""

    def classify_category(self, query: str) -> str:
        """
        Classify query style category.

        Returns:
            "noisy": Slang, typos, out-of-scope
            "conversational": Pronouns, follow-ups
            "complex": Synthesis, multi-part analysis
            "simple": Clear, well-formed queries
        """
        # Move current _classify_category() logic here
        pass

    def compute_max_expansions(self, query: str, category: str) -> int:
        """Compute expansion aggressiveness (1-5)."""
        # Move current _compute_max_expansions() logic here
        pass
```

**5. Updated query_classifier.py (Main Orchestrator)**
```python
class QueryClassifier:
    """Main orchestrator for query classification."""

    def __init__(self):
        self.greeting_detector = GreetingDetector()
        self.biographical_analyzer = BiographicalAnalyzer()
        self.complexity_estimator = ComplexityEstimator()
        self.category_classifier = CategoryClassifier()
        # ... pattern compilation

    def classify(self, query: str) -> ClassificationResult:
        """
        Orchestrate classification by delegating to specialized analyzers.

        NOTE: Greeting detection happens in chat.py BEFORE this method.
        """
        # Delegate to specialized classes
        is_biographical = self.biographical_analyzer.is_biographical(query)
        complexity_k = self.complexity_estimator.estimate_complexity(query)
        query_category = self.category_classifier.classify_category(query)
        max_expansions = self.category_classifier.compute_max_expansions(query, query_category)

        # Core classification logic remains here
        # ... weighted scoring, hybrid detection, etc.
```

#### Benefits

1. **Single Responsibility Principle** - Each class has one clear purpose
2. **Easier Testing** - Each class independently testable with focused unit tests
3. **Better Code Navigation** - Developers can quickly find specific functionality
4. **Parallel Development** - Multiple developers can work on different analyzers
5. **Reduced Coupling** - Changes to greeting detection don't affect complexity estimation

#### Migration Strategy

**Week 1: Extract GreetingDetector**
- Create `greeting_detector.py`
- Move `_is_greeting()` logic
- Update tests
- Verify 100% backward compatibility

**Week 2: Extract ComplexityEstimator**
- Create `complexity_estimator.py`
- Move `_estimate_question_complexity()` logic
- Update tests

**Week 3: Extract CategoryClassifier**
- Create `category_classifier.py`
- Move `_classify_category()` and `_compute_max_expansions()` logic
- Update tests

**Week 4: Extract BiographicalAnalyzer + Cleanup**
- Create `biographical_analyzer.py`
- Move `_is_biographical()` logic
- Clean up main `QueryClassifier`
- Final integration tests

#### Testing Requirements

Each extracted class must have:
- Unit tests covering all edge cases
- Integration tests with QueryClassifier
- Regression tests ensuring backward compatibility

**Test Coverage Target**: Maintain or exceed current 78.5%

---

### 2. Consolidate Pattern Definitions ⭐⭐

**Priority**: Medium
**Impact**: Medium
**Effort**: Low (2-3 hours)
**ROI**: High

#### Current Issue

Pattern groups (STAT_GROUPS, CTX_GROUPS) are defined as class attributes in `QueryClassifier`, making them:
- Difficult to maintain (scattered across 130+ lines)
- Hard to externalize for non-developers
- Tightly coupled to classifier implementation

#### Proposed Solution

Move to dedicated configuration module:

```
src/services/query_analysis/
└── patterns.py
```

**Implementation**:
```python
"""
FILE: patterns.py
STATUS: Proposed
RESPONSIBILITY: Pattern group definitions for query classification
LAST MAJOR UPDATE: TBD
MAINTAINER: TBD
"""

from dataclasses import dataclass
from typing import NamedTuple
import re

class PatternGroup(NamedTuple):
    """A weighted regex group that fires at most once per query."""
    name: str
    weight: float
    pattern: re.Pattern


class StatisticalPatterns:
    """13 weighted statistical pattern groups."""

    # NBA Database stat column headers
    _STAT_ABBRS = r"pts|reb|ast|stl|blk|tov|pf|gp|min|..."
    _PCT_ABBRS = r"fg%|ft%|3p%|efg%|ts%|..."
    _DB_DESCRIPTIONS = r"games\s+played|field\s+goals?\s+made|..."

    GROUPS = [
        PatternGroup("S1_db_abbreviations", 3.0, re.compile(
            rf"\b({_STAT_ABBRS})\b|(?<!\w)({_PCT_ABBRS})",
            re.IGNORECASE
        )),
        PatternGroup("S2_full_stat_words_and_db_descriptions", 3.0, re.compile(
            rf"\b(points?|rebounds?|assists?)\b|({_DB_DESCRIPTIONS})",
            re.IGNORECASE
        )),
        # ... all 13 groups
    ]


class ContextualPatterns:
    """10 weighted contextual pattern groups."""

    GROUPS = [
        PatternGroup("C1_why_how_questions", 3.0, re.compile(
            r"\b(why|explain|what makes|what caused)\b",
            re.IGNORECASE
        )),
        # ... all 10 groups
    ]


class HybridConnectors:
    """Structural connectors for hybrid detection."""

    PATTERN = re.compile(
        r"\b(and\s+explain|and\s+why|and\s+what\s+makes|then\s+explain|but\s+why|and\s+how)\b"
        r"|(?:\s+-\s+|\s*—\s*|\s*–\s*)(explain|why|how|what\s+makes)",
        re.IGNORECASE
    )
```

**Usage in QueryClassifier**:
```python
from .patterns import StatisticalPatterns, ContextualPatterns, HybridConnectors

class QueryClassifier:
    def __init__(self):
        self.stat_groups = StatisticalPatterns.GROUPS
        self.ctx_groups = ContextualPatterns.GROUPS
        self._hybrid_connector_re = HybridConnectors.PATTERN
```

#### Benefits

1. **Clear Separation** - Data separated from logic
2. **Easier Maintenance** - All patterns in one place
3. **Future Externalization** - Could move to YAML/JSON for non-developers
4. **Better Documentation** - Patterns can have extensive comments
5. **Reusability** - Other modules can access patterns if needed

#### Future Enhancement

Patterns could be externalized to configuration files:

```yaml
# config/patterns.yaml
statistical_groups:
  - name: S1_db_abbreviations
    weight: 3.0
    pattern: \b(pts|reb|ast|stl|blk)\b
    description: NBA stat abbreviations from database schema

  - name: S2_full_stat_words
    weight: 3.0
    pattern: \b(points?|rebounds?|assists?)\b
    description: Full stat word forms
```

This would allow business analysts to update patterns without touching code.

---

## Medium-Priority Refactorings

### 3. Extract Weighted Scoring Logic ⭐⭐

**Priority**: Medium
**Impact**: Medium
**Effort**: Medium (3-4 hours)
**ROI**: Medium

#### Current Issue

Scoring logic and hybrid detection are embedded in the `classify()` method, making it:
- Long and complex (60+ lines)
- Difficult to unit test in isolation
- Hard to swap scoring strategies

#### Proposed Solution

Create dedicated `QueryScorer` class:

```python
"""
FILE: query_scorer.py
STATUS: Proposed
RESPONSIBILITY: Compute weighted scores for query classification
LAST MAJOR UPDATE: TBD
MAINTAINER: TBD
"""

from dataclasses import dataclass
from typing import NamedTuple

@dataclass
class ScoringResult:
    """Result of weighted scoring."""
    stat_score: float
    ctx_score: float
    stat_groups: list[str]
    ctx_groups: list[str]
    is_hybrid: bool
    hybrid_reason: str  # "connector", "ratio", "auto-promote", or None


class QueryScorer:
    """Computes weighted scores for query classification."""

    def __init__(self, stat_groups: list[PatternGroup], ctx_groups: list[PatternGroup]):
        self.stat_groups = stat_groups
        self.ctx_groups = ctx_groups
        self._hybrid_connector_re = re.compile(...)

    def compute_scores(self, query: str) -> ScoringResult:
        """
        Compute weighted scores for both statistical and contextual signals.

        Returns:
            ScoringResult with scores, matched groups, and hybrid detection
        """
        stat_score, stat_groups = self._compute_weighted_score(query, self.stat_groups)
        ctx_score, ctx_groups = self._compute_weighted_score(query, self.ctx_groups)

        is_hybrid, hybrid_reason = self._detect_hybrid(query, stat_score, ctx_score)

        return ScoringResult(
            stat_score=stat_score,
            ctx_score=ctx_score,
            stat_groups=stat_groups,
            ctx_groups=ctx_groups,
            is_hybrid=is_hybrid,
            hybrid_reason=hybrid_reason
        )

    def _compute_weighted_score(self, query: str, groups: list[PatternGroup]) -> tuple[float, list[str]]:
        """Each group fires at most once — no double-counting."""
        total = 0.0
        matched = []
        for group in groups:
            if group.pattern.search(query):
                total += group.weight
                matched.append(group.name)
        return total, matched

    def _detect_hybrid(self, query: str, stat_score: float, ctx_score: float) -> tuple[bool, str]:
        """
        3-tier hybrid detection logic.

        Returns:
            (is_hybrid, reason) where reason is "connector", "ratio", "auto-promote", or None
        """
        # Tier 1: Connector-based (structural)
        if self._hybrid_connector_re.search(query) and stat_score > 0 and ctx_score > 0:
            return True, "connector"

        # Tier 2: Imbalance ratio (balanced strength)
        if stat_score >= 1.5 and ctx_score >= 1.5:
            ratio = min(stat_score, ctx_score) / max(stat_score, ctx_score)
            if ratio >= 0.4:
                return True, f"ratio({ratio:.2f})"

        # Tier 3: Fallback auto-promote (safety net)
        if stat_score >= 4.0 and ctx_score >= 2.0:
            return True, "auto-promote"

        return False, None
```

**Usage in QueryClassifier**:
```python
class QueryClassifier:
    def __init__(self):
        self.scorer = QueryScorer(
            stat_groups=StatisticalPatterns.GROUPS,
            ctx_groups=ContextualPatterns.GROUPS
        )

    def classify(self, query: str) -> ClassificationResult:
        # Compute metadata
        is_biographical = self.biographical_analyzer.is_biographical(query)
        complexity_k = self.complexity_estimator.estimate_complexity(query)

        # Compute scores
        scoring = self.scorer.compute_scores(query)

        # Determine query type from scores
        if scoring.is_hybrid:
            query_type = QueryType.HYBRID
        elif scoring.stat_score > scoring.ctx_score:
            query_type = QueryType.STATISTICAL
        elif scoring.ctx_score > scoring.stat_score:
            query_type = QueryType.CONTEXTUAL
        else:
            query_type = QueryType.CONTEXTUAL  # default

        return ClassificationResult(query_type, is_biographical, complexity_k, ...)
```

#### Benefits

1. **Separation of Concerns** - Scoring logic isolated from classification orchestration
2. **Better Testability** - Can test scoring in isolation with mock patterns
3. **Strategy Pattern** - Could swap out scorers (rule-based vs ML-based)
4. **Improved Logging** - `ScoringResult` provides detailed debug info
5. **Reduced Complexity** - Main `classify()` method becomes simpler orchestrator

---

### 4. API Response Standardization ⭐

**Priority**: Low
**Impact**: Low
**Effort**: Low (2-3 hours)
**ROI**: High

#### Current Issue

API responses vary across endpoints, making client integration inconsistent.

#### Proposed Solution

Create standard response models:

```python
"""
FILE: src/api/models/responses.py
STATUS: Proposed
RESPONSIBILITY: Standard API response models
LAST MAJOR UPDATE: TBD
MAINTAINER: TBD
"""

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standard wrapper for all API responses."""
    success: bool = Field(..., description="Whether request succeeded")
    data: Optional[T] = Field(None, description="Response data payload")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class SourceInfo(BaseModel):
    """Information about a source document."""
    text: str
    source: str
    score: float
    metadata: dict


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    response: str
    sources: list[SourceInfo]
    processing_time_ms: int
    query_type: str
    is_biographical: bool
    complexity_k: int

    model_config = {
        "json_schema_extra": {
            "example": {
                "response": "LeBron James has averaged 27.2 points per game...",
                "sources": [
                    {
                        "text": "LeBron James statistics...",
                        "source": "nba_stats.db",
                        "score": 0.95,
                        "metadata": {"table": "player_stats"}
                    }
                ],
                "processing_time_ms": 1250,
                "query_type": "hybrid",
                "is_biographical": True,
                "complexity_k": 5
            }
        }
    }


class FeedbackResponse(BaseModel):
    """Response from feedback submission."""
    feedback_id: str
    status: str
```

**Usage**:
```python
@app.post("/chat", response_model=APIResponse[ChatResponse])
async def chat(request: ChatRequest):
    try:
        result = await chat_service.chat(request)
        return APIResponse(
            success=True,
            data=ChatResponse(**result),
            metadata={"version": "1.0.0"}
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error=str(e),
            metadata={"error_type": type(e).__name__}
        )
```

#### Benefits

1. **Consistent API Contract** - All responses have same structure
2. **Better OpenAPI Docs** - Automatic schema generation with examples
3. **Easier Client Integration** - Clients can rely on consistent format
4. **Type Safety** - Pydantic validation ensures correct structure
5. **Error Handling** - Standardized error responses

---

## Low-Priority Refactorings

### 5. Service Layer Dependency Injection ⭐

**Priority**: Low
**Impact**: Medium
**Effort**: Medium (4-5 hours)
**ROI**: Medium

#### Current Issue

Services create their own dependencies, making testing harder.

#### Proposed Solution

Use dependency injection pattern:

```python
# Before
class ChatService:
    def __init__(self):
        self.query_classifier = QueryClassifier()
        self.sql_tool = SQLTool()
        self.vector_store = VectorStoreRepository()

# After
class ChatService:
    def __init__(
        self,
        query_classifier: QueryClassifier,
        sql_tool: SQLTool,
        vector_store: VectorStoreRepository,
        llm_client: LLMClient
    ):
        self.query_classifier = query_classifier
        self.sql_tool = sql_tool
        self.vector_store = vector_store
        self.llm_client = llm_client
```

**Dependency Container** (optional):
```python
# src/core/container.py
class ServiceContainer:
    """Simple dependency injection container."""

    @staticmethod
    def create_chat_service() -> ChatService:
        """Factory method for ChatService with all dependencies."""
        query_classifier = QueryClassifier()
        sql_tool = SQLTool()
        vector_store = VectorStoreRepository()
        llm_client = LLMClient()

        return ChatService(
            query_classifier=query_classifier,
            sql_tool=sql_tool,
            vector_store=vector_store,
            llm_client=llm_client
        )
```

#### Benefits

1. **Better Testability** - Easy to inject mocks/stubs
2. **Loose Coupling** - Services depend on interfaces, not implementations
3. **Configuration** - Can swap implementations via config
4. **Clear Dependencies** - Constructor shows all dependencies explicitly

---

### 6. Extract Evaluation Runners Interface ⭐

**Priority**: Low
**Impact**: Low
**Effort**: Medium (3-4 hours)
**ROI**: Low

#### Current Issue

Three evaluation runners (`run_sql_evaluation.py`, `run_vector_evaluation.py`, `run_hybrid_evaluation.py`) have similar structure but duplicated code.

#### Proposed Solution

Create base class with template method pattern:

```python
"""
FILE: src/evaluation/runners/base_runner.py
STATUS: Proposed
RESPONSIBILITY: Base class for evaluation runners
LAST MAJOR UPDATE: TBD
MAINTAINER: TBD
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

TestCase = TypeVar('TestCase')
EvaluationResult = TypeVar('EvaluationResult')

@dataclass
class EvaluationReport:
    """Standard evaluation report structure."""
    total_tests: int
    passed: int
    failed: int
    accuracy: float
    latency_p50: float
    latency_p95: float
    latency_p99: float
    category_breakdown: dict[str, dict]
    results: list


class EvaluationRunner(ABC, Generic[TestCase, EvaluationResult]):
    """Base class for all evaluation runners (template method pattern)."""

    @abstractmethod
    def load_test_cases(self) -> list[TestCase]:
        """Load test cases from module."""
        pass

    @abstractmethod
    def evaluate_query(self, test_case: TestCase) -> EvaluationResult:
        """Evaluate single query and return result."""
        pass

    @abstractmethod
    def validate_result(self, test_case: TestCase, result: EvaluationResult) -> bool:
        """Validate if result matches expected outcome (oracle logic)."""
        pass

    def run_evaluation(self) -> EvaluationReport:
        """
        Common evaluation flow (template method).

        1. Load test cases
        2. Evaluate each query
        3. Validate results
        4. Calculate metrics
        5. Generate report
        """
        test_cases = self.load_test_cases()
        results = []

        for test_case in test_cases:
            start_time = time.time()
            result = self.evaluate_query(test_case)
            latency_ms = (time.time() - start_time) * 1000

            passed = self.validate_result(test_case, result)

            results.append({
                "test_case": test_case,
                "result": result,
                "passed": passed,
                "latency_ms": latency_ms
            })

        return self.generate_report(results)

    def generate_report(self, results: list) -> EvaluationReport:
        """Common report generation logic."""
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        accuracy = (passed / total * 100) if total > 0 else 0.0

        latencies = [r["latency_ms"] for r in results]

        return EvaluationReport(
            total_tests=total,
            passed=passed,
            failed=failed,
            accuracy=accuracy,
            latency_p50=np.percentile(latencies, 50),
            latency_p95=np.percentile(latencies, 95),
            latency_p99=np.percentile(latencies, 99),
            category_breakdown=self._compute_category_breakdown(results),
            results=results
        )

    def _compute_category_breakdown(self, results: list) -> dict:
        """Compute per-category metrics."""
        # Common category breakdown logic
        pass
```

**Concrete Implementation**:
```python
class SQLEvaluationRunner(EvaluationRunner[SQLTestCase, SQLResult]):
    """SQL evaluation runner."""

    def load_test_cases(self) -> list[SQLTestCase]:
        from src.evaluation.sql_test_cases import SQL_TEST_CASES
        return SQL_TEST_CASES

    def evaluate_query(self, test_case: SQLTestCase) -> SQLResult:
        # Execute SQL query via ChatService
        response = chat_service.chat(test_case.query)
        return SQLResult(...)

    def validate_result(self, test_case: SQLTestCase, result: SQLResult) -> bool:
        # Oracle validation logic
        return result.query_type == "statistical" and result.success
```

#### Benefits

1. **DRY Principle** - Common evaluation flow defined once
2. **Consistency** - All evaluations follow same structure
3. **Extensibility** - Easy to add new evaluation types
4. **Common Metrics** - Standardized metric calculation

---

## What NOT to Refactor

These areas work well and should **remain as-is**:

### 1. ✅ Weighted Pattern Groups (STAT_GROUPS/CTX_GROUPS)

**Why**: The current structure is working perfectly:
- Each group fires at most once (prevents double-counting)
- Weights are well-calibrated (3.0 for strong signals, 0.5 for weak)
- Clear naming convention (S1-S13, C1-C10)

**Don't**: Break them up into individual variables or over-abstract

### 2. ✅ Chat.py Linear Flow

**Why**: The current linear flow in `chat()` is clear and easy to follow:
1. Sanitize query
2. Check greeting → early return
3. Build conversation context
4. Expand query
5. Classify query
6. Route to SQL/Vector/Hybrid
7. Generate response

**Don't**: Add layers of abstraction or break into too many small methods

### 3. ✅ Static Methods in QueryClassifier

**Why**: Methods like `_is_definitional()`, `_has_glossary_term()` are fine as static utilities. They don't need to be separate classes.

**Don't**: Extract every static method into a separate class

### 4. ✅ Repository Pattern

**Why**: Current repository implementations are clean and focused:
- `VectorStoreRepository`
- `SQLRepository`
- `FeedbackRepository`

**Don't**: Add unnecessary abstraction layers or interfaces

---

## Implementation Roadmap

### Phase 1: High-Priority Refactorings (2-3 weeks)

**Week 1-2**: Extract Query Classifier Responsibilities
- Create module structure
- Extract GreetingDetector
- Extract ComplexityEstimator
- Extract CategoryClassifier
- Extract BiographicalAnalyzer
- Update all tests

**Week 3**: Consolidate Pattern Definitions
- Create patterns.py module
- Move STAT_GROUPS, CTX_GROUPS
- Update imports
- Verify backward compatibility

### Phase 2: Medium-Priority Refactorings (1-2 weeks)

**Week 4**: Extract Weighted Scoring Logic
- Create QueryScorer class
- Move scoring + hybrid detection
- Update tests

**Week 5**: API Response Standardization
- Create response models
- Update all endpoints
- Update OpenAPI docs

### Phase 3: Low-Priority Refactorings (Optional)

**As Needed**:
- Dependency Injection (when adding new features)
- Evaluation Base Class (when adding new evaluation types)

---

## Risk Assessment

### Low Risk ✅

1. **Consolidate Pattern Definitions** - Pure code organization, no logic changes
2. **API Response Standardization** - Additive change, doesn't break existing clients

### Medium Risk ⚠️

1. **Extract Query Classifier** - High test coverage mitigates risk
2. **Extract Weighted Scoring** - Well-defined interface, easy to test

### High Risk ⛔

1. **Dependency Injection** - Could introduce bugs if not done carefully
   - **Mitigation**: Extensive integration testing, gradual rollout

---

## Success Metrics

### Code Quality Metrics

- **Test Coverage**: Maintain ≥ 78.5% (target: 80%+)
- **Code Duplication**: Reduce by 20%
- **Cyclomatic Complexity**: Reduce QueryClassifier complexity by 40%
- **Lines of Code**: Individual files should be < 300 lines

### Development Metrics

- **Time to Add New Pattern**: Reduce from 30min to 10min
- **Time to Debug Classification**: Reduce from 1hr to 30min
- **New Developer Onboarding**: Reduce from 2 days to 1 day

### Performance Metrics

- **Query Latency**: No regression (maintain < 2s p95)
- **Classification Accuracy**: Maintain 87%+ (current baseline)

---

## Approval & Sign-off

- [ ] **Development Lead** - Review and approve technical approach
- [ ] **Product Owner** - Confirm refactoring priorities align with roadmap
- [ ] **QA Lead** - Confirm testing strategy is adequate
- [ ] **DevOps** - Confirm no deployment/infrastructure impacts

---

## Appendix A: File Size Analysis

Current large files that would benefit from refactoring:

| File | Lines | Responsibilities | Refactoring Priority |
|------|-------|------------------|---------------------|
| `query_classifier.py` | 635 | 6 distinct responsibilities | ⭐⭐⭐ High |
| `chat.py` | 400+ | Service orchestration (OK) | ✅ No change |
| `sql_tool.py` | 350+ | SQL query generation (OK) | ✅ No change |

---

## Appendix B: Dependency Graph

**Current**:
```
ChatService
├── QueryClassifier (monolithic)
├── SQLTool
├── VectorStoreRepository
├── QueryExpansion
└── LLMClient
```

**Proposed** (after refactoring #1):
```
ChatService
├── QueryClassifier (orchestrator)
│   ├── GreetingDetector
│   ├── BiographicalAnalyzer
│   ├── ComplexityEstimator
│   ├── CategoryClassifier
│   └── QueryScorer
├── SQLTool
├── VectorStoreRepository
├── QueryExpansion
└── LLMClient
```

---

## Appendix C: Testing Strategy

### Unit Tests (per extracted class)

Each extracted class needs comprehensive unit tests:

```python
# tests/services/query_analysis/test_greeting_detector.py
class TestGreetingDetector:
    def test_pure_greetings(self):
        """Test all pure greeting variations."""
        detector = GreetingDetector()
        assert detector.is_greeting("hi")
        assert detector.is_greeting("hello")
        assert detector.is_greeting("good morning")

    def test_mixed_queries(self):
        """Test rejection of mixed queries."""
        detector = GreetingDetector()
        assert not detector.is_greeting("hi, what are the top 5 scorers?")
        assert not detector.is_greeting("hello LeBron fans")
```

### Integration Tests

Test that refactored components work together:

```python
# tests/integration/test_query_analysis_integration.py
class TestQueryAnalysisIntegration:
    def test_full_classification_pipeline(self):
        """Test complete classification flow through all analyzers."""
        classifier = QueryClassifier()

        result = classifier.classify("Who are the top 5 scorers?")

        assert result.query_type == QueryType.STATISTICAL
        assert result.complexity_k == 5
        assert result.query_category == "simple"
```

### Regression Tests

Ensure backward compatibility:

```python
# tests/regression/test_classification_compatibility.py
class TestClassificationBackwardCompatibility:
    """Ensure refactored classifier produces same results as original."""

    def test_all_206_evaluation_queries(self):
        """Run all 206 evaluation queries and verify results unchanged."""
        # Load all test cases
        sql_tests = SQL_TEST_CASES
        vector_tests = VECTOR_TEST_CASES
        hybrid_tests = HYBRID_TEST_CASES

        # Run through refactored classifier
        # Compare with baseline results
        # Assert 100% match
```

---

## Conclusion

This refactoring proposal focuses on improving maintainability while preserving the system's current functionality and performance. The recommendations are prioritized by ROI, with high-priority items offering the most value for effort.

**Key Takeaways**:
1. **Don't fix what isn't broken** - The codebase is already solid
2. **Refactor incrementally** - Tackle high-priority items first
3. **Maintain test coverage** - Every refactoring must preserve or improve tests
4. **Measure success** - Track code quality and development velocity metrics

**Recommendation**: Start with refactoring #1 (Extract Query Classifier Responsibilities) as it provides the highest ROI and enables future improvements.

---

**Document Version**: 1.0
**Last Updated**: 2026-02-13
**Next Review**: TBD
