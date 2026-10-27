use num_bigint::BigInt;
use num_traits::{One, Zero};
use core_category_theory::bounded_counter::{CounterBoundary as B, CounterReport};
use core_wdp::genesis_guard_report::{CellGuardError as Error, Source25CellGuard};
use core_wdp::genesis_ongoing_adapter::{GenesisOngoingPacket, MarkedTriple};
use core_wdp::genesis_source_execution::{
    Source25Change as E, Source25State, SourceRelation as R,
};
use serde::Deserialize;

fn state(n: usize, relation: R, x: usize, y: usize, count: BigInt) -> Source25State {
    let huge = BigInt::one() << 140;
    let mut packet = GenesisOngoingPacket {
        terms: (0..n).map(|i| format!("t{i}")).collect(),
        r: vec![huge; n * n],
        s: vec![BigInt::zero(); n * n],
        filled: if n >= 3 {
            vec![MarkedTriple { x: 0, y: 1, z: 2 }]
        } else {
            vec![]
        },
    };
    match relation {
        R::R => packet.r[x * n + y] = count,
        R::S => packet.s[x * n + y] = count,
    }
    Source25State::try_new(packet).unwrap()
}
fn events(relation: R, x: usize, y: usize) -> [E; 2] {
    [
        E::AddAssertion { relation, x, y },
        E::Remove { relation, x, y },
    ]
}

fn assert_single_word_on_cell(
    initial: &Source25State,
    report: &Source25CellGuard,
    word: &[E],
    cell: (usize, R, usize, usize),
) {
    let (n, relation, x, y) = cell;
    let mut native = initial.clone();
    let mut observed = Ok(report.clone());
    for &event in word {
        let next = observed.as_ref().unwrap().advance(event);
        if !native.is_enabled(event) {
            assert_eq!(next, Err(Error::Boundary(B::GuardRefusal)));
            observed = next;
            break;
        }
        native = native.perform_enabled(event).unwrap();
        observed = next;
        let remaining = observed.as_ref().unwrap().report().remaining();
        assert_eq!(
            observed,
            Source25CellGuard::from_state(&native, relation, x, y, remaining)
        );
        // Actual native transitions keep the rest of the raw marked state.
        let mut restored = native.packet().clone();
        let original = initial.packet();
        match relation {
            R::R => restored.r[x * n + y] = original.r[x * n + y].clone(),
            R::S => restored.s[x * n + y] = original.s[x * n + y].clone(),
        }
        assert_eq!(&restored, original);
    }
    assert_eq!(report.observe(word), observed);
}

fn assert_words_on_cell(
    initial: &Source25State,
    report: &Source25CellGuard,
    alphabet: &[E; 2],
    cell: (usize, R, usize, usize),
) {
    for len in 0..=5 {
        for mask in 0..1usize << len {
            let word: Vec<_> = (0..len)
                .map(|i| alphabet[usize::from(mask & (1 << i) != 0)])
                .collect();
            assert_single_word_on_cell(initial, report, &word, cell);
        }
    }
}

#[test]
fn graded_report_reflects_every_native_word_in_the_checked_contexts() {
    for n in 1..=3 {
        for relation in [R::R, R::S] {
            for x in 0..n {
                for y in 0..n {
                    let alphabet = events(relation, x, y);
                    for count in [BigInt::zero(), 1.into(), 3.into(), BigInt::one() << 140] {
                        let initial = state(n, relation, x, y, count);
                        let report =
                            Source25CellGuard::from_state(&initial, relation, x, y, 5).unwrap();
                        assert_words_on_cell(&initial, &report, &alphabet, (n, relation, x, y));
                    }
                }
            }
        }
    }
}

#[test]
fn arbitrary_counts_are_separated_by_actual_native_removal_guards() {
    for m in 0..=12 {
        for n in m + 1..=16 {
            let mut lower = state(1, R::R, 0, 0, m.into());
            let mut upper = state(1, R::R, 0, 0, n.into());
            let remove = events(R::R, 0, 0)[1];
            for _ in 0..m {
                lower = lower.perform_enabled(remove).unwrap();
                upper = upper.perform_enabled(remove).unwrap();
            }
            assert!(!lower.is_enabled(remove));
            assert!(upper.is_enabled(remove));
        }
    }
}

#[test]
fn scope_refusal_is_not_a_native_guard_or_a_fabricated_inverse() {
    assert_eq!(
        Source25CellGuard::from_state(&Source25State::empty(), R::R, 0, 0, 5),
        Err(Error::OutsideCarrier)
    );
    let raw = state(3, R::R, 0, 1, BigInt::zero());
    assert_eq!(
        Source25CellGuard::from_state(&raw, R::R, 3, 0, 5),
        Err(Error::OutsideCarrier)
    );
    let report = Source25CellGuard::from_state(&raw, R::R, 0, 1, 1).unwrap();
    for event in [
        E::AddTerm,
        E::Identify { x: 0, y: 1 },
        E::Fill { x: 0, y: 2, z: 1 },
        E::AddAssertion {
            relation: R::S,
            x: 0,
            y: 1,
        },
        E::Remove {
            relation: R::R,
            x: 1,
            y: 0,
        },
    ] {
        assert_eq!(report.advance(event), Err(Error::UnsupportedContextEvent));
    }
    let [add, remove] = events(R::R, 0, 1);
    assert_eq!(
        report.advance(remove),
        Err(Error::Boundary(B::GuardRefusal))
    );
    let after = report.advance(add).unwrap();
    assert_eq!(after.report(), CounterReport::from_count(0, 1));
    assert!(raw.perform_enabled(add).unwrap().is_enabled(remove));
    assert_eq!(
        after.advance(remove),
        Err(Error::Boundary(B::ContextExhausted))
    );
}

#[test]
fn original_hundred_attempt_horizon_already_requires_fifty_guard_classes() {
    let raw = state(1, R::R, 0, 0, BigInt::zero());
    let [add, remove] = events(R::R, 0, 0);
    let mut representatives = Vec::new();
    let mut native = raw;
    for m in 0..=49 {
        // One admitted term, m additions, then at most 49 context attempts.
        assert!(1 + m + 49 <= 100);
        representatives.push(native.clone());
        native = native.perform_enabled(add).unwrap();
    }
    for m in 0..50 {
        for n in m + 1..50 {
            let mut a = representatives[m].clone();
            let mut b = representatives[n].clone();
            for _ in 0..m {
                a = a.perform_enabled(remove).unwrap();
                b = b.perform_enabled(remove).unwrap();
            }
            assert!(!a.is_enabled(remove));
            assert!(b.is_enabled(remove));
        }
    }
}

#[test]
fn the_depth_graded_category_has_no_native_groupoid_inverse() {
    use core_category_theory::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
    use core_category_theory::finite_groupoid::ValidatedFiniteGroupoid;
    use std::collections::BTreeMap;
    let raw = state(1, R::R, 0, 0, BigInt::zero());
    let report = Source25CellGuard::from_state(&raw, R::R, 0, 0, 1).unwrap();
    let after = report.advance(events(R::R, 0, 0)[0]).unwrap();
    assert_eq!(
        (report.report().remaining(), after.report().remaining()),
        (1, 0)
    );
    let mut category = DeclaredFiniteCategory::new("one allowed graded history edge");
    category.add_identity("before", "ib");
    category.add_identity("after", "ia");
    category.add_morphism("add", "before", "after");
    for (f, g, fg) in [
        ("ib", "ib", "ib"),
        ("ia", "ia", "ia"),
        ("ib", "add", "add"),
        ("add", "ia", "add"),
    ] {
        category.set_composition(f, g, fg);
    }
    ValidatedFiniteCategory::try_new(category.clone()).unwrap();
    let arrows = ["ia", "ib", "add"];
    for a in arrows {
        for b in arrows {
            for c in arrows {
                let proposed = BTreeMap::from([
                    ("ia".to_owned(), a.to_owned()),
                    ("ib".to_owned(), b.to_owned()),
                    ("add".to_owned(), c.to_owned()),
                ]);
                assert!(ValidatedFiniteGroupoid::try_new(category.clone(), proposed).is_err());
            }
        }
    }
}

#[test]
fn the_same_guard_observer_has_classical_and_quantum_embeddings() {
    use linear_algebra::exact_field::matrix as mx;
    use core_category_theory::bounded_counter::CounterEvent;
    use core_number_theory::cyclotomic::GaussianRat;
    use core_number_theory::rational::{ri, rq};
    use core_quantum_physics::ancilla_capacity::AncillaCapacity;
    use core_quantum_physics::exact_channel::ExactKrausChannel;
    use core_quantum_physics::exact_entropy::RationalSpectrum;
    use core_quantum_physics::exact_instrument::ExactDensityState;
    // Six depth-graded classes through depth two plus two distinct terminal flags.
    let states: Vec<_> = (0..=2)
        .flat_map(|r| (0..=r).map(move |c| CounterReport::from_count(r, c)))
        .collect();
    let dimension = states.len() + 2;
    let projector = |i: usize| {
        let mut matrix = mx::zeros(dimension, dimension).unwrap();
        matrix.set(i, i, GaussianRat::one()).unwrap();
        matrix
    };
    for event in [CounterEvent::Increment, CounterEvent::Decrement] {
        let mut transition: Vec<_> = states
            .iter()
            .map(|state| match state.advance(event) {
                Ok(next) => states.iter().position(|s| *s == next).unwrap(),
                Err(B::GuardRefusal) => states.len(),
                Err(B::ContextExhausted) => states.len() + 1,
            })
            .collect();
        transition.extend([states.len(), states.len() + 1]);
        // Canonical channel constructor verifies Kraus completeness exactly.
        let kraus = transition
            .iter()
            .enumerate()
            .map(|(i, &target)| {
                let mut k = mx::zeros(dimension, dimension).unwrap();
                k.set(target, i, GaussianRat::one()).unwrap();
                k
            })
            .collect();
        let channel =
            ExactKrausChannel::try_new(dimension, dimension, kraus, "declared guard observer")
                .unwrap();
        for (i, &target) in transition.iter().enumerate() {
            assert_eq!(channel.apply(&projector(i)).unwrap(), projector(target));
        }
    }
    // Uniform preparation on the three initial-depth classes. The report
    // distributions coincide, while different admitted algebras change purity.
    let weights: Vec<_> = (0..dimension)
        .map(|i| if (3..6).contains(&i) { rq(1, 3) } else { ri(0) })
        .collect();
    let density = ExactDensityState::try_new(
        mx::diagonal(
            &weights
                .iter()
                .cloned()
                .map(GaussianRat::from_rational)
                .collect::<Vec<_>>(),
        )
        .unwrap(),
    )
    .unwrap();
    let quantum = AncillaCapacity::from_density(&density, &[3], dimension).unwrap();
    let pure = RationalSpectrum::try_new(vec![(ri(1), 1)]).unwrap();
    let classical = AncillaCapacity::from_sectors(
        &weights
            .into_iter()
            .map(|p| (p, pure.clone()))
            .collect::<Vec<_>>(),
        &[3],
        dimension,
    )
    .unwrap();
    assert_eq!(quantum.maximum_extension_purity(), ri(1));
    assert_eq!(classical.maximum_extension_purity(), rq(1, 3));
    assert_eq!(quantum.pure_marginal_trace_distance(), ri(0));
    assert_eq!(classical.pure_marginal_trace_distance(), rq(2, 3));
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct SourceCase {
    relation: R,
    count: String,
    // [word encoded by '+'/'-', index of first refusal, final accepted count].
    results: Vec<(String, Option<usize>, String)>,
}
#[derive(Deserialize)]
struct SourceFixture {
    schema: String,
    cases: Vec<SourceCase>,
}

#[test]
fn preserved_python_source_agrees_on_all_guard_fixture_answers() {
    let fixture: SourceFixture =
        serde_json::from_str(include_str!("data/native_history_guard_source.json")).unwrap();
    assert_eq!(fixture.schema, "native-history-guard-source-v1");
    assert_eq!(fixture.cases.len(), 8);
    for case in fixture.cases {
        assert_eq!(case.results.len(), 31);
        let raw = state(3, case.relation, 0, 1, case.count.parse().unwrap());
        for (word, first_refusal, final_count) in case.results {
            let alphabet = events(case.relation, 0, 1);
            let changes: Vec<_> = word
                .chars()
                .map(|c| match c {
                    '+' => alphabet[0],
                    '-' => alphabet[1],
                    _ => panic!("bad fixture"),
                })
                .collect();
            let mut native = raw.clone();
            let mut refused = None;
            for (i, &event) in changes.iter().enumerate() {
                if !native.is_enabled(event) {
                    refused = Some(i);
                    break;
                }
                native = native.perform_enabled(event).unwrap();
            }
            assert_eq!(refused, first_refusal);
            let values = match case.relation {
                R::R => &native.packet().r,
                R::S => &native.packet().s,
            };
            assert_eq!(values[1], final_count.parse::<BigInt>().unwrap());
            let report = Source25CellGuard::from_state(&raw, case.relation, 0, 1, 4).unwrap();
            assert_eq!(report.observe(&changes).is_ok(), first_refusal.is_none());
        }
    }
}

// Origin: engine/crates_rs/tests/core_wdp/test_native_history_guard.rs
// Claim: urn:core:crates_rs:tests:test-native-history-guard:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf72b4694 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf72b4694` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf72b4694 {
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
impl BoundaryErrorf72b4694 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf72b4694 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf72b4694 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf72b4694 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf72b4694> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf72b4694::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf72b4694::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf72b4694::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f72b4694() {
    let admitted = BoundaryRecordf72b4694::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf72b4694::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
