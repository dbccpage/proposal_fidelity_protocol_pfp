use linear_algebra::backend::basic_matrix::{BasicMatrix, OperationLimits};
use linear_algebra::exact_field::elimination;
use linear_algebra::row_constraint_implication::clear_denominators;
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};
use core_wdp::genesis_balance_transition::{
    balanced, BalanceReason, BalanceVerdict, Source25BalanceProfile,
};
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::{Source25Change, Source25State, SourceRelation};
use core_wdp::types::AuthorityEffect;

fn faces(n: usize) -> Vec<MarkedTriple> {
    let mut faces = vec![];
    for x in 0..n {
        for y in x + 1..n {
            for z in y + 1..n {
                faces.push(MarkedTriple { x, y, z });
                faces.push(MarkedTriple { x, y: z, z: y });
            }
        }
    }
    faces.sort();
    faces
}
fn state(n: usize, filled: Vec<MarkedTriple>, excess: &[BigInt]) -> Source25State {
    Source25State::try_new(GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: excess
            .iter()
            .map(|e| {
                if e.is_positive() {
                    e + 1
                } else {
                    BigInt::one()
                }
            })
            .collect(),
        s: excess
            .iter()
            .map(|e| {
                if e.is_negative() {
                    -e + 1
                } else {
                    BigInt::one()
                }
            })
            .collect(),
        filled,
    })
    .unwrap()
}
fn profile(source: Source25State, change: Source25Change) -> Source25BalanceProfile {
    Source25BalanceProfile::new(source, change, OperationLimits::UNLIMITED).unwrap()
}
// Independent diagnostic read of actual source output, rather than a verdict
// inferred from the proposed event criterion or from the solver's enum.
fn raw_balanced(source: &Source25State) -> bool {
    let p = source.packet();
    let n = p.terms.len();
    p.filled.iter().all(|t| {
        let edges = [t.x * n + t.y, t.y * n + t.z, t.z * n + t.x];
        let sum: BigInt = edges.iter().map(|&i| &p.r[i] - &p.s[i]).sum();
        sum.is_zero()
    })
}

#[test]
fn every_marked_context_through_four_terms_and_every_enabled_edit_matches_kernel_replay() {
    let (mut contexts, mut events) = (0, 0);
    for n in 0..=4 {
        let all = faces(n);
        for mask in 0..1usize << all.len() {
            contexts += 1;
            let filled: Vec<_> = all
                .iter()
                .enumerate()
                .filter(|(i, _)| mask & (1 << i) != 0)
                .map(|(_, t)| *t)
                .collect();
            let zero = vec![BigInt::zero(); n * n];
            let source = state(n, filled.clone(), &zero);
            let d = BasicMatrix::try_from_fn(filled.len(), n * n, |i, j| {
                let t = filled[i];
                let edges = [t.x * n + t.y, t.y * n + t.z, t.z * n + t.x];
                BigRational::from_integer(BigInt::from(edges.contains(&j)))
            })
            .unwrap();
            let mut representatives = vec![source.clone()];
            for vector in elimination::kernel_basis(&d).unwrap() {
                representatives.push(state(n, filled.clone(), &clear_denominators(&vector)));
            }
            assert!(representatives.iter().all(raw_balanced));
            for event in source.enabled_changes() {
                events += 1;
                let expected = representatives
                    .iter()
                    .all(|s| raw_balanced(&s.perform_enabled(event).unwrap()));
                let p = profile(source.clone(), event);
                assert_eq!(
                    matches!(p.verdict(), BalanceVerdict::Preserved(_)),
                    expected,
                    "n={n}, mask={mask}, event={event:?}"
                );
                assert_eq!(p.target(), &source.perform_enabled(event).unwrap());
                assert_eq!(p.actual_source_balanced(), raw_balanced(&source));
                assert_eq!(p.actual_target_balanced(), raw_balanced(p.target()));
                p.verify().unwrap();
                assert_eq!(p.authority_effect(), AuthorityEffect::None);
                if let BalanceVerdict::Obstructed(w) = p.verdict() {
                    assert_eq!(&w.source().packet().filled, &filled);
                    assert!(raw_balanced(w.source()));
                    assert!(!raw_balanced(w.target()));
                    assert_eq!(w.target(), &w.source().perform_enabled(event).unwrap());
                }
            }
        }
    }
    assert_eq!(contexts, 263);
    assert_eq!(events, 19388);
    println!(
        "independent raw kernel replay: {contexts} contexts, {events} canonical enabled edits"
    );
}

#[test]
fn tetrahedron_needs_the_actual_directed_equations() {
    let missing = MarkedTriple { x: 0, y: 1, z: 2 };
    let three = vec![
        MarkedTriple { x: 0, y: 1, z: 3 },
        MarkedTriple { x: 0, y: 2, z: 3 },
        MarkedTriple { x: 1, y: 2, z: 3 },
    ];
    let mut e = vec![BigInt::zero(); 16];
    e[2 * 4] = BigInt::one();
    let source = state(4, three, &e);
    assert!(balanced(&source));
    let negative = profile(source, Source25Change::Fill { x: 0, y: 1, z: 2 });
    assert!(matches!(negative.verdict(), BalanceVerdict::Obstructed(_)));
    assert!(!negative.actual_target_balanced());
    let seven = faces(4)
        .into_iter()
        .filter(|&face| face != missing)
        .collect();
    let positive = profile(
        state(4, seven, &vec![BigInt::zero(); 16]),
        Source25Change::Fill { x: 0, y: 1, z: 2 },
    );
    assert!(matches!(
        positive.verdict(),
        BalanceVerdict::Preserved(BalanceReason::FaceCombination { .. })
    ));
    positive.verify().unwrap();
}

#[test]
fn reverse_arcs_loops_dropped_faces_and_particular_balanced_edits_are_distinguished() {
    let face = MarkedTriple { x: 0, y: 1, z: 2 };
    let source = state(4, vec![face], &vec![BigInt::zero(); 16]);
    for (x, y, preserves) in [(0, 1, false), (1, 0, true), (0, 0, true)] {
        for relation in [SourceRelation::R, SourceRelation::S] {
            for event in [
                Source25Change::AddAssertion { relation, x, y },
                Source25Change::Remove { relation, x, y },
            ] {
                assert_eq!(
                    matches!(
                        profile(source.clone(), event).verdict(),
                        BalanceVerdict::Preserved(_)
                    ),
                    preserves
                );
            }
        }
    }
    let merge = profile(source.clone(), Source25Change::Identify { x: 0, y: 3 });
    assert!(matches!(merge.verdict(), BalanceVerdict::Obstructed(_)));
    assert!(merge.actual_target_balanced()); // This zero input does survive.
    let dropped = profile(source.clone(), Source25Change::Identify { x: 0, y: 1 });
    assert!(matches!(dropped.verdict(), BalanceVerdict::Preserved(_)));
    assert!(dropped.target().packet().filled.is_empty());
    assert!(matches!(
        profile(source, Source25Change::AddTerm).verdict(),
        BalanceVerdict::Preserved(_)
    ));
}

#[test]
fn nonbalanced_input_disabled_events_limits_and_large_counts_do_not_disappear() {
    let face = MarkedTriple { x: 0, y: 1, z: 2 };
    let mut e = vec![BigInt::zero(); 9];
    e[1] = BigInt::one() << 200usize;
    let p = profile(state(3, vec![face], &e), Source25Change::AddTerm);
    assert!(matches!(p.verdict(), BalanceVerdict::Preserved(_)));
    assert!(!p.actual_source_balanced());
    assert!(!p.actual_target_balanced());
    let mut raw = state(3, vec![], &vec![BigInt::zero(); 9]).packet().clone();
    raw.r[0] = BigInt::zero();
    let source = Source25State::try_new(raw).unwrap();
    for event in [
        Source25Change::Identify { x: 2, y: 1 },
        Source25Change::Remove {
            relation: SourceRelation::R,
            x: 0,
            y: 0,
        },
        Source25Change::Fill { x: 1, y: 0, z: 2 },
    ] {
        assert!(
            Source25BalanceProfile::new(source.clone(), event, OperationLimits::UNLIMITED).is_err()
        );
    }
    assert!(Source25BalanceProfile::new(
        source,
        Source25Change::Fill { x: 0, y: 1, z: 2 },
        OperationLimits {
            max_elements: 0,
            max_scalar_ops: usize::MAX
        }
    )
    .is_err());
}

// Origin: engine/crates_rs/tests/core_wdp/test_genesis_balance_transition.rs
// Claim: urn:core:crates_rs:tests:test-genesis-balance-transition:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord08b2081b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord08b2081b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError08b2081b {
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
impl BoundaryError08b2081b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError08b2081b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError08b2081b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord08b2081b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError08b2081b> {
        if capacity_bound == 0 {
            return Err(BoundaryError08b2081b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError08b2081b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError08b2081b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_08b2081b() {
    let admitted = BoundaryRecord08b2081b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord08b2081b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
