"""Uvicorn access-log helpers (reduce SPA root polling noise at INFO)."""

from __future__ import annotations

import logging
import re

# Uvicorn default: 127.0.0.1:49610 - "GET / HTTP/1.1" 200 OK
_ROOT_GET_200 = re.compile(r'"GET / HTTP/1\.1"\s+200\b')

_access_logger = logging.getLogger("uvicorn.access")


class RootGetAccessLogFilter(logging.Filter):
    """
    Log the first successful GET / at INFO; repeat root loads stay available at DEBUG
    for auditing without flooding the default console.
    """

    def __init__(self) -> None:
        super().__init__()
        self._root_get_info_logged = False
        self._root_get_repeat_count = 0

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if not _ROOT_GET_200.search(message):
            return True

        if not self._root_get_info_logged:
            self._root_get_info_logged = True
            return True

        self._root_get_repeat_count += 1
        if _access_logger.isEnabledFor(logging.DEBUG):
            record.levelno = logging.DEBUG
            record.levelname = logging.getLevelName(logging.DEBUG)
            return True
        return False


def install_root_get_access_log_filter() -> None:
    """Attach dedupe filter once (idempotent)."""
    logger = _access_logger
    for existing in logger.filters:
        if isinstance(existing, RootGetAccessLogFilter):
            return
    logger.addFilter(RootGetAccessLogFilter())
