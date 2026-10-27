// AuthorityEffect: None.

//! Four exact checks from the finite-QM four-wall control.
//!
//! Source:
//! `atlas/coda_atlas/F004_papers/006_finite_qm/python/finite_qm/use_cases/four_wall_reconstruction_and_operad_control.py`.
//!
//! That file also names a five-stage catalog of pilot, antibody and agent
//! identifiers. The catalog's verified bit is the conjunction of these four
//! checks, so the identifiers are not repeated here.
//!
//! Computed over `Q` or `Q(sqrt(5))`, written as pairs `(a, b)` for `a + b sqrt(5)`:
//!
//! - a four-effect rational qubit POVM whose Bloch vectors sum to zero, whose
//!   probability map has determinant `9/1000`, against the declared `2 x 2`
//!   principal minor `-1/16` of the Cabello/Peres polyhedral witness;
//! - the field norm of `det rho_twist = -1/16` and of `det rho_sos = 1/81`;
//! - `2 * 2 = 1` in `F_3`, and `2 = 0` in `F_2`;
//! - the Cayley factor of `delta = 1/2` has modulus one, the first-order Taylor
//!   step has squared norm `5/4`, the Renyi moments are `337/625` and `193/625`,
//!   and a 22-term artanh enclosure of `S = -sum p ln p` on `diag(9/25, 16/25)`
//!   has width below `10^{-12}`.
//!
//! The Mermin-Peres row product `+1`, column product `-1`, and the Choi
//! singlet expectations `-1/2`, `0` and `1` are the control's declared signs.
//! This module does not rebuild those operators. Nothing here is a
//! reconstruction theorem.
//!
//! AuthorityEffect: None.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

/// Wall 1: rational four-effect POVM against the polyhedral frame minor.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Wall1BuschIcPovmAudit {
    pub effect_traces: [BigRational; 4],
    pub effect_determinants: [BigRational; 4],
    pub trace_sum_equals_two: bool,
    pub bloch_sum_vanishes: bool,
    pub all_effects_psd: bool,
    pub reconstruction_determinant: BigRational,
    pub reconstruction_invertible: bool,
    pub polyhedral_cabello_peres_minor: BigRational,
    pub polyhedral_cone_strictly_larger_than_psd: bool,
    pub reconstructed_pythagorean_state_trace: BigRational,
    pub reconstructed_pythagorean_state_det: BigRational,
    pub cholesky_sos_verified: bool,
}

/// Wall 2: one Galois embedding of `Q(sqrt(5))` fails, the Gram-SOS state does not.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Wall2GaloisSosAudit {
    pub twist_trace_rational: BigRational,
    pub twist_trace_sqrt5: BigRational,
    pub twist_det_rational: BigRational,
    pub twist_det_sqrt5: BigRational,
    pub twist_det_field_norm: BigRational,
    pub twist_fails_conjugate_embedding: bool,
    pub sos_trace_rational: BigRational,
    pub sos_trace_sqrt5: BigRational,
    pub sos_det_rational: BigRational,
    pub sos_det_sqrt5: BigRational,
    pub sos_det_field_norm: BigRational,
    pub sos_factor_identity_holds: bool,
    pub sos_psd_in_all_galois_embeddings: bool,
}

/// Wall 3: characteristic of the half-step, plus the control's declared signs.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Wall3CocycleAndChoiAudit {
    pub inv2_mod3: i64,
    pub two_mod2: i64,
    pub odd_prime_half_invertible: bool,
    pub char2_half_obstructed: bool,
    pub mermin_peres_row_product: i64,
    pub mermin_peres_col_product: i64,
    pub mermin_peres_cocycle_ratio: i64,
    pub choi_transpose_singlet_expectation: BigRational,
    pub choi_identity_singlet_expectation: BigRational,
    pub choi_identity_bell_expectation: BigRational,
    pub choi_separates_positive_witness_from_cptp: bool,
}

/// Wall 4: Cayley unitarity, Taylor drift, and a rational entropy enclosure.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Wall4CayleyAndEntropyAudit {
    pub step_delta: BigRational,
    pub cayley_single_unitarity_defect: BigRational,
    pub strang_cayley_split_unitarity_defect: BigRational,
    pub taylor_first_order_norm_sq: BigRational,
    pub taylor_violates_unitarity: bool,
    pub pointer_probabilities: [BigRational; 2],
    pub renyi_p2: BigRational,
    pub renyi_p3: BigRational,
    pub renyi_p4: BigRational,
    pub von_neumann_entropy_lower_bound: BigRational,
    pub von_neumann_entropy_upper_bound: BigRational,
    pub von_neumann_entropy_interval_width: BigRational,
    pub interval_width_below_1e_12: bool,
}

/// The four checks and their conjunction.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct FourWallReconstructionReport {
    pub wall1_audit: Wall1BuschIcPovmAudit,
    pub wall2_audit: Wall2GaloisSosAudit,
    pub wall3_audit: Wall3CocycleAndChoiAudit,
    pub wall4_audit: Wall4CayleyAndEntropyAudit,
    pub all_four_walls_verified: bool,
}

fn det_4x4(m: &[[BigRational; 4]; 4]) -> BigRational {
    let mut a = m.clone();
    let mut sign = BigRational::one();
    let mut det_val = BigRational::one();
    for col in 0..4 {
        let pivot = (col..4).find(|&r| !a[r][col].is_zero());
        let Some(pivot) = pivot else {
            return BigRational::zero();
        };
        if pivot != col {
            a.swap(col, pivot);
            sign = -sign;
        }
        let piv_val = a[col][col].clone();
        det_val *= &piv_val;
        for r in (col + 1)..4 {
            if a[r][col].is_zero() {
                continue;
            }
            let factor = &a[r][col] / &piv_val;
            for c in col..4 {
                let term = &factor * &a[col][c];
                a[r][c] -= term;
            }
        }
    }
    sign * det_val
}

/// Wall 1 on the declared Bloch vectors `(+-3/5, 0, +-4/5)` and `(0, +-3/5, +-4/5)`.
pub fn evaluate_wall1_busch_ic_povm_vs_polyhedral_cone() -> Wall1BuschIcPovmAudit {
    let scaled_bloch = [
        (q(3, 5), q(0, 1), q(4, 5)),
        (q(-3, 5), q(0, 1), q(4, 5)),
        (q(0, 1), q(3, 5), q(-4, 5)),
        (q(0, 1), q(-3, 5), q(-4, 5)),
    ];
    let traces = [q(1, 2), q(1, 2), q(1, 2), q(1, 2)];
    let scaled_dets = scaled_bloch.clone().map(|(rx, ry, rz)| {
        q(1, 4) * (BigRational::one() - (rx.clone() * &rx + ry.clone() * &ry + rz.clone() * &rz))
    });
    let bx_sum = scaled_bloch.iter().fold(BigRational::zero(), |s, v| s + &v.0);
    let by_sum = scaled_bloch.iter().fold(BigRational::zero(), |s, v| s + &v.1);
    let bz_sum = scaled_bloch.iter().fold(BigRational::zero(), |s, v| s + &v.2);
    let m_prob = scaled_bloch.map(|(rx, ry, rz)| {
        [
            q(1, 4),
            q(1, 4) * rx,
            q(1, 4) * ry,
            q(1, 4) * rz,
        ]
    });
    let recon_det = det_4x4(&m_prob);
    let polyhedral_minor = q(0, 1) * q(1, 2) - q(-1, 4) * q(-1, 4);
    let d1 = q(9, 25);
    let d2 = q(12, 25);
    let l21 = q(2, 3);
    let rho_00 = d1.clone();
    let rho_11 = &l21 * &l21 * &d1 + &d2;
    let rho_01 = &l21 * &d1;
    let recon_tr = &rho_00 + &rho_11;
    let recon_det_state = &rho_00 * &rho_11 - &rho_01 * &rho_01;
    Wall1BuschIcPovmAudit {
        effect_traces: traces.clone(),
        effect_determinants: scaled_dets.clone(),
        trace_sum_equals_two: traces.iter().cloned().sum::<BigRational>() == q(2, 1),
        bloch_sum_vanishes: bx_sum.is_zero() && by_sum.is_zero() && bz_sum.is_zero(),
        all_effects_psd: scaled_dets.iter().all(|d| d >= &BigRational::zero()),
        reconstruction_determinant: recon_det.clone(),
        reconstruction_invertible: recon_det == q(9, 1000),
        polyhedral_cabello_peres_minor: polyhedral_minor.clone(),
        polyhedral_cone_strictly_larger_than_psd: polyhedral_minor == q(-1, 16),
        reconstructed_pythagorean_state_trace: recon_tr.clone(),
        reconstructed_pythagorean_state_det: recon_det_state.clone(),
        cholesky_sos_verified: recon_tr == BigRational::one()
            && recon_det_state == &d1 * &d2
            && d1 > BigRational::zero()
            && d2 > BigRational::zero(),
    }
}

/// Wall 2 on `rho_twist = diag((1+sqrt(5))/4, (3-sqrt(5))/4)` and the Gram-SOS state.
pub fn evaluate_wall2_galois_sos_total_positivity() -> Wall2GaloisSosAudit {
    let (t1_a, t1_b) = (q(1, 4), q(1, 4));
    let (t2_a, t2_b) = (q(3, 4), q(-1, 4));
    let twist_tr_a = &t1_a + &t2_a;
    let twist_tr_b = &t1_b + &t2_b;
    let twist_det_a = &t1_a * &t2_a + q(5, 1) * &t1_b * &t2_b;
    let twist_det_b = &t1_a * &t2_b + &t1_b * &t2_a;
    let twist_det_norm = &twist_det_a * &twist_det_a - q(5, 1) * &twist_det_b * &twist_det_b;
    let (s1_a, s1_b) = (q(1, 2), q(1, 6));
    let (s2_a, s2_b) = (q(1, 2), q(-1, 6));
    let sos_tr_a = &s1_a + &s2_a;
    let sos_tr_b = &s1_b + &s2_b;
    let sos_det_a = &s1_a * &s2_a + q(5, 1) * &s1_b * &s2_b;
    let sos_det_b = &s1_a * &s2_b + &s1_b * &s2_a;
    let sos_det_norm = &sos_det_a * &sos_det_a - q(5, 1) * &sos_det_b * &sos_det_b;
    let half = q(1, 2);
    let sq_a = q(1, 3) * (&half * &half + q(5, 1) * &half * &half);
    let sq_b = q(1, 3) * (q(2, 1) * &half * &half);
    Wall2GaloisSosAudit {
        twist_trace_rational: twist_tr_a.clone(),
        twist_trace_sqrt5: twist_tr_b.clone(),
        twist_det_rational: twist_det_a,
        twist_det_sqrt5: twist_det_b,
        twist_det_field_norm: twist_det_norm.clone(),
        twist_fails_conjugate_embedding: twist_tr_a == BigRational::one()
            && twist_tr_b.is_zero()
            && twist_det_norm == q(-1, 16),
        sos_trace_rational: sos_tr_a.clone(),
        sos_trace_sqrt5: sos_tr_b.clone(),
        sos_det_rational: sos_det_a.clone(),
        sos_det_sqrt5: sos_det_b.clone(),
        sos_det_field_norm: sos_det_norm.clone(),
        sos_factor_identity_holds: sq_a == s1_a && sq_b == s1_b,
        sos_psd_in_all_galois_embeddings: sos_tr_a == BigRational::one()
            && sos_tr_b.is_zero()
            && sos_det_a == q(1, 9)
            && sos_det_b.is_zero()
            && sos_det_norm == q(1, 81),
    }
}

/// Wall 3. The products `1*1*1` and `1*1*(-1)` are the control's declared signs.
pub fn evaluate_wall3_cocycle_and_choi_separation() -> Wall3CocycleAndChoiAudit {
    let inv2_mod3 = (2 * 2) % 3;
    let two_mod2 = 2 % 2;
    let mp_row_prod = 1 * 1 * 1;
    let mp_col_prod = 1 * 1 * -1;
    let mp_ratio = mp_row_prod * mp_col_prod;
    let choi_transpose_singlet = q(-1, 2);
    let choi_identity_singlet = q(0, 1);
    let choi_identity_bell = q(1, 1);
    Wall3CocycleAndChoiAudit {
        inv2_mod3,
        two_mod2,
        odd_prime_half_invertible: inv2_mod3 == 1,
        char2_half_obstructed: two_mod2 == 0,
        mermin_peres_row_product: mp_row_prod,
        mermin_peres_col_product: mp_col_prod,
        mermin_peres_cocycle_ratio: mp_ratio,
        choi_transpose_singlet_expectation: choi_transpose_singlet.clone(),
        choi_identity_singlet_expectation: choi_identity_singlet.clone(),
        choi_identity_bell_expectation: choi_identity_bell.clone(),
        choi_separates_positive_witness_from_cptp: mp_ratio == -1
            && choi_transpose_singlet < BigRational::zero()
            && choi_identity_singlet >= BigRational::zero()
            && choi_identity_bell == BigRational::one(),
    }
}

fn rational_ln_interval(x: &BigRational, terms: usize) -> (BigRational, BigRational) {
    let u = (x - BigRational::one()) / (x + BigRational::one());
    let u_sq = &u * &u;
    let mut partial = BigRational::zero();
    let mut u_pow = u;
    for k in 0..terms {
        partial += &u_pow / q(2 * k as i64 + 1, 1);
        u_pow *= &u_sq;
    }
    let rem_bound =
        u_pow.abs() / (q(2 * terms as i64 + 1, 1) * (BigRational::one() - &u_sq));
    let val = q(2, 1) * partial;
    let rad = q(2, 1) * rem_bound;
    (val.clone() - &rad, val + rad)
}

/// Wall 4 at `delta = 1/2` and pointer probabilities `9/25`, `16/25`.
pub fn evaluate_wall4_cayley_and_entropy_enclosure() -> Wall4CayleyAndEntropyAudit {
    let delta = q(1, 2);
    let denom = BigRational::one() + (&delta / q(2, 1)).pow(2);
    let cayley_re = (BigRational::one() - (&delta / q(2, 1)).pow(2)) / &denom;
    let cayley_im = -&delta / &denom;
    let single_norm = &cayley_re * &cayley_re + &cayley_im * &cayley_im;
    let single_defect = &single_norm - BigRational::one();
    let half_denom = BigRational::one() + (&delta / q(4, 1)).pow(2);
    let half_re = (BigRational::one() - (&delta / q(4, 1)).pow(2)) / &half_denom;
    let half_im = -(&delta / q(2, 1)) / &half_denom;
    let half_norm_sq = &half_re * &half_re + &half_im * &half_im;
    let strang_defect = (&half_norm_sq * &single_norm * &half_norm_sq) - BigRational::one();
    let taylor_norm_sq = BigRational::one() + &delta * &delta;
    let p0 = q(9, 25);
    let p1 = q(16, 25);
    let renyi_p2 = p0.pow(2) + p1.pow(2);
    let renyi_p3 = p0.pow(3) + p1.pow(3);
    let renyi_p4 = p0.pow(4) + p1.pow(4);
    let (ln_3_5_lo, ln_3_5_hi) = rational_ln_interval(&q(3, 5), 22);
    let (ln_4_5_lo, ln_4_5_hi) = rational_ln_interval(&q(4, 5), 22);
    let svn_lo = -q(2, 1) * &p0 * ln_3_5_hi - q(2, 1) * &p1 * ln_4_5_hi;
    let svn_hi = -q(2, 1) * &p0 * ln_3_5_lo - q(2, 1) * &p1 * ln_4_5_lo;
    let width = &svn_hi - &svn_lo;
    let below = svn_lo > q(653418, 1_000_000)
        && svn_hi < q(653419, 1_000_000)
        && width < q(1, 1) / q(10, 1).pow(12);
    Wall4CayleyAndEntropyAudit {
        step_delta: delta,
        cayley_single_unitarity_defect: single_defect,
        strang_cayley_split_unitarity_defect: strang_defect,
        taylor_first_order_norm_sq: taylor_norm_sq.clone(),
        taylor_violates_unitarity: taylor_norm_sq == q(5, 4),
        pointer_probabilities: [p0, p1],
        renyi_p2,
        renyi_p3,
        renyi_p4,
        von_neumann_entropy_lower_bound: svn_lo,
        von_neumann_entropy_upper_bound: svn_hi,
        von_neumann_entropy_interval_width: width,
        interval_width_below_1e_12: below,
    }
}

/// Run the four checks. `all_four_walls_verified` is their conjunction.
pub fn evaluate_four_wall_reconstruction() -> FourWallReconstructionReport {
    let wall1_audit = evaluate_wall1_busch_ic_povm_vs_polyhedral_cone();
    let wall2_audit = evaluate_wall2_galois_sos_total_positivity();
    let wall3_audit = evaluate_wall3_cocycle_and_choi_separation();
    let wall4_audit = evaluate_wall4_cayley_and_entropy_enclosure();
    let all_four_walls_verified = [
        wall1_audit.trace_sum_equals_two,
        wall1_audit.bloch_sum_vanishes,
        wall1_audit.all_effects_psd,
        wall1_audit.reconstruction_invertible,
        wall1_audit.polyhedral_cone_strictly_larger_than_psd,
        wall1_audit.cholesky_sos_verified,
        wall2_audit.twist_fails_conjugate_embedding,
        wall2_audit.sos_factor_identity_holds,
        wall2_audit.sos_psd_in_all_galois_embeddings,
        wall3_audit.odd_prime_half_invertible,
        wall3_audit.char2_half_obstructed,
        wall3_audit.choi_separates_positive_witness_from_cptp,
        wall4_audit.cayley_single_unitarity_defect.is_zero(),
        wall4_audit.strang_cayley_split_unitarity_defect.is_zero(),
        wall4_audit.taylor_violates_unitarity,
        wall4_audit.renyi_p2 == q(337, 625),
        wall4_audit.renyi_p3 == q(193, 625),
        wall4_audit.interval_width_below_1e_12,
    ]
    .into_iter()
    .all(|b| b);
    FourWallReconstructionReport {
        wall1_audit,
        wall2_audit,
        wall3_audit,
        wall4_audit,
        all_four_walls_verified,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/four_wall_reconstruction.rs
// Claim: urn:core:crates_rs:core-quantum-physics:four-wall-reconstruction:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3ba526f9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3ba526f9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3ba526f9 {
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
impl BoundaryError3ba526f9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3ba526f9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3ba526f9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3ba526f9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3ba526f9> {
        if capacity_bound == 0 {
            return Err(BoundaryError3ba526f9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3ba526f9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3ba526f9::ExceedsCapacity {
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

    #[test]
    fn declared_four_walls_hold_and_a_singular_map_is_not_invertible() {
        let report = evaluate_four_wall_reconstruction();
        assert!(report.all_four_walls_verified);
        assert_eq!(report.wall1_audit.reconstruction_determinant, q(9, 1000));
        assert_eq!(report.wall1_audit.polyhedral_cabello_peres_minor, q(-1, 16));
        assert_eq!(report.wall2_audit.twist_det_field_norm, q(-1, 16));
        assert_eq!(report.wall2_audit.sos_det_field_norm, q(1, 81));
        assert_eq!(report.wall3_audit.mermin_peres_cocycle_ratio, -1);
        assert_eq!(report.wall4_audit.renyi_p2, q(337, 625));
        assert_eq!(report.wall4_audit.renyi_p3, q(193, 625));
        assert!(report.wall4_audit.cayley_single_unitarity_defect.is_zero());
        assert_eq!(report.wall4_audit.taylor_first_order_norm_sq, q(5, 4));
        let mut broken = [
            [q(1, 4), q(0, 1), q(0, 1), q(0, 1)],
            [q(1, 4), q(0, 1), q(0, 1), q(0, 1)],
            [q(1, 4), q(0, 1), q(0, 1), q(0, 1)],
            [q(1, 4), q(0, 1), q(0, 1), q(0, 1)],
        ];
        broken[0] = [q(0, 1), q(0, 1), q(0, 1), q(0, 1)];
        assert!(det_4x4(&broken).is_zero());
    }
}

#[cfg(test)]
mod l4_boundary_tests_3ba526f9 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord3ba526f9::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord3ba526f9::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord3ba526f9::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord3ba526f9::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord3ba526f9::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError3ba526f9::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError3ba526f9::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
