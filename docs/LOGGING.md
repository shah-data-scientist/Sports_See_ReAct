# Local Logging System

**No external API required** - All logs are stored locally with structured JSON format and built-in viewer.

## Overview

The application uses a **hybrid logging approach**:

1. **Primary**: Local file-based logging (JSON format, rotating files)
2. **Optional**: Logfire external observability (requires API token)

If Logfire is not configured or fails, the system automatically falls back to local logging.

## Features

✅ **Structured JSON Logs** - Machine-readable with consistent schema
✅ **Log Rotation** - Automatic rotation at 10MB per file (keeps 5 backups)
✅ **Separate Log Files** - Different files for app, api, agent, errors
✅ **Colored Console Output** - Human-readable colored logs in terminal
✅ **Built-in Viewer** - Streamlit web interface to view/filter logs
✅ **Contextual Fields** - Query, conversation_id, processing_time, etc.
✅ **No External Dependencies** - Works offline, no API keys needed

## Log Files

| File | Purpose | Content |
|------|---------|---------|
| `logs/app.log` | All application logs | DEBUG and above from all modules |
| `logs/api.log` | API-specific logs | Requests, responses, errors |
| `logs/agent.log` | ReAct agent logs | Reasoning traces, tool calls |
| `logs/errors.log` | Errors only | ERROR and CRITICAL from all modules |

## Configuration

### Environment Variables (.env)

```bash
# Log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Optional: Logfire (external observability)
LOGFIRE_ENABLED=false
LOGFIRE_TOKEN=your_token_here  # Optional
```

### Programmatic Configuration

```python
from src.core.logging_config import configure_local_logging

# Configure with defaults (logs/ directory, 10MB rotation, 5 backups)
configure_local_logging()

# Or customize
configure_local_logging(
    log_dir="custom_logs",
    max_bytes=20 * 1024 * 1024,  # 20MB per file
    backup_count=10,  # Keep 10 backups
)
```

## Usage

### Basic Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Detailed trace information")
logger.info("General information")
logger.warning("Warning: potential issue")
logger.error("Error occurred")
logger.critical("Critical failure")
```

### Structured Logging with Context

```python
from src.core.logging_config import log_query_event

# Log a query with structured extra fields
log_query_event(
    logger=logger,
    query="Who is the top scorer?",
    query_type="sql_only",
    processing_time_ms=234.56,
    conversation_id="conv-123",
)
```

This creates a JSON log entry like:

```json
{
  "timestamp": "2026-02-16T14:30:45.123456",
  "level": "INFO",
  "logger": "src.services.chat",
  "message": "Query processed: Who is the top scorer?... (sql_only, 235ms)",
  "module": "chat",
  "function": "process_query",
  "line": 123,
  "query": "Who is the top scorer?",
  "query_type": "sql_only",
  "processing_time_ms": 234.56,
  "conversation_id": "conv-123"
}
```

### Exception Logging

```python
try:
    result = process_query(query)
except Exception as e:
    logger.exception("Query processing failed")  # Includes full stack trace
```

## Viewing Logs

### Option 1: Streamlit Web Viewer (Recommended)

```bash
poetry run streamlit run src/ui/app.py
```

Then navigate to **📊 Logs** page in the sidebar.

**Features**:
- ✅ Real-time viewing with auto-refresh (5s)
- ✅ Filter by log level (DEBUG, INFO, WARNING, ERROR)
- ✅ Search in messages
- ✅ View different log files (app, api, agent, errors)
- ✅ Color-coded by severity
- ✅ Expandable entries with full details
- ✅ View raw JSON for each log entry

### Option 2: Command Line

```bash
# View recent logs (colored output)
tail -f logs/app.log

# View errors only
tail -f logs/errors.log

# View API logs
tail -f logs/api.log

# Search for specific queries
grep "top scorer" logs/app.log
```

### Option 3: Programmatic Access

```python
from src.core.logging_config import get_recent_logs

# Get last 100 logs
logs = get_recent_logs("logs/app.log", lines=100)

# Filter by level
error_logs = get_recent_logs("logs/app.log", level="ERROR")

# Search in messages
search_results = get_recent_logs("logs/app.log", search="query processed")

# Process logs
for log in logs:
    print(f"{log['timestamp']} - {log['level']} - {log['message']}")
```

## Log Structure

Each JSON log entry contains:

```python
{
    "timestamp": str,       # ISO 8601 format
    "level": str,          # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "logger": str,         # Logger name (e.g., src.services.chat)
    "message": str,        # Log message
    "module": str,         # Python module name
    "function": str,       # Function name
    "line": int,          # Line number

    # Optional context fields
    "query": str,                    # User query
    "query_type": str,               # sql_only, vector_only, hybrid
    "conversation_id": str,          # Conversation ID
    "processing_time_ms": float,     # Processing time
    "exception": str,                # Exception trace (if error)
}
```

## Testing

```bash
# Test logging configuration
poetry run python scripts/test_local_logging.py

# Expected output:
# ✅ app.log created
# ✅ api.log created
# ✅ agent.log created
# ✅ errors.log created
```

## Log Rotation

Logs automatically rotate when they reach 10MB:

```
logs/
├── app.log           # Current log
├── app.log.1         # 1st backup (10MB)
├── app.log.2         # 2nd backup (10MB)
├── app.log.3         # 3rd backup (10MB)
├── app.log.4         # 4th backup (10MB)
├── app.log.5         # 5th backup (10MB - oldest, will be deleted on next rotation)
```

**Total storage**: ~60MB per log file (6 × 10MB)

## Troubleshooting

### Logs not appearing

1. **Check log level**: Set `LOG_LEVEL=DEBUG` in .env for verbose logging
2. **Check permissions**: Ensure write permissions for logs/ directory
3. **Check disk space**: Ensure sufficient disk space available

### Streamlit logs page not working

1. **Check Streamlit pages**: Ensure `src/ui/pages/` directory exists
2. **Restart Streamlit**: Kill and restart the Streamlit server
3. **Check logs directory**: Ensure `logs/` directory exists and contains log files

### Logs too verbose

1. **Increase log level**: Set `LOG_LEVEL=INFO` or `LOG_LEVEL=WARNING`
2. **Reduce retention**: Decrease `backup_count` in logging config
3. **Filter in viewer**: Use Streamlit viewer filters to show only relevant logs

## Best Practices

1. **Use appropriate log levels**:
   - `DEBUG`: Detailed tracing for debugging
   - `INFO`: General information (query processing, startup)
   - `WARNING`: Potential issues (fallbacks, retries)
   - `ERROR`: Actual errors (exceptions, failures)
   - `CRITICAL`: Critical failures (system shutdown)

2. **Include context**: Use extra fields for structured logging
   ```python
   logger.info("Query processed", extra={
       "query": query,
       "query_type": "sql_only",
       "processing_time_ms": 234.56,
   })
   ```

3. **Log exceptions properly**: Use `logger.exception()` for full stack traces
   ```python
   try:
       result = process()
   except Exception:
       logger.exception("Processing failed")  # Includes stack trace
   ```

4. **Avoid sensitive data**: Don't log API keys, passwords, or PII
   ```python
   # ❌ Bad
   logger.info(f"API key: {api_key}")

   # ✅ Good
   logger.info("API authentication successful")
   ```

## Comparison with Logfire

| Feature | Local Logging | Logfire |
|---------|---------------|---------|
| **Setup** | Zero config | Requires API token |
| **Cost** | Free | Paid (after free tier) |
| **Offline** | ✅ Yes | ❌ No (requires internet) |
| **Performance** | Fast (local I/O) | Slower (network calls) |
| **Viewer** | Streamlit (built-in) | Web dashboard |
| **Retention** | ~60MB per log file | Cloud-based (longer) |
| **Search** | Basic (grep, viewer) | Advanced (full-text) |
| **Traces** | Structured logs | Distributed tracing |

**Recommendation**: Use **local logging** for development and small deployments. Use **Logfire** for production with advanced observability needs.

## Migration from Logfire

If you were using Logfire and want to switch to local logging:

1. **Disable Logfire** in .env:
   ```bash
   LOGFIRE_ENABLED=false
   ```

2. **Remove token** (optional):
   ```bash
   # LOGFIRE_TOKEN=your_token_here  # Comment out
   ```

3. **Restart application** - automatically falls back to local logging

4. **View logs** in Streamlit at 📊 Logs page

No code changes needed - fallback is automatic!
