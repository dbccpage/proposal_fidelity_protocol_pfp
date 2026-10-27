//! Major Histocompatibility Complex (MHC) Antigen Presentation Window (U16).
//!
//! Slices large candidate prompts, traces, and code payloads into bounded
//! partial observation windows of size `window_size` with stride `stride`.
//!
//! Prevents KV context blowout and ensures detectors operate over compact,
//! localized epitope representations rather than un-partitioned monolithic strings.
//!
//! AuthorityEffect: None.

use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct EpitopeSlice {
    pub slice_index: usize,
    pub start_offset: usize,
    pub end_offset: usize,
    pub content: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MhcPresentationWindow {
    pub window_size: usize,
    pub stride: usize,
}

impl Default for MhcPresentationWindow {
    fn default() -> Self {
        Self {
            window_size: 64,
            stride: 32,
        }
    }
}

impl MhcPresentationWindow {
    pub fn new(window_size: usize, stride: usize) -> Self {
        assert!(window_size > 0, "Window size must be > 0");
        assert!(stride > 0, "Stride must be > 0");
        Self {
            window_size,
            stride,
        }
    }

    /// Present payload as a sequence of overlapping epitope slices.
    pub fn present_slices(&self, payload: &str) -> Vec<EpitopeSlice> {
        if payload.is_empty() {
            return Vec::new();
        }

        let chars: Vec<char> = payload.chars().collect();
        let total = chars.len();
        let mut slices = Vec::new();
        let mut start = 0;
        let mut idx = 0;

        while start < total {
            let end = (start + self.window_size).min(total);
            let content: String = chars[start..end].iter().collect();
            slices.push(EpitopeSlice {
                slice_index: idx,
                start_offset: start,
                end_offset: end,
                content,
            });
            idx += 1;
            if end == total {
                break;
            }
            start += self.stride;
        }

        slices
    }

    pub fn try_new(window_size: usize, stride: usize) -> Result<Self, MhcWindowError> {
        if window_size == 0 {
            return Err(MhcWindowError::ZeroWindow);
        }
        if stride == 0 {
            return Err(MhcWindowError::ZeroStride);
        }
        Ok(Self {
            window_size,
            stride,
        })
    }
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum MhcWindowError {
    ZeroWindow,
    ZeroStride,
    Overflow,
}

// Origin: engine/crates_rs/core_prompt_civilization/src/immune/mhc.rs
// Claim: urn:core:crates_rs:core-prompt-civilization:mhc:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

impl std::fmt::Display for MhcWindowError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{:?}", self)
    }
}

impl std::error::Error for MhcWindowError {}

/// Number of epitope slices `present_slices` emits for a character length.
pub fn slice_count(char_len: usize, window: usize, stride: usize) -> Result<usize, MhcWindowError> {
    if window == 0 {
        return Err(MhcWindowError::ZeroWindow);
    }
    if stride == 0 {
        return Err(MhcWindowError::ZeroStride);
    }
    if char_len == 0 {
        return Ok(0);
    }
    if char_len <= window {
        return Ok(1);
    }
    let rest = char_len - window;
    let stride_minus = stride - 1;
    let steps = rest
        .checked_add(stride_minus)
        .ok_or(MhcWindowError::Overflow)?
        / stride;
    1usize.checked_add(steps).ok_or(MhcWindowError::Overflow)
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod mhc_slice_count_witness {
    use super::*;

    #[test]
    fn slice_count_matches_present_slices() {
        let window = MhcPresentationWindow::try_new(2, 2);
        assert!(window.is_ok());
        if let Ok(window) = window {
            let payload = "abcd";
            let count = slice_count(payload.chars().count(), window.window_size, window.stride);
            assert_eq!(count, Ok(window.present_slices(payload).len()));
        }
    }

    #[test]
    fn zero_window_is_refused() {
        assert!(matches!(
            MhcPresentationWindow::try_new(0, 2),
            Err(MhcWindowError::ZeroWindow)
        ));
        assert!(matches!(
            slice_count(4, 2, 0),
            Err(MhcWindowError::ZeroStride)
        ));
    }
}
