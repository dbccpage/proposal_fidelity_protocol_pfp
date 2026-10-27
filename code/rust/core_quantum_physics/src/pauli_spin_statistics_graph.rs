// AuthorityEffect: None.

//! QM-223: Identical particles, Pauli exclusion, topological spin-statistics
//! on finite graphs (`Conf_2(G)`), Jordan-Wigner CAR Clifford nilpotency,
//! Slater determinant vs. bosonic permanent, and atomic shell capacities `2*n^2`
//! over `Q`.
//!
//! All arithmetic is exact over `Rational` (`Q`) and integer graph combinatorics.

use std::collections::{BTreeSet, VecDeque};

use core_number_theory::rational::{ri, rq, Rational};

/// Refusals for finite-graph spin-statistics and Pauli exclusion audits.
#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum SpinStatisticsError {
    #[error("vertex count must be at least 2, got {0}")]
    TooFewVertices(usize),
    #[error("edge ({u}, {v}) is out of range for {n_vertices} vertices or is a self-loop")]
    InvalidEdge {
        u: usize,
        v: usize,
        n_vertices: usize,
    },
    #[error("orbital matrix must be non-empty and square, got {rows}x{cols}")]
    NonSquareOrbitalMatrix { rows: usize, cols: usize },
    #[error("shell principal quantum number n must be >= 1, got {0}")]
    InvalidPrincipalNumber(u32),
}

/// Summary of the 2-particle unordered configuration 1-skeleton `Conf_2^(1)(G)`
/// and Abramsky-Ghrist square 2-complex `Conf_2^(2)(G)` of a finite simple graph `G`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Conf2GraphReport {
    pub base_vertices: usize,
    pub base_edges: usize,
    pub conf2_vertices: usize,
    pub conf2_edges: usize,
    pub conf2_components: usize,
    pub conf2_betti_1: usize,
    pub conf2_squares: usize,
    pub conf2_2complex_betti_1_q: usize,
    pub conf2_2complex_betti_1_f2: usize,
    pub conf2_z2_torsion_rank: usize,
    pub has_y_junction_exchange_cycle: bool,
}

fn rank_over_q(rows: &[Vec<i64>], ncols: usize) -> usize {
    if rows.is_empty() || ncols == 0 {
        return 0;
    }
    let mut mat: Vec<Vec<Rational>> = rows
        .iter()
        .map(|row| row.iter().map(|&x| ri(x)).collect())
        .collect();
    let mut rank = 0usize;
    for col in 0..ncols {
        let Some(piv) = (rank..mat.len()).find(|&r| mat[r][col] != ri(0)) else {
            continue;
        };
        mat.swap(rank, piv);
        let lead = mat[rank][col].clone();
        for c in 0..ncols {
            mat[rank][c] = &mat[rank][c] / &lead;
        }
        let piv_row = mat[rank].clone();
        for r in 0..mat.len() {
            if r != rank && mat[r][col] != ri(0) {
                let factor = mat[r][col].clone();
                for c in 0..ncols {
                    let prod = &factor * &piv_row[c];
                    mat[r][c] = &mat[r][c] - &prod;
                }
            }
        }
        rank += 1;
    }
    rank
}

fn rank_over_f2(rows: &[Vec<i64>], ncols: usize) -> usize {
    if rows.is_empty() || ncols == 0 {
        return 0;
    }
    let mut mat: Vec<Vec<u8>> = rows
        .iter()
        .map(|row| row.iter().map(|&x| (x.rem_euclid(2)) as u8).collect())
        .collect();
    let mut rank = 0usize;
    for col in 0..ncols {
        let Some(piv) = (rank..mat.len()).find(|&r| mat[r][col] != 0) else {
            continue;
        };
        mat.swap(rank, piv);
        let piv_row = mat[rank].clone();
        for r in 0..mat.len() {
            if r != rank && mat[r][col] != 0 {
                for c in 0..ncols {
                    mat[r][c] ^= piv_row[c];
                }
            }
        }
        rank += 1;
    }
    rank
}

fn build_base_graph(
    n_vertices: usize,
    edges: &[(usize, usize)],
) -> Result<(Vec<BTreeSet<usize>>, Vec<(usize, usize)>), SpinStatisticsError> {
    if n_vertices < 2 {
        return Err(SpinStatisticsError::TooFewVertices(n_vertices));
    }
    let mut base_adj = vec![BTreeSet::new(); n_vertices];
    let mut canonical_base_edges = BTreeSet::new();
    for &(u, v) in edges {
        if u >= n_vertices || v >= n_vertices || u == v {
            return Err(SpinStatisticsError::InvalidEdge { u, v, n_vertices });
        }
        let (a, b) = if u < v { (u, v) } else { (v, u) };
        canonical_base_edges.insert((a, b));
        base_adj[a].insert(b);
        base_adj[b].insert(a);
    }
    let sorted_base_edges = canonical_base_edges.into_iter().collect();
    Ok((base_adj, sorted_base_edges))
}

fn is_single_particle_hop(
    (u1, v1): (usize, usize),
    (u2, v2): (usize, usize),
    base_adj: &[BTreeSet<usize>],
) -> bool {
    if u1 == u2 {
        base_adj[v1].contains(&v2)
    } else if u1 == v2 {
        base_adj[v1].contains(&u2)
    } else if v1 == u2 {
        base_adj[u1].contains(&v2)
    } else if v1 == v2 {
        base_adj[u1].contains(&u2)
    } else {
        false
    }
}

#[allow(clippy::type_complexity)]
fn build_conf2_skeleton(
    n_vertices: usize,
    base_adj: &[BTreeSet<usize>],
) -> (
    usize,
    std::collections::BTreeMap<(usize, usize), usize>,
    Vec<BTreeSet<usize>>,
    std::collections::BTreeMap<(usize, usize), usize>,
    usize,
) {
    let mut conf_nodes = Vec::new();
    let mut node_to_idx = std::collections::BTreeMap::new();
    for u in 0..n_vertices {
        for v in (u + 1)..n_vertices {
            node_to_idx.insert((u, v), conf_nodes.len());
            conf_nodes.push((u, v));
        }
    }
    let n_conf = conf_nodes.len();
    let mut conf_adj = vec![BTreeSet::new(); n_conf];
    let mut conf_edge_to_idx = std::collections::BTreeMap::new();
    let mut conf_edges = 0usize;

    for i in 0..n_conf {
        for j in (i + 1)..n_conf {
            if is_single_particle_hop(conf_nodes[i], conf_nodes[j], base_adj) {
                conf_adj[i].insert(j);
                conf_adj[j].insert(i);
                conf_edge_to_idx.insert((i, j), conf_edges);
                conf_edges += 1;
            }
        }
    }
    (n_conf, node_to_idx, conf_adj, conf_edge_to_idx, conf_edges)
}

fn count_connected_components(conf_adj: &[BTreeSet<usize>]) -> usize {
    let n_conf = conf_adj.len();
    let mut visited = vec![false; n_conf];
    let mut components = 0usize;
    for start in 0..n_conf {
        if visited[start] {
            continue;
        }
        components += 1;
        let mut queue = VecDeque::new();
        visited[start] = true;
        queue.push_back(start);
        while let Some(curr) = queue.pop_front() {
            for &nbr in &conf_adj[curr] {
                if !visited[nbr] {
                    visited[nbr] = true;
                    queue.push_back(nbr);
                }
            }
        }
    }
    components
}

fn build_square_row(
    (a1, b1): (usize, usize),
    (a2, b2): (usize, usize),
    node_to_idx: &std::collections::BTreeMap<(usize, usize), usize>,
    conf_edge_to_idx: &std::collections::BTreeMap<(usize, usize), usize>,
    conf_edges: usize,
) -> Option<Vec<i64>> {
    if a1 == a2 || a1 == b2 || b1 == a2 || b1 == b2 {
        return None;
    }
    let pair_ord = |x: usize, y: usize| if x < y { (x, y) } else { (y, x) };
    let v00 = node_to_idx[&pair_ord(a1, a2)];
    let v10 = node_to_idx[&pair_ord(b1, a2)];
    let v11 = node_to_idx[&pair_ord(b1, b2)];
    let v01 = node_to_idx[&pair_ord(a1, b2)];
    let mut row = vec![0i64; conf_edges];
    for (p, q) in [(v00, v10), (v10, v11), (v11, v01), (v01, v00)] {
        if p < q {
            row[conf_edge_to_idx[&(p, q)]] += 1;
        } else {
            row[conf_edge_to_idx[&(q, p)]] -= 1;
        }
    }
    Some(row)
}

/// Construct the unordered 2-particle non-colliding configuration 1-skeleton `Conf_2^(1)(G)`
/// and square 2-complex `Conf_2^(2)(G)`, computing vertex count, edge count, connected
/// components, 1-skeleton `b_1`, 2-cell commuting square count, 2-complex Betti numbers
/// over `Q` and `F_2`, and the `Z_2` exchange torsion rank `b_1^(2)(F_2) - b_1^(2)(Q)`.
pub fn analyze_conf2_graph(
    n_vertices: usize,
    edges: &[(usize, usize)],
) -> Result<Conf2GraphReport, SpinStatisticsError> {
    let (base_adj, sorted_base_edges) = build_base_graph(n_vertices, edges)?;
    let (n_conf, node_to_idx, conf_adj, conf_edge_to_idx, conf_edges) =
        build_conf2_skeleton(n_vertices, &base_adj);
    let components = count_connected_components(&conf_adj);
    let betti_1 = (conf_edges + components).saturating_sub(n_conf);

    let mut square_rows: Vec<Vec<i64>> = Vec::new();
    for idx1 in 0..sorted_base_edges.len() {
        for idx2 in (idx1 + 1)..sorted_base_edges.len() {
            if let Some(row) = build_square_row(
                sorted_base_edges[idx1],
                sorted_base_edges[idx2],
                &node_to_idx,
                &conf_edge_to_idx,
                conf_edges,
            ) {
                square_rows.push(row);
            }
        }
    }

    let conf2_squares = square_rows.len();
    let rq_d2 = rank_over_q(&square_rows, conf_edges);
    let r2_d2 = rank_over_f2(&square_rows, conf_edges);
    let conf2_2complex_betti_1_q = betti_1.saturating_sub(rq_d2);
    let conf2_2complex_betti_1_f2 = betti_1.saturating_sub(r2_d2);
    let conf2_z2_torsion_rank = conf2_2complex_betti_1_f2.saturating_sub(conf2_2complex_betti_1_q);
    let has_y_junction_exchange_cycle = conf2_z2_torsion_rank > 0;

    Ok(Conf2GraphReport {
        base_vertices: n_vertices,
        base_edges: sorted_base_edges.len(),
        conf2_vertices: n_conf,
        conf2_edges: conf_edges,
        conf2_components: components,
        conf2_betti_1: betti_1,
        conf2_squares,
        conf2_2complex_betti_1_q,
        conf2_2complex_betti_1_f2,
        conf2_z2_torsion_rank,
        has_y_junction_exchange_cycle,
    })
}

/// Exact 2x2 Slater determinant `a*d - b*c` and bosonic permanent `a*d + b*c` over `Q`.
pub fn two_particle_slater_and_permanent(
    a: &Rational,
    b: &Rational,
    c: &Rational,
    d: &Rational,
) -> (Rational, Rational) {
    let slater = a * d - b * c;
    let permanent = a * d + b * c;
    (slater, permanent)
}

/// Exact NxN determinant (`alternating = true`, fermionic Slater determinant)
/// or permanent (`alternating = false`, bosonic permanent) over `Q` for `N <= 6`.
pub fn orbital_slater_or_permanent(
    matrix: &[Vec<Rational>],
    alternating: bool,
) -> Result<Rational, SpinStatisticsError> {
    let n = matrix.len();
    if n == 0 || n > 6 {
        return Err(SpinStatisticsError::NonSquareOrbitalMatrix { rows: n, cols: 0 });
    }
    for row in matrix {
        if row.len() != n {
            return Err(SpinStatisticsError::NonSquareOrbitalMatrix {
                rows: n,
                cols: row.len(),
            });
        }
    }
    let group = core_lie_theory::finite_group::symmetric_group(n)
        .map_err(|_| SpinStatisticsError::NonSquareOrbitalMatrix { rows: n, cols: n })?;
    let mut total = ri(0);
    for perm in group.elements() {
        let sign_i8 = crate::pair_exchange_characters::permutation_character(perm, alternating)
            .map_err(|_| SpinStatisticsError::NonSquareOrbitalMatrix { rows: n, cols: n })?;
        let mut prod = ri(i64::from(sign_i8));
        for i in 0..n {
            prod = &prod * &matrix[i][perm[i]];
        }
        total = &total + &prod;
    }
    Ok(total)
}

/// Verify the 2-mode Jordan-Wigner Canonical Anticommutation Relations (CAR) over `Q`
/// on the 4-dimensional Fock space `Lambda^*(Q^2) = span(|00>, |01>, |10>, |11>)`:
/// `c_1 = sigma^- (x) I_2`, `c_2 = sigma^z (x) sigma^-`.
/// Returns `(all_nilpotent, anticommutators_exact, number_trace_sum)`.
pub fn verify_two_mode_jordan_wigner_car() -> (bool, bool, Rational) {
    // 4x4 matrices over Q
    // Basis: 0=|00>, 1=|01>, 2=|10>, 3=|11>
    // c_1 annihilates mode 1: |10> -> |00>, |11> -> |01>
    let mut c1 = vec![vec![ri(0); 4]; 4];
    c1[0][2] = ri(1);
    c1[1][3] = ri(1);

    // c_2 annihilates mode 2 with Jordan-Wigner sign (-1)^{n_1}:
    // |01> -> +|00>, |11> -> -|10>
    let mut c2 = vec![vec![ri(0); 4]; 4];
    c2[0][1] = ri(1);
    c2[2][3] = ri(-1);

    let c1_dag = transpose_4(&c1);
    let c2_dag = transpose_4(&c2);

    let zero4 = vec![vec![ri(0); 4]; 4];
    let id4 = identity_4();

    // Nilpotency (Pauli exclusion): c1^2 = 0, c2^2 = 0, (c1^+)^2 = 0, (c2^+)^2 = 0
    let all_nilpotent = mul_4(&c1, &c1) == zero4
        && mul_4(&c2, &c2) == zero4
        && mul_4(&c1_dag, &c1_dag) == zero4
        && mul_4(&c2_dag, &c2_dag) == zero4
        && mul_4(&mul_4(&c1_dag, &c2_dag), &c1_dag) == zero4;

    // Anticommutators: {c_i, c_j^+} = delta_{ij} I_4 and {c_1, c_2} = 0
    let ac_11 = add_4(&mul_4(&c1, &c1_dag), &mul_4(&c1_dag, &c1));
    let ac_22 = add_4(&mul_4(&c2, &c2_dag), &mul_4(&c2_dag, &c2));
    let ac_12 = add_4(&mul_4(&c1, &c2_dag), &mul_4(&c2_dag, &c1));
    let ac_c1_c2 = add_4(&mul_4(&c1, &c2), &mul_4(&c2, &c1));

    let anticommutators_exact =
        ac_11 == id4 && ac_22 == id4 && ac_12 == zero4 && ac_c1_c2 == zero4;

    let n1 = mul_4(&c1_dag, &c1);
    let n2 = mul_4(&c2_dag, &c2);
    let n_tot = add_4(&n1, &n2);
    let mut tr_sum = ri(0);
    for i in 0..4 {
        tr_sum = &tr_sum + &n_tot[i][i];
    }

    (all_nilpotent, anticommutators_exact, tr_sum)
}

/// Compute the exact Pauli shell capacity `2 * sum_{l=0}^{n-1} (2*l + 1) = 2 * n^2`
/// and the orbital degeneracy `n^2` for principal quantum number `n >= 1`.
pub fn pauli_shell_capacity(n: u32) -> Result<(u32, u32), SpinStatisticsError> {
    if n == 0 {
        return Err(SpinStatisticsError::InvalidPrincipalNumber(n));
    }
    let orbital_sum: u32 = (0..n).map(|l| 2 * l + 1).sum();
    let capacity = 2 * orbital_sum;
    Ok((orbital_sum, capacity))
}

/// Noble-gas cumulative atomic numbers `Z in [2, 10, 18, 36, 54, 86, 118]`
/// from the finite Madelung `(n + l, n)` ordering and Pauli `2*(2l + 1)` subshell capacities.
pub fn madelung_noble_gas_closures() -> Vec<u32> {
    // Subshells ordered by (n + l, n) up to n + l = 8, terminating each period at a p (l=1) or 1s subshell
    let mut subshells: Vec<(u32, u32, u32)> = Vec::new();
    for sum_nl in 1..=8u32 {
        for n in 1..=sum_nl {
            let l = sum_nl - n;
            if l < n && n <= 7 {
                subshells.push((n, l, 2 * (2 * l + 1)));
            }
        }
    }
    let mut cumulative = 0u32;
    let mut closures = Vec::new();
    for (n, l, cap) in subshells {
        cumulative += cap;
        if (n == 1 && l == 0) || (n >= 2 && l == 1) {
            closures.push(cumulative);
        }
    }
    closures
}

/// Complete QM-223 verification certificate over `Q`.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm223SpinStatisticsCertificate {
    pub conf2_p3: Conf2GraphReport,
    pub conf2_y_star: Conf2GraphReport,
    pub conf2_c4: Conf2GraphReport,
    pub conf2_k4: Conf2GraphReport,
    pub conf2_k5: Conf2GraphReport,
    pub pauli_same_orbital_slater: Rational,
    pub swap_ratio_fermion: Rational,
    pub swap_ratio_boson: Rational,
    pub hbt_boson_bunching_ratio: Rational,
    pub jordan_wigner_nilpotent: bool,
    pub jordan_wigner_car_exact: bool,
    pub jordan_wigner_fock_number_trace: Rational,
    pub shell_capacities_1_to_4: Vec<u32>,
    pub noble_gas_atomic_numbers: Vec<u32>,
}

fn complete_graph_edges(n: usize) -> Vec<(usize, usize)> {
    let mut edges = Vec::new();
    for u in 0..n {
        for v in (u + 1)..n {
            edges.push((u, v));
        }
    }
    edges
}

/// Run the full QM-223 finite-graph spin-statistics and Pauli exclusion verification.
pub fn verify_qm223_spin_statistics_graph() -> Result<Qm223SpinStatisticsCertificate, SpinStatisticsError> {
    let conf2_p3 = analyze_conf2_graph(3, &[(0, 1), (1, 2)])?;
    let conf2_y_star = analyze_conf2_graph(4, &[(0, 1), (0, 2), (0, 3)])?;
    let conf2_c4 = analyze_conf2_graph(4, &[(0, 1), (1, 2), (2, 3), (3, 0)])?;
    let conf2_k4 = analyze_conf2_graph(4, &complete_graph_edges(4))?;
    let conf2_k5 = analyze_conf2_graph(5, &complete_graph_edges(5))?;

    let a = rq(3, 5);
    let b = rq(4, 5);
    let c = rq(5, 13);
    let d = rq(12, 13);

    let (slater_same, _) = two_particle_slater_and_permanent(&a, &b, &a, &b);
    let (slater_12, perm_12) = two_particle_slater_and_permanent(&a, &b, &c, &d);
    let (slater_21, perm_21) = two_particle_slater_and_permanent(&c, &d, &a, &b);
    let swap_ratio_fermion = &slater_21 / &slater_12;
    let swap_ratio_boson = &perm_21 / &perm_12;

    let (_, perm_coincide) = two_particle_slater_and_permanent(&a, &b, &a, &b);
    let boson_coincide_weight = &perm_coincide * &perm_coincide;
    let distinguishable_coincide_weight = &(&a * &b) * &(&a * &b) + &(&b * &a) * &(&b * &a);
    let hbt_boson_bunching_ratio = &boson_coincide_weight / &distinguishable_coincide_weight;

    let (jw_nil, jw_car, jw_tr) = verify_two_mode_jordan_wigner_car();

    let mut shell_caps = Vec::new();
    for n in 1..=4 {
        let (_, cap) = pauli_shell_capacity(n)?;
        shell_caps.push(cap);
    }

    Ok(Qm223SpinStatisticsCertificate {
        conf2_p3,
        conf2_y_star,
        conf2_c4,
        conf2_k4,
        conf2_k5,
        pauli_same_orbital_slater: slater_same,
        swap_ratio_fermion,
        swap_ratio_boson,
        hbt_boson_bunching_ratio,
        jordan_wigner_nilpotent: jw_nil,
        jordan_wigner_car_exact: jw_car,
        jordan_wigner_fock_number_trace: jw_tr,
        shell_capacities_1_to_4: shell_caps,
        noble_gas_atomic_numbers: madelung_noble_gas_closures(),
    })
}

fn identity_4() -> Vec<Vec<Rational>> {
    let mut m = vec![vec![ri(0); 4]; 4];
    for i in 0..4 {
        m[i][i] = ri(1);
    }
    m
}

fn transpose_4(m: &[Vec<Rational>]) -> Vec<Vec<Rational>> {
    let mut out = vec![vec![ri(0); 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            out[j][i] = m[i][j].clone();
        }
    }
    out
}

fn add_4(a: &[Vec<Rational>], b: &[Vec<Rational>]) -> Vec<Vec<Rational>> {
    let mut out = vec![vec![ri(0); 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            out[i][j] = &a[i][j] + &b[i][j];
        }
    }
    out
}

fn mul_4(a: &[Vec<Rational>], b: &[Vec<Rational>]) -> Vec<Vec<Rational>> {
    let mut out = vec![vec![ri(0); 4]; 4];
    for i in 0..4 {
        for k in 0..4 {
            for j in 0..4 {
                let prod = &a[i][k] * &b[k][j];
                out[i][j] = &out[i][j] + &prod;
            }
        }
    }
    out
}

// Origin: engine/crates_rs/core_quantum_physics/src/pauli_spin_statistics_graph.rs
// Claim: urn:core:crates_rs:core-quantum-physics:pauli-spin-statistics-graph:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn conf2_graph_topologies_separate_1d_2d_and_3connected() {
        let cert = verify_qm223_spin_statistics_graph().expect("valid QM-223 certificate");
        // 1D P_3: 3 vertices, 2 edges, b_1 = 0 (no exchange loops)
        assert_eq!(cert.conf2_p3.conf2_vertices, 3);
        assert_eq!(cert.conf2_p3.conf2_edges, 2);
        assert_eq!(cert.conf2_p3.conf2_betti_1, 0);
        assert_eq!(cert.conf2_p3.conf2_z2_torsion_rank, 0);
        assert!(!cert.conf2_p3.has_y_junction_exchange_cycle);

        // Star Y = K_{1,3}: 6 vertices, 6 edges, b_1 = 1, 0 squares, torsion-free Z
        assert_eq!(cert.conf2_y_star.conf2_vertices, 6);
        assert_eq!(cert.conf2_y_star.conf2_edges, 6);
        assert_eq!(cert.conf2_y_star.conf2_betti_1, 1);
        assert_eq!(cert.conf2_y_star.conf2_squares, 0);
        assert_eq!(cert.conf2_y_star.conf2_2complex_betti_1_q, 1);
        assert_eq!(cert.conf2_y_star.conf2_z2_torsion_rank, 0);
        assert!(!cert.conf2_y_star.has_y_junction_exchange_cycle);

        // 2D C_4: 6 vertices, 8 edges, b_1 = 3, 2 squares, b_1^(2)(Q) = 1, torsion-free
        assert_eq!(cert.conf2_c4.conf2_vertices, 6);
        assert_eq!(cert.conf2_c4.conf2_edges, 8);
        assert_eq!(cert.conf2_c4.conf2_betti_1, 3);
        assert_eq!(cert.conf2_c4.conf2_squares, 2);
        assert_eq!(cert.conf2_c4.conf2_2complex_betti_1_q, 1);
        assert_eq!(cert.conf2_c4.conf2_z2_torsion_rank, 0);
        assert!(!cert.conf2_c4.has_y_junction_exchange_cycle);

        // Planar 3-connected K_4: 6 vertices, 12 edges, b_1 = 7, 3 squares, b_1^(2)(Q) = 4, torsion-free
        assert_eq!(cert.conf2_k4.conf2_vertices, 6);
        assert_eq!(cert.conf2_k4.conf2_edges, 12);
        assert_eq!(cert.conf2_k4.conf2_betti_1, 7);
        assert_eq!(cert.conf2_k4.conf2_squares, 3);
        assert_eq!(cert.conf2_k4.conf2_2complex_betti_1_q, 4);
        assert_eq!(cert.conf2_k4.conf2_z2_torsion_rank, 0);
        assert!(!cert.conf2_k4.has_y_junction_exchange_cycle);

        // Nonplanar 3-connected K_5: 10 vertices, 30 edges, b_1 = 21, 15 squares,
        // b_1^(2)(Q) = 6, b_1^(2)(F_2) = 7, Z_2 torsion rank = 1
        assert_eq!(cert.conf2_k5.conf2_vertices, 10);
        assert_eq!(cert.conf2_k5.conf2_edges, 30);
        assert_eq!(cert.conf2_k5.conf2_betti_1, 21);
        assert_eq!(cert.conf2_k5.conf2_squares, 15);
        assert_eq!(cert.conf2_k5.conf2_2complex_betti_1_q, 6);
        assert_eq!(cert.conf2_k5.conf2_2complex_betti_1_f2, 7);
        assert_eq!(cert.conf2_k5.conf2_z2_torsion_rank, 1);
        assert!(cert.conf2_k5.has_y_junction_exchange_cycle);
    }

    #[test]
    fn slater_pauli_exclusion_and_jordan_wigner_car_hold_over_q() {
        let cert = verify_qm223_spin_statistics_graph().expect("valid QM-223 certificate");
        assert_eq!(cert.pauli_same_orbital_slater, ri(0));
        assert_eq!(cert.swap_ratio_fermion, ri(-1));
        assert_eq!(cert.swap_ratio_boson, ri(1));
        assert_eq!(cert.hbt_boson_bunching_ratio, ri(2));
        assert!(cert.jordan_wigner_nilpotent);
        assert!(cert.jordan_wigner_car_exact);
        assert_eq!(cert.jordan_wigner_fock_number_trace, ri(4));
        assert_eq!(cert.shell_capacities_1_to_4, vec![2, 8, 18, 32]);
        assert_eq!(
            cert.noble_gas_atomic_numbers,
            vec![2, 10, 18, 36, 54, 86, 118]
        );
    }

    #[test]
    fn three_particle_slater_vanishes_on_duplicate_row_and_flips_on_swap() {
        let row1 = vec![rq(1, 2), rq(1, 3), rq(1, 6)];
        let row2 = vec![rq(2, 5), rq(3, 5), rq(1, 5)];
        let row3 = vec![rq(3, 7), rq(2, 7), rq(4, 7)];

        let dup = vec![row1.clone(), row1.clone(), row2.clone()];
        assert_eq!(
            orbital_slater_or_permanent(&dup, true).expect("3x3 slater"),
            ri(0)
        );

        let m123 = vec![row1.clone(), row2.clone(), row3.clone()];
        let m213 = vec![row2, row1, row3];
        let det_123 = orbital_slater_or_permanent(&m123, true).expect("det 123");
        let det_213 = orbital_slater_or_permanent(&m213, true).expect("det 213");
        assert_eq!(det_213, -det_123);

        let perm_123 = orbital_slater_or_permanent(&m123, false).expect("perm 123");
        let perm_213 = orbital_slater_or_permanent(&m213, false).expect("perm 213");
        assert_eq!(perm_213, perm_123);
    }
}
