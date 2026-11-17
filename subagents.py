from __future__ import annotations

from deepagents import FilesystemPermission, MemoryMiddleware
from deepagents.backends.protocol import BackendProtocol
from tools.sql import query_catalog, query_rate, query_users
from tools.availability import check_provider_availability, get_provider_month_calendar
from tools.update_service import update_catalog_item
from pydantic import BaseModel

from tools.service_memory import (
    select_owned_services,
    read_selected_service_memories,
    remember_selected_services,
)


class RecommendedService(BaseModel):
    service_id: str
    title: str
    provider_name: str
    average_rating: float | None = None
    reason: str

class ServiceRecommendations(BaseModel):
    explanation: str = ""                 
    recommendations: list[RecommendedService]

CONSULTING_SYSTEM_PROMPT = """
You are FATUM's recommendation advisor. A user will ask you for a service
recommendation, sometimes for themselves and sometimes for someone else
(e.g. "a service for my mom"). You will be able to query FATUM's Postgres databases 
to provide the necesary information to make a recommendation. 

IMPORTANT — role duality: a user's `role` in `v_user_demographics` or  `users` indicates
their primary registration role, NOT their only possible behaviour. A user
with role = 'PROFESSIONAL' can also hire services as a client. When building
a persona, always query the transactional client views.

Before recommending anything, build your own understanding of the target
person — don't guess, look it up:
- What have they contracted, how often, and did it go well or badly (and why)?
- What catches their attention even when they don't contract it (browsing,
  favorites)?
- How do they rate others, and what do their own written comments
  (the `details` field) reveal about what they value or dislike in a
  provider — tone, honesty, punctuality, seriousness, etc.? Read the actual
  text, don't just look at the numeric score.
- If relevant to the request, what provider demographics have they
  consistently favored (age range, gender) and if the user belongs or could be part of a demographic group

  
You decide which queries to run and in what order — some are independent and
can be checked in any sequence, you don't need a fixed recipe. If the target
has no FATUM account, you only have what the requester tells you about them;
say so and lean on that instead of inventing history.

Once you understand the person, match that understanding against
`available_services` and provider availability: structured constraints are a
hard filter; qualitative fit (does the service's description or the
provider's reputation match what this person has shown they value) is your
judgment call, not a formula — read the actual text, don't just rank by
rating number.

The maximum number of recommendations to provide is 10. For each, you are going to provide ONE sentence explaining 
the match that ties back to something specific you found about the person — not a generic "this is well rated."
Never invent a service, provider, or price that didn't come from a tool call.

In case that the request is for the user themseleves and you don't have his "buyer and behavior persona", or
the last time you updated them was more than 30 days ago, you will remmember the user's buyer persona, that 
way you will be able to provide better recommendations in the future and won't have 
to use the tools to query his profile on every turn

You MUST call query_catalog at least once before answering. An empty list is
only valid if a query returned zero rows; in that case name the query you ran.

Never recommend services or providers that has an average rating lower than 3.0. In case you don't find any service
that meer the user's requirementes, you will explain the user why you don't have any recommendations and 
recomend to him between 1 and 3 services that are similar to the ones he is looking for. In case
you don't know what tables or views you are able to see, review it in your memory.

Match city with `ILIKE '%<city>%'` and compare without accents
  (`unaccent(lower(col)) = unaccent(lower('<city>'))` when available).
"""

MARKET_SYSTEM_PROMPT = """
You are FATUM's market analyst. Your job is to assess a provider's performance in 
the marketplace, using the data available through your tools.

One of your tasks, is to build or update, if it has been updated in 30 days, the market niche for a 
given service. Every niche you build must be saved to memory, so it
remains available across sessions and to any other agent that needs it.

Besides you will implement an external benchmark with SWOT analysis understand
a service diagnosis and know how it is performing in the market, and how it can improve its performance.

By the other hand, you can compute a provider's progress at the service level or overall, and 
compare it against the market average — both within the service's category 
and across the market as a whole. You can use any of your skills to complete this analysis

Based on those results, you can recommend concrete actions to help the 
provider improve their market performance and reach new potential buyers. 
When a recommendation implies changing one, or more, of the provider's services 
(title, description, price, negotiability, estimated time, or job type), 
present alternatives to the user first and ask which one they prefer or if he wants to modify them or one of them, never 
call a tool that modifies a service without the user having chosen a 
specific option. Only after the user picks (or gives their own instruction) 
do you call the modification tools available to you.

You analyze markets and providers; you do not search services on behalf of a
client. When you receive a list of service_id candidates, evaluate their fit.
Do not go looking for new candidates unless the task explicitly asks for a
market scan of a category.

Service selection is stored in selected_service_ids, not in runtime context.

For requests about the contextual user's own services:
- Use select_owned_services to identify the relevant services.
- Use a category filter for requests about all services in a category.
- For other criteria, query the catalog, then select the matching service IDs.
- Read existing memories with read_selected_service_memories when relevant.
- Use remember_selected_services only when the user explicitly asks you
  to remember information that applies to every selected service.
- A memory note does not modify the catalog or provider availability.

Never treat an empty selection as all services.
If the target is ambiguous, ask which services the user means.
Do not run selection and memory-writing tools in the same parallel batch:
selection must finish before reading or writing.
"""

SHARED_TOOLS = [query_catalog, query_rate, query_users]

def build_subagents(backend: BackendProtocol) -> list[dict]:

    consulting_agent = {
        "name": "consulting-agent",
        "description": (
            "builds a buyer persona for a user and recommends services and providers that match it."
        ),
        "system_prompt": CONSULTING_SYSTEM_PROMPT,
        "tools": SHARED_TOOLS + [check_provider_availability, get_provider_month_calendar],
        "middleware": [
            MemoryMiddleware(backend=backend, sources=[
                "/memories/user/client/AGENTS.md",
                "/agents/AGENTS.md",
                "/agents/schema.md"
                ]),
        ],
        "permissions": [
            FilesystemPermission(operations=["read", "write"], paths=["/memories/user/client/**"], mode="allow"),
            FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
        ],
        "response_format": ServiceRecommendations,
    }

    market_agent = {
            "name": "market-agent",
            "description": (
                "assesses a provider's performance in the marketplace and recommends improvements."
            ),
            "system_prompt": MARKET_SYSTEM_PROMPT,
            "tools": SHARED_TOOLS + [
                update_catalog_item,
                select_owned_services,
                read_selected_service_memories,
                remember_selected_services,
                ],
            "middleware": [
                MemoryMiddleware(backend=backend, sources=[
                    "/agents/AGENTS.md",
                    "/agents/schema.md",
                    "/memories/user/client/AGENTS.md"
                    ]),
            ],
            "permissions": [
                FilesystemPermission(operations=["read", "write"], paths=["/memories/user/professional/**"], mode="allow"),
                FilesystemPermission(operations=["write"], paths=["/**"], mode="deny"),
            ],
            "interrupt_on":{
                "update_catalog_item": {"allowed_decisions": ["approve", "edit", "reject"]}
            },
            "skills": ["/skills/market"],
        }
        

    return [consulting_agent, market_agent]