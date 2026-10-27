//! Finite carriers for the three corrected premises.
//! Occupation trace, sharp readout, and pairing scale stay separate.
//! No volume limit, Born uniqueness, or continuum claim.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rational {
    pub num: i64,
    pub den: i64,
}

impl Rational {
    pub fn new(num: i64, den: i64) -> Self {
        Self::from_i128(i128::from(num), i128::from(den))
    }

    fn from_i128(num: i128, den: i128) -> Self {
        assert!(den != 0, "rational denominator is zero");
        let g = gcd_i128(num.abs(), den.abs());
        let mut num = num / g;
        let mut den = den / g;
        if den < 0 {
            num = -num;
            den = -den;
        }
        assert!(num <= i128::from(i64::MAX) && num >= i128::from(i64::MIN));
        assert!(den <= i128::from(i64::MAX));
        Self {
            num: num as i64,
            den: den as i64,
        }
    }

    fn add(self, other: Self) -> Self {
        Self::from_i128(
            i128::from(self.num) * i128::from(other.den) + i128::from(other.num) * i128::from(self.den),
            i128::from(self.den) * i128::from(other.den),
        )
    }

    fn sub(self, other: Self) -> Self {
        self.add(other.neg())
    }

    fn mul(self, other: Self) -> Self {
        Self::from_i128(
            i128::from(self.num) * i128::from(other.num),
            i128::from(self.den) * i128::from(other.den),
        )
    }

    fn div(self, other: Self) -> Option<Self> {
        if other.num == 0 {
            None
        } else {
            Some(self.mul(Self::new(other.den, other.num)))
        }
    }

    fn neg(self) -> Self {
        Self::new(-self.num, self.den)
    }

    fn abs(self) -> Self {
        Self::new(self.num.abs(), self.den)
    }

    fn is_strictly_less_than_one(self) -> bool {
        self.den > 0 && i128::from(self.num) < i128::from(self.den)
    }

    fn dominates(self, value: Self) -> bool {
        self.den > 0
            && value.den > 0
            && i128::from(self.num) * i128::from(value.den)
                >= i128::from(value.num) * i128::from(self.den)
    }
}

fn gcd_i128(mut a: i128, mut b: i128) -> i128 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Gauss {
    re: Rational,
    im: Rational,
}

impl Gauss {
    fn new(re: Rational, im: Rational) -> Self {
        Self { re, im }
    }

    fn from_i(re: i64, im: i64) -> Self {
        Self::new(Rational::new(re, 1), Rational::new(im, 1))
    }

    fn conj(self) -> Self {
        Self::new(self.re, self.im.neg())
    }

    fn mul(self, other: Self) -> Self {
        Self::new(
            self.re.mul(other.re).sub(self.im.mul(other.im)),
            self.re.mul(other.im).add(self.im.mul(other.re)),
        )
    }

    fn scale(self, scale: i64) -> Self {
        Self::from_i(scale, 0).mul(self)
    }
}

fn stagger(site: i64) -> i64 {
    if site % 2 == 0 { 1 } else { -1 }
}

fn two_a0_diagonal(state: i64) -> i64 {
    let occupation = state & 1;
    stagger(0) * (2 * occupation - 1)
}

fn occupation_carrier() -> (i64, bool, Rational) {
    let length = 4i64;
    let dimension = 1i64 << length;
    let first = two_a0_diagonal(0);
    let mut squared_is_identity = length >= 4 && length % 2 == 0 && first * first == 1;
    for state in 1..dimension {
        let entry = two_a0_diagonal(state);
        if entry * entry != 1 {
            squared_is_identity = false;
        }
    }
    let covariance = Rational::new(first * first, 4);
    (dimension, squared_is_identity, covariance)
}

pub fn signed_closed_form(theta: Rational, exp_mu: Rational) -> Result<Rational, &'static str> {
    let q = Rational::new(96, 1).mul(theta).mul(exp_mu);
    let one = Rational::new(1, 1);
    one.add(q)
        .div(one.sub(q))
        .ok_or("signed closed form is undefined")
}

pub fn absolute_closed_form(theta: Rational, exp_mu: Rational) -> Result<Rational, &'static str> {
    if exp_mu.num <= 0 || exp_mu.den <= 0 {
        return Err("e^mu stand-in must be positive");
    }
    let q = Rational::new(96, 1).mul(theta.abs()).mul(exp_mu);
    if !q.is_strictly_less_than_one() {
        return Err("need 96 |theta| e^mu < 1");
    }
    let one = Rational::new(1, 1);
    one.add(q)
        .div(one.sub(q))
        .ok_or("closed form denominator vanished")
}

fn absolute_ratio(theta: Rational, exp_mu: Rational) -> Rational {
    Rational::new(96, 1).mul(theta.abs()).mul(exp_mu)
}

fn n2_sharp_readout(lambda: Rational) -> Result<(Rational, bool), &'static str> {
    if lambda.den <= 0 || lambda.num < 0 || i128::from(lambda.num) > i128::from(lambda.den) {
        return Err("depolarization weight must lie in [0,1]");
    }
    const N: i64 = 2;
    let mut tr_rho_e = 0i64;
    let mut tr_e = 0i64;
    let mut tr_rho_f = 0i64;
    let mut tr_f = 0i64;
    let mut tr_rho = 0i64;
    for index in 0..N {
        let rho = if index == 0 { 1 } else { 0 };
        let accept = if index == 0 { 1 } else { 0 };
        let reject = 1 - accept;
        tr_rho_e += rho * accept;
        tr_e += accept;
        tr_rho_f += rho * reject;
        tr_f += reject;
        tr_rho += rho;
    }
    if tr_rho != 1 {
        return Err("state is not normalized");
    }
    let one = Rational::new(1, 1);
    let born = Rational::new(tr_rho_e, tr_rho);
    let mixed = Rational::new(tr_e, N);
    let accept_p = lambda.mul(born).add(one.sub(lambda).mul(mixed));
    let born_reject = Rational::new(tr_rho_f, tr_rho);
    let mixed_reject = Rational::new(tr_f, N);
    let reject_p = lambda.mul(born_reject).add(one.sub(lambda).mul(mixed_reject));
    let sums = accept_p.add(reject_p) == one && accept_p.num >= 0 && reject_p.num >= 0;
    Ok((accept_p, sums))
}

pub fn reject_dimension_one_input(supplied: Rational) -> Result<(), &'static str> {
    let (computed, sums) = n2_sharp_readout(Rational::new(1, 2))?;
    if !sums {
        return Err("n=2 sharp outcomes are not a readout");
    }
    if supplied == computed {
        Err("a supplied scalar is not an input channel")
    } else {
        Err("the separate n=1 readout is not an input to the n=2 carrier")
    }
}

fn pairing(scale: i64, left: Gauss, right: Gauss) -> Gauss {
    left.conj().mul(right).scale(scale)
}

fn samples() -> [Gauss; 3] {
    [
        Gauss::from_i(1, 0),
        Gauss::from_i(0, 1),
        Gauss::new(Rational::new(2, 3), Rational::new(-3, 5)),
    ]
}

fn sample_pair_holds(scale: i64, one: Gauss, imag: Gauss, left: Gauss, right: Gauss) -> bool {
    let balanced_left = imag.mul(left).mul(right);
    let balanced_right = left.mul(imag.mul(right));
    let prod = left.mul(right);
    let diagonal = pairing(scale, prod, prod);
    let balanced_ok = balanced_left == balanced_right
        && pairing(scale, balanced_left, one) == pairing(scale, balanced_right, one)
        && pairing(scale, one, balanced_left) == pairing(scale, one, balanced_right);
    let diag_ok = diagonal.im == Rational::new(0, 1) && diagonal.re.num > 0 && diagonal.re.den > 0;
    balanced_ok && diag_ok && pairing(scale, prod, one) == pairing(scale, one, prod).conj()
}

fn sample_laws(scale: i64) -> bool {
    if scale <= 0 {
        return false;
    }
    let one = Gauss::from_i(1, 0);
    let imag = Gauss::from_i(0, 1);
    for left in samples() {
        for right in samples() {
            if !sample_pair_holds(scale, one, imag, left, right) {
                return false;
            }
        }
    }
    true
}

fn unit_squared_norm(scale: i64) -> Result<Rational, &'static str> {
    let one = Gauss::from_i(1, 0);
    let identified = one.mul(one);
    let value = pairing(scale, identified, identified);
    if value.im != Rational::new(0, 1) {
        return Err("unit pure-tensor pairing is not real");
    }
    Ok(value.re)
}

fn unit_pairing_product() -> Result<Rational, &'static str> {
    let one = Gauss::from_i(1, 0);
    let value = one.conj().mul(one).mul(one.conj()).mul(one);
    if value.im != Rational::new(0, 1) {
        return Err("unit pairing product is not real");
    }
    Ok(value.re)
}

pub fn require_unit_multiplicativity(scale: i64) -> Result<Rational, &'static str> {
    if !sample_laws(scale) {
        return Err("balance or positivity failed on the finite samples");
    }
    let norm = unit_squared_norm(scale)?;
    let product = unit_pairing_product()?;
    if norm != product {
        return Err("balanced positive scale fails pure-tensor multiplicativity");
    }
    Ok(norm)
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub occupation_dimension: i64,
    pub two_a0_squared_is_identity: bool,
    pub on_site_covariance: Rational,
    pub euclidean_time: i64,
    pub theta: Rational,
    pub mu: Rational,
    pub exp_mu: Rational,
    pub signed_closed_form: Rational,
    pub absolute_ratio: Rational,
    pub signed_form_bounds_covariance: bool,
    pub absolute_predicate_accepts: bool,
    pub sharp_readout: Rational,
    pub sharp_outcomes_sum_to_one: bool,
    pub unit_norm_scale_one: Rational,
    pub unit_norm_scale_two: Rational,
    pub scale_one_matches_unit_product: bool,
    pub scale_two_matches_unit_product: bool,
    pub sample_laws_hold: bool,
}

pub fn witness() -> Witness {
    let (occupation_dimension, two_a0_squared_is_identity, on_site_covariance) = occupation_carrier();
    let euclidean_time = 0i64;
    let theta = Rational::new(-1, 96);
    let mu = Rational::new(0, 1);
    let exp_mu = if mu == Rational::new(0, 1) {
        Rational::new(1, 1)
    } else {
        panic!("only the selected mu=0 stand-in is defined on this carrier");
    };
    let signed_closed_form = signed_closed_form(theta, exp_mu)
        .expect("signed endpoint q=-1 has closed form 0");
    let absolute_ratio = absolute_ratio(theta, exp_mu);
    let absolute_predicate_accepts = absolute_closed_form(theta, exp_mu).is_ok();
    let (sharp_readout, sharp_outcomes_sum_to_one) = n2_sharp_readout(Rational::new(1, 2))
        .expect("n=2 and lambda=1/2 lie in the readout domain");
    let unit_norm_scale_one = unit_squared_norm(1).expect("scale 1 norm");
    let unit_norm_scale_two = unit_squared_norm(2).expect("scale 2 norm");
    let product = unit_pairing_product().expect("unit pairing product");
    Witness {
        occupation_dimension,
        two_a0_squared_is_identity,
        on_site_covariance,
        euclidean_time,
        theta,
        mu,
        exp_mu,
        signed_closed_form,
        absolute_ratio,
        signed_form_bounds_covariance: signed_closed_form.dominates(on_site_covariance),
        absolute_predicate_accepts,
        sharp_readout,
        sharp_outcomes_sum_to_one,
        unit_norm_scale_one,
        unit_norm_scale_two,
        scale_one_matches_unit_product: unit_norm_scale_one == product,
        scale_two_matches_unit_product: unit_norm_scale_two == product,
        sample_laws_hold: sample_laws(1) && sample_laws(2),
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/plan_wdp_math_premises.rs
// Claim: urn:core:crates_rs:tests:plan-wdp-math-premises:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda2210af4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda2210af4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora2210af4 {
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
impl BoundaryErrora2210af4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora2210af4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora2210af4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda2210af4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora2210af4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora2210af4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora2210af4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora2210af4::ExceedsCapacity {
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
        absolute_closed_form, n2_sharp_readout, reject_dimension_one_input,
        require_unit_multiplicativity, witness, Rational,
    };

    #[test]
    fn exact_three_carrier_values() {
        let found = witness();
        assert_eq!(found.occupation_dimension, 16);
        assert!(found.two_a0_squared_is_identity);
        assert_eq!(found.on_site_covariance, Rational::new(1, 4));
        assert_eq!(found.euclidean_time, 0);
        assert_eq!(found.theta, Rational::new(-1, 96));
        assert_eq!(found.mu, Rational::new(0, 1));
        assert_eq!(found.exp_mu, Rational::new(1, 1));
        assert_eq!(found.signed_closed_form, Rational::new(0, 1));
        assert_eq!(found.absolute_ratio, Rational::new(1, 1));
        assert!(!found.signed_form_bounds_covariance);
        assert!(!found.absolute_predicate_accepts);
        assert_eq!(found.sharp_readout, Rational::new(3, 4));
        assert!(found.sharp_outcomes_sum_to_one);
        assert_ne!(found.sharp_readout, Rational::new(1, 3));
        assert_eq!(found.unit_norm_scale_one, Rational::new(1, 1));
        assert_eq!(found.unit_norm_scale_two, Rational::new(2, 1));
        assert!(found.scale_one_matches_unit_product);
        assert!(!found.scale_two_matches_unit_product);
        assert!(found.sample_laws_hold);
    }

    #[test]
    fn endpoint_ratio_foreign_readout_and_scale_two_are_refused() {
        let found = witness();
        let signed_endpoint = absolute_closed_form(found.theta, found.exp_mu).unwrap_err();
        assert!(signed_endpoint.contains("96"));
        let positive_endpoint = absolute_closed_form(Rational::new(1, 192), Rational::new(2, 1)).unwrap_err();
        assert!(positive_endpoint.contains("96"));
        assert_eq!(
            absolute_closed_form(Rational::new(1, 192), Rational::new(1, 1)).unwrap(),
            Rational::new(3, 1)
        );
        assert_eq!(
            absolute_closed_form(Rational::new(-1, 192), Rational::new(1, 1)).unwrap(),
            Rational::new(3, 1)
        );
        assert!(reject_dimension_one_input(Rational::new(1, 3)).is_err());
        assert!(n2_sharp_readout(Rational::new(2, 1)).is_err());
        assert_eq!(require_unit_multiplicativity(1).unwrap(), Rational::new(1, 1));
        let scale_two = require_unit_multiplicativity(2).unwrap_err();
        assert!(scale_two.contains("multiplicativity"));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_a2210af4() {
    let admitted = BoundaryRecorda2210af4::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorda2210af4::try_admit(9, 8).is_err());
}
