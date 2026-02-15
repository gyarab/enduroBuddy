from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from django.conf import settings

from .imports import import_fit_for_user, sync_garmin_for_user


_executor = ThreadPoolExecutor(max_workers=2)


def _mode() -> str:
    return str(getattr(settings, "IMPORT_TASK_MODE", "inline") or "inline").lower()


def _run_or_enqueue(func: Callable[..., Any], *args, **kwargs):
    if _mode() == "async":
        _executor.submit(func, *args, **kwargs)
        return None
    return func(*args, **kwargs)


def run_fit_import(user, uploaded_file):
    return _run_or_enqueue(import_fit_for_user, user, uploaded_file)


def run_garmin_sync(user, *, window: str):
    return _run_or_enqueue(sync_garmin_for_user, user, window=window)
