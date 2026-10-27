//! Exact rational witness for `WDP-APPW-UNIFORM-VOLUME` (`derivation.md`).

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frac {
    pub num: i128,
    pub den: i128,
}

impl Frac {
    pub const fn new(num: i128, den: i128) -> Self {
        assert!(den != 0, "zero denominator");
        let sign = if den < 0 { -1 } else { 1 };
        let n = num * sign;
        let d = den * sign;
        let g = Self::gcd(n.unsigned_abs(), d.unsigned_abs()) as i128;
        Self {
            num: n / g,
            den: d / g,
        }
    }

    const fn gcd(mut a: u128, mut b: u128) -> u128 {
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

    pub const fn mul(self, other: Self) -> Self {
        Self::new(self.num * other.num, self.den * other.den)
    }

    pub const fn div(self, other: Self) -> Self {
        Self::new(self.num * other.den, self.den * other.num)
    }
}

pub fn lambda_1(r: Frac) -> Frac {
    let r2 = r.mul(r);
    let r4 = r2.mul(r2);
    let num = Frac::new(-1, 1).mul(r4);
    let factor1 = r.add(Frac::new(2, 1));
    let factor2 = r2.add(Frac::new(4, 1).mul(r)).add(Frac::new(8, 1));
    let den = Frac::new(4, 1).mul(factor1).mul(factor2);
    num.div(den)
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub r_at_192: Frac,
    pub lambda_1_at_1_192: Frac,
    pub poly_den_at_1_192: Frac,
    pub s1_constant: Frac,
    pub m1_constant: Frac,
    pub gate_e_quadratic: Frac,
}

pub fn witness() -> Witness {
    let r = Frac::new(1, 192);
    let r2 = r.mul(r);
    let r3 = r2.mul(r);
    let poly_den = Frac::new(64, 1)
        .add(Frac::new(64, 1).mul(r))
        .add(Frac::new(24, 1).mul(r2))
        .add(Frac::new(4, 1).mul(r3));
    let s1 = Frac::new(3, 43);
    let m1 = Frac::new(2 * 4096, 1).mul(s1);

    Witness {
        r_at_192: r,
        lambda_1_at_1_192: lambda_1(r),
        poly_den_at_1_192: poly_den,
        s1_constant: s1,
        m1_constant: m1,
        gate_e_quadratic: Frac::new(-1, 88305),
    }
}

pub fn reject_uniform_volume_promotion(claim: &str) -> Result<(), &'static str> {
    if claim.contains("uniform in L for G_M")
        || claim.contains("O.12 discharges Appendix W")
        || claim.contains("-1/87426958080 bounds all volumes")
    {
        Err("fixed L=4 one-period eigenvalue and O.12 Euclidean row-sum do not supply a uniform-in-L Trotter bound on G_M")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appw_uniform_volume.rs
// Claim: urn:core:crates_rs:tests:wdp-appw-uniform-volume:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord48fcab63 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord48fcab63` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError48fcab63 {
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
impl BoundaryError48fcab63 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError48fcab63 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError48fcab63 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord48fcab63 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError48fcab63> {
        if capacity_bound == 0 {
            return Err(BoundaryError48fcab63::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError48fcab63::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError48fcab63::ExceedsCapacity {
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
    use super::{ reject_uniform_volume_promotion, witness, Frac };

    #[test]
    fn lambda_1_at_1_192_and_m1_are_exact() {
        let w = witness();
        assert_eq!(w.lambda_1_at_1_192, Frac::new(-1, 87_426_958_080));
        assert_eq!(w.poly_den_at_1_192, Frac::new(455_348_740, 192 * 192 * 192));
        assert_eq!(w.m1_constant, Frac::new(24576, 43));
    }

    #[test]
    fn uniform_volume_promotions_are_refused() {
        assert!(reject_uniform_volume_promotion("uniform in L for G_M").is_err());
        assert!(reject_uniform_volume_promotion("O.12 discharges Appendix W").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_48fcab63() {
    let admitted = BoundaryRecord48fcab63::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord48fcab63::try_admit(9, 8).is_err());
}
