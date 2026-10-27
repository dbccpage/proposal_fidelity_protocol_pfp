//! d=2 mandatory fixed-R1 arena on D={-1,0,1}, X0=D^2, with no fallback.
//! Sol has count 1, winning strategies from the initial state number 0,
//! and the restored two-transport arena has value 6. Witness (1, 0, 6).
//! WDP-CHS-N03: this check does not prove A1 or A3 and does not close WDP-CHS-O02.
//! No continuum limit is claimed.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Rat {
    n: i64,
    d: i64,
}

impl Rat {
    fn new(n: i64, d: i64) -> Self {
        assert!(d != 0, "zero denominator");
        let (mut n, mut d) = (n, d);
        if d < 0 {
            n = -n;
            d = -d;
        }
        let g = gcd(n.abs(), d);
        Self { n: n / g, d: d / g }
    }

    fn add(self, other: Self) -> Self {
        Self::new(self.n * other.d + other.n * self.d, self.d * other.d)
    }
}

impl PartialOrd for Rat {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Rat {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        let left = i128::from(self.n) * i128::from(other.d);
        let right = i128::from(other.n) * i128::from(self.d);
        left.cmp(&right)
    }
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a.abs()
}

fn price_proposal() -> Rat { Rat::new(1, 1) }
fn price_check() -> Rat { Rat::new(2, 1) }
fn price_emit() -> Rat { Rat::new(1, 1) }
fn price_guard() -> Rat { Rat::new(1, 2) }
fn price_transport() -> Rat { Rat::new(1, 1) }
fn price_draw() -> Rat { Rat::new(1, 1) }
fn price_installation() -> Rat { Rat::new(3, 1) }

type Pair = (i64, i64);

fn domain() -> [i64; 3] { [-1, 0, 1] }

fn f01(p: Pair) -> Pair { (p.0 + p.1, p.0 - p.1) }
fn f12(p: Pair) -> Pair { (p.0, p.1 + p.0) }
fn g21(p: Pair) -> Pair { (p.0, p.1 - p.0) }

fn g10_int(p: Pair) -> Pair {
    let (u, v) = p;
    assert_eq!((u + v) % 2, 0, "image numerator is even");
    assert_eq!((u - v) % 2, 0, "image numerator is even");
    ((u + v) / 2, (u - v) / 2)
}

fn g10_rat(u: i64, v: i64) -> (Rat, Rat) {
    (Rat::new(u + v, 2), Rat::new(u - v, 2))
}

fn h_image(r: i64, t: i64) -> Pair {
    assert_eq!(t % 2, 0, "level-2 image coordinate is even");
    (t / 2, r - t / 2)
}

fn x0() -> [Pair; 9] {
    let d = domain();
    let mut out = [(0, 0); 9];
    let mut k = 0;
    for x in d {
        for y in d {
            out[k] = (x, y);
            k += 1;
        }
    }
    assert_eq!(k, 9);
    out
}

fn carrier(level: usize) -> [Pair; 9] {
    let base = x0();
    let mut out = [(0, 0); 9];
    match level {
        0 => base,
        1 => {
            for i in 0..9 { out[i] = f01(base[i]); }
            out
        }
        2 => {
            for i in 0..9 { out[i] = f12(f01(base[i])); }
            out
        }
        _ => panic!("level outside 0..=2"),
    }
}

fn on_carrier(level: usize, p: Pair) -> bool {
    carrier(level).contains(&p)
}

fn decode(level: usize, p: Pair) -> Pair {
    assert!(on_carrier(level, p), "candidate outside the declared image carrier");
    match level {
        0 => p,
        1 => g10_int(p),
        2 => {
            let back = g21(p);
            let decoded = g10_int(back);
            assert_eq!(decoded, h_image(p.0, p.1));
            decoded
        }
        _ => panic!("level outside 0..=2"),
    }
}

fn valid(level: usize, task: i64, p: Pair) -> bool {
    if !on_carrier(level, p) {
        return false;
    }
    match level {
        0 => p.0 + p.1 == task,
        1 | 2 => p.0 == task,
        _ => panic!("level outside 0..=2"),
    }
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Guard { None, FixedR1, Parameterized }

fn source(level: usize, p: Pair) -> Pair {
    match level {
        0 => f01(p),
        1 => p,
        2 => g21(p),
        _ => panic!("level outside 0..=2"),
    }
}

fn rejects(level: usize, task: i64, p: Pair, guard: Guard) -> bool {
    match guard {
        Guard::None => false,
        Guard::FixedR1 => source(level, p).0 != 1,
        Guard::Parameterized => source(level, p).0 != task,
    }
}

fn widened_sum_checker(task: i64, p: Pair) -> bool {
    let sum = p.0 + p.1;
    sum == task || sum == task - 1
}

fn solution_count(task: i64) -> i64 {
    x0().iter().filter(|p| p.0 + p.1 == task).count() as i64
}

fn check_table() {
    let rows = [
        ((-1, -1), (-2, 0), (-2, -2)),
        ((-1, 0), (-1, -1), (-1, -2)),
        ((-1, 1), (0, -2), (0, -2)),
        ((0, -1), (-1, 1), (-1, 0)),
        ((0, 0), (0, 0), (0, 0)),
        ((0, 1), (1, -1), (1, 0)),
        ((1, -1), (0, 2), (0, 2)),
        ((1, 0), (1, 1), (1, 2)),
        ((1, 1), (2, 0), (2, 2)),
    ];
    let (c0, c1, c2) = (carrier(0), carrier(1), carrier(2));
    assert_eq!(domain(), [-1, 0, 1]);
    assert_eq!(c0.len(), 9);
    for i in 0..9 {
        assert_eq!((c0[i], c1[i], c2[i]), rows[i]);
        assert_eq!(decode(1, c1[i]), c0[i]);
        assert_eq!(decode(2, c2[i]), c0[i]);
        assert_eq!(f12(f01(c0[i])), c2[i]);
        assert_eq!(h_image(c2[i].0, c2[i].1), c0[i]);
    }
    for i in 0..9 {
        for j in (i + 1)..9 {
            assert_ne!(c0[i], c0[j]);
            assert_ne!(c1[i], c1[j]);
            assert_ne!(c2[i], c2[j]);
        }
    }
    assert!(!on_carrier(1, (1, 0)));
    assert!(on_carrier(2, (1, 0)));
    assert_eq!(g10_rat(1, 0), (Rat::new(1, 2), Rat::new(1, 2)));
    assert!(!on_carrier(0, (0, 0)) || decode(2, (1, 0)) == (0, 1));
    assert_eq!(decode(2, (1, 0)), (0, 1));
    assert_eq!(solution_count(-1), 2);
    assert_eq!(solution_count(0), 3);
    assert_eq!(solution_count(1), 2);
    assert_eq!(solution_count(2), 1);
    assert_eq!(
        x0().iter().filter(|p| p.0 + p.1 == 2).copied().collect::<Vec<_>>(),
        vec![(1, 1)]
    );
    let level1: Vec<_> = c1.into_iter().filter(|p| valid(1, 2, *p)).collect();
    let level2: Vec<_> = c2.into_iter().filter(|p| valid(2, 2, *p)).collect();
    assert_eq!(level1, vec![(2, 0)]);
    assert_eq!(level2, vec![(2, 2)]);
    assert!(rejects(1, 2, (2, 0), Guard::FixedR1));
    assert!(rejects(2, 2, (2, 2), Guard::FixedR1));
    assert!(!rejects(1, 2, (2, 0), Guard::Parameterized));
    assert!(!rejects(2, 2, (2, 2), Guard::Parameterized));
    assert!(widened_sum_checker(1, (0, 0)));
    assert!(!valid(0, 1, (0, 0)));
}

struct Edge {
    cost: Rat,
    to: usize,
}

struct Node {
    target: bool,
    decoded: Option<Pair>,
    edges: Vec<Edge>,
}

struct Graph {
    nodes: Vec<Node>,
}

impl Graph {
    fn fresh(&mut self, target: bool, decoded: Option<Pair>) -> usize {
        let id = self.nodes.len();
        self.nodes.push(Node { target, decoded, edges: Vec::new() });
        id
    }

    fn finish_check(&mut self, root: usize, check_at: usize, level: usize, task: i64, pair: Pair) {
        if valid(level, task, pair) {
            let checked = self.fresh(false, None);
            self.nodes[check_at].edges.push(Edge { cost: price_check(), to: checked });
            let emitted = self.fresh(true, Some(decode(level, pair)));
            self.nodes[checked].edges.push(Edge { cost: price_emit(), to: emitted });
        } else {
            self.nodes[check_at].edges.push(Edge { cost: price_check(), to: root });
        }
    }

    fn add_menu(&mut self, root: usize, level: usize, task: i64, guard: Guard) {
        for pair in carrier(level) {
            let proposed = self.fresh(false, None);
            self.nodes[root].edges.push(Edge { cost: price_proposal(), to: proposed });
            if guard == Guard::None {
                self.finish_check(root, proposed, level, task, pair);
            } else {
                let guard_node = self.fresh(false, None);
                let dest = if rejects(level, task, pair, guard) { root } else { guard_node };
                self.nodes[proposed].edges.push(Edge { cost: price_guard(), to: dest });
                self.finish_check(root, guard_node, level, task, pair);
            }
        }
    }
}

fn arena(level: usize, task: i64, guard: Guard, original_route: bool) -> Graph {
    assert!(!original_route || level == 2, "fallback example starts at level 2");
    let mut graph = Graph { nodes: Vec::new() };
    let root = graph.fresh(false, None);
    assert_eq!(root, 0);
    graph.add_menu(root, level, task, guard);
    if original_route {
        let back1 = graph.fresh(false, None);
        let original = graph.fresh(false, None);
        graph.nodes[root].edges.push(Edge { cost: price_transport(), to: back1 });
        graph.nodes[back1].edges.push(Edge { cost: price_transport(), to: original });
        graph.add_menu(original, 0, task, Guard::None);
    }
    graph
}

fn emittable(graph: &Graph) -> Vec<Pair> {
    let mut seen = vec![false; graph.nodes.len()];
    let mut stack = vec![0usize];
    seen[0] = true;
    let mut out = Vec::new();
    while let Some(at) = stack.pop() {
        if graph.nodes[at].target {
            out.push(graph.nodes[at].decoded.expect("target decodes an original"));
        }
        for edge in &graph.nodes[at].edges {
            if !seen[edge.to] {
                seen[edge.to] = true;
                stack.push(edge.to);
            }
        }
    }
    out.sort_unstable();
    out.dedup();
    out
}

fn winning(graph: &Graph) -> Vec<bool> {
    let n = graph.nodes.len();
    let mut win = vec![false; n];
    for (i, node) in graph.nodes.iter().enumerate() {
        if node.target {
            win[i] = true;
        }
    }
    let mut changed = true;
    while changed {
        changed = false;
        for i in 0..n {
            if win[i] {
                continue;
            }
            let forced = graph.nodes[i].edges.iter().any(|edge| win[edge.to]);
            if forced {
                win[i] = true;
                changed = true;
            }
        }
    }
    win
}

fn loss_trap_contains_initial(graph: &Graph, win: &[bool]) -> bool {
    if win[0] || graph.nodes[0].target {
        return false;
    }
    let mut seen = vec![false; graph.nodes.len()];
    let mut stack = vec![0usize];
    seen[0] = true;
    while let Some(at) = stack.pop() {
        if win[at] || graph.nodes[at].target {
            return false;
        }
        for edge in &graph.nodes[at].edges {
            if win[edge.to] {
                return false;
            }
            if !seen[edge.to] {
                seen[edge.to] = true;
                stack.push(edge.to);
            }
        }
    }
    true
}

fn relax_node_edges(graph: &Graph, dist: &mut [Option<Rat>], i: usize) -> bool {
    if graph.nodes[i].target {
        return false;
    }
    let mut changed = false;
    for edge in &graph.nodes[i].edges {
        if let Some(succ) = dist[edge.to] {
            let cand = edge.cost.add(succ);
            if dist[i].map_or(true, |have| cand < have) {
                dist[i] = Some(cand);
                changed = true;
            }
        }
    }
    changed
}

fn minimum_success_cost(graph: &Graph) -> Option<Rat> {
    let n = graph.nodes.len();
    let mut dist = vec![None; n];
    for (i, node) in graph.nodes.iter().enumerate() {
        if node.target {
            dist[i] = Some(Rat::new(0, 1));
        }
    }
    for _ in 0..n {
        let mut changed = false;
        for i in 0..n {
            changed |= relax_node_edges(graph, &mut dist, i);
        }
        if !changed {
            break;
        }
    }
    dist[0]
}

fn forced_reaches_target(graph: &Graph, start: usize) -> bool {
    let mut at = start;
    let mut seen = vec![false; graph.nodes.len()];
    loop {
        if graph.nodes[at].target {
            return true;
        }
        if seen[at] || graph.nodes[at].edges.len() != 1 {
            return false;
        }
        seen[at] = true;
        at = graph.nodes[at].edges[0].to;
    }
}

fn no_fallback_strategy_count() -> i64 {
    let graph = arena(2, 2, Guard::FixedR1, false);
    assert_eq!(graph.nodes[0].edges.len(), 9);
    let win = winning(&graph);
    assert!(loss_trap_contains_initial(&graph, &win));
    assert!(emittable(&graph).is_empty());
    assert!(minimum_success_cost(&graph).is_none());
    let mut successes = 0i64;
    for edge in &graph.nodes[0].edges {
        if forced_reaches_target(&graph, edge.to) {
            successes += 1;
        }
    }
    let level1 = arena(1, 2, Guard::FixedR1, false);
    assert!(emittable(&level1).is_empty());
    assert!(minimum_success_cost(&level1).is_none());
    successes
}

fn restored_value() -> Rat {
    let graph = arena(2, 2, Guard::FixedR1, true);
    assert_eq!(graph.nodes[0].edges.len(), 10);
    let value = minimum_success_cost(&graph).expect("two-transport route reaches a target");
    let manual = price_transport()
        .add(price_transport())
        .add(price_proposal())
        .add(price_check())
        .add(price_emit());
    assert_eq!(value, manual);
    assert_eq!(emittable(&graph), vec![(1, 1)]);
    value
}

fn named_proposal_value() -> Rat {
    let graph = arena(0, 2, Guard::None, false);
    let value = minimum_success_cost(&graph).expect("unguarded original proposal emits");
    assert_eq!(value, price_proposal().add(price_check()).add(price_emit()));
    assert_eq!(emittable(&graph), vec![(1, 1)]);
    value
}

fn guarded_operating() -> Rat {
    let graph = arena(0, 2, Guard::Parameterized, false);
    let value = minimum_success_cost(&graph).expect("parameterized guard keeps (1,1)");
    let manual = price_proposal().add(price_guard()).add(price_check()).add(price_emit());
    assert_eq!(value, manual);
    assert_eq!(emittable(&graph), vec![(1, 1)]);
    value
}

fn guarded_with_setup() -> Rat {
    guarded_operating().add(price_installation())
}

fn scan_step_costs(guarded: bool) -> (Rat, Rat, Rat) {
    let base = if guarded {
        price_draw().add(price_guard()).add(price_check())
    } else {
        price_draw().add(price_check())
    };
    (base.add(price_emit()), base, price_draw().add(price_guard()))
}

fn update_scan_dp_cell(dp: &mut [[Rat; 10]; 10], b: i64, r: i64, costs: (Rat, Rat, Rat)) {
    let (good, bad_step, reject_step) = costs;
    let mut best = good;
    if b > 0 {
        best = best.max(bad_step.add(dp[(b - 1) as usize][r as usize]));
    }
    if r > 0 {
        best = best.max(reject_step.add(dp[b as usize][(r - 1) as usize]));
    }
    dp[b as usize][r as usize] = best;
}

fn scan_operating(valid_count: i64, rejected: i64, guarded: bool) -> Rat {
    assert!((1..=9).contains(&valid_count));
    assert!((0..=(9 - valid_count)).contains(&rejected));
    if rejected > 0 {
        assert!(guarded, "rejection without a guard is not this scan");
    }
    let bad = 9 - valid_count - rejected;
    let costs = scan_step_costs(guarded);
    let mut dp = [[Rat::new(0, 1); 10]; 10];
    for total in 0..=(bad + rejected) {
        for b in 0..=bad {
            let r = total - b;
            if (0..=rejected).contains(&r) {
                update_scan_dp_cell(&mut dp, b, r, costs);
            }
        }
    }
    dp[bad as usize][rejected as usize]
}

fn maximal_scan_operating() -> Rat {
    let valid_count = solution_count(2);
    scan_operating(valid_count, 9 - valid_count, true)
}

fn scan_with_setup() -> Rat {
    maximal_scan_operating().add(price_installation())
}

fn bare_scan() -> Rat {
    scan_operating(solution_count(2), 0, false)
}

fn ledger_total() -> Rat {
    let charges = [
        price_proposal(), price_check(), price_emit(),
        Rat::new(1, 1), Rat::new(1, 1), Rat::new(1, 1),
        price_transport(),
        price_proposal(), price_guard(), price_check(), price_emit(),
        price_proposal(), price_guard(), price_check(), price_emit(),
    ];
    assert_eq!(charges.len(), 15);
    let mut spent = Rat::new(0, 1);
    for charge in charges {
        assert!(charge > Rat::new(0, 1));
        let next = spent.add(charge);
        assert!(next <= Rat::new(18, 1), "shared budget exhausted");
        spent = next;
    }
    spent
}

/// `(original solutions, no-fallback winning strategies, restored two-transport value)`.
pub fn witness() -> (i64, i64, i64) {
    check_table();
    let solutions = solution_count(2);
    assert_eq!(solutions, 1);
    let strategies = no_fallback_strategy_count();
    assert_eq!(strategies, 0);
    let restored = restored_value();
    assert_eq!(restored, Rat::new(6, 1));
    (solutions, strategies, restored.n)
}

/// Refuse a claimed no-fallback strategy count taken from another menu or run.
pub fn refuse_foreign_strategy_count(num: i64, den: i64) -> Result<(), &'static str> {
    let claimed = Rat::new(num, den);
    let strategies = Rat::new(witness().1, 1);
    if claimed == strategies {
        return Ok(());
    }
    let foreign = [
        named_proposal_value(),
        guarded_operating(),
        guarded_with_setup(),
        maximal_scan_operating(),
        scan_with_setup(),
        bare_scan(),
        ledger_total(),
        restored_value(),
        Rat::new(solution_count(1), 1),
        Rat::new(solution_count(-1), 1),
        Rat::new(solution_count(0), 1),
    ];
    if foreign.contains(&claimed) {
        Err("refused: other menu, run, or task count is not the no-fallback winning-strategy count")
    } else {
        Err("refused: not the no-fallback winning-strategy count")
    }
}

/// A1-A3 stay assumptions. WDP-CHS-N03 forbids reading this check as their proof.
pub fn refuse_assumption_discharge() -> Result<(), &'static str> {
    let (solutions, strategies, restored) = witness();
    let empty_emitted_omits_solution = solutions == 1 && strategies == 0;
    let widened_is_not_the_predicate = widened_sum_checker(1, (0, 0)) && !valid(0, 1, (0, 0));
    let restored_is_another_arena = restored == 6 && strategies == 0;
    if empty_emitted_omits_solution && widened_is_not_the_predicate && restored_is_another_arena {
        Err("refused: declaring A1-A3 does not discharge soundness, completeness, or winning-strategy coverage")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_chs_o02.rs
// Claim: urn:core:crates_rs:tests:wdp-chs-o02:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord4590abbc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord4590abbc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError4590abbc {
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
impl BoundaryError4590abbc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError4590abbc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError4590abbc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord4590abbc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError4590abbc> {
        if capacity_bound == 0 {
            return Err(BoundaryError4590abbc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError4590abbc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError4590abbc::ExceedsCapacity {
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
        bare_scan, guarded_operating, guarded_with_setup, ledger_total, maximal_scan_operating,
        named_proposal_value, refuse_assumption_discharge, refuse_foreign_strategy_count,
        restored_value, scan_with_setup, solution_count, valid, widened_sum_checker, witness,
        Rat,
    };

    #[test]
    fn witness_is_one_zero_six() {
        assert_eq!(witness(), (1, 0, 6));
        assert_eq!(solution_count(2), 1);
        assert_ne!(solution_count(2), solution_count(1));
        assert_eq!(named_proposal_value(), Rat::new(4, 1));
        assert_eq!(guarded_operating(), Rat::new(9, 2));
        assert_eq!(guarded_with_setup(), Rat::new(15, 2));
        assert_eq!(maximal_scan_operating(), Rat::new(33, 2));
        assert_eq!(scan_with_setup(), Rat::new(39, 2));
        assert!(scan_with_setup() > Rat::new(18, 1));
        assert_eq!(bare_scan(), Rat::new(28, 1));
        assert_eq!(ledger_total(), Rat::new(17, 1));
        assert_eq!(restored_value(), Rat::new(6, 1));
        assert_ne!(restored_value(), named_proposal_value());
        assert_ne!(Rat::new(witness().1, 1), restored_value());
    }

    #[test]
    fn refuses_other_menus_and_assumption_labels() {
        assert!(refuse_foreign_strategy_count(4, 1).is_err());
        assert!(refuse_foreign_strategy_count(9, 2).is_err());
        assert!(refuse_foreign_strategy_count(15, 2).is_err());
        assert!(refuse_foreign_strategy_count(33, 2).is_err());
        assert!(refuse_foreign_strategy_count(39, 2).is_err());
        assert!(refuse_foreign_strategy_count(28, 1).is_err());
        assert!(refuse_foreign_strategy_count(17, 1).is_err());
        assert!(refuse_foreign_strategy_count(6, 1).is_err());
        assert!(refuse_foreign_strategy_count(2, 1).is_err());
        assert!(refuse_foreign_strategy_count(3, 1).is_err());
        assert!(refuse_foreign_strategy_count(15, 4).is_err());
        assert!(refuse_foreign_strategy_count(29771, 1).is_err());
        assert!(refuse_foreign_strategy_count(0, 1).is_ok());
        assert!(refuse_assumption_discharge().is_err());
        assert!(widened_sum_checker(1, (0, 0)));
        assert!(!valid(0, 1, (0, 0)));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_4590abbc() {
    let admitted = BoundaryRecord4590abbc::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord4590abbc::try_admit(9, 8).is_err());
}
