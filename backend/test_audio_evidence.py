"""PR-9 — Audio async / Vishing: contract verdict on-device (reuse verdict_gate).

§13/§14.5: audio = semnal de analist, niciodată pilon de verdict. Zero endpoint
audio pe server, zero audio brut. `build_audio_case_verdict` e referința portată
on-device. STT solo → max SUSPECT; combo „cont sigur"+OTP+bancă → DANGEROUS.
"""
import json

from services.audio_evidence import build_audio_case_verdict


class TestPrivacyContract:
    def test_no_raw_audio_and_on_device(self):
        v = build_audio_case_verdict(transcript_redacted="[redactat]")
        assert v["raw_audio_stored"] is False
        assert v["processing"] == "on_device_only"
        assert v["input_type"] == "audio"

    def test_transcript_is_flag_not_text(self):
        v = build_audio_case_verdict(transcript_redacted="suna banca acum cont sigur")
        blob = json.dumps(v)
        assert "cont sigur" not in blob          # textul nu se propagă
        assert v["transcript_redacted"] is True  # doar flag


class TestVerdictRules:
    def test_safe_account_otp_bank_combo_is_dangerous(self):
        # Arc „cont sigur" + OTP + identitate bancă pe canal neoficial.
        v = build_audio_case_verdict(
            claimed_identity="banca", identity_provenance="mismatch",
            sensitive_asks=["otp"], arc_family="CONV_BANK_SAFE_ACCOUNT",
        )
        assert v["verdict"] == "DANGEROUS"

    def test_transfer_with_bank_identity_is_dangerous(self):
        v = build_audio_case_verdict(
            claimed_identity="politie", identity_provenance="mismatch",
            sensitive_asks=["transfer"], arc_family="CONV_BANK_SAFE_ACCOUNT",
        )
        assert v["verdict"] == "DANGEROUS"

    def test_stt_only_campaign_match_is_max_suspect(self):
        # Doar clasificarea ASR (campanie) — fără cerere sensibilă, fără identitate.
        v = build_audio_case_verdict(
            arc_family="CONV_BANK_SAFE_ACCOUNT",
            campaign_match="cf_bank_safe", campaign_confidence=0.91,
        )
        assert v["verdict"] == "SUSPECT"
        assert v["stt_only"] is True

    def test_stt_only_never_dangerous(self):
        v = build_audio_case_verdict(
            arc_family="CONV_BANK_SAFE_ACCOUNT",
            campaign_match="cf_x", campaign_confidence=0.99,
        )
        assert v["verdict"] != "DANGEROUS"

    def test_legit_unknown_caller_no_sensitive_not_dangerous(self):
        v = build_audio_case_verdict(transcript_redacted="[redactat]")
        assert v["verdict"] in {"UNVERIFIED", "SUSPECT"}
        assert v["verdict"] != "DANGEROUS"

    def test_determinism(self):
        kwargs = dict(claimed_identity="banca", identity_provenance="mismatch",
                      sensitive_asks=["otp"], arc_family="CONV_BANK_SAFE_ACCOUNT")
        assert build_audio_case_verdict(**kwargs) == build_audio_case_verdict(**kwargs)


class TestNoServerAudioEndpoint:
    def test_no_audio_route_registered(self):
        # Linia roșie §14.5: niciun endpoint care primește audio.
        import main as app_main
        paths = {r.path for r in app_main.app.routes if hasattr(r, "path")}
        assert not any("audio" in p.lower() for p in paths)
