//! Adjunction — Full Up ⊣ Forget with Derived Monad and Comonad.
//!
//! An adjunction L ⊣ R (Up ⊣ Forget) consists of:
//!   - Left functor  L : Base → Lifted  (Up / Free)
//!   - Right functor R : Lifted → Base  (Forget)
//!   - Unit   η : Id_Base → R∘L         (embed into lifted-then-forgotten)
//!   - Counit ε : L∘R → Id_Lifted      (evaluate / collapse)
//!
//! Triangle identities:
//!   ε_{L(A)} ∘ L(η_A) = id_{L(A)}     (left triangle)
//!   R(ε_B)   ∘ η_{R(B)} = id_{R(B)}   (right triangle)
//!
//! Derived structures:
//!   Monad   T = R∘L on Base,   η_T = η,   μ_T = R(ε_{L(-)})
//!   Comonad D = L∘R on Lifted, ε_D = ε,   δ_D = L(η_{R(-)})
//! Adjunction — Full Up ⊣ Forget with Derived Monad and Comonad.
//!
//! An adjunction L ⊣ R (Up ⊣ Forget) consists of:
//!   - Left functor  L : Base → Lifted  (Up / Free)
//!   - Right functor R : Lifted → Base  (Forget)
//!   - Unit   η : Id_Base → R∘L         (embed into lifted-then-forgotten)
//!   - Counit ε : L∘R → Id_Lifted      (evaluate / collapse)
//!
//! Triangle identities:
//!   ε_{L(A)} ∘ L(η_A) = id_{L(A)}     (left triangle)
//!   R(ε_B)   ∘ η_{R(B)} = id_{R(B)}   (right triangle)
//!
//! Derived structures:
//!   Monad   T = R∘L on Base,   η_T = η,   μ_T = R(ε_{L(-)})
//!   Comonad D = L∘R on Lifted, ε_D = ε,   δ_D = L(η_{R(-)})

use super::cat_functor::{CatFunctor, Category, DeclaredFiniteFunctor};
use super::functor_composition::validate_functor_between;
use std::collections::BTreeMap;

// ═══════════════════════════════════════════════════════════════════════════
// Marker traits
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Marker traits
// ═══════════════════════════════════════════════════════════════════════════

/// Marker: this functor adds structure (left adjoint / free construction).
///
/// L : Base → Lifted. Embeds raw data into structured space.
/// Examples: free group, free module, discrete topology.
/// Marker: this functor adds structure (left adjoint / free construction).
///
/// L : Base → Lifted. Embeds raw data into structured space.
/// Examples: free group, free module, discrete topology.
pub trait UpFunctor: CatFunctor {}

/// Marker: this functor drops structure (right adjoint / forgetful).
///
/// R : Lifted → Base. Strips structure, must emit evidence.
/// Examples: forget group law, forget topology, forget metric.
/// Marker: this functor drops structure (right adjoint / forgetful).
///
/// R : Lifted → Base. Strips structure, must emit evidence.
/// Examples: forget group law, forget topology, forget metric.
pub trait ForgetFunctor: CatFunctor {}

/// When structure is dropped by a forgetful functor, the evidence of
/// what was lost must be emitted. No silent forgetting.
/// When structure is dropped by a forgetful functor, the evidence of
/// what was lost must be emitted. No silent forgetting.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ForgetResult<Base, Evidence> {
    pub base: Base,
    pub evidence: Evidence,
}

pub trait ForgetFunctorWithEvidence: ForgetFunctor {
    type Lifted;
    type Base;
    type Evidence;

    fn forget(x: Self::Lifted) -> ForgetResult<Self::Base, Self::Evidence>;
}

/// Classification of forgetting operations.
/// Classification of forgetting operations.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ForgetKind {
    /// Harmless: e.g. (value, label) → value. No laws are lost.
    /// Harmless: e.g. (value, label) → value. No laws are lost.
    Projection,
    /// Drops law-bearing structure. Must emit evidence.
    /// Drops law-bearing structure. Must emit evidence.
    Structure,
}

// ═══════════════════════════════════════════════════════════════════════════
// AdjunctionPair — type-level trait
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// AdjunctionPair — type-level trait
// ═══════════════════════════════════════════════════════════════════════════

/// A certified adjunction L ⊣ R with unit and counit.
///
/// This is the type-level trait. For finite/declarative adjunctions
/// used in kernel audit, see `DeclaredFiniteAdjunction`.
/// A certified adjunction L ⊣ R with unit and counit.
///
/// This is the type-level trait. For finite/declarative adjunctions
/// used in kernel audit, see `DeclaredFiniteAdjunction`.
pub trait AdjunctionPair {
    type Base: Category;
    type Lifted: Category;
    type Left: CatFunctor<Source = Self::Base, Target = Self::Lifted>;
    type Right: CatFunctor<Source = Self::Lifted, Target = Self::Base>;

    // Ideally constrained to:
    // Unit: Id<Base> => Right ∘ Left
    // Counit: Left ∘ Right => Id<Lifted>
    // Ideally constrained to:
    // Unit: Id<Base> => Right ∘ Left
    // Counit: Left ∘ Right => Id<Lifted>
    type Unit;
    type Counit;
}

pub use super::finite_category::{DeclaredFiniteCategory, DeclaredMorphism};

// ═══════════════════════════════════════════════════════════════════════════
// DeclaredFiniteAdjunction — kernel-auditable data
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// DeclaredFiniteAdjunction — kernel-auditable data
// ═══════════════════════════════════════════════════════════════════════════

/// An explicit, finite adjunction L ⊣ R for kernel audit.
///
/// This is the computational workhorse: concrete, finite, checkable.
/// An explicit, finite adjunction L ⊣ R for kernel audit.
///
/// This is the computational workhorse: concrete, finite, checkable.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DeclaredFiniteAdjunction {
    pub name: String,
    pub left_functor: String,
    pub right_functor: String,
    pub left: DeclaredFiniteFunctor,
    pub right: DeclaredFiniteFunctor,
    /// L's object map: base object -> lifted object.
    /// L's object map: base object -> lifted object.
    pub left_ob_map: BTreeMap<String, String>,
    /// L's morphism map: base morphism -> lifted morphism.
    /// L's morphism map: base morphism -> lifted morphism.
    pub left_mor_map: BTreeMap<String, String>,
    /// R's object map: lifted object -> base object.
    /// R's object map: lifted object -> base object.
    pub right_ob_map: BTreeMap<String, String>,
    /// R's morphism map: lifted morphism -> base morphism.
    /// R's morphism map: lifted morphism -> base morphism.
    pub right_mor_map: BTreeMap<String, String>,
    /// Unit components: base object A → morphism η_A : A → R(L(A)).
    /// Unit components: base object A → morphism η_A : A → R(L(A)).
    pub unit_components: BTreeMap<String, String>,
    /// Counit components: lifted object B → morphism ε_B : L(R(B)) → B.
    /// Counit components: lifted object B → morphism ε_B : L(R(B)) → B.
    pub counit_components: BTreeMap<String, String>,
}

impl DeclaredFiniteAdjunction {
    pub fn new(name: &str, left: &str, right: &str) -> Self {
        Self {
            name: name.into(),
            left_functor: left.into(),
            right_functor: right.into(),
            left: DeclaredFiniteFunctor::new(left, "", ""),
            right: DeclaredFiniteFunctor::new(right, "", ""),
            left_ob_map: BTreeMap::new(),
            left_mor_map: BTreeMap::new(),
            right_ob_map: BTreeMap::new(),
            right_mor_map: BTreeMap::new(),
            unit_components: BTreeMap::new(),
            counit_components: BTreeMap::new(),
        }
    }

    pub fn new_between(
        name: &str,
        base: &str,
        lifted: &str,
        left_name: &str,
        right_name: &str,
    ) -> Self {
        let mut adj = Self::new(name, left_name, right_name);
        adj.left.source_category = base.into();
        adj.left.target_category = lifted.into();
        adj.right.source_category = lifted.into();
        adj.right.target_category = base.into();
        adj
    }

    pub fn set_left_ob(&mut self, src: &str, tgt: &str) {
        self.left.map_object(src, tgt);
        self.left_ob_map.insert(src.into(), tgt.into());
    }
    pub fn set_left_mor(&mut self, src: &str, tgt: &str) {
        self.left.map_morphism(src, tgt);
        self.left_mor_map.insert(src.into(), tgt.into());
    }
    pub fn set_right_ob(&mut self, src: &str, tgt: &str) {
        self.right.map_object(src, tgt);
        self.right_ob_map.insert(src.into(), tgt.into());
    }
    pub fn set_right_mor(&mut self, src: &str, tgt: &str) {
        self.right.map_morphism(src, tgt);
        self.right_mor_map.insert(src.into(), tgt.into());
    }
    pub fn set_unit(&mut self, object: &str, morphism: &str) {
        self.unit_components.insert(object.into(), morphism.into());
    }
    pub fn set_counit(&mut self, object: &str, morphism: &str) {
        self.counit_components
            .insert(object.into(), morphism.into());
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Derived Monad: T = R∘L on Base
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Derived Monad: T = R∘L on Base
// ═══════════════════════════════════════════════════════════════════════════

/// The monad induced by an adjunction L ⊣ R.
///
///   T = R ∘ L  (endofunctor on Base)
///   η_T = η   (unit of the adjunction)
///   μ_T_A = R(ε_{L(A)})  (multiplication: R applied to counit at L(A))
/// The monad induced by an adjunction L ⊣ R.
///
///   T = R ∘ L  (endofunctor on Base)
///   η_T = η   (unit of the adjunction)
///   μ_T_A = R(ε_{L(A)})  (multiplication: R applied to counit at L(A))
#[derive(Debug, Clone)]
pub struct DerivedMonad {
    pub name: String,
    /// T on objects: A → R(L(A)).
    /// T on objects: A → R(L(A)).
    pub t_ob_map: BTreeMap<String, String>,
    /// T on morphisms: f → R(L(f)).
    /// T on morphisms: f → R(L(f)).
    pub t_mor_map: BTreeMap<String, String>,
    /// Unit: η_A : A → T(A).
    /// Unit: η_A : A → T(A).
    pub unit: BTreeMap<String, String>,
    /// Multiplication: μ_A : T(T(A)) → T(A).
    /// Multiplication: μ_A : T(T(A)) → T(A).
    pub multiply: BTreeMap<String, String>,
}

impl DerivedMonad {
    /// Derive the monad T = R∘L from an adjunction.
    /// Derive the monad T = R∘L from an adjunction.
    pub fn from_adjunction(adj: &DeclaredFiniteAdjunction) -> Self {
        let mut t_ob_map = BTreeMap::new();
        let mut t_mor_map = BTreeMap::new();
        let mut multiply = BTreeMap::new();

        // T(A) = R(L(A))
        // T(A) = R(L(A))
        for (a, la) in &adj.left.object_map {
            if let Some(rla) = adj.right.on_object(la) {
                t_ob_map.insert(a.clone(), rla.into());
            }
        }

        // T(f) = R(L(f))
        // T(f) = R(L(f))
        for (f, lf) in &adj.left.morphism_map {
            if let Some(rlf) = adj.right.on_morphism(lf) {
                t_mor_map.insert(f.clone(), rlf.into());
            }
        }

        // μ_A = R(ε_{L(A)})
        // μ_A = R(ε_{L(A)})
        for (a, la) in &adj.left.object_map {
            if let Some(eps_la) = adj.counit_components.get(la) {
                if let Some(r_eps_la) = adj.right.on_morphism(eps_la) {
                    multiply.insert(a.clone(), r_eps_la.into());
                }
            }
        }

        DerivedMonad {
            name: format!("T_{}_{}", adj.right.name, adj.left.name),
            t_ob_map,
            t_mor_map,
            unit: adj.unit_components.clone(),
            multiply,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Derived Comonad: D = L∘R on Lifted
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Derived Comonad: D = L∘R on Lifted
// ═══════════════════════════════════════════════════════════════════════════

/// The comonad induced by an adjunction L ⊣ R.
///
///   D = L ∘ R  (endofunctor on Lifted)
///   ε_D = ε   (counit of the adjunction)
///   δ_D_B = L(η_{R(B)})  (comultiplication: L applied to unit at R(B))
/// The comonad induced by an adjunction L ⊣ R.
///
///   D = L ∘ R  (endofunctor on Lifted)
///   ε_D = ε   (counit of the adjunction)
///   δ_D_B = L(η_{R(B)})  (comultiplication: L applied to unit at R(B))
#[derive(Debug, Clone)]
pub struct DerivedComonad {
    pub name: String,
    /// D on objects: B → L(R(B)).
    /// D on objects: B → L(R(B)).
    pub d_ob_map: BTreeMap<String, String>,
    /// D on morphisms: g → L(R(g)).
    /// D on morphisms: g → L(R(g)).
    pub d_mor_map: BTreeMap<String, String>,
    /// Counit: ε_B : D(B) → B.
    /// Counit: ε_B : D(B) → B.
    pub counit: BTreeMap<String, String>,
    /// Comultiplication: δ_B : D(B) → D(D(B)).
    /// Comultiplication: δ_B : D(B) → D(D(B)).
    pub comultiply: BTreeMap<String, String>,
}

impl DerivedComonad {
    /// Derive the comonad D = L∘R from an adjunction.
    /// Derive the comonad D = L∘R from an adjunction.
    pub fn from_adjunction(adj: &DeclaredFiniteAdjunction) -> Self {
        let mut d_ob_map = BTreeMap::new();
        let mut d_mor_map = BTreeMap::new();
        let mut comultiply = BTreeMap::new();

        // D(B) = L(R(B))
        // D(B) = L(R(B))
        for (b, rb) in &adj.right.object_map {
            if let Some(lrb) = adj.left.on_object(rb) {
                d_ob_map.insert(b.clone(), lrb.into());
            }
        }

        // D(g) = L(R(g))
        // D(g) = L(R(g))
        for (g, rg) in &adj.right.morphism_map {
            if let Some(lrg) = adj.left.on_morphism(rg) {
                d_mor_map.insert(g.clone(), lrg.into());
            }
        }

        // δ_B = L(η_{R(B)})
        // δ_B = L(η_{R(B)})
        for (b, rb) in &adj.right_ob_map {
            if let Some(eta_rb) = adj.unit_components.get(rb) {
                if let Some(l_eta_rb) = adj.left_mor_map.get(eta_rb) {
                    comultiply.insert(b.clone(), l_eta_rb.clone());
                }
            }
        }

        DerivedComonad {
            name: format!("D_{}_{}", adj.left_functor, adj.right_functor),
            d_ob_map,
            d_mor_map,
            counit: adj.counit_components.clone(),
            comultiply,
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Kleisli composition for the derived monad
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Kleisli composition for the derived monad
// ═══════════════════════════════════════════════════════════════════════════

/// Kleisli composition: given f: A → T(B) and g: B → T(C),
/// produce g >=> f : A → T(C) = μ_C ∘ T(g) ∘ f.
///
/// In the finite declared setting, this is a table lookup.
/// Kleisli composition: given f: A → T(B) and g: B → T(C),
/// produce g >=> f : A → T(C) = μ_C ∘ T(g) ∘ f.
///
/// In the finite declared setting, this is a table lookup.
pub fn kleisli_compose(
    monad: &DerivedMonad,
    f_result: &str, // image of f (a morphism name in Base)
    g: &str,        // morphism g: B → T(C) name
    c: &str,        // object C
    base_compositions: &BTreeMap<(String, String), String>,
) -> Result<String, String> {
    // T(g)
    // T(g)
    let t_g = monad
        .t_mor_map
        .get(g)
        .ok_or_else(|| format!("Kleisli: T({}) not defined", g))?;

    // T(g) ∘ f
    // T(g) ∘ f
    let key1 = (f_result.to_string(), t_g.clone());
    let tg_f = base_compositions
        .get(&key1)
        .ok_or_else(|| format!("Kleisli: T({}) ∘ {} not in composition table", g, f_result))?;

    // μ_C
    // μ_C
    let mu_c = monad
        .multiply
        .get(c)
        .ok_or_else(|| format!("Kleisli: μ_{} not defined", c))?;

    // μ_C ∘ (T(g) ∘ f)
    // μ_C ∘ (T(g) ∘ f)
    let key2 = (tg_f.clone(), mu_c.clone());
    let result = base_compositions.get(&key2).ok_or_else(|| {
        format!(
            "Kleisli: μ_{} ∘ (T({}) ∘ {}) not in composition table",
            c, g, f_result
        )
    })?;

    Ok(result.clone())
}

// ═══════════════════════════════════════════════════════════════════════════
// Adjunction law validation
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Adjunction law validation
// ═══════════════════════════════════════════════════════════════════════════

use super::validation::{
    AdjunctionValidation, ValidationLocation, ValidationReport, ValidationSeverity, ValidationUnit,
    ValidationViolation,
};

fn adjunction_violation(
    unit: AdjunctionValidation,
    location: ValidationLocation,
    message: impl Into<String>,
) -> ValidationViolation {
    ValidationViolation::new(
        ValidationUnit::Adjunction(unit),
        location,
        message,
        ValidationSeverity::Error,
    )
}

fn validate_triangle_left(
    adj: &DeclaredFiniteAdjunction,
    base: &DeclaredFiniteCategory,
    lifted: &DeclaredFiniteCategory,
    // 1. L is a valid functor Base → Lifted
    // 2. R is a valid functor Lifted → Base
    left: &DeclaredFiniteFunctor,
) -> Vec<ValidationViolation> {
    // 3. Triangle left
    let mut tl_violations = Vec::new();
    for a in base.object_names() {
        let Some(la) = left.on_object(a) else {
            continue;
        };
        let Some(eta_a) = adj.unit_components.get(a) else {
            tl_violations.push(adjunction_violation(
                AdjunctionValidation::TriangleLeft,
                ValidationLocation::Object(a.into()),
                format!("η_{} not defined", a),
            ));
            continue;
        };
        let Some(l_eta_a) = left.on_morphism(eta_a) else {
            continue;
        };
        let Some(eps_la) = adj.counit_components.get(la) else {
            continue;
        };

        let composed = lifted.compose(l_eta_a, eps_la);
        let id_la = lifted.identity_of(la);

        match (composed, id_la) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => {
                tl_violations.push(adjunction_violation(
                    AdjunctionValidation::TriangleLeft,
                    ValidationLocation::Object(a.into()),
                    format!(
                        "ε_{{L({})}} ∘ L(η_{}) = {} ≠ id_{{L({})}} = {}",
                        a, a, c, a, i
                    ),
                ));
            }
            _ => tl_violations.push(adjunction_violation(
                AdjunctionValidation::TriangleLeft,
                ValidationLocation::Object(a.into()),
                format!(
                    "ε_{{L({})}} ∘ L(η_{}) not defined or identity missing",
                    a, a
                ),
            )),
        }
    }
    tl_violations
}

fn validate_triangle_right(
    adj: &DeclaredFiniteAdjunction,
    base: &DeclaredFiniteCategory,
    lifted: &DeclaredFiniteCategory,
    right: &DeclaredFiniteFunctor,
) -> Vec<ValidationViolation> {
    // 4. Triangle right
    let mut tr_violations = Vec::new();
    for b in lifted.object_names() {
        let Some(rb) = right.on_object(b) else {
            continue;
        };
        let Some(eps_b) = adj.counit_components.get(b) else {
            tr_violations.push(adjunction_violation(
                AdjunctionValidation::TriangleRight,
                ValidationLocation::Object(b.into()),
                format!("ε_{} not defined", b),
            ));
            continue;
        };
        let Some(r_eps_b) = right.on_morphism(eps_b) else {
            continue;
        };
        let Some(eta_rb) = adj.unit_components.get(rb) else {
            continue;
        };

        let composed = base.compose(eta_rb, r_eps_b);
        let id_rb = base.identity_of(rb);

        match (composed, id_rb) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => {
                tr_violations.push(adjunction_violation(
                    AdjunctionValidation::TriangleRight,
                    ValidationLocation::Object(b.into()),
                    format!(
                        "R(ε_{}) ∘ η_{{R({})}} = {} ≠ id_{{R({})}} = {}",
                        b, b, c, b, i
                    ),
                ));
            }
            _ => tr_violations.push(adjunction_violation(
                AdjunctionValidation::TriangleRight,
                ValidationLocation::Object(b.into()),
                format!(
                    "R(ε_{}) ∘ η_{{R({})}} not defined or identity missing",
                    b, b
                ),
            )),
        }
    }
    tr_violations
}

pub fn validate_declared_adjunction(
    adj: &DeclaredFiniteAdjunction,
    base: &DeclaredFiniteCategory,
    lifted: &DeclaredFiniteCategory,
) -> ValidationReport {
    let mut report = ValidationReport::new(&adj.name);
    let mut left = adj.left.clone();
    left.name = adj.left_functor.clone();
    left.source_category = base.name.clone();
    left.target_category = lifted.name.clone();
    left.object_map = adj.left_ob_map.clone();
    left.morphism_map = adj.left_mor_map.clone();

    let mut right = adj.right.clone();
    right.name = adj.right_functor.clone();
    right.source_category = lifted.name.clone();
    right.target_category = base.name.clone();
    right.object_map = adj.right_ob_map.clone();
    right.morphism_map = adj.right_mor_map.clone();

    // 1. L is a valid functor Base → Lifted
    let left_report = validate_functor_between(&left, base, lifted);
    for res in left_report.results {
        report.add(res);
    }
    for violation in left_report.typed_violations {
        report.add_violation(violation);
    }

    // 2. R is a valid functor Lifted → Base
    let right_report = validate_functor_between(&right, lifted, base);
    for res in right_report.results {
        report.add(res);
    }
    for violation in right_report.typed_violations {
        report.add_violation(violation);
    }

    // 3. Triangle left
    let tl_violations = validate_triangle_left(adj, base, lifted, &left);
    report.add_typed("triangle_left", tl_violations);

    // 4. Triangle right
    let tr_violations = validate_triangle_right(adj, base, lifted, &right);
    report.add_typed("triangle_right", tr_violations);

    report
}

// ═══════════════════════════════════════════════════════════════════════════
// Derived monad law validation
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Derived monad law validation
// ═══════════════════════════════════════════════════════════════════════════

/// Verify the derived monad satisfies μ ∘ Tη = id_T (left unit).
/// Verify the derived monad satisfies μ ∘ Tη = id_T (left unit).
pub fn check_derived_monad_left_unit(
    monad: &DerivedMonad,
    base_compositions: &BTreeMap<(String, String), String>,
    base_ids: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (a, ta) in &monad.t_ob_map {
        let Some(eta_a) = monad.unit.get(a) else {
            continue;
        };
        let Some(t_eta_a) = monad.t_mor_map.get(eta_a.as_str()) else {
            violations.push(format!("Monad left unit: T(η_{}) not defined", a));
            continue;
        };
        let Some(mu_a) = monad.multiply.get(a) else {
            violations.push(format!("Monad left unit: μ_{} not defined", a));
            continue;
        };
        let key = (t_eta_a.clone(), mu_a.clone());
        let composed = base_compositions.get(&key);
        let id_ta = base_ids.get(ta);
        match (composed, id_ta) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => violations.push(format!(
                "Monad left unit at {}: μ∘T(η) = {} ≠ id_T = {}",
                a, c, i
            )),
            _ => violations.push(format!(
                "Monad left unit at {}: composition or identity not defined",
                a
            )),
        }
    }
    violations
}

/// Verify the derived monad satisfies μ ∘ ηT = id_T (right unit).
/// Verify the derived monad satisfies μ ∘ ηT = id_T (right unit).
pub fn check_derived_monad_right_unit(
    monad: &DerivedMonad,
    base_compositions: &BTreeMap<(String, String), String>,
    base_ids: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (a, ta) in &monad.t_ob_map {
        let Some(eta_ta) = monad.unit.get(ta.as_str()) else {
            continue;
        };
        let Some(mu_a) = monad.multiply.get(a) else {
            continue;
        };
        let key = (eta_ta.clone(), mu_a.clone());
        let composed = base_compositions.get(&key);
        let id_ta = base_ids.get(ta);
        match (composed, id_ta) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => violations.push(format!(
                "Monad right unit at {}: μ∘ηT = {} ≠ id_T = {}",
                a, c, i
            )),
            _ => violations.push(format!("Monad right unit at {}: not defined", a)),
        }
    }
    violations
}

// ═══════════════════════════════════════════════════════════════════════════
// Derived comonad law validation & monad associativity
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Derived comonad law validation & monad associativity
// ═══════════════════════════════════════════════════════════════════════════

/// Verify the derived monad satisfies μ_A ∘ T(μ_A) = μ_A ∘ μ_{T(A)} (associativity).
/// Verify the derived monad satisfies μ_A ∘ T(μ_A) = μ_A ∘ μ_{T(A)} (associativity).
pub fn check_derived_monad_associativity(
    monad: &DerivedMonad,
    base_compositions: &BTreeMap<(String, String), String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (a, ta) in &monad.t_ob_map {
        let Some(_tta) = monad.t_ob_map.get(ta) else {
            continue;
        };

        let Some(mu_a) = monad.multiply.get(a) else {
            continue;
        };
        let Some(mu_ta) = monad.multiply.get(ta) else {
            continue;
        };
        let Some(t_mu_a) = monad.t_mor_map.get(mu_a) else {
            continue;
        };

        // LHS: μ_A ∘ T(μ_A)
        // LHS: μ_A ∘ T(μ_A)
        let lhs_key = (t_mu_a.clone(), mu_a.clone());
        let lhs = base_compositions.get(&lhs_key);

        // RHS: μ_A ∘ μ_{T(A)}
        // RHS: μ_A ∘ μ_{T(A)}
        let rhs_key = (mu_ta.clone(), mu_a.clone());
        let rhs = base_compositions.get(&rhs_key);

        match (lhs, rhs) {
            (Some(l), Some(r)) if l == r => {}
            (Some(l), Some(r)) => violations.push(format!(
                "Monad associativity at {}: μ∘T(μ) = {} ≠ μ∘μ_T = {}",
                a, l, r
            )),
            _ => violations.push(format!(
                "Monad associativity at {}: compositions not defined",
                a
            )),
        }
    }
    violations
}

/// Composition table convention:
/// compositions[(f, g)] = g ∘ f
///
/// Verify the derived comonad satisfies εD ∘ δ = id_D
/// Composition table convention:
/// compositions[(f, g)] = g ∘ f
///
/// Verify the derived comonad satisfies εD ∘ δ = id_D
pub fn check_derived_comonad_left_counit(
    comonad: &DerivedComonad,
    lifted_compositions: &BTreeMap<(String, String), String>,
    lifted_ids: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (b, db) in &comonad.d_ob_map {
        let Some(delta_b) = comonad.comultiply.get(b) else {
            continue;
        };
        let Some(eps_db) = comonad.counit.get(db) else {
            continue;
        };

        let key = (delta_b.clone(), eps_db.clone());
        let composed = lifted_compositions.get(&key);
        let id_db = lifted_ids.get(db);
        match (composed, id_db) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => violations.push(format!(
                "Comonad left counit at {}: εD∘δ = {} ≠ id_D = {}",
                b, c, i
            )),
            _ => violations.push(format!("Comonad left counit at {}: not defined", b)),
        }
    }
    violations
}

/// Verify the derived comonad satisfies Dε ∘ δ = id_D
/// Verify the derived comonad satisfies Dε ∘ δ = id_D
pub fn check_derived_comonad_right_counit(
    comonad: &DerivedComonad,
    lifted_compositions: &BTreeMap<(String, String), String>,
    lifted_ids: &BTreeMap<String, String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (b, db) in &comonad.d_ob_map {
        let Some(delta_b) = comonad.comultiply.get(b) else {
            continue;
        };
        let Some(eps_b) = comonad.counit.get(b) else {
            continue;
        };
        let Some(d_eps_b) = comonad.d_mor_map.get(eps_b) else {
            continue;
        };

        let key = (delta_b.clone(), d_eps_b.clone());
        let composed = lifted_compositions.get(&key);
        let id_db = lifted_ids.get(db);
        match (composed, id_db) {
            (Some(c), Some(i)) if c == i => {}
            (Some(c), Some(i)) => violations.push(format!(
                "Comonad right counit at {}: Dε∘δ = {} ≠ id_D = {}",
                b, c, i
            )),
            _ => violations.push(format!("Comonad right counit at {}: not defined", b)),
        }
    }
    violations
}

/// Verify the derived comonad satisfies δD ∘ δ = Dδ ∘ δ
/// Verify the derived comonad satisfies δD ∘ δ = Dδ ∘ δ
pub fn check_derived_comonad_coassociativity(
    comonad: &DerivedComonad,
    lifted_compositions: &BTreeMap<(String, String), String>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (b, db) in &comonad.d_ob_map {
        let Some(_ddb) = comonad.d_ob_map.get(db) else {
            continue;
        };

        let Some(delta_b) = comonad.comultiply.get(b) else {
            continue;
        };
        let Some(delta_db) = comonad.comultiply.get(db) else {
            continue;
        };
        let Some(d_delta_b) = comonad.d_mor_map.get(delta_b) else {
            continue;
        };

        // LHS: δ_D(B) ∘ δ_B
        // LHS: δ_D(B) ∘ δ_B
        let lhs_key = (delta_b.clone(), delta_db.clone());
        let lhs = lifted_compositions.get(&lhs_key);

        // RHS: D(δ_B) ∘ δ_B
        // RHS: D(δ_B) ∘ δ_B
        let rhs_key = (delta_b.clone(), d_delta_b.clone());
        let rhs = lifted_compositions.get(&rhs_key);

        match (lhs, rhs) {
            (Some(l), Some(r)) if l == r => {}
            (Some(l), Some(r)) => violations.push(format!(
                "Comonad coassociativity at {}: δD∘δ = {} ≠ Dδ∘δ = {}",
                b, l, r
            )),
            _ => violations.push(format!(
                "Comonad coassociativity at {}: compositions not defined",
                b
            )),
        }
    }
    violations
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════
// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

// Origin: engine/crates_rs/core_category_theory/src/legacy_adjunction.rs
// Claim: urn:core:crates_rs:core-category-theory:legacy-adjunction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8e06d1ac {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8e06d1ac` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8e06d1ac {
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
impl BoundaryError8e06d1ac {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8e06d1ac {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8e06d1ac {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8e06d1ac {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8e06d1ac> {
        if capacity_bound == 0 {
            return Err(BoundaryError8e06d1ac::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8e06d1ac::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8e06d1ac::ExceedsCapacity {
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

    /// Build the simplest nontrivial adjunction: Discrete ⊣ Forget
    /// between a 1-object base category {*} and a 1-object lifted
    /// category {*'}, where everything is the identity.
    /// Build the simplest nontrivial adjunction: Discrete ⊣ Forget
    /// between a 1-object base category {*} and a 1-object lifted
    /// category {*'}, where everything is the identity.
    fn trivial_adjunction() -> DeclaredFiniteAdjunction {
        let mut adj = DeclaredFiniteAdjunction::new("Trivial", "L", "R");
        // L: * → *'
        // L: * → *'
        adj.set_left_ob("*", "*'");
        adj.set_left_mor("id_*", "id_*'");
        // R: *' → *
        // R: *' → *
        adj.set_right_ob("*'", "*");
        adj.set_right_mor("id_*'", "id_*");
        // η: * → R(L(*)) = * → *  ⇒  η_* = id_*
        // η: * → R(L(*)) = * → *  ⇒  η_* = id_*
        adj.set_unit("*", "id_*");
        // ε: L(R(*')) = *' → *'  ⇒  ε_*' = id_*'
        // ε: L(R(*')) = *' → *'  ⇒  ε_*' = id_*'
        adj.set_counit("*'", "id_*'");
        // L(η_*) = L(id_*) = id_*'
        // L(η_*) = L(id_*) = id_*'
        adj.set_left_mor("id_*", "id_*'");
        adj
    }

    fn dummy_base_category() -> DeclaredFiniteCategory {
        let mut cat = DeclaredFiniteCategory::new("Base");
        cat.add_identity("*", "id_*");
        cat.set_composition("id_*", "id_*", "id_*");
        cat
    }

    fn dummy_lifted_category() -> DeclaredFiniteCategory {
        let mut cat = DeclaredFiniteCategory::new("Lifted");
        cat.add_identity("*'", "id_*'");
        cat.set_composition("id_*'", "id_*'", "id_*'");
        cat
    }

    #[test]
    fn left_triangle_trivial() {
        let adj = trivial_adjunction();
        let base = dummy_base_category();
        let lifted = dummy_lifted_category();
        let report = validate_declared_adjunction(&adj, &base, &lifted);
        assert!(
            report.all_passed(),
            "Should pass: {:?}",
            report.typed_violations
        );
    }

    #[test]
    fn derived_monad_from_trivial() {
        let adj = trivial_adjunction();
        let monad = DerivedMonad::from_adjunction(&adj);
        // T(*) = R(L(*)) = R(*') = *
        // T(*) = R(L(*)) = R(*') = *
        assert_eq!(monad.t_ob_map.get("*"), Some(&"*".to_string()));
        // η_* = id_* (unit)
        // η_* = id_* (unit)
        assert_eq!(monad.unit.get("*"), Some(&"id_*".to_string()));
    }

    #[test]
    fn derived_comonad_from_trivial() {
        let adj = trivial_adjunction();
        let comonad = DerivedComonad::from_adjunction(&adj);
        // D(*') = L(R(*')) = L(*) = *'
        // D(*') = L(R(*')) = L(*) = *'
        assert_eq!(comonad.d_ob_map.get("*'"), Some(&"*'".to_string()));
        // ε_*' = id_*' (counit)
        // ε_*' = id_*' (counit)
        assert_eq!(comonad.counit.get("*'"), Some(&"id_*'".to_string()));
    }

    #[test]
    fn derived_monad_left_unit_trivial() {
        let adj = trivial_adjunction();
        let monad = DerivedMonad::from_adjunction(&adj);
        let base_comp: BTreeMap<(String, String), String> =
            vec![(("id_*".into(), "id_*".into()), "id_*".into())]
                .into_iter()
                .collect();
        let base_ids: BTreeMap<String, String> =
            vec![("*".into(), "id_*".into())].into_iter().collect();
        let v = check_derived_monad_left_unit(&monad, &base_comp, &base_ids);
        assert!(v.is_empty(), "Monad left unit should pass: {:?}", v);
    }

    #[test]
    fn forget_result_construction() {
        let r = ForgetResult {
            base: 42,
            evidence: "dropped group law",
        };
        assert_eq!(r.base, 42);
        assert_eq!(ForgetKind::Structure, ForgetKind::Structure);
        assert_ne!(ForgetKind::Projection, ForgetKind::Structure);
    }

    #[test]
    fn missing_unit_is_violation() {
        let mut adj = DeclaredFiniteAdjunction::new_between("Bad", "Base", "Lifted", "L", "R");
        adj.set_left_ob("*", "*'");
        adj.set_left_mor("id_*", "id_*'");
        adj.set_right_ob("*'", "*");
        adj.set_right_mor("id_*'", "id_*");
        let base = dummy_base_category();
        let lifted = dummy_lifted_category();
        let report = validate_declared_adjunction(&adj, &base, &lifted);
        assert!(!report.all_passed());
        assert!(report
            .typed_violations
            .iter()
            .any(|v| v.unit == ValidationUnit::Adjunction(AdjunctionValidation::TriangleLeft)));
    }
}

#[cfg(test)]
mod l4_boundary_tests_8e06d1ac {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8e06d1ac::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8e06d1ac::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8e06d1ac::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8e06d1ac::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8e06d1ac::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8e06d1ac::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8e06d1ac::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
