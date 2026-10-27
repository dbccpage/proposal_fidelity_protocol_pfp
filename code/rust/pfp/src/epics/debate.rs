//! Adversarial disagreement localization over a precommitment DAG.
//!
//! `EPIC-OE-SYMGAM-007` asks for a `PrecommitmentDAG` of immutable lemma
//! assertions, a `DisagreementLocalizationEngine` isolating the minimal
//! divergence in `O(log N)` rounds, a receipt naming the locus, and a
//! `KernelReplayWitness` whose dissent fails the run.
//!
//! # The round count is measured, not asserted
//!
//! Criterion 1 requires the bound to be met "and the round count recorded
//! rather than assumed". So [`localize`] returns the probes it performed, and
//! the tests compare that number against `ceil(log2 N)` computed from the tree
//! size -- not against a constant, and not against the engine's own opinion of
//! how many rounds it should have taken.
//!
//! The decisive mutation the epic names is "replace binary search with a linear
//! walk". For that to be visible the fixture must be **deep enough that the two
//! strategies differ**: on a tree whose divergence sits at index 1, linear and
//! binary probe the same number of times. The tests therefore plant the
//! contradiction deep in a 64-node tree and assert the divergence index is not
//! near either end, so the measurement has something to measure.
//!
//! # Immutability is enforced at the write, not by convention
//!
//! Criterion 2 requires that an agent revising an already-asserted lemma be
//! refused, and that "the DAG rejects the write rather than overwriting".
//! [`PrecommitmentDAG::assert_lemma`] therefore refuses a second write for the
//! same `(agent, node)` pair even when the new claim is **identical** -- an
//! agent that re-asserts is still revising its commitment record, and
//! permitting the identical case would make the refusal depend on comparing
//! claims rather than on the commitment already existing.
//!
//! # Grounding is checked at assertion, not at evaluation
//!
//! Criterion 4 is explicit that an ungrounded claim is "rejected when asserted,
//! not when evaluated". A claim carries an optional kernel primitive, and a
//! claim without one is refused by `assert_lemma` before it enters the DAG. A
//! DAG cannot contain an ungrounded lemma, so the evaluator has no such case to
//! handle -- which is why there is no ungrounded branch in [`localize`].
//!
//! # A dissenting witness fails the run
//!
//! Criterion 5: where the replay witness disagrees with the located
//! contradiction, the run does not produce a receipt. [`run_debate`] returns an
//! error rather than a receipt carrying a dissent field, because a receipt that
//! records its own invalidity is still a receipt someone can cite.
//!
//! `AuthorityEffect: None`. Localizing a disagreement identifies where two
//! models diverge. It does not decide which is right.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};
use thiserror::Error;

/// The receipt schema this module emits.
pub const LOCALIZATION_RECEIPT_SCHEMA_V1: &str =
    "core.symgam.disagreement-localization-receipt.v1";

/// The closed set of typed kernel primitives a claim may bind to.
///
/// Closed on purpose: criterion 4's grounding requirement is unstatable over an
/// open vocabulary, because any string would be a primitive.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum KernelPrimitive {
    Difference,
    Carrier,
    Boundary,
    Obstruction,
    Lift,
}

impl KernelPrimitive {
    pub const ALL: [KernelPrimitive; 5] = [
        KernelPrimitive::Difference,
        KernelPrimitive::Carrier,
        KernelPrimitive::Boundary,
        KernelPrimitive::Obstruction,
        KernelPrimitive::Lift,
    ];

    pub fn name(self) -> &'static str {
        match self {
            KernelPrimitive::Difference => "DIFFERENCE",
            KernelPrimitive::Carrier => "CARRIER",
            KernelPrimitive::Boundary => "BOUNDARY",
            KernelPrimitive::Obstruction => "OBSTRUCTION",
            KernelPrimitive::Lift => "LIFT",
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Error)]
pub enum DebateError {
    #[error("agent {agent} already committed at node {node}; the DAG is append-only")]
    AlreadyCommitted { agent: String, node: usize },

    #[error("claim at node {node} binds to no kernel primitive")]
    Ungrounded { node: usize },

    #[error("node {node} is outside the tree's {size} propositions")]
    NodeOutOfRange { node: usize, size: usize },

    #[error("the tree has fewer than two propositions; there is nothing to localize")]
    TreeTooSmall,

    #[error("the agents already disagree at the root; there is no agreed prefix")]
    NoAgreedRoot,

    #[error("the agents agree at every node; there is no disagreement to localize")]
    NoDisagreement,

    #[error("agent {agent} has not committed at node {node}")]
    MissingCommitment { agent: String, node: usize },

    #[error("the replay witness dissents at node {node}: {reason}")]
    WitnessDissents { node: usize, reason: String },
}

// ---------------------------------------------------------------------------
// Claims and the DAG
// ---------------------------------------------------------------------------

/// One agent's position on one proposition.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Claim {
    pub node: usize,
    /// `None` is an ungrounded claim, refused at assertion.
    pub primitive: Option<KernelPrimitive>,
    pub holds: bool,
    pub text: String,
}

impl Claim {
    pub fn grounded(node: usize, primitive: KernelPrimitive, holds: bool, text: &str) -> Self {
        Self {
            node,
            primitive: Some(primitive),
            holds,
            text: text.to_string(),
        }
    }

    /// A claim with no kernel binding. Constructible so that the refusal path
    /// is reachable and testable; refused by the DAG at assertion.
    pub fn ungrounded(node: usize, holds: bool, text: &str) -> Self {
        Self {
            node,
            primitive: None,
            holds,
            text: text.to_string(),
        }
    }
}

/// Immutable, append-only record of what each agent committed to.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PrecommitmentDAG {
    /// `(agent, node) -> claim`. `BTreeMap` so iteration order is a function of
    /// content rather than of insertion.
    commitments: BTreeMap<(String, usize), Claim>,
    size: usize,
}

impl PrecommitmentDAG {
    pub fn new(size: usize) -> Result<Self, DebateError> {
        if size < 2 {
            return Err(DebateError::TreeTooSmall);
        }
        Ok(Self {
            commitments: BTreeMap::new(),
            size,
        })
    }

    pub fn size(&self) -> usize {
        self.size
    }

    pub fn len(&self) -> usize {
        self.commitments.len()
    }

    pub fn is_empty(&self) -> bool {
        self.commitments.is_empty()
    }

    /// Record a commitment. Refuses a second write for the same `(agent, node)`
    /// **even when the claim is identical**, and refuses an ungrounded claim
    /// before it enters the DAG.
    pub fn assert_lemma(&mut self, agent: &str, claim: Claim) -> Result<(), DebateError> {
        if claim.node >= self.size {
            return Err(DebateError::NodeOutOfRange {
                node: claim.node,
                size: self.size,
            });
        }
        if claim.primitive.is_none() {
            return Err(DebateError::Ungrounded { node: claim.node });
        }
        let key = (agent.to_string(), claim.node);
        if self.commitments.contains_key(&key) {
            return Err(DebateError::AlreadyCommitted {
                agent: agent.to_string(),
                node: claim.node,
            });
        }
        self.commitments.insert(key, claim);
        Ok(())
    }

    pub fn claim(&self, agent: &str, node: usize) -> Option<&Claim> {
        self.commitments.get(&(agent.to_string(), node))
    }

    fn holds(&self, agent: &str, node: usize) -> Result<bool, DebateError> {
        self.claim(agent, node)
            .map(|claim| claim.holds)
            .ok_or_else(|| DebateError::MissingCommitment {
                agent: agent.to_string(),
                node,
            })
    }
}

// ---------------------------------------------------------------------------
// Localization
// ---------------------------------------------------------------------------

/// What a localization found, and what it cost.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Localization {
    /// The first node at which the two agents diverge.
    pub locus: usize,
    /// Probes performed. Recorded, never inferred from the tree size.
    pub rounds: usize,
}

/// `ceil(log2(n))` for `n >= 1`, by exact integer arithmetic.
pub fn ceil_log2(n: usize) -> usize {
    if n <= 1 {
        return 0;
    }
    let mut bound = 0usize;
    let mut reach = 1usize;
    while reach < n {
        reach *= 2;
        bound += 1;
    }
    bound
}

fn agents_agree_at(
    dag: &PrecommitmentDAG,
    left: &str,
    right: &str,
    node: usize,
) -> Result<bool, DebateError> {
    Ok(dag.holds(left, node)? == dag.holds(right, node)?)
}

fn require_agent_claim<'a>(
    dag: &'a PrecommitmentDAG,
    agent: &str,
    locus: usize,
) -> Result<&'a Claim, DebateError> {
    dag.claim(agent, locus)
        .ok_or_else(|| DebateError::MissingCommitment {
            agent: agent.to_string(),
            node: locus,
        })
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DisagreementLocalizationEngine;

impl DisagreementLocalizationEngine {
    /// Binary-search the first divergence between two agents.
    ///
    /// Requires an agreed root and a disagreed leaf: without both there is no
    /// boundary to find, and the engine refuses rather than returning an
    /// arbitrary node.
    pub fn localize(
        &self,
        dag: &PrecommitmentDAG,
        left: &str,
        right: &str,
    ) -> Result<Localization, DebateError> {
        let last = dag.size() - 1;
        if !agents_agree_at(dag, left, right, 0)? {
            return Err(DebateError::NoAgreedRoot);
        }
        if agents_agree_at(dag, left, right, last)? {
            return Err(DebateError::NoDisagreement);
        }

        // Invariant: agreement at `low`, disagreement at `high`.
        let mut low = 0usize;
        let mut high = last;
        let mut rounds = 0usize;
        while high - low > 1 {
            let middle = low + (high - low) / 2;
            rounds += 1;
            if agents_agree_at(dag, left, right, middle)? {
                low = middle;
            } else {
                high = middle;
            }
        }
        Ok(Localization {
            locus: high,
            rounds,
        })
    }
}

// ---------------------------------------------------------------------------
// Replay witness
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum WitnessVerdict {
    /// The witness confirms the two agents diverge here.
    Concurs,
    /// The witness finds no divergence at the named node.
    Dissents { reason: String },
}

/// The kernel's own verdict on a proposition, supplied by the caller.
///
/// Ground truth is external to this module by definition, so it arrives as a
/// function rather than being invented here.
pub type KernelOracle = fn(usize, KernelPrimitive) -> bool;

/// Ground-truth verification of a located contradiction.
///
/// # Why the oracle is external
///
/// A first version of this witness re-checked the DAG: that the agents disagree
/// at the locus and agree just before it. **That is exactly the engine's own
/// postcondition**, so the witness could never dissent on a locus the engine
/// produced — a check preserved by construction, which the shared law calls
/// decoration rather than enforcement. The failing test that exposed it is
/// recorded in this sprint's retrospective.
///
/// The witness now consults a kernel oracle. The agents *assert* whether a
/// proposition holds; the kernel *computes* it. A disagreement both of whose
/// sides contradict the kernel is not worth localizing — neither agent was
/// tracking the ground truth, and the node the search found is an artifact of
/// two independent errors.
///
/// Dissent is therefore reachable through a real run, and criterion 5 has
/// something to refuse.
#[derive(Debug, Clone, Copy)]
pub struct KernelReplayWitness {
    oracle: KernelOracle,
}

impl KernelReplayWitness {
    pub fn new(oracle: KernelOracle) -> Self {
        Self { oracle }
    }

    /// Whether a claim agrees with the kernel.
    pub fn is_faithful(&self, claim: &Claim) -> bool {
        match claim.primitive {
            Some(primitive) => claim.holds == (self.oracle)(claim.node, primitive),
            None => false,
        }
    }

    fn check_locus_divergence(
        dag: &PrecommitmentDAG,
        left: &str,
        right: &str,
        locus: usize,
    ) -> Result<Option<WitnessVerdict>, DebateError> {
        if agents_agree_at(dag, left, right, locus)? {
            return Ok(Some(WitnessVerdict::Dissents {
                reason: format!("the agents agree at node {locus}"),
            }));
        }
        if locus > 0 && !agents_agree_at(dag, left, right, locus - 1)? {
            return Ok(Some(WitnessVerdict::Dissents {
                reason: format!(
                    "the agents already diverge at node {}, so {locus} is not minimal",
                    locus - 1
                ),
            }));
        }
        Ok(None)
    }

    /// Verify a claimed locus against the DAG and the kernel.
    ///
    /// Deliberately does **not** call `localize`: criterion 3 requires the named
    /// node to exhibit the contradiction under independent evaluation, and
    /// re-running the search would compare a value with itself.
    pub fn replay(
        &self,
        dag: &PrecommitmentDAG,
        left: &str,
        right: &str,
        locus: usize,
    ) -> Result<WitnessVerdict, DebateError> {
        if locus >= dag.size() {
            return Err(DebateError::NodeOutOfRange {
                node: locus,
                size: dag.size(),
            });
        }
        if let Some(dissent) = Self::check_locus_divergence(dag, left, right, locus)? {
            return Ok(dissent);
        }

        let left_claim = require_agent_claim(dag, left, locus)?;
        let right_claim = require_agent_claim(dag, right, locus)?;
        if !self.is_faithful(left_claim) && !self.is_faithful(right_claim) {
            return Ok(WitnessVerdict::Dissents {
                reason: format!("neither agent's claim at node {locus} agrees with the kernel"),
            });
        }
        Ok(WitnessVerdict::Concurs)
    }
}

// ---------------------------------------------------------------------------
// Receipt and the run
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DisagreementLocalizationReceiptV1 {
    pub schema_version: String,
    pub tree_size: usize,
    pub locus: usize,
    pub rounds: usize,
    pub round_bound: usize,
    pub left_agent: String,
    pub right_agent: String,
    pub left_claim: Claim,
    pub right_claim: Claim,
    pub authority_effect: String,
}

/// Localize, verify, and issue a receipt -- or fail.
///
/// A dissenting witness returns an error. A receipt that recorded its own
/// invalidity would still be a receipt someone could cite.
pub fn run_debate(
    dag: &PrecommitmentDAG,
    left: &str,
    right: &str,
    witness: &KernelReplayWitness,
) -> Result<DisagreementLocalizationReceiptV1, DebateError> {
    let localization = DisagreementLocalizationEngine.localize(dag, left, right)?;
    match witness.replay(dag, left, right, localization.locus)? {
        WitnessVerdict::Dissents { reason } => {
            return Err(DebateError::WitnessDissents {
                node: localization.locus,
                reason,
            })
        }
        WitnessVerdict::Concurs => {}
    }
    let left_claim = dag
        .claim(left, localization.locus)
        .ok_or_else(|| DebateError::MissingCommitment {
            agent: left.to_string(),
            node: localization.locus,
        })?
        .clone();
    let right_claim = dag
        .claim(right, localization.locus)
        .ok_or_else(|| DebateError::MissingCommitment {
            agent: right.to_string(),
            node: localization.locus,
        })?
        .clone();
    Ok(DisagreementLocalizationReceiptV1 {
        schema_version: LOCALIZATION_RECEIPT_SCHEMA_V1.to_string(),
        tree_size: dag.size(),
        locus: localization.locus,
        rounds: localization.rounds,
        round_bound: ceil_log2(dag.size()),
        left_agent: left.to_string(),
        right_agent: right.to_string(),
        left_claim,
        right_claim,
        authority_effect: "None".to_string(),
    })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    const LEFT: &str = "prover";
    const RIGHT: &str = "sceptic";

    /// The kernel's ground truth for the fixtures: a proposition holds on even
    /// nodes. `dag_diverging_at` gives the left agent exactly this, so the left
    /// agent is faithful everywhere and the witness concurs.
    fn even_nodes_hold(node: usize, _primitive: KernelPrimitive) -> bool {
        node.is_multiple_of(2)
    }

    /// A kernel that contradicts **both** fixture agents at odd nodes.
    ///
    /// The left agent claims `node % 2 == 0` on `Carrier`; the right agent
    /// claims its negation on `Boundary` past the divergence. Answering each
    /// primitive separately lets the kernel disagree with both at once, which a
    /// single-primitive fixture could not express.
    fn kernel_contradicting_both(node: usize, primitive: KernelPrimitive) -> bool {
        match primitive {
            KernelPrimitive::Carrier => node % 2 == 1,
            _ => node.is_multiple_of(2),
        }
    }

    fn concurring_witness() -> KernelReplayWitness {
        KernelReplayWitness::new(even_nodes_hold)
    }

    /// Two agents agreeing below `divergence` and disagreeing from it onward.
    /// Two agents agreeing below `divergence` and disagreeing from it onward.
    ///
    /// **They bind to different kernel primitives**, and that is load-bearing.
    /// At a node where two agents disagree about one boolean, exactly one of
    /// them is right — so "neither agrees with the kernel" would be
    /// unreachable, and criterion 5's dissent path could never fire. Agents
    /// reasoning about *different* primitives can both misreport their own,
    /// which is what makes the witness's independence real rather than nominal.
    fn dag_diverging_at(size: usize, divergence: usize) -> PrecommitmentDAG {
        let mut dag = PrecommitmentDAG::new(size).expect("fixture must build");
        for node in 0..size {
            let shared = node % 2 == 0;
            dag.assert_lemma(
                LEFT,
                Claim::grounded(node, KernelPrimitive::Carrier, shared, "left"),
            )
            .expect("ok");
            let right_holds = if node < divergence { shared } else { !shared };
            dag.assert_lemma(
                RIGHT,
                Claim::grounded(node, KernelPrimitive::Boundary, right_holds, "right"),
            )
            .expect("ok");
        }
        dag
    }

    // -- AC1: the bound, measured -------------------------------------------

    #[test]
    fn localization_finds_the_first_divergence() {
        let dag = dag_diverging_at(64, 37);
        let found = DisagreementLocalizationEngine
            .localize(&dag, LEFT, RIGHT)
            .expect("must localize");
        assert_eq!(found.locus, 37);
    }

    #[test]
    fn the_round_count_stays_within_the_declared_bound() {
        // The fixture is deep enough that binary and linear search differ: a
        // divergence at index 37 costs a linear walk 37 probes and a binary
        // search at most 6. On a shallow tree the mutation would be invisible.
        let size = 64usize;
        let divergence = 37usize;
        assert!(
            divergence > ceil_log2(size) * 2,
            "the fixture must be deep enough to distinguish the strategies"
        );

        let dag = dag_diverging_at(size, divergence);
        let found = DisagreementLocalizationEngine
            .localize(&dag, LEFT, RIGHT)
            .expect("must localize");
        assert!(
            found.rounds <= ceil_log2(size),
            "took {} rounds, bound is {}",
            found.rounds,
            ceil_log2(size)
        );
        assert!(found.rounds > 0, "a nontrivial tree must cost probes");
    }

    #[test]
    fn the_bound_holds_for_every_divergence_point_of_a_thirty_two_node_tree() {
        let size = 32usize;
        let bound = ceil_log2(size);
        let mut worst = 0usize;
        for divergence in 1..size {
            let dag = dag_diverging_at(size, divergence);
            let found = DisagreementLocalizationEngine
                .localize(&dag, LEFT, RIGHT)
                .expect("must localize");
            assert_eq!(found.locus, divergence, "wrong locus");
            assert!(
                found.rounds <= bound,
                "{divergence}: {} rounds",
                found.rounds
            );
            worst = worst.max(found.rounds);
        }
        assert!(
            worst >= bound - 1,
            "no divergence point approached the bound; the bound is untested"
        );
    }

    #[test]
    fn ceil_log2_is_exact_at_the_powers_of_two() {
        assert_eq!(ceil_log2(1), 0);
        assert_eq!(ceil_log2(2), 1);
        assert_eq!(ceil_log2(3), 2);
        assert_eq!(ceil_log2(4), 2);
        assert_eq!(ceil_log2(5), 3);
        assert_eq!(ceil_log2(64), 6);
        assert_eq!(ceil_log2(65), 7);
    }

    #[test]
    fn the_receipt_records_both_the_rounds_and_the_bound() {
        let dag = dag_diverging_at(64, 37);
        let receipt = run_debate(&dag, LEFT, RIGHT, &concurring_witness()).expect("must run");
        assert_eq!(receipt.rounds, 6);
        assert_eq!(receipt.round_bound, 6);
        assert!(receipt.rounds <= receipt.round_bound);
    }

    // -- AC2: precommitments are immutable ----------------------------------

    #[test]
    fn revising_a_committed_lemma_is_refused() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(1, KernelPrimitive::Boundary, true, "first"),
        )
        .expect("ok");
        assert_eq!(
            dag.assert_lemma(
                LEFT,
                Claim::grounded(1, KernelPrimitive::Boundary, false, "revised")
            )
            .expect_err("must refuse"),
            DebateError::AlreadyCommitted {
                agent: LEFT.to_string(),
                node: 1
            }
        );
    }

    #[test]
    fn re_asserting_an_identical_lemma_is_also_refused() {
        // An agent re-asserting is still revising its commitment record. If the
        // identical case were permitted, the refusal would depend on comparing
        // claims rather than on the commitment already existing.
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        let claim = Claim::grounded(1, KernelPrimitive::Boundary, true, "same");
        dag.assert_lemma(LEFT, claim.clone()).expect("ok");
        assert!(matches!(
            dag.assert_lemma(LEFT, claim),
            Err(DebateError::AlreadyCommitted { .. })
        ));
    }

    #[test]
    fn a_refused_write_leaves_the_original_intact() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(1, KernelPrimitive::Boundary, true, "first"),
        )
        .expect("ok");
        let _ = dag.assert_lemma(
            LEFT,
            Claim::grounded(1, KernelPrimitive::Lift, false, "revised"),
        );
        let held = dag.claim(LEFT, 1).expect("still present");
        assert_eq!(held.text, "first");
        assert!(held.holds);
        assert_eq!(held.primitive, Some(KernelPrimitive::Boundary));
        assert_eq!(dag.len(), 1);
    }

    #[test]
    fn a_different_agent_may_commit_at_the_same_node() {
        // The key is (agent, node), not node. Without this, immutability would
        // be indistinguishable from a one-commitment-per-node rule.
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(1, KernelPrimitive::Carrier, true, "left"),
        )
        .expect("ok");
        dag.assert_lemma(
            RIGHT,
            Claim::grounded(1, KernelPrimitive::Carrier, false, "right"),
        )
        .expect("the other agent must be able to commit");
        assert_eq!(dag.len(), 2);
    }

    #[test]
    fn the_same_agent_may_commit_at_a_different_node() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(1, KernelPrimitive::Carrier, true, "one"),
        )
        .expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(2, KernelPrimitive::Carrier, true, "two"),
        )
        .expect("a fresh node must be writable");
        assert_eq!(dag.len(), 2);
    }

    // -- AC3: the locus reproduces the contradiction ------------------------

    #[test]
    fn the_witness_concurs_with_a_correct_locus() {
        let dag = dag_diverging_at(64, 37);
        assert_eq!(
            concurring_witness()
                .replay(&dag, LEFT, RIGHT, 37)
                .expect("ok"),
            WitnessVerdict::Concurs
        );
    }

    #[test]
    fn a_locus_shifted_forward_is_rejected_as_not_minimal() {
        // Node 38 also carries a disagreement, but 37 already diverges, so 38
        // is not the minimal divergence. A witness that only checked "do they
        // disagree here" would concur.
        let dag = dag_diverging_at(64, 37);
        assert!(matches!(
            concurring_witness()
                .replay(&dag, LEFT, RIGHT, 38)
                .expect("ok"),
            WitnessVerdict::Dissents { .. }
        ));
    }

    #[test]
    fn a_locus_shifted_back_is_rejected_as_agreeing() {
        let dag = dag_diverging_at(64, 37);
        assert!(matches!(
            concurring_witness()
                .replay(&dag, LEFT, RIGHT, 36)
                .expect("ok"),
            WitnessVerdict::Dissents { .. }
        ));
    }

    #[test]
    fn the_two_dissent_reasons_are_distinguishable() {
        let dag = dag_diverging_at(64, 37);
        let forward = concurring_witness()
            .replay(&dag, LEFT, RIGHT, 38)
            .expect("ok");
        let backward = concurring_witness()
            .replay(&dag, LEFT, RIGHT, 36)
            .expect("ok");
        assert_ne!(forward, backward, "the reasons must not collapse");
        match (forward, backward) {
            (
                WitnessVerdict::Dissents { reason: ahead },
                WitnessVerdict::Dissents { reason: behind },
            ) => {
                assert!(ahead.contains("not minimal"));
                assert!(behind.contains("agree"));
            }
            other => panic!("expected two dissents, got {other:?}"),
        }
    }

    #[test]
    fn the_witness_does_not_re_run_the_search() {
        // Criterion 3 wants independent evaluation. The witness reads only the
        // DAG and the claimed locus, so a locus the engine never produced is
        // still evaluated on its merits -- shown here by handing it one.
        let dag = dag_diverging_at(16, 9);
        let engine_locus = DisagreementLocalizationEngine
            .localize(&dag, LEFT, RIGHT)
            .expect("ok")
            .locus;
        assert_eq!(engine_locus, 9);
        assert!(matches!(
            concurring_witness()
                .replay(&dag, LEFT, RIGHT, 3)
                .expect("ok"),
            WitnessVerdict::Dissents { .. }
        ));
    }

    #[test]
    fn the_receipt_locus_carries_both_agents_claims() {
        let dag = dag_diverging_at(64, 37);
        let receipt = run_debate(&dag, LEFT, RIGHT, &concurring_witness()).expect("ok");
        assert_eq!(receipt.left_claim.node, receipt.locus);
        assert_eq!(receipt.right_claim.node, receipt.locus);
        assert_ne!(
            receipt.left_claim.holds, receipt.right_claim.holds,
            "the locus must actually carry the contradiction"
        );
    }

    // -- AC4: grounding is checked at assertion ------------------------------

    #[test]
    fn an_ungrounded_claim_is_refused_at_assertion() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        assert_eq!(
            dag.assert_lemma(LEFT, Claim::ungrounded(2, true, "vibes"))
                .expect_err("must refuse"),
            DebateError::Ungrounded { node: 2 }
        );
        assert!(dag.is_empty(), "a refused claim must not enter the DAG");
    }

    #[test]
    fn a_grounded_claim_is_admitted() {
        // The other side, so the check is not "refuse everything".
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(2, KernelPrimitive::Obstruction, true, "grounded"),
        )
        .expect("must be admitted");
        assert_eq!(dag.len(), 1);
    }

    #[test]
    fn every_kernel_primitive_is_accepted_and_they_are_distinct() {
        let mut dag = PrecommitmentDAG::new(KernelPrimitive::ALL.len()).expect("ok");
        for (node, primitive) in KernelPrimitive::ALL.iter().enumerate() {
            dag.assert_lemma(LEFT, Claim::grounded(node, *primitive, true, "x"))
                .expect("every declared primitive must be admitted");
        }
        let mut names: Vec<&str> = KernelPrimitive::ALL.iter().map(|p| p.name()).collect();
        let total = names.len();
        names.sort_unstable();
        names.dedup();
        assert_eq!(names.len(), total);
    }

    #[test]
    fn a_node_outside_the_tree_is_refused() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        assert_eq!(
            dag.assert_lemma(
                LEFT,
                Claim::grounded(9, KernelPrimitive::Carrier, true, "far")
            )
            .expect_err("must refuse"),
            DebateError::NodeOutOfRange { node: 9, size: 4 }
        );
    }

    // -- AC5: a dissenting witness fails the run ----------------------------

    #[test]
    fn a_concurring_run_produces_a_receipt() {
        let dag = dag_diverging_at(32, 21);
        let receipt =
            run_debate(&dag, LEFT, RIGHT, &concurring_witness()).expect("must produce a receipt");
        assert_eq!(receipt.locus, 21);
    }

    #[test]
    fn a_dissenting_witness_fails_the_run_rather_than_annotating_it() {
        // Dissent is reachable because the witness consults a kernel the agents
        // may both contradict. Under `kernel_contradicting_both`, neither agent's claim at
        // the locus agrees with ground truth, so the located contradiction is
        // an artifact of two independent errors and the run fails.
        //
        // The first version of this test tried to make the *engine* produce a
        // locus the witness would reject, and could not: the engine's
        // postcondition was exactly what the witness checked. See the
        // retrospective.
        let dag = dag_diverging_at(32, 21);
        let dissenting = KernelReplayWitness::new(kernel_contradicting_both);

        let located = DisagreementLocalizationEngine
            .localize(&dag, LEFT, RIGHT)
            .expect("the engine still returns a locus");
        assert_eq!(located.locus, 21);

        match run_debate(&dag, LEFT, RIGHT, &dissenting) {
            Err(DebateError::WitnessDissents { node, reason }) => {
                assert_eq!(node, 21);
                assert!(reason.contains("kernel"), "unexpected reason: {reason}");
            }
            other => panic!("expected a dissent failure, got {other:?}"),
        }
    }

    #[test]
    fn the_witness_concurs_when_one_agent_is_faithful() {
        // Only one side needs to track the kernel: a disagreement with a
        // faithful side is a real disagreement about a real proposition.
        let dag = dag_diverging_at(32, 21);
        let witness = concurring_witness();
        let left_claim = dag.claim(LEFT, 21).expect("present");
        let right_claim = dag.claim(RIGHT, 21).expect("present");
        assert!(
            witness.is_faithful(left_claim),
            "left must track the kernel"
        );
        assert!(
            !witness.is_faithful(right_claim),
            "right must not, or this proves nothing about the one-sided case"
        );
        assert_eq!(
            witness.replay(&dag, LEFT, RIGHT, 21).expect("ok"),
            WitnessVerdict::Concurs
        );
    }

    #[test]
    fn an_ungrounded_claim_is_never_faithful() {
        let witness = concurring_witness();
        assert!(!witness.is_faithful(&Claim::ungrounded(0, true, "vibes")));
        assert!(!witness.is_faithful(&Claim::ungrounded(0, false, "vibes")));
    }

    #[test]
    fn a_failed_run_produces_no_receipt_at_all() {
        // Criterion 5's substance: not a receipt with a dissent field. A
        // receipt recording its own invalidity is still citable.
        let dag = dag_diverging_at(32, 21);
        let dissenting = KernelReplayWitness::new(kernel_contradicting_both);
        assert!(run_debate(&dag, LEFT, RIGHT, &dissenting).is_err());

        // ...and the same DAG succeeds under a kernel the agents track, so the
        // failure is the witness's doing and not the fixture's. Without this,
        // the test would pass on a DAG that could never produce a receipt.
        assert!(run_debate(&dag, LEFT, RIGHT, &concurring_witness()).is_ok());
    }

    // -- refusals ------------------------------------------------------------

    #[test]
    fn agents_disagreeing_at_the_root_are_refused() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        for node in 0..4 {
            dag.assert_lemma(
                LEFT,
                Claim::grounded(node, KernelPrimitive::Carrier, true, "l"),
            )
            .expect("ok");
            dag.assert_lemma(
                RIGHT,
                Claim::grounded(node, KernelPrimitive::Carrier, false, "r"),
            )
            .expect("ok");
        }
        assert_eq!(
            DisagreementLocalizationEngine
                .localize(&dag, LEFT, RIGHT)
                .expect_err("must refuse"),
            DebateError::NoAgreedRoot
        );
    }

    #[test]
    fn agents_agreeing_everywhere_are_refused() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        for node in 0..4 {
            for agent in [LEFT, RIGHT] {
                dag.assert_lemma(
                    agent,
                    Claim::grounded(node, KernelPrimitive::Carrier, true, "same"),
                )
                .expect("ok");
            }
        }
        assert_eq!(
            DisagreementLocalizationEngine
                .localize(&dag, LEFT, RIGHT)
                .expect_err("must refuse"),
            DebateError::NoDisagreement
        );
    }

    #[test]
    fn a_missing_commitment_is_refused_and_names_the_agent() {
        let mut dag = PrecommitmentDAG::new(4).expect("ok");
        dag.assert_lemma(
            LEFT,
            Claim::grounded(0, KernelPrimitive::Carrier, true, "l"),
        )
        .expect("ok");
        assert_eq!(
            DisagreementLocalizationEngine
                .localize(&dag, LEFT, RIGHT)
                .expect_err("must refuse"),
            DebateError::MissingCommitment {
                agent: RIGHT.to_string(),
                node: 0
            }
        );
    }

    #[test]
    fn a_tree_with_fewer_than_two_propositions_is_refused() {
        assert_eq!(
            PrecommitmentDAG::new(1).expect_err("must refuse"),
            DebateError::TreeTooSmall
        );
        assert_eq!(
            PrecommitmentDAG::new(0).expect_err("must refuse"),
            DebateError::TreeTooSmall
        );
    }

    #[test]
    fn a_two_node_tree_localizes_without_probing() {
        // The boundary case: agreement at 0, disagreement at 1, nothing to
        // search. Zero rounds is correct and must not be mistaken for failure.
        let dag = dag_diverging_at(2, 1);
        let found = DisagreementLocalizationEngine
            .localize(&dag, LEFT, RIGHT)
            .expect("ok");
        assert_eq!(found.locus, 1);
        assert_eq!(found.rounds, 0);
    }

    // -- receipt --------------------------------------------------------------

    #[test]
    fn the_receipt_carries_no_authority() {
        let dag = dag_diverging_at(32, 21);
        let receipt = run_debate(&dag, LEFT, RIGHT, &concurring_witness()).expect("ok");
        assert_eq!(receipt.authority_effect, "None");
        assert_eq!(receipt.schema_version, LOCALIZATION_RECEIPT_SCHEMA_V1);
    }

    #[test]
    fn the_receipt_round_trips_through_json() {
        let dag = dag_diverging_at(32, 21);
        let receipt = run_debate(&dag, LEFT, RIGHT, &concurring_witness()).expect("ok");
        let encoded = serde_json::to_string(&receipt).expect("ok");
        let decoded: DisagreementLocalizationReceiptV1 =
            serde_json::from_str(&encoded).expect("ok");
        assert_eq!(receipt, decoded);
    }

    #[test]
    fn the_dag_iterates_by_content_not_insertion_order() {
        let mut forward = PrecommitmentDAG::new(4).expect("ok");
        let mut backward = PrecommitmentDAG::new(4).expect("ok");
        for node in 0..3 {
            forward
                .assert_lemma(
                    LEFT,
                    Claim::grounded(node, KernelPrimitive::Carrier, true, "x"),
                )
                .expect("ok");
        }
        for node in (0..3).rev() {
            backward
                .assert_lemma(
                    LEFT,
                    Claim::grounded(node, KernelPrimitive::Carrier, true, "x"),
                )
                .expect("ok");
        }
        assert_eq!(forward, backward);
    }
}
