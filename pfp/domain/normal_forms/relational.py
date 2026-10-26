"""Classical relational dependency algebra and normal forms.

AuthorityEffect: None.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence

if TYPE_CHECKING:
    from .relational_extensions import MultivaluedDependency

# =============================================================================
# Part 2: Classical Relational Dependency Algebra & Normal Form Checker
# =============================================================================


@dataclass(frozen=True)
class FunctionalDependency:
    """A functional dependency X -> Y over attribute names."""

    determinant: frozenset[str]
    dependent: frozenset[str]

    def __post_init__(self) -> None:
        if not self.determinant:
            raise ValueError("Determinant of functional dependency cannot be empty")
        if not self.dependent:
            raise ValueError("Dependent of functional dependency cannot be empty")

    @classmethod
    def from_str(cls, det: str, dep: str) -> "FunctionalDependency":
        det_set = frozenset(x.strip() for x in det.split(",") if x.strip())
        dep_set = frozenset(x.strip() for x in dep.split(",") if x.strip())
        return cls(det_set, dep_set)

    def is_trivial(self) -> bool:
        return self.dependent.issubset(self.determinant)

    def __repr__(self) -> str:
        det = ",".join(sorted(self.determinant))
        dep = ",".join(sorted(self.dependent))
        return f"{det} -> {dep}"


def compute_attribute_closure(
    attributes: Iterable[str], dependencies: Iterable[FunctionalDependency]
) -> frozenset[str]:
    """Computes the attribute closure X^+ under Armstrong's Axioms."""
    closure = set(attributes)
    deps = list(dependencies)
    changed = True
    while changed:
        changed = False
        for fd in deps:
            additions = fd.dependent if fd.determinant.issubset(closure) else ()
            before = len(closure)
            closure.update(additions)
            changed = changed or len(closure) > before
    return frozenset(closure)


@dataclass(frozen=True)
class RelationalSchema:
    """A relational schema (Attributes, Dependencies)."""

    attributes: frozenset[str]
    dependencies: frozenset[FunctionalDependency]

    def attribute_closure(self, attrs: Iterable[str]) -> frozenset[str]:
        """Computes the attribute closure X^+ under Armstrong's Axioms for this schema."""
        return compute_attribute_closure(attrs, self.dependencies)

    def is_superkey(self, attrs: Iterable[str]) -> bool:
        closure = compute_attribute_closure(attrs, self.dependencies)
        return self.attributes.issubset(closure)

    def candidate_keys(self) -> list[frozenset[str]]:
        """Finds all minimal candidate keys."""
        all_attrs = sorted(self.attributes)
        keys: list[frozenset[str]] = []

        # Search by increasing size
        for size in range(1, len(all_attrs) + 1):
            for comb in combinations(all_attrs, size):
                comb_set = frozenset(comb)
                # Check if superkey
                if self.is_superkey(comb_set) and not any(k.issubset(comb_set) for k in keys):
                    keys.append(comb_set)
        return keys

    def prime_attributes(self) -> frozenset[str]:
        keys = self.candidate_keys()
        primes: set[str] = set()
        for k in keys:
            primes.update(k)
        return frozenset(primes)


def find_candidate_keys(schema: RelationalSchema) -> list[frozenset[str]]:
    """Returns all minimal candidate keys for the given schema."""
    return schema.candidate_keys()


def check_1nf(schema: RelationalSchema) -> tuple[bool, str | None]:
    """1NF requires atomic attribute domains."""
    if not schema.attributes:
        return False, "Schema has no declared attributes"
    return True, None


def check_2nf(schema: RelationalSchema) -> tuple[bool, str | None]:
    """2NF: 1NF and no non-prime attribute partially depends on any candidate key."""
    ok_1nf, err = check_1nf(schema)
    if not ok_1nf:
        return False, err

    keys = schema.candidate_keys()
    primes = schema.prime_attributes()
    non_primes = schema.attributes - primes

    for key in keys:
        violation = _partial_dependency_violation(schema, key, non_primes)
        if violation is not None:
            subset, dependent = violation
            return False, f"2NF Partial Dependency Violation: {set(subset)} -> {set(dependent)}"
    return True, None


def _partial_dependency_violation(
    schema: RelationalSchema,
    key: frozenset[str],
    non_primes: frozenset[str],
) -> tuple[frozenset[str], frozenset[str]] | None:
    subsets = (
        frozenset(subset) for size in range(1, len(key)) for subset in combinations(key, size)
    )
    for subset in subsets:
        dependent = (compute_attribute_closure(subset, schema.dependencies) & non_primes) - subset
        if dependent:
            return subset, frozenset(dependent)
    return None


def check_3nf(schema: RelationalSchema) -> tuple[bool, str | None]:
    """3NF: 2NF and for every non-trivial X -> A, X is superkey or A is prime."""
    ok_2nf, err = check_2nf(schema)
    if not ok_2nf:
        return False, err

    primes = schema.prime_attributes()
    for fd in schema.dependencies:
        for a in fd.dependent - fd.determinant:
            if schema.is_superkey(fd.determinant):
                continue
            if a in primes:
                continue
            return (
                False,
                f"3NF Transitive Dependency Violation: {set(fd.determinant)} -> {a} (not superkey and attribute not prime)",
            )
    return True, None


def check_bcnf(schema: RelationalSchema) -> tuple[bool, str | None]:
    """BCNF: For every non-trivial X -> Y, X is a superkey."""
    for fd in schema.dependencies:
        if not fd.is_trivial():
            if not schema.is_superkey(fd.determinant):
                return (
                    False,
                    f"BCNF Violation: determinant {set(fd.determinant)} is not a candidate superkey",
                )
    return True, None


@dataclass(frozen=True)
class JoinDependency:
    """A join dependency ⋈[R_1, R_2, ..., R_k] over a declared heading."""

    heading: frozenset[str]
    components: tuple[frozenset[str], ...]

    def __post_init__(self) -> None:
        if not self.heading:
            raise ValueError("Join dependency heading cannot be empty")
        if len(self.components) < 2:
            raise ValueError("Join dependency must have at least two components")
        union_comp = frozenset().union(*self.components)
        if union_comp != self.heading:
            raise ValueError(
                f"Union of components {set(union_comp)} does not equal declared heading {set(self.heading)}"
            )

    @classmethod
    def from_sub_schemas(
        cls, heading: Iterable[str], components: Sequence[Iterable[str]]
    ) -> "JoinDependency":
        h = frozenset(heading)
        comps = tuple(frozenset(c) for c in components)
        return cls(heading=h, components=comps)

    @classmethod
    def from_str(cls, text: str, heading: Iterable[str] | None = None) -> "JoinDependency":
        """Parses a join dependency string, e.g. '*(SP, PJ, JS)' or '⋈([S, P], [P, J], [J, S])'."""
        cleaned = text.strip()
        for pfx in ("*⋈", "⋈", "*"):
            if cleaned.startswith(pfx):
                cleaned = cleaned[len(pfx) :].strip()
        if cleaned.startswith("(") and cleaned.endswith(")"):
            cleaned = cleaned[1:-1].strip()

        comps = [_parse_join_component(raw) for raw in _split_join_components(cleaned)]

        h = frozenset(heading) if heading is not None else frozenset().union(*comps)
        return cls(heading=h, components=tuple(comps))

    def is_trivial(self, heading: Iterable[str] | None = None) -> bool:
        """A JD is trivial if any component equals the entire heading."""
        target_heading = frozenset(heading) if heading is not None else self.heading
        return any(c == target_heading for c in self.components)

    def __repr__(self) -> str:
        comps = ", ".join(f"[{','.join(sorted(c))}]" for c in self.components)
        return f"⋈({comps})"


def _split_join_components(cleaned: str) -> list[str]:
    if ";" in cleaned:
        return [component.strip() for component in cleaned.split(";") if component.strip()]
    if "],[" in cleaned or "], [" in cleaned or "[" in cleaned:
        import re

        return re.findall(r"\[(.*?)\]", cleaned)
    if "," in cleaned:
        return [component.strip() for component in cleaned.split(",") if component.strip()]
    return [cleaned]


def _parse_join_component(raw: str) -> frozenset[str]:
    cleaned = raw.strip("[]() ")
    if "," in cleaned:
        return frozenset(attr.strip() for attr in cleaned.split(",") if attr.strip())
    if " " in cleaned:
        return frozenset(attr.strip() for attr in cleaned.split() if attr.strip())
    if len(cleaned) > 1 and cleaned.isupper() and all(char.isalpha() for char in cleaned):
        return frozenset(cleaned)
    return frozenset([cleaned])


@dataclass(frozen=True)
class ChaseStep:
    """A single deterministic substitution step in the relational chase."""

    step_number: int
    fd_applied: FunctionalDependency
    rows_matched: tuple[int, int]
    attribute_equated: str
    old_symbol: str
    new_symbol: str


@dataclass(frozen=True)
class ChaseResult:
    """The result of applying the chase algorithm to test if FDs entail a JD."""

    is_implied: bool | None
    heading: tuple[str, ...]
    components: tuple[tuple[str, ...], ...]
    steps: tuple[ChaseStep, ...]
    initial_tableau: tuple[dict[str, str], ...]
    final_tableau: tuple[dict[str, str], ...]
    distinguished_row_index: int | None
    spurious_tuple_witness: dict[str, str] | None
    status: str = "Accept"

    def __repr__(self) -> str:
        res = (
            "IMPLIED"
            if self.is_implied is True
            else ("NOT_IMPLIED" if self.is_implied is False else "BUDGET_UNKNOWN")
        )
        return f"ChaseResult({res}, status={self.status}, steps={len(self.steps)}, dist_row={self.distinguished_row_index})"


def _find_distinguished_tableau_row(
    tableau: Sequence[Mapping[str, str]], sorted_attrs: Sequence[str]
) -> int | None:
    for r_idx, r in enumerate(tableau):
        if all(r[a] == f"a_{a}" for a in sorted_attrs):
            return r_idx
    return None


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


def _init_chase_tableau(
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

    union_comp = frozenset().union(*(frozenset(c) for c in comps))
    if union_comp != h_set:
        raise ValueError(f"Component union {set(union_comp)} does not match heading {set(h_set)}")

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


@dataclass
class _ChaseState:
    heading: tuple[str, ...]
    components: tuple[tuple[str, ...], ...]
    heading_set: frozenset[str]
    dependencies: list[FunctionalDependency]
    tableau: list[dict[str, str]]
    initial_tableau: tuple[dict[str, str], ...]
    steps: list[ChaseStep]
    early_exit: bool


@dataclass(frozen=True)
class _ChaseOptions:
    candidate_keys: Iterable[Iterable[str]] | None = None
    max_iterations: int = 1000
    early_exit: bool = True


def _apply_fd_chase_pair(state: _ChaseState, r1: int, r2: int, fd: FunctionalDependency) -> bool:
    tableau = state.tableau
    determinant = (attr for attr in fd.determinant if attr in state.heading_set)
    if not all(tableau[r1][attr] == tableau[r2][attr] for attr in determinant):
        return False
    applied = False
    for dep_attr in sorted(fd.dependent & state.heading_set):
        v1, v2 = tableau[r1][dep_attr], tableau[r2][dep_attr]
        if v1 == v2:
            continue
        new_sym, old_sym = _choose_canonical_symbol(v1, v2)
        _substitute_tableau_symbol(tableau, state.heading, old_sym, new_sym)
        state.steps.append(
            ChaseStep(
                step_number=len(state.steps) + 1,
                fd_applied=fd,
                rows_matched=(r1, r2),
                attribute_equated=dep_attr,
                old_symbol=old_sym,
                new_symbol=new_sym,
            )
        )
        applied = True
    return applied


def _run_chase_fd_iteration(state: _ChaseState) -> tuple[bool, int | None]:
    changed = False
    applications = (
        (fd, pair)
        for fd in state.dependencies
        for pair in combinations(range(len(state.components)), 2)
    )
    for fd, (r1, r2) in applications:
        if not _apply_fd_chase_pair(state, r1, r2, fd):
            continue
        changed = True
        dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
        if state.early_exit and dist_row is not None:
            return True, dist_row
    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    return changed, dist_row


def _parse_chase_options(args: tuple[Any, ...], kwargs: dict[str, Any]) -> _ChaseOptions:
    names = ("candidate_keys", "max_iterations", "early_exit")
    if len(args) > len(names):
        raise TypeError(
            f"chase_join_dependency() takes at most 6 arguments ({len(args) + 3} given)"
        )
    values: dict[str, Any] = dict(zip(names, args, strict=False))
    for name, value in kwargs.items():
        if name not in names:
            raise TypeError(f"chase_join_dependency() got an unexpected keyword argument '{name}'")
        if name in values:
            raise TypeError(f"chase_join_dependency() got multiple values for argument '{name}'")
        values[name] = value
    return _ChaseOptions(**values)


def _new_chase_state(
    heading: Iterable[str],
    dependencies: Iterable[FunctionalDependency],
    components: Sequence[Iterable[str]],
    options: _ChaseOptions,
) -> _ChaseState:
    attrs, comps, heading_set, all_fds, tableau = _init_chase_tableau(
        heading, components, dependencies, options.candidate_keys
    )
    return _ChaseState(
        attrs,
        comps,
        heading_set,
        all_fds,
        tableau,
        tuple(dict(row) for row in tableau),
        [],
        options.early_exit,
    )


def _chase_result(
    state: _ChaseState,
    implied: bool | None,
    status: str,
    distinguished_row: int | None,
    witness: dict[str, str] | None = None,
) -> ChaseResult:
    return ChaseResult(
        is_implied=implied,
        heading=state.heading,
        components=state.components,
        steps=tuple(state.steps),
        initial_tableau=state.initial_tableau,
        final_tableau=tuple(dict(row) for row in state.tableau),
        distinguished_row_index=distinguished_row,
        spurious_tuple_witness=witness,
        status=status,
    )


def chase_join_dependency(
    heading: Iterable[str],
    dependencies: Iterable[FunctionalDependency],
    components: Sequence[Iterable[str]],
    *args: Any,
    **kwargs: Any,
) -> ChaseResult:
    """Decide FD/key entailment of a join dependency by exact relational chase.

    Budget exhaustion remains ``BudgetUnknown`` rather than a false non-implication proof.
    """
    options = _parse_chase_options(args, kwargs)
    state = _new_chase_state(heading, dependencies, components, options)
    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    if dist_row is not None:
        return _chase_result(state, True, "Accept", dist_row)

    iteration = 0
    changed = True
    while changed and iteration < options.max_iterations:
        iteration += 1
        changed, dist_row = _run_chase_fd_iteration(state)
        if options.early_exit and dist_row is not None:
            break

    dist_row = _find_distinguished_tableau_row(state.tableau, state.heading)
    if dist_row is not None:
        return _chase_result(state, True, "Accept", dist_row)
    if changed or options.max_iterations <= 0:
        return _chase_result(state, None, "BudgetUnknown", None)
    witness = {attr: f"a_{attr}" for attr in state.heading}
    return _chase_result(state, False, "Reject", None, witness)


def is_5nf_implied_by_keys(
    heading: Iterable[str],
    candidate_keys: Sequence[Iterable[str]],
    components: Sequence[Iterable[str]],
) -> bool:
    """Determines whether a join dependency is logically implied by candidate keys alone.

    This provides the genuine 5NF membership test: a schema in 5NF requires
    that every non-trivial join dependency implied by its constraints is implied
    by its candidate keys alone (Fagin 1979; Darwen, Date, Fagin 2012).
    """
    res = chase_join_dependency(
        heading=heading,
        dependencies=(),
        components=components,
        candidate_keys=candidate_keys,
    )
    return res.is_implied


def check_5nf(
    schema: RelationalSchema,
    join_dependencies: Iterable[JoinDependency] = (),
    mvds: Iterable[MultivaluedDependency] = (),
) -> tuple[bool, str | None]:
    """Fifth Normal Form (5NF / PJNF): Schema is in 4NF and every non-trivial JD implied by its constraints is logically implied by candidate keys."""
    from .relational_extensions import check_4nf

    ok_4nf, err_4nf = check_4nf(schema, mvds)
    if not ok_4nf:
        return False, f"5NF requires 4NF: {err_4nf}"

    cand_keys = schema.candidate_keys()
    for jd in join_dependencies:
        if jd.is_trivial():
            continue
        is_implied = is_5nf_implied_by_keys(
            heading=schema.attributes,
            candidate_keys=cand_keys,
            components=jd.components,
        )
        if not is_implied:
            comps_str = ", ".join(f"[{','.join(sorted(c))}]" for c in jd.components)
            return (
                False,
                f"5NF Join Dependency Violation: JD ⋈({comps_str}) is not logically implied by candidate keys {cand_keys}",
            )

    return True, None


def check_sknf(
    schema: RelationalSchema,
    join_dependencies: Iterable[JoinDependency] = (),
) -> tuple[bool, str | None]:
    """Superkey Normal Form (SKNF): Every component of every non-trivial join dependency contains a candidate key.

    SKNF is strictly weaker than 5NF (Darwen, Date, Fagin 2012 Theorem 6.1).
    """
    cand_keys = schema.candidate_keys()
    for jd in join_dependencies:
        if jd.is_trivial():
            continue
        for comp in jd.components:
            if not any(k.issubset(comp) for k in cand_keys):
                comp_str = ",".join(sorted(comp))
                return (
                    False,
                    f"SKNF Violation: Component [{comp_str}] does not contain any candidate key",
                )
    return True, None


def check_etnf(
    schema: RelationalSchema,
    join_dependencies: Iterable[JoinDependency] = (),
) -> tuple[bool, str | None]:
    """Essential Tuple Normal Form (ETNF) - Darwen, Date, & Fagin (2012).

    A schema (R, Sigma) is in ETNF if and only if:
    1. The schema is in BCNF, AND
    2. Every explicitly declared (or implied non-trivial) join dependency has at least
       one component that is a superkey of R under the declared dependency theory.
    """
    ok_bcnf, err_bcnf = check_bcnf(schema)
    if not ok_bcnf:
        return False, f"ETNF requires BCNF: {err_bcnf}"

    for jd in join_dependencies:
        if not jd.is_trivial(schema.attributes):
            has_superkey = any(schema.is_superkey(comp) for comp in jd.components)
            if not has_superkey:
                return False, f"ETNF Violation: join dependency {jd} has no superkey component"

    return True, None


def _superkey_components_cover(schema: RelationalSchema, jd: JoinDependency) -> bool:
    """Union of the components that are superkeys equals the heading."""
    covered: set[str] = set()
    for component in jd.components:
        if schema.is_superkey(component):
            covered.update(component)
    return frozenset(covered) == schema.attributes


def check_rfnf(
    schema: RelationalSchema,
    join_dependencies: Iterable[JoinDependency] | None = None,
) -> tuple[bool, str | None]:
    """Redundancy-free normal form for one explicit join-dependency theory.

    ``None`` is not a theory, so BCNF alone stays a screen. An empty theory
    declares no join dependency, and the superkey-cover condition holds
    vacuously. A supplied join dependency is accepted only when the union of
    its superkey components equals the heading. Key implication is not the
    decision.
    """
    ok_bcnf, err = check_bcnf(schema)
    if not ok_bcnf:
        return False, f"RFNF requires BCNF: {err}"
    if join_dependencies is None:
        return (
            False,
            "RFNF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not an RFNF decision",
        )
    for jd in join_dependencies:
        if _superkey_components_cover(schema, jd):
            continue
        return (
            False,
            "RFNF Join Dependency Violation: "
            f"{jd} superkey components do not cover the heading",
        )
    return True, None


def check_6nf(
    schema: RelationalSchema,
    join_dependencies: Iterable[JoinDependency] | None = None,
) -> tuple[bool, str | None]:
    """Sixth normal form from a declared trivial join cover.

    The contract requires a cover that asserts every join dependency is
    trivial. Attribute shape is not that test. ``None`` and an empty tuple
    do not make the assertion, so both stay a screen. A non-trivial join
    dependency is a violation on every heading, including an all-key heading.
    """
    if not schema.candidate_keys():
        return False, "No candidate keys found"
    screen = (
        "6NF_SCREEN_NOT_DECISION: absence of a join-dependency theory is not a 6NF decision"
    )
    if join_dependencies is None:
        return False, screen
    declared = tuple(join_dependencies)
    if not declared:
        return False, screen
    for jd in declared:
        if not jd.is_trivial():
            return False, f"6NF Violation: non-trivial join dependency {jd}"
    return True, None


def check_dknf(
    schema: RelationalSchema,
    general_constraints: Sequence[str] | None = None,
) -> tuple[bool, str | None]:
    """Screen declared constraints. This is not a DKNF decision procedure.

    A hit on the five screened keywords is a violation. A BCNF failure is a
    violation. Absence of those keywords, including after a BCNF pass, is not
    a decision that every constraint follows from domains and keys.
    """
    if general_constraints:
        for c in general_constraints:
            c_lower = c.lower()
            if any(
                term in c_lower
                for term in ("cross_table", "inter_row", "aggregate", "cyclic", "non_key")
            ):
                return (
                    False,
                    f"DKNF Violation: General constraint '{c}' exceeds domain and key boundaries",
                )
    ok_bcnf, err = check_bcnf(schema)
    if not ok_bcnf:
        return False, f"DKNF requires all functional dependencies to be key consequences: {err}"
    return (
        False,
        "DKNF_SCREEN_NOT_DECISION: absence of the five screened keywords and a BCNF pass are not a DKNF decision",
    )


def compute_minimal_cover(
    dependencies: Iterable[FunctionalDependency],
) -> list[FunctionalDependency]:
    """Computes a minimal (canonical) cover F_c for a set of functional dependencies.

    Properties:
    1. Singleton right-hand sides: X -> A.
    2. No extraneous left-hand-side attributes: if (X \\ {B})^+ under F contains A, B can be removed from X.
    3. No redundant dependencies: if (F \\ {X -> A}) derives X -> A, it can be removed.
    """
    singleton_fds = _singleton_dependencies(dependencies)
    simplified_fds = [_remove_extraneous_determinants(fd, singleton_fds) for fd in singleton_fds]
    curr_fds = _deduplicate_dependencies(simplified_fds)
    idx = 0
    while idx < len(curr_fds):
        fd = curr_fds[idx]
        others = curr_fds[:idx] + curr_fds[idx + 1 :]
        target = next(iter(sorted(fd.dependent)))
        closure = compute_attribute_closure(fd.determinant, others)
        if target in closure:
            curr_fds.pop(idx)
        else:
            idx += 1

    # Deterministic sort
    return sorted(
        curr_fds, key=lambda f: (tuple(sorted(f.determinant)), tuple(sorted(f.dependent)))
    )


def _dependency_sort_key(fd: FunctionalDependency) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return tuple(sorted(fd.determinant)), tuple(sorted(fd.dependent))


def _singleton_dependencies(
    dependencies: Iterable[FunctionalDependency],
) -> list[FunctionalDependency]:
    result: list[FunctionalDependency] = []
    for fd in sorted(dependencies, key=_dependency_sort_key):
        result.extend(
            FunctionalDependency(fd.determinant, frozenset([attr]))
            for attr in sorted(fd.dependent)
            if attr not in fd.determinant
        )
    return result


def _remove_extraneous_determinants(
    fd: FunctionalDependency,
    dependencies: Sequence[FunctionalDependency],
) -> FunctionalDependency:
    determinant = set(fd.determinant)
    target = next(iter(sorted(fd.dependent)))
    for attr in sorted(determinant):
        if len(determinant) > 1 and target in compute_attribute_closure(
            determinant - {attr}, dependencies
        ):
            determinant.remove(attr)
    return FunctionalDependency(frozenset(determinant), fd.dependent)


def _deduplicate_dependencies(
    dependencies: Iterable[FunctionalDependency],
) -> list[FunctionalDependency]:
    return sorted(set(dependencies), key=_dependency_sort_key)


def synthesize_5nf_projections(
    heading: Iterable[str],
    candidate_keys: Sequence[Iterable[str]],
    join_dependencies: Sequence[JoinDependency | Sequence[Iterable[str]]] | None = None,
    dependencies: Sequence[FunctionalDependency] | None = None,
) -> tuple[frozenset[str], ...]:
    """Synthesizes the minimal set of join dependency projections required to eliminate cyclic join anomalies (PJNF / 5NF).

    Given heading U and candidate keys K_1, ..., K_m:
    1. If candidate keys already imply the join dependencies or if no cyclic join anomaly exists,
       returns the trivial decomposition (frozenset(heading),).
    2. If a cyclic join dependency is present (either explicitly in join_dependencies, or formed by
       the cyclic candidate keys covering the heading), the relation is projected onto the components
       that eliminate the cyclic anomaly.
    3. Prunes non-minimal components: ensures no component is a subset of another, and no component
       can be omitted while maintaining attribute coverage and lossless join reconstruction.
    """
    sorted_heading = frozenset(heading)
    cand_keys = [frozenset(k) for k in candidate_keys]
    fds = list(dependencies) if dependencies else []

    if not cand_keys or len(sorted_heading) <= 2:
        return (sorted_heading,)

    if sorted_heading in cand_keys and not join_dependencies:
        return (sorted_heading,)

    candidate_projections = _anomalous_5nf_projections(sorted_heading, cand_keys, join_dependencies)
    if not candidate_projections:
        return (sorted_heading,)

    # Ensure all attributes are covered
    _cover_missing_attributes(candidate_projections, sorted_heading, cand_keys, fds)

    minimal = _maximal_unique_projections(candidate_projections)
    for p in list(minimal):
        if len(minimal) <= 2:
            break
        test_subset = [x for x in minimal if x != p]
        if frozenset().union(*test_subset) != sorted_heading:
            continue
        chase_res = chase_join_dependency(
            sorted_heading, fds, test_subset, candidate_keys=cand_keys
        )
        if chase_res.is_implied:
            minimal.remove(p)

    return tuple(sorted(minimal, key=lambda s: sorted(s)))


def _anomalous_5nf_projections(
    heading: frozenset[str],
    candidate_keys: Sequence[frozenset[str]],
    join_dependencies: Sequence[JoinDependency | Sequence[Iterable[str]]] | None,
) -> list[frozenset[str]]:
    projections: list[frozenset[str]] = []
    cyclic_keys = (
        frozenset().union(*candidate_keys) == heading
        and len(candidate_keys) >= 3
        and all(len(key) < len(heading) for key in candidate_keys)
    )
    if cyclic_keys and not is_5nf_implied_by_keys(heading, candidate_keys, candidate_keys):
        projections.extend(candidate_keys)
    for entry in join_dependencies or ():
        components = tuple(
            frozenset(component)
            for component in (entry.components if isinstance(entry, JoinDependency) else entry)
        )
        if any(component == heading for component in components):
            continue
        if not is_5nf_implied_by_keys(heading, candidate_keys, components):
            projections.extend(
                component for component in components if component not in projections
            )
    return projections


def _cover_missing_attributes(
    projections: list[frozenset[str]],
    heading: frozenset[str],
    candidate_keys: Sequence[frozenset[str]],
    dependencies: Sequence[FunctionalDependency],
) -> None:
    uncovered = heading - frozenset().union(*projections)
    for key in candidate_keys:
        covered = compute_attribute_closure(key, dependencies) & uncovered
        if covered:
            projections.append(key | covered)
            uncovered -= covered


def _maximal_unique_projections(
    projections: Sequence[frozenset[str]],
) -> list[frozenset[str]]:
    return list(
        dict.fromkeys(
            projection
            for projection in projections
            if not any(projection < other for other in projections)
        )
    )


def evaluate_join_dependency_on_relation(
    relation: Sequence[Mapping[str, Any]],
    join_dependency: JoinDependency,
) -> tuple[bool, int, list[dict[str, Any]]]:
    """Evaluates whether a tabular relation satisfies a join dependency losslessly.

    Returns:
        (is_lossless, spurious_tuple_count, spurious_tuples)
    """
    if not relation:
        return True, 0, []

    heading = sorted(join_dependency.heading)

    projections = [
        _project_relation(relation, component) for component in join_dependency.components
    ]
    joined = projections[0]
    for projection in projections[1:]:
        joined = _natural_join(joined, projection)
    unique_join = _deduplicate_rows(joined, heading)

    # Set of original relation tuples
    orig_tuples = {tuple(r.get(a) for a in heading) for r in relation}
    spurious = [r for r in unique_join if tuple(r.get(a) for a in heading) not in orig_tuples]

    is_lossless = len(spurious) == 0 and len(unique_join) == len(orig_tuples)
    return is_lossless, len(spurious), spurious


def _project_relation(
    relation: Sequence[Mapping[str, Any]], component: Iterable[str]
) -> list[dict[str, Any]]:
    attributes = sorted(component)
    return _deduplicate_rows(relation, attributes)


def _natural_join(
    left: Sequence[Mapping[str, Any]], right: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    joined: list[dict[str, Any]] = []
    for left_row in left:
        for right_row in right:
            shared = set(left_row).intersection(right_row)
            if all(left_row[key] == right_row[key] for key in shared):
                joined.append(dict(left_row) | dict(right_row))
    return joined


def _deduplicate_rows(
    rows: Sequence[Mapping[str, Any]], attributes: Sequence[str]
) -> list[dict[str, Any]]:
    seen: set[tuple[Any, ...]] = set()
    unique: list[dict[str, Any]] = []
    for row in rows:
        values = tuple(row.get(attribute) for attribute in attributes)
        if values not in seen:
            seen.add(values)
            unique.append({attribute: row.get(attribute) for attribute in attributes})
    return unique


def chase_join_dependency_confluence(
    heading: Iterable[str],
    dependencies: Sequence[FunctionalDependency],
    components: Sequence[Iterable[str]],
    candidate_keys: Iterable[Iterable[str]] | None = None,
    permutations: Sequence[Sequence[int]] | None = None,
) -> tuple[bool, int, list[frozenset[frozenset[tuple[int, str]]]]]:
    """Tests whether permuting FD application sequences preserves final tableau cell partitions identically."""
    from .relational_extensions import chase_tableau_cell_partition

    dep_list = list(dependencies)
    if not permutations:
        import itertools

        idx_perms: list[Sequence[int]] = list(itertools.permutations(range(len(dep_list))))
    else:
        idx_perms = [list(p) for p in permutations]

    partitions: list[frozenset[frozenset[tuple[int, str]]]] = []
    verdicts: list[bool] = []

    for p in idx_perms:
        ordered_fds = [dep_list[i] for i in p]
        res = chase_join_dependency(
            heading=heading,
            dependencies=ordered_fds,
            components=components,
            candidate_keys=candidate_keys,
            early_exit=False,
        )
        verdicts.append(res.is_implied)
        part = chase_tableau_cell_partition(res.final_tableau, heading)
        partitions.append(part)

    is_confluent = all(v == verdicts[0] for v in verdicts) and all(
        pt == partitions[0] for pt in partitions
    )
    return is_confluent, len(idx_perms), partitions


def check_lossless_decomposition(
    schema: RelationalSchema, sub_schemas: Sequence[frozenset[str]]
) -> tuple[bool, str | None]:
    """Verifies lossless join reconstruction using the Chase algorithm."""
    if len(sub_schemas) < 2:
        return True, None

    res = chase_join_dependency(
        heading=schema.attributes,
        dependencies=schema.dependencies,
        components=sub_schemas,
    )
    if res.is_implied:
        return True, None

    return False, "Chase algorithm found no row with complete attribute recovery"


def check_dependency_preservation(
    schema: RelationalSchema, sub_schemas: Sequence[frozenset[str]]
) -> tuple[bool, str | None]:
    """Verifies whether the decomposition preserves all functional dependencies."""
    # Projected dependencies: for each sub_schema R_i, find all FDs implied by schema that fit in R_i
    projected_fds = [
        dependency
        for sub_schema in sub_schemas
        for dependency in _projected_dependencies(schema, sub_schema)
    ]

    # Verify every original FD is implied by projected_fds
    for orig_fd in schema.dependencies:
        closure = compute_attribute_closure(orig_fd.determinant, projected_fds)
        if not orig_fd.dependent.issubset(closure):
            return (
                False,
                f"Dependency Preservation Violation: original dependency {orig_fd} is not implied by projections",
            )
    return True, None


def _projected_dependencies(
    schema: RelationalSchema, sub_schema: frozenset[str]
) -> list[FunctionalDependency]:
    determinants = (
        frozenset(combination)
        for size in range(1, len(sub_schema))
        for combination in combinations(sub_schema, size)
    )
    dependencies: list[FunctionalDependency] = []
    for determinant in determinants:
        dependent = (
            compute_attribute_closure(determinant, schema.dependencies) & sub_schema
        ) - determinant
        if dependent:
            dependencies.append(FunctionalDependency(determinant, frozenset(dependent)))
    return dependencies
