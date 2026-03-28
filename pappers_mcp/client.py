from __future__ import annotations
from typing import Any
import httpx
from .config import Settings
from .exceptions import PappersAPIError, PappersValidationError
from .models import DecisionSearchParams
from .utils import clamp_page, clamp_per_page, clean_params


class PappersJusticeClient:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.logger = logger

    def _headers(self) -> dict[str, str]:
        return {"Accept": "application/json", "Authorization": f"Bearer {self.settings.pappers_api_key}"}

    async def _get_json(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.settings.pappers_justice_base_url.rstrip('/')}/{path.lstrip('/')}"
        safe_params = params or {}
        try:
            async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers(), params=safe_params)
        except httpx.TimeoutException as exc:
            raise PappersAPIError("Request timed out", payload={"url": url}) from exc
        except httpx.HTTPError as exc:
            raise PappersAPIError("HTTP client error", payload={"url": url}) from exc
        if response.status_code >= 400:
            raise PappersAPIError(f"Pappers Justice API returned an error ({response.status_code})", status_code=response.status_code, payload={"raw": response.text[:2000]})
        return response.json()

    async def _get_bytes(self, path: str) -> bytes:
        url = f"{self.settings.pappers_justice_base_url.rstrip('/')}/{path.lstrip('/')}"
        try:
            async with httpx.AsyncClient(timeout=self.settings.timeout_seconds) as client:
                response = await client.get(url, headers=self._headers())
        except httpx.TimeoutException as exc:
            raise PappersAPIError("Request timed out", payload={"url": url}) from exc
        except httpx.HTTPError as exc:
            raise PappersAPIError("HTTP client error", payload={"url": url}) from exc
        if response.status_code >= 400:
            raise PappersAPIError(f"Pappers Justice API returned an error ({response.status_code})", status_code=response.status_code, payload={"raw": response.text[:2000]})
        return response.content

    async def search_decisions(self, params: DecisionSearchParams) -> tuple[dict[str, Any], dict[str, Any]]:
        try:
            params = params.ensure_meaningful()
        except ValueError as exc:
            raise PappersValidationError(str(exc)) from exc
        payload = params.model_dump()
        payload["page"] = clamp_page(payload["page"], self.settings.max_page)
        payload["per_page"] = clamp_per_page(payload["per_page"], self.settings.max_per_page)
        api_params = clean_params(payload)
        api_params["page"] = payload["page"]
        api_params["par_page"] = payload["per_page"]
        raw = await self._get_json("recherche", api_params)
        return raw, payload

    async def get_decision_by_id(self, decision_id: str) -> dict[str, Any]:
        if not decision_id.strip():
            raise PappersValidationError("decision_id is required")
        return await self._get_json(f"decision/{decision_id.strip()}")

    async def get_decision_pdf(self, decision_id: str) -> bytes:
        if not decision_id.strip():
            raise PappersValidationError("decision_id is required")
        return await self._get_bytes(f"decision/{decision_id.strip()}/pdf")
