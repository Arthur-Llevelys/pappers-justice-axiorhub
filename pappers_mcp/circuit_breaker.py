from __future__ import annotations

import time
from .state_store import load_json_file, save_json_file


def _default_state():
    return {}


def load_circuit_breaker(path: str) -> dict:
    return load_json_file(path, _default_state())


def save_circuit_breaker(path: str, payload: dict) -> None:
    save_json_file(path, payload)


def _backend_state(data: dict, backend: str) -> dict:
    if backend not in data:
        data[backend] = {
            "state": "closed",
            "failure_count": 0,
            "last_failure_ts": None,
            "opened_ts": None,
            "last_error": None,
        }
    return data[backend]


def can_call_backend(path: str, backend: str, reset_timeout_seconds: int) -> tuple[bool, dict]:
    data = load_circuit_breaker(path)
    state = _backend_state(data, backend)
    now = int(time.time())

    if state["state"] == "open":
        opened_ts = state.get("opened_ts") or 0
        if now - opened_ts >= reset_timeout_seconds:
            state["state"] = "half_open"
            save_circuit_breaker(path, data)
            return True, state
        return False, state

    return True, state


def record_backend_success(path: str, backend: str) -> dict:
    data = load_circuit_breaker(path)
    state = _backend_state(data, backend)
    state["state"] = "closed"
    state["failure_count"] = 0
    state["last_error"] = None
    save_circuit_breaker(path, data)
    return data


def record_backend_failure(path: str, backend: str, failure_threshold: int, error: str | None = None) -> dict:
    data = load_circuit_breaker(path)
    state = _backend_state(data, backend)
    now = int(time.time())
    state["failure_count"] += 1
    state["last_failure_ts"] = now
    state["last_error"] = error
    if state["failure_count"] >= failure_threshold:
        state["state"] = "open"
        state["opened_ts"] = now
    save_circuit_breaker(path, data)
    return data


def reset_backend_circuit_breaker(path: str, backend: str | None = None) -> dict:
    data = load_circuit_breaker(path)
    if backend:
        data[backend] = {
            "state": "closed",
            "failure_count": 0,
            "last_failure_ts": None,
            "opened_ts": None,
            "last_error": None,
        }
    else:
        data = {}
    save_circuit_breaker(path, data)
    return data
