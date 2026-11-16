"""Trazabilidad en LangSmith.

El destino de las trazas (agente + entorno, o proyecto) NO se decide aquí:
se decide con las variables LANGSMITH_* del .env. Este archivo solo añade lo
que esas variables no cubren: nombre del agente, etiquetas y metadatos para
filtrar trazas después.
"""

from __future__ import annotations

import os
import subprocess

# Cambia esto (y LANGSMITH_AGENT_ID en el .env) por el nombre de tu agente.
AGENT_NAME = "orion-agent"


def _code_version() -> str:
    """Commit actual, para saber qué versión del código generó cada traza."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def trace_config(
    *,
    run_name: str | None = None,
    tags: list[str] | None = None,
    metadata: dict | None = None,
    recursion_limit: int = 50,
) -> dict:
    """RunnableConfig con etiquetas y metadatos.

    graph.with_config(trace_config())
    graph.with_config(trace_config(tags=["ventas"], metadata={"cliente": "X"}))
    """
    config: dict = {
        "recursion_limit": recursion_limit,
        "tags": [AGENT_NAME, *(tags or [])],
        "metadata": {
            "agent": AGENT_NAME,
            "agent_id": os.getenv("LANGSMITH_AGENT_ID", AGENT_NAME),
            "agent_environment": os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "local"),
            "code_version": _code_version(),
            **(metadata or {}),
        },
    }
    if run_name:
        config["run_name"] = run_name
    return config
