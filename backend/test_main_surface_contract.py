import ast
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parent
TARGET_ROOTS = [
    REPO_ROOT / "core",
    REPO_ROOT / "services",
    REPO_ROOT / "routers",
]


REQUIRED_CORE_ROUTES = {
    "/internal/orchestrated/{scan_id}/advance",
    "/v1/scan/orchestrated",
    "/v1/scan/orchestrated/{scan_id}",
    "/v1/scan/orchestrated/{scan_id}/status",
    "/v1/sandbox/urlscan",
    "/v1/sandbox/urlscan/{uuid}",
    "/v1/sandbox/urlscan/{uuid}/screenshot",
    "/v1/extract/image",
    "/v1/extract/pdf",
    "/v1/extract/email",
    "/v1/scan/text",
    "/v1/scan/url",
    "/v1/scan/email",
    "/v1/scan/image",
    "/v1/scan/pdf",
    "/v1/scan/invoice",
}


class _ImportMainVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imported_main = False

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "main":
                self.imported_main = True
                return
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module == "main" or (node.module and node.module.endswith(".main")):
            self.imported_main = True
            return
        self.generic_visit(node)


def _source_without_tests(root: pathlib.Path):
    for py in root.rglob("*.py"):
        if py.name.startswith("test_"):
            continue
        yield py


def _modules_with_main_import():
    offenders = []
    for root in TARGET_ROOTS:
        if not root.exists():
            continue
        for py in _source_without_tests(root):
            try:
                tree = ast.parse(py.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            visitor = _ImportMainVisitor()
            visitor.visit(tree)
            if visitor.imported_main:
                offenders.append(str(py.relative_to(REPO_ROOT)))
    return sorted(offenders)


def test_runtime_layers_do_not_import_main_module():
    offenders = _modules_with_main_import()
    assert not offenders, f"Import de main rămas în core/services/routers: {offenders}"


def test_required_scan_routes_are_registered():
    from app import app

    actual = {route.path for route in app.routes if hasattr(route, "path")}
    missing = sorted(REQUIRED_CORE_ROUTES - actual)
    assert not missing, f"Rute obligatorii lipsă: {missing}"
