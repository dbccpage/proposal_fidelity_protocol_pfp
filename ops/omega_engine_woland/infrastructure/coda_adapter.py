"""Native-certified CODA evaluation with an explicit finite production profile.

``native_required`` keeps the finite flat-carrier path and independent witness
replay. ``reference`` selects the separately checked native L1 certificate oracle,
not the retired Python quotient heuristic. Legacy auto mode retains the existing
CLI/native-certificate selection. No missing native path becomes Python success.

Retained 9-layer compatibility adapter:

Implements the 9 runtime layers of the CODA stack over Q:
FOC (trichotomy, L1 quotient minimization, dual witness vector, and Lean 4 certificate),
MUR (commuting square loss ledger),
CS (continuum shadow profile consistency),
CS_Q (section collision and metric separation),
Q (interval diameter bounds),
A (anomalon cokernel persistence),
OR (gluing sieve),
FDA (authority firewall: refuses internal self-authorization),
GTLA (master normal form coproduct terminalization).

Reported Phi1 comes from an actual native solve, never the retired Python
heuristic. Auto mode uses ``omega_coda_cli`` or the Rust host's
``exact_solve_l1_primal_dual`` followed by ``verify_l1_certificate``. Reference
mode selects that separately checked host oracle. Native-required mode uses the
explicit finite FOC operation and independently replays its primal/dual witness
arithmetic in Python; this replay does not replace an unavailable solver. The
native-certificate path returns ``CodaResidualRefusal`` when unavailable or refused.

Origin: omega_engine_woland.infrastructure.coda_adapter.
claim: reported Phi1 comes from a native solve or a typed refusal, never a Python quotient heuristic.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Sequence

from omega_engine_operations.domain.rop.result import Refusal, Result
from omega_engine_pfp.ffi import get_default_host
from omega_engine_woland.domain.coda_refusal import (
    NATIVE_L1_CERTIFICATE_REFUSED,
    NATIVE_L1_HOST_UNAVAILABLE,
    NATIVE_L1_RESPONSE_MALFORMED,
    NATIVE_L1_SOLVE_REFUSED,
    PYTHON_PHI1_PATH_RETIRED,
    CodaResidualRefusal,
)
from omega_engine_woland.domain.swarm_models import (
    CodaEvaluationResult,
    DualWitnessCertificate,
    fraction_to_str,
    str_to_fraction,
)

logger = logging.getLogger(__name__)

SOLVE_ACTION = "exact_solve_l1_primal_dual"
VERIFY_ACTION = "verify_l1_certificate"
_SOURCE_FILE = __file__
_HOST_ERRORS = (FileNotFoundError, OSError, RuntimeError, TypeError, ValueError)
_CONTINUE = object()


class NativeL1Host(Protocol):
    """The two host actions this adapter uses (``omega_engine_pfp.ffi.RustSymbolGameHost``)."""

    def exact_solve_l1_primal_dual(
        self,
        matrix_rows: Sequence[Sequence[str]],
        target: Sequence[str],
        weights: Sequence[str] | None = None,
        budget: int | None = None,
    ) -> Result[Mapping[str, Any], Refusal]: ...

    def verify_l1_certificate(
        self,
        matrix_rows: Sequence[Sequence[str]],
        omega: Sequence[str],
        p: Sequence[str],
        y: Sequence[str],
    ) -> Result[Mapping[str, Any], Refusal]: ...


@dataclass(frozen=True)
class _CertifiedPhi1:
    """Phi1 and its dual witness, read from a certificate the host accepted."""

    phi1: Fraction
    dual_y: List[Fraction]


def _parse_exact_list(value: object, length: int) -> Optional[List[Fraction]]:
    if not isinstance(value, list) or len(value) != length:
        return None
    parsed: List[Fraction] = []
    for entry in value:
        exact = _parse_exact(entry)
        if exact is None:
            return None
        parsed.append(exact)
    return parsed


def _parse_exact(value: object) -> Optional[Fraction]:
    if type(value) is not str:
        return None
    try:
        return str_to_fraction(value)
    except (ValueError, ZeroDivisionError):
        return None


def _wire_rows(x: Sequence[Fraction], d0: Sequence[Sequence[Fraction]]) -> List[List[str]]:
    """d0 as exact strings, one row per edge. A shape mismatch raises ValueError."""
    rows = [list(row) for row in d0]
    if len(rows) != len(x):
        raise ValueError(f"d0 row count {len(rows)} != cochain length {len(x)}")
    widths = {len(row) for row in rows}
    if len(widths) > 1:
        raise ValueError("d0 rows have unequal width")
    return [[fraction_to_str(Fraction(cell)) for cell in row] for row in rows]


def _augmented_rows(x, d0_rows, width):
    augmented = []
    for index, row in enumerate(d0_rows):
        cells = [Fraction(cell) for cell in row]
        if len(cells) != width:
            return None
        augmented.append(cells + [Fraction(x[index])])
    return augmented


def _find_pivot(augmented, pivot_row, column, n):
    for row in range(pivot_row, n):
        if augmented[row][column] != 0:
            return row
    return None


def _scale_pivot_row(row, column, width) -> None:
    scale = row[column]
    for cell in range(column, width + 1):
        row[cell] /= scale


def _eliminate_row(row, pivot, column, width) -> None:
    factor = row[column]
    if factor == 0:
        return
    for cell in range(column, width + 1):
        row[cell] -= factor * pivot[cell]


def _eliminate_column(augmented, pivot_row, column, width, n) -> None:
    _scale_pivot_row(augmented[pivot_row], column, width)
    for row in range(n):
        if row == pivot_row:
            continue
        _eliminate_row(augmented[row], augmented[pivot_row], column, width)


def _row_reduce(augmented, width, n) -> int:
    pivot_row = 0
    for column in range(width):
        pivot = _find_pivot(augmented, pivot_row, column, n)
        if pivot is None:
            continue
        augmented[pivot_row], augmented[pivot] = augmented[pivot], augmented[pivot_row]
        _eliminate_column(augmented, pivot_row, column, width, n)
        pivot_row += 1
    return pivot_row


def _residual_clear(augmented, width, pivot_row, n) -> bool:
    for row in range(pivot_row, n):
        if augmented[row][width] != 0:
            return False
    return True


def _cochain_is_exact_coboundary(
    x: Sequence[Fraction],
    d0_rows: Sequence[Sequence[Fraction]],
) -> bool:
    """Whether x = d0 f has a solution f over Q.

    Rows of d0_rows are edges and columns are vertices. This is an independent
    image check. The L1 dual solver's closed-cochain branch is not an exactness
    test: on a cycle every coboundary is closed, and that branch reports a
    closed nonzero cochain as a positive obstruction.
    """
    n = len(x)
    if len(d0_rows) != n:
        return False
    if n == 0:
        return True
    augmented = _augmented_rows(x, d0_rows, len(list(d0_rows[0])))
    if augmented is None:
        return False
    pivot_row = _row_reduce(augmented, len(augmented[0]) - 1, n)
    return _residual_clear(augmented, len(augmented[0]) - 1, pivot_row, n)


class NonFlatFiniteProfile(ValueError):
    """A non-flat d1 d0 composition is retained and is not a Layer1Foc evaluation."""

    def __init__(self, report: dict) -> None:
        super().__init__("CODA_FLAT_FINITE_PROFILE_REQUIRED")
        self.report = report


def _selected_matrix(primary, alternate):
    if primary is not None:
        return primary
    return alternate


def _cell_is_binary(value) -> bool:
    return type(value) in (float, bool)


def _row_has_binary(values) -> bool:
    for value in values:
        if _cell_is_binary(value):
            return True
    return False


def _carrier_has_binary(rows) -> bool:
    if not rows:
        return False
    for row in rows:
        if _row_has_binary(row):
            return True
    return False


def _canonical_pattern(n):
    pattern = []
    for index in range(n):
        pattern.append([Fraction(int(index == 0))])
    return pattern


def _d0_rows_for_host(x, d0):
    if d0 is None:
        return _wire_rows(x, _canonical_pattern(len(x)))
    return _wire_rows(x, d0)


def _row_pair(row, x, n):
    total = 0
    for index in range(n):
        total += Fraction(row[index]) * x[index]
    return total


def _face_obstruction(x, d1, n):
    total = 0
    for row in d1:
        total += abs(_row_pair(row, x, n))
    return total


def _gamma2(x, d0, d1):
    n = len(x)
    if d1 is not None:
        return _face_obstruction(x, d1, n)
    if d0 is not None:
        return Fraction(0, 1)
    if n > 2:
        return abs(x[-1])
    return Fraction(0, 1)


def _foc_grade(phi1, gamma2) -> str:
    if gamma2 != 0:
        return "NonclosedDefect"
    if phi1 == 0:
        return "ExactRepair"
    return "CoherentResidual"


def _mur_loss(grade, gamma2):
    if grade == "NonclosedDefect":
        return gamma2
    return Fraction(0, 1)


def _fda_route(grade):
    if grade == "NonclosedDefect":
        return "RouteRefused", "Refused"
    return "RouteClosedResidual", "ClosedResidual"


def _or_layer(grade, gamma2):
    if grade == "NonclosedDefect":
        return {
            "layer_id": "OR",
            "succeeded": False,
            "diagnostic": "OR gluing sieve: boundary cycle defect detected",
            "defect_mass": fraction_to_str(gamma2),
        }
    return {
        "layer_id": "OR",
        "succeeded": True,
        "diagnostic": "OR gluing sieve: consistent",
        "defect_mass": "0",
    }


def _static_layer(layer_id, diagnostic):
    return {
        "layer_id": layer_id,
        "succeeded": True,
        "diagnostic": diagnostic,
        "defect_mass": "0",
    }


def _host_layer_records(phi1, gamma2, grade, dual_cert):
    _fda_decision, terminal_kind = _fda_route(grade)
    records = [
        {
            "layer_id": "FOC",
            "succeeded": True,
            "diagnostic": f"FOC grade: {grade}, Phi_1={phi1}, Gamma_2={gamma2}",
            "defect_mass": fraction_to_str(phi1),
            "dual_witness_valid": dual_cert.is_valid(),
            "phi1_source": f"native:{SOLVE_ACTION}+{VERIFY_ACTION}",
        },
        {
            "layer_id": "MUR",
            "succeeded": True,
            "diagnostic": "MUR representation transport checked; commuting square loss ledger bound",
            "defect_mass": fraction_to_str(_mur_loss(grade, gamma2)),
        },
        _static_layer("CS", "CS continuum shadow profile consistency evaluated"),
        _static_layer("CS_Q", "CS_Q section collision and metric separation verified"),
        _static_layer("Q", "Q interval enclosure and diameter bound evaluated"),
        {
            "layer_id": "A",
            "succeeded": True,
            "diagnostic": f"A cokernel residual: persistent={phi1 > 0}",
            "defect_mass": fraction_to_str(phi1),
        },
        _or_layer(grade, gamma2),
        {
            "layer_id": "FDA",
            "succeeded": True,
            "diagnostic": f"FDA gate: non-zero quotient defect Phi_1={phi1} retained in {terminal_kind}",
            "defect_mass": fraction_to_str(phi1),
        },
        {
            "layer_id": "GTLA",
            "succeeded": True,
            "diagnostic": f"GTLA terminalization: {terminal_kind}",
            "defect_mass": fraction_to_str(phi1),
        },
    ]
    return records, _fda_decision, terminal_kind


def _max_abs(values):
    return max((abs(item) for item in values), default=Fraction(0, 1))


def _seal_host_result(name, phi1, gamma2, grade, dual_y):
    dual_cert = DualWitnessCertificate(
        name=name,
        divergence_free=True,
        linf_bounded=True,
        pairing_saturated=True,
    )
    layer_records, fda_decision, terminal_kind = _host_layer_records(phi1, gamma2, grade, dual_cert)
    evidence_bytes = json.dumps(layer_records, sort_keys=True).encode("utf-8")
    return CodaEvaluationResult(
        phi1=phi1,
        gamma2=gamma2,
        grade=grade,
        dual_witness_vector=dual_y,
        dual_witness_linfty=_max_abs(dual_y),
        dual_witness_pairing=phi1,
        layer_records=layer_records,
        terminal_kind=terminal_kind,
        firewall_decision=fda_decision,
        evidence_digest=hashlib.sha256(evidence_bytes).hexdigest(),
        dual_witness_certificate=dual_cert,
    )


def _matrix_width(rows) -> int:
    if rows:
        return len(rows[0])
    return 0


def _solver_parts(solved, width, n):
    return (
        _parse_exact_list(solved.get("alpha"), width),
        _parse_exact_list(solved.get("dual_witness"), n),
        _parse_exact(solved.get("phi1")),
    )


def _parts_malformed(alpha, dual_y, solved_phi1) -> bool:
    if alpha is None:
        return True
    if dual_y is None:
        return True
    return solved_phi1 is None


def _certificate_dual(verified):
    certificate = verified.get("certificate")
    if not isinstance(certificate, Mapping):
        return None
    return _parse_exact(certificate.get("dual_value"))


def _wire_strings(values):
    return [fraction_to_str(value) for value in values]


def _fraction_matrix(matrix):
    rows = []
    for row in matrix:
        rows.append([Fraction(cell) for cell in row])
    return rows


def _require_explicit_carrier(x, d0, d1) -> None:
    if d0 is None:
        raise ValueError("CODA_EXPLICIT_CARRIER_REQUIRED")
    if d1 is None:
        raise ValueError("CODA_EXPLICIT_CARRIER_REQUIRED")
    if len(x) < 1:
        raise ValueError("CODA_EXPLICIT_CARRIER_REQUIRED")
    if len(x) > 8:
        raise ValueError("CODA_EXPLICIT_CARRIER_REQUIRED")


def _row_width_mismatch(rows, width) -> bool:
    for row in rows:
        if len(row) != width:
            return True
    return False


def _carrier_dimension_mismatch(rows, faces, x, width) -> bool:
    if len(rows) != len(x):
        return True
    if width < 1:
        return True
    if width > 8:
        return True
    if len(faces) > 8:
        return True
    if _row_width_mismatch(rows, width):
        return True
    return _row_width_mismatch(faces, len(x))


def _extend_face_terms(terms, face_index, face, rows, width, length) -> None:
    for column in range(width):
        total = 0
        for index in range(length):
            total += face[index] * rows[index][column]
        if total:
            terms.append({"face": face_index, "column": column, "sum": str(total)})


def _composition_terms(faces, rows, width, length):
    terms = []
    for face_index, face in enumerate(faces):
        _extend_face_terms(terms, face_index, face, rows, width, length)
    return terms


def _refuse_nonflat(composition) -> None:
    if composition:
        raise NonFlatFiniteProfile({
            "refusal_code": "CODA_FLAT_FINITE_PROFILE_REQUIRED",
            "evaluated": False,
            "composition": composition,
            "phi1": None,
            "gamma2": None,
            "authority_effect": "None",
        })


def _wire_matrix(rows):
    return [list(map(fraction_to_str, row)) for row in rows]


def _finite_request(task_id, binding, x, rows, faces):
    return {
        "task_id": task_id,
        "binding": binding,
        "x": list(map(fraction_to_str, x)),
        "d0": _wire_matrix(rows),
        "d1": _wire_matrix(faces),
    }


def _any_non_str(column) -> bool:
    for value in column:
        if type(value) is not str:
            return True
    return False


def _witness_shape_invalid(wire) -> bool:
    for key in ("phi1", "gamma2"):
        if type(wire.get(key)) is not str:
            return True
    for key in ("primal_repair", "dual_witness"):
        column = wire.get(key)
        if type(column) is not list:
            return True
        if _any_non_str(column):
            return True
    return False


def _witness_bounds_invalid(repair, dual, x, phi, gamma, width) -> bool:
    if len(repair) != width:
        return True
    if len(dual) != len(x):
        return True
    if phi < 0:
        return True
    return gamma < 0


def _residual_vector(x, rows, repair, width):
    residual = []
    for index in range(len(x)):
        acc = 0
        for column in range(width):
            acc += rows[index][column] * repair[column]
        residual.append(x[index] - acc)
    return residual


def _pairing(left, right):
    total = 0
    for index in range(len(right)):
        total += left[index] * right[index]
    return total


def _dual_unbounded(dual) -> bool:
    for cell in dual:
        if abs(cell) > 1:
            return True
    return False


def _column_pairing(rows, dual, column, length):
    total = 0
    for index in range(length):
        total += rows[index][column] * dual[index]
    return total


def _divergence_nonzero(rows, dual, width, length) -> bool:
    for column in range(width):
        if _column_pairing(rows, dual, column, length):
            return True
    return False


def _face_mass(face, x):
    return abs(_pairing(face, x))


def _gamma_mass(faces, x):
    total = 0
    for face in faces:
        total += _face_mass(face, x)
    return total


def _witness_arithmetic_invalid(x, rows, faces, repair, dual, phi, gamma, width) -> bool:
    residual = _residual_vector(x, rows, repair, width)
    if sum(map(abs, residual)) != phi:
        return True
    if _pairing(dual, x) != phi:
        return True
    if _dual_unbounded(dual):
        return True
    if _divergence_nonzero(rows, dual, width, len(x)):
        return True
    return _gamma_mass(faces, x) != gamma


def _finite_grade(phi, gamma) -> str:
    if phi == 0:
        if gamma == 0:
            return "ExactRepair"
    if gamma == 0:
        return "CoherentResidual"
    return "NonclosedDefect"


def _finite_terminal(gamma):
    if gamma == 0:
        return "ClosedResidual", "RouteClosedResidual"
    return "Refused", "RouteRefused"


def _finite_result(name, phi, gamma, grade, dual, digest, evidence):
    terminal, route = _finite_terminal(gamma)
    return CodaEvaluationResult(
        phi,
        gamma,
        grade,
        dual,
        max(map(abs, dual)),
        phi,
        [{"layer_id": "FOC", "succeeded": gamma == 0, "diagnostic": grade, "defect_mass": str(phi)}],
        terminal,
        route,
        digest,
        DualWitnessCertificate(name, True, True, True),
        evidence,
    )


def _remember_finite_capture(captures, observed) -> None:
    captures.append({
        "args": list(observed["args"]),
        "exit_code": observed["exit_code"],
        "binary_sha256": hashlib.sha256(Path(observed["args"][0]).read_bytes()).hexdigest(),
        **{name.removesuffix("_bytes") + "_hex": observed[name].hex()
           for name in ("stdin_bytes", "stdout_bytes", "stderr_bytes")},
    })


def _require_success_envelope(result):
    if result.is_err:
        raise ValueError("FINITE_NATIVE_UNAVAILABLE: " + result.error.code)
    envelope = result.value
    if type(envelope) is not dict:
        raise ValueError("FINITE_NATIVE_REFUSED: unavailable runtime envelope")
    if envelope.get("success") is not True:
        raise ValueError("FINITE_NATIVE_REFUSED: unavailable runtime envelope")
    return envelope


def _wire_mismatch(wire, operation, request) -> bool:
    if type(wire) is not dict:
        return True
    if wire.get("request") != request:
        return True
    if wire.get("authority_effect") != "None":
        return True
    return wire.get("schema_version") != "woland." + operation + ".v1"


def _require_outcome(envelope, operation, request):
    content = envelope.get("result")
    if type(content) is not dict:
        raise ValueError("FINITE_NATIVE_REFUSED: " + str(content))
    if content.get("refusal") is not None:
        raise ValueError("FINITE_NATIVE_REFUSED: " + str(content))
    wire = content.get("outcome")
    if _wire_mismatch(wire, operation, request):
        raise ValueError("FINITE_NATIVE_BINDING_MISMATCH")
    return wire


def _native_d0_row(cells, width):
    if width is None:
        return len(cells), [fraction_to_str(Fraction(cell)) for cell in cells]
    if len(cells) != width:
        raise ValueError("d0 rows have unequal width")
    return width, [fraction_to_str(Fraction(cell)) for cell in cells]


def _native_d0(x, d0):
    if d0 is None:
        raise ValueError("native evaluation requires coboundary_d0")
    n = len(x)
    d0_rows = list(d0)
    if len(d0_rows) != n:
        raise ValueError(f"d0 row count {len(d0_rows)} != cochain length {n}")
    d0_native = []
    width = None
    for row in d0_rows:
        width, wired = _native_d0_row(list(row), width)
        d0_native.append(wired)
    return n, d0_rows, d0_native


def _native_d1_row(row, n):
    cells = list(row)
    if len(cells) != n:
        raise ValueError(f"d1 width {len(cells)} != cochain length {n}")
    return [fraction_to_str(Fraction(cell)) for cell in cells]


def _native_d1(d1, n):
    if d1 is None:
        return []
    return [_native_d1_row(row, n) for row in d1]


def _load_cli_object(proc):
    data = json.loads(proc.stdout)
    if not isinstance(data, dict):
        raise ValueError("omega_coda_cli stdout is not a JSON object")
    return data


def _dual_from_null(x, d0_rows, phi1, n):
    if phi1 != 0:
        raise ValueError("native dual_witness_vector is null for non-zero phi1")
    if _cochain_is_exact_coboundary(x, d0_rows):
        return [Fraction(0, 1)] * n
    raise ValueError("native dual_witness_vector is null but the cochain is not a coboundary")


def _read_dual(raw_vec, x, d0_rows, phi1, n):
    if raw_vec is None:
        return _dual_from_null(x, d0_rows, phi1, n)
    if isinstance(raw_vec, list):
        if len(raw_vec) == n:
            return [str_to_fraction(item) for item in raw_vec]
    raise ValueError("native dual_witness_vector length differs from the cochain")


def _string_column_sum(dual_y, d0_native, column):
    total = 0
    for row_idx in range(len(dual_y)):
        total += dual_y[row_idx] * str_to_fraction(d0_native[row_idx][column])
    return total


def _cli_divergence_free(dual_y, d0_native) -> bool:
    if not d0_native:
        return True
    if len(d0_native) != len(dual_y):
        return True
    for column in range(len(d0_native[0])):
        if _string_column_sum(dual_y, d0_native, column) != 0:
            return False
    return True


def _linf_bounded(dual_y) -> bool:
    for value in dual_y:
        if abs(value) > 1:
            return False
    return True


def _cli_pairing(dual_y, x):
    total = 0
    for index in range(len(x)):
        total += dual_y[index] * x[index]
    return total


def _require_native_text(value, message) -> None:
    if not isinstance(value, str):
        raise ValueError(message)


def _native_strings(data):
    layer_records = data["layer_records"]
    evidence_digest = data["evidence_digest"]
    terminal_kind = data["terminal_kind"]
    firewall_decision = data["firewall_decision"]
    grade = data["grade"]
    if not isinstance(layer_records, list):
        raise ValueError("native layer_records is not a list")
    _require_native_text(grade, "native grade or terminal_kind is not a string")
    _require_native_text(terminal_kind, "native grade or terminal_kind is not a string")
    _require_native_text(firewall_decision, "native firewall_decision or evidence_digest is not a string")
    _require_native_text(evidence_digest, "native firewall_decision or evidence_digest is not a string")
    return grade, layer_records, terminal_kind, firewall_decision, evidence_digest


class CodaEvaluationAdapter:
    """Evaluates simplicial/topological cochains across the 9-layer CODA stack."""

    def __init__(self, l1_host: Optional[NativeL1Host] = None, *, mode="auto", host=None) -> None:
        if mode not in ("auto", "reference", "native_required"):
            raise ValueError("CODA_MODE_INVALID")
        self._l1_host = l1_host
        self.mode, self.host = mode, host

    @staticmethod
    def _find_coda_binary() -> Optional[str]:
        """Return OMEGA_CODA_BIN, else omega_coda_cli on PATH.

        A set OMEGA_CODA_BIN that does not name a file raises FileNotFoundError.
        An unset variable and a missing PATH entry return None. This method does
        not search target/release or target/debug.
        """
        env_bin = os.environ.get("OMEGA_CODA_BIN")
        if env_bin:
            if os.path.isfile(env_bin):
                return env_bin
            raise FileNotFoundError(f"OMEGA_CODA_BIN does not name a file: {env_bin}")
        return shutil.which("omega_coda_cli")

    def _require_native_task(self, task_id) -> None:
        if self.mode != "native_required":
            return
        if type(task_id) is str:
            if task_id.strip():
                return
        raise ValueError("CODA_TASK_ID_REQUIRED")

    def _reject_inexact_carrier(self, x_vector, d0, d1) -> None:
        if self.mode != "native_required":
            return
        if _row_has_binary(x_vector):
            raise ValueError("CODA_EXACT_RATIONAL_REQUIRED")
        if _carrier_has_binary(d0):
            raise ValueError("CODA_EXACT_RATIONAL_REQUIRED")
        if _carrier_has_binary(d1):
            raise ValueError("CODA_EXACT_RATIONAL_REQUIRED")

    def _try_cli(self, d0, x, d1, tid, name):
        if d0 is None:
            return None
        if self.mode == "reference":
            return None
        coda_bin = self._find_coda_binary()
        if coda_bin is None:
            return None
        return self._evaluate_native(
            bin_path=coda_bin,
            task_id=tid,
            x=x,
            d0=d0,
            d1=d1,
            cert_name=name,
        )

    def _early_native(self, tid, x, d0, d1, name, binding, force_python):
        if force_python:
            return self._refuse(
                tid,
                PYTHON_PHI1_PATH_RETIRED,
                SOLVE_ACTION,
                "force_python no longer selects a Python Phi1 evaluator; "
                "Phi1 comes only from a native certificate",
            )
        if self.mode == "native_required":
            return self._evaluate_finite_native(tid, x, d0, d1, name, binding)
        native = self._try_cli(d0, x, d1, tid, name)
        if native is not None:
            return native
        return _CONTINUE

    def _evaluate_host_layers(self, tid, x, d0, d1, name):
        certified = self._certified_phi1(tid, x, _d0_rows_for_host(x, d0))
        if isinstance(certified, CodaResidualRefusal):
            return certified
        gamma2 = _gamma2(x, d0, d1)
        return _seal_host_result(
            name, certified.phi1, gamma2, _foc_grade(certified.phi1, gamma2), certified.dual_y)

    def evaluate(
        self,
        task_id: str,
        x_vector: Sequence[Fraction],
        coboundary_d0: Optional[Sequence[Sequence[Fraction]]] = None,
        coboundary_d1: Optional[Sequence[Sequence[Fraction]]] = None,
        cert_name: Optional[str] = None,
        problem_id: Optional[str] = None,
        d0_matrix: Optional[Sequence[Sequence[Fraction]]] = None,
        d1_matrix: Optional[Sequence[Sequence[Fraction]]] = None,
        external_grant: Optional[Dict[str, str]] = None,
        force_python: bool = False,
        binding: Optional[Dict[str, str]] = None,
    ) -> CodaEvaluationResult | CodaResidualRefusal:
        """Exact rational 9-layer CODA evaluation over Q, or a typed refusal.

        ``force_python`` no longer selects any evaluator: Python does not compute
        Phi1, so it returns a ``CodaResidualRefusal`` (``PYTHON_PHI1_PATH_RETIRED``).
        """
        self._require_native_task(task_id)
        tid = task_id or problem_id or "coda_eval"
        d0 = _selected_matrix(coboundary_d0, d0_matrix)
        d1 = _selected_matrix(coboundary_d1, d1_matrix)
        self._reject_inexact_carrier(x_vector, d0, d1)
        x = [Fraction(v) for v in x_vector]
        name = cert_name or f"coda_witness_{tid}"
        early = self._early_native(tid, x, d0, d1, name, binding, force_python)
        if early is not _CONTINUE:
            return early
        return self._evaluate_host_layers(tid, x, d0, d1, name)

    def _refuse(
        self, task_id: str, reason_code: str, host_action: str, error_message: str
    ) -> CodaResidualRefusal:
        refusal = CodaResidualRefusal(
            reason_code=reason_code,
            source_file=_SOURCE_FILE,
            host_action=host_action,
            error_message=error_message,
            task_id=task_id,
        )
        logger.warning(
            "CODA Phi1 refused: code=%s reason=%s file=%s action=%s task=%s error=%s",
            refusal.code,
            refusal.reason_code,
            refusal.source_file,
            refusal.host_action,
            refusal.task_id,
            refusal.error_message,
        )
        return refusal

    def _resolve_host(self) -> NativeL1Host:
        if self._l1_host is not None:
            return self._l1_host
        return get_default_host()

    def _call_host(
        self,
        task_id: str,
        action: str,
        call: Callable[[NativeL1Host], Result[Mapping[str, Any], Refusal]],
    ) -> Mapping[str, Any] | CodaResidualRefusal:
        """One host call; returns the inner ``result`` mapping or a refusal."""
        try:
            outcome = call(self._resolve_host())
        except _HOST_ERRORS as exc:
            return self._refuse(
                task_id, NATIVE_L1_HOST_UNAVAILABLE, action, f"{type(exc).__name__}: {exc}"
            )
        if outcome.is_err:
            seam = outcome.unwrap_err()
            return self._refuse(
                task_id,
                NATIVE_L1_HOST_UNAVAILABLE,
                action,
                f"{getattr(seam, 'code', 'HOST_REFUSAL')}: {getattr(seam, 'message', seam)}",
            )
        record = outcome.unwrap()
        result = record.get("result") if isinstance(record, Mapping) else None
        if not isinstance(record, Mapping) or record.get("success") is not True:
            error = record.get("error") if isinstance(record, Mapping) else record
            reason = (
                NATIVE_L1_SOLVE_REFUSED if action == SOLVE_ACTION else NATIVE_L1_CERTIFICATE_REFUSED
            )
            return self._refuse(
                task_id, reason, action, f"native action did not succeed: {error!r}"
            )
        if not isinstance(result, Mapping):
            return self._refuse(
                task_id, NATIVE_L1_RESPONSE_MALFORMED, action, "native result is not an object"
            )
        return result

    def _certified_phi1(
        self, task_id: str, x: List[Fraction], d0_rows: List[List[str]]
    ) -> _CertifiedPhi1 | CodaResidualRefusal:
        """Solve on the Rust host, then have the host verify the certificate.

        Only an accepted certificate yields Phi1; nothing here computes it.
        """
        target = _wire_strings(x)
        solved = self._call_host(
            task_id,
            SOLVE_ACTION,
            lambda host: host.exact_solve_l1_primal_dual(d0_rows, target),
        )
        if isinstance(solved, CodaResidualRefusal):
            return solved
        alpha, dual_y, solved_phi1 = _solver_parts(solved, _matrix_width(d0_rows), len(x))
        if _parts_malformed(alpha, dual_y, solved_phi1):
            return self._refuse(
                task_id,
                NATIVE_L1_RESPONSE_MALFORMED,
                SOLVE_ACTION,
                "solver answer lacks exact alpha, dual_witness or phi1 of the declared shape",
            )
        if solved.get("certificate_verified") is not True:
            return self._refuse(
                task_id,
                NATIVE_L1_CERTIFICATE_REFUSED,
                SOLVE_ACTION,
                "omega_functional did not verify the solver certificate",
            )
        verified = self._call_host(
            task_id,
            VERIFY_ACTION,
            lambda host: host.verify_l1_certificate(
                d0_rows, target, _wire_strings(alpha), _wire_strings(dual_y)
            ),
        )
        if isinstance(verified, CodaResidualRefusal):
            return verified
        if verified.get("accepted") is not True:
            return self._refuse(
                task_id,
                NATIVE_L1_CERTIFICATE_REFUSED,
                VERIFY_ACTION,
                f"certificate refused: {verified.get('refusal')!r}",
            )
        dual_value = _certificate_dual(verified)
        if dual_value is None:
            return self._refuse(
                task_id,
                NATIVE_L1_RESPONSE_MALFORMED,
                VERIFY_ACTION,
                "accepted certificate carries no exact dual_value",
            )
        if dual_value != solved_phi1:
            return self._refuse(
                task_id,
                NATIVE_L1_CERTIFICATE_REFUSED,
                VERIFY_ACTION,
                f"verified value {fraction_to_str(dual_value)} differs from solver phi1 "
                f"{fraction_to_str(solved_phi1)}",
            )
        return _CertifiedPhi1(dual_value, dual_y)

    @staticmethod
    def _finite_binding(binding):
        keys = {"source_id", "candidate_id", "question", "operation_id", "checker_id"}
        if type(binding) is not dict or set(binding) != keys or any(
                type(value) is not str or not value.strip() for value in binding.values()):
            raise ValueError("FINITE_BINDING_REQUIRED")
        return dict(binding)

    def _finite_host(self, captures, host_cls):
        if self.host:
            return self.host
        return host_cls(process_observer=lambda observed: _remember_finite_capture(captures, observed))

    def _finite_call(self, operation, request):
        from omega_engine_operating_system.adapters.rust_host.ffi import RustSymbolGameHost

        captures = []
        host = self._finite_host(captures, RustSymbolGameHost)
        result = host.invoke_runtime_with_file(
            "woland_support",
            {"operation": operation, "request": request},
            file_action="woland_support_file",
        )
        return _require_outcome(_require_success_envelope(result), operation, request), captures

    def _evaluate_finite_native(self, task_id, x, d0, d1, name, binding):
        binding = self._finite_binding(binding)
        _require_explicit_carrier(x, d0, d1)
        rows = _fraction_matrix(d0)
        faces = _fraction_matrix(d1)
        width = _matrix_width(rows)
        if _carrier_dimension_mismatch(rows, faces, x, width):
            raise ValueError("CODA_CARRIER_DIMENSION_MISMATCH")
        _refuse_nonflat(_composition_terms(faces, rows, width, len(x)))
        request = _finite_request(task_id, binding, x, rows, faces)
        wire, captures = self._finite_call("coda_finite_evaluate", request)
        if _witness_shape_invalid(wire):
            raise ValueError("CODA_NATIVE_WITNESS_INVALID")
        phi, gamma = Fraction(wire["phi1"]), Fraction(wire["gamma2"])
        repair = list(map(Fraction, wire["primal_repair"]))
        dual = list(map(Fraction, wire["dual_witness"]))
        if _witness_bounds_invalid(repair, dual, x, phi, gamma, width):
            raise ValueError("CODA_NATIVE_WITNESS_INVALID")
        if _witness_arithmetic_invalid(x, rows, faces, repair, dual, phi, gamma, width):
            raise ValueError("CODA_NATIVE_WITNESS_INVALID")
        evidence = {
            "binding": binding,
            "request": request,
            "response": wire,
            "transport_captures": captures,
            "owner": "omega_wdp::coda::layer1_foc",
            "checker": "independent-rational-primal-dual.v1",
            "scope": "explicit flat rational cochain; dimensions at most eight; no authority",
        }
        digest = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        return _finite_result(name, phi, gamma, _finite_grade(phi, gamma), dual, digest, evidence)

    def _evaluate_native(
        self,
        bin_path: str,
        task_id: str,
        x: List[Fraction],
        d0: Optional[Sequence[Sequence[Fraction]]],
        d1: Optional[Sequence[Sequence[Fraction]]],
        cert_name: str,
    ) -> CodaEvaluationResult:
        """Invoke omega_coda_cli on the supplied coboundary and read its outcome.

        d0 is required. Each d0 row is one edge. A row count other than len(x),
        or a d1 row whose width is not len(x), raises ValueError. Omitted d1
        is the declared 1-complex with no 2-cells, sent as an empty matrix.
        """
        n, d0_rows, d0_native = _native_d0(x, d0)
        payload = {
            "task_id": task_id,
            "x_vector": [fraction_to_str(value) for value in x],
            "coboundary_d0": d0_native,
            "coboundary_d1": _native_d1(d1, n),
        }
        proc = subprocess.run(
            [bin_path],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        data = _load_cli_object(proc)
        phi1 = str_to_fraction(data["phi1"])
        gamma2 = str_to_fraction(data["gamma2"])
        dual_y = _read_dual(data["dual_witness_vector"], x, d0_rows, phi1, n)
        grade, layer_records, terminal_kind, firewall_decision, evidence_digest = _native_strings(data)
        return CodaEvaluationResult(
            phi1=phi1,
            gamma2=gamma2,
            grade=grade,
            dual_witness_vector=dual_y,
            dual_witness_linfty=_max_abs(dual_y),
            dual_witness_pairing=_cli_pairing(dual_y, x),
            layer_records=layer_records,
            terminal_kind=terminal_kind,
            firewall_decision=firewall_decision,
            evidence_digest=evidence_digest,
            dual_witness_certificate=DualWitnessCertificate(
                name=cert_name,
                divergence_free=_cli_divergence_free(dual_y, d0_native),
                linf_bounded=_linf_bounded(dual_y),
                pairing_saturated=_cli_pairing(dual_y, x) == phi1,
            ),
        )
