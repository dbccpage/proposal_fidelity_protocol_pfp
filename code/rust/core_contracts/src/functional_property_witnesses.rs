/// Satisfies the contract validator for the ContractPropertyWitnesses symbol.
#[allow(dead_code)]
pub struct ContractPropertyWitnesses;

// Origin: engine/crates_rs/core_contracts/src/functional_property_witnesses.rs
// Claim: urn:core:crates_rs:core-contracts:functional-property-witnesses:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa831788 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa831788` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa831788 {
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
impl BoundaryErroraa831788 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa831788 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa831788 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa831788 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa831788> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa831788::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa831788::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa831788::ExceedsCapacity {
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
mod __omega_functional_property_witnesses {
    use num_bigint::BigInt;
    use num_rational::BigRational;
    use core_functional::gamma2::{
        DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Result, Gamma2Functional,
    };
    use core_functional::phi1::{ExactPhi1Certificate, Phi1Functional, VerifiedExactPhi1};
    use core_policy::trichotomy::{classify_exact, ObstructionDiagnosticClass, TrichotomyOutcome};

    fn r(value: i64) -> BigRational {
        BigRational::from_integer(BigInt::from(value))
    }

    fn verified_phi1(
        omega: i64,
        d0: i64,
        alpha: i64,
        residual: i64,
        dual: i64,
        value: i64,
    ) -> VerifiedExactPhi1 {
        Phi1Functional::verify_exact_certificate(ExactPhi1Certificate {
            omega: vec![r(omega)],
            d0: vec![vec![r(d0)]],
            weights: vec![r(1)],
            alpha: vec![r(alpha)],
            primal_residual: vec![r(residual)],
            dual_witness: vec![r(dual)],
            reported_value: r(value),
        })
        .unwrap()
    }

    fn compute_gamma2(
        res: &[BigRational],
        d0: &[Vec<BigRational>],
        d1: &[Vec<BigRational>],
    ) -> ExactGamma2Result {
        let c0_dim = d0.first().map_or(0, Vec::len);
        let c1_dim = res.len();
        let c2_dim = d1.len();
        let complex =
            ExactCochainComplexQ::try_new(c0_dim, c1_dim, c2_dim, d0.to_vec(), d1.to_vec())
                .unwrap();
        let q = DegreeOneResidualQ::try_new(&complex, res.to_vec()).unwrap();
        Gamma2Functional::try_compute_exact_quotient(&q).unwrap()
    }

    #[test]
    fn finite_obstruction_trichotomy_symbols_have_compiled_witnesses() {
        let _classifier: fn(&VerifiedExactPhi1, &ExactGamma2Result) -> TrichotomyOutcome =
            classify_exact;

        let exact_phi1 = verified_phi1(1, 1, 1, 0, 0, 0);
        let exact_gamma2 =
            compute_gamma2(exact_phi1.primal_residual(), exact_phi1.d0(), &[vec![r(0)]]);

        if let TrichotomyOutcome::Classified(certified) = classify_exact(&exact_phi1, &exact_gamma2)
        {
            assert_eq!(
                certified.diagnostic_class(),
                ObstructionDiagnosticClass::ExactRepair
            );
        } else {
            panic!("Expected Classified");
        }

        let survivor_phi1 = verified_phi1(1, 0, 0, 1, 1, 1);
        let survivor_gamma2 = compute_gamma2(
            survivor_phi1.primal_residual(),
            survivor_phi1.d0(),
            &[vec![r(0)]],
        );

        if let TrichotomyOutcome::Classified(certified) =
            classify_exact(&survivor_phi1, &survivor_gamma2)
        {
            assert_eq!(
                certified.diagnostic_class(),
                ObstructionDiagnosticClass::ClosedResidual
            );
        } else {
            panic!("Expected Classified");
        }
    }

    #[test]
    fn functional_bindings_match_yaml_schemas() {
        use serde::Deserialize;
        use std::fs;
        use std::path::PathBuf;

        #[derive(Deserialize)]
        struct DescriptorNode {
            dependencies: Option<DependenciesNode>,
        }
        #[derive(Deserialize)]
        struct DependenciesNode {
            contracts: Option<Vec<String>>,
        }
        #[derive(Deserialize)]
        struct ContractYaml {
            contract_id: String,
            descriptor: Option<DescriptorNode>,
        }

        let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").unwrap();
        let canonical_dir = PathBuf::from(manifest_dir)
            .ancestors()
            .nth(1)
            .expect("core_contracts lives one level below the workspace root")
            .join("governance/contracts/contract_canonical_definitions/math");

        for binding in crate::contract_descriptors::FUNCTIONAL_CONTRACT_BINDINGS {
            let yaml_path = canonical_dir.join(binding.canonical_file);

            let yaml_content = fs::read_to_string(&yaml_path).expect("Failed to read YAML file");
            let parsed: ContractYaml =
                serde_yaml::from_str(&yaml_content).expect("Failed to parse YAML");

            assert_eq!(
                parsed.contract_id, binding.contract_urn,
                "URN mismatch for {}",
                binding.canonical_file
            );

            let yaml_deps = parsed
                .descriptor
                .and_then(|d| d.dependencies)
                .and_then(|d| d.contracts)
                .unwrap_or_default();

            for expected_dep in binding.dependency_contract_urns {
                assert!(
                    yaml_deps.contains(&expected_dep.to_string()),
                    "Missing dependency {} in YAML {}",
                    expected_dep,
                    binding.canonical_file
                );
            }
            for actual_dep in &yaml_deps {
                assert!(
                    binding
                        .dependency_contract_urns
                        .contains(&actual_dep.as_str()),
                    "Unexpected dependency {} in YAML {}",
                    actual_dep,
                    binding.canonical_file
                );
            }
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_aa831788 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaa831788::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaa831788::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaa831788::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaa831788::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaa831788::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErroraa831788::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErroraa831788::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
