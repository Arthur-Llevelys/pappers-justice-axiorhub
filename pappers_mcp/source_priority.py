from __future__ import annotations

from .state_store import load_json_file, save_json_file


def get_source_priority_payload(settings) -> dict:
    persisted = load_json_file(settings.source_priority_file, {})
    priorities = {
        "jurisprudence": persisted.get("jurisprudence", settings.source_priority_jurisprudence),
        "company": persisted.get("company", settings.source_priority_company),
    }
    return {"ok": True, "priorities": priorities}


def set_source_priority_payload(settings, kind: str, backends: list[str], persist: bool = True) -> dict:
    if kind not in {"jurisprudence", "company"}:
        raise ValueError("kind must be either 'jurisprudence' or 'company'")

    allowed = {
        "jurisprudence": {"pappers_justice", "openlegi"},
        "company": {"recherche_entreprises"},
    }

    invalid = [b for b in backends if b not in allowed[kind]]
    if invalid:
        raise ValueError(f"Unsupported backends for {kind}: {invalid}")

    payload = load_json_file(settings.source_priority_file, {})
    payload[kind] = backends

    if persist:
        save_json_file(settings.source_priority_file, payload)

    return {
        "ok": True,
        "kind": kind,
        "backends": backends,
        "persisted": persist,
        "file": settings.source_priority_file if persist else None,
    }


def choose_from_priority(priority_list: list[str], available: list[str], default: str) -> str:
    for backend in priority_list:
        if backend in available:
            return backend
    return default
