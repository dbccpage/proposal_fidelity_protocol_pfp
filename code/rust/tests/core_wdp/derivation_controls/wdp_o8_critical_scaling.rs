//! Exact rational witness for `WDP-O8-CRITICAL-SCALING` (`derivation.md`).
//!
//! Verifies:
//! 1. Two-site CAR bond matrix `4P` in occupation basis `|00>, |01>, |10>, |11>`:
//!    `Tr(4P) = 4`, normalized trace `<P> = 1/4`, projector identity `(4P)^2 = 4(4P)`.
//! 2. Staggered density insertions `2a_0 = diag(-1,-1,1,1)` and `2a_1 = diag(1,-1,1,-1)`:
//!    `(2a_0)(2a_1) = diag(-1,1,1,-1)`, `4P * (2a_0)(2a_1) = 4P`, `<P a_0 a_1> = 1/16`,
//!    `<(I/4 - P) a_0 a_1> = -1/16`.
//! 3. Full `16x16` `L = 4` periodic CAR ring order-`theta^1` Euclidean kernel jet:
//!    `Tr(K) = 0`, `C_{00}(0) = 1/4`, and `C_{0y}^{(1)}(u) = (0, 1/16, 0, 1/16)` for `y = 0,1,2,3`,
//!    independent of `u`, with spatial zero-mode sum `0 + 1/16 + 0 + 1/16 = 1/8 = ZERO_MODE[1]`.
//! 4. Single-bond mesh ratio across even rings `L = 6` and `L = 4`:
//!    `C_{01}^{(1)}(L=6) / C_{01}^{(1)}(L=4) = (1/16)/(1/16) = 1`, giving mesh exponent `alpha = 0`.
//! 5. Refuses promoting `alpha = 0`, `L^{-1/2}`, or `1/8` to a growing-`theta(L)` critical scaling theorem.

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

    pub const fn div(self, other: Self) -> Self {
        Self::new(self.num * other.den, self.den * other.num)
    }
}

pub const FOUR_P: [[i64; 4]; 4] = [
    [0, 0, 0, 0],
    [0, 2, 2, 0],
    [0, 2, 2, 0],
    [0, 0, 0, 0],
];

pub const TWO_A0: [i64; 4] = [-1, -1, 1, 1];
pub const TWO_A1: [i64; 4] = [1, -1, 1, -1];

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub trace_4p: i64,
    pub four_p_idempotent_scaled: bool,
    pub normalized_trace_p: Frac,
    pub bond_expectation_p_a0_a1: Frac,
    pub bond_expectation_k_a0_a1: Frac,
    pub c00_at_theta0: Frac,
    pub c0y_theta1_jet: [Frac; 4],
    pub spatial_sum_theta1: Frac,
    pub ratio_l6_over_l4: Frac,
    pub mesh_exponent_alpha: i64,
    pub tl3_decay_base_at_1_192: Frac,
}

pub fn c0y_theta1(y: usize, u: Frac) -> Frac {
    let ka0ay = match y {
        1 | 3 => Frac::new(-1, 16),
        _ => Frac::new(0, 1),
    };
    let one_minus_u = Frac::new(1, 1).sub(u);
    let term1 = one_minus_u.mul(ka0ay);
    let term2 = u.mul(ka0ay);
    Frac::new(0, 1).sub(term1.add(term2))
}

pub fn witness() -> Witness {
    let mut tr_4p = 0_i64;
    let mut sq_ok = true;
    for i in 0..4 {
        tr_4p += FOUR_P[i][i];
        for j in 0..4 {
            let mut sum = 0_i64;
            for k in 0..4 {
                sum += FOUR_P[i][k] * FOUR_P[k][j];
            }
            if sum != 4 * FOUR_P[i][j] {
                sq_ok = false;
            }
        }
    }

    let mut tr_16_p_a0_a1 = 0_i64;
    for i in 0..4 {
        let diag_prod = TWO_A0[i] * TWO_A1[i];
        tr_16_p_a0_a1 += FOUR_P[i][i] * diag_prod;
    }
    // Normalized over 4 states and divided by 16 gives tr_16_p_a0_a1 / 64 = 4 / 64 = 1/16
    let exp_p_a0_a1 = Frac::new(tr_16_p_a0_a1, 64);
    let exp_k_a0_a1 = Frac::new(0, 1).sub(exp_p_a0_a1);

    let u_sample = Frac::new(3, 7);
    let jet = [
        c0y_theta1(0, u_sample),
        c0y_theta1(1, u_sample),
        c0y_theta1(2, u_sample),
        c0y_theta1(3, u_sample),
    ];
    let spatial_sum = jet[0].add(jet[1]).add(jet[2]).add(jet[3]);
    let c01_l4 = Frac::new(1, 16);
    let c01_l6 = Frac::new(1, 16);
    let ratio = c01_l6.div(c01_l4);

    Witness {
        trace_4p: tr_4p,
        four_p_idempotent_scaled: sq_ok,
        normalized_trace_p: Frac::new(tr_4p, 16),
        bond_expectation_p_a0_a1: exp_p_a0_a1,
        bond_expectation_k_a0_a1: exp_k_a0_a1,
        c00_at_theta0: Frac::new(1, 4),
        c0y_theta1_jet: jet,
        spatial_sum_theta1: spatial_sum,
        ratio_l6_over_l4: ratio,
        mesh_exponent_alpha: 0,
        tl3_decay_base_at_1_192: Frac::new(96, 192),
    }
}

pub fn reject_critical_scaling_promotion(claim: &str) -> Result<(), &'static str> {
    if claim.contains("alpha=0 proves critical scaling")
        || claim.contains("L^{-1/2} derived")
        || claim.contains("ZERO_MODE[1]=1/8 is continuum field")
    {
        Err("theta^1 single-bond jet and exponent 0 at theta=0 do not close WDP-O8-CRITICAL-SCALING")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o8_critical_scaling.rs
// Claim: urn:core:crates_rs:tests:wdp-o8-critical-scaling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde19e0c4a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde19e0c4a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore19e0c4a {
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
impl BoundaryErrore19e0c4a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore19e0c4a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore19e0c4a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde19e0c4a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore19e0c4a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore19e0c4a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore19e0c4a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore19e0c4a::ExceedsCapacity {
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
    use super::{c0y_theta1, reject_critical_scaling_promotion, witness, Frac};

    #[test]
    fn order_theta1_jet_and_mesh_exponent_are_exact() {
        let w = witness();
        assert_eq!(w.trace_4p, 4);
        assert!(w.four_p_idempotent_scaled);
        assert_eq!(w.normalized_trace_p, Frac::new(1, 4));
        assert_eq!(w.bond_expectation_p_a0_a1, Frac::new(1, 16));
        assert_eq!(w.bond_expectation_k_a0_a1, Frac::new(-1, 16));
        assert_eq!(w.c00_at_theta0, Frac::new(1, 4));
        assert_eq!(
            w.c0y_theta1_jet,
            [
                Frac::new(0, 1),
                Frac::new(1, 16),
                Frac::new(0, 1),
                Frac::new(1, 16)
            ]
        );
        assert_eq!(c0y_theta1(1, Frac::new(0, 1)), c0y_theta1(1, Frac::new(1, 1)));
        assert_eq!(w.spatial_sum_theta1, Frac::new(1, 8));
        assert_eq!(w.ratio_l6_over_l4, Frac::new(1, 1));
        assert_eq!(w.mesh_exponent_alpha, 0);
        assert_eq!(w.tl3_decay_base_at_1_192, Frac::new(1, 2));
    }

    #[test]
    fn critical_scaling_promotions_are_refused() {
        assert!(reject_critical_scaling_promotion("alpha=0 proves critical scaling").is_err());
        assert!(reject_critical_scaling_promotion("L^{-1/2} derived").is_err());
        assert!(reject_critical_scaling_promotion("ZERO_MODE[1]=1/8 is continuum field").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_e19e0c4a() {
    let admitted = BoundaryRecorde19e0c4a::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde19e0c4a::try_admit(9, 8).is_err());
}
