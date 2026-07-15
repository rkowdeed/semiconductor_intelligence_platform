"""Small shared utilities: request id generation and timing helpers."""

from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from collections.abc import Iterator


def new_request_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def timer() -> Iterator[dict]:
    """Context manager that records elapsed wall-clock time in milliseconds.

    Usage:
        with timer() as t:
            do_work()
        print(t["duration_ms"])
    """
    result: dict = {}
    start = time.perf_counter()
    try:
        yield result
    finally:
        result["duration_ms"] = round((time.perf_counter() - start) * 1000, 3)
