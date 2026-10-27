"""Architecture enforcement: AST import analysis of the OEEIS layers.

Imports are resolved to absolute module names, including relative imports
(`from ..infrastructure import x` has `node.level == 2`), which the previous
version of this test ignored. Checked:

- the domain imports no outer OEEIS layer, no framework, and no other bounded
  context;
- use cases import no OEEIS infrastructure, controllers or frontend, and no
  other bounded context's infrastructure, controllers, frontend or entrypoints;
- controllers import no infrastructure.

`entrypoints/` holds composition roots, the outermost layer, and may import any
layer. Exceptions are listed in `ALLOWED` with the reason for each.
"""

from __future__ import annotations

import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT.name
OUTER_LAYERS = ("use_cases", "infrastructure", "controllers", "frontend", "entrypoints")
FRAMEWORKS = ("fastapi", "pydantic", "sqlite3", "yaml", "requests", "httpx", "urllib")
FOREIGN_OUTER = ("infrastructure", "controllers", "frontend", "entrypoints")

_FARM_CODEC = (
    "the antimorphism-farm refusal receipt is written and verified with the Symbol "
    "Game demo-receipt codec; moving that use case's wiring to a composition root "
    "is an open item"
)
_NATIVE_DELEGATION = (
    "delegates exact consensus, admission, and guard activation to the sovereign native "
    "Rust host binary via infrastructure.native_domain adapter"
)
_YAML_LOADER = (
    "definitions_loader parses YAML text supplied by the caller"
)
ALLOWED: dict[tuple[str, str], str] = {
    (
        "use_cases/demos/antimorphism_farm/run.py",
        "pfp.infrastructure.demos.canonical",
    ): _FARM_CODEC,
    ("domain/definitions_loader.py", "yaml"): _YAML_LOADER,
    ("use_cases/antibody_admission.py", "eis.infrastructure.native_domain"): _NATIVE_DELEGATION,
    ("use_cases/guard_activation.py", "eis.infrastructure.native_domain"): _NATIVE_DELEGATION,
    ("use_cases/provisional_promotion.py", "eis.infrastructure.native_domain"): _NATIVE_DELEGATION,
}


def module_name(path: pathlib.Path) -> str:
    relative = path.relative_to(ROOT.parent).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def resolve_imports(source: str, module: str, is_package: bool) -> list[str]:
    """Absolute module names imported by `source`, resolving relative imports."""
    package_parts = module.split(".") if is_package else module.split(".")[:-1]
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package_parts[: len(package_parts) - (node.level - 1)]
                prefix = ".".join(base)
                target = f"{prefix}.{node.module}" if node.module else prefix
                if node.module is None:
                    found.extend(f"{prefix}.{alias.name}" for alias in node.names)
                else:
                    found.append(target)
            elif node.module:
                found.append(node.module)
    return found


def _imports(path: pathlib.Path) -> list[str]:
    return resolve_imports(
        path.read_text(encoding="utf-8"), module_name(path), path.name == "__init__.py"
    )


def _under(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(prefix + ".")


def _foreign_context(name: str) -> str | None:
    top = name.split(".")[0]
    if top.startswith("engine") and top != PACKAGE:
        return top
    return None


def _violations(layer: str, forbidden) -> list[tuple[str, str]]:
    found = []
    for path in sorted((ROOT / layer).rglob("*.py")):
        relative = path.relative_to(ROOT).as_posix()
        for name in _imports(path):
            if not forbidden(name):
                continue
            if any(key[0] == relative and _under(name, key[1]) for key in ALLOWED):
                continue
            found.append((relative, name))
    return found


class CleanArchitectureBoundaryTests(unittest.TestCase):
    def test_relative_imports_are_resolved(self) -> None:
        """Counterexample: the old extractor skipped `from ..infrastructure import x`."""
        source = "from ..infrastructure import mssn_ports\nfrom . import thymus\nfrom .x import y\n"
        names = resolve_imports(source, f"{PACKAGE}.domain.thymus", False)
        self.assertIn(f"{PACKAGE}.infrastructure", names)
        self.assertIn(f"{PACKAGE}.domain.thymus", names)
        self.assertIn(f"{PACKAGE}.domain.x", names)
        package_names = resolve_imports("from ..use_cases import screen\n", f"{PACKAGE}.domain", True)
        self.assertEqual(package_names, [f"{PACKAGE}.use_cases"])

    def test_domain_layer_never_imports_outer_layers_or_other_contexts(self) -> None:
        def forbidden(name: str) -> bool:
            return (
                any(_under(name, f"{PACKAGE}.{layer}") for layer in OUTER_LAYERS)
                or any(_under(name, framework) for framework in FRAMEWORKS)
                or _foreign_context(name) is not None
            )

        self.assertEqual(_violations("domain", forbidden), [])

    def test_use_cases_never_import_infrastructure(self) -> None:
        def forbidden(name: str) -> bool:
            if any(
                _under(name, f"{PACKAGE}.{layer}")
                for layer in ("infrastructure", "controllers", "frontend", "entrypoints")
            ):
                return True
            return _foreign_context(name) is not None and bool(
                set(name.split(".")[1:]) & set(FOREIGN_OUTER)
            )

        self.assertEqual(_violations("use_cases", forbidden), [])

    def test_the_demo_4e_use_case_imports_no_infrastructure_at_all(self) -> None:
        """Counterexample: the use case was the composition root and imported four
        infrastructure modules, each allowlisted."""
        path = ROOT / "use_cases" / "demos" / "demo_4e_cogsci_autopoiesis" / "run_packaged_immune.py"
        infrastructure = [name for name in _imports(path) if ".infrastructure" in name or "entrypoints" in name]
        self.assertEqual(infrastructure, [])
        self.assertFalse(any(key[0].startswith("use_cases/demos/demo_4e") for key in ALLOWED))

    def test_controllers_layer_never_imports_infrastructure(self) -> None:
        def forbidden(name: str) -> bool:
            return _under(name, f"{PACKAGE}.infrastructure") or _under(name, "sqlite3")

        self.assertEqual(_violations("controllers", forbidden), [])

    def test_every_allowlist_entry_is_still_needed(self) -> None:
        """An exception that no longer matches an import must be deleted."""
        used = set()
        for (relative, prefix) in ALLOWED:
            path = ROOT / relative
            if path.exists() and any(_under(name, prefix) for name in _imports(path)):
                used.add((relative, prefix))
        self.assertEqual(sorted(set(ALLOWED) - used), [])
