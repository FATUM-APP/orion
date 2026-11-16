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
def update_catalog_item(
    item_id: str,
    title: str | None = None,
    description: str | None = None,
    base_price: float | None = None,
    price_type: str | None = None,
    is_negotiable: bool | None = None,
    default_estimated_time: int | None = None,
    job_type: str | None = None,
) -> str:
    """Update an existing catalog item's text/value fields. Never touches images.

    Call this when the provider wants to change a catalog item's title,
    description, price, negotiability, estimated time, or job type. Do NOT
    use this to add, remove, or replace photos — this tool cannot change
    images; existing images are always kept as-is.

    Only pass the fields that should actually change; any field left as
    None is left untouched on the existing item.

    `price_type` must match one of the PriceType enum values (e.g. "FIXED",
    "HOURLY"). `job_type` must match one of the JobType enum values.

    Returns JSON with `success: true`, or `error` with details on failure.
    """
    fields = {
        "title": title,
        "description": description,
        "basePrice": base_price,
        "priceType": price_type,
        "isNegotiable": is_negotiable,
        "defaultEstimatedTime": default_estimated_time,
        "jobType": job_type,
    }
    payload = {"id": item_id}
    payload.update({k: v for k, v in fields.items() if v is not None})

    multipart = {
        "request": (None, json.dumps(payload), "application/json"),
    }

    try:
        resp = requests.put(
            f"{_base_url()}/catalog/item/update",
            files=multipart,
            headers=_auth_headers(),
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        return json.dumps({"error": f"catalog item update failed: {exc}"}, ensure_ascii=False)

    return json.dumps({"success": True}, ensure_ascii=False)