//! Wootters-Zurek no-cloning theorem and cloning obstruction for `core_quantum_physics`.
//!
//! Evaluates the Wootters-Zurek cloning obstruction functional:
//! \(\mathcal{O}(\psi, \phi) = |\langle\psi|\phi\rangle - \langle\psi|\phi\rangle^2|\),
//! verifying that non-orthogonal, non-identical quantum states cannot be cloned
//! by any linear unitary operator.
//!
//! Grounded in the mathematical foundational types of `core_linear_algebra` (`QuantumState`, `C64`).
//!
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.

use crate::density_matrix::ExactDensityMatrix;
use crate::quantum_state::{QuantumState, QuantumStateError, RayVector};
use core_number_theory::rational::{ri, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ExactCloningError {
    #[error("empty state family or invalid dimensions/copy counts")]
    InvalidParameters,
    #[error("ray: {0}")]
    Ray(#[from] crate::quantum_state::RayError),
    #[error("operator: {0}")]
    Operator(#[from] crate::exact_operator::OperatorError),
}

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; finite no-cloning face.";

/// Optimal Bužek-Hillery universal 1->2 qubit cloning fidelity bound: 5/6 ≈ 0.8333.
pub const BUZEK_HILLERY_MAX_FIDELITY: f64 = 5.0 / 6.0;

#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum NoCloningError {
    #[error("invalid diagnostic tolerance")]
    InvalidTolerance,
    #[error("state error: {0}")]
    State(#[from] QuantumStateError),
    #[error("dimension mismatch: expected {expected}, got {actual}")]
    DimensionMismatch { expected: usize, actual: usize },
}

/// Finite carrier for `no_cloning`.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct NoCloning {
    /// Degree / dimension proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl NoCloning {
    /// Exact phase-independent cloning obstruction t(1-t), where t is the
    /// transition probability. Zero exactly for equal or orthogonal rays.
    pub fn exact_obstruction(u: &RayVector, v: &RayVector) -> Result<Rational, ExactCloningError> {
        let t = u.transition_probability(v)?;
        Ok(&t * (ri(1) - &t))
    }
    /// A finite family can be perfectly cloned iff every pair of distinct rays
    /// is orthogonal. Returns the first obstructing pair, with its exact t.
    /// This checks the Gram obstruction; it does not claim a universal cloner.
    pub fn cloning_witness(
        family: &[RayVector],
    ) -> Result<Option<(usize, usize, Rational)>, ExactCloningError> {
        if family.is_empty() {
            return Err(ExactCloningError::InvalidParameters);
        }
        for i in 0..family.len() {
            for j in 0..i {
                let t = family[i].transition_probability(&family[j])?;
                if t != ri(0) && t != ri(1) {
                    return Ok(Some((j, i, t)));
                }
            }
        }
        Ok(None)
    }
    /// Finite-state broadcasting criterion: a family is broadcastable exactly
    /// when its density matrices commute pairwise. Returns an obstructing pair.
    pub fn broadcasting_witness(
        states: &[ExactDensityMatrix],
    ) -> Result<Option<(usize, usize)>, ExactCloningError> {
        if states.is_empty() {
            return Err(ExactCloningError::InvalidParameters);
        }
        for i in 0..states.len() {
            for j in 0..i {
                if states[i].as_operator().mul(states[j].as_operator())?
                    != states[j].as_operator().mul(states[i].as_operator())?
                {
                    return Ok(Some((j, i)));
                }
            }
        }
        Ok(None)
    }
    /// Optimal universal symmetric N->M single-copy fidelity for pure d-level
    /// inputs: N/M+(M-N)(N+1)/(M(N+d)). This formula is exact; no optimization
    /// solver or claim about a caller-supplied physical cloner is implied.
    pub fn universal_cloning_fidelity(
        d: usize,
        n: usize,
        m: usize,
    ) -> Result<Rational, ExactCloningError> {
        if d < 2 || n == 0 || m < n {
            return Err(ExactCloningError::InvalidParameters);
        }
        let (d, n, m) = (
            num_bigint::BigInt::from(d),
            num_bigint::BigInt::from(n),
            num_bigint::BigInt::from(m),
        );
        Ok(Rational::new(n.clone(), m.clone()) + Rational::new((&m - &n) * (&n + 1), m * (&n + d)))
    }

    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Phase-independent diagnostic obstruction t(1-t), where t is the
    /// transition probability. It vanishes for identical or orthogonal rays.
    pub fn cloning_obstruction(
        psi: &QuantumState,
        phi: &QuantumState,
    ) -> Result<f64, NoCloningError> {
        let t = psi.transition_probability(phi)?;
        Ok(t * (1.0 - t))
    }

    /// Verify whether a pair of states can be simultaneously cloned perfectly by a unitary.
    /// Returns true iff states are orthogonal or identical within `tol`.
    pub fn can_clone_perfectly(
        psi: &QuantumState,
        phi: &QuantumState,
        tol: f64,
    ) -> Result<bool, NoCloningError> {
        if !tol.is_finite() || tol < 0.0 || tol >= 0.5 {
            return Err(NoCloningError::InvalidTolerance);
        }
        let t = psi.transition_probability(phi)?;
        Ok(t <= tol || (t - 1.0).abs() <= tol)
    }

    /// Check whether an empirical or proposed cloning fidelity violates the
    /// Bužek-Hillery bound for 1->2 universal qubit cloning:
    /// returns true if \(F \le 5/6 + \text{tol}\) (physical), false if super-quantum (\(F > 5/6\)).
    pub fn obeys_buzek_hillery_bound(fidelity: f64, tol: f64) -> bool {
        fidelity.is_finite()
            && tol.is_finite()
            && tol >= 0.0
            && fidelity >= 0.0
            && fidelity <= 1.0
            && fidelity <= BUZEK_HILLERY_MAX_FIDELITY + tol
    }

    pub fn degree(&self) -> usize {
        self.degree
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/no_cloning.rs
// Claim: urn:core:crates_rs:core-quantum-physics:no-cloning:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::hilbert_space::HilbertSpace;
    use linear_algebra::linear_algebra::complex_matrix::C64;

    #[test]
    fn new_and_fence() {
        let x = NoCloning::new(1, "test");
        assert_eq!(x.degree, 1);
        assert!(NoCloning::authority_fence().contains("AuthorityEffect None"));
    }

    #[test]
    fn orthogonal_states_zero_obstruction() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();
        let s1 = QuantumState::computational_basis(&h2, 1, "1").unwrap();

        let obs = NoCloning::cloning_obstruction(&s0, &s1).unwrap();
        assert!(obs < 1e-12);
        assert!(NoCloning::can_clone_perfectly(&s0, &s1, 1e-6).unwrap());
    }

    #[test]
    fn identical_states_zero_obstruction() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();

        let obs = NoCloning::cloning_obstruction(&s0, &s0).unwrap();
        assert!(obs < 1e-12);
        assert!(NoCloning::can_clone_perfectly(&s0, &s0, 1e-6).unwrap());
    }

    #[test]
    fn non_orthogonal_states_nonzero_obstruction() {
        let h2 = HilbertSpace::try_new(2, "h2").unwrap();
        let s0 = QuantumState::computational_basis(&h2, 0, "0").unwrap();

        // |+> = 1/√2 (|0> + |1>), overlap = 1/√2 ≈ 0.7071
        // Phase-independent obstruction t(1-t) = 1/4 > 0
        let inv_sqrt2 = (0.5_f64).sqrt();
        let plus = QuantumState::try_normalized(
            &h2,
            vec![C64::new(inv_sqrt2, 0.0), C64::new(inv_sqrt2, 0.0)],
            "plus",
        )
        .unwrap();

        let obs = NoCloning::cloning_obstruction(&s0, &plus).unwrap();
        let expected = 0.25;
        assert!((obs - expected).abs() < 1e-10);
        assert!(!NoCloning::can_clone_perfectly(&s0, &plus, 1e-6).unwrap());
    }

    #[test]
    fn buzek_hillery_bound_enforcement() {
        assert!(NoCloning::obeys_buzek_hillery_bound(0.833, 1e-6));
        assert!(NoCloning::obeys_buzek_hillery_bound(5.0 / 6.0, 1e-6));
        assert!(!NoCloning::obeys_buzek_hillery_bound(0.95, 1e-6)); // super-quantum!
    }
}
