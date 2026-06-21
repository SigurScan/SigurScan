"""Orchestrated-scan engine, extracted from main.py incrementally.

Functions reference their main-module siblings/helpers/config/state via `import main;
main.X` (resolved at call time). main.py re-exports these names, so existing test
monkeypatching of main.<symbol> keeps working unchanged.
"""

import os
import re
import json
import time
import asyncio
import hashlib
import base64
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool
from bs4 import BeautifulSoup, Comment
import tldextract
from pypdf import PdfReader

import main


def _orchestrated_metrics(job: Dict[str, Any]) -> Dict[str, Any]:
    metrics = job.get("orchestration_metrics")
    if not isinstance(metrics, dict):
        metrics = {}
        job["orchestration_metrics"] = metrics
    metrics.setdefault("poll_count", 0)
    metrics.setdefault("stage_durations_ms", {})
    metrics.setdefault("component_durations_ms", {})
    metrics.setdefault("stage_sequence", [])
    metrics.setdefault("conflict_merge_count", 0)
    metrics.setdefault("conflict_merge_retry_count", 0)
    metrics.setdefault("conflict_merge_retry_failures", 0)
    metrics.setdefault("urlscan_reclaim_count", 0)
    metrics.setdefault("urlscan_reservation_guard_hits", 0)
    metrics.setdefault("urlscan_timeout_count", 0)
    metrics.setdefault("stage_entered_at", int(job.get("created_at") or int(time.time())))
    return metrics


def _increment_orchestrated_metric(job: Dict[str, Any], key: str, amount: int = 1) -> None:
    metrics = main._orchestrated_metrics(job)
    try:
        metrics[key] = int(metrics.get(key, 0) or 0) + int(amount)
    except Exception:
        metrics[key] = int(amount)


def _record_orchestrated_component_duration(job: Dict[str, Any], component: str, started_at: float) -> None:
    if not isinstance(job, dict):
        return
    elapsed_ms = max(0, int((time.perf_counter() - started_at) * 1000))
    metrics = main._orchestrated_metrics(job)
    durations = metrics.setdefault("component_durations_ms", {})
    if not isinstance(durations, dict):
        durations = {}
        metrics["component_durations_ms"] = durations
    key = str(component or "unknown")
    try:
        durations[key] = int(durations.get(key, 0) or 0) + elapsed_ms
    except Exception:
        durations[key] = elapsed_ms


def _timed_orchestrated_component(job: Dict[str, Any], component: str, fn):
    started_at = time.perf_counter()
    try:
        return fn()
    finally:
        main._record_orchestrated_component_duration(job, component, started_at)


def _set_orchestrated_stage(job: Dict[str, Any], next_stage: str) -> None:
    if not isinstance(job, dict):
        return
    next_stage = str(next_stage or "").strip().lower() or "queued"
    now = int(time.time())
    metrics = main._orchestrated_metrics(job)
    previous_stage = str(job.get("pipeline_stage") or "").strip().lower()
    previous_entered_at = int(metrics.get("stage_entered_at") or job.get("created_at") or now)
    if previous_stage and previous_stage != next_stage:
        durations = metrics.setdefault("stage_durations_ms", {})
        durations[previous_stage] = int(durations.get(previous_stage, 0) or 0) + max(0, now - previous_entered_at) * 1000
        metrics["stage_entered_at"] = now
        sequence = metrics.setdefault("stage_sequence", [])
        if isinstance(sequence, list):
            sequence.append({"stage": next_stage, "at": now})
    elif not previous_stage:
        metrics["stage_entered_at"] = now
        sequence = metrics.setdefault("stage_sequence", [])
        if isinstance(sequence, list):
            sequence.append({"stage": next_stage, "at": now})
    job["pipeline_stage"] = next_stage


def _emit_orchestrated_telemetry(event_type: str, job: Dict[str, Any], **metadata: Any) -> None:
    if not isinstance(job, dict):
        return
    scan_id = str(job.get("scan_id") or "").strip()
    if not scan_id:
        return
    try:
        metrics = main._orchestrated_metrics(job)
        urlscan_state = job.get("urlscan") if isinstance(job.get("urlscan"), dict) else {}
        main.log_scan_event(
            {
                "scan_id": scan_id,
                "event_type": event_type,
                "input_type": job.get("input_type", "unknown"),
                "source_channel": job.get("source_channel"),
                "risk_score": 0,
                "risk_level": None,
                "url_count": len(job.get("urls") if isinstance(job.get("urls"), list) else []),
                "metadata": {
                    "pipeline_stage": job.get("pipeline_stage"),
                    "status": job.get("status"),
                    "poll_count": metrics.get("poll_count"),
                    "age_ms": max(0, int(time.time()) - int(job.get("created_at") or int(time.time()))) * 1000,
                    "stage_durations_ms": metrics.get("stage_durations_ms", {}),
                    "component_durations_ms": metrics.get("component_durations_ms", {}),
                    "urlscan_status": urlscan_state.get("status"),
                    "urlscan_uuid": urlscan_state.get("uuid"),
                    "conflict_merge_count": metrics.get("conflict_merge_count", 0),
                    "conflict_merge_retry_count": metrics.get("conflict_merge_retry_count", 0),
                    "conflict_merge_retry_failures": metrics.get("conflict_merge_retry_failures", 0),
                    "urlscan_reclaim_count": metrics.get("urlscan_reclaim_count", 0),
                    "urlscan_reservation_guard_hits": metrics.get("urlscan_reservation_guard_hits", 0),
                    "urlscan_timeout_count": metrics.get("urlscan_timeout_count", 0),
                    **metadata,
                },
            }
        )
    except Exception:
        return


def _persist_orchestrated_job(job: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(job, dict) or not job.get("scan_id"):
        return job
    scan_id = str(job["scan_id"])
    saved = main.supabase_store.save_scan_job(job)
    if saved is False:
        main._increment_orchestrated_metric(job, "conflict_merge_count")
        reloaded = main.supabase_store.load_scan_job(scan_id)
        if isinstance(reloaded, dict):
            merged = main._merge_orchestrated_conflict_job(reloaded, job)
            if merged != reloaded:
                retry_saved = False
                for _ in range(2):
                    main._increment_orchestrated_metric(merged, "conflict_merge_retry_count")
                    retry_saved = main.supabase_store.save_scan_job(merged)
                    if retry_saved is not False:
                        break
                    latest = main.supabase_store.load_scan_job(scan_id)
                    if isinstance(latest, dict):
                        merged = main._merge_orchestrated_conflict_job(latest, merged)
                if retry_saved is False:
                    main._increment_orchestrated_metric(merged, "conflict_merge_retry_failures")
                main._emit_orchestrated_telemetry(
                    "orchestrated_conflict_merge",
                    merged,
                    retry_saved=retry_saved is not False,
                )
            main._ORCHESTRATED_SCAN_JOBS[scan_id] = merged
            return merged
        main._increment_orchestrated_metric(job, "persist_fallback_memory_count")
        main._ORCHESTRATED_SCAN_JOBS[scan_id] = job
        main._emit_orchestrated_telemetry("orchestrated_persist_memory_fallback", job)
        return job
    main._ORCHESTRATED_SCAN_JOBS[scan_id] = job
    return job


def _load_orchestrated_job(scan_id: str) -> Optional[Dict[str, Any]]:
    job = main.supabase_store.load_scan_job(scan_id)
    if isinstance(job, dict):
        main._ORCHESTRATED_SCAN_JOBS[scan_id] = job
        return job
    job = main._ORCHESTRATED_SCAN_JOBS.get(scan_id)
    if isinstance(job, dict):
        return job
    return None


def _orchestrated_lock_owner(scan_id: str) -> str:
    return f"cloudrun:{os.getenv('K_REVISION', 'local')}:{os.getpid()}:{scan_id}:{time.time_ns()}"


def _claim_distributed_orchestrated_refresh(job: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    revision = job.get("_storage_revision")
    scan_id = str(job.get("scan_id") or "")
    if not scan_id or not isinstance(revision, int):
        return None
    claimed = main.supabase_store.claim_scan_job(
        scan_id,
        expected_revision=revision,
        owner=main._orchestrated_lock_owner(scan_id),
        active_step=str(job.get("pipeline_stage") or "queued"),
        lock_seconds=main.ORCHESTRATED_REFRESH_LOCK_TTL_SECONDS,
    )
    if not isinstance(claimed, dict):
        return None
    claimed_job = main.supabase_store.scan_job_from_record(claimed)
    if isinstance(claimed_job, dict):
        main._ORCHESTRATED_SCAN_JOBS[scan_id] = claimed_job
        return claimed_job
    return job


def _prune_orchestrated_jobs() -> None:
    now = int(time.time())
    expired = [
        scan_id
        for scan_id, job in main._ORCHESTRATED_SCAN_JOBS.items()
        if now - int(job.get("created_at", now)) > main.ORCHESTRATED_JOB_TTL_SECONDS
    ]
    for scan_id in expired:
        main._ORCHESTRATED_SCAN_JOBS.pop(scan_id, None)
        main._ORCHESTRATED_SCAN_LOCKS.pop(scan_id, None)


def _orchestrated_stage_rank(stage: Any) -> int:
    return main._ORCHESTRATED_STAGE_RANK.get(str(stage or "").strip().lower(), -1)


def _merge_orchestrated_conflict_job(reloaded: Dict[str, Any], local: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(reloaded)
    local_urlscan = local.get("urlscan") if isinstance(local.get("urlscan"), dict) else {}
    local_is_unpersisted_urlscan_reservation = (
        str(local_urlscan.get("status") or "").strip().lower() == "submitting"
        and not local_urlscan.get("uuid")
    )

    if (
        not local_is_unpersisted_urlscan_reservation
        and main._orchestrated_stage_rank(local.get("pipeline_stage")) > main._orchestrated_stage_rank(merged.get("pipeline_stage"))
    ):
        merged["pipeline_stage"] = local.get("pipeline_stage")

    for key in (
        "resolved_urls",
        "primary_final_url",
        "threat_intel",
        "analysis",
        "result",
        "claim_verifier_required",
        "offer_web_claim",
        "invoice_analysis_text",
    ):
        local_value = local.get(key)
        if local_value not in (None, "", [], {}) and merged.get(key) in (None, "", [], {}):
            merged[key] = main._deep_copy_jsonable(local_value)

    merged_urlscan = merged.get("urlscan") if isinstance(merged.get("urlscan"), dict) else {}
    if local_urlscan and not local_is_unpersisted_urlscan_reservation:
        merged_urlscan = dict(merged_urlscan)
        local_has_uuid = bool(local_urlscan.get("uuid"))
        merged_has_uuid = bool(merged_urlscan.get("uuid"))
        if local_has_uuid and not merged_has_uuid:
            merged_urlscan = main._deep_copy_jsonable(local_urlscan)
        else:
            merged_urlscan = main._merge_progress_dict(
                merged_urlscan,
                local_urlscan,
                ranker=main._urlscan_merge_rank,
            )
        merged["urlscan"] = merged_urlscan

    local_preview = local.get("preview") if isinstance(local.get("preview"), dict) else {}
    if local_preview:
        merged_preview = dict(merged.get("preview") if isinstance(merged.get("preview"), dict) else {})
        merged_preview = main._merge_progress_dict(
            merged_preview,
            local_preview,
            ranker=main._preview_merge_rank,
        )
        merged["preview"] = merged_preview

    local_metrics = local.get("orchestration_metrics") if isinstance(local.get("orchestration_metrics"), dict) else {}
    if local_metrics:
        merged_metrics = dict(merged.get("orchestration_metrics") if isinstance(merged.get("orchestration_metrics"), dict) else {})
        for key, value in local_metrics.items():
            if key in {"stage_durations_ms", "component_durations_ms"} and isinstance(value, dict):
                durations = dict(merged_metrics.get("stage_durations_ms") if isinstance(merged_metrics.get("stage_durations_ms"), dict) else {})
                if key == "component_durations_ms":
                    durations = dict(merged_metrics.get("component_durations_ms") if isinstance(merged_metrics.get("component_durations_ms"), dict) else {})
                for stage_name, duration_ms in value.items():
                    try:
                        durations[str(stage_name)] = max(int(durations.get(stage_name, 0) or 0), int(duration_ms))
                    except Exception:
                        continue
                merged_metrics[key] = durations
            elif key == "stage_sequence" and isinstance(value, list):
                existing_sequence = merged_metrics.get("stage_sequence")
                if not isinstance(existing_sequence, list) or len(value) > len(existing_sequence):
                    merged_metrics["stage_sequence"] = main._deep_copy_jsonable(value)
            else:
                try:
                    merged_metrics[key] = max(int(merged_metrics.get(key, 0) or 0), int(value))
                except Exception:
                    if merged_metrics.get(key) in (None, "", [], {}):
                        merged_metrics[key] = main._deep_copy_jsonable(value)
        merged["orchestration_metrics"] = merged_metrics

    return merged


def _orchestrated_result_fingerprint(
    job: Dict[str, Any],
    analysis: Dict[str, Any],
    pillars: Dict[str, Dict[str, Any]],
    resolved_urls: List[Dict[str, Any]],
) -> str:
    payload = {
        "redacted_text": job.get("redacted_text", ""),
        "analysis": analysis,
        "pillars": pillars,
        "resolved_urls": resolved_urls,
        "primary_final_url": job.get("primary_final_url"),
        "urlscan": job.get("urlscan") if isinstance(job.get("urlscan"), dict) else {},
    }
    serialized = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _build_orchestrated_pillars(job: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    analysis = job.get("analysis") if isinstance(job.get("analysis"), dict) else {}
    evidence = analysis.get("evidence", {}) if isinstance(analysis.get("evidence"), dict) else {}
    summary = evidence.get("external_intel_summary") if isinstance(evidence.get("external_intel_summary"), dict) else {}
    resolved_urls = job.get("resolved_urls") if isinstance(job.get("resolved_urls"), list) else []
    raw_urls = job.get("urls") if isinstance(job.get("urls"), list) else []
    has_urls = bool(raw_urls or resolved_urls)
    final_url = job.get("primary_final_url") or main._first_final_url(resolved_urls)
    job_input_type = str(job.get("input_type") or "").strip().lower()

    claim = evidence.get("offer_claim_verification") if isinstance(evidence.get("offer_claim_verification"), dict) else {}
    claim_status = str(claim.get("status") or "").strip().lower()
    claim_required = bool(job.get("claim_verifier_required", main._claim_verifier_required(analysis)))
    semantic_review = evidence.get("semantic_review") if isinstance(evidence.get("semantic_review"), dict) else {}
    semantic_status = str(semantic_review.get("status") or "").strip().lower()
    claimed_brand = str(analysis.get("claimed_brand") or "Nespecificat")
    official_destination = main._official_destination_confirmed(resolved_urls, claimed_brand)
    provider_projection = main._provider_verdict_for_decision_bundle(summary, has_urls=has_urls)
    provider_projection_verdict = str(provider_projection.get("verdict") or "unknown").strip().lower()
    semantic_complete = (
        (semantic_status == "done" and semantic_review.get("completeness") is not False)
        or (job_input_type == "invoice" and semantic_status == "done")
        or provider_projection_verdict == "malicious"
        or (official_destination and provider_projection_verdict == "clean")
    )
    semantic_details = semantic_status or "atlas/corpus semantic review pending"
    if provider_projection_verdict == "malicious":
        semantic_details = "provider malicious decisive; semantic review not blocking"
    elif official_destination and provider_projection_verdict == "clean" and not semantic_status:
        semantic_details = "official clean destination accepted as legit semantic template"

    urlscan_state = job.get("urlscan") if isinstance(job.get("urlscan"), dict) else {}
    urlscan_status = str(urlscan_state.get("status") or "").strip().lower()
    screenshot_ready = bool(urlscan_state.get("screenshot_ready"))
    if urlscan_status == "finished":
        details = str(urlscan_state.get("verdict") or "finished")
        if not screenshot_ready:
            details = f"{details}; captura inca se proceseaza"
        urlscan_pillar = main._pillar("ok", required=False, details=details, ref=urlscan_state.get("uuid"))
    elif urlscan_status == "skipped" and not has_urls:
        urlscan_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru preview")
    elif urlscan_status in {"error", "timeout", "rate_limited", "skipped"}:
        urlscan_details = str(urlscan_state.get("details") or urlscan_status)
        if urlscan_status == "timeout" and urlscan_state.get("verdict") and urlscan_state.get("report_url"):
            urlscan_pillar = main._pillar(
                "ok",
                required=False,
                details=f"{urlscan_state.get('verdict')}; captura indisponibila la provider",
                ref=urlscan_state.get("uuid"),
            )
        elif official_destination and main._urlscan_scan_prevented(urlscan_details):
            urlscan_pillar = main._pillar(
                "ok",
                required=False,
                details="urlscan a refuzat sandbox-ul pentru o destinatie oficiala; preview indisponibil.",
                ref=urlscan_state.get("uuid"),
            )
        else:
            urlscan_pillar = main._pillar("error", required=False, details=urlscan_details, ref=urlscan_state.get("uuid"))
    elif urlscan_state.get("uuid"):
        urlscan_pillar = main._pillar("pending", required=False, details="urlscan verdict este in procesare.", ref=urlscan_state.get("uuid"))
    else:
        urlscan_pillar = main._pillar("pending", required=False, details="urlscan verdict nu a pornit.")

    if not has_urls:
        final_url_pillar = main._pillar("not_required", required=False, details="mesajul nu contine URL verificabil")
        web_risk_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru Web Risk")
        asf_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru ASF")
        phishing_database_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru Phishing.Database")
        phishtank_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru PhishTank")
        openphish_pillar = main._pillar("not_required", required=False, details="nu exista URL pentru OpenPhish")
    else:
        final_url_pillar = main._pillar("ok" if final_url else "pending", details=str(final_url or "se rezolva destinatia finala"))
        web_risk_pillar = main._provider_pillar_from_summary(summary, "google_web_risk")
        asf_pillar = main._provider_pillar_from_summary(summary, "asf_investor_alerts")
        asf_pillar["required"] = False
        phishing_database_pillar = main._provider_pillar_from_summary(summary, "phishing_database")
        phishtank_pillar = main._provider_pillar_from_summary(summary, "phishtank_online_valid")
        openphish_pillar = main._provider_pillar_from_summary(summary, "openphish")
        openphish_pillar["required"] = False

    return {
        "final_url": final_url_pillar,
        "google_web_risk": web_risk_pillar,
        "asf_investor_alerts": asf_pillar,
        "phishing_database": phishing_database_pillar,
        "phishtank_online_valid": phishtank_pillar,
        "openphish": openphish_pillar,
        "urlscan": urlscan_pillar,
        "claim_verifier": main._pillar(
            (
                "not_required"
                if not claim_required
                else "ok"
                if claim_status in {"confirmed", "not_found", "inconclusive", "skipped"}
                else "pending"
            ),
            required=claim_required,
            details=claim_status or ("required" if claim_required else "not required"),
        ),
        "semantic_review": main._pillar(
            "ok" if semantic_complete else "pending",
            required=True,
            details=semantic_details,
        ),
    }


def _orchestrated_required_pillars_timed_out(job: Dict[str, Any]) -> bool:
    created_at = int(job.get("created_at") or int(time.time()))
    return int(time.time()) - created_at >= main.ORCHESTRATED_REQUIRED_PILLAR_TIMEOUT_SECONDS


def _normalize_orchestrated_preview_status(job: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(preview, dict):
        return {}
    normalized = dict(preview)
    status = str(normalized.get("status") or "").strip().lower()
    has_visual = bool(normalized.get("image_url") or normalized.get("screenshot_url"))
    if status != "ready" or has_visual:
        return normalized

    urlscan_state = job.get("urlscan") if isinstance(job.get("urlscan"), dict) else {}
    looks_like_urlscan_preview = (
        str(normalized.get("source") or "").strip().lower() == "urlscan"
        or bool(normalized.get("report_url"))
        or bool(urlscan_state.get("uuid"))
        or str(urlscan_state.get("status") or "").strip().lower() in {"pending", "finished", "timeout"}
    )
    if not looks_like_urlscan_preview:
        return normalized

    normalized["status"] = "pending"
    normalized["source"] = "urlscan"
    normalized["image_url"] = None
    normalized["screenshot_url"] = None
    normalized["reason"] = normalized.get("reason") or "urlscan_screenshot_pending"
    return normalized


def _orchestrated_status_payload(job: Dict[str, Any]) -> Dict[str, Any]:
    pillars = main._build_orchestrated_pillars(job)
    raw_preview = job.get("preview") if isinstance(job.get("preview"), dict) else {}
    preview = main._normalize_orchestrated_preview_status(job, main._preview_for_final_url_unresolved(job, raw_preview))
    result = job.get("result") if isinstance(job.get("result"), dict) else None
    metrics = _orchestrated_metrics(job)
    result_is_final = result is not None and result.get("is_final", True) is not False
    final_url_unresolved = preview.get("reason") == "final_url_unresolved"
    enhancement_done = main._urlscan_enhancement_done(job) or final_url_unresolved
    if result_is_final:
        status = "complete"
    elif main._has_required_pillar_error(pillars):
        status = "incomplete"
    else:
        status = "scanning"
    job["status"] = status
    preview_pending = preview.get("status") == "pending" or preview.get("reason") in {
        "urlscan_pending",
        "urlscan_screenshot_pending",
    } or not (preview.get("image_url") or preview.get("screenshot_url"))
    poll_after_ms = 3000 if (
        status in {"scanning", "complete"}
        and isinstance(job.get("urlscan"), dict)
        and str(job["urlscan"].get("status") or "").lower() == "pending"
        and job["urlscan"].get("uuid")
        and preview_pending
    ) else 1000
    return {
        "scan_id": job["scan_id"],
        "status": status,
        "status_message": (
            "Scanarea este finalizata. Destinatia finala nu poate fi incarcata/verificata; nu continua fara verificare oficiala."
            if status == "complete" and final_url_unresolved
            else
            "Scanarea este finalizata."
            if status == "complete" and enhancement_done
            else "Verdictul este finalizat. Preview-ul securizat se poate actualiza separat."
            if status == "complete" and not enhancement_done
            else "Verdict preliminar disponibil. Verificarea suplimentara (sandbox) continua si poate doar creste nivelul de risc."
            if status == "scanning" and result is not None
            else "Scanarea continua pana cand verificarile necesare returneaza date."
            if status == "scanning"
            else "Scanarea nu are inca toate verificarile necesare pentru verdict sigur."
        ),
        "poll_after_ms": poll_after_ms,
        "pillars": pillars,
        "preview": preview,
        "result": result,
        "diagnostics": {
            "pipeline_stage": job.get("pipeline_stage"),
            "poll_count": metrics.get("poll_count", 0),
            "stage_durations_ms": metrics.get("stage_durations_ms", {}),
            "component_durations_ms": metrics.get("component_durations_ms", {}),
            "urlscan_status": (job.get("urlscan") if isinstance(job.get("urlscan"), dict) else {}).get("status"),
        },
    }


def _orchestrated_revision(job: Dict[str, Any]) -> int:
    revision = job.get("_storage_revision")
    if revision is None:
        revision = job.get("revision")
    try:
        return int(revision)
    except (TypeError, ValueError):
        return 0


def _orchestrated_verdict_state(status_payload: Dict[str, Any]) -> str:
    result = status_payload.get("result")
    status = str(status_payload.get("status") or "").strip().lower()
    if isinstance(result, dict):
        if result.get("is_final", True) is not False:
            return "verdict_done"
        return "verdict_pending"
    if status in {"incomplete", "error"}:
        return "verdict_error"
    return "running"


def _orchestrated_preview_state(status_payload: Dict[str, Any]) -> str:
    preview = status_payload.get("preview") if isinstance(status_payload.get("preview"), dict) else {}
    preview_status = str(preview.get("status") or "").strip().lower()
    reason = str(preview.get("reason") or "").strip().lower()
    has_visual = bool(preview.get("image_url") or preview.get("screenshot_url"))
    if has_visual:
        return "ready"
    if preview_status == "ready" and not has_visual:
        return "pending"
    if reason in {"no_url", "privacy_safe_mode"}:
        return "not_applicable"
    if preview_status == "pending" or reason in {"urlscan_pending", "urlscan_screenshot_pending"}:
        return "pending"
    if preview_status == "unavailable" or reason in {
        "final_url_unresolved",
        "preview_unavailable",
        "urlscan_timeout",
        "urlscan_screenshot_timeout",
    }:
        return "timeout"
    return "unknown"


def _orchestrated_read_status_payload(job: Dict[str, Any], *, changed: bool) -> Dict[str, Any]:
    payload = main._orchestrated_status_payload(job)
    payload["revision"] = main._orchestrated_revision(job)
    payload["changed"] = bool(changed)
    payload["verdict_state"] = main._orchestrated_verdict_state(payload)
    payload["preview_state"] = main._orchestrated_preview_state(payload)
    return payload


def _orchestrated_status_changed(job: Dict[str, Any], after_revision: Optional[int]) -> bool:
    if after_revision is None:
        return True
    return main._orchestrated_revision(job) > after_revision


def _orchestrated_worker_can_stop(status_payload: Dict[str, Any]) -> bool:
    if status_payload.get("verdict_state") != "verdict_done":
        return False
    return status_payload.get("preview_state") in {"ready", "timeout", "not_applicable"}


async def _wait_for_orchestrated_status_read(
    scan_id: str,
    *,
    after_revision: Optional[int],
    wait_seconds: float,
) -> Tuple[Optional[Dict[str, Any]], bool]:
    deadline = time.monotonic() + max(0.0, min(wait_seconds, 20.0))
    while True:
        job = main._load_orchestrated_job(scan_id)
        if not isinstance(job, dict):
            return None, False
        changed = main._orchestrated_status_changed(job, after_revision)
        remaining = deadline - time.monotonic()
        if changed or remaining <= 0:
            return job, changed
        await asyncio.sleep(min(0.75, remaining))


def _orchestrated_can_finalize_result(job: Dict[str, Any], pillars: Dict[str, Dict[str, Any]]) -> bool:
    if str(job.get("pipeline_stage") or "").strip().lower() == "done":
        return True
    if not main._all_required_pillars_terminal(pillars):
        return False
    if main.ORCHESTRATED_EARLY_VERDICT:
        # The verdict publishes as soon as the required pillars are terminal.
        # It stays is_final=false until the urlscan report is terminal, and the
        # report can only raise severity when it lands.
        return True
    # Legacy pacing: user-facing verdicts wait for the urlscan report when a
    # URL exists, but not for screenshot availability. The screenshot is an
    # async visual enhancement and can fill in after the final label.
    return main._urlscan_result_ready_for_verdict(job)


def _orchestrated_result_is_final(job: Dict[str, Any], analysis: Dict[str, Any]) -> bool:
    evidence = analysis.get("evidence", {}) if isinstance(analysis.get("evidence"), dict) else {}
    gate = evidence.get("verdict_gate") if isinstance(evidence.get("verdict_gate"), dict) else {}
    if main._final_url_unresolved_entry(job):
        return True
    label = str(gate.get("label") or "").upper()
    if label in {"SAFE", "SUSPECT", "DANGEROUS"}:
        return True
    if label != "UNVERIFIED":
        return False
    decision_bundle = evidence.get("decision_bundle") if isinstance(evidence.get("decision_bundle"), dict) else {}
    bundle_input = decision_bundle.get("input") if isinstance(decision_bundle.get("input"), dict) else {}
    if bundle_input.get("type") == "invoice":
        return True
    has_url_context = bool(job.get("urls")) or bool(job.get("resolved_urls"))
    if not has_url_context:
        provider_gate = evidence.get("provider_gate") if isinstance(evidence.get("provider_gate"), dict) else {}
        timeout_family = str(analysis.get("detected_family_id") or "") == "provider-gate-required-timeout"
        return (
            provider_gate.get("required_timeout") is not True
            and not timeout_family
            and job.get("required_pillars_timed_out") is not True
        )
    reason_codes = {str(item).strip() for item in gate.get("reason_codes") or []}
    return not (reason_codes & {"insufficient_evidence", "provider_error"})


def _orchestrated_cloud_tasks_configured() -> bool:
    return bool(
        main.ORCHESTRATED_CLOUD_TASKS_ENABLED
        and main.CLOUD_TASKS_PROJECT
        and main.CLOUD_TASKS_LOCATION
        and main.CLOUD_TASKS_QUEUE
        and main.INTERNAL_WORKER_TOKEN
    )


def _orchestrated_worker_task_url(scan_id: str, *, max_steps: int = 1) -> str:
    safe_scan_id = urllib.parse.quote(str(scan_id), safe="")
    step_budget = max(1, min(int(max_steps or 1), 3))
    public_base = main.SIGURSCAN_PUBLIC_API_BASE_URL or "https://api.sigurscan.com"
    return f"{public_base}/internal/orchestrated/{safe_scan_id}/advance?max_steps={step_budget}"


def _enqueue_orchestrated_worker_task(
    scan_id: str,
    request: Request,
    *,
    delay_seconds: int = 0,
    max_steps: int = 1,
) -> bool:
    if not main._orchestrated_cloud_tasks_configured():
        return False
    try:
        access_token = main._cloud_tasks_access_token()
        queue_url = (
            f"https://cloudtasks.googleapis.com/v2/projects/{main.CLOUD_TASKS_PROJECT}/"
            f"locations/{main.CLOUD_TASKS_LOCATION}/queues/{main.CLOUD_TASKS_QUEUE}/tasks"
        )
        body = json.dumps({"scan_id": str(scan_id)}, ensure_ascii=False).encode("utf-8")
        task: Dict[str, Any] = {
            "httpRequest": {
                "httpMethod": "POST",
                "url": main._orchestrated_worker_task_url(scan_id, max_steps=max_steps),
                "headers": {
                    "Content-Type": "application/json",
                    "X-Internal-Worker-Token": main.INTERNAL_WORKER_TOKEN,
                },
                "body": base64.b64encode(body).decode("ascii"),
            }
        }
        if delay_seconds > 0:
            run_at = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
            task["scheduleTime"] = run_at.isoformat().replace("+00:00", "Z")
        response = main.requests.post(
            queue_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={"task": task},
            timeout=main.CLOUD_TASKS_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        main.logger.warning("orchestrated Cloud Tasks enqueue failed: %s", type(exc).__name__)
        return False


def _build_orchestrated_text_context(payload: OrchestratedScanRequest) -> Dict[str, Any]:
    input_type = (payload.input_type or "text").strip().lower()
    source_channel = payload.source_channel or "android_native"

    if input_type == "url":
        raw_input = main._normalise_obfuscated_text(payload.url or payload.text or "").strip()
        embedded_urls = main.extract_urls(raw_input)
        if embedded_urls:
            first_url = embedded_urls[0]
            raw_text = raw_input if payload.text else f"Link: {first_url}"
            return {
                "input_type": "url",
                "source_channel": source_channel,
                "raw_text": raw_text,
                "urls": embedded_urls,
                "extra_fields": {"input_url": payload.url or payload.text, "canonical_url": first_url},
            }

        url = main._canonicalize_url(raw_input)
        if not url:
            raise HTTPException(status_code=400, detail="URL invalid sau format neacceptat.")
        return {
            "input_type": "url",
            "source_channel": source_channel,
            "raw_text": f"Link: {url}",
            "urls": [url],
            "extra_fields": {"input_url": payload.url or payload.text, "canonical_url": url},
        }

    if input_type in {"email", "email_html", "html"}:
        raw_email_or_html = payload.html_content or payload.text or ""
        mime_parts = main._extract_email_mime_parts(payload.text or "") if input_type == "email" and not payload.html_content else {}
        plain_text_context = main._normalise_obfuscated_text(mime_parts.get("plain") or "")
        email_subject = main._normalise_obfuscated_text(mime_parts.get("subject") or "")
        html_to_parse = main._normalise_obfuscated_text(
            payload.html_content
            or mime_parts.get("html")
            or plain_text_context
            or payload.text
            or ""
        )
        main._validate_text_input("Conținutul HTML trimis", raw_email_or_html, main.MAX_TEXT_CHARS * 8)
        soup = BeautifulSoup(html_to_parse, "html.parser")
        click_targets = main._collect_click_targets_from_html(soup)
        form_context = main._collect_form_context_from_html(soup)
        discovered_urls: List[str] = []
        buttons: List[Dict[str, Any]] = []
        cta_words = ["verific", "confirm", "plăte", "plate", "cont", "login", "conect", "intrare", "detalii", "colet", "awb", "reactivare", "urgent"]
        for target in click_targets:
            raw_url = target.get("original_url")
            if not raw_url or raw_url in discovered_urls:
                continue
            discovered_urls.append(raw_url)
            button_text = str(target.get("button_text") or "")
            buttons.append(
                {
                    "button_text": button_text,
                    "original_url": raw_url,
                    "is_sensitive_cta": any(word in button_text.lower() for word in cta_words),
                    "source_tag": target.get("source_tag"),
                    "source_attr": target.get("source_attr"),
                }
            )
        visible_text = soup.get_text(separator=" ", strip=True)
        for url in main.extract_urls(plain_text_context):
            if url not in discovered_urls:
                discovered_urls.append(url)
        for url in main.extract_urls(visible_text):
            if url not in discovered_urls:
                discovered_urls.append(url)
        inferred_brand_hints = main._infer_brand_hints_from_click_targets(click_targets)
        click_context = [
            f"CTA {button.get('source_tag')}/{button.get('source_attr')}: "
            f"{button.get('button_text')} -> {button.get('original_url')}"
            for button in buttons
            if button.get("original_url")
        ]
        raw_text = "\n".join(
            part
            for part in [
                email_subject,
                plain_text_context,
                visible_text,
                " ".join(inferred_brand_hints),
                *form_context,
                *click_context,
            ]
            if str(part or "").strip()
        )
        auto_invoice = main._invoice_auto_route_context(
            source_channel=source_channel,
            raw_text=raw_text,
            urls=discovered_urls,
            extra_fields={
                "buttons": buttons,
                "inferred_brand_hints": inferred_brand_hints,
                "email_mime_parsed": bool(mime_parts),
                "form_context": form_context,
                "is_forwarded_warning": True,
            },
            original_input_type=input_type,
        )
        if auto_invoice:
            return auto_invoice
        return {
            "input_type": "email",
            "source_channel": source_channel,
            "raw_text": raw_text,
            "urls": discovered_urls,
            "extra_fields": {
                "buttons": buttons,
                "inferred_brand_hints": inferred_brand_hints,
                "email_mime_parsed": bool(mime_parts),
                "form_context": form_context,
                "is_forwarded_warning": True,
            },
        }

    if input_type == "invoice":
        raw_text = main._normalise_obfuscated_text((payload.text or payload.url or "").strip())
        main._validate_text_input("Textul facturii", raw_text, main.MAX_TEXT_CHARS)
        return {
            "input_type": "invoice",
            "source_channel": source_channel,
            "raw_text": raw_text,
            "urls": main.extract_urls(raw_text),
            "extra_fields": {"invoice_scan": True},
        }

    if input_type == "offer":
        raw_text = main._normalise_obfuscated_text((payload.text or payload.url or "").strip())
        main._validate_text_input("Textul ofertei", raw_text, main.MAX_TEXT_CHARS)
        return {
            "input_type": "offer",
            "source_channel": source_channel,
            "raw_text": raw_text,
            "urls": main.extract_urls(raw_text),
            "extra_fields": {"offer_scan": True},
        }

    raw_text = main._normalise_obfuscated_text((payload.text or payload.url or "").strip())
    main._validate_text_input("Textul trimis", raw_text, main.MAX_TEXT_CHARS)
    auto_invoice = main._invoice_auto_route_context(
        source_channel=source_channel,
        raw_text=raw_text,
        urls=main.extract_urls(raw_text),
        original_input_type=input_type,
    )
    if auto_invoice:
        return auto_invoice
    return {
        "input_type": "text",
        "source_channel": source_channel,
        "raw_text": raw_text,
        "urls": main.extract_urls(raw_text),
        "extra_fields": {},
    }


async def _start_orchestrated_compat(payload: OrchestratedScanRequest) -> Dict[str, Any]:
    job = await main._create_orchestrated_job(payload)
    return main._orchestrated_status_payload(job)
