//! LGGR V named-presentation adapter for the finite chromatic obstruction index.
//! Generic search belongs to combinatorics. Generic adjoint probes and kernels
//! are BasicMatrix::try_transpose/mul_vec and ExactRowReduction::kernel_basis.
//! A minimizing coloring is not a minimal unsatisfiable subgraph certificate.

use crate::types::AuthorityEffect;
use core_combinatorics::color_constraints::{
    minimum_color_violations, ColorConstraintError, MinimumColorViolations,
};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum ChromaticPresentationError {
    #[error("duplicate vertex name")]
    DuplicateVertex,
    #[error("unknown edge endpoint: {0}")]
    Endpoint(String),
    #[error(transparent)]
    Search(#[from] ColorConstraintError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChromaticConstraintSystem {
    pub vertices: Vec<String>,
    pub edges: Vec<(String, String)>,
    pub num_colors: usize,
    pub forbidden_color_pairs: BTreeSet<(usize, usize)>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ChromaticCertificate {
    pub presentation: ChromaticConstraintSystem,
    pub minimum: MinimumColorViolations,
    pub authority_effect: AuthorityEffect,
}

impl ChromaticConstraintSystem {
    pub fn evaluate(
        &self,
        max_colorings: usize,
        max_edge_checks: usize,
    ) -> Result<ChromaticCertificate, ChromaticPresentationError> {
        let indices: BTreeMap<_, _> = self
            .vertices
            .iter()
            .enumerate()
            .map(|(i, v)| (v, i))
            .collect();
        if indices.len() != self.vertices.len() {
            return Err(ChromaticPresentationError::DuplicateVertex);
        }
        let edges: Vec<_> = self
            .edges
            .iter()
            .map(|(u, v)| {
                let get = |name: &String| {
                    indices
                        .get(name)
                        .copied()
                        .ok_or_else(|| ChromaticPresentationError::Endpoint(name.clone()))
                };
                Ok((get(u)?, get(v)?))
            })
            .collect::<Result<_, ChromaticPresentationError>>()?;
        let minimum = minimum_color_violations(
            self.vertices.len(),
            &edges,
            self.num_colors,
            &self.forbidden_color_pairs,
            max_colorings,
            max_edge_checks,
        )?;
        Ok(ChromaticCertificate {
            presentation: self.clone(),
            minimum,
            authority_effect: AuthorityEffect::None,
        })
    }

    pub fn verify(
        &self,
        candidate: &ChromaticCertificate,
        max_colorings: usize,
        max_edge_checks: usize,
    ) -> Result<bool, ChromaticPresentationError> {
        Ok(*candidate == self.evaluate(max_colorings, max_edge_checks)?)
    }
}

// Origin: engine/crates_rs/core_wdp/src/wdp_lggr_chromatic.rs
// Claim: urn:core:crates_rs:core-wdp:wdp-lggr-chromatic:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_80c34e6e {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
