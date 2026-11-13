"""Exact public-input check of the Hamiltonian's three matrix coefficients.

Equality of the J, Delta and K coefficients proves only the affine polynomial
matrix identity in basis 00, 01, 10, 11, for every real parameter triple. It
does not check spectrum, dynamics, entanglement, or any other seed obligation.
The expected coefficients are computed from Pauli tensor products, not stored
answer matrices. This module reads only its own source for the receipt binding.
"""

from __future__ import annotations

import hashlib
import json
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

CHECKER_ID = "pfp.public-hamiltonian-coefficients"
CHECKER_VERSION = "1.0"
SUPPORTED_SEED_SHA256 = "9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7"
MAX_INPUT_BYTES = 32 * 1024
MAX_RATIONAL_BITS = 128
MAX_RATIONAL_CHARS = 80
MAX_JSON_DEPTH = 8
BASIS = ("00", "01", "10", "11")
COEFFICIENTS = ("J", "Delta", "K")
RATIONAL_PATTERN = r"(?:0|-?[1-9][0-9]*)/[1-9][0-9]*"
CLAIM = "Exact affine Hamiltonian matrix identity for all real J, Delta, K in basis 00,01,10,11 only."

RationalComplex = tuple[Fraction, Fraction]
ComplexMatrix = tuple[tuple[RationalComplex, ...], ...]


class ArtifactError(ValueError):
    """A bounded, public explanation of an invalid candidate encoding."""


def _bindings(seed_hash: str) -> dict[str, Any]:
    return {
        "checker_id": CHECKER_ID,
        "checker_version": CHECKER_VERSION,
        "checker_source_path": "dag/benchmark/hamiltonian_artifact.py",
        "checker_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "seed_sha256": seed_hash if type(seed_hash) is str else None,
        "supported_seed_sha256": SUPPORTED_SEED_SHA256,
        "basis": list(BASIS),
        "claim": CLAIM,
    }


def _validate_seed_hash(seed_hash: str) -> None:
    if type(seed_hash) is not str or re.fullmatch(r"[0-9a-f]{64}", seed_hash) is None:
        raise ArtifactError("seed_hash must be a lowercase SHA256 hex string")
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ArtifactError("seed_hash does not bind the supported public seed")


def public_contract(seed_hash: str) -> dict[str, Any]:
    """Describe the artifact format and bindings without supplying coefficients."""
    _validate_seed_hash(seed_hash)
    entry = {
        "type": "string",
        "pattern": f"^{RATIONAL_PATTERN}$",
        "maxLength": MAX_RATIONAL_CHARS,
        "description": "Reduced n/d; positive denominator; zero is 0/1; both components at most 128 bits.",
    }
    matrix = {
        "type": "array", "minItems": 4, "maxItems": 4,
        "items": {"type": "array", "minItems": 4, "maxItems": 4, "items": entry},
    }
    return {
        **_bindings(seed_hash),
        "artifact_schema": {
            "type": "object", "additionalProperties": False,
            "required": ["schema_version", "seed_sha256", "coefficient_matrices"],
            "properties": {
                "schema_version": {"const": "1.0"},
                "seed_sha256": {"const": seed_hash},
                "coefficient_matrices": {
                    "type": "object", "additionalProperties": False,
                    "required": list(COEFFICIENTS),
                    "properties": {name: matrix for name in COEFFICIENTS},
                },
            },
        },
        "limits": {"utf8_bytes": MAX_INPUT_BYTES, "json_depth": MAX_JSON_DEPTH,
                   "rational_component_bits": MAX_RATIONAL_BITS, "compared_entries": 48},
        "encoding": "One JSON object only; no markdown, duplicate keys, numeric literals, booleans or null entries.",
        "semantics": "H = J*(X tensor X + Y tensor Y) + Delta*(Z tensor I - I tensor Z) + K*(Z tensor Z).",
    }


def _complex(real: int, imag: int = 0) -> RationalComplex:
    return Fraction(real), Fraction(imag)


def _multiply(a: RationalComplex, b: RationalComplex) -> RationalComplex:
    return a[0] * b[0] - a[1] * b[1], a[0] * b[1] + a[1] * b[0]


def _tensor(a: ComplexMatrix, b: ComplexMatrix) -> ComplexMatrix:
    # Row/column i=2*a_bit+b_bit is the declared computational basis ordering.
    return tuple(tuple(_multiply(a[row // 2][col // 2], b[row % 2][col % 2])
                       for col in range(4)) for row in range(4))


def _combine(a: ComplexMatrix, b: ComplexMatrix, sign: int) -> ComplexMatrix:
    return tuple(tuple((x[0] + sign * y[0], x[1] + sign * y[1])
                       for x, y in zip(ar, br, strict=True)) for ar, br in zip(a, b, strict=True))


def _expected_coefficients() -> dict[str, tuple[tuple[Fraction, ...], ...]]:
    zero, one, minus_one = _complex(0), _complex(1), _complex(-1)
    identity = ((one, zero), (zero, one))
    x = ((zero, one), (one, zero))
    y = ((zero, _complex(0, -1)), (_complex(0, 1), zero))
    z = ((one, zero), (zero, minus_one))
    complex_coefficients = {
        "J": _combine(_tensor(x, x), _tensor(y, y), 1),
        "Delta": _combine(_tensor(z, identity), _tensor(identity, z), -1),
        "K": _tensor(z, z),
    }
    expected = {}
    for name, matrix in complex_coefficients.items():
        if any(value[1] != 0 for row in matrix for value in row):
            raise RuntimeError("Pauli expression produced a nonreal coefficient")
        expected[name] = tuple(tuple(value[0] for value in row) for row in matrix)
    return expected


def public_input_artifact(seed_hash: str) -> dict[str, Any]:
    """Return the host-derived representation for the preprocessing control.

    This is an explicit public-input calculation, separate from the model's
    format contract. It is not evidence that a model derived the coefficients.
    """
    _validate_seed_hash(seed_hash)
    expected = _expected_coefficients()
    return {
        "schema_version": "1.0", "seed_sha256": seed_hash,
        "coefficient_matrices": {
            name: [[_format(value) for value in row] for row in expected[name]] for name in COEFFICIENTS
        },
    }


def _reject_number(_literal: str) -> Any:
    raise ArtifactError("JSON numeric and nonfinite literals are forbidden; use canonical rational strings")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ArtifactError("duplicate JSON object key")
        result[key] = value
    return result


def _check_text_bounds(text: str) -> None:
    if type(text) is not str:
        raise ArtifactError("artifact must be JSON text")
    if len(text) > MAX_INPUT_BYTES:
        raise ArtifactError("artifact exceeds the UTF8 byte limit")
    try:
        size = len(text.encode("utf8"))
    except UnicodeEncodeError as exc:
        raise ArtifactError("artifact is not valid UTF8 text") from exc
    if size > MAX_INPUT_BYTES:
        raise ArtifactError("artifact exceeds the UTF8 byte limit")
    _check_depth(text)


def _check_depth(text: str) -> None:
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            depth += 1
            if depth > MAX_JSON_DEPTH:
                raise ArtifactError("artifact exceeds the JSON depth limit")
        elif char in "]}":
            depth -= 1
            if depth < 0:
                raise ArtifactError("malformed JSON nesting")


def _closed_object(value: Any, keys: tuple[str, ...], label: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        raise ArtifactError(f"{label} must be an object with exactly the declared keys")
    return value


def _rational(value: Any, label: str) -> Fraction:
    if type(value) is not str or len(value) > MAX_RATIONAL_CHARS or re.fullmatch(RATIONAL_PATTERN, value) is None:
        raise ArtifactError(f"{label} must be a canonical n/d string within the component limits")
    numerator, denominator = map(int, value.split("/"))
    if abs(numerator).bit_length() > MAX_RATIONAL_BITS or denominator.bit_length() > MAX_RATIONAL_BITS:
        raise ArtifactError(f"{label} exceeds the rational component bit limit")
    rational = Fraction(numerator, denominator)
    if value != _format(rational):
        raise ArtifactError(f"{label} must be reduced; zero must be 0/1")
    return rational


def _format(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _candidate(text: str, seed_hash: str) -> tuple[dict[str, Any], dict[str, list[list[Fraction]]]]:
    _check_text_bounds(text)
    try:
        root = json.loads(text, object_pairs_hook=_unique_object, parse_int=_reject_number,
                          parse_float=_reject_number, parse_constant=_reject_number)
    except (json.JSONDecodeError, RecursionError) as exc:
        raise ArtifactError("malformed JSON artifact") from exc
    root = _closed_object(root, ("schema_version", "seed_sha256", "coefficient_matrices"), "root")
    if type(root["schema_version"]) is not str or root["schema_version"] != "1.0":
        raise ArtifactError("schema_version must be the string 1.0")
    if type(root["seed_sha256"]) is not str or root["seed_sha256"] != seed_hash:
        raise ArtifactError("artifact seed_sha256 mismatch")
    matrices = _closed_object(root["coefficient_matrices"], COEFFICIENTS, "coefficient_matrices")
    parsed = {}
    for name in COEFFICIENTS:
        matrix = matrices[name]
        if type(matrix) is not list or len(matrix) != 4:
            raise ArtifactError(f"{name} must have exactly four rows")
        parsed[name] = []
        for row_index, row in enumerate(matrix):
            if type(row) is not list or len(row) != 4:
                raise ArtifactError(f"{name} row {row_index} must have exactly four entries")
            parsed[name].append([_rational(value, f"{name}[{row_index}][{col}]") for col, value in enumerate(row)])
    canonical = {
        "schema_version": "1.0", "seed_sha256": seed_hash,
        "coefficient_matrices": {name: [[_format(v) for v in row] for row in parsed[name]] for name in COEFFICIENTS},
    }
    return canonical, parsed


def check_artifact(text: str, seed_hash: str) -> dict[str, Any]:
    """Compare all 48 exact coefficients, returning bounded public diagnostics."""
    result = {**_bindings(seed_hash), "accepted": False, "errors": [], "mismatches": [],
              "canonical_candidate": None, "comparison_count": 0}
    try:
        _validate_seed_hash(seed_hash)
        canonical, parsed = _candidate(text, seed_hash)
    except ArtifactError as exc:
        result["errors"].append(str(exc))
        return result
    expected = _expected_coefficients()
    result["canonical_candidate"] = canonical
    for name in COEFFICIENTS:
        for row in range(4):
            for col in range(4):
                observed, target = parsed[name][row][col], expected[name][row][col]
                result["comparison_count"] += 1
                if observed != target:
                    result["mismatches"].append({"coefficient": name, "row": row, "col": col,
                                                 "observed": _format(observed), "expected": _format(target)})
    result["accepted"] = not result["mismatches"]
    return result
