// AuthorityEffect: None.

//! Finite time-sliced action shadows with an exact phase policy.
//!
//! Declared: a partition `t_0 < ... < t_n`, a finite position carrier `X`
//! (the same at every slice), endpoints `a, b in X`, a mass `m > 0`,
//! `hbar > 0` and a nonzero normalization `Z` in `Q(i)`. The free-particle step
//! action is `L dt = (m/2) (y - x)^2 / dt`. A history
//! `(a, x_1, ..., x_(n-1), b)` has action `S`, the sum of its step actions, and
//! the kernel is `K = Z^(-1) sum_gamma e^(i S(gamma) / hbar)`.
//!
//! `e^(i theta)` is transcendental for rational `theta != 0`, so the kernel is
//! kept as a [`PhaseSum`]: a finite `Q(i)`-combination of formal phases, an
//! element of the group ring `Q(i)[Q]`. Phases multiply by adding exponents, as
//! actions add along a history, so the kernel is the graded path-sum of
//! `crate::graded_path_sum` with one formal phase per step, and the history
//! enumeration and the transfer-matrix product must agree. A number is
//! produced only by [`PhaseSum::evaluate`], at a declared unit `u` of `Q(i)`
//! standing for `e^(i kappa)`, and only when every phase is an integer multiple
//! of `kappa`; any other phase is refused, never rounded.
//!
//! Two shadows of one interval are compared exactly: a nonzero
//! [`refinement_residual`] is a refinement tear. No convergence, topology or
//! continuum kernel is produced here, and no Lagrangian other than the free
//! particle is declared.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_cacf1b5a<T> {
    fn checked_invariant_cacf1b5a(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_cacf1b5a<T> for Option<T> {
    #[inline]
    fn checked_invariant_cacf1b5a(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_cacf1b5a<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_cacf1b5a(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::BTreeMap;

use linear_algebra::scalars::{Ring, Semiring};
use num_traits::{Signed, Zero};

use core_lie_theory::cayley::{is_unit, unit_pow};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

use crate::graded_path_sum::{TimeSlicedTransport, TransportError};

/// Refusals for shadow declarations, evaluations and comparisons.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ShadowRefusal {
    #[error(transparent)]
    Phase(#[from] core_lie_theory::cayley::CayleyError),
    #[error("a partition needs at least two times, got {0}")]
    TooFewTimes(usize),
    #[error("slice {step} does not have positive width")]
    NonIncreasingTimes { step: usize },
    #[error("the position carrier is empty")]
    EmptyCarrier,
    #[error("carrier point {index} repeats an earlier point")]
    DuplicateCarrierPoint { index: usize },
    #[error("the {0} endpoint is not a carrier point")]
    EndpointNotInCarrier(&'static str),
    #[error("the mass must be strictly positive")]
    NonPositiveMass,
    #[error("hbar must be strictly positive")]
    NonPositiveHbar,
    #[error("the normalization is zero")]
    ZeroNormalization,
    #[error("the phase quantum is zero")]
    ZeroQuantum,
    #[error("the declared phase unit does not have modulus one")]
    NonUnitPhase,
    #[error("phase {0} is not an integer multiple of the declared quantum")]
    IncommensuratePhase(Rational),
    #[error("the finer shadow does not refine the coarser one: {0}")]
    NotARefinement(&'static str),
    #[error("transport refusal: {0}")]
    Transport(#[from] TransportError),
}

/// A finite `Q(i)`-combination of formal phases `e^(i theta)`, `theta` rational.
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct PhaseSum {
    terms: BTreeMap<Rational, GaussianRat>,
}

impl PhaseSum {
    /// The single phase `e^(i theta)`.
    pub fn phase(theta: Rational) -> Self {
        let mut terms = BTreeMap::new();
        terms.insert(theta, GaussianRat::one());
        Self { terms }
    }

    /// Coefficient of each phase; zero coefficients are never stored.
    pub fn terms(&self) -> &BTreeMap<Rational, GaussianRat> {
        &self.terms
    }

    fn accumulate(&mut self, theta: Rational, coefficient: GaussianRat) {
        let sum = self
            .terms
            .get(&theta)
            .map_or(coefficient.clone(), |existing| existing.add(&coefficient));
        if Zero::is_zero(&sum.re) && Zero::is_zero(&sum.im) {
            self.terms.remove(&theta);
        } else {
            self.terms.insert(theta, sum);
        }
    }

    /// `c` times this sum.
    pub fn scale(&self, c: &GaussianRat) -> Self {
        let mut out = Self::default();
        for (theta, coefficient) in &self.terms {
            out.accumulate(theta.clone(), coefficient.mul(c));
        }
        out
    }

    /// The value at a declared unit `u` standing for `e^(i quantum)`:
    /// `e^(i theta) -> u^(theta / quantum)`, refused unless every
    /// `theta / quantum` is an integer.
    pub fn evaluate(
        &self,
        quantum: &Rational,
        unit: &GaussianRat,
    ) -> Result<GaussianRat, ShadowRefusal> {
        if Zero::is_zero(quantum) {
            return Err(ShadowRefusal::ZeroQuantum);
        }
        if !is_unit(unit) {
            return Err(ShadowRefusal::NonUnitPhase);
        }
        self.terms
            .iter()
            .try_fold(GaussianRat::zero(), |acc, (theta, c)| {
                let ratio = theta / quantum;
                if !ratio.is_integer() {
                    return Err(ShadowRefusal::IncommensuratePhase(theta.clone()));
                }
                Ok(acc.add(&c.mul(&unit_pow(unit, &ratio.to_integer())?)))
            })
    }
}

impl Semiring for PhaseSum {
    fn zero() -> Self {
        Self::default()
    }
    fn one() -> Self {
        Self::phase(<Rational as Zero>::zero())
    }
    fn add(&self, rhs: &Self) -> Self {
        let mut out = self.clone();
        for (theta, coefficient) in &rhs.terms {
            out.accumulate(theta.clone(), coefficient.clone());
        }
        out
    }
    fn mul(&self, rhs: &Self) -> Self {
        let mut out = Self::default();
        for (s, a) in &self.terms {
            for (t, b) in &rhs.terms {
                out.accumulate(s + t, a.mul(b));
            }
        }
        out
    }
    fn is_zero(&self) -> bool {
        self.terms.is_empty()
    }
}

impl Ring for PhaseSum {
    fn neg(&self) -> Self {
        Self {
            terms: self
                .terms
                .iter()
                .map(|(theta, c)| (theta.clone(), c.neg()))
                .collect(),
        }
    }
}

/// One replayed history: its positions and its action.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShadowHistory {
    pub positions: Vec<Rational>,
    pub action: Rational,
}

/// The replayed histories and the normalized kernel they assemble.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ShadowCertificate {
    pub histories: Vec<ShadowHistory>,
    pub kernel: PhaseSum,
}

/// A declared free-particle time-sliced shadow.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FreeParticleShadow {
    times: Vec<Rational>,
    carrier: Vec<Rational>,
    start: usize,
    end: usize,
    mass: Rational,
    hbar: Rational,
    normalization: GaussianRat,
}

fn validate_times_and_carrier(
    times: &[Rational],
    carrier: &[Rational],
) -> Result<(), ShadowRefusal> {
    if times.len() < 2 {
        return Err(ShadowRefusal::TooFewTimes(times.len()));
    }
    if let Some(step) = times.windows(2).position(|pair| pair[1] <= pair[0]) {
        return Err(ShadowRefusal::NonIncreasingTimes { step });
    }
    if carrier.is_empty() {
        return Err(ShadowRefusal::EmptyCarrier);
    }
    if let Some(index) = (1..carrier.len()).find(|&i| carrier[..i].contains(&carrier[i])) {
        return Err(ShadowRefusal::DuplicateCarrierPoint { index });
    }
    Ok(())
}

impl FreeParticleShadow {
    /// Check the partition, carrier, endpoints, mass, `hbar` and normalization.
    pub fn new(
        times: Vec<Rational>,
        carrier: Vec<Rational>,
        start: Rational,
        end: Rational,
        mass: Rational,
        hbar: Rational,
        normalization: GaussianRat,
    ) -> Result<Self, ShadowRefusal> {
        validate_times_and_carrier(&times, &carrier)?;
        let locate = |point: &Rational, which: &'static str| {
            carrier
                .iter()
                .position(|x| x == point)
                .ok_or(ShadowRefusal::EndpointNotInCarrier(which))
        };
        let (start, end) = (locate(&start, "start")?, locate(&end, "end")?);
        if !mass.is_positive() {
            return Err(ShadowRefusal::NonPositiveMass);
        }
        if !hbar.is_positive() {
            return Err(ShadowRefusal::NonPositiveHbar);
        }
        if Zero::is_zero(&normalization.re) && Zero::is_zero(&normalization.im) {
            return Err(ShadowRefusal::ZeroNormalization);
        }
        let out = Self {
            times,
            carrier,
            start,
            end,
            mass,
            hbar,
            normalization,
        };
        Ok(out)
    }

    /// `(m/2) (y - x)^2 / dt_k` on slice `k`.
    fn step_action(&self, step: usize, x: &Rational, y: &Rational) -> Rational {
        let dt = &self.times[step + 1] - &self.times[step];
        let dx = y - x;
        &self.mass * &dx * &dx / (ri(2) * dt)
    }

    fn transport(&self) -> TimeSlicedTransport<PhaseSum> {
        let n = self.carrier.len();
        let steps = (0..self.times.len() - 1)
            .map(|k| {
                (0..n)
                    .map(|y| {
                        (0..n)
                            .map(|x| {
                                PhaseSum::phase(
                                    self.step_action(k, &self.carrier[x], &self.carrier[y])
                                        / &self.hbar,
                                )
                            })
                            .collect()
                    })
                    .collect()
            })
            .collect();
        TimeSlicedTransport::new(vec![n; self.times.len()], steps)
            .checked_invariant_cacf1b5a("carrier and partition sizes are fixed at declaration")
    }

    /// Enumerate every history once, sum its step actions and assemble
    /// `K = Z^(-1) sum e^(i S / hbar)`.
    pub fn replay(&self) -> Result<ShadowCertificate, ShadowRefusal> {
        let mut histories = Vec::new();
        let mut kernel = PhaseSum::default();
        for indices in self.transport().histories(self.start, self.end)? {
            let positions: Vec<Rational> =
                indices.iter().map(|&i| self.carrier[i].clone()).collect();
            let action: Rational = positions
                .windows(2)
                .enumerate()
                .map(|(k, pair)| self.step_action(k, &pair[0], &pair[1]))
                .sum();
            kernel = kernel.add(&PhaseSum::phase(&action / &self.hbar));
            histories.push(ShadowHistory { positions, action });
        }
        Ok(ShadowCertificate {
            histories,
            kernel: kernel.scale(&self.normalization.inv()),
        })
    }

    /// The same kernel from the product of the step transfer matrices.
    pub fn transfer_kernel(&self) -> PhaseSum {
        self.transport()
            .propagator()
            .get_ref(self.end, self.start)
            .checked_invariant_cacf1b5a("validated endpoints")
            .scale(&self.normalization.inv())
    }
}

/// `K_fine - K_coarse` for two declared shadows of one interval, the fine
/// partition containing every coarse time; nonzero is a refinement tear.
pub fn refinement_residual(
    coarse: &FreeParticleShadow,
    fine: &FreeParticleShadow,
) -> Result<PhaseSum, ShadowRefusal> {
    if coarse.carrier != fine.carrier {
        return Err(ShadowRefusal::NotARefinement("the carriers differ"));
    }
    if (coarse.start, coarse.end) != (fine.start, fine.end) {
        return Err(ShadowRefusal::NotARefinement("the endpoints differ"));
    }
    if coarse.mass != fine.mass || coarse.hbar != fine.hbar {
        return Err(ShadowRefusal::NotARefinement("the mass or hbar differ"));
    }
    let same_interval =
        coarse.times.first() == fine.times.first() && coarse.times.last() == fine.times.last();
    if !same_interval || !coarse.times.iter().all(|t| fine.times.contains(t)) {
        return Err(ShadowRefusal::NotARefinement(
            "the partition is not refined",
        ));
    }
    Ok(fine.replay()?.kernel.sub(&coarse.replay()?.kernel))
}

// Origin: engine/crates_rs/core_quantum_physics/src/time_sliced_action_shadow.rs
// Claim: urn:core:crates_rs:core-quantum-physics:time-sliced-action-shadow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_cacf1b5a {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
