from __future__ import annotations
from .utils import ensure_list_of_strings, truncate_text


def normalize_search_response(raw: dict, query: dict, preview_length: int) -> dict:
    results = []
    for item in (raw.get("resultats") or []):
        juridiction = item.get("juridiction") or {}
        corps = item.get("corps")
        results.append({
            "id": item.get("id"),
            "titre": item.get("titre"),
            "date_decision": item.get("date_decision"),
            "juridiction_nom": juridiction.get("nom"),
            "juridiction_code": juridiction.get("code"),
            "juridiction_chambre": juridiction.get("chambre"),
            "code_nac": item.get("code_nac"),
            "solution": item.get("solution"),
            "parties_formatees": item.get("parties_formatees"),
            "publications": ensure_list_of_strings(item.get("publications")),
            "sommaire": item.get("sommaire"),
            "corps_extrait": truncate_text(corps, preview_length),
            "source_raw": item,
        })
    total = raw.get("total")
    page = raw.get("page", query.get("page"))
    per_page = query.get("per_page")
    total_pages = (total + per_page - 1) // per_page if isinstance(total, int) and isinstance(per_page, int) and per_page > 0 else None
    has_next_page = page < total_pages if total_pages else None
    return {"ok": True, "query": query, "pagination": {"page": page, "per_page": per_page, "total": total, "total_pages": total_pages, "has_next_page": has_next_page}, "results": results, "raw_meta": {k: v for k, v in raw.items() if k != "resultats"}}


def normalize_decision_response(raw: dict, preview_length: int) -> dict:
    d = raw.get("decision") if isinstance(raw.get("decision"), dict) else raw
    juridiction = d.get("juridiction") or {}
    corps = d.get("corps")
    return {"ok": True, "decision": {
        "id": d.get("id"),
        "titre": d.get("titre"),
        "date_decision": d.get("date_decision"),
        "numero_role_general": d.get("numero_role_general"),
        "juridiction_nom": juridiction.get("nom"),
        "juridiction_code": juridiction.get("code"),
        "juridiction_chambre": juridiction.get("chambre"),
        "loi_appliquee": ensure_list_of_strings(d.get("loi_appliquee")),
        "code_nac": d.get("code_nac"),
        "solution": d.get("solution"),
        "parties_formatees": d.get("parties_formatees"),
        "publications": ensure_list_of_strings(d.get("publications")),
        "sommaire": d.get("sommaire"),
        "corps": corps,
        "corps_extrait": truncate_text(corps, preview_length),
        "moyens": d.get("moyens"),
        "motivation": d.get("motivation"),
        "dispositif": d.get("dispositif"),
        "siege": ensure_list_of_strings(d.get("siege")),
        "avocats": ensure_list_of_strings(d.get("avocats")),
        "source_raw": d,
    }}


def summarize_normalized_decision(normalized: dict) -> dict:
    d = normalized.get("decision", {})
    return {"ok": True, "decision": d, "summary": {"titre": d.get("titre"), "ratio_decidendi": d.get("motivation"), "arguments_des_parties": d.get("moyens"), "dispositif": d.get("dispositif"), "loi_appliquee": d.get("loi_appliquee", [])}}


def normalize_pdf_response(decision_id: str, raw_bytes_length: int | None = None) -> dict:
    return {"ok": True, "decision_id": decision_id, "pdf_available": True, "pdf_size_bytes": raw_bytes_length}
