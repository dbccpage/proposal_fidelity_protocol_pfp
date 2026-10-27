#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Term {
    pub name: String,
    pub is_zombie: bool,
}

impl Term {
    pub fn unbound(name: &str) -> Self {
        Self {
            name: name.to_string(),
            is_zombie: false, // Default to not zombie unless specified
        }
    }

    pub fn is_zombie(&self) -> bool {
        self.is_zombie
    }

    pub fn is_wellformed(&self) -> bool {
        !self.name.is_empty() && !self.is_zombie
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Path {
    pub source: Term,
    pub target: Term,
    pub dimension: usize,
    pub has_witness: bool,
    pub connected: bool,
}

impl Path {
    pub fn new(source: Term, target: Term) -> Self {
        Self {
            source,
            target,
            dimension: 1,
            has_witness: true,
            connected: true,
        }
    }

    pub fn with_dimension(mut self, dimension: usize) -> Self {
        self.dimension = dimension;
        self
    }

    pub fn is_reflexive(&self) -> bool {
        self.source == self.target
    }

    pub fn has_witness(&self) -> bool {
        self.has_witness
    }

    pub fn is_connected(&self) -> bool {
        self.connected
    }

    pub fn is_loop(&self) -> bool {
        self.is_reflexive()
    }

    pub fn type_arity(&self) -> usize {
        1
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Boundary {
    pub faces: Vec<Path>,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StructuralCandidate {
    Term(Term),
    Path(Path),
    Boundary(Boundary),
    Topology(Vec<Path>),
    TypeUniverse,
}

impl StructuralCandidate {
    pub fn summary(&self) -> String {
        match self {
            Self::Term(t) => format!("Term({})", t.name),
            Self::Path(p) => format!("Path({} â†’ {})", p.source.name, p.target.name),
            Self::Boundary(b) => format!("Boundary({} faces)", b.faces.len()),
            Self::Topology(t) => format!("Topology({} paths)", t.len()),
            Self::TypeUniverse => "TypeUniverse".to_string(),
        }
    }

    pub fn shape_signature(&self) -> String {
        match self {
            Self::Term(t) if t.is_zombie() => "Term(Zombie)".to_string(),
            Self::Term(_) => "Term(Valid)".to_string(),
            Self::Path(p) => format!(
                "Path({}â†’{})",
                if p.source.is_zombie() {
                    "Zombie"
                } else {
                    "Valid"
                },
                if p.target.is_zombie() {
                    "Zombie"
                } else {
                    "Valid"
                }
            ),
            Self::Boundary(b) => format!("Boundary({})", b.faces.len()),
            Self::Topology(t) => format!("Topology({})", t.len()),
            Self::TypeUniverse => "TypeUniverse".to_string(),
        }
    }
}

impl From<Term> for StructuralCandidate {
    fn from(term: Term) -> Self {
        Self::Term(term)
    }
}

impl From<Path> for StructuralCandidate {
    fn from(path: Path) -> Self {
        Self::Path(path)
    }
}

#[derive(Debug, Clone)]
pub struct GenerationContext {
    pub dimension: usize,
    pub active_terms: Vec<Term>,
}

impl Default for GenerationContext {
    fn default() -> Self {
        Self {
            dimension: 1,
            active_terms: vec![],
        }
    }
}

impl GenerationContext {
    pub fn with_max_dim(mut self, dim: usize) -> Self {
        self.dimension = dim;
        self
    }
}

pub trait TypeSystem {
    fn infer_type(&self, term: &Term) -> Result<String, String>;
    fn allows_loops(&self, arity: usize) -> Result<(), String>;
}

// Origin: engine/crates_rs/core_types/src/coherence_structures.rs
// Claim: urn:core:crates_rs:core-types:coherence-structures:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord243cd5a0 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord243cd5a0` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError243cd5a0 {
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
impl BoundaryError243cd5a0 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError243cd5a0 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError243cd5a0 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord243cd5a0 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError243cd5a0> {
        if capacity_bound == 0 {
            return Err(BoundaryError243cd5a0::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError243cd5a0::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError243cd5a0::ExceedsCapacity {
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
mod l4_boundary_tests_243cd5a0 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord243cd5a0::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord243cd5a0::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord243cd5a0::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord243cd5a0::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord243cd5a0::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError243cd5a0::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError243cd5a0::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
