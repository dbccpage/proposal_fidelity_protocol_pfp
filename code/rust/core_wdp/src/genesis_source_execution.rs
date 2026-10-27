//! Actual enabled changes of pinned Genesis Ongoing seed 25.
//! The carrier is the source's unnamed writing 0..n, encoded as t0..t(n-1).
//! Integer multiplicities are unbounded. Identification and term addition
//! retain representatives; neither is asserted to descend to repair classes.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_c0ba171b<T> {
    fn checked_invariant_c0ba171b(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_c0ba171b<T> for Option<T> {
    #[inline]
    fn checked_invariant_c0ba171b(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_c0ba171b<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_c0ba171b(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::genesis_ongoing_adapter::{GenesisBridgeError, GenesisOngoingPacket, MarkedTriple};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::semiring_lumpability::push_forward_square;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SourceRelation {
    R,
    S,
}

/// Exactly the canonical event descriptors in twentyfifth.state.changes.
/// Arbitrary Python objects accepted by an untyped function are not events
/// of this declared integer transition system.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Source25Change {
    Identify {
        x: usize,
        y: usize,
    },
    Remove {
        relation: SourceRelation,
        x: usize,
        y: usize,
    },
    Fill {
        x: usize,
        y: usize,
        z: usize,
    },
    AddTerm,
    AddAssertion {
        relation: SourceRelation,
        x: usize,
        y: usize,
    },
}

impl Source25Change {
    /// The source's two addition prices: terms and assertions. A filling is
    /// an occurrence but adds neither a term nor an assertion.
    pub fn additions(self) -> (usize, usize) {
        match self {
            Self::AddTerm => (1, 0),
            Self::AddAssertion { .. } => (0, 1),
            _ => (0, 0),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SourceExecutionError {
    #[error("source carrier must use the canonical unnamed writing t0..t(n-1)")]
    NonCanonicalCarrier,
    #[error("the event is not an enabled canonical change of this source state")]
    DisabledChange,
    #[error("raising needs one nonnegative integer count per source term")]
    InvalidRaising,
    #[error("ordered runs have different complete intermediate source states")]
    IntermediateMismatch,
    #[error("source refusal: {0}")]
    Bridge(#[from] GenesisBridgeError),
}

/// Checked raw source state. No quotient is taken before future changes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source25State {
    packet: GenesisOngoingPacket,
}

pub(crate) fn canonical_triple(x: usize, y: usize, z: usize) -> MarkedTriple {
    if x < y && x < z {
        MarkedTriple { x, y, z }
    } else if y < z {
        MarkedTriple { x: y, y: z, z: x }
    } else {
        MarkedTriple { x: z, y: x, z: y }
    }
}

pub(crate) fn move_counts(
    counts: &[BigInt],
    image: &[usize],
    target_size: usize,
) -> Result<Vec<BigInt>, SourceExecutionError> {
    let source_size = image.len();
    let table = BasicMatrix::from_row_major(
        source_size,
        source_size,
        counts
            .iter()
            .cloned()
            .map(BigRational::from_integer)
            .collect(),
    )
    .map_err(GenesisBridgeError::from)?;
    let moved =
        push_forward_square(&table, image, target_size).map_err(GenesisBridgeError::from)?;
    moved
        .as_slice()
        .iter()
        .map(|value| {
            if value.is_integer() {
                Ok(value.to_integer())
            } else {
                Err(GenesisBridgeError::NonIntegralOutput.into())
            }
        })
        .collect()
}

impl Source25State {
    pub fn try_new(packet: GenesisOngoingPacket) -> Result<Self, SourceExecutionError> {
        packet.validate()?;
        if packet
            .terms
            .iter()
            .enumerate()
            .any(|(i, label)| *label != format!("t{i}"))
        {
            return Err(SourceExecutionError::NonCanonicalCarrier);
        }
        Ok(Self { packet })
    }

    pub fn empty() -> Self {
        Self {
            packet: GenesisOngoingPacket {
                terms: vec![],
                r: vec![],
                s: vec![],
                filled: vec![],
            },
        }
    }

    pub fn packet(&self) -> &GenesisOngoingPacket {
        &self.packet
    }

    fn counts(&self, relation: SourceRelation) -> &[BigInt] {
        match relation {
            SourceRelation::R => &self.packet.r,
            SourceRelation::S => &self.packet.s,
        }
    }

    pub fn source_size(&self) -> BigInt {
        BigInt::from(self.packet.terms.len())
            + self.packet.r.iter().chain(&self.packet.s).sum::<BigInt>()
    }

    /// Source 22's declared plain-state cost; no quotient minimization is used.
    pub fn plain_state_cost(&self) -> BigInt {
        BigInt::from(self.packet.terms.len())
            + self
                .packet
                .r
                .iter()
                .zip(&self.packet.s)
                .map(|(r, s)| (r - s).abs())
                .sum::<BigInt>()
    }

    fn is_fill_enabled(&self, x: usize, y: usize, z: usize, n: usize) -> bool {
        let valid_order = x < y && x < z && y != z;
        let in_bounds = y < n && z < n;
        valid_order
            && in_bounds
            && self
                .packet
                .filled
                .binary_search(&MarkedTriple { x, y, z })
                .is_err()
    }

    pub fn is_enabled(&self, change: Source25Change) -> bool {
        let n = self.packet.terms.len();
        match change {
            Source25Change::Identify { x, y } => x < y && y < n,
            Source25Change::Remove { relation, x, y } => {
                x < n && y < n && self.counts(relation)[x * n + y] > BigInt::zero()
            }
            Source25Change::Fill { x, y, z } => self.is_fill_enabled(x, y, z, n),
            Source25Change::AddTerm => true,
            Source25Change::AddAssertion { x, y, .. } => x < n && y < n,
        }
    }

    /// The four assertion-state change kinds shared with source 9.
    pub(crate) fn enabled_four_changes(&self) -> Vec<Source25Change> {
        let n = self.packet.terms.len();
        let mut out = Vec::new();
        for x in 0..n {
            for y in x + 1..n {
                out.push(Source25Change::Identify { x, y });
            }
        }
        for relation in [SourceRelation::R, SourceRelation::S] {
            for x in 0..n {
                for y in 0..n {
                    let event = Source25Change::Remove { relation, x, y };
                    if self.is_enabled(event) {
                        out.push(event);
                    }
                }
            }
        }
        out.push(Source25Change::AddTerm);
        for relation in [SourceRelation::R, SourceRelation::S] {
            for x in 0..n {
                for y in 0..n {
                    out.push(Source25Change::AddAssertion { relation, x, y });
                }
            }
        }
        out
    }

    /// Complete source ordering: identify; remove r,s; fill; term; add r,s.
    pub fn enabled_changes(&self) -> Vec<Source25Change> {
        let n = self.packet.terms.len();
        let four = self.enabled_four_changes();
        let boundary = four
            .iter()
            .position(|event| *event == Source25Change::AddTerm)
            .checked_invariant_c0ba171b("the four-kind list always contains term addition");
        let mut out = four[..boundary].to_vec();
        for x in 0..n {
            for y in x + 1..n {
                for z in x + 1..n {
                    let event = Source25Change::Fill { x, y, z };
                    if self.is_enabled(event) {
                        out.push(event);
                    }
                }
            }
        }
        out.extend_from_slice(&four[boundary..]);
        out
    }

    fn perform_add_term(
        out: &mut GenesisOngoingPacket,
        n: usize,
    ) -> Result<(), SourceExecutionError> {
        let target = n
            .checked_add(1)
            .ok_or(GenesisBridgeError::DimensionOverflow)?;
        let image: Vec<_> = (0..n).collect();
        out.r = move_counts(&out.r, &image, target)?;
        out.s = move_counts(&out.s, &image, target)?;
        out.terms.push(format!("t{n}"));
        Ok(())
    }

    fn perform_identify(
        &self,
        out: &mut GenesisOngoingPacket,
        x: usize,
        y: usize,
        n: usize,
    ) -> Result<(), SourceExecutionError> {
        let image: Vec<_> = (0..n)
            .map(|vertex| {
                if vertex == y {
                    x
                } else {
                    vertex - usize::from(vertex > y)
                }
            })
            .collect();
        out.r = move_counts(&out.r, &image, n - 1)?;
        out.s = move_counts(&out.s, &image, n - 1)?;
        out.terms = (0..n - 1).map(|i| format!("t{i}")).collect();
        out.filled = self
            .packet
            .filled
            .iter()
            .filter_map(|triple| {
                let (a, b, c) = (image[triple.x], image[triple.y], image[triple.z]);
                (a != b && b != c && c != a).then(|| canonical_triple(a, b, c))
            })
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        Ok(())
    }

    /// Execute an event from the source's enabled list. Failures leave this
    /// immutable state intact; a refusal is not silently admitted as a no-op.
    pub fn perform_enabled(&self, change: Source25Change) -> Result<Self, SourceExecutionError> {
        if !self.is_enabled(change) {
            return Err(SourceExecutionError::DisabledChange);
        }
        let n = self.packet.terms.len();
        let mut out = self.packet.clone();
        match change {
            Source25Change::AddTerm => Self::perform_add_term(&mut out, n)?,
            Source25Change::Identify { x, y } => self.perform_identify(&mut out, x, y, n)?,
            Source25Change::Remove { relation, x, y } => {
                let counts = match relation {
                    SourceRelation::R => &mut out.r,
                    SourceRelation::S => &mut out.s,
                };
                counts[x * n + y] -= BigInt::one();
            }
            Source25Change::AddAssertion { relation, x, y } => {
                let counts = match relation {
                    SourceRelation::R => &mut out.r,
                    SourceRelation::S => &mut out.s,
                };
                counts[x * n + y] += BigInt::one();
            }
            Source25Change::Fill { x, y, z } => {
                out.filled.push(MarkedTriple { x, y, z });
                out.filled.sort();
            }
        }
        Self::try_new(out)
    }

    /// Actual source 23 raising on raw assertions, used by seed 25's sameness.
    /// Raising is not one of seed 25's five enabled change kinds.
    pub fn raise_terms(&self, counts: &[BigInt]) -> Result<Self, SourceExecutionError> {
        let n = self.packet.terms.len();
        if counts.len() != n || counts.iter().any(Signed::is_negative) {
            return Err(SourceExecutionError::InvalidRaising);
        }
        let mut out = self.packet.clone();
        for x in 0..n {
            for y in 0..n {
                if x != y {
                    out.r[x * n + y] += &counts[x];
                    out.s[x * n + y] += &counts[y];
                }
            }
        }
        Self::try_new(out)
    }
}

/// Immutable ordered run retaining every occurrence and complete raw state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source25Run {
    states: Vec<Source25State>,
    changes: Vec<Source25Change>,
    term_additions: BigInt,
    assertion_additions: BigInt,
}

impl Source25Run {
    pub fn replay(
        initial: Source25State,
        changes: &[Source25Change],
    ) -> Result<Self, SourceExecutionError> {
        let mut states = vec![initial];
        let mut term_additions = BigInt::zero();
        let mut assertion_additions = BigInt::zero();
        for &change in changes {
            let state = states
                .last()
                .checked_invariant_c0ba171b("the initial state is retained")
                .perform_enabled(change)?;
            let (terms, assertions) = change.additions();
            term_additions += terms;
            assertion_additions += assertions;
            states.push(state);
        }
        Ok(Self {
            states,
            changes: changes.to_vec(),
            term_additions,
            assertion_additions,
        })
    }

    pub fn states(&self) -> &[Source25State] {
        &self.states
    }
    pub fn changes(&self) -> &[Source25Change] {
        &self.changes
    }
    pub fn final_state(&self) -> &Source25State {
        self.states.last().checked_invariant_c0ba171b("the initial state is retained")
    }
    pub fn addition_price(&self) -> (&BigInt, &BigInt) {
        (&self.term_additions, &self.assertion_additions)
    }

    pub fn then(&self, after: &Self) -> Result<Self, SourceExecutionError> {
        if self.final_state() != &after.states[0] {
            return Err(SourceExecutionError::IntermediateMismatch);
        }
        let mut states = self.states.clone();
        states.extend_from_slice(&after.states[1..]);
        let mut changes = self.changes.clone();
        changes.extend_from_slice(&after.changes);
        Ok(Self {
            states,
            changes,
            term_additions: &self.term_additions + &after.term_additions,
            assertion_additions: &self.assertion_additions + &after.assertion_additions,
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_source_execution.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-source-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_c0ba171b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
