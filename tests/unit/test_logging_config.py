import json
import logging
from typing import Any

from bac_generator.core.logging_config import JsonFormatter, log_event


class CapturingHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def test_json_formatter_emits_request_id_and_safe_event_fields() -> None:
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="operation completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.event = "retrieval_completed"
    record.provider = "pinecone"
    record.retrieved_document_count = 5

    payload = json.loads(JsonFormatter().format(record))

    assert payload["event"] == "retrieval_completed"
    assert payload["request_id"] == "request-123"
    assert payload["provider"] == "pinecone"
    assert payload["retrieved_document_count"] == 5
    assert "pathname" not in payload


def test_log_event_drops_unknown_and_sensitive_fields() -> None:
    logger = logging.getLogger("test.safe-event")
    handler = CapturingHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    try:
        log_event(
            logger,
            "generation_started",
            provider="gemini",
            model="gemini-2.5-flash",
            raw_token="secret-token",
            prompt="private prompt",
        )
    finally:
        logger.removeHandler(handler)

    assert len(handler.records) == 1
    record: Any = handler.records[0]
    assert record.event == "generation_started"
    assert record.provider == "gemini"
    assert record.model == "gemini-2.5-flash"
    assert not hasattr(record, "raw_token")
    assert not hasattr(record, "prompt")
