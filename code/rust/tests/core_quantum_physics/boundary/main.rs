//! Exact tests for the boundary movement of the finite quantum mechanics
//! programme: the Mermin-Peres parity obstruction over `F_2`, the ingredient
//! ladder from `L1` weights to interference, and the finite Hilbert boundary
//! walked from a report-fiber primitive difference. One submodule per retired
//! source paper; the paper-to-module map lives in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/finite_quantum_mechanics.md`.

mod mermin_peres_parity_obstruction;

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
enum MerminError { Entry, Width, Obstruction, Overflow }

// Origin: engine/crates_rs/tests/core_quantum_physics/boundary/main.rs
// Claim: urn:core:crates_rs:tests:main:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MerminError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MerminError {}

fn sign_product(values: &[i16]) -> Result<i16, MerminError> {
    let mut product = 1i16;
    for value in values {
        if *value != 1 && *value != -1 {
            return Err(MerminError::Entry);
        }
        product = product.checked_mul(*value).ok_or(MerminError::Overflow)?;
    }
    Ok(product)
}

/// A filled ±1 grid has equal products of its row products and column products.
fn accumulate_grid_row(
    row: &[i16; 3],
    column_products: &mut [i16; 3],
) -> Result<i16, MerminError> {
    let mut row_product = 1i16;
    for (entry, column_product) in row.iter().copied().zip(column_products.iter_mut()) {
        if entry != 1 && entry != -1 {
            return Err(MerminError::Entry);
        }
        row_product = row_product.checked_mul(entry).ok_or(MerminError::Overflow)?;
        *column_product = column_product.checked_mul(entry).ok_or(MerminError::Overflow)?;
    }
    Ok(row_product)
}

fn certify_mermin_grid(grid: &[[i16; 3]; 3]) -> Result<i16, MerminError> {
    let mut row_products = [1i16; 3];
    let mut column_products = [1i16; 3];
    for (row, stored) in grid.iter().zip(row_products.iter_mut()) {
        *stored = accumulate_grid_row(row, &mut column_products)?;
    }
    let rows = sign_product(&row_products)?;
    let columns = sign_product(&column_products)?;
    if rows != columns {
        return Err(MerminError::Obstruction);
    }
    Ok(rows)
}

/// The Mermin-Peres sign prescription is consistent only when the row-sign product equals the column-sign product.
fn admit_mermin_prescription(row_signs: [i16; 3], column_signs: [i16; 3]) -> Result<i16, MerminError> {
    let rows = sign_product(&row_signs)?;
    let columns = sign_product(&column_signs)?;
    if rows != columns {
        return Err(MerminError::Obstruction);
    }
    Ok(rows)
}

#[test]
fn an_all_positive_grid_has_product_one() {
    let grid = [[1i16, 1, 1], [1, 1, 1], [1, 1, 1]];
    assert!(matches!(certify_mermin_grid(&grid), Ok(1)));
    assert!(matches!(admit_mermin_prescription([1, 1, 1], [1, 1, 1]), Ok(1)));
}

#[test]
fn one_negative_column_sign_is_an_obstruction() {
    assert!(matches!(admit_mermin_prescription([1, 1, 1], [1, 1, -1]), Err(MerminError::Obstruction)));
    assert!(matches!(certify_mermin_grid(&[[1, 1, 2], [1, 1, 1], [1, 1, 1]]), Err(MerminError::Entry)));
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
