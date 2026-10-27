//! Exact tests for the entanglement and separability movement of the finite
//! quantum mechanics programme: product defects of joint tables, separability
//! relative to declared families, the bit-shadow carrier, and finite Bell
//! bounds with no-signalling. One submodule per retired source paper; the
//! paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod bit_shadow;
mod finite_bell_bounds;
mod product_non_factorization;
mod separability_witness;

#[derive(Clone, Debug, PartialEq, Eq)]
enum ProductError {
    Overflow { left_index: usize, right_index: usize },
}

// Origin: engine/crates_rs/tests/core_quantum_physics/entanglement/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for ProductError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for ProductError {}

fn product_mass(left: &[u64], right: &[u64]) -> Result<Vec<u64>, ProductError> {
    let mut masses = Vec::new();
    for (left_index, left_mass) in left.iter().enumerate() {
        for (right_index, right_mass) in right.iter().enumerate() {
            let mass = left_mass.checked_mul(*right_mass).ok_or(ProductError::Overflow {
                left_index,
                right_index,
            })?;
            masses.push(mass);
        }
    }
    Ok(masses)
}

fn is_product_table(table: &[u64], left: &[u64], right: &[u64]) -> Result<bool, ProductError> {
    let expected = product_mass(left, right)?;
    Ok(table == expected.as_slice())
}

#[test]
fn a_rank_one_table_matches_its_factors() {
    let masses = product_mass(&[2, 3], &[4, 5]);
    assert_eq!(masses, Ok(vec![8, 10, 12, 15]));
    if let Ok(masses) = masses {
        assert_eq!(is_product_table(&masses, &[2, 3], &[4, 5]), Ok(true));
    }
}

#[test]
fn a_non_factor_table_is_not_a_product() {
    assert_eq!(is_product_table(&[8, 10, 12, 14], &[2, 3], &[4, 5]), Ok(false));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
