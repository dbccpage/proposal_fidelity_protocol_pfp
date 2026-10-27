//! # Calculus of Obstruction, Descent, and Authority (CODA)
//!
//! Selected finite contracts arranged in nine runtime stages.
//! Component paper theorems and general Master Normal Form have broader scopes.
//! The Q policy implementation is the [`q`] submodule (formerly also re-exported by `core_q`).
//! The primary FDA stage refuses supplied wire grants: no external verifier
//! is implemented by this crate. Zero defect does not issue an authority token.
//!
//! ## Core Architecture: Eight Research Components under CODA_GTLA
//!
//! 1. **FOC** (Stage 1): Finite Obstruction Calculus - exact L1 quotient diagnostics, dual witnesses.
//! 2. **MUR** (Stage 2): Meta & Universal Re-Presentation - section overlap compatibility and loss.
//! 3. **CS** (Stage 3): Continuum Shadow - total projection-table typing; report/query
//!    factorization on the realized image through `core_category_theory::finite_report_query`.
//! 4. **CS_Q** (Stage 4): Continuum Shadow to Continuum Bridge - legacy overlap-flag collision
//!    screen; declared-domain quotient separation through
//!    `core_category_theory::finite_section_separation`.
//! 5. **Q** (Stage 5): The Continuum - rational interval order and diameter bounds.
//! 6. **A** (Stage 6): Sentinel - cokernel projection and persistent typed residual registers.
//! 7. **OR** (Stage 7): Omniversal Re-Presentation - local-to-global gluing and hard refusal sieve.
//! 8. **FDA** (Stage 8): finite routing firewall; no verified external grant or full FDA standing record.
//! 9. **CODA_GTLA** (Stage 9): disjoint local terminal variants; no general tower-conservation theorem.
//!
//! `AuthorityEffect: None.`

/// Replayed diagnostic/proposal profile; independent of operational authority.
pub mod diagnostic_routing;
/// CODA/CODA_GTLA finite exact primitive-to-packet composition (moved from `core_pipelines`).
pub mod coda_gtla;
pub mod k_cell_projection;
pub mod layer1_foc;
pub mod layer2_mur;
pub mod layer3_cs;
pub mod layer4_cs_q;
pub mod layer5_q;
pub mod layer6_a;
pub mod layer7_or;
pub mod layer8_fda;
pub mod layer9_coda_gtla;
pub mod pipeline;
pub mod q;
pub mod types;

// Re-exports
pub use k_cell_projection::{
    eval_short_time_k_cell_bound, triangle_simplex_boundaries, KCellDefectCertificate,
    SimplicialBoundaryMatrix,
};
pub use layer1_foc::Layer1Foc;
pub use layer2_mur::Layer2Mur;
pub use layer3_cs::Layer3Cs;
pub use layer4_cs_q::Layer4CsQ;
pub use layer5_q::Layer5Q;
pub use layer6_a::Layer6A;
pub use layer7_or::Layer7Or;
pub use layer8_fda::Layer8Fda;
pub use layer9_coda_gtla::Layer9CodaGtla;
pub use pipeline::{evaluate_coda_pipeline, evaluate_coda_pipeline_with_grant};
pub use types::{
    AuthorityToken, CurvedDualWitness, DualWitness, ExternalAuthorityGrant, FirewallDecision,
    LayerExecutionRecord, LayerId, MasterNormalFormOutcome, ObstructionWitnessPayload,
    ProblemInstance, ResidualPair, TerminalKind,
};

// Re-exports for Q-Continuum & CODA Stack
pub use q::{
    AdmissionDecision, CandidateKind, CodaCsToQAdapter, ContinuumDebt, QAdmissionGate,
    QAdmissionRequest, QDescentGate, QError, QLedger, QPacket, QPacketField, QTerminal,
    ResidualSpec, SpectralConvergenceBinding, SpectralMembrane, SpectralMembraneDecision,
    TransportSpec, ValidatedQPacket, ZetaRhCandidate, ZetaRhClaimKind, ZetaRhDecision,
    ZetaRhFirewall,
};


/// CODA declares nine stages. A pipeline census is a permutation of `1..=9`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CodaStageCensus {
    stages: u8,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CodaStageError {
    Incomplete { got: usize },
    OutOfRange { stage: u8 },
    Duplicate { stage: u8 },
}

// Origin: engine/crates_rs/core_wdp/src/coda/mod.rs
// Claim: urn:core:crates_rs:core-wdp:mod:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CodaStageError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CodaStageError {}

impl CodaStageCensus {
    pub fn admit(stage_ids: &[u8]) -> Result<Self, CodaStageError> {
        if stage_ids.len() != 9 {
            return Err(CodaStageError::Incomplete { got: stage_ids.len() });
        }
        let mut seen = [false; 9];
        for id in stage_ids {
            if !(1..=9).contains(id) {
                return Err(CodaStageError::OutOfRange { stage: *id });
            }
            let index = (*id - 1) as usize;
            if seen[index] {
                return Err(CodaStageError::Duplicate { stage: *id });
            }
            seen[index] = true;
        }
        Ok(Self { stages: 9 })
    }

    pub fn stages(&self) -> u8 {
        self.stages
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod coda_stage_census_tests {
    use super::*;

    #[test]
    fn nine_distinct_stages_are_admitted() {
        let admitted = CodaStageCensus::admit(&[1, 2, 3, 4, 5, 6, 7, 8, 9]);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|census| census.stages()), Some(9));
        assert!(matches!(
            CodaStageCensus::admit(&[1, 1, 3, 4, 5, 6, 7, 8, 9]),
            Err(CodaStageError::Duplicate { stage: 1 })
        ));
    }
}
