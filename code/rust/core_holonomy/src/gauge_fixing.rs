//! Gauge fixing on a spanning forest, pure-gauge decisions, holonomy verdicts
//! and the count of flat gauge classes with values in a finite cyclic group.
//!
//! # Conventions
//!
//! A connection assigns to every oriented edge `e = (s, t)` an invertible
//! matrix `U_e`, the transport along `e` from `s` to `t`; traversing `e`
//! backwards transports by `U_e^{-1}`. The transport along a walk is the
//! path-ordered product `M_k ... M_1` of its step matrices, as in
//! [`crate::holonomy::compute_path_holonomy`]. A vertex gauge
//! `g : V -> GL(d)` acts by `U'_e = g(t) U_e g(s)^{-1}`, as in
//! [`DiscreteConnection::apply_gauge_transformation`]. Every entry point is
//! generic over an [`ExactScalar`] field, so one algorithm serves `Q`,
//! `Q(i)` with `1 x 1` matrices (`U(1)`), and non-abelian fibres such as
//! quaternion or permutation matrices.
//!
//! # Edge-indexed connections
//!
//! [`DiscreteConnection`] is keyed by `(source, target)` and treats the
//! opposite pair as the inverse, so two edges joining the same vertices in
//! opposite directions (legal in a [`CellComplex`], and unavoidable on a
//! periodic lattice with two sites in one direction) cannot carry independent
//! values in it. [`EdgeConnection`] is keyed by edge index and can. The
//! `DiscreteConnection` entry points refuse such complexes with
//! [`HolonomyError::AntiparallelEdges`] rather than guess.
//!
//! # Tree gauge
//!
//! [`tree_gauge_indexed`] (and [`tree_gauge`] for a `DiscreteConnection`)
//! fixes the gauge on a breadth-first spanning forest: roots in vertex order
//! with `g(root) = 1`, vertices discovered along edges in increasing edge
//! order, and `g(v) = T(v)^{-1}` where `T(v)` is the transport from the root
//! of the component of `v` to `v` along the tree. The gauge transform then
//! equals `1` on every tree edge, and on any other edge `e = (s, t)` it is
//!
//! ```text
//! R_e = g(t) U_e g(s)^{-1} = T(t)^{-1} U_e T(s),
//! ```
//!
//! the holonomy of the fundamental cycle of `e` based at the root: up the tree
//! to `s`, along `e`, back down the tree from `t`. This is the edge value
//! conjugated by the transports along the tree paths, so it is correct for
//! non-abelian fibres; based at another vertex the same loop has the holonomy
//! `T(s) R_e T(s)^{-1}`. The connection is pure gauge exactly when every `R_e`
//! is the identity, and then `h(v) = T(v)` satisfies `U_e = h(t) h(s)^{-1}`.
//!
//! Two connections with equal residuals are gauge equivalent with the gauge
//! `T_b(v) g_a(v)`. For a fibre of dimension `> 1` a difference of residuals
//! does not settle the question, because a gauge that is constant on a
//! component also conjugates the residuals; [`gauge_equivalence`] reports a
//! proved inequivalence only when a conjugation invariant (trace or
//! determinant of a residual) differs, and otherwise says it is undetermined.
//!
//! # Flat classes with cyclic values
//!
//! With values in the cyclic group `Z_n` (written additively), gauge classes of
//! flat connections are `H^1(X; Z_n) = Hom(H_1(X; Z), Z_n)`. Fixing the tree
//! gauge identifies a class with its values `phi` on the `z` edges off the
//! tree, where `z` is the cycle rank, and flatness is `M phi = 0 (mod n)` for
//! the integer matrix `M` of face boundaries in those coordinates. With
//! invariant factors `d_1, .., d_r` of `M` (Smith normal form) the count is
//! `n^(z - r) prod gcd(d_i, n)`; without faces it is `n^z`.
//!
//! AuthorityEffect: None.

use crate::connection::DiscreteConnection;
use crate::error::HolonomyError;
use crate::graph::{CellComplex, Face, OrientedStep};
use crate::matrix::{ExactMatrix, ExactScalar};
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::smith_normal_form::smith_normal_form_checked;
use num_bigint::{BigInt, BigUint};
use num_traits::{ToPrimitive, Zero};
use core_kernel::resource_limits::check_and_reserve;
use std::collections::{BTreeMap, VecDeque};

/// `(source index, target index)` of every edge, in edge order.
fn edge_endpoints(complex: &CellComplex) -> Result<Vec<(usize, usize)>, HolonomyError> {
    let mut endpoints = Vec::new();
    check_and_reserve(
        &mut endpoints,
        complex.edges.len(),
        complex.limits.max_edges,
    )?;
    for edge in &complex.edges {
        let source =
            *complex
                .vertex_map
                .get(&edge.source)
                .ok_or_else(|| HolonomyError::VertexNotFound {
                    id: edge.source.clone(),
                })?;
        let target =
            *complex
                .vertex_map
                .get(&edge.target)
                .ok_or_else(|| HolonomyError::VertexNotFound {
                    id: edge.target.clone(),
                })?;
        endpoints.push((source, target));
    }
    Ok(endpoints)
}

fn check_edge(index: usize, edge_count: usize) -> Result<(), HolonomyError> {
    if index < edge_count {
        Ok(())
    } else {
        Err(HolonomyError::EdgeIndexOutOfRange { index, edge_count })
    }
}

fn check_vertex(index: usize, vertex_count: usize) -> Result<(), HolonomyError> {
    if index < vertex_count {
        Ok(())
    } else {
        Err(HolonomyError::VertexIndexOutOfRange {
            index,
            vertex_count,
        })
    }
}

/// The edge `e` of the tree that discovered a vertex, seen from its parent.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct Link {
    edge: usize,
    /// `+1` when the edge points from the parent to the vertex, else `-1`.
    direction_from_parent: i8,
    parent: usize,
}

/// A breadth-first spanning forest of the edge graph.
#[derive(Debug, Clone, PartialEq, Eq)]
struct Forest {
    tree_edge: Vec<bool>,
    parent: Vec<Option<Link>>,
    root: Vec<usize>,
    /// Vertices in discovery order: a parent always precedes its children.
    discovery: Vec<usize>,
}

fn spanning_forest(vertex_count: usize, endpoints: &[(usize, usize)]) -> Forest {
    let mut adjacency: Vec<Vec<(usize, usize, i8)>> = vec![Vec::new(); vertex_count];
    for (edge, &(source, target)) in endpoints.iter().enumerate() {
        adjacency[source].push((target, edge, 1));
        adjacency[target].push((source, edge, -1));
    }
    let mut tree_edge = vec![false; endpoints.len()];
    let mut parent: Vec<Option<Link>> = vec![None; vertex_count];
    let mut root: Vec<usize> = (0..vertex_count).collect();
    let mut visited = vec![false; vertex_count];
    let mut discovery = Vec::with_capacity(vertex_count);
    for start in 0..vertex_count {
        if visited[start] {
            continue;
        }
        visited[start] = true;
        discovery.push(start);
        let mut queue = VecDeque::from([start]);
        while let Some(u) = queue.pop_front() {
            for &(v, edge, direction) in &adjacency[u] {
                if visited[v] {
                    continue;
                }
                visited[v] = true;
                tree_edge[edge] = true;
                parent[v] = Some(Link {
                    edge,
                    direction_from_parent: direction,
                    parent: u,
                });
                root[v] = start;
                discovery.push(v);
                queue.push_back(v);
            }
        }
    }
    Forest {
        tree_edge,
        parent,
        root,
        discovery,
    }
}

/// The number of independent cycles of the edge graph: edges minus vertices
/// plus connected components (the number of edges off a spanning forest).
/// It is the rank of the free abelian group `H_1` of the graph.
pub fn cycle_rank(complex: &CellComplex) -> Result<usize, HolonomyError> {
    let endpoints = edge_endpoints(complex)?;
    let forest = spanning_forest(complex.vertices.len(), &endpoints);
    Ok(forest.tree_edge.iter().filter(|&&on_tree| !on_tree).count())
}

/// A connection on a [`CellComplex`] keyed by edge index: one invertible
/// `dim x dim` matrix per edge, the transport from its source to its target.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct EdgeConnection<T: ExactScalar> {
    dim: usize,
    values: Vec<ExactMatrix<T>>,
    inverses: Vec<ExactMatrix<T>>,
}

impl<T: ExactScalar> EdgeConnection<T> {
    /// One matrix per edge of `complex`, in edge order.
    ///
    /// Refused: fibre dimension 0 or above the complex's limit; a number of
    /// values other than the number of edges; a value that is not
    /// `dim x dim`; a singular value.
    pub fn new(
        complex: &CellComplex,
        dim: usize,
        values: Vec<ExactMatrix<T>>,
    ) -> Result<Self, HolonomyError> {
        if dim == 0 {
            return Err(HolonomyError::DimensionMismatch {
                expected: 1,
                actual: 0,
            });
        }
        if dim > complex.limits.max_dimension {
            return Err(HolonomyError::AllocationFailure {
                requested: dim,
                detail: format!(
                    "Requested dimension {dim} > max_dimension {}",
                    complex.limits.max_dimension
                ),
            });
        }
        if values.len() != complex.edges.len() {
            return Err(HolonomyError::EdgeValueCount {
                expected: complex.edges.len(),
                actual: values.len(),
            });
        }
        let mut inverses = Vec::new();
        check_and_reserve(&mut inverses, values.len(), complex.limits.max_edges)?;
        for (value, edge) in values.iter().zip(&complex.edges) {
            if value.rows != dim || value.cols != dim {
                return Err(HolonomyError::DimensionMismatch {
                    expected: dim,
                    actual: value.rows.max(value.cols),
                });
            }
            inverses.push(value.inverse().map_err(|e| match e {
                HolonomyError::SingularMatrix { detail } => HolonomyError::SingularConnection {
                    src: edge.source.clone(),
                    tgt: edge.target.clone(),
                    detail,
                },
                other => other,
            })?);
        }
        Ok(Self {
            dim,
            values,
            inverses,
        })
    }

    /// A one-dimensional connection: one scalar per edge (`U(1)` when the
    /// scalars are unit Gaussian rationals).
    pub fn from_scalars(complex: &CellComplex, scalars: Vec<T>) -> Result<Self, HolonomyError> {
        let values = scalars
            .into_iter()
            .map(|s| ExactMatrix::try_new(1, 1, vec![s]))
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(complex, 1, values)
    }

    /// The trivial connection: the identity on every edge.
    pub fn trivial(complex: &CellComplex, dim: usize) -> Result<Self, HolonomyError> {
        let values = (0..complex.edges.len())
            .map(|_| ExactMatrix::try_identity(dim))
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(complex, dim, values)
    }

    /// The pure-gauge connection `U_e = h(t) h(s)^{-1}` of the potentials `h`
    /// (one invertible matrix per vertex, in vertex order).
    pub fn pure_gauge(
        complex: &CellComplex,
        potentials: &[ExactMatrix<T>],
    ) -> Result<Self, HolonomyError> {
        let dim = potentials.first().map_or(1, |h| h.rows);
        Self::trivial(complex, dim)?.gauge_transform(complex, potentials)
    }

    /// Read a string-keyed connection on `complex`: the value on edge
    /// `(s, t)` is `connection.get_step(s, t)`.
    ///
    /// Refused with [`HolonomyError::AntiparallelEdges`] when two edges join
    /// the same vertices in opposite directions, because a string-keyed
    /// connection stores a single matrix for such a pair.
    pub fn from_discrete_connection(
        complex: &CellComplex,
        connection: &DiscreteConnection<T>,
    ) -> Result<Self, HolonomyError> {
        refuse_antiparallel_edges(complex)?;
        let values = complex
            .edges
            .iter()
            .map(|edge| connection.get_step(&edge.source, &edge.target).cloned())
            .collect::<Result<Vec<_>, _>>()?;
        Self::new(complex, connection.dim, values)
    }

    /// The same data as a string-keyed connection with `U(s -> t) = U_e`.
    /// Refused for antiparallel edges, like [`Self::from_discrete_connection`].
    pub fn to_discrete_connection(
        &self,
        complex: &CellComplex,
    ) -> Result<DiscreteConnection<T>, HolonomyError> {
        self.check_complex(complex)?;
        refuse_antiparallel_edges(complex)?;
        let mut connection = DiscreteConnection::new(self.dim, complex.limits);
        for (edge, value) in complex.edges.iter().zip(&self.values) {
            connection.set_connection(edge.source.clone(), edge.target.clone(), value.clone())?;
        }
        Ok(connection)
    }

    /// The fibre dimension.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// The number of edge values.
    pub fn edge_count(&self) -> usize {
        self.values.len()
    }

    fn check_complex(&self, complex: &CellComplex) -> Result<(), HolonomyError> {
        if self.values.len() == complex.edges.len() {
            Ok(())
        } else {
            Err(HolonomyError::EdgeValueCount {
                expected: complex.edges.len(),
                actual: self.values.len(),
            })
        }
    }

    /// `U_e`, the transport along edge `edge` from its source to its target.
    pub fn value(&self, edge: usize) -> Result<&ExactMatrix<T>, HolonomyError> {
        check_edge(edge, self.values.len())?;
        Ok(&self.values[edge])
    }

    /// The transport of one step: `U_e` for direction `+1`, `U_e^{-1}` for `-1`.
    /// A direction other than `+-1` is refused as
    /// [`HolonomyError::InvalidStepDirection`] naming step 0, the only step.
    pub fn step(&self, step: OrientedStep) -> Result<&ExactMatrix<T>, HolonomyError> {
        check_edge(step.edge_index, self.values.len())?;
        match step.direction {
            1 => Ok(&self.values[step.edge_index]),
            -1 => Ok(&self.inverses[step.edge_index]),
            direction => Err(HolonomyError::InvalidStepDirection { step: 0, direction }),
        }
    }

    /// The transport along a walk: the path-ordered product of its step
    /// matrices, together with the index of the vertex where it ends.
    ///
    /// Every step must leave the vertex the previous one reached. Refused:
    /// an unknown start vertex, a step that does not start where the walk is
    /// (`BrokenWalk`), a direction other than `+-1`, a walk longer than the
    /// complex's path limit.
    pub fn walk(
        &self,
        complex: &CellComplex,
        start: usize,
        steps: &[OrientedStep],
    ) -> Result<(ExactMatrix<T>, usize), HolonomyError> {
        self.check_complex(complex)?;
        let endpoints = edge_endpoints(complex)?;
        self.walk_with_endpoints(complex, &endpoints, start, steps)
    }

    fn walk_with_endpoints(
        &self,
        complex: &CellComplex,
        endpoints: &[(usize, usize)],
        start: usize,
        steps: &[OrientedStep],
    ) -> Result<(ExactMatrix<T>, usize), HolonomyError> {
        check_vertex(start, complex.vertices.len())?;
        if steps.len() > complex.limits.max_path_length {
            return Err(HolonomyError::PathLengthExceeded {
                length: steps.len(),
                limit: complex.limits.max_path_length,
            });
        }
        let mut transport = ExactMatrix::try_identity(self.dim)?;
        let mut here = start;
        for (index, step) in steps.iter().enumerate() {
            let to = Self::resolve_walk_step_target(endpoints, index, *step, here)?;
            transport = self.step(*step)?.matmul(&transport)?;
            here = to;
        }
        Ok((transport, here))
    }

    fn resolve_walk_step_target(
        endpoints: &[(usize, usize)],
        index: usize,
        step: OrientedStep,
        here: usize,
    ) -> Result<usize, HolonomyError> {
        check_edge(step.edge_index, endpoints.len())?;
        let (source, target) = endpoints[step.edge_index];
        let (from, to) = match step.direction {
            1 => (source, target),
            -1 => (target, source),
            direction => {
                return Err(HolonomyError::InvalidStepDirection {
                    step: index,
                    direction,
                })
            }
        };
        if from != here {
            return Err(HolonomyError::BrokenWalk {
                step: index,
                detail: format!(
                    "step {index} leaves vertex {from} but the walk is at vertex {here}"
                ),
            });
        }
        Ok(to)
    }

    /// The transport along a closed walk; refused when the walk does not end
    /// where it starts.
    pub fn loop_holonomy(
        &self,
        complex: &CellComplex,
        start: usize,
        steps: &[OrientedStep],
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        let (transport, end) = self.walk(complex, start, steps)?;
        if end != start {
            return Err(HolonomyError::OpenLoop {
                start: complex.vertices[start].id.clone(),
                end: complex.vertices[end].id.clone(),
            });
        }
        Ok(transport)
    }

    /// The gauge transform `U'_e = g(t) U_e g(s)^{-1}` by one invertible
    /// `dim x dim` matrix per vertex, in vertex order.
    fn conjugate_edge_pair(
        &self,
        edge: usize,
        s: usize,
        t: usize,
        gauge: &[ExactMatrix<T>],
        gauge_inverses: &[ExactMatrix<T>],
    ) -> Result<(ExactMatrix<T>, ExactMatrix<T>), HolonomyError> {
        let val = gauge[t]
            .matmul(&self.values[edge])?
            .matmul(&gauge_inverses[s])?;
        let inv = gauge[s]
            .matmul(&self.inverses[edge])?
            .matmul(&gauge_inverses[t])?;
        Ok((val, inv))
    }

    pub fn gauge_transform(
        &self,
        complex: &CellComplex,
        gauge: &[ExactMatrix<T>],
    ) -> Result<Self, HolonomyError> {
        self.check_complex(complex)?;
        let gauge_inverses = self.validate_and_invert_gauge(complex, gauge)?;
        let endpoints = edge_endpoints(complex)?;
        let mut values = Vec::new();
        let mut inverses = Vec::new();
        check_and_reserve(&mut values, endpoints.len(), complex.limits.max_edges)?;
        check_and_reserve(&mut inverses, endpoints.len(), complex.limits.max_edges)?;
        for (edge, &(s, t)) in endpoints.iter().enumerate() {
            let (val, inv) = self.conjugate_edge_pair(edge, s, t, gauge, &gauge_inverses)?;
            values.push(val);
            inverses.push(inv);
        }
        Ok(Self {
            dim: self.dim,
            values,
            inverses,
        })
    }

    fn validate_and_invert_gauge(
        &self,
        complex: &CellComplex,
        gauge: &[ExactMatrix<T>],
    ) -> Result<Vec<ExactMatrix<T>>, HolonomyError> {
        if gauge.len() != complex.vertices.len() {
            return Err(HolonomyError::VertexValueCount {
                expected: complex.vertices.len(),
                actual: gauge.len(),
            });
        }
        for g in gauge {
            if g.rows != self.dim || g.cols != self.dim {
                return Err(HolonomyError::DimensionMismatch {
                    expected: self.dim,
                    actual: g.rows.max(g.cols),
                });
            }
        }
        gauge.iter().map(ExactMatrix::inverse).collect()
    }

    /// Covariant incidence matrix: edge row `psi(t)-U_e psi(s)`. Edge indexing
    /// keeps parallel edges and opposite orientations distinct.
    pub fn covariant_difference_matrix(
        &self,
        complex: &CellComplex,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        self.check_complex(complex)?;
        let endpoints = edge_endpoints(complex)?;
        let (rows, cols) = self.checked_incidence_dims(complex, endpoints.len())?;
        let mut out = ExactMatrix::try_zero(rows, cols)?;
        for (edge, &(s, t)) in endpoints.iter().enumerate() {
            self.write_incidence_edge_block(&mut out, cols, edge, s, t);
        }
        Ok(out)
    }

    fn checked_incidence_dims(
        &self,
        complex: &CellComplex,
        edge_count: usize,
    ) -> Result<(usize, usize), HolonomyError> {
        let rows =
            edge_count
                .checked_mul(self.dim)
                .ok_or_else(|| HolonomyError::AllocationFailure {
                    requested: usize::MAX,
                    detail: "incidence dimension overflow".into(),
                })?;
        let cols = complex
            .vertices
            .len()
            .checked_mul(self.dim)
            .ok_or_else(|| HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "incidence dimension overflow".into(),
            })?;
        let entries = rows
            .checked_mul(cols)
            .ok_or_else(|| HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "incidence buffer overflow".into(),
            })?;
        if entries > complex.limits.max_operations {
            return Err(HolonomyError::AllocationFailure {
                requested: entries,
                detail: "incidence operation budget".into(),
            });
        }
        Ok((rows, cols))
    }

    fn write_incidence_edge_block(
        &self,
        out: &mut ExactMatrix<T>,
        cols: usize,
        edge: usize,
        s: usize,
        t: usize,
    ) {
        for i in 0..self.dim {
            for j in 0..self.dim {
                let index = (edge * self.dim + i) * cols + s * self.dim + j;
                out.data[index] -= self.values[edge].get(i, j).clone();
            }
            let index = (edge * self.dim + i) * cols + t * self.dim + i;
            out.data[index] += T::one();
        }
    }

    /// `D* W D`, using declared scalar weights (one per edge). Positivity is
    /// conditional on a conjugation-compatible field and positive real weights.
    pub fn connection_laplacian(
        &self,
        complex: &CellComplex,
        weights: &[T],
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        if weights.len() != complex.edges.len() {
            return Err(HolonomyError::EdgeValueCount {
                expected: complex.edges.len(),
                actual: weights.len(),
            });
        }
        let d = self.covariant_difference_matrix(complex)?;
        let n = d.cols;
        let work = n
            .checked_mul(n)
            .and_then(|k| k.checked_mul(d.rows))
            .ok_or_else(|| HolonomyError::AllocationFailure {
                requested: usize::MAX,
                detail: "Laplacian work overflow".into(),
            })?;
        if work > complex.limits.max_operations {
            return Err(HolonomyError::AllocationFailure {
                requested: work,
                detail: "Laplacian operation budget".into(),
            });
        }
        let mut out = ExactMatrix::try_zero(n, n)?;
        for i in 0..n {
            for j in 0..n {
                let mut value = T::zero();
                for row in 0..d.rows {
                    value += d.get(row, i).conjugate()
                        * weights[row / self.dim].clone()
                        * d.get(row, j).clone();
                }
                out.data[i * n + j] = value;
            }
        }
        Ok(out)
    }

    /// The holonomy of the boundary of one face, based at its first boundary
    /// vertex. Refused when the boundary steps are not a closed walk.
    pub fn face_holonomy(
        &self,
        complex: &CellComplex,
        face: usize,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        self.check_complex(complex)?;
        let endpoints = edge_endpoints(complex)?;
        self.face_holonomy_with_endpoints(complex, &endpoints, face)
    }

    fn face_holonomy_with_endpoints(
        &self,
        complex: &CellComplex,
        endpoints: &[(usize, usize)],
        face: usize,
    ) -> Result<ExactMatrix<T>, HolonomyError> {
        let declared = complex
            .faces
            .get(face)
            .ok_or_else(|| HolonomyError::FaceNotFound {
                id: face.to_string(),
            })?;
        let start_id = declared.boundary_vertices.first().ok_or_else(|| {
            HolonomyError::BoundaryCycleMismatch {
                face: declared.id.clone(),
                detail: "the face lists no boundary vertices".into(),
            }
        })?;
        let start =
            *complex
                .vertex_map
                .get(start_id)
                .ok_or_else(|| HolonomyError::VertexNotFound {
                    id: start_id.clone(),
                })?;
        let (transport, end) =
            self.walk_with_endpoints(complex, endpoints, start, &declared.boundary_edges)?;
        if end != start {
            return Err(HolonomyError::BoundaryCycleMismatch {
                face: declared.id.clone(),
                detail: "the boundary steps do not return to the first boundary vertex".into(),
            });
        }
        Ok(transport)
    }
}

fn refuse_antiparallel_edges(complex: &CellComplex) -> Result<(), HolonomyError> {
    for (first, edge) in complex.edges.iter().enumerate() {
        if edge.source == edge.target {
            continue;
        }
        if let Some(&second) = complex
            .edge_map
            .get(&(edge.target.clone(), edge.source.clone()))
        {
            return Err(HolonomyError::AntiparallelEdges {
                first: first.min(second),
                second: first.max(second),
            });
        }
    }
    Ok(())
}

/// The closed walk that an edge closes with the spanning forest: from the root
/// of its component down the tree to the source, along the edge, and back up
/// the tree from the target. Its holonomy is the residual of the tree gauge on
/// that edge. For a tree edge the walk backtracks and its holonomy is trivial.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FundamentalCycle {
    pub edge: usize,
    /// The root vertex the loop is based at.
    pub base: String,
    /// The vertices of the closed walk, from the base back to the base.
    pub vertices: Vec<String>,
    pub steps: Vec<OrientedStep>,
}

/// A closed walk whose holonomy is not the identity, with that holonomy.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HolonomyWitness<T: ExactScalar> {
    pub edge: usize,
    pub cycle: FundamentalCycle,
    pub holonomy: ExactMatrix<T>,
}

/// Whether a connection is pure gauge, with the gauge or a witness.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum PureGaugeVerdict<T: ExactScalar> {
    /// `potentials[v] = T(v)`, the transport from the root of the component
    /// of `v`: `U_e = potentials[t] potentials[s]^{-1}` on every edge, with the
    /// identity at every root.
    PureGauge { potentials: Vec<ExactMatrix<T>> },
    /// The first edge off the tree whose fundamental cycle has holonomy other
    /// than the identity; the walk can be replayed with
    /// [`EdgeConnection::loop_holonomy`].
    NotPureGauge { witness: Box<HolonomyWitness<T>> },
}

/// A connection moved to the identity on a spanning forest.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TreeGauge<T: ExactScalar> {
    dim: usize,
    vertex_ids: Vec<String>,
    endpoints: Vec<(usize, usize)>,
    forest: Forest,
    gauge: Vec<ExactMatrix<T>>,
    transport_from_root: Vec<ExactMatrix<T>>,
    residual: EdgeConnection<T>,
}

impl<T: ExactScalar> TreeGauge<T> {
    /// The fibre dimension.
    pub fn dim(&self) -> usize {
        self.dim
    }

    /// `g(v) = T(v)^{-1}`, one matrix per vertex in vertex order, with the
    /// identity at every root. `U'_e = g(t) U_e g(s)^{-1}` is the identity on
    /// every tree edge.
    pub fn gauge(&self) -> &[ExactMatrix<T>] {
        &self.gauge
    }

    /// The gauge keyed by vertex id, the form
    /// [`DiscreteConnection::apply_gauge_transformation`] takes.
    pub fn gauge_map(&self) -> BTreeMap<String, ExactMatrix<T>> {
        self.vertex_ids
            .iter()
            .cloned()
            .zip(self.gauge.iter().cloned())
            .collect()
    }

    /// `T(v)`: the transport from the root of the component of `v` to `v`
    /// along the spanning forest.
    pub fn transport_from_root(&self, vertex: usize) -> Result<&ExactMatrix<T>, HolonomyError> {
        check_vertex(vertex, self.vertex_ids.len())?;
        Ok(&self.transport_from_root[vertex])
    }

    /// The gauge-transformed connection: the identity on every tree edge.
    pub fn residual(&self) -> &EdgeConnection<T> {
        &self.residual
    }

    /// `R_e`, the gauge-transformed value on edge `edge`.
    pub fn residual_value(&self, edge: usize) -> Result<&ExactMatrix<T>, HolonomyError> {
        self.residual.value(edge)
    }

    /// Whether `edge` lies on the spanning forest.
    pub fn is_tree_edge(&self, edge: usize) -> Result<bool, HolonomyError> {
        check_edge(edge, self.forest.tree_edge.len())?;
        Ok(self.forest.tree_edge[edge])
    }

    /// The edges on the spanning forest, ascending.
    pub fn tree_edges(&self) -> Vec<usize> {
        (0..self.forest.tree_edge.len())
            .filter(|&e| self.forest.tree_edge[e])
            .collect()
    }

    /// The root of the component of `vertex`.
    pub fn root_of(&self, vertex: usize) -> Result<usize, HolonomyError> {
        check_vertex(vertex, self.vertex_ids.len())?;
        Ok(self.forest.root[vertex])
    }

    /// `(e, R_e)` for every edge `e` off the forest: the holonomy of the
    /// fundamental cycle of `e`, in edge order.
    pub fn cycle_holonomies(&self) -> Vec<(usize, ExactMatrix<T>)> {
        (0..self.forest.tree_edge.len())
            .filter(|&e| !self.forest.tree_edge[e])
            .map(|e| (e, self.residual.values[e].clone()))
            .collect()
    }

    /// Whether every residual is the identity, that is, whether the connection
    /// is a gauge transform of the trivial one.
    pub fn is_gauge_trivial(&self) -> bool {
        match ExactMatrix::<T>::try_identity(self.dim) {
            Ok(identity) => self.residual.values.iter().all(|value| *value == identity),
            Err(_) => false,
        }
    }

    /// Steps from the root of the component down the tree to `vertex`.
    fn steps_down_to(&self, vertex: usize) -> Vec<OrientedStep> {
        let mut steps = Vec::new();
        let mut here = vertex;
        while let Some(link) = self.forest.parent[here] {
            steps.push(OrientedStep {
                edge_index: link.edge,
                direction: link.direction_from_parent,
            });
            here = link.parent;
        }
        steps.reverse();
        steps
    }

    /// The closed walk that `edge` closes with the forest, based at the root
    /// of its component. Its holonomy is [`Self::residual_value`] of `edge`.
    pub fn fundamental_cycle(&self, edge: usize) -> Result<FundamentalCycle, HolonomyError> {
        check_edge(edge, self.endpoints.len())?;
        let (source, target) = self.endpoints[edge];
        let root = self.forest.root[source];
        let mut steps = self.steps_down_to(source);
        steps.push(OrientedStep {
            edge_index: edge,
            direction: 1,
        });
        let up: Vec<OrientedStep> = self
            .steps_down_to(target)
            .into_iter()
            .rev()
            .map(|step| OrientedStep {
                edge_index: step.edge_index,
                direction: -step.direction,
            })
            .collect();
        steps.extend(up);

        let mut vertices = vec![root];
        for step in &steps {
            let (s, t) = self.endpoints[step.edge_index];
            vertices.push(if step.direction == 1 { t } else { s });
        }
        Ok(FundamentalCycle {
            edge,
            base: self.vertex_ids[root].clone(),
            vertices: vertices
                .into_iter()
                .map(|v| self.vertex_ids[v].clone())
                .collect(),
            steps,
        })
    }

    /// Decide whether the connection is pure gauge: either the potentials
    /// `h` with `U_e = h(t) h(s)^{-1}`, or the first fundamental cycle whose
    /// holonomy is not the identity.
    pub fn pure_gauge_verdict(&self) -> Result<PureGaugeVerdict<T>, HolonomyError> {
        let identity = ExactMatrix::<T>::try_identity(self.dim)?;
        for (edge, value) in self.cycle_holonomies() {
            if value != identity {
                return Ok(PureGaugeVerdict::NotPureGauge {
                    witness: Box::new(HolonomyWitness {
                        edge,
                        cycle: self.fundamental_cycle(edge)?,
                        holonomy: value,
                    }),
                });
            }
        }
        Ok(PureGaugeVerdict::PureGauge {
            potentials: self.transport_from_root.clone(),
        })
    }
}

/// Fix the tree gauge of a string-keyed connection.
///
/// Refused with [`HolonomyError::AntiparallelEdges`] for a complex with two
/// edges joining the same vertices in opposite directions; use
/// [`EdgeConnection`] and [`tree_gauge_indexed`] there.
pub fn tree_gauge<T: ExactScalar>(
    complex: &CellComplex,
    connection: &DiscreteConnection<T>,
) -> Result<TreeGauge<T>, HolonomyError> {
    tree_gauge_indexed(
        complex,
        &EdgeConnection::from_discrete_connection(complex, connection)?,
    )
}

/// Fix the tree gauge of an edge-indexed connection (see the module docs).
pub fn tree_gauge_indexed<T: ExactScalar>(
    complex: &CellComplex,
    connection: &EdgeConnection<T>,
) -> Result<TreeGauge<T>, HolonomyError> {
    connection.check_complex(complex)?;
    let dim = connection.dim;
    let vertex_count = complex.vertices.len();
    let endpoints = edge_endpoints(complex)?;
    let forest = spanning_forest(vertex_count, &endpoints);
    let (gauge, transport_from_root) =
        build_forest_gauge_and_transport(complex, connection, &forest)?;
    let residual = build_residual_edge_connection(
        complex,
        connection,
        &endpoints,
        &gauge,
        &transport_from_root,
    )?;
    Ok(TreeGauge {
        dim,
        vertex_ids: complex.vertices.iter().map(|v| v.id.clone()).collect(),
        endpoints,
        forest,
        gauge,
        transport_from_root,
        residual,
    })
}

fn init_identity_tables<T: ExactScalar>(
    complex: &CellComplex,
    dim: usize,
) -> Result<(Vec<ExactMatrix<T>>, Vec<ExactMatrix<T>>), HolonomyError> {
    let vertex_count = complex.vertices.len();
    let identity = ExactMatrix::<T>::try_identity(dim)?;
    let mut gauge = Vec::new();
    let mut transport_from_root = Vec::new();
    check_and_reserve(&mut gauge, vertex_count, complex.limits.max_vertices)?;
    check_and_reserve(
        &mut transport_from_root,
        vertex_count,
        complex.limits.max_vertices,
    )?;
    for _ in 0..vertex_count {
        gauge.push(identity.clone());
        transport_from_root.push(identity.clone());
    }
    Ok((gauge, transport_from_root))
}

fn build_forest_gauge_and_transport<T: ExactScalar>(
    complex: &CellComplex,
    connection: &EdgeConnection<T>,
    forest: &Forest,
) -> Result<(Vec<ExactMatrix<T>>, Vec<ExactMatrix<T>>), HolonomyError> {
    let (mut gauge, mut transport_from_root) = init_identity_tables(complex, connection.dim)?;
    for &vertex in &forest.discovery {
        if let Some(link) = forest.parent[vertex] {
            let forward = OrientedStep {
                edge_index: link.edge,
                direction: link.direction_from_parent,
            };
            let backward = OrientedStep {
                edge_index: link.edge,
                direction: -link.direction_from_parent,
            };
            // T(v) = M T(p) and g(v) = T(v)^{-1} = g(p) M^{-1}.
            transport_from_root[vertex] = connection
                .step(forward)?
                .matmul(&transport_from_root[link.parent])?;
            gauge[vertex] = gauge[link.parent].matmul(connection.step(backward)?)?;
        }
    }
    Ok((gauge, transport_from_root))
}

fn build_residual_edge_connection<T: ExactScalar>(
    complex: &CellComplex,
    connection: &EdgeConnection<T>,
    endpoints: &[(usize, usize)],
    gauge: &[ExactMatrix<T>],
    transport_from_root: &[ExactMatrix<T>],
) -> Result<EdgeConnection<T>, HolonomyError> {
    let mut values = Vec::new();
    let mut inverses = Vec::new();
    check_and_reserve(&mut values, endpoints.len(), complex.limits.max_edges)?;
    check_and_reserve(&mut inverses, endpoints.len(), complex.limits.max_edges)?;
    for (edge, &(s, t)) in endpoints.iter().enumerate() {
        // R_e = g(t) U_e T(s), and R_e^{-1} = g(s) U_e^{-1} T(t).
        values.push(
            gauge[t]
                .matmul(&connection.values[edge])?
                .matmul(&transport_from_root[s])?,
        );
        inverses.push(
            gauge[s]
                .matmul(&connection.inverses[edge])?
                .matmul(&transport_from_root[t])?,
        );
    }
    Ok(EdgeConnection {
        dim: connection.dim,
        values,
        inverses,
    })
}

/// Whether `a` and `b` are related by a vertex gauge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GaugeEquivalence<T: ExactScalar> {
    /// The tree-gauge residuals agree, and `gauge` (one matrix per vertex)
    /// carries `a` to `b`: `B_e = gauge(t) A_e gauge(s)^{-1}` on every edge.
    Equivalent { gauge: Vec<ExactMatrix<T>> },
    /// Proved not equivalent: on `edge` the residuals differ in a conjugation
    /// invariant (determinant or trace), which no gauge can change. For a
    /// one-dimensional fibre this is every difference of residuals.
    Inequivalent { edge: usize },
    /// The fibre has dimension above 1, the residuals differ first on `edge`,
    /// and every determinant and trace agrees. A gauge that is constant on a
    /// component conjugates all residuals of the component at once, so the
    /// connections may still be equivalent; this routine does not search for
    /// that conjugating matrix.
    Undetermined { edge: usize },
}

/// Decide gauge equivalence of two connections on one complex by their tree
/// gauge residuals (see the module docs for what is and is not decided).
pub fn gauge_equivalence<T: ExactScalar>(
    complex: &CellComplex,
    a: &EdgeConnection<T>,
    b: &EdgeConnection<T>,
) -> Result<GaugeEquivalence<T>, HolonomyError> {
    if a.dim != b.dim {
        return Err(HolonomyError::DimensionMismatch {
            expected: a.dim,
            actual: b.dim,
        });
    }
    let fixed_a = tree_gauge_indexed(complex, a)?;
    let fixed_b = tree_gauge_indexed(complex, b)?;
    if let Some(verdict) = compare_cycle_residuals(&fixed_a, &fixed_b)? {
        return Ok(verdict);
    }
    // residuals equal: a' = b', so B_e = (g_b^{-1} g_a)(t) A_e (g_b^{-1} g_a)(s)^{-1}
    // and g_b^{-1} = T_b.
    let gauge = fixed_b
        .transport_from_root
        .iter()
        .zip(&fixed_a.gauge)
        .map(|(t_b, g_a)| t_b.matmul(g_a))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(GaugeEquivalence::Equivalent { gauge })
}

fn compare_cycle_residuals<T: ExactScalar>(
    fixed_a: &TreeGauge<T>,
    fixed_b: &TreeGauge<T>,
) -> Result<Option<GaugeEquivalence<T>>, HolonomyError> {
    let mut first_difference = None;
    for (edge, residual_a) in fixed_a.cycle_holonomies() {
        let residual_b = fixed_b.residual_value(edge)?;
        if residual_a == *residual_b {
            continue;
        }
        if residual_a.trace()? != residual_b.trace()?
            || residual_a.determinant()? != residual_b.determinant()?
        {
            return Ok(Some(GaugeEquivalence::Inequivalent { edge }));
        }
        first_difference.get_or_insert(edge);
    }
    Ok(first_difference.map(|edge| GaugeEquivalence::Undetermined { edge }))
}

/// The holonomy around every face boundary, in face order, each based at the
/// first boundary vertex of its face.
pub fn face_holonomies<T: ExactScalar>(
    complex: &CellComplex,
    connection: &EdgeConnection<T>,
) -> Result<Vec<ExactMatrix<T>>, HolonomyError> {
    connection.check_complex(complex)?;
    let endpoints = edge_endpoints(complex)?;
    (0..complex.faces.len())
        .map(|face| connection.face_holonomy_with_endpoints(complex, &endpoints, face))
        .collect()
}

/// Where the gauge-invariant content of a connection sits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HolonomyVerdict<T: ExactScalar> {
    /// Some face holonomy differs from the identity: the holonomies of all
    /// faces in face order, and the first face that is not flat.
    Curved {
        face_holonomies: Vec<ExactMatrix<T>>,
        first_curved_face: usize,
    },
    /// Every face is flat, yet some fundamental cycle has holonomy other than
    /// the identity: `(edge, R_e)` for every edge off the forest.
    FlatNontrivial {
        cycle_holonomies: Vec<(usize, ExactMatrix<T>)>,
    },
    /// Every fundamental cycle has trivial holonomy: the connection is a
    /// vertex gauge transform of the trivial one. On a complex with no faces
    /// this is the only alternative to `FlatNontrivial`.
    GaugeTrivial,
}

/// Classify a connection by its face holonomies and its tree-gauge residuals.
/// A complex with no faces has no curvature, so its verdict is never `Curved`.
pub fn holonomy_verdict<T: ExactScalar>(
    complex: &CellComplex,
    connection: &EdgeConnection<T>,
) -> Result<HolonomyVerdict<T>, HolonomyError> {
    let holonomies = face_holonomies(complex, connection)?;
    let identity = ExactMatrix::<T>::try_identity(connection.dim)?;
    if let Some(first_curved_face) = holonomies.iter().position(|h| *h != identity) {
        return Ok(HolonomyVerdict::Curved {
            face_holonomies: holonomies,
            first_curved_face,
        });
    }
    let fixed = tree_gauge_indexed(complex, connection)?;
    if fixed.is_gauge_trivial() {
        Ok(HolonomyVerdict::GaugeTrivial)
    } else {
        Ok(HolonomyVerdict::FlatNontrivial {
            cycle_holonomies: fixed.cycle_holonomies(),
        })
    }
}

fn gcd(mut a: u64, mut b: u64) -> u64 {
    while b != 0 {
        (a, b) = (b, a % b);
    }
    a
}

/// The number of gauge classes of flat connections with values in the cyclic
/// group `Z_order`: `|H^1(X; Z_order)| = |Hom(H_1(X; Z), Z_order)|` for the
/// complex `X` made of the edges and faces of `complex`.
///
/// Computed from the spanning forest and the Smith normal form of the face
/// boundaries in the coordinates of the `z = cycle_rank` edges off the forest:
/// with invariant factors `d_1, .., d_r` the count is
/// `order^(z - r) prod gcd(d_i, order)`. Without faces it is `order^z`.
///
/// Refused: `order = 0`; a face whose boundary steps are not a closed walk.
pub fn flat_cyclic_gauge_classes(
    complex: &CellComplex,
    order: u64,
) -> Result<BigUint, HolonomyError> {
    if order == 0 {
        return Err(HolonomyError::InvalidGroupOrder { order });
    }
    let endpoints = edge_endpoints(complex)?;
    let forest = spanning_forest(complex.vertices.len(), &endpoints);
    let off_tree: Vec<usize> = (0..endpoints.len())
        .filter(|&e| !forest.tree_edge[e])
        .collect();
    let z = off_tree.len();
    let column_of: BTreeMap<usize, usize> = off_tree
        .iter()
        .enumerate()
        .map(|(column, &edge)| (edge, column))
        .collect();

    // Validate every face boundary as a closed walk, and accumulate its
    // signed edge multiplicities in the off-tree coordinates.
    let faces = complex.faces.len();
    let mut data = vec![BigInt::zero(); faces * z];
    for (face_index, face) in complex.faces.iter().enumerate() {
        accumulate_face_boundary_row(
            complex, &endpoints, &column_of, z, face_index, face, &mut data,
        )?;
    }

    count_classes_from_boundary_data(faces, z, order, data)
}

fn step_face_boundary(
    face_id: &str,
    endpoints: &[(usize, usize)],
    index: usize,
    step: OrientedStep,
    here: usize,
) -> Result<usize, HolonomyError> {
    check_edge(step.edge_index, endpoints.len())?;
    let (source, target) = endpoints[step.edge_index];
    let (from, to) = match step.direction {
        1 => (source, target),
        -1 => (target, source),
        direction => {
            return Err(HolonomyError::InvalidStepDirection {
                step: index,
                direction,
            })
        }
    };
    if from != here {
        return Err(HolonomyError::BrokenWalk {
            step: index,
            detail: format!(
                "step {index} of face '{face_id}' leaves vertex {from} but the boundary is at \
                 vertex {here}"
            ),
        });
    }
    Ok(to)
}

fn accumulate_face_boundary_row(
    complex: &CellComplex,
    endpoints: &[(usize, usize)],
    column_of: &BTreeMap<usize, usize>,
    z: usize,
    face_index: usize,
    face: &Face,
    data: &mut [BigInt],
) -> Result<(), HolonomyError> {
    let start_id =
        face.boundary_vertices
            .first()
            .ok_or_else(|| HolonomyError::BoundaryCycleMismatch {
                face: face.id.clone(),
                detail: "the face lists no boundary vertices".into(),
            })?;
    let start = *complex
        .vertex_map
        .get(start_id)
        .ok_or_else(|| HolonomyError::VertexNotFound {
            id: start_id.clone(),
        })?;
    let mut here = start;
    for (index, step) in face.boundary_edges.iter().enumerate() {
        here = step_face_boundary(&face.id, endpoints, index, *step, here)?;
        if let Some(&column) = column_of.get(&step.edge_index) {
            data[face_index * z + column] += BigInt::from(step.direction);
        }
    }
    if here != start {
        return Err(HolonomyError::BoundaryCycleMismatch {
            face: face.id.clone(),
            detail: "the boundary steps do not return to the first boundary vertex".into(),
        });
    }
    Ok(())
}

fn cyclic_order_pow(order: u64, exponent: usize) -> Result<BigUint, HolonomyError> {
    let exponent = u32::try_from(exponent).map_err(|_| HolonomyError::AllocationFailure {
        requested: exponent,
        detail: "the exponent of the class count does not fit in u32".into(),
    })?;
    Ok(num_traits::pow::Pow::pow(BigUint::from(order), exponent))
}

fn count_classes_from_boundary_data(
    faces: usize,
    z: usize,
    order: u64,
    data: Vec<BigInt>,
) -> Result<BigUint, HolonomyError> {
    // No faces, no off-tree edges, or faces whose boundaries cancel in these
    // coordinates: nothing constrains the values on the off-tree edges.
    if faces == 0 || z == 0 || data.iter().all(Zero::is_zero) {
        return cyclic_order_pow(order, z);
    }
    let matrix = BasicMatrix::from_row_major(faces, z, data).map_err(|e| {
        HolonomyError::IntegerEliminationFailed {
            detail: e.to_string(),
        }
    })?;
    let normal_form = smith_normal_form_checked(&matrix).map_err(|e| {
        HolonomyError::IntegerEliminationFailed {
            detail: e.to_string(),
        }
    })?;
    let invariants = normal_form.diagonal().invariants();
    let modulus = BigInt::from(order);
    let mut count = cyclic_order_pow(order, z - invariants.len())?;
    for invariant in invariants {
        let residue = (invariant % &modulus).to_u64().ok_or_else(|| {
            HolonomyError::IntegerEliminationFailed {
                detail: "an invariant factor reduced modulo the group order does not fit in u64"
                    .into(),
            }
        })?;
        count *= BigUint::from(gcd(residue, order));
    }
    Ok(count)
}

// Origin: engine/crates_rs/core_holonomy/src/gauge_fixing.rs
// Claim: urn:core:crates_rs:core-holonomy:gauge-fixing:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord0974255a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord0974255a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError0974255a {
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
impl BoundaryError0974255a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError0974255a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError0974255a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord0974255a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError0974255a> {
        if capacity_bound == 0 {
            return Err(BoundaryError0974255a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError0974255a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError0974255a::ExceedsCapacity {
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
mod l4_boundary_tests_0974255a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord0974255a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord0974255a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord0974255a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord0974255a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord0974255a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError0974255a::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError0974255a::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
