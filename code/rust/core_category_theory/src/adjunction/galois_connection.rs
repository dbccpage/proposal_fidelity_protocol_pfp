//! galois connection shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Order-theoretic adjunction: monotone maps f ⊣ g between posets
//! with f(x) ≤ y ⇔ x ≤ g(y). Diagnostic pair tags only.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_ccee1cd3;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_ccee1cd3<T> = std::result::Result<T, BoundaryError_ccee1cd3>;
use serde::{Deserialize, Serialize};

/// A single ordered pair tag (x, y) used as a monotone-map edge.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MonotonePair {
    pub domain_element: String,
    pub codomain_element: String,
}

impl MonotonePair {
    pub fn new(domain_element: impl Into<String>, codomain_element: impl Into<String>) -> Self {
        Self {
            domain_element: domain_element.into(),
            codomain_element: codomain_element.into(),
        }
    }
}

/// Best-effort shell for a Galois connection between posets.
///
/// `lower` / `upper` are monotone maps stored as Vec of pairs (diagnostic
/// graph edges, not a totality or monotonicity certificate).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct GaloisConnectionShell {
    pub label: String,
    /// Source poset label.
    pub poset_left: String,
    /// Target poset label.
    pub poset_right: String,
    /// Lower adjoint f : left → right (monotone map as pairs).
    pub lower: Vec<MonotonePair>,
    /// Upper adjoint g : right → left (monotone map as pairs).
    pub upper: Vec<MonotonePair>,
    pub notes: Vec<String>,
}

impl GaloisConnectionShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            poset_left: String::new(),
            poset_right: String::new(),
            lower: Vec::new(),
            upper: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        poset_left: impl Into<String>,
        poset_right: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            poset_left: poset_left.into(),
            poset_right: poset_right.into(),
            lower: Vec::new(),
            upper: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_lower_pair(
        mut self,
        domain_element: impl Into<String>,
        codomain_element: impl Into<String>,
    ) -> Self {
        self.lower
            .push(MonotonePair::new(domain_element, codomain_element));
        self
    }

    pub fn with_upper_pair(
        mut self,
        domain_element: impl Into<String>,
        codomain_element: impl Into<String>,
    ) -> Self {
        self.upper
            .push(MonotonePair::new(domain_element, codomain_element));
        self
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.poset_left.is_empty() {
            return Err("empty poset_left".into());
        }
        if self.poset_right.is_empty() {
            return Err("empty poset_right".into());
        }
        for (i, p) in self.lower.iter().enumerate() {
            if p.domain_element.is_empty() || p.codomain_element.is_empty() {
                return Err(format!("empty lower pair tag at index {i}"));
            }
        }
        for (i, p) in self.upper.iter().enumerate() {
            if p.domain_element.is_empty() || p.codomain_element.is_empty() {
                return Err(format!("empty upper pair tag at index {i}"));
            }
        }
        Ok(())
    }
}

// Origin: engine/crates_rs/core_category_theory/src/adjunction/galois_connection.rs
// Claim: urn:core:crates_rs:core-category-theory:galois-connection:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        let g = GaloisConnectionShell::between("gal", "P", "Q");
        assert!(g.validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(GaloisConnectionShell::new("").validate_shell().is_err());
    }

    #[test]
    fn with_maps_ok() {
        let g = GaloisConnectionShell::between("gal", "P", "Q")
            .with_lower_pair("x", "f(x)")
            .with_upper_pair("y", "g(y)");
        assert_eq!(g.lower.len(), 1);
        assert_eq!(g.upper.len(), 1);
        assert!(g.validate_shell().is_ok());
    }

    #[test]
    fn rejects_empty_pair() {
        let g = GaloisConnectionShell::between("gal", "P", "Q").with_lower_pair("", "y");
        assert!(g.validate_shell().is_err());
    }
}

/// Monotone Galois connection on a finite chain: f(x) <= y exactly when x <= g(y).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct FiniteGalois {
    size: usize,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum GaloisError {
    Bound,
    Shape,
    Monotone,
    Adjoint,
}

impl std::fmt::Display for GaloisError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            GaloisError::Bound => write!(formatter, "chain size must lie in 1..=8"),
            GaloisError::Shape => write!(formatter, "a map leaves the chain"),
            GaloisError::Monotone => write!(formatter, "a map is not monotone"),
            GaloisError::Adjoint => write!(formatter, "the adjunction equivalence failed"),
        }
    }
}

impl std::error::Error for GaloisError {}

fn validate_galois_map(size: usize, map: &[usize]) -> Result<(), GaloisError> {
    if map.len() != size || map.iter().any(|&v| v >= size) {
        return Err(GaloisError::Shape);
    }
    if map.windows(2).any(|w| w[0] > w[1]) {
        return Err(GaloisError::Monotone);
    }
    Ok(())
}

fn check_galois_adjunction(
    size: usize,
    lower: &[usize],
    upper: &[usize],
) -> Result<(), GaloisError> {
    for (domain, &image) in lower.iter().enumerate().take(size) {
        for (codomain, &preimage) in upper.iter().enumerate().take(size) {
            if (image <= codomain) != (domain <= preimage) {
                return Err(GaloisError::Adjoint);
            }
        }
    }
    Ok(())
}

impl FiniteGalois {
    pub fn certify(size: usize, lower: &[usize], upper: &[usize]) -> Result<Self, GaloisError> {
        if size == 0 || size > 8 {
            return Err(GaloisError::Bound);
        }
        validate_galois_map(size, lower)?;
        validate_galois_map(size, upper)?;
        check_galois_adjunction(size, lower, upper)?;
        Ok(Self { size })
    }

    pub fn size(&self) -> usize {
        self.size
    }
}

#[cfg(test)]
mod galois_tests {
    use super::*;

    fn taken<T, E>(value: Result<T, E>) -> T {
        match value {
            Ok(inner) => inner,
            Err(_) => loop {
                assert!(false);
            },
        }
    }

    #[test]
    fn the_identity_connection_holds_and_a_zero_upper_map_fails() {
        let connection = taken(FiniteGalois::certify(3, &[0, 1, 2], &[0, 1, 2]));
        assert_eq!(connection.size(), 3);
        assert!(FiniteGalois::certify(3, &[0, 1, 2], &[0, 0, 0]).is_err());
    }
}
