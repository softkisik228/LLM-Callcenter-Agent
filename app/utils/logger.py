import logging
import sys

import structlog


def setup_logging(log_level: str = "INFO") -> None:
    """
    Настроить структурированное логирование для приложения.

    Args:
    ----
        log_level (str): Уровень логирования (например, "INFO", "DEBUG").

    Returns:
    -------
        None

    """
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer()
            if log_level == "DEBUG"
            else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
