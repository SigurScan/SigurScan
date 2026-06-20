"""Result dataclasses for the invoice/offer orchestrator.

Extracted from invoice_orchestrator.py to separate the data model from the scan
logic and its module-level caches. `from __future__ import annotations` keeps all
field annotations lazy, so the concrete types are only needed for type-checking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from services.invoice_parser import InvoiceFields
    from services.iban_validator import IbanResult
    from services.invoice_coherence import CoherenceResult
    from services.invoice_readiness_gate import ReadinessGateResult
    from services.brand_registry import BrandMatchResult
    from services.offer_parser import OfferFields
    from services.offer_entity_verifier import OfferEntityResult


@dataclass
class InvoiceScanResult:
    raw_text: str
    fields: InvoiceFields
    readiness: ReadinessGateResult
    coherence: CoherenceResult
    iban_valid: Optional[IbanResult] = None
    brand: Optional[str] = None
    brand_match: Optional[BrandMatchResult] = None
    anaf_cui_check: Optional[dict] = None
    payment_destination: Optional[dict] = None
    beneficiary_name_check: Optional[dict] = None
    official_document_check: Optional[dict] = None
    email_domain_intel: Optional[dict] = None
    error: Optional[str] = None
    warnings: list = field(default_factory=list)
    fraud_flags: list[str] = field(default_factory=list)
    from_cache: bool = False


@dataclass
class OfferScanResult:
    raw_text: str
    fields: "OfferFields"
    readiness: ReadinessGateResult
    coherence: CoherenceResult
    iban_valid: Optional[IbanResult]
    entity: "OfferEntityResult"
    family_code: str
    family_name: str
    family_confidence: float
    signals: List[str]
    bundle: dict
    gate: dict
    error: Optional[str] = None
    warnings: list = field(default_factory=list)
    # Dovezi din registre publice (PR4): context structurat, nu verdict.
    registry: list = field(default_factory=list)
