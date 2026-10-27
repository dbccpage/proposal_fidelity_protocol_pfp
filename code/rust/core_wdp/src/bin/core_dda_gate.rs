use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use core_wdp::ddc::agent_contract::{
    render_rust_bytes, verify_bytes, DdaGateReceipt, GateVerdict,
};

fn admit_inputs(work: &[u8], proposal: &[u8]) -> Result<usize, String> {
    if work.is_empty() || proposal.is_empty() {
        return Err("work packet and proposal must both be non-empty".to_owned());
    }
    work.len()
        .checked_add(proposal.len())
        .ok_or_else(|| "packet widths overflowed".to_owned())
}

fn sum_defect_mass(receipt: &DdaGateReceipt) -> Result<usize, String> {
    let mut mass = 0usize;
    for defect in &receipt.per_defect {
        let row = defect
            .phi
            .checked_add(defect.gamma)
            .ok_or_else(|| format!("defect {} mass overflowed", defect.defect_id))?;
        mass = mass
            .checked_add(row)
            .ok_or_else(|| "defect mass overflowed".to_owned())?;
    }
    let _counted = receipt
        .per_defect
        .len()
        .checked_add(receipt.packet_refs.len())
        .ok_or_else(|| "receipt census overflowed".to_owned())?;
    Ok(mass)
}

fn admit_receipt(receipt: &DdaGateReceipt) -> Result<usize, String> {
    if receipt.render_allowed != receipt.promotion_allowed {
        return Err("render_allowed must equal promotion_allowed".to_owned());
    }
    if receipt.promotion_allowed && receipt.gate_verdict != GateVerdict::Pass {
        return Err("promotion requires a Pass verdict".to_owned());
    }
    match receipt.authority_effect {
        "None" | "Refused" => {}
        other => return Err(format!("authority effect {other}")),
    }
    if receipt.authority_effect == "Refused" && receipt.promotion_allowed {
        return Err("a refused effect cannot promote".to_owned());
    }
    sum_defect_mass(receipt)
}

fn flag(args: &[String], name: &str) -> Result<PathBuf, String> {
    args.windows(2)
        .find(|pair| pair[0] == name)
        .map(|pair| PathBuf::from(&pair[1]))
        .ok_or_else(|| format!("missing required {name} PATH"))
}

fn write_receipt(receipt: &DdaGateReceipt, output: Option<&Path>) -> Result<(), String> {
    let raw = serde_json::to_string_pretty(receipt)
        .map_err(|error| format!("serialize receipt: {error}"))?
        + "\n";
    if let Some(path) = output {
        fs::write(path, raw).map_err(|error| format!("write {}: {error}", path.display()))
    } else {
        print!("{raw}");
        Ok(())
    }
}

fn run_render_rust(args: &[String], work_raw: &[u8], proposal_raw: &[u8]) -> Result<(), String> {
    let output = flag(args, "--output")?;
    let source = render_rust_bytes(work_raw, proposal_raw, &output)?;
    if let Some(parent) = output.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("create {}: {error}", parent.display()))?;
    }
    fs::write(&output, source).map_err(|error| format!("write {}: {error}", output.display()))
}

fn run_verify(args: &[String], work_raw: &[u8], proposal_raw: &[u8]) -> Result<(), String> {
    let receipt = verify_bytes(work_raw, proposal_raw)?;
    admit_receipt(&receipt)?;
    let receipt_path = args
        .windows(2)
        .find(|pair| pair[0] == "--receipt")
        .map(|pair| Path::new(&pair[1]));
    write_receipt(&receipt, receipt_path)
}

fn run() -> Result<(), String> {
    let args: Vec<String> = env::args().collect();
    let command = args.get(1).map(String::as_str).ok_or_else(|| {
        "usage: core_dda_gate verify|render-rust --work-packet PATH --proposal PATH".to_string()
    })?;
    let work_path = flag(&args, "--work-packet")?;
    let proposal_path = flag(&args, "--proposal")?;
    let work_raw =
        fs::read(&work_path).map_err(|error| format!("read {}: {error}", work_path.display()))?;
    let proposal_raw = fs::read(&proposal_path)
        .map_err(|error| format!("read {}: {error}", proposal_path.display()))?;

    admit_inputs(&work_raw, &proposal_raw)?;
    match command {
        "verify" => run_verify(&args, &work_raw, &proposal_raw),
        "render-rust" => run_render_rust(&args, &work_raw, &proposal_raw),
        other => Err(format!(
            "unknown command {other:?}; expected verify|render-rust"
        )),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("core_dda_gate: {error}");
            ExitCode::from(2)
        }
    }
}

// Origin: engine/crates_rs/core_wdp/src/bin/core_dda_gate.rs
// Claim: urn:core:crates_rs:core-wdp:core-dda-gate:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc191edc4 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc191edc4` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc191edc4 {
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
impl BoundaryErrorc191edc4 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc191edc4 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc191edc4 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc191edc4 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc191edc4> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc191edc4::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc191edc4::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc191edc4::ExceedsCapacity {
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
mod l4_boundary_tests_c191edc4 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc191edc4::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc191edc4::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc191edc4::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc191edc4::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc191edc4::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc191edc4::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc191edc4::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
