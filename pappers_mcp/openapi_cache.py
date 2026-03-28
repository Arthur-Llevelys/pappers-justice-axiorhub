from __future__ import annotations

import json
import hashlib
import time
from pathlib import Path

import httpx


def _cache_file(cache_dir: str, url: str) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return Path(cache_dir) / f"{digest}.json"


def load_openapi_schema_cached(url: str, timeout_seconds: int, cache_dir: str, ttl_seconds: int, force_refresh: bool = False) -> dict:
    path = _cache_file(cache_dir, url)
    now = time.time()
    if path.exists() and not force_refresh:
        age = now - path.stat().st_mtime
        if age <= ttl_seconds:
            return json.loads(path.read_text(encoding="utf-8"))

    with httpx.Client(timeout=timeout_seconds) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def refresh_openapi_cache_entries(entries: list[tuple[str, str]], timeout_seconds: int, cache_dir: str, ttl_seconds: int) -> dict:
    refreshed = []
    for label, url in entries:
        try:
            load_openapi_schema_cached(url, timeout_seconds, cache_dir, ttl_seconds, force_refresh=True)
            refreshed.append({"label": label, "url": url, "status": "refreshed"})
        except Exception as exc:
            refreshed.append({"label": label, "url": url, "status": "error", "error": str(exc)})
    return {"ok": True, "entries": refreshed}
