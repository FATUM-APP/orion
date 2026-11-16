# auth.py — M2M token para que el agente llame al catalog-service
from __future__ import annotations

import os
import threading
import time

import requests

_TOKEN_MARGIN_SECONDS = 30


class ClientCredentialsTokenProvider:
    """Cachea un token OAuth2 client-credentials y lo renueva al vencer."""

    def __init__(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scope: str,
        *,
        margin_seconds: int = _TOKEN_MARGIN_SECONDS,
    ) -> None:
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._margin_seconds = margin_seconds

        self._session = requests.Session()
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at: float = 0.0

    def get_access_token(self) -> str:
        # Fast path sin lock: la gran mayoría de las llamadas caen aquí.
        if self._token and time.time() < self._expires_at - self._margin_seconds:
            return self._token

        with self._lock:
            # Re-chequear: otro hilo pudo haber refrescado mientras esperábamos el lock.
            if self._token and time.time() < self._expires_at - self._margin_seconds:
                return self._token
            return self._fetch_token()

    def _fetch_token(self) -> str:
        resp = self._session.post(
            self._token_url,
            data={"grant_type": "client_credentials", "scope": self._scope},
            auth=(self._client_id, self._client_secret),
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()

        self._token = data["access_token"]
        self._expires_at = time.time() + data["expires_in"]
        return self._token


def _provider_from_env() -> ClientCredentialsTokenProvider:
    return ClientCredentialsTokenProvider(
        token_url=os.environ["COGNITO_TOKEN_URL"],
        client_id=os.environ["CATALOG_AGENT_CLIENT_ID"],
        client_secret=os.environ["CATALOG_AGENT_CLIENT_SECRET"],
        scope="api.catalog-agent/read api.catalog-agent/write",
    )


_provider: ClientCredentialsTokenProvider | None = None


def get_access_token() -> str:
    """Punto de entrada compatible con el código existente."""
    global _provider
    if _provider is None:
        _provider = _provider_from_env()
    return _provider.get_access_token()