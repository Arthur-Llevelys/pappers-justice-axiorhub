from __future__ import annotations

from .unified_models import UnifiedDecision
from .quality import score_unified_decision


def normalize_pappers_search_response(payload: dict) -> list[dict]:
    results = []
    for item in payload.get("results", []):
        decision = UnifiedDecision(
            source_backend="pappers_justice",
            source_label="Pappers Justice",
            id=item.get("id"),
            title=item.get("titre"),
            date=item.get("date_decision"),
            jurisdiction=item.get("juridiction_nom"),
            chamber=item.get("juridiction_chambre"),
            rg_number=(item.get("source_raw") or {}).get("numero_role_general"),
            solution=item.get("solution"),
            summary=item.get("sommaire"),
            motivation=(item.get("source_raw") or {}).get("motivation"),
            dispositif=(item.get("source_raw") or {}).get("dispositif"),
            legal_basis=(item.get("source_raw") or {}).get("loi_appliquee") or [],
            parties=item.get("parties_formatees"),
            raw=item,
        ).to_dict()
        decision["quality_score"] = score_unified_decision(decision)
        results.append(decision)
    return results


def backend_status_payload(settings, healthchecks: dict | None = None) -> dict:
    payload = {
        "ok": True,
        "backends": {
            "pappers_justice": {"status": "configured", "label": "Pappers Justice", "base_url": settings.pappers_justice_base_url},
            "openlegi": {"status": "configured", "label": "OpenLegi", "openapi_url": settings.openlegi_openapi_url},
            "recherche_entreprises": {"status": "configured", "label": "Recherche Entreprises", "openapi_url": settings.recherche_entreprises_openapi_url},
        },
    }
    if healthchecks is not None:
        payload["healthchecks"] = healthchecks
    return payload
