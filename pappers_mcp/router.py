from __future__ import annotations

from .deduplication import (
    deduplicate_unified_companies,
    deduplicate_unified_decisions,
)
from .source_priority import choose_from_priority


def ordered_backends(
    priority_list: list[str] | None,
    available: list[str],
    default_order: list[str],
) -> list[str]:
    """
    Construit un ordre d'exécution stable des backends.

    Règles :
    - respecte d'abord la priorité fournie
    - conserve seulement les backends réellement disponibles
    - complète ensuite avec l'ordre par défaut
    - supprime les doublons
    """
    ordered: list[str] = []
    priority_list = priority_list or []

    for backend in priority_list:
        if backend in available and backend not in ordered:
            ordered.append(backend)

    for backend in default_order:
        if backend in available and backend not in ordered:
            ordered.append(backend)

    return ordered


def choose_backend_reason_with_priority(
    priority_list: list[str] | None,
    pappers_ok: bool,
    pappers_count: int,
    min_results: int,
) -> tuple[str, str | None]:
    """
    Détermine le backend logique retenu et la raison éventuelle.

    Ce helper ne pilote pas à lui seul tout l'ordre d'exécution,
    mais il fournit une décision cohérente à partir :
    - de la priorité configurée
    - de l'état de Pappers
    - du volume minimal de résultats attendu
    """
    preferred = choose_from_priority(
        priority_list or [],
        ["pappers_justice", "openlegi"],
        "pappers_justice",
    )

    if preferred == "openlegi":
        return "openlegi", "priorité configurée en faveur d'OpenLegi"

    if pappers_ok and pappers_count >= min_results:
        return "pappers_justice", None

    if not pappers_ok:
        return "openlegi", "backend primaire indisponible"

    return "openlegi", "nombre de résultats insuffisant sur le backend primaire"


def explain_source_selection_payload(
    selected_backend: str,
    fallback_reason: str | None,
    pappers_count: int,
    final_count: int,
    priority: list[str] | None = None,
) -> dict:
    """
    Produit une charge utile lisible expliquant la sélection de source.
    """
    return {
        "ok": True,
        "selected_backend": selected_backend,
        "fallback_reason": fallback_reason,
        "pappers_result_count": pappers_count,
        "final_result_count": final_count,
        "priority": priority or [],
    }


def federated_merge_decisions(
    primary_results: list[dict] | None,
    fallback_results: list[dict] | None,
    use_fallback: bool,
) -> list[dict]:
    """
    Fusionne puis déduplique les décisions.
    """
    combined: list[dict] = list(primary_results or [])

    if use_fallback:
        combined.extend(fallback_results or [])

    return deduplicate_unified_decisions(combined)


def federated_merge_companies(results: list[dict] | None) -> list[dict]:
    """
    Déduplique les résultats entreprise.
    """
    return deduplicate_unified_companies(list(results or []))
