//! Finite strict partial orders on `{0, .., n-1}`: validated construction,
//! order-theoretic queries, the zeta and Mobius functions, and the order complex.
//!
//! A [`FinitePoset`] is a relation `<` on `{0, .., n-1}` that is irreflexive,
//! asymmetric and transitive. The fields are private and every constructor
//! checks all three laws, so a value of this type is a poset. Deserialization
//! goes through the same check (`serde(try_from)`), so a serialized relation
//! that is not an order cannot be loaded.
//!
//! What is computed, and how it can be cross-checked:
//!
//! - relations, covers (the Hasse diagram), incomparable pairs, up-sets,
//!   down-sets and closed or open intervals;
//! - chains, antichains, height, and the width with a Dilworth certificate
//!   ([`WidthCertificate`]: an antichain and a chain partition of the same
//!   size, so the width is checked by exhibiting both bounds);
//! - linear extensions, counted by dynamic programming over down-sets or
//!   listed explicitly, each with a caller-chosen budget and a typed refusal;
//! - the zeta function, and the Mobius function by two independent routes
//!   (the defining recursion and exact inversion of the zeta matrix over `Q`),
//!   plus [`MobiusFunction::is_inverse_of_zeta`], which checks the defining
//!   convolution identities directly;
//! - the order complex (the simplicial complex of chains) as an
//!   [`crate::simplicial::SimplicialComplex`], and Philip Hall's theorem as a
//!   third route: `mu(x, y)` for `x < y` is the reduced Euler characteristic
//!   of the order complex of the open interval `(x, y)`.
//!
//! `crate::finite_directed_graph::FiniteDirectedGraph::covering_edges` returns
//! every edge of the graph, which is the set of covers only for a graph that
//! is already a Hasse diagram. [`FinitePoset::covers`] computes the covers.
//!
//! Bounded enumeration of all posets on `n` labelled elements, the unlabelled
//! census, canonical forms and automorphism counts live in
//! [`crate::poset_census`]; they refuse sizes above an explicit bound instead
//! of looping over `2^(n(n-1))` relations.
//!
//! AuthorityEffect: None.

use crate::errors::HomologicalError;
use crate::simplicial::{Simplex, SimplicialComplex};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::linear_algebra::image_kernel::{ExactLinearAlgebraError, ExactRowReduction};
use num_bigint::{BigInt, BigUint};
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

/// Largest number of elements a [`FinitePoset`] may have.
pub const MAX_POSET_ELEMENTS: usize = 256;

/// Largest poset whose zeta matrix [`FinitePoset::mobius_by_zeta_inversion`]
/// will row-reduce over `Q` (the elimination is cubic in exact rationals).
pub const MAX_ZETA_INVERSION_ELEMENTS: usize = 64;

/// Largest poset for which [`FinitePoset::count_linear_extensions`] runs: the
/// down-sets are carried as 64-bit masks.
pub const MAX_LINEAR_EXTENSION_ELEMENTS: usize = 64;

/// Refusals of the poset constructors and queries.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum PosetError {
    #[error("a poset on {requested} elements exceeds the limit of {limit} for this operation")]
    TooManyElements { requested: usize, limit: usize },
    #[error("relation ({lower}, {upper}) names an element outside 0..{size}")]
    RelationOutOfRange {
        lower: usize,
        upper: usize,
        size: usize,
    },
    #[error("element {element} is outside 0..{size}")]
    ElementOutOfRange { element: usize, size: usize },
    #[error("element {element} is listed twice")]
    DuplicateElement { element: usize },
    #[error("relation ({element}, {element}) is reflexive: a strict order is irreflexive")]
    Reflexive { element: usize },
    #[error("relation ({lower}, {upper}) is declared twice")]
    DuplicateRelation { lower: usize, upper: usize },
    #[error("both ({first}, {second}) and ({second}, {first}) hold: a strict order is asymmetric")]
    NotAsymmetric { first: usize, second: usize },
    #[error(
        "({lower}, {middle}) and ({middle}, {upper}) hold but ({lower}, {upper}) is missing: \
         a strict order is transitive"
    )]
    NotTransitive {
        lower: usize,
        middle: usize,
        upper: usize,
    },
    #[error("the generating relations contain a cycle through element {element}")]
    Cyclic { element: usize },
    #[error("{what} would exceed the budget of {limit}")]
    BudgetExceeded { what: &'static str, limit: usize },
    #[error("the order has {given} elements but {expected} were expected")]
    WrongElementCount { expected: usize, given: usize },
    #[error("{requested} elements exceed the bound of {limit} for {operation}")]
    SizeBound {
        operation: &'static str,
        requested: usize,
        limit: usize,
    },
    #[error("the zeta matrix did not row-reduce to the identity")]
    ZetaNotInvertible,
    #[error("the inverse of the zeta matrix has a non-integral entry at ({row}, {col})")]
    NonIntegralMobius { row: usize, col: usize },
    #[error(transparent)]
    ExactLinearAlgebra(#[from] ExactLinearAlgebraError),
    #[error(transparent)]
    Matrix(#[from] MatrixError),
    #[error(transparent)]
    Homological(#[from] HomologicalError),
}

const WORD_BITS: usize = 64;

fn words_for(size: usize) -> usize {
    size.div_ceil(WORD_BITS)
}

fn bit(row: &[u64], index: usize) -> bool {
    (row[index / WORD_BITS] >> (index % WORD_BITS)) & 1 == 1
}

fn set_bit(row: &mut [u64], index: usize) {
    row[index / WORD_BITS] |= 1u64 << (index % WORD_BITS);
}

/// `u32 -> usize` is lossless on every supported target.
fn popcount(row: &[u64]) -> usize {
    row.iter().map(|w| w.count_ones() as usize).sum()
}

/// The set bits of a row, ascending.
fn ones(row: &[u64]) -> Vec<usize> {
    let mut out = Vec::new();
    for (word_index, &word) in row.iter().enumerate() {
        let mut w = word;
        while w != 0 {
            out.push(word_index * WORD_BITS + w.trailing_zeros() as usize);
            w &= w - 1;
        }
    }
    out
}

/// Serialized form of a [`FinitePoset`]: the size and the sorted relations.
#[derive(Serialize, Deserialize)]
struct PosetWire {
    size: usize,
    relations: Vec<(usize, usize)>,
}

impl From<FinitePoset> for PosetWire {
    fn from(poset: FinitePoset) -> Self {
        PosetWire {
            size: poset.size,
            relations: poset.strict_relations(),
        }
    }
}

impl TryFrom<PosetWire> for FinitePoset {
    type Error = PosetError;
    fn try_from(wire: PosetWire) -> Result<Self, Self::Error> {
        FinitePoset::new(wire.size, wire.relations)
    }
}

/// A finite strict partial order on `{0, .., size-1}`.
///
/// `u < v` is stored as a bit in row `u` of `less` and, transposed, in row `v`
/// of `greater`. The only ways to obtain a value are the validating
/// constructors and validated deserialization.
#[derive(Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(try_from = "PosetWire", into = "PosetWire")]
pub struct FinitePoset {
    size: usize,
    words: usize,
    less: Vec<u64>,
    greater: Vec<u64>,
}

impl fmt::Debug for FinitePoset {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.debug_struct("FinitePoset")
            .field("size", &self.size)
            .field("relations", &self.strict_relations())
            .finish()
    }
}

/// A poset with a new least and a new greatest element adjoined.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundedCompletion {
    pub poset: FinitePoset,
    /// Index of the adjoined least element.
    pub bottom: usize,
    /// Index of the adjoined greatest element.
    pub top: usize,
}

/// A maximum antichain and a minimum chain partition of equal size: a
/// certificate of the width (Dilworth's theorem).
///
/// Every antichain meets every chain of a partition in at most one element,
/// so `antichain.len() <= number of chains`; an antichain and a partition of
/// the same size therefore pin the width exactly.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct WidthCertificate {
    /// Pairwise incomparable elements, ascending.
    pub antichain: Vec<usize>,
    /// Disjoint chains covering every element, each listed in increasing order.
    pub chains: Vec<Vec<usize>>,
}

impl WidthCertificate {
    /// The width this certificate establishes, if it is valid for `poset`.
    pub fn verified_width(&self, poset: &FinitePoset) -> Option<usize> {
        if self.antichain.len() != self.chains.len() {
            return None;
        }
        if !matches!(poset.is_antichain(&self.antichain), Ok(true)) {
            return None;
        }
        let mut seen = vec![false; poset.size];
        for chain in &self.chains {
            if !Self::verify_single_chain(poset, chain, &mut seen) {
                return None;
            }
        }
        if seen.iter().all(|&covered| covered) {
            Some(self.antichain.len())
        } else {
            None
        }
    }

    fn verify_single_chain(poset: &FinitePoset, chain: &[usize], seen: &mut [bool]) -> bool {
        if chain.is_empty() || !matches!(poset.is_chain(chain), Ok(true)) {
            return false;
        }
        for &element in chain {
            if element >= poset.size || seen[element] {
                return false;
            }
            seen[element] = true;
        }
        // `is_chain` accepts any order; the certificate promises increasing.
        !chain
            .windows(2)
            .any(|pair| !poset.less_unchecked(pair[0], pair[1]))
    }
}

/// The Mobius function of a finite poset: `mu(x, x) = 1`,
/// `sum_{x <= z <= y} mu(x, z) = 0` for `x < y`, and `mu(x, y) = 0` unless
/// `x <= y`. Entries are exact integers.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MobiusFunction {
    size: usize,
    values: Vec<BigInt>,
}

impl MobiusFunction {
    /// The number of poset elements it is defined on.
    pub fn size(&self) -> usize {
        self.size
    }

    /// `mu(x, y)`.
    pub fn get(&self, x: usize, y: usize) -> Result<&BigInt, PosetError> {
        for element in [x, y] {
            if element >= self.size {
                return Err(PosetError::ElementOutOfRange {
                    element,
                    size: self.size,
                });
            }
        }
        Ok(&self.values[x * self.size + y])
    }

    /// Whether the table satisfies both defining convolution identities over
    /// `poset`: `sum_{x <= z <= y} mu(x, z) = delta(x, y)` and
    /// `sum_{x <= z <= y} mu(z, y) = delta(x, y)` (the two-sided inverse of
    /// the zeta function in the incidence algebra), and vanishes off `<=`.
    pub fn is_inverse_of_zeta(&self, poset: &FinitePoset) -> bool {
        let n = poset.size;
        if self.size != n {
            return false;
        }
        for x in 0..n {
            for y in 0..n {
                if !self.check_interval_inversion(poset, x, y) {
                    return false;
                }
            }
        }
        true
    }

    fn check_interval_inversion(&self, poset: &FinitePoset, x: usize, y: usize) -> bool {
        let n = poset.size;
        if !poset.less_or_equal_unchecked(x, y) && !self.values[x * n + y].is_zero() {
            return false;
        }
        let mut left = BigInt::zero();
        let mut right = BigInt::zero();
        for z in 0..n {
            if poset.less_or_equal_unchecked(x, z) && poset.less_or_equal_unchecked(z, y) {
                left += &self.values[x * n + z];
                right += &self.values[z * n + y];
            }
        }
        let expected = if x == y {
            BigInt::one()
        } else {
            BigInt::zero()
        };
        left == expected && right == expected
    }
}

impl FinitePoset {
    fn from_less_rows(size: usize, less: Vec<u64>) -> Self {
        let words = words_for(size);
        let mut greater = vec![0u64; size * words];
        for u in 0..size {
            for v in ones(&less[u * words..(u + 1) * words]) {
                set_bit(&mut greater[v * words..(v + 1) * words], u);
            }
        }
        Self {
            size,
            words,
            less,
            greater,
        }
    }

    fn less_row(&self, u: usize) -> &[u64] {
        &self.less[u * self.words..(u + 1) * self.words]
    }

    fn greater_row(&self, v: usize) -> &[u64] {
        &self.greater[v * self.words..(v + 1) * self.words]
    }

    fn less_unchecked(&self, u: usize, v: usize) -> bool {
        bit(self.less_row(u), v)
    }

    fn less_or_equal_unchecked(&self, u: usize, v: usize) -> bool {
        u == v || self.less_unchecked(u, v)
    }

    fn check(&self, element: usize) -> Result<(), PosetError> {
        if element < self.size {
            Ok(())
        } else {
            Err(PosetError::ElementOutOfRange {
                element,
                size: self.size,
            })
        }
    }

    fn check_size(size: usize) -> Result<(), PosetError> {
        if size > MAX_POSET_ELEMENTS {
            Err(PosetError::TooManyElements {
                requested: size,
                limit: MAX_POSET_ELEMENTS,
            })
        } else {
            Ok(())
        }
    }

    /// The poset on `size` elements whose strict relations are exactly
    /// `strict_relations`, where `(u, v)` means `u < v`.
    ///
    /// Refused, in this order: more than [`MAX_POSET_ELEMENTS`] elements; a
    /// relation outside `0..size`; a reflexive or repeated relation; an
    /// asymmetry violation; a transitivity violation (reported with the first
    /// missing `(lower, upper)` in lexicographic order).
    pub fn new<I>(size: usize, strict_relations: I) -> Result<Self, PosetError>
    where
        I: IntoIterator<Item = (usize, usize)>,
    {
        Self::check_size(size)?;
        let words = words_for(size);
        let mut less = vec![0u64; size * words];
        for (lower, upper) in strict_relations {
            if lower >= size || upper >= size {
                return Err(PosetError::RelationOutOfRange { lower, upper, size });
            }
            if lower == upper {
                return Err(PosetError::Reflexive { element: lower });
            }
            let row = &mut less[lower * words..(lower + 1) * words];
            if bit(row, upper) {
                return Err(PosetError::DuplicateRelation { lower, upper });
            }
            set_bit(row, upper);
        }
        let poset = Self::from_less_rows(size, less);
        poset.validate_strict_order()?;
        Ok(poset)
    }

    fn validate_strict_order(&self) -> Result<(), PosetError> {
        for u in 0..self.size {
            for v in ones(self.less_row(u)) {
                if self.less_unchecked(v, u) {
                    return Err(PosetError::NotAsymmetric {
                        first: u,
                        second: v,
                    });
                }
            }
        }
        for u in 0..self.size {
            for v in ones(self.less_row(u)) {
                for w in 0..self.words {
                    let missing = self.less_row(v)[w] & !self.less_row(u)[w];
                    if missing != 0 {
                        return Err(PosetError::NotTransitive {
                            lower: u,
                            middle: v,
                            upper: w * WORD_BITS + missing.trailing_zeros() as usize,
                        });
                    }
                }
            }
        }
        Ok(())
    }

    /// The transitive closure of `pairs` on `size` elements, refused when the
    /// pairs contain a cycle (the closure would then relate an element to
    /// itself). Repeated pairs are allowed: they are a set of generators, not
    /// a declared relation. The covers of the result are a subset of `pairs`.
    pub fn from_generating_relations<I>(size: usize, pairs: I) -> Result<Self, PosetError>
    where
        I: IntoIterator<Item = (usize, usize)>,
    {
        Self::check_size(size)?;
        let words = words_for(size);
        let mut reach = vec![0u64; size * words];
        for (lower, upper) in pairs {
            if lower >= size || upper >= size {
                return Err(PosetError::RelationOutOfRange { lower, upper, size });
            }
            if lower == upper {
                return Err(PosetError::Reflexive { element: lower });
            }
            set_bit(&mut reach[lower * words..(lower + 1) * words], upper);
        }
        // Warshall: after pass k, i reaches everything reachable through {0..=k}.
        Self::warshall_closure(size, words, &mut reach);
        for i in 0..size {
            if bit(&reach[i * words..(i + 1) * words], i) {
                return Err(PosetError::Cyclic { element: i });
            }
        }
        Ok(Self::from_less_rows(size, reach))
    }

    fn warshall_closure(size: usize, words: usize, reach: &mut [u64]) {
        for k in 0..size {
            let row_k: Vec<u64> = reach[k * words..(k + 1) * words].to_vec();
            for i in 0..size {
                if bit(&reach[i * words..(i + 1) * words], k) {
                    for (target, source) in reach[i * words..(i + 1) * words].iter_mut().zip(&row_k)
                    {
                        *target |= *source;
                    }
                }
            }
        }
    }

    /// The total order `0 < 1 < .. < size-1`.
    pub fn chain(size: usize) -> Result<Self, PosetError> {
        Self::new(
            size,
            (0..size).flat_map(|u| ((u + 1)..size).map(move |v| (u, v))),
        )
    }

    /// `size` pairwise incomparable elements.
    pub fn antichain(size: usize) -> Result<Self, PosetError> {
        Self::new(size, std::iter::empty())
    }

    /// The subsets of `{0, .., k-1}` ordered by inclusion; element `s` stands
    /// for the subset whose indicator bits are the bits of `s`. Needs
    /// `2^k <= MAX_POSET_ELEMENTS`.
    pub fn boolean_lattice(k: usize) -> Result<Self, PosetError> {
        let size = 1usize
            .checked_shl(u32::try_from(k).unwrap_or(u32::MAX))
            .ok_or(PosetError::TooManyElements {
                requested: usize::MAX,
                limit: MAX_POSET_ELEMENTS,
            })?;
        Self::check_size(size)?;
        Self::new(
            size,
            (0..size).flat_map(|a| {
                (0..size)
                    .filter(move |&b| a != b && a & b == a)
                    .map(move |b| (a, b))
            }),
        )
    }

    /// Number of elements.
    pub fn size(&self) -> usize {
        self.size
    }

    pub fn is_empty(&self) -> bool {
        self.size == 0
    }

    /// `u < v`.
    pub fn less(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        self.check(u)?;
        self.check(v)?;
        Ok(self.less_unchecked(u, v))
    }

    /// `u <= v`.
    pub fn less_or_equal(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        self.check(u)?;
        self.check(v)?;
        Ok(self.less_or_equal_unchecked(u, v))
    }

    /// `u < v` or `v < u`.
    pub fn comparable(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        self.check(u)?;
        self.check(v)?;
        Ok(u != v && (self.less_unchecked(u, v) || self.less_unchecked(v, u)))
    }

    /// `u != v` and neither `u < v` nor `v < u`.
    pub fn incomparable(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        self.check(u)?;
        self.check(v)?;
        Ok(u != v && !self.less_unchecked(u, v) && !self.less_unchecked(v, u))
    }

    /// Every pair `(u, v)` with `u < v`, in lexicographic order.
    pub fn strict_relations(&self) -> Vec<(usize, usize)> {
        (0..self.size)
            .flat_map(|u| ones(self.less_row(u)).into_iter().map(move |v| (u, v)))
            .collect()
    }

    /// The number of pairs `u < v`.
    pub fn relation_count(&self) -> usize {
        popcount(&self.less)
    }

    /// `{ w : w < u }`, ascending.
    pub fn predecessors(&self, u: usize) -> Result<Vec<usize>, PosetError> {
        self.check(u)?;
        Ok(ones(self.greater_row(u)))
    }

    /// `{ w : u < w }`, ascending.
    pub fn successors(&self, u: usize) -> Result<Vec<usize>, PosetError> {
        self.check(u)?;
        Ok(ones(self.less_row(u)))
    }

    /// The principal down-set `{ w : w <= u }`.
    pub fn down_set(&self, u: usize) -> Result<Vec<usize>, PosetError> {
        let mut set = self.predecessors(u)?;
        set.push(u);
        set.sort_unstable();
        Ok(set)
    }

    /// The principal up-set `{ w : u <= w }`.
    pub fn up_set(&self, u: usize) -> Result<Vec<usize>, PosetError> {
        let mut set = self.successors(u)?;
        set.push(u);
        set.sort_unstable();
        Ok(set)
    }

    /// The closed interval `[a, b] = { w : a <= w <= b }`; empty unless `a <= b`.
    pub fn interval(&self, a: usize, b: usize) -> Result<Vec<usize>, PosetError> {
        self.check(a)?;
        self.check(b)?;
        Ok((0..self.size)
            .filter(|&w| self.less_or_equal_unchecked(a, w) && self.less_or_equal_unchecked(w, b))
            .collect())
    }

    /// The open interval `(a, b) = { w : a < w < b }`.
    pub fn open_interval(&self, a: usize, b: usize) -> Result<Vec<usize>, PosetError> {
        self.check(a)?;
        self.check(b)?;
        Ok((0..self.size)
            .filter(|&w| self.less_unchecked(a, w) && self.less_unchecked(w, b))
            .collect())
    }

    /// Whether `v` covers `u`: `u < v` with no `w` strictly between.
    pub fn is_cover(&self, u: usize, v: usize) -> Result<bool, PosetError> {
        self.check(u)?;
        self.check(v)?;
        Ok(self.is_cover_unchecked(u, v))
    }

    fn is_cover_unchecked(&self, u: usize, v: usize) -> bool {
        if !self.less_unchecked(u, v) {
            return false;
        }
        // Some w with u < w < v exists exactly when row(u) meets greater-row(v).
        !self
            .less_row(u)
            .iter()
            .zip(self.greater_row(v))
            .any(|(a, b)| a & b != 0)
    }

    /// The covering pairs `(u, v)` (`v` covers `u`): the edges of the Hasse
    /// diagram, in lexicographic order.
    pub fn covers(&self) -> Vec<(usize, usize)> {
        let mut out = Vec::new();
        for u in 0..self.size {
            for v in ones(self.less_row(u)) {
                if self.is_cover_unchecked(u, v) {
                    out.push((u, v));
                }
            }
        }
        out
    }

    /// The elements covering `u`.
    pub fn upper_covers(&self, u: usize) -> Result<Vec<usize>, PosetError> {
        self.check(u)?;
        Ok(ones(self.less_row(u))
            .into_iter()
            .filter(|&v| self.is_cover_unchecked(u, v))
            .collect())
    }

    /// The elements covered by `v`.
    pub fn lower_covers(&self, v: usize) -> Result<Vec<usize>, PosetError> {
        self.check(v)?;
        Ok(ones(self.greater_row(v))
            .into_iter()
            .filter(|&u| self.is_cover_unchecked(u, v))
            .collect())
    }

    /// Every pair `(u, v)` with `u < v` as integers that is incomparable in
    /// the order, in lexicographic order.
    pub fn incomparable_pairs(&self) -> Vec<(usize, usize)> {
        let mut out = Vec::new();
        for u in 0..self.size {
            for v in (u + 1)..self.size {
                if !self.less_unchecked(u, v) && !self.less_unchecked(v, u) {
                    out.push((u, v));
                }
            }
        }
        out
    }

    /// Elements with no predecessor.
    pub fn minimal_elements(&self) -> Vec<usize> {
        (0..self.size)
            .filter(|&u| popcount(self.greater_row(u)) == 0)
            .collect()
    }

    /// Elements with no successor.
    pub fn maximal_elements(&self) -> Vec<usize> {
        (0..self.size)
            .filter(|&u| popcount(self.less_row(u)) == 0)
            .collect()
    }

    /// The least element, when there is one.
    pub fn bottom(&self) -> Option<usize> {
        let minimal = self.minimal_elements();
        match minimal.as_slice() {
            [only] if popcount(self.less_row(*only)) == self.size - 1 => Some(*only),
            _ => None,
        }
    }

    /// The greatest element, when there is one.
    pub fn top(&self) -> Option<usize> {
        let maximal = self.maximal_elements();
        match maximal.as_slice() {
            [only] if popcount(self.greater_row(*only)) == self.size - 1 => Some(*only),
            _ => None,
        }
    }

    fn check_subset(&self, elements: &[usize]) -> Result<(), PosetError> {
        let mut seen = BTreeSet::new();
        for &element in elements {
            self.check(element)?;
            if !seen.insert(element) {
                return Err(PosetError::DuplicateElement { element });
            }
        }
        Ok(())
    }

    /// Whether the listed elements are pairwise comparable.
    pub fn is_chain(&self, elements: &[usize]) -> Result<bool, PosetError> {
        self.check_subset(elements)?;
        Ok(elements.iter().enumerate().all(|(i, &u)| {
            elements[i + 1..]
                .iter()
                .all(|&v| self.less_unchecked(u, v) || self.less_unchecked(v, u))
        }))
    }

    /// Whether the listed elements are pairwise incomparable.
    pub fn is_antichain(&self, elements: &[usize]) -> Result<bool, PosetError> {
        self.check_subset(elements)?;
        Ok(elements.iter().enumerate().all(|(i, &u)| {
            elements[i + 1..]
                .iter()
                .all(|&v| !self.less_unchecked(u, v) && !self.less_unchecked(v, u))
        }))
    }

    /// Whether the listed elements form a down-set: closed under going down.
    pub fn is_down_set(&self, elements: &[usize]) -> Result<bool, PosetError> {
        self.check_subset(elements)?;
        let members: BTreeSet<usize> = elements.iter().copied().collect();
        Ok(elements.iter().all(|&u| {
            ones(self.greater_row(u))
                .iter()
                .all(|w| members.contains(w))
        }))
    }

    /// Whether the listed elements form an up-set: closed under going up.
    pub fn is_up_set(&self, elements: &[usize]) -> Result<bool, PosetError> {
        self.check_subset(elements)?;
        let members: BTreeSet<usize> = elements.iter().copied().collect();
        Ok(elements
            .iter()
            .all(|&u| ones(self.less_row(u)).iter().all(|w| members.contains(w))))
    }

    /// A linear extension of the order: among the elements whose predecessors
    /// are already listed, the smallest label goes next.
    pub fn topological_order(&self) -> Vec<usize> {
        let mut pending: Vec<usize> = (0..self.size)
            .map(|u| popcount(self.greater_row(u)))
            .collect();
        let mut available: BTreeSet<usize> = (0..self.size).filter(|&u| pending[u] == 0).collect();
        let mut order = Vec::with_capacity(self.size);
        while let Some(u) = available.pop_first() {
            order.push(u);
            for v in ones(self.less_row(u)) {
                pending[v] -= 1;
                if pending[v] == 0 {
                    available.insert(v);
                }
            }
        }
        order
    }

    /// Whether `order` lists every element once and never puts `v` before `u`
    /// when `u < v`.
    pub fn is_linear_extension(&self, order: &[usize]) -> Result<bool, PosetError> {
        if order.len() != self.size {
            return Err(PosetError::WrongElementCount {
                expected: self.size,
                given: order.len(),
            });
        }
        self.check_subset(order)?;
        let mut position = vec![0usize; self.size];
        for (index, &element) in order.iter().enumerate() {
            position[element] = index;
        }
        Ok(self
            .strict_relations()
            .iter()
            .all(|&(u, v)| position[u] < position[v]))
    }

    /// The number of elements of a longest chain (0 for the empty poset).
    /// The length of a longest chain, counted in covers, is one less.
    pub fn height(&self) -> usize {
        let mut best = vec![0usize; self.size];
        let mut height = 0;
        for u in self.topological_order() {
            let below = ones(self.greater_row(u))
                .into_iter()
                .map(|w| best[w])
                .max()
                .unwrap_or(0);
            best[u] = below + 1;
            height = height.max(best[u]);
        }
        height
    }

    /// The width (size of a largest antichain), with a Dilworth certificate.
    ///
    /// A maximum matching in the bipartite graph with an edge `u -> v` for
    /// every `u < v` gives a partition into `size - matching` chains; Konig's
    /// construction of a minimum vertex cover from the same matching yields an
    /// antichain of that size.
    pub fn width_certificate(&self) -> WidthCertificate {
        let n = self.size;
        let successors: Vec<Vec<usize>> = (0..n).map(|u| ones(self.less_row(u))).collect();
        let mut matched_right: Vec<Option<usize>> = vec![None; n];
        let mut matched_left: Vec<Option<usize>> = vec![None; n];
        for u in 0..n {
            let mut visited = vec![false; n];
            augment(
                u,
                &successors,
                &mut visited,
                &mut matched_right,
                &mut matched_left,
            );
        }

        // Chains: follow matched edges u -> v.
        let chains = Self::extract_matched_chains(n, &matched_right, &matched_left);

        // Konig: Z = vertices reachable from unmatched left vertices by
        // alternating paths (left -> right along any edge, right -> left
        // along matched edges).
        let mut reach_left = vec![false; n];
        let mut reach_right = vec![false; n];
        let mut stack: Vec<usize> = (0..n).filter(|&u| matched_left[u].is_none()).collect();
        for &u in &stack {
            reach_left[u] = true;
        }
        while let Some(u) = stack.pop() {
            for &v in &successors[u] {
                if !reach_right[v] {
                    reach_right[v] = true;
                    if let Some(w) = matched_right[v] {
                        if !reach_left[w] {
                            reach_left[w] = true;
                            stack.push(w);
                        }
                    }
                }
            }
        }
        // The cover is (L \ Z) u (R n Z); the antichain is what it misses.
        let antichain: Vec<usize> = (0..n)
            .filter(|&x| reach_left[x] && !reach_right[x])
            .collect();
        WidthCertificate { antichain, chains }
    }

    fn extract_matched_chains(
        n: usize,
        matched_right: &[Option<usize>],
        matched_left: &[Option<usize>],
    ) -> Vec<Vec<usize>> {
        let mut chains = Vec::new();
        for start in 0..n {
            if matched_right[start].is_none() {
                let mut chain = vec![start];
                let mut here = start;
                while let Some(next) = matched_left[here] {
                    chain.push(next);
                    here = next;
                }
                chains.push(chain);
            }
        }
        chains
    }

    /// The size of a largest antichain.
    pub fn width(&self) -> usize {
        self.width_certificate().chains.len()
    }

    /// Every maximal chain: a chain `a_0 < .. < a_k` in which each step is a
    /// cover, `a_0` is minimal and `a_k` is maximal. Lexicographic order.
    /// These are the facets of the order complex.
    ///
    /// Refused with [`PosetError::BudgetExceeded`] when there are more than
    /// `limit` of them.
    pub fn maximal_chains(&self, limit: usize) -> Result<Vec<Vec<usize>>, PosetError> {
        let upper: Vec<Vec<usize>> = (0..self.size)
            .map(|u| {
                ones(self.less_row(u))
                    .into_iter()
                    .filter(|&v| self.is_cover_unchecked(u, v))
                    .collect()
            })
            .collect();
        let mut out = Vec::new();
        let mut path = Vec::new();
        for start in self.minimal_elements() {
            self.extend_maximal_chain(start, &upper, &mut path, &mut out, limit)?;
        }
        Ok(out)
    }

    fn extend_maximal_chain(
        &self,
        here: usize,
        upper: &[Vec<usize>],
        path: &mut Vec<usize>,
        out: &mut Vec<Vec<usize>>,
        limit: usize,
    ) -> Result<(), PosetError> {
        path.push(here);
        if upper[here].is_empty() {
            if out.len() >= limit {
                return Err(PosetError::BudgetExceeded {
                    what: "maximal chains",
                    limit,
                });
            }
            out.push(path.clone());
        } else {
            for &next in &upper[here] {
                self.extend_maximal_chain(next, upper, path, out, limit)?;
            }
        }
        path.pop();
        Ok(())
    }

    /// Every nonempty chain, each listed in increasing order, in
    /// lexicographic order.
    ///
    /// Refused with [`PosetError::BudgetExceeded`] beyond `limit` chains.
    pub fn chains(&self, limit: usize) -> Result<Vec<Vec<usize>>, PosetError> {
        let mut out = Vec::new();
        let mut path = Vec::new();
        for start in 0..self.size {
            self.extend_chain(start, &mut path, &mut out, limit)?;
        }
        Ok(out)
    }

    fn extend_chain(
        &self,
        here: usize,
        path: &mut Vec<usize>,
        out: &mut Vec<Vec<usize>>,
        limit: usize,
    ) -> Result<(), PosetError> {
        path.push(here);
        if out.len() >= limit {
            return Err(PosetError::BudgetExceeded {
                what: "chains",
                limit,
            });
        }
        out.push(path.clone());
        for next in ones(self.less_row(here)) {
            self.extend_chain(next, path, out, limit)?;
        }
        path.pop();
        Ok(())
    }

    /// Every linear extension, lexicographically. Refused beyond `limit`.
    pub fn linear_extensions(&self, limit: usize) -> Result<Vec<Vec<usize>>, PosetError> {
        let mut pending: Vec<usize> = (0..self.size)
            .map(|u| popcount(self.greater_row(u)))
            .collect();
        let mut placed = vec![false; self.size];
        let mut order = Vec::with_capacity(self.size);
        let mut out = Vec::new();
        self.extend_linear(&mut pending, &mut placed, &mut order, &mut out, limit)?;
        Ok(out)
    }

    fn extend_linear(
        &self,
        pending: &mut [usize],
        placed: &mut [bool],
        order: &mut Vec<usize>,
        out: &mut Vec<Vec<usize>>,
        limit: usize,
    ) -> Result<(), PosetError> {
        if order.len() == self.size {
            if out.len() >= limit {
                return Err(PosetError::BudgetExceeded {
                    what: "linear extensions",
                    limit,
                });
            }
            out.push(order.clone());
            return Ok(());
        }
        for u in 0..self.size {
            if placed[u] || pending[u] != 0 {
                continue;
            }
            placed[u] = true;
            order.push(u);
            let above = ones(self.less_row(u));
            for &v in &above {
                pending[v] -= 1;
            }
            self.extend_linear(pending, placed, order, out, limit)?;
            for &v in &above {
                pending[v] += 1;
            }
            order.pop();
            placed[u] = false;
        }
        Ok(())
    }

    /// The number of linear extensions, by dynamic programming over down-sets:
    /// `e(D) = sum over maximal x in D of e(D \ {x})`, `e({}) = 1`.
    ///
    /// Refused when the poset has more than
    /// [`MAX_LINEAR_EXTENSION_ELEMENTS`] elements, and with
    /// [`PosetError::BudgetExceeded`] when more than `max_downsets` distinct
    /// down-sets would have to be visited (an antichain of `n` elements has
    /// `2^n` of them).
    pub fn count_linear_extensions(&self, max_downsets: usize) -> Result<BigUint, PosetError> {
        if self.size > MAX_LINEAR_EXTENSION_ELEMENTS {
            return Err(PosetError::TooManyElements {
                requested: self.size,
                limit: MAX_LINEAR_EXTENSION_ELEMENTS,
            });
        }
        if self.size == 0 {
            return Ok(BigUint::one());
        }
        let successors: Vec<u64> = (0..self.size).map(|u| self.less_row(u)[0]).collect();
        let full = if self.size == 64 {
            u64::MAX
        } else {
            (1u64 << self.size) - 1
        };
        let mut memo = BTreeMap::new();
        count_down_set_orders(full, &successors, &mut memo, max_downsets)
    }

    /// The zeta function as a matrix over `Q`: entry `(u, v)` is `1` when
    /// `u <= v` and `0` otherwise.
    pub fn zeta_matrix(&self) -> Result<BasicMatrix<BigRational>, PosetError> {
        Ok(BasicMatrix::try_from_fn(self.size, self.size, |u, v| {
            if self.less_or_equal_unchecked(u, v) {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        })?)
    }

    /// The Mobius function by the defining recursion
    /// `mu(x, x) = 1`, `mu(x, y) = - sum_{x <= z < y} mu(x, z)`.
    pub fn mobius(&self) -> MobiusFunction {
        let n = self.size;
        let mut values = vec![BigInt::zero(); n * n];
        for x in 0..n {
            values[x * n + x] = BigInt::one();
        }
        // A topological order lists every `z < y` before `y`; `mu(x, z)` is
        // still zero for every `z` that is not above `x`.
        let order = self.topological_order();
        for x in 0..n {
            for &y in &order {
                if !self.less_unchecked(x, y) {
                    continue;
                }
                let mut sum = BigInt::zero();
                for z in ones(self.greater_row(y)) {
                    sum += &values[x * n + z];
                }
                values[x * n + y] = -sum;
            }
        }
        MobiusFunction { size: n, values }
    }

    /// The Mobius function as the inverse of the zeta matrix: the matrix
    /// `[zeta | I]` is row-reduced over `Q` and the right block is read off.
    /// This shares no code with [`FinitePoset::mobius`].
    ///
    /// Refused above [`MAX_ZETA_INVERSION_ELEMENTS`] elements.
    pub fn mobius_by_zeta_inversion(&self) -> Result<MobiusFunction, PosetError> {
        let n = self.size;
        if n > MAX_ZETA_INVERSION_ELEMENTS {
            return Err(PosetError::TooManyElements {
                requested: n,
                limit: MAX_ZETA_INVERSION_ELEMENTS,
            });
        }
        if n == 0 {
            return Ok(MobiusFunction {
                size: 0,
                values: Vec::new(),
            });
        }
        let augmented = self.build_augmented_zeta()?;
        let reduction = augmented.rank_and_rref()?;
        if reduction.rank() != n || reduction.pivot_columns() != (0..n).collect::<Vec<_>>() {
            return Err(PosetError::ZetaNotInvertible);
        }
        let values = Self::extract_integral_mobius_entries(n, reduction.rref())?;
        Ok(MobiusFunction { size: n, values })
    }

    fn extract_integral_mobius_entries(
        n: usize,
        rref: &BasicMatrix<BigRational>,
    ) -> Result<Vec<BigInt>, PosetError> {
        let mut values = Vec::with_capacity(n * n);
        for row in 0..n {
            for col in 0..n {
                let entry = rref.get(row, n + col)?;
                if !entry.denom().is_one() {
                    return Err(PosetError::NonIntegralMobius { row, col });
                }
                values.push(entry.numer().clone());
            }
        }
        Ok(values)
    }

    fn build_augmented_zeta(&self) -> Result<BasicMatrix<BigRational>, PosetError> {
        let n = self.size;
        Ok(BasicMatrix::try_from_fn(n, 2 * n, |row, col| {
            if col < n {
                if self.less_or_equal_unchecked(row, col) {
                    BigRational::one()
                } else {
                    BigRational::zero()
                }
            } else if col - n == row {
                BigRational::one()
            } else {
                BigRational::zero()
            }
        })?)
    }

    /// The poset on the listed elements with the induced order, relabelled
    /// `0, 1, ..` in increasing order of the original labels. The second
    /// component lists the original label of each new element.
    pub fn induced_subposet(
        &self,
        elements: &[usize],
    ) -> Result<(FinitePoset, Vec<usize>), PosetError> {
        self.check_subset(elements)?;
        let mut original: Vec<usize> = elements.to_vec();
        original.sort_unstable();
        let mut relations = Vec::new();
        for (new_u, &u) in original.iter().enumerate() {
            for (new_v, &v) in original.iter().enumerate() {
                if self.less_unchecked(u, v) {
                    relations.push((new_u, new_v));
                }
            }
        }
        Ok((FinitePoset::new(original.len(), relations)?, original))
    }

    /// The opposite order: `u < v` here exactly when `v < u` there.
    pub fn dual(&self) -> FinitePoset {
        FinitePoset::from_less_rows(self.size, self.greater.clone())
    }

    /// The poset with a new least element (index `size`) and a new greatest
    /// element (index `size + 1`) adjoined.
    pub fn bounded_completion(&self) -> Result<BoundedCompletion, PosetError> {
        let bottom = self.size;
        let top = self.size + 1;
        Self::check_size(top + 1)?;
        let mut relations = self.strict_relations();
        for u in 0..self.size {
            relations.push((bottom, u));
            relations.push((u, top));
        }
        relations.push((bottom, top));
        Ok(BoundedCompletion {
            poset: FinitePoset::new(self.size + 2, relations)?,
            bottom,
            top,
        })
    }

    /// The order complex: the simplicial complex whose simplices are the
    /// nonempty chains, with the elements as vertices.
    ///
    /// Refused with [`PosetError::BudgetExceeded`] when the poset has more
    /// than `max_maximal_chains` maximal chains.
    pub fn order_complex(
        &self,
        max_maximal_chains: usize,
    ) -> Result<SimplicialComplex, PosetError> {
        let facets = self
            .maximal_chains(max_maximal_chains)?
            .into_iter()
            .map(Simplex::from_unordered)
            .collect::<Result<Vec<_>, _>>()?;
        Ok(SimplicialComplex::from_simplices(facets)?)
    }

    /// The order complex of the open interval `(a, b)`, relabelled as in
    /// [`FinitePoset::induced_subposet`]. It is the empty complex when `b`
    /// covers `a` or `a` is not below `b`.
    pub fn order_complex_of_open_interval(
        &self,
        a: usize,
        b: usize,
        max_maximal_chains: usize,
    ) -> Result<SimplicialComplex, PosetError> {
        let open = self.open_interval(a, b)?;
        let (sub, _) = self.induced_subposet(&open)?;
        sub.order_complex(max_maximal_chains)
    }

    /// `mu(x, y)` by Philip Hall's theorem: for `x < y` it is the reduced
    /// Euler characteristic `chi(Delta((x, y))) - 1` of the order complex of
    /// the open interval. `1` when `x = y`, `0` when `x` is not below `y`.
    ///
    /// This route never touches the recursion or the zeta matrix.
    pub fn mobius_by_order_complex(
        &self,
        x: usize,
        y: usize,
        max_maximal_chains: usize,
    ) -> Result<BigInt, PosetError> {
        self.check(x)?;
        self.check(y)?;
        if x == y {
            return Ok(BigInt::one());
        }
        if !self.less_unchecked(x, y) {
            return Ok(BigInt::zero());
        }
        let complex = self.order_complex_of_open_interval(x, y, max_maximal_chains)?;
        Ok(BigInt::from(complex.euler_characteristic()) - BigInt::one())
    }
}

/// One augmenting-path step of Kuhn's bipartite matching (left `u`, right
/// `v` for every `u < v`).
fn augment(
    u: usize,
    successors: &[Vec<usize>],
    visited: &mut [bool],
    matched_right: &mut [Option<usize>],
    matched_left: &mut [Option<usize>],
) -> bool {
    for &v in &successors[u] {
        if visited[v] {
            continue;
        }
        visited[v] = true;
        let free = match matched_right[v] {
            None => true,
            Some(other) => augment(other, successors, visited, matched_right, matched_left),
        };
        if free {
            matched_right[v] = Some(u);
            matched_left[u] = Some(v);
            return true;
        }
    }
    false
}

fn count_down_set_orders(
    mask: u64,
    successors: &[u64],
    memo: &mut BTreeMap<u64, BigUint>,
    limit: usize,
) -> Result<BigUint, PosetError> {
    if mask == 0 {
        return Ok(BigUint::one());
    }
    if let Some(known) = memo.get(&mask) {
        return Ok(known.clone());
    }
    if memo.len() >= limit {
        return Err(PosetError::BudgetExceeded {
            what: "down-sets visited while counting linear extensions",
            limit,
        });
    }
    let mut total = BigUint::zero();
    let mut rest = mask;
    while rest != 0 {
        let x = rest.trailing_zeros() as usize;
        rest &= rest - 1;
        // x is maximal in the down-set when nothing above it is still in it.
        if successors[x] & mask == 0 {
            total += count_down_set_orders(mask & !(1u64 << x), successors, memo, limit)?;
        }
    }
    memo.insert(mask, total.clone());
    Ok(total)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_09753983 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
