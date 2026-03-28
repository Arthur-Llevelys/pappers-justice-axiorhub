from __future__ import annotations


def score_unified_decision(decision: dict) -> int:
    score = 0
    if decision.get("title"):
        score += 2
    if decision.get("date"):
        score += 1
    if decision.get("jurisdiction"):
        score += 2
    if decision.get("chamber"):
        score += 1
    if decision.get("rg_number"):
        score += 1
    if decision.get("summary"):
        score += 2
    if decision.get("motivation"):
        score += 4
    if decision.get("dispositif"):
        score += 3
    if decision.get("legal_basis"):
        score += 2
    if decision.get("solution"):
        score += 1
    return score


def score_unified_company(company: dict) -> int:
    score = 0
    if company.get("name"):
        score += 2
    if company.get("siren"):
        score += 3
    if company.get("siret"):
        score += 1
    if company.get("address"):
        score += 1
    if company.get("status"):
        score += 1
    return score
