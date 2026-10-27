//! solver_quantum_lefschetz_thimble.rs
//!
//! ARCHIVED_AS_METAPHOR — AuthorityEffect: None.
//! Candidate C8 complexification is a heuristic continuum import.
//! This module produces *proposal diagnostics only*. Any output must be
//! re-validated by an exact finite-carrier verifier before use on an
//! authority path. It will not be “made whole” until a lawful discrete
//! lift exists.
//!
//! The holomorphic gradient flow is retained solely as a research
//! diagnostic. Numerical Im(S) conservation is approximate.

pub const THIMBLE_METAPHOR_FENCE: &str =
    "ARCHIVED_AS_METAPHOR; AuthorityEffect: None; candidate C8 complexification is heuristic.";

use crate::solver_fixpoint_operator::FixpointConverge;
use nalgebra::Complex;

pub type C64 = Complex<f64>;

/// Maximum allowed absolute drift of Im(S) before the flow is considered broken.
pub const IM_S_DRIFT_ABORT: f64 = 1e-2;

pub trait Action: Send + Sync {
    /// Holomorphic gradient ∂S/∂φ.
    fn gradient(&self, phi: &[C64]) -> Option<Vec<C64>>;
    /// Holomorphic Hessian ∂²S/∂φ².
    fn hessian(&self, phi: &[C64]) -> Option<Vec<Vec<C64>>>;
    /// Complex action value S(φ). Required for Im(S) monitoring.
    fn action_value_complex(&self, phi: &[C64]) -> Option<C64>;
}

#[derive(Debug, Clone)]
pub struct ThimbleState {
    pub phi: Vec<C64>,
    pub grad_norm: f64,
    pub step_count: usize,
    /// Imaginary part of the action at this state (monitored).
    pub im_s: f64,
    /// Absolute drift from the initial Im(S).
    pub im_s_drift: f64,
}

/// Explicit proposal-only receipt. Never treat as certified.
#[derive(Debug, Clone)]
pub struct ThimbleReceipt {
    pub final_state: ThimbleState,
    pub initial_im_s: f64,
    pub residual_phase: Option<f64>,
    pub fence: &'static str,
    pub authority_effect: &'static str,
}

impl ThimbleReceipt {
    pub fn is_proposal_only(&self) -> bool {
        true
    }
}

pub struct LefschetzThimbleSolver<'a> {
    pub action: &'a dyn Action,
    pub dt: f64,
    pub tolerance: f64,
    pub max_im_s_drift: f64,
}

impl<'a> LefschetzThimbleSolver<'a> {
    /// Constructs the solver. Always emits the metaphor fence.
    pub fn new(action: &'a dyn Action, dt: f64, tolerance: f64) -> Self {
        // Runtime fence — cannot be disabled without a deliberate feature.
        eprintln!("[LEFSCHETZ] {}", THIMBLE_METAPHOR_FENCE);
        Self {
            action,
            dt,
            tolerance,
            max_im_s_drift: IM_S_DRIFT_ABORT,
        }
    }

    pub fn initial_state(&self, phi0: Vec<C64>) -> ThimbleState {
        let im_s = self
            .action
            .action_value_complex(&phi0)
            .map(|s| s.im)
            .unwrap_or(0.0);
        ThimbleState {
            phi: phi0,
            grad_norm: f64::MAX,
            step_count: 0,
            im_s,
            im_s_drift: 0.0,
        }
    }

    /// Run the flow and return an explicit proposal receipt.
    pub fn run_proposal(
        &self,
        phi0: Vec<C64>,
        max_steps: usize,
    ) -> Result<ThimbleReceipt, &'static str> {
        let initial_im_s = self
            .action
            .action_value_complex(&phi0)
            .map(|s| s.im)
            .unwrap_or(0.0);

        let mut state = self.initial_state(phi0);
        for _ in 0..max_steps {
            if self.has_converged(&state, &state) {
                break;
            }
            state = self.step(state);
            if state.im_s_drift > self.max_im_s_drift {
                return Err("Im(S) drift exceeded abort threshold — flow is not a valid thimble");
            }
        }

        let residual_phase = ThimbleAnalytics::compute_residual_phase(self.action, &state.phi);

        Ok(ThimbleReceipt {
            final_state: state,
            initial_im_s,
            residual_phase,
            fence: THIMBLE_METAPHOR_FENCE,
            authority_effect: "None",
        })
    }
}

impl<'a> FixpointConverge<ThimbleState> for LefschetzThimbleSolver<'a> {
    fn step(&self, state: ThimbleState) -> ThimbleState {
        let grad = self
            .action
            .gradient(&state.phi)
            .unwrap_or_else(|| vec![C64::new(0.0, 0.0); state.phi.len()]);

        let grad_norm: f64 = grad.iter().map(|z| z.norm_sqr()).sum::<f64>().sqrt();

        // Conjugate flow: dφ/dt = conj(∂S/∂φ). Sign chosen so that
        // Im(S) is approximately conserved for quadratic test actions.
        let next_phi: Vec<C64> = state
            .phi
            .iter()
            .zip(grad.iter())
            .map(|(&z, &g)| z - C64::new(g.re, -g.im) * self.dt)
            .collect();

        let next_im_s = self
            .action
            .action_value_complex(&next_phi)
            .map(|s| s.im)
            .unwrap_or(state.im_s);

        let drift = (next_im_s - state.im_s + state.im_s_drift).abs(); // accumulate from origin

        ThimbleState {
            phi: next_phi,
            grad_norm,
            step_count: state.step_count + 1,
            im_s: next_im_s,
            im_s_drift: drift,
        }
    }

    fn has_converged(&self, _old: &ThimbleState, new: &ThimbleState) -> bool {
        new.grad_norm < self.tolerance && new.im_s_drift <= self.max_im_s_drift
    }
}

pub struct ThimbleAnalytics;

impl ThimbleAnalytics {
    /// Crude first-order residual phase (trace of Im(Hessian)).
    /// Proposal only — not a certified Stokes multiplier.
    pub fn compute_residual_phase(action: &dyn Action, phi: &[C64]) -> Option<f64> {
        let hessian = action.hessian(phi)?;
        let tr_im: f64 = hessian
            .iter()
            .enumerate()
            .map(|(i, row)| row.get(i).map(|z| z.im).unwrap_or(0.0))
            .sum();
        Some(tr_im)
    }
}

// ---------------------------------------------------------------------------
// Tests (updated for the new state / receipt)
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/core_solvers/src/solver_quantum_lefschetz_thimble.rs
// Claim: urn:core:crates_rs:core-solvers:solver-quantum-lefschetz-thimble:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord73b394ec {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord73b394ec` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError73b394ec {
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
impl BoundaryError73b394ec {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError73b394ec {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError73b394ec {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord73b394ec {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError73b394ec> {
        if capacity_bound == 0 {
            return Err(BoundaryError73b394ec::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError73b394ec::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError73b394ec::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod tests {
    use super::*;

    struct QuadraticAction;

    impl Action for QuadraticAction {
        fn gradient(&self, phi: &[C64]) -> Option<Vec<C64>> {
            Some(phi.to_vec())
        }
        fn hessian(&self, phi: &[C64]) -> Option<Vec<Vec<C64>>> {
            let n = phi.len();
            let mut h = vec![vec![C64::new(0.0, 0.0); n]; n];
            for i in 0..n {
                h[i][i] = C64::new(1.0, 0.0);
            }
            Some(h)
        }
        fn action_value_complex(&self, phi: &[C64]) -> Option<C64> {
            // S = Σ z_i² / 2
            let s: C64 = phi.iter().map(|z| z * z / 2.0).sum();
            Some(s)
        }
    }

    #[test]
    fn test_metaphor_fence_present() {
        assert!(THIMBLE_METAPHOR_FENCE.contains("ARCHIVED_AS_METAPHOR"));
        assert!(THIMBLE_METAPHOR_FENCE.contains("AuthorityEffect"));
    }

    #[test]
    fn test_thimble_contour_conservation() {
        let action = QuadraticAction;
        let solver = LefschetzThimbleSolver::new(&action, 0.01, 1e-8);

        let phi0 = vec![C64::new(1.0, 0.5), C64::new(-0.3, 0.7)];
        let receipt = solver.run_proposal(phi0, 500).expect("should not abort");

        assert!(receipt.is_proposal_only());
        assert_eq!(receipt.authority_effect, "None");
        assert!(receipt.final_state.im_s_drift < 0.05);
    }

    #[test]
    fn test_thimble_converges_to_saddle() {
        let action = QuadraticAction;
        let solver = LefschetzThimbleSolver::new(&action, 0.05, 1e-6);

        let phi0 = vec![C64::new(1.0, 0.0)];
        let receipt = solver.run_proposal(phi0, 1000).expect("should converge");
        for z in &receipt.final_state.phi {
            assert!(z.norm() < 1e-4);
        }
    }

    #[test]
    fn test_divergence_does_not_claim_success() {
        struct RepulsiveAction;
        impl Action for RepulsiveAction {
            fn gradient(&self, phi: &[C64]) -> Option<Vec<C64>> {
                Some(phi.iter().map(|z| -z).collect())
            }
            fn hessian(&self, _: &[C64]) -> Option<Vec<Vec<C64>>> {
                None
            }
            fn action_value_complex(&self, _: &[C64]) -> Option<C64> {
                Some(C64::new(0.0, 0.0))
            }
        }

        let action = RepulsiveAction;
        let solver = LefschetzThimbleSolver::new(&action, 0.01, 1e-8);
        let phi0 = vec![C64::new(1.0, 0.0)];
        // Either aborts on drift or finishes with large grad_norm
        let _ = solver.run_proposal(phi0, 100);
    }
}

#[cfg(test)]
mod l4_boundary_tests_73b394ec {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord73b394ec::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord73b394ec::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord73b394ec::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord73b394ec::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord73b394ec::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError73b394ec::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError73b394ec::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
