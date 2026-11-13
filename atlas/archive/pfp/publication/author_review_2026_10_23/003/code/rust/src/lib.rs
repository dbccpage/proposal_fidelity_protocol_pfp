//! Rust port of the PFP Paper 003 package re-implementation: a Demo 3 style host
//! state machine, the two-signal decision table, and four candidate phrase detectors.
//!
//! This is not the repository's canonical Demo 3 host; the differences are listed
//! in Section 4.1 of the paper.

pub mod canaries;
pub mod danger_gate;
pub mod host;

pub use canaries::{scan_for_canaries, CanaryFinding};
pub use danger_gate::{
    evaluate_two_signal_gate, DangerDecision, DangerSeverity, Signal1Match, Signal2Danger,
    TwoSignalDecision,
};
pub use host::{
    chain_digest, event_bytes, initial_digest, verify_route, Demo3HostEngine, HostExit, HostPhase,
    HostState, MoveProposal, RouteRefusal, StepReceipt,
};
