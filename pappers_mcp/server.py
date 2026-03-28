from __future__ import annotations

import time
from fastmcp import FastMCP

from .client import PappersJusticeClient
from .config import Settings
from .exceptions import PappersAPIError, PappersValidationError
from .models import DecisionSearchParams, LegalDocumentRequest, LegalParty, LegalArgument, ExhibitItem, InlineReference
from .normalizers import normalize_decision_response, normalize_pdf_response, normalize_search_response, summarize_normalized_decision
from .renderers import render_decision_markdown_from_payload, render_search_results_markdown_from_payload, extract_motivation_snippets_from_payload
from .strategist import rank_decisions_payload, build_conclusion_ready_citations_from_payload, comparative_table_markdown_from_payloads
from .legal_documents import generate_legal_document_markdown, generate_exhibit_list_markdown, generate_conclusions_outline_markdown, generate_case_file_bundle_markdown, generate_exhibit_reference_map
from .exporters import export_text_markdown, export_text_docx, export_jurisprudence_note_markdown_from_payload, export_jurisprudence_note_docx_from_payload
from .logging_config import configure_logging
from .analysis import analyze_case_strategy_payload, build_argumentation_strategy_payload
from .utils import suggest_inline_references_for_text
from .backends import normalize_pappers_search_response, backend_status_payload
from .router import choose_backend_reason_with_priority, explain_source_selection_payload, federated_merge_decisions, federated_merge_companies, ordered_backends
from .remote_backends import search_openlegi_jurisprudence, search_company_backend
from .healthchecks import run_backend_healthchecks_payload
from .openapi_cache import refresh_openapi_cache_entries
from .source_priority import get_source_priority_payload, set_source_priority_payload
from .metrics import load_metrics, reset_metrics, record_backend_call
from .circuit_breaker import load_circuit_breaker, can_call_backend, record_backend_success, record_backend_failure, reset_backend_circuit_breaker


def create_mcp() -> FastMCP:
    settings = Settings.from_env()
    logger = configure_logging(settings.log_level)
    client = PappersJusticeClient(settings, logger)
    mcp = FastMCP("pappers-justice-timo")

    health_state = run_backend_healthchecks_payload(settings)["checks"] if settings.auto_healthcheck_on_start else {}

    async def _search(**kwargs):
        params = DecisionSearchParams(**kwargs)
        raw, query_payload = await client.search_decisions(params)
        return normalize_search_response(raw, query_payload, settings.content_preview_length)

    async def _decision(decision_id: str):
        raw = await client.get_decision_by_id(decision_id)
        return normalize_decision_response(raw, settings.content_preview_length)

    def _inline_refs(items):
        return [InlineReference(**x) for x in (items or [])]

    def _current_priorities():
        return get_source_priority_payload(settings)["priorities"]

    def _build_request(
        document_type: str,
        jurisdiction_name: str,
        main_party: dict,
        opposing_parties: list[dict],
        facts: str,
        facts_exhibit_numbers: list[int] | None = None,
        facts_exhibit_reference_note: str | None = None,
        facts_inline_references: list[dict] | None = None,
        procedure_history: str | None = None,
        object_text: str | None = None,
        discussion_text: str | None = None,
        discussion_exhibit_numbers: list[int] | None = None,
        discussion_exhibit_reference_note: str | None = None,
        discussion_inline_references: list[dict] | None = None,
        legal_texts: list[str] | None = None,
        jurisprudence_overview: list[str] | None = None,
        arguments: list[dict] | None = None,
        article_700_text: str | None = None,
        costs_text: str | None = None,
        final_requests: list[str] | None = None,
        subsidiary_requests: list[str] | None = None,
        infinitely_subsidiary_requests: list[str] | None = None,
        reconventional_requests: list[str] | None = None,
        in_any_case_requests: list[str] | None = None,
        exhibits: list[str] | None = None,
        title_override: str | None = None,
        intro_label: str | None = None,
        additional_notes: str | None = None,
        stylistic_mode: str = "juridiction_adaptee",
    ) -> LegalDocumentRequest:
        return LegalDocumentRequest(
            document_type=document_type,
            jurisdiction_name=jurisdiction_name,
            stylistic_mode=stylistic_mode,
            title_override=title_override,
            intro_label=intro_label,
            main_party=LegalParty(**main_party),
            opposing_parties=[LegalParty(**p) for p in (opposing_parties or [])],
            facts=facts,
            facts_exhibit_numbers=facts_exhibit_numbers or [],
            facts_exhibit_reference_note=facts_exhibit_reference_note,
            facts_inline_references=_inline_refs(facts_inline_references),
            procedure_history=procedure_history,
            object_text=object_text,
            discussion_text=discussion_text,
            discussion_exhibit_numbers=discussion_exhibit_numbers or [],
            discussion_exhibit_reference_note=discussion_exhibit_reference_note,
            discussion_inline_references=_inline_refs(discussion_inline_references),
            legal_texts=legal_texts or [],
            jurisprudence_overview=jurisprudence_overview or [],
            arguments=[LegalArgument(**a) for a in (arguments or [])],
            article_700_text=article_700_text,
            costs_text=costs_text,
            final_requests=final_requests or [],
            subsidiary_requests=subsidiary_requests or [],
            infinitely_subsidiary_requests=infinitely_subsidiary_requests or [],
            reconventional_requests=reconventional_requests or [],
            in_any_case_requests=in_any_case_requests or [],
            exhibits=exhibits or [],
            additional_notes=additional_notes,
        )

    @mcp.tool()
    async def refresh_openapi_cache():
        return refresh_openapi_cache_entries(
            [
                ("openlegi", settings.openlegi_openapi_url),
                ("recherche_entreprises", settings.recherche_entreprises_openapi_url),
            ],
            settings.openapi_discovery_timeout_seconds,
            settings.openapi_cache_dir,
            settings.openapi_cache_ttl_seconds,
        )

    @mcp.tool()
    async def run_backend_healthchecks():
        nonlocal health_state
        payload = run_backend_healthchecks_payload(settings)
        health_state = payload["checks"]
        return payload

    @mcp.tool()
    async def get_backend_status():
        return backend_status_payload(settings, healthchecks=health_state)

    @mcp.tool()
    async def get_source_priority():
        return get_source_priority_payload(settings)

    @mcp.tool()
    async def set_source_priority(kind: str, backends: list[str], persist: bool = True):
        return set_source_priority_payload(settings, kind, backends, persist=persist)

    @mcp.tool()
    async def get_backend_metrics():
        return {"ok": True, "metrics": load_metrics(settings.backend_metrics_file)}

    @mcp.tool()
    async def reset_backend_metrics():
        return {"ok": True, "metrics": reset_metrics(settings.backend_metrics_file)}

    @mcp.tool()
    async def get_circuit_breaker_status():
        return {"ok": True, "circuit_breaker": load_circuit_breaker(settings.circuit_breaker_file)}

    @mcp.tool()
    async def reset_circuit_breaker(backend: str | None = None):
        return {"ok": True, "circuit_breaker": reset_backend_circuit_breaker(settings.circuit_breaker_file, backend)}

    @mcp.tool()
    async def search_decisions(**kwargs):
        started = time.time()
        try:
            result = await _search(**kwargs)
            record_backend_call(settings.backend_metrics_file, "pappers_justice", True, int((time.time() - started) * 1000))
            record_backend_success(settings.circuit_breaker_file, "pappers_justice")
            return result
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            latency = int((time.time() - started) * 1000)
            record_backend_call(settings.backend_metrics_file, "pappers_justice", False, latency, str(exc))
            record_backend_failure(settings.circuit_breaker_file, "pappers_justice", settings.circuit_breaker_failure_threshold, str(exc))
            logger.error("search_decisions failed", extra={"extra": {"error": str(exc)}})
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def search_decisions_by_keyword(q: str, **kwargs):
        return await search_decisions(q=q, **kwargs)

    @mcp.tool()
    async def search_decisions_by_question(question: str, **kwargs):
        return await search_decisions(question=question, **kwargs)

    @mcp.tool()
    async def search_decisions_by_party(parties: str, **kwargs):
        return await search_decisions(parties=parties, **kwargs)

    @mcp.tool()
    async def search_decisions_by_rg_number(numero_rg: str, **kwargs):
        return await search_decisions(numero_rg=numero_rg, **kwargs)

    @mcp.tool()
    async def federated_search_jurisprudence(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        juridiction: list[str] | None = None,
        date_decision_min: str | None = None,
        date_decision_max: str | None = None,
        page: int = 1,
        per_page: int = 10,
        min_results: int = 3,
        include_fallback_results: bool = True,
        force_refresh_schema: bool = False,
        source_priority: list[str] | None = None,
    ):
        nonlocal health_state

        if settings.auto_healthcheck_before_search:
            health_state = run_backend_healthchecks_payload(settings)["checks"]

        priorities = _current_priorities()
        priority = source_priority or priorities.get("jurisprudence", settings.source_priority_jurisprudence)

        allow_pappers, pappers_cb = can_call_backend(settings.circuit_breaker_file, "pappers_justice", settings.circuit_breaker_reset_timeout_seconds)

        if allow_pappers:
            pappers_payload = await search_decisions(
                q=q,
                question=question,
                parties=parties,
                numero_rg=numero_rg,
                juridiction=juridiction,
                date_decision_min=date_decision_min,
                date_decision_max=date_decision_max,
                page=page,
                per_page=per_page,
            )
            pappers_ok = bool(pappers_payload.get("ok"))
            pappers_results = normalize_pappers_search_response(pappers_payload) if pappers_ok else []
        else:
            pappers_payload = {"ok": False, "error": "Circuit breaker open for pappers_justice"}
            pappers_ok = False
            pappers_results = []

        pappers_count = len(pappers_results)
        selected_backend, fallback_reason = choose_backend_reason_with_priority(priority, pappers_ok, pappers_count, min_results)
        if not allow_pappers:
            selected_backend = "openlegi"
            fallback_reason = "circuit breaker ouvert pour pappers_justice"

        fallback_results = []
        fallback_meta = None

        if selected_backend != "pappers_justice" and include_fallback_results:
            allow_openlegi, openlegi_cb = can_call_backend(settings.circuit_breaker_file, "openlegi", settings.circuit_breaker_reset_timeout_seconds)
            if allow_openlegi:
                started = time.time()
                try:
                    fallback_payload = search_openlegi_jurisprudence(
                        settings.openlegi_openapi_url,
                        settings.openapi_discovery_timeout_seconds,
                        settings.openapi_cache_dir,
                        settings.openapi_cache_ttl_seconds,
                        {
                            "q": q,
                            "question": question,
                            "parties": parties,
                            "numero_rg": numero_rg,
                            "page": page,
                            "per_page": per_page,
                        },
                        force_refresh_schema=force_refresh_schema,
                    )
                    latency = int((time.time() - started) * 1000)
                    if fallback_payload.get("ok"):
                        record_backend_call(settings.backend_metrics_file, "openlegi", True, latency)
                        record_backend_success(settings.circuit_breaker_file, "openlegi")
                        fallback_results = fallback_payload.get("results", [])
                        fallback_meta = {
                            "request_url": fallback_payload.get("request_url"),
                            "request_params": fallback_payload.get("request_params"),
                            "discovered_operation": fallback_payload.get("discovered_operation"),
                        }
                        for item in fallback_results:
                            item["fallback_reason"] = fallback_reason
                    else:
                        record_backend_call(settings.backend_metrics_file, "openlegi", False, latency, fallback_payload.get("error"))
                        record_backend_failure(settings.circuit_breaker_file, "openlegi", settings.circuit_breaker_failure_threshold, fallback_payload.get("error"))
                except Exception as exc:
                    latency = int((time.time() - started) * 1000)
                    record_backend_call(settings.backend_metrics_file, "openlegi", False, latency, str(exc))
                    record_backend_failure(settings.circuit_breaker_file, "openlegi", settings.circuit_breaker_failure_threshold, str(exc))
                    fallback_reason = f"{fallback_reason or 'fallback'} ; erreur backend OpenLegi: {exc}"
            else:
                fallback_reason = f"{fallback_reason or 'fallback'} ; circuit breaker ouvert pour openlegi"

        merged = federated_merge_decisions(pappers_results, fallback_results, use_fallback=bool(fallback_results))
        merged.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        return {
            "ok": True,
            "selected_backend": selected_backend,
            "fallback_reason": fallback_reason,
            "results": merged,
            "result_count": len(merged),
            "source_trace": {
                "priority": priority,
                "pappers_ok": pappers_ok,
                "pappers_result_count": pappers_count,
                "fallback_used": bool(fallback_results),
                "fallback_meta": fallback_meta,
            },
        }

    @mcp.tool()
    async def fallback_search_jurisprudence(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
    ):
        fed = await federated_search_jurisprudence(
            q=q,
            question=question,
            parties=parties,
            numero_rg=numero_rg,
            include_fallback_results=True,
            min_results=999999,
        )
        fed["forced_fallback"] = True
        return fed

    @mcp.tool()
    async def federated_search_company(
        name: str | None = None,
        siren: str | None = None,
        page: int = 1,
        per_page: int = 10,
        force_refresh_schema: bool = False,
        source_priority: list[str] | None = None,
    ):
        nonlocal health_state

        if settings.auto_healthcheck_before_search:
            health_state = run_backend_healthchecks_payload(settings)["checks"]

        priorities = _current_priorities()
        priority = source_priority or priorities.get("company", settings.source_priority_company)
        selected_backend = priority[0] if priority else "recherche_entreprises"

        allow_company, company_cb = can_call_backend(settings.circuit_breaker_file, "recherche_entreprises", settings.circuit_breaker_reset_timeout_seconds)
        if not allow_company:
            return {"ok": False, "error": "Circuit breaker open for recherche_entreprises", "selected_backend": selected_backend}

        started = time.time()
        try:
            payload = search_company_backend(
                settings.recherche_entreprises_openapi_url,
                settings.openapi_discovery_timeout_seconds,
                settings.openapi_cache_dir,
                settings.openapi_cache_ttl_seconds,
                name=name,
                siren=siren,
                page=page,
                per_page=per_page,
                force_refresh_schema=force_refresh_schema,
            )
            latency = int((time.time() - started) * 1000)
            if not payload.get("ok"):
                record_backend_call(settings.backend_metrics_file, "recherche_entreprises", False, latency, payload.get("error"))
                record_backend_failure(settings.circuit_breaker_file, "recherche_entreprises", settings.circuit_breaker_failure_threshold, payload.get("error"))
                return payload
            record_backend_call(settings.backend_metrics_file, "recherche_entreprises", True, latency)
            record_backend_success(settings.circuit_breaker_file, "recherche_entreprises")
            results = federated_merge_companies(payload.get("results", []))
            results.sort(key=lambda x: x.get("quality_score", 0), reverse=True)
            return {
                "ok": True,
                "selected_backend": selected_backend,
                "results": results,
                "result_count": len(results),
                "source_trace": {
                    "priority": priority,
                    "request_url": payload.get("request_url"),
                    "request_params": payload.get("request_params"),
                    "discovered_operation": payload.get("discovered_operation"),
                },
            }
        except Exception as exc:
            latency = int((time.time() - started) * 1000)
            record_backend_call(settings.backend_metrics_file, "recherche_entreprises", False, latency, str(exc))
            record_backend_failure(settings.circuit_breaker_file, "recherche_entreprises", settings.circuit_breaker_failure_threshold, str(exc))
            return {"ok": False, "error": str(exc), "selected_backend": selected_backend}

    @mcp.tool()
    async def explain_source_selection(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        min_results: int = 3,
        source_priority: list[str] | None = None,
    ):
        fed = await federated_search_jurisprudence(q=q, question=question, parties=parties, numero_rg=numero_rg, min_results=min_results, source_priority=source_priority)
        return explain_source_selection_payload(
            fed.get("selected_backend"),
            fed.get("fallback_reason"),
            fed.get("source_trace", {}).get("pappers_result_count", 0),
            fed.get("result_count", 0),
            priority=fed.get("source_trace", {}).get("priority"),
        )

    @mcp.tool()
    async def get_decision_by_id(decision_id: str):
        try:
            return await _decision(decision_id)
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def get_decision_pdf_info(decision_id: str):
        try:
            data = await client.get_decision_pdf(decision_id)
            return normalize_pdf_response(decision_id, len(data))
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def summarize_decision_for_llm(decision_id: str):
        try:
            normalized = await _decision(decision_id)
            return summarize_normalized_decision(normalized)
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def render_search_results_markdown(mode: str = "compact", **kwargs):
        payload = await search_decisions(**kwargs)
        if not payload.get("ok"):
            return payload
        return {"ok": True, "mode": mode, "markdown": render_search_results_markdown_from_payload(payload, mode=mode), "data": payload}

    @mcp.tool()
    async def render_decision_markdown(decision_id: str, mode: str = "compact"):
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return {"ok": True, "mode": mode, "markdown": render_decision_markdown_from_payload(payload, mode=mode), "data": payload}

    @mcp.tool()
    async def extract_motivation_snippets(decision_id: str, query: str | None = None, max_snippets: int = 3):
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return extract_motivation_snippets_from_payload(payload, query=query, max_snippets=max_snippets)

    @mcp.tool()
    async def rank_decisions_strategically(decision_ids: list[str]):
        payloads = []
        for decision_id in decision_ids:
            payload = await get_decision_by_id(decision_id)
            if payload.get("ok"):
                payloads.append(payload)
        return rank_decisions_payload(payloads)

    @mcp.tool()
    async def build_conclusion_ready_citations(decision_id: str, max_quotes: int = 3):
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return build_conclusion_ready_citations_from_payload(payload, max_quotes=max_quotes)

    @mcp.tool()
    async def render_comparative_table_markdown(decision_ids: list[str], mode: str = "compact"):
        payloads = []
        for decision_id in decision_ids:
            payload = await get_decision_by_id(decision_id)
            if payload.get("ok"):
                payloads.append(payload)
        return {"ok": True, "mode": mode, "markdown": comparative_table_markdown_from_payloads(payloads, mode=mode), "count": len(payloads)}

    @mcp.tool()
    async def analyze_case_strategy(facts: str, discussion_text: str | None = None, arguments: list[dict] | None = None, jurisprudence: list[dict] | None = None, exhibits: list[dict] | None = None):
        return analyze_case_strategy_payload(facts, discussion_text, arguments, jurisprudence, exhibits)

    @mcp.tool()
    async def build_argumentation_strategy(arguments: list[dict] | None = None):
        return build_argumentation_strategy_payload(arguments)

    @mcp.tool()
    async def suggest_inline_references(facts: str | None = None, discussion_text: str | None = None, arguments: list[dict] | None = None, exhibits: list[dict] | None = None):
        exhibits = exhibits or []
        suggestions = {
            "facts_inline_references": suggest_inline_references_for_text(facts or "", exhibits),
            "discussion_inline_references": suggest_inline_references_for_text(discussion_text or "", exhibits),
            "argument_inline_references": [],
        }
        for arg in arguments or []:
            suggestions["argument_inline_references"].append({
                "title": arg.get("title"),
                "inline_references": suggest_inline_references_for_text(arg.get("facts_application") or "", exhibits),
            })
        return {"ok": True, "suggestions": suggestions}

    @mcp.tool()
    async def generate_legal_document(**kwargs):
        try:
            req = _build_request(**kwargs)
            markdown = generate_legal_document_markdown(req)
            return {"ok": True, "document_type": kwargs.get("document_type"), "markdown": markdown, "request": req.model_dump()}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def generate_conclusions_document(**kwargs):
        return await generate_legal_document(document_type="conclusions", **kwargs)

    @mcp.tool()
    async def generate_assignation_document(**kwargs):
        return await generate_legal_document(document_type="assignation", **kwargs)

    @mcp.tool()
    async def generate_requete_document(**kwargs):
        return await generate_legal_document(document_type="requete", **kwargs)

    @mcp.tool()
    async def generate_exhibit_list(exhibits: list[dict]):
        items = [ExhibitItem(**item) for item in exhibits]
        markdown = generate_exhibit_list_markdown(items)
        return {"ok": True, "markdown": markdown, "count": len(items), "items": [i.model_dump() for i in items]}

    @mcp.tool()
    async def generate_conclusions_outline(**kwargs):
        req = _build_request(**kwargs)
        return {"ok": True, "markdown": generate_conclusions_outline_markdown(req)}

    @mcp.tool()
    async def generate_exhibit_reference_map(**kwargs):
        req = _build_request(**kwargs)
        return {"ok": True, "mapping": generate_exhibit_reference_map(req)}

    @mcp.tool()
    async def generate_case_file_bundle(exhibits: list[dict], **kwargs):
        req = _build_request(exhibits=[f"Pièce n° {x.get('number')} - {x.get('title')}" for x in exhibits], **kwargs)
        exhibit_items = [ExhibitItem(**item) for item in exhibits]
        exhibit_md = generate_exhibit_list_markdown(exhibit_items)
        bundle = generate_case_file_bundle_markdown(req, exhibit_md)
        return {"ok": True, "markdown": bundle}

    @mcp.tool()
    async def export_generated_document_markdown(**kwargs):
        generated = await generate_legal_document(**kwargs)
        if not generated.get("ok"):
            return generated
        path = export_text_markdown(generated["markdown"], settings.exports_dir, prefix=kwargs.get("document_type", "document"))
        return {"ok": True, "path": path, "markdown": generated["markdown"]}

    @mcp.tool()
    async def export_generated_document_docx(**kwargs):
        generated = await generate_legal_document(**kwargs)
        if not generated.get("ok"):
            return generated
        path = export_text_docx(generated["markdown"], settings.exports_dir, prefix=kwargs.get("document_type", "document"))
        return {"ok": True, "path": path}

    @mcp.tool()
    async def export_case_file_bundle_markdown(exhibits: list[dict], **kwargs):
        generated = await generate_case_file_bundle(exhibits=exhibits, **kwargs)
        if not generated.get("ok"):
            return generated
        return {"ok": True, "path": export_text_markdown(generated["markdown"], settings.exports_dir, prefix="dossier_complet")}

    @mcp.tool()
    async def export_case_file_bundle_docx(exhibits: list[dict], **kwargs):
        generated = await generate_case_file_bundle(exhibits=exhibits, **kwargs)
        if not generated.get("ok"):
            return generated
        return {"ok": True, "path": export_text_docx(generated["markdown"], settings.exports_dir, prefix="dossier_complet")}

    @mcp.tool()
    async def export_jurisprudence_note_markdown(decision_id: str):
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return {"ok": True, "path": export_jurisprudence_note_markdown_from_payload(payload, settings.exports_dir)}

    @mcp.tool()
    async def export_jurisprudence_note_docx(decision_id: str):
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return {"ok": True, "path": export_jurisprudence_note_docx_from_payload(payload, settings.exports_dir)}

    return mcp
