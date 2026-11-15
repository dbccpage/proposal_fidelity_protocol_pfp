//! Permutations of `0..n` in one-line notation, for the workflow hosts.
//!
//! AuthorityEffect: None.
//! Contract: urn:pfp-operads:perm:v1
//!
//! A permutation is the list of images: entry `i` is where `i` goes. Products are taken in
//! reading order, so `compose(p, q)` applies `p` and then `q`. The same product can be taken
//! over permutation matrices, which gives a second way to fold a word of permutations.

use crate::datum::Datum;

/// A permutation of `0..n`: entry `i` is the image of `i`.
pub type Perm = Vec<usize>;

/// A square matrix of small non-negative integers.
pub type Matrix = Vec<Vec<u64>>;

/// Whether the images are each of `0..n` once, for `n` the number of images.
pub fn is_permutation(images: &[usize]) -> bool {
    let mut seen = vec![false; images.len()];
    images.iter().all(|&image| {
        seen.get_mut(image)
            .is_some_and(|slot| !std::mem::replace(slot, true))
    })
}

/// The permutation of `0..n` a value denotes: a list of `n` exact integers that has each of
/// `0..n` once.
pub fn read(datum: &Datum, n: usize) -> Option<Perm> {
    let images: Perm = datum
        .as_list()?
        .iter()
        .map(Datum::as_count)
        .collect::<Option<_>>()?;
    (images.len() == n && is_permutation(&images)).then_some(images)
}

pub fn identity(n: usize) -> Perm {
    (0..n).collect()
}

/// Apply `p`, then `q`. An image `q` does not have is left where `p` put it.
pub fn compose(p: &[usize], q: &[usize]) -> Perm {
    p.iter()
        .map(|&middle| q.get(middle).copied().unwrap_or(middle))
        .collect()
}

/// The permutation that undoes `p`.
pub fn inverse(p: &[usize]) -> Perm {
    let mut back = identity(p.len());
    for (from, &to) in p.iter().enumerate() {
        if let Some(slot) = back.get_mut(to) {
            *slot = from;
        }
    }
    back
}

/// The matrix of `p`: row `i` has its 1 in column `p[i]`, so the matrix of `compose(p, q)` is
/// the product of the matrix of `p` and the matrix of `q`.
pub fn matrix(p: &[usize]) -> Matrix {
    p.iter()
        .map(|&image| {
            (0..p.len())
                .map(|column| u64::from(column == image))
                .collect()
        })
        .collect()
}

/// The product of two matrices. A row or column one side lacks is read as zeros, and a sum too
/// large for 64 bits stays at the largest value.
pub fn product(a: &[Vec<u64>], b: &[Vec<u64>]) -> Matrix {
    let width = b.iter().map(Vec::len).max().unwrap_or(0);
    a.iter()
        .map(|row| {
            (0..width)
                .map(|column| {
                    row.iter().zip(b).fold(0u64, |sum, (&left, right)| {
                        let entry = right.get(column).copied().unwrap_or(0);
                        sum.saturating_add(left.saturating_mul(entry))
                    })
                })
                .collect()
        })
        .collect()
}

/// The permutation a matrix is the matrix of, or nothing if it is not a permutation matrix.
pub fn of_matrix(matrix: &[Vec<u64>]) -> Option<Perm> {
    let n = matrix.len();
    let images: Perm = matrix
        .iter()
        .map(|row| {
            let ones = row.iter().filter(|&&entry| entry == 1).count();
            let zeros = row.iter().filter(|&&entry| entry == 0).count();
            if row.len() == n && ones == 1 && zeros + 1 == n {
                row.iter().position(|&entry| entry == 1)
            } else {
                None
            }
        })
        .collect::<Option<_>>()?;
    is_permutation(&images).then_some(images)
}
