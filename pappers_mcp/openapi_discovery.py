from __future__ import annotations

from urllib.parse import urljoin

from .openapi_cache import load_openapi_schema_cached

SEARCH_HINTS_JURISPRUDENCE = [
    "jurisprudence", "decision", "judiciaire", "search", "recherche", "legi"
]
SEARCH_HINTS_COMPANY = [
    "entreprise", "company", "siren", "siret", "search", "recherche"
]


def load_openapi_schema(url: str, timeout_seconds: int, cache_dir: str, ttl_seconds: int, force_refresh: bool = False) -> dict:
    return load_openapi_schema_cached(url, timeout_seconds, cache_dir, ttl_seconds, force_refresh=force_refresh)


def _score_operation(path: str, method: str, operation: dict, hints: list[str]) -> int:
    hay = " ".join([
        path.lower(),
        method.lower(),
        str(operation.get("operationId", "")).lower(),
        str(operation.get("summary", "")).lower(),
        str(operation.get("description", "")).lower(),
    ])
    score = 0
    if method.lower() == "get":
        score += 2
    for hint in hints:
        if hint in hay:
            score += 2
    params = operation.get("parameters", []) or []
    param_names = {str(p.get("name", "")).lower() for p in params}
    if "q" in param_names:
        score += 2
    if "query" in param_names:
        score += 2
    if "page" in param_names:
        score += 1
    if "limit" in param_names or "per_page" in param_names:
        score += 1
    return score


def discover_best_operation(openapi_url: str, schema: dict, target: str) -> dict | None:
    paths = schema.get("paths") or {}
    hints = SEARCH_HINTS_JURISPRUDENCE if target == "jurisprudence" else SEARCH_HINTS_COMPANY
    best = None
    for path, methods in paths.items():
        for method, operation in (methods or {}).items():
            if method.lower() not in {"get", "post"}:
                continue
            score = _score_operation(path, method, operation or {}, hints)
            candidate = {
                "path": path,
                "method": method.lower(),
                "operation": operation or {},
                "score": score,
            }
            if best is None or score > best["score"]:
                best = candidate
    if not best:
        return None
    best["base_url"] = openapi_url.rsplit("/openapi.json", 1)[0]
    return best


def build_query_params(operation: dict, user_query: dict) -> dict:
    params = {}
    parameters = operation.get("operation", {}).get("parameters", []) or []
    names = [str(p.get("name", "")) for p in parameters]

    q_like_value = user_query.get("q") or user_query.get("question") or user_query.get("parties") or user_query.get("name") or user_query.get("siren")
    for name in names:
        lname = name.lower()
        if lname in {"q", "query", "search", "texte", "terme"} and q_like_value:
            params[name] = q_like_value
        elif lname in {"page"} and user_query.get("page"):
            params[name] = user_query.get("page")
        elif lname in {"per_page", "limit", "page_size"} and user_query.get("per_page"):
            params[name] = user_query.get("per_page")
        elif lname in {"siren"} and user_query.get("siren"):
            params[name] = user_query.get("siren")
        elif lname in {"nom", "name", "denomination"} and user_query.get("name"):
            params[name] = user_query.get("name")
    return params


def operation_url(discovered: dict) -> str:
    return urljoin(discovered["base_url"].rstrip("/") + "/", discovered["path"].lstrip("/"))
