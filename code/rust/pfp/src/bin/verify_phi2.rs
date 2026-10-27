//! JSON line adapter for the canonical finite rational Phi2 (degree-2 obstruction) verifier.

use num_rational::BigRational;
use num_traits::Zero;
use core_functional::phi2::{ExactPhi2Certificate, Phi2Functional, VerifiedExactPhi2};
use serde_json::json;
use std::io::{self, Read};

#[derive(Debug, Clone, PartialEq, Eq)]
enum Phi2AdmitError {
    Shape { faces: usize, edges: usize },
    Defect { gap: String },
}

impl std::fmt::Display for Phi2AdmitError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Phi2AdmitError::Shape { faces, edges } => write!(
                formatter,
                "printed cell counts do not match the sealed shape ({faces} faces, {edges} edges)"
            ),
            Phi2AdmitError::Defect { gap } => {
                write!(formatter, "printed duality defect is {gap}, not the zero rational")
            }
        }
    }
}

/// Printed Phi2 certificate. Cell counts are the sealed face and edge dimensions,
/// and the duality defect is the exact difference of the primal and dual objectives.
#[derive(Debug, Clone, PartialEq, Eq)]
struct AdmittedPhi2Print {
    faces: usize,
    edges: usize,
    defect: BigRational,
}

impl AdmittedPhi2Print {
    fn validate_shapes(verified: &VerifiedExactPhi2) -> Result<(usize, usize), Phi2AdmitError> {
        let certificate = verified.certificate();
        let faces = certificate.flux_b.len();
        let edges = certificate.potential_a.len();
        let lengths_match = [
            verified.primal_residual().len(),
            certificate.primal_residual.len(),
            certificate.dual_witness.len(),
            certificate.weights.len(),
            certificate.d1.len(),
        ]
        .into_iter()
        .all(|len| len == faces)
            && verified.potential_a().len() == edges;
        if !lengths_match {
            return Err(Phi2AdmitError::Shape { faces, edges });
        }
        for row in &certificate.d1 {
            if row.len() != edges {
                return Err(Phi2AdmitError::Shape {
                    faces,
                    edges: row.len(),
                });
            }
        }
        Ok((faces, edges))
    }

    fn compute_objectives(
        verified: &VerifiedExactPhi2,
        faces: usize,
        edges: usize,
    ) -> Result<(BigRational, BigRational), Phi2AdmitError> {
        let certificate = verified.certificate();
        let mut primal = BigRational::zero();
        let mut dual = BigRational::zero();
        for index in 0..faces {
            let weight = certificate
                .weights
                .get(index)
                .ok_or(Phi2AdmitError::Shape { faces, edges })?;
            let residual = certificate
                .primal_residual
                .get(index)
                .ok_or(Phi2AdmitError::Shape { faces, edges })?;
            let flux = certificate
                .flux_b
                .get(index)
                .ok_or(Phi2AdmitError::Shape { faces, edges })?;
            let witness = certificate
                .dual_witness
                .get(index)
                .ok_or(Phi2AdmitError::Shape { faces, edges })?;
            let magnitude = if residual < &BigRational::zero() {
                -residual.clone()
            } else {
                residual.clone()
            };
            primal += weight.clone() * magnitude;
            dual += witness.clone() * flux.clone();
        }
        Ok((primal, dual))
    }

    fn try_admit(verified: &VerifiedExactPhi2) -> Result<Self, Phi2AdmitError> {
        let (faces, edges) = Self::validate_shapes(verified)?;
        let (primal, dual) = Self::compute_objectives(verified, faces, edges)?;
        let defect = primal.clone() - dual.clone();
        if !defect.is_zero() || primal != *verified.value() || dual != *verified.value() {
            return Err(Phi2AdmitError::Defect {
                gap: defect.to_string(),
            });
        }
        Ok(Self {
            faces,
            edges,
            defect,
        })
    }

    fn faces(&self) -> usize {
        self.faces
    }

    fn edges(&self) -> usize {
        self.edges
    }

    fn zero_defect_token(&self) -> Result<&'static str, Phi2AdmitError> {
        if self.defect.is_zero() {
            Ok("0")
        } else {
            Err(Phi2AdmitError::Defect {
                gap: self.defect.to_string(),
            })
        }
    }
}

fn render_pass(verified: &VerifiedExactPhi2) -> Result<serde_json::Value, String> {
    let printed = AdmittedPhi2Print::try_admit(verified).map_err(|error| error.to_string())?;
    let defect = printed.zero_defect_token().map_err(|error| error.to_string())?;
    Ok(json!({
        "status": "PASS",
        "reported_value": verified.value().to_string(),
        "duality_gap": defect,
        "face_count": printed.faces(),
        "edge_count": printed.edges()
    }))
}

fn main() {
    let mut input = String::new();
    let result = io::stdin()
        .read_to_string(&mut input)
        .map_err(|error| error.to_string())
        .and_then(|_| {
            serde_json::from_str::<ExactPhi2Certificate>(&input).map_err(|error| error.to_string())
        })
        .and_then(|certificate| {
            Phi2Functional::verify_exact_certificate(certificate).map_err(|error| error.to_string())
        });

    match result {
        Ok(verified) => match render_pass(&verified) {
            Ok(pass) => println!("{pass}"),
            Err(error) => {
                println!("{}", json!({"status": "REFUSE", "reason": error}));
                std::process::exit(2);
            }
        },
        Err(error) => {
            println!("{}", json!({"status": "REFUSE", "reason": error}));
            std::process::exit(2);
        }
    }
}

// Origin: engine/crates_rs/pfp/src/bin/verify_phi2.rs
// Claim: urn:core:crates_rs:pfp:verify-phi2:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod phi2_adapter_tests {
    use super::*;

    const SEALED_ZERO: &str = r#"{
        "flux_b": ["0"],
        "d1": [["0"]],
        "weights": ["1"],
        "potential_a": ["0"],
        "primal_residual": ["0"],
        "dual_witness": ["0"],
        "reported_value": "0"
    }"#;

    const OPEN_GAP: &str = r#"{
        "flux_b": ["0"],
        "d1": [["0"]],
        "weights": ["1"],
        "potential_a": ["0"],
        "primal_residual": ["0"],
        "dual_witness": ["0"],
        "reported_value": "1"
    }"#;

    #[test]
    fn an_admitted_certificate_prints_matching_counts_and_a_zero_defect() -> Result<(), String> {
        let certificate: ExactPhi2Certificate =
            serde_json::from_str(SEALED_ZERO).map_err(|error| error.to_string())?;
        let verified = Phi2Functional::verify_exact_certificate(certificate)
            .map_err(|error| error.to_string())?;
        let pass = render_pass(&verified)?;
        if pass.get("status").and_then(serde_json::Value::as_str) != Some("PASS")
            || pass.get("duality_gap").and_then(serde_json::Value::as_str) != Some("0")
            || pass.get("face_count").and_then(serde_json::Value::as_u64) != Some(1)
            || pass.get("edge_count").and_then(serde_json::Value::as_u64) != Some(1)
        {
            return Err(pass.to_string());
        }
        Ok(())
    }

    #[test]
    fn a_refused_certificate_is_not_a_pass() -> Result<(), String> {
        let certificate: ExactPhi2Certificate =
            serde_json::from_str(OPEN_GAP).map_err(|error| error.to_string())?;
        match Phi2Functional::verify_exact_certificate(certificate) {
            Ok(verified) => {
                if render_pass(&verified).is_ok() {
                    return Err("open duality gap was printed as PASS".to_string());
                }
                Ok(())
            }
            Err(_) => Ok(()),
        }
    }
}
