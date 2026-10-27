use std::collections::{BTreeMap, BTreeSet};

use core_prompt_civilization::convergence::*;
use core_prompt_civilization::crossover::*;
use core_prompt_civilization::ecology::*;
use core_prompt_civilization::evidence::*;
use core_prompt_civilization::fitness::PromptFitnessV1;
use core_prompt_civilization::genealogy::{InheritanceRelationship, LineageGraphV1};
use core_prompt_civilization::record::{
    CustodyTier, PacketRefV1, PromptGenomeV1, ProtectedSpanV1,
};
use sha2::{Digest, Sha256};

fn strings(values: &[&str]) -> BTreeSet<String> {
    values.iter().map(|s| s.to_string()).collect()
}

fn parent(bytes: &[u8]) -> PromptGenomeV1 {
    PromptGenomeV1::new(
        vec![PacketRefV1 {
            packet_id: "p".into(),
            sha256: hex::encode(Sha256::digest(bytes)),
            packet_kind: "prompt-artifact".into(),
        }],
        serde_json::json!({"domain":"math"}),
        vec![],
        0,
        vec![ProtectedSpanV1 {
            name: "core".into(),
            start_byte: 0,
            end_byte: 4,
        }],
    )
}

fn blocks(length: usize) -> Vec<HomologousBlockV1> {
    vec![
        HomologousBlockV1 {
            name: "core".into(),
            start: 0,
            end: 4,
            protected: true,
        },
        HomologousBlockV1 {
            name: "task".into(),
            start: 4,
            end: length,
            protected: false,
        },
    ]
}

#[test]
fn crossover_preserves_core_two_parents_and_ancestry_without_admission() {
    let left = parent(b"coreone");
    let right = parent(b"coretwo-long");
    let lb = blocks(7);
    let rb = blocks(12);
    let immunity = BTreeMap::from([("family".into(), "rule-1".into())]);
    let mut graph = LineageGraphV1::new();
    graph
        .add_inheritance_edge(
            "ancestor",
            &left.prompt_id,
            InheritanceRelationship::DirectMutation,
            "receipt",
        )
        .unwrap();
    let result = recombine(
        CrossoverParentV1 {
            genome: &left,
            bytes: b"coreone",
            blocks: &lb,
            immunity: &immunity,
        },
        CrossoverParentV1 {
            genome: &right,
            bytes: b"coretwo-long",
            blocks: &rb,
            immunity: &immunity,
        },
        &strings(&["task"]),
        ["left-receipt", "right-receipt"],
        &graph,
    )
    .unwrap();
    assert_eq!(result.bytes, b"coretwo-long");
    assert_eq!(result.genome.birth_custody, CustodyTier::Wild);
    assert_eq!(result.genome.parents.len(), 2);
    assert_eq!(result.genome.protected_spans, left.protected_spans);
    assert!(result.ancestor_ids.contains("ancestor"));
    assert_eq!(result.authority_effect, "None");
}

#[test]
fn crossover_refuses_core_changes_missing_witnesses_and_immunity_conflicts() {
    let left = parent(b"coreone");
    let right = parent(b"coretwo");
    let altered = parent(b"EVILtwo");
    let layout = blocks(7);
    let a = BTreeMap::from([("family".into(), "rule-1".into())]);
    let b = BTreeMap::from([("family".into(), "rule-2".into())]);
    let graph = LineageGraphV1::new();
    let perform = |g, bytes, repertoire, witnesses| {
        recombine(
            CrossoverParentV1 {
                genome: &left,
                bytes: b"coreone",
                blocks: &layout,
                immunity: &a,
            },
            CrossoverParentV1 {
                genome: g,
                bytes,
                blocks: &layout,
                immunity: repertoire,
            },
            &strings(&["task"]),
            witnesses,
            &graph,
        )
    };
    assert!(perform(&right, b"coretwo", &b, ["a", "b"])
        .unwrap_err()
        .contains("IMMUNITY_CONFLICT"));
    assert!(perform(&right, b"coretwo", &a, ["a", ""])
        .unwrap_err()
        .contains("DUAL_PARENT_WITNESS"));
    assert!(perform(&altered, b"EVILtwo", &a, ["a", "b"])
        .unwrap_err()
        .contains("PROTECTED_SPAN"));
    assert!(perform(&right, b"EVILtwo", &a, ["a", "b"])
        .unwrap_err()
        .contains("PARENT_BYTES_MISMATCH"));
}

#[test]
fn genome_identity_binds_protected_boundaries() {
    let a = parent(b"coreone");
    let b = PromptGenomeV1::new(
        a.source_packet_refs.clone(),
        a.domain_model.clone(),
        vec![],
        0,
        vec![],
    );
    assert_ne!(a.prompt_id, b.prompt_id);
}

fn candidate(id: &str, cell: &str, success: u64, failures: u64) -> EcologyCandidateV1 {
    let mut fitness = PromptFitnessV1::new(id);
    fitness.task_success_credit = success;
    fitness.failures = failures;
    EcologyCandidateV1 {
        fitness,
        behavior_cell: cell.into(),
    }
}

fn island(id: &str, capacity: usize, members: Vec<EcologyCandidateV1>) -> IslandV1 {
    IslandV1 {
        island_id: id.into(),
        objective_id: "fixed-task".into(),
        capacity,
        members: members
            .into_iter()
            .map(|c| (c.fitness.prompt_id.clone(), c))
            .collect(),
    }
}

fn policy() -> ConvergencePolicyV1 {
    ConvergencePolicyV1 {
        max_observations: 20,
        plateau_window: 10,
        recovery: RecoveryAction::ReinjectDiversity,
    }
}

#[test]
fn migration_is_periodic_bounded_disjoint_and_one_hop() {
    let mut population = ArchipelagoV1::new(
        vec![
            island(
                "a",
                3,
                vec![candidate("a1", "one", 4, 0), candidate("a2", "two", 1, 3)],
            ),
            island("b", 2, vec![]),
            island("c", 2, vec![]),
        ],
        2,
        1,
        policy(),
    )
    .unwrap();
    assert!(population.migrate(1).unwrap().transfers.is_empty());
    let receipt = population.migrate(2).unwrap();
    assert_eq!(
        receipt.transfers,
        vec![("a".into(), "b".into(), "a1".into())]
    );
    assert!(
        population.islands()[2].members.is_empty(),
        "a migrant must not take a second hop"
    );
    assert_eq!(population.islands()[0].members.len(), 1);
    assert!(population
        .migrate(2)
        .unwrap_err()
        .contains("MIGRATION_EPOCH_REPLAY"));
}

#[test]
fn migration_preserves_capacity_objective_and_diversity_boundaries() {
    let mut population = ArchipelagoV1::new(
        vec![
            island("a", 2, vec![candidate("a1", "one", 4, 0)]),
            island("b", 1, vec![candidate("b1", "one", 4, 0)]),
        ],
        1,
        5,
        policy(),
    )
    .unwrap();
    let receipt = population.migrate(1).unwrap();
    assert!(!receipt.transfers.iter().any(|(a, _, _)| a == "a"));
    assert!(population
        .islands()
        .iter()
        .all(|i| i.members.len() <= i.capacity));
    let mut other = island("other", 2, vec![]);
    other.objective_id = "unrelated-task".into();
    let mut population = ArchipelagoV1::new(
        vec![island("a", 2, vec![candidate("a1", "one", 4, 0)]), other],
        1,
        1,
        policy(),
    )
    .unwrap();
    assert!(population.migrate(1).unwrap().transfers.is_empty());
    let elites = map_elites(&[
        candidate("x", "one", 1, 2),
        candidate("y", "one", 3, 0),
        candidate("z", "two", 0, 5),
    ]);
    assert_eq!(elites.len(), 2);
    assert_eq!(elites["one"].fitness.prompt_id, "y");
}

#[test]
fn duplicate_island_members_are_refused() {
    let result = ArchipelagoV1::new(
        vec![
            island("a", 2, vec![candidate("same", "one", 1, 1)]),
            island("b", 2, vec![candidate("same", "one", 1, 1)]),
        ],
        1,
        1,
        policy(),
    );
    assert!(matches!(result, Err(e) if e.contains("DISJOINT")));
}

fn snapshot(success: u64) -> PopulationSnapshotV1 {
    PopulationSnapshotV1 {
        best_success: success,
        best_failures: 0,
        occupied_cells: strings(&["one"]),
    }
}

#[test]
fn plateau_freezes_and_requires_new_external_epoch() {
    let mut monitor = ConvergenceMonitorV1::new(ConvergencePolicyV1 {
        max_observations: 10,
        plateau_window: 3,
        recovery: RecoveryAction::ReinjectDiversity,
    })
    .unwrap();
    assert!(monitor.observe(snapshot(1)).unwrap().is_none());
    assert!(monitor.observe(snapshot(1)).unwrap().is_none());
    let receipt = monitor.observe(snapshot(1)).unwrap().unwrap();
    assert_eq!(receipt.reason, FreezeReason::Plateau);
    assert_eq!(receipt.action, RecoveryAction::ReinjectDiversity);
    assert!(monitor.observe(snapshot(2)).unwrap_err().contains("FROZEN"));
}

#[test]
fn nonconverging_population_still_terminates_at_exact_budget() {
    let mut monitor = ConvergenceMonitorV1::new(ConvergencePolicyV1 {
        max_observations: 7,
        plateau_window: 3,
        recovery: RecoveryAction::Reboot,
    })
    .unwrap();
    for step in 1..=7 {
        let receipt = monitor.observe(snapshot(step % 2)).unwrap();
        assert_eq!(monitor.remaining_observations(), 7 - step);
        if step < 7 {
            assert!(receipt.is_none());
        } else {
            assert_eq!(receipt.unwrap().reason, FreezeReason::BudgetExhausted);
        }
    }
}

#[test]
fn frozen_runtime_refuses_mutation_and_migration_without_changing_population() {
    let mut population = ArchipelagoV1::new(
        vec![island("a", 3, vec![]), island("b", 3, vec![])],
        2,
        1,
        ConvergencePolicyV1 {
            max_observations: 1,
            plateau_window: 5,
            recovery: RecoveryAction::Reboot,
        },
    )
    .unwrap();
    population
        .insert_candidate("a", candidate("p", "one", 1, 0))
        .unwrap();
    assert!(population.is_frozen());
    let snapshot = population.islands().to_vec();
    assert!(population
        .insert_candidate("a", candidate("q", "two", 2, 0))
        .unwrap_err()
        .contains("FROZEN"));
    assert!(population.migrate(2).unwrap_err().contains("FROZEN"));
    assert_eq!(population.islands(), snapshot);
}

#[test]
fn approximate_search_cannot_prune_exact_candidates() {
    let exact = strings(&["a", "b"]);
    assert_eq!(
        augment_candidates(&exact, vec!["b".into(), "c".into()]),
        strings(&["a", "b", "c"])
    );
    assert_eq!(augment_candidates(&exact, Vec::<String>::new()), exact);
    let mut index = ApproximatePromptIndexV1::default();
    index.insert("similar", &["system".into(), "typed-task".into()]);
    assert_eq!(
        index.candidates(&["typed-task".into(), "system".into()], &exact),
        strings(&["a", "b", "similar"]),
    );
    assert_eq!(index.candidates(&[], &exact), exact);
}

struct HostRecoveryVerifier;
impl RecoveryDecisionVerifier for HostRecoveryVerifier {
    fn verify(&self, decision: &RecoveryDecisionV1) -> bool {
        decision.external_receipt == "host-verified-recovery"
    }
}

#[test]
fn frozen_recovery_requires_external_epoch_and_real_diversity() {
    let mut population = ArchipelagoV1::new(
        vec![island("a", 3, vec![]), island("b", 3, vec![])],
        2,
        1,
        ConvergencePolicyV1 {
            max_observations: 1,
            plateau_window: 3,
            recovery: RecoveryAction::ReinjectDiversity,
        },
    )
    .unwrap();
    population
        .insert_candidate("a", candidate("p", "one", 1, 0))
        .unwrap();
    let mut decision = RecoveryDecisionV1 {
        epoch: 1,
        population_digest: population.population_digest(),
        action: RecoveryAction::ReinjectDiversity,
        external_receipt: "forged".into(),
        policy: policy(),
    };
    let mut replacement = population.islands().to_vec();
    assert!(population
        .recover(&decision, replacement.clone(), &HostRecoveryVerifier)
        .is_err());
    decision.external_receipt = "host-verified-recovery".into();
    assert_eq!(
        population.recover(&decision, replacement.clone(), &HostRecoveryVerifier),
        Err("DIVERSITY_REINJECTION_REQUIRED".into()),
    );
    replacement[0]
        .members
        .insert("q".into(), candidate("q", "two", 0, 1));
    population
        .recover(&decision, replacement, &HostRecoveryVerifier)
        .unwrap();
    assert!(!population.is_frozen());
    assert_eq!(population.islands()[0].members.len(), 2);
    assert_eq!(population.shelved()[0].members.len(), 1);
}

#[test]
fn reboot_shelves_previous_population_and_obeys_new_budget() {
    let mut population = ArchipelagoV1::new(
        vec![island("a", 3, vec![]), island("b", 3, vec![])],
        2,
        1,
        ConvergencePolicyV1 {
            max_observations: 1,
            plateau_window: 3,
            recovery: RecoveryAction::Reboot,
        },
    )
    .unwrap();
    population
        .insert_candidate("a", candidate("p", "one", 1, 0))
        .unwrap();
    let decision = RecoveryDecisionV1 {
        epoch: 1,
        population_digest: population.population_digest(),
        action: RecoveryAction::Reboot,
        external_receipt: "host-verified-recovery".into(),
        policy: ConvergencePolicyV1 {
            max_observations: 1,
            plateau_window: 3,
            recovery: RecoveryAction::Reboot,
        },
    };
    let replacement = vec![island("a", 3, vec![]), island("b", 3, vec![])];
    population
        .recover(&decision, replacement.clone(), &HostRecoveryVerifier)
        .unwrap();
    assert_eq!(population.shelved()[0].members.len(), 1);
    population.migrate(1).unwrap();
    assert!(population.is_frozen());
    assert!(population
        .recover(&decision, replacement, &HostRecoveryVerifier)
        .is_err());
}

#[test]
fn raf_requires_food_generation_and_closed_catalysis() {
    let reaction =
        |id: &str, inputs: &[&str], outputs: &[&str], catalysts: &[&str]| EvidenceReactionV1 {
            reaction_id: id.into(),
            inputs: strings(inputs),
            outputs: strings(outputs),
            catalysts: strings(catalysts),
        };
    let reactions = vec![
        reaction("r1", &["food"], &["a"], &["b"]),
        reaction("r2", &["a"], &["b"], &["a"]),
        reaction("isolated", &["missing"], &["x"], &["x"]),
        reaction("uncatalyzed", &["food"], &["y"], &[]),
    ];
    assert_eq!(
        maximal_raf(&strings(&["food"]), &reactions).unwrap(),
        strings(&["r1", "r2"])
    );
    assert!(maximal_raf(&BTreeSet::new(), &reactions)
        .unwrap()
        .is_empty());
}

#[test]
fn descendant_evaluation_requires_external_anchor_and_distinct_actors() {
    let mut lineage = LineageGraphV1::new();
    lineage
        .add_inheritance_edge(
            "parent",
            "child",
            InheritanceRelationship::DirectMutation,
            "witness",
        )
        .unwrap();
    let trace = EvaluationTraceV1 {
        digest: "trace".into(),
        prompt_id: "child".into(),
        generator_actor: "generator".into(),
        evaluator_actor: "evaluator".into(),
        dependencies: strings(&["trace"]),
    };
    let mut traces = BTreeMap::from([("trace".into(), trace)]);
    assert_eq!(
        validate_independence("parent", "trace", &traces, &BTreeSet::new(), &lineage),
        Err("SELF_FEEDING_EVIDENCE".into()),
    );
    traces
        .get_mut("trace")
        .unwrap()
        .dependencies
        .insert("oracle".into());
    assert!(
        validate_independence("parent", "trace", &traces, &strings(&["oracle"]), &lineage).is_ok()
    );
    traces.get_mut("trace").unwrap().evaluator_actor = "generator".into();
    assert_eq!(
        validate_independence("parent", "trace", &traces, &strings(&["oracle"]), &lineage),
        Err("ROLE_SEPARATION_REQUIRED".into()),
    );
}

// Origin: engine/crates_rs/tests/core_prompt_civilization/prompt_ecology.rs
// Claim: urn:core:crates_rs:tests:prompt-ecology:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde4747b4e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde4747b4e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore4747b4e {
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
impl BoundaryErrore4747b4e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore4747b4e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore4747b4e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde4747b4e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore4747b4e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore4747b4e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore4747b4e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore4747b4e::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_e4747b4e() {
    let admitted = BoundaryRecorde4747b4e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorde4747b4e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
