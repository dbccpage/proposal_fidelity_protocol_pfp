//! Typed newtype IDs for homological algebra entities.
//!
//! Each ID type uniquely identifies a specific kind of mathematical object
//! within the core_homology system.

use serde::{Deserialize, Serialize};

macro_rules! define_id {
    ($(#[$meta:meta])* $name:ident) => {
        $(#[$meta])*
        #[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
        pub struct $name(pub u64);

        impl $name {
            pub fn new(id: u64) -> Self {
                Self(id)
            }
        }

        impl std::fmt::Display for $name {
            fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
                write!(f, "{}({})", stringify!($name), self.0)
            }
        }
    };
}

define_id!(
    /// Identifies a chain element.
    ChainId
);
define_id!(
    /// Identifies a cochain element.
    CochainId
);
define_id!(
    /// Identifies a verified cycle.
    CycleId
);
define_id!(
    /// Identifies a verified cocycle.
    CocycleId
);
define_id!(
    /// Identifies a boundary element.
    BoundaryId
);
define_id!(
    /// Identifies a coboundary element.
    CoboundaryId
);
define_id!(
    /// Identifies a chain complex.
    ChainComplexId
);
define_id!(
    /// Identifies a cochain complex.
    CochainComplexId
);
define_id!(
    /// Identifies a homology class.
    HomologyClassId
);
define_id!(
    /// Identifies a cohomology class.
    CohomologyClassId
);
define_id!(
    /// Identifies a carrier.
    CarrierId
);
/// Identifies a basis by name.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct BasisId(pub String);

impl BasisId {
    pub fn new(name: impl Into<String>) -> Self {
        Self(name.into())
    }
}

impl std::fmt::Display for BasisId {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "BasisId({})", self.0)
    }
}

/// Exact carrier witness.
/// A basis roster is a non-empty set of non-empty names. A repeated name is not a second basis.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BasisRoster {
    names: Vec<BasisId>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BasisRosterError {
    EmptyRoster,
    EmptyId,
    Duplicate,
}

impl BasisRoster {
    pub fn try_new(names: impl IntoIterator<Item = impl Into<String>>) -> Result<Self, BasisRosterError> {
        let mut seen = std::collections::BTreeSet::new();
        let mut stored = Vec::new();
        for name in names {
            let name = name.into();
            if name.is_empty() {
                return Err(BasisRosterError::EmptyId);
            }
            if !seen.insert(name.clone()) {
                return Err(BasisRosterError::Duplicate);
            }
            stored.push(BasisId::new(name));
        }
        if stored.is_empty() {
            return Err(BasisRosterError::EmptyRoster);
        }
        Ok(Self { names: stored })
    }

    pub fn len(&self) -> usize {
        self.names.len()
    }

    pub fn names(&self) -> &[BasisId] {
        &self.names
    }
}
define_id!(
    /// Identifies a matrix.
    MatrixId
);
define_id!(
    /// Identifies a manifest.
    ManifestId
);
define_id!(
    /// Identifies a witness.
    WitnessId
);

/// Grading degree in a chain/cochain complex.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Degree(pub i32);

impl Degree {
    pub fn new(n: i32) -> Self {
        Self(n)
    }

    pub fn value(self) -> i32 {
        self.0
    }
}

impl std::fmt::Display for Degree {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "deg({})", self.0)
    }
}

// Origin: engine/crates_rs/core_homology/src/ids.rs
// Claim: urn:core:crates_rs:core-homology:ids:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_id_display() {
        let chain_id = ChainId::new(42);
        assert_eq!(format!("{}", chain_id), "ChainId(42)");
    }

    #[test]
    fn test_degree_ordering() {
        let d0 = Degree::new(0);
        let d1 = Degree::new(1);
        let d_neg = Degree::new(-1);
        assert!(d_neg < d0);
        assert!(d0 < d1);
    }

    #[test]
    fn test_id_equality() {
        let a = CarrierId::new(100);
        let b = CarrierId::new(100);
        let c = CarrierId::new(101);
        assert_eq!(a, b);
        assert_ne!(a, c);
    }

    #[test]
    fn a_basis_roster_refuses_an_empty_or_duplicate_id() {
        assert!(matches!(BasisRoster::try_new(Vec::<String>::new()), Err(BasisRosterError::EmptyRoster)));
        assert!(matches!(BasisRoster::try_new([""]), Err(BasisRosterError::EmptyId)));
        assert!(matches!(
            BasisRoster::try_new(["cycle", "cycle"]),
            Err(BasisRosterError::Duplicate)
        ));
        let roster = BasisRoster::try_new(["chains", "cochains"]);
        assert!(matches!(roster.as_ref(), Ok(value) if value.len() == 2 && value.names().len() == 2));
    }
}
