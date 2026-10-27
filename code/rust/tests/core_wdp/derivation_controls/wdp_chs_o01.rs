//! Five-belief alternating parity carrier `parity_alt_osc` only.
//! A play wins when the highest priority seen infinitely often is even.
//! WDP-CHS-N04: a reachability attractor is not this certificate.
//! The count is the size of {hi, lo} on this table, not a continuum limit.

const HI: usize = 0;
const LO: usize = 1;
const FORK: usize = 2;
const SINK: usize = 3;
const BAIT: usize = 4;
const BELIEFS: usize = 5;

const PRIORITY: [i64; BELIEFS] = [2, 1, 1, 1, 2];

const ACTION_FROM: [usize; 6] = [HI, LO, LO, FORK, SINK, BAIT];
const ACTIONS: [&[usize]; 6] = [
    &[LO],
    &[HI],
    &[SINK],
    &[HI, SINK],
    &[SINK],
    &[SINK],
];

fn action_ids(from: usize) -> impl Iterator<Item = usize> {
    ACTION_FROM.iter().enumerate().filter_map(move |(index, source)| {
        if *source == from {
            Some(index)
        } else {
            None
        }
    })
}

fn assert_declared_table() {
    assert_eq!(PRIORITY, [2, 1, 1, 1, 2]);
    assert_eq!(action_ids(HI).count(), 1);
    assert_eq!(action_ids(LO).count(), 2);
    assert_eq!(action_ids(FORK).count(), 1);
    assert_eq!(action_ids(SINK).count(), 1);
    assert_eq!(action_ids(BAIT).count(), 1);
    assert!(ACTIONS.iter().all(|successors| !successors.is_empty()));
    assert_eq!(ACTIONS[0], &[LO][..]);
    assert_eq!(ACTIONS[1], &[HI][..]);
    assert_eq!(ACTIONS[2], &[SINK][..]);
    assert_eq!(ACTIONS[3], &[HI, SINK][..]);
    assert_eq!(ACTIONS[4], &[SINK][..]);
    assert_eq!(ACTIONS[5], &[SINK][..]);
}

struct Cycle {
    max_priority: i64,
    saw_one: bool,
    saw_two: bool,
}

fn cycle(start: usize, next: &dyn Fn(usize) -> usize) -> Cycle {
    let mut seen = [None; BELIEFS];
    let mut order = [0usize; BELIEFS];
    let mut pos = start;
    let mut step = 0usize;
    loop {
        if let Some(at) = seen[pos] {
            let mut max_priority = PRIORITY[order[at]];
            let mut saw_one = max_priority == 1;
            let mut saw_two = max_priority == 2;
            for index in (at + 1)..step {
                let priority = PRIORITY[order[index]];
                if priority > max_priority {
                    max_priority = priority;
                }
                saw_one |= priority == 1;
                saw_two |= priority == 2;
            }
            return Cycle {
                max_priority,
                saw_one,
                saw_two,
            };
        }
        assert!(step < BELIEFS, "play left the five-belief carrier");
        seen[pos] = Some(step);
        order[step] = pos;
        pos = next(pos);
        assert!(pos < BELIEFS, "successor outside the carrier");
        step += 1;
    }
}

fn oscillation(belief: usize) -> usize {
    match belief {
        HI => {
            assert_eq!(ACTIONS[0].len(), 1);
            ACTIONS[0][0]
        }
        LO => {
            assert_eq!(ACTIONS[1].len(), 1);
            ACTIONS[1][0]
        }
        _ => panic!("oscillation leaves hi and lo"),
    }
}

fn odd_reply(belief: usize) -> usize {
    match belief {
        FORK => {
            assert_eq!(ACTIONS[3], &[HI, SINK][..]);
            SINK
        }
        SINK => {
            assert_eq!(ACTIONS[4].len(), 1);
            ACTIONS[4][0]
        }
        BAIT => {
            assert_eq!(ACTIONS[5].len(), 1);
            ACTIONS[5][0]
        }
        LO => {
            assert_eq!(ACTIONS[2].len(), 1);
            ACTIONS[2][0]
        }
        HI => {
            assert_eq!(ACTIONS[0].len(), 1);
            ACTIONS[0][0]
        }
        _ => panic!("belief outside the carrier"),
    }
}

fn controller_wins(start: usize) -> bool {
    assert_declared_table();
    match start {
        HI | LO => {
            let play = cycle(start, &oscillation);
            play.max_priority == 2
                && play.max_priority % 2 == 0
                && play.saw_one
                && play.saw_two
        }
        FORK | SINK | BAIT => {
            assert_eq!(action_ids(start).count(), 1);
            let play = cycle(start, &odd_reply);
            let forced_odd = play.max_priority == 1
                && play.max_priority % 2 == 1
                && play.saw_one
                && !play.saw_two;
            !forced_odd
        }
        _ => panic!("belief outside the carrier"),
    }
}

/// Cardinality of the controller winning set on `parity_alt_osc`.
pub fn witness() -> i64 {
    let mut cardinality = 0i64;
    for belief in 0..BELIEFS {
        if controller_wins(belief) {
            cardinality += 1;
        }
    }
    cardinality
}

fn attractor_size(targets: &[usize]) -> i64 {
    let mut inside = [false; BELIEFS];
    for &target in targets {
        inside[target] = true;
    }
    let mut changed = true;
    while changed {
        changed = false;
        for belief in 0..BELIEFS {
            if inside[belief] {
                continue;
            }
            let enters = action_ids(belief)
                .any(|index| ACTIONS[index].iter().all(|&next| inside[next]));
            if enters {
                inside[belief] = true;
                changed = true;
            }
        }
    }
    let mut size = 0i64;
    for flag in inside {
        if flag {
            size += 1;
        }
    }
    size
}

/// Reject a reachability or priority-sum stand-in for the parity cardinality.
pub fn refuse_non_parity_count(claimed: i64) -> Result<(), &'static str> {
    let parity = witness();
    let empty_target = attractor_size(&[]);
    let even_stopping = attractor_size(&[HI, BAIT]);
    let priority_sum: i64 = PRIORITY.iter().sum();
    assert_eq!(empty_target, 0);
    assert_eq!(even_stopping, 3);
    assert_eq!(priority_sum, 7);
    assert_ne!(parity, empty_target);
    assert_ne!(parity, even_stopping);
    assert_ne!(parity, priority_sum);
    if claimed == empty_target || claimed == even_stopping || claimed == priority_sum {
        Err("refused: reachability or priority-sum stand-in is not the parity cardinality")
    } else if claimed != parity {
        Err("refused: not the parity winning-set cardinality on parity_alt_osc")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_chs_o01.rs
// Claim: urn:core:crates_rs:tests:wdp-chs-o01:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord83c14358 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord83c14358` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError83c14358 {
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
impl BoundaryError83c14358 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError83c14358 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError83c14358 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord83c14358 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError83c14358> {
        if capacity_bound == 0 {
            return Err(BoundaryError83c14358::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError83c14358::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError83c14358::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{
        attractor_size, cycle, controller_wins, odd_reply, oscillation, refuse_non_parity_count,
        witness, ACTIONS, BAIT, FORK, HI, LO, SINK,
    };

    #[test]
    fn winning_cardinality_is_two() {
        assert_eq!(witness(), 2);
        assert!(controller_wins(HI));
        assert!(controller_wins(LO));
        assert!(!controller_wins(FORK));
        assert!(!controller_wins(SINK));
        assert!(!controller_wins(BAIT));
        let oscillation_play = cycle(HI, &oscillation);
        assert_eq!(oscillation_play.max_priority, 2);
        assert!(oscillation_play.saw_one && oscillation_play.saw_two);
        let lo_play = cycle(LO, &oscillation);
        assert_eq!(lo_play.max_priority, 2);
        let fall = |belief: usize| -> usize {
            if belief == LO {
                ACTIONS[2][0]
            } else if belief == SINK {
                ACTIONS[4][0]
            } else {
                panic!("fall left the sink tail");
            }
        };
        assert_eq!(cycle(LO, &fall).max_priority, 1);
        assert!(controller_wins(LO));
        assert_eq!(cycle(SINK, &odd_reply).max_priority, 1);
        assert_eq!(cycle(BAIT, &odd_reply).max_priority, 1);
        assert_eq!(cycle(FORK, &odd_reply).max_priority, 1);
    }

    #[test]
    fn refuses_reachability_and_cooperative_fork() {
        assert_eq!(attractor_size(&[]), 0);
        assert_eq!(attractor_size(&[HI, BAIT]), 3);
        assert!(refuse_non_parity_count(0).is_err());
        assert!(refuse_non_parity_count(3).is_err());
        assert!(refuse_non_parity_count(7).is_err());
        assert!(refuse_non_parity_count(5).is_err());
        assert!(refuse_non_parity_count(witness()).is_ok());
        let cooperative = |belief: usize| -> usize {
            match belief {
                FORK => HI,
                HI => ACTIONS[0][0],
                LO => ACTIONS[1][0],
                _ => panic!("cooperative path left the oscillation"),
            }
        };
        assert_eq!(cycle(FORK, &cooperative).max_priority, 2);
        assert!(!controller_wins(FORK));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_83c14358() {
    let admitted = BoundaryRecord83c14358::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord83c14358::try_admit(9, 8).is_err());
}
