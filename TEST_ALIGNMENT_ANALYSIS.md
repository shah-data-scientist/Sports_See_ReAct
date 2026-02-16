# Test-Code Structure Alignment Analysis

**Generated**: 2026-02-16

## 🎯 Goal
Ensure test structure mirrors source code structure exactly, with complete test coverage.

---

## 📊 Current Structure Comparison

### Source Code Structure (`src/`)
```
src/
├── agents/
│   ├── query_classifier.py
│   ├── react_agent.py
│   ├── results_formatter.py
│   └── tools.py
├── api/
│   ├── dependencies.py
│   ├── main.py
│   └── routes/
│       ├── chat.py
│       ├── conversation.py
│       ├── feedback.py
│       └── health.py
├── core/
│   ├── config.py
│   ├── exceptions.py
│   ├── logging_config.py
│   └── security.py
├── models/
│   ├── chat.py
│   ├── conversation.py
│   ├── document.py
│   ├── feedback.py
│   └── nba.py
├── pipeline/
│   ├── data_pipeline.py
│   ├── models.py
│   ├── quality_agent.py
│   └── reddit_chunker.py
├── repositories/
│   ├── conversation.py
│   ├── feedback.py
│   ├── nba_database.py
│   └── vector_store.py
├── services/
│   ├── chat.py
│   ├── conversation.py
│   ├── embedding.py
│   ├── feedback.py
│   └── visualization.py
├── tools/
│   └── sql_tool.py
├── ui/
│   ├── api_client.py
│   ├── app.py
│   └── pages/
│       └── 1_📊_Logs.py
└── utils/
    └── data_loader.py
```

### Test Structure (`tests/`)
```
tests/
├── agents/
│   ├── test_react_agent.py ✅
│   └── test_tools.py ✅
├── api/
│   ├── test_dependencies.py ✅
│   ├── test_main.py ✅
│   └── routes/
│       ├── test_chat.py ✅
│       ├── test_conversation.py ✅
│       ├── test_feedback.py ✅
│       └── test_health.py ✅
├── core/
│   ├── test_config.py ✅
│   ├── test_exceptions.py ✅
│   └── test_security.py ✅
├── models/
│   ├── test_chat.py ✅
│   ├── test_conversation.py ✅
│   ├── test_document.py ✅
│   ├── test_feedback.py ✅
│   └── test_nba.py ✅
├── pipeline/
│   ├── test_data_pipeline.py ✅
│   ├── test_models.py ✅
│   ├── test_quality_agent.py ✅
│   └── test_reddit_chunker.py ✅
├── repositories/
│   ├── test_conversation.py ✅
│   ├── test_feedback.py ✅
│   ├── test_nba_database.py ✅
│   └── test_vector_store.py ✅
├── services/
│   ├── test_chat.py ✅
│   ├── test_chat_service_flows.py ⚠️ (redundant?)
│   ├── test_chat_with_conversation.py ⚠️ (redundant?)
│   ├── test_conversation.py ✅
│   ├── test_embedding.py ✅
│   ├── test_evaluation_integration.py ⚠️ (should be in evaluation/)
│   ├── test_feedback.py ✅
│   ├── test_query_expansion.py ⚠️ (unclear mapping)
│   ├── test_stat_labels.py ⚠️ (unclear mapping)
│   ├── test_visualization_patterns.py ⚠️ (redundant?)
│   └── test_visualization_service.py ✅
├── tools/
│   └── test_sql_tool.py ✅
├── ui/
│   ├── test_api_client.py ✅
│   └── test_app.py ✅
├── utils/
│   └── test_data_loader.py ✅
├── e2e/ ✅ (end-to-end tests)
├── integration/ ✅ (integration tests)
├── evaluation/ ✅ (evaluation system tests)
├── ab_test_sql_formatting.py ❌ MISPLACED
└── test_ragas_implementation.py ❌ MISPLACED
```

---

## 🔴 Issues Found

### 1. **Missing Test Files** (Critical)

| Source File | Missing Test | Priority |
|-------------|--------------|----------|
| `src/agents/query_classifier.py` | `tests/agents/test_query_classifier.py` | **HIGH** - Core classification logic |
| `src/agents/results_formatter.py` | `tests/agents/test_results_formatter.py` | **MEDIUM** - Formatting logic |
| `src/core/logging_config.py` | `tests/core/test_logging_config.py` | **LOW** - Configuration only |

### 2. **Misplaced Test Files** (Organization)

| Current Location | Should Be | Reason |
|-----------------|-----------|---------|
| `tests/ab_test_sql_formatting.py` | `tests/agents/test_sql_formatting.py` or delete if obsolete | A/B test should be in relevant module |
| `tests/test_ragas_implementation.py` | `tests/evaluation/test_ragas_implementation.py` | RAGAS is part of evaluation system |

### 3. **Redundant/Unclear Test Files** (Cleanup)

| Test File | Issue | Recommendation |
|-----------|-------|----------------|
| `tests/services/test_chat_service_flows.py` | Overlaps with `test_chat.py` | Consider merging into `test_chat.py` |
| `tests/services/test_chat_with_conversation.py` | Overlaps with `test_chat.py` | Consider merging into `test_chat.py` |
| `tests/services/test_visualization_patterns.py` | Overlaps with `test_visualization_service.py` | Consider merging into `test_visualization_service.py` |
| `tests/services/test_query_expansion.py` | No clear source mapping | Check if belongs to agents or services |
| `tests/services/test_stat_labels.py` | No clear source mapping | Check if belongs to agents or services |
| `tests/services/test_evaluation_integration.py` | Wrong location | Move to `tests/evaluation/` or `tests/integration/` |

---

## ✅ Proposed Actions

### Phase 1: Create Missing Tests (High Priority)
1. Create `tests/agents/test_query_classifier.py`
2. Create `tests/agents/test_results_formatter.py`
3. Create `tests/core/test_logging_config.py` (optional)

### Phase 2: Move Misplaced Files
1. Move or delete `tests/ab_test_sql_formatting.py`
2. Move `tests/test_ragas_implementation.py` → `tests/evaluation/`

### Phase 3: Consolidate Redundant Tests
1. Review and possibly merge:
   - `test_chat.py`, `test_chat_service_flows.py`, `test_chat_with_conversation.py`
   - `test_visualization_service.py`, `test_visualization_patterns.py`
2. Clarify purpose of:
   - `test_query_expansion.py`
   - `test_stat_labels.py`
   - `test_evaluation_integration.py`

### Phase 4: Verify Coverage
1. Run coverage report: `poetry run pytest --cov=src --cov-report=term-missing`
2. Ensure all critical modules have >90% coverage

---

## 📝 Test File Naming Convention

**Rule**: `tests/{module_path}/test_{source_file}.py`

**Examples**:
- `src/agents/query_classifier.py` → `tests/agents/test_query_classifier.py`
- `src/services/chat.py` → `tests/services/test_chat.py`
- `src/api/routes/health.py` → `tests/api/routes/test_health.py`

---

## 🎯 Success Criteria

- [ ] Every source module has a corresponding test file
- [ ] No orphaned test files (tests without source files)
- [ ] Test directory structure mirrors source structure
- [ ] Test coverage >90% for critical modules
- [ ] All tests pass: `poetry run pytest tests/`

---

## 📊 Current Test Statistics

**Total Source Files**: ~45 Python modules
**Total Test Files**: ~90+ test files (including e2e, integration, evaluation)
**Missing Tests**: 3 critical files
**Misplaced Tests**: 2 files
**Redundant Tests**: ~5 files (need review)

---

## Next Steps

1. Review this analysis
2. Confirm which actions to take
3. Create missing test files
4. Move/consolidate redundant tests
5. Run full test suite to verify
