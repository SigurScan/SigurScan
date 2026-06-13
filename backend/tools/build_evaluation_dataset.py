"""
Build the evaluation dataset for precision/recall validation (§12.2).

Targets:
  - 100 legit, 200 scam, 50 gray cases
  - Covers main brands, domains, and phone patterns
  - Used by test_evaluation_metrics.py to assert:
      precision >= 0.98 DANGEROUS
      precision >= 0.995 SAFE
"""

import json, random, hashlib, time

random.seed(42)

LEGIT_TEMPLATES = [
    # (text, brand, channel, identity_status, sensitive, actual_label)
    ("FAN Courier: coletul tau este la locker. PIN: 4821. Detalii pe awb.fan.ro", "FAN Courier", "sms", "delegated", "none", "SAFE"),
    ("Orange: factura pe luna mai este disponibila pe orange.ro", "Orange", "sms", "official", "none", "SAFE"),
    ("ING: tranzactie autorizata 89.00 lei la Kaufland. Sold disponibil in Home'Bank", "ING", "sms", "official", "none", "SAFE"),
    ("eMAG: oferta limitata weekendul acesta, pana la -50%. Vezi pe emag.ro/promo", "eMAG", "email", "official", "none", "SAFE"),
    ("Vodafone: factura ta pe luna mai este disponibila. Vizualizeaza pe contul My Vodafone", "Vodafone Romania", "sms", "delegated", "none", "SAFE"),
    ("Banca Transilvania: ai primit 1500 lei in cont. Detalii in BT Pay", "Banca Transilvania", "sms", "official", "none", "SAFE"),
    ("Altex: cod reducere 10% valabil azi. Detalii pe altex.ro/voucher", "Altex", "email", "official", "none", "SAFE"),
    ("Sameday: coletul AWB 712334 este in livrare azi. Urmareste in aplicatie.", "Sameday", "sms", "official", "none", "SAFE"),
    ("ANAF: depunerea declaratiei unice se face pe anaf.ro/spv", "ANAF", "email", "official", "none", "SAFE"),
    ("Cargus: curierul ajunge azi intre 14-16. Plata ramburs 120 lei la livrare.", "Cargus", "sms", "official", "none", "SAFE"),
    ("BCR: ai primit un extras de cont pe luna mai. Detalii in George", "BCR", "email", "official", "none", "SAFE"),
    ("Orange YOXO: in 24h se va efectua automat plata abonamentului tau. Vezi factura pe yoxo.onelink.me", "Orange/YOXO", "sms", "delegated", "none", "SAFE"),
    ("Posta Romana: ai un colet in oficiul postal. Ridica-l cu buletinul.", "Posta Romana", "sms", "official", "none", "SAFE"),
    ("Netflix: planul tau s-a reinnoit. Gestioneaza abonamentul pe netflix.com/account", "Netflix", "email", "official", "none", "SAFE"),
    ("Ghiseul.ro: ai o noua factura de plata disponibila pe ghiseul.ro", "Ghiseul.ro", "email", "official", "none", "SAFE"),
    ("Electrica: factura pe luna mai este disponibila in contul tau.", "Electrica / PPC", "email", "official", "none", "SAFE"),
    ("DNSC: alerta saptamanala de securitate cibernetica publicata pe dnsc.ro", "DNSC", "email", "official", "none", "SAFE"),
    ("Uber: cursa ta a ajuns la destinatie. Multumim ca ai ales Uber.", "Uber", "app", "official", "none", "SAFE"),
    ("Revolut: ai primit o notificare de la suport. Verifica in aplicatie.", "Revolut", "app", "official", "none", "SAFE"),
    ("OLX: produsul tau a fost vandut. Preda-l la easybox.", "OLX", "app", "official", "none", "SAFE"),
]

SCAM_TEMPLATES = [
    ("FAN Courier: achita taxa de livrare 4.99 RON, introdu cardul pe fancourier-plata.top/pay", "FAN Courier", "sms", "lookalike", "card", "DANGEROUS"),
    ("BNR: ati fost victima unei fraude. Transferati fondurile in contul sigur de la banca-dvs.ro/securizare", "BNR", "phone", "lookalike", "transfer", "DANGEROUS"),
    ("ANAF: Aveti o rambursare de impozit de 1905 lei. Revendicati la anaf-rambursare.ro", "ANAF", "sms", "lookalike", "card", "DANGEROUS"),
    ("OLX: am platit prin OLX. Ca sa primesti banii pe card, introdu numarul si CVV pe olx-livrare.top", "OLX", "whatsapp", "lookalike", "card", "DANGEROUS"),
    ("ING: autentificare neautorizata detectata. Verifica pe ing-verificare.live", "ING", "sms", "lookalike", "password", "DANGEROUS"),
    ("BCR: am detectat o tranzactie suspecta. Blocheaza aici: bcr-george.top/secure", "BCR", "sms", "lookalike", "password", "DANGEROUS"),
    ("Banca Transilvania: PIN-ul tau a fost suspendat. Actualizeaza pe bt-confirma.xyz", "Banca Transilvania", "sms", "lookalike", "pin", "DANGEROUS"),
    ("Sunt de la IPJ Ilfov, sunteti implicat intr-un caz de frauda. Transferati fondurile in contul sigur.", "Politia/MAI", "phone", "unknown", "transfer", "DANGEROUS"),
    ("Sunt de la banca. Am detectat o tranzactie suspecta. Dati-mi codul OTP pentru a o bloca.", "Banca", "phone", "unknown", "otp", "DANGEROUS"),
    ("Netflix: there was an issue with your payment. Confirm on netflix-plata.top", "Netflix", "email", "lookalike", "card", "DANGEROUS"),
    ("Ai castigat 50000 EUR! Achita taxa de 199 lei pe claim-prize.xyz", "-", "sms", "unknown", "card", "DANGEROUS"),
    ("Investeste in actiunile Hidroelectrica de la 250 EUR. Castig garantat: hidro-invest.xyz", "Hidroelectrica", "social", "unrelated", "transfer", "DANGEROUS"),
    ("Instaleaza AnyDesk si da-mi codul de conectare pentru a procesa retragerea profitului.", "Broker", "phone", "unknown", "remote", "DANGEROUS"),
    ("Ti-am instalat malware si te-am filmat. Trimite 1200 USD in Bitcoin in 48h.", "-", "email", "unknown", "crypto", "DANGEROUS"),
    ("Mama, mi-am spart telefonul, am o plata urgenta, poti sa-mi trimiti pe IBAN?", "Ruda", "whatsapp", "unknown", "transfer", "SUSPECT"),
    ("Buna, ne-am schimbat contul bancar. Virati facturile la noul IBAN.", "Furnizor", "email", "unknown", "transfer", "SUSPECT"),
    ("Sameday: taxa de procesare 4.99 RON. Transfera pe sameday-livrari.com/achita (domeniu non-whitelist)", "Sameday", "sms", "unrelated", "transfer", "SUSPECT"),
    ("Lichidare stoc iPhone 15 -70% doar azi. Comanda pe best-deals-ro.shop", "-", "social", "unknown", "card", "SUSPECT"),
    ("Ajuta-l pe X operatie urgenta. Doneaza in contul personal RO49...", "-", "social", "unknown", "transfer", "SUSPECT"),
    ("Buna, mai e disponibil produsul? As dori sa il cumpar prin Livrare OLX.", "OLX", "web", "official", "none", "SAFE"),
]

def _hash_id(text: str, idx: int) -> str:
    return hashlib.sha256(f"{text}{idx}".encode()).hexdigest()[:12]

def _make_case(text, brand, channel, identity_status, sensitive, label, idx):
    return {
        "id": f"EVAL-{_hash_id(text, idx)[:8]}",
        "text": text,
        "brand": brand,
        "channel": channel,
        "expected_label": label,
        "identity_status": identity_status,
        "sensitive": sensitive,
        "actual_is_scam": label == "DANGEROUS",
    }

def _variant(text: str, token: str, replacement: str) -> str:
    return text.replace(token, replacement)

if __name__ == "__main__":
    cases = []
    idx = 0

    # Expand legit templates with minor variations
    for template in LEGIT_TEMPLATES:
        for _ in range(5):
            t = list(template)
            t[0] = _variant(t[0], "factura", random.choice(["factura", "notificare", "confirmare"]))
            t[0] = _variant(t[0], "mai", random.choice(["mai", "iunie", "iulie", "august"]))
            cases.append(_make_case(*t, idx))
            idx += 1

    # Expand scam templates with variations
    for template in SCAM_TEMPLATES:
        for _ in range(10):
            t = list(template)
            if "DANGEROUS" in str(t[5]):
                t[0] = _variant(t[0], "card", random.choice(["card", "carte", "card bancar"]))
                t[0] = _variant(t[0], "lei", random.choice(["lei", "RON", "euro"]))
            cases.append(_make_case(*t, idx))
            idx += 1

    # Add gray area cases (community report only, incomplete)
    gray_cases = [
        ("Un numar necunoscut ma suna de 3 ori si inchide. Nu stiu cine e.", "-", "phone", "unknown", "none", "UNVERIFIED"),
        ("Am primit un apel pierdut de la 021... nu stiu daca e important.", "-", "phone", "unknown", "none", "UNVERIFIED"),
        ("Un prieten mi-a trimis un link pe WhatsApp dar nu l-am deschis inca.", "Prieten", "whatsapp", "unknown", "none", "UNVERIFIED"),
        ("Vreau sa raportez un numar care mi se pare suspect. 07xxxxxxxx", "-", "report", "unknown", "none", "SUSPECT"),
        ("Am primit un email cu o oferta dar ceva nu mi se pare in regula.", "-", "email", "unknown", "none", "UNVERIFIED"),
        ("Site-ul arata bine dar domeniul e inregistrat de o saptamana.", "-", "web", "unknown", "none", "UNVERIFIED"),
        ("O cunostinta mi-a cerut bani pe Messenger. Pare contul ei dar nu sunt sigur.", "Cunostinta", "messenger", "unknown", "transfer", "SUSPECT"),
        ("Am gasit un anunt cu un pret foarte bun dar vanzatorul cere avans.", "-", "web", "unknown", "transfer", "SUSPECT"),
        ("Primul mesaj e normal. Al doilea cere detalii card. E clar ca e tentative.", "-", "sms", "unknown", "card", "DANGEROUS"),
    ]
    for template in gray_cases:
        for _ in range(5):
            cases.append(_make_case(*template, idx))
            idx += 1

    random.shuffle(cases)
    legit_count = sum(1 for c in cases if c["expected_label"] in ("SAFE",))
    scam_count = sum(1 for c in cases if c["expected_label"] in ("DANGEROUS",))
    gray_count = len(cases) - legit_count - scam_count

    output_path = __file__.replace("tools/build_evaluation_dataset.py", "data/evaluation_dataset_v1.jsonl")
    with open(output_path, "w") as f:
        for c in cases:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    print(f"Generated {len(cases)} cases: {legit_count} legit, {scam_count} scam, {gray_count} gray")
    print(f"  -> {output_path}")
