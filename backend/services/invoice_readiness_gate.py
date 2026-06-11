from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from services.invoice_parser import InvoiceFields


class ReadinessState(str, Enum):
    READY = "ready_for_analysis"
    MISSING = "missing_documents"
    BLOCKED = "procedural_blocker"
    LOW_CONFIDENCE = "analysis_allowed_but_low_confidence"


@dataclass
class ReadinessGateItem:
    id: str
    label: str
    detail: str
    next_action: str


@dataclass
class ReadinessGateResult:
    state: ReadinessState
    headline: str
    explanation: str
    next_action: str
    blocks_safe_verdict: bool
    items: List[ReadinessGateItem] = field(default_factory=list)

    def can_be_safe(self) -> bool:
        return self.state == ReadinessState.READY

    def verdict_minimum(self) -> str:
        if self.state == ReadinessState.READY:
            return "any"
        return "suspect"


def evaluate_readiness(fields: InvoiceFields, ocr_confidence: float | None = None) -> ReadinessGateResult:
    confidence = ocr_confidence if ocr_confidence is not None else _estimate_ocr_confidence(fields)
    items: List[ReadinessGateItem] = []

    has_cui = bool(fields.cui)
    has_iban = bool(fields.iban)
    has_total = fields.total is not None
    has_dates = bool(fields.data_emitere) and bool(fields.scadenta)

    if not has_cui and not has_iban:
        items.append(
            ReadinessGateItem(
                id="missing-cui-iban",
                label="CUI și IBAN",
                detail="Nu am putut citi nici CUI-ul, nici IBAN-ul facturii.",
                next_action="Verifică manual emitentul și datele de plată de pe factură.",
            )
        )
        return ReadinessGateResult(
            state=ReadinessState.MISSING,
            headline="Nu am suficiente date pentru un verdict",
            explanation="Nu am putut extrage CUI-ul și IBAN-ul din document. Fără aceste date nu pot verifica emitentul sau destinația plății.",
            next_action="Verifică manual emitentul facturii pe site-ul ANAF sau contactează compania pe canalele oficiale.",
            blocks_safe_verdict=True,
            items=items,
        )

    if not has_cui:
        items.append(
            ReadinessGateItem(
                id="missing-cui",
                label="CUI",
                detail="Nu am putut citi CUI-ul facturii.",
                next_action="Verifică numele și datele emitentului manual.",
            )
        )
    if not has_iban:
        items.append(
            ReadinessGateItem(
                id="missing-iban",
                label="IBAN",
                detail="Nu am putut citi IBAN-ul facturii.",
                next_action="Verifică IBAN-ul înainte de plată.",
            )
        )

    if confidence < 0.6:
        items.append(
            ReadinessGateItem(
                id="low-ocr-confidence",
                label="Document neclar",
                detail="Documentul s-a citit cu încredere scăzută. Datele extrase s-ar putea să fie incorecte.",
                next_action="Reîncarcă o poză mai clară sau verifică manual datele extrase.",
            )
        )
        return ReadinessGateResult(
            state=ReadinessState.LOW_CONFIDENCE,
            headline="Documentul s-a citit parțial",
            explanation="Nu am putut citi documentul suficient de clar. Datele extrase ar putea fi incomplete sau incorecte. Te rog verifică-le manual.",
            next_action="Corectează datele în ecranul de confirmare și reîncearcă.",
            blocks_safe_verdict=True,
            items=items,
        )

    if not has_total or not has_dates:
        items.append(
            ReadinessGateItem(
                id="missing-fields",
                label="Câmpuri factură",
                detail="Nu am putut extrage toate câmpurile obligatorii (total, date).",
                next_action="Verifică factura manual.",
            )
        )
        return ReadinessGateResult(
            state=ReadinessState.LOW_CONFIDENCE,
            headline="Date insuficiente pentru verificare completă",
            explanation="Am citit emitentul, dar lipsesc câmpuri importante. Verdictul rămâne cu precauție.",
            next_action="Completează datele lipsă și scanează din nou.",
            blocks_safe_verdict=True,
            items=items,
        )

    return ReadinessGateResult(
        state=ReadinessState.READY,
        headline="Documentul poate fi verificat",
        explanation="Am extras datele principale din factură și putem începe verificările.",
        next_action="Se efectuează verificările automate.",
        blocks_safe_verdict=False,
        items=items,
    )


def _estimate_ocr_confidence(fields: InvoiceFields) -> float:
    total_fields = 7
    filled = sum(
        1 for f in [fields.cui, fields.iban, fields.emitent, fields.nr_factura,
                     fields.data_emitere, fields.scadenta]
        if f
    )
    if fields.total is not None:
        filled += 1
    if total_fields == 0:
        return 0.0
    return filled / total_fields
