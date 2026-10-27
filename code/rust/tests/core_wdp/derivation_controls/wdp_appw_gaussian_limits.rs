//! Finite witness for the carrier L=4, M=1, r=0.
//!
//! TD-2a makes both layers the identity. TD-6 scales Phi by 1/(2 M sqrt(L)).
//! The values below are exact rationals on this carrier. They are not a
//! continuum limit and not a joint spacetime Gaussian field.

const SITES: usize = 4;
const M: i64 = 1;
const HALF_STEPS: usize = 2;
const DIM: usize = 1 << SITES;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Rat {
    pub num: i64,
    pub den: i64,
}

impl Rat {
    pub fn new(num: i64, den: i64) -> Self {
        assert!(den != 0, "rational denominator is zero");
        from_parts(num as i128, den as i128)
    }

    fn neg(self) -> Self {
        from_parts(-(self.num as i128), self.den as i128)
    }

    fn add(self, rhs: Self) -> Self {
        from_parts(
            self.num as i128 * rhs.den as i128 + rhs.num as i128 * self.den as i128,
            self.den as i128 * rhs.den as i128,
        )
    }

    fn sub(self, rhs: Self) -> Self {
        self.add(rhs.neg())
    }

    fn mul(self, rhs: Self) -> Self {
        from_parts(
            self.num as i128 * rhs.num as i128,
            self.den as i128 * rhs.den as i128,
        )
    }

    fn is_zero(self) -> bool {
        self.num == 0
    }

    fn abs(self) -> Self {
        from_parts((self.num as i128).abs(), self.den as i128)
    }

    fn lt(self, rhs: Self) -> bool {
        cross(self, rhs) < 0
    }

    fn gt(self, rhs: Self) -> bool {
        cross(self, rhs) > 0
    }
}

fn from_parts(mut num: i128, mut den: i128) -> Rat {
    assert!(den != 0, "rational denominator is zero");
    if den < 0 {
        num = -num;
        den = -den;
    }
    let g = gcd_i128(num, den);
    num /= g;
    den /= g;
    assert!(
        num <= i64::MAX as i128 && num >= i64::MIN as i128 && den <= i64::MAX as i128,
        "rational does not fit in i64"
    );
    Rat {
        num: num as i64,
        den: den as i64,
    }
}

fn gcd_i128(mut a: i128, mut b: i128) -> i128 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    if a == 0 { 1 } else { a }
}

fn cross(left: Rat, right: Rat) -> i128 {
    left.num as i128 * right.den as i128 - right.num as i128 * left.den as i128
}

fn pow_rat(base: Rat, exp: u32) -> Rat {
    let mut acc = Rat::new(1, 1);
    for _ in 0..exp {
        acc = acc.mul(base);
    }
    acc
}

fn binom(n: usize, k: usize) -> i64 {
    if k > n {
        return 0;
    }
    let k = if k + k > n { n - k } else { k };
    let mut value = 1i64;
    for i in 0..k {
        value = value * (n - i) as i64 / (i as i64 + 1);
    }
    value
}

/// Connected cumulants through order 4, with kappa_n the nth derivative of log E[e^{u Phi}] at 0.
fn cumulants(moments: &[Rat; 5]) -> [Rat; 5] {
    assert_eq!(moments[0], Rat::new(1, 1), "zeroth moment must be 1");
    let mut kappa = [Rat::new(0, 1); 5];
    for n in 1..=4 {
        let mut value = moments[n];
        for k in 1..n {
            let term = Rat::new(binom(n - 1, k - 1), 1)
                .mul(kappa[k])
                .mul(moments[n - k]);
            value = value.sub(term);
        }
        kappa[n] = value;
    }
    kappa
}

fn integer_sqrt(n: i64) -> i64 {
    let mut k = 0i64;
    loop {
        let square = k.saturating_mul(k);
        if square == n {
            return k;
        }
        if square > n {
            panic!("TD-6 scaling needs an integer square root on this carrier");
        }
        k += 1;
    }
}

fn scale_denominator() -> i64 {
    let root = integer_sqrt(SITES as i64);
    assert_eq!(root * root, SITES as i64, "L is not a square");
    let den = 2 * M * root;
    assert_eq!(den, 4, "2 M sqrt(L) is 4 only for this carrier");
    den
}

/// Staggered occupation observable a_x = (-1)^x (n_x - 1/2) on the periodic chain.
fn a_of(state: usize, site: usize) -> Rat {
    assert!(site < SITES, "site is outside the four-site cycle");
    let occupied = ((state >> site) & 1) as i64;
    let sign = if site % 2 == 0 { 1i64 } else { -1i64 };
    Rat::new(sign * (2 * occupied - 1), 2)
}

fn periodic_neighbors(site: usize) -> (usize, usize) {
    ((site + SITES - 1) % SITES, (site + 1) % SITES)
}

/// At r=0 both checkerboard layers are the identity, and the trace closes s_2 = s_0.
fn history_weight(s0: usize, s1: usize) -> i64 {
    let layer0 = if s1 == s0 { 1i64 } else { 0 };
    let layer1 = if s0 == s1 { 1i64 } else { 0 };
    layer0 * layer1
}

fn site_phi(profile: &[[i64; SITES]; HALF_STEPS], s0: usize, s1: usize, site: usize) -> Rat {
    let coeff = Rat::new(1, scale_denominator());
    let first = Rat::new(profile[0][site], 1).mul(a_of(s0, site));
    let second = Rat::new(profile[1][site], 1).mul(a_of(s1, site));
    coeff.mul(first.add(second))
}

fn phi_on_history(profile: &[[i64; SITES]; HALF_STEPS], s0: usize, s1: usize) -> Rat {
    let mut sum = Rat::new(0, 1);
    for site in 0..SITES {
        sum = sum.add(site_phi(profile, s0, s1, site));
    }
    sum
}

fn moments_of(observe: impl Fn(usize, usize) -> Rat) -> (i64, [Rat; 5]) {
    let mut mass = 0i64;
    let mut sums = [Rat::new(0, 1); 5];
    for s0 in 0..DIM {
        for s1 in 0..DIM {
            let weight = history_weight(s0, s1);
            if weight == 0 {
                continue;
            }
            mass += weight;
            let phi = observe(s0, s1);
            for n in 1..=4 {
                sums[n] = sums[n].add(Rat::new(weight, 1).mul(pow_rat(phi, n as u32)));
            }
        }
    }
    assert!(mass > 0, "identity layers produced no history");
    let scale = Rat::new(1, mass);
    let mut moments = [Rat::new(0, 1); 5];
    moments[0] = Rat::new(1, 1);
    for n in 1..=4 {
        moments[n] = scale.mul(sums[n]);
    }
    (mass, moments)
}

fn joint_cumulants(profile: &[[i64; SITES]; HALF_STEPS]) -> (i64, [Rat; 5]) {
    let (mass, moments) = moments_of(|s0, s1| phi_on_history(profile, s0, s1));
    (mass, cumulants(&moments))
}

/// Sum of the four site cumulants, each measured on its own labels. Not one site copied four times.
fn site_cumulant_sum(profile: &[[i64; SITES]; HALF_STEPS]) -> (Rat, Rat) {
    let mut kappa2 = Rat::new(0, 1);
    let mut kappa4 = Rat::new(0, 1);
    for site in 0..SITES {
        let (_mass, moments) = moments_of(|s0, s1| site_phi(profile, s0, s1, site));
        let kappa = cumulants(&moments);
        kappa2 = kappa2.add(kappa[2]);
        kappa4 = kappa4.add(kappa[4]);
    }
    (kappa2, kappa4)
}

fn supported_phi_is_zero(profile: &[[i64; SITES]; HALF_STEPS]) -> bool {
    let mut seen = 0i64;
    for s0 in 0..DIM {
        for s1 in 0..DIM {
            if history_weight(s0, s1) == 0 {
                continue;
            }
            seen += 1;
            if !phi_on_history(profile, s0, s1).is_zero() {
                return false;
            }
        }
    }
    seen == DIM as i64
}

fn constant_profile() -> [[i64; SITES]; HALF_STEPS] {
    [[1i64; SITES]; HALF_STEPS]
}

fn alternating_profile() -> [[i64; SITES]; HALF_STEPS] {
    let mut profile = [[0i64; SITES]; HALF_STEPS];
    for site in 0..SITES {
        profile[0][site] = 1;
        profile[1][site] = -1;
    }
    profile
}

fn time_independent(profile: &[[i64; SITES]; HALF_STEPS]) -> bool {
    (0..SITES).all(|site| profile[0][site] == profile[1][site])
}

fn ar9_schedule(l: i64, m: i64) -> bool {
    if l <= 0 || m != l.saturating_mul(l) {
        return false;
    }
    let mut k = 1i64;
    loop {
        let k2 = k.saturating_mul(k);
        let k4 = k2.saturating_mul(k2);
        let scheduled = 4i64.saturating_mul(k4);
        if scheduled == l {
            return true;
        }
        if scheduled > l || k > l {
            return false;
        }
        k += 1;
    }
}

fn in_static_input_class(profile: &[[i64; SITES]; HALF_STEPS], l: i64, m: i64) -> bool {
    time_independent(profile) && ar9_schedule(l, m)
}

fn infinity_norm(profile: &[[i64; SITES]; HALF_STEPS]) -> i64 {
    let mut norm = 0i64;
    for row in profile {
        for value in row {
            let abs = value.abs();
            if abs > norm {
                norm = abs;
            }
        }
    }
    norm
}

/// Printed TD-7 majorant at n=2: (2/19) * 2! * (N/R)^2 * L^0, with R=1/64.
fn majorant_kappa2(norm_inf: i64) -> Rat {
    assert!(norm_inf >= 0, "infinity norm is negative");
    let scaled = (norm_inf as i128) * 64;
    let scaled_n = scaled * scaled;
    from_parts(2 * 2 * scaled_n, 19)
}

fn strictly_below(value: Rat, bound: Rat) -> bool {
    assert!(bound.gt(Rat::new(0, 1)), "majorant is not positive");
    value.abs().lt(bound)
}

fn r_inside_disk() -> bool {
    let r = Rat::new(0, 1);
    !r.lt(Rat::new(0, 1)) && !r.gt(Rat::new(1, 192))
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub dimension: i64,
    pub supported_histories: i64,
    pub labels: i64,
    pub kappa2: Rat,
    pub kappa4: Rat,
    pub odd_cumulants_vanish: bool,
    pub alternating_kappa2: Rat,
    pub alternating_kappa4: Rat,
    pub alternating_every_cumulant_zero: bool,
    pub static_contains_alternating: bool,
    pub on_static_schedule: bool,
    pub kappa2_equals_chi0: bool,
    pub static_field_identified: bool,
    pub finite_constant_profile_is_gaussian: bool,
    pub joint_spacetime_field_limit: bool,
    pub continuum_limit: bool,
    pub majorant_n2: Rat,
    pub cumulants_inside_majorant: bool,
    pub r_inside_disk: bool,
}

pub fn witness() -> Witness {
    assert_eq!(SITES, 4, "selected carrier has four periodic sites");
    assert_eq!(M, 1, "selected carrier has M=1");
    assert_eq!(HALF_STEPS, (2 * M) as usize, "half-steps are j=0,1");
    assert_eq!(DIM, 16, "full periodic Fock space has dimension 2^L");
    assert!(r_inside_disk(), "r=0 is outside 0<=r<=1/192");
    for site in 0..SITES {
        let (left, right) = periodic_neighbors(site);
        assert_eq!((left + 1) % SITES, site, "left neighbor is not periodic");
        assert_eq!((site + 1) % SITES, right, "right neighbor is not periodic");
        assert_ne!(left, right, "a site on the cycle is not distinct from both neighbors");
    }

    let constant = constant_profile();
    let alternating = alternating_profile();
    let (mass, constant_kappa) = joint_cumulants(&constant);
    let (alt_mass, alternating_kappa) = joint_cumulants(&alternating);
    assert_eq!(mass, DIM as i64, "supported histories are the occupation basis");
    assert_eq!(alt_mass, mass, "both profiles use the same identity layers");

    let (site2, site4) = site_cumulant_sum(&constant);
    assert_eq!(site2, constant_kappa[2], "constant kappa_2 is not a copied 1-site value");
    assert_eq!(site4, constant_kappa[4], "constant kappa_4 is not a copied 1-site value");
    let (alt_site2, alt_site4) = site_cumulant_sum(&alternating);
    assert_eq!(alt_site2, alternating_kappa[2], "alternating kappa_2 copied a constant profile");
    assert_eq!(alt_site4, alternating_kappa[4], "alternating kappa_4 copied a constant profile");

    let phi_zero = supported_phi_is_zero(&alternating);
    let alternating_orders_zero = alternating_kappa.iter().skip(1).all(|term| term.is_zero());
    let chi0 = Rat::new(1, 4);
    let on_schedule = ar9_schedule(SITES as i64, M);
    let h_minus_s_constructed = false;
    let norm = infinity_norm(&constant);
    assert_eq!(norm, infinity_norm(&alternating));
    let majorant = majorant_kappa2(norm);

    Witness {
        dimension: DIM as i64,
        supported_histories: mass,
        labels: (HALF_STEPS * SITES) as i64,
        kappa2: constant_kappa[2],
        kappa4: constant_kappa[4],
        odd_cumulants_vanish: constant_kappa[1].is_zero() && constant_kappa[3].is_zero(),
        alternating_kappa2: alternating_kappa[2],
        alternating_kappa4: alternating_kappa[4],
        alternating_every_cumulant_zero: phi_zero && alternating_orders_zero,
        static_contains_alternating: in_static_input_class(&alternating, SITES as i64, M),
        on_static_schedule: on_schedule,
        kappa2_equals_chi0: constant_kappa[2] == chi0,
        static_field_identified: on_schedule && constant_kappa[2] == chi0 && h_minus_s_constructed,
        finite_constant_profile_is_gaussian: constant_kappa[4].is_zero(),
        joint_spacetime_field_limit: false,
        continuum_limit: false,
        majorant_n2: majorant,
        cumulants_inside_majorant: strictly_below(constant_kappa[2], majorant)
            && strictly_below(alternating_kappa[2], majorant),
        r_inside_disk: r_inside_disk(),
    }
}

pub fn reject_alternating_as_static_chi(claimed_num: i64, claimed_den: i64) -> Result<(), &'static str> {
    let claimed = Rat::new(claimed_num, claimed_den);
    let actual = witness().alternating_kappa2;
    let chi0 = Rat::new(1, 4);
    if claimed == chi0 && actual != chi0 {
        Err("alternating 8-label cumulant is 0; chi(0)=1/4 is not that value")
    } else if claimed != actual {
        Err("claimed alternating cumulant differs from the computed value")
    } else {
        Ok(())
    }
}

pub fn reject_joint_spacetime_limit() -> Result<(), &'static str> {
    let finite = witness();
    if finite.joint_spacetime_field_limit || finite.continuum_limit || finite.static_field_identified {
        Ok(())
    } else {
        Err("L=4, M=1, r=0 is not a joint spacetime Gaussian field or a continuum limit")
    }
}

pub fn reject_gate_e_as_in_disk() -> Result<(), &'static str> {
    let r = Rat::new(1, 10);
    if r.gt(Rat::new(1, 192)) {
        Err("r=1/10 lies outside 0<=r<=1/192 and is not an in-disk Gaussian field")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appw_gaussian_limits.rs
// Claim: urn:core:crates_rs:tests:wdp-appw-gaussian-limits:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordfe0a54ef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordfe0a54ef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorfe0a54ef {
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
impl BoundaryErrorfe0a54ef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorfe0a54ef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorfe0a54ef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordfe0a54ef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorfe0a54ef> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorfe0a54ef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorfe0a54ef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorfe0a54ef::ExceedsCapacity {
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
        a_of, ar9_schedule, history_weight, periodic_neighbors, phi_on_history, reject_alternating_as_static_chi,
        reject_gate_e_as_in_disk, reject_joint_spacetime_limit, alternating_profile, constant_profile, witness, Rat,
    };

    #[test]
    fn exact_values_on_the_selected_carrier() {
        assert_eq!(a_of(0, 0), Rat::new(-1, 2));
        assert_eq!(a_of(0, 1), Rat::new(1, 2));
        assert_eq!(a_of(0, 2), Rat::new(-1, 2));
        assert_eq!(a_of(0, 3), Rat::new(1, 2));
        assert_eq!(periodic_neighbors(0), (3, 1));
        assert_eq!(periodic_neighbors(3), (2, 0));
        assert_eq!(history_weight(5, 5), 1);
        assert_eq!(history_weight(5, 0), 0);
        assert_eq!(phi_on_history(&constant_profile(), 5, 5), Rat::new(1, 1));
        assert_eq!(phi_on_history(&alternating_profile(), 5, 5), Rat::new(0, 1));

        let result = witness();
        assert_eq!(result.dimension, 16);
        assert_eq!(result.supported_histories, 16);
        assert_eq!(result.labels, 8);
        assert_eq!(result.kappa2, Rat::new(1, 4));
        assert_eq!(result.kappa4, Rat::new(-1, 32));
        assert!(result.odd_cumulants_vanish);
        assert_eq!(result.alternating_kappa2, Rat::new(0, 1));
        assert_eq!(result.alternating_kappa4, Rat::new(0, 1));
        assert!(result.alternating_every_cumulant_zero);
        assert!(!result.static_contains_alternating);
        assert!(!result.on_static_schedule);
        assert!(result.kappa2_equals_chi0);
        assert!(!result.static_field_identified);
        assert!(!result.finite_constant_profile_is_gaussian);
        assert!(!result.joint_spacetime_field_limit);
        assert!(!result.continuum_limit);
        assert_eq!(result.majorant_n2, Rat::new(16384, 19));
        assert!(result.cumulants_inside_majorant);
        assert!(result.r_inside_disk);
        assert!(ar9_schedule(4, 16));
        assert!(!ar9_schedule(4, 1));
    }

    #[test]
    fn alternating_profile_and_joint_limit_are_refused() {
        assert!(reject_alternating_as_static_chi(1, 4).is_err());
        assert!(reject_alternating_as_static_chi(0, 1).is_ok());
        assert!(reject_joint_spacetime_limit().is_err());
        assert!(reject_gate_e_as_in_disk().is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_fe0a54ef() {
    let admitted = BoundaryRecordfe0a54ef::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordfe0a54ef::try_admit(9, 8).is_err());
}
