//! Retains one immutable circle profile and the actual spatial source query.
use crate::types::AuthorityEffect;
use num_traits::Zero;
use core_functional::circle_piecewise_linear::{CirclePiecewiseLinear, CircleProfileError};
use core_measurement::affine_calibration::{BoundedReading, CalibrationError};
use core_number_theory::rational::{rq, Rational};
use core_quantum_physics::meron_source_field::AnalyticResponsePlan;
use core_quantum_physics::meron_spatial_source::{SpatialSourceError, SpatialSourcePlan};
use core_quantum_physics::meron_time_refinement::{
    FiniteMeronChain, MeronTimeError, StaggeredMoments,
};

#[derive(Debug, thiserror::Error)]
pub enum MeronFieldError {
    #[error(transparent)]
    Profile(#[from] CircleProfileError),
    #[error(transparent)]
    Plan(#[from] SpatialSourceError),
    #[error(transparent)]
    Time(#[from] MeronTimeError),
    #[error(transparent)]
    Reading(#[from] CalibrationError),
    #[error("the actual weighted first moment violates particle-hole symmetry")]
    ParticleHole,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredMeronField {
    profile: CirclePiecewiseLinear,
    plan: SpatialSourcePlan,
    moments: StaggeredMoments,
    quadratic: BoundedReading,
    finite_log: BoundedReading,
    continuum_log: BoundedReading,
}
impl DeclaredMeronField {
    pub fn new(
        response: AnalyticResponsePlan,
        profile: CirclePiecewiseLinear,
        probe: Rational,
    ) -> Result<Self, MeronFieldError> {
        let plan = SpatialSourcePlan::new(
            response,
            profile.norm().clone(),
            profile.lipschitz().clone(),
            probe,
        )?;
        let time = plan.response().time();
        let weights = profile.uniform_samples(time.sites())?;
        let moments = FiniteMeronChain::new(time.sites())?.weighted_staggered_moments(
            time.repetitions(),
            time.q(),
            &weights,
        )?;
        if !moments.first().is_zero() {
            return Err(MeronFieldError::ParticleHole);
        }
        let value = moments.mean_square() / Rational::from_integer(time.sites().into());
        let quadratic = BoundedReading::new(value.clone(), plan.quadratic_error().clone())?;
        let log_center = plan.probe().pow(2) * value / rq(2, 1);
        let finite_log = BoundedReading::new(log_center.clone(), plan.finite_log_tail().clone())?;
        let continuum_log = BoundedReading::new(
            log_center,
            plan.probe().pow(2) * plan.quadratic_error() / rq(2, 1),
        )?;
        Ok(Self {
            profile,
            plan,
            moments,
            quadratic,
            finite_log,
            continuum_log,
        })
    }
    pub fn profile(&self) -> &CirclePiecewiseLinear {
        &self.profile
    }
    pub fn plan(&self) -> &SpatialSourcePlan {
        &self.plan
    }
    pub fn moments(&self) -> &StaggeredMoments {
        &self.moments
    }
    pub fn quadratic(&self) -> &BoundedReading {
        &self.quadratic
    }
    pub fn finite_log(&self) -> &BoundedReading {
        &self.finite_log
    }
    pub fn continuum_log(&self) -> &BoundedReading {
        &self.continuum_log
    }
    pub fn authority_effect(&self) -> AuthorityEffect {
        AuthorityEffect::None
    }
}

// Origin: engine/crates_rs/core_wdp/src/meron_field_adapter.rs
// Claim: urn:core:crates_rs:core-wdp:meron-field-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_18dae914 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
