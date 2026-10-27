use num_bigint::BigInt;
use core_wdp::genesis_future_compression::*;
use core_wdp::genesis_source_execution::{Source25Change, SourceRelation};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::OnceLock;

fn census() -> &'static BoundedFutureCensus {
    static CENSUS: OnceLock<BoundedFutureCensus> = OnceLock::new();
    CENSUS.get_or_init(|| generate_bounded_future().unwrap())
}

fn state(
    n: usize,
    r: &[(usize, usize, u8)],
    s: &[(usize, usize, u8)],
    filled: &[[usize; 3]],
) -> RawState {
    let table = |entries: &[(usize, usize, u8)]| {
        let mut out = vec![0; n * n];
        for &(x, y, value) in entries {
            out[x * n + y] = value;
        }
        out
    };
    RawState {
        n,
        r: table(r),
        s: table(s),
        filled: filled.to_vec(),
    }
}

fn id(raw: RawState) -> usize {
    census()
        .states
        .binary_search_by(|record| record.raw.cmp(&raw))
        .unwrap()
}

fn action_id(action: Source25Change) -> usize {
    census()
        .actions
        .iter()
        .position(|candidate| *candidate == action)
        .unwrap()
}

fn offer(state: usize, action: Source25Change) -> &'static Offer {
    &census().edges[state][action_id(action)]
}

fn remove(relation: SourceRelation, x: usize, y: usize) -> Source25Change {
    Source25Change::Remove { relation, x, y }
}

#[test]
fn full_carrier_alphabet_and_signed_sum_are_retained() {
    let c = census();
    assert_eq!(c.schema, "bounded-native-future/1");
    assert_eq!(
        c.profile,
        Profile {
            max_terms: 3,
            max_count: 4,
            horizon: 2
        }
    );
    assert_eq!(c.states.len(), 29_771);
    assert!(c.states.windows(2).all(|pair| pair[0].raw < pair[1].raw));
    let totals: Vec<_> = (0..=3)
        .map(|n| c.states.iter().filter(|s| s.raw.n == n).count())
        .collect();
    assert_eq!(totals, [1, 15, 495, 29_260]);
    assert_eq!(c.actions.len(), 42);
    assert_eq!(
        &c.actions[..3],
        &[
            Source25Change::Identify { x: 0, y: 1 },
            Source25Change::Identify { x: 0, y: 2 },
            Source25Change::Identify { x: 1, y: 2 },
        ]
    );
    assert_eq!(c.actions[3], remove(SourceRelation::R, 0, 0));
    assert_eq!(c.actions[11], remove(SourceRelation::R, 2, 2));
    assert_eq!(c.actions[12], remove(SourceRelation::S, 0, 0));
    assert_eq!(c.actions[20], remove(SourceRelation::S, 2, 2));
    assert_eq!(c.actions[21], Source25Change::Fill { x: 0, y: 1, z: 2 });
    assert_eq!(c.actions[22], Source25Change::Fill { x: 0, y: 2, z: 1 });
    assert_eq!(c.actions[23], Source25Change::AddTerm);
    assert_eq!(
        c.actions[24],
        Source25Change::AddAssertion {
            relation: SourceRelation::R,
            x: 0,
            y: 0
        }
    );
    assert_eq!(
        c.actions[41],
        Source25Change::AddAssertion {
            relation: SourceRelation::S,
            x: 2,
            y: 2
        }
    );
    assert_eq!(c.edges.len(), c.states.len());
    for (record, offers) in c.states.iter().zip(&c.edges) {
        assert_eq!(offers.len(), 42);
        let signed_raw: i64 = record.raw.r.iter().map(|&v| i64::from(v)).sum::<i64>()
            - record.raw.s.iter().map(|&v| i64::from(v)).sum::<i64>();
        let signed_mark = record
            .mark
            .normal
            .iter()
            .map(|s| s.parse::<BigInt>().unwrap())
            .sum::<BigInt>();
        assert_eq!(signed_mark, BigInt::from(signed_raw));
        assert_eq!(
            record
                .balance
                .iter()
                .map(|row| row.face)
                .collect::<Vec<_>>(),
            record.raw.filled
        );
        for (action, edge) in c.actions.iter().zip(offers) {
            match edge.status {
                OfferStatus::NativeDisabled => {
                    assert_eq!((edge.price, edge.child, edge.occurrences), (None, None, 0))
                }
                OfferStatus::BoundExcluded => {
                    let (a, b) = action.additions();
                    assert_eq!(
                        (edge.price, edge.child, edge.occurrences),
                        (Some([a, b]), None, 0)
                    );
                }
                OfferStatus::Admitted => {
                    let (a, b) = action.additions();
                    assert_eq!((edge.price, edge.occurrences), (Some([a, b]), 1));
                    assert!(edge.child.unwrap() < c.states.len());
                }
            }
        }
    }
}

#[test]
fn clipped_decoder_recovers_every_raw_state_and_refuses_invalid_reports() {
    for record in &census().states {
        assert_eq!(decode_clipped(&clipped_report(record)).unwrap(), record.raw);
    }
    let source = id(state(1, &[(0, 0, 3)], &[(0, 0, 1)], &[]));
    let report = clipped_report(&census().states[source]);
    assert_eq!(report.clipped_r, [2]);
    assert_eq!(report.clipped_s, [1]);
    let mut bad = report.clone();
    bad.mark.normal[0] = "9".into();
    assert!(decode_clipped(&bad).is_err());
    bad = report.clone();
    bad.mark.normal[0] = "+2".into();
    assert!(decode_clipped(&bad).is_err());
    bad = report.clone();
    bad.clipped_r[0] = 3;
    assert!(decode_clipped(&bad).is_err());
    bad = report.clone();
    bad.mark.n = 4;
    assert!(decode_clipped(&bad).is_err());
    bad = report.clone();
    bad.filled = vec![[0, 1, 2]];
    assert!(decode_clipped(&bad).is_err());
    bad = report.clone();
    bad.clipped_s.clear();
    assert!(decode_clipped(&bad).is_err());
    let both = id(state(1, &[(0, 0, 2)], &[(0, 0, 2)], &[]));
    assert_eq!(
        decode_clipped(&clipped_report(&census().states[both])).unwrap(),
        census().states[both].raw
    );
}

#[test]
fn every_layer_class_has_the_same_protected_steps_from_every_member() {
    let c = census();
    for (name, layers, terminal_probes) in [
        (
            "terminal_present_only",
            &c.partitions.terminal_present_only,
            false,
        ),
        (
            "terminal_status_probes",
            &c.partitions.terminal_status_probes,
            true,
        ),
    ] {
        assert_eq!(layers.len(), 3);
        let mut counts = Vec::new();
        for (h, layer) in layers.iter().enumerate() {
            assert_eq!(layer.len(), c.states.len());
            let mut representatives = BTreeMap::new();
            for (sid, &class) in layer.iter().enumerate() {
                let next_class = representatives.len();
                if let Some(&first) = representatives.get(&class) {
                    let first: usize = first;
                    assert_eq!(c.states[sid].mark, c.states[first].mark);
                    assert_eq!(c.states[sid].balance, c.states[first].balance);
                    if h > 0 || terminal_probes {
                        for (left, right) in c.edges[sid].iter().zip(&c.edges[first]) {
                            assert_eq!(left.status, right.status);
                            assert_eq!(left.price, right.price);
                            if h > 0 {
                                assert_eq!(left.occurrences, right.occurrences);
                                assert_eq!(
                                    left.child.map(|child| layers[h - 1][child]),
                                    right.child.map(|child| layers[h - 1][child])
                                );
                            }
                        }
                    }
                } else {
                    assert_eq!(class, next_class);
                    representatives.insert(class, sid);
                }
            }
            counts.push(representatives.len());
        }
        println!("{name} layer class counts: {counts:?}");
        assert_eq!(
            layers[2].iter().copied().collect::<BTreeSet<_>>().len(),
            c.states.len()
        );
    }
    assert_eq!(
        c.partitions.terminal_status_probes[1]
            .iter()
            .copied()
            .collect::<BTreeSet<_>>()
            .len(),
        c.states.len()
    );
}

#[test]
fn each_additional_report_field_has_a_deletion_collision() {
    let c = census();
    for relation in [SourceRelation::R, SourceRelation::S] {
        let (a, b) = match relation {
            SourceRelation::R => (
                state(2, &[(0, 1, 1)], &[], &[]),
                state(2, &[(1, 0, 1)], &[], &[]),
            ),
            SourceRelation::S => (
                state(2, &[], &[(0, 1, 1)], &[]),
                state(2, &[], &[(1, 0, 1)], &[]),
            ),
        };
        let (a, b) = (id(a), id(b));
        let (ra, rb) = (clipped_report(&c.states[a]), clipped_report(&c.states[b]));
        assert_eq!(ra.mark, rb.mark);
        assert_eq!(ra.filled, rb.filled);
        match relation {
            SourceRelation::R => assert_eq!(ra.clipped_s, rb.clipped_s),
            SourceRelation::S => assert_eq!(ra.clipped_r, rb.clipped_r),
        }
        assert_eq!(
            offer(a, remove(relation, 0, 1)).status,
            OfferStatus::Admitted
        );
        assert_eq!(
            offer(b, remove(relation, 0, 1)).status,
            OfferStatus::NativeDisabled
        );
    }
    let a = id(state(3, &[], &[], &[[0, 1, 2]]));
    let b = id(state(3, &[], &[], &[[0, 2, 1]]));
    let (ra, rb) = (clipped_report(&c.states[a]), clipped_report(&c.states[b]));
    assert_eq!(ra.mark, rb.mark);
    assert_eq!(ra.clipped_r, rb.clipped_r);
    assert_eq!(ra.clipped_s, rb.clipped_s);
    assert_ne!(ra.filled, rb.filled);
    assert_ne!(c.states[a].balance, c.states[b].balance);
    let fill = Source25Change::Fill { x: 0, y: 1, z: 2 };
    assert_eq!(offer(a, fill).status, OfferStatus::NativeDisabled);
    assert_eq!(offer(b, fill).status, OfferStatus::Admitted);
}

#[test]
fn the_one_step_collision_names_its_terminal_convention() {
    let c = census();
    let a = id(state(2, &[(0, 1, 1), (1, 0, 2)], &[], &[]));
    let b = id(state(2, &[(0, 1, 2), (1, 0, 1)], &[], &[]));
    assert_eq!(c.states[a].mark, c.states[b].mark);
    assert_eq!(c.states[a].balance, c.states[b].balance);
    let mut admitted = 0;
    for (left, right) in c.edges[a].iter().zip(&c.edges[b]) {
        assert_eq!(left.status, right.status);
        assert_eq!(left.price, right.price);
        assert_eq!(left.occurrences, right.occurrences);
        match (left.child, right.child) {
            (Some(x), Some(y)) => {
                admitted += 1;
                assert_eq!(c.states[x].mark, c.states[y].mark);
                assert_eq!(c.states[x].balance, c.states[y].balance);
            }
            (None, None) => {}
            _ => panic!("child presence differs"),
        }
    }
    assert_eq!(admitted, 12);
    assert_eq!(
        c.partitions.terminal_present_only[1][a],
        c.partitions.terminal_present_only[1][b]
    );
    assert_ne!(
        c.partitions.terminal_present_only[2][a],
        c.partitions.terminal_present_only[2][b]
    );
    assert_eq!(
        c.partitions.terminal_status_probes[0][a],
        c.partitions.terminal_status_probes[0][b]
    );
    assert_ne!(
        c.partitions.terminal_status_probes[1][a],
        c.partitions.terminal_status_probes[1][b]
    );
    let remove = remove(SourceRelation::R, 0, 1);
    let after_a = offer(a, remove).child.unwrap();
    let after_b = offer(b, remove).child.unwrap();
    assert_eq!(offer(after_a, remove).status, OfferStatus::NativeDisabled);
    assert_eq!(offer(after_b, remove).status, OfferStatus::Admitted);
}

#[test]
fn native_carrier_changes_keep_balance_counts_prices_and_occurrences() {
    let c = census();
    let a = id(state(2, &[], &[], &[]));
    let b = id(state(2, &[(0, 1, 1)], &[(1, 0, 1)], &[]));
    assert_eq!(c.states[a].mark, c.states[b].mark);
    let fill = Source25Change::Fill { x: 0, y: 1, z: 2 };
    for (start, balanced) in [(a, true), (b, false)] {
        let growth = offer(start, Source25Change::AddTerm);
        assert_eq!((growth.price, growth.occurrences), (Some([1, 0]), 1));
        let filling = offer(growth.child.unwrap(), fill);
        assert_eq!((filling.price, filling.occurrences), (Some([0, 0]), 1));
        assert_eq!(
            c.states[filling.child.unwrap()].balance,
            [BalanceRow {
                face: [0, 1, 2],
                balanced
            }]
        );
    }
    let a = id(state(3, &[(0, 1, 1)], &[], &[]));
    let b = id(state(3, &[(0, 2, 1)], &[], &[]));
    assert_eq!(c.states[a].mark, c.states[b].mark);
    let identify = Source25Change::Identify { x: 0, y: 1 };
    let first = offer(a, identify);
    let second = offer(b, identify);
    assert_eq!((first.price, first.occurrences), (Some([0, 0]), 1));
    assert_eq!(
        c.states[first.child.unwrap()].raw,
        state(2, &[(0, 0, 1)], &[], &[])
    );
    assert_eq!(
        c.states[second.child.unwrap()].raw,
        state(2, &[(0, 1, 1)], &[], &[])
    );
    assert_ne!(
        c.states[first.child.unwrap()].mark,
        c.states[second.child.unwrap()].mark
    );
    let both_faces = id(state(
        3,
        &[(0, 1, 1), (1, 0, 2)],
        &[(2, 2, 1)],
        &[[0, 1, 2], [0, 2, 1]],
    ));
    let identified = &c.states[offer(both_faces, identify).child.unwrap()].raw;
    assert_eq!(*identified, state(2, &[(0, 0, 3)], &[(1, 1, 1)], &[]));
}

#[test]
fn excluded_enabled_offers_are_distinct_from_disabled_offers_and_zero_price_edits() {
    let empty = id(state(0, &[], &[], &[]));
    let growth = offer(empty, Source25Change::AddTerm);
    assert_eq!(growth.status, OfferStatus::Admitted);
    assert_eq!(
        census().states[growth.child.unwrap()].raw,
        state(1, &[], &[], &[])
    );
    assert_eq!(
        census().edges[empty]
            .iter()
            .filter(|edge| edge.status == OfferStatus::Admitted)
            .count(),
        1
    );
    let full_terms = id(state(3, &[], &[], &[]));
    assert_eq!(
        *offer(full_terms, Source25Change::AddTerm),
        Offer {
            status: OfferStatus::BoundExcluded,
            price: Some([1, 0]),
            child: None,
            occurrences: 0
        }
    );
    let full_count = id(state(1, &[(0, 0, 2)], &[(0, 0, 2)], &[]));
    let add = Source25Change::AddAssertion {
        relation: SourceRelation::R,
        x: 0,
        y: 0,
    };
    assert_eq!(
        *offer(full_count, add),
        Offer {
            status: OfferStatus::BoundExcluded,
            price: Some([0, 1]),
            child: None,
            occurrences: 0
        }
    );
    let invalid = Source25Change::AddAssertion {
        relation: SourceRelation::R,
        x: 2,
        y: 2,
    };
    assert_eq!(
        *offer(full_count, invalid),
        Offer {
            status: OfferStatus::NativeDisabled,
            price: None,
            child: None,
            occurrences: 0
        }
    );
    let one = id(state(1, &[(0, 0, 1)], &[], &[]));
    let removal = offer(one, remove(SourceRelation::R, 0, 0));
    assert_eq!(
        (removal.status, removal.price, removal.occurrences),
        (OfferStatus::Admitted, Some([0, 0]), 1)
    );
    assert_eq!(
        census().states[removal.child.unwrap()].raw,
        state(1, &[], &[], &[])
    );
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_future_compression.rs
// Claim: urn:core:crates_rs:tests:test-genesis-future-compression:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1f89a18b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1f89a18b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1f89a18b {
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
impl BoundaryError1f89a18b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1f89a18b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1f89a18b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1f89a18b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1f89a18b> {
        if capacity_bound == 0 {
            return Err(BoundaryError1f89a18b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1f89a18b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1f89a18b::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_1f89a18b() {
    let admitted = BoundaryRecord1f89a18b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1f89a18b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
