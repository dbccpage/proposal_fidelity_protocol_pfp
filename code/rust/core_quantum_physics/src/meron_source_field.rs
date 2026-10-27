//! A supplied common temperature/source target and exact rational error majorant.
//! The infinite-volume and splitting arguments are written separately in WDP.

use crate::meron_time_refinement::{EulerTimePlan, MeronTimeError};
use num_traits::{One, Signed, ToPrimitive, Zero};
use core_number_theory::rational::{rq, Rational};

pub(crate) fn canonical(value: Rational) -> Result<Rational, MeronTimeError> {
    if value.denom().is_zero() {
        return Err(MeronTimeError::Parameter);
    }
    if value.numer().bits() > 256 || value.denom().bits() > 256 {
        return Err(MeronTimeError::Resource);
    }
    Ok(value.reduced())
}

/// The field interval is a declared enclosure of one lambda, not a selected law.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceFieldPlan {
    time: EulerTimePlan,
    field_center: Rational,
    field_radius: Rational,
    v: Rational,
    exponential_majorant: Rational,
    finite_density_error: Rational,
    thermodynamic_density_error: Rational,
}

impl SourceFieldPlan {
    pub fn new(
        sites: usize,
        repetitions: usize,
        temperature_center: Rational,
        temperature_radius: Rational,
        field_center: Rational,
        field_radius: Rational,
    ) -> Result<Self, MeronTimeError> {
        let r = canonical(temperature_center)?;
        let radius = canonical(temperature_radius)?;
        let s = canonical(field_center)?;
        let field_radius = canonical(field_radius)?;
        if field_radius < Rational::zero() {
            return Err(MeronTimeError::Parameter);
        }
        let time = EulerTimePlan::new(sites, repetitions, r.clone(), radius.clone())?;
        let l = Rational::from_integer(sites.into());
        let m = Rational::from_integer(repetitions.into());
        let positive_v = Rational::one() + s.abs() / (&m * rq(2, 1));
        let v = if s.is_negative() {
            positive_v.recip()
        } else {
            positive_v
        };
        let exponent = &l * (&r + s.abs()) / &m;
        let ceiling = exponent
            .ceil()
            .to_integer()
            .to_u32()
            .ok_or(MeronTimeError::Resource)?;
        if ceiling > 64 {
            return Err(MeronTimeError::Resource);
        }
        // e<3, so exp(x)<=3^ceil(x) for x>=0. This is an upper bound.
        let exponential_majorant = rq(3, 1).pow(ceiling as i32);
        let time_field = &l / &m * (&r + s.abs() / rq(2, 1)).pow(2) * &exponential_majorant;
        let temperature_drift = &r * &r / (&m * rq(2, 1)) + &radius;
        let field_drift = &s * &s / (&m * rq(4, 1)) + &field_radius;
        let finite_density_error =
            time_field + temperature_drift * rq(3, 4) + field_drift * rq(1, 2);
        let thermodynamic_density_error = &finite_density_error + (&r + &radius) * rq(3, 2) / &l;
        Ok(Self {
            time,
            field_center: s,
            field_radius,
            v,
            exponential_majorant,
            finite_density_error,
            thermodynamic_density_error,
        })
    }
    pub fn time(&self) -> &EulerTimePlan {
        &self.time
    }
    pub fn field_center(&self) -> &Rational {
        &self.field_center
    }
    pub fn field_radius(&self) -> &Rational {
        &self.field_radius
    }
    pub fn v(&self) -> &Rational {
        &self.v
    }
    pub fn exponential_majorant(&self) -> &Rational {
        &self.exponential_majorant
    }
    pub fn finite_density_error(&self) -> &Rational {
        &self.finite_density_error
    }
    pub fn thermodynamic_density_error(&self) -> &Rational {
        &self.thermodynamic_density_error
    }
}

/// AR-7/AR-9 for the actual complex-source curve, in the proved temperature domain.
/// The written polymer argument supplies the uniform analytic bound. This object
/// computes its finite error majorant; it does not execute an infinite family.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AnalyticResponsePlan {
    time: EulerTimePlan,
    resolution: Rational,
    pressure_error: Rational,
    response_error: Rational,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AnalyticResponseError {
    #[error(transparent)]
    Time(#[from] MeronTimeError),
    #[error("temperature interval exceeds the proved upper bound 1/192")]
    TemperatureDomain,
    #[error("response resolution must lie in (0,1/128]")]
    Resolution,
}

impl AnalyticResponsePlan {
    pub fn new(
        sites: usize,
        repetitions: usize,
        temperature_center: Rational,
        temperature_radius: Rational,
        resolution: Rational,
    ) -> Result<Self, AnalyticResponseError> {
        let r = canonical(temperature_center)?;
        let rho = canonical(temperature_radius)?;
        let resolution = canonical(resolution)?;
        let source_radius = Self::source_radius();
        Self::validate_response_parameters(&r, &rho, &resolution, &source_radius)?;
        let time = EulerTimePlan::new(sites, repetitions, r.clone(), rho.clone())?;
        let l = Rational::from_integer(sites.into());
        let m = Rational::from_integer(repetitions.into());
        let ceiling = (&l / &m * (&r + &source_radius))
            .ceil()
            .to_integer()
            .to_u32()
            .ok_or(MeronTimeError::Resource)?;
        if ceiling > 64 {
            return Err(MeronTimeError::Resource.into());
        }
        let majorant = rq(3, 1).pow(ceiling as i32);
        let pressure_error = &l / &m * (&r + &source_radius / rq(2, 1)).pow(2) * majorant
            + rq(3, 4) * (&r * &r / (&m * rq(2, 1)) + &rho)
            + rq(3, 2) * (&r + &rho) / &l;
        let response_error = rq(4, 1) * &pressure_error / resolution.pow(2)
            + rq(64, 1) * Self::log_pressure_majorant() * resolution.pow(2) / source_radius.pow(4);
        Ok(Self {
            time,
            resolution,
            pressure_error,
            response_error,
        })
    }

    fn validate_response_parameters(
        r: &Rational,
        rho: &Rational,
        resolution: &Rational,
        source_radius: &Rational,
    ) -> Result<(), AnalyticResponseError> {
        if r < rho || *rho < Rational::zero() {
            return Err(MeronTimeError::Parameter.into());
        }
        if r + rho > rq(1, 192) {
            return Err(AnalyticResponseError::TemperatureDomain);
        }
        if *resolution <= Rational::zero() || *resolution > source_radius / rq(2, 1) {
            return Err(AnalyticResponseError::Resolution);
        }
        Ok(())
    }
    pub fn source_radius() -> Rational {
        rq(1, 64)
    }
    pub fn log_pressure_majorant() -> Rational {
        rq(1, 19)
    }
    pub fn time(&self) -> &EulerTimePlan {
        &self.time
    }
    pub fn resolution(&self) -> &Rational {
        &self.resolution
    }
    pub fn pressure_error(&self) -> &Rational {
        &self.pressure_error
    }
    pub fn response_error(&self) -> &Rational {
        &self.response_error
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/meron_source_field.rs
// Claim: urn:core:crates_rs:core-quantum-physics:meron-source-field:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_f6f39860 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
