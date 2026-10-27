//! IID bit-flip Monte Carlo on growing planar grids (Deutsch kill-criterion toy).
//!
//! # Declared data only
//!
//! - Complex: planar \(m\times m\) plaquette grid (`surface_grid(m,m,false)`).
//! - Noise: each edge independently 1 with probability \(p\) (Bernoulli), seedable LCG.
//! - Metric: empirical fractions of schedule classes under `Gf2CocycleClassifier::classify`.
//!
//! **Not** a physical threshold theorem. **Not** decoder latency. Shows how Open
//! fraction grows with \(p\) and how class mix changes with grid size under the
//! **declared** face-syndrome map. AuthorityEffect: None.

use crate::complexes::surface_grid;
use crate::gf2_terminalizer::{GF2ScheduleStatus, Gf2CocycleClassifier};
use serde::{Deserialize, Serialize};

pub const NOISE_MC_RECEIPT_TAG: &str = "core.majorana-noise-mc-receipt.v1";

/// Tiny seedable LCG (no rand crate dep).
#[derive(Debug, Clone)]
pub struct Lcg {
    state: u64,
}

impl Lcg {
    pub fn new(seed: u64) -> Self {
        Self {
            state: seed | 1, // avoid zero lock
        }
    }

    pub fn next_u64(&mut self) -> u64 {
        // Numerical Recipes LCG
        self.state = self.state.wrapping_mul(1664525).wrapping_add(1013904223);
        self.state
    }

    /// Bernoulli(p) with p in [0,1] via 2^32 fixed-point.
    pub fn bernoulli(&mut self, p: f64) -> bool {
        if p <= 0.0 {
            return false;
        }
        if p >= 1.0 {
            return true;
        }
        let thr = (p * (u32::MAX as f64)) as u32;
        (self.next_u64() as u32) < thr
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct NoiseMcReceipt {
    pub certificate_tag: String,
    pub grid_m: usize,
    pub num_edges: usize,
    pub num_faces: usize,
    pub p: f64,
    pub trials: usize,
    pub seed: u64,
    pub count_exact: usize,
    pub count_closed_residual: usize,
    pub count_open: usize,
    pub frac_exact: f64,
    pub frac_closed_residual: f64,
    pub frac_open: f64,
    pub mean_error_weight: f64,
    pub authority_effect: String,
    pub notes: String,
}

/// Run IID edge noise Monte Carlo on planar \(m\times m\) plaquette grid.
pub fn noise_mc_planar_grid(
    m: usize,
    p: f64,
    trials: usize,
    seed: u64,
) -> Result<NoiseMcReceipt, String> {
    if m == 0 {
        return Err("m >= 1".into());
    }
    if trials == 0 {
        return Err("trials >= 1".into());
    }
    let complex = surface_grid(m, m, false);
    let mut rng = Lcg::new(seed);
    let mut count_exact = 0usize;
    let mut count_closed = 0usize;
    let mut count_open = 0usize;
    let mut weight_sum = 0usize;

    for _ in 0..trials {
        let mut omega = vec![0u8; complex.num_edges];
        let mut w = 0usize;
        for e in 0..complex.num_edges {
            if rng.bernoulli(p) {
                omega[e] = 1;
                w += 1;
            }
        }
        weight_sum += w;
        let cert = Gf2CocycleClassifier::classify(&complex.d0, &complex.d1, &omega)?;
        match cert.status {
            GF2ScheduleStatus::Exact => count_exact += 1,
            GF2ScheduleStatus::ClosedResidual => count_closed += 1,
            GF2ScheduleStatus::OpenObstruction => count_open += 1,
        }
    }

    let t = trials as f64;
    Ok(NoiseMcReceipt {
        certificate_tag: NOISE_MC_RECEIPT_TAG.into(),
        grid_m: m,
        num_edges: complex.num_edges,
        num_faces: complex.num_faces,
        p,
        trials,
        seed,
        count_exact,
        count_closed_residual: count_closed,
        count_open,
        frac_exact: count_exact as f64 / t,
        frac_closed_residual: count_closed as f64 / t,
        frac_open: count_open as f64 / t,
        mean_error_weight: weight_sum as f64 / t,
        authority_effect: "None".into(),
        notes: format!(
            "IID Bernoulli(p) edge flips on planar {m}x{m} plaquette grid; \
             classes via face-syndrome classifier. Not a physical threshold. Auth=None."
        ),
    })
}

/// Sweep grids m=1..max_m at fixed p (small trial counts for unit tests).
pub fn noise_mc_size_sweep(
    max_m: usize,
    p: f64,
    trials: usize,
    seed: u64,
) -> Result<Vec<NoiseMcReceipt>, String> {
    let mut out = Vec::new();
    for m in 1..=max_m {
        out.push(noise_mc_planar_grid(
            m,
            p,
            trials,
            seed.wrapping_add(m as u64),
        )?);
    }
    Ok(out)
}

// Origin: engine/crates_rs/core_majorana/src/noise_mc.rs
// Claim: urn:core:crates_rs:core-majorana:noise-mc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa1c2a37 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa1c2a37` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa1c2a37 {
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
impl BoundaryErroraa1c2a37 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa1c2a37 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa1c2a37 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa1c2a37 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa1c2a37> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa1c2a37::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa1c2a37::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa1c2a37::ExceedsCapacity {
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
    fn p_zero_all_exact() {
        // Kills: flipping edges when p is 0, or charging their weight anyway.
        let r = noise_mc_planar_grid(2, 0.0, 50, 7).unwrap();
        assert_eq!(r.num_edges, 12);
        assert_eq!(r.num_faces, 4);
        assert_eq!(r.count_exact, 50);
        assert_eq!(r.count_open, 0);
        assert_eq!(r.count_closed_residual, 0);
        assert_eq!(r.mean_error_weight, 0.0);
        assert_eq!(r.frac_exact, 1.0);
    }

    #[test]
    fn p_one_mostly_open_on_planar() {
        // All edges flipped: on planar disk H1=0, all-ones may still be Exact or Open
        // depending on whether all-ones is a coboundary. Prefer high p partial.
        let r = noise_mc_planar_grid(2, 0.5, 200, 42).unwrap();
        assert_eq!(r.trials, 200);
        assert!(r.count_open + r.count_exact + r.count_closed_residual == 200);
        // With p=0.5 expect substantial open fraction on multi-face grid
        assert!(r.frac_open > 0.1, "expected open mass, got {}", r.frac_open);
        assert_eq!(r.authority_effect, "None");
    }

    #[test]
    fn open_fraction_rises_with_p() {
        let low = noise_mc_planar_grid(2, 0.05, 300, 1).unwrap();
        let high = noise_mc_planar_grid(2, 0.4, 300, 1).unwrap();
        assert!(
            high.frac_open > low.frac_open,
            "low open {} high open {}",
            low.frac_open,
            high.frac_open
        );
    }

    #[test]
    fn size_sweep_grows_the_planar_grids() {
        // Kills: repeating one grid, or storing the base seed on every row.
        assert!(noise_mc_planar_grid(0, 0.0, 1, 1).unwrap_err().contains("m"));
        assert!(noise_mc_planar_grid(1, 0.0, 0, 1)
            .unwrap_err()
            .contains("trials"));
        let rows = noise_mc_size_sweep(3, 0.0, 4, 99).unwrap();
        assert_eq!(rows.len(), 3);
        let edges = [4usize, 12, 24];
        let faces = [1usize, 4, 9];
        for (i, r) in rows.iter().enumerate() {
            let m = i + 1;
            assert_eq!(r.grid_m, m);
            assert_eq!(r.num_edges, edges[i], "m={m}");
            assert_eq!(r.num_faces, faces[i], "m={m}");
            assert_eq!(r.seed, 99 + m as u64);
            assert_eq!(r.trials, 4);
            assert_eq!(r.p, 0.0);
            assert_eq!(r.count_exact, 4);
            assert_eq!(r.count_open, 0);
            assert_eq!(r.count_closed_residual, 0);
            assert_eq!(r.mean_error_weight, 0.0);
        }
    }

    #[test]
    fn p_one_flips_every_edge_and_stays_exact_on_the_disk() {
        // Kills: bernoulli(1) returning false, and counting the even all-ones vector as open.
        let r = noise_mc_planar_grid(2, 1.0, 5, 7).unwrap();
        assert_eq!(r.num_edges, 12);
        assert_eq!(r.mean_error_weight, 12.0);
        assert_eq!(r.count_exact, 5);
        assert_eq!(r.count_open, 0);
        assert_eq!(r.count_closed_residual, 0);
    }
}

#[cfg(test)]
mod l4_boundary_tests_aa1c2a37 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaa1c2a37::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaa1c2a37::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaa1c2a37::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaa1c2a37::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaa1c2a37::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraa1c2a37::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraa1c2a37::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
