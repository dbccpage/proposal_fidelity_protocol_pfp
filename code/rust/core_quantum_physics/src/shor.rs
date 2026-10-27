// AuthorityEffect: None.

//! Shor [[9, 1, 3]] concatenated quantum error correcting code in exact binary Pauli algebra.
//!
//! Features:
//!   - 8 stabilizer generators (6 bit-flip checks Z_j Z_{j+1} + 2 phase-flip checks X_1..X_6, X_4..X_9).
//!   - Exact syndrome extraction: s(E) in {0, 1}^8 via symplectic commutation.
//!   - Table lookup decoding and recovery operator R(s) in {I, X, Y, Z}^9.
//!   - 100% deterministic recovery of all 27 single-qubit Pauli errors (X, Y, Z on qubits 0..8).


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_98942817<T> {
    fn checked_invariant_98942817(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_98942817<T> for Option<T> {
    #[inline]
    fn checked_invariant_98942817(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_98942817<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_98942817(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::pauli::{pauli_anticommutes, Pauli, PauliError};
use crate::stabilizer_code_distance::StabilizerCode;
use core_number_theory::rational::{rq, Rational};
use serde::{Deserialize, Serialize};

pub type Pauli9 = [Pauli; 9];

/// Reads a word of nine Pauli letters; refuses any other letter and any other
/// length (counted in characters).
pub fn pauli9_from_str(s: &str) -> Result<Pauli9, PauliError> {
    let letters = s
        .chars()
        .map(Pauli::from_char)
        .collect::<Result<Vec<_>, _>>()?;
    letters
        .try_into()
        .map_err(|letters: Vec<Pauli>| PauliError::WrongLength {
            expected: 9,
            actual: letters.len(),
        })
}

/// A nine-letter word written in this module.
fn word(s: &str) -> Pauli9 {
    pauli9_from_str(s).checked_invariant_98942817("the words of this module are nine Pauli letters")
}

pub fn pauli9_anticommutes(a: &Pauli9, b: &Pauli9) -> bool {
    pauli_anticommutes(a, b)
}

pub fn pauli9_multiply(a: &Pauli9, b: &Pauli9) -> Pauli9 {
    let mut res = [Pauli::I; 9];
    for i in 0..9 {
        res[i] = a[i].multiply(b[i]);
    }
    res
}

/// Decodes 2-bit repetition syndrome into an error index 0..2.
fn decode_repetition_syndrome(s0: u8, s1: u8) -> Option<usize> {
    match (s0, s1) {
        (1, 0) => Some(0),
        (1, 1) => Some(1),
        (0, 1) => Some(2),
        _ => None,
    }
}

/// Exact combinatorial representation and syndrome recovery for Shor [[9, 1, 3]] code.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ShorNineQubitCode {
    pub n_physical: usize,
    pub k_logical: usize,
    pub distance: usize,
    pub n_stabilizers: usize,
    pub all_stabilizers_pairwise_commute: bool,
    pub logical_operators_anticommute: bool,
    pub single_qubit_errors_recoverable: usize,
    pub recovery_success_rate: Rational,
}

impl ShorNineQubitCode {
    /// Returns the 8 standard stabilizer generators of the Shor [[9, 1, 3]] code.
    pub fn stabilizers() -> Vec<Pauli9> {
        vec![
            word("ZZIIIIIII"),
            word("IZZIIIIII"),
            word("IIIZZIIII"),
            word("IIIIZZIII"),
            word("IIIIIIZZI"),
            word("IIIIIIIZZ"),
            word("XXXXXXIII"),
            word("IIIXXXXXX"),
        ]
    }

    pub fn logical_x() -> Pauli9 {
        word("XXXXXXXXX")
    }

    pub fn logical_z() -> Pauli9 {
        word("ZIIZIIZII")
    }

    /// Extracts the 8-bit syndrome (0 for commuting, 1 for anticommuting).
    pub fn extract_syndrome(err: &Pauli9) -> [u8; 8] {
        let stabs = Self::stabilizers();
        let mut syn = [0u8; 8];
        for (i, stab) in stabs.iter().enumerate() {
            if pauli9_anticommutes(err, stab) {
                syn[i] = 1;
            }
        }
        syn
    }

    /// Decodes an 8-bit syndrome into a 9-qubit recovery Pauli operator.
    pub fn decode_syndrome(syn: &[u8; 8]) -> Pauli9 {
        let mut rec = [Pauli::I; 9];

        // Decode bit-flip in each block of 3
        for b in 0..3 {
            let q_in_b = decode_repetition_syndrome(syn[2 * b], syn[2 * b + 1]);
            if let Some(q) = q_in_b {
                rec[3 * b + q] = Pauli::X;
            }
        }

        // Decode phase-flip across blocks
        let p_block = decode_repetition_syndrome(syn[6], syn[7]);

        if let Some(b) = p_block {
            let target_q = 3 * b;
            rec[target_q] = match rec[target_q] {
                Pauli::X => Pauli::Y,
                _ => Pauli::Z,
            };
        }

        rec
    }

    /// Simulates error recovery on a single Pauli error.
    /// Returns true if the residual operator R * E commutes with logical X and logical Z
    /// and with all stabilizers (meaning it acts as identity on the code space).
    pub fn recover_error(err: &Pauli9) -> bool {
        let syn = Self::extract_syndrome(err);
        let rec = Self::decode_syndrome(&syn);
        let residual = pauli9_multiply(&rec, err);

        let stabs = Self::stabilizers();
        let commutes_stabs = stabs.iter().all(|s| !pauli9_anticommutes(&residual, s));
        let commutes_log_x = !pauli9_anticommutes(&residual, &Self::logical_x());
        let commutes_log_z = !pauli9_anticommutes(&residual, &Self::logical_z());

        commutes_stabs && commutes_log_x && commutes_log_z
    }
}

impl Default for ShorNineQubitCode {
    fn default() -> Self {
        Self::new()
    }
}

impl ShorNineQubitCode {
    /// Creates and verifies the Shor code properties and tests recovery across all 27 single-qubit Pauli errors.
    pub fn new() -> Self {
        let stabs = Self::stabilizers();
        let mut pairwise_commute = true;
        for i in 0..stabs.len() {
            for j in (i + 1)..stabs.len() {
                if pauli9_anticommutes(&stabs[i], &stabs[j]) {
                    pairwise_commute = false;
                    break;
                }
            }
        }

        let logical_anticommute = pauli9_anticommutes(&Self::logical_x(), &Self::logical_z());

        // n, k and the distance are computed from the generators, not declared.
        let code = StabilizerCode::try_new(stabs.iter().map(|s| s.to_vec()).collect())
            .checked_invariant_98942817("the eight Shor generators commute pairwise");
        let distance = code
            .distance()
            .checked_invariant_98942817("the Shor code encodes one qubit and its search fits the default budget");

        // Test all 27 single-qubit errors
        let mut recovered_count = 0;
        let total_errors = 9 * 3;
        for q in 0..9 {
            for err_p in [Pauli::X, Pauli::Y, Pauli::Z] {
                let mut err = [Pauli::I; 9];
                err[q] = err_p;
                if Self::recover_error(&err) {
                    recovered_count += 1;
                }
            }
        }

        Self {
            n_physical: code.n(),
            k_logical: code.k(),
            distance: distance.distance(),
            n_stabilizers: stabs.len(),
            all_stabilizers_pairwise_commute: pairwise_commute,
            logical_operators_anticommute: logical_anticommute,
            single_qubit_errors_recoverable: recovered_count,
            recovery_success_rate: rq(recovered_count as i64, total_errors as i64),
        }
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/shor.rs
// Claim: urn:core:crates_rs:core-quantum-physics:shor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord98942817 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord98942817` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError98942817 {
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
impl BoundaryError98942817 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError98942817 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError98942817 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord98942817 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError98942817> {
        if capacity_bound == 0 {
            return Err(BoundaryError98942817::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError98942817::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError98942817::ExceedsCapacity {
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
    use core_number_theory::rational::r_one;

    #[test]
    fn nine_letter_words_are_read_and_others_refused() {
        assert_eq!(pauli9_from_str("XXXXXXXXX"), Ok([Pauli::X; 9]));
        assert_eq!(
            pauli9_from_str("ZZIIIIIIQ"),
            Err(PauliError::UnknownLetter('Q'))
        );
        assert_eq!(
            pauli9_from_str("ZZIIIIII"),
            Err(PauliError::WrongLength {
                expected: 9,
                actual: 8
            })
        );
        assert_eq!(
            pauli9_from_str("ZZIIIIIIII"),
            Err(PauliError::WrongLength {
                expected: 9,
                actual: 10
            })
        );
        // Nine bytes but eight characters.
        assert_eq!("ZZIIIIIé".len(), 9);
        assert_eq!(
            pauli9_from_str("ZZIIIIIé"),
            Err(PauliError::UnknownLetter('é'))
        );
        assert_eq!(
            pauli9_from_str("ZZIIIIII\u{0}"),
            Err(PauliError::UnknownLetter('\u{0}'))
        );
    }

    #[test]
    fn test_shor_code_invariants() {
        let s = ShorNineQubitCode::new();
        assert_eq!(s.n_physical, 9);
        assert_eq!(s.k_logical, 1);
        assert_eq!(s.distance, 3);
        assert!(s.all_stabilizers_pairwise_commute);
        assert!(s.logical_operators_anticommute);
        assert_eq!(s.single_qubit_errors_recoverable, 27);
        assert_eq!(s.recovery_success_rate, r_one());
    }

    /// The distance is computed from the generators: its witness is a weight-3
    /// logical operator, and dropping the two X-type checks gives a different code,
    /// `[[9, 3, 1]]`, through the same computation.
    #[test]
    fn test_shor_distance_is_computed_from_the_generators() {
        let stabs = ShorNineQubitCode::stabilizers();
        let code = StabilizerCode::try_new(stabs.iter().map(|s| s.to_vec()).collect()).unwrap();
        let d = code.distance().unwrap();
        assert_eq!(d.distance(), ShorNineQubitCode::new().distance);
        assert_eq!(d.witness().iter().filter(|&&p| p != Pauli::I).count(), 3);
        assert!(code.is_logical(d.witness()).unwrap());

        let z_checks = StabilizerCode::try_new(stabs[..6].iter().map(|s| s.to_vec()).collect());
        let z_checks = z_checks.unwrap();
        assert_eq!(
            (z_checks.k(), z_checks.distance().unwrap().distance()),
            (3, 1)
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_98942817 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord98942817::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord98942817::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord98942817::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord98942817::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord98942817::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError98942817::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError98942817::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
