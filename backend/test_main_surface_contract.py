import pathlib
import re

REPO_ROOT = pathlib.Path(__file__).resolve().parent
PATTERN = re.compile(r"\bmain\.([A-Za-z_][A-Za-z0-9_]*)")


def _referenced_main_symbols():
    names = set()
    for py in REPO_ROOT.rglob("*.py"):
        if py.name in {"main.py", "test_main_surface_contract.py"}:
            continue
        text = py.read_text(encoding="utf-8")
        if re.search(r"^\s*import\s+main\b", text, re.M):
            names |= set(PATTERN.findall(text))
    return names


def test_main_exposes_all_referenced_symbols():
    import main

    missing = sorted(name for name in _referenced_main_symbols() if not hasattr(main, name))
    assert not missing, f"main.X rupt: {missing}"
