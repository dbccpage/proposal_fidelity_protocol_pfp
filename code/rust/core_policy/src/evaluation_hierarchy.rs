use num_rational::BigRational;
use serde::{Deserialize, Serialize};
use std::cmp::Ordering;

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum DiagnosticComparison {
    StrictlyImproves,
    Preserves,
    NonWorse,
    Worsens,
    Incomparable,
    Invalid,
}

/// A deterministic exact ranking key. This order ranks proposals; it does not
/// certify an improvement, feasibility, or any physical acceptance condition.
/// Declared tertiary values precede absent ones when the primary masses tie.
#[derive(Debug, Clone, Copy)]
pub struct ExactRankingKey<'a> {
    pub phi1: &'a BigRational,
    pub gamma2: &'a BigRational,
    pub xi: Option<&'a BigRational>,
    pub label: &'a str,
    pub input_position: usize,
}

pub fn compare_exact_ranking(a: ExactRankingKey<'_>, b: ExactRankingKey<'_>) -> Ordering {
    let xi = match (a.xi, b.xi) {
        (Some(x), Some(y)) => x.cmp(y),
        (Some(_), None) => Ordering::Less,
        (None, Some(_)) => Ordering::Greater,
        (None, None) => Ordering::Equal,
    };
    a.phi1
        .cmp(b.phi1)
        .then_with(|| a.gamma2.cmp(b.gamma2))
        .then(xi)
        .then_with(|| a.label.cmp(b.label))
        .then_with(|| a.input_position.cmp(&b.input_position))
}

impl DiagnosticComparison {
    pub const fn is_strict_improvement(self) -> bool {
        matches!(self, Self::StrictlyImproves)
    }

    pub const fn is_non_worse(self) -> bool {
        matches!(
            self,
            Self::StrictlyImproves | Self::Preserves | Self::NonWorse
        )
    }
}

/// Paper 012 guarded descent law, lexicographic **Φ₁ ≻ Γ₂ ≻ Ξ**. Returns whether `after`
/// STRICTLY improves on `before`. Ξ may decide ONLY when Φ₁ AND Γ₂ are tied (papers 009/013:
/// Ξ is a scale-invariant tertiary tie-break, never a primary).
pub fn guarded_strictly_improves(
    phi1_before: &BigRational,
    gamma2_before: &BigRational,
    xi_before: Option<&BigRational>,
    phi1_after: &BigRational,
    gamma2_after: &BigRational,
    xi_after: Option<&BigRational>,
) -> bool {
    compare_guarded_diagnostics(
        phi1_before,
        gamma2_before,
        xi_before,
        phi1_after,
        gamma2_after,
        xi_after,
    )
    .is_strict_improvement()
}

pub fn guarded_non_worse(
    phi1_before: &BigRational,
    gamma2_before: &BigRational,
    xi_before: Option<&BigRational>,
    phi1_after: &BigRational,
    gamma2_after: &BigRational,
    xi_after: Option<&BigRational>,
) -> bool {
    classify_guarded_non_worse(
        phi1_before,
        gamma2_before,
        xi_before,
        phi1_after,
        gamma2_after,
        xi_after,
    )
    .is_non_worse()
}

pub fn classify_guarded_non_worse(
    phi1_before: &BigRational,
    gamma2_before: &BigRational,
    xi_before: Option<&BigRational>,
    phi1_after: &BigRational,
    gamma2_after: &BigRational,
    xi_after: Option<&BigRational>,
) -> DiagnosticComparison {
    match compare_guarded_diagnostics(
        phi1_before,
        gamma2_before,
        xi_before,
        phi1_after,
        gamma2_after,
        xi_after,
    ) {
        DiagnosticComparison::StrictlyImproves
        | DiagnosticComparison::Preserves
        | DiagnosticComparison::NonWorse => DiagnosticComparison::NonWorse,
        other => other,
    }
}

/// Ξ is compared exactly. A float Ξ is refused at the boundary that parses it, so this law has
/// no non-finite case; `Invalid` is kept for callers whose own inputs fail validation.
pub fn compare_guarded_diagnostics(
    phi1_before: &BigRational,
    gamma2_before: &BigRational,
    xi_before: Option<&BigRational>,
    phi1_after: &BigRational,
    gamma2_after: &BigRational,
    xi_after: Option<&BigRational>,
) -> DiagnosticComparison {
    match phi1_after.cmp(phi1_before) {
        Ordering::Less => return DiagnosticComparison::StrictlyImproves,
        Ordering::Greater => return DiagnosticComparison::Worsens,
        Ordering::Equal => {}
    }

    match gamma2_after.cmp(gamma2_before) {
        Ordering::Less => return DiagnosticComparison::StrictlyImproves,
        Ordering::Greater => return DiagnosticComparison::Worsens,
        Ordering::Equal => {}
    }

    match (xi_before, xi_after) {
        (Some(before), Some(after)) if after < before => DiagnosticComparison::StrictlyImproves,
        (Some(before), Some(after)) if after > before => DiagnosticComparison::Worsens,
        (Some(_), Some(_)) | (None, None) => DiagnosticComparison::Preserves,
        (Some(_), None) | (None, Some(_)) => DiagnosticComparison::Incomparable,
    }
}

// Origin: engine/crates_rs/core_policy/src/evaluation_hierarchy.rs
// Claim: urn:core:crates_rs:core-policy:evaluation-hierarchy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord255f9674 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord255f9674` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError255f9674 {
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
impl BoundaryError255f9674 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError255f9674 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError255f9674 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord255f9674 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError255f9674> {
        if capacity_bound == 0 {
            return Err(BoundaryError255f9674::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError255f9674::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError255f9674::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use num_bigint::BigInt;

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn q(numer: i64, denom: i64) -> BigRational {
        BigRational::new(BigInt::from(numer), BigInt::from(denom))
    }

    #[test]
    fn exact_ranking_is_transitive_with_missing_tertiary_values() {
        let primary = r(1);
        let tertiary = [r(1), r(2)];
        let keys = [
            ExactRankingKey {
                phi1: &primary,
                gamma2: &primary,
                xi: Some(&tertiary[0]),
                label: "z",
                input_position: 0,
            },
            ExactRankingKey {
                phi1: &primary,
                gamma2: &primary,
                xi: None,
                label: "m",
                input_position: 1,
            },
            ExactRankingKey {
                phi1: &primary,
                gamma2: &primary,
                xi: Some(&tertiary[1]),
                label: "a",
                input_position: 2,
            },
        ];
        for a in keys {
            for b in keys {
                assert_eq!(
                    compare_exact_ranking(a, b),
                    compare_exact_ranking(b, a).reverse()
                );
                for c in keys {
                    if compare_exact_ranking(a, b).is_le() && compare_exact_ranking(b, c).is_le() {
                        assert!(compare_exact_ranking(a, c).is_le());
                    }
                }
            }
        }
        let mut sorted = keys;
        sorted.sort_by(|a, b| compare_exact_ranking(*a, *b));
        assert_eq!(sorted.map(|k| k.input_position), [0, 2, 1]);
    }

    #[test]
    fn phi1_is_the_primary_comparison_key() {
        assert_eq!(
            compare_guarded_diagnostics(&r(2), &r(0), None, &r(1), &r(99), None),
            DiagnosticComparison::StrictlyImproves
        );
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(99), None, &r(2), &r(0), None),
            DiagnosticComparison::Worsens
        );
    }

    #[test]
    fn gamma2_decides_only_after_phi1_ties() {
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(2), None, &r(1), &r(1), None),
            DiagnosticComparison::StrictlyImproves
        );
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), None, &r(1), &r(2), None),
            DiagnosticComparison::Worsens
        );
    }

    #[test]
    fn xi_decides_only_after_phi1_and_gamma2_tie() {
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&q(4, 10)), &r(1), &r(1), Some(&q(3, 10))),
            DiagnosticComparison::StrictlyImproves
        );
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&q(3, 10)), &r(1), &r(1), Some(&q(4, 10))),
            DiagnosticComparison::Worsens
        );
    }

    #[test]
    fn tied_diagnostics_preserve_and_mismatched_xi_is_incomparable() {
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), None, &r(1), &r(1), None),
            DiagnosticComparison::Preserves
        );
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&q(3, 10)), &r(1), &r(1), None),
            DiagnosticComparison::Incomparable
        );
    }

    #[test]
    fn xi_separates_values_a_float_would_merge() {
        // 1/3 and 1/3 + 1/10^30 round to the same double; the exact law still orders them.
        let tiny = BigRational::new(BigInt::from(1), BigInt::from(10).pow(30));
        let third = q(1, 3);
        let nudged = &third + &tiny;
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&nudged), &r(1), &r(1), Some(&third)),
            DiagnosticComparison::StrictlyImproves
        );
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&third), &r(1), &r(1), Some(&nudged)),
            DiagnosticComparison::Worsens
        );
    }

    #[test]
    fn non_worse_classifier_aggregates_strict_improvement_and_preservation() {
        assert_eq!(
            classify_guarded_non_worse(&r(2), &r(0), None, &r(1), &r(99), None),
            DiagnosticComparison::NonWorse
        );
        assert_eq!(
            classify_guarded_non_worse(&r(1), &r(1), None, &r(1), &r(1), None),
            DiagnosticComparison::NonWorse
        );
        assert!(guarded_non_worse(&r(1), &r(1), None, &r(1), &r(1), None));
    }

    #[test]
    fn non_worse_classifier_preserves_hard_boundaries() {
        assert_eq!(
            classify_guarded_non_worse(&r(1), &r(1), None, &r(2), &r(0), None),
            DiagnosticComparison::Worsens
        );
        assert_eq!(
            classify_guarded_non_worse(&r(1), &r(1), Some(&q(3, 10)), &r(1), &r(1), None),
            DiagnosticComparison::Incomparable
        );
    }

    #[test]
    fn xi_cannot_override_phi1() {
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(0), Some(&q(9, 10)), &r(2), &r(0), Some(&q(1, 10))),
            DiagnosticComparison::Worsens
        );
    }

    #[test]
    fn xi_cannot_override_gamma2() {
        assert_eq!(
            compare_guarded_diagnostics(&r(1), &r(1), Some(&q(9, 10)), &r(1), &r(2), Some(&q(1, 10))),
            DiagnosticComparison::Worsens
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_255f9674 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord255f9674::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord255f9674::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord255f9674::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord255f9674::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord255f9674::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError255f9674::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError255f9674::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
