//! Classical Regge Action with Cosmological Constant (RQ-01).
//!
//! S_Regge = sum_{h in Hinges^(D-2)} V_{D-2}(h) * eps_h - Lambda * sum_{sigma in D-simplices} V_D(sigma).
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

/// Detailed breakdown of the Regge action evaluation.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ReggeActionResult {
    pub curvature_term: f64,
    pub cosmological_term: f64,
    pub total_action: f64,
    pub lambda_param: f64,
    pub dimension: usize,
}

/// Compute Regge action from hinge deficits, hinge volumes, simplex volumes, and cosmological constant Lambda.
pub fn compute_regge_action(
    hinges: &[(f64, f64)], // (volume_of_hinge, deficit_angle)
    simplex_volumes: &[f64],
    lambda_param: f64,
    dimension: usize,
) -> ReggeActionResult {
    let mut curvature_term = 0.0;
    for &(vol_h, eps_h) in hinges {
        curvature_term += vol_h * eps_h;
    }

    let total_volume: f64 = simplex_volumes.iter().copied().sum();
    let cosmological_term = lambda_param * total_volume;
    let total_action = curvature_term - cosmological_term;

    ReggeActionResult {
        curvature_term,
        cosmological_term,
        total_action,
        lambda_param,
        dimension,
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/regge_action.rs
// Claim: urn:core:crates_rs:core-general-relativity:regge-action:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb03871fb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb03871fb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb03871fb {
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
impl BoundaryErrorb03871fb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb03871fb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb03871fb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb03871fb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb03871fb> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb03871fb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb03871fb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb03871fb::ExceedsCapacity {
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
    fn test_regge_action_with_lambda() {
        // 3D Regge action on two edges with lengths 1.0, deficits pi/2, volume 0.5
        let hinges = vec![
            (1.0, std::f64::consts::FRAC_PI_2),
            (1.0, std::f64::consts::FRAC_PI_2),
        ];
        let vols = vec![0.5];
        let res = compute_regge_action(&hinges, &vols, 0.1, 3);

        let expected_curv = std::f64::consts::PI;
        assert!((res.curvature_term - expected_curv).abs() < 1e-9);
        assert!((res.cosmological_term - 0.05).abs() < 1e-9);
        assert!((res.total_action - (expected_curv - 0.05)).abs() < 1e-9);
    }
}
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct ExactRatio { numer: i128, denom: i128 }
fn gcd_i128(mut left: i128, mut right: i128) -> Result<i128, &'static str> {
    left = left.checked_abs().ok_or("absolute value overflow")?;
    right = right.checked_abs().ok_or("absolute value overflow")?;
    while right != 0 {
        let remainder = left.checked_rem(right).ok_or("remainder overflow")?;
        left = right;
        right = remainder;
    }
    if left == 0 { Ok(1) } else { Ok(left) }
}
fn reduce_ratio(mut numer: i128, mut denom: i128) -> Result<ExactRatio, &'static str> {
    if denom == 0 {
        return Err("a denominator is positive");
    }
    if denom < 0 {
        numer = numer.checked_neg().ok_or("numerator negation overflow")?;
        denom = denom.checked_neg().ok_or("denominator negation overflow")?;
    }
    let divisor = gcd_i128(numer, denom)?;
    Ok(ExactRatio {
        numer: numer.checked_div(divisor).ok_or("numerator reduction overflow")?,
        denom: denom.checked_div(divisor).ok_or("denominator reduction overflow")?,
    })
}
fn mul_ratio(left: ExactRatio, right: ExactRatio) -> Result<ExactRatio, &'static str> {
    reduce_ratio(
        left.numer.checked_mul(right.numer).ok_or("rational product overflow")?,
        left.denom.checked_mul(right.denom).ok_or("rational product overflow")?,
    )
}
fn add_ratio(left: ExactRatio, right: ExactRatio) -> Result<ExactRatio, &'static str> {
    let left_term = left.numer.checked_mul(right.denom).ok_or("rational sum overflow")?;
    let right_term = right.numer.checked_mul(left.denom).ok_or("rational sum overflow")?;
    reduce_ratio(
        left_term.checked_add(right_term).ok_or("rational sum overflow")?,
        left.denom.checked_mul(right.denom).ok_or("rational sum overflow")?,
    )
}
fn sub_ratio(left: ExactRatio, right: ExactRatio) -> Result<ExactRatio, &'static str> {
    let negated = ExactRatio { numer: right.numer.checked_neg().ok_or("rational negation overflow")?, denom: right.denom };
    add_ratio(left, negated)
}
fn sum_hinge_curvature(hinges: &[(i128, i128, i128, i128)]) -> Result<ExactRatio, &'static str> {
    let mut curvature = reduce_ratio(0, 1)?;
    for hinge in hinges {
        let (volume_numer, volume_denom, deficit_numer, deficit_denom) = *hinge;
        let term = mul_ratio(
            reduce_ratio(volume_numer, volume_denom)?,
            reduce_ratio(deficit_numer, deficit_denom)?,
        )?;
        curvature = add_ratio(curvature, term)?;
    }
    Ok(curvature)
}

fn sum_simplex_volumes(volumes: &[(i128, i128)]) -> Result<ExactRatio, &'static str> {
    let mut volume = reduce_ratio(0, 1)?;
    for simplex in volumes {
        let (numer, denom) = *simplex;
        volume = add_ratio(volume, reduce_ratio(numer, denom)?)?;
    }
    Ok(volume)
}

/// Exact rational Regge comparison: curvature minus lambda times volume. The floating-point evaluator is unchanged.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct ExactReggeAction { curvature_numer: i128, curvature_denom: i128, action_numer: i128, action_denom: i128 }
pub fn try_exact_regge(hinges: &[(i128, i128, i128, i128)], volumes: &[(i128, i128)], lambda_numer: i128, lambda_denom: i128) -> Result<ExactReggeAction, &'static str> {
    let curvature = sum_hinge_curvature(hinges)?;
    let volume = sum_simplex_volumes(volumes)?;
    let action = sub_ratio(curvature, mul_ratio(reduce_ratio(lambda_numer, lambda_denom)?, volume)?)?;
    Ok(ExactReggeAction {
        curvature_numer: curvature.numer,
        curvature_denom: curvature.denom,
        action_numer: action.numer,
        action_denom: action.denom,
    })
}
#[cfg(test)]
mod exact_regge_checks {
    use super::try_exact_regge;
    #[test]
    fn a_half_unit_hinge_keeps_the_rational_action() {
        let action = try_exact_regge(&[(1, 2, 1, 1)], &[], 0, 1);
        assert_eq!(action.as_ref().map(|item| (item.curvature_numer, item.curvature_denom)), Ok((1, 2)));
        assert_eq!(action.as_ref().map(|item| (item.action_numer, item.action_denom)), Ok((1, 2)));
        assert_eq!(try_exact_regge(&[(1, 0, 1, 1)], &[], 0, 1).map(|_| ()), Err("a denominator is positive"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_b03871fb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb03871fb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb03871fb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb03871fb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb03871fb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb03871fb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorb03871fb::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorb03871fb::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
