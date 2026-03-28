from typing import Literal
from pydantic import BaseModel, Field, field_validator

Section = Literal["expose_du_litige", "visa", "moyens", "motifs", "dispositif", "moyens_annexes"]
Tri = Literal["pertinence", "date", "ancien"]
DocumentType = Literal["conclusions", "assignation", "requete"]
StylisticMode = Literal["standard", "contentieux_formel", "juridiction_adaptee"]


class DecisionSearchParams(BaseModel):
    q: str | None = None
    question: str | None = None
    parties: str | None = None
    numero_rg: str | None = None
    code_nac: str | None = None
    sections: list[Section] | None = None
    juridiction: list[str] | None = None
    date_decision_min: str | None = None
    date_decision_max: str | None = None
    numero: str | None = None
    ecli: str | None = None
    page: int = Field(default=1, ge=1)
    tri: Tri = "pertinence"
    per_page: int = Field(default=10, ge=1, le=100)

    @field_validator("q", "question", "parties", "numero_rg", "code_nac", "numero", "ecli")
    @classmethod
    def blank_to_none(cls, value):
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("numero_rg")
    @classmethod
    def normalize_rg(cls, value):
        if value is None:
            return None
        return value.replace("-", "/").strip()

    def ensure_meaningful(self):
        if not any([self.q, self.question, self.parties, self.numero_rg, self.code_nac, self.numero, self.ecli, self.juridiction, self.date_decision_min, self.date_decision_max]):
            raise ValueError("At least one meaningful search criterion must be provided")
        return self


class InlineReference(BaseModel):
    target_text: str
    exhibit_numbers: list[int] = Field(default_factory=list)
    note: str | None = None


class LegalParty(BaseModel):
    party_type: Literal["personne_physique", "societe"]
    role_label: str
    first_name: str | None = None
    last_name: str | None = None
    birth_date: str | None = None
    birth_place: str | None = None
    profession: str | None = None
    address: str | None = None
    company_name: str | None = None
    company_form: str | None = None
    company_address: str | None = None
    siren: str | None = None
    representative_title: str | None = None
    representative_name: str | None = None
    lawyer_name: str | None = None
    lawyer_bar: str | None = None


class LegalArgument(BaseModel):
    title: str
    legal_basis: list[str] = Field(default_factory=list)
    jurisprudence: list[str] = Field(default_factory=list)
    facts_application: str | None = None
    adverse_arguments: str | None = None
    requested_relief: list[str] = Field(default_factory=list)
    exhibit_numbers: list[int] = Field(default_factory=list)
    exhibit_reference_note: str | None = None
    inline_references: list[InlineReference] = Field(default_factory=list)


class ExhibitItem(BaseModel):
    number: int
    title: str
    description: str | None = None
    observation: str | None = None


class LegalDocumentRequest(BaseModel):
    document_type: DocumentType
    jurisdiction_name: str
    stylistic_mode: StylisticMode = "juridiction_adaptee"
    title_override: str | None = None
    main_party: LegalParty
    opposing_parties: list[LegalParty] = Field(default_factory=list)
    intro_label: str | None = None
    facts: str
    facts_exhibit_numbers: list[int] = Field(default_factory=list)
    facts_exhibit_reference_note: str | None = None
    facts_inline_references: list[InlineReference] = Field(default_factory=list)
    procedure_history: str | None = None
    object_text: str | None = None
    discussion_text: str | None = None
    discussion_exhibit_numbers: list[int] = Field(default_factory=list)
    discussion_exhibit_reference_note: str | None = None
    discussion_inline_references: list[InlineReference] = Field(default_factory=list)
    legal_texts: list[str] = Field(default_factory=list)
    jurisprudence_overview: list[str] = Field(default_factory=list)
    arguments: list[LegalArgument] = Field(default_factory=list)
    article_700_text: str | None = None
    costs_text: str | None = None
    final_requests: list[str] = Field(default_factory=list)
    subsidiary_requests: list[str] = Field(default_factory=list)
    infinitely_subsidiary_requests: list[str] = Field(default_factory=list)
    reconventional_requests: list[str] = Field(default_factory=list)
    in_any_case_requests: list[str] = Field(default_factory=list)
    exhibits: list[str] = Field(default_factory=list)
    additional_notes: str | None = None
