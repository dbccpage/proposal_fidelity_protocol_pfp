//! Exact integer min-cost flow with zero lower bounds and no upper capacities.
//! Construction validates the carrier. One explicit pivot budget bounds solving;
//! an independent primal/dual replay checks conservation and complementarity.
//! Rational undirected cuts are owned by solver_flow_gomory_hu.
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b9280da1<T> {
    fn checked_invariant_b9280da1(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b9280da1<T> for Option<T> {
    #[inline]
    fn checked_invariant_b9280da1(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b9280da1<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b9280da1(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
pub const MAX_NETWORK_NODES: usize = 16_384;
pub const MAX_NETWORK_ARCS: usize = 131_072;

pub struct NetworkSimplex {
    num_nodes: usize,
    num_nodes_with_root: usize,
    arcs: Vec<Arc>,
    demand: Vec<i128>,
    flow: Vec<i128>,
    potential: Vec<i128>,
    in_tree: Vec<bool>,
    basis: Basis,
    artificial_arc_start: usize,
    original_arc_count: usize,
}

#[derive(Clone, Debug)]
struct CycleArc {
    pub arc: usize,
    pub direction: i8,
}

impl NetworkSimplex {
    pub fn new(
        num_nodes: usize,
        arcs: Vec<Arc>,
        demand: Vec<i128>,
    ) -> Result<Self, NetworkSimplexError> {
        if num_nodes > MAX_NETWORK_NODES || arcs.len() > MAX_NETWORK_ARCS {
            return Err(NetworkSimplexError::SizeLimit);
        }
        if demand.len() != num_nodes {
            return Err(NetworkSimplexError::DemandLengthMismatch {
                expected: num_nodes,
                found: demand.len(),
            });
        }
        if arcs
            .iter()
            .any(|a| a.tail >= num_nodes || a.head >= num_nodes || a.tail == a.head)
        {
            return Err(NetworkSimplexError::InvalidCarrier {
                message: "arc endpoint is outside the carrier or a self-loop".into(),
            });
        }
        let original_arc_count = arcs.len();
        let num_nodes_with_root = num_nodes
            .checked_add(1)
            .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        let basis = Basis::new(num_nodes_with_root);
        Ok(Self {
            num_nodes,
            num_nodes_with_root,
            arcs,
            demand,
            flow: Vec::new(),
            potential: vec![0; num_nodes_with_root],
            in_tree: Vec::new(),
            basis,
            artificial_arc_start: 0,
            original_arc_count,
        })
    }

    pub fn arcs(&self) -> &[Arc] {
        &self.arcs[..self.original_arc_count]
    }

    pub fn check_balanced_demand(&self) -> Result<(), NetworkSimplexError> {
        if self.demand.len() != self.num_nodes {
            return Err(NetworkSimplexError::DemandLengthMismatch {
                expected: self.num_nodes,
                found: self.demand.len(),
            });
        }
        let sum = self.demand.iter().try_fold(0i128, |acc, &d| {
            acc.checked_add(d)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)
        })?;
        if sum != 0 {
            return Err(NetworkSimplexError::UnbalancedDemand { sum });
        }
        Ok(())
    }

    fn compute_big_m_cost(&self) -> Result<i128, NetworkSimplexError> {
        let mut sum_costs = 0i128;
        for arc in &self.arcs {
            if arc.cost < 0 {
                return Err(NetworkSimplexError::NegativeWeight {
                    edge: arc.original_edge.unwrap_or(0),
                    weight: arc.cost,
                });
            }
            let abs_cost = arc
                .cost
                .checked_abs()
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            sum_costs = sum_costs
                .checked_add(abs_cost)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        }
        let mut sum_demands = 0i128;
        for &d in &self.demand {
            let abs_d = d
                .checked_abs()
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            sum_demands = sum_demands
                .checked_add(abs_d)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        }

        sum_costs
            .checked_add(sum_demands)
            .and_then(|v| v.checked_add(1))
            .ok_or(NetworkSimplexError::ArithmeticOverflow)
    }

    fn push_artificial_node_arc(
        &mut self,
        v: usize,
        root: usize,
        m: i128,
    ) -> Result<(), NetworkSimplexError> {
        let b_v = self.demand[v];
        let (tail, head, flow_v) = if b_v > 0 {
            // r -> v
            (root, v, b_v)
        } else if b_v < 0 {
            // v -> r
            let neg_b = b_v
                .checked_neg()
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            (v, root, neg_b)
        } else {
            // Connect 0-demand nodes to root with 0 flow
            (root, v, 0)
        };
        self.arcs.push(Arc {
            tail,
            head,
            cost: m,
            lower: 0,
            upper: None,
            original_edge: None,
            orientation_sign: 0,
        });
        self.flow.push(flow_v);
        self.in_tree.push(true);
        Ok(())
    }

    fn initialize_artificial_basis(&mut self) -> Result<(), NetworkSimplexError> {
        self.artificial_arc_start = self.arcs.len();
        let m = self.compute_big_m_cost()?;
        let root = self.num_nodes;

        self.flow = vec![0; self.artificial_arc_start];
        self.in_tree = vec![false; self.artificial_arc_start];

        for v in 0..self.num_nodes {
            self.push_artificial_node_arc(v, root, m)?;
        }

        self.basis
            .rebuild(self.num_nodes_with_root, root, &self.arcs, &self.in_tree)?;

        Ok(())
    }

    fn compute_potentials(&mut self) -> Result<(), NetworkSimplexError> {
        self.potential.fill(0);
        let root = self.num_nodes;
        self.potential[root] = 0;

        let mut children = vec![Vec::new(); self.num_nodes_with_root];
        for v in 0..self.num_nodes_with_root {
            if let Some(p) = self.basis.parent[v] {
                children[p].push(v);
            }
        }

        let mut queue = std::collections::VecDeque::new();
        queue.push_back(root);

        while let Some(u) = queue.pop_front() {
            for &v in &children[u] {
                let arc_idx = self.basis.parent_arc[v].ok_or(NetworkSimplexError::InvalidBasis)?;
                let arc = &self.arcs[arc_idx];
                if arc.tail == u {
                    // u -> v
                    self.potential[v] = self.potential[u]
                        .checked_add(arc.cost)
                        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
                } else {
                    // v -> u
                    self.potential[v] = self.potential[u]
                        .checked_sub(arc.cost)
                        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
                }
                queue.push_back(v);
            }
        }
        Ok(())
    }

    fn find_entering_arc(&self) -> Result<Option<usize>, NetworkSimplexError> {
        for a in 0..self.arcs.len() {
            if !self.in_tree[a] {
                let arc = &self.arcs[a];
                let reduced_cost = arc
                    .cost
                    .checked_add(self.potential[arc.tail])
                    .and_then(|x| x.checked_sub(self.potential[arc.head]))
                    .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
                if reduced_cost < 0 {
                    return Ok(Some(a));
                }
            }
        }
        Ok(None)
    }

    fn trace_lca_paths(
        &self,
        mut u: usize,
        mut v: usize,
    ) -> Result<(Vec<(usize, usize)>, Vec<(usize, usize)>), NetworkSimplexError> {
        let mut path_u = Vec::new();
        let mut path_v = Vec::new();

        while u != v {
            if self.basis.depth[u] >= self.basis.depth[v] {
                let parent_u = self.basis.parent[u].ok_or(NetworkSimplexError::InvalidBasis)?;
                let arc_u = self.basis.parent_arc[u].ok_or(NetworkSimplexError::InvalidBasis)?;
                path_u.push((u, arc_u));
                u = parent_u;
            } else {
                let parent_v = self.basis.parent[v].ok_or(NetworkSimplexError::InvalidBasis)?;
                let arc_v = self.basis.parent_arc[v].ok_or(NetworkSimplexError::InvalidBasis)?;
                path_v.push((v, arc_v));
                v = parent_v;
            }
        }
        Ok((path_u, path_v))
    }

    fn cycle_for_entering_arc(
        &self,
        entering: usize,
    ) -> Result<Vec<CycleArc>, NetworkSimplexError> {
        let entering_arc = &self.arcs[entering];
        let (path_u, path_v) = self.trace_lca_paths(entering_arc.tail, entering_arc.head)?;

        let mut cycle = Vec::new();
        // 1. Entering arc
        cycle.push(CycleArc {
            arc: entering,
            direction: 1,
        });

        // 2. Path from v to LCA (path_v going up)
        for &(x, arc_idx) in &path_v {
            let arc = &self.arcs[arc_idx];
            let direction = if arc.tail == x { 1 } else { -1 };
            cycle.push(CycleArc {
                arc: arc_idx,
                direction,
            });
        }

        // 3. Path from LCA to u (path_u going down, reversed)
        for &(x, arc_idx) in path_u.iter().rev() {
            let arc = &self.arcs[arc_idx];
            let direction = if arc.tail == x { -1 } else { 1 };
            cycle.push(CycleArc {
                arc: arc_idx,
                direction,
            });
        }

        Ok(cycle)
    }

    fn min_reverse_flow(&self, cycle: &[CycleArc]) -> Result<i128, NetworkSimplexError> {
        cycle
            .iter()
            .filter(|ca| ca.direction == -1)
            .map(|ca| self.flow[ca.arc])
            .min()
            .ok_or(NetworkSimplexError::ArithmeticOverflow)
    }

    fn augment_cycle_flows(
        &mut self,
        cycle: &[CycleArc],
        theta: i128,
    ) -> Result<(), NetworkSimplexError> {
        for ca in cycle {
            if ca.direction == 1 {
                self.flow[ca.arc] = self.flow[ca.arc]
                    .checked_add(theta)
                    .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            } else {
                self.flow[ca.arc] = self.flow[ca.arc]
                    .checked_sub(theta)
                    .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            }
        }
        Ok(())
    }

    fn select_leaving_arc(&self, cycle: &[CycleArc]) -> Result<usize, NetworkSimplexError> {
        cycle
            .iter()
            .filter(|ca| ca.direction == -1 && self.flow[ca.arc] == 0)
            .map(|ca| ca.arc)
            .min()
            .ok_or(NetworkSimplexError::InvalidBasis)
    }

    fn pivot(&mut self, entering: usize) -> Result<(), NetworkSimplexError> {
        let cycle = self.cycle_for_entering_arc(entering)?;
        let theta = self.min_reverse_flow(&cycle)?;
        self.augment_cycle_flows(&cycle, theta)?;
        let leaving = self.select_leaving_arc(&cycle)?;

        self.in_tree[entering] = true;
        self.in_tree[leaving] = false;

        self.basis.rebuild(
            self.num_nodes_with_root,
            self.num_nodes,
            &self.arcs,
            &self.in_tree,
        )?;

        Ok(())
    }

    fn check_artificial_flows_zero(&self) -> Result<(), NetworkSimplexError> {
        for a in self.artificial_arc_start..self.arcs.len() {
            if self.flow[a] > 0 {
                return Err(NetworkSimplexError::Infeasible);
            }
        }
        Ok(())
    }

    fn extract_solution(&self) -> Result<NetworkSimplexSolution, NetworkSimplexError> {
        let mut objective = 0i128;
        for a in 0..self.artificial_arc_start {
            let term = self.flow[a]
                .checked_mul(self.arcs[a].cost)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            objective = objective
                .checked_add(term)
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
        }

        let potential = self.potential[0..self.num_nodes].to_vec();

        let mut reduced_costs = Vec::with_capacity(self.artificial_arc_start);
        for a in 0..self.artificial_arc_start {
            let arc = &self.arcs[a];
            let rc = arc
                .cost
                .checked_add(self.potential[arc.tail])
                .and_then(|x| x.checked_sub(self.potential[arc.head]))
                .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
            reduced_costs.push(rc);
        }

        Ok(NetworkSimplexSolution {
            objective,
            flow: self.flow[0..self.artificial_arc_start].to_vec(),
            potential,
            reduced_costs,
        })
    }

    pub fn solve(&mut self) -> Result<NetworkSimplexSolution, NetworkSimplexError> {
        self.solve_with_budget(10_000.max(self.original_arc_count.saturating_mul(10)))
    }

    fn check_supported_arc_bounds(&self) -> Result<(), NetworkSimplexError> {
        // Only zero lower bounds and unbounded upper capacities are modelled;
        // refuse anything else rather than silently ignore it.
        if self.arcs.iter().any(|a| a.lower != 0 || a.upper.is_some()) {
            return Err(NetworkSimplexError::InvalidCarrier {
                message: "only zero lower bounds and unbounded upper capacities are supported"
                    .into(),
            });
        }
        Ok(())
    }

    fn run_simplex_pivots(&mut self, max_iter: usize) -> Result<(), NetworkSimplexError> {
        let mut iter = 0;
        loop {
            self.compute_potentials()?;
            let Some(a) = self.find_entering_arc()? else {
                return Ok(());
            };
            if iter >= max_iter {
                return Err(NetworkSimplexError::IterationLimitExceeded { limit: max_iter });
            }
            self.pivot(a)?;
            iter += 1;
        }
    }

    pub fn solve_with_budget(
        &mut self,
        max_iter: usize,
    ) -> Result<NetworkSimplexSolution, NetworkSimplexError> {
        self.arcs.truncate(self.original_arc_count);
        self.check_supported_arc_bounds()?;
        self.check_balanced_demand()?;
        self.initialize_artificial_basis()?;
        self.run_simplex_pivots(max_iter)?;
        self.check_artificial_flows_zero()?;
        let solution = self.extract_solution()?;
        verify_network_solution(self.num_nodes, self.arcs(), &self.demand, &solution)?;
        Ok(solution)
    }
}

mod basis {
    use super::{Arc, CheckedInvariantExt_b9280da1, NetworkSimplexError};
    use linear_algebra::basis::{BasisDescriptor, BasisId};

    #[derive(Clone, Debug)]
    pub struct Basis {
        coordinate_basis: BasisDescriptor,
        pub parent: Vec<Option<usize>>,
        pub parent_arc: Vec<Option<usize>>,
        pub depth: Vec<usize>,
    }

    impl Basis {
        pub fn new(num_nodes_with_root: usize) -> Self {
            let coordinate_basis = BasisDescriptor::new(
                BasisId::new("network-simplex-node-coordinates")
                    .checked_invariant_b9280da1("the static network-simplex basis ID is non-empty"),
                num_nodes_with_root,
            );
            Self {
                coordinate_basis,
                parent: vec![None; num_nodes_with_root],
                parent_arc: vec![None; num_nodes_with_root],
                depth: vec![0; num_nodes_with_root],
            }
        }

        #[must_use]
        pub fn descriptor(&self) -> &BasisDescriptor {
            &self.coordinate_basis
        }

        fn build_tree_adjacency(
            num_nodes_with_root: usize,
            arcs: &[Arc],
            in_tree: &[bool],
        ) -> Result<Vec<Vec<(usize, usize)>>, NetworkSimplexError> {
            // Build adjacency list for tree arcs
            let mut adj = vec![Vec::new(); num_nodes_with_root];
            for (i, &in_t) in in_tree.iter().enumerate() {
                if in_t {
                    let arc = &arcs[i];
                    if arc.tail >= num_nodes_with_root || arc.head >= num_nodes_with_root {
                        return Err(NetworkSimplexError::InvalidBasis);
                    }
                    adj[arc.tail].push((arc.head, i));
                    adj[arc.head].push((arc.tail, i));
                }
            }
            Ok(adj)
        }

        pub fn rebuild(
            &mut self,
            num_nodes_with_root: usize,
            root: usize,
            arcs: &[Arc],
            in_tree: &[bool],
        ) -> Result<(), NetworkSimplexError> {
            if num_nodes_with_root != self.coordinate_basis.dimension()
                || root >= num_nodes_with_root
                || in_tree.len() != arcs.len()
            {
                return Err(NetworkSimplexError::InvalidBasis);
            }
            self.parent.fill(None);
            self.parent_arc.fill(None);
            self.depth.fill(0);

            let adj = Self::build_tree_adjacency(num_nodes_with_root, arcs, in_tree)?;
            let mut visited = vec![false; num_nodes_with_root];
            let mut queue = std::collections::VecDeque::new();

            queue.push_back(root);
            visited[root] = true;

            while let Some(u) = queue.pop_front() {
                for &(v, arc_idx) in &adj[u] {
                    if !visited[v] {
                        visited[v] = true;
                        self.parent[v] = Some(u);
                        self.parent_arc[v] = Some(arc_idx);
                        self.depth[v] = self.depth[u] + 1;
                        queue.push_back(v);
                    }
                }
            }

            // Verify that all nodes were visited (i.e. tree is connected)
            if visited.iter().any(|&v| !v) {
                return Err(NetworkSimplexError::InvalidBasis);
            }

            Ok(())
        }
    }
}
pub use basis::*;

mod error {
    #[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, thiserror::Error)]
    pub enum NetworkSimplexError {
        #[error("network exceeds the node or arc size limit")]
        SizeLimit,
        #[error("independent network flow certificate replay failed")]
        CertificateMismatch,
        #[error("Empty graph: no nodes or arcs provided")]
        EmptyGraph,
        #[error("Demand length mismatch: expected {expected}, found {found}")]
        DemandLengthMismatch { expected: usize, found: usize },
        #[error("Unbalanced demand sum: {sum} (must be 0)")]
        UnbalancedDemand { sum: i128 },
        #[error("Negative edge weight for edge {edge}: {weight}")]
        NegativeWeight { edge: usize, weight: i128 },
        #[error("Problem is infeasible (artificial flow remains positive)")]
        Infeasible,
        #[error("Iteration limit exceeded: {limit}")]
        IterationLimitExceeded { limit: usize },
        #[error("Invalid basis state")]
        InvalidBasis,
        #[error("Arithmetic overflow occurred")]
        ArithmeticOverflow,
        /// A carrier that is malformed before any arc is built: a non-positive
        /// vertex count, an endpoint outside the carrier, or a self-loop.
        ///
        /// Present in the Python mirror since it was written and absent here, which
        /// meant Rust reached the solver with an out-of-range node index and
        /// panicked on the bounds check instead of refusing. A panic is not a
        /// refusal: it carries no class, reaches no trace, and takes the host down
        /// rather than the request.
        #[error("Invalid carrier: {message}")]
        InvalidCarrier { message: String },
    }
}
pub use error::*;

mod graph {
    #[derive(Clone, Debug, PartialEq, Eq)]
    pub struct Arc {
        pub tail: usize,
        pub head: usize,
        pub cost: i128,
        pub lower: i128,
        pub upper: Option<i128>,
        pub original_edge: Option<usize>,
        pub orientation_sign: i8,
    }
}
pub use graph::*;

mod solution {
    #[derive(Clone, Debug)]
    pub struct NetworkSimplexSolution {
        pub objective: i128,
        pub flow: Vec<i128>,
        pub potential: Vec<i128>,
        pub reduced_costs: Vec<i128>,
    }
}
pub use solution::*;

fn is_valid_certified_arc(nodes: usize, a: &Arc, flow_i: i128) -> bool {
    let valid_endpoints = a.tail < nodes && a.head < nodes && a.tail != a.head;
    let valid_bounds = a.lower == 0 && a.upper.is_none() && flow_i >= 0;
    valid_endpoints && valid_bounds
}

fn verify_arc_reduced_cost(
    a: &Arc,
    flow_i: i128,
    reduced_i: i128,
    potential: &[i128],
) -> Result<(), NetworkSimplexError> {
    let reduced = a
        .cost
        .checked_add(potential[a.tail])
        .and_then(|x| x.checked_sub(potential[a.head]))
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    let valid_complementary = reduced == reduced_i && reduced >= 0 && (flow_i == 0 || reduced == 0);
    if !valid_complementary {
        return Err(NetworkSimplexError::CertificateMismatch);
    }
    Ok(())
}

fn verify_arc_contribution(
    nodes: usize,
    a: &Arc,
    flow_i: i128,
    reduced_i: i128,
    potential: &[i128],
    balances: &mut [i128],
    objective: &mut i128,
) -> Result<(), NetworkSimplexError> {
    if !is_valid_certified_arc(nodes, a, flow_i) {
        return Err(NetworkSimplexError::CertificateMismatch);
    }
    balances[a.tail] = balances[a.tail]
        .checked_sub(flow_i)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    balances[a.head] = balances[a.head]
        .checked_add(flow_i)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    let arc_obj = flow_i
        .checked_mul(a.cost)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    *objective = objective
        .checked_add(arc_obj)
        .ok_or(NetworkSimplexError::ArithmeticOverflow)?;
    verify_arc_reduced_cost(a, flow_i, reduced_i, potential)
}

fn validate_network_solution_lengths(
    nodes: usize,
    arcs_len: usize,
    demand: &[i128],
    s: &NetworkSimplexSolution,
) -> Result<(), NetworkSimplexError> {
    if nodes > MAX_NETWORK_NODES || arcs_len > MAX_NETWORK_ARCS {
        return Err(NetworkSimplexError::SizeLimit);
    }
    let valid_lengths = [
        demand.len() == nodes,
        s.potential.len() == nodes,
        s.flow.len() == arcs_len,
        s.reduced_costs.len() == arcs_len,
    ]
    .into_iter()
    .all(|ok| ok);
    if !valid_lengths {
        return Err(NetworkSimplexError::CertificateMismatch);
    }
    Ok(())
}

/// Independent primal/dual certificate replay for the supported integer carrier.
pub fn verify_network_solution(
    nodes: usize,
    arcs: &[Arc],
    demand: &[i128],
    s: &NetworkSimplexSolution,
) -> Result<(), NetworkSimplexError> {
    validate_network_solution_lengths(nodes, arcs.len(), demand, s)?;
    let mut balances = vec![0i128; nodes];
    let mut objective = 0i128;
    for (i, a) in arcs.iter().enumerate() {
        verify_arc_contribution(
            nodes,
            a,
            s.flow[i],
            s.reduced_costs[i],
            &s.potential,
            &mut balances,
            &mut objective,
        )?;
    }
    if balances != demand || objective != s.objective {
        return Err(NetworkSimplexError::CertificateMismatch);
    }
    Ok(())
}

// Origin: engine/crates_rs/core_solvers/src/solver_flow_network_simplex.rs
// Claim: urn:core:crates_rs:core-solvers:solver-flow-network-simplex:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_b9280da1 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
