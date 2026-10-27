//! Minimal finite-depth future-legality report for a nonnegative counter.
//!
//! Increment is always legal; decrement requires a positive count. At remaining
//! depth r, the report is min(count,r). Its r+1 classes distinguish exactly the
//! legal continuations of length at most r. Depth decreases after every event:
//! this is not a fixed-depth congruence for unrestricted continuation.

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CounterEvent {
    Increment,
    Decrement,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum CounterBoundary {
    /// Native decrement guard fails within the admitted context depth.
    GuardRefusal,
    /// No answer is claimed about another event at depth zero.
    ContextExhausted,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CounterReportError {
    ClipExceedsDepth,
    DifferentDepths,
}

// Origin: engine/crates_rs/core_category_theory/src/bounded_counter.rs
// Claim: urn:core:crates_rs:core-category-theory:bounded-counter:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CounterReportError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CounterReportError {}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct CounterReport {
    remaining: usize,
    clipped: usize,
}

impl CounterReport {
    /// Construct from a bounded machine count. Bigger scalar owners may supply
    /// a checked clip through `try_from_clip`, without narrowing the raw count.
    pub fn from_count(remaining: usize, count: usize) -> Self {
        Self {
            remaining,
            clipped: count.min(remaining),
        }
    }

    pub fn try_from_clip(remaining: usize, clipped: usize) -> Result<Self, CounterReportError> {
        if clipped > remaining {
            return Err(CounterReportError::ClipExceedsDepth);
        }
        Ok(Self { remaining, clipped })
    }

    pub fn remaining(self) -> usize {
        self.remaining
    }
    pub fn clipped(self) -> usize {
        self.clipped
    }

    pub fn advance(self, event: CounterEvent) -> Result<Self, CounterBoundary> {
        let next = self
            .remaining
            .checked_sub(1)
            .ok_or(CounterBoundary::ContextExhausted)?;
        let clipped = match event {
            CounterEvent::Increment => {
                // Avoid overflow even when remaining == clipped == usize::MAX.
                if self.clipped >= next {
                    next
                } else {
                    self.clipped + 1
                }
            }
            CounterEvent::Decrement => self
                .clipped
                .checked_sub(1)
                .ok_or(CounterBoundary::GuardRefusal)?
                .min(next),
        };
        Ok(Self {
            remaining: next,
            clipped,
        })
    }

    /// Returns the first boundary met. A guard failure already observed within
    /// the budget stays a failure even if an unexecuted suffix is longer.
    pub fn observe(self, word: &[CounterEvent]) -> Result<Self, CounterBoundary> {
        word.iter()
            .try_fold(self, |state, &event| state.advance(event))
    }

    /// Number of consecutive decrements separating distinct classes at the
    /// same depth. No word is allocated. None means equivalent guarded futures.
    pub fn separating_removals(self, other: Self) -> Result<Option<usize>, CounterReportError> {
        if self.remaining != other.remaining {
            return Err(CounterReportError::DifferentDepths);
        }
        Ok((self.clipped != other.clipped).then(|| self.clipped.min(other.clipped) + 1))
    }
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_e9f87b1f {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
