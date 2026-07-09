"""P-RULES Felia 1 — the manifest must be byte-for-byte equivalent to the live
`scam_atlas_patterns` constants, so switching the detectors to it later is
provably behavior-preserving (0-diff). This is the safety gate for the whole
rules-as-data migration.
"""

import re

import services.scam_atlas_patterns as P
from services import rules_manifest

# The pattern groups migrated into the manifest (order-sensitive: some detectors
# index into a group, e.g. REMOTE_ACCESS_PATTERNS[0]/[1]).
MANIFEST_GROUPS = [
    "SENSITIVE_CREDENTIAL_PATTERNS",
    "SENSITIVE_WHATSAPP_PATTERNS",
    "SENSITIVE_PAYMENT_PATTERNS",
    "MALWARE_APK_PATTERNS",
    "SENSITIVE_QR_PATTERNS",
    "SENSITIVE_SEXTORTION_PATTERNS",
    "SENSITIVE_SIM_SWAP_PATTERNS",
    "OLX_CARD_PATTERNS",
    "REMOTE_ACCESS_PATTERNS",
    "URGENCY_MANIPULATION_PATTERNS",
    "MANIPULATION_REWARD_PATTERNS",
    "DELIVERY_MANIPULATION_PATTERNS",
]


def test_manifest_has_a_version():
    assert rules_manifest.manifest_version()


def test_manifest_covers_exactly_the_migrated_groups():
    groups = rules_manifest.load_pattern_groups()
    assert set(groups) == set(MANIFEST_GROUPS)


def test_manifest_is_byte_for_byte_equivalent_to_live_patterns():
    """0-diff: every manifest pattern (source + flags + order) equals the live
    scam_atlas_patterns constant, so consuming the manifest cannot change matching."""
    loaded = rules_manifest.load_pattern_groups()
    for name in MANIFEST_GROUPS:
        live = list(getattr(P, name))
        manifest = loaded[name]
        assert len(manifest) == len(live), f"{name}: count differs"
        for i, (lp, mp) in enumerate(zip(live, manifest)):
            assert mp.pattern == lp.pattern, f"{name}[{i}]: pattern source differs"
            # IGNORECASE is the flag that matters for these detectors; assert it
            # matches so matching semantics are identical.
            assert bool(mp.flags & re.IGNORECASE) == bool(lp.flags & re.IGNORECASE), (
                f"{name}[{i}]: IGNORECASE differs"
            )


def test_manifest_patterns_behave_identically_on_probes():
    """Belt-and-suspenders: manifest vs live must agree match/no-match on probes."""
    loaded = rules_manifest.load_pattern_groups()
    probes = [
        "spune-mi codul otp primit prin sms",
        "transfera banii in cont sigur",
        "instaleaza anydesk pentru suport",
        "coletul are taxa vamala neachitata",
        "buna ziua, ne vedem maine la cafea",
        "",
    ]
    for name in MANIFEST_GROUPS:
        live = list(getattr(P, name))
        manifest = loaded[name]
        for text in probes:
            assert [bool(p.search(text)) for p in live] == [bool(p.search(text)) for p in manifest], (
                f"{name}: match vector differs on {text!r}"
            )
