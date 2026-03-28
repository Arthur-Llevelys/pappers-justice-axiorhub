from __future__ import annotations
from .utils import truncate_text


def strategic_score_from_decision(decision: dict) -> int:
    score = 0
    if decision.get("sommaire"): score += 2
    if decision.get("motivation"): score += 4
    if decision.get("dispositif"): score += 3
    if decision.get("loi_appliquee"): score += 2
    if decision.get("numero_role_general"): score += 1
    if decision.get("publications"): score += 1
    if decision.get("juridiction_chambre"): score += 1
    return score


def rank_decisions_payload(decision_payloads: list[dict]) -> dict:
    ranked = [{"score": strategic_score_from_decision(p.get("decision", {})), "decision": p.get("decision", {})} for p in decision_payloads]
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {"ok": True, "count": len(ranked), "ranked": ranked}


def build_conclusion_ready_citations_from_payload(payload: dict, max_quotes: int = 3) -> dict:
    d = payload.get("decision", {})
    motivation = d.get("motivation") or ""
    lines = [x.strip() for x in motivation.split("\n") if x.strip()] or ([motivation] if motivation else [])
    citations = []
    for chunk in lines[:max_quotes]:
        excerpt = truncate_text(chunk, 500)
        citations.append({
            "heading": f"{d.get('juridiction_nom')}, {d.get('date_decision')}, RG {d.get('numero_role_general')}",
            "quote": excerpt,
            "ready_to_paste": f"> {excerpt}\n\n*{d.get('juridiction_nom')}, {d.get('date_decision')}, RG {d.get('numero_role_general')}*",
        })
    return {"ok": True, "decision_id": d.get("id"), "citations": citations}


def comparative_table_markdown_from_payloads(payloads: list[dict], mode: str = "compact") -> str:
    headers = ["ID", "Date", "Juridiction", "RG", "Solution", "Parties"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for payload in payloads:
        d = payload.get("decision", {})
        row = [str(d.get("id") or ""), str(d.get("date_decision") or ""), str(d.get("juridiction_nom") or ""), str(d.get("numero_role_general") or ""), str(d.get("solution") or ""), str(d.get("parties_formatees") or "")]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)
