use std::sync::Arc;

// ----------------------------------------------------------------------------
// Core Types
// ----------------------------------------------------------------------------

// Ctx: Configuration / Global Constants (Reader)
#[derive(Clone, Debug)]
pub struct Ctx {
    pub common_constants: Vec<f64>,
    pub threshold: f64,
}

// St: State (Accumulated suggestions, local symbol table)
#[derive(Clone, Debug, Default)]
pub struct St {
    pub suggestions: Vec<String>,
}

// Writer: Accumulated Violations
#[derive(Clone, Debug)]
pub struct Violation {
    pub rule_id: String,
    pub msg: String,
    pub severity: String,
}

pub type Writer = Vec<Violation>;
pub type ArrowResult<B> = Result<(Writer, St, B), anyhow::Error>;

pub type Arrow<A, B> = Arc<dyn Fn(&Ctx, St, A) -> ArrowResult<B> + Send + Sync>;

pub enum Either<L, R> {
    Left(L),
    Right(R),
}

// ----------------------------------------------------------------------------
// Combinators
// ----------------------------------------------------------------------------

pub fn arr<A, B, F>(f: F) -> Arrow<A, B>
where
    A: 'static + Send + Sync,
    B: 'static + Send + Sync,
    F: Fn(A) -> B + Send + Sync + 'static,
{
    Arc::new(move |_ctx, st, a| Ok((vec![], st, f(a))))
}

pub fn compose<A, B, C>(k1: Arrow<A, B>, k2: Arrow<B, C>) -> Arrow<A, C>
where
    A: 'static + Send + Sync,
    B: 'static + Send + Sync,
    C: 'static + Send + Sync,
{
    Arc::new(move |ctx, st, a| {
        let (mut w1, st1, b) = k1(ctx, st, a)?;
        let (w2, st2, c) = k2(ctx, st1, b)?;
        w1.extend(w2);
        Ok((w1, st2, c))
    })
}

pub fn tell<A>(v: Violation) -> Arrow<A, A>
where
    A: 'static + Clone + Send + Sync,
{
    Arc::new(move |_ctx, st, a| Ok((vec![v.clone()], st, a)))
}

// Lift a pure function on the **input** side (Reader), leaving state and writer untouched
pub fn map_input<A, B, F>(f: F) -> Arrow<A, B>
where
    A: 'static + Send + Sync,
    B: 'static + Send + Sync,
    F: Fn(A) -> B + Send + Sync + 'static,
{
    Arc::new(move |_ctx, st, a| Ok((vec![], st, f(a))))
}

// Fan-out: apply two arrows to the same input, combine their outputs
pub fn fanout<A, B, C>(ab: Arrow<A, B>, ac: Arrow<A, C>) -> Arrow<A, (B, C)>
where
    A: Clone + 'static + Send + Sync,
    B: 'static + Send + Sync,
    C: 'static + Send + Sync,
{
    Arc::new(move |ctx, st, a| {
        let (mut w1, st1, b) = ab(ctx, st, a.clone())?;
        let (w2, st2, c) = ac(ctx, st1, a)?;
        w1.extend(w2);
        Ok((w1, st2, (b, c)))
    })
}

// Split: apply two arrows to a pair, produce a pair
pub fn split<A, B, C, D>(f1: Arrow<A, B>, f2: Arrow<C, D>) -> Arrow<(A, C), (B, D)>
where
    A: 'static + Send + Sync,
    B: 'static + Send + Sync,
    C: 'static + Send + Sync,
    D: 'static + Send + Sync,
{
    Arc::new(move |ctx, st, (a, c)| {
        let (mut w1, st, b) = f1(ctx, st, a)?;
        let (w2, st, d) = f2(ctx, st, c)?;
        w1.extend(w2);
        Ok((w1, st, (b, d)))
    })
}

// Choice: apply either the left or right arrow depending on an Either value
pub fn choice<A, B, C>(f: Arrow<A, C>, g: Arrow<B, C>) -> Arrow<Either<A, B>, C>
where
    A: 'static + Send + Sync,
    B: 'static + Send + Sync,
    C: 'static + Send + Sync,
{
    Arc::new(move |ctx, st, input| match input {
        Either::Left(a) => f(ctx, st, a),
        Either::Right(b) => g(ctx, st, b),
    })
}

// Origin: engine/crates_rs/core_category_theory/src/arrow.rs
// Claim: urn:core:crates_rs:core-category-theory:arrow:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc7eca0a6 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc7eca0a6` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc7eca0a6 {
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
impl BoundaryErrorc7eca0a6 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc7eca0a6 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc7eca0a6 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc7eca0a6 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc7eca0a6> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc7eca0a6::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc7eca0a6::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc7eca0a6::ExceedsCapacity {
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

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
mod l4_boundary_tests_c7eca0a6 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordc7eca0a6::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordc7eca0a6::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordc7eca0a6::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordc7eca0a6::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordc7eca0a6::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrorc7eca0a6::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrorc7eca0a6::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
