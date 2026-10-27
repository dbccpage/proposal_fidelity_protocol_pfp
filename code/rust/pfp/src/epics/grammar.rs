//! Incremental token frontiers and grammar-aligned decoding.
//!
//! `EPIC-OE-SYMGAM-003` asks for a token trie with dynamic masking, Expected
//! Future Grammaticality over a finite horizon, and a frontier receipt carrying
//! the legal support width and a constraint compression ratio.
//!
//! # Lookup cost is measured, not asserted
//!
//! Acceptance criterion 4 requires that lookup step counts be *recorded* over
//! vocabularies from 2^10 to 2^16 and shown to grow within a logarithmic bound
//! -- and that a miss be recorded as a residual rather than omitted.
//!
//! So the descent counts its own comparisons. Children are held in a sorted
//! `Vec` and searched by a hand-written binary search that increments a counter
//! on every key comparison, rather than by `BTreeMap`, whose internal
//! comparison count is not observable. The cost is then a measurement the tests
//! can bound, not a complexity class quoted in a doc comment.
//!
//! A lookup that fails still returns its step count. Omitting the misses would
//! bias the measurement toward the cheap cases, which is precisely the residual
//! the criterion asks to be kept.
//!
//! # No float can enter the scoring
//!
//! Criterion 2 requires Expected Future Grammaticality to be an exact rational
//! lower bound, and says the scoring type must admit no 64-bit float. It is
//! `Ratio<i64>` throughout, and `the_module_contains_no_floating_point_type`
//! asserts the absence at the source level -- because a type-level guarantee
//! that holds only until someone writes one float cast is a convention, not a
//! gate.
//!
//! That test scans the implementation half of this file for the two Rust
//! floating-point type names. Which is why this paragraph does not spell them:
//! a source-level ban has to exclude the text that states the ban, and the
//! cheapest way to exclude the prose is not to write the token in it.
//!
//! # What is not built here
//!
//! Deliverable 4 asks to "expose fast mask vector generation via PyO3". This
//! module does not.
//!
//! This crate has no `pyo3` dependency. Two crates in the
//! workspace do -- `core_mub` and `core_operad_theory` -- and in both it is
//! **optional**, behind a `python` feature, so the default build has no
//! in-process Python linkage at all. `CLAUDE.md` states the Python-to-Rust seam
//! is a subprocess and not FFI, governed by `RULE_FFI_SEAM_ISOLATION_001`.
//!
//! More decisively: **`EPIC-OE-SYMGAM-009` is "PyO3 Clean Architecture Seam
//! Lowering"** -- an entire epic whose subject is how this seam should be
//! shaped. Adding an ad-hoc `#[pyfunction]` here would pre-empt that epic's
//! architecture decision and create the second native rail that
//! `EPIC-OE-OEWAS-RUST-001`'s migration doctrine 7 forbids.
//!
//! The mask is therefore produced as a plain `Vec<bool>` with a stable bit
//! order, which is the object any seam would carry. Criterion 5 -- that the
//! PyO3 mask be bit-identical to the native one -- is deferred with it.
//!
//! `AuthorityEffect: None`. A frontier receipt records what was admissible. It
//! does not decide what should be generated.

use std::collections::BTreeSet;

use num_rational::Ratio;
use serde::{Deserialize, Serialize};
use thiserror::Error;

/// A token identifier. Dense and small, because it indexes the mask vector.
pub type TokenId = u32;

/// The receipt schema this module emits.
pub const FRONTIER_RECEIPT_SCHEMA_V1: &str = "core.symgam.token-frontier-receipt.v1";

#[derive(Debug, Clone, PartialEq, Eq, Error)]
pub enum GrammarError {
    #[error("the grammar admits no sentences; an empty language masks everything")]
    EmptyGrammar,

    #[error("sentence {index} is empty; a grammar cannot admit the empty sentence")]
    EmptySentence { index: usize },

    #[error("token {token} is outside the declared vocabulary of {vocabulary_size}")]
    TokenOutsideVocabulary {
        token: TokenId,
        vocabulary_size: usize,
    },

    #[error("a vocabulary of zero tokens cannot be masked")]
    EmptyVocabulary,

    #[error("probability for token {token} is negative; c(h) is a sum of measures")]
    NegativeProbability { token: TokenId },
}

// ---------------------------------------------------------------------------
// The trie
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Default)]
struct TrieNode {
    /// Sorted by token id, so the descent can binary-search and count its own
    /// comparisons. A `BTreeMap` would be tidier and would hide the count.
    children: Vec<(TokenId, usize)>,
    terminal: bool,
}

/// An incremental prefix index over the sentences a grammar admits.
#[derive(Debug, Clone)]
pub struct TokenTrieIndex {
    nodes: Vec<TrieNode>,
    vocabulary_size: usize,
    sentence_count: usize,
}

/// What a descent cost, alongside what it found.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Descent {
    /// The node the prefix reaches, if the prefix is itself admissible.
    node: Option<usize>,
    /// Key comparisons performed. Recorded for hits **and** misses.
    pub comparisons: u64,
    /// True when the prefix left the trie -- a residual, kept rather than
    /// dropped, so a cost measurement is not biased toward successful lookups.
    pub missed: bool,
}

impl TokenTrieIndex {
    /// Build an index over a finite language.
    pub fn build(sentences: &[Vec<TokenId>], vocabulary_size: usize) -> Result<Self, GrammarError> {
        if vocabulary_size == 0 {
            return Err(GrammarError::EmptyVocabulary);
        }
        if sentences.is_empty() {
            return Err(GrammarError::EmptyGrammar);
        }
        let mut nodes = vec![TrieNode::default()];
        for (index, sentence) in sentences.iter().enumerate() {
            if sentence.is_empty() {
                return Err(GrammarError::EmptySentence { index });
            }
            let mut current = 0usize;
            for token in sentence {
                if *token as usize >= vocabulary_size {
                    return Err(GrammarError::TokenOutsideVocabulary {
                        token: *token,
                        vocabulary_size,
                    });
                }
                current = match nodes[current]
                    .children
                    .binary_search_by_key(token, |(key, _)| *key)
                {
                    Ok(slot) => nodes[current].children[slot].1,
                    Err(slot) => {
                        let fresh = nodes.len();
                        nodes.push(TrieNode::default());
                        nodes[current].children.insert(slot, (*token, fresh));
                        fresh
                    }
                };
            }
            nodes[current].terminal = true;
        }
        Ok(Self {
            nodes,
            vocabulary_size,
            sentence_count: sentences.len(),
        })
    }

    pub fn vocabulary_size(&self) -> usize {
        self.vocabulary_size
    }

    pub fn sentence_count(&self) -> usize {
        self.sentence_count
    }

    pub fn node_count(&self) -> usize {
        self.nodes.len()
    }

    /// Descend the trie along `prefix`, counting every key comparison.
    ///
    /// The binary search is written out rather than delegated because the
    /// comparison count *is* the deliverable: criterion 4 asks for measured
    /// cost, and a library search would hide the number behind an interface.
    pub fn descend(&self, prefix: &[TokenId]) -> Descent {
        let mut comparisons = 0u64;
        let mut current = 0usize;
        for token in prefix {
            let children = &self.nodes[current].children;
            let mut low = 0usize;
            let mut high = children.len();
            let mut found: Option<usize> = None;
            while low < high {
                let middle = low + (high - low) / 2;
                comparisons += 1;
                if children[middle].0 == *token {
                    found = Some(children[middle].1);
                    break;
                } else if children[middle].0 < *token {
                    low = middle + 1;
                } else {
                    high = middle;
                }
            }
            match found {
                Some(next) => current = next,
                None => {
                    return Descent {
                        node: None,
                        comparisons,
                        missed: true,
                    }
                }
            }
        }
        Descent {
            node: Some(current),
            comparisons,
            missed: false,
        }
    }

    /// The tokens with a valid continuation after `prefix`.
    ///
    /// Empty when the prefix has left the grammar, which is the honest answer:
    /// nothing continues an inadmissible history.
    pub fn admissible(&self, prefix: &[TokenId]) -> BTreeSet<TokenId> {
        match self.descend(prefix).node {
            None => BTreeSet::new(),
            Some(node) => self.nodes[node]
                .children
                .iter()
                .map(|(token, _)| *token)
                .collect(),
        }
    }

    /// Whether `prefix` completes a sentence the grammar admits.
    pub fn is_terminal(&self, prefix: &[TokenId]) -> bool {
        match self.descend(prefix).node {
            None => false,
            Some(node) => self.nodes[node].terminal,
        }
    }

    /// A dense mask over the whole vocabulary: `true` iff admissible.
    ///
    /// The bit order is the token id, so the vector is stable across processes
    /// and can be compared byte for byte -- which is what any seam carrying it
    /// would need.
    pub fn mask(&self, prefix: &[TokenId]) -> Vec<bool> {
        let admissible = self.admissible(prefix);
        (0..self.vocabulary_size)
            .map(|index| admissible.contains(&(index as TokenId)))
            .collect()
    }

    /// A direct enumeration of the admissible set, for use as an oracle.
    ///
    /// Deliberately **not** implemented in terms of `admissible`: criterion 3
    /// says support width must be counted rather than estimated, and a test
    /// that compared the receipt against the same function that produced it
    /// would compare a value with itself.
    pub fn enumerate_admissible(&self, prefix: &[TokenId]) -> Vec<TokenId> {
        let mut found = Vec::new();
        for candidate in 0..self.vocabulary_size {
            let token = candidate as TokenId;
            let mut extended = prefix.to_vec();
            extended.push(token);
            if !self.descend(&extended).missed {
                found.push(token);
            }
        }
        found
    }
}

// ---------------------------------------------------------------------------
// Expected Future Grammaticality
// ---------------------------------------------------------------------------

/// `c(h) = sum over admissible w of P(w | h)`, as an exact rational.
///
/// A lower bound on future grammaticality: it sums the mass the model would
/// place on tokens the grammar still allows. Every value is `Ratio<i64>`; no
/// float appears anywhere in this module, and a test asserts that at the source
/// level.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExpectedFutureGrammaticality {
    score: Ratio<i64>,
    admitted: usize,
    considered: usize,
}

impl ExpectedFutureGrammaticality {
    /// Score a prefix against a token distribution.
    ///
    /// `distribution` gives `P(w | h)` for each token by id. Tokens absent from
    /// it contribute nothing, which is the correct lower-bound behaviour: an
    /// unstated probability is not assumed to be positive.
    pub fn score(
        index: &TokenTrieIndex,
        prefix: &[TokenId],
        distribution: &[(TokenId, Ratio<i64>)],
    ) -> Result<Self, GrammarError> {
        let admissible = index.admissible(prefix);
        let mut score = Ratio::new(0, 1);
        let mut admitted = 0usize;
        for (token, probability) in distribution {
            if *probability < Ratio::new(0, 1) {
                return Err(GrammarError::NegativeProbability { token: *token });
            }
            if admissible.contains(token) {
                score += *probability;
                admitted += 1;
            }
        }
        Ok(Self {
            score,
            admitted,
            considered: distribution.len(),
        })
    }

    pub fn score_value(&self) -> Ratio<i64> {
        self.score
    }

    pub fn admitted(&self) -> usize {
        self.admitted
    }

    pub fn considered(&self) -> usize {
        self.considered
    }

    /// True when no admissible token carries any mass -- a dead end.
    pub fn is_dead_end(&self) -> bool {
        self.score == Ratio::new(0, 1)
    }
}

// ---------------------------------------------------------------------------
// Receipt
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TokenFrontierReceiptV1 {
    pub schema_version: String,
    /// `|A_G(h)|`, the legal support width.
    pub support_width: usize,
    pub vocabulary_size: usize,
    /// `|A_G(h)| / |V|`, exact. Serialised as a pair so no decimal expansion
    /// is ever written down.
    pub compression_numerator: i64,
    pub compression_denominator: i64,
    pub efg_numerator: i64,
    pub efg_denominator: i64,
    pub prefix_length: usize,
    pub comparisons: u64,
    pub prefix_missed: bool,
    pub authority_effect: String,
}

impl TokenFrontierReceiptV1 {
    pub fn build(
        index: &TokenTrieIndex,
        prefix: &[TokenId],
        efg: &ExpectedFutureGrammaticality,
    ) -> Self {
        let descent = index.descend(prefix);
        let support_width = index.admissible(prefix).len();
        let compression = Ratio::new(support_width as i64, index.vocabulary_size() as i64);
        Self {
            schema_version: FRONTIER_RECEIPT_SCHEMA_V1.to_string(),
            support_width,
            vocabulary_size: index.vocabulary_size(),
            compression_numerator: *compression.numer(),
            compression_denominator: *compression.denom(),
            efg_numerator: *efg.score_value().numer(),
            efg_denominator: *efg.score_value().denom(),
            prefix_length: prefix.len(),
            comparisons: descent.comparisons,
            prefix_missed: descent.missed,
            authority_effect: "None".to_string(),
        }
    }

    pub fn compression_ratio(&self) -> Ratio<i64> {
        Ratio::new(self.compression_numerator, self.compression_denominator)
    }

    pub fn efg(&self) -> Ratio<i64> {
        Ratio::new(self.efg_numerator, self.efg_denominator)
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Origin: engine/crates_rs/pfp/src/epics/grammar.rs
// Claim: urn:core:crates_rs:pfp:grammar:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    /// A tiny grammar: 0->1->2, 0->1->3, 0->4.
    fn small_index() -> TokenTrieIndex {
        TokenTrieIndex::build(&[vec![0, 1, 2], vec![0, 1, 3], vec![0, 4]], 8)
            .expect("the fixture grammar must build")
    }

    fn ratio(numerator: i64, denominator: i64) -> Ratio<i64> {
        Ratio::new(numerator, denominator)
    }

    // -- AC1: the mask is exactly the admissible set ----------------------

    #[test]
    fn the_mask_admits_exactly_the_tokens_with_a_continuation() {
        let index = small_index();
        let mask = index.mask(&[0]);
        let expected: Vec<bool> = (0..8).map(|t| t == 1 || t == 4).collect();
        assert_eq!(mask, expected);
    }

    #[test]
    fn the_mask_equals_a_direct_enumeration() {
        // Criterion 3 in force: the oracle walks the vocabulary and descends
        // for each candidate, so it shares no code path with `mask`.
        let index = small_index();
        for prefix in [vec![], vec![0], vec![0, 1], vec![0, 4]] {
            let from_mask: Vec<TokenId> = index
                .mask(&prefix)
                .iter()
                .enumerate()
                .filter(|(_, admitted)| **admitted)
                .map(|(token, _)| token as TokenId)
                .collect();
            assert_eq!(from_mask, index.enumerate_admissible(&prefix), "{prefix:?}");
        }
    }

    #[test]
    fn the_mask_is_the_width_of_the_vocabulary() {
        let index = small_index();
        assert_eq!(index.mask(&[0]).len(), index.vocabulary_size());
    }

    #[test]
    fn a_prefix_outside_the_grammar_admits_nothing() {
        let index = small_index();
        assert_eq!(index.admissible(&[7]), BTreeSet::new());
        assert!(index.mask(&[7]).iter().all(|admitted| !admitted));
    }

    #[test]
    fn a_completed_sentence_admits_nothing_further() {
        let index = small_index();
        assert!(index.is_terminal(&[0, 4]));
        assert_eq!(index.admissible(&[0, 4]), BTreeSet::new());
    }

    #[test]
    fn a_proper_prefix_that_is_not_a_sentence_is_not_terminal() {
        // Every existing terminality test asserted the *true* case, so a
        // mutation returning `true` unconditionally survived. `[0]` is a prefix
        // of three sentences and is not itself one.
        let index = small_index();
        assert!(!index.is_terminal(&[0]));
        assert!(!index.is_terminal(&[0, 1]));
        assert!(index.is_terminal(&[0, 1, 2]));
    }

    #[test]
    fn a_prefix_outside_the_grammar_is_not_terminal() {
        let index = small_index();
        assert!(!index.is_terminal(&[7]));
        assert!(!index.is_terminal(&[0, 6]));
    }

    #[test]
    fn a_prefix_can_be_both_terminal_and_extendable() {
        // The grammar admits "0 1" and "0 1 2"; after "0 1" the frontier is
        // non-empty and the prefix is also a complete sentence.
        let index = TokenTrieIndex::build(&[vec![0, 1], vec![0, 1, 2]], 4).expect("must build");
        assert!(index.is_terminal(&[0, 1]));
        assert_eq!(index.admissible(&[0, 1]), BTreeSet::from([2]));
    }

    // -- AC2: no float enters the scoring ---------------------------------

    #[test]
    fn the_module_contains_no_floating_point_type() {
        // The type-level gate, asserted at the source. A guarantee that holds
        // only until someone writes one `as f64` is a convention, not a gate.
        //
        // Scanned above `#[cfg(test)]` only. The first version scanned the whole
        // file and failed on *itself*: a test that names the tokens it forbids
        // is caught by its own predicate. A source-level ban has to exclude the
        // text that states the ban, or it can never pass.
        let source = include_str!("grammar.rs");
        let implementation = source
            .split("#[cfg(test)]")
            .next()
            .expect("the module must have a non-test half");
        assert!(
            implementation.len() > 1_000,
            "the split found no implementation; the marker moved"
        );
        for banned in ["f64", "f32"] {
            assert!(
                !implementation.contains(banned),
                "the scoring implementation must admit no {banned}"
            );
        }
    }

    #[test]
    fn the_float_gate_would_catch_a_float() {
        // The gate above asserts an absence, so its predicate must be shown to
        // fire on the thing it forbids -- sprint 019's rule about absence tests
        // and unproven queries.
        let contrived = "pub fn score(x: i64) -> f64 { x as f64 }";
        assert!(["f64", "f32"].iter().any(|b| contrived.contains(b)));
    }

    #[test]
    fn the_score_is_an_exact_rational_sum() {
        let index = small_index();
        // 1/3 + 1/7 = 10/21, a value no binary float represents exactly.
        let distribution = vec![(1, ratio(1, 3)), (4, ratio(1, 7)), (2, ratio(1, 2))];
        let efg =
            ExpectedFutureGrammaticality::score(&index, &[0], &distribution).expect("must score");
        assert_eq!(efg.score_value(), ratio(10, 21));
    }

    #[test]
    fn inadmissible_tokens_contribute_nothing() {
        let index = small_index();
        // Token 2 is not admissible after [0]; only 1 and 4 are.
        let with = vec![(1, ratio(1, 4)), (2, ratio(1, 2))];
        let without = vec![(1, ratio(1, 4))];
        let a = ExpectedFutureGrammaticality::score(&index, &[0], &with).expect("ok");
        let b = ExpectedFutureGrammaticality::score(&index, &[0], &without).expect("ok");
        assert_eq!(a.score_value(), b.score_value());
        assert_eq!(a.admitted(), 1);
    }

    #[test]
    fn a_token_absent_from_the_distribution_contributes_nothing() {
        // The lower-bound property: an unstated probability is not assumed
        // positive.
        let index = small_index();
        let efg =
            ExpectedFutureGrammaticality::score(&index, &[0], &[(1, ratio(1, 5))]).expect("ok");
        assert_eq!(efg.score_value(), ratio(1, 5));
        assert_eq!(efg.considered(), 1);
    }

    #[test]
    fn a_negative_probability_is_refused() {
        let index = small_index();
        assert_eq!(
            ExpectedFutureGrammaticality::score(&index, &[0], &[(1, ratio(-1, 2))])
                .expect_err("must refuse"),
            GrammarError::NegativeProbability { token: 1 }
        );
    }

    #[test]
    fn a_dead_end_scores_zero() {
        let index = small_index();
        let efg =
            ExpectedFutureGrammaticality::score(&index, &[0, 4], &[(1, ratio(1, 2))]).expect("ok");
        assert!(efg.is_dead_end());
        assert_eq!(efg.score_value(), ratio(0, 1));
    }

    #[test]
    fn scoring_is_order_independent() {
        let index = small_index();
        let forward = vec![(1, ratio(1, 3)), (4, ratio(1, 7))];
        let backward = vec![(4, ratio(1, 7)), (1, ratio(1, 3))];
        assert_eq!(
            ExpectedFutureGrammaticality::score(&index, &[0], &forward)
                .expect("ok")
                .score_value(),
            ExpectedFutureGrammaticality::score(&index, &[0], &backward)
                .expect("ok")
                .score_value()
        );
    }

    // -- AC3: support width is counted, not estimated ---------------------

    #[test]
    fn the_receipt_width_equals_a_direct_enumeration() {
        let index = small_index();
        for prefix in [vec![], vec![0], vec![0, 1], vec![0, 4], vec![7]] {
            let efg = ExpectedFutureGrammaticality::score(&index, &prefix, &[]).expect("ok");
            let receipt = TokenFrontierReceiptV1::build(&index, &prefix, &efg);
            assert_eq!(
                receipt.support_width,
                index.enumerate_admissible(&prefix).len(),
                "{prefix:?}"
            );
        }
    }

    #[test]
    fn the_compression_ratio_is_width_over_vocabulary() {
        let index = small_index();
        let efg = ExpectedFutureGrammaticality::score(&index, &[0], &[]).expect("ok");
        let receipt = TokenFrontierReceiptV1::build(&index, &[0], &efg);
        // Two admissible of eight.
        assert_eq!(receipt.compression_ratio(), ratio(2, 8));
        assert_eq!(receipt.support_width, 2);
    }

    #[test]
    fn the_receipt_stores_the_ratio_as_a_pair_not_a_decimal() {
        let index = small_index();
        let efg =
            ExpectedFutureGrammaticality::score(&index, &[0], &[(1, ratio(1, 3))]).expect("ok");
        let receipt = TokenFrontierReceiptV1::build(&index, &[0], &efg);
        assert_eq!(receipt.efg_numerator, 1);
        assert_eq!(receipt.efg_denominator, 3);
        let encoded = serde_json::to_string(&receipt).expect("must serialise");
        assert!(
            !encoded.contains("0.333"),
            "no decimal expansion may be written"
        );
    }

    #[test]
    fn the_receipt_records_a_miss_as_a_residual() {
        // Criterion 4's residual rule: a lookup that leaves the grammar is
        // recorded, not omitted.
        let index = small_index();
        let efg = ExpectedFutureGrammaticality::score(&index, &[7], &[]).expect("ok");
        let receipt = TokenFrontierReceiptV1::build(&index, &[7], &efg);
        assert!(receipt.prefix_missed);
        assert!(receipt.comparisons > 0, "a miss still costs comparisons");
        assert_eq!(receipt.support_width, 0);
    }

    #[test]
    fn the_receipt_carries_no_authority() {
        let index = small_index();
        let efg = ExpectedFutureGrammaticality::score(&index, &[0], &[]).expect("ok");
        let receipt = TokenFrontierReceiptV1::build(&index, &[0], &efg);
        assert_eq!(receipt.authority_effect, "None");
        assert_eq!(receipt.schema_version, FRONTIER_RECEIPT_SCHEMA_V1);
    }

    #[test]
    fn the_receipt_round_trips_through_json() {
        let index = small_index();
        let efg =
            ExpectedFutureGrammaticality::score(&index, &[0], &[(1, ratio(2, 5))]).expect("ok");
        let receipt = TokenFrontierReceiptV1::build(&index, &[0], &efg);
        let encoded = serde_json::to_string(&receipt).expect("must serialise");
        let decoded: TokenFrontierReceiptV1 =
            serde_json::from_str(&encoded).expect("must deserialise");
        assert_eq!(receipt, decoded);
    }

    // -- AC4: lookup cost is measured, not asserted -----------------------

    /// A wide grammar: `width` sentences of length 2, sharing the root.
    fn wide_index(width: usize) -> TokenTrieIndex {
        let sentences: Vec<Vec<TokenId>> =
            (0..width).map(|token| vec![token as TokenId, 0]).collect();
        TokenTrieIndex::build(&sentences, width).expect("must build")
    }

    #[test]
    fn lookup_cost_grows_logarithmically_from_2p10_to_2p16() {
        // The measurement criterion 4 asks for, recorded rather than asserted.
        let mut measured = Vec::new();
        for exponent in 10..=16u32 {
            let width = 1usize << exponent;
            let index = wide_index(width);
            // Search for the last token, the worst case for a binary descent.
            let descent = index.descend(&[(width - 1) as TokenId]);
            assert!(!descent.missed, "the token must be present");
            measured.push((exponent, descent.comparisons));
        }

        for (exponent, comparisons) in &measured {
            let bound = u64::from(*exponent) + 1;
            assert!(
                *comparisons <= bound,
                "at 2^{exponent} the descent took {comparisons} comparisons, \
                 above the logarithmic bound of {bound}: {measured:?}"
            );
        }

        // And the growth is genuinely sub-linear: a 64-fold vocabulary increase
        // must not cost 64 times as much.
        let first = measured.first().expect("measured").1;
        let last = measured.last().expect("measured").1;
        assert!(
            last < first * 4,
            "cost grew faster than logarithmically: {measured:?}"
        );
    }

    #[test]
    fn a_miss_still_reports_its_cost() {
        let index = wide_index(1024);
        // A token id inside the vocabulary but absent at depth 2.
        let descent = index.descend(&[0, 500]);
        assert!(descent.missed);
        assert!(descent.comparisons > 0);
    }

    #[test]
    fn a_deeper_prefix_costs_more_than_a_shallower_one() {
        let index = small_index();
        let shallow = index.descend(&[0]).comparisons;
        let deep = index.descend(&[0, 1, 2]).comparisons;
        assert!(deep > shallow);
    }

    #[test]
    fn an_empty_prefix_costs_nothing() {
        let index = small_index();
        let descent = index.descend(&[]);
        assert_eq!(descent.comparisons, 0);
        assert!(!descent.missed);
    }

    // -- construction refusals --------------------------------------------

    #[test]
    fn an_empty_grammar_is_refused() {
        assert_eq!(
            TokenTrieIndex::build(&[], 8).expect_err("must refuse"),
            GrammarError::EmptyGrammar
        );
    }

    #[test]
    fn an_empty_vocabulary_is_refused() {
        assert_eq!(
            TokenTrieIndex::build(&[vec![0]], 0).expect_err("must refuse"),
            GrammarError::EmptyVocabulary
        );
    }

    #[test]
    fn an_empty_sentence_is_refused() {
        assert_eq!(
            TokenTrieIndex::build(&[vec![0], vec![]], 4).expect_err("must refuse"),
            GrammarError::EmptySentence { index: 1 }
        );
    }

    #[test]
    fn a_token_outside_the_vocabulary_is_refused() {
        assert_eq!(
            TokenTrieIndex::build(&[vec![0, 9]], 4).expect_err("must refuse"),
            GrammarError::TokenOutsideVocabulary {
                token: 9,
                vocabulary_size: 4
            }
        );
    }

    #[test]
    fn duplicate_sentences_do_not_duplicate_nodes() {
        let once = TokenTrieIndex::build(&[vec![0, 1, 2]], 4).expect("ok");
        let twice = TokenTrieIndex::build(&[vec![0, 1, 2], vec![0, 1, 2]], 4).expect("ok");
        assert_eq!(once.node_count(), twice.node_count());
        assert_eq!(twice.sentence_count(), 2);
    }

    #[test]
    fn shared_prefixes_share_nodes() {
        // Three sentences over a shared prefix must cost fewer nodes than three
        // disjoint ones, or the trie is not a trie.
        let shared = TokenTrieIndex::build(&[vec![0, 1], vec![0, 2], vec![0, 3]], 8).expect("ok");
        let disjoint = TokenTrieIndex::build(&[vec![1, 1], vec![2, 2], vec![3, 3]], 8).expect("ok");
        assert!(shared.node_count() < disjoint.node_count());
    }

    // -- the deferred deliverable, recorded --------------------------------

    #[test]
    fn this_crate_has_no_pyo3_dependency() {
        // Deliverable 4 asks for a PyO3 export. `EPIC-OE-SYMGAM-009` is the epic
        // that owns how that seam should be shaped, and adding an ad-hoc one
        // here would pre-empt it. If pyo3 ever lands in this crate, this fails
        // and the module docstring's deferral becomes stale.
        let manifest = include_str!("../../Cargo.toml");
        assert!(
            !manifest.contains("pyo3"),
            "pyo3 is now a dependency; the seam deferral needs revisiting"
        );
    }

    #[test]
    fn the_mask_is_a_stable_bit_vector_any_seam_could_carry() {
        // What criterion 5 would compare, if the seam existed: a dense vector
        // in token-id order, identical across processes.
        let index = small_index();
        let first = index.mask(&[0]);
        let second = index.mask(&[0]);
        assert_eq!(first, second);
        assert_eq!(first.len(), index.vocabulary_size());
    }
}
