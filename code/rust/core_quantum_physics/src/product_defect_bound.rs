//! Premise checker for the short-time product-defect lower bound (WDP DP-7).
//!
//! Imported host (premises, not outputs): a finite tensor product of local Hilbert spaces
//! `C^{d_0} ⊗ … ⊗ C^{d_{N-1}}` (site 0 is the most significant tensor factor), a
//! time-independent Hermitian Hamiltonian `H = Σ_α h_α` whose terms act on one or two sites,
//! and `ρ(t) = e^{-itH} ρ(0) e^{itH}`. For a subsystem `σ` of `k = |σ|` sites put
//! `F_σ(t) = ρ_σ(t) − ⊗_{i∈σ} ρ_i(t)` and `D_σ(t) = ‖F_σ(t)‖₁`.
//!
//! Written statement (projection obstruction §5 extended to `k` sites, DP-7/c3): if
//! `F_σ(0) = 0`, `G ≥ max_v Σ_{α∋v} ‖h_α‖_∞` (one-site fields included) and
//! `0 ≤ ν ≤ ‖(I − P_σ) ρ_σ'(0)‖₁`, then for every `t ≥ 0`
//!
//! `D_σ(t) ≥ ν t − 4k(k+1) G² t²`,
//!
//! and `4k(k+1) ≤ 6k²` exactly when `k ≥ 2` (`6k² − 4k(k+1) = 2k(k−2)`). With half-trace
//! normalisation `T_σ = D_σ / 2` both coefficients halve: `T_σ(t) ≥ (ν/2) t − 3k² G² t²`.
//! `t* = ν / (2c)` (`c` the chosen raw coefficient) is the vertex of the envelope and a
//! half-slope window `D_σ(t) ≥ ν t / 2` on `0 ≤ t ≤ t*`; it is not a cutoff for the remainder.
//!
//! What this module checks: only the finite premises, exactly over `Q(i)`:
//! term locality, Hermiticity and support; `b_α I ± h_α ⪰ 0` (so `‖h_α‖_∞ ≤ b_α`); the
//! incident sums against `G`; density admission; `F_σ(0) = 0`; the initial derivative
//! `L_σ`, the product-tangent projection `P_σ` and `n_σ = (I − P_σ) L_σ`; a trace-dual witness
//! `W` with `I ± W ⪰ 0` and `Tr(W n_σ) ≥ ν` (so `ν ≤ ‖n_σ‖₁`). The Taylor/Duhamel remainder
//! estimate in the imported continuous-time host is a named residual
//! ([`ANALYTIC_RESIDUAL`]); no matrix exponential is evaluated here.
//!
//! AuthorityEffect: None.

use crate::exact_hermitian::{decide_psd, PsdDecision};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_kernel::Digest;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational, Zero};

/// Largest total Hilbert-space dimension admitted.
pub const MAX_TOTAL_DIMENSION: usize = 64;

/// The analytic step this module does not check: Taylor's formula with integral remainder
/// for `F_σ` in the imported finite host, with `‖F_σ''(u)‖₁ ≤ 8k(k+1)g²`.
pub const ANALYTIC_RESIDUAL: &str =
    "DP7_TAYLOR_REMAINDER_IN_IMPORTED_HOST: F(t) = t n + ∫_0^t (t-u) F''(u) du with ||F''||_1 <= 8k(k+1)g^2";

/// Source binding of the written statement whose premises are checked.
pub const SOURCE_THEOREM: &str =
    "projection_obstruction.md §5 Theorem 5.1 (k=2) extended to k sites, WDP DP-7/c3";

const MODEL_DOMAIN: &str = "core.quantum_physics.product_defect.model.v1";
const WITNESS_DOMAIN: &str = "core.quantum_physics.product_defect.witness.v1";
const SOURCE_DOMAIN: &str = "core.quantum_physics.product_defect.source.v1";

type Mat = Vec<Vec<GaussianRat>>;

/// One Hamiltonian term `h_α` acting on `support` (strictly ascending sites), with a declared
/// operator-norm bound `b_α`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SiteTerm {
    pub support: Vec<usize>,
    pub operator: BasicMatrix<GaussianRat>,
    pub norm_bound: Rational,
}

/// Whether the declared Hamiltonian depends on time. Only `Independent` is admitted.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum TimeDependence {
    Independent,
    Dependent,
}

/// The initial state: one density per site, or one global density whose `σ` reduction
/// must equal the product of its one-site marginals.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InitialState {
    Product(Vec<BasicMatrix<GaussianRat>>),
    Global(BasicMatrix<GaussianRat>),
}

/// Raw trace norm `D_σ` or trace distance `T_σ = D_σ / 2`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum DefectNormalisation {
    RawTraceNorm,
    HalfTrace,
}

/// Strong `4k(k+1)` or weak `6k²` raw remainder coefficient.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RemainderCoefficient {
    Strong,
    Weak,
}

/// Caller-supplied premises.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ProductDefectPremises {
    pub local_dims: Vec<usize>,
    pub terms: Vec<SiteTerm>,
    pub time_dependence: TimeDependence,
    pub initial: InitialState,
    /// `σ`, strictly ascending.
    pub subsystem: Vec<usize>,
    /// Declared `k`; must equal `|σ|` (site cardinality, not a simplex dimension).
    pub declared_k: usize,
    /// Declared `G`.
    pub coupling_bound: Rational,
    /// Declared lower bound `ν` on the normal rate.
    pub normal_rate: Rational,
    /// Trace-dual witness on the `σ` carrier; required when `ν > 0`.
    pub witness: Option<BasicMatrix<GaussianRat>>,
}

/// Typed refusals.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ProductDefectRefusal {
    #[error("no host model: empty site list or zero local dimension")]
    MissingHostModel,
    #[error("total dimension {0} exceeds the admitted limit")]
    ResourceLimit(usize),
    #[error("time-dependent Hamiltonian is outside this statement")]
    TimeDependentHamiltonian,
    #[error("term {term} has support size {size}; only one- and two-site terms are admitted")]
    UnsupportedLocality { term: usize, size: usize },
    #[error("term {term} support is not strictly ascending inside the site list")]
    BadSupport { term: usize },
    #[error("term {term} has the wrong shape for its support")]
    TermShapeMismatch { term: usize },
    #[error("term {term} is not Hermitian")]
    NonHermitianTerm { term: usize },
    #[error("term {term}: b I {sign} h is not positive semidefinite (value {value})")]
    NormBoundInvalid {
        term: usize,
        sign: char,
        value: Rational,
    },
    #[error("site {site}: incident norm sum {sum} exceeds the declared G")]
    IncidentNormUnderbound { site: usize, sum: Rational },
    #[error("negative declared G")]
    NegativeCouplingBound,
    #[error("subsystem is empty, unsorted, repeated or out of range")]
    BadSubsystem,
    #[error("declared k {declared} differs from the site cardinality {actual}")]
    KSemanticsMismatch { declared: usize, actual: usize },
    #[error("initial density {0:?} is malformed (shape, Hermitian, PSD or trace one)")]
    InvalidDensity(Option<usize>),
    #[error("F_sigma(0) is not zero: the initial sigma state is not the product of its marginals")]
    NotProductInitial,
    #[error("negative declared normal rate")]
    NegativeNormalRate,
    #[error("positive normal rate without a trace-dual witness")]
    NormalRateWitnessMissing,
    #[error("normal-rate witness invalid: {0}")]
    NormalRateWitnessInvalid(String),
    #[error("Tr(W n) = {trace} is below the declared normal rate")]
    NormalRateBelowClaim { trace: Rational },
    #[error("negative time")]
    NegativeTime,
    #[error("the weak coefficient 6k^2 needs k >= 2 (6k^2 - 4k(k+1) = 2k(k-2))")]
    WeakCoefficientNeedsTwoSites,
    #[error("no half-slope window: nu = 0 or G = 0")]
    NoHalfSlopeWindow,
    #[error("t lies outside the half-slope window [0, t*]")]
    OutsideHalfSlopeWindow,
    #[error("exact matrix operation failed: {0}")]
    Matrix(String),
}

/// Checked premises. Fields are private; the certificate exists only through
/// [`certify_product_defect_premises`].
#[derive(Debug, Clone)]
pub struct ProductDefectCertificate {
    k: usize,
    coupling_bound: Rational,
    normal_rate: Rational,
    incident_sums: Vec<Rational>,
    initial_derivative: BasicMatrix<GaussianRat>,
    normal_derivative: BasicMatrix<GaussianRat>,
    witness_trace: Rational,
    model_digest: Digest,
    witness_digest: Digest,
    source_digest: Digest,
}

impl PartialEq for ProductDefectCertificate {
    fn eq(&self, other: &Self) -> bool {
        self.model_digest == other.model_digest
            && self.witness_digest == other.witness_digest
            && self.source_digest == other.source_digest
            && self.k == other.k
            && self.coupling_bound == other.coupling_bound
            && self.normal_rate == other.normal_rate
    }
}
impl Eq for ProductDefectCertificate {}

impl ProductDefectCertificate {
    pub fn k(&self) -> usize {
        self.k
    }
    pub fn coupling_bound(&self) -> &Rational {
        &self.coupling_bound
    }
    pub fn normal_rate(&self) -> &Rational {
        &self.normal_rate
    }
    /// `Σ_{α∋v} b_α` per site, replayed.
    pub fn incident_sums(&self) -> &[Rational] {
        &self.incident_sums
    }
    /// `L_σ = Tr_{V∖σ}(−i[H, ρ(0)])`.
    pub fn initial_derivative(&self) -> &BasicMatrix<GaussianRat> {
        &self.initial_derivative
    }
    /// `n_σ = (I − P_σ) L_σ`.
    pub fn normal_derivative(&self) -> &BasicMatrix<GaussianRat> {
        &self.normal_derivative
    }
    /// `Tr(W n_σ)` (zero when no witness was supplied).
    pub fn witness_trace(&self) -> &Rational {
        &self.witness_trace
    }
    pub fn model_digest(&self) -> &Digest {
        &self.model_digest
    }
    pub fn witness_digest(&self) -> &Digest {
        &self.witness_digest
    }
    pub fn source_digest(&self) -> &Digest {
        &self.source_digest
    }

    /// Raw remainder coefficient: `4k(k+1)` or `6k²` (the latter refused for `k < 2`).
    pub fn raw_coefficient(
        &self,
        which: RemainderCoefficient,
    ) -> Result<Rational, ProductDefectRefusal> {
        raw_coefficient(self.k, which)
    }

    /// The polynomial lower envelope at `t ≥ 0`: raw `ν t − c G² t²`, half-trace
    /// `(ν/2) t − (c/2) G² t²`. Valid at every `t ≥ 0` under the written theorem.
    pub fn lower_envelope(
        &self,
        t: &Rational,
        which: RemainderCoefficient,
        normalisation: DefectNormalisation,
    ) -> Result<Rational, ProductDefectRefusal> {
        if t < &Rational::zero() {
            return Err(ProductDefectRefusal::NegativeTime);
        }
        let c = self.raw_coefficient(which)?;
        let g2 = &self.coupling_bound * &self.coupling_bound;
        let raw = &self.normal_rate * t - c * g2 * t * t;
        Ok(match normalisation {
            DefectNormalisation::RawTraceNorm => raw,
            DefectNormalisation::HalfTrace => raw / ri(2),
        })
    }

    /// `t* = ν / (2 c G²)`; refused when `ν = 0` or `G = 0`. The same in both normalisations.
    pub fn half_slope_endpoint(
        &self,
        which: RemainderCoefficient,
    ) -> Result<Rational, ProductDefectRefusal> {
        let c = self.raw_coefficient(which)?;
        if self.normal_rate.is_zero() || self.coupling_bound.is_zero() {
            return Err(ProductDefectRefusal::NoHalfSlopeWindow);
        }
        Ok(&self.normal_rate / (ri(2) * c * &self.coupling_bound * &self.coupling_bound))
    }

    /// The half-slope claim `envelope(t) ≥ slope·t/2` for `0 ≤ t ≤ t*`; returns `slope·t/2`.
    /// Outside the window this stronger claim is refused; [`Self::lower_envelope`] still holds.
    pub fn half_slope_claim(
        &self,
        t: &Rational,
        which: RemainderCoefficient,
        normalisation: DefectNormalisation,
    ) -> Result<Rational, ProductDefectRefusal> {
        let envelope = self.lower_envelope(t, which, normalisation)?;
        let t_star = self.half_slope_endpoint(which)?;
        if t > &t_star {
            return Err(ProductDefectRefusal::OutsideHalfSlopeWindow);
        }
        let slope = match normalisation {
            DefectNormalisation::RawTraceNorm => self.normal_rate.clone(),
            DefectNormalisation::HalfTrace => &self.normal_rate / ri(2),
        };
        let half = slope * t / ri(2);
        if envelope < half {
            return Err(ProductDefectRefusal::Matrix(
                "half-slope replay disagrees".into(),
            ));
        }
        Ok(half)
    }
}

/// Raw remainder coefficient for `k` sites.
pub fn raw_coefficient(
    k: usize,
    which: RemainderCoefficient,
) -> Result<Rational, ProductDefectRefusal> {
    let kr = Rational::from_integer((k as u64).into());
    match which {
        RemainderCoefficient::Strong => Ok(ri(4) * &kr * (&kr + ri(1))),
        RemainderCoefficient::Weak if k >= 2 => Ok(ri(6) * &kr * &kr),
        RemainderCoefficient::Weak => Err(ProductDefectRefusal::WeakCoefficientNeedsTwoSites),
    }
}

/// General-order Taylor remainder and lower-bound certificates for product defect (PO-000 §5.8 Theorem 5.5).
///
/// For order k, the remainder bound is:
/// R_{k+1}(t) = 2^{k+2} (k + 2) g^{k+1} t^{k+1} = 2 (k + 2) (2g)^{k+1} t^{k+1}
///
/// And the defect lower bound is:
/// D_e(t) >= (||F_e^{(k)}(0)||_1 / k!) * t^k - R_{k+1}(t).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct GeneralOrderDefectBound {
    pub k: usize,
}

impl GeneralOrderDefectBound {
    pub fn new(k: usize) -> Self {
        Self { k }
    }

    /// Computes the remainder bound R_{k+1}(t) = 2^{k+2} (k + 2) g^{k+1} t^{k+1}.
    pub fn compute_remainder_bound(k: usize, g: Rational, t: Rational) -> Rational {
        let two = ri(2);
        let two_g = &two * &g;
        let mut pow_2g = ri(1);
        for _ in 0..=(k) {
            pow_2g = pow_2g * &two_g;
        }
        let mut pow_t = ri(1);
        for _ in 0..=(k) {
            pow_t = pow_t * &t;
        }
        let coeff = ri(2 * ((k + 2) as i64));
        coeff * pow_2g * pow_t
    }

    /// Computes the k-th order lower bound: (||F_e^{(k)}(0)||_1 / k!) * t^k - R_{k+1}(t).
    pub fn lower_bound_at(k: usize, norm_fk: Rational, g: Rational, t: Rational) -> Rational {
        let mut fact = ri(1);
        for i in 1..=k {
            fact = fact * ri(i as i64);
        }
        let mut pow_t_k = ri(1);
        for _ in 0..k {
            pow_t_k = pow_t_k * &t;
        }
        let leading_term = (norm_fk / fact) * pow_t_k;
        let remainder = Self::compute_remainder_bound(k, g, t);
        leading_term - remainder
    }

    pub fn remainder_bound(&self, g: Rational, t: Rational) -> Rational {
        Self::compute_remainder_bound(self.k, g, t)
    }

    pub fn lower_bound(&self, norm_fk: Rational, g: Rational, t: Rational) -> Rational {
        Self::lower_bound_at(self.k, norm_fk, g, t)
    }
}

fn compute_total_dimension(local_dims: &[usize]) -> Result<usize, ProductDefectRefusal> {
    if local_dims.is_empty() || local_dims.contains(&0) {
        return Err(ProductDefectRefusal::MissingHostModel);
    }
    let mut total: usize = 1;
    for &d in local_dims {
        total = total
            .checked_mul(d)
            .filter(|&t| t <= MAX_TOTAL_DIMENSION)
            .ok_or_else(|| {
                ProductDefectRefusal::ResourceLimit(
                    local_dims.iter().fold(1usize, |a, &d| a.saturating_mul(d)),
                )
            })?;
    }
    Ok(total)
}

fn validate_and_accumulate_term(
    idx: usize,
    term: &SiteTerm,
    local_dims: &[usize],
    n_sites: usize,
    h_global: &mut Mat,
    incident: &mut [Rational],
) -> Result<(), ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    let size = term.support.len();
    if !(1..=2).contains(&size) {
        return Err(R::UnsupportedLocality { term: idx, size });
    }
    if !strictly_ascending_in_range(&term.support, n_sites) {
        return Err(R::BadSupport { term: idx });
    }
    let dim: usize = term.support.iter().map(|&s| local_dims[s]).product();
    let h = to_mat(&term.operator, dim).ok_or(R::TermShapeMismatch { term: idx })?;
    if !is_hermitian(&h) {
        return Err(R::NonHermitianTerm { term: idx });
    }
    for (sign, s) in [('-', -1i64), ('+', 1i64)] {
        let shifted = add(
            &scale_identity(dim, &term.norm_bound),
            &scale(&h, &GaussianRat::from_ints(s, 0)),
        );
        if let PsdDecision::Negative { value, .. } = psd(&shifted)? {
            return Err(R::NormBoundInvalid {
                term: idx,
                sign,
                value,
            });
        }
    }
    for &s in &term.support {
        incident[s] += &term.norm_bound;
    }
    *h_global = add(h_global, &embed(&h, &term.support, local_dims));
    Ok(())
}

fn accumulate_hamiltonian_terms(
    p: &ProductDefectPremises,
    total: usize,
    n_sites: usize,
) -> Result<(Mat, Vec<Rational>), ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    let mut h_global = zeros(total);
    let mut incident = vec![Rational::zero(); n_sites];
    for (idx, term) in p.terms.iter().enumerate() {
        validate_and_accumulate_term(
            idx,
            term,
            &p.local_dims,
            n_sites,
            &mut h_global,
            &mut incident,
        )?;
    }
    if p.coupling_bound < Rational::zero() {
        return Err(R::NegativeCouplingBound);
    }
    for (site, sum) in incident.iter().enumerate() {
        if sum > &p.coupling_bound {
            return Err(R::IncidentNormUnderbound {
                site,
                sum: sum.clone(),
            });
        }
    }
    Ok((h_global, incident))
}

fn build_initial_density(
    p: &ProductDefectPremises,
    total: usize,
    n_sites: usize,
) -> Result<Mat, ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    match &p.initial {
        InitialState::Product(locals) => {
            if locals.len() != n_sites {
                return Err(R::InvalidDensity(None));
            }
            let mut acc: Mat = vec![vec![GaussianRat::one()]];
            for (site, local) in locals.iter().enumerate() {
                let m = to_mat(local, p.local_dims[site]).ok_or(R::InvalidDensity(Some(site)))?;
                check_density(&m).map_err(|_| R::InvalidDensity(Some(site)))?;
                acc = kron(&acc, &m);
            }
            Ok(acc)
        }
        InitialState::Global(global) => {
            let m = to_mat(global, total).ok_or(R::InvalidDensity(None))?;
            check_density(&m).map_err(|_| R::InvalidDensity(None))?;
            Ok(m)
        }
    }
}

fn compute_sigma_derivatives(
    p: &ProductDefectPremises,
    h_global: &Mat,
    rho0: &Mat,
) -> Result<(Mat, Mat), ProductDefectRefusal> {
    let sigma = &p.subsystem;
    let rho_sigma = reduce(rho0, &p.local_dims, sigma);
    let marginals: Vec<Mat> = sigma
        .iter()
        .map(|&i| reduce(rho0, &p.local_dims, &[i]))
        .collect();
    if rho_sigma != kron_all(&marginals) {
        return Err(ProductDefectRefusal::NotProductInitial);
    }
    let minus_i = GaussianRat::from_ints(0, -1);
    let l_global = scale(&sub(&mul(h_global, rho0), &mul(rho0, h_global)), &minus_i);
    let l_sigma = reduce(&l_global, &p.local_dims, sigma);
    let mut tangent = zeros(rho_sigma.len());
    for (pos, &i) in sigma.iter().enumerate() {
        let li = reduce(&l_global, &p.local_dims, &[i]);
        let mut factors = marginals.clone();
        factors[pos] = li;
        tangent = add(&tangent, &kron_all(&factors));
    }
    let n_sigma = sub(&l_sigma, &tangent);
    Ok((l_sigma, n_sigma))
}

fn verify_supplied_witness_mat(
    w: &BasicMatrix<GaussianRat>,
    n_sigma: &Mat,
) -> Result<(Rational, Vec<u8>), ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    let dim_sigma = n_sigma.len();
    let wm = to_mat(w, dim_sigma).ok_or_else(|| {
        R::NormalRateWitnessInvalid("shape differs from the sigma carrier".into())
    })?;
    if !is_hermitian(&wm) {
        return Err(R::NormalRateWitnessInvalid("W is not Hermitian".into()));
    }
    for (label, s) in [("I - W", -1i64), ("I + W", 1i64)] {
        let shifted = add(
            &scale_identity(dim_sigma, &ri(1)),
            &scale(&wm, &GaussianRat::from_ints(s, 0)),
        );
        if let PsdDecision::Negative { value, .. } = psd(&shifted)? {
            return Err(R::NormalRateWitnessInvalid(format!(
                "{label} has negative value {value}"
            )));
        }
    }
    let tr = trace(&mul(&wm, n_sigma));
    if !tr.im.is_zero() {
        return Err(R::Matrix("Tr(W n) is not real".into()));
    }
    Ok((tr.re, mat_bytes(&wm)))
}

fn evaluate_normal_rate_witness(
    p: &ProductDefectPremises,
    n_sigma: &Mat,
) -> Result<(Rational, Vec<u8>), ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    if p.normal_rate < Rational::zero() {
        return Err(R::NegativeNormalRate);
    }
    let (witness_trace, witness_bytes) = match &p.witness {
        None if p.normal_rate > Rational::zero() => return Err(R::NormalRateWitnessMissing),
        None => (Rational::zero(), b"none".to_vec()),
        Some(w) => verify_supplied_witness_mat(w, n_sigma)?,
    };
    if witness_trace < p.normal_rate {
        return Err(R::NormalRateBelowClaim {
            trace: witness_trace,
        });
    }
    Ok((witness_trace, witness_bytes))
}

fn validate_subsystem_premises(
    p: &ProductDefectPremises,
    n_sites: usize,
) -> Result<(), ProductDefectRefusal> {
    use ProductDefectRefusal as R;
    if p.time_dependence == TimeDependence::Dependent {
        return Err(R::TimeDependentHamiltonian);
    }
    if p.subsystem.is_empty() || !strictly_ascending_in_range(&p.subsystem, n_sites) {
        return Err(R::BadSubsystem);
    }
    if p.declared_k != p.subsystem.len() {
        return Err(R::KSemanticsMismatch {
            declared: p.declared_k,
            actual: p.subsystem.len(),
        });
    }
    Ok(())
}

/// Checks every finite premise and returns the certificate.
pub fn certify_product_defect_premises(
    p: &ProductDefectPremises,
) -> Result<ProductDefectCertificate, ProductDefectRefusal> {
    let total = compute_total_dimension(&p.local_dims)?;
    let n_sites = p.local_dims.len();
    validate_subsystem_premises(p, n_sites)?;
    let (h_global, incident) = accumulate_hamiltonian_terms(p, total, n_sites)?;
    let rho0 = build_initial_density(p, total, n_sites)?;
    let (l_sigma, n_sigma) = compute_sigma_derivatives(p, &h_global, &rho0)?;
    let (witness_trace, witness_bytes) = evaluate_normal_rate_witness(p, &n_sigma)?;
    let mut witness_payload = witness_bytes;
    witness_payload
        .extend_from_slice(format!("|nu={}|G={}", p.normal_rate, p.coupling_bound).as_bytes());
    Ok(ProductDefectCertificate {
        k: p.subsystem.len(),
        coupling_bound: p.coupling_bound.clone(),
        normal_rate: p.normal_rate.clone(),
        incident_sums: incident,
        initial_derivative: to_basic(&l_sigma)?,
        normal_derivative: to_basic(&n_sigma)?,
        witness_trace,
        model_digest: Digest::of_domained(MODEL_DOMAIN, &model_bytes(p, &rho0)),
        witness_digest: Digest::of_domained(WITNESS_DOMAIN, &witness_payload),
        source_digest: Digest::of_domained(SOURCE_DOMAIN, SOURCE_THEOREM.as_bytes()),
    })
}

// --- exact helpers over Q(i) -------------------------------------------------------------

fn strictly_ascending_in_range(s: &[usize], n: usize) -> bool {
    s.windows(2).all(|w| w[0] < w[1]) && s.iter().all(|&x| x < n)
}

fn zeros(n: usize) -> Mat {
    vec![vec![GaussianRat::zero(); n]; n]
}

fn to_mat(m: &BasicMatrix<GaussianRat>, dim: usize) -> Option<Mat> {
    if m.rows() != dim || m.cols() != dim {
        return None;
    }
    (0..dim)
        .map(|i| {
            (0..dim)
                .map(|j| m.get_ref(i, j).ok().cloned())
                .collect::<Option<Vec<_>>>()
        })
        .collect()
}

fn to_basic(m: &Mat) -> Result<BasicMatrix<GaussianRat>, ProductDefectRefusal> {
    let n = m.len();
    BasicMatrix::from_row_major(n, n, m.iter().flatten().cloned().collect())
        .map_err(|e| ProductDefectRefusal::Matrix(e.to_string()))
}

fn psd(m: &Mat) -> Result<PsdDecision, ProductDefectRefusal> {
    decide_psd(&to_basic(m)?).map_err(|e| ProductDefectRefusal::Matrix(e.to_string()))
}

fn is_hermitian(m: &Mat) -> bool {
    (0..m.len()).all(|i| (0..m.len()).all(|j| m[i][j] == m[j][i].conj()))
}

fn trace(m: &Mat) -> GaussianRat {
    (0..m.len()).fold(GaussianRat::zero(), |acc, i| acc.add(&m[i][i]))
}

fn check_density(m: &Mat) -> Result<(), ()> {
    if !is_hermitian(m) || trace(m) != GaussianRat::one() {
        return Err(());
    }
    match psd(m) {
        Ok(PsdDecision::PositiveSemidefinite { .. }) => Ok(()),
        _ => Err(()),
    }
}

fn add(a: &Mat, b: &Mat) -> Mat {
    a.iter()
        .zip(b)
        .map(|(x, y)| x.iter().zip(y).map(|(u, v)| u.add(v)).collect())
        .collect()
}

fn sub(a: &Mat, b: &Mat) -> Mat {
    a.iter()
        .zip(b)
        .map(|(x, y)| x.iter().zip(y).map(|(u, v)| u.sub(v)).collect())
        .collect()
}

fn scale(a: &Mat, c: &GaussianRat) -> Mat {
    a.iter()
        .map(|r| r.iter().map(|x| x.mul(c)).collect())
        .collect()
}

fn scale_identity(n: usize, b: &Rational) -> Mat {
    let mut m = zeros(n);
    for (i, row) in m.iter_mut().enumerate() {
        row[i] = GaussianRat::from_rational(b.clone());
    }
    m
}

fn mul(a: &Mat, b: &Mat) -> Mat {
    let n = a.len();
    let mut out = zeros(n);
    for i in 0..n {
        for k in 0..n {
            if a[i][k].is_zero() {
                continue;
            }
            for j in 0..n {
                out[i][j] = out[i][j].add(&a[i][k].mul(&b[k][j]));
            }
        }
    }
    out
}

fn kron(a: &Mat, b: &Mat) -> Mat {
    let (na, nb) = (a.len(), b.len());
    let mut out = zeros(na * nb);
    for i in 0..na {
        for j in 0..na {
            for k in 0..nb {
                for l in 0..nb {
                    out[i * nb + k][j * nb + l] = a[i][j].mul(&b[k][l]);
                }
            }
        }
    }
    out
}

fn kron_all(fs: &[Mat]) -> Mat {
    fs.iter()
        .fold(vec![vec![GaussianRat::one()]], |acc, f| kron(&acc, f))
}

/// Mixed-radix digits of `index` (site 0 most significant).
fn digits(mut index: usize, dims: &[usize]) -> Vec<usize> {
    let mut out = vec![0; dims.len()];
    for s in (0..dims.len()).rev() {
        out[s] = index % dims[s];
        index /= dims[s];
    }
    out
}

fn sub_index(d: &[usize], dims: &[usize], sites: &[usize]) -> usize {
    sites.iter().fold(0, |acc, &s| acc * dims[s] + d[s])
}

/// `h` (acting on `support`) embedded as `h ⊗ I` in the declared tensor order.
fn embed(h: &Mat, support: &[usize], dims: &[usize]) -> Mat {
    let total: usize = dims.iter().product();
    let mut out = zeros(total);
    for i in 0..total {
        let di = digits(i, dims);
        for j in 0..total {
            let dj = digits(j, dims);
            let off_agree = (0..dims.len()).all(|s| support.contains(&s) || di[s] == dj[s]);
            if off_agree {
                out[i][j] = h[sub_index(&di, dims, support)][sub_index(&dj, dims, support)].clone();
            }
        }
    }
    out
}

/// Partial trace onto `keep` (strictly ascending).
fn reduce(m: &Mat, dims: &[usize], keep: &[usize]) -> Mat {
    let total = m.len();
    let dk: usize = keep.iter().map(|&s| dims[s]).product();
    let mut out = zeros(dk);
    for i in 0..total {
        let di = digits(i, dims);
        for j in 0..total {
            let dj = digits(j, dims);
            let traced_agree = (0..dims.len()).all(|s| keep.contains(&s) || di[s] == dj[s]);
            if traced_agree && !m[i][j].is_zero() {
                let (a, b) = (sub_index(&di, dims, keep), sub_index(&dj, dims, keep));
                out[a][b] = out[a][b].add(&m[i][j]);
            }
        }
    }
    out
}

fn mat_bytes(m: &Mat) -> Vec<u8> {
    let mut out = format!("{}:", m.len()).into_bytes();
    for row in m {
        for x in row {
            out.extend_from_slice(format!("{},{};", x.re, x.im).as_bytes());
        }
    }
    out
}

fn model_bytes(p: &ProductDefectPremises, rho0: &Mat) -> Vec<u8> {
    let mut out = format!(
        "dims={:?}|time={:?}|sigma={:?}|k={}|",
        p.local_dims, p.time_dependence, p.subsystem, p.declared_k
    )
    .into_bytes();
    for t in &p.terms {
        out.extend_from_slice(format!("term{:?}b={}|", t.support, t.norm_bound).as_bytes());
        if let Some(h) = to_mat(&t.operator, t.operator.rows()) {
            out.extend_from_slice(&mat_bytes(&h));
        }
    }
    out.extend_from_slice(b"|rho0=");
    out.extend_from_slice(&mat_bytes(rho0));
    out
}

// Origin: engine/crates_rs/core_quantum_physics/src/product_defect_bound.rs
// Claim: urn:core:crates_rs:core-quantum-physics:product-defect-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    fn qi(n: usize, e: &[(i64, i64)]) -> BasicMatrix<GaussianRat> {
        BasicMatrix::from_row_major(
            n,
            n,
            e.iter()
                .map(|&(a, b)| GaussianRat::from_ints(a, b))
                .collect(),
        )
        .expect("literal")
    }
    fn x() -> BasicMatrix<GaussianRat> {
        qi(2, &[(0, 0), (1, 0), (1, 0), (0, 0)])
    }
    fn z() -> BasicMatrix<GaussianRat> {
        qi(2, &[(1, 0), (0, 0), (0, 0), (-1, 0)])
    }
    fn ket0() -> BasicMatrix<GaussianRat> {
        qi(2, &[(1, 0), (0, 0), (0, 0), (0, 0)])
    }
    fn xx() -> BasicMatrix<GaussianRat> {
        let m = kron(&to_mat(&x(), 2).unwrap(), &to_mat(&x(), 2).unwrap());
        to_basic(&m).unwrap()
    }
    /// `n = i|00><11| − i|11><00|`.
    fn n_two_site() -> BasicMatrix<GaussianRat> {
        let mut e = vec![(0, 0); 16];
        e[3] = (0, 1);
        e[12] = (0, -1);
        qi(4, &e)
    }
    fn two_site() -> ProductDefectPremises {
        ProductDefectPremises {
            local_dims: vec![2, 2],
            terms: vec![SiteTerm {
                support: vec![0, 1],
                operator: xx(),
                norm_bound: ri(1),
            }],
            time_dependence: TimeDependence::Independent,
            initial: InitialState::Product(vec![ket0(), ket0()]),
            subsystem: vec![0, 1],
            declared_k: 2,
            coupling_bound: ri(1),
            normal_rate: ri(2),
            witness: Some(n_two_site()),
        }
    }
    use DefectNormalisation::{HalfTrace, RawTraceNorm};
    use RemainderCoefficient::{Strong, Weak};

    #[test]
    fn two_site_model_certifies_nu_two_and_replays_the_report_values() {
        let c = certify_product_defect_premises(&two_site()).unwrap();
        assert_eq!(c.normal_derivative(), &n_two_site());
        assert_eq!(c.witness_trace(), &ri(2));
        assert_eq!(c.k(), 2);
        assert_eq!(c.raw_coefficient(Strong).unwrap(), ri(24));
        assert_eq!(c.raw_coefficient(Weak).unwrap(), ri(24));
        let t = rq(1, 100);
        assert_eq!(
            c.lower_envelope(&t, Weak, RawTraceNorm).unwrap(),
            rq(11, 625)
        );
        assert_eq!(
            c.lower_envelope(&t, Strong, RawTraceNorm).unwrap(),
            rq(11, 625)
        );
        // Half-trace: (nu/2) t − 12 t².
        assert_eq!(c.lower_envelope(&t, Weak, HalfTrace).unwrap(), rq(11, 1250));
        let t_star = c.half_slope_endpoint(Weak).unwrap();
        assert_eq!(t_star, rq(1, 24));
        assert_eq!(
            c.half_slope_claim(&t_star, Weak, RawTraceNorm).unwrap(),
            rq(1, 24)
        );
        assert_eq!(
            c.lower_envelope(&t_star, Weak, RawTraceNorm).unwrap(),
            rq(1, 24)
        );
        // 2t*: the envelope is still a valid (zero) bound, but the half-slope claim is refused.
        let two = ri(2) * &t_star;
        assert_eq!(c.lower_envelope(&two, Weak, RawTraceNorm).unwrap(), ri(0));
        assert_eq!(
            c.half_slope_claim(&two, Weak, RawTraceNorm),
            Err(ProductDefectRefusal::OutsideHalfSlopeWindow)
        );
        assert_eq!(c.lower_envelope(&ri(0), Weak, RawTraceNorm).unwrap(), ri(0));
        assert_eq!(
            c.lower_envelope(&rq(-1, 100), Weak, RawTraceNorm),
            Err(ProductDefectRefusal::NegativeTime)
        );
        assert_eq!(c.incident_sums(), &[ri(1), ri(1)]);
    }

    #[test]
    fn half_trace_control_shows_raw_value_cannot_bound_trace_distance() {
        // Exact T(1/100) <= t + t² = 101/10000 (report control 5) is below the raw 11/625.
        let c = certify_product_defect_premises(&two_site()).unwrap();
        let raw = c.lower_envelope(&rq(1, 100), Weak, RawTraceNorm).unwrap();
        assert!(rq(101, 10000) < raw);
        assert!(c.lower_envelope(&rq(1, 100), Weak, HalfTrace).unwrap() <= rq(101, 10000));
    }

    #[test]
    fn inert_spectator_gives_the_three_site_fixture() {
        let mut p = two_site();
        p.local_dims = vec![2, 2, 2];
        p.initial = InitialState::Product(vec![ket0(), ket0(), ket0()]);
        p.subsystem = vec![0, 1, 2];
        p.declared_k = 3;
        let w = kron(
            &to_mat(&n_two_site(), 4).unwrap(),
            &to_mat(&ket0(), 2).unwrap(),
        );
        p.witness = Some(to_basic(&w).unwrap());
        let c = certify_product_defect_premises(&p).unwrap();
        assert_eq!(c.witness_trace(), &ri(2));
        let t = rq(1, 200);
        assert_eq!(
            c.lower_envelope(&t, Weak, RawTraceNorm).unwrap(),
            rq(173, 20000)
        );
        assert_eq!(
            c.lower_envelope(&t, Strong, RawTraceNorm).unwrap(),
            rq(11, 1250)
        );
        assert_eq!(c.half_slope_endpoint(Weak).unwrap(), rq(1, 54));
        assert_eq!(c.half_slope_endpoint(Strong).unwrap(), rq(1, 48));
        // Mutation: the k-semantics are site cardinality.
        p.declared_k = 4;
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::KSemanticsMismatch {
                declared: 4,
                actual: 3
            })
        );
    }

    #[test]
    fn local_tangent_has_zero_normal_rate_despite_a_nonzero_raw_derivative() {
        let mut p = two_site();
        p.terms = vec![SiteTerm {
            support: vec![0],
            operator: x(),
            norm_bound: ri(1),
        }];
        p.normal_rate = ri(0);
        p.witness = None;
        let c = certify_product_defect_premises(&p).unwrap();
        assert!(c.initial_derivative() != &to_basic(&zeros(4)).unwrap());
        assert_eq!(c.normal_derivative(), &to_basic(&zeros(4)).unwrap());
        assert_eq!(
            c.half_slope_endpoint(Weak),
            Err(ProductDefectRefusal::NoHalfSlopeWindow)
        );
        // Claiming a positive rate needs a witness, and no witness reaches it.
        p.normal_rate = ri(1);
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormalRateWitnessMissing)
        );
        p.witness = Some(to_basic(&scale_identity(4, &ri(1))).unwrap());
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormalRateBelowClaim { trace: ri(0) })
        );
    }

    #[test]
    fn understated_field_norm_is_refused_and_the_full_g_is_admitted() {
        let mut p = two_site();
        p.terms.push(SiteTerm {
            support: vec![0],
            operator: to_basic(&scale(
                &to_mat(&z(), 2).unwrap(),
                &GaussianRat::from_ints(100, 0),
            ))
            .unwrap(),
            norm_bound: ri(100),
        });
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::IncidentNormUnderbound {
                site: 0,
                sum: ri(101)
            })
        );
        p.coupling_bound = ri(101);
        let c = certify_product_defect_premises(&p).unwrap();
        // The field is tangent: the normal rate witness still gives 2.
        assert_eq!(c.witness_trace(), &ri(2));
        assert_eq!(c.half_slope_endpoint(Weak).unwrap(), rq(1, 24 * 101 * 101));
        // An understated per-term bound fails its PSD certificate.
        p.terms[1].norm_bound = ri(50);
        assert!(matches!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormBoundInvalid { term: 1, .. })
        ));
    }

    #[test]
    fn correlated_initial_state_is_refused() {
        // psi = c|00> + i s|11>, c = 9999/10001, s = 200/10001, 9999² + 200² = 10001².
        assert_eq!(9999i64 * 9999 + 200 * 200, 10001i64 * 10001);
        let (c, s) = (rq(9999, 10001), rq(200, 10001));
        let mut m = zeros(4);
        m[0][0] = GaussianRat::from_rational(&c * &c);
        m[3][3] = GaussianRat::from_rational(&s * &s);
        m[0][3] = GaussianRat {
            re: ri(0),
            im: -(&c * &s),
        };
        m[3][0] = GaussianRat {
            re: ri(0),
            im: &c * &s,
        };
        let mut p = two_site();
        p.initial = InitialState::Global(to_basic(&m).unwrap());
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NotProductInitial)
        );
        // A global product state passes the weaker F_sigma(0) = 0 premise.
        let prod = kron(&to_mat(&ket0(), 2).unwrap(), &to_mat(&ket0(), 2).unwrap());
        p.initial = InitialState::Global(to_basic(&prod).unwrap());
        assert!(certify_product_defect_premises(&p).is_ok());
    }

    #[test]
    fn host_admission_refusals() {
        let mut p = two_site();
        p.time_dependence = TimeDependence::Dependent;
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::TimeDependentHamiltonian)
        );
        let mut p = two_site();
        p.local_dims = vec![2, 2, 2];
        p.initial = InitialState::Product(vec![ket0(), ket0(), ket0()]);
        let xxx = kron(&to_mat(&xx(), 4).unwrap(), &to_mat(&x(), 2).unwrap());
        p.terms = vec![SiteTerm {
            support: vec![0, 1, 2],
            operator: to_basic(&xxx).unwrap(),
            norm_bound: ri(1),
        }];
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::UnsupportedLocality { term: 0, size: 3 })
        );
        let mut p = two_site();
        p.terms[0].operator = qi(2, &[(0, 0), (1, 0), (0, 0), (0, 0)]);
        p.terms[0].support = vec![0];
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NonHermitianTerm { term: 0 })
        );
        let mut p = two_site();
        p.terms[0].support = vec![1, 0];
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::BadSupport { term: 0 })
        );
        let mut p = two_site();
        p.initial = InitialState::Product(vec![qi(2, &[(2, 0), (0, 0), (0, 0), (-1, 0)]), ket0()]);
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::InvalidDensity(Some(0)))
        );
        p.initial = InitialState::Product(vec![qi(2, &[(2, 0), (0, 0), (0, 0), (0, 0)]), ket0()]);
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::InvalidDensity(Some(0)))
        );
        let mut p = two_site();
        p.local_dims = vec![];
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::MissingHostModel)
        );
        let mut p = two_site();
        p.local_dims = vec![2; 7];
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::ResourceLimit(128))
        );
        let mut p = two_site();
        p.coupling_bound = ri(-1);
        assert!(certify_product_defect_premises(&p).is_err());
    }

    #[test]
    fn witness_and_parameter_mutations_are_refused() {
        let mut p = two_site();
        p.normal_rate = ri(2) + rq(1, 1000);
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormalRateBelowClaim { trace: ri(2) })
        );
        let mut p = two_site();
        p.witness = Some(
            to_basic(&scale(
                &to_mat(&n_two_site(), 4).unwrap(),
                &GaussianRat::from_ints(2, 0),
            ))
            .unwrap(),
        );
        p.normal_rate = ri(4);
        assert!(matches!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormalRateWitnessInvalid(_))
        ));
        let mut p = two_site();
        p.witness = Some(ket0());
        assert!(matches!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NormalRateWitnessInvalid(_))
        ));
        let mut p = two_site();
        p.normal_rate = ri(-1);
        assert_eq!(
            certify_product_defect_premises(&p),
            Err(ProductDefectRefusal::NegativeNormalRate)
        );
        // Digests move with the model and with the witness parameters.
        let base = certify_product_defect_premises(&two_site()).unwrap();
        let mut p = two_site();
        p.coupling_bound = ri(2);
        let c = certify_product_defect_premises(&p).unwrap();
        assert_eq!(base.model_digest(), c.model_digest());
        assert_ne!(base.witness_digest(), c.witness_digest());
        let mut p = two_site();
        p.terms[0].norm_bound = ri(2);
        p.coupling_bound = ri(2);
        let c = certify_product_defect_premises(&p).unwrap();
        assert_ne!(base.model_digest(), c.model_digest());
        assert_eq!(base.source_digest(), c.source_digest());
    }

    #[test]
    fn weak_relaxation_holds_exactly_for_k_at_least_two() {
        for k in 1..=8usize {
            let strong = raw_coefficient(k, Strong).unwrap();
            let gap_formula = Rational::from_integer((2 * k as i64 * (k as i64 - 2)).into());
            match raw_coefficient(k, Weak) {
                Ok(weak) => {
                    assert!(k >= 2);
                    assert_eq!(&weak - &strong, gap_formula);
                    assert!(weak >= strong);
                }
                Err(e) => {
                    assert_eq!(
                        (k, e),
                        (1, ProductDefectRefusal::WeakCoefficientNeedsTwoSites)
                    );
                    assert_eq!(ri(6) - &strong, ri(-2));
                }
            }
        }
        // k = 1: the residual vanishes identically, so the certified rate is zero.
        let mut p = two_site();
        p.subsystem = vec![0];
        p.declared_k = 1;
        p.normal_rate = ri(0);
        p.witness = None;
        let c = certify_product_defect_premises(&p).unwrap();
        assert_eq!(c.normal_derivative(), &to_basic(&zeros(2)).unwrap());
        assert_eq!(
            c.lower_envelope(&rq(1, 10), Weak, RawTraceNorm),
            Err(ProductDefectRefusal::WeakCoefficientNeedsTwoSites)
        );
        assert_eq!(
            c.lower_envelope(&rq(1, 10), Strong, RawTraceNorm).unwrap(),
            rq(-8, 100)
        );
    }
}
