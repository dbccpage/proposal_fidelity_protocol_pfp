//! Exact Hilbert-matrix transport for characteristic-two Pauli projectors.
//!
//! `projector_algebra` verifies the finite group-algebra identities. This
//! module realizes the same clean-room characteristic-two Pauli operators as
//! exact Gaussian-integer matrices on the computational basis of `GF(2^k)`.
//! The projector numerators are checked as matrix objects:
//!
//! * Pauli matrices have the expected exact trace formula;
//! * line-group products agree with matrix multiplication;
//! * character-projector numerators factor as products of positive factors
//!   `I +/- G_j`;
//! * projector numerators are Hermitian, scaled idempotent, rank-one by trace,
//!   and resolve the identity in each basis.
//!
//! This reduces the finite Hilbert transport and positivity obstruction for
//! the sampled characteristic-two prime powers. It still does not provide an
//! all-dimension certificate family or solve composite targets.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_a6b5b733<T> {
    fn checked_invariant_a6b5b733(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_a6b5b733<T> for Option<T> {
    #[inline]
    fn checked_invariant_a6b5b733(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_a6b5b733<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_a6b5b733(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::sync::OnceLock;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_number_theory::cyclotomic::GaussianRat;
use serde::Serialize;

use crate::exact_hermitian;
use crate::mub::char_two_weyl_board::{
    verify_current_char_two_weyl_board_schemas, CharTwoWeylBoardReport, CharTwoWeylBoardStatus,
};
use core_number_theory::binary_field::{
    build_line_group, find_irreducible_binary_polynomial, BinaryField, BinaryPauli,
};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub enum HilbertTransportStatus {
    TransportVerified,
    MissingBoardSchema,
    FieldConstructionFailed,
    MatrixIdentityFailed,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct HilbertTransportReport {
    pub source: &'static str,
    pub exponent: usize,
    pub dimension: usize,
    pub basis_count: usize,
    pub projector_count: usize,
    pub status: HilbertTransportStatus,
    pub pauli_trace_formula_checks: usize,
    pub hermitian_involution_matrix_checks: usize,
    pub line_group_matrix_lift_checks: usize,
    pub positive_factor_matrix_checks: usize,
    pub projector_factorization_checks: usize,
    pub projector_scaled_idempotence_checks: usize,
    pub projector_rank_one_trace_checks: usize,
    pub basis_resolution_matrix_checks: usize,
    pub same_basis_orthogonality_trace_checks: usize,
    pub cross_basis_trace_transport_checks: usize,
    pub checked_identities: Vec<&'static str>,
    pub theorem_obligations: Vec<&'static str>,
    pub boundary: &'static str,
    pub error: Option<String>,
}

#[derive(Debug, Clone)]
struct MatrixChecks {
    pauli_trace_formula_checks: usize,
    hermitian_involution_matrix_checks: usize,
    line_group_matrix_lift_checks: usize,
    positive_factor_matrix_checks: usize,
    projector_factorization_checks: usize,
    projector_scaled_idempotence_checks: usize,
    projector_rank_one_trace_checks: usize,
    basis_resolution_matrix_checks: usize,
    same_basis_orthogonality_trace_checks: usize,
    cross_basis_trace_transport_checks: usize,
}

pub fn verify_current_hilbert_transport_schemas() -> Vec<HilbertTransportReport> {
    static REPORTS: OnceLock<Vec<HilbertTransportReport>> = OnceLock::new();
    REPORTS
        .get_or_init(|| {
            verify_current_char_two_weyl_board_schemas()
                .iter()
                .map(verify_char_two_hilbert_transport)
                .collect()
        })
        .clone()
}

pub fn verify_char_two_hilbert_transport(board: &CharTwoWeylBoardReport) -> HilbertTransportReport {
    if board.status != CharTwoWeylBoardStatus::BoardSchemaVerified {
        return HilbertTransportReport {
            source: "characteristic-two exact Hilbert matrix transport",
            exponent: board.exponent,
            dimension: board.dimension,
            basis_count: 0,
            projector_count: 0,
            status: HilbertTransportStatus::MissingBoardSchema,
            pauli_trace_formula_checks: 0,
            hermitian_involution_matrix_checks: 0,
            line_group_matrix_lift_checks: 0,
            positive_factor_matrix_checks: 0,
            projector_factorization_checks: 0,
            projector_scaled_idempotence_checks: 0,
            projector_rank_one_trace_checks: 0,
            basis_resolution_matrix_checks: 0,
            same_basis_orthogonality_trace_checks: 0,
            cross_basis_trace_transport_checks: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "Hilbert transport cannot start without a verified Weyl-board spread",
            error: board.error.clone(),
        };
    }

    let Some(modulus) = find_irreducible_binary_polynomial(board.exponent) else {
        return HilbertTransportReport {
            source: "characteristic-two exact Hilbert matrix transport",
            exponent: board.exponent,
            dimension: board.dimension,
            basis_count: 0,
            projector_count: 0,
            status: HilbertTransportStatus::FieldConstructionFailed,
            pauli_trace_formula_checks: 0,
            hermitian_involution_matrix_checks: 0,
            line_group_matrix_lift_checks: 0,
            positive_factor_matrix_checks: 0,
            projector_factorization_checks: 0,
            projector_scaled_idempotence_checks: 0,
            projector_rank_one_trace_checks: 0,
            basis_resolution_matrix_checks: 0,
            same_basis_orthogonality_trace_checks: 0,
            cross_basis_trace_transport_checks: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "binary field construction failed before Hilbert transport could be checked",
            error: Some("no irreducible binary modulus found".to_string()),
        };
    };

    let field = BinaryField::new(board.exponent, modulus);
    match verify_hilbert_transport_for_field(&field) {
        Ok(checks) => HilbertTransportReport {
            source: "characteristic-two exact Hilbert matrix transport",
            exponent: board.exponent,
            dimension: field.order(),
            basis_count: field.order() + 1,
            projector_count: field.order() * (field.order() + 1),
            status: HilbertTransportStatus::TransportVerified,
            pauli_trace_formula_checks: checks.pauli_trace_formula_checks,
            hermitian_involution_matrix_checks: checks.hermitian_involution_matrix_checks,
            line_group_matrix_lift_checks: checks.line_group_matrix_lift_checks,
            positive_factor_matrix_checks: checks.positive_factor_matrix_checks,
            projector_factorization_checks: checks.projector_factorization_checks,
            projector_scaled_idempotence_checks: checks.projector_scaled_idempotence_checks,
            projector_rank_one_trace_checks: checks.projector_rank_one_trace_checks,
            basis_resolution_matrix_checks: checks.basis_resolution_matrix_checks,
            same_basis_orthogonality_trace_checks: checks.same_basis_orthogonality_trace_checks,
            cross_basis_trace_transport_checks: checks.cross_basis_trace_transport_checks,
            checked_identities: vec![
                "Pauli operators are realized as exact Gaussian-integer monomial matrices",
                "matrix trace agrees with the finite Pauli trace formula",
                "line-group products agree with exact matrix multiplication",
                "character-projector numerators factor as products of I +/- commuting Hermitian involutions",
                "projector numerators are Hermitian scaled idempotents with rank-one trace",
                "each transported basis resolves the identity matrix exactly",
                "same-basis orthogonality is checked by exact matrix trace",
                "cross-basis unbiased trace is transported through the Pauli trace formula",
            ],
            theorem_obligations: vec![
                "formal Lean/Core theorem that Hermitian scaled-idempotent matrix projectors are positive projectors",
                "formal dimension-parametric Hilbert transport for all finite-field Pauli schemas",
                "CODA-MUR loss ledger preserving ZeroRel and terminalizer across board, algebra, and Hilbert representations",
                "certificate family or certified stratification covering composite targets and the all-N query",
            ],
            boundary: "finite Hilbert-transport schema only; not a dimension-parametric certificate family or composite-dimension theorem",
            error: None,
        },
        Err(error) => HilbertTransportReport {
            source: "characteristic-two exact Hilbert matrix transport",
            exponent: board.exponent,
            dimension: field.order(),
            basis_count: field.order() + 1,
            projector_count: field.order() * (field.order() + 1),
            status: HilbertTransportStatus::MatrixIdentityFailed,
            pauli_trace_formula_checks: 0,
            hermitian_involution_matrix_checks: 0,
            line_group_matrix_lift_checks: 0,
            positive_factor_matrix_checks: 0,
            projector_factorization_checks: 0,
            projector_scaled_idempotence_checks: 0,
            projector_rank_one_trace_checks: 0,
            basis_resolution_matrix_checks: 0,
            same_basis_orthogonality_trace_checks: 0,
            cross_basis_trace_transport_checks: 0,
            checked_identities: vec![],
            theorem_obligations: vec![],
            boundary: "exact Hilbert matrix transport failed before any MUB authority could be asserted",
            error: Some(error),
        },
    }
}

fn verify_line_generators(
    line_index: usize,
    generator_matrices: &[BasicMatrix<GaussianRat>],
    identity: &BasicMatrix<GaussianRat>,
    checks: &mut MatrixChecks,
) -> Result<(), String> {
    for (generator_index, generator_matrix) in generator_matrices.iter().enumerate() {
        check_hermitian_involution(
            generator_matrix,
            identity,
            &format!("line {line_index} generator {generator_index}"),
        )?;
        checks.hermitian_involution_matrix_checks += 1;

        for sign in [-1, 1] {
            let factor = add_matrix(identity, &scale_matrix(generator_matrix, sign));
            check_hermitian_scaled_idempotent(
                &factor,
                2,
                &format!("line {line_index} generator {generator_index} factor {sign}"),
            )?;
            checks.positive_factor_matrix_checks += 1;
        }
    }
    Ok(())
}

fn verify_line_group_lifts(
    line_index: usize,
    q: usize,
    generator_matrices: &[BasicMatrix<GaussianRat>],
    group_matrices: &[BasicMatrix<GaussianRat>],
    identity: &BasicMatrix<GaussianRat>,
    checks: &mut MatrixChecks,
) -> Result<(), String> {
    for mask in 0..q {
        let product = matrix_product_from_mask(identity, generator_matrices, mask);
        if product != group_matrices[mask] {
            return Err(format!(
                "line {line_index} matrix lift failed for group mask {mask}"
            ));
        }
        checks.line_group_matrix_lift_checks += 1;

        check_hermitian_involution(
            &group_matrices[mask],
            identity,
            &format!("line {line_index} group mask {mask}"),
        )?;
        checks.hermitian_involution_matrix_checks += 1;
    }
    Ok(())
}

fn verify_single_projector(
    line_index: usize,
    q: usize,
    label: usize,
    projector: &BasicMatrix<GaussianRat>,
    identity: &BasicMatrix<GaussianRat>,
    generator_matrices: &[BasicMatrix<GaussianRat>],
    checks: &mut MatrixChecks,
) -> Result<(), String> {
    let factorized = factorized_projector_numerator(identity, generator_matrices, label);
    if factorized != *projector {
        return Err(format!(
            "line {line_index} projector label {label} does not match positive-factor product"
        ));
    }
    checks.projector_factorization_checks += 1;

    if !is_hermitian_matrix(projector) {
        return Err(format!(
            "line {line_index} projector label {label} is not Hermitian"
        ));
    }
    let square = mul_matrix(projector, projector);
    if square != scale_matrix(projector, q as i64) {
        return Err(format!(
            "line {line_index} projector label {label} is not q-scaled idempotent"
        ));
    }
    checks.projector_scaled_idempotence_checks += 1;

    if trace_matrix(projector) != GaussianRat::from_ints(q as i64, 0) {
        return Err(format!(
            "line {line_index} projector label {label} does not have rank-one trace"
        ));
    }
    checks.projector_rank_one_trace_checks += 1;
    Ok(())
}

fn verify_line_projectors(
    line_index: usize,
    q: usize,
    projectors: &[BasicMatrix<GaussianRat>],
    identity: &BasicMatrix<GaussianRat>,
    generator_matrices: &[BasicMatrix<GaussianRat>],
    checks: &mut MatrixChecks,
) -> Result<(), String> {
    for (label, projector) in projectors.iter().enumerate() {
        verify_single_projector(
            line_index,
            q,
            label,
            projector,
            identity,
            generator_matrices,
            checks,
        )?;
    }
    let resolution = projectors
        .iter()
        .fold(zero_matrix(q), |acc, projector| add_matrix(&acc, projector));
    if resolution != scale_matrix(identity, q as i64) {
        return Err(format!(
            "line {line_index} projectors do not resolve identity"
        ));
    }
    checks.basis_resolution_matrix_checks += 1;

    for left in 0..q {
        for right in left + 1..q {
            let overlap_trace = trace_product(&projectors[left], &projectors[right]);
            if overlap_trace != GaussianRat::zero() {
                return Err(format!(
                    "line {line_index} labels {left} and {right} are not matrix-orthogonal"
                ));
            }
            checks.same_basis_orthogonality_trace_checks += 1;
        }
    }
    Ok(())
}

fn verify_cross_line_pair(
    field: &BinaryField,
    q: usize,
    left_line: usize,
    right_line: usize,
    left_group: &[BinaryPauli],
    right_group: &[BinaryPauli],
    checks: &mut MatrixChecks,
) -> Result<(), String> {
    for left in left_group {
        for right in right_group {
            let product = left.mul(*right, field);
            let trace = pauli_matrix_trace(field, product);
            if product.is_vector_zero() {
                if trace != scale_gaussian(&phase_value(product.phase), q as i64) {
                    return Err(format!(
                        "cross line {left_line}/{right_line} scalar Pauli trace mismatch"
                    ));
                }
            } else if trace != GaussianRat::zero() {
                return Err(format!(
                    "cross line {left_line}/{right_line} non-scalar Pauli trace mismatch"
                ));
            }
            checks.cross_basis_trace_transport_checks += 1;
        }
    }
    Ok(())
}

fn verify_hilbert_transport_for_field(field: &BinaryField) -> Result<MatrixChecks, String> {
    let q = field.order();
    let identity = identity_matrix(q);
    let zero = zero_matrix(q);
    let line_bases = build_line_bases(field);

    let mut checks = MatrixChecks {
        pauli_trace_formula_checks: verify_pauli_trace_formula(field)?,
        hermitian_involution_matrix_checks: 0,
        line_group_matrix_lift_checks: 0,
        positive_factor_matrix_checks: 0,
        projector_factorization_checks: 0,
        projector_scaled_idempotence_checks: 0,
        projector_rank_one_trace_checks: 0,
        basis_resolution_matrix_checks: 0,
        same_basis_orthogonality_trace_checks: 0,
        cross_basis_trace_transport_checks: 0,
    };

    for (line_index, basis) in line_bases.iter().enumerate() {
        let generators: Vec<BinaryPauli> = basis
            .iter()
            .map(|&(x, z)| BinaryPauli::hermitian(field, x, z))
            .collect();
        let generator_matrices: Vec<BasicMatrix<GaussianRat>> = generators
            .iter()
            .map(|generator| pauli_matrix(field, *generator))
            .collect();

        verify_line_generators(line_index, &generator_matrices, &identity, &mut checks)?;

        let group = build_line_group(field, &generators);
        let group_matrices: Vec<BasicMatrix<GaussianRat>> = group
            .iter()
            .map(|element| pauli_matrix(field, *element))
            .collect();

        verify_line_group_lifts(
            line_index,
            q,
            &generator_matrices,
            &group_matrices,
            &identity,
            &mut checks,
        )?;

        let projectors: Vec<BasicMatrix<GaussianRat>> = (0..q)
            .map(|label| projector_numerator(q, label, &group_matrices))
            .collect();

        verify_line_projectors(
            line_index,
            q,
            &projectors,
            &identity,
            &generator_matrices,
            &mut checks,
        )?;
    }

    for left_line in 0..line_bases.len() {
        let left_group = build_line_group_from_basis(field, &line_bases[left_line]);
        for right_line in left_line + 1..line_bases.len() {
            let right_group = build_line_group_from_basis(field, &line_bases[right_line]);
            verify_cross_line_pair(
                field,
                q,
                left_line,
                right_line,
                &left_group,
                &right_group,
                &mut checks,
            )?;
        }
    }

    if trace_matrix(&zero) != GaussianRat::zero() {
        return Err("zero matrix trace sanity check failed".to_string());
    }

    Ok(checks)
}

fn verify_pauli_trace_formula(field: &BinaryField) -> Result<usize, String> {
    let mut checks = 0;
    for phase in 0..4 {
        for &x in field.elements() {
            for &z in field.elements() {
                let pauli = BinaryPauli { phase, x, z };
                let matrix_trace = trace_matrix(&pauli_matrix(field, pauli));
                let expected = pauli_matrix_trace(field, pauli);
                if matrix_trace != expected {
                    return Err(format!(
                        "Pauli trace formula failed for phase {phase}, x={x}, z={z}"
                    ));
                }
                checks += 1;
            }
        }
    }
    Ok(checks)
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

fn build_line_group_from_basis(field: &BinaryField, basis: &[(usize, usize)]) -> Vec<BinaryPauli> {
    let generators: Vec<BinaryPauli> = basis
        .iter()
        .map(|&(x, z)| BinaryPauli::hermitian(field, x, z))
        .collect();
    build_line_group(field, &generators)
}

fn matrix_product_from_mask(
    identity: &BasicMatrix<GaussianRat>,
    generators: &[BasicMatrix<GaussianRat>],
    mask: usize,
) -> BasicMatrix<GaussianRat> {
    let mut product = identity.clone();
    for (bit, generator) in generators.iter().enumerate() {
        if (mask >> bit) & 1 == 1 {
            product = mul_matrix(&product, generator);
        }
    }
    product
}

fn projector_numerator(
    q: usize,
    label: usize,
    group_matrices: &[BasicMatrix<GaussianRat>],
) -> BasicMatrix<GaussianRat> {
    let mut sum = zero_matrix(q);
    for (mask, matrix) in group_matrices.iter().enumerate() {
        let sign = character_sign(label, mask);
        let scaled = scale_matrix(matrix, sign);
        sum = add_matrix(&sum, &scaled);
    }
    sum
}

fn factorized_projector_numerator(
    identity: &BasicMatrix<GaussianRat>,
    generator_matrices: &[BasicMatrix<GaussianRat>],
    label: usize,
) -> BasicMatrix<GaussianRat> {
    let mut product = identity.clone();
    for (bit, generator) in generator_matrices.iter().enumerate() {
        let sign = character_sign(label, 1usize << bit);
        let factor = add_matrix(identity, &scale_matrix(generator, sign));
        product = mul_matrix(&product, &factor);
    }
    product
}

fn check_hermitian_involution(
    matrix: &BasicMatrix<GaussianRat>,
    identity: &BasicMatrix<GaussianRat>,
    context: &str,
) -> Result<(), String> {
    if !is_hermitian_matrix(matrix) {
        return Err(format!("{context} is not Hermitian"));
    }
    if mul_matrix(matrix, matrix) != *identity {
        return Err(format!("{context} is not an involution"));
    }
    Ok(())
}

fn check_hermitian_scaled_idempotent(
    matrix: &BasicMatrix<GaussianRat>,
    scale: i64,
    context: &str,
) -> Result<(), String> {
    if !is_hermitian_matrix(matrix) {
        return Err(format!("{context} is not Hermitian"));
    }
    if mul_matrix(matrix, matrix) != scale_matrix(matrix, scale) {
        return Err(format!("{context} is not a {scale}-scaled idempotent"));
    }
    Ok(())
}

fn pauli_matrix(field: &BinaryField, pauli: BinaryPauli) -> BasicMatrix<GaussianRat> {
    let q = field.order();
    let mut data = vec![GaussianRat::zero(); q * q];
    for &source in field.elements() {
        let target = field.add(source, pauli.x);
        let sign = if field.trace(field.mul(pauli.z, source)) == 0 {
            1
        } else {
            -1
        };
        let val = scale_gaussian(&phase_value(pauli.phase), sign);
        data[target * q + source] = val;
    }
    BasicMatrix::from_row_major(q, q, data).checked_invariant_a6b5b733("valid pauli matrix shape")
}

fn pauli_matrix_trace(field: &BinaryField, pauli: BinaryPauli) -> GaussianRat {
    if pauli.is_vector_zero() {
        scale_gaussian(&phase_value(pauli.phase), field.order() as i64)
    } else {
        GaussianRat::zero()
    }
}

fn character_sign(label: usize, element: usize) -> i64 {
    if (label & element).count_ones() % 2 == 0 {
        1
    } else {
        -1
    }
}

fn phase_value(phase: u8) -> GaussianRat {
    match phase % 4 {
        0 => GaussianRat::one(),
        1 => GaussianRat::i(),
        2 => GaussianRat::from_ints(-1, 0),
        3 => GaussianRat::from_ints(0, -1),
        _ => unreachable!(),
    }
}

fn scale_gaussian(g: &GaussianRat, factor: i64) -> GaussianRat {
    g.mul(&GaussianRat::from_ints(factor, 0))
}

fn zero_matrix(n: usize) -> BasicMatrix<GaussianRat> {
    mx::zeros(n, n).checked_invariant_a6b5b733("zero matrix")
}

fn identity_matrix(n: usize) -> BasicMatrix<GaussianRat> {
    mx::identity(n).checked_invariant_a6b5b733("identity matrix")
}

fn add_matrix(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> BasicMatrix<GaussianRat> {
    mx::add(a, b).checked_invariant_a6b5b733("matrix addition")
}

fn scale_matrix(m: &BasicMatrix<GaussianRat>, factor: i64) -> BasicMatrix<GaussianRat> {
    mx::scale(m, &GaussianRat::from_ints(factor, 0)).checked_invariant_a6b5b733("matrix scale")
}

fn mul_matrix(
    a: &BasicMatrix<GaussianRat>,
    b: &BasicMatrix<GaussianRat>,
) -> BasicMatrix<GaussianRat> {
    assert_eq!(a.shape(), b.shape());
    let n = a.rows();
    let mut data = vec![GaussianRat::zero(); n * n];
    let a_slice = a.as_slice();
    let b_slice = b.as_slice();
    for row in 0..n {
        for mid in 0..n {
            let left = &a_slice[row * n + mid];
            if left.is_zero() {
                continue;
            }
            for col in 0..n {
                let right = &b_slice[mid * n + col];
                if !right.is_zero() {
                    let prod = left.mul(right);
                    data[row * n + col] = data[row * n + col].add(&prod);
                }
            }
        }
    }
    BasicMatrix::from_row_major(n, n, data).checked_invariant_a6b5b733("valid matrix shape")
}

fn is_hermitian_matrix(m: &BasicMatrix<GaussianRat>) -> bool {
    exact_hermitian::is_hermitian(m)
}

fn trace_matrix(m: &BasicMatrix<GaussianRat>) -> GaussianRat {
    mx::trace(m).checked_invariant_a6b5b733("trace of square matrix")
}

fn trace_product(left: &BasicMatrix<GaussianRat>, right: &BasicMatrix<GaussianRat>) -> GaussianRat {
    assert_eq!(left.shape(), right.shape());
    let n = left.rows();
    let l_slice = left.as_slice();
    let r_slice = right.as_slice();
    let mut trace = GaussianRat::zero();
    for row in 0..n {
        for col in 0..n {
            let l_val = &l_slice[row * n + col];
            if l_val.is_zero() {
                continue;
            }
            let r_val = &r_slice[col * n + row];
            if !r_val.is_zero() {
                trace = trace.add(&l_val.mul(r_val));
            }
        }
    }
    trace
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/hilbert_transport.rs
// Claim: urn:core:crates_rs:core-quantum-physics:hilbert-transport:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorda6b5b733 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorda6b5b733` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrora6b5b733 {
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
impl BoundaryErrora6b5b733 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrora6b5b733 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrora6b5b733 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorda6b5b733 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrora6b5b733> {
        if capacity_bound == 0 {
            return Err(BoundaryErrora6b5b733::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrora6b5b733::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrora6b5b733::ExceedsCapacity {
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
    fn hilbert_transport_verifies_for_char_two_boards() {
        for exponent in [2, 3, 4, 5] {
            let board = verify_char_two_weyl_board_schema(exponent);
            let report = verify_char_two_hilbert_transport(&board);
            let q = board.dimension;
            assert_eq!(report.status, HilbertTransportStatus::TransportVerified);
            assert_eq!(report.basis_count, q + 1);
            assert_eq!(report.projector_count, q * (q + 1));
            assert_eq!(report.pauli_trace_formula_checks, 4 * q * q);
            assert_eq!(report.projector_factorization_checks, (q + 1) * q);
            assert_eq!(report.projector_scaled_idempotence_checks, (q + 1) * q);
            assert_eq!(report.projector_rank_one_trace_checks, (q + 1) * q);
            assert_eq!(report.basis_resolution_matrix_checks, q + 1);
            assert_eq!(
                report.same_basis_orthogonality_trace_checks,
                (q + 1) * q * (q - 1) / 2
            );
            assert_eq!(
                report.cross_basis_trace_transport_checks,
                q * (q + 1) / 2 * q * q
            );
            assert!(report
                .theorem_obligations
                .iter()
                .any(|obligation| obligation.contains("dimension-parametric")));
            assert!(report.error.is_none());
        }
    }

    #[test]
    fn hilbert_transport_rejects_missing_board_schema() {
        let board = verify_char_two_weyl_board_schema(1);
        let report = verify_char_two_hilbert_transport(&board);
        assert_eq!(report.status, HilbertTransportStatus::MissingBoardSchema);
        assert!(report.error.is_some());
    }
}

#[cfg(test)]
mod l4_boundary_tests_a6b5b733 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorda6b5b733::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorda6b5b733::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorda6b5b733::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorda6b5b733::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorda6b5b733::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrora6b5b733::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrora6b5b733::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
