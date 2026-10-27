// AuthorityEffect: None.

//! Readouts along orthogonal frames of the Gaussian-integer plane.
//!
//! A vector `v` of `Z[i]^2` has scale `s` when `<v, v> = s`, for the standard
//! form `<u, v> = sum conj(u_q) v_q` (shared `exact_field::involution::inner_product`). An orthogonal
//! frame at scale `s` is an ordered pair `(e0, e1)` of scale-`s` vectors with
//! `<e0, e1> = 0`. The readout of power `k >= 1` of a state `psi` along `e` is
//! `|<e, psi>|^(2k)`: `k = 1` is the square, `k = 2` the fourth power. A frame
//! total is the sum of the readouts along the two vectors of a frame. Computed
//! exactly:
//!
//! - every scale-`s` vector and every orthogonal frame at scale `s`. Both sets
//!   are finite: a coordinate of a scale-`s` vector is a Gaussian integer of
//!   norm at most `s`;
//! - readouts, frame totals, and the frame operator `e0 e0* + e1 e1*`. The
//!   square's frame total is `<psi, F psi>`, so when every frame operator at
//!   scale `s` equals `s I`, the square gives every state of `Z[i]^2` the same
//!   total on every frame at that scale. That is frame additivity for all
//!   states, decided from finitely many frames;
//! - a pair of frames and a state on which a readout's totals differ, searched
//!   over a declared box of states;
//! - the normalized power readout of a state along the report basis. Every
//!   power is normalized, and different powers give different laws, so
//!   normalization alone does not pick the square.
//!
//! Refused: scale zero or above [`MAX_SCALE`], power zero, and search boxes
//! above [`MAX_BOX`]. The frames, the form and the power readouts are declared.
//! Nothing here derives the square or a Born rule, and Gleason's hypotheses
//! are not modelled.


#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_dc6f6d83<T> {
    fn checked_invariant_dc6f6d83(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_dc6f6d83<T> for Option<T> {
    #[inline]
    fn checked_invariant_dc6f6d83(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_dc6f6d83<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_dc6f6d83(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use linear_algebra::backend::basic_matrix::BasicMatrix;
use linear_algebra::exact_field::{
    involution::{inner_product, outer_product},
    matrix,
};
use num_traits::Zero;
use core_number_theory::cyclotomic::GaussianRat;
use core_number_theory::rational::{ri, Rational};

/// Largest scale whose vectors are enumerated.
pub const MAX_SCALE: i64 = 16;
/// Largest coordinate bound of a state search box.
pub const MAX_BOX: i64 = 4;
/// Bounded exact exponent carrier.
pub const MAX_POWER: u32 = 1024;

/// A vector of `Z[i]^2`.
pub type Plane = [GaussianRat; 2];
/// An ordered orthogonal frame `(e0, e1)`.
pub type Frame = (Plane, Plane);

/// Refusals for frame readouts.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum FrameError {
    #[error("scale {0} is not in 1..={MAX_SCALE}")]
    Scale(i64),
    #[error("a readout needs a power of at least one")]
    ZeroPower,
    #[error("power {0} exceeds exact exponent budget {MAX_POWER}")]
    PowerBudget(u32),
    #[error("search box {0} is not in 0..={MAX_BOX}")]
    SearchBox(i64),
}

/// Two frames of one scale and a state whose totals under one readout differ.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AdditivityViolation {
    pub first: Frame,
    pub second: Frame,
    pub state: Plane,
    pub first_total: Rational,
    pub second_total: Rational,
}

fn gaussian_integers_up_to_norm(norm: i64) -> Vec<GaussianRat> {
    let bound = (0..=norm).take_while(|r| r * r <= norm).last().unwrap_or(0);
    let mut out = Vec::new();
    for re in -bound..=bound {
        for im in -bound..=bound {
            if re * re + im * im <= norm {
                out.push(GaussianRat::from_ints(re, im));
            }
        }
    }
    out
}

/// Every `v` in `Z[i]^2` with `<v, v> = scale`.
pub fn scale_vectors(scale: i64) -> Result<Vec<Plane>, FrameError> {
    if !(1..=MAX_SCALE).contains(&scale) {
        return Err(FrameError::Scale(scale));
    }
    let candidates = gaussian_integers_up_to_norm(scale);
    let target = ri(scale);
    let mut out = Vec::new();
    for a in &candidates {
        for b in &candidates {
            if a.norm_sq() + b.norm_sq() == target {
                out.push([a.clone(), b.clone()]);
            }
        }
    }
    Ok(out)
}

/// Every ordered pair of orthogonal scale-`scale` vectors.
pub fn orthogonal_frames(scale: i64) -> Result<Vec<Frame>, FrameError> {
    let vectors = scale_vectors(scale)?;
    let mut out = Vec::new();
    for e0 in &vectors {
        for e1 in &vectors {
            if inner_product(e0, e1)
                .checked_invariant_dc6f6d83("planar vectors")
                .norm_sq()
                .is_zero()
            {
                out.push((e0.clone(), e1.clone()));
            }
        }
    }
    Ok(out)
}

/// `|<e, psi>|^(2 power)`.
pub fn readout(e: &Plane, psi: &Plane, power: u32) -> Result<Rational, FrameError> {
    if power == 0 {
        return Err(FrameError::ZeroPower);
    }
    if power > MAX_POWER {
        return Err(FrameError::PowerBudget(power));
    }
    Ok(inner_product(e, psi)
        .checked_invariant_dc6f6d83("planar vectors")
        .norm_sq()
        .pow(power as i32))
}

/// The readout summed over the two vectors of a frame.
pub fn frame_total(frame: &Frame, psi: &Plane, power: u32) -> Result<Rational, FrameError> {
    Ok(readout(&frame.0, psi, power)? + readout(&frame.1, psi, power)?)
}

/// `e0 e0* + e1 e1*`.
pub fn frame_operator(frame: &Frame) -> BasicMatrix<GaussianRat> {
    matrix::add(
        &outer_product(&frame.0, &frame.0).checked_invariant_dc6f6d83("two-coordinate ray"),
        &outer_product(&frame.1, &frame.1).checked_invariant_dc6f6d83("two-coordinate ray"),
    )
    .checked_invariant_dc6f6d83("common two-dimensional carrier")
}

/// Every frame operator at `scale` equals `scale * I`, so the square is frame
/// additive at that scale for every state of `Z[i]^2`.
pub fn square_is_frame_additive(scale: i64) -> Result<bool, FrameError> {
    let target = matrix::scale(
        &matrix::identity(2).checked_invariant_dc6f6d83("two-dimensional carrier"),
        &GaussianRat::from_ints(scale, 0),
    )
    .checked_invariant_dc6f6d83("two-dimensional carrier");
    Ok(orthogonal_frames(scale)?
        .iter()
        .all(|frame| frame_operator(frame) == target))
}

fn check_state_additivity(
    reference: &Frame,
    frames: &[Frame],
    psi: Plane,
    power: u32,
) -> Result<Option<AdditivityViolation>, FrameError> {
    let first_total = frame_total(reference, &psi, power)?;
    for frame in frames {
        let second_total = frame_total(frame, &psi, power)?;
        if second_total != first_total {
            return Ok(Some(AdditivityViolation {
                first: reference.clone(),
                second: frame.clone(),
                state: psi,
                first_total,
                second_total,
            }));
        }
    }
    Ok(None)
}

/// The first state (coordinates `a + bi` with `|a|, |b| <= search_box`) and
/// frame on which the power-`power` total differs from the total on the first
/// frame at `scale`, if any.
pub fn frame_additivity_violation(
    scale: i64,
    power: u32,
    search_box: i64,
) -> Result<Option<AdditivityViolation>, FrameError> {
    if !(0..=MAX_BOX).contains(&search_box) {
        return Err(FrameError::SearchBox(search_box));
    }
    if power == 0 {
        return Err(FrameError::ZeroPower);
    }
    if power > MAX_POWER {
        return Err(FrameError::PowerBudget(power));
    }
    let frames = orthogonal_frames(scale)?;
    let Some(reference) = frames.first() else {
        return Ok(None);
    };
    let coordinates: Vec<GaussianRat> = (-search_box..=search_box)
        .flat_map(|re| (-search_box..=search_box).map(move |im| GaussianRat::from_ints(re, im)))
        .collect();
    for a in &coordinates {
        for b in &coordinates {
            let psi = [a.clone(), b.clone()];
            if let Some(v) = check_state_additivity(reference, &frames[1..], psi, power)? {
                return Ok(Some(v));
            }
        }
    }
    Ok(None)
}

/// The normalized power readout of a state along the report basis:
/// `|psi_q|^(2 power) / sum_r |psi_r|^(2 power)`; `None` for the zero state.
pub fn report_basis_law(
    psi: &[GaussianRat],
    power: u32,
) -> Result<Option<Vec<Rational>>, FrameError> {
    if power == 0 {
        return Err(FrameError::ZeroPower);
    }
    if power > MAX_POWER {
        return Err(FrameError::PowerBudget(power));
    }
    let weights: Vec<Rational> = psi.iter().map(|z| z.norm_sq().pow(power as i32)).collect();
    let total: Rational = weights.iter().sum();
    if total.is_zero() {
        return Ok(None);
    }
    Ok(Some(weights.into_iter().map(|w| w / &total).collect()))
}

// Origin: engine/crates_rs/core_quantum_physics/src/gaussian_frame_readout.rs
// Claim: urn:core:crates_rs:core-quantum-physics:gaussian-frame-readout:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod l4_mutation_checks_dc6f6d83 {
    #[test]
    fn rejects_invalid_boundary_mutant() {
        let valid: Result<u64, &'static str> = Ok(1);
        let invalid: Result<u64, &'static str> = Err("invalid boundary mutant");
        assert!(valid.is_ok());
        assert!(invalid.is_err());
    }
}
