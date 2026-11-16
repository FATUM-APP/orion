
"""
Free-form, read-only SQL tools for the FATUM advisor agent.

Three query tools (one per database) plus three introspection tools. All
point at the `fatum_agent` Postgres role, which has SELECT granted ONLY
on the public v_* views — never on base tables. That boundary is enforced by
Postgres itself (see the GRANT statements you already ran); everything below
is defense in depth on top of it, same spirit as a hand-written query_chinook
tool, adapted to free SQL against three separate Postgres databases:

- only a single SELECT (or WITH ... SELECT) statement is accepted
- a keyword denylist blocks write/DDL statements, even though the role
  can't write anyway
- results are capped at MAX_ROWS via fetchmany(), regardless of whether the
  model's own query included a LIMIT
- each connection is opened with a 10s statement timeout and forced
  read-only (also set at the role level, as a second line of defense)

Requires: pip install "psycopg[binary]" langchain
Env vars: CATALOG_DSN, RATE_DSN, USERS_DSN (must use the fatum_agent role)
"""

from __future__ import annotations

import json
import os
from decimal import Decimal

import psycopg
from langchain.tools import tool

DSN_VARS = {"catalog": "CATALOG_DSN", "rate": "RATE_DSN", "users": "USERS_DSN"}
SESSION_OPTIONS = "-c statement_timeout=10000 -c default_transaction_read_only=on"
MAX_ROWS = 200


_FORBIDDEN = (
    "insert", "update", "delete", "drop", "alter", "create",
    "replace", "truncate", "attach", "detach", "grant", "revoke",
    "vacuum", "copy", "call", "do",
)


def _json(value):
    """Convert Decimal and dates so the model sees numbers, not opaque text."""
    if isinstance(value, Decimal):
        return float(value)
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _validate(sql: str) -> str | None:
    """Return an error message if the SQL isn't a safe single SELECT, else None."""
    stripped = sql.strip().rstrip(";").strip()
    lowered = stripped.lower()

    if not lowered.startswith(("select", "with")):
        return "Only SELECT (or WITH ... SELECT) statements are allowed."
    if ";" in stripped:
        return "Only a single statement is allowed."
    if any(f" {word} " in f" {lowered} " for word in _FORBIDDEN):
        return "Query contains a forbidden keyword."
    return None


def _run(database: str, sql: str) -> str:
    error = _validate(sql)
    if error:
        return json.dumps({"error": error}, ensure_ascii=False)

    stripped = sql.strip().rstrip(";").strip()

    try:
        with psycopg.connect(os.environ[DSN_VARS[database]], options=SESSION_OPTIONS) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(stripped)
                # Fetch one extra row to detect truncation without trusting
                # the query's own LIMIT (it may have none, or a huge one).
                rows = cur.fetchmany(MAX_ROWS + 1)
    except psycopg.Error as exc:
        return json.dumps({"error": f"query failed: {exc}"}, ensure_ascii=False)

    truncated = len(rows) > MAX_ROWS
    rows = rows[:MAX_ROWS]

    return json.dumps(
        {"rowCount": len(rows), "truncated": truncated, "rows": rows},
        default=_json, ensure_ascii=False,
    )


def _introspect(database: str) -> str:
    """List columns of every object the role can see (i.e. just the views,
    since that's all fatum_agent_ro has SELECT on)."""
    sql = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """
    try:
        with psycopg.connect(os.environ[DSN_VARS[database]], options=SESSION_OPTIONS) as conn:
            with conn.cursor(row_factory=psycopg.rows.dict_row) as cur:
                cur.execute(sql)
                rows = cur.fetchall()
    except psycopg.Error as exc:
        return json.dumps({"error": f"introspection failed: {exc}"}, ensure_ascii=False)

    tables: dict[str, list[dict]] = {}
    for row in rows:
        tables.setdefault(row["table_name"], []).append(
            {"column": row["column_name"], "type": row["data_type"]}
        )
    return json.dumps(tables, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Catalog database: services, contracted history, browsing behavior, orders
# ---------------------------------------------------------------------------

@tool
def query_catalog(sql: str) -> str:
    """Run a read-only SELECT against the catalog database (available
    services, a client's contracted/browsed services, provider clientele,
    order outcomes). Only the v_* views are visible, not base tables. Call
    introspect_catalog first if you don't already know the columns. Results
    are capped at 200 rows."""
    return _run("catalog", sql)


@tool
def introspect_catalog() -> str:
    """List the views and columns available in the catalog database."""
    return _introspect("catalog")


# ---------------------------------------------------------------------------
# Rate database: ratings given and received
# ---------------------------------------------------------------------------

@tool
def query_rate(sql: str) -> str:
    """Run a read-only SELECT against the rate database (individual and
    aggregate ratings for services, providers, and clients). Only the v_*
    views are visible, not base tables. Call introspect_rate first if you
    don't already know the columns. Results are capped at 200 rows."""
    return _run("rate", sql)


@tool
def introspect_rate() -> str:
    """List the views and columns available in the rate database."""
    return _introspect("rate")


# ---------------------------------------------------------------------------
# Users database: demographics
# ---------------------------------------------------------------------------

@tool
def query_users(sql: str) -> str:
    """Run a read-only SELECT against the users database (role, gender, age,
    city, active status). Only the v_* views are visible, not base tables.
    Call introspect_users first if you don't already know the columns.
    Results are capped at 200 rows."""
    return _run("users", sql)


@tool
def introspect_users() -> str:
    """List the views and columns available in the users database."""
    return _introspect("users")


