"""Regression guard: no f-string may emit a literal brace wrapping a URL.

Background
----------
The RDAP domain-age lookup in ``services/whois_ssl_signals.py`` was written
as an f-string with doubled (literal) braces around the URL, e.g.::

    f"{{https://rdap.org/domain/{domain}}}"

In Python an f-string turns ```` / ```` into literal ``{`` / ``}``
characters, so the request URL became ``{https://rdap.org/domain/example.com}``
and every RDAP request failed silently, disabling the domain-age signals.

This test walks the entire ``backend/`` source tree and parses each module
with :mod:`ast`. Working on the AST (not the raw text) makes the check
byte-accurate and immune to editor/terminal brace-doubling display
artifacts: ``ast`` already collapses ``{{`` to a single ``{`` inside the
string constant of an f-string, so a literal brace that survives in a
constant segment is a *real* literal brace in the emitted string.

The signature we flag is intentionally narrow -- a literal ``{`` immediately
followed by a URL scheme (``{http://`` / ``{https://``). That matches the
bug class (a URL accidentally wrapped in literal braces) while leaving
correct code alone:

* single-brace field substitution such as
  ``f"https://api/{project}/queues"`` -> not flagged (no literal brace).
* JSON-body f-strings such as ``f'"url": "https://x"'`` -> not flagged
  (the literal ``{`` is followed by a quote, not by a scheme).
"""

import ast
import os
import pathlib
import re

# Directory that holds this test == the backend source root.
BACKEND_DIR = pathlib.Path(__file__).resolve().parent

# Directories that never contain shippable URL-building source.
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "testdata",
    "data",
    "docs",
}

# A literal open brace immediately wrapping a URL scheme is the bug signature.
_BRACE_URL_RE = re.compile(r"\{https?://")


def _joined_str_literal(node: ast.JoinedStr) -> str:
    """Concatenate only the literal (constant) segments of an f-string.

    ``ast`` stores f-string text constants with ````/```` already
    collapsed to single braces, so any brace seen here is a literal brace
    that the f-string will emit at runtime.
    """
    return "".join(
        value.value
        for value in node.values
        if isinstance(value, ast.Constant) and isinstance(value.value, str)
    )


def _scan_source(path: pathlib.Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        # Not parseable under this interpreter; nothing to assert here.
        return []
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            literal = _joined_str_literal(node)
            if _BRACE_URL_RE.search(literal):
                offenders.append((path, node.lineno))
    return offenders


def _iter_python_files():
    for root, dirs, files in os.walk(BACKEND_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.endswith(".py") and name != os.path.basename(__file__):
                yield pathlib.Path(root) / name


def test_no_literal_brace_wrapped_urls():
    offenders = []
    for path in _iter_python_files():
        offenders.extend(_scan_source(path))

    assert not offenders, (
        "Found f-string(s) that emit a literal brace wrapping a URL. "
        "Build the URL with plain string concatenation instead of an "
        "f-string with doubled braces:\n"
        + "\n".join(
            "  {0}:{1}".format(p.relative_to(BACKEND_DIR), line)
            for p, line in offenders
        )
    )
