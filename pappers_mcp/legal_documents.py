from __future__ import annotations
from .models import LegalDocumentRequest, LegalParty, LegalArgument, ExhibitItem
from .utils import format_piece_reference, apply_inline_references


def _title_for_request(req: LegalDocumentRequest) -> str:
    if req.title_override:
        return req.title_override
    if req.document_type == "conclusions":
        return "Conclusions"
    if req.document_type == "assignation":
        return f"Assignation devant le/la {req.jurisdiction_name}"
    return f"Requête devant le/la {req.jurisdiction_name}"


def _intro_label(req: LegalDocumentRequest) -> str:
    if req.intro_label:
        return req.intro_label
    if "cour" in req.jurisdiction_name.lower():
        return "Plaise à la Cour"
    if req.document_type == "requete":
        return "Objet"
    return "Plaise au Tribunal"


def _piece_block(numbers: list[int], note: str | None = None) -> list[str]:
    ref = format_piece_reference(numbers)
    if not ref:
        return []
    lines = [f"**Pièces citées :** {ref}."]
    if note:
        lines.append(note)
    return lines


def _jurisdiction_style_prefix(req: LegalDocumentRequest, block: str) -> str:
    if req.stylistic_mode == "standard":
        return ""
    j = req.jurisdiction_name.lower()
    if req.stylistic_mode == "contentieux_formel":
        mapping = {
            "facts": "Il sera rappelé que",
            "discussion": "Il résulte de ce qui précède que",
            "procedure": "Il sera observé que",
            "adverse": "La partie adverse ne saurait utilement soutenir que",
            "in_case": "En l'espèce,",
        }
        return mapping.get(block, "")
    if "commerce" in j:
        mapping = {
            "facts": "Il sera rappelé que",
            "discussion": "Il résulte des relations commerciales nouées entre les parties que",
            "procedure": "Il sera observé que",
            "adverse": "La défenderesse ne saurait sérieusement prétendre que",
            "in_case": "En l'espèce,",
        }
        return mapping.get(block, "")
    if "cour" in j:
        mapping = {
            "facts": "Il sera rappelé à la Cour que",
            "discussion": "Il résulte de l'économie du litige que",
            "procedure": "Il sera encore rappelé que",
            "adverse": "L'intimée ne saurait valablement soutenir que",
            "in_case": "En l'espèce,",
        }
        return mapping.get(block, "")
    return {
        "facts": "Il sera rappelé que",
        "discussion": "Il ressort des éléments du dossier que",
        "procedure": "Il sera observé que",
        "adverse": "La partie adverse ne saurait utilement soutenir que",
        "in_case": "En l'espèce,",
    }.get(block, "")


def _apply_style(text: str, prefix: str) -> str:
    if not text:
        return text
    if not prefix:
        return text
    first = text[0].lower() + text[1:] if len(text) > 1 else text.lower()
    return f"{prefix} {first}"


def _format_party(party: LegalParty, heading: str) -> str:
    lines = [f"{heading} :"]
    if party.party_type == "personne_physique":
        identity = f"{party.first_name or ''} {party.last_name or ''}".strip()
        lines.append(f"{identity}, né(e) le {party.birth_date or '[date de naissance]'} à {party.birth_place or '[lieu de naissance]'},")
        lines.append(f"exerçant la profession de {party.profession or '[profession]'},")
        lines.append(f"demeurant {party.address or '[adresse complète]'} ;")
    else:
        lines.append(f"{party.company_name or '[nom de la société]'}, {party.company_form or '[forme sociale]'},")
        lines.append(f"ayant son siège social situé {party.company_address or '[adresse complète du siège social]'},")
        lines.append(f"immatriculée sous le numéro SIREN {party.siren or '[numéro SIREN]'},")
        lines.append(f"représentée par son {party.representative_title or '[Gérant/Président]'} {party.representative_name or 'ou représentant légal en exercice'} ;")
    lines.append(f"[{party.role_label}] ;")
    if party.lawyer_name:
        lawyer = f"Ayant pour avocat : Maître {party.lawyer_name}"
        if party.lawyer_bar:
            lawyer += f", avocat au Barreau de {party.lawyer_bar}"
        lawyer += " ;"
        lines.append(lawyer)
    return "\n".join(lines)


def _format_argument(arg: LegalArgument, req: LegalDocumentRequest) -> str:
    lines = [f"## {arg.title}", "", "### En droit :", ""]
    if arg.legal_basis:
        for item in arg.legal_basis:
            lines.append(f"- {item}")
    else:
        lines.append("- [Textes de loi à compléter]")
    if arg.jurisprudence:
        lines.extend(["", "### Jurisprudence :", ""])
        for j in arg.jurisprudence:
            lines.append(f"- {j}")
    lines.extend(["", "### En l'espèce :", ""])
    facts_application = arg.facts_application or "[Développement en faits à compléter]"
    facts_application = apply_inline_references(facts_application, arg.inline_references)
    facts_application = _apply_style(facts_application, _jurisdiction_style_prefix(req, "in_case"))
    lines.append(facts_application)
    piece_lines = _piece_block(arg.exhibit_numbers, arg.exhibit_reference_note)
    if piece_lines:
        lines.extend([""] + piece_lines)
    if arg.adverse_arguments:
        adverse = _apply_style(arg.adverse_arguments, _jurisdiction_style_prefix(req, "adverse"))
        lines.extend(["", "### Réponse aux arguments adverses :", "", adverse])
    lines.extend(["", "### Demandes en conséquence :", ""])
    if arg.requested_relief:
        for item in arg.requested_relief:
            lines.append(f"- {item}")
    else:
        lines.append("- [Demandes à compléter]")
    lines.append("")
    return "\n".join(lines)


def generate_legal_document_markdown(req: LegalDocumentRequest) -> str:
    lines = [f"# {_title_for_request(req)}", "", _format_party(req.main_party, "POUR"), ""]
    for idx, party in enumerate(req.opposing_parties, start=1):
        heading = "CONTRE" if idx == 1 else "ET CONTRE"
        lines.extend([_format_party(party, heading), ""])
    lines.extend([f"## {_intro_label(req)}", ""])
    if req.object_text:
        lines.extend([req.object_text, ""])
    facts_text = apply_inline_references(req.facts, req.facts_inline_references)
    facts_text = _apply_style(facts_text, _jurisdiction_style_prefix(req, "facts"))
    lines.extend(["## Rappel des faits et de la procédure :", "", facts_text])
    fact_pieces = _piece_block(req.facts_exhibit_numbers, req.facts_exhibit_reference_note)
    if fact_pieces:
        lines.extend([""] + fact_pieces)
    lines.append("")
    if req.procedure_history:
        proc = _apply_style(req.procedure_history, _jurisdiction_style_prefix(req, "procedure"))
        lines.extend([proc, ""])
    lines.extend(["## Discussion :", ""])
    if req.discussion_text:
        discussion_text = apply_inline_references(req.discussion_text, req.discussion_inline_references)
        discussion_text = _apply_style(discussion_text, _jurisdiction_style_prefix(req, "discussion"))
        lines.extend([discussion_text, ""])
    discussion_pieces = _piece_block(req.discussion_exhibit_numbers, req.discussion_exhibit_reference_note)
    if discussion_pieces:
        lines.extend(discussion_pieces + [""])
    for arg in req.arguments:
        lines.append(_format_argument(arg, req))
    lines.extend(["## Sur les frais irrépétibles, les dépens et les frais de procédure :", ""])
    lines.append(req.article_700_text or "Il serait inéquitable de laisser à la charge du demandeur l'intégralité des frais irrépétibles qu'il a dû exposer pour faire valoir ses droits. Il est en conséquence sollicité une indemnité au titre de l'article 700 du code de procédure civile, ou de tout texte équivalent applicable.")
    lines.append(req.costs_text or "Les dépens devront être mis à la charge de la partie adverse.")
    lines.extend(["", "## Par ces motifs :", "", "Vu les textes de loi et de code suivants :"])
    if req.legal_texts:
        for t in req.legal_texts:
            lines.append(f"- {t}")
    else:
        lines.append("- [Textes à compléter]")
    lines.extend(["", "Vu la jurisprudence suivante :"])
    if req.jurisprudence_overview:
        for j in req.jurisprudence_overview:
            lines.append(f"- {j}")
    else:
        lines.append("- [Jurisprudence à compléter]")
    lines.extend(["", "Vu les pièces :"])
    if req.exhibits:
        for p in req.exhibits:
            lines.append(f"- {p}")
    else:
        lines.append("- [Pièces à compléter]")
    lines.extend(["", f"Il est demandé à la / au {req.jurisdiction_name} de :", ""])
    if req.final_requests:
        lines.append("### A titre principal :")
        for item in req.final_requests:
            lines.append(f"- {item}")
        lines.append("")
    if req.subsidiary_requests:
        lines.append("### A titre subsidiaire :")
        for item in req.subsidiary_requests:
            lines.append(f"- {item}")
        lines.append("")
    if req.infinitely_subsidiary_requests:
        lines.append("### A titre infiniment subsidiaire :")
        for item in req.infinitely_subsidiary_requests:
            lines.append(f"- {item}")
        lines.append("")
    if req.reconventional_requests:
        lines.append("### A titre reconventionnel :")
        for item in req.reconventional_requests:
            lines.append(f"- {item}")
        lines.append("")
    if req.in_any_case_requests:
        lines.append("### En tout état de cause :")
        for item in req.in_any_case_requests:
            lines.append(f"- {item}")
        lines.append("")
    if req.additional_notes:
        lines.extend(["## Observations complémentaires :", "", req.additional_notes, ""])
    return "\n".join(lines)


def generate_exhibit_list_markdown(items: list[ExhibitItem]) -> str:
    items = sorted(items, key=lambda x: x.number)
    lines = ["# Bordereau de pièces", ""]
    for item in items:
        lines.append(f"## Pièce n° {item.number}")
        lines.append(f"- Intitulé : {item.title}")
        if item.description:
            lines.append(f"- Description : {item.description}")
        if item.observation:
            lines.append(f"- Observation : {item.observation}")
        lines.append("")
    return "\n".join(lines)


def generate_conclusions_outline_markdown(req: LegalDocumentRequest) -> str:
    lines = ["# Plan de conclusions", ""]
    lines.append("1. Rappel des faits et de la procédure")
    if req.facts_exhibit_numbers:
        lines.append(f"   - {format_piece_reference(req.facts_exhibit_numbers)}")
    lines.append("2. Discussion")
    if req.discussion_exhibit_numbers:
        lines.append(f"   - {format_piece_reference(req.discussion_exhibit_numbers)}")
    for idx, arg in enumerate(req.arguments, start=1):
        lines.append(f"   2.{idx} {arg.title}")
        lines.append("       - En droit")
        lines.append("       - En l'espèce")
        if arg.exhibit_numbers:
            lines.append(f"       - {format_piece_reference(arg.exhibit_numbers)}")
        lines.append("       - Réponse aux arguments adverses")
        lines.append("       - Demandes en conséquence")
    lines.append("3. Sur les frais irrépétibles, les dépens et les frais de procédure")
    lines.append("4. Par ces motifs")
    return "\n".join(lines)


def generate_case_file_bundle_markdown(req: LegalDocumentRequest, exhibit_list_markdown: str) -> str:
    outline = generate_conclusions_outline_markdown(req)
    act = generate_legal_document_markdown(req)
    lines = ["# Dossier complet", "", "## Sommaire", "", "1. Plan de conclusions", "2. Projet d'acte", "3. Bordereau de pièces", "4. Pièces citées", "5. Annexes", "", outline, "", act, "", exhibit_list_markdown, "", "## Pièces citées", ""]
    if req.facts_exhibit_numbers:
        lines.append(f"- Faits : {format_piece_reference(req.facts_exhibit_numbers)}")
    if req.discussion_exhibit_numbers:
        lines.append(f"- Discussion : {format_piece_reference(req.discussion_exhibit_numbers)}")
    for idx, arg in enumerate(req.arguments, start=1):
        if arg.exhibit_numbers:
            lines.append(f"- Moyen {idx} ({arg.title}) : {format_piece_reference(arg.exhibit_numbers)}")
    if not (req.facts_exhibit_numbers or req.discussion_exhibit_numbers or any(a.exhibit_numbers for a in req.arguments)):
        lines.append("- [Pièces citées à compléter]")
    lines.extend(["", "## Annexes", "", req.additional_notes or "[Annexes / notes complémentaires à compléter]"])
    return "\n".join(lines)


def generate_exhibit_reference_map(req: LegalDocumentRequest) -> dict:
    mapping = {}
    if req.facts_exhibit_numbers:
        mapping["faits"] = req.facts_exhibit_numbers
    if req.discussion_exhibit_numbers:
        mapping["discussion"] = req.discussion_exhibit_numbers
    for idx, arg in enumerate(req.arguments, start=1):
        if arg.exhibit_numbers:
            mapping[f"moyen_{idx}_{arg.title}"] = arg.exhibit_numbers
    return mapping
