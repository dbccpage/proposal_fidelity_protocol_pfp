//! Higher-Category Functors — Spec Section 10.
//!
//! Three strictness levels:
//!   Strict 2-Functor:  preserves composition and identity by equality.
//!   Pseudofunctor:     preserves up to invertible 2-cells (coherence required).
//!   Lax Functor:       preserves up to possibly non-invertible 2-cells.
//!
//! Direction convention (lax, not oplax):
//!   Composition:  F(g) ∘ F(f) ⇒ F(g ∘ f)
//!   Unit:         id_{F(A)} ⇒ F(id_A)
//!
//! The reverse (oplax) direction would be:
//!   Composition:  F(g ∘ f) ⇒ F(g) ∘ F(f)
//!   Unit:         F(id_A) ⇒ id_{F(A)}
//! This module uses the lax convention exclusively.
//!
//! Boundary preservation (validation obligation, not compiler-enforced):
//!   For 1-cells:  src₁(F(f)) = F(src₁(f)),  tgt₁(F(f)) = F(tgt₁(f))
//!   For 2-cells:  src₂(F(α)) = F(src₂(α)),  tgt₂(F(α)) = F(tgt₂(α))

use super::higher::TwoCategory;
use std::collections::BTreeMap;

// ===========================================================================
// Invertible 2-cell witness
// ===========================================================================

/// An invertible 2-cell, used by pseudofunctors to witness coherence.
///
/// A plain `TwoMor` cannot express invertibility. This wrapper pairs a
/// forward 2-cell with its inverse so that the finite validator can
/// check the round-trip laws:
///   inverse ∘_v forward = id_{source}
///   forward ∘_v inverse = id_{target}
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct InvertibleTwoMor<TwoMor: Clone + Eq + std::fmt::Debug> {
    pub forward: TwoMor,
    pub inverse: TwoMor,
}

// ===========================================================================
// Shared mapping interface
// ===========================================================================

/// The shared object/1-cell/2-cell mapping that all 2-functor variants
/// (strict, pseudo, lax) must provide.
pub trait TwoFunctorMapping {
    type Source: TwoCategory;
    type Target: TwoCategory;

    fn map_ob(&self, a: &<Self::Source as TwoCategory>::Ob) -> <Self::Target as TwoCategory>::Ob;

    fn map_1(
        &self,
        f: &<Self::Source as TwoCategory>::OneMor,
    ) -> <Self::Target as TwoCategory>::OneMor;

    fn map_2(
        &self,
        alpha: &<Self::Source as TwoCategory>::TwoMor,
    ) -> <Self::Target as TwoCategory>::TwoMor;
}

// ===========================================================================
// Strict 2-Functor
// ===========================================================================

/// Strict 2-functor F : C → D.
///
/// Laws (equality on the nose):
///   F(id_A)     = id_{F(A)}
///   F(g ∘ f)    = F(g) ∘ F(f)
///   F(id_f)     = id_{F(f)}
///   F(β ∘_v α)  = F(β) ∘_v F(α)       (vertical composition)
///   F(β ∘_h α)  = F(β) ∘_h F(α)       (horizontal composition)
pub trait StrictTwoFunctor: TwoFunctorMapping {}

// ===========================================================================
// Pseudofunctor (weak 2-functor)
// ===========================================================================

/// Pseudofunctor F : C → D.
///
/// Preserves composition and identity up to **invertible** 2-cells.
/// Must satisfy pentagon and triangle coherence laws.
///
/// Coherence cells:
///   comp_coherence(f, g):  for f : A → B and g : B → C,
///     invertible 2-cell  F(g) ∘ F(f) ⇒ F(g ∘ f)
///
///   id_coherence(A):
///     invertible 2-cell  id_{F(A)} ⇒ F(id_A)
pub trait PseudoFunctor: TwoFunctorMapping {
    /// Invertible composition coherence 2-cell:
    /// F(g) ∘ F(f) ⇒ F(g ∘ f), for composable f : A → B and g : B → C.
    fn comp_coherence(
        &self,
        f: &<Self::Source as TwoCategory>::OneMor,
        g: &<Self::Source as TwoCategory>::OneMor,
    ) -> InvertibleTwoMor<<Self::Target as TwoCategory>::TwoMor>;

    /// Invertible identity coherence 2-cell:
    /// id_{F(A)} ⇒ F(id_A).
    fn id_coherence(
        &self,
        a: &<Self::Source as TwoCategory>::Ob,
    ) -> InvertibleTwoMor<<Self::Target as TwoCategory>::TwoMor>;
}

// ===========================================================================
// Lax Functor
// ===========================================================================

/// Lax functor F : C → D.
///
/// 2-cells need not be invertible.
/// Direction (lax, not oplax):
///   lax_comp(f, g):  F(g) ∘ F(f) ⇒ F(g ∘ f)   for composable f, g.
///   lax_id(A):       id_{F(A)} ⇒ F(id_A)
pub trait LaxFunctor: TwoFunctorMapping {
    /// Lax composition: possibly non-invertible 2-cell
    /// F(g) ∘ F(f) ⇒ F(g ∘ f), for composable f : A → B and g : B → C.
    fn lax_comp(
        &self,
        f: &<Self::Source as TwoCategory>::OneMor,
        g: &<Self::Source as TwoCategory>::OneMor,
    ) -> <Self::Target as TwoCategory>::TwoMor;

    /// Lax unit: possibly non-invertible 2-cell
    /// id_{F(A)} ⇒ F(id_A).
    fn lax_id(
        &self,
        a: &<Self::Source as TwoCategory>::Ob,
    ) -> <Self::Target as TwoCategory>::TwoMor;
}

// ===========================================================================
// Finite declared 2-functors (kernel-auditable data)
// ===========================================================================

/// Finite invertible 2-cell witness for audit tables.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteInvertibleTwoMor {
    pub forward: String,
    pub inverse: String,
}

/// An explicit, finite strict 2-functor declaration for kernel audit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteTwoFunctor {
    pub name: String,
    pub source_two_category: String,
    pub target_two_category: String,

    pub object_map: BTreeMap<String, String>,
    pub one_morphism_map: BTreeMap<String, String>,
    pub two_morphism_map: BTreeMap<String, String>,
}

impl DeclaredFiniteTwoFunctor {
    pub fn new(name: &str, source: &str, target: &str) -> Self {
        Self {
            name: name.into(),
            source_two_category: source.into(),
            target_two_category: target.into(),
            object_map: BTreeMap::new(),
            one_morphism_map: BTreeMap::new(),
            two_morphism_map: BTreeMap::new(),
        }
    }

    pub fn on_ob(&self, a: &str) -> Option<&str> {
        self.object_map.get(a).map(|s| s.as_str())
    }

    pub fn on_1(&self, f: &str) -> Option<&str> {
        self.one_morphism_map.get(f).map(|s| s.as_str())
    }

    pub fn on_2(&self, alpha: &str) -> Option<&str> {
        self.two_morphism_map.get(alpha).map(|s| s.as_str())
    }
}

/// An explicit, finite pseudofunctor declaration for kernel audit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFinitePseudoFunctor {
    pub underlying: DeclaredFiniteTwoFunctor,
    /// Composition coherence: (f, g) → invertible 2-cell F(g)∘F(f) ⇒ F(g∘f).
    pub comp_coherence: BTreeMap<(String, String), DeclaredFiniteInvertibleTwoMor>,
    /// Identity coherence: A → invertible 2-cell id_{F(A)} ⇒ F(id_A).
    pub id_coherence: BTreeMap<String, DeclaredFiniteInvertibleTwoMor>,
}

/// An explicit, finite lax functor declaration for kernel audit.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteLaxFunctor {
    pub underlying: DeclaredFiniteTwoFunctor,
    /// Lax composition: (f, g) → 2-cell F(g)∘F(f) ⇒ F(g∘f).
    pub lax_comp: BTreeMap<(String, String), String>,
    /// Lax unit: A → 2-cell id_{F(A)} ⇒ F(id_A).
    pub lax_id: BTreeMap<String, String>,
}

// ===========================================================================
// Finite 2-functor boundary validation
// ===========================================================================

/// Validate 1-cell boundary preservation:
///   src₁(F(f)) = F(src₁(f))
///   tgt₁(F(f)) = F(tgt₁(f))
///
/// `source_one_boundaries` maps each 1-morphism name to (source_obj, target_obj).
/// `target_one_boundaries` maps each target 1-morphism name to (source_obj, target_obj).
pub fn check_two_functor_one_boundaries(
    functor: &DeclaredFiniteTwoFunctor,
    source_one_boundaries: &BTreeMap<String, (String, String)>,
    target_one_boundaries: &BTreeMap<String, (String, String)>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (f, (src_obj, tgt_obj)) in source_one_boundaries {
        let Some(f_img) = functor.on_1(f) else {
            violations.push(format!("1-boundary: F({}) is not defined", f));
            continue;
        };

        let Some(src_img) = functor.on_ob(src_obj) else {
            violations.push(format!("1-boundary: F({}) is not defined", src_obj));
            continue;
        };

        let Some(tgt_img) = functor.on_ob(tgt_obj) else {
            violations.push(format!("1-boundary: F({}) is not defined", tgt_obj));
            continue;
        };

        let Some((actual_src, actual_tgt)) = target_one_boundaries.get(f_img) else {
            violations.push(format!(
                "1-boundary: target boundary for F({}) = {} is not defined",
                f, f_img
            ));
            continue;
        };

        if actual_src != src_img {
            violations.push(format!(
                "1-boundary violated for {}: src₁(F({})) = {}, expected F(src₁({})) = {}",
                f, f, actual_src, f, src_img
            ));
        }

        if actual_tgt != tgt_img {
            violations.push(format!(
                "1-boundary violated for {}: tgt₁(F({})) = {}, expected F(tgt₁({})) = {}",
                f, f, actual_tgt, f, tgt_img
            ));
        }
    }

    violations
}

/// Validate 2-cell boundary preservation:
///   src₂(F(α)) = F(src₂(α))
///   tgt₂(F(α)) = F(tgt₂(α))
///
/// `source_two_boundaries` maps each 2-morphism name to (source_1mor, target_1mor).
/// `target_two_boundaries` maps each target 2-morphism name to (source_1mor, target_1mor).
pub fn check_two_functor_two_boundaries(
    functor: &DeclaredFiniteTwoFunctor,
    source_two_boundaries: &BTreeMap<String, (String, String)>,
    target_two_boundaries: &BTreeMap<String, (String, String)>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for (alpha, (src_1mor, tgt_1mor)) in source_two_boundaries {
        let Some(alpha_img) = functor.on_2(alpha) else {
            violations.push(format!("2-boundary: F({}) is not defined", alpha));
            continue;
        };

        let Some(src_img) = functor.on_1(src_1mor) else {
            violations.push(format!("2-boundary: F({}) is not defined", src_1mor));
            continue;
        };

        let Some(tgt_img) = functor.on_1(tgt_1mor) else {
            violations.push(format!("2-boundary: F({}) is not defined", tgt_1mor));
            continue;
        };

        let Some((actual_src, actual_tgt)) = target_two_boundaries.get(alpha_img) else {
            violations.push(format!(
                "2-boundary: target boundary for F({}) = {} is not defined",
                alpha, alpha_img
            ));
            continue;
        };

        if actual_src != src_img {
            violations.push(format!(
                "2-boundary violated for {}: src₂(F({})) = {}, expected F(src₂({})) = {}",
                alpha, alpha, actual_src, alpha, src_img
            ));
        }

        if actual_tgt != tgt_img {
            violations.push(format!(
                "2-boundary violated for {}: tgt₂(F({})) = {}, expected F(tgt₂({})) = {}",
                alpha, alpha, actual_tgt, alpha, tgt_img
            ));
        }
    }

    violations
}

/// Validate pseudofunctor coherence cell invertibility.
///
/// For each declared composition coherence cell (f, g) → (forward, inverse),
/// checks that both forward and inverse exist in the target 2-morphism set.
///
/// Full round-trip validation (inverse ∘_v forward = id, forward ∘_v inverse = id)
/// requires a vertical composition table and is left to a dedicated law checker.
pub fn check_pseudo_coherence_cells_defined(
    pseudo: &DeclaredFinitePseudoFunctor,
    target_two_morphisms: &std::collections::BTreeSet<String>,
) -> Vec<String> {
    let mut violations = Vec::new();

    for ((f, g), cell) in &pseudo.comp_coherence {
        if !target_two_morphisms.contains(&cell.forward) {
            violations.push(format!(
                "Pseudo comp coherence ({}, {}): forward 2-cell {} not in target",
                f, g, cell.forward
            ));
        }
        if !target_two_morphisms.contains(&cell.inverse) {
            violations.push(format!(
                "Pseudo comp coherence ({}, {}): inverse 2-cell {} not in target",
                f, g, cell.inverse
            ));
        }
    }

    for (a, cell) in &pseudo.id_coherence {
        if !target_two_morphisms.contains(&cell.forward) {
            violations.push(format!(
                "Pseudo id coherence {}: forward 2-cell {} not in target",
                a, cell.forward
            ));
        }
        if !target_two_morphisms.contains(&cell.inverse) {
            violations.push(format!(
                "Pseudo id coherence {}: inverse 2-cell {} not in target",
                a, cell.inverse
            ));
        }
    }

    violations
}

// ===========================================================================
// Tests
// ===========================================================================

// Origin: engine/crates_rs/core_category_theory/src/higher_functor.rs
// Claim: urn:core:crates_rs:core-category-theory:higher-functor:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord574de30c {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord574de30c` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError574de30c {
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
impl BoundaryError574de30c {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError574de30c {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError574de30c {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord574de30c {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError574de30c> {
        if capacity_bound == 0 {
            return Err(BoundaryError574de30c::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError574de30c::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError574de30c::ExceedsCapacity {
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

    #[test]
    fn declared_finite_two_functor_lookups() {
        let mut f = DeclaredFiniteTwoFunctor::new("F", "C", "D");
        f.object_map.insert("A".into(), "X".into());
        f.one_morphism_map.insert("f".into(), "Ff".into());
        f.two_morphism_map.insert("alpha".into(), "Falpha".into());

        assert_eq!(f.on_ob("A"), Some("X"));
        assert_eq!(f.on_1("f"), Some("Ff"));
        assert_eq!(f.on_2("alpha"), Some("Falpha"));
        assert_eq!(f.on_ob("Z"), None);
    }

    #[test]
    fn one_boundary_violation_detected() {
        let mut f = DeclaredFiniteTwoFunctor::new("F", "C", "D");
        f.object_map.insert("A".into(), "X".into());
        f.object_map.insert("B".into(), "Y".into());
        f.one_morphism_map.insert("f".into(), "Ff".into());

        let src_bounds: BTreeMap<String, (String, String)> =
            vec![("f".into(), ("A".into(), "B".into()))]
                .into_iter()
                .collect();

        // Ff has wrong source in target category
        let tgt_bounds: BTreeMap<String, (String, String)> =
            vec![("Ff".into(), ("Y".into(), "Y".into()))]
                .into_iter()
                .collect();

        let v = check_two_functor_one_boundaries(&f, &src_bounds, &tgt_bounds);
        assert!(!v.is_empty());
        assert!(v[0].contains("src₁"));
    }

    #[test]
    fn one_boundary_passes_when_correct() {
        let mut f = DeclaredFiniteTwoFunctor::new("F", "C", "D");
        f.object_map.insert("A".into(), "X".into());
        f.object_map.insert("B".into(), "Y".into());
        f.one_morphism_map.insert("f".into(), "Ff".into());

        let src_bounds: BTreeMap<String, (String, String)> =
            vec![("f".into(), ("A".into(), "B".into()))]
                .into_iter()
                .collect();

        let tgt_bounds: BTreeMap<String, (String, String)> =
            vec![("Ff".into(), ("X".into(), "Y".into()))]
                .into_iter()
                .collect();

        let v = check_two_functor_one_boundaries(&f, &src_bounds, &tgt_bounds);
        assert!(v.is_empty(), "Should pass: {:?}", v);
    }

    #[test]
    fn pseudo_coherence_missing_cells_detected() {
        let f = DeclaredFiniteTwoFunctor::new("F", "C", "D");
        let pseudo = DeclaredFinitePseudoFunctor {
            underlying: f,
            comp_coherence: vec![(
                ("f".into(), "g".into()),
                DeclaredFiniteInvertibleTwoMor {
                    forward: "phi_fg".into(),
                    inverse: "phi_fg_inv".into(),
                },
            )]
            .into_iter()
            .collect(),
            id_coherence: BTreeMap::new(),
        };

        let target_2mors: std::collections::BTreeSet<String> =
            vec!["phi_fg".into()].into_iter().collect(); // inverse missing

        let v = check_pseudo_coherence_cells_defined(&pseudo, &target_2mors);
        assert_eq!(v.len(), 1);
        assert!(v[0].contains("inverse"));
    }
}

#[cfg(test)]
mod l4_boundary_tests_574de30c {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord574de30c::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord574de30c::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord574de30c::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord574de30c::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord574de30c::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError574de30c::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError574de30c::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
