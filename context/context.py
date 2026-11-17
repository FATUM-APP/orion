
from __future__ import annotations

from dataclasses import dataclass



@dataclass
class Context:
    user_id: str = ""
    service_id: str = ""

