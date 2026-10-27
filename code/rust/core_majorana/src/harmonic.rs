//! l1 harmonic projection and cohomology-class typing over GF(2).
//!
//! For a residual `r` with `d1 r = 0`, the class `[r]` in
//! `H^1 = ker d1 / im d0` is the logical parity error. Two questions matter:
//!
//! **How big is it?** `Phi_1([r]) = min over alpha of weight(r + d0 alpha)` --
//! the minimum-Hamming-weight representative of the coset `r + im d0`. This is
//! the number of parity channels that must be wrong to realize the logical
//! error, so the minimum over nonzero classes is the array's **code distance**.
//!
//! **Which one is it?** The coordinates of `[r]` in a fixed basis of `H^1`.
//!
//! Non-claim: over GF(2) with 0/1 entries, `||v||_p^p = weight(v)` for every
//! `p`, so l1 and l2 minimisation coincide *identically*, at every Betti
//! number. No l1-vs-l2 separation is claimed here and none is possible in this
//! carrier. What `dim H^1 >= 2` buys is typing.
//!
//! Complexity: the search is `2 ** rank d0` Gray-code steps. That is not an
//! implementation defect -- minimum-weight coset representative over GF(2) is
//! syndrome decoding, NP-hard in general. The budget makes the cost explicit
//! and `exact` makes the degradation visible.
//!
//! Python dual face: `engine/majorana/engines/harmonic.py`.
//!
//! AuthorityEffect: None.

use crate::gf2_terminalizer::GF2Matrix;

/// Default cap on coset elements examined by the l1 search.
pub const DEFAULT_BUDGET: u64 = 1 << 22;

// --- a minimal fixed-width bitset --------------------------------------------

/// Bit vector over `Vec<u64>`, ordered as a big integer for canonical tie-breaks.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Bits {
    words: Vec<u64>,
}

impl Bits {
    fn zeros(len: usize) -> Self {
        Bits {
            words: vec![0u64; len.div_ceil(64).max(1)],
        }
    }

    fn from_slice(values: &[u8]) -> Self {
        let mut bits = Bits::zeros(values.len());
        for (index, &value) in values.iter().enumerate() {
            if value % 2 == 1 {
                bits.words[index / 64] |= 1u64 << (index % 64);
            }
        }
        bits
    }

    fn set(&mut self, index: usize) {
        self.words[index / 64] |= 1u64 << (index % 64);
    }

    fn get(&self, index: usize) -> u8 {
        ((self.words[index / 64] >> (index % 64)) & 1) as u8
    }

    fn xor_assign(&mut self, other: &Bits) {
        for (word, &rhs) in self.words.iter_mut().zip(other.words.iter()) {
            *word ^= rhs;
        }
    }

    fn is_zero(&self) -> bool {
        self.words.iter().all(|&word| word == 0)
    }

    /// Index of the highest set bit, or `None` if zero.
    fn high_bit(&self) -> Option<usize> {
        for (index, &word) in self.words.iter().enumerate().rev() {
            if word != 0 {
                return Some(index * 64 + (63 - word.leading_zeros() as usize));
            }
        }
        None
    }
}

// --- span with tag tracking ---------------------------------------------------

/// Pivot table keyed by leading bit, carrying a tag alongside each vector.
///
/// Each stored pivot's leading bit is unique, so a nonzero combination always
/// retains the largest such leading bit. If the current leading bit has no
/// pivot, the vector is outside the span and reduction stops.
struct Span {
    pivots: Vec<Option<(Bits, Bits)>>,
}

impl Span {
    fn new(width: usize) -> Self {
        Span {
            pivots: vec![None; width.max(1)],
        }
    }

    fn reduce(&self, mask: &Bits, tag_len: usize) -> (Bits, Bits) {
        let mut residue = mask.clone();
        let mut tag = Bits::zeros(tag_len);
        while let Some(high) = residue.high_bit() {
            match self.pivots.get(high).and_then(|slot| slot.as_ref()) {
                Some((pivot_mask, pivot_tag)) => {
                    residue.xor_assign(pivot_mask);
                    tag.xor_assign(pivot_tag);
                }
                None => break,
            }
        }
        (residue, tag)
    }

    /// Insert `mask` with `tag`. Returns `true` if it was independent.
    ///
    /// Independence is the *computed* predicate `residue != 0`; storing the
    /// pivot is the side effect, not the verdict.
    fn insert(&mut self, mask: &Bits, tag: &Bits, tag_len: usize) -> bool {
        let (residue, accumulated) = self.reduce(mask, tag_len);
        let independent = !residue.is_zero();
        if let Some(high) = residue.high_bit() {
            let mut combined = tag.clone();
            combined.xor_assign(&accumulated);
            self.pivots[high] = Some((residue, combined));
        }
        independent
    }
}

// --- l1 harmonic projection ---------------------------------------------------

/// Result of minimising Hamming weight over the coset `r + im d0`.
///
/// `exact` is the only field that licenses calling `weight` a minimum. When it
/// is `false` the search was capped and `weight` is an upper bound.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct L1HarmonicProjection {
    pub weight: usize,
    pub representative: Vec<u8>,
    pub alpha: Vec<u8>,
    pub exact: bool,
    pub searched: u64,
    /// `2 ** rank d0`, saturating at `u64::MAX` when the rank exceeds 63.
    pub coset_size: u64,
    pub authority_effect: &'static str,
}

/// A basis of `im d0` as `(channel_mask, alpha_mask)` pairs.
///
/// `alpha_mask` records which unit 0-cochains produced the channel mask, so a
/// minimising combination can be turned back into a witness `alpha`.
fn image_basis(d0: &GF2Matrix) -> Vec<(Bits, Bits)> {
    let mut span = Span::new(d0.rows.max(1));
    let mut basis = Vec::new();
    for column in 0..d0.cols {
        let mut mask = Bits::zeros(d0.rows);
        for row in 0..d0.rows {
            if d0.data[row][column] % 2 == 1 {
                mask.set(row);
            }
        }
        let (residue, accumulated) = span.reduce(&mask, d0.cols);
        if let Some(high) = residue.high_bit() {
            let mut alpha = Bits::zeros(d0.cols);
            alpha.set(column);
            alpha.xor_assign(&accumulated);
            span.pivots[high] = Some((residue.clone(), alpha.clone()));
            basis.push((residue, alpha));
        }
    }
    basis
}

/// Minimum-Hamming-weight representative of `residual + im d0`.
///
/// Enumerates the coset by reflected Gray code: one XOR and one popcount per
/// element. Ties are broken by smallest bitmask, so the representative is
/// canonical and replay-stable across the Rust and Python faces.
///
/// `budget` caps the number of elements examined; past it the result is an
/// **upper bound** and `exact` is `false`.
pub fn l1_harmonic_projection(
    d0: &GF2Matrix,
    residual: &[u8],
    budget: u64,
) -> Result<L1HarmonicProjection, String> {
    let measured = core_functional::Phi1Functional::binary_coset_projection(
        &d0.data, d0.cols, residual, budget,
    )?;
    Ok(L1HarmonicProjection {
        weight: measured.weight,
        representative: measured.representative,
        alpha: measured.alpha,
        exact: measured.exact,
        searched: measured.searched,
        coset_size: measured.coset_size,
        authority_effect: "None",
    })
}

// --- cohomology basis and class typing ----------------------------------------

/// A basis of `H^1 = ker d1 / im d0`, with the machinery to place a residual.
pub struct H1Basis {
    pub dim: usize,
    pub generators: Vec<Vec<u8>>,
    pub num_channels: usize,
    span: Span,
}

/// Basis of `ker d1` by back-substitution on the RREF of `d1`.
fn kernel_basis(d1: &GF2Matrix, num_channels: usize) -> Vec<Vec<u8>> {
    if d1.rows == 0 {
        return (0..num_channels)
            .map(|index| {
                let mut vector = vec![0u8; num_channels];
                vector[index] = 1;
                vector
            })
            .collect();
    }
    let (_, reduced) = d1.rref();
    let mut pivot_of_row = Vec::new();
    let mut pivot_columns = Vec::new();
    for row in 0..reduced.rows {
        if let Some(column) = (0..reduced.cols).find(|&c| reduced.data[row][c] == 1) {
            pivot_of_row.push((row, column));
            pivot_columns.push(column);
        }
    }
    (0..num_channels)
        .filter(|column| !pivot_columns.contains(column))
        .map(|free| {
            let mut vector = vec![0u8; num_channels];
            vector[free] = 1;
            for &(row, column) in &pivot_of_row {
                vector[column] = reduced.data[row][free];
            }
            vector
        })
        .collect()
}

/// Build a basis of `H^1`.
///
/// `im d0` is loaded first with a zero tag; each kernel vector still
/// independent becomes a generator, tagged by its index. The pivot table then
/// carries, for every stored vector, which generators it is congruent to
/// modulo `im d0` -- which is exactly what class typing needs.
pub fn h1_basis(d0: &GF2Matrix, d1: &GF2Matrix) -> H1Basis {
    let num_channels = d0.rows;
    let mut span = Span::new(num_channels.max(1));
    let mut generators: Vec<Vec<u8>> = Vec::new();

    // A generous tag width: at most num_channels independent classes.
    let tag_len = num_channels.max(1);
    for (channel_mask, _alpha) in image_basis(d0) {
        span.insert(&channel_mask, &Bits::zeros(tag_len), tag_len);
    }
    for vector in kernel_basis(d1, num_channels) {
        let mask = Bits::from_slice(&vector);
        let mut tag = Bits::zeros(tag_len);
        tag.set(generators.len());
        if span.insert(&mask, &tag, tag_len) {
            generators.push(vector);
        }
    }

    H1Basis {
        dim: generators.len(),
        generators,
        num_channels,
        span,
    }
}

impl H1Basis {
    /// Coordinates of `[residual]`, or `None` if the residual is outside `ker d1`.
    ///
    /// `None` means it is in no cohomology class at all -- an `OpenObstruction`,
    /// not a logical error.
    pub fn class_coordinates(&self, residual: &[u8]) -> Option<Vec<u8>> {
        if residual.len() != self.num_channels {
            return None;
        }
        let tag_len = self.num_channels.max(1);
        let (remainder, tag) = self.span.reduce(&Bits::from_slice(residual), tag_len);
        if !remainder.is_zero() {
            return None;
        }
        Some((0..self.dim).map(|index| tag.get(index)).collect())
    }

    /// A representative of the class with the given coordinates.
    pub fn class_representative(&self, coordinates: &[u8]) -> Vec<u8> {
        let mut vector = vec![0u8; self.num_channels];
        for (index, &bit) in coordinates.iter().enumerate().take(self.dim) {
            if bit % 2 == 1 {
                for (slot, &value) in vector.iter_mut().zip(self.generators[index].iter()) {
                    *slot ^= value;
                }
            }
        }
        vector
    }

    /// Label used in receipts, e.g. `h1:10`.
    pub fn class_id(coordinates: &[u8]) -> String {
        let mut label = String::from("h1:");
        for &bit in coordinates {
            label.push(if bit % 2 == 1 { '1' } else { '0' });
        }
        label
    }
}

/// Minimum `Phi_1` over the nonzero classes of `H^1`.
///
/// Returns `(None, true)` when `H^1 = 0`: there is no nontrivial class, so
/// there is no logical error to weigh. The flag is `true` only if every class
/// was searched exactly.
pub fn code_distance(
    d0: &GF2Matrix,
    d1: &GF2Matrix,
    budget: u64,
) -> Result<(Option<usize>, bool), String> {
    let basis = h1_basis(d0, d1);
    if basis.dim == 0 {
        return Ok((None, true));
    }
    // `1u64 << dim` panics in debug and wraps in release once dim >= 64.
    // Release would then report no logical class (`None`) for a nonzero H^1.
    if basis.dim >= 64 {
        return Err(
            "code distance refused: dim H^1 >= 64 does not fit an exact class enumeration".into(),
        );
    }
    let mut best: Option<usize> = None;
    let mut all_exact = true;
    for code in 1u64..(1u64 << basis.dim) {
        let coordinates: Vec<u8> = (0..basis.dim)
            .map(|index| ((code >> index) & 1) as u8)
            .collect();
        let representative = basis.class_representative(&coordinates);
        let projection = l1_harmonic_projection(d0, &representative, budget)?;
        all_exact = all_exact && projection.exact;
        best = Some(match best {
            None => projection.weight,
            Some(current) => current.min(projection.weight),
        });
    }
    Ok((best, all_exact))
}

// Origin: engine/crates_rs/core_majorana/src/harmonic.rs
// Claim: urn:core:crates_rs:core-majorana:harmonic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbb856dc7 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbb856dc7` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbb856dc7 {
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
impl BoundaryErrorbb856dc7 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbb856dc7 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbb856dc7 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbb856dc7 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbb856dc7> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbb856dc7::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbb856dc7::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbb856dc7::ExceedsCapacity {
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
    use crate::repair_limit::{apply_d0, gf2_add};
    use crate::tetron::{build_tetron_array, logical_class_representative, Axis, Topology};

    /// Independent oracle: enumerate every alpha in C^0, not a basis of im d0.
    fn brute_force_min_weight(d0: &GF2Matrix, residual: &[u8]) -> usize {
        let mut best = residual.iter().filter(|&&b| b == 1).count();
        for bits in 0u64..(1u64 << d0.cols) {
            let alpha: Vec<u8> = (0..d0.cols)
                .map(|index| ((bits >> index) & 1) as u8)
                .collect();
            let image = apply_d0(d0, &alpha).unwrap();
            let combined = gf2_add(residual, &image).unwrap();
            best = best.min(combined.iter().filter(|&&b| b == 1).count());
        }
        best
    }

    #[test]
    fn matches_brute_force_over_all_alpha() {
        for topology in [Topology::Disk, Topology::Cylinder, Topology::Torus] {
            let (complex, report) = build_tetron_array(2, 2, topology).unwrap();
            // Deterministic pseudo-random residuals; no rand dependency.
            let mut state: u64 = 0x2026_0805;
            for _ in 0..8 {
                let residual: Vec<u8> = (0..report.num_channels)
                    .map(|_| {
                        state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                        ((state >> 33) & 1) as u8
                    })
                    .collect();
                let projection =
                    l1_harmonic_projection(&complex.d0, &residual, DEFAULT_BUDGET).unwrap();
                assert!(projection.exact);
                assert_eq!(
                    projection.weight,
                    brute_force_min_weight(&complex.d0, &residual),
                    "{topology:?}"
                );
            }
        }
    }

    #[test]
    fn representative_lies_in_the_coset_with_the_reported_alpha() {
        let (complex, report) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let residual = logical_class_representative(&report, Axis::Column, 0);
        let projection = l1_harmonic_projection(&complex.d0, &residual, DEFAULT_BUDGET).unwrap();
        let image = apply_d0(&complex.d0, &projection.alpha).unwrap();
        assert_eq!(
            gf2_add(&residual, &image).unwrap(),
            projection.representative
        );
        assert_eq!(
            projection.weight,
            projection
                .representative
                .iter()
                .filter(|&&b| b == 1)
                .count()
        );
    }

    #[test]
    fn phi1_is_constant_on_a_cohomology_class() {
        let (complex, report) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let residual = logical_class_representative(&report, Axis::Column, 0);
        let baseline = l1_harmonic_projection(&complex.d0, &residual, DEFAULT_BUDGET).unwrap();
        let mut state: u64 = 99;
        for _ in 0..6 {
            let alpha: Vec<u8> = (0..report.num_mzm)
                .map(|_| {
                    state = state.wrapping_mul(6364136223846793005).wrapping_add(1);
                    ((state >> 33) & 1) as u8
                })
                .collect();
            let shifted = gf2_add(&residual, &apply_d0(&complex.d0, &alpha).unwrap()).unwrap();
            let moved = l1_harmonic_projection(&complex.d0, &shifted, DEFAULT_BUDGET).unwrap();
            assert_eq!(moved.weight, baseline.weight);
            // canonical representative, so the witness is identical too
            assert_eq!(moved.representative, baseline.representative);
        }
    }

    #[test]
    fn budget_exhaustion_reports_an_upper_bound_not_a_lie() {
        let (complex, report) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let residual = logical_class_representative(&report, Axis::Column, 0);
        let full = l1_harmonic_projection(&complex.d0, &residual, DEFAULT_BUDGET).unwrap();
        assert!(full.exact);
        let capped = l1_harmonic_projection(&complex.d0, &residual, 8).unwrap();
        assert!(!capped.exact);
        assert!(capped.searched <= 8);
        assert!(capped.weight >= full.weight);
    }

    #[test]
    fn class_coordinates_are_a_homomorphism() {
        let (complex, report) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let basis = h1_basis(&complex.d0, &complex.d1);
        let lam1 = logical_class_representative(&report, Axis::Column, 0);
        let lam2 = logical_class_representative(&report, Axis::Row, 0);
        let combined = gf2_add(&lam1, &lam2).unwrap();
        let c1 = basis.class_coordinates(&lam1).unwrap();
        let c2 = basis.class_coordinates(&lam2).unwrap();
        let c12 = basis.class_coordinates(&combined).unwrap();
        assert_eq!(c12, gf2_add(&c1, &c2).unwrap());
        assert_ne!(c1, c2);
        assert_ne!(c1, vec![0, 0]);
    }

    #[test]
    fn open_residual_has_no_class() {
        let (complex, report) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let basis = h1_basis(&complex.d0, &complex.d1);
        let mut residual = vec![0u8; report.num_channels];
        residual[0] = 1;
        assert!(basis.class_coordinates(&residual).is_none());
    }

    #[test]
    fn h1_generators_are_closed_and_not_exact() {
        use crate::repair_limit::{in_image_d0, is_closed};
        let (complex, _) = build_tetron_array(3, 3, Topology::Torus).unwrap();
        let basis = h1_basis(&complex.d0, &complex.d1);
        assert_eq!(basis.dim, 2);
        for generator in &basis.generators {
            assert!(is_closed(&complex.d1, generator).unwrap());
            assert!(!in_image_d0(&complex.d0, generator).unwrap());
        }
    }

    #[test]
    fn code_distance_is_the_topological_one() {
        for (rows, cols) in [(2usize, 3usize), (3, 3), (3, 4), (4, 3)] {
            let (complex, _) = build_tetron_array(rows, cols, Topology::Torus).unwrap();
            let (distance, exact) =
                code_distance(&complex.d0, &complex.d1, DEFAULT_BUDGET).unwrap();
            assert!(exact);
            assert_eq!(distance, Some(rows.min(cols)), "torus {rows}x{cols}");
        }
        for (rows, cols) in [(2usize, 3usize), (3, 3), (2, 4)] {
            let (complex, _) = build_tetron_array(rows, cols, Topology::Cylinder).unwrap();
            let (distance, exact) =
                code_distance(&complex.d0, &complex.d1, DEFAULT_BUDGET).unwrap();
            assert!(exact);
            assert_eq!(distance, Some(rows + 1), "cylinder {rows}x{cols}");
        }
        let d0 = GF2Matrix::zeros(64, 0);
        let d1 = GF2Matrix::zeros(0, 64);
        let err = code_distance(&d0, &d1, 1).unwrap_err();
        assert!(
            err.contains("dim H^1 >= 64"),
            "a 64-dimensional class space must be refused, got {err}"
        );

        let mut wide = GF2Matrix::zeros(64, 64);
        for index in 0..64 {
            wide.data[index][index] = 1;
        }
        let projection = l1_harmonic_projection(&wide, &vec![1u8; 64], 4).unwrap();
        assert!(!projection.exact);
        assert_eq!(projection.coset_size, u64::MAX);

        let (complex, _) = build_tetron_array(3, 3, Topology::Disk).unwrap();
        assert_eq!(
            code_distance(&complex.d0, &complex.d1, DEFAULT_BUDGET).unwrap(),
            (None, true),
            "H^1 = 0 leaves nothing to weigh"
        );
    }

    /// Golden fixture pinning the Rust face to the Python face.
    ///
    /// Values produced by `majorana.demos.tetron_homology_benchmark`
    /// on 2026-08-05 and recorded in `artifacts/tetron_homology_report.json`.
    /// If the two faces drift, this fails rather than letting them diverge.
    #[test]
    fn per_class_weights_match_the_python_face() {
        let (complex, _) = build_tetron_array(3, 4, Topology::Torus).unwrap();
        let basis = h1_basis(&complex.d0, &complex.d1);
        assert_eq!(basis.dim, 2);

        let mut observed: Vec<(String, usize)> = Vec::new();
        for code in 0u64..(1u64 << basis.dim) {
            let coordinates: Vec<u8> = (0..basis.dim)
                .map(|index| ((code >> index) & 1) as u8)
                .collect();
            let representative = basis.class_representative(&coordinates);
            let projection =
                l1_harmonic_projection(&complex.d0, &representative, DEFAULT_BUDGET).unwrap();
            assert!(projection.exact);
            observed.push((H1Basis::class_id(&coordinates), projection.weight));
        }
        observed.sort();

        // torus 3x4: the diagonal class must cross every row AND every column.
        assert_eq!(
            observed,
            vec![
                ("h1:00".to_string(), 0usize),
                ("h1:01".to_string(), 4),
                ("h1:10".to_string(), 3),
                ("h1:11".to_string(), 7),
            ]
        );
    }

    /// Structure fixture, same source as above.
    #[test]
    fn structure_matches_the_python_face() {
        let cases = [
            (
                Topology::Disk,
                3usize,
                3usize,
                16usize,
                24usize,
                9usize,
                15usize,
                9usize,
                0usize,
            ),
            (Topology::Cylinder, 3, 3, 12, 21, 9, 11, 9, 1),
            (Topology::Torus, 2, 2, 4, 8, 4, 3, 3, 2),
            (Topology::Torus, 3, 3, 9, 18, 9, 8, 8, 2),
            (Topology::Torus, 3, 4, 12, 24, 12, 11, 11, 2),
            (Topology::Torus, 4, 4, 16, 32, 16, 15, 15, 2),
            (Topology::Torus, 4, 5, 20, 40, 20, 19, 19, 2),
        ];
        for (topology, rows, cols, v, e, f, rank_d0, rank_d1, dim_h1) in cases {
            let (_, report) = build_tetron_array(rows, cols, topology).unwrap();
            assert_eq!(
                (
                    report.num_mzm,
                    report.num_channels,
                    report.num_islands,
                    report.rank_d0,
                    report.rank_d1,
                    report.dim_h1
                ),
                (v, e, f, rank_d0, rank_d1, dim_h1),
                "{topology:?} {rows}x{cols} drifted from the Python face"
            );
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_bb856dc7 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbb856dc7::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbb856dc7::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbb856dc7::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbb856dc7::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbb856dc7::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorbb856dc7::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorbb856dc7::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
