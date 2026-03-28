from __future__ import annotations
from .utils import truncate_text


def render_search_results_markdown_from_payload(payload: dict, mode: str = "compact") -> str:
    lines = ["# Resultats de recherche", ""]
    for idx, item in enumerate(payload.get("results", []), start=1):
        lines.append(f"## {idx}. {item.get('titre') or 'Decision sans titre'}")
        lines.append(f"- ID : `{item.get('id')}`")
        lines.append(f"- Date : {item.get('date_decision')}")
        lines.append(f"- Juridiction : {item.get('juridiction_nom')}")
        if item.get("sommaire"):
            lines.extend(["", item.get("sommaire"), ""])
    return "\n".join(lines)


def render_decision_markdown_from_payload(payload: dict, mode: str = "compact") -> str:
    d = payload.get("decision", {})
    lines = [f"# {d.get('titre') or 'Decision'}", "", f"- Date : {d.get('date_decision')}", f"- RG : {d.get('numero_role_general')}", f"- Juridiction : {d.get('juridiction_nom')}", ""]
    if d.get("motivation"):
        lines.extend(["## Motivation", "", d.get("motivation") if mode == "full" else truncate_text(d.get("motivation"), 1500), ""])
    if d.get("dispositif"):
        lines.extend(["## Dispositif", "", d.get("dispositif")])
    return "\n".join(lines)


def extract_motivation_snippets_from_payload(payload: dict, query: str | None = None, max_snippets: int = 3, context_chars: int = 240) -> dict:
    motivation = payload.get("decision", {}).get("motivation") or ""
    if not motivation:
        return {"ok": True, "snippets": [], "message": "Aucune motivation exploitable disponible."}
    if query:
        idx = motivation.lower().find(query.lower())
        if idx >= 0:
            left = max(0, idx - context_chars)
            right = min(len(motivation), idx + len(query) + context_chars)
            return {"ok": True, "query": query, "snippets": [motivation[left:right].strip()], "count": 1}
    return {"ok": True, "query": query, "snippets": [motivation[:context_chars*2]], "count": 1}
