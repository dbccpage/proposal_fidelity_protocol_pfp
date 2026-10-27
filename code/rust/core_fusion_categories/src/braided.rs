// Braided and ribbon fusion categories: R-symbols, the hexagon equations, twists,
// the ribbon (balancing) relation, and braid-group representations on fusion spaces.
//
// Conventions. `R^{ab}_c` (for `N_{ab}^c = 1`) is the braiding `a x b -> b x a` on the
// fusion channel `c`. With the F-symbol convention of `fusion_category`, the two
// hexagon equations are
//
// `R^{ec}_d [(F^{cab}_d)^{-1}]_{eg} = sum_f [F^{abc}_d]_{ef} R^{bc}_f [(F^{acb}_d)^{-1}]_{fg} R^{ac}_g`
//
// and the mirror form obtained by `R^{xy}_z -> (R^{yx}_z)^{-1}`. The quantum
// dimensions `d_a` of a ribbon category define the twist
// `theta_a = (1/d_a) sum_c N_{aa}^c d_c R^{aa}_c` (the partial trace of the braiding of
// `a` with itself), and the balancing relation reads
// `R^{ab}_c R^{ba}_c = theta_c / (theta_a theta_b)`.
//
// The braid group `B_n` acts on the fusion space `Hom(total, a_1 x ... x a_n)`, with
// basis the left-associated fusion paths `x_1 = a_1, x_j in x_{j-1} x a_j, x_n = total`.
// `sigma_1` is diagonal with entries `R^{a_1 a_2}_{x_2}`; for `i >= 2` the generator
// `sigma_i` changes `x_i` and acts, in coordinates, as the transpose of
// `F diag(R) F'^{-1}` (the blocks `F^{p a_i a_{i+1}}_r` and `F^{p a_{i+1} a_i}_r` with
// `p = x_{i-1}`, `r = x_{i+1}`).
//
// What is computed: both hexagon equations exactly over `K` (every violated index
// tuple), twists, the ribbon relation, gauge transformations, complex conjugation and
// the reversed braiding, and the braid-group generators as exact matrices. What is not:
// any claim about the image of the braid group being dense (see `braid_group` for the
// exact finite-closure statement), and positivity of dimensions.
//
// AuthorityEffect: None.
use std::cmp::Ordering;
use std::collections::BTreeMap;

use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Signed;
use thiserror::Error;

use crate::braid_group::{BraidRelationDefect, DEFAULT_BRAID_LIMITS};
use crate::error::FusionError;
use crate::fusion_category::{CategoryDefect, FBlock, FSymbols, FusionCategory, Gauge};
use crate::fusion_ring::FusionRing;
use crate::scalar::{sign_of, FusionScalar};
use linear_algebra::backend::basic_matrix::OperationLimits;
use linear_algebra::exact_field::matrix;
use core_number_theory::algebraic_real::{IsolatedRoot, RealAlgebraic};
use core_number_theory::quadratic::QuadraticNumber;

/// Largest dimension of a fusion space the braid-group routines will build.
pub const MAX_FUSION_SPACE: usize = 1 << 16;

/// Bounds on materialized fusion paths, distinct from exact path counting.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FusionSpaceLimits {
    pub max_strands: usize,
    pub max_paths: usize,
    pub max_path_labels: usize,
    pub max_extension_work: usize,
}

impl Default for FusionSpaceLimits {
    fn default() -> Self {
        Self {
            max_strands: 1024,
            max_paths: MAX_FUSION_SPACE,
            max_path_labels: 1 << 20,
            max_extension_work: 1 << 26,
        }
    }
}

fn charge_braid(what: &'static str, requested: u128, limit: usize) -> Result<(), FusionError> {
    if requested > limit as u128 {
        return Err(FusionError::Budget {
            what,
            requested,
            limit: limit as u128,
        });
    }
    Ok(())
}

fn braid_product_work(
    dimension: usize,
    products: usize,
    limits: OperationLimits,
) -> Result<(), FusionError> {
    let work = (dimension as u128)
        .checked_pow(3)
        .and_then(|work| work.checked_mul(2 * products as u128))
        .ok_or(FusionError::Overflow {
            context: "braid product work",
        })?;
    charge_braid("braid product scalar work", work, limits.max_scalar_ops)
}

/// A law of a braided or ribbon fusion category that fails.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Error)]
pub enum BraidedDefect {
    /// `N_{ab}^c != N_{ba}^c`: the fusion ring is not commutative.
    #[error("labels {left} and {right} do not fuse commutatively")]
    NotCommutative { left: usize, right: usize },
    /// A vertex `N_{ab}^c = 1` without an R-symbol.
    #[error("missing R-symbol at {labels:?}")]
    RMissing { labels: [usize; 3] },
    /// An R-symbol at something that is not a vertex.
    #[error("unexpected R-symbol at {labels:?}")]
    RUnexpected { labels: [usize; 3] },
    /// An R-symbol equal to zero.
    #[error("R-symbol at {labels:?} is zero")]
    RZero { labels: [usize; 3] },
    /// A violated hexagon equation at `(a, b, c, d, e, g)`.
    #[error("hexagon equation (mirror form: {mirror}) violated at {labels:?}")]
    Hexagon { mirror: bool, labels: [usize; 6] },
    /// The balancing relation `R^{ab}_c R^{ba}_c = theta_c / (theta_a theta_b)` fails.
    #[error("balancing relation fails at {labels:?}")]
    Ribbon { labels: [usize; 3] },
    /// `theta_a != theta_{a*}`.
    #[error("the twist of label {label} differs from the twist of its dual")]
    TwistNotDualInvariant { label: usize },
    /// `theta_0 != 1`.
    #[error("the twist of the unit is not 1")]
    TwistOfUnit,
    /// `theta_a` is zero (so the twist is not invertible).
    #[error("the twist of label {label} is zero")]
    TwistZero { label: usize },
}

/// R-symbols of a multiplicity-free commutative fusion ring: one nonzero scalar
/// `R^{ab}_c` per vertex `N_{ab}^c = 1`.
#[derive(Debug, Clone, PartialEq)]
pub struct RSymbols<K> {
    rank: usize,
    r: BTreeMap<[usize; 3], K>,
}

impl<K: FusionScalar> RSymbols<K> {
    fn collect_r_symbols_for_pair(
        ring: &FusionRing,
        a: usize,
        b: usize,
        value: &mut impl FnMut([usize; 3]) -> K,
        r: &mut BTreeMap<[usize; 3], K>,
    ) -> Result<(), FusionError> {
        for c in 0..ring.rank() {
            if ring.n(a, b, c) == 0 {
                continue;
            }
            let entry = value([a, b, c]);
            if entry.is_zero() {
                return Err(FusionError::Braided(BraidedDefect::RZero {
                    labels: [a, b, c],
                }));
            }
            r.insert([a, b, c], entry);
        }
        Ok(())
    }

    /// R-symbols from a function of the vertex; a zero value is refused.
    pub fn from_fn(
        ring: &FusionRing,
        mut value: impl FnMut([usize; 3]) -> K,
    ) -> Result<Self, FusionError> {
        let n = ring.rank();
        let mut r = BTreeMap::new();
        for a in 0..n {
            for b in 0..n {
                Self::collect_r_symbols_for_pair(ring, a, b, &mut value, &mut r)?;
            }
        }
        Ok(Self { rank: n, r })
    }

    /// `R^{ab}_c`, if `(a, b; c)` is a vertex.
    pub fn get(&self, labels: [usize; 3]) -> Option<&K> {
        self.r.get(&labels)
    }

    /// All entries in index order.
    pub fn entries(&self) -> impl Iterator<Item = (&[usize; 3], &K)> {
        self.r.iter()
    }

    /// A copy with one vertex's R-symbol replaced; a non-vertex or zero is refused.
    pub fn with_entry(&self, labels: [usize; 3], value: K) -> Result<Self, FusionError> {
        if value.is_zero() {
            return Err(FusionError::Braided(BraidedDefect::RZero { labels }));
        }
        if !self.r.contains_key(&labels) {
            return Err(FusionError::Braided(BraidedDefect::RMissing { labels }));
        }
        let mut r = self.r.clone();
        r.insert(labels, value);
        Ok(Self { rank: self.rank, r })
    }
}

/// Which of the two hexagon equations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum HexagonForm {
    /// With `R^{xy}_z`.
    Direct,
    /// With `R^{xy}_z` replaced by `(R^{yx}_z)^{-1}`.
    Mirror,
}

/// A violated hexagon equation with both sides.
#[derive(Debug, Clone, PartialEq)]
pub struct HexagonDefect<K> {
    /// Which equation.
    pub form: HexagonForm,
    /// `(a, b, c, d, e, g)`.
    pub labels: [usize; 6],
    /// `R^{ec}_d [(F^{cab}_d)^{-1}]_{eg}` (or its mirror).
    pub lhs: K,
    /// `sum_f [F^{abc}_d]_{ef} R^{bc}_f [(F^{acb}_d)^{-1}]_{fg} R^{ac}_g` (or its mirror).
    pub rhs: K,
}

impl<K> HexagonDefect<K> {
    /// Whether the R-symbol `R^{xy}_z` is read by this equation (for some summation label
    /// `f` on the right-hand side).
    pub fn reads_r(&self, [x, y, z]: [usize; 3]) -> bool {
        let [a, b, c, d, e, g] = self.labels;
        match self.form {
            HexagonForm::Direct => {
                [x, y, z] == [e, c, d] || [x, y] == [b, c] || [x, y, z] == [a, c, g]
            }
            HexagonForm::Mirror => {
                [x, y, z] == [c, e, d] || [x, y] == [c, b] || [x, y, z] == [c, a, g]
            }
        }
    }
}

/// A basis of `Hom(total, a_1 x ... x a_n)`: the left-associated fusion paths
/// `x_1 = a_1, x_j in x_{j-1} x a_j, x_n = total`, recorded as `(x_2, ..., x_{n-1})`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FusionSpace {
    word: Vec<usize>,
    total: usize,
    basis: Vec<Vec<usize>>,
    extension_work: usize,
}

impl FusionSpace {
    /// The word `(a_1, ..., a_n)`.
    pub fn word(&self) -> &[usize] {
        &self.word
    }

    /// The total charge.
    pub fn total(&self) -> usize {
        self.total
    }

    /// The number of basis paths.
    pub fn dimension(&self) -> usize {
        self.basis.len()
    }

    /// The basis paths `(x_2, ..., x_{n-1})`, lexicographically ascending.
    pub fn basis(&self) -> &[Vec<usize>] {
        &self.basis
    }

    /// The position of a path in the basis.
    pub fn index_of(&self, path: &[usize]) -> Option<usize> {
        self.basis.binary_search_by(|p| p.as_slice().cmp(path)).ok()
    }

    /// `x_j` (1-based `j` in `1..=n`) of a path.
    fn charge(&self, path: &[usize], j: usize) -> Option<usize> {
        let n = self.word.len();
        if j == 0 || j > n {
            None
        } else if j == 1 {
            self.word.first().copied()
        } else if j == n {
            Some(self.total)
        } else {
            path.get(j - 2).copied()
        }
    }
}

/// A multiplicity-free braided fusion category: a fusion category with R-symbols on a
/// commutative ring.
///
/// Construction checks structure (commutative ring, one nonzero R-symbol per vertex); the
/// hexagon equations are checked by [`Self::hexagon_defects`] and [`Self::validate`].
#[derive(Debug, Clone, PartialEq)]
pub struct BraidedFusionCategory<K> {
    category: FusionCategory<K>,
    r: RSymbols<K>,
}

impl<K: FusionScalar> BraidedFusionCategory<K> {
    /// A braided category from a category and R-symbols (structure checked, hexagons not).
    fn check_ring_commutativity(ring: &FusionRing) -> Result<(), FusionError> {
        let n = ring.rank();
        for left in 0..n {
            for right in left + 1..n {
                if (0..n).any(|c| ring.n(left, right, c) != ring.n(right, left, c)) {
                    return Err(FusionError::Braided(BraidedDefect::NotCommutative {
                        left,
                        right,
                    }));
                }
            }
        }
        Ok(())
    }

    fn validate_r_entry(
        entry: Option<&K>,
        is_allowed: bool,
        labels: [usize; 3],
    ) -> Result<(), FusionError> {
        match (entry, is_allowed) {
            (None, true) => Err(FusionError::Braided(BraidedDefect::RMissing { labels })),
            (Some(_), false) => Err(FusionError::Braided(BraidedDefect::RUnexpected { labels })),
            (Some(e), true) if e.is_zero() => {
                Err(FusionError::Braided(BraidedDefect::RZero { labels }))
            }
            _ => Ok(()),
        }
    }

    fn validate_r_symbols(ring: &FusionRing, r: &RSymbols<K>) -> Result<(), FusionError> {
        let n = ring.rank();
        if r.rank != n {
            return Err(FusionError::ListLength {
                what: "R-symbol labels",
                expected: n,
                got: r.rank,
            });
        }
        for a in 0..n {
            for b in 0..n {
                for c in 0..n {
                    let labels = [a, b, c];
                    Self::validate_r_entry(r.get(labels), ring.n(a, b, c) > 0, labels)?;
                }
            }
        }
        Ok(())
    }

    pub fn new(category: FusionCategory<K>, r: RSymbols<K>) -> Result<Self, FusionError> {
        let ring = category.ring();
        Self::check_ring_commutativity(ring)?;
        if let Some(labels) = category.singular_blocks().first() {
            return Err(FusionError::Category(CategoryDefect::BlockSingular {
                labels: *labels,
            }));
        }
        Self::validate_r_symbols(ring, &r)?;
        Ok(Self { category, r })
    }

    /// A braided category whose F-symbols satisfy the unit laws and pentagon and whose
    /// R-symbols satisfy both hexagon equations.
    pub fn validated(category: FusionCategory<K>, r: RSymbols<K>) -> Result<Self, FusionError> {
        let braided = Self::new(category, r)?;
        braided.validate()?;
        Ok(braided)
    }

    /// The underlying fusion category.
    pub fn category(&self) -> &FusionCategory<K> {
        &self.category
    }

    /// The fusion ring.
    pub fn ring(&self) -> &FusionRing {
        self.category.ring()
    }

    /// The R-symbols.
    pub fn r_symbols(&self) -> &RSymbols<K> {
        &self.r
    }

    /// `R^{ab}_c` (zero when `(a, b; c)` is not a vertex).
    pub fn r_entry(&self, labels: [usize; 3]) -> K {
        self.r.get(labels).cloned().unwrap_or_else(K::zero)
    }

    /// The R-symbol of the equation's form: `R^{xy}_z` or `(R^{yx}_z)^{-1}`.
    fn r_in_form(&self, form: HexagonForm, [x, y, z]: [usize; 3]) -> Option<K> {
        match form {
            HexagonForm::Direct => self.r.get([x, y, z]).cloned(),
            HexagonForm::Mirror => self.r.get([y, x, z])?.try_inv(),
        }
    }

    /// Every violated hexagon equation of the given form, exactly, in index order.
    pub fn hexagon_defects(&self, form: HexagonForm) -> Vec<HexagonDefect<K>> {
        self.hexagon_scan(form, false)
    }

    /// The first violated hexagon equation of the given form, if any.
    pub fn first_hexagon_defect(&self, form: HexagonForm) -> Option<HexagonDefect<K>> {
        self.hexagon_scan(form, true).into_iter().next()
    }

    fn scan_hexagon_block(
        &self,
        form: HexagonForm,
        [a, b, c, d]: [usize; 4],
        block: &FBlock<K>,
        targets: &[usize],
        stop_at_first: bool,
        defects: &mut Vec<HexagonDefect<K>>,
    ) -> bool {
        for &e in block.rows() {
            for &g in targets {
                let lhs = self.hexagon_lhs(form, [a, b, c, d], e, g);
                let rhs = self.hexagon_rhs(form, [a, b, c, d], e, g, block.cols());
                if lhs == rhs {
                    continue;
                }
                defects.push(HexagonDefect {
                    form,
                    labels: [a, b, c, d, e, g],
                    lhs,
                    rhs,
                });
                if stop_at_first {
                    return true;
                }
            }
        }
        false
    }

    fn scan_hexagon_for_c(
        &self,
        form: HexagonForm,
        a: usize,
        b: usize,
        c: usize,
        n: usize,
        stop_at_first: bool,
        defects: &mut Vec<HexagonDefect<K>>,
    ) -> bool {
        let ring = self.ring();
        for d in 0..n {
            let Some(block) = self.category.f_symbols().block([a, b, c, d]) else {
                continue;
            };
            let targets: Vec<usize> = (0..n)
                .filter(|&g| ring.n(a, c, g) > 0 && ring.n(g, b, d) > 0)
                .collect();
            if self.scan_hexagon_block(form, [a, b, c, d], block, &targets, stop_at_first, defects) {
                return true;
            }
        }
        false
    }

    fn scan_hexagon_for_b(
        &self,
        form: HexagonForm,
        a: usize,
        b: usize,
        n: usize,
        stop_at_first: bool,
        defects: &mut Vec<HexagonDefect<K>>,
    ) -> bool {
        for c in 0..n {
            if self.scan_hexagon_for_c(form, a, b, c, n, stop_at_first, defects) {
                return true;
            }
        }
        false
    }

    fn hexagon_scan(&self, form: HexagonForm, stop_at_first: bool) -> Vec<HexagonDefect<K>> {
        let ring = self.ring();
        let n = ring.rank();
        let mut defects = Vec::new();
        for a in 0..n {
            for b in 0..n {
                if self.scan_hexagon_for_b(form, a, b, n, stop_at_first, &mut defects) {
                    return defects;
                }
            }
        }
        defects
    }

    fn hexagon_lhs(&self, form: HexagonForm, [a, b, c, d]: [usize; 4], e: usize, g: usize) -> K {
        match self.r_in_form(form, [e, c, d]) {
            Some(r) => r.mul(&self.category.f_inverse_entry([c, a, b, d], e, g)),
            None => K::zero(),
        }
    }

    fn hexagon_rhs(
        &self,
        form: HexagonForm,
        [a, b, c, d]: [usize; 4],
        e: usize,
        g: usize,
        middle: &[usize],
    ) -> K {
        let Some(r_ac_g) = self.r_in_form(form, [a, c, g]) else {
            return K::zero();
        };
        let mut total = K::zero();
        for &f in middle {
            let Some(r_bc_f) = self.r_in_form(form, [b, c, f]) else {
                continue;
            };
            let term = self
                .category
                .f_entry([a, b, c, d], e, f)
                .mul(&r_bc_f)
                .mul(&self.category.f_inverse_entry([a, c, b, d], f, g))
                .mul(&r_ac_g);
            total = total.add(&term);
        }
        total
    }

    /// Checks the unit laws, the pentagon and both hexagon equations; the error names the
    /// first failure.
    pub fn validate(&self) -> Result<(), FusionError> {
        self.category.validate()?;
        for (form, mirror) in [(HexagonForm::Direct, false), (HexagonForm::Mirror, true)] {
            if let Some(defect) = self.first_hexagon_defect(form) {
                return Err(FusionError::Braided(BraidedDefect::Hexagon {
                    mirror,
                    labels: defect.labels,
                }));
            }
        }
        Ok(())
    }

    /// `R^{ab}_c R^{ba}_c`, the monodromy scalar of the vertex.
    pub fn monodromy(&self, [a, b, c]: [usize; 3]) -> Option<K> {
        Some(self.r.get([a, b, c])?.mul(self.r.get([b, a, c])?))
    }

    /// Whether every monodromy is `1` (a symmetric braiding; such a category is never
    /// modular unless trivial).
    pub fn is_symmetric(&self) -> bool {
        self.r
            .entries()
            .all(|(&[a, b, c], _)| self.monodromy([a, b, c]).is_some_and(|m| m == K::one()))
    }

    /// The category obtained by the gauge `u`: `F` as in
    /// [`FusionCategory::gauge_transform`] and `R'^{ab}_c = (u^{ab}_c / u^{ba}_c) R^{ab}_c`.
    pub fn gauge_transform(&self, gauge: &Gauge<K>) -> Result<Self, FusionError> {
        let category = self.category.gauge_transform(gauge)?;
        let mut entries = BTreeMap::new();
        for (&[a, b, c], value) in self.r.entries() {
            let forward = gauge.get([a, b, c]).ok_or(FusionError::Category(
                CategoryDefect::GaugeMissing { labels: [a, b, c] },
            ))?;
            let backward = gauge.get([b, a, c]).ok_or(FusionError::Category(
                CategoryDefect::GaugeMissing { labels: [b, a, c] },
            ))?;
            entries.insert(
                [a, b, c],
                core_number_theory::scalar::divide(forward, backward)
                    .map_err(FusionError::from)?
                    .mul(value),
            );
        }
        Self::new(
            category,
            RSymbols {
                rank: self.r.rank,
                r: entries,
            },
        )
    }

    /// The complex conjugate category (every F- and R-symbol conjugated): its twists and
    /// central charge are the conjugates and the negative.
    pub fn complex_conjugate(&self) -> Result<Self, FusionError> {
        let ring = self.ring().clone();
        let f = FSymbols::from_fn(&ring, |labels, e, f| {
            self.category.f_symbols().entry(labels, e, f).map_or_else(
                K::zero,
                linear_algebra::exact_field::involution::Involution::conjugate,
            )
        })?;
        let category = FusionCategory::new(ring.clone(), f)?;
        let r = RSymbols::from_fn(&ring, |labels| self.r_entry(labels).conjugate())?;
        Self::new(category, r)
    }

    /// The reversed-braiding category: `R'^{ab}_c = (R^{ba}_c)^{-1}` with the same F-symbols.
    pub fn reverse_braiding(&self) -> Result<Self, FusionError> {
        let ring = self.ring().clone();
        let mut entries = BTreeMap::new();
        for (&[a, b, c], _) in self.r.entries() {
            let opposite =
                self.r
                    .get([b, a, c])
                    .ok_or(FusionError::Braided(BraidedDefect::RMissing {
                        labels: [b, a, c],
                    }))?;
            entries.insert(
                [a, b, c],
                core_number_theory::scalar::inverse(opposite).map_err(FusionError::from)?,
            );
        }
        Self::new(
            FusionCategory::new(ring, self.category.f_symbols().clone())?,
            RSymbols {
                rank: self.r.rank,
                r: entries,
            },
        )
    }

    // ------------------------------------------------------------------
    // Braid-group representations
    // ------------------------------------------------------------------
    /// The fusion space `Hom(total, w_1 x ... x w_n)` with its path basis.
    pub fn fusion_space(&self, word: &[usize], total: usize) -> Result<FusionSpace, FusionError> {
        self.fusion_space_with_limits(word, total, FusionSpaceLimits::default())
    }

    /// [`Self::fusion_space`] with declared path-storage and extension-work limits.
    /// Every extension is charged before cloning or appending its path.
    fn validate_fusion_labels(word: &[usize], total: usize, rank: usize) -> Result<(), FusionError> {
        for &label in word.iter().chain(std::iter::once(&total)) {
            if label >= rank {
                return Err(FusionError::Label { label, rank });
            }
        }
        Ok(())
    }

    fn extend_fusion_path(
        path: &[usize],
        c: usize,
        limits: &FusionSpaceLimits,
        work: &mut u128,
        next: &mut Vec<(Vec<usize>, usize)>,
    ) -> Result<(), FusionError> {
        let count = next.len() as u128 + 1;
        charge_braid("fusion space dimension", count, limits.max_paths)?;
        charge_braid(
            "fusion path labels",
            count * (path.len() as u128 + 1),
            limits.max_path_labels,
        )?;
        *work = work
            .checked_add(path.len() as u128 + 1)
            .ok_or(FusionError::Overflow {
                context: "fusion path extension work",
            })?;
        charge_braid(
            "fusion path extension work",
            *work,
            limits.max_extension_work,
        )?;
        let mut extended = path.to_vec();
        extended.push(c);
        next.push((extended, c));
        Ok(())
    }

    fn extend_partial_paths(
        partial: &[(Vec<usize>, usize)],
        label: usize,
        ring: &FusionRing,
        limits: &FusionSpaceLimits,
        work: &mut u128,
    ) -> Result<Vec<(Vec<usize>, usize)>, FusionError> {
        let rank = ring.rank();
        let mut next = Vec::new();
        for (path, x) in partial {
            *work = work
                .checked_add(rank as u128)
                .ok_or(FusionError::Overflow {
                    context: "fusion path extension work",
                })?;
            charge_braid(
                "fusion path extension work",
                *work,
                limits.max_extension_work,
            )?;
            for c in 0..rank {
                if ring.n(*x, label, c) > 0 {
                    Self::extend_fusion_path(path, c, limits, work, &mut next)?;
                }
            }
        }
        Ok(next)
    }

    fn build_fusion_basis(
        word: &[usize],
        total: usize,
        ring: &FusionRing,
        limits: &FusionSpaceLimits,
        work: &mut u128,
    ) -> Result<Vec<Vec<usize>>, FusionError> {
        let n = word.len();
        let mut basis: Vec<Vec<usize>> = Vec::new();
        match n {
            0 => {
                if total == ring.unit() {
                    basis.push(Vec::new());
                }
            }
            1 => {
                if word.first() == Some(&total) {
                    basis.push(Vec::new());
                }
            }
            _ => {
                // x_1 = w_1; extend the path one fused charge at a time, in ascending order
                // (which keeps the paths lexicographically sorted).
                let first = word.first().copied().unwrap_or(0);
                let mut partial: Vec<(Vec<usize>, usize)> = vec![(Vec::new(), first)];
                for step in 2..n {
                    let label = word.get(step - 1).copied().unwrap_or(0);
                    partial = Self::extend_partial_paths(&partial, label, ring, limits, work)?;
                }
                let last = word.get(n - 1).copied().unwrap_or(0);
                for (path, x) in partial {
                    if ring.n(x, last, total) > 0 {
                        basis.push(path);
                    }
                }
            }
        }
        Ok(basis)
    }

    pub fn fusion_space_with_limits(
        &self,
        word: &[usize],
        total: usize,
        limits: FusionSpaceLimits,
    ) -> Result<FusionSpace, FusionError> {
        charge_braid(
            "materialized fusion strands",
            word.len() as u128,
            limits.max_strands,
        )?;
        let ring = self.ring();
        Self::validate_fusion_labels(word, total, ring.rank())?;
        let n = word.len();
        let mut work = n as u128;
        charge_braid(
            "fusion path extension work",
            work,
            limits.max_extension_work,
        )?;
        let mut basis = Self::build_fusion_basis(word, total, ring, &limits, &mut work)?;
        charge_braid(
            "fusion space dimension",
            basis.len() as u128,
            limits.max_paths,
        )?;
        charge_braid(
            "fusion path labels",
            basis.len() as u128 * n.saturating_sub(2) as u128 + n as u128,
            limits.max_path_labels,
        )?;
        basis.sort();
        Ok(FusionSpace {
            word: word.to_vec(),
            total,
            basis,
            extension_work: usize::try_from(work).map_err(|_| FusionError::Overflow {
                context: "fusion path work",
            })?,
        })
    }

    /// The generator `sigma_i` (`1 <= i <= n - 1`, exchanging strands `i` and `i + 1`) as a
    /// matrix from the space of `space.word()` to the space of the word with those two
    /// letters exchanged. Columns are source basis paths, rows target basis paths.
    pub fn braid_matrix(
        &self,
        space: &FusionSpace,
        i: usize,
    ) -> Result<(FusionSpace, BasicMatrix<K>), FusionError> {
        self.braid_matrix_with_limits(space, i, DEFAULT_BRAID_LIMITS)
    }

    /// [`Self::braid_matrix`] with an allocation and coefficient-work budget.
    pub fn braid_matrix_with_limits(
        &self,
        space: &FusionSpace,
        i: usize,
        limits: OperationLimits,
    ) -> Result<(FusionSpace, BasicMatrix<K>), FusionError> {
        let mut path_work = FusionSpaceLimits::default().max_extension_work;
        self.braid_matrix_using_path_budget(space, i, limits, &mut path_work)
    }

    fn fill_braid_matrix_col_i1(
        &self,
        space: &FusionSpace,
        target: &FusionSpace,
        path: &[usize],
        column: usize,
        a: usize,
        b: usize,
        n: usize,
        matrix: &mut BasicMatrix<K>,
    ) -> Result<(), FusionError> {
        let x2 = space
            .charge(path, 2)
            .ok_or(FusionError::Label { label: 2, rank: n })?;
        let row = target.index_of(path).ok_or(FusionError::Inconsistent {
            context: "a fusion path of the word is missing from the exchanged word",
        })?;
        let entry = self.r.get([a, b, x2]).ok_or(FusionError::Braided(
            BraidedDefect::RMissing { labels: [a, b, x2] },
        ))?;
        matrix.set(row, column, entry.clone())?;
        Ok(())
    }

    fn compute_braid_general_entry(
        source_block: &FBlock<K>,
        target_inverse: &FBlock<K>,
        r_symbols: &RSymbols<K>,
        e: usize,
        e_prime: usize,
        a: usize,
        b: usize,
    ) -> K {
        let mut entry = K::zero();
        for &f in source_block.cols() {
            let Some(f_e_f) = source_block.entry(e, f) else {
                continue;
            };
            let Some(r_f) = r_symbols.get([a, b, f]) else {
                continue;
            };
            let Some(inv) = target_inverse.entry(f, e_prime) else {
                continue;
            };
            entry = entry.add(&f_e_f.mul(r_f).mul(inv));
        }
        entry
    }

    fn get_braid_blocks(
        &self,
        space: &FusionSpace,
        path: &[usize],
        i: usize,
        a: usize,
        b: usize,
        n: usize,
    ) -> Result<(usize, &FBlock<K>, &FBlock<K>), FusionError> {
        let missing = |labels: [usize; 4]| FusionError::Category(CategoryDefect::BlockMissing { labels });
        let p = space.charge(path, i - 1).ok_or(FusionError::Label {
            label: i - 1,
            rank: n,
        })?;
        let e = space
            .charge(path, i)
            .ok_or(FusionError::Label { label: i, rank: n })?;
        let r = space.charge(path, i + 1).ok_or(FusionError::Label {
            label: i + 1,
            rank: n,
        })?;
        let source_block = self
            .category
            .f_symbols()
            .block([p, a, b, r])
            .ok_or_else(|| missing([p, a, b, r]))?;
        let target_inverse = self
            .category
            .f_inverse_block([p, b, a, r])
            .ok_or_else(|| missing([p, b, a, r]))?;
        Ok((e, source_block, target_inverse))
    }

    fn fill_braid_matrix_col_general(
        &self,
        space: &FusionSpace,
        target: &FusionSpace,
        path: &[usize],
        column: usize,
        i: usize,
        a: usize,
        b: usize,
        n: usize,
        matrix: &mut BasicMatrix<K>,
    ) -> Result<(), FusionError> {
        let (e, source_block, target_inverse) =
            self.get_braid_blocks(space, path, i, a, b, n)?;
        for &e_prime in target_inverse.cols() {
            let entry = Self::compute_braid_general_entry(
                source_block,
                target_inverse,
                &self.r,
                e,
                e_prime,
                a,
                b,
            );
            let mut new_path = path.to_vec();
            if let Some(slot) = new_path.get_mut(i - 2) {
                *slot = e_prime;
            }
            let row = target
                .index_of(&new_path)
                .ok_or(FusionError::Inconsistent {
                    context: "an exchanged fusion path is missing from the exchanged word",
                })?;
            matrix.set(row, column, entry)?;
        }
        Ok(())
    }

    fn prepare_braid_target(
        &self,
        space: &FusionSpace,
        i: usize,
        path_work: &mut usize,
    ) -> Result<FusionSpace, FusionError> {
        let source = self.fusion_space_with_limits(
            space.word(),
            space.total(),
            FusionSpaceLimits {
                max_extension_work: *path_work,
                ..FusionSpaceLimits::default()
            },
        )?;
        *path_work -= source.extension_work;
        if source != *space {
            return Err(FusionError::Inconsistent {
                context: "fusion space does not belong to this fusion ring",
            });
        }
        let mut swapped = space.word.clone();
        swapped.swap(i - 1, i);
        let target = self.fusion_space_with_limits(
            &swapped,
            space.total,
            FusionSpaceLimits {
                max_extension_work: *path_work,
                ..FusionSpaceLimits::default()
            },
        )?;
        *path_work -= target.extension_work;
        Ok(target)
    }

    fn populate_braid_matrix_columns(
        &self,
        space: &FusionSpace,
        target: &FusionSpace,
        i: usize,
        a: usize,
        b: usize,
        n: usize,
        matrix: &mut BasicMatrix<K>,
    ) -> Result<(), FusionError> {
        for (column, path) in space.basis.iter().enumerate() {
            if i == 1 {
                self.fill_braid_matrix_col_i1(space, target, path, column, a, b, n, matrix)?;
            } else {
                self.fill_braid_matrix_col_general(space, target, path, column, i, a, b, n, matrix)?;
            }
        }
        Ok(())
    }

    fn braid_matrix_using_path_budget(
        &self,
        space: &FusionSpace,
        i: usize,
        limits: OperationLimits,
        path_work: &mut usize,
    ) -> Result<(FusionSpace, BasicMatrix<K>), FusionError> {
        let n = space.word.len();
        if i == 0 || i >= n {
            return Err(FusionError::Label {
                label: i,
                rank: n.saturating_sub(1),
            });
        }
        let target = self.prepare_braid_target(space, i, path_work)?;
        let a = space.word.get(i - 1).copied().unwrap_or(0);
        let b = space.word.get(i).copied().unwrap_or(0);
        charge_braid(
            "braid matrix entries",
            target.dimension() as u128 * space.dimension() as u128,
            limits.max_elements,
        )?;
        charge_braid(
            "braid coefficient scalar work",
            3 * space.dimension() as u128 * (self.ring().rank() as u128).pow(2),
            limits.max_scalar_ops,
        )?;
        let mut matrix =
            matrix::zeros_with_limits::<K>(target.dimension(), space.dimension(), limits)?;
        self.populate_braid_matrix_columns(space, &target, i, a, b, n, &mut matrix)?;
        Ok((target, matrix))
    }

    /// The defining relations of the braid groupoid on the fusion space of `word`: for every
    /// `i`, `sigma_i sigma_{i+1} sigma_i = sigma_{i+1} sigma_i sigma_{i+1}` as maps from the
    /// space of `word` to the space of `word` with the first and third letters of the window
    /// exchanged, and `sigma_j sigma_i = sigma_i sigma_j` for `|i - j| >= 2`. Generator
    /// numbers in the defects are 0-based. For words of distinct letters these are the
    /// pentagon-and-hexagon consistency conditions seen through the braid group.
    fn compute_braid_side_matrix(
        &self,
        space: &FusionSpace,
        indices: [usize; 3],
        path_work: &mut usize,
    ) -> Result<(FusionSpace, BasicMatrix<K>), FusionError> {
        let (s1, m1) = self.braid_matrix_using_path_budget(
            space,
            indices[0],
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let (s2, m2) = self.braid_matrix_using_path_budget(
            &s1,
            indices[1],
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let (s3, m3) = self.braid_matrix_using_path_budget(
            &s2,
            indices[2],
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let prod = matrix::multiply_with_limits(
            &m3,
            &matrix::multiply_with_limits(&m2, &m1, DEFAULT_BRAID_LIMITS)?,
            DEFAULT_BRAID_LIMITS,
        )
        .map_err(FusionError::from)?;
        Ok((s3, prod))
    }

    fn check_braid_step(
        &self,
        space: &FusionSpace,
        i: usize,
        path_work: &mut usize,
    ) -> Result<Option<BraidRelationDefect>, FusionError> {
        let (a3, left) = self.compute_braid_side_matrix(space, [i, i + 1, i], path_work)?;
        let (b3, right) = self.compute_braid_side_matrix(space, [i + 1, i, i + 1], path_work)?;
        if a3.word() != b3.word() {
            return Err(FusionError::Inconsistent {
                context: "the two sides of a braid relation end in different words",
            });
        }
        if left != right {
            Ok(Some(BraidRelationDefect::Braid { i: i - 1 }))
        } else {
            Ok(None)
        }
    }

    fn check_far_commutation_step(
        &self,
        space: &FusionSpace,
        i: usize,
        j: usize,
        path_work: &mut usize,
    ) -> Result<Option<BraidRelationDefect>, FusionError> {
        let (x1, p1) = self.braid_matrix_using_path_budget(
            space,
            i,
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let (x2, p2) = self.braid_matrix_using_path_budget(
            &x1,
            j,
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let (y1, q1) = self.braid_matrix_using_path_budget(
            space,
            j,
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        let (y2, q2) = self.braid_matrix_using_path_budget(
            &y1,
            i,
            DEFAULT_BRAID_LIMITS,
            path_work,
        )?;
        if x2.word() != y2.word() {
            return Err(FusionError::Inconsistent {
                context: "the two sides of a commutation relation end in different words",
            });
        }
        if matrix::multiply_with_limits(&p2, &p1, DEFAULT_BRAID_LIMITS)?
            != matrix::multiply_with_limits(&q2, &q1, DEFAULT_BRAID_LIMITS)?
        {
            Ok(Some(BraidRelationDefect::Far { i: i - 1, j: j - 1 }))
        } else {
            Ok(None)
        }
    }

    fn charge_braid_word_budget(
        ring_rank: usize,
        n: usize,
        dim: usize,
    ) -> Result<(), FusionError> {
        let pairs = n
            .saturating_sub(1)
            .checked_pow(2)
            .ok_or(FusionError::Overflow {
                context: "braid relation count",
            })?;
        let products = pairs
            .checked_mul(2)
            .and_then(|count| count.checked_add(4 * n.saturating_sub(2)))
            .ok_or(FusionError::Overflow {
                context: "braid relation count",
            })?;
        braid_product_work(dim, products, DEFAULT_BRAID_LIMITS)?;
        let d = dim as u128;
        let coefficient_work =
            (6 * n as u128 + 2 * pairs as u128) * 3 * d * (ring_rank as u128).pow(2);
        charge_braid(
            "braid relation aggregate scalar work",
            2 * products as u128 * d.pow(3) + coefficient_work,
            DEFAULT_BRAID_LIMITS.max_scalar_ops,
        )
    }

    fn collect_far_commutation_defects(
        &self,
        space: &FusionSpace,
        n: usize,
        path_work: &mut usize,
        defects: &mut Vec<BraidRelationDefect>,
    ) -> Result<(), FusionError> {
        for i in 1..n {
            for j in (i + 2)..n {
                if let Some(defect) = self.check_far_commutation_step(space, i, j, path_work)? {
                    defects.push(defect);
                }
            }
        }
        Ok(())
    }

    fn collect_braid_defects(
        &self,
        space: &FusionSpace,
        n: usize,
        path_work: &mut usize,
        defects: &mut Vec<BraidRelationDefect>,
    ) -> Result<(), FusionError> {
        for i in 1..n.saturating_sub(1) {
            if let Some(defect) = self.check_braid_step(space, i, path_work)? {
                defects.push(defect);
            }
        }
        Ok(())
    }

    pub fn braid_relation_defects_on_word(
        &self,
        word: &[usize],
        total: usize,
    ) -> Result<Vec<BraidRelationDefect>, FusionError> {
        let space = self.fusion_space(word, total)?;
        let n = word.len();
        let mut path_work = FusionSpaceLimits::default().max_extension_work - space.extension_work;
        Self::charge_braid_word_budget(self.ring().rank(), n, space.dimension())?;
        let mut defects = Vec::new();
        self.collect_braid_defects(&space, n, &mut path_work, &mut defects)?;
        self.collect_far_commutation_defects(&space, n, &mut path_work, &mut defects)?;
        Ok(defects)
    }

    /// The braid-group generators `sigma_1, ..., sigma_{n-1}` of `n` copies of `a` fusing to
    /// `total`, as square matrices on the fusion space (every generator preserves the word).
    pub fn braid_generators(
        &self,
        a: usize,
        n: usize,
        total: usize,
    ) -> Result<Vec<BasicMatrix<K>>, FusionError> {
        self.braid_generators_with_limits(a, n, total, DEFAULT_BRAID_LIMITS)
    }

    /// [`Self::braid_generators`] with aggregate storage and assembly limits.
    pub fn braid_generators_with_limits(
        &self,
        a: usize,
        n: usize,
        total: usize,
        limits: OperationLimits,
    ) -> Result<Vec<BasicMatrix<K>>, FusionError> {
        charge_braid(
            "materialized fusion strands",
            n as u128,
            FusionSpaceLimits::default().max_strands,
        )?;
        let word = vec![a; n];
        let space = self.fusion_space(&word, total)?;
        let mut path_work = FusionSpaceLimits::default().max_extension_work - space.extension_work;
        let generators = n.saturating_sub(1) as u128;
        let dimension = space.dimension() as u128;
        charge_braid(
            "braid generator entries",
            generators * dimension * dimension,
            limits.max_elements,
        )?;
        let assembly = generators
            * dimension
            * (3 * (self.ring().rank() as u128).pow(2) + 3 * (n as u128).pow(2));
        charge_braid(
            "braid generator assembly work",
            assembly,
            limits.max_scalar_ops,
        )?;
        (1..n)
            .map(|i| {
                self.braid_matrix_using_path_budget(&space, i, limits, &mut path_work)
                    .map(|(_, matrix)| matrix)
            })
            .collect()
    }
}

/// A ribbon (spherical braided) fusion category: a braided fusion category with quantum
/// dimensions and the twists they define, verified against each other.
///
/// Construction verifies: the pentagon and both hexagons, the dimension data against the
/// ring and the F-symbols (see [`FusionCategory::verify_dimensions`]), and the balancing
/// relation `R^{ab}_c R^{ba}_c = theta_c / (theta_a theta_b)` with `theta_a = (1/d_a)
/// sum_c N_{aa}^c d_c R^{aa}_c`, together with `theta_{a*} = theta_a` and `theta_0 = 1`.
#[derive(Debug, Clone, PartialEq)]
pub struct RibbonFusionCategory<K> {
    braided: BraidedFusionCategory<K>,
    dimensions: Vec<K>,
    twists: Vec<K>,
}

impl<K: FusionScalar> RibbonFusionCategory<K> {
    /// The twist `theta_a` of each object computed from the R-symbols and dimensions.
    pub fn compute_twists(
        braided: &BraidedFusionCategory<K>,
        dimensions: &[K],
    ) -> Result<Vec<K>, FusionError> {
        let ring = braided.ring();
        let n = ring.rank();
        if dimensions.len() != n {
            return Err(FusionError::ListLength {
                what: "dimensions",
                expected: n,
                got: dimensions.len(),
            });
        }
        let mut twists = Vec::with_capacity(n);
        for a in 0..n {
            let mut total = K::zero();
            for (c, d_c) in dimensions.iter().enumerate() {
                if ring.n(a, a, c) > 0 {
                    total = total.add(&d_c.mul(&braided.r_entry([a, a, c])));
                }
            }
            let d_a = dimensions
                .get(a)
                .ok_or(FusionError::Label { label: a, rank: n })?;
            twists
                .push(core_number_theory::scalar::divide(&total, d_a).map_err(FusionError::from)?);
        }
        Ok(twists)
    }

    /// Builds and verifies a ribbon category from a braided category and dimensions.
    fn verify_twists_dual_invariance(
        ring: &FusionRing,
        twists: &[K],
    ) -> Result<(), FusionError> {
        let n = ring.rank();
        for a in 0..n {
            let twist = twists
                .get(a)
                .ok_or(FusionError::Label { label: a, rank: n })?;
            if twist.is_zero() {
                return Err(FusionError::Braided(BraidedDefect::TwistZero { label: a }));
            }
            let dual = ring.dual(a)?;
            if twists.get(dual) != Some(twist) {
                return Err(FusionError::Braided(BraidedDefect::TwistNotDualInvariant {
                    label: a,
                }));
            }
        }
        Ok(())
    }

    fn verify_ribbon_relations(
        braided: &BraidedFusionCategory<K>,
        twists: &[K],
    ) -> Result<(), FusionError> {
        for (&[a, b, c], _) in braided.r.entries() {
            let (Some(ta), Some(tb), Some(tc)) = (twists.get(a), twists.get(b), twists.get(c))
            else {
                continue;
            };
            let expected =
                core_number_theory::scalar::divide(tc, &ta.mul(tb)).map_err(FusionError::from)?;
            if braided.monodromy([a, b, c]) != Some(expected) {
                return Err(FusionError::Braided(BraidedDefect::Ribbon {
                    labels: [a, b, c],
                }));
            }
        }
        Ok(())
    }

    pub fn try_new(
        braided: BraidedFusionCategory<K>,
        dimensions: Vec<K>,
    ) -> Result<Self, FusionError> {
        braided.validate()?;
        braided.category.verify_dimensions(&dimensions)?;
        let twists = Self::compute_twists(&braided, &dimensions)?;
        let ring = braided.ring();
        if twists.first() != Some(&K::one()) {
            return Err(FusionError::Braided(BraidedDefect::TwistOfUnit));
        }
        Self::verify_twists_dual_invariance(ring, &twists)?;
        Self::verify_ribbon_relations(&braided, &twists)?;
        Ok(Self {
            braided,
            dimensions,
            twists,
        })
    }

    /// The braided fusion category.
    pub fn braided(&self) -> &BraidedFusionCategory<K> {
        &self.braided
    }

    /// The fusion category.
    pub fn category(&self) -> &FusionCategory<K> {
        self.braided.category()
    }

    /// The fusion ring.
    pub fn ring(&self) -> &FusionRing {
        self.braided.ring()
    }

    /// The quantum dimensions `d_a`.
    pub fn dimensions(&self) -> &[K] {
        &self.dimensions
    }

    /// The twists `theta_a`.
    pub fn twists(&self) -> &[K] {
        &self.twists
    }

    /// `d_a`.
    pub fn dimension(&self, a: usize) -> Result<&K, FusionError> {
        self.dimensions.get(a).ok_or(FusionError::Label {
            label: a,
            rank: self.dimensions.len(),
        })
    }

    /// `theta_a`.
    pub fn twist(&self, a: usize) -> Result<&K, FusionError> {
        self.twists.get(a).ok_or(FusionError::Label {
            label: a,
            rank: self.twists.len(),
        })
    }

    /// The global dimension squared `D^2 = sum_a d_a^2`, exactly in `K`.
    pub fn global_dimension_squared(&self) -> K {
        self.dimensions
            .iter()
            .fold(K::zero(), |acc, d| acc.add(&d.mul(d)))
    }

    /// `p_+ = sum_a d_a^2 theta_a`, the Gauss sum of the twists.
    pub fn gauss_sum(&self) -> K {
        self.dimensions
            .iter()
            .zip(&self.twists)
            .fold(K::zero(), |acc, (d, theta)| acc.add(&d.mul(d).mul(theta)))
    }

    fn check_quadratic_fp_dimension(
        d: &K,
        surd: &QuadraticNumber,
    ) -> Result<bool, FusionError> {
        let annihilates = core_number_theory::scalar::evaluate_integer_polynomial(
            &surd.minimal_polynomial(),
            d,
        )
        .map_err(FusionError::from)?
        .is_zero();
        let offset = d.sub(&K::from_rational(surd.rational_part()));
        let wanted = if surd.sqrt_part().is_positive() {
            Ordering::Greater
        } else {
            Ordering::Less
        };
        Ok(annihilates && sign_of(&offset)? == wanted)
    }

    fn check_root_fp_dimension(
        d: &K,
        root: &IsolatedRoot,
    ) -> Result<bool, FusionError> {
        let interval = root.isolating_interval()?;
        let annihilates = core_number_theory::scalar::evaluate_integer_polynomial(
            root.polynomial(),
            d,
        )
        .map_err(FusionError::from)?
        .is_zero();
        let above_lower =
            sign_of(&d.sub(&K::from_rational(interval.lo())))? == Ordering::Greater;
        let at_most_upper =
            sign_of(&K::from_rational(interval.hi()).sub(d))? != Ordering::Less;
        Ok(annihilates && above_lower && at_most_upper)
    }

    fn check_fp_dimension_agreement(d: &K, alg: RealAlgebraic) -> Result<bool, FusionError> {
        match alg {
            RealAlgebraic::Rational(q) => Ok(*d == K::from_rational(&q)),
            RealAlgebraic::Quadratic(surd) => Self::check_quadratic_fp_dimension(d, &surd),
            RealAlgebraic::Root(root) => Self::check_root_fp_dimension(d, &root),
        }
    }

    /// Whether every quantum dimension `d_a` is exactly the Frobenius-Perron dimension of
    /// its object (the category is pseudo-unitary as far as dimensions go).
    ///
    /// Decided exactly: `d_a` must be a root of the characteristic polynomial of `N_a`
    /// (checked in the field), and it must be the root the ring selects: equal to the
    /// rational value, or the larger root of the quadratic surd (the sign of `d_a - a` equal to
    /// the sign of `b` for `a + b sqrt(d)`), or inside the rational isolating interval
    /// `(lower, upper]` that contains exactly one root. The signs are decided by
    /// [`FusionScalar::real_sign`]; a scalar type that cannot decide them gives
    /// [`FusionError::SignUndecided`].
    pub fn dimensions_are_frobenius_perron(&self) -> Result<bool, FusionError> {
        let ring = self.ring();
        for a in 0..ring.rank() {
            let d = self.dimension(a)?;
            let alg = ring.frobenius_perron_dimension(a)?;
            if !Self::check_fp_dimension_agreement(d, alg)? {
                return Ok(false);
            }
        }
        Ok(true)
    }

    /// The complex conjugate ribbon category (conjugate symbols, conjugate dimensions and
    /// twists).
    pub fn complex_conjugate(&self) -> Result<Self, FusionError> {
        let dimensions = self
            .dimensions
            .iter()
            .map(linear_algebra::exact_field::involution::Involution::conjugate)
            .collect();
        Self::try_new(self.braided.complex_conjugate()?, dimensions)
    }

    /// The braid-group generators, see [`BraidedFusionCategory::braid_generators`].
    pub fn braid_generators(
        &self,
        a: usize,
        n: usize,
        total: usize,
    ) -> Result<Vec<BasicMatrix<K>>, FusionError> {
        self.braided.braid_generators(a, n, total)
    }

    /// The full twist `(sigma_1 ... sigma_{n-1})^n` of `n` copies of `a` fusing to `total`;
    /// by the ribbon structure it is the scalar `theta_total / theta_a^n`.
    pub fn full_twist(
        &self,
        a: usize,
        n: usize,
        total: usize,
    ) -> Result<BasicMatrix<K>, FusionError> {
        charge_braid(
            "materialized fusion strands",
            n as u128,
            FusionSpaceLimits::default().max_strands,
        )?;
        let space = self.braided.fusion_space(&vec![a; n], total)?;
        let dimension = space.dimension();
        let power_products = 2 * (usize::BITS - n.leading_zeros()) as usize;
        braid_product_work(
            dimension,
            n.saturating_sub(1) + power_products,
            DEFAULT_BRAID_LIMITS,
        )?;
        let d = dimension as u128;
        charge_braid(
            "full twist aggregate scalar work",
            2 * (n.saturating_sub(1) + power_products) as u128 * d.pow(3)
                + 3 * n.saturating_sub(1) as u128 * d * (self.ring().rank() as u128).pow(2),
            DEFAULT_BRAID_LIMITS.max_scalar_ops,
        )?;
        let mut product = matrix::identity_with_limits::<K>(dimension, DEFAULT_BRAID_LIMITS)?;
        for generator in self.braided.braid_generators(a, n, total)? {
            product = matrix::multiply_with_limits(&product, &generator, DEFAULT_BRAID_LIMITS)?;
        }
        matrix::power_with_limits(
            &product,
            u64::try_from(n).map_err(|_| FusionError::Overflow {
                context: "the number of strands",
            })?,
            DEFAULT_BRAID_LIMITS,
        )
        .map_err(FusionError::from)
    }

    /// The scalar `theta_total / theta_a^n` by which [`Self::full_twist`] acts.
    pub fn full_twist_scalar(&self, a: usize, n: usize, total: usize) -> Result<K, FusionError> {
        let theta_a = self.twist(a)?;
        let theta_total = self.twist(total)?;
        let power = core_number_theory::scalar::power(
            theta_a,
            i64::try_from(n).map_err(|_| FusionError::Overflow {
                context: "the number of strands",
            })?,
        )
        .map_err(FusionError::from)?;
        core_number_theory::scalar::divide(theta_total, &power).map_err(FusionError::from)
    }
}

// Origin: engine/crates_rs/core_fusion_categories/src/braided.rs
// Claim: urn:core:crates_rs:core-fusion-categories:braided:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod resource_tests {
    use super::*;
    use core_number_theory::cyclotomic_field::Cyclotomic;

    #[test]
    fn empty_sectors_charge_intermediate_paths_across_generator_materialization() {
        let model = crate::catalog::ising::<Cyclotomic<16>>().unwrap();
        let space = model.braided().fusion_space(&vec![1; 32], 1).unwrap();
        assert_eq!(space.dimension(), 0);
        // Even though sigma^32 cannot fuse to sigma, its intermediate path
        // carrier is large. Replaying every generator still consumes that work.
        assert!(matches!(
            model.braid_generators(1, 32, 1),
            Err(FusionError::Budget {
                what: "fusion path extension work",
                ..
            })
        ));
    }

    #[test]
    fn braid_materialization_refuses_oversized_dense_and_path_carriers() {
        let model = crate::catalog::ising::<Cyclotomic<16>>().unwrap();
        let braided = model.braided();
        let space = braided.fusion_space(&vec![1; 24], 0).unwrap();
        assert_eq!(space.dimension(), 2048);
        assert!(matches!(
            braided.braid_matrix(&space, 1),
            Err(FusionError::Budget {
                what: "braid matrix entries",
                ..
            })
        ));
        assert!(matches!(
            braided.braid_generators(1, 20, 0),
            Err(FusionError::Budget {
                what: "braid generator entries",
                ..
            })
        ));
        assert!(matches!(
            braided.fusion_space(&vec![1; 34], 0),
            Err(FusionError::Budget {
                what: "fusion path labels",
                ..
            })
        ));
        assert!(matches!(
            braided.braid_generators(1, usize::MAX, 0),
            Err(FusionError::Budget {
                what: "materialized fusion strands",
                ..
            })
        ));
        assert!(matches!(
            model.full_twist(1, usize::MAX, 0),
            Err(FusionError::Budget {
                what: "materialized fusion strands",
                ..
            })
        ));
        let tight = FusionSpaceLimits {
            max_extension_work: 1,
            ..FusionSpaceLimits::default()
        };
        assert!(matches!(
            braided.fusion_space_with_limits(&[1, 1, 1], 1, tight),
            Err(FusionError::Budget {
                what: "fusion path extension work",
                ..
            })
        ));
        assert_eq!(braided.fusion_space(&[], 0).unwrap().dimension(), 1);
        assert_eq!(braided.fusion_space(&[], 1).unwrap().dimension(), 0);
        // Empty sectors remain actual zero-dimensional mathematical carriers.
        let empty = braided.fusion_space(&[0, 0], 1).unwrap();
        assert_eq!(braided.braid_matrix(&empty, 1).unwrap().1.shape(), (0, 0));
    }
}
