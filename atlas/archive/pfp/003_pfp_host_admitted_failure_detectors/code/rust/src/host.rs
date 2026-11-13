//! Host state machine for PFP Paper 003 (Rust port of `code/host_engine.py`).
//!
//! 1. Phases: INTAKE -> COVERAGE -> WITNESS -> VERIFY -> TERMINAL.
//! 2. Fuel: each attempted batch costs one unit, which a rollback does not return.
//! 3. A batch is applied atomically or rolled back as a whole.
//! 4. A SHA-256 digest chain binds the prior digest, the proposed moves, and the decision.
//!
//! Every nonempty route returns `NO_NATIVE_PORT`; no witness is certified.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HostPhase {
    INTAKE,
    COVERAGE,
    WITNESS,
    VERIFY,
    TERMINAL,
}

// Variant names are the wire strings shared with the Python host.
#[allow(non_camel_case_types)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum HostExit {
    FUEL_EXHAUSTED,
    SCOPED_CERTIFICATE,
    REFUSED,
    REJECTED,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RouteRefusal {
    pub code: String,
    pub detail: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MoveProposal {
    pub move_type: String,
    #[serde(default)]
    pub payload: serde_json::Value,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HostState {
    pub fixture_id: String,
    pub arm: String,
    pub current_phase: HostPhase,
    pub remaining_fuel: u64,
    pub covered_elements: BTreeSet<String>,
    pub witness_candidate: Option<serde_json::Value>,
    pub terminal_exit: Option<HostExit>,
    pub terminal_label: Option<String>,
    pub state_digest: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct StepReceipt {
    pub host_decision: String,
    pub batch_rolled_back: bool,
    pub prior_state_digest: String,
    pub new_state_digest: String,
    pub detector_findings: Vec<String>,
}

pub fn initial_digest(fixture_id: &str, arm: &str) -> String {
    let mut hasher = Sha256::new();
    let val = serde_json::json!({
        "arm": arm,
        "fixture_id": fixture_id
    });
    let canonical = serde_json::to_string(&val).unwrap_or_default();
    hasher.update(canonical.as_bytes());
    format!("{:x}", hasher.finalize())
}

pub fn chain_digest(prior_digest: &str, event_bytes: &[u8], decision: &str) -> String {
    let mut hasher = Sha256::new();
    let mut hex_event = String::with_capacity(event_bytes.len() * 2);
    for b in event_bytes {
        use std::fmt::Write;
        let _ = write!(&mut hex_event, "{:02x}", b);
    }
    let input = format!("{}:{}:{}", prior_digest, hex_event, decision);
    hasher.update(input.as_bytes());
    format!("{:x}", hasher.finalize())
}

pub fn event_bytes(moves: &[MoveProposal]) -> Vec<u8> {
    let json_val = serde_json::to_string(moves).unwrap_or_default();
    json_val.into_bytes()
}

pub fn fixture_route(fixture_id: &str) -> Result<String, RouteRefusal> {
    match fixture_id {
        "gauge_even_triangle" => Ok("restricted_diagonal_sign_gauge".to_string()),
        "gauge_odd_triangle" => Ok("frustrated_parity_gauge".to_string()),
        "cochain_exact_cycle" => Ok("discrete_gauge_potential".to_string()),
        "meron_two_pairs_survivor" => Ok("meron_cluster_involution".to_string()),
        "frustrated_square_diagonal" => Ok("frustrated_diagonal_sign_gauge".to_string()),
        _ => Err(RouteRefusal {
            code: "UNKNOWN_FIXTURE".to_string(),
            detail: fixture_id.to_string(),
        }),
    }
}

pub fn verify_route(route: &str) -> Result<(), RouteRefusal> {
    if route.is_empty() {
        return Err(RouteRefusal {
            code: "UNKNOWN_ROUTE".to_string(),
            detail: "".to_string(),
        });
    }
    // Every nonempty declared route yields NO_NATIVE_PORT: no route port exists.
    Err(RouteRefusal {
        code: "NO_NATIVE_PORT".to_string(),
        detail: route.to_string(),
    })
}

#[derive(Debug, Clone)]
pub struct Demo3HostEngine {
    pub fixture_id: String,
    pub arm: String,
    pub fixture: BTreeMap<String, String>,
    pub state: HostState,
    pub route_refusal: Option<RouteRefusal>,
}

impl Demo3HostEngine {
    pub fn new(
        fixture_id: &str,
        arm: &str,
        initial_fuel: Option<u64>,
    ) -> Result<Self, RouteRefusal> {
        let route = fixture_route(fixture_id)?;
        let mut fixture = BTreeMap::new();
        fixture.insert("fixture_id".to_string(), fixture_id.to_string());
        fixture.insert("route".to_string(), route);

        let fuel = initial_fuel.unwrap_or(11);
        let init_dig = initial_digest(fixture_id, arm);

        let state = HostState {
            fixture_id: fixture_id.to_string(),
            arm: arm.to_string(),
            current_phase: HostPhase::INTAKE,
            remaining_fuel: fuel,
            covered_elements: BTreeSet::new(),
            witness_candidate: None,
            terminal_exit: None,
            terminal_label: None,
            state_digest: init_dig,
        };

        Ok(Self {
            fixture_id: fixture_id.to_string(),
            arm: arm.to_string(),
            fixture,
            state,
            route_refusal: None,
        })
    }

    pub fn execute_batch(&mut self, proposals: &[MoveProposal]) -> StepReceipt {
        let prior_digest = self.state.state_digest.clone();
        let ev_bytes = event_bytes(proposals);

        if self.state.current_phase == HostPhase::TERMINAL {
            let decision = "REJECT_TERMINAL_STATE".to_string();
            let new_dig = chain_digest(&prior_digest, &ev_bytes, &decision);
            self.state.state_digest = new_dig.clone();
            return StepReceipt {
                host_decision: decision,
                batch_rolled_back: true,
                prior_state_digest: prior_digest,
                new_state_digest: new_dig,
                detector_findings: Vec::new(),
            };
        }

        if self.state.remaining_fuel == 0 {
            self.state.current_phase = HostPhase::TERMINAL;
            self.state.terminal_exit = Some(HostExit::FUEL_EXHAUSTED);
            let decision = "FUEL_EXHAUSTED".to_string();
            let new_dig = chain_digest(&prior_digest, &ev_bytes, &decision);
            self.state.state_digest = new_dig.clone();
            return StepReceipt {
                host_decision: decision,
                batch_rolled_back: true,
                prior_state_digest: prior_digest,
                new_state_digest: new_dig,
                detector_findings: Vec::new(),
            };
        }

        // Attempting a batch costs 1 unit of fuel outside semantic rollback
        let attempt_fuel = self.state.remaining_fuel.saturating_sub(1);

        // Empty batch check
        if proposals.is_empty() {
            let decision = "REJECT_EMPTY_BATCH".to_string();
            let new_dig = chain_digest(&prior_digest, &ev_bytes, &decision);
            self.state.remaining_fuel = attempt_fuel;
            self.state.state_digest = new_dig.clone();
            if attempt_fuel == 0 {
                self.state.current_phase = HostPhase::TERMINAL;
                self.state.terminal_exit = Some(HostExit::FUEL_EXHAUSTED);
            }
            return StepReceipt {
                host_decision: decision,
                batch_rolled_back: true,
                prior_state_digest: prior_digest,
                new_state_digest: new_dig,
                detector_findings: Vec::new(),
            };
        }

        // Upfront check for invalid batch structure: move after VERIFY
        let verify_idx = proposals.iter().position(|p| p.move_type == "VERIFY");
        if let Some(idx) = verify_idx {
            if idx < proposals.len() - 1 {
                let decision = "REJECT_MOVE_AFTER_VERIFY".to_string();
                let new_dig = chain_digest(&prior_digest, &ev_bytes, &decision);
                self.state.remaining_fuel = attempt_fuel;
                self.state.state_digest = new_dig.clone();
                if attempt_fuel == 0 {
                    self.state.current_phase = HostPhase::TERMINAL;
                    self.state.terminal_exit = Some(HostExit::FUEL_EXHAUSTED);
                }
                return StepReceipt {
                    host_decision: decision,
                    batch_rolled_back: true,
                    prior_state_digest: prior_digest,
                    new_state_digest: new_dig,
                    detector_findings: Vec::new(),
                };
            }
        }

        // Snapshot state for atomic rollback
        let snapshot = self.state.clone();
        let mut temp_state = self.state.clone();
        temp_state.remaining_fuel = attempt_fuel;
        let mut saw_verify = false;
        let mut decision = "ACCEPTED".to_string();
        let mut rollback = false;

        for prop in proposals {
            if saw_verify {
                decision = "REJECT_MOVE_AFTER_VERIFY".to_string();
                rollback = true;
                break;
            }

            match prop.move_type.as_str() {
                "COVER_ELEMENT" => {
                    let elem_opt = prop.payload.get("element_id").and_then(|v| v.as_str());
                    if let Some(elem) = elem_opt {
                        if elem.is_empty() {
                            decision = "REJECT_MALFORMED_PAYLOAD".to_string();
                            rollback = true;
                            break;
                        }
                        temp_state.covered_elements.insert(elem.to_string());
                        if temp_state.current_phase == HostPhase::INTAKE {
                            temp_state.current_phase = HostPhase::COVERAGE;
                        }
                    } else {
                        decision = "REJECT_MALFORMED_PAYLOAD".to_string();
                        rollback = true;
                        break;
                    }
                }
                "PROPOSE_WITNESS" => {
                    temp_state.witness_candidate = Some(prop.payload.clone());
                    temp_state.current_phase = HostPhase::WITNESS;
                }
                "HOLD_DETECTOR_FEEDBACK" => {
                    decision = "HOLD_DETECTOR_FEEDBACK".to_string();
                }
                "VERIFY" => {
                    saw_verify = true;
                    if temp_state.covered_elements.is_empty() {
                        decision = "REJECT_INCOMPLETE_COVERAGE".to_string();
                        rollback = true;
                        break;
                    }
                    temp_state.current_phase = HostPhase::VERIFY;
                    // Check route
                    let route = self.fixture.get("route").cloned().unwrap_or_default();
                    match verify_route(&route) {
                        Ok(()) => {
                            decision = "ACCEPTED_CERTIFICATE".to_string();
                            temp_state.terminal_exit = Some(HostExit::SCOPED_CERTIFICATE);
                            temp_state.current_phase = HostPhase::TERMINAL;
                        }
                        Err(refusal) => {
                            decision = refusal.code.clone();
                            self.route_refusal = Some(refusal.clone());
                            rollback = true;
                            break;
                        }
                    }
                }
                unknown => {
                    decision = format!("REJECT_UNKNOWN_MOVE:{}", unknown);
                    rollback = true;
                    break;
                }
            }
        }

        let new_digest = chain_digest(&prior_digest, &ev_bytes, &decision);

        if rollback {
            // Restore semantic state, retaining non-refundable attempt fuel deduction
            self.state = snapshot;
            self.state.remaining_fuel = attempt_fuel;
            if attempt_fuel == 0 {
                self.state.current_phase = HostPhase::TERMINAL;
                self.state.terminal_exit = Some(HostExit::FUEL_EXHAUSTED);
            }
            self.state.state_digest = new_digest.clone();
            StepReceipt {
                host_decision: decision,
                batch_rolled_back: true,
                prior_state_digest: prior_digest,
                new_state_digest: new_digest,
                detector_findings: Vec::new(),
            }
        } else {
            temp_state.remaining_fuel = attempt_fuel;
            if attempt_fuel == 0 && temp_state.current_phase != HostPhase::TERMINAL {
                temp_state.current_phase = HostPhase::TERMINAL;
                temp_state.terminal_exit = Some(HostExit::FUEL_EXHAUSTED);
            }
            temp_state.state_digest = new_digest.clone();
            self.state = temp_state;
            StepReceipt {
                host_decision: decision,
                batch_rolled_back: false,
                prior_state_digest: prior_digest,
                new_state_digest: new_digest,
                detector_findings: Vec::new(),
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_host_initialization() {
        let engine = Demo3HostEngine::new("gauge_even_triangle", "T", None).unwrap();
        assert_eq!(engine.state.current_phase, HostPhase::INTAKE);
        assert_eq!(engine.state.remaining_fuel, 11);
        assert_eq!(
            engine.state.state_digest,
            initial_digest("gauge_even_triangle", "T")
        );
    }

    #[test]
    fn test_batch_rollback_on_unknown_move() {
        let mut engine = Demo3HostEngine::new("gauge_even_triangle", "T", None).unwrap();
        let receipt = engine.execute_batch(&[
            MoveProposal {
                move_type: "COVER_ELEMENT".to_string(),
                payload: serde_json::json!({"element_id": "elem_rollback"}),
            },
            MoveProposal {
                move_type: "ILLEGAL_POISONED_MOVE".to_string(),
                payload: serde_json::json!({}),
            },
        ]);
        assert!(receipt.batch_rolled_back);
        assert_eq!(
            receipt.host_decision,
            "REJECT_UNKNOWN_MOVE:ILLEGAL_POISONED_MOVE"
        );
        assert!(engine.state.covered_elements.is_empty());
        assert_eq!(engine.state.remaining_fuel, 10);
    }

    #[test]
    fn test_fuel_exhaustion() {
        let mut engine = Demo3HostEngine::new("gauge_even_triangle", "T", Some(0)).unwrap();
        let receipt = engine.execute_batch(&[MoveProposal {
            move_type: "COVER_ELEMENT".to_string(),
            payload: serde_json::json!({"element_id": "elem_all"}),
        }]);
        assert_eq!(receipt.host_decision, "FUEL_EXHAUSTED");
        assert_eq!(engine.state.terminal_exit, Some(HostExit::FUEL_EXHAUSTED));
        assert_eq!(engine.state.current_phase, HostPhase::TERMINAL);
    }
}
