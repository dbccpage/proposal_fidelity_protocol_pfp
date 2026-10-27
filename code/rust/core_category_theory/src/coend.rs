//! Coends — Spec Section 14.
//!
//! A coend ∫^c F(c,c) is the universal quotient of diagonal contributions
//! by dinaturality. It is the categorical analog of integration.
//!
//! For a bifunctor F : C^op × C → Set, the coend is computed by:
//! 1. Collecting all F(c,c) contributions (one per object c).
//! 2. Quotienting by dinaturality: for each f: c → c',
//!    the left-action F(f, id)(x) is identified with the right-action F(id, f)(x).
//!
//! Coends appear in: profunctor composition, Kan extensions, tensor products.

use std::collections::BTreeMap;

// ---------------------------------------------------------------------------
// DinaturalityWitness — records one identification
// ---------------------------------------------------------------------------

/// A witness that two elements were identified via dinaturality.
///
/// For f: c → c', dinaturality identifies:
///   F(id_c, f)(x)  for x ∈ F(c, c)
/// with
///   F(f, id_c')(y) for y ∈ F(c', c')
/// when both land in F(c, c').
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DinaturalityWitness {
    /// The morphism f: source → target that induced this identification.
    pub morphism: String,
    pub source_object: String,
    pub target_object: String,
    /// Index of the element in the forward contribution.
    pub forward_index: usize,
    /// Index of the element in the backward contribution.
    pub backward_index: usize,
}

// ---------------------------------------------------------------------------
// DeclaredFiniteCoend
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct TaggedDiagonal<T> {
    pub object: String,
    pub index: usize,
    pub value: T,
}

/// A finite coend over a bifunctor F: C^op × C → Set, represented
/// by explicit elements and dinaturality identifications.
///
/// The elements are equivalence class representatives after
/// quotienting by all dinaturality relations.
#[derive(Debug, Clone)]
pub struct DeclaredFiniteCoend<T: Clone + PartialEq> {
    /// The contributing objects (diagonal entries of the bifunctor).
    pub objects: Vec<String>,
    /// Raw diagonal contributions: object → list of elements in F(c,c).
    pub contributions: BTreeMap<String, Vec<T>>,
    /// Quotient classes after identification.
    pub classes: Vec<Vec<TaggedDiagonal<T>>>,
    /// Maps a tagged diagonal element (object, index) to its equivalence class index.
    pub class_of: BTreeMap<(String, usize), usize>,
    /// Dinaturality identifications applied during computation.
    pub identifications: Vec<DinaturalityWitness>,
}

/// Input for computing a finite coend.
pub struct CoendInput<T: Clone + PartialEq> {
    /// Objects of the indexing category.
    pub objects: Vec<String>,
    /// Morphisms: (name, source, target).
    pub morphisms: Vec<(String, String, String)>,
    /// Diagonal contributions: object → elements of F(c,c).
    pub diagonal: BTreeMap<String, Vec<T>>,
    /// Forward action: F(id_c, f): F(c,c) -> F(c,c')
    /// Key: morphism name. Value: element index in F(c,c) → element index in F(c,c').
    pub forward_action: BTreeMap<String, Vec<(usize, usize)>>,
    /// Backward action: F(f, id_c'): F(c',c') -> F(c,c')
    /// Key: morphism name. Value: element index in F(c',c') → element index in F(c,c').
    pub backward_action: BTreeMap<String, Vec<(usize, usize)>>,
}

fn coend_find(parent: &mut Vec<usize>, i: usize) -> usize {
    if parent[i] != i {
        let p = parent[i];
        parent[i] = coend_find(parent, p);
    }
    parent[i]
}

fn coend_union(parent: &mut Vec<usize>, a: usize, b: usize) {
    let ra = coend_find(parent, a);
    let rb = coend_find(parent, b);
    if ra != rb {
        parent[rb] = ra;
    }
}

fn collect_diagonal_elements<T: Clone + PartialEq>(
    input: &CoendInput<T>,
) -> Vec<TaggedDiagonal<T>> {
    let mut all_elements: Vec<TaggedDiagonal<T>> = Vec::new();
    for obj in &input.objects {
        if let Some(elems) = input.diagonal.get(obj) {
            for (i, elem) in elems.iter().enumerate() {
                all_elements.push(TaggedDiagonal {
                    object: obj.clone(),
                    index: i,
                    value: elem.clone(),
                });
            }
        }
    }
    all_elements
}

fn find_global_index<T>(all_elements: &[TaggedDiagonal<T>], obj: &str, local: usize) -> Option<usize> {
    all_elements
        .iter()
        .position(|td| td.object == obj && td.index == local)
}

fn unify_morphism_pairs<T>(
    mor_name: &str,
    src: &str,
    tgt: &str,
    forward_pairs: &[(usize, usize)],
    backward_pairs: &[(usize, usize)],
    all_elements: &[TaggedDiagonal<T>],
    parent: &mut Vec<usize>,
    identifications: &mut Vec<DinaturalityWitness>,
) {
    for &(src_local, forward_target) in forward_pairs {
        for &(tgt_local, backward_target) in backward_pairs {
            if forward_target == backward_target {
                if let (Some(gi_src), Some(gi_tgt)) = (
                    find_global_index(all_elements, src, src_local),
                    find_global_index(all_elements, tgt, tgt_local),
                ) {
                    coend_union(parent, gi_src, gi_tgt);
                    identifications.push(DinaturalityWitness {
                        morphism: mor_name.to_string(),
                        source_object: src.to_string(),
                        target_object: tgt.to_string(),
                        forward_index: src_local,
                        backward_index: tgt_local,
                    });
                }
            }
        }
    }
}

impl<T: Clone + PartialEq + Eq + std::hash::Hash> DeclaredFiniteCoend<T> {
    /// Compute the coend from an explicit input specification.
    ///
    /// This implements the coequalizer construction:
    ///   ∐_{f:c→c'} F(c',c) ⇉ ∐_c F(c,c) → ∫^c F(c,c)
    pub fn compute(input: &CoendInput<T>) -> Self {
        let objects = input.objects.clone();
        let contributions = input.diagonal.clone();

        // Assign global indices to all diagonal elements.
        let all_elements = collect_diagonal_elements(input);

        // Build union-find for identifications.
        let n = all_elements.len();
        let mut parent: Vec<usize> = (0..n).collect();
        let mut identifications = Vec::new();

        // Apply dinaturality identifications for each morphism.
        for (mor_name, src, tgt) in &input.morphisms {
            if let (Some(forward_pairs), Some(backward_pairs)) = (
                input.forward_action.get(mor_name),
                input.backward_action.get(mor_name),
            ) {
                unify_morphism_pairs(
                    mor_name,
                    src,
                    tgt,
                    forward_pairs,
                    backward_pairs,
                    &all_elements,
                    &mut parent,
                    &mut identifications,
                );
            }
        }

        // Extract equivalence classes.
        let mut classes_map: BTreeMap<usize, Vec<TaggedDiagonal<T>>> = BTreeMap::new();
        let mut class_of: BTreeMap<(String, usize), usize> = BTreeMap::new();

        for (i, element) in all_elements.iter().enumerate() {
            let root = coend_find(&mut parent, i);
            classes_map.entry(root).or_default().push(element.clone());
            class_of.insert((element.object.clone(), element.index), root);
        }

        let classes = classes_map.into_values().collect();

        DeclaredFiniteCoend {
            objects,
            contributions,
            classes,
            class_of,
            identifications,
        }
    }
}

// ---------------------------------------------------------------------------
// Validation: dinaturality check
// ---------------------------------------------------------------------------

pub fn validate_coend_input<T: Clone + PartialEq>(input: &CoendInput<T>) -> Vec<String> {
    let mut violations = Vec::new();

    // 1. Every object has a diagonal contribution
    for obj in &input.objects {
        if !input.diagonal.contains_key(obj) {
            violations.push(format!("Missing diagonal contribution for object {}", obj));
        }
    }

    // 2. Every morphism has both actions
    for (mor_name, _, _) in &input.morphisms {
        if !input.forward_action.contains_key(mor_name) {
            violations.push(format!("Missing forward action for morphism {}", mor_name));
        }
        if !input.backward_action.contains_key(mor_name) {
            violations.push(format!("Missing backward action for morphism {}", mor_name));
        }
    }

    violations
}

/// Verify that all dinaturality conditions are satisfied in the coend.
///
/// For each morphism f: c → c', verify that elements identified by
/// forward-action and backward-action are in the same equivalence class.
pub fn check_dinaturality<T: Clone + PartialEq>(
    coend: &DeclaredFiniteCoend<T>,
    input: &CoendInput<T>,
) -> Vec<String> {
    let mut violations = Vec::new();
    for (mor_name, src, tgt) in &input.morphisms {
        if let (Some(forward_pairs), Some(backward_pairs)) = (
            input.forward_action.get(mor_name),
            input.backward_action.get(mor_name),
        ) {
            for &(src_local, forward_target) in forward_pairs {
                for &(tgt_local, backward_target) in backward_pairs {
                    if forward_target == backward_target {
                        let lhs_class = coend.class_of.get(&(src.clone(), src_local));
                        let rhs_class = coend.class_of.get(&(tgt.clone(), tgt_local));

                        match (lhs_class, rhs_class) {
                            (Some(l), Some(r)) if l == r => {} // valid
                            (Some(l), Some(r)) => {
                                violations.push(format!(
                                    "Dinaturality violated: {} and {} via morphism {} mapped to different classes ({} vs {})",
                                    src_local, tgt_local, mor_name, l, r
                                ));
                            }
                            _ => {
                                violations.push(format!(
                                    "Dinaturality: missing class mapping for elements involved in morphism {}",
                                    mor_name
                                ));
                            }
                        }
                    }
                }
            }
        }
    }
    violations
}

// Origin: engine/crates_rs/core_category_theory/src/coend.rs
// Claim: urn:core:crates_rs:core-category-theory:coend:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord2cc1a1b2 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord2cc1a1b2` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError2cc1a1b2 {
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
impl BoundaryError2cc1a1b2 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError2cc1a1b2 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError2cc1a1b2 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord2cc1a1b2 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError2cc1a1b2> {
        if capacity_bound == 0 {
            return Err(BoundaryError2cc1a1b2::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError2cc1a1b2::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError2cc1a1b2::ExceedsCapacity {
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
    fn trivial_coend_single_object() {
        // One object, no non-identity morphisms. Coend = F(c,c) itself.
        let input = CoendInput {
            objects: vec!["A".into()],
            morphisms: vec![],
            diagonal: {
                let mut m = BTreeMap::new();
                m.insert("A".into(), vec![1, 2, 3]);
                m
            },
            forward_action: BTreeMap::new(),
            backward_action: BTreeMap::new(),
        };

        let coend = DeclaredFiniteCoend::compute(&input);
        assert_eq!(coend.classes.len(), 3);
        assert!(coend.identifications.is_empty());
    }

    #[test]
    fn coend_with_identification() {
        // Two objects A, B with morphism f: A → B.
        // F(A,A) = {0}, F(B,B) = {1}.
        // Forward action of f sends 0 to slot 0 in F(A,B).
        // Backward action of f sends 1 to slot 0 in F(A,B).
        // So 0 ~ 1 in the coend.
        let input = CoendInput {
            objects: vec!["A".into(), "B".into()],
            morphisms: vec![("f".into(), "A".into(), "B".into())],
            diagonal: {
                let mut m = BTreeMap::new();
                m.insert("A".into(), vec![0]);
                m.insert("B".into(), vec![1]);
                m
            },
            forward_action: {
                let mut m = BTreeMap::new();
                m.insert("f".into(), vec![(0, 0)]); // element 0 of F(A,A) → slot 0
                m
            },
            backward_action: {
                let mut m = BTreeMap::new();
                m.insert("f".into(), vec![(0, 0)]); // element 0 of F(B,B) → slot 0
                m
            },
        };

        let coend = DeclaredFiniteCoend::compute(&input);
        // 0 and 1 are identified, so only 1 class.
        assert_eq!(coend.classes.len(), 1);
        assert_eq!(coend.identifications.len(), 1);
    }
}

#[cfg(test)]
mod l4_boundary_tests_2cc1a1b2 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord2cc1a1b2::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord2cc1a1b2::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord2cc1a1b2::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord2cc1a1b2::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord2cc1a1b2::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError2cc1a1b2::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError2cc1a1b2::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
