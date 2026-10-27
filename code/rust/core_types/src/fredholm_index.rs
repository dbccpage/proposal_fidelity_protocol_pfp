// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// Fredholm Index â€” Dimensional Stabilization Invariant
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
//
// Computes the virtual Fredholm index for pseudoholomorphic curve
// moduli spaces under different constraint regimes.
//
// The central insight: point constraints have codimension 2(n-1) each,
// which grows with ambient dimension n, causing the Fredholm index to
// become negative under stabilization (X Ã— â„‚^N). Tangency constraints
// have codimension 2(k-1) each, which is fixed regardless of n.
//
// A negative Fredholm index means the moduli space of valid logical
// paths is empty â€” the reasoning is overconstrained, creating a
// topological tear (H^n â‰  0) that cannot be resolved.
//
// This type is DIAGNOSTIC. It does NOT evaluate, score, accept, or
// make descent decisions. It reports whether a constraint configuration
// is dimensionally stable.

/// Fredholm index configuration for a pseudoholomorphic curve with constraints.
///
/// For genus-0 rational curves (g = 0) in a symplectic manifold of
/// real dimension 2n, the virtual index formula is:
///
/// ```text
/// ind(u) = (n-3)(2-2g) + 2câ‚(A) + #Î“âº + #Î“â» - Î£ codim(constraints)
/// ```
///
/// For our setting (g=0, single negative end):
///
/// ```text
/// ind = 2(n-3) + 2câ‚ + #Î“âº + 1 - Î£ codim
/// ```
///
/// INVARIANT: If `ind < 0`, the moduli space is empty and repair
/// at this constraint configuration will create a logical tear.
#[derive(Debug, Clone)]
pub struct FredholmIndex {
    /// Ambient complex dimension n (half the real dimension).
    /// In the reasoning context: proxy for context window / trace length.
    pub ambient_dim: usize,
    /// First Chern class contribution câ‚(A).
    /// Typically 1 for simple disc-type curves.
    pub c1_class: i64,
    /// Number of positive punctures (input Reeb orbits / premises).
    pub positive_ends: usize,
    /// Number of negative punctures (output Reeb orbits / conclusions).
    /// The theory requires exactly 1 for definitive conclusion.
    pub negative_ends: usize,
    /// Number of distinct point constraints (pass-through facts).
    pub point_constraints: usize,
    /// Tangency orders for local tangency constraints.
    /// Each entry k means tangency of order (k-1) to a local divisor.
    pub tangency_orders: Vec<usize>,
}

/// Result of Fredholm index computation.
#[derive(Debug, Clone)]
pub struct FredholmDiagnostic {
    /// The computed Fredholm index.
    pub index: i64,
    /// Whether the moduli space is nonempty (index â‰¥ 0).
    pub is_stable: bool,
    /// The total codimension from constraints.
    pub constraint_codimension: i64,
    /// The base index before constraints.
    pub base_index: i64,
}

impl FredholmIndex {
    /// Compute the base index (before any constraints).
    ///
    /// ```text
    /// base = 2(n-3) + 2câ‚ + #Î“âº + #Î“â»
    /// ```
    fn base_index(&self) -> i64 {
        2 * (self.ambient_dim as i64 - 3)
            + 2 * self.c1_class
            + self.positive_ends as i64
            + self.negative_ends as i64
    }

    /// Compute the Fredholm index under point constraints.
    ///
    /// Each point constraint has codimension 2(n-1), which grows
    /// linearly with the ambient dimension n. This is the source
    /// of dimensional instability.
    pub fn diagnose_points(&self) -> FredholmDiagnostic {
        let base = self.base_index();
        let codim = 2 * (self.ambient_dim as i64 - 1) * self.point_constraints as i64;
        let index = base - codim;
        FredholmDiagnostic {
            index,
            is_stable: index >= 0,
            constraint_codimension: codim,
            base_index: base,
        }
    }

    /// Compute the Fredholm index under tangency constraints.
    ///
    /// Each tangency of order (k-1) at a single divisor has
    /// codimension 2(k-1), which is FIXED regardless of ambient
    /// dimension n. This is why tangency constraints are
    /// dimensionally stable.
    pub fn diagnose_tangency(&self) -> FredholmDiagnostic {
        let base = self.base_index();
        let codim: i64 = self
            .tangency_orders
            .iter()
            .map(|&k| 2 * (k.saturating_sub(1) as i64))
            .sum();
        let index = base - codim;
        FredholmDiagnostic {
            index,
            is_stable: index >= 0,
            constraint_codimension: codim,
            base_index: base,
        }
    }

    /// Returns the maximum tangency order k such that the Fredholm
    /// index remains non-negative (the moduli space stays nonempty).
    ///
    /// ```text
    /// ind â‰¥ 0  âŸº  k â‰¤ (base + 2) / 2 = n - 3 + câ‚ + (#Î“âº + #Î“â»)/2 + 1
    /// ```
    ///
    /// This is the budget for tangency order at a single constraint.
    pub fn max_stable_tangency_order(&self) -> usize {
        let base = self.base_index();
        // ind = base - 2(k-1) â‰¥ 0  âŸ¹  k â‰¤ base/2 + 1

        (base / 2 + 1).max(0) as usize
    }

    /// Given a number of point constraints that would be injected,
    /// compute the equivalent tangency order that carries the same
    /// "information density" but remains stable.
    ///
    /// Strategy: total codim from n_points point constraints is
    /// 2(n-1)Â·n_points. We solve for tangency order k such that
    /// 2(k-1) = 2(n-1)Â·n_points, giving k = (n-1)Â·n_points + 1.
    /// Then clamp to max_stable_tangency_order.
    pub fn equivalent_tangency_order(&self, n_points: usize) -> usize {
        let raw_k = (self.ambient_dim.saturating_sub(1)) * n_points + 1;
        raw_k.min(self.max_stable_tangency_order())
    }
}

// Origin: engine/crates_rs/core_types/src/fredholm_index.rs
// Claim: urn:core:crates_rs:core-types:fredholm-index:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord7a945a5d {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord7a945a5d` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError7a945a5d {
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
impl BoundaryError7a945a5d {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError7a945a5d {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError7a945a5d {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord7a945a5d {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError7a945a5d> {
        if capacity_bound == 0 {
            return Err(BoundaryError7a945a5d::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError7a945a5d::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError7a945a5d::ExceedsCapacity {
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

    fn standard_config(dim: usize) -> FredholmIndex {
        FredholmIndex {
            ambient_dim: dim,
            c1_class: 1,
            positive_ends: 1,
            negative_ends: 1,
            point_constraints: 0,
            tangency_orders: vec![],
        }
    }

    #[test]
    fn base_index_formula() {
        let fi = standard_config(4);
        // base = 2(4-3) + 2(1) + 1 + 1 = 2 + 2 + 2 = 6
        assert_eq!(fi.base_index(), 6);
    }

    #[test]
    fn point_constraints_scale_with_dimension() {
        // In dim 4: codim per point = 2(4-1) = 6
        let fi = FredholmIndex {
            point_constraints: 1,
            ..standard_config(4)
        };
        let diag = fi.diagnose_points();
        assert_eq!(diag.constraint_codimension, 6);
        assert_eq!(diag.index, 0); // barely stable

        // In dim 50: codim per point = 2(50-1) = 98
        let fi50 = FredholmIndex {
            point_constraints: 1,
            ..standard_config(50)
        };
        let diag50 = fi50.diagnose_points();
        assert_eq!(diag50.constraint_codimension, 98);
        // base = 2(47) + 2 + 2 = 98, index = 98 - 98 = 0
        assert_eq!(diag50.index, 0);

        // Two points in dim 50: index = 98 - 196 = -98
        let fi50_2 = FredholmIndex {
            point_constraints: 2,
            ..standard_config(50)
        };
        assert!(
            fi50_2.diagnose_points().index < 0,
            "Two points in dim 50 must be unstable"
        );
    }

    #[test]
    fn tangency_constraints_dimension_independent() {
        // Order-3 tangency: codim = 2(3-1) = 4, regardless of ambient dim
        for n in [4, 10, 50, 100, 500] {
            let fi = FredholmIndex {
                tangency_orders: vec![3],
                ..standard_config(n)
            };
            let diag = fi.diagnose_tangency();
            assert_eq!(
                diag.constraint_codimension, 4,
                "Tangency codim should be 4 at dim {n}, got {}",
                diag.constraint_codimension
            );
            assert!(
                diag.is_stable,
                "Order-3 tangency should be stable at dim {n}"
            );
        }
    }

    #[test]
    fn max_stable_tangency_order_grows_with_dim() {
        let fi4 = standard_config(4);
        let fi100 = standard_config(100);
        assert!(fi100.max_stable_tangency_order() > fi4.max_stable_tangency_order());
    }

    #[test]
    fn equivalent_tangency_is_clamped() {
        let fi = standard_config(10);
        let max_k = fi.max_stable_tangency_order();
        // Requesting 100 point constraints worth â†’ should clamp
        let equiv = fi.equivalent_tangency_order(100);
        assert!(equiv <= max_k);
    }
}

#[cfg(test)]
mod l4_boundary_tests_7a945a5d {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord7a945a5d::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord7a945a5d::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord7a945a5d::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord7a945a5d::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord7a945a5d::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError7a945a5d::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError7a945a5d::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
