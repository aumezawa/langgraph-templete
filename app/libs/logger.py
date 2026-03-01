"""
logger.py

Version : 2.0.0
Author  : aumezawa
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING, cast

from dotenv import load_dotenv
from loguru import logger

if TYPE_CHECKING:
    from types import FrameType


class InterceptHandler(logging.Handler):
    """Logs to loguru from Python logging module"""

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a record."""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        frame, depth = logging.currentframe(), 1
        while frame.f_code.co_filename in (logging.__file__, __file__):
            frame = cast("FrameType", frame.f_back)
            depth += 1
        logger_with_opts = logger.opt(depth=depth, exception=record.exc_info)
        try:
            logger_with_opts.log(level, "{}", record.getMessage())
        except Exception as e:
            safe_msg = getattr(record, "msg", None) or str(record)
            logger_with_opts.warning(
                "Exception logging the following native logger message: %s, %s",
                safe_msg,
                e,
            )


def setup_logger(
    modules: list[str] | None = None,
) -> None:
    """Logger setup."""
    load_dotenv()
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    logger.remove()
    logger.add(
        sink=sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level=f"{log_level}",
    )

    for module in modules or []:
        logging.getLogger(module).setLevel(logging.getLevelNamesMapping()[log_level])
        logging.getLogger(module).handlers = [InterceptHandler()]
