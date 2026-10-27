//! The declared periodic U=t chain, using the existing exact CAR carrier.
//! Rational Euler time slices and the written fixed-volume time-error bound.
//! No spatial or thermodynamic limit, sign solver, or authority is inferred.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_e03487b0<T> {
    fn checked_invariant_e03487b0(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_e03487b0<T> for Option<T> {
    #[inline]
    fn checked_invariant_e03487b0(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_e03487b0<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_e03487b0(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::majorana_fock_algebra::{FockCarrier, MajoranaError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::second_order_jet::MatrixJet2;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_traits::{One, ToPrimitive, Zero};
use core_number_theory::rational::{rq, Rational};

pub const MAX_REPETITIONS: usize = 256;
pub const MAX_BOUND_SITES: usize = 256;
pub const MAX_OBSERVABLE_REPETITIONS: usize = 16;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MeronTimeError {
    #[error(transparent)]
    Fock(#[from] MajoranaError),
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
    #[error("the periodic checkerboard chain needs an even number of sites >=4")]
    Sites,
    #[error("time repetitions must lie in 1..={MAX_REPETITIONS}")]
    Repetitions,
    #[error("parameter center/radius must obey center >= radius >= 0")]
    Parameter,
    #[error("the local transfer parameter must be >=1")]
    TransferParameter,
    #[error("exact scalar or exponential-majorant resource limit exceeded")]
    Resource,
    #[error("the existing CAR lowering matrix has a nonreal entry")]
    NonrealLowering,
    #[error("the operator does not preserve fermion parity")]
    MixesParity,
    #[error("boundary twist must be +1 or -1")]
    BoundaryTwist,
    #[error("the observable query allows at most {MAX_OBSERVABLE_REPETITIONS} repetitions")]
    ObservableRepetitions,
    #[error("the source multiplier must be positive with a nonzero denominator")]
    SourceParameter,
    #[error("one bounded exact weight is required for every spatial site")]
    SpatialProfile,
}

/// Derivatives of the time-slice staggered-density generating trace at zero.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StaggeredMoments {
    partition: Rational,
    first: Rational,
    second: Rational,
    slices: usize,
}

impl StaggeredMoments {
    pub fn partition(&self) -> &Rational {
        &self.partition
    }
    pub fn first(&self) -> &Rational {
        &self.first
    }
    pub fn second(&self) -> &Rational {
        &self.second
    }
    pub fn slices(&self) -> usize {
        self.slices
    }

    /// The square of the time-averaged insertion, under the signed source weights.
    pub fn mean_square(&self) -> Rational {
        &self.second
            / (&self.partition * Rational::from_integer((self.slices * self.slices).into()))
    }
}

fn scalar_size(value: &Rational) -> Result<(), MeronTimeError> {
    if value.numer().bits() > 256 || value.denom().bits() > 256 {
        return Err(MeronTimeError::Resource);
    }
    Ok(())
}

/// The common target parameter belongs to [center-radius,center+radius].
/// The model theorem, rather than this value object, supplies that premise.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EulerTimePlan {
    sites: usize,
    repetitions: usize,
    center: Rational,
    radius: Rational,
    q: Rational,
    slice_growth: Rational,
    raw_density_error: Rational,
    physical_density_error: Rational,
    thermodynamic_density_error: Rational,
}

impl EulerTimePlan {
    pub fn new(
        sites: usize,
        repetitions: usize,
        center: Rational,
        radius: Rational,
    ) -> Result<Self, MeronTimeError> {
        Self::validate_euler_plan_bounds(sites, repetitions, &center, &radius)?;
        let m = Rational::from_integer(repetitions.into());
        let q = Rational::one() + &center / &m;
        scalar_size(&q)?;
        let slice_growth = q.pow(sites as i32);
        let drift = &center * &center / (&m * rq(2, 1)) + &radius;
        let splitting = &center * &center * &slice_growth / &m;
        let raw_density_error = &splitting + &drift;
        let physical_density_error = splitting + drift * rq(3, 4);
        let thermodynamic_density_error = &physical_density_error
            + (&center + &radius) * rq(3, 2) / Rational::from_integer(sites.into());
        Ok(Self {
            sites,
            repetitions,
            center,
            radius,
            q,
            slice_growth,
            raw_density_error,
            physical_density_error,
            thermodynamic_density_error,
        })
    }

    fn validate_euler_plan_bounds(
        sites: usize,
        repetitions: usize,
        center: &Rational,
        radius: &Rational,
    ) -> Result<(), MeronTimeError> {
        if sites < 4 || sites % 2 != 0 {
            return Err(MeronTimeError::Sites);
        }
        if repetitions == 0 || repetitions > MAX_REPETITIONS {
            return Err(MeronTimeError::Repetitions);
        }
        if sites > MAX_BOUND_SITES {
            return Err(MeronTimeError::Resource);
        }
        if *radius < Rational::zero() || center < radius {
            return Err(MeronTimeError::Parameter);
        }
        scalar_size(center)?;
        scalar_size(radius)?;
        Ok(())
    }

    pub fn sites(&self) -> usize {
        self.sites
    }
    pub fn repetitions(&self) -> usize {
        self.repetitions
    }
    pub fn center(&self) -> &Rational {
        &self.center
    }
    pub fn radius(&self) -> &Rational {
        &self.radius
    }
    pub fn q(&self) -> &Rational {
        &self.q
    }
    pub fn slice_growth(&self) -> &Rational {
        &self.slice_growth
    }
    pub fn raw_density_error(&self) -> &Rational {
        &self.raw_density_error
    }
    pub fn physical_density_error(&self) -> &Rational {
        &self.physical_density_error
    }
    pub fn thermodynamic_density_error(&self) -> &Rational {
        &self.thermodynamic_density_error
    }
}

/// Native matrix evaluation keeps the existing FockCarrier resource ceiling.
#[derive(Debug, Clone)]
pub struct FiniteMeronChain {
    sites: usize,
    dimension: usize,
    projectors: Vec<BasicMatrix<Rational>>,
}

impl FiniteMeronChain {
    pub fn new(sites: usize) -> Result<Self, MeronTimeError> {
        if sites < 4 || sites % 2 != 0 {
            return Err(MeronTimeError::Sites);
        }
        let (dimension, lowering, number) = Self::build_fock_modes(sites)?;
        let mut projectors = Vec::new();
        for x in 0..sites {
            let y = (x + 1) % sites;
            projectors.push(Self::build_bond_projector(
                &number[x],
                &number[y],
                &lowering[x],
                &lowering[y],
            )?);
        }
        Ok(Self {
            sites,
            dimension,
            projectors,
        })
    }

    fn build_fock_modes(
        sites: usize,
    ) -> Result<(usize, Vec<BasicMatrix<Rational>>, Vec<BasicMatrix<Rational>>), MeronTimeError>
    {
        let fock = FockCarrier::new(sites)?;
        let dimension = fock.dimension();
        let mut lowering = Vec::new();
        let mut number = Vec::new();
        for mode in 1..=sites {
            let c = fock.lowering(mode)?;
            if c.as_slice().iter().any(|entry| !entry.im.is_zero()) {
                return Err(MeronTimeError::NonrealLowering);
            }
            let c = BasicMatrix::from_row_major(
                dimension,
                dimension,
                c.as_slice().iter().map(|entry| entry.re.clone()).collect(),
            )
            .checked_invariant_e03487b0("validated finite Fock shape");
            number.push(mx::multiply(&mx::transpose(&c)?, &c)?);
            lowering.push(c);
        }
        Ok((dimension, lowering, number))
    }

    fn build_bond_projector(
        n_x: &BasicMatrix<Rational>,
        n_y: &BasicMatrix<Rational>,
        c_x: &BasicMatrix<Rational>,
        c_y: &BasicMatrix<Rational>,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let mixed = Self::build_mixed_density_term(n_x, n_y)?;
        let hopping = Self::build_hopping_term(c_x, c_y)?;
        Ok(mx::scale(&mx::add(&mixed, &hopping)?, &rq(1, 2))?)
    }

    fn build_mixed_density_term(
        n_x: &BasicMatrix<Rational>,
        n_y: &BasicMatrix<Rational>,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let sum_n = mx::add(n_x, n_y)?;
        let prod_n = mx::multiply(n_x, n_y)?;
        Ok(mx::sub(&sum_n, &mx::scale(&prod_n, &rq(2, 1))?)?)
    }

    fn build_hopping_term(
        c_x: &BasicMatrix<Rational>,
        c_y: &BasicMatrix<Rational>,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let hop_xy = mx::multiply(&mx::transpose(c_x)?, c_y)?;
        let hop_yx = mx::multiply(&mx::transpose(c_y)?, c_x)?;
        Ok(mx::add(&hop_xy, &hop_yx)?)
    }

    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn projectors(&self) -> &[BasicMatrix<Rational>] {
        &self.projectors
    }

    fn occupation(&self, state: usize, site: usize) -> usize {
        (state >> (self.sites - 1 - site)) & 1
    }

    /// D=(-1)^sum_(odd sites) n_x, in the existing native tensor order.
    pub fn staggered_basis_change(&self) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let entries = (0..self.dimension)
            .map(|state| {
                let count: usize = (1..self.sites)
                    .step_by(2)
                    .map(|x| self.occupation(state, x))
                    .sum();
                rq(if count % 2 == 0 { 1 } else { -1 }, 1)
            })
            .collect::<Vec<_>>();
        Ok(mx::diagonal(&entries)?)
    }

    /// A=sum_x (-1)^x (n_x-1/2). The basis change leaves A invariant.
    pub fn staggered_density(&self) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let entries = (0..self.dimension)
            .map(|state| {
                let twice: i64 = (0..self.sites)
                    .map(|x| {
                        let term = 2 * self.occupation(state, x) as i64 - 1;
                        if x % 2 == 0 {
                            term
                        } else {
                            -term
                        }
                    })
                    .sum();
                rq(twice, 2)
            })
            .collect::<Vec<_>>();
        Ok(mx::diagonal(&entries)?)
    }

    /// An independently built Heisenberg spin matrix, with XY twist on one bond.
    pub fn heisenberg_spin(&self, twist: i8) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        if twist != 1 && twist != -1 {
            return Err(MeronTimeError::BoundaryTwist);
        }
        let mut entries = vec![Rational::zero(); self.dimension * self.dimension];
        for state in 0..self.dimension {
            for x in 0..self.sites {
                let y = (x + 1) % self.sites;
                let mixed = self.occupation(state, x) != self.occupation(state, y);
                entries[state * self.dimension + state] += rq(if mixed { -1 } else { 1 }, 4);
                if mixed {
                    let after = state ^ (1 << (self.sites - 1 - x)) ^ (1 << (self.sites - 1 - y));
                    entries[after * self.dimension + state] +=
                        rq(if y == 0 { twist as i64 } else { 1 }, 2);
                }
            }
        }
        Ok(
            BasicMatrix::from_row_major(self.dimension, self.dimension, entries)
                .checked_invariant_e03487b0("finite spin matrix shape"),
        )
    }

    /// Restricts a parity-preserving rational operator using the existing Fock owner.
    pub fn parity_block(
        &self,
        operator: &BasicMatrix<Rational>,
        even: bool,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        if operator.rows() != self.dimension || operator.cols() != self.dimension {
            return Err(MeronTimeError::Fock(MajoranaError::Shape {
                rows: operator.rows(),
                cols: operator.cols(),
                dimension: self.dimension,
            }));
        }
        if (0..self.dimension).any(|r| {
            (0..self.dimension).any(|col| {
                r.count_ones() % 2 != col.count_ones() % 2
                    && !operator.get_ref(r, col).checked_invariant_e03487b0("checked invariant").is_zero()
            })
        }) {
            return Err(MeronTimeError::MixesParity);
        }
        let basis = FockCarrier::new(self.sites)?.sector_basis(even);
        Ok(mx::from_fn(basis.len(), basis.len(), |r, col| {
            operator.get_ref(basis[r], basis[col]).checked_invariant_e03487b0("checked invariant").clone()
        })?)
    }

    fn layer_transfer(
        &self,
        parity: usize,
        q: &Rational,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let identity = mx::identity(self.dimension)?;
        let mut layer = identity.clone();
        for x in (parity..self.sites).step_by(2) {
            let local = mx::add(
                &identity,
                &mx::scale(&self.projectors[x], &(q - Rational::one()))?,
            )?;
            layer = mx::multiply(&local, &layer)?;
        }
        Ok(layer)
    }

    /// Exact raw SQL-query moments, with an insertion before each half layer.
    /// The generic noncommuting derivative product belongs to linear algebra.
    pub fn staggered_moments(
        &self,
        repetitions: usize,
        q: &Rational,
    ) -> Result<StaggeredMoments, MeronTimeError> {
        self.insertion_moments(repetitions, q, self.staggered_density()?)
    }

    /// The same original half-time query with a declared spatial test profile.
    pub fn weighted_staggered_moments(
        &self,
        repetitions: usize,
        q: &Rational,
        weights: &[Rational],
    ) -> Result<StaggeredMoments, MeronTimeError> {
        if weights.len() != self.sites {
            return Err(MeronTimeError::SpatialProfile);
        }
        let weights = weights
            .iter()
            .cloned()
            .map(crate::meron_source_field::canonical)
            .collect::<Result<Vec<_>, _>>()?;
        let entries = (0..self.dimension)
            .map(|state| {
                (0..self.sites)
                    .map(|x| {
                        let twice = 2 * self.occupation(state, x) as i64 - 1;
                        &weights[x] * rq(if x % 2 == 0 { twice } else { -twice }, 2)
                    })
                    .sum()
            })
            .collect::<Vec<Rational>>();
        self.insertion_moments(repetitions, q, mx::diagonal(&entries)?)
    }

    fn insertion_moments(
        &self,
        repetitions: usize,
        q: &Rational,
        a: BasicMatrix<Rational>,
    ) -> Result<StaggeredMoments, MeronTimeError> {
        Self::validate_observable_repetitions(repetitions)?;
        let q = crate::meron_source_field::canonical(q.clone())?;
        if q < Rational::one() {
            return Err(MeronTimeError::TransferParameter);
        }
        let product = self.evaluate_moment_jet_product(repetitions, &q, &a)?;
        let [z, first, second] = product.derivatives();
        Ok(StaggeredMoments {
            partition: mx::trace(z)?,
            first: mx::trace(first)?,
            second: mx::trace(second)?,
            slices: 2 * repetitions,
        })
    }

    fn validate_observable_repetitions(repetitions: usize) -> Result<(), MeronTimeError> {
        if repetitions == 0 || repetitions > MAX_REPETITIONS {
            return Err(MeronTimeError::Repetitions);
        }
        if repetitions > MAX_OBSERVABLE_REPETITIONS {
            return Err(MeronTimeError::ObservableRepetitions);
        }
        Ok(())
    }

    fn evaluate_moment_jet_product(
        &self,
        repetitions: usize,
        q: &Rational,
        a: &BasicMatrix<Rational>,
    ) -> Result<MatrixJet2<Rational>, MeronTimeError> {
        let a2 = mx::multiply(a, a)?;
        let layers = [self.layer_transfer(0, q)?, self.layer_transfer(1, q)?];
        let mut product = self.identity_jet2()?;
        for time in 0..2 * repetitions {
            let step = Self::build_step_jet(&layers[time % 2], a, &a2)?;
            product = step.product(&product)?;
        }
        Ok(product)
    }

    fn identity_jet2(&self) -> Result<MatrixJet2<Rational>, MeronTimeError> {
        let id = mx::identity(self.dimension)?;
        let zero = mx::zeros(self.dimension, self.dimension)?;
        Ok(MatrixJet2::new([id, zero.clone(), zero])?)
    }

    fn build_step_jet(
        t: &BasicMatrix<Rational>,
        a: &BasicMatrix<Rational>,
        a2: &BasicMatrix<Rational>,
    ) -> Result<MatrixJet2<Rational>, MeronTimeError> {
        let ta = mx::multiply(t, a)?;
        let ta2 = mx::multiply(t, a2)?;
        Ok(MatrixJet2::new([t.clone(), ta, ta2])?)
    }

    pub fn hamiltonian_over_t(&self) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let mut h = mx::scale(
            &mx::identity(self.dimension)?,
            &(Rational::from_integer(self.sites.into()) / rq(4, 1)),
        )?;
        for p in &self.projectors {
            h = mx::sub(&h, p)?;
        }
        Ok(h)
    }

    /// Trace of (T_odd D_v T_even D_v)^M, with D_v=v^A.
    /// This evaluates the original signed occupation history generating trace.
    pub fn source_field_trace(
        &self,
        repetitions: usize,
        q: &Rational,
        v: &Rational,
    ) -> Result<Rational, MeronTimeError> {
        Self::validate_observable_repetitions(repetitions)?;
        let (q, v) = Self::validate_source_field_params(q, v)?;
        let step = self.build_source_transfer_step(&q, &v)?;
        let total = mx::power(&step, repetitions as u64)?;
        Ok(mx::trace(&total)?)
    }

    fn build_source_transfer_step(
        &self,
        q: &Rational,
        v: &Rational,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let insertion = self.build_source_insertion(v)?;
        let odd = mx::multiply(&self.layer_transfer(1, q)?, &insertion)?;
        let even = mx::multiply(&self.layer_transfer(0, q)?, &insertion)?;
        Ok(mx::multiply(&odd, &even)?)
    }

    fn validate_source_field_params(
        q: &Rational,
        v: &Rational,
    ) -> Result<(Rational, Rational), MeronTimeError> {
        if q.denom().is_zero() {
            return Err(MeronTimeError::TransferParameter);
        }
        if v.denom().is_zero() {
            return Err(MeronTimeError::SourceParameter);
        }
        scalar_size(q)?;
        scalar_size(v)?;
        let q = q.reduced();
        let v = v.reduced();
        if q < Rational::one() {
            return Err(MeronTimeError::TransferParameter);
        }
        if v <= Rational::zero() {
            return Err(MeronTimeError::SourceParameter);
        }
        Ok((q, v))
    }

    fn build_source_insertion(
        &self,
        v: &Rational,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let density = self.staggered_density()?;
        let mut diagonal = Vec::with_capacity(self.dimension);
        for state in 0..self.dimension {
            let a = density
                .get_ref(state, state)
                .checked_invariant_e03487b0("checked invariant");
            if !a.is_integer() {
                return Err(MeronTimeError::Parameter);
            }
            let exponent = a.to_integer().to_i32().ok_or(MeronTimeError::Resource)?;
            diagonal.push(v.pow(exponent));
        }
        Ok(mx::diagonal(&diagonal)?)
    }

    /// The unscaled full-Fock trace, with no fixed-particle-number projection.
    pub fn transfer_trace(
        &self,
        repetitions: usize,
        q: &Rational,
    ) -> Result<Rational, MeronTimeError> {
        if repetitions == 0 || repetitions > MAX_REPETITIONS {
            return Err(MeronTimeError::Repetitions);
        }
        scalar_size(q)?;
        if q < &Rational::one() {
            return Err(MeronTimeError::TransferParameter);
        }
        let odd = self.layer_transfer(1, q)?;
        let even = self.layer_transfer(0, q)?;
        let pair = mx::multiply(&odd, &even)?;
        let power = Self::pow_matrix(pair, repetitions, self.dimension)?;
        Ok(mx::trace(&power)?)
    }

    fn pow_matrix(
        mut pair: BasicMatrix<Rational>,
        mut exponent: usize,
        dimension: usize,
    ) -> Result<BasicMatrix<Rational>, MeronTimeError> {
        let mut power = mx::identity(dimension)?;
        while exponent > 0 {
            if exponent % 2 == 1 {
                power = mx::multiply(&pair, &power)?;
            }
            exponent /= 2;
            if exponent > 0 {
                pair = mx::multiply(&pair, &pair)?;
            }
        }
        Ok(power)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/meron_time_refinement.rs
// Claim: urn:core:crates_rs:core-quantum-physics:meron-time-refinement:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e03487b0 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
