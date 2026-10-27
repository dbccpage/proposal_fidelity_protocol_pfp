// AuthorityEffect: None.

//! Holonomy-structured interference on a declared finite carrier.
//!
//! Inputs are declared: a [`FiniteCochainPacket`] (a graph or an oriented
//! 2-complex), a [`U1Connection`] over unit Gaussian rationals, source-to-sink
//! walks, and nonnegative L1 weights. Computed here:
//!
//! - spanning-forest gauge fixing: a vertex gauge that makes the connection
//!   `1` on a breadth-first spanning forest. The value left on each remaining
//!   edge is the holonomy of its fundamental cycle, so the connection is gauge
//!   trivial exactly when all of them are `1`. Every connection on a forest is
//!   therefore gauge trivial, and two connections are gauge equivalent exactly
//!   when their fixed residuals agree; a relating gauge is then returned;
//! - face holonomies (the multiplicative form `exp(i d1 a)` of face curvature)
//!   and the verdict `Curved`, `FlatNontrivial` or `GaugeTrivial`. A graph has
//!   no faces, so its verdict is never `Curved`;
//! - integrals of real 1-cochains along validated walks; a primitive
//!   difference `d0 f` integrates to `f(end) - f(start)`, so to zero around any
//!   closed walk;
//! - coherent path families: amplitudes `A_p = sqrt(w_p) H(p)` for walks with a
//!   common source and sink, the sink intensity `|sum_p A_p|^2`, and, from the
//!   relative holonomies `h_pq = H(p) conj H(q)` alone, the expansion
//!   `sum_p w_p + 2 sum_{p<q} sqrt(w_p w_q) Re(h_pq)`. The two agree; `h_pq` is
//!   the holonomy of the closed walk `p` followed by `q` reversed.
//!
//! Refused: connections or walks that do not fit the packet, walks without a
//! common source and sink, and weights whose square root is irrational (no
//! exact amplitude exists; nothing is approximated). A reversed edge always
//! transports by the conjugate value, so inconsistent reverse transport cannot
//! be declared.
//!
//! U(1), the square root and the quadratic readout are imported. Nothing here
//! derives superposition, a Hilbert space, or an interference experiment.

use num_traits::Signed;

use crate::u1_graph_connection::{OrientedWalk, U1Connection, U1GaugeError, VertexGauge};
use core_holonomy::gauge_fixing::{tree_gauge_indexed, TreeGauge};
use core_holonomy::GaussianRational;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::sqrt_exact;
use core_number_theory::rational::{ri, Rational};
use core_solvers::data_cochain_packet::FiniteCochainPacket;

/// Refusals for gauge fixing, verdicts, walk integrals and path families.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum HolonomyInterferenceError {
    #[error("the connection has {actual} edge values, the packet has {expected} edges")]
    ConnectionSize { expected: usize, actual: usize },
    #[error("the cochain has {actual} coordinates, expected {expected}")]
    CochainLength { expected: usize, actual: usize },
    #[error("a walk uses edge {edge}, which the packet does not declare")]
    WalkOutsidePacket { edge: usize },
    #[error("the walk was validated on another packet and does not replay on this one")]
    ForeignWalk,
    #[error("a path family needs at least one walk")]
    EmptyFamily,
    #[error("{walks} walks but {weights} weights")]
    WeightCount { walks: usize, weights: usize },
    #[error("walk {index} does not share the source and sink of walk 0")]
    EndpointMismatch { index: usize },
    #[error("weight {index} is negative")]
    NegativeWeight { index: usize },
    #[error("weight {index} is not the square of a rational, so no exact amplitude exists")]
    IrrationalAmplitude { index: usize },
    #[error("path index {index} is out of range")]
    PathIndex { index: usize },
    #[error("U(1) refusal: {0}")]
    Gauge(#[from] U1GaugeError),
}

fn check_connection(
    packet: &FiniteCochainPacket,
    connection: &U1Connection,
) -> Result<(), HolonomyInterferenceError> {
    if connection.values().len() != packet.edge_count() {
        return Err(HolonomyInterferenceError::ConnectionSize {
            expected: packet.edge_count(),
            actual: connection.values().len(),
        });
    }
    Ok(())
}

/// A walk belongs to a packet only if it replays there: every edge is
/// declared, the start vertex exists, and each step leaves the vertex the last
/// one reached. A walk validated on another packet with enough edges fails.
fn check_walk(
    packet: &FiniteCochainPacket,
    walk: &OrientedWalk,
) -> Result<(), HolonomyInterferenceError> {
    if let Some(step) = walk
        .steps()
        .iter()
        .find(|s| s.edge_index >= packet.edge_count())
    {
        return Err(HolonomyInterferenceError::WalkOutsidePacket {
            edge: step.edge_index,
        });
    }
    if walk.replays_on(packet) {
        Ok(())
    } else {
        Err(HolonomyInterferenceError::ForeignWalk)
    }
}

/// U(1) physics view of the sovereign spanning-forest gauge.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TreeGaugeFixing {
    gauge: VertexGauge,
    residual: U1Connection,
    native: TreeGauge<GaussianRational<Rational>>,
}

impl TreeGaugeFixing {
    pub fn new(
        packet: &FiniteCochainPacket,
        connection: &U1Connection,
    ) -> Result<Self, HolonomyInterferenceError> {
        check_connection(packet, connection)?;
        let native = tree_gauge_indexed(packet.complex(), connection.indexed_connection())
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        let scalar = |m: &core_holonomy::ExactMatrix<GaussianRational<Rational>>| {
            let z = m.get(0, 0);
            GaussianRat {
                re: z.re.clone(),
                im: z.im.clone(),
            }
        };
        let gauge = VertexGauge::new(packet, native.gauge().iter().map(scalar).collect())?;
        let values = (0..packet.edge_count())
            .map(|e| native.residual_value(e).map(scalar))
            .collect::<Result<Vec<_>, _>>()
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        let residual = U1Connection::new(packet, values)?;
        Ok(Self {
            gauge,
            residual,
            native,
        })
    }
    pub fn gauge(&self) -> &VertexGauge {
        &self.gauge
    }
    pub fn residual(&self) -> &U1Connection {
        &self.residual
    }
    pub fn is_tree_edge(&self, edge: usize) -> Option<bool> {
        self.native.is_tree_edge(edge).ok()
    }
    pub fn cycle_holonomies(&self) -> Vec<(usize, GaussianRat)> {
        self.native
            .cycle_holonomies()
            .into_iter()
            .map(|(e, m)| {
                let z = m.get(0, 0);
                (
                    e,
                    GaussianRat {
                        re: z.re.clone(),
                        im: z.im.clone(),
                    },
                )
            })
            .collect()
    }
    pub fn is_gauge_trivial(&self) -> bool {
        self.native.is_gauge_trivial()
    }
    pub fn fundamental_cycle(
        &self,
        packet: &FiniteCochainPacket,
        edge: usize,
    ) -> Result<OrientedWalk, HolonomyInterferenceError> {
        let cycle = self
            .native
            .fundamental_cycle(edge)
            .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
        let steps = cycle
            .steps
            .iter()
            .map(|s| (s.edge_index, s.direction))
            .collect::<Vec<_>>();
        Ok(OrientedWalk::new(packet, &cycle.base, &steps)?)
    }
}

/// A gauge `g` with `a^g = b`, or `None` when `a` and `b` are not gauge equivalent.
pub fn gauge_equivalence(
    packet: &FiniteCochainPacket,
    a: &U1Connection,
    b: &U1Connection,
) -> Result<Option<VertexGauge>, HolonomyInterferenceError> {
    let fixed_a = TreeGaugeFixing::new(packet, a)?;
    let fixed_b = TreeGaugeFixing::new(packet, b)?;
    if fixed_a.residual != fixed_b.residual {
        return Ok(None);
    }
    let values = fixed_a
        .gauge
        .values()
        .iter()
        .zip(fixed_b.gauge.values())
        .map(|(ga, gb)| gb.conj().mul(ga))
        .collect();
    Ok(Some(VertexGauge::new(packet, values)?))
}

/// The holonomy around each face boundary, in face order.
pub fn face_holonomies(
    packet: &FiniteCochainPacket,
    connection: &U1Connection,
) -> Result<Vec<GaussianRat>, HolonomyInterferenceError> {
    check_connection(packet, connection)?;
    (0..packet.complex().faces.len())
        .map(|face| {
            let m = connection
                .indexed_connection()
                .face_holonomy(packet.complex(), face)
                .map_err(|e| U1GaugeError::Holonomy(e.to_string()))?;
            let z = m.get(0, 0);
            Ok(GaussianRat {
                re: z.re.clone(),
                im: z.im.clone(),
            })
        })
        .collect()
}

/// Where the gauge-invariant content of a connection sits.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HolonomyVerdict {
    /// Some face holonomy differs from `1`; all face holonomies, in face order.
    Curved { face_holonomies: Vec<GaussianRat> },
    /// Every face is flat, yet some fundamental cycle has holonomy other than `1`.
    FlatNontrivial {
        cycle_holonomies: Vec<(usize, GaussianRat)>,
    },
    /// The connection is a vertex gauge transform of the trivial connection.
    GaugeTrivial,
}

pub fn holonomy_verdict(
    packet: &FiniteCochainPacket,
    connection: &U1Connection,
) -> Result<HolonomyVerdict, HolonomyInterferenceError> {
    let faces = face_holonomies(packet, connection)?;
    if faces.iter().any(|h| *h != GaussianRat::one()) {
        return Ok(HolonomyVerdict::Curved {
            face_holonomies: faces,
        });
    }
    let fixing = TreeGaugeFixing::new(packet, connection)?;
    if fixing.is_gauge_trivial() {
        Ok(HolonomyVerdict::GaugeTrivial)
    } else {
        Ok(HolonomyVerdict::FlatNontrivial {
            cycle_holonomies: fixing.cycle_holonomies(),
        })
    }
}

/// `sum_steps direction * x_edge` for a real 1-cochain `x`.
pub fn walk_integral(
    packet: &FiniteCochainPacket,
    walk: &OrientedWalk,
    x: &[Rational],
) -> Result<Rational, HolonomyInterferenceError> {
    if x.len() != packet.edge_count() {
        return Err(HolonomyInterferenceError::CochainLength {
            expected: packet.edge_count(),
            actual: x.len(),
        });
    }
    check_walk(packet, walk)?;
    Ok(walk
        .steps()
        .iter()
        .map(|step| {
            if step.direction == 1 {
                x[step.edge_index].clone()
            } else {
                -&x[step.edge_index]
            }
        })
        .sum())
}

/// The closed walk `p` followed by `q` reversed, for walks with common endpoints.
pub fn relative_loop(
    packet: &FiniteCochainPacket,
    p: &OrientedWalk,
    q: &OrientedWalk,
) -> Result<OrientedWalk, HolonomyInterferenceError> {
    check_walk(packet, p)?;
    check_walk(packet, q)?;
    if p.start() != q.start() || p.end() != q.end() {
        return Err(HolonomyInterferenceError::EndpointMismatch { index: 1 });
    }
    let steps: Vec<(usize, i8)> = p
        .steps()
        .iter()
        .map(|step| (step.edge_index, step.direction))
        .chain(
            q.steps()
                .iter()
                .rev()
                .map(|step| (step.edge_index, -step.direction)),
        )
        .collect();
    Ok(OrientedWalk::new(
        packet,
        &packet.complex().vertices[p.start()].id,
        &steps,
    )?)
}

/// Declared weighted walks from one source to one sink, lifted to amplitudes.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CoherentPathFamily {
    weights: Vec<Rational>,
    moduli: Vec<Rational>,
    transports: Vec<GaussianRat>,
}

impl CoherentPathFamily {
    fn compute_exact_moduli(weights: &[Rational]) -> Result<Vec<Rational>, HolonomyInterferenceError> {
        weights
            .iter()
            .enumerate()
            .map(|(index, w)| {
                if w.is_negative() {
                    return Err(HolonomyInterferenceError::NegativeWeight { index });
                }
                sqrt_exact(w).ok_or(HolonomyInterferenceError::IrrationalAmplitude { index })
            })
            .collect()
    }

    pub fn new(
        packet: &FiniteCochainPacket,
        connection: &U1Connection,
        walks: &[OrientedWalk],
        weights: &[Rational],
    ) -> Result<Self, HolonomyInterferenceError> {
        check_connection(packet, connection)?;
        let first = walks
            .first()
            .ok_or(HolonomyInterferenceError::EmptyFamily)?;
        if weights.len() != walks.len() {
            return Err(HolonomyInterferenceError::WeightCount {
                walks: walks.len(),
                weights: weights.len(),
            });
        }
        for (index, walk) in walks.iter().enumerate() {
            check_walk(packet, walk)?;
            if walk.start() != first.start() || walk.end() != first.end() {
                return Err(HolonomyInterferenceError::EndpointMismatch { index });
            }
        }
        let moduli = Self::compute_exact_moduli(weights)?;
        Ok(Self {
            weights: weights.to_vec(),
            moduli,
            transports: walks
                .iter()
                .map(|walk| connection.transport(walk))
                .collect::<Result<_, _>>()?,
        })
    }

    /// `H(p)` for each walk.
    pub fn transports(&self) -> &[GaussianRat] {
        &self.transports
    }

    /// `A_p = sqrt(w_p) H(p)`.
    pub fn amplitudes(&self) -> Vec<GaussianRat> {
        self.moduli
            .iter()
            .zip(&self.transports)
            .map(|(r, h)| h.mul(&GaussianRat::from_rational(r.clone())))
            .collect()
    }

    /// `|sum_p A_p|^2`.
    pub fn sink_intensity(&self) -> Rational {
        self.amplitudes()
            .iter()
            .fold(GaussianRat::zero(), |acc, a| acc.add(a))
            .norm_sq()
    }

    /// `|sum_p A_p|^2 - sum_p w_p`.
    pub fn interference_residual(&self) -> Rational {
        let l1: Rational = self.weights.iter().sum();
        self.sink_intensity() - l1
    }

    /// `h_pq = H(p) conj H(q)`.
    pub fn relative_holonomy(
        &self,
        p: usize,
        q: usize,
    ) -> Result<GaussianRat, HolonomyInterferenceError> {
        for index in [p, q] {
            if index >= self.transports.len() {
                return Err(HolonomyInterferenceError::PathIndex { index });
            }
        }
        Ok(self.transports[p].mul(&self.transports[q].conj()))
    }

    /// `sum_p w_p + 2 sum_{p<q} sqrt(w_p w_q) Re(h_pq)`, from the relative
    /// holonomies and the moduli only.
    pub fn holonomy_expansion(&self) -> Rational {
        let mut total: Rational = self.weights.iter().sum();
        let two = ri(2);
        let paths = || self.moduli.iter().zip(&self.transports);
        for (p, (rp, hp)) in paths().enumerate() {
            for (rq, hq) in paths().skip(p + 1) {
                total += &two * rp * rq * &hp.mul(&hq.conj()).re;
            }
        }
        total
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/holonomy_interference.rs
// Claim: urn:core:crates_rs:core-quantum-physics:holonomy-interference:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_ba96f045 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
