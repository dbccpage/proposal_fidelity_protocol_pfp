//! # core_epk — EPK host overlay
//!
//! **Path-kernel math (LGGR I)** lives in [`lggr_engine`].
//! That is the engine face: finite exact path mass, Δ_E, metrics, RKE.
//!
//! **This crate** keeps host overlays only:
//! - [`ledger`] — Auth=0 residual ledger + optional FOC family bridge
//! - [`adequacy`] — detector-adequacy protocol (green ≠ certificate)
//!
//! Re-exports engine surface so existing `use core_epk::…` paths keep working.
//! New theory / morphism work should use [`lggr_engine`] directly.
//!
//! OE layering: pipelines orchestrate engines; engines orchestrate 1-/2-morphisms
//! that do not increase Φ. EPK is an evaluator (Auth=0), not a terminalizer.
//!
//! **AuthorityEffect: None.**

/// Exact rational matrix specialization, with native graph/holonomy owners.
pub mod matrix_path_kernel;
pub mod lggr_engine;
pub use lggr_engine as epk_engine;

pub use crate::lggr_engine::{
    action_gluing_defect, analyze_composition, boundary_in_slice, calculate_metrics,
    compose_kernels, composed_kernel, evaluator_gluing_defect, evaluator_residual,
    exact_path_weight, fold_evaluator_events, g2_action_additive, g3_evaluator_factorizes,
    path_weight, residual_kernel_error, segment_kernel, validate_metric_identity, BoundarySlice,
    CompositionRecord, CompositionReport, EpkError, EpkMetrics, EvaluatorEvent, FormalExponent,
    FormalSeries, GluingDefect, Kernel, KernelKey, LggrError, LggrMetrics, ResidualKernelReport,
    TraceLedger, TraceRecord,
};

// Module paths preserved for `core_epk::core::…` / `::metrics::…` call sites.
pub mod composition {
    pub use crate::lggr_engine::{
        analyze_composition, boundary_in_slice, evaluator_residual, g2_action_additive,
        g3_evaluator_factorizes, CompositionReport,
    };
}
pub mod core {
    pub use crate::lggr_engine::{
        fold_evaluator_events, BoundarySlice, CompositionRecord, EvaluatorEvent, TraceLedger,
        TraceRecord,
    };
}
pub mod defects {
    pub use crate::lggr_engine::{action_gluing_defect, evaluator_gluing_defect, GluingDefect};
}
pub mod error {
    pub use crate::lggr_engine::{EpkError, LggrError};
}
pub mod kernels {
    pub use crate::lggr_engine::{
        compose_kernels, composed_kernel, exact_path_weight, path_weight, segment_kernel,
        FormalExponent, FormalSeries, Kernel, KernelKey,
    };
}
pub mod metrics {
    pub use crate::lggr_engine::{
        calculate_metrics, validate_metric_identity, EpkMetrics, LggrMetrics,
    };
}
pub mod residuals {
    pub use crate::lggr_engine::{residual_kernel_error, ResidualKernelReport};
}

pub mod adequacy;
pub mod bound_measurement;
pub mod ledger;
pub mod lggr_iv;
pub mod lggr_overlay;
pub mod lggr_v;
pub mod lggr_vi;
pub mod prime_seam;
pub mod residual_families;
pub mod verified_continuation_context_v2;
pub mod verified_continuation_context_v2_refusal_store;
pub mod verdict;

pub use verified_continuation_context_v2 as v2;
pub use verified_continuation_context_v2_refusal_store as v2_refusal_store;

pub use crate::adequacy::{
    detector_observed_corpus_digest, evaluate_detector_adequacy, DetectorAdequacyVerdict,
    DetectorAdequacyVerdictKind, DetectorCarrierClosureDisclosure, DetectorCorpusCounts,
    DetectorLocalSide, DetectorNumericalUnresolvedReason, DetectorStructuralFailure,
    DetectorUndeclaredReason, DETECTOR_ADEQUACY_VERDICT_SCHEMA,
    DETECTOR_OBSERVED_CORPUS_DIGEST_SCOPE, DETECTOR_THREAT_8_DISCLOSURE,
};
pub use crate::ledger::{EpkResidualFamilyError, EpkResidualFamilyReceipt, EpkResidualLedger};
pub use crate::lggr_iv::{
    check_completion_reflection, CompletionReflectionReport, FiniteInverseTower, LggrIvError,
    LGGR_IV_COMPLETION_SCHEMA,
};
pub use crate::lggr_v::{
    check_soundness, verify_unsoundness_witness, LggrSoundnessError, LggrSoundnessReport,
    LGGR_SOUNDNESS_SCHEMA, MAX_LGGR_CELLS,
};
pub use crate::lggr_vi::{
    check_postprocessing_and_probing, LggrViError, LggrViProbingReport, LGGR_VI_PROBING_SCHEMA,
};

// Origin: engine/crates_rs/core_local_green_global_red_lggr/src/lib.rs
// Claim: urn:core:crates_rs:core-local-green-global-red-lggr:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc263516e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc263516e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc263516e {
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
impl BoundaryErrorc263516e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc263516e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc263516e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc263516e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc263516e> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc263516e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc263516e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc263516e::ExceedsCapacity {
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
mod tests {
    use super::*;
    use num_rational::BigRational;

    #[test]
    fn host_reexports_engine_phone_test() {
        let comps: Vec<_> = [
            (true, true, true),
            (true, true, false),
            (true, true, false),
            (true, false, false),
            (false, true, false),
        ]
        .iter()
        .enumerate()
        .map(|(i, &(e1, e2, eg))| {
            CompositionRecord::new(format!("c{i}"), "l", "r", e1, e2, eg, None).unwrap()
        })
        .collect();
        let m = calculate_metrics(&comps, None, None, None, None).unwrap();
        assert_eq!(m.lpr, BigRational::new(3.into(), 5.into()));
        assert_eq!(m.ngd, BigRational::new(2.into(), 5.into()));
        assert_eq!(m.gpr, BigRational::new(1.into(), 5.into()));
        assert_eq!(m.avg_delta_eval, BigRational::new((-2).into(), 5.into()));
    }
}

#[cfg(test)]
mod l4_boundary_tests_c263516e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc263516e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc263516e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc263516e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc263516e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc263516e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc263516e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc263516e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
