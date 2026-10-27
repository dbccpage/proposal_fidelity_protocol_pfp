"""Tests for Clifford Tableau representation and operations (C023)."""

from __future__ import annotations

from projects.mssn_sn_symgam.challenges.c_quantum.c023_clifford_tableau_synthesis.reference_solver.tableau import (
    Tableau,
)


def test_tableau_identity():
    tab = Tableau(3)
    assert tab.n == 3
    is_sym, _ = tab.check_symplecticity()
    assert is_sym is True
    images = tab.to_images_dict()
    assert images["X0"] == "+XII"
    assert images["X1"] == "+IXI"
    assert images["Z0"] == "+ZII"


def test_tableau_single_qubit_gates():
    tab = Tableau(1)
    # Apply H: X -> Z, Z -> X
    tab.apply_H(0)
    assert tab.row_to_pauli_str(0) == "+Z"
    assert tab.row_to_pauli_str(1) == "+X"
    assert tab.check_symplecticity()[0] is True

    # Apply S: Z -> Z, X -> Y
    tab.apply_S(0)
    assert tab.row_to_pauli_str(0) == "+Z"
    assert tab.row_to_pauli_str(1) == "+Y"
    assert tab.check_symplecticity()[0] is True


def test_tableau_cnot():
    tab = Tableau(2)
    # Apply CNOT(0, 1): X0 -> X0 X1, X1 -> X1, Z0 -> Z0, Z1 -> Z0 Z1
    tab.apply_CNOT(0, 1)
    assert tab.row_to_pauli_str(0) == "+XX"
    assert tab.row_to_pauli_str(1) == "+IX"
    assert tab.row_to_pauli_str(2) == "+ZI"
    assert tab.row_to_pauli_str(3) == "+ZZ"
    assert tab.check_symplecticity()[0] is True


def test_tableau_symplecticity_violation():
    # Non-symplectic images: X0 and Z0 commute instead of anticommute
    images = {
        "X0": "+X",
        "Z0": "+X",
    }
    tab = Tableau.from_images_dict(1, images)
    is_sym, witness = tab.check_symplecticity()
    assert is_sym is False
    assert witness["pair"] == ["X0", "Z0"]
    assert witness["expected"] == "anticommute"


def test_tableau_copy_and_equality():
    tab1 = Tableau(2)
    tab1.apply_H(0)
    tab1.apply_CNOT(0, 1)
    tab2 = tab1.copy()
    assert tab1.x == tab2.x
    assert tab1.z == tab2.z
    assert tab1.r == tab2.r
    tab2.apply_S(1)
    assert tab1.z != tab2.z or tab1.r != tab2.r
