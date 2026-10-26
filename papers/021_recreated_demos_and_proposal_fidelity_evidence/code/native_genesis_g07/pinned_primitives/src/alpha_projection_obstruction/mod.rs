//! # alpha_projection_obstruction — PO-000 replicated in Rust
//!
//! `AuthorityEffect: None.`
//!
//! A replication of the CODA atlas paper **PO-000, "Projection
//! Obstruction"** (`coda_atlas/F004_papers/002_projection_obstruction/
//! 000_projection_obstruction/projection_obstruction.md`, v6.3) and of the
//! Python package in its `code/` folder, using only this crate — no
//! external dependency, no NumPy, no symbolic engine — and reading the
//! paper's constructions through the primitives of the sealed derivation
//! wherever one of them fits.
//!
//! ## What is replicated, and at what evidence kind
//!
//! | ledger | paper | file | kind | pinned against |
//! |---|---|---|---|---|
//! | B1, B2 | §2.2 coboundary, `I(s)`, the `2\|E\|‖s‖_∞` bound | `covering_edge.rs` | exact finite | defect `[['2']]`, `I = 2`, bound `6` |
//! | B3, C1 | §3 chart nonlinearity; semigroup defect | `retraction_geometry.rs` | exact symbolic instance | `[['x**2'], ['0']]`, `[['2*x','0'],['0','0']]`, `[['-2'],['0'],['0']]` |
//! | Prop 3.B | §3.4 projection ≠ authorization | `projection_factor.rs` | exact instance | left manifold, projected identity, collapse blocked |
//! | A2, A3, D8, G1 | §7.2 induced cochain, membership, quotient distance | `cochain_presentation.rs` | exact finite | `[2,3]`, witness `[2]`, separator `[-1,1]`, `Φ = 1` |
//! | B4, G2 | §7.2 no `C²`/`d₁` | `cochain_presentation.rs` | refusal | typed refusal |
//! | D1–D6 | §4 RE1–RE5 and the two countermodels | `replica_hierarchy.rs` | finite exhaustive; countermodels | 9 points; `ℓ²` breaks RE3; scaled sum breaks RE5 |
//! | E1 | §5 normalisation `D, D/2, D/d²` | `mod.rs` | exact | `4, 2, 1` |
//! | E5, E9 | Cor. 5.1.A on a supplied family | `family_bound.rs` | exact finite | window `1/64`, floors `3/256` |
//! | E8 | §5.6 reverse-triangle transfer | `transfer.rs` | exact finite | `2, 0, 2, −3` |
//! | A1, E2, E4, F1–F3 | §§5–6 lattice replays | `quantum_lattice.rs` (`numeric.rs`) | numerical replay | `ν = 2`, `g = 1 / 101`, defects, `1/√2 + 1/4`, TFIM `2\|J\|`, `g = 3.5` |
//! | H1–H7 | §7.4 observers, three-patch witness, scaling | `observer_carriers.rs` | exact finite; countermodel | `I = 6`, `J = 0`, `Λ = 6`; `3, 14, 30` |
//! | H8 | Prop. 7.4.7-B coupled carrier | `observer_carriers.rs` | exact finite (Lean-only in Python) | kernels nontrivial, All-Green ⇒ `I = 0` |
//! | H9 | §7.4.12 quotient witness | `observer_carriers.rs` | exact finite (Lean-only in Python) | `Φ([ω]) = 2`, `ω ∉ im d₀` |
//!
//! Refused here, as in the Python package: C2 (the general parallel-tensor
//! theorem), C4 and E3 (open nondegeneracy; the universally quantified
//! `8g²/24g²` estimates), E4-second and E4-commutator (Appendix B's
//! product-rule assembly — Lean-resident), the static scope fence A4–G4
//! (a prose audit, not mathematics), and the `so(k)` benchmark (a
//! floating-point optimisation outside the exact scope).  A refusal is a
//! typed disposition with a reason, never a pass and never a fail.
//!
//! ## The estate's vocabulary, applied
//!
//! * The paper's `I(s)` is a **represented** defect on a declared section —
//!   a number the observers can be shown, not an `H¹` class.  The
//!   three-patch witness is the estate's `ObserverIncomplete` terminal made
//!   concrete: every declared observer is green, the metatheory sees
//!   `I = 6`, and the gap is in the kernels, not in the section.
//! * Every exact result carries the estate's **certificate kind**:
//!   exhaustion (`⊢ᴱ`) for the RE grid audit and the vertex enumerations,
//!   witness (`⊢ᵂ`) for a repair or a bound recomputed on both sides,
//!   obstruction (`⊢ᴼ`) for a separating left-kernel vector.  A missing
//!   `d₁` is none of the three — it is a refusal — and no `Certificate` is
//!   ever built from a floating-point comparison (`FW-RECEIPT`).
//! * `projection_factor.rs` is the licence gate as a countermodel: an
//!   evaluation tally is never an authorization.
//!
//! ## Receipt
//!
//! `run()` recomputes everything and renders a deterministic text.
//! `RECEIPT.txt` beside this file is that text, and a test compares the
//! two byte for byte (set `PO000_WRITE_RECEIPT=1` to regenerate).  Floats
//! are printed to twelve significant digits so the receipt does not depend
//! on the last bits of a particular machine's summation order; the tests
//! pin the numerical values with explicit tolerances.

pub mod cochain_presentation;
pub mod covering_edge;
pub mod derivative_bound;
pub mod family_bound;
pub mod gauge_coupling_bridge;
pub mod matrix;
pub mod numeric;
pub mod observer_carriers;
pub mod projection_factor;
pub mod quantum_lattice;
pub mod rational;
pub mod replica_hierarchy;
pub mod retraction_geometry;
pub mod transfer;
pub mod verify;

/// Reference receipt beside the central implementation, independent of the
/// manifest directory of a compatibility binary that links this library.
pub fn receipt_path() -> std::path::PathBuf {
    std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join("alpha_projection_obstruction")
        .join("RECEIPT.txt")
}

use std::collections::BTreeMap;
use std::fmt::Write as _;

use rational::{q, r, Rational};

/// How a claim was replayed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EvidenceKind {
    /// Exact rational arithmetic on a finite instance.
    ExactFinite,
    /// Exact arithmetic with a symbol.
    ExactSymbolicInstance,
    /// Every point of a declared finite grid.
    FiniteExhaustive,
    /// A concrete instance where a would-be theorem fails.
    Counterexample,
    /// A premise inventory on one fixture.
    PremiseCheck,
    /// Floating point on one fixture.
    NumericalReplay,
    /// Not executable here.
    NotExecutable,
}

impl EvidenceKind {
    /// The Python package's spelling.
    pub fn name(self) -> &'static str {
        match self {
            EvidenceKind::ExactFinite => "exact_finite",
            EvidenceKind::ExactSymbolicInstance => "exact_symbolic_instance",
            EvidenceKind::FiniteExhaustive => "finite_exhaustive",
            EvidenceKind::Counterexample => "counterexample",
            EvidenceKind::PremiseCheck => "premise_check",
            EvidenceKind::NumericalReplay => "numerical_replay",
            EvidenceKind::NotExecutable => "not_executable",
        }
    }
}

/// The verdict of one replay.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Verdict {
    /// The replay ran and every pinned value matched.
    Pass,
    /// The replay ran and something did not match.
    Fail,
    /// Not executable here; a typed disposition with a reason.
    Refused,
}

impl Verdict {
    /// Text.
    pub fn name(self) -> &'static str {
        match self {
            Verdict::Pass => "pass",
            Verdict::Fail => "fail",
            Verdict::Refused => "refused",
        }
    }
}

/// One claim's replay.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct ClaimEvidence {
    /// Ledger ids.
    pub claim_ids: Vec<&'static str>,
    /// Title.
    pub title: &'static str,
    /// Kind.
    pub evidence_kind: EvidenceKind,
    /// Verdict.
    pub verdict: Verdict,
    /// What the statement ranges over.
    pub statement_scope: &'static str,
    /// The witness values, in order.
    pub witness: Vec<(&'static str, String)>,
    /// What this does not show.
    pub limitations: Vec<&'static str>,
}

fn verdict(passed: bool) -> Verdict {
    if passed {
        Verdict::Pass
    } else {
        Verdict::Fail
    }
}

/// Twelve significant digits, Python-style (`2.0`, `0.03`, `5.68e-14`).
pub fn receipt_float(x: f64) -> String {
    if x == 0.0 {
        return "0.0".into();
    }
    let rounded: f64 = format!("{x:.11e}").parse().expect("round trip");
    let a = rounded.abs();
    let s = if !(1e-4..1e16).contains(&a) { format!("{rounded:e}") } else { format!("{rounded}") };
    if s.contains('.') || s.contains('e') {
        s
    } else {
        format!("{s}.0")
    }
}

fn covering_edge_receipt() -> ClaimEvidence {
    let (d, s) = covering_edge::receipt_fixture();
    let defects = d.coboundary(&s).expect("fixture");
    let bound = d.coboundary_bound_certificate(&s).expect("fixture");
    let defect = defects["b>a"].to_string();
    let passed = defect == "[['2']]" && d.inconsistency(&s).expect("fixture") == q(2) && bound.holds && bound.certificate().is_some();
    ClaimEvidence {
        claim_ids: vec!["B1", "B2"],
        title: "Exact covering-edge coboundary and raw tally",
        evidence_kind: EvidenceKind::ExactFinite,
        verdict: verdict(passed),
        statement_scope: "one exact rational covering edge",
        witness: vec![("defect", defect), ("raw_I", bound.coboundary_norm.to_string()), ("bound", bound.bound.to_string()), ("certificate", bound.certificate().map_or("none".into(), |c| c.to_string()))],
        limitations: vec!["Finite rational instance; the Banach-space bound remains analytic."],
    }
}

fn geometry_receipt() -> ClaimEvidence {
    let g = retraction_geometry::affine_nonlinearity_instance();
    let s = retraction_geometry::semigroup_defect_instance();
    let passed = g.generator_is_skew && g.retraction_is_idempotent && g.tangent_projection_is_idempotent && g.derivative_is_nonconstant && g.midpoint_is_on_manifold && s.is_nonzero;
    ClaimEvidence {
        claim_ids: vec!["B3", "C1"],
        title: "Exact graph-retraction nonlinearity and semigroup defect",
        evidence_kind: EvidenceKind::ExactSymbolicInstance,
        verdict: verdict(passed),
        statement_scope: "the graph z=x^2 with one skew generator",
        witness: vec![
            ("chart_vector_field", g.chart_vector_field.to_string()),
            ("chart_derivative", g.chart_derivative.to_string()),
            ("midpoint_nonaffinity_defect", g.midpoint_nonaffinity_defect.to_string()),
            ("semigroup_defect", s.defect.to_string()),
        ],
        limitations: vec!["Concrete hypothesis-valid instance, not the quantified Banach theorem.", "Trigonometry is exact at multiples of pi/2 only; the instance uses pi/2 and pi."],
    }
}

fn projection_factor_receipt() -> ClaimEvidence {
    let e = projection_factor::run_experiment();
    let passed = e.left_manifold && e.projected_is_identity && e.normal_leak_nonzero && e.retraction_residual_nonzero && e.semigroup_defect_zero && !e.authorized && e.collapse_would_authorize && e.collapse_blocked;
    ClaimEvidence {
        claim_ids: vec!["Prop-3B"],
        title: "Projection is not authorization: orbit leaves M, projected family is the identity, tally is not an act",
        evidence_kind: EvidenceKind::ExactSymbolicInstance,
        verdict: verdict(passed),
        statement_scope: "T_t = [[1,0],[a(1-q),q]] with q = e^{-t} as a formal symbol, a = x = 1",
        witness: vec![
            ("left_manifold", e.left_manifold.to_string()),
            ("projected_is_identity", e.projected_is_identity.to_string()),
            ("authorized", e.authorized.to_string()),
            ("collapse_would_authorize", e.collapse_would_authorize.to_string()),
            ("collapse_blocked", e.collapse_blocked.to_string()),
        ],
        limitations: vec!["Finite replay; not a Banach-manifold theorem and not a quantum result.", "The Python evaluates at t=1 with e^{-1} as an exact atom; here q is a symbol and nonzero means nonzero as a polynomial."],
    }
}

fn cochain_receipts() -> (ClaimEvidence, ClaimEvidence) {
    let p = cochain_presentation::receipt_presentation();
    let residuals = BTreeMap::from([("e1".to_string(), matrix::Matrix::column_i128(&[2])), ("e2".to_string(), matrix::Matrix::column_i128(&[3]))]);
    let field = p.induce_field(&residuals).expect("fixture").as_vector();
    let problem = cochain_presentation::LinearRepairProblem::new(matrix::Matrix::from_i128(&[&[1], &[1]]));
    let exact = problem.exactness_certificate(&matrix::Matrix::column_i128(&[2, 2])).expect("fixture");
    let obstructed = problem.exactness_certificate(&field).expect("fixture");
    let quotient = problem.quotient_l1_distance(&field).expect("fixture");
    let refused = matches!(cochain_presentation::verify_cochain_complex(&problem.d0, None), Err(cochain_presentation::CochainRefusal::HigherDifferentialUnavailable(_)));
    let passed = exact.verify() && exact.is_exact_coboundary && obstructed.verify() && !obstructed.is_exact_coboundary && quotient.verify() && quotient.distance == q(1);
    (
        ClaimEvidence {
            claim_ids: vec!["A2", "A3", "D8", "G1"],
            title: "Exact linear observation, repair, image membership, and image distance pipeline",
            evidence_kind: EvidenceKind::ExactFinite,
            verdict: verdict(passed),
            statement_scope: "one ordered rational observation presentation",
            witness: vec![
                ("induced_field", field.to_string()),
                ("repair_witness", exact.witness.as_ref().map_or("none".into(), |w| w.to_string())),
                ("repair_certificate", exact.certificate().expect("verified exact witness").to_string()),
                ("separator", obstructed.separating_left_kernel_vector.as_ref().map_or("none".into(), |v| v.to_string())),
                ("separator_pairing", obstructed.separating_pairing.map_or("none".into(), |p| p.to_string())),
                ("obstruction_certificate", obstructed.certificate().expect("verified exact witness").to_string()),
                ("quotient_distance", quotient.distance.to_string()),
                ("quotient_dual_witness", quotient.dual_witness.to_string()),
                ("quotient_dual_pairing", quotient.dual_pairing.to_string()),
            ],
            limitations: vec!["Linear algebra repair level; no cochain complex capability is synthesized."],
        },
        ClaimEvidence {
            claim_ids: vec!["B4", "G2"],
            title: "Higher-cell data is absent and explicitly refused",
            evidence_kind: EvidenceKind::NotExecutable,
            verdict: if refused { Verdict::Refused } else { Verdict::Fail },
            statement_scope: "native covering-edge data without C2 or d1",
            witness: vec![("higher_differential_refused", refused.to_string())],
            limitations: vec!["Higher cells belong to PO-001/PO-003 and are not synthesized."],
        },
    )
}

fn replica_receipts() -> (ClaimEvidence, ClaimEvidence, ClaimEvidence) {
    use replica_hierarchy::{default_scalars, receipt_samples, Diagnostic, FiniteDiagnosticFamily};
    let (edges, gauges, types, samples) = receipt_samples();
    let family = |d: Diagnostic| FiniteDiagnosticFamily::new(edges.clone(), gauges.clone(), d, Some(types.clone())).expect("fixture");
    let unweighted = family(Diagnostic::UnweightedL1).audit(&samples, &default_scalars()).expect("fixture");
    let weighted = family(Diagnostic::weighted(edges.iter().map(|e| (e.clone(), q(2))).collect()).expect("fixture")).audit(&samples, &default_scalars()).expect("fixture");
    let lp = family(Diagnostic::LpCounterexample).audit(&samples, &default_scalars()).expect("fixture");
    let scaled = family(Diagnostic::scaled(q(2)).expect("fixture")).audit(&samples, &default_scalars()).expect("fixture");
    let finite_passed = unweighted.all_axioms() && weighted.re3_disjoint_replica_additivity && weighted.re4_edge_exchange_symmetry && !weighted.re5_singleton_calibration;
    let identity_passed = unweighted.re3_disjoint_replica_additivity && unweighted.re5_singleton_calibration;
    let counter_passed = !lp.re3_disjoint_replica_additivity && lp.re5_singleton_calibration && scaled.re3_disjoint_replica_additivity && !scaled.re5_singleton_calibration;
    (
        ClaimEvidence {
            claim_ids: vec!["D1", "D3", "D4"],
            title: "Finite exhaustive RE1--RE5 structural audit",
            evidence_kind: EvidenceKind::FiniteExhaustive,
            verdict: verdict(finite_passed),
            statement_scope: "all points and all subset bipartitions on the declared exact grid",
            witness: vec![
                ("checked_points", unweighted.checked_points.to_string()),
                ("all_unweighted_axioms", unweighted.all_axioms().to_string()),
                ("weighted_RE3", weighted.re3_disjoint_replica_additivity.to_string()),
                ("weighted_RE4", weighted.re4_edge_exchange_symmetry.to_string()),
                ("weighted_RE5", weighted.re5_singleton_calibration.to_string()),
                ("certificate", unweighted.certificate("the unweighted l1 sum").to_string()),
            ],
            limitations: vec!["Exhaustive only on the recorded finite exact grid."],
        },
        ClaimEvidence {
            claim_ids: vec!["D2", "D5"],
            title: "Exact finite singleton decomposition and calibration identities",
            evidence_kind: EvidenceKind::ExactFinite,
            verdict: verdict(identity_passed),
            statement_scope: "the declared exact finite diagnostic family",
            witness: vec![("RE3", unweighted.re3_disjoint_replica_additivity.to_string()), ("RE5", unweighted.re5_singleton_calibration.to_string())],
            limitations: vec!["Finite pointwise certificate; the finite-structural hierarchy remains prose/Lean."],
        },
        ClaimEvidence {
            claim_ids: vec!["D6"],
            title: "Exact drop-RE3 and drop-RE5 countermodels",
            evidence_kind: EvidenceKind::Counterexample,
            verdict: verdict(counter_passed),
            statement_scope: "the declared p=2 and scale=2 exact countermodels",
            witness: vec![
                ("lp_breaks_RE3", (!lp.re3_disjoint_replica_additivity).to_string()),
                ("lp_first_RE3_failure", lp.counterexamples.iter().find(|c| c.axiom == "RE3").map_or("none".into(), |c| c.detail.clone())),
                ("scaled_sum_breaks_RE5", (!scaled.re5_singleton_calibration).to_string()),
                ("scaled_first_RE5_failure", scaled.counterexamples.iter().find(|c| c.axiom == "RE5").map_or("none".into(), |c| c.detail.clone())),
            ],
            limitations: vec!["Concrete countermodels, not an independence proof beyond their scope."],
        },
    )
}

fn quantum_receipts() -> Result<(ClaimEvidence, ClaimEvidence), String> {
    use quantum_lattice::{pass45_counterexample_lattice, pass45_counterexample_replay, two_qubit_xx_lattice, DEFAULT_COMPARISON_ATOL};
    let c = pass45_counterexample_replay(0.03, DEFAULT_COMPARISON_ATOL)?;
    let lattice = pass45_counterexample_lattice()?;
    let full = lattice.short_time_bound_replay(("u", "v"), c.t, DEFAULT_COMPARISON_ATOL)?;
    let positive = two_qubit_xx_lattice(1.0)?.short_time_bound_replay(("a", "b"), 0.01, DEFAULT_COMPARISON_ATOL)?;
    let external = lattice.normal_rate_replay(("u", "v"), Some(&["uw"]))?;
    let all = lattice.normal_rate_replay(("u", "v"), None)?;
    let premises = (c.nu_e - 2.0).abs() < 1e-12 && (c.isolated_two_site_g - 1.0).abs() < 1e-12 && (c.full_incident_g - 101.0).abs() < 1e-12;
    let numerical = c.isolated_bound_violated
        && c.full_bound_satisfied_with_tolerance
        && positive.signed_lower_bound_rhs > 0.0
        && positive.bound_satisfied_with_tolerance
        && external.nu_e < 1e-9
        && (all.nu_e - 2.0).abs() < 1e-9
        && full.bound_satisfied_with_tolerance
        && full.signed_lower_bound_rhs < 0.0;
    Ok((
        ClaimEvidence {
            claim_ids: vec!["A1"],
            title: "Finite product-retraction and active-edge premise inventory",
            evidence_kind: EvidenceKind::PremiseCheck,
            verdict: verdict(premises),
            statement_scope: "the declared three-qubit Pass 45 carrier",
            witness: vec![("nu_e", receipt_float(c.nu_e)), ("isolated_two_site_g", receipt_float(c.isolated_two_site_g)), ("full_incident_g", receipt_float(c.full_incident_g))],
            limitations: vec!["Finite premise check; it does not prove positive density for families."],
        },
        ClaimEvidence {
            claim_ids: vec!["E2", "E4"],
            title: "Finite support-tangency and nontrivial positive short-time bound replays",
            evidence_kind: EvidenceKind::NumericalReplay,
            verdict: verdict(numerical),
            statement_scope: "one positive-RHS two-qubit check and the Pass 45 lattice at t=0.03",
            witness: vec![
                ("t", receipt_float(c.t)),
                ("observed_defect", receipt_float(c.observed_defect)),
                ("isolated_signed_rhs", receipt_float(c.isolated_signed_rhs)),
                ("full_signed_rhs", receipt_float(c.full_signed_rhs)),
                ("external_incident_normal_rate_below", "1e-9".to_string()),
                ("positive_rhs_t", receipt_float(positive.t)),
                ("positive_rhs_nu_e", receipt_float(positive.nu_e)),
                ("positive_rhs_g", receipt_float(positive.full_incident_g)),
                ("positive_rhs", receipt_float(positive.signed_lower_bound_rhs)),
                ("positive_rhs_observed_defect", receipt_float(positive.observed_defect)),
                ("comparison_tolerance", receipt_float(DEFAULT_COMPARISON_ATOL)),
            ],
            limitations: vec!["Numerical finite replay; not a proof for every lattice or time.", "Pass 45 remains a counterexample to the obsolete isolated-g substitution.", "Norms are Hermitian eigenvalue sums by cyclic Jacobi, not SVD; every input here is Hermitian."],
        },
    ))
}

/// E1 — `D = 4`, `T = D/2 = 2`, `D̂ = D/d² = 1` at `d = 2`.
pub fn normalization_arithmetic() -> (Rational, Rational, Rational) {
    let d = q(2);
    let raw = q(4);
    (raw, raw / q(2), raw / (d * d))
}

fn normalization_receipt() -> ClaimEvidence {
    let (raw, t, hat) = normalization_arithmetic();
    ClaimEvidence {
        claim_ids: vec!["E1"],
        title: "Exact normalization arithmetic",
        evidence_kind: EvidenceKind::ExactSymbolicInstance,
        verdict: verdict(t == q(2) && hat == q(1)),
        statement_scope: "one equal-endpoint d=2 scalar instance",
        witness: vec![("D", raw.to_string()), ("T", t.to_string()), ("D_hat", hat.to_string())],
        limitations: vec!["Norm comparison theorems remain imported analytic facts."],
    }
}

fn family_receipt() -> ClaimEvidence {
    let (members, premises) = family_bound::receipt_family();
    let c = family_bound::certify_uniform_family(&members, &premises, r(1, 64)).expect("fixture");
    let passed = c.accepted && c.verify() && c.uniform_window_upper == Some(r(1, 64)) && c.site_density_floor == Some(r(3, 256));
    ClaimEvidence {
        claim_ids: vec!["E5", "E9"],
        title: "Exact finite-family premise and density-bound certificate",
        evidence_kind: EvidenceKind::ExactFinite,
        verdict: verdict(passed),
        statement_scope: "two supplied finite family members at t=1/64",
        witness: vec![
            ("window", c.uniform_window_upper.map_or("none".into(), |v| v.to_string())),
            ("local_edge_polynomial", c.local_edge_polynomial.map_or("none".into(), |v| v.to_string())),
            ("edge_density_floor", c.edge_density_floor.map_or("none".into(), |v| v.to_string())),
            ("site_density_floor", c.site_density_floor.map_or("none".into(), |v| v.to_string())),
            ("member_count", c.member_bounds.len().to_string()),
        ],
        limitations: vec!["Finite supplied family; no infinite-family quantifier is discharged."],
    }
}

fn transfer_receipt() -> ClaimEvidence {
    let c = transfer::linear_projection_transfer_certificate(&matrix::Matrix::column_i128(&[1, 2]), &matrix::Matrix::column_i128(&[1, 0]), &matrix::Matrix::from_i128(&[&[1, 0], &[0, 0]]), r(1, 2)).expect("fixture");
    ClaimEvidence {
        claim_ids: vec!["E8"],
        title: "Exact reverse-triangle transfer certificate",
        evidence_kind: EvidenceKind::ExactFinite,
        verdict: verdict(c.accepted && c.verify()),
        statement_scope: "one exact rational pair and linear projection",
        witness: vec![
            ("source_distance", c.source_distance.to_string()),
            ("projection_distance", c.projection_distance.to_string()),
            ("rho_defect", c.rho_defect.to_string()),
            ("transfer_lower_bound", c.transfer_lower_bound.to_string()),
            ("certificate", c.certificate().map_or("none".into(), |x| x.to_string())),
        ],
        limitations: vec!["Instance receipt; the abstract theorem remains Lean/prose backed."],
    }
}

fn worked_examples_receipts() -> Result<(ClaimEvidence, ClaimEvidence), String> {
    let xx = quantum_lattice::two_qubit_xx_example(1.0)?;
    let tfim = quantum_lattice::tfim_normal_rate_example(4, 1.0, 1.5)?;
    let passed = xx.absolute_error < 1e-12 && (xx.closed_form_defect - xx.expected_special_value).abs() < 1e-12 && tfim.maximum_rate_error < 1e-10 && tfim.g_within_paper_bound && tfim.all_edges_active;
    Ok((
        ClaimEvidence {
            claim_ids: vec!["F1", "F2"],
            title: "Two-qubit XX and finite TFIM worked-example replays",
            evidence_kind: EvidenceKind::NumericalReplay,
            verdict: verdict(passed),
            statement_scope: "one two-qubit time and one four-site open TFIM chain",
            witness: vec![
                ("xx_observed", receipt_float(xx.observed_defect)),
                ("xx_closed_form", receipt_float(xx.closed_form_defect)),
                ("xx_absolute_error_below", "1e-12".to_string()),
                ("tfim_expected_rate", receipt_float(tfim.expected_rate)),
                ("tfim_max_rate_error_below", "1e-10".to_string()),
            ],
            limitations: vec!["Finite numerical worked examples only."],
        },
        ClaimEvidence {
            claim_ids: vec!["F3"],
            title: "Finite TFIM full-incident-load premise inventory",
            evidence_kind: EvidenceKind::PremiseCheck,
            verdict: verdict(tfim.g_within_paper_bound),
            statement_scope: "one four-site open TFIM chain",
            witness: vec![("tfim_full_g", receipt_float(tfim.full_incident_g)), ("tfim_g_upper_bound", receipt_float(tfim.paper_g_upper_bound))],
            limitations: vec!["Finite graph inventory; not an infinite-chain statement."],
        },
    ))
}

fn observer_receipts() -> Result<(ClaimEvidence, ClaimEvidence, ClaimEvidence, ClaimEvidence), String> {
    use observer_carriers::{coupled_carrier_certificate, quotient_witness, scaling_family_certificate, three_patch_certificate, LocalObserverCarrier, ObserverFamily};
    let three = three_patch_certificate(Rational::ONE)?;
    let scaling = scaling_family_certificate(&[r(1, 2), r(7, 3), q(5)])?;
    let injective = ObserverFamily::new(
        BTreeMap::from([("e".to_string(), 2)]),
        vec![
            LocalObserverCarrier { observer_id: "x".into(), maps: BTreeMap::from([("e".to_string(), matrix::Matrix::from_i128(&[&[1, 0]]))]) },
            LocalObserverCarrier { observer_id: "y".into(), maps: BTreeMap::from([("e".to_string(), matrix::Matrix::from_i128(&[&[0, 1]]))]) },
        ],
    )?;
    let injectivity = injective.joint_injectivity_certificate()?;
    let local_to_global = injective.local_to_global_certificate(&BTreeMap::from([("e".to_string(), matrix::Matrix::zeros(2, 1))]))?;
    let fragmented = ObserverFamily::new(
        BTreeMap::from([("e1".to_string(), 1), ("e2".to_string(), 1)]),
        vec![
            LocalObserverCarrier { observer_id: "left".into(), maps: BTreeMap::from([("e1".to_string(), matrix::Matrix::eye(1))]) },
            LocalObserverCarrier { observer_id: "right".into(), maps: BTreeMap::from([("e2".to_string(), matrix::Matrix::eye(1))]) },
        ],
    )?;
    let gap = fragmented.visibility_gap_decomposition(&BTreeMap::from([("e1".to_string(), matrix::Matrix::column_i128(&[1])), ("e2".to_string(), matrix::Matrix::column_i128(&[1]))]))?;
    let three_gap = three.family.visibility_gap_decomposition(&three.defects)?;
    let three_passed = three.verify() && three.tallies.i == q(6) && three.tallies.all_green();
    let passed = three_passed && scaling.verify() && gap.verify() && gap.edgewise_observation_loss.is_zero() && gap.single_observer_fragmentation == q(1) && injectivity.verify() && injectivity.premises_hold && local_to_global.verify() && local_to_global.accepted;
    let j_text = |t: &observer_carriers::ObserverTallies| format!("{{{}}}", t.j.iter().map(|(k, v)| format!("{k}: {v}")).collect::<Vec<_>>().join(", "));
    let coupled = coupled_carrier_certificate()?;
    let coupled_passed = coupled.full_edge_coverage && coupled.joint_kernel_nontrivial.values().all(|b| *b) && coupled.all_green_forces_zero && coupled.corollary_premise_refused;
    let witness = quotient_witness()?;
    let witness_passed = !witness.exactness.is_exact_coboundary && witness.exactness.verify() && witness.quotient.verify() && witness.quotient.distance == q(2);
    Ok((
        ClaimEvidence {
            claim_ids: vec!["H1", "H2", "H3", "H4", "H6", "H7"],
            title: "Exact observer passivity, kernels, scaling, and injectivity",
            evidence_kind: EvidenceKind::ExactFinite,
            verdict: verdict(passed),
            statement_scope: "one six-edge witness, three rational scales, and one rank-two carrier",
            witness: vec![
                ("three_patch_I", three.tallies.i.to_string()),
                ("three_patch_J", j_text(&three.tallies)),
                ("three_patch_Lambda", three.tallies.lambda.to_string()),
                ("three_patch_edgewise_observation_loss", three_gap.edgewise_observation_loss.to_string()),
                ("fragmentation_example_edgewise_observation_loss", gap.edgewise_observation_loss.to_string()),
                ("fragmentation_example_single_observer_fragmentation", gap.single_observer_fragmentation.to_string()),
                ("scaled_I", format!("[{}]", scaling.instances.iter().map(|i| i.tallies.i.to_string()).collect::<Vec<_>>().join(", "))),
                ("combined_rank", format!("{{e: {}}}", injectivity.edgewise_combined_rank["e"])),
                ("three_patch_corollary_7_4_7_refusal", three.family.local_to_global_certificate(&three.defects)?.refusals.join("; ")),
            ],
            limitations: vec!["Finite exact carriers only; finite-structural claims remain prose."],
        },
        ClaimEvidence {
            claim_ids: vec!["H5"],
            title: "Exact three-patch Local-Green/Global-Red counterexample",
            evidence_kind: EvidenceKind::Counterexample,
            verdict: verdict(three_passed),
            statement_scope: "the explicit covering diagram and section of Proposition 7.4.5",
            witness: vec![("I", three.tallies.i.to_string()), ("J", j_text(&three.tallies)), ("Lambda", three.tallies.lambda.to_string())],
            limitations: vec!["One exact finite counterexample carrier."],
        },
        ClaimEvidence {
            claim_ids: vec!["H8"],
            title: "Coupled carrier: joint kernels nontrivial on every edge, yet All-Green forces I = 0 (Proposition 7.4.7-B)",
            evidence_kind: EvidenceKind::ExactFinite,
            verdict: verdict(coupled_passed),
            statement_scope: "P = {x, u1, u2}, fibers R^2, zero restrictions, observer i reads coordinate 3-i; all sections, by linear algebra on C^0 = R^6",
            witness: vec![
                ("full_edge_coverage", coupled.full_edge_coverage.to_string()),
                ("joint_kernel_nontrivial", format!("{{{}}}", coupled.joint_kernel_nontrivial.iter().map(|(k, v)| format!("{k}: {v}")).collect::<Vec<_>>().join(", "))),
                ("all_green_section_dimension", coupled.all_green_section_dimension.to_string()),
                ("all_green_forces_zero", coupled.all_green_forces_zero.to_string()),
                ("corollary_7_4_7_premise_refused", coupled.corollary_premise_refused.to_string()),
                ("red_instance_I_at_s_x_eq_1_2", coupled.red_instance.i.to_string()),
                ("red_instance_J", j_text(&coupled.red_instance)),
            ],
            limitations: vec!["Computed here; the Python package leaves this to Lean (po000_l004_observer_visibility.lean, namespace Coupled)."],
        },
        ClaimEvidence {
            claim_ids: vec!["H9"],
            title: "Fiber-level quotient witness: Phi([omega]) = 2 > 0 on the coupled scalar gauge (section 7.4.12)",
            evidence_kind: EvidenceKind::ExactFinite,
            verdict: verdict(witness_passed),
            statement_scope: "scalar fibers on the coupled diagram, omega = (1, -1)",
            witness: vec![
                ("d0", witness.d0.to_string()),
                ("omega", witness.omega.to_string()),
                ("omega_exact", witness.exactness.is_exact_coboundary.to_string()),
                ("separator", witness.exactness.separating_left_kernel_vector.as_ref().map_or("none".into(), |v| v.to_string())),
                ("quotient_distance", witness.quotient.distance.to_string()),
                ("primal_repair", witness.quotient.repair_witness.to_string()),
                ("dual_witness", witness.quotient.dual_witness.to_string()),
                ("obstruction_certificate", witness.exactness.certificate().expect("verified exact witness").to_string()),
            ],
            limitations: vec!["Computed here; the Python package leaves this to Lean (namespace QuotientWitness).", "Does not identify any section 5 physical residual with omega."],
        },
    ))
}

fn refusals() -> Vec<ClaimEvidence> {
    let refused = |ids: Vec<&'static str>, title: &'static str, scope: &'static str, witness: Vec<(&'static str, String)>, limitations: Vec<&'static str>| ClaimEvidence {
        claim_ids: ids,
        title,
        evidence_kind: EvidenceKind::NotExecutable,
        verdict: Verdict::Refused,
        statement_scope: scope,
        witness,
        limitations,
    };
    vec![
        refused(
            vec!["A4", "A5", "A6", "A7", "C3", "D7", "D8a", "E6", "E7", "G3", "G4"],
            "Literal authority, nonclaim, host, and companion-paper scope fences",
            "the package's checked-in scope documents",
            vec![("reason", "a literal-fragment audit of prose is not replicated; it is not mathematics and this crate reads no paper text".into())],
            vec!["The Python receipt passes on the checked-in README and paper; nothing here depends on it."],
        ),
        refused(
            vec!["C2"],
            "General parallel-tensor theorem remains imported",
            "universally quantified differential geometry",
            vec![("reason", "this crate supplies instances, not a formal manifold library".into())],
            vec!["Requires prose or formal-library proof."],
        ),
        refused(
            vec!["C4", "E3"],
            "Open nondegeneracy and finite-structural analytic estimates remain outside this crate",
            "S1 and the universally quantified 8g^2/24g^2 bounds",
            vec![("C4", "open S1 obligation".into()), ("E3", "paper-resident analytic proof".into())],
            vec!["Finite instances cannot discharge either general statement."],
        ),
        refused(
            vec!["E4-second", "E4-commutator"],
            "Appendix B second-derivative and double-commutator cores are Lean-resident",
            "the Appendix B product-rule assembly and commutator-norm layer",
            vec![("E4-second", "po000_l003_second_deriv_bound.lean".into()), ("E4-commutator", "po000_l003_double_commutator_estimates.lean (numerical factors only)".into())],
            vec!["Not verified here; the constants 2g, 8g^2, 24g^2, 48g^2 are used by the family bound as declared inputs."],
        ),
        refused(
            vec!["so_k_benchmark"],
            "The so(k) three-cell benchmark is a floating-point optimisation outside the exact scope",
            "code/so_k_3cell_benchmark.py",
            vec![("reason", "L-BFGS over so(k) is neither exact nor part of the mechanization run; not replicated".into())],
            vec!["The Python package itself keeps it outside its receipts."],
        ),
    ]
}

/// The whole run.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct MechanizationRun {
    /// Paper version replicated.
    pub paper_version: &'static str,
    /// Every claim's evidence, in the Python package's order, plus the two
    /// Lean-only claims computed here.
    pub results: Vec<ClaimEvidence>,
    /// Every executable replay passed.
    pub executable_checks_passed: bool,
    /// Some claim was refused.
    pub refusals_present: bool,
}

impl MechanizationRun {
    /// The ledger ids covered, sorted.
    pub fn covered_claim_ids(&self) -> Vec<&'static str> {
        let mut ids: Vec<&'static str> = self.results.iter().flat_map(|r| r.claim_ids.iter().copied()).collect();
        ids.sort();
        ids.dedup();
        ids
    }

    /// Deterministic text.
    pub fn to_text(&self) -> String {
        let mut s = String::new();
        writeln!(s, "alpha_projection_obstruction — PO-000 v{} replicated in Rust from the ooutwire primitives.  AuthorityEffect: None.", self.paper_version).unwrap();
        writeln!(s, "executable_checks_passed: {}", self.executable_checks_passed).unwrap();
        writeln!(s, "refusals_present: {}", self.refusals_present).unwrap();
        writeln!(s, "results: {}", self.results.len()).unwrap();
        writeln!(s, "claim_ids: {}", self.covered_claim_ids().join(", ")).unwrap();
        for (k, r) in self.results.iter().enumerate() {
            writeln!(s).unwrap();
            writeln!(s, "[{k}] {} | {} | {}", r.claim_ids.join(", "), r.evidence_kind.name(), r.verdict.name()).unwrap();
            writeln!(s, "    {}", r.title).unwrap();
            writeln!(s, "    scope: {}", r.statement_scope).unwrap();
            for (key, value) in &r.witness {
                writeln!(s, "    {key} = {value}").unwrap();
            }
            for l in &r.limitations {
                writeln!(s, "    limitation: {l}").unwrap();
            }
        }
        writeln!(s).unwrap();
        writeln!(s, "not claimed:").unwrap();
        for n in NOT_CLAIMED {
            writeln!(s, "  - {n}").unwrap();
        }
        s
    }
}

/// What a green run does not show.
pub const NOT_CLAIMED: &[&str] = &[
    "that Theorem 3.1, Theorem 4.2, Theorem 5.1, or Corollary 5.1.A is proved: every exact result is an instance, every grid audit is bounded by its grid, every float is a replay",
    "that the Python package or the paper is correct: agreement with their pinned numbers is agreement, not verification of their payload (FW-RECEIPT)",
    "that the numerical rail is exact: it is f64 with printed tolerances, and no certificate is built from it",
    "that any refused claim is false: a refusal is a typed disposition, not a verdict",
    "that anything here bears on the frozen derivation tagged sealed-derivation-v1 (3100c4e): the crate reads the paper through the estate's vocabulary; it imports nothing into the derivation and the derivation establishes nothing about the paper",
];

/// Execute every replay and assemble the run.
pub fn run() -> Result<MechanizationRun, String> {
    let (cochain, higher) = cochain_receipts();
    let (d134, d25, d6) = replica_receipts();
    let (a1, e24) = quantum_receipts()?;
    let (f12, f3) = worked_examples_receipts()?;
    let (h_main, h5, h8, h9) = observer_receipts()?;
    let mut results = vec![
        covering_edge_receipt(),
        geometry_receipt(),
        projection_factor_receipt(),
        cochain,
        higher,
        d134,
        d25,
        d6,
        a1,
        e24,
        normalization_receipt(),
        family_receipt(),
        transfer_receipt(),
        f12,
        f3,
        h_main,
        h5,
        h8,
        h9,
    ];
    results.extend(refusals());
    let executable_checks_passed = results.iter().filter(|r| r.verdict != Verdict::Refused).all(|r| r.verdict == Verdict::Pass);
    let refusals_present = results.iter().any(|r| r.verdict == Verdict::Refused);
    Ok(MechanizationRun { paper_version: "6.3", results, executable_checks_passed, refusals_present })
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The Python package's claim universe, as its `REQUIRED_LEDGER_CLAIM_IDS`
    /// covers it, plus the two Lean-only ids computed here and the two
    /// extra dispositions this crate adds.
    const PYTHON_CLAIM_IDS: &[&str] = &[
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "B1", "B2", "B3", "B4", "C1", "C2", "C3", "C4", "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D8a", "E1", "E2", "E3", "E4",
        "E4-commutator", "E4-second", "E5", "E6", "E7", "E8", "E9", "F1", "F2", "F3", "G1", "G2", "G3", "G4", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8", "H9",
    ];

    #[test]
    fn every_executable_replay_passes_and_every_python_claim_is_dispositioned() {
        let run = run().unwrap();
        assert!(run.executable_checks_passed, "{}", run.to_text());
        assert!(run.refusals_present);
        let covered = run.covered_claim_ids();
        for id in PYTHON_CLAIM_IDS {
            assert!(covered.contains(id), "claim {id} has no disposition");
        }
        let extra: Vec<&&str> = covered.iter().filter(|c| !PYTHON_CLAIM_IDS.contains(c)).collect();
        assert_eq!(extra, vec![&"Prop-3B", &"so_k_benchmark"]);
        let computed_here: Vec<&ClaimEvidence> = run.results.iter().filter(|r| r.claim_ids == vec!["H8"] || r.claim_ids == vec!["H9"]).collect();
        assert!(computed_here.iter().all(|r| r.verdict == Verdict::Pass && r.evidence_kind == EvidenceKind::ExactFinite));
    }

    #[test]
    fn the_receipt_matches_the_committed_text_byte_for_byte() {
        let text = run().unwrap().to_text();
        let path = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src").join("alpha_projection_obstruction").join("RECEIPT.txt");
        if std::env::var("PO000_WRITE_RECEIPT").is_ok() {
            std::fs::write(&path, text.as_bytes()).expect("write receipt");
        }
        let committed = std::fs::read_to_string(&path).expect("RECEIPT.txt is committed beside the module").replace("\r\n", "\n");
        assert_eq!(text, committed, "the receipt drifted; regenerate deliberately with PO000_WRITE_RECEIPT=1");
    }

    #[test]
    fn receipt_floats_print_python_style() {
        assert_eq!(receipt_float(2.0), "2.0");
        assert_eq!(receipt_float(0.03), "0.03");
        assert_eq!(receipt_float(1.9999999999999996), "2.0");
        assert_eq!(receipt_float(0.0), "0.0");
        assert_eq!(receipt_float(-220.2816), "-220.2816");
        assert_eq!(receipt_float(5.6843418860808e-14), "5.68434188608e-14");
        assert_eq!(receipt_float(0.00279503008110974), "0.00279503008111");
    }

    #[test]
    fn a_certificate_is_never_built_from_a_float() {
        // The numerical rail's structs carry f64 and booleans only; the
        // exact rails are the only producers of `Certificate`.  This test
        // pins the receipt's claim by inspecting the source of the
        // numerical files for the type name.
        let dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("src").join("alpha_projection_obstruction");
        for file in ["numeric.rs", "quantum_lattice.rs"] {
            let src = std::fs::read_to_string(dir.join(file)).unwrap();
            let body: String = src.lines().filter(|l| !l.trim_start().starts_with("//")).collect::<Vec<_>>().join("\n");
            assert!(!body.contains("Certificate::"), "{file} constructs a Certificate");
        }
    }
}
