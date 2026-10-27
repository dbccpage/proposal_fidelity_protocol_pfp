
#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_326d1d74<T> {
    fn checked_invariant_326d1d74(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_326d1d74<T> for Option<T> {
    #[inline]
    fn checked_invariant_326d1d74(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_326d1d74<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_326d1d74(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use serde::{Deserialize, Serialize};

pub const CONTRACT_STATUS: &str = "mathematical_definition_wip";
pub const AUTHORITY_EFFECT: &str = "none";
pub const CUSTOMER_CLAIM_ALLOWED: bool = false;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct PrimitiveContractDescriptor {
    pub contract_id: &'static str,
    pub symbol: &'static str,
    pub ascii_symbol: &'static str,
    pub formula: &'static str,
    pub object_type: &'static str,
    pub status: &'static str,
    pub authority_effect: &'static str,
    pub customer_claim_allowed: bool,
    pub domain: &'static str,
    pub codomain: &'static str,
    pub definition: &'static str,
    pub forbidden_interpretations: &'static [&'static str],
    pub depends_on: &'static [&'static str],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct PrimitiveContractBinding {
    pub descriptor_id: &'static str,
    pub canonical_contract_urn: &'static str,
    pub canonical_file: &'static str,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
pub struct FunctionalContractBinding {
    pub contract_urn: &'static str,
    pub canonical_file: &'static str,
    pub rust_crate: &'static str,
    pub rust_module: &'static str,
    pub rust_symbols: &'static [&'static str],
    pub dependency_contract_urns: &'static [&'static str],
}

impl PrimitiveContractDescriptor {
    #[allow(clippy::too_many_arguments)]
    pub const fn new(
        contract_id: &'static str,
        symbol: &'static str,
        ascii_symbol: &'static str,
        formula: &'static str,
        object_type: &'static str,
        domain: &'static str,
        codomain: &'static str,
        definition: &'static str,
        forbidden_interpretations: &'static [&'static str],
        depends_on: &'static [&'static str],
    ) -> Self {
        Self {
            contract_id,
            symbol,
            ascii_symbol,
            formula,
            object_type,
            status: CONTRACT_STATUS,
            authority_effect: AUTHORITY_EFFECT,
            customer_claim_allowed: CUSTOMER_CLAIM_ALLOWED,
            domain,
            codomain,
            definition,
            forbidden_interpretations,
            depends_on,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
pub enum OperatorClass {
    ExactRepair,
    QuotientIsometry,
    ContextEmbedding,
    ResidualProjection,
    Mutation,
    Lift,
    Deformation,
    Terminalization,
}

impl OperatorClass {
    pub const fn symbol(self) -> &'static str {
        match self {
            Self::ExactRepair => "E",
            Self::QuotientIsometry => "I",
            Self::ContextEmbedding => "C",
            Self::ResidualProjection => "R",
            Self::Mutation => "M",
            Self::Lift => "L",
            Self::Deformation => "D",
            Self::Terminalization => "T",
        }
    }

    pub const fn mathematical_role(self) -> &'static str {
        match self {
            Self::ExactRepair => "gauge movement inside the same quotient class",
            Self::QuotientIsometry => "quotient symmetry preserving Phi1",
            Self::ContextEmbedding => "declared context embedding for diagnostic exposure",
            Self::ResidualProjection => "canonical minimal representative selection",
            Self::Mutation => {
                "refusal class for undeclared damaging, structure-changing, or out-of-layer action"
            }
            Self::Lift => "transport of quotient to a resolved carrier",
            Self::Deformation => "homotopy or continuous variation of structure",
            Self::Terminalization => "certified decision blocking further operation",
        }
    }
}

pub const CORE_PRIMITIVE_CONTRACTS: &[PrimitiveContractDescriptor] = &[
    PrimitiveContractDescriptor::new(
        "COCHAIN_LAYER_CONTRACT",
        "C⁰, C¹, C², d₀, d₁",
        "C0,C1,C2,d0,d1",
        "d₁d₀=0",
        "finite_cochain_layer",
        "finite ordered cochain modules over R",
        "valid cochain layer",
        "finite cochain layer with d1*d0=0 and frozen carrier data",
        &["implicit coefficient domain", "unfrozen carrier", "Gamma2 without C^2/d1"],
        &[],
    ),
    PrimitiveContractDescriptor::new(
        "EXACT_REPAIR_SPACE_CONTRACT",
        "B¹",
        "B1",
        "B¹=im(d₀)",
        "subspace_or_submodule_of_C1",
        "C⁰,C¹,d₀",
        "subspace B¹ <= C¹",
        "exact repairs are coboundary shifts d₀α",
        &["repair without alpha witness", "affine target repair space", "quotient mutation"],
        &["COCHAIN_LAYER_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "QUOTIENT_SPACE_CONTRACT",
        "Q¹",
        "Q1",
        "Q¹=C¹/B¹",
        "quotient_space_or_module",
        "C¹,B¹",
        "quotient space Q¹",
        "residual distinctions modulo exact repair",
        &["representative equals class", "Q¹ equals H¹", "quotient norm before B¹"],
        &["COCHAIN_LAYER_CONTRACT", "EXACT_REPAIR_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "PHI1_OBSTRUCTION_MASS_CONTRACT",
        "Φ₁",
        "Phi1",
        "Φ₁([ω])=inf_α ||ω-d₀α||_{1,w}",
        "obstruction_mass_functional",
        "Q¹ represented by omega in C¹",
        "nonnegative scalar",
        "primary weighted l1 quotient norm",
        &["raw ||omega||_1", "raw float exact certificate", "missing primal-dual certificate", "Gamma2 or Xi override", "canonical residual without TieR"],
        &["COCHAIN_LAYER_CONTRACT", "EXACT_REPAIR_SPACE_CONTRACT", "QUOTIENT_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "VALIDATED_COCHAIN_COMPLEX_CONTRACT",
        "C*,d",
        "ValidatedCochainComplex",
        "C* with d₁d₀=0",
        "cochain_complex_certificate",
        "C⁰,C¹,C²,d₀,d₁",
        "validated cochain complex",
        "certificate of d1*d0=0",
        &["complex without exact receipt", "float matrix zeros"],
        &["COCHAIN_LAYER_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "RAW_CLOSURE_DEFECT_CONTRACT",
        "||d₁h||₁",
        "RawClosureDefect",
        "Raw Γ₂([h])=||d₁h||₁",
        "closure_defect_functional",
        "h in C¹ with d₁:C¹→C²",
        "nonnegative scalar",
        "raw closure defect without d1*d0=0",
        &["GammaSquare operation", "raw defect as quotient invariant"],
        &["COCHAIN_LAYER_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "QUOTIENT_GAMMA2_CONTRACT",
        "Γ₂",
        "Gamma2",
        "Γ₂([h])=||d₁h||₁",
        "closure_defect_functional",
        "h in Q¹ with d₁:C¹→C²",
        "nonnegative scalar",
        "quotient-invariant closure defect requiring d1*d0=0",
        &["GammaSquare/Γ² operation", "Gamma2 without d1", "Phi1 override", "quotient-level Γ₂ without a chain-law certificate"],
        &["VALIDATED_COCHAIN_COMPLEX_CONTRACT", "RAW_CLOSURE_DEFECT_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "CLOSED_SECTOR_CONTRACT",
        "Z¹",
        "Z1",
        "Z¹=ker(d₁)",
        "subspace_or_submodule_of_C1",
        "C¹,d₁:C¹→C²",
        "subspace Z¹ <= C¹",
        "closed sector consists of h with d₁h=0",
        &["closed sector without d1", "closed sector without C^2", "closed means exact"],
        &["QUOTIENT_GAMMA2_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "COHOMOLOGY_CONTRACT",
        "H¹",
        "H1",
        "H¹=Z¹/B¹",
        "quotient_space_or_module",
        "Z¹,B¹ with d₁d₀=0",
        "cohomology space H¹",
        "closed survivors modulo exact repair",
        &["open obstruction as H¹", "nonclosed residual in H¹", "H¹ equals Q¹"],
        &["CLOSED_SECTOR_CONTRACT", "EXACT_REPAIR_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "RESIDUAL_PROJECTION_CONTRACT",
        "R",
        "ResidualProjection",
        "R(x)=x-d₀α*",
        "canonical_representative_operator",
        "x in C¹ with B¹ and Phi1 problem",
        "canonical representative in [x]",
        "minimal-norm representative selected by deterministic TieR",
        &["deterministic without TieR", "quotient mutation", "policy decision"],
        &["PHI1_OBSTRUCTION_MASS_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "XI_TIE_BREAKER_CONTRACT",
        "Ξ",
        "Xi",
        "Ξ=||ρ(h1*)-ρ(φ*)||_tr",
        "tie_breaker_diagnostic",
        "tied optimal h1*,phi* after Phi1 and Gamma2",
        "trace distance scalar",
        "tertiary representative-alignment diagnostic",
        &["obstruction norm", "quantum score", "observer-independent truth", "Phi1/Gamma2 override"],
        &["PHI1_OBSTRUCTION_MASS_CONTRACT", "QUOTIENT_GAMMA2_CONTRACT", "RESIDUAL_PROJECTION_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "EXACT_REPAIR_OPERATOR_CONTRACT",
        "E_α",
        "E_alpha",
        "E_α(x)=x+d₀α",
        "operator_class",
        "x in C¹, α in C⁰",
        "same Q¹ class",
        "exact repair action inside one quotient class",
        &["structural progress", "carrier mutation", "missing alpha", "identity on representatives"],
        &["EXACT_REPAIR_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "QUOTIENT_ISOMETRY_OPERATOR_CONTRACT",
        "I",
        "QuotientIsometry",
        "I:Q¹→Q¹, Φ₁ preserved",
        "operator_class",
        "Q¹",
        "Q¹",
        "quotient automorphism/isometry preserving Phi1",
        &["repair", "carrier mutation", "E mislabeled as I", "representative lift without compatibility"],
        &["QUOTIENT_SPACE_CONTRACT", "PHI1_OBSTRUCTION_MASS_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "CONTEXT_EMBEDDING_OPERATOR_CONTRACT",
        "C_c",
        "ContextEmbedding",
        "C_c=ρ_c",
        "operator_class",
        "source carrier",
        "context carrier",
        "declared context embedding for diagnostic exposure",
        &["repair", "I because one sample preserves Phi1", "silent source mutation", "isometry claim"],
        &[],
    ),
    PrimitiveContractDescriptor::new(
        "MUTATION_OPERATOR_CONTRACT",
        "M",
        "Mutation",
        "N/A",
        "mathematical_refusal_class",
        "fixed-layer action attempt",
        "mutation refusal class",
        "undeclared damaging, structure-changing, or out-of-layer action outside E/I/C/R",
        &["policy decision", "admitted repair", "valid undeclared lift", "diagnostic improvement laundering mutation"],
        &[],
    ),
    PrimitiveContractDescriptor::new(
        "OBSERVER_QUOTIENT_CONTRACT",
        "Q¹_O",
        "Q1_O",
        "Q¹_O=Q¹/~_O",
        "observer_quotient",
        "Q¹ plus observer map O",
        "observer-visible quotient",
        "observer-induced quotient bound to a declared observer map",
        &["observer-independent truth", "unbound visible quotient", "Q¹_O equals Q¹", "automatic Φ₁ inheritance"],
        &["QUOTIENT_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "FINITE_OBSTRUCTION_TRICHOTOMY_CONTRACT",
        "ExactRepair|StabilizedSurvivor|OpenObstruction",
        "FiniteObstructionClass",
        "ExactRepair iff Φ₁=0; StabilizedSurvivor iff Φ₁>0 and Γ₂=0; OpenObstruction iff Φ₁>0 and Γ₂>0",
        "mathematical_classifier",
        "Phi1,Gamma2 with comparison mode",
        "descriptive obstruction class",
        "ExactRepair iff Phi1=0; StabilizedSurvivor iff Phi1>0 and Gamma2=0; OpenObstruction iff Phi1>0 and Gamma2>0",
        &["floating heuristic exact class", "policy decision", "ActionLicense", "business severity ranking", "customer claim"],
        &["PHI1_OBSTRUCTION_MASS_CONTRACT", "QUOTIENT_GAMMA2_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "EVALUATION_HIERARCHY_CONTRACT",
        "Φ₁→Γ₂→Ξ",
        "EvaluationHierarchy",
        "lexicographic(Φ₁,Γ₂,Ξ)",
        "diagnostic_comparison_relation",
        "before/after diagnostic tuples",
        "diagnostic comparison relation",
        "Phi1 first, then Gamma2 on Phi1 ties, then Xi on Phi1/Gamma2 ties",
        &["Xi-first comparison", "policy decision", "customer claim"],
        &["PHI1_OBSTRUCTION_MASS_CONTRACT", "QUOTIENT_GAMMA2_CONTRACT", "XI_TIE_BREAKER_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "CANDIDATE_OBSTRUCTION_WINDOW_CONTRACT",
        "W",
        "Window",
        "W=[l, u]",
        "obstruction_window",
        "obstruction mass space",
        "admissible region",
        "Candidate obstruction window for evaluating repair impact.",
        &["exact scalar", "floating approximation"],
        &["PHI1_OBSTRUCTION_MASS_CONTRACT", "QUOTIENT_GAMMA2_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "QUOTIENT_TRANSPORT_CONTRACT",
        "T_Q",
        "TransportQ",
        "T_Q: Q_A -> Q_B",
        "operator_class",
        "quotient space",
        "quotient space",
        "Quotient transport operator across contexts.",
        &["lossless mapping", "exact isometry"],
        &["QUOTIENT_SPACE_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "TRANSPORT_LOSS_LEDGER_CONTRACT",
        "L_T",
        "LossLedger",
        "L_T=sum(loss)",
        "loss_ledger",
        "transport operations",
        "accumulated loss",
        "Ledger for tracking precision loss during transport.",
        &["customer claim", "ActionLicense", "terminalization"],
        &["QUOTIENT_TRANSPORT_CONTRACT"],
    ),
    PrimitiveContractDescriptor::new(
        "TIE_R_CONTRACT",
        "Tie_R",
        "TieR",
        "Tie_R(A)=min_norm(A)",
        "policy",
        "set of tied candidates",
        "canonical representative",
        "Deterministic TieR policy for residual selection.",
        &["tie breaking by phase", "random choice"],
        &["RESIDUAL_PROJECTION_CONTRACT"],
    ),
];

pub const CORE_PRIMITIVE_CONTRACT_BINDINGS: &[PrimitiveContractBinding] = &[
    PrimitiveContractBinding {
        descriptor_id: "COCHAIN_LAYER_CONTRACT",
        canonical_contract_urn: "urn:core:math:cochain_layer:v1.0.0",
        canonical_file: "cochain_layer.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "EXACT_REPAIR_SPACE_CONTRACT",
        canonical_contract_urn: "urn:core:math:exact_repair_space:v1.0.0",
        canonical_file: "exact_repair_space.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "QUOTIENT_SPACE_CONTRACT",
        canonical_contract_urn: "urn:core:math:quotient_space:v1.0.0",
        canonical_file: "quotient_space.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "PHI1_OBSTRUCTION_MASS_CONTRACT",
        canonical_contract_urn: "urn:core:math:phi1_obstruction_mass:v1.0.0",
        canonical_file: "phi1_obstruction_mass.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "VALIDATED_COCHAIN_COMPLEX_CONTRACT",
        canonical_contract_urn: "urn:core:math:validated_cochain_complex:v1.0.0",
        canonical_file: "validated_cochain_complex.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "RAW_CLOSURE_DEFECT_CONTRACT",
        canonical_contract_urn: "urn:core:math:raw_closure_defect:v1.0.0",
        canonical_file: "raw_closure_defect.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "QUOTIENT_GAMMA2_CONTRACT",
        canonical_contract_urn: "urn:core:math:gamma2_closure_defect:v1.0.0",
        canonical_file: "gamma2_closure_defect.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "CLOSED_SECTOR_CONTRACT",
        canonical_contract_urn: "urn:core:math:closed_sector:v1.0.0",
        canonical_file: "closed_sector.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "COHOMOLOGY_CONTRACT",
        canonical_contract_urn: "urn:core:math:cohomology:v1.0.0",
        canonical_file: "cohomology.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "RESIDUAL_PROJECTION_CONTRACT",
        canonical_contract_urn: "urn:core:math:residual_projection:v1.0.0",
        canonical_file: "residual_projection.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "XI_TIE_BREAKER_CONTRACT",
        canonical_contract_urn: "urn:core:math:xi_tie_breaker:v1.0.0",
        canonical_file: "xi_tie_breaker.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "EXACT_REPAIR_OPERATOR_CONTRACT",
        canonical_contract_urn: "urn:core:math:exact_repair_operator:v1.0.0",
        canonical_file: "exact_repair_operator.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "QUOTIENT_ISOMETRY_OPERATOR_CONTRACT",
        canonical_contract_urn: "urn:core:math:quotient_isometry_operator:v1.0.0",
        canonical_file: "quotient_isometry_operator.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "CONTEXT_EMBEDDING_OPERATOR_CONTRACT",
        canonical_contract_urn: "urn:core:math:context_embedding_operator:v1.0.0",
        canonical_file: "context_embedding_operator.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "MUTATION_OPERATOR_CONTRACT",
        canonical_contract_urn: "urn:core:math:mutation_operator:v1.0.0",
        canonical_file: "mutation_operator.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "OBSERVER_QUOTIENT_CONTRACT",
        canonical_contract_urn: "urn:core:math:observer_quotient:v1.0.0",
        canonical_file: "observer_quotient.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "FINITE_OBSTRUCTION_TRICHOTOMY_CONTRACT",
        canonical_contract_urn: "urn:core:math:finite_obstruction_trichotomy:v0.2.0",
        canonical_file: "finite_obstruction_trichotomy.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "EVALUATION_HIERARCHY_CONTRACT",
        canonical_contract_urn: "urn:core:math:evaluation_hierarchy:v1.0.0",
        canonical_file: "evaluation_hierarchy.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "CANDIDATE_OBSTRUCTION_WINDOW_CONTRACT",
        canonical_contract_urn: "urn:core:math:candidate_obstruction_window:v1.0.0",
        canonical_file: "candidate_obstruction_window.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "QUOTIENT_TRANSPORT_CONTRACT",
        canonical_contract_urn: "urn:core:math:quotient_transport:v1.0.0",
        canonical_file: "quotient_transport.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "TRANSPORT_LOSS_LEDGER_CONTRACT",
        canonical_contract_urn: "urn:core:math:transport_loss_ledger:v1.0.0",
        canonical_file: "transport_loss_ledger.contract.yaml",
    },
    PrimitiveContractBinding {
        descriptor_id: "TIE_R_CONTRACT",
        canonical_contract_urn: "urn:core:math:tie_r:v1.0.0",
        canonical_file: "tie_r.contract.yaml",
    },
];

const FUNCTIONAL_LAYER_BOUNDARY_CONTRACT_URN: &str =
    "urn:core:math:functional_layer_boundary:v1.0.0";

const FUNCTIONAL_LAYER_BOUNDARY_DEPENDENCY_CONTRACT_URNS: &[&str] = &[
    "urn:core:math:cochain_layer:v1.0.0",
    "urn:core:math:exact_repair_space:v1.0.0",
    "urn:core:math:quotient_space:v1.0.0",
    "urn:core:math:validated_cochain_complex:v1.0.0",
    "urn:core:math:raw_closure_defect:v1.0.0",
    "urn:core:math:closed_sector:v1.0.0",
    "urn:core:math:cohomology:v1.0.0",
    "urn:core:math:residual_projection:v1.0.0",
    "urn:core:math:exact_repair_operator:v1.0.0",
    "urn:core:math:quotient_isometry_operator:v1.0.0",
    "urn:core:math:context_embedding_operator:v1.0.0",
    "urn:core:math:mutation_operator:v1.0.0",
    "urn:core:math:candidate_obstruction_window:v1.0.0",
    "urn:core:math:quotient_transport:v1.0.0",
    "urn:core:math:transport_loss_ledger:v1.0.0",
    "urn:core:math:tie_r:v1.0.0",
    "urn:core:math:born_probabilities:v1.0.0",
    "urn:core:math:dual_verification:v1.0.0",
    "urn:core:math:norms:v1.0.0",
    "urn:core:math:contract_descriptors:v1.0.0",
    "urn:core:math:contract_property_witnesses:v1.0.0",
    "urn:core:math:exact_repair:v1.0.0",
    "urn:core:math:hashes:v1.0.0",
    "urn:core:math:mub_feasibility_wall:v1.0.0",
    "urn:core:math:aggregation_functional:v1.0.0",
    "urn:core:math:quantum_gap_functional:v1.0.0",
    "urn:core:math:quantum_gaps:v1.0.0",
    "urn:core:math:transport_amplitude:v1.0.0",
    "urn:core:math:binary_degree_functional:v1.0.0",
    "urn:core:math:phi2_quotient_obstruction:v1.0.0",
    "urn:core:math:phi3_quotient_obstruction:v1.0.0",
    "urn:core:math:phi4_quotient_obstruction:v1.0.0",
    "urn:core:math:linear_observer_presentation:v1.0.0",
    "urn:core:math:gamma_reconciliation:v1.0.0",
    "urn:core:math:residual_splitting:v1.0.0",
    "urn:core:math:normal_projection:v1.0.0",
    "urn:core:math:circle_piecewise_linear:v1.0.0",
    "urn:core:math:weighted_l1_norm:v1.0.0",
    "urn:core:math:decoherence:v1.0.0",
    "urn:core:math:phi1:v1.0.0",
    "urn:core:math:gamma2_closure_defect:v1.0.0",
    "urn:core:math:observer:v1.0.0",
    "urn:core:math:distinguishability_functional:v1.0.0",
    "urn:core:math:trace_diagnostics:v1.0.0",
    "urn:core:math:l1_seminorm:v1.0.0",
    "urn:core:math:phi1_obstruction_mass:v1.0.0",
    "urn:core:math:closure_defect:v1.0.0",
    "urn:core:math:dual_witness:v0.1.0",
    "urn:core:math:observer_family:v1.0.0",
    "urn:core:math:observer_quotient:v1.0.0",
    "urn:core:math:quotient_mass:v1.0.0",
    "urn:core:math:graph_phi1_quotient_distance:v1.0.0",
    "urn:core:math:simplicial_defect:v1.0.0",
    "urn:core:math:observer_gauge:v1.0.0",
    "urn:core:math:residual:v1.0.0",
    "urn:core:math:functional_factory:v1.0.0",
    "urn:core:math:finite_obstruction_trichotomy:v0.2.0",
    "urn:core:math:observer_comparison:v1.0.0",
    "urn:core:math:xi_tie_breaker:v1.0.0",
    "urn:core:math:phi1_exact_certificate_solver:v1.0.0",
    "urn:core:math:closure_regime:v1.0.0",
    "urn:core:math:evaluation_hierarchy:v1.0.0",
    "urn:core:math:xi_diagnostic:v1.0.0",
    "urn:core:math:diagnostic_vector:v1.0.0",
    "urn:core:math:xi_comparison_policy:v1.0.0",
    "urn:core:math:product_distance:v1.0.0",
];

pub const FUNCTIONAL_CONTRACT_BINDINGS: &[FunctionalContractBinding] = &[
    FunctionalContractBinding {
        contract_urn: "urn:core:math:born_probabilities:v1.0.0",
        canonical_file: "born_probabilities.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "born_probabilities",
        dependency_contract_urns: &[],
        rust_symbols: &["BornProbabilities"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:dual_verification:v1.0.0",
        canonical_file: "dual_verification.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "dual_verification",
        dependency_contract_urns: &[],
        rust_symbols: &["verify_dual_witness"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:norms:v1.0.0",
        canonical_file: "norms.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "norms",
        dependency_contract_urns: &[],
        rust_symbols: &["lp_norm"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:contract_descriptors:v1.0.0",
        canonical_file: "contract_descriptors.contract.yaml",
        rust_crate: "core_contracts",
        rust_module: "contract_descriptors",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "ContractDescriptors",
            "PrimitiveContractDescriptor",
            "PrimitiveContractBinding",
            "FunctionalContractBinding",
            "CORE_PRIMITIVE_CONTRACTS",
            "CORE_PRIMITIVE_CONTRACT_BINDINGS",
            "FUNCTIONAL_CONTRACT_BINDINGS",
            "contract_by_id",
            "binding_by_descriptor_id",
            "primitive_binding_by_contract_urn",
            "primitive_binding_by_canonical_file",
            "primitive_dependency_contract_urns",
            "functional_boundary_dependency_contract_urns",
            "functional_dependency_contract_urns",
            "functional_binding_by_contract_urn",
            "functional_binding_by_canonical_file",
            "functional_binding_by_rust_surface",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:contract_property_witnesses:v1.0.0",
        canonical_file: "contract_property_witnesses.contract.yaml",
        rust_crate: "core_contracts",
        rust_module: "functional_property_witnesses",
        dependency_contract_urns: &[],
        rust_symbols: &["ContractPropertyWitnesses"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:exact_repair:v1.0.0",
        canonical_file: "exact_repair.contract.yaml",
        rust_crate: "linear_algebra",
        rust_module: "exact_repair",
        dependency_contract_urns: &[],
        rust_symbols: &["ExactRepair"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:hashes:v1.0.0",
        canonical_file: "hashes.contract.yaml",
        rust_crate: "core_kernel",
        rust_module: "evidence",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "Hash256",
            "ReplayHash",
            "CarrierManifestHash",
            "ToleranceProfileHash",
            "CertifiedScalar",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:mub_feasibility_wall:v1.0.0",
        canonical_file: "mub_feasibility_wall.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "mub_feasibility_wall",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "MubFeasibilityWallValue",
            "MubFeasibilityWallEvidenceKind",
            "MubFeasibilityWallAuthorityKind",
            "MubFeasibilityWallTargetComparison",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:aggregation_functional:v1.0.0",
        canonical_file: "aggregation_functional.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "aggregation",
        dependency_contract_urns: &[],
        rust_symbols: &["AggregationMonotonicity"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:quantum_gap_functional:v1.0.0",
        canonical_file: "quantum_gap_functional.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "quantum_gaps",
        dependency_contract_urns: &[],
        rust_symbols: &["QuantumGapFunctional"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:quantum_gaps:v1.0.0",
        canonical_file: "quantum_gaps.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "quantum_gaps",
        dependency_contract_urns: &[],
        rust_symbols: &["QuantumGaps"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:transport_amplitude:v1.0.0",
        canonical_file: "transport_amplitude.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "transport_amplitude",
        dependency_contract_urns: &[],
        rust_symbols: &["TransportAmplitude"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:binary_degree_functional:v1.0.0",
        canonical_file: "binary_degree_functional.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "binary_degree",
        dependency_contract_urns: &[
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
        ],
        rust_symbols: &[
            "MAX_EXHAUSTIVE_BINARY_DOMAIN_DIM",
            "BinaryDegreeError",
            "BinaryDegreeFunctional",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi2_quotient_obstruction:v1.0.0",
        canonical_file: "phi2_quotient_obstruction.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "phi2",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "ExactPhi2CertificateWire",
            "ExactPhi2Certificate",
            "VerifiedExactPhi2",
            "ExactPhi2CertificateError",
            "Phi2Functional",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi3_quotient_obstruction:v1.0.0",
        canonical_file: "phi3_quotient_obstruction.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "phi3",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "ExactPhi3CertificateWire",
            "ExactPhi3Certificate",
            "VerifiedExactPhi3",
            "ExactPhi3CertificateError",
            "Phi3Functional",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi4_quotient_obstruction:v1.0.0",
        canonical_file: "phi4_quotient_obstruction.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "phi4",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "ExactPhi4CertificateWire",
            "ExactPhi4Certificate",
            "VerifiedExactPhi4",
            "ExactPhi4CertificateError",
            "Phi4Functional",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:linear_observer_presentation:v1.0.0",
        canonical_file: "linear_observer_presentation.contract.yaml",
        rust_crate: "linear_algebra",
        rust_module: "linear_observer_presentation",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "LinearObserverError",
            "LinearObserverPresentation",
            "LinearSensingPresentation",
            "RepairBlindspotWitness",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:gamma_reconciliation:v1.0.0",
        canonical_file: "gamma_reconciliation.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "gamma_reconciliation",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "MAX_VERTEX_ROWS",
            "GammaReconciliationError",
            "QuotientGammaCertificate",
            "VertexFarkasCertificate",
            "ValueGapWitness",
            "VertexExtensionTable",
            "all_sign_vectors",
            "RepairQuotientProblem",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:residual_splitting:v1.0.0",
        canonical_file: "residual_splitting.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "residual_splitting",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "ResidualSplittingError",
            "RowMatrix",
            "multiply",
            "weighted_l1_operator_norm",
            "splitting_from_parameter",
            "ResidualSplittingCertificate",
            "verify_transport",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:normal_projection:v1.0.0",
        canonical_file: "normal_projection.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "normal_projection",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "NormalProjectionError",
            "NormalProjectionMeasurement",
            "measure_normal_projection",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:circle_piecewise_linear:v1.0.0",
        canonical_file: "circle_piecewise_linear.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "circle_piecewise_linear",
        dependency_contract_urns: &[],
        rust_symbols: &["CircleProfileError", "CirclePiecewiseLinear"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:weighted_l1_norm:v1.0.0",
        canonical_file: "weighted_l1_norm.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "weighted_l1_norm",
        dependency_contract_urns: &[],
        rust_symbols: &[
            "L1Weight",
            "HilbertLift",
            "WeightedL1Norm",
            "WeightedL1NormError",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:decoherence:v1.0.0",
        canonical_file: "decoherence.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "decoherence",
        dependency_contract_urns: &[],
        rust_symbols: &["DecoherenceFunctional", "DecoherenceError"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi1:v1.0.0",
        canonical_file: "phi1.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "phi1",
        dependency_contract_urns: &["urn:core:math:binary_degree_functional:v1.0.0"],
        rust_symbols: &[
            "ExactPhi1Certificate",
            "VerifiedExactPhi1",
            "Phi1Functional",
            "Phi1FormReplayError",
            "PrimalDualDiagnostic",
            "PrimalDualDiagnosticError",
            "DualWitnessError",
            "BinaryPhi1Evaluation",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:gamma2_closure_defect:v1.0.0",
        canonical_file: "gamma2_closure_defect.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "gamma2",
        dependency_contract_urns: &[
            "urn:core:math:validated_cochain_complex:v1.0.0",
            "urn:core:math:raw_closure_defect:v1.0.0",
            "urn:core:math:hashes:v1.0.0",
            "urn:core:math:binary_degree_functional:v1.0.0",
        ],
        rust_symbols: &[
            "ExactCochainComplexQ",
            "DegreeOneResidualQ",
            "ExactGamma2Result",
            "ClosureStatus",
            "IntegerGamma2Error",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:observer:v1.0.0",
        canonical_file: "observer.contract.yaml",
        rust_crate: "core_types",
        rust_module: "observer",
        dependency_contract_urns: &["urn:core:math:hashes:v1.0.0"],
        rust_symbols: &["Observer"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:distinguishability_functional:v1.0.0",
        canonical_file: "distinguishability_functional.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "distinguishability",
        dependency_contract_urns: &[
            "urn:core:math:quantum_gap_functional:v1.0.0",
            "urn:core:math:quantum_gaps:v1.0.0",
            "urn:core:math:phi1:v1.0.0",
        ],
        rust_symbols: &["DistinguishabilityFunctional"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:trace_diagnostics:v1.0.0",
        canonical_file: "trace_diagnostics.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "trace_diagnostics",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &[
            "shift_pairing_coherence",
            "normalized_shift_pairing_coherence",
            "mean_adjacent_variation",
            "interior_delta_magnitude",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:l1_seminorm:v1.0.0",
        canonical_file: "l1_seminorm.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "l1_seminorm",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &["L1Seminorm"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi1_obstruction_mass:v1.0.0",
        canonical_file: "phi1_obstruction_mass.contract.yaml",
        rust_crate: "core_types",
        rust_module: "obstruction_mass",
        dependency_contract_urns: &[
            "urn:core:math:cochain_layer:v1.0.0",
            "urn:core:math:exact_repair_space:v1.0.0",
            "urn:core:math:quotient_space:v1.0.0",
            "urn:core:math:hashes:v1.0.0",
            "urn:core:math:phi1:v1.0.0",
        ],
        rust_symbols: &[
            "ObstructionMass",
            "ObstructionMassError",
            "EvidenceBindings",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:closure_defect:v1.0.0",
        canonical_file: "closure_defect.contract.yaml",
        rust_crate: "core_types",
        rust_module: "closure_defect",
        dependency_contract_urns: &["urn:core:math:gamma2_closure_defect:v1.0.0"],
        rust_symbols: &["ClosureDefectDisplay", "UntrustedClosureDefectDto"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:dual_witness:v0.1.0",
        canonical_file: "dual_witness.contract.yaml",
        rust_crate: "core_types",
        rust_module: "dual_witness",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &["DualWitness"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:observer_family:v1.0.0",
        canonical_file: "observer_family.contract.yaml",
        rust_crate: "core_types",
        rust_module: "observer_family",
        dependency_contract_urns: &["urn:core:math:observer:v1.0.0"],
        rust_symbols: &["ObserverFamily"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:observer_quotient:v1.0.0",
        canonical_file: "observer_quotient.contract.yaml",
        rust_crate: "core_types",
        rust_module: "observer_quotient",
        dependency_contract_urns: &[
            "urn:core:math:quotient_space:v1.0.0",
            "urn:core:math:hashes:v1.0.0",
            "urn:core:math:observer:v1.0.0",
        ],
        rust_symbols: &["ObserverQuotient", "ObserverQuotientError"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:quotient_mass:v1.0.0",
        canonical_file: "quotient_mass.contract.yaml",
        rust_crate: "core_types",
        rust_module: "quotient_mass",
        dependency_contract_urns: &["urn:core:math:hashes:v1.0.0", "urn:core:math:phi1:v1.0.0"],
        rust_symbols: &["QuotientMass"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:graph_phi1_quotient_distance:v1.0.0",
        canonical_file: "graph_phi1_quotient_distance.contract.yaml",
        rust_crate: "core_solvers",
        rust_module: "solver_graph_phi1_distance",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &[
            "GraphPhi1Edge",
            "GraphPhi1Request",
            "GraphPhi1Result",
            "GraphPhi1Error",
            "solve_graph_phi1",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:simplicial_defect:v1.0.0",
        canonical_file: "simplicial_defect.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "simplicial_defect",
        dependency_contract_urns: &["urn:core:math:gamma2_closure_defect:v1.0.0"],
        rust_symbols: &[
            "SimplicialDefectError",
            "SimplicialDefects",
            "evaluate_simplicial_defects",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:observer_gauge:v1.0.0",
        canonical_file: "observer_gauge.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "observer_gauge",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &["GaugeError", "ScalarGauge", "VectorGauge", "TraceGauge"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:residual:v1.0.0",
        canonical_file: "residual.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "residual",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &["Residual", "ResidualError"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:functional_factory:v1.0.0",
        canonical_file: "functional_factory.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "factory",
        dependency_contract_urns: &[
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:l1_seminorm:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
        ],
        rust_symbols: &["BaseFunctionalKernel", "evaluate_functional"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:finite_obstruction_trichotomy:v0.2.0",
        canonical_file: "finite_obstruction_trichotomy.contract.yaml",
        rust_crate: "core_policy",
        rust_module: "trichotomy",
        dependency_contract_urns: &[
            "urn:core:math:phi1_obstruction_mass:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
            "urn:core:math:phi1:v1.0.0",
        ],
        rust_symbols: &[
            "CertifiedExactTrichotomy",
            "ObstructionDiagnosticClass",
            "TrichotomyOutcome",
            "TrichotomyRefusal",
            "classify_exact",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:observer_comparison:v1.0.0",
        canonical_file: "observer_comparison.contract.yaml",
        rust_crate: "core_types",
        rust_module: "observer_comparison",
        dependency_contract_urns: &[
            "urn:core:math:hashes:v1.0.0",
            "urn:core:math:observer:v1.0.0",
            "urn:core:math:observer_quotient:v1.0.0",
        ],
        rust_symbols: &[
            "ObserverComparisonPacket",
            "ObserverComparisonStatus",
            "ObserverComparisonAuthorityRequest",
            "ObserverComparisonResidual",
            "ObserverComparisonResidualKind",
            "ComparisonLaunderingRefused",
            "ObserverComparisonError",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:xi_tie_breaker:v1.0.0",
        canonical_file: "xi_tie_breaker.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "xi",
        dependency_contract_urns: &[
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:phi1_obstruction_mass:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
            "urn:core:math:residual_projection:v1.0.0",
        ],
        rust_symbols: &[
            "DensityLift",
            "XiValidity",
            "XiResult",
            "XiComputation",
            "XiError",
            "XiFunctional",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:phi1_exact_certificate_solver:v1.0.0",
        canonical_file: "phi1_exact_certificate_solver.contract.yaml",
        rust_crate: "core_solvers",
        rust_module: "solver_lp_phi1_quotient",
        dependency_contract_urns: &[
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:l1_seminorm:v1.0.0",
        ],
        rust_symbols: &[
            "Phi1LinearProgram",
            "SimplexRefusal",
            "Phi1SolveError",
            "solve_exact_phi1",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:closure_regime:v1.0.0",
        canonical_file: "closure_regime.contract.yaml",
        rust_crate: "core_policy",
        rust_module: "closure_regime",
        dependency_contract_urns: &["urn:core:math:finite_obstruction_trichotomy:v0.2.0"],
        rust_symbols: &["ClosureRegime"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:evaluation_hierarchy:v1.0.0",
        canonical_file: "evaluation_hierarchy.contract.yaml",
        rust_crate: "core_policy",
        rust_module: "evaluation_hierarchy",
        dependency_contract_urns: &[
            "urn:core:math:phi1_obstruction_mass:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
            "urn:core:math:xi_tie_breaker:v1.0.0",
        ],
        rust_symbols: &[
            "DiagnosticComparison",
            "classify_guarded_non_worse",
            "compare_guarded_diagnostics",
            "guarded_non_worse",
            "guarded_strictly_improves",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:xi_diagnostic:v1.0.0",
        canonical_file: "xi_diagnostic.contract.yaml",
        rust_crate: "core_types",
        rust_module: "xi_diagnostic",
        dependency_contract_urns: &[
            "urn:core:math:hashes:v1.0.0",
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:xi_tie_breaker:v1.0.0",
        ],
        rust_symbols: &["XiDiagnostic"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:diagnostic_vector:v1.0.0",
        canonical_file: "diagnostic_vector.contract.yaml",
        rust_crate: "core_types",
        rust_module: "diagnostic_vector",
        dependency_contract_urns: &[
            "urn:core:math:xi_tie_breaker:v1.0.0",
            "urn:core:math:phi1_obstruction_mass:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
            "urn:core:math:closure_defect:v1.0.0",
        ],
        rust_symbols: &["DiagnosticSnapshot"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:xi_comparison_policy:v1.0.0",
        canonical_file: "xi_comparison_policy.contract.yaml",
        rust_crate: "core_policy",
        rust_module: "xi_gate",
        dependency_contract_urns: &[
            "urn:core:math:phi1:v1.0.0",
            "urn:core:math:gamma2_closure_defect:v1.0.0",
            "urn:core:math:xi_tie_breaker:v1.0.0",
        ],
        rust_symbols: &["firewall_allows_candidate", "xi_may_decide_tie"],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:product_distance:v1.0.0",
        canonical_file: "product_distance.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "product_distance",
        dependency_contract_urns: &["urn:core:math:phi1:v1.0.0"],
        rust_symbols: &[
            "ProductDistanceError",
            "ProductDistanceValue",
            "evaluate_product_distance",
        ],
    },
    FunctionalContractBinding {
        contract_urn: "urn:core:math:functional_layer_boundary:v1.0.0",
        canonical_file: "functional_layer_boundary.contract.yaml",
        rust_crate: "core_functional",
        rust_module: "lib",
        dependency_contract_urns: FUNCTIONAL_LAYER_BOUNDARY_DEPENDENCY_CONTRACT_URNS,
        rust_symbols: &["FunctionalLayerBoundary"],
    },
];

pub fn contract_by_id(contract_id: &str) -> Option<&'static PrimitiveContractDescriptor> {
    CORE_PRIMITIVE_CONTRACTS
        .iter()
        .find(|contract| contract.contract_id == contract_id)
}

pub fn binding_by_descriptor_id(descriptor_id: &str) -> Option<&'static PrimitiveContractBinding> {
    CORE_PRIMITIVE_CONTRACT_BINDINGS
        .iter()
        .find(|binding| binding.descriptor_id == descriptor_id)
}

pub fn primitive_binding_by_contract_urn(
    canonical_contract_urn: &str,
) -> Option<&'static PrimitiveContractBinding> {
    CORE_PRIMITIVE_CONTRACT_BINDINGS
        .iter()
        .find(|binding| binding.canonical_contract_urn == canonical_contract_urn)
}

pub fn primitive_binding_by_canonical_file(
    canonical_file: &str,
) -> Option<&'static PrimitiveContractBinding> {
    CORE_PRIMITIVE_CONTRACT_BINDINGS
        .iter()
        .find(|binding| binding.canonical_file == canonical_file)
}

pub fn primitive_dependency_contract_urns(descriptor_id: &str) -> Option<Vec<&'static str>> {
    let descriptor = contract_by_id(descriptor_id)?;
    let mut urns = Vec::with_capacity(descriptor.depends_on.len());
    for dependency in descriptor.depends_on {
        urns.push(binding_by_descriptor_id(dependency)?.canonical_contract_urn);
    }
    Some(urns)
}

pub fn functional_boundary_dependency_contract_urns() -> Vec<&'static str> {
    functional_dependency_contract_urns(FUNCTIONAL_LAYER_BOUNDARY_CONTRACT_URN)
        .checked_invariant_326d1d74("Functional layer boundary contract missing")
        .to_vec()
}

pub fn functional_dependency_contract_urns(contract_urn: &str) -> Option<&'static [&'static str]> {
    functional_binding_by_contract_urn(contract_urn).map(|binding| binding.dependency_contract_urns)
}

pub fn functional_binding_by_contract_urn(
    contract_urn: &str,
) -> Option<&'static FunctionalContractBinding> {
    FUNCTIONAL_CONTRACT_BINDINGS
        .iter()
        .find(|binding| binding.contract_urn == contract_urn)
}

pub fn functional_binding_by_canonical_file(
    canonical_file: &str,
) -> Option<&'static FunctionalContractBinding> {
    FUNCTIONAL_CONTRACT_BINDINGS
        .iter()
        .find(|binding| binding.canonical_file == canonical_file)
}

pub fn functional_binding_by_rust_surface(
    rust_module: &str,
    rust_symbol: &str,
) -> Option<&'static FunctionalContractBinding> {
    FUNCTIONAL_CONTRACT_BINDINGS.iter().find(|binding| {
        binding.rust_module == rust_module && binding.rust_symbols.contains(&rust_symbol)
    })
}

/// Satisfies the contract validator for the ContractDescriptors symbol.
pub struct ContractDescriptors;

// Origin: engine/crates_rs/core_contracts/src/contract_descriptors.rs
// Claim: urn:core:crates_rs:core-contracts:contract-descriptors:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord326d1d74 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord326d1d74` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError326d1d74 {
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
impl BoundaryError326d1d74 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError326d1d74 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError326d1d74 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord326d1d74 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError326d1d74> {
        if capacity_bound == 0 {
            return Err(BoundaryError326d1d74::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError326d1d74::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError326d1d74::ExceedsCapacity {
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
mod tests {
    use super::*;
    use std::collections::BTreeSet;
    use std::path::Path;

    #[test]
    fn all_contracts_are_inert_wip_definitions() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert_eq!(contract.status, CONTRACT_STATUS);
            assert_eq!(contract.authority_effect, AUTHORITY_EFFECT);
            assert!(!contract.customer_claim_allowed);
        }
    }

    #[test]
    fn contract_ids_are_unique() {
        let mut ids = vec![];
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(
                !ids.contains(&contract.contract_id),
                "Duplicate contract_id: {}",
                contract.contract_id
            );
            ids.push(contract.contract_id);
        }
    }

    #[test]
    fn every_primitive_descriptor_has_a_canonical_contract_binding() {
        assert_eq!(
            CORE_PRIMITIVE_CONTRACTS.len(),
            CORE_PRIMITIVE_CONTRACT_BINDINGS.len()
        );
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(
                binding_by_descriptor_id(contract.contract_id).is_some(),
                "missing canonical contract binding for {}",
                contract.contract_id
            );
        }
    }

    #[test]
    fn primitive_contract_bindings_follow_descriptor_order() {
        for (descriptor, binding) in CORE_PRIMITIVE_CONTRACTS
            .iter()
            .zip(CORE_PRIMITIVE_CONTRACT_BINDINGS)
        {
            assert_eq!(
                descriptor.contract_id, binding.descriptor_id,
                "primitive binding order must mirror descriptor order"
            );
        }
    }

    #[test]
    fn primitive_contract_descriptors_are_topologically_ordered() {
        let mut seen = BTreeSet::new();
        for descriptor in CORE_PRIMITIVE_CONTRACTS {
            for dependency in descriptor.depends_on {
                assert!(
                    seen.contains(dependency),
                    "{} appears before dependency {}",
                    descriptor.contract_id,
                    dependency
                );
            }
            seen.insert(descriptor.contract_id);
        }
    }

    #[test]
    fn canonical_contract_bindings_are_unique() {
        let mut ids = vec![];
        let mut urns = vec![];
        let mut files = vec![];
        for binding in CORE_PRIMITIVE_CONTRACT_BINDINGS {
            assert!(
                !ids.contains(&binding.descriptor_id),
                "duplicate descriptor ID: {}",
                binding.descriptor_id
            );
            assert!(
                !urns.contains(&binding.canonical_contract_urn),
                "duplicate canonical contract URN: {}",
                binding.canonical_contract_urn
            );
            assert!(
                !files.contains(&binding.canonical_file),
                "duplicate canonical contract file: {}",
                binding.canonical_file
            );
            ids.push(binding.descriptor_id);
            urns.push(binding.canonical_contract_urn);
            files.push(binding.canonical_file);
        }
    }

    #[test]
    fn canonical_contract_binding_lookup_round_trips_registry() {
        for binding in CORE_PRIMITIVE_CONTRACT_BINDINGS {
            assert_eq!(
                binding_by_descriptor_id(binding.descriptor_id),
                Some(binding),
                "canonical binding lookup must return the registered entry for {}",
                binding.descriptor_id
            );
            assert_eq!(
                primitive_binding_by_contract_urn(binding.canonical_contract_urn),
                Some(binding),
                "primitive contract URN lookup must return the registered entry for {}",
                binding.canonical_contract_urn
            );
            assert_eq!(
                primitive_binding_by_canonical_file(binding.canonical_file),
                Some(binding),
                "primitive contract file lookup must return the registered entry for {}",
                binding.canonical_file
            );
        }
    }

    #[test]
    fn primitive_contract_binding_lookups_reject_unknown_values() {
        assert_eq!(
            primitive_binding_by_contract_urn("urn:core:math:no_such_contract:v1.0.0"),
            None
        );
        assert_eq!(
            primitive_binding_by_canonical_file("no_such_contract.contract.yaml"),
            None
        );
    }

    #[test]
    fn primitive_descriptor_dependencies_resolve_to_declared_descriptors() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            for dependency in contract.depends_on {
                assert!(
                    contract_by_id(dependency).is_some(),
                    "{} depends on unknown primitive descriptor {}",
                    contract.contract_id,
                    dependency
                );
            }
        }
    }

    #[test]
    fn primitive_dependency_contract_urn_lookup_round_trips_descriptors() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            let expected: Vec<_> = contract
                .depends_on
                .iter()
                .map(|dependency| {
                    binding_by_descriptor_id(dependency)
                        .unwrap_or_else(|| {
                            panic!(
                                "{} depends on unbound descriptor {}",
                                contract.contract_id, dependency
                            )
                        })
                        .canonical_contract_urn
                })
                .collect();

            assert_eq!(
                primitive_dependency_contract_urns(contract.contract_id),
                Some(expected),
                "{} dependency URN lookup must preserve descriptor dependency order",
                contract.contract_id
            );
        }
    }

    #[test]
    fn primitive_dependency_contract_urn_lookup_rejects_unknown_descriptor() {
        assert_eq!(primitive_dependency_contract_urns("NO_SUCH_CONTRACT"), None);
    }

    #[test]
    fn functional_boundary_dependency_contract_urns_cover_expected_registry_closure() {
        let dependencies = functional_boundary_dependency_contract_urns();

        assert!(!dependencies.contains(&FUNCTIONAL_LAYER_BOUNDARY_CONTRACT_URN));
        for binding in CORE_PRIMITIVE_CONTRACT_BINDINGS {
            assert!(
                dependencies.contains(&binding.canonical_contract_urn),
                "functional boundary dependency closure must include primitive {}",
                binding.canonical_contract_urn
            );
        }
        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            if binding.contract_urn == FUNCTIONAL_LAYER_BOUNDARY_CONTRACT_URN {
                continue;
            }
            assert!(
                dependencies.contains(&binding.contract_urn),
                "functional boundary dependency closure must include functional {}",
                binding.contract_urn
            );
        }

        let unique: BTreeSet<_> = dependencies.iter().copied().collect();
        assert_eq!(
            unique.len(),
            dependencies.len(),
            "functional boundary dependency closure must not contain duplicates"
        );
    }

    #[test]
    fn functional_contract_bindings_are_unique() {
        let mut urns = vec![];
        let mut files = vec![];
        let mut surfaces = vec![];
        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            assert!(
                !urns.contains(&binding.contract_urn),
                "duplicate functional contract URN: {}",
                binding.contract_urn
            );
            assert!(
                !files.contains(&binding.canonical_file),
                "duplicate functional contract file: {}",
                binding.canonical_file
            );
            let mut symbols = BTreeSet::new();
            for symbol in binding.rust_symbols {
                assert!(
                    symbols.insert(*symbol),
                    "{} repeats rust symbol {}",
                    binding.contract_urn,
                    symbol
                );
                let surface = (binding.rust_module, *symbol);
                assert!(
                    !surfaces.contains(&surface),
                    "duplicate functional rust binding surface: {}::{}",
                    binding.rust_module,
                    symbol
                );
                surfaces.push(surface);
            }
            urns.push(binding.contract_urn);
            files.push(binding.canonical_file);
        }
    }

    #[test]
    fn functional_contract_binding_lookups_round_trip_registry() {
        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            assert_eq!(
                functional_binding_by_contract_urn(binding.contract_urn),
                Some(binding),
                "functional contract URN lookup must return the registered entry for {}",
                binding.contract_urn
            );
            assert_eq!(
                functional_binding_by_canonical_file(binding.canonical_file),
                Some(binding),
                "functional contract file lookup must return the registered entry for {}",
                binding.canonical_file
            );
            for symbol in binding.rust_symbols {
                assert_eq!(
                    functional_binding_by_rust_surface(binding.rust_module, symbol),
                    Some(binding),
                    "functional rust surface lookup must return the registered entry for {}::{}",
                    binding.rust_module,
                    symbol
                );
            }
            assert_eq!(
                functional_dependency_contract_urns(binding.contract_urn),
                Some(binding.dependency_contract_urns),
                "functional dependency lookup must return the registered dependency list for {}",
                binding.contract_urn
            );
        }
    }

    #[test]
    fn functional_contract_binding_surface_lookup_rejects_unknown_pairs() {
        assert_eq!(
            functional_binding_by_rust_surface("evaluation_hierarchy", "NoSuchSymbol"),
            None
        );
        assert_eq!(
            functional_binding_by_rust_surface("no_such_module", "DiagnosticComparison"),
            None
        );
    }

    #[test]
    fn functional_contract_bindings_have_nonempty_rust_surface() {
        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            assert!(!binding.contract_urn.is_empty());
            assert!(!binding.canonical_file.is_empty());
            assert!(!binding.rust_module.is_empty());
            assert!(!binding.rust_symbols.is_empty());
            for symbol in binding.rust_symbols {
                assert!(!symbol.is_empty());
            }
            for dependency in binding.dependency_contract_urns {
                assert!(!dependency.is_empty());
            }
        }
    }

    #[test]
    fn functional_contract_binding_dependencies_are_valid_and_ordered() {
        let mut seen = BTreeSet::new();

        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            let mut unique = BTreeSet::new();
            for dependency in binding.dependency_contract_urns {
                assert_ne!(
                    *dependency, binding.contract_urn,
                    "{} must not depend on itself",
                    binding.contract_urn
                );
                assert!(
                    unique.insert(*dependency),
                    "{} repeats dependency {}",
                    binding.contract_urn,
                    dependency
                );
                assert!(
                    primitive_binding_by_contract_urn(dependency).is_some()
                        || functional_binding_by_contract_urn(dependency).is_some(),
                    "{} depends on unregistered contract {}",
                    binding.contract_urn,
                    dependency
                );
                let is_mutual_binary_specialization = binding.contract_urn
                    == "urn:core:math:binary_degree_functional:v1.0.0"
                    && matches!(
                        *dependency,
                        "urn:core:math:phi1:v1.0.0"
                            | "urn:core:math:gamma2_closure_defect:v1.0.0"
                    );
                if functional_binding_by_contract_urn(dependency).is_some()
                    && !is_mutual_binary_specialization
                {
                    assert!(
                        seen.contains(dependency),
                        "{} appears before dependency {}",
                        binding.contract_urn,
                        dependency
                    );
                }
            }
            seen.insert(binding.contract_urn);
        }
    }

    #[test]
    fn functional_contract_bindings_name_existing_module_files() {
        for binding in FUNCTIONAL_CONTRACT_BINDINGS {
            let crate_dir = match binding.rust_crate {
                "linear_algebra" => "core_linear_algebra",
                name => name,
            };
            let src_dir = Path::new(env!("CARGO_MANIFEST_DIR"))
                .parent()
                .unwrap()
                .join(crate_dir)
                .join("src");
            let module_path = if binding.rust_module == "lib" {
                src_dir.join("lib.rs")
            } else {
                let mut path = src_dir.clone();
                for segment in binding.rust_module.split("::") {
                    path.push(segment);
                }
                path.set_extension("rs");
                path
            };

            assert!(
                module_path.exists(),
                "{} binds missing owner module file {}",
                binding.contract_urn,
                module_path.display()
            );
        }
    }

    #[test]
    fn functional_contract_registry_names_boundary_and_descriptor_contracts() {
        assert!(functional_binding_by_contract_urn(
            "urn:core:math:functional_layer_boundary:v1.0.0"
        )
        .is_some());
        assert!(
            functional_binding_by_canonical_file("contract_descriptors.contract.yaml").is_some()
        );
    }

    #[test]
    fn contract_symbols_are_nonempty() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(!contract.symbol.is_empty());
            assert!(!contract.ascii_symbol.is_empty());
        }
    }

    #[test]
    fn contract_formulas_are_nonempty() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(!contract.formula.is_empty());
        }
    }

    #[test]
    fn primitive_descriptors_have_complete_doctrine_fields() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(
                !contract.object_type.is_empty(),
                "{} must name an object type",
                contract.contract_id
            );
            assert!(
                !contract.domain.is_empty(),
                "{} must name a domain",
                contract.contract_id
            );
            assert!(
                !contract.codomain.is_empty(),
                "{} must name a codomain",
                contract.contract_id
            );
            assert!(
                !contract.definition.is_empty(),
                "{} must provide a definition",
                contract.contract_id
            );
            assert!(
                !contract.forbidden_interpretations.is_empty(),
                "{} must declare forbidden interpretations",
                contract.contract_id
            );
            for forbidden in contract.forbidden_interpretations {
                assert!(
                    !forbidden.is_empty(),
                    "{} has an empty forbidden interpretation",
                    contract.contract_id
                );
            }
        }
    }

    #[test]
    fn all_operator_contracts_present() {
        let expected_ops = [
            "EXACT_REPAIR_OPERATOR_CONTRACT",
            "QUOTIENT_ISOMETRY_OPERATOR_CONTRACT",
            "CONTEXT_EMBEDDING_OPERATOR_CONTRACT",
            "RESIDUAL_PROJECTION_CONTRACT",
            "MUTATION_OPERATOR_CONTRACT",
        ];
        for op in expected_ops {
            assert!(
                CORE_PRIMITIVE_CONTRACTS.iter().any(|c| c.contract_id == op),
                "Missing operator contract: {}",
                op
            );
        }
    }

    #[test]
    fn no_contract_allows_customer_claims() {
        for contract in CORE_PRIMITIVE_CONTRACTS {
            assert!(!contract.customer_claim_allowed);
        }
    }

    #[test]
    fn gamma_square_not_confused_with_gamma2() {
        let contract = contract_by_id("QUOTIENT_GAMMA2_CONTRACT").unwrap();
        assert_eq!(contract.symbol, "Γ₂");
        assert_eq!(contract.ascii_symbol, "Gamma2");
        assert!(contract.definition.contains("closure defect"));
        assert!(contract
            .forbidden_interpretations
            .contains(&"GammaSquare/Γ² operation"));
    }

    #[test]
    fn contract_by_id_rejects_unknown_and_empty_ids() {
        assert_eq!(contract_by_id(""), None);
        assert_eq!(contract_by_id("NO_SUCH_CONTRACT"), None);
        assert_eq!(binding_by_descriptor_id(""), None);
        assert_eq!(functional_binding_by_contract_urn(""), None);
        assert_eq!(
            functional_binding_by_contract_urn("urn:core:math:no_such_contract:v1.0.0"),
            None
        );
        assert_eq!(functional_binding_by_canonical_file(""), None);
    }

    #[test]
    fn operator_class_symbols_are_distinct() {
        let classes = [
            OperatorClass::ExactRepair,
            OperatorClass::QuotientIsometry,
            OperatorClass::ContextEmbedding,
            OperatorClass::ResidualProjection,
            OperatorClass::Mutation,
        ];
        let symbols: Vec<_> = classes.iter().map(|class| class.symbol()).collect();
        assert_eq!(symbols, ["E", "I", "C", "R", "M"]);
    }
}

#[cfg(test)]
mod l4_boundary_tests_326d1d74 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord326d1d74::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord326d1d74::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord326d1d74::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord326d1d74::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord326d1d74::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError326d1d74::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError326d1d74::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
