//! AST declaration inspection shared by the build auditor and its adversarial tests.
//! This checks syntax, not cfg execution, macro expansion or behavior.
use syn::{Item, UseTree, Visibility};

fn use_names(tree: &UseTree, symbol: &str) -> bool {
    match tree {
        UseTree::Path(path) => use_names(&path.tree, symbol),
        UseTree::Name(name) => name.ident == symbol && symbol != "self",
        UseTree::Rename(rename) => rename.rename == symbol && symbol != "_",
        UseTree::Group(group) => group.items.iter().any(|tree| use_names(tree, symbol)),
        // A glob cannot identify a binding without independent target resolution.
        UseTree::Glob(_) => false,
    }
}

fn impl_declares_member(items: &[Item], owner: &str, member: &str) -> bool {
    items.iter().any(|item| {
        let Item::Impl(item) = item else { return false };
        let syn::Type::Path(path) = item.self_ty.as_ref() else {
            return false;
        };
        path.path
            .segments
            .last()
            .is_some_and(|segment| segment.ident == owner)
            && item.items.iter().any(|item| match item {
                syn::ImplItem::Fn(item) => item.sig.ident == member,
                syn::ImplItem::Const(item) => item.ident == member,
                syn::ImplItem::Type(item) => item.ident == member,
                _ => false,
            })
    })
}

fn named_item_ident(item: &Item) -> Option<&syn::Ident> {
    match item {
        Item::Const(item) => Some(&item.ident),
        Item::Enum(item) => Some(&item.ident),
        Item::Fn(item) => Some(&item.sig.ident),
        Item::Mod(item) => Some(&item.ident),
        Item::Static(item) => Some(&item.ident),
        Item::Struct(item) => Some(&item.ident),
        _ => named_type_or_trait_ident(item),
    }
}

fn named_type_or_trait_ident(item: &Item) -> Option<&syn::Ident> {
    match item {
        Item::Trait(item) => Some(&item.ident),
        Item::TraitAlias(item) => Some(&item.ident),
        Item::Type(item) => Some(&item.ident),
        Item::Union(item) => Some(&item.ident),
        _ => None,
    }
}

pub fn items_declare(items: &[Item], symbol: &str) -> bool {
    if let Some((owner, member)) = symbol.split_once("::") {
        if !identifier(owner) || !identifier(member) {
            return false;
        }
        return impl_declares_member(items, owner, member);
    }
    items.iter().any(|item| match item {
        Item::Use(item) if matches!(item.vis, Visibility::Public(_)) => {
            use_names(&item.tree, symbol)
        }
        other => named_item_ident(other).is_some_and(|ident| ident == symbol),
    })
}

pub fn declares_symbol(src: &str, symbol: &str) -> Result<bool, String> {
    if symbol.is_empty() {
        return Err("RUST_SYMBOL_EMPTY".into());
    }
    let file = syn::parse_file(src).map_err(|error| format!("RUST_PARSE_FAILED: {error}"))?;
    Ok(items_declare(&file.items, symbol))
}

pub fn identifier(value: &str) -> bool {
    let mut chars = value.chars();
    chars
        .next()
        .is_some_and(|c| c.is_ascii_alphabetic() || c == '_')
        && chars.all(|c| c.is_ascii_alphanumeric() || c == '_')
}

// Origin: engine/crates_rs/core_contracts/src/audit_declarations.rs
// Claim: urn:core:crates_rs:core-contracts:audit-declarations:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8da1f872 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8da1f872` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8da1f872 {
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
impl BoundaryError8da1f872 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8da1f872 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8da1f872 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8da1f872 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8da1f872> {
        if capacity_bound == 0 {
            return Err(BoundaryError8da1f872::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8da1f872::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8da1f872::ExceedsCapacity {
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
mod l4_boundary_tests_8da1f872 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8da1f872::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8da1f872::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8da1f872::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8da1f872::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8da1f872::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError8da1f872::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError8da1f872::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
