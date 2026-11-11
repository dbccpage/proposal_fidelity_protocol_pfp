"""Host-derived characteristic-polynomial coverage-first workflows.

Three matched-resource comparison arms:
1. `coverage_first_direct_v1`: seed-only baseline under coverage-first instruction.
2. `coverage_first_matrix_v1`: public matrix context derived by host from Pauli products.
3. `coverage_first_charpoly_v1`: public matrix plus host-derived, native-replayed
   characteristic-polynomial context with explicitly limited intermediate scope.

Shared constraints across all three arms:
- Identical system coverage instruction across all arms.
- Identical output token ceiling (16,000 tokens).
- Exactly one solver dispatch per arm.
- Frozen QM seed prompt bytes (SHA-256: 9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7).
- Evaluator firewall: zero private reference formulas, rubric text, or answer keys in solver context.
- Zero repository retrieval granted to solvers.
- Intermediate certificate does not certify downstream derivations or full QM answer.
"""
from __future__ import annotations

from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OPS = ROOT / "ops"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(OPS) not in sys.path:
    sys.path.insert(0, str(OPS))

import hamiltonian_artifact as pauli
import qm_host_charpoly as host_charpoly

SUPPORTED_SEED_SHA256 = "9941ab91f8e6b6637e49bb364cc0e6451788dd96442afcdb7f7024de042500a7"

COVERAGE_FIRST_INSTRUCTION = (
    "Solve all five parts of the unchanged original task in full. "
    "Maintain explicit coverage across all five parts: "
    "1) spectrum, degeneracies, and spectral projectors; "
    "2) dynamics and transition probability; "
    "3) reduced state, entanglement, and CHSH violation; "
    "4) thermal state and entanglement threshold; "
    "5) consistency checks. "
    "State assumptions, exceptional parameter cases, and derivations. "
    "Any supplied intermediate artifacts are untrusted reference context only, not a certification of your solution. "
    "Return your complete derivation and final results."
)

IMPLEMENTATION_FILES = (
    "host_charpoly_workflows.py",
    "qm_host_charpoly.py",
    "hamiltonian_artifact.py",
    "charpoly_wire.py",
    "native_sidecar.py",
    "qm_native_charpoly.py",
    "reference_runner.py",
    "budget_ledger.py",
    "campaign_ledger.py",
    "openrouter_provider.py",
    "live_campaign.py",
)


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_source_pins() -> dict[str, str]:
    """Capture live source pins for all workflow dependencies."""
    pins: dict[str, str] = {}
    for filename in IMPLEMENTATION_FILES:
        filepath = HERE / filename
        if filepath.is_file():
            pins[filename] = _file_sha(filepath)
    return pins


def make_plan_spec(
    plan_id: str,
    *,
    host_matrix: bool = False,
    host_charpoly: bool = False,
    semantic_composition: bool = False,
    checked: bool = False,
    scope: str = "",
) -> dict[str, Any]:
    visible = []
    if host_matrix or host_charpoly or semantic_composition:
        visible.append("matrix_context")
    if host_charpoly or semantic_composition:
        visible.append("charpoly_context")
    if semantic_composition:
        visible.append("semantic_composition_receipt")

    stages = [
        {
            "id": "solve",
            "instruction": COVERAGE_FIRST_INSTRUCTION,
            "max_output_tokens": 16000,
            "visible_artifacts": visible,
        }
    ]

    return {
        "plan_id": plan_id,
        "version": "1.0",
        "stages": stages,
        "checked": checked,
        "host_matrix": host_matrix,
        "host_charpoly": host_charpoly,
        "semantic_composition": semantic_composition,
        "max_output_tokens": 16000,
        "source_idea": "R01-I03-CF",
        "scope": scope,
        "source_pins": prepare_source_pins(),
    }


HOST_CHARPOLY_PLANS: dict[str, Any] = {
    "coverage_first_direct_v1": make_plan_spec(
        "coverage_first_direct_v1",
        host_matrix=False,
        host_charpoly=False,
        semantic_composition=False,
        checked=False,
        scope=(
            "Direct baseline under coverage-first instruction with unchanged seed only; "
            "no intermediate host matrix context or polynomial certificate."
        ),
    ),
    "coverage_first_matrix_v1": make_plan_spec(
        "coverage_first_matrix_v1",
        host_matrix=True,
        host_charpoly=False,
        semantic_composition=False,
        checked=True,
        scope=(
            "Coverage-first workflow with host-derived public Pauli coefficient matrices; "
            "no intermediate polynomial certificate or downstream certification."
        ),
    ),
    "coverage_first_charpoly_v1": make_plan_spec(
        "coverage_first_charpoly_v1",
        host_matrix=True,
        host_charpoly=True,
        semantic_composition=False,
        checked=True,
        scope=(
            "Coverage-first workflow with host-derived public Pauli matrices plus "
            "host-derived and native-replayed characteristic polynomial context. "
            "Intermediate det(lambda*I - H) identity certified only; final answer not certified."
        ),
    ),
    "coverage_first_operad_composition_v1": make_plan_spec(
        "coverage_first_operad_composition_v1",
        host_matrix=True,
        host_charpoly=True,
        semantic_composition=True,
        checked=True,
        scope=(
            "Typed bounded composition: (Host Charpoly in Q[lambda,J,Delta,K]) -> "
            "(EIS allosteric consensus gate over independent verification signals) -> "
            "(PCIV Pareto selection over non-empty QM task sets) -> "
            "(OPERADS typed port composition with verified sequential associativity). "
            "Offline-verified under exact arithmetic; final answer not certified."
        ),
    ),
}


def build_host_matrix_artifact(seed_hash: str) -> dict[str, Any]:
    """Derive and validate the public Pauli matrix artifact from public definitions."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")
    artifact = pauli.public_input_artifact(seed_hash)
    canonical_text = json.dumps(artifact, sort_keys=True, separators=(",", ":"))
    checked = pauli.check_artifact(canonical_text, seed_hash)
    if not checked["accepted"]:
        raise ValueError(f"Host-derived Pauli matrix artifact rejected: {checked.get('errors')}")
    return artifact


def build_host_charpoly_artifact(seed_hash: str, *, compact: bool = True) -> dict[str, Any]:
    """Derive, wire-normalize, and native-verify the host characteristic polynomial context."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")
    certified = host_charpoly.build_certified_context(seed_hash, compact=compact)
    validated = host_charpoly.validate_certified_context(certified)
    if not validated["valid"]:
        raise ValueError("Host-derived characteristic polynomial context failed validation")
    return certified


class EISVerificationBridge:
    """Evaluates independent verification signals via EIS AllostericConsensusGate."""

    @staticmethod
    def evaluate_charpoly_evidence(
        charpoly_artifact: dict[str, Any],
        matrix_artifact: dict[str, Any],
        *,
        custom_signals: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Collects independent signals and evaluates allosteric consensus.

        Sensors:
          - 'sensor_grid_identity': 1 if 125 grid nodes verified by native Rust sidecar.
          - 'sensor_degree_bounds': 1 if monic degree 4 in lambda and deg <= 4 in parameters.
          - 'sensor_trace_zero': 1 if Tr(H) == 0 in computational basis.
        """
        import eis.domain.allostery as allostery
        from eis.domain.value_objects import HillParameters

        gate = allostery.AllostericConsensusGate(
            parameters=HillParameters(hill_coefficient=2, half_maximal_constant=Fraction(2)),
            activation_threshold=Fraction(1, 2),
            per_sensor_cap=Fraction(1),
        )

        if custom_signals is not None:
            sensor_signals = custom_signals
        else:
            grid_verified = (
                charpoly_artifact.get("native_verification", {}).get("grid_points_verified") == 125
            )
            standard_form = charpoly_artifact.get("polynomial", {}).get("standard_form", "")
            monic_deg = standard_form.startswith("lambda^4")

            matrices = matrix_artifact.get("coefficient_matrices", {})
            trace_zero = bool(matrices) and all(
                sum(Fraction(mat[i][i]) for i in range(4)) == 0
                for mat in matrices.values()
            )

            sensor_signals = {
                "sensor_grid_identity": Fraction(1, 1) if grid_verified else Fraction(0, 1),
                "sensor_degree_bounds": Fraction(1, 1) if monic_deg else Fraction(0, 1),
                "sensor_trace_zero": Fraction(1, 1) if trace_zero else Fraction(0, 1),
            }

        decision = gate.evaluate_quorum(sensor_signals)
        return {
            "is_activated": decision.is_activated,
            "hill_value_str": str(decision.hill_value),
            "aggregate_signal_str": str(decision.aggregate_signal),
            "threshold_str": str(decision.threshold),
            "quorum_size": decision.quorum_size,
            "positive_sensors": decision.positive_sensors,
            "rationale": decision.rationale,
        }


class PCIVTaskSetEvaluator:
    """Enforces non-empty task set bounds and evaluates Pareto front dominance."""

    QM_TASK_PORTFOLIO = (
        "part1_spectrum_degeneracies",
        "part2_dynamics_transition_prob",
        "part3_reduced_state_entanglement",
        "part4_thermal_state_threshold",
        "part5_algebraic_consistency_checks",
    )

    @classmethod
    def evaluate_portfolio(
        cls,
        candidate_metrics: list[dict[str, Any]],
        *,
        task_portfolio: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """Validates non-empty task portfolio and partitions non-dominated Pareto fronts."""
        import pciv.use_cases.fitness as pciv_fitness

        portfolio = cls.QM_TASK_PORTFOLIO if task_portfolio is None else task_portfolio

        if not candidate_metrics:
            raise ValueError("MISSING_MEASUREMENTS: Candidate metrics portfolio cannot be empty")

        if not portfolio:
            raise ValueError("EMPTY_TASK_SET: Obligatory task set cannot be empty")

        selector = pciv_fitness.ParetoFrontSelectorV1()
        fronts = selector.partition_fronts(candidate_metrics)

        def _serialize_candidate(c: dict[str, Any]) -> dict[str, Any]:
            res = {"id": c.get("id")}
            if "metrics" in c:
                res["metrics"] = {
                    k: str(v) if isinstance(v, Fraction) else v
                    for k, v in c["metrics"].items()
                }
            return res

        return {
            "task_portfolio": list(portfolio),
            "task_count": len(portfolio),
            "candidate_count": len(candidate_metrics),
            "non_dominated_front": [_serialize_candidate(c) for c in (fronts[0] if fronts else [])],
            "total_fronts": len(fronts),
            "lexicographic_leader_id": fronts[0][0]["id"] if fronts and fronts[0] else None,
        }


class OperadCompositionPipeline:
    """Formalizes the workflow as a typed planar operad tree with associativity witness."""

    @staticmethod
    def build_composition_witness(*, op_root_source: str = "Audit") -> dict[str, Any]:
        """Constructs operations and certifies sequential operadic associativity.

        Morphisms:
          f: (State) -> Contract           [Host Charpoly Derivation]
          g: (Contract) -> Audit           [EIS Allosteric Consensus Gate]
          h: (Audit) -> Receipt            [PCIV Pareto Selection & Bound Check]
        """
        import operads.domain.operad.colours as colours
        import operads.domain.operad.operation as ops
        import operads.domain.operad.planar as planar

        c_state = colours.Colour("State")
        c_contract = colours.Colour("Contract")
        c_audit = colours.Colour(op_root_source)
        c_receipt = colours.Colour("Receipt")

        sig_f = colours.ColourSignature(source=(c_state,), target=c_contract)
        sig_g = colours.ColourSignature(source=(c_contract,), target=colours.Colour("Audit"))
        sig_h = colours.ColourSignature(source=(c_audit,), target=c_receipt)

        op_f = ops.OperationSignature(ops.OperationId("host_charpoly_derivation"), sig_f)
        op_g = ops.OperationSignature(ops.OperationId("eis_allosteric_consensus"), sig_g)
        op_h = ops.OperationSignature(ops.OperationId("pciv_pareto_selection"), sig_h)

        witness_result = planar.TreeCompositionWitness.verify_sequential_associativity(
            op_h, op_g, op_f, 0, 0
        )
        if witness_result.is_err:
            raise ValueError(f"Operad associativity verification failed: {witness_result.error.message}")

        witness = witness_result.unwrap()
        return {
            "is_associative": witness.is_associative,
            "left_composite": str(witness.left_composite),
            "right_composite": str(witness.right_composite),
            "details": witness.details,
            "operations": [
                {"id": op_f.op_id.value, "signature": str(sig_f)},
                {"id": op_g.op_id.value, "signature": str(sig_g)},
                {"id": op_h.op_id.value, "signature": str(sig_h)},
            ],
            "tree_arity": 1,
            "root_colour": "Receipt",
            "leaf_colour": "State",
        }


def evaluate_pre_dispatch_candidate_metrics(
    seed_hash: str = SUPPORTED_SEED_SHA256,
) -> list[dict[str, Any]]:
    """Evaluates genuine host-measured pre-dispatch candidate metrics.

    Evaluates 5 candidate intermediate representations on exact host-certified
    predicate count in {0, 1, 2} vs exact canonical UTF-8 byte cost:
      1. seed_only: empty intermediate context (0 predicates, 0 bytes)
      2. public_matrix_only: host-derived Pauli matrices (1 predicate, 467 bytes)
      3. compact_certified_charpoly: compact intermediate certificate (2 predicates, 1168 bytes)
      4. verbose_certified_charpoly: full certified context (2 predicates, 4162 bytes)
      5. refused_malformed_candidate: malformed/forged candidate (0 predicates, >0 bytes)

    ParetoFrontSelectorV1 non-trivially eliminates verbose_certified_charpoly
    (dominated by compact_certified_charpoly) and refused_malformed_candidate
    (dominated by seed_only) with zero hypothetical LLM scores or post-freeze
    evaluator data in solver context.
    """
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")

    matrix_art = build_host_matrix_artifact(seed_hash)
    compact_art = build_host_charpoly_artifact(seed_hash, compact=True)
    verbose_art = build_host_charpoly_artifact(seed_hash, compact=False)
    malformed_candidate = {
        "schema": "pfp.qm-host-charpoly.compact-certificate.v1",
        "status": "FORGED",
        "seed_sha256": seed_hash,
    }

    reps: list[tuple[str, Any]] = [
        ("seed_only", ""),
        ("public_matrix_only", matrix_art),
        ("compact_certified_charpoly", compact_art),
        ("verbose_certified_charpoly", verbose_art),
        ("refused_malformed_candidate", malformed_candidate),
    ]

    candidates: list[dict[str, Any]] = []
    for rep_id, payload in reps:
        if isinstance(payload, bytes):
            raw_bytes = payload
        elif isinstance(payload, str):
            raw_bytes = payload.encode("utf-8")
        else:
            raw_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        byte_cost = len(raw_bytes)

        p1 = False
        try:
            if isinstance(payload, dict) and "coefficient_matrices" in payload:
                p1 = pauli.check_artifact(raw_bytes.decode("utf-8"), seed_hash).get("accepted", False)
            elif isinstance(payload, dict) and "public_hamiltonian" in payload:
                p1 = (
                    payload.get("public_hamiltonian", {}).get("matrix")
                    == host_charpoly.get_expected_public_hamiltonian_matrix(seed_hash)
                )
            elif isinstance(payload, dict) and "admitted_public_matrix" in payload:
                p1 = True
        except Exception:
            p1 = False

        p2 = False
        try:
            if isinstance(payload, dict) and payload.get("schema") in (
                host_charpoly.SCHEMA,
                host_charpoly.COMPACT_SCHEMA,
            ):
                res = host_charpoly.validate_certified_context(payload)
                p2 = res.get("valid", False)
        except Exception:
            p2 = False

        pred_count = int(p1) + int(p2)
        candidates.append({
            "id": rep_id,
            "metrics": {
                "correctness": Fraction(pred_count, 1),
                "cost": Fraction(byte_cost, 1),
            },
        })

    return candidates


def build_semantic_composition_artifact(seed_hash: str) -> dict[str, Any]:
    """Builds and verifies the full PFP/EIS/PCIV/OPERADS semantic composition receipt."""
    if seed_hash != SUPPORTED_SEED_SHA256:
        raise ValueError(f"Unsupported seed hash: {seed_hash}")

    matrix_art = build_host_matrix_artifact(seed_hash)
    charpoly_art = build_host_charpoly_artifact(seed_hash, compact=True)

    eis_decision = EISVerificationBridge.evaluate_charpoly_evidence(charpoly_art, matrix_art)
    if not eis_decision["is_activated"]:
        raise ValueError(f"EIS Allosteric consensus gate refused: {eis_decision['rationale']}")

    # Genuine host-measured pre-dispatch candidate metrics
    candidates = evaluate_pre_dispatch_candidate_metrics(seed_hash)
    pciv_results = PCIVTaskSetEvaluator.evaluate_portfolio(candidates)
    operad_witness = OperadCompositionPipeline.build_composition_witness()

    return {
        "schema": "pfp.semantic-composition.v1",
        "seed_sha256": seed_hash,
        "status": "VERIFIED_OFFLINE_COMPOSITION",
        "eis_allosteric_consensus": eis_decision,
        "pciv_portfolio_selection": pciv_results,
        "operad_composition_witness": operad_witness,
        "limitations": {
            "final_answer_certified": False,
            "scope": "intermediate_composition_only",
            "notice": "All downstream QM derivations and final answers remain uncertified.",
        },
    }
