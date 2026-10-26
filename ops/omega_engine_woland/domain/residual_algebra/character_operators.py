"""Character operator catalog and deterministic package dispatch.

This module owns Role-A package construction only.  It does not value Φ,
license transitions, synthesize dialogue, or perform I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from omega_engine_woland.domain.residual_algebra.residual_package import (
    ResidualTypedPackage,
)
from omega_engine_woland.domain.residual_algebra.residual_sorts import (
    R_CONTEXT_TRANSPORT,
    R_COVERT_VERIFICATION,
    R_EXACTNESS_WITNESS,
    R_EXECUTABLE_RUNTIME,
    R_GAUGE_BREAK,
    R_GOVERNANCE_AUDIT,
    R_METHODICAL_COMPLETION,
    R_PHYSICAL_CONSTRAINT,
    R_PREDICTION_ERROR,
    R_PRESENTATION_GAUGE,
    R_PRIOR_LOCK,
    R_PRODUCT_EDGE,
    R_QUARANTINE,
    R_RECORD_CUSTODY,
    R_RED,
    R_RETRACTION_DEFECT,
    R_STABLE_EQUILIBRIUM,
    R_STOCHASTIC_FRICTION,
    R_TRUTH_REPAIR,
    R_WHITE,
    Residual1Cochain,
    ResidualSort,
)

CarrierDict = Dict[str, Any]


@dataclass(frozen=True)
class CharacterOperatorSpec:
    """Declarative data required to construct one deterministic operator."""

    key: str
    aliases: Tuple[str, ...]
    residual_sort: ResidualSort
    updates: Tuple[Tuple[str, Any], ...]
    witness_data: Tuple[Any, ...]
    nonclaim: str

    def matches(self, normalized_name: str) -> bool:
        return any(alias in normalized_name for alias in self.aliases)


# Keep source ordering: dispatch historically used an if/elif chain, so first
# matching specification remains authoritative when aliases overlap.
_OPERATOR_SPECS: Tuple[CharacterOperatorSpec, ...] = (
    CharacterOperatorSpec(
        key="annushka",
        aliases=("annushka", "e_annushka"),
        residual_sort=R_STOCHASTIC_FRICTION,
        updates=(("turnstile_friction", True), ("oil_spilled_on_tracks", True)),
        witness_data=("annushka_sunflower_oil_turnstile",),
        nonclaim="Noise injection is diagnostic stress-testing; does not mint executive authority.",
    ),
    CharacterOperatorSpec(
        key="bezdomny",
        aliases=("predictive", "bezdomny", "e_predictive"),
        residual_sort=R_PREDICTION_ERROR,
        updates=(("priors_updated", True), ("run_journal_logged", True)),
        witness_data=("prediction_error_assimilated_into_journal",),
        nonclaim="Journal entries are historical empirical evidence; do not grant executive license.",
    ),
    CharacterOperatorSpec(
        key="koroviev",
        aliases=("nocebo", "koroviev", "e_nocebo"),
        residual_sort=R_RED,
        updates=(("adversarial_inversion_applied", True), ("mocking_arithmetic_verified", True)),
        witness_data=("koroviev_checked_jacket_arithmetic",),
        nonclaim="Nocebo findings are diagnostic challenges; do not create permanent debt if disproven.",
    ),
    CharacterOperatorSpec(
        key="bengalsky",
        aliases=("anti_hype", "bengalsky", "e_anti_hype"),
        residual_sort=R_WHITE,
        updates=(("hype_words_excised", True), ("head_severed_and_reattached_humbled", True)),
        witness_data=("bengalsky_unearned_claims_purged",),
        nonclaim="Anti-hype audit enforces claim discipline; does not confer automatic promotion.",
    ),
    CharacterOperatorSpec(
        key="begemot",
        aliases=("surprise", "begemot", "e_surprise"),
        residual_sort=R_PRESENTATION_GAUGE,
        updates=(("nine_dot_gauge_jump", True), ("primus_gasoline_chessboard_swapped", True)),
        witness_data=("begemot_gs001_gauge_break",),
        nonclaim="Nine-dot lateral gambits must still traverse 8-stage waist; comedy is not an ActionLicense bypass.",
    ),
    CharacterOperatorSpec(
        key="azazello",
        aliases=("scope", "azazello", "e_scope"),
        residual_sort=R_RED,
        updates=(("execution_capped_at_10_rounds", True), ("firewall_enforced", True)),
        witness_data=("azazello_fanged_scope_cap",),
        nonclaim="Scope muscle terminates non-converging loops; does not mint executive overrides.",
    ),
    CharacterOperatorSpec(
        key="stravinsky",
        aliases=("flow", "stravinsky", "e_flow"),
        residual_sort=R_QUARANTINE,
        updates=(
            ("epistemic_quarantine_cleared", True),
            ("csikszentmihalyi_flow_stabilized", True),
        ),
        witness_data=("stravinsky_two_ivans_stabilization",),
        nonclaim="Quarantine provides epistemic stabilization; not punitive deletion.",
    ),
    CharacterOperatorSpec(
        key="master",
        aliases=("formal", "master", "e_formal"),
        residual_sort=R_EXACTNESS_WITNESS,
        updates=(("lean4_manuscript_restored", True), ("zero_sorry_lake_build", True)),
        witness_data=("master_manuscripts_dont_burn_lean4",),
        nonclaim="Formal mechanization produces verifiable receipts; subject to external kernel checks.",
    ),
    CharacterOperatorSpec(
        key="margarita",
        aliases=("placebo", "margarita", "e_placebo"),
        residual_sort=R_PRIOR_LOCK,
        updates=(("courage_prior_attached", True), ("unvarnished_residual_honesty", True)),
        witness_data=("margarita_queen_of_ball_courage",),
        nonclaim="Generative hope is an exploration frame; never an ActionLicense.",
    ),
    CharacterOperatorSpec(
        key="hella",
        aliases=("hygiene", "hella", "e_hygiene"),
        residual_sort="syntax_hygiene_residual",
        updates=(("syntax_sanitized", True), ("cp1252_mojibake_purged", True)),
        witness_data=("hella_cold_syntax_vampire_sanitization",),
        nonclaim="Hygiene filter is stateless syntax scrubbing; never alters mathematical logic.",
    ),
    CharacterOperatorSpec(
        key="jeremy",
        aliases=("yankee", "jeremy", "e_yankee_solver"),
        residual_sort=R_EXECUTABLE_RUNTIME,
        updates=(("yankee_physics_rigor", True), ("working_python_executable", True)),
        witness_data=("jeremy_yankee_solver_runtime",),
        nonclaim="Executable prototypes verify empirical claims; do not substitute for formal Lean 4 kernels.",
    ),
    CharacterOperatorSpec(
        key="polina",
        aliases=("polina", "e_polina_gauge_breaker"),
        residual_sort=R_GAUGE_BREAK,
        updates=(
            ("southern_wit_zinger_delivered", True),
            ("jeremy_knocked_on_ass", True),
            ("gauge_reset", True),
        ),
        witness_data=("polina_razor_sharp_wit_puncture",),
        nonclaim="Comedic puncture resets cognitive overconfidence; does not bypass Gate-11 validation.",
    ),
    CharacterOperatorSpec(
        key="liudmila",
        aliases=("luda", "liudmila", "e_luda_resilience"),
        residual_sort=R_STABLE_EQUILIBRIUM,
        updates=(("soviet_90s_calm_wisdom", True), ("manufactured_panic_dissolved", True)),
        witness_data=("liudmila_calm_problem_solving",),
        nonclaim="Equilibrium stabilization resolves operational paralysis; preserves all true structural obligations.",
    ),
    CharacterOperatorSpec(
        key="yaroslava",
        aliases=("yaroslava", "e_yaroslava_discipline"),
        residual_sort=R_METHODICAL_COMPLETION,
        updates=(
            ("punctual_delivery_verified", True),
            ("methodical_completion_zero_loose_ends", True),
        ),
        witness_data=("yaroslava_punctual_discipline",),
        nonclaim="Methodical task execution satisfies delivery schedules; does not mint unearned authority.",
    ),
    CharacterOperatorSpec(
        key="ratslayer",
        aliases=("ratslayer", "krysoboy", "e_ratslayer"),
        residual_sort=R_PHYSICAL_CONSTRAINT,
        updates=(
            ("physical_hardware_limits_enforced", True),
            ("memory_and_cpu_bounds_guarded", True),
        ),
        witness_data=("ratslayer_centurion_discipline",),
        nonclaim="Physical hardware constraints reflect reality; never mint speculative authority.",
    ),
    CharacterOperatorSpec(
        key="pilate",
        aliases=("pilate", "e_pilate"),
        residual_sort=R_GOVERNANCE_AUDIT,
        updates=(("hand_washing_detected", True), ("hemicrania_diagnosed", True)),
        witness_data=("pilate_governance_cowardice_audited",),
        nonclaim="Governance audits evaluate procedural honesty; cannot override formal kernels.",
    ),
    CharacterOperatorSpec(
        key="yeshua",
        aliases=("yeshua", "e_yeshua"),
        residual_sort=R_TRUTH_REPAIR,
        updates=(
            ("truth_repair_applied", True),
            ("hemicrania_dissolved", True),
            ("all_men_are_good", True),
        ),
        witness_data=("yeshua_finite_truth_repair_exact_coboundary",),
        nonclaim="Truth is self-verifying under formal observation; requires no artificial executive license.",
    ),
    CharacterOperatorSpec(
        key="abadonna",
        aliases=("abadonna", "e_abadonna", "annihilator"),
        residual_sort=R_RETRACTION_DEFECT,
        updates=(
            ("continuous_relaxations_purged", True),
            ("discrete_exact_rational_enforced", True),
        ),
        witness_data=("abadonna_zero_backdoor_annihilator",),
        nonclaim="Zero-backdoor purge eliminates continuous heuristics; does not mint executive license.",
    ),
    CharacterOperatorSpec(
        key="natasha",
        aliases=("natasha", "e_natasha", "context_transport"),
        residual_sort=R_CONTEXT_TRANSPORT,
        updates=(
            ("lossless_context_transport_verified", True),
            ("anointed_fast_path_routed", True),
        ),
        witness_data=("natasha_witch_flight_transport",),
        nonclaim="Fast-path context transport preserves topological invariants; does not bypass structural gates.",
    ),
    CharacterOperatorSpec(
        key="levy_matvei",
        aliases=("levy_matvei", "levy", "e_levy_matvei", "parchment_custody"),
        residual_sort=R_RECORD_CUSTODY,
        updates=(
            ("transcript_fidelity_verified", True),
            ("parchment_custody_recorded", True),
        ),
        witness_data=("levy_matvei_unyielding_record_custody",),
        nonclaim="Transcript custody preserves unedited execution history; does not validate theorem truth.",
    ),
    CharacterOperatorSpec(
        key="aphranius",
        aliases=("aphranius", "e_aphranius", "covert_verification"),
        residual_sort=R_COVERT_VERIFICATION,
        updates=(
            ("covert_receipt_verified", True),
            ("false_green_eliminated", True),
        ),
        witness_data=("aphranius_secret_guard_verification",),
        nonclaim="Covert verification confirms empirical signals independently; does not mint mathematical authority.",
    ),
    CharacterOperatorSpec(
        key="woland",
        aliases=("terminal", "woland", "e_terminal"),
        residual_sort=R_EXACTNESS_WITNESS,
        updates=(("terminal_gate_evaluated", True), ("reality_arbiter_verified", True)),
        witness_data=("woland_adversarial_terminal_gate",),
        nonclaim="Woland terminal verdicts are immutable proposals subject to human authority minting.",
    ),
)


def _build_package(spec: CharacterOperatorSpec) -> ResidualTypedPackage[CarrierDict]:
    """Construct a Φ-blind residual package from declarative operator data."""

    def pure_transform(carrier: CarrierDict) -> CarrierDict:
        transformed = dict(carrier)
        transformed.update(spec.updates)
        return transformed

    def observation_maps(pre: CarrierDict, post: CarrierDict) -> Residual1Cochain:
        return Residual1Cochain(
            residual_sort=spec.residual_sort,
            mass=0.0,
            defects=(),
            witness_data=spec.witness_data,
        )

    return ResidualTypedPackage(
        residual_in=spec.residual_sort,
        pure_transform=pure_transform,
        observation_maps=observation_maps,
        residual_out=spec.residual_sort,
        nonclaim=spec.nonclaim,
    )


def _find_spec(name_or_op: str) -> CharacterOperatorSpec | None:
    normalized = name_or_op.strip().lower()
    return next((spec for spec in _OPERATOR_SPECS if spec.matches(normalized)), None)


class CharacterOperatorRegistry:
    """Resolve names to deterministic character residual packages."""

    @staticmethod
    def get_operator_package(name_or_op: str) -> ResidualTypedPackage[CarrierDict]:
        spec = _find_spec(name_or_op)
        return (
            _build_package(spec)
            if spec is not None
            else CharacterOperatorRegistry._make_generic_pkg(name_or_op)
        )

    @staticmethod
    def registered_specs() -> Tuple[CharacterOperatorSpec, ...]:
        """Expose immutable catalog data for inspection/tests without mutability."""
        return _OPERATOR_SPECS

    @staticmethod
    def _make_generic_pkg(name: str) -> ResidualTypedPackage[CarrierDict]:
        def pure_transform(carrier: CarrierDict) -> CarrierDict:
            transformed = dict(carrier)
            transformed[f"{name}_executed"] = True
            return transformed

        def observation_maps(pre: CarrierDict, post: CarrierDict) -> Residual1Cochain:
            return Residual1Cochain(
                residual_sort=R_PRODUCT_EDGE,
                mass=0.0,
                defects=(),
                witness_data=(f"generic_{name}_execution",),
            )

        return ResidualTypedPackage(
            residual_in=R_PRODUCT_EDGE,
            pure_transform=pure_transform,
            observation_maps=observation_maps,
            residual_out=R_PRODUCT_EDGE,
            nonclaim="Generic diagnostic operator; AuthorityEffect: None.",
        )
