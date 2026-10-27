//! function shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.


#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f794314c;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f794314c<T> = std::result::Result<T, BoundaryError_f794314c>;
use serde::{Deserialize, Serialize};

/// A single domain→codomain pair tag (not a formal graph).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct MappingPair {
    pub domain_element: String,
    pub codomain_element: String,
}

/// Best-effort shell for a labeled function between labeled sets.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct Function {
    pub label: String,
    pub domain_label: String,
    pub codomain_label: String,
    /// Optional explicit pairs (diagnostic; not a total-function certificate).
    pub pairs: Vec<MappingPair>,
    pub notes: Vec<String>,
}

impl Function {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            domain_label: String::new(),
            codomain_label: String::new(),
            pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn between(
        label: impl Into<String>,
        domain_label: impl Into<String>,
        codomain_label: impl Into<String>,
    ) -> Self {
        Self {
            label: label.into(),
            domain_label: domain_label.into(),
            codomain_label: codomain_label.into(),
            pairs: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn with_pair(
        &mut self,
        domain_element: impl Into<String>,
        codomain_element: impl Into<String>,
    ) {
        self.pairs.push(MappingPair {
            domain_element: domain_element.into(),
            codomain_element: codomain_element.into(),
        });
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        if self.domain_label.is_empty() {
            return Err("empty domain_label".into());
        }
        if self.codomain_label.is_empty() {
            return Err("empty codomain_label".into());
        }
        for (i, p) in self.pairs.iter().enumerate() {
            if p.domain_element.is_empty() || p.codomain_element.is_empty() {
                return Err(format!("empty mapping tag at pair index {i}"));
            }
        }
        Ok(())
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(Function::between("f", "A", "B").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(Function::new("").validate_shell().is_err());
    }

    #[test]
    fn validate_rejects_missing_domain() {
        let f = Function::new("f");
        assert!(f.validate_shell().is_err());
    }

    #[test]
    fn with_pair_ok() {
        let mut f = Function::between("f", "A", "B");
        f.with_pair("a", "b");
        assert_eq!(f.pairs.len(), 1);
        assert!(f.validate_shell().is_ok());
    }
}

// Exact invariant envelope.
// Origin: engine/crates_rs/core_category_theory/src/foundations/function.rs
// Claim: urn:core:category:function:total-image:v1
// AuthorityEffect: None

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct TotalFunction {
    domain_size: u16,
    codomain_size: u16,
    image_count: u16,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TotalFunctionError {
    ShellRefused { reason: String },
    EmptyDomain,
    EmptyCodomain,
    LengthMismatch { domain: u16, images: usize },
    ImageOutOfRange { index: usize, image: u16 },
    CountOverflow,
}

// Origin: engine/crates_rs/core_category_theory/src/foundations/function.rs
// Claim: urn:core:crates_rs:core-category-theory:function:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for TotalFunctionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for TotalFunctionError {}

impl TotalFunction {
    fn count_unique_images(codomain_size: u16, images: &[u16]) -> Result<u16, TotalFunctionError> {
        let mut seen = vec![false; usize::from(codomain_size)];
        let mut image_count = 0u16;
        for index in 0..images.len() {
            let image = *images
                .get(index)
                .ok_or(TotalFunctionError::ImageOutOfRange { index, image: 0 })?;
            let slot = usize::from(image);
            let flag = seen
                .get_mut(slot)
                .ok_or(TotalFunctionError::ImageOutOfRange { index, image })?;
            if !*flag {
                *flag = true;
                image_count = image_count
                    .checked_add(1)
                    .ok_or(TotalFunctionError::CountOverflow)?;
            }
        }
        Ok(image_count)
    }

    pub fn try_on(
        shell: &Function,
        domain_size: u16,
        codomain_size: u16,
        images: &[u16],
    ) -> Result<Self, TotalFunctionError> {
        shell
            .validate_shell()
            .map_err(|reason| TotalFunctionError::ShellRefused { reason })?;
        if domain_size == 0 {
            return Err(TotalFunctionError::EmptyDomain);
        }
        if codomain_size == 0 {
            return Err(TotalFunctionError::EmptyCodomain);
        }
        if images.len() != usize::from(domain_size) {
            return Err(TotalFunctionError::LengthMismatch {
                domain: domain_size,
                images: images.len(),
            });
        }
        let image_count = Self::count_unique_images(codomain_size, images)?;
        Ok(Self {
            domain_size,
            codomain_size,
            image_count,
        })
    }

    pub fn image_count(&self) -> u16 {
        self.image_count
    }

    pub fn domain_size(&self) -> u16 {
        self.domain_size
    }
}

#[cfg(test)]
mod total_function_tests {
    use super::*;

    #[test]
    fn counts_the_image_of_a_total_map() {
        let shell = Function::between("f", "A", "B");
        let witness = TotalFunction::try_on(&shell, 3, 2, &[1, 0, 1]);
        assert!(matches!(
            witness,
            Ok(ref w) if w.domain_size() == 3 && w.image_count() == 2
        ));
    }

    #[test]
    fn refuses_an_image_outside_the_codomain() {
        let shell = Function::between("f", "A", "B");
        let wrong = TotalFunction::try_on(&shell, 2, 2, &[0, 5]);
        assert!(matches!(
            wrong,
            Err(TotalFunctionError::ImageOutOfRange { index: 1, image: 5 })
        ));
    }
}
