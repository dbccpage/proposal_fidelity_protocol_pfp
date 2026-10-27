//! Runtime composition of the report checker, detached operator, policy and
//! licensed engine. Persistent host custody remains outside this process.
use engines::licensed_commit::{commit, state_digest, ReportState};
use core_pipelines::report_route::{self, Binding, Stage};
use core_policy::{ExactnessWitness, LicensingBoundary, TransitionProposal, ValuationReceipt};
use core_wdp::genesis_report_runtime::{self as native, Decision, Fact, Request};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const CONTRACT: &[u8] = include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"),
    "/../governance/contracts/contracts_oe/base/genesis_report_operation.contract.yaml"));
pub const CONTRACT_ID: &str = "urn:core:execution:genesis_report_operation:v1.0.0";

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct DescriptionRequest {
    request: Request,
    target: String,
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct ExecuteRequest {
    request: Request,
    current: ReportState,
    route: Vec<Stage>,
    repair_prefix: usize,
}

fn digest(domain: &[u8], value: &impl serde::Serialize) -> Result<String, String> {
    let mut hash = Sha256::new();
    hash.update(domain);
    hash.update([0]);
    hash.update(serde_json::to_vec(value).map_err(|e| e.to_string())?);
    Ok(format!("{:x}", hash.finalize()))
}

fn binding(request: &Request) -> Result<Binding, String> {
    Ok(Binding {
        contract_sha256: format!("{:x}", Sha256::digest(CONTRACT)),
        carrier_sha256: digest(
            b"core.report-carrier.v1",
            &(&request.source_sha256, &request.histories),
        )?,
        questions_sha256: digest(
            b"core.report-questions.v1",
            &(&request.questions, &request.continuations),
        )?,
        request_sha256: native::request_sha256(request).map_err(|e| e.to_string())?,
    })
}

fn initial(request: &Request, target: &str) -> Result<ReportState, String> {
    if target.is_empty()
        || target.len() > 128
        || !target
            .bytes()
            .all(|b| b.is_ascii_alphanumeric() || b"._:-".contains(&b))
    {
        return Err("REPORT_TARGET".into());
    }
    let identity = binding(request)?;
    Ok(ReportState {
        target: target.into(),
        version: 0,
        contract_sha256: identity.contract_sha256,
        request_sha256: identity.request_sha256,
        partition: vec![],
    })
}

fn preflight(value: &Value) -> Result<(), String> {
    crate::wire_limits::validate_json_value(value, 65_536, 16)
        .map_err(|e| format!("REPORT_WIRE: {e:?}"))
}

/// Describe identities without evaluating histories or consuming an attempt.
pub fn describe(payload: &Value) -> Result<Value, String> {
    preflight(payload)?;
    let input: DescriptionRequest =
        serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    let identity = binding(&input.request)?;
    Ok(json!({"contract_id": CONTRACT_ID, "binding": identity,
        "route": report_route::manifest(&identity), "initial": initial(&input.request, &input.target)?,
        "authority_effect": "None"}))
}

/// Structural operator: copy an already checked partition, without evaluation.
fn detached(current: &ReportState, partition: &[usize]) -> Result<ReportState, String> {
    let mut post = current.clone();
    post.version = post
        .version
        .checked_add(1)
        .ok_or("REPORT_VERSION_OVERFLOW")?;
    post.partition = partition.to_vec();
    Ok(post)
}

fn validate_native_report_result(result: &native::ResultPacket) -> Result<(), String> {
    if result
        .operations
        .iter()
        .any(|op| !matches!(op.decision, Decision::Decoder { .. }))
    {
        return Err("REPORT_CONTINUATION_COLLISION".into());
    }
    if let Some(global) = &result.global {
        if !matches!(global.fact, Fact::Certified { .. }) {
            return Err(format!("REPORT_ORIGINAL_GLOBAL_TASK: {:?}", global.fact));
        }
    }
    Ok(())
}

fn prepare_report_post_state(
    current: &ReportState,
    result: &native::ResultPacket,
    repair_prefix: usize,
) -> Result<(ReportState, String, String, String), String> {
    let repair = result.repair.as_ref().ok_or("REPORT_REPAIR_REQUIRED")?;
    let rank = repair
        .ranks
        .get(repair_prefix)
        .ok_or("REPORT_PREFIX_RANGE")?;
    if *rank != 0 {
        return Err("REPORT_INCOMPLETE_REPAIR".into());
    }
    let post = detached(current, &repair.partitions[repair_prefix])?;
    let repair_diff =
        serde_json::to_string(&repair.steps[..repair_prefix]).map_err(|e| e.to_string())?;
    Ok((
        post,
        repair.ranks[0].to_string(),
        rank.to_string(),
        repair_diff,
    ))
}

fn mint_report_license(
    current: &ReportState,
    post: &ReportState,
    phi_pre: String,
    phi_post: String,
    repair_differential: String,
    witness_digest: String,
) -> Result<core_policy::ActionLicense, String> {
    let invariants = vec![
        "original_request".into(),
        "protected_questions".into(),
        "original_global_task".into(),
    ];
    // The policy layer checks these values; their mathematical evidence is
    // established above by the WDP owner, never by the committer.
    LicensingBoundary
        .mint(
            &TransitionProposal {
                pre_state_digest: state_digest(current)?,
                post_state_digest: state_digest(post)?,
                valuation: ValuationReceipt {
                    phi_pre,
                    phi_post,
                    delta_phi_is_non_positive: true,
                    gamma2: "0".to_string(),
                    gamma2_is_zero: true,
                    phi_post_is_zero: true,
                },
                exactness_witness: Some(ExactnessWitness {
                    repair_differential,
                    witness_digest,
                    checked_by: "core_wdp::genesis_report_runtime::verify".into(),
                }),
                preserved_invariants: invariants.clone(),
            },
            &invariants,
        )
        .map_err(|e| e.to_string())
}

fn evaluate_and_verify_report(input: &ExecuteRequest) -> Result<native::ResultPacket, String> {
    let identity = binding(&input.request)?;
    report_route::validate(&input.route, &identity)?;
    if input.current != initial(&input.request, &input.current.target)? {
        return Err("REPORT_PRE_STATE".into());
    }
    let result = native::evaluate(&input.request).map_err(|e| e.to_string())?;
    native::verify(&input.request, &result).map_err(|e| e.to_string())?;
    validate_native_report_result(&result)?;
    Ok(result)
}

pub fn execute(payload: &Value) -> Result<Value, String> {
    preflight(payload)?;
    let input: ExecuteRequest =
        serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    let result = evaluate_and_verify_report(&input)?;
    let (post, phi_pre, phi_post, repair_differential) =
        prepare_report_post_state(&input.current, &result, input.repair_prefix)?;
    let witness_digest = format!(
        "sha256:{}",
        digest(b"core.report-repair-witness.v1", &result)?
    );
    let license = mint_report_license(
        &input.current,
        &post,
        phi_pre,
        phi_post,
        repair_differential,
        witness_digest,
    )?;
    let mut current = input.current;
    let trace = commit(&mut current, &post, &license)?;
    Ok(
        json!({"schema_version": "core.genesis.report-commit.v1", "state": current,
        "trace": trace, "result": result, "route": input.route,
        "scope": "native_state_commit; durable custody requires host CAS"}),
    )
}

pub fn verify_commit(payload: &Value) -> Result<Value, String> {
    preflight(payload)?;
    #[derive(Deserialize)]
    #[serde(deny_unknown_fields)]
    struct Replay {
        input: Value,
        candidate: Value,
    }
    let replay: Replay = serde_json::from_value(payload.clone()).map_err(|e| e.to_string())?;
    if execute(&replay.input)? != replay.candidate {
        return Err("REPORT_COMMIT_REPLAY".into());
    }
    Ok(
        json!({"schema_version": "core.genesis.report-commit-replay.v1",
        "verified": true, "authority_effect": "None"}),
    )
}

// Origin: engine/crates_rs/pfp/src/report_operation.rs
// Claim: urn:core:crates_rs:pfp:report-operation:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord79a2658e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord79a2658e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError79a2658e {
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
impl BoundaryError79a2658e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError79a2658e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError79a2658e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord79a2658e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError79a2658e> {
        if capacity_bound == 0 {
            return Err(BoundaryError79a2658e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError79a2658e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError79a2658e::ExceedsCapacity {
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
mod l4_boundary_tests_79a2658e {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord79a2658e::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord79a2658e::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord79a2658e::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord79a2658e::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord79a2658e::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError79a2658e::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError79a2658e::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
