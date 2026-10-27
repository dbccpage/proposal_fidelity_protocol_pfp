// Multiplicity-free fusion categories: F-symbols, the pentagon equation, unit
// normalisation, gauge transformations, unitarity and dimension data.
//
// Conventions. For simple objects `a, b, c, d` the F-symbol `[F^{abc}_d]_{ef}` is the
// coefficient in `|(a b)_e c; d> = sum_f [F^{abc}_d]_{ef} |a (b c)_f; d>`, where `e`
// runs over the labels of `a x b` that fuse with `c` to `d`, and `f` over the labels
// of `b x c` that fuse with `a` to `d`. The pentagon equation, for all labels, is
//
// `[F^{fcd}_e]_{gl} [F^{abl}_e]_{fk} = sum_h [F^{abc}_g]_{fh} [F^{ahd}_e]_{gk} [F^{bcd}_k]_{hl}`,
//
// with the convention that an F-symbol whose indices are not admissible is zero. A
// gauge is a nonzero scalar `u^{ab}_c` for each vertex `N_{ab}^c = 1`; it acts by
// `F' = u^{ab}_e u^{ec}_d / (u^{bc}_f u^{af}_d) F`.
//
// The unit normalisation asks `F^{abc}_d = 1` whenever one of `a, b, c` is the unit.
// The quantity `[F^{a a* a}_a]_{00} [F^{a* a a*}_{a*}]_{00}` is invariant under gauges
// that fix the unit vertices, and equals `1 / (d_a d_{a*})` for the quantum
// dimensions of a pivotal category; a Frobenius-Schur indicator of a self-dual object
// is `nu_a = d_a [F^{aaa}_a]_{00}`.
//
// What is computed: the pentagon equation exactly over `K` (every violated index
// tuple, not a tolerance), unit-law violations, unitarity of the F-matrices, exact
// gauge transformations and the canonical unit-normalising gauge, and the
// consistency of a proposed dimension vector with the ring and with the F-symbols.
// What is not: the existence of a category for ring data without F-symbols,
// categorification of rings with multiplicity (`N > 1`), or positivity of dimensions.
//
// AuthorityEffect: None.
use std::collections::BTreeMap;

use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use thiserror::Error;

use crate::error::FusionError;
use crate::fusion_ring::FusionRing;
use crate::scalar::FusionScalar;
use linear_algebra::exact_field::{elimination, involution};

/// Default bounds for constructing F-symbols and replaying all category laws.
/// These charge aggregate symbol storage, defect records, label traversal and
/// scalar calls; they do not count work inside a caller's coefficient generator.
pub const DEFAULT_CATEGORY_LIMITS: OperationLimits = OperationLimits {
    max_elements: 1 << 20,
    max_scalar_ops: 1 << 28,
};

// All callers hold a sealed FusionRing: 1<=rank<=32 and multiplicities are0/1.
fn label_pairs(rank: usize) -> impl Iterator<Item = [usize; 2]> {
    (0..rank).flat_map(move |a| (0..rank).map(move |b| [a, b]))
}

fn label_triples(rank: usize) -> impl Iterator<Item = [usize; 3]> {
    label_pairs(rank).flat_map(move |[a, b]| (0..rank).map(move |c| [a, b, c]))
}

fn label_quadruples(rank: usize) -> impl Iterator<Item = [usize; 4]> {
    label_triples(rank).flat_map(move |[a, b, c]| (0..rank).map(move |d| [a, b, c, d]))
}

type FusionSupport = Vec<Vec<Vec<usize>>>;

fn fusion_support(ring: &FusionRing) -> FusionSupport {
    (0..ring.rank())
        .map(|a| {
            (0..ring.rank())
                .map(|b| (0..ring.rank()).filter(|&c| ring.n(a, b, c) > 0).collect())
                .collect()
        })
        .collect()
}

fn charge_category(what: &'static str, requested: u128, limit: usize) -> Result<(), FusionError> {
    if requested > limit as u128 {
        return Err(FusionError::Budget {
            what,
            requested,
            limit: limit as u128,
        });
    }
    Ok(())
}

fn triple_path_counts(fuse: &FusionSupport, [a, b, c]: [usize; 3], counts: &mut [usize]) {
    counts.fill(0);
    for &e in &fuse[a][b] {
        for &total in &fuse[e][c] {
            counts[total] += 1;
        }
    }
}

fn extend_path_counts(fuse: &FusionSupport, counts: &[usize], label: usize, output: &mut [usize]) {
    output.fill(0);
    for (g, &count) in counts.iter().enumerate().filter(|(_, count)| **count != 0) {
        for &total in &fuse[g][label] {
            output[total] += count;
        }
    }
}

fn block_resource_totals(dimensions: &[usize]) -> (u128, u128) {
    dimensions
        .iter()
        .filter(|&&d| d != 0)
        .fold((0, 0), |(entries, work), &dimension| {
            let d = dimension as u128;
            (
                entries + 2 * (d * d + 2 * d + 4),
                work + 4 * d.pow(3) + 2 * d * d + d,
            )
        })
}

fn admit_category_resources(ring: &FusionRing, limits: OperationLimits) -> Result<(), FusionError> {
    let rank = ring.rank();
    let n = rank as u128;
    let fuse = fusion_support(ring);
    let width = fuse.iter().flatten().map(Vec::len).max().unwrap_or(0) as u128;
    let metadata = 4 * n.pow(5);
    let traversal = n.pow(4) * (2 * width.pow(6) + 2 * width.pow(3));
    charge_category(
        "fusion category label traversal",
        metadata + traversal,
        limits.max_scalar_ops,
    )?;
    let (mut entries, mut inverse_work, mut equations) = (0u128, 0u128, 0u128);
                    // F and its inverse, with their row/column/key labels.
                    // The two parenthesizations have the same dimension by
                    // fusion-ring associativity, so there are dimension^2 equations.
    // Two rank-sized buffers are reused for every label tuple.
    let mut three = vec![0usize; rank];
    let mut four = vec![0usize; rank];
    for labels in label_triples(rank) {
        triple_path_counts(&fuse, labels, &mut three);
        let (storage, inverse) = block_resource_totals(&three);
        entries += storage;
        inverse_work += inverse;
        for d in 0..rank {
            extend_path_counts(&fuse, &three, d, &mut four);
            equations += four
                .iter()
                .map(|&count| (count as u128).pow(2))
                .sum::<u128>();
        }
    }
    charge_category(
        "fusion category symbol storage",
        entries,
        limits.max_elements,
    )?;
    charge_category("pentagon defect records", equations, limits.max_elements)?;
    let pentagon_work = equations * (1 + 3 * width);
    let hexagon_work = 2 * n.pow(4) * width.pow(2) * (1 + 4 * width);
    charge_category(
        "fusion category aggregate replay work",
        metadata + traversal + inverse_work + pentagon_work + hexagon_work,
        limits.max_scalar_ops,
    )
}

/// A law of a fusion category that fails, with the indices at which it fails.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum CategoryDefect {
    /// `N_{ab}^c > 1`: F-symbols of this crate are scalars, which needs multiplicity one.
    #[error("the ring has multiplicity {multiplicity} at {labels:?}; only multiplicity-free categories are supported")]
    NotMultiplicityFree {
        labels: [usize; 3],
        multiplicity: u64,
    },
    /// An admissible `(a, b, c, d)` without an F-block.
    #[error("missing F-block for {labels:?}")]
    BlockMissing { labels: [usize; 4] },
    /// An F-block at a non-admissible `(a, b, c, d)`.
    #[error("unexpected F-block for {labels:?}")]
    BlockUnexpected { labels: [usize; 4] },
    /// An F-block that is not square or has the wrong size.
    #[error("F-block {labels:?} is {rows}x{cols}, expected {expected}x{expected}")]
    BlockShape {
        labels: [usize; 4],
        rows: usize,
        cols: usize,
        expected: usize,
    },
    /// An F-block whose row or column labels are not the admissible intermediate labels.
    #[error("F-block {labels:?} has the wrong intermediate labels")]
    BlockLabels { labels: [usize; 4] },
    /// An F-block that is not invertible.
    #[error("F-block {labels:?} is singular")]
    BlockSingular { labels: [usize; 4] },
    /// A violated pentagon equation at `(a, b, c, d, e, f, g, k, l)`.
    #[error("pentagon equation violated at {labels:?}")]
    Pentagon { labels: [usize; 9] },
    /// An F-symbol with a unit leg that is not `1`.
    #[error("F-symbol with a unit leg is not 1 at {labels:?}")]
    UnitLaw { labels: [usize; 4] },
    /// A gauge without an entry for an admissible vertex.
    #[error("the gauge has no entry for the vertex {labels:?}")]
    GaugeMissing { labels: [usize; 3] },
    /// A gauge entry equal to zero.
    #[error("the gauge entry at {labels:?} is zero")]
    GaugeZero { labels: [usize; 3] },
    /// The unit-normalising gauge does not exist for this data.
    #[error("no gauge normalises the unit F-symbols (obstruction at {labels:?})")]
    UnitNormalizationImpossible { labels: [usize; 3] },
    /// A dimension vector inconsistent with the category.
    #[error("dimension data: {0}")]
    Dimensions(DimensionDefect),
}

/// Why a proposed dimension vector is not the dimension vector of the category.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Error)]
pub enum DimensionDefect {
    /// The vector does not have one entry per simple object.
    #[error("expected {expected} dimensions, got {got}")]
    Count { expected: usize, got: usize },
    /// `d_0 != 1`.
    #[error("the unit has dimension other than 1")]
    UnitNotOne,
    /// `d_a` is zero.
    #[error("label {label} has dimension zero")]
    Zero { label: usize },
    /// `d_{a*} != d_a` (not spherical).
    #[error("label {label} and its dual have different dimensions")]
    NotSpherical { label: usize },
    /// `d_a d_b != sum_c N_{ab}^c d_c`.
    #[error("dimensions are not a character of the fusion ring at ({a}, {b})")]
    NotCharacter { a: usize, b: usize },
    /// `d_a d_{a*} [F^{a a* a}_a]_{00} [F^{a* a a*}_{a*}]_{00} != 1`.
    #[error("dimension of label {label} disagrees with the F-symbols")]
    DisagreesWithF { label: usize },
    /// `d_a [F^{aaa}_a]_{00}` is not `+1` or `-1`.
    #[error("Frobenius-Schur value of label {label} is not a sign")]
    FrobeniusSchurNotSign { label: usize },
}

fn dimension_error(defect: DimensionDefect) -> FusionError {
    FusionError::Category(CategoryDefect::Dimensions(defect))
}

/// One F-matrix `F^{abc}_d`: rows are the admissible `e`, columns the admissible `f`,
/// both ascending.
#[derive(Debug, Clone, PartialEq)]
pub struct FBlock<K> {
    rows: Vec<usize>,
    cols: Vec<usize>,
    matrix: BasicMatrix<K>,
}

impl<K: FusionScalar> FBlock<K> {
    /// The row labels `e`.
    pub fn rows(&self) -> &[usize] {
        &self.rows
    }

    /// The column labels `f`.
    pub fn cols(&self) -> &[usize] {
        &self.cols
    }

    /// The matrix (rows indexed by [`Self::rows`], columns by [`Self::cols`]).
    pub fn matrix(&self) -> &BasicMatrix<K> {
        &self.matrix
    }

    /// The entry `[F]_{ef}`, or `None` when `e` or `f` is not admissible (an F-symbol
    /// with non-admissible indices is zero).
    pub fn entry(&self, e: usize, f: usize) -> Option<&K> {
        let i = self.rows.binary_search(&e).ok()?;
        let j = self.cols.binary_search(&f).ok()?;
        self.matrix.get_ref(i, j).ok()
    }

    /// The inverse block: rows are the old columns, columns the old rows.
    pub fn inverse(&self) -> Result<FBlock<K>, FusionError> {
        Ok(FBlock {
            rows: self.cols.clone(),
            cols: self.rows.clone(),
            matrix: elimination::inverse(&self.matrix).map_err(FusionError::from)?,
        })
    }
}

/// The F-symbols of a multiplicity-free fusion ring.
#[derive(Debug, Clone, PartialEq)]
pub struct FSymbols<K> {
    rank: usize,
    blocks: BTreeMap<[usize; 4], FBlock<K>>,
}

impl<K: FusionScalar> FSymbols<K> {
    /// Builds the F-blocks of `ring` from an entry function
    /// `entry([a, b, c, d], e, f) = [F^{abc}_d]_{ef}`, called once per admissible entry.
    pub fn from_fn(
        ring: &FusionRing,
        mut entry: impl FnMut([usize; 4], usize, usize) -> K,
    ) -> Result<Self, FusionError> {
        Self::try_from_fn(ring, |labels, e, f| Ok(entry(labels, e, f)))
    }

    /// [`Self::from_fn`] with full category-law resource admission.
    pub fn from_fn_with_limits(
        ring: &FusionRing,
        limits: OperationLimits,
        mut entry: impl FnMut([usize; 4], usize, usize) -> K,
    ) -> Result<Self, FusionError> {
        Self::try_from_fn_with_limits(ring, limits, |labels, e, f| Ok(entry(labels, e, f)))
    }

    /// F-symbols from a fallible exact formula. A refused coefficient is
    /// propagated before an incomplete block can become category data.
    pub fn try_from_fn(
        ring: &FusionRing,
        entry: impl FnMut([usize; 4], usize, usize) -> Result<K, FusionError>,
    ) -> Result<Self, FusionError> {
        Self::try_from_fn_with_limits(ring, DEFAULT_CATEGORY_LIMITS, entry)
    }

    /// [`Self::try_from_fn`] with storage and full-law replay admission before
    /// invoking a coefficient formula or allocating its blocks.
    pub fn try_from_fn_with_limits(
        ring: &FusionRing,
        limits: OperationLimits,
        mut entry: impl FnMut([usize; 4], usize, usize) -> Result<K, FusionError>,
    ) -> Result<Self, FusionError> {
        require_multiplicity_free(ring)?;
        admit_category_resources(ring, limits)?;
        let mut blocks = BTreeMap::new();
        for labels in label_quadruples(ring.rank()) {
            if let Some(block) = build_f_block(ring, labels, limits.max_elements, &mut entry)? {
                blocks.insert(labels, block);
            }
        }
        Ok(Self {
            rank: ring.rank(),
            blocks,
        })
    }

    /// The trivial associator `F = 1` of a pointed ring (every block is `1 x 1`).
    pub fn trivial(ring: &FusionRing) -> Result<Self, FusionError> {
        if !ring.is_pointed() {
            return Err(FusionError::NotInSubfield {
                what: "a fusion ring with non-invertible objects",
                expected: "pointed (every F-block 1x1)",
            });
        }
        Self::from_fn(ring, |_, _, _| K::one())
    }

    /// The number of simple objects.
    pub fn rank(&self) -> usize {
        self.rank
    }

    /// The block `F^{abc}_d`, if `(a, b, c, d)` is admissible.
    pub fn block(&self, labels: [usize; 4]) -> Option<&FBlock<K>> {
        self.blocks.get(&labels)
    }

    /// The entry `[F^{abc}_d]_{ef}`, or `None` (zero) when an index is not admissible.
    pub fn entry(&self, labels: [usize; 4], e: usize, f: usize) -> Option<&K> {
        self.block(labels)?.entry(e, f)
    }

    /// All blocks in index order.
    pub fn blocks(&self) -> impl Iterator<Item = (&[usize; 4], &FBlock<K>)> {
        self.blocks.iter()
    }

    /// A copy with one admissible entry replaced (for negative controls and
    /// experiments). Refuses a non-admissible index.
    pub fn with_entry(
        &self,
        labels: [usize; 4],
        e: usize,
        f: usize,
        value: K,
    ) -> Result<Self, FusionError> {
        let block = self.blocks.get(&labels).ok_or(FusionError::Category(
            CategoryDefect::BlockMissing { labels },
        ))?;
        let i = block
            .rows
            .binary_search(&e)
            .map_err(|_| FusionError::Category(CategoryDefect::BlockLabels { labels }))?;
        let j = block
            .cols
            .binary_search(&f)
            .map_err(|_| FusionError::Category(CategoryDefect::BlockLabels { labels }))?;
        let mut blocks = self.blocks.clone();
        let block =
            blocks
                .get_mut(&labels)
                .ok_or(FusionError::Category(CategoryDefect::BlockMissing {
                    labels,
                }))?;
        block.matrix.set(i, j, value)?;
        Ok(Self {
            rank: self.rank,
            blocks,
        })
    }
}

fn build_f_block<K: FusionScalar>(
    ring: &FusionRing,
    labels: [usize; 4],
    max_elements: usize,
    entry: &mut impl FnMut([usize; 4], usize, usize) -> Result<K, FusionError>,
) -> Result<Option<FBlock<K>>, FusionError> {
    let (rows, cols) = intermediate_labels(ring, labels);
    if rows.is_empty() && cols.is_empty() {
        return Ok(None);
    }
    if rows.len() != cols.len() {
        return Err(FusionError::Category(CategoryDefect::BlockShape {
            labels,
            rows: rows.len(),
            cols: cols.len(),
            expected: rows.len(),
        }));
    }
    // Matrix callbacks supply indices within the admitted row/column shape.
    let matrix = BasicMatrix::try_from_fn_result_with_limit(
        rows.len(),
        cols.len(),
        max_elements,
        |i, j| entry(labels, rows[i], cols[j]),
    )?;
    Ok(Some(FBlock { rows, cols, matrix }))
}

fn require_multiplicity_free(ring: &FusionRing) -> Result<(), FusionError> {
    for labels in label_triples(ring.rank()) {
        let [a, b, c] = labels;
        let multiplicity = ring.n(a, b, c);
        if multiplicity > 1 {
            return Err(FusionError::Category(CategoryDefect::NotMultiplicityFree {
                labels,
                multiplicity,
            }));
        }
    }
    Ok(())
}

/// The admissible `(rows e, cols f)` of the block `F^{abc}_d`.
fn row_channels(
    ring: &FusionRing,
    [a, b, c, d]: [usize; 4],
) -> impl Iterator<Item = usize> + Clone + '_ {
    (0..ring.rank()).filter(move |&e| ring.n(a, b, e) > 0 && ring.n(e, c, d) > 0)
}

fn column_channels(
    ring: &FusionRing,
    [a, b, c, d]: [usize; 4],
) -> impl Iterator<Item = usize> + Clone + '_ {
    (0..ring.rank()).filter(move |&f| ring.n(b, c, f) > 0 && ring.n(a, f, d) > 0)
}

fn intermediate_labels(ring: &FusionRing, labels: [usize; 4]) -> (Vec<usize>, Vec<usize>) {
    (
        row_channels(ring, labels).collect(),
        column_channels(ring, labels).collect(),
    )
}

struct PentagonPaths {
    left: Vec<[usize; 3]>,
    right: Vec<Vec<[usize; 2]>>,
}

impl PentagonPaths {
    fn new(rank: usize) -> Self {
        Self {
            left: Vec::new(),
            right: vec![Vec::new(); rank],
        }
    }

    fn fill_left(&mut self, fuse: &FusionSupport, [a, b, c, d]: [usize; 4]) {
        self.left.clear();
        for &f in &fuse[a][b] {
            for &g in &fuse[f][c] {
                for &e in &fuse[g][d] {
                    self.left.push([e, f, g]);
                }
            }
        }
        self.left.sort_unstable();
    }

    fn fill_right(&mut self, fuse: &FusionSupport, [a, b, c, d]: [usize; 4]) {
        for group in &mut self.right {
            group.clear();
        }
        for &l in &fuse[c][d] {
            for &k in &fuse[b][l] {
                for &e in &fuse[a][k] {
                    self.right[e].push([k, l]);
                }
            }
        }
        for group in &mut self.right {
            group.sort_unstable();
        }
    }
}

/// A violated pentagon equation with both sides.
#[derive(Debug, Clone, PartialEq)]
pub struct PentagonDefect<K> {
    /// `(a, b, c, d, e, f, g, k, l)`.
    pub labels: [usize; 9],
    /// `[F^{fcd}_e]_{gl} [F^{abl}_e]_{fk}`.
    pub lhs: K,
    /// `sum_h [F^{abc}_g]_{fh} [F^{ahd}_e]_{gk} [F^{bcd}_k]_{hl}`.
    pub rhs: K,
}

impl<K> PentagonDefect<K> {
    /// Whether the F-symbol entry `[F^{a2 b2 c2}_{d2}]_{e2 f2}` is one of the entries this
    /// equation reads: the two factors of the left-hand side, or a factor of a term of
    /// the right-hand side for some summation label `h`.
    ///
    /// An equation reads only those entries, so a perturbation of any other entry cannot
    /// make it fail; the set is an upper bound on the entries that can matter (terms with
    /// an inadmissible `h` are zero).
    pub fn involves(&self, [a2, b2, c2, d2]: [usize; 4], e2: usize, f2: usize) -> bool {
        let [a, b, c, d, e, f, g, k, l] = self.labels;
        let left = ([a2, b2, c2, d2] == [f, c, d, e] && (e2, f2) == (g, l))
            || ([a2, b2, c2, d2] == [a, b, l, e] && (e2, f2) == (f, k));
        let right = ([a2, b2, c2, d2] == [a, b, c, g] && e2 == f)
            || ([a2, c2, d2] == [a, d, e] && (e2, f2) == (g, k))
            || ([a2, b2, c2, d2] == [b, c, d, k] && f2 == l);
        left || right
    }
}

/// A gauge: a nonzero scalar `u^{ab}_c` for every vertex `N_{ab}^c = 1`.
#[derive(Debug, Clone, PartialEq)]
pub struct Gauge<K> {
    u: BTreeMap<[usize; 3], K>,
}

impl<K: FusionScalar> Gauge<K> {
    /// The trivial gauge (`u = 1` everywhere).
    pub fn trivial(ring: &FusionRing) -> Self {
        Self::build(ring, |_| K::one())
    }

    fn build(ring: &FusionRing, mut value: impl FnMut([usize; 3]) -> K) -> Self {
        let mut u = BTreeMap::new();
        for labels in label_triples(ring.rank()) {
            if ring.n(labels[0], labels[1], labels[2]) > 0 {
                u.insert(labels, value(labels));
            }
        }
        Self { u }
    }

    /// A gauge from a function of the vertex; a zero value is refused.
    pub fn from_fn(
        ring: &FusionRing,
        value: impl FnMut([usize; 3]) -> K,
    ) -> Result<Self, FusionError> {
        let gauge = Self::build(ring, value);
        if let Some((labels, _)) = gauge.u.iter().find(|(_, v)| v.is_zero()) {
            return Err(FusionError::Category(CategoryDefect::GaugeZero {
                labels: *labels,
            }));
        }
        Ok(gauge)
    }

    /// `u^{ab}_c`, if `(a, b; c)` is a vertex.
    pub fn get(&self, labels: [usize; 3]) -> Option<&K> {
        self.u.get(&labels)
    }

    fn require(&self, labels: [usize; 3]) -> Result<&K, FusionError> {
        self.u
            .get(&labels)
            .ok_or(FusionError::Category(CategoryDefect::GaugeMissing {
                labels,
            }))
    }

    /// A copy with one vertex changed; a zero value or a non-vertex is refused.
    fn validate_entry(&self, labels: [usize; 3], value: &K) -> Result<(), FusionError> {
        if value.is_zero() {
            return Err(FusionError::Category(CategoryDefect::GaugeZero { labels }));
        }
        self.require(labels)?;
        Ok(())
    }

    fn replace(&mut self, labels: [usize; 3], value: K) -> Result<(), FusionError> {
        self.validate_entry(labels, &value)?;
        self.u.insert(labels, value);
        Ok(())
    }

    pub fn with(&self, labels: [usize; 3], value: K) -> Result<Self, FusionError> {
        self.validate_entry(labels, &value)?;
        let mut result = self.clone();
        result.u.insert(labels, value);
        Ok(result)
    }

    /// The pointwise inverse gauge.
    pub fn inverse(&self) -> Result<Self, FusionError> {
        let mut u = BTreeMap::new();
        for (labels, value) in &self.u {
            u.insert(
                *labels,
                core_number_theory::scalar::inverse(value).map_err(FusionError::from)?,
            );
        }
        Ok(Self { u })
    }
}

enum InverseBlock<K> {
    Vacant,
    Invertible(FBlock<K>),
    Singular,
}

fn classify_f_block<K: FusionScalar>(
    ring: &FusionRing,
    f: &FSymbols<K>,
    labels: [usize; 4],
) -> Result<InverseBlock<K>, FusionError> {
    let rows = row_channels(ring, labels);
    let cols = column_channels(ring, labels);
    let admissible = rows.clone().next().is_some() || cols.clone().next().is_some();
    let block = match (f.block(labels), admissible) {
        (None, false) => return Ok(InverseBlock::Vacant),
        (None, true) => {
            return Err(FusionError::Category(CategoryDefect::BlockMissing {
                labels,
            }))
        }
        (Some(_), false) => {
            return Err(FusionError::Category(CategoryDefect::BlockUnexpected {
                labels,
            }))
        }
        (Some(block), true) => block,
    };
    if !block.rows.iter().copied().eq(rows) || !block.cols.iter().copied().eq(cols) {
        return Err(FusionError::Category(CategoryDefect::BlockLabels {
            labels,
        }));
    }
    if block.matrix.shape() != (block.rows.len(), block.cols.len()) {
        return Err(FusionError::Category(CategoryDefect::BlockShape {
            labels,
            rows: block.matrix.shape().0,
            cols: block.matrix.shape().1,
            expected: block.rows.len(),
        }));
    }
    invert_f_block(block)
}

fn invert_f_block<K: FusionScalar>(block: &FBlock<K>) -> Result<InverseBlock<K>, FusionError> {
    match block.inverse() {
        Ok(inverse) => Ok(InverseBlock::Invertible(inverse)),
        Err(
            FusionError::Singular { .. }
            | FusionError::NoInverse { .. }
            | FusionError::ExactField(linear_algebra::exact_field::ExactFieldError::Singular {
                ..
            }),
        ) => Ok(InverseBlock::Singular),
        Err(other) => Err(other),
    }
}

/// A multiplicity-free fusion category: a fusion ring with its F-symbols.
///
/// Construction checks structure (blocks present exactly at the admissible labels, with
/// the right labels). Blocks that are not invertible are recorded ([`Self::singular_blocks`]),
/// not refused, so that the pentagon equation can still be checked on such data and report
/// exactly where it fails; [`Self::validate`] and every braided construction refuse them.
/// The pentagon and unit laws are checked by [`Self::pentagon_defects`],
/// [`Self::unit_defects`] and [`Self::validate`].
#[derive(Debug, Clone, PartialEq)]
pub struct FusionCategory<K> {
    ring: FusionRing,
    f: FSymbols<K>,
    f_inverse: BTreeMap<[usize; 4], FBlock<K>>,
    singular: Vec<[usize; 4]>,
}

impl<K: FusionScalar> FusionCategory<K> {
    /// A category from a ring and its F-symbols (structure checked, pentagon not).
    pub fn new(ring: FusionRing, f: FSymbols<K>) -> Result<Self, FusionError> {
        Self::new_with_limits(ring, f, DEFAULT_CATEGORY_LIMITS)
    }

    /// [`Self::new`] with admission for aggregate construction and all law scans.
    pub fn new_with_limits(
        ring: FusionRing,
        f: FSymbols<K>,
        limits: OperationLimits,
    ) -> Result<Self, FusionError> {
        require_multiplicity_free(&ring)?;
        admit_category_resources(&ring, limits)?;
        let r = ring.rank();
        if f.rank != r {
            return Err(FusionError::ListLength {
                what: "F-symbol labels",
                expected: r,
                got: f.rank,
            });
        }
        let mut f_inverse = BTreeMap::new();
        let mut singular = Vec::new();
        for labels in label_quadruples(r) {
            match classify_f_block(&ring, &f, labels)? {
                InverseBlock::Vacant => {}
                InverseBlock::Invertible(inverse) => {
                    f_inverse.insert(labels, inverse);
                }
                InverseBlock::Singular => singular.push(labels),
            }
        }
        Ok(Self {
            ring,
            f,
            f_inverse,
            singular,
        })
    }

    /// The labels `(a, b, c, d)` of the F-blocks that are not invertible (none in any
    /// valid category).
    pub fn singular_blocks(&self) -> &[[usize; 4]] {
        &self.singular
    }

    /// A category whose structure, unit laws and pentagon equation all hold.
    pub fn validated(ring: FusionRing, f: FSymbols<K>) -> Result<Self, FusionError> {
        let category = Self::new(ring, f)?;
        category.validate()?;
        Ok(category)
    }

    /// The fusion ring.
    pub fn ring(&self) -> &FusionRing {
        &self.ring
    }

    /// The F-symbols.
    pub fn f_symbols(&self) -> &FSymbols<K> {
        &self.f
    }

    /// `[F^{abc}_d]_{ef}` (zero when an index is not admissible).
    pub fn f_entry(&self, labels: [usize; 4], e: usize, f: usize) -> K {
        self.f.entry(labels, e, f).cloned().unwrap_or_else(K::zero)
    }

    /// The inverse block `(F^{abc}_d)^{-1}`: rows are the old columns `f`, columns the
    /// old rows `e`.
    pub fn f_inverse_block(&self, labels: [usize; 4]) -> Option<&FBlock<K>> {
        self.f_inverse.get(&labels)
    }

    /// `[(F^{abc}_d)^{-1}]_{fe}` (zero when an index is not admissible).
    pub fn f_inverse_entry(&self, labels: [usize; 4], f: usize, e: usize) -> K {
        self.f_inverse
            .get(&labels)
            .and_then(|block| block.entry(f, e))
            .cloned()
            .unwrap_or_else(K::zero)
    }

    fn fuse_table(&self) -> FusionSupport {
        fusion_support(&self.ring)
    }

    /// Every violated pentagon equation, exactly, in index order.
    pub fn pentagon_defects(&self) -> Vec<PentagonDefect<K>> {
        self.pentagon_scan(false)
    }

    /// The first violated pentagon equation in index order, if any.
    pub fn first_pentagon_defect(&self) -> Option<PentagonDefect<K>> {
        self.pentagon_scan(true).into_iter().next()
    }

    /// Scans the pentagon tuples `(a, b, c, d, e, f, g, k, l)` in lexicographic order.
    ///
    /// Every nonzero term of either side needs `f in a x b`, `g in f x c`, `e in g x d`,
    /// `l in c x d`, `k in b x l` and `e in a x k` (the basis vectors at both ends of the
    /// equation exist), so the scan is restricted to those tuples; any other tuple has
    /// both sides zero.
    fn pentagon_scan(&self, stop_at_first: bool) -> Vec<PentagonDefect<K>> {
        let fuse = self.fuse_table();
        let mut defects = Vec::new();
        let mut paths = PentagonPaths::new(self.ring.rank());
        for labels in label_quadruples(self.ring.rank()) {
            if self.pentagon_quad_scan(labels, &fuse, &mut paths, stop_at_first, &mut defects) {
                break;
            }
        }
        defects
    }

    fn pentagon_quad_scan(
        &self,
        [a, b, c, d]: [usize; 4],
        fuse: &FusionSupport,
        paths: &mut PentagonPaths,
        stop_at_first: bool,
        defects: &mut Vec<PentagonDefect<K>>,
    ) -> bool {
        paths.fill_left(fuse, [a, b, c, d]);
        paths.fill_right(fuse, [a, b, c, d]);
        for &[e, f, g] in &paths.left {
            for &[k, l] in &paths.right[e] {
                let labels = [a, b, c, d, e, f, g, k, l];
                let lhs = self.pentagon_lhs(labels);
                let rhs = self.pentagon_rhs(labels, &fuse[b][c]);
                if lhs == rhs {
                    continue;
                }
                defects.push(PentagonDefect { labels, lhs, rhs });
                if stop_at_first {
                    return true;
                }
            }
        }
        false
    }

    fn pentagon_lhs(&self, [a, b, c, d, e, f, g, k, l]: [usize; 9]) -> K {
        match (
            self.f.entry([f, c, d, e], g, l),
            self.f.entry([a, b, l, e], f, k),
        ) {
            (Some(x), Some(y)) => x.mul(y),
            _ => K::zero(),
        }
    }

    fn pentagon_rhs(&self, [a, b, c, d, e, f, g, k, l]: [usize; 9], h_labels: &[usize]) -> K {
        let mut total = K::zero();
        for &h in h_labels {
            if let (Some(x), Some(y), Some(z)) = (
                self.f.entry([a, b, c, g], f, h),
                self.f.entry([a, h, d, e], g, k),
                self.f.entry([b, c, d, k], h, l),
            ) {
                total = total.add(&x.mul(y).mul(z));
            }
        }
        total
    }

    /// The labels `(a, b, c, d)` of every F-symbol with a unit leg whose entry is not `1`.
    fn unit_defect_labels(&self) -> impl Iterator<Item = [usize; 4]> + '_ {
        let unit = self.ring.unit();
        self.f
            .blocks
            .iter()
            .filter(move |([a, b, c, _], _)| *a == unit || *b == unit || *c == unit)
            .filter(|(_, block)| {
                !(block.matrix.shape() == (1, 1)
                    && block.matrix.get_ref(0, 0).is_ok_and(|x| *x == K::one()))
            })
            .map(|(labels, _)| *labels)
    }

    pub fn unit_defects(&self) -> Vec<[usize; 4]> {
        self.unit_defect_labels().collect()
    }

    /// Checks invertibility of the F-blocks, the unit laws and the pentagon equation; the
    /// error names the first failure.
    pub fn validate(&self) -> Result<(), FusionError> {
        if let Some(labels) = self.singular.first() {
            return Err(FusionError::Category(CategoryDefect::BlockSingular {
                labels: *labels,
            }));
        }
        if let Some(labels) = self.unit_defect_labels().next() {
            return Err(FusionError::Category(CategoryDefect::UnitLaw { labels }));
        }
        if let Some(defect) = self.first_pentagon_defect() {
            return Err(FusionError::Category(CategoryDefect::Pentagon {
                labels: defect.labels,
            }));
        }
        Ok(())
    }

    /// Whether every F-matrix is unitary: `F F^dagger = 1`, with the field's conjugation.
    pub fn is_unitary(&self) -> Result<bool, FusionError> {
        for block in self.f.blocks.values() {
            if !involution::is_unitary(&block.matrix).map_err(FusionError::from)? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// The category obtained by the gauge `u`:
    /// `F' = u^{ab}_e u^{ec}_d / (u^{bc}_f u^{af}_d) F`.
    pub fn gauge_transform(&self, gauge: &Gauge<K>) -> Result<Self, FusionError> {
        let mut blocks = BTreeMap::new();
        for (&[a, b, c, d], block) in &self.f.blocks {
            let matrix = BasicMatrix::try_from_fn_result(
                block.rows.len(),
                block.cols.len(),
                |i, j| -> Result<K, FusionError> {
                    let e = block.rows[i];
                    let f = block.cols[j];
                    let numerator = gauge.require([a, b, e])?.mul(gauge.require([e, c, d])?);
                    let denominator = gauge.require([b, c, f])?.mul(gauge.require([a, f, d])?);
                    let factor = core_number_theory::scalar::divide(&numerator, &denominator)
                        .map_err(FusionError::from)?;
                    Ok(factor.mul(block.matrix.get_ref(i, j)?))
                },
            )?;
            blocks.insert(
                [a, b, c, d],
                FBlock {
                    rows: block.rows.clone(),
                    cols: block.cols.clone(),
                    matrix,
                },
            );
        }
        Self::new(
            self.ring.clone(),
            FSymbols {
                rank: self.f.rank,
                blocks,
            },
        )
    }

    /// The gauge (nontrivial only on the unit vertices) under which every F-symbol with a
    /// unit leg becomes `1`, or an error when the data admit none.
    ///
    /// With `r_x = u^{x0}_x` and `l_x = u^{0x}_x` the conditions read
    /// `F^{0bc}_d[b,d] = l_d / l_b`, `F^{a0c}_d[a,c] = l_c / r_a` and
    /// `F^{ab0}_d[d,b] = r_b / r_d`; they are solved by `r_b = F^{b* b 0}_0[0,b]` and
    /// `l_b = 1 / F^{0 b b*}_0[b,0]` (normalising `l_0 = r_0 = 1`), and the result is
    /// verified, not assumed.
    fn unit_constraint(&self, labels: [usize; 4], e: usize, f: usize) -> Result<&K, FusionError> {
        self.f.entry(labels, e, f).ok_or(FusionError::Category(
            CategoryDefect::UnitNormalizationImpossible {
                labels: [labels[0], labels[1], labels[2]],
            },
        ))
    }

    fn unit_gauge_pair(&self, b: usize) -> Result<(K, K), FusionError> {
        let unit = self.ring.unit();
        let b_star = self.ring.dual(b)?;
        let right = self.unit_constraint([b_star, b, unit, unit], unit, b)?;
        let left_inverse = self.unit_constraint([unit, b, b_star, unit], b, unit)?;
        let left = core_number_theory::scalar::inverse(left_inverse).map_err(FusionError::from)?;
        Ok((right.clone(), left))
    }

    fn normalized_units_and_gauge(&self) -> Result<(Self, Gauge<K>), FusionError> {
        let unit = self.ring.unit();
        let mut gauge = Gauge::trivial(&self.ring);
        for b in (0..self.ring.rank()).filter(|&b| b != unit) {
            let (right, left) = self.unit_gauge_pair(b)?;
            gauge.replace([b, unit, b], right)?;
            gauge.replace([unit, b, b], left)?;
        }
        let normalized = self.gauge_transform(&gauge)?;
        if let Some(labels) = normalized.unit_defect_labels().next() {
            return Err(FusionError::Category(
                CategoryDefect::UnitNormalizationImpossible {
                    labels: [labels[0], labels[1], labels[2]],
                },
            ));
        }
        Ok((normalized, gauge))
    }

    pub fn unit_normalizing_gauge(&self) -> Result<Gauge<K>, FusionError> {
        self.normalized_units_and_gauge().map(|(_, gauge)| gauge)
    }

    /// The category in the canonical unit-normalised gauge (see
    /// [`Self::unit_normalizing_gauge`]).
    pub fn normalize_units(&self) -> Result<Self, FusionError> {
        self.normalized_units_and_gauge()
            .map(|(normalized, _)| normalized)
    }

    /// `[F^{a a* a}_a]_{00} [F^{a* a a*}_{a*}]_{00}`, the gauge-invariant (for gauges that
    /// fix the unit vertices) product whose inverse is `d_a d_{a*}`.
    pub fn dimension_invariant(&self, a: usize) -> Result<K, FusionError> {
        let unit = self.ring.unit();
        let a_star = self.ring.dual(a)?;
        let first = self.f.entry([a, a_star, a, a], unit, unit);
        let second = self.f.entry([a_star, a, a_star, a_star], unit, unit);
        match (first, second) {
            (Some(x), Some(y)) => Ok(x.mul(y)),
            _ => Err(FusionError::Category(CategoryDefect::BlockMissing {
                labels: [a, a_star, a, a],
            })),
        }
    }

    fn verify_dimension_entry(&self, a: usize, dims: &[K]) -> Result<(), FusionError> {
        if dims[a].is_zero() {
            return Err(dimension_error(DimensionDefect::Zero { label: a }));
        }
        if dims[a] != dims[self.ring.dual(a)?] {
            return Err(dimension_error(DimensionDefect::NotSpherical { label: a }));
        }
        Ok(())
    }

    fn verify_character_pair(&self, [a, b]: [usize; 2], dims: &[K]) -> Result<(), FusionError> {
        let mut total = K::zero();
        for (c, dimension) in dims.iter().enumerate() {
            let multiplicity = self.ring.n(a, b, c);
            if multiplicity == 0 {
                continue;
            }
            let n = core_number_theory::scalar::from_i64::<K>(
                i64::try_from(multiplicity).map_err(|_| FusionError::Overflow {
                    context: "embedding a fusion coefficient",
                })?,
            );
            total = total.add(&n.mul(dimension));
        }
        if dims[a].mul(&dims[b]) != total {
            return Err(dimension_error(DimensionDefect::NotCharacter { a, b }));
        }
        Ok(())
    }

    fn verify_dimension_invariant(&self, a: usize, dims: &[K]) -> Result<(), FusionError> {
        let product = dims[a]
            .mul(&dims[self.ring.dual(a)?])
            .mul(&self.dimension_invariant(a)?);
        if product != K::one() {
            return Err(dimension_error(DimensionDefect::DisagreesWithF {
                label: a,
            }));
        }
        Ok(())
    }

    /// Checks a proposed dimension vector: `d_0 = 1`, `d_a != 0`, `d_{a*} = d_a`,
    /// `d_a d_b = sum_c N_{ab}^c d_c`, and `d_a d_{a*} [F^{a a* a}_a]_{00}
    /// [F^{a* a a*}_{a*}]_{00} = 1` (valid in a unit-normalised gauge).
    ///
    /// Positivity is not decided here: a dimension vector that passes is a character of
    /// the ring consistent with the F-symbols, and the same data admit the Galois
    /// conjugate vectors (for Ising, `d_sigma = -sqrt 2`) as pivotal structures.
    pub fn verify_dimensions(&self, dims: &[K]) -> Result<(), FusionError> {
        let rank = self.ring.rank();
        if dims.len() != rank {
            return Err(dimension_error(DimensionDefect::Count {
                expected: rank,
                got: dims.len(),
            }));
        }
        if dims[self.ring.unit()] != K::one() {
            return Err(dimension_error(DimensionDefect::UnitNotOne));
        }
        for a in 0..rank {
            self.verify_dimension_entry(a, dims)?;
        }
        for labels in label_pairs(rank) {
            self.verify_character_pair(labels, dims)?;
        }
        for a in 0..rank {
            self.verify_dimension_invariant(a, dims)?;
        }
        Ok(())
    }

    /// The Frobenius-Schur indicator `nu_a = d_a [F^{aaa}_a]_{00}` of a self-dual object
    /// (`+1` or `-1`), given dimensions that passed [`Self::verify_dimensions`]; `None` for
    /// an object that is not self-dual (its indicator is not gauge invariant).
    pub fn frobenius_schur_indicator(
        &self,
        a: usize,
        dims: &[K],
    ) -> Result<Option<i8>, FusionError> {
        if self.ring.dual(a)? != a {
            return Ok(None);
        }
        let unit = self.ring.unit();
        let entry = self
            .f
            .entry([a, a, a, a], unit, unit)
            .ok_or(FusionError::Category(CategoryDefect::BlockMissing {
                labels: [a, a, a, a],
            }))?;
        let d = dims.get(a).ok_or(FusionError::Label {
            label: a,
            rank: dims.len(),
        })?;
        let value = d.mul(entry);
        if value == K::one() {
            Ok(Some(1))
        } else if value == K::one().neg() {
            Ok(Some(-1))
        } else {
            Err(FusionError::Category(CategoryDefect::Dimensions(
                DimensionDefect::FrobeniusSchurNotSign { label: a },
            )))
        }
    }
}

// Origin: engine/crates_rs/core_fusion_categories/src/fusion_category.rs
// Claim: urn:core:crates_rs:core-fusion-categories:fusion-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::{rq, Rational};

    #[test]
    fn generic_category_admission_bounds_storage_and_law_work_before_coefficients() {
        let ring = FusionRing::pointed(&[8], None).unwrap();
        let calls = std::cell::Cell::new(0usize);
        let tight = OperationLimits {
            max_elements: 1 << 20,
            max_scalar_ops: 1,
        };
        assert!(matches!(
            FSymbols::<Rational>::from_fn_with_limits(&ring, tight, |_, _, _| {
                calls.set(calls.get() + 1);
                rq(1, 1)
            }),
            Err(FusionError::Budget { .. })
        ));
        assert_eq!(calls.get(), 0);
        let tight = OperationLimits {
            max_elements: 1,
            max_scalar_ops: 1 << 28,
        };
        assert!(matches!(
            FSymbols::<Rational>::from_fn_with_limits(&ring, tight, |_, _, _| {
                calls.set(calls.get() + 1);
                rq(1, 1)
            }),
            Err(FusionError::Budget {
                what: "fusion category symbol storage",
                ..
            })
        ));
        assert_eq!(calls.get(), 0);
        let symbols = FSymbols::<Rational>::trivial(&ring).unwrap();
        assert!(matches!(
            FusionCategory::new_with_limits(ring.clone(), symbols.clone(), tight),
            Err(FusionError::Budget { .. })
        ));
        let category = FusionCategory::new(ring, symbols).unwrap();
        assert!(category.validate().is_ok());
        assert!(category.pentagon_defects().is_empty());
    }

    #[test]
    fn pointed_rank32_replays_every_pentagon_without_dense_label_products() {
        let ring = FusionRing::pointed(&[32], None).unwrap();
        let category =
            FusionCategory::<Rational>::validated(ring.clone(), FSymbols::trivial(&ring).unwrap())
                .unwrap();
        assert_eq!(category.ring().rank(), 32);
        assert!(category.first_pentagon_defect().is_none());
    }

    fn z2_category(omega: i64) -> Result<FusionCategory<Rational>, FusionError> {
        let ring = FusionRing::z_n(2)?;
        // The only nontrivial block is F^{111}_1; every other block is 1.
        let f = FSymbols::from_fn(&ring, |labels, _, _| {
            if labels == [1, 1, 1, 1] {
                rq(omega, 1)
            } else {
                rq(1, 1)
            }
        })?;
        FusionCategory::new(ring, f)
    }

    #[test]
    fn the_two_associators_of_z2_satisfy_the_pentagon_and_nothing_else_does() {
        // omega = +1 (trivial) and omega = -1 (the semion associator) are the two classes of
        // 3-cocycles on Z_2; the pentagon forces omega^2 = 1.
        for omega in [1, -1] {
            let category = z2_category(omega).unwrap();
            assert_eq!(category.pentagon_defects(), vec![], "omega = {omega}");
            assert!(category.validate().is_ok());
        }
        let bad = z2_category(2).unwrap();
        let defects = bad.pentagon_defects();
        assert!(!defects.is_empty());
        assert!(matches!(
            bad.validate(),
            Err(FusionError::Category(CategoryDefect::Pentagon { .. }))
        ));
        // A singular F-block is recorded at construction (so the pentagon can still be
        // checked on it) and refused by validation.
        let zero_entry = z2_category(0).unwrap();
        assert_eq!(zero_entry.singular_blocks(), &[[1, 1, 1, 1]]);
        assert!(
            matches!(
                zero_entry.validate(),
                Err(FusionError::Category(CategoryDefect::BlockSingular {
                    labels: [1, 1, 1, 1]
                }))
            ),
            "a singular F-block is refused by validation"
        );
    }

    #[test]
    fn the_pentagon_defect_reports_the_first_tuple_and_both_sides() {
        // F^{111}_1 = w, every other F-symbol 1. For each (a, b, c, d) the labels
        // e = a+b+c+d, f = a+b, g = a+b+c, l = c+d, k = b+c+d, h = b+c (mod 2) are forced, and
        // the two sides are powers of w. They differ only at (1,1,1,1): the left side is 1
        // and the right side is w^2 (two factors F^{111}_1), so the single defect is
        // pentagon(1,1,1,1; e=0, f=0, g=1, k=1, l=0).
        let bad = z2_category(3).unwrap();
        let defects = bad.pentagon_defects();
        assert_eq!(defects.len(), 1);
        let first = bad.first_pentagon_defect().unwrap();
        assert_eq!(defects[0], first);
        assert_eq!(first.labels, [1, 1, 1, 1, 0, 0, 1, 1, 0]);
        assert_eq!(first.lhs, rq(1, 1));
        assert_eq!(first.rhs, rq(9, 1));
        // The reported equation reads the perturbed entry F^{111}_1[0,0]; the equations
        // that hold do not need to.
        assert!(first.involves([1, 1, 1, 1], 0, 0));
        assert!(!first.involves([0, 0, 0, 0], 0, 0));
    }

    #[test]
    fn unit_laws_are_checked_and_repaired_by_the_canonical_gauge() {
        let category = z2_category(-1).unwrap();
        assert_eq!(category.unit_defects(), Vec::<[usize; 4]>::new());
        // Scale the unit vertices: u^{10}_1 = 2, u^{01}_1 = 3. The F-symbols with a unit leg
        // are no longer 1, but the pentagon still holds (gauge covariance).
        let gauge = Gauge::trivial(category.ring())
            .with([1, 0, 1], rq(2, 1))
            .unwrap()
            .with([0, 1, 1], rq(3, 1))
            .unwrap();
        let scaled = category.gauge_transform(&gauge).unwrap();
        assert!(!scaled.unit_defects().is_empty());
        assert_eq!(scaled.pentagon_defects(), vec![]);
        let repaired = scaled.normalize_units().unwrap();
        assert_eq!(repaired.unit_defects(), Vec::<[usize; 4]>::new());
        assert_eq!(repaired.pentagon_defects(), vec![]);
        assert_eq!(
            repaired, category,
            "the normalised gauge is the original one"
        );
    }

    #[test]
    fn the_gauge_transform_follows_its_defining_formula_entrywise() {
        let category = z2_category(-1).unwrap();
        let gauge = Gauge::from_fn(category.ring(), |[a, b, c]| {
            rq(1 + 2 * a as i64 + 5 * b as i64 + 7 * c as i64, 3)
        })
        .unwrap();
        let transformed = category.gauge_transform(&gauge).unwrap();
        let g = |a, b, c| gauge.get([a, b, c]).unwrap().clone();
        // F^{111}_1 has e = f = 0: (u^{11}_0 u^{01}_1)/(u^{11}_0 u^{10}_1) F.
        let expected = (g(1, 1, 0) * g(0, 1, 1)) / (g(1, 1, 0) * g(1, 0, 1)) * rq(-1, 1);
        assert_eq!(transformed.f_entry([1, 1, 1, 1], 0, 0), expected);
        // The inverse gauge undoes it exactly.
        let back = transformed
            .gauge_transform(&gauge.inverse().unwrap())
            .unwrap();
        assert_eq!(back, category);
    }

    #[test]
    fn structural_defects_in_f_data_are_refused_with_typed_errors() {
        let ring = FusionRing::z_n(2).unwrap();
        // A ring with multiplicity cannot carry scalar F-symbols.
        let s3 = FusionRing::rep_s3().unwrap();
        assert!(FSymbols::<Rational>::trivial(&s3).is_err());
        let fusion = FSymbols::from_fn(&ring, |_, _, _| rq(1, 1)).unwrap();
        // Wrong rank.
        let other = FusionRing::z_n(3).unwrap();
        assert!(matches!(
            FusionCategory::new(other, fusion.clone()),
            Err(FusionError::ListLength { .. })
        ));
        // Entry replacement refuses non-admissible indices and missing blocks.
        assert!(fusion.with_entry([0, 0, 0, 1], 0, 0, rq(1, 1)).is_err());
        assert!(fusion.with_entry([1, 1, 1, 1], 1, 1, rq(1, 1)).is_err());
        let replaced = fusion.with_entry([1, 1, 1, 1], 0, 0, rq(-1, 1)).unwrap();
        assert_eq!(replaced.entry([1, 1, 1, 1], 0, 0), Some(&rq(-1, 1)));
        assert_eq!(replaced.entry([1, 1, 1, 1], 1, 0), None);
    }

    #[test]
    fn dimensions_are_checked_against_the_ring_and_the_f_symbols() {
        let semion = z2_category(-1).unwrap();
        let ones = vec![rq(1, 1), rq(1, 1)];
        assert_eq!(semion.verify_dimensions(&ones), Ok(()));
        // The semion has Frobenius-Schur indicator -1 (F^{sss}_s = -1, d = 1).
        assert_eq!(semion.frobenius_schur_indicator(1, &ones), Ok(Some(-1)));
        assert_eq!(semion.frobenius_schur_indicator(0, &ones), Ok(Some(1)));
        let trivial = z2_category(1).unwrap();
        assert_eq!(trivial.frobenius_schur_indicator(1, &ones), Ok(Some(1)));
        // Wrong dimension data.
        let defect = |dims: Vec<Rational>| match semion.verify_dimensions(&dims) {
            Err(FusionError::Category(CategoryDefect::Dimensions(defect))) => defect,
            other => panic!("expected a dimension defect, got {other:?}"),
        };
        assert_eq!(
            defect(vec![rq(1, 1)]),
            DimensionDefect::Count {
                expected: 2,
                got: 1
            }
        );
        assert_eq!(
            defect(vec![rq(2, 1), rq(1, 1)]),
            DimensionDefect::UnitNotOne
        );
        assert_eq!(
            defect(vec![rq(1, 1), rq(0, 1)]),
            DimensionDefect::Zero { label: 1 }
        );
        // d_s = 2 is not a character of the Z_2 ring: d_s^2 = 4 but N_{ss}^0 d_0 = 1.
        assert_eq!(
            defect(vec![rq(1, 1), rq(2, 1)]),
            DimensionDefect::NotCharacter { a: 1, b: 1 }
        );
        // d_s = -1 is the other character of Z_2 (the Galois-conjugate pivotal structure):
        // it passes, and it flips the Frobenius-Schur indicator of the semion.
        let flipped = vec![rq(1, 1), rq(-1, 1)];
        assert_eq!(semion.verify_dimensions(&flipped), Ok(()));
        assert_eq!(semion.frobenius_schur_indicator(1, &flipped), Ok(Some(1)));
        // An F-block scaled away from the normalisation disagrees with d = 1 (F = 2 is not a
        // pentagon solution, but the dimension check reads only the F-symbols it needs).
        let scaled = z2_category(2).unwrap();
        match scaled.verify_dimensions(&ones) {
            Err(FusionError::Category(CategoryDefect::Dimensions(defect))) => {
                assert_eq!(defect, DimensionDefect::DisagreesWithF { label: 1 });
            }
            other => panic!("expected a disagreement with the F-symbols, got {other:?}"),
        }
        // A Frobenius-Schur value that is not a sign is refused.
        assert_eq!(
            scaled.frobenius_schur_indicator(1, &ones),
            Err(FusionError::Category(CategoryDefect::Dimensions(
                DimensionDefect::FrobeniusSchurNotSign { label: 1 }
            )))
        );
    }
}
