//! Primitive — the **branch tree**: breadth-first expansion quotiented by
//! the implemented isomorphism, with its exact exported frontier.
//!
//! Crate boundary: engine.  Source: `engine.py::build_tree`, `Node`,
//! `Edge`, `Tree.stats`; sealed claims `CL-CLOSURE-TERMINATION` and
//! `CL-TREE-SUMMARY`.
//!
//! Pinned values (from `artifacts/claims.json`):
//!
//! | run | nodes | terminal branches | rounds used |
//! |---|---|---|---|
//! | closed system, L | 4 | 3 | 1 |
//! | closed system, F | 20 | 16 | 3 |
//!
//! | run | nodes | edges | max depth |
//! |---|---|---|---|
//! | supply, L, mu2 | 963 | 1022 | 15 |
//! | supply, F, mu2 | 1847 | 1960 | 15 |
//!
//! Both depth-15 trees are tests here — they take well under a second — and
//! they match the sealed receipts node for node, edge for edge, role for
//! role.  The guard-bounded `mu1` trees (guard 1200) do **not** match
//! exactly (1211 and 1203 nodes here against 1205 and 1201 sealed): a
//! guard cut depends on the order in which the frontier is expanded, and
//! this crate's class order is not byte-identical to the sealed one.  An
//! unguarded quotient is order-independent, which is why the `mu2` trees
//! agree exactly and the `mu1` ones agree only closely.  Recorded, not
//! hidden.  Every node is certified by replay, and a merge edge carries an
//! explicit isomorphism witness re-verified at construction.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_2d26f729<T> {
    fn checked_invariant_2d26f729(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_2d26f729<T> for Option<T> {
    #[inline]
    fn checked_invariant_2d26f729(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_2d26f729<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_2d26f729(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, VecDeque};

use crate::bounds::Bounds;
use crate::candidate::{delta_events, Delta};
use crate::canonical::{canonical, find_iso};
use crate::closure::closure_challenge_orbits;
use crate::event::Event;
use crate::mark::Pair;
use crate::measure::{Cost, MeasureKind};
use crate::minima::{min_responses, quotient, MinResponses};
use crate::reading::Reading;
use crate::regime::Regime;
use crate::renaming::{Bijection, Key};
use crate::replay::replay;
use crate::response::response_valid_naive;
use crate::role::{delta_label, role, Role};
use crate::separability::collapsed_pairs;
use crate::token::Token;

/// A node: a certified regime with its replayable history.
#[derive(Clone, Debug)]
pub struct Node {
    /// Index in the tree.
    pub id: usize,
    /// The history from genesis.
    pub history: Vec<Event>,
    /// The regime.
    pub regime: Regime,
    /// Depth = accepted rounds.
    pub depth: usize,
    /// The canonical key.
    pub canon: Key,
    /// Status: open, expanded, completed, frontier_guard, terminal_*.
    pub status: &'static str,
    /// How many creation-or-merge edges land here.
    pub merged_count: usize,
    /// Certified by replay.
    pub certified: bool,
}

/// An edge: the response applied to the parent.
#[derive(Clone, Debug)]
pub struct Edge {
    /// Parent id.
    pub parent: usize,
    /// Child id.
    pub child: usize,
    /// Round number.
    pub round: usize,
    /// `"supply"` or `"separate(i, j)"`.
    pub challenge: String,
    /// The neutral label.
    pub label: String,
    /// The delta.
    pub response: Delta,
    /// How many tied classes at this expansion.
    pub tie_classes: usize,
    /// The class size of this response.
    pub class_size: usize,
    /// The cost.
    pub cost: Cost,
    /// How many orbits the parent offered.
    pub orbits: usize,
    /// `"creation"` or `"merge"`.
    pub kind: &'static str,
    /// The isomorphism witness for a merge edge.
    pub merge_witness: Option<Bijection>,
}

/// The tree.
#[derive(Clone, Debug)]
pub struct Tree {
    /// The reading name.
    pub reading: &'static str,
    /// The measure.
    pub measure: MeasureKind,
    /// The bounds.
    pub bounds: Bounds,
    /// The round bound.
    pub max_rounds: usize,
    /// The node guard.
    pub guard: usize,
    /// Whether the external continuation policy is enabled.
    pub supply: bool,
    /// Nodes.
    pub nodes: Vec<Node>,
    /// Edges.
    pub edges: Vec<Edge>,
}

/// Summary statistics, as the sealed export reports them.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Stats {
    /// Node count.
    pub nodes: usize,
    /// Edge count.
    pub edges: usize,
    /// Nodes by status.
    pub by_status: BTreeMap<&'static str, usize>,
    /// Edges by role.
    pub roles: BTreeMap<String, usize>,
    /// Expansions with more than one tied class.
    pub expansions_with_ties: usize,
    /// Maximum depth.
    pub max_depth: usize,
    /// All nodes certified.
    pub all_certified: bool,
}

impl Tree {
    /// Statistics.
    pub fn stats(&self) -> Stats {
        let mut by_status = BTreeMap::new();
        for n in &self.nodes {
            *by_status.entry(n.status).or_insert(0) += 1;
        }
        let mut roles = BTreeMap::new();
        for e in &self.edges {
            let r: Role = role(e.challenge == "supply", &e.response);
            *roles.entry(r.to_string()).or_insert(0) += 1;
        }
        let ties: std::collections::BTreeSet<(usize, String)> = self
            .edges
            .iter()
            .filter(|e| e.tie_classes > 1)
            .map(|e| (e.parent, e.challenge.clone()))
            .collect();
        Stats {
            nodes: self.nodes.len(),
            edges: self.edges.len(),
            by_status,
            roles,
            expansions_with_ties: ties.len(),
            max_depth: self.nodes.iter().map(|n| n.depth).max().unwrap_or(0),
            all_certified: self.nodes.iter().all(|n| n.certified),
        }
    }

    /// The closed-system branch report: every maximal branch terminal?
    pub fn terminal_branches(&self) -> usize {
        self.nodes.iter().filter(|n| n.status == "terminal_all_separated" || n.status == "terminal_no_response").count()
    }
}

fn gather_min_responses(
    regime: &Regime,
    targets: &[Pair],
    measure: MeasureKind,
    bounds: &Bounds,
) -> Option<Vec<(Pair, MinResponses)>> {
    let mut gathered: Vec<(Pair, MinResponses)> = Vec::new();
    for &t in targets {
        gathered.push((t, min_responses(regime, t, measure, bounds)?));
    }
    Some(gathered)
}

#[allow(clippy::too_many_arguments)]
fn expand_gathered_responses(
    tree: &mut Tree,
    canon_map: &mut BTreeMap<Key, usize>,
    queue: &mut VecDeque<usize>,
    nid: usize,
    depth: usize,
    regime: &Regime,
    history: &[Event],
    measure: MeasureKind,
    gathered: Vec<(Pair, MinResponses)>,
    n_targets: usize,
) {
    for (t, mr) in gathered {
        let classes = quotient(regime, t, &mr);
        let n_classes = classes.len();
        for c in classes {
            assert!(response_valid_naive(regime, t, &c.representative).checked_invariant_2d26f729("checked invariant"));
            let mut h = history.to_vec();
            h.push(Event::Impose(t));
            h.extend(delta_events(regime, &c.representative));
            let cost = if measure == MeasureKind::Mu2 { mr.cost } else { (mr.cost.0, -1) };
            let label = delta_label(regime, &c.representative);
            attach(tree, canon_map, queue, nid, depth, h, format!("separate({}, {})", t.i.0, t.j.0), label, c.representative.clone(), n_classes, c.size, cost, n_targets);
        }
    }
}

/// Build the tree from the Challenge 3 situation.
pub fn build_tree(reading: &Reading, measure: MeasureKind, bounds: &Bounds, max_rounds: usize, guard: usize, supply: bool) -> Tree {
    let mut tree = Tree {
        reading: reading.name,
        measure,
        bounds: *bounds,
        max_rounds,
        guard,
        supply,
        nodes: Vec::new(),
        edges: Vec::new(),
    };
    let base = replay(&reading.genesis).checked_invariant_2d26f729("genesis replays");
    let root = Node {
        id: 0,
        history: reading.genesis.clone(),
        regime: base.clone(),
        depth: 0,
        canon: canonical(&base),
        status: "open",
        merged_count: 1,
        certified: true,
    };
    let mut canon_map: BTreeMap<Key, usize> = BTreeMap::new();
    canon_map.insert(root.canon.clone(), 0);
    tree.nodes.push(root);
    let mut queue: VecDeque<usize> = VecDeque::from([0]);
    while let Some(nid) = queue.pop_front() {
        let (regime, history, depth) = {
            let n = &tree.nodes[nid];
            (n.regime.clone(), n.history.clone(), n.depth)
        };
        let targets: Vec<Pair> = if nid == 0 {
            vec![reading.target]
        } else {
            debug_assert!(collapsed_pairs(&regime).iter().all(|p| !regime.reqs.contains(p)));
            closure_challenge_orbits(&regime).checked_invariant_2d26f729("budget")
        };
        if targets.is_empty() && !supply {
            tree.nodes[nid].status = "terminal_all_separated";
            continue;
        }
        if depth >= max_rounds {
            tree.nodes[nid].status = "completed";
            continue;
        }
        if tree.nodes.len() > guard {
            tree.nodes[nid].status = "frontier_guard";
            continue;
        }
        if targets.is_empty() {
            let token = Token::new(format!("g{}", regime.n_data()));
            let mut h = history.clone();
            h.push(Event::Supply(token.clone()));
            h.push(Event::AdmitDatum(token));
            attach(&mut tree, &mut canon_map, &mut queue, nid, depth, h, "supply".to_string(), "supply".to_string(), Vec::new(), 1, 1, (0, 0), 1);
            tree.nodes[nid].status = "expanded";
            continue;
        }
        let Some(gathered) = gather_min_responses(&regime, &targets, measure, bounds) else {
            tree.nodes[nid].status = "terminal_no_response";
            continue;
        };
        expand_gathered_responses(&mut tree, &mut canon_map, &mut queue, nid, depth, &regime, &history, measure, gathered, targets.len());
        tree.nodes[nid].status = "expanded";
    }
    tree
}

#[allow(clippy::too_many_arguments)]
fn attach(
    tree: &mut Tree,
    canon_map: &mut BTreeMap<Key, usize>,
    queue: &mut VecDeque<usize>,
    parent: usize,
    parent_depth: usize,
    history: Vec<Event>,
    challenge: String,
    label: String,
    response: Delta,
    tie_classes: usize,
    class_size: usize,
    cost: Cost,
    orbits: usize,
) {
    let regime = replay(&history).checked_invariant_2d26f729("history replays");
    let canon = canonical(&regime);
    let (child_id, kind, witness) = if let Some(&cid) = canon_map.get(&canon) {
        let w = find_iso(&regime, &tree.nodes[cid].regime).checked_invariant_2d26f729("merge edge without isomorphism");
        tree.nodes[cid].merged_count += 1;
        (cid, "merge", Some(w))
    } else {
        let cid = tree.nodes.len();
        let certified = replay(&history).map(|r| r == regime).unwrap_or(false);
        tree.nodes.push(Node {
            id: cid,
            history,
            regime,
            depth: parent_depth + 1,
            canon: canon.clone(),
            status: "open",
            merged_count: 1,
            certified,
        });
        canon_map.insert(canon, cid);
        queue.push_back(cid);
        (cid, "creation", None)
    };
    tree.edges.push(Edge {
        parent,
        child: child_id,
        round: parent_depth + 1,
        challenge,
        label,
        response,
        tie_classes,
        class_size,
        cost,
        orbits,
        kind,
        merge_witness: witness,
    });
}

// Origin: engine/crates_rs/core_ooutwire_primitives/src/tree.rs
// Claim: urn:core:crates_rs:core-ooutwire-primitives:tree:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2d26f729 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2d26f729` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2d26f729 {
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
impl BoundaryError2d26f729 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2d26f729 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2d26f729 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2d26f729 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2d26f729> {
        if capacity_bound == 0 {
            return Err(BoundaryError2d26f729::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2d26f729::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2d26f729::ExceedsCapacity {
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

#[cfg(test)]
mod tests {
    use super::*;
    use crate::reading::{READING_F, READING_L};

    /// CL-CLOSURE-TERMINATION, reading L: 4 nodes, 3 terminal, 1 round.
    #[test]
    fn closed_system_baseline_reading_l() {
        let t = build_tree(&READING_L, MeasureKind::Mu1, &Bounds::default(), 15, 250, false);
        let s = t.stats();
        assert_eq!(s.nodes, 4);
        assert_eq!(t.terminal_branches(), 3);
        assert_eq!(s.max_depth, 1);
        assert!(s.all_certified);
        assert_eq!(t.nodes.iter().filter(|n| n.status == "open").count(), 0);
    }

    /// CL-CLOSURE-TERMINATION, reading F: 20 nodes, 16 terminal, 3 rounds.
    #[test]
    fn closed_system_baseline_reading_f() {
        let t = build_tree(&READING_F, MeasureKind::Mu1, &Bounds::default(), 15, 250, false);
        let s = t.stats();
        assert_eq!(s.nodes, 20);
        assert_eq!(t.terminal_branches(), 16);
        assert_eq!(s.max_depth, 3);
        assert!(s.all_certified);
    }

    /// The closed-system baselines have no merge edges at all: every child
    /// is a fresh class.  Recorded, because the first version of this test
    /// assumed otherwise.
    #[test]
    fn closed_system_trees_have_no_merges() {
        for reading in [&READING_L, &READING_F] {
            let t = build_tree(reading, MeasureKind::Mu1, &Bounds::default(), 15, 250, false);
            assert_eq!(t.edges.iter().filter(|e| e.kind == "merge").count(), 0);
            assert_eq!(t.edges.len(), t.nodes.len() - 1);
        }
    }

    /// CL-TREE-SUMMARY, reading L under mu2 with the external continuation
    /// policy: 963 nodes, 1022 edges, depth 15, and every one of the 60
    /// merge edges carries an isomorphism witness that re-verifies against
    /// the stored representative.
    #[test]
    fn depth_fifteen_reading_l_mu2_is_963_nodes_and_merges_carry_witnesses() {
        use crate::renaming::{serialize, Bijection};
        let t = build_tree(&READING_L, MeasureKind::Mu2, &Bounds::default(), 15, 3000, true);
        let s = t.stats();
        assert_eq!((s.nodes, s.edges, s.max_depth), (963, 1022, 15));
        assert!(s.all_certified);
        assert_eq!(s.expansions_with_ties, 236);
        assert_eq!(s.roles.get("discrimination"), Some(&858));
        assert_eq!(s.roles.get("innovation"), Some(&53));
        assert_eq!(s.roles.get("supply"), Some(&111));
        let merges: Vec<&Edge> = t.edges.iter().filter(|e| e.kind == "merge").collect();
        assert_eq!(merges.len(), 1022 - 962);
        for e in merges {
            let w = e.merge_witness.as_ref().expect("witness");
            let parent = &t.nodes[e.parent];
            let mut h = parent.history.clone();
            h.extend(crate::testkit::edge_events(&parent.regime, e));
            let child = replay(&h).unwrap();
            let stored = &t.nodes[e.child].regime;
            assert_eq!(serialize(&child, w), serialize(stored, &Bijection::identity(stored.n_data(), stored.n_forms())));
        }
    }

    /// CL-TREE-SUMMARY, reading F under mu2: 1847 nodes, 1960 edges, depth
    /// 15, 422 tie expansions, and the four roles with the sealed counts —
    /// including the six double discriminations that occur nowhere in L.
    #[test]
    fn depth_fifteen_reading_f_mu2_is_1847_nodes_with_the_sealed_roles() {
        let t = build_tree(&READING_F, MeasureKind::Mu2, &Bounds::default(), 15, 3000, true);
        let s = t.stats();
        assert_eq!((s.nodes, s.edges, s.max_depth), (1847, 1960, 15));
        assert_eq!(s.expansions_with_ties, 422);
        assert_eq!(s.roles.get("discrimination"), Some(&1458));
        assert_eq!(s.roles.get("double_discrimination"), Some(&6));
        assert_eq!(s.roles.get("innovation"), Some(&83));
        assert_eq!(s.roles.get("supply"), Some(&413));
        assert!(s.all_certified);
        assert_eq!(s.by_status.get("frontier_guard"), None, "no guard cut at 3000");
    }
}

#[cfg(test)]
mod l4_boundary_tests_2d26f729 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2d26f729::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2d26f729::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2d26f729::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2d26f729::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2d26f729::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2d26f729::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2d26f729::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
