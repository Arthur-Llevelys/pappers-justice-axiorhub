from __future__ import annotations

import time
import httpx


def check_url_json(url: str, timeout_seconds: int) -> dict:
    started = time.time()
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
        return {
            "status": "ok",
            "latency_ms": int((time.time() - started) * 1000),
            "content_type": response.headers.get("Content-Type"),
            "top_level_keys": list(payload.keys())[:10] if isinstance(payload, dict) else [],
        }
    except Exception as exc:
        return {
            "status": "error",
            "latency_ms": int((time.time() - started) * 1000),
            "error": str(exc),
        }


def run_backend_healthchecks_payload(settings) -> dict:
    checks = {
        "openlegi_openapi": check_url_json(settings.openlegi_openapi_url, settings.openapi_discovery_timeout_seconds),
        "recherche_entreprises_openapi": check_url_json(settings.recherche_entreprises_openapi_url, settings.openapi_discovery_timeout_seconds),
    }
    return {"ok": True, "checks": checks}
