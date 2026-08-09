import logging

from bac_generator.core.request_context import get_request_id


class RequestIDFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RequestIDFilter())

    formatter = logging.Formatter(
        "%(asctime)s - request_id=%(request_id)s - "
        "%(name)s - %(levelname)s - %(message)s"
    )

    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    root_logger.handlers.clear()
    root_logger.addHandler(handler)