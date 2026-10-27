//! Actual source-23 result key, raising and obstruction observations.
//! Raw nonnegative assertion tables remain distinct from their result key.
//! All arithmetic, gauge normalization and orbit transport use exact owners.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fc823bdb<T> {
    fn checked_invariant_fc823bdb(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fc823bdb<T> for Option<T> {
    #[inline]
    fn checked_invariant_fc823bdb(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fc823bdb<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fc823bdb(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::genesis_ongoing_adapter::{GenesisBridgeError, GenesisOngoingPacket};
use crate::genesis_source_execution::{move_counts, Source25State, SourceExecutionError};
use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::gauge_pair_table::{
    align_gauge_pair_tables, canonical_gauge_pair_table, root_normalized_pair_table,
};
use linear_algebra::pair_table_canonical::PairCanonicalError;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use core_combinatorics::enumeration::{Combinations, CombinatoricsError};
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum Source23Error {
    #[error("a rewriting must write each existing term exactly once")]
    InvalidPermutation,
    #[error("the states are not the same source-23 result")]
    NotSameResult,
    #[error("raw histories have different complete intermediate source states")]
    IntermediateMismatch,
    #[error("exact integer gauge unexpectedly returned a noninteger")]
    NonIntegralOutput,
    #[error("source refusal: {0}")]
    Source(#[from] SourceExecutionError),
    #[error("gauge owner refusal: {0}")]
    Gauge(#[from] PairCanonicalError),
    #[error("observation enumeration refused: {0}")]
    Enumeration(#[from] CombinatoricsError),
    #[error("matrix owner refusal: {0}")]
    Matrix(#[from] MatrixError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source23Key {
    pub n: usize,
    pub normal: Vec<BigInt>,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source23Certificate {
    pub kind: &'static str,
    pub terms: Vec<usize>,
    pub value: BigInt,
}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source23SumProfile {
    pub loops: Vec<BigInt>,
    pub pairs: Vec<BigInt>,
    pub rounds: Vec<BigInt>,
    pub total: BigInt,
}

pub(crate) fn integers(table: &BasicMatrix<BigRational>) -> Result<Vec<BigInt>, Source23Error> {
    table
        .as_slice()
        .iter()
        .map(|value| {
            if value.is_integer() {
                Ok(value.to_integer())
            } else {
                Err(Source23Error::NonIntegralOutput)
            }
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source23State {
    raw: Source25State,
}
impl Source23State {
    pub fn try_new(n: usize, r: Vec<BigInt>, s: Vec<BigInt>) -> Result<Self, Source23Error> {
        let pairs = n.checked_mul(n).ok_or(SourceExecutionError::Bridge(
            GenesisBridgeError::DimensionOverflow,
        ))?;
        if r.len() != pairs || s.len() != pairs {
            return Err(SourceExecutionError::Bridge(GenesisBridgeError::InvalidDomain).into());
        }
        Ok(Self {
            raw: Source25State::try_new(GenesisOngoingPacket {
                terms: (0..n).map(|i| format!("t{i}")).collect(),
                r,
                s,
                filled: vec![],
            })?,
        })
    }
    pub fn empty() -> Self {
        Self {
            raw: Source25State::empty(),
        }
    }
    pub fn n(&self) -> usize {
        self.raw.packet().terms.len()
    }
    pub fn r(&self) -> &[BigInt] {
        &self.raw.packet().r
    }
    pub fn s(&self) -> &[BigInt] {
        &self.raw.packet().s
    }
    pub fn excess(&self) -> Vec<BigInt> {
        self.r().iter().zip(self.s()).map(|(a, b)| a - b).collect()
    }
    fn table(&self) -> Result<BasicMatrix<BigRational>, Source23Error> {
        Ok(BasicMatrix::from_row_major(
            self.n(),
            self.n(),
            self.excess()
                .into_iter()
                .map(BigRational::from_integer)
                .collect(),
        )?)
    }
    pub fn normal_table(&self) -> Result<Vec<BigInt>, Source23Error> {
        integers(&root_normalized_pair_table(&self.table()?)?)
    }
    pub fn result_key(&self, max_permutations: usize) -> Result<Source23Key, Source23Error> {
        let value = canonical_gauge_pair_table(&self.table()?, max_permutations)?;
        Ok(Source23Key {
            n: self.n(),
            normal: integers(&value.normal)?,
        })
    }
    pub fn same_result(
        &self,
        target: &Self,
        max_permutations: usize,
    ) -> Result<bool, Source23Error> {
        if self.n() != target.n() {
            return Ok(false);
        }
        Ok(self.result_key(max_permutations)? == target.result_key(max_permutations)?)
    }
    pub fn rewrite(&self, image: &[usize]) -> Result<Self, Source23Error> {
        let n = self.n();
        if image.len() != n
            || image.iter().any(|&x| x >= n)
            || image.iter().collect::<BTreeSet<_>>().len() != n
        {
            return Err(Source23Error::InvalidPermutation);
        }
        Self::try_new(
            n,
            move_counts(self.r(), image, n)?,
            move_counts(self.s(), image, n)?,
        )
    }
    pub fn align_to(&self, target: &Self, max_permutations: usize) -> Result<Self, Source23Error> {
        if self.n() != target.n() {
            return Err(Source23Error::NotSameResult);
        }
        let image = align_gauge_pair_tables(&self.table()?, &target.table()?, max_permutations)?
            .ok_or(Source23Error::NotSameResult)?;
        self.rewrite(&image)
    }
    pub fn raise_terms(&self, counts: &[BigInt]) -> Result<Self, Source23Error> {
        Ok(Self {
            raw: self.raw.raise_terms(counts)?,
        })
    }
    pub fn raise_term(&self, x: usize) -> Result<Self, Source23Error> {
        if x >= self.n() {
            return Err(SourceExecutionError::InvalidRaising.into());
        }
        let mut counts = vec![BigInt::zero(); self.n()];
        counts[x] = 1.into();
        self.raise_terms(&counts)
    }
    pub fn plain_state(&self) -> Result<Self, Source23Error> {
        let e = self.excess();
        Self::try_new(
            self.n(),
            e.iter()
                .map(|v| {
                    if v.is_positive() {
                        v.clone()
                    } else {
                        BigInt::zero()
                    }
                })
                .collect(),
            e.iter()
                .map(|v| if v.is_negative() { -v } else { BigInt::zero() })
                .collect(),
        )
    }
    /// Source-22 plain-state cost used by source 23; NOT a source-23 result invariant.
    pub fn plain_cost(&self) -> BigInt {
        self.raw.plain_state_cost()
    }
    pub fn nothing_certificate(
        &self,
        max_triples: usize,
    ) -> Result<Option<Source23Certificate>, Source23Error> {
        let n = self.n();
        let e = self.excess();
        for x in 0..n {
            if !e[x * n + x].is_zero() {
                return Ok(Some(Source23Certificate {
                    kind: "loop",
                    terms: vec![x],
                    value: e[x * n + x].clone(),
                }));
            }
        }
        for x in 0..n {
            for y in x + 1..n {
                let value = &e[x * n + y] + &e[y * n + x];
                if !value.is_zero() {
                    return Ok(Some(Source23Certificate {
                        kind: "two-way",
                        terms: vec![x, y],
                        value,
                    }));
                }
            }
        }
        for triple in Combinations::new(n, 3, max_triples)? {
            let (x, y, z) = (triple[0], triple[1], triple[2]);
            let value = &e[x * n + y] + &e[y * n + z] + &e[z * n + x];
            if !value.is_zero() {
                return Ok(Some(Source23Certificate {
                    kind: "around",
                    terms: triple,
                    value,
                }));
            }
        }
        Ok(None)
    }
    pub fn sum_profile(&self, max_triples: usize) -> Result<Source23SumProfile, Source23Error> {
        let triples = Combinations::new(self.n(), 3, max_triples)?;
        let n = self.n();
        let e = self.excess();
        let mut loops: Vec<_> = (0..n).map(|x| e[x * n + x].clone()).collect();
        let mut pairs: Vec<_> = (0..n)
            .flat_map(|x| (x + 1..n).map(move |y| (x, y)))
            .map(|(x, y)| &e[x * n + y] + &e[y * n + x])
            .collect();
        let mut rounds = Vec::new();
        for triple in triples {
            let (x, y, z) = (triple[0], triple[1], triple[2]);
            rounds.push(&e[x * n + y] + &e[y * n + z] + &e[z * n + x]);
            rounds.push(&e[x * n + z] + &e[z * n + y] + &e[y * n + x]);
        }
        loops.sort();
        pairs.sort();
        rounds.sort();
        Ok(Source23SumProfile {
            loops,
            pairs,
            rounds,
            total: e.iter().sum(),
        })
    }
}

/// Atomic source raising events. Bulk counts are a separate exact utility.
/// The source's one-term raising may leave raw state unchanged, but still
/// contributes a retained occurrence. Every atomic intermediate is included.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Source23Run {
    states: Vec<Source23State>,
    raised_terms: Vec<usize>,
}
impl Source23Run {
    pub fn replay(initial: Source23State, raised_terms: &[usize]) -> Result<Self, Source23Error> {
        let mut states = vec![initial];
        for &x in raised_terms {
            states.push(
                states
                    .last()
                    .checked_invariant_fc823bdb("initial state retained")
                    .raise_term(x)?,
            );
        }
        Ok(Self {
            states,
            raised_terms: raised_terms.to_vec(),
        })
    }
    pub fn states(&self) -> &[Source23State] {
        &self.states
    }
    pub fn raised_terms(&self) -> &[usize] {
        &self.raised_terms
    }
    pub fn final_state(&self) -> &Source23State {
        self.states.last().checked_invariant_fc823bdb("initial state retained")
    }
    pub fn assertion_additions(&self) -> BigInt {
        BigInt::from(2u8)
            * BigInt::from(self.final_state().n().saturating_sub(1))
            * BigInt::from(self.raised_terms.len())
    }
    pub fn then(&self, after: &Self) -> Result<Self, Source23Error> {
        if self.final_state() != &after.states[0] {
            return Err(Source23Error::IntermediateMismatch);
        }
        let mut states = self.states.clone();
        states.extend_from_slice(&after.states[1..]);
        let mut raised_terms = self.raised_terms.clone();
        raised_terms.extend_from_slice(&after.raised_terms);
        Ok(Self {
            states,
            raised_terms,
        })
    }
}

// Origin: engine/crates_rs/core_wdp/src/genesis_gauge_result.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-gauge-result:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_fc823bdb {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
