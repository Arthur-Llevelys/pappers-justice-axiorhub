from __future__ import annotations
from pathlib import Path
from datetime import datetime
from docx import Document
from .strategist import build_conclusion_ready_citations_from_payload
from .utils import truncate_text


def _safe_filename(prefix: str, suffix: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}.{suffix}"


def export_text_markdown(text: str, exports_dir: str, prefix: str = "document") -> str:
    path = Path(exports_dir) / _safe_filename(prefix, "md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)


def export_text_docx(text: str, exports_dir: str, prefix: str = "document") -> str:
    path = Path(exports_dir) / _safe_filename(prefix, "docx")
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = Document()
    for block in text.split("\n\n"):
        doc.add_paragraph(block)
    doc.save(path)
    return str(path)


def export_jurisprudence_note_markdown_from_payload(payload: dict, exports_dir: str) -> str:
    d = payload.get("decision", {})
    text = ["# Note de jurisprudence", "", f"## {d.get('titre')}", f"- Date : {d.get('date_decision')}", f"- Juridiction : {d.get('juridiction_nom')}", f"- RG : {d.get('numero_role_general')}", ""]
    if d.get("sommaire"):
        text.extend(["## Sommaire", "", d.get("sommaire"), ""])
    if d.get("motivation"):
        text.extend(["## Motivation", "", truncate_text(d.get("motivation"), 3000), ""])
    citations = build_conclusion_ready_citations_from_payload(payload, max_quotes=3).get("citations", [])
    if citations:
        text.extend(["## Citations exploitables", ""])
        for c in citations:
            text.extend([c["ready_to_paste"], ""])
    return export_text_markdown("\n".join(text), exports_dir, prefix="note_jurisprudence")


def export_jurisprudence_note_docx_from_payload(payload: dict, exports_dir: str) -> str:
    d = payload.get("decision", {})
    text = ["Note de jurisprudence", "", d.get("titre") or "Decision", "", f"Date : {d.get('date_decision')}", f"Juridiction : {d.get('juridiction_nom')}", f"RG : {d.get('numero_role_general')}", ""]
    if d.get("sommaire"):
        text.extend(["Sommaire", d.get("sommaire"), ""])
    if d.get("motivation"):
        text.extend(["Motivation", truncate_text(d.get("motivation"), 3000), ""])
    return export_text_docx("\n".join(text), exports_dir, prefix="note_jurisprudence")
