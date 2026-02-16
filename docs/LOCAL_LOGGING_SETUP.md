# Local Logging Setup - Quick Start

**✅ No external API required** - All logs stored locally with built-in web viewer

## Problem Solved

You were unable to use Logfire observability because the API key wasn't recognized. This local logging solution provides:

- ✅ **No external API dependencies** - works offline
- ✅ **Structured JSON logs** - machine-readable format
- ✅ **Built-in web viewer** - Streamlit interface to view/filter logs
- ✅ **Automatic rotation** - prevents disk space issues
- ✅ **Zero configuration** - works out of the box

## Quick Start

### 1. Test the Logging System

```bash
poetry run python scripts/test_local_logging.py
```

**Expected output**:
```
✅ app.log created
✅ api.log created
✅ agent.log created
✅ errors.log created
```

### 2. Start Your Application

The logging system is automatically initialized when you start the API or UI:

```bash
# Start API server
poetry run uvicorn src.api.main:app --reload

# Or start Streamlit UI
poetry run streamlit run src/ui/app.py
```

Logs will be automatically created in the `logs/` directory.

### 3. View Logs in Browser

```bash
poetry run streamlit run src/ui/app.py
```

Then navigate to **📊 Logs** page in the sidebar.

**Features**:
- 🔄 Auto-refresh every 5 seconds
- 🎯 Filter by log level (DEBUG, INFO, WARNING, ERROR)
- 🔍 Search in messages
- 📁 Switch between log files (app, api, agent, errors)
- 🎨 Color-coded by severity
- 📊 Expandable entries with full context

## Log Files

| File | Purpose |
|------|---------|
| `logs/app.log` | All application logs (DEBUG and above) |
| `logs/api.log` | API requests/responses |
| `logs/agent.log` | ReAct agent reasoning traces |
| `logs/errors.log` | Errors and critical issues only |

## Configuration (Optional)

### Disable Logfire (if needed)

Edit `.env` file:

```bash
LOGFIRE_ENABLED=false
```

The system will automatically use local logging.

### Change Log Level

Edit `.env` file:

```bash
# Options: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO
```

## Command Line Viewing

```bash
# Watch logs in real-time
tail -f logs/app.log

# View errors only
tail -f logs/errors.log

# Search for specific queries
grep "query processed" logs/app.log

# Pretty-print JSON logs
cat logs/app.log | python -m json.tool
```

## Example Log Entry

```json
{
    "timestamp": "2026-02-16T21:32:51.797593",
    "level": "INFO",
    "logger": "src.services.chat",
    "message": "Query processed: Who is the top scorer in the NBA?... (sql_only, 235ms)",
    "module": "chat",
    "function": "process_query",
    "line": 123,
    "conversation_id": "test-conv-123",
    "query": "Who is the top scorer in the NBA?",
    "query_type": "sql_only",
    "processing_time_ms": 234.56
}
```

## Troubleshooting

### No logs appearing?

1. Check log level: `LOG_LEVEL=DEBUG` in .env
2. Check permissions: Ensure write access to `logs/` directory
3. Restart application: Kill and restart the server

### Streamlit logs page not working?

1. Restart Streamlit: Kill the process and run again
2. Check if `logs/` directory exists with log files
3. Navigate to the sidebar and click **📊 Logs**

### Logs too verbose?

1. Set `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING` in .env
2. Use filters in Streamlit viewer (level, search)

## Full Documentation

See [docs/LOGGING.md](./LOGGING.md) for complete documentation including:
- Advanced configuration
- Programmatic log access
- Best practices
- Log rotation details
- Comparison with Logfire

## Benefits vs Logfire

| Feature | Local Logging | Logfire |
|---------|---------------|---------|
| API Key | ❌ Not needed | ✅ Required |
| Internet | ❌ Not needed | ✅ Required |
| Cost | Free | Paid (after free tier) |
| Setup | Zero config | Requires token |
| Offline | Works | Doesn't work |

**Recommendation**: Use local logging for development and when Logfire API is unavailable.
