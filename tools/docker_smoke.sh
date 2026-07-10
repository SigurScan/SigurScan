#!/usr/bin/env bash
# Docker build + import/boot smoke test for the SigurScan backend image.
#
# Guards against the class of deploy regressions where the image *builds* but the
# app cannot *import/boot* -- e.g. a Dockerfile COPY that forgets config.py /
# core/ / runtime_state.py, which crashes Cloud Run with ModuleNotFoundError even
# though `pytest` stays green (pytest runs against the full source tree, not the
# image).
#
# Usage:
#   IMAGE_TAG=sigurscan-backend:test BUILD_CONTEXT=backend PORT=8080 tools/docker_smoke.sh
set -euo pipefail

IMAGE_TAG="${IMAGE_TAG:-sigurscan-backend:smoke}"
BUILD_CONTEXT="${BUILD_CONTEXT:-backend}"
PORT="${PORT:-8080}"

echo "==> Building image ${IMAGE_TAG} from ${BUILD_CONTEXT}/"
docker build -t "${IMAGE_TAG}" "${BUILD_CONTEXT}"

echo "==> Import smoke: verifying the ASGI app imports inside the image"
docker run --rm \
  -e PRIVACY_SAFE_MODE="${PRIVACY_SAFE_MODE:-false}" \
  -e ENABLE_CLOUD_AI_EXPLANATION="${ENABLE_CLOUD_AI_EXPLANATION:-false}" \
  -e ENABLE_MISTRAL_SHADOW_ADJUDICATION="${ENABLE_MISTRAL_SHADOW_ADJUDICATION:-false}" \
  -e INVOICE_CACHE_HMAC_KEY="${INVOICE_CACHE_HMAC_KEY:-ci-test-hmac-key}" \
  "${IMAGE_TAG}" \
  python -c "import app; assert hasattr(app, 'app'), 'app:app ASGI callable is missing'; print('import OK')"

echo "==> Boot smoke: starting the container and probing HTTP"
cid="$(docker run -d \
  -e PRIVACY_SAFE_MODE="${PRIVACY_SAFE_MODE:-false}" \
  -e ENABLE_CLOUD_AI_EXPLANATION="${ENABLE_CLOUD_AI_EXPLANATION:-false}" \
  -e ENABLE_MISTRAL_SHADOW_ADJUDICATION="${ENABLE_MISTRAL_SHADOW_ADJUDICATION:-false}" \
  -e INVOICE_CACHE_HMAC_KEY="${INVOICE_CACHE_HMAC_KEY:-ci-test-hmac-key}" \
  -e PORT="${PORT}" \
  -p "${PORT}:${PORT}" \
  "${IMAGE_TAG}")"

cleanup() {
  docker logs "${cid}" 2>&1 | tail -n 30 || true
  docker rm -f "${cid}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

ok=""
for i in $(seq 1 30); do
  code="$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:${PORT}/" || true)"
  if [ -n "${code}" ] && [ "${code}" != "000" ]; then
    echo "Server responded with HTTP ${code} after ${i}s"
    ok="yes"
    break
  fi
  sleep 1
done

if [ -z "${ok}" ]; then
  echo "::error::Container did not serve HTTP on port ${PORT} within 30s"
  exit 1
fi

echo "==> Smoke test passed"
