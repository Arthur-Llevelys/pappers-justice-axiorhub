from __future__ import annotations


def _decision_key(decision: dict) -> tuple:
    if decision.get("id"):
        return ("id", str(decision.get("id")).strip().lower())
    return (
        "composite",
        str(decision.get("title") or "").strip().lower(),
        str(decision.get("date") or "").strip().lower(),
        str(decision.get("jurisdiction") or "").strip().lower(),
        str(decision.get("rg_number") or "").strip().lower(),
    )


def _company_key(company: dict) -> tuple:
    if company.get("siren"):
        return ("siren", str(company.get("siren")).strip())
    return ("name", str(company.get("name") or "").strip().lower())


def deduplicate_unified_decisions(decisions: list[dict]) -> list[dict]:
    best = {}
    for decision in decisions:
        k = _decision_key(decision)
        current = best.get(k)
        if current is None or decision.get("quality_score", 0) > current.get("quality_score", 0):
            best[k] = decision
    return list(best.values())


def deduplicate_unified_companies(companies: list[dict]) -> list[dict]:
    best = {}
    for company in companies:
        k = _company_key(company)
        current = best.get(k)
        if current is None or company.get("quality_score", 0) > current.get("quality_score", 0):
            best[k] = company
    return list(best.values())
