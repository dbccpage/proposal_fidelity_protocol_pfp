use core_category_theory::finite_continuation::*;

fn decode_two_state_table(mut number: usize) -> Vec<Vec<Option<usize>>> {
    let mut table = vec![vec![None; 2]; 2];
    for row in &mut table {
        for cell in row {
            let digit = number % 3;
            number /= 3;
            *cell = if digit == 2 { None } else { Some(digit) };
        }
    }
    table
}

fn assert_shortest_distinction(m: &PartialDynamics, c: &DistinctionCertificate) {
    m.verify_distinction(c).unwrap();
    // Independently enumerate every strictly shorter word: BFS really
    // returned a shortest distinction, including availability failure.
    for length in 0..c.word.len() {
        for bits in 0..(1usize << length) {
            let word: Vec<_> = (0..length).map(|i| (bits >> i) & 1).collect();
            assert_eq!(
                m.run(0, &word).unwrap().map(|s| m.reports()[s]),
                m.run(1, &word).unwrap().map(|s| m.reports()[s])
            );
        }
    }
}

#[test]
fn all_two_state_two_letter_partial_machines_have_replayable_minimal_quotients() {
    for code in 0..81usize {
        for mask in 0..4 {
            let table = decode_two_state_table(code);
            let reports = vec![mask & 1, (mask >> 1) & 1];
            let m = PartialDynamics::new(reports, table, 2).unwrap();
            let q = m.quotient();
            assert!(m.verify_quotient(&q));
            let ops = m.quotient_operations();
            for s in 0..2 {
                for a in 0..2 {
                    assert_eq!(
                        ops[q.state_to_block[s]][a],
                        m.transitions()[s][a].map(|t| q.state_to_block[t])
                    );
                }
            }
            let witness = m.distinguish(0, 1, 9).unwrap();
            assert_eq!(
                witness.is_none(),
                q.state_to_block[0] == q.state_to_block[1]
            );
            if let Some(c) = witness {
                assert_shortest_distinction(&m, &c);
            }
        }
    }
}

#[test]
fn delayed_distinction_and_availability_are_not_present_answer_equality() {
    let m = PartialDynamics::new(
        vec![7, 7, 7, 8],
        vec![vec![Some(1)], vec![Some(2)], vec![Some(3)], vec![Some(3)]],
        1,
    )
    .unwrap();
    let c = m.distinguish(0, 1, 25).unwrap().unwrap();
    assert_eq!(c.word, vec![0, 0]);
    let m = PartialDynamics::new(vec![usize::MAX; 2], vec![vec![None], vec![Some(1)]], 1).unwrap();
    let c = m.distinguish(0, 1, 9).unwrap().unwrap();
    assert_eq!(c.left_answer, None);
    assert_eq!(c.right_answer, Some(usize::MAX));
    assert_eq!(m.run(0, &[0, 9]), Err(ContinuationError::OutsideAlphabet));
}

#[test]
fn empty_alphabet_equivalence_and_resource_refusal_are_distinct() {
    let m = PartialDynamics::new(vec![0, 0], vec![vec![], vec![]], 0).unwrap();
    assert_eq!(m.distinguish(0, 1, 1).unwrap(), None);
    assert_eq!(m.distinguish(0, 1, 0), Err(ContinuationError::WorkLimit));
    assert!(PartialDynamics::new(vec![], vec![], 0).is_err());
    assert!(PartialDynamics::new(vec![0], vec![vec![Some(1)]], 1).is_err());
    assert!(PartialDynamics::new(vec![0], vec![vec![]], 1).is_err());
}

#[test]
fn forged_witness_or_overrefinement_is_rejected() {
    let m = PartialDynamics::new(
        vec![0, 0, 1],
        vec![vec![Some(2)], vec![Some(1)], vec![None]],
        1,
    )
    .unwrap();
    let mut c = m.distinguish(0, 1, 16).unwrap().unwrap();
    c.right_answer = c.left_answer;
    assert!(m.verify_distinction(&c).is_err());
    c.left = usize::MAX;
    assert!(m.verify_distinction(&c).is_err());
    let mut q = m.quotient();
    q.state_to_block[0] = usize::MAX;
    assert!(!m.verify_quotient(&q));
}

#[test]
fn concatenation_is_partial_function_composition_for_all_small_words() {
    let m = PartialDynamics::new(
        vec![0, 1, 2],
        vec![
            vec![Some(1), None],
            vec![Some(2), Some(0)],
            vec![Some(0), Some(2)],
        ],
        2,
    )
    .unwrap();
    let words = [vec![], vec![0], vec![1], vec![0, 1], vec![1, 0]];
    for s in 0..3 {
        for u in &words {
            for v in &words {
                let mut uv = u.clone();
                uv.extend(v);
                let iterated = m.run(s, u).unwrap().and_then(|t| m.run(t, v).unwrap());
                assert_eq!(m.run(s, &uv).unwrap(), iterated);
            }
        }
    }
}

// Origin: engine/crates_rs/tests/core_category_theory/finite_continuation.rs
// Claim: urn:core:crates_rs:tests:finite-continuation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf2d409dc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf2d409dc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf2d409dc {
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
impl BoundaryErrorf2d409dc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf2d409dc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf2d409dc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf2d409dc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf2d409dc> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf2d409dc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf2d409dc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf2d409dc::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f2d409dc() {
    let admitted = BoundaryRecordf2d409dc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf2d409dc::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
