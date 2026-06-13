from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class EvaluationTemplate:
    """Deterministic gate-evaluation input.

    These cases are intentionally evidence-first. Expected labels never feed
    semantic_review directly, so the test can catch real gate regressions.
    """

    id: str
    text: str
    expected_label: str
    provider_verdict: str = "clean"
    identity_status: str = "unknown"
    sensitive: str = "none"
    channel: str = "official"
    semantic_risk: str = "unknown"
    semantic_status: str = "done"
    provenance: tuple[str, ...] = field(default_factory=tuple)
    tld_suspicious: bool = False
    domain_age_days: int | None = None
    ssl_invalid: bool = False
    violated_never_asks: tuple[str, ...] = field(default_factory=tuple)
    violated_never_does: tuple[str, ...] = field(default_factory=tuple)
    campaign_confidence: float = 0.0
    community_reports: int = 0
    resolution_status: str = "resolved"


SAFE_TEMPLATES: tuple[EvaluationTemplate, ...] = (
    EvaluationTemplate("safe-fan-awb", "FAN Courier: coletul tau este la locker. Detalii pe awb.fan.ro", "SAFE", identity_status="delegated"),
    EvaluationTemplate("safe-orange-factura", "Orange: factura lunara este disponibila in contul tau Orange.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-yoxo-deeplink", "YOXO: plata abonamentului se va face automat. Vezi factura in aplicatie.", "SAFE", identity_status="delegated"),
    EvaluationTemplate("safe-ing-app", "ING: ai o notificare noua in Home'Bank.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-bt-app", "BT: ai primit o notificare in BT Pay.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-bcr-george", "BCR: extrasul tau este disponibil in George.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-emag-order", "eMAG: comanda ta a fost expediata. Urmareste in cont.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-sameday-delivery", "Sameday: coletul tau este in livrare azi.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-posta-info", "Posta Romana: ai un colet disponibil pentru ridicare.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-anaf-spv", "ANAF: document nou disponibil in SPV.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-ghiseul", "Ghiseul.ro: plata ta a fost confirmata.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-dnsc-alert", "DNSC: alerta informativa publicata pe dnsc.ro.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-uber-receipt", "Uber: cursa ta a fost finalizata.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-revolut-app", "Revolut: verifica detaliile in aplicatie.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-vodafone", "Vodafone: factura este disponibila in MyVodafone.", "SAFE", identity_status="delegated"),
    EvaluationTemplate("safe-altex", "Altex: comanda ta este pregatita pentru livrare.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-cargus", "Cargus: curierul ajunge azi intre 14-16.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-netflix", "Netflix: abonamentul tau a fost reinnoit.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-olx-app", "OLX: mesaj nou in aplicatie pentru anuntul tau.", "SAFE", identity_status="official"),
    EvaluationTemplate("safe-provenance-domain", "Brand confirmat prin domeniu oficial.", "SAFE", provenance=("official_domain_match",)),
)


DANGEROUS_TEMPLATES: tuple[EvaluationTemplate, ...] = (
    EvaluationTemplate("danger-provider-malicious", "URL raportat ca phishing de provider.", "DANGEROUS", provider_verdict="malicious"),
    EvaluationTemplate("danger-provider-phishing", "Pagina confirmata ca phishing.", "DANGEROUS", provider_verdict="phishing"),
    EvaluationTemplate("danger-provider-malware", "Fisier malware atasat.", "DANGEROUS", provider_verdict="malware"),
    EvaluationTemplate("danger-provider-blacklisted", "Domeniu blacklistat.", "DANGEROUS", provider_verdict="blacklisted"),
    EvaluationTemplate("danger-fan-card-lookalike", "FAN Courier cere card pentru taxa livrare.", "DANGEROUS", identity_status="lookalike", sensitive="card", channel="sms"),
    EvaluationTemplate("danger-olx-card", "OLX cere card ca sa primesti banii.", "DANGEROUS", identity_status="lookalike", sensitive="card", channel="whatsapp"),
    EvaluationTemplate("danger-bank-otp-phone", "Banca cere cod OTP la telefon.", "DANGEROUS", sensitive="otp", channel="phone"),
    EvaluationTemplate("danger-password-reply", "Raspunde cu parola pentru verificare.", "DANGEROUS", sensitive="password", channel="reply"),
    EvaluationTemplate("danger-pin-sms", "Trimite PIN-ul prin SMS.", "DANGEROUS", sensitive="pin", channel="sms"),
    EvaluationTemplate("danger-remote-phone", "Instaleaza AnyDesk si da codul operatorului.", "DANGEROUS", sensitive="remote", channel="phone"),
    EvaluationTemplate("danger-crypto-whatsapp", "Transfera crypto catre broker pe WhatsApp.", "DANGEROUS", sensitive="crypto", channel="whatsapp"),
    EvaluationTemplate("danger-transfer-phone-high", "BNR cere transfer in cont sigur.", "DANGEROUS", sensitive="transfer", channel="phone", semantic_risk="high"),
    EvaluationTemplate("danger-spoof-value-tld", "Brand imitat cere plata pe domeniu suspect.", "DANGEROUS", identity_status="unrelated", sensitive="transfer", tld_suspicious=True),
    EvaluationTemplate("danger-young-ssl-spoof", "Domeniu tanar cu SSL invalid imita banca.", "DANGEROUS", identity_status="lookalike", domain_age_days=3, ssl_invalid=True),
    EvaluationTemplate("danger-never-does", "Curierul cere cod WhatsApp, desi brandul nu face asta.", "DANGEROUS", violated_never_does=("asks_whatsapp_code",)),
    EvaluationTemplate("danger-never-asks-sms", "Posta cere PIN card prin SMS.", "DANGEROUS", sensitive="pin", channel="sms", violated_never_asks=("card_pin",)),
    EvaluationTemplate("danger-semantic-card", "Oferta cunoscuta ca scam cere card.", "DANGEROUS", sensitive="card", channel="official", semantic_risk="high"),
    EvaluationTemplate("danger-id-document-whatsapp", "Trimite poza buletinului pe WhatsApp.", "DANGEROUS", sensitive="id_document", channel="whatsapp"),
    EvaluationTemplate("danger-password-sms", "Actualizeaza parola prin SMS.", "DANGEROUS", sensitive="password", channel="sms"),
    EvaluationTemplate("danger-pin-reply", "Raspunde cu PIN-ul pentru blocare tranzactie.", "DANGEROUS", sensitive="pin", channel="reply"),
    EvaluationTemplate("danger-card-unofficial-site", "Introdu datele cardului pe site neoficial.", "DANGEROUS", sensitive="card", channel="unofficial_site"),
    EvaluationTemplate("danger-otp-whatsapp", "Trimite codul OTP pe WhatsApp.", "DANGEROUS", sensitive="otp", channel="whatsapp"),
    EvaluationTemplate("danger-crypto-phone", "Brokerul cere crypto prin apel telefonic.", "DANGEROUS", sensitive="crypto", channel="phone"),
    EvaluationTemplate("danger-unrelated-card", "Institutie imitata cere card pe domeniu nelegat.", "DANGEROUS", identity_status="unrelated", sensitive="card"),
    EvaluationTemplate("danger-semantic-transfer-spoof", "Scenariu de cont sigur cu brand imitat.", "DANGEROUS", identity_status="lookalike", sensitive="transfer", semantic_risk="high"),
)


GRAY_TEMPLATES: tuple[EvaluationTemplate, ...] = (
    EvaluationTemplate("gray-provider-error", "Providerii nu au raspuns.", "SUSPECT", provider_verdict="error"),
    EvaluationTemplate("gray-campaign-only", "Mesaj similar unei campanii raportate.", "SUSPECT", campaign_confidence=0.9),
    EvaluationTemplate("gray-community-only", "Un utilizator a raportat numarul.", "SUSPECT", community_reports=1),
    EvaluationTemplate("gray-value-no-provenance", "Cineva cere un avans fara verificare.", "SUSPECT", sensitive="transfer"),
    EvaluationTemplate("gray-transfer-social", "Cunostinta cere bani pe chat.", "SUSPECT", sensitive="transfer", channel="messenger"),
    EvaluationTemplate("gray-unknown-clean", "Domeniu necunoscut, providerii clean.", "UNVERIFIED"),
    EvaluationTemplate("gray-established-unknown", "Domeniu vechi dar neconfirmat oficial.", "UNVERIFIED", domain_age_days=1200),
    EvaluationTemplate("gray-provider-pending", "Scanare inca in curs.", "UNVERIFIED", provider_verdict="pending"),
    EvaluationTemplate("gray-semantic-pending", "Analiza semantica inca in curs.", "UNVERIFIED", semantic_status="pending"),
    EvaluationTemplate("gray-resolution-failed", "Nu s-a putut rezolva destinatia.", "UNVERIFIED", resolution_status="failed"),
)


def _expand(templates: Iterable[EvaluationTemplate], repeats: int) -> list[dict]:
    cases: list[dict] = []
    for template in templates:
        for idx in range(repeats):
            data = asdict(template)
            data["id"] = f"{template.id}-{idx + 1:02d}"
            data["text"] = f"{template.text} Ref {idx + 1:02d}"
            data["provenance"] = list(template.provenance)
            data["violated_never_asks"] = list(template.violated_never_asks)
            data["violated_never_does"] = list(template.violated_never_does)
            cases.append(data)
    return cases


def build_cases() -> list[dict]:
    cases = []
    cases.extend(_expand(SAFE_TEMPLATES, 5))
    cases.extend(_expand(DANGEROUS_TEMPLATES, 8))
    cases.extend(_expand(GRAY_TEMPLATES, 5))
    return sorted(cases, key=lambda item: item["id"])


def write_jsonl(path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for case in build_cases():
            handle.write(json.dumps(case, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    output_path = Path(__file__).resolve().parents[1] / "data" / "evaluation_dataset_v1.jsonl"
    write_jsonl(output_path)
    cases = build_cases()
    counts = {label: sum(1 for case in cases if case["expected_label"] == label) for label in ("SAFE", "DANGEROUS", "SUSPECT", "UNVERIFIED")}
    print(f"Generated {len(cases)} cases at {output_path}")
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
