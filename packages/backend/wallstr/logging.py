import logging
import logging.config
import sys
from collections.abc import Iterable
from copy import copy
from typing import Any, cast

import logfire
import rich
import structlog
from langchain_core.messages import BaseMessage
from rich.panel import Panel
from rich.pretty import pprint
from structlog.dev import DIM, RESET_ALL, ConsoleRenderer, Styles, plain_traceback
from structlog.stdlib import _FixedFindCallerLogger
from structlog.typing import EventDict, Processor, WrappedLogger

from wallstr.conf import settings

TRACE = 5

if not sys.warnoptions:
    import warnings

    # crypt is required by passlib
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="'crypt' is deprecated and slated for removal in Python 3.13",
    )


def truncate_log_event(
    _: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    if method_name in ["error", "critical", "exception"]:
        return event_dict
    MAX_EVENT_LEN = 80
    event = event_dict.get("event", "")
    if len(event) > (MAX_EVENT_LEN + 20):
        event_dict["event"] = (
            f"{event[:MAX_EVENT_LEN]}...{event[-20:]} [{len(event)} symbols]"
        )
    return event_dict


"""
https://www.structlog.org/en/stable/standard-library.html#rendering-within-structlog
"""
processors: Iterable[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    *(
        [structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False)]
        if settings.ENV != "prod"
        else []
    ),
]

styles = {
    **ConsoleRenderer.get_default_level_styles(),
    "debug": RESET_ALL,
    "trace": DIM,
}


class CustomLogger(_FixedFindCallerLogger):
    def trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)


def configure_logging(name: str) -> None:
    logging.addLevelName(TRACE, "TRACE")

    if settings.LOGFIRE_TOKEN:
        logfire.configure(
            token=settings.LOGFIRE_TOKEN.get_secret_value(),
            environment=settings.ENV,
            service_name=name,
            console=False,
        )

    logging_config = _get_logging_config()
    logging.config.dictConfig(logging_config)

    structlog.configure(
        processors=[
            *processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.setLoggerClass(CustomLogger)


def debug(*args: Any) -> None:
    """
    Output to the console in debug mode
    For development purposes only (may contain personal data)
    Disabled in production mode
    """
    if settings.ENV == "production":
        return
    if not settings.DEBUG:
        return

    # pretty print Langchain BaseMessages
    if (
        len(args) == 1
        and isinstance(args[0], list)
        and len(args[0]) > 0
        and isinstance(args[0][0], BaseMessage)
    ):
        for msg in args[0]:
            rich.print(Panel(msg.content, title=msg.__class__.__name__))
        return

    pprint(args)


class AccessLogsFormatter(structlog.stdlib.ProcessorFormatter):
    def format(self, record: logging.LogRecord) -> str:
        recordcopy = copy(record)
        (
            client_addr,
            method,
            full_path,
            http_version,
            status_code,
        ) = recordcopy.args  # type: ignore[misc]
        request_line = f"{method} {full_path} HTTP/{http_version}"
        recordcopy.__dict__.update(
            {
                "client_addr": client_addr,
                "request_line": request_line,
                "status_code": status_code,
            }
        )
        return super().format(recordcopy)


def _get_logging_config() -> dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": processors,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    *([logfire.StructlogProcessor()] if settings.LOGFIRE_TOKEN else []),
                    structlog.dev.ConsoleRenderer(
                        level_styles=cast(Styles, styles),  # structlog bug
                        exception_formatter=plain_traceback,
                    ),
                ],
            },
            "access": {
                "()": AccessLogsFormatter,
                "foreign_pre_chain": [
                    *processors,
                ],
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    *([logfire.StructlogProcessor()] if settings.LOGFIRE_TOKEN else []),
                    structlog.dev.ConsoleRenderer(
                        level_styles=cast(Styles, styles),  # structlog bug
                        exception_formatter=plain_traceback,
                    ),
                ],
            },
        },
        "handlers": {
            "default": {
                "level": "NOTSET",
                "class": "logging.StreamHandler",
                "formatter": "console",
            },
            "access": {
                "level": "NOTSET",
                "class": "logging.StreamHandler",
                "formatter": "access",
            },
        },
        "loggers": {
            "root": {
                "handlers": ["default"],
                "level": "NOTSET",
            },
            "wallstr": {"level": "NOTSET"},
            "authlib": {"level": "DEBUG"},
            "uvicorn": {"level": "DEBUG"},
            "uvicorn.access": {
                "level": "DEBUG",
                "handlers": ["access"],
                "propagate": False,
            },
            # boto3
            "botocore": {"level": "INFO"},
            "pika": {"level": "WARNING"},
            "httpcore": {"level": "INFO"},
            "s3transfer": {"level": "INFO"},
            # openai
            "openai": {"level": "INFO"},
            "urllib3": {"level": "INFO"},
            # unstructured
            "unstructured": {"level": "NOTSET"},
            "pdfminer": {"level": "INFO"},
            "weaviate": {"level": "DEBUG"},
        },
    }
