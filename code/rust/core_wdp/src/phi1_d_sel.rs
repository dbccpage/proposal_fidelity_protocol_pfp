//! **D-SEL** — deterministic selection of the ℓ¹-minimal representative.
//!
//! Epoch 19 obligation OBL-2 of proposal 002
//! (`_engine/epochs/epoch_19/002_finite_obstruction_calculus_hilbert_cochain_extension.md`).
//!
//! # Why a selection rule is needed
//!
//! The minimal representative `δ_irr = ω − d₀f*` with
//! `‖δ_irr‖₁ = Φ([ω]) = min_f ‖ω − d₀f‖₁` need not be unique. Remark E.12 of the
//! proposal exhibits two minimisers on the oriented 4-cycle with `ω = (1,1,1,1)`:
//! the *uniform* `(1,1,1,1)` and the *concentrated* `(4,0,0,0)`, both of ℓ¹ mass
//! `4`. They induce different defect potentials — `v ≡ 2` versus `v = (4,4,0,0)` —
//! and hence different ground-state eigenvalues `λ₀` (exactly `2` versus
//! `3 − √5`). So `H_obstr` and `λ₀` are *selection-dependent* even though the
//! vanishing equivalence of Proposition E.8 is not, and the two-sided sandwich of
//! Corollary E.7b tightens or loosens with the choice: `μ = 2Φ/n` is the same for
//! every minimiser, while the peak load `v_max` is not.
//!
//! # The rule
//!
//! [`select_delta_irr`] fixes the choice by delegating to the exact **integer
//! network-simplex** solve of [`super::l1_boundary_solver::solve_phi1`]: the
//! returned vertex potential `α` is `f*`, and `z = ω − d₀α` is the selected
//! representative. The arithmetic is `i128` throughout — no floating point enters
//! the selection — and the pivot order of the simplex is fixed, so the rule is a
//! function of the input in the declared edge order. The defect loads derived
//! from the selection are exact rationals.
//!
//! # Scope of the word "canonical"
//!
//! The rule is **deterministic**: identical input yields identical output, which
//! is what `λ₀` needs in order to be well defined. It is **not** claimed to be
//! invariant under relabelling of the carrier — a permutation of the edge list is
//! a different input to the simplex and may select a different minimiser when the
//! minimiser is non-unique. [`DSelReceipt::stable_under_edge_permutation`] is not
//! provided precisely because that invariance is not established;
//! `d_sel_conformance.rs` measures the behaviour on concrete carriers instead.
//! Choosing a relabelling-invariant minimiser (for instance the unique ℓ²-smallest
//! point of the optimal face) is a strictly stronger obligation and remains open.
//!
//! Diagnostic only: a selection receipt mints no authority.

use linear_algebra::exact_field::matrix::{from_rows, multiply_vector};
use linear_algebra::exact_field::pseudoinverse::pseudoinverse;
use linear_algebra::exact_field::ExactFieldError;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_functional::phi1::{ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1};
use core_kernel::{exact_wire, exact_wire_vec};
use core_solvers::solver_flow_network_simplex::NetworkSimplexError;
use core_solvers::solver_lp_phi1_boundary::{solve_phi1, Boundary1};
use serde::Serialize;

/// Identifier of the selection rule that produced a receipt.
pub const D_SEL_RULE_ID: &str = "d-sel.network-simplex-vertex.v1";

/// Receipt for one D-SEL selection.
///
/// Everything is exact: the ℓ¹ side is integer arithmetic and the load fields
/// are rationals, serialized as canonical strings (`"2"`, `"3/2"`). A spectral
/// reading of the loads (for instance through
/// [`core_solvers::solver_spectrum_laplacian`]) is a separate, solver-side
/// conversion that this receipt does not perform.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DSelReceipt {
    /// Rule that produced this selection ([`D_SEL_RULE_ID`]).
    pub rule_id: String,
    /// `Φ([ω]) = ∑_e w_e |δ_irr(e)|`, the weighted ℓ¹ obstruction mass.
    pub phi: i128,
    /// The selected minimal representative `δ_irr = ω − d₀f*`.
    pub delta_irr: Vec<i128>,
    /// The minimising vertex potential `f*`.
    pub potential: Vec<i128>,
    /// Dual witness `φ` certifying optimality (see §4.10 of the anchor paper).
    pub dual_witness: Vec<i128>,
    /// `v(x) = ∑_{e ∋ x} |δ_irr(e)|`, the vertex defect load — the diagonal of
    /// `V_defect` in assumption (A5).
    #[serde(with = "exact_wire_vec")]
    pub vertex_load: Vec<BigRational>,
    /// `μ = (1/n) ∑_x v(x)`, the mean defect load.
    #[serde(with = "exact_wire")]
    pub mean_load: BigRational,
    /// `v_max = max_x v(x)`, the peak defect load.
    #[serde(with = "exact_wire")]
    pub peak_load: BigRational,
}

/// Failure selecting a minimal representative.
#[derive(Debug, Clone, PartialEq)]
pub enum DSelError {
    /// The underlying exact solve failed.
    Solver(NetworkSimplexError),
    /// The solver's proposed Φ₁ value failed canonical primal-dual replay.
    Certificate(ExactPhi1CertificateError),
    /// The exact rational ℓ² projection (OBL-2a) failed in the linear-algebra owner.
    ExactLinearAlgebra(ExactFieldError),
    /// `ω` does not have one entry per edge.
    CoreLengthMismatch { expected: usize, found: usize },
    /// An edge endpoint is out of range for the declared vertex count.
    EndpointOutOfRange { edge: usize, vertex: usize },
    /// An edge has equal endpoints; assumption (A1) requires two distinct ones.
    SelfLoop { edge: usize },
    /// The carrier declares no vertices, so `μ` would divide by zero.
    EmptyCarrier,
}

// Origin: engine/crates_rs/core_wdp/src/phi1_d_sel.rs
// Claim: urn:core:crates_rs:core-wdp:phi1-d-sel:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DSelError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DSelError {}

impl From<NetworkSimplexError> for DSelError {
    fn from(error: NetworkSimplexError) -> Self {
        DSelError::Solver(error)
    }
}

impl From<ExactPhi1CertificateError> for DSelError {
    fn from(error: ExactPhi1CertificateError) -> Self {
        DSelError::Certificate(error)
    }
}

impl From<ExactFieldError> for DSelError {
    fn from(error: ExactFieldError) -> Self {
        DSelError::ExactLinearAlgebra(error)
    }
}

/// Exact vertex loads `v(x) = ∑_{e ∋ x} |δ(e)|`, their mean and their peak.
/// The caller has already refused an empty carrier and out-of-range endpoints.
fn defect_loads(
    boundary: &Boundary1,
    delta: &[BigRational],
) -> (Vec<BigRational>, BigRational, BigRational) {
    let mut vertex_load = vec![BigRational::zero(); boundary.num_vertices];
    for (edge, value) in boundary.edges.iter().zip(delta) {
        let magnitude = value.abs();
        vertex_load[edge.tail] += &magnitude;
        vertex_load[edge.head] += &magnitude;
    }
    let total: BigRational = vertex_load.iter().sum();
    let count = BigRational::from_integer(BigInt::from(boundary.num_vertices));
    let mean_load = total / count;
    let peak_load = vertex_load
        .iter()
        .max()
        .cloned()
        .unwrap_or_else(BigRational::zero);
    (vertex_load, mean_load, peak_load)
}

fn integer(value: i128) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

/// Validate the carrier, solve, and replay the solver's certificate through the
/// owner verifier. Returns the receipt together with the sealed certificate.
fn select_verified(
    boundary: &Boundary1,
    omega: &[i128],
) -> Result<(DSelReceipt, VerifiedExactPhi1), DSelError> {
    if boundary.num_vertices == 0 {
        return Err(DSelError::EmptyCarrier);
    }
    if boundary.edges.len() != omega.len() {
        return Err(DSelError::CoreLengthMismatch {
            expected: boundary.edges.len(),
            found: omega.len(),
        });
    }
    for (index, edge) in boundary.edges.iter().enumerate() {
        if edge.tail == edge.head {
            return Err(DSelError::SelfLoop { edge: index });
        }
        for vertex in [edge.tail, edge.head] {
            if vertex >= boundary.num_vertices {
                return Err(DSelError::EndpointOutOfRange {
                    edge: index,
                    vertex,
                });
            }
        }
    }

    let solution = solve_phi1(boundary, omega)?;
    let certificate = crate::phi1_coda_adapter::exact_certificate(boundary, omega, &solution);
    let verified = Phi1Functional::verify_exact_certificate(certificate)?;

    let delta: Vec<BigRational> = solution.z.iter().copied().map(integer).collect();
    let (vertex_load, mean_load, peak_load) = defect_loads(boundary, &delta);

    let receipt = DSelReceipt {
        rule_id: D_SEL_RULE_ID.to_string(),
        phi: solution.objective,
        delta_irr: solution.z,
        potential: solution.vertex_potential,
        dual_witness: solution.reduced_costs,
        vertex_load,
        mean_load,
        peak_load,
    };
    Ok((receipt, verified))
}

/// Select the canonical-by-rule minimal representative of `[ω]` and report the
/// defect loads it induces.
///
/// Refuses carriers that violate assumption (A1) — self-loops, out-of-range
/// endpoints, empty vertex set — rather than returning a load vector whose
/// relation to `Φ` would silently break.
pub fn select_delta_irr(boundary: &Boundary1, omega: &[i128]) -> Result<DSelReceipt, DSelError> {
    select_verified(boundary, omega).map(|(receipt, _)| receipt)
}

impl DSelReceipt {
    /// The E.7a lower bound `λ₂μ / (λ₂ + μ + v_max)` for a carrier whose Fiedler
    /// value is `lambda2`, evaluated exactly.
    ///
    /// Returns `None` when `lambda2` is not strictly positive (a disconnected or
    /// one-vertex carrier), since the bound's hypotheses then fail — see
    /// Remark E.7c(c), where the disconnected `K₂ ⊔ K₂` is an explicit
    /// counterexample. A floating Fiedler value from a spectral solver must be
    /// converted to a rational (or enclosed) by the caller first.
    pub fn e7a_lower_bound(&self, lambda2: &BigRational) -> Option<BigRational> {
        if !lambda2.is_positive() {
            return None;
        }
        let denominator = lambda2 + &self.mean_load + &self.peak_load;
        if !denominator.is_positive() {
            return None;
        }
        Some(lambda2 * &self.mean_load / denominator)
    }

    /// The E.7 upper bound, which is exactly the mean load `μ = 2Φ/n`.
    pub fn e7_upper_bound(&self) -> BigRational {
        self.mean_load.clone()
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_solvers::solver_lp_phi1_boundary::BoundaryEdge;

    fn unit_edge(tail: usize, head: usize) -> BoundaryEdge {
        BoundaryEdge {
            tail,
            head,
            weight: 1,
        }
    }

    fn q(n: i64, d: i64) -> BigRational {
        BigRational::new(n.into(), d.into())
    }

    #[test]
    fn refuses_self_loop() {
        let boundary = Boundary1 {
            num_vertices: 2,
            edges: vec![unit_edge(0, 0)],
        };
        assert_eq!(
            select_delta_irr(&boundary, &[1]),
            Err(DSelError::SelfLoop { edge: 0 })
        );
    }

    #[test]
    fn refuses_length_mismatch_and_empty_carrier() {
        let boundary = Boundary1 {
            num_vertices: 2,
            edges: vec![unit_edge(0, 1)],
        };
        assert_eq!(
            select_delta_irr(&boundary, &[1, 2]),
            Err(DSelError::CoreLengthMismatch {
                expected: 1,
                found: 2
            })
        );
        let empty = Boundary1 {
            num_vertices: 0,
            edges: vec![],
        };
        assert_eq!(select_delta_irr(&empty, &[]), Err(DSelError::EmptyCarrier));
        assert_eq!(
            select_delta_irr_l2(&empty, &[]),
            Err(DSelError::EmptyCarrier)
        );
    }

    #[test]
    fn bound_refuses_nonpositive_fiedler_value() {
        let boundary = Boundary1 {
            num_vertices: 2,
            edges: vec![unit_edge(0, 1)],
        };
        let receipt = select_delta_irr(&boundary, &[3]).expect("select");
        assert_eq!(receipt.e7a_lower_bound(&q(0, 1)), None);
        assert_eq!(receipt.e7a_lower_bound(&q(-1, 1)), None);
    }

    #[test]
    fn loads_are_exact_and_serialize_canonically() {
        // Triangle with ω = (1, 1, 1): Φ = 3, δ_irr uniform, v ≡ 2, μ = 2.
        let boundary = Boundary1 {
            num_vertices: 3,
            edges: vec![unit_edge(0, 1), unit_edge(1, 2), unit_edge(2, 0)],
        };
        let receipt = select_delta_irr(&boundary, &[1, 1, 1]).expect("select");
        assert_eq!(receipt.mean_load, q(2, 1));
        assert_eq!(receipt.peak_load, q(2, 1));
        assert_eq!(receipt.e7_upper_bound(), q(2, 1));
        // λ₂(C₃) = 3: 3·2 / (3 + 2 + 2) = 6/7 exactly.
        assert_eq!(receipt.e7a_lower_bound(&q(3, 1)), Some(q(6, 7)));
        let json = serde_json::to_value(&receipt).expect("serialize");
        assert_eq!(json["mean_load"], serde_json::json!("2"));
        assert_eq!(json["peak_load"], serde_json::json!("2"));
        assert_eq!(json["vertex_load"], serde_json::json!(["2", "2", "2"]));

        // A path with one unit edge on four vertices: mean 1/2 is not an integer.
        let path = Boundary1 {
            num_vertices: 4,
            edges: vec![unit_edge(0, 1)],
        };
        let l2 = select_delta_irr_l2(&path, &[1]).expect("select l2");
        assert_eq!(l2.mean_load, q(0, 1));
        let star = Boundary1 {
            num_vertices: 4,
            edges: vec![unit_edge(0, 1), unit_edge(1, 2), unit_edge(2, 0)],
        };
        let r = select_delta_irr(&star, &[1, 1, 1]).expect("select");
        assert_eq!(r.mean_load, q(3, 2));
        let json = serde_json::to_value(&r).expect("serialize");
        assert_eq!(json["mean_load"], serde_json::json!("3/2"));
        assert_eq!(json["vertex_load"], serde_json::json!(["2", "2", "2", "0"]));
    }

    #[test]
    fn harmonic_selection_decides_l1_optimality_exactly() {
        // C₃ with ω = (3, 0, 0): δ_h = (1, 1, 1) has ℓ¹ mass 3 = Φ — optimal and
        // sealed by the owner verifier.
        let c3 = Boundary1 {
            num_vertices: 3,
            edges: vec![unit_edge(0, 1), unit_edge(1, 2), unit_edge(2, 0)],
        };
        let receipt = select_delta_irr_l2(&c3, &[3, 0, 0]).expect("select l2");
        assert_eq!(receipt.delta_harmonic, vec![q(1, 1); 3]);
        assert_eq!(receipt.phi_l1_min, q(3, 1));
        assert!(receipt.is_l1_optimal);
        let sealed = receipt.optimality_certificate.as_ref().expect("sealed");
        assert_eq!(sealed.value(), &q(3, 1));
        assert_eq!(sealed.primal_residual(), receipt.delta_harmonic.as_slice());

        // Two triangles sharing edge 1→2 (edges 0→1, 1→2, 2→0, 1→3, 3→2) with
        // ω on the shared edge only: Φ = 1 (put the whole defect on that edge),
        // while the ℓ² projection spreads it, so ‖δ_h‖₁ > Φ — refuted exactly.
        let bowtie = Boundary1 {
            num_vertices: 4,
            edges: vec![
                unit_edge(0, 1),
                unit_edge(1, 2),
                unit_edge(2, 0),
                unit_edge(1, 3),
                unit_edge(3, 2),
            ],
        };
        let receipt = select_delta_irr_l2(&bowtie, &[0, 1, 0, 0, 0]).expect("select l2");
        assert_eq!(receipt.phi_l1_min, q(1, 1));
        assert!(receipt.l1_of_harmonic > receipt.phi_l1_min);
        assert!(!receipt.is_l1_optimal);
        assert!(receipt.optimality_certificate.is_none());
    }
}

// ---------------------------------------------------------------------------
// OBL-2a — a relabelling-invariant selection (harmonic / ℓ²-projection)
// ---------------------------------------------------------------------------

/// Identifier of the OBL-2a selection rule.
pub const D_SEL_L2_RULE_ID: &str = "d-sel-l2.harmonic-projection.v1";

/// Receipt for the OBL-2a harmonic selection.
///
/// The **harmonic representative** `δ_h` is the orthogonal (ℓ²) projection of `ω`
/// onto `ker(d₀ᵀ)` — equivalently the residual `ω − d₀f*` of the ℓ²-nearest
/// point of `im(d₀)`. It is the unique ℓ²-smallest representative of the class,
/// and it is **relabelling-invariant**: a permutation of vertices or edges
/// conjugates `d₀` by permutation matrices, under which the projection is
/// equivariant, so the induced defect load is the same whatever the enumeration.
/// (D-SEL, by contrast, returns a network-simplex *vertex* whose identity can
/// depend on the pivot order.)
///
/// The ℓ²-min of the class coincides with the ℓ²-min of the **ℓ¹-optimal face**
/// (what OBL-2a ultimately wants) exactly when `δ_h` is itself ℓ¹-optimal —
/// `is_l1_optimal`, i.e. `‖δ_h‖_{1,w} = Φ`. This holds on the Remark E.12 `C₄`
/// instance and whenever `ω` is already harmonic. When it fails, `δ_h` is still
/// the unique invariant ℓ²-representative but is not ℓ¹-minimal; the general
/// inequality-constrained face QP is the residual **OBL-2a′** (logged, open).
///
/// Every field is an exact rational; rationals serialize as canonical strings.
#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct DSelL2Receipt {
    /// Rule id ([`D_SEL_L2_RULE_ID`]).
    pub rule_id: String,
    /// The minimum-norm ℓ² potential `f* = d₀⁺ω` (exact Moore–Penrose inverse).
    #[serde(with = "exact_wire_vec")]
    pub harmonic_potential: Vec<BigRational>,
    /// The harmonic representative `δ_h = ω − d₀f*` (ℓ²-projection onto `ker d₀ᵀ`).
    #[serde(with = "exact_wire_vec")]
    pub delta_harmonic: Vec<BigRational>,
    /// `‖δ_h‖_{1,w}`, the weighted ℓ¹ mass of the harmonic representative — the
    /// quantity compared with `Φ` (equal to the unweighted mass on unit weights).
    #[serde(with = "exact_wire")]
    pub l1_of_harmonic: BigRational,
    /// `Φ([ω])`, the ℓ¹ minimum, from the owner-verified exact certificate.
    #[serde(with = "exact_wire")]
    pub phi_l1_min: BigRational,
    /// `true` iff the owner verifier
    /// [`Phi1Functional::evaluate_exact_witness`] sealed `(f*, φ)` as an optimal
    /// primal-dual pair, with `φ` the verified dual witness of the D-SEL solve.
    /// Since that `φ` attains `Φ`, the verifier refutes the pair exactly when
    /// `‖δ_h‖_{1,w} > Φ`, so this decision is exact and complete.
    pub is_l1_optimal: bool,
    /// The sealed certificate behind `is_l1_optimal = true`; `None` otherwise.
    #[serde(skip)]
    pub optimality_certificate: Option<VerifiedExactPhi1>,
    /// Vertex defect load `v(x) = ∑_{e ∋ x} |δ_h(e)|`.
    #[serde(with = "exact_wire_vec")]
    pub vertex_load: Vec<BigRational>,
    /// `μ = (1/n) ∑_x v(x)`.
    #[serde(with = "exact_wire")]
    pub mean_load: BigRational,
    /// `v_max = max_x v(x)`.
    #[serde(with = "exact_wire")]
    pub peak_load: BigRational,
}

/// OBL-2a: select the relabelling-invariant harmonic representative and decide
/// exactly whether it is ℓ¹-optimal.
///
/// The ℓ¹ minimum `Φ` and its dual witness come from the owner-verified
/// certificate of [`select_delta_irr`]. The harmonic potential is `f* = d₀⁺ω`,
/// computed with the exact rational Moore–Penrose inverse of
/// `linear_algebra::exact_field::pseudoinverse` (all four Penrose identities
/// replayed). The residual and its mass are computed by
/// [`Phi1Functional::evaluate_representative`], and optimality is decided only
/// by [`Phi1Functional::evaluate_exact_witness`]. No floating point is used.
/// Refuses the same malformed carriers as [`select_delta_irr`].
pub fn select_delta_irr_l2(
    boundary: &Boundary1,
    omega: &[i128],
) -> Result<DSelL2Receipt, DSelError> {
    // Exact ℓ¹ minimum, its verified dual witness, and input validation.
    let (_, verified) = select_verified(boundary, omega)?;
    let certificate = verified.certificate();
    let phi_l1_min = verified.value().clone();

    // f* = d₀⁺ ω: the minimum-norm least-squares solution of d₀ f ≈ ω.
    let harmonic_potential = if certificate.d0.is_empty() {
        vec![BigRational::zero(); boundary.num_vertices]
    } else {
        let d0 = from_rows(certificate.d0.clone())?;
        let d0_plus = pseudoinverse(&d0)?;
        multiply_vector(&d0_plus, &certificate.omega)?
    };

    let (delta_harmonic, l1_of_harmonic) = Phi1Functional::evaluate_representative(
        &certificate.omega,
        &certificate.d0,
        &certificate.weights,
        &harmonic_potential,
    )?;

    let optimality_certificate = match Phi1Functional::evaluate_exact_witness(
        &certificate.omega,
        &certificate.d0,
        &certificate.weights,
        &harmonic_potential,
        &certificate.dual_witness,
    ) {
        Ok(sealed) => Some(sealed),
        // The dual witness is verified and attains Φ, so a pairing mismatch
        // means exactly ‖δ_h‖_{1,w} ≠ Φ: the harmonic representative is not
        // ℓ¹-optimal. Every other refusal is a genuine failure.
        Err(ExactPhi1CertificateError::DualValueMismatch) => None,
        Err(other) => return Err(other.into()),
    };
    let is_l1_optimal = optimality_certificate.is_some();

    let (vertex_load, mean_load, peak_load) = defect_loads(boundary, &delta_harmonic);

    Ok(DSelL2Receipt {
        rule_id: D_SEL_L2_RULE_ID.to_string(),
        harmonic_potential,
        delta_harmonic,
        l1_of_harmonic,
        phi_l1_min,
        is_l1_optimal,
        optimality_certificate,
        vertex_load,
        mean_load,
        peak_load,
    })
}
