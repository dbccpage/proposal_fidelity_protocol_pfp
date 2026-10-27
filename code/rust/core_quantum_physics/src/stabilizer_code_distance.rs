// AuthorityEffect: None.

//! Exact distance, syndromes and correction-radius certificates for declared
//! stabilizer codes, computed rather than declared.
//!
//! A stabilizer code on `n` qubits is fixed by pairwise commuting Pauli
//! generators `S`, phases dropped. With `r` the rank of `S` over `F_2`
//! (symplectic rows `[x | z]`, ranks from
//! `core_homology::f2::F2Matrix::rank`), it encodes `k = n - r` logical
//! qubits. Computed exactly:
//!
//! - the syndrome of an error, one bit per generator it anticommutes with, and
//!   membership of a Pauli string in the stabilizer group, up to phase;
//! - the distance over a declared single-qubit alphabet: the least weight of a
//!   string with zero syndrome outside the stabilizer group, by exhaustive
//!   search in increasing weight, so the first logical string met has minimum
//!   weight and the exhausted search below it is the lower bound. The alphabet
//!   `{X, Y, Z}` ([`StabilizerCode::distance`]) gives the code distance `d`;
//!   `{X}` alone gives the distance against bit flips;
//! - a minimum-weight lookup decoder (for each syndrome, the first string of
//!   least weight), and whether its correction returns an error to the
//!   stabilizer group;
//! - the correction radius `t = floor((d - 1) / 2)`, for an alphabet closed
//!   under products (one letter, or all three): only then is the product of two
//!   errors over the alphabet again a string over it, which the argument needs.
//!   Over `{X, Y}` the product `X Y = Z` leaves the alphabet, and the code
//!   `ZZI, IZZ` shows the radius would be wrong there;
//! - from a distance witness `L`, two errors of weights `ceil(d/2)` and
//!   `floor(d/2)` with equal syndromes whose product is `L`. No decoder
//!   corrects both, so no decoder corrects every error of weight `t + 1`.
//!
//! Every enumeration stops at a candidate budget ([`DEFAULT_CANDIDATE_BUDGET`]
//! unless one is passed) and is refused past it, never guessed.
//!
//! Refused: no generators, strings of zero or unequal length, anticommuting
//! generators, symbols other than `I, X, Y, Z`, an alphabet that is empty,
//! repeats a letter or contains `I`, a distance for a code without a logical
//! qubit, and a correction radius over an alphabet not closed under products. A
//! distance is a property of the declared generators; nothing here is a
//! threshold theorem or a statement about physical noise.
//!
//! Not PROVED. Not GlobalGreen.

use std::collections::BTreeMap;
use std::ops::ControlFlow;

use num_bigint::{BigInt, BigUint};
use num_traits::{One, Zero};
use core_combinatorics::enumeration::binomial;
use core_number_theory::gf2::{F2Matrix, F2Span, F2Vector};

use crate::pauli::{pauli_anticommutes, pauli_commutes, Pauli};

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; stabilizer code distance by exhaustive search.";

/// Candidates one search may examine before refusing.
pub const DEFAULT_CANDIDATE_BUDGET: usize = 1 << 20;

/// `X, Y, Z`: over this alphabet the distance is the code distance.
pub const FULL_ALPHABET: [Pauli; 3] = [Pauli::X, Pauli::Y, Pauli::Z];

/// Why a stabilizer code, an operator or a search was refused.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum StabilizerCodeError {
    /// No generators were given.
    #[error("at least one generator is required")]
    NoGenerators,
    #[error("stabilizer request exceeds the finite storage budget")]
    StorageBudget,
    #[error(transparent)]
    Combinatorics(#[from] core_combinatorics::enumeration::CombinatoricsError),
    #[error("region indices are repeated or outside the carrier")]
    Region,
    #[error("entropy requires a pure stabilizer state (rank n)")]
    NotPureState,
    #[error("signed stabilizers contain minus the identity or an anti-Hermitian generator")]
    InconsistentSigns,
    #[error("exact Pauli or GF(2) operation refused: {0}")]
    Algebra(String),
    /// The generators act on zero qubits.
    #[error("generators must act on at least one qubit")]
    ZeroQubits,
    /// Generator `index` has a different length from generator 0.
    #[error("generator {index} has length {actual}, expected {expected}")]
    RaggedGenerator {
        index: usize,
        expected: usize,
        actual: usize,
    },
    /// Generators `left` and `right` anticommute.
    #[error("generators {left} and {right} anticommute")]
    AnticommutingGenerators { left: usize, right: usize },
    /// An operator does not act on the code's qubits.
    #[error("an operator of length {actual} does not act on {expected} qubits")]
    LengthMismatch { expected: usize, actual: usize },
    /// A symbol of a Pauli string is not `I, X, Y, Z`.
    #[error("symbol {symbol:?} at position {index} is not one of I, X, Y, Z")]
    UnknownSymbol { index: usize, symbol: char },
    /// The alphabet is empty, repeats a letter or contains `I`.
    #[error("an alphabet needs one or more distinct letters from X, Y, Z")]
    BadAlphabet,
    /// A correction radius needs an alphabet closed under products.
    #[error("the alphabet is not closed under products (use one letter or all three)")]
    AlphabetNotClosed,
    /// `k = 0`: every operator commuting with `S` is in `S`, so no distance exists.
    #[error("the code has no logical qubit (n = {n}, rank = {rank})")]
    NoLogicalQubits { n: usize, rank: usize },
    /// The search reached its budget while examining operators of weight `weight`.
    #[error("candidate budget reached at weight {weight} after {candidates_checked} candidates")]
    CandidateBudgetExceeded {
        weight: usize,
        candidates_checked: usize,
    },
    /// No string over the alphabet up to weight `n` is a nontrivial logical operator.
    #[error("no logical operator over the alphabet ({candidates_checked} candidates checked)")]
    SearchExhausted { candidates_checked: usize },
}

/// Parse `I`, `X`, `Y`, `Z`; any other symbol is refused.
pub fn pauli_string(text: &str) -> Result<Vec<Pauli>, StabilizerCodeError> {
    text.chars()
        .enumerate()
        .map(|(index, symbol)| match symbol {
            'I' => Ok(Pauli::I),
            'X' => Ok(Pauli::X),
            'Y' => Ok(Pauli::Y),
            'Z' => Ok(Pauli::Z),
            _ => Err(StabilizerCodeError::UnknownSymbol { index, symbol }),
        })
        .collect()
}

/// Number of non-identity tensor factors.
pub fn pauli_weight(p: &[Pauli]) -> usize {
    p.iter().filter(|&&q| q != Pauli::I).count()
}

/// The qubitwise product, phases dropped.
pub fn product(a: &[Pauli], b: &[Pauli]) -> Result<Vec<Pauli>, StabilizerCodeError> {
    if a.len() != b.len() {
        return Err(StabilizerCodeError::LengthMismatch {
            expected: a.len(),
            actual: b.len(),
        });
    }
    Ok(a.iter().zip(b).map(|(&x, &y)| x.multiply(y)).collect())
}

fn check_alphabet(alphabet: &[Pauli]) -> Result<(), StabilizerCodeError> {
    let distinct = alphabet
        .iter()
        .enumerate()
        .all(|(i, a)| !alphabet[..i].contains(a));
    if alphabet.is_empty() || alphabet.contains(&Pauli::I) || !distinct {
        return Err(StabilizerCodeError::BadAlphabet);
    }
    Ok(())
}

/// Call `visit` on every string of length `n` with exactly `w` positions from
/// the alphabet and `I` elsewhere: supports in lexicographic order, then letters
/// in alphabet order with the last position fastest. Stops at the first `Break`.
fn for_each_string_of_weight<T>(
    n: usize,
    w: usize,
    alphabet: &[Pauli],
    mut visit: impl FnMut(&[Pauli]) -> ControlFlow<T>,
) -> Option<T> {
    if w > n {
        return None;
    }
    let mut support: Vec<usize> = (0..w).collect();
    let mut s = vec![Pauli::I; n];
    loop {
        let mut letters = vec![0usize; w];
        loop {
            s.fill(Pauli::I);
            for (&position, &letter) in support.iter().zip(&letters) {
                s[position] = alphabet[letter];
            }
            if let ControlFlow::Break(value) = visit(&s) {
                return Some(value);
            }
            let Some(slot) = letters.iter().rposition(|&l| l + 1 < alphabet.len()) else {
                break;
            };
            letters[slot] += 1;
            letters[slot + 1..].fill(0);
        }
        let Some(slot) = (0..w).rposition(|i| support[i] < n - w + i) else {
            return None;
        };
        support[slot] += 1;
        for i in slot + 1..w {
            support[i] = support[i - 1] + 1;
        }
    }
}

/// `C(n, w) letters^w`, the size of one weight class, or `None` when it does
/// not fit `usize`.
fn weight_class_size(n: usize, w: usize, letters: usize) -> Option<usize> {
    if w > n {
        return Some(0);
    }
    let mut binomial = 1usize;
    for i in 0..w {
        binomial = binomial.checked_mul(n - i)? / (i + 1);
    }
    binomial.checked_mul(letters.checked_pow(u32::try_from(w).ok()?)?)
}

/// Refuse, before enumerating, a set of weight classes larger than the budget.
fn check_enumeration(
    n: usize,
    weights: std::ops::RangeInclusive<usize>,
    letters: usize,
) -> Result<(), StabilizerCodeError> {
    let mut total = 0usize;
    for w in weights {
        total = weight_class_size(n, w, letters)
            .and_then(|size| total.checked_add(size))
            .filter(|&t| t <= DEFAULT_CANDIDATE_BUDGET)
            .ok_or(StabilizerCodeError::CandidateBudgetExceeded {
                weight: w,
                candidates_checked: 0,
            })?;
    }
    Ok(())
}

/// Every string of length `n` with exactly `w` positions from the alphabet and
/// `I` elsewhere, in the order of the searches here. There are
/// `C(n, w) |alphabet|^w` of them; weight `0` gives the identity alone. Refused,
/// before any is built, when that count exceeds [`DEFAULT_CANDIDATE_BUDGET`].
pub fn strings_of_weight(
    n: usize,
    w: usize,
    alphabet: &[Pauli],
) -> Result<Vec<Vec<Pauli>>, StabilizerCodeError> {
    check_alphabet(alphabet)?;
    check_enumeration(n, w..=w, alphabet.len())?;
    let mut strings = Vec::new();
    for_each_string_of_weight(n, w, alphabet, |s| -> ControlFlow<()> {
        strings.push(s.to_vec());
        ControlFlow::Continue(())
    });
    Ok(strings)
}

fn symplectic_row(p: &[Pauli]) -> Vec<u8> {
    let (xs, zs): (Vec<u8>, Vec<u8>) = p.iter().map(|q| q.symplectic_coords()).unzip();
    xs.into_iter().chain(zs).collect()
}

/// A stabilizer code: validated, pairwise commuting generators.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct StabilizerCode {
    n: usize,
    generators: Vec<Vec<Pauli>>,
    rows: Vec<Vec<u8>>,
    rank: usize,
    span: F2Span,
}

impl StabilizerCode {
    /// Accept generators acting on an explicit carrier length `n >= 1`.
    /// When `generators` is empty, produces a code with `0` generators,
    /// `rank = 0`, `k = n`, and distance `d = 1`.
    pub fn try_new_with_length(
        n: usize,
        generators: Vec<Vec<Pauli>>,
    ) -> Result<Self, StabilizerCodeError> {
        if n == 0 {
            return Err(StabilizerCodeError::ZeroQubits);
        }
        if n > 4096 {
            return Err(StabilizerCodeError::StorageBudget);
        }
        if generators.is_empty() {
            let span = F2Span::new(2 * n);
            return Ok(Self {
                n,
                generators: Vec::new(),
                rows: Vec::new(),
                rank: 0,
                span,
            });
        }
        for (index, g) in generators.iter().enumerate() {
            if g.len() != n {
                return Err(StabilizerCodeError::RaggedGenerator {
                    index,
                    expected: n,
                    actual: g.len(),
                });
            }
        }
        Self::try_new(generators)
    }

    /// Alias for try_new_with_length.
    pub fn with_carrier_length(
        n: usize,
        generators: Vec<Vec<Pauli>>,
    ) -> Result<Self, StabilizerCodeError> {
        Self::try_new_with_length(n, generators)
    }

    /// Accept generators that are non-empty, of one length `n >= 1`, and pairwise
    /// commuting. Dependent generators are allowed; `k` uses the rank.
    pub fn try_new(generators: Vec<Vec<Pauli>>) -> Result<Self, StabilizerCodeError> {
        let n = generators
            .first()
            .ok_or(StabilizerCodeError::NoGenerators)?
            .len();
        if n > 4096
            || generators.len() > 8192
            || n.checked_mul(generators.len()).is_none_or(|n| n > 1 << 22)
        {
            return Err(StabilizerCodeError::StorageBudget);
        }
        // Pairwise commutation is work on the declared generator list even
        // when every row is redundant; bound it before the quadratic loop.
        let commutation_work = generators
            .len()
            .checked_mul(generators.len().saturating_sub(1))
            .map(|pairs_twice| pairs_twice / 2)
            .and_then(|pairs| pairs.checked_mul(n));
        if commutation_work.is_none_or(|work| work > 1 << 26) {
            return Err(StabilizerCodeError::StorageBudget);
        }
        if n == 0 {
            return Err(StabilizerCodeError::ZeroQubits);
        }
        for (index, g) in generators.iter().enumerate() {
            if g.len() != n {
                return Err(StabilizerCodeError::RaggedGenerator {
                    index,
                    expected: n,
                    actual: g.len(),
                });
            }
        }
        for (left, a) in generators.iter().enumerate() {
            for (right, b) in generators.iter().enumerate().skip(left + 1) {
                if !pauli_commutes(a, b) {
                    return Err(StabilizerCodeError::AnticommutingGenerators { left, right });
                }
            }
        }
        let rows: Vec<Vec<u8>> = generators.iter().map(|g| symplectic_row(g)).collect();
        let mut span = F2Span::new(2 * n);
        for row in &rows {
            span.insert(
                &F2Vector::from_bits(row)
                    .map_err(|e| StabilizerCodeError::Algebra(e.to_string()))?,
            )
            .map_err(|e| StabilizerCodeError::Algebra(e.to_string()))?;
        }
        let rank = span.dimension();
        Ok(Self {
            n,
            generators,
            rows,
            rank,
            span,
        })
    }

    /// Physical qubits.
    pub fn n(&self) -> usize {
        self.n
    }

    /// Rank of the generators over `F_2`: the number of independent stabilizers.
    pub fn rank(&self) -> usize {
        self.rank
    }

    /// Logical qubits, `n - rank`.
    pub fn k(&self) -> usize {
        self.n - self.rank
    }

    pub fn generators(&self) -> &[Vec<Pauli>] {
        &self.generators
    }

    fn check_length(&self, p: &[Pauli]) -> Result<(), StabilizerCodeError> {
        if p.len() != self.n {
            return Err(StabilizerCodeError::LengthMismatch {
                expected: self.n,
                actual: p.len(),
            });
        }
        Ok(())
    }

    /// Bit `i` is `1` when the error anticommutes with generator `i`.
    pub fn syndrome(&self, error: &[Pauli]) -> Result<Vec<u8>, StabilizerCodeError> {
        self.check_length(error)?;
        Ok(self
            .generators
            .iter()
            .map(|g| u8::from(pauli_anticommutes(g, error)))
            .collect())
    }

    /// Whether `p` is a product of generators, up to phase: adding it does not
    /// raise the rank.
    pub fn in_stabilizer_group(&self, p: &[Pauli]) -> Result<bool, StabilizerCodeError> {
        self.check_length(p)?;
        self.span
            .contains(
                &F2Vector::from_bits(&symplectic_row(p))
                    .map_err(|e| StabilizerCodeError::Algebra(e.to_string()))?,
            )
            .map_err(|e| StabilizerCodeError::Algebra(e.to_string()))
    }

    /// `p` is a nontrivial logical operator: it commutes with every generator
    /// and is not a stabilizer.
    pub fn is_logical(&self, p: &[Pauli]) -> Result<bool, StabilizerCodeError> {
        self.check_length(p)?;
        Ok(self.generators.iter().all(|g| pauli_commutes(g, p)) && !self.in_stabilizer_group(p)?)
    }

    /// The code distance: [`StabilizerCode::distance_over`] the alphabet
    /// `{X, Y, Z}` with [`DEFAULT_CANDIDATE_BUDGET`].
    pub fn distance(&self) -> Result<CodeDistance, StabilizerCodeError> {
        self.distance_over(&FULL_ALPHABET, DEFAULT_CANDIDATE_BUDGET)
    }

    /// The least weight of a nontrivial logical string over `alphabet`, by
    /// exhaustive search in increasing weight, refused once `budget` candidates
    /// have been examined.
    pub fn distance_over(
        &self,
        alphabet: &[Pauli],
        budget: usize,
    ) -> Result<CodeDistance, StabilizerCodeError> {
        check_alphabet(alphabet)?;
        if self.k() == 0 {
            return Err(StabilizerCodeError::NoLogicalQubits {
                n: self.n,
                rank: self.rank,
            });
        }
        let mut checked = 0usize;
        for weight in 1..=self.n {
            let lighter = checked;
            let found = for_each_string_of_weight(self.n, weight, alphabet, |s| {
                if checked == budget {
                    return ControlFlow::Break(Err(StabilizerCodeError::CandidateBudgetExceeded {
                        weight,
                        candidates_checked: checked,
                    }));
                }
                checked += 1;
                match self.is_logical(s) {
                    Ok(true) => ControlFlow::Break(Ok(s.to_vec())),
                    Ok(false) => ControlFlow::Continue(()),
                    Err(e) => ControlFlow::Break(Err(e)),
                }
            });
            match found {
                Some(Ok(witness)) => {
                    return Ok(CodeDistance {
                        distance: weight,
                        witness,
                        alphabet: alphabet.to_vec(),
                        candidates_checked: checked,
                        lighter_candidates_checked: lighter,
                    })
                }
                Some(Err(e)) => return Err(e),
                None => {}
            }
        }
        Err(StabilizerCodeError::SearchExhausted {
            candidates_checked: checked,
        })
    }

    /// For every syndrome of a string of weight at most `max_weight` over the
    /// alphabet, the first such string of least weight. Refused, before any
    /// string is built, when there are more than [`DEFAULT_CANDIDATE_BUDGET`].
    pub fn minimum_weight_decoder(
        &self,
        max_weight: usize,
        alphabet: &[Pauli],
    ) -> Result<LookupDecoder, StabilizerCodeError> {
        check_alphabet(alphabet)?;
        let top = max_weight.min(self.n);
        check_enumeration(self.n, 0..=top, alphabet.len())?;
        let mut table = BTreeMap::new();
        for weight in 0..=top {
            let refused =
                for_each_string_of_weight(self.n, weight, alphabet, |s| match self.syndrome(s) {
                    Ok(syndrome) => {
                        table.entry(syndrome).or_insert_with(|| s.to_vec());
                        ControlFlow::Continue(())
                    }
                    Err(e) => ControlFlow::Break(e),
                });
            if let Some(e) = refused {
                return Err(e);
            }
        }
        Ok(LookupDecoder { table })
    }

    /// `Some(true)` when the decoder's correction times the error lies in the
    /// stabilizer group; `None` when the decoder has no entry for the syndrome.
    pub fn is_corrected(
        &self,
        decoder: &LookupDecoder,
        error: &[Pauli],
    ) -> Result<Option<bool>, StabilizerCodeError> {
        let syndrome = self.syndrome(error)?;
        match decoder.correction(&syndrome) {
            None => Ok(None),
            Some(correction) => Ok(Some(
                self.in_stabilizer_group(&product(correction, error)?)?,
            )),
        }
    }

    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

/// Result of a distance search: the distance, a logical operator of that
/// weight, the alphabet, and how many candidates the search examined.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodeDistance {
    distance: usize,
    witness: Vec<Pauli>,
    alphabet: Vec<Pauli>,
    candidates_checked: usize,
    lighter_candidates_checked: usize,
}

impl CodeDistance {
    pub fn distance(&self) -> usize {
        self.distance
    }

    /// The first nontrivial logical string of least weight.
    pub fn witness(&self) -> &[Pauli] {
        &self.witness
    }

    /// The alphabet the search ran over.
    pub fn alphabet(&self) -> &[Pauli] {
        &self.alphabet
    }

    /// Every candidate examined, the witness included.
    pub fn candidates_checked(&self) -> usize {
        self.candidates_checked
    }

    /// The candidates of weight below the distance, all found harmless or
    /// detected: the evidence for the lower bound.
    pub fn lighter_candidates_checked(&self) -> usize {
        self.lighter_candidates_checked
    }

    /// `t = floor((d - 1) / 2)`, for an alphabet closed under products (one
    /// letter, or all three); refused otherwise.
    pub fn correction_radius(&self) -> Result<usize, StabilizerCodeError> {
        if self.alphabet.len() == 2 {
            return Err(StabilizerCodeError::AlphabetNotClosed);
        }
        Ok((self.distance - 1) / 2)
    }

    /// The witness split into its first `ceil(d/2)` and remaining support
    /// positions: equal syndromes, product equal to the witness.
    pub fn uncorrectable_pair(&self) -> (Vec<Pauli>, Vec<Pauli>) {
        let support: Vec<usize> = (0..self.witness.len())
            .filter(|&q| self.witness[q] != Pauli::I)
            .collect();
        let half = support.len().div_ceil(2);
        let mut first = vec![Pauli::I; self.witness.len()];
        let mut second = first.clone();
        for (rank, &q) in support.iter().enumerate() {
            if rank < half {
                first[q] = self.witness[q];
            } else {
                second[q] = self.witness[q];
            }
        }
        (first, second)
    }
}

/// A syndrome-indexed table of corrections.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct LookupDecoder {
    table: BTreeMap<Vec<u8>, Vec<Pauli>>,
}

impl LookupDecoder {
    pub fn correction(&self, syndrome: &[u8]) -> Option<&[Pauli]> {
        self.table.get(syndrome).map(Vec::as_slice)
    }

    /// The number of syndromes with an entry.
    pub fn syndrome_count(&self) -> usize {
        self.table.len()
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/stabilizer_code_distance.rs
// Claim: urn:core:crates_rs:core-quantum-physics:stabilizer-code-distance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn code(generators: &[&str]) -> Result<StabilizerCode, StabilizerCodeError> {
        StabilizerCode::try_new(
            generators
                .iter()
                .map(|g| pauli_string(g))
                .collect::<Result<_, _>>()?,
        )
    }

    fn assert_nkd(generators: &[&str], n: usize, k: usize, d: usize) {
        let c = code(generators).unwrap();
        assert_eq!((c.n(), c.k()), (n, k));
        let dist = c.distance().unwrap();
        assert_eq!(dist.distance(), d);
        assert_eq!(pauli_weight(dist.witness()), d);
        assert!(c.is_logical(dist.witness()).unwrap());
    }

    const SHOR: [&str; 8] = [
        "ZZIIIIIII",
        "IZZIIIIII",
        "IIIZZIIII",
        "IIIIZZIII",
        "IIIIIIZZI",
        "IIIIIIIZZ",
        "XXXXXXIII",
        "IIIXXXXXX",
    ];

    #[test]
    fn shor_code_is_9_1_3() {
        assert_nkd(&SHOR, 9, 1, 3);
    }

    #[test]
    fn four_qubit_css_code_is_4_2_2() {
        assert_nkd(&["XXXX", "ZZZZ"], 4, 2, 2);
    }

    #[test]
    fn steane_code_is_7_1_3() {
        assert_nkd(
            &[
                "IIIXXXX", "IXXIIXX", "XIXIXIX", "IIIZZZZ", "IZZIIZZ", "ZIZIZIZ",
            ],
            7,
            1,
            3,
        );
    }

    #[test]
    fn five_qubit_code_is_5_1_3() {
        assert_nkd(&["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"], 5, 1, 3);
    }

    /// Anti-vacuity: the three-qubit bit-flip code has distance 1 as a quantum code
    /// (a single `Z` is logical), so the search does not return a constant.
    #[test]
    fn bit_flip_code_has_distance_one() {
        assert_nkd(&["ZZI", "IZZ"], 3, 1, 1);
    }

    /// Dependent generators: `YYYY = XXXX · ZZZZ` adds nothing, and `k` follows the rank.
    #[test]
    fn dependent_generators_use_the_rank() {
        let c = code(&["XXXX", "ZZZZ", "YYYY"]).unwrap();
        assert_eq!((c.rank(), c.k()), (2, 2));
        assert!(c.in_stabilizer_group(&[Pauli::Y; 4]).unwrap());
        assert_eq!(c.distance().unwrap().distance(), 2);
    }

    /// Stabilizers are not logical operators, even though they commute with `S`.
    #[test]
    fn stabilizers_are_excluded_from_the_search() {
        let c = code(&SHOR).unwrap();
        let block = pauli_string("XXXXXXIII").unwrap();
        assert!(c.in_stabilizer_group(&block).unwrap());
        assert!(!c.is_logical(&block).unwrap());
        // Logical Z of the Shor code has weight 3.
        let z_l = pauli_string("ZIIZIIZII").unwrap();
        assert!(c.is_logical(&z_l).unwrap());
    }

    #[test]
    fn refusals_are_typed() {
        assert_eq!(
            StabilizerCode::try_new(vec![]),
            Err(StabilizerCodeError::NoGenerators)
        );
        assert_eq!(
            StabilizerCode::try_new(vec![vec![Pauli::I; 128]; 1025]),
            Err(StabilizerCodeError::StorageBudget)
        );
        assert_eq!(code(&[""]), Err(StabilizerCodeError::ZeroQubits));
        assert_eq!(
            code(&["XX", "Z"]),
            Err(StabilizerCodeError::RaggedGenerator {
                index: 1,
                expected: 2,
                actual: 1
            })
        );
        assert_eq!(
            code(&["XI", "ZI"]),
            Err(StabilizerCodeError::AnticommutingGenerators { left: 0, right: 1 })
        );
        // The Bell stabilizer XX, ZZ encodes nothing.
        assert_eq!(
            code(&["XX", "ZZ"]).unwrap().distance(),
            Err(StabilizerCodeError::NoLogicalQubits { n: 2, rank: 2 })
        );
        // Shor's 27 weight-one candidates are all detected; a budget of 10 stops early.
        assert_eq!(
            code(&SHOR).unwrap().distance_over(&FULL_ALPHABET, 10),
            Err(StabilizerCodeError::CandidateBudgetExceeded {
                weight: 1,
                candidates_checked: 10
            })
        );
        // An operator of the wrong length is refused, not called trivial.
        assert_eq!(
            code(&SHOR).unwrap().in_stabilizer_group(&[Pauli::X]),
            Err(StabilizerCodeError::LengthMismatch {
                expected: 9,
                actual: 1
            })
        );
    }

    /// Over `{X, Y}` the bit-flip code has distance 3, but `XII` and `YII` share
    /// a syndrome and their product `ZII` is logical, so a radius of 1 would be
    /// wrong: the radius is refused for an alphabet not closed under products.
    #[test]
    fn correction_radius_needs_a_product_closed_alphabet() {
        let c = code(&["ZZI", "IZZ"]).unwrap();
        let two_letters = c
            .distance_over(&[Pauli::X, Pauli::Y], DEFAULT_CANDIDATE_BUDGET)
            .unwrap();
        assert_eq!(two_letters.distance(), 3);
        assert_eq!(
            two_letters.correction_radius(),
            Err(StabilizerCodeError::AlphabetNotClosed)
        );
        let (x, y) = (pauli_string("XII").unwrap(), pauli_string("YII").unwrap());
        assert_eq!(c.syndrome(&x).unwrap(), c.syndrome(&y).unwrap());
        assert!(c.is_logical(&product(&x, &y).unwrap()).unwrap());
        // Over {X} alone the radius is sound, and over {X, Y, Z} it is 0 here.
        assert_eq!(
            c.distance_over(&[Pauli::X], DEFAULT_CANDIDATE_BUDGET)
                .unwrap()
                .correction_radius(),
            Ok(1)
        );
        assert_eq!(c.distance().unwrap().correction_radius(), Ok(0));
    }

    /// Enumerations are budgeted: a weight class larger than the budget is
    /// refused before it is built.
    #[test]
    fn large_weight_classes_are_refused() {
        // C(40, 5) 3^5 = 159,895,944 strings.
        assert_eq!(
            strings_of_weight(40, 5, &FULL_ALPHABET),
            Err(StabilizerCodeError::CandidateBudgetExceeded {
                weight: 5,
                candidates_checked: 0
            })
        );
        assert_eq!(strings_of_weight(9, 2, &FULL_ALPHABET).unwrap().len(), 324);
        let bit_flip_20: Vec<Vec<Pauli>> = (0..19)
            .map(|i| {
                (0..20)
                    .map(|q| {
                        if q == i || q == i + 1 {
                            Pauli::Z
                        } else {
                            Pauli::I
                        }
                    })
                    .collect()
            })
            .collect();
        let c = StabilizerCode::try_new(bit_flip_20).unwrap();
        assert!(matches!(
            c.minimum_weight_decoder(20, &[Pauli::X, Pauli::Y]),
            Err(StabilizerCodeError::CandidateBudgetExceeded { .. })
        ));
    }

    #[test]
    fn authority_fence_is_none() {
        assert!(StabilizerCode::authority_fence().contains("AuthorityEffect None"));
    }
}

fn f2_error(e: impl std::fmt::Display) -> StabilizerCodeError {
    StabilizerCodeError::Algebra(e.to_string())
}
fn from_symplectic(row: &F2Vector) -> Vec<Pauli> {
    let bits = row.to_bits();
    let n = bits.len() / 2;
    (0..n)
        .map(|i| match (bits[i], bits[n + i]) {
            (0, 0) => Pauli::I,
            (1, 0) => Pauli::X,
            (0, 1) => Pauli::Z,
            _ => Pauli::Y,
        })
        .collect()
}
fn symplectic_pair(a: &F2Vector, b: &F2Vector) -> u8 {
    let a = a.to_bits();
    let b = b.to_bits();
    let n = a.len() / 2;
    (0..n).fold(0, |value, i| value ^ (a[i] & b[n + i]) ^ (a[n + i] & b[i]))
}
impl StabilizerCode {
    /// S(A)=rank(G_A)-|A| bits for a pure stabilizer state. Signs do not
    /// change its reduced spectrum; a signed physical state can be validated below.
    pub fn entropy(&self, region: &[usize]) -> Result<usize, StabilizerCodeError> {
        if self.k() != 0 {
            return Err(StabilizerCodeError::NotPureState);
        }
        let mut sorted = region.to_vec();
        sorted.sort_unstable();
        if sorted.iter().any(|&q| q >= self.n) || sorted.windows(2).any(|w| w[0] == w[1]) {
            return Err(StabilizerCodeError::Region);
        }
        let restricted: Vec<Vec<u8>> = self
            .rows
            .iter()
            .map(|g| {
                region
                    .iter()
                    .map(|&i| g[i])
                    .chain(region.iter().map(|&i| g[self.n + i]))
                    .collect()
            })
            .collect();
        let rank = F2Matrix::from_rows(&restricted).map_err(f2_error)?.rank();
        rank.checked_sub(region.len())
            .ok_or(StabilizerCodeError::NotPureState)
    }
    fn orthogonalize_symplectic_quotient(
        quotient: &mut [F2Vector],
        x: &F2Vector,
        z: &F2Vector,
    ) -> Result<(), StabilizerCodeError> {
        for w in quotient {
            let wx = symplectic_pair(w, x);
            let wz = symplectic_pair(w, z);
            if wz == 1 {
                w.add_assign(x).map_err(f2_error)?;
            }
            if wx == 1 {
                w.add_assign(z).map_err(f2_error)?;
            }
        }
        Ok(())
    }
    /// Symplectic Gram-Schmidt on the centralizer modulo stabilizers.
    pub fn logical_pairs(&self) -> Result<Vec<(Vec<Pauli>, Vec<Pauli>)>, StabilizerCodeError> {
        let rows: Vec<Vec<u8>> = self
            .rows
            .iter()
            .map(|r| r[self.n..].iter().chain(&r[..self.n]).copied().collect())
            .collect();
        let normalizer = F2Matrix::from_rows(&rows).map_err(f2_error)?.nullspace();
        let mut span = self.span.clone();
        let mut quotient = Vec::new();
        for v in normalizer {
            if span.insert(&v).map_err(f2_error)? {
                quotient.push(v);
            }
        }
        let mut pairs = Vec::new();
        while let Some(x) = quotient.pop() {
            let partner = quotient
                .iter()
                .position(|z| symplectic_pair(&x, z) == 1)
                .ok_or_else(|| f2_error("degenerate quotient symplectic form"))?;
            let z = quotient.remove(partner);
            Self::orthogonalize_symplectic_quotient(&mut quotient, &x, &z)?;
            pairs.push((from_symplectic(&x), from_symplectic(&z)));
        }
        Ok(pairs)
    }
    fn enumerate_basis_weights(
        &self,
        budget: usize,
        basis: &[F2Vector],
    ) -> Result<Vec<BigUint>, StabilizerCodeError> {
        let count = 1usize
            .checked_shl(
                u32::try_from(basis.len()).map_err(|_| StabilizerCodeError::StorageBudget)?,
            )
            .ok_or(StabilizerCodeError::StorageBudget)?;
        if count > budget {
            return Err(StabilizerCodeError::StorageBudget);
        }
        let mut result = vec![BigUint::zero(); self.n + 1];
        for mask in 0..count {
            let mut v = F2Vector::zeros(2 * self.n).map_err(f2_error)?;
            for (i, b) in basis.iter().enumerate() {
                if mask & (1usize << i) != 0 {
                    v.add_assign(b).map_err(f2_error)?;
                }
            }
            result[pauli_weight(&from_symplectic(&v))] += BigUint::one();
        }
        Ok(result)
    }
    /// Exact stabilizer and normalizer weight enumerators under the caller budget.
    pub fn weight_enumerators(
        &self,
        budget: usize,
    ) -> Result<(Vec<BigUint>, Vec<BigUint>), StabilizerCodeError> {
        if budget > DEFAULT_CANDIDATE_BUDGET {
            return Err(StabilizerCodeError::StorageBudget);
        }
        let s = F2Matrix::from_rows(&self.rows)
            .map_err(f2_error)?
            .row_space_basis();
        let rows: Vec<Vec<u8>> = self
            .rows
            .iter()
            .map(|r| r[self.n..].iter().chain(&r[..self.n]).copied().collect())
            .collect();
        let normalizer = F2Matrix::from_rows(&rows).map_err(f2_error)?.nullspace();
        Ok((
            self.enumerate_basis_weights(budget, &s)?,
            self.enumerate_basis_weights(budget, &normalizer)?,
        ))
    }
    /// Quantum Hamming inequality for a nondegenerate code; this is only the
    /// arithmetic bound and does not assert that this code is nondegenerate.
    pub fn nondegenerate_hamming_bound(
        &self,
        distance: usize,
    ) -> Result<bool, StabilizerCodeError> {
        if distance == 0 || distance > self.n {
            return Err(StabilizerCodeError::Region);
        }
        let t = (distance - 1) / 2;
        let mut sum = BigUint::zero();
        for j in 0..=t {
            sum += binomial(self.n as u64, j as u64)? * BigUint::from(3u32).pow(j as u32);
        }
        Ok(sum <= (BigUint::one() << self.rank))
    }
    pub fn singleton_bound(&self, distance: usize) -> Result<bool, StabilizerCodeError> {
        if distance == 0 || distance > self.n {
            return Err(StabilizerCodeError::Region);
        }
        Ok(self.rank >= 2 * (distance - 1))
    }
    fn accumulate_krawtchouk_row(
        &self,
        i: usize,
        a: &BigUint,
        transformed: &mut [BigInt],
    ) -> Result<(), StabilizerCodeError> {
        let a = BigInt::from(a.clone());
        let mut previous = BigInt::zero();
        let mut current = BigInt::one();
        for w in 0..=self.n {
            transformed[w] += &a * &current;
            if w < self.n {
                let numerator = BigInt::from(3 * self.n as i64 - 4 * i as i64 - 2 * w as i64)
                    * &current
                    - BigInt::from(3 * (self.n - w + 1)) * &previous;
                let divisor = BigInt::from(w + 1);
                if &numerator % &divisor != BigInt::zero() {
                    return Err(f2_error("nonintegral Krawtchouk recurrence"));
                }
                previous = current;
                current = numerator / divisor;
            }
        }
        Ok(())
    }
    /// MacWilliams transform B_w=|S|^-1 sum_i A_i K_w(i;n), checked for integrality.
    pub fn macwilliams_normalizer(
        &self,
        stabilizer: &[BigUint],
    ) -> Result<Vec<BigUint>, StabilizerCodeError> {
        if stabilizer.len() != self.n + 1 {
            return Err(StabilizerCodeError::Region);
        }
        let size = BigInt::one() << self.rank;
        let mut transformed = vec![BigInt::zero(); self.n + 1];
        // The q=4 Krawtchouk recurrence computes every K_w(i;n) in
        // O(n) work per nonzero input coefficient, rather than a cubic sum:
        // (w+1)K_(w+1)=(3n-4i-2w)K_w-3(n-w+1)K_(w-1).
        for (i, a) in stabilizer.iter().enumerate() {
            if !a.is_zero() {
                self.accumulate_krawtchouk_row(i, a, &mut transformed)?;
            }
        }
        let mut result = Vec::with_capacity(self.n + 1);
        for sum in transformed {
            if &sum % &size != BigInt::zero() {
                return Err(f2_error("nonintegral MacWilliams transform"));
            }
            result.push(
                (sum / &size)
                    .to_biguint()
                    .ok_or_else(|| f2_error("negative weight enumerator"))?,
            );
        }
        Ok(result)
    }
}
/// A signed physical stabilizer state. The older code API explicitly drops
/// phases; this separate constructor checks the full group before using it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SignedStabilizerState {
    code: StabilizerCode,
    generators: Vec<crate::pauli::PauliString>,
}
impl SignedStabilizerState {
    fn verify_dependent_generator_phase(
        n: usize,
        g: &crate::pauli::PauliString,
        bits: &[u8],
        independent: &[crate::pauli::PauliString],
    ) -> Result<(), StabilizerCodeError> {
        let mut product = crate::pauli::PauliString::new(vec![Pauli::I; n]).map_err(f2_error)?;
        for (i, &bit) in bits.iter().enumerate() {
            if bit == 1 {
                product = product.multiply(&independent[i]).map_err(f2_error)?;
            }
        }
        if product.phase() != g.phase() {
            return Err(StabilizerCodeError::InconsistentSigns);
        }
        Ok(())
    }
    pub fn new(generators: Vec<crate::pauli::PauliString>) -> Result<Self, StabilizerCodeError> {
        let code =
            StabilizerCode::try_new(generators.iter().map(|g| g.letters().to_vec()).collect())?;
        if code.k() != 0 {
            return Err(StabilizerCodeError::NotPureState);
        }
        let n = code.n;
        let mut independent = Vec::<crate::pauli::PauliString>::new();
        let mut columns = Vec::new();
        for g in &generators {
            if g.phase() % 2 != 0 {
                return Err(StabilizerCodeError::InconsistentSigns);
            }
            let v = F2Vector::from_bits(&symplectic_row(g.letters())).map_err(f2_error)?;
            let map = F2Matrix::from_columns(2 * n, &columns).map_err(f2_error)?;
            if let Some(solution) = map.solve(&v).map_err(f2_error)? {
                Self::verify_dependent_generator_phase(
                    n,
                    g,
                    &solution.particular().to_bits(),
                    &independent,
                )?;
            } else {
                columns.push(v);
                independent.push(g.clone());
            }
        }
        let out = Self { code, generators };
        Ok(out)
    }
    pub fn code(&self) -> &StabilizerCode {
        &self.code
    }
    pub fn generators(&self) -> &[crate::pauli::PauliString] {
        &self.generators
    }
    pub fn entropy(&self, region: &[usize]) -> Result<usize, StabilizerCodeError> {
        self.code.entropy(region)
    }
}
#[cfg(test)]
mod enrichment_tests {
    use super::*;
    #[test]
    fn signed_stabilizer_states_refuse_minus_identity_and_compute_bell_entropy() {
        let words = ["XX", "YY", "ZZ"].map(|w| crate::pauli::PauliString::parse(w).unwrap());
        assert_eq!(
            SignedStabilizerState::new(words.to_vec()),
            Err(StabilizerCodeError::InconsistentSigns)
        );
        let bell = SignedStabilizerState::new(vec![words[0].clone(), words[2].clone()]).unwrap();
        assert_eq!(bell.entropy(&[0]).unwrap(), 1);
        assert_eq!(bell.entropy(&[0, 1]).unwrap(), 0);
    }
    #[test]
    fn five_qubit_weight_enumerators_obey_macwilliams_and_coding_bounds() {
        let c = StabilizerCode::try_new(
            ["XZZXI", "IXZZX", "XIXZZ", "ZXIXZ"]
                .map(|w| pauli_string(w).unwrap())
                .to_vec(),
        )
        .unwrap();
        let (a, b) = c.weight_enumerators(1024).unwrap();
        assert_eq!(
            a.iter().map(|x| x.to_string()).collect::<Vec<_>>(),
            ["1", "0", "0", "0", "15", "0"]
        );
        assert_eq!(
            b.iter().map(|x| x.to_string()).collect::<Vec<_>>(),
            ["1", "0", "0", "30", "15", "18"]
        );
        assert_eq!(c.macwilliams_normalizer(&a).unwrap(), b);
        assert!(c.nondegenerate_hamming_bound(3).unwrap());
        assert!(c.singleton_bound(3).unwrap());
        let logical = c.logical_pairs().unwrap();
        assert_eq!(logical.len(), 1);
        assert!(pauli_anticommutes(&logical[0].0, &logical[0].1));
        assert!(c.is_logical(&logical[0].0).unwrap());
    }

    #[test]
    fn macwilliams_recurrence_matches_full_pauli_weight_counts_beyond_small_code_search() {
        let n = 64;
        let trivial = StabilizerCode::try_new(vec![vec![Pauli::I; n]]).unwrap();
        let mut identity_enumerator = vec![BigUint::zero(); n + 1];
        identity_enumerator[0] = BigUint::one();
        let all_paulis = trivial
            .macwilliams_normalizer(&identity_enumerator)
            .unwrap();
        for (w, count) in all_paulis.iter().enumerate() {
            assert_eq!(
                *count,
                binomial(n as u64, w as u64).unwrap() * BigUint::from(3u32).pow(w as u32)
            );
        }
        assert_eq!(
            all_paulis.iter().sum::<BigUint>(),
            BigUint::one() << (2 * n)
        );
        let nontrivial = StabilizerCode::try_new(vec![pauli_string("ZZ").unwrap()]).unwrap();
        assert!(nontrivial
            .macwilliams_normalizer(&[1u32.into(), 0u32.into(), 0u32.into()])
            .is_err());
    }
}
