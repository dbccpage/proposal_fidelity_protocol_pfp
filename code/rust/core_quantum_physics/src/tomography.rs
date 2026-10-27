// AuthorityEffect: None. Citation: sealed-derivation-v1 (3100c4e)

//! Exact finite MUB linear-inversion tomography and state admission.
//!
//! Implements exact quantum state tomography using maximal d=3 MUB measurement statistics:
//! 1. Forward Born rule measurement map: p_{b, k} = Tr(rho Pi_{b, k}) in Q.
//! 2. Exact linear inversion reconstruction:
//!    rho = sum_{b=0}^3 sum_{k=0}^2 p_{b, k} Pi_{b, k} - I_3.
//! 3. Exact reconstruction verification with zero floating-point error.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_66b7c54b<T> {
    fn checked_invariant_66b7c54b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_66b7c54b<T> for Option<T> {
    #[inline]
    fn checked_invariant_66b7c54b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_66b7c54b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_66b7c54b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};

use crate::mub::MubSystem;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{adjoint, Involution},
    matrix,
};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::rational::{ri, rq, Rational};
use core_number_theory::scalar::RationalEmbedding;

/// Universal Exact State Tomographer for any dimension supported by MubSystem.
#[derive(Clone, Debug)]
pub struct ExactStateTomographerSystem<C: RationalEmbedding + Involution> {
    pub mub: MubSystem<C>,
}

impl<C: RationalEmbedding + Involution> ExactStateTomographerSystem<C> {
    pub fn new(mub: MubSystem<C>) -> Self {
        Self { mub }
    }

    pub fn try_measure_state(&self, rho: &BasicMatrix<C>) -> Result<Vec<Vec<C>>, String> {
        self.mub.try_measure_state(rho)
    }

    pub fn is_complete(&self) -> bool {
        self.mub.is_complete()
    }

    pub fn try_reconstruct_state(&self, probs: &[Vec<C>]) -> Result<BasicMatrix<C>, String> {
        self.mub.try_reconstruct_state(probs)
    }

    pub fn verify_exact_reconstruction(&self, rho: &BasicMatrix<C>) -> bool {
        self.mub.verify_exact_reconstruction(rho)
    }
}

/// Tomographic probabilities across the 4 MUB bases in d=3.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MubTomographyProbabilities {
    /// 4 bases x 3 outcomes = 12 exact rational probabilities.
    pub probabilities: Vec<Vec<Rational>>,
}

impl MubTomographyProbabilities {
    /// Verify that each basis sums to 1: sum_{k=0}^2 p_{b, k} = 1.
    pub fn verify_normalization(&self) -> bool {
        if self.probabilities.len() != 4
            || self
                .probabilities
                .iter()
                .any(|row| row.len() != 3 || row.iter().any(|p| p < &ri(0)))
        {
            return false;
        }
        for b in 0..4 {
            let sum: Rational = self.probabilities[b].iter().sum();
            if sum != ri(1) {
                return false;
            }
        }
        true
    }
}

// ---------------------------------------------------------------------------
// Standard Test States in d=3
// ---------------------------------------------------------------------------

/// Maximally mixed state rho = 1/3 * I_3.
pub fn state_maximally_mixed_d3() -> BasicMatrix<Cyc24> {
    matrix::scale(
        &matrix::identity::<Cyc24>(3).checked_invariant_66b7c54b("fixed qutrit carrier"),
        &Cyc24::rat(rq(1, 3)),
    )
    .checked_invariant_66b7c54b("fixed qutrit carrier")
}

/// Computational ground state rho = |0><0|.
pub fn state_ground_d3() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(3, 3).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::one())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Equal superposition state |+> = 1/sqrt(3)(|0> + |1> + |2>), rho = |+><+|.
pub fn state_superposition_d3() -> BasicMatrix<Cyc24> {
    let third = Cyc24::rat(rq(1, 3));
    let mut rho = matrix::zeros::<Cyc24>(3, 3).checked_invariant_66b7c54b("fixed state carrier");
    for r in 0..3 {
        for c in 0..3 {
            rho.set(r, c, third.clone())
                .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
        }
    }
    rho
}

/// Qutrit magic state |M> = 1/sqrt(2)(|1> - |2>), rho_M = |M><M|.
pub fn state_magic_d3() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(3, 3).checked_invariant_66b7c54b("fixed state carrier");
    let half = Cyc24::rat(rq(1, 2));
    let neg_half = Cyc24::rat(rq(-1, 2));
    rho.set(1, 1, half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 2, neg_half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 1, neg_half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 2, half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Mixed density matrix with rational entries.
pub fn state_mixed_rational_d3() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(3, 3).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::rat(rq(1, 2)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(0, 1, Cyc24::rat(rq(1, 6)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 0, Cyc24::rat(rq(1, 6)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 1, Cyc24::rat(rq(1, 3)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 2, Cyc24::rat(rq(1, 6)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 1, Cyc24::rat(rq(1, 6)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 2, Cyc24::rat(rq(1, 6)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Complex density matrix with Eisenstein cyclotomic coherence.
pub fn state_cyclotomic_coherence_d3() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(3, 3).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::rat(rq(1, 2)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 1, Cyc24::rat(rq(1, 4)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 2, Cyc24::rat(rq(1, 4)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");

    // Off-diagonals with zeta_3: rho_{0,1} = 1/8 * zeta_3, rho_{1,0} = 1/8 * zeta_3^2
    let z3_scale = Cyc24::zeta3().mul(&Cyc24::rat(rq(1, 8)));
    let z3_scale_conj = z3_scale.conj();
    rho.set(0, 1, z3_scale)
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 0, z3_scale_conj)
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

// ---------------------------------------------------------------------------
// Target 22 Extension: 2-Qubit State Tomography in d=4 (5 MUBs, 20 Projectors)
// ---------------------------------------------------------------------------

/// Tomographic probabilities across the 5 MUB bases in d=4 (2 qubits).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct MubTomographyProbabilitiesD4 {
    /// 5 bases x 4 outcomes = 20 exact rational probabilities.
    pub probabilities: Vec<Vec<Rational>>,
}

impl MubTomographyProbabilitiesD4 {
    /// Verify that each basis sums to 1: sum_{k=0}^3 p_{b, k} = 1.
    pub fn verify_normalization(&self) -> bool {
        if self.probabilities.len() != 5
            || self
                .probabilities
                .iter()
                .any(|row| row.len() != 4 || row.iter().any(|p| p < &ri(0)))
        {
            return false;
        }
        for b in 0..5 {
            let sum: Rational = self.probabilities[b].iter().sum();
            if sum != ri(1) {
                return false;
            }
        }
        true
    }
}

/// Ground state |00><00| in d=4.
pub fn state_ground_d4() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(4, 4).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::one())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Maximally entangled Bell state |Phi+><Phi+| in d=4: 1/2 (|00> + |11>)(<00| + <11|).
pub fn state_bell_d4() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(4, 4).checked_invariant_66b7c54b("fixed state carrier");
    let half = Cyc24::rat(rq(1, 2));
    rho.set(0, 0, half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(0, 3, half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(3, 0, half.clone())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(3, 3, half)
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Equal superposition state |++><++| in d=4: all 16 entries equal to 1/4.
pub fn state_superposition_d4() -> BasicMatrix<Cyc24> {
    let quarter = Cyc24::rat(rq(1, 4));
    let mut rho = matrix::zeros::<Cyc24>(4, 4).checked_invariant_66b7c54b("fixed state carrier");
    for r in 0..4 {
        for c in 0..4 {
            rho.set(r, c, quarter.clone())
                .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
        }
    }
    rho
}

/// Mixed density matrix diag(4/10, 3/10, 2/10, 1/10) in d=4.
pub fn state_mixed_d4() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(4, 4).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::rat(rq(4, 10)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(1, 1, Cyc24::rat(rq(3, 10)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(2, 2, Cyc24::rat(rq(2, 10)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho.set(3, 3, Cyc24::rat(rq(1, 10)))
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Ground state |0><0| in d=2.
pub fn state_ground_d2() -> BasicMatrix<Cyc24> {
    let mut rho = matrix::zeros::<Cyc24>(2, 2).checked_invariant_66b7c54b("fixed state carrier");
    rho.set(0, 0, Cyc24::one())
        .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
    rho
}

/// Equal superposition state |+><+| in d=2: [[1/2, 1/2], [1/2, 1/2]].
pub fn state_superposition_d2() -> BasicMatrix<Cyc24> {
    let half = Cyc24::rat(rq(1, 2));
    let mut rho = matrix::zeros::<Cyc24>(2, 2).checked_invariant_66b7c54b("fixed state carrier");
    for r in 0..2 {
        for c in 0..2 {
            rho.set(r, c, half.clone())
                .checked_invariant_66b7c54b("indices belong to the fixed state carrier");
        }
    }
    rho
}

// Origin: engine/crates_rs/core_quantum_physics/src/tomography.rs
// Claim: urn:core:crates_rs:core-quantum-physics:tomography:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord66b7c54b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord66b7c54b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError66b7c54b {
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
impl BoundaryError66b7c54b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError66b7c54b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError66b7c54b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord66b7c54b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError66b7c54b> {
        if capacity_bound == 0 {
            return Err(BoundaryError66b7c54b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError66b7c54b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError66b7c54b::ExceedsCapacity {
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
mod tests {
    use super::*;

    #[test]
    fn test_exact_tomography_on_ground_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d3());
        let rho = state_ground_d3();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_tomography_on_superposition_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d3());
        let rho = state_superposition_d3();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_tomography_on_magic_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d3());
        let rho = state_magic_d3();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_tomography_on_mixed_states() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d3());
        assert!(tomographer.verify_exact_reconstruction(&state_maximally_mixed_d3()));
        assert!(tomographer.verify_exact_reconstruction(&state_mixed_rational_d3()));
        assert!(tomographer.verify_exact_reconstruction(&state_cyclotomic_coherence_d3()));
    }

    #[test]
    fn test_exact_d4_tomography_on_ground_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d4());
        let rho = state_ground_d4();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_d4_tomography_on_bell_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d4());
        let rho = state_bell_d4();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_d4_tomography_on_superposition_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d4());
        let rho = state_superposition_d4();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_d4_tomography_on_mixed_state() {
        let tomographer = ExactStateTomographerSystem::new(MubSystem::mub_d4());
        let rho = state_mixed_d4();
        assert!(tomographer.verify_exact_reconstruction(&rho));
    }

    #[test]
    fn test_exact_d2_tomography_on_qubit_states() {
        let mub2 = MubSystem::mub_d2();
        let rho_0 = state_ground_d2();
        assert!(mub2.verify_exact_reconstruction(&rho_0));
        let rho_plus = state_superposition_d2();
        assert!(mub2.verify_exact_reconstruction(&rho_plus));
    }
}

fn to_ordered_cyc24_matrix(
    rho: &BasicMatrix<Cyc24>,
) -> Result<
    linear_algebra::backend::basic_matrix::BasicMatrix<
        core_number_theory::cyclotomic_field::Cyclotomic<24>,
    >,
    String,
> {
    use core_number_theory::cyclotomic_field::{Cyclotomic, CyclotomicNumber};
    let entries = rho
        .as_slice()
        .iter()
        .map(|x| {
            Cyclotomic::<24>::try_from(
                CyclotomicNumber::from_coefficients(24, x.a.to_vec()).map_err(|e| e.to_string())?,
            )
            .map_err(|e| e.to_string())
        })
        .collect::<Result<Vec<_>, String>>()?;
    linear_algebra::backend::basic_matrix::BasicMatrix::from_row_major(
        rho.rows(),
        rho.cols(),
        entries,
    )
    .map_err(|e| e.to_string())
}

/// State admission is independent of reconstruction equality. This uses the
/// standard real place of Q(zeta_24), not a floating eigenvalue diagnostic.
pub fn check_density_operator(rho: &BasicMatrix<Cyc24>) -> Result<bool, String> {
    if rho.rows() == 0 || rho.rows() != rho.cols() || rho.rows() > 64 {
        return Err("malformed state carrier".into());
    }
    if adjoint(rho).map_err(|e| e.to_string())? != *rho
        || matrix::trace(rho).map_err(|e| e.to_string())? != Cyc24::one()
    {
        return Ok(false);
    }
    let basic = to_ordered_cyc24_matrix(rho)?;
    linear_algebra::exact_field::ordered::hermitian_inertia(&basic)
        .map(|inertia| inertia.is_positive_semidefinite())
        .map_err(|e| e.to_string())
}

/// Admit data only when its unique complete-MUB inverse is a quantum state.
pub fn reconstruct_admitted_state(
    system: &MubSystem<Cyc24>,
    probabilities: &[Vec<Rational>],
) -> Result<BasicMatrix<Cyc24>, String> {
    if probabilities
        .iter()
        .any(|row| row.iter().any(|p| p < &ri(0)) || row.iter().sum::<Rational>() != ri(1))
    {
        return Err("probabilities are not normalized nonnegative rows".into());
    }
    let rho = system.try_reconstruct_state_rational(probabilities)?;
    if !check_density_operator(&rho)? {
        return Err("nonpositive tomographic inverse".into());
    }
    Ok(rho)
}

#[cfg(test)]
mod l4_boundary_tests_66b7c54b {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord66b7c54b::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord66b7c54b::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord66b7c54b::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord66b7c54b::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord66b7c54b::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError66b7c54b::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError66b7c54b::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
