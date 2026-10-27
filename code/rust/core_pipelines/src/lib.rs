//! --- Math Contract: bounded orchestration preserves explicit authority and residual boundaries.
//! `core_pipelines` — the canonical home for the authority pipeline `Π_S^#`
//! (ADR-107-001).
//!
//! This crate is a **composer / orchestrator**: it composes the five named
//! Kleisli stages over the refusal monad `M(Y) = Y + F` (whose *primitive* lives
//! in [`core_types::Refusable`], Sprint 108), and provides the CODA_GTLANF idempotent
//! normalizer. Each stage delegates to the leaf crate that owns its substrate;
//! **nothing depends on `core_pipelines`** except the top-level binary / PyO3
//! surface (leaf-direction preserved, ADR-107-001 §1).
//!
//! Modules (added per story across Sprint 110):
//! - `kleisli`   — `∘_K` composition over `Refusable` (STORY-110-002)
//! - `coda_gtlanf`    — the CODA_GTLANF idempotent normalizer `L ⊣ I` (STORY-110-004)
//! - `loop_step` — the core_certifier_loop guard-only no-op Kleisli step over
//!   sealed rows (Sprint core_certifier_loop, 2026-06-21; honesty pass 2026-06-22)
//! - `rewrite_scheduler` - exact, non-identity rewrites that create a fresh
//!   checked row before evidence certification; authority promotion remains a
//!   separate authenticated host operation

pub mod bounded_rewrite;
pub mod coda_gtla;
pub mod finite_lambda_adapter;
pub mod coda_gtlanf;
pub mod kleisli;
pub mod loop_step;
pub mod rewrite_scheduler;
pub mod runtime;
pub mod report_route;

pub use coda_gtla::{evaluate_pipeline, PipelineInput, PipelineOutput};

/// Exact integer carried by an admitted Kleisli composition.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct KleisliPayload {
    payload: i64,
}

/// Refusal of a Kleisli payload check.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum KleisliPayloadError {
    DownstreamRan,
    NotRefused,
    Refused,
    Overflow,
    PayloadMismatch { expected: i64, actual: i64 },
}

// Origin: engine/crates_rs/core_pipelines/src/lib.rs
// Claim: urn:core:crates_rs:core-pipelines:lib:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for KleisliPayloadError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for KleisliPayloadError {}

impl KleisliPayload {
    /// A refusing first arrow stays refused, and the downstream arrow does not run.
    pub fn refused(seed: i64) -> Result<core_types::Refusable<i64>, KleisliPayloadError> {
        let downstream_ran = std::cell::Cell::new(false);
        let composed = kleisli::compose_k(
            |_value: i64| {
                downstream_ran.set(true);
                core_types::Refusable::Value(0)
            },
            |_value: i64| core_types::Refusable::Refused(core_types::RefusalSource::Refusal),
        );
        let outcome = composed(seed);
        if downstream_ran.get() {
            return Err(KleisliPayloadError::DownstreamRan);
        }
        match outcome {
            core_types::Refusable::Refused(_) => Ok(outcome),
            core_types::Refusable::Value(_) => Err(KleisliPayloadError::NotRefused),
        }
    }

    /// Increment then double, and keep the composition only when it equals that exact value.
    pub fn admitted(start: i64) -> Result<Self, KleisliPayloadError> {
        let composed = kleisli::then(
            |value: i64| match value.checked_add(1) {
                Some(next) => core_types::Refusable::Value(next),
                None => core_types::Refusable::Refused(core_types::RefusalSource::Refusal),
            },
            |value: i64| match value.checked_mul(2) {
                Some(next) => core_types::Refusable::Value(next),
                None => core_types::Refusable::Refused(core_types::RefusalSource::Refusal),
            },
        );
        let expected = start
            .checked_add(1)
            .and_then(|value| value.checked_mul(2))
            .ok_or(KleisliPayloadError::Overflow)?;
        match composed(start) {
            core_types::Refusable::Value(payload) if payload == expected => Ok(Self { payload }),
            core_types::Refusable::Value(actual) => Err(KleisliPayloadError::PayloadMismatch { expected, actual }),
            core_types::Refusable::Refused(_) => Err(KleisliPayloadError::Refused),
        }
    }

    /// Payload preserved by the admitted composition.
    pub fn payload(self) -> i64 {
        self.payload
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod kleisli_payload_checks {
    use super::{KleisliPayload, KleisliPayloadError};

    #[test]
    fn a_refused_composition_stays_refused_and_an_admitted_one_keeps_its_payload() {
        let refused = KleisliPayload::refused(7);
        assert!(matches!(
            refused,
            Ok(core_types::Refusable::Refused(core_types::RefusalSource::Refusal))
        ));
        let admitted = KleisliPayload::admitted(7);
        assert_eq!(admitted.map(KleisliPayload::payload), Ok(16));
        assert!(matches!(
            KleisliPayload::admitted(i64::MAX),
            Err(KleisliPayloadError::Overflow)
        ));
    }
}
