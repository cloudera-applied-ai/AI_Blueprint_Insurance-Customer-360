"""Access log dedupe for SPA root GET / polling."""

from __future__ import annotations

import logging

from customer360.logging_access import RootGetAccessLogFilter


def _record(msg: str, level: int = logging.INFO) -> logging.LogRecord:
    return logging.LogRecord(
        name="uvicorn.access",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=(),
        exc_info=None,
    )


def test_first_root_get_allowed_at_info():
    filt = RootGetAccessLogFilter()
    msg = '127.0.0.1:49610 - "GET / HTTP/1.1" 200 OK'
    assert filt.filter(_record(msg)) is True


def test_repeat_root_get_suppressed_at_info():
    filt = RootGetAccessLogFilter()
    msg = '127.0.0.1:49610 - "GET / HTTP/1.1" 200 OK'
    assert filt.filter(_record(msg)) is True
    assert filt.filter(_record(msg)) is False


def test_repeat_root_get_emitted_at_debug():
    filt = RootGetAccessLogFilter()
    msg = '127.0.0.1:49610 - "GET / HTTP/1.1" 200 OK'
    access = logging.getLogger("uvicorn.access")
    prev = access.level
    access.setLevel(logging.DEBUG)
    try:
        assert filt.filter(_record(msg)) is True
        repeat = _record(msg)
        assert filt.filter(repeat) is True
        assert repeat.levelno == logging.DEBUG
    finally:
        access.setLevel(prev)


def test_other_paths_always_logged():
    filt = RootGetAccessLogFilter()
    msg = '127.0.0.1:49610 - "GET /api/health HTTP/1.1" 200 OK'
    assert filt.filter(_record(msg)) is True
    assert filt.filter(_record(msg)) is True
