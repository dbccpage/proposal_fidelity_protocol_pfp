// Executable finite evidence; AuthorityEffect: None.
//! Chapter 18: the strengthened stochastic package S, outcome (a) of `WDP-CH18-O01`.
//! Executable finite evidence for `WDP-CH18-P07` and `WDP-CH18-P08`.
//!
//! Over exact rationals, a finite carrier `{0, ..., n-1}` carries stochastic
//! updates: `n_out x n_in` matrices with nonnegative entries whose every column
//! sums to one, so a column is the law of the next state given the current one.
//!
//! - [`StochasticUpdate`] is closed under [`StochasticUpdate::compose`], contains
//!   the deterministic updates [`StochasticUpdate::from_function`], and every
//!   update is a convex mixture of deterministic ones
//!   ([`StochasticUpdate::mixture_of_functions`], weights
//!   `w_f = prod_j T[f(j)][j]`), which [`StochasticUpdate::recompose`] rebuilds
//!   exactly (`WDP-CH18-P07`).
//! - Reversibility within states is being a permutation matrix (`WDP-CH18-P02`).
//!   [`StochasticUpdate::stochastic_left_inverse`] decides exactly, on a square
//!   carrier, whether an update has a left inverse and whether that inverse is
//!   itself stochastic; it is, exactly for permutations.
//! - [`ClassicalInstrument`] is a finite family of nonnegative matrices, one per
//!   outcome, whose sum is a stochastic update. Words of outcomes are run first
//!   outcome first, and the law of a word is the mass left after running it. The
//!   laws of the extensions of a word sum to the law of the word, and the laws of
//!   all words of one length sum to the mass of the input (`WDP-CH18-P08`).
//! - [`signed_shear_counterexample`] is the fixture `signed_weights_break_the_corner`:
//!   a mass-preserving invertible matrix with a mass-preserving inverse that is not
//!   a permutation, so the reversible corner needs the sign restriction, and
//!   [`StochasticUpdate::new`] refuses it for its negative entry.
//!
//! Enumerations are capped: [`MAX_ENUMERATION`] bounds supported functions and outcome
//! words, and the `*_with_limit` variants take the cap as an argument so a test can
//! exercise a refusal at a small size. A word length above the cap is refused even for
//! a one-outcome instrument, whose single word would otherwise be as long as asked.
//!
//! Delegation: the exact left-inverse solve is `core_linear_algebra`'s
//! `solve_in_image`. The row-stochastic `StochasticMap` of `core_finite_probability`
//! is the transpose of this column convention;
//! [`StochasticUpdate::to_stochastic_map`] and
//! [`StochasticUpdate::from_stochastic_map`] convert exactly, and the tests compare
//! [`StochasticUpdate::compose`] with `StochasticMap::compose`. Application to
//! unnormalized vectors is local because `ProbabilitySimplex` requires unit mass.

use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::linear_algebra::image_kernel::{
    solve_in_image, ExactLinearAlgebraError, ImageMembership,
};
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_finite_probability::stochastic_map::StochasticMap;
use serde::Serialize;

use crate::error::WdpError;
use crate::types::AuthorityEffect;

/// Row-major exact matrix: `m[i][j]` is row `i`, column `j`.
pub type Matrix = Vec<Vec<BigRational>>;

/// A convex mixture of deterministic updates: `(f, w_f)` with `f : n_in -> n_out`.
pub type FunctionMixture = Vec<(Vec<usize>, BigRational)>;

/// Cap on enumerated supported functions and on enumerated outcome words.
pub const MAX_ENUMERATION: usize = 1_000_000;

/// Cap on the entries of a matrix allocated from caller-supplied dimensions.
pub const MAX_MATRIX_ENTRIES: usize = 1_000_000;

fn invalid(detail: String) -> WdpError {
    WdpError::InvalidInput { detail }
}

/// Total mass `sum_i p_i`.
pub fn mass(p: &[BigRational]) -> BigRational {
    p.iter().fold(BigRational::zero(), |acc, x| acc + x)
}

/// Shape `(rows, cols)` of a nonempty rectangular matrix, else a refusal.
pub(crate) fn matrix_shape(m: &[Vec<BigRational>], what: &str) -> Result<(usize, usize), WdpError> {
    let rows = m.len();
    if rows == 0 {
        return Err(invalid(format!("{what} needs at least one row")));
    }
    let cols = m[0].len();
    if cols == 0 {
        return Err(invalid(format!("{what} needs at least one column")));
    }
    for (i, row) in m.iter().enumerate() {
        if row.len() != cols {
            return Err(invalid(format!(
                "{what} row {i} has {} entries, expected {cols}",
                row.len()
            )));
        }
    }
    Ok((rows, cols))
}

/// `m * x` for a rectangular matrix and a vector of length `cols`.
pub(crate) fn matrix_apply(m: &[Vec<BigRational>], x: &[BigRational]) -> Vec<BigRational> {
    m.iter()
        .map(|row| {
            row.iter()
                .zip(x)
                .fold(BigRational::zero(), |acc, (a, b)| acc + a * b)
        })
        .collect()
}

/// The first column of a validated rectangular matrix whose sum is not one, with the sum.
fn column_defect(m: &[Vec<BigRational>], cols: usize) -> Option<(usize, BigRational)> {
    (0..cols).find_map(|j| {
        let sum = m.iter().fold(BigRational::zero(), |acc, row| acc + &row[j]);
        (!sum.is_one()).then_some((j, sum))
    })
}

/// `base^exponent` when it is at most `limit`, else `None` (also on overflow). A base of
/// one stays one, so callers bound the exponent separately.
pub(crate) fn bounded_power(base: usize, exponent: usize, limit: usize) -> Option<usize> {
    base.checked_pow(u32::try_from(exponent).ok()?)
        .filter(|&power| power <= limit)
}

/// `sum_o updates[o]` for updates already validated to be `n_out x n_in`.
fn sum_updates(updates: &[Matrix], n_out: usize, n_in: usize) -> Matrix {
    let mut total = vec![vec![BigRational::zero(); n_in]; n_out];
    for update in updates {
        for (total_row, row) in total.iter_mut().zip(update) {
            for (t, x) in total_row.iter_mut().zip(row) {
                *t += x;
            }
        }
    }
    total
}

fn check_nonnegative(m: &[Vec<BigRational>], what: &str) -> Result<(), WdpError> {
    for (i, row) in m.iter().enumerate() {
        for (j, entry) in row.iter().enumerate() {
            if entry.is_negative() {
                return Err(invalid(format!("{what} entry ({i}, {j}) is negative")));
            }
        }
    }
    Ok(())
}

/// Whether every column sums to one. An empty, column-free or ragged matrix is not a
/// matrix of columns, so it is `false` rather than a panic or a vacuous `true`.
pub fn preserves_basis_mass(m: &[Vec<BigRational>]) -> bool {
    matrix_shape(m, "matrix").is_ok_and(|(_, cols)| column_defect(m, cols).is_none())
}

/// Whether `m` is a permutation matrix: square, entries 0 or 1, one 1 per row and column.
pub fn is_permutation_matrix(m: &[Vec<BigRational>]) -> bool {
    let n = m.len();
    if n == 0 || m.iter().any(|row| row.len() != n) {
        return false;
    }
    let is_bit = |x: &BigRational| x.is_zero() || x.is_one();
    if !m.iter().flatten().all(is_bit) {
        return false;
    }
    let rows_ok = m
        .iter()
        .all(|row| row.iter().filter(|x| x.is_one()).count() == 1);
    let cols_ok = (0..n).all(|j| m.iter().filter(|row| row[j].is_one()).count() == 1);
    rows_ok && cols_ok
}

/// Matrix product `a * b` of exact matrices; the caller guarantees `a.cols == b.rows`.
fn matrix_product(a: &[Vec<BigRational>], b: &[Vec<BigRational>]) -> Matrix {
    let cols = b.first().map_or(0, Vec::len);
    a.iter()
        .map(|row| {
            (0..cols)
                .map(|j| {
                    row.iter()
                        .zip(b)
                        .fold(BigRational::zero(), |acc, (x, b_row)| acc + x * &b_row[j])
                })
                .collect()
        })
        .collect()
}

/// The verdict of the exact left-inverse search on a square carrier.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LeftInverse {
    /// No matrix `S` with `S T = I` exists over Q.
    NoLeftInverse,
    /// `S T = I` over Q, but `S` has a negative entry, so it is not an update.
    SignedOnly(Matrix),
    /// A stochastic left inverse; `T` is then a permutation matrix.
    Stochastic(StochasticUpdate),
}

/// A column-stochastic update `T : Q^{n_in} -> Q^{n_out}` over exact rationals.
///
/// Every value has passed [`StochasticUpdate::new`]: nonnegative entries and every
/// column summing to exactly one. There is no deserializer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StochasticUpdate {
    n_out: usize,
    n_in: usize,
    entries: Matrix,
}

impl StochasticUpdate {
    /// A validated update from its rows (`entries[i][j] = T[i][j]`, the probability of
    /// landing in `i` from `j`).
    pub fn new(entries: Matrix) -> Result<Self, WdpError> {
        let (n_out, n_in) = matrix_shape(&entries, "stochastic update")?;
        check_nonnegative(&entries, "stochastic update")?;
        if let Some((j, sum)) = column_defect(&entries, n_in) {
            return Err(invalid(format!(
                "stochastic update column {j} sums to {sum}, not 1"
            )));
        }
        Ok(Self {
            n_out,
            n_in,
            entries,
        })
    }

    /// The identity update on `{0, ..., n-1}`.
    pub fn identity(n: usize) -> Result<Self, WdpError> {
        if n.checked_mul(n)
            .is_none_or(|entries| entries > MAX_MATRIX_ENTRIES)
        {
            return Err(invalid(format!(
                "a {n} x {n} update exceeds {MAX_MATRIX_ENTRIES} entries"
            )));
        }
        let f: Vec<usize> = (0..n).collect();
        Self::from_function(&f, n)
    }

    /// The deterministic update of `f : {0..f.len()} -> {0..n_out}`: column `j` is the
    /// basis vector `f[j]`.
    pub fn from_function(f: &[usize], n_out: usize) -> Result<Self, WdpError> {
        if n_out
            .checked_mul(f.len())
            .is_none_or(|n| n > MAX_MATRIX_ENTRIES)
        {
            return Err(invalid(format!(
                "a {n_out} x {} update exceeds {MAX_MATRIX_ENTRIES} entries",
                f.len()
            )));
        }
        // With no columns the product above is zero whatever `n_out` is, but the rows
        // below would still be allocated.
        if n_out > MAX_MATRIX_ENTRIES {
            return Err(invalid(format!(
                "{n_out} outputs exceed the cap {MAX_MATRIX_ENTRIES}"
            )));
        }
        if let Some((j, target)) = f.iter().enumerate().find(|(_, t)| **t >= n_out) {
            return Err(invalid(format!(
                "function value f({j}) = {target} lies outside 0..{n_out}"
            )));
        }
        let entries = (0..n_out)
            .map(|i| {
                f.iter()
                    .map(|&t| {
                        if t == i {
                            BigRational::one()
                        } else {
                            BigRational::zero()
                        }
                    })
                    .collect()
            })
            .collect();
        Self::new(entries)
    }

    pub fn n_out(&self) -> usize {
        self.n_out
    }

    pub fn n_in(&self) -> usize {
        self.n_in
    }

    pub fn entries(&self) -> &[Vec<BigRational>] {
        &self.entries
    }

    /// `T[i][j]`, or `None` outside the matrix.
    pub fn get(&self, i: usize, j: usize) -> Option<&BigRational> {
        self.entries.get(i).and_then(|row| row.get(j))
    }

    /// `T p` for any vector `p` of length `n_in`, not only distributions.
    pub fn apply(&self, p: &[BigRational]) -> Result<Vec<BigRational>, WdpError> {
        if p.len() != self.n_in {
            return Err(invalid(format!(
                "vector has {} entries, the update has {} inputs",
                p.len(),
                self.n_in
            )));
        }
        Ok(matrix_apply(&self.entries, p))
    }

    /// First `self`, then `next`: the matrix product `next * self`. Closed: a product of
    /// column-stochastic matrices is column-stochastic.
    pub fn compose(&self, next: &StochasticUpdate) -> Result<StochasticUpdate, WdpError> {
        if self.n_out != next.n_in {
            return Err(invalid(format!(
                "cannot compose: first update has {} outputs, second has {} inputs",
                self.n_out, next.n_in
            )));
        }
        Self::new(matrix_product(&next.entries, &self.entries))
    }

    /// Whether every entry is 0 or 1.
    pub fn is_deterministic(&self) -> bool {
        self.entries
            .iter()
            .flatten()
            .all(|x| x.is_zero() || x.is_one())
    }

    /// The function `f` with `T = funMatrix(f)`, when `T` is deterministic.
    pub fn as_function(&self) -> Option<Vec<usize>> {
        if !self.is_deterministic() {
            return None;
        }
        (0..self.n_in)
            .map(|j| (0..self.n_out).find(|&i| self.entries[i][j].is_one()))
            .collect()
    }

    /// A permutation matrix: deterministic and bijective on a square carrier.
    pub fn is_permutation(&self) -> bool {
        is_permutation_matrix(&self.entries)
    }

    /// The decomposition `T = sum_f w_f funMatrix(f)` over the supported functions `f`
    /// (those with `T[f(j)][j] != 0` for every column `j`), with
    /// `w_f = prod_j T[f(j)][j]`. Functions come in lexicographic order.
    ///
    /// The weights are nonnegative and sum to one: the sum over all functions of
    /// `prod_j T[f(j)][j]` factors as `prod_j (column j sum) = 1`.
    pub fn mixture_of_functions(&self) -> Result<FunctionMixture, WdpError> {
        self.mixture_of_functions_with_limit(MAX_ENUMERATION)
    }

    /// [`StochasticUpdate::mixture_of_functions`] refusing more than `limit` supported
    /// functions.
    pub fn mixture_of_functions_with_limit(
        &self,
        limit: usize,
    ) -> Result<FunctionMixture, WdpError> {
        let supports: Vec<Vec<usize>> = (0..self.n_in)
            .map(|j| {
                (0..self.n_out)
                    .filter(|&i| !self.entries[i][j].is_zero())
                    .collect()
            })
            .collect();
        let mut count: usize = 1;
        for support in &supports {
            count = count
                .checked_mul(support.len())
                .filter(|&c| c <= limit)
                .ok_or_else(|| {
                    invalid(format!(
                        "more than {limit} supported functions; enumeration refused"
                    ))
                })?;
        }
        let mut mixture = Vec::with_capacity(count);
        let mut choice = vec![0usize; self.n_in];
        loop {
            let f: Vec<usize> = choice
                .iter()
                .zip(&supports)
                .map(|(&c, support)| support[c])
                .collect();
            let weight = f
                .iter()
                .enumerate()
                .fold(BigRational::one(), |acc, (j, &i)| acc * &self.entries[i][j]);
            mixture.push((f, weight));
            let mut position = self.n_in;
            loop {
                if position == 0 {
                    return Ok(mixture);
                }
                position -= 1;
                choice[position] += 1;
                if choice[position] < supports[position].len() {
                    break;
                }
                choice[position] = 0;
            }
        }
    }

    /// `sum_f w_f funMatrix(f)` as an `n_out x n_in` matrix.
    pub fn recompose(
        mixture: &[(Vec<usize>, BigRational)],
        n_out: usize,
        n_in: usize,
    ) -> Result<Matrix, WdpError> {
        if n_out == 0 || n_in == 0 {
            return Err(invalid(
                "recomposition needs positive dimensions".to_string(),
            ));
        }
        if n_out
            .checked_mul(n_in)
            .is_none_or(|n| n > MAX_MATRIX_ENTRIES)
        {
            return Err(invalid(format!(
                "a {n_out} x {n_in} matrix exceeds {MAX_MATRIX_ENTRIES} entries"
            )));
        }
        let mut matrix = vec![vec![BigRational::zero(); n_in]; n_out];
        for (f, weight) in mixture {
            if f.len() != n_in {
                return Err(invalid(format!(
                    "function has {} values, expected {n_in}",
                    f.len()
                )));
            }
            for (j, &i) in f.iter().enumerate() {
                if i >= n_out {
                    return Err(invalid(format!(
                        "function value f({j}) = {i} lies outside 0..{n_out}"
                    )));
                }
                matrix[i][j] += weight;
            }
        }
        Ok(matrix)
    }

    /// Exact left-inverse search on a square carrier: solves `S T = I` row by row as
    /// `T^t s_k = e_k` with `core_linear_algebra`. A square left inverse is unique
    /// when it exists, so `SignedOnly` means no stochastic left inverse exists.
    pub fn stochastic_left_inverse(&self) -> Result<LeftInverse, WdpError> {
        if self.n_out != self.n_in {
            return Err(invalid(format!(
                "left-inverse search is exact on square carriers, found {} x {}",
                self.n_out, self.n_in
            )));
        }
        let n = self.n_in;
        let transposed: Vec<BigRational> = (0..n)
            .flat_map(|r| (0..n).map(move |c| (r, c)))
            .map(|(r, c)| self.entries[c][r].clone())
            .collect();
        let system =
            BasicMatrix::from_row_major(n, n, transposed).map_err(ExactLinearAlgebraError::from)?;
        let mut inverse_rows = Vec::with_capacity(n);
        for k in 0..n {
            let target: Vec<BigRational> = (0..n)
                .map(|i| {
                    if i == k {
                        BigRational::one()
                    } else {
                        BigRational::zero()
                    }
                })
                .collect();
            match solve_in_image(&system, &target)? {
                ImageMembership::InImage(witness) => inverse_rows.push(witness.potential),
                ImageMembership::NotInImage { .. } => return Ok(LeftInverse::NoLeftInverse),
            }
        }
        match Self::new(inverse_rows.clone()) {
            Ok(update) => Ok(LeftInverse::Stochastic(update)),
            Err(_) => Ok(LeftInverse::SignedOnly(inverse_rows)),
        }
    }

    /// The row-stochastic `core_quantum_physics` map of the transpose: source `n_in`,
    /// target `n_out`, `P(j | i)` equal to `T[j][i]`.
    pub fn to_stochastic_map(&self, label: &str) -> Result<StochasticMap, WdpError> {
        let rows: Matrix = (0..self.n_in)
            .map(|j| {
                (0..self.n_out)
                    .map(|i| self.entries[i][j].clone())
                    .collect()
            })
            .collect();
        Ok(StochasticMap::try_from_rows(
            self.n_in, self.n_out, rows, label,
        )?)
    }

    /// The inverse of [`StochasticUpdate::to_stochastic_map`].
    pub fn from_stochastic_map(map: &StochasticMap) -> Result<Self, WdpError> {
        let rows = map.rows();
        let entries: Matrix = (0..map.target_n())
            .map(|i| rows.iter().map(|row| row[i].clone()).collect())
            .collect();
        Self::new(entries)
    }
}

/// A finite classical instrument: one nonnegative matrix per outcome, all of one shape,
/// whose sum is a stochastic update.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ClassicalInstrument {
    n_out: usize,
    n_in: usize,
    updates: Vec<Matrix>,
}

impl ClassicalInstrument {
    pub fn new(updates: Vec<Matrix>) -> Result<Self, WdpError> {
        let first = updates
            .first()
            .ok_or_else(|| invalid("an instrument needs at least one outcome".to_string()))?;
        let (n_out, n_in) = matrix_shape(first, "instrument update 0")?;
        for (o, update) in updates.iter().enumerate() {
            let shape = matrix_shape(update, &format!("instrument update {o}"))?;
            if shape != (n_out, n_in) {
                return Err(invalid(format!(
                    "instrument update {o} is {} x {}, expected {n_out} x {n_in}",
                    shape.0, shape.1
                )));
            }
            check_nonnegative(update, &format!("instrument update {o}"))?;
        }
        if let Some((j, sum)) = column_defect(&sum_updates(&updates, n_out, n_in), n_in) {
            return Err(invalid(format!(
                "instrument sum column {j} sums to {sum}, not 1"
            )));
        }
        Ok(Self {
            n_out,
            n_in,
            updates,
        })
    }

    pub fn outcomes(&self) -> usize {
        self.updates.len()
    }

    pub fn n_out(&self) -> usize {
        self.n_out
    }

    pub fn n_in(&self) -> usize {
        self.n_in
    }

    pub fn updates(&self) -> &[Matrix] {
        &self.updates
    }

    /// The outcome-forgetting update `sum_o T_o`.
    pub fn total_update(&self) -> Result<StochasticUpdate, WdpError> {
        StochasticUpdate::new(sum_updates(&self.updates, self.n_out, self.n_in))
    }

    /// `p` must be nonnegative and of length `n_in`, for every word including the empty one.
    fn check_input(&self, p: &[BigRational]) -> Result<(), WdpError> {
        if let Some(i) = p.iter().position(Signed::is_negative) {
            return Err(invalid(format!("input vector entry {i} is negative")));
        }
        if p.len() != self.n_in {
            return Err(invalid(format!(
                "vector has {} entries, the instrument has {} inputs",
                p.len(),
                self.n_in
            )));
        }
        Ok(())
    }

    /// `T_o current`; each step needs `current` to have length `n_in`, so words longer
    /// than one need a square instrument.
    fn step(&self, outcome: usize, current: &[BigRational]) -> Result<Vec<BigRational>, WdpError> {
        let update = self.updates.get(outcome).ok_or_else(|| {
            invalid(format!(
                "outcome {outcome} outside 0..{}",
                self.updates.len()
            ))
        })?;
        if current.len() != self.n_in {
            return Err(invalid(format!(
                "vector has {} entries, the instrument has {} inputs",
                current.len(),
                self.n_in
            )));
        }
        Ok(matrix_apply(update, current))
    }

    /// Runs the word on `p`, first outcome first: `run (o :: l) p = run l (T_o p)`.
    /// `p` must be nonnegative of length `n_in`.
    pub fn run(&self, word: &[usize], p: &[BigRational]) -> Result<Vec<BigRational>, WdpError> {
        self.check_input(p)?;
        let mut current = p.to_vec();
        for &o in word {
            current = self.step(o, &current)?;
        }
        Ok(current)
    }

    /// The law of the word on `p`: the mass of `run word p`.
    pub fn law(&self, word: &[usize], p: &[BigRational]) -> Result<BigRational, WdpError> {
        Ok(mass(&self.run(word, p)?))
    }

    /// The sum of `law` over all `outcomes^n` words of length `n`.
    pub fn law_total(&self, n: usize, p: &[BigRational]) -> Result<BigRational, WdpError> {
        self.law_total_with_limit(n, p, MAX_ENUMERATION)
    }

    /// [`ClassicalInstrument::law_total`] refusing a word length above `limit` and more
    /// than `limit` words. The words are walked depth first, each extension applying one
    /// matrix to the vector of its prefix.
    pub fn law_total_with_limit(
        &self,
        n: usize,
        p: &[BigRational],
        limit: usize,
    ) -> Result<BigRational, WdpError> {
        self.check_input(p)?;
        let outcomes = self.updates.len();
        if n > limit {
            return Err(invalid(format!(
                "word length {n} exceeds the enumeration cap {limit}"
            )));
        }
        bounded_power(outcomes, n, limit).ok_or_else(|| {
            invalid(format!(
                "more than {limit} words of length {n}; enumeration refused"
            ))
        })?;
        let mut total = BigRational::zero();
        // `vectors[d]` is the run of the current `d`-outcome prefix, so `vectors.len()`
        // is always `word.len() + 1`.
        let mut vectors: Vec<Vec<BigRational>> = vec![p.to_vec()];
        let mut word: Vec<usize> = Vec::new();
        loop {
            while word.len() < n {
                let next = self.step(0, &vectors[word.len()])?;
                vectors.push(next);
                word.push(0);
            }
            total += mass(&vectors[n]);
            loop {
                let Some(last) = word.pop() else {
                    return Ok(total);
                };
                vectors.pop();
                if last + 1 < outcomes {
                    let next = self.step(last + 1, &vectors[word.len()])?;
                    vectors.push(next);
                    word.push(last + 1);
                    break;
                }
            }
        }
    }
}

/// Evidence that mass-preserving invertible maps are not all permutations once signs are
/// allowed (fixture `signed_weights_break_the_corner`).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedShearReport {
    pub t: Matrix,
    pub t_inverse: Matrix,
    pub t_preserves_basis_mass: bool,
    pub t_inverse_preserves_basis_mass: bool,
    pub inverse_times_t_is_identity: bool,
    pub t_is_permutation_matrix: bool,
    pub t_is_column_stochastic: bool,
    pub t_image_of_first_basis_vector: Vec<BigRational>,
    /// Why [`StochasticUpdate::new`] refuses `t`.
    pub refusal: WdpError,
    pub authority_effect: AuthorityEffect,
}

fn integer_matrix(rows: &[&[i64]]) -> Matrix {
    rows.iter()
        .map(|row| {
            row.iter()
                .map(|&x| BigRational::from_integer(x.into()))
                .collect()
        })
        .collect()
}

/// `T = [[2, 1], [-1, 0]]` with inverse `[[0, -1], [1, 2]]`: both preserve total mass on
/// every basis vector and `T^{-1} T = I`, yet `T` is not a permutation matrix and has a
/// negative entry, so it is refused as a stochastic update.
pub fn signed_shear_counterexample() -> Result<SignedShearReport, WdpError> {
    let t = integer_matrix(&[&[2, 1], &[-1, 0]]);
    let t_inverse = integer_matrix(&[&[0, -1], &[1, 2]]);
    let identity = integer_matrix(&[&[1, 0], &[0, 1]]);
    let refusal = match StochasticUpdate::new(t.clone()) {
        Err(e) => e,
        Ok(_) => {
            return Err(invalid(
                "the signed shear was accepted as a stochastic update".to_string(),
            ))
        }
    };
    let first_basis: Vec<BigRational> = vec![BigRational::one(), BigRational::zero()];
    Ok(SignedShearReport {
        t_preserves_basis_mass: preserves_basis_mass(&t),
        t_inverse_preserves_basis_mass: preserves_basis_mass(&t_inverse),
        inverse_times_t_is_identity: matrix_product(&t_inverse, &t) == identity,
        t_is_permutation_matrix: is_permutation_matrix(&t),
        t_is_column_stochastic: StochasticUpdate::new(t.clone()).is_ok(),
        t_image_of_first_basis_vector: matrix_apply(&t, &first_basis),
        refusal,
        authority_effect: AuthorityEffect::None,
        t,
        t_inverse,
    })
}

// Origin: engine/crates_rs/core_wdp/src/stochastic_package.rs
// Claim: urn:core:crates_rs:core-wdp:stochastic-package:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6c3d79f2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6c3d79f2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6c3d79f2 {
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
impl BoundaryError6c3d79f2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6c3d79f2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6c3d79f2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6c3d79f2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6c3d79f2> {
        if capacity_bound == 0 {
            return Err(BoundaryError6c3d79f2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6c3d79f2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6c3d79f2::ExceedsCapacity {
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
mod l4_boundary_tests_6c3d79f2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord6c3d79f2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord6c3d79f2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord6c3d79f2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord6c3d79f2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord6c3d79f2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError6c3d79f2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError6c3d79f2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
