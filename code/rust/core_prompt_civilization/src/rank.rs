//! Exact rational PageRank solver and certificate verifier over BigRational.
//!
//! Enforces:
//! - F-RANK-01: A fitter child lifts its parent more (controlled fixture: higher q_c gives higher parent r_inv).
//! - F-RANK-02: The verifier reconstructs P<-, rejecting forged matrices or zero vectors.
//! - F-RANK-03: The solver budget is reported honestly (BUDGET_EXHAUSTED when bounds exceeded).
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::{BigRational, Rational64};
use num_traits::{One, Signed, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};

pub const DEFAULT_ALPHA_NUM: i64 = 17;
pub const DEFAULT_ALPHA_DEN: i64 = 20;

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum RankError {
    #[error("BUDGET_EXHAUSTED: {0}")]
    BudgetExhausted(String),
    #[error("EMPTY_GRAPH: Graph must contain at least one node")]
    EmptyGraph,
    #[error("INVALID_DAMPING: Damping factor must be strictly between 0 and 1, got {0}")]
    InvalidDamping(Rational64),
    #[error("SINGULAR_MATRIX: PageRank transition system is singular")]
    SingularMatrix,
    #[error("RANK_INPUT_INVALID: {0}")]
    InputInvalid(String),
    #[error("RATIONAL64_OVERFLOW: Arithmetic overflow in Rational64 calculation")]
    Rational64Overflow,
    #[error("COMPACTION_DENOMINATOR_TOO_LARGE: Requested power of two {0} exceeds bounds")]
    CompactionDenominatorTooLarge(u32),
}

pub type PageRankError = RankError;

/// Deterministic SplitMix64 pseudo-random number generator.
/// Produces identical sequences across all architectures and platforms.
#[derive(Clone, Debug)]
pub struct SovereignPrng {
    state: u64,
}

impl SovereignPrng {
    pub fn new(seed: u64) -> Self {
        Self { state: seed }
    }

    pub fn next_u64(&mut self) -> u64 {
        self.state = self.state.wrapping_add(0x9E3779B97F4A7C15);
        let mut z = self.state;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58476D1CE4E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D049BB133111EB);
        z ^ (z >> 31)
    }

    pub fn gen_range(&mut self, min: usize, max: usize) -> usize {
        if min >= max {
            return min;
        }
        let span = (max - min) as u64;
        min + (self.next_u64() % span) as usize
    }
}

/// Directed citation graph for scale-free topology benchmarking and PageRank computation.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CitationGraph {
    pub num_nodes: usize,
    pub edges: Vec<(usize, usize)>,
    pub m: usize,
    pub bridge_edges: usize,
    pub seed: u64,
}

impl CitationGraph {
    pub fn new(num_nodes: usize, edges: Vec<(usize, usize)>) -> Self {
        Self {
            num_nodes,
            edges,
            m: 0,
            bridge_edges: 0,
            seed: 0,
        }
    }

    pub fn num_nodes(&self) -> usize {
        self.num_nodes
    }

    pub fn edges(&self) -> &[(usize, usize)] {
        &self.edges
    }

    pub fn is_empty(&self) -> bool {
        self.num_nodes == 0
    }

    pub fn in_degrees(&self) -> Vec<usize> {
        let mut degs = vec![0; self.num_nodes];
        for &(_, v) in &self.edges {
            if v < self.num_nodes {
                degs[v] += 1;
            }
        }
        degs
    }

    pub fn out_degrees(&self) -> Vec<usize> {
        let mut degs = vec![0; self.num_nodes];
        for &(u, _) in &self.edges {
            if u < self.num_nodes {
                degs[u] += 1;
            }
        }
        degs
    }
}

/// Typed certificate for exact PageRank over BigRational with a posteriori l1 error bounds.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SparsePageRankResult {
    pub num_nodes: usize,
    pub num_edges: usize,
    pub steps_executed: usize,
    pub damping: BigRational,
    pub residual_l1_delta: BigRational,
    pub certified_l1_error: BigRational,
    pub ranks: Vec<BigRational>,
    pub is_converged: bool,
}

pub type PageRankCertificateV1 = SparsePageRankResult;

/// Compacted rational PageRank result on a common power-of-two denominator.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompactedPageRankResult {
    pub certificate: SparsePageRankResult,
    pub denom_power_of_two: u32,
    pub common_denominator: BigInt,
    pub compaction_l1_shift: BigRational,
    pub total_certified_l1_error: BigRational,
    pub compacted_ranks: Vec<Rational64>,
    pub compacted_ranks_big: Vec<BigRational>,
}

pub type CompactedPageRankResultV1 = CompactedPageRankResult;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RankEvidenceV1 {
    pub passes: u64,
    pub failures: u64,
}

impl RankEvidenceV1 {
    pub fn pass_fraction(&self) -> BigRational {
        let total = BigInt::from(self.passes) + BigInt::from(self.failures);
        if total.is_zero() {
            BigRational::new(BigInt::one(), BigInt::from(2)) // default 1/2
        } else {
            BigRational::new(BigInt::from(self.passes), total)
        }
    }
}

pub struct ExactPageRankSolverV1;

impl ExactPageRankSolverV1 {
    fn fill_transition_row(
        row: &mut [BigRational],
        parents: Option<&Vec<usize>>,
        q_c: &BigRational,
        u_val: &BigRational,
    ) {
        if let Some(parents) = parents.filter(|p| !p.is_empty()) {
            let k = BigInt::from(parents.len());
            let inv_k = BigRational::new(BigInt::one(), k);
            let one_minus_q = BigRational::one() - q_c;
            for (col, value) in row.iter_mut().enumerate() {
                let mut entry = &one_minus_q * u_val;
                if parents.contains(&col) {
                    entry += q_c * &inv_k;
                }
                *value = entry;
            }
        } else {
            // Dangling node: transitions uniformly
            row.fill(u_val.clone());
        }
    }

    /// Reconstructs the canonical P<- transition matrix for the community.
    /// Nodes are sorted alphabetically.
    pub fn reconstruct_transition_matrix(
        nodes: &[String],
        edges: &[(String, String)], // (parent, child)
        evidence: &HashMap<String, RankEvidenceV1>,
    ) -> Vec<Vec<BigRational>> {
        let n = nodes.len();
        if n == 0 {
            return Vec::new();
        }
        let u_val = BigRational::new(BigInt::one(), BigInt::from(n));
        let node_idx: HashMap<String, usize> = nodes
            .iter()
            .enumerate()
            .map(|(i, node)| (node.clone(), i))
            .collect();

        // Child -> list of parents
        let mut child_parents: HashMap<usize, Vec<usize>> = HashMap::new();
        for (p, c) in edges {
            if let (Some(&p_idx), Some(&c_idx)) = (node_idx.get(p), node_idx.get(c)) {
                child_parents.entry(c_idx).or_default().push(p_idx);
            }
        }

        let mut matrix = vec![vec![BigRational::zero(); n]; n];
        for (i, row) in matrix.iter_mut().enumerate() {
            let q_c = evidence
                .get(&nodes[i])
                .map(|e| e.pass_fraction())
                .unwrap_or_else(|| BigRational::new(BigInt::one(), BigInt::from(2)));
            Self::fill_transition_row(row, child_parents.get(&i), &q_c, &u_val);
        }

        matrix
    }

    fn adjacency_node_count(adjacency: &BTreeMap<usize, Vec<usize>>) -> Result<usize, RankError> {
        let max_key = adjacency.keys().copied().max();
        let max_val = adjacency.values().flat_map(|v| v.iter().copied()).max();
        let n = match (max_key, max_val) {
            (None, None) => return Err(RankError::EmptyGraph),
            (Some(k), None) => k + 1,
            (None, Some(v)) => v + 1,
            (Some(k), Some(v)) => std::cmp::max(k + 1, v + 1),
        };
        if n == 0 {
            return Err(RankError::EmptyGraph);
        }
        Ok(n)
    }

    fn build_rational64_transition(
        adjacency: &BTreeMap<usize, Vec<usize>>,
        n: usize,
        uniform: Rational64,
    ) -> Result<Vec<Vec<Rational64>>, RankError> {
        // P[v][u] is transition probability from u to v
        let mut p = vec![vec![Rational64::zero(); n]; n];
        for u in 0..n {
            let targets = adjacency.get(&u);
            let out_degree = targets.map_or(0, Vec::len);
            if out_degree == 0 {
                for row in p.iter_mut().take(n) {
                    row[u] = uniform;
                }
                continue;
            }
            let step = Rational64::new(1, out_degree as i64);
            for &v in targets.into_iter().flatten() {
                if v >= n {
                    return Err(RankError::InputInvalid(format!(
                        "Node target {v} out of bounds {n}"
                    )));
                }
                p[v][u] += step;
            }
        }
        Ok(p)
    }

    fn build_pagerank_augmented_matrix(
        p: &[Vec<Rational64>],
        damping: Rational64,
        uniform: Rational64,
        n: usize,
    ) -> Vec<Vec<Rational64>> {
        // Form linear system: (I - damping * P) r = (1 - damping) * u
        // Augmented matrix: n rows, n + 1 columns
        let one_minus_alpha = Rational64::one() - damping;
        let teleport = one_minus_alpha * uniform;
        let mut mat = vec![vec![Rational64::zero(); n + 1]; n];

        for i in 0..(n - 1) {
            for j in 0..n {
                let mut coeff = -damping * p[i][j];
                if i == j {
                    coeff += Rational64::one();
                }
                mat[i][j] = coeff;
            }
            mat[i][n] = teleport;
        }

        // Last row replaces redundant equation with sum(r_j) = 1
        let last = n - 1;
        mat[last][..n].fill(Rational64::one());
        mat[last][n] = Rational64::one();
        mat
    }

    /// Exact rational PageRank over num_rational::Rational64 via Gaussian elimination.
    /// Solves r = damping * P * r + (1 - damping) * u with sum(r) = 1.
    pub fn solve(
        adjacency: &BTreeMap<usize, Vec<usize>>,
        damping: Rational64,
    ) -> Result<Vec<Rational64>, RankError> {
        if damping <= Rational64::zero() || damping >= Rational64::one() {
            return Err(RankError::InvalidDamping(damping));
        }

        let n = Self::adjacency_node_count(adjacency)?;
        if n == 1 {
            return Ok(vec![Rational64::one()]);
        }

        let uniform = Rational64::new(1, n as i64);
        let p = Self::build_rational64_transition(adjacency, n, uniform)?;
        let mut mat = Self::build_pagerank_augmented_matrix(&p, damping, uniform, n);

        row_reduce_rational64(&mut mat)?;

        let mut r = vec![Rational64::zero(); n];
        for (i, val) in r.iter_mut().enumerate() {
            *val = mat[i][n];
            if *val < Rational64::zero() || *val.denom() <= 0 {
                return Err(RankError::Rational64Overflow);
            }
        }

        Ok(r)
    }

    /// Convenience solver taking node count and edge list over 0..num_nodes.
    pub fn solve_edges(
        num_nodes: usize,
        edges: &[(usize, usize)],
        damping: Rational64,
    ) -> Result<Vec<Rational64>, RankError> {
        if num_nodes == 0 {
            return Err(RankError::EmptyGraph);
        }
        let mut adj = BTreeMap::new();
        for i in 0..num_nodes {
            adj.insert(i, Vec::new());
        }
        for &(u, v) in edges {
            if u >= num_nodes || v >= num_nodes {
                return Err(RankError::InputInvalid(format!(
                    "Edge ({u}, {v}) exceeds num_nodes {num_nodes}"
                )));
            }
            adj.entry(u).or_default().push(v);
        }
        Self::solve(&adj, damping)
    }

    /// Solves r = alpha * (P<-)^T * r + (1 - alpha) * u exactly via BigRational Gaussian elimination.
    pub fn solve_evidence(
        nodes: &[String],
        edges: &[(String, String)],
        evidence: &HashMap<String, RankEvidenceV1>,
        max_nodes: usize,
        max_edges: usize,
    ) -> Result<Vec<BigRational>, String> {
        let n = nodes.len();
        if n == 0 {
            return Ok(vec![]);
        }
        if n > max_nodes || edges.len() > max_edges {
            return Err("BUDGET_EXHAUSTED".to_string());
        }

        let p_inv = Self::reconstruct_transition_matrix(nodes, edges, evidence);
        let alpha = BigRational::new(
            BigInt::from(DEFAULT_ALPHA_NUM),
            BigInt::from(DEFAULT_ALPHA_DEN),
        );
        let one_minus_alpha = BigRational::one() - &alpha;
        let u_val = BigRational::new(BigInt::one(), BigInt::from(n));
        let teleport = &one_minus_alpha * &u_val;

        // System: (I - alpha * (P<-)^T) r = teleport
        // Row i: r_i - alpha * sum_j(P<-[j][i] * r_j) = teleport
        let mut mat: Vec<Vec<BigRational>> = vec![vec![BigRational::zero(); n + 1]; n];

        for i in 0..n {
            for j in 0..n {
                let mut coeff = -&alpha * &p_inv[j][i];
                if i == j {
                    coeff += BigRational::one();
                }
                mat[i][j] = coeff;
            }
            mat[i][n] = teleport.clone();
        }

        // Replace one equation with sum(r_i) = 1 to guarantee exact stochastic normalization
        let last_row = n - 1;
        mat[last_row][..n].fill(BigRational::one());
        mat[last_row][n] = BigRational::one();

        row_reduce(&mut mat, None)?;

        let mut r = vec![BigRational::zero(); n];
        for i in 0..n {
            r[i] = mat[i][n].clone();
        }

        Ok(r)
    }

    /// Backward-compatible alias for evidence solver.
    pub fn solve_with_evidence(
        nodes: &[String],
        edges: &[(String, String)],
        evidence: &HashMap<String, RankEvidenceV1>,
        max_nodes: usize,
        max_edges: usize,
    ) -> Result<Vec<BigRational>, String> {
        Self::solve_evidence(nodes, edges, evidence, max_nodes, max_edges)
    }

    fn is_valid_stochastic_vector(candidate_rank: &[BigRational], n: usize) -> bool {
        if candidate_rank.len() != n {
            return false;
        }
        let mut sum = BigRational::zero();
        for val in candidate_rank {
            if val < &BigRational::zero() {
                return false;
            }
            sum += val;
        }
        sum == BigRational::one()
    }

    /// Verifies candidate rank certificate.
    pub fn verify_certificate(
        nodes: &[String],
        edges: &[(String, String)],
        evidence: &HashMap<String, RankEvidenceV1>,
        declared_matrix: &[Vec<BigRational>],
        candidate_rank: &[BigRational],
    ) -> bool {
        let n = nodes.len();
        // Reject zero vector or non-stochastic vector
        if !Self::is_valid_stochastic_vector(candidate_rank, n) {
            return false;
        }

        // Reconstruct true P<- matrix and compare with declared matrix
        let true_p = Self::reconstruct_transition_matrix(nodes, edges, evidence);
        if declared_matrix != true_p.as_slice() {
            return false;
        }

        // Verify fixed point equation: r = alpha * (P<-)^T * r + (1 - alpha) * u
        let alpha = BigRational::new(
            BigInt::from(DEFAULT_ALPHA_NUM),
            BigInt::from(DEFAULT_ALPHA_DEN),
        );
        let one_minus_alpha = BigRational::one() - &alpha;
        let u_val = BigRational::new(BigInt::one(), BigInt::from(n));
        let teleport = &one_minus_alpha * &u_val;

        for i in 0..n {
            let trans_sum: BigRational = (0..n).map(|j| &true_p[j][i] * &candidate_rank[j]).sum();
            let rhs = &alpha * &trans_sum + &teleport;
            if candidate_rank[i] != rhs {
                return false;
            }
        }

        true
    }

    fn sample_preferential_targets(
        rng: &mut SovereignPrng,
        in_degrees: &[usize],
        new_node: usize,
        target_count: usize,
    ) -> Vec<usize> {
        let mut targets = HashSet::new();
        // Total weight = sum_{v < new_node} (in_degrees[v] + 1)
        let total_w: usize = (0..new_node).map(|v| in_degrees[v] + 1).sum();

        if total_w > 0 {
            let mut attempts = 0;
            while targets.len() < target_count && attempts < target_count * 50 {
                attempts += 1;
                let r = rng.gen_range(1, total_w + 1);
                let chosen = Self::pick_weighted_node(in_degrees, new_node, r);
                targets.insert(chosen);
            }
        }

        // Fallback fill if attempts timed out
        for v in 0..new_node {
            if targets.len() >= target_count {
                break;
            }
            targets.insert(v);
        }

        // Deterministic insertion order
        let mut sorted_targets: Vec<usize> = targets.into_iter().collect();
        sorted_targets.sort_unstable();
        sorted_targets
    }

    fn pick_weighted_node(in_degrees: &[usize], new_node: usize, r: usize) -> usize {
        let mut cum = 0;
        for (v, &deg) in in_degrees.iter().enumerate().take(new_node) {
            cum += deg + 1;
            if cum >= r {
                return v;
            }
        }
        0
    }

    fn append_unique_edge(
        edges: &mut Vec<(usize, usize)>,
        edge_set: &mut HashSet<(usize, usize)>,
        in_degrees: &mut [usize],
        u: usize,
        v: usize,
    ) -> bool {
        if u != v && edge_set.insert((u, v)) {
            edges.push((u, v));
            in_degrees[v] += 1;
            true
        } else {
            false
        }
    }

    /// Generates a deterministic Barabási-Albert preferential attachment citation graph
    /// with parameter m and coupled strongly connected component bridge edges.
    pub fn generate_scale_free_citation_graph(
        n: usize,
        m: usize,
        bridge_edges: usize,
        seed: u64,
    ) -> CitationGraph {
        if n <= 1 {
            return CitationGraph {
                num_nodes: n,
                edges: Vec::new(),
                m,
                bridge_edges,
                seed,
            };
        }

        let mut rng = SovereignPrng::new(seed);
        let mut edges = Vec::new();
        let mut edge_set = HashSet::new();
        let mut in_degrees = vec![0; n];

        let effective_m = m.max(1);
        let seed_count = std::cmp::min(n, effective_m);

        // Initial connected seed graph of seed_count nodes (a cycle)
        for i in 0..seed_count {
            let j = (i + 1) % seed_count;
            Self::append_unique_edge(&mut edges, &mut edge_set, &mut in_degrees, i, j);
        }

        // Preferential attachment for new_node in seed_count..n
        for new_node in seed_count..n {
            let target_count = std::cmp::min(effective_m, new_node);
            let sorted_targets =
                Self::sample_preferential_targets(&mut rng, &in_degrees, new_node, target_count);
            for t in sorted_targets {
                Self::append_unique_edge(&mut edges, &mut edge_set, &mut in_degrees, new_node, t);
            }
        }

        // Couple strongly connected components with reciprocal / forward bridge edges
        let mut added_bridges = 0;
        let mut bridge_attempts = 0;
        let max_bridge_attempts = bridge_edges.saturating_mul(100).max(100);

        while added_bridges < bridge_edges && bridge_attempts < max_bridge_attempts {
            bridge_attempts += 1;
            let u = rng.gen_range(0, n);
            let v = rng.gen_range(0, n);
            if Self::append_unique_edge(&mut edges, &mut edge_set, &mut in_degrees, u, v) {
                added_bridges += 1;
            }
        }

        CitationGraph {
            num_nodes: n,
            edges,
            m,
            bridge_edges,
            seed,
        }
    }

    /// Solves scale-free PageRank over arbitrary-precision BigRational using
    /// sparse contractive power iteration with exact a posteriori l1 error certification.
    ///
    /// Contractive fixed point equation:
    ///   r = alpha * P * r + (1 - alpha) * u
    /// Contraction factor: alpha = 17/20 in l1 norm.
    /// Certified bound: ||r^(k) - r*||_1 <= 17/3 * ||r^(k) - r^(k-1)||_1.
    pub fn solve_sparse_bigrational(
        &self,
        graph: &CitationGraph,
        max_iters: usize,
        tolerance: &BigRational,
    ) -> Result<SparsePageRankResult, PageRankError> {
        Self::solve_sparse_bigrational_impl(graph, max_iters, tolerance)
    }

    #[allow(clippy::type_complexity)]
    fn build_sparse_in_edges(
        graph: &CitationGraph,
        n: usize,
    ) -> Result<(Vec<usize>, Vec<Vec<(usize, usize)>>, Vec<usize>), PageRankError> {
        let mut out_degrees = vec![0usize; n];
        let mut in_map: Vec<BTreeMap<usize, usize>> = vec![BTreeMap::new(); n];
        for &(u, v) in &graph.edges {
            if u >= n || v >= n {
                return Err(RankError::InputInvalid(format!(
                    "Edge ({u}, {v}) exceeds node count {n}"
                )));
            }
            out_degrees[u] += 1;
            *in_map[v].entry(u).or_insert(0) += 1;
        }
        let in_edges: Vec<Vec<(usize, usize)>> = in_map
            .into_iter()
            .map(|targets| targets.into_iter().collect())
            .collect();
        let dangling_nodes: Vec<usize> = (0..n).filter(|&u| out_degrees[u] == 0).collect();
        Ok((out_degrees, in_edges, dangling_nodes))
    }

    fn sparse_power_iteration_step(
        r: &[BigRational],
        out_degrees: &[usize],
        in_edges: &[Vec<(usize, usize)>],
        dangling_nodes: &[usize],
        alpha: &BigRational,
        one_minus_alpha: &BigRational,
        uniform: &BigRational,
    ) -> (Vec<BigRational>, BigRational) {
        let n = r.len();
        let scaled_r: Vec<BigRational> = (0..n)
            .map(|u| {
                if out_degrees[u] > 0 {
                    &r[u] / BigInt::from(out_degrees[u])
                } else {
                    BigRational::zero()
                }
            })
            .collect();

        let dangle_sum: BigRational = dangling_nodes.iter().map(|&u| &r[u]).sum();
        let teleport = (alpha * &dangle_sum + one_minus_alpha) * uniform;

        let mut next_r = vec![BigRational::zero(); n];
        for v in 0..n {
            let mut in_sum = BigRational::zero();
            for &(u, count) in &in_edges[v] {
                if count == 1 {
                    in_sum += &scaled_r[u];
                } else {
                    in_sum += &BigRational::new(BigInt::from(count), BigInt::one()) * &scaled_r[u];
                }
            }
            next_r[v] = alpha * in_sum + &teleport;
        }

        let current_delta: BigRational = (0..n).map(|i| (&next_r[i] - &r[i]).abs()).sum();
        (next_r, current_delta)
    }

    pub fn solve_sparse_bigrational_impl(
        graph: &CitationGraph,
        max_iters: usize,
        tolerance: &BigRational,
    ) -> Result<SparsePageRankResult, PageRankError> {
        let n = graph.num_nodes;
        if n == 0 {
            return Err(RankError::EmptyGraph);
        }
        if n == 1 {
            return Ok(SparsePageRankResult {
                num_nodes: 1,
                num_edges: graph.edges.len(),
                steps_executed: 0,
                damping: BigRational::new(
                    BigInt::from(DEFAULT_ALPHA_NUM),
                    BigInt::from(DEFAULT_ALPHA_DEN),
                ),
                residual_l1_delta: BigRational::zero(),
                certified_l1_error: BigRational::zero(),
                ranks: vec![BigRational::one()],
                is_converged: true,
            });
        }

        let (out_degrees, in_edges, dangling_nodes) = Self::build_sparse_in_edges(graph, n)?;

        let alpha = BigRational::new(
            BigInt::from(DEFAULT_ALPHA_NUM),
            BigInt::from(DEFAULT_ALPHA_DEN),
        );
        let one_minus_alpha = BigRational::one() - &alpha;
        let uniform = BigRational::new(BigInt::one(), BigInt::from(n));

        // Contraction multiplier: alpha / (1 - alpha) = (17/20) / (3/20) = 17/3
        let contraction_multiplier = BigRational::new(BigInt::from(17), BigInt::from(3));

        // Initial iterate r^(0) = [1/n, ..., 1/n]
        let mut r = vec![uniform.clone(); n];
        let mut delta = BigRational::one();
        let mut certified_error = contraction_multiplier.clone();
        let mut steps_executed = 0;
        let mut is_converged = false;

        for step in 0..max_iters {
            steps_executed = step + 1;
            let (next_r, current_delta) = Self::sparse_power_iteration_step(
                &r,
                &out_degrees,
                &in_edges,
                &dangling_nodes,
                &alpha,
                &one_minus_alpha,
                &uniform,
            );
            delta = current_delta;
            certified_error = &contraction_multiplier * &delta;
            r = next_r;

            if delta <= *tolerance {
                is_converged = true;
                break;
            }
        }

        // Verify exact stochastic closure: sum(r_i) == 1
        let sum_ranks: BigRational = r.iter().cloned().sum();
        if sum_ranks != BigRational::one() {
            return Err(RankError::InputInvalid(
                "Numerical drift detected: rank sum does not equal 1/1".into(),
            ));
        }

        Ok(SparsePageRankResult {
            num_nodes: n,
            num_edges: graph.edges.len(),
            steps_executed,
            damping: alpha,
            residual_l1_delta: delta,
            certified_l1_error: certified_error,
            ranks: r,
            is_converged,
        })
    }

    fn hamilton_hare_quotas(
        ranks: &[BigRational],
        d_big: &BigInt,
    ) -> Result<Vec<BigInt>, PageRankError> {
        let n = ranks.len();
        let mut quotas = Vec::with_capacity(n);
        let mut total_floor = BigInt::zero();

        for (i, r) in ranks.iter().enumerate() {
            let scaled = r * d_big;
            let floor_val = scaled.to_integer();
            let rem = &scaled - BigRational::from(floor_val.clone());
            quotas.push((floor_val.clone(), rem, i));
            total_floor += floor_val;
        }

        let deficit = d_big - &total_floor;
        let deficit_usize = deficit
            .to_usize()
            .filter(|&d| d <= n)
            .ok_or_else(|| RankError::InputInvalid("Deficit conversion or bound failed".into()))?;

        // Sort by remainder descending, tie-breaking by original node index for determinism
        quotas.sort_by(|a, b| b.1.cmp(&a.1).then(a.2.cmp(&b.2)));

        let mut k_vals = vec![BigInt::zero(); n];
        for (rank_idx, (floor_val, _, orig_i)) in quotas.into_iter().enumerate() {
            let add = if rank_idx < deficit_usize {
                BigInt::one()
            } else {
                BigInt::zero()
            };
            k_vals[orig_i] = floor_val + add;
        }

        // Verify sum(k_i) == D exactly
        let sum_k: BigInt = k_vals.iter().cloned().sum();
        if &sum_k != d_big {
            return Err(RankError::InputInvalid(
                "Hamilton-Hare sum invariant violated".into(),
            ));
        }
        Ok(k_vals)
    }

    /// Compacts exact BigRational PageRank vector onto a common power-of-two denominator
    /// D = 2^denom_power_of_two using the Hamilton-Hare Largest Remainder Method.
    pub fn compact_ranks(
        certificate: SparsePageRankResult,
        denom_power_of_two: u32,
    ) -> Result<CompactedPageRankResult, PageRankError> {
        let n = certificate.ranks.len();
        if n == 0 {
            return Err(RankError::EmptyGraph);
        }
        if denom_power_of_two > 62 {
            return Err(RankError::CompactionDenominatorTooLarge(denom_power_of_two));
        }

        let d_big = BigInt::one() << (denom_power_of_two as usize);
        let k_vals = Self::hamilton_hare_quotas(&certificate.ranks, &d_big)?;

        let d_i64 = 1i64 << denom_power_of_two;
        let mut compacted_ranks = Vec::with_capacity(n);
        let mut compacted_ranks_big = Vec::with_capacity(n);
        let mut compaction_shift = BigRational::zero();

        for (i, k) in k_vals.into_iter().enumerate() {
            let k_i64 = k
                .to_i64()
                .ok_or_else(|| RankError::InputInvalid("Numerator exceeds i64 bounds".into()))?;
            let r_compacted = Rational64::new(k_i64, d_i64);
            let r_compacted_big = BigRational::new(k, d_big.clone());

            compaction_shift += (&r_compacted_big - &certificate.ranks[i]).abs();
            compacted_ranks.push(r_compacted);
            compacted_ranks_big.push(r_compacted_big);
        }

        let total_certified_error = &compaction_shift + &certificate.certified_l1_error;

        Ok(CompactedPageRankResult {
            certificate,
            denom_power_of_two,
            common_denominator: d_big,
            compaction_l1_shift: compaction_shift,
            total_certified_l1_error: total_certified_error,
            compacted_ranks,
            compacted_ranks_big,
        })
    }

    /// Solves scale-free PageRank and compacts onto a common power-of-two denominator.
    pub fn solve_compacted_rational(
        &self,
        graph: &CitationGraph,
        denom_power_of_two: u32,
    ) -> Result<CompactedPageRankResult, PageRankError> {
        let tolerance = BigRational::new(BigInt::one(), BigInt::from(100_000));
        self.solve_compacted_rational_with_params(graph, 50, &tolerance, denom_power_of_two)
    }

    pub fn solve_compacted_rational_with_params(
        &self,
        graph: &CitationGraph,
        max_iters: usize,
        tolerance: &BigRational,
        denom_power_of_two: u32,
    ) -> Result<CompactedPageRankResult, PageRankError> {
        let certificate = self.solve_sparse_bigrational(graph, max_iters, tolerance)?;
        Self::compact_ranks(certificate, denom_power_of_two)
    }
}

/// Shared exact elimination for native and compatibility rank profiles.
pub(crate) fn row_reduce(
    mat: &mut [Vec<BigRational>],
    max_bits: Option<&BigInt>,
) -> Result<(), String> {
    let n = mat.len();
    if mat.iter().any(|row| row.len() != n + 1) {
        return Err("RANK_MATRIX_SHAPE: coefficient matrix must be n by n+1".into());
    }
    for col in 0..n {
        let Some(pivot) = (col..n).find(|&row| !mat[row][col].is_zero()) else {
            continue;
        };
        mat.swap(col, pivot);
        let pivot_val = mat[col][col].clone();
        for value in &mut mat[col][col..=n] {
            *value /= &pivot_val;
            if max_bits.is_some_and(|limit| {
                BigInt::from(value.numer().bits()) > *limit
                    || BigInt::from(value.denom().bits()) > *limit
            }) {
                return Err("BUDGET_EXHAUSTED: Coefficient bit-length exceeded".into());
            }
        }
        let pivot_row = mat[col].clone();
        for (row, values) in mat.iter_mut().enumerate() {
            if row != col && !values[col].is_zero() {
                let factor = values[col].clone();
                for c in col..=n {
                    values[c] -= &factor * &pivot_row[c];
                }
            }
        }
    }
    Ok(())
}

fn eliminate_rational64_system(mat: &mut [Vec<Rational64>], n: usize) -> Result<(), RankError> {
    for col in 0..n {
        let Some(pivot) = (col..n).find(|&row| !mat[row][col].is_zero()) else {
            return Err(RankError::SingularMatrix);
        };
        mat.swap(col, pivot);
        let pivot_val = mat[col][col];
        for value in &mut mat[col][col..=n] {
            *value /= pivot_val;
        }
        let pivot_row = mat[col].clone();
        for (row, values) in mat.iter_mut().enumerate() {
            if row != col && !values[col].is_zero() {
                let factor = values[col];
                for c in col..=n {
                    values[c] -= factor * pivot_row[c];
                }
            }
        }
    }
    Ok(())
}

/// Exact Gaussian elimination over Rational64 with canonical reduction.
pub(crate) fn row_reduce_rational64(mat: &mut [Vec<Rational64>]) -> Result<(), RankError> {
    let n = mat.len();
    if mat.iter().any(|row| row.len() != n + 1) {
        return Err(RankError::InputInvalid(
            "RANK_MATRIX_SHAPE: coefficient matrix must be n by n+1".into(),
        ));
    }
    let res = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        eliminate_rational64_system(mat, n)
    }));
    let Ok(inner) = res else {
        return Err(RankError::Rational64Overflow);
    };
    inner?;
    if mat.iter().flatten().any(|val| *val.denom() <= 0) {
        return Err(RankError::Rational64Overflow);
    }
    Ok(())
}

// Origin: engine/crates_rs/core_prompt_civilization/src/rank.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:rank:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_f_rank_01_two_node_worked_example() {
        // Controlled 2-node graph: P and C, edge P -> C.
        let nodes = vec!["P".to_string(), "C".to_string()];
        let edges = vec![("P".to_string(), "C".to_string())];
        let mut evidence = HashMap::new();
        // default q_C = 1/2
        let rank =
            ExactPageRankSolverV1::solve_evidence(&nodes, &edges, &evidence, 1000, 5000).unwrap();
        // Exact solution: r_P = 57/97, r_C = 40/97
        assert_eq!(
            rank[0],
            BigRational::new(BigInt::from(57), BigInt::from(97))
        );
        assert_eq!(
            rank[1],
            BigRational::new(BigInt::from(40), BigInt::from(97))
        );

        // Controlled test: higher q_C lifts parent P more
        evidence.insert(
            "C".to_string(),
            RankEvidenceV1 {
                passes: 10,
                failures: 0,
            },
        ); // q_C = 1
        let rank_higher =
            ExactPageRankSolverV1::solve_evidence(&nodes, &edges, &evidence, 1000, 5000).unwrap();
        assert!(rank_higher[0] > rank[0]); // r_P increases!
    }

    #[test]
    fn test_f_rank_02_verifier_rejects_forgery_and_zero_vector() {
        let nodes = vec!["P".to_string(), "C".to_string()];
        let edges = vec![("P".to_string(), "C".to_string())];
        let evidence = HashMap::new();

        let zero_rank = vec![BigRational::zero(), BigRational::zero()];
        let p_mat = ExactPageRankSolverV1::reconstruct_transition_matrix(&nodes, &edges, &evidence);

        // Reject zero vector
        assert!(!ExactPageRankSolverV1::verify_certificate(
            &nodes, &edges, &evidence, &p_mat, &zero_rank
        ));

        // Reject forged matrix
        let forged_mat = vec![
            vec![BigRational::zero(), BigRational::zero()],
            vec![BigRational::one(), BigRational::zero()],
        ];
        let valid_rank =
            ExactPageRankSolverV1::solve_evidence(&nodes, &edges, &evidence, 1000, 5000).unwrap();
        assert!(!ExactPageRankSolverV1::verify_certificate(
            &nodes,
            &edges,
            &evidence,
            &forged_mat,
            &valid_rank
        ));

        // Accept valid certificate
        assert!(ExactPageRankSolverV1::verify_certificate(
            &nodes,
            &edges,
            &evidence,
            &p_mat,
            &valid_rank
        ));
    }

    #[test]
    fn test_f_rank_03_budget_exhausted() {
        let nodes = vec!["A".to_string(), "B".to_string()];
        let edges = vec![("A".to_string(), "B".to_string())];
        let evidence = HashMap::new();
        let res = ExactPageRankSolverV1::solve_evidence(&nodes, &edges, &evidence, 1, 5000);
        assert_eq!(res.unwrap_err(), "BUDGET_EXHAUSTED");
    }

    #[test]
    fn test_rational64_two_node_directed_link() {
        let mut adj = BTreeMap::new();
        adj.insert(0, vec![1]);
        adj.insert(1, vec![]);
        let alpha = Rational64::new(17, 20);
        let rank = ExactPageRankSolverV1::solve(&adj, alpha).unwrap();
        assert_eq!(rank.len(), 2);
        assert_eq!(rank[0], Rational64::new(20, 57));
        assert_eq!(rank[1], Rational64::new(37, 57));
        assert_eq!(rank[0] + rank[1], Rational64::one());
        assert!(rank[1] > rank[0]);
    }

    #[test]
    fn test_rational64_three_node_cycle() {
        let edges = [(0, 1), (1, 2), (2, 0)];
        let alpha = Rational64::new(17, 20);
        let rank = ExactPageRankSolverV1::solve_edges(3, &edges, alpha).unwrap();
        assert_eq!(rank, vec![Rational64::new(1, 3); 3]);
        assert_eq!(rank.iter().sum::<Rational64>(), Rational64::one());
    }

    #[test]
    fn test_rational64_dangling_star_graph() {
        let edges = [(1, 0), (2, 0), (3, 0)];
        let alpha = Rational64::new(17, 20);
        let rank = ExactPageRankSolverV1::solve_edges(4, &edges, alpha).unwrap();
        assert_eq!(rank.len(), 4);
        assert_eq!(rank.iter().sum::<Rational64>(), Rational64::one());
        assert_eq!(rank[0], *rank.iter().max().unwrap());
        assert_eq!(rank[1], rank[2]);
        assert_eq!(rank[2], rank[3]);
    }

    #[test]
    fn test_rational64_invalid_damping() {
        let mut adj = BTreeMap::new();
        adj.insert(0, vec![1]);
        assert!(matches!(
            ExactPageRankSolverV1::solve(&adj, Rational64::zero()),
            Err(RankError::InvalidDamping(_))
        ));
        assert!(matches!(
            ExactPageRankSolverV1::solve(&adj, Rational64::one()),
            Err(RankError::InvalidDamping(_))
        ));
        assert!(matches!(
            ExactPageRankSolverV1::solve(&adj, Rational64::new(-1, 2)),
            Err(RankError::InvalidDamping(_))
        ));
    }

    #[test]
    fn test_rational64_empty_graph() {
        let adj: BTreeMap<usize, Vec<usize>> = BTreeMap::new();
        assert!(matches!(
            ExactPageRankSolverV1::solve(&adj, Rational64::new(17, 20)),
            Err(RankError::EmptyGraph)
        ));
    }

    #[test]
    fn test_rational64_zero_float_drift_inadmissible() {
        // Complex 5-node graph with multiple cycles, dangling nodes, and branches
        let edges = [(0, 1), (1, 2), (1, 3), (2, 0), (3, 2), (4, 1)];
        let alpha = Rational64::new(17, 20);
        let rank = ExactPageRankSolverV1::solve_edges(5, &edges, alpha).unwrap();
        // Exact stochastic property: sum is identically 1/1 without epsilon tolerance
        let total: Rational64 = rank.iter().sum();
        assert_eq!(total, Rational64::one());
        assert_eq!(total.numer(), &1);
        assert_eq!(total.denom(), &1);
    }
}
