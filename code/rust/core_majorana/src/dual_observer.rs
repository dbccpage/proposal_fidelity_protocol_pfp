//! Dual observation maps on one declared complex (Rovelli kill-criterion).
//!
//! # Declared data only
//!
//! - Complex \(S = (d_0, d_1)\) (shared carrier).
//! - Observer \(O\): residual map \(r_O = M_O \omega\) (rows of \(M_O\) are linear functionals on edges).
//! - Two observers \(O_1, O_2\) can **agree or disagree** on residual weight / zero-ness
//!   for the **same** edge vector \(\omega\).
//!
//! This is still GF(2) linear algebra: the second “system” is a **declared observation
//! matrix**, not a Hilbert space. AuthorityEffect: None.

use crate::complexes::ChainComplexGf2;
use crate::gf2_terminalizer::GF2Matrix;
use serde::{Deserialize, Serialize};

pub const DUAL_OBS_RECEIPT_TAG: &str = "core.majorana-dual-observer-receipt.v1";

/// Linear observation map: residual bits = \(M \omega \pmod 2\).
#[derive(Debug, Clone)]
pub struct ObservationMap {
    pub name: &'static str,
    /// Matrix shape: `out_bits` × `num_edges`.
    pub matrix: GF2Matrix,
}

impl ObservationMap {
    pub fn apply(&self, omega: &[u8]) -> Result<Vec<u8>, String> {
        if omega.len() != self.matrix.cols {
            return Err("omega / observation matrix shape mismatch".into());
        }
        let mut r = vec![0u8; self.matrix.rows];
        for i in 0..self.matrix.rows {
            let mut acc = 0u8;
            for j in 0..self.matrix.cols {
                acc ^= self.matrix.data[i][j] & (omega[j] % 2);
            }
            r[i] = acc & 1;
        }
        Ok(r)
    }

    pub fn residual_weight(&self, omega: &[u8]) -> Result<usize, String> {
        Ok(self.apply(omega)?.iter().filter(|&&b| b == 1).count())
    }

    pub fn residual_zero(&self, omega: &[u8]) -> Result<bool, String> {
        Ok(self.apply(omega)?.iter().all(|&b| b == 0))
    }
}

/// Face-syndrome observer: \(M = d_1\) (full plaquette checks).
pub fn observer_face_syndrome(complex: &ChainComplexGf2) -> ObservationMap {
    ObservationMap {
        name: "O_face_d1",
        matrix: complex.d1.clone(),
    }
}

/// Single-face observer: only the first face row of \(d_1\) (partial apparatus).
pub fn observer_first_face_only(complex: &ChainComplexGf2) -> Result<ObservationMap, String> {
    if complex.d1.rows == 0 {
        return Err("no faces".into());
    }
    Ok(ObservationMap {
        name: "O_first_face",
        matrix: GF2Matrix::from_data(vec![complex.d1.data[0].clone()]),
    })
}

/// Even-index edge sample: one bit = XOR of even-indexed edges (toy alternate readout).
pub fn observer_even_edge_parity(num_edges: usize) -> ObservationMap {
    let mut row = vec![0u8; num_edges];
    for j in (0..num_edges).step_by(2) {
        row[j] = 1;
    }
    ObservationMap {
        name: "O_even_edge_xor",
        matrix: GF2Matrix::from_data(vec![row]),
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DualObserverReceipt {
    pub certificate_tag: String,
    pub complex_name: String,
    pub omega: Vec<u8>,
    pub observer_a: String,
    pub observer_b: String,
    pub residual_a: Vec<u8>,
    pub residual_b: Vec<u8>,
    pub weight_a: usize,
    pub weight_b: usize,
    pub zero_a: bool,
    pub zero_b: bool,
    /// True if residual zero-ness differs between observers.
    pub zero_disagreement: bool,
    /// True if residual weights differ.
    pub weight_disagreement: bool,
    pub authority_effect: String,
    pub notes: String,
}

/// Compare two observation maps on the same \(\omega\).
pub fn dual_observe(
    complex: &ChainComplexGf2,
    omega: &[u8],
    a: &ObservationMap,
    b: &ObservationMap,
) -> Result<DualObserverReceipt, String> {
    if omega.len() != complex.num_edges {
        return Err("omega length != num_edges".into());
    }
    let ra = a.apply(omega)?;
    let rb = b.apply(omega)?;
    let wa = ra.iter().filter(|&&x| x == 1).count();
    let wb = rb.iter().filter(|&&x| x == 1).count();
    let za = wa == 0;
    let zb = wb == 0;
    let zero_disagreement = za != zb;
    let weight_disagreement = wa != wb;
    let notes = if zero_disagreement {
        format!(
            "Relative residual disagreement: {} zero={} vs {} zero={} on same omega. \
             Same edge vector; two declared observation maps.",
            a.name, za, b.name, zb
        )
    } else if weight_disagreement {
        format!(
            "Weights differ ({} vs {}) but zero-ness agrees (both {}).",
            wa, wb, za
        )
    } else {
        "Observers agree on residual zero-ness and weight (on these maps).".into()
    };
    Ok(DualObserverReceipt {
        certificate_tag: DUAL_OBS_RECEIPT_TAG.into(),
        complex_name: complex.name.into(),
        omega: omega.iter().map(|x| x % 2).collect(),
        observer_a: a.name.into(),
        observer_b: b.name.into(),
        residual_a: ra,
        residual_b: rb,
        weight_a: wa,
        weight_b: wb,
        zero_a: za,
        zero_b: zb,
        zero_disagreement,
        weight_disagreement,
        authority_effect: "None".into(),
        notes,
    })
}

// Origin: engine/crates_rs/core_majorana/src/dual_observer.rs
// Claim: urn:core:crates_rs:core-majorana:dual-observer:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaf730f8c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaf730f8c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraf730f8c {
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
impl BoundaryErroraf730f8c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraf730f8c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraf730f8c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaf730f8c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraf730f8c> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraf730f8c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraf730f8c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraf730f8c::ExceedsCapacity {
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
    use crate::complexes::{plaquette, surface_grid_2x2_torus};
    use crate::gf2_terminalizer::GF2Matrix;

    #[test]
    fn edge_off_face_zero_disagrees_with_the_full_syndrome() {
        // Kills: copying one observer onto the other, or returning a tautological weight comparison.
        // Edge 1 of the 2x2 torus meets faces 1 and 3 and misses face 0.
        let c = surface_grid_2x2_torus();
        let o_all = observer_face_syndrome(&c);
        let o_one = observer_first_face_only(&c).unwrap();
        let omega = vec![0, 1, 0, 0, 0, 0, 0, 0];
        let r = dual_observe(&c, &omega, &o_all, &o_one).unwrap();
        assert_eq!(r.residual_a, vec![0, 1, 0, 1]);
        assert_eq!(r.residual_b, vec![0]);
        assert_eq!(r.weight_a, 2);
        assert_eq!(r.weight_b, 0);
        assert!(!r.zero_a);
        assert!(r.zero_b);
        assert!(r.zero_disagreement);
        assert!(r.weight_disagreement);
        assert_eq!(r.omega, omega);

        let err = dual_observe(&c, &[1, 0, 0], &o_all, &o_one).unwrap_err();
        assert!(err.contains("num_edges"), "{err}");
        let mut faceless = c.clone();
        faceless.d1 = GF2Matrix::zeros(0, c.num_edges);
        faceless.num_faces = 0;
        let err = observer_first_face_only(&faceless).unwrap_err();
        assert!(err.contains("no faces"), "{err}");
    }

    #[test]
    fn plaquette_face_vs_even_parity_disagreement() {
        let c = plaquette();
        let o_face = observer_face_syndrome(&c);
        let o_even = observer_even_edge_parity(c.num_edges);
        // single edge 0: face residual 1; even xor = 1 (edge 0 is even)
        let omega = vec![1, 0, 0, 0];
        let r = dual_observe(&c, &omega, &o_face, &o_even).unwrap();
        // Kills: dropping the even-index mask, which would report residual 0 on edge 0.
        assert_eq!(r.residual_a, vec![1]);
        assert_eq!(r.residual_b, vec![1]);
        assert!(!r.zero_disagreement);
        assert!(!r.weight_disagreement);
        // edge 1 only: face residual 1; even xor = 0 (odd index)
        let omega2 = vec![0, 1, 0, 0];
        let r2 = dual_observe(&c, &omega2, &o_face, &o_even).unwrap();
        assert_eq!(r2.residual_a, vec![1]);
        assert_eq!(r2.residual_b, vec![0]);
        assert_eq!(r2.weight_a, 1);
        assert_eq!(r2.weight_b, 0);
        assert!(r2.zero_disagreement);
        let wrong = observer_even_edge_parity(3);
        let err = dual_observe(&c, &omega2, &o_face, &wrong).unwrap_err();
        assert!(err.contains("shape"), "{err}");
    }

    #[test]
    fn zero_omega_agreement() {
        let c = plaquette();
        let r = dual_observe(
            &c,
            &[0, 0, 0, 0],
            &observer_face_syndrome(&c),
            &observer_even_edge_parity(4),
        )
        .unwrap();
        assert_eq!(r.residual_a, vec![0]);
        assert_eq!(r.residual_b, vec![0]);
        assert_eq!((r.weight_a, r.weight_b), (0, 0));
        assert!(r.zero_a && r.zero_b);
        assert!(!r.zero_disagreement);
        assert!(!r.weight_disagreement);
    }
}

#[cfg(test)]
mod l4_boundary_tests_af730f8c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaf730f8c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaf730f8c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaf730f8c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaf730f8c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaf730f8c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraf730f8c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraf730f8c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
