#!/usr/bin/env python3
"""Demo 1: Signed Graph & Matrix Gauge Certification.

Demonstrates exact $\\mathbb{Z}_2$ diagonal sign-gauge classification and odd-cycle
obstruction detection on both explicit rewrite graphs and symmetric matrices.
"""

from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

_code_dir = Path(__file__).resolve().parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

if __package__:
    from .genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        matrix_sign_graph,
    )
    from .native_sign_graph import (
        classify_matrix_sign_gauge,
        classify_sign_graph,
        find_binary,
        verify_gauge,
        verify_odd_cycle,
    )
else:
    from genesis_alpha.sign_graph import (
        GaugeWitness,
        OddCycleWitness,
        SignedRewrite,
        matrix_sign_graph,
    )
    from native_sign_graph import (
        classify_matrix_sign_gauge,
        classify_sign_graph,
        find_binary,
        verify_gauge,
        verify_odd_cycle,
    )


def run_demo():
    print("=" * 72)
    print("DEMO 1: SIGNED PRESENTATIONS & EXACT GAUGE CERTIFICATION")
    print("=" * 72)

    bin_path = find_binary()
    print(f"[*] Native Rust Binary: {bin_path if bin_path else 'Not found (using Python fallback)'}")
    print()

    # Case A: Gaugeable Stoquastic Presentation (Tree / Bipartite-like sign pattern)
    print("--- Case A: Gaugeable Presentation (Frustration-Free) ---")
    vertices_a = ("v0", "v1", "v2", "v3")
    edges_a = (
        SignedRewrite("v0", "v1", 1),
        SignedRewrite("v1", "v2", 0),
        SignedRewrite("v2", "v3", 1),
        SignedRewrite("v0", "v3", 0),
    )
    print(f"Vertices: {vertices_a}")
    print(f"Edges: {[(e.source, e.target, 'odd' if e.odd else 'even') for e in edges_a]}")

    witness_a = classify_sign_graph(vertices_a, edges_a)
    print(f"Solver Result: {type(witness_a).__name__}")
    if not isinstance(witness_a, GaugeWitness):
        print(f"[X] Case A expected GaugeWitness, got {type(witness_a).__name__}")
        return False
    print(f"  Gauge Bits: {witness_a.bits}")
    is_valid = verify_gauge(vertices_a, edges_a, witness_a)
    print(f"  Independent Verification: {'PASS (Gauge Validated)' if is_valid else 'FAIL'}")
    if not is_valid:
        print("[X] Case A independent verification failed!")
        return False
    print()

    # Case B: Frustrated Presentation (Odd Cycle Obstruction)
    print("--- Case B: Frustrated Presentation (Odd-Cycle Obstruction) ---")
    vertices_b = ("u0", "u1", "u2")
    edges_b = (
        SignedRewrite("u0", "u1", 1),
        SignedRewrite("u1", "u2", 0),
        SignedRewrite("u2", "u0", 0),
    )
    print(f"Vertices: {vertices_b}")
    print(f"Edges: {[(e.source, e.target, 'odd' if e.odd else 'even') for e in edges_b]}")

    witness_b = classify_sign_graph(vertices_b, edges_b)
    print(f"Solver Result: {type(witness_b).__name__}")
    if not isinstance(witness_b, OddCycleWitness):
        print(f"[X] Case B expected OddCycleWitness, got {type(witness_b).__name__}")
        return False
    print("  Obstruction Cycle Steps:")
    for step in witness_b.steps:
        e_idx, dep, arr = step
        parity = edges_b[e_idx].odd
        print(f"    Edge {e_idx}: {dep} -> {arr} (parity={parity})")
    is_valid = verify_odd_cycle(vertices_b, edges_b, witness_b)
    print(f"  Independent Verification: {'PASS (Odd Cycle Validated)' if is_valid else 'FAIL'}")
    if not is_valid:
        print("[X] Case B independent verification failed!")
        return False
    print()

    # Case C: Matrix Sign Gauge
    print("--- Case C: Exact Rational Matrix Sign-Gauge ---")
    matrix = [
        [Fraction(0), Fraction(1, 2), Fraction(-1, 3)],
        [Fraction(1, 2), Fraction(0), Fraction(1, 4)],
        [Fraction(-1, 3), Fraction(1, 4), Fraction(0)],
    ]
    print("Matrix M:")
    for row in matrix:
        print("  [" + ", ".join(f"{str(x):>6}" for x in row) + " ]")

    vs, es = matrix_sign_graph(matrix)
    print(f"Derived Graph: {len(vs)} vertices, {len(es)} edges")
    mat_witness = classify_matrix_sign_gauge(matrix)
    print(f"Matrix Classification: {type(mat_witness).__name__}")
    if not isinstance(mat_witness, GaugeWitness):
        print(f"[X] Case C expected GaugeWitness, got {type(mat_witness).__name__}")
        return False
    print(f"  Gauge Bits: {mat_witness.bits}")
    is_valid_mat = verify_gauge(vs, es, mat_witness)
    if not is_valid_mat:
        print("  Independent Verification: FAIL (Gauge verification failed)")
        return False
    print("  Independent Verification: PASS (Diagonal Transformation Eliminates Positive Off-Diagonals)")

    print()
    print("[+] Demo 1 Completed Successfully.")
    return True


if __name__ == "__main__":
    run_demo()
