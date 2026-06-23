import pathlib
import ast

REPO_ROOT = pathlib.Path(__file__).resolve().parent


class _MainAttributeVisitor(ast.NodeVisitor):
    def __init__(self):
        self.main_aliases = {"main"}
        self.imported_main = False
        self.names = set()

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "main":
                self.imported_main = True
                self.main_aliases.add(alias.asname or alias.name)
            if alias.name.endswith(".main"):
                self.imported_main = True
                self.main_aliases.add(alias.asname or alias.name.split(".")[-1])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            if alias.name == "main":
                self.imported_main = True
                self.main_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        if (
            isinstance(node.value, ast.Name)
            and node.value.id in self.main_aliases
        ):
            if isinstance(node.ctx, (ast.Load, ast.Del, ast.Store)) and isinstance(node.attr, str):
                self.names.add(node.attr)
        self.generic_visit(node)


def _referenced_main_symbols():
    names = set()
    for py in REPO_ROOT.rglob("*.py"):
        if py.name in {"main.py", "test_main_surface_contract.py"}:
            continue
        text = py.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        visitor = _MainAttributeVisitor()
        visitor.visit(tree)
        if visitor.imported_main:
            names |= visitor.names
    return names


def test_main_exposes_all_referenced_symbols():
    import main

    missing = sorted(name for name in _referenced_main_symbols() if not hasattr(main, name))
    assert not missing, f"main.X rupt: {missing}"
