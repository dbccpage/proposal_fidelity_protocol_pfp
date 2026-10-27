//! Dagger structures on explicit finite categories: identity on objects,
//! contravariant on arrows, involutive and composition-reversing. Validation
//! checks every declared arrow and composite, after the canonical finite
//! category checker. AuthorityEffect: None.
use crate::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use crate::validation::ValidationReport;
use std::collections::BTreeMap;

#[derive(Debug, Clone)]
pub enum DaggerValidationError {
    Budget,
    Category(ValidationReport),
    Domain,
    MissingImage { morphism: String },
    Boundary { morphism: String },
    Involution { morphism: String },
    Identity { object: String },
    Composition { first: String, second: String },
}
impl std::fmt::Display for DaggerValidationError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "finite dagger validation refused: {self:?}")
    }
}
impl std::error::Error for DaggerValidationError {}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DaggerStructure {
    category: ValidatedFiniteCategory,
    dagger: BTreeMap<String, String>,
}
fn check_dagger_arrow_involution(
    declared: &DeclaredFiniteCategory,
    dagger: &BTreeMap<String, String>,
) -> Result<(), DaggerValidationError> {
    for (f, morphism) in &declared.morphisms {
        let fd = dagger
            .get(f)
            .ok_or_else(|| DaggerValidationError::MissingImage {
                morphism: f.clone(),
            })?;
        let image =
            declared
                .morphisms
                .get(fd)
                .ok_or_else(|| DaggerValidationError::MissingImage {
                    morphism: f.clone(),
                })?;
        if image.source != morphism.target || image.target != morphism.source {
            return Err(DaggerValidationError::Boundary {
                morphism: f.clone(),
            });
        }
        if dagger.get(fd) != Some(f) {
            return Err(DaggerValidationError::Involution {
                morphism: f.clone(),
            });
        }
    }
    Ok(())
}

fn check_dagger_identities_and_compositions(
    declared: &DeclaredFiniteCategory,
    dagger: &BTreeMap<String, String>,
) -> Result<(), DaggerValidationError> {
    for (object, identity) in &declared.identities {
        if dagger.get(identity) != Some(identity) {
            return Err(DaggerValidationError::Identity {
                object: object.clone(),
            });
        }
    }
    for ((first, second), composite) in &declared.compositions {
        let expected = declared.compose(&dagger[second], &dagger[first]);
        if expected != dagger.get(composite).map(String::as_str) {
            return Err(DaggerValidationError::Composition {
                first: first.clone(),
                second: second.clone(),
            });
        }
    }
    Ok(())
}

impl DaggerStructure {
    /// A total involutive contravariant dagger. The arrow bound protects the
    /// cubic associativity validation; there is no unchecked declaration mode.
    pub fn try_new(
        category: DeclaredFiniteCategory,
        dagger: BTreeMap<String, String>,
    ) -> Result<Self, DaggerValidationError> {
        if category.objects.len() > 64
            || category.morphisms.len() > 64
            || category.compositions.len() > 4096
        {
            return Err(DaggerValidationError::Budget);
        }
        let category =
            ValidatedFiniteCategory::try_new(category).map_err(DaggerValidationError::Category)?;
        let declared = category.declared();
        if dagger.len() != declared.morphisms.len()
            || dagger.keys().any(|f| !declared.has_morphism(f))
        {
            return Err(DaggerValidationError::Domain);
        }
        check_dagger_arrow_involution(declared, &dagger)?;
        check_dagger_identities_and_compositions(declared, &dagger)?;
        Ok(Self { category, dagger })
    }
    pub fn category(&self) -> &ValidatedFiniteCategory {
        &self.category
    }
    pub fn dagger(&self, morphism: &str) -> Option<&str> {
        self.dagger.get(morphism).map(String::as_str)
    }
    /// A unitary arrow has both inverse equations with its dagger. Unknown
    /// arrows return None, so absence cannot be mistaken for nonunitarity.
    pub fn is_unitary(&self, morphism: &str) -> Option<bool> {
        let c = self.category.declared();
        let (source, target) = c.boundary_of(morphism)?;
        let fd = self.dagger(morphism)?;
        Some(
            c.compose(morphism, fd) == c.identity_of(source)
                && c.compose(fd, morphism) == c.identity_of(target),
        )
    }
}

// Origin: engine/crates_rs/core_category_theory/src/dagger.rs
// Claim: urn:core:crates_rs:core-category-theory:dagger:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    fn check_s3_dagger() {
        // The one-object S3 category; composition applies first then second.
        let permutations = [
            [0, 1, 2],
            [0, 2, 1],
            [1, 0, 2],
            [1, 2, 0],
            [2, 0, 1],
            [2, 1, 0],
        ];
        let name = |i: usize| format!("p{i}");
        let mut group = DeclaredFiniteCategory::new("S3");
        for i in 0..6 {
            group.add_morphism(&name(i), "*", "*");
        }
        group.set_identity("*", &name(0));
        let mut dagger = BTreeMap::new();
        for i in 0..6 {
            let inverse = permutations
                .iter()
                .position(|p| (0..3).all(|j| p[permutations[i][j]] == j))
                .unwrap();
            dagger.insert(name(i), name(inverse));
            for j in 0..6 {
                let product =
                    std::array::from_fn::<_, 3, _>(|a| permutations[j][permutations[i][a]]);
                let k = permutations.iter().position(|p| *p == product).unwrap();
                group.set_composition(&name(i), &name(j), &name(k));
            }
        }
        let group = DaggerStructure::try_new(group, dagger).unwrap();
        assert!((0..6).all(|i| group.is_unitary(&name(i)) == Some(true)));
    }

    fn check_pair_groupoid_dagger() {
        let mut pair = DeclaredFiniteCategory::new("pair groupoid");
        let mut dagger = BTreeMap::new();
        let arrow = |i: usize, j: usize| format!("{i}>{j}");
        for i in 0..2 {
            for j in 0..2 {
                pair.add_morphism(&arrow(i, j), &i.to_string(), &j.to_string());
                dagger.insert(arrow(i, j), arrow(j, i));
                for k in 0..2 {
                    pair.set_composition(&arrow(i, j), &arrow(j, k), &arrow(i, k));
                }
            }
            pair.set_identity(&i.to_string(), &arrow(i, i));
        }
        assert!(DaggerStructure::try_new(pair, dagger)
            .unwrap()
            .is_unitary("0>1")
            .unwrap());
    }

    fn check_relations_dagger() {
        let name = |i: usize| format!("p{i}");
        // All binary relations on a two-point set, not only invertible arrows.
        let mut relations = DeclaredFiniteCategory::new("Rel(2)");
        let mut dagger = BTreeMap::new();
        for a in 0..16usize {
            relations.add_morphism(&name(a), "2", "2");
            let converse = (0..2)
                .flat_map(|i| (0..2).map(move |j| (i, j)))
                .fold(0, |r, (i, j)| r | (((a >> (2 * j + i)) & 1) << (2 * i + j)));
            dagger.insert(name(a), name(converse));
            for b in 0..16usize {
                let mut product = 0;
                for i in 0..2 {
                    for j in 0..2 {
                        if (0..2)
                            .any(|k| a & (1 << (2 * i + k)) != 0 && b & (1 << (2 * k + j)) != 0)
                        {
                            product |= 1 << (2 * i + j);
                        }
                    }
                }
                relations.set_composition(&name(a), &name(b), &name(product));
            }
        }
        relations.set_identity("2", &name(9));
        let relations = DaggerStructure::try_new(relations, dagger).unwrap();
        assert_eq!(relations.is_unitary("p6"), Some(true));
        assert_eq!(relations.is_unitary("p15"), Some(false));
        assert_eq!(relations.is_unitary("missing"), None);
    }

    #[test]
    fn group_groupoid_and_relations_are_dagger_categories() {
        check_s3_dagger();
        check_pair_groupoid_dagger();
        check_relations_dagger();
    }
    #[test]
    fn the_walking_arrow_with_identity_dagger_is_refused() {
        let mut c = DeclaredFiniteCategory::new("arrow");
        c.add_identity("A", "id_A");
        c.add_identity("B", "id_B");
        c.add_morphism("f", "A", "B");
        for (f, g, h) in [
            ("id_A", "id_A", "id_A"),
            ("id_B", "id_B", "id_B"),
            ("id_A", "f", "f"),
            ("f", "id_B", "f"),
        ] {
            c.set_composition(f, g, h);
        }
        let d = ["id_A", "id_B", "f"]
            .map(|f| (f.to_string(), f.to_string()))
            .into_iter()
            .collect();
        assert!(matches!(
            DaggerStructure::try_new(c, d),
            Err(DaggerValidationError::Boundary { .. })
        ));
    }
}
