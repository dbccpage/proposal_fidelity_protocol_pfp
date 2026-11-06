"""Minimal exact symbolic engine for PO-000 (stdlib only).

Added 2026-08-31: this module replaces the package's former SymPy dependency
so that the deposit runs on the Python standard library plus NumPy alone.
It implements exactly the surface the PO-000 certificate rail uses:

* ``Rational`` is ``fractions.Fraction`` (exact rational arithmetic).
* ``Basic`` is a canonical-form symbolic expression: a Q-linear combination
  of monomials over a small atom set -- free symbols, square roots of
  square-free integers, ``exp(q)`` for rational ``q``, and ``pi``.
* ``Matrix`` is an exact dense matrix over ``Fraction``/``Basic`` entries
  with the rational linear algebra the certificates need (rank, inverse,
  nullspace, Gauss-Jordan solve, extraction, stacking, Jacobian).
* ``simplify``, ``Abs``, ``Max``, ``sqrt``, ``exp``, ``cos``, ``sin``,
  ``pi``, ``symbols``, ``Symbol`` mirror the SymPy names the modules used.

Equality of expressions is decided on the canonical form.  Order
comparisons on constant expressions are decided exactly: structural zero
first, then adaptive-precision interval arithmetic with ``Fraction``
endpoints (square roots via integer square roots, ``exp`` via Taylor
series with certified remainders, ``pi`` from a fixed 50-digit constant).
Comparisons involving free symbols raise ``TypeError``, matching the
SymPy behaviour the callers rely on.  Binary floats are rejected
throughout: the exact rail stays exact.
"""

from __future__ import annotations

from fractions import Fraction
from math import isqrt
from typing import Any, Iterable, Iterator, Mapping, Sequence, Union

Rational = Fraction

_PI_DIGITS = "314159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798"

# ---------------------------------------------------------------------------
# scalar coercion helpers
# ---------------------------------------------------------------------------


def _coerce_scalar(value: object) -> Any:
    """Coerce to Fraction or Basic; reject binary floats."""

    if isinstance(value, Basic):
        return value._as_fraction_or_self()
    if isinstance(value, bool):
        return Fraction(int(value))
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Fraction):
        return value
    if isinstance(value, float):
        raise TypeError("exact symbolic arithmetic rejects float; use an exact scalar")
    raise TypeError(f"cannot coerce {type(value).__name__} into an exact scalar")


def _try_coerce(value: object) -> Any | None:
    try:
        return _coerce_scalar(value)
    except TypeError:
        return None


def _squarefree(n: int) -> tuple[int, int]:
    """Return (outside, radicand) with n = outside**2 * radicand, radicand squarefree."""

    if n < 0:
        raise ValueError("square roots of negative values are not supported")
    outside = 1
    radicand = 1
    remaining = n
    factor = 2
    while factor * factor <= remaining:
        if remaining % factor == 0:
            count = 0
            while remaining % factor == 0:
                remaining //= factor
                count += 1
            outside *= factor ** (count // 2)
            if count % 2:
                radicand *= factor
        factor += 1 if factor == 2 else 2
    radicand *= remaining
    return outside, radicand


# ---------------------------------------------------------------------------
# atoms and monomials
#
# atom keys (all tuples, totally ordered by their repr-stable contents):
#   ("sym", name)          free symbol, integer exponent >= 1
#   ("surd", n)            sqrt(n), n squarefree int > 1, exponent always 1
#   ("exp", p, q)          exp(p/q), nonzero rational, exponent always 1
#   ("pi",)                pi, integer exponent >= 1
# a monomial is a tuple of (atom, exponent) pairs sorted by atom
# ---------------------------------------------------------------------------

_Atom = tuple
_Monomial = tuple


def _atom_sort_key(pair: tuple[_Atom, int]) -> tuple:
    atom, exponent = pair
    return (atom[0], tuple(str(part) for part in atom[1:]), exponent)


def _normalize_monomial(pairs: Iterable[tuple[_Atom, int]]) -> tuple[Fraction, _Monomial]:
    """Combine atom powers, applying surd and exp reduction rules."""

    coefficient = Fraction(1)
    sym_powers: dict[_Atom, int] = {}
    surd_radicand = 1
    exp_argument = Fraction(0)
    pi_power = 0
    for atom, exponent in pairs:
        if exponent == 0:
            continue
        kind = atom[0]
        if kind == "sym":
            sym_powers[atom] = sym_powers.get(atom, 0) + exponent
        elif kind == "surd":
            if exponent < 0:
                raise ValueError("negative surd powers are not supported")
            radicand = atom[1]
            coefficient *= Fraction(radicand ** (exponent // 2))
            if exponent % 2:
                merged = surd_radicand * radicand
                outside, reduced = _squarefree(merged)
                coefficient *= outside
                surd_radicand = reduced
        elif kind == "exp":
            exp_argument += Fraction(atom[1], atom[2]) * exponent
        elif kind == "pi":
            pi_power += exponent
        else:  # pragma: no cover - internal invariant
            raise ValueError(f"unknown atom kind {kind!r}")
    result: list[tuple[_Atom, int]] = []
    for atom, exponent in sym_powers.items():
        if exponent < 0:
            raise ValueError("negative symbol powers are not supported")
        if exponent:
            result.append((atom, exponent))
    if surd_radicand > 1:
        result.append((("surd", surd_radicand), 1))
    if exp_argument != 0:
        result.append((("exp", exp_argument.numerator, exp_argument.denominator), 1))
    if pi_power:
        if pi_power < 0:
            raise ValueError("negative pi powers are not supported")
        result.append((("pi",), pi_power))
    result.sort(key=_atom_sort_key)
    return coefficient, tuple(result)


class Basic:
    """A canonical exact symbolic expression."""

    __slots__ = ("_terms",)
    _terms: dict[_Monomial, Fraction]

    def __init__(self, terms: Mapping[_Monomial, Fraction] | None = None):
        cleaned = {
            monomial: coefficient
            for monomial, coefficient in (terms or {}).items()
            if coefficient != 0
        }
        object.__setattr__(self, "_terms", cleaned)

    # -- construction helpers ------------------------------------------------

    @staticmethod
    def _from_terms(terms: Mapping[_Monomial, Fraction]) -> Any:
        expr = Basic(terms)
        return expr._as_fraction_or_self()

    @staticmethod
    def _constant(value: Fraction) -> "Basic":
        if value == 0:
            return Basic({})
        return Basic({(): value})

    @staticmethod
    def _atom(atom: _Atom, exponent: int = 1) -> "Basic":
        coefficient, monomial = _normalize_monomial([(atom, exponent)])
        return Basic({monomial: coefficient})

    def _as_fraction_or_self(self) -> Any:
        """Collapse a constant expression to a plain Fraction."""

        if not self._terms:
            return Fraction(0)
        if len(self._terms) == 1 and () in self._terms:
            return self._terms[()]
        return self

    @staticmethod
    def _lift(value: object) -> "Basic":
        if isinstance(value, Basic):
            return value
        coerced = _coerce_scalar(value)
        if isinstance(coerced, Basic):
            return coerced
        return Basic._constant(coerced)

    # -- structure -----------------------------------------------------------

    @property
    def free_symbols(self) -> set:
        names = set()
        for monomial in self._terms:
            for atom, _exponent in monomial:
                if atom[0] == "sym":
                    names.add(Basic._atom(atom))
        return names

    def _is_constant(self) -> bool:
        return all(
            atom[0] != "sym" for monomial in self._terms for atom, _exp in monomial
        )

    def _symbol_name(self) -> str | None:
        if len(self._terms) == 1:
            ((monomial, coefficient),) = self._terms.items()
            if (
                coefficient == 1
                and len(monomial) == 1
                and monomial[0][0][0] == "sym"
                and monomial[0][1] == 1
            ):
                return monomial[0][0][1]
        return None

    # -- arithmetic ----------------------------------------------------------

    def __add__(self, other: object) -> Any:
        if _try_coerce(other) is None:
            return NotImplemented
        left = self._terms
        right = Basic._lift(other)._terms
        merged = dict(left)
        for monomial, coefficient in right.items():
            merged[monomial] = merged.get(monomial, Fraction(0)) + coefficient
        return Basic._from_terms(merged)

    __radd__ = __add__

    def __sub__(self, other: object) -> Any:
        if _try_coerce(other) is None:
            return NotImplemented
        return self.__add__(-Basic._lift(other))

    def __rsub__(self, other: object) -> Any:
        if _try_coerce(other) is None:
            return NotImplemented
        return Basic._lift(other).__add__(-self)

    def __neg__(self) -> Any:
        return Basic._from_terms(
            {monomial: -coefficient for monomial, coefficient in self._terms.items()}
        )

    def __pos__(self) -> Any:
        return self

    def __mul__(self, other: object) -> Any:
        if _try_coerce(other) is None:
            return NotImplemented
        right = Basic._lift(other)
        product: dict[_Monomial, Fraction] = {}
        for mono_a, coeff_a in self._terms.items():
            for mono_b, coeff_b in right._terms.items():
                extra, monomial = _normalize_monomial(list(mono_a) + list(mono_b))
                coefficient = coeff_a * coeff_b * extra
                product[monomial] = product.get(monomial, Fraction(0)) + coefficient
        return Basic._from_terms(product)

    __rmul__ = __mul__

    def __truediv__(self, other: object) -> Any:
        divisor = _try_coerce(other)
        if divisor is None:
            return NotImplemented
        if isinstance(divisor, Basic):
            collapsed = divisor._as_fraction_or_self()
            if isinstance(collapsed, Basic):
                raise TypeError("exact symbolic division by a symbolic value is not supported")
            divisor = collapsed
        if divisor == 0:
            raise ZeroDivisionError("division by zero")
        return self.__mul__(Fraction(1) / divisor)

    def __rtruediv__(self, other: object) -> Any:
        raise TypeError("exact symbolic division by a symbolic value is not supported")

    def __pow__(self, exponent: object) -> Any:
        if isinstance(exponent, bool) or not isinstance(exponent, int):
            raise TypeError("exact symbolic powers must be nonnegative integers")
        if exponent < 0:
            raise TypeError("exact symbolic powers must be nonnegative integers")
        result: Any = Fraction(1)
        for _ in range(exponent):
            result = self.__mul__(result)
        return result

    def __abs__(self) -> Any:
        sign = self._sign()
        if sign < 0:
            return -self
        return self

    # -- calculus and substitution -------------------------------------------

    def diff(self, symbol: "Basic") -> Any:
        name = symbol._symbol_name() if isinstance(symbol, Basic) else None
        if name is None:
            raise TypeError("differentiation requires a plain symbol")
        atom = ("sym", name)
        derivative: dict[_Monomial, Fraction] = {}
        for monomial, coefficient in self._terms.items():
            for index, (candidate, exponent) in enumerate(monomial):
                if candidate == atom:
                    rest = list(monomial[:index]) + list(monomial[index + 1:])
                    if exponent > 1:
                        rest.append((candidate, exponent - 1))
                    extra, reduced = _normalize_monomial(rest)
                    value = coefficient * exponent * extra
                    derivative[reduced] = derivative.get(reduced, Fraction(0)) + value
                    break
        return Basic._from_terms(derivative)

    def subs(self, mapping: Mapping[object, object]) -> Any:
        replacements: dict[str, Any] = {}
        for key, value in mapping.items():
            if isinstance(key, Basic):
                name = key._symbol_name()
            elif isinstance(key, str):
                name = key
            else:
                name = None
            if name is None:
                raise TypeError("substitution keys must be plain symbols")
            replacements[name] = _coerce_scalar(value)
        total: Any = Fraction(0)
        for monomial, coefficient in self._terms.items():
            term: Any = coefficient
            for atom, exponent in monomial:
                if atom[0] == "sym" and atom[1] in replacements:
                    base = replacements[atom[1]]
                    for _ in range(exponent):
                        term = term * base if isinstance(term, Basic) else base * term
                else:
                    factor = Basic._atom(atom, exponent)
                    term = factor * term
            total = term + total if isinstance(term, Basic) else total + term
        return simplify(total)

    # -- comparisons ---------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        coerced = _try_coerce(other)
        if coerced is None:
            return NotImplemented
        difference = self.__sub__(coerced)
        if isinstance(difference, Basic):
            return not difference._terms
        return difference == 0

    def __ne__(self, other: object) -> bool:
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def __hash__(self) -> int:
        collapsed = self._as_fraction_or_self()
        if isinstance(collapsed, Fraction):
            return hash(collapsed)
        return hash(frozenset(self._terms.items()))

    def _sign(self) -> int:
        """Exact sign of a constant expression; TypeError on free symbols."""

        if not self._is_constant():
            raise TypeError("cannot determine the sign of an expression with free symbols")
        if not self._terms:
            return 0
        if set(self._terms) == {()}:
            value = self._terms[()]
            return (value > 0) - (value < 0)
        for precision in (30, 60, 120, 240, 480, 960):
            low, high = self._interval(precision)
            if low > 0:
                return 1
            if high < 0:
                return -1
        raise ArithmeticError(
            "interval refinement failed to separate a structurally nonzero value from zero"
        )

    def _interval(self, precision: int) -> tuple[Fraction, Fraction]:
        low_total = Fraction(0)
        high_total = Fraction(0)
        for monomial, coefficient in self._terms.items():
            low = Fraction(1)
            high = Fraction(1)
            for atom, exponent in monomial:
                atom_low, atom_high = _atom_interval(atom, precision)
                for _ in range(exponent):
                    low, high = low * atom_low, high * atom_high
            if coefficient >= 0:
                low_total += coefficient * low
                high_total += coefficient * high
            else:
                low_total += coefficient * high
                high_total += coefficient * low
        return low_total, high_total

    def _compare(self, other: object, operation: str) -> bool:
        coerced = _try_coerce(other)
        if coerced is None:
            raise TypeError(
                f"cannot compare an exact symbolic value with {type(other).__name__}"
            )
        difference = Basic._lift(self.__sub__(coerced))
        sign = difference._sign()
        if operation == "lt":
            return sign < 0
        if operation == "le":
            return sign <= 0
        if operation == "gt":
            return sign > 0
        return sign >= 0

    def __lt__(self, other: object) -> bool:
        return self._compare(other, "lt")

    def __le__(self, other: object) -> bool:
        return self._compare(other, "le")

    def __gt__(self, other: object) -> bool:
        return self._compare(other, "gt")

    def __ge__(self, other: object) -> bool:
        return self._compare(other, "ge")

    # -- rendering -----------------------------------------------------------

    @staticmethod
    def _render_atom(atom: _Atom, exponent: int) -> str:
        kind = atom[0]
        if kind == "sym":
            base = atom[1]
        elif kind == "surd":
            base = f"sqrt({atom[1]})"
        elif kind == "exp":
            base = f"exp({Fraction(atom[1], atom[2])})"
        else:
            base = "pi"
        if exponent == 1:
            return base
        return f"{base}**{exponent}"

    def __str__(self) -> str:
        if not self._terms:
            return "0"
        rendered: list[str] = []
        ordered = sorted(
            self._terms.items(),
            key=lambda item: tuple(_atom_sort_key(pair) for pair in item[0]),
        )
        for monomial, coefficient in ordered:
            parts = [Basic._render_atom(atom, exponent) for atom, exponent in monomial]
            if not parts:
                body = str(abs(coefficient))
            elif abs(coefficient) == 1:
                body = "*".join(parts)
            else:
                body = "*".join([str(abs(coefficient))] + parts)
            if not rendered:
                rendered.append(body if coefficient > 0 else f"-{body}")
            else:
                rendered.append(f"+ {body}" if coefficient > 0 else f"- {body}")
        return " ".join(rendered)

    def __repr__(self) -> str:
        return str(self)


# ---------------------------------------------------------------------------
# certified interval bounds for numeric atoms
# ---------------------------------------------------------------------------


def _sqrt_interval(value: Fraction, precision: int) -> tuple[Fraction, Fraction]:
    scale = 1 << precision
    scaled = value * scale * scale
    root = isqrt(scaled.numerator // scaled.denominator)
    low = Fraction(root, scale)
    high = Fraction(root + 2, scale)
    return low, high


def _exp_interval(argument: Fraction, precision: int) -> tuple[Fraction, Fraction]:
    if argument < 0:
        low, high = _exp_interval(-argument, precision + 8)
        return Fraction(1) / high, Fraction(1) / low
    halvings = 0
    reduced = argument
    while reduced > Fraction(1, 2):
        reduced /= 2
        halvings += 1
    total = Fraction(1)
    term = Fraction(1)
    index = 0
    tolerance = Fraction(1, 1 << (precision + 4 * (halvings + 1)))
    while True:
        index += 1
        term = term * reduced / index
        total += term
        if term < tolerance:
            break
    low, high = total, total + 2 * term
    for _ in range(halvings):
        low, high = low * low, high * high
    return low, high


def _pi_interval(precision: int) -> tuple[Fraction, Fraction]:
    digits = min(2 + precision // 3, len(_PI_DIGITS) - 1)
    scale = 10 ** digits
    approx = int(_PI_DIGITS[: digits + 1])
    return Fraction(approx, scale), Fraction(approx + 1, scale)


def _atom_interval(atom: _Atom, precision: int) -> tuple[Fraction, Fraction]:
    kind = atom[0]
    if kind == "surd":
        return _sqrt_interval(Fraction(atom[1]), precision)
    if kind == "exp":
        return _exp_interval(Fraction(atom[1], atom[2]), precision)
    if kind == "pi":
        return _pi_interval(precision)
    raise TypeError("cannot bound an expression with free symbols")


# ---------------------------------------------------------------------------
# public scalar functions
# ---------------------------------------------------------------------------


def simplify(value: object) -> Any:
    """Return the canonical form of an exact scalar (idempotent)."""

    coerced = _coerce_scalar(value)
    if isinstance(coerced, Basic):
        return coerced._as_fraction_or_self()
    return coerced


def Abs(value: object) -> Any:
    coerced = _coerce_scalar(value)
    if isinstance(coerced, Fraction):
        return abs(coerced)
    return abs(coerced)


def Max(*values: object) -> Any:
    if not values:
        raise TypeError("Max requires at least one argument")
    best = simplify(values[0])
    for candidate in values[1:]:
        challenger = simplify(candidate)
        if _greater(challenger, best):
            best = challenger
    return best


def _greater(left: Any, right: Any) -> bool:
    if isinstance(left, Basic) or isinstance(right, Basic):
        return bool(Basic._lift(left)._compare(right, "gt"))
    return left > right


def sqrt(value: object) -> Any:
    coerced = simplify(value)
    if isinstance(coerced, Basic):
        raise TypeError("sqrt of a non-constant symbolic value is not supported")
    if coerced < 0:
        raise ValueError("sqrt of a negative value is not supported")
    if coerced == 0:
        return Fraction(0)
    combined = coerced.numerator * coerced.denominator
    outside, radicand = _squarefree(combined)
    scale = Fraction(outside, coerced.denominator)
    if radicand == 1:
        return scale
    return Basic({((("surd", radicand), 1),): scale})


def exp(value: object) -> Any:
    coerced = simplify(value)
    if isinstance(coerced, Basic):
        raise TypeError("exp of a non-constant symbolic value is not supported")
    if coerced == 0:
        return Fraction(1)
    return Basic._atom(("exp", coerced.numerator, coerced.denominator))


def _pi_multiple(value: Any) -> Fraction | None:
    """Return q when value == q*pi (or 0), else None."""

    if isinstance(value, Fraction):
        return Fraction(0) if value == 0 else None
    if not isinstance(value, Basic):
        return None
    if len(value._terms) != 1:
        return None
    ((monomial, coefficient),) = value._terms.items()
    if monomial == ((("pi",), 1),):
        return coefficient
    return None


def cos(value: object) -> Any:
    multiple = _pi_multiple(simplify(value))
    if multiple is None:
        raise TypeError("cos is supported at rational multiples of pi/2 only")
    reduced = multiple % 2
    table = {
        Fraction(0): Fraction(1),
        Fraction(1, 2): Fraction(0),
        Fraction(1): Fraction(-1),
        Fraction(3, 2): Fraction(0),
    }
    if reduced not in table:
        raise TypeError("cos is supported at rational multiples of pi/2 only")
    return table[reduced]


def sin(value: object) -> Any:
    multiple = _pi_multiple(simplify(value))
    if multiple is None:
        raise TypeError("sin is supported at rational multiples of pi/2 only")
    reduced = multiple % 2
    table = {
        Fraction(0): Fraction(0),
        Fraction(1, 2): Fraction(1),
        Fraction(1): Fraction(0),
        Fraction(3, 2): Fraction(-1),
    }
    if reduced not in table:
        raise TypeError("sin is supported at rational multiples of pi/2 only")
    return table[reduced]


def Symbol(name: str, **_assumptions: object) -> Basic:
    if not isinstance(name, str) or not name:
        raise TypeError("symbol names must be nonempty strings")
    return Basic._atom(("sym", name))


def symbols(names: str, **assumptions: object) -> Any:
    parts = names.replace(",", " ").split()
    created = tuple(Symbol(part, **assumptions) for part in parts)
    if len(created) == 1:
        return created[0]
    return created


pi = Basic._atom(("pi",))

ExactScalar = Union[Fraction, Basic]


# ---------------------------------------------------------------------------
# exact dense matrices
# ---------------------------------------------------------------------------


class Matrix:
    """Exact dense matrix over Fraction/Basic entries."""

    __slots__ = ("_rows", "_cols", "_data")
    _rows: int
    _cols: int
    _data: list

    def __init__(self, *args: object):
        if len(args) == 3:
            rows, cols, flat = args
            if not isinstance(rows, int) or not isinstance(cols, int):
                raise TypeError("matrix dimensions must be integers")
            if not isinstance(flat, (list, tuple)):
                raise TypeError("matrix data must be a list or tuple")
            data = [simplify(value) for value in flat]
            if len(data) != rows * cols:
                raise ValueError("matrix data length does not match its dimensions")
            self._init(rows, cols, data)
            return
        if len(args) != 1:
            raise TypeError("Matrix expects one data argument or (rows, cols, flat)")
        source = args[0]
        if isinstance(source, Matrix):
            self._init(source._rows, source._cols, list(source._data))
            return
        if not isinstance(source, (list, tuple)):
            raise TypeError(f"cannot build a Matrix from {type(source).__name__}")
        if not source:
            self._init(0, 0, [])
            return
        if all(isinstance(row, (list, tuple)) for row in source):
            width = len(source[0])
            if any(len(row) != width for row in source):
                raise ValueError("matrix rows must have equal length")
            data = [simplify(value) for row in source for value in row]
            self._init(len(source), width, data)
            return
        data = [simplify(value) for value in source]
        self._init(len(data), 1, data)

    def _init(self, rows: int, cols: int, data: list) -> None:
        object.__setattr__(self, "_rows", rows)
        object.__setattr__(self, "_cols", cols)
        object.__setattr__(self, "_data", data)

    # -- constructors --------------------------------------------------------

    @staticmethod
    def zeros(rows: int, cols: int | None = None) -> "Matrix":
        if cols is None:
            cols = rows
        return Matrix(rows, cols, [Fraction(0)] * (rows * cols))

    @staticmethod
    def eye(size: int) -> "Matrix":
        result = Matrix.zeros(size)
        for index in range(size):
            result._data[index * size + index] = Fraction(1)
        return result

    @staticmethod
    def vstack(*matrices: "Matrix") -> "Matrix":
        if not matrices:
            return Matrix.zeros(0, 0)
        cols = matrices[0]._cols
        if any(matrix._cols != cols for matrix in matrices):
            raise ValueError("vstack requires equal column counts")
        data: list = []
        rows = 0
        for matrix in matrices:
            data.extend(matrix._data)
            rows += matrix._rows
        return Matrix(rows, cols, data)

    # -- basic properties ----------------------------------------------------

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def shape(self) -> tuple[int, int]:
        return (self._rows, self._cols)

    @property
    def T(self) -> "Matrix":
        data = [
            self._data[row * self._cols + col]
            for col in range(self._cols)
            for row in range(self._rows)
        ]
        return Matrix(self._cols, self._rows, data)

    @property
    def free_symbols(self) -> set:
        found: set = set()
        for value in self._data:
            if isinstance(value, Basic):
                found |= value.free_symbols
        return found

    # -- element access ------------------------------------------------------

    def __getitem__(self, key: object) -> Any:
        if isinstance(key, int):
            return self._data[key]
        if isinstance(key, tuple) and len(key) == 2:
            row_key, col_key = key
            if isinstance(row_key, int) and isinstance(col_key, int):
                if not (0 <= row_key < self._rows and 0 <= col_key < self._cols):
                    raise IndexError("matrix index out of range")
                return self._data[row_key * self._cols + col_key]
            row_indices = self._expand_index(row_key, self._rows)
            col_indices = self._expand_index(col_key, self._cols)
            return self.extract(row_indices, col_indices)
        raise TypeError("unsupported matrix index")

    @staticmethod
    def _expand_index(key: object, size: int) -> Sequence[int]:
        if isinstance(key, int):
            return (key,)
        if isinstance(key, slice):
            return range(*key.indices(size))
        if isinstance(key, (list, tuple, range)):
            return list(key)
        raise TypeError("unsupported matrix index component")

    def __setitem__(self, key: tuple[int, int], value: object) -> None:
        row, col = key
        self._data[row * self._cols + col] = simplify(value)

    def __iter__(self) -> Iterator:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def row(self, index: int) -> list:
        start = index * self._cols
        return list(self._data[start : start + self._cols])

    def extract(self, row_indices: Sequence[int], col_indices: Sequence[int]) -> "Matrix":
        data = [
            self._data[row * self._cols + col]
            for row in row_indices
            for col in col_indices
        ]
        return Matrix(len(list(row_indices)), len(list(col_indices)), data)

    def row_join(self, other: "Matrix") -> "Matrix":
        if self._rows != other._rows:
            raise ValueError("row_join requires equal row counts")
        data: list = []
        for row in range(self._rows):
            data.extend(self.row(row))
            data.extend(other.row(row))
        return Matrix(self._rows, self._cols + other._cols, data)

    # -- arithmetic ----------------------------------------------------------

    def _check_same_shape(self, other: "Matrix") -> None:
        if self.shape != other.shape:
            raise ValueError(f"matrix shapes {self.shape} and {other.shape} differ")

    def __add__(self, other: object) -> "Matrix":
        if not isinstance(other, Matrix):
            return NotImplemented
        self._check_same_shape(other)
        return Matrix(
            self._rows,
            self._cols,
            [a + b for a, b in zip(self._data, other._data)],
        )

    def __sub__(self, other: object) -> "Matrix":
        if not isinstance(other, Matrix):
            return NotImplemented
        self._check_same_shape(other)
        return Matrix(
            self._rows,
            self._cols,
            [a - b for a, b in zip(self._data, other._data)],
        )

    def __neg__(self) -> "Matrix":
        return Matrix(self._rows, self._cols, [-value for value in self._data])

    def __mul__(self, other: object) -> "Matrix":
        if isinstance(other, Matrix):
            if self._cols != other._rows:
                raise ValueError(
                    f"matrix shapes {self.shape} and {other.shape} do not compose"
                )
            data: list = []
            for row in range(self._rows):
                for col in range(other._cols):
                    total: Any = Fraction(0)
                    for inner in range(self._cols):
                        total = total + self._data[row * self._cols + inner] * other._data[
                            inner * other._cols + col
                        ]
                    data.append(simplify(total))
            return Matrix(self._rows, other._cols, data)
        scalar = _try_coerce(other)
        if scalar is None:
            return NotImplemented
        return Matrix(
            self._rows, self._cols, [simplify(value * scalar) for value in self._data]
        )

    def __rmul__(self, other: object) -> "Matrix":
        scalar = _try_coerce(other)
        if scalar is None:
            return NotImplemented
        return self.__mul__(other)

    def __truediv__(self, other: object) -> "Matrix":
        scalar = _try_coerce(other)
        if scalar is None:
            return NotImplemented
        return Matrix(
            self._rows, self._cols, [simplify(value / scalar) for value in self._data]
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Matrix):
            return NotImplemented
        return self.shape == other.shape and all(
            _entries_equal(a, b) for a, b in zip(self._data, other._data)
        )

    def __ne__(self, other: object) -> bool:
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal

    def __hash__(self) -> int:
        return hash((self._rows, self._cols, tuple(self._data)))

    # -- functional helpers --------------------------------------------------

    def applyfunc(self, function) -> "Matrix":
        return Matrix(self._rows, self._cols, [function(value) for value in self._data])

    def subs(self, mapping: Mapping[object, object]) -> "Matrix":
        return self.applyfunc(
            lambda value: value.subs(mapping) if isinstance(value, Basic) else value
        )

    def jacobian(self, variables: Sequence[Basic]) -> "Matrix":
        if self._cols != 1 and self._rows != 1:
            raise ValueError("jacobian requires a vector")
        entries = list(self._data)
        data: list = []
        for value in entries:
            for variable in variables:
                if isinstance(value, Basic):
                    data.append(simplify(value.diff(variable)))
                else:
                    data.append(Fraction(0))
        return Matrix(len(entries), len(list(variables)), data)

    # -- rational linear algebra ---------------------------------------------

    def _rational_rows(self) -> list[list[Fraction]]:
        rows: list[list[Fraction]] = []
        for row in range(self._rows):
            current: list[Fraction] = []
            for col in range(self._cols):
                value = self._data[row * self._cols + col]
                if isinstance(value, Basic):
                    raise TypeError(
                        "rational linear algebra requires rational matrix entries"
                    )
                current.append(value)
            rows.append(current)
        return rows

    @staticmethod
    def _rref(rows: list[list[Fraction]]) -> tuple[list[list[Fraction]], list[int]]:
        matrix = [list(row) for row in rows]
        row_count = len(matrix)
        col_count = len(matrix[0]) if matrix else 0
        pivots: list[int] = []
        pivot_row = 0
        for col in range(col_count):
            chosen = None
            for row in range(pivot_row, row_count):
                if matrix[row][col] != 0:
                    chosen = row
                    break
            if chosen is None:
                continue
            matrix[pivot_row], matrix[chosen] = matrix[chosen], matrix[pivot_row]
            pivot_value = matrix[pivot_row][col]
            matrix[pivot_row] = [value / pivot_value for value in matrix[pivot_row]]
            for row in range(row_count):
                if row != pivot_row and matrix[row][col] != 0:
                    factor = matrix[row][col]
                    matrix[row] = [
                        value - factor * pivot
                        for value, pivot in zip(matrix[row], matrix[pivot_row])
                    ]
            pivots.append(col)
            pivot_row += 1
            if pivot_row == row_count:
                break
        return matrix, pivots

    def rank(self) -> int:
        if self._rows == 0 or self._cols == 0:
            return 0
        _reduced, pivots = Matrix._rref(self._rational_rows())
        return len(pivots)

    def inv(self) -> "Matrix":
        if self._rows != self._cols:
            raise ValueError("only square matrices are invertible")
        size = self._rows
        augmented = [
            row + [Fraction(1) if index == position else Fraction(0) for position in range(size)]
            for index, row in enumerate(self._rational_rows())
        ]
        reduced, pivots = Matrix._rref(augmented)
        if pivots[:size] != list(range(size)) or len(pivots) < size:
            raise ValueError("matrix is not invertible")
        data = [value for row in reduced for value in row[size:]]
        return Matrix(size, size, data)

    def nullspace(self) -> list["Matrix"]:
        if self._cols == 0:
            return []
        if self._rows == 0:
            return [
                Matrix.eye(self._cols)[:, (index,)] for index in range(self._cols)
            ]
        reduced, pivots = Matrix._rref(self._rational_rows())
        free_columns = [col for col in range(self._cols) if col not in pivots]
        basis: list[Matrix] = []
        for free in free_columns:
            vector = [Fraction(0)] * self._cols
            vector[free] = Fraction(1)
            for pivot_index, pivot_col in enumerate(pivots):
                vector[pivot_col] = -reduced[pivot_index][free]
            basis.append(Matrix(self._cols, 1, vector))
        return basis

    def gauss_jordan_solve(self, rhs: "Matrix") -> tuple["Matrix", "Matrix"]:
        if rhs.rows != self._rows or rhs.cols != 1:
            raise ValueError("gauss_jordan_solve expects a matching column vector")
        augmented = [
            row + [value]
            for row, value in zip(self._rational_rows(), rhs._rational_rows_flat())
        ]
        if not augmented:
            return Matrix.zeros(self._cols, 1), Matrix.zeros(self._cols, 1)
        reduced, pivots = Matrix._rref(augmented)
        pivot_cols = [col for col in pivots if col < self._cols]
        if len(pivot_cols) != len(pivots):
            raise ValueError("Linear system has no solution")
        solution = [Fraction(0)] * self._cols
        for pivot_index, pivot_col in enumerate(pivot_cols):
            solution[pivot_col] = reduced[pivot_index][self._cols]
        free_count = self._cols - len(pivot_cols)
        return Matrix(self._cols, 1, solution), Matrix.zeros(free_count, 1)

    def _rational_rows_flat(self) -> list[Fraction]:
        return [value for row in self._rational_rows() for value in row]

    # -- rendering -----------------------------------------------------------

    def __str__(self) -> str:
        rows = [
            "[" + ", ".join(str(value) for value in self.row(index)) + "]"
            for index in range(self._rows)
        ]
        return "Matrix([" + ", ".join(rows) + "])"

    def __repr__(self) -> str:
        return str(self)


def _entries_equal(left: Any, right: Any) -> bool:
    if isinstance(left, Basic) or isinstance(right, Basic):
        return bool(Basic._lift(left).__eq__(right))
    return left == right


MatrixBase = Matrix
