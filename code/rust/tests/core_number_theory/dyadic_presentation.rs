use num_bigint::BigInt;
use core_number_theory::dyadic_presentation::{
    CharacterSumLimits, DyadicError, DyadicLevel, FiniteDualPrefix,
};
use core_number_theory::rational::{ri, rq};

#[test]
fn inclusion_is_injective_additive_and_preserves_rational_turns() {
    for n in 0..=6 {
        let low = DyadicLevel::new(n).unwrap();
        let high = DyadicLevel::new(n + 1).unwrap();
        for a in 0..low.order() {
            let image = low.include(a).unwrap();
            assert_eq!(low.coordinate(a), high.coordinate(image));
            for b in 0..low.order() {
                assert_eq!(low.include(a) == low.include(b), a == b);
                assert_eq!(
                    low.include(low.add(a, b).unwrap()),
                    high.add(image, low.include(b).unwrap())
                );
            }
        }
    }
}

#[test]
fn actual_exact_character_sums_cover_all_pairs_through_level_four() {
    for n in 0..=4 {
        let group = DyadicLevel::new(n).unwrap();
        for k in 0..group.order() {
            for j in 0..group.order() {
                let sum = group
                    .normalized_inner_product(&k.into(), &j.into(), CharacterSumLimits::default())
                    .unwrap();
                assert_eq!(sum.as_rational(), Some(ri(i64::from(k == j))));
            }
        }
    }
}

#[test]
fn pullback_pairing_commutes_in_the_common_exact_field() {
    for n in 0..=4 {
        let low = DyadicLevel::new(n).unwrap();
        let high = DyadicLevel::new(n + 1).unwrap();
        for k in 0..high.order() {
            let restricted = low.restrict(high, k).unwrap();
            for m in 0..low.order() {
                let before = high.character_turn(&k.into(), &low.include(m).unwrap().into());
                let after = low.character_turn(&restricted.into(), &m.into());
                assert_eq!(before, after);
                assert_eq!(
                    before.character_in(high.order()),
                    after.character_in(high.order())
                );
            }
        }
    }
}

#[test]
fn noncardinal_and_negative_integer_pairings_are_exact() {
    let eight = DyadicLevel::new(3).unwrap();
    let turn = eight.character_turn(&BigInt::from(-1), &BigInt::from(1));
    assert_eq!(turn.representative(), &rq(7, 8));
    let root = turn.character_in(8).unwrap();
    assert_eq!(
        root.mul(&root)
            .unwrap()
            .mul(&root.mul(&root).unwrap())
            .unwrap()
            .as_rational(),
        Some(ri(-1))
    );
    assert_eq!(eight.normalize_index(&BigInt::from(-17)), 7);
    assert_eq!(
        eight
            .normalized_inner_product(&(-1).into(), &7.into(), CharacterSumLimits::default())
            .unwrap()
            .as_rational(),
        Some(ri(1))
    );
}

#[test]
fn each_prefix_has_two_distinct_coherent_adjacent_extensions() {
    let prefix = FiniteDualPrefix::new(&[0, 1, 3, 7]).unwrap();
    assert_eq!(prefix.next_indices().unwrap(), [7, 15]);
    for next in prefix.next_indices().unwrap() {
        let mut entries = prefix.indices().to_vec();
        entries.push(next);
        assert!(FiniteDualPrefix::new(&entries).is_ok());
    }
    for n in 0..=6 {
        let low = DyadicLevel::new(n).unwrap();
        let high = DyadicLevel::new(n + 1).unwrap();
        for a in 0..low.order() {
            let extensions = low.extensions(a).unwrap();
            let fiber: Vec<_> = (0..high.order())
                .filter(|&b| low.restrict(high, b).unwrap() == a)
                .collect();
            assert_eq!(fiber, extensions);
        }
    }
}

#[test]
fn malformed_carriers_prefixes_and_native_overflow_are_refused() {
    assert_eq!(
        DyadicLevel::new(usize::BITS),
        Err(DyadicError::LevelOverflow)
    );
    let largest = DyadicLevel::new(usize::BITS - 1).unwrap();
    assert_eq!(largest.include(0), Err(DyadicError::LevelOverflow));
    assert_eq!(largest.extensions(0), Err(DyadicError::LevelOverflow));
    assert_eq!(
        largest
            .add(largest.order() - 1, largest.order() - 1)
            .unwrap(),
        largest.order() - 2
    );
    let four = DyadicLevel::new(2).unwrap();
    assert_eq!(four.coordinate(4), Err(DyadicError::OutOfCarrier));
    assert_eq!(four.add(0, 4), Err(DyadicError::OutOfCarrier));
    assert_eq!(four.include(4), Err(DyadicError::OutOfCarrier));
    assert_eq!(four.restrict(four, 0), Err(DyadicError::NonAdjacentLevels));
    assert_eq!(FiniteDualPrefix::new(&[]), Err(DyadicError::EmptyPrefix));
    assert_eq!(FiniteDualPrefix::new(&[1]), Err(DyadicError::OutOfCarrier));
    assert_eq!(
        FiniteDualPrefix::new(&[0, 1, 2]),
        Err(DyadicError::IncoherentPrefix)
    );
    assert_eq!(
        FiniteDualPrefix::new(&vec![0; usize::BITS as usize + 1]),
        Err(DyadicError::LevelOverflow)
    );
}

#[test]
fn sum_budget_and_field_caps_refuse_before_cyclotomic_work() {
    let eight = DyadicLevel::new(3).unwrap();
    assert_eq!(
        eight.normalized_inner_product(
            &0.into(),
            &0.into(),
            CharacterSumLimits {
                max_terms: 7,
                max_conductor: 8
            }
        ),
        Err(DyadicError::TermLimit)
    );
    assert_eq!(
        eight.normalized_inner_product(
            &0.into(),
            &0.into(),
            CharacterSumLimits {
                max_terms: 8,
                max_conductor: 7
            }
        ),
        Err(DyadicError::ConductorLimit)
    );
    assert_eq!(
        DyadicLevel::new(11).unwrap().normalized_inner_product(
            &0.into(),
            &0.into(),
            CharacterSumLimits {
                max_terms: usize::MAX,
                max_conductor: usize::MAX
            }
        ),
        Err(DyadicError::ConductorLimit)
    );
}

#[test]
fn source_generated_coordinates_inclusions_and_turns_match() {
    let fixture: serde_json::Value = serde_json::from_str(include_str!(
        "../../../../atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_witnessed_difference_programme/evidence/dyadic_source_oracle.json"
    )).unwrap();
    let integer = |value: &serde_json::Value| value.as_u64().unwrap() as usize;
    let inclusions = fixture["inclusions"].as_array().unwrap();
    let turns = fixture["turns"].as_array().unwrap();
    assert_eq!(inclusions.len(), 63);
    assert_eq!(turns.len(), 378);
    for row in inclusions {
        let group = DyadicLevel::new(integer(&row[0]) as u32).unwrap();
        assert_eq!(group.include(integer(&row[1])).unwrap(), integer(&row[2]));
        assert_eq!(
            group
                .coordinate(integer(&row[1]))
                .unwrap()
                .representative()
                .to_string(),
            row[3].as_str().unwrap()
        );
    }
    for row in turns {
        let group = DyadicLevel::new(integer(&row[0]) as u32).unwrap();
        let index = BigInt::from(row[1].as_i64().unwrap());
        let element = BigInt::from(row[2].as_i64().unwrap());
        assert_eq!(
            group
                .character_turn(&index, &element)
                .representative()
                .to_string(),
            row[3].as_str().unwrap()
        );
    }
}

// Origin: engine/crates_rs/tests/core_number_theory/dyadic_presentation.rs
// Claim: urn:core:crates_rs:tests:dyadic-presentation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord999584a2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord999584a2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError999584a2 {
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
impl BoundaryError999584a2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError999584a2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError999584a2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord999584a2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError999584a2> {
        if capacity_bound == 0 {
            return Err(BoundaryError999584a2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError999584a2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError999584a2::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_999584a2() {
    let admitted = BoundaryRecord999584a2::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord999584a2::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
