from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
DOCKERFILE = BACKEND_DIR / "Dockerfile"
LOCKFILE = BACKEND_DIR / "requirements.lock"
REQUIREMENTS = BACKEND_DIR / "requirements.txt"


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


def test_cloud_run_lockfile_covers_declared_requirements():
    requirements = REQUIREMENTS.read_text(encoding="utf-8")
    lockfile = LOCKFILE.read_text(encoding="utf-8")

    declared = []
    for raw_line in requirements.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        package = line.split("==", 1)[0].strip().lower().replace("_", "-")
        declared.append(package)

    missing = [
        package
        for package in declared
        if f"{package}==" not in lockfile.lower().replace("_", "-")
    ]
    assert missing == []
