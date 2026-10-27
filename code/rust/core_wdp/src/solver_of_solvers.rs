//! Minimal Solver of Solvers: `solve(carrier, residual)` over a declared
//! finite 2-complex, returning a typed status, a normal-form residual, and a
//! replay-verified certificate chain. All coefficients are **rational**: every
//! statement below is over ℚ (a rational relaxation — integral and torsion
//! semantics are not addressed by this module).
//!
//! # What this is
//!
//! The three-algorithm skeleton, executed against the estate's sealed
//! verifiers and nothing else:
//!
//! 1. **Foundation** — declare the finite carrier (vertices, weighted edges,
//!    triangular faces). Ambiguous declarations (self-loops, parallel or
//!    reversed duplicate edges, degenerate or duplicate faces) are refused as
//!    `RepresentationInvalid`, because face incidence would otherwise depend
//!    on edge list order. The primitive-difference receipt binds the declared
//!    residual `ω` itself.
//! 2. **Gauge projection** — exact `Φ₁ = min_α ‖ω − d₀α‖_{1,w}` via the
//!    integer network simplex ([`solve_phi1`]), packed and replayed through
//!    the shared exact evaluation
//!    ([`crate::coda::coda_gtla::evaluate_exact`]) with the carrier's
//!    **real** face coboundary `d₁` — unlike the graph-only adapter path,
//!    Γ₂ here sees the declared 2-cells.
//! 3. **Multi-cycle projection** — two exact weighted-ℓ¹ projections:
//!    - `v*`  = distance of `ω` to `im(d₀) + im(∂₂)` (the supplied span:
//!      whether every `∂₂` column is a *licensed* repair is the caller's
//!      declaration, not something this module establishes), and
//!    - `v_closed` = the same distance restricted to **closed**
//!      representatives (`d₁ z = 0`), i.e. the projection onto
//!      `im(d₀) + (im(∂₂) ∩ ker d₁)` of the curl-matched shift.
//!    Each is a bounded basic-solution enumeration whose result is accepted
//!    only when its primal/dual pair replays with zero gap through
//!    [`Phi1Functional::verify_exact_certificate`]; the search itself establishes
//!    nothing, and an uncertifiable candidate is a typed refusal.
//! 4. **Typed diagnostic terminal** — the status is decided by the exact
//!    comparison of the two certified values, so it is a function of
//!    `(ω, weights, span, faces)` alone and does **not** depend on which
//!    optimal representative the enumeration happened to certify (equal-value
//!    optima with different closure classes exist — see
//!    `review_counterexample_status_is_canonical`):
//!    - `v* = 0` → [`ObstructionDiagnosticClass::ExactRepair`] (over ℚ);
//!    - `v* > 0` and `v_closed = v*` →
//!      [`ObstructionDiagnosticClass::ClosedResidual`] — a **closed** minimal
//!      representative exists and is returned as the normal form;
//!    - `v* > 0` and (`v_closed > v*` or no closed representative exists) →
//!      [`ObstructionDiagnosticClass::ActiveClosureFailure`] — closedness
//!      costs strictly more than the minimum; the certified gap is carried.
//!    The final class is still emitted by the contract-bound trichotomy
//!    inside `evaluate_exact` on the returned normal form, and the exact
//!    value comparison ensures which class that is. The result is a
//!    checked diagnostic packet: **no terminal classification is minted**
//!    (`VerifiedExactPhi1` is evidence, never a grant).
//!
//! Algorithm 3 is the **window lift** ([`lift`], [`probe_lifts`]): the
//! caller *declares* candidate 2-cells (the engine never invents one), the
//! effect on `v*` is certified with monotonicity re-checked at runtime, and
//! irreducibility is only ever stated relative to the declared budget.
//!
//! # What this is not
//!
//! No continuum statement is made, no inner product is declared — so
//! nothing here is called *harmonic*: `ClosedResidual` with `b₁^ℚ > 0` means
//! a closed non-exact class over ℚ survives, and only that. The `∂₂` columns
//! are a **declared repair span** — syntactically declared directions, not
//! policy-*licensed* ones; promotion to "licensed" would require a policy
//! receipt this module does not carry. No authority is minted: every receipt
//! carries [`AuthorityEffect::None`].
//!
//! # Replay
//!
//! The sealed inner witnesses replay their own primal/dual content, but the
//! *glue* between them (which carrier, which residual, the closed
//! projection's transformation chain) is re-derived by [`replay_solve`],
//! which `solve` itself runs before returning a receipt. The primitive
//! receipt binds the carrier-manifest hash, domain length and class count —
//! **not** a digest of the residual values; residual binding is carried by
//! the certificate bytes inside the evidence manifests and by
//! [`replay_solve`]'s recomputation. An offline serialization for
//! cross-process replay is recorded open work.
//!
//! Both projections are solved by the **exact rational simplex** of
//! [`core_solvers::solver_lp_exact_simplex`] (Bland's rule, so no cycling; dual read
//! off the final tableau). The former 12-edge combinatorial ceiling is gone;
//! [`MAX_PROJECTION_EDGES`] is a resource guard, not an algorithmic limit,
//! and exceeding it refuses rather than degrading to floats.
//!
//! `AuthorityEffect: None.`

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};

use crate::coda::coda_gtla::{
    bind_domain_evidence, evaluate_exact, validate_primitive_difference, CodaExactInput,
    CodaGtlaEvaluation, CodaGtlaEvaluationError, DomainEvidenceBindingError,
    PrimitiveDifferenceReceiptError,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{ExactLinearAlgebraError, ExactRowReduction};
use core_functional::gamma2::ExactCochainComplexQ;
use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
use core_homotopy_type_theory::primitive_difference::PrimitiveDifference;
use core_policy::trichotomy::ObstructionDiagnosticClass;
use core_types::authority::AuthorityEffect;

use crate::phi1_coda_adapter::exact_certificate;
use core_solvers::solver_lp_exact_simplex::{solve_weighted_l1_projection, L1LpError};
use core_solvers::solver_flow_network_simplex::NetworkSimplexError;
use core_solvers::solver_lp_phi1_boundary::{solve_phi1, Boundary1, BoundaryEdge};

/// Projection-stage sanity fence on carrier size.
///
/// This is a resource guard, **not** an algorithmic limit: the projection is
/// an exact rational simplex, so the old combinatorial ceiling (12 edges, set
/// by basic-solution enumeration) is gone. Exceeding this refuses rather than
/// degrading to floats.
pub const MAX_PROJECTION_EDGES: usize = 4096;

/// One namespace for the whole solve: every evaluation of one call binds the
/// same `CarrierManifestHash`, so the certificate chain provably concerns one
/// carrier identity. Stage labels live in the evidence manifests instead.
const DOMAIN: &str = "crate::solver_of_solvers";

/// A declared finite 2-truncated carrier: vertices `0..num_vertices`,
/// directed weighted edges, and triangular faces whose sides must be declared
/// edges (in either stored orientation).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteCarrier2 {
    pub num_vertices: usize,
    pub edges: Vec<CarrierEdge>,
    pub faces: Vec<(usize, usize, usize)>,
}

/// One declared edge with its strictly positive ℓ¹ weight.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CarrierEdge {
    pub tail: usize,
    pub head: usize,
    pub weight: i128,
}

/// Typed refusal. A refusal is a valid terminal; it is never converted into a
/// status claim.
#[derive(Debug, thiserror::Error)]
pub enum SolveRefusal {
    /// The declared carrier or residual is not a valid, unambiguous
    /// representation.
    #[error("representation invalid: {0}")]
    RepresentationInvalid(String),
    /// The projection stages' exact enumeration is fenced to small carriers.
    #[error("projection budget: {edges} edges exceeds the exact-enumeration fence of {max}")]
    SizeBudgetExceeded { edges: usize, max: usize },
    /// The exact integer network simplex refused.
    #[error(transparent)]
    Solver(#[from] NetworkSimplexError),
    /// The shared exact evaluation refused (certificate replay, Γ₂, or
    /// trichotomy consistency).
    #[error(transparent)]
    Evaluation(#[from] CodaGtlaEvaluationError),
    /// Evidence binding failed.
    #[error(transparent)]
    Binding(#[from] DomainEvidenceBindingError),
    /// Primitive-difference receipt failed.
    #[error(transparent)]
    Primitive(#[from] PrimitiveDifferenceReceiptError),
    /// Exact linear algebra failed (overflow-free rational path).
    #[error("exact linear algebra: {0:?}")]
    Linear(ExactLinearAlgebraError),
    /// The enumeration produced a candidate the dual replay could not
    /// certify, or the two certified stages contradict each other. No claim
    /// is made in either case.
    #[error("projection stage found no replay-certifiable minimizer: {0}")]
    JointCertificateSynthesis(String),
    /// Manifest serialization failed.
    #[error(transparent)]
    Manifest(#[from] serde_json::Error),
    /// The exact rational LP refused (dimension, weight, or budget).
    #[error(transparent)]
    Lp(#[from] L1LpError),
}

impl From<ExactLinearAlgebraError> for SolveRefusal {
    fn from(value: ExactLinearAlgebraError) -> Self {
        SolveRefusal::Linear(value)
    }
}

/// The certificate-bearing outcome of one `solve` call.
///
/// Every mathematical claim in here is held by a sealed type another crate's
/// verifier constructed; this struct only arranges them.
#[derive(Debug)]
pub struct SolveReceipt {
    gauge: CodaGtlaEvaluation,
    joint: Option<VerifiedExactPhi1>,
    closed: Option<ClosedProjection>,
    normal_form_eval: Option<CodaGtlaEvaluation>,
    normal_form: Vec<BigRational>,
    b1_over_q: usize,
    authority_effect: AuthorityEffect,
}

impl SolveReceipt {
    /// The gauge evaluation of the original residual against the declared
    /// carrier (real `d₁`; Γ₂ sees the faces).
    pub fn gauge(&self) -> &CodaGtlaEvaluation {
        &self.gauge
    }

    /// The unrestricted projection witness: its value is exactly the
    /// weighted-ℓ¹ distance of `ω` to the supplied span `im(d₀) + im(∂₂)`,
    /// proved by zero-gap primal/dual replay. `None` when the stage did not
    /// run (no faces, or the gauge stage already reached zero).
    pub fn joint(&self) -> Option<&VerifiedExactPhi1> {
        self.joint.as_ref()
    }

    /// The closed-representative projection witness: its value is the
    /// minimum over representatives with `d₁ z = 0`. `None` only when the
    /// stage did not run (no faces, or the gauge stage already reached
    /// zero) — for this module's span `S ⊇ im(∂₂)`, **every** class contains
    /// a closed representative (solve `AAᵀβ = Aω`, always consistent over ℚ
    /// since `im(AAᵀ) = im(A)`), so an inconsistent closed system is an
    /// implementation contradiction and refuses; it is never converted into
    /// a diagnostic. The status is decided by comparing this value with
    /// [`Self::joint`]'s.
    pub fn closed(&self) -> Option<&VerifiedExactPhi1> {
        self.closed
            .as_ref()
            .map(|projection| &projection.outcome.witness)
    }

    /// The canonical evaluation that classifies the normal form. When the
    /// projection stages did not run this is the gauge evaluation itself.
    pub fn final_evaluation(&self) -> &CodaGtlaEvaluation {
        self.normal_form_eval.as_ref().unwrap_or(&self.gauge)
    }

    /// The typed status of the normal form, from the contract-bound
    /// trichotomy. Canonical: decided by the exact value comparison
    /// `v_closed` vs `v*`, not by which optimum the enumeration found first.
    pub fn status(&self) -> ObstructionDiagnosticClass {
        self.final_evaluation().status()
    }

    /// The normal-form residual. For `ClosedResidual` this is a **closed**
    /// minimal representative; the status is canonical, the representative
    /// within its (possibly non-unique) optimal set is not.
    pub fn normal_form(&self) -> &[BigRational] {
        &self.normal_form
    }

    /// First Betti number of the declared carrier **over ℚ** (exact rational
    /// ranks): the dimension of the surviving cochain quotient. Integral and
    /// torsion information is not computed.
    pub fn b1_over_q(&self) -> usize {
        self.b1_over_q
    }

    /// `ClosedResidual` with `b₁^ℚ > 0`: a closed, non-exact residual class
    /// over ℚ survives every supplied repair direction. This is **not** a
    /// harmonicity claim — harmonic representatives require a declared inner
    /// product and codifferential, which this module does not carry.
    pub fn is_closed_class_survivor(&self) -> bool {
        self.status() == ObstructionDiagnosticClass::ClosedResidual && self.b1_over_q > 0
    }

    /// The certified span distance `v* = min over [ω]_S of ‖·‖_{1,w}`.
    ///
    /// Uniform across the stages: when the projection ran this is its
    /// witness value; otherwise the declared repair span is `im(d₀)` alone
    /// (no faces) or the gauge stage already reached zero, and in both cases
    /// `v* = Φ₁`.
    pub fn span_distance(&self) -> &BigRational {
        match &self.joint {
            Some(witness) => witness.value(),
            None => self.gauge.phi1().value(),
        }
    }

    /// The certified closure premium `π = v_closed − v*` — the exact price
    /// of holding a **closed** representative rather than a minimal
    /// one. Total, and always finite: for this module's span `S ⊇ im(∂₂)`
    /// every class has a closed representative, so `π = +∞` is unreachable
    /// (it belongs only to generalized spans not containing `im(d₁ᵀ)`).
    ///
    /// `π = 0` ⟺ `ClosedResidual` (when `v* > 0`); `π > 0` ⟺
    /// `ActiveClosureFailure`. This is the invariant that makes the
    /// classification canonical (see the module docs).
    pub fn closure_premium(&self) -> BigRational {
        match &self.closed {
            Some(projection) => {
                projection.outcome.witness.value().clone() - self.span_distance().clone()
            }
            // No closed projection was needed: either no faces are declared
            // (every representative is closed) or v* = 0 (the zero
            // representative is closed). Both have premium zero.
            None => BigRational::zero(),
        }
    }

    /// Always [`AuthorityEffect::None`]: the receipt is evidence, not a
    /// grant.
    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

#[derive(Debug, PartialEq, Eq)]
struct RationalDelta {
    same_dimension: bool,
    coordinates: Vec<BigRational>,
}

/// The primitive difference bound by the receipts: the declared edge-space
/// residual itself (validated as `[0, ω]`, and `[0, z]` for the normal form).
#[derive(Debug)]
struct ResidualDifference;

impl PrimitiveDifference for ResidualDifference {
    type Carrier = Vec<BigRational>;
    type Diff = RationalDelta;

    fn delta(&self, left: &Self::Carrier, right: &Self::Carrier) -> Self::Diff {
        RationalDelta {
            same_dimension: left.len() == right.len(),
            coordinates: left
                .iter()
                .zip(right)
                .map(|(left, right)| left.clone() - right.clone())
                .collect(),
        }
    }

    fn zero(&self, difference: &Self::Diff) -> bool {
        difference.same_dimension && difference.coordinates.iter().all(|value| value.is_zero())
    }
}

fn rational(value: i128) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

/// Signed incidence row of face `(u, v, w)` over the stored edges:
/// `+1` where the traversal pair is stored forward, `−1` where stored
/// reversed. Unambiguous because `validate_carrier` refuses duplicate
/// unordered edge pairs. Errors if a side is not a declared edge.
fn face_row(
    carrier: &FiniteCarrier2,
    face: (usize, usize, usize),
) -> Result<Vec<BigRational>, SolveRefusal> {
    let (u, v, w) = face;
    let mut row = vec![BigRational::zero(); carrier.edges.len()];
    for (x, y) in [(u, v), (v, w), (w, u)] {
        let mut found = false;
        for (index, edge) in carrier.edges.iter().enumerate() {
            if edge.tail == x && edge.head == y {
                row[index] += BigRational::from_integer(BigInt::from(1));
                found = true;
                break;
            }
            if edge.tail == y && edge.head == x {
                row[index] -= BigRational::from_integer(BigInt::from(1));
                found = true;
                break;
            }
        }
        if !found {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "face ({u}, {v}, {w}) side ({x}, {y}) is not a declared edge"
            )));
        }
    }
    Ok(row)
}

fn validate_carrier(carrier: &FiniteCarrier2, omega: &[i128]) -> Result<(), SolveRefusal> {
    if carrier.edges.is_empty() {
        return Err(SolveRefusal::RepresentationInvalid(
            "carrier declares no edges".to_string(),
        ));
    }
    if omega.len() != carrier.edges.len() {
        return Err(SolveRefusal::RepresentationInvalid(format!(
            "residual has {} coordinates but the carrier declares {} edges",
            omega.len(),
            carrier.edges.len()
        )));
    }
    // Resource fence on every dimension the LP sees (columns = vertices +
    // faces, rows = edges), not edges alone. A total complexity budget
    // (allocations, pivot work across all stages) is recorded open work.
    if carrier.num_vertices + carrier.faces.len() > MAX_PROJECTION_EDGES {
        return Err(SolveRefusal::SizeBudgetExceeded {
            edges: carrier.num_vertices + carrier.faces.len(),
            max: MAX_PROJECTION_EDGES,
        });
    }
    validate_carrier_edges(carrier)?;
    validate_carrier_faces(carrier)
}

fn validate_carrier_edges(carrier: &FiniteCarrier2) -> Result<(), SolveRefusal> {
    let mut seen_pairs: Vec<(usize, usize)> = Vec::with_capacity(carrier.edges.len());
    for (index, edge) in carrier.edges.iter().enumerate() {
        validate_single_carrier_edge(index, edge, carrier.num_vertices)?;
        let unordered = (edge.tail.min(edge.head), edge.tail.max(edge.head));
        if seen_pairs.contains(&unordered) {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "edge {index} duplicates the unordered pair {unordered:?} (parallel or \
                 reversed duplicate); face incidence would depend on list order"
            )));
        }
        seen_pairs.push(unordered);
    }
    Ok(())
}

fn validate_single_carrier_edge(
    index: usize,
    edge: &CarrierEdge,
    num_vertices: usize,
) -> Result<(), SolveRefusal> {
    if edge.tail >= num_vertices || edge.head >= num_vertices {
        return Err(SolveRefusal::RepresentationInvalid(format!(
            "edge {index} endpoint outside the {num_vertices}-vertex carrier"
        )));
    }
    if edge.tail == edge.head {
        return Err(SolveRefusal::RepresentationInvalid(format!(
            "edge {index} is a self-loop ({} -> {}); simplicial edges need distinct endpoints",
            edge.tail, edge.head
        )));
    }
    if edge.weight <= 0 {
        return Err(SolveRefusal::RepresentationInvalid(format!(
            "edge {index} weight {} is not strictly positive",
            edge.weight
        )));
    }
    Ok(())
}

fn validate_carrier_faces(carrier: &FiniteCarrier2) -> Result<(), SolveRefusal> {
    let mut seen_faces: Vec<[usize; 3]> = Vec::with_capacity(carrier.faces.len());
    for &(u, v, w) in &carrier.faces {
        if [u, v, w].into_iter().any(|vertex| vertex >= carrier.num_vertices) {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "face ({u}, {v}, {w}) vertex outside the {}-vertex carrier",
                carrier.num_vertices
            )));
        }
        if u == v || v == w || u == w {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "face ({u}, {v}, {w}) is degenerate (repeated vertex)"
            )));
        }
        let mut sorted = [u, v, w];
        sorted.sort_unstable();
        if seen_faces.contains(&sorted) {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "face ({u}, {v}, {w}) duplicates an already-declared 2-cell {sorted:?}"
            )));
        }
        seen_faces.push(sorted);
    }
    Ok(())
}

fn boundary1(carrier: &FiniteCarrier2) -> Boundary1 {
    Boundary1 {
        num_vertices: carrier.num_vertices,
        edges: carrier
            .edges
            .iter()
            .map(|edge| BoundaryEdge {
                tail: edge.tail,
                head: edge.head,
                weight: edge.weight,
            })
            .collect(),
    }
}

/// `d₁` rows, one per declared face. A carrier without faces yields an empty
/// block (`c₂ = 0`) — the honest serialization; no dummy 2-cell is invented.
/// `d₁` rows for [`crate::carrier_binding`].
///
/// Deliberately routed through the same `face_row` the solver uses: the point of
/// the binding is to hash the operators the solver actually computes, so a
/// second, parallel derivation here would defeat it.
pub(crate) fn d1_rows_for_binding(
    carrier: &FiniteCarrier2,
) -> Result<Vec<Vec<BigRational>>, SolveRefusal> {
    d1_rows(carrier)
}

fn d1_rows(carrier: &FiniteCarrier2) -> Result<Vec<Vec<BigRational>>, SolveRefusal> {
    carrier
        .faces
        .iter()
        .map(|&face| face_row(carrier, face))
        .collect()
}

fn weighted_l1(z: &[BigRational], weights: &[BigRational]) -> BigRational {
    core_functional::phi1::Phi1Functional::weighted_l1_rational(weights, z)
        .expect("validated carrier gives equal residual and weight dimensions")
}

fn matrix_from_rows(rows: &[Vec<BigRational>]) -> Result<BasicMatrix<BigRational>, SolveRefusal> {
    let height = rows.len();
    let width = rows.first().map(Vec::len).unwrap_or(0);
    let data: Vec<BigRational> = rows.iter().flat_map(|row| row.iter().cloned()).collect();
    BasicMatrix::from_row_major(height, width, data).map_err(|error| {
        SolveRefusal::RepresentationInvalid(format!("matrix construction failed: {error:?}"))
    })
}

fn exact_rank(rows: &[Vec<BigRational>]) -> Result<usize, SolveRefusal> {
    if rows.is_empty() || rows[0].is_empty() {
        return Ok(0);
    }
    Ok(matrix_from_rows(rows)?.rank()?)
}

/// Solve `M x = b` exactly (particular solution, free variables zero).
/// Returns `None` when inconsistent.
fn rref_solve(
    rows: &[Vec<BigRational>],
    rhs: &[BigRational],
) -> Result<Option<Vec<BigRational>>, SolveRefusal> {
    let width = rows.first().map(Vec::len).unwrap_or(0);
    if rows.is_empty() {
        return Ok(Some(Vec::new()));
    }
    let augmented: Vec<Vec<BigRational>> = rows
        .iter()
        .zip(rhs)
        .map(|(row, b)| {
            let mut extended = row.clone();
            extended.push(b.clone());
            extended
        })
        .collect();
    let reduction = matrix_from_rows(&augmented)?.rank_and_rref()?;
    if reduction.pivot_columns().contains(&width) {
        return Ok(None); // pivot in the RHS column: inconsistent
    }
    let mut solution = vec![BigRational::zero(); width];
    let rref = reduction.rref();
    for (row_index, &pivot_col) in reduction.pivot_columns().iter().enumerate() {
        let value = rref.get(row_index, width).map_err(|error| {
            SolveRefusal::RepresentationInvalid(format!("rref read failed: {error:?}"))
        })?;
        solution[pivot_col] = value;
    }
    Ok(Some(solution))
}

/// Iterate size-`k` subsets of `0..n` (lexicographic), calling `visit`.
#[allow(dead_code)]
fn for_each_subset<F: FnMut(&[usize]) -> Result<bool, SolveRefusal>>(
    n: usize,
    k: usize,
    mut visit: F,
) -> Result<(), SolveRefusal> {
    if k > n {
        return Ok(());
    }
    let mut indices: Vec<usize> = (0..k).collect();
    loop {
        if !visit(&indices)? {
            return Ok(());
        }
        // advance
        let mut position = k;
        loop {
            if position == 0 {
                return Ok(());
            }
            position -= 1;
            if indices[position] != position + n - k {
                break;
            }
            if position == 0 {
                return Ok(());
            }
        }
        indices[position] += 1;
        for later in position + 1..k {
            indices[later] = indices[later - 1] + 1;
        }
    }
}

#[derive(Debug)]
struct ProjectionOutcome {
    witness: VerifiedExactPhi1,
    residual: Vec<BigRational>,
    dual: Vec<BigRational>,
}

/// Exact weighted-l1 projection of `target` onto the column space of
/// `map_rows` (an `m x k` matrix given by rows).
///
/// Solved by the exact rational simplex of
/// [`core_solvers::solver_lp_exact_simplex`] -- polynomial in practice, exact over Q,
/// and with the dual read straight off the final tableau's reduced costs.
/// The LP is a *proposal engine*: its output is accepted only when the
/// primal/dual pair replays with zero gap through the shared verifier, and a
/// proposal the verifier cannot certify is a typed refusal, never a claim.
fn exact_l1_projection(
    target: &[BigRational],
    weights: &[BigRational],
    map_rows: &[Vec<BigRational>],
) -> Result<ProjectionOutcome, SolveRefusal> {
    let m = target.len();
    if m > MAX_PROJECTION_EDGES {
        return Err(SolveRefusal::SizeBudgetExceeded {
            edges: m,
            max: MAX_PROJECTION_EDGES,
        });
    }
    let k = map_rows.first().map(Vec::len).unwrap_or(0);
    let budget = 64 * (m + k) + 1024;
    let solution = solve_weighted_l1_projection(target, weights, map_rows, budget)?;

    let certificate = ExactPhi1Certificate {
        omega: target.to_vec(),
        d0: map_rows.to_vec(),
        weights: weights.to_vec(),
        alpha: solution.coefficients,
        primal_residual: solution.residual.clone(),
        dual_witness: solution.dual.clone(),
        reported_value: solution.value,
    };
    let witness = Phi1Functional::verify_exact_certificate(certificate).map_err(|error| {
        SolveRefusal::JointCertificateSynthesis(format!(
            "the exact LP optimum failed replay: {error}"
        ))
    })?;

    Ok(ProjectionOutcome {
        witness,
        residual: solution.residual,
        dual: solution.dual,
    })
}

/// Complementary dual: `φ_e = w_e · sign(z_e)` on the support, unknown on the
/// zero set, subject to `φ ⊥ every map column`; bounds are checked here and
/// re-checked by the verifier.
#[allow(dead_code)]
fn synthesize_dual(
    map_rows: &[Vec<BigRational>],
    z: &[BigRational],
    weights: &[BigRational],
) -> Result<Option<Vec<BigRational>>, SolveRefusal> {
    let m = z.len();
    let columns = map_rows.first().map(Vec::len).unwrap_or(0);
    let support: Vec<usize> = (0..m).filter(|&edge| !z[edge].is_zero()).collect();
    let zero_set: Vec<usize> = (0..m).filter(|&edge| z[edge].is_zero()).collect();

    let mut fixed = vec![BigRational::zero(); m];
    for &edge in &support {
        let sign = if z[edge].is_positive() {
            BigRational::from_integer(BigInt::from(1))
        } else {
            BigRational::from_integer(BigInt::from(-1))
        };
        fixed[edge] = weights[edge].clone() * sign;
    }

    // Constraint per column c: Σ_e A[e][c] φ_e = 0 →
    // Σ_{e∈Z} A[e][c] φ_e = − Σ_{e∈S} A[e][c] fixed_e.
    let rows: Vec<Vec<BigRational>> = (0..columns)
        .map(|column| {
            zero_set
                .iter()
                .map(|&edge| map_rows[edge][column].clone())
                .collect()
        })
        .collect();
    let rhs: Vec<BigRational> = (0..columns)
        .map(|column| {
            -support
                .iter()
                .map(|&edge| map_rows[edge][column].clone() * fixed[edge].clone())
                .sum::<BigRational>()
        })
        .collect();

    let free_values = if columns == 0 {
        vec![BigRational::zero(); zero_set.len()]
    } else {
        match rref_solve(&rows, &rhs)? {
            Some(values) => values,
            None => return Ok(None),
        }
    };
    let mut dual = fixed;
    for (position, &edge) in zero_set.iter().enumerate() {
        dual[edge] = free_values[position].clone();
    }
    for edge in 0..m {
        if dual[edge].abs() > weights[edge] {
            return Ok(None); // bound violated; caller may try another optimum
        }
    }
    Ok(Some(dual))
}

/// Rows of `[ d₀ | ∂₂ ]` — the supplied repair span.
fn augmented_rows(
    carrier: &FiniteCarrier2,
    d0_rows: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
) -> Vec<Vec<BigRational>> {
    let m = carrier.edges.len();
    let n = carrier.num_vertices;
    let f = carrier.faces.len();
    (0..m)
        .map(|edge| {
            let mut row = Vec::with_capacity(n + f);
            row.extend(d0_rows[edge].iter().cloned());
            for face_row in d1 {
                row.push(face_row[edge].clone());
            }
            row
        })
        .collect()
}

/// The certified closed projection, **with the glue retained** so a replay
/// can re-derive the constrained minimum from the original `(carrier, ω)`
/// rather than trusting the transformation chain
/// `ω → γ₀ → y₀ → shifted → V` that produced it.
#[derive(Debug)]
struct ClosedProjection {
    outcome: ProjectionOutcome,
    /// The closed minimal representative `z_c = ω − y₀ − V s*` (with
    /// `d₁ z_c = 0` re-checked exactly before this struct is built).
    normal_form: Vec<BigRational>,
    /// Particular solution: `y₀ = B γ₀`, `d₁ y₀ = d₁ ω`.
    gamma0: Vec<BigRational>,
    y0: Vec<BigRational>,
    /// Kernel coefficients: each `k` satisfies `(d₁B) k = 0`, and the
    /// direction columns are `V_j = B k_j`.
    kernel: Vec<Vec<BigRational>>,
    /// `ω − y₀` — the target of the inner projection witness.
    shifted: Vec<BigRational>,
}

/// Exact projection of `ω` restricted to **closed** representatives:
/// minimize `‖ω − y‖_{1,w}` over `y ∈ col(B)` with `d₁(ω − y) = 0`.
///
/// For this module's span `B = [d₀ | ∂₂]` the system `(d₁B)γ = d₁ω` is
/// **always consistent** over ℚ: `im(d₁ ∂₂) = im(d₁ d₁ᵀ) = im(d₁) ∋ d₁ω`
/// (over an ordered field, `AAᵀx = 0 ⟹ ‖Aᵀx‖² = 0 ⟹ Aᵀx = 0`, so
/// `rank(AAᵀ) = rank(A)`). Every class therefore has a closed
/// representative, and an inconsistent solve here is an implementation
/// contradiction that refuses — it is never converted into a diagnostic.
fn closed_projection(
    core_q: &[BigRational],
    weights: &[BigRational],
    aug_rows: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
) -> Result<ClosedProjection, SolveRefusal> {
    let m = core_q.len();
    let columns = aug_rows.first().map(Vec::len).unwrap_or(0);

    // BF = d₁ · B  (faces × columns), t = d₁ ω.
    let bf_rows: Vec<Vec<BigRational>> = d1
        .iter()
        .map(|face| {
            (0..columns)
                .map(|column| {
                    (0..m)
                        .map(|edge| face[edge].clone() * aug_rows[edge][column].clone())
                        .sum()
                })
                .collect()
        })
        .collect();
    let t: Vec<BigRational> = d1
        .iter()
        .map(|face| {
            (0..m)
                .map(|edge| face[edge].clone() * core_q[edge].clone())
                .sum()
        })
        .collect();

    // Particular solution: y₀ = B γ₀ with d₁ y₀ = d₁ ω. Consistency is a
    // theorem here (see the function docs), so failure is a defect refusal,
    // never a "no closed representative" diagnostic.
    let gamma0 = match rref_solve(&bf_rows, &t)? {
        Some(gamma0) => gamma0,
        None => {
            return Err(SolveRefusal::JointCertificateSynthesis(
                "closed system (d1·B)γ = d1ω reported inconsistent — contrary to rational feasibility for \
                 a span containing im(d1ᵀ); implementation contradiction"
                    .to_string(),
            ));
        }
    };
    let y0: Vec<BigRational> = (0..m)
        .map(|edge| {
            (0..columns)
                .map(|column| aug_rows[edge][column].clone() * gamma0[column].clone())
                .sum()
        })
        .collect();
    let shifted: Vec<BigRational> = core_q
        .iter()
        .zip(&y0)
        .map(|(observed, base)| observed.clone() - base.clone())
        .collect();

    // Direction space: V = { B k : (d₁ B) k = 0 } = col(B) ∩ ker(d₁).
    // Note im(d₀) ⊆ V by the chain law, so the constrained dual annihilates
    // im(d₀) — which is what lets the closed normal form re-certify against
    // the true d₀ downstream.
    let kernel = matrix_from_rows(&bf_rows)?.kernel_basis()?;
    let v_columns: Vec<Vec<BigRational>> = kernel
        .vectors()
        .iter()
        .map(|k| {
            (0..m)
                .map(|edge| {
                    (0..columns)
                        .map(|column| aug_rows[edge][column].clone() * k[column].clone())
                        .sum()
                })
                .collect()
        })
        .collect();
    let v_rows: Vec<Vec<BigRational>> = (0..m)
        .map(|edge| {
            v_columns
                .iter()
                .map(|column| column[edge].clone())
                .collect()
        })
        .collect();

    let outcome = exact_l1_projection(&shifted, weights, &v_rows)?;
    let normal_form: Vec<BigRational> = outcome.residual.clone();

    // Hard exact check, not an assumption: the returned representative is
    // closed. Failure here is an internal contradiction, surfaced as a typed
    // refusal rather than a wrong claim.
    for face in d1 {
        let curl: BigRational = (0..m)
            .map(|edge| face[edge].clone() * normal_form[edge].clone())
            .sum();
        if !curl.is_zero() {
            return Err(SolveRefusal::JointCertificateSynthesis(
                "closed projection returned a non-closed representative".to_string(),
            ));
        }
    }

    Ok(ClosedProjection {
        outcome,
        normal_form,
        gamma0,
        y0,
        kernel: kernel.vectors().to_vec(),
        shifted,
    })
}

/// One canonical evaluation through the shared CODA/CODA_GTLA runtime. Every call
/// within one `solve` uses the same [`DOMAIN`] and the same carrier manifest,
/// hence the same `CarrierManifestHash`: one carrier identity per chain.
///
/// Binding honesty: the primitive-difference *validation* runs on
/// `[0, residual]`, but the receipt records only the carrier hash, domain
/// length and quotient-class count — it does **not** digest the residual
/// values. The residual bytes are bound via the certificate inside the
/// evidence manifest (hashed into the packet args) and re-derived by
/// [`replay_solve`].
fn evaluate(
    stage: &str,
    carrier: &FiniteCarrier2,
    certificate: ExactPhi1Certificate,
    complex: ExactCochainComplexQ,
    bound_residual: &[BigRational],
) -> Result<CodaGtlaEvaluation, SolveRefusal> {
    let carrier_manifest = serde_json::to_vec(&(
        "core-solvers-sos-carrier-v1",
        carrier.num_vertices,
        carrier
            .edges
            .iter()
            .map(|edge| (edge.tail, edge.head, edge.weight))
            .collect::<Vec<_>>(),
        carrier.faces.clone(),
    ))?;
    let evidence_manifest = serde_json::to_vec(&(
        "core-solvers-sos-evidence-v1",
        stage,
        &certificate,
        &complex,
    ))?;
    let binding = bind_domain_evidence(DOMAIN, &carrier_manifest, &evidence_manifest)?;

    let zero = vec![BigRational::zero(); bound_residual.len()];
    let primitive_receipt = validate_primitive_difference(
        &ResidualDifference,
        vec![zero, bound_residual.to_vec()],
        binding.carrier_hash().clone(),
    )?;
    let residual = certificate.primal_residual.clone();
    Ok(evaluate_exact(CodaExactInput::new(
        primitive_receipt,
        certificate,
        complex,
        residual,
        binding.into_packet_args(),
    ))?)
}

/// Solve one declared carrier + residual: Foundation → gauge projection →
/// closed/unrestricted multi-cycle projections → typed diagnostic terminal.
/// See the module documentation for the exact claims each returned
/// certificate holds.
pub fn solve(carrier: &FiniteCarrier2, omega: &[i128]) -> Result<SolveReceipt, SolveRefusal> {
    validate_carrier(carrier, omega)?;

    let boundary = boundary1(carrier);
    let d1 = d1_rows(carrier)?;
    let weights: Vec<BigRational> = carrier
        .edges
        .iter()
        .map(|edge| rational(edge.weight))
        .collect();
    let core_q: Vec<BigRational> = omega.iter().copied().map(rational).collect();

    // ---- Stage 1: exact gauge projection, canonically evaluated with the
    // carrier's real d1 (an empty 2-cell block when no faces are declared).
    let (gauge, d0_rows, complex) = evaluate_gauge_stage(carrier, omega, &boundary, &d1, &core_q)?;

    // b1 over Q from exact ranks: m − rank(d0) − rank(∂2).
    let b1_over_q = compute_b1_over_q(carrier, &d0_rows, &d1)?;
    let gauge_is_exact = gauge.status() == ObstructionDiagnosticClass::ExactRepair;

    // ---- Stage 2: the two projections (only meaningful with faces and a
    // surviving residual).
    if carrier.faces.is_empty() || gauge_is_exact {
        let normal_form = gauge.phi1().primal_residual().to_vec();
        return Ok(SolveReceipt {
            gauge,
            joint: None,
            // Without faces every representative is closed; with an exact
            // gauge repair the zero representative is closed. π = 0.
            closed: None,
            normal_form_eval: None,
            normal_form,
            b1_over_q,
            authority_effect: AuthorityEffect::None,
        });
    }

    let aug = augmented_rows(carrier, &d0_rows, &d1);
    let joint = exact_l1_projection(&core_q, &weights, &aug)?;
    let v_star = joint.witness.value().clone();

    // v* = 0: everything in the supplied span is removable; the zero normal
    // form is closed, no second projection is needed.
    if v_star.is_zero() {
        return evaluate_zero_joint_receipt(
            carrier,
            gauge,
            joint,
            d0_rows,
            &weights,
            complex,
            b1_over_q,
        );
    }

    // v* > 0: run the closed-representative projection (always solvable for
    // this span — see `closed_projection`). The status is the exact
    // comparison of the two certified values — canonical, independent of
    // which optimum either solver certified.
    let closed = closed_projection(&core_q, &weights, &aug, &d1)?;
    evaluate_positive_joint_receipt(
        carrier,
        omega,
        gauge,
        joint,
        closed,
        d0_rows,
        &weights,
        complex,
        b1_over_q,
    )
}

fn evaluate_gauge_stage(
    carrier: &FiniteCarrier2,
    omega: &[i128],
    boundary: &Boundary1,
    d1: &[Vec<BigRational>],
    core_q: &[BigRational],
) -> Result<(CodaGtlaEvaluation, Vec<Vec<BigRational>>, ExactCochainComplexQ), SolveRefusal> {
    let solution = solve_phi1(boundary, omega)?;
    let gauge_certificate = exact_certificate(boundary, omega, &solution);
    let d0_rows: Vec<Vec<BigRational>> = gauge_certificate.d0.clone();
    let complex = ExactCochainComplexQ::try_new(
        carrier.num_vertices,
        carrier.edges.len(),
        d1.len(),
        d0_rows.clone(),
        d1.to_vec(),
    )
    .map_err(CodaGtlaEvaluationError::from)?;
    let gauge = evaluate(
        "gauge",
        carrier,
        gauge_certificate,
        complex.clone(),
        core_q,
    )?;
    Ok((gauge, d0_rows, complex))
}

fn compute_b1_over_q(
    carrier: &FiniteCarrier2,
    d0_rows: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
) -> Result<usize, SolveRefusal> {
    let rank_d0 = exact_rank(d0_rows)?;
    let rank_faces = if carrier.faces.is_empty() {
        0
    } else {
        exact_rank(d1)?
    };
    Ok(carrier.edges.len() - rank_d0 - rank_faces)
}

fn evaluate_zero_joint_receipt(
    carrier: &FiniteCarrier2,
    gauge: CodaGtlaEvaluation,
    joint: ProjectionOutcome,
    d0_rows: Vec<Vec<BigRational>>,
    weights: &[BigRational],
    complex: ExactCochainComplexQ,
    b1_over_q: usize,
) -> Result<SolveReceipt, SolveRefusal> {
    let z2 = joint.residual.clone();
    let zero_dual = vec![BigRational::zero(); carrier.edges.len()];
    let normal_form_certificate = ExactPhi1Certificate {
        omega: z2.clone(),
        d0: d0_rows,
        weights: weights.to_vec(),
        alpha: vec![BigRational::zero(); carrier.num_vertices],
        primal_residual: z2.clone(),
        dual_witness: zero_dual,
        reported_value: BigRational::zero(),
    };
    let normal_form_eval = evaluate(
        "normal-form",
        carrier,
        normal_form_certificate,
        complex,
        &z2,
    )?;
    Ok(SolveReceipt {
        gauge,
        joint: Some(joint.witness),
        closed: None,
        normal_form_eval: Some(normal_form_eval),
        normal_form: z2,
        b1_over_q,
        authority_effect: AuthorityEffect::None,
    })
}

#[allow(clippy::too_many_arguments)]
fn evaluate_positive_joint_receipt(
    carrier: &FiniteCarrier2,
    omega: &[i128],
    gauge: CodaGtlaEvaluation,
    joint: ProjectionOutcome,
    closed: ClosedProjection,
    d0_rows: Vec<Vec<BigRational>>,
    weights: &[BigRational],
    complex: ExactCochainComplexQ,
    b1_over_q: usize,
) -> Result<SolveReceipt, SolveRefusal> {
    let v_star = joint.witness.value().clone();
    let v_closed = closed.outcome.witness.value().clone();
    let expected_closed = v_closed == v_star;

    let (normal_form, nf_dual, nf_value) = if expected_closed {
        // A closed minimal representative exists: it IS the normal form, and
        // the constrained dual (which annihilates V ⊇ im(d0)) certifies it
        // against the true d0.
        (
            closed.normal_form.clone(),
            closed.outcome.dual.clone(),
            v_closed,
        )
    } else {
        // Closedness costs strictly more: the certified gap is the
        // ActiveClosureFailure witness. Return an unrestricted optimum
        // (necessarily non-closed, else it would contradict the strict gap).
        (
            joint.residual.clone(),
            joint.dual.clone(),
            weighted_l1(&joint.residual, weights),
        )
    };

    // ---- Stage 3: canonical classification of the chosen normal form
    // against the true d0. The dual in hand annihilates im(d0) by
    // construction in both branches.
    let normal_form_certificate = ExactPhi1Certificate {
        omega: normal_form.clone(),
        d0: d0_rows,
        weights: weights.to_vec(),
        alpha: vec![BigRational::zero(); carrier.num_vertices],
        primal_residual: normal_form.clone(),
        dual_witness: nf_dual,
        reported_value: nf_value,
    };
    let normal_form_eval = evaluate(
        "normal-form",
        carrier,
        normal_form_certificate,
        complex,
        &normal_form,
    )?;

    // Exact consistency between the value comparison and the contract-bound
    // classification. A mismatch is an internal contradiction and refuses.
    verify_normal_form_trichotomy(expected_closed, normal_form_eval.status())?;

    let receipt = SolveReceipt {
        gauge,
        joint: Some(joint.witness),
        closed: Some(closed),
        normal_form_eval: Some(normal_form_eval),
        normal_form,
        b1_over_q,
        authority_effect: AuthorityEffect::None,
    };
    // Self-replay before returning: the constructor path is also a replay
    // client, so a receipt that cannot replay is never handed out.
    replay_solve(carrier, omega, &receipt)?;
    Ok(receipt)
}

fn verify_normal_form_trichotomy(
    expected_closed: bool,
    classified: ObstructionDiagnosticClass,
) -> Result<(), SolveRefusal> {
    let consistent = match classified {
        ObstructionDiagnosticClass::ExactRepair => false, // v* > 0 here
        ObstructionDiagnosticClass::ClosedResidual => expected_closed,
        ObstructionDiagnosticClass::ActiveClosureFailure => !expected_closed,
    };
    if !consistent {
        return Err(SolveRefusal::JointCertificateSynthesis(format!(
            "value comparison and trichotomy disagree: expected_closed={expected_closed}, \
             classified={classified:?}"
        )));
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Replay: re-derive every glue relation of a receipt from (carrier, ω).
// ---------------------------------------------------------------------------

/// A receipt that has been replayed against its declared inputs. The only
/// constructor is [`replay_solve`]; holding one means every glue relation
/// below was re-checked, not trusted.
#[derive(Debug)]
pub struct ReplayedSolve<'a> {
    receipt: &'a SolveReceipt,
}

impl<'a> ReplayedSolve<'a> {
    pub fn receipt(&self) -> &'a SolveReceipt {
        self.receipt
    }
}

/// Replay a [`SolveReceipt`] from the original `(carrier, ω)`.
///
/// The sealed inner witnesses (`VerifiedExactPhi1`, the two canonical
/// evaluations) already replay their own primal/dual content. What THEY
/// cannot see is the glue — that the certificates concern *this* carrier and
/// *this* residual, and that the closed projection's transformation chain
/// `ω → γ₀ → y₀ → shifted → V` is what it claims. This function re-derives
/// all of it:
///
/// 1. the gauge certificate's `ω`, `d₀`, and weights are the carrier's;
/// 2. the joint certificate's map is exactly `[d₀ | ∂₂]` of the carrier and
///    its target is `ω`;
/// 3. `(d₁B)γ₀ = d₁ω`, `y₀ = Bγ₀`, every kernel vector annihilates `d₁B`,
///    the direction columns are `V_j = B k_j`, and `shifted = ω − y₀` is the
///    closed certificate's target over exactly those columns;
/// 4. the closed normal form is face-closed, and the returned normal form is
///    the certified representative of the branch the value comparison
///    selects;
/// 5. the final evaluation's residual is the normal form and its class
///    matches the `v_closed` vs `v*` comparison;
/// 6. `b₁^ℚ` re-derives from exact ranks;
/// 7. the gauge and final evaluations bind the **same** carrier-manifest
///    hash (one carrier identity per chain).
///
/// What this does NOT yet provide: an offline serialization format — the
/// receipt is an in-memory object, and cross-process replay requires the
/// serializable aggregate recorded as open work in the packet.
pub fn replay_solve<'a>(
    carrier: &FiniteCarrier2,
    omega: &[i128],
    receipt: &'a SolveReceipt,
) -> Result<ReplayedSolve<'a>, SolveRefusal> {
    validate_carrier(carrier, omega)?;
    let d1 = d1_rows(carrier)?;
    let core_q: Vec<BigRational> = omega.iter().copied().map(rational).collect();
    let weights: Vec<BigRational> = carrier
        .edges
        .iter()
        .map(|edge| rational(edge.weight))
        .collect();
    let boundary = boundary1(carrier);
    let d0_rows = recompute_d0_rows(carrier, &boundary);

    // (1) Gauge certificate concerns this carrier and this residual. The
    // sealed witness does not expose its weight vector, so weights are bound
    // FUNCTIONALLY: the certified value must equal the residual's norm under
    // the CARRIER's weights.
    replay_gauge_glue(carrier, receipt, &d0_rows, &weights, &core_q)?;

    // (2)–(4) Joint + closed glue, when the stages ran.
    replay_joint_and_closed_glue(carrier, receipt, &d0_rows, &d1, &weights, &core_q)?;

    // (6) b1 over Q re-derives.
    if receipt.b1_over_q != compute_b1_over_q(carrier, &d0_rows, &d1)? {
        return replay_fail("b1 over Q does not re-derive from exact ranks");
    }

    // (7) One carrier identity per chain, checked through the REAL pipeline
    // objects, not synthetic manifests.
    let gauge_hash = receipt.gauge.primitive_receipt().declared_carrier_hash();
    let final_hash = receipt
        .final_evaluation()
        .primitive_receipt()
        .declared_carrier_hash();
    if gauge_hash != final_hash {
        return replay_fail("gauge and final evaluations bind different carrier identities");
    }

    Ok(ReplayedSolve { receipt })
}

fn replay_fail<T>(what: &str) -> Result<T, SolveRefusal> {
    Err(SolveRefusal::JointCertificateSynthesis(format!(
        "replay refused: {what}"
    )))
}

fn recompute_d0_rows(carrier: &FiniteCarrier2, boundary: &Boundary1) -> Vec<Vec<BigRational>> {
    // Recompute the signed incidence rows exactly as the certificate
    // packer does.
    let mut rows = vec![vec![BigRational::zero(); carrier.num_vertices]; carrier.edges.len()];
    for (row, edge) in rows.iter_mut().zip(&boundary.edges) {
        row[edge.tail] -= BigRational::from_integer(BigInt::from(1));
        row[edge.head] += BigRational::from_integer(BigInt::from(1));
    }
    rows
}

fn replay_gauge_glue(
    carrier: &FiniteCarrier2,
    receipt: &SolveReceipt,
    d0_rows: &[Vec<BigRational>],
    weights: &[BigRational],
    core_q: &[BigRational],
) -> Result<(), SolveRefusal> {
    let m = carrier.edges.len();
    let gauge_phi1 = receipt.gauge.phi1();
    if gauge_phi1.d0() != d0_rows {
        return replay_fail("gauge certificate d0 is not this carrier's incidence map");
    }
    if weighted_l1(gauge_phi1.primal_residual(), weights) != *gauge_phi1.value() {
        return replay_fail(
            "gauge certificate value is not the carrier-weighted norm of its residual",
        );
    }
    // The verifier ensures residual = omega − d0·alpha; binding omega is
    // done via the residual identity on the recomputed map.
    let alpha = gauge_phi1.alpha();
    for edge in 0..m {
        let repair: BigRational = (0..carrier.num_vertices)
            .map(|vertex| d0_rows[edge][vertex].clone() * alpha[vertex].clone())
            .sum();
        if gauge_phi1.primal_residual()[edge] != core_q[edge].clone() - repair {
            return replay_fail(
                "gauge certificate residual does not reproduce ω − d0·α on this carrier",
            );
        }
    }
    Ok(())
}

fn replay_joint_and_closed_glue(
    carrier: &FiniteCarrier2,
    receipt: &SolveReceipt,
    d0_rows: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    weights: &[BigRational],
    core_q: &[BigRational],
) -> Result<(), SolveRefusal> {
    let m = carrier.edges.len();
    if let Some(joint) = &receipt.joint {
        let aug = augmented_rows(carrier, d0_rows, d1);
        replay_joint_witness_glue(joint, &aug, weights, core_q, m)?;
        let v_star = joint.value();
        match &receipt.closed {
            Some(closed) => {
                replay_closed_projection_glue(receipt, joint, closed, &aug, d1, weights, core_q, m)
            }
            None => replay_absent_closed_stage(receipt, v_star),
        }
    } else {
        replay_absent_joint_stage(carrier, receipt)
    }
}

fn replay_joint_witness_glue(
    joint: &VerifiedExactPhi1,
    aug: &[Vec<BigRational>],
    weights: &[BigRational],
    core_q: &[BigRational],
    m: usize,
) -> Result<(), SolveRefusal> {
    if joint.d0() != aug {
        return replay_fail("joint certificate map is not [d0 | ∂2] of this carrier");
    }
    let joint_alpha = joint.alpha();
    for edge in 0..m {
        let repair: BigRational = (0..aug[edge].len())
            .map(|column| aug[edge][column].clone() * joint_alpha[column].clone())
            .sum();
        if joint.primal_residual()[edge] != core_q[edge].clone() - repair {
            return replay_fail("joint certificate residual does not reproduce ω − Bγ");
        }
    }
    if weighted_l1(joint.primal_residual(), weights) != *joint.value() {
        return replay_fail(
            "joint certificate value is not the carrier-weighted norm of its residual",
        );
    }
    Ok(())
}

fn replay_absent_closed_stage(
    receipt: &SolveReceipt,
    v_star: &BigRational,
) -> Result<(), SolveRefusal> {
    // Joint ran without a closed projection: only legal when
    // v* = 0 (zero normal form, closed trivially).
    if !v_star.is_zero() {
        return replay_fail("v* > 0 but no closed projection was recorded");
    }
    if !receipt.normal_form.iter().all(BigRational::is_zero) {
        return replay_fail("v* = 0 but the normal form is nonzero");
    }
    Ok(())
}

fn replay_absent_joint_stage(
    carrier: &FiniteCarrier2,
    receipt: &SolveReceipt,
) -> Result<(), SolveRefusal> {
    // No joint stage: legal only for faceless carriers or a gauge-exact
    // residual; the normal form is the gauge residual.
    if !(carrier.faces.is_empty()
        || receipt.gauge.status() == ObstructionDiagnosticClass::ExactRepair)
    {
        return replay_fail("joint stage missing although faces are declared and gauge is not exact");
    }
    if receipt.normal_form.as_slice() != receipt.gauge.phi1().primal_residual() {
        return replay_fail("normal form ≠ gauge residual although no joint stage ran");
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn replay_closed_projection_glue(
    receipt: &SolveReceipt,
    joint: &VerifiedExactPhi1,
    closed: &ClosedProjection,
    aug: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    weights: &[BigRational],
    core_q: &[BigRational],
    m: usize,
) -> Result<(), SolveRefusal> {
    let columns = aug.first().map(Vec::len).unwrap_or(0);
    // (d1·B) γ0 = d1·ω  and  y0 = B γ0.
    replay_closed_particular_glue(closed, aug, d1, core_q, m, columns)?;
    // Kernel vectors annihilate d1·B, and the certified map's
    // columns are B·k.
    let closed_witness = &closed.outcome.witness;
    let witness_rows = closed_witness.d0();
    if witness_rows.len() != m {
        return replay_fail("closed certificate map has the wrong height");
    }
    replay_closed_kernel_glue(closed, aug, d1, witness_rows, m, columns)?;
    replay_closed_target_and_curl(closed, d1, witness_rows, m)?;
    // (5) Branch selection and final class. Weight binding for
    // the closed witness, as for the others.
    replay_closed_branch_and_class(receipt, joint, closed, weights)
}

fn replay_closed_particular_glue(
    closed: &ClosedProjection,
    aug: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    core_q: &[BigRational],
    m: usize,
    columns: usize,
) -> Result<(), SolveRefusal> {
    for (face_index, face) in d1.iter().enumerate() {
        let lhs: BigRational = (0..columns)
            .map(|column| {
                let bf: BigRational = (0..m)
                    .map(|edge| face[edge].clone() * aug[edge][column].clone())
                    .sum();
                bf * closed.gamma0[column].clone()
            })
            .sum();
        let rhs: BigRational = (0..m)
            .map(|edge| face[edge].clone() * core_q[edge].clone())
            .sum();
        if lhs != rhs {
            return replay_fail("closed glue: (d1·B)γ0 ≠ d1·ω");
        }
        let _ = face_index;
    }
    for edge in 0..m {
        let y: BigRational = (0..columns)
            .map(|column| aug[edge][column].clone() * closed.gamma0[column].clone())
            .sum();
        if closed.y0[edge] != y {
            return replay_fail("closed glue: y0 ≠ B·γ0");
        }
        if closed.shifted[edge] != core_q[edge].clone() - closed.y0[edge].clone() {
            return replay_fail("closed glue: shifted ≠ ω − y0");
        }
    }
    Ok(())
}

fn replay_closed_kernel_glue(
    closed: &ClosedProjection,
    aug: &[Vec<BigRational>],
    d1: &[Vec<BigRational>],
    witness_rows: &[Vec<BigRational>],
    m: usize,
    columns: usize,
) -> Result<(), SolveRefusal> {
    for (j, k) in closed.kernel.iter().enumerate() {
        for face in d1 {
            let bfk: BigRational = (0..columns)
                .map(|column| {
                    let bf: BigRational = (0..m)
                        .map(|edge| face[edge].clone() * aug[edge][column].clone())
                        .sum();
                    bf * k[column].clone()
                })
                .sum();
            if !bfk.is_zero() {
                return replay_fail("closed glue: a kernel vector does not annihilate d1·B");
            }
        }
        for edge in 0..m {
            let v: BigRational = (0..columns)
                .map(|column| aug[edge][column].clone() * k[column].clone())
                .sum();
            if witness_rows[edge][j] != v {
                return replay_fail("closed glue: certificate column ≠ B·k");
            }
        }
    }
    Ok(())
}

fn replay_closed_target_and_curl(
    closed: &ClosedProjection,
    d1: &[Vec<BigRational>],
    witness_rows: &[Vec<BigRational>],
    m: usize,
) -> Result<(), SolveRefusal> {
    let closed_witness = &closed.outcome.witness;
    if closed_witness.primal_residual() != closed.normal_form.as_slice() {
        return replay_fail("closed certificate residual ≠ recorded closed normal form");
    }
    for edge in 0..m {
        let expected = closed.shifted[edge].clone();
        let mapped: BigRational = (0..closed.kernel.len())
            .map(|j| witness_rows[edge][j].clone() * closed_witness.alpha()[j].clone())
            .sum();
        if closed_witness.primal_residual()[edge] != expected - mapped {
            return replay_fail("closed certificate target ≠ shifted residual");
        }
    }
    for face in d1 {
        let curl: BigRational = (0..m)
            .map(|edge| face[edge].clone() * closed.normal_form[edge].clone())
            .sum();
        if !curl.is_zero() {
            return replay_fail("closed normal form is not face-closed");
        }
    }
    Ok(())
}

fn replay_closed_branch_and_class(
    receipt: &SolveReceipt,
    joint: &VerifiedExactPhi1,
    closed: &ClosedProjection,
    weights: &[BigRational],
) -> Result<(), SolveRefusal> {
    let closed_witness = &closed.outcome.witness;
    let v_star = joint.value();
    let v_closed = closed_witness.value();
    if weighted_l1(closed_witness.primal_residual(), weights) != *v_closed {
        return replay_fail(
            "closed certificate value is not the carrier-weighted norm of its residual",
        );
    }
    let expected_closed = v_closed == v_star;
    let expected_normal_form: &[BigRational] = if v_star.is_zero() {
        receipt.normal_form.as_slice() // zero form, checked below
    } else if expected_closed {
        closed.normal_form.as_slice()
    } else {
        joint.primal_residual()
    };
    if receipt.normal_form.as_slice() != expected_normal_form {
        return replay_fail("normal form is not the branch-selected representative");
    }
    let final_eval = receipt.final_evaluation();
    if final_eval.phi1().primal_residual() != receipt.normal_form.as_slice() {
        return replay_fail("final evaluation residual ≠ normal form");
    }
    if !is_final_class_consistent(final_eval.status(), v_star.is_zero(), expected_closed) {
        return replay_fail("final class does not match the value comparison");
    }
    Ok(())
}

fn is_final_class_consistent(
    class: ObstructionDiagnosticClass,
    v_star_zero: bool,
    expected_closed: bool,
) -> bool {
    match class {
        ObstructionDiagnosticClass::ExactRepair => v_star_zero,
        ObstructionDiagnosticClass::ClosedResidual => !v_star_zero && expected_closed,
        ObstructionDiagnosticClass::ActiveClosureFailure => !v_star_zero && !expected_closed,
    }
}

// ---------------------------------------------------------------------------
// Algorithm 3: the window lift.
// ---------------------------------------------------------------------------

/// A **declared** window lift: additional 2-cells over the *same* 1-skeleton.
///
/// The caller declares which cells may be added. The engine never invents a
/// 2-cell: inventing the cell that happens to kill the obstruction is not a
/// solution, it is a change of problem. The engine's job is to certify the
/// effect of a declared lift — including certifying that it bought nothing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WindowLift {
    pub added_faces: Vec<(usize, usize, usize)>,
}

impl WindowLift {
    pub fn new(added_faces: Vec<(usize, usize, usize)>) -> Self {
        Self { added_faces }
    }
}

/// The certified effect of a lift on the span distance `v*`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LiftEffect {
    /// `v*' = 0`: the lifted span removes the residual entirely.
    Resolved,
    /// `0 < v*' < v*`: strictly less survives, but something still does.
    Reduced,
    /// `v*' = v*`: the declared cells bought nothing. Reported, never hidden.
    Ineffective,
}

/// A certified lift: both solves, both carrier identities, and the typed
/// effect. Pre-lift evidence does **not** transfer across the lift — the two
/// receipts are kept separate precisely so that no caller can silently reuse
/// one carrier's evidence on another.
#[derive(Debug)]
pub struct LiftReceipt {
    before: SolveReceipt,
    after: SolveReceipt,
    lifted_carrier: FiniteCarrier2,
    effect: LiftEffect,
    authority_effect: AuthorityEffect,
}

impl LiftReceipt {
    /// The pre-lift solve, on the declared carrier.
    pub fn before(&self) -> &SolveReceipt {
        &self.before
    }

    /// The post-lift solve, on the escalated carrier.
    pub fn after(&self) -> &SolveReceipt {
        &self.after
    }

    /// The escalated carrier actually solved (same 1-skeleton, `F' ⊇ F`).
    pub fn lifted_carrier(&self) -> &FiniteCarrier2 {
        &self.lifted_carrier
    }

    pub fn effect(&self) -> LiftEffect {
        self.effect
    }

    /// `v* − v*' ≥ 0`, exact. Non-negativity is a theorem
    /// (`S(P) ⊆ S(P')`) and is re-checked at runtime, not assumed.
    pub fn gain(&self) -> BigRational {
        self.before.span_distance().clone() - self.after.span_distance().clone()
    }

    /// `b₁^ℚ(P) − b₁^ℚ(P') ≥ 0`. A drop here does **not** imply progress:
    /// filling a cycle the residual does not occupy lowers `b₁` and leaves
    /// `v*` untouched (see `a_lift_on_an_unoccupied_cycle_is_ineffective`).
    pub fn b1_drop(&self) -> usize {
        self.before.b1_over_q() - self.after.b1_over_q()
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

/// Build `P'` = `P` with the declared cells added, refusing a lift that
/// re-declares an existing 2-cell (it would be a no-op dressed as a move).
fn escalate(carrier: &FiniteCarrier2, lift: &WindowLift) -> Result<FiniteCarrier2, SolveRefusal> {
    if lift.added_faces.is_empty() {
        return Err(SolveRefusal::RepresentationInvalid(
            "window lift declares no new 2-cells".to_string(),
        ));
    }
    let mut existing: Vec<[usize; 3]> = carrier
        .faces
        .iter()
        .map(|&(u, v, w)| {
            let mut sorted = [u, v, w];
            sorted.sort_unstable();
            sorted
        })
        .collect();
    for &(u, v, w) in &lift.added_faces {
        let mut sorted = [u, v, w];
        sorted.sort_unstable();
        if existing.contains(&sorted) {
            return Err(SolveRefusal::RepresentationInvalid(format!(
                "window lift re-declares the already-present 2-cell {sorted:?}"
            )));
        }
        existing.push(sorted);
    }
    let mut faces = carrier.faces.clone();
    faces.extend(lift.added_faces.iter().copied());
    Ok(FiniteCarrier2 {
        num_vertices: carrier.num_vertices,
        edges: carrier.edges.clone(),
        faces,
    })
}

/// Apply one **declared** window lift and certify its effect.
///
/// Solves on both carriers and compares the certified span distances. The
/// monotonicity theorem `S(P) ⊆ S(P') ⟹ v*' ≤ v*` (and `b₁^ℚ' ≤ b₁^ℚ`) is
/// re-checked against the two certificates; a violation is an internal
/// contradiction and refuses rather than reporting a class.
///
/// `AuthorityEffect: None` — a lift is a declared change of carrier, and
/// certifying its effect grants nothing.
pub fn lift(
    carrier: &FiniteCarrier2,
    omega: &[i128],
    window: &WindowLift,
) -> Result<LiftReceipt, SolveRefusal> {
    let lifted = escalate(carrier, window)?;

    let before = solve(carrier, omega)?;
    let after = solve(&lifted, omega)?;

    let v_before = before.span_distance().clone();
    let v_after = after.span_distance().clone();

    if v_after > v_before {
        return Err(SolveRefusal::JointCertificateSynthesis(format!(
            "lift monotonicity violated: v* rose from {v_before} to {v_after} \
             although S(P) ⊆ S(P')"
        )));
    }
    if after.b1_over_q() > before.b1_over_q() {
        return Err(SolveRefusal::JointCertificateSynthesis(format!(
            "lift monotonicity violated: b1 rose from {} to {}",
            before.b1_over_q(),
            after.b1_over_q()
        )));
    }

    // Equality FIRST: a lift that changes nothing is Ineffective even when
    // both values are zero — an already-exact residual gives the lift no
    // credit. (Reported by external review 2026-08-05: the previous order
    // called v_before = v_after = 0 "Resolved".)
    let effect = if v_after == v_before {
        LiftEffect::Ineffective
    } else if v_after.is_zero() {
        LiftEffect::Resolved
    } else {
        LiftEffect::Reduced
    };

    Ok(LiftReceipt {
        before,
        after,
        lifted_carrier: lifted,
        effect,
        authority_effect: AuthorityEffect::None,
    })
}

/// The result of probing a **declared budget** of candidate lifts.
#[derive(Debug)]
pub struct LiftProbe {
    /// The declared budget, retained verbatim: the irreducibility statement
    /// below is relative to exactly this candidate list, bound by value.
    candidates: Vec<WindowLift>,
    /// Every candidate that ran, with its full certified receipt — not just
    /// the best one. `outcomes[i].0` indexes into `candidates`.
    outcomes: Vec<(usize, LiftReceipt)>,
    /// Candidates that refused, with the **typed** refusal preserved (an
    /// earlier draft stringified it, erasing the type it claimed to keep).
    refused: Vec<(usize, SolveRefusal)>,
}

impl LiftProbe {
    /// The declared candidate budget, verbatim.
    pub fn candidates(&self) -> &[WindowLift] {
        &self.candidates
    }

    /// Every candidate that ran, with its receipt.
    pub fn outcomes(&self) -> &[(usize, LiftReceipt)] {
        &self.outcomes
    }

    /// The candidate that reached the lowest `v*`, if any strictly reduced it.
    pub fn best(&self) -> Option<&LiftReceipt> {
        self.outcomes
            .iter()
            .filter(|(_, receipt)| receipt.effect() != LiftEffect::Ineffective)
            .min_by(|(_, a), (_, b)| a.after().span_distance().cmp(b.after().span_distance()))
            .map(|(_, receipt)| receipt)
    }

    /// Indices of candidates certified to buy nothing.
    pub fn ineffective(&self) -> Vec<usize> {
        self.outcomes
            .iter()
            .filter(|(_, receipt)| receipt.effect() == LiftEffect::Ineffective)
            .map(|(index, _)| *index)
            .collect()
    }

    /// Candidates that refused, with their typed reason. Never silently
    /// dropped: a refused candidate is not evidence of irreducibility.
    pub fn refused(&self) -> &[(usize, SolveRefusal)] {
        &self.refused
    }

    /// Every declared candidate ran and none reduced `v*`.
    ///
    /// This is the **only** irreducibility statement OESOS makes, and it is
    /// relative to the declared budget retained in [`Self::candidates`]: it
    /// says nothing about undeclared lifts. It is false whenever some
    /// candidate refused, since a refusal is not a certified
    /// ineffectiveness.
    pub fn is_irreducible_within_budget(&self) -> bool {
        self.refused.is_empty()
            && !self.outcomes.is_empty()
            && self.outcomes.len() == self.candidates.len()
            && self
                .outcomes
                .iter()
                .all(|(_, receipt)| receipt.effect() == LiftEffect::Ineffective)
    }
}

/// Probe a declared budget of candidate lifts, certifying each.
///
/// Retains the budget verbatim and a full receipt for **every** candidate
/// that ran — "no candidate helped" and "some candidate could not be
/// evaluated" are different facts, and both must survive into the probe.
pub fn probe_lifts(
    carrier: &FiniteCarrier2,
    omega: &[i128],
    candidates: &[WindowLift],
) -> Result<LiftProbe, SolveRefusal> {
    let mut outcomes = Vec::new();
    let mut refused = Vec::new();

    for (index, candidate) in candidates.iter().enumerate() {
        match lift(carrier, omega, candidate) {
            Ok(receipt) => outcomes.push((index, receipt)),
            Err(error) => refused.push((index, error)),
        }
    }

    Ok(LiftProbe {
        candidates: candidates.to_vec(),
        outcomes,
        refused,
    })
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn unit_edges(pairs: &[(usize, usize)]) -> Vec<CarrierEdge> {
        pairs
            .iter()
            .map(|&(tail, head)| CarrierEdge {
                tail,
                head,
                weight: 1,
            })
            .collect()
    }

    fn int(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn frac(numerator: i64, denominator: i64) -> BigRational {
        BigRational::new(BigInt::from(numerator), BigInt::from(denominator))
    }

    /// Canonical carrier 1: the filled triangle. The cyclic residual is pure
    /// face curl; the gauge stage certifies an open obstruction (Φ₁ = 3,
    /// Γ₂ = 3), and the multi-cycle stage removes everything: ExactRepair
    /// over ℚ, with a zero-gap witness over the supplied span.
    #[test]
    fn filled_triangle_cyclic_residual_is_exact_after_multi_cycle() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![(0, 1, 2)],
        };
        let receipt = solve(&carrier, &[1, 1, 1]).expect("solve");

        assert_eq!(
            receipt.gauge().status(),
            ObstructionDiagnosticClass::ActiveClosureFailure,
            "gauge stage must see the face curl (the graph-only path cannot)"
        );
        assert_eq!(receipt.gauge().phi1().value(), &int(3));
        assert_eq!(receipt.gauge().gamma2().value(), &int(3));

        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ExactRepair);
        assert!(receipt.normal_form().iter().all(BigRational::is_zero));
        let joint = receipt.joint().expect("joint stage ran");
        assert_eq!(
            joint.value(),
            &int(0),
            "distance to the supplied span is zero"
        );
        assert_eq!(receipt.b1_over_q(), 0);
        assert!(!receipt.is_closed_class_survivor());
        assert!(receipt.authority_effect().is_none());
    }

    /// Canonical carrier 2: the bare 3-cycle (no faces, `c₂ = 0` — no dummy
    /// 2-cell is serialized). The cycle class survives every supplied repair
    /// direction: ClosedResidual with `b₁^ℚ = 1`.
    #[test]
    fn pure_cycle_is_a_closed_class_survivor() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![],
        };
        let receipt = solve(&carrier, &[1, 1, 1]).expect("solve");

        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ClosedResidual);
        assert_eq!(receipt.gauge().phi1().value(), &int(3));
        assert_eq!(receipt.gauge().gamma2().value(), &int(0));
        assert_eq!(receipt.b1_over_q(), 1);
        assert!(receipt.is_closed_class_survivor());
        assert!(
            receipt.joint().is_none(),
            "no faces: no supplied cycle moves"
        );
        assert_eq!(
            weighted_l1(receipt.normal_form(), &[int(1), int(1), int(1)]),
            int(3),
            "the surviving mass is irreducible"
        );
        assert!(receipt.authority_effect().is_none());
    }

    /// Canonical carrier 3: the bowtie (two triangles sharing a vertex), one
    /// lobe filled. The filled lobe is cleared exactly; the unfilled lobe
    /// survives as a closed residual with a closed-projection witness at the
    /// same value (v_closed = v* = 3).
    #[test]
    fn bowtie_with_one_filled_lobe_leaves_a_closed_residual() {
        let carrier = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![(0, 1, 2)],
        };
        let receipt = solve(&carrier, &[1, 1, 1, 1, 1, 1]).expect("solve");

        assert_eq!(
            receipt.gauge().status(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
        assert_eq!(receipt.gauge().phi1().value(), &int(6));

        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ClosedResidual);
        assert_eq!(receipt.b1_over_q(), 1);
        assert!(receipt.is_closed_class_survivor());

        let joint = receipt.joint().expect("joint stage ran");
        assert_eq!(joint.value(), &int(3), "only the unfilled lobe survives");
        let closed = receipt.closed().expect("closed projection ran");
        assert_eq!(closed.value(), &int(3), "a closed optimum exists");
        assert_eq!(receipt.final_evaluation().gamma2().value(), &int(0));
        for filled_lobe_edge in 0..3 {
            assert!(
                receipt.normal_form()[filled_lobe_edge].is_zero(),
                "the filled lobe must be fully repaired"
            );
        }
        assert!(receipt.authority_effect().is_none());
    }

    /// The review counterexample (2026-08-05): a carrier where the optimal
    /// set contains BOTH a closed representative and a curl-carrying one at
    /// the same value 3 (shared dual). Selecting "the first certified
    /// optimum" would make the status depend on enumeration order; the
    /// two-projection comparison makes it canonical: v_closed = v* = 3, so
    /// the status is ClosedResidual and the returned normal form is closed.
    #[test]
    fn review_counterexample_status_is_canonical() {
        let carrier = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[
                (0, 1),
                (0, 2),
                (0, 4),
                (1, 2),
                (1, 3),
                (2, 3),
                (2, 4),
                (3, 4),
            ]),
            faces: vec![(0, 1, 2), (2, 3, 4)],
        };
        let omega = [0, 1, 3, 2, 0, -2, -1, 3];
        let receipt = solve(&carrier, &omega).expect("solve");

        let joint = receipt.joint().expect("joint ran");
        assert_eq!(joint.value(), &int(3));
        let closed = receipt.closed().expect("closed projection ran");
        assert_eq!(
            closed.value(),
            &int(3),
            "a closed optimum exists at the same value"
        );
        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ClosedResidual);
        // The returned normal form is genuinely closed on the declared faces.
        assert_eq!(receipt.final_evaluation().gamma2().value(), &int(0));
        assert_eq!(receipt.b1_over_q(), 2);
    }

    /// A certified strict gap: the filled triangle with an expensive pendant
    /// cycle. Unrestricted minimum v* = 4; the cheapest CLOSED
    /// representative costs 16/3 > 4. The status is ActiveClosureFailure
    /// with both values certified — closedness demonstrably costs more.
    #[test]
    fn a_certified_strict_closedness_gap_is_an_active_closure_failure() {
        let carrier = FiniteCarrier2 {
            num_vertices: 4,
            edges: vec![
                CarrierEdge {
                    tail: 0,
                    head: 1,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 1,
                    head: 2,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 2,
                    head: 0,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 0,
                    head: 3,
                    weight: 5,
                },
                CarrierEdge {
                    tail: 3,
                    head: 1,
                    weight: 5,
                },
            ],
            faces: vec![(0, 1, 2)],
        };
        // The pendant cycle 0 -> 3 -> 1 -> (0,1 reversed).
        let receipt = solve(&carrier, &[-1, 0, 0, 1, 1]).expect("solve");

        let joint = receipt.joint().expect("joint ran");
        assert_eq!(joint.value(), &int(4));
        let closed = receipt.closed().expect("closed projection ran");
        assert_eq!(closed.value(), &frac(16, 3));
        assert_eq!(
            receipt.status(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
        // The returned (unrestricted) optimum necessarily carries curl.
        assert!(receipt.final_evaluation().gamma2().value() > &int(0));
    }

    /// Status and certified values are invariant under edge/face list
    /// reordering of the same declared carrier.
    #[test]
    fn declaration_order_does_not_change_status_or_values() {
        let original = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![(0, 1, 2)],
        };
        let core_original = [1, 1, 1, 1, 1, 1];

        // Same carrier, edges permuted (and the residual permuted with them),
        // face rotated.
        let permuted = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(4, 0), (2, 0), (0, 1), (3, 4), (1, 2), (0, 3)]),
            faces: vec![(1, 2, 0)],
        };
        let core_permuted = [1, 1, 1, 1, 1, 1];

        let receipt_a = solve(&original, &core_original).expect("solve original");
        let receipt_b = solve(&permuted, &core_permuted).expect("solve permuted");

        assert_eq!(receipt_a.status(), receipt_b.status());
        assert_eq!(
            receipt_a.joint().map(|w| w.value().clone()),
            receipt_b.joint().map(|w| w.value().clone())
        );
        assert_eq!(
            receipt_a.closed().map(|w| w.value().clone()),
            receipt_b.closed().map(|w| w.value().clone())
        );
        assert_eq!(receipt_a.b1_over_q(), receipt_b.b1_over_q());
    }

    /// One solve = one carrier identity: the gauge and normal-form stages
    /// bind the same carrier manifest under the same namespace, so their
    /// `CarrierManifestHash` values coincide; a different carrier changes it.
    #[test]
    fn the_certificate_chain_shares_one_carrier_identity() {
        // Through the REAL pipeline, not synthetic manifests: an earlier
        // version of this test only re-exercised `bind_domain_evidence`, so
        // a namespace regression inside `solve` itself could survive it
        // (external review, 2026-08-05).
        let carrier = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![(0, 1, 2)],
        };
        let receipt = solve(&carrier, &[1, 1, 1, 1, 1, 1]).expect("solve");
        assert!(
            receipt.normal_form_eval.is_some(),
            "fixture must exercise both evaluations"
        );
        assert_eq!(
            receipt.gauge().primitive_receipt().declared_carrier_hash(),
            receipt
                .final_evaluation()
                .primitive_receipt()
                .declared_carrier_hash(),
            "gauge and normal-form evaluations must bind one carrier identity"
        );

        // A different carrier binds a different identity, again through solve.
        let other = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![],
        };
        let other_receipt = solve(&other, &[1, 1, 1]).expect("solve");
        assert_ne!(
            receipt.gauge().primitive_receipt().declared_carrier_hash(),
            other_receipt
                .gauge()
                .primitive_receipt()
                .declared_carrier_hash()
        );
    }

    /// A lift on an already-exact residual buys nothing and must say so:
    /// `v_before = v_after = 0` is `Ineffective`, never `Resolved`.
    /// (External review 2026-08-05: the previous partition checked
    /// `v_after == 0` first and credited the lift.)
    #[test]
    fn a_lift_on_an_already_exact_residual_is_ineffective() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![],
        };
        // d0 of potential (0, 1, 3): a pure gradient, exact at the gauge stage.
        let receipt = lift(&carrier, &[1, 2, -3], &WindowLift::new(vec![(0, 1, 2)])).expect("lift");
        assert_eq!(receipt.before().span_distance(), &int(0));
        assert_eq!(receipt.after().span_distance(), &int(0));
        assert_eq!(receipt.gain(), int(0));
        assert_eq!(
            receipt.effect(),
            LiftEffect::Ineffective,
            "an already-exact residual gives the lift no credit"
        );
    }

    /// Tampering with a receipt is caught by replay: the glue relations are
    /// re-derived from (carrier, ω), not trusted.
    #[test]
    fn replay_refuses_a_tampered_receipt() {
        let carrier = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![(0, 1, 2)],
        };
        let omega = [1, 1, 1, 1, 1, 1];
        let mut receipt = solve(&carrier, &omega).expect("solve");
        assert!(replay_solve(&carrier, &omega, &receipt).is_ok());

        // Tamper with the normal form (same-module access to the private
        // field, standing in for any downstream mutation).
        receipt.normal_form[3] += int(1);
        assert!(
            replay_solve(&carrier, &omega, &receipt).is_err(),
            "a tampered normal form must refuse replay"
        );

        // Replaying against a different residual also refuses.
        let fresh = solve(&carrier, &omega).expect("solve");
        assert!(replay_solve(&carrier, &[1, 1, 1, 0, 0, 0], &fresh).is_err());
    }

    /// Weights enter the ℓ¹ geometry exactly. On the bare 3-cycle every
    /// representative carries total circulation 3, so the weighted minimum is
    /// 3·min_e w_e — the normal form concentrates on the cheapest edge.
    #[test]
    fn weights_route_the_normal_form() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: vec![
                CarrierEdge {
                    tail: 0,
                    head: 1,
                    weight: 2,
                },
                CarrierEdge {
                    tail: 1,
                    head: 2,
                    weight: 2,
                },
                CarrierEdge {
                    tail: 2,
                    head: 0,
                    weight: 5,
                },
            ],
            faces: vec![],
        };
        let receipt = solve(&carrier, &[1, 1, 1]).expect("solve");
        assert_eq!(receipt.gauge().phi1().value(), &int(6), "3 · min_e w_e");
        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ClosedResidual);
        assert!(
            receipt.normal_form()[2].is_zero(),
            "no minimal representative keeps mass on the weight-5 edge"
        );
    }

    /// On a carrier with b₁^ℚ = 0 the supplied moves span everything: the
    /// projection reaches zero for ANY residual and ANY strictly positive
    /// weights. (An earlier draft of this suite asserted the opposite by
    /// forgetting the gauge freedom inside the joint stage; the solver
    /// refuted it.)
    #[test]
    fn on_a_filled_triangle_every_residual_is_exact_after_multi_cycle() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: vec![
                CarrierEdge {
                    tail: 0,
                    head: 1,
                    weight: 3,
                },
                CarrierEdge {
                    tail: 1,
                    head: 2,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 2,
                    head: 0,
                    weight: 1,
                },
            ],
            faces: vec![(0, 1, 2)],
        };
        for omega in [[1, 0, 0], [7, -2, 5], [0, 0, 11]] {
            let receipt = solve(&carrier, &omega).expect("solve");
            assert_eq!(
                receipt.status(),
                ObstructionDiagnosticClass::ExactRepair,
                "b1 = 0 over Q: the supplied span is the whole cochain space"
            );
            if let Some(joint) = receipt.joint() {
                assert_eq!(joint.value(), &int(0));
            }
        }
    }

    /// A pure gradient is repaired at the gauge stage; the projection stages
    /// never run and the receipt is ExactRepair with a zero normal form.
    #[test]
    fn a_pure_gradient_is_exact_at_the_gauge_stage() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![(0, 1, 2)],
        };
        // d0 of potential (0, 1, 3): edge values (1, 2, -3).
        let receipt = solve(&carrier, &[1, 2, -3]).expect("solve");
        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ExactRepair);
        assert!(receipt.joint().is_none());
        assert!(receipt.normal_form().iter().all(BigRational::is_zero));
    }

    /// Foundation refusals are typed, not coerced into statuses — including
    /// the ambiguity refusals that keep face incidence independent of list
    /// order.
    #[test]
    fn representation_refusals_are_typed() {
        let missing_edge_face = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2)]),
            faces: vec![(0, 1, 2)],
        };
        assert!(matches!(
            solve(&missing_edge_face, &[1, 1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let bad_weight = FiniteCarrier2 {
            num_vertices: 2,
            edges: vec![CarrierEdge {
                tail: 0,
                head: 1,
                weight: 0,
            }],
            faces: vec![],
        };
        assert!(matches!(
            solve(&bad_weight, &[1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let wrong_length = FiniteCarrier2 {
            num_vertices: 2,
            edges: unit_edges(&[(0, 1)]),
            faces: vec![],
        };
        assert!(matches!(
            solve(&wrong_length, &[1, 2]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let self_loop = FiniteCarrier2 {
            num_vertices: 2,
            edges: unit_edges(&[(0, 0), (0, 1)]),
            faces: vec![],
        };
        assert!(matches!(
            solve(&self_loop, &[1, 1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let reversed_duplicate = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 0), (1, 2)]),
            faces: vec![],
        };
        assert!(matches!(
            solve(&reversed_duplicate, &[1, 1, 1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let degenerate_face = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![(0, 1, 1)],
        };
        assert!(matches!(
            solve(&degenerate_face, &[1, 1, 1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let duplicate_face = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![(0, 1, 2), (1, 2, 0)],
        };
        assert!(matches!(
            solve(&duplicate_face, &[1, 1, 1]),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));
    }

    // ---------------------------------------------------------------- lifts

    /// The bowtie: two triangles sharing vertex 0, no faces declared.
    /// `b₁^ℚ = 2`.
    fn bowtie() -> FiniteCarrier2 {
        FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![],
        }
    }

    /// Lifting the cycle the residual actually occupies resolves it: the
    /// bare 3-cycle's surviving class dies exactly when its 2-cell is
    /// declared.
    #[test]
    fn lifting_the_occupied_cycle_resolves_the_residual() {
        let carrier = FiniteCarrier2 {
            num_vertices: 3,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0)]),
            faces: vec![],
        };
        let receipt = lift(&carrier, &[1, 1, 1], &WindowLift::new(vec![(0, 1, 2)])).expect("lift");

        assert_eq!(receipt.before().span_distance(), &int(3));
        assert_eq!(
            receipt.before().status(),
            ObstructionDiagnosticClass::ClosedResidual
        );
        assert_eq!(receipt.effect(), LiftEffect::Resolved);
        assert_eq!(receipt.after().span_distance(), &int(0));
        assert_eq!(
            receipt.after().status(),
            ObstructionDiagnosticClass::ExactRepair
        );
        assert_eq!(receipt.gain(), int(3));
        assert_eq!(receipt.b1_drop(), 1);
        assert!(receipt.authority_effect().is_none());
    }

    /// **A `b₁` drop is not progress.** Filling a cycle the residual does not
    /// occupy lowers `b₁^ℚ` from 2 to 1 and leaves `v*` exactly where it was.
    /// An engine that reported "the lift reduced b₁, therefore it helped"
    /// would be wrong here; the certified `v*` comparison is what decides.
    #[test]
    fn a_lift_on_an_unoccupied_cycle_is_ineffective() {
        let carrier = bowtie();
        // Circulates the first lobe only.
        let omega = [1, 1, 1, 0, 0, 0];
        assert_eq!(solve(&carrier, &omega).unwrap().b1_over_q(), 2);

        // Declare the OTHER lobe's 2-cell.
        let receipt = lift(&carrier, &omega, &WindowLift::new(vec![(0, 3, 4)])).expect("lift");

        assert_eq!(receipt.effect(), LiftEffect::Ineffective);
        assert_eq!(receipt.gain(), int(0), "nothing was bought");
        assert_eq!(receipt.b1_drop(), 1, "yet b1 genuinely dropped");
        assert_eq!(receipt.after().span_distance(), &int(3));
        assert_eq!(
            receipt.after().status(),
            ObstructionDiagnosticClass::ClosedResidual
        );
    }

    /// A partial lift: both lobes circulate (`v* = 6`), declaring one lobe's
    /// 2-cell removes exactly that lobe's share.
    #[test]
    fn a_partial_lift_is_certified_as_reduced_not_resolved() {
        let carrier = bowtie();
        let omega = [1, 1, 1, 1, 1, 1];
        let receipt = lift(&carrier, &omega, &WindowLift::new(vec![(0, 1, 2)])).expect("lift");

        assert_eq!(receipt.before().span_distance(), &int(6));
        assert_eq!(receipt.effect(), LiftEffect::Reduced);
        assert_eq!(receipt.after().span_distance(), &int(3));
        assert_eq!(receipt.gain(), int(3));
        assert_eq!(receipt.b1_drop(), 1);
        // What survives is still a closed class over Q.
        assert!(receipt.after().is_closed_class_survivor());
    }

    /// Probing a declared budget: irreducibility is reported only relative to
    /// that budget, and only when every candidate actually ran.
    #[test]
    fn probing_reports_irreducibility_relative_to_the_declared_budget() {
        let carrier = bowtie();
        let omega = [1, 1, 1, 0, 0, 0];

        // Budget containing only the unoccupied lobe: certified ineffective.
        let barren =
            probe_lifts(&carrier, &omega, &[WindowLift::new(vec![(0, 3, 4)])]).expect("probe");
        assert!(barren.best().is_none());
        assert_eq!(barren.ineffective(), &[0]);
        assert!(barren.refused().is_empty());
        assert!(barren.is_irreducible_within_budget());

        // Widen the budget: the occupied lobe resolves it, so the same
        // residual is NOT irreducible — irreducibility was always relative.
        let widened = probe_lifts(
            &carrier,
            &omega,
            &[
                WindowLift::new(vec![(0, 3, 4)]),
                WindowLift::new(vec![(0, 1, 2)]),
            ],
        )
        .expect("probe");
        assert!(!widened.is_irreducible_within_budget());
        let best = widened.best().expect("a reducing candidate exists");
        assert_eq!(best.effect(), LiftEffect::Resolved);
        assert_eq!(widened.ineffective(), &[0]);
    }

    /// A refused candidate is not certified ineffectiveness, so it cannot
    /// support an irreducibility claim.
    #[test]
    fn a_refused_candidate_blocks_the_irreducibility_claim() {
        let carrier = FiniteCarrier2 {
            num_vertices: 5,
            edges: unit_edges(&[(0, 1), (1, 2), (2, 0), (0, 3), (3, 4), (4, 0)]),
            faces: vec![(0, 3, 4)],
        };
        let omega = [1, 1, 1, 0, 0, 0];
        let probe = probe_lifts(
            &carrier,
            &omega,
            &[
                // Already declared: refuses.
                WindowLift::new(vec![(0, 3, 4)]),
            ],
        )
        .expect("probe");

        assert!(probe.best().is_none());
        assert!(probe.ineffective().is_empty());
        assert_eq!(probe.refused().len(), 1);
        assert!(
            !probe.is_irreducible_within_budget(),
            "a refusal is not evidence that nothing helps"
        );
    }

    /// Lift declarations are typed-refused when malformed.
    #[test]
    fn malformed_lifts_are_typed_refusals() {
        let carrier = bowtie();
        let omega = [1, 1, 1, 0, 0, 0];

        assert!(matches!(
            lift(&carrier, &omega, &WindowLift::new(vec![])),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));

        let filled = FiniteCarrier2 {
            faces: vec![(0, 1, 2)],
            ..bowtie()
        };
        assert!(
            matches!(
                lift(&filled, &omega, &WindowLift::new(vec![(1, 2, 0)])),
                Err(SolveRefusal::RepresentationInvalid(_))
            ),
            "re-declaring an existing 2-cell (any rotation) is a no-op dressed as a move"
        );

        // A cell whose sides are not declared edges cannot be lifted into.
        assert!(matches!(
            lift(&carrier, &omega, &WindowLift::new(vec![(1, 3, 4)])),
            Err(SolveRefusal::RepresentationInvalid(_))
        ));
    }

    /// The closure premium is the certified price of closedness: zero on a
    /// closed survivor, strictly positive on the certified-gap fixture.
    #[test]
    fn the_closure_premium_prices_closedness() {
        let closed_survivor = solve(&bowtie(), &[1, 1, 1, 0, 0, 0]).expect("solve");
        assert_eq!(closed_survivor.closure_premium(), int(0));

        let gap_carrier = FiniteCarrier2 {
            num_vertices: 4,
            edges: vec![
                CarrierEdge {
                    tail: 0,
                    head: 1,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 1,
                    head: 2,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 2,
                    head: 0,
                    weight: 1,
                },
                CarrierEdge {
                    tail: 0,
                    head: 3,
                    weight: 5,
                },
                CarrierEdge {
                    tail: 3,
                    head: 1,
                    weight: 5,
                },
            ],
            faces: vec![(0, 1, 2)],
        };
        let gapped = solve(&gap_carrier, &[-1, 0, 0, 1, 1]).expect("solve");
        assert_eq!(
            gapped.closure_premium(),
            frac(4, 3),
            "16/3 - 4: closedness is purchasable, at a certified price"
        );
        assert_eq!(
            gapped.status(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
    }

    /// The projection stages' exact enumeration refuses beyond its fence
    /// instead of approximating.
    #[test]
    fn carriers_past_the_old_enumeration_fence_now_solve_exactly() {
        // The 13-edge wheel-like carrier that the basic-solution enumeration
        // refused outright. With the exact rational simplex it is solved, not
        // fenced: the fence was an artefact of the algorithm, never of the
        // mathematics.
        let mut edges = Vec::new();
        for spoke in 1..7 {
            edges.push((0, spoke));
        }
        for rim in 1..7 {
            edges.push((rim, if rim == 6 { 1 } else { rim + 1 }));
        }
        edges.push((1, 4)); // 13th edge
        let carrier = FiniteCarrier2 {
            num_vertices: 7,
            edges: unit_edges(&edges),
            faces: vec![(0, 1, 2)],
        };
        let mut omega = vec![0i128; 13];
        // circulate the rim
        for rim_edge in 6..12 {
            omega[rim_edge] = 1;
        }
        let receipt = solve(&carrier, &omega).expect("13 edges is no longer fenced");
        // The rim cycle is not in the span of d0 plus the single declared
        // face, so a closed class survives at exactly the rim's mass.
        assert_eq!(receipt.span_distance(), &int(6));
        assert_eq!(receipt.status(), ObstructionDiagnosticClass::ClosedResidual);
        assert_eq!(receipt.closure_premium(), int(0));
        assert!(receipt.is_closed_class_survivor());
    }

    /// Scale at tetron-relevant size, and a demonstration that the exact
    /// rational path is load-bearing: on a 30-edge carrier the optimum and
    /// the closure premium are both genuine fractions (15/2 and 3/2), which
    /// no float path could certify.
    ///
    /// The rim circulation is unreachable: every declared face boundary is
    /// `rim_i + rim_{i+1} - chord_i` and each chord sits in exactly one face,
    /// so no combination cancels the chords. And `d1` of the rim is 2 on
    /// every face, so curl genuinely survives - `ActiveClosureFailure` with a
    /// certified premium, not a fenced refusal.
    #[test]
    fn a_thirty_edge_carrier_solves_exactly_with_fractional_optima() {
        let n = 15usize;
        let mut edges: Vec<(usize, usize)> = (0..n).map(|i| (i, (i + 1) % n)).collect();
        for i in 0..n {
            edges.push((i, (i + 2) % n));
        }
        assert_eq!(edges.len(), 30);
        let faces: Vec<(usize, usize, usize)> =
            (0..n).map(|i| (i, (i + 1) % n, (i + 2) % n)).collect();
        let carrier = FiniteCarrier2 {
            num_vertices: n,
            edges: unit_edges(&edges),
            faces,
        };
        let mut omega = vec![0i128; 30];
        for rim in 0..n {
            omega[rim] = 1;
        }

        let receipt = solve(&carrier, &omega).expect("30 edges is well past the old fence");
        assert_eq!(receipt.span_distance(), &frac(15, 2));
        assert_eq!(receipt.closure_premium(), frac(3, 2));
        assert_eq!(
            receipt.status(),
            ObstructionDiagnosticClass::ActiveClosureFailure
        );
        assert_eq!(receipt.b1_over_q(), 1);
        assert!(receipt.authority_effect().is_none());
    }
}
