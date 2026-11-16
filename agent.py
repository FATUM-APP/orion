from __future__ import annotations

from dataclasses import dataclass

from deepagents import create_deep_agent, FilesystemPermission, FilesystemBackend, CompositeBackend, StateBackend, StoreBackend


from models import model
from tracing import AGENT_NAME, trace_config
from subagents import build_subagents


from dataclasses import dataclass
from pathlib import Path




HERE = Path(__file__).resolve().parent

SYSTEM_PROMPT = """
You are the Fatum main market analyst agent. Your principal job is to delegate tasks to subagents and provide a final 
answer to the user. You will use the subagents to perform specific tasks,
 and you will be responsible for coordinating their work and ensuring that they are working together effectively.
 Follow your operating manual (loaded from your memory)
""" 


@dataclass
class Context:
    user_id: str = ""
    service_id: str = ""


def _thread_id(rt) -> str:
    info = getattr(rt, "execution_info", None)
    return getattr(info, "thread_id", None) or "no-thread"


def client_ns(rt):
    uid = (rt.context.user_id or "").strip()
    if not uid:
        return ("memory", "anon", _thread_id(rt), "client")
    return ("memory", "user", uid, "client")


def professional_ns(rt):
    uid = (rt.context.user_id or "").strip()
    if not uid:
        return ("memory", "anon", _thread_id(rt), "professional")
    return ("memory", "user", uid, "professional")


def service_ns(rt):
    sid = (rt.context.service_id or "").strip()
    if not sid:
        return ("memory", "anon", _thread_id(rt), "service")
    return ("memory", "service", sid)


_backend = CompositeBackend(
    default=StateBackend(),
    routes={
        "/agents/": FilesystemBackend(
            root_dir=str(HERE / "agents"),
            virtual_mode=True,
        ),
        "/skills/": FilesystemBackend(
            root_dir=str(HERE / "skills"),
            virtual_mode=True,
        ),

        "/memories/user/client/":       StoreBackend(namespace=client_ns),
        "/memories/user/professional/": StoreBackend(namespace=professional_ns),
        "/memories/service/":           StoreBackend(namespace=service_ns),
    },
)


def make_graph():
    agent = create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        name=AGENT_NAME,
        backend=_backend,
        memory=[
            "/agents/AGENTS.md",
            "/memories/user/client/AGENTS.md",
            "/memories/service/AGENTS.md",
        ],
        subagents=build_subagents(_backend),
        context_schema=Context,
        permissions=[
        FilesystemPermission(operations=["read"], paths=["/agents/**"], mode="allow"),
        FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
    ],

        
    )
    return agent.with_config({"recursion_limit": 50})