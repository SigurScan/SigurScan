# SigurScan Scam Family Corpus Schema

Ultima actualizare: 2026-06-02

Scop: corpusul este baza empirica a produsului. Fiecare schimbare in extractor, evidence gate sau decision engine trebuie testata pe corpus.

## Regula centrala

Corpusul nu este o lista de povesti. Este un set de cazuri versionate cu input, dovezi, verdict asteptat si motivul verdictului.

## Schema canonica

```json
{
  "case_id": "ro-uber-real-promo-001",
  "locale": "ro-RO",
  "input_type": "email_html_or_eml",
  "source_channel": "yahoo_mail_share",
  "scam_family": "legitimate_marketing",
  "original_input": {
    "text": "Te asteptam cu drag inapoi...",
    "html": "<a href=\"https://rides.sng.link/...\">Comanda o cursa</a>",
    "headers": {
      "from": "Uber <...>",
      "reply_to": "",
      "subject": "Economiseste 50%"
    },
    "attachments": []
  },
  "extraction": {
    "visible_text": "Te asteptam cu drag inapoi. Comanda o cursa.",
    "visible_urls": [],
    "hidden_urls": ["https://rides.sng.link/..."],
    "forms": [],
    "buttons": [
      {
        "label": "Comanda o cursa",
        "url": "https://rides.sng.link/..."
      }
    ]
  },
  "evidence": {
    "claimed_brand": "Uber",
    "brand_confidence": "high",
    "expected_official_domains": ["uber.com", "uber.link", "ubereats.com"],
    "primary_url": "https://rides.sng.link/...",
    "final_url": "https://www.uber.com",
    "redirect_chain": ["https://rides.sng.link/...", "https://www.uber.com"],
    "is_tracking_redirect": true,
    "is_official_or_official_fallback": true,
    "page_intent": "none",
    "form_action_domain": null,
    "web_risk": {
      "verdict": "No Threats",
      "severity": "low"
    },
    "urlscan": {
      "verdict": "No malicious verdict",
      "severity": "low",
      "screenshot_available": true
    },
    "virus_total": null,
    "dnsc_blacklist": null,
    "local_signals": ["marketing_urgency"],
    "source_conflicts": []
  },
  "expected": {
    "action_class": "LOW_RISK",
    "user_action": "Poti continua cu prudenta",
    "must_not_include_family": ["eMAG fals / Premiu fals", "Mail cu link ascuns"],
    "reason": "Tracking legitim catre domeniu oficial Uber; marketing language singur nu este dovada de scam."
  }
}
```

## Campuri obligatorii

- `case_id`
- `locale`
- `input_type`
- `source_channel`
- `scam_family`
- `original_input`
- `extraction`
- `evidence`
- `expected`

## Categorii minime Romania

- Uber real promo email;
- eMAG real newsletter;
- FAN Courier real;
- FAN Courier fake cu taxa/livrare;
- ANAF fake/SPV;
- banca fake OTP;
- Revolut real;
- Revolut fake;
- OLX fake plata/curier;
- Poșta Romana fake;
- WhatsApp takeover;
- AnyDesk/remote access fraud;
- crypto/investment scam;
- job scam;
- marketplace escrow fake;
- giveaway/voucher fake;
- tracking link legitim;
- email cu HTML shell Yahoo/Gmail/Outlook, fara corpul real.

## Reguli pentru testare

Fiecare caz trebuie sa verifice:

- ce linkuri au fost extrase;
- care este URL-ul principal ales;
- care este final URL;
- daca brandul a fost identificat corect;
- ce verdict asteptat apare;
- ce familii nu au voie sa apara;
- ce motiv user-facing trebuie sa existe;
- ce semnale tehnice raman in detalii.

## Politica de schimbare

Nu se modifica Decision Engine fara:

1. Caz nou in corpus sau caz existent actualizat.
2. Test automat care pica inainte de schimbare.
3. Test automat verde dupa schimbare.
4. Verificare ca false-positive cases raman corecte.
