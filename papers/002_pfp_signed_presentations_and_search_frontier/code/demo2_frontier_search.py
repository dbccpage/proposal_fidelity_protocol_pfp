#!/usr/bin/env python3
"""Demo 2: Bounded Frontier Search & Receipt Replay Chain.

Demonstrates resumable batch search, deterministic candidate indexing,
gauge frontier tracking, and SHA-256 receipt replay.
"""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

_code_dir = Path(__file__).resolve().parent
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

if __package__:
    from .genesis_alpha.frontier_search import (
        CHECKER_VERSION,
        DIAGONAL_Z2_GRAMMAR,
        GaugeFrontier,
        PresentationKey,
        SearchReceipt,
        graph_digest,
        search_sign_graph,
        verify_search_receipt,
    )
    from .genesis_alpha.sign_graph import SignedRewrite
else:
    from genesis_alpha.frontier_search import (
        CHECKER_VERSION,
        DIAGONAL_Z2_GRAMMAR,
        GaugeFrontier,
        PresentationKey,
        SearchReceipt,
        graph_digest,
        search_sign_graph,
        verify_search_receipt,
    )
    from genesis_alpha.sign_graph import SignedRewrite


def make_sample_key(hamiltonian_digest: str, adapter_digest: str) -> PresentationKey:
    return PresentationKey(
        hamiltonian_digest=hamiltonian_digest,
        basis="computational-z",
        ensemble="canonical",
        filling="half-filled",
        boundary="periodic",
        representation="site-fermion",
        estimator="exact-diagonalization",
        observables=("energy", "parity"),
        beta="1/4",
        parameters=(("U", "2"), ("t", "1")),
        transformation_grammar=DIAGONAL_Z2_GRAMMAR,
        adapter_digest=adapter_digest,
        checker_version=CHECKER_VERSION,
    )


def run_demo():
    print("=" * 72)
    print("DEMO 2: BOUNDED FRONTIER SEARCH & RECEIPT REPLAY CHAIN")
    print("=" * 72)

    # 4-vertex gaugeable graph: 2^4 = 16 candidate gauges (indices 0..15)
    vertices = ("v0", "v1", "v2", "v3")
    edges = (
        SignedRewrite("v0", "v1", 1),
        SignedRewrite("v1", "v2", 0),
        SignedRewrite("v2", "v3", 1),
        SignedRewrite("v0", "v3", 0),
    )
    g_dig = graph_digest(vertices, edges)
    h_dig = sha256(b"hamiltonian-4-site").hexdigest()
    a_dig = sha256(b"adapter-v1").hexdigest()
    key = make_sample_key(h_dig, a_dig)

    print(f"Graph Digest: {g_dig[:16]}...")
    print(f"Presentation Key Digest: {key.digest()[:16]}...")
    print(f"Total Candidate Search Space: 2^{len(vertices)} = {1 << len(vertices)} configurations")
    print()

    # Step 1: Execute partial search with budget=4 (checks indices 0..3)
    print("[*] Step 1: Launching initial search with node_budget = 4...")
    receipt_1 = search_sign_graph(
        vertices=vertices,
        edges=edges,
        key=key,
        node_budget=4,
        workers=2,
    )
    print(f"  Receipt 1 Status: {receipt_1.status}")
    print(f"  Checked Suffix Range: [{receipt_1.start_index}, {receipt_1.frontier.next_index})")
    print(f"  Next Frontier Index: {receipt_1.frontier.next_index} / {receipt_1.frontier.stop_index}")
    print(f"  Receipt SHA256: {receipt_1.receipt_sha256[:16]}...")
    if receipt_1.status != "UNKNOWN":
        print(f"[X] Receipt 1 expected UNKNOWN, got {receipt_1.status}")
        return False
    if not verify_search_receipt(vertices, edges, key, receipt_1):
        print("[X] Receipt 1 verification failed!")
        return False
    print("  Independent Verification: PASS (Receipt 1 verified)")
    print()

    # Step 2: Resume search from Step 1 frontier with budget=4 (checks indices 4..7)
    print(f"[*] Step 2: Resuming search from index {receipt_1.frontier.next_index} with node_budget = 4...")
    receipt_2 = search_sign_graph(
        vertices=vertices,
        edges=edges,
        key=key,
        node_budget=4,
        workers=2,
        frontier=receipt_1.frontier,
        prior_receipts=[receipt_1],
    )
    print(f"  Receipt 2 Status: {receipt_2.status}")
    print(f"  Checked Range: [{receipt_2.start_index}, {receipt_2.frontier.next_index})")
    print(f"  Next Frontier Index: {receipt_2.frontier.next_index} / {receipt_2.frontier.stop_index}")
    print(f"  Witness Discovered: {receipt_2.witness}")
    print(f"  Receipt SHA256: {receipt_2.receipt_sha256[:16]}...")
    if receipt_2.status != "GAUGE_VERIFIED":
        print(f"[X] Receipt 2 expected GAUGE_VERIFIED, got {receipt_2.status}")
        return False
    if not verify_search_receipt(vertices, edges, key, receipt_2, prior_receipts=[receipt_1]):
        print("[X] Replay chain verification failed for Receipt 2!")
        return False
    print("  Independent Replay Chain Verification: PASS (Chain [Receipt 1 -> Receipt 2] verified)")
    print()

    # Step 3: Invariant Guard - Resuming after terminal GAUGE_VERIFIED receipt is refused
    print("[*] Step 3: Invariant Guard - Attempting continuation past terminal receipt...")
    try:
        search_sign_graph(
            vertices=vertices,
            edges=edges,
            key=key,
            node_budget=4,
            frontier=receipt_2.frontier,
            prior_receipts=[receipt_1, receipt_2],
        )
        print("  FAIL: Expected refusal!")
        return False
    except ValueError as e:
        print(f"  Correctly Refused: {e}")
    print()

    # Step 4: Odd-Cycle Exhaustive Frontier Search (Walks UNKNOWN chain until RESTRICTED_OBSTRUCTION)
    print("--- Part B: Frustrated Graph Exhaustive Multi-Segment Search ---")
    tri_vertices = ("w0", "w1", "w2")  # 2^3 = 8 configurations
    tri_edges = (
        SignedRewrite("w0", "w1", 1),
        SignedRewrite("w1", "w2", 0),
        SignedRewrite("w2", "w0", 0),
    )
    tri_key = make_sample_key(sha256(b"h-triangle").hexdigest(), a_dig)

    # Segment A: check first 4 (budget=4)
    print("[*] Segment A: Checking indices 0..3 (budget=4)...")
    r_a = search_sign_graph(tri_vertices, tri_edges, tri_key, node_budget=4, workers=2)
    if r_a.status != "UNKNOWN":
        print(f"[X] Segment A expected UNKNOWN, got {r_a.status}")
        return False
    print(f"  Segment A Status: {r_a.status} (frontier at {r_a.frontier.next_index})")

    # Segment B: check remaining 4 (budget=4), exhausts space -> seals RESTRICTED_OBSTRUCTION
    print(f"[*] Segment B: Resuming from index {r_a.frontier.next_index} with budget=4...")
    r_b = search_sign_graph(
        tri_vertices,
        tri_edges,
        tri_key,
        node_budget=4,
        workers=2,
        frontier=r_a.frontier,
        prior_receipts=[r_a],
    )
    print(f"  Segment B Final Status: {r_b.status}")
    print(f"  Obstruction Witness: {type(r_b.witness).__name__}")
    print(f"  Receipt SHA256: {r_b.receipt_sha256[:16]}...")
    if r_b.status != "RESTRICTED_OBSTRUCTION":
        print(f"[X] Segment B expected RESTRICTED_OBSTRUCTION, got {r_b.status}")
        return False
    if not verify_search_receipt(tri_vertices, tri_edges, tri_key, r_b, prior_receipts=[r_a]):
        print("[X] Multi-receipt replay verification failed!")
        return False
    print("  Complete Multi-Receipt Replay: PASS (every recorded check replayed)")
    print()

    # Step 5: Negative Control - Tampered Receipt Rejection
    print("[*] Step 5: Negative Control - Testing Replay Security on Tampered Receipt...")
    tampered_receipt = SearchReceipt(
        status="UNKNOWN",
        presentation_digest=receipt_1.presentation_digest,
        graph_digest=receipt_1.graph_digest,
        start_index=0,
        node_budget=4,
        checks=receipt_1.checks,
        frontier=GaugeFrontier(receipt_1.frontier.graph_digest, 5, 16),
        witness=None,
        complete_oracle_used=False,
        receipt_sha256=receipt_1.receipt_sha256,
    )
    is_tampered_valid = verify_search_receipt(vertices, edges, key, tampered_receipt)
    print(f"  Tampered Receipt Replay Accepted: {is_tampered_valid} (Correctly Rejected: {not is_tampered_valid})")
    if is_tampered_valid:
        print("[X] Security failure: Tampered receipt was accepted!")
        return False

    print()
    print("[+] Demo 2 Completed Successfully.")
    return True


if __name__ == "__main__":
    run_demo()
