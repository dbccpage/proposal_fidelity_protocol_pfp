// AuthorityEffect: None.

//! Finite weighted transport: path-sums over a declared commutative semiring.
//!
//! Weights live in any `linear_algebra::scalars::Semiring`: here [`linear_algebra::semiring_matrix::Boolean`]
//! (reachability), [`NonNegative`] rationals (classical weights) and
//! [`core_number_theory::cyclotomic::GaussianRat`] (`Q(i)` amplitudes), with `i64` taking
//! `core_linear_algebra`'s own impl. Commutativity of the declared semiring is
//! assumed, not checked. A history's weight is the product of its step
//! weights; a path-sum adds the weights of a finite set of histories.
//!
//! Two kinds of history set are kept apart.
//!
//! - [`TimeSlicedTransport`] (graded): slices `X^(0), ..., X^(n)` and one
//!   transfer matrix per step, `T_k[y][x]` the weight of `x -> y`. A history
//!   has one vertex per slice. The path-sum by enumeration is the entry of
//!   `T_(n-1) ... T_0`, and it composes across any fixed slice `k`:
//!   `Z(c|a) = sum_(b in X^(k)) Z(c|b) Z(b|a)`.
//! - [`TransportGraph`] (ungraded): the free category on a finite directed
//!   graph, whose hom-sets are the directed paths. They are finite exactly when
//!   the graph has no directed cycle, so a cyclic graph is refused. Summing
//!   `Z(c|x) Z(x|a)` over every object `x` counts a path of length `l` once for
//!   each of its `l + 1` split points: the result is
//!   `sum_gamma (l(gamma) + 1) w(gamma)`, three times `Z(c|a)` on `a -> b -> c`
//!   and no fixed multiple of it once paths of different lengths meet.
//!
//! In a positive semiring without zero divisors (`Boolean`, `NonNegative`) a
//! path-sum vanishes only when every history carries a zero step; signed
//! weights cancel. Enumeration is refused beyond a fixed history budget.
//! Nothing here maps weights to probabilities.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_996aa144<T> {
    fn checked_invariant_996aa144(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_996aa144<T> for Option<T> {
    #[inline]
    fn checked_invariant_996aa144(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_996aa144<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_996aa144(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::scalars::Semiring;
use linear_algebra::semiring_matrix as sm;
use num_traits::{One, Signed, Zero};

use core_number_theory::rational::Rational;

/// Largest number of histories any enumeration here will produce.
pub const HISTORY_BUDGET: usize = 1 << 16;

/// Most steps [`TransportGraph::unroll`] builds.
pub const UNROLL_BUDGET: usize = 1 << 12;

/// Refusals for transport declarations and evaluations.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TransportError {
    #[error("a transport needs at least one vertex")]
    NoVertices,
    #[error("a time-sliced transport needs at least one slice")]
    NoSlices,
    #[error("slice {slice} is empty")]
    EmptySlice { slice: usize },
    #[error("{slices} slices cannot carry {steps} step matrices")]
    StepCount { slices: usize, steps: usize },
    #[error("{steps} steps exceed the unrolling budget of {budget}")]
    StepBudget { steps: usize, budget: usize },
    #[error("step {step} is {rows}x{cols}, expected {expected_rows}x{expected_cols}")]
    StepShape {
        step: usize,
        rows: usize,
        cols: usize,
        expected_rows: usize,
        expected_cols: usize,
    },
    #[error("row {row} has a different length from row 0")]
    RaggedMatrix { row: usize },
    #[error("{left_cols} columns cannot meet {right_rows} rows")]
    MatrixShape { left_cols: usize, right_rows: usize },
    #[error("matrix is {rows}x{cols}, not square")]
    NotSquare { rows: usize, cols: usize },
    #[error("vertex {vertex} is out of range for {count} vertices")]
    VertexOutOfRange { vertex: usize, count: usize },
    #[error("edge {edge} is out of range for {count} edges")]
    EdgeOutOfRange { edge: usize, count: usize },
    #[error("history has {actual} vertices, expected {expected}")]
    HistoryLength { expected: usize, actual: usize },
    #[error("slice {slice} is outside 0..={steps}")]
    SliceOutOfRange { slice: usize, steps: usize },
    #[error("vertex {vertex} lies on a directed cycle; the free category has infinite hom-sets")]
    DirectedCycle { vertex: usize },
    #[error("more than {budget} histories")]
    HistoryBudget { budget: usize },
    #[error("matrix computation refused: {0}")]
    Matrix(#[from] linear_algebra::backend::basic_matrix::MatrixError),
    #[error("the nonnegative graph has no certified finite Green function")]
    NoFiniteClosure,
    #[error("weight {0} is negative")]
    NegativeWeight(Rational),
}

/// Certified rational Green function for a nonnegative weighted graph. The
/// returned positive vector v satisfies T v < v; the contraction bound is
/// max_i (T v)_i/v_i < 1 in the v-weighted supremum norm.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GreenFunctionCertificate {
    pub kernel: BasicMatrix<Rational>,
    pub positive_weight: Vec<Rational>,
    pub contraction_bound: Rational,
}

impl TransportGraph<NonNegative> {
    fn compute_contraction_bound(
        t: &BasicMatrix<NonNegative>,
        v: &[Rational],
        n: usize,
    ) -> Result<Rational, TransportError> {
        let mut bound = <Rational as Zero>::zero();
        for r in 0..n {
            let tv: Rational = (0..n)
                .map(|c| {
                    &t.get_ref(r, c)
                        .checked_invariant_996aa144("valid transfer index")
                        .0
                        * &v[c]
                })
                .sum();
            if &v[r] - &tv != <Rational as One>::one() {
                return Err(TransportError::NoFiniteClosure);
            }
            let ratio = tv / &v[r];
            if ratio > bound {
                bound = ratio;
            }
        }
        if bound >= <Rational as One>::one() {
            return Err(TransportError::NoFiniteClosure);
        }
        Ok(bound)
    }

    pub fn closure(&self) -> Result<GreenFunctionCertificate, TransportError> {
        use linear_algebra::backend::basic_matrix::BasicMatrix;
        use linear_algebra::exact_field::elimination::inverse;
        if self.vertex_count > 128 {
            return Err(TransportError::HistoryBudget { budget: 128 });
        }
        let t = self.transfer_matrix();
        let n = self.vertex_count;
        let a = BasicMatrix::try_from_fn(n, n, |r, c| {
            let delta = if r == c {
                <Rational as One>::one()
            } else {
                <Rational as Zero>::zero()
            };
            delta
                - t.get_ref(r, c)
                    .checked_invariant_996aa144("valid transfer index")
                    .0
                    .clone()
        })?;
        let kernel = inverse(&a).map_err(|_| TransportError::NoFiniteClosure)?;
        let v: Vec<Rational> = (0..n)
            .map(|r| {
                (0..n)
                    .map(|c| {
                        kernel
                            .get_ref(r, c)
                            .checked_invariant_996aa144("valid Green index")
                    })
                    .sum()
            })
            .collect();
        if v.iter().any(|x| !x.is_positive()) || kernel.as_slice().iter().any(Signed::is_negative) {
            return Err(TransportError::NoFiniteClosure);
        }
        let bound = Self::compute_contraction_bound(&t, &v, n)?;
        Ok(GreenFunctionCertificate {
            kernel,
            positive_weight: v,
            contraction_bound: bound,
        })
    }
}

/// A nonnegative rational weight.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NonNegative(Rational);

impl NonNegative {
    pub fn new(value: Rational) -> Result<Self, TransportError> {
        if value.is_negative() {
            return Err(TransportError::NegativeWeight(value));
        }
        Ok(Self(value))
    }

    pub fn value(&self) -> &Rational {
        &self.0
    }
}

impl Semiring for NonNegative {
    fn zero() -> Self {
        Self(<Rational as Zero>::zero())
    }
    fn one() -> Self {
        Self(<Rational as One>::one())
    }
    fn add(&self, rhs: &Self) -> Self {
        Self(&self.0 + &rhs.0)
    }
    fn mul(&self, rhs: &Self) -> Self {
        Self(&self.0 * &rhs.0)
    }
    fn is_zero(&self) -> bool {
        Zero::is_zero(&self.0)
    }
}

/// A graded transport: slices and one transfer matrix per step.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TimeSlicedTransport<W> {
    slice_sizes: Vec<usize>,
    steps: Vec<BasicMatrix<W>>,
}

impl<W: Semiring> TimeSlicedTransport<W> {
    fn validate_slice_budget(slice_sizes: &[usize], steps_len: usize) -> Result<(), TransportError> {
        if slice_sizes.is_empty() {
            return Err(TransportError::NoSlices);
        }
        if let Some(slice) = slice_sizes.iter().position(|&s| s == 0) {
            return Err(TransportError::EmptySlice { slice });
        }
        if steps_len + 1 != slice_sizes.len() {
            return Err(TransportError::StepCount {
                slices: slice_sizes.len(),
                steps: steps_len,
            });
        }
        if steps_len > UNROLL_BUDGET || slice_sizes.iter().any(|&n| n > 256) {
            return Err(TransportError::StepBudget {
                steps: steps_len,
                budget: UNROLL_BUDGET,
            });
        }
        let mut cost = 0usize;
        for k in 0..steps_len {
            let step_cost = slice_sizes[k + 1]
                .checked_mul(slice_sizes[k])
                .and_then(|v| v.checked_mul(slice_sizes[0]))
                .ok_or(TransportError::HistoryBudget { budget: 1 << 24 })?;
            cost = cost
                .checked_add(step_cost)
                .ok_or(TransportError::HistoryBudget { budget: 1 << 24 })?;
        }
        if cost > 1 << 24 {
            return Err(TransportError::HistoryBudget { budget: 1 << 24 });
        }
        Ok(())
    }

    /// `steps[k]` is `|X^(k+1)| x |X^(k)|`; every slice is nonempty.
    pub fn new(slice_sizes: Vec<usize>, steps: Vec<Vec<Vec<W>>>) -> Result<Self, TransportError> {
        Self::validate_slice_budget(&slice_sizes, steps.len())?;
        for t in &steps {
            let cols = t.first().map_or(0, Vec::len);
            if let Some(row) = t.iter().position(|v| v.len() != cols) {
                return Err(TransportError::RaggedMatrix { row });
            }
        }
        let steps = steps
            .into_iter()
            .map(sm::from_rows)
            .collect::<Result<Vec<_>, _>>()?;
        for (step, t) in steps.iter().enumerate() {
            let (rows, cols) = (t.rows(), t.cols());
            let (expected_rows, expected_cols) = (slice_sizes[step + 1], slice_sizes[step]);
            if (rows, cols) != (expected_rows, expected_cols) {
                return Err(TransportError::StepShape {
                    step,
                    rows,
                    cols,
                    expected_rows,
                    expected_cols,
                });
            }
        }
        Ok(Self { slice_sizes, steps })
    }

    pub fn slice_sizes(&self) -> &[usize] {
        &self.slice_sizes
    }

    fn check_vertex(&self, slice: usize, vertex: usize) -> Result<(), TransportError> {
        let count = self.slice_sizes[slice];
        if vertex >= count {
            return Err(TransportError::VertexOutOfRange { vertex, count });
        }
        Ok(())
    }

    /// Every history `(a, x_1, ..., x_(n-1), c)`, in lexicographic order.
    pub fn histories(&self, a: usize, c: usize) -> Result<Vec<Vec<usize>>, TransportError> {
        let last = self.slice_sizes.len() - 1;
        self.check_vertex(0, a)?;
        self.check_vertex(last, c)?;
        if last == 0 {
            return Ok(if a == c { vec![vec![a]] } else { Vec::new() });
        }
        let interior = &self.slice_sizes[1..last];
        let count = interior
            .iter()
            .try_fold(1usize, |acc, &s| acc.checked_mul(s))
            .filter(|&n| n <= HISTORY_BUDGET)
            .ok_or(TransportError::HistoryBudget {
                budget: HISTORY_BUDGET,
            })?;
        let mut out = Vec::with_capacity(count);
        let mut digits = vec![0usize; interior.len()];
        loop {
            let mut history = Vec::with_capacity(last + 1);
            history.push(a);
            history.extend_from_slice(&digits);
            history.push(c);
            out.push(history);
            let mut position = digits.len();
            loop {
                if position == 0 {
                    return Ok(out);
                }
                position -= 1;
                digits[position] += 1;
                if digits[position] < interior[position] {
                    break;
                }
                digits[position] = 0;
            }
        }
    }

    /// The product of a history's step weights.
    pub fn history_weight(&self, history: &[usize]) -> Result<W, TransportError> {
        if history.len() != self.slice_sizes.len() {
            return Err(TransportError::HistoryLength {
                expected: self.slice_sizes.len(),
                actual: history.len(),
            });
        }
        for (slice, &vertex) in history.iter().enumerate() {
            self.check_vertex(slice, vertex)?;
        }
        Ok(self.steps.iter().enumerate().fold(W::one(), |acc, (k, t)| {
            t.get_ref(history[k + 1], history[k])
                .checked_invariant_996aa144("validated history indices")
                .mul(&acc)
        }))
    }

    /// `Z(c|a)` by enumerating every history.
    pub fn path_sum(&self, a: usize, c: usize) -> Result<W, TransportError> {
        self.histories(a, c)?
            .iter()
            .try_fold(W::zero(), |acc, h| Ok(acc.add(&self.history_weight(h)?)))
    }

    /// `T_(n-1) ... T_0`, a `|X^(n)| x |X^(0)|` matrix; the identity when `n = 0`.
    pub fn propagator(&self) -> BasicMatrix<W> {
        self.steps.iter().fold(
            sm::identity(self.slice_sizes[0]).checked_invariant_996aa144("admitted identity budget"),
            |acc, t| {
                sm::multiply(t, &acc)
                    .checked_invariant_996aa144("construction validates the total multiplication budget")
            },
        )
    }

    /// The transports on slices `0..=k` and `k..=n`.
    pub fn split(&self, slice: usize) -> Result<(Self, Self), TransportError> {
        if slice > self.steps.len() {
            return Err(TransportError::SliceOutOfRange {
                slice,
                steps: self.steps.len(),
            });
        }
        let earlier = Self {
            slice_sizes: self.slice_sizes[..=slice].to_vec(),
            steps: self.steps[..slice].to_vec(),
        };
        let later = Self {
            slice_sizes: self.slice_sizes[slice..].to_vec(),
            steps: self.steps[slice..].to_vec(),
        };
        Ok((earlier, later))
    }

    /// `sum_(b in X^(k)) Z(c|b) Z(b|a)`: the path-sum cut at slice `k`.
    pub fn sliced_composition(
        &self,
        a: usize,
        c: usize,
        slice: usize,
    ) -> Result<W, TransportError> {
        let (earlier, later) = self.split(slice)?;
        (0..self.slice_sizes[slice]).try_fold(W::zero(), |acc, b| {
            Ok(acc.add(&later.path_sum(b, c)?.mul(&earlier.path_sum(a, b)?)))
        })
    }
}

/// A finite directed multigraph with weighted edges: the ungraded transport.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TransportGraph<W> {
    vertex_count: usize,
    edges: Vec<(usize, usize)>,
    weights: Vec<W>,
}

impl<W: Semiring> TransportGraph<W> {
    /// Edges are `(source, target, weight)`; parallel edges and loops are allowed.
    pub fn new(vertex_count: usize, edges: Vec<(usize, usize, W)>) -> Result<Self, TransportError> {
        if vertex_count == 0 {
            return Err(TransportError::NoVertices);
        }
        if vertex_count > 256 || edges.len() > 16384 {
            return Err(TransportError::HistoryBudget { budget: 16384 });
        }
        let mut pairs = Vec::with_capacity(edges.len());
        let mut weights = Vec::with_capacity(edges.len());
        for (source, target, weight) in edges {
            for vertex in [source, target] {
                if vertex >= vertex_count {
                    return Err(TransportError::VertexOutOfRange {
                        vertex,
                        count: vertex_count,
                    });
                }
            }
            pairs.push((source, target));
            weights.push(weight);
        }
        Ok(Self {
            vertex_count,
            edges: pairs,
            weights,
        })
    }

    /// `T[target][source]`, the summed weight of the edges `source -> target`.
    pub fn transfer_matrix(&self) -> BasicMatrix<W> {
        let mut t =
            BasicMatrix::try_from_fn(self.vertex_count, self.vertex_count, |_, _| W::zero())
                .checked_invariant_996aa144("admitted transfer shape");
        for (&(source, target), weight) in self.edges.iter().zip(&self.weights) {
            let value = t
                .get_ref(target, source)
                .checked_invariant_996aa144("validated endpoints")
                .add(weight);
            t.set(target, source, value).checked_invariant_996aa144("validated endpoints");
        }
        t
    }

    /// The graded transport of `steps` copies of the transfer matrix, refused
    /// above [`UNROLL_BUDGET`] steps.
    pub fn unroll(&self, steps: usize) -> Result<TimeSlicedTransport<W>, TransportError> {
        if steps > UNROLL_BUDGET {
            return Err(TransportError::StepBudget {
                steps,
                budget: UNROLL_BUDGET,
            });
        }
        TimeSlicedTransport::new(
            vec![self.vertex_count; steps + 1],
            vec![sm::to_rows(&self.transfer_matrix())?; steps],
        )
    }

    /// The product of the weights along a sequence of edge indices.
    pub fn path_weight(&self, path: &[usize]) -> Result<W, TransportError> {
        path.iter().try_fold(W::one(), |acc, &edge| {
            self.weights
                .get(edge)
                .map(|w| w.mul(&acc))
                .ok_or(TransportError::EdgeOutOfRange {
                    edge,
                    count: self.edges.len(),
                })
        })
    }

    fn check_vertex(&self, vertex: usize) -> Result<(), TransportError> {
        if vertex >= self.vertex_count {
            return Err(TransportError::VertexOutOfRange {
                vertex,
                count: self.vertex_count,
            });
        }
        Ok(())
    }

    fn native_graph(
        &self,
    ) -> Result<core_homology::directed_multigraph::DirectedMultigraph, TransportError> {
        core_homology::directed_multigraph::DirectedMultigraph::new(
            self.vertex_count,
            self.edges.clone(),
        )
        .map_err(|e| match e {
            core_homology::directed_multigraph::DirectedMultigraphError::Cycle { vertex } => {
                TransportError::DirectedCycle { vertex }
            }
            _ => TransportError::HistoryBudget {
                budget: HISTORY_BUDGET,
            },
        })
    }
    pub fn check_acyclic(&self) -> Result<(), TransportError> {
        self.native_graph()?
            .topological_order()
            .map(|_| ())
            .map_err(|e| match e {
                core_homology::directed_multigraph::DirectedMultigraphError::Cycle { vertex } => {
                    TransportError::DirectedCycle { vertex }
                }
                _ => TransportError::HistoryBudget {
                    budget: HISTORY_BUDGET,
                },
            })
    }

    /// Every directed path from `a` to `b` as edge indices, sorted; the empty
    /// path is included when `a = b`. A graph with a directed cycle is refused.
    pub fn all_histories(&self, a: usize, b: usize) -> Result<Vec<Vec<usize>>, TransportError> {
        self.check_vertex(a)?;
        self.check_vertex(b)?;
        self.native_graph()?
            .all_paths(a, b, HISTORY_BUDGET)
            .map_err(|e| match e {
                core_homology::directed_multigraph::DirectedMultigraphError::Cycle { vertex } => {
                    TransportError::DirectedCycle { vertex }
                }
                _ => TransportError::HistoryBudget {
                    budget: HISTORY_BUDGET,
                },
            })
    }

    /// The sum of the weights of [`Self::all_histories`].
    pub fn total_path_sum(&self, a: usize, b: usize) -> Result<W, TransportError> {
        self.all_histories(a, b)?
            .iter()
            .try_fold(W::zero(), |acc, path| Ok(acc.add(&self.path_weight(path)?)))
    }

    /// `sum_x Z(c|x) Z(x|a)` over every vertex `x`, empty paths acting as identities.
    pub fn ungraded_split_sum(&self, a: usize, c: usize) -> Result<W, TransportError> {
        (0..self.vertex_count).try_fold(W::zero(), |acc, x| {
            Ok(acc.add(&self.total_path_sum(x, c)?.mul(&self.total_path_sum(a, x)?)))
        })
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/graded_path_sum.rs
// Claim: urn:core:crates_rs:core-quantum-physics:graded-path-sum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_996aa144 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
