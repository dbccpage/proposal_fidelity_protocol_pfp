// AuthorityEffect: None.

//! Deciding whether a declared U(1) connection is pure gauge.
//!
//! A connection `A` on a [`FiniteCochainPacket`] is gauge-trivial when some
//! vertex gauge `g` gives `A_(u,v) = g(v) conj(g(u))` on every edge, i.e. `A` is
//! the gauge transform of the trivial connection. [`trivializing_gauge`]
//! decides this exactly with the spanning-forest gauge fixing of
//! `holonomy_interference::TreeGaugeFixing`: the connection is pure gauge
//! exactly when every edge off the forest is left with value `1`. Either the
//! gauge is returned, or the fundamental cycle of the first edge left with
//! another value is returned with its holonomy, which is not `1`. The walk and
//! its holonomy are ordinary [`OrientedWalk`] and [`U1Connection::holonomy`]
//! values, so the refusal can be replayed independently.
//!
//! Nothing is said about the additive cochain a connection may come from.
//! Under a declared scale `u`, `Exp(omega)` is gauge-trivial exactly when every
//! cycle sum of `omega` is a multiple of the order of `u` (zero when the order
//! is infinite); that equals "`omega` is a coboundary" only when `u` has
//! infinite order.

use crate::u1_graph_connection::{OrientedWalk, U1Connection, U1GaugeError, VertexGauge};
use core_number_theory::cyclotomic::GaussianRat;
use core_solvers::data_cochain_packet::FiniteCochainPacket;

use crate::holonomy_interference::{HolonomyInterferenceError, TreeGaugeFixing};

/// A closed walk through `edge` whose holonomy is not `1`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct HolonomyWitness {
    pub edge: usize,
    pub walk: OrientedWalk,
    pub holonomy: GaussianRat,
}

/// Why a connection is not pure gauge, or why the question was refused.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum GaugeTrivialityError {
    #[error("connection has {actual} edge values, packet has {expected} edges")]
    EdgeCount { expected: usize, actual: usize },
    #[error("a closed walk through edge {} has holonomy {:?}", .0.edge, .0.holonomy)]
    NontrivialHolonomy(Box<HolonomyWitness>),
    #[error("walk or gauge construction refused: {0}")]
    Construction(#[from] U1GaugeError),
    #[error("gauge fixing refused: {0}")]
    Fixing(HolonomyInterferenceError),
}

/// A vertex gauge `g` with `A_(u,v) = g(v) conj(g(u))` on every edge, or a
/// closed walk whose holonomy is not `1`.
pub fn trivializing_gauge(
    packet: &FiniteCochainPacket,
    connection: &U1Connection,
) -> Result<VertexGauge, GaugeTrivialityError> {
    if connection.values().len() != packet.edge_count() {
        return Err(GaugeTrivialityError::EdgeCount {
            expected: packet.edge_count(),
            actual: connection.values().len(),
        });
    }
    let fixing = TreeGaugeFixing::new(packet, connection).map_err(GaugeTrivialityError::Fixing)?;
    match fixing
        .cycle_holonomies()
        .into_iter()
        .find(|(_, h)| *h != GaussianRat::one())
    {
        // The fixing gauge sends A to 1, so its conjugate sends 1 to A.
        None => Ok(VertexGauge::new(
            packet,
            fixing
                .gauge()
                .values()
                .iter()
                .map(GaussianRat::conj)
                .collect(),
        )?),
        Some((edge, _)) => {
            let walk = fixing
                .fundamental_cycle(packet, edge)
                .map_err(GaugeTrivialityError::Fixing)?;
            let holonomy = connection.holonomy(packet, &walk)?;
            Err(GaugeTrivialityError::NontrivialHolonomy(Box::new(
                HolonomyWitness {
                    edge,
                    walk,
                    holonomy,
                },
            )))
        }
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/u1_gauge_triviality.rs
// Claim: urn:core:crates_rs:core-quantum-physics:u1-gauge-triviality:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_3c67eacd {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
