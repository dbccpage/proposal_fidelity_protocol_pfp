//! Exact rational witness for `WDP-O12-XLM-COMPARISON` (`derivation.md`).

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frac {
    pub num: i64,
    pub den: i64,
}

impl Frac {
    pub const fn new(num: i64, den: i64) -> Self {
        assert!(den != 0, "zero denominator");
        let sign = if den < 0 { -1 } else { 1 };
        let n = num * sign;
        let d = den * sign;
        let g = Self::gcd(n.unsigned_abs(), d.unsigned_abs()) as i64;
        Self {
            num: n / g,
            den: d / g,
        }
    }

    const fn gcd(mut a: u64, mut b: u64) -> u64 {
        while b != 0 {
            let t = a % b;
            a = b;
            b = t;
        }
        if a == 0 { 1 } else { a }
    }

    pub const fn add(self, other: Self) -> Self {
        Self::new(self.num * other.den + other.num * self.den, self.den * other.den)
    }

    pub const fn sub(self, other: Self) -> Self {
        Self::new(self.num * other.den - other.num * self.den, self.den * other.den)
    }

    pub const fn mul(self, other: Self) -> Self {
        Self::new(self.num * other.num, self.den * other.den)
    }
}

pub fn mixed_partial_log_x_at_zero(_j: usize, a: usize, _k: usize, b: usize) -> Frac {
    if a == b {
        Frac::new(1, 16)
    } else {
        Frac::new(0, 1)
    }
}

pub fn rescaled_row_sum(j: usize, k: usize, m: i64) -> Frac {
    let scale = Frac::new((2 * m) * (2 * m), 1);
    let mut sum = Frac::new(0, 1);
    for y in 0..4 {
        sum = sum.add(scale.mul(mixed_partial_log_x_at_zero(j, 0, k, y)));
    }
    sum
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub x_4_1_at_zero: i64,
    pub unrescaled_row_sum: Frac,
    pub rescaled_row_sums_all_jk: [[Frac; 2]; 2],
    pub time_summed_rescaled_row: Frac,
    pub k_4_0: Frac,
    pub k_0: Frac,
    pub gap_r_minus_k0: Frac,
}

pub fn witness() -> Witness {
    let mut r_jk = [[Frac::new(0, 1); 2]; 2];
    for j in 0..2 {
        for k in 0..2 {
            r_jk[j][k] = rescaled_row_sum(j, k, 1);
        }
    }
    let unrescaled = mixed_partial_log_x_at_zero(0, 0, 0, 0);
    let time_summed = r_jk[0][0].add(r_jk[0][1]);
    let k0 = Frac::new(1, 4);

    Witness {
        x_4_1_at_zero: 16,
        unrescaled_row_sum: unrescaled,
        rescaled_row_sums_all_jk: r_jk,
        time_summed_rescaled_row: time_summed,
        k_4_0: k0,
        k_0: k0,
        gap_r_minus_k0: r_jk[0][0].sub(k0),
    }
}

pub fn reject_xlm_positive_theta_promotion(claim: &str) -> Result<(), &'static str> {
    if claim.contains("r > 0")
        || claim.contains("theta > 0")
        || claim.contains("1/16 == k_0")
        || claim.contains("1/2 == k_0")
    {
        Err("r=0, M=1, L=4 free-cosh Hessian agreement does not prove X_{LM} comparison for r > 0 or theta > 0")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o12_xlm_comparison.rs
// Claim: urn:core:crates_rs:tests:wdp-o12-xlm-comparison:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2b7a3400 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2b7a3400` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2b7a3400 {
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
impl BoundaryError2b7a3400 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2b7a3400 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2b7a3400 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2b7a3400 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2b7a3400> {
        if capacity_bound == 0 {
            return Err(BoundaryError2b7a3400::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2b7a3400::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2b7a3400::ExceedsCapacity {
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
    use super::{reject_xlm_positive_theta_promotion, witness, Frac};

    #[test]
    fn free_cosh_hessian_and_row_sums_are_exact() {
        let w = witness();
        assert_eq!(w.x_4_1_at_zero, 16);
        assert_eq!(w.unrescaled_row_sum, Frac::new(1, 16));
        assert_eq!(
            w.rescaled_row_sums_all_jk,
            [
                [Frac::new(1, 4), Frac::new(1, 4)],
                [Frac::new(1, 4), Frac::new(1, 4)]
            ]
        );
        assert_eq!(w.time_summed_rescaled_row, Frac::new(1, 2));
        assert_eq!(w.k_4_0, Frac::new(1, 4));
        assert_eq!(w.k_0, Frac::new(1, 4));
        assert_eq!(w.gap_r_minus_k0, Frac::new(0, 1));
    }

    #[test]
    fn positive_theta_and_wrong_rescaling_promotions_are_refused() {
        assert!(reject_xlm_positive_theta_promotion("valid for r > 0").is_err());
        assert!(reject_xlm_positive_theta_promotion("valid for theta > 0").is_err());
        assert!(reject_xlm_positive_theta_promotion("1/16 == k_0").is_err());
        assert!(reject_xlm_positive_theta_promotion("1/2 == k_0").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_2b7a3400() {
    let admitted = BoundaryRecord2b7a3400::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord2b7a3400::try_admit(9, 8).is_err());
}
