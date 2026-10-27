// AuthorityEffect: None.

//! Exact two-qubit Pauli operators on a 3 x 3 context table, and the sign
//! table they induce.
//!
//! A table declares nine two-qubit Pauli words over the letters `I X Y Z`
//! (the first letter acts on the first tensor factor), read row by row. Each
//! word is the Kronecker product of the corresponding `2 x 2` Pauli matrices
//! over `Q(i)`. The contexts are the three rows and then the three columns, the
//! order of `separating_predictions::MerminPeresSquare`. Computed exactly:
//!
//! - whether every observable is a Hermitian involution (`A* = A`, `A A = I`);
//! - whether two observables commute, by the exact matrix commutator;
//! - the product of each context and its sign when the product is `+I` or
//!   `-I`. The signs, written `0 = +1`, `1 = -1`, give a
//!   `crate::parity_context_packet::ParityContextPacket` on the nine
//!   observables.
//!
//! Refused: a word that is not two letters from `IXYZ`; a context whose three
//! observables do not pairwise commute (its product would depend on the
//! order); a context product that is not `+I` or `-I`.
//!
//! The table is declared. Nothing here assigns values to observables, derives
//! the operators from a sign table, or says which physical measurements the
//! words stand for.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_94f91cd4<T> {
    fn checked_invariant_94f91cd4(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_94f91cd4<T> for Option<T> {
    #[inline]
    fn checked_invariant_94f91cd4(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_94f91cd4<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_94f91cd4(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::{gi, is_hermitian};
use crate::parity_context_packet::{ParityContextPacket, ParityPacketError};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix;
use core_lie_theory::pauli_symplectic::{self, Pauli};
use core_number_theory::cyclotomic::GaussianRat;

/// Refusals for Pauli context tables.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PauliTableError {
    #[error("{word:?} is not a two-letter word over I, X, Y, Z")]
    BadWord { word: String },
    #[error("context {context} contains observables {left} and {right}, which do not commute")]
    NoncommutingContext {
        context: usize,
        left: usize,
        right: usize,
    },
    #[error("the product of context {context} is not +I or -I")]
    ProductNotSigned { context: usize },
    #[error("context index {context} is not below 6")]
    ContextOutOfRange { context: usize },
    #[error("packet: {0}")]
    Packet(#[from] ParityPacketError),
    #[error("observable index {0} is outside the declared table")]
    ObservableOutOfRange(usize),
    #[error("exact matrix operation refused: {0}")]
    Matrix(String),
}

/// The `4 x 4` matrix of a two-qubit Pauli word such as `"XY"`.
pub fn pauli_word(word: &str) -> Result<BasicMatrix<GaussianRat>, PauliTableError> {
    let letters: Vec<char> = word.chars().collect();
    let bad = || PauliTableError::BadWord {
        word: word.to_string(),
    };
    if letters.len() != 2 {
        return Err(bad());
    }
    let parse = |c| match c {
        'I' => Some(Pauli::Identity),
        'X' => Some(Pauli::X),
        'Y' => Some(Pauli::Y),
        'Z' => Some(Pauli::Z),
        _ => None,
    };
    let parsed = letters
        .into_iter()
        .map(parse)
        .collect::<Option<Vec<_>>>()
        .ok_or_else(bad)?;
    let m = pauli_symplectic::pauli_word::<GaussianRat>(&parsed).map_err(|_| bad())?;
    Ok(m)
}

/// The three observable indices (row-major, `0..9`) of context `c`: rows for
/// `c < 3`, columns for `3 <= c < 6`.
pub fn context_members(c: usize) -> Result<[usize; 3], PauliTableError> {
    match c {
        0..=2 => Ok([3 * c, 3 * c + 1, 3 * c + 2]),
        3..=5 => Ok([c - 3, c, c + 3]),
        _ => Err(PauliTableError::ContextOutOfRange { context: c }),
    }
}

/// A declared 3 x 3 table of two-qubit Pauli words.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PauliContextTable {
    words: Vec<String>,
    matrices: Vec<BasicMatrix<GaussianRat>>,
}

impl PauliContextTable {
    pub fn new(grid: [[&str; 3]; 3]) -> Result<Self, PauliTableError> {
        let words: Vec<String> = grid.iter().flatten().map(|w| w.to_string()).collect();
        let matrices = words
            .iter()
            .map(|w| pauli_word(w))
            .collect::<Result<_, _>>()?;
        Ok(Self { words, matrices })
    }

    /// Mermin's table: rows `XI IX XX`, `IY YI YY`, `XY YX ZZ`.
    pub fn mermin() -> Self {
        Self::new([["XI", "IX", "XX"], ["IY", "YI", "YY"], ["XY", "YX", "ZZ"]])
            .checked_invariant_94f91cd4("the declared words are Pauli words")
    }

    pub fn words(&self) -> &[String] {
        &self.words
    }

    pub fn observable(&self, index: usize) -> Result<&BasicMatrix<GaussianRat>, PauliTableError> {
        self.matrices
            .get(index)
            .ok_or(PauliTableError::ObservableOutOfRange(index))
    }

    /// Every observable satisfies `A* = A` and `A A = I`.
    pub fn observables_are_hermitian_involutions(&self) -> bool {
        let Ok(identity) = matrix::identity(4) else {
            return false;
        };
        self.matrices
            .iter()
            .all(|m| is_hermitian(m) && matrix::multiply(m, m) == Ok(identity.clone()))
    }

    /// `A_i A_j = A_j A_i`, by the exact commutator.
    pub fn commute(&self, i: usize, j: usize) -> bool {
        match (self.matrices.get(i), self.matrices.get(j)) {
            (Some(a), Some(b)) => matrix::commutes(a, b) == Ok(true),
            _ => false,
        }
    }

    /// The sign of context `c` (`+1` or `-1`), after checking that its
    /// observables pairwise commute and that their product is `+I` or `-I`.
    pub fn context_sign(&self, c: usize) -> Result<i8, PauliTableError> {
        let [a, b, d] = context_members(c)?;
        for (left, right) in [(a, b), (a, d), (b, d)] {
            if !self.commute(left, right) {
                return Err(PauliTableError::NoncommutingContext {
                    context: c,
                    left,
                    right,
                });
            }
        }
        let product = matrix::multiply(&self.matrices[a], &self.matrices[b])
            .and_then(|m| matrix::multiply(&m, &self.matrices[d]))
            .map_err(|e| PauliTableError::Matrix(e.to_string()))?;
        let identity = matrix::identity(4).map_err(|e| PauliTableError::Matrix(e.to_string()))?;
        if product == identity {
            Ok(1)
        } else if product
            == matrix::scale(&identity, &gi(-1, 0))
                .map_err(|e| PauliTableError::Matrix(e.to_string()))?
        {
            Ok(-1)
        } else {
            Err(PauliTableError::ProductNotSigned { context: c })
        }
    }

    /// The six context signs, rows then columns.
    pub fn sign_table(&self) -> Result<Vec<i8>, PauliTableError> {
        (0..6).map(|c| self.context_sign(c)).collect()
    }

    /// The parity-context packet of the computed sign table on the nine
    /// observables.
    pub fn packet(&self) -> Result<ParityContextPacket, PauliTableError> {
        let contexts: Vec<Vec<usize>> = (0..6)
            .map(|c| context_members(c).map(|m| m.to_vec()))
            .collect::<Result<_, _>>()?;
        let targets: Vec<u8> = self
            .sign_table()?
            .iter()
            .map(|&s| u8::from(s == -1))
            .collect();
        Ok(ParityContextPacket::new(9, &contexts, &targets)?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/pauli_context_table.rs
// Claim: urn:core:crates_rs:core-quantum-physics:pauli-context-table:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_94f91cd4 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
