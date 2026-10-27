//! Finite channel amplitudes and resolvent/Born identities at a declared energy.
//! T=(S-I)/(2i) follows the convention of `s_matrix`; no on-shell limit is taken.
//! AuthorityEffect: None. Not PROVED. Not GlobalGreen.
use crate::s_matrix::{SMatrix, ScatteringError};
use linear_algebra::{
    backend::basic_matrix::BasicMatrix,
    exact_field::{elimination, involution, matrix},
};
use num_traits::Signed;
use core_number_theory::{
    cyclotomic::GaussianRat,
    rational::{rq, Rational},
};
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite scattering amplitudes.";
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AmplitudeError {
    #[error(transparent)]
    Scattering(#[from] ScatteringError),
    #[error("incoming or outgoing channel is outside the carrier")]
    Channel,
    #[error("Hamiltonian is malformed or not Hermitian")]
    Hamiltonian,
    #[error("request exceeds dimension sixteen or Born order 256")]
    Budget,
    #[error("exact matrix operation refused: {0}")]
    Matrix(String),
}
fn err(e: impl std::fmt::Display) -> AmplitudeError {
    AmplitudeError::Matrix(e.to_string())
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScatteringAmplitude {
    s: SMatrix,
}
impl ScatteringAmplitude {
    pub fn from_s(s: SMatrix) -> Self {
        Self { s }
    }
    pub fn amplitude(
        &self,
        incoming: usize,
        outgoing: usize,
    ) -> Result<GaussianRat, AmplitudeError> {
        if incoming >= self.s.channels() || outgoing >= self.s.channels() {
            return Err(AmplitudeError::Channel);
        }
        Ok(self
            .s
            .operator()
            .get_ref(outgoing, incoming)
            .map_err(err)?
            .clone())
    }
    pub fn probability(
        &self,
        incoming: usize,
        outgoing: usize,
    ) -> Result<Rational, AmplitudeError> {
        let a = self.amplitude(incoming, outgoing)?;
        Ok(&a.re * &a.re + &a.im * &a.im)
    }
    pub fn optical_theorem_defect(&self) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        let t = self.s.transition_operator()?;
        let td = involution::adjoint(&t).map_err(err)?;
        let lhs = matrix::sub(&t, &td).map_err(err)?;
        let rhs = matrix::scale(
            &matrix::multiply(&td, &t).map_err(err)?,
            &(GaussianRat::i() * GaussianRat::from_rational(rq(2, 1))),
        )
        .map_err(err)?;
        matrix::sub(&lhs, &rhs).map_err(err)
    }
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ScatteringProblem {
    h0: BasicMatrix<GaussianRat>,
    v: BasicMatrix<GaussianRat>,
}
impl ScatteringProblem {
    pub fn new(h0: Vec<Rational>, v: BasicMatrix<GaussianRat>) -> Result<Self, AmplitudeError> {
        let n = h0.len();
        if n == 0 || n > 16 {
            return Err(AmplitudeError::Budget);
        }
        if v.shape() != (n, n) || !involution::is_hermitian(&v).map_err(err)? {
            return Err(AmplitudeError::Hamiltonian);
        }
        let diagonal = matrix::diagonal(
            &h0.into_iter()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )
        .map_err(err)?;
        Ok(Self { h0: diagonal, v })
    }
    fn inverse_at(
        &self,
        z: &GaussianRat,
        h: &BasicMatrix<GaussianRat>,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        let shifted = matrix::sub(
            &matrix::scale(&matrix::identity(h.rows()).map_err(err)?, z).map_err(err)?,
            h,
        )
        .map_err(err)?;
        elimination::inverse(&shifted).map_err(err)
    }
    pub fn free_resolvent(
        &self,
        z: &GaussianRat,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        self.inverse_at(z, &self.h0)
    }
    pub fn resolvent(&self, z: &GaussianRat) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        self.inverse_at(z, &matrix::add(&self.h0, &self.v).map_err(err)?)
    }
    pub fn t_matrix(&self, z: &GaussianRat) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        let kernel = matrix::multiply(&self.free_resolvent(z)?, &self.v).map_err(err)?;
        matrix::multiply(
            &self.v,
            &elimination::inverse(
                &matrix::sub(&matrix::identity(self.h0.rows()).map_err(err)?, &kernel)
                    .map_err(err)?,
            )
            .map_err(err)?,
        )
        .map_err(err)
    }
    /// Sum k=0..order V(G0 V)^k, with the same ordering as Lippmann-Schwinger.
    pub fn born_series(
        &self,
        z: &GaussianRat,
        order: usize,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        if order > 256 {
            return Err(AmplitudeError::Budget);
        }
        let kernel = matrix::multiply(&self.free_resolvent(z)?, &self.v).map_err(err)?;
        let mut power = matrix::identity(self.h0.rows()).map_err(err)?;
        let mut result = self.v.clone();
        for _ in 0..order {
            power = matrix::multiply(&power, &kernel).map_err(err)?;
            result = matrix::add(&result, &matrix::multiply(&self.v, &power).map_err(err)?)
                .map_err(err)?;
        }
        Ok(result)
    }
    pub fn lippmann_schwinger_defect(
        &self,
        z: &GaussianRat,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        let t = self.t_matrix(z)?;
        let correction = matrix::multiply(
            &matrix::multiply(&self.v, &self.free_resolvent(z)?).map_err(err)?,
            &t,
        )
        .map_err(err)?;
        matrix::sub(&matrix::sub(&t, &self.v).map_err(err)?, &correction).map_err(err)
    }
    pub fn resolvent_identity_defect(
        &self,
        z: &GaussianRat,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        let g = self.resolvent(z)?;
        let g0 = self.free_resolvent(z)?;
        let correction =
            matrix::multiply(&matrix::multiply(&g0, &self.v).map_err(err)?, &g).map_err(err)?;
        matrix::sub(&matrix::sub(&g, &g0).map_err(err)?, &correction).map_err(err)
    }
    pub fn born_remainder(
        &self,
        z: &GaussianRat,
        order: usize,
    ) -> Result<BasicMatrix<GaussianRat>, AmplitudeError> {
        if order > 256 {
            return Err(AmplitudeError::Budget);
        }
        let kernel = matrix::multiply(&self.free_resolvent(z)?, &self.v).map_err(err)?;
        let inverse = elimination::inverse(
            &matrix::sub(&matrix::identity(self.h0.rows()).map_err(err)?, &kernel).map_err(err)?,
        )
        .map_err(err)?;
        let power = matrix::power(&kernel, (order + 1) as u64).map_err(err)?;
        matrix::multiply(&matrix::multiply(&self.v, &power).map_err(err)?, &inverse).map_err(err)
    }
    /// A rational upper bound on the absolute row-sum norm, using |re|+|im|.
    pub fn born_convergence_sufficient(&self, z: &GaussianRat) -> Result<bool, AmplitudeError> {
        let kernel = matrix::multiply(&self.free_resolvent(z)?, &self.v).map_err(err)?;
        for i in 0..kernel.rows() {
            let sum = (0..kernel.cols()).try_fold(rq(0, 1), |a, j| {
                let x = kernel.get_ref(i, j).map_err(err)?;
                Ok::<_, AmplitudeError>(a + x.re.abs() + x.im.abs())
            })?;
            if sum >= rq(1, 1) {
                return Ok(false);
            }
        }
        Ok(true)
    }
}
// Origin: engine/crates_rs/core_quantum_physics/src/scattering_amplitude.rs
// Claim: urn:core:crates_rs:core-quantum-physics:scattering-amplitude:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use num_traits::Zero;
    fn q(n: i64) -> GaussianRat {
        GaussianRat::from_rational(rq(n, 1))
    }
    #[test]
    fn scattering_optical_theorem_and_channel_probabilities_follow_unitarity() {
        let s = SMatrix::from_k(
            &matrix::from_rows(vec![
                vec![q(0), GaussianRat::from_rational(rq(1, 2))],
                vec![GaussianRat::from_rational(rq(1, 2)), q(0)],
            ])
            .unwrap(),
        )
        .unwrap();
        let a = ScatteringAmplitude::from_s(s);
        assert!(a
            .optical_theorem_defect()
            .unwrap()
            .as_slice()
            .iter()
            .all(|x| x.re.is_zero() && x.im.is_zero()));
        assert_eq!(a.probability(0, 0).unwrap(), rq(9, 25));
        assert_eq!(a.probability(0, 1).unwrap(), rq(16, 25));
        assert!(a.amplitude(2, 0).is_err());
    }
    #[test]
    fn lippmann_schwinger_resolvent_and_born_remainder_are_exact() {
        let v = matrix::from_rows(vec![
            vec![q(0), GaussianRat::from_rational(rq(1, 2))],
            vec![GaussianRat::from_rational(rq(1, 2)), q(0)],
        ])
        .unwrap();
        let p = ScatteringProblem::new(vec![rq(1, 1), rq(2, 1)], v).unwrap();
        let z = q(4);
        assert!(p
            .lippmann_schwinger_defect(&z)
            .unwrap()
            .as_slice()
            .iter()
            .all(|x| x.re.is_zero() && x.im.is_zero()));
        assert!(p
            .resolvent_identity_defect(&z)
            .unwrap()
            .as_slice()
            .iter()
            .all(|x| x.re.is_zero() && x.im.is_zero()));
        for order in [0, 1, 4] {
            assert_eq!(
                matrix::sub(&p.t_matrix(&z).unwrap(), &p.born_series(&z, order).unwrap()).unwrap(),
                p.born_remainder(&z, order).unwrap()
            );
        }
        assert!(p.born_convergence_sufficient(&z).unwrap());
        assert!(p.free_resolvent(&q(1)).is_err());
    }
}
