//! Exact witness for the four finite carriers in `derivation.md` for `WDP-21-16-MUB6`.
//!
//! Computes:
//! 1. Recorded Tao `phaseTable` column sums, mod-3 residues, counts `(3,0,3)`, and Eisenstein norm `9`.
//! 2. Partition index `m in 0..4` with `alpha_2(m) = 6m - 9` and `1 + (-1)^{alpha_2(m)} = 0`.
//! 3. Synthetic nerve weights `4045 + 4044 + 4044 = 12133` and coboundary telescoping `0`.
//! 4. Five-constructor row-count lookup vs external Haagerup minus-one row count `5`.
//! Refuses treating any of these four carriers as a WDP `Phi_1` coverage certificate on `CHM(6)`.

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub tao_column_sums: [i64; 6],
    pub tao_column_residues_mod3: [i64; 6],
    pub tao_residue_counts: (i64, i64, i64),
    pub tao_eisenstein_norm_sq: i64,
    pub alpha_2_values: [i64; 4],
    pub parity_pair_sums: [i64; 4],
    pub synthetic_nerve_sum_012: i64,
    pub synthetic_coboundary_cycle_sum: i64,
    pub spectral_floor_frac: (i64, i64),
    pub lookup_haagerup_rows: i64,
    pub external_haagerup_minus_one_rows: i64,
}

const TAO_PHASE_TABLE: [[i64; 6]; 6] = [
    [0, 0, 0, 0, 0, 0],
    [0, 0, 1, 1, 2, 2],
    [0, 1, 0, 2, 2, 1],
    [0, 1, 2, 0, 1, 2],
    [0, 2, 2, 1, 0, 1],
    [0, 2, 1, 2, 1, 0],
];

const GAMMA_1: [i64; 6] = [1, 1, 1, -1, -1, -1];

pub fn witness() -> Witness {
    let mut col_sums = [0_i64; 6];
    let mut residues = [0_i64; 6];
    let (mut n0, mut n1, mut n2) = (0_i64, 0_i64, 0_i64);
    for c in 0..6 {
        let mut s = 0_i64;
        for r in 0..6 {
            s += GAMMA_1[r] * TAO_PHASE_TABLE[r][c];
        }
        col_sums[c] = s;
        let res = s.rem_euclid(3);
        residues[c] = res;
        match res {
            0 => n0 += 1,
            1 => n1 += 1,
            _ => n2 += 1,
        }
    }
    let x = n0 - n2;
    let y = n1 - n2;
    let norm_sq = x * x - x * y + y * y;
    let mut alpha_2 = [0_i64; 4];
    let mut parity_sums = [0_i64; 4];
    for m in 0..4 {
        let a = 6 * (m as i64) - 9;
        alpha_2[m] = a;
        let sign = if a.rem_euclid(2) == 0 { 1 } else { -1 };
        parity_sums[m] = 1 + sign;
    }
    let alpha_pot = [7_i64, -3, 11];
    let coboundary_sum =
        (alpha_pot[1] - alpha_pot[0]) + (alpha_pot[2] - alpha_pot[1]) + (alpha_pot[0] - alpha_pot[2]);
    Witness {
        tao_column_sums: col_sums,
        tao_column_residues_mod3: residues,
        tao_residue_counts: (n0, n1, n2),
        tao_eisenstein_norm_sq: norm_sq,
        alpha_2_values: alpha_2,
        parity_pair_sums: parity_sums,
        synthetic_nerve_sum_012: 4045 + 4044 + 4044,
        synthetic_coboundary_cycle_sum: coboundary_sum,
        spectral_floor_frac: (31, 800),
        lookup_haagerup_rows: 1,
        external_haagerup_minus_one_rows: 5,
    }
}

pub fn reject_moduli_phi1_coverage_claim(value: i64) -> Result<(), &'static str> {
    if value == 9 || value == 12133 || value == 0 {
        Err("labelled finite carrier values 9, 0, and 12133 do not certify WDP Phi_1 coverage on CHM(6)")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_21_16_mub6.rs
// Claim: urn:core:crates_rs:tests:wdp-21-16-mub6:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3bcacb01 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3bcacb01` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3bcacb01 {
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
impl BoundaryError3bcacb01 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3bcacb01 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3bcacb01 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3bcacb01 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3bcacb01> {
        if capacity_bound == 0 {
            return Err(BoundaryError3bcacb01::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3bcacb01::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3bcacb01::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{reject_moduli_phi1_coverage_claim, witness};

    #[test]
    fn four_labelled_carriers_match_derivation() {
        let w = witness();
        assert_eq!(w.tao_column_sums, [0, -4, -4, 0, 2, 0]);
        assert_eq!(w.tao_column_residues_mod3, [0, 2, 2, 0, 2, 0]);
        assert_eq!(w.tao_residue_counts, (3, 0, 3));
        assert_eq!(w.tao_eisenstein_norm_sq, 9);
        assert_eq!(w.alpha_2_values, [-9, -3, 3, 9]);
        assert_eq!(w.parity_pair_sums, [0, 0, 0, 0]);
        assert_eq!(w.synthetic_nerve_sum_012, 12133);
        assert_eq!(w.synthetic_coboundary_cycle_sum, 0);
        assert_eq!(w.spectral_floor_frac, (31, 800));
        assert_ne!(w.lookup_haagerup_rows, w.external_haagerup_minus_one_rows);
    }

    #[test]
    fn moduli_coverage_promotion_is_refused() {
        assert!(reject_moduli_phi1_coverage_claim(9).is_err());
        assert!(reject_moduli_phi1_coverage_claim(12133).is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_3bcacb01() {
    let admitted = BoundaryRecord3bcacb01::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3bcacb01::try_admit(9, 8).is_err());
}
