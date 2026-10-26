"""Entities and Aggregate Root for the Grammar Bounded Context.

Enforces:
- Domain Purity (no frameworks, pure language types)
- Exact-Type Equality (RULE_VO_EXACT_TYPE_EQUALITY_001)
- Result Monad Error Handling (RULE_ROP_RESULT_MONAD_001)
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Optional, Sequence

from omega_engine_pfp.domain.mssn_research.grammar.authority import (
    DialectContainer,
    HodgePacket,
    IndObjectPacket,
    MasterHorizonPacket,
)
from omega_engine_pfp.domain.mssn_research.grammar.exact_structures import (
    DownMapObstruction,
    EdgeInvolution,
    ExactRationalTensor,
    ProtectedDistinction,
    QuarantinedShadowPacket,
    ReversalMap,
)
from omega_engine_pfp.domain.mssn_research.grammar.lexical import (
    Alphabet,
    FrontierCandidate,
    ProbabilityMass,
    QuantifierMask,
)
from omega_engine_pfp.domain.mssn_research.grammar.quantification import (
    BoundedAlternationBlock,
    ExactPhi4Certificate,
)
from omega_engine_pfp.domain.mssn_research.grammar.rewriting import (
    BQNFRoute,
    BQNFViewCochain,
    DDAEventRecord,
    PolygraphPacket,
)
from omega_engine_pfp.domain.mssn_research.grammar.spectral_geometry import (
    AutopoieticExpansionCyclePacket,
    Regge4DPacket,
    ZetaShadowPacket,
)
from omega_engine_pfp.domain.mssn_research.shared_kernel.result import Err, Ok, Refusal, Result
from omega_engine_pfp.domain.mssn_research.shared_kernel.value_objects import StageLevel

from ..packets.entities import Packet
from ..packets.value_objects import Opcode, RefusalCode
from .errors import (
    AlphabetViolationError,
    AlternationBudgetError,
    AlternationDepthExceededError,
    AuthorityBoundaryError,
    AutopoieticCycleError,
    BQNFRoutingError,
    DDAEventVerificationError,
    DialectChecksumError,
    DualCavityGapError,
    FrontierInconsistencyError,
    GrammarDomainError,
    HodgeDecompositionError,
    IndObjectMorphismError,
    PolygraphConfluenceError,
    ReggeSimplicialError,
    TensorInvariantError,
    ZeroRetainedMassError,
    ZetaSpectralQuarantineError,
)


def _frontier_error(message: str) -> FrontierInconsistencyError:
    return FrontierInconsistencyError(code=RefusalCode.WRONG_ARITY, message=message)


def _validate_frontier(
    vocabulary_size: int,
    candidates: tuple[FrontierCandidate, ...],
    retained_mass: Fraction,
) -> Result[bool, GrammarDomainError]:
    if len(candidates) > vocabulary_size:
        return Err(_frontier_error(
            f"Candidate count ({len(candidates)}) exceeds declared vocabulary size ({vocabulary_size})"
        ))
    token_ids = [candidate.token_id for candidate in candidates]
    if len(set(token_ids)) != len(token_ids):
        return Err(_frontier_error("Duplicate candidate token ID in frontier"))
    invalid = next((candidate for candidate in candidates
                    if not 0 <= candidate.token_id < vocabulary_size), None)
    if invalid is not None:
        return Err(_frontier_error(
            f"Candidate token ID {invalid.token_id} out of bounds [0, {vocabulary_size})"
        ))
    probability_result = _validate_frontier_probabilities(candidates, retained_mass)
    if probability_result.is_err():
        return probability_result
    return _validate_conditioning(candidates, retained_mass)


def _validate_frontier_probabilities(
    candidates: tuple[FrontierCandidate, ...],
    retained_mass: Fraction,
) -> Result[bool, GrammarDomainError]:
    base_sum = sum((Fraction(item.base_probability.numerator, item.base_probability.denominator)
                    for item in candidates), Fraction(0))
    if base_sum != retained_mass:
        return Err(_frontier_error(
            f"Sum of candidate base probabilities ({base_sum}) does not match retained mass ({retained_mass})"
        ))
    constrained_sum = sum((Fraction(item.constrained_probability.numerator,
                                    item.constrained_probability.denominator)
                           for item in candidates), Fraction(0))
    if constrained_sum != Fraction(1):
        return Err(_frontier_error(
            f"Sum of constrained probabilities ({constrained_sum}) must equal 1"
        ))
    return Ok(True)


def _validate_conditioning(
    candidates: tuple[FrontierCandidate, ...],
    retained_mass: Fraction,
) -> Result[bool, GrammarDomainError]:
    for candidate in candidates:
        base = Fraction(candidate.base_probability.numerator, candidate.base_probability.denominator)
        constrained = Fraction(
            candidate.constrained_probability.numerator,
            candidate.constrained_probability.denominator,
        )
        expected = base / retained_mass
        if constrained != expected:
            return Err(_frontier_error(
                f"Candidate token ID {candidate.token_id} constrained probability ({constrained}) "
                f"does not match conditioned value ({expected})"
            ))
    return Ok(True)


@dataclass(frozen=True)
class TokenFrontier:
    """Entity representing an evaluated incremental token generation frontier."""
    vocabulary_size: int
    support_width: int
    masked_token_count: int
    retained_mass: ProbabilityMass
    candidates: tuple[FrontierCandidate, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.candidates, tuple):
            object.__setattr__(self, "candidates", tuple(self.candidates))

    @classmethod
    def create(
        cls,
        vocabulary_size: int,
        candidates: Sequence[FrontierCandidate],
        retained_mass: ProbabilityMass,
    ) -> Result[TokenFrontier, GrammarDomainError]:
        """Factory method validating frontier structural and probability invariants."""
        if retained_mass.is_zero():
            return Refusal(ZeroRetainedMassError(
                code=RefusalCode.ZERO_RETAINED_MASS,
                message="Retained probability mass dropped to zero; zero unconstrained token escapes"
            ))

        cand_tuple = tuple(candidates)
        expected_base = Fraction(retained_mass.mass.numerator, retained_mass.mass.denominator)
        validation = _validate_frontier(vocabulary_size, cand_tuple, expected_base)
        if validation.is_err():
            return validation
        support_w = len(cand_tuple)
        return Ok(cls(
            vocabulary_size=vocabulary_size,
            support_width=support_w,
            masked_token_count=vocabulary_size - support_w,
            retained_mass=retained_mass,
            candidates=cand_tuple,
        ))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TokenFrontier)
        return (
            self.vocabulary_size == other.vocabulary_size
            and self.support_width == other.support_width
            and self.masked_token_count == other.masked_token_count
            and self.retained_mass == other.retained_mass
            and self.candidates == other.candidates
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.vocabulary_size,
            self.support_width,
            self.masked_token_count,
            self.retained_mass,
            self.candidates,
        ))


@dataclass(frozen=True)
class TowerGrammar:
    """Aggregate Root for the Grammar Bounded Context at a specific stage level."""
    stage_level: StageLevel
    alphabet: Alphabet
    admitted_opcodes: frozenset[Opcode]
    max_alternation_depth: int = 12

    def __post_init__(self) -> None:
        if not isinstance(self.stage_level, StageLevel):
            raise TypeError("stage_level must be a StageLevel")
        if not isinstance(self.alphabet, Alphabet):
            raise TypeError("alphabet must be an Alphabet")
        if not isinstance(self.admitted_opcodes, frozenset):
            object.__setattr__(self, "admitted_opcodes", frozenset(self.admitted_opcodes))

    @classmethod
    def for_stage(cls, stage: StageLevel) -> TowerGrammar:
        """Construct the canonical stage grammar specification."""
        if stage.level == 0:
            alpha = Alphabet.level_0()
            opcodes: frozenset[Opcode] = frozenset()
            max_depth = 0
        elif stage.level == 1:
            alpha = Alphabet.level_1()
            opcodes = frozenset([Opcode.from_int(0)])
            max_depth = 1
        else:
            alpha = Alphabet.for_stage(stage)
            # Collect all registered opcodes whose stage floor <= current stage
            opcodes_list = [
                Opcode.from_int(dec)
                for dec in Opcode.registered_decimals()
                if Opcode.from_int(dec).stage_floor <= stage
            ]
            opcodes = frozenset(opcodes_list)
            max_depth = stage.level

        return cls(stage_level=stage, alphabet=alpha, admitted_opcodes=opcodes, max_alternation_depth=max_depth)

    def validate_tensor_application(self, tensor: ExactRationalTensor) -> Result[bool, GrammarDomainError]:
        """Validate a higher-order tensor application against stage invariants."""
        if self.stage_level.level < 8:
            return Refusal(TensorInvariantError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Tensor product applications require Stage 8 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.foundational_policies import (
            check_tensor_product_invariants,
        )
        return check_tensor_product_invariants(tensor)

    def validate_atom_characters(self, s: str) -> Result[bool, GrammarDomainError]:
        """Verify that all characters in an atom belong to the stage's active alphabet."""
        if self.stage_level.level == 0:
            return Refusal(AlphabetViolationError(
                code=RefusalCode.INACTIVE_SYMBOL,
                message="Level 0 admits no atom characters; only primitive Diff <> is valid"
            ))
        for idx, char in enumerate(s):
            if not self.alphabet.contains(char):
                return Refusal(AlphabetViolationError(
                    code=RefusalCode.INACTIVE_SYMBOL,
                    message=f"Character {char!r} at index {idx} outside stage {self.stage_level.level} alphabet"
                ))
        return Ok(True)

    def evaluate_frontier(
        self,
        vocabulary_size: int,
        candidates: Sequence[FrontierCandidate],
        retained_mass: ProbabilityMass,
    ) -> Result[TokenFrontier, GrammarDomainError]:
        """Evaluate an incremental generation frontier under grammar licensing invariants."""
        return TokenFrontier.create(vocabulary_size, candidates, retained_mass)

    def check_quantifier_mask(self, mask: QuantifierMask) -> Result[bool, GrammarDomainError]:
        """Validate quantifier alternation depth against the declared stage budget."""
        depth = mask.alternation_depth
        if depth > self.max_alternation_depth:
            return Refusal(AlternationDepthExceededError(
                code=RefusalCode.HOST_VERIFICATION_REQUIRED,
                message=f"Alternation depth {depth} exceeds stage limit {self.max_alternation_depth}"
            ))
        return Ok(True)

    def parse_packet(self, raw_wire: str) -> Result[Packet, GrammarDomainError]:
        """Compile a wire string into a verified Packet aggregate root."""
        res = Packet.from_wire(
            raw_wire,
            self.stage_level,
            alphabet=self.alphabet,
            admitted_opcodes=self.admitted_opcodes,
        )
        if isinstance(res, Err):
            return Err(AlphabetViolationError(code=res.error.code, message=res.error.message))
        elif isinstance(res, Refusal):
            return Refusal(AlphabetViolationError(code=res.refusal.code, message=res.refusal.message))
        return Ok(res.unwrap())

    def validate_polygraph(self, packet: PolygraphPacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 11 Polygraph packet against stage floor and peak join confluence."""
        if self.stage_level.level < 11:
            return Refusal(PolygraphConfluenceError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Polygraph packets require Stage 11 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.rewriting_policies import (
    check_peak_claim_confluence,
    check_step_continuity,
)
        step_res = check_step_continuity(packet.step_list)
        if step_res.is_err() or step_res.is_refusal():
            return step_res
        return check_peak_claim_confluence(packet.peak_claim)

    def validate_dda_event(self, event: DDAEventRecord) -> Result[bool, GrammarDomainError]:
        """Validate a Level 12 DDA event record against stage floor and proof-relevant invariants."""
        if self.stage_level.level < 12:
            return Refusal(DDAEventVerificationError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"DDA event records require Stage 12 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.rewriting_policies import (
            check_dda_event_proof,
        )
        return check_dda_event_proof(event)

    def validate_bqnf_repair(self, cochain: BQNFViewCochain, route: BQNFRoute) -> Result[bool, GrammarDomainError]:
        """Validate a Level 13 BQNF cochain repair against exact 0-potential witness."""
        if self.stage_level.level < 13:
            return Refusal(BQNFRoutingError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"BQNF cochains require Stage 13 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.rewriting_policies import (
            check_bqnf_route_repair,
        )
        return check_bqnf_route_repair(cochain, route)

    def validate_bounded_alternation(self, block: BoundedAlternationBlock) -> Result[bool, GrammarDomainError]:
        """Validate a Level 14 bounded quantifier alternation block."""
        if self.stage_level.level < 14:
            return Refusal(AlternationBudgetError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Bounded alternation blocks require Stage 14 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.quantifier_policies import (
            check_bounded_quantifier_block,
        )
        return check_bounded_quantifier_block(block)

    def validate_phi4_certificate(self, cert: ExactPhi4Certificate) -> Result[bool, GrammarDomainError]:
        """Validate a Level 14 exact degree-4 cavity LP weak duality certificate."""
        if self.stage_level.level < 14:
            return Refusal(DualCavityGapError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Phi_4 cavity certificates require Stage 14 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.quantifier_policies import (
            check_phi4_dual_certificate,
        )
        return check_phi4_dual_certificate(cert)

    def validate_master_horizon(self, packet: MasterHorizonPacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 15 Master Horizon packet against stage floor and authority calculus."""
        if self.stage_level.level < 15:
            return Refusal(AuthorityBoundaryError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Master horizon packets require Stage 15 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.authority_policies import (
            check_master_horizon_authority,
        )
        return check_master_horizon_authority(packet)

    def validate_ind_object(self, packet: IndObjectPacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 16 Ind-Object diagram packet against stage floor and conservative morphisms."""
        if self.stage_level.level < 16:
            return Refusal(IndObjectMorphismError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Ind-object packets require Stage 16 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.authority_policies import (
            check_ind_object_morphism,
        )
        return check_ind_object_morphism(packet)

    def validate_dialect_container(self, container: DialectContainer) -> Result[bool, GrammarDomainError]:
        """Validate a Level 17 Dialect Container against stage floor and checksum integrity."""
        if self.stage_level.level < 17:
            return Refusal(DialectChecksumError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Dialect containers require Stage 17 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.authority_policies import (
            check_dialect_container_integrity,
        )
        return check_dialect_container_integrity(container)

    def validate_hodge_decomposition(self, packet: HodgePacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 18 discrete l^2 Hodge decomposition packet against stage floor and exact reconstruction."""
        if self.stage_level.level < 18:
            return Refusal(HodgeDecompositionError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Hodge decomposition packets require Stage 18 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.authority_policies import (
            check_hodge_decomposition,
        )
        return check_hodge_decomposition(packet)

    def validate_zeta_shadow(self, packet: ZetaShadowPacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 19 Zeta spectral shadow packet against stage floor and quarantine fence."""
        if self.stage_level.level < 19:
            return Refusal(ZetaSpectralQuarantineError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Zeta spectral shadow packets require Stage 19 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.spectral_policies import (
            check_zeta_spectral_quarantine,
        )
        return check_zeta_spectral_quarantine(packet)

    def validate_autopoietic_cycle(self, packet: AutopoieticExpansionCyclePacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 20 Autopoietic cycle packet against stage floor and recursion preservation."""
        if self.stage_level.level < 20:
            return Refusal(AutopoieticCycleError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Autopoietic cycle packets require Stage 20 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.spectral_policies import (
            check_autopoietic_expansion_cycle,
        )
        return check_autopoietic_expansion_cycle(packet)

    def validate_regge_4d(self, packet: Regge4DPacket) -> Result[bool, GrammarDomainError]:
        """Validate a Level 21 Discrete 4D Regge simplicial curvature packet against stage floor and non-linear Bianchi closure."""
        if self.stage_level.level < 21:
            return Refusal(ReggeSimplicialError(
                code=RefusalCode.UNKNOWN_OPCODE,
                message=f"Regge 4D simplicial packets require Stage 21 or higher; current is Stage {self.stage_level.level}"
            ))
        from omega_engine_pfp.domain.mssn_research.grammar.spectral_policies import (
            check_regge_4d_simplicial_curvature,
        )
        return check_regge_4d_simplicial_curvature(packet)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, TowerGrammar)
        return (
            self.stage_level == other.stage_level
            and self.alphabet == other.alphabet
            and self.admitted_opcodes == other.admitted_opcodes
            and self.max_alternation_depth == other.max_alternation_depth
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.stage_level,
            self.alphabet,
            self.admitted_opcodes,
            self.max_alternation_depth,
        ))

    def __repr__(self) -> str:
        return f"TowerGrammar(stage={self.stage_level.level}, opcodes={len(self.admitted_opcodes)})"


def _down_map_obstruction(
    model: AntimorphismTransitionModel,
    target_stage: StageLevel,
    projection: dict[str, str],
) -> DownMapObstruction | None:
    distinction = next(
        (item for item in model.protected_distinctions if item.is_collapsed_by(projection)),
        None,
    )
    if distinction is None:
        return None
    collapsed = projection.get(distinction.state_a, distinction.state_a)
    return DownMapObstruction(
        source_stage=model.stage_level,
        target_stage=target_stage,
        obstructed_distinction=distinction,
        collapsed_target_state=collapsed,
        message=(f"Down-map projection from stage {model.stage_level.level} to {target_stage.level} "
                 f"erases protected distinction ({distinction.state_a}, {distinction.state_b}) -> {collapsed}"),
    )


def _project_transition_model(
    model: AntimorphismTransitionModel,
    target_stage: StageLevel,
    state_projection: dict[str, str],
    edge_projection: dict[str, str],
) -> AntimorphismTransitionModel:
    involutions = tuple(EdgeInvolution(
        source_edge=edge_projection.get(item.source_edge, item.source_edge),
        reversed_edge=edge_projection.get(item.reversed_edge, item.reversed_edge),
    ) for item in model.reversal_map.involutions)
    distinctions = frozenset(ProtectedDistinction(
        state_projection.get(item.state_a, item.state_a),
        state_projection.get(item.state_b, item.state_b),
        label=item.label,
    ) for item in model.protected_distinctions if not item.is_collapsed_by(state_projection))
    original_id = model.model_id.split("/lift_")[0]
    return AntimorphismTransitionModel(
        model_id=original_id if "/lift_" in model.model_id else f"{model.model_id}/down_{target_stage.level}",
        stage_level=target_stage,
        states=frozenset(state_projection.get(state, state) for state in model.states),
        edges=frozenset(edge_projection.get(edge, edge) for edge in model.edges),
        reversal_map=ReversalMap(involutions),
        protected_distinctions=distinctions,
    )


@dataclass(frozen=True)
class DownMapQuarantineRequest:
    """Arguments for an obstructable down-map and its quarantine sink."""

    target_stage: StageLevel
    state_projection: dict[str, str]
    edge_projection: Optional[dict[str, str]] = None
    quarantine_ledger: Optional[EpistemicQuarantineLedger] = None
    target_theorem: Optional[str] = None


@dataclass(frozen=True)
class AntimorphismTransitionModel:
    """Small transition model equipped with an explicit reversal map and protected distinctions.

    Evaluates:
    1. Involution law: ((e)^dag)^dag == e
    2. Contravariant composition: (e1 . e2)^dag == e2^dag . e1^dag
    3. Conservative retraction across lift and down map: d_n o u_n == id
    4. Fail-stop refusal on protected distinction erasure.
    """
    model_id: str
    stage_level: StageLevel
    states: frozenset[str]
    edges: frozenset[str]
    reversal_map: ReversalMap
    protected_distinctions: frozenset[ProtectedDistinction]

    def __post_init__(self) -> None:
        if not isinstance(self.stage_level, StageLevel):
            raise TypeError("stage_level must be a StageLevel")
        if not isinstance(self.states, frozenset):
            object.__setattr__(self, "states", frozenset(self.states))
        if not isinstance(self.edges, frozenset):
            object.__setattr__(self, "edges", frozenset(self.edges))
        if not isinstance(self.reversal_map, ReversalMap):
            raise TypeError("reversal_map must be a ReversalMap")
        if not isinstance(self.protected_distinctions, frozenset):
            object.__setattr__(self, "protected_distinctions", frozenset(self.protected_distinctions))

    def reverse_edge(self, edge: str) -> Result[str, DownMapObstruction]:
        """Reverse an individual edge under the contravariant involution."""
        rev = self.reversal_map.reverse(edge)
        if rev is None:
            return Err(DownMapObstruction(
                source_stage=self.stage_level,
                target_stage=self.stage_level,
                obstructed_distinction=ProtectedDistinction(edge, "bot", label="irreversible_edge"),
                collapsed_target_state="bot",
                message=f"Edge '{edge}' is irreversible (obstructed involution)",
            ))
        return Ok(rev)

    def reverse_path(self, path: Sequence[str]) -> Result[tuple[str, ...], DownMapObstruction]:
        """Reverse a sequence of edges contravariantly: (e1 . e2)^dag = e2^dag . e1^dag."""
        reversed_steps: list[str] = []
        for edge in reversed(path):
            step_res = self.reverse_edge(edge)
            if step_res.is_err():
                return step_res
            reversed_steps.append(step_res.unwrap())
        return Ok(tuple(reversed_steps))

    def satisfies_involution(self) -> bool:
        """Check involution law across all edges in the model."""
        return self.reversal_map.satisfies_involution_law()

    def lift(self, target_stage: StageLevel) -> AntimorphismTransitionModel:
        """Conservative embedding u_n: S_n -> S_{n+1} into a higher stage."""
        if target_stage <= self.stage_level:
            raise ValueError(f"Lift target stage {target_stage.level} must be > current {self.stage_level.level}")
        return AntimorphismTransitionModel(
            model_id=f"{self.model_id}/lift_{target_stage.level}",
            stage_level=target_stage,
            states=self.states,
            edges=self.edges,
            reversal_map=self.reversal_map,
            protected_distinctions=self.protected_distinctions,
        )

    def down_map(
        self,
        target_stage: StageLevel,
        state_projection: dict[str, str],
        edge_projection: Optional[dict[str, str]] = None,
    ) -> Result[AntimorphismTransitionModel, DownMapObstruction]:
        """Antimorphic down map d_n: S_{n} -> S_{n-1} enforcing zero data-loss on protected distinctions."""
        if target_stage >= self.stage_level:
            raise ValueError(f"Down-map target stage {target_stage.level} must be < current {self.stage_level.level}")
        obstruction = _down_map_obstruction(self, target_stage, state_projection)
        if obstruction is not None:
            return Err(obstruction)
        return Ok(_project_transition_model(
            self, target_stage, state_projection, edge_projection or {}
        ))

    def down_map_with_quarantine(
        self,
        request: DownMapQuarantineRequest,
    ) -> Result[AntimorphismTransitionModel, QuarantinedObstruction]:
        """Down-map projection that automatically commits any encountered obstruction to Stage 10 epistemic quarantine.

        If projection preserves all protected distinctions, returns Ok(contracted_model).
        If projection erases any protected distinction, constructs a DownMapObstruction,
        emits a QuarantinedShadowPacket, commits it to the EpistemicQuarantineLedger,
        and returns Err(QuarantinedObstruction(...)).
        """
        ledger = request.quarantine_ledger or EpistemicQuarantineLedger(
            ledger_id=f"quarantine/{self.model_id}"
        )
        down_res = self.down_map(
            target_stage=request.target_stage,
            state_projection=request.state_projection,
            edge_projection=request.edge_projection,
        )
        if down_res.is_ok():
            return Ok(down_res.unwrap())

        obstruction = down_res.error
        updated_ledger, shadow_packet = ledger.commit_obstruction(
            obstruction=obstruction,
            target_theorem=request.target_theorem,
        )
        return Err(QuarantinedObstruction(
            obstruction=obstruction,
            packet=shadow_packet,
            ledger=updated_ledger,
        ))

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, AntimorphismTransitionModel)
        return (
            self.model_id == other.model_id
            and self.stage_level == other.stage_level
            and self.states == other.states
            and self.edges == other.edges
            and self.reversal_map == other.reversal_map
            and self.protected_distinctions == other.protected_distinctions
        )

    def __hash__(self) -> int:
        return hash((
            type(self),
            self.model_id,
            self.stage_level,
            self.states,
            self.edges,
            self.reversal_map,
            self.protected_distinctions,
        ))

    def __repr__(self) -> str:
        return (
            f"AntimorphismTransitionModel(id={self.model_id!r}, stage={self.stage_level.level}, "
            f"|V|={len(self.states)}, |E|={len(self.edges)}, |D|={len(self.protected_distinctions)})"
        )


@dataclass(frozen=True)
class QuarantinedObstruction:
    """Composite refusal record packaging an obstruction, its shadow packet, and the updated quarantine ledger."""
    obstruction: DownMapObstruction
    packet: QuarantinedShadowPacket
    ledger: EpistemicQuarantineLedger

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, QuarantinedObstruction)
        return (
            self.obstruction == other.obstruction
            and self.packet == other.packet
            and self.ledger == other.ledger
        )

    def __hash__(self) -> int:
        return hash((type(self), self.obstruction, self.packet, self.ledger))

    def __repr__(self) -> str:
        return (
            f"QuarantinedObstruction(obstruction={self.obstruction}, "
            f"shadow_packet={self.packet.target_theorem!r}, "
            f"ledger_entries={self.ledger.entry_count})"
        )


@dataclass(frozen=True)
class EpistemicQuarantineLedger:
    """Stage 10+ append-only epistemic quarantine ledger (Permanent Quarantine Law).

    Stores quarantined shadow packets resulting from rejected promotion assertions,
    un-reconstructed profunctors, and obstructed down-map projections under the
    Zero Data-Loss Invariant.
    """
    ledger_id: str
    stage_level: StageLevel = StageLevel(10)
    entries: tuple[QuarantinedShadowPacket, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.ledger_id, str):
            raise TypeError("ledger_id must be a str")
        if not isinstance(self.stage_level, StageLevel):
            raise TypeError("stage_level must be a StageLevel")
        if self.stage_level.level < 10:
            raise ValueError(f"EpistemicQuarantineLedger stage floor is Stage 10, got Stage {self.stage_level.level}")
        if not isinstance(self.entries, tuple):
            object.__setattr__(self, "entries", tuple(self.entries))
        for item in self.entries:
            if not isinstance(item, QuarantinedShadowPacket):
                raise TypeError(f"All ledger entries must be QuarantinedShadowPacket, got {type(item)}")

    @property
    def entry_count(self) -> int:
        return len(self.entries)

    def commit(self, packet: QuarantinedShadowPacket) -> EpistemicQuarantineLedger:
        """Append a QuarantinedShadowPacket to the append-only ledger."""
        if not isinstance(packet, QuarantinedShadowPacket):
            raise TypeError(f"Can only commit QuarantinedShadowPacket to EpistemicQuarantineLedger, got {type(packet)}")
        return EpistemicQuarantineLedger(
            ledger_id=self.ledger_id,
            stage_level=self.stage_level,
            entries=(*self.entries, packet),
        )

    def commit_obstruction(
        self,
        obstruction: DownMapObstruction,
        target_theorem: Optional[str] = None,
        raw_transcript: Sequence[str] = (),
    ) -> tuple[EpistemicQuarantineLedger, QuarantinedShadowPacket]:
        """Convert a DownMapObstruction to QuarantinedShadowPacket and commit to the ledger."""
        shadow_packet = obstruction.to_quarantined_shadow_packet(
            target_theorem=target_theorem,
            raw_transcript=raw_transcript,
        )
        updated_ledger = self.commit(shadow_packet)
        return updated_ledger, shadow_packet

    def find_by_theorem(self, target_theorem: str) -> Optional[QuarantinedShadowPacket]:
        """Find the first quarantined shadow packet matching a target theorem."""
        for entry in self.entries:
            if entry.target_theorem == target_theorem:
                return entry
        return None

    def verify_isolation_against_stage(self, target_stage: StageLevel) -> Result[bool, GrammarDomainError]:
        """Verify that no quarantined packet in this ledger can be promoted/imported into target_stage (FW-SCOPE)."""
        from omega_engine_pfp.domain.mssn_research.grammar.foundational_policies import (
            check_permanent_quarantine_isolation,
        )
        for entry in self.entries:
            res = check_permanent_quarantine_isolation(entry, target_stage)
            if res.is_err() or res.is_refusal():
                return res
        return Ok(True)

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        assert isinstance(other, EpistemicQuarantineLedger)
        return (
            self.ledger_id == other.ledger_id
            and self.stage_level == other.stage_level
            and self.entries == other.entries
        )

    def __hash__(self) -> int:
        return hash((type(self), self.ledger_id, self.stage_level, self.entries))

    def __repr__(self) -> str:
        return f"EpistemicQuarantineLedger(id={self.ledger_id!r}, stage={self.stage_level.level}, count={len(self.entries)})"

