"""Sovereign deterministic gate engine (`G0`..`G9`) for the Finite-QM Derivation PFP System.

Executes 10 fail-closed mathematical and schema gates over exact integer (`Z`)
and exact rational (`Q`) invariants in < 2 ms per derivation, emitting a typed
`FiniteQmGateReceipt` (`PASS` | `FAIL` | `REFUSAL`) with SHA-256 digest.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from pilots.llm_mechanism.derivation_dag_pfp_staged_benchmark import (
    CarrierDerivationProjection,
    derivation_candidate_json_schema,
)

FINITE_QM_GATE_IDS: tuple[str, ...] = (
    "G0_STRICT_TYPED_JSON_SCHEMA",
    "G1_COCHAIN_EXACT_SEQUENCE_D1D0",
    "G2_P_STAR_TREE_CHORD_SYNDROME_DECODE",
    "G3_DAG_ROUTE_AND_SECTOR_GAP_HONESTY",
    "G4_DENSITY_LIFT_PHI1_GAMMA2_XI_PURITY",
    "G5_SUPERPOSITION_FIBER_INTERFERENCE_GAP",
    "G6_GAUSSIAN_HOLONOMY_COHERENT_INTENSITY",
    "G7_SORKIN_HIERARCHY_AND_QUARTIC_EXCLUSION",
    "G8_K23_TRACE_ZERO_PRIMAL_DUAL_DUALITY",
    "G9_MERMIN_PERES_F2_CONTEXTUALITY_OBSTRUCTION",
)


@dataclass(frozen=True)
class FiniteQmGateReceipt:
    """Typed machine receipt for a Finite-QM derivation evaluation."""

    work_id: str
    status: str  # "PASS" | "FAIL" | "REFUSAL"
    all_gates_passed: bool
    gate_results: Mapping[str, bool]
    failures: tuple[str, ...]
    elapsed_ms: float
    receipt_sha256: str
    authority_effect: str = "None"

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "core.pfp.finite_qm.gate_receipt.v1",
            "authority_effect": self.authority_effect,
            "work_id": self.work_id,
            "status": self.status,
            "all_gates_passed": self.all_gates_passed,
            "gate_results": dict(self.gate_results),
            "failures": list(self.failures),
            "elapsed_ms": self.elapsed_ms,
            "receipt_sha256": self.receipt_sha256,
        }


def _is_exact_int(val: Any) -> bool:
    return type(val) is int


def _check_g0_strict_schema(candidate: Any) -> tuple[bool, list[str]]:
    if not isinstance(candidate, Mapping):
        return False, ["REFUSAL_G0_NOT_A_JSON_OBJECT"]
    schema = derivation_candidate_json_schema()
    required = set(schema["required"])
    props = schema["properties"]
    got_keys = set(candidate.keys())
    errors: list[str] = []
    missing = sorted(required - got_keys)
    extra = sorted(got_keys - set(props.keys()))
    if missing:
        errors.append(f"G0_MISSING_KEYS:{','.join(missing)}")
    if extra:
        errors.append(f"G0_EXTRA_KEYS:{','.join(extra)}")
    for k, spec in props.items():
        if k not in candidate:
            continue
        v = candidate[k]
        expected_type = spec.get("type")
        if expected_type == "integer":
            if not _is_exact_int(v):
                errors.append(f"G0_NON_EXACT_INT:{k}={type(v).__name__}")
        elif expected_type == "boolean":
            if type(v) is not bool:
                errors.append(f"G0_NON_BOOL:{k}={type(v).__name__}")
        elif expected_type == "string":
            if type(v) is not str:
                errors.append(f"G0_NON_STR:{k}={type(v).__name__}")
            elif "enum" in spec and v not in spec["enum"]:
                errors.append(f"G0_ENUM_VIOLATION:{k}={v}")
        elif expected_type == "array":
            if not isinstance(v, list):
                errors.append(f"G0_NON_ARRAY:{k}")
            else:
                min_items = spec.get("minItems")
                max_items = spec.get("maxItems")
                if min_items is not None and len(v) < min_items:
                    errors.append(f"G0_ARRAY_TOO_SHORT:{k}:{len(v)}<{min_items}")
                if max_items is not None and len(v) > max_items:
                    errors.append(f"G0_ARRAY_TOO_LONG:{k}:{len(v)}>{max_items}")
                item_type = spec.get("items", {}).get("type")
                if item_type == "integer" and not all(_is_exact_int(x) for x in v):
                    errors.append(f"G0_ARRAY_NON_EXACT_INT:{k}")
                elif item_type == "string" and not all(type(x) is str for x in v):
                    errors.append(f"G0_ARRAY_NON_STR:{k}")
    return len(errors) == 0, errors


def evaluate_all_gates(
    proj: CarrierDerivationProjection,
    candidate: Any,
) -> FiniteQmGateReceipt:
    """Execute all 10 sovereign Finite-QM gates (`G0`..`G9`) against `candidate`."""
    t0 = time.perf_counter()
    g0_ok, g0_errs = _check_g0_strict_schema(candidate)
    if not g0_ok or not isinstance(candidate, Mapping):
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        gate_results = {gid: False for gid in FINITE_QM_GATE_IDS}
        failures = tuple(g0_errs)
        status = (
            "REFUSAL"
            if any(e.startswith("REFUSAL_") for e in failures)
            else "FAIL"
        )
        digest_payload = json.dumps(
            {
                "work_id": proj.slice_id,
                "status": status,
                "gate_results": gate_results,
                "failures": list(failures),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return FiniteQmGateReceipt(
            work_id=proj.slice_id,
            status=status,
            all_gates_passed=False,
            gate_results=gate_results,
            failures=failures,
            elapsed_ms=elapsed_ms,
            receipt_sha256=sha256(digest_payload).hexdigest(),
        )

    exp = proj.expected_certificate
    failures_list: list[str] = []

    # G1: Cochain Exact Sequence d_1 d_0 = 0
    g1_ok = candidate.get("d1_d0_zero") is True and candidate.get("slice_id") == exp["slice_id"]
    if not g1_ok:
        failures_list.append("FAIL_G1_COCHAIN_EXACT_SEQUENCE_D1D0")

    # G2: P* Tree Potentials, Chord Syndromes, and Single-Edge Coboundary Decode
    g2_ok = (
        candidate.get("tree_potentials") == exp["tree_potentials"]
        and candidate.get("chord_syndromes") == exp["chord_syndromes"]
        and candidate.get("repaired_edge") == exp["repaired_edge"]
        and candidate.get("repaired_value") == exp["repaired_value"]
    )
    if not g2_ok:
        failures_list.append("FAIL_G2_P_STAR_TREE_CHORD_SYNDROME_DECODE")

    # G3: DAG Route Status & C_4 Sector Gap Honesty
    g3_ok = (
        candidate.get("c4_minimizer_sector_gap") == exp["c4_minimizer_sector_gap"]
        and candidate.get("route_l1_r_residual_to_weights_status")
        == exp["route_l1_r_residual_to_weights_status"]
    )
    if not g3_ok:
        failures_list.append("FAIL_G3_DAG_ROUTE_AND_SECTOR_GAP_HONESTY")

    # G4: Density Lift Phi_1, Gamma_2, Reduced Rational Xi, and Purity Gap
    xi_num = int(candidate.get("sector_xi_num", 0))
    xi_den = int(candidate.get("sector_xi_den", 1))
    g4_ok = (
        candidate.get("sector_phi1") == exp["sector_phi1"]
        and candidate.get("sector_gamma2") == exp["sector_gamma2"]
        and xi_num == exp["sector_xi_num"]
        and xi_den == exp["sector_xi_den"]
        and xi_den > 0
        and math.gcd(xi_num, xi_den) == 1
        and candidate.get("purity_gap_rank1_minus_diag")
        == exp["purity_gap_rank1_minus_diag"]
    )
    if not g4_ok:
        failures_list.append("FAIL_G4_DENSITY_LIFT_PHI1_GAMMA2_XI_PURITY")

    # G5: Superposition Quotient Fiber Interference Gap
    g5_ok = (
        candidate.get("interference_i_plus") == exp["interference_i_plus"]
        and candidate.get("interference_i_minus") == exp["interference_i_minus"]
        and candidate.get("interference_fiber_gap") == exp["interference_fiber_gap"]
        and int(candidate.get("interference_fiber_gap", 0)) > 0
    )
    if not g5_ok:
        failures_list.append("FAIL_G5_SUPERPOSITION_FIBER_INTERFERENCE_GAP")

    # G6: Gaussian Z[i] Holonomy & Coherent Intensity
    g6_ok = (
        candidate.get("norm_z1_sq") == exp["norm_z1_sq"]
        and candidate.get("norm_z2_sq") == exp["norm_z2_sq"]
        and candidate.get("holonomy_cross_term") == exp["holonomy_cross_term"]
        and candidate.get("coherent_total_intensity") == exp["coherent_total_intensity"]
    )
    if not g6_ok:
        failures_list.append("FAIL_G6_GAUSSIAN_HOLONOMY_COHERENT_INTENSITY")

    # G7: Sorkin Readout Hierarchy & Quartic Exclusion
    g7_ok = (
        candidate.get("sorkin_i2_12") == exp["sorkin_i2_12"]
        and candidate.get("sorkin_i3_quadratic") == exp["sorkin_i3_quadratic"]
        and candidate.get("sorkin_quartic_i3_111") == exp["sorkin_quartic_i3_111"]
        and candidate.get("sorkin_beta_quartic_coeff") == exp["sorkin_beta_quartic_coeff"]
    )
    if not g7_ok:
        failures_list.append("FAIL_G7_SORKIN_HIERARCHY_AND_QUARTIC_EXCLUSION")

    # G8: K_{2,3} Trace-Zero Primal-Dual Duality
    g8_ok = (
        candidate.get("k23_scalar_primal_dual_val") == exp["k23_scalar_primal_dual_val"]
        and candidate.get("k23_trace_zero_gap_num") == exp["k23_trace_zero_gap_num"]
        and candidate.get("k23_trace_zero_gap_den") == exp["k23_trace_zero_gap_den"]
    )
    if not g8_ok:
        failures_list.append("FAIL_G8_K23_TRACE_ZERO_PRIMAL_DUAL_DUALITY")

    # G9: Mermin-Peres F_2 Contextuality Obstruction
    g9_ok = (
        candidate.get("mermin_peres_f2_defect") == exp["mermin_peres_f2_defect"]
        and candidate.get("mermin_peres_global_sections_count")
        == exp["mermin_peres_global_sections_count"]
        and candidate.get("mermin_peres_max_satisfiable_contexts")
        == exp["mermin_peres_max_satisfiable_contexts"]
        and candidate.get("contextuality_verdict") == exp["contextuality_verdict"]
    )
    if not g9_ok:
        failures_list.append("FAIL_G9_MERMIN_PERES_F2_CONTEXTUALITY_OBSTRUCTION")

    gate_results = {
        "G0_STRICT_TYPED_JSON_SCHEMA": True,
        "G1_COCHAIN_EXACT_SEQUENCE_D1D0": g1_ok,
        "G2_P_STAR_TREE_CHORD_SYNDROME_DECODE": g2_ok,
        "G3_DAG_ROUTE_AND_SECTOR_GAP_HONESTY": g3_ok,
        "G4_DENSITY_LIFT_PHI1_GAMMA2_XI_PURITY": g4_ok,
        "G5_SUPERPOSITION_FIBER_INTERFERENCE_GAP": g5_ok,
        "G6_GAUSSIAN_HOLONOMY_COHERENT_INTENSITY": g6_ok,
        "G7_SORKIN_HIERARCHY_AND_QUARTIC_EXCLUSION": g7_ok,
        "G8_K23_TRACE_ZERO_PRIMAL_DUAL_DUALITY": g8_ok,
        "G9_MERMIN_PERES_F2_CONTEXTUALITY_OBSTRUCTION": g9_ok,
    }
    all_ok = all(gate_results.values())
    status = "PASS" if all_ok else "FAIL"
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
    digest_payload = json.dumps(
        {
            "work_id": proj.slice_id,
            "status": status,
            "gate_results": gate_results,
            "failures": failures_list,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return FiniteQmGateReceipt(
        work_id=proj.slice_id,
        status=status,
        all_gates_passed=all_ok,
        gate_results=gate_results,
        failures=tuple(failures_list),
        elapsed_ms=elapsed_ms,
        receipt_sha256=sha256(digest_payload).hexdigest(),
    )


def verify_dag_work_unit_reply(
    expected_work_unit: Mapping[str, Any],
    reply_obj: Any,
) -> FiniteQmGateReceipt:
    """Verify a single-node or single-route mined DAG work-unit JSON reply."""
    t0 = time.perf_counter()
    work_id = str(expected_work_unit.get("work_id", "UNKNOWN"))
    if not isinstance(reply_obj, Mapping):
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        return FiniteQmGateReceipt(
            work_id=work_id,
            status="REFUSAL",
            all_gates_passed=False,
            gate_results={"G0_STRICT_TYPED_JSON_SCHEMA": False},
            failures=("REFUSAL_NOT_A_JSON_OBJECT",),
            elapsed_ms=elapsed_ms,
            receipt_sha256=sha256(f"{work_id}:REFUSAL".encode("utf-8")).hexdigest(),
        )

    exp_cert = expected_work_unit["expected_certificate"]
    gate_results: dict[str, bool] = {}
    failures: list[str] = []

    g0_ok = set(reply_obj.keys()) == set(exp_cert.keys()) and all(
        not isinstance(v, float) for v in reply_obj.values()
    )
    gate_results["G0_STRICT_TYPED_JSON_SCHEMA"] = g0_ok
    if not g0_ok:
        failures.append("FAIL_G0_SCHEMA_KEYS_OR_FLOAT")

    for k, exp_v in exp_cert.items():
        got_v = reply_obj.get(k)
        ok = got_v == exp_v and type(got_v) is type(exp_v)
        gate_results[f"FIELD_{k.upper()}"] = ok
        if not ok:
            failures.append(f"MISMATCH_{k}:got={got_v!r},exp={exp_v!r}")

    all_ok = len(failures) == 0
    status = "PASS" if all_ok else "FAIL"
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
    digest_payload = json.dumps(
        {
            "work_id": work_id,
            "status": status,
            "gate_results": gate_results,
            "failures": failures,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return FiniteQmGateReceipt(
        work_id=work_id,
        status=status,
        all_gates_passed=all_ok,
        gate_results=gate_results,
        failures=tuple(failures),
        elapsed_ms=elapsed_ms,
        receipt_sha256=sha256(digest_payload).hexdigest(),
    )


def verify_dag_prompt_node_reply(
    expected_ground_truth: Mapping[str, Any],
    reply_obj: Any,
) -> FiniteQmGateReceipt:
    """Verify the 18-field typed JSON certificate for a 35-node DAG prompt run."""
    t0 = time.perf_counter()
    node_id = str(expected_ground_truth.get("node_id", "UNKNOWN"))
    if not isinstance(reply_obj, Mapping):
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
        return FiniteQmGateReceipt(
            work_id=node_id,
            status="REFUSAL",
            all_gates_passed=False,
            gate_results={"G0_STRICT_TYPED_JSON_SCHEMA": False},
            failures=("REFUSAL_NOT_A_JSON_OBJECT",),
            elapsed_ms=elapsed_ms,
            receipt_sha256=sha256(f"{node_id}:REFUSAL".encode("utf-8")).hexdigest(),
        )

    gate_results: dict[str, bool] = {}
    failures: list[str] = []

    req_keys = set(expected_ground_truth.keys())
    got_keys = set(reply_obj.keys())
    no_floats = all(
        not isinstance(v, float)
        and (not isinstance(v, list) or all(not isinstance(x, float) for x in v))
        for v in reply_obj.values()
    )
    g0_ok = (req_keys == got_keys) and no_floats
    gate_results["G0_STRICT_TYPED_JSON_SCHEMA"] = g0_ok
    if not g0_ok:
        failures.append(f"G0_SCHEMA_OR_FLOAT:missing={sorted(req_keys - got_keys)},extra={sorted(got_keys - req_keys)}")

    g1_ok = reply_obj.get("cochain_d1_d0_exact_zero") is True
    gate_results["G1_COCHAIN_EXACT_SEQUENCE_D1D0"] = g1_ok
    if not g1_ok:
        failures.append("G1_COCHAIN_D1D0_NOT_TRUE")

    g2_ok = (
        reply_obj.get("p_star_tree_potentials") == expected_ground_truth["p_star_tree_potentials"]
        and reply_obj.get("p_star_chord_potential") == expected_ground_truth["p_star_chord_potential"]
        and reply_obj.get("p_star_holonomy_gamma2") == expected_ground_truth["p_star_holonomy_gamma2"]
    )
    gate_results["G2_P_STAR_TREE_CHORD_SYNDROME_DECODE"] = g2_ok
    if not g2_ok:
        failures.append(
            f"G2_P_STAR_MISMATCH:got={(reply_obj.get('p_star_tree_potentials'), reply_obj.get('p_star_chord_potential'), reply_obj.get('p_star_holonomy_gamma2'))}"
        )

    g3_ok = (
        reply_obj.get("finite_shadow_witness_int") == expected_ground_truth["finite_shadow_witness_int"]
        and _is_exact_int(reply_obj.get("finite_shadow_witness_int"))
    )
    gate_results["G3_FINITE_SHADOW_EXACT_WITNESS"] = g3_ok
    if not g3_ok:
        failures.append(
            f"G3_FINITE_SHADOW_MISMATCH:got={reply_obj.get('finite_shadow_witness_int')!r},exp={expected_ground_truth['finite_shadow_witness_int']!r}"
        )

    g4_ok = (
        reply_obj.get("countermodel_witness_int") == expected_ground_truth["countermodel_witness_int"]
        and _is_exact_int(reply_obj.get("countermodel_witness_int"))
    )
    gate_results["G4_COUNTERMODEL_SEPARATION_WITNESS"] = g4_ok
    if not g4_ok:
        failures.append(
            f"G4_COUNTERMODEL_MISMATCH:got={reply_obj.get('countermodel_witness_int')!r},exp={expected_ground_truth['countermodel_witness_int']!r}"
        )

    g5_ok = (
        reply_obj.get("unpaid_import_count") == expected_ground_truth["unpaid_import_count"]
        and reply_obj.get("unconditional_promotion_refused") is True
        and reply_obj.get("authority_effect") == "None"
        and reply_obj.get("derived_under_policy") == "SPK-001"
    )
    gate_results["G5_IMPORT_BOUNDARY_AND_FIREWALL_HONESTY"] = g5_ok
    if not g5_ok:
        failures.append("G5_IMPORT_BOUNDARY_OR_FIREWALL_VIOLATION")

    g6_ok = (
        reply_obj.get("lean4_theorem_anchor") == expected_ground_truth["lean4_theorem_anchor"]
        and reply_obj.get("rust_witness_anchor") == expected_ground_truth["rust_witness_anchor"]
    )
    gate_results["G6_TRI_LANGUAGE_ANCHOR_BINDING"] = g6_ok
    if not g6_ok:
        failures.append("G6_TRI_LANGUAGE_ANCHOR_MISMATCH")

    all_ok = len(failures) == 0
    status = "PASS" if all_ok else "FAIL"
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 4)
    digest_payload = json.dumps(
        {
            "work_id": node_id,
            "status": status,
            "gate_results": gate_results,
            "failures": failures,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return FiniteQmGateReceipt(
        work_id=node_id,
        status=status,
        all_gates_passed=all_ok,
        gate_results=gate_results,
        failures=tuple(failures),
        elapsed_ms=elapsed_ms,
        receipt_sha256=sha256(digest_payload).hexdigest(),
    )

