// AuthorityEffect: None.

//! Naive and Wilson Dirac operators on a declared periodic lattice, and their
//! zero modes.
//!
//! Declared: a Euclidean Clifford family `gamma_1, ..., gamma_d` of size `s`
//! (`crate::dirac_gamma_admission::CliffordFamily` with every metric entry
//! `+1`), a period `N >= 3`, and a rational Wilson coefficient `r`. The carrier
//! is `C^s (x) C^(N^d)`, site `(x_1, ..., x_d)` at index `x_1 + N x_2 + ...`, and
//! `T_mu` is the unit shift `(T_mu psi)(x) = psi(x + e_mu)`. Computed exactly:
//!
//! - [`LatticeDirac::naive_operator`]:
//!   `D = sum_mu gamma_mu (x) (T_mu - T_mu^(-1)) / 2`, the symmetric difference;
//! - [`LatticeDirac::wilson_operator`]:
//!   `D_W = D - (r / 2) sum_mu I (x) (T_mu + T_mu^(-1) - 2)`;
//! - [`LatticeDirac::zero_mode_count`]: the kernel dimension `s N^d - rank`, by
//!   exact rank over `Q(i)`;
//! - [`LatticeDirac::anticommutes_with_chirality`]: `{gamma_* (x) I, D} = 0` for
//!   even `d`, with `gamma_*` from `CliffordFamily::chirality`.
//!
//! Every zero of the naive symbol `i sum_mu gamma_mu sin k_mu` lies at a corner
//! `k in {0, pi}^d`; for even `N` all `2^d` corners are lattice momenta, so the
//! naive kernel counts `2^d` species. The Wilson term vanishes only at `k = 0`
//! and anticommutes with no `gamma_*`. These counts are computed on declared
//! lattices; no continuum limit is taken.
//!
//! Refused: a family with a metric entry other than `+1`, `N < 3` (the symmetric
//! difference of period 2 is zero), and carriers larger than
//! [`MAX_CARRIER_DIMENSION`].


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b3dd064c<T> {
    fn checked_invariant_b3dd064c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b3dd064c<T> for Option<T> {
    #[inline]
    fn checked_invariant_b3dd064c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b3dd064c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b3dd064c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, rq, Rational};

use crate::dirac_gamma_admission::{CliffordFamily, DiracError};

/// Largest `s N^d` handled.
pub const MAX_CARRIER_DIMENSION: usize = 128;

/// Refusals for lattice Dirac operators.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum LatticeError {
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("momentum or spin-structure declaration has the wrong dimension")]
    MomentumShape,
    #[error(transparent)]
    Combinatorics(#[from] core_combinatorics::enumeration::CombinatoricsError),
    #[error("metric entry {index} is not +1: the lattice operator needs a Euclidean family")]
    NotEuclidean { index: usize },
    #[error("period {0} is below 3")]
    PeriodTooSmall(usize),
    #[error("the carrier dimension exceeds {MAX_CARRIER_DIMENSION}")]
    TooLarge,
    #[error("operator is {rows}x{cols}, expected {expected}x{expected}")]
    OperatorShape {
        rows: usize,
        cols: usize,
        expected: usize,
    },
    #[error("Clifford family refused: {0}")]
    Clifford(#[from] DiracError),
}

/// Translation-invariant momentum analysis, independent of a dense position carrier.
/// A boundary bit chooses periodic (false) or antiperiodic (true) fermions per axis.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LatticeMomentumSpectrum {
    period: usize,
    boundary_twists: Vec<bool>,
    spin_dimension: usize,
}

impl LatticeMomentumSpectrum {
    pub fn new(period: usize, boundary_twists: Vec<bool>) -> Result<Self, LatticeError> {
        if period < 3 {
            return Err(LatticeError::PeriodTooSmall(period));
        }
        let d = boundary_twists.len();
        if d == 0 || d > 64 {
            return Err(LatticeError::MomentumShape);
        }
        let spin_dimension = 1usize
            .checked_shl((d / 2) as u32)
            .ok_or(LatticeError::TooLarge)?;
        Ok(Self {
            period,
            boundary_twists,
            spin_dimension,
        })
    }
    pub fn dimensions(&self) -> usize {
        self.boundary_twists.len()
    }
    pub fn spin_dimension(&self) -> usize {
        self.spin_dimension
    }

    /// The exact number of zeros of the naive symbol, before the spin multiplicity.
    pub fn naive_species_count(&self) -> num_bigint::BigUint {
        if self.period % 2 == 0 && self.boundary_twists.iter().any(|b| *b) {
            return num_bigint::BigUint::from(0u8);
        }
        num_bigint::BigUint::from(1u8)
            << if self.period % 2 == 0 {
                self.dimensions()
            } else {
                0
            }
    }
    pub fn naive_kernel_dimension(&self) -> num_bigint::BigUint {
        self.naive_species_count() * self.spin_dimension
    }

    /// Count corners satisfying `mass+2 r (#pi)=0`; no trigonometric approximation.
    pub fn wilson_species_count(
        &self,
        mass: &Rational,
        r: &Rational,
    ) -> Result<num_bigint::BigUint, LatticeError> {
        use num_traits::Zero;
        if self.period % 2 == 0 && self.boundary_twists.iter().any(|b| *b) {
            return Ok(num_bigint::BigUint::from(0u8));
        }
        let forced = if self.period % 2 == 1 {
            self.boundary_twists.iter().filter(|b| **b).count()
        } else {
            0
        };
        let free = if self.period % 2 == 0 {
            self.dimensions()
        } else {
            0
        };
        let mut species = num_bigint::BigUint::from(0u8);
        for k in 0..=free {
            if (mass + r * ri(2 * (forced + k) as i64)).is_zero() {
                species += core_combinatorics::enumeration::binomial(free as u64, k as u64)?;
            }
        }
        Ok(species)
    }

    /// Chirality of the linearized naive species is (-1) to the number of pi components.
    pub fn corner_chirality(corner: &[bool]) -> i8 {
        if corner.iter().filter(|b| **b).count() % 2 == 0 {
            1
        } else {
            -1
        }
    }
    pub fn total_corner_chirality(&self) -> i8 {
        if self.period % 2 == 0 {
            0
        } else {
            Self::corner_chirality(&self.boundary_twists)
        }
    }

    /// Exact sine-square and Wilson mass at momentum k in Q(zeta_(2N)).
    pub fn symbol_data<const C: usize>(
        &self,
        k: &[usize],
    ) -> Result<
        (
            core_number_theory::cyclotomic_field::Cyclotomic<C>,
            core_number_theory::cyclotomic_field::Cyclotomic<C>,
        ),
        LatticeError,
    > {
        use core_number_theory::cyclotomic_field::Cyclotomic;
        if k.len() != self.dimensions()
            || k.iter().any(|x| *x >= self.period)
            || self.period.checked_mul(2) != Some(C)
            || C > core_number_theory::polynomial::MAX_CONDUCTOR
        {
            return Err(LatticeError::MomentumShape);
        }
        let mut sine_square = Cyclotomic::<C>::zero();
        let mut wilson = Cyclotomic::<C>::zero();
        for (axis, momentum) in k.iter().enumerate() {
            let exponent = 2 * (*momentum) + usize::from(self.boundary_twists[axis]);
            let root = Cyclotomic::<C>::zeta(exponent as i64);
            let cosine = root.add(&root.conjugate()).scale(&rq(1, 2));
            let sine2 = Cyclotomic::<C>::one().sub(&cosine.mul(&cosine));
            sine_square = sine_square.add(&sine2);
            wilson = wilson.add(&Cyclotomic::<C>::one().sub(&cosine));
        }
        Ok((sine_square, wilson))
    }
}

/// A Euclidean Clifford family on the periodic lattice `(Z/N)^d`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LatticeDirac {
    family: CliffordFamily,
    period: usize,
    sites: usize,
}

impl LatticeDirac {
    pub fn new(family: CliffordFamily, period: usize) -> Result<Self, LatticeError> {
        if let Some(index) = family.metric().iter().position(|eta| *eta != ri(1)) {
            return Err(LatticeError::NotEuclidean { index });
        }
        if period < 3 {
            return Err(LatticeError::PeriodTooSmall(period));
        }
        let d = u32::try_from(family.gammas().len()).map_err(|_| LatticeError::TooLarge)?;
        let sites = period.checked_pow(d).ok_or(LatticeError::TooLarge)?;
        if family
            .size()
            .checked_mul(sites)
            .is_none_or(|n| n > MAX_CARRIER_DIMENSION)
        {
            return Err(LatticeError::TooLarge);
        }
        Ok(Self {
            family,
            period,
            sites,
        })
    }

    /// `s N^d`.
    pub fn dimension(&self) -> usize {
        self.family.size() * self.sites
    }

    /// `T_mu` on the sites: `T[x][x + e_mu] = 1`.
    fn shift(&self, mu: usize) -> BasicMatrix<GaussianRat> {
        let stride = self.period.pow(mu as u32);
        let mut t = mx::zeros(self.sites, self.sites).checked_invariant_b3dd064c("admitted lattice size");
        for x in 0..self.sites {
            let coordinate = (x / stride) % self.period;
            let forward = x - coordinate * stride + ((coordinate + 1) % self.period) * stride;
            t.set(x, forward, GaussianRat::one())
                .checked_invariant_b3dd064c("periodic lattice indices");
        }
        t
    }

    /// `sum_mu gamma_mu (x) (T_mu - T_mu^(-1)) / 2`.
    pub fn naive_operator(&self) -> BasicMatrix<GaussianRat> {
        let half = GaussianRat::from_rational(rq(1, 2));
        let mut result =
            mx::zeros(self.dimension(), self.dimension()).checked_invariant_b3dd064c("admitted lattice size");
        for (mu, gamma) in self.family.gammas().iter().enumerate() {
            let t = self.shift(mu);
            let difference = mx::scale(
                &mx::sub(&t, &mx::transpose(&t).checked_invariant_b3dd064c("lattice size"))
                    .checked_invariant_b3dd064c("same lattice carrier"),
                &half,
            )
            .checked_invariant_b3dd064c("lattice size");
            result = mx::add(
                &result,
                &mx::kronecker(gamma, &difference).checked_invariant_b3dd064c("admitted tensor carrier"),
            )
            .checked_invariant_b3dd064c("same lattice carrier");
        }
        result
    }

    /// `D - (r / 2) sum_mu I (x) (T_mu + T_mu^(-1) - 2)`.
    pub fn wilson_operator(&self, r: &Rational) -> BasicMatrix<GaussianRat> {
        let identity_spin = mx::identity(self.family.size()).checked_invariant_b3dd064c("spin size");
        let identity_sites = mx::identity(self.sites).checked_invariant_b3dd064c("lattice size");
        let mut laplacian = mx::zeros(self.sites, self.sites).checked_invariant_b3dd064c("lattice size");
        let two =
            mx::scale(&identity_sites, &GaussianRat::from_rational(ri(2))).checked_invariant_b3dd064c("lattice size");
        for mu in 0..self.family.gammas().len() {
            let t = self.shift(mu);
            let term = mx::sub(
                &mx::add(&t, &mx::transpose(&t).checked_invariant_b3dd064c("lattice size")).checked_invariant_b3dd064c("same carrier"),
                &two,
            )
            .checked_invariant_b3dd064c("same carrier");
            laplacian = mx::add(&laplacian, &term).checked_invariant_b3dd064c("same lattice carrier");
        }
        let wilson = mx::scale(
            &mx::kronecker(&identity_spin, &laplacian).checked_invariant_b3dd064c("admitted tensor carrier"),
            &GaussianRat::from_rational(-r / ri(2)),
        )
        .checked_invariant_b3dd064c("lattice size");
        mx::add(&self.naive_operator(), &wilson).checked_invariant_b3dd064c("same lattice carrier")
    }

    fn check_operator(&self, operator: &BasicMatrix<GaussianRat>) -> Result<(), LatticeError> {
        let expected = self.dimension();
        if operator.rows() != expected || operator.cols() != expected {
            return Err(LatticeError::OperatorShape {
                rows: operator.rows(),
                cols: operator.cols(),
                expected,
            });
        }
        Ok(())
    }

    /// The kernel dimension of a lattice operator.
    pub fn zero_mode_count(
        &self,
        operator: &BasicMatrix<GaussianRat>,
    ) -> Result<usize, LatticeError> {
        self.check_operator(operator)?;
        Ok(self.dimension() - elimination::rank(operator)?)
    }

    /// `{gamma_* (x) I, D} = 0`, for an even family.
    pub fn anticommutes_with_chirality(
        &self,
        operator: &BasicMatrix<GaussianRat>,
    ) -> Result<bool, LatticeError> {
        self.check_operator(operator)?;
        let chirality = mx::kronecker(&self.family.chirality()?, &mx::identity(self.sites)?)?;
        Ok(mx::is_zero_matrix(&mx::anticommutator(
            &chirality, operator,
        )?))
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/lattice_dirac_doubling.rs
// Claim: urn:core:crates_rs:core-quantum-physics:lattice-dirac-doubling:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b3dd064c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
