"""Multivalued dependencies, exact relational invariants, and simplicial DHNF.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from typing import Iterable, Mapping, Sequence

from .relational import (
    FunctionalDependency,
    RelationalSchema,
    check_bcnf,
    compute_attribute_closure,
)
from .tower_forms import ZfnfResult, verify_zfnf

# =============================================================================
# Part 6: Advanced Relational, Hodge & Invariance Extensions
# =============================================================================


@dataclass(frozen=True)
class MultivaluedDependency:
    """A multivalued dependency X ->> Y over a relational heading."""

    determinant: frozenset[str]
    dependent: frozenset[str]

    @classmethod
    def from_str(cls, determinant: str, dependent: str) -> "MultivaluedDependency":
        det = frozenset(d.strip() for d in determinant.split(",") if d.strip())
        dep = frozenset(d.strip() for d in dependent.split(",") if d.strip())
        return cls(determinant=det, dependent=dep)

    def is_trivial(self, heading: frozenset[str]) -> bool:
        """Trivial MVD: Y ⊆ X or X ∪ Y = heading."""
        return (
            self.dependent.issubset(self.determinant)
            or (self.determinant | self.dependent) == heading
        )

    def __repr__(self) -> str:
        det = ",".join(sorted(self.determinant))
        dep = ",".join(sorted(self.dependent))
        return f"{det} ->> {dep}"


@dataclass(frozen=True)
class ChaseMvdResult:
    """Result of running chase with both FDs and MVDs."""

    is_implied: bool
    heading: tuple[str, ...]
    components: tuple[tuple[str, ...], ...]
    fd_steps: int
    mvd_tuples_generated: int
    final_row_count: int
    distinguished_row_index: int | None
    final_tableau: tuple[dict[str, str], ...]


@dataclass
class _MvdChaseState:
    heading: tuple[str, ...]
    components: tuple[tuple[str, ...], ...]
    heading_set: frozenset[str]
    dependencies: list[FunctionalDependency]
    mvds: list[MultivaluedDependency]
    tableau: list[dict[str, str]]
    fd_steps: int = 0
    mvd_tuples_generated: int = 0


@dataclass(frozen=True)
class _MvdChaseOptions:
    components: Sequence[Iterable[str]]
    candidate_keys: Iterable[Iterable[str]] | None = None
    max_iterations: int = 1000


def _find_distinguished_tableau_row(
    tableau: Sequence[Mapping[str, str]], sorted_attrs: Sequence[str]
) -> int | None:
    for r_idx, r in enumerate(tableau):
        if all(r[a] == f"a_{a}" for a in sorted_attrs):
            return r_idx
    return None


def _init_mvd_chase_tableau(
    heading: Iterable[str],
    components: Sequence[Iterable[str]],
    dependencies: Iterable[FunctionalDependency],
    candidate_keys: Iterable[Iterable[str]] | None,
) -> tuple[
    tuple[str, ...],
    tuple[tuple[str, ...], ...],
    frozenset[str],
    list[FunctionalDependency],
    list[dict[str, str]],
]:
    sorted_attrs = tuple(sorted(set(heading)))
    comps = tuple(tuple(sorted(set(c))) for c in components)
    h_set = frozenset(sorted_attrs)

    all_fds: list[FunctionalDependency] = list(dependencies)
    if candidate_keys:
        for k in candidate_keys:
            k_set = frozenset(k)
            dep_set = h_set - k_set
            if dep_set:
                all_fds.append(FunctionalDependency(determinant=k_set, dependent=dep_set))

    tableau: list[dict[str, str]] = []
    for i, comp in enumerate(comps):
        c_set = frozenset(comp)
        row: dict[str, str] = {}
        for a in sorted_attrs:
            row[a] = f"a_{a}" if a in c_set else f"b_{i}_{a}"
        tableau.append(row)
    return sorted_attrs, comps, h_set, all_fds, tableau


def _choose_canonical_symbol(v1: str, v2: str) -> tuple[str, str]:
    if v1.startswith("a_"):
        return v1, v2
    if v2.startswith("a_"):
        return v2, v1
    return min(v1, v2), max(v1, v2)


def _substitute_tableau_symbol(
    tableau: list[dict[str, str]], sorted_attrs: Sequence[str], old_sym: str, new_sym: str
) -> None:
    for r in tableau:
        for col in sorted_attrs:
            if r[col] == old_sym:
                r[col] = new_sym


def _apply_fd_to_tableau_pair(
    state: _MvdChaseState,
    r1: int,
    r2: int,
    fd: FunctionalDependency,
) -> tuple[str, str] | None:
    determinant = (attr for attr in fd.determinant if attr in state.heading_set)
    if not all(state.tableau[r1][attr] == state.tableau[r2][attr] for attr in determinant):
        return None
    for dep_attr in sorted(fd.dependent & state.heading_set):
        v1, v2 = state.tableau[r1][dep_attr], state.tableau[r2][dep_attr]
        if v1 != v2:
            new_sym, old_sym = _choose_canonical_symbol(v1, v2)
            _substitute_tableau_symbol(state.tableau, state.heading, old_sym, new_sym)
            return old_sym, new_sym
    return None


def _apply_fds_fixpoint_step(
    state: _MvdChaseState,
) -> int:
    steps = 0
    applications = (
        (fd, pair)
        for fd in state.dependencies
        for pair in combinations(range(len(state.tableau)), 2)
    )
    for fd, (r1, r2) in applications:
        if _apply_fd_to_tableau_pair(state, r1, r2, fd) is None:
            continue
        steps += 1
        if _find_distinguished_tableau_row(state.tableau, state.heading) is not None:
            return steps
    return steps


def _apply_mvd_to_pair(
    state: _MvdChaseState,
    r1: int,
    r2: int,
    mvd: MultivaluedDependency,
) -> bool:
    det = mvd.determinant & state.heading_set
    dep = mvd.dependent & state.heading_set
    rest = state.heading_set - (det | dep)
    if not all(state.tableau[r1][attr] == state.tableau[r2][attr] for attr in det):
        return False

    new_row = {attr: state.tableau[r1][attr] for attr in det | dep}
    new_row.update({attr: state.tableau[r2][attr] for attr in rest})
    if any(all(existing[a] == new_row[a] for a in state.heading) for existing in state.tableau):
        return False
    state.tableau.append(new_row)
    return True


def _apply_mvds_round(
    state: _MvdChaseState,
) -> int:
    tuples_generated = 0
    row_count = len(state.tableau)
    applications = (
        (mvd, r1, r2)
        for mvd in state.mvds
        for r1 in range(row_count)
        for r2 in range(row_count)
        if r1 != r2
    )
    for mvd, r1, r2 in applications:
        if not _apply_mvd_to_pair(state, r1, r2, mvd):
            continue
        tuples_generated += 1
        if _find_distinguished_tableau_row(state.tableau, state.heading) is not None:
            return tuples_generated
    return tuples_generated


def _make_chase_mvd_result(
    state: _MvdChaseState,
    dist_row: int | None,
) -> ChaseMvdResult:
    return ChaseMvdResult(
        is_implied=dist_row is not None,
        heading=state.heading,
        components=state.components,
        fd_steps=state.fd_steps,
        mvd_tuples_generated=state.mvd_tuples_generated,
        final_row_count=len(state.tableau),
        distinguished_row_index=dist_row,
        final_tableau=tuple(dict(r) for r in state.tableau),
    )


def chase_mvd(
    heading: Iterable[str],
    dependencies: Iterable[FunctionalDependency],
    mvds: Iterable[MultivaluedDependency],
    *args: object,
    **kwargs: object,
) -> ChaseMvdResult:
    """Tests whether functional and multivalued dependencies entail a lossless decomposition.

    Executes both equality-generating dependencies (EGDs / FDs) via global symbol substitution
    and tuple-generating dependencies (TGDs / MVDs) via tuple synthesis.
    """
    options = _parse_mvd_chase_options(args, kwargs)
    attrs, comps, heading_set, all_fds, tableau = _init_mvd_chase_tableau(
        heading, options.components, dependencies, options.candidate_keys
    )
    state = _MvdChaseState(attrs, comps, heading_set, all_fds, list(mvds), tableau)
    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    if dist_row is not None:
        return _make_chase_mvd_result(state, dist_row)

    iteration = 0
    changed = True
    while changed and iteration < options.max_iterations:
        changed = False
        iteration += 1
        fd_changed, result = _run_fd_phase(state, options.max_iterations, iteration)
        if result is not None:
            return result
        mvd_changed, result = _run_mvd_phase(state)
        if result is not None:
            return result
        changed = fd_changed or mvd_changed

    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    return _make_chase_mvd_result(state, dist_row)


def _parse_mvd_chase_options(
    args: tuple[object, ...], kwargs: dict[str, object]
) -> _MvdChaseOptions:
    names = ("components", "candidate_keys", "max_iterations")
    if len(args) > len(names):
        raise TypeError(f"chase_mvd() takes at most 6 arguments ({len(args) + 3} given)")
    values = dict(zip(names, args, strict=False))
    for name, value in kwargs.items():
        if name not in names:
            raise TypeError(f"chase_mvd() got an unexpected keyword argument '{name}'")
        if name in values:
            raise TypeError(f"chase_mvd() got multiple values for argument '{name}'")
        values[name] = value
    if "components" not in values:
        raise TypeError("chase_mvd() missing required argument: 'components'")
    return _MvdChaseOptions(**values)  # type: ignore[arg-type]


def _run_fd_phase(
    state: _MvdChaseState, max_iterations: int, iteration: int
) -> tuple[bool, ChaseMvdResult | None]:
    changed = False
    while iteration < max_iterations:
        steps = _apply_fds_fixpoint_step(state)
        if steps == 0:
            break
        state.fd_steps += steps
        changed = True
        dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
        if dist_row is not None:
            return True, _make_chase_mvd_result(state, dist_row)
    return changed, None


def _run_mvd_phase(state: _MvdChaseState) -> tuple[bool, ChaseMvdResult | None]:
    generated = _apply_mvds_round(state)
    if generated == 0:
        return False, None
    state.mvd_tuples_generated += generated
    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    result = None if dist_row is None else _make_chase_mvd_result(state, dist_row)
    return True, result


def check_4nf(
    schema: RelationalSchema, mvds: Iterable[MultivaluedDependency]
) -> tuple[bool, str | None]:
    """Fourth Normal Form (4NF): Schema is in BCNF and every non-trivial MVD X ->> Y has X as a superkey."""
    ok_bcnf, err_bcnf = check_bcnf(schema)
    if not ok_bcnf:
        return False, f"4NF requires BCNF: {err_bcnf}"

    for mvd in mvds:
        if mvd.is_trivial(schema.attributes):
            continue
        if not schema.is_superkey(mvd.determinant):
            det_str = ",".join(sorted(mvd.determinant))
            dep_str = ",".join(sorted(mvd.dependent))
            return (
                False,
                f"4NF MVD Violation: {det_str} ->> {dep_str} is non-trivial but determinant is not a superkey",
            )

    return True, None


def chase_tableau_cell_partition(
    tableau: Sequence[Mapping[str, str]], heading: Sequence[str]
) -> frozenset[frozenset[tuple[int, str]]]:
    """Computes the equivalence classes of tableau cells based on their equated symbols."""
    symbol_to_cells: dict[str, set[tuple[int, str]]] = {}
    for r_idx, row in enumerate(tableau):
        for col in heading:
            sym = row[col]
            symbol_to_cells.setdefault(sym, set()).add((r_idx, col))
    return frozenset(frozenset(cells) for cells in symbol_to_cells.values())


def verify_armstrong_closure_axioms(
    heading: Iterable[str], dependencies: Iterable[FunctionalDependency]
) -> dict[str, bool]:
    """Verifies that attribute closure X^+ satisfies the Armstrong and Kuratowski closure axioms."""
    h_list = sorted(set(heading))
    deps = list(dependencies)
    subsets = [frozenset(c) for r in range(len(h_list) + 1) for c in combinations(h_list, r)]
    closures = {s: compute_attribute_closure(s, deps) for s in subsets}

    reflexive = all(s.issubset(closures[s]) for s in subsets)
    idempotent = all(compute_attribute_closure(closures[s], deps) == closures[s] for s in subsets)

    monotonic = all(
        not left.issubset(right) or closures[left].issubset(closures[right])
        for left in subsets
        for right in subsets
    )
    augmented = all(
        not dependent.issubset(closures[determinant])
        or (dependent | extension).issubset(closures[determinant | extension])
        for determinant in subsets
        for dependent in subsets
        for extension in subsets
    )
    transitive = all(
        not intermediate.issubset(closures[determinant])
        or not dependent.issubset(closures[intermediate])
        or dependent.issubset(closures[determinant])
        for determinant in subsets
        for intermediate in subsets
        for dependent in subsets
    )

    all_sat = reflexive and idempotent and monotonic and augmented and transitive
    return {
        "reflexivity": reflexive,
        "idempotence": idempotent,
        "monotonicity": monotonic,
        "augmentation": augmented,
        "transitivity": transitive,
        "all_satisfied": all_sat,
    }


def verify_candidate_keys_antichain(schema: RelationalSchema) -> tuple[bool, list[str]]:
    """Verifies that candidate keys of schema form an antichain of strictly minimal superkeys."""
    keys = schema.candidate_keys()
    defects: list[str] = []

    for k in keys:
        if not schema.is_superkey(k):
            defects.append(f"Key {set(k)} is not a superkey")

    for i, k1 in enumerate(keys):
        for j, k2 in enumerate(keys):
            if i != j and k1.issubset(k2) and k1 != k2:
                defects.append(f"Key {set(k2)} contains candidate key {set(k1)} (not minimal)")

    for k in keys:
        for attr in k:
            sub = k - {attr}
            if schema.is_superkey(sub):
                defects.append(
                    f"Key {set(k)} is not minimal: proper subset {set(sub)} is a superkey"
                )

    return (len(defects) == 0, defects)


def verify_zfnf_scaling_invariance(
    primal_obj: int | Fraction,
    dual_obj: int | Fraction,
    scale: int | Fraction,
) -> tuple[bool, ZfnfResult, ZfnfResult]:
    """Verifies that Zero-Float LP Duality is invariant under positive rational scaling."""
    if scale <= 0:
        raise ValueError("Scaling factor must be strictly positive rational")

    res_base = verify_zfnf(primal_obj, dual_obj)
    scaled_primal = Fraction(primal_obj) * Fraction(scale)
    scaled_dual = Fraction(dual_obj) * Fraction(scale)
    res_scaled = verify_zfnf(scaled_primal, scaled_dual)

    invariant = res_base.terminal == res_scaled.terminal
    return invariant, res_base, res_scaled


@dataclass(frozen=True)
class Simplicial2DComplex:
    """Oriented 2D simplicial complex with vertex, edge, and face incidence."""

    num_vertices: int
    edges: tuple[tuple[int, int], ...]
    faces: tuple[tuple[int, int, int], ...]

    def coboundary_d0(self, alpha: Sequence[int | Fraction]) -> list[Fraction]:
        """d0: 0-cochain (potential) -> 1-cochain on edges: (d0 alpha)(u, v) = alpha[v] - alpha[u]."""
        return [Fraction(alpha[v]) - Fraction(alpha[u]) for u, v in self.edges]

    def coboundary_d1(self, beta: Sequence[int | Fraction]) -> list[Fraction]:
        """d1: 1-cochain -> 2-cochain on faces: (d1 beta)(u, v, w) = beta(u, v) + beta(v, w) + beta(w, u)."""
        edge_idx = {e: i for i, e in enumerate(self.edges)}
        res: list[Fraction] = []
        for u, v, w in self.faces:
            oriented_edges = ((u, v), (v, w), (w, u))
            res.append(
                sum(
                    (_oriented_edge_value(beta, edge_idx, edge) for edge in oriented_edges),
                    Fraction(0),
                )
            )
        return res

    def inner_product_edges(
        self, beta1: Sequence[int | Fraction], beta2: Sequence[int | Fraction]
    ) -> Fraction:
        """Standard discrete Hodge inner product on 1-cochains."""
        return sum(Fraction(b1) * Fraction(b2) for b1, b2 in zip(beta1, beta2, strict=True))


def _oriented_edge_value(
    beta: Sequence[int | Fraction],
    edge_index: Mapping[tuple[int, int], int],
    edge: tuple[int, int],
) -> Fraction:
    if edge in edge_index:
        return Fraction(beta[edge_index[edge]])
    reversed_edge = edge[1], edge[0]
    if reversed_edge in edge_index:
        return -Fraction(beta[edge_index[reversed_edge]])
    raise ValueError(f"Face edge {edge} not declared in edges")


def verify_simplicial_dhnf(
    complex_2d: Simplicial2DComplex,
    potential: Sequence[int | Fraction],
    harmonic: Sequence[int | Fraction],
) -> tuple[bool, Fraction, list[Fraction]]:
    """Verifies Discrete Hodge Normal Form (DHNF) on a 2D simplicial complex:
    1. Nilpotency: d1(d0(alpha)) == 0 (exact cochains are closed cycles).
    2. Orthogonality: <d0(alpha), h> == 0 (exact cochains are orthogonal to harmonic 1-forms).
    """
    exact_cochain = complex_2d.coboundary_d0(potential)
    curl = complex_2d.coboundary_d1(exact_cochain)
    nilpotent = all(c == 0 for c in curl)

    dot_harmonic = complex_2d.inner_product_edges(exact_cochain, harmonic)
    orthogonal = dot_harmonic == 0

    return (nilpotent and orthogonal, dot_harmonic, curl)
