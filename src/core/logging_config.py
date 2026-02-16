"""
FILE: logging_config.py
STATUS: Active
RESPONSIBILITY: Local structured logging with rotation and JSON formatting
LAST MAJOR UPDATE: 2026-02-16
MAINTAINER: Shahu
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from src.core.config import settings


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON string with structured log data
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields (conversation_id, query, etc.)
        if hasattr(record, "conversation_id"):
            log_data["conversation_id"] = record.conversation_id
        if hasattr(record, "query"):
            log_data["query"] = record.query
        if hasattr(record, "query_type"):
            log_data["query_type"] = record.query_type
        if hasattr(record, "processing_time_ms"):
            log_data["processing_time_ms"] = record.processing_time_ms

        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for human-readable logs."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console output.

        Args:
            record: Log record to format

        Returns:
            Colored log string
        """
        # Don't modify record - create colored strings directly
        color = self.COLORS.get(record.levelname, self.RESET)
        colored_level = f"{color}{record.levelname}{self.RESET}"
        colored_time = f"{color}{self.formatTime(record)}{self.RESET}"
        colored_logger = f"{color}{record.name}{self.RESET}"

        # Format: timestamp - level - logger - message
        formatted = (
            f"{colored_time} - "
            f"{colored_level} - "
            f"{colored_logger} - "
            f"{record.getMessage()}"
        )

        # Add exception if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"

        return formatted


def configure_local_logging(
    log_dir: str | Path = "logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB per file
    backup_count: int = 5,  # Keep 5 backup files
) -> None:
    """Configure local file-based logging with rotation.

    Creates separate log files for different components:
    - app.log: All application logs (JSON format)
    - api.log: API-specific logs (JSON format)
    - errors.log: Error and critical logs only (JSON format)
    - console: Human-readable colored output

    Args:
        log_dir: Directory to store log files
        max_bytes: Maximum size per log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create logs directory
    log_dir = Path(log_dir)
    log_dir.mkdir(exist_ok=True, parents=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Clear existing handlers
    root_logger.handlers.clear()

    # 1. CONSOLE HANDLER - Colored human-readable output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredConsoleFormatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 2. MAIN APP LOG - All logs in JSON format
    app_handler = logging.handlers.RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.DEBUG)
    app_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(app_handler)

    # 3. ERROR LOG - Errors and critical only
    error_handler = logging.handlers.RotatingFileHandler(
        log_dir / "errors.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(error_handler)

    # 4. API LOG - API-specific logs
    api_logger = logging.getLogger("src.api")
    api_handler = logging.handlers.RotatingFileHandler(
        log_dir / "api.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    api_handler.setLevel(logging.DEBUG)
    api_handler.setFormatter(StructuredFormatter())
    api_logger.addHandler(api_handler)

    # 5. AGENT LOG - ReAct agent reasoning traces
    agent_logger = logging.getLogger("src.agents")
    agent_handler = logging.handlers.RotatingFileHandler(
        log_dir / "agent.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    agent_handler.setLevel(logging.DEBUG)
    agent_handler.setFormatter(StructuredFormatter())
    agent_logger.addHandler(agent_handler)

    logging.info("✓ Local structured logging configured successfully")
    logging.info(f"✓ Log files: {log_dir.absolute()}")


def get_recent_logs(
    log_file: str | Path = "logs/app.log",
    lines: int = 100,
    level: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """Read recent logs from file with optional filtering.

    Args:
        log_file: Path to log file
        lines: Number of recent lines to read
        level: Filter by log level (DEBUG, INFO, WARNING, ERROR)
        search: Filter by text search in message

    Returns:
        List of log entries as dictionaries
    """
    log_file = Path(log_file)
    if not log_file.exists():
        return []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            # Read last N lines efficiently
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]

        logs = []
        for line in recent_lines:
            try:
                log_entry = json.loads(line.strip())

                # Apply filters
                if level and log_entry.get("level") != level:
                    continue
                if search and search.lower() not in log_entry.get("message", "").lower():
                    continue

                logs.append(log_entry)
            except json.JSONDecodeError:
                # Skip malformed JSON lines
                continue

        return logs

    except Exception as e:
        logging.error(f"Failed to read logs: {e}")
        return []


def log_query_event(
    logger: logging.Logger,
    query: str,
    query_type: str,
    processing_time_ms: float,
    conversation_id: str | None = None,
    level: int = logging.INFO,
) -> None:
    """Log a query event with structured extra fields.

    Args:
        logger: Logger instance
        query: User query
        query_type: Query type (sql_only, vector_only, hybrid)
        processing_time_ms: Processing time in milliseconds
        conversation_id: Conversation ID (optional)
        level: Log level (default: INFO)
    """
    extra = {
        "query": query,
        "query_type": query_type,
        "processing_time_ms": processing_time_ms,
    }
    if conversation_id:
        extra["conversation_id"] = conversation_id

    logger.log(
        level,
        f"Query processed: {query[:100]}... ({query_type}, {processing_time_ms:.0f}ms)",
        extra=extra,
    )
