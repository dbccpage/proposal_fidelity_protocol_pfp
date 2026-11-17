#!/usr/bin/env python3
"""
ast_cochain_obstruction_scanner.py
==================================

AST Simplicial Cochain Obstruction Scanner (19L57G1).

Scans Python packages and bounded contexts to evaluate:
  - 1-Skeleton Dependency Simplicial Complex (C_0, C_1)
  - Boundary Leakage Obstruction Norm (Phi_1)
  - Cycle Obstruction Norm (Gamma_2)
  - Clean Architecture Layer Inward Invariant Breaches
  - Circular Dependency Cycles

AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Optional

# Locate workspace root
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from adversary.stage.domain.cochain import (
        DEFAULT_CLEAN_ARCH_LAYERS,
        ASTDependencyComplex,
    )
except ImportError:
    print("[WARNING] Could not import adversary.stage.domain.cochain; check sys.path.")
    DEFAULT_CLEAN_ARCH_LAYERS = {
        "domain": 0,
        "use_cases": 1,
        "application": 1,
        "infrastructure": 2,
        "infra": 2,
        "controllers": 3,
        "frontend": 4,
        "cli": 4,
        "entrypoints": 4,
    }


def load_sources(pkg_path: Path) -> Dict[str, str]:
    """Recursively discover and load Python source files into a module dictionary."""
    sources: Dict[str, str] = {}
    if not pkg_path.exists():
        return sources

    for p in pkg_path.rglob("*.py"):
        if "__pycache__" in p.parts or "_tests" in p.parts or "tests" in p.parts:
            continue
        try:
            rel = p.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            rel = p.as_posix()
        mod_name = rel.replace("/", ".").removesuffix(".py")
        if mod_name.endswith(".__init__"):
            mod_name = mod_name.removesuffix(".__init__")
        try:
            sources[mod_name] = p.read_text(encoding="utf-8")
        except Exception:
            pass
    return sources


def get_clean_arch_layer(mod_name: str) -> int:
    """Classify module path into Clean Architecture layer index 0..4."""
    if ".domain." in mod_name or mod_name.endswith(".domain"):
        return 0
    if ".use_cases." in mod_name or mod_name.endswith(".use_cases") or ".application." in mod_name:
        return 1
    if (
        ".infrastructure." in mod_name
        or mod_name.endswith(".infrastructure")
        or ".infra." in mod_name
    ):
        return 2
    if ".controllers." in mod_name or mod_name.endswith(".controllers"):
        return 3
    if (
        ".frontend." in mod_name
        or mod_name.endswith(".frontend")
        or ".cli." in mod_name
        or ".entrypoints." in mod_name
    ):
        return 4
    return -1


def scan_package_obstructions(pkg_path: Path, pkg_name: Optional[str] = None) -> Dict:
    """Execute AST simplicial cochain obstruction evaluation over target path."""
    name = pkg_name or pkg_path.name
    sources = load_sources(pkg_path)

    complex_obj = ASTDependencyComplex()
    complex_obj._get_layer = get_clean_arch_layer
    complex_obj.build_complex(sources)

    # Filter defects to internal workspace dependencies
    internal_defects = [
        d
        for d in complex_obj.defects
        if d.target_module in sources or d.defect_type == "circular_import"
    ]

    phi_1 = 0.0
    gamma_2 = 0.0
    for d in internal_defects:
        if d.defect_type == "clean_arch_violation":
            phi_1 += 1.5 * d.weight
        elif d.defect_type == "circular_import":
            gamma_2 += 1.0 * d.weight
            phi_1 += 0.5 * d.weight
        else:
            phi_1 += 1.0 * d.weight

    layer_violations = [d for d in internal_defects if d.defect_type == "clean_arch_violation"]
    circular_imports = [d for d in internal_defects if d.defect_type == "circular_import"]

    return {
        "package_name": name,
        "target_path": str(pkg_path),
        "production_modules": len(sources),
        "nodes": complex_obj.graph.number_of_nodes(),
        "edges": complex_obj.graph.number_of_edges(),
        "phi_1": phi_1,
        "gamma_2": gamma_2,
        "is_exact": (phi_1 == 0.0 and gamma_2 == 0.0 and len(internal_defects) == 0),
        "is_closed": (gamma_2 == 0.0),
        "total_internal_defects": len(internal_defects),
        "layer_violations_count": len(layer_violations),
        "circular_imports_count": len(circular_imports),
        "defects": [
            {
                "type": d.defect_type,
                "source": d.source_module,
                "target": d.target_module,
                "description": d.description,
                "weight": d.weight,
            }
            for d in internal_defects
        ],
    }


def print_report(res: Dict) -> None:
    """Render human-readable CLI summary table."""
    print(f"\n{'=' * 70}")
    print(f"=== OEAOHS AST OBSTRUCTION REPORT: {res['package_name'].upper()} ===")
    print(f"{'=' * 70}")
    print(f"  Target Path:               {res['target_path']}")
    print(f"  Production Modules:        {res['production_modules']}")
    print(f"  1-Skeleton Nodes (C_0):    {res['nodes']}")
    print(f"  Dependency Edges (C_1):    {res['edges']}")
    print(f"  Boundary Leakage (Phi_1):  {res['phi_1']:.2f}")
    print(f"  Cycle Obstruction (Gamma_2): {res['gamma_2']:.2f}")
    print(f"  Is Exact (Phi_1=0, Gamma_2=0): {res['is_exact']}")
    print(f"  Is Closed (Gamma_2=0):         {res['is_closed']}")
    print(f"  Total Internal Defects:    {res['total_internal_defects']}")
    print(f"  Layer Violations:          {res['layer_violations_count']}")
    print(f"  Circular Cycles:           {res['circular_imports_count']}")

    if res["defects"]:
        print("\n  Active Non-Fit Obstructions:")
        for d in res["defects"]:
            print(f"    - [{d['type'].upper()}] {d['source']} -> {d['target']}")
            print(f"      Description: {d['description']}")
    print(f"{'=' * 70}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OEAOHS AST Simplicial Cochain Obstruction Scanner"
    )
    parser.add_argument(
        "targets",
        nargs="*",
        default=["pfp", "governance"],
        help="Target directories or packages to scan (relative to repo root)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON results")
    args = parser.parse_args()

    results = []
    for t in args.targets:
        target_path = REPO_ROOT / t if not Path(t).is_absolute() else Path(t)
        if not target_path.exists():
            print(f"[ERROR] Target path does not exist: {target_path}", file=sys.stderr)
            continue
        res = scan_package_obstructions(target_path, pkg_name=t)
        results.append(res)
        if not args.json:
            print_report(res)

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
