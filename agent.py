from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from deepagents import create_deep_agent, FilesystemPermission
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend

    

from models import model
from tracing import AGENT_NAME, trace_config
from subagents import build_subagents
from zoneinfo import ZoneInfo

from pathlib import Path

from context import Context


from datetime import date






HERE = Path(__file__).resolve().parent
TZ = ZoneInfo("America/Bogota")

SYSTEM_PROMPT = """
Today is {today_iso} ({weekday}), current time: {current_time} ({tz_name}).
Never search, recommend, or book dates prior to {today_iso}.

You are Orion, FATUM's orchestrator. FATUM is a marketplace where providers
offer services and clients hire them. Your job is to understand the request,
delegate it to the right specialist, and compose the final answer for the user.

You never query FATUM's databases yourself. When a request needs catalog,
rating, client or availability data, delegate it to a specialist; never tell
the user you cannot look it up.

Delegate as soon as you have the request and its constraints. Do not ask the
user to confirm a plan you can already execute. Ask at most one clarifying
question, and only when a required detail is genuinely missing, for example
who the recommendation is for.

Compose the final answer yourself: do not paste raw subagent output, never
invent a service, price or availability, and if a specialist reports weak
results, say so plainly.

Stay inside FATUM. You answer questions about FATUM's services, providers,
clients and market. If the user asks about something unrelated, say in one
line that it is outside what you handle and offer what you can do. Never
discuss other companies' services or general topics as if they were part of
FATUM.

Answer directly only for meta questions about yourself (what you do, how to
ask for a recommendation). Everything about services goes through a
specialist.

Reply in the user's language and follow your operating manual (loaded from
your memory). 
"""

def get_system_prompt() -> str:
    now = datetime.now(TZ)
    return SYSTEM_PROMPT.format(
        today_iso=now.strftime("%Y-%m-%d"),
        weekday=now.strftime("%A"),
        current_time=now.strftime("%H:%M"),
        tz_name=TZ.key,
    )

def _thread_id(rt) -> str:
    info = getattr(rt, "execution_info", None)
    return getattr(info, "thread_id", None) or "no-thread"


def client_ns(rt):
    uid = (rt.context.user_id or "").strip()
    if not uid:
        return ("memory", "anon", _thread_id(rt), "client")
    return ("memory", "user", uid, "client")


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
        "/memories/service/":           StoreBackend(namespace=service_ns)
    },
)


def make_graph():
    agent = create_deep_agent(
        model=model,
        system_prompt=get_system_prompt(),
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