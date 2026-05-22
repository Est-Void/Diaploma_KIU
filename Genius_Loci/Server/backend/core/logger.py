"""
Structured logging module for Genius Loci Server.
Provides centralized logging with JSON output for remote analysis.
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "context"):
            log_obj["context"] = record.context
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, ensure_ascii=False)


class ContextAdapter(logging.LoggerAdapter):
    """Logger adapter that adds context to every log record."""

    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["context"] = self.extra.get("context", {})
        return msg, kwargs


# Global logger registry
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(
    level: int = logging.DEBUG,
    log_file: Optional[str] = None,
    use_json: bool = False,
    log_dir: str = "logs"
) -> None:
    """Configure global logging settings."""
    if log_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        file_path = Path(log_dir) / log_file
        handlers.append(logging.FileHandler(file_path, encoding="utf-8"))

    formatter = JSONFormatter() if use_json else logging.Formatter(
        "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s"
    )

    for handler in handlers:
        handler.setFormatter(formatter)

    root_logger = logging.getLogger("Server")
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    for handler in handlers:
        root_logger.addHandler(handler)


def get_logger(name: str, context: Optional[Dict[str, Any]] = None) -> ContextAdapter:
    """Get a named logger with optional context."""
    logger = logging.getLogger(f"Server.{name}")

    if name not in _loggers:
        _loggers[name] = logger

    ctx = context or {}
    ctx.setdefault("module", name)

    return ContextAdapter(logger, {"context": ctx})
