from __future__ import annotations

import inspect
import time
from typing import Any

from fastmcp import FastMCP

from .analysis import analyze_case_strategy_payload, build_argumentation_strategy_payload
from .backends import backend_status_payload, normalize_pappers_search_response
from .circuit_breaker import (
    can_call_backend,
    load_circuit_breaker,
    record_backend_failure,
    record_backend_success,
    reset_backend_circuit_breaker,
)
from .client import PappersJusticeClient
from .config import Settings
from .exceptions import PappersAPIError, PappersValidationError
from .exporters import (
    export_jurisprudence_note_docx_from_payload,
    export_jurisprudence_note_markdown_from_payload,
    export_text_docx,
    export_text_markdown,
)
from .healthchecks import run_backend_healthchecks_payload
from .legal_documents import (
    generate_case_file_bundle_markdown,
    generate_conclusions_outline_markdown,
    generate_exhibit_list_markdown,
    generate_exhibit_reference_map,
    generate_legal_document_markdown,
)
from .logging_config import configure_logging
from .metrics import load_metrics, record_backend_call, reset_metrics
from .models import (
    DecisionSearchParams,
    ExhibitItem,
    InlineReference,
    LegalArgument,
    LegalDocumentRequest,
    LegalParty,
)
from .normalizers import (
    normalize_decision_response,
    normalize_pdf_response,
    normalize_search_response,
    summarize_normalized_decision,
)
from .openapi_cache import refresh_openapi_cache_entries
from .remote_backends import search_company_backend, search_openlegi_jurisprudence
from .renderers import (
    extract_motivation_snippets_from_payload,
    render_decision_markdown_from_payload,
    render_search_results_markdown_from_payload,
)
from .router import (
    choose_backend_reason_with_priority,
    explain_source_selection_payload,
    federated_merge_companies,
    federated_merge_decisions,
    ordered_backends,
)
from .source_priority import get_source_priority_payload, set_source_priority_payload
from .strategist import (
    build_conclusion_ready_citations_from_payload,
    comparative_table_markdown_from_payloads,
    rank_decisions_payload,
)
from .utils import suggest_inline_references_for_text


async def _maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def create_mcp() -> FastMCP:
    settings = Settings.from_env()
    logger = configure_logging(settings.log_level)
    client = PappersJusticeClient(settings, logger)
    mcp = FastMCP("pappers-justice-axiorhub")

    health_state = (
        run_backend_healthchecks_payload(settings)["checks"]
        if settings.auto_healthcheck_on_start
        else {}
    )

    async def _search(params: DecisionSearchParams) -> dict:
        raw, query_payload = await client.search_decisions(params)
        return normalize_search_response(raw, query_payload, settings.content_preview_length)

    async def _decision(decision_id: str) -> dict:
        raw = await client.get_decision_by_id(decision_id)
        return normalize_decision_response(raw, settings.content_preview_length)

    def _current_priorities() -> dict:
        return get_source_priority_payload(settings)["priorities"]

    def _inline_refs(items: list[dict] | None) -> list[InlineReference]:
        return [InlineReference(**item) for item in (items or [])]

    def _build_request_from_dict(request: dict) -> LegalDocumentRequest:
        request = dict(request)

        return LegalDocumentRequest(
            document_type=request["document_type"],
            jurisdiction_name=request["jurisdiction_name"],
            stylistic_mode=request.get("stylistic_mode", "juridiction_adaptee"),
            title_override=request.get("title_override"),
            intro_label=request.get("intro_label"),
            main_party=LegalParty(**request["main_party"]),
            opposing_parties=[LegalParty(**p) for p in request.get("opposing_parties", [])],
            facts=request["facts"],
            facts_exhibit_numbers=request.get("facts_exhibit_numbers", []),
            facts_exhibit_reference_note=request.get("facts_exhibit_reference_note"),
            facts_inline_references=_inline_refs(request.get("facts_inline_references")),
            procedure_history=request.get("procedure_history"),
            object_text=request.get("object_text"),
            discussion_text=request.get("discussion_text"),
            discussion_exhibit_numbers=request.get("discussion_exhibit_numbers", []),
            discussion_exhibit_reference_note=request.get("discussion_exhibit_reference_note"),
            discussion_inline_references=_inline_refs(request.get("discussion_inline_references")),
            legal_texts=request.get("legal_texts", []),
            jurisprudence_overview=request.get("jurisprudence_overview", []),
            arguments=[LegalArgument(**a) for a in request.get("arguments", [])],
            article_700_text=request.get("article_700_text"),
            costs_text=request.get("costs_text"),
            final_requests=request.get("final_requests", []),
            subsidiary_requests=request.get("subsidiary_requests", []),
            infinitely_subsidiary_requests=request.get("infinitely_subsidiary_requests", []),
            reconventional_requests=request.get("reconventional_requests", []),
            in_any_case_requests=request.get("in_any_case_requests", []),
            exhibits=request.get("exhibits", []),
            additional_notes=request.get("additional_notes"),
        )

    async def _call_pappers_search(
        *,
        q: str | None,
        question: str | None,
        parties: str | None,
        numero_rg: str | None,
        code_nac: str | None,
        sections: list[str] | None,
        juridiction: list[str] | None,
        date_decision_min: str | None,
        date_decision_max: str | None,
        numero: str | None,
        ecli: str | None,
        page: int,
        tri: str,
        per_page: int,
    ) -> dict:
        started = time.time()
        try:
            params = DecisionSearchParams(
                q=q,
                question=question,
                parties=parties,
                numero_rg=numero_rg,
                code_nac=code_nac,
                sections=sections,
                juridiction=juridiction,
                date_decision_min=date_decision_min,
                date_decision_max=date_decision_max,
                numero=numero,
                ecli=ecli,
                page=page,
                tri=tri,
                per_page=per_page,
            )
            result = await _search(params)
            latency = int((time.time() - started) * 1000)
            record_backend_call(
                settings.backend_metrics_file,
                "pappers_justice",
                True,
                latency,
            )
            record_backend_success(settings.circuit_breaker_file, "pappers_justice")
            return result
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            latency = int((time.time() - started) * 1000)
            record_backend_call(
                settings.backend_metrics_file,
                "pappers_justice",
                False,
                latency,
                str(exc),
            )
            record_backend_failure(
                settings.circuit_breaker_file,
                "pappers_justice",
                settings.circuit_breaker_failure_threshold,
                str(exc),
            )
            logger.error(
                "search_decisions failed",
                extra={"extra": {"backend": "pappers_justice", "error": str(exc)}},
            )
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def refresh_openapi_cache() -> dict:
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
    async def run_backend_healthchecks() -> dict:
        nonlocal health_state
        payload = run_backend_healthchecks_payload(settings)
        health_state = payload["checks"]
        return payload

    @mcp.tool()
    async def get_backend_status() -> dict:
        return backend_status_payload(settings, healthchecks=health_state)

    @mcp.tool()
    async def get_source_priority() -> dict:
        return get_source_priority_payload(settings)

    @mcp.tool()
    async def set_source_priority(
        kind: str,
        backends: list[str],
        persist: bool = True,
    ) -> dict:
        return set_source_priority_payload(settings, kind, backends, persist=persist)

    @mcp.tool()
    async def get_backend_metrics() -> dict:
        return {"ok": True, "metrics": load_metrics(settings.backend_metrics_file)}

    @mcp.tool()
    async def reset_backend_metrics() -> dict:
        return {"ok": True, "metrics": reset_metrics(settings.backend_metrics_file)}

    @mcp.tool()
    async def get_circuit_breaker_status() -> dict:
        return {
            "ok": True,
            "circuit_breaker": load_circuit_breaker(settings.circuit_breaker_file),
        }

    @mcp.tool()
    async def reset_circuit_breaker(backend: str | None = None) -> dict:
        return {
            "ok": True,
            "circuit_breaker": reset_backend_circuit_breaker(
                settings.circuit_breaker_file,
                backend,
            ),
        }

    @mcp.tool()
    async def search_decisions(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        code_nac: str | None = None,
        sections: list[str] | None = None,
        juridiction: list[str] | None = None,
        date_decision_min: str | None = None,
        date_decision_max: str | None = None,
        numero: str | None = None,
        ecli: str | None = None,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        return await _call_pappers_search(
            q=q,
            question=question,
            parties=parties,
            numero_rg=numero_rg,
            code_nac=code_nac,
            sections=sections,
            juridiction=juridiction,
            date_decision_min=date_decision_min,
            date_decision_max=date_decision_max,
            numero=numero,
            ecli=ecli,
            page=page,
            tri=tri,
            per_page=per_page,
        )

    @mcp.tool()
    async def search_decisions_by_keyword(
        q: str,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        return await search_decisions(q=q, page=page, tri=tri, per_page=per_page)

    @mcp.tool()
    async def search_decisions_by_question(
        question: str,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        return await search_decisions(
            question=question,
            page=page,
            tri=tri,
            per_page=per_page,
        )

    @mcp.tool()
    async def search_decisions_by_party(
        parties: str,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        return await search_decisions(
            parties=parties,
            page=page,
            tri=tri,
            per_page=per_page,
        )

    @mcp.tool()
    async def search_decisions_by_rg_number(
        numero_rg: str,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        return await search_decisions(
            numero_rg=numero_rg,
            page=page,
            tri=tri,
            per_page=per_page,
        )

    @mcp.tool()
    async def federated_search_jurisprudence(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        code_nac: str | None = None,
        sections: list[str] | None = None,
        juridiction: list[str] | None = None,
        date_decision_min: str | None = None,
        date_decision_max: str | None = None,
        numero: str | None = None,
        ecli: str | None = None,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
        min_results: int = 3,
        include_fallback_results: bool = True,
        force_refresh_schema: bool = False,
        source_priority: list[str] | None = None,
    ) -> dict:
        nonlocal health_state

        if settings.auto_healthcheck_before_search:
            health_state = run_backend_healthchecks_payload(settings)["checks"]

        priorities = _current_priorities()
        priority = source_priority or priorities.get(
            "jurisprudence",
            settings.source_priority_jurisprudence,
        )

        backend_order = ordered_backends(
            priority,
            ["pappers_justice", "openlegi"],
            ["pappers_justice", "openlegi"],
        )

        pappers_payload: dict = {"ok": False, "error": "not_called"}
        pappers_ok = False
        pappers_results: list[dict] = []
        pappers_count = 0

        fallback_results: list[dict] = []
        fallback_meta: dict | None = None
        selected_backend = backend_order[0] if backend_order else "pappers_justice"
        fallback_reason: str | None = None

        for backend in backend_order:
            if backend == "pappers_justice":
                allow_pappers, _ = can_call_backend(
                    settings.circuit_breaker_file,
                    "pappers_justice",
                    settings.circuit_breaker_reset_timeout_seconds,
                )
                if not allow_pappers:
                    fallback_reason = "circuit breaker ouvert pour pappers_justice"
                    continue

                pappers_payload = await search_decisions(
                    q=q,
                    question=question,
                    parties=parties,
                    numero_rg=numero_rg,
                    code_nac=code_nac,
                    sections=sections,
                    juridiction=juridiction,
                    date_decision_min=date_decision_min,
                    date_decision_max=date_decision_max,
                    numero=numero,
                    ecli=ecli,
                    page=page,
                    tri=tri,
                    per_page=per_page,
                )
                pappers_ok = bool(pappers_payload.get("ok"))
                pappers_results = (
                    normalize_pappers_search_response(pappers_payload)
                    if pappers_ok
                    else []
                )
                pappers_count = len(pappers_results)

                if pappers_ok and pappers_count >= min_results:
                    selected_backend = "pappers_justice"
                    fallback_reason = None
                    break

                if not pappers_ok:
                    fallback_reason = "backend primaire indisponible"
                else:
                    fallback_reason = "nombre de résultats insuffisant sur le backend primaire"

            elif backend == "openlegi":
                if not include_fallback_results:
                    continue

                allow_openlegi, _ = can_call_backend(
                    settings.circuit_breaker_file,
                    "openlegi",
                    settings.circuit_breaker_reset_timeout_seconds,
                )
                if not allow_openlegi:
                    fallback_reason = (
                        f"{fallback_reason or 'fallback'} ; circuit breaker ouvert pour openlegi"
                    )
                    continue

                started = time.time()
                try:
                    fallback_payload = await _maybe_await(
                        search_openlegi_jurisprudence(
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
                    )
                    latency = int((time.time() - started) * 1000)

                    if fallback_payload.get("ok"):
                        record_backend_call(
                            settings.backend_metrics_file,
                            "openlegi",
                            True,
                            latency,
                        )
                        record_backend_success(settings.circuit_breaker_file, "openlegi")

                        fallback_results = fallback_payload.get("results", [])
                        fallback_meta = {
                            "request_url": fallback_payload.get("request_url"),
                            "request_params": fallback_payload.get("request_params"),
                            "discovered_operation": fallback_payload.get("discovered_operation"),
                        }
                        for item in fallback_results:
                            item["fallback_reason"] = fallback_reason

                        selected_backend = "openlegi"
                        if fallback_reason is None:
                            fallback_reason = "priorité configurée en faveur d'OpenLegi"
                        break

                    error_message = fallback_payload.get("error", "unknown OpenLegi error")
                    record_backend_call(
                        settings.backend_metrics_file,
                        "openlegi",
                        False,
                        latency,
                        error_message,
                    )
                    record_backend_failure(
                        settings.circuit_breaker_file,
                        "openlegi",
                        settings.circuit_breaker_failure_threshold,
                        error_message,
                    )
                    fallback_reason = f"{fallback_reason or 'fallback'} ; erreur backend OpenLegi: {error_message}"

                except Exception as exc:
                    latency = int((time.time() - started) * 1000)
                    record_backend_call(
                        settings.backend_metrics_file,
                        "openlegi",
                        False,
                        latency,
                        str(exc),
                    )
                    record_backend_failure(
                        settings.circuit_breaker_file,
                        "openlegi",
                        settings.circuit_breaker_failure_threshold,
                        str(exc),
                    )
                    fallback_reason = f"{fallback_reason or 'fallback'} ; erreur backend OpenLegi: {exc}"

        if selected_backend == "openlegi":
            merged = federated_merge_decisions(
                pappers_results,
                fallback_results,
                use_fallback=bool(fallback_results),
            )
        else:
            merged = federated_merge_decisions(
                pappers_results,
                [],
                use_fallback=False,
            )

        merged.sort(key=lambda x: x.get("quality_score", 0), reverse=True)

        if selected_backend != "pappers_justice" and pappers_ok and pappers_count >= min_results:
            selected_backend, fallback_reason = choose_backend_reason_with_priority(
                priority,
                pappers_ok,
                pappers_count,
                min_results,
            )

        return {
            "ok": True,
            "selected_backend": selected_backend,
            "fallback_reason": fallback_reason,
            "results": merged,
            "result_count": len(merged),
            "source_trace": {
                "priority": priority,
                "backend_order": backend_order,
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
    ) -> dict:
        result = await federated_search_jurisprudence(
            q=q,
            question=question,
            parties=parties,
            numero_rg=numero_rg,
            min_results=999999,
            include_fallback_results=True,
        )
        result["forced_fallback"] = True
        return result

    @mcp.tool()
    async def federated_search_company(
        name: str | None = None,
        siren: str | None = None,
        page: int = 1,
        per_page: int = 10,
        force_refresh_schema: bool = False,
        source_priority: list[str] | None = None,
    ) -> dict:
        nonlocal health_state

        if settings.auto_healthcheck_before_search:
            health_state = run_backend_healthchecks_payload(settings)["checks"]

        priorities = _current_priorities()
        priority = source_priority or priorities.get(
            "company",
            settings.source_priority_company,
        )

        selected_backend = priority[0] if priority else "recherche_entreprises"

        allow_company, _ = can_call_backend(
            settings.circuit_breaker_file,
            "recherche_entreprises",
            settings.circuit_breaker_reset_timeout_seconds,
        )
        if not allow_company:
            return {
                "ok": False,
                "error": "Circuit breaker open for recherche_entreprises",
                "selected_backend": selected_backend,
            }

        started = time.time()
        try:
            payload = await _maybe_await(
                search_company_backend(
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
            )
            latency = int((time.time() - started) * 1000)

            if not payload.get("ok"):
                error_message = payload.get("error", "unknown company backend error")
                record_backend_call(
                    settings.backend_metrics_file,
                    "recherche_entreprises",
                    False,
                    latency,
                    error_message,
                )
                record_backend_failure(
                    settings.circuit_breaker_file,
                    "recherche_entreprises",
                    settings.circuit_breaker_failure_threshold,
                    error_message,
                )
                return payload

            record_backend_call(
                settings.backend_metrics_file,
                "recherche_entreprises",
                True,
                latency,
            )
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
            record_backend_call(
                settings.backend_metrics_file,
                "recherche_entreprises",
                False,
                latency,
                str(exc),
            )
            record_backend_failure(
                settings.circuit_breaker_file,
                "recherche_entreprises",
                settings.circuit_breaker_failure_threshold,
                str(exc),
            )
            return {
                "ok": False,
                "error": str(exc),
                "selected_backend": selected_backend,
            }

    @mcp.tool()
    async def explain_source_selection(
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        min_results: int = 3,
        source_priority: list[str] | None = None,
    ) -> dict:
        fed = await federated_search_jurisprudence(
            q=q,
            question=question,
            parties=parties,
            numero_rg=numero_rg,
            min_results=min_results,
            source_priority=source_priority,
        )
        return explain_source_selection_payload(
            fed.get("selected_backend"),
            fed.get("fallback_reason"),
            fed.get("source_trace", {}).get("pappers_result_count", 0),
            fed.get("result_count", 0),
            priority=fed.get("source_trace", {}).get("priority"),
        )

    @mcp.tool()
    async def get_decision_by_id(decision_id: str) -> dict:
        try:
            return await _decision(decision_id)
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def get_decision_pdf_info(decision_id: str) -> dict:
        try:
            data = await client.get_decision_pdf(decision_id)
            return normalize_pdf_response(decision_id, len(data))
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def summarize_decision_for_llm(decision_id: str) -> dict:
        try:
            normalized = await _decision(decision_id)
            return summarize_normalized_decision(normalized)
        except (PappersValidationError, PappersAPIError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def render_search_results_markdown(
        mode: str = "compact",
        q: str | None = None,
        question: str | None = None,
        parties: str | None = None,
        numero_rg: str | None = None,
        code_nac: str | None = None,
        sections: list[str] | None = None,
        juridiction: list[str] | None = None,
        date_decision_min: str | None = None,
        date_decision_max: str | None = None,
        numero: str | None = None,
        ecli: str | None = None,
        page: int = 1,
        tri: str = "pertinence",
        per_page: int = 10,
    ) -> dict:
        payload = await search_decisions(
            q=q,
            question=question,
            parties=parties,
            numero_rg=numero_rg,
            code_nac=code_nac,
            sections=sections,
            juridiction=juridiction,
            date_decision_min=date_decision_min,
            date_decision_max=date_decision_max,
            numero=numero,
            ecli=ecli,
            page=page,
            tri=tri,
            per_page=per_page,
        )
        if not payload.get("ok"):
            return payload

        return {
            "ok": True,
            "mode": mode,
            "markdown": render_search_results_markdown_from_payload(payload, mode=mode),
            "data": payload,
        }

    @mcp.tool()
    async def render_decision_markdown(
        decision_id: str,
        mode: str = "compact",
    ) -> dict:
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload

        return {
            "ok": True,
            "mode": mode,
            "markdown": render_decision_markdown_from_payload(payload, mode=mode),
            "data": payload,
        }

    @mcp.tool()
    async def extract_motivation_snippets(
        decision_id: str,
        query: str | None = None,
        max_snippets: int = 3,
    ) -> dict:
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return extract_motivation_snippets_from_payload(
            payload,
            query=query,
            max_snippets=max_snippets,
        )

    @mcp.tool()
    async def rank_decisions_strategically(decision_ids: list[str]) -> dict:
        payloads = []
        for decision_id in decision_ids:
            payload = await get_decision_by_id(decision_id)
            if payload.get("ok"):
                payloads.append(payload)
        return rank_decisions_payload(payloads)

    @mcp.tool()
    async def build_conclusion_ready_citations(
        decision_id: str,
        max_quotes: int = 3,
    ) -> dict:
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return build_conclusion_ready_citations_from_payload(
            payload,
            max_quotes=max_quotes,
        )

    @mcp.tool()
    async def render_comparative_table_markdown(
        decision_ids: list[str],
        mode: str = "compact",
    ) -> dict:
        payloads = []
        for decision_id in decision_ids:
            payload = await get_decision_by_id(decision_id)
            if payload.get("ok"):
                payloads.append(payload)

        return {
            "ok": True,
            "mode": mode,
            "markdown": comparative_table_markdown_from_payloads(payloads, mode=mode),
            "count": len(payloads),
        }

    @mcp.tool()
    async def analyze_case_strategy(
        facts: str,
        discussion_text: str | None = None,
        arguments: list[dict] | None = None,
        jurisprudence: list[dict] | None = None,
        exhibits: list[dict] | None = None,
    ) -> dict:
        return analyze_case_strategy_payload(
            facts,
            discussion_text,
            arguments,
            jurisprudence,
            exhibits,
        )

    @mcp.tool()
    async def build_argumentation_strategy(
        arguments: list[dict] | None = None,
    ) -> dict:
        return build_argumentation_strategy_payload(arguments)

    @mcp.tool()
    async def suggest_inline_references(
        facts: str | None = None,
        discussion_text: str | None = None,
        arguments: list[dict] | None = None,
        exhibits: list[dict] | None = None,
    ) -> dict:
        exhibits = exhibits or []
        suggestions = {
            "facts_inline_references": suggest_inline_references_for_text(facts or "", exhibits),
            "discussion_inline_references": suggest_inline_references_for_text(
                discussion_text or "",
                exhibits,
            ),
            "argument_inline_references": [],
        }

        for arg in arguments or []:
            suggestions["argument_inline_references"].append(
                {
                    "title": arg.get("title"),
                    "inline_references": suggest_inline_references_for_text(
                        arg.get("facts_application") or "",
                        exhibits,
                    ),
                }
            )

        return {"ok": True, "suggestions": suggestions}

    @mcp.tool()
    async def generate_legal_document(request: dict) -> dict:
        try:
            req = _build_request_from_dict(request)
            markdown = generate_legal_document_markdown(req)
            return {
                "ok": True,
                "document_type": request.get("document_type"),
                "markdown": markdown,
                "request": req.model_dump(),
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool()
    async def generate_conclusions_document(request: dict) -> dict:
        request = dict(request)
        request["document_type"] = "conclusions"
        return await generate_legal_document(request)

    @mcp.tool()
    async def generate_assignation_document(request: dict) -> dict:
        request = dict(request)
        request["document_type"] = "assignation"
        return await generate_legal_document(request)

    @mcp.tool()
    async def generate_requete_document(request: dict) -> dict:
        request = dict(request)
        request["document_type"] = "requete"
        return await generate_legal_document(request)

    @mcp.tool()
    async def generate_exhibit_list(exhibits: list[dict]) -> dict:
        items = [ExhibitItem(**item) for item in exhibits]
        markdown = generate_exhibit_list_markdown(items)
        return {
            "ok": True,
            "markdown": markdown,
            "count": len(items),
            "items": [i.model_dump() for i in items],
        }

    @mcp.tool()
    async def generate_conclusions_outline(request: dict) -> dict:
        req = _build_request_from_dict(request)
        return {"ok": True, "markdown": generate_conclusions_outline_markdown(req)}

    @mcp.tool()
    async def generate_exhibit_reference_map(request: dict) -> dict:
        req = _build_request_from_dict(request)
        return {"ok": True, "mapping": generate_exhibit_reference_map(req)}

    @mcp.tool()
    async def generate_case_file_bundle(exhibits: list[dict], request: dict) -> dict:
        request = dict(request)
        request["exhibits"] = [
            f"Pièce n° {x.get('number')} - {x.get('title')}"
            for x in exhibits
        ]
        req = _build_request_from_dict(request)
        exhibit_items = [ExhibitItem(**item) for item in exhibits]
        exhibit_md = generate_exhibit_list_markdown(exhibit_items)
        bundle = generate_case_file_bundle_markdown(req, exhibit_md)
        return {"ok": True, "markdown": bundle}

    @mcp.tool()
    async def export_generated_document_markdown(request: dict) -> dict:
        generated = await generate_legal_document(request)
        if not generated.get("ok"):
            return generated

        path = export_text_markdown(
            generated["markdown"],
            settings.exports_dir,
            prefix=request.get("document_type", "document"),
        )
        return {"ok": True, "path": path, "markdown": generated["markdown"]}

    @mcp.tool()
    async def export_generated_document_docx(request: dict) -> dict:
        generated = await generate_legal_document(request)
        if not generated.get("ok"):
            return generated

        path = export_text_docx(
            generated["markdown"],
            settings.exports_dir,
            prefix=request.get("document_type", "document"),
        )
        return {"ok": True, "path": path}

    @mcp.tool()
    async def export_case_file_bundle_markdown(
        exhibits: list[dict],
        request: dict,
    ) -> dict:
        generated = await generate_case_file_bundle(exhibits, request)
        if not generated.get("ok"):
            return generated

        return {
            "ok": True,
            "path": export_text_markdown(
                generated["markdown"],
                settings.exports_dir,
                prefix="dossier_complet",
            ),
        }

    @mcp.tool()
    async def export_case_file_bundle_docx(
        exhibits: list[dict],
        request: dict,
    ) -> dict:
        generated = await generate_case_file_bundle(exhibits, request)
        if not generated.get("ok"):
            return generated

        return {
            "ok": True,
            "path": export_text_docx(
                generated["markdown"],
                settings.exports_dir,
                prefix="dossier_complet",
            ),
        }

    @mcp.tool()
    async def export_jurisprudence_note_markdown(decision_id: str) -> dict:
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return {
            "ok": True,
            "path": export_jurisprudence_note_markdown_from_payload(
                payload,
                settings.exports_dir,
            ),
        }

    @mcp.tool()
    async def export_jurisprudence_note_docx(decision_id: str) -> dict:
        payload = await get_decision_by_id(decision_id)
        if not payload.get("ok"):
            return payload
        return {
            "ok": True,
            "path": export_jurisprudence_note_docx_from_payload(
                payload,
                settings.exports_dir,
            ),
        }

    return mcp
