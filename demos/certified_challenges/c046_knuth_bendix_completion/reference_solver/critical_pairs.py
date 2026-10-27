# AuthorityEffect: None.
"""
Critical Pair Generator for Term Rewriting Systems in C046.
Computes all non-trivial critical pairs between rewrite rules.
"""

from typing import List, Tuple

from .term import Fun, Term, Var, mgu


def rename_vars(term: Term, prefix: str) -> Term:
    """Renames all variables in term with a given prefix to ensure disjoint variables."""
    if term.is_var():
        assert isinstance(term, Var)
        return Var(f"{prefix}_{term.name}")
    assert isinstance(term, Fun)
    return Fun(term.symbol, [rename_vars(a, prefix) for a in term.args])


def get_critical_pairs(rules: List[Tuple[Term, Term]]) -> List[Tuple[Term, Term, str]]:
    """
    Computes all critical pairs between rules in the TRS.
    Returns list of (t1, t2, source_info).
    """
    critical_pairs: List[Tuple[Term, Term, str]] = []

    for idx1, (l1, r1) in enumerate(rules):
        for idx2, (l2, r2) in enumerate(rules):
            # Rename variables of rule 2 to prevent clash
            l2_ren = rename_vars(l2, f"r{idx2}")
            r2_ren = rename_vars(r2, f"r{idx2}")

            # Iterate over all non-variable subterms of l1
            for path, subterm in l1.subterms_with_paths():
                if subterm.is_var():
                    continue

                # If same rule and root position, skip trivial overlap
                if idx1 == idx2 and not path:
                    continue

                sigma = mgu(subterm, l2_ren)
                if sigma is not None:
                    # Overlap found!
                    # Path 1: reduce whole l1 via rule 1 -> r1
                    c1 = r1.apply_subst(sigma)
                    # Path 2: replace subterm at path with r2_ren
                    l1_sigma = l1.apply_subst(sigma)
                    sub_repl = r2_ren.apply_subst(sigma)
                    c2 = l1_sigma.replace_at_path(path, sub_repl)

                    info = f"Rule {idx1} at path {path} with Rule {idx2}"
                    critical_pairs.append((c1, c2, info))

    return critical_pairs
