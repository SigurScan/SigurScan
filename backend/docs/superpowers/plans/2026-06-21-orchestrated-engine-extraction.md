# Orchestrated-Scan Engine Extraction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the remaining 19 orchestrated-scan engine functions out of `backend/main.py` into `backend/services/orchestrated_scan.py`, preserving 100% of behavior, using the file's existing `import main; main.X` late-binding convention — but driven by an AST-correct qualifier instead of the regex mover that corrupted batch 4.

**Architecture:** The service file already does `import main` at module scope and references every main-side symbol as `main.X`, resolved at call time. Because `main` is the same module object tests patch as `app_main`, every `setattr(app_main, X, …)` already reaches the moved code. We continue this exact convention. The only new machinery is `tools/qualify_orchestrated.py`: a `symtable` + `ast` tool that rewrites a moved function's references to main-module globals into `main.X` precisely — never touching locals, params, closure vars, builtins, string literals, dict keys, or attribute names. Each function (or tight sub-cluster) is moved, qualified, re-exported, and gated on the **full backend pytest suite staying green** before commit.

**Tech Stack:** Python 3, `ast`, `symtable`, pytest. No new runtime dependencies.

---

## The Invariant (read before every task)

Batch 4 did not fail because of the `main.X` pattern. It failed because the regex mover:
1. **Over-qualified** — rewrote names inside string literals and dict keys (`.get("verdict")` → `.get("main.verdict")`) and qualified locals/params that aren't main globals → `AttributeError`/`NameError` (loud crashes → cascade of `AssertionError`).
2. **Under-qualified** — left a main-defined, test-patched helper as a bare service-local binding → the `setattr(app_main, …)` patch missed → **silent** wrong verdict (SAFE→UNVERIFIED).

Both directions are eliminated by qualifying **only** `Name(Load)` nodes that Python's own `symtable` resolves as *module-global references* AND that are actually top-level globals in `main.py` AND are not locally imported stdlib/third-party modules in the service.

**Hard acceptance gate, every task:** `python3 -m pytest -q` from `backend/` must report the same pass count as the baseline recorded in Task 0 (expected: **1400 passed**), with **0 failures**. No task is "done" — and nothing is committed — until the full suite is green. If a move goes red, the diff is one small cluster: read the failure, fix or revert that cluster only, never proceed red.

**Move order is leaf-first** (callees before callers) so that when a moved function references a sibling via `main.X`, that sibling is already moved-and-re-exported (or still in main) — either way `main.X` resolves.

## Scope

**In scope — the 19 engine functions (current `main.py` line anchors):**

| Cluster | Functions |
|---|---|
| A cloud-tasks | `_orchestrated_cloud_tasks_configured` (7522), `_cloud_tasks_access_token` (7532), `_orchestrated_worker_task_url` (7545), `_enqueue_orchestrated_worker_task` (7552) |
| B context-builders | `_invoice_auto_route_context` (9083), `_build_orchestrated_text_context` (9110), `_assemble_extracted_text_for_orchestration` (11160) |
| C urlscan-submit | `_submit_orchestrated_urlscan_preview_once` (8902), `_submit_orchestrated_urlscan` (8870) |
| D finalize | `_finalize_orchestrated_job_if_ready` (8752) |
| E exception-marker | `_mark_orchestrated_job_exception` (10211) |
| F create-job | `_create_orchestrated_job` (9269) |
| G fast-lanes | `_run_orchestrated_fast_lane` (9391), `_run_orchestrated_invoice_fast_lane` (9596), `_run_orchestrated_offer_fast_lane` (9948) |
| H refresh | `_refresh_orchestrated_job_impl` (10320), `_refresh_orchestrated_job` (10313) |
| I compat/starters | `_start_orchestrated_from_extraction` (11182), `_start_orchestrated_compat` (11215) |

**Out of scope (stay in `main.py`):** the FastAPI route handlers (`start_orchestrated_scan`, `get_orchestrated_scan`, `get_orchestrated_scan_status`, `advance_orchestrated_scan_worker`, `extract_image/pdf/email_for_orchestration`) and the pillar/finalize-gate helpers (`_pillar`, `_official_clean_can_finalize_before_urlscan`, `_baseline_pillars_ready_without_urlscan`, `_mark_required_pillars_timeout`, …). The engine calls these via `main.X`; they remain dependencies, not move targets.

## File Structure

- **Create:** `backend/tools/qualify_orchestrated.py` — the AST qualifier (Task 0).
- **Create:** `backend/tools/test_qualify_orchestrated.py` — unit tests for the qualifier (Task 0).
- **Modify:** `backend/services/orchestrated_scan.py` — receives the 19 functions.
- **Modify:** `backend/main.py` — functions cut out; their names appended to the existing `from services.orchestrated_scan import (...)` re-export block at ~line 11496.

---

### Task 0: Build and unit-test the AST qualifier

**Files:**
- Create: `backend/tools/qualify_orchestrated.py`
- Create: `backend/tools/test_qualify_orchestrated.py`

- [ ] **Step 1: Record the green baseline**

Run from `backend/`:
```bash
python3 -m pytest -q 2>&1 | tail -3
```
Expected: a line like `1400 passed` (record the exact number; it is the gate for every later task). If it is not all-green here, stop — the worktree is not at a clean baseline.

- [ ] **Step 2: Write the failing qualifier unit tests**

Create `backend/tools/test_qualify_orchestrated.py`:
```python
import textwrap
from tools.qualify_orchestrated import qualify_source


def _q(src, main_globals, service_imports=frozenset()):
    return qualify_source(
        textwrap.dedent(src), main_globals, service_imports
    )


def test_qualifies_module_global_load():
    out = _q(
        """
        def f(job):
            return helper(job)
        """,
        main_globals={"helper"},
    )
    assert "return main.helper(job)" in out


def test_leaves_param_and_local_untouched():
    out = _q(
        """
        def f(helper):
            local = helper
            return local
        """,
        main_globals={"helper", "local"},
    )
    assert "main." not in out  # helper is a param, local is assigned


def test_never_touches_string_literals_or_dict_keys():
    out = _q(
        """
        def f(job):
            return job.get("helper") or {"helper": 1}
        """,
        main_globals={"helper"},
    )
    assert '"helper"' in out and "main." not in out


def test_never_touches_attribute_names():
    out = _q(
        """
        def f(obj):
            return obj.helper
        """,
        main_globals={"helper"},
    )
    assert "obj.helper" in out and "main." not in out


def test_leaves_locally_imported_modules_bare():
    out = _q(
        """
        def f():
            return time.time()
        """,
        main_globals={"time"},
        service_imports={"time"},
    )
    assert "time.time()" in out and "main.time" not in out


def test_handles_nested_scope_local_shadow():
    out = _q(
        """
        def f(job):
            def inner(helper):
                return helper
            return inner(helper)
        """,
        main_globals={"helper"},
    )
    # outer use is a module global -> qualified; inner param -> not
    assert "return inner(main.helper)" in out
    assert "return helper" in out  # the inner return stays bare


def test_idempotent():
    once = _q(
        "def f(job):\n    return helper(job)\n",
        main_globals={"helper"},
    )
    twice = qualify_source(once, {"helper"}, frozenset())
    assert once == twice


def test_qualifies_inside_comprehension():
    out = _q(
        """
        def f(items):
            return [helper(x) for x in items]
        """,
        main_globals={"helper"},
    )
    assert "main.helper(x)" in out
```

- [ ] **Step 3: Run the tests to verify they fail**

Run from `backend/`:
```bash
python3 -m pytest tools/test_qualify_orchestrated.py -q
```
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.qualify_orchestrated'`.

- [ ] **Step 4: Implement the qualifier**

Create `backend/tools/qualify_orchestrated.py`:
```python
#!/usr/bin/env python3
"""AST-correct `main.` qualifier for functions moved into orchestrated_scan.py.

`qualify_source` rewrites every Name(Load) that Python's symtable resolves as a
module-global reference AND that is a real top-level global in main.py into
`main.<id>` — and nothing else. It never touches parameters, locals, closure
free vars, builtins, locally-imported stdlib/3rd-party modules, string literals,
dict keys, or attribute names (none of those are global-ref Name nodes).

CLI: python3 tools/qualify_orchestrated.py <func> [<func> ...]
applies the transform to the named functions inside services/orchestrated_scan.py
in place and prints a per-function report of what was qualified.
"""
from __future__ import annotations

import ast
import builtins
import symtable
import sys

MAIN = "main.py"
SERVICE = "services/orchestrated_scan.py"
_BUILTINS = frozenset(dir(builtins))


def main_top_level_globals(path: str = MAIN) -> set[str]:
    tree = ast.parse(open(path).read())
    g: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            g.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                g.add(a.asname or a.name.split(".")[0])
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name):
                        g.add(x.id)
        elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name):
            g.add(n.target.id)
    return g


def service_imported_names(path: str = SERVICE) -> set[str]:
    tree = ast.parse(open(path).read())
    s: set[str] = set()
    for n in tree.body:
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                s.add(a.asname or a.name.split(".")[0])
    return s


# AST node types that introduce a new symtable child scope, in the order
# symtable.get_children() yields them.
_SCOPE_NODES = (
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Lambda,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
)


def _global_refs(scope: symtable.SymbolTable) -> set[str]:
    out = set()
    for name in scope.get_identifiers():
        sym = scope.lookup(name)
        if sym.is_global() and not sym.is_local():
            out.add(name)
    return out


def _collect(node, scope, main_globals, service_imports, edits):
    """Walk `node`'s own scope, pairing nested AST scopes with symtable children."""
    qualify = {
        n
        for n in _global_refs(scope)
        if n in main_globals
        and n not in service_imports
        and n not in _BUILTINS
        and n != "main"
    }
    child_scopes = iter(scope.get_children())

    def visit(n, in_own_scope: bool):
        # A scope-creating node: its body belongs to a child symtable scope.
        if isinstance(n, _SCOPE_NODES):
            child = next(child_scopes)
            # The function/lambda signature defaults & comprehension's first
            # iterable are evaluated in the ENCLOSING scope, so recurse into
            # those parts here, then hand the body to the child scope.
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                for d in getattr(n.args, "defaults", []) or []:
                    visit(d, in_own_scope)
                for d in getattr(n.args, "kw_defaults", []) or []:
                    if d is not None:
                        visit(d, in_own_scope)
            _collect(n, child, main_globals, service_imports, edits)
            return
        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
            if n.id in qualify:
                edits.append((n.lineno, n.col_offset, n.end_col_offset, n.id))
            return
        # ast.Attribute: only recurse into .value, never the attr identifier.
        for child in ast.iter_child_nodes(n):
            visit(child, in_own_scope)

    for child in ast.iter_child_nodes(node):
        visit(child, True)


def qualify_source(
    source: str, main_globals: set[str], service_imports: frozenset[str]
) -> str:
    """Return `source` with module-global refs rewritten to `main.<id>`."""
    tree = ast.parse(source)
    table = symtable.symtable(source, "<qualify>", "exec")
    edits: list[tuple[int, int, int, str]] = []
    # Pair each top-level function def in the source with its symtable child.
    fn_nodes = [
        n
        for n in tree.body
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    fn_scopes = [c for c in table.get_children() if c.get_type() == "function"]
    for node, scope in zip(fn_nodes, fn_scopes):
        _collect(node, scope, main_globals, set(service_imports), edits)
    # Apply right-to-left so earlier offsets stay valid.
    lines = source.splitlines(keepends=True)
    for lineno, col, end_col, name in sorted(edits, reverse=True):
        line = lines[lineno - 1]
        lines[lineno - 1] = line[:col] + "main." + name + line[end_col:]
    return "".join(lines)


def _extract_function(service_src: str, name: str) -> tuple[int, int]:
    """Return (start_line, end_line) 1-based inclusive of top-level def `name`."""
    tree = ast.parse(service_src)
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name:
            return n.lineno, n.end_lineno
    raise SystemExit(f"function {name!r} not found at top level of {SERVICE}")


def qualify_service_functions(names: list[str]) -> None:
    main_globals = main_top_level_globals()
    service_imports = frozenset(service_imported_names())
    src = open(SERVICE).read()
    for name in names:
        start, end = _extract_function(src, name)
        lines = src.splitlines(keepends=True)
        block = "".join(lines[start - 1 : end])
        new_block = qualify_source(block, main_globals, service_imports)
        if new_block != block:
            src = "".join(lines[: start - 1]) + new_block + "".join(lines[end:])
        added = new_block.count("main.") - block.count("main.")
        print(f"{name}: +{added} main.<x> qualifications")
    open(SERVICE, "w").write(src)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: qualify_orchestrated.py <func> [<func> ...]")
    qualify_service_functions(sys.argv[1:])
```

- [ ] **Step 5: Run the tests to verify they pass**

Run from `backend/`:
```bash
python3 -m pytest tools/test_qualify_orchestrated.py -q
```
Expected: PASS (8 passed).

- [ ] **Step 6: Commit the tool**

```bash
git add tools/qualify_orchestrated.py tools/test_qualify_orchestrated.py
git commit -m "refactor(backend): add AST-correct main.X qualifier for orchestrated extraction

symtable+ast tool replaces the regex mover that corrupted batch 4.
Qualifies only module-global Name(Load) refs to real main top-level
globals; never touches locals/params/strings/dict-keys/attributes.
Unit-tested for shadowing, comprehensions, and idempotency.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Per-cluster move procedure (Tasks 1–11 all follow this exact shape)

Each move task performs these steps for its cluster's function list `FUNCS`:

1. **Cut** each function in `FUNCS` from `backend/main.py` (full `def`/`async def` body, including its decorator-free leading comment block if any).
2. **Paste** the functions verbatim into `backend/services/orchestrated_scan.py`, appended before the final blank line of the file (module-level order is irrelevant for defs).
3. **Qualify:** run `python3 tools/qualify_orchestrated.py <FUNCS...>` from `backend/`. Read the printed report.
4. **Review the diff obsessively** (`git diff -- services/orchestrated_scan.py`): every change must be `name` → `main.name`. Confirm **zero** edits inside strings, dict keys, f-string format fields, or after a `.` (attribute). Confirm no param/local got qualified.
5. **Re-export:** add each name in `FUNCS` to the `from services.orchestrated_scan import (...)` block in `backend/main.py` (the block currently ending at ~line 11524, the `_orchestrated_can_finalize_result, _orchestrated_result_is_final,` lines). Keep one name per line, trailing comma.
6. **Smoke import:** `python3 -c "import main"` — must exit 0 (catches qualification typos / circular issues immediately).
7. **Gate:** `python3 -m pytest -q` from `backend/` — must equal the Task 0 baseline, 0 failures.
8. **Commit** with the cluster message.

If step 6 or 7 fails: the offending cluster is small. Inspect, fix the specific `main.X`/bare mismatch (or `git checkout -- main.py services/orchestrated_scan.py` to revert just this cluster), and retry. **Never** advance to the next task with red tests.

---

### Task 1: Cluster A — cloud-tasks (4 leaf functions)

**Files:** Modify `backend/main.py`, `backend/services/orchestrated_scan.py`

`FUNCS = _orchestrated_cloud_tasks_configured _cloud_tasks_access_token _orchestrated_worker_task_url _enqueue_orchestrated_worker_task`

- [ ] **Step 1:** Cut the 4 functions (main.py anchors 7522, 7532, 7545, 7552) and paste into `services/orchestrated_scan.py`.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _orchestrated_cloud_tasks_configured _cloud_tasks_access_token _orchestrated_worker_task_url _enqueue_orchestrated_worker_task`
- [ ] **Step 3:** Review diff (expect `main.` on `CLOUD_TASKS_PROJECT/LOCATION/QUEUE`, `INTERNAL_WORKER_TOKEN`, `CLOUD_TASKS_*`, `SIGURSCAN_PUBLIC_API_BASE_URL`, `ORCHESTRATED_CLOUD_TASKS_ENABLED`, `logger`; `requests`/`time`/`json`/`base64` stay bare).
- [ ] **Step 4:** Add the 4 names to the re-export block in `main.py`.
- [ ] **Step 5:** `python3 -c "import main"` → exit 0.
- [ ] **Step 6:** `python3 -m pytest -q` → baseline, 0 failures.
- [ ] **Step 7:** Commit:
```bash
git add main.py services/orchestrated_scan.py
git commit -m "refactor(backend): move orchestrated cloud-tasks cluster into engine service

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

### Task 2: Cluster B — context-builders (3 functions)

`FUNCS = _invoice_auto_route_context _build_orchestrated_text_context _assemble_extracted_text_for_orchestration`

- [ ] **Step 1:** Cut (anchors 9083, 9110, 11160), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _invoice_auto_route_context _build_orchestrated_text_context _assemble_extracted_text_for_orchestration`
- [ ] **Step 3:** Review diff (expect `main.MAX_TEXT_CHARS`, `main._normalise_obfuscated_text`, `main.extract_urls`, `main._collect_form_context_from_html`, `main._infer_brand_hints_from_click_targets`, `main._extract_email_mime_parts`, `main._invoice_payment_destination_for_client`, `main._looks_like_structured_invoice_text`; intra-cluster calls become `main._invoice_auto_route_context`).
- [ ] **Step 4:** Add the 3 names to the re-export block.
- [ ] **Step 5:** `python3 -c "import main"` → 0.
- [ ] **Step 6:** `python3 -m pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated context-builder cluster into engine service`.

### Task 3: Cluster C — urlscan-submit (2 functions)

`FUNCS = _submit_orchestrated_urlscan_preview_once _submit_orchestrated_urlscan`

- [ ] **Step 1:** Cut (anchors 8902, 8870), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _submit_orchestrated_urlscan_preview_once _submit_orchestrated_urlscan`
- [ ] **Step 3:** Review diff (expect `main.submit_urlscan_sandbox`, `main._save_urlscan_preview_cache`, `main._urlscan_preview_cache_entry_from_job`, `main.prepare_external_url`, urlscan state helpers; `main._submit_orchestrated_urlscan_preview_once` for the intra-cluster call). Pay attention: any `URLSCAN_*_DEFAULT` used here is a main global → must become `main.URLSCAN_*_DEFAULT` (these are test-patched).
- [ ] **Step 4:** Add the 2 names to the re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated urlscan-submit cluster into engine service`.

### Task 4: Cluster D — finalize (1 function, behavior-critical)

`FUNCS = _finalize_orchestrated_job_if_ready`

- [ ] **Step 1:** Cut (anchor 8752), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _finalize_orchestrated_job_if_ready`
- [ ] **Step 3:** Review diff with extra care — this is verdict-bearing. Confirm `main.reduce_verdict`, `main._build_scan_response`, `main._apply_provider_gate_verdict`, `main._has_bad_provider_verdict`, `main._urlscan_result_ready_for_verdict`, `main._apply_decision_contract_result`, `main._build_orchestrated_pillars`, `main._orchestrated_can_finalize_result`, `main._emit_scan_event` all qualified; `reduce_verdict` must NOT appear inside any string/dict key.
- [ ] **Step 4:** Add the name to the re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline. **If any SAFE→UNVERIFIED appears, this single function is the cause — diff it against `git show HEAD:main.py` for the original body and find the missed/extra `main.` ref.**
- [ ] **Step 7:** Commit `move orchestrated finalize gate into engine service`.

### Task 5: Cluster E — exception-marker (1 function)

`FUNCS = _mark_orchestrated_job_exception`

- [ ] **Step 1:** Cut (anchor 10211), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _mark_orchestrated_job_exception`
- [ ] **Step 3:** Review diff.
- [ ] **Step 4:** Add to re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated exception-marker into engine service`.

### Task 6: Cluster F — create-job (1 function)

`FUNCS = _create_orchestrated_job`

- [ ] **Step 1:** Cut (anchor 9269), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _create_orchestrated_job`
- [ ] **Step 3:** Review diff (expect `main._new_scan_id`, `main._validate_text_input`, `main._build_orchestrated_text_context`, `main.ORCHESTRATED_JOB_TTL_SECONDS`, etc.).
- [ ] **Step 4:** Add to re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated create-job into engine service`.

### Task 7: Cluster G1 — text fast-lane (1 function, behavior-critical)

`FUNCS = _run_orchestrated_fast_lane`

- [ ] **Step 1:** Cut (anchor 9391), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _run_orchestrated_fast_lane`
- [ ] **Step 3:** Review diff with extra care. Confirm the test-patched helpers are qualified: `main._safe_scan_url_list`, `main._gather_external_intel_safe`, `main._enrich_offer_claim_verification_async`, `main.check_domain_ssl_parallel` (if referenced), `main.generate_fallback_explanation`. Confirm `main._finalize_orchestrated_job_if_ready`, `main._submit_orchestrated_urlscan`, `main.reduce_verdict`. This is the exact function family that regressed in batch 4 — the `_patch_clean_scan` fixture patches these on `app_main`, so a missed qualification here = SAFE→UNVERIFIED.
- [ ] **Step 4:** Add to re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated text fast-lane into engine service`.

### Task 8: Cluster G2 — invoice fast-lane (1 function, behavior-critical)

`FUNCS = _run_orchestrated_invoice_fast_lane`

- [ ] **Step 1:** Cut (anchor 9596), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _run_orchestrated_invoice_fast_lane`
- [ ] **Step 3:** Review diff (same scrutiny as G1; invoice path adds `main._attach_offer_claim_verification`, `main._skipped_offer_claim_payload`, `main._claim_verifier_required`).
- [ ] **Step 4:** Add to re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated invoice fast-lane into engine service`.

### Task 9: Cluster G3 — offer fast-lane (1 function, behavior-critical)

`FUNCS = _run_orchestrated_offer_fast_lane`

- [ ] **Step 1:** Cut (anchor 9948), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _run_orchestrated_offer_fast_lane`
- [ ] **Step 3:** Review diff (adds `main._run_offer_web_claim_enrichment`, `main._enrich_offer_claim_verification_async`).
- [ ] **Step 4:** Add to re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated offer fast-lane into engine service`.

### Task 10: Cluster H — refresh (2 functions, behavior-critical)

`FUNCS = _refresh_orchestrated_job_impl _refresh_orchestrated_job`

- [ ] **Step 1:** Cut (anchors 10320, 10313 — move `_impl` and its thin wrapper together), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _refresh_orchestrated_job_impl _refresh_orchestrated_job`
- [ ] **Step 3:** Review diff. The wrapper `_refresh_orchestrated_job` calls `_refresh_orchestrated_job_impl` → becomes `main._refresh_orchestrated_job_impl`. `_impl` references `main._finalize_orchestrated_job_if_ready`, `main._submit_orchestrated_urlscan`, `main._mark_orchestrated_job_exception`, `main._claim_distributed_orchestrated_refresh`, urlscan/pillar timeout helpers.
- [ ] **Step 4:** Add both names to the re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated refresh loop into engine service`.

### Task 11: Cluster I — compat / extraction starters (2 functions)

`FUNCS = _start_orchestrated_from_extraction _start_orchestrated_compat`

- [ ] **Step 1:** Cut (anchors 11182, 11215), paste into service.
- [ ] **Step 2:** `python3 tools/qualify_orchestrated.py _start_orchestrated_from_extraction _start_orchestrated_compat`
- [ ] **Step 3:** Review diff (expect `main._create_orchestrated_job`, `main._run_orchestrated_fast_lane` and siblings, `main._assemble_extracted_text_for_orchestration`).
- [ ] **Step 4:** Add both names to the re-export block.
- [ ] **Step 5–6:** `import main` → 0; `pytest -q` → baseline.
- [ ] **Step 7:** Commit `move orchestrated compat/extraction starters into engine service`.

---

### Task 12: Final verification & cleanup

**Files:** none (verification only)

- [ ] **Step 1: Confirm all 19 functions left main.py**

Run from `backend/`:
```bash
grep -nE "^(async )?def (_orchestrated_cloud_tasks_configured|_cloud_tasks_access_token|_orchestrated_worker_task_url|_enqueue_orchestrated_worker_task|_invoice_auto_route_context|_build_orchestrated_text_context|_assemble_extracted_text_for_orchestration|_submit_orchestrated_urlscan|_submit_orchestrated_urlscan_preview_once|_finalize_orchestrated_job_if_ready|_mark_orchestrated_job_exception|_create_orchestrated_job|_run_orchestrated_fast_lane|_run_orchestrated_invoice_fast_lane|_run_orchestrated_offer_fast_lane|_refresh_orchestrated_job_impl|_refresh_orchestrated_job|_start_orchestrated_from_extraction|_start_orchestrated_compat)\b" main.py
```
Expected: **no output** (all defs now live in the service; only the re-export names remain in main).

- [ ] **Step 2: Confirm the route handlers still resolve them**

```bash
grep -nE "_run_orchestrated_fast_lane|_refresh_orchestrated_job|_create_orchestrated_job|_start_orchestrated_compat" main.py | head
```
Expected: references inside route handlers + the re-export import block, all bare (resolved via the re-export).

- [ ] **Step 3: Full suite one more time**

```bash
python3 -m pytest -q 2>&1 | tail -3
```
Expected: baseline pass count, 0 failures.

- [ ] **Step 4: Report the line-count reduction**

```bash
git diff --stat HEAD~11 -- main.py services/orchestrated_scan.py
```
Record main.py shrinkage (~1800 lines moved). Do **not** push — per project policy this branch is reviewed by Codex before any merge to main.

---

## Self-Review notes (author)

- **Spec coverage:** all 19 in-scope functions are assigned to Tasks 1–11; route handlers and pillar helpers explicitly excluded.
- **No placeholders:** the qualifier is fully implemented and unit-tested in Task 0; every move task gives exact function names, the exact CLI invocation, the exact gate commands.
- **Type/name consistency:** the tool's public API (`qualify_source(source, main_globals, service_imports)`, `qualify_service_functions(names)`) is identical between Task 0's tests and Tasks 1–11's CLI usage.
- **Risk ordering:** leaf clusters (A–C) first to exercise the tool on low-risk code before the verdict-bearing finalize/fast-lane/refresh clusters (D, G, H); each behavior-critical function is its own task for minimal red-diff surface.
