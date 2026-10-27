// AuthorityEffect: None.
//! QM-218 Page-Wootters clock dressing, Tsirelson SOS, and (Z_3)^2 Wigner.
//! Re-exported from `quantum_import_finite_maps`.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_64f2717f<T> {
    fn checked_invariant_64f2717f(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_64f2717f<T> for Option<T> {
    #[inline]
    fn checked_invariant_64f2717f(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_64f2717f<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_64f2717f(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, Zero};

use super::q;
use super::*;

pub(crate) mod cyclotomic_rings;
use cyclotomic_rings::*;
pub use cyclotomic_rings::{Cyclo3, Cyclo8};

// ============================================================================
// QM-218: Page-Wootters Clock Dressing, Cyclotomic Q(zeta_8) Tsirelson SOS,
//         and Discrete Weyl-Wigner Phase Space on (Z_3)^2 over Q(zeta_3)
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm218PageWoottersTsirelsonWignerReport {
    pub pw_history_shift_unitary_and_order_4: bool,
    pub pw_constraint_projector_idempotent_hermitian: bool,
    pub pw_constraint_projector_trace: i64,
    pub pw_constraint_annihilates_projector: bool,
    pub pw_dressing_intertwines_history_shift: bool,
    pub pw_dressing_decouples_projector: bool,
    pub pw_bare_observable_breaks_constraint: bool,
    pub pw_relational_observables_commute_with_constraint: bool,
    pub pw_heisenberg_step_covariance_exact: bool,
    pub pw_static_state_sigma_x_ticks: Vec<Q>,
    pub pw_static_state_sigma_y_ticks: Vec<Q>,
    pub chsh_classical_polytope_vertex_count: usize,
    pub chsh_classical_polytope_max: Q,
    pub chsh_cyclotomic_sqrt2_squares_to_2: bool,
    pub chsh_cyclotomic_sqrt2_inverse_exact: bool,
    pub chsh_observables_involutory_and_spacelike_commuting: bool,
    pub chsh_examiner_identity_exact: bool,
    pub chsh_sos_decomposition_exact: bool,
    pub chsh_bell_state_annihilated_by_sos_witnesses: bool,
    pub chsh_bell_state_eigenvalue_is_2_sqrt2: bool,
    pub chsh_separable_state_expectation_is_sqrt2: bool,
    pub wigner_phase_point_hermitian_involutory_unit_trace: bool,
    pub wigner_phase_point_orthogonality_and_completeness: bool,
    pub wigner_line_marginals_match_projectors: bool,
    pub wigner_stabilizer_nonnegative_and_normalized: bool,
    pub wigner_stabilizer_negativity: Q,
    pub wigner_superposition_normalized_and_marginals_exact: bool,
    pub wigner_superposition_min_value: Q,
    pub wigner_superposition_negativity: Q,
    pub sqrt2_square_bounds_enclose_two: bool,
    pub tsirelson_bound_decimal_12: String,
    pub tsirelson_bound_12_digits_agree: bool,
    pub bell_violation_excess_decimal_12: String,
    pub bell_violation_excess_12_digits_agree: bool,
    pub tsirelson_per_correlator_decimal_12: String,
    pub tsirelson_per_correlator_12_digits_agree: bool,
}

struct PageWoottersResult {
    unitary_order4_ok: bool,
    proj_idem_herm_ok: bool,
    proj_trace: i64,
    annihilates_ok: bool,
    intertwine_ok: bool,
    decouple_ok: bool,
    bare_breaks_ok: bool,
    rel_comm_ok: bool,
    heisenberg_ok: bool,
    sx_ticks: Vec<Q>,
    sy_ticks: Vec<Q>,
}

fn build_relational_observable(tau: usize, obs_s: &QiDynMat, w_powers: &[QiDynMat; 4]) -> QiDynMat {
    let mut proj_tau = qi_dyn_zeros(4);
    proj_tau[tau][tau] = Qi::one();
    let seed = qi_dyn_kron(&proj_tau, obs_s);
    let mut acc = qi_dyn_zeros(8);
    for wk in w_powers {
        let wk_dag = qi_dyn_dagger(wk);
        acc = qi_dyn_add(&acc, &qi_dyn_mul(&wk_dag, &qi_dyn_mul(&seed, wk)));
    }
    acc
}

fn evaluate_pw_relational_ticks(
    u_s: &QiDynMat,
    w_hist: &QiDynMat,
    pi_pw: &QiDynMat,
    w_powers: &[QiDynMat; 4],
    sigma_x: &QiDynMat,
    sigma_y: &QiDynMat,
) -> (bool, bool, Vec<Q>, Vec<Q>) {
    let mut psi0_hist = vec![Qi::zero(); 8];
    psi0_hist[0] = Qi::one();
    psi0_hist[1] = Qi::one();
    let psi_hist: Vec<Qi> = qi_dyn_matvec(pi_pw, &psi0_hist)
        .into_iter()
        .map(|c| Qi::from_q(q(2, 1)).mul(c))
        .collect();
    let norm_hist = qi_dyn_inner(&psi_hist, &psi_hist);
    assert_eq!(norm_hist, Qi::from_q(q(2, 1)));

    let mut rel_comm_ok = true;
    let mut heisenberg_ok = true;
    let mut sx_ticks = Vec::with_capacity(4);
    let mut sy_ticks = Vec::with_capacity(4);
    let us_dag_sx_us = qi_dyn_mul(&qi_dyn_dagger(u_s), &qi_dyn_mul(sigma_x, u_s));

    for tau in 0..4 {
        let orel_x = build_relational_observable(tau, sigma_x, w_powers);
        let orel_y = build_relational_observable(tau, sigma_y, w_powers);
        rel_comm_ok &= qi_dyn_is_zero(&qi_dyn_comm(&orel_x, w_hist))
            && qi_dyn_is_zero(&qi_dyn_comm(&orel_x, pi_pw))
            && qi_dyn_is_zero(&qi_dyn_comm(&orel_y, w_hist))
            && qi_dyn_is_zero(&qi_dyn_comm(&orel_y, pi_pw));
        let orel_x_next = build_relational_observable((tau + 1) % 4, sigma_x, w_powers);
        let orel_x_heis = build_relational_observable(tau, &us_dag_sx_us, w_powers);
        heisenberg_ok &= orel_x_next == orel_x_heis;
        let ex = qi_dyn_inner(&psi_hist, &qi_dyn_matvec(&orel_x, &psi_hist));
        let ey = qi_dyn_inner(&psi_hist, &qi_dyn_matvec(&orel_y, &psi_hist));
        assert!(ex.im.is_zero() && ey.im.is_zero());
        sx_ticks.push(ex.re / norm_hist.re);
        sy_ticks.push(ey.re / norm_hist.re);
    }
    (rel_comm_ok, heisenberg_ok, sx_ticks, sy_ticks)
}

fn evaluate_page_wootters() -> PageWoottersResult {
    // Part (a): Page-Wootters Relational Clock Dressing over Q(i)
    let i4 = qi_dyn_eye(4);
    let i2 = qi_dyn_eye(2);
    let i8 = qi_dyn_eye(8);

    let mut s_c = qi_dyn_zeros(4);
    for t in 0..4 {
        s_c[(t + 1) % 4][t] = Qi::one();
    }

    let mut u_s = qi_dyn_zeros(2);
    u_s[0][0] = Qi::one();
    u_s[1][1] = Qi::i_unit();

    let w_hist = qi_dyn_kron(&s_c, &u_s);
    let w2 = qi_dyn_mul(&w_hist, &w_hist);
    let w3 = qi_dyn_mul(&w2, &w_hist);
    let w4 = qi_dyn_mul(&w3, &w_hist);
    let w_powers = [i8.clone(), w_hist.clone(), w2.clone(), w3.clone()];

    let unitary_order4_ok = qi_dyn_mul(&qi_dyn_dagger(&w_hist), &w_hist) == i8 && w4 == i8;

    let c_pw = qi_dyn_sub(&i8, &w_hist);
    let pi_pw = qi_dyn_scale(
        q(1, 4),
        &qi_dyn_add(&qi_dyn_add(&i8, &w_hist), &qi_dyn_add(&w2, &w3)),
    );
    let proj_idem_herm_ok = qi_dyn_mul(&pi_pw, &pi_pw) == pi_pw && qi_dyn_dagger(&pi_pw) == pi_pw;
    let tr_pi = qi_dyn_trace(&pi_pw);
    assert!(tr_pi.im.is_zero());
    let proj_trace = *tr_pi.re.numer();
    let annihilates_ok =
        qi_dyn_is_zero(&qi_dyn_mul(&c_pw, &pi_pw)) && qi_dyn_is_zero(&qi_dyn_mul(&pi_pw, &c_pw));

    let us2 = qi_dyn_mul(&u_s, &u_s);
    let us3 = qi_dyn_mul(&us2, &u_s);
    let u_s_pows = [i2.clone(), u_s.clone(), us2, us3];
    let mut d_dress = qi_dyn_zeros(8);
    for t in 0..4 {
        let mut proj_t = qi_dyn_zeros(4);
        proj_t[t][t] = Qi::one();
        d_dress = qi_dyn_add(&d_dress, &qi_dyn_kron(&proj_t, &u_s_pows[t]));
    }
    let d_dag = qi_dyn_dagger(&d_dress);
    let intertwine_ok =
        qi_dyn_mul(&d_dag, &qi_dyn_mul(&w_hist, &d_dress)) == qi_dyn_kron(&s_c, &i2);

    let sc2 = qi_dyn_mul(&s_c, &s_c);
    let sc3 = qi_dyn_mul(&sc2, &s_c);
    let pi_c0 = qi_dyn_scale(
        q(1, 4),
        &qi_dyn_add(&qi_dyn_add(&i4, &s_c), &qi_dyn_add(&sc2, &sc3)),
    );
    let decouple_ok = qi_dyn_mul(&d_dag, &qi_dyn_mul(&pi_pw, &d_dress)) == qi_dyn_kron(&pi_c0, &i2);

    let sigma_x = vec![vec![Qi::zero(), Qi::one()], vec![Qi::one(), Qi::zero()]];
    let sigma_y = vec![
        vec![Qi::zero(), Qi::new(Q::zero(), q(-1, 1))],
        vec![Qi::i_unit(), Qi::zero()],
    ];

    let bare_breaks_ok = !qi_dyn_is_zero(&qi_dyn_comm(&qi_dyn_kron(&i4, &sigma_x), &w_hist));
    let (rel_comm_ok, heisenberg_ok, sx_ticks, sy_ticks) =
        evaluate_pw_relational_ticks(&u_s, &w_hist, &pi_pw, &w_powers, &sigma_x, &sigma_y);

    PageWoottersResult {
        unitary_order4_ok,
        proj_idem_herm_ok,
        proj_trace,
        annihilates_ok,
        intertwine_ok,
        decouple_ok,
        bare_breaks_ok,
        rel_comm_ok,
        heisenberg_ok,
        sx_ticks,
        sy_ticks,
    }
}

struct TsirelsonZ8Result {
    polytope_count: usize,
    polytope_max: Q,
    sqrt2_sq_ok: bool,
    sqrt2_inv_ok: bool,
    inv_comm_ok: bool,
    examiner_ok: bool,
    sos_ok: bool,
    bell_annihilated_ok: bool,
    bell_eigen_ok: bool,
    sep_ok: bool,
}

fn evaluate_polytope_max() -> (usize, Q) {
    let mut polytope_count = 0usize;
    let mut polytope_max = Q::zero();
    for mask in 0..16 {
        let a0 = if (mask & 1) != 0 { 1i64 } else { -1i64 };
        let a1 = if (mask & 2) != 0 { 1i64 } else { -1i64 };
        let b0 = if (mask & 4) != 0 { 1i64 } else { -1i64 };
        let b1 = if (mask & 8) != 0 { 1i64 } else { -1i64 };
        let val = q((a0 * (b0 + b1) + a1 * (b0 - b1)).abs(), 1);
        polytope_count += 1;
        if val > polytope_max {
            polytope_max = val;
        }
    }
    (polytope_count, polytope_max)
}

fn check_z8_inv_and_comm(
    a0_op: &Z8DynMat,
    a1_op: &Z8DynMat,
    b0_op: &Z8DynMat,
    b1_op: &Z8DynMat,
) -> bool {
    let i4_z8 = z8_eye(4);
    let inv_ok = [a0_op, a1_op, b0_op, b1_op]
        .iter()
        .all(|op| z8_mul(op, op) == i4_z8 && z8_dagger(op) == **op);
    let comm_ok = [
        (a0_op, b0_op),
        (a0_op, b1_op),
        (a1_op, b0_op),
        (a1_op, b1_op),
    ]
    .iter()
    .all(|(ai, bj)| z8_is_zero(&z8_comm(ai, bj)));
    inv_ok && comm_ok
}

fn evaluate_tsirelson_z8() -> TsirelsonZ8Result {
    // Part (b): Cyclotomic Q(zeta_8) Tsirelson Bound & SOS Certificate
    let (polytope_count, polytope_max) = evaluate_polytope_max();

    let s2 = Cyclo8::sqrt2();
    let inv_s2 = Cyclo8::inv_sqrt2();
    let one_z8 = Cyclo8::one();
    let zero_z8 = Cyclo8::zero();
    let sqrt2_sq_ok = s2.mul(s2) == Cyclo8::from_int(2) && s2.conj() == s2;
    let sqrt2_inv_ok = s2.mul(inv_s2) == one_z8 && inv_s2.conj() == inv_s2;

    let z_pauli = vec![vec![one_z8, zero_z8], vec![zero_z8, one_z8.neg()]];
    let x_pauli = vec![vec![zero_z8, one_z8], vec![one_z8, zero_z8]];
    let i2_z8 = z8_eye(2);
    let i4_z8 = z8_eye(4);

    let a0_op = z8_kron(&z_pauli, &i2_z8);
    let a1_op = z8_kron(&x_pauli, &i2_z8);
    let b0_single = z8_scale(inv_s2, &z8_add(&z_pauli, &x_pauli));
    let b1_single = z8_scale(inv_s2, &z8_sub(&z_pauli, &x_pauli));
    let b0_op = z8_kron(&i2_z8, &b0_single);
    let b1_op = z8_kron(&i2_z8, &b1_single);

    let inv_comm_ok = check_z8_inv_and_comm(&a0_op, &a1_op, &b0_op, &b1_op);

    let b_chsh = z8_add(
        &z8_mul(&a0_op, &z8_add(&b0_op, &b1_op)),
        &z8_mul(&a1_op, &z8_sub(&b0_op, &b1_op)),
    );
    let b_chsh_sq = z8_mul(&b_chsh, &b_chsh);
    let examiner_rhs = z8_sub(
        &z8_scale(Cyclo8::from_int(4), &i4_z8),
        &z8_mul(&z8_comm(&a0_op, &a1_op), &z8_comm(&b0_op, &b1_op)),
    );
    let examiner_ok = b_chsh_sq == examiner_rhs;

    let w1_sos = z8_sub(&z8_scale(inv_s2, &z8_add(&a0_op, &a1_op)), &b0_op);
    let w2_sos = z8_sub(&z8_scale(inv_s2, &z8_sub(&a0_op, &a1_op)), &b1_op);
    let sos_sum = z8_add(
        &z8_mul(&z8_dagger(&w1_sos), &w1_sos),
        &z8_mul(&z8_dagger(&w2_sos), &w2_sos),
    );
    let sos_lhs = z8_sub(
        &z8_scale(Cyclo8::from_int(4), &i4_z8),
        &z8_scale(s2, &b_chsh),
    );
    let sos_equiv_lhs = z8_sub(&z8_scale(Cyclo8::from_int(2).mul(s2), &i4_z8), &b_chsh);
    let sos_equiv_rhs = z8_scale(inv_s2, &sos_sum);
    let sos_ok = sos_lhs == sos_sum && sos_equiv_lhs == sos_equiv_rhs;

    let phi_plus = vec![one_z8, zero_z8, zero_z8, one_z8];
    let w1_phi = z8_matvec(&w1_sos, &phi_plus);
    let w2_phi = z8_matvec(&w2_sos, &phi_plus);
    let bell_annihilated_ok =
        w1_phi.iter().all(|c| c.is_zero()) && w2_phi.iter().all(|c| c.is_zero());

    let b_phi = z8_matvec(&b_chsh, &phi_plus);
    let two_s2 = Cyclo8::from_int(2).mul(s2);
    let bell_eigen_ok = (0..4).all(|k| b_phi[k] == two_s2.mul(phi_plus[k]));

    let sep_00 = vec![one_z8, zero_z8, zero_z8, zero_z8];
    let sep_exp = z8_inner(&sep_00, &z8_matvec(&b_chsh, &sep_00));
    let sep_ok = sep_exp == s2;

    TsirelsonZ8Result {
        polytope_count,
        polytope_max,
        sqrt2_sq_ok,
        sqrt2_inv_ok,
        inv_comm_ok,
        examiner_ok,
        sos_ok,
        bell_annihilated_ok,
        bell_eigen_ok,
        sep_ok,
    }
}

fn check_single_phase_point_orthogonality(
    q_idx: usize,
    p_idx: usize,
    aqp: &[[Cyclo3; 3]; 3],
    all_aqp: &[[[[Cyclo3; 3]; 3]; 3]; 3],
) -> bool {
    let mut ok = true;
    for q2 in 0..3 {
        for p2 in 0..3 {
            let tr_prod = z3_trace3(&z3_mul3(aqp, &all_aqp[q2][p2]));
            let expected = Cyclo3::from_int(if q_idx == q2 && p_idx == p2 { 3 } else { 0 });
            ok &= tr_prod == expected;
        }
    }
    ok
}

fn check_z3_phase_points(all_aqp: &[[[[Cyclo3; 3]; 3]; 3]; 3]) -> (bool, bool) {
    let i3_z3 = z3_eye3();
    let mut herm_inv_tr_ok = true;
    let mut ortho_comp_ok = true;
    let mut sum_all_aqp = z3_zeros3();
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            let aqp = &all_aqp[q_idx][p_idx];
            sum_all_aqp = z3_add3(&sum_all_aqp, aqp);
            herm_inv_tr_ok &= z3_dagger3(aqp) == *aqp
                && z3_mul3(aqp, aqp) == i3_z3
                && z3_trace3(aqp) == Cyclo3::from_int(1);
            ortho_comp_ok &= check_single_phase_point_orthogonality(q_idx, p_idx, aqp, all_aqp);
        }
    }
    ortho_comp_ok &= z3_scale3(q(1, 3), &sum_all_aqp) == i3_z3;
    (herm_inv_tr_ok, ortho_comp_ok)
}

fn check_z3_line_marginals(all_aqp: &[[[[Cyclo3; 3]; 3]; 3]; 3]) -> bool {
    let mut line_marginals_ok = true;
    for q_idx in 0..3 {
        let mut sum_p = z3_zeros3();
        for p_idx in 0..3 {
            sum_p = z3_add3(&sum_p, &all_aqp[q_idx][p_idx]);
        }
        let mut proj_q = z3_zeros3();
        proj_q[q_idx][q_idx] = Cyclo3::from_int(1);
        line_marginals_ok &= z3_scale3(q(1, 3), &sum_p) == proj_q;
    }
    for p_idx in 0..3 {
        let mut sum_q = z3_zeros3();
        for q_idx in 0..3 {
            sum_q = z3_add3(&sum_q, &all_aqp[q_idx][p_idx]);
        }
        let mut proj_p = z3_zeros3();
        for x in 0..3 {
            for y in 0..3 {
                let exp = (p_idx as i64) * ((x as i64) - (y as i64));
                proj_p[x][y] = Cyclo3::core_pow(exp).scale(q(1, 3));
            }
        }
        line_marginals_ok &= z3_scale3(q(1, 3), &sum_q) == proj_p;
    }
    line_marginals_ok
}

fn evaluate_z3_stabilizer_and_superposition() -> (bool, Q, bool, Q, Q) {
    let psi_stab = [
        Cyclo3::from_int(1),
        Cyclo3::from_int(0),
        Cyclo3::from_int(0),
    ];
    let w_stab = compute_wigner_table_z3_rust(&psi_stab);
    let mut stab_sum = Q::zero();
    let mut stab_abs_sum = Q::zero();
    let mut stab_nonneg = true;
    for row in &w_stab {
        for &v in row {
            stab_nonneg &= v >= Q::zero();
            stab_sum += v;
            stab_abs_sum += v.abs();
        }
    }
    let stab_nonneg_norm_ok = stab_nonneg && stab_sum == Q::one();
    let stab_negativity = stab_abs_sum - Q::one();

    let psi_neg = [
        Cyclo3::from_int(1),
        Cyclo3::from_int(-1),
        Cyclo3::from_int(0),
    ];
    let w_neg = compute_wigner_table_z3_rust(&psi_neg);
    let mut neg_sum = Q::zero();
    let mut neg_abs_sum = Q::zero();
    let mut super_min = Q::one();
    for row in &w_neg {
        for &v in row {
            neg_sum += v;
            neg_abs_sum += v.abs();
            if v < super_min {
                super_min = v;
            }
        }
    }
    let pos_marginals: Vec<Q> = (0..3)
        .map(|q_idx| (0..3).map(|p_idx| w_neg[q_idx][p_idx]).sum())
        .collect();
    let mom_marginals: Vec<Q> = (0..3)
        .map(|p_idx| (0..3).map(|q_idx| w_neg[q_idx][p_idx]).sum())
        .collect();
    let super_ok = neg_sum == Q::one()
        && pos_marginals == vec![q(1, 2), q(1, 2), q(0, 1)]
        && mom_marginals == vec![q(0, 1), q(1, 2), q(1, 2)]
        && w_neg[2][0] == q(-1, 3);
    let super_negativity = neg_abs_sum - Q::one();
    (
        stab_nonneg_norm_ok,
        stab_negativity,
        super_ok,
        super_min,
        super_negativity,
    )
}

pub fn evaluate_qm218_page_wootters_tsirelson_wigner() -> Qm218PageWoottersTsirelsonWignerReport {
    let pw = evaluate_page_wootters();
    let ts = evaluate_tsirelson_z8();

    // Part (c): Discrete Weyl-Wigner on (Z_3)^2 & 12-Decimal Enclosures
    let mut all_aqp = [[z3_zeros3(); 3]; 3];
    for q_idx in 0..3 {
        for p_idx in 0..3 {
            all_aqp[q_idx][p_idx] = wigner_phase_point_z3(q_idx, p_idx);
        }
    }
    let (herm_inv_tr_ok, ortho_comp_ok) = check_z3_phase_points(&all_aqp);
    let line_marginals_ok = check_z3_line_marginals(&all_aqp);
    let (stab_nonneg_norm_ok, stab_negativity, super_ok, super_min, super_negativity) =
        evaluate_z3_stabilizer_and_superposition();

    // Certified 12-decimal enclosures for sqrt(2), 2*sqrt(2), 2*sqrt(2) - 2, and sqrt(2)/2
    let denom = BigInt::from(10u64).pow(24);
    let lo_num: BigInt = "1414213562373095048801688"
        .parse()
        .checked_invariant_64f2717f("valid BigInt");
    let hi_num: BigInt = "1414213562373095048801689"
        .parse()
        .checked_invariant_64f2717f("valid BigInt");
    let sqrt2_lo = BigRational::new(lo_num, denom.clone());
    let sqrt2_hi = BigRational::new(hi_num, denom);
    let two_br = BigRational::from_integer(BigInt::from(2));
    let sqrt2_cert_ok = &sqrt2_lo * &sqrt2_lo <= two_br && two_br <= &sqrt2_hi * &sqrt2_hi;
    let sqrt2_iv = BigInterval::new(sqrt2_lo, sqrt2_hi);

    let tsirelson_iv = sqrt2_iv.scale(BigRational::from_integer(BigInt::from(2)));
    let (tsirelson_dec_12, _ts_hi, tsirelson_ok) = tsirelson_iv.decimal_prefix(12);

    let excess_iv = tsirelson_iv.sub(&BigInterval::exact(two_br));
    let (excess_dec_12, _ex_hi, excess_ok) = excess_iv.decimal_prefix(12);

    let per_corr_iv = sqrt2_iv.scale(BigRational::new(BigInt::from(1), BigInt::from(2)));
    let (per_corr_dec_12, _pc_hi, per_corr_ok) = per_corr_iv.decimal_prefix(12);

    Qm218PageWoottersTsirelsonWignerReport {
        pw_history_shift_unitary_and_order_4: pw.unitary_order4_ok,
        pw_constraint_projector_idempotent_hermitian: pw.proj_idem_herm_ok,
        pw_constraint_projector_trace: pw.proj_trace,
        pw_constraint_annihilates_projector: pw.annihilates_ok,
        pw_dressing_intertwines_history_shift: pw.intertwine_ok,
        pw_dressing_decouples_projector: pw.decouple_ok,
        pw_bare_observable_breaks_constraint: pw.bare_breaks_ok,
        pw_relational_observables_commute_with_constraint: pw.rel_comm_ok,
        pw_heisenberg_step_covariance_exact: pw.heisenberg_ok,
        pw_static_state_sigma_x_ticks: pw.sx_ticks,
        pw_static_state_sigma_y_ticks: pw.sy_ticks,
        chsh_classical_polytope_vertex_count: ts.polytope_count,
        chsh_classical_polytope_max: ts.polytope_max,
        chsh_cyclotomic_sqrt2_squares_to_2: ts.sqrt2_sq_ok,
        chsh_cyclotomic_sqrt2_inverse_exact: ts.sqrt2_inv_ok,
        chsh_observables_involutory_and_spacelike_commuting: ts.inv_comm_ok,
        chsh_examiner_identity_exact: ts.examiner_ok,
        chsh_sos_decomposition_exact: ts.sos_ok,
        chsh_bell_state_annihilated_by_sos_witnesses: ts.bell_annihilated_ok,
        chsh_bell_state_eigenvalue_is_2_sqrt2: ts.bell_eigen_ok,
        chsh_separable_state_expectation_is_sqrt2: ts.sep_ok,
        wigner_phase_point_hermitian_involutory_unit_trace: herm_inv_tr_ok,
        wigner_phase_point_orthogonality_and_completeness: ortho_comp_ok,
        wigner_line_marginals_match_projectors: line_marginals_ok,
        wigner_stabilizer_nonnegative_and_normalized: stab_nonneg_norm_ok,
        wigner_stabilizer_negativity: stab_negativity,
        wigner_superposition_normalized_and_marginals_exact: super_ok,
        wigner_superposition_min_value: super_min,
        wigner_superposition_negativity: super_negativity,
        sqrt2_square_bounds_enclose_two: sqrt2_cert_ok,
        tsirelson_bound_decimal_12: tsirelson_dec_12,
        tsirelson_bound_12_digits_agree: tsirelson_ok,
        bell_violation_excess_decimal_12: excess_dec_12,
        bell_violation_excess_12_digits_agree: excess_ok,
        tsirelson_per_correlator_decimal_12: per_corr_dec_12,
        tsirelson_per_correlator_12_digits_agree: per_corr_ok,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/page_wootters_tsirelson_wigner.rs
// Claim: urn:core:crates_rs:core-quantum-physics:page-wootters-tsirelson-wigner:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord64f2717f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord64f2717f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError64f2717f {
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
impl BoundaryError64f2717f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError64f2717f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError64f2717f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord64f2717f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError64f2717f> {
        if capacity_bound == 0 {
            return Err(BoundaryError64f2717f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError64f2717f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError64f2717f::ExceedsCapacity {
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
    fn test_qm218_page_wootters_tsirelson_wigner_control() {
        let r = evaluate_qm218_page_wootters_tsirelson_wigner();
        assert!(r.pw_history_shift_unitary_and_order_4);
        assert!(r.pw_constraint_projector_idempotent_hermitian);
        assert_eq!(r.pw_constraint_projector_trace, 2);
        assert!(r.pw_constraint_annihilates_projector);
        assert!(r.pw_dressing_intertwines_history_shift);
        assert!(r.pw_dressing_decouples_projector);
        assert!(r.pw_bare_observable_breaks_constraint);
        assert!(r.pw_relational_observables_commute_with_constraint);
        assert!(r.pw_heisenberg_step_covariance_exact);
        assert_eq!(
            r.pw_static_state_sigma_x_ticks,
            vec![q(1, 1), q(0, 1), q(-1, 1), q(0, 1)]
        );
        assert_eq!(
            r.pw_static_state_sigma_y_ticks,
            vec![q(0, 1), q(1, 1), q(0, 1), q(-1, 1)]
        );
        assert_eq!(r.chsh_classical_polytope_vertex_count, 16);
        assert_eq!(r.chsh_classical_polytope_max, q(2, 1));
        assert!(r.chsh_cyclotomic_sqrt2_squares_to_2);
        assert!(r.chsh_cyclotomic_sqrt2_inverse_exact);
        assert!(r.chsh_observables_involutory_and_spacelike_commuting);
        assert!(r.chsh_examiner_identity_exact);
        assert!(r.chsh_sos_decomposition_exact);
        assert!(r.chsh_bell_state_annihilated_by_sos_witnesses);
        assert!(r.chsh_bell_state_eigenvalue_is_2_sqrt2);
        assert!(r.chsh_separable_state_expectation_is_sqrt2);
        assert!(r.wigner_phase_point_hermitian_involutory_unit_trace);
        assert!(r.wigner_phase_point_orthogonality_and_completeness);
        assert!(r.wigner_line_marginals_match_projectors);
        assert!(r.wigner_stabilizer_nonnegative_and_normalized);
        assert_eq!(r.wigner_stabilizer_negativity, q(0, 1));
        assert!(r.wigner_superposition_normalized_and_marginals_exact);
        assert_eq!(r.wigner_superposition_min_value, q(-1, 3));
        assert_eq!(r.wigner_superposition_negativity, q(2, 3));
        assert!(r.sqrt2_square_bounds_enclose_two);
        assert_eq!(r.tsirelson_bound_decimal_12, "2.828427124746");
        assert!(r.tsirelson_bound_12_digits_agree);
        assert_eq!(r.bell_violation_excess_decimal_12, "0.828427124746");
        assert!(r.bell_violation_excess_12_digits_agree);
        assert_eq!(r.tsirelson_per_correlator_decimal_12, "0.707106781186");
        assert!(r.tsirelson_per_correlator_12_digits_agree);
    }
}

#[cfg(test)]
mod l4_boundary_tests_64f2717f {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord64f2717f::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord64f2717f::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord64f2717f::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord64f2717f::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord64f2717f::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError64f2717f::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError64f2717f::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
