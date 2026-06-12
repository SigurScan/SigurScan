from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DOCKERFILE = BACKEND_DIR / "Dockerfile"
LOCKFILE = BACKEND_DIR / "requirements.lock"


def test_cloud_run_container_build_is_reproducible_and_warning_free():
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert dockerfile.startswith(
        "FROM python:3.12.13-slim-trixie@sha256:"
    ), "Cloud Run base image must pin both the Python patch version and image digest"
    assert "pip install --upgrade pip" not in dockerfile
    assert "requirements.lock" in dockerfile
    assert "--require-hashes" in dockerfile
    assert "--root-user-action=ignore" in dockerfile

    lockfile = LOCKFILE.read_text(encoding="utf-8")
    assert "--hash=sha256:" in lockfile
