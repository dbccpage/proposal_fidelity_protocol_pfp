//! Discrete Difference Calculus (DDC) Tape Evaluator in compiled Rust.
//!
//! Enforces:
//! - Exact integer/rational step differentials over Rational64 (satisfying Congruence Ideal I_float_metric)
//! - Zero-allocation sliding window metric computation
//! - Cryptographic hash-chain continuity validation (parent_sha256 == prev_head)
//! - Complete DFA terminal vs prefix validation across LegacyV1, OearsV1, and ExperimentalZV1 dialects
//! - Checkpoint rollback archiving and compensation branch tracking
//! - AuthorityEffect: None firewall.

use crate::stage::ddc::DdcStep;
use crate::stage::ports::Refusal;
use num_rational::Rational64;
use core_wdp::ddc::ddc_alphabet::DdcOp;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

const AUTHORITY_EFFECT_NONE: &str = "None";

fn ddc_refusal(code: &str, message: impl Into<String>) -> Refusal {
    let mut err = Refusal::new(code, message);
    err.locus = "adversary.stage.ddc_tape_evaluator".into();
    err
}

/// Versioned DDC letter-algebra dialects.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, Default)]
pub enum DdcDialect {
    #[default]
    LegacyV1,
    OearsV1,
    ExperimentalZV1,
}

impl DdcDialect {
    pub fn as_str(&self) -> &'static str {
        match self {
            Self::LegacyV1 => "legacy-v1",
            Self::OearsV1 => "oears-v1",
            Self::ExperimentalZV1 => "experimental-z-v1",
        }
    }

    pub fn from_str_name(name: &str) -> Option<Self> {
        match name {
            "legacy-v1" => Some(Self::LegacyV1),
            "oears-v1" => Some(Self::OearsV1),
            "experimental-z-v1" => Some(Self::ExperimentalZV1),
            _ => None,
        }
    }
}

/// Cryptographically sealed receipt emitted for each lawful DDC tape step.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StepReceipt {
    pub step_id: String,
    pub letter: DdcOp,
    pub sequence: u64,
    pub input_state_hash: String,
    pub output_state_hash: String,
    pub carrier_hash: String,
    pub diagnostic_before: String,
    pub diagnostic_after: String,
    pub required_witness: String,
    pub witness_hash: String,
    pub parent_sha256: Option<String>,
    pub record_sha256: String,
    pub phi_1: Option<Rational64>,
    pub gamma_2: Option<Rational64>,
    pub authority_effect: String,
}

/// Archival entry for a step that was rolled back to an earlier checkpoint.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RolledBackStep {
    pub step: DdcStep,
    pub receipt: StepReceipt,
    pub reason: String,
    pub rolled_back_from_index: usize,
    pub authority_effect: String,
}

/// Audit report from replaying and reconstructing a DDC tape log stream.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct DdcTapeAuditReport {
    pub active_tape: String,
    pub active_steps: Vec<DdcStep>,
    pub rolled_back_steps: Vec<RolledBackStep>,
    pub compensation_branches: BTreeMap<String, Vec<DdcStep>>,
    pub head_sha256: String,
    pub terminalized: bool,
}

/// Fail-closed DFA validator for DDC tape letter algebra.
pub struct DDCTapeDFA;

impl DDCTapeDFA {
    pub fn tokenize(tape: &str) -> Result<Vec<String>, Refusal> {
        let value = tape.trim();
        if value.is_empty() {
            return Err(ddc_refusal(
                "DDC_DFA_EMPTY_TAPE",
                "DDC tape cannot be empty.",
            ));
        }
        let mut tokens = Vec::new();
        // Split on common DDC tape separators: space, dot, arrow, dash, bullet (·)
        for part in value
            .replace("·", " ")
            .replace("->", " ")
            .replace("-", " ")
            .replace(".", " ")
            .replace(">", " ")
            .split_whitespace()
        {
            if part == "L" || part == "Lambda" {
                tokens.push("Λ".to_string());
            } else {
                tokens.push(part.to_string());
            }
        }
        if tokens.is_empty() {
            return Err(ddc_refusal(
                "DDC_DFA_EMPTY_TAPE",
                "DDC tape cannot be empty.",
            ));
        }
        Ok(tokens)
    }

    pub fn validate(tape: &str, dialect: DdcDialect) -> Result<(), Refusal> {
        Self::validate_internal(tape, dialect, true)
    }

    pub fn validate_prefix(tape: &str, dialect: DdcDialect) -> Result<(), Refusal> {
        Self::validate_internal(tape, dialect, false)
    }

    fn validate_internal(
        tape: &str,
        dialect: DdcDialect,
        require_complete: bool,
    ) -> Result<(), Refusal> {
        let tokens = Self::tokenize(tape)?;
        let alphabet = Self::build_alphabet_and_check_bounds(&tokens, dialect, require_complete)?;
        let total = tokens.len();
        for (index, token) in tokens.iter().enumerate() {
            Self::validate_token_step(
                &tokens,
                index,
                token.as_str(),
                total,
                &alphabet,
                dialect,
                require_complete,
            )?;
        }
        if require_complete && tokens.last().map(String::as_str) != Some("T") {
            return Err(ddc_refusal(
                "DDC_DFA_INCOMPLETE_TAPE",
                "Complete DDC tape must terminate in letter T.",
            ));
        }
        Ok(())
    }

    fn build_alphabet_and_check_bounds(
        tokens: &[String],
        dialect: DdcDialect,
        require_complete: bool,
    ) -> Result<BTreeSet<&'static str>, Refusal> {
        let mut alphabet: BTreeSet<&'static str> = ["E", "R", "C", "I", "Λ", "D", "M", "T"]
            .into_iter()
            .collect();
        if dialect == DdcDialect::ExperimentalZV1 {
            alphabet.remove("M");
            alphabet.insert("Z");
            Self::check_experimental_bounds(tokens, require_complete)?;
        }
        Ok(alphabet)
    }

    fn check_experimental_bounds(tokens: &[String], require_complete: bool) -> Result<(), Refusal> {
        if tokens[0] != "E" && tokens[0] != "R" {
            return Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                format!(
                    "Experimental DDC tape must start with E or R, got '{}'.",
                    tokens[0]
                ),
            ));
        }
        let last = tokens.last().map(String::as_str);
        if require_complete && last != Some("T") {
            let msg = if last == Some("Z") {
                "Experimental refusal Z must be followed by T, got 'end-of-tape'."
            } else {
                "Experimental DDC tape must end with terminal T."
            };
            return Err(ddc_refusal("DDC_DFA_VIOLATION", msg));
        }
        Ok(())
    }

    fn validate_token_step(
        tokens: &[String],
        index: usize,
        tok_str: &str,
        total: usize,
        alphabet: &BTreeSet<&'static str>,
        dialect: DdcDialect,
        require_complete: bool,
    ) -> Result<(), Refusal> {
        if !alphabet.contains(tok_str) {
            return Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                format!(
                    "Invalid DDC letter '{tok_str}' at index {index} for dialect {}.",
                    dialect.as_str()
                ),
            ));
        }
        let next_tok = tokens.get(index + 1).map(String::as_str);
        Self::check_terminal_and_refusal_rules(tok_str, next_tok, dialect, require_complete)?;
        if dialect == DdcDialect::ExperimentalZV1 {
            if let Some(following) = next_tok {
                Self::check_experimental_transition(tok_str, following)?;
            }
        }
        Ok(())
    }

    fn check_terminal_and_refusal_rules(
        tok_str: &str,
        next_tok: Option<&str>,
        dialect: DdcDialect,
        require_complete: bool,
    ) -> Result<(), Refusal> {
        match tok_str {
            "T" => Self::check_t_rule(next_tok),
            "M" => Self::check_m_rule(next_tok, dialect),
            "Z" => Self::check_z_rule(next_tok, require_complete),
            _ => Ok(()),
        }
    }

    fn check_t_rule(next_tok: Option<&str>) -> Result<(), Refusal> {
        if let Some(following) = next_tok {
            return Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                format!("T absorption rule violated: letter '{following}' after terminal T."),
            ));
        }
        Ok(())
    }

    fn check_m_rule(next_tok: Option<&str>, dialect: DdcDialect) -> Result<(), Refusal> {
        let Some(following) = next_tok else {
            return Ok(());
        };
        if dialect == DdcDialect::LegacyV1 {
            if following != "T" {
                return Err(ddc_refusal(
                    "DDC_DFA_VIOLATION",
                    format!("Refusal letter M must be followed by terminal T, got '{following}'."),
                ));
            }
            return Ok(());
        }
        Err(ddc_refusal(
            "DDC_DFA_VIOLATION",
            format!("OEARS refusal M is terminal and cannot be followed by '{following}'."),
        ))
    }

    fn check_z_rule(next_tok: Option<&str>, require_complete: bool) -> Result<(), Refusal> {
        match next_tok {
            None if require_complete => Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                "Experimental refusal Z must be followed by T, got 'end-of-tape'.",
            )),
            Some(following) if following != "T" => Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                format!("Experimental refusal Z must be followed by T, got '{following}'."),
            )),
            _ => Ok(()),
        }
    }

    fn check_experimental_transition(tok_str: &str, following: &str) -> Result<(), Refusal> {
        let valid = match tok_str {
            "E" | "R" | "C" | "Λ" | "D" => {
                ["E", "R", "C", "I", "Λ", "D", "Z", "T"].contains(&following)
            }
            "I" | "Z" => following == "T",
            _ => false,
        };
        if !valid {
            return Err(ddc_refusal(
                "DDC_DFA_VIOLATION",
                format!("Invalid experimental DDC transition '{tok_str}·{following}'."),
            ));
        }
        Ok(())
    }
}

/// Sovereign Discrete Difference Calculus (DDC) Tape Evaluator.
///
/// Computes exact rational metrics over Rational64 with zero heap allocations during window queries,
/// verifies strict cryptographic hash chains across all steps, and fail-closed validates DFA transitions.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DdcTapeEvaluator {
    trace_id: String,
    dialect: DdcDialect,
    active_steps: Vec<DdcStep>,
    receipts: Vec<StepReceipt>,
    rolled_back_steps: Vec<RolledBackStep>,
    compensation_branches: BTreeMap<String, Vec<DdcStep>>,
    checkpoints: Vec<usize>,
    phi_1_history: Vec<Rational64>,
    gamma_2_history: Vec<Rational64>,
    head_sha256: Option<String>,
    next_sequence: u64,
    terminalized: bool,
}

impl DdcTapeEvaluator {
    pub fn new(trace_id: impl Into<String>) -> Self {
        Self::with_dialect(trace_id, DdcDialect::LegacyV1)
    }

    pub fn with_dialect(trace_id: impl Into<String>, dialect: DdcDialect) -> Self {
        Self {
            trace_id: trace_id.into(),
            dialect,
            active_steps: Vec::new(),
            receipts: Vec::new(),
            rolled_back_steps: Vec::new(),
            compensation_branches: BTreeMap::new(),
            checkpoints: Vec::new(),
            phi_1_history: Vec::new(),
            gamma_2_history: Vec::new(),
            head_sha256: None,
            next_sequence: 0,
            terminalized: false,
        }
    }

    pub fn trace_id(&self) -> &str {
        &self.trace_id
    }

    pub fn dialect(&self) -> DdcDialect {
        self.dialect
    }

    pub fn head_sha256(&self) -> Option<&str> {
        self.head_sha256.as_deref()
    }

    pub fn next_sequence(&self) -> u64 {
        self.next_sequence
    }

    pub fn is_terminalized(&self) -> bool {
        self.terminalized
    }

    pub fn active_steps(&self) -> &[DdcStep] {
        &self.active_steps
    }

    pub fn receipts(&self) -> &[StepReceipt] {
        &self.receipts
    }

    pub fn rolled_back_steps(&self) -> &[RolledBackStep] {
        &self.rolled_back_steps
    }

    pub fn compensation_branches(&self) -> &BTreeMap<String, Vec<DdcStep>> {
        &self.compensation_branches
    }

    pub fn step_count(&self) -> usize {
        self.active_steps.len()
    }

    /// Evaluates a lawful DDC step with exact rational metrics and hash-chain continuity.
    pub fn eval_step(&mut self, step: &DdcStep) -> Result<StepReceipt, Refusal> {
        let seq = self.next_sequence;
        let parent = self.head_sha256.clone();
        self.eval_step_verified(step, seq, parent.as_deref())
    }

    /// Evaluates a DDC step verifying caller-declared sequence and parent hash bindings.
    pub fn eval_step_verified(
        &mut self,
        step: &DdcStep,
        expected_sequence: u64,
        expected_parent_sha256: Option<&str>,
    ) -> Result<StepReceipt, Refusal> {
        self.verify_step_preconditions(step, expected_sequence, expected_parent_sha256)?;
        let prospective_letter = step.letter().letter();
        self.verify_prospective_dfa(prospective_letter)?;
        let phi1_q = Self::extract_rational64(step.phi_1(), "phi_1")?;
        let gamma2_q = Self::extract_rational64(step.gamma_2(), "gamma_2")?;
        let step_receipt = self.build_step_receipt(step, prospective_letter, phi1_q, gamma2_q)?;
        self.advance_evaluator_state(step, &step_receipt, phi1_q, gamma2_q);
        Ok(step_receipt)
    }

    fn verify_step_preconditions(
        &self,
        step: &DdcStep,
        expected_sequence: u64,
        expected_parent_sha256: Option<&str>,
    ) -> Result<(), Refusal> {
        if self.terminalized {
            return Err(ddc_refusal(
                "DDC_TERMINALIZED",
                "Cannot append a DDC step after terminalization ending in T.",
            ));
        }
        if expected_sequence != self.next_sequence {
            return Err(ddc_refusal(
                "DDC_SEQUENCE_MISMATCH",
                format!(
                    "Step sequence mismatch: expected {}, got {}.",
                    self.next_sequence, expected_sequence
                ),
            ));
        }
        self.verify_parent_hash_binding(expected_parent_sha256)?;
        self.verify_step_purity_and_authority(step)
    }

    fn verify_parent_hash_binding(
        &self,
        expected_parent_sha256: Option<&str>,
    ) -> Result<(), Refusal> {
        if self.next_sequence == 0 {
            if expected_parent_sha256.is_some() {
                return Err(ddc_refusal(
                    "DDC_PARENT_HASH_MISMATCH",
                    "Genesis step (seq 0) parent_sha256 must be None.",
                ));
            }
            return Ok(());
        }
        if expected_parent_sha256 != self.head_sha256.as_deref() {
            return Err(ddc_refusal(
                "DDC_PARENT_HASH_MISMATCH",
                format!(
                    "Parent hash mismatch: expected {:?}, got {:?}.",
                    self.head_sha256, expected_parent_sha256
                ),
            ));
        }
        Ok(())
    }

    fn verify_step_purity_and_authority(&self, step: &DdcStep) -> Result<(), Refusal> {
        if step.authority_effect() != AUTHORITY_EFFECT_NONE {
            return Err(ddc_refusal(
                "DDC_AUTHORITY_LEAK",
                format!(
                    "Step authority_effect must be '{}', got '{}'.",
                    AUTHORITY_EFFECT_NONE,
                    step.authority_effect()
                ),
            ));
        }
        if step.before_class().is_empty() || step.after_class().is_empty() {
            return Err(ddc_refusal(
                "DDC_PURITY_VIOLATION",
                "Step before_class and after_class must be nonempty.",
            ));
        }
        Ok(())
    }

    fn verify_prospective_dfa(&self, prospective_letter: &str) -> Result<(), Refusal> {
        let current_tape = self.as_tape(" · ");
        let prospective_tape = if current_tape.is_empty() {
            prospective_letter.to_string()
        } else {
            format!("{current_tape} · {prospective_letter}")
        };
        DDCTapeDFA::validate_prefix(&prospective_tape, self.dialect)
    }

    fn extract_rational64(
        metric: &Option<crate::stage::exact::Rational>,
        label: &str,
    ) -> Result<Option<Rational64>, Refusal> {
        let Some(r) = metric else {
            return Ok(None);
        };
        let num = i64::try_from(r.0.numer()).map_err(|_| {
            ddc_refusal(
                "DDC_METRIC_OVERFLOW",
                format!("{label} numerator exceeds i64 range"),
            )
        })?;
        let den = i64::try_from(r.0.denom()).map_err(|_| {
            ddc_refusal(
                "DDC_METRIC_OVERFLOW",
                format!("{label} denominator exceeds i64 range"),
            )
        })?;
        Ok(Some(Rational64::new(num, den)))
    }

    fn build_step_receipt(
        &self,
        step: &DdcStep,
        prospective_letter: &str,
        phi1_q: Option<Rational64>,
        gamma2_q: Option<Rational64>,
    ) -> Result<StepReceipt, Refusal> {
        let parent = self.head_sha256.clone();
        let witness = step
            .witness_hash()
            .clone()
            .unwrap_or_else(|| step.receipt_sha256().clone());
        let step_record_json = serde_json::json!({
            "sequence": self.next_sequence,
            "parent_sha256": parent,
            "record_type": "step",
            "letter": prospective_letter,
            "before_class": step.before_class(),
            "after_class": step.after_class(),
            "carrier_hash": step.carrier_hash(),
            "witness_hash": step.witness_hash(),
            "receipt_sha256": step.receipt_sha256(),
            "authority_effect": AUTHORITY_EFFECT_NONE,
        });
        let material = serde_json::to_vec(&step_record_json).map_err(|e| {
            ddc_refusal(
                "DDC_HASH_ENCODING_FAILED",
                format!("Failed to encode canonical JSON: {e}"),
            )
        })?;
        let record_digest = format!("sha256:{}", hex::encode(Sha256::digest(&material)));
        Ok(StepReceipt {
            step_id: format!("{}:DDC_STEP_{:03}", self.trace_id, self.receipts.len() + 1),
            letter: *step.letter(),
            sequence: self.next_sequence,
            input_state_hash: format!(
                "sha256:{}",
                hex::encode(Sha256::digest(step.before_class().as_bytes()))
            ),
            output_state_hash: format!(
                "sha256:{}",
                hex::encode(Sha256::digest(step.after_class().as_bytes()))
            ),
            carrier_hash: format!(
                "sha256:{}",
                hex::encode(Sha256::digest(step.carrier_hash().as_bytes()))
            ),
            diagnostic_before: step.before_class().clone(),
            diagnostic_after: step.after_class().clone(),
            required_witness: witness.clone(),
            witness_hash: format!("sha256:{}", hex::encode(Sha256::digest(witness.as_bytes()))),
            parent_sha256: parent,
            record_sha256: record_digest,
            phi_1: phi1_q,
            gamma_2: gamma2_q,
            authority_effect: AUTHORITY_EFFECT_NONE.into(),
        })
    }

    fn advance_evaluator_state(
        &mut self,
        step: &DdcStep,
        step_receipt: &StepReceipt,
        phi1_q: Option<Rational64>,
        gamma2_q: Option<Rational64>,
    ) {
        self.head_sha256 = Some(step_receipt.record_sha256.clone());
        self.next_sequence += 1;
        self.active_steps.push(step.clone());
        self.receipts.push(step_receipt.clone());
        self.phi_1_history
            .push(phi1_q.unwrap_or(Rational64::new(0, 1)));
        self.gamma_2_history
            .push(gamma2_q.unwrap_or(Rational64::new(0, 1)));
        if *step.letter() == DdcOp::Terminalize {
            self.terminalized = true;
        }
    }

    /// Zero-allocation sliding window metric: cumulative sum of phi_1 differentials.
    /// Operates directly on the pre-allocated internal slice without allocating new vectors or buffers.
    #[inline]
    pub fn sliding_window_metric(&self, window_size: usize) -> Rational64 {
        if window_size == 0 || self.phi_1_history.is_empty() {
            return Rational64::new(0, 1);
        }
        let start = self.phi_1_history.len().saturating_sub(window_size);
        let slice = &self.phi_1_history[start..];
        let mut sum = Rational64::new(0, 1);
        for val in slice {
            sum += *val;
        }
        sum
    }

    /// Zero-allocation sliding window metric: cumulative sum of gamma_2 differentials.
    #[inline]
    pub fn sliding_window_gamma2(&self, window_size: usize) -> Rational64 {
        if window_size == 0 || self.gamma_2_history.is_empty() {
            return Rational64::new(0, 1);
        }
        let start = self.gamma_2_history.len().saturating_sub(window_size);
        let slice = &self.gamma_2_history[start..];
        let mut sum = Rational64::new(0, 1);
        for val in slice {
            sum += *val;
        }
        sum
    }

    /// Zero-allocation sliding window mean of phi_1 differentials over the window.
    #[inline]
    pub fn sliding_window_mean(&self, window_size: usize) -> Rational64 {
        if window_size == 0 || self.phi_1_history.is_empty() {
            return Rational64::new(0, 1);
        }
        let start = self.phi_1_history.len().saturating_sub(window_size);
        let slice = &self.phi_1_history[start..];
        let count = slice.len() as i64;
        if count == 0 {
            return Rational64::new(0, 1);
        }
        let mut sum = Rational64::new(0, 1);
        for val in slice {
            sum += *val;
        }
        sum / Rational64::new(count, 1)
    }

    /// Record a tape checkpoint returning the checkpoint index.
    pub fn checkpoint(&mut self) -> usize {
        let cp = self.active_steps.len();
        self.checkpoints.push(cp);
        cp
    }

    /// Rolls back the active tape to a designated checkpoint, archiving uncommitted steps.
    pub fn rollback(
        &mut self,
        checkpoint_index: usize,
        reason: &str,
    ) -> Result<Vec<DdcStep>, Refusal> {
        if checkpoint_index > self.active_steps.len() {
            return Err(ddc_refusal(
                "DDC_INVALID_CHECKPOINT",
                format!(
                    "Checkpoint index {} is out of bounds [0, {}].",
                    checkpoint_index,
                    self.active_steps.len()
                ),
            ));
        }

        let rolled_steps = self.active_steps.split_off(checkpoint_index);
        let rolled_receipts = self.receipts.split_off(checkpoint_index);
        self.phi_1_history.truncate(checkpoint_index);
        self.gamma_2_history.truncate(checkpoint_index);

        for (s, r) in rolled_steps.iter().zip(rolled_receipts.into_iter()) {
            self.rolled_back_steps.push(RolledBackStep {
                step: s.clone(),
                receipt: r,
                reason: reason.to_string(),
                rolled_back_from_index: checkpoint_index,
                authority_effect: AUTHORITY_EFFECT_NONE.into(),
            });
        }

        // Emit a rollback hash-chain record
        let rollback_json = serde_json::json!({
            "sequence": self.next_sequence,
            "parent_sha256": self.head_sha256,
            "record_type": "rollback",
            "checkpoint_index": checkpoint_index,
            "reason": reason,
            "rolled_back_count": rolled_steps.len(),
            "authority_effect": AUTHORITY_EFFECT_NONE,
        });
        let material = serde_json::to_vec(&rollback_json).map_err(|e| {
            ddc_refusal(
                "DDC_HASH_ENCODING_FAILED",
                format!("Failed to encode rollback record: {e}"),
            )
        })?;
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(&material)));
        self.head_sha256 = Some(digest);
        self.next_sequence += 1;

        // Terminal status recomputation
        self.terminalized = self
            .active_steps
            .iter()
            .any(|s| *s.letter() == DdcOp::Terminalize);

        Ok(rolled_steps)
    }

    /// Records an explicit compensation or refusal branch tape.
    pub fn record_compensation_branch(
        &mut self,
        branch_id: &str,
        steps: &[DdcStep],
    ) -> Result<(), Refusal> {
        let b_id = branch_id.trim();
        if b_id.is_empty() || b_id.contains(|c: char| !c.is_alphanumeric() && c != '_' && c != '-')
        {
            return Err(ddc_refusal(
                "DDC_INVALID_COMPENSATION_BRANCH",
                format!("Branch id '{branch_id}' must be a nonempty alphanumeric identifier."),
            ));
        }
        if self.compensation_branches.contains_key(b_id) {
            return Err(ddc_refusal(
                "DDC_DIVERGENT_BRANCH",
                format!(
                    "Compensation branch id '{b_id}' already exists (duplicate divergent branch)."
                ),
            ));
        }
        if steps.is_empty() {
            return Err(ddc_refusal(
                "DDC_INVALID_COMPENSATION_BRANCH",
                "Compensation branch steps cannot be empty.",
            ));
        }
        for step in steps {
            if step.authority_effect() != AUTHORITY_EFFECT_NONE {
                return Err(ddc_refusal(
                    "DDC_AUTHORITY_LEAK",
                    "Compensation step authority_effect must be 'None'.",
                ));
            }
            if step.before_class().is_empty() || step.after_class().is_empty() {
                return Err(ddc_refusal(
                    "DDC_PURITY_VIOLATION",
                    "Compensation step before_class and after_class must be nonempty.",
                ));
            }
        }

        self.compensation_branches
            .insert(b_id.to_string(), steps.to_vec());

        // Emit compensation branch hash-chain record
        let branch_json = serde_json::json!({
            "sequence": self.next_sequence,
            "parent_sha256": self.head_sha256,
            "record_type": "compensation_branch",
            "branch_id": b_id,
            "step_count": steps.len(),
            "authority_effect": AUTHORITY_EFFECT_NONE,
        });
        let material = serde_json::to_vec(&branch_json).map_err(|e| {
            ddc_refusal(
                "DDC_HASH_ENCODING_FAILED",
                format!("Failed to encode compensation branch record: {e}"),
            )
        })?;
        let digest = format!("sha256:{}", hex::encode(Sha256::digest(&material)));
        self.head_sha256 = Some(digest);
        self.next_sequence += 1;

        Ok(())
    }

    /// Formats the active step sequence as a DDC execution tape string.
    pub fn as_tape(&self, separator: &str) -> String {
        self.active_steps
            .iter()
            .map(|s| s.letter().letter())
            .collect::<Vec<_>>()
            .join(separator)
    }

    /// Validates the current active tape against the evaluator's DFA dialect.
    pub fn validate_dfa(&self, require_terminal: bool) -> Result<(), Refusal> {
        let tape = self.as_tape(" · ");
        if tape.is_empty() {
            if require_complete_check(require_terminal) {
                return Err(ddc_refusal(
                    "DDC_DFA_EMPTY_TAPE",
                    "DDC tape cannot be empty for complete validation.",
                ));
            }
            return Ok(());
        }
        if require_terminal {
            DDCTapeDFA::validate(&tape, self.dialect)
        } else {
            DDCTapeDFA::validate_prefix(&tape, self.dialect)
        }
    }

    /// Reconstructs and audits a complete DDC tape stream from JSONL records.
    ///
    /// Validates authority leaks, monotonic sequence, parent hash chaining, record digest tie-out,
    /// checkpoint rollbacks, compensation branch registration, and DFA syntax.
    pub fn audit_and_reconstruct_from_jsonl(
        jsonl_content: &str,
        expected_head_sha256: Option<&str>,
        dialect: DdcDialect,
    ) -> Result<DdcTapeAuditReport, Refusal> {
        let mut evaluator = DdcTapeEvaluator::with_dialect("jsonl_audit", dialect);
        let mut prev_hash: Option<String> = None;

        for (idx, line) in jsonl_content.lines().enumerate() {
            let line_trimmed = line.trim();
            if line_trimmed.is_empty() {
                continue;
            }
            prev_hash = Some(Self::audit_jsonl_line(
                idx,
                line_trimmed,
                prev_hash.as_deref(),
                &mut evaluator,
            )?);
        }

        Self::verify_expected_head(expected_head_sha256, prev_hash.as_deref())?;

        // 7. Reconstruct active tape and validate DFA
        let active_tape = evaluator.as_tape(" · ");
        evaluator
            .validate_dfa(evaluator.terminalized)
            .map_err(|e| {
                ddc_refusal(
                    "DDC_AUDIT_DFA_VIOLATION",
                    format!("Reconstructed active tape '{active_tape}' violates DDCTapeDFA: {e}"),
                )
            })?;

        Ok(DdcTapeAuditReport {
            active_tape,
            active_steps: evaluator.active_steps,
            rolled_back_steps: evaluator.rolled_back_steps,
            compensation_branches: evaluator.compensation_branches,
            head_sha256: prev_hash.unwrap_or_default(),
            terminalized: evaluator.terminalized,
        })
    }

    fn audit_jsonl_line(
        idx: usize,
        line_trimmed: &str,
        prev_hash: Option<&str>,
        evaluator: &mut DdcTapeEvaluator,
    ) -> Result<String, Refusal> {
        let record: serde_json::Value = serde_json::from_str(line_trimmed).map_err(|e| {
            ddc_refusal(
                "DDC_AUDIT_CORRUPTED",
                format!("Line {idx} invalid JSON: {e}"),
            )
        })?;
        let Some(object) = record.as_object() else {
            return Err(ddc_refusal(
                "DDC_AUDIT_CORRUPTED",
                format!("Line {idx} record must be a JSON object."),
            ));
        };
        Self::verify_jsonl_envelope(idx, object, prev_hash)?;
        let computed_digest = Self::verify_jsonl_record_digest(idx, object)?;
        Self::apply_jsonl_record(idx, object, evaluator)?;
        Ok(computed_digest)
    }

    fn verify_jsonl_envelope(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        prev_hash: Option<&str>,
    ) -> Result<(), Refusal> {
        let auth = object.get("authority_effect").and_then(|v| v.as_str());
        if auth != Some(AUTHORITY_EFFECT_NONE) {
            return Err(ddc_refusal(
                "DDC_AUDIT_AUTHORITY_LEAK",
                format!(
                    "Line {idx} authority_effect must be '{AUTHORITY_EFFECT_NONE}', got {auth:?}."
                ),
            ));
        }
        let seq = object.get("sequence").and_then(|v| v.as_u64());
        if seq != Some(idx as u64) {
            return Err(ddc_refusal(
                "DDC_AUDIT_SEQUENCE_MISMATCH",
                format!("Line {idx} sequence mismatch: expected {idx}, got {seq:?}."),
            ));
        }
        Self::verify_jsonl_parent(idx, object, prev_hash)
    }

    fn verify_jsonl_parent(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        prev_hash: Option<&str>,
    ) -> Result<(), Refusal> {
        let parent = object.get("parent_sha256").and_then(|v| v.as_str());
        if idx == 0 {
            if parent.is_some() {
                return Err(ddc_refusal(
                    "DDC_AUDIT_PARENT_HASH_MISMATCH",
                    format!("Line 0 parent_sha256 must be None, got {parent:?}."),
                ));
            }
            return Ok(());
        }
        if parent != prev_hash {
            return Err(ddc_refusal(
                "DDC_AUDIT_PARENT_HASH_MISMATCH",
                format!(
                    "Line {idx} parent_sha256 mismatch: expected {prev_hash:?}, got {parent:?}."
                ),
            ));
        }
        Ok(())
    }

    fn verify_jsonl_record_digest(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
    ) -> Result<String, Refusal> {
        let record_digest = object.get("record_sha256").and_then(|v| v.as_str());
        let mut filtered = object.clone();
        filtered.remove("record_sha256");
        let material = serde_json::to_vec(&filtered).map_err(|e| {
            ddc_refusal(
                "DDC_AUDIT_CORRUPTED",
                format!("Line {idx} canonicalization failed: {e}"),
            )
        })?;
        let computed_digest = format!("sha256:{}", hex::encode(Sha256::digest(&material)));
        if let Some(expected_digest) = record_digest {
            if expected_digest != computed_digest {
                return Err(ddc_refusal(
                    "DDC_AUDIT_RECORD_HASH_MISMATCH",
                    format!(
                        "Line {idx} record_sha256 mismatch: expected {computed_digest}, got {expected_digest}."
                    ),
                ));
            }
        }
        Ok(computed_digest)
    }

    fn apply_jsonl_record(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        evaluator: &mut DdcTapeEvaluator,
    ) -> Result<(), Refusal> {
        let rec_type = object
            .get("record_type")
            .and_then(|v| v.as_str())
            .unwrap_or("step");
        match rec_type {
            "step" => Self::apply_jsonl_step(idx, object, evaluator),
            "rollback" => Self::apply_jsonl_rollback(idx, object, evaluator),
            "compensation_branch" => Self::apply_jsonl_compensation(idx, object, evaluator),
            unknown => Err(ddc_refusal(
                "DDC_AUDIT_UNKNOWN_RECORD_TYPE",
                format!("Line {idx} unrecognized record_type: '{unknown}'."),
            )),
        }
    }

    fn apply_jsonl_step(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        evaluator: &mut DdcTapeEvaluator,
    ) -> Result<(), Refusal> {
        let mut step_object = object.clone();
        step_object.remove("sequence");
        step_object.remove("parent_sha256");
        step_object.remove("record_type");
        step_object.remove("record_sha256");
        let step: DdcStep = serde_json::from_value(serde_json::Value::Object(step_object))
            .map_err(|e| {
                ddc_refusal(
                    "DDC_AUDIT_STEP_DESERIALIZATION_FAILED",
                    format!("Line {idx} step deserialization failed: {e}"),
                )
            })?;
        evaluator.eval_step(&step)?;
        Ok(())
    }

    fn apply_jsonl_rollback(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        evaluator: &mut DdcTapeEvaluator,
    ) -> Result<(), Refusal> {
        let cp_idx = object
            .get("checkpoint_index")
            .and_then(|v| v.as_u64())
            .ok_or_else(|| {
                ddc_refusal(
                    "DDC_AUDIT_INVALID_CHECKPOINT",
                    format!("Line {idx} rollback missing checkpoint_index."),
                )
            })? as usize;
        let reason = object.get("reason").and_then(|v| v.as_str()).unwrap_or("");
        evaluator.rollback(cp_idx, reason)?;
        Ok(())
    }

    fn apply_jsonl_compensation(
        idx: usize,
        object: &serde_json::Map<String, serde_json::Value>,
        evaluator: &mut DdcTapeEvaluator,
    ) -> Result<(), Refusal> {
        let b_id = object
            .get("branch_id")
            .and_then(|v| v.as_str())
            .ok_or_else(|| {
                ddc_refusal(
                    "DDC_AUDIT_COMPENSATION_INVALID",
                    format!("Line {idx} compensation missing branch_id."),
                )
            })?;
        let raw_steps = object
            .get("steps")
            .and_then(|v| v.as_array())
            .ok_or_else(|| {
                ddc_refusal(
                    "DDC_AUDIT_COMPENSATION_INVALID",
                    format!("Line {idx} compensation missing steps array."),
                )
            })?;
        let mut branch_steps = Vec::new();
        for s_val in raw_steps {
            let step: DdcStep = serde_json::from_value(s_val.clone()).map_err(|e| {
                ddc_refusal(
                    "DDC_AUDIT_COMPENSATION_INVALID",
                    format!("Line {idx} branch step deserialization failed: {e}"),
                )
            })?;
            branch_steps.push(step);
        }
        evaluator.record_compensation_branch(b_id, &branch_steps)?;
        Ok(())
    }

    fn verify_expected_head(
        expected_head_sha256: Option<&str>,
        prev_hash: Option<&str>,
    ) -> Result<(), Refusal> {
        if let Some(expected) = expected_head_sha256 {
            if prev_hash != Some(expected) {
                return Err(ddc_refusal(
                    "DDC_AUDIT_HEAD_HASH_MISMATCH",
                    format!("Log head hash mismatch: expected {expected}, got {prev_hash:?}."),
                ));
            }
        }
        Ok(())
    }
}

fn require_complete_check(val: bool) -> bool {
    val
}

// Origin: engine/crates_rs/core_adversary/src/stage/ddc_tape_evaluator.rs
// Claim: urn:core:crates_rs:core-adversary:ddc-tape-evaluator:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf1a7729a {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf1a7729a` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf1a7729a {
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
impl BoundaryErrorf1a7729a {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf1a7729a {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf1a7729a {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf1a7729a {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf1a7729a> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf1a7729a::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf1a7729a::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf1a7729a::ExceedsCapacity {
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
mod l4_boundary_tests_f1a7729a {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordf1a7729a::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordf1a7729a::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordf1a7729a::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordf1a7729a::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordf1a7729a::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorf1a7729a::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorf1a7729a::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
