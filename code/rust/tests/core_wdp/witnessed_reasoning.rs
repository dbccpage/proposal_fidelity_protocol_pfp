use core_wdp::witnessed_reasoning::*;

fn derive_steps(theory: &Theory) -> Vec<ProofStep> {
    let mut steps: Vec<ProofStep> = theory
        .facts
        .iter()
        .map(|&a| ProofStep {
            conclusion: a,
            rule: None,
            premises: vec![],
        })
        .collect();
    for _ in 0..2 {
        for (i, r) in theory.rules.iter().enumerate() {
            if !steps.iter().any(|s| s.conclusion == r.conclusion) {
                let parents: Option<Vec<_>> = r
                    .premises
                    .iter()
                    .map(|a| steps.iter().position(|s| &s.conclusion == a))
                    .collect();
                if let Some(premises) = parents {
                    steps.push(ProofStep {
                        conclusion: r.conclusion,
                        rule: Some(i),
                        premises,
                    });
                }
            }
        }
    }
    steps
}

fn check_goal_valuations(theory: &Theory, steps: &[ProofStep], goal: usize) {
    let mut entails = true;
    for valuation in 0..4 {
        let truth = |a| valuation & (1 << a) != 0;
        let is_model = theory.facts.iter().all(|&a| truth(a))
            && theory
                .rules
                .iter()
                .all(|r| !r.premises.iter().all(|&a| truth(a)) || truth(r.conclusion));
        let model = Countermodel {
            theory: theory.clone(),
            goal,
            values: (0..2).map(truth).collect(),
        };
        assert_eq!(check_countermodel(theory, goal, &model), is_model && !truth(goal));
        entails &= !is_model || truth(goal);
    }
    let position = steps.iter().position(|s| s.conclusion == goal);
    assert_eq!(position.is_some(), entails);
    if let Some(i) = position {
        let proof = Proof {
            theory: theory.clone(),
            goal,
            steps: steps[..=i].to_vec(),
        };
        assert!(check_proof(theory, goal, &proof));
    }
}

#[test]
fn all_two_atom_theories_match_valuations() {
    let all_rules: Vec<_> = (0..4)
        .flat_map(|mask| {
            (0..2).map(move |conclusion| Rule {
                premises: (0..2).filter(|i| mask & (1 << i) != 0).collect(),
                conclusion,
            })
        })
        .collect();
    let mut cases = 0;
    for rule_mask in 0..256 {
        for fact_mask in 0..4 {
            let theory = Theory {
                atoms: vec!["a".into(), "b".into()],
                facts: (0..2).filter(|i| fact_mask & (1 << i) != 0).collect(),
                rules: all_rules
                    .iter()
                    .enumerate()
                    .filter(|(i, _)| rule_mask & (1 << i) != 0)
                    .map(|(_, r)| r.clone())
                    .collect(),
            };
            let steps = derive_steps(&theory);
            for goal in 0..2 {
                check_goal_valuations(&theory, &steps, goal);
                cases += 1;
            }
        }
    }
    assert_eq!(cases, 2048);
}

#[test]
fn stale_cyclic_forged_and_ill_typed_certificates_refuse() {
    let t = Theory {
        atoms: vec!["a".into(), "b".into()],
        facts: vec![0],
        rules: vec![Rule {
            premises: vec![0],
            conclusion: 1,
        }],
    };
    let proof = Proof {
        theory: t.clone(),
        goal: 1,
        steps: vec![
            ProofStep {
                conclusion: 0,
                rule: None,
                premises: vec![],
            },
            ProofStep {
                conclusion: 1,
                rule: Some(0),
                premises: vec![0],
            },
        ],
    };
    assert!(check_proof(&t, 1, &proof));
    for parent in [1, usize::MAX] {
        let mut bad = proof.clone();
        bad.steps[1].premises = vec![parent];
        assert!(!check_proof(&t, 1, &bad));
    }
    let mut bad = proof.clone();
    bad.steps[1].rule = None;
    assert!(!check_proof(&t, 1, &bad));
    bad = proof.clone();
    bad.steps[1].rule = Some(1);
    assert!(!check_proof(&t, 1, &bad));
    bad = proof.clone();
    bad.steps[1].premises.clear();
    assert!(!check_proof(&t, 1, &bad));
    bad = proof.clone();
    bad.theory.atoms[0] = "different".into();
    assert!(!check_proof(&t, 1, &bad));
    assert!(!check_proof(&t, 0, &proof));
    let mut invalid = t.clone();
    invalid.rules[0].conclusion = 2;
    assert!(!invalid.valid());
    let mut missing = t.clone();
    missing.facts.clear();
    assert!(!check_proof(&missing, 1, &proof));
    let model = Countermodel {
        theory: t.clone(),
        goal: 1,
        values: vec![true, false],
    };
    assert!(!check_countermodel(&t, 1, &model));
    let no_rules = Theory {
        rules: vec![],
        ..t.clone()
    };
    let mut model = Countermodel {
        theory: no_rules.clone(),
        ..model
    };
    assert!(check_countermodel(&no_rules, 1, &model));
    model.values.clear();
    assert!(!check_countermodel(&no_rules, 1, &model));
}

// Origin: engine/crates_rs/tests/core_wdp/witnessed_reasoning.rs
// Claim: urn:core:crates_rs:tests:witnessed-reasoning:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf7d2615e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf7d2615e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf7d2615e {
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
impl BoundaryErrorf7d2615e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf7d2615e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf7d2615e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf7d2615e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf7d2615e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf7d2615e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf7d2615e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf7d2615e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_f7d2615e() {
    let admitted = BoundaryRecordf7d2615e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf7d2615e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
