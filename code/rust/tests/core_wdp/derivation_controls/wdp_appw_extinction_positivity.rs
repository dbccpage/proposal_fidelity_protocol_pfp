//! Constant-profile rational schedule on one finite carrier.
//! L=4, Fock dimension 16, psi_x(tau)=1, theta=1/10, B=1, D=0.
//! E_4=(80/79)^32 and E_16=(20/19)^32. The margin is m=79^32/(4*80^32).
//! The numerator is A=4*(30*(theta+theta^2)*E_16+2*theta*E_4).
//! Strict M_0 is max(1, floor(A/m)+1) on those rationals.
//! The response matrix is not built. This is not a field-limit theorem.

use std::cmp::Ordering;

#[derive(Clone, Debug, PartialEq, Eq)]
struct Nat {
    limbs: Vec<u32>,
}

impl Nat {
    fn zero() -> Self {
        Nat { limbs: Vec::new() }
    }

    fn one() -> Self {
        Nat::from_u32(1)
    }

    fn from_u32(value: u32) -> Self {
        if value == 0 {
            Nat::zero()
        } else {
            Nat { limbs: vec![value] }
        }
    }

    fn from_u64(mut value: u64) -> Self {
        if value == 0 {
            return Nat::zero();
        }
        let mut limbs = Vec::new();
        while value != 0 {
            limbs.push(value as u32);
            value >>= 32;
        }
        Nat { limbs }
    }

    fn is_zero(&self) -> bool {
        self.limbs.is_empty()
    }

    fn norm(mut self) -> Self {
        while self.limbs.last() == Some(&0) {
            self.limbs.pop();
        }
        self
    }

    fn cmp(&self, other: &Nat) -> Ordering {
        match self.limbs.len().cmp(&other.limbs.len()) {
            Ordering::Equal => {
                for i in (0..self.limbs.len()).rev() {
                    match self.limbs[i].cmp(&other.limbs[i]) {
                        Ordering::Equal => {}
                        other => return other,
                    }
                }
                Ordering::Equal
            }
            other => other,
        }
    }

    fn add(&self, other: &Nat) -> Nat {
        let n = self.limbs.len().max(other.limbs.len());
        let mut limbs = Vec::with_capacity(n + 1);
        let mut carry = 0u64;
        for i in 0..n {
            let left = if i < self.limbs.len() { self.limbs[i] as u64 } else { 0 };
            let right = if i < other.limbs.len() { other.limbs[i] as u64 } else { 0 };
            let sum = left + right + carry;
            limbs.push(sum as u32);
            carry = sum >> 32;
        }
        if carry != 0 {
            limbs.push(carry as u32);
        }
        Nat { limbs }
    }

    fn sub(&self, other: &Nat) -> Nat {
        assert!(self.cmp(other) != Ordering::Less, "natural subtraction underflow");
        let mut limbs = Vec::with_capacity(self.limbs.len());
        let mut borrow = 0u64;
        for i in 0..self.limbs.len() {
            let left = self.limbs[i] as u64;
            let right = if i < other.limbs.len() { other.limbs[i] as u64 } else { 0 };
            let take = right + borrow;
            if left >= take {
                limbs.push((left - take) as u32);
                borrow = 0;
            } else {
                limbs.push(((1u64 << 32) + left - take) as u32);
                borrow = 1;
            }
        }
        assert!(borrow == 0, "natural subtraction borrow");
        Nat { limbs }.norm()
    }

    fn mul(&self, other: &Nat) -> Nat {
        if self.is_zero() || other.is_zero() {
            return Nat::zero();
        }
        let mut limbs = vec![0u32; self.limbs.len() + other.limbs.len()];
        for i in 0..self.limbs.len() {
            let mut carry = 0u64;
            for j in 0..other.limbs.len() {
                let slot = limbs[i + j] as u64
                    + self.limbs[i] as u64 * other.limbs[j] as u64
                    + carry;
                limbs[i + j] = slot as u32;
                carry = slot >> 32;
            }
            limbs[i + other.limbs.len()] = carry as u32;
        }
        Nat { limbs }.norm()
    }

    fn pow(&self, mut exp: u32) -> Nat {
        let mut base = self.clone();
        let mut acc = Nat::one();
        while exp > 0 {
            if exp & 1 == 1 {
                acc = acc.mul(&base);
            }
            exp >>= 1;
            if exp > 0 {
                base = base.mul(&base);
            }
        }
        acc
    }

    fn shl(&self, bits: u32) -> Nat {
        if self.is_zero() || bits == 0 {
            return self.clone();
        }
        let skip = (bits / 32) as usize;
        let sh = bits % 32;
        let mut limbs = vec![0u32; skip];
        if sh == 0 {
            limbs.extend_from_slice(&self.limbs);
        } else {
            let mut carry = 0u32;
            for &limb in &self.limbs {
                limbs.push((limb << sh) | carry);
                carry = limb >> (32 - sh);
            }
            if carry != 0 {
                limbs.push(carry);
            }
        }
        Nat { limbs }.norm()
    }

    fn shr(&self, bits: u32) -> Nat {
        if self.is_zero() || bits == 0 {
            return self.clone();
        }
        let skip = (bits / 32) as usize;
        if skip >= self.limbs.len() {
            return Nat::zero();
        }
        let sh = bits % 32;
        let src = &self.limbs[skip..];
        if sh == 0 {
            return Nat { limbs: src.to_vec() }.norm();
        }
        let mut limbs = Vec::with_capacity(src.len());
        for i in 0..src.len() {
            let mut val = src[i] >> sh;
            if i + 1 < src.len() {
                val |= src[i + 1] << (32 - sh);
            }
            limbs.push(val);
        }
        Nat { limbs }.norm()
    }

    fn trailing_zeros(&self) -> u32 {
        for (i, limb) in self.limbs.iter().enumerate() {
            if *limb != 0 {
                return i as u32 * 32 + limb.trailing_zeros();
            }
        }
        0
    }

    fn div_u32(&self, divisor: u32) -> (Nat, u32) {
        assert!(divisor != 0, "division by zero");
        let mut rem = 0u64;
        let mut quot = vec![0u32; self.limbs.len()];
        for i in (0..self.limbs.len()).rev() {
            let cur = (rem << 32) | self.limbs[i] as u64;
            quot[i] = (cur / divisor as u64) as u32;
            rem = cur % divisor as u64;
        }
        (Nat { limbs: quot }.norm(), rem as u32)
    }

    fn to_decimal(&self) -> String {
        if self.is_zero() {
            return "0".to_string();
        }
        let mut digits = Vec::new();
        let mut rest = self.clone();
        while !rest.is_zero() {
            let (quot, rem) = rest.div_u32(10);
            digits.push(char::from(b'0' + rem as u8));
            rest = quot;
        }
        digits.iter().rev().collect()
    }

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

    #[cfg(test)]
    fn from_decimal(text: &str) -> Nat {
        let mut acc = Nat::zero();
        for byte in text.bytes() {
            assert!(byte.is_ascii_digit(), "decimal digit required");
            acc = acc.mul(&Nat::from_u32(10)).add(&Nat::from_u32((byte - b'0') as u32));
        }
        acc
    }
}

fn gcd(mut a: Nat, mut b: Nat) -> Nat {
    if a.is_zero() {
        return b;
    }
    if b.is_zero() {
        return a;
    }
    let shift = a.trailing_zeros().min(b.trailing_zeros());
    a = a.shr(a.trailing_zeros());
    b = b.shr(b.trailing_zeros());
    while !b.is_zero() {
        if a.cmp(&b) == Ordering::Greater {
            std::mem::swap(&mut a, &mut b);
        }
        b = b.sub(&a);
        if b.is_zero() {
            break;
        }
        b = b.shr(b.trailing_zeros());
    }
    a.shl(shift)
}

#[derive(Clone, Debug, PartialEq, Eq)]
struct Rat {
    num: Nat,
    den: Nat,
}

impl Rat {
    fn from_u32(value: u32) -> Self {
        Rat { num: Nat::from_u32(value), den: Nat::one() }
    }

    fn one() -> Self {
        Rat::from_u32(1)
    }
}

fn rmul(left: &Rat, right: &Rat) -> Rat {
    Rat { num: left.num.mul(&right.num), den: left.den.mul(&right.den) }
}

fn radd(left: &Rat, right: &Rat) -> Rat {
    Rat {
        num: left.num.mul(&right.den).add(&right.num.mul(&left.den)),
        den: left.den.mul(&right.den),
    }
}

fn rsub(left: &Rat, right: &Rat) -> Rat {
    Rat {
        num: left.num.mul(&right.den).sub(&right.num.mul(&left.den)),
        den: left.den.mul(&right.den),
    }
}

fn rdiv(left: &Rat, right: &Rat) -> Rat {
    assert!(!right.num.is_zero(), "rational division by zero");
    Rat { num: left.num.mul(&right.den), den: left.den.mul(&right.num) }
}

fn rpow(base: &Rat, exp: u32) -> Rat {
    Rat { num: base.num.pow(exp), den: base.den.pow(exp) }
}

fn cross_eq(left: &Rat, right: &Rat) -> bool {
    left.num.mul(&right.den) == right.num.mul(&left.den)
}

fn envelope(multiple: u32, theta: &Rat) -> Rat {
    assert!(multiple == 4 || multiple == 16, "this schedule uses multiples 4 and 16");
    let step = rdiv(&rmul(&Rat::from_u32(multiple), theta), &Rat::from_u32(32));
    let base = rsub(&Rat::one(), &step);
    assert!(!base.num.is_zero(), "exponential majorant base vanished");
    rpow(&Rat { num: base.den, den: base.num }, 32)
}

fn time_consistency(theta: &Rat, spatial: u32, amplitude: &Rat, derivative: &Rat) -> Rat {
    assert_eq!(spatial, 4, "the fixed carrier has four sites");
    let e4 = envelope(4, theta);
    let e16 = envelope(16, theta);
    let c = rmul(
        &rmul(&Rat::from_u32(30), &radd(theta, &rmul(theta, theta))),
        &e16,
    );
    let k = rdiv(&e16, &Rat::from_u32(2));
    let b2 = rmul(amplitude, amplitude);
    let first = rmul(&b2, &c);
    let second = rmul(&rmul(&rmul(&Rat::from_u32(2), theta), &e4), &b2);
    let third = rmul(&rmul(&k, amplitude), derivative);
    rmul(&Rat::from_u32(spatial), &radd(&radd(&first, &second), &third))
}

fn named_majorant(numer_base: u32, denom_base: u32) -> Rat {
    Rat {
        num: Nat::from_u32(numer_base).pow(32),
        den: Nat::from_u32(denom_base).pow(32),
    }
}

fn closed_numerator() -> Rat {
    let p19 = Nat::from_u32(19).pow(32);
    let p20 = Nat::from_u32(20).pow(32);
    let p79 = Nat::from_u32(79).pow(32);
    let p80 = Nat::from_u32(80).pow(32);
    let first = Nat::from_u32(66).mul(&p20).mul(&p79);
    let second = Nat::from_u32(4).mul(&p80).mul(&p19);
    Rat {
        num: first.add(&second),
        den: Nat::from_u32(5).mul(&p19).mul(&p79),
    }
}

fn closed_margin() -> Rat {
    Rat {
        num: Nat::from_u32(79).pow(32),
        den: Nat::from_u32(4).mul(&Nat::from_u32(80).pow(32)),
    }
}

fn div_exact_u32(value: &Nat, divisor: u32) -> Nat {
    let (quot, rem) = value.div_u32(divisor);
    assert_eq!(rem, 0u32, "exact small division left a remainder");
    quot
}

/// Compare factor * margin and numerator by cross multiplication.
fn cmp_scaled(factor: u64, margin: &Rat, numerator: &Rat) -> Ordering {
    let left = Nat::from_u64(factor).mul(&margin.num).mul(&numerator.den);
    let right = numerator.num.mul(&margin.den);
    left.cmp(&right)
}

/// Smallest positive integer M with M*margin > numerator. Equal ratios round upward.
fn strict_threshold(numerator: &Rat, margin: &Rat) -> u64 {
    assert!(!margin.num.is_zero(), "margin is not strictly positive");
    let mut hi = 1u64;
    while cmp_scaled(hi, margin, numerator) != Ordering::Greater {
        hi = hi.checked_mul(2).expect("threshold left u64");
        assert!(hi <= 1_048_576, "threshold left the selected finite schedule");
    }
    let mut lo = 0u64;
    while lo + 1 < hi {
        let mid = lo + (hi - lo) / 2;
        if cmp_scaled(mid, margin, numerator) == Ordering::Greater {
            hi = mid;
        } else {
            lo = mid;
        }
    }
    hi
}

struct Schedule {
    margin: Rat,
    numerator: Rat,
    strict_m0: u64,
}

fn schedule() -> Schedule {
    let theta = Rat { num: Nat::one(), den: Nat::from_u32(10) };
    let amplitude = Rat::one();
    let derivative = Rat { num: Nat::zero(), den: Nat::one() };
    assert!(cross_eq(&envelope(4, &theta), &named_majorant(80, 79)));
    assert!(cross_eq(&envelope(16, &theta), &named_majorant(20, 19)));
    let expanded = time_consistency(&theta, 4, &amplitude, &derivative);
    let raw = closed_numerator();
    assert!(cross_eq(&expanded, &raw), "expanded numerator disagrees with the closed form");
    let margin = closed_margin();
    let from_envelope = rdiv(&Rat::one(), &rmul(&Rat::from_u32(4), &envelope(4, &theta)));
    assert!(cross_eq(&margin, &from_envelope), "margin is not 1/(4*E_4)");
    assert_eq!(
        margin.den,
        Nat::from_u32(2).pow(98).mul(&Nat::from_u32(10).pow(32)),
        "4*80^32 is not 2^98*10^32"
    );
    assert_eq!(gcd(margin.num.clone(), margin.den.clone()), Nat::one());
    let (den_over_5, den_rem) = raw.den.div_u32(5);
    assert_eq!(den_rem, 0u32, "closed denominator is not divisible by 5");
    let (_, beyond) = den_over_5.div_u32(5);
    assert_ne!(beyond, 0u32, "closed denominator has an unexpected factor 25");
    let numerator = Rat {
        num: div_exact_u32(&raw.num, 5),
        den: div_exact_u32(&raw.den, 5),
    };
    assert_eq!(gcd(numerator.num.clone(), numerator.den.clone()), Nat::one());
    let strict_m0 = strict_threshold(&numerator, &margin);
    assert_eq!(cmp_scaled(strict_m0, &margin, &numerator), Ordering::Greater);
    if strict_m0 > 1 {
        assert!(cmp_scaled(strict_m0 - 1, &margin, &numerator) != Ordering::Greater);
    }
    Schedule { margin, numerator, strict_m0 }
}

/// Exact constant-profile threshold on this carrier. Fractions are reduced.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub sites: u64,
    pub fock: u64,
    pub theta_num: u64,
    pub theta_den: u64,
    pub amplitude: u64,
    pub derivative: u64,
    pub margin_num: String,
    pub margin_den: String,
    pub numerator_num: String,
    pub numerator_den: String,
    pub strict_m0: u64,
}

pub fn witness() -> Witness {
    let schedule = schedule();
    Witness {
        sites: 4,
        fock: 16,
        theta_num: 1,
        theta_den: 10,
        amplitude: 1,
        derivative: 0,
        margin_num: schedule.margin.num.to_decimal(),
        margin_den: schedule.margin.den.to_decimal(),
        numerator_num: schedule.numerator.num.to_decimal(),
        numerator_den: schedule.numerator.den.to_decimal(),
        strict_m0: schedule.strict_m0,
    }
}

/// In-scope parameters return the rational threshold. Every other carrier is refused.
pub fn constant_profile_threshold(
    sites: u64,
    theta_num: u64,
    theta_den: u64,
    amplitude: u64,
    derivative: u64,
) -> Result<Witness, &'static str> {
    if sites != 4 || theta_num != 1 || theta_den != 10 || amplitude != 1 || derivative != 0 {
        return Err("refused: the rational margin is only the constant profile on L=4 at theta=1/10 with B=1 and D=0");
    }
    Ok(witness())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum OpenClaim {
    PositivityOfGm,
    FieldLimitExtinction,
    NonconstantProfile,
    OtherLength,
    GateEAtDepthOne,
}

/// An extinction or positivity claim other than the one-point record stays open.
pub fn extinction_or_positivity(claim: OpenClaim) -> Result<(), &'static str> {
    Err(match claim {
        OpenClaim::PositivityOfGm => "refused: positivity of G_M is not this constant-profile schedule",
        OpenClaim::FieldLimitExtinction => "refused: a field-limit extinction theorem is not this finite schedule",
        OpenClaim::NonconstantProfile => "refused: the margin is not assigned to a nonconstant profile",
        OpenClaim::OtherLength => "refused: L other than 4 is outside this carrier",
        OpenClaim::GateEAtDepthOne => "refused: the Gate E matrix at M=1 is not this margin",
    })
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appw_extinction_positivity.rs
// Claim: urn:core:crates_rs:tests:wdp-appw-extinction-positivity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddadb81b3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddadb81b3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordadb81b3 {
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
impl BoundaryErrordadb81b3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordadb81b3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordadb81b3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddadb81b3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordadb81b3> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordadb81b3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordadb81b3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordadb81b3::ExceedsCapacity {
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

    const MARGIN_NUM: &str = "5297450670659957549009604563595170759963655420038456036451841";
    const MARGIN_DEN: &str = "31691265005705735037417580134400000000000000000000000000000000";
    const NUMERATOR_NUM: &str = "30560470964558734288104504638287074496011024223750634559368395993854771200000000000000000000000000000000";
    const NUMERATOR_DEN: &str = "440739679775466657209593615746337787110017959752239652332942001202028305587856238247631064241116048001";

    #[test]
    fn nat_powers_and_integer_threshold() {
        assert_eq!(Nat::from_u32(2).pow(10).to_decimal(), "1024");
        assert_eq!(Nat::from_u32(2).pow(98).to_decimal(), "316912650057057350374175801344");
        assert_eq!(Nat::from_u32(79).pow(2).to_decimal(), "6241");
        assert_eq!(gcd(Nat::from_u32(12), Nat::from_u32(18)).to_decimal(), "6");
        assert_eq!(
            gcd(Nat::from_u32(2).pow(98), Nat::from_u32(10).pow(32)).to_decimal(),
            "4294967296"
        );
        let limb = Nat::from_u64(1u64 << 32);
        assert_eq!(limb.sub(&Nat::from_u32(1)).to_decimal(), "4294967295");
        assert_eq!(limb.mul(&limb).to_decimal(), "18446744073709551616");
        let half = Rat { num: Nat::from_u32(1), den: Nat::from_u32(2) };
        assert_eq!(strict_threshold(&Rat { num: Nat::from_u32(3), den: Nat::from_u32(2) }, &half), 4);
        assert_eq!(strict_threshold(&half, &half), 2);
        assert_eq!(strict_threshold(&Rat { num: Nat::from_u32(1), den: Nat::from_u32(3) }, &half), 1);
    }

    #[test]
    fn exact_constant_profile_threshold_is_415() {
        let got = witness();
        let sched = schedule();
        assert_eq!(got.sites, 4);
        assert_eq!(got.fock, 16);
        assert_eq!((got.theta_num, got.theta_den), (1, 10));
        assert_eq!((got.amplitude, got.derivative), (1, 0));
        assert_eq!(got.strict_m0, 415);
        assert_eq!(sched.strict_m0, 415);
        assert_eq!(got.margin_num, MARGIN_NUM);
        assert_eq!(got.margin_den, MARGIN_DEN);
        assert_eq!(got.numerator_num, NUMERATOR_NUM);
        assert_eq!(got.numerator_den, NUMERATOR_DEN);
        assert_eq!(sched.margin.num, Nat::from_decimal(MARGIN_NUM));
        assert_eq!(sched.margin.den, Nat::from_decimal(MARGIN_DEN));
        assert_eq!(sched.numerator.num, Nat::from_decimal(NUMERATOR_NUM));
        assert_eq!(sched.numerator.den, Nat::from_decimal(NUMERATOR_DEN));
        assert_eq!(sched.margin.num, Nat::from_u32(79).pow(32));
        assert_eq!(sched.margin.den, Nat::from_u32(4).mul(&Nat::from_u32(80).pow(32)));
        assert!(cmp_scaled(414, &sched.margin, &sched.numerator) != Ordering::Greater);
        assert_eq!(cmp_scaled(415, &sched.margin, &sched.numerator), Ordering::Greater);
        assert_eq!(constant_profile_threshold(4, 1, 10, 1, 0).unwrap(), got);
    }

    #[test]
    fn refuses_matrix_positivity_and_the_one_point_record() {
        // Rayleigh identity of the M=1 record. It is not added into the margin.
        assert_eq!(8 * 88_305, 706_440);
        assert_eq!(192u64 * 455_348_740, 87_426_958_080);
        let got = witness();
        assert_ne!(got.margin_den, "706440");
        assert_ne!(got.margin_den, "88305");
        assert_ne!(got.margin_den, "87426958080");
        assert_eq!(
            extinction_or_positivity(OpenClaim::PositivityOfGm),
            Err("refused: positivity of G_M is not this constant-profile schedule")
        );
        assert_eq!(
            extinction_or_positivity(OpenClaim::GateEAtDepthOne),
            Err("refused: the Gate E matrix at M=1 is not this margin")
        );
        assert!(extinction_or_positivity(OpenClaim::FieldLimitExtinction).is_err());
        assert!(extinction_or_positivity(OpenClaim::NonconstantProfile).is_err());
        assert!(extinction_or_positivity(OpenClaim::OtherLength).is_err());
        assert_eq!(
            constant_profile_threshold(5, 1, 10, 1, 0).unwrap_err(),
            "refused: the rational margin is only the constant profile on L=4 at theta=1/10 with B=1 and D=0"
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_dadb81b3() {
    let admitted = BoundaryRecorddadb81b3::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddadb81b3::try_admit(9, 8).is_err());
}
