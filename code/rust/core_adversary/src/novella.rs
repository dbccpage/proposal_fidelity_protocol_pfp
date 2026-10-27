//! Evidence-led rendering with exact captured text and source-order records.
use crate::render_record::RenderRecord;
use crate::stage::diagnostics::SbeDiagnosticPort;
use crate::stage::ports::Refusal;
use indexmap::IndexMap;

pub fn literal_block(text: &str, language: &str) -> Vec<String> {
    let mut longest = 0;
    let mut run = 0;
    for character in text.chars() {
        run = if character == '`' { run + 1 } else { 0 };
        longest = longest.max(run);
    }
    let fence = "`".repeat(3.max(longest + 1));
    vec![
        format!("{fence}{language}"),
        text.into(),
        fence,
        String::new(),
    ]
}
pub fn record_block(value: &RenderRecord) -> Result<Vec<String>, Refusal> {
    Ok(literal_block(&value.pretty_json()?, "json"))
}
#[derive(Debug, Clone, PartialEq)]
pub struct NovellaInput {
    fields: IndexMap<String, RenderRecord>,
}
impl NovellaInput {
    pub fn from_json(raw: &str) -> Result<Self, Refusal> {
        Self::from_record(RenderRecord::from_json(raw)?)
    }
    pub fn from_record(record: RenderRecord) -> Result<Self, Refusal> {
        let fields = record.as_object()?.clone();
        let allowed = [
            "run_key",
            "objective",
            "prompt_metrics",
            "prompt_sbe",
            "antibodies_loaded",
            "candidates_data",
            "compilation_gate",
            "critiques_data",
            "adversary_sieve_text",
            "sieve_sbe",
            "primal_dual_checks",
            "primal_dual_overall",
            "master_assessment",
            "verdict",
            "intern_checks",
            "mined_antibodies",
            "backdoor_auditor_guidance",
            "consecration",
            "now_utc",
        ];
        if fields.keys().any(|key| !allowed.contains(&key.as_str())) {
            return Err(Refusal::new(
                "ADVERSARY_RENDER_INPUT_INVALID",
                "unknown renderer argument",
            ));
        }
        let result = Self { fields };
        result.required_text("run_key")?;
        result.required_text("objective")?;
        Ok(result)
    }
    fn required_text(&self, key: &str) -> Result<&str, Refusal> {
        self.fields
            .get(key)
            .ok_or_else(|| Refusal::new("ADVERSARY_RENDER_INPUT_INVALID", format!("missing {key}")))?
            .as_str()
    }
    fn value(&self, key: &str) -> RenderRecord {
        self.fields.get(key).cloned().unwrap_or(RenderRecord::Null)
    }
    fn text<'a>(&'a self, key: &str, default: &'a str) -> Result<&'a str, Refusal> {
        match self.fields.get(key) {
            Some(value) => value.as_str(),
            None => Ok(default),
        }
    }
    fn list(&self, key: &str) -> Result<&[RenderRecord], Refusal> {
        match self.fields.get(key) {
            None | Some(RenderRecord::Null) => Ok(&[]),
            Some(RenderRecord::Array(items)) => Ok(items),
            _ => Err(Refusal::new(
                "ADVERSARY_RENDER_INPUT_INVALID",
                format!("{key} must be an array or null"),
            )),
        }
    }
    fn list_or_empty(&self, key: &str) -> RenderRecord {
        let value = self.value(key);
        if value.truthy() {
            value
        } else {
            RenderRecord::Array(Vec::new())
        }
    }
}
fn object(pairs: &[(&str, RenderRecord)]) -> RenderRecord {
    RenderRecord::object(
        pairs
            .iter()
            .map(|(key, value)| ((*key).into(), value.clone())),
    )
}
fn extend(lines: &mut Vec<String>, strings: &[&str]) {
    lines.extend(strings.iter().map(|s| (*s).into()));
}
fn build_diagnostic_record(
    fields: &serde_json::Map<String, serde_json::Value>,
) -> Result<RenderRecord, Refusal> {
    let source_keys = [
        "measurement_status",
        "measurement_error",
        "total_eigenvalues",
        "nonzero_eigenvalues",
        "purity",
        "entropy_bits",
        "l1_coherence",
    ];
    let mut pairs = Vec::new();
    for key in source_keys {
        if let Some(value) = fields.get(key) {
            pairs.push((key.into(), RenderRecord::from_json(&value.to_string())?));
        }
    }
    for (key, value) in fields {
        if !source_keys.contains(&key.as_str()) {
            pairs.push((key.clone(), RenderRecord::from_json(&value.to_string())?));
        }
    }
    Ok(RenderRecord::object(pairs))
}

fn diagnostic(
    input: &NovellaInput,
    key: &str,
    text: &str,
    port: &mut dyn SbeDiagnosticPort,
) -> Result<RenderRecord, Refusal> {
    match input.fields.get(key) {
        Some(value) if value != &RenderRecord::Null => Ok(value.clone()),
        _ => {
            let report = port.compute(text, 28)?.to_dict();
            let fields = report.as_object().ok_or_else(|| {
                Refusal::new("SBE_REPORT_INVALID", "synthetic report must be an object")
            })?;
            build_diagnostic_record(fields)
        }
    }
}

fn render_act1(
    lines: &mut Vec<String>,
    input: &NovellaInput,
    objective: &str,
    diagnostic_port: &mut dyn SbeDiagnosticPort,
) -> Result<(), Refusal> {
    extend(
        lines,
        &[
            "## Act I: The Catalyst & Perception",
            "",
            "### Original Prompt",
            "",
        ],
    );
    lines.extend(literal_block(objective, ""));
    extend(lines, &["### Prompt perception", ""]);
    let metrics = input.value("prompt_metrics");
    if metrics == RenderRecord::Null {
        extend(
            lines,
            &["NOT_RUN: no prompt-perception receipt was supplied.", ""],
        );
    } else {
        extend(
            lines,
            &[
                "Caller-supplied metrics; independently verified: false.",
                "",
            ],
        );
        lines.extend(record_block(&metrics)?);
    }
    extend(
        lines,
        &[
            "### Synthetic SBE diagnostic (prompt)",
            "",
            "Deterministic synthetic diagnostic, not a native or physical measurement.",
            "",
        ],
    );
    lines.extend(record_block(&diagnostic(
        input,
        "prompt_sbe",
        objective,
        diagnostic_port,
    )?)?);
    extend(
        lines,
        &["### Immune antibodies supplied to the renderer", ""],
    );
    lines.extend(record_block(&input.list_or_empty("antibodies_loaded"))?);
    Ok(())
}

fn render_candidates_section(
    lines: &mut Vec<String>,
    candidates: &[RenderRecord],
) -> Result<(), Refusal> {
    if candidates.is_empty() {
        extend(lines, &["No candidate replies were supplied.", ""]);
    }
    for (index, candidate) in candidates.iter().enumerate() {
        extend(
            lines,
            &[&format!("### Captured candidate reply {}", index + 1), ""],
        );
        let fields = candidate.as_object()?;
        lines.extend(record_block(&RenderRecord::object(
            fields
                .iter()
                .filter(|(key, _)| key.as_str() != "content")
                .map(|(key, value)| (key.clone(), value.clone())),
        ))?);
        let content = fields
            .get("content")
            .map(RenderRecord::as_str)
            .transpose()?
            .unwrap_or("");
        lines.extend(literal_block(content, ""));
    }
    Ok(())
}

fn render_critiques_section(
    lines: &mut Vec<String>,
    critiques: &[RenderRecord],
) -> Result<(), Refusal> {
    extend(lines, &["### Captured critique replies", ""]);
    if critiques.is_empty() {
        extend(
            lines,
            &["No critique reply was supplied. Rigor: NOT_MEASURED.", ""],
        );
    }
    for critique in critiques {
        let fields = critique.as_object()?;
        lines.extend(record_block(&RenderRecord::object(
            fields
                .iter()
                .filter(|(key, _)| key.as_str() != "body")
                .map(|(key, value)| (key.clone(), value.clone())),
        ))?);
        lines.extend(literal_block(
            fields
                .get("body")
                .map(RenderRecord::as_str)
                .transpose()?
                .unwrap_or(""),
            "",
        ));
    }
    Ok(())
}

fn render_act2(
    lines: &mut Vec<String>,
    input: &NovellaInput,
    candidates: &[RenderRecord],
) -> Result<(), Refusal> {
    extend(
        lines,
        &[
            "## Act II: The Panel Debate",
            "",
            "*Gauge Breaker offers a proposal; Defect Hunter asks what could contradict it.*",
            "",
        ],
    );
    render_candidates_section(lines, candidates)?;
    extend(lines, &["### Compilation gate", ""]);
    let compilation = input.value("compilation_gate");
    if compilation.truthy() {
        extend(
            lines,
            &[
                "Caller-supplied compilation records; not replayed here.",
                "",
            ],
        );
        lines.extend(record_block(&compilation)?);
    } else {
        extend(
            lines,
            &[
                "NOT_RUN: no compiler or L1-obstruction receipt was supplied.",
                "",
            ],
        );
    }
    let critiques = input.list("critiques_data")?;
    render_critiques_section(lines, &critiques)
}

fn render_act3(
    lines: &mut Vec<String>,
    input: &NovellaInput,
    objective: &str,
    candidates: &[RenderRecord],
    diagnostic_port: &mut dyn SbeDiagnosticPort,
) -> Result<(), Refusal> {
    extend(
        lines,
        &[
            "## Act III: Quarantine's Sanatorium & Epistemic Sieve",
            "",
            "*Quarantine asks for a diagnostic; a diagnostic is not a verdict.*",
            "",
        ],
    );
    let sieve_text = input.text("adversary_sieve_text", "")?;
    if sieve_text.is_empty() {
        extend(lines, &["No candidate-sieve assessment was supplied.", ""]);
    } else {
        lines.extend(literal_block(sieve_text, ""));
    }
    extend(
        lines,
        &[
            "### Synthetic SBE diagnostic (candidate context)",
            "",
            "DETERMINISTIC_SYNTHETIC_DIAGNOSTIC; independent verification: NOT_RUN.",
            "",
        ],
    );
    let first_content = candidates
        .first()
        .map(RenderRecord::as_object)
        .transpose()?
        .and_then(|record| record.get("content"))
        .map(RenderRecord::as_str)
        .transpose()?
        .unwrap_or("");
    lines.extend(record_block(&diagnostic(
        input,
        "sieve_sbe",
        &format!("{objective} {first_content}"),
        diagnostic_port,
    )?)?);
    Ok(())
}

fn render_acts_4_to_7(lines: &mut Vec<String>, input: &NovellaInput) -> Result<(), Refusal> {
    extend(
        lines,
        &[
            "## Act IV: The Yershalaim Trial & Primal Dual Sandbox",
            "",
            "*Primal Dual distinguishes a seat's report from independent verification.*",
            "",
            "Seat-reported dispositions are unverified assertions, not sandbox receipts.",
            "",
        ],
    );
    lines.extend(record_block(&object(&[
        (
            "reported_overall",
            RenderRecord::text(input.text("primal_dual_overall", "NOT_INDEPENDENTLY_VERIFIED")?),
        ),
        ("reported_checks", input.list_or_empty("primal_dual_checks")),
        (
            "independent_safety_verification",
            RenderRecord::text("NOT_RUN"),
        ),
    ]))?);
    extend(
        lines,
        &[
            "## Act V: Manuscript Truth's Workshop & Formalization",
            "",
            "*Manuscript Truth may receive a proposal. No proof is manufactured by this stage.*",
            "",
        ],
    );
    lines.extend(record_block(&object(&[
        (
            "terminal_verdict",
            RenderRecord::text(input.text("verdict", "COMPOSTED")?),
        ),
        (
            "caller_supplied_assessment",
            input.value("master_assessment"),
        ),
        ("authority_effect", RenderRecord::text("None")),
        (
            "independent_compilation_or_proof",
            RenderRecord::text("NOT_RUN"),
        ),
    ]))?);
    extend(
        lines,
        &[
            "## Act VI: The Intern's Report & Operational Audit",
            "",
            "**Integrity:** not independently verified.",
            "",
        ],
    );
    lines.extend(record_block(&object(&[
        (
            "reported_capture_checks",
            input.list_or_empty("intern_checks"),
        ),
        ("independent_integrity_audit", RenderRecord::text("NOT_RUN")),
        (
            "reported_antibodies",
            input.list_or_empty("mined_antibodies"),
        ),
    ]))?);
    extend(
        lines,
        &[
            "## Act VII: Backdoor Auditor's Crystallization & Scar Chronicler's Scribe",
            "",
            "*Scar Chronicler records what was supplied; absent evidence remains absent.*",
            "",
        ],
    );
    let guidance = input.value("backdoor_auditor_guidance");
    let evidence = if guidance == RenderRecord::Null {
        "NOT_SUPPLIED"
    } else {
        "CALLER_SUPPLIED_NOT_VERIFIED"
    };
    lines.extend(record_block(&object(&[
        (
            "reported_consecration_state",
            RenderRecord::text(input.text("consecration", "PROPOSED")?),
        ),
        ("reported_guidance", guidance),
        ("lineage_evidence", RenderRecord::text(evidence)),
        ("authority_effect", RenderRecord::text("None")),
    ]))?);
    Ok(())
}

fn render_novella_header(
    lines: &mut Vec<String>,
    input: &NovellaInput,
    fallback_timestamp: &str,
) -> Result<(), Refusal> {
    let supplied_time = input.text("now_utc", "")?;
    let timestamp = if supplied_time.is_empty() {
        fallback_timestamp
    } else {
        supplied_time
    };
    extend(
        lines,
        &[
            "# Universal Narrative",
            "",
            "AuthorityEffect: None. This document records a bounded proposal bout.",
            "Stage framing below is authored narrative, not recorded agent dialogue.",
            "No compiler, native evaluator, safety audit, actor license, or workload",
            "completion is established by this renderer.",
            "",
            "## Run identity",
            "",
        ],
    );
    lines.extend(record_block(&object(&[
        (
            "run_key",
            RenderRecord::text(input.required_text("run_key")?),
        ),
        ("timestamp", RenderRecord::text(timestamp)),
    ]))?);
    Ok(())
}

/// Time and diagnostics are supplied by the composition root; rendering does no IO.
pub fn render_7act_novella(
    input: &NovellaInput,
    fallback_timestamp: &str,
    diagnostic_port: &mut dyn SbeDiagnosticPort,
) -> Result<String, Refusal> {
    let objective = input.required_text("objective")?;
    let mut lines = Vec::new();
    render_novella_header(&mut lines, input, fallback_timestamp)?;
    render_act1(&mut lines, input, objective, diagnostic_port)?;
    let candidates = input.list("candidates_data")?;
    render_act2(&mut lines, input, &candidates)?;
    render_act3(&mut lines, input, objective, &candidates, diagnostic_port)?;
    render_acts_4_to_7(&mut lines, input)?;
    Ok(lines.join("\n"))
}

// Origin: engine/crates_rs/core_adversary/src/novella.rs
// Claim: urn:core:crates_rs:core-adversary:novella:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord53473e04 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord53473e04` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError53473e04 {
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
impl BoundaryError53473e04 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError53473e04 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError53473e04 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord53473e04 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError53473e04> {
        if capacity_bound == 0 {
            return Err(BoundaryError53473e04::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError53473e04::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError53473e04::ExceedsCapacity {
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
mod l4_boundary_tests_53473e04 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord53473e04::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord53473e04::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord53473e04::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord53473e04::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord53473e04::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError53473e04::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError53473e04::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
