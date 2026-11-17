
from __future__ import annotations

from dataclasses import dataclass
from typing import NotRequired

from deepagents import DeepAgentState


@dataclass
class Context:
    user_id: str = ""

class OrionState(DeepAgentState):
    selected_service_ids: NotRequired[list[str]]