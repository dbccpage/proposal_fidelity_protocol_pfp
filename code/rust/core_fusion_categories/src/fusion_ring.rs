// Fusion rings: the based ring `K_0` of a fusion category, as a table of
// non-negative integer structure constants `N_{ab}^c`.
//
// A [`FusionTable`] is a *declared* table: it is checked for shape only, and
// [`FusionTable::first_defect`] reports the first failure of the ring laws (unit,
// commutativity, associativity, duality, Frobenius reciprocity), so mutated tables
// can be refused one law at a time. A [`FusionRing`] is a table that passed the
// laws; its dual involution is computed from the table, not declared.
//
// Conventions: label `0` is the unit; `N_{ab}^c` is the number of times `c` occurs in
// `a x b`; the dual `a*` is the unique label with `N_{a a*}^0 = 1`; Frobenius
// reciprocity is `N_{ab}^c = N_{a* c}^b = N_{c b*}^a`. All sums are checked: a sum that
// would overflow 128 bits is a typed defect, never a wrapped number, and fusion-path
// counts are arbitrary-precision.
//
// What is computed: the ring laws, fusion-path counts (Bratteli counts), the
// characteristic polynomial and Frobenius-Perron dimension of each object, the global
// dimension `D^2 = sum_a d_a^2` as the Perron eigenvalue of `sum_a N_a N_{a*}`, and
// the Verlinde consistency of a candidate S-matrix. What is not: any statement about
// whether a ring is the ring of a fusion category (that needs F-symbols, see
// `fusion_category`).
//
// AuthorityEffect: None.
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_bigint::{BigInt, BigUint};
use num_traits::{One, ToPrimitive, Zero};
use thiserror::Error;

use crate::error::FusionError;
use crate::scalar::FusionScalar;
use linear_algebra::exact_field::{characteristic_polynomial, matrix};
use core_number_theory::algebraic_real::{largest_real_root, RealAlgebraic};

/// Largest supported rank of a fusion ring.
pub const MAX_RANK: usize = 32;

/// Largest number of factors in a fusion word accepted by the path counters.
pub const MAX_FUSION_WORD: usize = 1 << 14;

/// Conservative scalar-bit work, not elapsed CPU cycles or heap bytes.
pub const MAX_FUSION_PATH_WORK: u128 = 1 << 32;

fn admit_rank(rank: usize) -> Result<(), FusionError> {
    if rank == 0 || rank > MAX_RANK {
        return Err(FusionError::RankOutOfRange {
            rank,
            max: MAX_RANK,
        });
    }
    Ok(())
}

// Callers admit R first or pass a fixed catalog array of rank at most three.
fn flatten_multiplicities<const R: usize>(n: &[[[u64; R]; R]; R]) -> Vec<u64> {
    let mut flat = Vec::with_capacity(R * R * R);
    flat.extend(
        n.iter()
            .flat_map(|plane| plane.iter().flat_map(|row| row.iter().copied())),
    );
    flat
}

/// The first failing law of a fusion ring.
#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum RingDefect {
    /// `0 x a` or `a x 0` is not `a`.
    #[error("unit law fails on label {label}")]
    Unit { label: usize },
    /// `a x b != b x a`.
    #[error("labels {left} and {right} do not commute")]
    Commutativity { left: usize, right: usize },
    /// `outcome` occurs `left` times in `(a x b) x c` and `right` times in `a x (b x c)`.
    #[error(
        "associativity fails on {labels:?}: outcome {outcome} occurs {left} times in the \
         left bracketing and {right} in the right"
    )]
    Associativity {
        labels: (usize, usize, usize),
        outcome: usize,
        left: u128,
        right: u128,
    },
    /// The unit does not occur exactly once in `a x b` for exactly one `b`, or the duality
    /// it defines is not an involution.
    #[error("label {label} has no dual (unit occurs once in label x dual, involutively)")]
    Duality { label: usize },
    /// `N_{ab}^c != N_{a* c}^b` or `N_{ab}^c != N_{c b*}^a`.
    #[error("Frobenius reciprocity fails on {labels:?}")]
    Reciprocity { labels: (usize, usize, usize) },
    /// A multiplicity sum does not fit 128 bits, so the law could not be checked.
    #[error("a multiplicity sum overflows 128 bits on {labels:?}")]
    Overflow { labels: (usize, usize, usize) },
}

/// A finite abelian group `Z_{m_1} x ... x Z_{m_r}` with labels in mixed radix:
/// `label = d_1 + m_1 (d_2 + m_2 (...))`, digit 1 least significant.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AbelianGroup {
    moduli: Vec<usize>,
    order: usize,
}

impl AbelianGroup {
    /// The group with the given cyclic factors (each at least 2), of order at most
    /// [`MAX_RANK`].
    pub fn new(moduli: &[usize]) -> Result<Self, FusionError> {
        let mut order: usize = 1;
        for &m in moduli {
            if m < 2 {
                return Err(FusionError::RankOutOfRange {
                    rank: m,
                    max: MAX_RANK,
                });
            }
            order = order.checked_mul(m).ok_or(FusionError::Overflow {
                context: "sizing an abelian group",
            })?;
            if order > MAX_RANK {
                return Err(FusionError::RankOutOfRange {
                    rank: order,
                    max: MAX_RANK,
                });
            }
        }
        Ok(Self {
            moduli: moduli.to_vec(),
            order,
        })
    }

    /// The cyclic factors.
    pub fn moduli(&self) -> &[usize] {
        &self.moduli
    }

    /// The number of elements.
    pub fn order(&self) -> usize {
        self.order
    }

    /// The digits `(d_1, ..., d_r)` of a label.
    fn check_label(&self, label: usize) -> Result<(), FusionError> {
        if label >= self.order {
            return Err(FusionError::Label {
                label,
                rank: self.order,
            });
        }
        Ok(())
    }

    pub fn digits(&self, label: usize) -> Result<Vec<usize>, FusionError> {
        self.check_label(label)?;
        let mut rest = label;
        Ok(self
            .moduli
            .iter()
            .map(|&m| {
                let digit = rest % m;
                rest /= m;
                digit
            })
            .collect())
    }

    /// The label with the given digits (each below its modulus).
    pub fn label(&self, digits: &[usize]) -> Result<usize, FusionError> {
        if digits.len() != self.moduli.len() {
            return Err(FusionError::ListLength {
                what: "digits",
                expected: self.moduli.len(),
                got: digits.len(),
            });
        }
        let mut label = 0usize;
        let mut stride = 1usize;
        for (&digit, &m) in digits.iter().zip(&self.moduli) {
            if digit >= m {
                return Err(FusionError::Label {
                    label: digit,
                    rank: m,
                });
            }
            label += digit * stride;
            stride *= m;
        }
        Ok(label)
    }

    /// `a + b`.
    pub fn add(&self, a: usize, b: usize) -> Result<usize, FusionError> {
        self.check_label(a)?;
        self.check_label(b)?;
        let (mut left, mut right, mut label, mut stride) = (a, b, 0usize, 1usize);
        for &m in &self.moduli {
            label += ((left % m + right % m) % m) * stride;
            left /= m;
            right /= m;
            stride *= m;
        }
        Ok(label)
    }

    /// `-a`.
    pub fn negate(&self, a: usize) -> Result<usize, FusionError> {
        self.check_label(a)?;
        let (mut rest, mut label, mut stride) = (a, 0usize, 1usize);
        for &m in &self.moduli {
            label += ((m - rest % m) % m) * stride;
            rest /= m;
            stride *= m;
        }
        Ok(label)
    }
}

/// A declared fusion table of rank `r`: `N_{ab}^c` for labels `0..r`, checked for shape
/// only. Label `0` is the unit by convention.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FusionTable {
    rank: usize,
    names: Vec<String>,
    n: Vec<u64>,
}

impl FusionTable {
    /// A table from the flat array `n[(a * rank + b) * rank + c] = N_{ab}^c`.
    pub fn new(rank: usize, multiplicities: Vec<u64>) -> Result<Self, FusionError> {
        admit_rank(rank)?;
        let names = (0..rank).map(|label| label.to_string()).collect();
        Self::with_names(rank, names, multiplicities)
    }

    /// A table with explicit label names.
    pub fn with_names(
        rank: usize,
        names: Vec<String>,
        multiplicities: Vec<u64>,
    ) -> Result<Self, FusionError> {
        admit_rank(rank)?;
        let expected = rank * rank * rank;
        if multiplicities.len() != expected {
            return Err(FusionError::TableShape {
                rank,
                expected,
                got: multiplicities.len(),
            });
        }
        if names.len() != rank {
            return Err(FusionError::ListLength {
                what: "label names",
                expected: rank,
                got: names.len(),
            });
        }
        Ok(Self {
            rank,
            names,
            n: multiplicities,
        })
    }

    /// A table from a nested array `n[a][b][c]` of a size known at compile time.
    pub fn from_array<const R: usize>(n: [[[u64; R]; R]; R]) -> Result<Self, FusionError> {
        admit_rank(R)?;
        let flat = flatten_multiplicities(&n);
        Self::new(R, flat)
    }

    /// The number of labels.
    pub fn rank(&self) -> usize {
        self.rank
    }

    /// The label names.
    pub fn names(&self) -> &[String] {
        &self.names
    }

    fn check(&self, label: usize) -> Result<usize, FusionError> {
        if label < self.rank {
            Ok(label)
        } else {
            Err(FusionError::Label {
                label,
                rank: self.rank,
            })
        }
    }

    /// `N_{ab}^c`, with no bounds panics: loop-bounded callers inside the crate use this.
    fn at(&self, a: usize, b: usize, c: usize) -> u64 {
        self.n
            .get((a * self.rank + b) * self.rank + c)
            .copied()
            .unwrap_or(0)
    }

    /// `N_{ab}^c`, the number of times `c` occurs in `a x b`.
    pub fn multiplicity(&self, a: usize, b: usize, c: usize) -> Result<u64, FusionError> {
        Ok(self.at(self.check(a)?, self.check(b)?, self.check(c)?))
    }

    fn associativity_sum(&self, first: impl Fn(usize) -> (u64, u64)) -> Option<u128> {
        (0..self.rank).try_fold(0u128, |acc, e| {
            let (x, y) = first(e);
            acc.checked_add(u128::from(x).checked_mul(u128::from(y))?)
        })
    }

    fn unique_dual(&self, a: usize) -> Result<usize, usize> {
        let mut found = None;
        for b in 0..self.rank {
            let multiplicity = self.at(a, b, 0);
            if multiplicity > 0 {
                if found.is_some() || multiplicity != 1 {
                    return Err(a);
                }
                found = Some(b);
            }
        }
        found.ok_or(a)
    }

    /// The dual of each label (`N_{a a*}^0 = 1`), or the first label without one.
    fn dual_labels(&self) -> Result<Vec<usize>, usize> {
        let mut dual = Vec::with_capacity(self.rank);
        for a in 0..self.rank {
            dual.push(self.unique_dual(a)?);
        }
        for a in 0..self.rank {
            let back = dual.get(dual.get(a).copied().unwrap_or(a)).copied();
            if back != Some(a) {
                return Err(a);
            }
        }
        Ok(dual)
    }

    fn first_unit_defect(&self) -> Option<RingDefect> {
        (0..self.rank)
            .find(|&label| {
                (0..self.rank).any(|c| {
                    let expected = u64::from(c == label);
                    self.at(0, label, c) != expected || self.at(label, 0, c) != expected
                })
            })
            .map(|label| RingDefect::Unit { label })
    }

    fn first_commutativity_defect(&self) -> Option<RingDefect> {
        (0..self.rank)
            .flat_map(|left| (left + 1..self.rank).map(move |right| (left, right)))
            .find(|&(left, right)| {
                (0..self.rank).any(|c| self.at(left, right, c) != self.at(right, left, c))
            })
            .map(|(left, right)| RingDefect::Commutativity { left, right })
    }

    fn associativity_defect_at(
        &self,
        a: usize,
        b: usize,
        c: usize,
        d: usize,
    ) -> Option<RingDefect> {
        let left = self.associativity_sum(|e| (self.at(a, b, e), self.at(e, c, d)));
        let right = self.associativity_sum(|f| (self.at(b, c, f), self.at(a, f, d)));
        match (left, right) {
            (Some(left), Some(right)) if left != right => Some(RingDefect::Associativity {
                labels: (a, b, c),
                outcome: d,
                left,
                right,
            }),
            (Some(_), Some(_)) => None,
            _ => Some(RingDefect::Overflow { labels: (a, b, c) }),
        }
    }

    fn associativity_defect_for_pair(&self, a: usize, b: usize) -> Option<RingDefect> {
        for c in 0..self.rank {
            for d in 0..self.rank {
                if let Some(defect) = self.associativity_defect_at(a, b, c, d) {
                    return Some(defect);
                }
            }
        }
        None
    }

    fn first_associativity_defect(&self) -> Option<RingDefect> {
        for a in 0..self.rank {
            for b in 0..self.rank {
                if let Some(defect) = self.associativity_defect_for_pair(a, b) {
                    return Some(defect);
                }
            }
        }
        None
    }

    fn first_duality_defect(&self) -> Option<RingDefect> {
        self.dual_labels()
            .err()
            .map(|label| RingDefect::Duality { label })
    }

    fn reciprocity_defect_for_pair(&self, dual: &[usize], a: usize, b: usize) -> Option<usize> {
        let a_star = dual.get(a).copied().unwrap_or(a);
        let b_star = dual.get(b).copied().unwrap_or(b);
        (0..self.rank).find(|&c| {
            let here = self.at(a, b, c);
            here != self.at(a_star, c, b) || here != self.at(c, b_star, a)
        })
    }

    fn first_reciprocity_defect(&self, dual: &[usize]) -> Option<RingDefect> {
        for a in 0..self.rank {
            for b in 0..self.rank {
                if let Some(c) = self.reciprocity_defect_for_pair(dual, a, b) {
                    return Some(RingDefect::Reciprocity { labels: (a, b, c) });
                }
            }
        }
        None
    }

    /// The first failure of the laws of a *commutative* fusion ring, in the order unit,
    /// commutativity, associativity, duality, Frobenius reciprocity. Every anyon model is
    /// commutative.
    pub fn first_defect(&self) -> Option<RingDefect> {
        self.first_unit_defect()
            .or_else(|| self.first_commutativity_defect())
            .or_else(|| self.first_noncommutative_remainder())
    }

    /// The first failure of the laws of a fusion ring that is allowed to be
    /// non-commutative: unit, associativity, duality, Frobenius reciprocity.
    pub fn first_defect_allowing_noncommutative(&self) -> Option<RingDefect> {
        self.first_unit_defect()
            .or_else(|| self.first_noncommutative_remainder())
    }

    fn first_noncommutative_remainder(&self) -> Option<RingDefect> {
        self.first_associativity_defect()
            .or_else(|| self.first_duality_defect())
            .or_else(|| {
                let dual = self.dual_labels().ok()?;
                self.first_reciprocity_defect(&dual)
            })
    }

    /// Validates the table as a fusion ring (commutativity is not required).
    pub fn validate(&self) -> Result<FusionRing, FusionError> {
        FusionRing::try_new(self.clone())
    }

    /// Fusion paths of `copies` copies of `label`, by total charge: the unit vector
    /// multiplied `copies` times by the fusion matrix of `label`. Counts are exact.
    pub fn charge_counts(&self, label: usize, copies: usize) -> Result<Vec<BigUint>, FusionError> {
        let label = self.check(label)?;
        if copies > MAX_FUSION_WORD {
            return Err(FusionError::Budget {
                what: "fusion word length",
                requested: copies as u128,
                limit: MAX_FUSION_WORD as u128,
            });
        }
        self.admit_path_work(std::iter::repeat(label).take(copies))?;
        Ok(self.path_counts(std::iter::repeat(label).take(copies)))
    }

    /// [`Self::charge_counts`] as `u64`, refusing counts that do not fit.
    pub fn charge_counts_u64(&self, label: usize, copies: usize) -> Result<Vec<u64>, FusionError> {
        self.charge_counts(label, copies)?
            .iter()
            .map(|count| {
                count.to_u64().ok_or(FusionError::Overflow {
                    context: "narrowing a fusion-path count to u64",
                })
            })
            .collect()
    }

    fn unit_counts(&self) -> Vec<BigUint> {
        (0..self.rank)
            .map(|c| {
                if c == 0 {
                    BigUint::one()
                } else {
                    BigUint::zero()
                }
            })
            .collect()
    }

    /// One fusion step: `next[c] = sum_a counts[a] N_{a w}^c`.
    fn path_growth(&self, w: usize) -> u32 {
        let max_sum = (0..self.rank)
            .map(|a| {
                (0..self.rank)
                    .map(|c| u128::from(self.at(a, w, c)))
                    .sum::<u128>()
            })
            .max()
            .unwrap_or(0);
        if max_sum <= 1 {
            0
        } else {
            128 - (max_sum - 1).leading_zeros()
        }
    }

    fn admit_path_work(&self, labels: impl Iterator<Item = usize>) -> Result<(), FusionError> {
        let mut growths = [None; MAX_RANK];
        let (mut bits, mut work) = (1u128, 0u128);
        let cells = (self.rank * self.rank) as u128;
        for w in labels {
            work += cells * (bits + 64);
            if work > MAX_FUSION_PATH_WORK {
                return Err(FusionError::Budget {
                    what: "fusion path scalar-bit work",
                    requested: work,
                    limit: MAX_FUSION_PATH_WORK,
                });
            }
            let growth = *growths[w].get_or_insert_with(|| self.path_growth(w));
            bits += u128::from(growth);
        }
        Ok(())
    }

    fn step_into(&self, counts: &[BigUint], w: usize, next: &mut [BigUint]) {
        for value in next.iter_mut() {
            value.set_zero();
        }
        for (a, count) in counts.iter().take(self.rank).enumerate() {
            if count.is_zero() {
                continue;
            }
            for (c, value) in next.iter_mut().enumerate() {
                let multiplicity = self.at(a, w, c);
                if multiplicity != 0 {
                    *value += count * multiplicity;
                }
            }
        }
    }

    fn path_counts(&self, labels: impl Iterator<Item = usize>) -> Vec<BigUint> {
        let mut counts = self.unit_counts();
        let mut next = Vec::new();
        for w in labels {
            if next.is_empty() {
                next = vec![BigUint::zero(); self.rank];
            }
            self.step_into(&counts, w, &mut next);
            std::mem::swap(&mut counts, &mut next);
        }
        counts
    }

    /// The Ising fusion rules: labels `1 = 0`, `sigma = 1`, `psi = 2`; `sigma x sigma =
    /// 1 + psi`, `sigma x psi = sigma`, `psi x psi = 1`.
    pub fn ising() -> Self {
        let n = [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            [[0, 0, 1], [0, 1, 0], [1, 0, 0]],
        ];
        let flat = flatten_multiplicities(&n);
        Self {
            rank: 3,
            names: ["1", "sigma", "psi"].map(String::from).to_vec(),
            n: flat,
        }
    }
}

/// A validated fusion ring: a [`FusionTable`] that satisfies the unit, associativity,
/// duality and reciprocity laws, together with its dual involution.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FusionRing {
    table: FusionTable,
    dual: Vec<usize>,
}

impl FusionRing {
    /// Validates a declared table (commutativity is not required; see
    /// [`Self::is_commutative`]).
    pub fn try_new(table: FusionTable) -> Result<Self, FusionError> {
        if let Some(defect) = table.first_defect_allowing_noncommutative() {
            return Err(FusionError::Ring(defect));
        }
        let dual = table
            .dual_labels()
            .map_err(|label| FusionError::Ring(RingDefect::Duality { label }))?;
        Ok(Self { table, dual })
    }

    /// The number of simple objects.
    pub fn rank(&self) -> usize {
        self.table.rank
    }

    /// The label names.
    pub fn names(&self) -> &[String] {
        &self.table.names
    }

    /// The unit label (always `0`).
    pub fn unit(&self) -> usize {
        0
    }

    /// The table this ring was validated from.
    pub fn table(&self) -> &FusionTable {
        &self.table
    }

    /// The dual `a*` of a label.
    pub fn dual(&self, a: usize) -> Result<usize, FusionError> {
        self.table.check(a)?;
        self.dual.get(a).copied().ok_or(FusionError::Label {
            label: a,
            rank: self.table.rank,
        })
    }

    /// `N_{ab}^c`.
    pub fn multiplicity(&self, a: usize, b: usize, c: usize) -> Result<u64, FusionError> {
        self.table.multiplicity(a, b, c)
    }

    /// `N_{ab}^c` for labels already known to be in range (loop-bounded internal use).
    pub(crate) fn n(&self, a: usize, b: usize, c: usize) -> u64 {
        self.table.at(a, b, c)
    }

    /// The labels `c` with `N_{ab}^c > 0`, ascending.
    pub fn fuse(&self, a: usize, b: usize) -> Result<Vec<usize>, FusionError> {
        self.table.check(a)?;
        self.table.check(b)?;
        Ok((0..self.table.rank)
            .filter(|&c| self.table.at(a, b, c) > 0)
            .collect())
    }

    /// Whether `a x b = b x a` for all labels.
    pub fn is_commutative(&self) -> bool {
        self.table.first_commutativity_defect().is_none()
    }

    /// Whether every `N_{ab}^c` is `0` or `1`.
    pub fn is_multiplicity_free(&self) -> bool {
        self.table.n.iter().all(|&m| m <= 1)
    }

    /// Whether every object is invertible (`a x b` is a single simple object for all `a, b`).
    pub fn is_pointed(&self) -> bool {
        (0..self.rank()).all(|a| {
            (0..self.rank()).all(|b| {
                (0..self.rank()).try_fold(0u64, |acc, c| acc.checked_add(self.table.at(a, b, c)))
                    == Some(1)
            })
        })
    }

    /// The number of fusion paths `unit -> w_1 -> w_2 -> ... -> target` for the word
    /// `w`: the dimension of the fusion space `Hom(target, w_1 x ... x w_n)`.
    pub fn fusion_paths(&self, word: &[usize], target: usize) -> Result<BigUint, FusionError> {
        let counts = self.fusion_path_counts(word)?;
        self.table.check(target)?;
        Ok(counts.into_iter().nth(target).unwrap_or_else(BigUint::zero))
    }

    /// The fusion-path counts of a word, by total charge.
    pub fn fusion_path_counts(&self, word: &[usize]) -> Result<Vec<BigUint>, FusionError> {
        if word.len() > MAX_FUSION_WORD {
            return Err(FusionError::Budget {
                what: "fusion word length",
                requested: word.len() as u128,
                limit: MAX_FUSION_WORD as u128,
            });
        }
        for &w in word {
            self.table.check(w)?;
        }
        self.table.admit_path_work(word.iter().copied())?;
        Ok(self.table.path_counts(word.iter().copied()))
    }

    /// The fusion matrix `N_a` with `(N_a)_{bc} = N_{ab}^c`, as integers.
    pub fn fusion_matrix(&self, a: usize) -> Result<Vec<Vec<BigInt>>, FusionError> {
        self.table.check(a)?;
        Ok((0..self.rank())
            .map(|b| {
                (0..self.rank())
                    .map(|c| BigInt::from(self.table.at(a, b, c)))
                    .collect()
            })
            .collect())
    }

    fn rational_fusion_matrix(
        &self,
        a: usize,
    ) -> Result<BasicMatrix<core_number_theory::rational::Rational>, FusionError> {
        self.table.check(a)?;
        BasicMatrix::try_from_fn_with_limit(
            self.rank(),
            self.rank(),
            MAX_RANK * MAX_RANK,
            |b, c| {
                core_number_theory::rational::Rational::from_integer(BigInt::from(
                    self.table.at(a, b, c),
                ))
            },
        )
        .map_err(FusionError::from)
    }

    fn integral_coefficients(
        values: Vec<core_number_theory::rational::Rational>,
    ) -> Result<Vec<BigInt>, FusionError> {
        values
            .into_iter()
            .map(|q| {
                if q.is_integer() {
                    Ok(q.to_integer())
                } else {
                    Err(FusionError::Polynomial(
                        "characteristic polynomial coefficient is not integral",
                    ))
                }
            })
            .collect()
    }

    /// The characteristic polynomial of `N_a` (monic, lowest degree first).
    pub fn characteristic_polynomial(&self, a: usize) -> Result<Vec<BigInt>, FusionError> {
        Self::integral_coefficients(characteristic_polynomial::characteristic_polynomial(
            &self.rational_fusion_matrix(a)?,
        )?)
    }

    /// The Frobenius-Perron dimension of `a`: the largest real root of the characteristic
    /// polynomial of `N_a` (the spectral radius of a non-negative matrix), as an exact
    /// integer or quadratic surd when it is one, else as an isolated root.
    pub fn frobenius_perron_dimension(&self, a: usize) -> Result<RealAlgebraic, FusionError> {
        largest_real_root(&self.characteristic_polynomial(a)?).map_err(FusionError::from)
    }

    /// The global dimension `D^2 = sum_a d_a^2` with `d_a` the Frobenius-Perron
    /// dimensions: the Perron eigenvalue of `sum_a N_a N_{a*}`, because the positive
    /// character `d` satisfies `(sum_a N_a N_{a*}) d = (sum_a d_a d_{a*}) d`.
    pub fn global_dimension_squared(&self) -> Result<RealAlgebraic, FusionError> {
        let r = self.rank();
        let mut total = matrix::zeros::<core_number_theory::rational::Rational>(r, r)?;
        for a in 0..r {
            let a_star = self.dual(a)?;
            let left = self.rational_fusion_matrix(a)?;
            let right = self.rational_fusion_matrix(a_star)?;
            total = matrix::add(&total, &matrix::multiply(&left, &right)?)?;
        }
        largest_real_root(&Self::integral_coefficients(
            characteristic_polynomial::characteristic_polynomial(&total)?,
        )?)
        .map_err(FusionError::from)
    }

    /// The triples `(a, b, c)` at which the Verlinde formula
    /// `N_{ab}^c = (1/D^2) sum_x S_{ax} S_{bx} conj(S_{cx}) / S_{0x}` (with `S` the
    /// unnormalised matrix `D * S`) fails to reproduce the ring, evaluated exactly in
    /// the field. `s_tilde` must be `rank x rank` with nonzero first row.
    pub fn verlinde_defects<K: FusionScalar>(
        &self,
        s_tilde: &BasicMatrix<K>,
        d_squared: &K,
    ) -> Result<Vec<[usize; 3]>, FusionError> {
        let r = self.rank();
        if s_tilde.shape() != (r, r) {
            return Err(FusionError::Shape {
                operation: "Verlinde check",
                left: s_tilde.shape(),
                right: (r, r),
            });
        }
        let d_inverse =
            core_number_theory::scalar::inverse(d_squared).map_err(FusionError::from)?;
        let mut first_row_inverse = Vec::with_capacity(r);
        for x in 0..r {
            first_row_inverse.push(
                core_number_theory::scalar::inverse(s_tilde.get_ref(0, x)?)
                    .map_err(FusionError::from)?,
            );
        }
        let mut defects = Vec::new();
        for a in 0..r {
            for b in 0..r {
                self.collect_verlinde_pair(
                    s_tilde,
                    &first_row_inverse,
                    &d_inverse,
                    a,
                    b,
                    &mut defects,
                )?;
            }
        }
        Ok(defects)
    }

    fn verlinde_value<K: FusionScalar>(
        &self,
        s_tilde: &BasicMatrix<K>,
        weights: &[K],
        d_inverse: &K,
        a: usize,
        b: usize,
        c: usize,
    ) -> Result<K, FusionError> {
        let mut total = K::zero();
        for (x, weight) in weights.iter().enumerate() {
            let term = s_tilde
                .get_ref(a, x)?
                .mul(s_tilde.get_ref(b, x)?)
                .mul(&s_tilde.get_ref(c, x)?.conjugate())
                .mul(weight);
            total = total.add(&term);
        }
        Ok(total.mul(d_inverse))
    }

    fn collect_verlinde_pair<K: FusionScalar>(
        &self,
        s_tilde: &BasicMatrix<K>,
        weights: &[K],
        d_inverse: &K,
        a: usize,
        b: usize,
        defects: &mut Vec<[usize; 3]>,
    ) -> Result<(), FusionError> {
        for c in 0..self.rank() {
            let value = self.verlinde_value(s_tilde, weights, d_inverse, a, b, c)?;
            let expected = core_number_theory::scalar::from_i64::<K>(
                i64::try_from(self.table.at(a, b, c)).map_err(|_| FusionError::Overflow {
                    context: "embedding a fusion coefficient",
                })?,
            );
            if value != expected {
                defects.push([a, b, c]);
            }
        }
        Ok(())
    }

    /// `Z_n` with addition: `n` invertible objects `0, 1, ..., n-1`, `a x b = a + b`.
    pub fn z_n(n: usize) -> Result<Self, FusionError> {
        Self::pointed(&[n], None)
    }

    /// The pointed ring of a finite abelian group: `a x b = a + b`, `a* = -a`. Labels are
    /// the mixed-radix encodings of [`AbelianGroup`].
    pub fn pointed(moduli: &[usize], names: Option<Vec<String>>) -> Result<Self, FusionError> {
        let group = AbelianGroup::new(moduli)?;
        let order = group.order();
        let mut n = vec![0u64; order * order * order];
        for a in 0..order {
            for b in 0..order {
                let c = group.add(a, b)?;
                if let Some(slot) = n.get_mut((a * order + b) * order + c) {
                    *slot = 1;
                }
            }
        }
        let names = names.unwrap_or_else(|| (0..order).map(|k| k.to_string()).collect());
        Self::try_new(FusionTable::with_names(order, names, n)?)
    }

    /// The Ising ring (`1, sigma, psi`).
    pub fn ising() -> Result<Self, FusionError> {
        Self::try_new(FusionTable::ising())
    }

    /// The Fibonacci ring: `tau x tau = 1 + tau`.
    pub fn fibonacci() -> Result<Self, FusionError> {
        let n = [[[1, 0], [0, 1]], [[0, 1], [1, 1]]];
        let names = ["1", "tau"].map(String::from).to_vec();
        let flat = flatten_multiplicities(&n);
        Self::try_new(FusionTable::with_names(2, names, flat)?)
    }

    /// The semion ring: `Z_2` with objects `1, s`.
    pub fn semion() -> Result<Self, FusionError> {
        Self::pointed(&[2], Some(["1", "s"].map(String::from).to_vec()))
    }

    /// The toric-code ring `Z_2 x Z_2` with objects `1, e, m, eps = e x m`.
    pub fn toric_code() -> Result<Self, FusionError> {
        Self::pointed(
            &[2, 2],
            Some(["1", "e", "m", "eps"].map(String::from).to_vec()),
        )
    }

    /// The three-fermion ring `Z_2 x Z_2` with objects `1, f1, f2, f3`.
    pub fn three_fermion() -> Result<Self, FusionError> {
        Self::pointed(
            &[2, 2],
            Some(["1", "f1", "f2", "f3"].map(String::from).to_vec()),
        )
    }

    /// The `SU(2)_k` fusion ring: labels `0..=k` (twice the spin), `N_{ij}^l = 1` exactly
    /// when `|i - j| <= l <= min(i + j, 2k - i - j)` and `i + j + l` is even.
    pub fn su2_level(k: usize) -> Result<Self, FusionError> {
        let rank = k.checked_add(1).ok_or(FusionError::Overflow {
            context: "sizing an SU(2) fusion ring",
        })?;
        if k == 0 || rank > MAX_RANK {
            return Err(FusionError::RankOutOfRange {
                rank,
                max: MAX_RANK,
            });
        }
        let mut n = vec![0u64; rank * rank * rank];
        for i in 0..rank {
            for j in 0..rank {
                Self::fill_su2_product(&mut n, rank, k, i, j);
            }
        }
        let names = (0..rank).map(|i| format!("j={i}/2")).collect();
        Self::try_new(FusionTable::with_names(rank, names, n)?)
    }

    fn fill_su2_product(n: &mut [u64], rank: usize, k: usize, i: usize, j: usize) {
        let low = i.abs_diff(j);
        let high = (i + j).min((2 * k) - (i + j));
        for l in low..=high {
            if (i + j + l) % 2 == 0 {
                if let Some(slot) = n.get_mut((i * rank + j) * rank + l) {
                    *slot = 1;
                }
            }
        }
    }

    /// The representation ring of `S_3`: `1, sgn, std` with `sgn x sgn = 1`,
    /// `sgn x std = std`, `std x std = 1 + sgn + std`.
    pub fn rep_s3() -> Result<Self, FusionError> {
        let n = [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 1, 0], [1, 0, 0], [0, 0, 1]],
            [[0, 0, 1], [0, 0, 1], [1, 1, 1]],
        ];
        let flat = flatten_multiplicities(&n);
        Self::try_new(FusionTable::with_names(
            3,
            ["1", "sgn", "std"].map(String::from).to_vec(),
            flat,
        )?)
    }
}

// Origin: engine/crates_rs/core_fusion_categories/src/fusion_ring.rs
// Claim: urn:core:crates_rs:core-fusion-categories:fusion-ring:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use core_number_theory::rational::rq;

    fn ising_array() -> [[[u64; 3]; 3]; 3] {
        [
            [[1, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 1, 0], [1, 0, 1], [0, 1, 0]],
            [[0, 0, 1], [0, 1, 0], [1, 0, 0]],
        ]
    }

    #[test]
    fn the_declared_ising_table_satisfies_every_ring_law() {
        let table = FusionTable::ising();
        assert_eq!(table.first_defect(), None);
        assert_eq!(table.multiplicity(1, 1, 0), Ok(1));
        assert_eq!(table.multiplicity(1, 1, 2), Ok(1));
        assert_eq!(table.multiplicity(1, 1, 1), Ok(0));
        let ring = table.validate().unwrap();
        assert_eq!(ring.rank(), 3);
        assert_eq!(ring.dual(1), Ok(1));
        assert!(ring.is_commutative());
        assert!(ring.is_multiplicity_free());
        assert!(!ring.is_pointed());
        assert_eq!(FusionTable::from_array(ising_array()).unwrap(), {
            let mut named = FusionTable::ising();
            named.names = (0..3).map(|k| k.to_string()).collect();
            named
        });
    }

    #[test]
    fn mutated_tables_are_refused_by_exactly_the_law_they_break() {
        let base = ising_array();

        let mut unit = base;
        unit[0][1] = [0, 0, 1];
        assert_eq!(
            FusionTable::from_array(unit).unwrap().first_defect(),
            Some(RingDefect::Unit { label: 1 })
        );

        let mut lopsided = base;
        lopsided[2][1] = [1, 0, 0];
        assert_eq!(
            FusionTable::from_array(lopsided).unwrap().first_defect(),
            Some(RingDefect::Commutativity { left: 1, right: 2 })
        );

        let mut psi_absorbs = base;
        psi_absorbs[1][2] = [0, 0, 1];
        psi_absorbs[2][1] = [0, 0, 1];
        assert_eq!(
            FusionTable::from_array(psi_absorbs).unwrap().first_defect(),
            Some(RingDefect::Associativity {
                labels: (1, 1, 2),
                outcome: 0,
                left: 1,
                right: 0
            })
        );

        // 1 x 1 = 2 * unit: unital, commutative and associative (a commutative monoid), but
        // the unit occurs twice in `a x a`, so `a` has no dual.
        let doubled = FusionTable::from_array([[[1, 0], [0, 1]], [[0, 1], [2, 0]]]).unwrap();
        assert_eq!(
            doubled.first_defect(),
            Some(RingDefect::Duality { label: 1 })
        );
        assert_eq!(
            doubled.validate(),
            Err(FusionError::Ring(RingDefect::Duality { label: 1 }))
        );
    }

    #[test]
    fn frobenius_reciprocity_is_a_separate_law_with_its_own_defect() {
        // In the table where sigma x psi = psi, the pair (sigma, psi) fails reciprocity at
        // (1, 1, 2): N_{sigma sigma}^psi = 1 but N_{sigma* psi}^sigma = 0.
        let mut psi_absorbs = ising_array();
        psi_absorbs[1][2] = [0, 0, 1];
        psi_absorbs[2][1] = [0, 0, 1];
        let table = FusionTable::from_array(psi_absorbs).unwrap();
        assert_eq!(
            table.first_reciprocity_defect(&[0, 1, 2]),
            Some(RingDefect::Reciprocity { labels: (1, 1, 2) })
        );
        // The genuine Ising table passes the same check.
        assert_eq!(
            FusionTable::ising().first_reciprocity_defect(&[0, 1, 2]),
            None
        );
        // A wrong duality vector is caught by reciprocity too (swap sigma's dual with psi's).
        assert!(FusionTable::ising()
            .first_reciprocity_defect(&[0, 2, 1])
            .is_some());
    }

    #[test]
    fn shapes_and_labels_are_refused_with_typed_errors() {
        assert_eq!(
            FusionTable::new(0, vec![]),
            Err(FusionError::RankOutOfRange {
                rank: 0,
                max: MAX_RANK
            })
        );
        assert_eq!(
            FusionTable::new(3, vec![0; 26]),
            Err(FusionError::TableShape {
                rank: 3,
                expected: 27,
                got: 26
            })
        );
        assert_eq!(
            FusionTable::new(MAX_RANK + 1, vec![]),
            Err(FusionError::RankOutOfRange {
                rank: MAX_RANK + 1,
                max: MAX_RANK
            })
        );
        let ising = FusionTable::ising();
        assert_eq!(
            ising.multiplicity(3, 0, 0),
            Err(FusionError::Label { label: 3, rank: 3 })
        );
        assert_eq!(
            ising.charge_counts(3, 2),
            Err(FusionError::Label { label: 3, rank: 3 })
        );
        assert!(matches!(
            ising.charge_counts(1, MAX_FUSION_WORD + 1),
            Err(FusionError::Budget { .. })
        ));
        assert_eq!(
            FusionTable::with_names(2, vec!["only".into()], vec![0; 8]),
            Err(FusionError::ListLength {
                what: "label names",
                expected: 2,
                got: 1
            })
        );
    }

    #[test]
    fn sigma_paths_count_the_parity_sectors_with_exact_arithmetic() {
        let ising = FusionTable::ising();
        // 2L copies of sigma: 2^(L-1) paths to 1 and to psi; odd copies fuse only to sigma.
        for l in 1..=10u32 {
            let half = BigUint::from(2u32).pow(l - 1);
            let even = ising.charge_counts(1, 2 * l as usize).unwrap();
            assert_eq!(even, vec![half.clone(), BigUint::zero(), half.clone()]);
            let odd = ising.charge_counts(1, 2 * l as usize - 1).unwrap();
            assert_eq!(odd, vec![BigUint::zero(), half, BigUint::zero()]);
        }
        assert_eq!(
            ising.charge_counts(1, 0).unwrap(),
            vec![BigUint::one(), BigUint::zero(), BigUint::zero()]
        );
        assert_eq!(
            ising.charge_counts_u64(2, 3).unwrap(),
            vec![0, 0, 1],
            "psi x psi x psi = psi"
        );
        // 400 sigmas: the count 2^199 does not fit u64, and the checked variant says so
        // instead of wrapping (the superseded table wrapped at about 130 copies).
        let big = ising.charge_counts(1, 400).unwrap();
        assert_eq!(big[0], BigUint::from(2u32).pow(199));
        assert_eq!(
            ising.charge_counts_u64(1, 400),
            Err(FusionError::Overflow {
                context: "narrowing a fusion-path count to u64"
            })
        );
    }

    #[test]
    fn fusion_paths_of_mixed_words_and_targets() {
        let ring = FusionRing::ising().unwrap();
        // sigma sigma sigma sigma -> 1 : 2 paths; sigma psi sigma -> psi : 1 path.
        assert_eq!(
            ring.fusion_paths(&[1, 1, 1, 1], 0).unwrap(),
            BigUint::from(2u32)
        );
        assert_eq!(ring.fusion_paths(&[1, 2, 1], 2).unwrap(), BigUint::one());
        assert_eq!(ring.fusion_paths(&[1, 2, 1], 0).unwrap(), BigUint::one());
        assert_eq!(ring.fusion_paths(&[], 0).unwrap(), BigUint::one());
        assert_eq!(ring.fusion_paths(&[1], 0).unwrap(), BigUint::zero());
        assert!(ring.fusion_paths(&[1, 7], 0).is_err());
        assert!(ring.fusion_paths(&[1], 9).is_err());
    }

    #[test]
    fn the_catalog_rings_have_their_known_shape() {
        let fib = FusionRing::fibonacci().unwrap();
        assert_eq!(fib.fuse(1, 1).unwrap(), vec![0, 1]);
        assert_eq!(fib.dual(1), Ok(1));

        let toric = FusionRing::toric_code().unwrap();
        assert!(toric.is_pointed());
        assert_eq!(toric.fuse(1, 2).unwrap(), vec![3], "e x m = eps");
        assert_eq!(toric.dual(3), Ok(3));

        let z5 = FusionRing::z_n(5).unwrap();
        assert!(z5.is_pointed());
        assert_eq!(z5.dual(2), Ok(3));
        assert_eq!(z5.fuse(2, 4).unwrap(), vec![1]);

        // SU(2)_1 is the semion ring and SU(2)_2 the Ising ring.
        let semion = FusionRing::semion().unwrap();
        let su2_1 = FusionRing::su2_level(1).unwrap();
        assert_eq!(semion.table().n, su2_1.table().n);
        let su2_2 = FusionRing::su2_level(2).unwrap();
        assert_eq!(su2_2.table().n, FusionTable::ising().n);

        // SU(2)_3: the half-integer spin 3/2 (label 3) is the simple current; 3 x 3 = 0.
        let su2_3 = FusionRing::su2_level(3).unwrap();
        assert_eq!(su2_3.fuse(3, 3).unwrap(), vec![0]);
        assert_eq!(su2_3.fuse(1, 1).unwrap(), vec![0, 2]);
        assert_eq!(
            su2_3.fuse(2, 2).unwrap(),
            vec![0, 2],
            "truncation at level 3"
        );

        let s3 = FusionRing::rep_s3().unwrap();
        assert_eq!(s3.fuse(2, 2).unwrap(), vec![0, 1, 2]);
        assert_eq!(s3.fuse(1, 2).unwrap(), vec![2]);
        assert!(s3.is_commutative());

        assert!(matches!(
            FusionRing::su2_level(0),
            Err(FusionError::RankOutOfRange { .. })
        ));
        assert!(matches!(
            FusionRing::su2_level(MAX_RANK),
            Err(FusionError::RankOutOfRange { .. })
        ));
    }

    #[test]
    fn the_abelian_group_labels_are_mixed_radix_and_refuse_bad_input() {
        let group = AbelianGroup::new(&[2, 3]).unwrap();
        assert_eq!(group.order(), 6);
        assert_eq!(group.digits(5).unwrap(), vec![1, 2]);
        assert_eq!(group.label(&[1, 2]).unwrap(), 5);
        // 5 = (1, 2), 3 = (1, 1): the sum is (0, 0) and the negative of (1, 2) is (1, 1).
        assert_eq!(group.add(5, 3), Ok(0));
        assert_eq!(group.negate(5), Ok(3));
        assert!(group.digits(6).is_err());
        assert!(group.label(&[2, 0]).is_err());
        assert!(group.label(&[0]).is_err());
        assert!(AbelianGroup::new(&[1]).is_err());
        assert!(
            AbelianGroup::new(&[7, 7]).is_err(),
            "49 exceeds the maximum rank"
        );
    }

    #[test]
    fn frobenius_perron_dimensions_are_exact() {
        // Ising: d = (1, sqrt 2, 1), D^2 = 4.
        let ising = FusionRing::ising().unwrap();
        assert_eq!(
            ising.frobenius_perron_dimension(0).unwrap(),
            RealAlgebraic::Rational(rq(1, 1))
        );
        let sigma = ising.frobenius_perron_dimension(1).unwrap();
        let surd = sigma.as_quadratic().unwrap();
        assert_eq!(surd.radicand(), &BigInt::from(2));
        assert_eq!(surd.sqrt_part(), &rq(1, 1));
        assert_eq!(
            ising.frobenius_perron_dimension(2).unwrap(),
            RealAlgebraic::Rational(rq(1, 1))
        );
        assert_eq!(
            ising.global_dimension_squared().unwrap(),
            RealAlgebraic::Rational(rq(4, 1))
        );

        // Fibonacci: d = phi, D^2 = 1 + phi^2 = (5 + sqrt 5)/2.
        let fib = FusionRing::fibonacci().unwrap();
        let phi = fib.frobenius_perron_dimension(1).unwrap();
        let surd = phi.as_quadratic().unwrap();
        assert_eq!(surd.rational_part(), &rq(1, 2));
        assert_eq!(surd.radicand(), &BigInt::from(5));
        let d2 = fib.global_dimension_squared().unwrap();
        let surd = d2.as_quadratic().unwrap();
        assert_eq!(surd.rational_part(), &rq(5, 2));
        assert_eq!(surd.sqrt_part(), &rq(1, 2));
        assert_eq!(surd.radicand(), &BigInt::from(5));

        // A pointed ring has D^2 = order and every dimension 1.
        let toric = FusionRing::toric_code().unwrap();
        assert_eq!(
            toric.global_dimension_squared().unwrap(),
            RealAlgebraic::Rational(rq(4, 1))
        );
        // Rep(S_3): dimensions (1, 1, 2), D^2 = 6.
        let s3 = FusionRing::rep_s3().unwrap();
        assert_eq!(
            s3.frobenius_perron_dimension(2).unwrap(),
            RealAlgebraic::Rational(rq(2, 1))
        );
        assert_eq!(
            s3.global_dimension_squared().unwrap(),
            RealAlgebraic::Rational(rq(6, 1))
        );
        // SU(2)_4: d = (1, sqrt 3, 2, sqrt 3, 1), D^2 = 12.
        let su2_4 = FusionRing::su2_level(4).unwrap();
        let d1 = su2_4.frobenius_perron_dimension(1).unwrap();
        assert_eq!(d1.as_quadratic().unwrap().radicand(), &BigInt::from(3));
        assert_eq!(
            su2_4.frobenius_perron_dimension(2).unwrap(),
            RealAlgebraic::Rational(rq(2, 1))
        );
        assert_eq!(
            su2_4.global_dimension_squared().unwrap(),
            RealAlgebraic::Rational(rq(12, 1))
        );
        // SU(2)_5: d_1 = 2cos(pi/7) is a cubic irrational: only an isolated root.
        let su2_5 = FusionRing::su2_level(5).unwrap();
        let d1 = su2_5.frobenius_perron_dimension(1).unwrap();
        assert!(
            !d1.is_closed_form(),
            "2cos(pi/7) is not a quadratic surd: {d1}"
        );
        let enclosure = d1.enclosure(&rq(1, 1_000_000)).unwrap();
        // 2 cos(pi/7) = 1.8019377358...
        assert!(enclosure.lo() > &rq(18_019, 10_000) && enclosure.hi() < &rq(18_020, 10_000));
    }

    #[test]
    fn the_characteristic_polynomials_match_the_minimal_equations() {
        let fib = FusionRing::fibonacci().unwrap();
        assert_eq!(
            fib.characteristic_polynomial(1).unwrap(),
            vec![BigInt::from(-1), BigInt::from(-1), BigInt::from(1)]
        );
        let ising = FusionRing::ising().unwrap();
        assert_eq!(
            ising.characteristic_polynomial(1).unwrap(),
            vec![
                BigInt::from(0),
                BigInt::from(-2),
                BigInt::from(0),
                BigInt::from(1)
            ]
        );
    }
}
