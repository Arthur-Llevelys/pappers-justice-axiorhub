from __future__ import annotations


def analyze_case_strategy_payload(
    facts: str,
    discussion_text: str | None,
    arguments: list[dict] | None,
    jurisprudence: list[dict] | None,
    exhibits: list[dict] | None,
) -> dict:
    arguments = arguments or []
    jurisprudence = jurisprudence or []
    exhibits = exhibits or []

    strengths = []
    weaknesses = []
    recommendations = []

    if len(exhibits) >= 3:
        strengths.append("Le dossier paraît suffisamment documenté par plusieurs pièces.")
    else:
        weaknesses.append("Le nombre de pièces paraît limité pour sécuriser la démonstration.")

    if jurisprudence:
        strengths.append("Un appui jurisprudentiel est disponible.")
    else:
        weaknesses.append("Aucune jurisprudence sélectionnée n'a été fournie à ce stade.")

    if len(arguments) >= 2:
        strengths.append("Plusieurs axes d'argumentation peuvent être articulés.")
    elif len(arguments) == 1:
        weaknesses.append("Le dossier semble reposer sur un seul axe principal.")
    else:
        weaknesses.append("Aucun moyen structuré n'a été fourni.")

    lowered_facts = (facts or "").lower()
    lowered_discussion = (discussion_text or "").lower()

    if "rupture" in lowered_facts:
        recommendations.append("Mettre en avant la chronologie, le préavis et la brutalité de la rupture.")
    if "préavis" in lowered_facts or "preavis" in lowered_facts:
        recommendations.append("Isoler les pièces démontrant l'insuffisance ou l'absence de préavis.")
    if "indemn" in lowered_discussion:
        recommendations.append("Relier chaque poste de préjudice à une pièce justificative.")
    if arguments:
        recommendations.append("Hiérarchiser les moyens entre principal, subsidiaire et en tout état de cause.")

    return {
        "ok": True,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "primary_strategy": "Construire un moyen principal étayé par les pièces les plus probantes et la jurisprudence la plus convergente.",
        "secondary_strategy": "Prévoir un axe subsidiaire sur la responsabilité ou l'indemnisation si le fondement principal est discuté.",
    }


def build_argumentation_strategy_payload(arguments: list[dict] | None) -> dict:
    arguments = arguments or []
    prioritized = []
    for idx, arg in enumerate(arguments, start=1):
        score = 0
        if arg.get("legal_basis"):
            score += 2
        if arg.get("jurisprudence"):
            score += 2
        if arg.get("exhibit_numbers"):
            score += 2
        if arg.get("requested_relief"):
            score += 1
        prioritized.append({
            "rank": idx,
            "title": arg.get("title"),
            "score": score,
            "recommendation": "À placer en tête" if score >= 5 else "À conserver en soutien ou en subsidiaire",
        })
    prioritized.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(prioritized, start=1):
        item["rank"] = i
    return {"ok": True, "prioritized_arguments": prioritized}
