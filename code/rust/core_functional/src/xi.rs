use nalgebra::{DMatrix, DVector};
use num_complex::Complex64;
use num_traits::{Signed, Zero};
use core_kernel::Exact;
use serde::{Deserialize, Serialize};

/// Conditional density lift ρ(v) as a density matrix.
///
/// This is a scale-invariant representation of the vector v:
/// - `ψ(v)_e = sign(v_e) · √(|v_e|/‖v‖₁)`
/// - `ρ(v) = |ψ⟩⟨ψ|` (rank-1 density matrix)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DensityLift {
    pub density_matrix: DMatrix<Complex64>,
    pub state_vector: DVector<Complex64>,
    pub total_mass: f64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum XiValidity {
    Valid,
    SaturationFailed,
    DensityLiftUndefined,
    NonFiniteInput,
    FirewallNotChecked,
}

/// Evaluator-owned magnitude. A wire scalar cannot construct this result.
///
/// ```compile_fail
/// use core_functional::xi::XiResult;
/// let forged: XiResult = serde_json::from_str("{}").unwrap();
/// ```
/// ```compile_fail
/// use core_functional::xi::XiResult;
/// fn overwrite(result: &mut XiResult) { result.value = 4.0; }
/// ```
#[derive(Debug, Clone, Serialize)]
pub struct XiResult {
    value: f64,
    validity: XiValidity,
    primal_density: Option<DensityLift>,
    dual_density: Option<DensityLift>,
    saturation_verified: bool,
    #[serde(skip)]
    primal_residual: Vec<Exact>,
    #[serde(skip)]
    dual_witness: Vec<Exact>,
    #[serde(skip)]
    phi1_value: Exact,
}

impl XiResult {
    pub fn value(&self) -> f64 {
        self.value
    }
    pub fn validity(&self) -> XiValidity {
        self.validity
    }
    pub fn primal_density(&self) -> Option<&DensityLift> {
        self.primal_density.as_ref()
    }
    pub fn dual_density(&self) -> Option<&DensityLift> {
        self.dual_density.as_ref()
    }
    pub fn saturation_verified(&self) -> bool {
        self.saturation_verified
    }
}

#[derive(Debug, Clone, Serialize)]
enum XiComputationKind {
    ExactZero,
    ValidTieBreaker(XiResult),
    Invalid(XiValidity),
}

/// Outcome constructed only by the canonical evaluator. Serialization is a
/// display projection; it cannot deserialize back into evaluated evidence.
///
/// ```compile_fail
/// use core_functional::xi::XiComputation;
/// let forged: XiComputation = serde_json::from_str("\"ExactZero\"").unwrap();
/// ```
#[derive(Debug, Clone, Serialize)]
#[serde(transparent)]
pub struct XiComputation {
    kind: XiComputationKind,
}

impl XiComputation {
    pub fn is_exact_zero(&self) -> bool {
        matches!(self.kind, XiComputationKind::ExactZero)
    }
    pub fn result(&self) -> Option<&XiResult> {
        match &self.kind {
            XiComputationKind::ValidTieBreaker(result) => Some(result),
            _ => None,
        }
    }
    pub fn value(&self) -> Option<f64> {
        match &self.kind {
            XiComputationKind::ExactZero => Some(0.0),
            XiComputationKind::ValidTieBreaker(result) => Some(result.value),
            XiComputationKind::Invalid(_) => None,
        }
    }
    pub fn matches_phi1(&self, phi1: &crate::phi1::VerifiedExactPhi1) -> bool {
        match &self.kind {
            XiComputationKind::ExactZero => phi1.value().is_zero(),
            XiComputationKind::ValidTieBreaker(result) => {
                &result.phi1_value == phi1.value()
                    && result.primal_residual == phi1.primal_residual()
                    && result.dual_witness == phi1.dual_witness()
            }
            XiComputationKind::Invalid(_) => false,
        }
    }
}

#[derive(Debug, thiserror::Error)]
pub enum XiError {
    #[error("non-finite vector entries in input")]
    NonFiniteInput,
    #[error("zero mass in density lift")]
    ZeroMass,
    #[error("density-lift tolerance must be finite and nonnegative")]
    InvalidTolerance,
}

/// Ξ: Primal-dual density tie-breaker diagnostic.
///
/// Computes the trace distance between conditional density lifts.
pub struct XiFunctional;

impl XiFunctional {
    fn build_density_state_vector(
        vector: &DVector<f64>,
        total_mass: f64,
    ) -> Result<DVector<Complex64>, XiError> {
        // Compute the conditional state vector: ψ_e = sign(v_e) · √(|v_e|/M)
        let n = vector.len();
        let mut state_vector = DVector::from_element(n, Complex64::new(0.0, 0.0));

        for i in 0..n {
            let v_i = vector[i];
            let sign = if v_i >= 0.0 { 1.0 } else { -1.0 };
            let magnitude = (v_i.abs() / total_mass).sqrt();
            if !magnitude.is_finite() {
                return Err(XiError::NonFiniteInput);
            }
            state_vector[i] = Complex64::new(sign * magnitude, 0.0);
        }
        Ok(state_vector)
    }

    /// Compute the conditional density lift ρ(v) for a vector v.
    pub fn compute_density_lift(
        vector: &DVector<f64>,
        tolerance: f64,
    ) -> Result<DensityLift, XiError> {
        // A non-finite or negative tolerance makes `mass <= tolerance` false
        // for a zero vector, and the following division then yields NaN.
        if !tolerance.is_finite() || tolerance < 0.0 {
            return Err(XiError::InvalidTolerance);
        }
        if vector.iter().any(|&x| !x.is_finite()) {
            return Err(XiError::NonFiniteInput);
        }

        // Compute total mass M(v) = ‖v‖₁
        let total_mass: f64 = vector.iter().map(|&x| x.abs()).sum();
        if !total_mass.is_finite() {
            return Err(XiError::NonFiniteInput);
        }

        // If mass is zero, the lift is undefined
        if total_mass <= tolerance {
            return Err(XiError::ZeroMass);
        }

        let state_vector = Self::build_density_state_vector(vector, total_mass)?;

        // Compute the density matrix: ρ = |ψ⟩⟨ψ|
        let n = vector.len();
        let mut density_matrix = DMatrix::from_element(n, n, Complex64::new(0.0, 0.0));
        for i in 0..n {
            for j in 0..n {
                density_matrix[(i, j)] = state_vector[i] * state_vector[j].conj();
            }
        }

        Ok(DensityLift {
            density_matrix,
            state_vector,
            total_mass,
        })
    }

    /// Compute the trace distance between two pure-state density vectors.
    ///
    /// For rank-1 pure-state density matrices `ρ_ψ = |ψ⟩⟨ψ|` and `ρ_φ = |φ⟩⟨φ|`,
    /// the half-normalized trace distance is:
    /// ```text
    /// D(ρ_ψ, ρ_φ) = sqrt(1 - |⟨ψ|φ⟩|²)
    /// ```
    /// Unhalved trace norm is:
    /// ```text
    /// 2 * sqrt(1 - |⟨ψ|φ⟩|²)
    /// ```
    pub fn pure_state_trace_distance(
        psi: &DVector<Complex64>,
        phi: &DVector<Complex64>,
        half_normalized: bool,
    ) -> f64 {
        let finite_state = |state: &DVector<Complex64>| {
            state
                .iter()
                .all(|entry| entry.re.is_finite() && entry.im.is_finite())
        };
        // Zip would drop the longer tail and report a distance for a different pair.
        if psi.len() != phi.len() || !finite_state(psi) || !finite_state(phi) {
            return f64::NAN;
        }
        // Compute inner product ⟨ψ|φ⟩
        let inner_product: Complex64 = psi.iter().zip(phi.iter()).map(|(p, d)| p.conj() * d).sum();
        let overlap = inner_product.norm_sqr(); // |⟨ψ|φ⟩|²

        // Cap overlap to 1.0 to avoid floating point precision issues
        let overlap = overlap.clamp(0.0, 1.0);
        let dist = f64::sqrt(1.0 - overlap);

        if half_normalized {
            dist
        } else {
            2.0 * dist
        }
    }

    /// Compute Ξ(P,ω) = ‖ρ(h₁*) - ρ(φ*)‖_tr from exact inputs.
    ///
    /// Everything that gates admission is decided on ℚ: Φ₁ = 0, and the
    /// primal-dual saturation ⟨φ*, h₁*⟩ = Φ₁. Only the returned magnitude is a
    /// float, because Ξ is a trace distance `sqrt(1 - |⟨ψ|φ⟩|²)` over density
    /// lifts whose entries are `√(|v_e|/M)` — a sum of surds, with no exact
    /// rational form. It is typed [`XiState::UncertifiedFloat`] downstream and
    /// may only separate candidates the exact functionals already tied.
    pub fn compute(
        primal_residual: &[Exact],
        dual_witness: &[Exact],
        phi1_value: &Exact,
        tolerance: f64,
        half_normalized: bool,
    ) -> XiComputation {
        XiComputation {
            kind: Self::compute_kind(
                primal_residual,
                dual_witness,
                phi1_value,
                tolerance,
                half_normalized,
            ),
        }
    }

    fn compute_kind(
        primal_residual: &[Exact],
        dual_witness: &[Exact],
        phi1_value: &Exact,
        tolerance: f64,
        half_normalized: bool,
    ) -> XiComputationKind {
        if primal_residual
            .iter()
            .chain(dual_witness)
            .chain(std::iter::once(phi1_value))
            .any(|value| value.denom().is_zero())
            || phi1_value.is_negative()
        {
            return XiComputationKind::Invalid(XiValidity::NonFiniteInput);
        }
        // Φ₁ = 0 is exact repair, and it is decided on ℚ. Deciding it by
        // `phi1 <= tolerance` reported a Φ₁ of 1/10^11 as an exact repair --
        // the same defect class as a residual gate calling 1e-9 closed.
        if phi1_value.is_zero() {
            return XiComputationKind::ExactZero;
        }

        if primal_residual.len() != dual_witness.len() {
            return XiComputationKind::Invalid(XiValidity::DensityLiftUndefined);
        }

        // Saturation, decided on ℚ: ⟨φ*, h₁*⟩ = Φ₁ exactly, or Ξ is not admitted.
        let inner_product = primal_residual
            .iter()
            .zip(dual_witness.iter())
            .fold(Exact::zero(), |acc, (p, d)| acc + p * d);
        if inner_product != *phi1_value {
            return XiComputationKind::Invalid(XiValidity::SaturationFailed);
        }

        // Past the exact gates. The lift itself needs reals.
        let to_float = |values: &[Exact]| -> Option<DVector<f64>> {
            values
                .iter()
                .map(core_kernel::approximate)
                .collect::<Option<Vec<f64>>>()
                .map(DVector::from_vec)
        };
        let (Some(primal_f), Some(dual_f)) = (to_float(primal_residual), to_float(dual_witness))
        else {
            return XiComputationKind::Invalid(XiValidity::NonFiniteInput);
        };

        let primal_density = Self::compute_density_lift(&primal_f, tolerance);
        let dual_density = Self::compute_density_lift(&dual_f, tolerance);

        let (primal_lift, dual_lift) = match (primal_density, dual_density) {
            (Ok(p), Ok(d)) => (p, d),
            (Err(XiError::NonFiniteInput | XiError::InvalidTolerance), _)
            | (_, Err(XiError::NonFiniteInput | XiError::InvalidTolerance)) => {
                return XiComputationKind::Invalid(XiValidity::NonFiniteInput);
            }
            _ => {
                return XiComputationKind::Invalid(XiValidity::DensityLiftUndefined);
            }
        };

        // Compute trace distance via pure-state formula
        let value = Self::pure_state_trace_distance(
            &primal_lift.state_vector,
            &dual_lift.state_vector,
            half_normalized,
        );
        if !value.is_finite() {
            return XiComputationKind::Invalid(XiValidity::NonFiniteInput);
        }

        XiComputationKind::ValidTieBreaker(XiResult {
            value,
            validity: XiValidity::Valid,
            primal_density: Some(primal_lift),
            dual_density: Some(dual_lift),
            // Established exactly above, before any float was taken.
            saturation_verified: true,
            primal_residual: primal_residual.to_vec(),
            dual_witness: dual_witness.to_vec(),
            phi1_value: phi1_value.clone(),
        })
    }
}

// Origin: engine/crates_rs/core_functional/src/xi.rs
// Claim: urn:core:crates_rs:core-functional:xi:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use approx::assert_relative_eq;

    fn compute(
        primal: &[Exact],
        dual: &[Exact],
        phi1: &Exact,
        tolerance: f64,
        half: bool,
    ) -> XiComputationKind {
        XiFunctional::compute(primal, dual, phi1, tolerance, half).kind
    }

    fn ex(value: i64) -> Exact {
        core_kernel::integer(value)
    }

    #[test]
    fn test_density_lift_rejects_zero_mass() {
        let v = DVector::from_vec(vec![0.0, 0.0, 0.0]);
        assert!(matches!(
            XiFunctional::compute_density_lift(&v, 1e-10),
            Err(XiError::ZeroMass)
        ));
    }

    #[test]
    fn test_density_lift_rejects_nan_entries() {
        let v = DVector::from_vec(vec![1.0, f64::NAN, 3.0]);
        assert!(matches!(
            XiFunctional::compute_density_lift(&v, 1e-10),
            Err(XiError::NonFiniteInput)
        ));
    }

    #[test]
    fn test_density_lift_state_norm_is_one() {
        let v = DVector::from_vec(vec![1.0, -2.0, 3.0]);
        let lift = XiFunctional::compute_density_lift(&v, 1e-10).unwrap();
        let norm_sqr: f64 = lift.state_vector.iter().map(|c| c.norm_sqr()).sum();
        assert_relative_eq!(norm_sqr, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_density_lift_is_scale_invariant_for_positive_scale() {
        let v = DVector::from_vec(vec![1.0, 2.0, 3.0]);
        let v_scaled = DVector::from_vec(vec![2.0, 4.0, 6.0]);
        let lift1 = XiFunctional::compute_density_lift(&v, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v_scaled, 1e-10).unwrap();

        for i in 0..3 {
            for j in 0..3 {
                assert_relative_eq!(
                    lift1.density_matrix[(i, j)].norm(),
                    lift2.density_matrix[(i, j)].norm(),
                    epsilon = 1e-6
                );
            }
        }
    }

    #[test]
    fn test_density_lift_changes_sign_for_negative_scale_or_doc_clarifies_phase_equivalence() {
        let v = DVector::from_vec(vec![1.0, 2.0, 3.0]);
        let v_scaled = DVector::from_vec(vec![-2.0, -4.0, -6.0]);
        let lift1 = XiFunctional::compute_density_lift(&v, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v_scaled, 1e-10).unwrap();

        // rho = |psi><psi| should be identical despite global phase factor of -1
        for i in 0..3 {
            for j in 0..3 {
                assert_relative_eq!(
                    lift1.density_matrix[(i, j)].norm(),
                    lift2.density_matrix[(i, j)].norm(),
                    epsilon = 1e-6
                );
            }
        }
    }

    #[test]
    fn test_identical_density_lifts_have_zero_distance() {
        let v = DVector::from_vec(vec![1.0, 2.0, 3.0]);
        let lift = XiFunctional::compute_density_lift(&v, 1e-10).unwrap();
        let dist =
            XiFunctional::pure_state_trace_distance(&lift.state_vector, &lift.state_vector, true);
        assert_relative_eq!(dist, 0.0, epsilon = 1e-10);
    }

    #[test]
    fn test_orthogonal_density_lifts_have_distance_one_half_normalized() {
        let v1 = DVector::from_vec(vec![1.0, 0.0]);
        let v2 = DVector::from_vec(vec![0.0, 1.0]);
        let lift1 = XiFunctional::compute_density_lift(&v1, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v2, 1e-10).unwrap();
        let dist =
            XiFunctional::pure_state_trace_distance(&lift1.state_vector, &lift2.state_vector, true);
        assert_relative_eq!(dist, 1.0, epsilon = 1e-10);
    }

    #[test]
    fn test_trace_distance_uses_pure_state_formula_not_entrywise_l1() {
        let v1 = DVector::from_vec(vec![1.0, 0.0]);
        let v2 = DVector::from_vec(vec![1.0, 1.0]);
        let lift1 = XiFunctional::compute_density_lift(&v1, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v2, 1e-10).unwrap();
        let dist_half =
            XiFunctional::pure_state_trace_distance(&lift1.state_vector, &lift2.state_vector, true);
        let dist_full = XiFunctional::pure_state_trace_distance(
            &lift1.state_vector,
            &lift2.state_vector,
            false,
        );
        // <psi1|psi2> = 1/sqrt(2) = ~0.707. overlap sqr = 0.5. 1 - 0.5 = 0.5. sqrt(0.5) = ~0.707
        assert_relative_eq!(dist_half, 0.5f64.sqrt(), epsilon = 1e-10);
        assert_relative_eq!(dist_full, 2.0 * 0.5f64.sqrt(), epsilon = 1e-10);
    }

    #[test]
    fn test_xi_bounded_by_one_half_normalized() {
        let v1 = DVector::from_vec(vec![1.0, 0.0]);
        let v2 = DVector::from_vec(vec![0.0, 1.0]);
        let lift1 = XiFunctional::compute_density_lift(&v1, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v2, 1e-10).unwrap();
        let dist =
            XiFunctional::pure_state_trace_distance(&lift1.state_vector, &lift2.state_vector, true);
        assert!(dist <= 1.0);
    }

    #[test]
    fn test_xi_bounded_by_two_unhalved() {
        let v1 = DVector::from_vec(vec![1.0, 0.0]);
        let v2 = DVector::from_vec(vec![0.0, 1.0]);
        let lift1 = XiFunctional::compute_density_lift(&v1, 1e-10).unwrap();
        let lift2 = XiFunctional::compute_density_lift(&v2, 1e-10).unwrap();
        let dist = XiFunctional::pure_state_trace_distance(
            &lift1.state_vector,
            &lift2.state_vector,
            false,
        );
        assert!(dist <= 2.0);
    }

    #[test]
    fn a_sub_tolerance_phi1_is_not_an_exact_repair() {
        // Under the previous `phi1 <= tolerance` test, Phi1 = 1/10^11 returned
        // ExactZero: an open obstruction reported as a repair.
        let tiny = core_kernel::exact(1, 100_000_000_000);
        let primal = [ex(1), ex(0)];
        let dual = [ex(1), ex(0)];
        assert!(!matches!(
            compute(&primal, &dual, &tiny, 1e-10, true),
            XiComputationKind::ExactZero
        ));
        assert!(matches!(
            compute(&primal, &dual, &ex(0), 1e-10, true),
            XiComputationKind::ExactZero
        ));
    }

    #[test]
    fn test_saturation_failure_blocks_xi_admission() {
        let primal = [ex(1), ex(0)];
        let dual = [ex(0), ex(1)]; // inner prod = 0
        let phi1 = ex(1); // mismatch
        let tol = 1e-10;

        let comp = compute(&primal, &dual, &phi1, tol, true);
        assert!(matches!(
            comp,
            XiComputationKind::Invalid(XiValidity::SaturationFailed)
        ));
    }

    #[test]
    fn compute_rejects_primal_dual_length_mismatch() {
        let primal = [ex(1), ex(0)];
        let dual = [ex(1)];
        let phi1 = ex(1);
        assert!(matches!(
            compute(&primal, &dual, &phi1, 1e-10, true),
            XiComputationKind::Invalid(XiValidity::DensityLiftUndefined)
        ));
    }

    #[test]
    fn bad_tolerance_and_overflowed_mass_do_not_return_a_nan_lift() {
        let zero = DVector::from_vec(vec![0.0]);
        assert!(matches!(
            XiFunctional::compute_density_lift(&zero, f64::NAN),
            Err(XiError::InvalidTolerance)
        ));
        assert!(matches!(
            XiFunctional::compute_density_lift(&zero, -1.0),
            Err(XiError::InvalidTolerance)
        ));
        let huge = DVector::from_vec(vec![f64::MAX, f64::MAX]);
        assert!(matches!(
            XiFunctional::compute_density_lift(&huge, 0.0),
            Err(XiError::NonFiniteInput)
        ));
        assert!(matches!(
            compute(&[ex(1)], &[ex(1)], &ex(1), f64::NAN, true),
            XiComputationKind::Invalid(XiValidity::NonFiniteInput)
        ));
        let left = DVector::from_vec(vec![Complex64::new(1.0, 0.0)]);
        let right = DVector::from_vec(vec![Complex64::new(1.0, 0.0), Complex64::new(0.0, 0.0)]);
        assert!(XiFunctional::pure_state_trace_distance(&left, &right, true).is_nan());
    }
}
