"""Study-plan storage.

Plans are saved in Supabase when those tables exist. If they do not, they are
saved in the local database so building a plan still works.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from database import fetch_all, fetch_one, insert_row, insert_rows, update_row

logger = logging.getLogger(__name__)

_PLAN_TABLES = frozenset({"learning_plans", "learning_plan_weeks", "learning_plan_tasks"})
_CACHE_TABLE = "learning_video_cache"
_local_plans = False
_local_cache = False


def _missing_table(exc: Exception) -> bool:
    text = str(exc)
    return "PGRST205" in text or "schema cache" in text


def _local_call(name: str):
    from local_database import (
        local_fetch_all,
        local_fetch_one,
        local_insert_row,
        local_insert_rows,
        local_update_row,
    )

    return {
        "fetch_all": local_fetch_all,
        "fetch_one": local_fetch_one,
        "insert_row": local_insert_row,
        "insert_rows": local_insert_rows,
        "update_row": local_update_row,
    }[name]


def _uses_local(table: str) -> bool:
    if table in _PLAN_TABLES:
        return _local_plans
    if table == _CACHE_TABLE:
        return _local_cache
    return False


def _remember_local(table: str) -> None:
    global _local_plans, _local_cache
    if table in _PLAN_TABLES:
        if not _local_plans:
            logger.info("Study plans will be saved on this computer")
        _local_plans = True
    elif table == _CACHE_TABLE:
        _local_cache = True


def plan_fetch_all(
    table: str,
    filters: Optional[dict[str, Any]] = None,
    order_by: Optional[str] = None,
    ascending: bool = False,
) -> list[dict]:
    if _uses_local(table):
        return _local_call("fetch_all")(table, filters, order_by, ascending)
    try:
        return fetch_all(table, filters, order_by, ascending)
    except Exception as exc:
        if _missing_table(exc):
            _remember_local(table)
            return _local_call("fetch_all")(table, filters, order_by, ascending)
        raise


def plan_fetch_one(table: str, filters: dict[str, Any]) -> Optional[dict]:
    if _uses_local(table):
        return _local_call("fetch_one")(table, filters)
    try:
        return fetch_one(table, filters)
    except Exception as exc:
        if _missing_table(exc):
            _remember_local(table)
            return _local_call("fetch_one")(table, filters)
        raise


def plan_insert_row(table: str, data: dict[str, Any]) -> dict:
    if _uses_local(table):
        return _local_call("insert_row")(table, data)
    try:
        return insert_row(table, data)
    except Exception as exc:
        if _missing_table(exc):
            _remember_local(table)
            return _local_call("insert_row")(table, data)
        raise


def plan_insert_rows(table: str, rows: list[dict[str, Any]]) -> list[dict]:
    if _uses_local(table):
        return _local_call("insert_rows")(table, rows)
    try:
        return insert_rows(table, rows)
    except Exception as exc:
        if _missing_table(exc):
            _remember_local(table)
            return _local_call("insert_rows")(table, rows)
        raise


def plan_update_row(table: str, row_id: str, data: dict[str, Any]) -> dict:
    if _uses_local(table):
        return _local_call("update_row")(table, row_id, data)
    try:
        return update_row(table, row_id, data)
    except Exception as exc:
        if _missing_table(exc):
            _remember_local(table)
            return _local_call("update_row")(table, row_id, data)
        raise
