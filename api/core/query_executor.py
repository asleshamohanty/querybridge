from __future__ import annotations
from decimal import Decimal
import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session
from api.config import settings


class ExecutionError(Exception):
    pass


def run_query(sql: str, db: Session) -> dict:
    try:
        result = db.execute(text(sql))
        columns = list(result.keys())
        raw_rows = result.fetchmany(settings.max_rows + 1)
    except Exception as exc:
        raise ExecutionError(f"Query execution failed: {exc}") from exc

    truncated = len(raw_rows) > settings.max_rows
    rows = raw_rows[:settings.max_rows]

    serialised_rows = []
    for row in rows:
        serialised_rows.append([_serialise(v) for v in row])

    return {
        "columns": columns,
        "rows": serialised_rows,
        "row_count": len(serialised_rows),
        "truncated": truncated,
    }


def _serialise(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value
