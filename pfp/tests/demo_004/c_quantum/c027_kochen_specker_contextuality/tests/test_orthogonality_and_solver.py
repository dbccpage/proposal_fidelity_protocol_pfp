# AuthorityEffect: None.
"""Tests for orthogonality graph, context enumeration, and contextuality solver in C027."""

from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.orthogonality import (
    compute_orthogonality_graph,
    enumerate_contexts,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.quad_field import (
    QuadRat,
)
from omega_engine_projects.mssn_sn_symgam.challenges.c_quantum.c027_kochen_specker_contextuality.reference_solver.solver import (
    solve,
)


def test_standard_basis_orthogonality_dim4():
    # 4 standard basis vectors in dim 4: form 1 complete context
    rays = [
        [QuadRat.one(), QuadRat.zero(), QuadRat.zero(), QuadRat.zero()],
        [QuadRat.zero(), QuadRat.one(), QuadRat.zero(), QuadRat.zero()],
        [QuadRat.zero(), QuadRat.zero(), QuadRat.one(), QuadRat.zero()],
        [QuadRat.zero(), QuadRat.zero(), QuadRat.zero(), QuadRat.one()],
    ]
    adj, edges = compute_orthogonality_graph(rays)
    assert len(edges) == 6  # Complete K_4 graph
    contexts = enumerate_contexts(4, rays, adj)
    assert len(contexts) == 1
    assert contexts[0] == [0, 1, 2, 3]


def test_cabello_18_parity_uncolourability():
    cabello_raw = [
        [1, 1, 1, 1],
        [1, 1, 1, -1],
        [1, 1, 0, 0],
        [1, 1, -1, -1],
        [1, 0, 1, 0],
        [1, 0, 0, 1],
        [1, 0, 0, -1],
        [1, 0, -1, 0],
        [1, -1, 1, 1],
        [1, -1, 0, 0],
        [1, -1, -1, 1],
        [1, -1, -1, -1],
        [0, 1, 0, 1],
        [0, 1, 0, 0],
        [0, 1, -1, 0],
        [0, 0, 1, 0],
        [0, 0, 1, -1],
        [0, 0, 0, 1],
    ]
    wire = [[[str(c), "0"] for c in v] for v in cabello_raw]
    case = {"case_id": "test_cabello_18", "dimension": 4, "vectors": wire}

    ans = solve(case)
    assert ans["status"] == "SOLVED"
    assert ans["colourable"] is False
    assert ans["certificate"]["kind"] == "parity"
    assert len(ans["certificate"]["contexts"]) == 9
