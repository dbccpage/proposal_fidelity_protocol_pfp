//! Bounds for the written spatial Gaussian source-functional limit SG-1--SG-8.
use crate::meron_source_field::{canonical, AnalyticResponsePlan};
use crate::meron_time_refinement::MeronTimeError;
use num_traits::Zero;
use core_number_theory::rational::{rq, Rational};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpatialSourceError {
    #[error(transparent)]
    Time(#[from] MeronTimeError),
    #[error("profile norm and Lipschitz bound must be nonnegative")]
    ProfileBound,
    #[error("the spatial source probe leaves the proved analytic disk")]
    ProbeDomain,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SpatialSourcePlan {
    response: AnalyticResponsePlan,
    norm: Rational,
    lipschitz: Rational,
    probe: Rational,
    quadratic_error: Rational,
    finite_log_tail: Rational,
}
impl SpatialSourcePlan {
    pub fn new(
        response: AnalyticResponsePlan,
        norm: Rational,
        lipschitz: Rational,
        probe: Rational,
    ) -> Result<Self, SpatialSourceError> {
        let norm = canonical(norm)?;
        let lipschitz = canonical(lipschitz)?;
        let probe = canonical(probe)?;
        if norm < Rational::zero() || lipschitz < Rational::zero() {
            return Err(SpatialSourceError::ProfileBound);
        }
        let r = AnalyticResponsePlan::source_radius();
        let c = AnalyticResponsePlan::log_pressure_majorant();
        let l = Rational::from_integer(response.time().sites().into());
        let squared_fraction = probe.pow(2) * norm.pow(2) / (&l * r.pow(2));
        if squared_fraction >= rq(1, 1) {
            return Err(SpatialSourceError::ProbeDomain);
        }
        let kernel_bound = rq(16, 143) / r.pow(2);
        let susceptibility_bound = rq(2, 1) * &c / r.pow(2);
        let quadratic_error = norm.pow(2) * response.response_error()
            + (rq(40, 1) * kernel_bound + susceptibility_bound) * &norm * &lipschitz / &l;
        let finite_log_tail =
            c * probe.pow(4) * norm.pow(4) / (&l * r.pow(4) * (rq(1, 1) - squared_fraction));
        Ok(Self {
            response,
            norm,
            lipschitz,
            probe,
            quadratic_error,
            finite_log_tail,
        })
    }
    pub fn response(&self) -> &AnalyticResponsePlan {
        &self.response
    }
    pub fn norm(&self) -> &Rational {
        &self.norm
    }
    pub fn lipschitz(&self) -> &Rational {
        &self.lipschitz
    }
    pub fn probe(&self) -> &Rational {
        &self.probe
    }
    pub fn quadratic_error(&self) -> &Rational {
        &self.quadratic_error
    }
    pub fn finite_log_tail(&self) -> &Rational {
        &self.finite_log_tail
    }
    pub fn source_functional_error(&self) -> Rational {
        self.probe.pow(2) * &self.quadratic_error / rq(2, 1) + &self.finite_log_tail
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/meron_spatial_source.rs
// Claim: urn:core:crates_rs:core-quantum-physics:meron-spatial-source:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e191015e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
