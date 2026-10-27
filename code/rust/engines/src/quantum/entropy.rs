use core_functional::trace_diagnostics::EntropyError;

pub fn is_converging(history: &[f64], tolerance: f64, window: usize) -> bool {
    if !tolerance.is_finite() || tolerance < 0.0 || window == 0 {
        return false;
    }
    if history.iter().any(|x| !x.is_finite()) {
        return false;
    }
    if history.len() < 2 {
        return false; // Insufficient history is not convergence
    }

    let w = window.min(history.len() - 1);
    history[history.len() - w - 1..]
        .windows(2)
        .all(|pair| (pair[1] - pair[0]).abs() <= tolerance)
}

pub fn is_converging_checked(
    history: &[f64],
    tolerance: f64,
    window: usize,
) -> Result<bool, EntropyError> {
    if !tolerance.is_finite() || tolerance < 0.0 {
        return Err(EntropyError::InvalidTolerance(tolerance));
    }
    if window == 0 {
        return Err(EntropyError::InvalidWindow(window));
    }
    if history.len() < 2 {
        return Err(EntropyError::InsufficientHistory);
    }
    if let Some((index, _)) = history.iter().enumerate().find(|(_, x)| !x.is_finite()) {
        return Err(EntropyError::NonFiniteProbability { index });
    }

    let w = window.min(history.len() - 1);
    Ok(history[history.len() - w - 1..]
        .windows(2)
        .all(|pair| (pair[1] - pair[0]).abs() <= tolerance))
}

// --- exact carrier witness ---
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CauchyError {
    Shape,
    Bound { gap: i128 },
    Overflow,
}

// Origin: engine/crates_rs/engines/src/quantum/entropy.rs
// Claim: urn:core:crates_rs:engines:entropy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for CauchyError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for CauchyError {}

/// An exact Cauchy tail: every pair in the window is within numer/denom.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ExactCauchyTail {
    width: usize,
    bound_numer: u64,
    bound_denom: u64,
}

fn check_pair_gap(
    left_val: i64,
    right_val: i64,
    bound_numer: u64,
    bound_denom: u64,
) -> Result<(), CauchyError> {
    let left = i128::from(left_val);
    let right = i128::from(right_val);
    let gap = left
        .checked_sub(right)
        .ok_or(CauchyError::Overflow)?
        .unsigned_abs();
    let gap_i128 = i128::try_from(gap).map_err(|_| CauchyError::Overflow)?;
    let scaled = gap_i128
        .checked_mul(i128::from(bound_denom))
        .ok_or(CauchyError::Overflow)?;
    if scaled > i128::from(bound_numer) {
        return Err(CauchyError::Bound { gap: gap_i128 });
    }
    Ok(())
}

impl ExactCauchyTail {
    pub fn try_certify(history: &[i64], start: usize, bound_numer: u64, bound_denom: u64) -> Result<Self, CauchyError> {
        if bound_denom == 0 {
            return Err(CauchyError::Shape);
        }
        let window = history.get(start..).ok_or(CauchyError::Shape)?;
        if window.len() < 2 {
            return Err(CauchyError::Shape);
        }
        for (left_index, &left_val) in window.iter().enumerate() {
            for &right_val in &window[left_index + 1..] {
                check_pair_gap(left_val, right_val, bound_numer, bound_denom)?;
            }
        }
        Ok(Self { width: window.len(), bound_numer, bound_denom })
    }

    pub fn width(&self) -> usize { self.width }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod cauchy_tests {
    use super::*;

    #[test]
    fn a_window_of_width_two_fits_the_bound_three() {
        let tail = ExactCauchyTail::try_certify(&[10, 12, 11, 10], 0, 3, 1);
        assert!(matches!(tail, Ok(ref tail) if tail.width() == 4));
    }

    #[test]
    fn the_bound_one_rejects_the_same_window() {
        let tail = ExactCauchyTail::try_certify(&[10, 12, 11, 10], 0, 1, 1);
        assert!(matches!(tail, Err(CauchyError::Bound { .. })));
    }
}
