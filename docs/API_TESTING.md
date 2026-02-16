# API Testing Guide

Quick guide to test the API works for all query types.

## Prerequisites

1. **API server must be running**
2. **Vector index must be loaded** (run indexer if needed)
3. **Environment variables set** in `.env`

## Quick Test (Recommended)

### Step 1: Start API Server

```bash
# Terminal 1
poetry run uvicorn src.api.main:app --reload --port 8000
```

Wait for: `✓ Local structured logging configured successfully`

### Step 2: Run Tests

```bash
# Terminal 2
poetry run python scripts/test_api_simple.py
```

## Expected Output

```
======================================================================
API TEST - All Query Types
======================================================================

✅ API is running

======================================================================
TEST 1: SQL Query (Top Scorers)
======================================================================
Query: Who are the top 5 scorers this season?

✅ Answer: Based on the data, here are the top 5 scorers this season:
1. Shai Gilgeous-Alexander - 30.3 PPG
2. Giannis Antetokounmpo - 30.2 PPG
...
⏱️  Time: 2345ms
🗄️  SQL: SELECT name, ppg FROM players ORDER BY ppg DESC LIMIT 5

======================================================================
TEST 2: Vector Query (Fan Opinion)
======================================================================
Query: Why do fans consider LeBron James great?

✅ Answer: Fans consider LeBron James one of the greatest because...
⏱️  Time: 1876ms

======================================================================
TEST 3: Hybrid Query (Player Bio)
======================================================================
Query: Who is Nikola Jokic?

✅ Answer: Nikola Jokic is a Serbian professional basketball player...
⏱️  Time: 3210ms

======================================================================
TEST 4: Conversational Query (Follow-up)
======================================================================
Initial: Who scored the most points?
✅ Answer: Shai Gilgeous-Alexander scored the most points...

Follow-up: What about his assists?
✅ Answer: Shai Gilgeous-Alexander averages 6.2 assists per game...
⏱️  Time: 1965ms

======================================================================
SUMMARY
======================================================================
✅ PASS SQL Query
✅ PASS Vector Query
✅ PASS Hybrid Query
✅ PASS Conversational Query

Total: 4/4 tests passed (100%)

🎉 All query types working correctly!
```

## What Each Test Validates

### 1. SQL Query
- **Query Type**: Statistical questions (rankings, stats, comparisons)
- **Data Source**: SQLite database
- **Validation**:
  - Returns player statistics
  - Generates SQL query
  - Includes numerical data

### 2. Vector Query
- **Query Type**: Contextual questions (opinions, explanations, discussions)
- **Data Source**: FAISS vector store (Reddit discussions)
- **Validation**:
  - Returns contextual answer
  - No SQL generated
  - Provides reasoning/opinions

### 3. Hybrid Query
- **Query Type**: Questions needing both stats AND context (biographical)
- **Data Source**: Both database and vector store
- **Validation**:
  - Returns comprehensive answer
  - May include both stats and context
  - Longer, detailed response

### 4. Conversational Query
- **Query Type**: Follow-up questions with pronouns ("he", "his", "them")
- **Data Source**: Uses conversation history + appropriate data source
- **Validation**:
  - Resolves pronoun references
  - Maintains conversation context
  - Returns relevant follow-up answer

## Troubleshooting

### API not responding

**Problem**: `❌ API is not running!`

**Solution**:
```bash
# Start API server in Terminal 1
poetry run uvicorn src.api.main:app --reload --port 8000
```

### Import errors

**Problem**: `ModuleNotFoundError: No module named 'src.core.observability'`

**Solution**: Observability was removed. Check latest code:
```bash
git pull
git log --oneline -5  # Should show observability removal commit
```

### Timeout errors

**Problem**: `Request timed out (>60s)`

**Possible causes**:
1. **LLM API rate limit** - Wait a few minutes and retry
2. **Vector index not loaded** - Check server logs for index loading
3. **Database not found** - Run `poetry run python -m src.pipeline.data_pipeline`

**Check logs**:
```bash
tail -f logs/api.log    # API requests
tail -f logs/errors.log # Errors only
```

### Conversation context not working

**Problem**: Follow-up query doesn't understand pronouns

**Check**:
1. Conversation ID is being passed correctly
2. Turn numbers are sequential (1, 2, 3, ...)
3. Database has conversation storage enabled

**Test manually**:
```bash
# First query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Who scored the most points?", "conversation_id": "test-123", "turn_number": 1}'

# Follow-up query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What about his assists?", "conversation_id": "test-123", "turn_number": 2}'
```

## Advanced Testing

### Test with curl

```bash
# SQL query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Top 5 scorers this season"}' | python -m json.tool

# Vector query
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Why is LeBron great?"}' | python -m json.tool
```

### Test with Python requests

```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"query": "Who are the top scorers?"}
)

print(response.json()["answer"])
```

### View Logs in Real-Time

```bash
# All logs
tail -f logs/app.log

# Errors only
tail -f logs/errors.log

# API requests only
tail -f logs/api.log

# Agent reasoning
tail -f logs/agent.log
```

## Performance Benchmarks

Expected response times:

| Query Type | Expected Time | Notes |
|------------|---------------|-------|
| SQL Query | 1-3 seconds | Depends on query complexity |
| Vector Query | 1-2 seconds | Depends on k (number of results) |
| Hybrid Query | 2-4 seconds | Both searches + LLM synthesis |
| Conversational | 1-3 seconds | Plus conversation retrieval |

If queries take >10 seconds consistently, check:
- LLM API rate limits
- Network latency
- Database/index size

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Test API
  run: |
    poetry run uvicorn src.api.main:app --port 8000 &
    sleep 10
    poetry run python scripts/test_api_simple.py
```

## Related Documentation

- [Local Logging Setup](./LOCAL_LOGGING_SETUP.md) - View API logs
- [API Documentation](http://localhost:8000/docs) - Swagger UI (when server running)
- [ReDoc](http://localhost:8000/redoc) - Alternative API docs
