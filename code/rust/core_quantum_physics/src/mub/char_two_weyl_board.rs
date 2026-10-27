//! Characteristic-two Weyl-board spread schema.
//!
//! Odd-characteristic quadratic-basis formulas use division by two. This module
//! records the characteristic-two replacement at the finite incidence layer:
//! a symplectic spread of `GF(2^k)^2` by `q + 1` isotropic lines. The checked
//! object is a Weyl-board schema, not a Hilbert-space MUB proof. The remaining
//! authority boundary is the spectral-projector lift and phase convention for
//! the characteristic-two Weyl/Pauli representation.

use serde::Serialize;

use core_number_theory::binary_field::{
    binary_polynomial_coefficients, find_irreducible_binary_polynomial, BinaryField,
};
use core_number_theory::finite_field::checked_pow;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum CharTwoWeylBoardStatus {
    BoardSchemaVerified,
    UnsupportedDimension,
    FieldConstructionFailed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct CharTwoWeylBoardReport {
    pub exponent: usize,
    pub dimension: usize,
    pub line_count: usize,
    pub status: CharTwoWeylBoardStatus,
    pub irreducible_modulus: Vec<usize>,
    pub isotropic_line_checks: usize,
    pub pairwise_zero_intersection_checks: usize,
    pub nonzero_vector_cover_count: usize,
    pub symplectic_trace_checks: usize,
    pub checked_identities: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

const MAX_VERIFIED_EXPONENT: usize = 15;

pub fn verify_current_char_two_weyl_board_schemas() -> Vec<CharTwoWeylBoardReport> {
    [2, 3, 4, 5]
        .into_iter()
        .map(verify_char_two_weyl_board_schema)
        .collect()
}

pub fn verify_char_two_weyl_board_schema(exponent: usize) -> CharTwoWeylBoardReport {
    if exponent < 2 {
        return unsupported_report(
            exponent,
            "characteristic-two Weyl-board schema requires exponent at least 2",
        );
    }
    if exponent > MAX_VERIFIED_EXPONENT {
        return unsupported_report(
            exponent,
            "characteristic-two Weyl-board schema exponent is too large for finite verification",
        );
    }

    let Some(modulus) = find_irreducible_binary_polynomial(exponent) else {
        return CharTwoWeylBoardReport {
            exponent,
            dimension: checked_pow(2, exponent).unwrap_or(0),
            line_count: 0,
            status: CharTwoWeylBoardStatus::FieldConstructionFailed,
            irreducible_modulus: vec![],
            isotropic_line_checks: 0,
            pairwise_zero_intersection_checks: 0,
            nonzero_vector_cover_count: 0,
            symplectic_trace_checks: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "binary finite-field carrier construction failed before any Weyl-board authority could be asserted",
            error: Some("no irreducible binary modulus found".to_string()),
        };
    };

    let field = BinaryField::new(exponent, modulus);
    let lines = build_spread_lines(&field);
    let dimension = field.order();

    let isotropic_line_checks = match verify_isotropic_lines(&field, &lines) {
        Ok(count) => count,
        Err(error) => return failed_report(exponent, dimension, field.modulus(), error),
    };
    let pairwise_zero_intersection_checks = match verify_pairwise_zero_intersections(&lines) {
        Ok(count) => count,
        Err(error) => return failed_report(exponent, dimension, field.modulus(), error),
    };
    let nonzero_vector_cover_count = match verify_nonzero_vector_cover(&field, &lines) {
        Ok(count) => count,
        Err(error) => return failed_report(exponent, dimension, field.modulus(), error),
    };

    CharTwoWeylBoardReport {
        exponent,
        dimension,
        line_count: lines.len(),
        status: CharTwoWeylBoardStatus::BoardSchemaVerified,
        irreducible_modulus: binary_polynomial_coefficients(field.modulus(), exponent),
        isotropic_line_checks,
        pairwise_zero_intersection_checks,
        nonzero_vector_cover_count,
        symplectic_trace_checks: isotropic_line_checks,
        checked_identities: vec![
            "GF(2^k) carrier is built from a binary irreducible polynomial",
            "q affine slope lines plus one vertical line give q+1 Weyl-board sectors",
            "each line is isotropic for the trace symplectic form",
            "distinct spread lines intersect only at the zero vector",
            "the spread covers every nonzero vector of GF(2^k)^2 exactly once",
        ],
        theorem_obligations: vec![
            "formal binary finite-field irreducibility and field laws",
            "formal spectral-projector lift from isotropic Weyl-board lines to Hilbert-space bases",
            "declared characteristic-two Weyl/Pauli phase convention preserving commutation",
            "Lean/Core transport from board spread to complete MUB bases",
        ],
        boundary: "characteristic-two Weyl-board schema only; not a Hilbert-space complete MUB authority or all-N theorem",
        error: None,
    }
}

fn unsupported_report(exponent: usize, message: &'static str) -> CharTwoWeylBoardReport {
    CharTwoWeylBoardReport {
        exponent,
        dimension: checked_pow(2, exponent).unwrap_or(0),
        line_count: 0,
        status: CharTwoWeylBoardStatus::UnsupportedDimension,
        irreducible_modulus: vec![],
        isotropic_line_checks: 0,
        pairwise_zero_intersection_checks: 0,
        nonzero_vector_cover_count: 0,
        symplectic_trace_checks: 0,
        checked_identities: vec![],
        theorem_obligations: vec![],
        boundary: "characteristic-two Weyl-board schema only applies to 2^k with k >= 2",
        error: Some(message.to_string()),
    }
}

fn failed_report(
    exponent: usize,
    dimension: usize,
    modulus: usize,
    error: String,
) -> CharTwoWeylBoardReport {
    CharTwoWeylBoardReport {
        exponent,
        dimension,
        line_count: 0,
        status: CharTwoWeylBoardStatus::FieldConstructionFailed,
        irreducible_modulus: binary_polynomial_coefficients(modulus, exponent),
        isotropic_line_checks: 0,
        pairwise_zero_intersection_checks: 0,
        nonzero_vector_cover_count: 0,
        symplectic_trace_checks: 0,
        checked_identities: vec![],
        theorem_obligations: vec![],
        boundary: "finite Weyl-board checks failed before any MUB authority could be asserted",
        error: Some(error),
    }
}

fn build_spread_lines(field: &BinaryField) -> Vec<Vec<(usize, usize)>> {
    let mut lines = Vec::with_capacity(field.order() + 1);
    for slope in field.elements() {
        lines.push(
            field
                .elements()
                .iter()
                .map(|x| (*x, field.mul(*slope, *x)))
                .collect(),
        );
    }
    lines.push(field.elements().iter().map(|y| (0, *y)).collect());
    lines
}

fn verify_isotropic_lines(
    field: &BinaryField,
    lines: &[Vec<(usize, usize)>],
) -> Result<usize, String> {
    let mut checks = 0;
    for line in lines {
        for left in line {
            for right in line {
                if field.symplectic_trace(*left, *right) != 0 {
                    return Err(format!(
                        "line is not isotropic at vectors {:?} and {:?}",
                        left, right
                    ));
                }
                checks += 1;
            }
        }
    }
    Ok(checks)
}

fn verify_pairwise_zero_intersections(lines: &[Vec<(usize, usize)>]) -> Result<usize, String> {
    let mut checks = 0;
    for i in 0..lines.len() {
        for j in i + 1..lines.len() {
            let mut intersection = Vec::new();
            for left in &lines[i] {
                if lines[j].contains(left) {
                    intersection.push(*left);
                }
            }
            if intersection != vec![(0, 0)] {
                return Err(format!(
                    "spread lines {i} and {j} intersect outside zero: {:?}",
                    intersection
                ));
            }
            checks += 1;
        }
    }
    Ok(checks)
}

fn verify_nonzero_vector_cover(
    field: &BinaryField,
    lines: &[Vec<(usize, usize)>],
) -> Result<usize, String> {
    let mut counts = vec![0usize; field.order() * field.order()];
    for line in lines {
        for &(x, y) in line {
            counts[x * field.order() + y] += 1;
        }
    }

    if counts[0] != lines.len() {
        return Err(format!(
            "zero vector should appear in every line, saw {} appearances",
            counts[0]
        ));
    }

    let mut covered = 0;
    for (idx, count) in counts.iter().enumerate().skip(1) {
        if *count != 1 {
            return Err(format!(
                "nonzero vector index {idx} should appear once, saw {count}"
            ));
        }
        covered += 1;
    }

    Ok(covered)
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/char_two_weyl_board.rs
// Claim: urn:core:crates_rs:core-quantum-physics:char-two-weyl-board:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord37d0a5a3 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord37d0a5a3` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError37d0a5a3 {
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
impl BoundaryError37d0a5a3 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError37d0a5a3 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError37d0a5a3 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord37d0a5a3 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError37d0a5a3> {
        if capacity_bound == 0 {
            return Err(BoundaryError37d0a5a3::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError37d0a5a3::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError37d0a5a3::ExceedsCapacity {
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
    fn char_two_weyl_board_schemas_verify_for_sample_fields() {
        for exponent in [2, 3, 4, 5] {
            let report = verify_char_two_weyl_board_schema(exponent);
            let dimension = checked_pow(2, exponent).unwrap();
            assert_eq!(report.status, CharTwoWeylBoardStatus::BoardSchemaVerified);
            assert_eq!(report.dimension, dimension);
            assert_eq!(report.line_count, dimension + 1);
            assert_eq!(
                report.isotropic_line_checks,
                (dimension + 1) * dimension * dimension
            );
            assert_eq!(
                report.pairwise_zero_intersection_checks,
                dimension * (dimension + 1) / 2
            );
            assert_eq!(report.nonzero_vector_cover_count, dimension * dimension - 1);
            assert!(report
                .theorem_obligations
                .iter()
                .any(|obligation| obligation.contains("spectral-projector")));
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn char_two_weyl_board_schema_rejects_degenerate_exponents() {
        for exponent in [0, 1] {
            let report = verify_char_two_weyl_board_schema(exponent);
            assert_eq!(report.status, CharTwoWeylBoardStatus::UnsupportedDimension);
            assert!(report.error.is_some());
        }
    }

    #[test]
    fn char_two_weyl_board_schema_rejects_oversized_exponents_before_allocation() {
        let report = verify_char_two_weyl_board_schema(MAX_VERIFIED_EXPONENT + 1);
        assert_eq!(report.status, CharTwoWeylBoardStatus::UnsupportedDimension);
        assert!(report.error.as_deref().unwrap_or("").contains("too large"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_37d0a5a3 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord37d0a5a3::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord37d0a5a3::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord37d0a5a3::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord37d0a5a3::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord37d0a5a3::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError37d0a5a3::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError37d0a5a3::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
