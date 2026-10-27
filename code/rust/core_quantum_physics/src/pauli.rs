//! The Pauli group: single-qubit letters, phased `n`-qubit strings, the symplectic
//! commutation form, and the exact matrices over `Q(i)`.
//!
//! The single-qubit Pauli letters `I, X, Y, Z` multiply as
//! `XY = iZ, YZ = iX, ZX = iY` (and the reversed products with `-i`). An `n`-qubit
//! Pauli element is `i^k P_1 (x) ... (x) P_n` with `k` in `Z/4`, a group of order
//! `4 * 4^n`, and two elements commute exactly when the binary symplectic form
//! `omega(A, B) = sum_i (x_i z'_i + z_i x'_i) mod 2` of their coordinates
//! `(x, z) in F_2^(2n)` is zero: `AB = (-1)^omega(A,B) BA`. These laws are checked by the
//! tests against the exact matrix products, not assumed:
//!
//! - [`Pauli::to_operator`] and [`PauliString::to_operator`] are the exact matrices over
//!   `Q(i)` (entries `0, +-1, +-i`), the only copies of the Pauli matrices that the
//!   exact tier of this crate needs; the `f64` face derives its Pauli matrices from
//!   them ([`Pauli::to_cmatrix`]), exactly, since every entry is representable;
//! - [`PauliString::multiply`] tracks the phase exactly;
//! - [`try_symplectic_inner_product`] refuses strings of different lengths. The older
//!   [`symplectic_inner_product`], [`pauli_commutes`] and [`pauli_anticommutes`] panic
//!   on unequal lengths and remain only because their callers
//!   (`stabilizer_code_distance`, `toric`, `shor`, `cochain_repair_code`,
//!   `foundational_targets`) still use them; they are superseded by the `try_`
//!   variants.
//!
//! Strings admit 1 through 4096 qubits; their dense matrices have the smaller
//! Hilbert-dimension limit. Qudit Weyl-Heisenberg operators and Clifford
//! conjugation are owned by `core_lie_theory`.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_4377d7a8<T> {
    fn checked_invariant_4377d7a8(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_4377d7a8<T> for Option<T> {
    #[inline]
    fn checked_invariant_4377d7a8(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_4377d7a8<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_4377d7a8(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::linear_algebra::complex_matrix::{CMatrix, C64};
use num_traits::ToPrimitive;
use core_number_theory::cyclotomic::GaussianRat;
use serde::{Deserialize, Serialize};

use crate::exact_operator::{ExactOperator, OperatorError};
use crate::hilbert_space::{HilbertError, HilbertSpace};

/// Maximum number of qubits in the exact symbolic Pauli string carrier.
pub const MAX_PAULI_STRING_QUBITS: usize = 4096;

/// Refusals for reading Pauli letters and words and for building their matrices.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum PauliError {
    #[error("{0:?} is not a Pauli letter (I, X, Y or Z)")]
    UnknownLetter(char),
    #[error("a Pauli word of {expected} letters was expected, got {actual}")]
    WrongLength { expected: usize, actual: usize },
    #[error("a Pauli string needs at least one letter")]
    Empty,
    #[error("a Pauli string of {qubits} qubits exceeds the limit {max}")]
    StringBudget { qubits: usize, max: usize },
    #[error("the matrix of the string is too large: {0}")]
    Carrier(HilbertError),
    #[error("exact operator refused: {0}")]
    Operator(OperatorError),
}

/// Discrete phase i^k, with k in Z/4.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[repr(u8)]
pub enum PhaseZ4 {
    P0 = 0,
    P1 = 1,
    P2 = 2,
    P3 = 3,
}
impl PhaseZ4 {
    pub fn from_u8(value: u8) -> Self {
        match value % 4 {
            0 => Self::P0,
            1 => Self::P1,
            2 => Self::P2,
            _ => Self::P3,
        }
    }
    pub fn as_u8(self) -> u8 {
        self as u8
    }
    pub fn mul(self, other: Self) -> Self {
        Self::from_u8(self.as_u8() + other.as_u8())
    }
    pub fn to_real_sign(self) -> Option<i8> {
        match self {
            Self::P0 => Some(1),
            Self::P2 => Some(-1),
            _ => None,
        }
    }
}

/// Single-qubit Pauli operator.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum Pauli {
    I,
    X,
    Y,
    Z,
}

impl Pauli {
    /// The four letters in the order `I, X, Y, Z`.
    pub const ALL: [Pauli; 4] = [Pauli::I, Pauli::X, Pauli::Y, Pauli::Z];

    /// Construct from the letters `I`, `X`, `Y`, `Z` (either case); any other
    /// character is refused.
    pub fn from_char(c: char) -> Result<Self, PauliError> {
        match c {
            'I' | 'i' => Ok(Pauli::I),
            'X' | 'x' => Ok(Pauli::X),
            'Y' | 'y' => Ok(Pauli::Y),
            'Z' | 'z' => Ok(Pauli::Z),
            _ => Err(PauliError::UnknownLetter(c)),
        }
    }

    /// Single-qubit anticommutation relation: {P, Q} = 0 iff P != I, Q != I, P != Q.
    pub fn anticommutes_with(self, other: Pauli) -> bool {
        self != Pauli::I && other != Pauli::I && self != other
    }

    /// Symplectic binary coordinates (x, z) in F_2^2.
    pub fn symplectic_coords(self) -> (u8, u8) {
        match self {
            Pauli::I => (0, 0),
            Pauli::X => (1, 0),
            Pauli::Z => (0, 1),
            Pauli::Y => (1, 1),
        }
    }

    /// Group multiplication modulo global phase factor (+/- 1, +/- i); see
    /// [`Pauli::product`] for the phase.
    pub fn multiply(self, other: Pauli) -> Pauli {
        self.product(other).1
    }

    /// The exact product `self * other = i^k * letter`, as `(k, letter)` with
    /// `k in {0, 1, 2, 3}`: `XY = iZ`, `YX = -iZ`, `P P = I`, `I P = P`.
    pub fn product(self, other: Pauli) -> (u8, Pauli) {
        match (self, other) {
            (Pauli::I, p) | (p, Pauli::I) => (0, p),
            (Pauli::X, Pauli::X) | (Pauli::Y, Pauli::Y) | (Pauli::Z, Pauli::Z) => (0, Pauli::I),
            (Pauli::X, Pauli::Y) => (1, Pauli::Z),
            (Pauli::Y, Pauli::X) => (3, Pauli::Z),
            (Pauli::Y, Pauli::Z) => (1, Pauli::X),
            (Pauli::Z, Pauli::Y) => (3, Pauli::X),
            (Pauli::Z, Pauli::X) => (1, Pauli::Y),
            (Pauli::X, Pauli::Z) => (3, Pauli::Y),
        }
    }

    /// Typed phase view of the already checked exact product table.
    pub fn mul_phased(self, other: Self) -> (PhaseZ4, Self) {
        let (phase, letter) = self.product(other);
        (PhaseZ4::from_u8(phase), letter)
    }

    /// The exact `2 x 2` matrix over `Q(i)`.
    pub fn to_operator(self) -> ExactOperator {
        use core_lie_theory::pauli_symplectic::{pauli, Pauli as Letter};
        let letter = match self {
            Self::I => Letter::Identity,
            Self::X => Letter::X,
            Self::Y => Letter::Y,
            Self::Z => Letter::Z,
        };
        let matrix = pauli::<GaussianRat>(letter).checked_invariant_4377d7a8("Q(i) contains the fixed Pauli letters");
        // The data has exactly 2 * 2 entries by construction above.
        ExactOperator::try_new(matrix).checked_invariant_4377d7a8("a 2x2 matrix with four entries is well formed")
    }

    /// The `f64` matrix derived from the exact one; every entry (`0, +-1, +-i`) is
    /// represented exactly.
    pub fn to_cmatrix(self) -> CMatrix {
        let exact = self.to_operator();
        CMatrix::from_fn(2, 2, |r, c| {
            // `get` is `Some` for r, c < 2, and `0, +-1` convert to f64 exactly.
            let z = exact.get(r, c).checked_invariant_4377d7a8("r, c < 2");
            C64::new(
                z.re.to_f64().checked_invariant_4377d7a8("0, +-1 fit in f64"),
                z.im.to_f64().checked_invariant_4377d7a8("0, +-1 fit in f64"),
            )
        })
    }

    /// The letter as a one-character string.
    pub fn letter(self) -> char {
        match self {
            Pauli::I => 'I',
            Pauli::X => 'X',
            Pauli::Y => 'Y',
            Pauli::Z => 'Z',
        }
    }
}

/// The binary symplectic inner product of two `n`-qubit Pauli strings,
/// `omega(A, B) = sum_i (x_i z'_i + z_i x'_i) mod 2`; unequal lengths are refused.
pub fn try_symplectic_inner_product(a: &[Pauli], b: &[Pauli]) -> Result<u8, PauliError> {
    if a.len() != b.len() {
        return Err(PauliError::WrongLength {
            expected: a.len(),
            actual: b.len(),
        });
    }
    let mut sum: u8 = 0;
    for (&pa, &pb) in a.iter().zip(b.iter()) {
        let (x1, z1) = pa.symplectic_coords();
        let (x2, z2) = pb.symplectic_coords();
        sum ^= (x1 & z2) ^ (z1 & x2);
    }
    Ok(sum)
}

/// Two multi-qubit Pauli operators commute iff their symplectic inner product is 0;
/// unequal lengths are refused.
pub fn try_pauli_commutes(a: &[Pauli], b: &[Pauli]) -> Result<bool, PauliError> {
    Ok(try_symplectic_inner_product(a, b)? == 0)
}

/// Evaluates the binary symplectic inner product across two n-qubit Pauli strings:
///   omega(A, B) = sum_{i=0}^{n-1} (x1_i * z2_i - z1_i * x2_i) mod 2.
///
/// # Panics
///
/// Panics when the strings have different lengths. Superseded by
/// [`try_symplectic_inner_product`]; kept for the callers that still use it.
pub fn symplectic_inner_product(a: &[Pauli], b: &[Pauli]) -> u8 {
    assert_eq!(a.len(), b.len(), "Pauli strings must have equal length");
    let mut sum: u8 = 0;
    for (&pa, &pb) in a.iter().zip(b.iter()) {
        let (x1, z1) = pa.symplectic_coords();
        let (x2, z2) = pb.symplectic_coords();
        sum ^= (x1 & z2) ^ (z1 & x2);
    }
    (sum % 2) as u8
}

/// Two multi-qubit Pauli operators anticommute iff their symplectic inner product is 1.
///
/// # Panics
///
/// Panics on unequal lengths; superseded by [`try_pauli_commutes`].
pub fn pauli_anticommutes(a: &[Pauli], b: &[Pauli]) -> bool {
    symplectic_inner_product(a, b) == 1
}

/// Two multi-qubit Pauli operators commute iff their symplectic inner product is 0.
///
/// # Panics
///
/// Panics on unequal lengths; superseded by [`try_pauli_commutes`].
pub fn pauli_commutes(a: &[Pauli], b: &[Pauli]) -> bool {
    symplectic_inner_product(a, b) == 0
}

/// An element `i^phase P_1 (x) ... (x) P_n` of the `n`-qubit Pauli group, `phase` in
/// `Z/4`.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize)]
pub struct PauliString {
    phase: u8,
    letters: Vec<Pauli>,
}

impl PauliString {
    /// The string with phase `1` and between 1 and 4096 letters.
    pub fn new(letters: Vec<Pauli>) -> Result<Self, PauliError> {
        Self::with_phase(0, letters)
    }

    /// `i^phase * letters`; the phase is reduced modulo 4.
    pub fn with_phase(phase: u8, letters: Vec<Pauli>) -> Result<Self, PauliError> {
        if letters.is_empty() {
            return Err(PauliError::Empty);
        }
        if letters.len() > MAX_PAULI_STRING_QUBITS {
            return Err(PauliError::StringBudget {
                qubits: letters.len(),
                max: MAX_PAULI_STRING_QUBITS,
            });
        }
        Ok(Self {
            phase: phase % 4,
            letters,
        })
    }

    /// Read a word such as `"XZI"`; other characters are refused.
    pub fn parse(word: &str) -> Result<Self, PauliError> {
        let qubits = word.chars().count();
        if qubits > MAX_PAULI_STRING_QUBITS {
            return Err(PauliError::StringBudget {
                qubits,
                max: MAX_PAULI_STRING_QUBITS,
            });
        }
        let letters = word
            .chars()
            .map(Pauli::from_char)
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(letters)
    }

    /// Incoming trimmed-word admission retains the checked nonempty carrier.
    pub fn try_parse(word: &str) -> Result<Self, PauliError> {
        Self::parse(word.trim())
    }

    pub fn identity(qubits: usize) -> Result<Self, PauliError> {
        if qubits > MAX_PAULI_STRING_QUBITS {
            return Err(PauliError::StringBudget {
                qubits,
                max: MAX_PAULI_STRING_QUBITS,
            });
        }
        Self::new(vec![Pauli::I; qubits])
    }

    /// The phase-free letters, suitable for symplectic basis descriptions.
    pub fn word(&self) -> String {
        self.letters.iter().map(|p| p.letter()).collect()
    }

    pub fn to_symplectic_vector(&self) -> Vec<u8> {
        self.letters
            .iter()
            .map(|p| p.symplectic_coords().0)
            .chain(self.letters.iter().map(|p| p.symplectic_coords().1))
            .collect()
    }
    pub fn to_symplectic_bools(&self) -> Vec<bool> {
        self.to_symplectic_vector()
            .into_iter()
            .map(|b| b != 0)
            .collect()
    }
    pub fn from_symplectic_coords(x: &[bool], z: &[bool]) -> Result<Self, PauliError> {
        if x.len() != z.len() {
            return Err(PauliError::WrongLength {
                expected: x.len(),
                actual: z.len(),
            });
        }
        if x.len() > MAX_PAULI_STRING_QUBITS {
            return Err(PauliError::StringBudget {
                qubits: x.len(),
                max: MAX_PAULI_STRING_QUBITS,
            });
        }
        Self::new(
            x.iter()
                .zip(z)
                .map(|(&x, &z)| match (x, z) {
                    (false, false) => Pauli::I,
                    (true, false) => Pauli::X,
                    (true, true) => Pauli::Y,
                    (false, true) => Pauli::Z,
                })
                .collect(),
        )
    }

    /// Factor the full phased product as i^k times a returned phase-zero word.
    /// The returned word clears its phase so callers accumulating k never count it twice.
    pub fn mul_phased(&self, other: &Self) -> Result<(PhaseZ4, Self), PauliError> {
        let mut product = self.multiply(other)?;
        let phase = PhaseZ4::from_u8(product.phase);
        product.phase = 0;
        Ok((phase, product))
    }

    pub fn anticommutes_with(&self, other: &Self) -> Result<bool, PauliError> {
        Ok(!self.commutes_with(other)?)
    }

    /// The exponent `k` of the phase `i^k`.
    pub fn phase(&self) -> u8 {
        self.phase
    }

    /// The letters.
    pub fn letters(&self) -> &[Pauli] {
        &self.letters
    }

    /// Number of qubits.
    pub fn len(&self) -> usize {
        self.letters.len()
    }

    /// Always `false`: a string has at least one letter.
    pub fn is_empty(&self) -> bool {
        false
    }

    /// The number of letters other than `I`.
    pub fn weight(&self) -> usize {
        self.letters.iter().filter(|&&p| p != Pauli::I).count()
    }

    /// The exact product `self * other`, with the phase tracked; unequal lengths are
    /// refused.
    pub fn multiply(&self, other: &Self) -> Result<Self, PauliError> {
        if self.len() != other.len() {
            return Err(PauliError::WrongLength {
                expected: self.len(),
                actual: other.len(),
            });
        }
        let mut phase = u32::from(self.phase) + u32::from(other.phase);
        let mut letters = Vec::with_capacity(self.len());
        for (&a, &b) in self.letters.iter().zip(&other.letters) {
            let (k, p) = a.product(b);
            phase = (phase + u32::from(k)) % 4;
            letters.push(p);
        }
        Ok(Self {
            phase: (phase % 4) as u8,
            letters,
        })
    }

    /// `self other = (-1)^omega other self`: the two strings commute exactly when the
    /// symplectic form vanishes. Unequal lengths are refused.
    pub fn commutes_with(&self, other: &Self) -> Result<bool, PauliError> {
        try_pauli_commutes(&self.letters, &other.letters)
    }

    /// The exact `2^n x 2^n` matrix `i^phase P_1 (x) ... (x) P_n` over `Q(i)`; `n` is
    /// bounded by the default Hilbert-dimension limit.
    pub fn to_operator(&self) -> Result<ExactOperator, PauliError> {
        HilbertSpace::qubits(self.len()).map_err(PauliError::Carrier)?;
        let mut acc = self.letters[0].to_operator();
        for letter in &self.letters[1..] {
            acc = acc
                .kron(&letter.to_operator())
                .map_err(PauliError::Operator)?;
        }
        let phase = match self.phase {
            0 => GaussianRat::one(),
            1 => GaussianRat::i(),
            2 => GaussianRat::from_ints(-1, 0),
            _ => GaussianRat::from_ints(0, -1),
        };
        Ok(acc.scale(&phase).map_err(PauliError::Operator)?)
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/pauli.rs
// Claim: urn:core:crates_rs:core-quantum-physics:pauli:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_single_qubit_pauli_algebra() {
        assert!(!Pauli::I.anticommutes_with(Pauli::X));
        assert!(Pauli::X.anticommutes_with(Pauli::Z));
        assert!(Pauli::X.anticommutes_with(Pauli::Y));
        assert!(Pauli::Y.anticommutes_with(Pauli::Z));
        assert_eq!(Pauli::X.multiply(Pauli::Z), Pauli::Y);
    }

    #[test]
    fn letters_are_read_and_other_characters_refused() {
        for (c, p) in [
            ('I', Pauli::I),
            ('x', Pauli::X),
            ('Y', Pauli::Y),
            ('z', Pauli::Z),
        ] {
            assert_eq!(Pauli::from_char(c), Ok(p));
        }
        for c in ['Q', ' ', '1', 'é'] {
            assert_eq!(Pauli::from_char(c), Err(PauliError::UnknownLetter(c)));
        }
    }

    #[test]
    fn test_multi_qubit_commutation() {
        // [X \otimes X, Z \otimes Z] has 2 anticommutes => (-1)^2 = +1 => commutes!
        let a = [Pauli::X, Pauli::X];
        let b = [Pauli::Z, Pauli::Z];
        assert!(pauli_commutes(&a, &b));

        // [X \otimes I, Z \otimes I] has 1 anticommute => anticommutes!
        let c = [Pauli::X, Pauli::I];
        let d = [Pauli::Z, Pauli::I];
        assert!(pauli_anticommutes(&c, &d));
    }

    /// The product table, including its phase, agrees with the exact matrix product for
    /// all sixteen ordered pairs of letters.
    #[test]
    fn the_letter_product_table_matches_the_exact_matrices() {
        let phase = |k: u8| match k {
            0 => GaussianRat::one(),
            1 => GaussianRat::i(),
            2 => GaussianRat::from_ints(-1, 0),
            _ => GaussianRat::from_ints(0, -1),
        };
        for a in Pauli::ALL {
            for b in Pauli::ALL {
                let (k, p) = a.product(b);
                let lhs = a.to_operator().mul(&b.to_operator()).unwrap();
                let rhs = p.to_operator().scale(&phase(k)).unwrap();
                assert_eq!(lhs, rhs, "{a:?} {b:?}");
            }
        }
        assert_eq!(Pauli::X.product(Pauli::Y), (1, Pauli::Z));
        assert_eq!(Pauli::Y.product(Pauli::X), (3, Pauli::Z));
    }

    /// `AB = (-1)^omega BA` for every pair of two-qubit strings, decided on exact
    /// matrices: the commutator vanishes iff the symplectic form does, and otherwise the
    /// anticommutator does.
    #[test]
    fn the_symplectic_form_decides_commutation_on_every_two_qubit_pair() {
        let all: Vec<PauliString> = Pauli::ALL
            .iter()
            .flat_map(|&a| {
                Pauli::ALL
                    .iter()
                    .map(move |&b| PauliString::new(vec![a, b]).unwrap())
            })
            .collect();
        assert_eq!(all.len(), 16);
        for a in &all {
            for b in &all {
                let (ma, mb) = (a.to_operator().unwrap(), b.to_operator().unwrap());
                let commute = a.commutes_with(b).unwrap();
                if commute {
                    assert!(ma.commutator(&mb).unwrap().is_zero(), "{a:?} {b:?}");
                } else {
                    assert!(ma.anticommutator(&mb).unwrap().is_zero(), "{a:?} {b:?}");
                    assert!(!ma.commutator(&mb).unwrap().is_zero());
                }
            }
        }
    }

    /// The string product, with its phase, is the matrix product; and the symplectic
    /// coordinates add modulo 2 (the Pauli group modulo phase is an `F_2`-space).
    #[test]
    fn string_multiplication_tracks_the_phase_exactly() {
        let all: Vec<PauliString> = Pauli::ALL
            .iter()
            .flat_map(|&a| {
                Pauli::ALL
                    .iter()
                    .map(move |&b| PauliString::new(vec![a, b]).unwrap())
            })
            .collect();
        for a in &all {
            for b in &all {
                let product = a.multiply(b).unwrap();
                assert_eq!(
                    a.to_operator()
                        .unwrap()
                        .mul(&b.to_operator().unwrap())
                        .unwrap(),
                    product.to_operator().unwrap(),
                    "{a:?} {b:?}"
                );
                for ((pa, pb), pc) in a.letters().iter().zip(b.letters()).zip(product.letters()) {
                    let ((xa, za), (xb, zb), (xc, zc)) = (
                        pa.symplectic_coords(),
                        pb.symplectic_coords(),
                        pc.symplectic_coords(),
                    );
                    assert_eq!((xa ^ xb, za ^ zb), (xc, zc));
                }
            }
        }
    }

    /// The group generated by `X_i, Z_i` alone has order `2 * 4^n` (the phases are only
    /// `+-1`: 8 for one qubit, 32 for two); adding the scalar `i` gives the full Pauli
    /// group of order `4 * 4^n` (16 and 64).
    #[test]
    fn the_pauli_group_has_order_four_times_four_to_the_n() {
        let closure = |generators: &[PauliString], n: usize| {
            let mut group = std::collections::BTreeSet::new();
            group.insert(PauliString::new(vec![Pauli::I; n]).unwrap());
            loop {
                let before = group.len();
                let snapshot: Vec<PauliString> = group.iter().cloned().collect();
                for element in &snapshot {
                    for g in generators {
                        group.insert(element.multiply(g).unwrap());
                    }
                }
                if group.len() == before {
                    return group.len();
                }
            }
        };
        for n in 1..=2usize {
            let mut generators = Vec::new();
            for i in 0..n {
                for letter in [Pauli::X, Pauli::Z] {
                    let mut letters = vec![Pauli::I; n];
                    letters[i] = letter;
                    generators.push(PauliString::new(letters).unwrap());
                }
            }
            assert_eq!(
                closure(&generators, n),
                2 * 4usize.pow(n as u32),
                "real group, n = {n}"
            );
            generators.push(PauliString::with_phase(1, vec![Pauli::I; n]).unwrap());
            assert_eq!(
                closure(&generators, n),
                4 * 4usize.pow(n as u32),
                "full group, n = {n}"
            );
        }
    }

    #[test]
    fn checked_functions_refuse_what_the_legacy_ones_panic_on() {
        let a = [Pauli::X, Pauli::Z];
        let b = [Pauli::X];
        assert_eq!(
            try_symplectic_inner_product(&a, &b),
            Err(PauliError::WrongLength {
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(
            PauliString::parse("XZ")
                .unwrap()
                .commutes_with(&PauliString::parse("X").unwrap()),
            Err(PauliError::WrongLength {
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(PauliString::new(vec![]), Err(PauliError::Empty));
        assert_eq!(
            PauliString::parse("XQ"),
            Err(PauliError::UnknownLetter('Q'))
        );
        // The limit on the matrix size is a refusal, not an allocation.
        let big = PauliString::new(vec![Pauli::Z; 11]).unwrap();
        assert!(matches!(big.to_operator(), Err(PauliError::Carrier(_))));
    }

    #[test]
    fn the_float_matrices_are_the_exact_ones() {
        let y = Pauli::Y.to_cmatrix();
        assert_eq!(y[(0, 1)], C64::new(0.0, -1.0));
        assert_eq!(y[(1, 0)], C64::new(0.0, 1.0));
        let z = Pauli::Z.to_cmatrix();
        assert_eq!(z[(1, 1)], C64::new(-1.0, 0.0));
    }

    #[test]
    fn weight_counts_non_identity_letters() {
        assert_eq!(PauliString::parse("XIZIY").unwrap().weight(), 3);
        assert_eq!(
            PauliString::with_phase(5, vec![Pauli::X]).unwrap().phase(),
            1
        );
    }
}

impl std::fmt::Display for Pauli {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.letter())
    }
}
impl std::fmt::Display for PauliString {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let prefix = match self.phase {
            0 => "",
            1 => "i*",
            2 => "-",
            _ => "-i*",
        };
        write!(f, "{prefix}{}", self.word())
    }
}
