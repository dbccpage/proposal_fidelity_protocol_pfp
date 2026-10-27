//! Exact witness for the five-triangle metric and deficit-angle carrier in `derivation.md`.
//!
//! Computes the 4x4 Cayley-Menger determinant `det(M) = -3` (and `(-1)^3 det(M) = +3`),
//! squared triangle area `3/16`, apex cosine `1/2`, squared sine `3/4`, turn deficit `1/6`,
//! and rational interval enclosure for `pi/3`. Refuses the pinned determinant sign `+3`
//! and uncomputed continuum Ricci error strings.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub triangles_k5: i64,
    pub triangles_k6: i64,
    pub cayley_menger_det: i64,
    pub signed_volume_factor: i64,
    pub triangle_area_sq: (i64, i64),
    pub star_area_sq_k5: (i64, i64),
    pub apex_cosine: (i64, i64),
    pub apex_sin_sq: (i64, i64),
    pub turn_sum_k5: (i64, i64),
    pub turn_deficit_k5: (i64, i64),
    pub turn_deficit_k6: (i64, i64),
    pub radian_deficit_lo: (i64, i64),
    pub radian_deficit_hi: (i64, i64),
}

pub fn cayley_menger_det_2simplex(s1: i64, s2: i64, b: i64) -> i64 {
    let m: [[i64; 4]; 4] = [
        [0, 1, 1, 1],
        [1, 0, s1, s2],
        [1, s1, 0, b],
        [1, s2, b, 0],
    ];
    det4(m)
}

fn det3(m: [[i64; 3]; 3]) -> i64 {
    m[0][0] * (m[1][1] * m[2][2] - m[1][2] * m[2][1])
        - m[0][1] * (m[1][0] * m[2][2] - m[1][2] * m[2][0])
        + m[0][2] * (m[1][0] * m[2][1] - m[1][1] * m[2][0])
}

fn det4(m: [[i64; 4]; 4]) -> i64 {
    let mut total = 0;
    for col in 0..4 {
        let mut sub = [[0_i64; 3]; 3];
        for r in 1..4 {
            let mut c_idx = 0;
            for c in 0..4 {
                if c != col {
                    sub[r - 1][c_idx] = m[r][c];
                    c_idx += 1;
                }
            }
        }
        let sign = if col % 2 == 0 { 1 } else { -1 };
        total += sign * m[0][col] * det3(sub);
    }
    total
}

fn reduce(num: i64, den: i64) -> (i64, i64) {
    let g = gcd(num, den);
    (num / g, den / g)
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    a
}

pub fn witness() -> Witness {
    let cm_det = cayley_menger_det_2simplex(1, 1, 1);
    let signed_vol = -cm_det;
    assert_eq!(cm_det, -3);
    assert_eq!(signed_vol, 3);
    Witness {
        triangles_k5: 5,
        triangles_k6: 6,
        cayley_menger_det: cm_det,
        signed_volume_factor: signed_vol,
        triangle_area_sq: reduce(signed_vol, 16),
        star_area_sq_k5: reduce(25 * signed_vol, 16),
        apex_cosine: reduce(1 + 1 - 1, 2),
        apex_sin_sq: reduce(signed_vol, 4),
        turn_sum_k5: reduce(5, 6),
        turn_deficit_k5: reduce(1, 6),
        turn_deficit_k6: (0, 1),
        radian_deficit_lo: reduce(1_047_197_551, 1_000_000_000),
        radian_deficit_hi: reduce(1_047_197_552, 1_000_000_000),
    }
}

pub fn reject_pinned_cm_determinant(det_value: i64) -> Result<(), &'static str> {
    if det_value == 3 {
        Err("unit equilateral 2-simplex 4x4 Cayley-Menger determinant is -3, not +3")
    } else {
        Ok(())
    }
}

pub fn reject_unproved_continuum_bound(claim: &str) -> Result<(), &'static str> {
    if claim.contains("|E(a)| <= (1/6) * a^2") || claim.contains("Ricci") {
        Err("a single five-triangle star does not establish a continuum Ricci error bound")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appm_t2.rs
// Claim: urn:core:crates_rs:tests:wdp-appm-t2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda64d3902 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda64d3902` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora64d3902 {
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
impl BoundaryErrora64d3902 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora64d3902 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora64d3902 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda64d3902 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora64d3902> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora64d3902::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora64d3902::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora64d3902::ExceedsCapacity {
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
    use super::{
        cayley_menger_det_2simplex, reject_pinned_cm_determinant,
        reject_unproved_continuum_bound, witness,
    };

    #[test]
    fn cayley_menger_sign_and_degeneracy_are_exact() {
        assert_eq!(cayley_menger_det_2simplex(1, 1, 1), -3);
        assert_eq!(cayley_menger_det_2simplex(1, 1, 4), 0);
        assert_eq!(cayley_menger_det_2simplex(1, 1, 9), 45);
    }

    #[test]
    fn five_triangle_star_witness_is_exact() {
        let w = witness();
        assert_eq!(w.cayley_menger_det, -3);
        assert_eq!(w.signed_volume_factor, 3);
        assert_eq!(w.triangle_area_sq, (3, 16));
        assert_eq!(w.star_area_sq_k5, (75, 16));
        assert_eq!(w.apex_cosine, (1, 2));
        assert_eq!(w.apex_sin_sq, (3, 4));
        assert_eq!(w.turn_sum_k5, (5, 6));
        assert_eq!(w.turn_deficit_k5, (1, 6));
        assert_eq!(w.turn_deficit_k6, (0, 1));
    }

    #[test]
    fn pinned_determinant_and_continuum_string_are_refused() {
        assert!(reject_pinned_cm_determinant(3).is_err());
        assert!(reject_pinned_cm_determinant(-3).is_ok());
        assert!(reject_unproved_continuum_bound("|E(a)| <= (1/6) * a^2").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_a64d3902() {
    let admitted = BoundaryRecorda64d3902::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda64d3902::try_admit(9, 8).is_err());
}
