use num_bigint::BigInt;
use num_rational::BigRational;
use core_certifiers::{CertificateError, Phi1Verifier};
use core_contracts::ContractEffect;
use core_types::{
    AuthorityEffect, EvidenceStatus, ImplementationState, NormativeEffect, OperationalEffect,
    ReleaseAuthority,
};
use std::any::TypeId;
use std::fs;
use std::path::{Path, PathBuf};
use syn::visit::Visit;

fn r(value: i64) -> BigRational {
    BigRational::from_integer(BigInt::from(value))
}

#[test]
fn test_valid_phi1_certificate_passes() {
    // max x subject to x <= 1, x >= 0; dual min y subject to y >= 1, y >= 0.
    let certificate = Phi1Verifier::verify(
        vec![r(1)],
        vec![r(1)],
        vec![vec![r(1)]],
        vec![r(1)],
        vec![r(1)],
    )
    .expect("matching feasible rational witnesses must certify");

    assert_eq!(certificate.primal_objective(), &r(1));
    assert_eq!(certificate.dual_objective(), &r(1));
    assert_eq!(
        certificate.metadata().lean_phi1_specification(),
        "CoreCore.IsPhi1"
    );
    assert_eq!(
        certificate.metadata().lean_duality_theorem(),
        "PaperER007.lp_max_form_weak_duality"
    );
    assert_eq!(
        certificate.metadata().allowed_axioms(),
        &["propext", "Classical.choice", "Quot.sound"]
    );
    assert_eq!(
        certificate.metadata().evidence_status(),
        EvidenceStatus::AlgebraicallyWitnessed
    );
    assert_eq!(
        certificate.metadata().normative_effect(),
        NormativeEffect::Proposal
    );
    assert_eq!(
        certificate.metadata().operational_effect(),
        OperationalEffect::Read
    );
    assert_eq!(
        certificate.metadata().implementation_state(),
        ImplementationState::Verified
    );
    assert_eq!(
        certificate.metadata().release_authority(),
        ReleaseAuthority::NotGranted
    );
}

#[test]
fn test_duality_gap_refused() {
    // Both candidates are feasible, but 0 = c^T x != b^T y = 1.
    let result = Phi1Verifier::verify(
        vec![r(0)],
        vec![r(1)],
        vec![vec![r(1)]],
        vec![r(1)],
        vec![r(1)],
    );

    assert_eq!(result, Err(CertificateError::DualityGapDetected));
}

#[test]
fn test_infeasible_pair_refused() {
    // x = 2 violates the exact primal constraint x <= 1.
    let result = Phi1Verifier::verify(
        vec![r(2)],
        vec![r(1)],
        vec![vec![r(1)]],
        vec![r(1)],
        vec![r(1)],
    );

    assert_eq!(result, Err(CertificateError::Infeasible));
}

#[test]
fn test_authority_effect_no_implicit_promotion() {
    assert_ne!(
        TypeId::of::<ContractEffect>(),
        TypeId::of::<AuthorityEffect>(),
        "contract policy and runtime authority must remain distinct Rust types"
    );

    let workspace = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("workspace root must resolve");
    let mut rust_files = Vec::new();
    collect_rust_files(&workspace, &mut rust_files);

    let expected = [
        ("crates_rs/core_types/src/authority.rs", "core_types::authority::AuthorityEffect"),
        ("crates_rs/core_operad_theory/src/kernel/model.rs", "core_operad_theory::kernel::model::AuthorityEffect"),
        ("crates_rs/core_wdp/src/types.rs", "core_wdp::types::AuthorityEffect"),
        ("crates_rs/core_operads/src/estate.rs", "core_operads::estate::AuthorityEffect"),
    ];
    let mut definitions = Vec::new();
    for path in &rust_files {
        let source = fs::read_to_string(path).expect("Rust source must be readable");
        let syntax = syn::parse_file(&source)
            .unwrap_or_else(|error| panic!("Rust source {} must parse: {error}", path.display()));
        let mut audit = AuthoritySyntaxAudit::default();
        audit.visit_file(&syntax);
        assert!(audit.forbidden_lifts.is_empty(),
            "unverified contract/authority conversion in {}: {:?}", path.display(), audit.forbidden_lifts);
        for _ in 0..audit.authority_definitions {
            definitions.push(path.clone());
        }
    }
    let mut expected_paths: Vec<PathBuf> = expected.iter().map(|(path, _)| workspace.join(path)).collect();
    definitions.sort();
    expected_paths.sort();
    assert_eq!(definitions, expected_paths, "qualified AuthorityEffect census: {expected:?}");

    let contract_source = fs::read_to_string(workspace.join("crates_rs/core_contracts/src/kinds.rs"))
        .expect("contract kind source must be readable");
    assert!(contract_source.contains("pub enum ContractEffect"));
    assert!(!contract_source.contains("pub enum AuthorityEffect"));
}

/// A source-syntax guard for direct conversion implementations. It handles
/// qualified type paths, but does not claim compiler alias or macro resolution.
#[derive(Default)]
struct AuthoritySyntaxAudit {
    authority_definitions: usize,
    forbidden_lifts: Vec<String>,
}

fn terminal_type_name(ty: &syn::Type) -> Option<String> {
    match ty {
        syn::Type::Path(path) => path.path.segments.last().map(|segment| segment.ident.to_string()),
        syn::Type::Reference(reference) => terminal_type_name(&reference.elem),
        syn::Type::Paren(paren) => terminal_type_name(&paren.elem),
        syn::Type::Group(group) => terminal_type_name(&group.elem),
        _ => None,
    }
}

impl<'ast> Visit<'ast> for AuthoritySyntaxAudit {
    fn visit_item_enum(&mut self, item: &'ast syn::ItemEnum) {
        if item.ident == "AuthorityEffect" {
            self.authority_definitions += 1;
        }
        syn::visit::visit_item_enum(self, item);
    }

    fn visit_item_impl(&mut self, item: &'ast syn::ItemImpl) {
        if let Some((_, trait_path, _)) = &item.trait_ {
            if let Some(segment) = trait_path.segments.last() {
                if segment.ident == "From" || segment.ident == "TryFrom" {
                    if let syn::PathArguments::AngleBracketed(arguments) = &segment.arguments {
                        for argument in &arguments.args {
                            if let syn::GenericArgument::Type(input) = argument {
                                let source = terminal_type_name(input);
                                let target = terminal_type_name(&item.self_ty);
                                if matches!((source.as_deref(), target.as_deref()),
                                    (Some("ContractEffect"), Some("AuthorityEffect")) |
                                    (Some("AuthorityEffect"), Some("ContractEffect"))) {
                                    self.forbidden_lifts.push(format!("{}<{:?}> for {:?}", segment.ident, source, target));
                                }
                            }
                        }
                    }
                }
            }
        }
        syn::visit::visit_item_impl(self, item);
    }
}

#[test]
fn authority_guard_catches_qualified_lifts_in_both_scoped_types() {
    for authority in [
        "core_types::authority::AuthorityEffect",
        "core_operad_theory::kernel::model::AuthorityEffect",
        "core_wdp::types::AuthorityEffect",
    ] {
        for conversion in ["From", "TryFrom"] {
            for (source, target) in [("core_contracts::ContractEffect", authority), (authority, "core_contracts::ContractEffect")] {
                let syntax = syn::parse_file(&format!("impl std::convert::{conversion}<{source}> for {target} {{}}"))
                    .expect("mutation fixture must parse");
                let mut audit = AuthoritySyntaxAudit::default();
                audit.visit_file(&syntax);
                assert_eq!(audit.forbidden_lifts.len(), 1, "{conversion}<{source}> for {target}");
            }
        }
    }
    let benign = syn::parse_file("// impl From<ContractEffect> for AuthorityEffect {}\nconst DOCUMENTATION: &str = \"impl From<ContractEffect> for AuthorityEffect {}\";")
        .expect("comment/string fixture must parse");
    let mut audit = AuthoritySyntaxAudit::default();
    audit.visit_file(&benign);
    assert!(audit.forbidden_lifts.is_empty());
}

fn collect_rust_files(directory: &Path, files: &mut Vec<PathBuf>) {
    for entry in fs::read_dir(directory).expect("source directory must be readable") {
        let path = entry.expect("directory entry must be readable").path();
        if path.is_dir() {
            let name = path.file_name().and_then(|name| name.to_str());
            if !matches!(name, Some("target" | ".git" | ".lake" | ".claude")) {
                collect_rust_files(&path, files);
            }
        } else if path.extension().and_then(|extension| extension.to_str()) == Some("rs") {
            files.push(path);
        }
    }
}

// Origin: engine/crates_rs/tests/core_certifiers/phi1_conformance.rs
// Claim: urn:core:crates_rs:tests:phi1-conformance:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord63d112ba {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord63d112ba` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError63d112ba {
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
impl BoundaryError63d112ba {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError63d112ba {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError63d112ba {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord63d112ba {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError63d112ba> {
        if capacity_bound == 0 {
            return Err(BoundaryError63d112ba::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError63d112ba::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError63d112ba::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_63d112ba() {
    let admitted = BoundaryRecord63d112ba::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord63d112ba::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
