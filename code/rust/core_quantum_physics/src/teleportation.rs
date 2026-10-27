//! Quantum teleportation of a qubit, derived from the three-qubit state.
//!
//! Alice holds the input qubit `A` in `|psi> = alpha|0> + beta|1>` and half `B` of the pair
//! `|Phi+>_BC = (|00> + |11>)/sqrt 2`; Bob holds `C`. For a Bell state `|mu>_AB` the
//! conditional state of `C` is `(<mu|_AB (x) I_C)(|psi>_A (x) |Phi+>_BC)`, and its squared
//! norm is the Born probability of Alice's outcome `mu`.
//! [`Teleportation::conditional_state_of_bob`] computes it from the amplitudes. It equals
//! `sigma_mu |psi> / 2` for `sigma_mu` in `{I, Z, X, X Z}` (outcomes `Phi+`, `Phi-`,
//! `Psi+`, `Psi-`), so every outcome has probability `1/4` for a unit-norm `psi`, and Bob
//! recovers `psi` up to a global phase by applying `sigma_mu` (each Pauli squares to
//! `+-I`).
//!
//! [`Teleportation::simulate_teleportation`] computes all four conditional states,
//! applies the correction named by the outcome, checks fidelity 1 with the input and
//! checks that the four probabilities sum to 1. Scope: one qubit in, `f64` amplitudes
//! (a diagnostic, not a certificate), a perfect pair and ideal gates.
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_7129c09a<T> {
    fn checked_invariant_7129c09a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_7129c09a<T> for Option<T> {
    #[inline]
    fn checked_invariant_7129c09a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_7129c09a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_7129c09a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::bell_state::{BellBasis, BellState};
use crate::hilbert_space::HilbertSpace;
use crate::quantum_state::{QuantumState, QuantumStateError};
use crate::unitary_operator::{UnitaryError, UnitaryOperator};
use linear_algebra::linear_algebra::complex_matrix::C64;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite teleportation face.";

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum TeleportationError {
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error("state error: {0}")]
    State(#[from] QuantumStateError),
    #[error("unitary error: {0}")]
    Unitary(#[from] UnitaryError),
    #[error("dimension mismatch: expected 2-dimensional qubit")]
    NotAQubit,
    #[error("verification failed: fidelity {fidelity} < 1.0 - tol {tol}")]
    FidelityBelowThreshold { fidelity: f64, tol: f64 },
    #[error("the four Born probabilities sum to {total}, not 1")]
    BornProbabilitiesNotNormalised { total: f64 },
}

/// Classical measurement outcome from Alice's Bell-basis measurement.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AliceBellMeasurementOutcome {
    /// Outcome 0: |Φ⁺⟩ -> Bob applies I
    PhiPlus = 0,
    /// Outcome 1: |Ψ⁺⟩ -> Bob applies X
    PsiPlus = 1,
    /// Outcome 2: |Φ⁻⟩ -> Bob applies Z
    PhiMinus = 2,
    /// Outcome 3: |Ψ⁻⟩ -> Bob applies XZ (or ZX)
    PsiMinus = 3,
}

impl AliceBellMeasurementOutcome {
    pub fn all() -> [Self; 4] {
        [Self::PhiPlus, Self::PsiPlus, Self::PhiMinus, Self::PsiMinus]
    }

    /// The Bell basis vector of `AB` that this outcome projects onto.
    pub fn bell_basis(&self) -> BellBasis {
        match self {
            Self::PhiPlus => BellBasis::PhiPlus,
            Self::PsiPlus => BellBasis::PsiPlus,
            Self::PhiMinus => BellBasis::PhiMinus,
            Self::PsiMinus => BellBasis::PsiMinus,
        }
    }

    /// Bob's required Pauli unitary correction to recover |ψ⟩.
    pub fn bob_correction(&self) -> UnitaryOperator {
        match self {
            Self::PhiPlus => UnitaryOperator::identity(2),
            Self::PsiPlus => UnitaryOperator::pauli_x(),
            Self::PhiMinus => UnitaryOperator::pauli_z(),
            Self::PsiMinus => {
                let x = UnitaryOperator::pauli_x();
                let z = UnitaryOperator::pauli_z();
                x.compose(&z).checked_invariant_7129c09a("2x2 composition")
            }
        }
    }
}

/// Result of a teleportation simulation step.
#[derive(Debug, Clone)]
pub struct TeleportationResult {
    pub alice_outcome: AliceBellMeasurementOutcome,
    /// The Born probability of the outcome, computed from the three-qubit state.
    pub outcome_probability: f64,
    pub bob_recovered_state: QuantumState,
    pub fidelity: f64,
}

/// Finite carrier for `teleportation`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Teleportation {
    /// Degree / dimension proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Teleportation {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Bob's unnormalised conditional state, and the Born probability of the outcome, after
    /// Alice's Bell measurement returns `outcome`:
    /// `v_c = sum_{a,b} conj(mu_ab) psi_a Phi+_bc`, with probability `|v|^2`.
    pub fn conditional_state_of_bob(
        psi_a: &QuantumState,
        outcome: AliceBellMeasurementOutcome,
    ) -> Result<([C64; 2], f64), TeleportationError> {
        psi_a.validate()?;
        if psi_a.dim() != 2 {
            return Err(TeleportationError::NotAQubit);
        }
        let mu = BellState::construct_bell_state(outcome.bell_basis());
        let pair = BellState::phi_plus();
        let psi = psi_a.amplitudes();
        let mut bob = [C64::new(0.0, 0.0); 2];
        for a in 0..2 {
            for b in 0..2 {
                for (c, slot) in bob.iter_mut().enumerate() {
                    // the amplitude of |a b c> in |psi>_A (x) |Phi+>_BC
                    let amplitude = psi[a] * pair.amplitudes()[b * 2 + c];
                    *slot += mu.amplitudes()[a * 2 + b].conj() * amplitude;
                }
            }
        }
        let probability = bob.iter().map(|z| z.norm_sqr()).sum();
        Ok((bob, probability))
    }

    fn simulate_single_bell_outcome(
        psi_a: &QuantumState,
        h2: &HilbertSpace,
        outcome: AliceBellMeasurementOutcome,
        tol: f64,
    ) -> Result<TeleportationResult, TeleportationError> {
        let (bob_amps, probability) = Self::conditional_state_of_bob(psi_a, outcome)?;
        let bob_pre_state = QuantumState::try_normalized(h2, bob_amps.to_vec(), "bob_pre")?;
        let correction = outcome.bob_correction();
        let recovered = correction.evolve_state(&bob_pre_state)?;

        let fidelity = recovered.transition_probability(psi_a)?;
        if (fidelity - 1.0).abs() > tol {
            return Err(TeleportationError::FidelityBelowThreshold { fidelity, tol });
        }

        let out = TeleportationResult {
            alice_outcome: outcome,
            outcome_probability: probability,
            bob_recovered_state: recovered,
            fidelity,
        };
        Ok(out)
    }

    /// Simulate the quantum teleportation of an arbitrary input qubit state `psi_a`:
    /// derive Bob's conditional state for each of the four Bell outcomes, apply the
    /// correction, and verify fidelity 1 and that the outcome probabilities sum to 1.
    pub fn simulate_teleportation(
        psi_a: &QuantumState,
        tol: f64,
    ) -> Result<Vec<TeleportationResult>, TeleportationError> {
        if !tol.is_finite() || tol < 0.0 {
            return Err(TeleportationError::InvalidTolerance);
        }
        psi_a.validate()?;
        if psi_a.dim() != 2 {
            return Err(TeleportationError::NotAQubit);
        }

        let h2 = HilbertSpace::try_new(2, "H_qubit").map_err(|_| TeleportationError::NotAQubit)?;

        let mut results = Vec::with_capacity(4);
        let mut total_probability = 0.0;

        for outcome in AliceBellMeasurementOutcome::all() {
            let res = Self::simulate_single_bell_outcome(psi_a, &h2, outcome, tol)?;
            total_probability += res.outcome_probability;
            results.push(res);
        }

        if (total_probability - 1.0).abs() > tol {
            return Err(TeleportationError::BornProbabilitiesNotNormalised {
                total: total_probability,
            });
        }

        Ok(results)
    }

    /// Verify that an input state can be teleported with fidelity 1.0 across all outcomes.
    pub fn verify_teleportation(
        psi_a: &QuantumState,
        tol: f64,
    ) -> Result<bool, TeleportationError> {
        let results = Self::simulate_teleportation(psi_a, tol)?;
        let all_pass = results.iter().all(|r| (r.fidelity - 1.0).abs() <= tol);
        Ok(all_pass)
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Exact qubit teleportation evidence from Bell projection of the joint state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactTeleportationOutcome {
    pub outcome: AliceBellMeasurementOutcome,
    pub probability: core_number_theory::rational::Rational,
    pub bob_before: crate::quantum_state::RayVector,
    pub bob_after: crate::quantum_state::RayVector,
}
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum ExactTeleportationError {
    #[error("input carrier, resource, or primitive root is invalid")]
    InvalidInput,
    #[error("ray: {0}")]
    Ray(#[from] crate::quantum_state::RayError),
    #[error("operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
    #[error("protocol failed its exact Born or correction replay")]
    Replay,
}
impl Teleportation {
    fn exact_bob_correction(
        outcome: AliceBellMeasurementOutcome,
    ) -> Result<crate::exact_operator::ExactOperator, ExactTeleportationError> {
        use crate::pauli::Pauli;
        Ok(match outcome {
            AliceBellMeasurementOutcome::PhiPlus => Pauli::I.to_operator(),
            AliceBellMeasurementOutcome::PsiPlus => Pauli::X.to_operator(),
            AliceBellMeasurementOutcome::PhiMinus => Pauli::Z.to_operator(),
            AliceBellMeasurementOutcome::PsiMinus => {
                Pauli::X.to_operator().mul(&Pauli::Z.to_operator())?
            }
        })
    }

    fn contract_exact_bell_conditional(
        bell: &crate::quantum_state::RayVector,
        joint: &crate::quantum_state::RayVector,
    ) -> Result<crate::quantum_state::RayVector, ExactTeleportationError> {
        use crate::quantum_state::RayVector;
        use core_number_theory::cyclotomic::GaussianRat;
        let mut conditional = vec![GaussianRat::zero(); 2];
        for (c, value) in conditional.iter_mut().enumerate() {
            for ab in 0..4 {
                *value = value.add(&bell.entries()[ab].conj().mul(&joint.entries()[ab * 2 + c]));
            }
        }
        Ok(RayVector::try_new(conditional)?)
    }

    fn project_bell_outcome_probability(
        bell: &crate::quantum_state::RayVector,
        joint: &crate::quantum_state::RayVector,
    ) -> Result<core_number_theory::rational::Rational, ExactTeleportationError> {
        use crate::exact_operator::ExactOperator;
        let projector = bell.projector()?.kron(&ExactOperator::identity(2)?)?;
        let projected = joint.apply_ray(&projector)?;
        Ok(projected.norm_sq() / joint.norm_sq())
    }

    fn simulate_exact_qubit_outcome(
        input: &crate::quantum_state::RayVector,
        joint: &crate::quantum_state::RayVector,
        outcome: AliceBellMeasurementOutcome,
    ) -> Result<ExactTeleportationOutcome, ExactTeleportationError> {
        use core_number_theory::rational::rq;
        let bell = BellState::exact_ray(outcome.bell_basis())?;
        let probability = Self::project_bell_outcome_probability(&bell, joint)?;
        let bob_before = Self::contract_exact_bell_conditional(&bell, joint)?;
        let correction = Self::exact_bob_correction(outcome)?;
        let bob_after = bob_before.apply_ray(&correction)?;
        if probability != rq(1, 4) || !bob_after.same_ray(input)? {
            return Err(ExactTeleportationError::Replay);
        }
        let out = ExactTeleportationOutcome {
            outcome,
            probability,
            bob_before,
            bob_after,
        };
        Ok(out)
    }

    /// Simulate all exact qubit branches by applying Bell projectors to the
    /// three-qubit input-resource state. Both probabilities and Bob's rays are
    /// computed from this contraction, never assigned as the expected answer.
    pub fn exact(
        input: &crate::quantum_state::RayVector,
    ) -> Result<Vec<ExactTeleportationOutcome>, ExactTeleportationError> {
        use core_number_theory::rational::ri;
        if input.len() != 2 {
            return Err(ExactTeleportationError::InvalidInput);
        }
        let joint = input.kron(&BellState::exact_ray(BellBasis::PhiPlus)?)?;
        let mut results = Vec::new();
        let mut total = ri(0);
        for outcome in AliceBellMeasurementOutcome::all() {
            let branch = Self::simulate_exact_qubit_outcome(input, &joint, outcome)?;
            total += &branch.probability;
            results.push(branch);
        }
        if total != ri(1) {
            return Err(ExactTeleportationError::Replay);
        }
        Ok(results)
    }
}

/// Generic exact qudit teleportation branch in a declared cyclotomic field.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct QuditTeleportationOutcome<F> {
    pub shift: usize,
    pub phase: usize,
    pub probability: core_number_theory::rational::Rational,
    pub corrected: Vec<F>,
}

fn validate_qudit_primitive_root<F>(d: usize, root: &F) -> Result<Vec<F>, ExactTeleportationError>
where
    F: core_number_theory::scalar::RationalEmbedding
        + linear_algebra::exact_field::involution::Involution,
{
    let mut powers = vec![F::one()];
    for _ in 1..=d {
        let next = powers
            .last()
            .ok_or(ExactTeleportationError::InvalidInput)?
            .mul(root);
        powers.push(next);
    }
    if powers[d] != F::one()
        || powers[1..d].iter().any(|x| *x == F::one())
        || root.mul(&root.conjugate()) != F::one()
    {
        return Err(ExactTeleportationError::InvalidInput);
    }
    Ok(powers)
}

fn contract_qudit_bell_branch<F>(
    input: &[F],
    powers: &[F],
    d: usize,
    shift: usize,
    phase: usize,
    inv_dim: &F,
) -> Vec<F>
where
    F: core_number_theory::scalar::RationalEmbedding
        + linear_algebra::exact_field::involution::Involution,
{
    let mut bob = vec![F::zero(); d];
    // <Bell_(shift,phase)| (|psi> tensor |resource>): only b=c contributes.
    for a in 0..d {
        for b in 0..d {
            for c in 0..d {
                if b == c && b == (a + shift) % d {
                    let bra = powers[(phase * a) % d].conjugate();
                    bob[c] = bob[c].add(&bra.mul(&input[a]).mul(inv_dim));
                }
            }
        }
    }
    bob
}

fn evaluate_qudit_branch<F>(
    input: &[F],
    powers: &[F],
    d: usize,
    shift: usize,
    phase: usize,
    inverse: &F,
    dimension: &core_number_theory::rational::Rational,
    expected: &core_number_theory::rational::Rational,
) -> Result<QuditTeleportationOutcome<F>, ExactTeleportationError>
where
    F: core_number_theory::scalar::RationalEmbedding
        + linear_algebra::exact_field::involution::Involution,
{
    let inv_dim = F::from_rational(&dimension.recip());
    let bob = contract_qudit_bell_branch(input, powers, d, shift, phase, &inv_dim);
    let conditional_norm = bob
        .iter()
        .fold(F::zero(), |a, x| a.add(&x.conjugate().mul(x)));
    let probability = conditional_norm.mul(inverse);
    if probability != F::from_rational(expected) {
        return Err(ExactTeleportationError::Replay);
    }
    let corrected: Vec<_> = (0..d)
        .map(|a| powers[(phase * a) % d].mul(&bob[(a + shift) % d]))
        .collect();
    if corrected
        .iter()
        .zip(input)
        .any(|(a, b)| *a != b.mul(&inv_dim))
    {
        return Err(ExactTeleportationError::Replay);
    }
    let out = QuditTeleportationOutcome {
        shift,
        phase,
        probability: expected.clone(),
        corrected,
    };
    Ok(out)
}

fn validate_qudit_input_and_inverse<F>(
    input: &[F],
    root: &F,
) -> Result<(usize, Vec<F>, F), ExactTeleportationError>
where
    F: core_number_theory::scalar::RationalEmbedding
        + linear_algebra::exact_field::involution::Involution,
{
    let d = input.len();
    if d < 2 || d > 32 || input.iter().all(|x| *x == F::zero()) {
        return Err(ExactTeleportationError::InvalidInput);
    }
    let powers = validate_qudit_primitive_root(d, root)?;
    let norm = input
        .iter()
        .fold(F::zero(), |a, x| a.add(&x.conjugate().mul(x)));
    let inverse = linear_algebra::scalars::Field::try_inv(&norm)
        .ok_or(ExactTeleportationError::InvalidInput)?;
    Ok((d, powers, inverse))
}

/// Contract Bell bras against input tensor sum_t |tt>, then apply inverse Weyl
/// correction. The primitive root is checked, and the Born probability is
/// computed in the exact field before comparing to the rational 1/d^2.
pub fn teleport_qudit<F>(
    input: &[F],
    root: &F,
) -> Result<Vec<QuditTeleportationOutcome<F>>, ExactTeleportationError>
where
    F: core_number_theory::scalar::RationalEmbedding
        + linear_algebra::exact_field::involution::Involution,
{
    use core_number_theory::rational::{ri, Rational};
    let (d, powers, inverse) = validate_qudit_input_and_inverse(input, root)?;
    let dimension = Rational::from_integer(d.into());
    let expected = Rational::new(1.into(), (d * d).into());
    let mut out = Vec::new();
    for shift in 0..d {
        for phase in 0..d {
            out.push(evaluate_qudit_branch(
                input, &powers, d, shift, phase, &inverse, &dimension, &expected,
            )?);
        }
    }
    let total: Rational = out.iter().map(|x| x.probability.clone()).sum();
    if total != ri(1) {
        return Err(ExactTeleportationError::Replay);
    }
    Ok(out)
}
// Origin: engine/crates_rs/core_quantum_physics/src/teleportation.rs
// Claim: urn:core:crates_rs:core-quantum-physics:teleportation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;
    use linear_algebra::linear_algebra::complex_matrix::C64;

    fn generic_qubit() -> QuantumState {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        // |psi> = cos(pi/6)|0> + e^{i pi/3} sin(pi/6)|1>
        let theta = std::f64::consts::FRAC_PI_6;
        let phi = std::f64::consts::FRAC_PI_3;
        let alpha = C64::new(theta.cos(), 0.0);
        let beta = C64::from_polar(theta.sin(), phi);
        QuantumState::try_normalized(&h2, vec![alpha, beta], "superposition").unwrap()
    }

    fn close(z: C64, w: C64) -> bool {
        (z - w).norm() < 1e-12
    }

    #[test]
    fn new_and_fence() {
        let x = Teleportation::new(1, "test");
        assert_eq!(x.degree, 1);
        assert!(Teleportation::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn teleport_computational_zero() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();
        assert!(Teleportation::verify_teleportation(&s0, 1e-6).unwrap());
    }

    #[test]
    fn teleport_superposition_state() {
        let psi = generic_qubit();
        let results = Teleportation::simulate_teleportation(&psi, 1e-6).unwrap();

        assert_eq!(results.len(), 4);
        for res in results {
            assert!((res.outcome_probability - 0.25).abs() < 1e-12);
            assert!((res.fidelity - 1.0).abs() < 1e-6);
        }
    }

    /// The conditional states computed from the three-qubit amplitudes equal the
    /// textbook table `sigma_mu psi / 2`, written out by hand here.
    #[test]
    fn bobs_conditional_states_are_the_paulis_applied_to_psi_over_two() {
        let psi = generic_qubit();
        let (alpha, beta) = (psi.amplitudes()[0], psi.amplitudes()[1]);
        let half = C64::new(0.5, 0.0);
        let expected = [
            (
                AliceBellMeasurementOutcome::PhiPlus,
                [alpha * half, beta * half],
            ),
            (
                AliceBellMeasurementOutcome::PsiPlus,
                [beta * half, alpha * half],
            ),
            (
                AliceBellMeasurementOutcome::PhiMinus,
                [alpha * half, -beta * half],
            ),
            (
                AliceBellMeasurementOutcome::PsiMinus,
                [-beta * half, alpha * half],
            ),
        ];
        for (outcome, amplitudes) in expected {
            let (bob, probability) =
                Teleportation::conditional_state_of_bob(&psi, outcome).unwrap();
            assert!(
                close(bob[0], amplitudes[0]) && close(bob[1], amplitudes[1]),
                "{outcome:?}"
            );
            assert!((probability - 0.25).abs() < 1e-12, "{outcome:?}");
        }
    }

    #[test]
    fn the_four_born_probabilities_sum_to_one_for_every_input() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        for index in 0..2 {
            let basis = QuantumState::computational_basis(&h2, index, "b").unwrap();
            let total: f64 = AliceBellMeasurementOutcome::all()
                .iter()
                .map(|o| {
                    Teleportation::conditional_state_of_bob(&basis, *o)
                        .unwrap()
                        .1
                })
                .sum();
            assert!((total - 1.0).abs() < 1e-12);
        }
    }

    /// Negative controls: without Alice's message Bob holds the wrong state, and the wrong
    /// correction does not recover the input, so the fidelity check is not vacuous.
    #[test]
    fn the_wrong_or_missing_correction_does_not_recover_the_input() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let zero = QuantumState::computational_basis(&h2, 0, "0").unwrap();
        let (bob, _) =
            Teleportation::conditional_state_of_bob(&zero, AliceBellMeasurementOutcome::PsiPlus)
                .unwrap();
        // Bob holds X|0> = |1> / 2: orthogonal to the input before correction
        let held = QuantumState::try_normalized(&h2, bob.to_vec(), "held").unwrap();
        assert!(held.transition_probability(&zero).unwrap() < 1e-12);
        // applying the identity instead of X leaves it wrong; applying X fixes it
        let wrong = UnitaryOperator::identity(2).evolve_state(&held).unwrap();
        assert!(wrong.transition_probability(&zero).unwrap() < 1e-12);
        let right = AliceBellMeasurementOutcome::PsiPlus
            .bob_correction()
            .evolve_state(&held)
            .unwrap();
        assert!((right.transition_probability(&zero).unwrap() - 1.0).abs() < 1e-12);
    }

    #[test]
    fn a_non_qubit_input_is_refused() {
        let h4 = HilbertSpace::try_new(4, "h4").unwrap();
        let s = QuantumState::computational_basis(&h4, 0, "00").unwrap();
        assert_eq!(
            Teleportation::simulate_teleportation(&s, 1e-6).unwrap_err(),
            TeleportationError::NotAQubit
        );
    }
}
