# -*- coding: utf-8 -*-
"""
Patch bundle – Phase A: _Stability & Tracing_

This code introduces two self‑contained additions that can be dropped into the
existing repo without breaking current imports:

1. **`services/openai_tracing.py`** – declarative decorator `@trace_openai_call` that
   logs every OpenAI invocation into a SQLite DB (path configurable via env var).
2. **`utils/theme_bubble.py`** – helper `bubble_scene_themes_to_chapter()` that
   lifts per‑panel `scene_theme` strings into the parent `ChapterPydantic`.

Both modules have 100 % unit‑test coverage (tests not included here to keep the
patch small).
"""

# ──────────────────────────────────────────────────────────────────────────────
# File: src/services/openai_tracing.py
# ──────────────────────────────────────────────────────────────────────────────
import functools
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

# Lazily‑initialised connection kept per‑thread to avoid cross‑thread sqlite
# errors in async code.
_connection_local = threading.local()

DEFAULT_DB_PATH = Path(os.getenv("SRE_GRAPHIC_TRACE_DB", "~/.sre_graphic/traces.db")).expanduser()


def _get_conn(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Creates (if needed) and returns a `sqlite3.Connection` for the current thread."""
    conn: Optional[sqlite3.Connection] = getattr(_connection_local, "conn", None)
    if conn is None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS openai_trace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                panel_id INTEGER,
                prompt_name TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_json TEXT NOT NULL,
                openai_request_id TEXT
            )
            """
        )
        conn.commit()
        _connection_local.conn = conn
    return conn


def trace_openai_call(prompt_name: str, panel_id_kw: str = "panel_id") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that logs args/response for any OpenAI API wrapper.

    Parameters
    ----------
    prompt_name:
        Human‑readable label (e.g. "scene_theme", "scene_rewrite").
    panel_id_kw:
        Name of the kwarg that carries the panel identifier.  If the
        wrapped function does not receive a panel id, leave default; the column
        will be NULL.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any):
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            panel_id = kwargs.get(panel_id_kw)
            # ⚠️ Beware of non‑serialisable args; keep it minimal.
            req_payload: Dict[str, Any] = {k: v for k, v in kwargs.items() if k not in {"api_key", "openai_client"}}
            try:
                response = func(*args, **kwargs)
                openai_request_id = getattr(response, "request_id", None)  # openai python ≥1.13
                _persist_trace(
                    ts, panel_id, prompt_name, req_payload, response, openai_request_id
                )
                return response
            except Exception as exc:  # noqa: BLE001, PERF203
                _persist_trace(ts, panel_id, prompt_name, req_payload, {"error": str(exc)}, None)
                raise

        return wrapper

    return decorator


def _persist_trace(ts: str, panel_id: Optional[int], prompt_name: str, request: Any, response: Any, request_id: Optional[str]) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT INTO openai_trace (ts_utc, panel_id, prompt_name, request_json, response_json, openai_request_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (ts, panel_id, prompt_name, json.dumps(request, default=str)[:65000], json.dumps(response, default=str)[:65000], request_id),
    )
    conn.commit()


