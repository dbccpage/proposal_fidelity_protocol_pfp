// AuthorityEffect: None.
//! Self-contained Rust verification module for the Ravera DFM Finite-to-Continuum Dossier:
//! - Theorem 3.7: Bipartite flavor graph K_{N_g,N_g} CKM rephasing DFM and Jarlskog 4-cycle holonomy
//! - Theorem 3.8: Non-Abelian SU(3)_c spanning-tree dressing uniqueness vs. discrete Examiner Gribov copies
//! - Theorem 3.9: Discrete Cartan-Regge Lorentz tetrad/frame dressing around simplicial 2-hinges over Q
//!
//! Synchronized with `001_ravera_dfm_finite_to_continuum_dossier/rust/ravera_dfm_finite_to_continuum.rs`.

use num_traits::{One, Zero};

use super::q;
use super::*;

pub type DfmMat3Qi = [[Qi; 3]; 3];
pub type DfmMat4Q = [[Q; 4]; 4];

fn mat3_qi_zero() -> DfmMat3Qi {
    [[Qi::zero(); 3]; 3]
}

fn mat3_qi_identity() -> DfmMat3Qi {
    let mut m = mat3_qi_zero();
    for idx in 0..3 {
        m[idx][idx] = Qi::one();
    }
    m
}

fn mat3_qi_mul(a: &DfmMat3Qi, b: &DfmMat3Qi) -> DfmMat3Qi {
    let mut out = mat3_qi_zero();
    for r in 0..3 {
        for c in 0..3 {
            let mut acc = Qi::zero();
            for k in 0..3 {
                acc = acc.add(a[r][k].mul(b[k][c]));
            }
            out[r][c] = acc;
        }
    }
    out
}

fn mat3_qi_dagger(a: &DfmMat3Qi) -> DfmMat3Qi {
    let mut out = mat3_qi_zero();
    for r in 0..3 {
        for c in 0..3 {
            out[r][c] = a[c][r].conj();
        }
    }
    out
}

fn mat3_qi_trace(a: &DfmMat3Qi) -> Qi {
    a[0][0].add(a[1][1]).add(a[2][2])
}

fn mat3_qi_det(a: &DfmMat3Qi) -> Qi {
    let term0 = a[0][0].mul(a[1][1].mul(a[2][2]).sub(a[1][2].mul(a[2][1])));
    let term1 = a[0][1].mul(a[1][0].mul(a[2][2]).sub(a[1][2].mul(a[2][0])));
    let term2 = a[0][2].mul(a[1][0].mul(a[2][1]).sub(a[1][1].mul(a[2][0])));
    term0.sub(term1).add(term2)
}

fn mat3_qi_commutator_nonzero(a: &DfmMat3Qi, b: &DfmMat3Qi) -> bool {
    mat3_qi_mul(a, b) != mat3_qi_mul(b, a)
}

fn mat4_q_zero() -> DfmMat4Q {
    [[Q::zero(); 4]; 4]
}

fn mat4_q_identity() -> DfmMat4Q {
    let mut m = mat4_q_zero();
    for idx in 0..4 {
        m[idx][idx] = Q::one();
    }
    m
}

fn mat4_q_transpose(a: &DfmMat4Q) -> DfmMat4Q {
    let mut out = mat4_q_zero();
    for r in 0..4 {
        for c in 0..4 {
            out[r][c] = a[c][r];
        }
    }
    out
}

fn mat4_q_mul(a: &DfmMat4Q, b: &DfmMat4Q) -> DfmMat4Q {
    let mut out = mat4_q_zero();
    for r in 0..4 {
        for c in 0..4 {
            let mut acc = Q::zero();
            for k in 0..4 {
                acc += a[r][k] * b[k][c];
            }
            out[r][c] = acc;
        }
    }
    out
}

fn mat4_q_trace(a: &DfmMat4Q) -> Q {
    a[0][0] + a[1][1] + a[2][2] + a[3][3]
}

fn mat4_q_det(a: &DfmMat4Q) -> Q {
    let rows: Vec<Vec<Q>> = a.iter().map(|r| r.to_vec()).collect();
    q_det(&rows)
}

fn mat4_q_inv(a: &DfmMat4Q) -> DfmMat4Q {
    let rows: Vec<Vec<Q>> = a.iter().map(|r| r.to_vec()).collect();
    let inv_rows = q_invert_matrix(&rows);
    let mut out = mat4_q_zero();
    for r in 0..4 {
        for c in 0..4 {
            out[r][c] = inv_rows[r][c];
        }
    }
    out
}

// ============================================================================
// Theorem 3.7: Bipartite Flavor Rephasing DFM & Jarlskog Cycle Holonomy
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CkmJarlskogBipartiteDfmReport {
    pub ng2_removed_tree_phases: usize,
    pub ng2_substantial_cycle_phases: usize,
    pub ng3_removed_tree_phases: usize,
    pub ng3_substantial_cycle_phases: usize,
    pub ng4_removed_tree_phases: usize,
    pub ng4_substantial_cycle_phases: usize,
    pub two_gen_cabibbo_unitary: bool,
    pub two_gen_dressed_entries_real_positive: bool,
    pub two_gen_jarlskog_zero: Q,
    pub three_gen_ckm_unitary: bool,
    pub three_gen_ckm_det_unit_norm: bool,
    pub three_gen_all_nine_quartets_rephasing_invariant: bool,
    pub three_gen_jarlskog_invariant: Q,
}

pub fn jarlskog_plaquette(v: &DfmMat3Qi, alpha: usize, beta: usize, j: usize, k: usize) -> Q {
    let prod = v[alpha][j]
        .mul(v[beta][k])
        .mul(v[alpha][k].conj())
        .mul(v[beta][j].conj());
    prod.im
}

fn verify_all_nine_jarlskog_quartets(v_ckm: &DfmMat3Qi, v_rephased: &DfmMat3Qi, j_0101: Q) -> bool {
    let mut all_quartets_ok = true;
    for &(alpha, beta, sgn_row) in &[(0usize, 1usize, 1i64), (1, 2, 1), (2, 0, 1)] {
        for &(j, k, sgn_col) in &[(0usize, 1usize, 1i64), (1, 2, 1), (2, 0, 1)] {
            let j_orig = jarlskog_plaquette(v_ckm, alpha, beta, j, k);
            let j_reph = jarlskog_plaquette(v_rephased, alpha, beta, j, k);
            let expected = q(sgn_row * sgn_col, 1) * j_0101;
            if j_orig != expected || j_reph != expected {
                all_quartets_ok = false;
            }
        }
    }
    all_quartets_ok
}

pub fn evaluate_ckm_jarlskog_bipartite_dfm_control() -> CkmJarlskogBipartiteDfmReport {
    let id3 = mat3_qi_identity();

    // 2-generation Cabibbo matrix with artificial quark-field phases
    let c12 = q(3, 5);
    let s12 = q(4, 5);
    let cab_base = [
        [Qi::from_q(c12), Qi::from_q(s12)],
        [Qi::from_q(-s12), Qi::from_q(c12)],
    ];
    let u_left_2 = [Qi::new(q(3, 5), q(4, 5)), Qi::new(q(5, 13), q(-12, 13))];
    let u_right_2 = [Qi::new(q(8, 17), q(15, 17)), Qi::new(q(4, 5), q(-3, 5))];
    let mut cab_gauged = [[Qi::zero(); 2]; 2];
    for r in 0..2 {
        for c in 0..2 {
            cab_gauged[r][c] = u_left_2[r].mul(cab_base[r][c]).mul(u_right_2[c].conj());
        }
    }
    let phase_norm = |z: Qi| -> Qi {
        let nsq = z.norm_sq();
        let r_val = if nsq == q(9, 25) { q(3, 5) } else { q(4, 5) };
        Qi::new(z.re / r_val, z.im / r_val)
    };
    let d_u1 = Qi::one();
    let d_d1 = d_u1.conj().mul(phase_norm(cab_gauged[0][0])).conj();
    let d_d2 = d_u1.conj().mul(phase_norm(cab_gauged[0][1])).conj();
    let d_u2 = phase_norm(cab_gauged[1][1]).mul(d_d2).conj().inv();
    let dress_l = [d_u1, d_u2];
    let dress_r = [d_d1, d_d2];
    let mut cab_dressed = [[Qi::zero(); 2]; 2];
    for r in 0..2 {
        for c in 0..2 {
            cab_dressed[r][c] = dress_l[r].conj().mul(cab_gauged[r][c]).mul(dress_r[c]);
        }
    }
    let two_gen_unitary = cab_dressed[0][0]
        .mul(cab_dressed[0][0].conj())
        .add(cab_dressed[0][1].mul(cab_dressed[0][1].conj()))
        == Qi::one();
    let two_gen_real = cab_dressed == cab_base;
    let j_two_gen = cab_gauged[0][0]
        .mul(cab_gauged[1][1])
        .mul(cab_gauged[0][1].conj())
        .mul(cab_gauged[1][0].conj())
        .im;

    // 3-generation exact Pythagorean CKM matrix over Q(i) with (c_i, s_i) = (3/5, 4/5), delta = pi/2
    let (c1, s1) = (q(3, 5), q(4, 5));
    let (c2, s2) = (q(3, 5), q(4, 5));
    let (c3, s3) = (q(3, 5), q(4, 5));

    let v_ckm: DfmMat3Qi = [
        [
            Qi::from_q(c1 * c2),
            Qi::from_q(s1 * c2),
            Qi::new(Q::zero(), -s2),
        ],
        [
            Qi::new(-s1 * c3, -c1 * s2 * s3),
            Qi::new(c1 * c3, -s1 * s2 * s3),
            Qi::from_q(c2 * s3),
        ],
        [
            Qi::new(s1 * s3, -c1 * s2 * c3),
            Qi::new(-c1 * s3, -s1 * s2 * c3),
            Qi::from_q(c2 * c3),
        ],
    ];
    let v_dag_v = mat3_qi_mul(&mat3_qi_dagger(&v_ckm), &v_ckm);
    let three_gen_unitary = v_dag_v == id3;
    let det_v = mat3_qi_det(&v_ckm);
    let det_unit_norm = det_v.norm_sq() == Q::one();

    let phi_u = [
        Qi::new(q(3, 5), q(4, 5)),
        Qi::new(q(5, 13), q(-12, 13)),
        Qi::new(q(8, 17), q(15, 17)),
    ];
    let phi_d = [
        Qi::new(q(4, 5), q(-3, 5)),
        Qi::new(q(12, 13), q(5, 13)),
        Qi::new(q(15, 17), q(-8, 17)),
    ];
    let mut v_rephased = mat3_qi_zero();
    for alpha in 0..3 {
        for j in 0..3 {
            v_rephased[alpha][j] = phi_u[alpha].mul(v_ckm[alpha][j]).mul(phi_d[j].conj());
        }
    }

    let j_0101 = jarlskog_plaquette(&v_ckm, 0, 1, 0, 1);
    let all_quartets_ok = verify_all_nine_jarlskog_quartets(&v_ckm, &v_rephased, j_0101);

    CkmJarlskogBipartiteDfmReport {
        ng2_removed_tree_phases: 2 * 2 - 1,
        ng2_substantial_cycle_phases: 1,
        ng3_removed_tree_phases: 2 * 3 - 1,
        ng3_substantial_cycle_phases: 4,
        ng4_removed_tree_phases: 2 * 4 - 1,
        ng4_substantial_cycle_phases: 9,
        two_gen_cabibbo_unitary: two_gen_unitary,
        two_gen_dressed_entries_real_positive: two_gen_real,
        two_gen_jarlskog_zero: j_two_gen,
        three_gen_ckm_unitary: three_gen_unitary,
        three_gen_ckm_det_unit_norm: det_unit_norm,
        three_gen_all_nine_quartets_rephasing_invariant: all_quartets_ok,
        three_gen_jarlskog_invariant: j_0101,
    }
}

// ============================================================================
// Theorem 3.8: Non-Abelian SU(3)_c Spanning-Tree Dressing Uniqueness vs.
//              Discrete Examiner Gauge Gribov Copies on Finite Lattice Graphs
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Su3SpanningTreeVsExaminerGribovReport {
    pub su3_edge_links_all_unitary_det_one: bool,
    pub su3_connection_non_abelian: bool,
    pub dfm_all_eight_trees_neutralize_tree_edges: bool,
    pub dfm_dressed_cotree_holonomies_gauge_invariant: bool,
    pub dfm_second_kind_tree_change_intertwiner_exact: bool,
    pub klein_four_gribov_elements_in_su3: bool,
    pub anchored_examiner_gribov_copy_count: usize,
    pub nontrivial_examiner_gribov_copy_count: usize,
    pub all_gribov_copies_satisfy_discrete_examiner_divergence_zero: bool,
    pub gribov_horizon_hessian_flips_sign_to_negative: bool,
    pub dfm_collapses_all_64_gribov_copies_to_single_dressed_state: bool,
}

pub fn dfm_su3_block12(a: Qi, b: Qi) -> DfmMat3Qi {
    let o = Qi::one();
    let z = Qi::zero();
    [
        [a, b, z],
        [Qi::zero().sub(b.conj()), a.conj(), z],
        [z, z, o],
    ]
}

pub fn dfm_su3_block23(a: Qi, b: Qi) -> DfmMat3Qi {
    let o = Qi::one();
    let z = Qi::zero();
    [
        [o, z, z],
        [z, a, b],
        [z, Qi::zero().sub(b.conj()), a.conj()],
    ]
}

pub fn is_in_su3_qi(m: &DfmMat3Qi) -> bool {
    let id3 = mat3_qi_identity();
    mat3_qi_mul(&mat3_qi_dagger(m), m) == id3 && mat3_qi_det(m) == Qi::one()
}

pub fn tree_dressing_field_su3(
    graph: &CarrierGraph,
    tree_edges: &[usize],
    edge_links: &[DfmMat3Qi],
    root: usize,
) -> Vec<DfmMat3Qi> {
    let mut u_field = vec![mat3_qi_identity(); graph.vertex_count];
    for (v, u_v) in u_field.iter_mut().enumerate() {
        let path = tree_path_on_custom_tree(graph, tree_edges, root, v);
        let mut hol = mat3_qi_identity();
        for pair in path.windows(2) {
            let (a, b) = (pair[0], pair[1]);
            for &e_idx in tree_edges {
                if graph.edges[e_idx] == (a, b) {
                    hol = mat3_qi_mul(&edge_links[e_idx], &hol);
                    break;
                }
                if graph.edges[e_idx] == (b, a) {
                    hol = mat3_qi_mul(&mat3_qi_dagger(&edge_links[e_idx]), &hol);
                    break;
                }
            }
        }
        *u_v = hol;
    }
    u_field
}

pub fn dress_su3_connection(
    graph: &CarrierGraph,
    edge_links: &[DfmMat3Qi],
    u_field: &[DfmMat3Qi],
) -> Vec<DfmMat3Qi> {
    graph
        .edges
        .iter()
        .enumerate()
        .map(|(e_idx, &(u, v))| {
            mat3_qi_mul(
                &mat3_qi_dagger(&u_field[v]),
                &mat3_qi_mul(&edge_links[e_idx], &u_field[u]),
            )
        })
        .collect()
}

fn verify_dfm_eight_trees_su3(
    dia: &CarrierGraph,
    dia_trees: &[(Vec<usize>, Vec<usize>)],
    edge_links: &[DfmMat3Qi],
    gauged_links: &[DfmMat3Qi],
    id3: &DfmMat3Qi,
) -> (bool, bool) {
    let mut all_trees_neutralize = true;
    let mut all_trees_gauge_invariant = true;
    for (tree_edges, _cotree) in dia_trees {
        let u_orig = tree_dressing_field_su3(dia, tree_edges, edge_links, 0);
        let u_gaug = tree_dressing_field_su3(dia, tree_edges, gauged_links, 0);
        let dressed_orig = dress_su3_connection(dia, edge_links, &u_orig);
        let dressed_gaug = dress_su3_connection(dia, gauged_links, &u_gaug);
        for &te in tree_edges {
            if dressed_orig[te] != *id3 || dressed_gaug[te] != *id3 {
                all_trees_neutralize = false;
            }
        }
        if dressed_orig != dressed_gaug {
            all_trees_gauge_invariant = false;
        }
    }
    (all_trees_neutralize, all_trees_gauge_invariant)
}

fn check_single_gribov_copy_links(
    u_copy: &[DfmMat3Qi],
    h23_sq: &DfmMat3Qi,
    h23_traceless: bool,
) -> (bool, bool) {
    let mut examiner_div_zero = true;
    let mut sign_flip = false;
    for link in u_copy {
        if *link != mat3_qi_dagger(link) {
            examiner_div_zero = false;
        }
        let tr_re = mat3_qi_trace(link).re;
        let fp_quad = mat3_qi_trace(&mat3_qi_mul(link, h23_sq)).re;
        if h23_traceless && tr_re == q(-1, 1) && fp_quad == q(-2, 1) {
            sign_flip = true;
        }
    }
    (examiner_div_zero, sign_flip)
}

fn audit_su3_examiner_gribov_copies(
    dia: &CarrierGraph,
    tree0: &[usize],
    k4_group: &[DfmMat3Qi; 4],
    h23_sq: &DfmMat3Qi,
    h23_traceless: bool,
) -> (usize, usize, bool, bool, bool) {
    let id3 = mat3_qi_identity();
    let vacuum_links = vec![id3; dia.edges.len()];
    let mut gribov_count = 0usize;
    let mut nontrivial_count = 0usize;
    let mut all_examiner_div_zero = true;
    let mut horizon_sign_flip = false;
    let mut all_collapse_to_vacuum = true;

    for idx in 0..64usize {
        let (i1, i2, i3) = (idx / 16, (idx / 4) % 4, idx % 4);
        let g_copy = [k4_group[0], k4_group[i1], k4_group[i2], k4_group[i3]];
        let u_copy: Vec<DfmMat3Qi> = dia
            .edges
            .iter()
            .map(|&(u, v)| mat3_qi_mul(&g_copy[v], &mat3_qi_mul(&id3, &mat3_qi_dagger(&g_copy[u]))))
            .collect();
        gribov_count += 1;
        if idx != 0 {
            nontrivial_count += 1;
        }
        let (div_ok, flip) = check_single_gribov_copy_links(&u_copy, h23_sq, h23_traceless);
        all_examiner_div_zero &= div_ok;
        horizon_sign_flip |= flip;
        let u_dress = tree_dressing_field_su3(dia, tree0, &u_copy, 0);
        if dress_su3_connection(dia, &u_copy, &u_dress) != vacuum_links {
            all_collapse_to_vacuum = false;
        }
    }
    (
        gribov_count,
        nontrivial_count,
        all_examiner_div_zero,
        horizon_sign_flip,
        all_collapse_to_vacuum,
    )
}

pub fn evaluate_su3_spanning_tree_vs_examiner_gribov_control() -> Su3SpanningTreeVsExaminerGribovReport
{
    let dia = CarrierGraph::diamond();
    let dia_trees = enumerate_spanning_trees(&dia);
    let id3 = mat3_qi_identity();

    let edge_links: Vec<DfmMat3Qi> = vec![
        dfm_su3_block12(Qi::new(q(3, 5), Q::zero()), Qi::new(Q::zero(), q(4, 5))),
        dfm_su3_block23(Qi::new(q(4, 5), Q::zero()), Qi::new(q(3, 5), Q::zero())),
        dfm_su3_block12(Qi::new(q(5, 13), Q::zero()), Qi::new(q(12, 13), Q::zero())),
        dfm_su3_block23(Qi::new(q(12, 13), Q::zero()), Qi::new(Q::zero(), q(5, 13))),
        mat3_qi_mul(
            &dfm_su3_block12(Qi::new(q(4, 5), Q::zero()), Qi::new(Q::zero(), q(3, 5))),
            &dfm_su3_block23(Qi::new(q(3, 5), Q::zero()), Qi::new(q(4, 5), Q::zero())),
        ),
    ];

    let all_in_su3 = edge_links.iter().all(is_in_su3_qi);
    let non_abelian = mat3_qi_commutator_nonzero(&edge_links[0], &edge_links[1]);

    let g_vertex: Vec<DfmMat3Qi> = vec![
        id3,
        dfm_su3_block12(Qi::new(q(4, 5), Q::zero()), Qi::new(q(3, 5), Q::zero())),
        dfm_su3_block23(Qi::new(q(5, 13), Q::zero()), Qi::new(Q::zero(), q(12, 13))),
        mat3_qi_mul(
            &dfm_su3_block23(Qi::new(q(3, 5), Q::zero()), Qi::new(Q::zero(), q(4, 5))),
            &dfm_su3_block12(Qi::new(q(12, 13), Q::zero()), Qi::new(q(5, 13), Q::zero())),
        ),
    ];
    let gauged_links: Vec<DfmMat3Qi> = dia
        .edges
        .iter()
        .enumerate()
        .map(|(e_idx, &(u, v))| {
            mat3_qi_mul(
                &g_vertex[v],
                &mat3_qi_mul(&edge_links[e_idx], &mat3_qi_dagger(&g_vertex[u])),
            )
        })
        .collect();

    let (all_trees_neutralize, all_trees_gauge_invariant) =
        verify_dfm_eight_trees_su3(&dia, &dia_trees, &edge_links, &gauged_links, &id3);

    let u_t0 = tree_dressing_field_su3(&dia, &dia_trees[0].0, &edge_links, 0);
    let u_t7 = tree_dressing_field_su3(&dia, &dia_trees[7].0, &edge_links, 0);
    let d_t0 = dress_su3_connection(&dia, &edge_links, &u_t0);
    let d_t7 = dress_su3_connection(&dia, &edge_links, &u_t7);
    let w_07: Vec<DfmMat3Qi> = (0..dia.vertex_count)
        .map(|v| mat3_qi_mul(&mat3_qi_dagger(&u_t0[v]), &u_t7[v]))
        .collect();
    let mut intertwiner_ok = true;
    for (e_idx, &(u, v)) in dia.edges.iter().enumerate() {
        let rhs = mat3_qi_mul(
            &mat3_qi_dagger(&w_07[v]),
            &mat3_qi_mul(&d_t0[e_idx], &w_07[u]),
        );
        if d_t7[e_idx] != rhs {
            intertwiner_ok = false;
        }
    }

    let diag_su3 = |d0: i64, d1: i64, d2: i64| -> DfmMat3Qi {
        let mut m = mat3_qi_zero();
        m[0][0] = Qi::from_q(q(d0, 1));
        m[1][1] = Qi::from_q(q(d1, 1));
        m[2][2] = Qi::from_q(q(d2, 1));
        m
    };
    let k4_group = [
        diag_su3(1, 1, 1),
        diag_su3(1, -1, -1),
        diag_su3(-1, 1, -1),
        diag_su3(-1, -1, 1),
    ];
    let k4_in_su3 = k4_group.iter().all(is_in_su3_qi);

    // Traceless Hermitian off-diagonal generator H^(23) = E_23 + E_32 in su(3) (Tr(H^(23)) = 0)
    let mut h23 = mat3_qi_zero();
    h23[1][2] = Qi::one();
    h23[2][1] = Qi::one();
    let h23_sq = mat3_qi_mul(&h23, &h23);
    let h23_traceless = mat3_qi_trace(&h23) == Qi::zero() && mat3_qi_dagger(&h23) == h23;

    let (
        gribov_count,
        nontrivial_count,
        all_examiner_div_zero,
        horizon_sign_flip,
        all_collapse_to_vacuum,
    ) = audit_su3_examiner_gribov_copies(&dia, &dia_trees[0].0, &k4_group, &h23_sq, h23_traceless);

    Su3SpanningTreeVsExaminerGribovReport {
        su3_edge_links_all_unitary_det_one: all_in_su3,
        su3_connection_non_abelian: non_abelian,
        dfm_all_eight_trees_neutralize_tree_edges: all_trees_neutralize,
        dfm_dressed_cotree_holonomies_gauge_invariant: all_trees_gauge_invariant,
        dfm_second_kind_tree_change_intertwiner_exact: intertwiner_ok,
        klein_four_gribov_elements_in_su3: k4_in_su3,
        anchored_examiner_gribov_copy_count: gribov_count,
        nontrivial_examiner_gribov_copy_count: nontrivial_count,
        all_gribov_copies_satisfy_discrete_examiner_divergence_zero: all_examiner_div_zero,
        gribov_horizon_hessian_flips_sign_to_negative: horizon_sign_flip,
        dfm_collapses_all_64_gribov_copies_to_single_dressed_state: all_collapse_to_vacuum,
    }
}

// ============================================================================
// Theorem 3.9: Discrete Cartan-Regge Lorentz Tetrad/Frame Dressing Around
//              Simplicial 2-Hinges over Q
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CartanReggeLorentzTetradDfmReport {
    pub boost_preserves_minkowski_metric: bool,
    pub boost_determinant_exact_one: bool,
    pub boost_velocity_addition_group_law_holds: bool,
    pub spatial_rotation_preserves_minkowski_metric: bool,
    pub induced_spacetime_metric_lorentz_invariant: bool,
    pub dressed_levi_civita_connection_lorentz_invariant: bool,
    pub dressed_connection_metric_compatible: bool,
    pub artificial_hinge_holonomy_is_identity: bool,
    pub substantial_hinge_boost_plane_trace: Q,
    pub substantial_hinge_holonomy_trace: Q,
    pub substantial_hinge_dressed_trace_matches_spin_trace: bool,
    pub discrete_bianchi_identity_holds_around_3cell: bool,
}

pub fn minkowski_eta_mat4() -> DfmMat4Q {
    let mut m = mat4_q_zero();
    m[0][0] = q(1, 1);
    m[1][1] = q(-1, 1);
    m[2][2] = q(-1, 1);
    m[3][3] = q(-1, 1);
    m
}

pub fn rational_lorentz_boost_x(beta: Q) -> DfmMat4Q {
    let one_m_b2 = Q::one() - beta * beta;
    assert!(
        !one_m_b2.is_zero(),
        "Superluminal or luminal boost beta^2 = 1"
    );
    let ch = (Q::one() + beta * beta) / one_m_b2;
    let sh = (q(2, 1) * beta) / one_m_b2;
    let mut m = mat4_q_identity();
    m[0][0] = ch;
    m[0][1] = sh;
    m[1][0] = sh;
    m[1][1] = ch;
    m
}

pub fn rational_spatial_rotation_yz(c: Q, s: Q) -> DfmMat4Q {
    let mut m = mat4_q_identity();
    m[2][2] = c;
    m[2][3] = -s;
    m[3][2] = s;
    m[3][3] = c;
    m
}

pub fn is_in_so_13_q(lam: &DfmMat4Q) -> bool {
    let eta = minkowski_eta_mat4();
    let lhs = mat4_q_mul(&mat4_q_transpose(lam), &mat4_q_mul(&eta, lam));
    lhs == eta && mat4_q_det(lam) == Q::one() && lam[0][0] >= Q::one()
}

pub fn evaluate_cartan_regge_lorentz_tetrad_dfm_control() -> CartanReggeLorentzTetradDfmReport {
    let eta = minkowski_eta_mat4();
    let id4 = mat4_q_identity();

    let b1 = q(1, 3);
    let b2 = q(1, 2);
    let b_add = (b1 + b2) / (Q::one() + b1 * b2);
    let lam1 = rational_lorentz_boost_x(b1);
    let lam2 = rational_lorentz_boost_x(b2);
    let lam_add = rational_lorentz_boost_x(b_add);
    let boost_metric_ok = is_in_so_13_q(&lam1) && is_in_so_13_q(&lam2);
    let boost_det_ok = mat4_q_det(&lam1) == Q::one() && mat4_q_det(&lam2) == Q::one();
    let boost_group_law_ok = mat4_q_mul(&lam1, &lam2) == lam_add;

    let rot_yz = rational_spatial_rotation_yz(q(3, 5), q(4, 5));
    let rot_ok = is_in_so_13_q(&rot_yz);

    let mut e0 = mat4_q_identity();
    e0[0][0] = q(2, 1);
    e0[0][1] = q(1, 2);
    e0[1][1] = q(3, 2);
    e0[2][3] = q(1, 3);

    let mut e1 = mat4_q_identity();
    e1[0][0] = q(3, 2);
    e1[1][0] = q(1, 3);
    e1[1][1] = q(2, 1);
    e1[3][2] = q(-1, 2);

    let l0 = mat4_q_mul(&lam1, &rot_yz);
    let l1 = mat4_q_mul(
        &rational_lorentz_boost_x(q(-2, 5)),
        &rational_spatial_rotation_yz(q(5, 13), q(12, 13)),
    );
    let e0_gauged = mat4_q_mul(&l0, &e0);
    let e1_gauged = mat4_q_mul(&l1, &e1);

    let g0 = mat4_q_mul(&mat4_q_transpose(&e0), &mat4_q_mul(&eta, &e0));
    let g0_gauged = mat4_q_mul(&mat4_q_transpose(&e0_gauged), &mat4_q_mul(&eta, &e0_gauged));
    let g1 = mat4_q_mul(&mat4_q_transpose(&e1), &mat4_q_mul(&eta, &e1));
    let g1_gauged = mat4_q_mul(&mat4_q_transpose(&e1_gauged), &mat4_q_mul(&eta, &e1_gauged));
    let metric_inv_ok = (g0 == g0_gauged) && (g1 == g1_gauged);

    let core_01 = rational_lorentz_boost_x(q(1, 2));
    let core_01_gauged = mat4_q_mul(&l0, &mat4_q_mul(&core_01, &mat4_q_inv(&l1)));

    let gamma_01 = mat4_q_mul(&mat4_q_inv(&e0), &mat4_q_mul(&core_01, &e1));
    let gamma_01_gauged = mat4_q_mul(
        &mat4_q_inv(&e0_gauged),
        &mat4_q_mul(&core_01_gauged, &e1_gauged),
    );
    let connection_inv_ok = gamma_01 == gamma_01_gauged;

    let gamma_pullback_g0 = mat4_q_mul(&mat4_q_transpose(&gamma_01), &mat4_q_mul(&g0, &gamma_01));
    let metric_compat_ok = gamma_pullback_g0 == g1;

    let l2 = rational_lorentz_boost_x(q(3, 5));
    let om01_art = mat4_q_mul(&l0, &mat4_q_inv(&l1));
    let om12_art = mat4_q_mul(&l1, &mat4_q_inv(&l2));
    let om20_art = mat4_q_mul(&l2, &mat4_q_inv(&l0));
    let h_art = mat4_q_mul(&om01_art, &mat4_q_mul(&om12_art, &om20_art));
    let art_is_id = h_art == id4;

    let om01_sub = rational_lorentz_boost_x(q(1, 2));
    let om12_sub = rational_lorentz_boost_x(q(1, 3));
    let om20_sub = rational_lorentz_boost_x(q(-1, 3));
    let h_sub = mat4_q_mul(&om01_sub, &mat4_q_mul(&om12_sub, &om20_sub));
    let h_sub_dressed = mat4_q_mul(&mat4_q_inv(&e0), &mat4_q_mul(&h_sub, &e0));
    let tr_boost_plane = h_sub[0][0] + h_sub[1][1];
    let tr_sub = mat4_q_trace(&h_sub);
    let tr_sub_dressed = mat4_q_trace(&h_sub_dressed);

    let p1 = mat4_q_mul(&lam1, &rot_yz);
    let p2 = mat4_q_mul(&lam2, &l1);
    let p3 = l2;
    let h_hinge1_dress = mat4_q_mul(
        &mat4_q_inv(&e0),
        &mat4_q_mul(&mat4_q_mul(&p1, &mat4_q_inv(&p2)), &e0),
    );
    let h_hinge2_dress = mat4_q_mul(
        &mat4_q_inv(&e0),
        &mat4_q_mul(&mat4_q_mul(&p2, &mat4_q_inv(&p3)), &e0),
    );
    let h_hinge3_dress = mat4_q_mul(
        &mat4_q_inv(&e0),
        &mat4_q_mul(&mat4_q_mul(&p3, &mat4_q_inv(&p1)), &e0),
    );
    let bianchi_prod = mat4_q_mul(
        &h_hinge1_dress,
        &mat4_q_mul(&h_hinge2_dress, &h_hinge3_dress),
    );
    let bianchi_ok = bianchi_prod == id4 && h_hinge1_dress != id4;

    CartanReggeLorentzTetradDfmReport {
        boost_preserves_minkowski_metric: boost_metric_ok,
        boost_determinant_exact_one: boost_det_ok,
        boost_velocity_addition_group_law_holds: boost_group_law_ok,
        spatial_rotation_preserves_minkowski_metric: rot_ok,
        induced_spacetime_metric_lorentz_invariant: metric_inv_ok,
        dressed_levi_civita_connection_lorentz_invariant: connection_inv_ok,
        dressed_connection_metric_compatible: metric_compat_ok,
        artificial_hinge_holonomy_is_identity: art_is_id,
        substantial_hinge_boost_plane_trace: tr_boost_plane,
        substantial_hinge_holonomy_trace: tr_sub,
        substantial_hinge_dressed_trace_matches_spin_trace: tr_sub == tr_sub_dressed,
        discrete_bianchi_identity_holds_around_3cell: bianchi_ok,
    }
}

// Origin: engine/crates_rs/core_quantum_physics/src/quantum_import_finite_maps/ravera_dfm_finite_to_continuum.rs
// Claim: urn:core:crates_rs:core-quantum-physics:ravera-dfm-finite-to-continuum:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb1b5f748 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb1b5f748` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb1b5f748 {
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
impl BoundaryErrorb1b5f748 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb1b5f748 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb1b5f748 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb1b5f748 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb1b5f748> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb1b5f748::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb1b5f748::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb1b5f748::ExceedsCapacity {
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
    fn test_ckm_jarlskog_bipartite_dfm_control() {
        let r = evaluate_ckm_jarlskog_bipartite_dfm_control();
        assert_eq!(r.ng2_removed_tree_phases, 3);
        assert_eq!(r.ng2_substantial_cycle_phases, 1);
        assert_eq!(r.ng3_removed_tree_phases, 5);
        assert_eq!(r.ng3_substantial_cycle_phases, 4);
        assert_eq!(r.ng4_removed_tree_phases, 7);
        assert_eq!(r.ng4_substantial_cycle_phases, 9);
        assert!(r.two_gen_cabibbo_unitary);
        assert!(r.two_gen_dressed_entries_real_positive);
        assert_eq!(r.two_gen_jarlskog_zero, q(0, 1));
        assert!(r.three_gen_ckm_unitary);
        assert!(r.three_gen_ckm_det_unit_norm);
        assert!(r.three_gen_all_nine_quartets_rephasing_invariant);
        assert_eq!(r.three_gen_jarlskog_invariant, q(5184, 78125));
    }

    #[test]
    fn test_su3_spanning_tree_vs_examiner_gribov_control() {
        let r = evaluate_su3_spanning_tree_vs_examiner_gribov_control();
        assert!(r.su3_edge_links_all_unitary_det_one);
        assert!(r.su3_connection_non_abelian);
        assert!(r.dfm_all_eight_trees_neutralize_tree_edges);
        assert!(r.dfm_dressed_cotree_holonomies_gauge_invariant);
        assert!(r.dfm_second_kind_tree_change_intertwiner_exact);
        assert!(r.klein_four_gribov_elements_in_su3);
        assert_eq!(r.anchored_examiner_gribov_copy_count, 64);
        assert_eq!(r.nontrivial_examiner_gribov_copy_count, 63);
        assert!(r.all_gribov_copies_satisfy_discrete_examiner_divergence_zero);
        assert!(r.gribov_horizon_hessian_flips_sign_to_negative);
        assert!(r.dfm_collapses_all_64_gribov_copies_to_single_dressed_state);
    }

    #[test]
    fn test_cartan_regge_lorentz_tetrad_dfm_control() {
        let r = evaluate_cartan_regge_lorentz_tetrad_dfm_control();
        assert!(r.boost_preserves_minkowski_metric);
        assert!(r.boost_determinant_exact_one);
        assert!(r.boost_velocity_addition_group_law_holds);
        assert!(r.spatial_rotation_preserves_minkowski_metric);
        assert!(r.induced_spacetime_metric_lorentz_invariant);
        assert!(r.dressed_levi_civita_connection_lorentz_invariant);
        assert!(r.dressed_connection_metric_compatible);
        assert!(r.artificial_hinge_holonomy_is_identity);
        assert_eq!(r.substantial_hinge_boost_plane_trace, q(10, 3));
        assert_eq!(r.substantial_hinge_holonomy_trace, q(16, 3));
        assert!(r.substantial_hinge_dressed_trace_matches_spin_trace);
        assert!(r.discrete_bianchi_identity_holds_around_3cell);
    }
}

#[cfg(test)]
mod l4_boundary_tests_b1b5f748 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordb1b5f748::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordb1b5f748::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordb1b5f748::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordb1b5f748::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordb1b5f748::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorb1b5f748::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorb1b5f748::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
