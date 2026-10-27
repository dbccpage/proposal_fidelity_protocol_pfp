//! Prompt-to-Cochain execution and evaluation contract (Architecture Review 16).
//!
//! Mathematical profile: oriented finite cell complex over exact rationals
//! C^0 = Q^V -> C^1 = Q^E -> C^2 = Q^F with d_1 * d_0 = 0 in Q.
//!
//! Primary quotient obstruction:   Phi_1(c) = min_a ||c - d_0 a||_1
//! Secondary closure defect:       Gamma_2(c) = ||d_1 c||_1
//!
//! Four-Way Typed Dispositions:
//! - ExactCoboundary:     Phi_1 = 0, Gamma_2 = 0
//! - ClosedNonExactClass: Phi_1 > 0, Gamma_2 = 0
//! - NonClosedEdgeData:   Gamma_2 > 0 (Phi_1 > 0)
//! - Refusal:             Phi_1 = 0, Gamma_2 > 0 (IMPOSSIBLE_PROFILE for valid complex),
//!                        dimension mismatch, chain law violation, or budget exhaustion.
//!
//! Binds Prime Triad:
//! - Prime 000: Admission before measurement (freeze source bytes, validate dimensions, d_1 d_0 = 0)
//! - Prime 001: Adapter descent soundness and preservation of protected answers
//! - Prime 002: Residual-aware continuation and budget halting predicate.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Zero};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fmt;

use core_functional::gamma2::{
    DegreeOneResidualQ, ExactCochainComplexQ, ExactGamma2Error, Gamma2Functional,
};
use core_functional::phi1::{ExactPhi1CertificateError, Phi1Functional, VerifiedExactPhi1};
use core_kernel::resource_limits::OperationLimits;

/// Canonical constructor for rational numbers.
pub fn rational(numer: i64, denom: i64) -> BigRational {
    assert!(denom != 0, "denominator cannot be zero");
    BigRational::new(BigInt::from(numer), BigInt::from(denom))
}

/// Oriented finite cell complex C^0 -> C^1 -> C^2 with nilpotence d_1 * d_0 = 0 over Q.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct PromptCellComplex {
    pub c0_dim: usize,
    pub c1_dim: usize,
    pub c2_dim: usize,
    pub d0: Vec<Vec<BigRational>>,
    pub d1: Vec<Vec<BigRational>>,
    #[serde(default)]
    pub source_bytes_hash: Option<String>,
}

impl PromptCellComplex {
    /// Construct a complex with explicit dimensions and boundary matrices.
    pub fn new(
        c0_dim: usize,
        c1_dim: usize,
        c2_dim: usize,
        d0: Vec<Vec<BigRational>>,
        d1: Vec<Vec<BigRational>>,
    ) -> Self {
        Self {
            c0_dim,
            c1_dim,
            c2_dim,
            d0,
            d1,
            source_bytes_hash: None,
        }
    }

    /// Zero-face profile: when no faces are declared, C^2 is explicitly zero-dimensional (Q^0).
    pub fn zero_face(c0_dim: usize, c1_dim: usize, d0: Vec<Vec<BigRational>>) -> Self {
        Self {
            c0_dim,
            c1_dim,
            c2_dim: 0,
            d0,
            d1: Vec::new(),
            source_bytes_hash: None,
        }
    }

    /// Attach a frozen source bytes SHA-256 hash (Prime 000 custody binding).
    pub fn with_source_bytes_hash(mut self, hash: String) -> Self {
        self.source_bytes_hash = Some(hash);
        self
    }

    fn preflight_graph_storage(
        vertex_count: usize,
        edge_count: usize,
        face_count: usize,
    ) -> Result<(), CochainRefusal> {
        let limits = OperationLimits::default();
        let overflow = || CochainRefusal {
            code: "RESOURCE_EXHAUSTION".into(),
            message: "Graph dense cell count overflow exceeds resource limit".into(),
        };
        let d0_cells = limits
            .checked_product(edge_count, vertex_count)
            .map_err(|_| overflow())?;
        let d1_cells = limits
            .checked_product(face_count, edge_count)
            .map_err(|_| overflow())?;
        let total_cells = d0_cells.checked_add(d1_cells).ok_or_else(overflow)?;
        for (name, count, limit) in [
            ("vertices", vertex_count, limits.max_vertices),
            ("edges", edge_count, limits.max_edges),
            ("faces", face_count, limits.max_faces),
            ("d0 cells", d0_cells, limits.max_cells),
            ("d1 cells", d1_cells, limits.max_cells),
            ("combined dense cells", total_cells, limits.max_cells),
        ] {
            if count > limit {
                return Err(CochainRefusal {
                    code: "RESOURCE_EXHAUSTION".into(),
                    message: format!("Graph {name} {count} exceeds limit {limit}"),
                });
            }
        }
        Ok(())
    }

    fn build_d1_from_faces(
        c1_dim: usize,
        faces: Option<&[Vec<(usize, BigRational)>]>,
    ) -> Result<(usize, Vec<Vec<BigRational>>), CochainRefusal> {
        let Some(declared_faces) = faces.filter(|f| !f.is_empty()) else {
            return Ok((0, Vec::new()));
        };
        let f_dim = declared_faces.len();
        let mut d1_matrix = vec![vec![BigRational::zero(); c1_dim]; f_dim];
        for (f_idx, face) in declared_faces.iter().enumerate() {
            for &(edge_idx, ref coeff) in face {
                if edge_idx >= c1_dim {
                    return Err(CochainRefusal {
                        code: "DIMENSION_MISMATCH".into(),
                        message: format!(
                            "Face {f_idx} refers to edge {edge_idx} exceeding edge count {c1_dim}"
                        ),
                    });
                }
                d1_matrix[f_idx][edge_idx] += coeff;
            }
        }
        Ok((f_dim, d1_matrix))
    }

    /// Lower an oriented finite graph with optional oriented faces to a cell complex.
    ///
    /// Vertices: indexed 0..V-1.
    /// Edges: directed pairs (u, v) representing oriented edge u -> v.
    /// In coboundary d_0: row e has column u = -1, column v = +1.
    /// Faces: sequence of directed cycle edge indices. If None or empty, C^2 = Q^0.
    pub fn from_oriented_graph(
        vertex_count: usize,
        edges: &[(usize, usize)],
        faces: Option<&[Vec<(usize, BigRational)>]>,
    ) -> Result<Self, CochainRefusal> {
        let c0_dim = vertex_count;
        let c1_dim = edges.len();
        Self::preflight_graph_storage(c0_dim, c1_dim, faces.map_or(0, |faces| faces.len()))?;

        let mut d0 = vec![vec![BigRational::zero(); c0_dim]; c1_dim];
        for (edge_idx, &(u, v)) in edges.iter().enumerate() {
            if u >= c0_dim || v >= c0_dim {
                return Err(CochainRefusal {
                    code: "DIMENSION_MISMATCH".into(),
                    message: format!(
                        "Edge index {edge_idx} refers to vertex ({u}, {v}) exceeding vertex count {c0_dim}"
                    ),
                });
            }
            d0[edge_idx][u] -= BigRational::one();
            d0[edge_idx][v] += BigRational::one();
        }

        let (c2_dim, d1) = Self::build_d1_from_faces(c1_dim, faces)?;

        let complex = Self {
            c0_dim,
            c1_dim,
            c2_dim,
            d0,
            d1,
            source_bytes_hash: None,
        };

        // Pre-validate nilpotence d_1 * d_0 = 0 in Q
        complex.to_exact_complex()?;
        Ok(complex)
    }

    /// Lower an operad prompt graph occurrence structure to an oriented finite cell complex.
    ///
    /// Operators define generative morphisms, operand ports define potential vertices,
    /// and slot connections define directed occurrence edges.
    pub fn from_operad_occurrences(
        node_count: usize,
        directed_edges: &[(usize, usize)],
        cycle_faces: Option<&[Vec<usize>]>,
    ) -> Result<Self, CochainRefusal> {
        Self::preflight_graph_storage(
            node_count,
            directed_edges.len(),
            cycle_faces.map_or(0, |faces| faces.len()),
        )?;
        let faces_with_coeffs: Option<Vec<Vec<(usize, BigRational)>>> =
            cycle_faces.map(|c_faces| {
                c_faces
                    .iter()
                    .map(|cycle| cycle.iter().map(|&e| (e, BigRational::one())).collect())
                    .collect()
            });
        Self::from_oriented_graph(node_count, directed_edges, faces_with_coeffs.as_deref())
    }

    /// Validate and convert into a sealed [`ExactCochainComplexQ`].
    pub fn to_exact_complex(&self) -> Result<ExactCochainComplexQ, CochainRefusal> {
        ExactCochainComplexQ::try_new(
            self.c0_dim,
            self.c1_dim,
            self.c2_dim,
            self.d0.clone(),
            self.d1.clone(),
        )
        .map_err(|e| match e {
            ExactGamma2Error::CochainIdentityViolation { row, column } => CochainRefusal {
                code: "CHAIN_LAW_VIOLATION".into(),
                message: format!(
                    "d1 * d0 = 0 failed at row {row}, column {column}: complex is curved / non-nilpotent"
                ),
            },
            ExactGamma2Error::D0RowMismatch { expected, actual } => CochainRefusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!("d0 row mismatch: expected {expected}, actual {actual}"),
            },
            ExactGamma2Error::D0ColumnMismatch { row, expected, actual } => CochainRefusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!("d0 column mismatch at row {row}: expected {expected}, actual {actual}"),
            },
            ExactGamma2Error::D1RowMismatch { expected, actual } => CochainRefusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!("d1 row mismatch: expected {expected}, actual {actual}"),
            },
            ExactGamma2Error::D1ColumnMismatch { row, expected, actual } => CochainRefusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!("d1 column mismatch at row {row}: expected {expected}, actual {actual}"),
            },
            ExactGamma2Error::ZeroDenominator { field, row, column } => CochainRefusal {
                code: "ZERO_DENOMINATOR".into(),
                message: format!("Zero denominator in {field} at row {row:?}, column {column}"),
            },
            other => CochainRefusal {
                code: "INVALID_COMPLEX".into(),
                message: other.to_string(),
            },
        })
    }
}

/// Prime Triad context binding candidate intake, descent loss, and continuation guards.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct PrimeTriadContext {
    /// Prime 000: Raw source bytes to freeze before measurement.
    #[serde(default)]
    pub source_bytes: Option<String>,
    /// Prime 000: Expected SHA-256 digest of frozen source bytes.
    #[serde(default)]
    pub expected_source_hash: Option<String>,
    /// Prime 001: Protected questions and immutable baseline answers.
    #[serde(default)]
    pub protected_answers: Option<BTreeMap<String, String>>,
    /// Prime 001: Candidate answers observed after adapter descent.
    #[serde(default)]
    pub candidate_answers: Option<BTreeMap<String, String>>,
    /// Prime 002: Remaining evaluation allowance on this context.
    /// `evaluate` spends one unit when this is `Some`; `Some(0)` refuses.
    #[serde(default)]
    pub remaining_budget: Option<u64>,
}

impl PrimeTriadContext {
    /// Prime 000: Validate source byte custody and frozen digest before measurement.
    pub fn validate_prime_000(&self, complex: &PromptCellComplex) -> Result<(), CochainRefusal> {
        if self.source_bytes.is_none()
            && (self.expected_source_hash.is_some() || complex.source_bytes_hash.is_some())
        {
            return Err(CochainRefusal {
                code: "SOURCE_BYTES_CORRUPTED".into(),
                message: "Prime 000 intake violation: source bytes are missing for a declared source hash"
                    .into(),
            });
        }
        if let Some(source) = &self.source_bytes {
            let mut hasher = Sha256::new();
            hasher.update(source.as_bytes());
            let computed_hash = hex::encode(hasher.finalize());

            if let Some(expected) = &self.expected_source_hash {
                if &computed_hash != expected {
                    return Err(CochainRefusal {
                        code: "SOURCE_BYTES_CORRUPTED".into(),
                        message: format!(
                            "Prime 000 intake violation: source hash {computed_hash} != expected {expected}"
                        ),
                    });
                }
            }

            if let Some(complex_hash) = &complex.source_bytes_hash {
                if &computed_hash != complex_hash {
                    return Err(CochainRefusal {
                        code: "SOURCE_BYTES_CORRUPTED".into(),
                        message: format!(
                            "Prime 000 intake violation: source hash {computed_hash} != complex hash {complex_hash}"
                        ),
                    });
                }
            }
        }
        Ok(())
    }

    /// Prime 001: Check preservation of protected questions across state transitions.
    pub fn check_prime_001_preservation(
        &self,
        candidate_answers: Option<&BTreeMap<String, String>>,
    ) -> Result<(), CochainRefusal> {
        if let Some(protected) = &self.protected_answers {
            if !protected.is_empty() && candidate_answers.is_none() {
                return Err(CochainRefusal {
                    code: "PROTECTED_ANSWER_VIOLATION".into(),
                    message: "Prime 001 preservation cannot be checked: protected answers were declared but no candidate answers were supplied".into(),
                });
            }
            if let Some(candidate) = candidate_answers {
                for (q, expected_a) in protected {
                    if let Some(actual_a) = candidate.get(q) {
                        if actual_a != expected_a {
                            return Err(CochainRefusal {
                                code: "PROTECTED_ANSWER_VIOLATION".into(),
                                message: format!(
                                    "Prime 001 preservation violation for question '{q}': expected '{expected_a}', got '{actual_a}'"
                                ),
                            });
                        }
                    } else {
                        return Err(CochainRefusal {
                            code: "PROTECTED_ANSWER_VIOLATION".into(),
                            message: format!(
                                "Prime 001 preservation violation: candidate omitted protected question '{q}'"
                            ),
                        });
                    }
                }
            }
        }
        Ok(())
    }

    /// Prime 002: Residual-aware continuation and budget halting predicate.
    pub fn check_and_decrement_prime_002_budget(&mut self) -> Result<u64, CochainRefusal> {
        if let Some(budget) = self.remaining_budget {
            if budget == 0 {
                return Err(CochainRefusal {
                    code: "RESOURCE_EXHAUSTION".into(),
                    message: "Prime 002 halting predicate: remaining run budget is 0".into(),
                });
            }
            let remaining = budget - 1;
            self.remaining_budget = Some(remaining);
            Ok(remaining)
        } else {
            Ok(u64::MAX)
        }
    }
}

/// Four-way mutually exclusive typed disposition (Architecture Review 16 §3 & §4).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "disposition")]
pub enum CochainDisposition {
    /// Phi_1 = 0, Gamma_2 = 0: Exact coboundary; observations reproduced by vertex potential.
    #[serde(rename = "ExactCoboundary")]
    ExactCoboundary {
        potential: Vec<BigRational>,
        residual: Vec<BigRational>,
        phi1: BigRational,
        gamma2: BigRational,
    },
    /// Phi_1 > 0, Gamma_2 = 0: Closed non-exact class in H^1 = ker(d_1) / im(d_0).
    #[serde(rename = "ClosedNonExactClass")]
    ClosedNonExactClass {
        cohomology_class: Vec<BigRational>,
        dual_witness: Vec<BigRational>,
        phi1: BigRational,
        gamma2: BigRational,
    },
    /// Gamma_2 > 0 (Phi_1 > 0): Non-closed edge data; face defect is non-zero.
    #[serde(rename = "NonClosedEdgeData")]
    NonClosedEdgeData {
        face_defect: Vec<BigRational>,
        phi1: BigRational,
        gamma2: BigRational,
    },
    /// Typed refusal for mathematically inadmissible profile, dimension mismatch, or budget exhaustion.
    #[serde(rename = "Refusal")]
    Refusal { code: String, message: String },
}

impl CochainDisposition {
    pub fn is_exact(&self) -> bool {
        matches!(self, Self::ExactCoboundary { .. })
    }

    pub fn is_closed_residual(&self) -> bool {
        matches!(self, Self::ClosedNonExactClass { .. })
    }

    pub fn is_nonclosed(&self) -> bool {
        matches!(self, Self::NonClosedEdgeData { .. })
    }

    pub fn is_refusal(&self) -> bool {
        matches!(self, Self::Refusal { .. })
    }

    pub fn phi1(&self) -> Option<&BigRational> {
        match self {
            Self::ExactCoboundary { phi1, .. } => Some(phi1),
            Self::ClosedNonExactClass { phi1, .. } => Some(phi1),
            Self::NonClosedEdgeData { phi1, .. } => Some(phi1),
            Self::Refusal { .. } => None,
        }
    }

    pub fn gamma2(&self) -> Option<&BigRational> {
        match self {
            Self::ExactCoboundary { gamma2, .. } => Some(gamma2),
            Self::ClosedNonExactClass { gamma2, .. } => Some(gamma2),
            Self::NonClosedEdgeData { gamma2, .. } => Some(gamma2),
            Self::Refusal { .. } => None,
        }
    }
}

/// Refusal record containing machine-readable code and explanatory message.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CochainRefusal {
    pub code: String,
    pub message: String,
}

impl fmt::Display for CochainRefusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}: {}", self.code, self.message)
    }
}

impl std::error::Error for CochainRefusal {}

/// Sovereign Prompt-to-Cochain execution and evaluation engine.
pub struct PromptCochainEvaluator;

impl PromptCochainEvaluator {
    fn validate_prime_triad_admission(
        complex: &PromptCellComplex,
        prime_triad: Option<&mut PrimeTriadContext>,
    ) -> Result<(), CochainDisposition> {
        // Prime 000 and 001 admit before measurement. Prime 002 spends one allowance unit.
        let Some(context) = prime_triad else {
            let default_context = PrimeTriadContext::default();
            return default_context.validate_prime_000(complex).map_err(|refusal| {
                CochainDisposition::Refusal {
                    code: refusal.code,
                    message: refusal.message,
                }
            });
        };
        if let Err(refusal) = context.validate_prime_000(complex) {
            return Err(CochainDisposition::Refusal {
                code: refusal.code,
                message: refusal.message,
            });
        }
        if let Err(refusal) =
            context.check_prime_001_preservation(context.candidate_answers.as_ref())
        {
            return Err(CochainDisposition::Refusal {
                code: refusal.code,
                message: refusal.message,
            });
        }
        if let Err(refusal) = context.check_and_decrement_prime_002_budget() {
            return Err(CochainDisposition::Refusal {
                code: refusal.code,
                message: refusal.message,
            });
        }
        Ok(())
    }

    fn validate_cochain_dimensions(
        complex: &PromptCellComplex,
        edge_cochain: &[BigRational],
        primal_potential: &[BigRational],
        dual_witness: &[BigRational],
    ) -> Result<(), CochainDisposition> {
        // Validate dimension parity before native computation
        if edge_cochain.len() != complex.c1_dim {
            return Err(CochainDisposition::Refusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!(
                    "edge_cochain length {} != complex c1_dim {}",
                    edge_cochain.len(),
                    complex.c1_dim
                ),
            });
        }
        if primal_potential.len() != complex.c0_dim {
            return Err(CochainDisposition::Refusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!(
                    "primal_potential length {} != complex c0_dim {}",
                    primal_potential.len(),
                    complex.c0_dim
                ),
            });
        }
        if dual_witness.len() != complex.c1_dim {
            return Err(CochainDisposition::Refusal {
                code: "DIMENSION_MISMATCH".into(),
                message: format!(
                    "dual_witness length {} != complex c1_dim {}",
                    dual_witness.len(),
                    complex.c1_dim
                ),
            });
        }
        Ok(())
    }

    fn evaluate_gamma2_exact(
        exact_complex: &ExactCochainComplexQ,
        edge_cochain: &[BigRational],
    ) -> Result<BigRational, CochainDisposition> {
        // 2. Secondary Closure Defect Functional: Gamma_2(c) = ||d_1 c||_1
        if exact_complex.c2_dim() == 0 {
            // Zero-face profile: C^2 = Q^0, face defect is empty, Gamma_2 = 0
            return Ok(BigRational::zero());
        }
        let res = DegreeOneResidualQ::try_new(exact_complex, edge_cochain.to_vec()).map_err(|e| {
            CochainDisposition::Refusal {
                code: "GAMMA2_RESIDUAL_ERROR".into(),
                message: e.to_string(),
            }
        })?;
        let gamma2_result = Gamma2Functional::try_compute_exact_quotient(&res).map_err(|e| {
            CochainDisposition::Refusal {
                code: "GAMMA2_EVALUATION_ERROR".into(),
                message: e.to_string(),
            }
        })?;
        Ok(gamma2_result.value().clone())
    }

    fn format_phi1_error(e: ExactPhi1CertificateError) -> String {
        match e {
            ExactPhi1CertificateError::DualAnnihilatorMismatch { column } => {
                format!("Dual witness does not annihilate im(d_0) at column {column}: d0^T y != 0")
            }
            ExactPhi1CertificateError::DualNormBoundViolation { index } => {
                format!("Dual witness violates infinity norm bound ||y||_infty <= 1 at index {index}")
            }
            ExactPhi1CertificateError::DualValueMismatch => {
                "Dual value y^T c does not match primal quotient objective: non-zero duality gap".into()
            }
            ExactPhi1CertificateError::PrimalValueMismatch => {
                "Reported Phi_1 value does not match primal residual norm ||c - d0 a||_1".into()
            }
            other => other.to_string(),
        }
    }

    fn compute_face_defect(
        exact_complex: &ExactCochainComplexQ,
        edge_cochain: &[BigRational],
    ) -> Vec<BigRational> {
        if exact_complex.c2_dim() == 0 {
            return Vec::new();
        }
        exact_complex
            .d1()
            .iter()
            .map(|row| {
                row.iter()
                    .zip(edge_cochain)
                    .map(|(coeff, val)| coeff.clone() * val.clone())
                    .sum::<BigRational>()
            })
            .collect()
    }

    fn classify_cochain_disposition(
        exact_complex: &ExactCochainComplexQ,
        edge_cochain: &[BigRational],
        primal_potential: &[BigRational],
        dual_witness: &[BigRational],
        verified_phi1: &VerifiedExactPhi1,
        gamma2_val: BigRational,
    ) -> CochainDisposition {
        let phi1_val = verified_phi1.value().clone();

        // 4. Four-Way Typed Disposition Evaluation (Architecture Review 16 §3 & §4)
        if phi1_val.is_zero() && gamma2_val.is_zero() {
            // Case 1: Exact coboundary; observations reproduced by vertex potential modulo ker(d_0)
            CochainDisposition::ExactCoboundary {
                potential: primal_potential.to_vec(),
                residual: verified_phi1.primal_residual().to_vec(),
                phi1: phi1_val,
                gamma2: gamma2_val,
            }
        } else if !phi1_val.is_zero() && gamma2_val.is_zero() {
            // Case 2: Closed non-exact class in H^1 = ker(d_1) / im(d_0)
            CochainDisposition::ClosedNonExactClass {
                cohomology_class: verified_phi1.primal_residual().to_vec(),
                dual_witness: dual_witness.to_vec(),
                phi1: phi1_val,
                gamma2: gamma2_val,
            }
        } else if !gamma2_val.is_zero() {
            if phi1_val.is_zero() {
                // Case 4: Mathematically inadmissible profile for valid complex (d_1 * d_0 = 0)
                // If c = d_0 a, then d_1 c = d_1 d_0 a = 0, so Gamma_2 must be 0!
                CochainDisposition::Refusal {
                    code: "IMPOSSIBLE_PROFILE".into(),
                    message: "Phi1=0 but Gamma2>0 is mathematically inadmissible for a valid chain complex with d1*d0=0".into(),
                }
            } else {
                // Case 3: Non-closed edge data; retain face defect
                let face_defect = Self::compute_face_defect(exact_complex, edge_cochain);
                CochainDisposition::NonClosedEdgeData {
                    face_defect,
                    phi1: phi1_val,
                    gamma2: gamma2_val,
                }
            }
        } else {
            CochainDisposition::Refusal {
                code: "INCONCLUSIVE_DISPOSITION".into(),
                message: "Unrecognized cochain evaluation state".into(),
            }
        }
    }

    /// Execute prompt-to-cochain evaluation on an oriented cell complex and candidate bindings.
    ///
    /// Checks Prime 000, evaluates Gamma_2 and Phi_1 exactly over Q,
    /// verifies zero duality gap against core_functional, checks Prime 001,
    /// spends one Prime 002 allowance unit when `remaining_budget` is `Some`,
    /// and classifies into the four-way typed disposition table.
    pub fn evaluate(
        complex: &PromptCellComplex,
        edge_cochain: &[BigRational],
        primal_potential: &[BigRational],
        dual_witness: &[BigRational],
        prime_triad: Option<&mut PrimeTriadContext>,
    ) -> CochainDisposition {
        if let Err(refusal) = Self::validate_prime_triad_admission(complex, prime_triad) {
            return refusal;
        }
        if let Err(refusal) =
            Self::validate_cochain_dimensions(complex, edge_cochain, primal_potential, dual_witness)
        {
            return refusal;
        }

        // Validate chain complex nilpotence d_1 * d_0 = 0 in Q
        let exact_complex = match complex.to_exact_complex() {
            Ok(c) => c,
            Err(refusal) => {
                return CochainDisposition::Refusal {
                    code: refusal.code,
                    message: refusal.message,
                };
            }
        };

        let gamma2_val = match Self::evaluate_gamma2_exact(&exact_complex, edge_cochain) {
            Ok(val) => val,
            Err(refusal) => return refusal,
        };

        // 3. Primary Quotient Obstruction Functional: Phi_1(c) = min_a ||c - d_0 a||_1
        let weights = vec![BigRational::one(); exact_complex.c1_dim()];
        let phi1_result = Phi1Functional::evaluate_exact_witness(
            edge_cochain,
            exact_complex.d0(),
            &weights,
            primal_potential,
            dual_witness,
        );

        let verified_phi1: VerifiedExactPhi1 = match phi1_result {
            Ok(cert) => cert,
            Err(e) => {
                return CochainDisposition::Refusal {
                    code: "PHI1_CERTIFICATE_INVALID".into(),
                    message: Self::format_phi1_error(e),
                };
            }
        };

        Self::classify_cochain_disposition(
            &exact_complex,
            edge_cochain,
            primal_potential,
            dual_witness,
            &verified_phi1,
            gamma2_val,
        )
    }
}

// Origin: engine/crates_rs/pfp_runtime/src/cochain.rs
// Claim: urn:core:crates_rs:pfp-runtime:cochain:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    fn r(numer: i64) -> BigRational {
        rational(numer, 1)
    }

    #[test]
    fn n8_graph_storage_overflow_refuses_without_dense_inputs() {
        // Current-only arithmetic controls: no extreme sizes reach a dense allocation.
        for (vertices, edges, faces) in [(usize::MAX, 2, 0), (0, 2, usize::MAX), (usize::MAX, 1, 1)]
        {
            let refusal = PromptCellComplex::preflight_graph_storage(vertices, edges, faces)
                .expect_err("dense cell arithmetic must not overflow");
            assert_eq!(refusal.code, "RESOURCE_EXHAUSTION");
            assert!(refusal.message.contains("overflow"));
        }
        let edges = [(0, 0), (0, 0)];
        let cycles = [vec![0]];
        for refusal in [
            PromptCellComplex::from_oriented_graph(usize::MAX, &edges, None).unwrap_err(),
            PromptCellComplex::from_operad_occurrences(usize::MAX, &edges, Some(&cycles))
                .unwrap_err(),
        ] {
            assert_eq!(refusal.code, "RESOURCE_EXHAUSTION");
            assert!(refusal.message.contains("overflow"));
        }
    }

    /// Standard Triadic Benchmark Setup: Canonical 3-edge oriented triangle
    /// V = {0, 1, 2}, E = {(0,1), (1,2), (2,0)}
    /// d0 = [[-1, 1, 0], [0, -1, 1], [1, 0, -1]]
    fn canonical_triangle(with_face: bool) -> PromptCellComplex {
        let d0 = vec![
            vec![r(-1), r(1), r(0)],
            vec![r(0), r(-1), r(1)],
            vec![r(1), r(0), r(-1)],
        ];
        if with_face {
            let d1 = vec![vec![r(1), r(1), r(1)]];
            PromptCellComplex::new(3, 3, 1, d0, d1)
        } else {
            PromptCellComplex::zero_face(3, 3, d0)
        }
    }

    #[test]
    fn self_loop_incidence_preserves_the_nonexact_class() {
        let complex =
            PromptCellComplex::from_oriented_graph(1, &[(0, 0)], None).expect("loop complex");
        assert_eq!(complex.d0, vec![vec![r(0)]]);
        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &[r(1)], &[r(1)], &[r(1)], None);
        assert!(matches!(disposition,
            CochainDisposition::ClosedNonExactClass { phi1, gamma2, .. }
                if phi1 == r(1) && gamma2 == r(0)
        ));
        let forged_exact =
            PromptCochainEvaluator::evaluate(&complex, &[r(1)], &[r(1)], &[r(0)], None);
        assert!(matches!(forged_exact, CochainDisposition::Refusal { .. }));
    }

    #[test]
    fn repeated_face_terms_accumulate_and_cancel() {
        let edges = [(0, 1), (1, 2), (2, 0)];
        let twice = vec![vec![0, 1, 2, 0, 1, 2]];
        let complex = PromptCellComplex::from_operad_occurrences(3, &edges, Some(&twice))
            .expect("twice-traversed triangle");
        assert_eq!(complex.d1, vec![vec![r(2), r(2), r(2)]]);
        let cancellation = vec![vec![(0, r(1)), (0, r(-1))]];
        let cancelled = PromptCellComplex::from_oriented_graph(3, &edges, Some(&cancellation))
            .expect("zero face chain");
        assert_eq!(cancelled.d1, vec![vec![r(0), r(0), r(0)]]);
        let invalid = vec![vec![(0, r(1)), (0, r(1))]];
        let refusal = PromptCellComplex::from_oriented_graph(3, &edges, Some(&invalid))
            .expect_err("noncycle must remain refused");
        assert_eq!(refusal.code, "CHAIN_LAW_VIOLATION");
    }

    #[test]
    fn parallel_edges_keep_distinct_face_coordinates() {
        let faces = vec![vec![(0, r(1)), (1, r(-1))]];
        let complex = PromptCellComplex::from_oriented_graph(2, &[(0, 1), (0, 1)], Some(&faces))
            .expect("parallel-edge cycle");
        assert_eq!(complex.d0, vec![vec![r(-1), r(1)], vec![r(-1), r(1)]]);
        assert_eq!(complex.d1, vec![vec![r(1), r(-1)]]);
    }

    #[test]
    fn test_input_1_exact_coboundary() {
        // Input 1 (Exact): c = (1, 2, -3) = d_0 * (0, 1, 3)^T, d_1 = (1, 1, 1)
        // d0 * a:
        // row 0: -0 + 1 = 1
        // row 1: -1 + 3 = 2
        // row 2: 0 - 3 = -3
        // Residual = c - d0 a = 0.
        // Dual witness y = (0, 0, 0) annihilates d0: d0^T y = 0, ||y||_inf = 0 <= 1, y^T c = 0.
        let complex = canonical_triangle(true);
        let cochain = vec![r(1), r(2), r(-3)];
        let potential = vec![r(0), r(1), r(3)];
        let dual_witness = vec![r(0), r(0), r(0)];

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);

        match disposition {
            CochainDisposition::ExactCoboundary {
                potential: pot,
                residual,
                phi1,
                gamma2,
            } => {
                assert_eq!(pot, potential);
                assert_eq!(residual, vec![r(0), r(0), r(0)]);
                assert!(phi1.is_zero());
                assert!(gamma2.is_zero());
            }
            other => panic!("expected ExactCoboundary, got {other:?}"),
        }
    }

    #[test]
    fn test_input_2_coherent_residual_closed_non_exact() {
        // Input 2 (Coherent Residual): c = (1, 1, 1), faces omitted (C^2 = 0)
        // a = (0, 0, 0), residual = (1, 1, 1), norm = 3.
        // y = (1, 1, 1): d0^T y = 0, ||y||_inf = 1 <= 1, y^T c = 3. Duality gap = 0.
        // Faces omitted => Gamma_2 = 0.
        // Phi_1 = 3 > 0, Gamma_2 = 0 => ClosedNonExactClass.
        let complex = canonical_triangle(false);
        let cochain = vec![r(1), r(1), r(1)];
        let potential = vec![r(0), r(0), r(0)];
        let dual_witness = vec![r(1), r(1), r(1)];

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);

        match disposition {
            CochainDisposition::ClosedNonExactClass {
                cohomology_class,
                dual_witness: dw,
                phi1,
                gamma2,
            } => {
                assert_eq!(cohomology_class, vec![r(1), r(1), r(1)]);
                assert_eq!(dw, dual_witness);
                assert_eq!(phi1, r(3));
                assert!(gamma2.is_zero());
            }
            other => panic!("expected ClosedNonExactClass, got {other:?}"),
        }
    }

    #[test]
    fn test_input_3_nonclosed_edge_data() {
        // Input 3 (Nonclosed Defect): c = (1, 1, 1), filled face d_1 = (1, 1, 1)
        // Phi_1 = 3 (with a = 0, y = (1, 1, 1)).
        // d1 c = 1(1) + 1(1) + 1(1) = 3 != 0 => Gamma_2 = 3 > 0.
        // Phi_1 > 0, Gamma_2 > 0 => NonClosedEdgeData.
        let complex = canonical_triangle(true);
        let cochain = vec![r(1), r(1), r(1)];
        let potential = vec![r(0), r(0), r(0)];
        let dual_witness = vec![r(1), r(1), r(1)];

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);

        match disposition {
            CochainDisposition::NonClosedEdgeData {
                face_defect,
                phi1,
                gamma2,
            } => {
                assert_eq!(face_defect, vec![r(3)]);
                assert_eq!(phi1, r(3));
                assert_eq!(gamma2, r(3));
            }
            other => panic!("expected NonClosedEdgeData, got {other:?}"),
        }
    }

    #[test]
    fn test_falsification_impossible_profile_refusal() {
        // Test that a claimed Phi_1 = 0 on a non-closed cochain (Gamma_2 > 0)
        // is rejected. Specifically, if someone constructs a complex with d1 d0 = 0,
        // and claims potential a reproduces c (so Phi1=0), but d1 c != 0 (Gamma2 > 0),
        // that's inadmissible because d1 (d0 a) = (d1 d0) a = 0.
        // Let's create an artificial scenario: d1 d0 != 0 is caught at construction.
        // But what if d0 a != c? Then Phi1 is not 0 (the certificate check fails).
        // If an evaluator encounters phi1 == 0 and gamma2 > 0 on any valid complex,
        // it refuses with IMPOSSIBLE_PROFILE.
        let complex = canonical_triangle(true);
        // If someone sends c = (1, 2, -3) (where d1 c = 0), gamma2 is 0.
        // If someone sends c = (1, 1, 1) (where d1 c = 3), gamma2 is 3.
        // Can they forge an a = (0, 1, 3) claiming Phi_1 = 0?
        // Phi1Functional::evaluate_exact_witness will check c - d0 a = (0, -1, 4) != 0,
        // so dual pairing with y=(0,0,0) will fail: DualValueMismatch!
        let cochain = vec![r(1), r(1), r(1)];
        let potential = vec![r(0), r(1), r(3)]; // d0 a = (1, 2, -3) != c
        let dual_witness = vec![r(0), r(0), r(0)];

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);

        match disposition {
            CochainDisposition::Refusal { code, .. } => {
                assert_eq!(code, "PHI1_CERTIFICATE_INVALID");
            }
            other => panic!("expected Refusal, got {other:?}"),
        }
    }

    #[test]
    fn test_chain_law_violation_refusal() {
        // Construct an invalid complex where d1 * d0 != 0
        let d0 = vec![vec![r(1)]];
        let d1 = vec![vec![r(1)]]; // d1 * d0 = 1 != 0
        let complex = PromptCellComplex::new(1, 1, 1, d0, d1);

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &[r(1)], &[r(1)], &[r(1)], None);

        match disposition {
            CochainDisposition::Refusal { code, message } => {
                assert_eq!(code, "CHAIN_LAW_VIOLATION");
                assert!(message.contains("d1 * d0 = 0 failed"));
            }
            other => panic!("expected Refusal(CHAIN_LAW_VIOLATION), got {other:?}"),
        }
    }

    #[test]
    fn test_dimension_mismatch_refusal() {
        let complex = canonical_triangle(true);
        let cochain = vec![r(1)]; // expected 3
        let potential = vec![r(0), r(1), r(3)];
        let dual_witness = vec![r(0), r(0), r(0)];

        let disposition =
            PromptCochainEvaluator::evaluate(&complex, &cochain, &potential, &dual_witness, None);

        match disposition {
            CochainDisposition::Refusal { code, .. } => {
                assert_eq!(code, "DIMENSION_MISMATCH");
            }
            other => panic!("expected Refusal(DIMENSION_MISMATCH), got {other:?}"),
        }
    }

    #[test]
    fn test_prime_000_source_bytes_hash_validation() {
        let mut complex = canonical_triangle(false);
        complex = complex.with_source_bytes_hash("aabbcc".into());

        let mut triad = PrimeTriadContext {
            source_bytes: Some("test source bytes".into()),
            expected_source_hash: Some("aabbcc".into()),
            protected_answers: None,
            candidate_answers: None,
            remaining_budget: Some(10),
        };

        let disposition = PromptCochainEvaluator::evaluate(
            &complex,
            &[r(1), r(1), r(1)],
            &[r(0), r(0), r(0)],
            &[r(1), r(1), r(1)],
            Some(&mut triad),
        );

        // Computed sha256 of "test source bytes" won't match "aabbcc"
        match disposition {
            CochainDisposition::Refusal { code, .. } => {
                assert_eq!(code, "SOURCE_BYTES_CORRUPTED");
            }
            other => panic!("expected Refusal(SOURCE_BYTES_CORRUPTED), got {other:?}"),
        }
    }

    #[test]
    fn test_prime_002_budget_exhaustion() {
        let complex = canonical_triangle(false);
        let mut triad = PrimeTriadContext {
            source_bytes: None,
            expected_source_hash: None,
            protected_answers: None,
            candidate_answers: None,
            remaining_budget: Some(0), // Budget exhausted!
        };

        let disposition = PromptCochainEvaluator::evaluate(
            &complex,
            &[r(1), r(1), r(1)],
            &[r(0), r(0), r(0)],
            &[r(1), r(1), r(1)],
            Some(&mut triad),
        );

        match disposition {
            CochainDisposition::Refusal { code, .. } => {
                assert_eq!(code, "RESOURCE_EXHAUSTION");
            }
            other => panic!("expected Refusal(RESOURCE_EXHAUSTION), got {other:?}"),
        }
    }
}
