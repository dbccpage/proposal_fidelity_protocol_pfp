//! Finite Markov chains: classes, recurrence, period, stationary laws, absorption and mixing.
//!
//! A [`MarkovChain`] is a square [`StochasticMap`]. Everything here is exact:
//!
//! - the communicating classes (strongly connected components of the support graph, found by
//!   Tarjan's algorithm), which classes are closed, recurrent versus transient states, and the
//!   period of a class (the gcd of its cycle lengths, from breadth-first levels);
//! - the stationary law of every closed class, and of the whole chain when it has exactly one
//!   closed class, by an exact linear solve (`core_linear_algebra::solve_in_image`) whose
//!   solution is replayed against `pi P = pi`;
//! - absorption probabilities into each closed class and expected absorption times from the
//!   transient states, by exact solves of `(I - Q) x = b`;
//! - expected hitting and return times, time reversal and detailed balance;
//! - mixing diagnostics with no limits: the exact total variation distance to the stationary
//!   law after `k` steps, and the smallest `k` within a declared step bound for which it is at
//!   most a given `epsilon`, refused with a typed error otherwise.
//!
//! Nothing is a limit or an approximation. A question about `k -> infinity` is answered by a
//! finite computation on the support graph or by a linear solve, or it is not answered.
//!
//! AuthorityEffect: None.

use linear_algebra::backend::basic_matrix::{BasicMatrix, MatrixError};
use linear_algebra::linear_algebra::image_kernel::{
    solve_in_image, ExactLinearAlgebraError, ExactRowReduction, ImageMembership,
};
use num_integer::Integer;
use num_traits::{One, Signed, Zero};
use core_number_theory::rational::Rational;

use crate::error::ClassicalShadowError;
use crate::simplex::ProbabilitySimplex;
use crate::stochastic_map::StochasticMap;

/// The largest step count an exact mixing computation accepts.
///
/// The entries of `P^k` have denominators that grow linearly in bit length with `k`, so the
/// bound keeps a mixing profile a finite, predictable amount of exact arithmetic.
pub const MAX_EXACT_STEPS: u32 = 1024;

/// Refusals of Markov-chain analysis.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MarkovChainError {
    /// A chain needs a square kernel.
    #[error("a chain needs a square kernel, found {source_n} x {target_n}")]
    NotSquare { source_n: usize, target_n: usize },
    /// A state index lies outside the chain.
    #[error("state {index} is outside 0..{bound}")]
    StateOutOfRange { index: usize, bound: usize },
    /// The stationary distribution is unique only with exactly one closed class.
    #[error("the chain has {closed_classes} closed communicating classes, so its stationary distribution is not unique")]
    NotUnique { closed_classes: usize },
    /// Some state cannot reach the target, so its hitting time is infinite.
    #[error("state {from} cannot reach state {target}, so its hitting time is infinite")]
    TargetUnreachable { from: usize, target: usize },
    /// A linear system that theory says has a unique solution had none.
    #[error("the system for {what} has no solution")]
    NoSolution { what: &'static str },
    /// A linear system that theory says has a unique solution had several.
    #[error("the system for {what} has more than one solution")]
    SolutionNotUnique { what: &'static str },
    /// A computed solution failed its replay check.
    #[error("the solution for {what} failed its exact replay")]
    ReplayFailed { what: &'static str },
    /// The total variation distance to stationarity did not reach `epsilon` in the allowed steps.
    #[error("the distance to stationarity is still above epsilon after {max_steps} steps")]
    NotMixedWithin { max_steps: u32 },
    /// A bounded operation was asked for more than its declared limit.
    #[error("{what} {requested} exceeds the limit {limit}")]
    LimitExceeded {
        what: &'static str,
        requested: usize,
        limit: usize,
    },
    /// A stochastic-map or simplex refusal.
    #[error("probability refusal: {0}")]
    Probability(#[from] ClassicalShadowError),
    /// Dense matrix storage refused a shape.
    #[error("matrix storage refusal: {0}")]
    Matrix(#[from] MatrixError),
    /// Exact elimination refused.
    #[error("linear algebra refusal: {0}")]
    LinearAlgebra(#[from] ExactLinearAlgebraError),
}

/// A communicating class: a maximal set of states that reach one another.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CommunicatingClass {
    states: Vec<usize>,
    closed: bool,
    period: Option<usize>,
}

impl CommunicatingClass {
    /// The states of the class, increasing.
    pub fn states(&self) -> &[usize] {
        &self.states
    }

    /// No transition leaves the class. A state of a closed class is recurrent, every other
    /// state of a finite chain is transient.
    pub fn is_closed(&self) -> bool {
        self.closed
    }

    /// The gcd of the lengths of the cycles inside the class, or `None` when the class holds
    /// no cycle (a single state with no self-loop).
    pub fn period(&self) -> Option<usize> {
        self.period
    }
}

/// Whether a state of a finite chain is visited infinitely often or only finitely often.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum StateKind {
    /// The state lies in a closed class: started there, the chain returns with probability one.
    Recurrent,
    /// The state lies outside every closed class: the chain leaves it for good with
    /// probability one.
    Transient,
}

/// One closed class together with its stationary distribution on the whole state space.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ClassStationary {
    /// The states of the closed class, increasing.
    pub class: Vec<usize>,
    /// The unique stationary distribution supported on the class; zero outside it.
    pub distribution: ProbabilitySimplex,
}

/// Absorption of the transient states into the closed classes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AbsorptionAnalysis {
    /// The transient states, increasing.
    pub transient: Vec<usize>,
    /// The closed classes, ordered by smallest state.
    pub closed_classes: Vec<Vec<usize>>,
    /// `probabilities[t][k]`: the probability that the chain started at `transient[t]` is
    /// eventually absorbed into `closed_classes[k]`. Each row sums to one.
    pub probabilities: Vec<Vec<Rational>>,
    /// `expected_steps[t]`: the expected number of steps before the chain started at
    /// `transient[t]` first enters a closed class.
    pub expected_steps: Vec<Rational>,
}

/// A finite Markov chain: a square row-stochastic kernel.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct MarkovChain {
    kernel: StochasticMap,
}

/// The states `j` with `P[i][j] > 0`, for each `i`.
fn support_graph(kernel: &StochasticMap) -> Vec<Vec<usize>> {
    kernel
        .rows()
        .iter()
        .map(|row| {
            row.iter()
                .enumerate()
                .filter(|(_, p)| p.is_positive())
                .map(|(j, _)| j)
                .collect()
        })
        .collect()
}

fn advance_dfs_step(
    v: usize,
    edge_idx: usize,
    adjacency: &[Vec<usize>],
    unvisited: usize,
    next_index: &mut usize,
    index: &mut [usize],
    lowlink: &mut [usize],
    stack: &mut Vec<usize>,
    on_stack: &mut [bool],
    frames: &mut Vec<(usize, usize)>,
) {
    let w = adjacency[v][edge_idx];
    if index[w] == unvisited {
        index[w] = *next_index;
        lowlink[w] = *next_index;
        *next_index += 1;
        stack.push(w);
        on_stack[w] = true;
        frames.push((w, 0));
    } else if on_stack[w] {
        lowlink[v] = lowlink[v].min(index[w]);
    }
}

fn pop_scc_component(
    v: usize,
    stack: &mut Vec<usize>,
    on_stack: &mut [bool],
    components: &mut Vec<Vec<usize>>,
) {
    let mut component = Vec::new();
    while let Some(member) = stack.pop() {
        on_stack[member] = false;
        component.push(member);
        if member == v {
            break;
        }
    }
    component.sort_unstable();
    components.push(component);
}

/// Strongly connected components by Tarjan's algorithm, iteratively, so the recursion depth
/// does not grow with the number of states. Components and their members are returned in
/// increasing order of smallest member.
fn strongly_connected_components(adjacency: &[Vec<usize>]) -> Vec<Vec<usize>> {
    let n = adjacency.len();
    let unvisited = usize::MAX;
    let mut index = vec![unvisited; n];
    let mut lowlink = vec![0usize; n];
    let mut on_stack = vec![false; n];
    let mut stack: Vec<usize> = Vec::new();
    let mut components: Vec<Vec<usize>> = Vec::new();
    let mut next_index = 0usize;

    for root in 0..n {
        if index[root] != unvisited {
            continue;
        }
        index[root] = next_index;
        lowlink[root] = next_index;
        next_index += 1;
        stack.push(root);
        on_stack[root] = true;
        // Each frame is (vertex, position of the next neighbour to explore).
        let mut frames: Vec<(usize, usize)> = vec![(root, 0)];
        while let Some(frame) = frames.last_mut() {
            let v = frame.0;
            if frame.1 < adjacency[v].len() {
                let edge_idx = frame.1;
                frame.1 += 1;
                advance_dfs_step(
                    v,
                    edge_idx,
                    adjacency,
                    unvisited,
                    &mut next_index,
                    &mut index,
                    &mut lowlink,
                    &mut stack,
                    &mut on_stack,
                    &mut frames,
                );
            } else {
                frames.pop();
                if lowlink[v] == index[v] {
                    pop_scc_component(v, &mut stack, &mut on_stack, &mut components);
                }
                if let Some(parent) = frames.last() {
                    lowlink[parent.0] = lowlink[parent.0].min(lowlink[v]);
                }
            }
        }
    }
    components.sort_by_key(|component| component[0]);
    components
}

/// The gcd of the lengths of the cycles inside `class`, from breadth-first levels: with
/// `level` the distance from the class's smallest state, every edge `u -> v` inside the class
/// contributes `level[u] + 1 - level[v]`, and the gcd of these is the period.
fn class_period(adjacency: &[Vec<usize>], class: &[usize]) -> Option<usize> {
    let mut level = vec![usize::MAX; adjacency.len()];
    let mut in_class = vec![false; adjacency.len()];
    for &s in class {
        in_class[s] = true;
    }
    let root = class[0];
    level[root] = 0;
    let mut queue = std::collections::VecDeque::from([root]);
    while let Some(u) = queue.pop_front() {
        for &v in &adjacency[u] {
            if in_class[v] && level[v] == usize::MAX {
                level[v] = level[u] + 1;
                queue.push_back(v);
            }
        }
    }
    let mut g = 0usize;
    for &u in class {
        for &v in &adjacency[u] {
            if in_class[v] {
                g = g.gcd(&(level[u] + 1).abs_diff(level[v]));
            }
        }
    }
    (g > 0).then_some(g)
}

/// The unique solution of `system * x = target`, refused when there is none or several.
fn solve_unique(
    system: &BasicMatrix<Rational>,
    target: &[Rational],
    what: &'static str,
) -> Result<Vec<Rational>, MarkovChainError> {
    if system.rank()? != system.cols() {
        return Err(MarkovChainError::SolutionNotUnique { what });
    }
    match solve_in_image(system, target)? {
        ImageMembership::InImage(witness) => Ok(witness.potential),
        ImageMembership::NotInImage { .. } => Err(MarkovChainError::NoSolution { what }),
    }
}

impl MarkovChain {
    /// A chain from a square kernel.
    pub fn try_new(kernel: StochasticMap) -> Result<Self, MarkovChainError> {
        if !kernel.is_endomorphism() {
            return Err(MarkovChainError::NotSquare {
                source_n: kernel.source_n(),
                target_n: kernel.target_n(),
            });
        }
        Ok(Self { kernel })
    }

    /// A chain from rows of transition probabilities.
    pub fn from_rows(
        rows: Vec<Vec<Rational>>,
        label: impl Into<String>,
    ) -> Result<Self, MarkovChainError> {
        let n = rows.len();
        let kernel = StochasticMap::try_from_rows(n, n, rows, label)?;
        Self::try_new(kernel)
    }

    /// The transition kernel.
    pub fn kernel(&self) -> &StochasticMap {
        &self.kernel
    }

    /// The number of states.
    pub fn n(&self) -> usize {
        self.kernel.source_n()
    }

    /// One step: `p -> p P`.
    pub fn step(&self, p: &ProbabilitySimplex) -> Result<ProbabilitySimplex, MarkovChainError> {
        Ok(self.kernel.apply(p)?)
    }

    /// The law after `steps` steps, `p P^steps`, by repeated application.
    pub fn distribution_after(
        &self,
        initial: &ProbabilitySimplex,
        steps: u32,
    ) -> Result<ProbabilitySimplex, MarkovChainError> {
        if steps > MAX_EXACT_STEPS {
            return Err(MarkovChainError::LimitExceeded {
                what: "step count",
                requested: steps as usize,
                limit: MAX_EXACT_STEPS as usize,
            });
        }
        let mut current = initial.clone();
        for _ in 0..steps {
            current = self.step(&current)?;
        }
        Ok(current)
    }

    // --- structure -------------------------------------------------------------------

    /// The communicating classes, ordered by smallest state, each with its closedness and
    /// period.
    pub fn classes(&self) -> Vec<CommunicatingClass> {
        let adjacency = support_graph(&self.kernel);
        let components = strongly_connected_components(&adjacency);
        let mut class_of = vec![0usize; self.n()];
        for (k, component) in components.iter().enumerate() {
            for &s in component {
                class_of[s] = k;
            }
        }
        components
            .into_iter()
            .enumerate()
            .map(|(k, states)| {
                let closed = states
                    .iter()
                    .all(|&s| adjacency[s].iter().all(|&t| class_of[t] == k));
                let period = class_period(&adjacency, &states);
                CommunicatingClass {
                    states,
                    closed,
                    period,
                }
            })
            .collect()
    }

    /// The closed classes, ordered by smallest state.
    pub fn closed_classes(&self) -> Vec<Vec<usize>> {
        self.classes()
            .into_iter()
            .filter(|c| c.closed)
            .map(|c| c.states)
            .collect()
    }

    /// Recurrent or transient, for each state.
    pub fn state_kinds(&self) -> Vec<StateKind> {
        let mut kinds = vec![StateKind::Transient; self.n()];
        for class in self.classes().iter().filter(|c| c.closed) {
            for &s in &class.states {
                kinds[s] = StateKind::Recurrent;
            }
        }
        kinds
    }

    /// The transient states, increasing.
    pub fn transient_states(&self) -> Vec<usize> {
        self.state_kinds()
            .iter()
            .enumerate()
            .filter(|(_, kind)| **kind == StateKind::Transient)
            .map(|(s, _)| s)
            .collect()
    }

    /// The absorbing states: `P[i][i] = 1`.
    pub fn absorbing_states(&self) -> Vec<usize> {
        self.kernel
            .rows()
            .iter()
            .enumerate()
            .filter(|(i, row)| row[*i].is_one())
            .map(|(i, _)| i)
            .collect()
    }

    /// Every state reaches every other: there is exactly one class.
    pub fn is_irreducible(&self) -> bool {
        self.classes().len() == 1
    }

    /// The period of an irreducible chain, `None` when the chain is reducible.
    pub fn period(&self) -> Option<usize> {
        let mut classes = self.classes();
        if classes.len() == 1 {
            classes.pop().and_then(|c| c.period)
        } else {
            None
        }
    }

    /// Irreducible with period one.
    pub fn is_aperiodic(&self) -> bool {
        self.period() == Some(1)
    }

    /// Some power of the kernel has only positive entries (a regular chain). For a chain of
    /// `n` states this holds exactly when the chain is irreducible and aperiodic, and then
    /// `P^k > 0` already at `k = (n - 1)^2 + 1` (Wielandt).
    pub fn is_primitive(&self) -> bool {
        self.is_aperiodic()
    }
}

fn boolean_matrix_multiply(a: &[Vec<bool>], b: &[Vec<bool>], n: usize) -> Vec<Vec<bool>> {
    let mut next = vec![vec![false; n]; n];
    for i in 0..n {
        for (m, &reaches) in a[i].iter().enumerate() {
            if !reaches {
                continue;
            }
            for j in 0..n {
                next[i][j] |= b[m][j];
            }
        }
    }
    next
}

impl MarkovChain {
    /// The smallest `k <= max_power` with every entry of `P^k` positive, computed on the
    /// support (boolean matrix products), or `None` when there is no such `k`.
    pub fn first_positive_power(&self, max_power: u32) -> Option<u32> {
        let adjacency = support_graph(&self.kernel);
        let n = self.n();
        let mut step = vec![vec![false; n]; n];
        for (i, successors) in adjacency.iter().enumerate() {
            for &j in successors {
                step[i][j] = true;
            }
        }
        let mut power = step.clone();
        for k in 1..=max_power {
            if power.iter().all(|row| row.iter().all(|&b| b)) {
                return Some(k);
            }
            power = boolean_matrix_multiply(&power, &step, n);
        }
        None
    }

    // --- stationary laws ---------------------------------------------------------------

    /// `p P = p`, exactly.
    pub fn is_stationary(&self, p: &ProbabilitySimplex) -> Result<bool, MarkovChainError> {
        Ok(self.kernel.apply(p)? == *p)
    }

    /// Detailed balance `pi_i P_ij = pi_j P_ji` for every pair, which implies that `pi` is
    /// stationary.
    pub fn is_reversible_with(&self, pi: &ProbabilitySimplex) -> Result<bool, MarkovChainError> {
        if pi.n() != self.n() {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: pi.n(),
                right: self.n(),
            }
            .into());
        }
        let rows = self.kernel.rows();
        let p = pi.probs();
        Ok((0..self.n())
            .all(|i| (i + 1..self.n()).all(|j| &p[i] * &rows[i][j] == &p[j] * &rows[j][i])))
    }

    /// The stationary distribution of one closed class, on the whole state space.
    fn class_stationary(&self, class: &[usize]) -> Result<ProbabilitySimplex, MarkovChainError> {
        const WHAT: &str = "the stationary law of a closed class";
        let k = class.len();
        let rows = self.kernel.rows();
        // Unknown pi on the class. Equation r is sum_c (P[c][r] - delta_rc) pi_c = 0; the
        // last row is the normalisation sum_c pi_c = 1.
        let mut data = Vec::with_capacity((k + 1) * k);
        for r in 0..k {
            for c in 0..k {
                let mut entry = rows[class[c]][class[r]].clone();
                if r == c {
                    entry -= Rational::one();
                }
                data.push(entry);
            }
        }
        data.extend(std::iter::repeat_with(Rational::one).take(k));
        let system = BasicMatrix::from_row_major(k + 1, k, data)?;
        let mut target = vec![Rational::zero(); k + 1];
        target[k] = Rational::one();
        let on_class = solve_unique(&system, &target, WHAT)?;

        let mut full = vec![Rational::zero(); self.n()];
        for (c, value) in on_class.into_iter().enumerate() {
            full[class[c]] = value;
        }
        let distribution = ProbabilitySimplex::try_new(full)?;
        if !self.is_stationary(&distribution)? {
            return Err(MarkovChainError::ReplayFailed { what: WHAT });
        }
        Ok(distribution)
    }

    /// The stationary distribution of every closed class, ordered by smallest state. Every
    /// stationary distribution of the chain is a convex combination of these.
    pub fn closed_class_stationary_distributions(
        &self,
    ) -> Result<Vec<ClassStationary>, MarkovChainError> {
        self.closed_classes()
            .into_iter()
            .map(|class| {
                let distribution = self.class_stationary(&class)?;
                Ok(ClassStationary {
                    class,
                    distribution,
                })
            })
            .collect()
    }

    /// The unique stationary distribution, refused when the chain has several closed classes.
    pub fn stationary_distribution(&self) -> Result<ProbabilitySimplex, MarkovChainError> {
        let mut closed = self.closed_classes();
        if closed.len() != 1 {
            return Err(MarkovChainError::NotUnique {
                closed_classes: closed.len(),
            });
        }
        let class = closed.remove(0);
        self.class_stationary(&class)
    }

    /// The matrix `P^T - I` whose kernel is the space of stationary vectors (not
    /// necessarily normalised or nonnegative), in dense storage.
    pub fn stationarity_matrix(&self) -> Result<BasicMatrix<Rational>, MarkovChainError> {
        let n = self.n();
        let rows = self.kernel.rows();
        let mut data = Vec::with_capacity(n * n);
        for r in 0..n {
            for c in 0..n {
                let mut entry = rows[c][r].clone();
                if r == c {
                    entry -= Rational::one();
                }
                data.push(entry);
            }
        }
        Ok(BasicMatrix::from_row_major(n, n, data)?)
    }

    /// The time reversal `P*[i][j] = pi_j P[j][i] / pi_i` against a positive `pi`.
    ///
    /// It is stochastic exactly when `pi` is stationary; otherwise the refused row is
    /// reported. The chain is reversible with `pi` exactly when `P* = P`.
    pub fn time_reversal(&self, pi: &ProbabilitySimplex) -> Result<MarkovChain, MarkovChainError> {
        if pi.n() != self.n() {
            return Err(ClassicalShadowError::ShapeMismatch {
                left: pi.n(),
                right: self.n(),
            }
            .into());
        }
        if let Some(index) = pi.probs().iter().position(Zero::is_zero) {
            return Err(ClassicalShadowError::ZeroMass { index }.into());
        }
        let rows = self.kernel.rows();
        let p = pi.probs();
        let reversed: Vec<Vec<Rational>> = (0..self.n())
            .map(|i| (0..self.n()).map(|j| &p[j] * &rows[j][i] / &p[i]).collect())
            .collect();
        Self::from_rows(reversed, format!("reverse({})", self.kernel.label()))
    }
}

fn build_identity_minus_submatrix(
    states: &[usize],
    rows: &[Vec<Rational>],
) -> Result<BasicMatrix<Rational>, MarkovChainError> {
    let m = states.len();
    let mut data = Vec::with_capacity(m * m);
    for (r, &i) in states.iter().enumerate() {
        for (c, &j) in states.iter().enumerate() {
            let mut entry = -rows[i][j].clone();
            if r == c {
                entry += Rational::one();
            }
            data.push(entry);
        }
    }
    BasicMatrix::from_row_major(m, m, data).map_err(Into::into)
}
    // --- absorption and hitting ----------------------------------------------------------

fn validate_absorption_probabilities(
    probabilities: &[Vec<Rational>],
) -> Result<(), MarkovChainError> {
    for row in probabilities {
        let sum: Rational = row.iter().sum();
        if !sum.is_one() || row.iter().any(Signed::is_negative) {
            return Err(MarkovChainError::ReplayFailed {
                what: "absorption probabilities",
            });
        }
    }
    Ok(())
}

fn verify_target_reachable(
    target: usize,
    n: usize,
    adjacency: &[Vec<usize>],
) -> Result<(), MarkovChainError> {
    let mut predecessors = vec![Vec::new(); n];
    for (i, successors) in adjacency.iter().enumerate() {
        for &j in successors {
            predecessors[j].push(i);
        }
    }
    let mut reaches = vec![false; n];
    reaches[target] = true;
    let mut queue = std::collections::VecDeque::from([target]);
    while let Some(v) = queue.pop_front() {
        for &u in &predecessors[v] {
            if !reaches[u] {
                reaches[u] = true;
                queue.push_back(u);
            }
        }
    }
    if let Some(from) = reaches.iter().position(|&r| !r) {
        return Err(MarkovChainError::TargetUnreachable { from, target });
    }
    Ok(())
}

impl MarkovChain {
    /// Absorption probabilities into each closed class and expected absorption times, from
    /// every transient state.
    pub fn absorption_analysis(&self) -> Result<AbsorptionAnalysis, MarkovChainError> {
        let closed_classes = self.closed_classes();
        let transient = self.transient_states();
        if transient.is_empty() {
            return Ok(AbsorptionAnalysis {
                transient,
                closed_classes,
                probabilities: Vec::new(),
                expected_steps: Vec::new(),
            });
        }
        let rows = self.kernel.rows();
        let t = transient.len();
        // I - Q, with Q the kernel restricted to the transient states.
        let system = build_identity_minus_submatrix(&transient, rows)?;

        let mut probabilities = vec![vec![Rational::zero(); closed_classes.len()]; t];
        for (k, class) in closed_classes.iter().enumerate() {
            let target: Vec<Rational> = transient
                .iter()
                .map(|&i| class.iter().map(|&j| &rows[i][j]).sum::<Rational>())
                .collect();
            let column = solve_unique(&system, &target, "absorption probabilities")?;
            for (row, value) in probabilities.iter_mut().zip(column) {
                row[k] = value;
            }
        }
        validate_absorption_probabilities(&probabilities)?;
        let expected_steps = solve_unique(
            &system,
            &vec![Rational::one(); t],
            "expected absorption steps",
        )?;
        if expected_steps.iter().any(|s| *s < Rational::one()) {
            return Err(MarkovChainError::ReplayFailed {
                what: "expected absorption steps",
            });
        }
        Ok(AbsorptionAnalysis {
            transient,
            closed_classes,
            probabilities,
            expected_steps,
        })
    }

    /// `h[i]`: the expected number of steps for the chain started at `i` to first reach
    /// `target`, with `h[target] = 0`. Refused when some state cannot reach `target`.
    pub fn expected_hitting_times(&self, target: usize) -> Result<Vec<Rational>, MarkovChainError> {
        let n = self.n();
        if target >= n {
            return Err(MarkovChainError::StateOutOfRange {
                index: target,
                bound: n,
            });
        }
        // Every state must reach the target: search backwards from it.
        let adjacency = support_graph(&self.kernel);
        verify_target_reachable(target, n, &adjacency)?;

        let others: Vec<usize> = (0..n).filter(|&i| i != target).collect();
        let mut times = vec![Rational::zero(); n];
        if others.is_empty() {
            return Ok(times);
        }
        let rows = self.kernel.rows();
        let m = others.len();
        let system = build_identity_minus_submatrix(&others, rows)?;
        let solution = solve_unique(&system, &vec![Rational::one(); m], "expected hitting times")?;
        for (&i, value) in others.iter().zip(solution) {
            times[i] = value;
        }
        Ok(times)
    }

    /// The expected number of steps, started at `state`, to return to `state`: one plus the
    /// expected hitting time of `state` after the first step. For an irreducible chain this is
    /// `1 / pi_state` (Kac).
    pub fn expected_return_time(&self, state: usize) -> Result<Rational, MarkovChainError> {
        let times = self.expected_hitting_times(state)?;
        let rows = self.kernel.rows();
        Ok(Rational::one()
            + rows[state]
                .iter()
                .zip(&times)
                .map(|(p, h)| p * h)
                .sum::<Rational>())
    }

    // --- mixing ------------------------------------------------------------------------

    /// `d(k) = max_i TV(P^k(i, .), pi)` for `k = 1, ..., max_steps`, against the unique
    /// stationary distribution.
    ///
    /// Exact. `d(k) <= delta(P)^k` for the Dobrushin coefficient `delta`, and `d` does not
    /// tend to zero for a periodic chain.
    pub fn distance_profile(&self, max_steps: u32) -> Result<Vec<Rational>, MarkovChainError> {
        if max_steps > MAX_EXACT_STEPS {
            return Err(MarkovChainError::LimitExceeded {
                what: "mixing steps",
                requested: max_steps as usize,
                limit: MAX_EXACT_STEPS as usize,
            });
        }
        let pi = self.stationary_distribution()?;
        let mut profile = Vec::with_capacity(max_steps as usize);
        let mut power = self.kernel.clone();
        for k in 1..=max_steps {
            if k > 1 {
                power = power.compose(&self.kernel)?;
            }
            profile.push(self.worst_distance(&power, &pi)?);
        }
        Ok(profile)
    }

    fn worst_distance(
        &self,
        power: &StochasticMap,
        pi: &ProbabilitySimplex,
    ) -> Result<Rational, MarkovChainError> {
        let mut worst = Rational::zero();
        for i in 0..power.source_n() {
            let d = power.conditional(i)?.total_variation(pi)?;
            if d > worst {
                worst = d;
            }
        }
        Ok(worst)
    }

    /// The smallest `k <= max_steps` with `d(k) <= epsilon`, or a typed refusal when there is
    /// none within the bound.
    pub fn mixing_time(&self, epsilon: &Rational, max_steps: u32) -> Result<u32, MarkovChainError> {
        let profile = self.distance_profile(max_steps)?;
        let index = profile
            .iter()
            .position(|d| d <= epsilon)
            .ok_or(MarkovChainError::NotMixedWithin { max_steps })?;
        // `index < max_steps <= MAX_EXACT_STEPS`, so the step count fits in `u32`.
        u32::try_from(index + 1).map_err(|_| MarkovChainError::LimitExceeded {
            what: "mixing steps",
            requested: index + 1,
            limit: MAX_EXACT_STEPS as usize,
        })
    }
}

// Origin: engine/crates_rs/core_finite_probability/src/markov_chain.rs
// Claim: urn:core:crates_rs:core-finite-probability:markov-chain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_support::stochastic;
    use core_number_theory::rational::{ri, rq};

    fn chain(rows: &[&[(i64, i64)]]) -> MarkovChain {
        MarkovChain::try_new(stochastic(rows)).unwrap()
    }

    /// Eight states: a transient pair {0, 1}, a closed class {2, 3} of period two, a closed
    /// aperiodic class {4, 5, 6} and an absorbing state 7.
    fn mixed_chain() -> MarkovChain {
        let z = (0, 1);
        chain(&[
            &[z, (1, 2), (1, 4), z, z, z, z, (1, 4)],
            &[(1, 4), z, z, (1, 2), (1, 4), z, z, z],
            &[z, z, z, (1, 1), z, z, z, z],
            &[z, z, (1, 1), z, z, z, z, z],
            &[z, z, z, z, (1, 2), (1, 2), z, z],
            &[z, z, z, z, z, z, (1, 1), z],
            &[z, z, z, z, (1, 1), z, z, z],
            &[z, z, z, z, z, z, z, (1, 1)],
        ])
    }

    #[test]
    fn a_non_square_kernel_is_not_a_chain() {
        let rectangular = stochastic(&[&[(1, 2), (1, 2), (0, 1)], &[(0, 1), (1, 2), (1, 2)]]);
        assert_eq!(
            MarkovChain::try_new(rectangular),
            Err(MarkovChainError::NotSquare {
                source_n: 2,
                target_n: 3
            })
        );
        assert_eq!(
            MarkovChain::from_rows(vec![vec![rq(1, 2), rq(1, 3)]], "bad"),
            Err(MarkovChainError::Probability(
                ClassicalShadowError::DimensionMismatch {
                    expected: 1,
                    actual: 2
                }
            ))
        );
    }

    #[test]
    fn classes_closedness_periods_and_state_kinds_have_their_hand_values() {
        let c = mixed_chain();
        let classes = c.classes();
        let summary: Vec<(Vec<usize>, bool, Option<usize>)> = classes
            .iter()
            .map(|k| (k.states().to_vec(), k.is_closed(), k.period()))
            .collect();
        assert_eq!(
            summary,
            vec![
                (vec![0, 1], false, Some(2)),
                (vec![2, 3], true, Some(2)),
                (vec![4, 5, 6], true, Some(1)),
                (vec![7], true, Some(1)),
            ]
        );
        assert_eq!(c.closed_classes(), vec![vec![2, 3], vec![4, 5, 6], vec![7]]);
        assert_eq!(c.transient_states(), vec![0, 1]);
        assert_eq!(c.absorbing_states(), vec![7]);
        assert_eq!(
            c.state_kinds(),
            vec![
                StateKind::Transient,
                StateKind::Transient,
                StateKind::Recurrent,
                StateKind::Recurrent,
                StateKind::Recurrent,
                StateKind::Recurrent,
                StateKind::Recurrent,
                StateKind::Recurrent,
            ]
        );
        assert!(!c.is_irreducible());
        assert_eq!(c.period(), None);
        assert!(!c.is_primitive());
    }

    #[test]
    fn a_single_state_without_a_self_loop_has_no_period_and_is_not_a_chain_class_with_a_cycle() {
        // 0 -> 1 -> 1: state 0 is a trivial transient class with no cycle.
        let c = chain(&[&[(0, 1), (1, 1)], &[(0, 1), (1, 1)]]);
        let classes = c.classes();
        assert_eq!(classes[0].states(), &[0]);
        assert_eq!(classes[0].period(), None);
        assert!(!classes[0].is_closed());
        assert_eq!(classes[1].period(), Some(1));
        assert!(classes[1].is_closed());
    }

    #[test]
    fn a_long_path_does_not_overflow_the_stack_of_the_component_search() {
        // A directed path of 20000 states ending in a self-loop: every state is its own class.
        let n = 20_000usize;
        let mut adjacency = vec![Vec::new(); n];
        for (i, successors) in adjacency.iter_mut().enumerate() {
            successors.push(if i + 1 < n { i + 1 } else { i });
        }
        let components = strongly_connected_components(&adjacency);
        assert_eq!(components.len(), n);
        assert!(components.iter().enumerate().all(|(k, c)| c == &vec![k]));
    }

    #[test]
    fn the_stationary_laws_of_the_closed_classes_are_exact_and_the_chain_has_none_unique() {
        let c = mixed_chain();
        let laws = c.closed_class_stationary_distributions().unwrap();
        assert_eq!(laws.len(), 3);
        let mass = |l: &ClassStationary| l.distribution.probs().to_vec();
        let z = ri(0);
        assert_eq!(
            mass(&laws[0]),
            vec![
                z.clone(),
                z.clone(),
                rq(1, 2),
                rq(1, 2),
                z.clone(),
                z.clone(),
                z.clone(),
                z.clone()
            ]
        );
        assert_eq!(
            mass(&laws[1]),
            vec![
                z.clone(),
                z.clone(),
                z.clone(),
                z.clone(),
                rq(1, 2),
                rq(1, 4),
                rq(1, 4),
                z.clone()
            ]
        );
        assert_eq!(
            mass(&laws[2]),
            vec![
                z.clone(),
                z.clone(),
                z.clone(),
                z.clone(),
                z.clone(),
                z.clone(),
                z,
                ri(1)
            ]
        );
        for law in &laws {
            assert!(c.is_stationary(&law.distribution).unwrap());
        }
        assert_eq!(
            c.stationary_distribution(),
            Err(MarkovChainError::NotUnique { closed_classes: 3 })
        );
        // The dimension of the space of stationary vectors is the number of closed classes.
        let kernel_dimension = c
            .stationarity_matrix()
            .unwrap()
            .kernel_basis()
            .unwrap()
            .len();
        assert_eq!(kernel_dimension, 3);
    }

    #[test]
    fn absorption_probabilities_and_times_have_their_hand_values() {
        let analysis = mixed_chain().absorption_analysis().unwrap();
        assert_eq!(analysis.transient, vec![0, 1]);
        assert_eq!(
            analysis.closed_classes,
            vec![vec![2, 3], vec![4, 5, 6], vec![7]]
        );
        assert_eq!(
            analysis.probabilities,
            vec![
                vec![rq(4, 7), rq(1, 7), rq(2, 7)],
                vec![rq(9, 14), rq(2, 7), rq(1, 14)],
            ]
        );
        assert_eq!(analysis.expected_steps, vec![rq(12, 7), rq(10, 7)]);
    }

    #[test]
    fn a_chain_with_no_transient_state_has_an_empty_absorption_analysis() {
        let c = chain(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        let analysis = c.absorption_analysis().unwrap();
        assert!(analysis.transient.is_empty() && analysis.probabilities.is_empty());
        assert_eq!(analysis.closed_classes, vec![vec![0, 1]]);
    }

    #[test]
    fn hitting_times_are_refused_when_a_state_cannot_reach_the_target() {
        let c = mixed_chain();
        assert_eq!(
            c.expected_hitting_times(2),
            Err(MarkovChainError::TargetUnreachable { from: 4, target: 2 })
        );
        assert_eq!(
            c.expected_hitting_times(8),
            Err(MarkovChainError::StateOutOfRange { index: 8, bound: 8 })
        );
        // A one-state chain reaches its only state in zero steps.
        let one = chain(&[&[(1, 1)]]);
        assert_eq!(one.expected_hitting_times(0).unwrap(), vec![ri(0)]);
        assert_eq!(one.expected_return_time(0).unwrap(), ri(1));
    }

    #[test]
    fn the_time_reversal_needs_a_positive_stationary_law() {
        let c = chain(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        let pi = c.stationary_distribution().unwrap();
        assert_eq!(pi.probs(), &[rq(2, 5), rq(3, 5)]);
        // Not stationary: the reversal has a row that does not sum to one.
        let not_stationary = ProbabilitySimplex::try_new(vec![rq(1, 2), rq(1, 2)]).unwrap();
        assert!(matches!(
            c.time_reversal(&not_stationary),
            Err(MarkovChainError::Probability(
                ClassicalShadowError::RowNotNormalized { .. }
            ))
        ));
        // A zero-mass state has no reversal.
        let dirac = ProbabilitySimplex::try_new(vec![ri(1), ri(0)]).unwrap();
        assert_eq!(
            c.time_reversal(&dirac),
            Err(MarkovChainError::Probability(
                ClassicalShadowError::ZeroMass { index: 1 }
            ))
        );
        let wrong_size = ProbabilitySimplex::try_new(vec![rq(1, 3); 3]).unwrap();
        assert!(c.time_reversal(&wrong_size).is_err());
        assert!(c.is_reversible_with(&wrong_size).is_err());
    }

    #[test]
    fn step_counts_above_the_exact_limit_are_refused() {
        let c = chain(&[&[(1, 2), (1, 2)], &[(1, 3), (2, 3)]]);
        assert_eq!(
            c.distance_profile(MAX_EXACT_STEPS + 1),
            Err(MarkovChainError::LimitExceeded {
                what: "mixing steps",
                requested: (MAX_EXACT_STEPS + 1) as usize,
                limit: MAX_EXACT_STEPS as usize
            })
        );
        let start = ProbabilitySimplex::try_new(vec![ri(1), ri(0)]).unwrap();
        assert!(matches!(
            c.distribution_after(&start, MAX_EXACT_STEPS + 1),
            Err(MarkovChainError::LimitExceeded { .. })
        ));
        assert_eq!(c.distribution_after(&start, 0).unwrap(), start);
        assert_eq!(
            c.distribution_after(&start, 1).unwrap().probs(),
            &[rq(1, 2), rq(1, 2)]
        );
    }
}
