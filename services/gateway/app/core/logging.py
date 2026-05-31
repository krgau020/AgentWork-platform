"""
Structured Logging (app/core/logging.py)

Purpose:
    Configures the root Python logger to emit JSON-formatted log lines.
    Every log message across the gateway becomes a single JSON object —
    machine-readable, searchable, and compatible with log aggregation tools
    (Datadog, ELK, Loki, CloudWatch, etc.).

JSON log format:
    {
      "timestamp":   "2026-05-23T08:15:00.123456+00:00",
      "service":     "gateway",
      "level":       "INFO",
      "message":     "request",
      "method":      "GET",
      "path":        "/api/v1/users",
      "status":      200,
      "duration_ms": 45,
      "request_id":  "3f2a1b4c-8d2e-4f1a-b3c9-..."
    }

Why configure at startup:
    Calling configure_logging() in main.py replaces the default uvicorn
    text formatter before any request is served. All subsequent log calls
    (including from middleware, rate_limiter, etc.) use JSON automatically.
"""

import json
import logging
from datetime import datetime, timezone

_SERVICE_NAME = "gateway"


class JsonFormatter(logging.Formatter):
    """Formats every log record as a single-line JSON string."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": _SERVICE_NAME,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            if hasattr(record, key):
                entry[key] = getattr(record, key)
        return json.dumps(entry)


def configure_logging(service_name: str = "gateway") -> None:
    """
    Replace the root logger's handlers with a single JSON stream handler.
    Call once at application startup (main.py) before the app starts serving.
    """
    global _SERVICE_NAME
    _SERVICE_NAME = service_name
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)
