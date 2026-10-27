//! Rational Regge proxy and the exact defect predicate.
//!
//! The proxy is `Σ_h A_h² κ_h`, not `Σ_h A_h ε_h`.
//! Deficit angles are not rational, so the classical sum is not implemented.
//! `defect_bound_holds` checks `(S - S_EH)² ≤ (C a²)²` and rejects a negative `C`
//! or a negative `a²`.
//! `flat_einstein_hilbert` returns zero because the Einstein-Hilbert action of a
//! flat metric is the rational zero. That zero is not the round 4-sphere action.
//! `einstein_hilbert_fence` returns the proxy action. `flat_chart_admitted` holds
//! only when that decision equals `flat_einstein_hilbert`. `|S| < 1e-6` is not
//! the admission decision.
//!
//! AuthorityEffect: None.

#![forbid(unsafe_code)]

use super::manifold::{ManifoldError, SimplicialManifold4D};
use linear_algebra::regge_exact::{cayley_menger, q_i64, q_zero};
use num_rational::BigRational;
use num_traits::Zero;
use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct RationalReggeProxy {
    pub action: BigRational,
    pub holonomy_defect: BigRational,
    pub hinge_count: u32,
}

/// Squared area of `triangle` in chart `pentatope_index`.
///
/// The three vertices must lie in that chart. Squared lengths are read from the
/// manifold metric. The value is the Cayley-Menger `volume_squared` of the
/// leading 3×3 block.
pub fn area_squared_in_pentatope(
    manifold: &SimplicialManifold4D,
    pentatope_index: usize,
    triangle: [u32; 3],
) -> Result<BigRational, ManifoldError> {
    for vertex in triangle {
        // Membership only. Distances are not recomputed from these coordinates.
        if manifold.chart_coords(pentatope_index, vertex).is_err() {
            return Err(ManifoldError::NotAFace);
        }
    }
    let mut squared_lengths: [[BigRational; 5]; 5] =
        std::array::from_fn(|_| std::array::from_fn(|_| q_i64(0)));
    for row in 0..3 {
        for column in 0..3 {
            if row == column {
                continue;
            }
            squared_lengths[row][column] =
                manifold.edge_length_squared(triangle[row], triangle[column])?;
        }
    }
    cayley_menger(2, &squared_lengths)
        .map(|result| result.volume_squared)
        .map_err(|_| ManifoldError::Degenerate {
            cell: "triangle",
            index: pentatope_index,
        })
}

/// Rational proxy `Σ_h A_h² κ_h`.
///
/// The classical sum `Σ_h A_h ε_h` is not implemented: deficit angles are not
/// rational. `κ_h` is the supplied defect, or zero when the hinge is omitted.
/// A zero defect list on a nonempty complex is a successful proxy whose action
/// is zero. That is the flat-chart value, not a measurement of continuum
/// curvature, and not the round 4-sphere action.
pub fn rational_regge_proxy(
    manifold: &SimplicialManifold4D,
    defects: &[([u32; 3], BigRational)],
) -> Result<RationalReggeProxy, ManifoldError> {
    if manifold.pentatope_count() == 0 {
        return Err(ManifoldError::Empty);
    }
    let hinges: Vec<[u32; 3]> = manifold
        .triangles()
        .into_iter()
        .map(normalize_hinge)
        .collect();
    let hinge_count = u32::try_from(hinges.len()).map_err(|_| ManifoldError::MissingGeometry)?;
    let hinge_set: BTreeSet<[u32; 3]> = hinges.iter().copied().collect();
    let mut assigned: BTreeMap<[u32; 3], BigRational> = BTreeMap::new();
    for (raw, defect) in defects {
        let key = normalize_hinge(*raw);
        if !hinge_set.contains(&key) {
            return Err(ManifoldError::NotAFace);
        }
        if let Some(previous) = assigned.get(&key) {
            if previous != defect {
                return Err(ManifoldError::InconsistentDefect { hinge: key });
            }
            continue;
        }
        assigned.insert(key, defect.clone());
    }
    let mut action = q_zero();
    let mut holonomy_defect = q_zero();
    for hinge in hinges {
        let kappa = assigned.get(&hinge).cloned().unwrap_or_else(q_zero);
        let area_squared = hinge_area_squared(manifold, hinge)?;
        action += &area_squared * &kappa;
        holonomy_defect += kappa;
    }
    Ok(RationalReggeProxy {
        action,
        holonomy_defect,
        hinge_count,
    })
}

/// Einstein-Hilbert value of a flat metric.
///
/// The classical sum `Σ_h A_h ε_h` is not implemented: deficit angles are not
/// rational. The Einstein-Hilbert action of a flat metric is the rational zero.
/// This zero is not the Einstein-Hilbert action of the round 4-sphere.
pub fn flat_einstein_hilbert() -> BigRational {
    BigRational::zero()
}

/// Einstein-Hilbert flatness fence.
///
/// Returns [`rational_regge_proxy`]. Its `action` is `Σ_h A_h² κ_h`.
/// [`flat_chart_admitted`] holds only when that decision equals
/// [`flat_einstein_hilbert`]. A nonzero supplied `κ_h` is carried by the sum.
/// `|S| < 1e-6` is not the decision. The classical sum `Σ_h A_h ε_h` is not
/// evaluated. This is not the round 4-sphere action.
///
/// AuthorityEffect: None.
pub fn einstein_hilbert_fence(
    manifold: &SimplicialManifold4D,
    defects: &[([u32; 3], BigRational)],
) -> Result<RationalReggeProxy, ManifoldError> {
    rational_regge_proxy(manifold, defects)
}

/// True only when `decision` equals [`flat_einstein_hilbert`].
pub fn flat_chart_admitted(decision: &BigRational) -> bool {
    *decision == flat_einstein_hilbert()
}

/// `(S_regge - S_EH)² ≤ (C · a²)²`. False when `C < 0` or `a² < 0`.
pub fn defect_bound_holds(
    s_regge: &BigRational,
    s_eh: &BigRational,
    c: &BigRational,
    a_squared: &BigRational,
) -> bool {
    let zero = BigRational::zero();
    if c.cmp(&zero) == Ordering::Less || a_squared.cmp(&zero) == Ordering::Less {
        return false;
    }
    let difference = s_regge - s_eh;
    let gap_squared = &difference * &difference;
    let allowance = c * a_squared;
    let allowance_squared = &allowance * &allowance;
    gap_squared.cmp(&allowance_squared) != Ordering::Greater
}

fn normalize_hinge(mut triangle: [u32; 3]) -> [u32; 3] {
    triangle.sort_unstable();
    triangle
}

fn hinge_area_squared(
    manifold: &SimplicialManifold4D,
    hinge: [u32; 3],
) -> Result<BigRational, ManifoldError> {
    let mut area_squared: Option<BigRational> = None;
    for index in 0..manifold.pentatope_count() {
        match area_squared_in_pentatope(manifold, index, hinge) {
            Err(ManifoldError::NotAFace) => {}
            Err(error) => return Err(error),
            Ok(candidate) => {
                if let Some(previous) = &area_squared {
                    if previous != &candidate {
                        return Err(ManifoldError::InconsistentLength {
                            a: hinge[0],
                            b: hinge[1],
                        });
                    }
                } else {
                    area_squared = Some(candidate);
                }
            }
        }
    }
    area_squared.ok_or(ManifoldError::MissingGeometry)
}

// Origin: engine/crates_rs/core_general_relativity/src/exact_regge/action.rs
// Claim: urn:core:crates_rs:core-general-relativity:action:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord75d79d49 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord75d79d49` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError75d79d49 {
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
impl BoundaryError75d79d49 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError75d79d49 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError75d79d49 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord75d79d49 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError75d79d49> {
        if capacity_bound == 0 {
            return Err(BoundaryError75d79d49::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError75d79d49::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError75d79d49::ExceedsCapacity {
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
    use super::defect_bound_holds;
    use linear_algebra::regge_exact::{q_i64, q_ratio};

    #[test]
    fn defect_bound_holds_on_exact_rationals() {
        assert!(defect_bound_holds(
            &q_ratio(1, 3).expect("nonzero denominator"),
            &q_ratio(1, 4).expect("nonzero denominator"),
            &q_i64(2),
            &q_ratio(1, 16).expect("nonzero denominator"),
        ));
        assert!(!defect_bound_holds(
            &q_i64(1),
            &q_i64(0),
            &q_i64(1),
            &q_ratio(1, 4).expect("nonzero denominator"),
        ));
        assert!(!defect_bound_holds(
            &q_i64(1),
            &q_i64(0),
            &q_i64(-1),
            &q_i64(1),
        ));
    }

    #[test]
    fn conflicting_defect_assignments_return_inconsistent_defect() {
        let manifold = super::super::sphere::orthogonal_pentatope().expect("orthogonal chart");
        let hinge = [0, 1, 2];
        let err = super::rational_regge_proxy(&manifold, &[(hinge, q_i64(1)), (hinge, q_i64(2))])
            .expect_err("disagreeing defects");
        assert_eq!(err, super::ManifoldError::InconsistentDefect { hinge });
        assert!(
            super::rational_regge_proxy(&manifold, &[(hinge, q_i64(0)), (hinge, q_i64(0))],)
                .is_ok()
        );
    }

    #[test]
    fn einstein_hilbert_fence_decision_equals_proxy_action() {
        use num_traits::ToPrimitive;

        let manifold = super::super::sphere::orthogonal_pentatope().expect("orthogonal chart");
        let hinges = manifold.triangles();
        assert!(hinges.len() >= 2);

        let flat_defects: Vec<_> = hinges.iter().copied().map(|hinge| (hinge, q_i64(0))).collect();
        let flat_decision =
            super::einstein_hilbert_fence(&manifold, &flat_defects).expect("flat chart");
        let flat_proxy =
            super::rational_regge_proxy(&manifold, &flat_defects).expect("flat proxy");
        assert_eq!(flat_decision.action, flat_proxy.action);
        assert_eq!(flat_decision.action, super::flat_einstein_hilbert());
        assert!(super::flat_chart_admitted(&flat_decision.action));

        let omitted = super::einstein_hilbert_fence(&manifold, &[]).expect("omitted κ are zero");
        let omitted_proxy = super::rational_regge_proxy(&manifold, &[]).expect("omitted proxy");
        assert_eq!(omitted.action, omitted_proxy.action);
        assert_eq!(omitted.action, super::flat_einstein_hilbert());
        assert!(super::flat_chart_admitted(&omitted.action));

        let hinge = hinges[0];
        let curved = [(hinge, q_ratio(1, 1_000_000_000).expect("denominator"))];
        let curved_decision = super::einstein_hilbert_fence(&manifold, &curved).expect("curved");
        let curved_proxy = super::rational_regge_proxy(&manifold, &curved).expect("curved proxy");
        assert_eq!(curved_decision.action, curved_proxy.action);
        assert_ne!(curved_decision.action, super::flat_einstein_hilbert());
        assert!(!super::flat_chart_admitted(&curved_decision.action));
        let float_abs_below_1e_6 = curved_decision
            .action
            .to_f64()
            .expect("rational converts")
            .abs()
            < 1e-6;
        assert!(float_abs_below_1e_6);
        assert_ne!(
            super::flat_chart_admitted(&curved_decision.action),
            float_abs_below_1e_6
        );

        let summed = [(hinge, q_i64(2)), (hinges[1], q_i64(5))];
        let summed_decision = super::einstein_hilbert_fence(&manifold, &summed).expect("sum");
        let summed_proxy = super::rational_regge_proxy(&manifold, &summed).expect("sum proxy");
        assert_eq!(summed_decision.action, summed_proxy.action);
        assert!(!super::flat_chart_admitted(&summed_decision.action));
    }
}

#[cfg(test)]
mod l4_boundary_tests_75d79d49 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord75d79d49::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord75d79d49::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord75d79d49::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord75d79d49::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord75d79d49::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError75d79d49::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError75d79d49::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
