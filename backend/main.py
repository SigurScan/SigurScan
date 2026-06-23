"""Backward-compatibility module for legacy ``main`` imports."""

from __future__ import annotations

import asyncio  # noqa: F401 - re-export for legacy compatibility

from app import app, create_app  # noqa: F401
from app_stores import brand_truth_registry, urechea_ingester  # noqa: F401
from config import *  # noqa: F401,F403
from config import (  # noqa: F401
    _ORCHESTRATED_STAGE_RANK,
    _VERDICT_SEVERITY_RANK,
)
from core.click_intelligence import _collect_click_targets_from_html  # noqa: F401
from starlette.concurrency import run_in_threadpool  # noqa: F401
from core.email_auth import _is_domain_aligned  # noqa: F401
from core.scan_context import (  # noqa: F401
    EVAL_DATASET_DEFAULT_PATH,
    _attach_initial_url_privacy,
    _extract_email_auth_context,
    _safe_mode_url_entry,
    _safe_scan_url_list,
    _resolve_eval_dataset_path,
)
from core.text_utils import _normalise_obfuscated_text  # noqa: F401
from core.url_intelligence import (  # noqa: F401
    _canonicalize_url,
    _dedupe_preserve_order,
    _extract_image_qr_payloads,
    _extract_pdf_annotation_links,
    _extract_pdf_embedded_text,
    _extract_pdf_qr_payloads,
    extract_urls,
)
from runtime_state import _URLSCAN_PREVIEW_CACHE, _FAST_PREVIEW_CACHE, engine  # noqa: F401
from services import supabase_store  # noqa: F401
from services.brand_registry import BRAND_REGISTRY  # noqa: F401
from services.gemini_explainer import generate_ai_explanation, generate_fallback_explanation  # noqa: F401
from services.google_vision_ocr import has_vision_key  # noqa: F401
from services.mistral_shadow_adjudicator import maybe_run_shadow_adjudication  # noqa: F401
from services.offer_claim_verifier import verify_offer_claim  # noqa: F401
from services.telemetry import load_scan_records, load_feedback_records, log_scan_event  # noqa: F401
from services.url_reputation import get_reputation_cache_stats, get_reputation_for_urls  # noqa: F401
from services.orchestrated_scan import orchestrated_engine, OrchestratedScanRequest  # noqa: F401
from routers.orchestrated import (  # noqa: F401
    start_orchestrated_scan as start_orchestrated_scan,
    get_orchestrated_scan as get_orchestrated_scan,
)
from services.provider_gate import (  # noqa: F401
    _apply_provider_gate_verdict,
    _maybe_add_dns_reputation,
    _project_provider_gate_verdict,
    _claim_verifier_required,
)
from services.reputation_enrich import (  # noqa: F401
    _gather_external_intel,
    _gather_external_intel_safe,
    _external_intel_summary_from_threat_intel,
    _analyze_with_reputation,
    _attach_reputation_lookup_urls,
    _attach_reputation_lookup_hashes,
    _has_bad_provider_verdict,
)
from services.scan_analysis import (  # noqa: F401
    _apply_best_preview_cache_hit,
    _apply_fast_preview_cache_hit,
    _attach_offer_claim_verification,
    _brand_token_lookalike_in_resolved_urls,
    _build_ai_explanation,
    _build_ai_explanation_async,
    _build_decision_evidence_bundle,
    _build_orchestration_telemetry_payload,
    _build_scan_response,
    _build_shadow_adjudication_payload,
    _calibrate_semantic_review_with_tier1,
    _call_mistral_semantic_review,
    _collect_signal_ids,
    _emit_scan_event,
    _enrich_local_semantic_review,
    _enrich_offer_claim_verification_async,
    _enrich_semantic_review_async,
    _enrich_with_btr_provenance,
    _has_direct_sensitive_request,
    _has_sensitive_url_path,
    _has_social_engineering_pressure,
    _load_fast_preview_cache,
    _looks_like_official_safety_education,
    _looks_like_structured_invoice_text,
    _local_high_risk_semantic_review,
    _mark_required_pillars_timeout,
    _normalize_fast_preview_cache_entry,
    _normalize_mistral_semantic_review,
    _normalize_model_intent_analysis,
    _normalize_model_social_engineering_signal,
    _official_destination_confirmed,
    _preview_for_final_url_unresolved,
    _provider_pillar_from_summary,
    _provider_required_for_runtime,
    _request_sensitivity_from_signals,
    _semantic_review_for_decision_bundle,
    _social_engineering_signal_for_decision_bundle,
    _user_recommended_action,
    _user_risk_level_label,
    _user_risk_level_text,
)
from services.extract_pipeline import (  # noqa: F401
    extract_email_for_orchestration,
    extract_image_for_orchestration,
    extract_pdf_for_orchestration,
)
from services.scan_helpers import (  # noqa: F401
    _invoice_payment_destination_for_client,
    _is_allowed_image_bytes,
    _validate_file_upload,
    extract_text_for_scan,
)
from services.urlscan_helpers import (  # noqa: F401
    _load_urlscan_preview_cache,
    _normalize_screenshot_proxy_url,
    _normalize_urlscan_preview_cache_entry,
    _public_route_url,
    _urlscan_preview_cache_is_fresh,
    _urlscan_preview_cache_key,
    _urlscan_screenshot_is_ready,
)
from services.urlscan_pipeline import get_urlscan_result  # noqa: F401
from services.external_url_privacy import prepare_external_url, prepare_external_urls, prepare_reputation_lookup_url  # noqa: F401
from services.redirect_resolver import get_spf_dns_record, check_dkim_dns_record, get_dmarc_policy, resolve_redirects_safely  # noqa: F401
from services.urlscan_logic import (  # noqa: F401
    _apply_urlscan_preview_cache_hit,
    _save_urlscan_preview_cache,
    _sanitize_urlscan_result_payload,
    _sync_resolved_urls_with_urlscan_final,
    _urlscan_enhancement_done,
)
from services import rate_limiter  # noqa: F401
import json as json  # noqa: F401 - re-export for legacy test compat
import requests as requests  # noqa: F401 - used externally as main.requests
from services.whois_ssl_signals import check_domain_ssl_parallel  # noqa: F401

__all__ = [
    "app",
    "create_app",
    "engine",
    "orchestrated_engine",
    "brand_truth_registry",
]
