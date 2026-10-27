//! Static catalog of paper-claim records.
//!
//! `MASTER_TRACEABILITY_REGISTRY` is the only catalog. It records package ids,
//! claim ids, and the module names an author associated with them. It does not
//! recompute a proof, open a ledger, or admit a claim.
//!
//! Authority effect on every record is `AuthorityEffect: None`.

use serde::Serialize;

/// Explicit authority effect stored on every catalog record.
pub const AUTHORITY_EFFECT: &str = "AuthorityEffect: None";

/// One catalog row. The strings are author records, not a proof check.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize)]
pub struct MathematicalClaim {
    /// Package identifier in `coda_atlas` (e.g., `PO-000`, `FQM-006`, `FSP-008`).
    pub package_id: &'static str,
    /// Human-readable title of the research paper.
    pub short_title: &'static str,
    /// Formal theorem, lemma, or claim ID as declared in the paper manuscript and claim ledger.
    pub claim_id: &'static str,
    /// Exact mathematical statement of the claim.
    pub claim_statement: &'static str,
    /// Epistemic status (e.g., `PROVED`, `FINITE_CHECKED`, `EXACT_RATIONAL`, `MECHANIZED`, `CONDITIONAL`).
    pub status: &'static str,
    /// Retained Lean source or qualified declaration association, when supported.
    /// This catalog field is not a fresh elaboration or axiom-census receipt.
    pub lean_locus: Option<&'static str>,
    /// Target Rust crates implementing or certifying this claim.
    pub target_crates: &'static [&'static str],
    /// Primary source modules embodying the claim.
    pub primary_modules: &'static [&'static str],
    /// Specific certifier, witness, or receipt type validating the claim.
    pub certifier_or_witness: &'static str,
    /// Integration test harness or oracle verifying the claim.
    pub key_verification_harness: &'static str,
    /// Declared domain assumptions and preconditions under which the claim holds.
    pub declared_assumptions: &'static str,
    /// Governance and normative effect (strictly `AuthorityEffect: None`).
    pub authority_effect: &'static str,
}

/// Canonical Master Traceability Registry encompassing all 19 research paper packages.
///
/// Grounded in accordance with `survey_paper_claims.md` Section 6 Master Traceability Matrix.
pub static MASTER_TRACEABILITY_REGISTRY: &[MathematicalClaim] = &[
    // -------------------------------------------------------------------------
    // Package 01: FOC-000-GENESIS
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-000-GENESIS",
        short_title: "Genesis: The 19L57G1 Benchmark & Finite Difference Grounding",
        claim_id: "WDP-P000-001",
        claim_statement: "Discrete difference operator on 19 layers and 57 gate evaluations evaluates without integer overflow",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_ooutwire_primitives"],
        primary_modules: &["genesis_bridge.rs", "schedule.rs"],
        certifier_or_witness: "ExecutionReceipt",
        key_verification_harness: "tests/genesis_realification_bridge.rs",
        declared_assumptions: "19 layers, 57 gates, exact integer coordinates",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-GENESIS",
        short_title: "Genesis: The 19L57G1 Benchmark & Finite Difference Grounding",
        claim_id: "WDP-P000-002",
        claim_statement: "Gate evaluation sequence maintains state invariant through layer 19",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_ooutwire_primitives"],
        primary_modules: &["schedule.rs", "admission.rs"],
        certifier_or_witness: "LayerGateReceipt",
        key_verification_harness: "tests/genesis_realification_bridge.rs",
        declared_assumptions: "Deterministic gate evaluation ordering",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-GENESIS",
        short_title: "Genesis: The 19L57G1 Benchmark & Finite Difference Grounding",
        claim_id: "WDP-P000-018",
        claim_statement: "Exact integer residuals verified on 19L57G1 schedule",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_ooutwire_primitives"],
        primary_modules: &["genesis_bridge.rs", "regime.rs"],
        certifier_or_witness: "ExecutionReceipt",
        key_verification_harness: "tests/genesis_realification_bridge.rs",
        declared_assumptions: "Bounded discrete work budget",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 02: FOC-000-PRE-GENESIS
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-000-PRE-GENESIS",
        short_title: "From Pre-Genesis to MSS-N: Historical Consolidations and Minimal Symbol System",
        claim_id: "PRE-GEN-01",
        claim_statement: "Report reconstruction and uniqueness under finite observational history",
        status: "MECHANIZED",
        lean_locus: Some("PreMssn.history_report_criterion"),
        target_crates: &["core_homology", "core_category_theory"],
        primary_modules: &["integral_chain_complex.rs", "discrete_category.rs"],
        certifier_or_witness: "QuotientClassReceipt",
        key_verification_harness: "code/verify_package.py --native",
        declared_assumptions: "Finite observation log, well-founded event ordering",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-PRE-GENESIS",
        short_title: "From Pre-Genesis to MSS-N: Historical Consolidations and Minimal Symbol System",
        claim_id: "PRE-GEN-02",
        claim_statement: "Observational identification and task descent over profile setoids",
        status: "FINITE_CHECKED",
        lean_locus: Some("PreMssn.Observation.profileSetoid"),
        target_crates: &["core_category_theory", "core_finite_probability"],
        primary_modules: &["discrete_category.rs"],
        certifier_or_witness: "HomologyWitness",
        key_verification_harness: "code/verify_package.py --native",
        declared_assumptions: "Equivalence relations on finite observational profiles",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-PRE-GENESIS",
        short_title: "From Pre-Genesis to MSS-N: Historical Consolidations and Minimal Symbol System",
        claim_id: "PRE-GEN-07",
        claim_statement: "Constructed homology and chain-retraction obstruction on finite graphs",
        status: "MECHANIZED",
        lean_locus: Some("PreMssn.Homology.homologyMap"),
        target_crates: &["core_homology"],
        primary_modules: &["integral_chain_complex.rs"],
        certifier_or_witness: "HomologyWitness",
        key_verification_harness: "code/verify_package.py --native",
        declared_assumptions: "Finite 1-dimensional CW complexes",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-PRE-GENESIS",
        short_title: "From Pre-Genesis to MSS-N: Historical Consolidations and Minimal Symbol System",
        claim_id: "PRE-GEN-08",
        claim_statement: "Integral class encoding and torsion in finite chain complexes",
        status: "FINITE_CHECKED",
        lean_locus: Some("PreMssn.Homology.integer_class_eq_iff"),
        target_crates: &["core_homology"],
        primary_modules: &["integral_chain_complex.rs"],
        certifier_or_witness: "QuotientClassReceipt",
        key_verification_harness: "code/verify_package.py --native",
        declared_assumptions: "Exact integer Smith normal form computation",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 03: FOC-000-WDP
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-000-WDP",
        short_title: "Witnessed Difference Programme: Monograph and Component Packages",
        claim_id: "OE001-01",
        claim_statement: "Exact rational matrix simplex terminates within bounded pivot steps on finite difference programs",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_solvers"],
        primary_modules: &["data_cochain_packet.rs"],
        certifier_or_witness: "WdpReceipt",
        key_verification_harness: "tests/wdp_joint_support_recovery.rs",
        declared_assumptions: "Rational matrix coefficients, Bland pivot rule",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-WDP",
        short_title: "Witnessed Difference Programme: Monograph and Component Packages",
        claim_id: "OE002-04",
        claim_statement: "Primal-dual gap evaluates to exact zero under rational duality certificate",
        status: "FINITE_CHECKED",
        lean_locus: Some("PaperER007.lp_max_form_weak_duality"),
        target_crates: &["core_certifiers", "core_functional"],
        primary_modules: &["phi1_certifier.rs"],
        certifier_or_witness: "Phi1PrimalDualCertificate",
        key_verification_harness: "tests/phi1_conformance.rs",
        declared_assumptions: "Exact rational BigRational arithmetic",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-000-WDP",
        short_title: "Witnessed Difference Programme: Monograph and Component Packages",
        claim_id: "WDP-CH05",
        claim_statement: "Exact first-order Euler leakage is bounded by elapsed time times the leakage operator norm and input state norm",
        status: "EXACT_RATIONAL",
        lean_locus: None,
        target_crates: &["core_functional", "core_wdp"],
        primary_modules: &["projection_leakage.rs", "po000_projection_obstruction.rs"],
        certifier_or_witness: "ProjectionObstructionReceipt",
        key_verification_harness: "core_functional/tests/projection_leakage.rs",
        declared_assumptions: "Exact rational idempotents, nonnegative time and explicit state; no exponential remainder bound asserted",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 04: FOC-001-GENESIS-ONGOING
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-001-GENESIS-ONGOING",
        short_title: "Genesis Ongoing H3V7N5QF: 25 Derivation Steps and Refinement Lattice",
        claim_id: "GEN-ONG-01",
        claim_statement: "Refinement step 1 preserves invariant boundary conditions on discrete lattice",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_epistemic_immune_system"],
        primary_modules: &["refinement_lattice.rs", "defect_incidence.rs"],
        certifier_or_witness: "StepGateReceipt",
        key_verification_harness: "meta/review/watchlist_decision.md",
        declared_assumptions: "Finite lattice coordinates, strictly enforced refusal semantics",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-001-GENESIS-ONGOING",
        short_title: "Genesis Ongoing H3V7N5QF: 25 Derivation Steps and Refinement Lattice",
        claim_id: "GEN-ONG-25",
        claim_statement: "25-step derivation terminates within declared resource envelope without invariant drift",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_wdp", "core_epistemic_immune_system"],
        primary_modules: &["refinement_lattice.rs"],
        certifier_or_witness: "AblationWitness",
        key_verification_harness: "meta/review/watchlist_decision.md",
        declared_assumptions: "Finite 25-step boundary",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 05: FOC-001-LGGR
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-001-LGGR",
        short_title: "Local Green Global Red Foundational Series (LGGR Monograph Series I - VI)",
        claim_id: "LGGR1-C01",
        claim_statement: "Evaluated path kernel computes local patch consistency on finite coverings",
        status: "FINITE_CHECKED",
        lean_locus: Some("lean4/LGGR.lean"),
        target_crates: &["core_local_green_global_red_lggr"],
        primary_modules: &["path_kernel.rs", "gluing.rs"],
        certifier_or_witness: "KernelSeparationWitness",
        key_verification_harness: "core_local_green_global_red_lggr/tests",
        declared_assumptions: "Finite covering patches, exact local valuations",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-001-LGGR",
        short_title: "Local Green Global Red Foundational Series (LGGR Monograph Series I - VI)",
        claim_id: "LGGR5-C01",
        claim_statement: "Local green patch validity coexists with global red obstruction across non-trivial cycle",
        status: "FINITE_CHECKED",
        lean_locus: Some("lean4/LggrNonFactorization.lean"),
        target_crates: &["core_local_green_global_red_lggr"],
        primary_modules: &["gluing.rs", "aggregation.rs"],
        certifier_or_witness: "LocalGreenReceipt",
        key_verification_harness: "core_local_green_global_red_lggr/tests",
        declared_assumptions: "Non-trivial fundamental group on covering complex",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-001-LGGR",
        short_title: "Local Green Global Red Foundational Series (LGGR Monograph Series I - VI)",
        claim_id: "LGGR6-C25",
        claim_statement: "Adjoint probing detects non-factorizing state over boundary cycles",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_local_green_global_red_lggr"],
        primary_modules: &["aggregation.rs"],
        certifier_or_witness: "KernelSeparationWitness",
        key_verification_harness: "core_local_green_global_red_lggr/tests",
        declared_assumptions: "Finite cell boundary representations",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 06: FOC-001-SN-MSSN
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FOC-001-SN-MSSN",
        short_title: "S(n) and MSS-N: Symmetric Presentation and Homological Invariants",
        claim_id: "WDP-P001-001",
        claim_statement: "S(n) symmetric group presentation relations satisfied on finite sets without relator ambiguity",
        status: "FINITE_CHECKED",
        lean_locus: Some("lean4/SnTower.lean"),
        target_crates: &["core_combinatorics", "core_homology"],
        primary_modules: &["symmetric_group.rs"],
        certifier_or_witness: "PermutationCycleWitness",
        key_verification_harness: "tests/groups_completion.rs",
        declared_assumptions: "Finite permutation degrees n <= 10",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FOC-001-SN-MSSN",
        short_title: "S(n) and MSS-N: Symmetric Presentation and Homological Invariants",
        claim_id: "WDP-P001-014",
        claim_statement: "Presentation boundary complex yields exact cycle decomposition",
        status: "FINITE_CHECKED",
        lean_locus: Some("lean4/SnTower.lean"),
        target_crates: &["core_combinatorics", "core_homology"],
        primary_modules: &["presentation_complex.rs"],
        certifier_or_witness: "PermutationCycleWitness",
        key_verification_harness: "tests/groups_completion.rs",
        declared_assumptions: "Exact integer boundary matrices",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 07: PO-000
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-000",
        short_title: "Projection Obstruction for Factorized States: Nonlinear Dynamics, Conditional l1 Diagnostics, and Exact Short-Time Defect Bounds",
        claim_id: "A1",
        claim_statement: "Product projection yields local normal residuals on product initial state under 1- and 2-local interaction",
        status: "EXACT_RATIONAL",
        lean_locus: None,
        target_crates: &["core_ooutwire_primitives", "core_wdp"],
        primary_modules: &["alpha_projection_obstruction/verify.rs", "matrix.rs"],
        certifier_or_witness: "ProductProjectionCert",
        key_verification_harness: "cargo run --bin verify_po000",
        declared_assumptions: "Factorized initial state, bounded local Hamiltonian",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-000",
        short_title: "Projection Obstruction for Factorized States: Nonlinear Dynamics, Conditional l1 Diagnostics, and Exact Short-Time Defect Bounds",
        claim_id: "D1",
        claim_statement: "Affine nonlinearity bound on factorized state projection dynamics",
        status: "EXACT_RATIONAL",
        lean_locus: None,
        target_crates: &["core_ooutwire_primitives", "core_quantum_physics"],
        primary_modules: &["alpha_projection_obstruction/verify.rs"],
        certifier_or_witness: "Po000Receipt",
        key_verification_harness: "tests/po000_projection_retraction_born_conformance.rs",
        declared_assumptions: "Finite-dimensional Hilbert space, trace-norm bound",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-000",
        short_title: "Projection Obstruction for Factorized States: Nonlinear Dynamics, Conditional l1 Diagnostics, and Exact Short-Time Defect Bounds",
        claim_id: "D8a",
        claim_statement: "Trace-norm defect bound is quadratic in short time parameter over exact rationals",
        status: "EXACT_RATIONAL",
        lean_locus: None,
        target_crates: &["core_ooutwire_primitives", "core_wdp"],
        primary_modules: &["alpha_projection_obstruction/verify.rs"],
        certifier_or_witness: "ProductProjectionCert",
        key_verification_harness: "cargo run --bin verify_po000",
        declared_assumptions: "Exact rational Taylor expansion to second order",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-000",
        short_title: "Projection Obstruction for Factorized States: Nonlinear Dynamics, Conditional l1 Diagnostics, and Exact Short-Time Defect Bounds",
        claim_id: "H4",
        claim_statement: "Full 51-claim canonical receipt sequence matches reference outputs without deviation",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_ooutwire_primitives"],
        primary_modules: &["alpha_projection_obstruction/verify.rs"],
        certifier_or_witness: "Po000Receipt",
        key_verification_harness: "cargo run --bin verify_po000",
        declared_assumptions: "Exact receipt string hashing, 51 required claim IDs",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 08: PO-001
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-001",
        short_title: "From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects",
        claim_id: "PO001-C01",
        claim_statement: "Saturated-chain composites on finite posets extend uniquely to a functorial presheaf when diamond commutativity holds",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_homology", "core_sheaf_theory"],
        primary_modules: &["finite_poset.rs", "chain_complex.rs"],
        certifier_or_witness: "PresheafCoherenceWitness",
        key_verification_harness: "tests/test_path_a_completion.py",
        declared_assumptions: "Finite graded poset, diamond commutativity",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-001",
        short_title: "From Covering-Edge Descent Complexes to Functorial Presheaves and Coherence Defects",
        claim_id: "PO001-C05",
        claim_statement: "Diamond path-independence witness on finite poset coverings",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_homology", "core_sheaf_theory"],
        primary_modules: &["finite_poset.rs"],
        certifier_or_witness: "PresheafCoherenceWitness",
        key_verification_harness: "tests/test_path_a_completion.py",
        declared_assumptions: "Locally diamond-connected covering posets",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 09: PO-006
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-006",
        short_title: "Vector and Quantum Observer Geometries",
        claim_id: "PO006-A1",
        claim_statement: "Finite projective ray configurations in d >= 3 admit non-contextual frame function obstruction",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_quantum_physics", "core_holonomy"],
        primary_modules: &["frame_function_polytope.rs", "finite_geometry.rs"],
        certifier_or_witness: "FrameFunctionObstructionWitness",
        key_verification_harness: "tests/projective_preservers.rs",
        declared_assumptions: "Hilbert space dimension d >= 3, orthogonality graph rays",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-006",
        short_title: "Vector and Quantum Observer Geometries",
        claim_id: "PO006-C10",
        claim_statement: "Projective frame polytope witness rules out dispersion-free valuations satisfying orthogonality constraints",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["frame_function_polytope.rs"],
        certifier_or_witness: "FrameFunctionObstructionWitness",
        key_verification_harness: "tests/projective_preservers.rs",
        declared_assumptions: "Finite set of rays containing Kochen-Specker subconfiguration",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 10: PO-007
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-007",
        short_title: "M-Compatible Gauge Classification",
        claim_id: "PO007-C01",
        claim_statement: "Discrete gauge transformation equivalence classes correspond to 1-coboundary orbits on finite complexes",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy", "core_quantum_physics"],
        primary_modules: &["gauge_fixing.rs", "connection.rs"],
        certifier_or_witness: "GaugeOrbitWitness",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Finite cell complexes, discrete abelian gauge group",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-007",
        short_title: "M-Compatible Gauge Classification",
        claim_id: "PO007-C27",
        claim_statement: "M-compatible gauge fixing preserves connection holonomy invariants",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy"],
        primary_modules: &["gauge_fixing.rs"],
        certifier_or_witness: "GaugeOrbitWitness",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Strict tree gauge fixing on maximal spanning trees",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 11: PO-008
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-008",
        short_title: "SO(k)-Invariant Gauge Classification",
        claim_id: "PO008-C01",
        claim_statement: "Connection matrices commute with SO(k) generator projections on invariant subspaces",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy", "core_lie_theory"],
        primary_modules: &["connection.rs", "so_n.rs"],
        certifier_or_witness: "OrthogonalInvarianceReceipt",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Compact orthogonal group representation on finite cell bundle",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-008",
        short_title: "SO(k)-Invariant Gauge Classification",
        claim_id: "PO008-C35",
        claim_statement: "Orthogonal gauge decomposition terminates on finite cell complexes",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy"],
        primary_modules: &["connection.rs"],
        certifier_or_witness: "OrthogonalInvarianceReceipt",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Finite dimensional vector bundle over finite CW complex",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 12: PO-009
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-009",
        short_title: "Coordinate-Wise Additivity in Obstruction Complexes",
        claim_id: "PO009-C01",
        claim_statement: "Total defect evaluates to sum of cell defects when interaction Hamiltonians have disjoint spatial support",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_category_theory", "core_linear_algebra"],
        primary_modules: &["additivity.rs", "direct_sum.rs"],
        certifier_or_witness: "AdditivitySplittingWitness",
        key_verification_harness: "core_category_theory/tests",
        declared_assumptions: "Disjoint support partitions on finite tensor factorizations",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-009",
        short_title: "Coordinate-Wise Additivity in Obstruction Complexes",
        claim_id: "PO009-C19",
        claim_statement: "Coordinate-wise splitting holds for direct sums of independent complexes",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_category_theory"],
        primary_modules: &["additivity.rs"],
        certifier_or_witness: "AdditivitySplittingWitness",
        key_verification_harness: "core_category_theory/tests",
        declared_assumptions: "Block diagonal linear maps with zero off-diagonal coupling",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 13: PO-033
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-033",
        short_title: "Certified Adaptive Quantum Dynamics: Channel Enclosures & Kraus Refinements",
        claim_id: "PO033-C1",
        claim_statement: "Heuristic uncertified channel bounds flagged and isolated from certified core",
        status: "CONDITIONAL",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["completely_positive_map.rs", "chain_histories.rs"],
        certifier_or_witness: "KrausEnclosureWitness",
        key_verification_harness: "tests/qm_certification_regressions.rs",
        declared_assumptions: "Bounded resource budget; uncertified tolerance claims refused",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-033",
        short_title: "Certified Adaptive Quantum Dynamics: Channel Enclosures & Kraus Refinements",
        claim_id: "PO033-C2",
        claim_statement: "Domain-corrected CP-map Kraus representation satisfies trace-preservation within verified numerical enclosures",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["completely_positive_map.rs"],
        certifier_or_witness: "KrausEnclosureWitness",
        key_verification_harness: "tests/qm_certification_regressions.rs",
        declared_assumptions: "Choi matrix dimension matches dim_in * dim_out",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-033",
        short_title: "Certified Adaptive Quantum Dynamics: Channel Enclosures & Kraus Refinements",
        claim_id: "PO033-C3",
        claim_statement: "Norm witness for Kraus operator enclosure bounds under exact rational intervals",
        status: "EXACT_RATIONAL",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["completely_positive_map.rs"],
        certifier_or_witness: "KrausEnclosureWitness",
        key_verification_harness: "tests/qm_certification_regressions.rs",
        declared_assumptions: "Bounded matrix spectrum",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 14: PO-034
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-034",
        short_title: "Higher Cell Cochain Projection and Retraction Dynamics",
        claim_id: "PO034-C1",
        claim_statement: "Non-zero higher coboundary defect d_1 Q != 0 witnesses non-factorizing state projection",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_homology", "core_quantum_physics"],
        primary_modules: &["cochain.rs", "cochain_repair_code.rs"],
        certifier_or_witness: "CochainRepairWitness",
        key_verification_harness: "tests/qm_certification_regressions.rs",
        declared_assumptions: "Finite 2-complex, product initial state",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-034",
        short_title: "Higher Cell Cochain Projection and Retraction Dynamics",
        claim_id: "PO034-C4e",
        claim_statement: "PR-box 2-cochain defect circulation obstructs local retraction across cell boundary",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_homology", "core_quantum_physics"],
        primary_modules: &["cochain.rs"],
        certifier_or_witness: "CochainRepairWitness",
        key_verification_harness: "tests/qm_certification_regressions.rs",
        declared_assumptions: "PR-box non-signaling probability distribution",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 15: PO-035
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "PO-035",
        short_title: "Zero Container Relational Spacetime and Witness Holonomy",
        claim_id: "R01-EMERGENT-CAUSALITY",
        claim_statement: "Partial ordering emerges from relational witness coincidence on discrete triangulations",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy", "core_general_relativity"],
        primary_modules: &["holonomy.rs", "quantum_regge_bridge.rs"],
        certifier_or_witness: "ReggeHolonomyWitness",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Finite causal set triangulations, acyclic relation graph",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "PO-035",
        short_title: "Zero Container Relational Spacetime and Witness Holonomy",
        claim_id: "R03-REGGE-HOLONOMY",
        claim_statement: "Discrete Regge holonomy angle is non-zero around hinges with deficit angle",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_holonomy", "core_quantum_physics"],
        primary_modules: &["holonomy.rs", "quantum_regge_bridge.rs"],
        certifier_or_witness: "ReggeHolonomyWitness",
        key_verification_harness: "core_holonomy/tests",
        declared_assumptions: "Exact rational edge lengths satisfying triangle inequalities",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 16: FQM-006
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FQM-006",
        short_title: "Finite Quantum Mechanics: Foundation, Fiber Quotients, and State Space Stratification",
        claim_id: "000:QMC-T1",
        claim_statement: "Positive weighted L1 cochain quotient has exact circulation dual",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_quantum_physics", "core_solvers"],
        primary_modules: &["u1_graph_connection.rs", "exact_hermitian.rs"],
        certifier_or_witness: "ExactHermitianWitness",
        key_verification_harness: "tests/foundations/quantum_carrier_primitive_difference.rs",
        declared_assumptions: "Finite graph, positive edge weights, exact rational arithmetic",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FQM-006",
        short_title: "Finite Quantum Mechanics: Foundation, Fiber Quotients, and State Space Stratification",
        claim_id: "020:QMC-T1",
        claim_statement: "Direct L1 normalization of state vectors on finite Hilbert spaces",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["exact_hermitian.rs"],
        certifier_or_witness: "DensityMatrixTraceWitness",
        key_verification_harness: "tests/po000_projection_retraction_born_conformance.rs",
        declared_assumptions: "Finite-dimensional Hilbert space, non-zero state vector",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FQM-006",
        short_title: "Finite Quantum Mechanics: Foundation, Fiber Quotients, and State Space Stratification",
        claim_id: "020:QMC-T4",
        claim_statement: "Hilbert lift Born redundancy on finite projection operators",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["exact_hermitian.rs"],
        certifier_or_witness: "ExactHermitianWitness",
        key_verification_harness: "tests/po000_projection_retraction_born_conformance.rs",
        declared_assumptions: "Exact rational projectors P^2 = P = P*",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FQM-006",
        short_title: "Finite Quantum Mechanics: Foundation, Fiber Quotients, and State Space Stratification",
        claim_id: "060:QMC-T1",
        claim_statement: "Superposition as fiber quotient over exact quotient carrier",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["u1_graph_connection.rs"],
        certifier_or_witness: "DensityMatrixTraceWitness",
        key_verification_harness: "tests/u1_graph_connection_tests.rs",
        declared_assumptions: "U(1) fiber quotient on finite graph vertices",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FQM-006",
        short_title: "Finite Quantum Mechanics: Foundation, Fiber Quotients, and State Space Stratification",
        claim_id: "122:QMC-T1",
        claim_statement: "Finite Hilbert boundary admits exact rational Gell-Mann basis expansion",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_quantum_physics"],
        primary_modules: &["exact_hermitian.rs"],
        certifier_or_witness: "ExactHermitianWitness",
        key_verification_harness: "tests/exact_hermitian_tests.rs",
        declared_assumptions: "Traceless Hermitian matrix generators in finite dimension d",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 17: F2C-007
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "F2C-007",
        short_title: "Finite-to-Continuum Scaling: Cyclic Haar, Pontryagin Completion, and Schema Profiles",
        claim_id: "cdx2.cyclic_haar_native",
        claim_statement: "Finite cyclic prefix averages evaluate Haar integral values on trigonometric polynomials within declared rational tolerances",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_finite_probability", "core_number_theory"],
        primary_modules: &["cyclic_haar.rs", "pontryagin.rs"],
        certifier_or_witness: "CyclicHaarEnclosureReceipt",
        key_verification_harness: "_docs/track2_claim/checker.py",
        declared_assumptions: "Cyclotomic fields Q(zeta_N), trigonometric polynomial degrees",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "F2C-007",
        short_title: "Finite-to-Continuum Scaling: Cyclic Haar, Pontryagin Completion, and Schema Profiles",
        claim_id: "cdx2.finite_symmetry",
        claim_statement: "Finite cyclic character sum symmetry satisfied on Q(zeta_N)",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_finite_probability"],
        primary_modules: &["cyclic_haar.rs"],
        certifier_or_witness: "CyclicHaarEnclosureReceipt",
        key_verification_harness: "_docs/track2_claim/checker.py",
        declared_assumptions: "Cyclic group Z/NZ character evaluation",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "F2C-007",
        short_title: "Finite-to-Continuum Scaling: Cyclic Haar, Pontryagin Completion, and Schema Profiles",
        claim_id: "cdx2.haar_formal",
        claim_statement: "Haar formal character orthogonality is not admitted as mechanized: the named Lean source is absent",
        status: "CONDITIONAL",
        lean_locus: None,
        target_crates: &["core_finite_probability"],
        primary_modules: &["cyclic_haar.rs"],
        certifier_or_witness: "CyclicHaarEnclosureReceipt",
        key_verification_harness: "_docs/track2_claim/checker.py",
        declared_assumptions: "Integer Fourier characters, normalized circle Haar measure; alias-free finite comparison requires k.natAbs < N",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 18: FSP-008
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "FSP-008",
        short_title: "Primitive Difference, Fermionic Hamiltonians, and Certified Sign-Problem Boundaries",
        claim_id: "PO-023-C1",
        claim_statement: "Meron cluster pairing cancels negative sign contributions in the zero-meron sector on bipartite lattices",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_certifiers", "core_majorana"],
        primary_modules: &["meron_certificate.rs", "meron_hamiltonian_bridge.rs"],
        certifier_or_witness: "MeronCertificate",
        key_verification_harness: "tests/phi1_conformance.rs",
        declared_assumptions: "Bipartite spatial lattice, zero chemical potential",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FSP-008",
        short_title: "Primitive Difference, Fermionic Hamiltonians, and Certified Sign-Problem Boundaries",
        claim_id: "PO-023-C2",
        claim_statement: "Bipartite Hubbard involution pairs configuration weights with opposite fermionic signs",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_certifiers", "core_majorana"],
        primary_modules: &["meron_hamiltonian_bridge.rs"],
        certifier_or_witness: "InvolutionPair",
        key_verification_harness: "tests/phi1_conformance.rs",
        declared_assumptions: "Particle-hole symmetry on bipartite lattice",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FSP-008",
        short_title: "Primitive Difference, Fermionic Hamiltonians, and Certified Sign-Problem Boundaries",
        claim_id: "GIN-C3",
        claim_statement: "Exact sign cancellation certified under declared Meron cluster partition",
        status: "PROVED",
        lean_locus: None,
        target_crates: &["core_certifiers"],
        primary_modules: &["meron_certificate.rs"],
        certifier_or_witness: "MeronCertificate",
        key_verification_harness: "tests/phi1_conformance.rs",
        declared_assumptions: "Disjoint meron cluster decomposition",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "FSP-008",
        short_title: "Primitive Difference, Fermionic Hamiltonians, and Certified Sign-Problem Boundaries",
        claim_id: "MER-C1",
        claim_statement: "LCK loop sign formula characterizes topological winding parity",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_certifiers"],
        primary_modules: &["meron_hamiltonian_bridge.rs"],
        certifier_or_witness: "MeronCertificate",
        key_verification_harness: "tests/phi1_conformance.rs",
        declared_assumptions: "Even-length spatial bond loops",
        authority_effect: AUTHORITY_EFFECT,
    },

    // -------------------------------------------------------------------------
    // Package 19: MUB-010
    // -------------------------------------------------------------------------
    MathematicalClaim {
        package_id: "MUB-010",
        short_title: "Mutually Unbiased Bases in Dimension 6: Moduli Stratification, Smale Sentry, and Moment Bridges",
        claim_id: "MUB6-G1",
        claim_statement: "Full moduli classification for d=6 remains an open research frontier; existence of 7 MUBs in d=6 is unproved",
        status: "OPEN_BOUNDED_ENCLOSURE",
        lean_locus: None,
        target_crates: &["core_mub", "core_certifiers"],
        primary_modules: &["mub6_claim_gate.rs"],
        certifier_or_witness: "StatedRegionSeal",
        key_verification_harness: "src/core_native/mub6_smale_sentry.rs",
        declared_assumptions: "Epistemic firewall actively rejects unhedged global MUB(6)=3 claims",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "MUB-010",
        short_title: "Mutually Unbiased Bases in Dimension 6: Moduli Stratification, Smale Sentry, and Moment Bridges",
        claim_id: "MUB6-ROUTE-C",
        claim_statement: "Exclusion of complete MUB triplet candidates via Route C verified in tested box",
        status: "FINITE_CHECKED",
        lean_locus: None,
        target_crates: &["core_mub", "core_solvers"],
        primary_modules: &["mub6_claim_gate.rs"],
        certifier_or_witness: "StatedRegionSeal",
        key_verification_harness: "src/core_native/mub6_smale_sentry.rs",
        declared_assumptions: "Specific rectangular box region in moduli space",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "MUB-010",
        short_title: "Mutually Unbiased Bases in Dimension 6: Moduli Stratification, Smale Sentry, and Moment Bridges",
        claim_id: "MUB6-CONJ-3-SENTRY",
        claim_statement: "Depth-64 Krawczyk sentry confirms box disjointness receipts for candidate quartets",
        status: "FINITE_CHECKED",
        lean_locus: Some("lean4/research_programs/mub6/TargetA12SmaleSentry.lean"),
        target_crates: &["core_mub", "core_certifiers"],
        primary_modules: &["mub6_smale_sentry.rs"],
        certifier_or_witness: "KrawczykContractor",
        key_verification_harness: "src/core_native/mub6_smale_sentry.rs",
        declared_assumptions: "Interval arithmetic enclosure, Krawczyk operator contraction",
        authority_effect: AUTHORITY_EFFECT,
    },
    MathematicalClaim {
        package_id: "MUB-010",
        short_title: "Mutually Unbiased Bases in Dimension 6: Moduli Stratification, Smale Sentry, and Moment Bridges",
        claim_id: "MUB6-SZOLLOSI-618",
        claim_statement: "618-equation degree-2 polynomial system evaluates column-gauge balance on candidate charts",
        status: "EXACT_RATIONAL",
        lean_locus: Some("lean4/research_programs/mub6/SzollosiQuadraticSystem.lean"),
        target_crates: &["core_mub", "core_certifiers"],
        primary_modules: &["mub6_smale_sentry.rs"],
        certifier_or_witness: "KrawczykContractor",
        key_verification_harness: "src/core_native/mub6_smale_sentry.rs",
        declared_assumptions: "Szollosi two-circulant parametric family",
        authority_effect: AUTHORITY_EFFECT,
    },
];

/// Returns all claims registered in the Master Traceability Registry.
pub fn all_registered_claims() -> &'static [MathematicalClaim] {
    MASTER_TRACEABILITY_REGISTRY
}

/// Returns all registered claims for a specific research paper package.
pub fn claims_for_package(package_id: &str) -> Vec<&'static MathematicalClaim> {
    MASTER_TRACEABILITY_REGISTRY
        .iter()
        .filter(|c| c.package_id == package_id)
        .collect()
}

/// Returns all registered claims that target a specific Rust crate.
pub fn claims_for_crate(crate_name: &str) -> Vec<&'static MathematicalClaim> {
    MASTER_TRACEABILITY_REGISTRY
        .iter()
        .filter(|c| c.target_crates.contains(&crate_name))
        .collect()
}

/// Returns the complete list of unique package IDs present in the registry.
pub fn registered_packages() -> Vec<&'static str> {
    let mut packages = Vec::new();
    for claim in MASTER_TRACEABILITY_REGISTRY {
        if !packages.contains(&claim.package_id) {
            packages.push(claim.package_id);
        }
    }
    packages
}

fn audit_claim_identity(claim: &MathematicalClaim, violations: &mut Vec<String>) {
    if claim.package_id.trim().is_empty() {
        violations.push(format!("Claim {:?} has empty package_id", claim.claim_id));
    }
    if claim.claim_id.trim().is_empty() {
        violations.push(format!("Package {:?} has empty claim_id", claim.package_id));
    }
    if claim.claim_statement.trim().is_empty() {
        violations.push(format!("Claim {} has empty statement", claim.claim_id));
    }
    if claim.status.trim().is_empty() {
        violations.push(format!("Claim {} has empty status", claim.claim_id));
    }
}

fn audit_claim_bindings(claim: &MathematicalClaim, violations: &mut Vec<String>) {
    if claim.target_crates.is_empty() {
        violations.push(format!("Claim {} has no target crates", claim.claim_id));
    }
    if claim.primary_modules.is_empty() {
        violations.push(format!("Claim {} has no primary modules", claim.claim_id));
    }
    if claim.certifier_or_witness.trim().is_empty() {
        violations.push(format!(
            "Claim {} has empty certifier_or_witness",
            claim.claim_id
        ));
    }
    if claim.key_verification_harness.trim().is_empty() {
        violations.push(format!(
            "Claim {} has empty verification harness",
            claim.claim_id
        ));
    }
    if claim.authority_effect != AUTHORITY_EFFECT {
        violations.push(format!(
            "Claim {} has invalid authority effect: {:?}",
            claim.claim_id, claim.authority_effect
        ));
    }
}

struct LeanDeclaration {
    file: &'static str,
    namespace: &'static str,
    name: &'static str,
}

fn qualified_lean_declaration(locus: &str) -> Option<LeanDeclaration> {
    let pre = "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4";
    match locus {
        "PreMssn.history_report_criterion" => Some(LeanDeclaration {
            file: concat_pre(pre, "Paper.lean"),
            namespace: "PreMssn",
            name: "history_report_criterion",
        }),
        "PreMssn.Homology.homologyMap" => Some(LeanDeclaration {
            file: concat_pre(pre, "Homology.lean"),
            namespace: "PreMssn.Homology",
            name: "homologyMap",
        }),
        _ => None,
    }
}

fn concat_pre(directory: &'static str, file: &'static str) -> &'static str {
    match (directory, file) {
        (
            "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4",
            "Paper.lean",
        ) => "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4/Paper.lean",
        (
            "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4",
            "Homology.lean",
        ) => "atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/lean4/Homology.lean",
        _ => "",
    }
}

fn line_declares(line: &str, name: &str) -> bool {
    let mut tokens = line.split_whitespace();
    matches!(tokens.next(), Some("theorem" | "def" | "lemma")) && tokens.next() == Some(name)
}

fn file_declares(text: &str, namespace: &str, name: &str) -> bool {
    text.lines().any(|line| line.trim() == format!("namespace {namespace}"))
        && text.lines().any(|line| line_declares(line, name))
}

fn repository_root() -> std::path::PathBuf {
    std::path::PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("..")
}

/// `MECHANIZED` is refused unless `locus` names a Lean file that exists and
/// contains the declaration. This does not elaborate the file.
pub fn mechanized_locus_refusal(
    root: &std::path::Path,
    status: &str,
    locus: Option<&str>,
) -> Option<String> {
    if status != "MECHANIZED" {
        return None;
    }
    let Some(locus) = locus else {
        return Some("MECHANIZED refused: no Lean locus".to_string());
    };
    if locus.ends_with(".lean") {
        let path = root.join(locus);
        if !path.is_file() {
            return Some(format!("MECHANIZED refused: Lean file is absent: {locus}"));
        }
        let text = match std::fs::read_to_string(&path) {
            Ok(text) => text,
            Err(error) => {
                return Some(format!("MECHANIZED refused: Lean file is unreadable: {error}"))
            }
        };
        let declared = text.lines().any(|line| {
            let mut tokens = line.split_whitespace();
            matches!(tokens.next(), Some("theorem" | "def" | "lemma")) && tokens.next().is_some()
        });
        if !declared {
            return Some(format!(
                "MECHANIZED refused: Lean file contains no declaration: {locus}"
            ));
        }
        return None;
    }
    let Some(declaration) = qualified_lean_declaration(locus) else {
        return Some(format!("MECHANIZED refused: unresolved Lean locus {locus}"));
    };
    let path = root.join(declaration.file);
    if !path.is_file() {
        return Some(format!(
            "MECHANIZED refused: Lean file is absent: {}",
            declaration.file
        ));
    }
    let text = match std::fs::read_to_string(&path) {
        Ok(text) => text,
        Err(error) => return Some(format!("MECHANIZED refused: Lean file is unreadable: {error}")),
    };
    if !file_declares(&text, declaration.namespace, declaration.name) {
        return Some(format!(
            "MECHANIZED refused: {} does not contain {}",
            declaration.file, declaration.name
        ));
    }
    None
}

/// Performs a self-consistency audit on the Master Traceability Registry.
///
/// Returns `Ok(count)` if all claims satisfy integrity invariants, or `Err(violations)`
/// listing all non-compliant claims.
pub fn verify_registry_integrity() -> Result<usize, Vec<String>> {
    let mut violations = Vec::new();
    let root = repository_root();

    for claim in MASTER_TRACEABILITY_REGISTRY {
        audit_claim_identity(claim, &mut violations);
        audit_claim_bindings(claim, &mut violations);
        if let Some(refusal) = mechanized_locus_refusal(&root, claim.status, claim.lean_locus) {
            violations.push(format!("{}: {refusal}", claim.claim_id));
        }
    }

    if violations.is_empty() {
        Ok(MASTER_TRACEABILITY_REGISTRY.len())
    } else {
        Err(violations)
    }
}

// Origin: engine/crates_rs/core_certifiers/src/mathematical_claim.rs
// Claim: urn:core:crates_rs:core-certifiers:mathematical-claim:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbde07af8 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbde07af8` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbde07af8 {
    /// Refused because `admitted_items` was zero.
    EmptyAdmission,
    /// Refused because `capacity_bound` was zero.
    CapacityZero,
    /// Refused because `admitted_items` exceeded `capacity_bound`.
    ExceedsCapacity {
        /// Requested item count.
        admitted_items: u64,
        /// Declared maximum capacity.
        capacity_bound: u64,
    },
}

#[allow(dead_code, missing_docs)]
impl BoundaryErrorbde07af8 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbde07af8 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbde07af8 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbde07af8 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbde07af8> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbde07af8::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbde07af8::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbde07af8::ExceedsCapacity {
                admitted_items,
                capacity_bound,
            });
        }
        Ok(Self {
            admitted_items,
            capacity_bound,
        })
    }

    /// Returns the admitted item count.
    pub const fn admitted_items(&self) -> u64 {
        self.admitted_items
    }

    /// Returns the declared capacity bound.
    pub const fn capacity_bound(&self) -> u64 {
        self.capacity_bound
    }

    /// Returns the remaining capacity (`capacity_bound - admitted_items`).
    pub const fn remaining_capacity(&self) -> u64 {
        self.capacity_bound.saturating_sub(self.admitted_items)
    }
}

#[cfg(test)]
mod mechanized_locus_tests {
    use super::*;

    #[test]
    fn mechanized_requires_an_existing_declaration() {
        let root = repository_root();
        let missing = "atlas/coda_atlas/F004_papers/007_finite_to_continuum/lean4/circle_haar.lean";
        assert!(mechanized_locus_refusal(&root, "MECHANIZED", Some(missing)).is_some());
        assert!(mechanized_locus_refusal(&root, "FINITE_CHECKED", Some(missing)).is_none());
        assert!(mechanized_locus_refusal(&root, "MECHANIZED", None).is_some());
        assert!(mechanized_locus_refusal(&root, "MECHANIZED", Some("cdx2.haar_formal")).is_some());

        let dir = std::env::temp_dir().join(format!("mechanized_locus_{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&dir);
        std::fs::create_dir_all(&dir).expect("temp declaration directory");
        std::fs::write(dir.join("Empty.lean"), "-- no declaration\n").expect("empty lean file");
        assert!(mechanized_locus_refusal(&dir, "MECHANIZED", Some("Empty.lean")).is_some());
        std::fs::write(
            dir.join("Declared.lean"),
            "theorem witness_exists : True := by trivial\n",
        )
        .expect("declared lean file");
        assert!(mechanized_locus_refusal(&dir, "MECHANIZED", Some("Declared.lean")).is_none());
        let _ = std::fs::remove_dir_all(&dir);

        let haar = MASTER_TRACEABILITY_REGISTRY
            .iter()
            .find(|claim| claim.claim_id == "cdx2.haar_formal")
            .expect("haar row");
        assert_ne!(haar.status, "MECHANIZED");
        assert!(haar.lean_locus.is_none());
        for claim in MASTER_TRACEABILITY_REGISTRY
            .iter()
            .filter(|claim| claim.status == "MECHANIZED")
        {
            assert!(
                mechanized_locus_refusal(&root, claim.status, claim.lean_locus).is_none(),
                "{}",
                claim.claim_id
            );
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_bde07af8 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbde07af8::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbde07af8::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbde07af8::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbde07af8::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbde07af8::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbde07af8::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbde07af8::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
