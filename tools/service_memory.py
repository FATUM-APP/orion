from __future__ import annotations

import json
import os
from uuid import UUID

import psycopg


from deepagents.backends.utils import create_file_data, file_data_to_string
from langchain.tools import ToolRuntime, tool


from context import Context


MEMORY_KEY = "/AGENTS.md"




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

    ids = []
    invalid = []
    for sid in service_ids:
        try:
            ids.append(str(UUID(sid.strip())))
        except ValueError:
            invalid.append(sid)

    if invalid:
        return json.dumps(
            {"error": f"Invalid service_id(s): {invalid}. Use query_catalog to find the correct service_id UUID first."},
            ensure_ascii=False,
        )

    ids = list(dict.fromkeys(ids))
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

@tool
def save_service_analysis(
    service_id: str,
    content: str,
    runtime: ToolRuntime[Context],
    key: str = MEMORY_KEY,
) -> str:
    """Save a market niche or analysis to a service's memory.

    Use this to persist a niche definition or SWOT after building it.
    Does not require ownership — any active service in the catalog
    can receive a niche. Use key="/swot.md" for SWOT analyses.
    This does not modify catalog records, prices, or availability.
    """
    if not content.strip():
        raise ValueError("Content cannot be empty.")

    if runtime.store is None:
        raise RuntimeError("A LangGraph Store is required.")

    sid = str(UUID(service_id))

    with psycopg.connect(
        os.environ["CATALOG_DSN"],
        connect_timeout=5,
        options=(
            "-c statement_timeout=10000 "
            "-c default_transaction_read_only=on"
        ),
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM public.v_available_services "
                "WHERE service_id = %s",
                [sid],
            )
            if cur.fetchone() is None:
                raise ValueError(
                    f"Service {sid} not found in the catalog."
                )

    namespace = ("memory", "service", sid)
    existing = runtime.store.get(namespace, key)

    file_data = create_file_data(
        content.strip(),
        created_at=(
            existing.value.get("created_at")
            if existing
            else None
        ),
    )

    runtime.store.put(namespace, key, file_data)

    return json.dumps(
        {"service_id": sid, "key": key, "saved": True},
        ensure_ascii=False,
    )
