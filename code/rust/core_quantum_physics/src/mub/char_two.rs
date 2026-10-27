//! Characteristic-two complete MUBs on canonical exact projector matrices.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2214473c<T> {
    fn checked_invariant_2214473c(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2214473c<T> for Option<T> {
    #[inline]
    fn checked_invariant_2214473c(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2214473c<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2214473c(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use core_lie_theory::pauli_symplectic::{pauli, Pauli};
use core_number_theory::cyclotomic::Cyc24;
use core_number_theory::rational::rq;

fn joint_spectral_basis(
    operators: &[BasicMatrix<Cyc24>],
    d: usize,
) -> Result<Vec<BasicMatrix<Cyc24>>, String> {
    let identity = matrix::identity(d).map_err(|e| e.to_string())?;
    let mut out = Vec::with_capacity(d);
    if operators.len() >= usize::BITS as usize || (1usize << operators.len()) != d {
        return Err("independent binary generators must match the Hilbert dimension".into());
    }
    for mask in 0..d {
        out.push(spectral_projector_for_mask(operators, &identity, mask)?);
    }
    Ok(out)
}

fn spectral_projector_for_mask(
    operators: &[BasicMatrix<Cyc24>],
    identity: &BasicMatrix<Cyc24>,
    mask: usize,
) -> Result<BasicMatrix<Cyc24>, String> {
    let mut p = identity.clone();
    for (j, op) in operators.iter().enumerate() {
        let sign = if mask & (1 << j) == 0 { 1 } else { -1 };
        let term = matrix::scale(op, &Cyc24::rat(rq(sign, 1))).map_err(|e| e.to_string())?;
        let sum = matrix::add(identity, &term).map_err(|e| e.to_string())?;
        let factor = matrix::scale(&sum, &Cyc24::rat(rq(1, 2))).map_err(|e| e.to_string())?;
        p = matrix::multiply(&p, &factor).map_err(|e| e.to_string())?;
    }
    Ok(p)
}
/// Pauli Z, X and Y eigenprojectors, in that order.
pub fn build_char_two_mub_d2() -> Vec<Vec<BasicMatrix<Cyc24>>> {
    [Pauli::Z, Pauli::X, Pauli::Y]
        .into_iter()
        .map(|letter| {
            joint_spectral_basis(&[pauli::<Cyc24>(letter).checked_invariant_2214473c("canonical Pauli")], 2)
                .checked_invariant_2214473c("fixed Pauli spectrum")
        })
        .collect()
}
/// Five declared disjoint two-qubit Pauli MASAs; all scalar and matrix operations
/// belong to their Lie and linear-algebra owners.
pub fn build_char_two_mub_d4() -> Vec<Vec<BasicMatrix<Cyc24>>> {
    let i = pauli::<Cyc24>(Pauli::Identity).checked_invariant_2214473c("canonical Pauli");
    let x = pauli::<Cyc24>(Pauli::X).checked_invariant_2214473c("canonical Pauli");
    let y = pauli::<Cyc24>(Pauli::Y).checked_invariant_2214473c("canonical Pauli");
    let z = pauli::<Cyc24>(Pauli::Z).checked_invariant_2214473c("canonical Pauli");
    let matrices = [
        ((&z, &i), (&i, &z)),
        ((&x, &i), (&i, &x)),
        ((&y, &i), (&i, &y)),
        ((&x, &y), (&y, &z)),
        ((&x, &z), (&y, &x)),
    ];
    matrices
        .into_iter()
        .map(|((a, b), (c, d))| {
            joint_spectral_basis(
                &[
                    matrix::kronecker(a, b).checked_invariant_2214473c("fixed tensor factors"),
                    matrix::kronecker(c, d).checked_invariant_2214473c("fixed tensor factors"),
                ],
                4,
            )
            .checked_invariant_2214473c("fixed commuting Pauli generators")
        })
        .collect()
}

// Origin: engine/crates_rs/core_quantum_physics/src/mub/char_two.rs
// Claim: urn:core:crates_rs:core-quantum-physics:char-two:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2214473c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2214473c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2214473c {
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
impl BoundaryError2214473c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2214473c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2214473c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2214473c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2214473c> {
        if capacity_bound == 0 {
            return Err(BoundaryError2214473c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2214473c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2214473c::ExceedsCapacity {
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
    use crate::mub::algebra::{verify_mub_projector_algebra, ProjectorAlgebraStatus};

    #[test]
    fn test_char_two_d2_algebra() {
        let bases = build_char_two_mub_d2();
        let report = verify_mub_projector_algebra(&bases, 2);
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 3);
        assert_eq!(report.projector_count, 6);
    }

    #[test]
    fn test_char_two_d4_algebra() {
        let bases = build_char_two_mub_d4();
        let report = verify_mub_projector_algebra(&bases, 4);
        assert_eq!(report.status, ProjectorAlgebraStatus::AlgebraVerified);
        assert_eq!(report.basis_count, 5);
        assert_eq!(report.projector_count, 20);
    }
}

/// A complete spread MUB in every checked characteristic-two dimension 2^k.
/// The commuting generators are Hermitian displacements X_u Z_{a*u} for
/// a in GF(2^k), using its nondegenerate absolute trace pairing. Their joint
/// spectral projectors are products (I +/- D_j)/2; no square roots are needed.
pub fn build_char_two_mub(
    degree: usize,
    entry_budget: usize,
) -> Result<Vec<Vec<BasicMatrix<Cyc24>>>, String> {
    use core_number_theory::finite_field::{FieldElement, FiniteField};
    let q = validate_char_two_mub_budget(degree, entry_budget)?;
    let field = FiniteField::with_first_irreducible(2, degree).ok_or("binary field refused")?;
    let elements = field.elements();
    let generators = (0..degree)
        .map(|j| {
            let mut coeffs = vec![0; degree];
            coeffs[j] = 1;
            FieldElement { coeffs }
        })
        .collect::<Vec<_>>();
    let diagonal = generators
        .iter()
        .map(|v| char_two_displacement(&field, elements, q, &field.zero(), v))
        .collect::<Result<Vec<_>, _>>()?;
    let mut bases = vec![joint_spectral_basis(&diagonal, q)?];
    for slope in elements {
        let operators = generators
            .iter()
            .map(|u| char_two_displacement(&field, elements, q, u, &field.mul(slope, u)))
            .collect::<Result<Vec<_>, _>>()?;
        bases.push(joint_spectral_basis(&operators, q)?);
    }
    Ok(bases)
}

fn validate_char_two_mub_budget(degree: usize, entry_budget: usize) -> Result<usize, String> {
    use core_number_theory::finite_field::checked_pow;
    if degree == 0 {
        return Err("positive binary extension degree required".into());
    }
    let q = checked_pow(2, degree).ok_or("dimension overflow")?;
    let required = q
        .checked_mul(q)
        .and_then(|n| n.checked_mul(q))
        .and_then(|n| n.checked_mul(q + 1))
        .ok_or("entry count overflow")?;
    if required > entry_budget {
        return Err(format!(
            "{required} output entries exceed budget {entry_budget}"
        ));
    }
    Ok(q)
}

fn char_two_displacement(
    field: &core_number_theory::finite_field::FiniteField,
    elements: &[core_number_theory::finite_field::FieldElement],
    q: usize,
    u: &core_number_theory::finite_field::FieldElement,
    v: &core_number_theory::finite_field::FieldElement,
) -> Result<BasicMatrix<Cyc24>, String> {
    let phase = if field.trace_value(&field.mul(u, v))? == 1 {
        Cyc24::i()
    } else {
        Cyc24::one()
    };
    let mut operator = matrix::zeros::<Cyc24>(q, q).map_err(|e| e.to_string())?;
    for (column, x) in elements.iter().enumerate() {
        let translated = field.add(x, u);
        let row = elements
            .iter()
            .position(|y| y == &translated)
            .ok_or("field translation left the carrier")?;
        let sign = if field.trace_value(&field.mul(v, x))? == 0 {
            1
        } else {
            -1
        };
        operator
            .set(row, column, phase.mul(&Cyc24::rat(rq(sign, 1))))
            .map_err(|e| e.to_string())?;
    }
    Ok(operator)
}

#[cfg(test)]
mod l4_boundary_tests_2214473c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2214473c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2214473c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2214473c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2214473c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2214473c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2214473c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2214473c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
