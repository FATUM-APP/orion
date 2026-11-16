from __future__ import annotations

import json
import os

import requests
from langchain.tools import tool

from auth import get_access_token

def _base_url() -> str:
    return os.environ["CATALOG_SERVICE_BASE_URL"]


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {get_access_token()}"}


@tool
def check_provider_availability(provider_id: str, booking: str, duration_minutes: int | None = None) -> str:
    """Check whether a provider can take a booking at a specific date/time.

    Call this whenever the client gave (or you're about to recommend a
    specific booking for) a concrete date and time — not for a general
    "what does this person usually offer" question.

    `booking` must be an ISO-8601 datetime (e.g. "2026-11-20T15:00:00").
    `duration_minutes` is optional; omit it to use the service's default.

    Returns the full JSON body from the service:
    - `providerId` (str), `booking` (ISO datetime) — echo of the request
    - `durationMinutes` (int) — the duration actually used (service default if you omitted it)
    - `endsAt` (ISO datetime) — when the booking would end
    - `available` (bool)
    - `reason` (str, only present when `available` is false) — one of
      LEAD_TIME (too soon), UNAVAILABLE_RANGE (provider marked unavailable),
      OVERLAP (already booked), or OUT_OF_SCHEDULE (outside weekly hours)
    """
    params = {"providerId": provider_id, "booking": booking}
    if duration_minutes is not None:
        params["durationMinutes"] = duration_minutes

    try:
        resp = requests.get(
            f"{_base_url()}/order/availability",
            params=params,
            headers=_auth_headers(),
            timeout=5,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return json.dumps({"error": f"availability check failed: {exc}"}, ensure_ascii=False)

    return json.dumps(resp.json(), ensure_ascii=False)


@tool
def get_provider_month_calendar(provider_id: str, year: int, month: int) -> str:
    """Get a provider's full calendar for a given month: per-day availability,
    unavailable-range reasons, and booked slots already resolved together.

    Use this instead of checking day-by-day when the client asked something
    broader than one exact slot (e.g. "does she have room this week?",
    "what days is he free this month?").

    Returns a JSON array, one entry per day in the month:
    - `date` (ISO date, e.g. "2026-11-20")
    - `available` (bool) — note: NOT "isAvailable"; the service's Jackson
      serializer strips the "is" prefix from boolean getters
    - `initialTime` / `finalTime` (ISO time, e.g. "09:00:00") — the
      provider's working window that day, null if not set
    - `unavailableReason` (str or null) — why the day is marked unavailable,
      when applicable
    - `bookedSlots` (array) — slots already booked that day
    """
    params = {"providerId": provider_id, "year": year, "month": month}

    try:
        resp = requests.get(
            f"{_base_url()}/provider/calendar",
            params=params,
            headers=_auth_headers(),
            timeout=5,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return json.dumps({"error": f"calendar lookup failed: {exc}"}, ensure_ascii=False)

    return json.dumps(resp.json(), ensure_ascii=False)