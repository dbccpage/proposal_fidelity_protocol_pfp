"""Architecture enforcement: AST import analysis verifying strict Clean Architecture boundaries.

Relative imports are resolved to absolute module names before any rule is
applied. The previous extractor read only ``node.module`` and ignored
``node.level``, so ``from ..infrastructure import x`` inside ``domain/`` was
recorded as ``infrastructure`` (or, for ``from .. import infrastructure``, not at
all) and could never match a forbidden prefix such as
``omega_engine_operads.infrastructure``. Every layer rule was
therefore blind to the import style the package itself uses most.
"""

import ast
import pathlib
import unittest
from typing import Iterable, List, Sequence, Tuple

ROOT = pathlib.Path(__file__).resolve().parents[2]
PACKAGE = ROOT.name
REPO_ROOT = ROOT.parent

# Bounded contexts the domain layer must never import. The four named here are
# asserted to be present in the discovered set, so an on-disk discovery that
# found nothing cannot turn the rule into a vacuous pass.
NAMED_OTHER_CONTEXTS = (
    "omega_engine_epistemic_immune_system",
    "omega_engine_pfp",
    "omega_engine_woland",
)


def _discover_other_contexts() -> Tuple[str, ...]:
    """Every sibling ``omega_engine_*`` package on disk, plus the named four."""
    found = {
        child.name
        for child in REPO_ROOT.iterdir()
        if child.is_dir()
        and child.name.startswith("omega_engine_")
        and child.name != PACKAGE
    }
    return tuple(sorted(found | set(NAMED_OTHER_CONTEXTS)))


def _module_name(file_path: pathlib.Path) -> Tuple[str, bool]:
    """Dotted module name of a file under the repository root, and whether it is a package."""
    parts = list(file_path.resolve().relative_to(REPO_ROOT).with_suffix("").parts)
    is_package = parts[-1] == "__init__"
    if is_package:
        parts = parts[:-1]
    return ".".join(parts), is_package


def extract_imports_from_source(source: str, module_name: str, is_package: bool) -> List[str]:
    """Absolute names of every module a source text imports.

    ``from X import a`` records both ``X`` and ``X.a``: ``a`` may be a
    submodule (``from .. import infrastructure``) and recording it costs
    nothing when it is merely an attribute, because a forbidden prefix that
    matches ``X.a`` but not ``X`` must name ``a`` itself.
    """
    package_parts = module_name.split(".") if is_package else module_name.split(".")[:-1]
    tree = ast.parse(source)
    imports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                ascend = node.level - 1
                if ascend > len(package_parts) - 1:
                    raise ValueError(
                        f"{module_name}: relative import of level {node.level} "
                        f"climbs above the top-level package"
                    )
                base = package_parts[: len(package_parts) - ascend]
                target = ".".join(base + ([node.module] if node.module else []))
            else:
                target = node.module or ""
            if target:
                imports.append(target)
            for alias in node.names:
                if alias.name != "*":
                    imports.append(f"{target}.{alias.name}" if target else alias.name)
    return imports


def _matches(imported: str, prefix: str) -> bool:
    return imported == prefix or imported.startswith(prefix + ".")


def _violations(
    file_label: str, imports: Iterable[str], forbidden: Sequence[str]
) -> List[Tuple[str, str]]:
    found = []
    for imported in imports:
        for prefix in forbidden:
            if _matches(imported, prefix):
                found.append((file_label, imported))
                break
    return found


def _foreign_infrastructure(imported: str) -> bool:
    """Whether a module is another bounded context's infrastructure layer."""
    parts = imported.split(".")
    return (
        parts[0].startswith("omega_engine")
        and parts[0] != PACKAGE
        and "infrastructure" in parts[1:]
    )


class CleanArchitectureBoundaryTests(unittest.TestCase):
    def _extract_imports(self, file_path: pathlib.Path) -> List[str]:
        module_name, is_package = _module_name(file_path)
        return extract_imports_from_source(
            file_path.read_text(encoding="utf-8"), module_name, is_package
        )

    def _layer_files(self, layer: str) -> List[pathlib.Path]:
        files = sorted((ROOT / layer).rglob("*.py"))
        self.assertTrue(files, f"no Python files under {layer}/; the rule would be vacuous")
        return files

    def test_domain_layer_never_imports_outer_layers(self) -> None:
        forbidden = [
            f"{PACKAGE}.application",
            f"{PACKAGE}.infrastructure",
            f"{PACKAGE}.controllers",
            f"{PACKAGE}.frontend",
            "fastapi",
            "pydantic",
            "sqlite3",
            "yaml",
            "pathlib",
        ]
        violations = []
        for p in self._layer_files("domain"):
            violations += _violations(
                p.relative_to(ROOT).as_posix(), self._extract_imports(p), forbidden
            )
        self.assertEqual(violations, [], f"Domain layer violations: {violations}")

    def test_application_layer_never_imports_infrastructure_or_controllers(self) -> None:
        forbidden = [
            f"{PACKAGE}.infrastructure",
            f"{PACKAGE}.controllers",
            f"{PACKAGE}.frontend",
            "fastapi",
            "sqlite3",
            "pydantic",
        ]
        violations = []
        for p in self._layer_files("application"):
            violations += _violations(
                p.relative_to(ROOT).as_posix(), self._extract_imports(p), forbidden
            )
        self.assertEqual(violations, [], f"Application layer violations: {violations}")

    def test_controllers_layer_never_imports_infrastructure_adapters(self) -> None:
        forbidden = [
            f"{PACKAGE}.infrastructure.storage",
            f"{PACKAGE}.infrastructure.parser",
            f"{PACKAGE}.infrastructure.fs",
            f"{PACKAGE}.infrastructure.operad",
            "sqlite3",
        ]
        violations = []
        for p in self._layer_files("controllers"):
            violations += _violations(
                p.relative_to(ROOT).as_posix(), self._extract_imports(p), forbidden
            )
        self.assertEqual(violations, [], f"Controllers layer violations: {violations}")

    # -- cross-bounded-context rules -------------------------------------

    def test_domain_layer_imports_no_other_bounded_context(self) -> None:
        """The OEWAS domain reaches other contexts only through application ports.

        No allowlist: a domain module importing another context's domain is the
        coupling this rule exists to remove, not an exception to it.
        """
        others = _discover_other_contexts()
        for named in NAMED_OTHER_CONTEXTS:
            self.assertIn(named, others)
        violations = []
        for p in self._layer_files("domain"):
            violations += _violations(
                p.relative_to(ROOT).as_posix(), self._extract_imports(p), others
            )
        self.assertEqual(
            violations, [], f"Domain layer imports other bounded contexts: {violations}"
        )

    def test_application_layer_imports_no_other_context_infrastructure(self) -> None:
        violations = []
        for p in self._layer_files("application"):
            for imported in self._extract_imports(p):
                if _foreign_infrastructure(imported):
                    violations.append((p.relative_to(ROOT).as_posix(), imported))
        self.assertEqual(
            violations,
            [],
            f"Application layer imports another context's infrastructure: {violations}",
        )

    # -- self-tests: the extractor must see what the rules check ---------

    def test_a_relative_outer_layer_import_in_domain_is_caught(self) -> None:
        """``from ..infrastructure import storage`` inside ``domain/`` is a violation.

        The old extractor recorded ``infrastructure`` (no package prefix), which
        matched no forbidden entry, so the rule passed.
        """
        module = f"{PACKAGE}.domain.example"
        imports = extract_imports_from_source(
            "from ..infrastructure import storage\n", module, is_package=False
        )
        self.assertIn(f"{PACKAGE}.infrastructure", imports)
        self.assertIn(f"{PACKAGE}.infrastructure.storage", imports)
        self.assertTrue(
            _violations("example.py", imports, [f"{PACKAGE}.infrastructure"])
        )

    def test_a_bare_relative_package_import_is_caught(self) -> None:
        """``from ... import infrastructure`` has no module; it was invisible before."""
        module = f"{PACKAGE}.domain.operad"
        imports = extract_imports_from_source(
            "from ... import infrastructure\n", module, is_package=True
        )
        self.assertEqual(imports, [PACKAGE, f"{PACKAGE}.infrastructure"])
        self.assertTrue(
            _violations("__init__.py", imports, [f"{PACKAGE}.infrastructure"])
        )

    def test_a_same_layer_relative_import_is_not_a_violation(self) -> None:
        module = f"{PACKAGE}.domain.operad.planar"
        imports = extract_imports_from_source(
            "from .errors import Err\nfrom ..value_objects import ContentDigest\n",
            module,
            is_package=False,
        )
        self.assertIn(f"{PACKAGE}.domain.operad.errors", imports)
        self.assertIn(f"{PACKAGE}.domain.value_objects", imports)
        forbidden = [f"{PACKAGE}.application", f"{PACKAGE}.infrastructure"]
        self.assertEqual(_violations("planar.py", imports, forbidden), [])

    def test_a_relative_import_above_the_top_level_package_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            extract_imports_from_source(
                "from .... import x\n", f"{PACKAGE}.domain.example", is_package=False
            )

    def test_cross_context_imports_are_caught_in_source(self) -> None:
        domain_imports = extract_imports_from_source(
            "from omega_engine_woland.domain import models\n",
            f"{PACKAGE}.domain.example",
            is_package=False,
        )
        self.assertTrue(
            _violations("example.py", domain_imports, _discover_other_contexts())
        )
        app_imports = extract_imports_from_source(
            "import omega_engine_pfp.infrastructure.adapters.x\n",
            f"{PACKAGE}.application.example",
            is_package=False,
        )
        self.assertTrue(any(_foreign_infrastructure(i) for i in app_imports))
        own = extract_imports_from_source(
            "from ..ports import clock_port\n",
            f"{PACKAGE}.application.commands.example",
            is_package=False,
        )
        self.assertFalse(any(_foreign_infrastructure(i) for i in own))
