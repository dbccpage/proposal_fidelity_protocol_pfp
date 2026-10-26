#!/usr/bin/env python3
"""Domain packages must not import an outer layer from bounded_contexts.yaml.

AuthorityEffect: None.

An import resolves to path segments. A segment is an outer layer only when it
equals a name in outer_layers and it is not inside the file's domain package.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

IGNORE_PARTS = frozenset({".git", "target", ".venv", "build", "dist", "_archive", "__pycache__"})
MANIFEST = Path(__file__).resolve().parent.parent / "bounded_contexts.yaml"


def load_manifest(path: Path) -> dict:
    import yaml

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest must be a mapping")
    layers = data.get("outer_layers")
    if (
        not isinstance(layers, list)
        or not layers
        or not all(isinstance(item, str) and item for item in layers)
    ):
        raise ValueError("outer_layers must be a non-empty list of strings")
    if len(set(layers)) != len(layers):
        raise ValueError("outer_layers contains a duplicate")
    contexts = data.get("bounded_contexts")
    if not isinstance(contexts, list) or not contexts:
        raise ValueError("bounded_contexts must be a non-empty list")
    seen: set[str] = set()
    for item in contexts:
        if not isinstance(item, dict):
            raise ValueError("context entry must be a mapping")
        root = item.get("canonical_root")
        if not isinstance(root, str) or not root or root in seen:
            raise ValueError(f"canonical_root invalid or duplicated: {root!r}")
        seen.add(root)
        if not isinstance(item.get("single_root_enforced"), bool):
            raise ValueError(f"single_root_enforced must be bool for {root}")
    return data


def outer_layer_outside_domain(segments: tuple[str, ...], outer_layers: frozenset[str]) -> str | None:
    """Return the outer-layer segment that is not inside a domain package."""
    domain_at = next((index for index, segment in enumerate(segments) if segment == "domain"), None)
    for index, segment in enumerate(segments):
        if segment in outer_layers and (domain_at is None or index < domain_at):
            return segment
    return None


def import_targets(file: Path, node: ast.AST) -> list[tuple[str, ...]]:
    parent = file.parent.parts
    if isinstance(node, ast.Import):
        return [tuple(alias.name.split(".")) for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level:
        drop = node.level - 1
        if drop > len(parent):
            return [()]
        base = parent[: len(parent) - drop]
        if node.module:
            return [tuple(base) + tuple(node.module.split("."))]
        return [tuple(base) + (alias.name,) for alias in node.names]
    if node.module:
        return [tuple(node.module.split("."))]
    return [()]


def check_pure_domain_sink(repo_root: Path, outer_layers: frozenset[str]) -> list[str]:
    violations: list[str] = []
    domain_files = [
        file
        for file in repo_root.glob("**/domain/**/*.py")
        if not any(part in IGNORE_PARTS for part in file.parts)
    ]
    for file in domain_files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(f"{file}: unreadable domain module: {exc}")
            continue
        relative = file.relative_to(repo_root) if repo_root in file.parents else file
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for segments in import_targets(file, node):
                if not segments:
                    violations.append(f"{relative}:{getattr(node, 'lineno', 0)} - relative import escapes the file path")
                    continue
                hit = outer_layer_outside_domain(segments, outer_layers)
                if hit is not None:
                    violations.append(
                        f"{relative}:{node.lineno} - domain imports outer layer {hit}"
                    )
    return violations


def self_check(outer: frozenset[str]) -> None:
    if not {"use_cases", "infrastructure"} <= outer:
        raise AssertionError("resolver cases use use_cases and infrastructure")
    domain_file = Path("pkg/domain/a.py")
    nested = Path("pkg/domain/bridge/a.py")
    cases = [
        (domain_file, ast.parse("from ..infrastructure import X").body[0], "infrastructure"),
        (nested, ast.parse("from ..models import X").body[0], None),
        (domain_file, ast.parse("from .use_cases_port import X").body[0], None),
        (domain_file, ast.parse("import pkg.infrastructure.foo").body[0], "infrastructure"),
        (nested, ast.parse("from ...use_cases import X").body[0], "use_cases"),
        (domain_file, ast.parse("from .. import use_cases").body[0], "use_cases"),
        (nested, ast.parse("from .infrastructure_port import X").body[0], None),
    ]
    for file, node, expected in cases:
        hits = [
            outer_layer_outside_domain(segments, outer)
            for segments in import_targets(file, node)
            if segments
        ]
        found = next((hit for hit in hits if hit), None)
        if found != expected:
            raise AssertionError(f"{ast.dump(node)} on {file}: expected {expected}, found {found}")


def main() -> int:
    try:
        manifest = load_manifest(MANIFEST)
        self_check(frozenset(manifest["outer_layers"]))
    except (OSError, UnicodeError, ValueError, AssertionError, ImportError) as exc:
        print(f"[FAIL] {exc}", file=sys.stderr)
        return 1
    outer_layers = frozenset(manifest["outer_layers"])
    violations = check_pure_domain_sink(Path.cwd(), outer_layers)
    if violations:
        print(
            f"Clean Architecture inward dependency violations found ({len(violations)}):",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"  [FAIL] {violation}", file=sys.stderr)
        return 1
    print("PASS: domain packages do not import outer layers.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
