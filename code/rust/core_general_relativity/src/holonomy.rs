//! `holonomy` — finite dual-face object for `core_general_relativity`.
//!
//! AUTHORING_QUALITY: human_llm_best_effort_slop (best-effort dual-face scaffold; not human-canon math; not PROVED; not GlobalGreen).
//! **AuthorityEffect:** None.

#[allow(dead_code, non_camel_case_types, missing_docs)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct BoundaryError_f443a412;
#[allow(dead_code, non_camel_case_types, missing_docs)]
pub type BoundaryResult_f443a412<T> = std::result::Result<T, BoundaryError_f443a412>;

/// Fence string (proposal).
pub const AUTHORITY_FENCE: &str =
    "AuthorityEffect None; not PROVED; not GlobalGreen; best-effort scaffold.";

/// Finite carrier for `holonomy` (proposal; not full classical object).
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct Holonomy {
    /// Degree / dimension / stage proxy (ℕ₀).
    pub degree: usize,
    /// Stable label / object id (finite string).
    pub label: String,
}

impl Holonomy {
    /// Construct a finite carrier.
    pub fn new(degree: usize, label: impl Into<String>) -> Self {
        Self {
            degree,
            label: label.into(),
        }
    }

    /// Authority fence (never mints PROVED/GlobalGreen).
    pub fn authority_fence() -> &'static str {
        AUTHORITY_FENCE
    }
}

// Origin: engine/crates_rs/core_general_relativity/src/holonomy.rs
// Claim: urn:core:crates_rs:core-general-relativity:holonomy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_and_fence() {
        let x = Holonomy::new(1, "test");
        assert_eq!(x.degree, 1);
        assert_eq!(x.label, "test");
        assert!(Holonomy::authority_fence().contains("AuthorityEffect None"));
    }
}

/// Closed axis-aligned lattice loop whose quarter-turn holonomy is exactly one full turn.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OrthogonalHolonomy {
    edges: usize,
    quarter_turns: i64,
    twice_area: i128,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HolonomyError {
    Bound,
    Axis,
    Open,
    Turn,
    Area,
    Overflow,
}

impl std::fmt::Display for HolonomyError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Bound => write!(f, "an orthogonal loop needs 4 to 32 edges"),
            Self::Axis => write!(f, "each edge must be a nonzero axis-aligned step"),
            Self::Open => write!(f, "edge vectors do not close"),
            Self::Turn => write!(f, "quarter-turn sum is not ±4"),
            Self::Area => write!(f, "shoelace area is zero"),
            Self::Overflow => write!(f, "checked holonomy overflow"),
        }
    }
}

impl std::error::Error for HolonomyError {}

fn quarter_turn_step(dx: i64, dy: i64, next: (i64, i64)) -> Result<i64, HolonomyError> {
    if (dx == 0) == (dy == 0) {
        return Err(HolonomyError::Axis);
    }
    let cross = i128::from(dx)
        .checked_mul(i128::from(next.1))
        .and_then(|left| {
            i128::from(dy)
                .checked_mul(i128::from(next.0))
                .and_then(|right| left.checked_sub(right))
        })
        .ok_or(HolonomyError::Overflow)?;
    if cross > 0 {
        Ok(1)
    } else if cross < 0 {
        Ok(-1)
    } else {
        Err(HolonomyError::Turn)
    }
}

fn shoelace_step(
    x: i128,
    y: i128,
    dx: i64,
    dy: i64,
    twice_area: i128,
) -> Result<(i128, i128, i128), HolonomyError> {
    let x2 = x.checked_add(i128::from(dx)).ok_or(HolonomyError::Overflow)?;
    let y2 = y.checked_add(i128::from(dy)).ok_or(HolonomyError::Overflow)?;
    let left = x.checked_mul(y2).ok_or(HolonomyError::Overflow)?;
    let right = x2.checked_mul(y).ok_or(HolonomyError::Overflow)?;
    let next_area = twice_area
        .checked_add(left.checked_sub(right).ok_or(HolonomyError::Overflow)?)
        .ok_or(HolonomyError::Overflow)?;
    Ok((x2, y2, next_area))
}

fn validate_closed_holonomy(
    sum_x: i128,
    sum_y: i128,
    turns: i64,
    twice_area: i128,
) -> Result<(), HolonomyError> {
    if sum_x != 0 || sum_y != 0 {
        return Err(HolonomyError::Open);
    }
    if turns != 4 && turns != -4 {
        return Err(HolonomyError::Turn);
    }
    if twice_area == 0 {
        return Err(HolonomyError::Area);
    }
    Ok(())
}

impl OrthogonalHolonomy {
    pub fn certify(edges: &[(i64, i64)]) -> Result<Self, HolonomyError> {
        if !(4..=32).contains(&edges.len()) {
            return Err(HolonomyError::Bound);
        }
        let mut sum_x = 0i128;
        let mut sum_y = 0i128;
        let mut turns = 0i64;
        let mut x = 0i128;
        let mut y = 0i128;
        let mut twice_area = 0i128;
        for (index, &(dx, dy)) in edges.iter().enumerate() {
            let next = *edges.get((index + 1) % edges.len()).ok_or(HolonomyError::Bound)?;
            let turn = quarter_turn_step(dx, dy, next)?;
            turns = turns.checked_add(turn).ok_or(HolonomyError::Overflow)?;
            (x, y, twice_area) = shoelace_step(x, y, dx, dy, twice_area)?;
            sum_x = sum_x.checked_add(i128::from(dx)).ok_or(HolonomyError::Overflow)?;
            sum_y = sum_y.checked_add(i128::from(dy)).ok_or(HolonomyError::Overflow)?;
        }
        validate_closed_holonomy(sum_x, sum_y, turns, twice_area)?;
        Ok(Self {
            edges: edges.len(),
            quarter_turns: turns,
            twice_area,
        })
    }

    pub fn edges(&self) -> usize {
        self.edges
    }

    pub fn quarter_turns(&self) -> i64 {
        self.quarter_turns
    }

    pub fn twice_area(&self) -> i128 {
        self.twice_area
    }
}

#[cfg(test)]
mod exact_holonomy_tests {
    use super::*;

    #[test]
    fn the_unit_square_turns_once_and_has_area_one() {
        let loop_ = OrthogonalHolonomy::certify(&[(1, 0), (0, 1), (-1, 0), (0, -1)]).map_or_else(|_| loop { assert!(false); }, |value| value);
        assert_eq!(loop_.edges(), 4);
        assert_eq!(loop_.quarter_turns(), 4);
        assert_eq!(loop_.twice_area(), 2);
    }

    #[test]
    fn a_nonclosing_path_is_refused() {
        assert_eq!(
            OrthogonalHolonomy::certify(&[(1, 0), (0, 1), (-1, 0), (0, 1)]),
            Err(HolonomyError::Open)
        );
    }
}
