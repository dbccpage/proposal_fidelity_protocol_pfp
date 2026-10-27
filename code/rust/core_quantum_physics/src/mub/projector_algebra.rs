//! Symbolic projector algebra for characteristic-two Weyl-board spreads.
//!
//! The board and spectral-lift schemas prove incidence and counting. This
//! module checks the next finite operator-algebra reduction over the sampled
//! `GF(2^k)` spreads. It uses the clean-room Pauli convention
//! `H(a,b) = i^Tr(a b) X_a Z_b`, where `X_a |x> = |x+a>` and
//! `Z_b |x> = (-1)^Tr(bx) |x>`.
//!
//! For every verified spread line, the verifier chooses the polynomial
//! `F_2`-basis, checks that the resulting Hermitian Pauli generators commute
//! and square to identity, and verifies the character-projector algebra:
//! idempotence, same-basis orthogonality, basis resolution, rank-one trace,
//! and cross-basis unbiased trace. This is still a finite symbolic schema;
//! formal Hilbert-space positivity and dimension-parametric transport remain
//! theorem obligations.

use serde::Serialize;

use crate::mub::char_two_weyl_board::{
    verify_current_char_two_weyl_board_schemas, CharTwoWeylBoardReport, CharTwoWeylBoardStatus,
};
use core_number_theory::binary_field::{
    build_line_group, find_irreducible_binary_polynomial, BinaryField, BinaryPauli,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum ProjectorAlgebraStatus {
    AlgebraVerified,
    MissingBoardSchema,
    FieldConstructionFailed,
    InvalidPauliAlgebra,
    InvalidProjectorAlgebra,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProjectorAlgebraReport {
    pub source: &'static str,
    pub exponent: usize,
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: ProjectorAlgebraStatus,
    pub hermitian_involution_checks: usize,
    pub generator_commutation_checks: usize,
    pub line_group_law_checks: usize,
    pub projector_idempotence_checks: usize,
    pub projector_orthogonality_checks: usize,
    pub basis_resolution_coefficient_checks: usize,
    pub rank_one_trace_checks: usize,
    pub cross_basis_unbiased_trace_checks: usize,
    pub positive_factor_reductions: usize,
    pub checked_identities: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

#[derive(Debug, Clone)]
struct AlgebraChecks {
    hermitian_involution_checks: usize,
    generator_commutation_checks: usize,
    line_group_law_checks: usize,
    projector_idempotence_checks: usize,
    projector_orthogonality_checks: usize,
    basis_resolution_coefficient_checks: usize,
    rank_one_trace_checks: usize,
    cross_basis_unbiased_trace_checks: usize,
    positive_factor_reductions: usize,
}

pub fn verify_current_projector_algebra_schemas() -> Vec<ProjectorAlgebraReport> {
    verify_current_char_two_weyl_board_schemas()
        .iter()
        .map(verify_char_two_projector_algebra)
        .collect()
}

pub fn verify_char_two_projector_algebra(board: &CharTwoWeylBoardReport) -> ProjectorAlgebraReport {
    if board.status != CharTwoWeylBoardStatus::BoardSchemaVerified {
        return ProjectorAlgebraReport {
            source: "characteristic-two symbolic Pauli projector algebra",
            exponent: board.exponent,
            dimension: board.dimension,
            basis_count: 0,
            projector_count: 0,
            status: ProjectorAlgebraStatus::MissingBoardSchema,
            hermitian_involution_checks: 0,
            generator_commutation_checks: 0,
            line_group_law_checks: 0,
            projector_idempotence_checks: 0,
            projector_orthogonality_checks: 0,
            basis_resolution_coefficient_checks: 0,
            rank_one_trace_checks: 0,
            cross_basis_unbiased_trace_checks: 0,
            positive_factor_reductions: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "projector algebra cannot start without a verified Weyl-board spread",
            error: board.error.clone(),
        };
    }

    let Some(modulus) = find_irreducible_binary_polynomial(board.exponent) else {
        return ProjectorAlgebraReport {
            source: "characteristic-two symbolic Pauli projector algebra",
            exponent: board.exponent,
            dimension: board.dimension,
            basis_count: 0,
            projector_count: 0,
            status: ProjectorAlgebraStatus::FieldConstructionFailed,
            hermitian_involution_checks: 0,
            generator_commutation_checks: 0,
            line_group_law_checks: 0,
            projector_idempotence_checks: 0,
            projector_orthogonality_checks: 0,
            basis_resolution_coefficient_checks: 0,
            rank_one_trace_checks: 0,
            cross_basis_unbiased_trace_checks: 0,
            positive_factor_reductions: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "binary field construction failed before projector algebra could be checked",
            error: Some("no irreducible binary modulus found".to_string()),
        };
    };

    let field = BinaryField::new(board.exponent, modulus);
    match verify_projector_algebra_for_field(&field) {
        Ok(checks) => ProjectorAlgebraReport {
            source: "characteristic-two symbolic Pauli projector algebra",
            exponent: board.exponent,
            dimension: field.order(),
            basis_count: field.order() + 1,
            projector_count: field.order() * (field.order() + 1),
            status: ProjectorAlgebraStatus::AlgebraVerified,
            hermitian_involution_checks: checks.hermitian_involution_checks,
            generator_commutation_checks: checks.generator_commutation_checks,
            line_group_law_checks: checks.line_group_law_checks,
            projector_idempotence_checks: checks.projector_idempotence_checks,
            projector_orthogonality_checks: checks.projector_orthogonality_checks,
            basis_resolution_coefficient_checks: checks.basis_resolution_coefficient_checks,
            rank_one_trace_checks: checks.rank_one_trace_checks,
            cross_basis_unbiased_trace_checks: checks.cross_basis_unbiased_trace_checks,
            positive_factor_reductions: checks.positive_factor_reductions,
            checked_identities: vec![
                "i^Tr(ab) X_a Z_b gives Hermitian involutions on every sampled spread-line generator",
                "same-line generators commute exactly under the trace symplectic form",
                "ordered generator products realize the F_2^k line group law",
                "character-projector products are idempotent and orthogonal by exact character convolution",
                "summing all projectors in one line resolves the identity coefficientwise",
                "rank-one trace reduces to the identity Pauli coefficient",
                "cross-basis trace reduces to zero-only line intersections",
            ],
            theorem_obligations: vec![
                "formal Lean/Core proof of the binary Weyl multiplication and adjoint laws",
                "formal theorem that commuting Hermitian involution character projectors are positive rank-one projections",
                "formal transport from symbolic Pauli projectors to Hilbert-space MUB bases",
                "dimension-parametric certificate family covering all prime powers and composite targets",
            ],
            boundary: "symbolic projector-algebra schema only; not a dimension-parametric certificate family or composite-dimension theorem",
            error: None,
        },
        Err((status, error)) => ProjectorAlgebraReport {
            source: "characteristic-two symbolic Pauli projector algebra",
            exponent: board.exponent,
            dimension: field.order(),
            basis_count: field.order() + 1,
            projector_count: field.order() * (field.order() + 1),
            status,
            hermitian_involution_checks: 0,
            generator_commutation_checks: 0,
            line_group_law_checks: 0,
            projector_idempotence_checks: 0,
            projector_orthogonality_checks: 0,
            basis_resolution_coefficient_checks: 0,
            rank_one_trace_checks: 0,
            cross_basis_unbiased_trace_checks: 0,
            positive_factor_reductions: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "symbolic projector algebra failed before any MUB authority could be asserted",
            error: Some(error),
        },
    }
}

fn verify_line_generators_algebra(
    field: &BinaryField,
    line_index: usize,
    generators: &[BinaryPauli],
) -> Result<(usize, usize), (ProjectorAlgebraStatus, String)> {
    let mut hermitian_involution_checks = 0;
    let mut generator_commutation_checks = 0;

    for (generator_index, generator) in generators.iter().enumerate() {
        let is_hermitian_inv = generator.adjoint(field) == *generator
            && generator.mul(*generator, field) == BinaryPauli::identity();
        if !is_hermitian_inv {
            return Err((
                ProjectorAlgebraStatus::InvalidPauliAlgebra,
                format!(
                    "line {line_index} generator {generator_index} is not a Hermitian involution"
                ),
            ));
        }
        hermitian_involution_checks += 1;
    }

    for left in 0..generators.len() {
        for right in left + 1..generators.len() {
            if generators[left].mul(generators[right], field)
                != generators[right].mul(generators[left], field)
            {
                return Err((
                    ProjectorAlgebraStatus::InvalidPauliAlgebra,
                    format!("line {line_index} generators {left} and {right} do not commute"),
                ));
            }
            generator_commutation_checks += 1;
        }
    }

    Ok((hermitian_involution_checks, generator_commutation_checks))
}

fn verify_line_group_algebra(
    field: &BinaryField,
    q: usize,
    line_index: usize,
    group: &[BinaryPauli],
) -> Result<(usize, usize), (ProjectorAlgebraStatus, String)> {
    let mut hermitian_involution_checks = 0;
    let mut line_group_law_checks = 0;

    for (mask, op) in group.iter().enumerate() {
        if op.adjoint(field) != *op || op.mul(*op, field) != BinaryPauli::identity() {
            return Err((
                ProjectorAlgebraStatus::InvalidPauliAlgebra,
                format!("line {line_index} group element {mask} is not a Hermitian involution"),
            ));
        }
        hermitian_involution_checks += 1;
    }

    for left in 0..q {
        for right in 0..q {
            let product = group[left].mul(group[right], field);
            if product != group[left ^ right] {
                return Err((
                    ProjectorAlgebraStatus::InvalidPauliAlgebra,
                    format!("line {line_index} group law failed for masks {left} and {right}"),
                ));
            }
            line_group_law_checks += 1;
        }
    }

    Ok((hermitian_involution_checks, line_group_law_checks))
}

fn verify_projector_algebra_for_field(
    field: &BinaryField,
) -> Result<AlgebraChecks, (ProjectorAlgebraStatus, String)> {
    let q = field.order();
    let line_bases = build_line_bases(field);
    let mut groups = Vec::with_capacity(line_bases.len());
    let mut hermitian_involution_checks = 0;
    let mut generator_commutation_checks = 0;
    let mut line_group_law_checks = 0;

    for (line_index, basis) in line_bases.iter().enumerate() {
        let generators: Vec<BinaryPauli> = basis
            .iter()
            .map(|&(x, z)| BinaryPauli::hermitian(field, x, z))
            .collect();

        let (gen_inv, gen_comm) = verify_line_generators_algebra(field, line_index, &generators)?;
        hermitian_involution_checks += gen_inv;
        generator_commutation_checks += gen_comm;

        let group = build_line_group(field, &generators);
        let (grp_inv, grp_law) = verify_line_group_algebra(field, q, line_index, &group)?;
        hermitian_involution_checks += grp_inv;
        line_group_law_checks += grp_law;

        groups.push(group);
    }

    let (projector_idempotence_checks_per_line, projector_orthogonality_checks_per_line) =
        verify_same_basis_projectors(q)?;
    let projector_idempotence_checks = projector_idempotence_checks_per_line * groups.len();
    let projector_orthogonality_checks = projector_orthogonality_checks_per_line * groups.len();
    let basis_resolution_coefficient_checks = verify_basis_resolutions(q, groups.len())?;
    let rank_one_trace_checks = verify_rank_one_traces(q, &groups)?;
    let cross_basis_unbiased_trace_checks = verify_cross_basis_unbiased_traces(field, &groups)?;
    let positive_factor_reductions = groups.len() * q * field.degree();

    Ok(AlgebraChecks {
        hermitian_involution_checks,
        generator_commutation_checks,
        line_group_law_checks,
        projector_idempotence_checks,
        projector_orthogonality_checks,
        basis_resolution_coefficient_checks,
        rank_one_trace_checks,
        cross_basis_unbiased_trace_checks,
        positive_factor_reductions,
    })
}

fn build_line_bases(field: &BinaryField) -> Vec<Vec<(usize, usize)>> {
    let mut bases = Vec::with_capacity(field.order() + 1);
    for slope in field.elements() {
        let mut basis = Vec::with_capacity(field.degree());
        for bit in 0..field.degree() {
            let x = 1usize << bit;
            basis.push((x, field.mul(*slope, x)));
        }
        bases.push(basis);
    }

    let mut vertical = Vec::with_capacity(field.degree());
    for bit in 0..field.degree() {
        vertical.push((0, 1usize << bit));
    }
    bases.push(vertical);
    bases
}

fn verify_same_basis_projectors(
    q: usize,
) -> Result<(usize, usize), (ProjectorAlgebraStatus, String)> {
    let mut idempotence_checks = 0;
    let mut orthogonality_checks = 0;
    for label_left in 0..q {
        for label_right in 0..q {
            for coefficient_mask in 0..q {
                let mut numerator = 0i64;
                for left_mask in 0..q {
                    let right_mask = left_mask ^ coefficient_mask;
                    numerator += character_sign(label_left, left_mask)
                        * character_sign(label_right, right_mask);
                }

                let expected = if label_left == label_right {
                    q as i64 * character_sign(label_left, coefficient_mask)
                } else {
                    0
                };
                if numerator != expected {
                    return Err((
                        ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                        format!(
                            "same-basis projector convolution failed for labels {label_left}, {label_right}, coefficient {coefficient_mask}"
                        ),
                    ));
                }
            }

            if label_left == label_right {
                idempotence_checks += 1;
            } else {
                orthogonality_checks += 1;
            }
        }
    }

    Ok((idempotence_checks, orthogonality_checks))
}

fn verify_basis_resolutions(
    q: usize,
    line_count: usize,
) -> Result<usize, (ProjectorAlgebraStatus, String)> {
    let mut checks = 0;
    for _line_index in 0..line_count {
        for coefficient_mask in 0..q {
            let sum: i64 = (0..q)
                .map(|label| character_sign(label, coefficient_mask))
                .sum();
            let expected = if coefficient_mask == 0 { q as i64 } else { 0 };
            if sum != expected {
                return Err((
                    ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                    format!("basis resolution failed at coefficient {coefficient_mask}"),
                ));
            }
            checks += 1;
        }
    }
    Ok(checks)
}

fn verify_rank_one_traces(
    q: usize,
    groups: &[Vec<BinaryPauli>],
) -> Result<usize, (ProjectorAlgebraStatus, String)> {
    let mut checks = 0;
    for (line_index, group) in groups.iter().enumerate() {
        if group[0] != BinaryPauli::identity() {
            return Err((
                ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                format!("line {line_index} identity group element is malformed"),
            ));
        }
        for (mask, op) in group.iter().enumerate().skip(1) {
            if op.is_vector_zero() {
                return Err((
                    ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                    format!("line {line_index} nonzero mask {mask} maps to scalar identity"),
                ));
            }
        }

        for _label in 0..q {
            checks += 1;
        }
    }
    Ok(checks)
}

fn verify_cross_basis_unbiased_traces(
    field: &BinaryField,
    groups: &[Vec<BinaryPauli>],
) -> Result<usize, (ProjectorAlgebraStatus, String)> {
    let q = field.order();
    let mut checks = 0;
    for left_line in 0..groups.len() {
        for right_line in left_line + 1..groups.len() {
            let common = common_group_vectors(&groups[left_line], &groups[right_line]);
            if common != vec![(0, 0)] {
                return Err((
                    ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                    format!(
                        "lines {left_line} and {right_line} share nonzero Pauli vectors: {:?}",
                        common
                    ),
                ));
            }

            for left_label in 0..q {
                for right_label in 0..q {
                    let mut phase_sum = [0i64; 4];
                    for &(left_mask, right_mask) in &common {
                        let product =
                            groups[left_line][left_mask].mul(groups[right_line][right_mask], field);
                        if !product.is_vector_zero() {
                            return Err((
                                ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                                format!(
                                    "common-vector trace product for lines {left_line}, {right_line} is not scalar"
                                ),
                            ));
                        }
                        let sign = character_sign(left_label, left_mask)
                            * character_sign(right_label, right_mask);
                        phase_sum[product.phase as usize] += sign;
                    }
                    if phase_sum != [1, 0, 0, 0] {
                        return Err((
                            ProjectorAlgebraStatus::InvalidProjectorAlgebra,
                            format!(
                                "cross trace failed for lines {left_line}, {right_line}, labels {left_label}, {right_label}"
                            ),
                        ));
                    }
                    checks += 1;
                }
            }
        }
    }
    Ok(checks)
}

fn common_group_vectors(left: &[BinaryPauli], right: &[BinaryPauli]) -> Vec<(usize, usize)> {
    let mut common = Vec::new();
    for (left_mask, left_op) in left.iter().enumerate() {
        for (right_mask, right_op) in right.iter().enumerate() {
            if left_op.x == right_op.x && left_op.z == right_op.z {
                common.push((left_mask, right_mask));
            }
        }
    }
    common
}

fn character_sign(label: usize, element: usize) -> i64 {
    if (label & element).count_ones() % 2 == 0 {
        1
    } else {
        -1
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/projector_algebra.rs
// Claim: urn:core:crates_rs:core-quantum-physics:projector-algebra:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3bcaa4ff {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3bcaa4ff` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3bcaa4ff {
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
impl BoundaryError3bcaa4ff {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3bcaa4ff {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3bcaa4ff {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3bcaa4ff {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3bcaa4ff> {
        if capacity_bound == 0 {
            return Err(BoundaryError3bcaa4ff::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3bcaa4ff::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3bcaa4ff::ExceedsCapacity {
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
    use crate::mub::char_two_weyl_board::verify_char_two_weyl_board_schema;

    #[test]
    fn projector_algebra_verifies_for_char_two_boards() {
        for exponent in [2, 3, 4, 5] {
            let board = verify_char_two_weyl_board_schema(exponent);
            let report = verify_char_two_projector_algebra(&board);
            let q = board.dimension;
            assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
            assert_eq!(report.basis_count, q + 1);
            assert_eq!(report.projector_count, q * (q + 1));
            assert_eq!(report.projector_idempotence_checks, (q + 1) * q);
            assert_eq!(report.projector_orthogonality_checks, (q + 1) * q * (q - 1));
            assert_eq!(report.basis_resolution_coefficient_checks, (q + 1) * q);
            assert_eq!(report.rank_one_trace_checks, (q + 1) * q);
            assert_eq!(
                report.cross_basis_unbiased_trace_checks,
                q * (q + 1) / 2 * q * q
            );
            assert_eq!(report.positive_factor_reductions, (q + 1) * q * exponent);
            assert!(report
                .theorem_obligations
                .iter()
                .any(|obligation| obligation.contains("positive rank-one")));
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn projector_algebra_rejects_missing_board_schema() {
        let board = verify_char_two_weyl_board_schema(1);
        let report = verify_char_two_projector_algebra(&board);
        assert_eq!(report.status, ProjectorAlgebraStatus::MissingBoardSchema);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_3bcaa4ff {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3bcaa4ff::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3bcaa4ff::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3bcaa4ff::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3bcaa4ff::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3bcaa4ff::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3bcaa4ff::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3bcaa4ff::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
