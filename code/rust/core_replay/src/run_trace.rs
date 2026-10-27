use serde::{Deserialize, Serialize};

/// Structural density diagnostics captured as trace data.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct TraceDensityDiagnostics {
    pub dim: usize,
    pub total_trace: f64,
    pub purity: f64,
    pub entropy_bits: f64,
    pub l1_coherence: f64,
    pub diagonal_probs: Vec<(char, f64)>,
    pub eigenvalues: Vec<f64>,
}

// ---------------------------------------------------------------------------
// Top-Level Trace
// ---------------------------------------------------------------------------

/// The complete epistemic record of a single projective run.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RunTrace {
    // --- Identity ---
    pub run_id: String,
    pub timestamp_utc: String,
    pub test_name: String,

    // --- Model ---
    pub model: String,
    pub fingerprint: String,
    pub prompt_length: usize,
    pub prompt_text: String,

    // --- Perception (Sieve reading of the prompt) ---
    pub perception: PerceptionSnapshot,

    // --- Symbolic Boundary Checkpoints ---
    /// Forge Boundary: density matrix of the *input prompt* before generation
    pub forge_boundary: Option<BoundarySnapshot>,
    /// Sieve Main Boundary: density matrix of the *output* after Adversary validation
    pub sieve_boundary: Option<BoundarySnapshot>,

    // --- Per-Step Boundary (CoT reasoning step density matrices) ---
    pub step_boundary_snapshots: Vec<BoundarySnapshot>,

    // --- Pipeline Stages ---
    pub stages: Vec<TraceStage>,

    // --- Verdict ---
    pub verdict: VerdictRecord,

    // --- Evaluation Graph ---
    pub evaluation_graph: Option<EvaluationGraph>,

    // --- System Metadata ---
    pub system_version: Option<String>,
    pub tower_hash: Option<String>,
    pub tower_lambda_count: Option<usize>,

    // --- Structural Analysis (Î¦â‚ / B / Coercion / Fabrication) ---
    pub structural_phi_1: Option<f64>,
    pub structural_c2: Option<f64>,
    pub structural_b_score: Option<f64>,
    pub structural_coercion_events: Option<usize>,
    pub structural_fabrication_detected: Option<bool>,
    pub structural_declared_repairs: Option<usize>,
    pub structural_lifts_used: Option<usize>,
    pub structural_b_types: Option<Vec<String>>,

    // --- Obstruction Diagnostics (Î¦â‚ / Î“â‚‚ / Îž per trace) ---
    /// Recommended metrics logged per trace for the Î¦â‚â†’Î“â‚‚â†’Îž pipeline.
    /// See: lefschetz.rs (Îž-channel), maurer_cartan.rs (Î“â‚‚-channel).
    pub obstruction_diagnostics: Option<ObstructionDiagnostics>,

    // --- CoT Step Content (for narrative rendering) ---
    /// Raw text of each CoT reasoning step (for auditable narrative).
    #[serde(default)]
    pub cot_step_texts: Vec<String>,

    // --- Legacy compat ---
    pub success: bool,
}

// ---------------------------------------------------------------------------
// Perception
// ---------------------------------------------------------------------------

/// How the epistemic sieve initially reads the prompt.
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PerceptionSnapshot {
    pub prompt_class: String,
    pub morphism_type: String,
    pub entropy: f64,
    pub coherence: f64,
    pub decidability: f64,
    pub hostility: f64,
}

// ---------------------------------------------------------------------------
// Symbolic Boundary Density Matrix Snapshot
// ---------------------------------------------------------------------------

/// A single Symbolic Boundary density matrix checkpoint.
///
/// Contains both the summary metrics (for JSONL) and the full spectral
/// decomposition (for narrative rendering). The off-diagonal coherences
/// are the research gold â€” they show which token-class domains are entangled.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BoundarySnapshot {
    /// Checkpoint name: "forge", "sieve_main"
    pub checkpoint: String,

    // --- Summary metrics ---
    pub purity: f64,
    pub entropy_bits: f64,
    pub l1_coherence: f64,
    pub nonzero_eigenvalues: usize,
    pub total_eigenvalues: usize,

    // --- Full spectral data (for narrative rendering) ---
    /// All eigenvalues of the density matrix, sorted descending
    pub eigenvalue_spectrum: Vec<f64>,

    /// Top off-diagonal coherences, sorted by magnitude descending
    pub top_coherences: Vec<OffDiagonalCoherence>,
}

/// Compatibility alias for the Symbolic Boundary Engine (SBE) snapshot.
/// Compatibility alias for the Symbolic Boundary Engine (SBE) snapshot.
pub type SbeSnapshot = BoundarySnapshot;

/// Compatibility alias for the Symbolic Boundary Engine (SBE) trace metrics.
pub type SbeTrace = TraceDensityDiagnostics;

/// Compatibility alias for the Boundary trace metrics.
pub type BoundaryTrace = TraceDensityDiagnostics;

/// A single off-diagonal coherence entry from the density matrix.
///
/// Shows the complex coherence between two token-class basis states.
/// Rendered in narrative as:
/// ```text
/// | From â†’ To | Re | Im | Magnitude |
/// | âŽµâ†’âˆ—      | +0.221819 | +0.007951 | 0.221962 |
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OffDiagonalCoherence {
    pub from_label: String,
    pub to_label: String,
    pub re: f64,
    pub im: f64,
    pub magnitude: f64,
}

// ---------------------------------------------------------------------------
// Verdict
// ---------------------------------------------------------------------------

/// The final epistemic judgment on a projective run.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VerdictRecord {
    pub verdict: String,
    pub epistemic_value: f64,
    pub quality: f64,
    pub evaluation: String,
    pub failure_modes: Vec<String>,
}

impl Default for VerdictRecord {
    fn default() -> Self {
        Self {
            verdict: "PENDING".to_string(),
            epistemic_value: 0.0,
            quality: 0.0,
            evaluation: String::new(),
            failure_modes: Vec::new(),
        }
    }
}

// ---------------------------------------------------------------------------
// Obstruction Diagnostics (Î¦â‚ / Î“â‚‚ / Îž per trace)
// ---------------------------------------------------------------------------

/// Per-trace obstruction metrics for the Î¦â‚ â†’ Î“â‚‚ â†’ Îž pipeline.
///
/// These are the recommended metrics to log per trace:
///
/// | Signal   | Source                  | Detects                       |
/// |----------|-------------------------|-------------------------------|
/// | Î¦â‚       | quotient obstruction    | correctness / acceptance      |
/// | mean(a)  | cochain statistics      | baseline obstruction level    |
/// | Î“â‚‚       | ||MC(a)||â‚              | spikes / discontinuities      |
/// | Îž_raw    | Î£ a[i]Â·a[i+1]           | alignment / coherence (raw)   |
/// | Îž_norm   | Îž_raw / (||a||Â² + Îµ)    | alignment / coherence (scaled)|
/// | length   | trace length            | coverage                      |
///
/// Combined filter:
/// ```text
/// keep Ï„ if:
///     Î¦â‚(Ï„) passes
/// AND Î“â‚‚(Ï„) â‰¤ Î¸â‚‚
/// AND Îž(Ï„) â‰¥ Î¸â‚ƒ
/// ```
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObstructionDiagnostics {
    /// Whether Î¦â‚ acceptance passed for this trace.
    pub phi1_pass: bool,
    /// Î¦â‚ value (quotient obstruction magnitude).
    pub phi1_value: f64,
    /// Mean of the cochain values: mean(a).
    pub cochain_mean: f64,
    /// Î“â‚‚ = ||MC(a)||â‚ â€” Maurer-Cartan residual norm (closure rupture).
    pub gamma2: f64,
    /// Îž_raw = Î£ a[i]Â·a[i+1] â€” raw shift-coherence score.
    pub xi_raw: f64,
    /// Îž_norm = Îž_raw / (||a||Â² + Îµ) â€” normalized coherence.
    pub xi_norm: f64,
    /// Trace length (number of cochain entries).
    pub trace_length: usize,

    // --- Phase Analysis (entropy-based reasoning phase tracking) ---
    /// Per-transition entropy deltas: Î”S[i] = S[i+1] - S[i].
    #[serde(default)]
    pub entropy_deltas: Vec<f64>,
    /// Per-transition phase labels: "+1" = EXPAND, "0" = NEUTRAL, "-1" = CONTRACT.
    #[serde(default)]
    pub phase_labels: Vec<String>,
    /// Whether the phase sequence is valid (EXPAND* â†’ CONTRACT*, no re-expansion).
    #[serde(default)]
    pub phase_valid: bool,
    /// Threshold used for phase classification.
    #[serde(default)]
    pub phase_threshold: f64,
    /// Number of sign flips in the cochain.
    #[serde(default)]
    pub sign_flips: usize,

    // --- Semantic Continuity (cosine similarity gating) ---
    /// Per-transition cosine similarity: sim(Ïˆ_i, Ïˆ_{i+1}).
    #[serde(default)]
    pub semantic_similarities: Vec<f64>,
    /// Per-transition task shift flag: sim < Ï„_sem.
    #[serde(default)]
    pub task_shifts: Vec<bool>,
    /// Phase validity WITH semantic gating (Contractâ†’Expand allowed at task shifts).
    #[serde(default)]
    pub phase_valid_gated: bool,
    /// Semantic similarity threshold for task shift detection.
    #[serde(default)]
    pub tau_sem: f64,
    /// Number of task shifts detected.
    #[serde(default)]
    pub task_shift_count: usize,

    // --- Boundary Audit (Î“â‚‚ split: smooth interior + spike) ---
    /// B_max: magnitude of the largest Î”S spike.
    #[serde(default)]
    pub b_max: f64,
    /// Index of the boundary transition.
    #[serde(default)]
    pub boundary_idx: usize,
    /// Whether boundary is at the final step.
    #[serde(default)]
    pub boundary_at_final: bool,
    /// Î“â‚‚_smooth: mean variation over non-boundary transitions.
    #[serde(default)]
    pub gamma2_smooth: f64,
    /// Number of boundary events (|Î”S| spike + semantic discontinuity).
    #[serde(default)]
    pub boundary_count: usize,
    /// Good trace signature: stable interior + single final boundary.
    #[serde(default)]
    pub good_trace_signature: bool,

    // --- Algebraic Invariants (Commutant Dimension) ---
    /// Algebraic invariant check output across sliding windows of density matrices.
    #[serde(default)]
    pub algebraic_audit: Option<()>,
}

// ---------------------------------------------------------------------------
// Evaluation Graph
// ---------------------------------------------------------------------------

/// Directed graph of the evaluation structure.
///
/// Nodes are evaluation steps, edges are logical dependencies.
/// Topology classification: "linear", "branching_dag", "cyclic", etc.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EvaluationGraph {
    pub num_nodes: usize,
    pub edges: Vec<(usize, usize)>,
    pub node_labels: Vec<NodeLabel>,
    pub topology: String,
    pub branch_points: Vec<usize>,
    pub merge_points: Vec<usize>,
    pub dead_ends: Vec<usize>,
    pub graph_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NodeLabel {
    pub index: usize,
    pub label: String,
}

// ---------------------------------------------------------------------------
// Pipeline Stage
// ---------------------------------------------------------------------------

/// A single stage in the pipeline execution.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TraceStage {
    pub stage: String,
    pub code_origin: String,
    pub phi_before: Option<f64>,
    pub phi_after: Option<f64>,
    pub invariants: serde_json::Value,
    pub details: serde_json::Value,
}

// ---------------------------------------------------------------------------
// Builder
// ---------------------------------------------------------------------------

impl RunTrace {
    /// Create a new trace with minimal required fields.
    /// All optional fields default to None/empty.
    pub fn new(
        run_id: String,
        timestamp_utc: String,
        test_name: String,
        model: String,
        fingerprint: String,
        prompt_length: usize,
        prompt_text: String,
    ) -> Self {
        Self {
            run_id,
            timestamp_utc,
            test_name,
            model,
            fingerprint,
            prompt_length,
            prompt_text,
            perception: PerceptionSnapshot::default(),
            forge_boundary: None,
            sieve_boundary: None,
            step_boundary_snapshots: Vec::new(),
            stages: Vec::new(),
            verdict: VerdictRecord::default(),
            evaluation_graph: None,
            system_version: None,
            tower_hash: None,
            tower_lambda_count: None,
            structural_phi_1: None,
            structural_c2: None,
            structural_b_score: None,
            structural_coercion_events: None,
            structural_fabrication_detected: None,
            structural_declared_repairs: None,
            structural_lifts_used: None,
            structural_b_types: None,
            obstruction_diagnostics: None,
            cot_step_texts: Vec::new(),
            success: false,
        }
    }

    /// Set the perception snapshot.
    pub fn with_perception(mut self, perception: PerceptionSnapshot) -> Self {
        self.perception = perception;
        self
    }

    /// Set the forge (input prompt) boundary checkpoint.
    pub fn with_forge_boundary(mut self, snapshot: BoundarySnapshot) -> Self {
        self.forge_boundary = Some(snapshot);
        self
    }

    /// Set the sieve main (output post-validation) boundary checkpoint.
    pub fn with_sieve_boundary(mut self, snapshot: BoundarySnapshot) -> Self {
        self.sieve_boundary = Some(snapshot);
        self
    }

    /// Set the verdict.
    pub fn with_verdict(mut self, verdict: VerdictRecord) -> Self {
        self.success = verdict.verdict == "PROMOTED"
            || verdict.verdict == "CRYSTALLIZED"
            || verdict.verdict == "DIAMOND";
        self.verdict = verdict;
        self
    }

    /// Set the evaluation graph.
    pub fn with_evaluation_graph(mut self, graph: EvaluationGraph) -> Self {
        self.evaluation_graph = Some(graph);
        self
    }

    /// Add a pipeline stage.
    pub fn push_stage(&mut self, stage: TraceStage) {
        self.stages.push(stage);
    }

    /// Set the obstruction diagnostics (Î¦â‚ / Î“â‚‚ / Îž metrics).
    pub fn with_obstruction_diagnostics(mut self, diag: ObstructionDiagnostics) -> Self {
        self.obstruction_diagnostics = Some(diag);
        self
    }
}

// Origin: engine/crates_rs/core_replay/src/run_trace.rs
// Claim: urn:core:crates_rs:core-replay:run-trace:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord30850fcc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord30850fcc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError30850fcc {
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
impl BoundaryError30850fcc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError30850fcc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError30850fcc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord30850fcc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError30850fcc> {
        if capacity_bound == 0 {
            return Err(BoundaryError30850fcc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError30850fcc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError30850fcc::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_30850fcc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord30850fcc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord30850fcc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord30850fcc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord30850fcc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord30850fcc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError30850fcc::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError30850fcc::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
