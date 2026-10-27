//! Exact majorization of quantum population and Schmidt spectra.
//! The simplex owner validates probabilities; comparison uses all exact partial
//! sums after sorting, so ordering of eigenvalues is irrelevant. No LOCC
//! authority follows without the remaining physical hypotheses.
use num_traits::{One, Zero};
use core_finite_probability::error::ClassicalShadowError;
use core_finite_probability::simplex::ProbabilitySimplex;
use core_number_theory::rational::Rational;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Majorization {
    Equal,
    PMajorizesQ,
    QMajorizesP,
    Incomparable,
}
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MajorizationError {
    #[error("spectrum dimensions differ: {first} and {second}")]
    Dimension { first: usize, second: usize },
    #[error("thermal ladder requires a positive ratio")]
    NonPositiveRatio,
    #[error("thermal ladder level budget exceeded: {levels} > {maximum}")]
    LevelBudget { levels: usize, maximum: usize },
    #[error(transparent)]
    Probability(#[from] ClassicalShadowError),
}
pub fn compare(
    p: &ProbabilitySimplex,
    q: &ProbabilitySimplex,
) -> Result<Majorization, MajorizationError> {
    if p.probs().len() != q.probs().len() {
        return Err(MajorizationError::Dimension {
            first: p.probs().len(),
            second: q.probs().len(),
        });
    }
    let mut a = p.probs().to_vec();
    let mut b = q.probs().to_vec();
    a.sort_by(|a, b| b.cmp(a));
    b.sort_by(|a, b| b.cmp(a));
    let (mut sum_a, mut sum_b) = (Rational::zero(), Rational::zero());
    let (mut p_dom, mut q_dom) = (true, true);
    for (a, b) in a.iter().zip(&b) {
        sum_a += a;
        sum_b += b;
        p_dom &= sum_a >= sum_b;
        q_dom &= sum_b >= sum_a;
    }
    Ok(match (p_dom, q_dom) {
        (true, true) => Majorization::Equal,
        (true, false) => Majorization::PMajorizesQ,
        (false, true) => Majorization::QMajorizesP,
        (false, false) => Majorization::Incomparable,
    })
}
/// Majorization of declared spectra, including exact degeneracies. The expansion
/// is bounded explicitly for callers whose multiplicities are untrusted.
pub fn compare_spectra(
    p: &crate::exact_entropy::RationalSpectrum,
    q: &crate::exact_entropy::RationalSpectrum,
) -> Result<Majorization, MajorizationError> {
    compare_spectra_with_budget(p, q, 4096)
}
pub fn compare_spectra_with_budget(
    p: &crate::exact_entropy::RationalSpectrum,
    q: &crate::exact_entropy::RationalSpectrum,
    max_dimension: usize,
) -> Result<Majorization, MajorizationError> {
    let expand=|spectrum:&crate::exact_entropy::RationalSpectrum|->Result<ProbabilitySimplex,MajorizationError>{
        if spectrum.dimension()>max_dimension{return Err(MajorizationError::LevelBudget{levels:spectrum.dimension(),maximum:max_dimension});}
        let mut probabilities=Vec::new();for (q,m) in spectrum.entries(){for _ in 0..*m{probabilities.push(q.clone());}}
        Ok(ProbabilitySimplex::try_new(probabilities)?)
    };
    compare(&expand(p)?, &expand(q)?)
}

/// Gibbs populations proportional to ratio^k, in ascending energy-level order.
pub fn thermal_ladder(
    ratio: &Rational,
    levels: usize,
    max_levels: usize,
) -> Result<ProbabilitySimplex, MajorizationError> {
    if ratio <= &Rational::zero() {
        return Err(MajorizationError::NonPositiveRatio);
    }
    if levels > max_levels {
        return Err(MajorizationError::LevelBudget {
            levels,
            maximum: max_levels,
        });
    }
    let mut weights = Vec::new();
    let mut power = Rational::one();
    for _ in 0..levels {
        weights.push(power.clone());
        power *= ratio;
    }
    let total: Rational = weights.iter().cloned().sum();
    if total.is_zero() {
        return Err(ClassicalShadowError::Empty.into());
    }
    Ok(ProbabilitySimplex::try_new(
        weights.into_iter().map(|q| q / &total).collect(),
    )?)
}
// Origin: engine/crates_rs/core_quantum_physics/src/majorization.rs
// Claim: urn:core:crates_rs:core-quantum-physics:majorization:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{ri, rq};
    fn p(values: Vec<Rational>) -> ProbabilitySimplex {
        ProbabilitySimplex::try_new(values).unwrap()
    }
    #[test]
    fn incomparable_spectra_and_order_invariance_use_every_partial_sum() {
        let a = p(vec![rq(7, 10), rq(3, 20), rq(3, 20)]);
        let b = p(vec![rq(3, 5), rq(7, 20), rq(1, 20)]);
        assert_eq!(compare(&a, &b).unwrap(), Majorization::Incomparable);
        assert_eq!(compare(&a, &a).unwrap(), Majorization::Equal);
        let reordered = p(vec![rq(3, 20), rq(7, 10), rq(3, 20)]);
        assert_eq!(compare(&a, &reordered).unwrap(), Majorization::Equal);
        let pure = p(vec![ri(1), ri(0), ri(0)]);
        let uniform = p(vec![rq(1, 3); 3]);
        assert_eq!(compare(&pure, &a).unwrap(), Majorization::PMajorizesQ);
        assert_eq!(compare(&a, &uniform).unwrap(), Majorization::PMajorizesQ);
        assert_eq!(compare(&pure, &uniform).unwrap(), Majorization::PMajorizesQ);
    }
    #[test]
    fn thermal_order_and_entropy_schur_concavity_have_exact_witnesses() {
        let cold = thermal_ladder(&rq(1, 2), 4, 16).unwrap();
        let warm = thermal_ladder(&rq(3, 4), 4, 16).unwrap();
        assert_eq!(cold.probs(), &[rq(8, 15), rq(4, 15), rq(2, 15), rq(1, 15)]);
        assert_eq!(compare(&cold, &warm).unwrap(), Majorization::PMajorizesQ);
        let cold_form = core_finite_probability::log_form::shannon_entropy_form(&cold).unwrap();
        let warm_form = core_finite_probability::log_form::shannon_entropy_form(&warm).unwrap();
        assert_eq!(
            cold_form.compare(&warm_form, 128).unwrap(),
            std::cmp::Ordering::Less
        );
        assert!(thermal_ladder(&ri(0), 4, 16).is_err());
        assert!(thermal_ladder(&rq(1, 2), 17, 16).is_err());
        assert!(thermal_ladder(&rq(1, 2), 0, 16).is_err());
    }
}
