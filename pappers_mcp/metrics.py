from __future__ import annotations

import time
from .state_store import load_json_file, save_json_file


def _default_metrics():
    return {}


def load_metrics(path: str) -> dict:
    return load_json_file(path, _default_metrics())


def save_metrics(path: str, payload: dict) -> None:
    save_json_file(path, payload)


def record_backend_call(path: str, backend: str, success: bool, latency_ms: int, error: str | None = None) -> dict:
    metrics = load_metrics(path)
    item = metrics.get(backend, {
        "calls": 0,
        "successes": 0,
        "failures": 0,
        "total_latency_ms": 0,
        "avg_latency_ms": 0,
        "last_error": None,
        "last_call_ts": None,
    })
    item["calls"] += 1
    item["total_latency_ms"] += int(latency_ms)
    item["avg_latency_ms"] = int(item["total_latency_ms"] / item["calls"]) if item["calls"] else 0
    item["last_call_ts"] = int(time.time())
    if success:
        item["successes"] += 1
    else:
        item["failures"] += 1
        item["last_error"] = error
    metrics[backend] = item
    save_metrics(path, metrics)
    return metrics


def reset_metrics(path: str) -> dict:
    payload = {}
    save_metrics(path, payload)
    return payload
