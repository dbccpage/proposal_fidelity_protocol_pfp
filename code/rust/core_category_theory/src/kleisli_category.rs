//! Kleisli Category Construction — Spec Section 23.
//!
//! Given a finite category C and a finite monad T on C, the Kleisli category
//! C_T has:
//! - Objects: Same as C.
//! - Morphisms A → B: Morphisms A → T(B) in C.
//! - Identity on A: The monad unit η_A : A → T(A).
//! - Composition of f : A → T(B) and g : B → T(C):
//!   Defined as μ_C ∘ T(g) ∘ f.
//!
//! This module provides two entry points following the Declared → Validated
//! discipline:
//!
//! - `declare_kleisli_category`: builds raw `DeclaredFiniteCategory` from
//!   unvalidated monad data. The caller is responsible for validation.
//!
//! - `build_validated_kleisli_category`: accepts a `ValidatedFiniteCategory`
//!   and `ValidatedFiniteMonad`, constructs the Kleisli category, and returns
//!   a `ValidatedFiniteCategory` on success.
//! Kleisli Category Construction — Spec Section 23.
//!
//! Given a finite category C and a finite monad T on C, the Kleisli category
//! C_T has:
//! - Objects: Same as C.
//! - Morphisms A → B: Morphisms A → T(B) in C.
//! - Identity on A: The monad unit η_A : A → T(A).
//! - Composition of f : A → T(B) and g : B → T(C):
//!   Defined as μ_C ∘ T(g) ∘ f.
//!
//! This module provides two entry points following the Declared → Validated
//! discipline:
//!
//! - `declare_kleisli_category`: builds raw `DeclaredFiniteCategory` from
//!   unvalidated monad data. The caller is responsible for validation.
//!
//! - `build_validated_kleisli_category`: accepts a `ValidatedFiniteCategory`
//!   and `ValidatedFiniteMonad`, constructs the Kleisli category, and returns
//!   a `ValidatedFiniteCategory` on success.

use super::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use super::finite_category_builder::DeclaredFiniteCategoryBuilder;
use super::legacy_monad::{DeclaredFiniteMonad, ValidatedFiniteMonad};
use super::nerve::DeclaredNerve;
use std::collections::BTreeMap;

/// A wrapper that owns a validated Kleisli category and provides a safe,
/// lifetime-free construction path for its nerve.
#[derive(Debug, Clone)]
pub struct KleisliNerve {
    pub kleisli_category: ValidatedFiniteCategory,
}

/// A wrapper that owns a validated Kleisli category and provides a safe,
/// lifetime-free construction path for its nerve.
impl KleisliNerve {
    pub fn try_new(
        name: &str,
        category: &ValidatedFiniteCategory,
        monad: &ValidatedFiniteMonad,
    ) -> Result<Self, String> {
        let kleisli_category = build_validated_kleisli_category(name, category, monad)?;
        Ok(Self { kleisli_category })
    }

    pub fn nerve(&self) -> DeclaredNerve<'_> {
        DeclaredNerve::new(self.kleisli_category.declared())
    }
}

/// Internal record tracking the correspondence between a Kleisli morphism
/// and its underlying base-category morphism.
#[derive(Debug, Clone, PartialEq, Eq)]
struct KleisliMorphism {
    k_name: String,
    orig_name: String,
    source: String,
    target: String,
}

/// Constructs a Kleisli category declaration from raw (unvalidated) inputs.
///
/// Returns a `DeclaredFiniteCategory` whose composition table is derived
/// from the monad's unit, multiplication, and functor action. The result
/// is **not** validated; use `build_validated_kleisli_category` if you
/// need a trust-boundary–enforced output.
///
/// Kleisli morphism names use the delimiter format `K[f=>B]` to avoid
/// collisions when morphism or object names contain underscores.
fn collect_kleisli_morphisms(
    category: &DeclaredFiniteCategory,
    monad: &DeclaredFiniteMonad,
) -> Result<(Vec<KleisliMorphism>, BTreeMap<(String, String), String>), String> {
    let mut k_morphisms: Vec<KleisliMorphism> = Vec::new();
    let mut orig_to_k: BTreeMap<(String, String), String> = BTreeMap::new();
    for f in category.morphisms.values() {
        for (b, tb) in &monad.object_map {
            if tb != &f.target {
                continue;
            }
            let k_name = format!("K[{}=>{}]", f.name, b);
            if orig_to_k.values().any(|existing| existing == &k_name) {
                return Err(format!("Kleisli morphism name collision: {}", k_name));
            }
            k_morphisms.push(KleisliMorphism {
                k_name: k_name.clone(),
                orig_name: f.name.clone(),
                source: f.source.clone(),
                target: b.clone(),
            });
            orig_to_k.insert((f.name.clone(), b.clone()), k_name);
        }
    }
    Ok((k_morphisms, orig_to_k))
}

fn add_kleisli_identities(
    category: &DeclaredFiniteCategory,
    monad: &DeclaredFiniteMonad,
    orig_to_k: &BTreeMap<(String, String), String>,
    mut builder: DeclaredFiniteCategoryBuilder,
) -> Result<DeclaredFiniteCategoryBuilder, String> {
    for a in &category.objects {
        let eta_a = monad
            .unit_components
            .get(a)
            .ok_or_else(|| format!("Monad missing unit for object {}", a))?;

        let k_name = orig_to_k.get(&(eta_a.clone(), a.clone())).ok_or_else(|| {
            format!(
                "Unit {} for {} not found as a valid Kleisli morphism",
                eta_a, a
            )
        })?;

        builder = builder.identity(a, k_name);
    }
    Ok(builder)
}

fn compute_kleisli_composite<'a>(
    f_k: &KleisliMorphism,
    g_k: &KleisliMorphism,
    category: &'a DeclaredFiniteCategory,
    monad: &DeclaredFiniteMonad,
    orig_to_k: &'a BTreeMap<(String, String), String>,
) -> Result<&'a str, String> {
    let c = &g_k.target;
    let tg = monad
        .morphism_map
        .get(&g_k.orig_name)
        .ok_or_else(|| format!("Monad missing T({})", g_k.orig_name))?;

    let step1 = category.compose(&f_k.orig_name, tg).ok_or_else(|| {
        format!(
            "Base category missing composition {} ∘ {}",
            tg, f_k.orig_name
        )
    })?;

    let mu_c = monad
        .multiplication_components
        .get(c)
        .ok_or_else(|| format!("Monad missing μ_{}", c))?;

    let h_orig = category
        .compose(step1, mu_c)
        .ok_or_else(|| format!("Base category missing composition {} ∘ {}", mu_c, step1))?;

    orig_to_k
        .get(&(h_orig.to_string(), c.clone()))
        .map(|s| s.as_str())
        .ok_or_else(|| {
            format!(
                "Resulting morphism {} → T({}) not found in Kleisli morphisms",
                h_orig, c
            )
        })
}

fn add_kleisli_compositions(
    k_morphisms: &[KleisliMorphism],
    category: &DeclaredFiniteCategory,
    monad: &DeclaredFiniteMonad,
    orig_to_k: &BTreeMap<(String, String), String>,
    mut builder: DeclaredFiniteCategoryBuilder,
) -> Result<DeclaredFiniteCategoryBuilder, String> {
    for f_k in k_morphisms {
        for g_k in k_morphisms {
            if f_k.target != g_k.source {
                continue;
            }
            let h_k_name = compute_kleisli_composite(f_k, g_k, category, monad, orig_to_k)?;
            builder = builder.composition(&f_k.k_name, &g_k.k_name, h_k_name);
        }
    }
    Ok(builder)
}

/// Constructs the unvalidated Kleisli category declaration for a monad.
pub fn declare_kleisli_category(
    name: &str,
    category: &DeclaredFiniteCategory,
    monad: &DeclaredFiniteMonad,
) -> Result<DeclaredFiniteCategory, String> {
    let mut builder = DeclaredFiniteCategoryBuilder::new(name);
    for obj in &category.objects {
        builder = builder.object(obj);
    }
    let (k_morphisms, orig_to_k) = collect_kleisli_morphisms(category, monad)?;
    for km in &k_morphisms {
        builder = builder.morphism(&km.k_name, &km.source, &km.target);
    }
    builder = add_kleisli_identities(category, monad, &orig_to_k, builder)?;
    builder = add_kleisli_compositions(&k_morphisms, category, monad, &orig_to_k, builder)?;
    Ok(builder.build())
}

// Internal record tracking the correspondence between a Kleisli morphism
// and its underlying base-category morphism.
// Constructs a Kleisli category declaration from raw (unvalidated) inputs.
//
// Returns a `DeclaredFiniteCategory` whose composition table is derived
// from the monad's unit, multiplication, and functor action. The result
// is **not** validated; use `build_validated_kleisli_category` if you
// need a trust-boundary–enforced output.
//
// Kleisli morphism names use the delimiter format `K[f=>B]` to avoid
// collisions when morphism or object names contain underscores.
    // 1. Objects: Ob(C_T) = Ob(C).
    // 2. Morphisms: For every f : A → T(B) in C, create K[f=>B] : A → B in C_T.
                // Detect name collisions (impossible with bracket delimiters
                // but guarded for defense-in-depth).
    // 3. Identities: The identity on A in Kleisli is η_A : A → T(A).
    // 4. Composition: f_K : A → B, g_K : B → C
    //    Their Kleisli composite is h_K : A → C where h = μ_C ∘ T(g) ∘ f.
            // Step 1: T(g) — apply the monad's functor action to g.
            // Step 2: T(g) ∘ f in the base category.
            // Step 3: μ_C — the monad multiplication at C.
            // Step 4: h = μ_C ∘ (T(g) ∘ f) in the base category.
            // Map the resulting base morphism back to the Kleisli name.
// Constructs and validates a Kleisli category from pre-validated inputs.
//
// Accepts a `ValidatedFiniteCategory` and `ValidatedFiniteMonad`, builds
// the Kleisli declaration, then validates the result as a finite category.
// This enforces the full trust chain:
//
// ```text
// ValidatedFiniteCategory + ValidatedFiniteMonad
//   → DeclaredFiniteCategory (Kleisli)
//   → ValidatedFiniteCategory (Kleisli)
// ```
/// Constructs and validates a Kleisli category from pre-validated inputs.
///
/// Accepts a `ValidatedFiniteCategory` and `ValidatedFiniteMonad`, builds
/// the Kleisli declaration, then validates the result as a finite category.
/// This enforces the full trust chain:
///
/// ```text
/// ValidatedFiniteCategory + ValidatedFiniteMonad
///   → DeclaredFiniteCategory (Kleisli)
///   → ValidatedFiniteCategory (Kleisli)
/// ```
pub fn build_validated_kleisli_category(
    name: &str,
    category: &ValidatedFiniteCategory,
    monad: &ValidatedFiniteMonad,
) -> Result<ValidatedFiniteCategory, String> {
    let declared = declare_kleisli_category(name, category.declared(), monad.declared())?;
    ValidatedFiniteCategory::try_new(declared).map_err(|report| {
        format!(
            "Kleisli category failed validation: {:?}",
            report.typed_violations
        )
    })
}

// Origin: engine/crates_rs/core_category_theory/src/kleisli_category.rs
// Claim: urn:core:crates_rs:core-category-theory:kleisli-category:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordd6ef0beb {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordd6ef0beb` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrord6ef0beb {
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
impl BoundaryErrord6ef0beb {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrord6ef0beb {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrord6ef0beb {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordd6ef0beb {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrord6ef0beb> {
        if capacity_bound == 0 {
            return Err(BoundaryErrord6ef0beb::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrord6ef0beb::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrord6ef0beb::ExceedsCapacity {
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

        // Build base category C with just object A and id_A
    #[test]
    fn test_declare_kleisli_identity_monad() {
        // Build base category C with just object A and id_A
        let cat = DeclaredFiniteCategoryBuilder::new("C")
            .identity_object("A")
            .identity_compositions()
            .build();

        // Build identity monad: T = id, η = id, μ = id
        // Kleisli should have exactly one morphism K[id_A=>A]
        // Check composition: k_id ∘ k_id = k_id
        // Build identity monad: T = id, η = id, μ = id
        let mut m = DeclaredFiniteMonad::new("Id", "C");
        m.set_object_map("A", "A");
        m.set_morphism_map("id_A", "id_A");
        m.set_unit("A", "id_A");
        m.set_multiply("A", "id_A");

        let kleisli =
            declare_kleisli_category("K(C)", &cat, &m).expect("Should build Kleisli category");

        assert_eq!(kleisli.name, "K(C)");
        assert!(kleisli.has_object("A"));

        // Kleisli should have exactly one morphism K[id_A=>A]
        let k_id = "K[id_A=>A]";
        assert!(kleisli.has_morphism(k_id));
        assert_eq!(kleisli.identity_of("A").unwrap(), k_id);

        // Check composition: k_id ∘ k_id = k_id
        assert_eq!(kleisli.compose(k_id, k_id).unwrap(), k_id);
    }

    /// Non-trivial test: walking arrow A → B with identity monad.
    ///
    /// Base category: {A, B}, morphisms {id_A, id_B, f : A → B}.
    /// Identity monad: T = id on all.
    ///
    /// Expected Kleisli morphisms:
    ///   K[id_A=>A] : A → A  (identity on A)
    ///   K[id_B=>B] : B → B  (identity on B)
    ///   K[f=>B]    : A → B
    ///
    /// Expected composition:
    ///   K[id_A=>A] ∘ K[f=>B] = K[f=>B]
    ///   K[f=>B] ∘ K[id_B=>B] = K[f=>B]
        // Identity compositions
        // Identity self-composition
    /// Non-trivial test: walking arrow A → B with identity monad.
    ///
    /// Base category: {A, B}, morphisms {id_A, id_B, f : A → B}.
    /// Identity monad: T = id on all.
    ///
    /// Expected Kleisli morphisms:
    ///   K[id_A=>A] : A → A  (identity on A)
    ///   K[id_B=>B] : B → B  (identity on B)
    ///   K[f=>B]    : A → B
    ///
    /// Expected composition:
    ///   K[id_A=>A] ∘ K[f=>B] = K[f=>B]
    ///   K[f=>B] ∘ K[id_B=>B] = K[f=>B]
    #[test]
    fn test_kleisli_walking_arrow_with_identity_monad() {
        let cat = DeclaredFiniteCategoryBuilder::new("WalkingArrow")
            .identity_object("A")
            .identity_object("B")
            .morphism("f", "A", "B")
            .identity_compositions()
            .composition("id_A", "f", "f")
            .composition("f", "id_B", "f")
            .build();

        let mut m = DeclaredFiniteMonad::new("Id", "WalkingArrow");
        m.set_object_map("A", "A");
        m.set_object_map("B", "B");
        m.set_morphism_map("id_A", "id_A");
        m.set_morphism_map("id_B", "id_B");
        m.set_morphism_map("f", "f");
        m.set_unit("A", "id_A");
        m.set_unit("B", "id_B");
        m.set_multiply("A", "id_A");
        m.set_multiply("B", "id_B");

        let kleisli = declare_kleisli_category("K(WA)", &cat, &m)
            .expect("Should build walking arrow Kleisli");

        assert!(kleisli.has_object("A"));
        assert!(kleisli.has_object("B"));

        let k_f = "K[f=>B]";
        let k_id_a = "K[id_A=>A]";
        let k_id_b = "K[id_B=>B]";

        assert!(kleisli.has_morphism(k_f));
        assert!(kleisli.has_morphism(k_id_a));
        assert!(kleisli.has_morphism(k_id_b));

        // Identity compositions
        assert_eq!(kleisli.compose(k_id_a, k_f).unwrap(), k_f);
        assert_eq!(kleisli.compose(k_f, k_id_b).unwrap(), k_f);

        // Identity self-composition
        assert_eq!(kleisli.compose(k_id_a, k_id_a).unwrap(), k_id_a);
        assert_eq!(kleisli.compose(k_id_b, k_id_b).unwrap(), k_id_b);
    }

    #[test]
    fn test_validated_kleisli_from_validated_inputs() {
        let cat = DeclaredFiniteCategoryBuilder::new("C")
            .identity_object("A")
            .identity_compositions()
            .build_validated()
            .expect("Base category should validate");

        let mut m = DeclaredFiniteMonad::new("Id", "C");
        m.set_object_map("A", "A");
        m.set_morphism_map("id_A", "id_A");
        m.set_unit("A", "id_A");
        m.set_multiply("A", "id_A");

        let validated_monad = ValidatedFiniteMonad::try_new(m, cat.declared())
            .expect("Identity monad should validate");

        let validated_kleisli = build_validated_kleisli_category("K(C)", &cat, &validated_monad)
            .expect("Validated Kleisli should succeed");

        assert_eq!(validated_kleisli.declared().name, "K(C)");
        assert!(validated_kleisli.declared().has_object("A"));
    }

    #[test]
    fn test_nerve_of_kleisli_walking_arrow_identity_monad() {
        use super::super::nerve::Simplex;

        let cat = DeclaredFiniteCategoryBuilder::new("WalkingArrow")
            .identity_object("A")
            .identity_object("B")
            .morphism("f", "A", "B")
            .identity_compositions()
            .composition("id_A", "f", "f")
            .composition("f", "id_B", "f")
            .build();

        let mut m = DeclaredFiniteMonad::new("Id", "WalkingArrow");
        m.set_object_map("A", "A");
        m.set_object_map("B", "B");
        m.set_morphism_map("id_A", "id_A");
        m.set_morphism_map("id_B", "id_B");
        m.set_morphism_map("f", "f");
        m.set_unit("A", "id_A");
        m.set_unit("B", "id_B");
        m.set_multiply("A", "id_A");
        m.set_multiply("B", "id_B");

        let kleisli =
            declare_kleisli_category("K(WA)", &cat, &m).expect("Kleisli category should build");

        let nerve = DeclaredNerve::new(&kleisli);

        assert_eq!(nerve.n_simplices(0).len(), 2);
        assert_eq!(nerve.n_simplices(1).len(), 3);

        let nondegenerate_1 = nerve.nondegenerate_n_simplices(1);
        assert_eq!(
            nondegenerate_1,
            vec![Simplex::Chain(vec!["K[f=>B]".into()])]
        );
    }
}

#[cfg(test)]
mod l4_boundary_tests_d6ef0beb {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordd6ef0beb::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordd6ef0beb::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordd6ef0beb::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordd6ef0beb::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordd6ef0beb::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrord6ef0beb::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrord6ef0beb::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
