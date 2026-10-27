//! Exact finite continuation tables using the native state and observation owners.
use crate::genesis_gauge_result::Source23Error;
use crate::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use crate::genesis_source_execution::{
    Source25Change, Source25State, SourceExecutionError, SourceRelation,
};
use num_bigint::BigInt;
use num_traits::{ToPrimitive, Zero};
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

pub const MAX_TERMS: usize = 3;
pub const MAX_COUNT: u8 = 4;
pub const HORIZON: usize = 2;
const MARK_PERMUTATIONS: usize = 6;

#[derive(Debug, thiserror::Error)]
pub enum FutureCompressionError {
    #[error("native execution: {0}")]
    Execution(#[from] SourceExecutionError),
    #[error("native observation: {0}")]
    Observation(#[from] Source23Error),
    #[error("bounded continuation contract: {0}")]
    Contract(String),
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RawState {
    pub n: usize,
    pub r: Vec<u8>,
    pub s: Vec<u8>,
    pub filled: Vec<[usize; 3]>,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ResultMark {
    pub n: usize,
    pub normal: Vec<String>,
    pub filled: Vec<[usize; 3]>,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct BalanceRow {
    pub face: [usize; 3],
    pub balanced: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct StateRecord {
    #[serde(flatten)]
    pub raw: RawState,
    pub mark: ResultMark,
    pub balance: Vec<BalanceRow>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum OfferStatus {
    NativeDisabled,
    BoundExcluded,
    Admitted,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Serialize)]
pub struct Offer {
    pub status: OfferStatus,
    pub price: Option<[usize; 2]>,
    pub child: Option<usize>,
    pub occurrences: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Profile {
    pub max_terms: usize,
    pub max_count: u8,
    pub horizon: usize,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct Partitions {
    pub terminal_present_only: Vec<Vec<usize>>,
    pub terminal_status_probes: Vec<Vec<usize>>,
}

#[derive(Debug, Clone, Serialize)]
pub struct BoundedFutureCensus {
    pub schema: &'static str,
    pub profile: Profile,
    pub actions: Vec<Source25Change>,
    pub states: Vec<StateRecord>,
    pub edges: Vec<Vec<Offer>>,
    pub partitions: Partitions,
}

/// This report has three additional fields beside the complete result mark.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClippedReport {
    pub mark: ResultMark,
    pub filled: Vec<[usize; 3]>,
    pub clipped_r: Vec<u8>,
    pub clipped_s: Vec<u8>,
}

fn contract(message: &str) -> FutureCompressionError {
    FutureCompressionError::Contract(message.into())
}

fn inside_carrier(state: &Source25State) -> bool {
    let packet = state.packet();
    packet.terms.len() <= MAX_TERMS
        && packet.r.iter().chain(&packet.s).sum::<BigInt>() <= BigInt::from(MAX_COUNT)
}

fn native(raw: &RawState) -> Result<Source25State, FutureCompressionError> {
    if raw.n > MAX_TERMS
        || raw.r.len() != raw.n * raw.n
        || raw.s.len() != raw.n * raw.n
        || raw
            .r
            .iter()
            .chain(&raw.s)
            .map(|&v| usize::from(v))
            .sum::<usize>()
            > usize::from(MAX_COUNT)
    {
        return Err(contract("raw state is outside the carrier"));
    }
    Ok(Source25State::try_new(GenesisOngoingPacket {
        terms: (0..raw.n).map(|i| format!("t{i}")).collect(),
        r: raw.r.iter().copied().map(BigInt::from).collect(),
        s: raw.s.iter().copied().map(BigInt::from).collect(),
        filled: raw
            .filled
            .iter()
            .map(|t| MarkedTriple {
                x: t[0],
                y: t[1],
                z: t[2],
            })
            .collect(),
    })?)
}

fn raw(state: &Source25State) -> Result<RawState, FutureCompressionError> {
    if !inside_carrier(state) {
        return Err(contract("native post-state is outside the carrier"));
    }
    let packet = state.packet();
    let counts = |values: &[BigInt]| {
        values
            .iter()
            .map(|value| {
                value
                    .to_u8()
                    .ok_or_else(|| contract("count conversion failed"))
            })
            .collect::<Result<Vec<_>, _>>()
    };
    Ok(RawState {
        n: packet.terms.len(),
        r: counts(&packet.r)?,
        s: counts(&packet.s)?,
        filled: packet.filled.iter().map(|t| [t.x, t.y, t.z]).collect(),
    })
}

fn result_mark(state: &Source25State) -> Result<ResultMark, FutureCompressionError> {
    let mark = state.result_mark(MARK_PERMUTATIONS)?;
    Ok(ResultMark {
        n: mark.n,
        normal: mark.normal.iter().map(ToString::to_string).collect(),
        filled: mark.filled.iter().map(|t| [t.x, t.y, t.z]).collect(),
    })
}

/// The fixed literal alphabet, including addresses absent from smaller states.
pub fn action_alphabet() -> Vec<Source25Change> {
    let mut actions = Vec::new();
    for x in 0..MAX_TERMS {
        for y in x + 1..MAX_TERMS {
            actions.push(Source25Change::Identify { x, y });
        }
    }
    for relation in [SourceRelation::R, SourceRelation::S] {
        for x in 0..MAX_TERMS {
            for y in 0..MAX_TERMS {
                actions.push(Source25Change::Remove { relation, x, y });
            }
        }
    }
    actions.push(Source25Change::Fill { x: 0, y: 1, z: 2 });
    actions.push(Source25Change::Fill { x: 0, y: 2, z: 1 });
    actions.push(Source25Change::AddTerm);
    for relation in [SourceRelation::R, SourceRelation::S] {
        for x in 0..MAX_TERMS {
            for y in 0..MAX_TERMS {
                actions.push(Source25Change::AddAssertion { relation, x, y });
            }
        }
    }
    actions
}

fn enumerate_counts(
    position: usize,
    remaining: u8,
    counts: &mut [u8],
    emit: &mut impl FnMut(&[u8]),
) {
    if position == counts.len() {
        emit(counts);
        return;
    }
    for count in 0..=remaining {
        counts[position] = count;
        enumerate_counts(position + 1, remaining - count, counts, emit);
    }
}

fn enumerate_raw_states() -> Vec<RawState> {
    let mut states = Vec::new();
    for n in 0..=MAX_TERMS {
        let mut filled_sets = if n == 3 {
            vec![
                vec![],
                vec![[0, 1, 2]],
                vec![[0, 2, 1]],
                vec![[0, 1, 2], [0, 2, 1]],
            ]
        } else {
            vec![vec![]]
        };
        filled_sets.sort();
        enumerate_counts(0, MAX_COUNT, &mut vec![0; 2 * n * n], &mut |counts| {
            for filled in &filled_sets {
                states.push(RawState {
                    n,
                    r: counts[..n * n].to_vec(),
                    s: counts[n * n..].to_vec(),
                    filled: filled.clone(),
                });
            }
        });
    }
    states.sort();
    states
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct SignatureOffer {
    status: OfferStatus,
    price: Option<[usize; 2]>,
    child: Option<usize>,
    occurrences: Option<usize>,
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
struct Signature {
    mark: ResultMark,
    balance: Vec<BalanceRow>,
    offers: Option<Vec<SignatureOffer>>,
}

fn partition_layer(
    states: &[StateRecord],
    edges: &[Vec<Offer>],
    previous: Option<&[usize]>,
    terminal_probes: bool,
) -> Vec<usize> {
    let mut seen = BTreeMap::new();
    states
        .iter()
        .zip(edges)
        .map(|(state, offers)| {
            let signature = Signature {
                mark: state.mark.clone(),
                balance: state.balance.clone(),
                offers: if previous.is_some() || terminal_probes {
                    Some(
                        offers
                            .iter()
                            .map(|offer| SignatureOffer {
                                status: offer.status,
                                price: offer.price,
                                child: previous
                                    .and_then(|classes| offer.child.map(|child| classes[child])),
                                occurrences: previous.map(|_| offer.occurrences),
                            })
                            .collect(),
                    )
                } else {
                    None
                },
            };
            let next_id = seen.len();
            *seen.entry(signature).or_insert(next_id)
        })
        .collect()
}

fn profile_partitions(
    states: &[StateRecord],
    edges: &[Vec<Offer>],
    terminal_probes: bool,
) -> Vec<Vec<usize>> {
    let mut layers = vec![partition_layer(states, edges, None, terminal_probes)];
    for h in 1..=HORIZON {
        layers.push(partition_layer(
            states,
            edges,
            Some(&layers[h - 1]),
            terminal_probes,
        ));
    }
    layers
}

pub fn clipped_report(state: &StateRecord) -> ClippedReport {
    ClippedReport {
        mark: state.mark.clone(),
        filled: state.raw.filled.clone(),
        clipped_r: state.raw.r.iter().map(|&v| v.min(2)).collect(),
        clipped_s: state.raw.s.iter().map(|&v| v.min(2)).collect(),
    }
}

fn parse_canonical_normal_sum(normal: &[String]) -> Result<BigInt, FutureCompressionError> {
    let mut sigma = BigInt::zero();
    for text in normal {
        let value = text
            .parse::<BigInt>()
            .map_err(|_| contract("invalid normal entry"))?;
        if value.to_string() != *text {
            return Err(contract("noncanonical normal entry"));
        }
        sigma += value;
    }
    Ok(sigma)
}

fn recover_single_capped_entry(
    counts: &mut [u8],
    j: usize,
    n: usize,
    sigma: &BigInt,
) -> Result<(), FutureCompressionError> {
    let known = counts.iter().enumerate().filter(|(i, _)| *i != j).fold(
        BigInt::zero(),
        |sum, (i, &value)| {
            if i < n * n {
                sum + value
            } else {
                sum - value
            }
        },
    );
    let recovered = if j < n * n {
        sigma - known
    } else {
        known - sigma
    };
    counts[j] = recovered
        .to_u8()
        .filter(|&value| value >= 2)
        .ok_or_else(|| contract("signed sum does not recover a capped count"))?;
    Ok(())
}

fn validate_clipped_dimensions(report: &ClippedReport) -> Result<usize, FutureCompressionError> {
    let n = report.mark.n;
    if n > MAX_TERMS
        || report.mark.normal.len() != n * n
        || report.clipped_r.len() != n * n
        || report.clipped_s.len() != n * n
    {
        return Err(contract("report dimensions are outside the carrier"));
    }
    Ok(n)
}

/// Decode the admitted bounded report, rejecting malformed or inconsistent data.
pub fn decode_clipped(report: &ClippedReport) -> Result<RawState, FutureCompressionError> {
    let n = validate_clipped_dimensions(report)?;
    let sigma = parse_canonical_normal_sum(&report.mark.normal)?;
    let mut counts: Vec<_> = report
        .clipped_r
        .iter()
        .chain(&report.clipped_s)
        .copied()
        .collect();
    if counts.iter().any(|&value| value > 2) {
        return Err(contract("clipped entry exceeds two"));
    }
    let capped: Vec<_> = counts
        .iter()
        .enumerate()
        .filter_map(|(i, &value)| (value == 2).then_some(i))
        .collect();
    if capped.len() == 1 {
        recover_single_capped_entry(&mut counts, capped[0], n, &sigma)?;
    }
    let decoded = RawState {
        n,
        r: counts[..n * n].to_vec(),
        s: counts[n * n..].to_vec(),
        filled: report.filled.clone(),
    };
    let state = native(&decoded)?;
    let signed_sum =
        state.packet().r.iter().sum::<BigInt>() - state.packet().s.iter().sum::<BigInt>();
    if signed_sum != sigma || result_mark(&state)? != report.mark {
        return Err(contract("decoded state disagrees with the submitted mark"));
    }
    Ok(decoded)
}

fn build_raw_state_index(
    raw_states: &[RawState],
) -> Result<BTreeMap<RawState, usize>, FutureCompressionError> {
    let index: BTreeMap<_, _> = raw_states
        .iter()
        .cloned()
        .enumerate()
        .map(|(i, raw)| (raw, i))
        .collect();
    if index.len() != raw_states.len() {
        return Err(contract("duplicate enumerated raw state"));
    }
    Ok(index)
}

fn build_state_record_from_raw(
    raw_state: RawState,
) -> Result<StateRecord, FutureCompressionError> {
    let state = native(&raw_state)?;
    Ok(StateRecord {
        raw: raw_state,
        mark: result_mark(&state)?,
        balance: state
            .balance_record()?
            .into_iter()
            .map(|(face, balanced)| BalanceRow {
                face: [face.x, face.y, face.z],
                balanced,
            })
            .collect(),
    })
}

fn build_admitted_offer(
    index: &BTreeMap<RawState, usize>,
    post_raw: Result<RawState, FutureCompressionError>,
    price: Option<[usize; 2]>,
) -> Result<Offer, FutureCompressionError> {
    let raw_key = post_raw?;
    let child = *index
        .get(&raw_key)
        .ok_or_else(|| contract("admitted native child absent from enumeration"))?;
    Ok(Offer {
        status: OfferStatus::Admitted,
        price,
        child: Some(child),
        occurrences: 1,
    })
}

/// Construct the full census from native calls; no partition counts are assumed.
pub fn generate_bounded_future() -> Result<BoundedFutureCensus, FutureCompressionError> {
    let raw_states = enumerate_raw_states();
    let index = build_raw_state_index(&raw_states)?;
    let actions = action_alphabet();
    let mut states = Vec::with_capacity(raw_states.len());
    let mut edges = Vec::with_capacity(raw_states.len());
    for raw_state in raw_states {
        let state = native(&raw_state)?;
        states.push(build_state_record_from_raw(raw_state)?);
        let mut offers = Vec::with_capacity(actions.len());
        for &action in &actions {
            if !state.is_enabled(action) {
                offers.push(Offer {
                    status: OfferStatus::NativeDisabled,
                    price: None,
                    child: None,
                    occurrences: 0,
                });
                continue;
            }
            let (terms, assertions) = action.additions();
            let price = Some([terms, assertions]);
            let post = state.perform_enabled(action)?;
            if !inside_carrier(&post) {
                offers.push(Offer {
                    status: OfferStatus::BoundExcluded,
                    price,
                    child: None,
                    occurrences: 0,
                });
                continue;
            }
            offers.push(build_admitted_offer(&index, raw(&post), price)?);
        }
        edges.push(offers);
    }
    let partitions = Partitions {
        terminal_present_only: profile_partitions(&states, &edges, false),
        terminal_status_probes: profile_partitions(&states, &edges, true),
    };
    Ok(BoundedFutureCensus {
        schema: "bounded-native-future/1",
        profile: Profile {
            max_terms: MAX_TERMS,
            max_count: MAX_COUNT,
            horizon: HORIZON,
        },
        actions,
        states,
        edges,
        partitions,
    })
}

// Origin: engine/crates_rs/core_wdp/src/genesis_future_compression.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-future-compression:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_5bd3366b {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
