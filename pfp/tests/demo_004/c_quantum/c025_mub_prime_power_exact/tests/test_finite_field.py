# AuthorityEffect: None.
"""Unit tests for finite field and Galois ring arithmetic."""

from projects.mssn_sn_symgam.challenges.c_quantum.c025_mub_prime_power_exact.reference_solver.finite_field import (
    FiniteFieldGF9,
    GaloisRingGR4,
)


def test_galois_ring_gr4_ranks():
    for r in (1, 2, 3):
        gr = GaloisRingGR4(r)
        teich = gr.teichmuller_set
        assert len(teich) == 2**r

        # Every non-zero element satisfies x^{2^r - 1} = 1 in Z_4[xi]
        one = gr.one()
        for x in teich[1:]:
            curr = x
            for _ in range(2**r - 2):
                curr = gr.mul(curr, x)
            assert curr == one


def test_galois_ring_trace():
    for r in (1, 2, 3):
        gr = GaloisRingGR4(r)
        for x in gr.teichmuller_set:
            tr = gr.trace(x)
            assert tr in (0, 1, 2, 3)
        # Trace of 0 is 0
        assert gr.trace(gr.zero()) == 0


def test_finite_field_gf9():
    gf9 = FiniteFieldGF9()
    assert len(gf9.elements) == 9

    # Test trace map: Tr(x) = 2*x0 mod 3
    for x in gf9.elements:
        tr = gf9.trace(x)
        assert tr in (0, 1, 2)
        assert tr == (2 * x[0]) % 3

    # Test multiplication: u^2 = -1 = 2 mod 3
    u = (0, 1)
    u2 = gf9.mul(u, u)
    assert u2 == (2, 0)
