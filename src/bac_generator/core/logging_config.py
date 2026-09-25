import json
import logging
from datetime import UTC, datetime
from typing import Any

from bac_generator.core.request_context import get_request_id


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


EVENT_FIELDS = frozenset(
    {
        "event",
        "request_id",
        "exercise_id",
        "user_hash",
        "topic",
        "difficulty",
        "retrieved_document_count",
        "retrieval_latency_ms",
        "generation_latency_ms",
        "sandbox_latency_ms",
        "persistence_latency_ms",
        "total_latency_ms",
        "retry_count",
        "provider",
        "model",
        "exception_type",
        "safe_error_message",
        "method",
        "path",
        "status_code",
    }
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=UTC,
            ).isoformat(),
            "severity": record.levelname,
            "logger": record.name,
            "message": str(
                getattr(record, "event", "unstructured_log")
            ),
            "request_id": getattr(record, "request_id", get_request_id()),
        }

        for field in EVENT_FIELDS:
            if field == "request_id":
                continue
            if hasattr(record, field):
                payload[field] = getattr(record, field)

        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    message: str | None = None,
    **fields: object,
) -> None:
    safe_fields = {
        key: value
        for key, value in fields.items()
        if key in EVENT_FIELDS and key not in {"event", "request_id"}
    }
    logger.log(
        level,
        message or event,
        extra={"event": event, **safe_fields},
    )


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIDFilter())

    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)
