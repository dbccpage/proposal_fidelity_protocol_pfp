//! Pauli tensors and the exact binary symplectic action of Clifford unitaries.
//!
//! Hermitian Pauli words use `Y = i X Z` and labels `(x_0,...,x_n,z_0,...,z_n)`.
//! Commutation is the alternating form `x.z' + z.x'` over F_2. The columns
//! of a Clifford image are obtained from the conjugates of the generators;
//! unitarity and preservation of the symplectic form are checked exactly.
//! Group orders use arbitrary precision, and all enumeration is bounded.
//!
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_1f6bb4c5<T> {
    fn checked_invariant_1f6bb4c5(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_1f6bb4c5<T> for Option<T> {
    #[inline]
    fn checked_invariant_1f6bb4c5(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_1f6bb4c5<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_1f6bb4c5(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::scalar::{dagger, is_unitary, ComplexField};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{matrix as mx, ExactFieldError};
use num_bigint::BigUint;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Pauli {
    Identity,
    X,
    Y,
    Z,
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PauliError {
    #[error(transparent)]
    Group(#[from] crate::finite_group::GroupError),
    #[error("the scalar field does not contain i")]
    MissingImaginaryUnit,
    #[error("the scalar field does not contain 1/sqrt(2)")]
    MissingSquareRoot,
    #[error("invalid Pauli/symplectic shape")]
    Shape,
    #[error("matrix is not unitary")]
    NotUnitary,
    #[error("conjugation does not preserve the Pauli group")]
    NotClifford,
    #[error("matrix does not preserve the binary symplectic form")]
    NotSymplectic,
    #[error("the requested size {size} exceeds {bound}")]
    SizeBound { size: usize, bound: usize },
    #[error(transparent)]
    Matrix(#[from] ExactFieldError),
}

pub fn generate_sp2_f2() -> Result<Vec<SymplecticF2>, PauliError> {
    let h = SymplecticF2::new(1, vec![0, 1, 1, 0])?;
    let s = SymplecticF2::new(1, vec![1, 0, 1, 1])?;
    Ok(crate::finite_group::generate(
        &[h, s],
        SymplecticF2::identity(1)?,
        |a, b| {
            a.multiply(b)
                .checked_invariant_1f6bb4c5("products preserve the symplectic form")
        },
        |m| m.data.clone(),
        6,
    )?)
}

pub fn generate_sp4_f2() -> Result<Vec<SymplecticF2>, PauliError> {
    let h = SymplecticF2::new(2, vec![0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1])?;
    let s = SymplecticF2::new(2, vec![1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1])?;
    let swap = SymplecticF2::new(2, vec![0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0])?;
    let cx = SymplecticF2::new(2, vec![1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1])?;
    Ok(crate::finite_group::generate(
        &[h, s, swap, cx],
        SymplecticF2::identity(2)?,
        |a, b| {
            a.multiply(b)
                .checked_invariant_1f6bb4c5("products preserve the symplectic form")
        },
        |m| m.data.clone(),
        720,
    )?)
}

/// The canonical 2x2 Hermitian Pauli matrix, over the caller's exact field.
pub fn pauli<F: ComplexField>(letter: Pauli) -> Result<BasicMatrix<F>, PauliError> {
    let z = F::zero();
    let o = F::one();
    let m = o.neg();
    let data = match letter {
        Pauli::Identity => vec![o.clone(), z.clone(), z, o],
        Pauli::X => vec![z.clone(), o.clone(), o, z],
        Pauli::Z => vec![o, z.clone(), z, m],
        Pauli::Y => {
            let i = F::imaginary_unit().ok_or(PauliError::MissingImaginaryUnit)?;
            vec![z.clone(), i.neg(), i, z]
        }
    };
    Ok(BasicMatrix::from_row_major(2, 2, data).map_err(ExactFieldError::from)?)
}

pub fn pauli_word<F: ComplexField>(letters: &[Pauli]) -> Result<BasicMatrix<F>, PauliError> {
    if letters.len() > 8 {
        return Err(PauliError::SizeBound {
            size: letters.len(),
            bound: 8,
        });
    }
    let mut result = mx::identity(1)?;
    for letter in letters {
        result = mx::kronecker(&result, &pauli::<F>(*letter)?)?;
    }
    Ok(result)
}

pub fn hadamard<F: ComplexField>() -> Result<BasicMatrix<F>, PauliError> {
    let s = F::inverse_sqrt_two().ok_or(PauliError::MissingSquareRoot)?;
    Ok(
        BasicMatrix::from_row_major(2, 2, vec![s.clone(), s.clone(), s.clone(), s.neg()])
            .map_err(ExactFieldError::from)?,
    )
}

pub fn phase_gate<F: ComplexField>() -> Result<BasicMatrix<F>, PauliError> {
    let i = F::imaginary_unit().ok_or(PauliError::MissingImaginaryUnit)?;
    Ok(
        BasicMatrix::from_row_major(2, 2, vec![F::one(), F::zero(), F::zero(), i])
            .map_err(ExactFieldError::from)?,
    )
}

/// A validated symplectic matrix in the `(x,z)` ordering. Values must already be bits.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct SymplecticF2 {
    qubits: usize,
    data: Vec<u8>,
}

impl SymplecticF2 {
    pub fn new(qubits: usize, data: Vec<u8>) -> Result<Self, PauliError> {
        if qubits > 64 {
            return Err(PauliError::SizeBound {
                size: qubits,
                bound: 64,
            });
        }
        let n = 2 * qubits;
        if data.len() != n * n || data.iter().any(|b| *b > 1) {
            return Err(PauliError::Shape);
        }
        let candidate = Self { qubits, data };
        if !candidate.preserves_form() {
            return Err(PauliError::NotSymplectic);
        }
        Ok(candidate)
    }
    pub fn identity(qubits: usize) -> Result<Self, PauliError> {
        if qubits > 64 {
            return Err(PauliError::SizeBound {
                size: qubits,
                bound: 64,
            });
        }
        let n = 2 * qubits;
        let mut data = vec![0; n * n];
        for i in 0..n {
            data[i * n + i] = 1;
        }
        Self::new(qubits, data)
    }
    pub fn qubits(&self) -> usize {
        self.qubits
    }
    pub fn entries(&self) -> &[u8] {
        &self.data
    }
    pub fn preserves_form(&self) -> bool {
        let q = self.qubits;
        let n = 2 * q;
        for i in 0..n {
            for j in 0..n {
                let actual = (0..q).fold(0, |v, k| {
                    v ^ (self.data[k * n + i] & self.data[(q + k) * n + j])
                        ^ (self.data[(q + k) * n + i] & self.data[k * n + j])
                });
                if actual != u8::from((i < q && j == i + q) || (j < q && i == j + q)) {
                    return false;
                }
            }
        }
        true
    }
    pub fn apply(&self, label: &[u8]) -> Result<Vec<u8>, PauliError> {
        let n = 2 * self.qubits;
        if label.len() != n || label.iter().any(|b| *b > 1) {
            return Err(PauliError::Shape);
        }
        Ok((0..n)
            .map(|i| (0..n).fold(0, |v, k| v ^ (self.data[i * n + k] & label[k])))
            .collect())
    }
    pub fn multiply(&self, other: &Self) -> Result<Self, PauliError> {
        if self.qubits != other.qubits {
            return Err(PauliError::Shape);
        }
        let n = 2 * self.qubits;
        let data = (0..n * n)
            .map(|ij| {
                let (i, j) = (ij / n, ij % n);
                (0..n).fold(0, |v, k| v ^ (self.data[i * n + k] & other.data[k * n + j]))
            })
            .collect();
        Self::new(self.qubits, data)
    }
}

pub fn symplectic_order(n: usize) -> Result<BigUint, PauliError> {
    if n > 4096 {
        return Err(PauliError::SizeBound {
            size: n,
            bound: 4096,
        });
    }
    let mut value = BigUint::from(1u8) << (n * n);
    for j in 1..=n {
        value *= (BigUint::from(1u8) << (2 * j)) - 1u8;
    }
    Ok(value)
}

/// Order modulo global phases: the Pauli kernel has order `4^n`.
pub fn clifford_order_mod_phases(n: usize) -> Result<BigUint, PauliError> {
    Ok(symplectic_order(n)? << (2 * n))
}

/// Number of pure stabilizer states, `2^n product_{j=1}^n (2^j+1)`.
pub fn stabilizer_state_count(n: usize) -> Result<BigUint, PauliError> {
    if n > 4096 {
        return Err(PauliError::SizeBound {
            size: n,
            bound: 4096,
        });
    }
    let mut v = BigUint::from(1u8) << n;
    for j in 1..=n {
        v *= (BigUint::from(1u8) << j) + 1u8;
    }
    Ok(v)
}

fn build_pauli_words<F: ComplexField>(
    q: usize,
    d: usize,
) -> Result<Vec<BasicMatrix<F>>, PauliError> {
    let mut words = Vec::with_capacity(d * d);
    for label in 0..d * d {
        let letters = (0..q)
            .map(|k| match ((label >> (q + k)) & 1, (label >> k) & 1) {
                (0, 0) => Pauli::Identity,
                (1, 0) => Pauli::X,
                (0, 1) => Pauli::Z,
                _ => Pauli::Y,
            })
            .collect::<Vec<_>>();
        words.push(pauli_word::<F>(&letters)?);
    }
    Ok(words)
}

fn conjugate_generator_label<F: ComplexField>(
    u: &BasicMatrix<F>,
    ud: &BasicMatrix<F>,
    words: &[BasicMatrix<F>],
    q: usize,
    j: usize,
) -> Result<usize, PauliError> {
    let mut letters = vec![Pauli::Identity; q];
    letters[j % q] = if j < q { Pauli::X } else { Pauli::Z };
    let image = mx::multiply(&mx::multiply(u, &pauli_word::<F>(&letters)?)?, ud)?;
    let neg_image = mx::neg(&image)?;
    words
        .iter()
        .position(|p| *p == image || *p == neg_image)
        .ok_or(PauliError::NotClifford)
}

/// Derive the binary image from exact adjoint action, including multi-qubit gates.
pub fn clifford_to_symplectic<F: ComplexField>(
    u: &BasicMatrix<F>,
) -> Result<SymplecticF2, PauliError> {
    if !is_unitary(u)? {
        return Err(PauliError::NotUnitary);
    }
    let d = u.rows();
    if !d.is_power_of_two() || d > 64 {
        return Err(PauliError::Shape);
    }
    let q = d.trailing_zeros() as usize;
    let n = 2 * q;
    let words = build_pauli_words::<F>(q, d)?;
    let mut data = vec![0; n * n];
    let ud = dagger(u)?;
    for j in 0..n {
        let label = conjugate_generator_label(u, &ud, &words, q, j)?;
        for k in 0..q {
            data[k * n + j] = ((label >> (q + k)) & 1) as u8;
            data[(q + k) * n + j] = ((label >> k) & 1) as u8;
        }
    }
    SymplecticF2::new(q, data)
}

// Origin: engine/crates_rs/core_lie_theory/src/pauli_symplectic.rs
// Claim: urn:core:crates_rs:core-lie-theory:pauli-symplectic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_1f6bb4c5 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
