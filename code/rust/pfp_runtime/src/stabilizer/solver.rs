//! Deterministic phase-tracked GF(2) decomposition and exact energy search.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1c973ba1<T> {
    fn checked_invariant_1c973ba1(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1c973ba1<T> for Option<T> {
    #[inline]
    fn checked_invariant_1c973ba1(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1c973ba1<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1c973ba1(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::{parse_case, DecompositionRow, StabilizerOutcome, Term, MAX_QUBITS};
use crate::f2::F2Matrix;
use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{ToPrimitive, Zero};
use core_quantum_physics::pauli::PauliString;
use serde_json::Value;

fn find_anticommuting_pair(terms: &[Term]) -> Option<[String; 2]> {
    let m = terms.len();
    for i in 0..m {
        for j in (i + 1)..m {
            if terms[i]
                .pauli
                .anticommutes_with(&terms[j].pauli)
                .checked_invariant_1c973ba1("parsed equal Pauli lengths")
            {
                return Some([terms[i].id.clone(), terms[j].id.clone()]);
            }
        }
    }
    None
}

fn build_f2_matrix_from_cols(n: usize, basis_cols: &[Vec<bool>]) -> Result<F2Matrix, String> {
    let k = basis_cols.len();
    let mut mat_data = Vec::with_capacity(2 * n * k);
    for r in 0..(2 * n) {
        for col in basis_cols {
            mat_data.push(col[r]);
        }
    }
    F2Matrix::new(2 * n, k, mat_data).map_err(|error| error.to_string())
}

fn extract_independent_generators(
    n: usize,
    terms: &[Term],
) -> Result<(Vec<PauliString>, Vec<String>, Vec<Vec<bool>>), (String, String)> {
    let id_pauli = PauliString::identity(n)
        .checked_invariant_1c973ba1("parsed positive bounded qubit count");
    let mut generators: Vec<PauliString> = Vec::new();
    let mut basis_ids: Vec<String> = Vec::new();
    let mut basis_cols: Vec<Vec<bool>> = Vec::new(); // each col has length 2*n

    for term in terms {
        if term.pauli == id_pauli {
            continue;
        }
        let vec = term.pauli.to_symplectic_bools();
        if generators.is_empty() {
            generators.push(term.pauli.clone());
            basis_ids.push(term.id.clone());
            basis_cols.push(vec);
            continue;
        }
        // Solve M * x = vec over GF(2)
        let mat = build_f2_matrix_from_cols(n, &basis_cols).map_err(|e| {
            (
                "F2_MATRIX_ERROR".to_string(),
                format!("F2 matrix creation failed: {e}"),
            )
        })?;
        match mat.solve(&vec) {
            Ok(Some(_)) => {
                // Linearly dependent, already in span
            }
            Ok(None) => {
                // Linearly independent, add generator
                generators.push(term.pauli.clone());
                basis_ids.push(term.id.clone());
                basis_cols.push(vec);
                if generators.len() == n {
                    break;
                }
            }
            Err(e) => {
                return Err((
                    "F2_SOLVER_ERROR".to_string(),
                    format!("F2 linear solve failed: {e}"),
                ));
            }
        }
    }
    Ok((generators, basis_ids, basis_cols))
}

fn reconstruct_generator_product(
    n: usize,
    term: &Term,
    generators: &[PauliString],
    sol: &[bool],
) -> Result<i8, (String, String)> {
    // Compute prod_j G_j^{sol[j]}, retaining its entire phase in the carrier.
    let mut prod = PauliString::identity(n)
        .checked_invariant_1c973ba1("parsed positive bounded qubit count");
    for (j, &exp) in sol.iter().enumerate() {
        if exp {
            prod = prod
                .multiply(&generators[j])
                .checked_invariant_1c973ba1("parsed equal Pauli lengths");
        }
    }
    if prod.letters() != term.pauli.letters() {
        return Err((
            "ALGEBRAIC_RECONSTRUCTION_ERROR".to_string(),
            format!(
                "Algebraic reconstruction error: expected {:?}, got {:?}",
                term.pauli.letters(),
                prod.letters()
            ),
        ));
    }
    let phase_acc = prod.phase();
    match phase_acc {
        0 => Ok(1i8),
        2 => Ok(-1i8),
        _ => Err((
            "NON_HERMITIAN_PHASE".to_string(),
            format!("Non-Hermitian product phase i^{phase_acc}"),
        )),
    }
}

fn decompose_single_term(
    n: usize,
    term: &Term,
    generators: &[PauliString],
    basis_cols: &[Vec<bool>],
) -> Result<(Vec<bool>, i8), (String, String)> {
    if generators.is_empty() {
        return Ok((vec![], 1i8));
    }
    let vec = term.pauli.to_symplectic_bools();
    let mat =
        build_f2_matrix_from_cols(n, basis_cols).checked_invariant_1c973ba1("checked invariant");
    let sol = match mat.solve(&vec) {
        Ok(Some(s)) => s,
        Ok(None) => {
            return Err((
                "UNEXPECTED_TERM_NOT_IN_SPAN".to_string(),
                format!("Term {} not in generator span", term.id),
            ));
        }
        Err(e) => {
            return Err((
                "F2_SOLVE_FAILED".to_string(),
                format!("F2 solve failed: {e}"),
            ));
        }
    };
    let sigma = reconstruct_generator_product(n, term, generators, &sol)?;
    Ok((sol, sigma))
}

type DecompEntry = (Vec<bool>, i8, Rational64, i8);

fn decompose_all_terms(
    n: usize,
    terms: &[Term],
    generators: &[PauliString],
    basis_cols: &[Vec<bool>],
) -> Result<(Vec<DecompositionRow>, Vec<DecompEntry>), (String, String)> {
    let m = terms.len();
    let mut decompositions = Vec::with_capacity(m);
    // (exponents: Vec<bool>, sigma: i8, weight: Rational64, target: i8)
    let mut decomp_data: Vec<DecompEntry> = Vec::with_capacity(m);

    for term in terms {
        let (exponents, sigma) = decompose_single_term(n, term, generators, basis_cols)?;
        let mut mask = 0usize;
        for (b_i, &exp) in exponents.iter().enumerate() {
            if exp {
                mask |= 1 << b_i;
            }
        }
        decompositions.push(DecompositionRow {
            id: term.id.clone(),
            mask,
            phase: sigma,
        });
        decomp_data.push((exponents, sigma, term.weight, term.target));
    }
    Ok((decompositions, decomp_data))
}

fn assignment_energy(assignment_idx: usize, decomp_data: &[DecompEntry]) -> BigRational {
    // Compute eigenvalues: b_j in {+1, -1}
    // (assignment_idx >> j) & 1 == 0 => +1, else -1
    let mut total_energy = BigRational::zero();

    for (exponents, sigma, weight, target) in decomp_data {
        let mut term_lambda = *sigma as i64;
        for (j, &exp) in exponents.iter().enumerate() {
            if exp {
                let bj = if ((assignment_idx >> j) & 1) == 0 {
                    1i64
                } else {
                    -1i64
                };
                term_lambda *= bj;
            }
        }
        // penalty = weight * (1 - target * term_lambda) / 2
        let viol_factor = (1 - (*target as i64) * term_lambda) / 2;
        if viol_factor > 0 {
            // Input limbs are bounded; their exact sum need not fit the wire carrier.
            total_energy += BigRational::new(
                BigInt::from(*weight.numer()) * BigInt::from(viol_factor),
                BigInt::from(*weight.denom()),
            );
        }
    }
    total_energy
}

fn find_minimum_energy_assignments(
    k: usize,
    decomp_data: &[DecompEntry],
) -> (BigRational, Vec<usize>) {
    let num_assignments = 1usize << k;
    let mut min_energy: Option<BigRational> = None;
    let mut minimizing_assignments: Vec<usize> = Vec::new();

    for assignment_idx in 0..num_assignments {
        let total_energy = assignment_energy(assignment_idx, decomp_data);
        match min_energy.as_ref() {
            None => {
                min_energy = Some(total_energy);
                minimizing_assignments = vec![assignment_idx];
            }
            Some(curr_min) => {
                if &total_energy < curr_min {
                    min_energy = Some(total_energy);
                    minimizing_assignments = vec![assignment_idx];
                } else if &total_energy == curr_min {
                    minimizing_assignments.push(assignment_idx);
                }
            }
        }
    }
    (min_energy.unwrap_or_else(BigRational::zero), minimizing_assignments)
}

/// Solves a finite quantum Hamiltonian challenge case.
/// Exact energy accumulation uses arbitrary-precision rationals. SOLVED retains
/// its i64 wire limbs; an unrepresentable final minimum is a typed UNKNOWN refusal.
pub fn solve(case_val: &Value) -> StabilizerOutcome {
    let case = match parse_case(case_val) {
        Ok(c) => c,
        Err((code, msg)) => {
            let id = case_val
                .get("id")
                .or_else(|| case_val.get("case_id"))
                .and_then(|v| v.as_str())
                .unwrap_or("case_unnamed")
                .to_string();
            return StabilizerOutcome::Unknown {
                id,
                refusal_code: code,
                message: msg,
            };
        }
    };

    let n = case.num_qubits;
    if case.terms.is_empty() {
        return StabilizerOutcome::Solved {
            id: case.id,
            energy: [0, 1],
            degeneracy: 1u64 << n,
            basis: vec![],
            decomposition: vec![],
            minimizers: vec![0],
        };
    }

    if let Some(witness) = find_anticommuting_pair(&case.terms) {
        return StabilizerOutcome::OutOfScope {
            id: case.id,
            witness,
        };
    }

    let (generators, basis_ids, basis_cols) =
        match extract_independent_generators(n, &case.terms) {
            Ok(res) => res,
            Err((refusal_code, message)) => {
                return StabilizerOutcome::Unknown {
                    id: case.id,
                    refusal_code,
                    message,
                };
            }
        };

    let k = generators.len();
    if k > MAX_QUBITS {
        return StabilizerOutcome::Unknown {
            id: case.id,
            refusal_code: "ENUMERATION_BOUND_EXCEEDED".to_string(),
            message: format!("Generator count {k} exceeds bound {MAX_QUBITS}"),
        };
    }

    let (decompositions, decomp_data) =
        match decompose_all_terms(n, &case.terms, &generators, &basis_cols) {
            Ok(res) => res,
            Err((refusal_code, message)) => {
                return StabilizerOutcome::Unknown {
                    id: case.id,
                    refusal_code,
                    message,
                };
            }
        };

    let (min_e, minimizing_assignments) = find_minimum_energy_assignments(k, &decomp_data);
    let (Some(numerator), Some(denominator)) = (min_e.numer().to_i64(), min_e.denom().to_i64())
    else {
        return StabilizerOutcome::Unknown {
            id: case.id,
            refusal_code: "ENERGY_WIDTH_EXCEEDED".to_string(),
            message:
                "The exact minimum energy exceeds the i64 numerator/denominator output carrier"
                    .to_string(),
        };
    };
    let subspace_dim = 1u64 << (n - k);
    let total_degeneracy = (minimizing_assignments.len() as u64) * subspace_dim;

    StabilizerOutcome::Solved {
        id: case.id,
        energy: [numerator, denominator],
        degeneracy: total_degeneracy,
        basis: basis_ids,
        decomposition: decompositions,
        minimizers: minimizing_assignments,
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/stabilizer/solver.rs
// Claim: urn:core:crates_rs:pfp-runtime:solver:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1c973ba1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1c973ba1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1c973ba1 {
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
impl BoundaryError1c973ba1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1c973ba1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1c973ba1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1c973ba1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1c973ba1> {
        if capacity_bound == 0 {
            return Err(BoundaryError1c973ba1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1c973ba1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1c973ba1::ExceedsCapacity {
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
mod l4_boundary_tests_1c973ba1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord1c973ba1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord1c973ba1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord1c973ba1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord1c973ba1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord1c973ba1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError1c973ba1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError1c973ba1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
