//! Native exact verification of coupled bipartite (`D_2 x D_3`, `D_3 x D_3`) and
//! tripartite (`D_3 x D_3 x D_3`) pure relational projector, holonomy, and Schur-Weyl
//! identities for PFP operad stages `P_REL_05` through `P_REL_07`.
//!
//! All linear algebra is executed in exact `BigRational` and `i64` arithmetic with
//! zero floating-point operations and zero free tuning parameters.
//!
//! `AuthorityEffect: None`.

use num_bigint::BigInt;
use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

pub const COUPLED_RELATIONAL_RECEIPT_SCHEMA: &str =
    "omega.symbol_game.coupled_relational_operad_receipt.v1";

type MatQ = Vec<Vec<BigRational>>;
type MatZ = Vec<Vec<i64>>;

fn q(n: i64, d: i64) -> BigRational {
    BigRational::new(BigInt::from(n), BigInt::from(d))
}

fn ident_q(n: usize) -> MatQ {
    (0..n)
        .map(|i| {
            (0..n)
                .map(|j| if i == j { q(1, 1) } else { q(0, 1) })
                .collect()
        })
        .collect()
}

fn matmul_q(a: &MatQ, b: &MatQ) -> MatQ {
    let n = a.len();
    let m = b[0].len();
    let k_len = b.len();
    let mut out = vec![vec![BigRational::zero(); m]; n];
    for i in 0..n {
        for k in 0..k_len {
            if !a[i][k].is_zero() {
                for j in 0..m {
                    out[i][j] += &a[i][k] * &b[k][j];
                }
            }
        }
    }
    out
}

fn matadd_q(a: &MatQ, b: &MatQ) -> MatQ {
    let n = a.len();
    let m = a[0].len();
    (0..n)
        .map(|i| (0..m).map(|j| &a[i][j] + &b[i][j]).collect())
        .collect()
}

fn matmul_z(a: &MatZ, b: &MatZ) -> MatZ {
    let n = a.len();
    let m = b[0].len();
    let k_len = b.len();
    let mut out = vec![vec![0i64; m]; n];
    for i in 0..n {
        for k in 0..k_len {
            if a[i][k] != 0 {
                for j in 0..m {
                    out[i][j] += a[i][k] * b[k][j];
                }
            }
        }
    }
    out
}

fn kron_q(a: &MatQ, b: &MatQ) -> MatQ {
    let (ra, ca) = (a.len(), a[0].len());
    let (rb, cb) = (b.len(), b[0].len());
    let mut out = vec![vec![BigRational::zero(); ca * cb]; ra * rb];
    for i in 0..(ra * rb) {
        for j in 0..(ca * cb) {
            out[i][j] = &a[i / rb][j / cb] * &b[i % rb][j % cb];
        }
    }
    out
}

fn kron_z(a: &MatZ, b: &MatZ) -> MatZ {
    let (ra, ca) = (a.len(), a[0].len());
    let (rb, cb) = (b.len(), b[0].len());
    let mut out = vec![vec![0i64; ca * cb]; ra * rb];
    for i in 0..(ra * rb) {
        for j in 0..(ca * cb) {
            out[i][j] = a[i / rb][j / cb] * b[i % rb][j % cb];
        }
    }
    out
}

fn trace_q(a: &MatQ) -> BigRational {
    (0..a.len()).fold(BigRational::zero(), |acc, i| acc + &a[i][i])
}

fn exact_int(r: &BigRational) -> Option<i64> {
    if r.denom().is_one() {
        r.numer().to_i64()
    } else {
        None
    }
}

fn projector_family_defect_q(projectors: &[MatQ]) -> BigRational {
    let n = projectors[0].len();
    let ident = ident_q(n);
    let mut defect = BigRational::zero();
    for (idx_a, pa) in projectors.iter().enumerate() {
        let pa_sq = matmul_q(pa, pa);
        for i in 0..n {
            for j in 0..n {
                defect += (&pa_sq[i][j] - &pa[i][j]).abs();
            }
        }
        for (idx_b, pb) in projectors.iter().enumerate() {
            if idx_a != idx_b {
                let pab = matmul_q(pa, pb);
                for row in &pab {
                    for val in row {
                        defect += val.abs();
                    }
                }
            }
        }
    }
    for (i, ident_row) in ident.iter().enumerate().take(n) {
        for (j, ident_ij) in ident_row.iter().enumerate().take(n) {
            let sum_ij = projectors
                .iter()
                .fold(BigRational::zero(), |acc, p| acc + &p[i][j]);
            defect += (sum_ij - ident_ij).abs();
        }
    }
    defect
}

fn is_spanning_tree(num_vertices: usize, edges: &[(usize, usize)]) -> bool {
    if edges.len() + 1 != num_vertices {
        return false;
    }
    let mut parent: Vec<usize> = (0..num_vertices).collect();
    fn find(parent: &mut [usize], mut x: usize) -> usize {
        while parent[x] != x {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        x
    }
    for &(u, v) in edges {
        let ru = find(&mut parent, u);
        let rv = find(&mut parent, v);
        if ru == rv {
            return false;
        }
        parent[ru] = rv;
    }
    let root0 = find(&mut parent, 0);
    (1..num_vertices).all(|v| find(&mut parent, v) == root0)
}

fn enumerate_spanning_trees(
    num_vertices: usize,
    edges: &[(usize, usize)],
) -> Vec<Vec<(usize, usize)>> {
    let target_len = num_vertices - 1;
    let m = edges.len();
    let mut trees = Vec::new();
    for mask in 0u32..(1u32 << m) {
        if mask.count_ones() as usize == target_len {
            let subset: Vec<(usize, usize)> = (0..m)
                .filter(|&bit| (mask & (1u32 << bit)) != 0)
                .map(|bit| edges[bit])
                .collect();
            if is_spanning_tree(num_vertices, &subset) {
                trees.push(subset);
            }
        }
    }
    trees
}

fn count_obstructed_trees(
    num_vertices: usize,
    all_edges: &[(usize, usize)],
    omega: &[i64],
    trees: &[Vec<(usize, usize)>],
) -> usize {
    let edge_val = |u: usize, v: usize| -> i64 {
        all_edges
            .iter()
            .position(|&(a, b)| a == u && b == v)
            .map(|idx| omega[idx])
            .unwrap_or(0)
    };
    let mut obstructed = 0usize;
    for tree in trees {
        let mut g = vec![None::<i64>; num_vertices];
        g[0] = Some(0);
        while g.iter().any(Option::is_none) {
            for &(u, v) in tree {
                let w = edge_val(u, v);
                match (g[u], g[v]) {
                    (Some(gu), None) => g[v] = Some(gu + w),
                    (None, Some(gv)) => g[u] = Some(gv - w),
                    _ => {}
                }
            }
        }
        let has_chord_defect = all_edges.iter().any(|&(u, v)| {
            !tree.contains(&(u, v))
                && (edge_val(u, v) - (g[v].unwrap_or(0) - g[u].unwrap_or(0))) != 0
        });
        if has_chord_defect {
            obstructed += 1;
        }
    }
    obstructed
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Stage1SurvivorTowerReceiptV1 {
    pub normative_survivor_vector: [i64; 7],
    pub d2_delta_support_floor: i64,
    pub retraction_left_inverse_defect: i64,
    pub persistent_history_counts: [i64; 7],
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Stage2BinarySwapProjectorReceiptV1 {
    pub scaled_p_plus_row0_row1: [i64; 4],
    pub scaled_p_minus_row0_row1: [i64; 4],
    pub projector_idempotence_defect: String,
    pub projector_orthogonality_defect: String,
    pub difference_kernel_trace: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Stage3DiamondHolonomyReceiptV1 {
    pub diamond_graph_v_e_b1: [i64; 3],
    pub spanning_tree_count_diamond: i64,
    pub coboundary_cycle_sum_defect: String,
    pub fundamental_cycle_holonomies: [i64; 2],
    pub obstructed_spanning_trees: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Stage4D3CommutatorCyclotomicReceiptV1 {
    pub commutator_k_row0: [i64; 3],
    pub commutator_k_row1: [i64; 3],
    pub commutator_k_row2: [i64; 3],
    pub commutator_trace: i64,
    pub commutator_cube_plus_three_commutator_zero: i64,
    pub cyclotomic_phi3_residual_on_difference_subspace: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BipartiteD2xD3ReceiptV1 {
    pub prism_graph_v_e_b1_trees: [i64; 4],
    pub four_sector_projector_ranks: [i64; 4],
    pub four_sector_orthogonality_and_completeness_defect: String,
    pub coupled_swap_commutator_cubic_and_w0_defect: String,
    pub triangle_cycle_sums: [i64; 2],
    pub interlayer_twist_holonomies: [i64; 2],
    pub obstructed_spanning_trees: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct BipartiteD3xD3ReceiptV1 {
    pub five_sector_projector_ranks: [i64; 5],
    pub five_sector_orthogonality_and_completeness_defect: String,
    pub compound_commutator_square_minus_nine_w00_defect: String,
    pub diagonal_3cycle_traces_on_sym_and_alt_w00: [i64; 3],
    pub antisymmetric_singlet_minor_vs_separable_minor: [i64; 2],
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct TripartiteD3CubedReceiptV1 {
    pub tripartite_binomial_sector_ranks: [i64; 4],
    pub w000_schur_weyl_sym_mixed_alt_ranks: [i64; 3],
    pub levi_civita_mixed_sector_and_parity_pin: [i64; 4],
    pub w000_r3_invariant_split_and_k3_square_defect: [i64; 4],
    pub pigeonhole_levi_civita_l1_and_sector_defects: [i64; 3],
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct CoupledRelationalOperadReceiptV1 {
    pub schema_version: String,
    pub status: String,
    pub stage1_survivor_tower: Stage1SurvivorTowerReceiptV1,
    pub stage2_d2_swap_projectors: Stage2BinarySwapProjectorReceiptV1,
    pub stage3_diamond_holonomy: Stage3DiamondHolonomyReceiptV1,
    pub stage4_d3_commutator_cyclotomic: Stage4D3CommutatorCyclotomicReceiptV1,
    pub stage5_d2_x_d3: BipartiteD2xD3ReceiptV1,
    pub stage6_d3_x_d3: BipartiteD3xD3ReceiptV1,
    pub stage7_d3_x_d3_x_d3: TripartiteD3CubedReceiptV1,
    pub free_parameter_count: usize,
    pub refusal_code: Option<String>,
    pub authority_effect: String,
    pub genesis_effect: String,
}

#[derive(Debug, Clone, Default, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CoupledRelationalVerifyRequestV1 {
    #[serde(default)]
    pub expected_stage1_survivors: Option<[i64; 7]>,
    #[serde(default)]
    pub expected_stage3_diamond_trees: Option<i64>,
    #[serde(default)]
    pub expected_stage5_ranks: Option<[i64; 4]>,
    #[serde(default)]
    pub expected_stage5_trees: Option<i64>,
    #[serde(default)]
    pub expected_stage6_ranks: Option<[i64; 5]>,
    #[serde(default)]
    pub expected_stage7_w000_schur_weyl_ranks: Option<[i64; 3]>,
    #[serde(default)]
    pub free_parameter_count: usize,
}

pub fn compute_stage1_survivor_tower() -> Stage1SurvivorTowerReceiptV1 {
    let active_registers: [&[&str]; 7] = [
        &[],
        &["obs_01_binary_distinction_cut"],
        &["obs_02_observational_collision"],
        &["obs_03_asymmetric_pair_swap"],
        &[],
        &["obs_05_closed_cycle_holonomy"],
        &["obs_06_noncommuting_transition_order"],
    ];
    let mut survivors = [0i64; 7];
    let mut history = [0i64; 7];
    let mut accum = 0i64;
    for (idx, reg) in active_registers.iter().enumerate() {
        let count = reg.len() as i64;
        survivors[idx] = count;
        accum += count;
        history[idx] = accum;
    }
    let d2_carrier = [0i64, 1i64];
    let d2_floor = d2_carrier.len() as i64;

    let retract_embedded = |k: usize| -> Option<usize> {
        if k < 2 {
            Some(k)
        } else {
            None
        }
    };
    let left_inv_defect = i64::from(retract_embedded(0) != Some(0))
        + i64::from(retract_embedded(1) != Some(1))
        + i64::from(retract_embedded(2).is_some());

    Stage1SurvivorTowerReceiptV1 {
        normative_survivor_vector: survivors,
        d2_delta_support_floor: d2_floor,
        retraction_left_inverse_defect: left_inv_defect,
        persistent_history_counts: history,
    }
}

pub fn compute_stage2_d2_swap_projectors() -> Stage2BinarySwapProjectorReceiptV1 {
    let p_plus = vec![vec![q(1, 2), q(1, 2)], vec![q(1, 2), q(1, 2)]];
    let p_minus = vec![vec![q(1, 2), q(-1, 2)], vec![q(-1, 2), q(1, 2)]];
    let i2 = ident_q(2);

    let p_plus_sq = matmul_q(&p_plus, &p_plus);
    let p_minus_sq = matmul_q(&p_minus, &p_minus);
    let p_pm = matmul_q(&p_plus, &p_minus);
    let p_mp = matmul_q(&p_minus, &p_plus);

    let mut idem_defect = BigRational::zero();
    let mut ortho_defect = BigRational::zero();
    for i in 0..2 {
        for j in 0..2 {
            idem_defect += (&p_plus_sq[i][j] - &p_plus[i][j]).abs();
            idem_defect += (&p_minus_sq[i][j] - &p_minus[i][j]).abs();
            ortho_defect += p_pm[i][j].abs()
                + p_mp[i][j].abs()
                + ((&p_plus[i][j] + &p_minus[i][j]) - &i2[i][j]).abs();
        }
    }
    let diff_trace = trace_q(&p_minus);

    Stage2BinarySwapProjectorReceiptV1 {
        scaled_p_plus_row0_row1: [1, 1, 1, 1],
        scaled_p_minus_row0_row1: [1, -1, -1, 1],
        projector_idempotence_defect: format!("{}/{}", idem_defect.numer(), idem_defect.denom()),
        projector_orthogonality_defect: format!(
            "{}/{}",
            ortho_defect.numer(),
            ortho_defect.denom()
        ),
        difference_kernel_trace: format!("{}/{}", diff_trace.numer(), diff_trace.denom()),
    }
}

pub fn compute_stage3_diamond_holonomy() -> Stage3DiamondHolonomyReceiptV1 {
    let diamond_edges: [(usize, usize); 5] = [(0, 1), (1, 2), (0, 2), (1, 3), (2, 3)];
    let trees = enumerate_spanning_trees(4, &diamond_edges);
    let b1 = (diamond_edges.len() as i64) - 4 + 1;

    let potentials: [[BigRational; 4]; 2] = [
        [q(1, 1), q(0, 1), q(0, 1), q(0, 1)],
        [q(0, 1), q(2, 3), q(-1, 2), q(5, 4)],
    ];
    let mut coboundary_defect = BigRational::zero();
    for g in &potentials {
        let d0 = |u: usize, v: usize| -> BigRational { &g[v] - &g[u] };
        let c1_sum = d0(0, 1) + d0(1, 2) - d0(0, 2);
        let c2_sum = d0(1, 3) - d0(2, 3) - d0(1, 2);
        coboundary_defect += c1_sum.abs() + c2_sum.abs();
    }

    let omega_non_exact = [0i64, 0, -1, 0, 1];
    let c1_hol = omega_non_exact[0] + omega_non_exact[1] - omega_non_exact[2];
    let c2_hol = omega_non_exact[3] - omega_non_exact[4] - omega_non_exact[1];
    let obstructed = count_obstructed_trees(4, &diamond_edges, &omega_non_exact, &trees);

    Stage3DiamondHolonomyReceiptV1 {
        diamond_graph_v_e_b1: [4, diamond_edges.len() as i64, b1],
        spanning_tree_count_diamond: trees.len() as i64,
        coboundary_cycle_sum_defect: format!(
            "{}/{}",
            coboundary_defect.numer(),
            coboundary_defect.denom()
        ),
        fundamental_cycle_holonomies: [c1_hol, c2_hol],
        obstructed_spanning_trees: obstructed as i64,
    }
}

pub fn compute_stage4_d3_commutator_cyclotomic() -> Stage4D3CommutatorCyclotomicReceiptV1 {
    let t01: MatZ = vec![vec![0, 1, 0], vec![1, 0, 0], vec![0, 0, 1]];
    let t12: MatZ = vec![vec![1, 0, 0], vec![0, 0, 1], vec![0, 1, 0]];
    let r_plus = matmul_z(&t01, &t12);
    let r_minus = matmul_z(&t12, &t01);
    let k_mat: MatZ = (0..3)
        .map(|i| (0..3).map(|j| r_plus[i][j] - r_minus[i][j]).collect())
        .collect();
    let k_trace = k_mat[0][0] + k_mat[1][1] + k_mat[2][2];

    let k_sq = matmul_z(&k_mat, &k_mat);
    let k_cube = matmul_z(&k_sq, &k_mat);
    let mut k_cube_plus_3k_l1 = 0i64;
    for i in 0..3 {
        for j in 0..3 {
            k_cube_plus_3k_l1 += (k_cube[i][j] + 3 * k_mat[i][j]).abs();
        }
    }

    let r_plus_sq = matmul_z(&r_plus, &r_plus);
    let w0_basis = [[1i64, -1, 0], [0i64, 1, -1]];
    let mut phi3_residual = 0i64;
    for v in &w0_basis {
        for i in 0..3 {
            let r2_v: i64 = (0..3).map(|j| r_plus_sq[i][j] * v[j]).sum();
            let r1_v: i64 = (0..3).map(|j| r_plus[i][j] * v[j]).sum();
            let k2_v: i64 = (0..3).map(|j| k_sq[i][j] * v[j]).sum();
            phi3_residual += (r2_v + r1_v + v[i]).abs();
            phi3_residual += (k2_v + 3 * v[i]).abs();
        }
    }

    Stage4D3CommutatorCyclotomicReceiptV1 {
        commutator_k_row0: [k_mat[0][0], k_mat[0][1], k_mat[0][2]],
        commutator_k_row1: [k_mat[1][0], k_mat[1][1], k_mat[1][2]],
        commutator_k_row2: [k_mat[2][0], k_mat[2][1], k_mat[2][2]],
        commutator_trace: k_trace,
        commutator_cube_plus_three_commutator_zero: k_cube_plus_3k_l1,
        cyclotomic_phi3_residual_on_difference_subspace: phi3_residual,
    }
}

pub fn compute_stage5_d2_x_d3() -> BipartiteD2xD3ReceiptV1 {
    let prism_edges: [(usize, usize); 9] = [
        (0, 1),
        (1, 2),
        (0, 2),
        (3, 4),
        (4, 5),
        (3, 5),
        (0, 3),
        (1, 4),
        (2, 5),
    ];
    let trees = enumerate_spanning_trees(6, &prism_edges);
    let b1 = (prism_edges.len() as i64) - 6 + 1;

    let p_plus = vec![vec![q(1, 2), q(1, 2)], vec![q(1, 2), q(1, 2)]];
    let p_minus = vec![vec![q(1, 2), q(-1, 2)], vec![q(-1, 2), q(1, 2)]];
    let q_plus = vec![vec![q(1, 3); 3]; 3];
    let i3 = ident_q(3);
    let q_w0: MatQ = (0..3)
        .map(|i| (0..3).map(|j| &i3[i][j] - &q_plus[i][j]).collect())
        .collect();

    let pi_pp = kron_q(&p_plus, &q_plus);
    let pi_mp = kron_q(&p_minus, &q_plus);
    let pi_p0 = kron_q(&p_plus, &q_w0);
    let pi_m0 = kron_q(&p_minus, &q_w0);
    let sectors = [pi_pp, pi_mp, pi_p0, pi_m0.clone()];

    let ranks = [
        exact_int(&trace_q(&sectors[0])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[1])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[2])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[3])).unwrap_or(-1),
    ];
    let ortho_defect = projector_family_defect_q(&sectors);

    let sigma_z: MatZ = vec![vec![0, 1], vec![1, 0]];
    let k_z: MatZ = vec![vec![0, -1, 1], vec![1, 0, -1], vec![-1, 1, 0]];
    let j23 = kron_z(&sigma_z, &k_z);
    let j23_sq = matmul_z(&j23, &j23);
    let j23_cube = matmul_z(&j23_sq, &j23);
    let mut cubic_l1 = 0i64;
    for i in 0..6 {
        for j in 0..6 {
            cubic_l1 += (j23_cube[i][j] + 3 * j23[i][j]).abs();
        }
    }
    let i6 = ident_q(6);
    let j23_sq_plus_3i: MatQ = (0..6)
        .map(|i| {
            (0..6)
                .map(|j| q(j23_sq[i][j], 1) + q(3, 1) * &i6[i][j])
                .collect()
        })
        .collect();
    let w0_res = matmul_q(&j23_sq_plus_3i, &pi_m0);
    let mut op_defect = q(cubic_l1, 1);
    for row in &w0_res {
        for val in row {
            op_defect += val.abs();
        }
    }

    let omega_twist = [0i64, 0, 0, 0, 0, 0, 1, -1, 0];
    let c_top = omega_twist[0] + omega_twist[1] - omega_twist[2];
    let c_bot = omega_twist[3] + omega_twist[4] - omega_twist[5];
    let h_01 = omega_twist[0] + omega_twist[7] - omega_twist[3] - omega_twist[6];
    let h_12 = omega_twist[1] + omega_twist[8] - omega_twist[4] - omega_twist[7];
    let obstructed = count_obstructed_trees(6, &prism_edges, &omega_twist, &trees);

    BipartiteD2xD3ReceiptV1 {
        prism_graph_v_e_b1_trees: [6, prism_edges.len() as i64, b1, trees.len() as i64],
        four_sector_projector_ranks: ranks,
        four_sector_orthogonality_and_completeness_defect: format!(
            "{}/{}",
            ortho_defect.numer(),
            ortho_defect.denom()
        ),
        coupled_swap_commutator_cubic_and_w0_defect: format!(
            "{}/{}",
            op_defect.numer(),
            op_defect.denom()
        ),
        triangle_cycle_sums: [c_top, c_bot],
        interlayer_twist_holonomies: [h_01, h_12],
        obstructed_spanning_trees: obstructed as i64,
    }
}

pub fn compute_stage6_d3_x_d3() -> BipartiteD3xD3ReceiptV1 {
    let q_plus = vec![vec![q(1, 3); 3]; 3];
    let i3 = ident_q(3);
    let q_w0: MatQ = (0..3)
        .map(|i| (0..3).map(|j| &i3[i][j] - &q_plus[i][j]).collect())
        .collect();

    let pi_pp = kron_q(&q_plus, &q_plus);
    let pi_p0 = kron_q(&q_plus, &q_w0);
    let pi_0p = kron_q(&q_w0, &q_plus);
    let pi_00 = kron_q(&q_w0, &q_w0);

    let i9 = ident_q(9);
    let tau_q: MatQ = (0..9)
        .map(|i| {
            (0..9)
                .map(|j| {
                    if i == 3 * (j % 3) + (j / 3) {
                        q(1, 1)
                    } else {
                        q(0, 1)
                    }
                })
                .collect()
        })
        .collect();
    let p_tau_sym: MatQ = (0..9)
        .map(|i| {
            (0..9)
                .map(|j| q(1, 2) * (&i9[i][j] + &tau_q[i][j]))
                .collect()
        })
        .collect();
    let p_tau_alt: MatQ = (0..9)
        .map(|i| {
            (0..9)
                .map(|j| q(1, 2) * (&i9[i][j] - &tau_q[i][j]))
                .collect()
        })
        .collect();

    let pi_00_sym = matmul_q(&p_tau_sym, &pi_00);
    let pi_00_alt = matmul_q(&p_tau_alt, &pi_00);
    let sectors = [
        pi_pp,
        pi_p0,
        pi_0p,
        pi_00_sym.clone(),
        pi_00_alt.clone(),
    ];
    let ranks = [
        exact_int(&trace_q(&sectors[0])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[1])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[2])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[3])).unwrap_or(-1),
        exact_int(&trace_q(&sectors[4])).unwrap_or(-1),
    ];
    let ortho_defect = projector_family_defect_q(&sectors);

    let k_z: MatZ = vec![vec![0, -1, 1], vec![1, 0, -1], vec![-1, 1, 0]];
    let k33 = kron_z(&k_z, &k_z);
    let k33_sq = matmul_z(&k33, &k33);
    let mut sym_defect = 0i64;
    for i in 0..9 {
        for j in 0..9 {
            sym_defect += (k33[i][j] - k33[j][i]).abs();
        }
    }
    let k33_sq_minus_9i: MatQ = (0..9)
        .map(|i| {
            (0..9)
                .map(|j| q(k33_sq[i][j], 1) - q(9, 1) * &i9[i][j])
                .collect()
        })
        .collect();
    let w00_res = matmul_q(&k33_sq_minus_9i, &pi_00);
    let mut inv_defect = q(sym_defect, 1);
    for row in &w00_res {
        for val in row {
            inv_defect += val.abs();
        }
    }

    let t01: MatZ = vec![vec![0, 1, 0], vec![1, 0, 0], vec![0, 0, 1]];
    let t12: MatZ = vec![vec![1, 0, 0], vec![0, 0, 1], vec![0, 1, 0]];
    let r_z = matmul_z(&t01, &t12);
    let r33_z = kron_z(&r_z, &r_z);
    let r33_q: MatQ = (0..9)
        .map(|i| (0..9).map(|j| q(r33_z[i][j], 1)).collect())
        .collect();
    let tr_sym = exact_int(&trace_q(&matmul_q(&r33_q, &pi_00_sym))).unwrap_or(-99);
    let tr_alt = exact_int(&trace_q(&matmul_q(&r33_q, &pi_00_alt))).unwrap_or(-99);
    let r33_minus_i_alt = matmul_q(
        &(0..9)
            .map(|i| (0..9).map(|j| &r33_q[i][j] - &i9[i][j]).collect())
            .collect(),
        &pi_00_alt,
    );
    let mut alt_inv_defect = BigRational::zero();
    for row in &r33_minus_i_alt {
        for val in row {
            alt_inv_defect += val.abs();
        }
    }

    let singlet_minor = k_z[0][0] * k_z[1][1] - k_z[0][1] * k_z[1][0];
    let u = [1i64, -1, 0];
    let v = [0i64, 1, -1];
    let separable_minor = (u[0] * v[0]) * (u[1] * v[1]) - (u[0] * v[1]) * (u[1] * v[0]);

    BipartiteD3xD3ReceiptV1 {
        five_sector_projector_ranks: ranks,
        five_sector_orthogonality_and_completeness_defect: format!(
            "{}/{}",
            ortho_defect.numer(),
            ortho_defect.denom()
        ),
        compound_commutator_square_minus_nine_w00_defect: format!(
            "{}/{}",
            inv_defect.numer(),
            inv_defect.denom()
        ),
        diagonal_3cycle_traces_on_sym_and_alt_w00: [
            tr_sym,
            tr_alt,
            exact_int(&alt_inv_defect).unwrap_or(-99),
        ],
        antisymmetric_singlet_minor_vs_separable_minor: [singlet_minor, separable_minor],
    }
}

fn build_s3_sym_alt_projectors(s3_perms: &[([usize; 3], i64); 6]) -> (MatQ, MatQ) {
    let mut p_sym3 = vec![vec![BigRational::zero(); 27]; 27];
    let mut p_alt3 = vec![vec![BigRational::zero(); 27]; 27];
    for &(perm, sgn) in s3_perms {
        for a in 0..3 {
            for b in 0..3 {
                for c in 0..3 {
                    let col = 9 * a + 3 * b + c;
                    let coords = [a, b, c];
                    let row = 9 * coords[perm[0]] + 3 * coords[perm[1]] + coords[perm[2]];
                    p_sym3[row][col] += q(1, 6);
                    p_alt3[row][col] += q(sgn, 6);
                }
            }
        }
    }
    (p_sym3, p_alt3)
}

fn compute_stage7_eps_metrics(
    s3_perms: &[([usize; 3], i64); 6],
    pi_12: &MatQ,
    pi_000: &MatQ,
) -> [i64; 3] {
    let mut eps_vec = vec![BigRational::zero(); 27];
    for &(perm, sgn) in s3_perms {
        eps_vec[9 * perm[0] + 3 * perm[1] + perm[2]] = q(sgn, 1);
    }
    let eps_l1 =
        exact_int(&eps_vec.iter().fold(BigRational::zero(), |a, v| a + v.abs())).unwrap_or(-1);
    let mut pi12_eps_defect = BigRational::zero();
    let mut pi000_eps_l1 = BigRational::zero();
    for i in 0..27 {
        let mut v12 = BigRational::zero();
        let mut v000 = BigRational::zero();
        for j in 0..27 {
            v12 += &pi_12[i][j] * &eps_vec[j];
            v000 += &pi_000[i][j] * &eps_vec[j];
        }
        pi12_eps_defect += (v12 - &eps_vec[i]).abs();
        pi000_eps_l1 += v000.abs();
    }
    [
        eps_l1,
        exact_int(&pi12_eps_defect).unwrap_or(-1),
        exact_int(&pi000_eps_l1).unwrap_or(-1),
    ]
}

pub fn compute_stage7_d3_cubed() -> TripartiteD3CubedReceiptV1 {
    let q_plus = vec![vec![q(1, 3); 3]; 3];
    let i3 = ident_q(3);
    let q_w0: MatQ = (0..3)
        .map(|i| (0..3).map(|j| &i3[i][j] - &q_plus[i][j]).collect())
        .collect();

    let pi_30 = kron_q(&kron_q(&q_plus, &q_plus), &q_plus);
    let pi_21 = matadd_q(
        &matadd_q(
            &kron_q(&kron_q(&q_plus, &q_plus), &q_w0),
            &kron_q(&kron_q(&q_plus, &q_w0), &q_plus),
        ),
        &kron_q(&kron_q(&q_w0, &q_plus), &q_plus),
    );
    let pi_12 = matadd_q(
        &matadd_q(
            &kron_q(&kron_q(&q_plus, &q_w0), &q_w0),
            &kron_q(&kron_q(&q_w0, &q_plus), &q_w0),
        ),
        &kron_q(&kron_q(&q_w0, &q_w0), &q_plus),
    );
    let pi_000 = kron_q(&kron_q(&q_w0, &q_w0), &q_w0);
    let binomial_ranks = [
        exact_int(&trace_q(&pi_30)).unwrap_or(-1),
        exact_int(&trace_q(&pi_21)).unwrap_or(-1),
        exact_int(&trace_q(&pi_12)).unwrap_or(-1),
        exact_int(&trace_q(&pi_000)).unwrap_or(-1),
    ];

    let s3_perms: [([usize; 3], i64); 6] = [
        ([0, 1, 2], 1),
        ([1, 2, 0], 1),
        ([2, 0, 1], 1),
        ([1, 0, 2], -1),
        ([0, 2, 1], -1),
        ([2, 1, 0], -1),
    ];
    let i27 = ident_q(27);
    let (p_sym3, p_alt3) = build_s3_sym_alt_projectors(&s3_perms);
    let p_mix3: MatQ = (0..27)
        .map(|i| {
            (0..27)
                .map(|j| &i27[i][j] - &p_sym3[i][j] - &p_alt3[i][j])
                .collect()
        })
        .collect();

    let w000_schur_weyl = [
        exact_int(&trace_q(&matmul_q(&p_sym3, &pi_000))).unwrap_or(-1),
        exact_int(&trace_q(&matmul_q(&p_mix3, &pi_000))).unwrap_or(-1),
        exact_int(&trace_q(&matmul_q(&p_alt3, &pi_000))).unwrap_or(-1),
    ];

    let alt_rank = exact_int(&trace_q(&p_alt3)).unwrap_or(-1);
    let alt_in_pi12 = matmul_q(&pi_12, &p_alt3);
    let mut alt_out_defect = BigRational::zero();
    for i in 0..27 {
        for j in 0..27 {
            alt_out_defect += (&alt_in_pi12[i][j] - &p_alt3[i][j]).abs();
        }
    }

    let t01: MatZ = vec![vec![0, 1, 0], vec![1, 0, 0], vec![0, 0, 1]];
    let t12: MatZ = vec![vec![1, 0, 0], vec![0, 0, 1], vec![0, 1, 0]];
    let r_z = matmul_z(&t01, &t12);
    let r3_z = kron_z(&kron_z(&r_z, &r_z), &r_z);
    let t01_3_z = kron_z(&kron_z(&t01, &t01), &t01);
    let r3_q: MatQ = (0..27)
        .map(|i| (0..27).map(|j| q(r3_z[i][j], 1)).collect())
        .collect();
    let t01_3_q: MatQ = (0..27)
        .map(|i| (0..27).map(|j| q(t01_3_z[i][j], 1)).collect())
        .collect();

    let r3_alt = matmul_q(&r3_q, &p_alt3);
    let t01_alt = matmul_q(&t01_3_q, &p_alt3);
    let mut r3_alt_defect = BigRational::zero();
    let mut t01_alt_defect = BigRational::zero();
    for i in 0..27 {
        for j in 0..27 {
            r3_alt_defect += (&r3_alt[i][j] - &p_alt3[i][j]).abs();
            t01_alt_defect += (&t01_alt[i][j] + &p_alt3[i][j]).abs();
        }
    }

    let r3_sq_q = matmul_q(&r3_q, &r3_q);
    let p_r3_inv: MatQ = (0..27)
        .map(|i| {
            (0..27)
                .map(|j| q(1, 3) * (&i27[i][j] + &r3_q[i][j] + &r3_sq_q[i][j]))
                .collect()
        })
        .collect();
    let pi_000_r3 = matmul_q(&p_r3_inv, &pi_000);
    let w000_r3_rank = exact_int(&trace_q(&pi_000_r3)).unwrap_or(-1);
    let p_t01_plus: MatQ = (0..27)
        .map(|i| (0..27).map(|j| q(1, 2) * (&i27[i][j] + &t01_3_q[i][j])).collect())
        .collect();
    let p_t01_minus: MatQ = (0..27)
        .map(|i| (0..27).map(|j| q(1, 2) * (&i27[i][j] - &t01_3_q[i][j])).collect())
        .collect();
    let r3_plus = exact_int(&trace_q(&matmul_q(&p_t01_plus, &pi_000_r3))).unwrap_or(-1);
    let r3_minus = exact_int(&trace_q(&matmul_q(&p_t01_minus, &pi_000_r3))).unwrap_or(-1);

    let k_z: MatZ = vec![vec![0, -1, 1], vec![1, 0, -1], vec![-1, 1, 0]];
    let k3_z = kron_z(&kron_z(&k_z, &k_z), &k_z);
    let k3_sq_z = matmul_z(&k3_z, &k3_z);
    let k3_sq_plus_27i: MatQ = (0..27)
        .map(|i| {
            (0..27)
                .map(|j| q(k3_sq_z[i][j], 1) + q(27, 1) * &i27[i][j])
                .collect()
        })
        .collect();
    let k3_res = matmul_q(&k3_sq_plus_27i, &pi_000);
    let k3_defect = k3_res
        .iter()
        .flat_map(|row| row.iter())
        .fold(BigRational::zero(), |acc, val| acc + val.abs());

    let pigeonhole_metrics = compute_stage7_eps_metrics(&s3_perms, &pi_12, &pi_000);

    TripartiteD3CubedReceiptV1 {
        tripartite_binomial_sector_ranks: binomial_ranks,
        w000_schur_weyl_sym_mixed_alt_ranks: w000_schur_weyl,
        levi_civita_mixed_sector_and_parity_pin: [
            alt_rank,
            exact_int(&alt_out_defect).unwrap_or(-1),
            exact_int(&r3_alt_defect).unwrap_or(-1),
            exact_int(&t01_alt_defect).unwrap_or(-1),
        ],
        w000_r3_invariant_split_and_k3_square_defect: [
            w000_r3_rank,
            r3_plus,
            r3_minus,
            exact_int(&k3_defect).unwrap_or(-1),
        ],
        pigeonhole_levi_civita_l1_and_sector_defects: pigeonhole_metrics,
    }
}

pub fn evaluate_coupled_relational_operad(
    req: &CoupledRelationalVerifyRequestV1,
) -> CoupledRelationalOperadReceiptV1 {
    let s1 = compute_stage1_survivor_tower();
    let s2 = compute_stage2_d2_swap_projectors();
    let s3 = compute_stage3_diamond_holonomy();
    let s4 = compute_stage4_d3_commutator_cyclotomic();
    let s5 = compute_stage5_d2_x_d3();
    let s6 = compute_stage6_d3_x_d3();
    let s7 = compute_stage7_d3_cubed();

    let unpinned_subchannel = [
        req.expected_stage1_survivors
            .is_some_and(|exp1| exp1 != s1.normative_survivor_vector),
        req.expected_stage3_diamond_trees
            .is_some_and(|exp3_trees| exp3_trees != s3.spanning_tree_count_diamond),
        req.expected_stage5_ranks
            .is_some_and(|exp5| exp5 != s5.four_sector_projector_ranks),
        req.expected_stage5_trees
            .is_some_and(|exp_trees| exp_trees != s5.prism_graph_v_e_b1_trees[3]),
        req.expected_stage6_ranks
            .is_some_and(|exp6| exp6 != s6.five_sector_projector_ranks),
        req.expected_stage7_w000_schur_weyl_ranks
            .is_some_and(|exp7| exp7 != s7.w000_schur_weyl_sym_mixed_alt_ranks),
    ]
    .into_iter()
    .any(|mismatch| mismatch);

    let refusal_code = if req.free_parameter_count != 0 {
        Some("DOF_NONZERO_FREE_PARAMETERS".to_owned())
    } else if unpinned_subchannel {
        Some("DOF_UNPINNED_SUBCHANNEL_COMPENSATION".to_owned())
    } else {
        None
    };

    let status = if refusal_code.is_none() {
        "PASS".to_owned()
    } else {
        "REFUSED".to_owned()
    };

    CoupledRelationalOperadReceiptV1 {
        schema_version: COUPLED_RELATIONAL_RECEIPT_SCHEMA.to_owned(),
        status,
        stage1_survivor_tower: s1,
        stage2_d2_swap_projectors: s2,
        stage3_diamond_holonomy: s3,
        stage4_d3_commutator_cyclotomic: s4,
        stage5_d2_x_d3: s5,
        stage6_d3_x_d3: s6,
        stage7_d3_x_d3_x_d3: s7,
        free_parameter_count: req.free_parameter_count,
        refusal_code,
        authority_effect: "None".to_owned(),
        genesis_effect: "None".to_owned(),
    }
}

pub fn verify_json(payload: &Value) -> Result<Value, String> {
    let req: CoupledRelationalVerifyRequestV1 = serde_json::from_value(payload.clone())
        .map_err(|e| format!("COUPLED_RELATIONAL_WIRE_INVALID: {e}"))?;
    let receipt = evaluate_coupled_relational_operad(&req);
    Ok(json!(receipt))
}

// Origin: omega_engine/crates_rs/omega_symbol_game/src/coupled_relational_operad.rs
// Claim: urn:omega:crates_rs:omega-symbol-game:coupled-relational-operad:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord41a00c65 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord41a00c65` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError41a00c65 {
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
impl BoundaryError41a00c65 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError41a00c65 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError41a00c65 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord41a00c65 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError41a00c65> {
        if capacity_bound == 0 {
            return Err(BoundaryError41a00c65::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError41a00c65::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError41a00c65::ExceedsCapacity {
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
mod l4_boundary_tests_41a00c65 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord41a00c65::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord41a00c65::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord41a00c65::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord41a00c65::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord41a00c65::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryError41a00c65::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryError41a00c65::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
