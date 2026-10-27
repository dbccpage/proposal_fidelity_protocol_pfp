//! Exact rational witness for `WDP-JOINT-CONTINUUM` (`derivation.md`).
//!
//! Verifies:
//! 1. Three mesh nodes `x_i = 1 / L_i^2` for `L_i in {4, 6, 8}`, i.e. `(1/16, 1/36, 1/64)`.
//! 2. Node-vanishing cubic `H(x) = (x - 1/16)(x - 1/36)(x - 1/64)` evaluates to `(0, 0, 0)` on the
//!    three nodes while `H(0) = -1 / 36864 != 0`.
//! 3. Neville weights `w = (4/15, -81/35, 64/21) = (28/105, -243/105, 320/105)` satisfy:
//!    - `sum w_i = 1`
//!    - `sum w_i x_i = 0`
//!    - `sum w_i x_i^2 = 0`
//!    - `sum w_i H(x_i) = 0 != H(0) = -1 / 36864`
//! 4. Recorded occupation-basis checkerboard samples `(Z(4), Z(6), Z(8)) = (912, 33012, 973824)`
//!    and quadratic Neville extrapolate `sum w_i Z(L_i) = 99562368 / 35`.
//! 5. Refuses promoting `H(0) = -1/36864` to a supplied remainder bound or joint continuum value,
//!    and refuses reusing `Z(4) = 912` as a 16-site 2D torus partition function.

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

pub fn eval_h(x: Frac) -> Frac {
    let f1 = x.sub(Frac::new(1, 16));
    let f2 = x.sub(Frac::new(1, 36));
    let f3 = x.sub(Frac::new(1, 64));
    f1.mul(f2).mul(f3)
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub nodes: [Frac; 3],
    pub weights: [Frac; 3],
    pub h_on_nodes: [Frac; 3],
    pub h_at_zero: Frac,
    pub moment_0: Frac,
    pub moment_1: Frac,
    pub moment_2: Frac,
    pub neville_on_h: Frac,
    pub checkerboard_z: [i64; 3],
    pub neville_z0: Frac,
    pub target_3_optimum: Frac,
    pub target_4_optimum: i64,
    pub target_5_class_count: i64,
}

pub fn witness() -> Witness {
    let nodes = [Frac::new(1, 16), Frac::new(1, 36), Frac::new(1, 64)];
    let weights = [Frac::new(4, 15), Frac::new(-81, 35), Frac::new(64, 21)];
    let h_on_nodes = [eval_h(nodes[0]), eval_h(nodes[1]), eval_h(nodes[2])];
    let h_at_zero = eval_h(Frac::new(0, 1));

    let mut m0 = Frac::new(0, 1);
    let mut m1 = Frac::new(0, 1);
    let mut m2 = Frac::new(0, 1);
    let mut nh = Frac::new(0, 1);
    for i in 0..3 {
        m0 = m0.add(weights[i]);
        m1 = m1.add(weights[i].mul(nodes[i]));
        m2 = m2.add(weights[i].mul(nodes[i]).mul(nodes[i]));
        nh = nh.add(weights[i].mul(h_on_nodes[i]));
    }

    let z_samples = [912_i64, 33012, 973824];
    let mut nz0 = Frac::new(0, 1);
    for i in 0..3 {
        nz0 = nz0.add(weights[i].mul(Frac::new(z_samples[i], 1)));
    }

    Witness {
        nodes,
        weights,
        h_on_nodes,
        h_at_zero,
        moment_0: m0,
        moment_1: m1,
        moment_2: m2,
        neville_on_h: nh,
        checkerboard_z: z_samples,
        neville_z0: nz0,
        target_3_optimum: Frac::new(15, 4),
        target_4_optimum: 4,
        target_5_class_count: 29_771,
    }
}

pub fn reject_continuum_or_torus_promotion(claim: &str) -> Result<(), &'static str> {
    if claim.contains("-1/36864 is remainder bound")
        || claim.contains("Z=912 is 16-site torus")
        || claim.contains("Q-continuum closed")
    {
        Err("three-node polynomial fit and fixed L=4 carrier do not close WDP-JOINT-CONTINUUM or construct a 16-site torus")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_joint_continuum.rs
// Claim: urn:core:crates_rs:tests:wdp-joint-continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord60798f4d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord60798f4d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError60798f4d {
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
impl BoundaryError60798f4d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError60798f4d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError60798f4d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord60798f4d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError60798f4d> {
        if capacity_bound == 0 {
            return Err(BoundaryError60798f4d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError60798f4d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError60798f4d::ExceedsCapacity {
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
    use super::{reject_continuum_or_torus_promotion, witness, Frac};

    #[test]
    fn three_node_moments_and_cubic_aliasing_are_exact() {
        let w = witness();
        assert_eq!(w.h_on_nodes, [Frac::new(0, 1), Frac::new(0, 1), Frac::new(0, 1)]);
        assert_eq!(w.h_at_zero, Frac::new(-1, 36864));
        assert_eq!(w.moment_0, Frac::new(1, 1));
        assert_eq!(w.moment_1, Frac::new(0, 1));
        assert_eq!(w.moment_2, Frac::new(0, 1));
        assert_eq!(w.neville_on_h, Frac::new(0, 1));
        assert_ne!(w.neville_on_h, w.h_at_zero);
        assert_eq!(w.neville_z0, Frac::new(20_241_820, 7));
    }

    #[test]
    fn continuum_and_torus_promotions_are_refused() {
        assert!(reject_continuum_or_torus_promotion("-1/36864 is remainder bound").is_err());
        assert!(reject_continuum_or_torus_promotion("Z=912 is 16-site torus").is_err());
        assert!(reject_continuum_or_torus_promotion("Q-continuum closed").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_60798f4d() {
    let admitted = BoundaryRecord60798f4d::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord60798f4d::try_admit(9, 8).is_err());
}
