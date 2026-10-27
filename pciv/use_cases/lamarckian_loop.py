"""Lamarckian Retro-Inheritance Loop Service (NF-02).

Orchestrates the Lamarckian feedback cycle:
T_loop = <P_0, G_g> -> [Adversary Dialectic] -> Artifact A -> [PFP Measurement] -> Defect Witness W -> [Thymus] -> Antibody alpha -> [Forge] -> G_{g+1}

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
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, NoReturn, Optional, Sequence

from ..domain.lamarckian import (
    SHA256_HEX_PATTERN,
    CochainResidualV1,
    LamarckianMutationReceiptV1,
)
from ..domain.models import ProtectedSpanV1
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


class UnmeasuredCurvatureRefusal(Exception):
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
        obstructions: List[str],
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
        mutation_engine: Optional[PromptMutationEngineV1] = None,
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
        edit_start_byte: Optional[int] = None,
        edit_end_byte: Optional[int] = None,
        origin_generation: Optional[int] = None,
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
            f"# Cochain Residual: Phi1={cochain_residual.phi1}, Gamma2={cochain_residual.gamma2}, Xi={cochain_residual.xi}\n"
            f"{guidance_text}\n"
            f"# --------------------------------------------------------------------------------------\n"
        ).encode("utf-8")

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
        sources: Dict[str, str],
    ) -> NoReturn:
        """Read an AST dependency complex and refuse an unmeasured curvature triple.

        The profile is admitted so a complex that fails that check does not
        continue. Its residual is not published as phi1. Gamma2 and xi are
        not measured, so no ``CochainResidualV1`` is published.
        """
        from pfp.domain.ast_cochain.ast_dependency_complex import (
            DEFAULT_LAYER_RANKS,
            DependencyComplexBuilder,
        )
        from pfp.domain.ast_cochain.ast_source_parser import (
            PythonSourceParser,
        )

        parser = PythonSourceParser()
        builder = DependencyComplexBuilder(DEFAULT_LAYER_RANKS)
        parsed = parser.parse(sources)
        complex_ = builder.build(parsed)

        obstructions = list(complex_.defect_descriptions)
        defect_bytes = (
            f"{len(obstructions)}:{','.join(sorted(obstructions))}".encode("utf-8")
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


__all__ = [
    "LamarckianLoopResultV1",
    "LamarckianLoopService",
    "UnmeasuredCurvatureRefusal",
]
