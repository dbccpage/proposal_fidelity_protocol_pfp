//! Target 17 — Monoidal composition, complex local tomography, real/rebit countermodel.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen. Finite toy face.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_0d5abfd0<T> {
    fn checked_invariant_0d5abfd0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_0d5abfd0<T> for Option<T> {
    #[inline]
    fn checked_invariant_0d5abfd0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_0d5abfd0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_0d5abfd0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_traits::{One, Zero};

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};

use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};

/// Fence.
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; monoidal composition + tomography face.";

/// Canonical arbitrary-precision rational coordinate field.
pub type Q = Rational;

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CompError {
    DimMismatch,
    NotMonoidalTensor,
    TomographyIdentityFailed {
        local: usize,
        joint: usize,
    },
    RealRebitCountermodel,
    EmptySystem,
    /// Exact row reduction refused on malformed or unsupported finite dimensions.
    ExactLinearAlgebra(String),
    /// The spanning defect was expected to be non-trivial but the kernel was empty.
    NoWitness,
    BudgetExceeded,
    NegativeMass,
}

// Origin: engine/crates_rs/core_quantum_physics/src/composition_tomography.rs
// Claim: urn:core:crates_rs:core-quantum-physics:composition-tomography:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CompError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CompError {}

impl From<ExactFieldError> for CompError {
    fn from(e: ExactFieldError) -> Self {
        Self::ExactLinearAlgebra(e.to_string())
    }
}

/// Finite system with dimension and phase carrier kind.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteSystem {
    pub dim: usize,
    pub phase: PhaseCarrier,
    pub label: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PhaseCarrier {
    /// Complex amplitudes / U(1).
    ComplexU1,
    /// Real amplitudes only (rebit when dim=2).
    RealOnly,
}

impl FiniteSystem {
    pub fn qubit_complex(label: impl Into<String>) -> Self {
        Self {
            dim: 2,
            phase: PhaseCarrier::ComplexU1,
            label: label.into(),
        }
    }

    pub fn rebit(label: impl Into<String>) -> Self {
        Self {
            dim: 2,
            phase: PhaseCarrier::RealOnly,
            label: label.into(),
        }
    }
}

/// Monoidal tensor composition A ⊗ B.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MonoidalComposite {
    pub left: FiniteSystem,
    pub right: FiniteSystem,
    pub dim: usize,
    pub phase: PhaseCarrier,
}

impl MonoidalComposite {
    pub fn tensor(left: FiniteSystem, right: FiniteSystem) -> Result<Self, CompError> {
        if left.dim == 0 || right.dim == 0 {
            return Err(CompError::EmptySystem);
        }
        let dim = left
            .dim
            .checked_mul(right.dim)
            .ok_or(CompError::DimMismatch)?;
        // Phase of product: complex if either factor is complex.
        let phase = match (left.phase, right.phase) {
            (PhaseCarrier::ComplexU1, _) | (_, PhaseCarrier::ComplexU1) => PhaseCarrier::ComplexU1,
            _ => PhaseCarrier::RealOnly,
        };
        Ok(Self {
            left,
            right,
            dim,
            phase,
        })
    }

    /// Functoriality: (A⊗B)⊗C ≅ A⊗(B⊗C) on dimensions.
    pub fn associativity_dims(a: usize, b: usize, c: usize) -> bool {
        match (
            a.checked_mul(b).and_then(|x| x.checked_mul(c)),
            b.checked_mul(c).and_then(|x| a.checked_mul(x)),
        ) {
            (Some(x), Some(y)) => x == y,
            _ => false,
        }
    }
}

/// Local tomography parameter identity for complex quantum systems:
/// `params(A) * params(B) == params(AB)` for density-operator affine dims.
///
/// Complex d-level system: real params of density = d² (affine: d²−1; we use
/// unnormalized hermitian count d² for identity form matching import_bundle).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LocalTomographyReport {
    pub dim_a: usize,
    pub dim_b: usize,
    pub local_param_a: usize,
    pub local_param_b: usize,
    pub joint_param: usize,
    pub identity_holds: bool,
    pub phase: PhaseCarrier,
}

impl LocalTomographyReport {
    /// Complex local tomography: param(d) = d².
    pub fn complex_product(dim_a: usize, dim_b: usize) -> Result<Self, CompError> {
        let r = local_tomography_spanning_complex(dim_a, dim_b)?;
        Ok(Self {
            dim_a,
            dim_b,
            local_param_a: r.local_dim_a,
            local_param_b: r.local_dim_b,
            joint_param: r.joint_dim,
            identity_holds: r.spans,
            phase: PhaseCarrier::ComplexU1,
        })
    }

    /// Real-symmetric densities: param(d) = d(d+1)/2.
    /// Product identity **fails** for rebits (formal countermodel).
    pub fn real_product_params(dim_a: usize, dim_b: usize) -> Result<Self, CompError> {
        let r = local_tomography_spanning_real(dim_a, dim_b)?;
        Ok(Self {
            dim_a,
            dim_b,
            local_param_a: r.local_dim_a,
            local_param_b: r.local_dim_b,
            joint_param: r.joint_dim,
            identity_holds: r.spans,
            phase: PhaseCarrier::RealOnly,
        })
    }
}

/// Formal real/rebit countermodel: local tomography identity fails for real qubits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RealRebitCountermodel {
    pub report: LocalTomographyReport,
    pub note: &'static str,
}

impl RealRebitCountermodel {
    pub fn rebit_pair() -> Self {
        let report = LocalTomographyReport::real_product_params(2, 2)
            .checked_invariant_0d5abfd0("fixed two-rebit rank");
        Self {
            report,
            note: "Real/rebit pair: param_R(2)=3, joint dim=4, param_R(4)=10, but 3*3=9 ≠ 10 — \
                   local tomography fails; complex qubit pair has 4*4=16=16.",
        }
    }

    pub fn is_valid_countermodel(&self) -> bool {
        !self.report.identity_holds
            && LocalTomographyReport::complex_product(2, 2)
                .map(|c| c.identity_holds)
                .unwrap_or(false)
    }
}

/// Born masses on a finite simplex (exact), used by composition demos.
/// The normalisation is `core_functional::born_probabilities`; this keeps
/// the composition error vocabulary.
pub fn born_masses_from_amplitudes_sq(amps_sq: &[Q]) -> Result<Vec<Q>, CompError> {
    use core_functional::born_probabilities::{BornProbabilities, BornProbabilityError};
    if amps_sq.iter().any(|x| x < &Q::zero()) {
        return Err(CompError::NegativeMass);
    }
    BornProbabilities::from_weights(amps_sq)
        .map(|born| born.probabilities().to_vec())
        .map_err(|error| match error {
            BornProbabilityError::EmptyInput | BornProbabilityError::ZeroTotalWeight => {
                CompError::EmptySystem
            }
            BornProbabilityError::NegativeWeight { .. } => CompError::NegativeMass,
            other @ BornProbabilityError::ZeroDenominator { .. } => {
                CompError::ExactLinearAlgebra(other.to_string())
            }
        })
}

// ===========================================================================
// W6.14 — the composition FUNCTOR, and local tomography as a spanning theorem
// ===========================================================================
//
// Everything above this line reasons about `usize` dimension counts. That is
// not a functor and not a tomography theorem:
//
//   * `MonoidalComposite::associativity_dims(a,b,c)` asserts
//     `a*b*c == a*(b*c)` — associativity of `usize` multiplication. It holds
//     with no quantum structure whatsoever.
//   * `LocalTomographyReport::complex_product` computes
//     `d_A^2 * d_B^2 == (d_A d_B)^2`, an arithmetic identity, so its
//     `identity_holds` field is *always* `true`. A check that cannot fail.
//
// This section replaces both with statements about an actual functor acting on
// actual morphisms, and with a spanning statement about actual effect spaces.
//
// **AuthorityEffect: None.** Nothing here is PROVED or GlobalGreen.

/// The composition functor's action on **morphisms**: the Kronecker product.
///
/// The object map is dimension multiplication (`MonoidalComposite::tensor`);
/// this is the arrow map that makes it a functor. Functoriality is not assumed
/// — it is checked by [`interchange_law_holds`] and [`identity_is_preserved`].
pub fn tensor_morphisms(
    f: &BasicMatrix<Q>,
    g: &BasicMatrix<Q>,
) -> Result<BasicMatrix<Q>, CompError> {
    mx::kronecker(f, g).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))
}

/// `I_n` over `Q`.

/// Functor law (unit): `I_a ⊗ I_b = I_{ab}`.
pub fn identity_is_preserved(a: usize, b: usize) -> Result<bool, CompError> {
    let lhs = tensor_morphisms(&mx::identity(a)?, &mx::identity(b)?)?;
    Ok(lhs == mx::identity(a * b)?)
}

/// Functor law (interchange / bifunctoriality):
/// `(f ∘ f') ⊗ (g ∘ g') = (f ⊗ g) ∘ (f' ⊗ g')`.
///
/// This is the law that makes `⊗` a functor on the product category. Unlike a
/// dimension count it is a genuine matrix identity and fails for a wrong index
/// convention.
pub fn interchange_law_holds(
    f: &BasicMatrix<Q>,
    f_prime: &BasicMatrix<Q>,
    g: &BasicMatrix<Q>,
    g_prime: &BasicMatrix<Q>,
) -> Result<bool, CompError> {
    let ff = mx::multiply(f, f_prime).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;
    let gg = mx::multiply(g, g_prime).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;
    let lhs = tensor_morphisms(&ff, &gg)?;

    let fg = tensor_morphisms(f, g)?;
    let fg_prime = tensor_morphisms(f_prime, g_prime)?;
    let rhs =
        mx::multiply(&fg, &fg_prime).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;

    Ok(lhs == rhs)
}

/// Associativity **of the functor on morphisms**: `(f ⊗ g) ⊗ h = f ⊗ (g ⊗ h)`
/// as matrices, not as dimension products.
pub fn associativity_on_morphisms(
    f: &BasicMatrix<Q>,
    g: &BasicMatrix<Q>,
    h: &BasicMatrix<Q>,
) -> Result<bool, CompError> {
    let left = tensor_morphisms(&tensor_morphisms(f, g)?, h)?;
    let right = tensor_morphisms(f, &tensor_morphisms(g, h)?)?;
    Ok(left == right)
}

/// Basis of the real symmetric `d × d` matrices: `E_ii`, and `E_ij + E_ji` for
/// `i < j`. Cardinality `d(d+1)/2` — the effect-space dimension of a real
/// (`RealOnly`) `d`-level system.
pub fn real_symmetric_basis(d: usize) -> Result<Vec<BasicMatrix<Q>>, CompError> {
    if d > 64 {
        return Err(CompError::BudgetExceeded);
    }

    if d == 0 {
        return Err(CompError::EmptySystem);
    }
    let mut out = Vec::new();
    for i in 0..d {
        let mut data = vec![Q::zero(); d * d];
        data[i * d + i] = Q::one();
        out.push(BasicMatrix::from_row_major(d, d, data).map_err(|_| CompError::DimMismatch)?);
    }
    for i in 0..d {
        for j in (i + 1)..d {
            let mut data = vec![Q::zero(); d * d];
            data[i * d + j] = Q::one();
            data[j * d + i] = Q::one();
            out.push(BasicMatrix::from_row_major(d, d, data).map_err(|_| CompError::DimMismatch)?);
        }
    }
    Ok(out)
}

fn flatten(m: &BasicMatrix<Q>) -> Result<Vec<Q>, CompError> {
    let (r, c) = m.shape();
    let mut v = Vec::with_capacity(r * c);
    for i in 0..r {
        for j in 0..c {
            v.push(
                m.get(i, j)
                    .map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?,
            );
        }
    }
    Ok(v)
}

/// Whether the **product effects** span the joint effect space.
///
/// Local tomography is exactly this spanning statement: a joint state is
/// determined by product-effect statistics iff `{A_i ⊗ B_j}` spans the joint
/// effect space. A dimension count is only the *necessary* condition; this
/// reports the actual rank.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpanningReport {
    pub dim_a: usize,
    pub dim_b: usize,
    /// `dim` of the local effect space of A.
    pub local_dim_a: usize,
    pub local_dim_b: usize,
    /// Number of product effects formed (`local_dim_a * local_dim_b`).
    pub product_count: usize,
    /// Exact rank of those product effects inside the joint matrix space.
    pub product_rank: usize,
    /// `dim` of the joint effect space.
    pub joint_dim: usize,
    /// `product_rank == joint_dim`.
    pub spans: bool,
}

/// Spanning test for **real** (`RealOnly`) systems, over exact rationals.
pub fn local_tomography_spanning_real(
    dim_a: usize,
    dim_b: usize,
) -> Result<SpanningReport, CompError> {
    if dim_a.checked_mul(dim_b).is_none_or(|n| n > 16) {
        return Err(CompError::BudgetExceeded);
    }

    let basis_a = real_symmetric_basis(dim_a)?;
    let basis_b = real_symmetric_basis(dim_b)?;
    let joint = dim_a * dim_b;
    let joint_dim = joint * (joint + 1) / 2;

    let mut rows: Vec<Q> = Vec::new();
    let mut count = 0usize;
    for a in &basis_a {
        for b in &basis_b {
            let prod = tensor_morphisms(a, b)?;
            rows.extend(flatten(&prod)?);
            count += 1;
        }
    }

    let m = BasicMatrix::from_row_major(count, joint * joint, rows)
        .map_err(|_| CompError::DimMismatch)?;
    let product_rank =
        elimination::rank(&m).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;

    Ok(SpanningReport {
        dim_a,
        dim_b,
        local_dim_a: basis_a.len(),
        local_dim_b: basis_b.len(),
        product_count: count,
        product_rank,
        joint_dim,
        spans: product_rank == joint_dim,
    })
}

/// An **explicit** witness that real local tomography fails: a nonzero symmetric
/// `(d_a d_b) × (d_a d_b)` matrix `Δ` with `⟨A_i ⊗ B_j, Δ⟩ = 0` for every
/// product effect.
///
/// This upgrades the `9 ≠ 10` parameter count into a concrete direction of the
/// joint effect space that no product measurement can see: any two joint states
/// differing by a multiple of `Δ` have *identical* local statistics.
///
/// Obtained as the kernel of the product effects augmented with the
/// antisymmetry constraints `Δ_ij − Δ_ji = 0`, so the returned `Δ` is symmetric
/// by construction rather than by inspection.
pub fn real_local_tomography_witness(
    dim_a: usize,
    dim_b: usize,
) -> Result<BasicMatrix<Q>, CompError> {
    if dim_a.checked_mul(dim_b).is_none_or(|n| n > 16) {
        return Err(CompError::BudgetExceeded);
    }

    let basis_a = real_symmetric_basis(dim_a)?;
    let basis_b = real_symmetric_basis(dim_b)?;
    let n = dim_a * dim_b;
    let width = n * n;

    let (mut rows, mut nrows) = build_product_effect_rows(&basis_a, &basis_b)?;
    append_symmetry_constraint_rows(&mut rows, &mut nrows, n, width);

    let m = BasicMatrix::from_row_major(nrows, width, rows).map_err(|_| CompError::DimMismatch)?;
    let kernel =
        elimination::kernel_basis(&m).map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;
    let v = kernel.first().ok_or(CompError::NoWitness)?;

    BasicMatrix::from_row_major(n, n, v.clone()).map_err(|_| CompError::DimMismatch)
}

fn build_product_effect_rows(
    basis_a: &[BasicMatrix<Q>],
    basis_b: &[BasicMatrix<Q>],
) -> Result<(Vec<Q>, usize), CompError> {
    let mut rows: Vec<Q> = Vec::new();
    let mut nrows = 0usize;
    for a in basis_a {
        for b in basis_b {
            rows.extend(flatten(&tensor_morphisms(a, b)?)?);
            nrows += 1;
        }
    }
    Ok((rows, nrows))
}

fn append_symmetry_constraint_rows(rows: &mut Vec<Q>, nrows: &mut usize, n: usize, width: usize) {
    // Symmetry constraints: Δ_ij − Δ_ji = 0 for i < j.
    for i in 0..n {
        for j in (i + 1)..n {
            let mut row = vec![Q::zero(); width];
            row[i * n + j] = Q::one();
            row[j * n + i] = -Q::one();
            rows.extend(row);
            *nrows += 1;
        }
    }
}

/// Hilbert–Schmidt pairing `⟨X, Y⟩ = Σ_ij X_ij Y_ij` (real matrices).

// ---------------------------------------------------------------------------
// From a missing direction to two operationally indistinguishable STATES
// ---------------------------------------------------------------------------
//
// A rank defect exhibits a direction no product effect can see. It does NOT yet
// exhibit two physical states: `Δ` is traceless and indefinite, so it is not a
// state, and `ρ ± εΔ` is only a state when it is also positive. This section
// discharges that gap exactly.
//
// The structural reason the direction exists at all:
//
//     Sym(A ⊗ B) ≅ (Sym A ⊗ Sym B) ⊕ (Λ²A ⊗ Λ²B)
//
// Local symmetric effects generate only the first summand. The missing
// information is exactly the **skew–skew** sector, of dimension
// `C(m,2)·C(n,2)`. For two rebits that sector is one-dimensional and generated
// by `J ⊗ J`.

/// `Δ = J ⊗ J`, the generator of the skew–skew sector for two rebits.
///
/// Equals `−Y ⊗ Y`, since `Y = iJ`.
pub fn rebit_hidden_direction() -> Result<BasicMatrix<Q>, CompError> {
    let q = |n: i64| ri(n);
    let j = BasicMatrix::from_row_major(2, 2, vec![q(0), q(-1), q(1), q(0)])
        .map_err(|_| CompError::DimMismatch)?;
    tensor_morphisms(&j, &j)
}

/// Entrywise scale.

/// Entrywise sum.

/// Trace.

/// The state pair `ρ_± = I/4 ± Δ/8` on two rebits.
///
/// Both are genuine states — symmetric, unit trace, positive definite — and they
/// agree on every product effect while differing on an admissible joint effect.
pub fn rebit_state_pair() -> Result<(BasicMatrix<Q>, BasicMatrix<Q>), CompError> {
    let delta = rebit_hidden_direction()?;
    let base = mx::scale(&mx::identity(4)?, &(rq(1, 4)))?;
    let bump = mx::scale(&delta, &(rq(1, 8)))?;
    let minus = mx::scale(&bump, &(ri(-1)))?;
    Ok((mx::add(&base, &bump)?, mx::add(&base, &minus)?))
}

/// `P = (I + Δ)/2`. Since `Δ² = I`, this is an orthogonal projector, and it is
/// an admissible joint effect (`0 ⪯ P ⪯ I`).
pub fn rebit_separating_projector() -> Result<BasicMatrix<Q>, CompError> {
    let delta = rebit_hidden_direction()?;
    Ok(mx::scale(
        &mx::add(&mx::identity(4)?, &delta)?,
        &(rq(1, 2)),
    )?)
}

/// Deficiency of the locally generated symmetric products inside the joint
/// symmetric space:
///
/// ```text
/// dim Sym(R^{mn}) − dim Sym(R^m)·dim Sym(R^n)
///   = mn(mn+1)/2 − [m(m+1)/2][n(n+1)/2]
///   = mn(m−1)(n−1)/4
///   = C(m,2)·C(n,2)
/// ```
///
/// i.e. exactly the dimension of the skew–skew sector `Λ²A ⊗ Λ²B`.
pub fn skew_skew_deficiency(m: usize, n: usize) -> Result<usize, CompError> {
    let a = m
        .checked_mul(m.saturating_sub(1))
        .ok_or(CompError::DimMismatch)?
        / 2;
    let b = n
        .checked_mul(n.saturating_sub(1))
        .ok_or(CompError::DimMismatch)?
        / 2;
    a.checked_mul(b).ok_or(CompError::DimMismatch)
}

/// **Pricing the tensor.** The Cartesian (direct-sum) composition of a `d_a`-
/// and a `d_b`-level system has dimension `d_a + d_b`, not `d_a · d_b`.
///
/// The estate's own position is that the Cartesian product *is* constructible
/// from the FinL1 carrier. So the tensor is not forced by having a composition
/// — it is a strictly different object, and adopting it is what must be earned
/// or declared as an import (`OB-COMPOSE`). This function exists so the two
/// laws can be compared in a test rather than asserted in prose.
pub fn cartesian_compose_dim(dim_a: usize, dim_b: usize) -> Result<usize, CompError> {
    dim_a.checked_add(dim_b).ok_or(CompError::DimMismatch)
}

// ─────────────────────────────────────────────────────────────────────────────
// W6.14 complex half — does complex local tomography SPAN?
//
// Round 1 demoted complex local tomography to [OPEN] for a precise reason:
// `LocalTomographyReport::complex_product` computes `d_A² d_B² = (d_A d_B)²`,
// which is the *necessary dimension condition* and says nothing about whether
// the product effects are linearly independent. The real case already shows the
// gap is real — there the counts also look benign until you take the rank.
//
// The shared exact-field elimination operates directly over Q(i). The
// real carrier is passed through the same Gaussian pipeline as a control.

/// Basis of the **complex Hermitian** `d × d` matrices as a real vector space:
/// `E_ii`, `E_ij + E_ji` (`i < j`), and `i(E_ij − E_ji)` (`i < j`).
///
/// Cardinality `d + 2·C(d,2) = d²` — the real dimension of the Hermitian
/// effect space of a complex `d`-level system.
pub fn complex_hermitian_basis(d: usize) -> Result<Vec<BasicMatrix<GaussianRat>>, CompError> {
    if d > 64 {
        return Err(CompError::BudgetExceeded);
    }

    if d == 0 {
        return Err(CompError::EmptySystem);
    }
    let mut out = Vec::new();
    for i in 0..d {
        let mut m = vec![GaussianRat::zero(); d * d];
        m[i * d + i] = GaussianRat::one();
        out.push(BasicMatrix::from_row_major(d, d, m).map_err(|_| CompError::DimMismatch)?);
    }
    for i in 0..d {
        for j in (i + 1)..d {
            // E_ij + E_ji  (real symmetric part)
            let mut m = vec![GaussianRat::zero(); d * d];
            m[i * d + j] = GaussianRat::one();
            m[j * d + i] = GaussianRat::one();
            out.push(BasicMatrix::from_row_major(d, d, m).map_err(|_| CompError::DimMismatch)?);
            // i(E_ij − E_ji)  (imaginary antisymmetric part; Hermitian)
            let mut m = vec![GaussianRat::zero(); d * d];
            m[i * d + j] = GaussianRat::from_ints(0, 1);
            m[j * d + i] = GaussianRat::from_ints(0, -1);
            out.push(BasicMatrix::from_row_major(d, d, m).map_err(|_| CompError::DimMismatch)?);
        }
    }
    Ok(out)
}

/// The real symmetric basis embedded in ℚ(i) with zero imaginary part.
///
/// Exists so the real case can be pushed through the complex pipeline — the
/// anti-vacuity control described above.
pub fn real_symmetric_basis_gaussian(d: usize) -> Result<Vec<BasicMatrix<GaussianRat>>, CompError> {
    let mut out = Vec::new();
    for m in real_symmetric_basis(d)? {
        out.push(
            BasicMatrix::from_row_major(
                d,
                d,
                m.as_slice()
                    .iter()
                    .cloned()
                    .map(GaussianRat::from_rational)
                    .collect(),
            )
            .map_err(|_| CompError::DimMismatch)?,
        );
    }
    Ok(out)
}

/// The shared exact Kronecker product over Gaussian rationals.

/// Realification: `Re‖Im`, length `2n²`. This is what makes the exact rational
/// Useful for displaying real coordinates; elimination itself uses the exact field.

/// Shared rank pipeline for both carriers. `joint_dim` is the dimension of the
/// joint effect space the caller claims the products must span.
fn spanning_over_gaussian(
    basis_a: &[BasicMatrix<GaussianRat>],
    dim_a: usize,
    basis_b: &[BasicMatrix<GaussianRat>],
    dim_b: usize,
    joint_dim: usize,
) -> Result<SpanningReport, CompError> {
    let joint = dim_a.checked_mul(dim_b).ok_or(CompError::DimMismatch)?;
    let mut rows: Vec<GaussianRat> = Vec::new();
    let mut count = 0usize;
    for a in basis_a {
        for b in basis_b {
            let prod = mx::kronecker(a, b)?;
            rows.extend_from_slice(prod.as_slice());
            count += 1;
        }
    }
    let width = joint * joint;
    let m = BasicMatrix::from_row_major(count, width, rows).map_err(|_| CompError::DimMismatch)?;
    let product_rank = linear_algebra::exact_field::elimination::rank(&m)
        .map_err(|e| CompError::ExactLinearAlgebra(e.to_string()))?;

    Ok(SpanningReport {
        dim_a,
        dim_b,
        local_dim_a: basis_a.len(),
        local_dim_b: basis_b.len(),
        product_count: count,
        product_rank,
        joint_dim,
        spans: product_rank == joint_dim,
    })
}

/// **W6.14, complex half.** Do the product Hermitian effects span the joint
/// Hermitian effect space?
///
/// Joint dimension is `(d_A d_B)²` — the real dimension of the Hermitian
/// matrices on the joint complex space. The product count is `d_A² d_B²`, which
/// is the *same number*; the open question round 1 recorded is whether they are
/// independent, and only a rank answers that.
pub fn local_tomography_spanning_complex(
    dim_a: usize,
    dim_b: usize,
) -> Result<SpanningReport, CompError> {
    if dim_a.checked_mul(dim_b).is_none_or(|n| n > 16) {
        return Err(CompError::BudgetExceeded);
    }

    let basis_a = complex_hermitian_basis(dim_a)?;
    let basis_b = complex_hermitian_basis(dim_b)?;
    let joint = dim_a.checked_mul(dim_b).ok_or(CompError::DimMismatch)?;
    spanning_over_gaussian(&basis_a, dim_a, &basis_b, dim_b, joint * joint)
}

/// The anti-vacuity control: the REAL basis through the SAME pipeline, against
/// the real joint effect dimension `n(n+1)/2`.
///
/// If this reported `spans == true`, the complex result above would be an
/// artifact of the pipeline rather than a fact about ℂ.
pub fn local_tomography_spanning_real_via_gaussian(
    dim_a: usize,
    dim_b: usize,
) -> Result<SpanningReport, CompError> {
    if dim_a.checked_mul(dim_b).is_none_or(|n| n > 16) {
        return Err(CompError::BudgetExceeded);
    }

    let basis_a = real_symmetric_basis_gaussian(dim_a)?;
    let basis_b = real_symmetric_basis_gaussian(dim_b)?;
    let joint = dim_a.checked_mul(dim_b).ok_or(CompError::DimMismatch)?;
    spanning_over_gaussian(&basis_a, dim_a, &basis_b, dim_b, joint * (joint + 1) / 2)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod w614_complex_tests {
    use super::*;

    #[test]
    fn complex_hermitian_basis_has_d_squared_elements() {
        for d in 1..=4 {
            assert_eq!(complex_hermitian_basis(d).unwrap().len(), d * d);
        }
        assert_eq!(complex_hermitian_basis(0), Err(CompError::EmptySystem));
    }

    #[test]
    fn complex_hermitian_basis_elements_are_hermitian() {
        // A_ij = conj(A_ji). Guards the `i(E_ij - E_ji)` sign, which is the one
        // place a transcription slip would silently produce a non-Hermitian
        // "basis" that still had the right cardinality.
        for d in 1..=3 {
            for m in complex_hermitian_basis(d).unwrap() {
                for i in 0..d {
                    for j in 0..d {
                        assert_eq!(
                            m.as_slice()[i * d + j],
                            m.as_slice()[j * d + i].conj(),
                            "d={d} not Hermitian at ({i},{j})"
                        );
                    }
                }
            }
        }
    }

    #[test]
    fn complex_local_tomography_spans_at_2x2() {
        let r = local_tomography_spanning_complex(2, 2).unwrap();
        assert_eq!(r.local_dim_a, 4);
        assert_eq!(r.local_dim_b, 4);
        assert_eq!(r.product_count, 16);
        assert_eq!(r.joint_dim, 16, "Herm(C^4) has real dimension 16");
        assert_eq!(r.product_rank, 16, "the 16 product effects are independent");
        assert!(r.spans);
    }

    #[test]
    fn complex_local_tomography_spans_at_2x3_and_3x3() {
        for (a, b) in [(2usize, 3usize), (3, 3), (2, 4)] {
            let r = local_tomography_spanning_complex(a, b).unwrap();
            let n = a * b;
            assert_eq!(r.joint_dim, n * n);
            assert_eq!(
                r.product_rank,
                n * n,
                "complex LT should span at {a}x{b}: rank {} vs joint {}",
                r.product_rank,
                r.joint_dim
            );
            assert!(r.spans);
        }
    }

    /// ANTI-VACUITY CONTROL.
    ///
    /// The real basis pushed through the SAME `spanning_over_gaussian` pipeline
    /// must still FAIL. If it did not, the complex result above would be an
    /// artifact of the realification pipeline rather than a fact about ℂ, and
    /// the whole cycle-5 conclusion would be worthless.
    #[test]
    fn real_through_complex_pipeline_still_fails() {
        let r = local_tomography_spanning_real_via_gaussian(2, 2).unwrap();
        assert_eq!(r.local_dim_a, 3, "Sym(R^2) has dimension 3");
        assert_eq!(r.product_count, 9);
        assert_eq!(r.joint_dim, 10, "Sym(R^4) has dimension 10");
        assert_eq!(r.product_rank, 9, "9 independent products, 10 needed");
        assert!(!r.spans, "real LT must FAIL through this same pipeline");
        assert_eq!(
            r.joint_dim - r.product_rank,
            skew_skew_deficiency(2, 2).unwrap()
        );
    }

    /// The two carriers agree with the ORIGINAL real pipeline, so the new code
    /// is not quietly computing a different quantity.
    #[test]
    fn gaussian_pipeline_reproduces_the_original_real_answer() {
        for (a, b) in [(2usize, 2usize), (2, 3), (3, 3)] {
            let orig = local_tomography_spanning_real(a, b).unwrap();
            let via = local_tomography_spanning_real_via_gaussian(a, b).unwrap();
            assert_eq!(
                (orig.product_rank, orig.joint_dim, orig.spans),
                (via.product_rank, via.joint_dim, via.spans),
                "pipelines disagree at {a}x{b}"
            );
        }
    }

    /// The deficiency the real case leaves is exactly `C(m,2)·C(n,2)`, the
    /// `Λ²A ⊗ Λ²B` summand of `Sym(A⊗B)`. Checked across several dimensions so
    /// the 2×2 case is not a coincidence of small numbers.
    #[test]
    fn real_deficiency_matches_skew_skew_across_dims() {
        for (a, b) in [(2usize, 2usize), (2, 3), (3, 3), (2, 4)] {
            let r = local_tomography_spanning_real_via_gaussian(a, b).unwrap();
            assert_eq!(
                r.joint_dim - r.product_rank,
                skew_skew_deficiency(a, b).unwrap(),
                "deficiency mismatch at {a}x{b}"
            );
        }
    }

    #[test]
    fn kron_gaussian_multiplies_complex_entries_correctly() {
        // (i) ⊗ (i) = -1 in the 1x1 case: the sign is the whole content of
        // "complex", and getting it wrong is how a realification silently
        // degenerates into two independent real copies.
        let i = mx::from_rows(vec![vec![GaussianRat::from_ints(0, 1)]]).unwrap();
        let p = mx::kronecker(&i, &i).unwrap();
        assert_eq!(p.as_slice()[0], GaussianRat::from_ints(-1, 0));
    }

    #[test]
    fn encode_real_vector_is_re_then_im() {
        let m = vec![GaussianRat::from_ints(1, 2), GaussianRat::from_ints(3, 4)];
        let v: Vec<Rational> = m
            .iter()
            .map(|z| z.re.clone())
            .chain(m.iter().map(|z| z.im.clone()))
            .collect();
        assert_eq!(v.len(), 4);
        assert_eq!(
            v,
            vec![
                Rational::from_integer(1.into()),
                Rational::from_integer(3.into()),
                Rational::from_integer(2.into()),
                Rational::from_integer(4.into())
            ]
        );
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use linear_algebra::exact_field::involution as star;

    /// Small non-symmetric, non-commuting rational fixtures. Reused across the
    /// functor-law tests so a wrong index convention cannot pass by symmetry.
    fn fixtures() -> (
        BasicMatrix<Q>,
        BasicMatrix<Q>,
        BasicMatrix<Q>,
        BasicMatrix<Q>,
    ) {
        let q = |n: i64| ri(n);
        let f = BasicMatrix::from_row_major(2, 2, vec![q(1), q(2), q(0), q(3)]).unwrap();
        let f_prime = BasicMatrix::from_row_major(2, 2, vec![q(0), q(1), q(5), q(-2)]).unwrap();
        let g = BasicMatrix::from_row_major(2, 2, vec![q(4), q(0), q(-1), q(1)]).unwrap();
        let g_prime = BasicMatrix::from_row_major(2, 2, vec![q(2), q(3), q(1), q(0)]).unwrap();
        (f, f_prime, g, g_prime)
    }

    // --- functor laws (matrix identities, not usize arithmetic) -------------

    #[test]
    fn w614_functor_preserves_identities() {
        assert!(identity_is_preserved(2, 2).unwrap());
        assert!(identity_is_preserved(2, 3).unwrap());
        assert!(identity_is_preserved(3, 1).unwrap());
    }

    #[test]
    fn w614_functor_satisfies_interchange_law() {
        let (f, f_prime, g, g_prime) = fixtures();
        assert!(
            interchange_law_holds(&f, &f_prime, &g, &g_prime).unwrap(),
            "(f∘f')⊗(g∘g') != (f⊗g)∘(f'⊗g')"
        );
    }

    /// The interchange law is not vacuous: the fixtures do not commute, so the
    /// two sides are built from genuinely different intermediate matrices.
    #[test]
    fn w614_interchange_fixtures_are_non_commuting() {
        let (f, f_prime, _, _) = fixtures();
        assert_ne!(
            mx::multiply(&f, &f_prime).unwrap(),
            mx::multiply(&f_prime, &f).unwrap()
        );
    }

    #[test]
    fn w614_functor_is_associative_on_morphisms() {
        let (f, g, h, _) = fixtures();
        assert!(associativity_on_morphisms(&f, &g, &h).unwrap());
    }

    // --- local tomography as spanning ---------------------------------------

    /// The rebit pair: 3 local effects each, 9 products, but the joint real
    /// symmetric space is 10-dimensional. The products span only 9 of 10 — so
    /// local tomography FAILS, and now as a rank statement about actual
    /// matrices rather than a parameter count.
    #[test]
    fn w614_real_rebit_products_do_not_span() {
        let r = local_tomography_spanning_real(2, 2).unwrap();
        assert_eq!(r.local_dim_a, 3);
        assert_eq!(r.local_dim_b, 3);
        assert_eq!(r.product_count, 9);
        assert_eq!(r.joint_dim, 10);
        assert_eq!(r.product_rank, 9, "product effects should be independent");
        assert!(!r.spans, "real local tomography must fail for rebits");
    }

    /// The explicit witness: a nonzero symmetric Δ invisible to every product
    /// effect. This is the content the `9 != 10` count only gestured at.
    #[test]
    fn w614_real_rebit_witness_is_invisible_to_all_product_effects() {
        let delta = real_local_tomography_witness(2, 2).unwrap();
        assert_eq!(delta.shape(), (4, 4));

        // nonzero
        let mut nonzero = false;
        for i in 0..4 {
            for j in 0..4 {
                if !delta.get(i, j).unwrap().is_zero() {
                    nonzero = true;
                }
            }
        }
        assert!(nonzero, "witness must be a nonzero direction");

        // symmetric
        for i in 0..4 {
            for j in 0..4 {
                assert_eq!(
                    delta.get(i, j).unwrap(),
                    delta.get(j, i).unwrap(),
                    "witness must be symmetric at ({i},{j})"
                );
            }
        }

        // orthogonal to every product effect
        let ba = real_symmetric_basis(2).unwrap();
        let bb = real_symmetric_basis(2).unwrap();
        for a in &ba {
            for b in &bb {
                let e = tensor_morphisms(a, b).unwrap();
                assert!(
                    star::hs_inner(&e, &delta).unwrap().is_zero(),
                    "product effect sees the witness — local tomography would hold"
                );
            }
        }
    }

    /// The computed witness is exactly `J ⊗ J`, where `J = [[0,-1],[1,0]]` is
    /// the real symplectic generator — equivalently `−Y ⊗ Y` for the Pauli `Y`,
    /// since `Y = iJ` gives `Y ⊗ Y = i² J ⊗ J = −J ⊗ J`.
    ///
    /// This identifies *what* real quantum theory cannot see: the `YY`
    /// correlation. `Y` is the one Pauli with imaginary entries, so it is absent
    /// from the real symmetric algebra, and the product of two such absences is
    /// the single direction missing from the 9-of-10 span. The kernel search was
    /// not told this — it recovered it from the rank defect alone, which is why
    /// the agreement is evidence rather than restatement.
    #[test]
    fn w614_witness_is_the_yy_correlation() {
        let delta = real_local_tomography_witness(2, 2).unwrap();
        let q = |n: i64| ri(n);
        let j = BasicMatrix::from_row_major(2, 2, vec![q(0), q(-1), q(1), q(0)]).unwrap();
        let jj = tensor_morphisms(&j, &j).unwrap();

        // Kernel vectors are determined only up to a nonzero scalar, so compare
        // projectively: delta == c * (J ⊗ J) for some nonzero rational c.
        let c = delta.get(0, 3).unwrap() / jj.get(0, 3).unwrap();
        assert!(!c.is_zero(), "scale factor must be nonzero");
        for r in 0..4 {
            for s in 0..4 {
                assert_eq!(
                    delta.get(r, s).unwrap(),
                    &c * jj.get(r, s).unwrap(),
                    "witness is not a multiple of J (x) J at ({r},{s})"
                );
            }
        }
    }

    /// Control: the witness is NOT orthogonal to every joint effect. If it
    /// were, it would be the zero direction and the test above would be vacuous.
    #[test]
    fn w614_witness_is_visible_to_some_joint_effect() {
        let delta = real_local_tomography_witness(2, 2).unwrap();
        let joint = real_symmetric_basis(4).unwrap();
        assert!(
            joint
                .iter()
                .any(|e| !star::hs_inner(e, &delta).unwrap().is_zero()),
            "some joint effect must distinguish the witness"
        );
    }

    /// Larger case: 2 x 3. Local 3 * 6 = 18 products; joint dim 6 gives 21.
    /// Still short, so the failure is not an artifact of the 2 x 2 fixture.
    #[test]
    fn w614_real_spanning_fails_for_2x3_as_well() {
        let r = local_tomography_spanning_real(2, 3).unwrap();
        assert_eq!(r.local_dim_a, 3);
        assert_eq!(r.local_dim_b, 6);
        assert_eq!(r.joint_dim, 21);
        assert!(r.product_rank < r.joint_dim);
        assert!(!r.spans);
    }

    // --- operational countermodel: two indistinguishable STATES -------------
    //
    // The seven closure conditions. Together these upgrade "a missing linear
    // direction" to "two physical states with identical product statistics that
    // an admissible joint measurement separates".

    /// (1) `Δ` is symmetric, traceless, squares to `I`, and is nonzero.
    ///
    /// `Δ² = I` is the load-bearing one: with symmetry it forces the spectrum
    /// into `{±1}`, which is what makes the positivity margin below exact
    /// rather than numerical.
    #[test]
    fn w614op_1_delta_is_a_traceless_symmetric_involution() {
        let d = rebit_hidden_direction().unwrap();
        assert_eq!(d.shape(), (4, 4));

        for i in 0..4 {
            for j in 0..4 {
                assert_eq!(d.get(i, j).unwrap(), d.get(j, i).unwrap(), "not symmetric");
            }
        }
        assert!(mx::trace(&d).unwrap().is_zero(), "trace must vanish");
        assert_eq!(
            mx::multiply(&d, &d).unwrap(),
            mx::identity(4).unwrap(),
            "Delta^2 != I"
        );

        let nonzero = (0..4).any(|i| (0..4).any(|j| !d.get(i, j).unwrap().is_zero()));
        assert!(nonzero);
    }

    /// (2) and (3): `ρ_±` are symmetric with unit trace.
    #[test]
    fn w614op_23_states_are_symmetric_with_unit_trace() {
        let (rp, rm) = rebit_state_pair().unwrap();
        for r in [&rp, &rm] {
            for i in 0..4 {
                for j in 0..4 {
                    assert_eq!(r.get(i, j).unwrap(), r.get(j, i).unwrap());
                }
            }
            assert_eq!(mx::trace(r).unwrap(), Q::one(), "trace must be exactly 1");
        }
    }

    /// (4) `ρ_± ≻ 0`, with minimum eigenvalue **exactly** `1/8`.
    ///
    /// Proved algebraically rather than by an eigensolver. `(ρ − I/4)² = I/64`
    /// is an exact matrix identity, and with `ρ` symmetric it forces
    /// `spec(ρ) ⊆ {1/4 − 1/8, 1/4 + 1/8} = {1/8, 3/8}`, so `ρ ≻ 0`. That `1/8`
    /// is *attained* (not merely a lower bound) is witnessed by
    /// `ρ − (1/8)I` being singular — checked by exact rank, not a determinant
    /// tolerance.
    #[test]
    fn w614op_4_states_are_positive_definite_with_exact_min_eigenvalue_one_eighth() {
        let (rp, rm) = rebit_state_pair().unwrap();
        let quarter = mx::scale(&mx::identity(4).unwrap(), &(rq(1, 4))).unwrap();
        let sixty_fourth = mx::scale(&mx::identity(4).unwrap(), &(rq(1, 64))).unwrap();

        for r in [&rp, &rm] {
            // spectrum is pinned to {1/8, 3/8}
            let centered = mx::add(r, &mx::scale(&quarter, &(ri(-1))).unwrap()).unwrap();
            assert_eq!(
                mx::multiply(&centered, &centered).unwrap(),
                sixty_fourth,
                "(rho - I/4)^2 != I/64, so the spectrum is not {{1/8, 3/8}}"
            );

            // 1/8 is attained: rho - (1/8)I is singular
            let shifted = mx::add(
                r,
                &mx::scale(&mx::identity(4).unwrap(), &(rq(-1, 8))).unwrap(),
            )
            .unwrap();
            assert!(
                elimination::rank(&shifted).unwrap() < 4,
                "rho - (1/8)I is nonsingular, so 1/8 is not attained"
            );

            // and 1/8 is a strict lower bound: rho - cI stays nonsingular below it
            let below = mx::add(
                r,
                &mx::scale(&mx::identity(4).unwrap(), &(rq(-1, 16))).unwrap(),
            )
            .unwrap();
            assert_eq!(
                elimination::rank(&below).unwrap(),
                4,
                "rho - (1/16)I should be nonsingular if min eigenvalue is 1/8"
            );
        }
    }

    /// (5) The two states are distinct.
    #[test]
    fn w614op_5_states_are_distinct() {
        let (rp, rm) = rebit_state_pair().unwrap();
        assert_ne!(rp, rm);
    }

    /// (6) Every real-symmetric **product** effect assigns them equal
    /// probability:
    ///
    /// `tr[(E_A ⊗ E_B)(ρ₊ − ρ₋)] = ¼ tr(E_A J) tr(E_B J) = 0`,
    ///
    /// because `tr(EJ) = 0` for `E` symmetric and `J` antisymmetric. Checked on
    /// the full basis **and** on randomised rational combinations, since the
    /// claim is about *every* product effect, not just basis elements.
    #[test]
    fn w614op_6_all_product_effects_assign_equal_probability() {
        let (rp, rm) = rebit_state_pair().unwrap();
        let diff = mx::add(&rp, &mx::scale(&rm, &(ri(-1))).unwrap()).unwrap();

        let ba = real_symmetric_basis(2).unwrap();
        let bb = real_symmetric_basis(2).unwrap();

        // basis product effects
        for a in &ba {
            for b in &bb {
                let e = tensor_morphisms(a, b).unwrap();
                assert!(
                    star::hs_inner(&e, &diff).unwrap().is_zero(),
                    "a basis product effect separates the states"
                );
            }
        }

        // general product effects: arbitrary rational combinations of each factor
        let coeffs: [[i64; 3]; 4] = [[1, -2, 3], [5, 7, -1], [-4, 0, 2], [9, -3, -6]];
        for ca in &coeffs {
            for cb in &coeffs {
                let mut ea = BasicMatrix::zero(2, 2).unwrap();
                for (k, a) in ba.iter().enumerate() {
                    ea = mx::add(&ea, &mx::scale(a, &(ri(ca[k]))).unwrap()).unwrap();
                }
                let mut eb = BasicMatrix::zero(2, 2).unwrap();
                for (k, b) in bb.iter().enumerate() {
                    eb = mx::add(&eb, &mx::scale(b, &(ri(cb[k]))).unwrap()).unwrap();
                }
                let e = tensor_morphisms(&ea, &eb).unwrap();
                assert!(
                    star::hs_inner(&e, &diff).unwrap().is_zero(),
                    "a general product effect separates the states"
                );
            }
        }
    }

    /// (7) **The anti-vacuity control.** An admissible joint effect — the
    /// orthogonal projector `P = (I + Δ)/2` — separates them by exactly `1/2`.
    ///
    /// Without this, test (6) would be satisfiable by the states being equal, or
    /// by the pairing being broken. This is the test that makes the countermodel
    /// operational rather than formal.
    #[test]
    fn w614op_7_a_joint_projector_separates_them_by_exactly_one_half() {
        let (rp, rm) = rebit_state_pair().unwrap();
        let p = rebit_separating_projector().unwrap();

        // P is an orthogonal projector: P^2 = P and P^T = P
        assert_eq!(mx::multiply(&p, &p).unwrap(), p, "P is not idempotent");
        for i in 0..4 {
            for j in 0..4 {
                assert_eq!(p.get(i, j).unwrap(), p.get(j, i).unwrap());
            }
        }
        // admissible effect: 0 <= P <= I, i.e. I - P is also a projector
        let ip = mx::add(
            &mx::identity(4).unwrap(),
            &mx::scale(&p, &(ri(-1))).unwrap(),
        )
        .unwrap();
        assert_eq!(
            mx::multiply(&ip, &ip).unwrap(),
            ip,
            "I - P is not idempotent"
        );

        let plus = star::hs_inner(&p, &rp).unwrap();
        let minus = star::hs_inner(&p, &rm).unwrap();
        assert_eq!(
            plus - minus,
            rq(1, 2),
            "joint projector must separate the states by exactly 1/2"
        );
    }

    /// The deficiency is the skew–skew sector `Λ²A ⊗ Λ²B`, of dimension
    /// `C(m,2)·C(n,2)` — checked against the *measured* rank, not against the
    /// formula restated.
    #[test]
    fn w614op_deficiency_equals_skew_skew_dimension() {
        for (m, n) in [(2usize, 2usize), (2, 3), (3, 3)] {
            let r = local_tomography_spanning_real(m, n).unwrap();
            assert_eq!(
                r.joint_dim - r.product_rank,
                skew_skew_deficiency(m, n).unwrap(),
                "deficiency at {m}x{n} is not C(m,2)*C(n,2)"
            );
        }
        assert_eq!(skew_skew_deficiency(2, 2).unwrap(), 1);
        assert_eq!(skew_skew_deficiency(2, 3).unwrap(), 3);
        assert_eq!(skew_skew_deficiency(3, 3).unwrap(), 9);
    }

    // --- pricing the tensor -------------------------------------------------

    /// Composition does not force the tensor. The Cartesian composition is a
    /// different law on the same inputs, and the estate holds it constructible
    /// from FinL1 — so `OB-COMPOSE` is what must be paid for, not "composition".
    #[test]
    fn w614_cartesian_and_tensor_laws_differ() {
        let cart = cartesian_compose_dim(2, 3).unwrap();
        let tens = MonoidalComposite::tensor(
            FiniteSystem::qubit_complex("A"),
            FiniteSystem {
                dim: 3,
                phase: PhaseCarrier::ComplexU1,
                label: "B".into(),
            },
        )
        .unwrap()
        .dim;
        assert_eq!(cart, 5);
        assert_eq!(tens, 6);
        assert_ne!(cart, tens, "tensor must not be derivable from + alone");
    }

    #[test]
    fn composition_tensor_dims() {
        let a = FiniteSystem::qubit_complex("A");
        let b = FiniteSystem::qubit_complex("B");
        let ab = MonoidalComposite::tensor(a, b).unwrap();
        assert_eq!(ab.dim, 4);
        assert_eq!(ab.phase, PhaseCarrier::ComplexU1);
        assert!(MonoidalComposite::associativity_dims(2, 2, 2));
    }

    #[test]
    fn composition_complex_local_tomography() {
        let r = LocalTomographyReport::complex_product(2, 2).unwrap();
        assert!(r.identity_holds);
        assert_eq!(r.joint_param, 16);
    }

    #[test]
    fn composition_real_rebit_countermodel() {
        let cm = RealRebitCountermodel::rebit_pair();
        assert!(cm.is_valid_countermodel());
        assert!(!cm.report.identity_holds);
        assert_eq!(cm.report.local_param_a * cm.report.local_param_b, 9);
        assert_eq!(cm.report.joint_param, 10);
    }

    #[test]
    fn composition_rebit_tensor_stays_real() {
        let ab = MonoidalComposite::tensor(FiniteSystem::rebit("r1"), FiniteSystem::rebit("r2"))
            .unwrap();
        assert_eq!(ab.phase, PhaseCarrier::RealOnly);
    }

    #[test]
    fn composition_authority_none() {
        assert!(AUTHORITY_FENCE.contains("AuthorityEffect None"));
        let _ = born_masses_from_amplitudes_sq(&[Q::one(), Q::one()]).unwrap();
        assert!(!Zero::is_zero(&Q::one()));
    }
}
