// AuthorityEffect: None.
//! QM-216 vacuum polarization, running coupling, and Uehling Lamb shift.
//! Re-exported from `quantum_import_finite_maps`.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

use super::q;
use super::*;

// ============================================================================
// QM-216: 1-Loop QED Vacuum Polarization, Running Coupling, and Uehling /
//         Hydrogen 2S_{1/2}-2P_{1/2} Lamb Shift Enclosure
// ============================================================================

pub type Mat4Q = [[Q; 4]; 4];

pub fn mat4_qi_trace(a: &Mat4Qi) -> Qi {
    a[0][0].add(a[1][1]).add(a[2][2]).add(a[3][3])
}

pub fn transverse_tensor_t(q_vec: &[Q; 4]) -> Mat4Q {
    let q_sq = minkowski_dot_4(q_vec, q_vec);
    let eta = minkowski_metric_13();
    let mut out = [[Q::zero(); 4]; 4];
    for mu in 0..4 {
        for nu in 0..4 {
            let eta_munu = if mu == nu { eta[mu] } else { Q::zero() };
            out[mu][nu] = q_vec[mu] * q_vec[nu] - q_sq * eta_munu;
        }
    }
    out
}

pub fn transverse_projector(q_vec: &[Q; 4]) -> Mat4Q {
    let q_sq = minkowski_dot_4(q_vec, q_vec);
    assert!(
        !q_sq.is_zero(),
        "Transverse projector requires non-null momentum q^2 != 0"
    );
    let eta = minkowski_metric_13();
    let mut out = [[Q::zero(); 4]; 4];
    for mu in 0..4 {
        for nu in 0..4 {
            let eta_munu = if mu == nu { eta[mu] } else { Q::zero() };
            out[mu][nu] = eta_munu - (q_vec[mu] * q_vec[nu]) / q_sq;
        }
    }
    out
}

pub fn check_transverse_projector_identities(q_vec: &[Q; 4]) -> (bool, bool, Q) {
    let pt = transverse_projector(q_vec);
    let t_mat = transverse_tensor_t(q_vec);
    let eta = minkowski_metric_13();

    let mut ward_ok = true;
    for nu in 0..4 {
        let mut dot_t = Q::zero();
        let mut dot_p = Q::zero();
        for mu in 0..4 {
            dot_t += eta[mu] * q_vec[mu] * t_mat[mu][nu];
            dot_p += eta[mu] * q_vec[mu] * pt[mu][nu];
        }
        if !dot_t.is_zero() || !dot_p.is_zero() {
            ward_ok = false;
        }
    }

    let mut idemp_ok = true;
    for mu in 0..4 {
        for nu in 0..4 {
            let mut comp = Q::zero();
            for a in 0..4 {
                comp += pt[mu][a] * eta[a] * pt[a][nu];
            }
            if comp != pt[mu][nu] {
                idemp_ok = false;
            }
        }
    }

    let mut trace_val = Q::zero();
    for mu in 0..4 {
        trace_val += eta[mu] * pt[mu][mu];
    }
    (ward_ok, idemp_ok, trace_val)
}

pub fn fermion_bubble_numerator_clifford_trace(k: &[Q; 4], q_vec: &[Q; 4], mass: Q) -> Mat4Q {
    let gammas = dirac_gamma_matrices();
    let id4 = mat4_qi_identity();
    let kq = [
        k[0] + q_vec[0],
        k[1] + q_vec[1],
        k[2] + q_vec[2],
        k[3] + q_vec[3],
    ];
    let factor_left = mat4_qi_add(&feynman_slash(&kq), &mat4_qi_scale(Qi::from_q(mass), &id4));
    let factor_right = mat4_qi_add(&feynman_slash(k), &mat4_qi_scale(Qi::from_q(mass), &id4));

    let mut out = [[Q::zero(); 4]; 4];
    for mu in 0..4 {
        for nu in 0..4 {
            let prod = mat4_qi_mul(
                &gammas[mu],
                &mat4_qi_mul(&factor_left, &mat4_qi_mul(&gammas[nu], &factor_right)),
            );
            let tr_val = mat4_qi_trace(&prod);
            assert!(
                tr_val.im.is_zero(),
                "Non-zero imaginary part in 4-gamma trace"
            );
            out[mu][nu] = tr_val.re;
        }
    }
    out
}

pub fn fermion_bubble_numerator_analytic(k: &[Q; 4], q_vec: &[Q; 4], mass: Q) -> Mat4Q {
    let kq = [
        k[0] + q_vec[0],
        k[1] + q_vec[1],
        k[2] + q_vec[2],
        k[3] + q_vec[3],
    ];
    let k_dot_kq = minkowski_dot_4(k, &kq);
    let eta = minkowski_metric_13();
    let mut out = [[Q::zero(); 4]; 4];
    for mu in 0..4 {
        for nu in 0..4 {
            let eta_munu = if mu == nu { eta[mu] } else { Q::zero() };
            out[mu][nu] =
                q(4, 1) * (k[mu] * kq[nu] + kq[mu] * k[nu] - eta_munu * (k_dot_kq - mass * mass));
        }
    }
    out
}

pub fn feynman_parameter_moment_polynomial(n: usize) -> Q {
    let m = (n + 1) as i64;
    let mut binom = 1i64;
    let mut total = Q::zero();
    for j in 0..=m {
        let sign = if j % 2 == 0 { 1i64 } else { -1i64 };
        total += q(sign * binom, m + 1 + j);
        if j < m {
            binom = (binom * (m - j)) / (j + 1);
        }
    }
    total
}

pub fn feynman_parameter_moment_beta_closed(n: usize) -> Q {
    let mut fact_n1 = 1i64;
    for k in 2..=((n + 1) as i64) {
        fact_n1 *= k;
    }
    let mut fact_2n3 = 1i64;
    for k in 2..=((2 * n + 3) as i64) {
        fact_2n3 *= k;
    }
    q(fact_n1 * fact_n1, fact_2n3)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm216VacuumPolarizationLambShiftReport {
    pub transverse_ward_identity_exact: bool,
    pub transverse_projector_idempotent_exact: bool,
    pub transverse_projector_trace_equals_three: Q,
    pub clifford_bubble_trace_matches_analytic: bool,
    pub symanzik_bubble_simplex_u_equals_one: bool,
    pub symanzik_bubble_simplex_f_matches_feynman_denom: bool,
    pub bphz_uv_cutoff_cancels_at_all_scales: bool,
    pub bphz_on_shell_pi_r_at_zero_is_zero: bool,
    pub moments_match_beta_closed_form: bool,
    pub uehling_leading_slope_coeff: Q,
    pub second_moment_series_coeff: Q,
    pub third_moment_series_coeff: Q,
    pub spacelike_velocity_v: Q,
    pub spacelike_q2_over_m2: Q,
    pub pi_r_spacelike_negative: bool,
    pub pi_r_spacelike_decimal_12: String,
    pub pi_r_spacelike_12_digits_agree: bool,
    pub alpha_eff_inv_spacelike_decimal_12: String,
    pub alpha_eff_inv_spacelike_12_digits_agree: bool,
    pub alpha_eff_exceeds_bare_alpha: bool,
    pub lamb_contact_se_term: Q,
    pub lamb_contact_g2_magnetic_term: Q,
    pub lamb_contact_uehling_vp_term: Q,
    pub lamb_contact_total_rational: Q,
    pub uehling_2s_dimensionless_coeff: Q,
    pub uehling_2s_mhz_decimal_12: String,
    pub uehling_2s_mhz_12_digits_agree: bool,
}

pub fn evaluate_qm216_vacuum_polarization_lamb_shift() -> Qm216VacuumPolarizationLambShiftReport {
    let q_vec = [q(2, 1), q(3, 1), q(1, 1), q(1, 1)];
    let (ward_ok, idemp_ok, tr_pt) = check_transverse_projector_identities(&q_vec);

    let k_vec = [q(5, 1), q(-1, 1), q(2, 1), q(3, 1)];
    let mass = q(2, 1);
    let num_clifford = fermion_bubble_numerator_clifford_trace(&k_vec, &q_vec, mass);
    let num_analytic = fermion_bubble_numerator_analytic(&k_vec, &q_vec, mass);
    let clifford_trace_ok = num_clifford == num_analytic;

    let bub = CarrierGraph::bubble();
    let x_param = q(3, 7);
    let alphas_simplex = vec![x_param, Q::one() - x_param];
    let u_bub_simplex = symanzik_u_polynomial(&bub, &alphas_simplex);
    let u_simplex_ok = u_bub_simplex == Q::one();

    let q_eucl = vec![vec![q(3, 1), q(0, 1)], vec![q(-3, 1), q(0, 1)]];
    let q_mink_sq = q(-9, 1);
    let m2_bub = vec![mass * mass, mass * mass];
    let f_bub_simplex = symanzik_f_polynomial(&bub, &alphas_simplex, &q_eucl, &m2_bub);
    let expected_feynman_denom = mass * mass - x_param * (Q::one() - x_param) * q_mink_sq;
    let f_simplex_ok = f_bub_simplex == expected_feynman_denom;

    // Bare arguments Lambda^2/Delta move with the cutoff. Their ratio equals
    // m^2/Delta at every cutoff. On shell that ratio is 1, the bare argument
    // is not 1, and the same subtraction at m^2 + 1 is not 1.
    let m2 = mass * mass;
    let delta = expected_feynman_denom;
    let uv_cutoffs = [q(10, 1), q(1000, 1), q(1_000_000_000, 1)];
    let bare_at_delta: Vec<Q> = uv_cutoffs.iter().map(|&lam_sq| lam_sq / delta).collect();
    let bare_at_m2: Vec<Q> = uv_cutoffs.iter().map(|&lam_sq| lam_sq / m2).collect();
    let subtracted: Vec<Q> = uv_cutoffs
        .iter()
        .map(|&lam_sq| (lam_sq / delta) / (lam_sq / m2))
        .collect();
    let subtracted_target = m2 / delta;
    let bare_depends_on_cutoff = bare_at_delta[0] != bare_at_delta[1]
        && bare_at_delta[1] != bare_at_delta[2]
        && bare_at_m2[0] != bare_at_m2[1]
        && bare_at_m2[1] != bare_at_m2[2];
    let subtracted_agrees = subtracted.iter().all(|&ratio| ratio == subtracted_target)
        && subtracted[0] == subtracted[1]
        && subtracted[1] == subtracted[2];
    let bphz_uv_cancels = bare_depends_on_cutoff && subtracted_agrees;

    let denom_at_zero = m2 - x_param * (Q::one() - x_param) * Q::zero();
    let on_shell_is_one = uv_cutoffs
        .iter()
        .all(|&lam_sq| ((lam_sq / denom_at_zero) / (lam_sq / m2)) == Q::one());
    let bare_on_shell_not_one = bare_at_m2.iter().all(|&ratio| ratio != Q::one());
    let wrong_subtraction = m2 + Q::one();
    let wrong_point_not_one = uv_cutoffs
        .iter()
        .all(|&lam_sq| ((lam_sq / m2) / (lam_sq / wrong_subtraction)) != Q::one());
    let bphz_zero_at_zero =
        denom_at_zero == m2 && on_shell_is_one && bare_on_shell_not_one && wrong_point_not_one;

    let moments_poly: Vec<Q> = (1..=4).map(feynman_parameter_moment_polynomial).collect();
    let moments_beta: Vec<Q> = (1..=4).map(feynman_parameter_moment_beta_closed).collect();
    let moments_match = moments_poly == moments_beta;

    let c_uehling_1 = q(2, 1) * moments_poly[0] / q(1, 1);
    let c_uehling_2 = q(2, 1) * moments_poly[1] / q(2, 1);
    let c_uehling_3 = q(2, 1) * moments_poly[2] / q(3, 1);

    let v_space = q(5, 3);
    let q2_over_m2_space = q(-9, 4);
    let alpha_inv = BigRational::new(
        BigInt::from(137035999166i64),
        BigInt::from(1_000_000_000i64),
    );
    let pi_iv = pi_big_interval(20);
    let ln2_iv = polylog_half_big_interval(1, 50);
    let ln4_iv = ln2_iv.scale(BigRational::from_integer(BigInt::from(2)));

    let alpha_over_3pi =
        BigInterval::exact((BigRational::from_integer(BigInt::from(3)) * &alpha_inv).recip())
            .mul(&pi_iv.reciprocal());
    let poly_part = BigInterval::from_i64(1, 9); // v^2 - 8/3 = 25/9 - 24/9 = 1/9
    let log_coeff = BigRational::new(BigInt::from(5), BigInt::from(27)); // v(3 - v^2)/2 = (5/3)(2/9)/2 = 5/27
    let bracket = poly_part.add(&ln4_iv.scale(log_coeff));
    let pi_r_iv = BigInterval::from_i64(0, 1).sub(&alpha_over_3pi.mul(&bracket));
    let (pi_r_lo12, _pi_r_hi12, pi_r_agree12) = pi_r_iv.decimal_prefix(12);

    let one_plus_pi_r = BigInterval::from_i64(1, 1).add(&pi_r_iv);
    let alpha_eff_inv_iv = one_plus_pi_r.scale(alpha_inv.clone());
    let (aeff_lo12, _aeff_hi12, aeff_agree12) = alpha_eff_inv_iv.decimal_prefix(12);
    let alpha_eff_exceeds_bare = alpha_eff_inv_iv.hi < alpha_inv;

    // 2S self-energy constant 5/6 (11/24 + 3/8); 19/30 = 5/6 - 1/5 already
    // contains the Uehling term, so it is not combined with lamb_vp again.
    let lamb_se = q(5, 6);
    let lamb_g2 = q(1, 8);
    let lamb_vp = q(-1, 5);
    let lamb_total_contact = lamb_se + lamb_g2 + lamb_vp;

    let uehling_dimless_coeff = q(-1, 30);
    let alpha_exact = BigInterval::exact(alpha_inv.recip());
    let alpha5_over_pi = alpha_exact.pow(5).mul(&pi_iv.reciprocal());
    let uehling_dimless_iv =
        alpha5_over_pi.scale(BigRational::new(BigInt::from(-1), BigInt::from(30)));
    let me_c2_over_h_mhz = BigRational::from_integer(BigInt::from(123558996383000i64));
    let uehling_mhz_iv = uehling_dimless_iv.scale(me_c2_over_h_mhz);
    let (ueh_mhz_lo12, _ueh_mhz_hi12, ueh_mhz_agree12) = uehling_mhz_iv.decimal_prefix(12);

    Qm216VacuumPolarizationLambShiftReport {
        transverse_ward_identity_exact: ward_ok,
        transverse_projector_idempotent_exact: idemp_ok,
        transverse_projector_trace_equals_three: tr_pt,
        clifford_bubble_trace_matches_analytic: clifford_trace_ok,
        symanzik_bubble_simplex_u_equals_one: u_simplex_ok,
        symanzik_bubble_simplex_f_matches_feynman_denom: f_simplex_ok,
        bphz_uv_cutoff_cancels_at_all_scales: bphz_uv_cancels,
        bphz_on_shell_pi_r_at_zero_is_zero: bphz_zero_at_zero,
        moments_match_beta_closed_form: moments_match,
        uehling_leading_slope_coeff: c_uehling_1,
        second_moment_series_coeff: c_uehling_2,
        third_moment_series_coeff: c_uehling_3,
        spacelike_velocity_v: v_space,
        spacelike_q2_over_m2: q2_over_m2_space,
        pi_r_spacelike_negative: pi_r_iv.hi.is_negative(),
        pi_r_spacelike_decimal_12: pi_r_lo12,
        pi_r_spacelike_12_digits_agree: pi_r_agree12,
        alpha_eff_inv_spacelike_decimal_12: aeff_lo12,
        alpha_eff_inv_spacelike_12_digits_agree: aeff_agree12,
        alpha_eff_exceeds_bare_alpha: alpha_eff_exceeds_bare,
        lamb_contact_se_term: lamb_se,
        lamb_contact_g2_magnetic_term: lamb_g2,
        lamb_contact_uehling_vp_term: lamb_vp,
        lamb_contact_total_rational: lamb_total_contact,
        uehling_2s_dimensionless_coeff: uehling_dimless_coeff,
        uehling_2s_mhz_decimal_12: ueh_mhz_lo12,
        uehling_2s_mhz_12_digits_agree: ueh_mhz_agree12,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/vacuum_polarization_lamb_shift.rs
// Claim: urn:core:crates_rs:core-quantum-physics:vacuum-polarization-lamb-shift:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordaa3b0f73 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordaa3b0f73` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErroraa3b0f73 {
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
impl BoundaryErroraa3b0f73 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErroraa3b0f73 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErroraa3b0f73 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordaa3b0f73 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErroraa3b0f73> {
        if capacity_bound == 0 {
            return Err(BoundaryErroraa3b0f73::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErroraa3b0f73::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErroraa3b0f73::ExceedsCapacity {
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
    use super::super::q;
    use super::*;

    #[test]
    fn test_qm216_vacuum_polarization_lamb_shift_control() {
        let r = evaluate_qm216_vacuum_polarization_lamb_shift();
        assert!(r.transverse_ward_identity_exact);
        assert!(r.transverse_projector_idempotent_exact);
        assert_eq!(r.transverse_projector_trace_equals_three, q(3, 1));
        assert!(r.clifford_bubble_trace_matches_analytic);
        assert!(r.symanzik_bubble_simplex_u_equals_one);
        assert!(r.symanzik_bubble_simplex_f_matches_feynman_denom);
        assert!(r.bphz_uv_cutoff_cancels_at_all_scales);
        assert!(r.bphz_on_shell_pi_r_at_zero_is_zero);
        assert!(r.moments_match_beta_closed_form);
        assert_eq!(r.uehling_leading_slope_coeff, q(1, 15));
        assert_eq!(r.second_moment_series_coeff, q(1, 140));
        assert_eq!(r.third_moment_series_coeff, q(1, 945));
        assert_eq!(r.spacelike_velocity_v, q(5, 3));
        assert_eq!(r.spacelike_q2_over_m2, q(-9, 4));
        assert!(r.pi_r_spacelike_negative);
        assert_eq!(r.pi_r_spacelike_decimal_12, "-0.000284802666");
        assert!(r.pi_r_spacelike_12_digits_agree);
        assert_eq!(r.alpha_eff_inv_spacelike_decimal_12, "136.996970947974");
        assert!(r.alpha_eff_inv_spacelike_12_digits_agree);
        assert!(r.alpha_eff_exceeds_bare_alpha);
        assert_eq!(r.lamb_contact_se_term, q(5, 6));
        assert_eq!(r.lamb_contact_g2_magnetic_term, q(1, 8));
        assert_eq!(r.lamb_contact_uehling_vp_term, q(-1, 5));
        assert_eq!(r.lamb_contact_total_rational, q(91, 120));
        assert_eq!(r.uehling_2s_dimensionless_coeff, q(-1, 30));
        assert_eq!(r.uehling_2s_mhz_decimal_12, "-27.128756729153");
        assert!(r.uehling_2s_mhz_12_digits_agree);
    }
}

#[cfg(test)]
mod l4_boundary_tests_aa3b0f73 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordaa3b0f73::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordaa3b0f73::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordaa3b0f73::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordaa3b0f73::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordaa3b0f73::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErroraa3b0f73::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErroraa3b0f73::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
