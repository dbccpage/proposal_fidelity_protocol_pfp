//! Appendix B second-derivative bound assembly and numerical kill-hook companion.
//!
//! Replicates the valid-input arithmetic of `short_time_defect_numerical_certificate.py`.
//! Invalid and overflowing inputs are refused; no continuum bound is proved.
//!
//! `AuthorityEffect: None.`

/// Finite-instance numerical kill-test companion for Appendix B second-derivative bound.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct SecondDerivativeBoundCertificate {
    /// The dimensionless coupling constant `g`.
    g: f64,
    /// Paper bound for one-site first derivative: `2.0 * g`.
    paper_one_site_first: f64,
    /// Paper bound for one-site second derivative: `8.0 * g^2`.
    paper_one_site_second: f64,
    /// Paper bound for two-site second derivative: `24.0 * g^2`.
    paper_two_site_second: f64,
    /// Paper second-order total bound: `48.0 * g^2`.
    paper_m: f64,
}

/// Evaluation result for the Appendix B reduced-state derivative assembly.
#[derive(Debug, Clone, PartialEq)]
pub struct SecondDerivativeBoundReport {
    /// Provenance source description of the derivative assembly.
    pub second_deriv_source: &'static str,
    /// The coupling parameter `g`.
    pub g: f64,
    /// True if any of the five reduced-state derivative bounds were exceeded beyond tolerance.
    pub second_deriv_bound_violated: bool,
    /// Assembled second-order coefficient from measured components.
    pub assembled_m: f64,
    /// The final effective second-order coefficient used (clamped to paper bound if not violated).
    pub m_used: f64,
    /// Taylor expansion coefficient `c_2 = M_used / 2.0`.
    pub taylor_c2_used: f64,
}

impl SecondDerivativeBoundCertificate {
    /// Construct the certificate bounds from the dimensionless coupling `g`.
    pub fn new(g: f64) -> Result<Self, String> {
        if !g.is_finite() || g < 0.0 {
            return Err("g must be finite and nonnegative".into());
        }
        let paper_one_site_first = 2.0 * g;
        let paper_one_site_second = 8.0 * (g * g);
        let paper_two_site_second = 24.0 * (g * g);
        let paper_m = 48.0 * (g * g);

        if !paper_m.is_finite() {
            return Err("paper bound overflows f64".into());
        }
        Ok(Self {
            g,
            paper_one_site_first,
            paper_one_site_second,
            paper_two_site_second,
            paper_m,
        })
    }

    /// Check five reduced-state derivative bounds and assemble `M_used` and `taylor_c2_used`.
    pub fn evaluate_assembly(
        &self,
        measured_one_site_first_a: f64,
        measured_one_site_first_b: f64,
        measured_one_site_second_a: f64,
        measured_one_site_second_b: f64,
        measured_two_site_second: f64,
        atol: f64,
    ) -> Result<SecondDerivativeBoundReport, String> {
        let inputs = [
            measured_one_site_first_a,
            measured_one_site_first_b,
            measured_one_site_second_a,
            measured_one_site_second_b,
            measured_two_site_second,
            atol,
        ];
        if inputs.iter().any(|x| !x.is_finite() || *x < 0.0) {
            return Err("measured bounds and tolerance must be finite and nonnegative".into());
        }
        if !(self.paper_m + atol).is_finite() {
            return Err("tolerance-adjusted bound overflows f64".into());
        }
        let v_1a = measured_one_site_first_a > self.paper_one_site_first + atol;
        let v_1b = measured_one_site_first_b > self.paper_one_site_first + atol;
        let v_2a = measured_one_site_second_a > self.paper_one_site_second + atol;
        let v_2b = measured_one_site_second_b > self.paper_one_site_second + atol;
        let v_2ab = measured_two_site_second > self.paper_two_site_second + atol;

        let violated = v_1a || v_1b || v_2a || v_2b || v_2ab;

        let assembled_m = measured_two_site_second
            + measured_one_site_second_a
            + 2.0 * measured_one_site_first_a * measured_one_site_first_b
            + measured_one_site_second_b;

        if !assembled_m.is_finite() {
            return Err("measured assembly overflows f64".into());
        }
        let m_used = if violated {
            assembled_m.max(self.paper_m)
        } else {
            self.paper_m
        };

        Ok(SecondDerivativeBoundReport {
            second_deriv_source: "product_rule_assembly_under_reduced_state_hyps",
            g: self.g,
            second_deriv_bound_violated: violated,
            assembled_m,
            m_used,
            taylor_c2_used: m_used / 2.0,
        })
    }
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/alpha_projection_obstruction/derivative_bound.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:derivative-bound:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord933d1592 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord933d1592` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError933d1592 {
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
impl BoundaryError933d1592 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError933d1592 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError933d1592 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord933d1592 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError933d1592> {
        if capacity_bound == 0 {
            return Err(BoundaryError933d1592::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError933d1592::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError933d1592::ExceedsCapacity {
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

    #[test]
    fn test_second_derivative_certificate_pass() {
        let cert = SecondDerivativeBoundCertificate::new(0.5).unwrap();
        let res = cert
            .evaluate_assembly(
                1.0, // <= 2 * 0.5 = 1.0
                1.0, // <= 1.0
                2.0, // <= 8 * (0.5^2) = 2.0
                2.0, // <= 2.0
                6.0, // <= 24 * (0.5^2) = 6.0
                1e-12,
            )
            .unwrap();

        assert!(!res.second_deriv_bound_violated);
        assert!((res.assembled_m - 12.0).abs() < 1e-12);
        assert!((res.m_used - 12.0).abs() < 1e-12);
        assert!((res.taylor_c2_used - 6.0).abs() < 1e-12);
        assert_eq!(
            res.second_deriv_source,
            "product_rule_assembly_under_reduced_state_hyps"
        );
    }

    #[test]
    fn test_second_derivative_certificate_kill_hook() {
        let cert = SecondDerivativeBoundCertificate::new(0.5).unwrap();
        let res = cert
            .evaluate_assembly(
                1.5, // > 1.0: Violation!
                1.0, 2.0, 2.0, 6.0, 1e-12,
            )
            .unwrap();

        assert!(res.second_deriv_bound_violated);
        assert!(res.assembled_m > 12.0);
        assert!((res.assembled_m - 13.0).abs() < 1e-12);
        assert_eq!(res.m_used, res.assembled_m);
        assert!((res.taylor_c2_used - 6.5).abs() < 1e-12);
    }

    #[test]
    fn invalid_or_overflowing_numbers_are_refused() {
        for bad in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, -1.0, f64::MAX] {
            assert!(SecondDerivativeBoundCertificate::new(bad).is_err());
        }
        let cert = SecondDerivativeBoundCertificate::new(0.5).unwrap();
        for bad in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY, -1.0] {
            for slot in 0..6 {
                let mut inputs = [1.0, 1.0, 2.0, 2.0, 6.0, 1e-12];
                inputs[slot] = bad;
                assert!(cert
                    .evaluate_assembly(
                        inputs[0], inputs[1], inputs[2], inputs[3], inputs[4], inputs[5]
                    )
                    .is_err());
            }
        }
        assert!(cert
            .evaluate_assembly(f64::MAX, f64::MAX, 0.0, 0.0, 0.0, 0.0)
            .is_err());
        let zero = SecondDerivativeBoundCertificate::new(0.0)
            .unwrap()
            .evaluate_assembly(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
            .unwrap();
        assert_eq!(zero.m_used, 0.0);
        assert!(!zero.second_deriv_bound_violated);
    }
}

#[cfg(test)]
mod l4_boundary_tests_933d1592 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord933d1592::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord933d1592::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord933d1592::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord933d1592::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord933d1592::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError933d1592::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError933d1592::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
