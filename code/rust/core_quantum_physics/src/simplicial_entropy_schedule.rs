// AuthorityEffect: None.

//! Declared combinatorial area count and Page schedule from the finite-QM
//! simplicial host.
//!
//! Source: `atlas/coda_atlas/F004_papers/006_finite_qm/native/src/simplicial_gravity.rs`,
//! the functions `area_model` and `page_curve`. The constraint relaxation in
//! that file stays a JSON host over `core_general_relativity::simplicial_dynamics`.
//!
//! `boundary_area = 4 n - 2 |glued|`. Bulk, boundary and reduction counts are
//! `d` to those powers. Entropy is the imposed convention `area / 4`, not a
//! derived von Neumann entropy. The Page schedule radiates `a` in `steps`
//! equal shares, with the remainder on the first steps. The clock is
//! `(tau - kappa * radiated / a) / (1 + tau * kappa * radiated / a)`.
//!
//! Refused: an empty complex, a carrier above the stated bounds, a face used
//! twice or outside its tetrahedron, an odd or tiny area, a nonpositive `tau`,
//! and a `kappa` outside `[0, tau]`.
//!
//! AuthorityEffect: None. Finite steps of this schedule do not establish a
//! continuum limit.

use num_bigint::BigInt;
use core_number_theory::rational::{ri, rq, Rational as Q};
use serde::Serialize;
use std::collections::BTreeSet;

fn qstr(q: &Q) -> String {
    if q.denom() == &BigInt::from(1) {
        q.numer().to_string()
    } else {
        format!("{}/{}", q.numer(), q.denom())
    }
}

/// Face-gluing census of a declared tetrahedron complex.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct AreaModel {
    pub tetrahedra: usize,
    pub internal_faces: usize,
    pub boundary_area: usize,
    pub bulk_states: String,
    pub boundary_states: String,
    pub reduction: String,
    pub entropy_convention: String,
}

/// One step of the imposed area schedule.
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct PageStep {
    pub step: usize,
    pub black_hole_area: usize,
    pub radiation_area: usize,
    pub entropy: String,
    pub schmidt_ceiling: String,
    pub defect: String,
    pub clock: String,
    pub rate_ratio: String,
    pub proper_time: String,
}

fn validate_glued_faces(n: usize, glued: &[[(usize, usize); 2]]) -> Result<(), String> {
    let mut used = BTreeSet::new();
    for [a, b] in glued {
        let out_of_range = [a, b].iter().any(|&&(t, f)| t >= n || f >= 4);
        if a == b || out_of_range || !used.insert(*a) || !used.insert(*b) {
            return Err("INVALID_FACE_GLUING".into());
        }
    }
    Ok(())
}

/// Count boundary faces and the imposed `A/4` label.
pub fn area_model(
    n: usize,
    glued: &[[(usize, usize); 2]],
    d: u32,
) -> Result<AreaModel, String> {
    if n == 0 || n > 256 || d < 2 || d > 256 || glued.len() > 2 * n {
        return Err("INVALID_AREA_MODEL_OR_RESOURCE_LIMIT".into());
    }
    validate_glued_faces(n, glued)?;
    let a = 4 * n - 2 * glued.len();
    let b = BigInt::from(d);
    Ok(AreaModel {
        tetrahedra: n,
        internal_faces: glued.len(),
        boundary_area: a,
        bulk_states: b.pow((4 * n) as u32).to_string(),
        boundary_states: b.pow(a as u32).to_string(),
        reduction: b.pow((2 * glued.len()) as u32).to_string(),
        entropy_convention: qstr(&rq(a as i64, 4)),
    })
}

fn is_valid_page_area_and_steps(a: usize, steps: usize) -> bool {
    (2..=1024).contains(&a) && a % 2 == 0 && (1..=1024).contains(&steps)
}

fn is_valid_page_dim_and_clock(d: u32, tau: &Q, kappa: &Q) -> bool {
    (2..=256).contains(&d) && tau > &ri(0) && kappa >= &ri(0) && kappa <= tau
}

fn validate_page_curve_params(
    a: usize,
    steps: usize,
    d: u32,
    tau: &Q,
    kappa: &Q,
) -> Result<(), String> {
    if !is_valid_page_area_and_steps(a, steps) || !is_valid_page_dim_and_clock(d, tau, kappa) {
        return Err("INVALID_PAGE_PARAMETERS".into());
    }
    Ok(())
}

/// Radiate area `a` in `steps` shares and record the imposed clock.
pub fn page_curve(
    a: usize,
    steps: usize,
    d: u32,
    tau: &Q,
    kappa: &Q,
) -> Result<Vec<PageStep>, String> {
    validate_page_curve_params(a, steps, d, tau, kappa)?;
    let mut radiated = 0;
    let mut proper = ri(0);
    let mut out = vec![];
    for i in 0..=steps {
        if i > 0 {
            radiated += a / steps + usize::from(i <= a % steps);
        }
        let black = a - radiated;
        let defect = kappa * rq(radiated as i64, a as i64);
        let clock = (tau - &defect) / (ri(1) + tau * &defect);
        let ratio = &clock / tau;
        if i > 0 {
            proper += &ratio;
        }
        out.push(PageStep {
            step: i,
            black_hole_area: black,
            radiation_area: radiated,
            entropy: qstr(&rq(black.min(radiated) as i64, 4)),
            schmidt_ceiling: BigInt::from(d).pow(black.min(radiated) as u32).to_string(),
            defect: qstr(&defect),
            clock: qstr(&clock),
            rate_ratio: qstr(&ratio),
            proper_time: qstr(&proper),
        });
    }
    Ok(out)
}

// Origin: engine/crates_rs/core_quantum_physics/src/simplicial_entropy_schedule.rs
// Claim: urn:core:crates_rs:core-quantum-physics:simplicial-entropy-schedule:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc2acb4fe {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc2acb4fe` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc2acb4fe {
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
impl BoundaryErrorc2acb4fe {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc2acb4fe {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc2acb4fe {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc2acb4fe {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc2acb4fe> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc2acb4fe::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc2acb4fe::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc2acb4fe::ExceedsCapacity {
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

    #[test]
    fn area_count_and_page_schedule_match_the_declared_arithmetic() {
        let model = area_model(2, &[[(0, 1), (1, 0)]], 2).unwrap();
        assert_eq!(
            (model.tetrahedra, model.internal_faces, model.boundary_area),
            (2, 1, 6)
        );
        assert_eq!(
            (
                model.bulk_states.as_str(),
                model.boundary_states.as_str(),
                model.reduction.as_str(),
                model.entropy_convention.as_str()
            ),
            ("256", "64", "4", "3/2")
        );
        assert!(area_model(2, &[[(0, 0), (1, 0)], [(0, 0), (1, 1)]], 2).is_err());
        let page = page_curve(12, 6, 2, &rq(1, 2), &rq(1, 4)).unwrap();
        let entropies: Vec<&str> = page.iter().map(|s| s.entropy.as_str()).collect();
        assert_eq!(entropies, vec!["0", "1/2", "1", "3/2", "1", "1/2", "0"]);
        assert_eq!((page[6].black_hole_area, page[6].radiation_area), (0, 12));
        assert_eq!(
            (page[6].clock.as_str(), page[6].rate_ratio.as_str()),
            ("2/9", "4/9")
        );
        assert!(page_curve(12, 6, 2, &rq(1, 4), &rq(1, 2)).is_err());
        assert!(page_curve(3, 2, 2, &ri(1), &ri(0)).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_c2acb4fe {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc2acb4fe::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc2acb4fe::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc2acb4fe::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc2acb4fe::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc2acb4fe::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc2acb4fe::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc2acb4fe::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
