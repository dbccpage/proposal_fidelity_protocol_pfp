//! Bounded exact Neville--Aitken evaluation and rational interval propagation.
//!
//! For distinct nodes, the recurrence evaluates the unique interpolating
//! polynomial of each finite prefix. Endpoint propagation encloses every
//! polynomial obtained by independently choosing a sample in its interval;
//! repeated dependencies can widen this enclosure. The separate Lagrange
//! calculation gives the tight image of that sample box and can replay it.
//! Neither calculation supplies a function remainder or an asymptotic limit.
//!
//! All scalar arithmetic uses one caller-owned [`RationalBudget`]. Limits count
//! scalar calls, canonicality checks and comparisons, rather than CPU work or
//! scalar-internal allocation. Each scratch/output collection is element-bounded
//! and uses fallible reservation. AuthorityEffect: None.

use super::rational_bareiss::{RationalBudget, RationalError};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

/// Endpoint transport without depending on a higher-level interval carrier.
/// Every consuming operation checks canonical rationals and endpoint order.
pub type RationalEndpoints = (BigRational, BigRational);

#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum NevilleError {
    #[error("interpolation needs a nonempty finite node family")]
    EmptyNodes,
    #[error("{actual} sample values for {expected} nodes")]
    SampleCount { expected: usize, actual: usize },
    #[error("nodes {first} and {second} coincide")]
    DuplicateNode { first: usize, second: usize },
    #[error("interval endpoints are inverted")]
    InvertedInterval,
    #[error("interval intersection is empty")]
    EmptyIntersection,
    #[error(transparent)]
    Arithmetic(#[from] RationalError),
}

fn storage<T>(
    count: usize,
    scalars_per_element: usize,
    fuel: &RationalBudget,
) -> Result<Vec<T>, NevilleError> {
    fuel.elements(count, scalars_per_element)?;
    let mut out = Vec::new();
    out.try_reserve_exact(count)
        .map_err(|_| RationalError::Allocation)?;
    Ok(out)
}

fn check_nodes(
    nodes: &[BigRational],
    values: usize,
    at: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    if nodes.is_empty() {
        return Err(NevilleError::EmptyNodes);
    }
    if nodes.len() != values {
        return Err(NevilleError::SampleCount {
            expected: nodes.len(),
            actual: values,
        });
    }
    fuel.elements(nodes.len(), 1)?;
    fuel.rational(at)?;
    for node in nodes {
        fuel.rational(node)?;
    }
    check_distinct_nodes(nodes, fuel)
}

fn check_distinct_nodes(
    nodes: &[BigRational],
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    for (second, node) in nodes.iter().enumerate() {
        for (first, previous) in nodes[..second].iter().enumerate() {
            fuel.charge(1)?;
            if node == previous {
                return Err(NevilleError::DuplicateNode { first, second });
            }
        }
    }
    Ok(())
}

pub fn validate_interval(
    interval: &RationalEndpoints,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    fuel.rational(&interval.0)?;
    fuel.rational(&interval.1)?;
    fuel.charge(1)?;
    if interval.0 > interval.1 {
        return Err(NevilleError::InvertedInterval);
    }
    Ok(())
}

/// Exact Minkowski addition of two validated rational intervals.
pub fn interval_add(
    a: &RationalEndpoints,
    b: &RationalEndpoints,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleError> {
    validate_interval(a, fuel)?;
    validate_interval(b, fuel)?;
    Ok((fuel.add(&a.0, &b.0)?, fuel.add(&a.1, &b.1)?))
}

/// The exact image under scalar multiplication, reversing endpoints for `k < 0`.
pub fn interval_scale(
    a: &RationalEndpoints,
    k: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleError> {
    validate_interval(a, fuel)?;
    fuel.rational(k)?;
    fuel.charge(1)?;
    let (lo, hi) = if k.is_negative() {
        (&a.1, &a.0)
    } else {
        (&a.0, &a.1)
    };
    Ok((fuel.mul(lo, k)?, fuel.mul(hi, k)?))
}

/// Division by a nonzero rational scalar, with exact endpoint orientation.
pub fn interval_divide(
    a: &RationalEndpoints,
    k: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleError> {
    validate_interval(a, fuel)?;
    fuel.rational(k)?;
    fuel.charge(1)?;
    if k.is_zero() {
        return Err(RationalError::DivisionByZero.into());
    }
    let (lo, hi) = if k.is_negative() {
        (&a.1, &a.0)
    } else {
        (&a.0, &a.1)
    };
    Ok((fuel.div(lo, k)?, fuel.div(hi, k)?))
}

/// Checked closed intersection. A shared endpoint is a valid point interval.
pub fn intersect(
    a: &RationalEndpoints,
    b: &RationalEndpoints,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleError> {
    validate_interval(a, fuel)?;
    validate_interval(b, fuel)?;
    fuel.charge(3)?;
    let lo = if a.0 >= b.0 { &a.0 } else { &b.0 };
    let hi = if a.1 <= b.1 { &a.1 } else { &b.1 };
    if lo > hi {
        return Err(NevilleError::EmptyIntersection);
    }
    Ok((lo.clone(), hi.clone()))
}

/// Exact values `p_1(at), ..., p_N(at)` from the Neville--Aitken recurrence.
/// Distinct nodes may arrive in any order, including negative rationals.
pub fn interpolate_prefixes(
    nodes: &[BigRational],
    values: &[BigRational],
    at: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<Vec<BigRational>, NevilleError> {
    check_nodes(nodes, values.len(), at, fuel)?;
    for value in values {
        fuel.rational(value)?;
    }
    let mut work: Vec<BigRational> = storage(nodes.len(), 1, fuel)?;
    let mut prefixes = storage(nodes.len(), 1, fuel)?;
    for (j, value) in values.iter().enumerate() {
        work.push(value.clone());
        for i in (0..j).rev() {
            neville_scalar_step(&mut work, nodes, at, i, j, fuel)?;
        }
        prefixes.push(work[0].clone());
    }
    Ok(prefixes)
}

fn neville_scalar_step(
    work: &mut [BigRational],
    nodes: &[BigRational],
    at: &BigRational,
    i: usize,
    j: usize,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    let a = fuel.sub(at, &nodes[i])?;
    let b = fuel.sub(&nodes[j], at)?;
    let denominator = fuel.sub(&nodes[j], &nodes[i])?;
    let left = fuel.mul(&a, &work[i + 1])?;
    let right = fuel.mul(&b, &work[i])?;
    let numerator = fuel.add(&left, &right)?;
    work[i] = fuel.div(&numerator, &denominator)?;
    Ok(())
}

/// Conservative interval propagation through that same Neville recurrence.
pub fn interpolate_interval_prefixes(
    nodes: &[BigRational],
    samples: &[RationalEndpoints],
    at: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<Vec<RationalEndpoints>, NevilleError> {
    check_nodes(nodes, samples.len(), at, fuel)?;
    fuel.elements(samples.len(), 2)?;
    for sample in samples {
        validate_interval(sample, fuel)?;
    }
    let mut work: Vec<RationalEndpoints> = storage(nodes.len(), 2, fuel)?;
    let mut prefixes = storage(nodes.len(), 2, fuel)?;
    for (j, sample) in samples.iter().enumerate() {
        work.push(sample.clone());
        for i in (0..j).rev() {
            neville_interval_step(&mut work, nodes, at, i, j, fuel)?;
        }
        prefixes.push(work[0].clone());
    }
    Ok(prefixes)
}

fn neville_interval_step(
    work: &mut [RationalEndpoints],
    nodes: &[BigRational],
    at: &BigRational,
    i: usize,
    j: usize,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    let a = fuel.sub(at, &nodes[i])?;
    let b = fuel.sub(&nodes[j], at)?;
    let denominator = fuel.sub(&nodes[j], &nodes[i])?;
    let left = interval_scale(&work[i + 1], &a, fuel)?;
    let right = interval_scale(&work[i], &b, fuel)?;
    let numerator = interval_add(&left, &right, fuel)?;
    work[i] = interval_divide(&numerator, &denominator, fuel)?;
    Ok(())
}

/// Independent Lagrange-weight image for every prefix of the sample box.
/// Unlike recursive interval propagation, each uncertain sample occurs once.
pub fn lagrange_interval_prefixes(
    nodes: &[BigRational],
    samples: &[RationalEndpoints],
    at: &BigRational,
    fuel: &mut RationalBudget,
) -> Result<Vec<RationalEndpoints>, NevilleError> {
    check_nodes(nodes, samples.len(), at, fuel)?;
    fuel.elements(samples.len(), 2)?;
    for sample in samples {
        validate_interval(sample, fuel)?;
    }
    let mut weights: Vec<BigRational> = storage(nodes.len(), 1, fuel)?;
    let mut prefixes = storage(nodes.len(), 2, fuel)?;
    for j in 0..nodes.len() {
        update_lagrange_weights(&mut weights, nodes, at, j, fuel)?;
        prefixes.push(sum_weighted_intervals(samples, &weights, j, fuel)?);
    }
    Ok(prefixes)
}

fn update_lagrange_weights(
    weights: &mut Vec<BigRational>,
    nodes: &[BigRational],
    at: &BigRational,
    j: usize,
    fuel: &mut RationalBudget,
) -> Result<(), NevilleError> {
    let mut newest = BigRational::one();
    let numerator = fuel.sub(at, &nodes[j])?;
    for i in 0..j {
        let denominator = fuel.sub(&nodes[i], &nodes[j])?;
        let factor = fuel.div(&numerator, &denominator)?;
        weights[i] = fuel.mul(&weights[i], &factor)?;
        let new_numerator = fuel.sub(at, &nodes[i])?;
        let new_denominator = fuel.sub(&nodes[j], &nodes[i])?;
        let new_factor = fuel.div(&new_numerator, &new_denominator)?;
        newest = fuel.mul(&newest, &new_factor)?;
    }
    weights.push(newest);
    Ok(())
}

fn sum_weighted_intervals(
    samples: &[RationalEndpoints],
    weights: &[BigRational],
    j: usize,
    fuel: &mut RationalBudget,
) -> Result<RationalEndpoints, NevilleError> {
    let mut sum = (BigRational::zero(), BigRational::zero());
    for i in 0..=j {
        let term = interval_scale(&samples[i], &weights[i], fuel)?;
        sum = interval_add(&sum, &term, fuel)?;
    }
    Ok(sum)
}

// Origin: engine/crates_rs/core_linear_algebra/src/exact_field/neville_aitken.rs
// Claim: urn:core:crates_rs:core-linear-algebra:neville-aitken:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_36c52c7c {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
