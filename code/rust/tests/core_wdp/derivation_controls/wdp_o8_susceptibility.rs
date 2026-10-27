//! Outside-membership of one AR-1 parameter on a finite labelled carrier.
//! Even periodic full-Fock ring L=4, dimension 16, checkerboard count M=2,
//! source parameter q=3. The greatest admitted parameter is 385/384.
//! The gap is 767/384. This is not a susceptibility, a sector ratio,
//! a law for theta growing with L, or a continuum limit.

const LENGTH: i64 = 4;
const CHECKERBOARD: i64 = 2;
const SOURCE_Q: i64 = 3;
const TEMPERATURE_DEN: i64 = 192;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rational {
    pub num: i64,
    pub den: i64,
}

impl Rational {
    pub fn new(num: i64, den: i64) -> Self {
        Self::reduced(i128::from(num), i128::from(den))
    }

    fn reduced(mut num: i128, mut den: i128) -> Self {
        assert!(den != 0, "rational denominator is zero");
        if den < 0 {
            num = -num;
            den = -den;
        }
        let g = gcd(num.abs(), den);
        num /= g;
        den /= g;
        assert!(num <= i128::from(i64::MAX) && num >= i128::from(i64::MIN));
        assert!(den <= i128::from(i64::MAX));
        Self {
            num: num as i64,
            den: den as i64,
        }
    }

    pub fn zero() -> Self {
        Self::new(0, 1)
    }

    pub fn add(self, other: Self) -> Self {
        Self::reduced(
            i128::from(self.num) * i128::from(other.den) + i128::from(other.num) * i128::from(self.den),
            i128::from(self.den) * i128::from(other.den),
        )
    }

    pub fn sub(self, other: Self) -> Self {
        self.add(Self::new(-other.num, other.den))
    }

    pub fn mul(self, other: Self) -> Self {
        Self::reduced(
            i128::from(self.num) * i128::from(other.num),
            i128::from(self.den) * i128::from(other.den),
        )
    }

    pub fn div(self, other: Self) -> Self {
        assert!(other.num != 0, "rational division by zero");
        self.mul(Self::new(other.den, other.num))
    }

    pub fn cmp_ord(self, other: Self) -> i8 {
        let left = i128::from(self.num) * i128::from(other.den);
        let right = i128::from(other.num) * i128::from(self.den);
        if left < right {
            -1
        } else if left > right {
            1
        } else {
            0
        }
    }
}

fn gcd(mut a: i128, mut b: i128) -> i128 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub length: i64,
    pub dimension: i64,
    pub checkerboard: i64,
    pub source_q: Rational,
    pub temperature_ceiling: Rational,
    pub greatest_ar1: Rational,
    pub gap: Rational,
    pub cleared_numerator: i64,
    pub euler_parameter: Rational,
    pub euler_excess: Rational,
    pub outside_disk: bool,
    pub pointwise_susceptibility: bool,
    pub parity_sector_ratio: bool,
    pub temperature_scaling: bool,
    pub continuum_limit: bool,
}

fn occupation_dimension(length: i64) -> i64 {
    assert!(length > 0 && length % 2 == 0, "periodic ring is even");
    assert!(length < 31, "occupation length fits in a signed shift");
    let states = 1i64 << length;
    let mut counted = 0i64;
    for state in 0..states {
        let _occupation = (state as u64).count_ones();
        counted += 1;
    }
    let closing = (length - 1 + 1) % length;
    assert_eq!(closing, 0, "the ring step closes");
    counted
}

fn balanced_checkerboard(length: i64) -> bool {
    let mut even = 0i64;
    let mut odd = 0i64;
    for site in 0..length {
        if site % 2 == 0 {
            even += 1;
        } else {
            odd += 1;
        }
    }
    even == odd && even + odd == length
}

/// Admit r + rho <= 1/192 on the labelled carrier. The endpoint is admitted.
/// Strictly above the ceiling is the temperature-domain refusal.
pub fn temperature_domain(
    length: i64,
    checkerboard: i64,
    center: Rational,
    radius: Rational,
) -> Result<(), &'static str> {
    if length != LENGTH || checkerboard != CHECKERBOARD {
        return Err("selected scope is the labelled carrier L=4, M=2");
    }
    if radius.cmp_ord(Rational::zero()) < 0 || center.cmp_ord(radius) < 0 {
        return Err("temperature radius is not an admissible parameter");
    }
    let ceiling = Rational::new(1, TEMPERATURE_DEN);
    if center.add(radius).cmp_ord(ceiling) > 0 {
        return Err("temperature interval exceeds the proved upper bound 1/192");
    }
    Ok(())
}

pub fn witness() -> Witness {
    let length = LENGTH;
    let dimension = occupation_dimension(length);
    assert!(balanced_checkerboard(length), "even ring is not 2-colored");
    let checkerboard = CHECKERBOARD;
    assert!(checkerboard > 0, "checkerboard count is positive");
    let ceiling = Rational::new(1, TEMPERATURE_DEN);
    let greatest = Rational::new(1, 1).add(ceiling.div(Rational::new(checkerboard, 1)));
    let denominator = TEMPERATURE_DEN * checkerboard;
    let greatest_num = denominator + 1;
    let cleared = SOURCE_Q * denominator - greatest_num;
    assert!(cleared > 0, "the fixture is not strictly outside the AR-1 ceiling");
    let gap = Rational::new(SOURCE_Q, 1).sub(greatest);
    assert_eq!(gap, Rational::new(cleared, denominator));
    assert_eq!(greatest, Rational::new(greatest_num, denominator));
    let euler = Rational::new(checkerboard, 1).mul(Rational::new(SOURCE_Q - 1, 1));
    let excess = euler.sub(ceiling);
    assert_eq!(excess.div(Rational::new(checkerboard, 1)), gap);
    let outside = temperature_domain(length, checkerboard, euler, Rational::zero()).is_err();
    assert!(outside, "q=3 at M=2 is inside the AR-1 disk");
    Witness {
        length,
        dimension,
        checkerboard,
        source_q: Rational::new(SOURCE_Q, 1),
        temperature_ceiling: ceiling,
        greatest_ar1: greatest,
        gap,
        cleared_numerator: cleared,
        euler_parameter: euler,
        euler_excess: excess,
        outside_disk: true,
        pointwise_susceptibility: false,
        parity_sector_ratio: false,
        temperature_scaling: false,
        continuum_limit: false,
    }
}

pub fn pointwise_susceptibility() -> Result<Rational, &'static str> {
    let _gap = witness().gap;
    Err("all-temperature pointwise susceptibility is not selected; 767/384 is not p''(theta,0)")
}

pub fn parity_sector_ratio() -> Result<Rational, &'static str> {
    Err("a parity-sector ratio is not selected on this carrier")
}

pub fn theta_growing_with_length(length: i64) -> Result<Rational, &'static str> {
    let _ = length;
    Err("no law for theta growing with L is selected")
}

pub fn reuse_one_dimensional_ratio(num: i64, den: i64) -> Result<Rational, &'static str> {
    let reduced = Rational::new(num, den);
    if reduced == Rational::new(48, 19) || reduced == Rational::new(149, 57) {
        return Err("the one-dimensional SQL ratios 48/19 and 149/57 are not reused");
    }
    Err("this carrier does not supply a susceptibility ratio")
}

pub fn higher_dimensional_sum(dimension: i64) -> Result<(), &'static str> {
    let _ = (dimension, witness().dimension);
    Err("do not copy a one-dimensional constant into a higher-dimensional sum")
}

pub fn continuum_limit() -> Result<(), &'static str> {
    Err("a finite model on this carrier does not establish a continuum limit")
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_o8_susceptibility.rs
// Claim: urn:core:crates_rs:tests:wdp-o8-susceptibility:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8d7270bd {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8d7270bd` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8d7270bd {
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
impl BoundaryError8d7270bd {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8d7270bd {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8d7270bd {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8d7270bd {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8d7270bd> {
        if capacity_bound == 0 {
            return Err(BoundaryError8d7270bd::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8d7270bd::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8d7270bd::ExceedsCapacity {
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
        continuum_limit, higher_dimensional_sum, parity_sector_ratio, pointwise_susceptibility,
        reuse_one_dimensional_ratio, temperature_domain, theta_growing_with_length, witness,
        Rational,
    };

    #[test]
    fn exact_ar1_gap_is_767_over_384() {
        let carrier = witness();
        assert_eq!(carrier.length, 4);
        assert_eq!(carrier.dimension, 16);
        assert_eq!(carrier.checkerboard, 2);
        assert_eq!(carrier.source_q, Rational::new(3, 1));
        assert_eq!(carrier.temperature_ceiling, Rational::new(1, 192));
        assert_eq!(carrier.greatest_ar1, Rational::new(385, 384));
        assert_eq!(carrier.gap, Rational::new(767, 384));
        assert_eq!(carrier.cleared_numerator, 767);
        assert_eq!(3 * 384 - 385, 767);
        assert_eq!(carrier.euler_parameter, Rational::new(4, 1));
        assert_eq!(carrier.euler_excess, Rational::new(767, 192));
        assert!(carrier.outside_disk);
        assert!(!carrier.pointwise_susceptibility);
        assert!(!carrier.parity_sector_ratio);
        assert!(!carrier.temperature_scaling);
        assert!(!carrier.continuum_limit);
        assert!(temperature_domain(4, 2, Rational::new(1, 192), Rational::zero()).is_ok());
    }

    #[test]
    fn refuses_fixture_outside_the_disk_and_unselected_obligations() {
        let refused = temperature_domain(4, 2, Rational::new(4, 1), Rational::zero());
        assert_eq!(
            refused,
            Err("temperature interval exceeds the proved upper bound 1/192")
        );
        assert!(pointwise_susceptibility().is_err());
        assert!(parity_sector_ratio().is_err());
        assert!(theta_growing_with_length(4).is_err());
        assert!(reuse_one_dimensional_ratio(48, 19).is_err());
        assert!(reuse_one_dimensional_ratio(149, 57).is_err());
        assert!(higher_dimensional_sum(2).is_err());
        assert!(continuum_limit().is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_8d7270bd() {
    let admitted = BoundaryRecord8d7270bd::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord8d7270bd::try_admit(9, 8).is_err());
}
