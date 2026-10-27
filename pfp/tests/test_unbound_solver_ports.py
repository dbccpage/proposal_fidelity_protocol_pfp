"""The default homology and holonomy ports refuse; they never verify.

Counterexample from the study: before any adapter was bound, the default
homology port answered ``boundary_law_verified: True`` for any input, including
one that is not a simplicial complex at all, so a missing native host read as a
verified boundary law. The package import binds the native adapter, so these
tests load a fresh copy of ``domain/solvers/kinds.py`` to see its defaults.
AuthorityEffect: None.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

import pfp.domain.solvers as solvers_package
from pfp.domain.exact.q import Q
from pfp.domain.solvers.regime import Regime

KINDS = Path(solvers_package.__file__).resolve().parent / "kinds.py"
FRESH = "pfp.domain.solvers._kinds_unbound_copy"


@pytest.fixture
def fresh_kinds() -> ModuleType:
    spec = importlib.util.spec_from_file_location(FRESH, KINDS)
    module = importlib.util.module_from_spec(spec)
    sys.modules[FRESH] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(FRESH, None)


def _assert_port_unbound(call) -> None:
    with pytest.raises(Exception) as caught:
        call()
    assert getattr(caught.value, "code", None) == "PORT_UNBOUND", repr(caught.value)


def test_default_homology_port_refuses_instead_of_verifying(fresh_kinds: ModuleType) -> None:
    port = fresh_kinds.get_homology_port()
    not_a_complex = ((0, 0, 0), (7,), ())
    _assert_port_unbound(lambda: port.verify_simplicial_boundary_law(not_a_complex))
    _assert_port_unbound(lambda: port.verify_boundary_law(object()))
    _assert_port_unbound(lambda: port.verify_boundary_closed((((0, 1, 1),),)))
    _assert_port_unbound(lambda: port.compute_betti_numbers(object()))


def test_default_holonomy_port_refuses_instead_of_computing(fresh_kinds: ModuleType) -> None:
    port = fresh_kinds.get_holonomy_port()
    table = ((Q(1), Q(0)), (Q(0), Q(1)))
    _assert_port_unbound(lambda: port.is_ordered_closure((table,), ((0, False),)))
    _assert_port_unbound(lambda: port.ordered_loop_product((table,), ((0, False),)))
    _assert_port_unbound(lambda: port.path_holonomy(object(), ("a",)))
    _assert_port_unbound(lambda: port.loop_curvature(object(), ("a",)))


def test_requirement_with_unbound_port_is_refused_not_satisfied(fresh_kinds: ModuleType) -> None:
    oracle = fresh_kinds.RegimeOracle(Regime((), (), frozenset(), frozenset(), frozenset()))
    requirement = fresh_kinds.SimplicialBoundaryLawSatisfied("bogus", ((0, 0, 0),))
    _assert_port_unbound(lambda: fresh_kinds.satisfies(oracle, requirement))
    _assert_port_unbound(lambda: fresh_kinds.refutation(oracle, requirement))
