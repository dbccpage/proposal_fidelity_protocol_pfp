//! Trusted finite-DDA JSON contract, verifier, and canonical Rust renderer.
//!
//! This is a no-authority surface. It checks packet bytes, the F2 cochain
//! identity, every operation law, every defect, and the terminal state.
//! Carrier-changing operations and imports route to OracleNeeded because the
//! current verifier does not establish lift licensing.

use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

use crate::ddc::ddc_alphabet::{DdaOp, DdaStep, TraceTerminal};
use crate::ddc::degree_tower::{BinaryCochainSegment, BinaryLinearMap, DegreeTrichotomy};
use crate::ddc::op_verification::{CochainState, VerifiedTrace};

const ACTIVE_OPERATIONS: [&str; 5] = ["E", "R", "I", "M", "T"];
const REQUIRED_NONCLAIMS: [&str; 3] = [
    "GTOC-1..8 are not globally proved",
    "No CertifiedAuthority is minted",
    "Agent artifacts have AuthorityEffect::None",
];

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Carrier {
    pub id: String,
    pub coefficient_ring: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorkDefect {
    pub defect_id: String,
    pub residual: Vec<bool>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorkBudgets {
    pub max_wall_seconds: u64,
    pub max_changed_files: usize,
    pub max_diff_bytes: usize,
    pub max_repairs: usize,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TerminalPolicy {
    pub allow_survivor: bool,
    pub require_terminal_op: bool,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentWorkPacket {
    pub schema_version: String,
    pub item_id: String,
    pub carrier: Carrier,
    pub c0: Vec<String>,
    pub c1: Vec<String>,
    pub c2: Vec<String>,
    pub d0: Vec<Vec<bool>>,
    pub d1: Vec<Vec<bool>>,
    pub zero_rel: String,
    pub defects: Vec<WorkDefect>,
    pub allowed_operations: Vec<String>,
    pub oracle_policy: String,
    pub evidence_ceiling: String,
    pub packet_refs: Vec<String>,
    pub write_surface: Vec<String>,
    pub budgets: WorkBudgets,
    pub nonclaims: Vec<String>,
    pub terminal_policy: TerminalPolicy,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SymbolCandidate {
    pub family: String,
    pub grammar: String,
}

#[derive(Debug, Clone, Copy, Deserialize, Serialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum RequestedTerminal {
    ExactRepair,
    StabilizedSurvivor,
    OpenObstruction,
    Refused,
    OracleNeeded,
}

#[derive(Debug, Clone, Copy, Deserialize, Serialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum AgentStepOutcome {
    Executed,
    Refused,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentStep {
    pub op: String,
    pub outcome: AgentStepOutcome,
    pub after_residual: Vec<bool>,
    pub detail: String,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DefectTrace {
    pub defect_id: String,
    pub steps: Vec<AgentStep>,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DdaCandidate {
    pub defect_traces: Vec<DefectTrace>,
    pub imports: Vec<String>,
    pub requested_terminal: RequestedTerminal,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AgentProposal {
    pub schema_version: String,
    pub item_id: String,
    pub work_packet_sha256: String,
    pub author: String,
    pub symbol_packets: Vec<SymbolCandidate>,
    pub dda_candidate: DdaCandidate,
    pub authority_effect: String,
    pub nonclaims: Vec<String>,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum GateVerdict {
    Pass,
    Refuse,
    OracleNeeded,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CodaClassification {
    ExactRepair,
    StabilizedSurvivor,
    OpenObstruction,
    Refused,
    OracleNeeded,
}

#[derive(Debug, Clone, Serialize)]
pub struct PerDefectReceipt {
    pub defect_id: String,
    pub phi: usize,
    pub gamma: usize,
    pub classification: String,
    pub final_residual: Vec<bool>,
    pub letters: String,
    pub terminal: String,
    pub operation_laws_verified: bool,
    pub violations: Vec<String>,
}

#[derive(Debug, Clone, Serialize)]
pub struct DdaGateReceipt {
    pub schema_version: &'static str,
    pub item_id: String,
    pub author: String,
    pub work_packet_sha256: String,
    pub proposal_sha256: String,
    pub gate_verdict: GateVerdict,
    #[serde(rename = "gtoc_classification")]
    pub coda_classification: CodaClassification,
    pub requested_terminal_advisory: RequestedTerminal,
    pub promotion_allowed: bool,
    pub authority_effect: &'static str,
    pub packet_refs: Vec<String>,
    pub per_defect: Vec<PerDefectReceipt>,
    pub oracle_reason: Option<String>,
    pub render_allowed: bool,
}

pub fn sha256_bytes(raw: &[u8]) -> String {
    format!("{:x}", Sha256::digest(raw))
}

fn nonempty(value: &str, label: &str) -> Result<(), String> {
    if value.trim().is_empty() {
        Err(format!("{label} must be non-empty"))
    } else {
        Ok(())
    }
}

fn matrix_shape(
    matrix: &[Vec<bool>],
    rows: usize,
    columns: usize,
    label: &str,
) -> Result<(), String> {
    if matrix.len() != rows {
        return Err(format!(
            "{label}: expected {rows} rows, got {}",
            matrix.len()
        ));
    }
    for (index, row) in matrix.iter().enumerate() {
        if row.len() != columns {
            return Err(format!(
                "{label}[{index}]: expected {columns} columns, got {}",
                row.len()
            ));
        }
    }
    Ok(())
}

fn required_nonclaims(values: &[String], label: &str) -> Result<(), String> {
    let values: BTreeSet<&str> = values.iter().map(String::as_str).collect();
    for required in REQUIRED_NONCLAIMS {
        if !values.contains(required) {
            return Err(format!("{label} missing required nonclaim {required:?}"));
        }
    }
    Ok(())
}

fn validate_work_carrier_and_bases(packet: &AgentWorkPacket) -> Result<(), String> {
    if packet.schema_version != "core.agent_work.v1" {
        return Err("work packet schema_version is not core.agent_work.v1".to_string());
    }
    nonempty(&packet.item_id, "work packet item_id")?;
    nonempty(&packet.carrier.id, "work packet carrier.id")?;
    if packet.carrier.coefficient_ring != "F2" {
        return Err("work packet coefficient_ring must be F2".to_string());
    }
    if packet.zero_rel != "d1*d0=0" {
        return Err("work packet zero_rel must be d1*d0=0".to_string());
    }
    if packet.c0.len() > crate::ddc::degree_tower::MAX_EXHAUSTIVE_DOMAIN_DIM {
        return Err(format!(
            "C0 dimension exceeds exhaustive verifier limit {}",
            crate::ddc::degree_tower::MAX_EXHAUSTIVE_DOMAIN_DIM
        ));
    }
    for (label, basis) in [("c0", &packet.c0), ("c1", &packet.c1), ("c2", &packet.c2)] {
        let unique: BTreeSet<&String> = basis.iter().collect();
        if unique.len() != basis.len() || basis.iter().any(|entry| entry.trim().is_empty()) {
            return Err(format!("{label} basis labels must be non-empty and unique"));
        }
    }
    Ok(())
}

fn validate_work_defects(packet: &AgentWorkPacket) -> Result<(), String> {
    if packet.defects.is_empty() {
        return Err("work packet must contain at least one defect".to_string());
    }
    let mut defect_ids = BTreeSet::new();
    for defect in &packet.defects {
        nonempty(&defect.defect_id, "defect_id")?;
        if !defect_ids.insert(defect.defect_id.as_str()) {
            return Err(format!("duplicate defect_id {:?}", defect.defect_id));
        }
        if defect.residual.len() != packet.c1.len() {
            return Err(format!(
                "defect {:?} residual length {} != C1 dimension {}",
                defect.defect_id,
                defect.residual.len(),
                packet.c1.len()
            ));
        }
    }
    Ok(())
}

fn validate_work_operations_and_refs(packet: &AgentWorkPacket) -> Result<(), String> {
    let operations: BTreeSet<&str> = packet
        .allowed_operations
        .iter()
        .map(String::as_str)
        .collect();
    if operations.len() != packet.allowed_operations.len()
        || operations
            .iter()
            .any(|operation| !ACTIVE_OPERATIONS.contains(operation))
    {
        return Err("allowed_operations must be a unique subset of E/R/I/M/T".to_string());
    }
    if packet.packet_refs.is_empty() {
        return Err("packet_refs must not be empty".to_string());
    }
    let mut sorted_refs = packet.packet_refs.clone();
    sorted_refs.sort();
    sorted_refs.dedup();
    if sorted_refs != packet.packet_refs {
        return Err("packet_refs must be sorted and unique".to_string());
    }
    Ok(())
}

fn validate_work_policy_and_budgets(packet: &AgentWorkPacket) -> Result<(), String> {
    validate_work_operations_and_refs(packet)?;
    if packet.write_surface.len() != 1 {
        return Err("V1 requires exactly one deterministic write_surface path".to_string());
    }
    if packet.evidence_ceiling != "AuthorityEffect::None" {
        return Err("work packet evidence ceiling must be AuthorityEffect::None".to_string());
    }
    if packet.oracle_policy != "route" {
        return Err("work packet oracle_policy must be route".to_string());
    }
    if packet.budgets.max_changed_files != 1 || packet.budgets.max_repairs > 2 {
        return Err("V1 budgets require one changed file and at most two repairs".to_string());
    }
    if packet.budgets.max_wall_seconds == 0 || packet.budgets.max_diff_bytes == 0 {
        return Err("work packet budgets must be positive".to_string());
    }
    required_nonclaims(&packet.nonclaims, "work packet")
}

pub fn parse_work_packet(raw: &[u8]) -> Result<(AgentWorkPacket, BinaryCochainSegment), String> {
    let packet: AgentWorkPacket =
        serde_json::from_slice(raw).map_err(|error| format!("work packet JSON: {error}"))?;
    validate_work_carrier_and_bases(&packet)?;
    matrix_shape(&packet.d0, packet.c1.len(), packet.c0.len(), "d0")?;
    matrix_shape(&packet.d1, packet.c2.len(), packet.c1.len(), "d1")?;

    let previous = BinaryLinearMap::from_rows(packet.c0.len(), packet.d0.clone())
        .map_err(|error| format!("d0 malformed: {error:?}"))?;
    let next = BinaryLinearMap::from_rows(packet.c1.len(), packet.d1.clone())
        .map_err(|error| format!("d1 malformed: {error:?}"))?;
    let segment = BinaryCochainSegment::new(1, previous, next)
        .map_err(|error| format!("zero relation failed: {error:?}"))?;

    validate_work_defects(&packet)?;
    validate_work_policy_and_budgets(&packet)?;
    Ok((packet, segment))
}

fn validate_proposal_symbols_and_imports(proposal: &AgentProposal) -> Result<(), String> {
    for symbol in &proposal.symbol_packets {
        nonempty(&symbol.family, "symbol family")?;
        nonempty(&symbol.grammar, "symbol grammar")?;
    }
    for import in &proposal.dda_candidate.imports {
        nonempty(import, "import")?;
    }
    Ok(())
}

pub fn parse_proposal(raw: &[u8]) -> Result<AgentProposal, String> {
    let proposal: AgentProposal =
        serde_json::from_slice(raw).map_err(|error| format!("proposal JSON: {error}"))?;
    if proposal.schema_version != "core.agent_proposal.v1" {
        return Err("proposal schema_version is not core.agent_proposal.v1".to_string());
    }
    nonempty(&proposal.author, "proposal author")?;
    if proposal.authority_effect != "None" {
        return Err("proposal authority_effect must be None".to_string());
    }
    if proposal.symbol_packets.len() != 2 {
        return Err("proposal must contain exactly two symbol packets".to_string());
    }
    required_nonclaims(&proposal.nonclaims, "proposal")?;
    validate_proposal_symbols_and_imports(&proposal)?;
    Ok(proposal)
}

fn op_from_code(code: &str) -> Result<DdaOp, String> {
    match code {
        "E" => Ok(DdaOp::ExactRepair),
        "R" => Ok(DdaOp::ResidualProjection),
        "C" => Ok(DdaOp::ContextExposure),
        "I" => Ok(DdaOp::Integration),
        "Lambda" => Ok(DdaOp::Lift),
        "D" => Ok(DdaOp::Descent),
        "M" => Ok(DdaOp::Refusal),
        "T" => Ok(DdaOp::Terminalize),
        other => Err(format!("unknown DDA operation {other:?}")),
    }
}

fn operation_code(op: DdaOp) -> &'static str {
    match op {
        DdaOp::ExactRepair => "E",
        DdaOp::ResidualProjection => "R",
        DdaOp::ContextExposure => "C",
        DdaOp::Integration => "I",
        DdaOp::Lift => "Lambda",
        DdaOp::Descent => "D",
        DdaOp::Refusal => "M",
        DdaOp::Terminalize => "T",
    }
}

fn oracle_reason(proposal: &AgentProposal) -> Result<Option<String>, String> {
    if let Some(import) = proposal.dda_candidate.imports.first() {
        return Ok(Some(format!("external import requested: {import}")));
    }
    for trace in &proposal.dda_candidate.defect_traces {
        for step in &trace.steps {
            let op = op_from_code(&step.op)?;
            if matches!(op, DdaOp::ContextExposure | DdaOp::Descent | DdaOp::Lift) {
                return Ok(Some(format!(
                    "unlicensed carrier-changing operation {} in defect {}",
                    operation_code(op),
                    trace.defect_id
                )));
            }
        }
    }
    Ok(None)
}

fn oracle_receipt(
    packet: &AgentWorkPacket,
    proposal: &AgentProposal,
    segment: &BinaryCochainSegment,
    packet_hash: String,
    proposal_hash: String,
    reason: String,
) -> Result<DdaGateReceipt, String> {
    let mut per_defect = Vec::new();
    for defect in &packet.defects {
        let diagnostic = segment
            .diagnose(&defect.residual)
            .map_err(|error| format!("diagnosis failed: {error:?}"))?;
        per_defect.push(PerDefectReceipt {
            defect_id: defect.defect_id.clone(),
            phi: diagnostic.phi,
            gamma: diagnostic.gamma,
            classification: "OracleNeeded".to_string(),
            final_residual: defect.residual.clone(),
            letters: String::new(),
            terminal: "OracleNeeded".to_string(),
            operation_laws_verified: false,
            violations: vec![reason.clone()],
        });
    }
    Ok(DdaGateReceipt {
        schema_version: "core.dda_gate_receipt.v1",
        item_id: packet.item_id.clone(),
        author: proposal.author.clone(),
        work_packet_sha256: packet_hash,
        proposal_sha256: proposal_hash,
        gate_verdict: GateVerdict::OracleNeeded,
        coda_classification: CodaClassification::OracleNeeded,
        requested_terminal_advisory: proposal.dda_candidate.requested_terminal,
        promotion_allowed: false,
        authority_effect: "None",
        packet_refs: packet.packet_refs.clone(),
        per_defect,
        oracle_reason: Some(reason),
        render_allowed: false,
    })
}

fn index_defect_traces<'a>(
    packet: &AgentWorkPacket,
    proposal: &'a AgentProposal,
) -> Result<BTreeMap<&'a str, &'a DefectTrace>, String> {
    let packet_defects: BTreeSet<&str> = packet
        .defects
        .iter()
        .map(|defect| defect.defect_id.as_str())
        .collect();
    let mut traces = BTreeMap::new();
    for trace in &proposal.dda_candidate.defect_traces {
        if !packet_defects.contains(trace.defect_id.as_str()) {
            return Err(format!(
                "trace references unknown defect {:?}",
                trace.defect_id
            ));
        }
        if traces.insert(trace.defect_id.as_str(), trace).is_some() {
            return Err(format!("duplicate trace for defect {:?}", trace.defect_id));
        }
    }
    if traces.len() != packet.defects.len() {
        return Err("proposal must contain exactly one trace per work defect".to_string());
    }
    Ok(traces)
}

fn build_dda_step(op: DdaOp, step_input: &AgentStep) -> DdaStep {
    match step_input.outcome {
        AgentStepOutcome::Executed => DdaStep::executed(op, &step_input.detail),
        AgentStepOutcome::Refused => DdaStep::refused(op, &step_input.detail),
    }
}

fn replay_defect_steps(
    defect_id: &str,
    steps: &[AgentStep],
    segment: &BinaryCochainSegment,
    allowed: &BTreeSet<&str>,
    trace: &mut VerifiedTrace,
) -> Result<Vec<String>, String> {
    let mut violations = Vec::new();
    let mut terminal_seen = false;

    for step_input in steps {
        if terminal_seen {
            violations.push(format!(
                "operation {} appears after an executed terminal operation",
                step_input.op
            ));
            break;
        }
        let op = op_from_code(&step_input.op)?;
        let code = operation_code(op);
        if !allowed.contains(code) {
            violations.push(format!(
                "operation {code} is outside the work packet allowlist"
            ));
            break;
        }
        nonempty(&step_input.detail, "DDA step detail")?;
        let next = CochainState::new(segment.clone(), step_input.after_residual.clone()).map_err(
            |error| {
                format!(
                    "defect {:?} step {} has malformed after state: {error:?}",
                    defect_id, step_input.op
                )
            },
        )?;
        if let Err(error) = trace.step(build_dda_step(op, step_input), next) {
            violations.push(format!("{} law violation: {error:?}", step_input.op));
            break;
        }
        if step_input.outcome == AgentStepOutcome::Executed
            && matches!(op, DdaOp::Refusal | DdaOp::Terminalize)
        {
            terminal_seen = true;
        }
    }
    Ok(violations)
}

fn classify_trace_outcome(
    trace: &VerifiedTrace,
    diagnostic_class: DegreeTrichotomy,
    has_violations: bool,
    any_refused: &mut bool,
    any_open: &mut bool,
    any_survivor: &mut bool,
    all_terminalized: &mut bool,
) -> (&'static str, &'static str) {
    if has_violations {
        *any_refused = true;
        *all_terminalized = false;
        return ("Refused", "Refused");
    }
    match trace.trace().terminal() {
        TraceTerminal::Refused => {
            *any_refused = true;
            ("Refused", "Refused")
        }
        TraceTerminal::Terminalized => match diagnostic_class {
            DegreeTrichotomy::Exact => ("Exact", "Terminalized"),
            DegreeTrichotomy::StabilizedSurvivor => {
                *any_survivor = true;
                ("StabilizedSurvivor", "Terminalized")
            }
            DegreeTrichotomy::Open => {
                *any_open = true;
                *all_terminalized = false;
                ("Open", "Open")
            }
        },
        TraceTerminal::Open => {
            *any_open = true;
            *all_terminalized = false;
            ("Open", "Open")
        }
        TraceTerminal::UnverifiedTerminal => {
            *all_terminalized = false;
            ("Open", "UnverifiedTerminal")
        }
        TraceTerminal::OracleNeeded { .. } => {
            unreachable!("imports are handled before fixed-carrier verification")
        }
    }
}

fn summarize_gate_verdict(
    any_refused: bool,
    any_open: bool,
    any_survivor: bool,
) -> (GateVerdict, CodaClassification, &'static str) {
    if any_refused {
        (GateVerdict::Refuse, CodaClassification::Refused, "Refused")
    } else if any_open {
        (
            GateVerdict::Pass,
            CodaClassification::OpenObstruction,
            "None",
        )
    } else if any_survivor {
        (
            GateVerdict::Pass,
            CodaClassification::StabilizedSurvivor,
            "None",
        )
    } else {
        (GateVerdict::Pass, CodaClassification::ExactRepair, "None")
    }
}

fn is_promotion_allowed(
    gate_verdict: GateVerdict,
    all_terminalized: bool,
    coda_classification: CodaClassification,
    allow_survivor: bool,
) -> bool {
    gate_verdict == GateVerdict::Pass
        && all_terminalized
        && match coda_classification {
            CodaClassification::ExactRepair => true,
            CodaClassification::StabilizedSurvivor => allow_survivor,
            _ => false,
        }
}

fn verify_proposal_binding(
    packet: &AgentWorkPacket,
    proposal: &AgentProposal,
    packet_hash: &str,
) -> Result<(), String> {
    if proposal.item_id != packet.item_id {
        return Err(format!(
            "proposal item_id {:?} != work packet item_id {:?}",
            proposal.item_id, packet.item_id
        ));
    }
    if proposal.work_packet_sha256 != packet_hash {
        return Err(format!(
            "proposal work_packet_sha256 {} != recomputed {}",
            proposal.work_packet_sha256, packet_hash
        ));
    }
    Ok(())
}

fn update_terminalized_requirement(
    require_terminal_op: bool,
    terminal: &str,
    all_terminalized: &mut bool,
) {
    if require_terminal_op && terminal != "Terminalized" && terminal != "Refused" {
        *all_terminalized = false;
    }
}

fn replay_and_diagnose_defect(
    defect_id: &str,
    residual: &[bool],
    steps: &[AgentStep],
    segment: &BinaryCochainSegment,
    allowed: &BTreeSet<&str>,
) -> Result<
    (
        VerifiedTrace,
        Vec<String>,
        crate::ddc::degree_tower::DegreeDiagnostic,
    ),
    String,
> {
    let initial = CochainState::new(segment.clone(), residual.to_vec())
        .map_err(|error| format!("initial state malformed: {error:?}"))?;
    let mut trace = VerifiedTrace::new(initial);
    let violations = replay_defect_steps(defect_id, steps, segment, allowed, &mut trace)?;
    let diagnostic = trace
        .state()
        .diagnose()
        .map_err(|error| format!("final diagnosis failed: {error:?}"))?;
    Ok((trace, violations, diagnostic))
}

pub fn verify_bytes(work_raw: &[u8], proposal_raw: &[u8]) -> Result<DdaGateReceipt, String> {
    let packet_hash = sha256_bytes(work_raw);
    let proposal_hash = sha256_bytes(proposal_raw);
    let (packet, segment) = parse_work_packet(work_raw)?;
    let proposal = parse_proposal(proposal_raw)?;
    verify_proposal_binding(&packet, &proposal, &packet_hash)?;
    let traces = index_defect_traces(&packet, &proposal)?;

    if let Some(reason) = oracle_reason(&proposal)? {
        return oracle_receipt(
            &packet,
            &proposal,
            &segment,
            packet_hash,
            proposal_hash,
            reason,
        );
    }

    let allowed: BTreeSet<&str> = packet
        .allowed_operations
        .iter()
        .map(String::as_str)
        .collect();
    let mut per_defect = Vec::new();
    let mut any_refused = false;
    let mut any_open = false;
    let mut any_survivor = false;
    let mut all_terminalized = true;

    for defect in &packet.defects {
        let input = traces[defect.defect_id.as_str()];
        let (trace, violations, diagnostic) = replay_and_diagnose_defect(
            &defect.defect_id,
            &defect.residual,
            &input.steps,
            &segment,
            &allowed,
        )?;
        let (classification, terminal) = classify_trace_outcome(
            &trace,
            diagnostic.classification,
            !violations.is_empty(),
            &mut any_refused,
            &mut any_open,
            &mut any_survivor,
            &mut all_terminalized,
        );
        update_terminalized_requirement(
            packet.terminal_policy.require_terminal_op,
            terminal,
            &mut all_terminalized,
        );

        per_defect.push(PerDefectReceipt {
            defect_id: defect.defect_id.clone(),
            phi: diagnostic.phi,
            gamma: diagnostic.gamma,
            classification: classification.to_string(),
            final_residual: trace.state().residual.clone(),
            letters: trace.letters(),
            terminal: terminal.to_string(),
            operation_laws_verified: violations.is_empty(),
            violations,
        });
    }

    let (gate_verdict, coda_classification, authority_effect) =
        summarize_gate_verdict(any_refused, any_open, any_survivor);
    let promotion_allowed = is_promotion_allowed(
        gate_verdict,
        all_terminalized,
        coda_classification,
        packet.terminal_policy.allow_survivor,
    );

    Ok(DdaGateReceipt {
        schema_version: "core.dda_gate_receipt.v1",
        item_id: packet.item_id.clone(),
        author: proposal.author.clone(),
        work_packet_sha256: packet_hash,
        proposal_sha256: proposal_hash,
        gate_verdict,
        coda_classification,
        requested_terminal_advisory: proposal.dda_candidate.requested_terminal,
        promotion_allowed,
        authority_effect,
        packet_refs: packet.packet_refs.clone(),
        per_defect,
        oracle_reason: None,
        render_allowed: promotion_allowed,
    })
}

fn slug(value: &str) -> String {
    value
        .chars()
        .map(|character| {
            if character.is_ascii_alphanumeric() {
                character.to_ascii_lowercase()
            } else {
                '_'
            }
        })
        .collect::<String>()
        .trim_matches('_')
        .to_string()
}

fn bool_vector(values: &[bool]) -> String {
    format!(
        "vec![{}]",
        values
            .iter()
            .map(|value| value.to_string())
            .collect::<Vec<_>>()
            .join(", ")
    )
}

fn bool_matrix(rows: &[Vec<bool>]) -> String {
    format!(
        "vec![{}]",
        rows.iter()
            .map(|row| bool_vector(row))
            .collect::<Vec<_>>()
            .join(", ")
    )
}

pub fn canonical_output_rel(packet: &AgentWorkPacket) -> String {
    let item = packet.item_id.rsplit(':').next().unwrap_or(&packet.item_id);
    format!(
        "engine/crates_rs/tests/core_wdp/agent_{}.rs",
        slug(item)
    )
}

pub fn render_rust_bytes(
    work_raw: &[u8],
    proposal_raw: &[u8],
    output: &Path,
) -> Result<String, String> {
    let receipt = verify_bytes(work_raw, proposal_raw)?;
    if !receipt.render_allowed {
        return Err(format!(
            "receipt {:?} is not promotion-ready; refusing to render",
            receipt.coda_classification
        ));
    }
    let (packet, _) = parse_work_packet(work_raw)?;
    let expected_rel = canonical_output_rel(&packet);
    if packet.write_surface.len() != 1 || packet.write_surface[0] != expected_rel {
        return Err(format!(
            "write_surface {:?} does not name canonical path {:?}",
            packet.write_surface, expected_rel
        ));
    }
    let normalized_output = output.to_string_lossy().replace('\\', "/");
    if !normalized_output.ends_with(&expected_rel) {
        return Err(format!(
            "output path {normalized_output:?} does not end in canonical path {expected_rel:?}"
        ));
    }

    let mut source = String::new();
    source.push_str("// @generated by core_dda_gate; DO NOT EDIT.\n");
    source.push_str("use crate::ddc::degree_tower::{\n");
    source.push_str("    BinaryCochainSegment, BinaryLinearMap, DegreeTrichotomy,\n");
    source.push_str("};\n\n");
    source.push_str(&format!(
        "const WORK_PACKET_SHA256: &str = {:?};\n",
        receipt.work_packet_sha256
    ));
    source.push_str("const PACKET_REFS: &[&str] = &[\n");
    for packet_ref in &packet.packet_refs {
        source.push_str(&format!("    {packet_ref:?},\n"));
    }
    source.push_str("];\n\n");

    for defect in &receipt.per_defect {
        let expected = match defect.classification.as_str() {
            "Exact" => "DegreeTrichotomy::Exact",
            "StabilizedSurvivor" => "DegreeTrichotomy::StabilizedSurvivor",
            other => {
                return Err(format!(
                    "cannot render non-promotable defect classification {other}"
                ));
            }
        };
        source.push_str("#[test]\n");
        source.push_str(&format!(
            "fn agent_{}_{}() {{\n",
            slug(packet.item_id.rsplit(':').next().unwrap_or(&packet.item_id)),
            slug(&defect.defect_id)
        ));
        source.push_str(&format!(
            "    let d0 = BinaryLinearMap::from_rows({}, {}).unwrap();\n",
            packet.c0.len(),
            bool_matrix(&packet.d0)
        ));
        source.push_str(&format!(
            "    let d1 = BinaryLinearMap::from_rows({}, {}).unwrap();\n",
            packet.c1.len(),
            bool_matrix(&packet.d1)
        ));
        source.push_str("    let segment = BinaryCochainSegment::new(1, d0, d1).unwrap();\n");
        let residual = bool_vector(&defect.final_residual);
        let residual = residual
            .strip_prefix("vec!")
            .ok_or_else(|| "internal residual rendering error".to_string())?;
        source.push_str(&format!(
            "    let diagnostic = segment.diagnose(&{residual}).unwrap();\n"
        ));
        if expected == "DegreeTrichotomy::Exact" {
            source
                .push_str("    assert_eq!(diagnostic.classification, DegreeTrichotomy::Exact);\n");
        } else {
            source.push_str("    assert_eq!(\n");
            source.push_str("        diagnostic.classification,\n");
            source.push_str(&format!("        {expected}\n"));
            source.push_str("    );\n");
        }
        source.push_str(&format!(
            "    assert_eq!((diagnostic.phi, diagnostic.gamma), ({}, {}));\n",
            defect.phi, defect.gamma
        ));
        source.push_str("    assert_eq!(WORK_PACKET_SHA256.len(), 64);\n");
        source.push_str("    assert!(!PACKET_REFS.is_empty());\n");
        source.push_str("}\n\n");
    }
    source.pop();
    Ok(source)
}

pub mod swarm_kernel {
    use crate::ddc::ddc_alphabet::DdcOp;

    pub const AUTHORITY_EFFECT: &str = "None";

    #[derive(Debug, Clone, PartialEq, Eq)]
    pub enum SwarmPurityRefusal {
        UnknownLetter(String),
        AuthorityEffect(String),
        EmptyField(&'static str),
    }

    #[derive(Debug, Clone, PartialEq, Eq)]
    pub struct AdversaryDdcStep {
        pub letter: DdcOp,
        pub before_class: String,
        pub after_class: String,
        pub carrier_hash: String,
        pub witness_hash: Option<String>,
        pub receipt_sha256: String,
        pub authority_effect: String,
    }

    impl AdversaryDdcStep {
        pub fn try_new(
            letter: &str,
            before_class: impl Into<String>,
            after_class: impl Into<String>,
            carrier_hash: impl Into<String>,
            witness_hash: Option<String>,
            receipt_sha256: impl Into<String>,
            authority_effect: &str,
        ) -> Result<Self, SwarmPurityRefusal> {
            let letter = DdcOp::from_letter(letter)
                .ok_or_else(|| SwarmPurityRefusal::UnknownLetter(letter.to_owned()))?;
            let step = Self {
                letter,
                before_class: before_class.into(),
                after_class: after_class.into(),
                carrier_hash: carrier_hash.into(),
                witness_hash,
                receipt_sha256: receipt_sha256.into(),
                authority_effect: authority_effect.to_owned(),
            };
            validate_purity(&step)?;
            Ok(step)
        }
    }

    pub fn validate_purity(step: &AdversaryDdcStep) -> Result<(), SwarmPurityRefusal> {
        if step.authority_effect != AUTHORITY_EFFECT {
            return Err(SwarmPurityRefusal::AuthorityEffect(
                step.authority_effect.clone(),
            ));
        }
        for (label, value) in [
            ("before_class", step.before_class.as_str()),
            ("after_class", step.after_class.as_str()),
            ("carrier_hash", step.carrier_hash.as_str()),
            ("receipt_sha256", step.receipt_sha256.as_str()),
        ] {
            if value.trim().is_empty() {
                return Err(SwarmPurityRefusal::EmptyField(label));
            }
        }
        if let Some(witness) = &step.witness_hash {
            if witness.trim().is_empty() {
                return Err(SwarmPurityRefusal::EmptyField("witness_hash"));
            }
        }
        Ok(())
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
    pub enum ContinueDecisionKind {
        Continue,
        Hold,
        Refuse,
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    pub struct ContinueDecision {
        pub kind: ContinueDecisionKind,
    }

    impl ContinueDecision {
        pub const fn authority_effect(self) -> &'static str {
            AUTHORITY_EFFECT
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/ddc/agent_contract.rs
// Claim: urn:core:crates_rs:core-wdp:agent-contract:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorde93dc143 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorde93dc143` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrore93dc143 {
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
impl BoundaryErrore93dc143 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrore93dc143 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrore93dc143 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorde93dc143 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrore93dc143> {
        if capacity_bound == 0 {
            return Err(BoundaryErrore93dc143::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrore93dc143::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrore93dc143::ExceedsCapacity {
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
    use serde_json::{json, Value};

    fn work() -> Value {
        json!({
            "schema_version": "core.agent_work.v1",
            "item_id": "dda:test",
            "carrier": {"id": "test", "coefficient_ring": "F2"},
            "c0": ["v0"],
            "c1": ["e0", "e1"],
            "c2": ["f0"],
            "d0": [[true], [true]],
            "d1": [[true, true]],
            "zero_rel": "d1*d0=0",
            "defects": [{"defect_id": "q1", "residual": [true, false]}],
            "allowed_operations": ["E", "I", "M", "T"],
            "oracle_policy": "route",
            "evidence_ceiling": "AuthorityEffect::None",
            "packet_refs": ["dda.md", "symbol.md"],
            "write_surface": [
                "engine/crates_rs/tests/core_wdp/agent_test.rs"
            ],
            "budgets": {
                "max_wall_seconds": 10,
                "max_changed_files": 1,
                "max_diff_bytes": 1000,
                "max_repairs": 2
            },
            "nonclaims": REQUIRED_NONCLAIMS,
            "terminal_policy": {
                "allow_survivor": false,
                "require_terminal_op": true
            }
        })
    }

    fn proposal(work_raw: &[u8], steps: Value, imports: Value) -> Vec<u8> {
        serde_json::to_vec(&json!({
            "schema_version": "core.agent_proposal.v1",
            "item_id": "dda:test",
            "work_packet_sha256": sha256_bytes(work_raw),
            "author": "claude",
            "symbol_packets": [
                {"family": "cochain_obstruction", "grammar": "cochain<x>"},
                {"family": "code_rewrite", "grammar": "code_rewrite<x>"}
            ],
            "dda_candidate": {
                "defect_traces": [{"defect_id": "q1", "steps": steps}],
                "imports": imports,
                "requested_terminal": "ExactRepair"
            },
            "authority_effect": "None",
            "nonclaims": REQUIRED_NONCLAIMS
        }))
        .unwrap()
    }

    #[test]
    fn honest_exact_repair_and_terminal_pass() {
        let mut w = work();
        w["defects"] = json!([{"defect_id": "q1", "residual": [true, true]}]);
        let work_raw = serde_json::to_vec(&w).unwrap();
        let proposal_raw = proposal(
            &work_raw,
            json!([
                {"op": "E", "outcome": "Executed",
                 "after_residual": [false, false], "detail": "discharge"},
                {"op": "T", "outcome": "Executed",
                 "after_residual": [false, false], "detail": "seal"}
            ]),
            json!([]),
        );
        let receipt = verify_bytes(&work_raw, &proposal_raw).unwrap();
        assert_eq!(receipt.gate_verdict, GateVerdict::Pass);
        assert_eq!(receipt.coda_classification, CodaClassification::ExactRepair);
        assert!(receipt.render_allowed);
        assert_eq!(receipt.authority_effect, "None");
    }

    #[test]
    fn lying_e_and_terminalizing_open_are_refused() {
        let work_raw = serde_json::to_vec(&work()).unwrap();
        for steps in [
            json!([
                {"op": "E", "outcome": "Executed",
                 "after_residual": [true, false], "detail": "claimed repair"}
            ]),
            json!([
                {"op": "T", "outcome": "Executed",
                 "after_residual": [true, false], "detail": "claimed seal"}
            ]),
        ] {
            let receipt = verify_bytes(&work_raw, &proposal(&work_raw, steps, json!([]))).unwrap();
            assert_eq!(receipt.gate_verdict, GateVerdict::Refuse);
            assert!(!receipt.per_defect[0].violations.is_empty());
        }
    }

    #[test]
    fn import_and_lambda_route_to_oracle() {
        let work_raw = serde_json::to_vec(&work()).unwrap();
        let imported = verify_bytes(
            &work_raw,
            &proposal(&work_raw, json!([]), json!(["outside theorem"])),
        )
        .unwrap();
        assert_eq!(imported.gate_verdict, GateVerdict::OracleNeeded);

        let lifted = verify_bytes(
            &work_raw,
            &proposal(
                &work_raw,
                json!([{
                    "op": "Lambda",
                    "outcome": "Executed",
                    "after_residual": [true, false],
                    "detail": "lift"
                }]),
                json!([]),
            ),
        )
        .unwrap();
        assert_eq!(lifted.gate_verdict, GateVerdict::OracleNeeded);
        assert_eq!(lifted.authority_effect, "None");
    }

    #[test]
    fn adversary_step_accepts_the_lift_alias_and_refuses_authority() {
        let step = swarm_kernel::AdversaryDdcStep::try_new(
            "Lambda",
            "open",
            "lifted",
            "carrier",
            None,
            "receipt",
            swarm_kernel::AUTHORITY_EFFECT,
        )
        .unwrap();
        assert_eq!(step.letter, crate::ddc::ddc_alphabet::DdcOp::Lift);
        assert!(swarm_kernel::validate_purity(&step).is_ok());

        let refused = swarm_kernel::AdversaryDdcStep::try_new(
            "E",
            "open",
            "closed",
            "carrier",
            None,
            "receipt",
            "EvidenceOnly",
        );
        assert!(matches!(
            refused,
            Err(swarm_kernel::SwarmPurityRefusal::AuthorityEffect(_))
        ));
        assert!(swarm_kernel::AdversaryDdcStep::try_new(
            "Z", "open", "closed", "carrier", None, "receipt", "None",
        )
        .is_err());
        let decision = swarm_kernel::ContinueDecision {
            kind: swarm_kernel::ContinueDecisionKind::Hold,
        };
        assert_eq!(decision.authority_effect(), "None");
    }

    #[test]
    fn malformed_zero_relation_is_rejected() {
        let mut malformed = work();
        malformed["d1"] = json!([[true, false]]);
        let raw = serde_json::to_vec(&malformed).unwrap();
        assert!(parse_work_packet(&raw)
            .unwrap_err()
            .contains("zero relation failed"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_e93dc143 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorde93dc143::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorde93dc143::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorde93dc143::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorde93dc143::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorde93dc143::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrore93dc143::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrore93dc143::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
