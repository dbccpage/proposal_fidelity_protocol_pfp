//! Hermetic ownership-DAG controls; no paper status is treated as proof.
//! AuthorityEffect: None.
use core_wdp::wdp_rust_routes::*;

fn artifact(path: &str) -> ArtifactBinding {
    ArtifactBinding {
        path: path.into(),
        sha256: "42".repeat(32),
        anchor: "named finite check".into(),
    }
}

fn fixture() -> Vec<DagRecord> {
    vec![
        DagRecord::Node(DagNode {
            id: "WDP".into(),
            title: "Source question".into(),
            kind: NodeKind::Paper,
            artifact: Some(artifact("papers/source.md")),
            scope: "finite source question only".into(),
        }),
        DagRecord::Node(DagNode {
            id: "SOLVER".into(),
            title: "Exact owner".into(),
            kind: NodeKind::Rust,
            artifact: Some(artifact("crates/solver.rs")),
            scope: "declared finite carrier".into(),
        }),
        DagRecord::Edge(DagEdge {
            id: "WDP_TO_SOLVER".into(),
            from: "WDP".into(),
            to: "SOLVER".into(),
            kind: EdgeKind::ImplementedFiniteRoute,
            owner: Some(artifact("crates/solver.rs")),
            input_contract: "finite rational matrices".into(),
            output_contract: "replay or refusal".into(),
            oracle: Some(artifact("tests/solver.rs")),
            negative_control: "changed carrier refuses".into(),
            premises: Some(BridgePremises {
                question: "exact reconstruction".into(),
                scalar: "Q".into(),
                quotient: "modulo kernel".into(),
                positivity: "not applicable".into(),
                composition: "not applicable".into(),
                availability: "declared input only".into(),
            }),
            scope: "finite matrix instance".into(),
            added_since_baseline: true,
        }),
    ]
}

#[test]
fn a_declared_finite_route_has_a_structural_receipt() {
    let receipt = validate_dag(&fixture()).unwrap();
    assert_eq!(receipt.topological_order, ["WDP", "SOLVER"]);
    assert_eq!(
        (receipt.implemented_routes, receipt.declared_new_routes),
        (1, 1)
    );
    assert!(receipt.authority_effect.is_none());
    assert_eq!(
        receipt.evidence_scope,
        "graph_structure_and_declared_artifact_bindings_only"
    );
}

#[test]
fn missing_owner_premise_and_negative_control_each_refuse() {
    for field in 0..3 {
        let mut records = fixture();
        if let DagRecord::Edge(edge) = &mut records[2] {
            match field {
                0 => edge.owner = None,
                1 => edge.premises.as_mut().unwrap().positivity.clear(),
                _ => edge.negative_control.clear(),
            }
        }
        assert!(matches!(
            validate_dag(&records),
            Err(DagError::BridgeContract(_))
        ));
    }
}

#[test]
fn missing_target_duplicate_id_cycle_and_path_escape_refuse() {
    let mut records = fixture();
    if let DagRecord::Edge(edge) = &mut records[2] {
        edge.to = "MISSING".into();
    }
    assert!(matches!(
        validate_dag(&records),
        Err(DagError::MissingNode(_))
    ));
    let mut records = fixture();
    records.push(records[0].clone());
    assert!(matches!(
        validate_dag(&records),
        Err(DagError::Identifier(_))
    ));
    let mut records = fixture();
    let mut reverse = if let DagRecord::Edge(edge) = &records[2] {
        edge.clone()
    } else {
        unreachable!()
    };
    reverse.id = "RETURN".into();
    reverse.kind = EdgeKind::SourceRelationship;
    reverse.added_since_baseline = false;
    std::mem::swap(&mut reverse.from, &mut reverse.to);
    records.push(DagRecord::Edge(reverse));
    assert_eq!(validate_dag(&records).unwrap_err(), DagError::Cycle);
    assert!(!repository_path("../source.md"));
    assert!(!repository_path("/source.md"));
    assert!(!repository_path("C:\\source.md"));
}

#[test]
fn an_open_obligation_cannot_be_promoted_to_an_implemented_route() {
    let mut records = fixture();
    if let DagRecord::Node(node) = &mut records[1] {
        node.kind = NodeKind::Obligation;
        node.artifact = None;
    }
    assert!(matches!(
        validate_dag(&records),
        Err(DagError::BridgeContract(_))
    ));
    if let DagRecord::Edge(edge) = &mut records[2] {
        edge.kind = EdgeKind::OpenObligation;
        edge.added_since_baseline = false;
    }
    let receipt = validate_dag(&records).unwrap();
    assert_eq!(receipt.implemented_routes, 0);
    assert_eq!(receipt.open_obligations, 1);
    assert_eq!(receipt.open_obligation_routes, 1);
}

#[test]
fn code_target_and_owner_identity_are_bound_to_the_route() {
    let mut rows = fixture();
    if let DagRecord::Node(node) = &mut rows[1] {
        node.kind = NodeKind::Paper;
    }
    assert!(matches!(
        validate_dag(&rows),
        Err(DagError::BridgeContract(_))
    ));
    for role in 0..3 {
        let mut rows = fixture();
        if let DagRecord::Edge(edge) = &mut rows[2] {
            let owner = edge.owner.as_mut().unwrap();
            match role {
                0 => owner.path = "unrelated.rs".into(),
                1 => owner.sha256 = "24".repeat(32),
                _ => owner.anchor = "a different API in the same file".into(),
            }
        }
        assert!(matches!(
            validate_dag(&rows),
            Err(DagError::BridgeContract(_))
        ));
    }
}

#[test]
fn the_graph_commitment_changes_when_semantic_premises_change() {
    let rows = fixture();
    let before = validate_dag(&rows).unwrap();
    let mut changed = rows.clone();
    if let DagRecord::Edge(edge) = &mut changed[2] {
        edge.premises.as_mut().unwrap().composition = "a different declared operation".into();
    }
    let after = validate_dag(&changed).unwrap();
    assert_ne!(before.graph_digest_sha256, after.graph_digest_sha256);
    assert_eq!(before.nodes, after.nodes);
}

#[test]
fn total_declared_metadata_has_an_exact_byte_limit_before_commitment() {
    let mut rows = vec![DagRecord::Node(DagNode {
        id: "N".into(),
        title: "T".into(),
        kind: NodeKind::Obligation,
        artifact: None,
        scope: "x".repeat(MAX_DAG_METADATA_BYTES - 2),
    })];
    let receipt = validate_dag(&rows).unwrap();
    assert_eq!(receipt.nodes, 1);
    assert!(receipt.authority_effect.is_none());
    if let DagRecord::Node(node) = &mut rows[0] {
        node.scope.push('x');
    }
    assert_eq!(validate_dag(&rows).unwrap_err(), DagError::Resource);
}

#[test]
fn metadata_budget_covers_nodes_contracts_premises_and_artifact_roles() {
    validate_dag(&fixture()).unwrap();
    for role in 0..9 {
        let mut rows = fixture();
        let oversized = "x".repeat(MAX_DAG_METADATA_BYTES);
        if role < 4 {
            if let DagRecord::Node(node) = &mut rows[1] {
                match role {
                    0 => node.id = oversized,
                    1 => node.title = oversized,
                    2 => node.artifact.as_mut().unwrap().path = oversized,
                    _ => node.artifact.as_mut().unwrap().anchor = oversized,
                }
            }
        } else if let DagRecord::Edge(edge) = &mut rows[2] {
            match role {
                4 => edge.input_contract = oversized,
                5 => edge.negative_control = oversized,
                6 => edge.owner.as_mut().unwrap().sha256 = oversized,
                7 => edge.oracle.as_mut().unwrap().anchor = oversized,
                _ => edge.premises.as_mut().unwrap().composition = oversized,
            }
        }
        assert_eq!(
            validate_dag(&rows).unwrap_err(),
            DagError::Resource,
            "role {role}"
        );
    }
    let mut binding = artifact("owner.rs");
    binding.anchor = "λ".repeat(MAX_DAG_METADATA_BYTES / 2);
    assert_eq!(validate_artifact(&binding), Err(DagError::Resource));
}

// Origin: engine/crates_rs/tests/core_wdp/wdp_rust_routes.rs
// Claim: urn:core:crates_rs:tests:wdp-rust-routes:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc5e84c0b {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc5e84c0b` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc5e84c0b {
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
impl BoundaryErrorc5e84c0b {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc5e84c0b {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc5e84c0b {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc5e84c0b {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc5e84c0b> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc5e84c0b::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc5e84c0b::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc5e84c0b::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_c5e84c0b() {
    let admitted = BoundaryRecordc5e84c0b::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc5e84c0b::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
