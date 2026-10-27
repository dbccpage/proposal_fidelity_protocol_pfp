"""Checkable architecture metadata; this module executes no mathematical solver.

Source-byte commitments, nominal typing, finite tree shape and declaration
bindings are validated. Success never verifies a theorem, a signature, density
positivity, channel laws, DPO confluence, or native runtime acceptance.
AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)

Identifier = Annotated[
    StrictStr, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z][A-Za-z0-9_.:-]*$")
]
Digest = Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
Natural = Annotated[StrictInt, Field(ge=0, le=1_048_576)]
Positive = Annotated[StrictInt, Field(ge=1, le=1_048_576)]


def _canonical_rational(value: str) -> str:
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("expected a canonical exact rational string") from error
    if str(parsed) != value:
        raise ValueError("noncanonical rational alias")
    return value


RationalToken = Annotated[
    StrictStr, Field(min_length=1, max_length=4096), AfterValidator(_canonical_rational)
]


class SpecificationMetadata(BaseModel):
    """Frozen metadata carriers with no implicit coercion or unknown fields."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)


class ArtifactRef(SpecificationMetadata):
    artifact_id: Identifier
    path: Annotated[StrictStr, Field(min_length=1, max_length=4096)]
    sha256: Digest
    byte_length: Natural
    media_type: Annotated[StrictStr, Field(min_length=1, max_length=128)]


class SourceDocument(SpecificationMetadata):
    source_id: Identifier
    artifact_id: Identifier
    content_utf8: Annotated[StrictStr, Field(max_length=65_536)]
    coordinate_profile: Literal["utf8-bytes-half-open-v1"] = "utf8-bytes-half-open-v1"


class SourceByteSpan(SpecificationMetadata):
    span_id: Identifier
    source_id: Identifier
    source_sha256: Digest
    start_byte: Natural
    end_byte: Natural
    span_sha256: Digest
    colour: Identifier

    @model_validator(mode="after")
    def nonempty_interval(self) -> Self:
        if self.start_byte >= self.end_byte:
            raise ValueError("source span must be a nonempty half-open byte interval")
        return self


class NominalColour(SpecificationMetadata):
    colour_id: Identifier
    payload_schema_artifact_id: Identifier
    interpretation_artifact_id: Identifier


class BoundObligation(SpecificationMetadata):
    obligation_id: Identifier
    kind: Identifier
    subject_artifact_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=32)]
    evidence_artifact_id: Identifier
    verification_status: Literal["declared_unverified"] = "declared_unverified"


class CongruenceIdeal(SpecificationMetadata):
    ideal_id: Identifier
    relation_artifact_id: Identifier
    substitution_closure: BoundObligation
    action: Literal["quotient_declaration", "typed_null_tree"]
    enforcement_status: Literal["not_executed"] = "not_executed"

    @model_validator(mode="after")
    def relation_binding(self) -> Self:
        if self.relation_artifact_id not in self.substitution_closure.subject_artifact_ids:
            raise ValueError("ideal obligation must bind the declared relation")
        return self


class OperatorSignature(SpecificationMetadata):
    operator_id: Identifier
    input_colours: Annotated[tuple[Identifier, ...], Field(max_length=32)]
    output_colour: Identifier
    polarity: Literal["constructive", "annihilator", "interrogative", "verifier"]
    effect_class: Literal["pure", "provider", "clock", "signing", "external_write"]
    work_limit: Positive
    semantics_artifact_id: Identifier
    ideal_ids: Annotated[tuple[Identifier, ...], Field(max_length=32)] = ()
    equivariance: BoundObligation

    @model_validator(mode="after")
    def semantic_binding(self) -> Self:
        if self.semantics_artifact_id not in self.equivariance.subject_artifact_ids:
            raise ValueError("equivariance obligation must bind this operation")
        return self


class LeafNode(SpecificationMetadata):
    kind: Literal["leaf"]
    node_id: Identifier
    span_id: Identifier
    colour: Identifier


class GraftNode(SpecificationMetadata):
    """input_permutation[slot] indexes children for that operator input slot."""

    kind: Literal["graft"]
    node_id: Identifier
    operator_id: Identifier
    children: Annotated[tuple[Identifier, ...], Field(max_length=32)]
    input_permutation: Annotated[tuple[Natural, ...], Field(max_length=32)]


class NullTreeNode(SpecificationMetadata):
    """A typed failed term; it is never a zero matrix or a density operator."""

    kind: Literal["null_tree"]
    node_id: Identifier
    colour: Identifier
    refusal_code: Identifier
    evidence_artifact_id: Identifier


TreeNode = Annotated[LeafNode | GraftNode | NullTreeNode, Field(discriminator="kind")]


class GraftTree(SpecificationMetadata):
    tree_id: Identifier
    nodes: Annotated[tuple[TreeNode, ...], Field(min_length=1, max_length=256)]
    root: Identifier
    expected_output_colour: Identifier


DPO_OWNER = "pfp.domain.rewriting.finite_dpo.apply_registered_rule"
DENSITY_OWNER = "core_quantum_physics::density_matrix::ExactDensityMatrix"
DPO_OBLIGATIONS = frozenset(
    {
        "monic_interfaces",
        "injective_match",
        "dangling",
        "identification",
        "attribute_compatibility",
        "pushout_complement",
        "pushout",
        "critical_pair_coverage",
        "critical_pair_joinability",
        "well_founded_termination",
    }
)


class DPODeclaration(SpecificationMetadata):
    declaration_id: Identifier
    owner: Literal["pfp.domain.rewriting.finite_dpo.apply_registered_rule"] = DPO_OWNER
    owner_source_artifact_id: Identifier
    supported_schema: Literal["finite-attributed-directed-graph-identity-key-monic-v1"]
    rule_artifact_id: Identifier
    schema_artifact_id: Identifier
    left_artifact_id: Identifier
    interface_artifact_id: Identifier
    right_artifact_id: Identifier
    host_artifact_id: Identifier
    match_artifact_id: Identifier
    obligations: Annotated[tuple[BoundObligation, ...], Field(min_length=10, max_length=32)]
    verification_status: Literal["declaration_only_no_rewrite_or_confluence_verified"] = (
        "declaration_only_no_rewrite_or_confluence_verified"
    )

    @model_validator(mode="after")
    def complete_artifact_obligations(self) -> Self:
        _unique(self.obligations, "obligation_id")
        kinds = [obligation.kind for obligation in self.obligations]
        if len(kinds) != len(set(kinds)) or not DPO_OBLIGATIONS <= set(kinds):
            raise ValueError(
                "DPO obligations must uniquely cover the declared structural and confluence duties"
            )
        required = {
            self.rule_artifact_id,
            self.schema_artifact_id,
            self.left_artifact_id,
            self.interface_artifact_id,
            self.right_artifact_id,
            self.host_artifact_id,
            self.match_artifact_id,
        }
        for obligation in self.obligations:
            if not required <= set(obligation.subject_artifact_ids):
                raise ValueError(
                    "each DPO obligation must bind the entire declared rewrite context"
                )
        return self


class TensorFactor(SpecificationMetadata):
    factor_id: Identifier
    dimension: Positive


class FiniteFiber(SpecificationMetadata):
    fiber_id: Identifier
    base_observation_artifact_id: Identifier
    dimension: Positive
    tensor_factors: Annotated[tuple[TensorFactor, ...], Field(max_length=16)]
    interpretation_artifact_id: Identifier
    semantic_status: Literal["finite_model_declaration_only"] = "finite_model_declaration_only"

    @model_validator(mode="after")
    def declared_dimension_product(self) -> Self:
        _unique(self.tensor_factors, "factor_id")
        product = 1
        for factor in self.tensor_factors:
            product *= factor.dimension
            if product > 1_048_576:
                raise ValueError("declared tensor dimension exceeds metadata bound")
        if product != self.dimension:
            raise ValueError("fiber dimension must equal its declared factor-dimension product")
        return self


class EpistemicBundleDeclaration(SpecificationMetadata):
    """Finite vector-bundle/sheaf metadata; no gluing or cocycle solver runs."""

    bundle_id: Identifier
    base_artifact_id: Identifier
    cover_artifact_id: Identifier
    transition_artifact_id: Identifier
    sheaf_artifact_id: Identifier
    fiber_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=64)]
    rank: Positive
    cocycle_obligations: Annotated[tuple[BoundObligation, ...], Field(min_length=3, max_length=32)]
    verification_status: Literal["declared_unverified_no_bundle_sheaf_or_gluing_theorem"] = (
        "declared_unverified_no_bundle_sheaf_or_gluing_theorem"
    )

    @model_validator(mode="after")
    def declared_cocycle_duties(self) -> Self:
        if len(set(self.fiber_ids)) != len(self.fiber_ids):
            raise ValueError("bundle fiber identities must be unique")
        _unique(self.cocycle_obligations, "obligation_id")
        kinds = [obligation.kind for obligation in self.cocycle_obligations]
        if len(kinds) != len(set(kinds)) or not {"identity", "inverse", "triple_overlap"} <= set(
            kinds
        ):
            raise ValueError("bundle needs distinct identity, inverse and triple-overlap duties")
        required = {
            self.base_artifact_id,
            self.cover_artifact_id,
            self.transition_artifact_id,
            self.sheaf_artifact_id,
        }
        if any(
            not required <= set(obligation.subject_artifact_ids)
            for obligation in self.cocycle_obligations
        ):
            raise ValueError(
                "cocycle obligations must bind base, cover, transition and sheaf artifacts"
            )
        return self


class DensityDeclaration(SpecificationMetadata):
    density_id: Identifier
    fiber_id: Identifier
    dimension: Positive
    coefficient_domain: Literal["Q(i)"] = "Q(i)"
    matrix_artifact_id: Identifier
    owner: Literal["core_quantum_physics::density_matrix::ExactDensityMatrix"] = DENSITY_OWNER
    owner_source_artifact_id: Identifier
    obligations: Annotated[tuple[BoundObligation, ...], Field(min_length=3, max_length=16)]
    verification_status: Literal["matrix_not_loaded_hermiticity_trace_psd_not_verified"] = (
        "matrix_not_loaded_hermiticity_trace_psd_not_verified"
    )

    @model_validator(mode="after")
    def declared_density_duties(self) -> Self:
        _unique(self.obligations, "obligation_id")
        kinds = [obligation.kind for obligation in self.obligations]
        if len(kinds) != len(set(kinds)) or not {
            "hermiticity",
            "trace_one",
            "positive_semidefinite",
        } <= set(kinds):
            raise ValueError(
                "density declaration needs distinct hermiticity, trace-one and PSD obligations"
            )
        if any(
            self.matrix_artifact_id not in obligation.subject_artifact_ids
            for obligation in self.obligations
        ):
            raise ValueError("density obligations must bind their matrix artifact")
        return self


class PartialTraceRGStep(SpecificationMetadata):
    step_id: Identifier
    fine_density_id: Identifier
    coarse_density_id: Identifier
    trace_factor_id: Identifier
    operation: Literal["partial_trace_first", "partial_trace_second"]
    owner: Literal["core_quantum_physics::density_matrix::ExactDensityMatrix"] = DENSITY_OWNER
    owner_source_artifact_id: Identifier
    channel_artifact_id: Identifier
    scale_parameter: RationalToken
    channel_laws: BoundObligation
    wilsonian_interpretation_artifact_id: Identifier | None = None
    verification_status: Literal[
        "finite_partial_trace_declared_no_rg_or_channel_theorem_verified"
    ] = "finite_partial_trace_declared_no_rg_or_channel_theorem_verified"


class ReceiptCommon(SpecificationMetadata):
    receipt_id: Identifier
    task_artifact_id: Identifier
    candidate_artifact_id: Identifier
    witness_artifact_id: Identifier
    outcome_artifact_id: Identifier
    authority_effect: Literal["None"] = "None"
    acceptance_status: Literal["metadata_only_not_native_acceptance"] = (
        "metadata_only_not_native_acceptance"
    )


class UnsignedBenchmarkReceiptMetadata(ReceiptCommon):
    kind: Literal["unsigned_benchmark"]
    signature_status: Literal["not_supplied"] = "not_supplied"


class SignedReceiptMetadata(ReceiptCommon):
    kind: Literal["signed_metadata"]
    algorithm: Literal["Ed25519"]
    public_key_hex: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{64}$")]
    signature_hex: Annotated[StrictStr, Field(pattern=r"^[0-9a-f]{128}$")]
    signed_payload_artifact_id: Identifier
    trust_policy_artifact_id: Identifier
    verifier_source_artifact_id: Identifier
    signature_status: Literal["supplied_not_cryptographically_verified"] = (
        "supplied_not_cryptographically_verified"
    )


ReceiptMetadata = Annotated[
    UnsignedBenchmarkReceiptMetadata | SignedReceiptMetadata, Field(discriminator="kind")
]


def _unique(values: tuple, key: str) -> dict:
    indexed = {getattr(value, key): value for value in values}
    if len(indexed) != len(values):
        raise ValueError(f"duplicate {key}")
    return indexed


def _artifact_references(value: object):
    if isinstance(value, BaseModel):
        for name in type(value).model_fields:
            child = getattr(value, name)
            if name == "artifact_id" or name.endswith("_artifact_id"):
                if child is not None:
                    yield child
            elif name.endswith("_artifact_ids"):
                yield from child
            else:
                yield from _artifact_references(child)
    elif isinstance(value, tuple):
        for child in value:
            yield from _artifact_references(child)


class ArchitectureSpec(SpecificationMetadata):
    schema_version: Literal["oepfp.operad-architecture.metadata.v1"]
    spec_id: Identifier
    authority_effect: Literal["None"] = "None"
    validation_effect: Literal[
        "source_bindings_and_metadata_only_no_theorem_signature_psd_confluence_or_runtime_acceptance"
    ] = "source_bindings_and_metadata_only_no_theorem_signature_psd_confluence_or_runtime_acceptance"
    artifacts: Annotated[tuple[ArtifactRef, ...], Field(min_length=1, max_length=512)]
    sources: Annotated[tuple[SourceDocument, ...], Field(min_length=1, max_length=64)]
    spans: Annotated[tuple[SourceByteSpan, ...], Field(min_length=1, max_length=256)]
    colours: Annotated[tuple[NominalColour, ...], Field(min_length=1, max_length=64)]
    ideals: Annotated[tuple[CongruenceIdeal, ...], Field(max_length=64)]
    operators: Annotated[tuple[OperatorSignature, ...], Field(min_length=1, max_length=128)]
    trees: Annotated[tuple[GraftTree, ...], Field(min_length=1, max_length=64)]
    dpo_declarations: Annotated[tuple[DPODeclaration, ...], Field(max_length=32)]
    fibers: Annotated[tuple[FiniteFiber, ...], Field(max_length=64)]
    bundles: Annotated[tuple[EpistemicBundleDeclaration, ...], Field(max_length=64)]
    densities: Annotated[tuple[DensityDeclaration, ...], Field(max_length=64)]
    rg_steps: Annotated[tuple[PartialTraceRGStep, ...], Field(max_length=64)]
    receipts: Annotated[tuple[ReceiptMetadata, ...], Field(min_length=1, max_length=64)]

    @model_validator(mode="after")
    def check_finite_declaration_bindings(self) -> Self:
        artifacts = _unique(self.artifacts, "artifact_id")
        missing = set(_artifact_references(self)) - artifacts.keys()
        if missing:
            raise ValueError(f"unknown artifact references: {sorted(missing)}")
        sources = _unique(self.sources, "source_id")
        spans = _unique(self.spans, "span_id")
        colours = _unique(self.colours, "colour_id")
        ideals = _unique(self.ideals, "ideal_id")
        operators = _unique(self.operators, "operator_id")
        _unique(self.trees, "tree_id")
        _unique(self.dpo_declarations, "declaration_id")
        _unique(self.rg_steps, "step_id")
        _unique(self.receipts, "receipt_id")
        for source in sources.values():
            encoded = source.content_utf8.encode("utf-8")
            artifact = artifacts[source.artifact_id]
            if (
                len(encoded) > 65_536
                or len(encoded) != artifact.byte_length
                or hashlib.sha256(encoded).hexdigest() != artifact.sha256
            ):
                raise ValueError("source byte length/hash does not match its artifact")
        for span in spans.values():
            if span.source_id not in sources or span.colour not in colours:
                raise ValueError("span references unknown source or nominal colour")
            source = sources[span.source_id]
            encoded = source.content_utf8.encode("utf-8")
            if span.source_sha256 != artifacts[source.artifact_id].sha256 or span.end_byte > len(
                encoded
            ):
                raise ValueError("span source binding or bounds mismatch")
            segment = encoded[span.start_byte : span.end_byte]
            segment.decode("utf-8")  # Refuse intervals cutting through a code point.
            if hashlib.sha256(segment).hexdigest() != span.span_sha256:
                raise ValueError("source span bytes do not match span hash")
        for operator in operators.values():
            if not set(operator.input_colours + (operator.output_colour,)) <= colours.keys():
                raise ValueError("operator uses an undeclared nominal colour")
            if not set(operator.ideal_ids) <= ideals.keys():
                raise ValueError("operator uses an undeclared congruence ideal")
        for tree in self.trees:
            _check_tree(tree, spans, colours, operators)
        fibers = _unique(self.fibers, "fiber_id")
        _unique(self.bundles, "bundle_id")
        for bundle in self.bundles:
            if any(fiber_id not in fibers for fiber_id in bundle.fiber_ids):
                raise ValueError("bundle references an unknown fiber")
            if any(fibers[fiber_id].dimension != bundle.rank for fiber_id in bundle.fiber_ids):
                raise ValueError("bundle fiber dimension does not match its declared rank")
        densities = _unique(self.densities, "density_id")
        for declaration in self.dpo_declarations:
            _require_owner_source(
                artifacts,
                declaration.owner_source_artifact_id,
                "pfp/domain/rewriting/finite_dpo.py",
            )
        for receipt in self.receipts:
            if isinstance(receipt, SignedReceiptMetadata):
                _require_owner_source(
                    artifacts,
                    receipt.verifier_source_artifact_id,
                    "engine/crates_rs/core_epistemic_immune_system/src/authenticated.rs",
                )
        for density in densities.values():
            _require_owner_source(
                artifacts,
                density.owner_source_artifact_id,
                "engine/crates_rs/core_quantum_physics/src/density_matrix.rs",
            )
            if (
                density.fiber_id not in fibers
                or density.dimension != fibers[density.fiber_id].dimension
            ):
                raise ValueError("density/fiber identity or dimension mismatch")
        for step in self.rg_steps:
            _require_owner_source(
                artifacts,
                step.owner_source_artifact_id,
                "engine/crates_rs/core_quantum_physics/src/density_matrix.rs",
            )
            if step.fine_density_id not in densities or step.coarse_density_id not in densities:
                raise ValueError("RG step references an unknown density declaration")
            fine = densities[step.fine_density_id]
            coarse = densities[step.coarse_density_id]
            fine_factors = fibers[fine.fiber_id].tensor_factors
            coarse_factors = fibers[coarse.fiber_id].tensor_factors
            index = 0 if step.operation == "partial_trace_first" else 1
            if len(fine_factors) != 2 or fine_factors[index].factor_id != step.trace_factor_id:
                raise ValueError(
                    "existing owner requires an explicit matching two-factor partial trace"
                )
            if coarse_factors != (fine_factors[1 - index],):
                raise ValueError("coarse fiber must retain exactly the untraced factor")
            required = {
                fine.matrix_artifact_id,
                coarse.matrix_artifact_id,
                step.channel_artifact_id,
            }
            if not required <= set(step.channel_laws.subject_artifact_ids):
                raise ValueError(
                    "channel-law declaration must bind fine, coarse and channel artifacts"
                )
        return self


def _require_owner_source(artifacts: dict, artifact_id: str, path: str) -> None:
    if artifacts[artifact_id].path != path:
        raise ValueError("owner source artifact does not name the existing declared owner")


def _check_tree(tree: GraftTree, spans: dict, colours: dict, operators: dict) -> None:
    seen: dict[str, str] = {}
    consumed: set[str] = set()
    for node in tree.nodes:
        if node.node_id in seen:
            raise ValueError("duplicate tree node")
        if isinstance(node, LeafNode):
            if node.span_id not in spans or node.colour != spans[node.span_id].colour:
                raise ValueError("leaf span/colour binding mismatch")
            colour = node.colour
        elif isinstance(node, NullTreeNode):
            if len(tree.nodes) != 1:
                raise ValueError("typed NullTree is a standalone failed term")
            colour = node.colour
        else:
            operator = operators.get(node.operator_id)
            if operator is None or len(node.children) != len(operator.input_colours):
                raise ValueError("unknown operator or graft arity mismatch")
            if sorted(node.input_permutation) != list(range(len(node.children))):
                raise ValueError("input permutation must be a bijection on all slots")
            if len(set(node.children)) != len(node.children) or any(
                child in consumed for child in node.children
            ):
                raise ValueError("tree nodes cannot be reused")
            if any(child not in seen for child in node.children):
                raise ValueError("children must precede their parent in topological order")
            if any(
                seen[node.children[node.input_permutation[slot]]] != expected
                for slot, expected in enumerate(operator.input_colours)
            ):
                raise ValueError("graft nominal input colour mismatch")
            consumed.update(node.children)
            colour = operator.output_colour
        if colour not in colours:
            raise ValueError("tree uses an undeclared nominal colour")
        seen[node.node_id] = colour
    if tree.root != tree.nodes[-1].node_id or consumed != set(seen) - {tree.root}:
        raise ValueError("tree must have one connected final root and no unused nodes")
    if seen[tree.root] != tree.expected_output_colour:
        raise ValueError("tree output colour mismatch")


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_architecture_json(raw: str | bytes) -> ArchitectureSpec:
    """Parse UTF-8 JSON without duplicate-key loss, then validate metadata only."""
    text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
    value = json.loads(text, object_pairs_hook=_unique_json_object)
    return ArchitectureSpec.model_validate_json(
        json.dumps(value, ensure_ascii=False, allow_nan=False)
    )
