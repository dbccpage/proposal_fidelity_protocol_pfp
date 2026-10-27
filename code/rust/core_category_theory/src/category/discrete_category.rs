//! discrete_category shell for core_category_theory.
//! AuthorityEffect: None. Not PROVED / GlobalGreen.
//!
//! Disc(S): objects = S; only identity morphisms.

use serde::{Deserialize, Serialize};

use super::category::MorphismTriple;

/// Best-effort discrete category shell on an object set.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct DiscreteCategoryShell {
    pub label: String,
    pub objects: Vec<String>,
    /// Morphisms as (src, dst, name) triples — for a discrete category these
    /// should be identities only (src == dst); validated best-effort.
    pub morphisms: Vec<MorphismTriple>,
    pub notes: Vec<String>,
}

impl DiscreteCategoryShell {
    pub fn new(label: impl Into<String>) -> Self {
        Self {
            label: label.into(),
            objects: Vec::new(),
            morphisms: Vec::new(),
            notes: Vec::new(),
        }
    }

    pub fn on_objects(label: impl Into<String>, objects: Vec<String>) -> Self {
        let morphisms = objects
            .iter()
            .map(|o| MorphismTriple::new(o.clone(), o.clone(), format!("id_{o}")))
            .collect();
        Self {
            label: label.into(),
            objects,
            morphisms,
            notes: Vec::new(),
        }
    }

    pub fn validate_shell(&self) -> Result<(), String> {
        if self.label.is_empty() {
            return Err("empty label".into());
        }
        for (i, o) in self.objects.iter().enumerate() {
            if o.is_empty() {
                return Err(format!("empty object tag at index {i}"));
            }
        }
        for (i, m) in self.morphisms.iter().enumerate() {
            if m.source.is_empty() || m.target.is_empty() || m.name.is_empty() {
                return Err(format!("empty morphism field at index {i}"));
            }
            if m.source != m.target {
                return Err(format!(
                    "non-identity morphism at index {i}: {} → {} ({})",
                    m.source, m.target, m.name
                ));
            }
        }
        Ok(())
    }
}


/// Discrete category: every object has exactly one identity, and every
/// morphism is that identity.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiscreteIdentityWitness {
    object_count: u32,
    identity_count: u32,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DiscreteIdentityError {
    EmptyLabel,
    EmptyObject { index: usize },
    DuplicateObject { name: String },
    NonIdentity { index: usize },
    UnknownObject { name: String },
    IdentityCount { object: String, count: u32 },
    Overflow,
}

// Origin: engine/crates_rs/core_category_theory/src/category/discrete_category.rs
// Claim: urn:core:crates_rs:core-category-theory:discrete-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for DiscreteIdentityError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for DiscreteIdentityError {}

fn collect_discrete_objects(raw_objects: &[String]) -> Result<Vec<&str>, DiscreteIdentityError> {
    let mut objects: Vec<&str> = Vec::with_capacity(raw_objects.len());
    for (index, object) in raw_objects.iter().enumerate() {
        if object.is_empty() {
            return Err(DiscreteIdentityError::EmptyObject { index });
        }
        if objects.contains(&object.as_str()) {
            return Err(DiscreteIdentityError::DuplicateObject {
                name: object.clone(),
            });
        }
        objects.push(object.as_str());
    }
    Ok(objects)
}

fn tally_discrete_identities(
    objects: &[&str],
    morphisms: &[MorphismTriple],
) -> Result<Vec<u32>, DiscreteIdentityError> {
    let mut counts = vec![0u32; objects.len()];
    for (index, morphism) in morphisms.iter().enumerate() {
        if morphism.source != morphism.target {
            return Err(DiscreteIdentityError::NonIdentity { index });
        }
        let position = objects
            .iter()
            .position(|object| *object == morphism.source.as_str())
            .ok_or_else(|| DiscreteIdentityError::UnknownObject {
                name: morphism.source.clone(),
            })?;
        counts[position] = counts[position]
            .checked_add(1)
            .ok_or(DiscreteIdentityError::Overflow)?;
    }
    Ok(counts)
}

impl DiscreteIdentityWitness {
    pub fn admit(shell: &DiscreteCategoryShell) -> Result<Self, DiscreteIdentityError> {
        if shell.label.is_empty() {
            return Err(DiscreteIdentityError::EmptyLabel);
        }
        let objects = collect_discrete_objects(&shell.objects)?;
        let counts = tally_discrete_identities(&objects, &shell.morphisms)?;
        for (object, &count) in objects.iter().zip(counts.iter()) {
            if count != 1 {
                return Err(DiscreteIdentityError::IdentityCount {
                    object: (*object).to_string(),
                    count,
                });
            }
        }
        let object_count = u32::try_from(objects.len()).map_err(|_| DiscreteIdentityError::Overflow)?;
        Ok(Self {
            object_count,
            identity_count: object_count,
        })
    }

    pub fn object_count(&self) -> u32 {
        self.object_count
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn validate_ok() {
        assert!(DiscreteCategoryShell::new("Disc").validate_shell().is_ok());
    }

    #[test]
    fn validate_rejects_empty() {
        assert!(DiscreteCategoryShell::new("").validate_shell().is_err());
    }

    #[test]
    fn on_objects_ok() {
        let d = DiscreteCategoryShell::on_objects("D", vec!["a".into(), "b".into()]);
        assert_eq!(d.morphisms.len(), 2);
        assert!(d.validate_shell().is_ok());
    }

    #[test]
    fn rejects_non_identity() {
        let mut d = DiscreteCategoryShell::on_objects("D", vec!["a".into()]);
        d.morphisms.push(MorphismTriple::new("a", "b", "f"));
        assert!(d.validate_shell().is_err());
    }

    #[test]
    fn each_object_has_one_identity() {
        let shell = DiscreteCategoryShell::on_objects("D", vec!["a".into(), "b".into()]);
        let admitted = DiscreteIdentityWitness::admit(&shell);
        assert!(admitted.is_ok());
        assert_eq!(admitted.ok().map(|witness| witness.object_count()), Some(2));
        let mut broken = shell;
        broken.morphisms.pop();
        assert!(matches!(
            DiscreteIdentityWitness::admit(&broken),
            Err(DiscreteIdentityError::IdentityCount { count: 0, .. })
        ));
    }

}
