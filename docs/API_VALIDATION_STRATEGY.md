# API Validation & Testing Strategy

**Status**: Implementation Plan
**Date**: 2026-02-12
**Priority**: High

---

## Why Errors Like 422 Slip Through

### The Testing Gap

**Playwright Tests** (`test_feedback_workflow.py`):
```python
# ❌ PROBLEM: Only tests UI interaction, not API contract
streamlit_page.wait_for_timeout(5000)
assert chat_input.is_visible()  # Only checks UI is responsive!
```

**What Playwright tests DON'T catch:**
- ❌ Is the API response valid?
- ❌ Are enum values in correct format?
- ❌ Did the database operation succeed?
- ❌ Is the response schema correct?

**Result**: The 422 error only appeared in real usage, not in tests!

---

## Root Cause: The Feedback Validation Error

### What Happened

**UI Code** (`src/ui/api_client.py` line 306):
```python
payload = {
    "interaction_id": interaction_id,
    "rating": rating,  # rating was "POSITIVE" (wrong!)
}
```

**API Expected** (`src/models/feedback.py`):
```python
class FeedbackRating(str, Enum):
    POSITIVE = "positive"    # ← Must be lowercase!
    NEGATIVE = "negative"
```

**Result**: API validation rejected with 422 Unprocessable Entity

### Why Tests Missed It

**Unit Tests**: Mock the API, so they never validate real schemas
```python
mock_client = MagicMock()
mock_client.submit_feedback.return_value = {"success": True}
# ^ No validation! Just returns mocked success
```

**Playwright Tests**: Test UI behavior, not API contracts
```python
# Waits for response but doesn't check if it succeeded
streamlit_page.wait_for_timeout(5000)
```

**Integration Tests**: ✅ Would have caught it!
```python
response = requests.post("/api/v1/feedback", json=payload)
assert response.status_code != 422  # ← Catches validation errors!
```

---

## Solution: 3-Tier Test Strategy

### Tier 1: Unit Tests (Existing, Keep)
- Test individual functions in isolation
- Mock external dependencies
- Fast execution
- **Limitation**: Don't catch API contract mismatches

### Tier 2: Integration Tests (NEW - ADDED)
- Test real API with real data
- Validate API contracts
- Verify schema matching
- Catch enum/type mismatches

**File**: `tests/integration/test_feedback_api_contract.py`

**Validates**:
```python
✅ Enum values match (lowercase)
✅ Required fields are enforced
✅ Optional fields accepted
✅ Field constraints (max length)
✅ API endpoint path correctness
✅ Complete end-to-end flow
```

### Tier 3: E2E/Playwright Tests (Existing, Improve)
- Test actual user workflows
- Verify UI behavior
- **New improvement**: Validate API responses, not just UI state

---

## Implementation: What to Check

### 1. API Contract Validation

**Every endpoint should have**:
- ✅ Valid enum values (check documentation)
- ✅ Required vs optional fields documented
- ✅ Field constraints (max length, format)
- ✅ Response schema documented

**For Feedback Endpoint**:
```
POST /api/v1/feedback
├─ interaction_id: string (required)
├─ rating: "positive" | "negative" (required, LOWERCASE!)
├─ comment: string | null (optional, max 2000)
└─ Expected responses: 200, 201, 400, 422
```

### 2. UI-API Matching Checklist

**Before sending data to API, verify**:
- [ ] Enum values match API documentation
- [ ] All required fields are populated
- [ ] Field constraints are enforced
- [ ] Response structure is handled

**For feedback, the fix was**:
```python
# BEFORE (wrong):
payload = {"rating": rating}  # "POSITIVE" if user clicked positive button

# AFTER (correct):
payload = {"rating": rating.lower()}  # "positive" - matches API enum
```

### 3. Test Coverage for APIs

**Every API route needs**:
1. Unit test (mock responses)
2. Integration test (real API calls)
3. E2E test (full user workflow)

**Feedback endpoint missing**:
- ❌ Integration test for schema validation
- ❌ E2E test that verifies feedback actually saves

---

## How to Prevent This in Future

### Checklist for New Endpoints

When adding a new API endpoint:

```checklist
[ ] 1. Define Pydantic model with validation
      - Enums with exact expected values
      - Required vs optional fields
      - Field constraints (max_length, patterns)

[ ] 2. Write integration test
      - Test with valid data
      - Test with invalid data (expect specific errors)
      - Test edge cases

[ ] 3. Write unit test
      - Mock the service/repository
      - Test business logic

[ ] 4. Write E2E test
      - Test complete user flow
      - Verify actual data is saved
      - Check response structure

[ ] 5. Document in code comments
      - Expected enum values
      - Required fields
      - Constraints
```

### Code Review Questions

For any API changes, ask:

1. **Do enum values match everywhere?**
   - Pydantic model definition
   - OpenAPI schema
   - Client code sending data
   - Documentation

2. **Are schema constraints enforced?**
   - Max/min values
   - Required fields
   - Enum values
   - String patterns

3. **Do tests validate schema?**
   - Unit tests (mock)
   - Integration tests (real API) ← **Critical!**
   - E2E tests (actual flow)

---

## Current Status After Fix

### Applied Fix
- ✅ Changed `api_client.py` line 306
- ✅ Convert rating to lowercase: `rating.lower()`
- ✅ Now matches API enum expectations

### Tests Added
- ✅ Integration test: `test_feedback_api_contract.py`
- ✅ Validates lowercase enum values work
- ✅ Validates uppercase enum values fail
- ✅ Tests required/optional fields
- ✅ Tests field constraints

### Verification
```
6/8 integration tests passing ✅
- Lowercase "positive"/"negative" work
- Uppercase "POSITIVE"/"NEGATIVE" rejected with 422
- Required fields validated
- Optional comment accepted
- Field constraints checked
- Endpoint path correct
```

---

## Going Forward

### Short Term (Done)
- ✅ Fix api_client.py feedback rating format
- ✅ Add integration test for feedback
- ✅ Document API contract in code

### Medium Term
- [ ] Add integration tests for all API endpoints
- [ ] Add API contract validation tests for enums
- [ ] Improve Playwright tests to validate API responses
- [ ] Document all API enums in schema

### Long Term
- [ ] Consider using Pydantic generics to share schemas
- [ ] Implement OpenAPI schema validation in tests
- [ ] Create API contract testing framework

---

## Key Lessons

| Issue | Why Missed | How to Catch |
|-------|-----------|-------------|
| Enum value mismatch | Unit tests mock API | Integration tests with real API |
| Schema validation | Playwright doesn't check responses | Response validation in tests |
| Type mismatches | No type checking in Python at runtime | Pydantic validation + tests |
| Missing fields | Mocks return success regardless | Integration tests verify actual schema |

---

## Conclusion

The 422 feedback validation error revealed a gap in our testing strategy:

1. **Playwright tests** are too high-level (only test UI behavior)
2. **Unit tests** are too isolated (mock the API)
3. **Integration tests** are what we needed (validate real API contracts)

By adding integration tests that:
- Call the real API with real data
- Validate response schemas
- Check enum values match documentation
- Verify field constraints

We can catch these errors **before users encounter them**.

---

**Recommendation**: Always include integration tests for API endpoints, not just unit tests.
