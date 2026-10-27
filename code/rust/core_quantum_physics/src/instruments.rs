//! Quantum instruments, positive operator-valued measurements, and exact Lüders updates.
//!
//! Bound to spectral evidence: projective/Lüders instruments require a paid
//! spectral certificate (diagonal exact decomposition). Without it, construction
//! fails closed.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen. Finite rational face.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::{One, Zero};
use core_number_theory::cyclotomic::GaussianRat;

use crate::hermitian_spectral::{
    spectral_decompose, HermitianMatrix, ScalarCarrier, SpectralDecomposition,
};
use core_number_theory::rational::{ri, sqrt_exact, Rational};

/// Fence string.
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; instruments bound to spectral evidence.";

/// Exact non-negative rational probability / weight.
pub type Q = Rational;

/// Error for instrument construction / application.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum InstrumentError {
    Limits(core_kernel::resource_limits::ResourceError),
    EmptyEffects,
    DimMismatch { expected: usize, actual: usize },
    NotPositiveSemidefiniteHint,
    NotResolutionOfIdentity,
    MissingSpectralEvidence,
    Spectral(String),
    NonNormalizedState,
    ChannelNotTracePreserving,
    NonSquareRoot,
}

/// Spectral evidence required before projective / Lüders instruments mint.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpectralEvidence {
    /// Human / machine id of the spectral certificate.
    pub certificate_id: String,
    /// Hilbert dimension.
    pub dim: usize,
    /// Eigenvalues (exact rationals for real-symmetric diagonal case).
    pub eigenvalues: Vec<Q>,
    /// Whether hypotheses were paid (hermitian + finite_n + exact carrier).
    pub hypotheses_paid: bool,
}

impl SpectralEvidence {
    /// Build from a paid spectral decomposition.
    pub fn from_decomposition(
        certificate_id: impl Into<String>,
        decomp: &SpectralDecomposition,
    ) -> Result<Self, InstrumentError> {
        if !decomp.hypotheses.all_paid() {
            return Err(InstrumentError::MissingSpectralEvidence);
        }
        if decomp.authority_effect != crate::hermitian_spectral::SpectralAuthorityTag::None {
            return Err(InstrumentError::MissingSpectralEvidence);
        }
        let eigenvalues = decomp.eigenvalues.iter().map(|z| z.re.clone()).collect();
        Ok(Self {
            certificate_id: certificate_id.into(),
            dim: decomp.n,
            eigenvalues,
            hypotheses_paid: true,
        })
    }

    pub fn require_paid(&self) -> Result<(), InstrumentError> {
        if self.hypotheses_paid && self.dim >= 1 && self.eigenvalues.len() == self.dim {
            Ok(())
        } else {
            Err(InstrumentError::MissingSpectralEvidence)
        }
    }
}

/// One POVM effect E_k (diagonal PSD face).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PovmEffect {
    pub outcome_id: String,
    /// Diagonal entries (length = dim).
    pub diagonal: Vec<Q>,
}

/// Finite POVM {E_k} with ∑ E_k = I (exact rational diagonal face).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Povm {
    pub dim: usize,
    pub effects: Vec<PovmEffect>,
    pub label: String,
}

impl Povm {
    fn validate_effects_and_resolution(
        dim: usize,
        effects: &[PovmEffect],
    ) -> Result<(), InstrumentError> {
        for e in effects {
            if e.diagonal.len() != dim {
                return Err(InstrumentError::DimMismatch {
                    expected: dim,
                    actual: e.diagonal.len(),
                });
            }
            if e.diagonal.iter().any(|x| *x < Zero::zero()) {
                return Err(InstrumentError::NotPositiveSemidefiniteHint);
            }
        }
        for i in 0..dim {
            let mut s = Q::zero();
            for e in effects {
                s += &e.diagonal[i];
            }
            if s != Q::one() {
                return Err(InstrumentError::NotResolutionOfIdentity);
            }
        }
        Ok(())
    }

    pub fn try_new(
        dim: usize,
        effects: Vec<PovmEffect>,
        label: impl Into<String>,
    ) -> Result<Self, InstrumentError> {
        if dim == 0 || effects.is_empty() {
            return Err(InstrumentError::EmptyEffects);
        }
        core_kernel::resource_limits::OperationLimits::default()
            .check_dense_matrix(dim, dim, std::mem::size_of::<Rational>())
            .map_err(InstrumentError::Limits)?;
        core_kernel::resource_limits::OperationLimits::default()
            .check_operator_count(effects.len())
            .map_err(InstrumentError::Limits)?;
        Self::validate_effects_and_resolution(dim, &effects)?;
        Ok(Self {
            dim,
            effects,
            label: label.into(),
        })
    }

    /// Computational-basis projective measurement (requires spectral evidence).
    pub fn computational_basis(
        evidence: &SpectralEvidence,
        label: impl Into<String>,
    ) -> Result<Self, InstrumentError> {
        evidence.require_paid()?;
        let dim = evidence.dim;
        let mut effects = Vec::with_capacity(dim);
        for k in 0..dim {
            let mut diag = vec![Q::zero(); dim];
            diag[k] = Q::one();
            effects.push(PovmEffect {
                outcome_id: format!("basis_{k}"),
                diagonal: diag,
            });
        }
        Self::try_new(dim, effects, label)
    }
}

/// Kraus operator on the diagonal face.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagonalKraus {
    pub dim: usize,
    pub ops: Vec<Vec<Q>>,
    pub label: String,
}

impl DiagonalKraus {
    /// K_k = √E_k when diagonals are perfect-square rationals.
    pub fn from_povm_sqrt(povm: &Povm, label: impl Into<String>) -> Result<Self, InstrumentError> {
        let mut ops = Vec::new();
        for e in &povm.effects {
            let mut diag = Vec::with_capacity(povm.dim);
            for p in &e.diagonal {
                diag.push(exact_sqrt_nonneg(p)?);
            }
            ops.push(diag);
        }
        Ok(Self {
            dim: povm.dim,
            ops,
            label: label.into(),
        })
    }
}

fn exact_sqrt_nonneg(q: &Rational) -> Result<Rational, InstrumentError> {
    if q < &Rational::zero() {
        return Err(InstrumentError::NotPositiveSemidefiniteHint);
    }
    sqrt_exact(q).ok_or(InstrumentError::NonSquareRoot)
}

/// Lüders instrument bound to spectral evidence.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LudersInstrument {
    pub povm: Povm,
    pub kraus: DiagonalKraus,
    pub spectral: SpectralEvidence,
    pub label: String,
}

impl LudersInstrument {
    pub fn try_new(
        spectral: SpectralEvidence,
        povm: Povm,
        label: impl Into<String>,
    ) -> Result<Self, InstrumentError> {
        spectral.require_paid()?;
        if povm.dim != spectral.dim {
            return Err(InstrumentError::DimMismatch {
                expected: spectral.dim,
                actual: povm.dim,
            });
        }
        let kraus = DiagonalKraus::from_povm_sqrt(&povm, "luders_kraus")?;
        Ok(Self {
            povm,
            kraus,
            spectral,
            label: label.into(),
        })
    }

    pub fn apply_diagonal_state(
        &self,
        populations: &[Q],
    ) -> Result<LudersOutcome, InstrumentError> {
        if populations.len() != self.povm.dim {
            return Err(InstrumentError::DimMismatch {
                expected: self.povm.dim,
                actual: populations.len(),
            });
        }
        if populations.iter().any(|p| *p < Zero::zero()) {
            return Err(InstrumentError::NonNormalizedState);
        }
        let total: Q = populations.iter().cloned().sum();
        if total != Q::one() {
            return Err(InstrumentError::NonNormalizedState);
        }

        let mut outcome_probs = Vec::new();
        let mut posteriors = Vec::new();
        for effect in &self.povm.effects {
            let mut pk = Q::zero();
            for i in 0..self.povm.dim {
                pk += &effect.diagonal[i] * &populations[i];
            }
            outcome_probs.push((effect.outcome_id.clone(), pk.clone()));
            if pk.is_zero() {
                posteriors.push(None);
                continue;
            }
            let mut post = vec![Q::zero(); self.povm.dim];
            for i in 0..self.povm.dim {
                post[i] = &effect.diagonal[i] * &populations[i] / &pk;
            }
            posteriors.push(Some(post));
        }
        Ok(LudersOutcome {
            outcome_probs,
            posteriors,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LudersOutcome {
    pub outcome_probs: Vec<(String, Q)>,
    pub posteriors: Vec<Option<Vec<Q>>>,
}

/// Channel composition for diagonal Kraus instruments.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InstrumentChannel {
    pub dim: usize,
    pub kraus: DiagonalKraus,
    pub spectral_binding: Option<String>,
    pub label: String,
}

impl InstrumentChannel {
    pub fn from_luders(inst: &LudersInstrument, label: impl Into<String>) -> Self {
        Self {
            dim: inst.povm.dim,
            kraus: inst.kraus.clone(),
            spectral_binding: Some(inst.spectral.certificate_id.clone()),
            label: label.into(),
        }
    }

    fn verify_trace_preserving(dim: usize, ops: &[Vec<Q>]) -> Result<(), InstrumentError> {
        for i in 0..dim {
            let mut s = Q::zero();
            for op in ops {
                s += &op[i] * &op[i];
            }
            if s != Q::one() {
                return Err(InstrumentError::ChannelNotTracePreserving);
            }
        }
        Ok(())
    }

    fn combine_spectral_bindings(
        left: &Option<String>,
        right: &Option<String>,
    ) -> Option<String> {
        match (left, right) {
            (Some(a), Some(b)) => Some(format!("{a};{b}")),
            (Some(a), None) => Some(a.clone()),
            (None, Some(b)) => Some(b.clone()),
            (None, None) => None,
        }
    }

    /// Compose `next ∘ self` (apply self then next).
    pub fn compose(&self, next: &Self) -> Result<Self, InstrumentError> {
        if self.dim != next.dim {
            return Err(InstrumentError::DimMismatch {
                expected: self.dim,
                actual: next.dim,
            });
        }
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let count = limits
            .checked_product(self.kraus.ops.len(), next.kraus.ops.len())
            .map_err(InstrumentError::Limits)?;
        limits
            .check_operator_count(count)
            .map_err(InstrumentError::Limits)?;
        let mut ops = Vec::new();
        for l in &next.kraus.ops {
            for m in &self.kraus.ops {
                let mut d = vec![Q::zero(); self.dim];
                for i in 0..self.dim {
                    d[i] = &l[i] * &m[i];
                }
                ops.push(d);
            }
        }
        Self::verify_trace_preserving(self.dim, &ops)?;
        let binding = Self::combine_spectral_bindings(&self.spectral_binding, &next.spectral_binding);
        Ok(Self {
            dim: self.dim,
            kraus: DiagonalKraus {
                dim: self.dim,
                ops,
                label: format!("{}∘{}", next.label, self.label),
            },
            spectral_binding: binding,
            label: format!("compose({},{})", self.label, next.label),
        })
    }
}

/// Paid spectral evidence for diagonal eigenvalues 0..n-1 (computational shell).
pub fn paid_computational_spectral(dim: usize) -> Result<SpectralEvidence, InstrumentError> {
    if dim == 0 {
        return Err(InstrumentError::EmptyEffects);
    }
    let diag: Vec<Rational> = (0..dim).map(|i| Rational::from_integer(i.into())).collect();
    let mat = HermitianMatrix::try_diagonal_rational(&diag, ScalarCarrier::Rational)
        .map_err(|e| InstrumentError::Spectral(format!("{e:?}")))?;
    let decomp =
        spectral_decompose(&mat).map_err(|e| InstrumentError::Spectral(format!("{e:?}")))?;
    SpectralEvidence::from_decomposition(format!("spec:comp:{dim}"), &decomp)
}

/// Exact full-matrix POVMs and instruments over Q(i). The diagonal presentation
/// above is a finite classical restriction; none of its claim flags is used here.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactInstrumentError {
    #[error("empty outcomes or effects")]
    Empty,
    #[error("wrong shape or outcome index")]
    Shape,
    #[error("effect is not Hermitian positive semidefinite")]
    NotPositive,
    #[error("effects do not sum to the identity")]
    Incomplete,
    #[error("declared effect square root does not check")]
    BadRoot,
    #[error("projective effects do not commute")]
    Noncommuting,
    #[error("zero probability outcome has no conditional state")]
    ZeroProbability,
    #[error("operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error("density: {0}")]
    Density(#[from] crate::density_matrix::ExactDensityError),
    #[error("channel: {0}")]
    Channel(#[from] crate::exact_channel::ExactChannelError),
    #[error("Hermitian algebra: {0}")]
    Hermitian(#[from] crate::exact_hermitian::ExactHermitianError),
    #[error("declared spectrum: {0:?}")]
    Spectrum(crate::exact_hermitian::SpectrumError),
}

/// Positive Hermitian effects E_k with sum E_k=I, checked without tolerance.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactPovm {
    dim: usize,
    effects: Vec<crate::exact_operator::ExactOperator>,
}
impl ExactPovm {
    fn validate_single_effect(
        effect: BasicMatrix<GaussianRat>,
        dim: usize,
    ) -> Result<crate::exact_operator::ExactOperator, ExactInstrumentError> {
        let op = crate::exact_operator::ExactOperator::try_new(effect)?;
        if op.shape() != (dim, dim) {
            return Err(ExactInstrumentError::Shape);
        }
        if !crate::exact_hermitian::is_psd(op.as_matrix())? {
            return Err(ExactInstrumentError::NotPositive);
        }
        Ok(op)
    }

    pub fn try_new(effects: Vec<BasicMatrix<GaussianRat>>) -> Result<Self, ExactInstrumentError> {
        use crate::exact_operator::ExactOperator;
        core_kernel::resource_limits::OperationLimits::default()
            .check_operator_count(effects.len())
            .map_err(crate::exact_channel::ExactChannelError::from)?;
        let dim = effects.first().ok_or(ExactInstrumentError::Empty)?.rows();
        let mut sum = ExactOperator::zeros(dim, dim)?;
        let mut checked = Vec::new();
        for effect in effects {
            let op = Self::validate_single_effect(effect, dim)?;
            sum = sum.add(&op)?;
            checked.push(op);
        }
        if sum != ExactOperator::identity(dim)? {
            return Err(ExactInstrumentError::Incomplete);
        }
        Ok(Self {
            dim,
            effects: checked,
        })
    }
    pub fn dim(&self) -> usize {
        self.dim
    }
    pub fn effects(&self) -> &[crate::exact_operator::ExactOperator] {
        &self.effects
    }
    pub fn probabilities(
        &self,
        rho: &crate::density_matrix::ExactDensityMatrix,
    ) -> Result<Vec<Rational>, ExactInstrumentError> {
        self.effects
            .iter()
            .map(|e| rho.expectation(e).map_err(ExactInstrumentError::Density))
            .collect()
    }
    /// Declared positive roots S_k must be Hermitian PSD and satisfy S_k^2=E_k.
    /// General irrational roots are refused unless provided in the coefficient field.
    pub fn luders(
        &self,
        roots: Vec<BasicMatrix<GaussianRat>>,
    ) -> Result<ExactInstrument, ExactInstrumentError> {
        if roots.len() != self.effects.len() {
            return Err(ExactInstrumentError::Shape);
        }
        let mut outcomes = Vec::new();
        for (root, effect) in roots.into_iter().zip(&self.effects) {
            let op = crate::exact_operator::ExactOperator::try_new(root.clone())?;
            if op.shape() != effect.shape()
                || !crate::exact_hermitian::is_psd(op.as_matrix())?
                || op.mul(&op)? != *effect
            {
                return Err(ExactInstrumentError::BadRoot);
            }
            outcomes.push(vec![(ri(1), root)]);
        }
        ExactInstrument::try_new(self.dim, self.dim, outcomes)
    }
}

/// A quantum instrument with weighted Kraus operators per classical outcome.
/// Completeness is checked by the common exact CPTP implementation; positivity
/// then implies every individual outcome is trace non-increasing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactInstrument {
    dim_in: usize,
    dim_out: usize,
    outcomes: Vec<Vec<(Rational, BasicMatrix<GaussianRat>)>>,
    povm: ExactPovm,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactInstrumentOutcome {
    pub probability: Rational,
    pub state: Option<crate::density_matrix::ExactDensityMatrix>,
}
impl ExactInstrument {
    fn build_outcome_effect(
        dim_in: usize,
        terms: &[(Rational, BasicMatrix<GaussianRat>)],
    ) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        use crate::exact_operator::ExactOperator;
        let mut effect = ExactOperator::zeros(dim_in, dim_in)?;
        for (w, k) in terms {
            let op = ExactOperator::try_new(k.clone())?;
            effect = effect.add(&op.dagger()?.mul(&op)?.scale_rat(w)?)?;
        }
        Ok(effect.into_matrix())
    }

    pub fn try_new(
        dim_in: usize,
        dim_out: usize,
        outcomes: Vec<Vec<(Rational, BasicMatrix<GaussianRat>)>>,
    ) -> Result<Self, ExactInstrumentError> {
        if outcomes.is_empty() || outcomes.iter().any(Vec::is_empty) {
            return Err(ExactInstrumentError::Empty);
        }
        crate::exact_channel::ExactKrausChannel::try_weighted(
            dim_in,
            dim_out,
            outcomes.iter().flatten().cloned().collect(),
            "instrument",
        )?;
        let mut effects = Vec::new();
        for terms in &outcomes {
            effects.push(Self::build_outcome_effect(dim_in, terms)?);
        }
        let povm = ExactPovm::try_new(effects)?;
        Ok(Self {
            dim_in,
            dim_out,
            outcomes,
            povm,
        })
    }
    pub fn povm(&self) -> &ExactPovm {
        &self.povm
    }
    pub fn num_outcomes(&self) -> usize {
        self.outcomes.len()
    }
    pub fn unselective(
        &self,
    ) -> Result<crate::exact_channel::ExactKrausChannel, ExactInstrumentError> {
        Ok(crate::exact_channel::ExactKrausChannel::try_weighted(
            self.dim_in,
            self.dim_out,
            self.outcomes.iter().flatten().cloned().collect(),
            "unselective instrument",
        )?)
    }

    fn apply_outcome_terms(
        dim_out: usize,
        rho: &crate::density_matrix::ExactDensityMatrix,
        terms: &[(Rational, BasicMatrix<GaussianRat>)],
    ) -> Result<crate::exact_operator::ExactOperator, ExactInstrumentError> {
        use crate::exact_operator::ExactOperator;
        let mut out = ExactOperator::zeros(dim_out, dim_out)?;
        for (w, k) in terms {
            let op = ExactOperator::try_new(k.clone())?;
            out = out.add(
                &op.mul(rho.as_operator())?
                    .mul(&op.dagger()?)?
                    .scale_rat(w)?,
            )?;
        }
        Ok(out)
    }

    pub fn outcome(
        &self,
        rho: &crate::density_matrix::ExactDensityMatrix,
        index: usize,
    ) -> Result<ExactInstrumentOutcome, ExactInstrumentError> {
        let terms = self
            .outcomes
            .get(index)
            .ok_or(ExactInstrumentError::Shape)?;
        if rho.dim() != self.dim_in {
            return Err(ExactInstrumentError::Shape);
        }
        let out = Self::apply_outcome_terms(self.dim_out, rho, terms)?;
        let probability = out.trace()?.re;
        let state = if probability.is_zero() {
            None
        } else {
            Some(crate::density_matrix::ExactDensityMatrix::from_unnormalized(out)?.0)
        };
        Ok(ExactInstrumentOutcome { probability, state })
    }

    fn build_register_kraus_op(
        rows: usize,
        dim_in: usize,
        dim_out: usize,
        count: usize,
        outcome: usize,
        k: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, ExactInstrumentError> {
        let mut op = linear_algebra::exact_field::matrix::zeros_with_limits(
            rows,
            dim_in,
            crate::exact_hermitian::exact_limits(),
        )
        .map_err(crate::exact_operator::OperatorError::Algebra)?;
        for b in 0..dim_out {
            for a in 0..dim_in {
                let val = k
                    .get_ref(b, a)
                    .map_err(|e| crate::exact_operator::OperatorError::Algebra(e.into()))?
                    .clone();
                op.set(b * count + outcome, a, val)
                    .map_err(|e| crate::exact_operator::OperatorError::Algebra(e.into()))?;
            }
        }
        Ok(op)
    }

    /// Channel retaining the measured system and an explicit classical outcome
    /// register, with basis order (system, outcome).
    pub fn classical_register_channel(
        &self,
    ) -> Result<crate::exact_channel::ExactKrausChannel, ExactInstrumentError> {
        let count = self.outcomes.len();
        let rows = core_kernel::resource_limits::OperationLimits::default()
            .checked_product(self.dim_out, count)
            .map_err(crate::exact_channel::ExactChannelError::from)?;
        core_kernel::resource_limits::OperationLimits::default()
            .check_hilbert_dim(rows)
            .map_err(crate::exact_channel::ExactChannelError::from)?;
        let mut terms = Vec::new();
        for (outcome, ops) in self.outcomes.iter().enumerate() {
            for (w, k) in ops {
                let op = Self::build_register_kraus_op(
                    rows,
                    self.dim_in,
                    self.dim_out,
                    count,
                    outcome,
                    k,
                )?;
                terms.push((w.clone(), op));
            }
        }
        Ok(crate::exact_channel::ExactKrausChannel::try_weighted(
            self.dim_in,
            rows,
            terms,
            "classical instrument register",
        )?)
    }
}

/// Spectral projective measurement, constructed from verified rational-spectrum
/// Lagrange projectors. Distinct effects are orthogonal and repeatable exactly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactProjectiveMeasurement {
    eigenvalues: Vec<Rational>,
    povm: ExactPovm,
}
impl ExactProjectiveMeasurement {
    pub fn from_observable(
        h: &BasicMatrix<GaussianRat>,
        spectrum: &[Rational],
    ) -> Result<Self, ExactInstrumentError> {
        let resolution = crate::exact_hermitian::spectral_resolution(h, spectrum)
            .map_err(ExactInstrumentError::Spectrum)?;
        let povm = ExactPovm::try_new(resolution.projectors().to_vec())?;
        Ok(Self {
            eigenvalues: resolution.eigenvalues().to_vec(),
            povm,
        })
    }
    pub fn povm(&self) -> &ExactPovm {
        &self.povm
    }
    pub fn eigenvalues(&self) -> &[Rational] {
        &self.eigenvalues
    }
    pub fn instrument(&self) -> Result<ExactInstrument, ExactInstrumentError> {
        self.povm.luders(
            self.povm
                .effects
                .iter()
                .map(|p| p.as_matrix().clone())
                .collect(),
        )
    }
    /// Joint projective measurement exists exactly when every pair of effects
    /// commutes; products then form a positive orthogonal resolution.
    pub fn joint(&self, other: &Self) -> Result<ExactPovm, ExactInstrumentError> {
        if self.povm.dim != other.povm.dim {
            return Err(ExactInstrumentError::Shape);
        }
        let mut effects = Vec::new();
        for p in &self.povm.effects {
            for q in &other.povm.effects {
                if p.mul(q)? != q.mul(p)? {
                    return Err(ExactInstrumentError::Noncommuting);
                }
                effects.push(p.mul(q)?.into_matrix());
            }
        }
        ExactPovm::try_new(effects)
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/instruments.rs
// Claim: urn:core:crates_rs:core-quantum-physics:instruments:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn paid_dim2() -> SpectralEvidence {
        paid_computational_spectral(2).expect("paid d2")
    }

    #[test]
    fn instruments_require_spectral_evidence() {
        let mut unpaid = paid_dim2();
        unpaid.hypotheses_paid = false;
        let err = Povm::computational_basis(&unpaid, "cb");
        assert_eq!(err, Err(InstrumentError::MissingSpectralEvidence));
    }

    #[test]
    fn instruments_computational_basis_povm() {
        let ev = paid_dim2();
        let povm = Povm::computational_basis(&ev, "cb").expect("povm");
        assert_eq!(povm.effects.len(), 2);
        assert_eq!(povm.dim, 2);
    }

    #[test]
    fn instruments_luders_on_pure_basis() {
        let ev = paid_dim2();
        let povm = Povm::computational_basis(&ev, "cb").unwrap();
        let lud = LudersInstrument::try_new(ev, povm, "L").unwrap();
        let out = lud
            .apply_diagonal_state(&[Q::one(), Q::zero()])
            .expect("apply");
        assert_eq!(out.outcome_probs[0].1, Q::one());
        assert_eq!(out.outcome_probs[1].1, Q::zero());
        assert_eq!(out.posteriors[0].as_ref().unwrap()[0], Q::one());
    }

    #[test]
    fn instruments_channel_compose_tp() {
        let ev = paid_dim2();
        let povm = Povm::computational_basis(&ev.clone(), "cb").unwrap();
        let lud = LudersInstrument::try_new(ev, povm, "L").unwrap();
        let ch = InstrumentChannel::from_luders(&lud, "A");
        let composed = ch.compose(&ch).expect("compose TP");
        assert_eq!(composed.dim, 2);
        assert!(composed.spectral_binding.is_some());
    }

    #[test]
    fn instruments_authority_none() {
        assert!(AUTHORITY_FENCE.contains("AuthorityEffect None"));
    }
}
