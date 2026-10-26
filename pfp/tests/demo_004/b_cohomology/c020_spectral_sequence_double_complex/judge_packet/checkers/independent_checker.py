"""Independent filtered-complex checker for C020.

This checker intentionally imports neither the reference solver nor the first
checker. It rebuilds the total complex over F2, computes the filtered
subquotients defining E_r, and verifies the complete reported certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class IndependentCheckError(ValueError):
    """Raised when a case cannot be interpreted as a bounded F2 complex."""


def _basis(vectors: Iterable[int]) -> list[int]:
    """Return a deterministic reduced XOR basis of bit vectors."""
    pivots: dict[int, int] = {}
    for original in vectors:
        value = int(original)
        while value:
            pivot = value.bit_length() - 1
            incumbent = pivots.get(pivot)
            if incumbent is not None:
                value ^= incumbent
                continue
            for other_pivot, other in list(pivots.items()):
                if (other >> pivot) & 1:
                    pivots[other_pivot] = other ^ value
            pivots[pivot] = value
            break
    return [pivots[pivot] for pivot in sorted(pivots, reverse=True)]


def _rank(vectors: Iterable[int]) -> int:
    return len(_basis(vectors))


def _nullspace(row_masks: Iterable[int], ncols: int) -> list[int]:
    """Compute a basis for the nullspace of an F2 matrix encoded by rows."""
    mask = (1 << ncols) - 1
    rows = [int(row) & mask for row in row_masks if int(row)]
    pivot_cols: list[int] = []
    pivot_row = 0
    for col in range(ncols):
        found = next(
            (idx for idx in range(pivot_row, len(rows)) if (rows[idx] >> col) & 1),
            None,
        )
        if found is None:
            continue
        rows[pivot_row], rows[found] = rows[found], rows[pivot_row]
        for idx in range(len(rows)):
            if idx != pivot_row and ((rows[idx] >> col) & 1):
                rows[idx] ^= rows[pivot_row]
        pivot_cols.append(col)
        pivot_row += 1
        if pivot_row == len(rows):
            break

    pivot_set = set(pivot_cols)
    result: list[int] = []
    for free_col in range(ncols):
        if free_col in pivot_set:
            continue
        vector = 1 << free_col
        for row_idx, pivot_col in enumerate(pivot_cols):
            if (rows[row_idx] >> free_col) & 1:
                vector |= 1 << pivot_col
        result.append(vector)
    return _basis(result)


def _apply(row_masks: list[int], vector: int) -> int:
    output = 0
    for row_idx, row in enumerate(row_masks):
        if (row & vector).bit_count() & 1:
            output |= 1 << row_idx
    return output


def _multiply(left: list[list[int]], right: list[list[int]]) -> list[list[int]]:
    if not left:
        return []
    inner = len(right)
    ncols = len(right[0]) if right else 0
    product = [[0] * ncols for _ in range(len(left))]
    for row_idx, left_row in enumerate(left):
        for inner_idx in range(inner):
            if left_row[inner_idx] & 1:
                for col_idx in range(ncols):
                    product[row_idx][col_idx] ^= right[inner_idx][col_idx] & 1
    return product


def _first_nonzero_column(matrix: list[list[int]]) -> int:
    ncols = len(matrix[0]) if matrix else 0
    for col_idx in range(ncols):
        if any(row[col_idx] for row in matrix):
            return col_idx
    return 0


@dataclass(frozen=True)
class _FiltrationResult:
    e2: dict[str, str]
    differentials: list[dict[str, str]]
    einf: dict[str, str]
    total_homology: dict[str, str]


class _IndependentDoubleComplex:
    """Small, bounded F2 double complex reconstructed from untrusted input."""

    def __init__(self, case: dict[str, Any]) -> None:
        raw_dims = case.get("dims", {})
        raw_dh = case.get("d_h", {})
        raw_dv = case.get("d_v", {})
        if (
            not isinstance(raw_dims, dict)
            or not isinstance(raw_dh, dict)
            or not isinstance(raw_dv, dict)
        ):
            raise IndependentCheckError("dims, d_h, and d_v must be mappings")

        self.dims: dict[tuple[int, int], int] = {}
        for p in range(6):
            for q in range(6):
                raw_dim = raw_dims.get(f"{p},{q}", 0)
                if type(raw_dim) is not int or raw_dim < 0:
                    raise IndependentCheckError(f"invalid dimension at {p},{q}: {raw_dim!r}")
                self.dims[(p, q)] = raw_dim

        self.dh: dict[tuple[int, int], list[list[int]]] = {}
        self.dv: dict[tuple[int, int], list[list[int]]] = {}
        for p in range(6):
            for q in range(6):
                source_dim = self.dims[(p, q)]
                self.dh[(p, q)] = self._matrix(
                    raw_dh.get(f"{p},{q}"),
                    self.dims.get((p - 1, q), 0),
                    source_dim,
                    f"d_h[{p},{q}]",
                )
                self.dv[(p, q)] = self._matrix(
                    raw_dv.get(f"{p},{q}"),
                    self.dims.get((p, q - 1), 0),
                    source_dim,
                    f"d_v[{p},{q}]",
                )

        self.offsets: dict[int, dict[tuple[int, int], tuple[int, int]]] = {}
        self.total_dims: dict[int, int] = {}
        for degree in range(11):
            cursor = 0
            degree_offsets: dict[tuple[int, int], tuple[int, int]] = {}
            for p in range(6):
                q = degree - p
                if 0 <= q <= 5:
                    dim = self.dims[(p, q)]
                    degree_offsets[(p, q)] = (cursor, cursor + dim)
                    cursor += dim
            self.offsets[degree] = degree_offsets
            self.total_dims[degree] = cursor
        self.boundaries = {degree: self._build_total_boundary(degree) for degree in range(1, 11)}

    @staticmethod
    def _matrix(raw: Any, nrows: int, ncols: int, label: str) -> list[list[int]]:
        if raw is None:
            return [[0] * ncols for _ in range(nrows)]
        if not isinstance(raw, list) or len(raw) != nrows:
            raise IndependentCheckError(f"{label} must have shape {nrows}x{ncols}")
        matrix: list[list[int]] = []
        for row in raw:
            if not isinstance(row, list) or len(row) != ncols:
                raise IndependentCheckError(f"{label} must have shape {nrows}x{ncols}")
            parsed: list[int] = []
            for entry in row:
                if type(entry) is not int:
                    raise IndependentCheckError(f"{label} contains non-integer entry {entry!r}")
                parsed.append(entry & 1)
            matrix.append(parsed)
        return matrix

    def _build_total_boundary(self, degree: int) -> list[int]:
        rows = [0] * self.total_dims[degree - 1]
        for (p, q), (source_start, _) in self.offsets[degree].items():
            for matrix, target in (
                (self.dh[(p, q)], (p - 1, q)),
                (self.dv[(p, q)], (p, q - 1)),
            ):
                if target not in self.offsets[degree - 1]:
                    continue
                target_start, _ = self.offsets[degree - 1][target]
                for local_row, matrix_row in enumerate(matrix):
                    for local_col, value in enumerate(matrix_row):
                        if value:
                            rows[target_start + local_row] ^= 1 << (source_start + local_col)
        return rows

    def invalid_witness(self) -> dict[str, str] | None:
        for p in range(2, 6):
            for q in range(6):
                product = _multiply(self.dh[(p - 1, q)], self.dh[(p, q)])
                if any(any(row) for row in product):
                    return {
                        "reason": "DH_DH_NOT_ZERO",
                        "generator": f"{p},{q}:{_first_nonzero_column(product)}",
                    }
        for p in range(6):
            for q in range(2, 6):
                product = _multiply(self.dv[(p, q - 1)], self.dv[(p, q)])
                if any(any(row) for row in product):
                    return {
                        "reason": "DV_DV_NOT_ZERO",
                        "generator": f"{p},{q}:{_first_nonzero_column(product)}",
                    }
        for p in range(1, 6):
            for q in range(1, 6):
                first = _multiply(self.dh[(p, q - 1)], self.dv[(p, q)])
                second = _multiply(self.dv[(p - 1, q)], self.dh[(p, q)])
                difference = [
                    [a ^ b for a, b in zip(first_row, second_row)]
                    for first_row, second_row in zip(first, second)
                ]
                if any(any(row) for row in difference):
                    return {
                        "reason": "DH_DV_NOT_COMMUTING",
                        "generator": f"{p},{q}:{_first_nonzero_column(difference)}",
                    }
        return None

    def _levels(self, degree: int, filtration: str) -> list[int]:
        levels = [0] * self.total_dims[degree]
        for (p, q), (start, end) in self.offsets[degree].items():
            level = p if filtration == "columns" else q
            for index in range(start, end):
                levels[index] = level
        return levels

    def _z_basis(
        self,
        degree: int,
        bound: int,
        page: int,
        filtration: str,
        memo: dict[tuple[int, int, int], list[int]],
    ) -> list[int]:
        key = (degree, bound, page)
        if key in memo:
            return memo[key]
        dim = self.total_dims.get(degree, 0)
        if dim == 0 or bound < 0:
            memo[key] = []
            return []
        constraints = [
            1 << idx for idx, level in enumerate(self._levels(degree, filtration)) if level > bound
        ]
        if degree > 0:
            target_bound = bound - page
            constraints.extend(
                self.boundaries[degree][idx]
                for idx, level in enumerate(self._levels(degree - 1, filtration))
                if level > target_bound
            )
        memo[key] = _nullspace(constraints, dim)
        return memo[key]

    def _denominator(
        self,
        degree: int,
        bound: int,
        page: int,
        filtration: str,
        memo: dict[tuple[int, int, int], list[int]],
    ) -> list[int]:
        previous = self._z_basis(degree, bound - 1, page - 1, filtration, memo)
        incoming_source = self._z_basis(degree + 1, bound + page - 1, page - 1, filtration, memo)
        incoming = [
            _apply(self.boundaries.get(degree + 1, []), vector) for vector in incoming_source
        ]
        return _basis([*previous, *incoming])

    def total_homology(self) -> dict[str, str]:
        result: dict[str, str] = {}
        for degree in range(11):
            dim = self.total_dims[degree]
            if dim == 0:
                continue
            homology_dim = (
                dim
                - _rank(self.boundaries.get(degree, []))
                - _rank(self.boundaries.get(degree + 1, []))
            )
            if homology_dim < 0:
                raise IndependentCheckError("total boundary does not square to zero")
            if homology_dim:
                result[str(degree)] = str(homology_dim)
        return result

    def filtration(self, filtration: str) -> _FiltrationResult:
        memo: dict[tuple[int, int, int], list[int]] = {}
        page_dims = {page: {} for page in range(2, 7)}
        denominators: dict[tuple[int, int, int], list[int]] = {}
        for page in range(2, 7):
            for p in range(6):
                for q in range(6):
                    degree = p + q
                    bound = p if filtration == "columns" else q
                    numerator = self._z_basis(degree, bound, page, filtration, memo)
                    denominator = self._denominator(degree, bound, page, filtration, memo)
                    denominators[(page, p, q)] = denominator
                    numerator_rank = _rank(numerator)
                    denominator_rank = _rank(denominator)
                    if _rank([*numerator, *denominator]) != numerator_rank:
                        raise IndependentCheckError("spectral denominator escaped numerator")
                    page_dims[page][(p, q)] = numerator_rank - denominator_rank

        differentials: list[dict[str, str]] = []
        for page in range(2, 6):
            for p in range(6):
                for q in range(6):
                    degree = p + q
                    bound = p if filtration == "columns" else q
                    image = [
                        _apply(self.boundaries.get(degree, []), vector)
                        for vector in self._z_basis(degree, bound, page, filtration, memo)
                    ]
                    target = (
                        (p - page, q + page - 1)
                        if filtration == "columns"
                        else (p + page - 1, q - page)
                    )
                    target_denominator = (
                        denominators[(page, target[0], target[1])]
                        if 0 <= target[0] <= 5 and 0 <= target[1] <= 5
                        else []
                    )
                    induced_rank = _rank([*target_denominator, *image]) - _rank(target_denominator)
                    if induced_rank:
                        differentials.append(
                            {"r": str(page), "from": f"{p},{q}", "rank": str(induced_rank)}
                        )

        e2 = {f"{p},{q}": str(dim) for (p, q), dim in page_dims[2].items() if dim > 0}
        einf = {f"{p},{q}": str(dim) for (p, q), dim in page_dims[6].items() if dim > 0}
        return _FiltrationResult(e2, differentials, einf, self.total_homology())


def _expected_payload(complex_: _IndependentDoubleComplex, filtration: str) -> dict[str, Any]:
    result = complex_.filtration(filtration)
    return {
        "E2": result.e2,
        "differentials": result.differentials,
        "Einf": result.einf,
        "tot_homology": result.total_homology,
    }


def independent_check_certificate(case: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Verify a C020 certificate without consulting either first-party oracle."""
    if not isinstance(case, dict) or not isinstance(cert, dict):
        return {"verdict": "FAIL", "reason": "case and certificate must be mappings"}
    try:
        complex_ = _IndependentDoubleComplex(case)
        invalid = complex_.invalid_witness()
        if invalid is not None:
            if cert.get("status") != "OUT_OF_SCOPE":
                return {"verdict": "FAIL", "reason": "invalid double complex was not refused"}
            witness = cert.get("witness")
            if not isinstance(witness, dict):
                return {"verdict": "FAIL", "reason": "OUT_OF_SCOPE witness must be a mapping"}
            if witness.get("reason") != invalid["reason"]:
                return {"verdict": "FAIL", "reason": "OUT_OF_SCOPE reason is not the first defect"}
            if witness.get("generator") != invalid["generator"]:
                return {
                    "verdict": "FAIL",
                    "reason": (
                        "OUT_OF_SCOPE generator does not witness the first defect: "
                        f"expected {invalid['generator']}, got {witness.get('generator')}"
                    ),
                }
            return {"verdict": "PASS", "details": "independent defect witness verified"}

        if cert.get("status") != "SOLVED":
            return {"verdict": "FAIL", "reason": "valid double complex requires SOLVED status"}
        requested = case.get("filtration", "columns")
        if requested not in {"columns", "rows", "both"}:
            return {"verdict": "FAIL", "reason": f"unsupported filtration {requested!r}"}
        if cert.get("filtration") != requested:
            return {"verdict": "FAIL", "reason": "filtration mismatch"}

        if requested == "both":
            for label in ("columns", "rows"):
                expected = _expected_payload(complex_, label)
                actual = cert.get(label)
                if not isinstance(actual, dict):
                    return {"verdict": "FAIL", "reason": f"missing {label} certificate"}
                for field in ("E2", "differentials", "Einf"):
                    if actual.get(field) != expected[field]:
                        return {
                            "verdict": "FAIL",
                            "reason": f"independent {label} {field} mismatch",
                        }
            if cert.get("tot_homology") != complex_.total_homology():
                return {"verdict": "FAIL", "reason": "independent total homology mismatch"}
        else:
            expected = _expected_payload(complex_, requested)
            for field in ("E2", "differentials", "Einf", "tot_homology"):
                if cert.get(field) != expected[field]:
                    return {
                        "verdict": "FAIL",
                        "reason": f"independent {requested} {field} mismatch",
                    }
    except (IndependentCheckError, KeyError, TypeError, ValueError) as exc:
        return {"verdict": "FAIL", "reason": f"independent checker error: {exc}"}
    return {"verdict": "PASS", "details": "independent filtered-complex computation verified"}
