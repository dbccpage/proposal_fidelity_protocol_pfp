"""Lamarckian Retro-Inheritance Loop Service (NF-02).

Orchestrates the Lamarckian feedback cycle:
T_loop = <P_0, G_g> -> [Adversary] -> Artifact A -> [PFP] -> Witness W -> [Thymus] -> alpha -> [Forge] -> G_{g+1}

Enforces:
- Rule 1: Protected Core Invariance (Core(G_{g+1}) == Core(G_g)).
- Rule 2: A syntactically valid witness identifier is required.
- Rule 3: Attenuated Influence (w(alpha, d) = (1/2)^d for 1 <= d <= 10; d > 10 evaporated).

AuthorityEffect: None.
Zero-Float Law: Uses exact rational arithmetic.

This low-level byte mutation helper does not authenticate a witness digest or
admit an antibody. The composition root must independently execute/bind its
checker before supplying experimental guidance, as the current feedback runner
does. Digest shape and this mutation receipt alone establish no task failure.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, NoReturn

from ..domain.lamarckian import (
    SHA256_HEX_PATTERN,
    CochainResidualV1,
    LamarckianMutationReceiptV1,
    LineageCureReceiptV1,
    ReproducedFailureCaseV1,
)
from ..domain.models import PromptGenomeV1, ProtectedSpanV1
from ..profile.cochain_profile import (
    PROMPT_COCHAIN_COMPLEX_PROFILE,
    ComplexConditionFailed,
)
from ..use_cases.forge import PromptMutationEngineV1


def _integer_boundary_entry(entry: object) -> int:
    """Keep an int or a whole float. Refuse a bool or a non-integer float."""
    if type(entry) is bool:
        raise ComplexConditionFailed(
            "d1*d0=0 complex condition failed: entry is not an exact integer or rational"
        )
    if type(entry) is int:
        return entry
    if type(entry) is Fraction:
        if entry.denominator != 1:
            raise ComplexConditionFailed(
                "d1*d0=0 complex condition failed: entry is not an exact integer"
            )
        return entry.numerator
    item = getattr(entry, "item", None)
    if callable(item):
        return _integer_boundary_entry(item())
    if type(entry) is float:
        if not entry.is_integer():
            raise ComplexConditionFailed(
                "d1*d0=0 complex condition failed: entry is not an exact integer or rational"
            )
        return int(entry)
    raise ComplexConditionFailed(
        "d1*d0=0 complex condition failed: entry is not an exact integer or rational"
    )


def _integer_boundary(matrix: object) -> list[list[int]]:
    """Convert an integer-valued boundary before the cochain verifier admits it."""
    if isinstance(matrix, (str, bytes)):
        raise ComplexConditionFailed("d1 and d0 dimensions do not compose")
    try:
        rows = list(matrix)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ComplexConditionFailed("d1 and d0 dimensions do not compose") from exc
    converted: list[list[int]] = []
    for row in rows:
        if isinstance(row, (str, bytes)):
            raise ComplexConditionFailed("d1 and d0 dimensions do not compose")
        try:
            entries = list(row)
        except TypeError as exc:
            raise ComplexConditionFailed("d1 and d0 dimensions do not compose") from exc
        converted.append([_integer_boundary_entry(entry) for entry in entries])
    return converted


class UnmeasuredCurvatureRefusal(Exception):  # noqa: N818
    """Refuse to publish a curvature triple when gamma2 and xi are unmeasured.

    The profile residual is not published as phi1. gamma2 and xi stay None.
    AuthorityEffect: None.
    """

    code = "UNMEASURED_CURVATURE"
    authority_effect = "None"

    def __init__(
        self,
        *,
        witness_sha256: str,
        obstructions: list[str],
    ) -> None:
        self.gamma2 = None
        self.xi = None
        self.published = False
        self.witness_sha256 = witness_sha256
        self.obstructions = tuple(obstructions)
        super().__init__(
            "UNMEASURED_CURVATURE: gamma2 and xi were not measured; "
            "refusing to publish CochainResidualV1"
        )


@dataclass(frozen=True, slots=True)
class LamarckianLoopResultV1:
    """Result of a protected-span mutation with caller-supplied witness metadata."""

    child_prompt_bytes: bytes
    child_genome_id: str
    receipt: LamarckianMutationReceiptV1
    mutation_applied: bool
    authority_effect: str = "None"


class LamarckianLoopService:
    """Application use case service driving the Lamarckian retro-inheritance loop."""

    def __init__(
        self,
        mutation_engine: PromptMutationEngineV1 | None = None,
    ) -> None:
        self.mutation_engine = mutation_engine or PromptMutationEngineV1()

    def execute_loop(
        self,
        *,
        parent_prompt_bytes: bytes,
        parent_genome_id: str,
        protected_spans: Sequence[ProtectedSpanV1],
        generation: int,
        falsification_witness_sha256: str,
        cochain_residual: CochainResidualV1,
        antibody_id: str,
        guidance_text: str,
        edit_start_byte: int | None = None,
        edit_end_byte: int | None = None,
        origin_generation: int | None = None,
    ) -> LamarckianLoopResultV1:
        """Execute one Lamarckian retro-inheritance step with fail-closed invariant enforcement."""
        # 1. Validate witness identifier syntax; authentication belongs to the caller.
        if not falsification_witness_sha256 or not SHA256_HEX_PATTERN.match(
            falsification_witness_sha256
        ):
            raise ValueError(
                f"WITNESS_GROUNDING_FAILED: Invalid or missing falsification witness: {falsification_witness_sha256!r}"
            )
        if cochain_residual.phi1_fraction == 0 and not falsification_witness_sha256:
            raise ValueError(
                "WITNESS_GROUNDING_FAILED: Zero cochain residual without defect witness"
            )

        # 2. Enforce Rule 3: Attenuated Influence & Hop Distance Bounds
        child_generation = generation + 1
        orig_gen = generation if origin_generation is None else origin_generation
        hop_distance = child_generation - orig_gen
        if hop_distance < 1 or hop_distance > 10:
            raise ValueError(
                f"HOP_DISTANCE_OUT_OF_BOUNDS: hop_distance={hop_distance} "
                f"(origin={orig_gen}, child={child_generation}). "
                "Antibodies with d > 10 must undergo formal constitutional canalization or evaporate."
            )

        attenuation_weight = LamarckianMutationReceiptV1.calculate_attenuation_weight(
            hop_distance
        )

        # 3. Format injection payload
        replacement_bytes = (
            f"\n\n# --- LAMARCKIAN IMMUNE GUIDANCE [hop={hop_distance}, weight={attenuation_weight}] ---\n"
            f"# Antibody: {antibody_id}\n"
            f"# Witness SHA256: {falsification_witness_sha256}\n"
            f"# Cochain Residual: Phi1={cochain_residual.phi1}, "
            f"Gamma2={cochain_residual.gamma2}, Xi={cochain_residual.xi}\n"
            f"{guidance_text}\n"
            f"# --------------------------------------------------------------------------------------\n"
        ).encode()

        # Determine target edit slice
        if edit_start_byte is None:
            edit_start_byte = len(parent_prompt_bytes)
        if edit_end_byte is None:
            edit_end_byte = edit_start_byte

        # 4. Enforce Rule 1: Protected Core Invariance via Mutation Engine
        child_prompt_bytes = self.mutation_engine.apply_mutation(
            original_bytes=parent_prompt_bytes,
            protected_spans=protected_spans,
            edit_start_byte=edit_start_byte,
            edit_end_byte=edit_end_byte,
            replacement_bytes=replacement_bytes,
        )

        # Post-mutation assertion: Core byte slices must be strictly identical
        for span in protected_spans:
            parent_slice = parent_prompt_bytes[span.start_byte : span.end_byte]
            # Since insertion happened at edit_start_byte:
            # If edit was strictly after the span, the span offset in child is unchanged
            if edit_start_byte >= span.end_byte:
                child_slice = child_prompt_bytes[span.start_byte : span.end_byte]
            else:
                delta = len(replacement_bytes) - (edit_end_byte - edit_start_byte)
                child_slice = child_prompt_bytes[
                    span.start_byte : span.end_byte + delta
                ]
            if child_slice != parent_slice:
                raise PermissionError(
                    f"PROTECTED_SPAN_MUTATION_REFUSED: Core span '{span.name}' was corrupted"
                )

        # 5. Content-addressed Child Genome Identity
        child_genome_id = f"sha256:{hashlib.sha256(child_prompt_bytes).hexdigest()}"

        # 6. Emit sealed LamarckianMutationReceiptV1
        receipt = LamarckianMutationReceiptV1.create(
            parent_genome_id=parent_genome_id,
            child_genome_id=child_genome_id,
            falsification_witness_sha256=falsification_witness_sha256,
            cochain_residual=cochain_residual,
            antibody_id=antibody_id,
            hop_distance=hop_distance,
            attenuation_weight=attenuation_weight,
        )

        return LamarckianLoopResultV1(
            child_prompt_bytes=child_prompt_bytes,
            child_genome_id=child_genome_id,
            receipt=receipt,
            mutation_applied=True,
            authority_effect="None",
        )

    @staticmethod
    def extract_cochain_from_ast(
        sources: dict[str, str],
    ) -> NoReturn:
        """Read an AST dependency complex and refuse an unmeasured curvature triple.

        The profile is admitted so a complex that fails that check does not
        continue. Its residual is not published as phi1. Gamma2 and xi are
        not measured, so no ``CochainResidualV1`` is published.
        """
        from pfp.domain.ast_cochain.ast_dependency_complex import (  # noqa: PLC0415
            DEFAULT_LAYER_RANKS,
            DependencyComplexBuilder,
        )
        from pfp.domain.ast_cochain.ast_source_parser import (  # noqa: PLC0415
            PythonSourceParser,
        )

        parser = PythonSourceParser()
        builder = DependencyComplexBuilder(DEFAULT_LAYER_RANKS)
        parsed = parser.parse(sources)
        complex_ = builder.build(parsed)

        obstructions = list(complex_.defect_descriptions)
        defect_bytes = (
            f"{len(obstructions)}:{','.join(sorted(obstructions))}".encode()
        )
        witness_sha256 = hashlib.sha256(defect_bytes).hexdigest()

        PROMPT_COCHAIN_COMPLEX_PROFILE.admit(
            _integer_boundary(complex_.d0),
            _integer_boundary(complex_.d1),
        )
        raise UnmeasuredCurvatureRefusal(
            witness_sha256=witness_sha256,
            obstructions=obstructions,
        )


class LamarckianReceiptStore:
    """Append-only JSONL ledger of ``LamarckianMutationReceiptV1`` lineage edges."""

    def __init__(self, path: Path | str, *, read_only: bool = False) -> None:
        self.path = Path(path)
        self.read_only = bool(read_only)

    def append(
        self,
        receipt: LamarckianMutationReceiptV1,
        *,
        parent_prompt_id: str | None = None,
        child_prompt_id: str | None = None,
    ) -> None:
        """Validate and append one mutation receipt line to the lineage JSONL ledger."""
        if self.read_only:
            raise PermissionError("LAMARCKIAN_RECEIPT_STORE_READ_ONLY")
        receipt.validate()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row: dict[str, Any] = dict(receipt.to_dict())
        if parent_prompt_id is not None:
            row["parent_prompt_id"] = parent_prompt_id
        if child_prompt_id is not None:
            row["child_prompt_id"] = child_prompt_id
        line = json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")

    def all_records(self) -> tuple[dict[str, Any], ...]:
        """Return all persisted receipt records in append order."""
        if not self.path.is_file():
            return ()
        records: list[dict[str, Any]] = []
        for raw_line in self.path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if stripped:
                records.append(json.loads(stripped))
        return tuple(records)


def _extract_antibody_field(antibody: Any, name: str, default: Any = None) -> Any:
    if isinstance(antibody, Mapping):
        return antibody.get(name, default)
    return getattr(antibody, name, default)


def spawn_antibody_constrained_child(
    *,
    parent_genome: PromptGenomeV1,
    parent_prompt_bytes: bytes,
    antibody: Any,
    falsification_witness_sha256: str,
    cochain_residual: CochainResidualV1,
    receipt_store: LamarckianReceiptStore,
    origin_generation: int | None = None,
) -> tuple[PromptGenomeV1, bytes, LamarckianMutationReceiptV1]:
    """Derive a child prompt constrained by an admitted antibody and append its receipt."""
    from .custody import ensure_caller_prompt_genome  # noqa: PLC0415

    ab_id = _extract_antibody_field(antibody, "antibody_id")
    status_raw = _extract_antibody_field(antibody, "pharmacy_status")
    status = status_raw.value if hasattr(status_raw, "value") else status_raw
    revoked = bool(_extract_antibody_field(antibody, "revoked", False))
    suspended = bool(_extract_antibody_field(antibody, "suspended", False))
    if status != "admitted" or revoked or suspended:
        raise ValueError(f"UNADMITTED_ANTIBODY_INJECTION:{ab_id!r}:{status!r}")
    if not isinstance(ab_id, str) or not ab_id.strip():
        raise ValueError("ANTIBODY_ID_REQUIRED")

    guidance_raw = (
        _extract_antibody_field(antibody, "guidance_text")
        or _extract_antibody_field(antibody, "description")
        or _extract_antibody_field(antibody, "target_pattern")
        or f"Avoid defect {ab_id}"
    )
    guidance = str(guidance_raw).strip()
    if not guidance.startswith("#"):
        guidance = f"# Constraint ({ab_id}): {guidance}"

    generation = 0 if origin_generation is None else int(origin_generation)
    loop_res = LamarckianLoopService().execute_loop(
        parent_prompt_bytes=parent_prompt_bytes,
        parent_genome_id=parent_genome.content_digest,
        protected_spans=parent_genome.protected_spans,
        generation=generation,
        falsification_witness_sha256=falsification_witness_sha256,
        cochain_residual=cochain_residual,
        antibody_id=ab_id,
        guidance_text=guidance,
    )
    child_bytes = loop_res.child_prompt_bytes
    child_genome = ensure_caller_prompt_genome(
        child_bytes,
        parent_genome.to_dict()["domain_model"],
        parents=[{"prompt_id": parent_genome.prompt_id, "generation": parent_genome.generation}],
        protected_spans=parent_genome.protected_spans,
    )
    receipt = LamarckianMutationReceiptV1.create(
        parent_genome_id=parent_genome.content_digest,
        child_genome_id=child_genome.content_digest,
        falsification_witness_sha256=falsification_witness_sha256,
        cochain_residual=cochain_residual,
        antibody_id=ab_id,
        hop_distance=loop_res.receipt.hop_distance,
    )
    receipt_store.append(
        receipt,
        parent_prompt_id=parent_genome.prompt_id,
        child_prompt_id=child_genome.prompt_id,
    )
    return child_genome, child_bytes, receipt


def load_active_lineage_antibodies(
    prompt_id: str,
    receipt_store: LamarckianReceiptStore | None,
    catalog: Any,
) -> tuple[tuple[dict[str, Any], ...], tuple[LamarckianMutationReceiptV1, ...]]:
    """Resolve active admitted antibodies within hop distance 1..10 along ancestor edges."""
    if receipt_store is None:
        return (), ()
    raw_records = receipt_store.all_records()
    if not raw_records:
        return (), ()

    by_child: dict[str, list[tuple[LamarckianMutationReceiptV1, str]]] = {}
    for row in raw_records:
        receipt = LamarckianMutationReceiptV1.from_dict(row)
        p_id = row.get("parent_prompt_id") or (
            "genome_" + receipt.parent_genome_id.removeprefix("sha256:")
        )
        c_id = row.get("child_prompt_id") or (
            "genome_" + receipt.child_genome_id.removeprefix("sha256:")
        )
        by_child.setdefault(c_id, []).append((receipt, p_id))

    max_dist_by_ab: dict[str, int] = {}
    receipts_by_ab: dict[str, list[LamarckianMutationReceiptV1]] = {}

    def _walk(node_id: str, cum_downstream: int, visited: frozenset[str]) -> None:
        for receipt, parent_id in by_child.get(node_id, ()):
            cum_dist = cum_downstream + receipt.hop_distance
            ab_id = receipt.antibody_id
            prev = max_dist_by_ab.get(ab_id, 0)
            if cum_dist > prev:
                max_dist_by_ab[ab_id] = cum_dist
            receipts_by_ab.setdefault(ab_id, []).append(receipt)
            if parent_id not in visited:
                _walk(parent_id, cum_dist, visited | {parent_id})

    _walk(prompt_id, 0, frozenset({prompt_id}))
    if not max_dist_by_ab:
        return (), ()

    entries = catalog.load_catalog().get("antibodies", {})
    active_records: list[dict[str, Any]] = []
    active_receipts: list[LamarckianMutationReceiptV1] = []
    seen_receipt_ids: set[str] = set()
    for ab_id, max_hop in max_dist_by_ab.items():
        if not (1 <= max_hop <= 10):
            continue
        rec = entries.get(ab_id)
        if not isinstance(rec, Mapping):
            continue
        if rec.get("pharmacy_status") != "admitted":
            continue
        if rec.get("revoked") or rec.get("suspended"):
            continue
        active_records.append(dict(rec))
        for r in receipts_by_ab.get(ab_id, ()):
            if r.receipt_id not in seen_receipt_ids:
                seen_receipt_ids.add(r.receipt_id)
                active_receipts.append(r)

    return tuple(active_records), tuple(active_receipts)


def verify_lineage_cure(
    *,
    parent_genome: PromptGenomeV1,
    child_genome: PromptGenomeV1,
    parent_prompt_bytes: bytes,
    child_prompt_bytes: bytes,
    mutation_receipt: LamarckianMutationReceiptV1,
    reproducing_case: ReproducedFailureCaseV1,
    child_reply_bytes: bytes,
    child_host_danger: Any | None,
    held_out_passed: bool = True,
    store: Any,
    cemetery: Any | None = None,
    taint_engine: Any | None = None,
) -> LineageCureReceiptV1:
    """Test whether a mutated child genome cured its parent's reproduced failure or relapsed."""
    import pfp_core.caller_feedback as cf  # noqa: PLC0415

    mutation_receipt.validate()
    if (
        mutation_receipt.parent_genome_id != parent_genome.content_digest
        or mutation_receipt.child_genome_id != child_genome.content_digest
    ):
        raise ValueError("LINEAGE_RECEIPT_GENOME_MISMATCH")

    for span in parent_genome.protected_spans:
        if len(child_prompt_bytes) < span.end_byte or (
            parent_prompt_bytes[span.start_byte : span.end_byte]
            != child_prompt_bytes[span.start_byte : span.end_byte]
        ):
            raise PermissionError("PROTECTED_SPAN_MUTATION_REFUSED")

    parent_verdict = cf.screen_caller_turn(
        cf.ImmuneScreenRequestV1(
            lineage=cf.CallerLineageContextV1(prompt_id=parent_genome.prompt_id),
            prompt_utf8_bytes=reproducing_case.prompt_utf8_bytes,
            candidate_reply_bytes=reproducing_case.parent_failing_reply_bytes,
            signal2_danger=cf.host_danger(
                "PUBLIC_CHECK_FAILED",
                "host.public_smoke",
                reproducing_case.witness_sha256,
            ),
        ),
        store,
    )
    antibody_fired_on_parent = mutation_receipt.antibody_id in parent_verdict.fired_antibody_ids

    child_verdict = cf.screen_caller_turn(
        cf.ImmuneScreenRequestV1(
            lineage=cf.CallerLineageContextV1(prompt_id=child_genome.prompt_id),
            prompt_utf8_bytes=child_prompt_bytes,
            candidate_reply_bytes=child_reply_bytes,
            signal2_danger=child_host_danger,
        ),
        store,
    )
    child_signal1_fired = mutation_receipt.antibody_id in child_verdict.fired_antibody_ids
    host_failure_reproduced = (
        (child_host_danger is not None)
        or (not held_out_passed)
        or (child_verdict.disposition == cf.HOLD)
    )

    if child_host_danger is not None:
        receipt_material = (
            f"{child_host_danger.observer_id}:{child_host_danger.danger_type}:{child_host_danger.evidence_digest}"
        ).encode()
    else:
        receipt_material = child_reply_bytes + (
            b":held_out_pass" if held_out_passed else b":held_out_fail"
        )
    child_checker_receipt_sha256 = "sha256:" + hashlib.sha256(receipt_material).hexdigest()

    relapsed = host_failure_reproduced or child_signal1_fired or (not antibody_fired_on_parent)
    if relapsed:
        if cemetery is not None:
            from adversary.stage.domain.genealogy import CemeteryHeadstoneV1  # noqa: PLC0415

            cemetery.record_headstone(
                CemeteryHeadstoneV1(
                    candidate_id=child_genome.prompt_id,
                    run_key=reproducing_case.case_id,
                    scene_id="lineage_cure",
                    cause_of_death=f"RELAPSED_ON_PARENT_FAILURE:{mutation_receipt.antibody_id}",
                    killing_seat_id="eis_cure_verifier",
                    evidence_refs=(mutation_receipt.antibody_id,),
                    candidate_payload_sha256="sha256:" + hashlib.sha256(child_reply_bytes).hexdigest(),
                )
            )
        if taint_engine is not None:
            taint_engine.mark_tainted(child_genome.prompt_id)
        cure_status = "RELAPSED_BURIED"
    else:
        cure_status = "CURED_ADOPTED"

    return LineageCureReceiptV1.create(
        parent_genome_id=parent_genome.content_digest,
        child_genome_id=child_genome.content_digest,
        lamarckian_receipt_id=mutation_receipt.receipt_id,
        antibody_id=mutation_receipt.antibody_id,
        antibody_screened=bool(mutation_receipt.antibody_id),
        antibody_fired_on_parent_failure=antibody_fired_on_parent,
        child_signal1_fired=child_signal1_fired,
        host_failure_reproduced=host_failure_reproduced,
        child_checker_receipt_sha256=child_checker_receipt_sha256,
        cure_status=cure_status,
    )


__all__ = [
    "LamarckianLoopResultV1",
    "LamarckianLoopService",
    "LamarckianReceiptStore",
    "UnmeasuredCurvatureRefusal",
    "load_active_lineage_antibodies",
    "spawn_antibody_constrained_child",
    "verify_lineage_cure",
]
