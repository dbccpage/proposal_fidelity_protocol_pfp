//! Exact tests for the repair-capacity and gravity movement of the finite
//! quantum mechanics programme: threshold theorems read as conditional
//! repair-capacity certificates, distance and correction radius of declared
//! codes, the show-the-packet checker, and finite kinematical shadows of loop
//! quantum gravity and general relativity. One submodule per retired source
//! paper; the paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::GaussianRat;

mod support;

mod general_relativity_kinematical_shadows;
mod loop_quantum_gravity_kinematical_shadows;
mod threshold_repair_certificates;

// Exact invariant envelope.
// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/main.rs
// Claim: urn:core:quantum:repair:quaternion-relation:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
struct QuaternionRelation {
    order: u64,
    fiber: u64,
}

#[derive(Debug, Clone, PartialEq, Eq)]
enum QuaternionError {
    Order,
    Index,
    Fiber,
    Product,
    Square,
    ProductRule,
    Commutator,
}

// Origin: engine/crates_rs/tests/core_quantum_physics/repair_and_gravity/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for QuaternionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for QuaternionError {}

fn verify_quaternion_products(
    i: &BasicMatrix<GaussianRat>,
    j: &BasicMatrix<GaussianRat>,
    k: &BasicMatrix<GaussianRat>,
    minus: &BasicMatrix<GaussianRat>,
    minus_k: &BasicMatrix<GaussianRat>,
) -> Result<(), QuaternionError> {
    if i.rows() != 2 || i.cols() != 2 {
        return Err(QuaternionError::Fiber);
    }
    if &i.mul(i).map_err(|_| QuaternionError::Product)? != minus {
        return Err(QuaternionError::Square);
    }
    if &i.mul(j).map_err(|_| QuaternionError::Product)? != k {
        return Err(QuaternionError::ProductRule);
    }
    if &j.mul(i).map_err(|_| QuaternionError::Product)? != minus_k {
        return Err(QuaternionError::Commutator);
    }
    Ok(())
}

fn get_qmat(
    group: &[BasicMatrix<GaussianRat>],
    index: usize,
) -> Result<&BasicMatrix<GaussianRat>, QuaternionError> {
    group.get(index).ok_or(QuaternionError::Index)
}

fn verify_group_relations(
    group: &[BasicMatrix<GaussianRat>],
    minus_k_idx: usize,
) -> Result<(), QuaternionError> {
    verify_quaternion_products(
        get_qmat(group, support::I)?,
        get_qmat(group, support::J)?,
        get_qmat(group, support::K)?,
        get_qmat(group, support::MINUS_ONE)?,
        get_qmat(group, minus_k_idx)?,
    )
}

fn try_quaternion_relation() -> Result<QuaternionRelation, QuaternionError> {
    let group = support::quaternion_group();
    let span = support::K.checked_add(2).ok_or(QuaternionError::Order)?;
    if group.len() != span {
        return Err(QuaternionError::Order);
    }
    let minus_k_idx = support::K.checked_add(1).ok_or(QuaternionError::Order)?;
    verify_group_relations(&group, minus_k_idx)?;
    let order = u64::try_from(span).map_err(|_| QuaternionError::Order)?;
    Ok(QuaternionRelation { order, fiber: 2 })
}

#[test]
fn the_support_quaternion_group_obeys_ij_equals_k() {
    let relation = try_quaternion_relation();
    assert!(matches!(relation, Ok(ref row) if row.order == 8 && row.fiber == 2));
}

#[test]
fn a_short_index_span_is_not_the_group_order() {
    let span = support::K.checked_add(1);
    assert!(matches!(span, Some(7)));
    assert!(support::K.checked_add(2) != Some(support::quaternion_group().len().saturating_sub(1)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
