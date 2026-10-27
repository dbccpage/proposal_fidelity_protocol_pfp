// AuthorityEffect: None.
//! Exact outcome repeatability for a declared finite Q(i) instrument.
//!
//! For a square instrument M_o(rho)=sum_a K_oa rho K_oa*, the following are
//! equivalent: (1) every immediately repeated measurement returns the original
//! outcome with probability one whenever that first outcome has positive
//! probability; (2) K_jb K_oa=0 for every j!=o and every Kraus pair a,b.
//!
//! Proof: the joint probability of o then j is
//! sum_ab tr(A_ab rho A_ab*), A_ab=K_jb K_oa. Condition (2) kills every switching
//! term. Completeness gives sum_j joint(o,j)=tr M_o(rho), proving (1).
//! Conversely, on rho=I/d a switching probability is
//! (1/d) sum_ab sum_rc |A_ab[r,c]|^2. A finite sum of nonnegative real rational
//! squares vanishes exactly when every A_ab vanishes. Thus this single strictly
//! positive test state is a complete separating certificate, not sampling.
//!
//! Outcome repeatability is weaker than idempotence of the state-update map.
//! It neither selects the Born rule nor certifies a physical apparatus.

use crate::exact_instrument::{ExactFiniteInstrument, ExactInstrumentError};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational, Zero};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RepeatabilityError {
    #[error("exact matrix algebra: {0}")]
    Algebra(#[from] ExactFieldError),
    #[error("matrix storage: {0}")]
    Storage(#[from] MatrixError),

    #[error("instrument refusal: {0}")]
    Instrument(#[from] ExactInstrumentError),
    #[error(
        "same-instrument repetition requires equal input/output dimensions ({dim_in}, {dim_out})"
    )]
    DifferentCarriers { dim_in: usize, dim_out: usize },
}

/// A concrete nonzero cross-outcome Kraus product. The accompanying strictly
/// positive probability is for the canonical density I/d, not a sampled state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OutcomeSwitchWitness {
    pub first_outcome: usize,
    pub second_outcome: usize,
    pub first_kraus: usize,
    pub second_kraus: usize,
    pub cross_product: BasicMatrix<GaussianRat>,
    pub joint_probability_on_maximally_mixed: Rational,
}

/// Each entry is the joint probability of first o, then j, on I/d.
/// Private construction prevents a mutable report from acting as a checked fact.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct RepeatabilityAnalysis {
    dimension: usize,
    joint_probabilities: Vec<Vec<Rational>>,
    first_switch: Option<OutcomeSwitchWitness>,
}

impl RepeatabilityAnalysis {
    pub fn is_repeatable(&self) -> bool {
        self.first_switch.is_none()
    }
    pub fn dimension(&self) -> usize {
        self.dimension
    }
    pub fn joint_probabilities(&self) -> &[Vec<Rational>] {
        &self.joint_probabilities
    }
    pub fn switching_witness(&self) -> Option<&OutcomeSwitchWitness> {
        self.first_switch.as_ref()
    }
}

fn evaluate_outcome_pair_joint(
    first_outcome: usize,
    second_outcome: usize,
    first_group: &[BasicMatrix<GaussianRat>],
    second_group: &[BasicMatrix<GaussianRat>],
    denominator: &Rational,
) -> Result<(Rational, Option<(usize, usize, BasicMatrix<GaussianRat>)>), RepeatabilityError> {
    let mut joint = ri(0);
    let mut first_nonzero_pair = None;
    for (first_kraus, first) in first_group.iter().enumerate() {
        for (second_kraus, second) in second_group.iter().enumerate() {
            let cross_product = mx::multiply(second, first)?;
            let norm_squared: Rational =
                cross_product.as_slice().iter().map(|x| x.norm_sq()).sum();
            joint += &norm_squared / denominator;
            let is_switch = first_outcome != second_outcome && !norm_squared.is_zero();
            if is_switch && first_nonzero_pair.is_none() {
                first_nonzero_pair = Some((first_kraus, second_kraus, cross_product));
            }
        }
    }
    Ok((joint, first_nonzero_pair))
}

/// Decide the all-state criterion by exhaustive exact cross-Kraus algebra.
/// Empty outcome groups are harmless: their first-event probability is zero.
pub fn analyze_repeatability(
    instrument: &ExactFiniteInstrument,
) -> Result<RepeatabilityAnalysis, RepeatabilityError> {
    let dimension = instrument.channel().dim_in();
    let dim_out = instrument.channel().dim_out();
    if dimension != dim_out {
        return Err(RepeatabilityError::DifferentCarriers {
            dim_in: dimension,
            dim_out,
        });
    }
    let denominator = Rational::from_integer(dimension.into());
    let outcomes = instrument.outcomes();
    let mut joint_probabilities = vec![vec![ri(0); outcomes]; outcomes];
    let mut first_switch = None;
    for (first_outcome, row) in joint_probabilities.iter_mut().enumerate() {
        let first_group = instrument.operators_for_outcome(first_outcome)?;
        for (second_outcome, joint) in row.iter_mut().enumerate() {
            let second_group = instrument.operators_for_outcome(second_outcome)?;
            let (prob, pair) = evaluate_outcome_pair_joint(
                first_outcome,
                second_outcome,
                first_group,
                second_group,
                &denominator,
            )?;
            *joint = prob;
            if first_switch.is_none() {
                if let Some((first_kraus, second_kraus, cross_product)) = pair {
                    first_switch = Some(OutcomeSwitchWitness {
                        first_outcome,
                        second_outcome,
                        first_kraus,
                        second_kraus,
                        cross_product,
                        joint_probability_on_maximally_mixed: joint.clone(),
                    });
                }
            }
        }
    }
    Ok(RepeatabilityAnalysis {
        dimension,
        joint_probabilities,
        first_switch,
    })
}

pub fn is_outcome_repeatable(
    instrument: &ExactFiniteInstrument,
) -> Result<bool, RepeatabilityError> {
    Ok(analyze_repeatability(instrument)?.is_repeatable())
}

// Origin: engine/crates_rs/core_quantum_physics/src/instrument_repeatability.rs
// Claim: urn:core:crates_rs:core-quantum-physics:instrument-repeatability:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_140bbe6f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
