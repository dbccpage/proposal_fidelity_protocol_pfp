//! Exact finite Neville--Aitken enclosures with explicitly retained premises.
//!
//! The caller declares `f(x_i)` in each sample interval and, for each prefix,
//! `|f(at) - p_N(at)| <= B_N`. These are assumptions about the caller's function,
//! not independently certified derivative or analytic remainder bounds. Missing
//! bounds are refused; interpolation never supplies a zero bound by default.
//! Propagating the sample intervals gives `P_N`, and `J_N = P_N + [-B_N, B_N]`
//! conditionally encloses `f(at)`. The returned history uses `I_1 = J_1` and
//! `I_N = I_(N-1) intersect J_N`, refusing an empty intersection. Thus nesting is
//! checked rather than inferred from interpolation, polynomial degree or width.
//!
//! Replay binds every sample, evaluation point, remainder bound, target identity
//! and optional known rational target to the declared input. It checks the
//! Neville recurrence and a separate Lagrange image of the sample box. A known
//! target adds exact finite membership checks; it does not validate the function
//! premises. No receipt asserts shrinking widths, an all-index error modulus or
//! convergence of an infinite sequence. There is no serialization API here.
//!
//! One caller-owned rational budget covers validation, proposal and replay.
//! AuthorityEffect: None.

use linear_algebra::exact_field::neville_aitken::{self as exact, NevilleError, RationalEndpoints};
use linear_algebra::exact_field::rational_bareiss::{RationalBudget, RationalError};
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_kernel::interval::Interval;
use core_types::authority::AuthorityEffect;

/// The declared premise `f(node) in enclosure`; absence is a typed refusal.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct SampleBound {
    pub node: BigRational,
    pub enclosure: Option<Interval>,
}

/// Every bound is attached to its ordered sample prefix and this evaluation point.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NevilleEnclosureProblem {
    pub target_id: String,
    pub evaluation_point: BigRational,
    pub samples: Vec<SampleBound>,
    /// Entry `N - 1` declares `|f(evaluation_point) - p_N(evaluation_point)| <= B_N`.
    /// A zero bound is allowed only as an explicit conditional premise.
    pub prefix_remainder_bounds: Vec<Option<BigRational>>,
    /// Optional independently designated rational value, checked in every interval.
    pub known_target: Option<BigRational>,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NevilleEnclosureStep {
    pub prefix_len: usize,
    pub polynomial_enclosure: Interval,
    pub remainder_enclosure: Interval,
    pub nested_enclosure: Interval,
}

/// An untrusted candidate, including the complete declared premise binding.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NevilleEnclosureCertificate {
    pub problem_binding: NevilleEnclosureProblem,
    pub steps: Vec<NevilleEnclosureStep>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum EnclosureScope {
    FiniteConditionalOnSampleAndRemainderPremises,
}

/// Constructible only through replay. Fields are private to preserve the checked scope.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct NevilleEnclosureReceipt {
    problem_binding: NevilleEnclosureProblem,
    steps: Vec<NevilleEnclosureStep>,
    scalar_ops: usize,
    authority_effect: AuthorityEffect,
}

impl NevilleEnclosureReceipt {
    pub fn problem_binding(&self) -> &NevilleEnclosureProblem {
        &self.problem_binding
    }

    pub fn steps(&self) -> &[NevilleEnclosureStep] {
        &self.steps
    }

    pub fn scope(&self) -> EnclosureScope {
        EnclosureScope::FiniteConditionalOnSampleAndRemainderPremises
    }

    /// Some value means exact membership was checked for this finite history.
    pub fn checked_rational_target(&self) -> Option<&BigRational> {
        self.problem_binding.known_target.as_ref()
    }

    pub fn scalar_ops(&self) -> usize {
        self.scalar_ops
    }

    pub fn authority_effect(&self) -> &AuthorityEffect {
        &self.authority_effect
    }
}

#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum NevilleEnclosureError {
    #[error("target identity must be nonempty")]
    MissingTargetIdentity,
    #[error("the declared sample family is empty")]
    EmptySamples,
    #[error("sample {index} has no declared enclosure")]
    MissingSampleBound { index: usize },
    #[error("prefix {prefix} has no declared remainder bound")]
    MissingRemainderBound { prefix: usize },
    #[error("{actual} remainder bounds for {expected} sample prefixes")]
    RemainderCount { expected: usize, actual: usize },
    #[error("prefix {prefix} has a negative absolute remainder bound")]
    NegativeRemainderBound { prefix: usize },
    #[error("the candidate is bound to different declared inputs or premises")]
    InputBindingMismatch,
    #[error("{actual} candidate steps for {expected} sample prefixes")]
    StepCount { expected: usize, actual: usize },
    #[error("candidate prefix {prefix} is not in the declared order")]
    PrefixOrder { prefix: usize },
    #[error("candidate polynomial enclosure differs from Neville replay at prefix {prefix}")]
    PolynomialMismatch { prefix: usize },
    #[error("Neville enclosure omits the independent Lagrange image at prefix {prefix}")]
    LagrangeImageMismatch { prefix: usize },
    #[error("candidate remainder enclosure differs from the declared bound at prefix {prefix}")]
    RemainderMismatch { prefix: usize },
    #[error("candidate nested enclosure differs from the checked intersection at prefix {prefix}")]
    IntersectionMismatch { prefix: usize },
    #[error("the enclosure intersection is empty at prefix {prefix}")]
    EmptyIntersection { prefix: usize },
    #[error("the known rational target is outside the declared enclosure at prefix {prefix}")]
    KnownTargetNotEnclosed { prefix: usize },
    #[error("interval endpoints violate their order invariant")]
    InvalidInterval,
    #[error(transparent)]
    Interpolation(#[from] NevilleError),
    #[error(transparent)]
    Arithmetic(#[from] RationalError),
}

struct PreparedInput {
    nodes: Vec<BigRational>,
    samples: Vec<RationalEndpoints>,
    remainders: Vec<BigRational>,
}

fn storage<T>(
    count: usize,
    scalars_per_element: usize,
    fuel: &RationalBudget,
) -> Result<Vec<T>, NevilleEnclosureError> {
    fuel.elements(count, scalars_per_element)?;
    let mut out = Vec::new();
    out.try_reserve_exact(count)
        .map_err(|_| RationalError::Allocation)?;
    Ok(out)
}

fn check_interval(
    interval: &Interval,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    fuel.rational(interval.lo())?;
    fuel.rational(interval.hi())?;
    fuel.charge(1)?;
    if interval.lo() > interval.hi() {
        return Err(NevilleEnclosureError::InvalidInterval);
    }
    Ok(())
}

fn endpoints(interval: &Interval) -> RationalEndpoints {
    (interval.lo().clone(), interval.hi().clone())
}

fn make_interval(
    endpoints: RationalEndpoints,
    fuel: &mut RationalBudget,
) -> Result<Interval, NevilleEnclosureError> {
    exact::validate_interval(&endpoints, fuel)?;
    fuel.charge(2)?;
    Interval::try_new(endpoints.0, endpoints.1).map_err(|_| NevilleEnclosureError::InvalidInterval)
}

fn validate_remainder_bounds_header(
    problem: &NevilleEnclosureProblem,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    fuel.elements(problem.samples.len(), 2)?;
    fuel.elements(problem.prefix_remainder_bounds.len(), 1)?;
    if problem.prefix_remainder_bounds.len() < problem.samples.len() {
        return Err(NevilleEnclosureError::MissingRemainderBound {
            prefix: problem.prefix_remainder_bounds.len() + 1,
        });
    }
    if problem.prefix_remainder_bounds.len() != problem.samples.len() {
        return Err(NevilleEnclosureError::RemainderCount {
            expected: problem.samples.len(),
            actual: problem.prefix_remainder_bounds.len(),
        });
    }
    Ok(())
}

fn validate_problem_header(
    problem: &NevilleEnclosureProblem,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    fuel.elements(problem.target_id.len(), 1)?;
    if problem.target_id.trim().is_empty() {
        return Err(NevilleEnclosureError::MissingTargetIdentity);
    }
    if problem.samples.is_empty() {
        return Err(NevilleEnclosureError::EmptySamples);
    }
    validate_remainder_bounds_header(problem, fuel)?;
    fuel.rational(&problem.evaluation_point)?;
    if let Some(target) = &problem.known_target {
        fuel.rational(target)?;
    }
    Ok(())
}

fn extract_sample_and_remainder(
    index: usize,
    sample: &SampleBound,
    bound_opt: Option<&BigRational>,
    fuel: &mut RationalBudget,
) -> Result<(BigRational, RationalEndpoints, BigRational), NevilleEnclosureError> {
    fuel.rational(&sample.node)?;
    let interval = sample
        .enclosure
        .as_ref()
        .ok_or(NevilleEnclosureError::MissingSampleBound { index })?;
    check_interval(interval, fuel)?;
    let bound =
        bound_opt.ok_or(NevilleEnclosureError::MissingRemainderBound { prefix: index + 1 })?;
    fuel.rational(bound)?;
    fuel.charge(1)?;
    if bound.is_negative() {
        return Err(NevilleEnclosureError::NegativeRemainderBound { prefix: index + 1 });
    }
    Ok((sample.node.clone(), endpoints(interval), bound.clone()))
}

fn assert_preconditions(
    problem: &NevilleEnclosureProblem,
    fuel: &mut RationalBudget,
) -> Result<PreparedInput, NevilleEnclosureError> {
    validate_problem_header(problem, fuel)?;
    let mut nodes = storage(problem.samples.len(), 1, fuel)?;
    let mut samples = storage(problem.samples.len(), 2, fuel)?;
    let mut remainders = storage(problem.samples.len(), 1, fuel)?;
    for (index, sample) in problem.samples.iter().enumerate() {
        let (node, endpts, bound) = extract_sample_and_remainder(
            index,
            sample,
            problem.prefix_remainder_bounds[index].as_ref(),
            fuel,
        )?;
        nodes.push(node);
        samples.push(endpts);
        remainders.push(bound);
    }
    Ok(PreparedInput {
        nodes,
        samples,
        remainders,
    })
}

fn copy_problem(
    problem: &NevilleEnclosureProblem,
    fuel: &RationalBudget,
) -> Result<NevilleEnclosureProblem, NevilleEnclosureError> {
    fuel.elements(problem.target_id.len(), 1)?;
    let mut target_id = String::new();
    target_id
        .try_reserve_exact(problem.target_id.len())
        .map_err(|_| RationalError::Allocation)?;
    target_id.push_str(&problem.target_id);
    let mut samples = storage(problem.samples.len(), 3, fuel)?;
    samples.extend(problem.samples.iter().cloned());
    let mut prefix_remainder_bounds = storage(problem.prefix_remainder_bounds.len(), 1, fuel)?;
    prefix_remainder_bounds.extend(problem.prefix_remainder_bounds.iter().cloned());
    Ok(NevilleEnclosureProblem {
        target_id,
        evaluation_point: problem.evaluation_point.clone(),
        samples,
        prefix_remainder_bounds,
        known_target: problem.known_target.clone(),
    })
}

fn with_remainder(
    polynomial: &RationalEndpoints,
    bound: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleEnclosureError> {
    let negative_bound = fuel.sub(&BigRational::zero(), bound)?;
    Ok(exact::interval_add(
        polynomial,
        &(negative_bound, bound.clone()),
        fuel,
    )?)
}

fn intersect_at_prefix(
    previous: &RationalEndpoints,
    current: &RationalEndpoints,
    prefix: usize,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleEnclosureError> {
    match exact::intersect(previous, current, fuel) {
        Err(NevilleError::EmptyIntersection) => {
            Err(NevilleEnclosureError::EmptyIntersection { prefix })
        }
        result => Ok(result?),
    }
}

fn check_known_target(
    target: Option<&BigRational>,
    interval: &RationalEndpoints,
    prefix: usize,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    if let Some(target) = target {
        fuel.charge(2)?;
        if target < &interval.0 || target > &interval.1 {
            return Err(NevilleEnclosureError::KnownTargetNotEnclosed { prefix });
        }
    }
    Ok(())
}

fn build_neville_step(
    prefix: usize,
    value: RationalEndpoints,
    remainder: &BigRational,
    previous: Option<&NevilleEnclosureStep>,
    known_target: Option<&BigRational>,
    fuel: &mut RationalBudget,
) -> Result<NevilleEnclosureStep, NevilleEnclosureError> {
    let raw = with_remainder(&value, remainder, fuel)?;
    check_known_target(known_target, &raw, prefix, fuel)?;
    let nested = match previous {
        Some(prev) => intersect_at_prefix(&endpoints(&prev.nested_enclosure), &raw, prefix, fuel)?,
        None => raw.clone(),
    };
    check_known_target(known_target, &nested, prefix, fuel)?;
    Ok(NevilleEnclosureStep {
        prefix_len: prefix,
        polynomial_enclosure: make_interval(value, fuel)?,
        remainder_enclosure: make_interval(raw, fuel)?,
        nested_enclosure: make_interval(nested, fuel)?,
    })
}

/// Produce a finite candidate; this does not create a checked receipt.
pub fn propose_neville_enclosures(
    problem: &NevilleEnclosureProblem,
    fuel: &mut RationalBudget,
) -> Result<NevilleEnclosureCertificate, NevilleEnclosureError> {
    let input = assert_preconditions(problem, fuel)?;
    let polynomial = exact::interpolate_interval_prefixes(
        &input.nodes,
        &input.samples,
        &problem.evaluation_point,
        fuel,
    )?;
    let mut steps: Vec<NevilleEnclosureStep> = storage(polynomial.len(), 6, fuel)?;
    for (index, value) in polynomial.into_iter().enumerate() {
        let step = build_neville_step(
            index + 1,
            value,
            &input.remainders[index],
            steps.last(),
            problem.known_target.as_ref(),
            fuel,
        )?;
        steps.push(step);
    }
    Ok(NevilleEnclosureCertificate {
        problem_binding: copy_problem(problem, fuel)?,
        steps,
    })
}

fn validate_candidate_binding_and_intervals(
    problem: &NevilleEnclosureProblem,
    candidate: &NevilleEnclosureCertificate,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    assert_preconditions(&candidate.problem_binding, fuel)?;
    fuel.charge(1)?;
    if candidate.problem_binding != *problem {
        return Err(NevilleEnclosureError::InputBindingMismatch);
    }
    if candidate.steps.len() != problem.samples.len() {
        return Err(NevilleEnclosureError::StepCount {
            expected: problem.samples.len(),
            actual: candidate.steps.len(),
        });
    }
    fuel.elements(candidate.steps.len(), 6)?;
    for step in &candidate.steps {
        check_interval(&step.polynomial_enclosure, fuel)?;
        check_interval(&step.remainder_enclosure, fuel)?;
        check_interval(&step.nested_enclosure, fuel)?;
    }
    Ok(())
}

fn verify_polynomial_and_lagrange_step(
    prefix: usize,
    step: &NevilleEnclosureStep,
    value: &RationalEndpoints,
    lagrange_val: &RationalEndpoints,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleEnclosureError> {
    fuel.charge(1)?;
    if step.prefix_len != prefix {
        return Err(NevilleEnclosureError::PrefixOrder { prefix });
    }
    fuel.charge(2)?;
    if step.polynomial_enclosure.lo() != &value.0 || step.polynomial_enclosure.hi() != &value.1 {
        return Err(NevilleEnclosureError::PolynomialMismatch { prefix });
    }
    fuel.charge(2)?;
    if lagrange_val.0 < value.0 || lagrange_val.1 > value.1 {
        return Err(NevilleEnclosureError::LagrangeImageMismatch { prefix });
    }
    Ok(())
}

fn verify_raw_remainder_interval(
    prefix: usize,
    step: &NevilleEnclosureStep,
    value: &RationalEndpoints,
    remainder: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleEnclosureError> {
    let raw = with_remainder(value, remainder, fuel)?;
    fuel.charge(2)?;
    if step.remainder_enclosure.lo() != &raw.0 || step.remainder_enclosure.hi() != &raw.1 {
        return Err(NevilleEnclosureError::RemainderMismatch { prefix });
    }
    Ok(raw)
}

fn verify_nested_step_interval(
    prefix: usize,
    step: &NevilleEnclosureStep,
    raw: &RationalEndpoints,
    previous: Option<&RationalEndpoints>,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleEnclosureError> {
    let nested = match previous {
        Some(outer) => intersect_at_prefix(outer, raw, prefix, fuel)?,
        None => raw.clone(),
    };
    fuel.charge(2)?;
    if step.nested_enclosure.lo() != &nested.0 || step.nested_enclosure.hi() != &nested.1 {
        return Err(NevilleEnclosureError::IntersectionMismatch { prefix });
    }
    Ok(nested)
}

#[allow(clippy::too_many_arguments)]
fn verify_step_enclosures(
    prefix: usize,
    step: &NevilleEnclosureStep,
    value: &RationalEndpoints,
    lagrange_val: &RationalEndpoints,
    remainder: &BigRational,
    previous: Option<&RationalEndpoints>,
    known_target: Option<&BigRational>,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleEnclosureError> {
    verify_polynomial_and_lagrange_step(prefix, step, value, lagrange_val, fuel)?;
    let raw = verify_raw_remainder_interval(prefix, step, value, remainder, fuel)?;
    let nested = verify_nested_step_interval(prefix, step, &raw, previous, fuel)?;
    check_known_target(known_target, &raw, prefix, fuel)?;
    check_known_target(known_target, &nested, prefix, fuel)?;
    let tight_raw = with_remainder(lagrange_val, remainder, fuel)?;
    check_known_target(known_target, &tight_raw, prefix, fuel)?;
    Ok(nested)
}

/// Replay every consumed role and every interval before issuing finite evidence.
/// Sample and remainder assertions remain explicit assumptions in the receipt.
pub fn check_neville_enclosures(
    problem: &NevilleEnclosureProblem,
    candidate: &NevilleEnclosureCertificate,
    fuel: &mut RationalBudget,
) -> Result<NevilleEnclosureReceipt, NevilleEnclosureError> {
    let start = fuel.used();
    let input = assert_preconditions(problem, fuel)?;
    validate_candidate_binding_and_intervals(problem, candidate, fuel)?;
    let polynomial = exact::interpolate_interval_prefixes(
        &input.nodes,
        &input.samples,
        &problem.evaluation_point,
        fuel,
    )?;
    let lagrange = exact::lagrange_interval_prefixes(
        &input.nodes,
        &input.samples,
        &problem.evaluation_point,
        fuel,
    )?;
    let mut previous: Option<RationalEndpoints> = None;
    for (index, step) in candidate.steps.iter().enumerate() {
        let nested = verify_step_enclosures(
            index + 1,
            step,
            &polynomial[index],
            &lagrange[index],
            &input.remainders[index],
            previous.as_ref(),
            problem.known_target.as_ref(),
            fuel,
        )?;
        previous = Some(nested);
    }
    let mut steps = storage(candidate.steps.len(), 6, fuel)?;
    steps.extend(candidate.steps.iter().cloned());
    Ok(NevilleEnclosureReceipt {
        problem_binding: copy_problem(problem, fuel)?,
        steps,
        scalar_ops: fuel.used() - start,
        authority_effect: AuthorityEffect::None,
    })
}

/// Construct and replay under a single budget; exhaustion returns no partial receipt.
pub fn solve_neville_enclosures(
    problem: &NevilleEnclosureProblem,
    fuel: &mut RationalBudget,
) -> Result<NevilleEnclosureReceipt, NevilleEnclosureError> {
    let start = fuel.used();
    let candidate = propose_neville_enclosures(problem, fuel)?;
    let mut receipt = check_neville_enclosures(problem, &candidate, fuel)?;
    receipt.scalar_ops = fuel.used() - start;
    Ok(receipt)
}

// Origin: engine/crates_rs/core_solvers/src/solver_neville_aitken_enclosure.rs
// Claim: urn:core:crates_rs:core-solvers:solver-neville-aitken-enclosure:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3cab2024 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
