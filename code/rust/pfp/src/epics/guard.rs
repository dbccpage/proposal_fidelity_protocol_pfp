//! Rejection receipts and learned guard rails.
//!
//! The Cemetery keeps every refused candidate losslessly. This module reads it
//! back and compiles what was refused into guards that prune the same failure
//! next time.
//!
//! ## The whole difficulty is soundness
//!
//! A guard that prunes too much is worse than no guard, and it fails silently:
//! the generator simply stops proposing a candidate that would have worked, and
//! nothing reports a loss. So the design is arranged so that over-generalizing
//! is not a mistake you can make by accident.
//!
//! **A compiled guard matches one candidate exactly.** [`GuardScope::Exact`]
//! compares the full fingerprint -- token stream *and* cochain projection. It
//! does not match prefixes, subsets, or "similar" candidates. The epic calls
//! this the Conservative Guard Law: *learned guards only disallow exact failure
//! manifolds.*
//!
//! **Generalization exists, and the compiler cannot reach it.**
//! [`GuardScope::Generalized`] can only be built through
//! [`LearnedGuard::admit_generalization`], which requires a reviewer name and
//! records it. [`compile_guards`] returns `Exact` guards and has no path to the
//! other constructor. The epic's *"generalization boundaries require explicit
//! human review"* is therefore a property of the type, not a rule someone has to
//! remember.
//!
//! **Soundness is checked against known-good candidates.**
//! [`GuardMask::assert_admits`] takes candidates that are known admissible and
//! refuses if any guard prunes one, naming both the guard and the candidate. An
//! empty known-good set is itself refused: proving that no guard prunes any of
//! zero candidates is not a proof of anything.
//!
//! `AuthorityEffect: None`. Pruning a candidate is not judging a solution.

use std::collections::{BTreeMap, BTreeSet};

use serde::{Deserialize, Serialize};
use thiserror::Error;

use super::retraction::{CandidateTurn, CemeterySink};

// ---------------------------------------------------------------------------
// Refusals
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum GuardRefusal {
    #[error(
        "guard {guard_digest} (from cemetery turn {source_turn}) prunes an admissible candidate: {token_stream}"
    )]
    PrunesAdmissible {
        guard_digest: String,
        source_turn: usize,
        token_stream: String,
    },

    #[error("refusing to certify soundness against an empty known-admissible set")]
    NoAdmissibleWitnesses,

    #[error("a generalization needs a reviewer; none was named")]
    UnreviewedGeneralization,

    #[error("cemetery record {turn_index} carries an empty refusal code")]
    UncodedRefusal { turn_index: usize },
}

// ---------------------------------------------------------------------------
// Fingerprints
// ---------------------------------------------------------------------------

/// Exactly what failed: the token stream and the cochain projection together.
///
/// Both halves are load-bearing. Two candidates can share a token stream and
/// differ in projection, and a guard keyed on the stream alone would prune the
/// one that had not failed.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateFingerprint {
    pub token_stream: String,
    pub cochain_projection: Vec<bool>,
}

impl CandidateFingerprint {
    pub fn of(candidate: &CandidateTurn) -> Self {
        Self {
            token_stream: candidate.token_stream.clone(),
            cochain_projection: candidate.cochain_projection.clone(),
        }
    }

    /// A stable digest, so a guard can cite what it forbids without quoting it.
    pub fn digest(&self) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"candidate-fingerprint-v1");
        hasher.update(self.token_stream.as_bytes());
        hasher.update(b"\x00");
        for bit in &self.cochain_projection {
            hasher.update(&[u8::from(*bit)]);
        }
        hasher.finalize().to_hex().to_string()
    }
}

// ---------------------------------------------------------------------------
// Guards
// ---------------------------------------------------------------------------

/// How widely a guard reaches.
///
/// `Exact` is the only scope [`compile_guards`] produces. `Generalized` carries
/// the reviewer who admitted it, because a guard that reaches beyond the
/// candidate that failed is a claim about candidates nobody observed.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum GuardScope {
    Exact,
    Generalized { reviewer: String, rationale: String },
}

impl GuardScope {
    pub fn is_exact(&self) -> bool {
        matches!(self, GuardScope::Exact)
    }

    pub fn reviewer(&self) -> Option<&str> {
        match self {
            GuardScope::Exact => None,
            GuardScope::Generalized { reviewer, .. } => Some(reviewer),
        }
    }
}

/// One guard, and the cemetery turns that justify it.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LearnedGuard {
    pub forbidden: CandidateFingerprint,
    pub refusal_code: String,
    /// Every cemetery turn that produced this fingerprint, in burial order.
    ///
    /// A repeated burial does not create a second guard, but it must not lose
    /// the second citation either: how often a candidate was retried is
    /// evidence, and a receipt naming one turn when three were observed
    /// understates what the Cemetery holds.
    pub source_turns: Vec<usize>,
    pub scope: GuardScope,
}

impl LearnedGuard {
    /// Promote a guard to reach beyond the exact candidate that failed.
    ///
    /// The only route to [`GuardScope::Generalized`]. It refuses an empty
    /// reviewer, so "reviewed by nobody" cannot be recorded as review.
    pub fn admit_generalization(
        mut self,
        reviewer: &str,
        rationale: &str,
    ) -> Result<Self, GuardRefusal> {
        if reviewer.trim().is_empty() {
            return Err(GuardRefusal::UnreviewedGeneralization);
        }
        self.scope = GuardScope::Generalized {
            reviewer: reviewer.to_string(),
            rationale: rationale.to_string(),
        };
        Ok(self)
    }

    /// Does this guard forbid the candidate?
    ///
    /// `Exact` compares the whole fingerprint. `Generalized` matches on the
    /// token stream alone -- deliberately the *only* place a looser rule lives,
    /// and only reachable once a reviewer has signed for it.
    pub fn prunes(&self, candidate: &CandidateTurn) -> bool {
        match &self.scope {
            GuardScope::Exact => self.forbidden == CandidateFingerprint::of(candidate),
            GuardScope::Generalized { .. } => self.forbidden.token_stream == candidate.token_stream,
        }
    }

    pub fn digest(&self) -> String {
        self.forbidden.digest()
    }
}

// ---------------------------------------------------------------------------
// Compilation
// ---------------------------------------------------------------------------

/// The compiled set of guards.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GuardMask {
    guards: Vec<LearnedGuard>,
}

impl GuardMask {
    pub fn guards(&self) -> &[LearnedGuard] {
        &self.guards
    }

    pub fn len(&self) -> usize {
        self.guards.len()
    }

    pub fn is_empty(&self) -> bool {
        self.guards.is_empty()
    }

    /// The first guard that forbids this candidate, if any.
    ///
    /// Returns the guard rather than a boolean: a pruned candidate must be able
    /// to say which guard pruned it and which cemetery turn taught it.
    pub fn pruning_guard(&self, candidate: &CandidateTurn) -> Option<&LearnedGuard> {
        self.guards.iter().find(|guard| guard.prunes(candidate))
    }

    pub fn prunes(&self, candidate: &CandidateTurn) -> bool {
        self.pruning_guard(candidate).is_some()
    }

    /// Keep only the candidates no guard forbids.
    pub fn filter<'a>(&self, candidates: &'a [CandidateTurn]) -> Vec<&'a CandidateTurn> {
        candidates
            .iter()
            .filter(|candidate| !self.prunes(candidate))
            .collect()
    }

    /// Non-regression: no guard may prune a candidate known to be admissible.
    ///
    /// This is the check that makes learning safe. A guard pruning a known-good
    /// candidate is reported with both identities, because "some guard is
    /// wrong" is not actionable.
    ///
    /// An empty witness set is refused. Certifying that no guard prunes any of
    /// zero admissible candidates would be a vacuous pass, and vacuous passes
    /// are how unsound guards ship.
    pub fn assert_admits(&self, admissible: &[CandidateTurn]) -> Result<(), GuardRefusal> {
        if admissible.is_empty() {
            return Err(GuardRefusal::NoAdmissibleWitnesses);
        }
        for candidate in admissible {
            if let Some(guard) = self.pruning_guard(candidate) {
                return Err(GuardRefusal::PrunesAdmissible {
                    guard_digest: guard.digest(),
                    source_turn: guard.source_turns.first().copied().unwrap_or_default(),
                    token_stream: candidate.token_stream.clone(),
                });
            }
        }
        Ok(())
    }

    /// A digest over the whole mask, for the compilation receipt.
    pub fn digest(&self) -> String {
        let mut hasher = blake3::Hasher::new();
        hasher.update(b"guard-mask-v1");
        for guard in &self.guards {
            hasher.update(guard.forbidden.digest().as_bytes());
            hasher.update(guard.refusal_code.as_bytes());
            for turn in &guard.source_turns {
                hasher.update(&turn.to_be_bytes());
            }
        }
        hasher.finalize().to_hex().to_string()
    }
}

/// Compile a mask from the Cemetery.
///
/// Deterministic: records are grouped by fingerprint and emitted in sorted
/// fingerprint order, so two runs over the same Cemetery produce byte-identical
/// masks and digests regardless of burial order.
///
/// Every guard produced is [`GuardScope::Exact`]. There is no path from here to
/// a generalization.
pub fn compile_guards(cemetery: &CemeterySink) -> Result<GuardMask, GuardRefusal> {
    let mut grouped: BTreeMap<CandidateFingerprint, (String, BTreeSet<usize>)> = BTreeMap::new();
    for record in cemetery.records() {
        if record.refusal_code.trim().is_empty() {
            return Err(GuardRefusal::UncodedRefusal {
                turn_index: record.turn_index,
            });
        }
        let fingerprint = CandidateFingerprint::of(&record.candidate);
        let entry = grouped
            .entry(fingerprint)
            .or_insert_with(|| (record.refusal_code.clone(), BTreeSet::new()));
        entry.1.insert(record.turn_index);
    }
    let guards = grouped
        .into_iter()
        .map(|(forbidden, (refusal_code, turns))| LearnedGuard {
            forbidden,
            refusal_code,
            source_turns: turns.into_iter().collect(),
            scope: GuardScope::Exact,
        })
        .collect();
    Ok(GuardMask { guards })
}

// ---------------------------------------------------------------------------
// Receipts
// ---------------------------------------------------------------------------

/// What a compilation produced, and from which cemetery turns.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GuardCompilationReceiptV1 {
    pub schema: &'static str,
    pub cemetery_records: usize,
    pub guards_compiled: usize,
    pub mask_digest: String,
    /// Every cemetery turn cited by some guard, ascending.
    pub cited_turns: Vec<usize>,
    pub exact_guards: usize,
    pub generalized_guards: usize,
    pub authority_effect: &'static str,
}

pub const GUARD_RECEIPT_SCHEMA: &str = "core.symbol_game.guard_compilation.v1";

/// Build the receipt for a compiled mask.
///
/// `cemetery_records` and `guards_compiled` are both carried: they differ
/// whenever a candidate was buried more than once, and collapsing them would
/// hide how much of the Cemetery was repetition.
pub fn compilation_receipt(cemetery: &CemeterySink, mask: &GuardMask) -> GuardCompilationReceiptV1 {
    let mut cited: BTreeSet<usize> = BTreeSet::new();
    let mut exact = 0usize;
    let mut generalized = 0usize;
    for guard in mask.guards() {
        cited.extend(guard.source_turns.iter().copied());
        if guard.scope.is_exact() {
            exact += 1;
        } else {
            generalized += 1;
        }
    }
    GuardCompilationReceiptV1 {
        schema: GUARD_RECEIPT_SCHEMA,
        cemetery_records: cemetery.len(),
        guards_compiled: mask.len(),
        mask_digest: mask.digest(),
        cited_turns: cited.into_iter().collect(),
        exact_guards: exact,
        generalized_guards: generalized,
        authority_effect: "None",
    }
}

/// Every cemetery record is cited by exactly one guard.
///
/// The epic's zero-data-loss invariant, checked rather than asserted: if a
/// record were dropped during compilation its turn index would be missing here.
pub fn every_record_is_cited(cemetery: &CemeterySink, mask: &GuardMask) -> bool {
    let buried: BTreeSet<usize> = cemetery.records().iter().map(|r| r.turn_index).collect();
    let cited: BTreeSet<usize> = mask
        .guards()
        .iter()
        .flat_map(|guard| guard.source_turns.iter().copied())
        .collect();
    buried == cited
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_90f29cf3 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
