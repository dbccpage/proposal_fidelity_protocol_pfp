//! Checked finite groupoids and their matrix/group coordinates.
//!
//! This strengthens the canonical finite dagger category by requiring every
//! arrow to be unitary. It does not freely adjoin inverses or identify histories.
//! Composition retains the category convention: `compose(f, g)` means g after f.
//! The inherited bound is 64 arrows. AuthorityEffect: None.

use crate::dagger::{DaggerStructure, DaggerValidationError};
use crate::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use std::collections::{BTreeMap, BTreeSet};

#[derive(Debug, Clone)]
pub enum GroupoidError {
    Dagger(DaggerValidationError),
    Noninvertible {
        morphism: String,
    },
    /// A required witness could not be resolved; never silently omit it.
    MissingStructure,
}
impl std::fmt::Display for GroupoidError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "finite groupoid refused: {self:?}")
    }
}
impl std::error::Error for GroupoidError {}

/// A component with a chosen base object and arrows p_x : root -> x.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GroupoidComponent {
    pub root: String,
    pub objects: BTreeSet<String>,
    pub isotropy: BTreeSet<String>,
    pub connectors: BTreeMap<String, String>,
}

/// g : x -> y maps to E_(y,x) tensor (p_y^-1 g p_x).
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct GroupoidMatrixCoordinate {
    pub component_root: String,
    pub row_object: String,
    pub column_object: String,
    pub isotropy_arrow: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ValidatedFiniteGroupoid {
    dagger: DaggerStructure,
}
impl ValidatedFiniteGroupoid {
    pub fn try_new(
        category: DeclaredFiniteCategory,
        inverses: BTreeMap<String, String>,
    ) -> Result<Self, GroupoidError> {
        Self::try_from_dagger(
            DaggerStructure::try_new(category, inverses).map_err(GroupoidError::Dagger)?,
        )
    }

    pub fn try_from_dagger(dagger: DaggerStructure) -> Result<Self, GroupoidError> {
        for morphism in dagger.category().declared().morphisms.keys() {
            if dagger.is_unitary(morphism) != Some(true) {
                return Err(GroupoidError::Noninvertible {
                    morphism: morphism.clone(),
                });
            }
        }
        Ok(Self { dagger })
    }

    pub fn category(&self) -> &ValidatedFiniteCategory {
        self.dagger.category()
    }
    pub fn inverse(&self, morphism: &str) -> Option<&str> {
        self.dagger.dagger(morphism)
    }

    /// Deterministic choices: least remaining object, then least connector;
    /// the root connector is its identity. No sampled reachability is used.
    pub fn components(&self) -> Result<Vec<GroupoidComponent>, GroupoidError> {
        let c = self.category().declared();
        let mut remaining = c.objects.clone();
        let mut result = Vec::new();
        while let Some(root) = remaining.first().cloned() {
            // In a groupoid, composites and inverses turn every zigzag into
            // a single arrow. All connected objects occur among these targets.
            let mut connectors = BTreeMap::new();
            let mut isotropy = BTreeSet::new();
            for (name, arrow) in &c.morphisms {
                if arrow.source == root {
                    connectors
                        .entry(arrow.target.clone())
                        .or_insert(name.clone());
                    if arrow.target == root {
                        isotropy.insert(name.clone());
                    }
                }
            }
            let identity = c
                .identity_of(&root)
                .ok_or(GroupoidError::MissingStructure)?;
            connectors.insert(root.clone(), identity.to_owned());
            let objects: BTreeSet<_> = connectors.keys().cloned().collect();
            for object in &objects {
                if !remaining.remove(object) {
                    return Err(GroupoidError::MissingStructure);
                }
            }
            result.push(GroupoidComponent {
                root,
                objects,
                isotropy,
                connectors,
            });
        }
        Ok(result)
    }

    fn component_arrow_coordinate(
        &self,
        c: &DeclaredFiniteCategory,
        component: &GroupoidComponent,
        name: &str,
        source: &String,
        target: &String,
    ) -> Result<Option<GroupoidMatrixCoordinate>, GroupoidError> {
        if !component.objects.contains(source) {
            return Ok(None);
        }
        let px = component
            .connectors
            .get(source)
            .ok_or(GroupoidError::MissingStructure)?;
        let py = component
            .connectors
            .get(target)
            .ok_or(GroupoidError::MissingStructure)?;
        let pyi = self.inverse(py).ok_or(GroupoidError::MissingStructure)?;
        let gpx = c.compose(px, name).ok_or(GroupoidError::MissingStructure)?;
        let h = c.compose(gpx, pyi).ok_or(GroupoidError::MissingStructure)?;
        if !component.isotropy.contains(h) {
            return Err(GroupoidError::MissingStructure);
        }
        Ok(Some(GroupoidMatrixCoordinate {
            component_root: component.root.clone(),
            row_object: target.clone(),
            column_object: source.clone(),
            isotropy_arrow: h.to_owned(),
        }))
    }

    pub fn matrix_coordinates(
        &self,
    ) -> Result<BTreeMap<String, GroupoidMatrixCoordinate>, GroupoidError> {
        let c = self.category().declared();
        let mut result = BTreeMap::new();
        for component in self.components()? {
            for (name, arrow) in &c.morphisms {
                if let Some(coord) = self.component_arrow_coordinate(
                    c,
                    &component,
                    name,
                    &arrow.source,
                    &arrow.target,
                )? {
                    result.insert(name.clone(), coord);
                }
            }
        }
        if result.len() != c.morphisms.len() {
            return Err(GroupoidError::MissingStructure);
        }
        Ok(result)
    }

    /// Structural criterion for a nonzero simple COMPLEX groupoid algebra.
    /// This is not a claim about admitted states, scalars, or physical processes.
    pub fn is_connected_thin(&self) -> Result<bool, GroupoidError> {
        let components = self.components()?;
        Ok(components.len() == 1 && components[0].isotropy.len() == 1)
    }
}

// Origin: engine/crates_rs/core_category_theory/src/finite_groupoid.rs
// Claim: urn:core:crates_rs:core-category-theory:finite-groupoid:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn an_involutive_dagger_need_not_supply_inverses() {
        // The idempotent monoid {1,z}, z^2=z, with identity dagger.
        let mut c = DeclaredFiniteCategory::new("noninvertible dagger");
        c.add_identity("x", "1");
        c.add_morphism("z", "x", "x");
        for (a, b, ab) in [
            ("1", "1", "1"),
            ("1", "z", "z"),
            ("z", "1", "z"),
            ("z", "z", "z"),
        ] {
            c.set_composition(a, b, ab);
        }
        let d = DaggerStructure::try_new(
            c,
            BTreeMap::from([("1".into(), "1".into()), ("z".into(), "z".into())]),
        )
        .unwrap();
        assert!(matches!(ValidatedFiniteGroupoid::try_from_dagger(d),
            Err(GroupoidError::Noninvertible { morphism }) if morphism == "z"));
    }

    #[test]
    fn missing_composition_and_wrong_inverse_are_refused() {
        let mut c = DeclaredFiniteCategory::new("C3");
        let name = |i: usize| i.to_string();
        for i in 0..3 {
            c.add_morphism(&name(i), "x", "x");
        }
        c.set_identity("x", "0");
        for i in 0..3 {
            for j in 0..3 {
                c.set_composition(&name(i), &name(j), &name((i + j) % 3));
            }
        }
        let inv = (0..3).map(|i| (name(i), name((3 - i) % 3))).collect();
        let g = ValidatedFiniteGroupoid::try_new(c.clone(), inv).unwrap();
        assert_eq!(g.inverse("1"), Some("2"));
        assert_eq!(g.inverse("unknown"), None);
        assert!(!g.is_connected_thin().unwrap());
        let bad = (0..3).map(|i| (name(i), name(i))).collect();
        assert!(ValidatedFiniteGroupoid::try_new(c.clone(), bad).is_err());
        let missing = (0..2).map(|i| (name(i), name((3 - i) % 3))).collect();
        assert!(matches!(
            ValidatedFiniteGroupoid::try_new(c.clone(), missing),
            Err(GroupoidError::Dagger(DaggerValidationError::Domain))
        ));
        c.compositions.remove(&("1".into(), "2".into()));
        let inv = (0..3).map(|i| (name(i), name((3 - i) % 3))).collect();
        assert!(matches!(
            ValidatedFiniteGroupoid::try_new(c, inv),
            Err(GroupoidError::Dagger(DaggerValidationError::Category(_)))
        ));
    }

    #[test]
    fn empty_groupoid_is_not_connected_thin_and_budget_is_enforced() {
        let empty =
            ValidatedFiniteGroupoid::try_new(DeclaredFiniteCategory::new("empty"), BTreeMap::new())
                .unwrap();
        assert!(empty.components().unwrap().is_empty());
        assert!(!empty.is_connected_thin().unwrap());
        let mut too_large = DeclaredFiniteCategory::new("over budget");
        for i in 0..65 {
            too_large.add_object(&i.to_string());
        }
        assert!(matches!(
            ValidatedFiniteGroupoid::try_new(too_large, BTreeMap::new()),
            Err(GroupoidError::Dagger(DaggerValidationError::Budget))
        ));
    }
}
