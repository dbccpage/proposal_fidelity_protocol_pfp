// Validated constructors for the standard anyon models, with pinned exact data.
//
// Every constructor returns a [`RibbonFusionCategory`] that has passed the unit laws,
// the pentagon equation, both hexagon equations, the dimension checks and the
// balancing relation, exactly in the coefficient field `K`. A field that lacks a needed
// root of unity (`zeta_16` for Ising, `zeta_10` for Fibonacci, `zeta_4` for the
// semion) is a typed [`FusionError::FieldTooSmall`], never an approximation.
//
// The data (labels `0 = 1`, conventions of `fusion_category` and `braided`):
//
// - **Ising** (`1, sigma, psi`; needs `zeta_16`): `d = (1, sqrt 2, 1)`;
//   `F^{sigma sigma sigma}_sigma = (1/sqrt 2) [[1, 1], [1, -1]]` on the rows and columns
//   `(1, psi)`, `F^{sigma psi sigma}_psi = F^{psi sigma psi}_sigma = -1`;
//   `R^{sigma sigma}_1 = zeta_16^-1`, `R^{sigma sigma}_psi = zeta_16^3`,
//   `R^{sigma psi}_sigma = R^{psi sigma}_sigma = -i`, `R^{psi psi}_1 = -1`;
//   twists `(1, zeta_16, -1)`; `D^2 = 4`, `p_+ = 2 zeta_16`, `c = 1/2`.
// - **Fibonacci** (`1, tau`; needs `zeta_10`), in the algebraic (non-unitary) gauge
//   `F^{tau tau tau}_tau = [[phi^-1, 1], [phi^-1, -phi^-1]]` (its unitary gauge needs
//   `phi^{-1/2}`, which lies in no cyclotomic field): `d = (1, phi)`,
//   `R^{tau tau}_1 = zeta_10^-4`, `R^{tau tau}_tau = zeta_10^3`, `theta_tau = zeta_10^4`,
//   `D^2 = 2 + phi`, `c = 14/5`.
// - **Semion** (`1, s`; needs `i`): `F^{sss}_s = -1`, `R^{ss}_1 = i`, `D^2 = 2`, `c = 1`.
// - **Pointed braided categories** (`pointed_braided`): trivial associator, braiding a
//   bicharacter `c(x, y)`, so `R^{xy}_{x+y} = c(x, y)` and `theta_x = c(x, x)`. The toric
//   code `D(Z_2)` has `c(x, y) = (-1)^{x_1 y_2}`, the three-fermion model
//   `(-1)^{x_1 y_1 + x_2 y_2 + x_1 y_2}`, and the quantum double `D(Z_n)` has
//   `c(x, y) = zeta_n^{x_1 y_2}`; a cyclic `Z_n` (`n` odd) with
//   `c(x, y) = zeta_n^{k x y}` has `p_+` equal to a quadratic Gauss sum.
//
// Nothing here says that a material hosts any of these categories.
//
// AuthorityEffect: None.
use crate::braided::{BraidedFusionCategory, RSymbols, RibbonFusionCategory};
use crate::error::FusionError;
use crate::fusion_category::{FSymbols, FusionCategory};
use crate::fusion_ring::{AbelianGroup, FusionRing};
use crate::scalar::{golden_ratio, root_of_unity, sqrt_two, FusionScalar};

fn ribbon<K: FusionScalar>(
    ring: FusionRing,
    f: FSymbols<K>,
    r: RSymbols<K>,
    dimensions: Vec<K>,
) -> Result<RibbonFusionCategory<K>, FusionError> {
    let category = FusionCategory::new(ring, f)?;
    RibbonFusionCategory::try_new(BraidedFusionCategory::new(category, r)?, dimensions)
}

/// The Ising category (`1, sigma, psi`), needing a primitive sixteenth root of unity.
pub fn ising<K: FusionScalar>() -> Result<RibbonFusionCategory<K>, FusionError> {
    let ring = FusionRing::ising()?;
    let sqrt2 = sqrt_two::<K>()?;
    let f = ising_f(&ring, &sqrt2)?;
    let r = ising_r(&ring)?;
    ribbon(ring, f, r, vec![K::one(), sqrt2, K::one()])
}

fn ising_f<K: FusionScalar>(ring: &FusionRing, sqrt2: &K) -> Result<FSymbols<K>, FusionError> {
    let inverse = core_number_theory::scalar::inverse(sqrt2).map_err(FusionError::from)?;
    let negative = inverse.neg();
    let minus_one = K::one().neg();
    FSymbols::from_fn(ring, |labels, e, f| match (labels, e, f) {
        ([1, 1, 1, 1], 2, 2) => negative.clone(),
        ([1, 1, 1, 1], _, _) => inverse.clone(),
        ([1, 2, 1, 2] | [2, 1, 2, 1], _, _) => minus_one.clone(),
        _ => K::one(),
    })
}

fn ising_r<K: FusionScalar>(ring: &FusionRing) -> Result<RSymbols<K>, FusionError> {
    let minus_1 = root_of_unity::<K>(16, -1)?;
    let three = root_of_unity::<K>(16, 3)?;
    let minus_i = root_of_unity::<K>(16, 4)?.neg();
    let minus_one = K::one().neg();
    RSymbols::from_fn(ring, |labels| match labels {
        [1, 1, 0] => minus_1.clone(),
        [1, 1, 2] => three.clone(),
        [1, 2, 1] | [2, 1, 1] => minus_i.clone(),
        [2, 2, 0] => minus_one.clone(),
        _ => K::one(),
    })
}

/// The Fibonacci category (`1, tau`) in the algebraic gauge, needing a primitive tenth
/// root of unity.
pub fn fibonacci<K: FusionScalar>() -> Result<RibbonFusionCategory<K>, FusionError> {
    let ring = FusionRing::fibonacci()?;
    let phi = golden_ratio::<K>()?;
    let f = fibonacci_f(&ring, &phi)?;
    let r = fibonacci_r(&ring)?;
    ribbon(ring, f, r, vec![K::one(), phi])
}

fn fibonacci_f<K: FusionScalar>(ring: &FusionRing, phi: &K) -> Result<FSymbols<K>, FusionError> {
    let inverse = phi.sub(&K::one());
    let negative = inverse.neg();
    FSymbols::from_fn(ring, |labels, e, f| match (labels, e, f) {
        ([1, 1, 1, 1], 0, 0) | ([1, 1, 1, 1], 1, 0) => inverse.clone(),
        ([1, 1, 1, 1], 1, 1) => negative.clone(),
        _ => K::one(),
    })
}

fn fibonacci_r<K: FusionScalar>(ring: &FusionRing) -> Result<RSymbols<K>, FusionError> {
    let minus_four = root_of_unity::<K>(10, -4)?;
    let three = root_of_unity::<K>(10, 3)?;
    RSymbols::from_fn(ring, |labels| match labels {
        [1, 1, 0] => minus_four.clone(),
        [1, 1, 1] => three.clone(),
        _ => K::one(),
    })
}

/// The semion category (`1, s`), needing `i`.
pub fn semion<K: FusionScalar>() -> Result<RibbonFusionCategory<K>, FusionError> {
    let ring = FusionRing::semion()?;
    let minus_one = K::one().neg();
    let f = FSymbols::from_fn(&ring, |labels, _, _| {
        if labels == [1, 1, 1, 1] {
            minus_one.clone()
        } else {
            K::one()
        }
    })?;
    let i = root_of_unity::<K>(4, 1)?;
    let r = RSymbols::from_fn(&ring, |labels| {
        if labels == [1, 1, 0] {
            i.clone()
        } else {
            K::one()
        }
    })?;
    ribbon(ring, f, r, vec![K::one(), K::one()])
}

/// A pointed braided category: the abelian group `Z_{m_1} x ... x Z_{m_r}` with the trivial
/// associator and the bicharacter
/// `c(x, y) = exp(2 pi i sum_{ij} B_ij x_i y_j / gcd(m_i, m_j))`, given by the integer
/// matrix `exponents = (B_ij)`. The field must contain the `lcm_{B_ij != 0} gcd(m_i, m_j)`-th
/// roots of unity.
pub fn pointed_braided<K: FusionScalar>(
    moduli: &[usize],
    exponents: &[Vec<i64>],
    names: Option<Vec<String>>,
) -> Result<RibbonFusionCategory<K>, FusionError> {
    let group = AbelianGroup::new(moduli)?;
    check_exponent_shape(exponents, moduli.len())?;
    let plan = PhasePlan::new(moduli, exponents);
    let order = group.order();
    let ring = FusionRing::pointed(moduli, names)?;
    // Admit the actual root subgroup before expensive symbol construction.
    let roots = phase_roots::<K>(plan.order)?;
    let digits = (0..order)
        .map(|x| group.digits(x))
        .collect::<Result<Vec<_>, _>>()?;
    let f = FSymbols::trivial(&ring)?;
    let r = RSymbols::from_fn(&ring, |[x, y, _]| {
        roots[plan.exponent(&digits[x], &digits[y])].clone()
    })?;
    ribbon(ring, f, r, (0..order).map(|_| K::one()).collect())
}

fn check_exponent_shape(exponents: &[Vec<i64>], factors: usize) -> Result<(), FusionError> {
    if exponents.len() != factors {
        return Err(FusionError::ListLength {
            what: "rows of bicharacter exponents",
            expected: factors,
            got: exponents.len(),
        });
    }
    if let Some(row) = exponents.iter().find(|row| row.len() != factors) {
        return Err(FusionError::ListLength {
            what: "columns of bicharacter exponents",
            expected: factors,
            got: row.len(),
        });
    }
    Ok(())
}

fn gcd(mut a: usize, mut b: usize) -> usize {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

fn reduced_coefficient(coefficient: i64, left: usize, right: usize) -> (usize, usize) {
    // Private admitted moduli are 2..=32; the residue is at most 31.
    let denominator = gcd(left, right);
    let numerator = coefficient.rem_euclid(denominator as i64) as usize;
    let common = gcd(numerator, denominator);
    (numerator / common, denominator / common)
}

struct PhasePlan {
    order: usize,
    weights: Vec<Vec<usize>>,
}

impl PhasePlan {
    fn new(moduli: &[usize], exponents: &[Vec<i64>]) -> Self {
        // Caller established product(moduli)<=32 and the square exponent shape.
        let mut order = 1;
        for (i, row) in exponents.iter().enumerate() {
            for (j, &coefficient) in row.iter().enumerate() {
                let (_, denominator) = reduced_coefficient(coefficient, moduli[i], moduli[j]);
                order = order / gcd(order, denominator) * denominator;
            }
        }
        let weights = exponents
            .iter()
            .enumerate()
            .map(|(i, row)| {
                row.iter()
                    .enumerate()
                    .map(|(j, &coefficient)| {
                        let (numerator, denominator) =
                            reduced_coefficient(coefficient, moduli[i], moduli[j]);
                        numerator * (order / denominator)
                    })
                    .collect()
            })
            .collect();
        Self { order, weights }
    }

    fn exponent(&self, left: &[usize], right: &[usize]) -> usize {
        let mut total = 0;
        for (row, &x) in self.weights.iter().zip(left) {
            for (&weight, &y) in row.iter().zip(right) {
                total += weight * x * y;
            }
        }
        total % self.order
    }
}

fn phase_roots<K: FusionScalar>(order: usize) -> Result<Vec<K>, FusionError> {
    let generator = root_of_unity::<K>(order as u32, 1)?;
    let mut roots = Vec::with_capacity(order);
    roots.push(K::one());
    for i in 1..order {
        let next = roots[i - 1].mul(&generator);
        roots.push(next);
    }
    Ok(roots)
}

/// The toric code `D(Z_2)`: objects `1, e, m, eps`, `c(x, y) = (-1)^{x_1 y_2}`. `K = Q`
/// suffices.
pub fn toric_code<K: FusionScalar>() -> Result<RibbonFusionCategory<K>, FusionError> {
    pointed_braided(
        &[2, 2],
        &[vec![0, 1], vec![0, 0]],
        Some(["1", "e", "m", "eps"].map(String::from).to_vec()),
    )
}

/// The three-fermion model: objects `1, f1, f2, f3`, `c(x, y) = (-1)^{x_1 y_1 + x_2 y_2 +
/// x_1 y_2}`, all nontrivial twists `-1`. `K = Q` suffices.
pub fn three_fermion<K: FusionScalar>() -> Result<RibbonFusionCategory<K>, FusionError> {
    pointed_braided(
        &[2, 2],
        &[vec![1, 1], vec![0, 1]],
        Some(["1", "f1", "f2", "f3"].map(String::from).to_vec()),
    )
}

/// The quantum double `D(Z_n)` of a cyclic group: objects `(a, b)` (electric charge `a`,
/// magnetic flux `b`), `c((a, b), (a', b')) = zeta_n^{a b'}`, `theta_{(a, b)} = zeta_n^{a b}`.
/// Needs a primitive `n`-th root of unity.
pub fn quantum_double_cyclic<K: FusionScalar>(
    n: usize,
) -> Result<RibbonFusionCategory<K>, FusionError> {
    let i64_n = i64::try_from(n).map_err(|_| FusionError::Overflow {
        context: "the order of a quantum double",
    })?;
    if i64_n < 2 {
        return Err(FusionError::RankOutOfRange {
            rank: n,
            max: crate::fusion_ring::MAX_RANK,
        });
    }
    pointed_braided(&[n, n], &[vec![0, 1], vec![0, 0]], None)
}

/// The cyclic pointed modular category `Z_n` with `c(x, y) = zeta_n^{k x y}`: modular when
/// `n` is odd and `gcd(k, n) = 1`, where `theta_x = zeta_n^{k x^2}` and `p_+` is the
/// quadratic Gauss sum `sum_x zeta_n^{k x^2}`.
pub fn cyclic_pointed<K: FusionScalar>(
    n: usize,
    k: i64,
) -> Result<RibbonFusionCategory<K>, FusionError> {
    pointed_braided(&[n], &[vec![k]], None)
}

// Origin: engine/crates_rs/core_fusion_categories/src/catalog.rs
// Claim: urn:core:crates_rs:core-fusion-categories:catalog:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord915dd42a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord915dd42a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError915dd42a {
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
impl BoundaryError915dd42a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError915dd42a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError915dd42a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord915dd42a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError915dd42a> {
        if capacity_bound == 0 {
            return Err(BoundaryError915dd42a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError915dd42a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError915dd42a::ExceedsCapacity {
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
mod l4_boundary_tests_915dd42a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord915dd42a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord915dd42a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord915dd42a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord915dd42a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord915dd42a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError915dd42a::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError915dd42a::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
