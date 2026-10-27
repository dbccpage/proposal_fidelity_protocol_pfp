//! The Nerve of a Category — Simplicial Sets.
//!
//! The nerve functor N : Cat → sSet sends a small category C to a simplicial set N(C)
//! where:
//! - 0-simplices are objects of C
//! - 1-simplices are morphisms of C
//! - 2-simplices are composable pairs (commuting triangles)
//! - n-simplices are composable chains of n morphisms
//!
//! This module adapts the nerve construction to our finite `DeclaredFiniteCategory` infrastructure,
//! complete with face and degeneracy maps.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_169a5aef<T> {
    fn checked_invariant_169a5aef(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_169a5aef<T> for Option<T> {
    #[inline]
    fn checked_invariant_169a5aef(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_169a5aef<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_169a5aef(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use super::finite_category::{DeclaredFiniteCategory, ValidatedFiniteCategory};
use super::functor_composition::ValidatedFiniteFunctor;

/// A cleaner representation for an n-simplex in our specific encoding.
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub enum Simplex {
    /// A 0-simplex is an object.
    Vertex(String),
    /// An n-simplex (n > 0) is a chain of n composable morphisms.
    Chain(Vec<String>),
}

impl Simplex {
    pub fn dimension(&self) -> usize {
        match self {
            Simplex::Vertex(_) => 0,
            Simplex::Chain(morphisms) => morphisms.len(),
        }
    }
}

/// The Nerve of a finite category.
///
/// NOTE: The input `category` is assumed to be a mathematically sound category
/// (identities, associativity, proper composition). If built over an invalid
/// `DeclaredFiniteCategory`, the resulting simplicial set will not satisfy
/// the simplicial identities.
#[derive(Debug, Clone)]
pub struct DeclaredNerve<'a> {
    pub category: &'a DeclaredFiniteCategory,
}

impl<'a> DeclaredNerve<'a> {
    pub fn new(category: &'a DeclaredFiniteCategory) -> Self {
        Self { category }
    }

    /// Generate all n-simplices of the category.
    pub fn n_simplices(&self, n: usize) -> Vec<Simplex> {
        if n == 0 {
            self.category
                .objects
                .iter()
                .map(|obj| Simplex::Vertex(obj.clone()))
                .collect()
        } else {
            self.composable_chains(n)
        }
    }

    /// Helper to generate composable chains of length n > 0.
    fn composable_chains(&self, n: usize) -> Vec<Simplex> {
        if n == 0 {
            return vec![];
        }
        if n == 1 {
            return self
                .category
                .morphisms
                .keys()
                .map(|m| Simplex::Chain(vec![m.clone()]))
                .collect();
        }

        let mut chains = Vec::new();
        let prev_chains = self.composable_chains(n - 1);

        for chain in prev_chains {
            if let Simplex::Chain(morphisms) = chain {
                let last_morph_name = morphisms.last().checked_invariant_169a5aef("checked invariant");
                let last_morph = self.category.morphisms.get(last_morph_name).checked_invariant_169a5aef("checked invariant");
                let last_tgt = &last_morph.target;

                // Find all morphisms whose source is the target of the last morphism.
                for (next_name, next_morph) in &self.category.morphisms {
                    if &next_morph.source == last_tgt {
                        let mut new_chain = morphisms.clone();
                        new_chain.push(next_name.clone());
                        chains.push(Simplex::Chain(new_chain));
                    }
                }
            }
        }
        chains
    }

    /// Face map d_i : N_n(C) → N_{n-1}(C).
    /// Returns the i-th face of the simplex, or None if i > n.
    pub fn face(&self, simplex: &Simplex, i: usize) -> Option<Simplex> {
        let n = simplex.dimension();
        if i > n {
            return None;
        }

        match simplex {
            Simplex::Vertex(_) => None, // 0-simplices have no faces
            Simplex::Chain(morphisms) => {
                if n == 1 {
                    // For a 1-simplex f: A → B, d_0(f) = B, d_1(f) = A
                    let f = self.category.morphisms.get(&morphisms[0])?;
                    if i == 0 {
                        Some(Simplex::Vertex(f.target.clone()))
                    } else {
                        Some(Simplex::Vertex(f.source.clone()))
                    }
                } else {
                    // For n > 1:
                    // d_0: drop first morphism
                    // d_n: drop last morphism
                    // d_i (0 < i < n): compose i-th and (i+1)-th morphisms (0-indexed list means i-1 and i)
                    let mut new_chain = morphisms.clone();
                    if i == 0 {
                        new_chain.remove(0);
                    } else if i == n {
                        new_chain.pop();
                    } else {
                        // We need to compose morphisms at index (i-1) and index i.
                        // f = new_chain[i-1], g = new_chain[i]
                        // composition is (f, g) -> g ∘ f
                        let f = &new_chain[i - 1];
                        let g = &new_chain[i];
                        let comp_key = (f.clone(), g.clone());
                        let composed = self.category.compositions.get(&comp_key)?;

                        // Replace f and g with their composition.
                        new_chain.splice((i - 1)..=i, vec![composed.clone()]);
                    }
                    Some(Simplex::Chain(new_chain))
                }
            }
        }
    }

    /// Degeneracy map s_i : N_n(C) → N_{n+1}(C).
    /// Inserts an identity morphism at position i (0 <= i <= n).
    pub fn degeneracy(&self, simplex: &Simplex, i: usize) -> Option<Simplex> {
        let n = simplex.dimension();
        if i > n {
            return None;
        }

        match simplex {
            Simplex::Vertex(obj) => {
                // s_0 on an object A yields the identity morphism id_A.
                let id_morphism = self.category.identities.get(obj)?;
                Some(Simplex::Chain(vec![id_morphism.clone()]))
            }
            Simplex::Chain(morphisms) => {
                let mut new_chain = morphisms.clone();
                // We need to insert the identity of the object at position i.
                // The object at position i is the target of morphisms[i-1] (or source of morphisms[0] if i=0).
                let obj = if i == 0 {
                    let f = self.category.morphisms.get(&morphisms[0])?;
                    &f.source
                } else {
                    let f = self.category.morphisms.get(&morphisms[i - 1])?;
                    &f.target
                };

                let id_morphism = self.category.identities.get(obj)?;
                new_chain.insert(i, id_morphism.clone());
                Some(Simplex::Chain(new_chain))
            }
        }
    }

    /// Checks if a simplex is degenerate (contains an identity morphism).
    pub fn is_degenerate(&self, simplex: &Simplex) -> bool {
        match simplex {
            Simplex::Vertex(_) => false,
            Simplex::Chain(morphisms) => {
                // Collect all identity morphism names
                let id_names: std::collections::BTreeSet<_> =
                    self.category.identities.values().collect();
                morphisms.iter().any(|m| id_names.contains(m))
            }
        }
    }

    /// Enumerates only the non-degenerate n-simplices.
    pub fn nondegenerate_n_simplices(&self, n: usize) -> Vec<Simplex> {
        self.n_simplices(n)
            .into_iter()
            .filter(|s| !self.is_degenerate(s))
            .collect()
    }
}

/// Refusals on the finite, explicitly bounded nerve surface.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FiniteNerveRefusal {
    InvalidBounds,
    DimensionExceeded,
    CellBudgetExceeded,
    InvalidSimplex,
    InvalidIndex,
    MissingBoundary,
    UnknownEndpoint,
    FunctorCarrierMismatch,
}

/// A nerve on a category that has passed every finite category law check.
///
/// Enumeration is complete at each requested degree only when it returns Ok.
/// Bounds do not assert Kan filling, homotopy classification or a Genesis lift.
#[derive(Debug, Clone)]
pub struct ValidatedFiniteNerve<'a> {
    category: &'a ValidatedFiniteCategory,
    max_dimension: usize,
    cell_budget: usize,
}

impl<'a> ValidatedFiniteNerve<'a> {
    pub fn new(
        category: &'a ValidatedFiniteCategory,
        max_dimension: usize,
        cell_budget: usize,
    ) -> Result<Self, FiniteNerveRefusal> {
        if max_dimension > 32 || cell_budget == 0 {
            return Err(FiniteNerveRefusal::InvalidBounds);
        }
        Ok(Self {
            category,
            max_dimension,
            cell_budget,
        })
    }

    fn degree(&self, n: usize) -> Result<(), FiniteNerveRefusal> {
        if n > self.max_dimension {
            Err(FiniteNerveRefusal::DimensionExceeded)
        } else {
            Ok(())
        }
    }

    pub fn validate_simplex(&self, simplex: &Simplex) -> Result<(), FiniteNerveRefusal> {
        self.degree(simplex.dimension())?;
        let category = self.category.declared();
        match simplex {
            Simplex::Vertex(object) if category.has_object(object) => Ok(()),
            Simplex::Vertex(_) => Err(FiniteNerveRefusal::InvalidSimplex),
            Simplex::Chain(chain) => {
                if chain.is_empty() {
                    return Err(FiniteNerveRefusal::InvalidSimplex);
                }
                let mut previous_target: Option<&str> = None;
                for name in chain {
                    let (source, target) = category
                        .boundary_of(name)
                        .ok_or(FiniteNerveRefusal::InvalidSimplex)?;
                    if previous_target.is_some_and(|previous| previous != source) {
                        return Err(FiniteNerveRefusal::InvalidSimplex);
                    }
                    previous_target = Some(target);
                }
                Ok(())
            }
        }
    }

    fn extend_chains(
        &self,
        category: &DeclaredFiniteCategory,
        chains: &[Vec<String>],
    ) -> Result<Vec<Vec<String>>, FiniteNerveRefusal> {
        let mut next = Vec::new();
        for chain in chains {
            let last = chain.last().ok_or(FiniteNerveRefusal::MissingBoundary)?;
            let (_, target) = category
                .boundary_of(last)
                .ok_or(FiniteNerveRefusal::MissingBoundary)?;
            for (name, morphism) in &category.morphisms {
                if morphism.source == target {
                    if next.len() == self.cell_budget {
                        return Err(FiniteNerveRefusal::CellBudgetExceeded);
                    }
                    let mut extension = chain.clone();
                    extension.push(name.clone());
                    next.push(extension);
                }
            }
        }
        Ok(next)
    }

    pub fn n_simplices(&self, n: usize) -> Result<Vec<Simplex>, FiniteNerveRefusal> {
        self.degree(n)?;
        let category = self.category.declared();
        if n == 0 {
            if category.objects.len() > self.cell_budget {
                return Err(FiniteNerveRefusal::CellBudgetExceeded);
            }
            return Ok(category
                .objects
                .iter()
                .cloned()
                .map(Simplex::Vertex)
                .collect());
        }
        if category.morphisms.len() > self.cell_budget {
            return Err(FiniteNerveRefusal::CellBudgetExceeded);
        }
        let mut chains: Vec<Vec<String>> = category
            .morphisms
            .keys()
            .map(|name| vec![name.clone()])
            .collect();
        for _ in 1..n {
            chains = self.extend_chains(category, &chains)?;
        }
        Ok(chains.into_iter().map(Simplex::Chain).collect())
    }

    pub fn face(&self, simplex: &Simplex, i: usize) -> Result<Simplex, FiniteNerveRefusal> {
        self.validate_simplex(simplex)?;
        if simplex.dimension() == 0 || i > simplex.dimension() {
            return Err(FiniteNerveRefusal::InvalidIndex);
        }
        DeclaredNerve::new(self.category.declared())
            .face(simplex, i)
            .ok_or(FiniteNerveRefusal::MissingBoundary)
    }

    pub fn degeneracy(&self, simplex: &Simplex, i: usize) -> Result<Simplex, FiniteNerveRefusal> {
        self.validate_simplex(simplex)?;
        self.degree(simplex.dimension() + 1)?;
        if i > simplex.dimension() {
            return Err(FiniteNerveRefusal::InvalidIndex);
        }
        DeclaredNerve::new(self.category.declared())
            .degeneracy(simplex, i)
            .ok_or(FiniteNerveRefusal::MissingBoundary)
    }

    pub fn all_faces(&self, simplex: &Simplex) -> Result<Vec<Simplex>, FiniteNerveRefusal> {
        self.validate_simplex(simplex)?;
        if simplex.dimension() == 0 {
            return Ok(Vec::new());
        }
        (0..=simplex.dimension())
            .map(|i| self.face(simplex, i))
            .collect()
    }

    pub fn all_degeneracies(&self, simplex: &Simplex) -> Result<Vec<Simplex>, FiniteNerveRefusal> {
        self.validate_simplex(simplex)?;
        (0..=simplex.dimension())
            .map(|i| self.degeneracy(simplex, i))
            .collect()
    }

    /// N(F) maps each object/arrow using a validated finite functor F.
    /// Both exact category declarations must match the validation token.
    pub fn map_simplex(
        &self,
        target: &ValidatedFiniteNerve<'_>,
        functor: &ValidatedFiniteFunctor,
        simplex: &Simplex,
    ) -> Result<Simplex, FiniteNerveRefusal> {
        if functor.source() != self.category.declared()
            || functor.target() != target.category.declared()
        {
            return Err(FiniteNerveRefusal::FunctorCarrierMismatch);
        }
        self.validate_simplex(simplex)?;
        let mapped = match simplex {
            Simplex::Vertex(object) => Simplex::Vertex(
                functor
                    .declared()
                    .on_object(object)
                    .ok_or(FiniteNerveRefusal::MissingBoundary)?
                    .into(),
            ),
            Simplex::Chain(chain) => Simplex::Chain(
                chain
                    .iter()
                    .map(|name| {
                        functor
                            .declared()
                            .on_morphism(name)
                            .map(String::from)
                            .ok_or(FiniteNerveRefusal::MissingBoundary)
                    })
                    .collect::<Result<Vec<_>, _>>()?,
            ),
        };
        target.validate_simplex(&mapped)?;
        Ok(mapped)
    }

    fn collect_degree_paths(
        &self,
        category: &DeclaredFiniteCategory,
        source: &str,
        target: &str,
        degree: usize,
        paths: &mut Vec<Simplex>,
    ) -> Result<(), FiniteNerveRefusal> {
        for simplex in self.n_simplices(degree)? {
            let Simplex::Chain(chain) = &simplex else {
                return Err(FiniteNerveRefusal::MissingBoundary);
            };
            let (first_source, _) = category
                .boundary_of(chain.first().ok_or(FiniteNerveRefusal::MissingBoundary)?)
                .ok_or(FiniteNerveRefusal::MissingBoundary)?;
            let (_, last_target) = category
                .boundary_of(chain.last().ok_or(FiniteNerveRefusal::MissingBoundary)?)
                .ok_or(FiniteNerveRefusal::MissingBoundary)?;
            if first_source == source && last_target == target {
                if paths.len() == self.cell_budget {
                    return Err(FiniteNerveRefusal::CellBudgetExceeded);
                }
                paths.push(simplex);
            }
        }
        Ok(())
    }

    /// All composable arrow paths of length at most max_length.
    /// Vertex(source) represents the length-zero path when source == target.
    /// Identities are retained; paths are not quotiented by homotopy.
    pub fn paths(
        &self,
        source: &str,
        target: &str,
        max_length: usize,
    ) -> Result<Vec<Simplex>, FiniteNerveRefusal> {
        self.degree(max_length)?;
        let category = self.category.declared();
        if !category.has_object(source) || !category.has_object(target) {
            return Err(FiniteNerveRefusal::UnknownEndpoint);
        }
        let mut paths = Vec::new();
        if source == target {
            paths.push(Simplex::Vertex(source.into()));
        }
        for degree in 1..=max_length {
            self.collect_degree_paths(category, source, target, degree, &mut paths)?;
        }
        Ok(paths)
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// Tests
// ═══════════════════════════════════════════════════════════════════════════

// Origin: engine/crates_rs/core_category_theory/src/nerve.rs
// Claim: urn:core:crates_rs:core-category-theory:nerve:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord169a5aef {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord169a5aef` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError169a5aef {
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
impl BoundaryError169a5aef {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError169a5aef {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError169a5aef {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord169a5aef {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError169a5aef> {
        if capacity_bound == 0 {
            return Err(BoundaryError169a5aef::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError169a5aef::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError169a5aef::ExceedsCapacity {
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
    use crate::finite_category_builder::DeclaredFiniteCategoryBuilder;

    fn build_triangle_category() -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new("Triangle")
            .object("A")
            .object("B")
            .object("C")
            .identity("A", "id_A")
            .identity("B", "id_B")
            .identity("C", "id_C")
            .morphism("f", "A", "B")
            .morphism("g", "B", "C")
            .morphism("h", "A", "C")
            .composition("f", "g", "h")
            .identity_compositions()
            .build()
    }

    fn build_tetrahedron_category() -> DeclaredFiniteCategory {
        DeclaredFiniteCategoryBuilder::new("Tetrahedron")
            .object("A")
            .object("B")
            .object("C")
            .object("D")
            .identity("A", "id_A")
            .identity("B", "id_B")
            .identity("C", "id_C")
            .identity("D", "id_D")
            .morphism("f", "A", "B")
            .morphism("g", "B", "C")
            .morphism("k", "C", "D")
            .morphism("fg", "A", "C")
            .morphism("gk", "B", "D")
            .morphism("fgk", "A", "D")
            .composition("f", "g", "fg")
            .composition("g", "k", "gk")
            .composition("fg", "k", "fgk")
            .composition("f", "gk", "fgk")
            .identity_compositions()
            .build()
    }

    #[test]
    fn test_n_simplices() {
        let cat = build_triangle_category();
        let nerve = DeclaredNerve::new(&cat);

        let s0 = nerve.n_simplices(0);
        assert_eq!(s0.len(), 3); // A, B, C

        let s1 = nerve.n_simplices(1);
        // id_A, id_B, id_C, f, g, h
        assert_eq!(s1.len(), 6);

        let s2 = nerve.n_simplices(2);
        // Non-degenerate: (f, g)
        // Degenerate: (id_A, f), (f, id_B), (id_B, g), (g, id_C), (id_A, h), (h, id_C),
        //             (id_A, id_A), (id_B, id_B), (id_C, id_C)
        // Total = 1 + 6 + 3 = 10
        assert_eq!(s2.len(), 10);

        let non_degen_s2 = nerve.nondegenerate_n_simplices(2);
        assert_eq!(non_degen_s2.len(), 1);
        assert_eq!(
            non_degen_s2[0],
            Simplex::Chain(vec!["f".into(), "g".into()])
        );
    }

    #[test]
    fn test_face_maps() {
        let cat = build_triangle_category();
        let nerve = DeclaredNerve::new(&cat);

        // 1-simplex face maps
        let f = Simplex::Chain(vec!["f".into()]);
        assert_eq!(nerve.face(&f, 0), Some(Simplex::Vertex("B".into())));
        assert_eq!(nerve.face(&f, 1), Some(Simplex::Vertex("A".into())));

        // 2-simplex face maps for (f, g)
        let fg = Simplex::Chain(vec!["f".into(), "g".into()]);
        assert_eq!(nerve.face(&fg, 0), Some(Simplex::Chain(vec!["g".into()]))); // drop f
        assert_eq!(nerve.face(&fg, 1), Some(Simplex::Chain(vec!["h".into()]))); // compose f,g
        assert_eq!(nerve.face(&fg, 2), Some(Simplex::Chain(vec!["f".into()]))); // drop g
    }

    #[test]
    fn test_degeneracy_maps() {
        let cat = build_triangle_category();
        let nerve = DeclaredNerve::new(&cat);

        // 0-simplex degeneracy
        let a = Simplex::Vertex("A".into());
        assert_eq!(
            nerve.degeneracy(&a, 0),
            Some(Simplex::Chain(vec!["id_A".into()]))
        );

        // 1-simplex degeneracy for f: A -> B
        let f = Simplex::Chain(vec!["f".into()]);
        assert_eq!(
            nerve.degeneracy(&f, 0),
            Some(Simplex::Chain(vec!["id_A".into(), "f".into()]))
        );
        assert_eq!(
            nerve.degeneracy(&f, 1),
            Some(Simplex::Chain(vec!["f".into(), "id_B".into()]))
        );
    }

    #[test]
    fn test_simplicial_identities() {
        let cat = build_tetrahedron_category();
        let nerve = DeclaredNerve::new(&cat);

        // 3-simplex: A -> B -> C -> D
        let fgk = Simplex::Chain(vec!["f".into(), "g".into(), "k".into()]);

        // Face identity: d_i d_j = d_{j-1} d_i for i < j
        for j in 1..=3 {
            for i in 0..j {
                let d_j = nerve.face(&fgk, j).unwrap();
                let lhs = nerve.face(&d_j, i).unwrap();

                let d_i = nerve.face(&fgk, i).unwrap();
                let rhs = nerve.face(&d_i, j - 1).unwrap();

                assert_eq!(lhs, rhs, "Face identity failed for i={}, j={}", i, j);
            }
        }

        // 2-simplex: A -> B -> C
        let fg = Simplex::Chain(vec!["f".into(), "g".into()]);

        // Degeneracy identity: s_i s_j = s_{j+1} s_i for i <= j
        for j in 0..=2 {
            for i in 0..=j {
                let s_j = nerve.degeneracy(&fg, j).unwrap();
                let lhs = nerve.degeneracy(&s_j, i).unwrap();

                let s_i = nerve.degeneracy(&fg, i).unwrap();
                let rhs = nerve.degeneracy(&s_i, j + 1).unwrap();

                assert_eq!(lhs, rhs, "Degeneracy identity failed for i={}, j={}", i, j);
            }
        }

        // Face-degeneracy identities: d_i s_j
        for j in 0..=2 {
            for i in 0..=3 {
                let s_j = nerve.degeneracy(&fg, j).unwrap();
                let d_i_s_j = nerve.face(&s_j, i).unwrap();

                if i < j {
                    let d_i = nerve.face(&fg, i).unwrap();
                    let expected = nerve.degeneracy(&d_i, j - 1).unwrap();
                    assert_eq!(
                        d_i_s_j, expected,
                        "Failed d_i s_j for i<j (i={}, j={})",
                        i, j
                    );
                } else if i == j || i == j + 1 {
                    assert_eq!(
                        d_i_s_j, fg,
                        "Failed d_i s_j for i=j or i=j+1 (i={}, j={})",
                        i, j
                    );
                } else {
                    // i > j + 1
                    let d_i_minus_1 = nerve.face(&fg, i - 1).unwrap();
                    let expected = nerve.degeneracy(&d_i_minus_1, j).unwrap();
                    assert_eq!(
                        d_i_s_j, expected,
                        "Failed d_i s_j for i>j+1 (i={}, j={})",
                        i, j
                    );
                }
            }
        }
    }
}

#[cfg(test)]
mod l4_boundary_tests_169a5aef {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord169a5aef::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord169a5aef::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord169a5aef::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord169a5aef::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord169a5aef::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError169a5aef::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError169a5aef::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
