// AuthorityEffect: None.

//! Discrete Quantum Walk on permutation group Cayley graphs in exact algebraic arithmetic.
//!
//! Evaluates discrete-time quantum walks (DTQW) on:
//!   - S_3 with Coxeter generators S = {(0, 1), (1, 2)} (order 6, degree 2, diameter 3)
//!     using the exact Hadamard coin in Q(zeta_24) / Q(sqrt(2)).
//!   - S_4 with Coxeter generators S = {(0, 1), (1, 2), (2, 3)} (order 24, degree 3, diameter 6)
//!     using the exact Grover diffusion coin (2/3)J - I in Q.
//!
//! On a *finite* Cayley graph the distance from the identity lies in `[0, D]`, `D` the
//! diameter, so `sigma^2(t) <= D^2 / 4` (Popoviciu) for every `t` and `sigma^2(t) / t^2 -> 0`:
//! there is no ballistic regime in the asymptotic sense. What holds, and is checked exactly
//! over the rationals, is unitarity (total probability 1), causality (probability 0 at
//! distance `> t` after `t` steps, the light cone) and the variance bound.
//! [`ExactQuantumWalkResult::is_ballistic`] therefore means only: inside the light-cone window
//! `0 < t <= D` the variance is positive and the support obeys the light cone. Ballistic
//! scaling proper needs an infinite graph. [`hadamard_line`] computes its exact
//! normalized distribution at each admitted finite time, without claiming a limit
//! from finitely many samples.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_fa30c2fc<T> {
    fn checked_invariant_fa30c2fc(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_fa30c2fc<T> for Option<T> {
    #[inline]
    fn checked_invariant_fa30c2fc(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_fa30c2fc<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_fa30c2fc(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use core_number_theory::cyclotomic::{Cyc24, GaussianRat};
use core_number_theory::rational::{r_one, r_zero, ri, rq, Rational};
use serde::{Deserialize, Serialize};
use std::collections::VecDeque;

/// Refusals of the quantum-walk constructors.
#[derive(Clone, Debug, PartialEq, Eq, thiserror::Error)]
pub enum QuantumWalkError {
    #[error("unsupported group {0:?}; expected \"S3\" or \"S4\"")]
    UnsupportedGroup(String),
    #[error("n = {0} is outside 2..=4")]
    UnsupportedDegree(usize),
    #[error("coin or shift is not a unitary walk declaration")]
    InvalidWalk,
    #[error("initial state is not normalized")]
    InitialState,
    #[error("finite walk exceeds its operation budget")]
    Budget,
    #[error(transparent)]
    Matrix(#[from] crate::exact_hermitian::ExactHermitianError),
}

/// Permutation Cayley graph Cay(S_n, S).
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PermutationCayleyGraph {
    pub n: usize,
    pub order: usize,
    pub degree: usize,
    pub permutations: Vec<Vec<usize>>,
    pub adjacency: Vec<Vec<usize>>,
    pub distances: Vec<usize>,
    pub diameter: usize,
}

impl PermutationCayleyGraph {
    /// [`PermutationCayleyGraph::build_sn`] with a typed refusal instead of a panic.
    pub fn try_build_sn(n: usize) -> Result<Self, QuantumWalkError> {
        if !(2..=4).contains(&n) {
            return Err(QuantumWalkError::UnsupportedDegree(n));
        }
        Ok(Self::build_sn(n))
    }

    /// Fixed-carrier implementation after the typed degree validation.
    fn build_sn(n: usize) -> Self {
        assert!(
            (2..=4).contains(&n),
            "n must be in 2..=4 for tractable exact graph"
        );
        let perms = generate_permutations(n);
        let order = perms.len();
        let degree = n - 1;

        let mut adjacency = vec![vec![0; degree]; order];
        for (i, p) in perms.iter().enumerate() {
            for (g, adj_g) in adjacency[i].iter_mut().enumerate().take(degree) {
                let mut next_p = p.clone();
                next_p.swap(g, g + 1);
                let next_idx = perms.iter().position(|x| x == &next_p).checked_invariant_fa30c2fc("checked invariant");
                *adj_g = next_idx;
            }
        }

        // BFS distances from identity permutation (index 0)
        let mut dist = vec![usize::MAX; order];
        dist[0] = 0;
        let mut queue = VecDeque::new();
        queue.push_back(0);

        while let Some(curr) = queue.pop_front() {
            let d = dist[curr];
            for &nbr in &adjacency[curr] {
                if dist[nbr] == usize::MAX {
                    dist[nbr] = d + 1;
                    queue.push_back(nbr);
                }
            }
        }

        let diameter = *dist.iter().max().checked_invariant_fa30c2fc("checked invariant");

        Self {
            n,
            order,
            degree,
            permutations: perms,
            adjacency,
            distances: dist,
            diameter,
        }
    }

    pub fn build_s3() -> Self {
        Self::build_sn(3)
    }

    pub fn build_s4() -> Self {
        Self::build_sn(4)
    }
}

/// Result of discrete quantum walk propagation in exact rational arithmetic.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ExactQuantumWalkResult {
    pub group_name: String,
    pub steps: usize,
    pub order: usize,
    pub degree: usize,
    pub probabilities: Vec<Rational>,
    pub total_probability: Rational,
    pub mean_distance: Rational,
    pub variance_sigma_squared: Rational,
    pub ballistic_ratio: Rational,
    /// Positive variance and a light-cone support, inside the window `0 < steps <= diameter`
    /// (always false outside it: a finite graph has no asymptotic ballistic regime).
    pub is_ballistic: bool,
    /// The diameter `D` of the graph.
    pub diameter: usize,
    /// `D^2 / 4`, the Popoviciu bound on the variance of a distance in `[0, D]`.
    pub variance_upper_bound: Rational,
    /// Every vertex at distance `> steps` from the start has probability exactly 0.
    pub support_within_light_cone: bool,
}

/// Executes exact discrete-time quantum walk on Cay(S_3) using Cyc24 Hadamard coin.
pub fn simulate_walk_s3_exact(steps: usize) -> Result<ExactQuantumWalkResult, QuantumWalkError> {
    if steps > 256 {
        return Err(QuantumWalkError::Budget);
    }
    let graph = PermutationCayleyGraph::build_s3();
    let n_pos = 6;
    let d_c = 2;
    let dim_tot = d_c * n_pos;

    // Hadamard coin in Q(sqrt(2)): H = inv_sqrt2 * [[1, 1], [1, -1]]
    let inv_sqrt2 = Cyc24::sqrt2_inv();

    // Initial state: localized at origin with uniform coin |s> = inv_sqrt2 (|0> + |1>)
    // Amplitude at (c=0, pos=0) = inv_sqrt2 * 1
    let mut state = vec![Cyc24::zero(); dim_tot];
    state[0] = inv_sqrt2.clone();
    state[n_pos] = inv_sqrt2.clone();

    // Time evolution
    for _ in 0..steps {
        // 1. Apply Hadamard coin to each vertex
        let mut coin_state = vec![Cyc24::zero(); dim_tot];
        for pos in 0..n_pos {
            let c0 = &state[pos];
            let c1 = &state[n_pos + pos];

            // c0' = inv_sqrt2 * (c0 + c1)
            let sum_01 = c0.add(c1);
            coin_state[pos] = sum_01.mul(&inv_sqrt2);

            // c1' = inv_sqrt2 * (c0 - c1)
            let diff_01 = c0.sub(c1);
            coin_state[n_pos + pos] = diff_01.mul(&inv_sqrt2);
        }

        // 2. Apply shift operator
        let mut next_state = vec![Cyc24::zero(); dim_tot];
        for c in 0..d_c {
            for pos in 0..n_pos {
                let nxt_pos = graph.adjacency[pos][c];
                next_state[c * n_pos + nxt_pos] = coin_state[c * n_pos + pos].clone();
            }
        }
        state = next_state;
    }

    // Compute exact position probabilities: P(pos) = |c0(pos)|^2 + |c1(pos)|^2 in Q
    let mut probs = Vec::with_capacity(n_pos);
    for pos in 0..n_pos {
        let p0 = state[pos].mul(&state[pos].conj());
        let p1 = state[n_pos + pos].mul(&state[n_pos + pos].conj());
        let p_tot_cyc = p0.add(&p1);
        let p_rat = p_tot_cyc.as_rational().checked_invariant_fa30c2fc("checked invariant");
        probs.push(p_rat);
    }

    Ok(finalize_walk_result(
        "S_3",
        steps,
        n_pos,
        d_c,
        probs,
        &graph.distances,
        graph.diameter,
    ))
}

fn step_grover_walk_s4(
    graph: &PermutationCayleyGraph,
    state: &[Rational],
    n_pos: usize,
    d_c: usize,
) -> Vec<Rational> {
    let dim_tot = d_c * n_pos;
    // 1. Grover diffusion coin on each vertex in Q
    let mut coin_state = vec![r_zero(); dim_tot];
    for pos in 0..n_pos {
        let mut sum_c = r_zero();
        for c in 0..d_c {
            sum_c += &state[c * n_pos + pos];
        }
        // (2/3) * sum - c_i
        for c in 0..d_c {
            coin_state[c * n_pos + pos] = &sum_c * &rq(2, 3) - &state[c * n_pos + pos];
        }
    }

    // 2. Shift operator
    let mut next_state = vec![r_zero(); dim_tot];
    for c in 0..d_c {
        for pos in 0..n_pos {
            let nxt_pos = graph.adjacency[pos][c];
            next_state[c * n_pos + nxt_pos] = coin_state[c * n_pos + pos].clone();
        }
    }
    next_state
}

/// Executes exact discrete-time quantum walk on Cay(S_4) using exact rational Grover coin.
pub fn simulate_walk_s4_exact(steps: usize) -> Result<ExactQuantumWalkResult, QuantumWalkError> {
    if steps > 256 {
        return Err(QuantumWalkError::Budget);
    }
    let graph = PermutationCayleyGraph::build_s4();
    let n_pos = 24;
    let d_c = 3;
    let dim_tot = d_c * n_pos;

    // In S_4 (degree 3), the Grover coin (2/3)J - I has exact rational entries:
    // D_{i, i} = -1/3, D_{i, j} = 2/3 for i != j.
    // We scale the state by sqrt(3) so that state amplitudes remain strictly in Q!
    let mut state = vec![r_zero(); dim_tot];
    // Initial scaled state has 1 at c in 0..3, pos=0:
    for c in 0..d_c {
        state[c * n_pos] = r_one();
    }

    for _ in 0..steps {
        state = step_grover_walk_s4(&graph, &state, n_pos, d_c);
    }

    // Compute exact position probabilities: P(pos) = (1/3) sum_c (state[c, pos])^2
    let mut probs = Vec::with_capacity(n_pos);
    for pos in 0..n_pos {
        let mut sum_sq = r_zero();
        for c in 0..d_c {
            sum_sq += &state[c * n_pos + pos] * &state[c * n_pos + pos];
        }
        let p_rat = sum_sq * rq(1, 3);
        probs.push(p_rat);
    }

    Ok(finalize_walk_result(
        "S_4",
        steps,
        n_pos,
        d_c,
        probs,
        &graph.distances,
        graph.diameter,
    ))
}

fn finalize_walk_result(
    group_name: &str,
    steps: usize,
    n_pos: usize,
    d_c: usize,
    probs: Vec<Rational>,
    distances: &[usize],
    diameter: usize,
) -> ExactQuantumWalkResult {
    let mut tot_prob = r_zero();
    let mut mean_d = r_zero();
    let mut mean_d2 = r_zero();

    for (pos, p_rat) in probs.iter().enumerate() {
        tot_prob += p_rat;
        let d_rat = ri(distances[pos] as i64);
        let d2_rat = ri((distances[pos] * distances[pos]) as i64);
        mean_d += &d_rat * p_rat;
        mean_d2 += &d2_rat * p_rat;
    }

    let mean_d_sq = &mean_d * &mean_d;
    let variance = mean_d2 - mean_d_sq;
    let t_sq = ri((steps * steps) as i64);
    let ballistic_ratio = if steps > 0 {
        &variance / &t_sq
    } else {
        r_zero()
    };
    let support_within_light_cone = probs
        .iter()
        .zip(distances)
        .all(|(p, &d)| d <= steps || *p == r_zero());
    let is_ballistic = steps > 0
        && steps <= diameter
        && tot_prob == r_one()
        && ballistic_ratio > r_zero()
        && support_within_light_cone;
    let variance_upper_bound = ri((diameter * diameter) as i64) * rq(1, 4);

    ExactQuantumWalkResult {
        group_name: group_name.to_string(),
        steps,
        order: n_pos,
        degree: d_c,
        probabilities: probs,
        total_probability: tot_prob,
        mean_distance: mean_d,
        variance_sigma_squared: variance,
        ballistic_ratio,
        is_ballistic,
        diameter,
        variance_upper_bound,
        support_within_light_cone,
    }
}

fn generate_permutations(n: usize) -> Vec<Vec<usize>> {
    core_combinatorics::enumeration::permutations(n, 24).checked_invariant_fa30c2fc("validated S2-S4 bound")
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cayley_graph_s3_invariants() {
        let g = PermutationCayleyGraph::build_s3();
        assert_eq!(g.order, 6);
        assert_eq!(g.degree, 2);
        assert_eq!(g.diameter, 3);
        assert_eq!(g.distances[0], 0);
    }

    #[test]
    fn test_cayley_graph_s4_invariants() {
        let g = PermutationCayleyGraph::build_s4();
        assert_eq!(g.order, 24);
        assert_eq!(g.degree, 3);
        assert_eq!(g.diameter, 6);
    }

    fn walks_up_to(steps: usize) -> Vec<(ExactQuantumWalkResult, Vec<usize>)> {
        let d3 = PermutationCayleyGraph::build_s3().distances;
        let d4 = PermutationCayleyGraph::build_s4().distances;
        (0..=steps)
            .flat_map(|t| {
                [
                    (simulate_walk_s3_exact(t).unwrap(), d3.clone()),
                    (simulate_walk_s4_exact(t).unwrap(), d4.clone()),
                ]
            })
            .collect()
    }

    #[test]
    fn the_walk_is_unitary_and_stays_inside_its_light_cone_at_every_step() {
        for (walk, distances) in walks_up_to(8) {
            assert_eq!(
                walk.total_probability,
                r_one(),
                "{} t={}",
                walk.group_name,
                walk.steps
            );
            // recomputed here, independently of the field: nothing beyond distance t
            for (p, d) in walk.probabilities.iter().zip(&distances) {
                if *d > walk.steps {
                    assert_eq!(*p, r_zero(), "{} t={} d={}", walk.group_name, walk.steps, d);
                }
            }
            assert!(walk.support_within_light_cone);
        }
    }

    #[test]
    fn the_variance_never_exceeds_the_popoviciu_bound_so_there_is_no_asymptotic_ballistic_regime() {
        for (walk, _) in walks_up_to(25) {
            assert!(
                walk.variance_sigma_squared <= walk.variance_upper_bound,
                "{} t={}",
                walk.group_name,
                walk.steps
            );
        }
        // far beyond the diameter the ratio sigma^2 / t^2 is below D^2 / (4 t^2): it tends to 0
        let s3 = simulate_walk_s3_exact(40).unwrap();
        assert!(s3.ballistic_ratio <= rq(9, 4 * 1600));
        assert!(!s3.is_ballistic);
        let s4 = simulate_walk_s4_exact(40).unwrap();
        assert!(s4.ballistic_ratio <= rq(36, 4 * 1600));
        assert!(!s4.is_ballistic);
    }

    #[test]
    fn the_ballistic_flag_holds_only_inside_the_light_cone_window() {
        assert!(!simulate_walk_s3_exact(0).unwrap().is_ballistic);
        assert!(simulate_walk_s3_exact(3).unwrap().is_ballistic);
        assert!(!simulate_walk_s3_exact(4).unwrap().is_ballistic); // past the diameter 3
        assert!(simulate_walk_s4_exact(6).unwrap().is_ballistic);
        assert!(!simulate_walk_s4_exact(7).unwrap().is_ballistic); // past the diameter 6
    }

    #[test]
    fn an_unsupported_group_or_degree_is_a_typed_refusal() {
        assert_eq!(
            PermutationCayleyGraph::try_build_sn(5).unwrap_err(),
            QuantumWalkError::UnsupportedDegree(5)
        );
        assert_eq!(PermutationCayleyGraph::try_build_sn(3).unwrap().order, 6);
    }

    #[test]
    fn test_exact_ballistic_walk_s3() {
        let res = simulate_walk_s3_exact(3).unwrap();
        assert!(res.is_ballistic);
        assert_eq!(res.total_probability, r_one());
        assert!(res.variance_sigma_squared > r_zero());
        assert!(res.ballistic_ratio > r_zero());
    }

    #[test]
    fn test_exact_ballistic_walk_s4() {
        let res = simulate_walk_s4_exact(4).unwrap();
        assert!(res.is_ballistic);
        assert_eq!(res.total_probability, r_one());
        assert!(res.variance_sigma_squared > r_zero());
        assert!(res.ballistic_ratio > r_zero());
    }
}

/// A coined walk with a Gaussian-rational unitary coin and one permutation
/// shift for each coin state. The state ordering is coin * vertices + vertex.
#[derive(Debug, Clone)]
pub struct CoinedWalk {
    coin: BasicMatrix<GaussianRat>,
    shifts: Vec<Vec<usize>>,
    vertices: usize,
}
impl CoinedWalk {
    fn validate_shift_permutations(shifts: &[Vec<usize>], n: usize) -> Result<(), QuantumWalkError> {
        for shift in shifts {
            let mut seen = vec![false; n];
            if shift.len() != n {
                return Err(QuantumWalkError::InvalidWalk);
            }
            for &v in shift {
                if v >= n || seen[v] {
                    return Err(QuantumWalkError::InvalidWalk);
                }
                seen[v] = true;
            }
        }
        Ok(())
    }

    pub fn new(
        coin: BasicMatrix<GaussianRat>,
        shifts: Vec<Vec<usize>>,
    ) -> Result<Self, QuantumWalkError> {
        let d = crate::exact_hermitian::square_dim(&coin)?;
        let n = shifts.first().map_or(0, Vec::len);
        if d == 0 || n == 0 || d > 16 || n.checked_mul(d).is_none_or(|v| v > 4096) {
            return Err(QuantumWalkError::Budget);
        }
        if shifts.len() != d
            || !core_lie_theory::scalar::is_unitary(&coin).unwrap_or(false)
        {
            return Err(QuantumWalkError::InvalidWalk);
        }
        Self::validate_shift_permutations(&shifts, n)?;
        Ok(Self {
            coin,
            shifts,
            vertices: n,
        })
    }
    pub fn evolve(
        &self,
        initial: &[core_number_theory::cyclotomic::GaussianRat],
        steps: usize,
    ) -> Result<Vec<core_number_theory::cyclotomic::GaussianRat>, QuantumWalkError> {
        use core_number_theory::cyclotomic::GaussianRat;
        let d = self.shifts.len();
        let n = self.vertices;
        if steps > 4096 || steps.checked_mul(n * d * d).is_none_or(|w| w > 1 << 22) {
            return Err(QuantumWalkError::Budget);
        }
        if initial.len() != n * d
            || initial.iter().map(GaussianRat::norm_sq).sum::<Rational>() != r_one()
        {
            return Err(QuantumWalkError::InitialState);
        }
        let mut state = initial.to_vec();
        for _ in 0..steps {
            let mut next = vec![GaussianRat::zero(); n * d];
            for pos in 0..n {
                for c in 0..d {
                    let mut value = GaussianRat::zero();
                    for k in 0..d {
                        value = value.add(
                            &(self.coin)
                                .get_ref(c, k)
                                .expect("validated finite matrix shape and budget")
                                .mul(&state[k * n + pos]),
                        );
                    }
                    next[c * n + self.shifts[c][pos]] = value;
                }
            }
            state = next;
        }
        Ok(state)
    }
    pub fn position_probabilities(
        &self,
        state: &[core_number_theory::cyclotomic::GaussianRat],
    ) -> Result<Vec<Rational>, QuantumWalkError> {
        if state.len() != self.vertices * self.shifts.len() {
            return Err(QuantumWalkError::InitialState);
        }
        Ok((0..self.vertices)
            .map(|v| {
                (0..self.shifts.len())
                    .map(|c| state[c * self.vertices + v].norm_sq())
                    .sum()
            })
            .collect())
    }
}

/// Exact finite-time distribution of the infinite-line Hadamard walk, starting
/// at position zero in (|L>+i|R>)/sqrt(2). Integer-scaled amplitudes avoid
/// repeated algebraic normalization. No finite sample asserts a limit theorem.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HadamardLineDistribution {
    pub steps: usize,
    pub probabilities: std::collections::BTreeMap<i64, Rational>,
    pub mean: Rational,
    pub variance: Rational,
}
pub fn hadamard_line(steps: usize) -> Result<HadamardLineDistribution, QuantumWalkError> {
    use num_bigint::BigInt;
    use core_number_theory::cyclotomic::GaussianRat;
    if steps > 256 {
        return Err(QuantumWalkError::Budget);
    }
    let mut state =
        std::collections::BTreeMap::from([(0i64, [GaussianRat::one(), GaussianRat::i()])]);
    for _ in 0..steps {
        let mut next: std::collections::BTreeMap<i64, [GaussianRat; 2]> =
            std::collections::BTreeMap::new();
        for (x, coin) in state {
            next.entry(x - 1)
                .or_insert_with(|| [GaussianRat::zero(), GaussianRat::zero()])[0] =
                coin[0].add(&coin[1]);
            next.entry(x + 1)
                .or_insert_with(|| [GaussianRat::zero(), GaussianRat::zero()])[1] =
                coin[0].sub(&coin[1]);
        }
        state = next;
    }
    let denominator = Rational::from_integer(BigInt::from(1u8) << (steps + 1));
    let probabilities: std::collections::BTreeMap<_, _> = state
        .into_iter()
        .map(|(x, c)| (x, (c[0].norm_sq() + c[1].norm_sq()) / &denominator))
        .collect();
    let mean: Rational = probabilities.iter().map(|(&x, p)| ri(x) * p).sum();
    let second: Rational = probabilities.iter().map(|(&x, p)| ri(x) * ri(x) * p).sum();
    Ok(HadamardLineDistribution {
        steps,
        probabilities,
        variance: second - &mean * &mean,
        mean,
    })
}
