from __future__ import annotations

from .deduplication import deduplicate_unified_decisions, deduplicate_unified_companies
from .source_priority import choose_from_priority


def choose_backend_reason_with_priority(priority_list: list[str], pappers_ok: bool, pappers_count: int, min_results: int) -> tuple[str, str | None]:
    preferred = choose_from_priority(priority_list, ["pappers_justice", "openlegi"], "pappers_justice")
    if preferred == "openlegi":
        if pappers_ok and pappers_count >= min_results:
            return "openlegi", "priorité configurée en faveur d'OpenLegi"
        return "openlegi", "priorité configurée en faveur d'OpenLegi"
    if pappers_ok and pappers_count >= min_results:
        return "pappers_justice", None
    if not pappers_ok:
        return "openlegi", "backend primaire indisponible"
    return "openlegi", "nombre de résultats insuffisant sur le backend primaire"


def explain_source_selection_payload(selected_backend: str, fallback_reason: str | None, pappers_count: int, final_count: int, priority: list[str] | None = None) -> dict:
    return {
        "ok": True,
        "selected_backend": selected_backend,
        "fallback_reason": fallback_reason,
        "pappers_result_count": pappers_count,
        "final_result_count": final_count,
        "priority": priority or [],
    }


def federated_merge_decisions(primary_results: list[dict], fallback_results: list[dict], use_fallback: bool) -> list[dict]:
    combined = list(primary_results)
    if use_fallback:
        combined.extend(fallback_results)
    return deduplicate_unified_decisions(combined)


def federated_merge_companies(results: list[dict]) -> list[dict]:
    return deduplicate_unified_companies(results)
