"""Lazy public exports; optional adapters load only on use."""

from importlib import import_module

_EXPORTS = {
    "Alg": ".alg",
    "Interval": ".alg",
    "alg_cmp": ".alg",
    "alg_equal": ".alg",
    "alg_sign_of": ".alg",
    "isolate": ".alg",
    "canonical_json": ".digest",
    "digest_of": ".digest",
    "sha256": ".digest",
    "ExactError": ".errors",
    "ExactRefusal": ".errors",
    "Matrix": ".linalg",
    "as_matrix": ".linalg",
    "char_poly": ".linalg",
    "det": ".linalg",
    "first_nonpositive_minor": ".linalg",
    "is_positive_definite": ".linalg",
    "is_symmetric": ".linalg",
    "leading_minors": ".linalg",
    "rank": ".linalg",
    "Poly": ".poly",
    "add": ".poly",
    "cauchy_bound": ".poly",
    "degree": ".poly",
    "deriv": ".poly",
    "divmod_poly": ".poly",
    "evaluate": ".poly",
    "gcd_poly": ".poly",
    "monic": ".poly",
    "mul": ".poly",
    "neg": ".poly",
    "root_count": ".poly",
    "squarefree": ".poly",
    "sturm_sequence": ".poly",
    "sub": ".poly",
    "trim": ".poly",
    "ONE": ".q",
    "ZERO": ".q",
    "Q": ".q",
    "fmt_q": ".q",
    "parse_q": ".q",
    "QI": ".qi",
    "fmt_qi": ".qi",
    "parse_qi": ".qi",
    "qi_from_q": ".qi",
    "RationalWire": ".wire",
    "RationalDualityGap": ".wire",
}
__all__ = list(_EXPORTS)


def __getattr__(name):
    if name not in _EXPORTS:
        raise AttributeError(name)
    value = getattr(import_module(_EXPORTS[name], __name__), name)
    globals()[name] = value
    return value
