# Dual-checker capsules

Four self-contained math challenges. Each has a reference solver, two
independent checkers that verify a full answer certificate, a set of input
cases (base, gauge controls, poisoned traps), and a set of corrupted answers
that both checkers must reject. Ported from an internal test suite. Standard
library plus pytest (the spectral checker uses NumPy for an optional secondary
check if it is installed).

| Capsule | Problem |
|---|---|
| `c011_cycle_rank_ladder_coboundary_repair` | minimum weighted L1 repair of edge claims on a graph so they become a potential difference, with an LP dual circulation certificate |
| `c021_q40_r` | exact ground energy and degeneracy of a commuting Pauli Hamiltonian on up to 8 qubits |
| `c039_lattice_z2_gauge_theory_gauss_law` | ground-state degeneracy and logical operators of the Z2 lattice gauge (toric-code) model on a surface |
| `c050_equational_theorem_proving` | prove an equation by rewriting with axioms, or refute it with a finite countermodel |

Run everything from the repository root:

    python -m pytest demos/dual_checker_capsules -q

Expected: `351 passed`.

One capsule at a time:

    python -m pytest demos/dual_checker_capsules/test_c011_reference_cases.py demos/dual_checker_capsules/c011_cycle_rank_ladder_coboundary_repair -q
    python -m pytest demos/dual_checker_capsules/test_c021_reference_cases.py demos/dual_checker_capsules/c021_q40_r -q
    python -m pytest demos/dual_checker_capsules/test_c039_reference_cases.py demos/dual_checker_capsules/c039_lattice_z2_gauge_theory_gauss_law -q
    python -m pytest demos/dual_checker_capsules/test_c050_reference_and_mutations.py -q

Wiki pages: Test-Graph-Coboundary-Repair-Capsule, Test-Commuting-Pauli-Ground-State-Capsule,
Test-Lattice-Gauge-Gauss-Law-Capsule, Test-Equational-Proof-Capsule.
