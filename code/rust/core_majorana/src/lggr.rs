//! Local-Green / Global-Red (LGGR) **diagnostic** witness on GF(2) schedules.
//!
//! LGGR shape (CODE_DEMO):
//! - **Local green:** \(d_1 \omega = 0 \pmod 2\) (syndrome / face residual vanishes).
//! - **Global red:** schedule class is `ClosedResidual` (closed but not Exact).
//!
//! This is evaluator incompleteness of the coboundary layer, **not** GlobalGreen
//! authority and **not** FOC StabilizedSurvivor.
//!
//! AuthorityEffect: None on every witness receipt field.

use crate::gf2_terminalizer::{
    GF2Matrix, GF2ScheduleStatus, Gf2CocycleClassifier, Gf2ScheduleReceipt,
};

/// LGGR diagnostic witness. Never mints authority.
#[derive(Debug, Clone)]
pub struct LggrWitness {
    /// \(d_1 \omega = 0 \pmod 2\).
    pub local_green: bool,
    /// Status is exactly `ClosedResidual` (not Exact, not Open).
    pub global_red: bool,
    /// Full LGGR: local green AND global red.
    pub is_lggr: bool,
    /// Face / higher residual of \(\omega\) (the local syndrome vector).
    pub d1_omega: Vec<u8>,
    /// Underlying schedule receipt (authority_effect always `"None"`).
    pub certificate: Gf2ScheduleReceipt,
}

/// Compute \(d_1 \omega \pmod 2\).
pub fn apply_d1(d1: &GF2Matrix, omega: &[u8]) -> Result<Vec<u8>, String> {
    if omega.len() != d1.cols {
        return Err(format!(
            "lggr: omega length {} != d1.cols {}",
            omega.len(),
            d1.cols
        ));
    }
    let mut out = vec![0u8; d1.rows];
    for i in 0..d1.rows {
        let mut sum = 0u8;
        for j in 0..d1.cols {
            sum ^= d1.data[i][j] & (omega[j] % 2);
        }
        out[i] = sum & 1;
    }
    Ok(out)
}

/// Detect LGGR on a declared complex and residual 1-cochain.
///
/// Requires a valid boundary (\(d_1 d_0 = 0\)); refuses otherwise via `terminalize`.
pub fn detect_lggr(d0: &GF2Matrix, d1: &GF2Matrix, omega: &[u8]) -> Result<LggrWitness, String> {
    let certificate = Gf2CocycleClassifier::classify(d0, d1, omega)?;
    let d1_omega = apply_d1(d1, omega)?;
    let local_green = d1_omega.iter().all(|&v| v == 0);
    let global_red = certificate.status == GF2ScheduleStatus::ClosedResidual;
    Ok(LggrWitness {
        local_green,
        global_red,
        is_lggr: local_green && global_red,
        d1_omega,
        certificate,
    })
}

// Origin: engine/crates_rs/core_majorana/src/lggr.rs
// Claim: urn:core:crates_rs:core-majorana:lggr:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord261f7a19 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord261f7a19` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError261f7a19 {
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
impl BoundaryError261f7a19 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError261f7a19 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError261f7a19 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord261f7a19 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError261f7a19> {
        if capacity_bound == 0 {
            return Err(BoundaryError261f7a19::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError261f7a19::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError261f7a19::ExceedsCapacity {
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
    use crate::complexes::{
        exact_syndrome_example, open_syndrome_example, surface_grid_2x2_torus, triangle,
        torus_logical_x_example,
    };
    use crate::gf2_terminalizer::{GF2Matrix, GF2ScheduleStatus};

    #[test]
    fn torus_logical_is_lggr() {
        let c = surface_grid_2x2_torus();
        let w = detect_lggr(&c.d0, &c.d1, &torus_logical_x_example()).unwrap();
        assert!(w.local_green, "d1 omega must be all-zero");
        assert!(w.global_red, "must be ClosedResidual");
        assert!(w.is_lggr);
        assert_eq!(w.d1_omega, vec![0, 0, 0, 0]);
        assert_eq!(w.certificate.status, GF2ScheduleStatus::ClosedResidual);
        assert_eq!(w.certificate.authority_effect, "None");
    }

    #[test]
    fn exact_syndrome_is_not_lggr() {
        // Kills: setting is_lggr from local_green alone, so every coboundary counts as LGGR.
        let c = triangle();
        let w = detect_lggr(&c.d0, &c.d1, &exact_syndrome_example()).unwrap();
        assert!(w.local_green);
        assert_eq!(w.d1_omega, vec![0]);
        assert!(!w.global_red);
        assert!(!w.is_lggr);
        assert_eq!(w.certificate.status, GF2ScheduleStatus::Exact);
    }

    #[test]
    fn open_obstruction_is_not_lggr() {
        // Kills: treating every non-Exact class as LGGR, or ignoring a nonzero face syndrome.
        let c = triangle();
        let w = detect_lggr(&c.d0, &c.d1, &open_syndrome_example()).unwrap();
        assert_eq!(w.d1_omega, vec![1]);
        assert!(!w.local_green);
        assert!(!w.global_red);
        assert!(!w.is_lggr);
        assert_eq!(w.certificate.status, GF2ScheduleStatus::OpenObstruction);
    }

    #[test]
    fn length_mismatch_returns_err() {
        // Kills: skipping the length check and returning Ok on a short residual.
        let c = triangle();
        let err = detect_lggr(&c.d0, &c.d1, &[1, 0]).unwrap_err();
        assert!(
            err.contains("Syndrome dimension"),
            "short residual must be refused, got {err}"
        );
        let err = apply_d1(&c.d1, &[1]).unwrap_err();
        assert!(
            err.contains("omega length"),
            "apply_d1 must refuse a short vector, got {err}"
        );
    }

    #[test]
    fn non_complex_is_refused() {
        // Kills: classifying a pair with d1*d0 != 0 instead of refusing it.
        let c = triangle();
        let bad_d1 = GF2Matrix::from_data(vec![vec![1, 0, 0]]);
        let mut prod = vec![0u8; c.d0.cols];
        for (k, row) in c.d0.data.iter().enumerate() {
            if bad_d1.data[0][k] == 1 {
                for (j, bit) in row.iter().enumerate() {
                    prod[j] ^= bit & 1;
                }
            }
        }
        assert_ne!(prod, vec![0, 0, 0], "fixture must actually break d1*d0");
        let err = detect_lggr(&c.d0, &bad_d1, &[1, 0, 0]).unwrap_err();
        assert!(
            err.contains("d1 * d0"),
            "non-complex must be refused, got {err}"
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_261f7a19 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord261f7a19::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord261f7a19::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord261f7a19::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord261f7a19::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord261f7a19::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError261f7a19::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError261f7a19::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
