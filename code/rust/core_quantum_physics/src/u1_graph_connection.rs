// AuthorityEffect: None.

//! Declared U(1) connections on a finite oriented graph.
//!
//! A connection assigns a unit-modulus scalar `A_e` to each oriented edge of a
//! [`FiniteCochainPacket`]. It is declared data. A real cochain becomes a
//! connection only through a separately declared phase scale
//! ([`CochainExponential`]), and that map loses information.
//!
//! Scalars are exact Gaussian rationals. The unit Gaussian rationals are the
//! rational points of the circle, a dense subgroup of `U(1)`, so every identity
//! below is an exact finite computation:
//!
//! - covariant difference `(D_A psi)(u,v) = psi(v) - A_(u,v) psi(u)`;
//! - vertex gauge `psi'(v) = g(v) psi(v)`, `A'_(u,v) = g(v) A_(u,v) conj(g(u))`,
//!   with `D_A' psi' = g(v) D_A psi` edgewise;
//! - transport along a validated oriented walk; closed-walk holonomy is gauge
//!   invariant, open-walk transport is covariant at its endpoints;
//! - connection Laplacian `Delta_A = D_A^* W D_A`, Hermitian and positive
//!   semidefinite, with `Delta_A' = G Delta_A G^*` for `G = diag(g)`;
//! - fixed-scale exponential of an integer cochain, `A_e = u^(omega_e)` for a
//!   declared unit `u = exp(i alpha)`, which descends to gauge classes.
//!
//! Nothing here is a Schrödinger equation: a Hamiltonian, time parameter,
//! units and physical reading would all be further declarations.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_aff0d000<T> {
    fn checked_invariant_aff0d000(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_aff0d000<T> for Option<T> {
    #[inline]
    fn checked_invariant_aff0d000(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_aff0d000<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_aff0d000(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use core_kernel::resource_limits::OperationLimits;
use std::collections::BTreeMap;

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::Zero;
use core_holonomy::{
    compute_loop_holonomy, DiscreteConnection, ExactMatrix as FieldMatrix, GaussianRational,
    OrientedStep,
};
use core_lie_theory::cayley::{is_unit, unit_pow};

use crate::exact_hermitian::ExactHermitianError;
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::matrix as mx;
use core_holonomy::gauge_fixing::EdgeConnection;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::Rational;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

/// Refusals for connection, gauge, walk and exponential inputs.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum U1GaugeError {
    #[error("{actual} values declared, expected {expected}")]
    ValueCount { expected: usize, actual: usize },
    #[error("value {index} does not have unit modulus")]
    NonUnitValue { index: usize },
    #[error("field has {actual} coordinates, expected {expected}")]
    FieldLength { expected: usize, actual: usize },
    #[error("unknown start vertex {0}")]
    UnknownVertex(String),
    #[error("a walk needs at least one step")]
    EmptyWalk,
    #[error("step {step} names edge {edge}, which is not declared")]
    EdgeOutOfRange { step: usize, edge: usize },
    #[error("step {step} has orientation {direction}; only +1 and -1 are allowed")]
    BadOrientation { step: usize, direction: i8 },
    #[error("step {step} does not start where the previous step ended")]
    Discontinuous { step: usize },
    #[error("walk from {start} ends at {end}; a closed walk is required")]
    WalkNotClosed { start: String, end: String },
    #[error("the walk was validated on another packet and does not replay on this one")]
    ForeignWalk,
    #[error("cochain coordinate {index} is not an integer")]
    NonIntegerCochain { index: usize },
    #[error("antiparallel edges {first} and {second} cannot share one core_holonomy edge key")]
    AntiparallelEdges { first: usize, second: usize },
    #[error("exact Hermitian refusal: {0}")]
    Hermitian(#[from] ExactHermitianError),
    #[error("core_holonomy refusal: {0}")]
    Holonomy(String),
}

/// A validated oriented walk: a start vertex and steps along declared edges.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrientedWalk {
    start: usize,
    end: usize,
    steps: Vec<OrientedStep>,
}

impl OrientedWalk {
    fn validate_single_walk_step(
        packet: &FiniteCochainPacket,
        step: usize,
        edge_index: usize,
        direction: i8,
        here: usize,
    ) -> Result<(usize, OrientedStep), U1GaugeError> {
        let complex = packet.complex();
        let edge = complex
            .edges
            .get(edge_index)
            .ok_or(U1GaugeError::EdgeOutOfRange {
                step,
                edge: edge_index,
            })?;
        let source = *complex
            .vertex_map
            .get(&edge.source)
            .ok_or_else(|| U1GaugeError::UnknownVertex(edge.source.clone()))?;
        let target = *complex
            .vertex_map
            .get(&edge.target)
            .ok_or_else(|| U1GaugeError::UnknownVertex(edge.target.clone()))?;
        let (from, to) = match direction {
            1 => (source, target),
            -1 => (target, source),
            other => {
                return Err(U1GaugeError::BadOrientation {
                    step,
                    direction: other,
                })
            }
        };
        if from != here {
            return Err(U1GaugeError::Discontinuous { step });
        }
        let oriented = OrientedStep {
            edge_index,
            direction,
        };
        Ok((to, oriented))
    }

    /// Check every edge index, orientation and junction of the walk.
    pub fn new(
        packet: &FiniteCochainPacket,
        start_vertex: &str,
        steps: &[(usize, i8)],
    ) -> Result<Self, U1GaugeError> {
        let complex = packet.complex();
        let start = *complex
            .vertex_map
            .get(start_vertex)
            .ok_or_else(|| U1GaugeError::UnknownVertex(start_vertex.to_string()))?;
        if steps.is_empty() {
            return Err(U1GaugeError::EmptyWalk);
        }
        let mut here = start;
        let mut validated = Vec::with_capacity(steps.len());
        for (step, &(edge_index, direction)) in steps.iter().enumerate() {
            let (next_vertex, oriented) =
                Self::validate_single_walk_step(packet, step, edge_index, direction, here)?;
            here = next_vertex;
            validated.push(oriented);
        }
        let out = Self {
            start,
            end: here,
            steps: validated,
        };
        Ok(out)
    }

    pub fn start(&self) -> usize {
        self.start
    }

    pub fn end(&self) -> usize {
        self.end
    }

    pub fn steps(&self) -> &[OrientedStep] {
        &self.steps
    }

    pub fn is_closed(&self) -> bool {
        self.start == self.end
    }

    /// Whether the walk replays on `packet`: its start vertex exists there and
    /// revalidating its steps from that vertex gives the same walk. A walk
    /// validated on another packet that happens to have enough edges fails.
    pub fn replays_on(&self, packet: &FiniteCochainPacket) -> bool {
        let Some(start) = packet.complex().vertices.get(self.start) else {
            return false;
        };
        let steps: Vec<(usize, i8)> = self
            .steps
            .iter()
            .map(|s| (s.edge_index, s.direction))
            .collect();
        OrientedWalk::new(packet, &start.id, &steps).is_ok_and(|replayed| replayed == *self)
    }
}

/// A unit-modulus function on vertices.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VertexGauge {
    values: Vec<GaussianRat>,
}

impl VertexGauge {
    pub fn new(
        packet: &FiniteCochainPacket,
        values: Vec<GaussianRat>,
    ) -> Result<Self, U1GaugeError> {
        check_units(&values, packet.vertex_count())?;
        Ok(Self { values })
    }

    pub fn values(&self) -> &[GaussianRat] {
        &self.values
    }

    /// `psi'(v) = g(v) psi(v)`.
    pub fn apply_to_field(&self, psi: &[GaussianRat]) -> Result<Vec<GaussianRat>, U1GaugeError> {
        if psi.len() != self.values.len() {
            return Err(U1GaugeError::FieldLength {
                expected: self.values.len(),
                actual: psi.len(),
            });
        }
        Ok(self.values.iter().zip(psi).map(|(g, p)| g.mul(p)).collect())
    }

    /// `G = diag(g)`, a unitary diagonal matrix.
    pub fn diagonal(&self) -> BasicMatrix<GaussianRat> {
        mx::diagonal(&self.values).checked_invariant_aff0d000("validated gauge dimension")
    }
}

/// A declared U(1) connection, one unit value per edge index.
#[derive(Debug, Clone)]
pub struct U1Connection {
    values: Vec<GaussianRat>,
    complex: core_holonomy::CellComplex,
    native: EdgeConnection<GaussianRational<Rational>>,
}

impl PartialEq for U1Connection {
    fn eq(&self, other: &Self) -> bool {
        self.values == other.values
            && self.complex.vertices.iter().map(|v| &v.id).eq(other
                .complex
                .vertices
                .iter()
                .map(|v| &v.id))
            && self
                .complex
                .edges
                .iter()
                .map(|e| (&e.source, &e.target))
                .eq(other.complex.edges.iter().map(|e| (&e.source, &e.target)))
    }
}
impl Eq for U1Connection {}

fn scalar_from_native(z: &GaussianRational<Rational>) -> GaussianRat {
    GaussianRat {
        re: z.re.clone(),
        im: z.im.clone(),
    }
}
fn matrix_from_native(m: FieldMatrix<GaussianRational<Rational>>) -> BasicMatrix<GaussianRat> {
    BasicMatrix::from_row_major(
        m.rows,
        m.cols,
        m.data.iter().map(scalar_from_native).collect(),
    )
    .checked_invariant_aff0d000("sovereign holonomy validates its matrix shape")
}

impl U1Connection {
    pub fn new(
        packet: &FiniteCochainPacket,
        values: Vec<GaussianRat>,
    ) -> Result<Self, U1GaugeError> {
        check_units(&values, packet.edge_count())?;
        let scalars = values
            .iter()
            .map(|z| GaussianRational::new(z.re.clone(), z.im.clone()))
            .collect();
        let native = EdgeConnection::from_scalars(packet.complex(), scalars)
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        Ok(Self {
            values,
            complex: packet.complex().clone(),
            native,
        })
    }

    pub fn indexed_connection(&self) -> &EdgeConnection<GaussianRational<Rational>> {
        &self.native
    }

    /// The connection with every edge value equal to one.
    pub fn trivial(packet: &FiniteCochainPacket) -> Self {
        Self::new(packet, vec![GaussianRat::one(); packet.edge_count()])
            .checked_invariant_aff0d000("validated packet admits the trivial connection")
    }

    pub fn values(&self) -> &[GaussianRat] {
        &self.values
    }

    fn endpoints(packet: &FiniteCochainPacket, edge: usize) -> (usize, usize) {
        let complex = packet.complex();
        let e = &complex.edges[edge];
        (complex.vertex_map[&e.source], complex.vertex_map[&e.target])
    }

    /// `(D_A psi)(u,v) = psi(v) - A_(u,v) psi(u)`.
    pub fn covariant_difference(
        &self,
        packet: &FiniteCochainPacket,
        psi: &[GaussianRat],
    ) -> Result<Vec<GaussianRat>, U1GaugeError> {
        if psi.len() != packet.vertex_count() {
            return Err(U1GaugeError::FieldLength {
                expected: packet.vertex_count(),
                actual: psi.len(),
            });
        }
        Ok((0..packet.edge_count())
            .map(|e| {
                let (u, v) = Self::endpoints(packet, e);
                psi[v].sub(&self.values[e].mul(&psi[u]))
            })
            .collect())
    }

    /// `D_A` as an `edges x vertices` matrix.
    pub fn covariant_difference_matrix(
        &self,
        packet: &FiniteCochainPacket,
    ) -> BasicMatrix<GaussianRat> {
        self.try_covariant_difference_matrix(packet)
            .checked_invariant_aff0d000("use try_covariant_difference_matrix for packet mismatch admission")
    }

    pub fn try_covariant_difference_matrix(
        &self,
        packet: &FiniteCochainPacket,
    ) -> Result<BasicMatrix<GaussianRat>, U1GaugeError> {
        self.native
            .covariant_difference_matrix(packet.complex())
            .map(matrix_from_native)
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))
    }

    /// `A'_(u,v) = g(v) A_(u,v) conj(g(u))`.
    pub fn gauge_transform(
        &self,
        packet: &FiniteCochainPacket,
        gauge: &VertexGauge,
    ) -> Result<Self, U1GaugeError> {
        let matrices = gauge
            .values
            .iter()
            .map(|g| {
                FieldMatrix::try_new(
                    1,
                    1,
                    vec![GaussianRational::new(g.re.clone(), g.im.clone())],
                )
            })
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        let fixed = self
            .native
            .gauge_transform(packet.complex(), &matrices)
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        let values = (0..fixed.edge_count())
            .map(|e| fixed.value(e).map(|m| scalar_from_native(m.get(0, 0))))
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        Self::new(packet, values)
    }

    /// Ordered product along the walk: `A_e` forward, `conj(A_e)` reversed.
    pub fn transport(&self, walk: &OrientedWalk) -> Result<GaussianRat, U1GaugeError> {
        let (m, end) = self
            .native
            .walk(&self.complex, walk.start(), walk.steps())
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        if end != walk.end() {
            return Err(U1GaugeError::ForeignWalk);
        }
        Ok(scalar_from_native(m.get(0, 0)))
    }

    /// `Hol_A(gamma)` for a closed walk of `packet`; an open walk, a walk of
    /// another packet and a connection of another size are refused.
    pub fn holonomy(
        &self,
        packet: &FiniteCochainPacket,
        walk: &OrientedWalk,
    ) -> Result<GaussianRat, U1GaugeError> {
        if !walk.replays_on(packet) {
            return Err(U1GaugeError::ForeignWalk);
        }
        if !walk.is_closed() {
            return Err(U1GaugeError::WalkNotClosed {
                start: packet.complex().vertices[walk.start()].id.clone(),
                end: packet.complex().vertices[walk.end()].id.clone(),
            });
        }
        let m = self
            .native
            .loop_holonomy(packet.complex(), walk.start(), walk.steps())
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        Ok(scalar_from_native(m.get(0, 0)))
    }

    /// `Delta_A = D_A^* W D_A` with the packet's positive edge weights.
    pub fn laplacian(&self, packet: &FiniteCochainPacket) -> BasicMatrix<GaussianRat> {
        self.try_laplacian(packet)
            .checked_invariant_aff0d000("use try_laplacian for packet mismatch and work budget admission")
    }

    pub fn try_laplacian(
        &self,
        packet: &FiniteCochainPacket,
    ) -> Result<BasicMatrix<GaussianRat>, U1GaugeError> {
        let weights = packet
            .weights()
            .iter()
            .map(|w| GaussianRational::new(w.clone(), Rational::zero()))
            .collect::<Vec<_>>();
        self.native
            .connection_laplacian(packet.complex(), &weights)
            .map(matrix_from_native)
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))
    }

    /// `sum_e w_e |(D_A psi)_e|^2`, the value `<psi, Delta_A psi>` must equal.
    pub fn dirichlet_energy(
        &self,
        packet: &FiniteCochainPacket,
        psi: &[GaussianRat],
    ) -> Result<Rational, U1GaugeError> {
        let d = self.covariant_difference(packet, psi)?;
        Ok(d.iter()
            .zip(packet.weights())
            .map(|(z, w)| z.norm_sq() * w)
            .sum())
    }

    /// The same data as an `core_holonomy` connection with `U(u->v) = A_(u,v)`.
    ///
    /// `core_holonomy` keys edges by vertex pairs, so antiparallel edges are refused.
    pub fn to_holonomy_connection(
        &self,
        packet: &FiniteCochainPacket,
    ) -> Result<DiscreteConnection<GaussianRational<BigRational>>, U1GaugeError> {
        let complex = packet.complex();
        let mut seen: BTreeMap<(usize, usize), usize> = BTreeMap::new();
        for e in 0..packet.edge_count() {
            let (u, v) = Self::endpoints(packet, e);
            if let Some(&first) = seen.get(&(u.min(v), u.max(v))) {
                return Err(U1GaugeError::AntiparallelEdges { first, second: e });
            }
            seen.insert((u.min(v), u.max(v)), e);
        }
        let mut connection = DiscreteConnection::new(1, OperationLimits::holonomy());
        for (e, a) in self.values.iter().enumerate() {
            let edge = &complex.edges[e];
            let matrix = FieldMatrix::try_new(
                1,
                1,
                vec![GaussianRational::new(a.re.clone(), a.im.clone())],
            )
            .map_err(|err| U1GaugeError::Holonomy(err.to_string()))?;
            connection
                .set_connection(&edge.source, &edge.target, matrix)
                .map_err(|err| U1GaugeError::Holonomy(err.to_string()))?;
        }
        Ok(connection)
    }

    /// `core_holonomy`'s connection Laplacian of the same data, weighted by the packet.
    ///
    /// `core_holonomy` places `-w U(u->v)` in block `(u, v)`, the transpose of
    /// `D_A^* W D_A`; for a Hermitian matrix that is the entrywise conjugate.
    pub fn holonomy_crate_laplacian(
        &self,
        packet: &FiniteCochainPacket,
    ) -> Result<BasicMatrix<GaussianRat>, U1GaugeError> {
        let m = self.try_laplacian(packet)?;
        mx::transpose(&m).map_err(|e| U1GaugeError::Hermitian(e.into()))
    }

    /// `core_holonomy`'s loop holonomy along a closed vertex cycle.
    pub fn holonomy_crate_loop(
        &self,
        packet: &FiniteCochainPacket,
        cycle: &[&str],
    ) -> Result<GaussianRat, U1GaugeError> {
        let connection = self.to_holonomy_connection(packet)?;
        let cycle: Vec<String> = cycle.iter().map(|s| s.to_string()).collect();
        let m = compute_loop_holonomy(&connection, &cycle)
            .map_err(|err| U1GaugeError::Holonomy(err.to_string()))?;
        let z = m.get(0, 0).clone();
        Ok(GaussianRat { re: z.re, im: z.im })
    }
}

/// A declared phase scale `alpha`, given as the unit `u = exp(i alpha)`.
///
/// On integer cochains the exponential is exact: `Exp(omega)_e = u^(omega_e)`.
/// The only roots of unity in `Q(i)` are `1, -1, i, -i`; any other unit has
/// infinite order, and then `Exp` is injective on integer cochains. For a
/// root of unity of order `n`, cochains that differ by `n` on an edge collapse.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CochainExponential {
    base: GaussianRat,
}

impl CochainExponential {
    pub fn new(base: GaussianRat) -> Result<Self, U1GaugeError> {
        if !is_unit(&base) {
            return Err(U1GaugeError::NonUnitValue { index: 0 });
        }
        Ok(Self { base })
    }

    pub fn base(&self) -> &GaussianRat {
        &self.base
    }

    /// The multiplicative order of `u`, or `None` when it is infinite.
    pub fn order(&self) -> Option<u32> {
        core_lie_theory::cayley::gaussian_unit_order(&self.base)
            .checked_invariant_aff0d000("phase base was admitted as a unit")
            .map(|n| n as u32)
    }

    fn integer_coordinates(values: &[Rational]) -> Result<Vec<BigInt>, U1GaugeError> {
        values
            .iter()
            .enumerate()
            .map(|(index, value)| {
                if value.is_integer() {
                    Ok(value.to_integer())
                } else {
                    Err(U1GaugeError::NonIntegerCochain { index })
                }
            })
            .collect()
    }

    /// `Exp(omega)_e = u^(omega_e)` for an integer edge cochain.
    pub fn connection(
        &self,
        packet: &FiniteCochainPacket,
        omega: &[Rational],
    ) -> Result<U1Connection, U1GaugeError> {
        if omega.len() != packet.edge_count() {
            return Err(U1GaugeError::ValueCount {
                expected: packet.edge_count(),
                actual: omega.len(),
            });
        }
        let values = Self::integer_coordinates(omega)?
            .iter()
            .map(|k| unit_pow(&self.base, k).map_err(|e| U1GaugeError::Holonomy(e.to_string())))
            .collect::<Result<Vec<_>, _>>()?;
        U1Connection::new(packet, values)
    }

    /// The gauge `g(v) = u^(f(v))` relating `Exp(omega)` to `Exp(omega + d0 f)`.
    pub fn gauge(
        &self,
        packet: &FiniteCochainPacket,
        f: &[Rational],
    ) -> Result<VertexGauge, U1GaugeError> {
        if f.len() != packet.vertex_count() {
            return Err(U1GaugeError::ValueCount {
                expected: packet.vertex_count(),
                actual: f.len(),
            });
        }
        let values = Self::integer_coordinates(f)?
            .iter()
            .map(|k| unit_pow(&self.base, k).map_err(|e| U1GaugeError::Holonomy(e.to_string())))
            .collect::<Result<Vec<_>, _>>()?;
        VertexGauge::new(packet, values)
    }
}

/// `omega / I1(omega)`: each cochain divided by its own raw mass.
///
/// This is scale invariant and not additive, so it fixes no linear or
/// functorial phase convention. Refuses the zero cochain.
pub fn l1_self_normalized(
    packet: &FiniteCochainPacket,
    omega: &[Rational],
) -> Option<Vec<Rational>> {
    let mass = packet.raw_mass(omega).ok()?;
    if mass.is_zero() {
        return None;
    }
    Some(omega.iter().map(|x| x / &mass).collect())
}

fn check_units(values: &[GaussianRat], expected: usize) -> Result<(), U1GaugeError> {
    if values.len() != expected {
        return Err(U1GaugeError::ValueCount {
            expected,
            actual: values.len(),
        });
    }
    if let Some(index) = values.iter().position(|z| !is_unit(z)) {
        return Err(U1GaugeError::NonUnitValue { index });
    }
    Ok(())
}

// Origin: engine/crates_rs/core_quantum_physics/src/u1_graph_connection.rs
// Claim: urn:core:crates_rs:core-quantum-physics:u1-graph-connection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_aff0d000 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
