use core_number_theory::rational::{rq, One, Rational, Zero};
use core_quantum_physics::meron_source_field::SourceFieldPlan;
use core_wdp::meron_time_adapter::DeclaredMeronSource;
use core_wdp::types::AuthorityEffect;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum TraceError {
    Sites,
    Repetitions,
    TransferNotIdentity,
    Source,
    Overflow,
}

// Origin: engine/crates_rs/tests/core_wdp/test_meron_source_adapter.rs
// Claim: urn:core:crates_rs:tests:test-meron-source-adapter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TraceError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TraceError {}

fn occupation(state: usize, site: usize, sites: usize) -> Result<i64, TraceError> {
    let shift = sites
        .checked_sub(site)
        .and_then(|value| value.checked_sub(1))
        .ok_or(TraceError::Sites)?;
    let shift_u = u32::try_from(shift).map_err(|_| TraceError::Sites)?;
    let bit = state.checked_shr(shift_u).ok_or(TraceError::Sites)?;
    i64::try_from(bit & 1).map_err(|_| TraceError::Overflow)
}

fn staggered_twice(state: usize, sites: usize) -> Result<i64, TraceError> {
    let mut twice = 0i64;
    let mut site = 0usize;
    while site < sites {
        let occupied = occupation(state, site, sites)?;
        let centered = occupied.checked_mul(2).and_then(|value| value.checked_sub(1)).ok_or(TraceError::Overflow)?;
        let signed = if site % 2 == 0 {
            centered
        } else {
            centered.checked_neg().ok_or(TraceError::Overflow)?
        };
        twice = twice.checked_add(signed).ok_or(TraceError::Overflow)?;
        site = site.checked_add(1).ok_or(TraceError::Overflow)?;
    }
    Ok(twice)
}

fn rat_pow(base: &Rational, exponent: i32) -> Result<Rational, TraceError> {
    if exponent < 0 && *base == Rational::zero() {
        return Err(TraceError::Source);
    }
    let mut exp = exponent.unsigned_abs();
    let mut result = Rational::one();
    let mut factor = base.clone();
    while exp > 0 {
        if exp & 1 == 1 {
            result = &result * &factor;
        }
        exp >>= 1;
        if exp > 0 {
            factor = &factor * &factor;
        }
    }
    if exponent < 0 {
        if result == Rational::zero() {
            return Err(TraceError::Source);
        }
        Ok(result.recip())
    } else {
        Ok(result)
    }
}

// Exact carrier witness.
// At q = 1 each half-layer is the identity, so the source trace is the sum of v^(2AM) over occupation states.
fn validate_identity_layer_plan(plan: &SourceFieldPlan) -> Result<(usize, usize), TraceError> {
    let sites = plan.time().sites();
    let repetitions = plan.time().repetitions();
    if !(4..=12).contains(&sites) || sites % 2 != 0 {
        return Err(TraceError::Sites);
    }
    if !(1..=16).contains(&repetitions) {
        return Err(TraceError::Repetitions);
    }
    if plan.time().q() != &Rational::one() {
        return Err(TraceError::TransferNotIdentity);
    }
    if plan.v() <= &Rational::zero() {
        return Err(TraceError::Source);
    }
    Ok((sites, repetitions))
}

fn identity_layer_source_trace(plan: &SourceFieldPlan) -> Result<Rational, TraceError> {
    let (sites, repetitions) = validate_identity_layer_plan(plan)?;
    let shift = u32::try_from(sites).map_err(|_| TraceError::Sites)?;
    let dimension = 1usize.checked_shl(shift).ok_or(TraceError::Sites)?;
    let reps = i64::try_from(repetitions).map_err(|_| TraceError::Repetitions)?;
    let mut total = Rational::zero();
    for state in 0..dimension {
        let exponent = staggered_twice(state, sites)?.checked_mul(reps).ok_or(TraceError::Overflow)?;
        let exp_i32 = i32::try_from(exponent).map_err(|_| TraceError::Overflow)?;
        total = &total + &rat_pow(plan.v(), exp_i32)?;
    }
    Ok(total)
}

#[test]
fn thin_source_adapter_retains_the_actual_trace_without_authority_promotion() {
    let plan = SourceFieldPlan::new(4, 1, rq(0, 1), rq(0, 1), rq(2, 1), rq(0, 1)).unwrap();
    let source = DeclaredMeronSource::new(plan.clone()).unwrap();
    let computed = identity_layer_source_trace(&plan);
    assert_eq!(source.plan(), &plan);
    assert_eq!(computed.as_ref(), Ok(source.unscaled_partition()));
    assert_eq!(computed, Ok(rq(625, 16)));
    assert_eq!(source.authority_effect(), AuthorityEffect::None);
}

#[test]
fn a_nonunit_transfer_parameter_is_not_an_identity_layer() {
    let plan = SourceFieldPlan::new(4, 1, rq(1, 1), rq(0, 1), rq(2, 1), rq(0, 1));
    assert!(matches!(
        plan.map(|value| identity_layer_source_trace(&value)),
        Ok(Err(TraceError::TransferNotIdentity))
    ));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
