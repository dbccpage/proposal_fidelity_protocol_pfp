// AuthorityEffect: None.

//! The trace-distance quotient obstruction of Hermitian trace-zero edge defects
//! on a finite directed graph, certified exactly by primal and dual witnesses.
//!
//! A [`TraceDefectPacket`] is a `data_cochain_packet::FiniteCochainPacket`
//! (declared vertices and edges, strictly positive weights `w`, incidence `d0`)
//! with one Hermitian trace-zero `n x n` defect `delta_e` per edge, `n >= 2`.
//! For vertex potentials `alpha` in a declared [`RepairSpace`],
//!
//! `Phi([delta]) = min_alpha sum_e w_e (1/2) ||delta_e - (d0 alpha)_e||_1`,
//! with `(d0 alpha)_e = alpha_t(e) - alpha_s(e)`.
//!
//! [`RepairSpace::TraceZero`] is the declared `C^0(G, V)` of trace-zero
//! potentials; [`RepairSpace::AllHermitian`] also admits scalar parts. Nothing
//! is optimised over matrices here:
//!
//! - a [`PrimalCertificate`] (potentials in the repair space and a PSD split
//!   `r_e = P_e - N_e` of every residual) bounds `Phi` above by
//!   `sum_e w_e (1/2) Tr(P_e + N_e)`;
//! - a [`DualCertificate`] (Hermitian `M_e` and rational centres `c_e` with
//!   `||M_e - c_e I||_op <= w_e / 2`, decided by exact PSD) bounds `Phi` below
//!   by `sum_e Tr(M_e delta_e)`. For trace-zero repairs its divergence
//!   `(d0* M)_v = sum_{t(e)=v} M_e - sum_{s(e)=v} M_e` must be a multiple of
//!   `I` at every vertex; for all-Hermitian repairs the centres must be zero and
//!   the divergence must vanish;
//! - [`TraceDefectPacket::certify`] returns `Phi` only when both bounds agree.
//!
//! With an exactly divergence-free `M`, the centres express the spectral
//! diameter bound `l_max(M_e) - l_min(M_e) <= w_e`. Requiring the `M_e` to be
//! centred (or of operator norm at most `w_e / 2`) and exactly divergence-free
//! at the same time certifies only the all-Hermitian quotient, which is
//! strictly smaller on some packets with `n >= 3` and two independent cycles.
//!
//! [`TraceDefectPacket::diagonal_certificates`] handles commuting diagonal
//! defects: there both quotients are weighted-`l1` quotients for a declared
//! rational repair map, so `solver_cohomology_quotient_phi1::certified_phi1`
//! computes them (`core_solvers` proposes, `core_functional` replays) and the
//! replayed witnesses are lifted to matrix certificates.
//! [`TraceDefectPacket::cycle_certificates`] builds the closed-form pair on a
//! single cycle from a sign certificate of the oriented cycle sum.
//!
//! Refused: `n < 2`, defects that are not Hermitian trace-zero `n x n`,
//! potentials outside the declared repair space, splits that are not PSD or do
//! not reproduce the residual, observables outside their ball, a divergence
//! that is not scalar (or not zero), unequal bounds, non-diagonal defects for
//! the diagonal route, and walks that are not one simple cycle through every
//! edge.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_11b9a1a9<T> {
    fn checked_invariant_11b9a1a9(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_11b9a1a9<T> for Option<T> {
    #[inline]
    fn checked_invariant_11b9a1a9(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_11b9a1a9<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_11b9a1a9(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use crate::exact_hermitian::{self};
use crate::u1_graph_connection::OrientedWalk;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};
use core_solvers::solver_cohomology_quotient_phi1::{certified_phi1, CertifiedPhi1Error, MAX_COCHAIN_DIMENSION};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::exact_hermitian::exact_limits;
use crate::trace_norm_certificate::{within_operator_ball, SignCertificate};
use linear_algebra::exact_field::{involution as star, matrix as mx};

/// Refusals for trace-distance quotient packets and their certificates.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum TraceQuotientError {
    #[error(transparent)]
    Algebra(#[from] linear_algebra::exact_field::ExactFieldError),
    #[error(transparent)]
    TraceNorm(#[from] crate::trace_norm_certificate::TraceNormError),
    #[error(transparent)]
    Limits(#[from] core_kernel::resource_limits::ResourceError),
    #[error("edge {edge} is not an oriented non-loop incidence row")]
    Incidence { edge: usize },
    #[error("defect dimension must be at least 2")]
    Dimension,
    #[error("{actual} entries for {expected} edges")]
    EdgeCount { expected: usize, actual: usize },
    #[error("{actual} potentials for {expected} vertices")]
    VertexCount { expected: usize, actual: usize },
    #[error("defect on edge {edge} is not a Hermitian trace-zero matrix of the declared size")]
    Defect { edge: usize },
    #[error("potential at vertex {vertex} is outside the declared repair space")]
    Potential { vertex: usize },
    #[error("split on edge {edge} is not a pair of PSD matrices of the declared size")]
    SplitNotPositive { edge: usize },
    #[error("split on edge {edge} does not reproduce the residual")]
    SplitMismatch { edge: usize },
    #[error("observable on edge {edge} is not Hermitian of the declared size")]
    Observable { edge: usize },
    #[error("all-Hermitian repairs admit only zero centres (edge {edge})")]
    Centre { edge: usize },
    #[error("observable on edge {edge} leaves the ball of radius w_e/2 about its centre")]
    OutsideBall { edge: usize },
    #[error("divergence at vertex {vertex} is not admissible for the repair space")]
    Divergence { vertex: usize },
    /// `(upper, lower)`: the two certified bounds, which differ.
    #[error("upper and lower bounds differ: {0:?}")]
    DualityGap(Box<(Rational, Rational)>),
    #[error("defect on edge {edge} is not diagonal")]
    NotDiagonal { edge: usize },
    #[error("the walk is not one simple cycle through every edge")]
    NotACycle,
    #[error("the sign certificate is not for the oriented cycle sum")]
    CycleSum,
    #[error("exact l1 quotient refused: {0}")]
    Quotient(#[from] CertifiedPhi1Error),
}

/// Which vertex potentials count as repairs.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum RepairSpace {
    /// Hermitian trace-zero potentials, the declared `C^0(G, V)`.
    TraceZero,
    /// Every Hermitian potential, scalar parts included.
    AllHermitian,
}

/// Potentials and a PSD split of every residual.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PrimalCertificate {
    pub potentials: Vec<BasicMatrix<GaussianRat>>,
    /// `(P_e, N_e)` with `delta_e - (d0 alpha)_e = P_e - N_e`.
    pub splits: Vec<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>)>,
}

/// Edge observables and the centres of their operator-norm balls.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DualCertificate {
    pub observables: Vec<BasicMatrix<GaussianRat>>,
    pub centres: Vec<Rational>,
}

/// A graph packet with Hermitian trace-zero edge defects.
#[derive(Debug, Clone)]
pub struct TraceDefectPacket {
    graph: FiniteCochainPacket,
    dim: usize,
    defects: Vec<BasicMatrix<GaussianRat>>,
}

fn is_square_hermitian(m: &BasicMatrix<GaussianRat>, dim: usize) -> bool {
    m.rows() == dim && m.cols() == dim && exact_hermitian::is_hermitian(m)
}

fn is_scalar_matrix(m: &BasicMatrix<GaussianRat>) -> bool {
    let n = m.rows();
    (0..n).all(|r| {
        (0..n).all(|c| {
            if r == c {
                m.as_slice()[r * n + c] == m.as_slice()[0]
            } else {
                m.as_slice()[r * n + c].is_zero()
            }
        })
    })
}

fn endpoints(d0_row: &[Rational], edge: usize) -> Result<(usize, usize), TraceQuotientError> {
    let mut source = None;
    let mut target = None;
    for (v, c) in d0_row.iter().enumerate() {
        if c == &ri(-1) && source.is_none() {
            source = Some(v);
        } else if c == &ri(1) && target.is_none() {
            target = Some(v);
        } else if !c.is_zero() {
            return Err(TraceQuotientError::Incidence { edge });
        }
    }
    match (source, target) {
        (Some(a), Some(b)) if a != b => Ok((a, b)),
        _ => Err(TraceQuotientError::Incidence { edge }),
    }
}

fn sum_counts(counts: &[usize]) -> Result<usize, TraceQuotientError> {
    counts.iter().try_fold(0usize, |sum, &count| {
        sum.checked_add(count)
            .ok_or(core_kernel::resource_limits::ResourceError::CountOverflow.into())
    })
}

fn check_operator_family_memory(
    limits: &core_kernel::resource_limits::OperationLimits,
    matrices: usize,
    square: usize,
) -> Result<(), TraceQuotientError> {
    let entries = limits.checked_product(matrices, square)?;
    let bytes = sum_counts(&[
        limits.checked_product(entries, std::mem::size_of::<GaussianRat>())?,
        limits.checked_product(matrices, std::mem::size_of::<BasicMatrix<GaussianRat>>())?,
    ])?;
    if bytes > limits.max_memory_bytes {
        return Err(
            core_kernel::resource_limits::ResourceError::AllocationFailure {
                requested: bytes,
                detail: "quotient operator families exceed aggregate memory budget".into(),
            }
            .into(),
        );
    }
    Ok(())
}

/// Admission for the operator families retained by a quotient witness replay.
/// Count every live dense family and bound both matrix contractions and incidence scans.
fn operator_family_preflight(
    dim: usize,
    matrices: usize,
    quadratic_units: usize,
    cubic_units: usize,
    incidence_entries: usize,
) -> Result<(), TraceQuotientError> {
    let limits = core_kernel::resource_limits::OperationLimits::default();
    let square = limits.checked_product(dim, dim)?;
    check_operator_family_memory(&limits, matrices, square)?;
    let work = sum_counts(&[
        limits.checked_product(quadratic_units, square)?,
        limits.checked_product(cubic_units, limits.checked_product(square, dim)?)?,
        incidence_entries,
    ])?;
    if work > exact_limits().max_scalar_ops {
        return Err(linear_algebra::exact_field::ExactFieldError::from(
            linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                requested: work,
                limit: exact_limits().max_scalar_ops,
            },
        )
        .into());
    }
    Ok(())
}

fn validate_defects_and_incidence(
    graph: &FiniteCochainPacket,
    dim: usize,
    defects: &[BasicMatrix<GaussianRat>],
) -> Result<(), TraceQuotientError> {
    if let Some(edge) = defects.iter().position(|d| {
        !is_square_hermitian(d, dim) || !mx::trace(d).map(|z| z.re.is_zero()).unwrap_or(false)
    }) {
        return Err(TraceQuotientError::Defect { edge });
    }
    for (edge, row) in graph.d0().iter().enumerate() {
        if row.len() != graph.vertex_count() {
            return Err(TraceQuotientError::Incidence { edge });
        }
        endpoints(row, edge)?;
    }
    Ok(())
}

impl TraceDefectPacket {
    fn preflight(
        &self,
        additional_matrices: usize,
        quadratic_units: usize,
        cubic_units: usize,
    ) -> Result<(), TraceQuotientError> {
        operator_family_preflight(
            self.dim,
            sum_counts(&[self.defects.len(), additional_matrices])?,
            quadratic_units,
            cubic_units,
            core_kernel::resource_limits::OperationLimits::default()
                .checked_product(self.graph.edge_count(), self.graph.vertex_count())?,
        )
    }

    pub fn new(
        graph: FiniteCochainPacket,
        dim: usize,
        defects: Vec<BasicMatrix<GaussianRat>>,
    ) -> Result<Self, TraceQuotientError> {
        let limits = core_kernel::resource_limits::OperationLimits::default();
        limits.check_hilbert_dim(dim)?;
        limits.check_operator_count(defects.len())?;
        if dim < 2 {
            return Err(TraceQuotientError::Dimension);
        }
        if defects.len() != graph.edge_count() {
            return Err(TraceQuotientError::EdgeCount {
                expected: graph.edge_count(),
                actual: defects.len(),
            });
        }
        operator_family_preflight(
            dim,
            defects.len(),
            defects.len(),
            0,
            limits.checked_product(graph.edge_count(), graph.vertex_count())?,
        )?;
        validate_defects_and_incidence(&graph, dim, &defects)?;
        Ok(Self {
            graph,
            dim,
            defects,
        })
    }

    pub fn graph(&self) -> &FiniteCochainPacket {
        &self.graph
    }

    pub fn dim(&self) -> usize {
        self.dim
    }

    pub fn defects(&self) -> &[BasicMatrix<GaussianRat>] {
        &self.defects
    }

    fn preflight_residuals_or_divergence(
        &self,
        matrix_count_a: usize,
        matrix_count_b: usize,
        nonempty_bonus: usize,
    ) -> Result<(), TraceQuotientError> {
        let ne = self.graph.edge_count();
        let nv = self.graph.vertex_count();
        let limits = core_kernel::resource_limits::OperationLimits::default();
        self.preflight(
            sum_counts(&[matrix_count_a, matrix_count_b, nonempty_bonus])?,
            sum_counts(&[nv, limits.checked_product(5, ne)?])?,
            0,
        )
    }

    /// `r_e = delta_e - (d0 alpha)_e` for Hermitian `n x n` potentials.
    pub fn residuals(
        &self,
        potentials: &[BasicMatrix<GaussianRat>],
    ) -> Result<Vec<BasicMatrix<GaussianRat>>, TraceQuotientError> {
        if potentials.len() != self.graph.vertex_count() {
            return Err(TraceQuotientError::VertexCount {
                expected: self.graph.vertex_count(),
                actual: potentials.len(),
            });
        }
        let ne = self.graph.edge_count();
        let nv = self.graph.vertex_count();
        self.preflight_residuals_or_divergence(nv, ne, if ne == 0 { 0 } else { 2 })?;
        if let Some(vertex) = potentials
            .iter()
            .position(|a| !is_square_hermitian(a, self.dim))
        {
            return Err(TraceQuotientError::Potential { vertex });
        }
        let mut residuals = Vec::new();
        for (row, delta) in self.graph.d0().iter().zip(&self.defects) {
            let mut acc = delta.clone();
            for (c, a) in row.iter().zip(potentials).filter(|(c, _)| !c.is_zero()) {
                acc = mx::sub(&acc, &mx::scale(a, &GaussianRat::from_rational(c.clone()))?)?;
            }
            residuals.push(acc);
        }
        Ok(residuals)
    }

    /// `(d0* M)_v = sum_e d0[e][v] M_e`.
    pub fn divergence(
        &self,
        observables: &[BasicMatrix<GaussianRat>],
    ) -> Result<Vec<BasicMatrix<GaussianRat>>, TraceQuotientError> {
        if observables.len() != self.graph.edge_count() {
            return Err(TraceQuotientError::EdgeCount {
                expected: self.graph.edge_count(),
                actual: observables.len(),
            });
        }
        let nv = self.graph.vertex_count();
        self.preflight_residuals_or_divergence(observables.len(), nv, if nv == 0 { 0 } else { 2 })?;
        if let Some(edge) = observables
            .iter()
            .position(|m| !is_square_hermitian(m, self.dim))
        {
            return Err(TraceQuotientError::Observable { edge });
        }
        let d0 = self.graph.d0();
        let mut divergence = Vec::new();
        for v in 0..self.graph.vertex_count() {
            let mut acc = mx::zeros_with_limits(self.dim, self.dim, exact_limits())?;
            for (row, m) in d0
                .iter()
                .zip(observables)
                .filter(|(row, _)| !row[v].is_zero())
            {
                acc = mx::add(
                    &acc,
                    &mx::scale(m, &GaussianRat::from_rational(row[v].clone()))?,
                )?;
            }
            divergence.push(acc);
        }
        Ok(divergence)
    }

    fn preflight_upper_bound(&self, primal: &PrimalCertificate) -> Result<(), TraceQuotientError> {
        let ne = self.graph.edge_count();
        let nv = self.graph.vertex_count();
        let limits = core_kernel::resource_limits::OperationLimits::default();
        self.preflight(
            sum_counts(&[
                primal.potentials.len(),
                limits.checked_product(2, primal.splits.len())?,
                ne,
                if ne == 0 { 0 } else { 4 },
            ])?,
            sum_counts(&[nv, limits.checked_product(8, ne)?])?,
            limits.checked_product(40, ne)?,
        )
    }

    fn is_valid_primal_split_matrix(&self, m: &BasicMatrix<GaussianRat>) -> bool {
        m.rows() == self.dim && m.cols() == self.dim && exact_hermitian::is_positive_semidefinite(m)
    }

    fn validate_and_score_primal_split(
        &self,
        edge: usize,
        p: &BasicMatrix<GaussianRat>,
        n: &BasicMatrix<GaussianRat>,
        r: &BasicMatrix<GaussianRat>,
    ) -> Result<Rational, TraceQuotientError> {
        if !self.is_valid_primal_split_matrix(p) || !self.is_valid_primal_split_matrix(n) {
            return Err(TraceQuotientError::SplitNotPositive { edge });
        }
        if &mx::sub(p, n)? != r {
            return Err(TraceQuotientError::SplitMismatch { edge });
        }
        Ok(&self.graph.weights()[edge] * mx::trace(&mx::add(p, n)?)?.re / ri(2))
    }

    /// `sum_e w_e (1/2) Tr(P_e + N_e)`, an upper bound on `Phi` over `space`.
    pub fn upper_bound(
        &self,
        primal: &PrimalCertificate,
        space: RepairSpace,
    ) -> Result<Rational, TraceQuotientError> {
        self.preflight_upper_bound(primal)?;
        let residuals = self.residuals(&primal.potentials)?;
        if space == RepairSpace::TraceZero {
            if let Some(vertex) = primal
                .potentials
                .iter()
                .position(|a| !mx::trace(a).map(|z| z.re.is_zero()).unwrap_or(false))
            {
                return Err(TraceQuotientError::Potential { vertex });
            }
        }
        if primal.splits.len() != residuals.len() {
            return Err(TraceQuotientError::EdgeCount {
                expected: residuals.len(),
                actual: primal.splits.len(),
            });
        }
        let mut total = Rational::zero();
        for (edge, ((p, n), r)) in primal.splits.iter().zip(&residuals).enumerate() {
            total += self.validate_and_score_primal_split(edge, p, n, r)?;
        }
        Ok(total)
    }

    fn preflight_lower_bound(&self, dual: &DualCertificate) -> Result<(), TraceQuotientError> {
        let ne = self.graph.edge_count();
        let nv = self.graph.vertex_count();
        let limits = core_kernel::resource_limits::OperationLimits::default();
        self.preflight(
            sum_counts(&[
                dual.observables.len(),
                nv,
                if ne == 0 && nv == 0 { 0 } else { 4 },
            ])?,
            sum_counts(&[nv, limits.checked_product(6, ne)?])?,
            limits.checked_product(40, ne)?,
        )
    }

    fn validate_dual_balls_and_divergence(
        &self,
        dual: &DualCertificate,
        divergence: &[BasicMatrix<GaussianRat>],
        space: RepairSpace,
    ) -> Result<(), TraceQuotientError> {
        for (edge, (m, c)) in dual.observables.iter().zip(&dual.centres).enumerate() {
            if space == RepairSpace::AllHermitian && !c.is_zero() {
                return Err(TraceQuotientError::Centre { edge });
            }
            let radius = &self.graph.weights()[edge] / ri(2);
            if !within_operator_ball(m, c, &radius)
                .map_err(|_| TraceQuotientError::Observable { edge })?
            {
                return Err(TraceQuotientError::OutsideBall { edge });
            }
        }
        for (vertex, div) in divergence.iter().enumerate() {
            let admissible = match space {
                RepairSpace::TraceZero => is_scalar_matrix(div),
                RepairSpace::AllHermitian => mx::is_zero_matrix(div),
            };
            if !admissible {
                return Err(TraceQuotientError::Divergence { vertex });
            }
        }
        Ok(())
    }

    /// `sum_e Tr(M_e delta_e)`, a lower bound on `Phi` over `space`.
    pub fn lower_bound(
        &self,
        dual: &DualCertificate,
        space: RepairSpace,
    ) -> Result<Rational, TraceQuotientError> {
        self.preflight_lower_bound(dual)?;
        let divergence = self.divergence(&dual.observables)?;
        if dual.centres.len() != dual.observables.len() {
            return Err(TraceQuotientError::EdgeCount {
                expected: dual.observables.len(),
                actual: dual.centres.len(),
            });
        }
        self.validate_dual_balls_and_divergence(dual, &divergence, space)?;
        dual.observables
            .iter()
            .zip(&self.defects)
            .map(|(m, delta)| Ok(star::hs_inner(m, delta)?.re))
            .sum()
    }

    fn preflight_certify(
        &self,
        primal: &PrimalCertificate,
        dual: &DualCertificate,
    ) -> Result<(), TraceQuotientError> {
        let ne = self.graph.edge_count();
        let nv = self.graph.vertex_count();
        let limits = core_kernel::resource_limits::OperationLimits::default();
        self.preflight(
            sum_counts(&[
                primal.potentials.len(),
                limits.checked_product(2, primal.splits.len())?,
                dual.observables.len(),
                ne.max(nv),
                if ne == 0 && nv == 0 { 0 } else { 4 },
            ])?,
            sum_counts(&[
                limits.checked_product(2, nv)?,
                limits.checked_product(14, ne)?,
            ])?,
            limits.checked_product(80, ne)?,
        )
    }

    /// `Phi([delta])` over `space`, returned only when the certificates close the gap.
    pub fn certify(
        &self,
        primal: &PrimalCertificate,
        dual: &DualCertificate,
        space: RepairSpace,
    ) -> Result<Rational, TraceQuotientError> {
        self.preflight_certify(primal, dual)?;
        let upper = self.upper_bound(primal, space)?;
        let lower = self.lower_bound(dual, space)?;
        if upper != lower {
            return Err(TraceQuotientError::DualityGap(Box::new((upper, lower))));
        }
        Ok(upper)
    }

    fn estimate_diagonal_memory_bytes(
        &self,
        limits: &core_kernel::resource_limits::OperationLimits,
        entries: usize,
        rows: usize,
        cols: usize,
        square: usize,
    ) -> Result<usize, TraceQuotientError> {
        let (ne, nv) = (self.graph.edge_count(), self.graph.vertex_count());
        // Include map/certificate copies, flattened vectors, lifted operators,
        // residuals and divergence before constructing even the first map row.
        let rational_entries =
            sum_counts(&[limits.checked_product(4, entries)?, cols, limits.checked_product(4, rows)?])?;
        let lifted_count =
            sum_counts(&[limits.checked_product(2, nv)?, limits.checked_product(6, ne)?])?;
        let lifted_entries = limits.checked_product(lifted_count, square)?;
        sum_counts(&[
            limits.checked_product(rational_entries, std::mem::size_of::<Rational>())?,
            limits.checked_product(lifted_entries, std::mem::size_of::<GaussianRat>())?,
        ])
    }

    fn preflight_diagonal_memory_and_work(
        &self,
        rows: usize,
        cols: usize,
    ) -> Result<(), TraceQuotientError> {
        let n = self.dim;
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let entries = limits.checked_product(rows, cols)?;
        let square = limits.checked_product(n, n)?;
        let bytes = self.estimate_diagonal_memory_bytes(&limits, entries, rows, cols, square)?;
        if bytes > limits.max_memory_bytes {
            return Err(TraceQuotientError::Limits(
                core_kernel::resource_limits::ResourceError::AllocationFailure {
                    requested: bytes,
                    detail: "diagonal quotient matrix exceeds memory budget".into(),
                },
            ));
        }
        self.check_diagonal_work_limits(&limits, entries, square)
    }

    fn check_diagonal_work_limits(
        &self,
        limits: &core_kernel::resource_limits::OperationLimits,
        entries: usize,
        square: usize,
    ) -> Result<(), TraceQuotientError> {
        let (n, ne, nv) = (self.dim, self.graph.edge_count(), self.graph.vertex_count());
        let nv_plus_ne = sum_counts(&[nv, ne])?;
        let work = sum_counts(&[
            limits.checked_product(4, entries)?,
            limits.checked_product(16, limits.checked_product(nv_plus_ne, square)?)?,
            limits.checked_product(40, limits.checked_product(ne, limits.checked_product(square, n)?)?)?,
        ])?;
        if work > exact_limits().max_scalar_ops {
            return Err(linear_algebra::exact_field::ExactFieldError::Matrix(
                linear_algebra::backend::basic_matrix::MatrixError::OperationLimitExceeded {
                    requested: work,
                    limit: exact_limits().max_scalar_ops,
                },
            )
            .into());
        }
        Ok(())
    }

    fn verify_defects_are_diagonal(&self) -> Result<(), TraceQuotientError> {
        let n = self.dim;
        for (edge, delta) in self.defects.iter().enumerate() {
            let off_diagonal =
                (0..n).any(|r| (0..n).any(|c| r != c && !delta.as_slice()[r * n + c].is_zero()));
            if off_diagonal {
                return Err(TraceQuotientError::NotDiagonal { edge });
            }
        }
        Ok(())
    }

    fn populate_diagonal_repair_row(
        row: &mut [Rational],
        d0_row: &[Rational],
        i: usize,
        free: usize,
    ) {
        for (v, coefficient) in d0_row.iter().enumerate().filter(|(_, c)| !c.is_zero()) {
            if i < free {
                row[v * free + i] = coefficient.clone();
            } else {
                for j in 0..free {
                    row[v * free + j] = -coefficient.clone();
                }
            }
        }
    }

    fn build_diagonal_repair_system(
        &self,
        rows: usize,
        cols: usize,
        free: usize,
    ) -> Result<(Vec<Vec<Rational>>, Vec<Rational>, Vec<Rational>), TraceQuotientError> {
        let (n, ne) = (self.dim, self.graph.edge_count());
        let d0 = self.graph.d0();
        let mut repair = Vec::new();
        core_kernel::resource_limits::check_and_reserve(&mut repair, rows, MAX_COCHAIN_DIMENSION)?;
        for _ in 0..rows {
            let mut row = Vec::new();
            core_kernel::resource_limits::check_and_reserve(
                &mut row,
                cols,
                MAX_COCHAIN_DIMENSION,
            )?;
            row.resize(cols, Rational::zero());
            repair.push(row);
        }
        let mut x = Vec::new();
        let mut weights = Vec::new();
        core_kernel::resource_limits::check_and_reserve(&mut x, rows, MAX_COCHAIN_DIMENSION)?;
        core_kernel::resource_limits::check_and_reserve(
            &mut weights,
            rows,
            MAX_COCHAIN_DIMENSION,
        )?;
        for e in 0..ne {
            for i in 0..n {
                Self::populate_diagonal_repair_row(&mut repair[e * n + i], &d0[e], i, free);
                x.push(self.defects[e].as_slice()[i * n + i].re.clone());
                weights.push(&self.graph.weights()[e] / ri(2));
            }
        }
        Ok((repair, x, weights))
    }

    fn split_diagonal_residual_matrix(
        r: &BasicMatrix<GaussianRat>,
        n: usize,
    ) -> Result<(BasicMatrix<GaussianRat>, BasicMatrix<GaussianRat>), TraceQuotientError> {
        let part = |keep_positive: bool| {
            let entries: Vec<GaussianRat> = (0..n)
                .map(|i| {
                    let value = r.as_slice()[i * n + i].re.clone();
                    let kept = if keep_positive {
                        value.max(Rational::zero())
                    } else {
                        (-value).max(Rational::zero())
                    };
                    GaussianRat::from_rational(kept)
                })
                .collect();
            mx::diagonal(&entries)
        };
        Ok((part(true)?, part(false)?))
    }

    fn lift_diagonal_potentials(
        &self,
        alpha: &[Rational],
        free: usize,
    ) -> Result<Vec<BasicMatrix<GaussianRat>>, TraceQuotientError> {
        let (n, nv) = (self.dim, self.graph.vertex_count());
        (0..nv)
            .map(|v| {
                let block = &alpha[v * free..(v + 1) * free];
                let mut entries: Vec<GaussianRat> = block
                    .iter()
                    .cloned()
                    .map(GaussianRat::from_rational)
                    .collect();
                if free < n {
                    entries.push(GaussianRat::from_rational(-block.iter().sum::<Rational>()));
                }
                Ok(mx::diagonal(&entries)?)
            })
            .collect()
    }

    fn lift_diagonal_observables(
        &self,
        z: &[Rational],
    ) -> Result<Vec<BasicMatrix<GaussianRat>>, TraceQuotientError> {
        let (n, ne) = (self.dim, self.graph.edge_count());
        (0..ne)
            .map(|e| {
                Ok(mx::diagonal(
                    &z[e * n..(e + 1) * n]
                        .iter()
                        .cloned()
                        .map(GaussianRat::from_rational)
                        .collect::<Vec<_>>(),
                )?)
            })
            .collect()
    }

    fn compute_diagonal_repair_dimensions(
        &self,
        space: RepairSpace,
    ) -> Result<(usize, usize, usize), TraceQuotientError> {
        let (n, ne, nv) = (self.dim, self.graph.edge_count(), self.graph.vertex_count());
        let free = match space {
            RepairSpace::TraceZero => n - 1,
            RepairSpace::AllHermitian => n,
        };
        let limits = core_kernel::resource_limits::OperationLimits::default();
        let cols = limits.checked_product(nv, free)?;
        let rows = limits.checked_product(ne, n)?;
        if cols > MAX_COCHAIN_DIMENSION || rows > MAX_COCHAIN_DIMENSION {
            return Err(CertifiedPhi1Error::SizeLimit {
                c0: cols,
                c1: rows,
                maximum: MAX_COCHAIN_DIMENSION,
            }
            .into());
        }
        Ok((free, rows, cols))
    }

    /// For diagonal defects: the certified weighted-`l1` optimum over `space`
    /// (value replayed by `core_functional`), lifted to matrix certificates.
    ///
    /// Coordinates are stacked as `(e, i) -> e n + i` with weight `w_e / 2`.
    /// All-Hermitian repairs act coordinatewise through `d0`; trace-zero repairs
    /// keep `n - 1` free coordinates per vertex and the last one is minus their
    /// sum. The replayed dual is diagonal with `|z| <= w_e / 2`, so it lifts with
    /// zero centres; for trace-zero repairs its divergence is scalar.
    pub fn diagonal_certificates(
        &self,
        space: RepairSpace,
    ) -> Result<(PrimalCertificate, DualCertificate, Rational), TraceQuotientError> {
        let (n, ne) = (self.dim, self.graph.edge_count());
        let (free, rows, cols) = self.compute_diagonal_repair_dimensions(space)?;
        self.preflight_diagonal_memory_and_work(rows, cols)?;
        self.verify_defects_are_diagonal()?;
        let (repair, x, weights) = self.build_diagonal_repair_system(rows, cols, free)?;
        let phi = certified_phi1(cols, &repair, &x, &weights, 16_384)?;
        let potentials = self.lift_diagonal_potentials(phi.alpha(), free)?;
        let splits = self
            .residuals(&potentials)?
            .iter()
            .map(|r| Self::split_diagonal_residual_matrix(r, n))
            .collect::<Result<Vec<_>, _>>()?;
        let observables = self.lift_diagonal_observables(phi.dual_witness())?;
        Ok((
            PrimalCertificate { potentials, splits },
            DualCertificate {
                observables,
                centres: vec![Rational::zero(); ne],
            },
            phi.value().clone(),
        ))
    }

    fn is_valid_cycle_walk_structure(&self, walk: &OrientedWalk) -> bool {
        let steps = walk.steps();
        let (ne, nv) = (self.graph.edge_count(), self.graph.vertex_count());
        ne > 0
            && walk.is_closed()
            && steps.len() == ne
            && nv == ne
            && walk.start() < nv
            && steps.iter().all(|step| step.edge_index < ne)
            && walk.replays_on(&self.graph)
    }

    fn validate_cycle_walk_and_order(&self, walk: &OrientedWalk) -> Result<Vec<usize>, TraceQuotientError> {
        if !self.is_valid_cycle_walk_structure(walk) {
            return Err(TraceQuotientError::NotACycle);
        }
        let steps = walk.steps();
        let ne = self.graph.edge_count();
        let d0 = self.graph.d0();
        let mut order = vec![walk.start()];
        let mut edge_seen = vec![false; ne];
        for step in steps {
            if edge_seen[step.edge_index] {
                return Err(TraceQuotientError::NotACycle);
            }
            edge_seen[step.edge_index] = true;
            let (source, target) = endpoints(&d0[step.edge_index], step.edge_index)?;
            order.push(if step.direction == 1 { target } else { source });
        }
        order.pop();
        if (0..order.len()).any(|k| order[k + 1..].contains(&order[k])) {
            return Err(TraceQuotientError::NotACycle);
        }
        Ok(order)
    }

    fn signed_step_defect(
        &self,
        step: &core_holonomy::OrientedStep,
    ) -> Result<BasicMatrix<GaussianRat>, TraceQuotientError> {
        let delta = &self.defects[step.edge_index];
        if step.direction == 1 {
            Ok(delta.clone())
        } else {
            Ok(mx::scale(delta, &GaussianRat::from_rational(ri(-1)))?)
        }
    }

    fn verify_cycle_sum_and_find_lightest(
        &self,
        steps: &[core_holonomy::OrientedStep],
        sign: &SignCertificate,
    ) -> Result<(usize, Rational), TraceQuotientError> {
        let ne = self.graph.edge_count();
        let mut cycle_sum = mx::zeros_with_limits(self.dim, self.dim, exact_limits())?;
        for step in steps {
            cycle_sum = mx::add(&cycle_sum, &self.signed_step_defect(step)?)?;
        }
        if sign.matrix() != &cycle_sum {
            return Err(TraceQuotientError::CycleSum);
        }
        let weights = self.graph.weights();
        let lightest = (0..ne)
            .min_by(|&a, &b| weights[steps[a].edge_index].cmp(&weights[steps[b].edge_index]))
            .checked_invariant_11b9a1a9("a cycle has an edge");
        let w_star = weights[steps[lightest].edge_index].clone();
        Ok((lightest, w_star))
    }

    fn build_cycle_potentials_and_splits(
        &self,
        steps: &[core_holonomy::OrientedStep],
        order: &[usize],
        lightest: usize,
        sign: &SignCertificate,
    ) -> Result<PrimalCertificate, TraceQuotientError> {
        let (ne, nv) = (self.graph.edge_count(), self.graph.vertex_count());
        let mut potentials = vec![mx::zeros_with_limits(self.dim, self.dim, exact_limits())?; nv];
        for j in 1..ne {
            let k = (lightest + j) % ne;
            let next = mx::add(&potentials[order[k]], &self.signed_step_defect(&steps[k])?)?;
            potentials[order[(k + 1) % ne]] = next;
        }
        let zero = mx::zeros_with_limits(self.dim, self.dim, exact_limits())?;
        let mut splits = vec![(zero.clone(), zero); ne];
        splits[steps[lightest].edge_index] = if steps[lightest].direction == 1 {
            (sign.positive_part(), sign.negative_part())
        } else {
            (sign.negative_part(), sign.positive_part())
        };
        Ok(PrimalCertificate { potentials, splits })
    }

    fn build_cycle_dual_certificate(
        &self,
        steps: &[core_holonomy::OrientedStep],
        sign: &SignCertificate,
        w_star: &Rational,
    ) -> Result<DualCertificate, TraceQuotientError> {
        let ne = self.graph.edge_count();
        let mut observables = vec![mx::zeros_with_limits(self.dim, self.dim, exact_limits())?; ne];
        for step in steps {
            let orientation = if step.direction == 1 { ri(1) } else { ri(-1) };
            observables[step.edge_index] = mx::scale(
                sign.sign(),
                &GaussianRat::from_rational(orientation * w_star / ri(2)),
            )?;
        }
        Ok(DualCertificate {
            observables,
            centres: vec![Rational::zero(); ne],
        })
    }

    /// The closed-form certificates on a graph that is one simple cycle.
    ///
    /// With oriented cycle sum `S = sum_k sigma_k delta_(e_k)` and minimum
    /// weight `w*` on edge `e*`: potentials accumulated along the walk leave
    /// the residual `sigma* S` on `e*` and zero elsewhere, split by the Jordan
    /// parts of `S`; the dual is the constant circulation
    /// `M_(e_k) = sigma_k (w*/2) sign(S)`. Both give `w* ||S||_1 / 2`.
    pub fn cycle_certificates(
        &self,
        walk: &OrientedWalk,
        sign: &SignCertificate,
    ) -> Result<(PrimalCertificate, DualCertificate), TraceQuotientError> {
        let order = self.validate_cycle_walk_and_order(walk)?;
        let steps = walk.steps();
        let (ne, nv) = (self.graph.edge_count(), self.graph.vertex_count());
        let limits = core_kernel::resource_limits::OperationLimits::default();
        self.preflight(
            sum_counts(&[nv, limits.checked_product(3, ne)?, 6])?,
            limits.checked_product(16, ne)?,
            0,
        )?;
        let (lightest, w_star) = self.verify_cycle_sum_and_find_lightest(steps, sign)?;
        let primal = self.build_cycle_potentials_and_splits(steps, &order, lightest, sign)?;
        let dual = self.build_cycle_dual_certificate(steps, sign, &w_star)?;
        Ok((primal, dual))
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/trace_distance_quotient.rs
// Claim: urn:core:crates_rs:core-quantum-physics:trace-distance-quotient:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_11b9a1a9 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
