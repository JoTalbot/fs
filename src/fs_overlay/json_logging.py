"""Small structured JSON logging adapter for local FS processes."""
from __future__ import annotations

import json
import logging
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """Render log records as one deterministic JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        fields = getattr(record, "fs_fields", None)
        if fields is not None:
            if not isinstance(fields, dict):
                raise TypeError("fs_fields must be a dictionary")
            payload["fields"] = dict(sorted(fields.items()))
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def configure_json_logging(
    logger: logging.Logger | None = None,
    *,
    level: int = logging.INFO,
    handler: logging.Handler | None = None,
) -> logging.Logger:
    """Configure exactly one FS JSON handler without disturbing other handlers."""
    target = logger or logging.getLogger("fs_overlay")
    if handler is None:
        handler = logging.StreamHandler()
    handler.setFormatter(JsonLogFormatter())
    handler.setLevel(level)
    target.setLevel(level)
    target.addHandler(handler)
    return target


def log_event(logger: logging.Logger, level: int, message: str, **fields: Any) -> None:
    """Emit a structured event without flattening application fields into text."""
    logger.log(level, message, extra={"fs_fields": fields})
