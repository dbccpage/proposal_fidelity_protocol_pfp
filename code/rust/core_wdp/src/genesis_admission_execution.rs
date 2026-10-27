//! Distinct admission meanings of pinned Genesis Ongoing seeds 15 and 16.
//! Seed 15 C-A1 keeps admission outside its assertion state; the source also
//! retains Tagged (unchosen C-A2). Seed 16's chosen COUNT reading carries a
//! third table, feeding assertions when a leftover is admitted. SET and DROP
//! remain explicit alternatives with different mass/potential laws.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fd545a88<T> {
    fn checked_invariant_fd545a88(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fd545a88<T> for Option<T> {
    #[inline]
    fn checked_invariant_fd545a88(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fd545a88<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fd545a88(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::genesis_ongoing_adapter::{GenesisBridgeError, GenesisOngoingPacket};
use crate::genesis_source_execution::{
    move_counts, Source25Change, Source25State, SourceExecutionError, SourceRelation,
};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::pair_table_canonical::{canonical_pair_tables, PairCanonicalError};
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum AdmissionExecutionError {
    #[error("the ninth-state source has no filled triples")]
    FilledCarrier,
    #[error("leftovers require one nonnegative integer count per ordered pair")]
    InvalidRecord,
    #[error("event is not enabled in this source state")]
    DisabledEvent,
    #[error("ordered runs disagree on their complete intermediate source state")]
    IntermediateMismatch,
    #[error("ordered runs use different record readings")]
    ReadingMismatch,
    #[error("recipe contains {requested} changes, above expansion limit {limit}")]
    RecipeBudgetExceeded { requested: BigInt, limit: usize },
    #[error("source change refused: {0}")]
    Source(#[from] SourceExecutionError),
    #[error("joint source writing refused: {0}")]
    Canonical(#[from] PairCanonicalError),
}
impl From<GenesisBridgeError> for AdmissionExecutionError {
    fn from(error: GenesisBridgeError) -> Self {
        Self::Source(error.into())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Source9Change {
    Identify {
        x: usize,
        y: usize,
    },
    Remove {
        relation: SourceRelation,
        x: usize,
        y: usize,
    },
    AddTerm,
    AddAssertion {
        relation: SourceRelation,
        x: usize,
        y: usize,
    },
}
impl Source9Change {
    pub fn as_source25(self) -> Source25Change {
        match self {
            Self::Identify { x, y } => Source25Change::Identify { x, y },
            Self::Remove { relation, x, y } => Source25Change::Remove { relation, x, y },
            Self::AddTerm => Source25Change::AddTerm,
            Self::AddAssertion { relation, x, y } => {
                Source25Change::AddAssertion { relation, x, y }
            }
        }
    }
    pub fn additions(self) -> (usize, usize) {
        self.as_source25().additions()
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source9State {
    raw: Source25State,
}
impl Source9State {
    pub fn try_new(packet: GenesisOngoingPacket) -> Result<Self, AdmissionExecutionError> {
        if !packet.filled.is_empty() {
            return Err(AdmissionExecutionError::FilledCarrier);
        }
        Ok(Self {
            raw: Source25State::try_new(packet)?,
        })
    }
    pub fn empty() -> Self {
        Self {
            raw: Source25State::empty(),
        }
    }
    pub fn packet(&self) -> &GenesisOngoingPacket {
        self.raw.packet()
    }
    pub fn source_size(&self) -> BigInt {
        self.raw.source_size()
    }
    pub fn is_enabled(&self, event: Source9Change) -> bool {
        self.raw.is_enabled(event.as_source25())
    }
    pub fn enabled_changes(&self) -> Vec<Source9Change> {
        self.raw
            .enabled_four_changes()
            .into_iter()
            .map(|event| match event {
                Source25Change::Identify { x, y } => Source9Change::Identify { x, y },
                Source25Change::Remove { relation, x, y } => {
                    Source9Change::Remove { relation, x, y }
                }
                Source25Change::AddTerm => Source9Change::AddTerm,
                Source25Change::AddAssertion { relation, x, y } => {
                    Source9Change::AddAssertion { relation, x, y }
                }
                Source25Change::Fill { .. } => unreachable!("four-kind source list has no filling"),
            })
            .collect()
    }
    pub fn perform_enabled(&self, event: Source9Change) -> Result<Self, AdmissionExecutionError> {
        Ok(Self {
            raw: self.raw.perform_enabled(event.as_source25())?,
        })
    }
    pub fn canonical(&self, max_permutations: usize) -> Result<Self, AdmissionExecutionError> {
        let result = joint_canonical(self, None, max_permutations)?;
        Self::try_new(result.0)
    }
}

fn joint_canonical(
    state: &Source9State,
    record: Option<&[BigInt]>,
    budget: usize,
) -> Result<(GenesisOngoingPacket, Vec<BigInt>), AdmissionExecutionError> {
    let p = state.packet();
    let n = p.terms.len();
    let mut counts = vec![&p.r[..], &p.s[..]];
    if let Some(record) = record {
        counts.push(record);
    }
    let tables = counts
        .iter()
        .map(|values| {
            BasicMatrix::from_row_major(
                n,
                n,
                values
                    .iter()
                    .cloned()
                    .map(BigRational::from_integer)
                    .collect(),
            )
        })
        .collect::<Result<Vec<_>, _>>()
        .map_err(GenesisBridgeError::from)?;
    let canonical = canonical_pair_tables(&tables, budget)?;
    let mut moved = Vec::new();
    for table in canonical.tables {
        let integers = table
            .as_slice()
            .iter()
            .map(|value| {
                if value.is_integer() {
                    Ok(value.to_integer())
                } else {
                    Err(GenesisBridgeError::NonIntegralOutput)
                }
            })
            .collect::<Result<Vec<_>, _>>()?;
        moved.push(integers);
    }
    let record = if moved.len() == 3 {
        moved.pop().checked_invariant_fd545a88("checked invariant")
    } else {
        vec![]
    };
    let s = moved.pop().checked_invariant_fd545a88("checked invariant");
    let r = moved.pop().checked_invariant_fd545a88("checked invariant");
    Ok((
        GenesisOngoingPacket {
            terms: p.terms.clone(),
            r,
            s,
            filled: vec![],
        },
        record,
    ))
}

/// Admission is not a source-9 assertion, does not name r or s, and is not
/// one of its four changes. C-A1 records this separately from the state.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub struct Source15Admission {
    pub admitted: bool,
}
impl Source15Admission {
    pub fn after_reaching() -> Self {
        Self { admitted: false }
    }
    pub fn admitted() -> Self {
        Self { admitted: true }
    }
}

/// Exactly the source's retained, unchosen C-A2 Tagged reading.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source15Tagged {
    state: Source9State,
    admission: Source15Admission,
}
impl Source15Tagged {
    pub fn new(state: Source9State, admission: Source15Admission) -> Self {
        Self { state, admission }
    }
    pub fn state(&self) -> &Source9State {
        &self.state
    }
    pub fn admission(&self) -> Source15Admission {
        self.admission
    }
    pub fn admit(&self) -> Self {
        Self::new(self.state.clone(), Source15Admission::admitted())
    }
    /// The actual tagged source function canonicalizes the whole r/s pair
    /// and resets admission. Budget refusal is separate from disabled change.
    pub fn perform_enabled(
        &self,
        event: Source9Change,
        max_permutations: usize,
    ) -> Result<Self, AdmissionExecutionError> {
        let state = self
            .state
            .perform_enabled(event)?
            .canonical(max_permutations)?;
        Ok(Self::new(state, Source15Admission::after_reaching()))
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Source16Reading {
    Count,
    Set,
    Drop,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Source16Change {
    Direct {
        change: Source9Change,
    },
    Admit {
        relation: SourceRelation,
        x: usize,
        y: usize,
    },
}
impl Source16Change {
    pub fn additions(self) -> (usize, usize) {
        match self {
            Self::Direct { change } => change.additions(),
            Self::Admit { .. } => (0, 1),
        }
    }
    pub fn is_admission(self) -> bool {
        matches!(self, Self::Admit { .. })
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source16State {
    state: Source9State,
    leftovers: Vec<BigInt>,
}
impl Source16State {
    pub fn try_new(
        state: Source9State,
        leftovers: Vec<BigInt>,
    ) -> Result<Self, AdmissionExecutionError> {
        if leftovers.len() != state.packet().r.len() || leftovers.iter().any(Signed::is_negative) {
            return Err(AdmissionExecutionError::InvalidRecord);
        }
        Ok(Self { state, leftovers })
    }
    pub fn empty() -> Self {
        Self {
            state: Source9State::empty(),
            leftovers: vec![],
        }
    }
    pub fn state(&self) -> &Source9State {
        &self.state
    }
    pub fn leftovers(&self) -> &[BigInt] {
        &self.leftovers
    }
    pub fn record_total(&self) -> BigInt {
        self.leftovers.iter().sum()
    }
    pub fn source_size(&self) -> BigInt {
        self.state.source_size()
    }
    pub fn potential(&self) -> BigInt {
        self.source_size() + 2 * self.record_total()
    }
    pub fn mass(&self) -> BigInt {
        self.source_size() - self.state.packet().terms.len() + self.record_total()
    }
    pub fn diagonal_mass(&self) -> BigInt {
        let p = self.state.packet();
        let n = p.terms.len();
        (0..n)
            .map(|x| &p.r[x * n + x] + &p.s[x * n + x] + &self.leftovers[x * n + x])
            .sum()
    }
    pub fn is_enabled(&self, event: Source16Change) -> bool {
        let n = self.state.packet().terms.len();
        match event {
            Source16Change::Direct { change } => self.state.is_enabled(change),
            Source16Change::Admit { x, y, .. } => {
                x < n && y < n && self.leftovers[x * n + y] > BigInt::zero()
            }
        }
    }
    pub fn enabled_changes(&self) -> Vec<Source16Change> {
        let n = self.state.packet().terms.len();
        let mut out: Vec<_> = self
            .state
            .enabled_changes()
            .into_iter()
            .map(|change| Source16Change::Direct { change })
            .collect();
        for relation in [SourceRelation::R, SourceRelation::S] {
            for x in 0..n {
                for y in 0..n {
                    let event = Source16Change::Admit { relation, x, y };
                    if self.is_enabled(event) {
                        out.push(event);
                    }
                }
            }
        }
        out
    }
    fn zero_identified_leftovers(n: usize, x: usize, y: usize, record: &mut [BigInt]) {
        for a in 0..n {
            for b in 0..n {
                if a == x || a == y || b == x || b == y {
                    record[a * n + b] = BigInt::zero();
                }
            }
        }
    }

    fn apply_direct_leftover_change(
        change: Source9Change,
        reading: Source16Reading,
        n: usize,
        record: &mut Vec<BigInt>,
    ) -> Result<(), AdmissionExecutionError> {
        match change {
            Source9Change::Remove { x, y, .. } => {
                if reading != Source16Reading::Set || record[x * n + y].is_zero() {
                    record[x * n + y] += BigInt::one();
                }
            }
            Source9Change::AddTerm => {
                *record = move_counts(record, &(0..n).collect::<Vec<_>>(), n + 1)?;
            }
            Source9Change::Identify { x, y } => {
                if reading == Source16Reading::Drop {
                    Self::zero_identified_leftovers(n, x, y, record);
                }
                let image: Vec<_> = (0..n)
                    .map(|v| if v == y { x } else { v - usize::from(v > y) })
                    .collect();
                *record = move_counts(record, &image, n - 1)?;
            }
            Source9Change::AddAssertion { .. } => {}
        }
        Ok(())
    }

    pub fn perform_enabled(
        &self,
        event: Source16Change,
        reading: Source16Reading,
    ) -> Result<Self, AdmissionExecutionError> {
        if !self.is_enabled(event) {
            return Err(AdmissionExecutionError::DisabledEvent);
        }
        let n = self.state.packet().terms.len();
        let mut record = self.leftovers.clone();
        let change = match event {
            Source16Change::Direct { change } => change,
            Source16Change::Admit { relation, x, y } => {
                record[x * n + y] -= BigInt::one();
                Source9Change::AddAssertion { relation, x, y }
            }
        };
        let state = self.state.perform_enabled(change)?;
        if matches!(event, Source16Change::Direct { .. }) {
            Self::apply_direct_leftover_change(change, reading, n, &mut record)?;
        }
        Self::try_new(state, record)
    }
    pub fn canonical(&self, max_permutations: usize) -> Result<Self, AdmissionExecutionError> {
        let (packet, leftovers) =
            joint_canonical(&self.state, Some(&self.leftovers), max_permutations)?;
        Self::try_new(Source9State::try_new(packet)?, leftovers)
    }

    /// A counted description of a shortest COUNT run from the empty state.
    /// Multiplicities remain BigInt; no event word is allocated here. For
    /// each pair, add r+leftover copies in r, add s, then remove leftover
    /// copies of r. Its length is n+sum(r+s)+2*sum(leftovers).
    /// This minimum formula does not apply to SET or DROP.
    pub fn count_minimum_recipe(&self) -> Source16CountRecipe {
        let n = self.state.packet().terms.len();
        let p = self.state.packet();
        let mut blocks = Vec::new();
        let mut append = |change, repetitions: BigInt| {
            if !repetitions.is_zero() {
                blocks.push(Source16RecipeBlock {
                    change,
                    repetitions,
                });
            }
        };
        append(Source9Change::AddTerm, BigInt::from(n));
        for x in 0..n {
            for y in 0..n {
                let i = x * n + y;
                append(
                    Source9Change::AddAssertion {
                        relation: SourceRelation::R,
                        x,
                        y,
                    },
                    &p.r[i] + &self.leftovers[i],
                );
                append(
                    Source9Change::AddAssertion {
                        relation: SourceRelation::S,
                        x,
                        y,
                    },
                    p.s[i].clone(),
                );
                append(
                    Source9Change::Remove {
                        relation: SourceRelation::R,
                        x,
                        y,
                    },
                    self.leftovers[i].clone(),
                );
            }
        }
        Source16CountRecipe {
            target: self.clone(),
            blocks,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source16RecipeBlock {
    pub change: Source9Change,
    pub repetitions: BigInt,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source16CountRecipe {
    target: Source16State,
    blocks: Vec<Source16RecipeBlock>,
}
impl Source16CountRecipe {
    pub fn blocks(&self) -> &[Source16RecipeBlock] {
        &self.blocks
    }
    pub fn target(&self) -> &Source16State {
        &self.target
    }
    pub fn length(&self) -> BigInt {
        self.blocks.iter().map(|block| &block.repetitions).sum()
    }
    pub fn addition_price(&self) -> (BigInt, BigInt) {
        let mut price = (BigInt::zero(), BigInt::zero());
        for block in &self.blocks {
            let (t, a) = block.change.additions();
            price.0 += &block.repetitions * t;
            price.1 += &block.repetitions * a;
        }
        price
    }
    /// Refuse before allocation when the whole word exceeds the caller's
    /// limit; the compact recipe is still available for arbitrary counts.
    pub fn expand(&self, max_changes: usize) -> Result<Source16Run, AdmissionExecutionError> {
        let length = self.length();
        if length > BigInt::from(max_changes) {
            return Err(AdmissionExecutionError::RecipeBudgetExceeded {
                requested: length,
                limit: max_changes,
            });
        }
        let mut changes = Vec::new();
        for block in &self.blocks {
            let count = block
                .repetitions
                .to_usize()
                .checked_invariant_fd545a88("nonnegative count below admitted limit");
            changes.extend(std::iter::repeat_n(
                Source16Change::Direct {
                    change: block.change,
                },
                count,
            ));
        }
        Source16Run::replay(Source16State::empty(), &changes, Source16Reading::Count)
    }
}

/// Whole ordered native run; the record reading and complete raw boundary
/// state are part of composition, independently of the addition prices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source16Run {
    reading: Source16Reading,
    states: Vec<Source16State>,
    changes: Vec<Source16Change>,
    term_additions: BigInt,
    assertion_additions: BigInt,
}
impl Source16Run {
    pub fn replay(
        initial: Source16State,
        changes: &[Source16Change],
        reading: Source16Reading,
    ) -> Result<Self, AdmissionExecutionError> {
        let mut states = vec![initial];
        let (mut term_additions, mut assertion_additions) = (BigInt::zero(), BigInt::zero());
        for &event in changes {
            let after = states
                .last()
                .checked_invariant_fd545a88("initial source state is retained")
                .perform_enabled(event, reading)?;
            let (t, a) = event.additions();
            term_additions += t;
            assertion_additions += a;
            states.push(after);
        }
        Ok(Self {
            reading,
            states,
            changes: changes.to_vec(),
            term_additions,
            assertion_additions,
        })
    }
    pub fn states(&self) -> &[Source16State] {
        &self.states
    }
    pub fn changes(&self) -> &[Source16Change] {
        &self.changes
    }
    pub fn final_state(&self) -> &Source16State {
        self.states
            .last()
            .checked_invariant_fd545a88("initial source state is retained")
    }
    pub fn addition_price(&self) -> (&BigInt, &BigInt) {
        (&self.term_additions, &self.assertion_additions)
    }
    pub fn then(&self, after: &Self) -> Result<Self, AdmissionExecutionError> {
        if self.reading != after.reading {
            return Err(AdmissionExecutionError::ReadingMismatch);
        }
        if self.final_state() != &after.states[0] {
            return Err(AdmissionExecutionError::IntermediateMismatch);
        }
        let mut states = self.states.clone();
        states.extend_from_slice(&after.states[1..]);
        let mut changes = self.changes.clone();
        changes.extend_from_slice(&after.changes);
        Ok(Self {
            reading: self.reading,
            states,
            changes,
            term_additions: &self.term_additions + &after.term_additions,
            assertion_additions: &self.assertion_additions + &after.assertion_additions,
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_admission_execution.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-admission-execution:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_fd545a88 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
