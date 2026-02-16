# Test Alignment Implementation Plan

**Date**: 2026-02-16
**Principle**: Only create/modify tests for code that has actually changed

---

## 🎯 Alignment Rules

### 1:1 Correspondence Rule
**Every source file MUST have exactly ONE test file:**

```
src/{module}/{file}.py  →  tests/{module}/test_{file}.py
```

### Examples:
- `src/agents/query_classifier.py` → `tests/agents/test_query_classifier.py`
- `src/services/chat.py` → `tests/services/test_chat.py`
- `src/api/routes/health.py` → `tests/api/routes/test_health.py`

---

## 📋 Current Status Check

### Source Files Analysis
```bash
# Count source files
find src -type f -name "*.py" -not -path "*/__pycache__/*" | wc -l
# Result: ~45 Python modules
```

### Test Files Analysis
```bash
# Count test files (excluding e2e, integration, evaluation)
find tests -type f -name "test_*.py" -not -path "*/e2e/*" -not -path "*/integration/*" -not -path "*/evaluation/*" | wc -l
# Result: ~45 test files
```

---

## 🔍 Missing Tests Identified

### Priority 1: Core Agent Files
1. ✅ `src/agents/query_classifier.py` - EXISTS (but imported incorrectly in tests)
2. ✅ `src/agents/results_formatter.py` - EXISTS (used in react_agent)
3. ✅ `src/agents/react_agent.py` - HAS TEST (tests/agents/test_react_agent.py)
4. ✅ `src/agents/tools.py` - HAS TEST (tests/agents/test_tools.py)

### Priority 2: Core Modules
All core modules have corresponding tests ✅

### Priority 3: Services
All service modules have corresponding tests ✅

---

## 🚨 Issues Found

### Issue 1: Import Path Mismatch
**Location**: `tests/services/test_chat.py`
**Problem**: Tests try to import `from src.services.query_classifier import QueryClassifier`
**Reality**: QueryClassifier is in `src.agents.query_classifier`
**Status**: This will cause test failures

### Issue 2: Misplaced Files
1. `tests/ab_test_sql_formatting.py` - Root level (should be in agents or deleted)
2. `tests/test_ragas_implementation.py` - Root level (should be in evaluation/)

### Issue 3: Redundant Test Files
Multiple test files for same functionality:
- `tests/services/test_chat.py`
- `tests/services/test_chat_service_flows.py`
- `tests/services/test_chat_with_conversation.py`

---

## ✅ Action Plan

### Phase 1: Fix Broken Imports (CRITICAL)
1. Check test failures from pytest suite
2. Fix import paths in failing tests
3. Ensure all tests can import correctly

### Phase 2: Move Misplaced Files
```bash
# Move root-level test files to appropriate locations
mv tests/test_ragas_implementation.py tests/evaluation/
# Delete or move ab_test_sql_formatting.py based on relevance
```

### Phase 3: Create Missing Tests (ONLY IF NEEDED)
- Only create tests for files that:
  1. Have NO test coverage
  2. Have recently changed
  3. Are critical to functionality

### Phase 4: Consolidate Redundant Tests (OPTIONAL)
- Review and possibly merge redundant test files
- Ensure no duplicate test coverage

### Phase 5: Verify Coverage
```bash
# Run coverage report
poetry run pytest --cov=src --cov-report=term-missing --cov-report=html

# Target coverage:
# - Critical modules (agents, services, repositories): >90%
# - Models (Pydantic validation): >80%
# - Utils: >70%
```

---

## 🧪 Test Execution Plan

### 1. Unit Tests (Fast)
```bash
poetry run pytest tests/core/ tests/models/ tests/repositories/ tests/services/ tests/agents/ -v
```

### 2. Integration Tests
```bash
poetry run pytest tests/integration/ -v
```

### 3. E2E Tests
```bash
poetry run pytest tests/e2e/ -v --maxfail=3
```

### 4. UI Tests (Slowest - requires Streamlit running)
```bash
# Terminal 1: Start Streamlit
poetry run streamlit run src/ui/app.py

# Terminal 2: Run UI tests
poetry run pytest tests/ui/ -v
```

### 5. Evaluation Tests
```bash
poetry run pytest tests/evaluation/ -v
```

---

## 📊 Success Metrics

- [ ] All pytest tests pass
- [ ] No import errors
- [ ] 1:1 correspondence between src/ and tests/
- [ ] Coverage >85% overall
- [ ] E2E tests pass
- [ ] UI tests pass (if Streamlit is running)

---

## 🚫 What NOT to Do

### DON'T:
1. ❌ Create tests just to pass CI if production code has flaws
2. ❌ Modify tests to match broken production code
3. ❌ Create redundant test files
4. ❌ Test implementation details (test behavior, not internals)
5. ❌ Mock everything (use real dependencies when reasonable)

### DO:
1. ✅ Fix production code if it's broken
2. ✅ Create tests that verify correct behavior
3. ✅ Use clear test names that describe behavior
4. ✅ Follow AAA pattern (Arrange, Act, Assert)
5. ✅ Test edge cases and error conditions

---

## 📝 Notes

- Tests running in background (ID: ba71a37)
- Will review failures before making any changes
- Principle: Fix code, not tests (unless tests are wrong)
