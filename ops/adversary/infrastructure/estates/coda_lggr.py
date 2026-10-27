"""Native-required finite CODA/LGGR consumers with explicit reference modes.

CODA uses the existing exact flat-cochain FOC owner; LGGR uses the existing
2x2 rational matrix path owner. Python independently checks supplied native
witness arithmetic; it never revives the retired quotient heuristic. Explicit
reference mode uses the separately checked native L1 certificate oracle. Probes report connection only after the
compiled owner executes and its finite result is replayed.

Origin: adversary/infrastructure/estates/coda_lggr.py
Claim: connection is reported only after the compiled owner executes and its finite rational result is replayed.
AuthorityEffect: None.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping, Sequence
from fractions import Fraction

from operations.domain.rop.result import Err, Ok, Refusal, Result
from adversary.domain.coda_refusal import CodaResidualRefusal
from adversary.domain.connection import ConnectionReceiptV1, EstateName, disconnected
from adversary.domain.specialization import PortName
from adversary.domain.swarm_models import (
    CodaEvaluationResult,
    JointKernelVerdictV1,
    LggrGluingResult,
)
from adversary.infrastructure.coda_adapter import CodaEvaluationAdapter
from adversary.infrastructure.lggr_adapter import LggrGluingAdapter

from .probe_support import canonical_bytes, observed, refusal, run_probe

_LOCUS = "adversary.infrastructure.estates.coda_lggr"
_EVALUATION_ERRORS = (
    ArithmeticError,
    KeyError,
    OSError,
    subprocess.SubprocessError,
    TypeError,
    ValueError,
)


class CodaPortAdapter:
    estate = EstateName.CRATES_RS
    port = PortName.CODA_EVALUATION
    adapter_id = "adversary.coda_evaluation_adapter"

    def __init__(self, adapter: CodaEvaluationAdapter | None = None, *, mode="native_required", host=None) -> None:
        self.adapter = adapter or CodaEvaluationAdapter(mode=mode, host=host)

    def evaluate(
        self,
        task_id: str,
        x_vector: Sequence[Fraction],
        coboundary_d0: Sequence[Sequence[Fraction]] | None = None,
        coboundary_d1: Sequence[Sequence[Fraction]] | None = None,
        cert_name: str | None = None,
        *, binding=None,
    ) -> Result[CodaEvaluationResult, Refusal]:
        try:
            options = {"binding": binding} if binding is not None else {}
            evaluated = self.adapter.evaluate(task_id, x_vector, coboundary_d0, coboundary_d1, cert_name, **options)
        except _EVALUATION_ERRORS as exc:
            return Err(refusal("CODA_EVALUATION_FAILED", exc, _LOCUS))
        if isinstance(evaluated, CodaResidualRefusal):
            return Err(evaluated.to_refusal())
        return Ok(evaluated)

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body() -> ConnectionReceiptV1:
            if getattr(self.adapter, "mode", "reference") != "native_required":
                return disconnected(
                    self.estate,
                    self.port,
                    self.adapter_id,
                    "REFERENCE_MODE: not a native-required connection",
                )
            # One edge between two vertices: x = (1) is the coboundary of f = (0, 1).
            result = self.adapter.evaluate(
                "connection-probe", [Fraction(1)], [[Fraction(-1), Fraction(1)]], [],
                binding=_probe_binding("CODA")
            )
            if isinstance(result, CodaResidualRefusal):
                return disconnected(self.estate, self.port, self.adapter_id,
                    f"{result.code}: {result.reason_code}: {result.error_message}")
            if result.phi1 != 0 or not (result.native_evidence or {}).get("transport_captures"):
                return disconnected(
                    self.estate, self.port, self.adapter_id, "probe needs an exact finite result and actual native capture"
                )
            return observed(
                self.estate,
                self.port,
                self.adapter_id,
                canonical_bytes(result.to_dict()),
                "native core_wdp exact FOC evaluated and independently replayed the supplied probe",
            )

        return run_probe(self.estate, self.port, self.adapter_id, body)


class LggrPortAdapter:
    estate = EstateName.CRATES_RS
    port = PortName.LGGR_GLUING
    adapter_id = "adversary.lggr_gluing_adapter"

    def __init__(self, adapter: LggrGluingAdapter | None = None, *, mode="native_required", host=None) -> None:
        if mode not in ("reference", "native_required"):
            raise ValueError("LGGR_MODE_INVALID")
        self.adapter, self.mode = adapter or LggrGluingAdapter(), mode
        self.native = CodaEvaluationAdapter(mode="native_required", host=host)

    def evaluate(
        self,
        local_evaluators: Mapping[str, int],
        global_evaluator: int,
        corpus_samples: Sequence[tuple[Mapping[str, int], int]] | None = None,
        *, carrier=None, binding=None, soundness=None,
    ) -> Result[LggrGluingResult, Refusal]:
        try:
            joint = None if soundness is None else self._joint_kernel(soundness, binding)
            if self.mode == "native_required" and (carrier is not None or joint is None):
                return Ok(self._evaluate_carrier(carrier, binding, joint))
            return Ok(
                self.adapter.evaluate_boundary(
                    dict(local_evaluators),
                    global_evaluator,
                    [(dict(local), verdict) for local, verdict in corpus_samples]
                    if corpus_samples is not None
                    else None,
                    joint,
                )
            )
        except _EVALUATION_ERRORS as exc:
            return Err(refusal("LGGR_EVALUATION_FAILED", exc, _LOCUS))

    def probe(self, scratch_root: str) -> ConnectionReceiptV1:
        def body():
            if self.mode != "native_required":
                return disconnected(self.estate, self.port, self.adapter_id, "REFERENCE_MODE")
            result = self._evaluate_carrier({"vertices": ["a"], "edges": [["a", "a"]],
                "matrices": [[["1", "0"], ["0", "1"]]], "cycle": [0],
                "edge_threshold": "0", "cycle_threshold": "0"}, _probe_binding("LGGR"))
            if not (result.native_evidence or {}).get("transport_captures"):
                return disconnected(self.estate, self.port, self.adapter_id, "native process capture unavailable")
            return observed(self.estate, self.port, self.adapter_id, canonical_bytes(result.to_dict()),
                "native LGGR exact matrix path owner executed; independent rational product replayed")
        return run_probe(self.estate, self.port, self.adapter_id, body)

    def _joint_kernel(self, soundness, binding):
        """Ask `lggr_v::check_soundness` for (D, Q), then replay any witness exactly."""
        binding = self.native._finite_binding(binding)
        d, q = _soundness_matrices(soundness)
        if not _soundness_dimensions_ok(d, q):
            raise ValueError("LGGR_SOUNDNESS_DIMENSION_MISMATCH")
        request = {"binding": binding, "d": soundness["d"], "q": soundness["q"]}
        wire, _ = self.native._finite_call("lggr_joint_kernel_soundness", request)
        sound, d_rank, qd_rank = _wire_ranks(wire)
        witness = _parse_witness(wire)
        if witness is not None and _witness_replay_failed(d, q, witness):
            raise ValueError("LGGR_SOUNDNESS_WITNESS_REPLAY_FAILED")
        return JointKernelVerdictV1(sound, d_rank, qd_rank, witness, str(wire.get("decision")))

    def _evaluate_carrier(self, carrier, binding, joint=None):
        binding = self.native._finite_binding(binding)
        if not _carrier_keys_ok(carrier):
            raise ValueError("LGGR_EXPLICIT_CARRIER_REQUIRED")
        request = {"binding": binding, "carrier": carrier}
        matrices = _parse_matrices(carrier)
        if not _matrix_dimensions_ok(matrices, carrier["edges"]):
            raise ValueError("LGGR_MATRIX_DIMENSION_MISMATCH")
        if not _cycle_ok(carrier["cycle"], len(matrices)):
            raise ValueError("LGGR_CYCLE_INVALID")
        if not _closed_path_ok(carrier, carrier["cycle"]):
            raise ValueError("LGGR_DECLARED_CLOSED_PATH_REQUIRED")
        wire, captures = self.native._finite_call("lggr_finite_evaluate", request)
        edge_threshold = Fraction(carrier["edge_threshold"])
        green = _local_greens(matrices, edge_threshold)
        product = _cycle_product(matrices, carrier["cycle"])
        global_green = _identity_deviation(product) <= Fraction(carrier["cycle_threshold"])
        if not _replay_matches(wire, green, global_green, product):
            raise ValueError("LGGR_NATIVE_REPLAY_MISMATCH")
        return _gluing_result(green, global_green, binding, request, wire, captures, joint)


def _fraction_matrix(rows):
    return [[Fraction(cell) for cell in row] for row in rows]


def _soundness_matrices(soundness):
    if type(soundness) is not dict or set(soundness) != {"d", "q"}:
        raise ValueError("LGGR_SOUNDNESS_CARRIER_REQUIRED")
    return _fraction_matrix(soundness["d"]), _fraction_matrix(soundness["q"])


def _matrix_width_ok(rows):
    if not rows or not rows[0]:
        return False
    width = len(rows[0])
    for row in rows:
        if len(row) != width:
            return False
    return True


def _soundness_dimensions_ok(d, q):
    if not _matrix_width_ok(d):
        return False
    if not q or len(q[0]) != len(d):
        return False
    width = len(q[0])
    for row in q:
        if len(row) != width:
            return False
    return True


def _wire_ranks(wire):
    sound, d_rank, qd_rank = wire.get("sound"), wire.get("d_rank"), wire.get("qd_rank")
    if type(sound) is not bool or type(d_rank) is not int or type(qd_rank) is not int:
        raise ValueError("LGGR_SOUNDNESS_WIRE_INVALID")
    return sound, d_rank, qd_rank


def _parse_witness(wire):
    witness = wire.get("witness")
    if witness is None:
        return None
    if type(witness) is not list or any(type(cell) is not str for cell in witness):
        raise ValueError("LGGR_SOUNDNESS_WIRE_INVALID")
    return tuple(Fraction(cell) for cell in witness)


def _matvec(rows, vector):
    return [sum(row[index] * vector[index] for index in range(len(vector))) for row in rows]


def _witness_replay_failed(d, q, witness):
    if len(witness) != len(d[0]):
        return True
    dv = _matvec(d, witness)
    if not dv:
        return True
    qdv = _matvec(q, dv)
    if all(cell == 0 for cell in dv):
        return True
    return any(cell != 0 for cell in qdv)


_CARRIER_KEYS = {"vertices", "edges", "matrices", "cycle", "edge_threshold", "cycle_threshold"}


def _carrier_keys_ok(carrier):
    return type(carrier) is dict and set(carrier) == _CARRIER_KEYS


def _parse_matrices(carrier):
    matrices = []
    for matrix in carrier["matrices"]:
        parsed = []
        for row in matrix:
            parsed.append([Fraction(value) for value in row])
        matrices.append(parsed)
    return matrices


def _matrix_dimensions_ok(matrices, edges):
    if not 1 <= len(matrices) <= 8:
        return False
    if len(matrices) != len(edges):
        return False
    for matrix in matrices:
        if len(matrix) != 2:
            return False
        for row in matrix:
            if len(row) != 2:
                return False
    return True


def _cycle_ok(cycle, matrix_count):
    if type(cycle) is not list:
        return False
    if not 1 <= len(cycle) <= 16:
        return False
    for index in cycle:
        if type(index) is not int or not 0 <= index < matrix_count:
            return False
    return True


def _vertices_ok(vertices):
    if type(vertices) is not list or not 1 <= len(vertices) <= 8:
        return False
    for vertex in vertices:
        if type(vertex) is not str or not vertex:
            return False
    return len(set(vertices)) == len(vertices)


def _edges_ok(edges, vertices):
    if type(edges) is not list:
        return False
    for edge in edges:
        if type(edge) is not list or len(edge) != 2:
            return False
        for vertex in edge:
            if vertex not in vertices:
                return False
    return True


def _cycle_closed(edges, cycle):
    for left, right in zip(cycle, cycle[1:]):
        if edges[left][1] != edges[right][0]:
            return False
    return edges[cycle[0]][0] == edges[cycle[-1]][1]


def _thresholds_nonnegative(carrier):
    for key in ("edge_threshold", "cycle_threshold"):
        if Fraction(carrier[key]) < 0:
            return False
    return True


def _closed_path_ok(carrier, cycle):
    if not _vertices_ok(carrier["vertices"]):
        return False
    if not _edges_ok(carrier["edges"], carrier["vertices"]):
        return False
    if not _cycle_closed(carrier["edges"], cycle):
        return False
    return _thresholds_nonnegative(carrier)


def _identity_deviation(matrix):
    total = Fraction(0)
    for row_index in range(2):
        for column_index in range(2):
            identity = 1 if row_index == column_index else 0
            total += abs(matrix[row_index][column_index] - identity)
    return total


def _locally_green(matrix, edge_threshold):
    determinant = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    if determinant <= 0:
        return False
    return _identity_deviation(matrix) <= edge_threshold


def _local_greens(matrices, edge_threshold):
    return [_locally_green(matrix, edge_threshold) for matrix in matrices]


def _multiply_2x2(matrix, product):
    result = []
    for row_index in range(2):
        row = []
        for column_index in range(2):
            cell = Fraction(0)
            for term in range(2):
                cell += matrix[row_index][term] * product[term][column_index]
            row.append(cell)
        result.append(row)
    return result


def _cycle_product(matrices, cycle):
    product = [[Fraction(1), Fraction(0)], [Fraction(0), Fraction(1)]]
    for index in cycle:
        product = _multiply_2x2(matrices[index], product)
    return product


def _wire_product(wire):
    return [[Fraction(value) for value in row] for row in wire["product"]]


def _replay_matches(wire, green, global_green, product):
    local = wire["local_green"]
    if type(local) is not list:
        return False
    for value in local:
        if type(value) is not bool:
            return False
    if local != green:
        return False
    if wire["global_green"] is not global_green:
        return False
    return _wire_product(wire) == product


def _defect_name(delta):
    if delta == -1:
        return "NegativeGluingDefect_LocalGreenGlobalRed"
    if delta == 1:
        return "PositiveGluingDefect"
    return "ZeroDefectResidual"


def _blind_spots(joint):
    if joint is None or joint.sound:
        return []
    return ["BlindSpotIntersection: rank(Q·D) = %d < rank(D) = %d" % (joint.qd_rank, joint.d_rank)]


def _joint_sound(joint):
    return joint is not None and joint.sound


def _gluing_result(green, global_green, binding, request, wire, captures, joint):
    local_product = int(all(green))
    delta = int(global_green) - local_product
    locals_green = {str(index): int(value) for index, value in enumerate(green)}
    name = _defect_name(delta)
    failures = ["DETECTOR_ADEQUACY_NOT_MEASURED"] + _blind_spots(joint)
    sound = _joint_sound(joint)
    evidence = {"binding": binding, "request": request, "response": wire, "transport_captures": captures,
                "owner": "core_epk::matrix_path_kernel", "checker": "independent-2x2-rational-product.v1"}
    if joint is not None:
        evidence["joint_kernel"] = joint.to_dict()
    return LggrGluingResult(locals_green, int(global_green), local_product, delta, name, False, failures, sound,
        "Only the supplied finite rational path and thresholds were checked; no global adequacy or authority.",
        evidence)


def _probe_binding(owner):
    return {"source_id": "adversary:" + owner + ":finite-probe-v1", "candidate_id": "identity-carrier",
            "question": "Evaluate the explicitly supplied identity finite carrier.",
            "operation_id": "adversary.native-" + owner.lower() + ".v1",
            "checker_id": "independent-rational-replay.v1"}


__all__ = ["CodaPortAdapter", "LggrPortAdapter"]
