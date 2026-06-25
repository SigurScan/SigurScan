"""Guard for the bank credential-update phishing family.

SYNTHETIC TEST VECTORS ONLY (constructed stress vectors, not real reported cases)
-> kept OUT of the provenance corpus on purpose.

The critical property of this class is that the differentiator is DESTINATION /
provenance, NOT text: real banks DO send "for security, please update your data"
emails. So:
- A bank credential-update message whose link is a placeholder / lookalike (not the
  bank's official domain) must escalate to DANGEROUS.
- The SAME wording with a link to the bank's OFFICIAL domain must NOT escalate
  (official_destination -> channel becomes official -> the channel-gated escalation
  rules are suppressed).
"""

import os

import eval.large_offline_fixture_runner as runner


def _verdict(text, channel="email"):
    for k, v in {
        "PRIVACY_SAFE_MODE": "false", "ENABLE_CLOUD_AI_EXPLANATION": "false",
        "ENABLE_MISTRAL_SHADOW_ADJUDICATION": "false", "ENABLE_DNS_REPUTATION": "false",
        "INVOICE_CACHE_HMAC_KEY": "ci-test-hmac-key",
    }.items():
        os.environ.setdefault(k, v)
    return runner._run_case({"id": "x", "text": text, "expected": "DANGEROUS",
                             "source": "synthetic", "meta": {"input_type": channel}}).get("actual")


def test_bank_credential_phish_placeholder_link_escalates():
    text = ("BCR: din motive de securitate este necesara actualizarea/confirmarea "
            "datelor contului de internet banking. Accesati linkul pentru a confirma "
            "datele, altfel contul va fi restrictionat: <LINK>")
    assert _verdict(text) == "DANGEROUS"


def test_bank_credential_phish_lookalike_domain_escalates():
    text = ("BCR: din motive de securitate, actualizati datele contului de internet "
            "banking, altfel contul va fi blocat. https://bcr-secure-login.com/auth")
    assert _verdict(text) == "DANGEROUS"


def test_bank_credential_update_to_official_domain_does_not_escalate():
    # FP boundary: identical wording, but the link is the bank's OFFICIAL domain.
    text = ("BCR: din motive de securitate va recomandam sa va actualizati datele de "
            "contact in Internet Banking. Accesati: "
            "https://www.bcr.ro/ro/persoane-fizice/internet-banking")
    assert _verdict(text) != "DANGEROUS"
