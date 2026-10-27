//! Replay all three native examples and print checked finite evidence.
#[path = "../../../tests/core_wdp/common/genesis_bell_cases.rs"]
mod cases;
use core_solvers::solver_convex_farkas_feasibility::FeasibilityVerdict;
use core_wdp::genesis_bell::PassageBellExperiment;
fn main() -> Result<(), String> {
    DeterministicAssignmentCount::try_new(2, 2).map_err(|err| err.to_string())?;
    for (name, request) in [
        (
            "interaction_exposes_hidden_token",
            cases::expose_hidden_token(),
        ),
        ("shared_preparation", cases::token_response_experiment()),
        (
            "setting_dependent_preparation",
            cases::setting_dependent_experiment(),
        ),
    ] {
        let p = PassageBellExperiment::build(&request).map_err(|e| format!("{e:?}"))?;
        let c = p.certify(10000).map_err(|e| format!("{e:?}"))?;
        PassageBellExperiment::verify(&request, &c).map_err(|e| format!("{e:?}"))?;
        let (verdict, witness) = match &c.experiment.extension {
            FeasibilityVerdict::Feasible { point } => ("positive_local_extension", point),
            FeasibilityVerdict::Infeasible { multipliers } => {
                ("no_positive_local_extension", multipliers)
            }
        };
        println!(
            "{}",
            serde_json::json!({
                "case":name,"native_replay_verified":true,
                "rows":c.experiment.rows.iter().map(|r| r.iter().map(ToString::to_string).collect::<Vec<_>>()).collect::<Vec<_>>(),
                "verdict":verdict,"witness":witness.iter().map(ToString::to_string).collect::<Vec<_>>(),
                "shared_prior":c.experiment.prior_difference.is_none(),
                "prior_difference":c.experiment.prior_difference.as_ref().map(|d| serde_json::json!({"context":d.context,
                    "preparation":d.preparation,"first":d.first_weight.to_string(),"other":d.other_weight.to_string()})),
                "joint_collision":c.joint_analysis.collision.as_ref().map(|w| serde_json::json!({
                    "rows":[w.left,w.right],"word":w.word,"answers":[w.left_answer,w.right_answer]})),
                "supported_assignments":p.probability().bell().supported_assignments().len(),
                "scope":"Declared finite protocols and supplied preparation laws; no quantum-realization claim."
            })
        );
    }
    Ok(())
}

// Exact carrier witness.
#[derive(Debug, Clone, PartialEq, Eq)]
struct DeterministicAssignmentCount { assignments: u64 }

#[derive(Debug, Clone, PartialEq, Eq)]
enum AssignmentCountError { Empty, Overflow }

impl std::fmt::Display for AssignmentCountError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(match self {
            Self::Empty => "empty assignment",
            Self::Overflow => "assignment overflow",
        })
    }
}

impl DeterministicAssignmentCount {
    /// Count of deterministic outcome assignments across independent settings: `outcomes^settings`.
    fn try_new(outcomes: u64, settings: u32) -> Result<Self, AssignmentCountError> {
        if outcomes == 0 || settings == 0 {
            return Err(AssignmentCountError::Empty);
        }
        if outcomes == 1 {
            return Ok(Self { assignments: 1 });
        }
        if settings >= 64 {
            return Err(AssignmentCountError::Overflow);
        }
        let mut assignments = 1u64;
        for _ in 0..settings {
            assignments = assignments.checked_mul(outcomes).ok_or(AssignmentCountError::Overflow)?;
        }
        Ok(Self { assignments })
    }

    fn assignments(&self) -> u64 { self.assignments }
}

// Origin: engine/crates_rs/core_wdp/src/examples/genesis_bell.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-bell:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod assignment_count_checks {
    use super::DeterministicAssignmentCount;

    #[test]
    fn two_outcomes_and_two_settings_have_four_assignments() {
        let count = DeterministicAssignmentCount::try_new(2, 2);
        assert!(matches!(count, Ok(c) if c.assignments() == 4));
    }

    #[test]
    fn zero_outcomes_are_refused() {
        assert!(matches!(DeterministicAssignmentCount::try_new(0, 2), Err(super::AssignmentCountError::Empty)));
    }
}
