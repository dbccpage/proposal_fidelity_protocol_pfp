"""Advanced relational normal forms and decompositions.

AuthorityEffect: None.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Iterable, Sequence

from .relational import (
    FunctionalDependency,
    RelationalSchema,
    check_bcnf,
    compute_attribute_closure,
    compute_minimal_cover,
)

# =============================================================================
# Part 2b: Advanced Relational Normal Forms & Decomposition Algorithms (Tranche 3)
# =============================================================================


def check_eknf(schema: RelationalSchema) -> tuple[bool, str | None]:
    """Elementary Key Normal Form (EKNF) - Carlo Zaniolo (1982).

    A schema is in EKNF if and only if for every non-trivial functional dependency X -> A:
    Either X is a superkey of R, OR A is an elementary key attribute.

    - A functional dependency X -> A is elementary (full) if no proper subset X' < X determines A.
    - A candidate key K is an elementary key if there exists some attribute A not in K such that
      K -> A is an elementary functional dependency (i.e. no proper subset of K determines A).
    - An attribute is an elementary key attribute if it belongs to at least one elementary key.
    """
    keys = schema.candidate_keys()
    if not keys:
        return False, "No candidate keys found"

    elementary_keys = {key for key in keys if _is_elementary_key(schema, key)}

    elementary_key_attributes = (
        frozenset().union(*elementary_keys) if elementary_keys else frozenset()
    )

    for fd in schema.dependencies:
        violation = _eknf_violation(schema, fd, elementary_key_attributes)
        if violation is not None:
            return False, violation
    return True, None


def _eknf_violation(
    schema: RelationalSchema,
    dependency: FunctionalDependency,
    elementary_attributes: frozenset[str],
) -> str | None:
    if dependency.is_trivial() or schema.is_superkey(dependency.determinant):
        return None
    attribute = next(
        (
            candidate
            for candidate in dependency.dependent - dependency.determinant
            if candidate not in elementary_attributes
        ),
        None,
    )
    if attribute is None:
        return None
    return (
        f"EKNF Violation: {set(dependency.determinant)} -> {attribute} "
        f"(determinant is not a superkey and attribute '{attribute}' "
        "is not an elementary key attribute)"
    )


def _is_elementary_key(schema: RelationalSchema, key: frozenset[str]) -> bool:
    other_attributes = schema.attributes - key
    if not other_attributes:
        return True
    return any(
        not any(attribute in schema.attribute_closure(key - {member}) for member in key)
        for attribute in other_attributes
    )


def gyo_reduction(
    edges: Sequence[Iterable[str]],
) -> tuple[bool, list[frozenset[str]], list[str]]:
    """Graham-Yu-Ozsoyoglu (GYO) algorithm for hypergraph alpha-acyclicity.

    Classifies join hypergraphs as alpha-acyclic or cyclic by iterative ear elimination.
    Returns (is_acyclic, remaining_edges, step_trace).
    """
    current = [frozenset(e) for e in edges if e]
    steps: list[str] = []

    changed = True
    while changed and len(current) > 1:
        changed = _eliminate_subset(current, steps) or _eliminate_ear(current, steps)

    is_acyclic = len(current) <= 1
    remaining = [] if is_acyclic else current
    return is_acyclic, remaining, steps


def _eliminate_subset(edges: list[frozenset[str]], steps: list[str]) -> bool:
    pairs = (
        (left_index, left, right_index, right)
        for left_index, left in enumerate(edges)
        for right_index, right in enumerate(edges)
    )
    match = next((entry for entry in pairs if entry[0] != entry[2] and entry[1] <= entry[3]), None)
    if match is None:
        return False
    index, edge, _, superset = match
    edges.pop(index)
    steps.append(f"eliminate_subset {sorted(edge)} <= {sorted(superset)}")
    return True


def _eliminate_ear(edges: list[frozenset[str]], steps: list[str]) -> bool:
    for index, edge in enumerate(edges):
        others = [candidate for other_index, candidate in enumerate(edges) if index != other_index]
        shared = {vertex for vertex in edge if any(vertex in other for other in others)}
        if any(shared <= candidate for candidate in others):
            edges.pop(index)
            steps.append(f"eliminate_ear {sorted(edge)} (shared {sorted(shared)})")
            return True
    return False


def synthesize_3nf_bernstein(schema: RelationalSchema) -> list[frozenset[str]]:
    """Bernstein's (1976) 3NF synthesis algorithm.

    Produces a dependency-preserving, lossless-join 3NF decomposition:
    1. Compute minimal cover F_c.
    2. Partition F_c by identical determinants.
    3. Form subschema X U Y for each determinant group.
    4. Ensure at least one candidate key is preserved for lossless join.
    5. Eliminate redundant subschemas.
    """
    min_cover = compute_minimal_cover(schema.dependencies)
    groups: dict[frozenset[str], set[str]] = {}
    for fd in min_cover:
        groups.setdefault(fd.determinant, set()).update(fd.dependent)

    subschemas = [det | dep for det, dep in groups.items()]

    cand_keys = schema.candidate_keys()
    if cand_keys:
        has_key = any(any(k <= s for s in subschemas) for k in cand_keys)
        if not has_key:
            first_key = sorted(cand_keys, key=lambda k: (len(k), tuple(sorted(k))))[0]
            subschemas.append(frozenset(first_key))

    pruned: list[frozenset[str]] = []
    for s1 in subschemas:
        if not any(s1 < s2 for s2 in subschemas):
            if s1 not in pruned:
                pruned.append(s1)

    return sorted(pruned, key=lambda s: (len(s), sorted(s)))


def project_functional_dependencies(
    dependencies: Iterable[FunctionalDependency],
    subset: frozenset[str],
) -> list[FunctionalDependency]:
    """Computes the exact projection of functional dependencies onto an attribute subset."""
    fds = list(dependencies)
    sub_attrs = sorted(subset)
    projected: list[FunctionalDependency] = []

    for r in range(1, len(sub_attrs)):
        for det_tuple in combinations(sub_attrs, r):
            det = frozenset(det_tuple)
            closure = compute_attribute_closure(det, fds)
            dep = (closure & subset) - det
            if dep:
                projected.append(FunctionalDependency(determinant=det, dependent=dep))

    return compute_minimal_cover(projected)


def decompose_bcnf_tree(schema: RelationalSchema) -> list[RelationalSchema]:
    """Tsou & Fischer (1982) BCNF decomposition tree algorithm.

    Recursively decomposes a schema into BCNF subschemas with lossless joins
    using deterministic lexicographical attribute tie-breaking over violating FDs.
    """
    ok_bcnf, _ = check_bcnf(schema)
    if ok_bcnf:
        return [schema]

    violating_fd: FunctionalDependency | None = None
    ordered_deps = sorted(
        schema.dependencies,
        key=lambda f: (tuple(sorted(f.determinant)), tuple(sorted(f.dependent))),
    )
    for fd in ordered_deps:
        if not fd.is_trivial() and not schema.is_superkey(fd.determinant):
            violating_fd = fd
            break

    if violating_fd is None:
        return [schema]

    x_closure = schema.attribute_closure(violating_fd.determinant)
    r1_attrs = x_closure
    r2_attrs = schema.attributes - (x_closure - violating_fd.determinant)

    if r1_attrs == schema.attributes or r2_attrs == schema.attributes:
        return [schema]

    r1_fds = project_functional_dependencies(schema.dependencies, r1_attrs)
    r2_fds = project_functional_dependencies(schema.dependencies, r2_attrs)

    s1 = RelationalSchema(attributes=r1_attrs, dependencies=frozenset(r1_fds))
    s2 = RelationalSchema(attributes=r2_attrs, dependencies=frozenset(r2_fds))

    return decompose_bcnf_tree(s1) + decompose_bcnf_tree(s2)


def pnf_nest(
    relation: Sequence[dict[str, Any]],
    group_keys: Iterable[str],
    nested_key: str,
    sub_attrs: Iterable[str],
) -> list[dict[str, Any]]:
    """Partitioned Normal Form (Roth, Korth, & Silberschatz 1988) nest operation."""
    g_keys = list(group_keys)
    s_attrs = list(sub_attrs)
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}

    for row in relation:
        key_tuple = tuple(row[k] for k in g_keys)
        child = {a: row[a] for a in s_attrs}
        grouped.setdefault(key_tuple, []).append(child)

    nested: list[dict[str, Any]] = []
    for key_tuple, children in grouped.items():
        entry = {k: v for k, v in zip(g_keys, key_tuple)}
        entry[nested_key] = children
        nested.append(entry)
    return nested


def pnf_unnest(
    nested_relation: Sequence[dict[str, Any]],
    nested_key: str,
) -> list[dict[str, Any]]:
    """Partitioned Normal Form unnest operation: reconstructs flat relation."""
    flat: list[dict[str, Any]] = []
    for row in nested_relation:
        parent_attrs = {k: v for k, v in row.items() if k != nested_key}
        children = row.get(nested_key, [])
        for child in children:
            flat.append({**parent_attrs, **child})
    return flat


def temporal_6nf_decompose(
    schema: RelationalSchema,
    temporal_key_attrs: Iterable[str] = (),
) -> list[RelationalSchema]:
    """Decomposes a schema into irreducible 6NF temporal relvars.

    Each 6NF relvar has a candidate key and at most one non-key attribute.
    """
    keys = schema.candidate_keys()
    if not keys:
        return [schema]
    primary_key = next(iter(keys))
    non_prime = sorted(schema.attributes - schema.prime_attributes())

    if len(non_prime) <= 1:
        return [schema]

    subschemas: list[RelationalSchema] = []
    for np in non_prime:
        sub_attrs = primary_key | {np}
        sub_fds = project_functional_dependencies(schema.dependencies, sub_attrs)
        subschemas.append(RelationalSchema(attributes=sub_attrs, dependencies=frozenset(sub_fds)))
    return subschemas


def temporal_interval_join(
    r1: Sequence[dict[str, Any]],
    r2: Sequence[dict[str, Any]],
    key_attrs: Iterable[str],
    time_attr: str,
) -> list[dict[str, Any]]:
    """Performs an interval join of two 6NF temporal relations."""
    k_attrs = list(key_attrs)
    joined: list[dict[str, Any]] = []
    for row1 in r1:
        for row2 in r2:
            match = all(row1[k] == row2[k] for k in k_attrs) and (
                row1[time_attr] == row2[time_attr]
            )
            if match:
                joined.append({**row1, **row2})
    return joined
