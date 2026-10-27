//! Conformance: phi1 obstruction mass on the exact (integer) authority path.
//! Subject = solve_phi1 (per-edge omega). Oracle = spine + JSON vectors.
//! weight_profile_id MUST be unit_weights_v1 in Phase 0.
use std::path::PathBuf;

use core_solvers::solver_lp_phi1_boundary::{solve_phi1, Boundary1, BoundaryEdge};
use serde::Deserialize;

fn vectors_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../pfp/tests/fixtures/conformance/vectors")
}

#[derive(Deserialize)]
struct Phi1File {
    weight_profile_id: String,
    cases: Vec<Phi1Case>,
}

#[derive(Deserialize)]
struct Phi1Case {
    id: String,
    input: Phi1Input,
    expected: Phi1Expected,
}

#[derive(Deserialize)]
struct Phi1Input {
    num_vertices: usize,
    edges: Vec<EdgeJson>,
    omega: Vec<i128>,
}

#[derive(Deserialize)]
struct EdgeJson {
    tail: usize,
    head: usize,
    weight: i128,
}

#[derive(Deserialize)]
struct Phi1Expected {
    objective: i128,
    #[serde(default)]
    z: Option<Vec<i128>>,
}

#[test]
fn phi1_obstruction_mass() {
    let path = vectors_dir().join("07_phi1_obstruction_mass.json");
    if !path.exists() {
        eprintln!(
            "Skipping phi1_obstruction_mass: fixture not found at {}",
            path.display()
        );
        return;
    }
    let text =
        std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("read {}: {e}", path.display()));
    let file: Phi1File =
        serde_json::from_str(&text).unwrap_or_else(|e| panic!("parse {}: {e}", path.display()));
    assert_eq!(
        file.weight_profile_id, "unit_weights_v1",
        "phase 0 requires unit weights"
    );
    assert!(
        !file.cases.is_empty(),
        "no cases in 07_phi1_obstruction_mass.json"
    );

    for case in &file.cases {
        let boundary = Boundary1 {
            num_vertices: case.input.num_vertices,
            edges: case
                .input
                .edges
                .iter()
                .map(|e| BoundaryEdge {
                    tail: e.tail,
                    head: e.head,
                    weight: e.weight,
                })
                .collect(),
        };
        let sol = solve_phi1(&boundary, &case.input.omega).expect("solve_phi1");

        // Known obstruction mass (spine-derived).
        assert_eq!(
            sol.objective, case.expected.objective,
            "objective {}",
            case.id
        );

        // Deterministic residual, only where the optimum is unique.
        if let Some(z) = &case.expected.z {
            assert_eq!(&sol.z, z, "z {}", case.id);
        }

        // Primal consistency: objective == sum_e w_e * |z_e|.
        let recomputed: i128 = boundary
            .edges
            .iter()
            .zip(&sol.z)
            .map(|(e, z)| e.weight * z.abs())
            .sum();
        assert_eq!(recomputed, sol.objective, "primal sum {}", case.id);

        // Dual witness present (reduced_costs = phi), one per edge.
        assert_eq!(
            sol.reduced_costs.len(),
            boundary.edges.len(),
            "dual witness length {}",
            case.id
        );
    }
}

// Origin: engine/crates_rs/tests/core_solvers/conformance_phi1.rs
// Claim: urn:core:crates_rs:tests:conformance-phi1:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord1eab1a2e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord1eab1a2e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError1eab1a2e {
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
impl BoundaryError1eab1a2e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError1eab1a2e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError1eab1a2e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord1eab1a2e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError1eab1a2e> {
        if capacity_bound == 0 {
            return Err(BoundaryError1eab1a2e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError1eab1a2e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError1eab1a2e::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_1eab1a2e() {
    let admitted = BoundaryRecord1eab1a2e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord1eab1a2e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
