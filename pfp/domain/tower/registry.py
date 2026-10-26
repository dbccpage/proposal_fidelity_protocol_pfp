"""Source-bound stage index and quarantined extension opcode registry."""

from __future__ import annotations

from dataclasses import dataclass

# These primary constructors are transcribed from research/mssn_sn_tower/grammar/readme.md.
# Level 4 adds a derived graph construction, not a fresh global opcode.
SOURCE_PRIMARY = (
    None,
    0,
    3,
    5,
    None,
    7,
    11,
    13,
    16,
    20,
    21,
    22,
    23,
    37,
    38,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
)
SOURCE_EXTRA = {1, 2, 4, 6, 9, 10, 12, 14, 15, 17, 18, 19, 24, 25, 26, 27, 28, 30, 31}
SOURCE_OPCODE_SET = set(SOURCE_PRIMARY) - {None} | SOURCE_EXTRA
PROPOSAL_START = 128
PROPOSAL_FIRST_STAGE = 22
PROPOSAL_BLOCK_SIZE = 8


@dataclass(frozen=True)
class Stage:
    level: int
    title: str
    capability_a: str
    capability_b: str
    obligation: str
    counterexample: str

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return (
            self.level,
            self.title,
            self.capability_a,
            self.capability_b,
            self.obligation,
            self.counterexample,
        ) == (
            other.level,
            other.title,
            other.capability_a,
            other.capability_b,
            other.obligation,
            other.counterexample,
        )

    @property
    def status(self) -> str:
        """Evidence grade computed by ``stage_status``; never a band on the level."""
        from .stage_status import stage_status
        return stage_status(self.level).grade

    @property
    def primary_opcode(self) -> int | None:
        if self.level < len(SOURCE_PRIMARY):
            return SOURCE_PRIMARY[self.level]
        return PROPOSAL_START + PROPOSAL_BLOCK_SIZE * (self.level - PROPOSAL_FIRST_STAGE)

    @property
    def reserved_opcodes(self) -> tuple[int, ...]:
        if self.level < PROPOSAL_FIRST_STAGE or self.primary_opcode is None:
            return ()
        return tuple(range(self.primary_opcode, self.primary_opcode + PROPOSAL_BLOCK_SIZE))

    @property
    def generator_ids(self) -> tuple[str, ...]:
        if self.level == 0:
            return ()
        if self.level == 1:
            return ("0", "1")
        # Fresh typed *child identifiers*, not host opcodes. Binary names
        # coexist with the fixed wire alphabet at arbitrary stages.
        return (
            format(1_000_000 + 2 * self.level, "b"),
            format(1_000_001 + 2 * self.level, "b"),
        )


STAGES = tuple(
    Stage(*row)
    for row in (
        (
            0,
            "Primitive difference",
            "primitive_mark",
            "nonresolution",
            "Accept precisely the two bytes <> at this stage",
            "Any interior glyph or nested packet is rejected",
        ),
        (
            1,
            "Binary up-lift",
            "generator_zero",
            "generator_one",
            "Reparse the source <> and preserve it under the first lift",
            "A lift omitting the source is rejected",
        ),
        (
            2,
            "Directed and obstructed graphs",
            "directed_edge",
            "obstruction_attachment",
            "Resolve each directed endpoint and preserve the obstruction carrier",
            "An edge to an absent vertex is rejected",
        ),
        (
            3,
            "Abstract simplices",
            "dimension_index",
            "vertex_closure",
            "Check n+1 distinct vertices and all implied subfaces",
            "A two-simplex with two vertices is rejected",
        ),
        (
            4,
            "Simplex graph expansions",
            "one_skeleton",
            "transitive_orientation",
            "Match graph edges to simplex 1-faces with declared orientation",
            "A missing edge of a triangle is rejected",
        ),
        (
            5,
            "Regge metric simplices",
            "squared_length",
            "deficit_receipt",
            "Check complete lengths and positive definite Gram matrix; verify incidence before curvature",
            "An indefinite Gram matrix with positive full determinant is rejected",
        ),
        (
            6,
            "General tower and higher cells",
            "stage_embedding",
            "higher_cell",
            "Check old presentations embed conservatively and boundary endpoints match",
            "A new relation collapsing old generators is rejected",
        ),
        (
            7,
            "Transfer operators and periodic orbits",
            "shift_spec",
            "primitive_orbit",
            "Check orbit closure, minimal period and cyclic representative",
            "00 cannot be a primitive period-two orbit",
        ),
        (
            8,
            "Adjunction and l1 cochains",
            "adjunction_unit",
            "dual_lp_witness",
            "Replay triangle identities and rational primal-dual feasibility",
            "A zero-gap string without dual feasibility is rejected",
        ),
        (
            9,
            "Dagger and profunctor reversal",
            "dagger_action",
            "reversal_witness",
            "Check involution and variance on typed arrows",
            "Reversing only endpoints while dropping obstruction is rejected",
        ),
        (
            10,
            "Quarantined spectral shadows",
            "shadow_packet",
            "scope_fence",
            "Prevent a discrete spectral claim becoming a continuum assertion",
            "An Ihara pole treated as a Riemann zero is rejected",
        ),
        (
            11,
            "Positioned polygraph rewrites",
            "redex_position",
            "peak_join",
            "Replay each substitution and both arms of a join",
            "An empty join of distinct nonnormal terms is rejected",
        ),
        (
            12,
            "Observer and DDA event",
            "kleene_value",
            "event_ledger",
            "Recompute bounded transition with parent digest and typed uncertainty",
            "A model-written Pass without host proof is rejected",
        ),
        (
            13,
            "Alternation and BQNF routing",
            "cycle_record",
            "route_token",
            "Check repeated state with unchanged progress and replay chosen route",
            "A syntactic route code alone cannot certify exact repair",
        ),
        (
            14,
            "Bounded quantifier blocks",
            "bound_ast",
            "polarity_mask",
            "Enumerate finite domains and recompute mask from formula tree",
            "An unbounded quantifier with a finite step budget is rejected",
        ),
        (
            15,
            "RBG master horizon",
            "candidate_proposal",
            "host_receipt",
            "Bind verifier digest and scope before accepting any terminal authority",
            "A candidate-authored Green verdict is rejected",
        ),
        (
            16,
            "Filtered ind-objects",
            "stage_transition",
            "coherence_check",
            "Check composition on generators and all source relations",
            "An injective generator map that collapses a source equation is rejected",
        ),
        (
            17,
            "Per-lift dialect containers",
            "dialect_tag",
            "digest_proof",
            "Decode with local tag dispatch and hash exact canonical bytes",
            "A changed body with unchanged digest is rejected",
        ),
        (
            18,
            "Discrete l2 Hodge",
            "harmonic_component",
            "coexact_component",
            "Reconstruct c and check exact harmonic coexact orthogonality",
            "A zero residual field without matrices is rejected",
        ),
        (
            19,
            "Discrete zeta shadows",
            "transfer_polynomial",
            "zeta_fence",
            "Compute exact polynomial from finite matrix and retain scope",
            "An irrational pole rounded to a rational is rejected",
        ),
        (
            20,
            "Expansion cycle receipts",
            "repeated_state",
            "progress_measure",
            "Compare full canonical states and detect nondecreasing repeated cycles",
            "A decreasing recursive call is not declared an expansion cycle",
        ),
        (
            21,
            "Four dimensional Regge",
            "triangle_hinge",
            "rotation_holonomy",
            "Check 4-simplex Gram positivity and ordered hinge holonomies",
            "A scalar sum of deficits cannot stand in for Bianchi closure",
        ),
        (
            22,
            "Fibred dependent contexts",
            "context_projection",
            "dependent_fiber",
            "Check reindexing identity and fiber typing for every declared base arrow",
            "A term reindexed into the wrong fiber is rejected",
        ),
        (
            23,
            "Sheaf and descent",
            "cover_family",
            "gluing_witness",
            "Check compatible overlap restrictions and unique gluing for declared cover",
            "Locally agreeing names with conflicting overlaps are rejected",
        ),
        (
            24,
            "Topos and subobject",
            "subobject_mono",
            "truth_classifier",
            "Check mono factorization and a commuting classifier pullback",
            "An arbitrary boolean label without characteristic pullback is rejected",
        ),
        (
            25,
            "Model localization",
            "weak_equivalence",
            "localized_roof",
            "Check weak-equivalence class and well-typed roofs in a declared model",
            "An untyped inverted arrow is rejected",
        ),
        (
            26,
            "Operad and multiarity",
            "operation_arity",
            "substitution_map",
            "Check matching input colors and operadic unit and associativity",
            "Substituting a binary output into a mismatched color is rejected",
        ),
        (
            27,
            "Higher coherence",
            "associator_cell",
            "pentagon_witness",
            "Check both composite boundaries of the pentagon are equal",
            "Two different 3-cell composites cannot be declared coherent",
        ),
        (
            28,
            "Homotopy type equivalence",
            "equivalence_witness",
            "identity_transport",
            "Check both inverse homotopies before any univalence use",
            "One-sided inverse asserted as equivalence is rejected",
        ),
        (
            29,
            "Derived obstruction",
            "resolution_complex",
            "derived_limit",
            "Check chain degrees and boundaries square to zero",
            "A nonzero composite of consecutive differentials is rejected",
        ),
        (
            30,
            "Spectral sequence pages",
            "filtration",
            "page_differential",
            "Check page bidegrees and d_r composed with itself is zero",
            "A class killed on a prior page cannot reappear without transport",
        ),
        (
            31,
            "Cohomology operations",
            "operation_degree",
            "naturality_square",
            "Check cocycle independence and map naturality in declared coefficients",
            "An operation depending on a coboundary representative is rejected",
        ),
        (
            32,
            "Coarse graining",
            "block_map",
            "loss_ledger",
            "Check explicit scale map and record lost distinctions",
            "Coarse map silently erasing a protected defect is rejected",
        ),
        (
            33,
            "Renormalization flow",
            "scale_parameter",
            "flow_receipt",
            "Check composition across scale steps and declared approximation error",
            "A scale jump without a loss bound is rejected",
        ),
        (
            34,
            "Statistical manifolds",
            "parametric_family",
            "fisher_matrix",
            "Check normalized likelihood and positive semidefinite Fisher matrix",
            "A negative variance direction is rejected",
        ),
        (
            35,
            "Finite Markov kernels",
            "stochastic_kernel",
            "transition_measure",
            "Check every rational row sums to one and entries are nonnegative",
            "A transition row summing to three halves is rejected",
        ),
        (
            36,
            "Bayesian updates",
            "likelihood",
            "posterior",
            "Check positive evidence and exact normalized posterior",
            "Conditioning on a zero-mass event is refused",
        ),
        (
            37,
            "Causal intervention",
            "structural_equation",
            "do_operator",
            "Check graph acyclicity and replace structural assignment for intervention",
            "An observational correlation is not labeled a causal effect",
        ),
        (
            38,
            "Counterfactuals",
            "exogenous_context",
            "twin_model",
            "Check both worlds reuse the same exogenous assignment",
            "A counterfactual changing the latent draw is rejected",
        ),
        (
            39,
            "Game strategies",
            "strategy_map",
            "payoff_rule",
            "Check strategy domains and evaluate payoffs on all joint actions",
            "An undefined action profile cannot count as equilibrium",
        ),
        (
            40,
            "Equilibrium evidence",
            "best_response",
            "deviation_witness",
            "Check every unilateral deviation against declared rational payoff",
            "A profitable deviation refutes an equilibrium claim",
        ),
        (
            41,
            "Linear resources",
            "resource_token",
            "tensor_compose",
            "Check use counts and typed tensor introduction",
            "A protected resource duplicated without contraction is rejected",
        ),
        (
            42,
            "Session protocols",
            "send_state",
            "receive_state",
            "Check dual endpoints and progress of finite session automata",
            "Two endpoints both waiting to receive are rejected",
        ),
        (
            43,
            "Effect and capability",
            "effect_row",
            "capability_grant",
            "Check scope and effect inclusion at each execution edge",
            "An effect outside granted capability is refused",
        ),
        (
            44,
            "Refinement contracts",
            "predicate_refinement",
            "prepost_contract",
            "Check precondition and postcondition with declared decidable theory",
            "A satisfiable looking assertion without solver witness remains pending",
        ),
        (
            45,
            "Proof kernel boundary",
            "proof_term",
            "trusted_checker",
            "Recheck all steps against hashed axioms and inference rules",
            "A self-reported proof check is not host certification",
        ),
        (
            46,
            "Self host and termination",
            "self_description",
            "termination_measure",
            "Require an external checker and decrease on recursive calls",
            "A self-certified unbounded evaluation is refused",
        ),
        (
            47,
            "Exact complex scalars",
            "rational_pair",
            "conjugation",
            "Check addition multiplication and conjugation of rational pairs",
            "A complex phase encoded as untyped decimal is rejected",
        ),
        (
            48,
            "Finite Hilbert states",
            "state_vector",
            "inner_product",
            "Check declared basis and exact unit norm",
            "A nonunit vector cannot claim normalized state",
        ),
        (
            49,
            "Spin one half states",
            "spin_basis",
            "spin_amplitude",
            "Check two-component norm in declared field and basis",
            "An unnamed measurement basis is rejected",
        ),
        (
            50,
            "Pauli observables",
            "pauli_matrix",
            "eigenprojector",
            "Check Hermitian square equals identity and projector identities",
            "A matrix with nonreal eigenvalues cannot be Pauli observable",
        ),
        (
            51,
            "Born instruments",
            "projector_family",
            "outcome_weight",
            "Check projector completeness and exact Born weights",
            "A reported probability not matching the projector norm is rejected",
        ),
        (
            52,
            "Sequential instruments",
            "measurement_order",
            "post_state",
            "Check conditional normalization and order-dependent probabilities",
            "Independent marginal probabilities substituted for conditionals are rejected",
        ),
        (
            53,
            "Tensor product states",
            "factor_basis",
            "product_state",
            "Check product dimension and basis ordering",
            "A permuted factor basis without transport is rejected",
        ),
        (
            54,
            "Entanglement witness",
            "schmidt_rank",
            "separability_test",
            "Check rank of reshaped pure-state amplitude matrix",
            "A product vector cannot claim rank two",
        ),
        (
            55,
            "No signaling marginals",
            "local_measurement",
            "remote_marginal",
            "Recompute local marginal across remote choices",
            "Different local marginals without postselection flag are rejected",
        ),
        (
            56,
            "Environment tracing",
            "joint_state",
            "partial_trace",
            "Check traced density is positive semidefinite with trace one",
            "A trace-changing reduction is rejected",
        ),
        (
            57,
            "Discrete unitary dynamics",
            "hamiltonian_spec",
            "unitary_step",
            "Check conjugate transpose times step equals identity",
            "A norm-changing step cannot claim unitary evolution",
        ),
        (
            58,
            "Contextuality scenarios",
            "measurement_context",
            "compatibility_graph",
            "Check consistent shared outcome labels on overlapping contexts",
            "A context assignment inconsistent on overlap is rejected",
        ),
        (
            59,
            "Bell correlation tests",
            "setting_pair",
            "correlator",
            "Recompute rational correlations and declared inequality bound",
            "A bound violation is not inferred from a receipt label alone",
        ),
        (
            60,
            "Quantum error correction",
            "stabilizer_generators",
            "syndrome_map",
            "Check commuting generators and unique declared syndrome behavior",
            "Anticommuting stabilizers are rejected",
        ),
        (
            61,
            "Gauge connections",
            "group_action",
            "parallel_transport",
            "Check path composition and endpoint covariance",
            "Changing gauge at source but not target is rejected",
        ),
        (
            62,
            "Discrete lattice gauge",
            "link_variable",
            "plaquette_holonomy",
            "Multiply ordered links around a closed face",
            "An open walk is rejected as a plaquette",
        ),
        (
            63,
            "Discrete gravity",
            "simplicial_metric",
            "metric_action",
            "Check simplex geometry and discrete action from incidence",
            "A curvature term without hinge incidence is rejected",
        ),
        (
            64,
            "Discrete Bianchi tests",
            "loop_family",
            "holonomy_closure",
            "Check ordered group products on a declared 3-cell boundary",
            "Scalar deficit cancellation is insufficient",
        ),
        (
            65,
            "Quantum gravity interface",
            "representation_map",
            "compatibility_square",
            "Check commuting typed maps on common finite carrier",
            "Calling both theories equivalent without map is rejected",
        ),
        (
            66,
            "Signed sum models",
            "signed_weight",
            "cancellation_pair",
            "Check exact signed totals and residual support",
            "A claimed zero with unpaired signed terms is rejected",
        ),
        (
            67,
            "Sign problem lower bounds",
            "problem_family",
            "complexity_reduction",
            "Require a formal reduction before a hardness claim",
            "Surrogate database keys alone do not prove NP hardness",
        ),
        (
            68,
            "Interval arithmetic",
            "interval_value",
            "enclosure_rule",
            "Check outward enclosure on every rational operation",
            "An approximation without a certified bound is rejected",
        ),
        (
            69,
            "Algebraic real numbers",
            "minimal_polynomial",
            "isolating_interval",
            "Check unique root in rational interval and polynomial evaluation",
            "An interval containing two roots is rejected",
        ),
        (
            70,
            "Finite transfer spectra",
            "transfer_matrix",
            "characteristic_poly",
            "Compute exact determinant polynomial",
            "An asserted eigenvalue with no matrix witness is rejected",
        ),
        (
            71,
            "Analytic limit fences",
            "sequence_family",
            "limit_certificate",
            "Check quantified convergence and retained hypotheses",
            "A finite orbit count cannot imply analytic continuation",
        ),
        (
            72,
            "Finite element cochains",
            "mesh_complex",
            "discrete_operator",
            "Check incidence nilpotency and boundary conditions",
            "An invalid mesh boundary is rejected",
        ),
        (
            73,
            "Continuum approximation",
            "mesh_refinement",
            "error_bound",
            "Check uniform refinement estimates against target functional",
            "Convergence inferred from a single mesh is rejected",
        ),
        (
            74,
            "Relational query mapping",
            "relation_schema",
            "query_plan",
            "Check typed columns and exact finite query semantics",
            "An absent column is refused during translation",
        ),
        (
            75,
            "Incremental views",
            "delta_relation",
            "view_patch",
            "Check patched view equals recomputed view on fixture",
            "A nonempty deletion omitted from delta is rejected",
        ),
        (
            76,
            "Topological database cells",
            "cell_schema",
            "boundary_index",
            "Check boundary squared is zero and relation references exist",
            "A dangling edge violates the cell schema",
        ),
        (
            77,
            "Transactional receipts",
            "write_set",
            "commit_receipt",
            "Check serializable conflict graph and parent digest",
            "A conflicting uncommitted write is refused",
        ),
        (
            78,
            "Distributed event logs",
            "event_clock",
            "causal_parent",
            "Check parent references and causal monotonicity",
            "An event referencing a future parent is rejected",
        ),
        (
            79,
            "Convergent replicated data",
            "merge_operation",
            "join_law",
            "Check commutativity associativity and idempotence on bounded domain",
            "A nonidempotent merge is rejected",
        ),
        (
            80,
            "Scoped authorization",
            "principal_scope",
            "grant_receipt",
            "Check exact resource and action against independent authorization",
            "A model-authored privilege escalation is refused",
        ),
        (
            81,
            "Privacy boundaries",
            "release_query",
            "privacy_ledger",
            "Check composition against declared finite privacy budget",
            "A release exceeding remaining budget is refused",
        ),
        (
            82,
            "Security provenance",
            "signed_manifest",
            "origin_binding",
            "Check digest and trusted signature chain before action",
            "An unsigned checksum is not an authenticated source",
        ),
        (
            83,
            "Data lineage",
            "source_digest",
            "derivation_edge",
            "Check every derived value points to immutable inputs",
            "A missing source breaks provenance",
        ),
        (
            84,
            "LLM tool calls",
            "tool_schema",
            "call_receipt",
            "Validate arguments and compare actual tool result digest",
            "A guessed tool result is rejected",
        ),
        (
            85,
            "Agent task routing",
            "task_scope",
            "handoff_receipt",
            "Check delegated scope is a subset of principal scope",
            "An agent expands its own authorization is refused",
        ),
        (
            86,
            "Multi agent traces",
            "agent_event",
            "dependency_dag",
            "Check event parents are acyclic and evidence links resolve",
            "A circular dependency without base witness is rejected",
        ),
        (
            87,
            "Audit challenge",
            "negative_fixture",
            "challenge_result",
            "Check challenger mutation changes expected verdict",
            "A negative fixture that still passes is flagged",
        ),
        (
            88,
            "Sandbox boundaries",
            "execution_policy",
            "resource_budget",
            "Check declared limits and captured exit state",
            "A timeout claimed as a completed proof is rejected",
        ),
        (
            89,
            "Error accounting",
            "error_source",
            "composed_bound",
            "Check algebraic sum or justified dependence of error bounds",
            "Two correlated errors assumed independent are rejected",
        ),
        (
            90,
            "Natural language fidelity",
            "source_span",
            "formalization_link",
            "Record source coverage and scope exceptions for human audit",
            "A missing quantified clause remains an open residual",
        ),
        (
            91,
            "Typed translation",
            "source_ast",
            "target_ast",
            "Check semantics on the declared decidable fragment",
            "Changing quantifier order without proof is rejected",
        ),
        (
            92,
            "Proof extraction",
            "solver_trace",
            "kernel_proof",
            "Replay proof object in independent kernel",
            "A solver success flag with no proof is rejected",
        ),
        (
            93,
            "Compiler preservation",
            "intermediate_ast",
            "simulation_step",
            "Check source target simulation on bounded fragment",
            "A compiled branch changing outcome is rejected",
        ),
        (
            94,
            "Protocol composition",
            "interface_port",
            "composition_witness",
            "Check both directions of handshake types",
            "Connecting two output ports is rejected",
        ),
        (
            95,
            "Performance receipts",
            "resource_counter",
            "measurement_manifest",
            "Check measured counters match run logs and environment",
            "A model estimated speedup is not a benchmark",
        ),
        (
            96,
            "Benchmark trials",
            "trial_manifest",
            "statistical_interval",
            "Check immutable corpus and recompute interval from counts",
            "A point estimate with no trial count is rejected",
        ),
        (
            97,
            "Mutation suites",
            "mutation_operator",
            "kill_matrix",
            "Check changed fixtures fail for the intended invariant",
            "A surviving dangerous mutation is flagged",
        ),
        (
            98,
            "Differential checking",
            "checker_pair",
            "disagreement_receipt",
            "Run independent implementations on same canonical input",
            "Different outputs cannot be silently merged",
        ),
        (
            99,
            "Property tests",
            "generator_seed",
            "shrunk_counterexample",
            "Replay seed and shrink without changing failure predicate",
            "A reported failure without replay seed is quarantined",
        ),
        (
            100,
            "Open horizon and release",
            "release_manifest",
            "open_obligation",
            "Check all claimed scope has tests or explicitly typed unresolved obligations",
            "A release that declares final self certification is refused",
        ),
    )
)


def check_registry() -> None:
    used = set(SOURCE_OPCODE_SET)
    generator_ids = set()
    for stage in STAGES:
        if stage.level and (len(stage.generator_ids) != 2 or len(set(stage.generator_ids)) != 2):
            raise ValueError("each proposed lift must bind two distinct generator IDs")
        for identifier in stage.generator_ids:
            if identifier in generator_ids:
                raise ValueError("generator ID repeated")
            generator_ids.add(identifier)
        if stage.level >= PROPOSAL_FIRST_STAGE:
            if used.intersection(stage.reserved_opcodes):
                raise ValueError("proposal opcode collision")
            used.update(stage.reserved_opcodes)


def load_stages() -> list[Stage]:
    """Return copy of the stage catalogue."""
    return list(STAGES)

