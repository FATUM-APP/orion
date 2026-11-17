from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from deepagents.backends.utils import create_file_data, file_data_to_string
from langchain.tools import ToolRuntime, tool
from langchain_core.messages import ToolMessage
from langgraph.types import Command

from context import Context


MEMORY_KEY = "/AGENTS.md"


def _owned_services(
    runtime: ToolRuntime[Context],
    *,
    category: str = "",
    service_ids: list[str] | None = None,
) -> list[dict]:
    """Resolve active services owned by the contextual user."""
    uid = (runtime.context.user_id or "").strip()
    if not uid:
        raise ValueError("A contextual user_id is required for owned services.")

    uid = str(UUID(uid))

    conditions = ["provider_id = %s"]
    params: list = [uid]

    if category.strip():
        conditions.append("lower(category) = lower(%s)")
        params.append(category.strip())

    if service_ids is not None:
        ids = list(dict.fromkeys(str(UUID(sid)) for sid in service_ids))
        if not ids:
            return []

        conditions.append("service_id = ANY(%s)")
        params.append(ids)

    sql = (
        "SELECT service_id, provider_id, title, category "
        "FROM public.v_available_services "
        "WHERE " + " AND ".join(conditions) +
        " ORDER BY category, title, service_id"
    )

    with psycopg.connect(
        os.environ["CATALOG_DSN"],
        connect_timeout=5,
        options=(
            "-c statement_timeout=10000 "
            "-c default_transaction_read_only=on"
        ),
    ) as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def _selected_services(runtime: ToolRuntime[Context]) -> list[dict]:
    """Revalidate the current selection before memory access."""
    ids = runtime.state.get("selected_service_ids", [])

    if not ids:
        raise ValueError("Select services before accessing their memories.")

    services = _owned_services(runtime, service_ids=ids)

    if {str(row["service_id"]) for row in services} != set(ids):
        raise ValueError(
            "The selection contains inactive, missing, or unauthorized services. "
            "Select services again."
        )

    return services


@tool
def select_owned_services(
    runtime: ToolRuntime[Context],
    category: str = "",
    service_ids: list[str] | None = None,
) -> Command:
    """Select the contextual user's active services.

    Use category for all services in an exact catalog category.
    Use service_ids for a specific subset found through catalog queries.
    With neither filter, select all active services owned by this user.
    This replaces the previous selection.
    """
    services = _owned_services(
        runtime,
        category=category,
        service_ids=service_ids,
    )

    ids = [str(row["service_id"]) for row in services]

    return Command(
        update={
            "selected_service_ids": ids,
            "messages": [
                ToolMessage(
                    content=json.dumps(
                        {
                            "user_id": runtime.context.user_id,
                            "selected_service_ids": ids,
                            "services": services,
                        },
                        default=str,
                        ensure_ascii=False,
                    ),
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )


@tool
def read_selected_service_memories(
    runtime: ToolRuntime[Context],
) -> str:
    """Read the separate memories of the currently selected owned services."""
    services = _selected_services(runtime)

    if runtime.store is None:
        raise RuntimeError("A LangGraph Store is required.")

    memories = []

    for service in services:
        sid = str(service["service_id"])
        item = runtime.store.get(
            ("memory", "service", sid),
            MEMORY_KEY,
        )

        memories.append(
            {
                "service_id": sid,
                "title": service["title"],
                "memory": file_data_to_string(item.value) if item else "",
            }
        )

    return json.dumps(memories, ensure_ascii=False)


@tool
def remember_selected_services(
    note: str,
    runtime: ToolRuntime[Context],
    key: str = MEMORY_KEY,
    replace: bool = False,
) -> str:
    """Write to every selected owned service's memory.

    Only use after an explicit request to remember information or when a
    skill (market-niche, SWOT) produces a structured analysis to save.
    The same content must apply to every selected service.
    This does not modify catalog records, prices, or availability.

    key: memory slot to write to. Default is the main niche document
         ("/AGENTS.md"). Use "/swot.md" for SWOT analyses.
    replace: if True, replaces the entire content instead of appending.
             Use for structured analyses (niche, SWOT). Default False
             appends a timestamped note.
    """
    if not note.strip():
        raise ValueError("The memory note cannot be empty.")

    services = _selected_services(runtime)

    if runtime.store is None:
        raise RuntimeError("A LangGraph Store is required.")

    timestamp = datetime.now(timezone.utc).isoformat()
    saved_ids = []

    for service in services:
        sid = str(service["service_id"])
        namespace = ("memory", "service", sid)
        existing = runtime.store.get(namespace, key)

        if replace:
            final_content = note.strip()
        else:
            content = (
                file_data_to_string(existing.value)
                if existing
                else f"# Service memory\n\nService ID: {sid}\n"
            )

            entry = (
                f"\n\n## Provider note — {timestamp}\n"
                f"Source: contextual user {runtime.context.user_id}\n\n"
                f"{note.strip()}\n"
            )

            final_content = content + entry

        file_data = create_file_data(
            final_content,
            created_at=(
                existing.value.get("created_at")
                if existing
                else None
            ),
        )

        runtime.store.put(namespace, key, file_data)
        saved_ids.append(sid)

    return json.dumps(
        {"saved_service_ids": saved_ids, "key": key, "replaced": replace},
        ensure_ascii=False,
    )

@tool
def read_service_memories(
    service_ids: list[str],
    runtime: ToolRuntime[Context],
) -> str:
    """Read memories (market niche, analysis) for any list of services.

    Use this when evaluating service fit in a recommendation flow
    or when reviewing a service's existing niche before updating it.
    Does not require ownership — any active service can be read.
    """
    if not service_ids:
        raise ValueError("Provide at least one service_id.")

    if runtime.store is None:
        raise RuntimeError("A LangGraph Store is required.")

    ids = list(dict.fromkeys(str(UUID(sid)) for sid in service_ids))
    memories = []

    for sid in ids:
        namespace = ("memory", "service", sid)
        niche = runtime.store.get(namespace, MEMORY_KEY)
        swot = runtime.store.get(namespace, "/swot.md")

        memories.append({
            "service_id": sid,
            "niche": file_data_to_string(niche.value) if niche else "",
            "swot": file_data_to_string(swot.value) if swot else "",
        })

    return json.dumps(memories, ensure_ascii=False)
