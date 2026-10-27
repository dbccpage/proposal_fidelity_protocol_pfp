//! Exact finite scattering matrices over Q(i).
//!
//! A Hermitian reaction matrix K gives S = (I + iK)(I - iK)^(-1).
//! Construction replays S†S = I using the shared exact linear algebra.
//! Modular S-data belongs to core_fusion_categories::modular::ModularData.
//! This is finite channel scattering at a declared energy, not an asymptotic
//! continuum scattering construction. AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{elimination, involution, matrix, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;

pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; exact finite scattering.";

/// Dense exact channel operations are admitted only on this finite carrier.
pub const MAX_SCATTERING_CHANNELS: usize = 128;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ScatteringError {
    #[error("at least one scattering channel is required")]
    Empty,
    #[error("scattering carrier {requested} exceeds the supported limit {maximum}")]
    ChannelLimit { requested: usize, maximum: usize },
    #[error("the reaction matrix must be Hermitian")]
    NonHermitian,
    #[error("the scattering matrix must be unitary")]
    NonUnitary,
    #[error(transparent)]
    Algebra(#[from] ExactFieldError),
}

/// A validated unitary scattering matrix; its entries cannot be mutated.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SMatrix {
    operator: BasicMatrix<GaussianRat>,
}

impl SMatrix {
    fn check_carrier(operator: &BasicMatrix<GaussianRat>) -> Result<(), ScatteringError> {
        if operator.rows() == 0 || operator.cols() == 0 {
            return Err(ScatteringError::Empty);
        }
        let requested = operator.rows().max(operator.cols());
        if requested > MAX_SCATTERING_CHANNELS {
            return Err(ScatteringError::ChannelLimit {
                requested,
                maximum: MAX_SCATTERING_CHANNELS,
            });
        }
        Ok(())
    }

    pub fn from_unitary(operator: BasicMatrix<GaussianRat>) -> Result<Self, ScatteringError> {
        Self::check_carrier(&operator)?;
        if !involution::is_unitary(&operator)? {
            return Err(ScatteringError::NonUnitary);
        }
        Ok(Self { operator })
    }

    /// Cayley transform with outgoing-wave convention S=(I+iK)/(I-iK).
    pub fn from_k(reaction: &BasicMatrix<GaussianRat>) -> Result<Self, ScatteringError> {
        Self::check_carrier(reaction)?;
        if !involution::is_hermitian(reaction)? {
            return Err(ScatteringError::NonHermitian);
        }
        let identity = matrix::identity(reaction.rows())?;
        let ik = matrix::scale(reaction, &GaussianRat::i())?;
        let numerator = matrix::add(&identity, &ik)?;
        let denominator = matrix::sub(&identity, &ik)?;
        Self::from_unitary(matrix::multiply(
            &numerator,
            &elimination::inverse(&denominator)?,
        )?)
    }

    pub fn operator(&self) -> &BasicMatrix<GaussianRat> {
        &self.operator
    }

    pub fn channels(&self) -> usize {
        self.operator.rows()
    }

    /// T=(S-I)/(2i), with optical theorem T-T†=2i T†T.
    pub fn transition_operator(&self) -> Result<BasicMatrix<GaussianRat>, ScatteringError> {
        use core_number_theory::rational::{ri, rq};
        let difference = matrix::sub(&self.operator, &matrix::identity(self.channels())?)?;
        Ok(matrix::scale(
            &difference,
            &GaussianRat {
                re: ri(0),
                im: rq(-1, 2),
            },
        )?)
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/s_matrix.rs
// Claim: urn:core:crates_rs:core-quantum-physics:s-matrix:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::ri;

    fn q(n: i64) -> GaussianRat {
        GaussianRat::from_rational(ri(n))
    }

    #[test]
    fn cayley_scalar_pins_the_scattering_sign_convention() {
        let k = matrix::from_rows(vec![vec![q(1)]]).unwrap();
        let s = SMatrix::from_k(&k).unwrap();
        assert_eq!(s.operator().get(0, 0).unwrap(), GaussianRat::i());
        assert_eq!(s.channels(), 1);
    }

    #[test]
    fn coupled_channels_are_unitary_and_obey_the_optical_theorem() {
        let k = matrix::from_rows(vec![
            vec![q(1), GaussianRat::i()],
            vec![GaussianRat::i().neg(), q(-2)],
        ])
        .unwrap();
        let s = SMatrix::from_k(&k).unwrap();
        assert!(involution::is_unitary(s.operator()).unwrap());
        let t = s.transition_operator().unwrap();
        let td = involution::adjoint(&t).unwrap();
        let lhs = matrix::sub(&t, &td).unwrap();
        let rhs = matrix::scale(
            &matrix::multiply(&td, &t).unwrap(),
            &GaussianRat::i().scale_rat(&ri(2)),
        )
        .unwrap();
        assert_eq!(lhs, rhs);
    }

    #[test]
    fn malformed_and_nonphysical_scattering_inputs_are_refused() {
        assert_eq!(
            SMatrix::from_k(&matrix::identity(0).unwrap()),
            Err(ScatteringError::Empty)
        );
        let k = matrix::from_rows(vec![vec![GaussianRat::i()]]).unwrap();
        assert_eq!(SMatrix::from_k(&k), Err(ScatteringError::NonHermitian));
        assert_eq!(
            SMatrix::from_unitary(matrix::from_rows(vec![vec![q(2)]]).unwrap()),
            Err(ScatteringError::NonUnitary)
        );
        assert!(SMatrix::from_k(&matrix::from_rows(vec![vec![q(1), q(2)]]).unwrap()).is_err());
        let oversized = matrix::from_rows(vec![vec![q(0); MAX_SCATTERING_CHANNELS + 1]]).unwrap();
        let expected = Err(ScatteringError::ChannelLimit {
            requested: MAX_SCATTERING_CHANNELS + 1,
            maximum: MAX_SCATTERING_CHANNELS,
        });
        assert_eq!(SMatrix::from_k(&oversized), expected);
        assert_eq!(SMatrix::from_unitary(oversized), expected);
    }

    #[test]
    fn new_and_fence() {
        let s = SMatrix::from_k(&matrix::from_rows(vec![vec![q(0)]]).unwrap()).unwrap();
        assert_eq!(s.operator(), &matrix::identity(1).unwrap());
        assert!(SMatrix::authority_fence().contains("AuthorityEffect None"));
    }
}
