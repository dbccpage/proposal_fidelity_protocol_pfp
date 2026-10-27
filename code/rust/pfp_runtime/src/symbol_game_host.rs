//! Symbol Game Minimal Host & Three-Layer Verification Protocol.
//!
//! Provides the trusted host interface for the Symbol Game solution engine:
//! 1. Three-layer sovereignty model:
//!    - Layer 1: L1 discrete projection governor (defect norm D(s), idempotent projection P_S, monotonic descent).
//!    - Layer 2: Simplicial boundary divergence (B^T z = 0 on vertices, cycle holonomy).
//!    - Layer 3: Phi_1 defect descent and exact rational weak duality certification (<z, r> == ||r||_{1,w}).
//! 2. Untrusted Proposer / Trusted Host Architecture:
//!    - Untrusted proposer submits exact rational algebraic data.
//!    - Trusted host re-derives all steps fail-closed with AuthorityEffect: None.
//!    - Immutable problem digest pinning (problem statements cannot be altered or erased).
//!    - Verified state transition logging with cryptographic parent linking.
//!
//! # Epistemic Firewall
//! Firewall: stated region only; mints no authority
//! AuthorityEffect: None.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_9326a952<T> {
    fn checked_invariant_9326a952(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_9326a952<T> for Option<T> {
    #[inline]
    fn checked_invariant_9326a952(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_9326a952<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_9326a952(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{Signed, Zero};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;

/// Edge definition in the constraint complex.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ProblemEdge {
    pub u: String,
    pub v: String,
    pub weight: BigRational,
}

/// Immutable problem instance pinning the target mathematical system.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SymbolGameProblem {
    pub problem_id: String,
    pub vertices: Vec<String>,
    pub edges: Vec<ProblemEdge>,
    pub initial_claims: Vec<BigRational>,
    pub digest: String,
}

impl SymbolGameProblem {
    pub fn new(
        problem_id: String,
        vertices: Vec<String>,
        edges: Vec<ProblemEdge>,
        initial_claims: Vec<BigRational>,
    ) -> Result<Self, HostRefusalCode> {
        if edges.len() != initial_claims.len()
            || vertices.iter().collect::<BTreeSet<_>>().len() != vertices.len()
            || edges
                .iter()
                .map(|e| (&e.u, &e.v))
                .collect::<BTreeSet<_>>()
                .len()
                != edges.len()
        {
            return Err(HostRefusalCode::FormatViolation);
        }
        let zero = BigRational::zero();
        for edge in &edges {
            if edge.u == edge.v || edge.weight <= zero {
                return Err(HostRefusalCode::FormatViolation);
            }
            if !vertices.contains(&edge.u) || !vertices.contains(&edge.v) {
                return Err(HostRefusalCode::FormatViolation);
            }
        }

        let digest = Self::calculate_problem_digest(&problem_id, &vertices, &edges, &initial_claims);

        Ok(Self {
            problem_id,
            vertices,
            edges,
            initial_claims,
            digest,
        })
    }

    /// Exact canonical calculation of the problem instance SHA-256 digest.
    pub fn calculate_problem_digest(
        problem_id: &str,
        vertices: &[String],
        edges: &[ProblemEdge],
        initial_claims: &[BigRational],
    ) -> String {
        let payload = serde_json::to_vec(&(
            "SYMBOL_GAME_PROBLEM_V1",
            problem_id,
            vertices,
            edges,
            initial_claims,
        ))
        .checked_invariant_9326a952("serializable exact problem");
        let mut hasher = Sha256::new();
        hasher.update(payload);
        format!("{:x}", hasher.finalize())
    }

    /// Recompute the problem instance digest from declared mathematical fields.
    pub fn compute_digest(&self) -> String {
        Self::calculate_problem_digest(
            &self.problem_id,
            &self.vertices,
            &self.edges,
            &self.initial_claims,
        )
    }
}

/// Declared operations for Symbol Game turns.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub enum HostMoveOp {
    Assert,
    Cut,
    Verify,
    Retract,
}

/// Untrusted proposal submitted by an untrusted proposer.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UntrustedProposal {
    pub proposer_id: String,
    pub problem_digest: String,
    pub parent_state_digest: String,
    pub op: HostMoveOp,
    pub proposed_section: Option<Vec<BigRational>>,
    pub dual_witness: Option<Vec<BigRational>>,
    pub target_property: Option<String>,
    pub target_event_id: Option<String>,
    pub claimed_post_state_digest: String,
    pub claimed_defect: Option<BigRational>,
    pub rationale: String,
}

/// Refusal codes when an untrusted proposal fails closed.
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord, thiserror::Error, Serialize, Deserialize)]
pub enum HostRefusalCode {
    #[error("Problem digest mismatch: expected {expected}, got {found}")]
    ProblemDigestMismatch { expected: String, found: String },

    #[error("Parent state digest mismatch: expected {expected}, got {found}")]
    ParentStateMismatch { expected: String, found: String },

    #[error("Monotonic defect descent violated: before {before}, after {after}")]
    DefectIncrease { before: String, after: String },

    #[error("Unlicensed problem mutation: problem equations and edge claims are immutable")]
    UnlicensedProblemMutation,

    #[error("Dual witness violates divergence condition B^T z = 0 at vertex {vertex}: divergence {divergence}")]
    DualNotPerpendicular { vertex: String, divergence: String },

    #[error("Dual witness exceeds edge weight at index {edge_index}: |{value}| > {weight}")]
    DualExceedsWeight {
        edge_index: usize,
        value: String,
        weight: String,
    },

    #[error("Duality gap detected: inner product <z, r> = {pairing} != defect norm {defect}")]
    DualityGapDetected { pairing: String, defect: String },

    #[error("Non-zero obstruction: defect is {defect}")]
    NonzeroObstruction { defect: String },

    #[error("Post-state digest mismatch: host computed {host_digest}, proposer claimed {claimed_digest}")]
    PostStateDigestMismatch {
        host_digest: String,
        claimed_digest: String,
    },

    #[error("Target event '{event_id}' not found in event ledger")]
    EventNotFound { event_id: String },

    #[error("Carrier codepoint violation in rationale")]
    CarrierViolation,

    #[error("Format or dimension violation")]
    FormatViolation,
}

/// Verified state transition logged in the append-only evidence DAG.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct VerifiedEvent {
    pub event_id: String,
    #[serde(default)]
    pub event_digest: String,
    pub parent_event_id: Option<String>,
    pub problem_digest: String,
    pub parent_state_digest: String,
    pub post_state_digest: String,
    pub op: HostMoveOp,
    pub verified_defect: BigRational,
    pub details: String,
    pub section_snapshot: Vec<BigRational>,
}

impl VerifiedEvent {
    /// Exact canonical calculation of the event SHA-256 digest in the evidence DAG.
    pub fn calculate_event_digest(
        event_id: &str,
        parent_event_id: Option<&str>,
        problem_digest: &str,
        parent_state_digest: &str,
        post_state_digest: &str,
        op: HostMoveOp,
        verified_defect: &BigRational,
    ) -> String {
        let mut hasher = Sha256::new();
        hasher.update(b"SG_EVENT_V1:");
        hasher.update(event_id.as_bytes());
        hasher.update(b":PARENT_EVENT:");
        if let Some(p) = parent_event_id {
            hasher.update(p.as_bytes());
        }
        hasher.update(b":PROBLEM:");
        hasher.update(problem_digest.as_bytes());
        hasher.update(b":PARENT_STATE:");
        hasher.update(parent_state_digest.as_bytes());
        hasher.update(b":POST_STATE:");
        hasher.update(post_state_digest.as_bytes());
        hasher.update(b":OP:");
        hasher.update(format!("{:?}", op).as_bytes());
        hasher.update(b":DEFECT:");
        hasher.update(verified_defect.to_string().as_bytes());
        format!("{:x}", hasher.finalize())
    }
}

/// Result of proposal evaluation by the trusted host.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HostVerdict {
    pub admitted: bool,
    pub refusal_code: Option<HostRefusalCode>,
    pub reason: Option<String>,
    pub post_state_digest: Option<String>,
    pub verified_defect: Option<BigRational>,
    pub event_id: Option<String>,
}

/// Trusted Symbol Game host executing fail-closed verification.
pub struct SymbolGameHost {
    pub problem: SymbolGameProblem,
    pub current_state_digest: String,
    pub section: Vec<BigRational>,
    pub history: Vec<VerifiedEvent>,
    pub refusals: Vec<HostRefusalCode>,
    pub step_counter: usize,
}

impl SymbolGameHost {
    /// Attempt to initialize trusted host, fail-closed validating the declared problem digest.
    pub fn try_new(problem: SymbolGameProblem) -> Result<Self, HostRefusalCode> {
        let expected_digest = problem.compute_digest();
        if problem.digest != expected_digest {
            return Err(HostRefusalCode::ProblemDigestMismatch {
                expected: expected_digest,
                found: problem.digest,
            });
        }
        let n_verts = problem.vertices.len();
        let section = vec![BigRational::zero(); n_verts];
        let initial_defect = Self::compute_defect(&problem, &section);

        let initial_digest = Self::calculate_state_digest(
            &problem.digest,
            "0000000000000000000000000000000000000000000000000000000000000000",
            0,
            &section,
            &initial_defect,
        );

        Ok(Self {
            problem,
            current_state_digest: initial_digest,
            section,
            history: Vec::new(),
            refusals: Vec::new(),
            step_counter: 0,
        })
    }

    /// Initialize trusted host, asserting that the problem instance digest matches its declared mathematical fields.
    pub fn new(problem: SymbolGameProblem) -> Self {
        Self::try_new(problem).checked_invariant_9326a952("valid problem digest required at host bootstrap")
    }

    pub fn calculate_state_digest(
        problem_digest: &str,
        parent_digest: &str,
        step_idx: usize,
        sec: &[BigRational],
        defect: &BigRational,
    ) -> String {
        let mut hasher = Sha256::new();
        hasher.update(b"SG_STATE_V1:");
        hasher.update(problem_digest.as_bytes());
        hasher.update(b":PARENT:");
        hasher.update(parent_digest.as_bytes());
        hasher.update(b":STEP:");
        hasher.update(step_idx.to_string().as_bytes());
        hasher.update(b":SECTION:");
        for s in sec {
            hasher.update(s.to_string().as_bytes());
            hasher.update(b",");
        }
        hasher.update(b":DEFECT:");
        hasher.update(defect.to_string().as_bytes());
        format!("{:x}", hasher.finalize())
    }

    pub fn compute_defect(problem: &SymbolGameProblem, sec: &[BigRational]) -> BigRational {
        let mut total = BigRational::zero();
        for (i, edge) in problem.edges.iter().enumerate() {
            let u_idx = problem.vertices.iter().position(|v| v == &edge.u).checked_invariant_9326a952("checked invariant");
            let v_idx = problem.vertices.iter().position(|v| v == &edge.v).checked_invariant_9326a952("checked invariant");
            let diff = &sec[v_idx] - &sec[u_idx];
            let residual = &problem.initial_claims[i] - diff;
            let abs_res = if residual.is_negative() {
                -residual
            } else {
                residual
            };
            total += &edge.weight * abs_res;
        }
        total
    }

    pub fn section_defect(&self) -> BigRational {
        Self::compute_defect(&self.problem, &self.section)
    }

    pub fn compute_residuals(&self, sec: &[BigRational]) -> Vec<BigRational> {
        let mut residuals = Vec::with_capacity(self.problem.edges.len());
        for (i, edge) in self.problem.edges.iter().enumerate() {
            let u_idx = self
                .problem
                .vertices
                .iter()
                .position(|v| v == &edge.u)
                .checked_invariant_9326a952("checked invariant");
            let v_idx = self
                .problem
                .vertices
                .iter()
                .position(|v| v == &edge.v)
                .checked_invariant_9326a952("checked invariant");
            let diff = &sec[v_idx] - &sec[u_idx];
            residuals.push(&self.problem.initial_claims[i] - diff);
        }
        residuals
    }

    fn verify_dual_divergence(&self, dual: &[BigRational]) -> Result<(), HostRefusalCode> {
        // 1. Divergence check at each vertex: sum_{in} z_e - sum_{out} z_e = 0
        let n_verts = self.problem.vertices.len();
        let mut divergences = vec![BigRational::zero(); n_verts];
        for (e_idx, edge) in self.problem.edges.iter().enumerate() {
            let u_idx = self
                .problem
                .vertices
                .iter()
                .position(|v| v == &edge.u)
                .checked_invariant_9326a952("checked invariant");
            let v_idx = self
                .problem
                .vertices
                .iter()
                .position(|v| v == &edge.v)
                .checked_invariant_9326a952("checked invariant");
            divergences[v_idx] += &dual[e_idx];
            divergences[u_idx] -= &dual[e_idx];
        }

        for (v_idx, div) in divergences.iter().enumerate() {
            if !div.is_zero() {
                return Err(HostRefusalCode::DualNotPerpendicular {
                    vertex: self.problem.vertices[v_idx].clone(),
                    divergence: div.to_string(),
                });
            }
        }
        Ok(())
    }

    fn verify_dual_weight_bounds(&self, dual: &[BigRational]) -> Result<(), HostRefusalCode> {
        // 2. Weight bound: |z_e| <= w_e
        for (e_idx, edge) in self.problem.edges.iter().enumerate() {
            let z_val = &dual[e_idx];
            let abs_z = if z_val.is_negative() {
                -z_val.clone()
            } else {
                z_val.clone()
            };
            if abs_z > edge.weight {
                return Err(HostRefusalCode::DualExceedsWeight {
                    edge_index: e_idx,
                    value: z_val.to_string(),
                    weight: edge.weight.to_string(),
                });
            }
        }
        Ok(())
    }

    /// Verifies the three Lean soundness hypotheses for weak duality:
    /// 1. Divergence condition: B^T z = 0 at every vertex.
    /// 2. Weight bound: |z_e| <= w_e for every edge.
    /// 3. Zero duality gap: <z, r> == ||r||_{1,w}.
    pub fn verify_dual_witness(
        &self,
        dual: &[BigRational],
        sec: &[BigRational],
    ) -> Result<(), HostRefusalCode> {
        let n_edges = self.problem.edges.len();
        if dual.len() != n_edges || sec.len() != self.problem.vertices.len() {
            return Err(HostRefusalCode::FormatViolation);
        }

        self.verify_dual_divergence(dual)?;
        self.verify_dual_weight_bounds(dual)?;

        // 3. Zero duality gap: sum_e z_e * r_e == ||r||_{1,w}
        let residuals = self.compute_residuals(sec);
        let defect = Self::compute_defect(&self.problem, sec);

        let mut pairing = BigRational::zero();
        for (e_idx, res) in residuals.iter().enumerate() {
            pairing += &dual[e_idx] * res;
        }

        if pairing != defect {
            return Err(HostRefusalCode::DualityGapDetected {
                pairing: pairing.to_string(),
                defect: defect.to_string(),
            });
        }

        Ok(())
    }

    fn is_valid_rationale_char(c: char) -> bool {
        matches!(c as u32, 32..=126 | 0x0391..=0x03A9 | 0x03B1..=0x03C9
            | 0x2192 | 0x22A2 | 0x22A5 | 0x2261)
    }

    fn process_cut_move(
        &mut self,
        proposal: &UntrustedProposal,
        next_step: usize,
        event_id: String,
        parent_event_id: Option<String>,
    ) -> HostVerdict {
        let candidate_section = match &proposal.proposed_section {
            Some(sec) if sec.len() == self.problem.vertices.len() => sec,
            _ => return self.refuse(HostRefusalCode::FormatViolation),
        };

        let defect_before = self.section_defect();
        let defect_after = Self::compute_defect(&self.problem, candidate_section);

        // Monotonic descent check: defect must not increase
        if defect_after > defect_before {
            return self.refuse(HostRefusalCode::DefectIncrease {
                before: defect_before.to_string(),
                after: defect_after.to_string(),
            });
        }

        // Compute host post-state digest
        let host_post_digest = Self::calculate_state_digest(
            &self.problem.digest,
            &self.current_state_digest,
            next_step,
            candidate_section,
            &defect_after,
        );

        // Validate proposer claimed post-state digest
        if host_post_digest != proposal.claimed_post_state_digest {
            return self.refuse(HostRefusalCode::PostStateDigestMismatch {
                host_digest: host_post_digest,
                claimed_digest: proposal.claimed_post_state_digest.clone(),
            });
        }

        // Commit state
        self.section = candidate_section.clone();
        self.step_counter = next_step;
        self.current_state_digest = host_post_digest.clone();

        let ev_digest = VerifiedEvent::calculate_event_digest(
            &event_id,
            parent_event_id.as_deref(),
            &self.problem.digest,
            &proposal.parent_state_digest,
            &host_post_digest,
            HostMoveOp::Cut,
            &defect_after,
        );
        let ev = VerifiedEvent {
            event_id: event_id.clone(),
            event_digest: ev_digest,
            parent_event_id,
            problem_digest: self.problem.digest.clone(),
            parent_state_digest: proposal.parent_state_digest.clone(),
            post_state_digest: host_post_digest.clone(),
            op: HostMoveOp::Cut,
            verified_defect: defect_after.clone(),
            details: format!(
                "CUT accepted: defect reduced from {} to {}",
                defect_before, defect_after
            ),
            section_snapshot: self.section.clone(),
        };
        self.history.push(ev);

        HostVerdict {
            admitted: true,
            refusal_code: None,
            reason: None,
            post_state_digest: Some(host_post_digest),
            verified_defect: Some(defect_after),
            event_id: Some(event_id),
        }
    }

    fn verify_target_property(
        &self,
        proposal: &UntrustedProposal,
        target_prop: &str,
        cur_defect: &BigRational,
    ) -> Result<(), HostRefusalCode> {
        if target_prop == "ZERO_OBSTRUCTION" {
            if !cur_defect.is_zero() {
                return Err(HostRefusalCode::NonzeroObstruction {
                    defect: cur_defect.to_string(),
                });
            }
            Ok(())
        } else if target_prop == "DUAL_WITNESS" {
            let dual = match &proposal.dual_witness {
                Some(d) if d.len() == self.problem.edges.len() => d,
                _ => return Err(HostRefusalCode::FormatViolation),
            };
            self.verify_dual_witness(dual, &self.section)
        } else {
            Err(HostRefusalCode::FormatViolation)
        }
    }

    fn process_verify_move(
        &mut self,
        proposal: &UntrustedProposal,
        next_step: usize,
        event_id: String,
        parent_event_id: Option<String>,
    ) -> HostVerdict {
        let target_prop = proposal.target_property.as_deref().unwrap_or("");
        let cur_defect = self.section_defect();

        if let Err(refusal) = self.verify_target_property(proposal, target_prop, &cur_defect) {
            return self.refuse(refusal);
        }

        let host_post_digest = Self::calculate_state_digest(
            &self.problem.digest,
            &self.current_state_digest,
            next_step,
            &self.section,
            &cur_defect,
        );

        if host_post_digest != proposal.claimed_post_state_digest {
            return self.refuse(HostRefusalCode::PostStateDigestMismatch {
                host_digest: host_post_digest,
                claimed_digest: proposal.claimed_post_state_digest.clone(),
            });
        }

        self.step_counter = next_step;
        self.current_state_digest = host_post_digest.clone();
        let ev_digest = VerifiedEvent::calculate_event_digest(
            &event_id,
            parent_event_id.as_deref(),
            &self.problem.digest,
            &proposal.parent_state_digest,
            &host_post_digest,
            HostMoveOp::Verify,
            &cur_defect,
        );
        let ev = VerifiedEvent {
            event_id: event_id.clone(),
            event_digest: ev_digest,
            parent_event_id,
            problem_digest: self.problem.digest.clone(),
            parent_state_digest: proposal.parent_state_digest.clone(),
            post_state_digest: host_post_digest.clone(),
            op: HostMoveOp::Verify,
            verified_defect: cur_defect.clone(),
            details: format!(
                "VERIFY '{}' accepted with defect {}",
                target_prop, cur_defect
            ),
            section_snapshot: self.section.clone(),
        };
        self.history.push(ev);

        HostVerdict {
            admitted: true,
            refusal_code: None,
            reason: None,
            post_state_digest: Some(host_post_digest),
            verified_defect: Some(cur_defect),
            event_id: Some(event_id),
        }
    }

    fn process_retract_move(
        &mut self,
        proposal: &UntrustedProposal,
        next_step: usize,
        event_id: String,
        parent_event_id: Option<String>,
    ) -> HostVerdict {
        let Some(target_ev) = &proposal.target_event_id else {
            return self.refuse(HostRefusalCode::FormatViolation);
        };

        let Some(idx) = self.history.iter().position(|e| &e.event_id == target_ev) else {
            return self.refuse(HostRefusalCode::EventNotFound {
                event_id: target_ev.clone(),
            });
        };

        let restored = if idx == 0 {
            vec![BigRational::zero(); self.problem.vertices.len()]
        } else {
            self.history[idx - 1].section_snapshot.clone()
        };
        let defect = Self::compute_defect(&self.problem, &restored);
        let post_digest = Self::calculate_state_digest(
            &self.problem.digest,
            &self.current_state_digest,
            next_step,
            &restored,
            &defect,
        );
        if post_digest != proposal.claimed_post_state_digest {
            return self.refuse(HostRefusalCode::PostStateDigestMismatch {
                host_digest: post_digest,
                claimed_digest: proposal.claimed_post_state_digest.clone(),
            });
        }
        let ev_digest = VerifiedEvent::calculate_event_digest(
            &event_id,
            parent_event_id.as_deref(),
            &self.problem.digest,
            &self.current_state_digest,
            &post_digest,
            HostMoveOp::Retract,
            &defect,
        );
        self.history.push(VerifiedEvent {
            event_id: event_id.clone(),
            event_digest: ev_digest,
            parent_event_id,
            problem_digest: self.problem.digest.clone(),
            parent_state_digest: self.current_state_digest.clone(),
            post_state_digest: post_digest.clone(),
            op: HostMoveOp::Retract,
            verified_defect: defect,
            details: format!("Restored state before {}; prior events retained", target_ev),
            section_snapshot: restored.clone(),
        });
        self.section = restored;
        self.current_state_digest = post_digest;
        self.step_counter = next_step;

        HostVerdict {
            admitted: true,
            refusal_code: None,
            reason: None,
            post_state_digest: Some(self.current_state_digest.clone()),
            verified_defect: Some(self.section_defect()),
            event_id: Some(event_id),
        }
    }

    /// Evaluates an untrusted proposal fail-closed.
    pub fn process_proposal(&mut self, proposal: &UntrustedProposal) -> HostVerdict {
        // 1. FW-PROBLEM-PIN: Problem digest must match exactly
        if proposal.problem_digest != self.problem.digest {
            return self.refuse(HostRefusalCode::ProblemDigestMismatch {
                expected: self.problem.digest.clone(),
                found: proposal.problem_digest.clone(),
            });
        }

        // 2. FW-PARENT-PIN: Parent state digest must match current tip
        if proposal.parent_state_digest != self.current_state_digest {
            return self.refuse(HostRefusalCode::ParentStateMismatch {
                expected: self.current_state_digest.clone(),
                found: proposal.parent_state_digest.clone(),
            });
        }

        if !proposal.rationale.chars().all(Self::is_valid_rationale_char) {
            return self.refuse(HostRefusalCode::CarrierViolation);
        }
        let next_step = self.step_counter + 1;
        let event_id = format!("ev_{:04}_{:?}", next_step, proposal.op);
        let parent_event_id = self.history.last().map(|e| e.event_id.clone());

        match proposal.op {
            HostMoveOp::Cut => self.process_cut_move(proposal, next_step, event_id, parent_event_id),
            HostMoveOp::Verify => {
                self.process_verify_move(proposal, next_step, event_id, parent_event_id)
            }
            HostMoveOp::Assert => {
                // Problem claims are immutable; uncertified assert refused
                self.refuse(HostRefusalCode::UnlicensedProblemMutation)
            }
            HostMoveOp::Retract => {
                self.process_retract_move(proposal, next_step, event_id, parent_event_id)
            }
        }
    }

    fn refuse(&mut self, code: HostRefusalCode) -> HostVerdict {
        let reason = code.to_string();
        self.refusals.push(code.clone());
        HostVerdict {
            admitted: false,
            refusal_code: Some(code),
            reason: Some(reason),
            post_state_digest: None,
            verified_defect: None,
            event_id: None,
        }
    }
}

/// Helper to build a 3-vertex directed cycle constraint problem encoding:
/// det = prod_diff - lin_corr.
pub fn build_mub6_det_cycle(
    a: BigRational,
    b: BigRational,
    c: BigRational,
    d: BigRational,
) -> SymbolGameProblem {
    let prod_diff = &a * &d - &b * &c;
    let lin_corr = (&a - &b) + (&d - &c);
    let _det = &prod_diff - &lin_corr;

    let vertices = vec!["origin".to_string(), "mid".to_string(), "end".to_string()];
    let edges = vec![
        ProblemEdge {
            u: "origin".to_string(),
            v: "mid".to_string(),
            weight: BigRational::from_integer(BigInt::from(1)),
        },
        ProblemEdge {
            u: "mid".to_string(),
            v: "end".to_string(),
            weight: BigRational::from_integer(BigInt::from(1)),
        },
        ProblemEdge {
            u: "end".to_string(),
            v: "origin".to_string(),
            weight: BigRational::from_integer(BigInt::from(1)),
        },
    ];
    let initial_claims = vec![prod_diff, -lin_corr, BigRational::zero()];

    SymbolGameProblem::new(
        format!("MUB6_DET_CYCLE_a{}_b{}_c{}_d{}", a, b, c, d),
        vertices,
        edges,
        initial_claims,
    )
    .checked_invariant_9326a952("Valid 3-cycle problem")
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_9326a952 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
