from __future__ import annotations

import httpx

from .openapi_discovery import load_openapi_schema, discover_best_operation, build_query_params, operation_url
from .unified_models import UnifiedDecision, UnifiedCompany
from .quality import score_unified_decision, score_unified_company


def _flatten_results(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ["results", "resultats", "items", "data", "hits"]:
            if isinstance(payload.get(key), list):
                return payload.get(key)
    return []


def search_openlegi_jurisprudence(openapi_url: str, timeout_seconds: int, cache_dir: str, ttl_seconds: int, query: dict, force_refresh_schema: bool = False) -> dict:
    schema = load_openapi_schema(openapi_url, timeout_seconds, cache_dir, ttl_seconds, force_refresh=force_refresh_schema)
    discovered = discover_best_operation(openapi_url, schema, target="jurisprudence")
    if not discovered:
        return {"ok": False, "error": "No suitable OpenLegi jurisprudence operation found in OpenAPI schema."}

    url = operation_url(discovered)
    params = build_query_params(discovered, query)

    with httpx.Client(timeout=timeout_seconds) as client:
        if discovered["method"] == "get":
            response = client.get(url, params=params)
        else:
            response = client.post(url, json=params)
        response.raise_for_status()
        payload = response.json()

    results = []
    for item in _flatten_results(payload):
        decision = UnifiedDecision(
            source_backend="openlegi",
            source_label="OpenLegi",
            id=item.get("id") or item.get("cid") or item.get("uuid"),
            title=item.get("title") or item.get("titre") or item.get("intitule"),
            date=item.get("date") or item.get("date_decision"),
            jurisdiction=item.get("juridiction") or item.get("juridiction_nom") or item.get("jurisdiction"),
            chamber=item.get("chambre") or item.get("chamber"),
            rg_number=item.get("numero_role_general") or item.get("rg") or item.get("numero"),
            solution=item.get("solution"),
            summary=item.get("summary") or item.get("sommaire") or item.get("resume"),
            motivation=item.get("motivation"),
            dispositif=item.get("dispositif"),
            legal_basis=item.get("legal_basis") or item.get("loi_appliquee") or [],
            parties=item.get("parties") or item.get("parties_formatees"),
            raw=item,
        ).to_dict()
        decision["quality_score"] = score_unified_decision(decision)
        results.append(decision)

    return {
        "ok": True,
        "discovered_operation": discovered,
        "request_url": url,
        "request_params": params,
        "results": results,
    }


def search_company_backend(openapi_url: str, timeout_seconds: int, cache_dir: str, ttl_seconds: int, name: str | None = None, siren: str | None = None, page: int = 1, per_page: int = 10, force_refresh_schema: bool = False) -> dict:
    schema = load_openapi_schema(openapi_url, timeout_seconds, cache_dir, ttl_seconds, force_refresh=force_refresh_schema)
    discovered = discover_best_operation(openapi_url, schema, target="company")
    if not discovered:
        return {"ok": False, "error": "No suitable company search operation found in OpenAPI schema."}

    url = operation_url(discovered)
    params = build_query_params(discovered, {"name": name, "siren": siren, "page": page, "per_page": per_page})

    with httpx.Client(timeout=timeout_seconds) as client:
        if discovered["method"] == "get":
            response = client.get(url, params=params)
        else:
            response = client.post(url, json=params)
        response.raise_for_status()
        payload = response.json()

    results = []
    for item in _flatten_results(payload):
        company = UnifiedCompany(
            source_backend="recherche_entreprises",
            source_label="Recherche Entreprises",
            name=item.get("name") or item.get("nom_complet") or item.get("denomination") or item.get("nom"),
            siren=item.get("siren"),
            siret=item.get("siret"),
            address=item.get("address") or item.get("siege") or item.get("adresse"),
            status=item.get("status") or item.get("etat_administratif") or item.get("statut"),
            raw=item,
        ).to_dict()
        company["quality_score"] = score_unified_company(company)
        results.append(company)

    return {
        "ok": True,
        "discovered_operation": discovered,
        "request_url": url,
        "request_params": params,
        "results": results,
    }
