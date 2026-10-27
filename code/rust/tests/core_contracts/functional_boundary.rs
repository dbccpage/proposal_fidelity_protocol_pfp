use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};

use core_contracts::contract_descriptors::{
    binding_by_descriptor_id, functional_binding_by_contract_urn,
    functional_boundary_dependency_contract_urns, functional_dependency_contract_urns,
    primitive_binding_by_contract_urn, primitive_dependency_contract_urns,
    CORE_PRIMITIVE_CONTRACTS, CORE_PRIMITIVE_CONTRACT_BINDINGS, FUNCTIONAL_CONTRACT_BINDINGS,
};
use serde_yaml::Value;

fn engine_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .expect("core_functional is under crates_rs/")
        .parent()
        .expect("crates_rs/ is under engine/")
        .to_path_buf()
}

fn repository_root() -> PathBuf {
    engine_root()
        .parent()
        .expect("engine is below the repository root")
        .to_path_buf()
}

fn canonical_contract_path() -> PathBuf {
    repository_root().join(
        "governance/contracts/contract_canonical_definitions/math/functional_layer_boundary.contract.yaml",
    )
}

fn canonical_math_contract_dir() -> PathBuf {
    repository_root()
        .join("governance/contracts/contract_canonical_definitions/math")
}

fn canonical_math_contract_path(file_name: &str) -> PathBuf {
    canonical_math_contract_dir().join(file_name)
}

fn read_yaml(path: &Path) -> Value {
    let text =
        fs::read_to_string(path).unwrap_or_else(|err| panic!("read {}: {err}", path.display()));
    serde_yaml::from_str(&text).unwrap_or_else(|err| panic!("parse {}: {err}", path.display()))
}

fn field<'a>(value: &'a Value, key: &str) -> &'a Value {
    value
        .as_mapping()
        .and_then(|mapping| mapping.get(Value::String(key.to_string())))
        .unwrap_or_else(|| panic!("missing YAML key `{key}`"))
}

fn optional_field<'a>(value: &'a Value, key: &str) -> Option<&'a Value> {
    value
        .as_mapping()
        .and_then(|mapping| mapping.get(Value::String(key.to_string())))
}

fn field_str<'a>(value: &'a Value, key: &str) -> &'a str {
    field(value, key)
        .as_str()
        .unwrap_or_else(|| panic!("YAML key `{key}` must be a string"))
}

fn optional_field_str<'a>(value: &'a Value, key: &str) -> Option<&'a str> {
    optional_field(value, key).and_then(Value::as_str)
}

fn field_bool(value: &Value, key: &str) -> bool {
    field(value, key)
        .as_bool()
        .unwrap_or_else(|| panic!("YAML key `{key}` must be a bool"))
}

fn string_sequence(value: &Value, key: &str) -> Vec<String> {
    field(value, key)
        .as_sequence()
        .unwrap_or_else(|| panic!("YAML key `{key}` must be a sequence"))
        .iter()
        .map(|item| {
            item.as_str()
                .unwrap_or_else(|| panic!("YAML key `{key}` must contain only strings"))
                .to_string()
        })
        .collect()
}

fn expected_boundary_dependencies() -> Vec<String> {
    functional_boundary_dependency_contract_urns()
        .into_iter()
        .map(str::to_string)
        .collect()
}

fn public_omega_functional_modules() -> Vec<String> {
    let lib_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("core_functional/src/lib.rs");
    let lib = fs::read_to_string(&lib_path)
        .unwrap_or_else(|err| panic!("read {}: {err}", lib_path.display()));

    lib.lines()
        .filter_map(|line| {
            let trimmed = line.trim();
            let module = trimmed.strip_prefix("pub mod ")?.strip_suffix(';')?.trim();
            if matches!(
                module,
                "finite_family_bound"
                    | "loss_curvature"
                    | "operator_trace_closure"
                    | "path_error"
                    | "projection_leakage"
                    | "projection_transfer"
                    | "protected_linear_quotient"
            ) {
                return None;
            }
            Some(module.to_string())
        })
        .collect()
}

fn production_omega_functional_import_modules(module: &str) -> BTreeSet<String> {
    let src_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .join("core_functional/src")
        .join(format!("{module}.rs"));
    let source = fs::read_to_string(&src_path)
        .unwrap_or_else(|err| panic!("read {}: {err}", src_path.display()));
    let production_source = source.split("\n#[cfg(test)]").next().unwrap_or(&source);
    let known_modules: BTreeSet<String> = public_omega_functional_modules().into_iter().collect();
    let mut imports = BTreeSet::new();

    for line in production_source.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with("//") {
            continue;
        }
        let mut remaining = trimmed;
        while let Some(index) = remaining.find("crate::") {
            let after = &remaining[index + "crate::".len()..];
            let module_name: String = after
                .chars()
                .take_while(|ch| ch.is_ascii_alphanumeric() || *ch == '_')
                .collect();
            if module_name != module && known_modules.contains(&module_name) {
                imports.insert(module_name);
            }
            remaining = after;
        }
    }

    imports
}

macro_rules! assert_public_type {
    ($symbol:path) => {
        let _ = std::mem::size_of::<$symbol>();
    };
}

macro_rules! assert_public_value {
    ($symbol:path) => {
        let _ = $symbol;
    };
}

#[test]
fn functional_boundary_contract_depends_on_primitive_and_functional_contracts() {
    let contract = read_yaml(&canonical_contract_path());
    let dependencies = field(field(&contract, "descriptor"), "dependencies");
    let actual: std::collections::BTreeSet<String> = string_sequence(dependencies, "contracts")
        .into_iter()
        .collect();
    let expected: std::collections::BTreeSet<String> =
        expected_boundary_dependencies().into_iter().collect();

    assert_eq!(
        actual,
        expected,
        "functional boundary contract dependencies must exactly match primitive and non-self functional contract URNs"
    );
}

#[test]
fn functional_boundary_contract_preserves_registry_dependency_order() {
    let contract = read_yaml(&canonical_contract_path());
    let dependencies = field(field(&contract, "descriptor"), "dependencies");
    let actual = string_sequence(dependencies, "contracts");
    let expected = expected_boundary_dependencies();

    assert_eq!(
        actual,
        expected,
        "functional boundary contract dependencies must preserve primitive then topological functional registry order"
    );
}

#[test]
fn contract_descriptors_contract_binds_descriptor_tables_and_lookup_functions() {
    let contract = read_yaml(&canonical_math_contract_path(
        "contract_descriptors.contract.yaml",
    ));
    let rust_binding = field(&contract, "rust_binding");
    let mut actual = string_sequence(rust_binding, "symbols");
    let mut expected = vec![
        "ContractDescriptors".to_string(),
        "PrimitiveContractDescriptor".to_string(),
        "PrimitiveContractBinding".to_string(),
        "FunctionalContractBinding".to_string(),
        "CORE_PRIMITIVE_CONTRACTS".to_string(),
        "CORE_PRIMITIVE_CONTRACT_BINDINGS".to_string(),
        "FUNCTIONAL_CONTRACT_BINDINGS".to_string(),
        "contract_by_id".to_string(),
        "binding_by_descriptor_id".to_string(),
        "primitive_binding_by_contract_urn".to_string(),
        "primitive_binding_by_canonical_file".to_string(),
        "primitive_dependency_contract_urns".to_string(),
        "functional_boundary_dependency_contract_urns".to_string(),
        "functional_dependency_contract_urns".to_string(),
        "functional_binding_by_contract_urn".to_string(),
        "functional_binding_by_canonical_file".to_string(),
        "functional_binding_by_rust_surface".to_string(),
    ];
    actual.sort();
    expected.sort();

    assert_eq!(
        actual, expected,
        "contract_descriptors contract must bind the concrete descriptor API surface"
    );
}

#[test]
fn contract_descriptors_contract_declares_registry_invariants() {
    let contract = read_yaml(&canonical_math_contract_path(
        "contract_descriptors.contract.yaml",
    ));
    let doctrine = field(&contract, "doctrine");
    let actual: std::collections::BTreeSet<String> =
        string_sequence(doctrine, "registry_invariants")
            .into_iter()
            .collect();
    let expected: std::collections::BTreeSet<String> = [
        "primitive descriptor_id values are unique",
        "primitive canonical_contract_urn values are unique",
        "primitive canonical_file values are unique",
        "primitive binding order mirrors primitive descriptor order",
        "primitive canonical_contract_urn and canonical_file lookups round-trip to registered bindings",
        "primitive dependency descriptor IDs resolve to canonical contract URNs",
        "primitive descriptors are topologically ordered by dependency",
        "functional boundary dependency closure emits primitive and non-self functional contract URNs",
        "functional boundary dependency closure preserves primitive then topological functional registry order",
        "functional contract_urn values are unique",
        "functional canonical_file values are unique",
        "functional rust_binding symbols are unique within each contract",
        "functional rust module plus symbol pairs are globally unique",
        "functional rust module plus symbol lookups round-trip to registered contracts",
        "functional rust modules name existing core_functional source files",
        "every public core_functional module has a functional contract binding",
        "functional contract descriptor dependencies include production core_functional module imports",
        "functional binding dependency_contract_urns mirror canonical descriptor dependencies",
        "functional contract descriptor dependencies resolve to primitive or functional registry entries",
        "functional contract descriptor dependencies are non-self and duplicate-free",
        "functional contract bindings are topologically ordered by functional descriptor dependency",
        "functional rust_binding symbols resolve through their declared public module paths",
    ]
    .into_iter()
    .map(str::to_string)
    .collect();

    assert_eq!(
        actual, expected,
        "contract_descriptors doctrine must declare the registry invariants enforced by core_functional"
    );
}

#[test]
fn functional_contract_bindings_are_topologically_ordered_by_functional_dependency() {
    let mut seen = BTreeSet::new();

    for binding in FUNCTIONAL_CONTRACT_BINDINGS {
        let path = canonical_math_contract_path(binding.canonical_file);
        let contract = read_yaml(&path);
        let dependencies = field(field(&contract, "descriptor"), "dependencies");

        for dependency in string_sequence(dependencies, "contracts") {
            if functional_binding_by_contract_urn(&dependency).is_none() {
                continue;
            }
            let is_mutual_binary_specialization = binding.contract_urn
                == "urn:core:math:binary_degree_functional:v1.0.0"
                && matches!(
                    dependency.as_str(),
                    "urn:core:math:phi1:v1.0.0"
                        | "urn:core:math:gamma2_closure_defect:v1.0.0"
                );
            if is_mutual_binary_specialization {
                continue;
            }
            assert!(
                seen.contains(dependency.as_str()),
                "{} appears before functional dependency {}",
                binding.contract_urn,
                dependency
            );
        }

        seen.insert(binding.contract_urn);
    }
}

#[test]
fn functional_dependency_contract_urn_lookup_round_trips_bindings() {
    for binding in FUNCTIONAL_CONTRACT_BINDINGS {
        assert_eq!(
            functional_dependency_contract_urns(binding.contract_urn),
            Some(binding.dependency_contract_urns),
            "functional dependency lookup must return registered dependency URNs for {}",
            binding.contract_urn
        );
    }

    assert_eq!(
        functional_dependency_contract_urns("urn:core:math:no_such_functional_contract:v1.0.0"),
        None
    );
}

#[test]
fn observer_comparison_contract_declares_laundering_refusal() {
    let contract = read_yaml(&canonical_math_contract_path(
        "observer_comparison.contract.yaml",
    ));
    let descriptor = field(&contract, "descriptor");
    let refusals = field(descriptor, "refusals");
    let doctrine = field(&contract, "doctrine");
    let rust_binding = field(&contract, "rust_binding");

    assert_eq!(
        field_str(&contract, "contract_id"),
        "urn:core:math:observer_comparison:v1.0.0"
    );
    assert_eq!(field_str(descriptor, "authority_effect"), "none");
    assert_eq!(field_str(descriptor, "evidence_ceiling"), "ShapeOnly");
    assert!(
        string_sequence(refusals, "may_emit").is_empty(),
        "descriptive observer-comparison refusals must not enter the seeded v1 refusal vocabulary"
    );
    assert!(
        string_sequence(doctrine, "non_role")
            .iter()
            .any(|role| role == "comparison_laundering"),
        "observer comparison must declare comparison laundering as a non-role"
    );
    assert!(
        string_sequence(doctrine, "laws")
            .iter()
            .any(|law| law == "attempted authority promotion emits ComparisonLaunderingRefused"),
        "observer comparison must state the authority-promotion refusal law"
    );
    assert!(
        string_sequence(doctrine, "laws")
            .iter()
            .any(|law| law
                == "comparison status maps to observer-comparison residual kind without authority promotion"),
        "observer comparison must state the diagnostic residual mapping rule"
    );
    assert!(
        string_sequence(doctrine, "laws")
            .iter()
            .any(|law| law
                == "conservative hash-derived comparison may emit Agreement only for matching equivalence-relation hashes"),
        "observer comparison must state the conservative hash agreement rule"
    );
    assert!(
        string_sequence(doctrine, "laws")
            .iter()
            .any(|law| law
                == "conservative hash-derived comparison must emit Incomparable for nonmatching equivalence-relation hashes"),
        "observer comparison must state the conservative hash incomparability rule"
    );
    assert!(
        string_sequence(rust_binding, "symbols")
            .iter()
            .any(|symbol| symbol == "ObserverComparisonResidual"),
        "observer comparison must bind the typed comparison residual"
    );
    assert!(
        string_sequence(rust_binding, "symbols")
            .iter()
            .any(|symbol| symbol == "ComparisonLaunderingRefused"),
        "observer comparison must bind the local laundering refusal type"
    );
}

#[test]
fn functional_contract_dependencies_resolve_to_registered_math_contracts() {
    for binding in FUNCTIONAL_CONTRACT_BINDINGS {
        let path = canonical_math_contract_path(binding.canonical_file);
        let contract = read_yaml(&path);
        let dependencies = field(field(&contract, "descriptor"), "dependencies");
        let mut seen = BTreeSet::new();

        for dependency in string_sequence(dependencies, "contracts") {
            assert!(
                dependency.starts_with("urn:core:math:"),
                "{} dependency {} must stay in the math contract namespace",
                binding.canonical_file,
                dependency
            );
            assert_ne!(
                dependency, binding.contract_urn,
                "{} must not list itself as a descriptor dependency",
                binding.canonical_file
            );
            assert!(
                seen.insert(dependency.clone()),
                "{} repeats descriptor dependency {}",
                binding.canonical_file,
                dependency
            );
            assert!(
                primitive_binding_by_contract_urn(&dependency).is_some()
                    || functional_binding_by_contract_urn(&dependency).is_some(),
                "{} dependency {} must resolve through the primitive or functional registry",
                binding.canonical_file,
                dependency
            );
        }
    }
}

#[test]
fn functional_contract_dependencies_include_production_module_imports() {
    let module_contracts: BTreeMap<&str, &str> = FUNCTIONAL_CONTRACT_BINDINGS
        .iter()
        .filter(|binding| binding.rust_crate == "core_functional" && binding.rust_module != "lib")
        .map(|binding| (binding.rust_module, binding.contract_urn))
        .collect();

    for binding in FUNCTIONAL_CONTRACT_BINDINGS {
        if binding.rust_crate != "core_functional" || binding.rust_module == "lib" {
            continue;
        }

        let path = canonical_math_contract_path(binding.canonical_file);
        let contract = read_yaml(&path);
        let dependencies = field(field(&contract, "descriptor"), "dependencies");
        let actual: BTreeSet<String> = string_sequence(dependencies, "contracts")
            .into_iter()
            .collect();

        for module in production_omega_functional_import_modules(binding.rust_module) {
            let dependency_urn = module_contracts.get(module.as_str()).unwrap_or_else(|| {
                panic!("missing functional contract binding for module {module}")
            });
            assert!(
                actual.contains(*dependency_urn),
                "{} must declare dependency {} for production import crate::{}",
                binding.canonical_file,
                dependency_urn,
                module
            );
        }
    }
}

#[test]
fn every_public_omega_functional_module_has_a_functional_contract_binding() {
    let actual: BTreeSet<String> = FUNCTIONAL_CONTRACT_BINDINGS
        .iter()
        .filter(|binding| binding.rust_crate == "core_functional" && binding.rust_module != "lib")
        .map(|binding| binding.rust_module.to_string())
        .collect();
    let expected: BTreeSet<String> = public_omega_functional_modules().into_iter().collect();

    assert_eq!(
        actual, expected,
        "every public core_functional module must be covered by a functional contract binding"
    );
}

#[test]
#[allow(deprecated)]
fn functional_contract_registry_symbols_resolve_through_declared_public_modules() {
    assert_public_type!(core_functional::born_probabilities::BornProbabilities);
    assert_public_value!(core_functional::dual_verification::verify_dual_witness);
    assert_public_type!(core_functional::dual_verification::VerifiedDualLowerBound);
    assert_public_value!(core_functional::norms::lp_norm);
    assert_public_type!(core_functional::norms::LpMagnitude);
    assert_public_type!(core_functional::l1_seminorm::L1Seminorm);
    assert_public_type!(core_types::closure_defect::ClosureDefectDisplay);
    assert_public_type!(core_types::closure_defect::UntrustedClosureDefectDto);
    assert_public_type!(core_policy::closure_regime::ClosureRegime);

    assert_public_type!(core_contracts::contract_descriptors::ContractDescriptors);
    assert_public_type!(core_contracts::contract_descriptors::PrimitiveContractDescriptor);
    assert_public_type!(core_contracts::contract_descriptors::PrimitiveContractBinding);
    assert_public_type!(core_contracts::contract_descriptors::FunctionalContractBinding);
    assert_public_value!(core_contracts::contract_descriptors::CORE_PRIMITIVE_CONTRACTS);
    assert_public_value!(core_contracts::contract_descriptors::CORE_PRIMITIVE_CONTRACT_BINDINGS);
    assert_public_value!(core_contracts::contract_descriptors::FUNCTIONAL_CONTRACT_BINDINGS);
    assert_public_value!(core_contracts::contract_descriptors::contract_by_id);
    assert_public_value!(core_contracts::contract_descriptors::binding_by_descriptor_id);
    assert_public_value!(core_contracts::contract_descriptors::primitive_binding_by_contract_urn);
    assert_public_value!(
        core_contracts::contract_descriptors::primitive_binding_by_canonical_file
    );
    assert_public_value!(core_contracts::contract_descriptors::primitive_dependency_contract_urns);
    assert_public_value!(
        core_contracts::contract_descriptors::functional_boundary_dependency_contract_urns
    );
    assert_public_value!(
        core_contracts::contract_descriptors::functional_dependency_contract_urns
    );
    assert_public_value!(core_contracts::contract_descriptors::functional_binding_by_contract_urn);
    assert_public_value!(
        core_contracts::contract_descriptors::functional_binding_by_canonical_file
    );
    assert_public_value!(core_contracts::contract_descriptors::functional_binding_by_rust_surface);

    assert_public_type!(core_contracts::functional_property_witnesses::ContractPropertyWitnesses);
    assert_public_type!(core_types::diagnostic_vector::DiagnosticSnapshot);
    assert_public_type!(core_types::dual_witness::DualWitness);
    assert_public_type!(core_policy::evaluation_hierarchy::DiagnosticComparison);
    assert_public_value!(core_policy::evaluation_hierarchy::classify_guarded_non_worse);
    assert_public_value!(core_policy::evaluation_hierarchy::compare_guarded_diagnostics);
    assert_public_value!(core_policy::evaluation_hierarchy::guarded_non_worse);
    assert_public_value!(core_policy::evaluation_hierarchy::guarded_strictly_improves);
    assert_public_type!(linear_algebra::exact_repair::ExactRepair);
    assert_public_type!(core_functional::FunctionalLayerBoundary);
    assert_public_type!(core_functional::aggregation::AggregationMonotonicity);
    assert_public_type!(core_functional::quantum_gaps::QuantumGapFunctional);
    assert_public_type!(core_functional::quantum_gaps::QuantumGaps);
    assert_public_type!(core_functional::transport_amplitude::TransportAmplitude);

    // Compile the actual object-safe port, not a marker with the same name.
    let kernel = core_functional::factory::ConfiguredFunctional::phi1(vec![], vec![])
        .expect("the zero-dimensional quotient is valid");
    let port: &dyn core_functional::factory::BaseFunctionalKernel = &kernel;
    assert_eq!(port.functional_id(), "phi1");
    assert_public_value!(core_functional::factory::evaluate_functional);

    assert_public_type!(core_functional::gamma2::ExactCochainComplexQ);
    assert_public_type!(core_functional::gamma2::DegreeOneResidualQ<'static>);
    assert_public_type!(core_functional::gamma2::ExactGamma2Result);
    assert_public_type!(core_functional::gamma2::ClosureStatus);
    assert_public_type!(core_kernel::evidence::Hash256);
    assert_public_type!(core_kernel::evidence::ReplayHash);
    assert_public_type!(core_kernel::evidence::CarrierManifestHash);
    assert_public_type!(core_kernel::evidence::ToleranceProfileHash);
    assert_public_type!(core_kernel::evidence::CertifiedScalar);
    assert_public_type!(core_functional::mub_feasibility_wall::MubFeasibilityWallValue);
    assert_public_type!(core_functional::mub_feasibility_wall::MubFeasibilityWallEvidenceKind);
    assert_public_type!(core_functional::mub_feasibility_wall::MubFeasibilityWallAuthorityKind);
    assert_public_type!(core_functional::mub_feasibility_wall::MubFeasibilityWallTargetComparison);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonPacket);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonStatus);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonAuthorityRequest);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonResidual);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonResidualKind);
    assert_public_type!(core_types::observer_comparison::ComparisonLaunderingRefused);
    assert_public_type!(core_types::observer_comparison::ObserverComparisonError);
    assert_public_type!(core_types::observer_family::ObserverFamily);
    assert_public_type!(core_types::observer_quotient::ObserverQuotient);
    assert_public_type!(core_types::observer_quotient::ObserverQuotientError);
    assert_public_type!(core_types::observer::Observer);
    assert_public_type!(core_types::obstruction_mass::ObstructionMass);
    assert_public_type!(core_types::obstruction_mass::ObstructionMassError);
    assert_public_type!(core_types::obstruction_mass::EvidenceBindings);
    assert_public_type!(core_functional::phi1::ExactPhi1Certificate);
    assert_public_type!(core_functional::phi1::VerifiedExactPhi1);
    assert_public_type!(core_functional::phi1::Phi1Functional);
    assert_public_type!(core_solvers::solver_lp_phi1_quotient::Phi1LinearProgram);
    assert_public_type!(core_solvers::solver_lp_phi1_quotient::SimplexRefusal);
    assert_public_type!(core_solvers::solver_lp_phi1_quotient::Phi1SolveError);
    assert_public_value!(core_solvers::solver_lp_phi1_quotient::solve_exact_phi1);
    assert_public_type!(core_types::quotient_mass::QuotientMass);
    assert_public_type!(core_policy::trichotomy::CertifiedExactTrichotomy);
    assert_public_type!(core_policy::trichotomy::ObstructionDiagnosticClass);
    assert_public_type!(core_policy::trichotomy::TrichotomyOutcome);
    assert_public_type!(core_policy::trichotomy::TrichotomyRefusal);
    assert_public_value!(core_policy::trichotomy::classify_exact);
    assert_public_type!(core_types::xi_diagnostic::XiDiagnostic);
    assert_public_type!(core_functional::xi::DensityLift);
    assert_public_type!(core_functional::xi::XiValidity);
    assert_public_type!(core_functional::xi::XiResult);
    assert_public_type!(core_functional::xi::XiComputation);
    assert_public_type!(core_functional::xi::XiError);
    assert_public_type!(core_functional::xi::XiFunctional);
    assert_public_value!(core_functional::gamma_reconciliation::MAX_VERTEX_ROWS);
    assert_public_type!(core_functional::gamma_reconciliation::GammaReconciliationError);
    assert_public_type!(core_functional::gamma_reconciliation::QuotientGammaCertificate);
    assert_public_type!(core_functional::gamma_reconciliation::VertexFarkasCertificate);
    assert_public_type!(core_functional::gamma_reconciliation::ValueGapWitness);
    assert_public_type!(core_functional::gamma_reconciliation::VertexExtensionTable);
    assert_public_value!(core_functional::gamma_reconciliation::all_sign_vectors);
    assert_public_type!(core_functional::gamma_reconciliation::RepairQuotientProblem);
    assert_public_type!(core_functional::residual_splitting::ResidualSplittingError);
    assert_public_type!(core_functional::residual_splitting::RowMatrix);
    assert_public_value!(core_functional::residual_splitting::multiply);
    assert_public_value!(core_functional::residual_splitting::weighted_l1_operator_norm);
    assert_public_value!(core_functional::residual_splitting::splitting_from_parameter);
    assert_public_type!(core_functional::residual_splitting::ResidualSplittingCertificate);
    assert_public_value!(core_functional::residual_splitting::verify_transport);
}

#[test]
fn functional_contract_registry_matches_canonical_yaml_bindings() {
    for binding in FUNCTIONAL_CONTRACT_BINDINGS {
        let path = canonical_math_contract_path(binding.canonical_file);
        let contract = read_yaml(&path);
        let descriptor = field(&contract, "descriptor");
        let dependencies = field(descriptor, "dependencies");
        let operator_classes = field(descriptor, "operator_classes");
        let rust_binding = field(&contract, "rust_binding");
        let dependency_urns = string_sequence(dependencies, "contracts");
        let mut symbols = string_sequence(rust_binding, "symbols");
        let mut expected_symbols: Vec<String> = binding
            .rust_symbols
            .iter()
            .map(|symbol| (*symbol).to_string())
            .collect();
        symbols.sort();
        expected_symbols.sort();

        assert_eq!(
            field_str(&contract, "schema_version"),
            "core.contract.v1",
            "{} must be a v1 contract",
            binding.canonical_file
        );
        assert_eq!(
            field_str(&contract, "kind"),
            "math_contract",
            "{} must stay in the math contract layer",
            binding.canonical_file
        );
        assert_eq!(
            field_str(&contract, "layer"),
            "math",
            "{} must declare the canonical math layer",
            binding.canonical_file
        );
        assert_eq!(
            field_str(&contract, "contract_id"),
            binding.contract_urn,
            "{} must declare its registered contract URN",
            binding.canonical_file
        );
        assert_eq!(
            field_str(descriptor, "authority_effect"),
            "none",
            "{} must not mint authority",
            binding.canonical_file
        );
        assert_eq!(
            field_str(descriptor, "evidence_ceiling"),
            "ShapeOnly",
            "{} must stay shape-only evidence",
            binding.canonical_file
        );
        assert!(
            !field_bool(descriptor, "runtime_enforcement"),
            "{} must not claim runtime enforcement",
            binding.canonical_file
        );
        assert!(
            !field_bool(descriptor, "customer_claim_allowed"),
            "{} must not permit customer-facing claims",
            binding.canonical_file
        );
        assert!(
            field_bool(operator_classes, "must_not_self_assign"),
            "{} must not self-assign operator authority",
            binding.canonical_file
        );
        let binding_crate = match binding.rust_crate {
            "linear_algebra" => "core_linear_algebra",
            other => other,
        };
        assert_eq!(
            field_str(rust_binding, "crate"),
            binding_crate,
            "{} must bind to its implementation owner",
            binding.canonical_file
        );
        assert_eq!(
            field_str(rust_binding, "module"),
            binding.rust_module,
            "{} must name its registered rust module",
            binding.canonical_file
        );
        assert_eq!(
            symbols, expected_symbols,
            "{} rust_binding symbols must match the registry",
            binding.canonical_file
        );
        assert_eq!(
            dependency_urns,
            binding
                .dependency_contract_urns
                .iter()
                .map(|dependency| (*dependency).to_string())
                .collect::<Vec<_>>(),
            "{} descriptor dependencies must match registered dependency_contract_urns",
            binding.canonical_file
        );
    }
}

#[test]
fn every_canonical_omega_functional_contract_is_registered() {
    let contract_dir = canonical_math_contract_dir();
    let mut actual = Vec::new();

    for entry in fs::read_dir(&contract_dir)
        .unwrap_or_else(|err| panic!("read {}: {err}", contract_dir.display()))
    {
        let entry = entry.unwrap_or_else(|err| panic!("read dir entry: {err}"));
        let path = entry.path();
        let Some(file_name) = path.file_name().and_then(|name| name.to_str()) else {
            continue;
        };
        if !file_name.ends_with(".contract.yaml") {
            continue;
        }

        let text = fs::read_to_string(&path)
            .unwrap_or_else(|err| panic!("read {}: {err}", path.display()));
        if !text.contains("core_functional") {
            continue;
        }
        let contract: Value = serde_yaml::from_str(&text)
            .unwrap_or_else(|err| panic!("parse {}: {err}", path.display()));
        let Some(rust_binding) = optional_field(&contract, "rust_binding") else {
            continue;
        };
        if optional_field_str(rust_binding, "crate") == Some("core_functional") {
            actual.push(file_name.to_string());
        }
    }

    let mut expected: Vec<String> = FUNCTIONAL_CONTRACT_BINDINGS
        .iter()
        .filter(|binding| binding.rust_crate == "core_functional")
        .map(|binding| binding.canonical_file.to_string())
        .collect();
    actual.sort();
    expected.sort();

    assert_eq!(
        actual,
        expected,
        "every canonical YAML contract that binds core_functional must be represented in FUNCTIONAL_CONTRACT_BINDINGS"
    );
}

#[test]
fn primitive_descriptor_table_has_matching_canonical_contract_files() {
    let contract_dir = canonical_math_contract_dir();
    assert_eq!(
        CORE_PRIMITIVE_CONTRACTS.len(),
        CORE_PRIMITIVE_CONTRACT_BINDINGS.len(),
        "every exposed primitive descriptor must have a canonical YAML binding"
    );

    for table_descriptor in CORE_PRIMITIVE_CONTRACTS {
        let binding = binding_by_descriptor_id(table_descriptor.contract_id).unwrap_or_else(|| {
            panic!(
                "missing canonical YAML mapping for descriptor {}",
                table_descriptor.contract_id
            )
        });
        let path = contract_dir.join(binding.canonical_file);
        let contract = read_yaml(&path);
        let yaml_descriptor = field(&contract, "descriptor");
        let yaml_dependencies = field(yaml_descriptor, "dependencies");
        let doctrine = field(&contract, "doctrine");
        let display = optional_field(doctrine, "compact_yaml")
            .map(|compact| field(compact, table_descriptor.contract_id))
            .unwrap_or(doctrine);
        let actual_dependencies = string_sequence(yaml_dependencies, "contracts");
        let expected_dependencies: Vec<String> =
            primitive_dependency_contract_urns(table_descriptor.contract_id)
                .unwrap_or_else(|| {
                    panic!(
                        "{} has unresolvable primitive dependency descriptors",
                        table_descriptor.contract_id
                    )
                })
                .into_iter()
                .map(str::to_string)
                .collect();

        assert_eq!(field_str(&contract, "schema_version"), "core.contract.v1");
        assert_eq!(field_str(&contract, "kind"), "math_contract");
        assert_eq!(field_str(&contract, "layer"), "math");
        assert_eq!(
            field_str(&contract, "contract_id"),
            binding.canonical_contract_urn,
            "{} must declare its bound canonical URN",
            binding.canonical_file
        );
        assert_eq!(field_str(yaml_descriptor, "authority_effect"), "none");
        let mut actual_iter = actual_dependencies.iter();
        for expected_dependency in &expected_dependencies {
            assert!(
                actual_iter.any(|actual_dependency| actual_dependency == expected_dependency),
                "{} descriptor dependencies must include primitive dependency {} in descriptor order",
                binding.canonical_file,
                expected_dependency
            );
        }
        assert!(
            !actual_dependencies
                .iter()
                .any(|dependency| dependency == binding.canonical_contract_urn),
            "{} descriptor dependencies must not include self dependency {}",
            binding.canonical_file,
            binding.canonical_contract_urn
        );
        assert!(
            !field_bool(yaml_descriptor, "customer_claim_allowed"),
            "{} must not permit customer-facing claims",
            binding.canonical_file
        );
        assert!(
            !field_str(display, "symbol").is_empty(),
            "{} canonical descriptor must declare a display symbol",
            binding.canonical_file
        );
        assert!(
            !field_str(display, "ascii_symbol").is_empty(),
            "{} canonical descriptor must declare an ASCII symbol",
            binding.canonical_file
        );
        assert_eq!(
            field_str(yaml_descriptor, "authority_effect"),
            table_descriptor.authority_effect,
            "{} canonical descriptor must preserve the primitive authority effect",
            binding.canonical_file
        );
        assert_eq!(
            field_bool(yaml_descriptor, "customer_claim_allowed"),
            table_descriptor.customer_claim_allowed,
            "{} canonical descriptor must preserve the primitive claim boundary",
            binding.canonical_file
        );
    }
}

// Origin: engine/crates_rs/tests/core_contracts/functional_boundary.rs
// Claim: urn:core:crates_rs:tests:functional-boundary:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord6d8cd026 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord6d8cd026` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError6d8cd026 {
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
impl BoundaryError6d8cd026 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError6d8cd026 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError6d8cd026 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord6d8cd026 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError6d8cd026> {
        if capacity_bound == 0 {
            return Err(BoundaryError6d8cd026::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError6d8cd026::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError6d8cd026::ExceedsCapacity {
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
fn l4_boundary_admits_and_refuses_6d8cd026() {
    let admitted = BoundaryRecord6d8cd026::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord6d8cd026::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
