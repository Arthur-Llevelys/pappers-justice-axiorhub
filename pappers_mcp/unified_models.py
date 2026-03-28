from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class UnifiedDecision:
    source_backend: str
    source_label: str
    id: str | None = None
    title: str | None = None
    date: str | None = None
    jurisdiction: str | None = None
    chamber: str | None = None
    rg_number: str | None = None
    solution: str | None = None
    summary: str | None = None
    motivation: str | None = None
    dispositif: str | None = None
    legal_basis: list[str] | None = None
    parties: str | None = None
    raw: dict[str, Any] | None = None
    quality_score: int = 0
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class UnifiedCompany:
    source_backend: str
    source_label: str
    name: str | None = None
    siren: str | None = None
    siret: str | None = None
    address: str | None = None
    status: str | None = None
    raw: dict[str, Any] | None = None
    quality_score: int = 0
    fallback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
