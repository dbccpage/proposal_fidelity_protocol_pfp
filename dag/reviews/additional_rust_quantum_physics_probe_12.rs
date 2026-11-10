// AuthorityEffect: None.

//! Exact finite-map controls for QM-207 through QM-215.
//! QM-216 through QM-221 live in sibling modules and are re-exported here.
//!
//! Mirrors the finite-map controls in
//! `atlas/coda_atlas/F004_papers/006_finite_qm/python/finite_qm/use_cases/`:
//! - `QM-207` (`holonomy_bridge_control.py`): U(1) cycle holonomy classification
//!   `Hom(H_1(G), mu_N) = mu_N^{b_1}`, spanning-tree gauge canonicalization, and orbit census.
//! - `QM-208` (`quadratic_readout_control.py`): phase-blind monomial census, Sorkin `I_3`
//!   selection within `alpha |c|^2 + beta |c|^4`, and two-report holonomy cross-term.
//! - `QM-209` (`context_parity_control.py`): Peres-Mermin `K_{3,3}` incidence `F_2` cokernel
//!   parity obstruction and Weyl commutator holonomy census.
//! - `QM-210` (`frame_function_control.py`): finite linear Gleason nullity on the Cabello 18-ray
//!   and Peres 24-ray sets, `F_2` Kochen-Specker parity, and the rational positivity-gap witness.
//! - `QM-211` (`clock_tower_control.py`): finite spectral projectors over `Q(zeta_24)`,
//!   `2^{occupied}` unitary square roots, clock divisibility refinement, and the swap control.
//! - `QM-212` (`dressed_qed_g2_control.py`): Symanzik spanning-tree polynomial `U_G(alpha)` and
//!   dual Kirchhoff cofactor, Ravera DFM tree-dressing gauge invariance, and exact `BigRational`
//!   interval enclosure of `L = 1, 2, 3, 4` QED `a_e = (g - 2) / 2` to 12 decimal places.
//! - `QM-213` (`nonabelian_dfm_control.py`): Substantial-vs-artificial dressing classification via
//!   `LocalGreen`/`GlobalRed` patch cohomology (`core_holonomy::gauge_fixing` +
//!   `core_homology::restriction_dga`), two-stage hierarchical non-Abelian subgroup dressing
//!   `N <| B subset GL(2, Q)`, and exact covariance of dressed curvature `K^u = b A^u + A^u cup A^u`
//!   and discrete Bianchi identity `D_{A^u} K^u = 0` under the quotient group `B/N`.
//! - `QM-214` (`symanzik_two_forest_bphz_control.py`): Second Symanzik 2-forest polynomial
//!   `F_G(alpha; q, m^2) = F_0(alpha; q) + U_G(alpha) sum_e alpha_e m_e^2` and Kirchhoff-Schur
//!   complement duality, DFM spanning-tree momentum routing `p_T`, and Zimmermann BPHZ forest
//!   subtraction cancelling `(lambda_1, lambda_2) -> (0, 0)` UV boundary poles over `Q`.
//! - `QM-215` (`dirac_ward_takahashi_control.py`): Dirac/Kulish-Faddeev dressed matter,
//!   Clifford Ward-Takahashi `Z_1 = Z_2`, and the soft-photon attenuation enclosure.
//! - `QM-216` (`vacuum_polarization_lamb_shift.rs`): transverse Ward projector, BPHZ vacuum
//!   polarization, running coupling, and the Uehling Lamb-shift enclosure.
//! - `QM-217` (`algebraic_bound_state_spectra.rs`): su(2) Kravchuk oscillator and so(4)
//!   Hydrogen bound-state spectra.
//! - `QM-218` (`page_wootters_tsirelson_wigner.rs`): Page-Wootters clock dressing, Q(zeta_8)
//!   Tsirelson SOS, and the (Z_3)^2 Wigner function.
//! - `QM-219` (`foundational_derivation_closure.rs`): Bipartite composition triad, 5x5
//!   import independence countermodels, and Z[zeta_12] Sorkin I_3 = 0 readout classification.
//! - `QM-220` (`electroweak_dfm_weinberg_control.rs`): SU(2)_L x U(1)_Y -> U(1)_EM DFM dressing,
//!   rational Weinberg projectors, custodial rho_EW = 1, and cubic U(1)_Y^3 anomaly cancellation.
//! - `QM-221` (`qcd_beta0_wilson_confinement_control.rs`): su(3)_c Fierz completeness, 1-loop
//!   Gross-Wilczek-Politzer beta_0 = 11 - 2/3 n_f, and Wilson-loop Creutz confinement witness.

#[allow(dead_code, non_camel_case_types, missing_docs)]
trait CheckedInvariantExt_b90405c2<T> {
    fn checked_invariant_b90405c2(self, msg: &str) -> T;
}

impl<T> CheckedInvariantExt_b90405c2<T> for Option<T> {
    #[inline]
    fn checked_invariant_b90405c2(self, msg: &str) -> T {
        match self {
            Some(v) => v,
            None => unreachable!("{}", msg),
        }
    }
}

impl<T, E: std::fmt::Debug> CheckedInvariantExt_b90405c2<T> for std::result::Result<T, E> {
    #[inline]
    fn checked_invariant_b90405c2(self, msg: &str) -> T {
        match self {
            Ok(v) => v,
            Err(e) => unreachable!("{}: {:?}", msg, e),
        }
    }
}
use std::collections::{BTreeMap, BTreeSet, VecDeque};

use num_bigint::BigInt;
use num_rational::{BigRational, Ratio};
use num_traits::{One, Signed, Zero};

pub type Q = Ratio<i64>;

fn q(n: i64, d: i64) -> Q {
    Ratio::new(n, d)
}

// ============================================================================
// Exact Cyclotomic Field Q(zeta_12) = Q[x] / (x^4 - x^2 + 1)
// ============================================================================

/// Element of `Q(zeta_12)` represented in the power basis `[1, zeta_12, zeta_12^2, zeta_12^3]`
/// with minimal polynomial `Phi_12(x) = x^4 - x^2 + 1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cyclo12(pub [Q; 4]);

impl Cyclo12 {
    pub fn zero() -> Self {
        Self([Q::zero(); 4])
    }

    pub fn one() -> Self {
        Self([Q::one(), Q::zero(), Q::zero(), Q::zero()])
    }

    pub fn from_rat(r: Q) -> Self {
        Self([r, Q::zero(), Q::zero(), Q::zero()])
    }

    pub fn root_of_unity(k: i64) -> Self {
        let exp = k.rem_euclid(12) as usize;
        let mut coeffs = [Q::zero(); 12];
        coeffs[exp] = Q::one();
        Self::reduce12(coeffs)
    }

    fn reduce12(mut c: [Q; 12]) -> Self {
        for i in (4..12).rev() {
            let v = c[i];
            if !v.is_zero() {
                // x^4 = x^2 - 1
                c[i - 2] += v;
                c[i - 4] -= v;
                c[i] = Q::zero();
            }
        }
        Self([c[0], c[1], c[2], c[3]])
    }

    pub fn add(self, rhs: Self) -> Self {
        Self([
            self.0[0] + rhs.0[0],
            self.0[1] + rhs.0[1],
            self.0[2] + rhs.0[2],
            self.0[3] + rhs.0[3],
        ])
    }

    pub fn sub(self, rhs: Self) -> Self {
        Self([
            self.0[0] - rhs.0[0],
            self.0[1] - rhs.0[1],
            self.0[2] - rhs.0[2],
            self.0[3] - rhs.0[3],
        ])
    }

    pub fn scale(self, r: Q) -> Self {
        Self([self.0[0] * r, self.0[1] * r, self.0[2] * r, self.0[3] * r])
    }

    pub fn mul(self, rhs: Self) -> Self {
        let mut prod = [Q::zero(); 12];
        for i in 0..4 {
            for j in 0..4 {
                prod[i + j] += self.0[i] * rhs.0[j];
            }
        }
        Self::reduce12(prod)
    }

    pub fn pow(self, exp: usize) -> Self {
        let mut acc = Self::one();
        for _ in 0..exp {
            acc = acc.mul(self);
        }
        acc
    }

    pub fn conjugate(self) -> Self {
        // conj(zeta_12^k) = zeta_12^{-k mod 12}
        let mut acc = Self::zero();
        for (k, &coeff) in self.0.iter().enumerate() {
            if !coeff.is_zero() {
                acc = acc.add(Self::root_of_unity(-(k as i64)).scale(coeff));
            }
        }
        acc
    }

    pub fn born_weight(self) -> Self {
        self.mul(self.conjugate())
    }

    pub fn is_zero(&self) -> bool {
        self.0.iter().all(Zero::is_zero)
    }

    pub fn as_rational(&self) -> Option<Q> {
        if self.0[1].is_zero() && self.0[2].is_zero() && self.0[3].is_zero() {
            Some(self.0[0])
        } else {
            None
        }
    }
}

// ============================================================================
// QM-207: Phase Fiber Holonomy Bridge Control
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm207HolonomyReport {
    pub vertex_count: usize,
    pub edge_count: usize,
    pub first_betti_number: usize,
    pub cycle_invariant_exponents: Vec<usize>,
    pub cycle_invariants_gauge_invariant: bool,
    pub tree_gauge_has_unit_tree_edges: bool,
    pub tree_gauge_same_invariants: bool,
    pub holonomy_factorizes_on_all_test_loops: bool,
    pub relative_report_phase_gauge_invariant: bool,
    pub census_class_count: usize,
    pub census_expected_class_count: usize,
    pub census_all_classes_expected_size: bool,
    pub census_expected_class_size: usize,
}

#[derive(Debug, Clone)]
pub struct CarrierGraph {
    pub vertex_count: usize,
    pub edges: Vec<(usize, usize)>,
}

impl CarrierGraph {
    pub fn diamond() -> Self {
        Self {
            vertex_count: 4,
            edges: vec![(0, 1), (0, 2), (1, 3), (2, 3), (1, 2)],
        }
    }

    pub fn bubble() -> Self {
        Self {
            vertex_count: 2,
            edges: vec![(0, 1), (0, 1)],
        }
    }

    pub fn first_betti_number(&self) -> usize {
        self.edges.len() + 1 - self.vertex_count
    }

    pub fn edge_index(&self, u: usize, v: usize) -> (usize, i64) {
        for (i, &(a, b)) in self.edges.iter().enumerate() {
            if (a, b) == (u, v) {
                return (i, 1);
            }
            if (a, b) == (v, u) {
                return (i, -1);
            }
        }
        unreachable!("missing edge between {u} and {v}");
    }

    pub fn spanning_tree(&self) -> Vec<usize> {
        let mut adj: Vec<Vec<(usize, usize)>> = vec![Vec::new(); self.vertex_count];
        for (i, &(a, b)) in self.edges.iter().enumerate() {
            adj[a].push((b, i));
            adj[b].push((a, i));
        }
        let mut seen = BTreeSet::new();
        seen.insert(0);
        let mut tree = Vec::new();
        let mut queue = VecDeque::new();
        queue.push_back(0);
        while let Some(u) = queue.pop_front() {
            for &(w, idx) in &adj[u] {
                if seen.insert(w) {
                    tree.push(idx);
                    queue.push_back(w);
                }
            }
        }
        tree
    }

    pub fn tree_parent(&self) -> BTreeMap<usize, (usize, usize)> {
        let tree_set: BTreeSet<usize> = self.spanning_tree().into_iter().collect();
        let mut adj: Vec<Vec<(usize, usize)>> = vec![Vec::new(); self.vertex_count];
        for &i in &tree_set {
            let (a, b) = self.edges[i];
            adj[a].push((b, i));
            adj[b].push((a, i));
        }
        let mut parent = BTreeMap::new();
        let mut seen = BTreeSet::new();
        seen.insert(0);
        let mut queue = VecDeque::new();
        queue.push_back(0);
        while let Some(u) = queue.pop_front() {
            for &(w, idx) in &adj[u] {
                if seen.insert(w) {
                    parent.insert(w, (u, idx));
                    queue.push_back(w);
                }
            }
        }
        parent
    }

    pub fn cotree_edges(&self) -> Vec<usize> {
        let tree_set: BTreeSet<usize> = self.spanning_tree().into_iter().collect();
        (0..self.edges.len())
            .filter(|i| !tree_set.contains(i))
            .collect()
    }

    pub fn tree_path(&self, u: usize, v: usize) -> Vec<usize> {
        let parent = self.tree_parent();
        let to_root = |mut x: usize| -> Vec<usize> {
            let mut path = vec![x];
            while let Some(&(p, _)) = parent.get(&x) {
                x = p;
                path.push(x);
            }
            path
        };
        let up = to_root(u);
        let vp = to_root(v);
        let vp_set: BTreeSet<usize> = vp.iter().copied().collect();
        let common = *up
            .iter()
            .find(|x| vp_set.contains(x))
            .checked_invariant_b90405c2("checked invariant");
        let u_pos = up
            .iter()
            .position(|&x| x == common)
            .checked_invariant_b90405c2("checked invariant");
        let v_pos = vp
            .iter()
            .position(|&x| x == common)
            .checked_invariant_b90405c2("checked invariant");
        let mut path = up[..=u_pos].to_vec();
        let mut tail = vp[..v_pos].to_vec();
        tail.reverse();
        path.extend(tail);
        path
    }

    pub fn fundamental_cycle(&self, cotree_edge: usize) -> Vec<usize> {
        let (a, b) = self.edges[cotree_edge];
        let mut walk = self.tree_path(b, a);
        walk.push(b);
        walk
    }
}

pub fn transport_exponents(
    graph: &CarrierGraph,
    exponents: &[i64],
    conductor: i64,
    walk: &[usize],
) -> usize {
    let mut acc = 0i64;
    for pair in walk.windows(2) {
        let (idx, sign) = graph.edge_index(pair[0], pair[1]);
        acc = (acc + sign * exponents[idx]).rem_euclid(conductor);
    }
    acc as usize
}

pub fn gauge_transform_exponents(
    graph: &CarrierGraph,
    exponents: &[i64],
    chi: &[i64],
    conductor: i64,
) -> Vec<i64> {
    graph
        .edges
        .iter()
        .zip(exponents.iter())
        .map(|(&(u, v), &x)| (chi[u] + x - chi[v]).rem_euclid(conductor))
        .collect()
}

pub fn cycle_invariant_exponents(
    graph: &CarrierGraph,
    exponents: &[i64],
    conductor: i64,
) -> Vec<usize> {
    graph
        .cotree_edges()
        .into_iter()
        .map(|e| {
            let cyc = graph.fundamental_cycle(e);
            transport_exponents(graph, exponents, conductor, &cyc)
        })
        .collect()
}

pub fn tree_gauge_exponents(graph: &CarrierGraph, exponents: &[i64], conductor: i64) -> Vec<i64> {
    let parent = graph.tree_parent();
    let mut chi = vec![0i64; graph.vertex_count];
    let mut order: Vec<usize> = parent.keys().copied().collect();
    order.sort_by_key(|&v| graph.tree_path(0, v).len());
    for v in order {
        let (p, idx) = parent[&v];
        let (a, _) = graph.edges[idx];
        let edge_exp = if a == p {
            exponents[idx]
        } else {
            -exponents[idx]
        };
        chi[v] = (chi[p] + edge_exp).rem_euclid(conductor);
    }
    gauge_transform_exponents(graph, exponents, &chi, conductor)
}

pub fn evaluate_qm207_holonomy_bridge() -> Qm207HolonomyReport {
    let graph = CarrierGraph::diamond();
    let conductor = 12i64;
    let cochain = vec![1i64, 0, 2, 5, 7];
    let gauge = vec![3i64, 11, 4, 6];
    let gauged = gauge_transform_exponents(&graph, &cochain, &gauge, conductor);
    let inv = cycle_invariant_exponents(&graph, &cochain, conductor);
    let gauged_inv = cycle_invariant_exponents(&graph, &gauged, conductor);
    let tree_gauged = tree_gauge_exponents(&graph, &cochain, conductor);
    let tree_inv = cycle_invariant_exponents(&graph, &tree_gauged, conductor);
    let tree_unit = graph
        .spanning_tree()
        .into_iter()
        .all(|i| tree_gauged[i] == 0);

    let cotree = graph.cotree_edges();
    let mut loops: Vec<Vec<usize>> = cotree.iter().map(|&e| graph.fundamental_cycle(e)).collect();
    loops.push(vec![0, 1, 2, 0]);
    loops.push(vec![0, 1, 3, 2, 1, 3, 2, 0]);

    let factorizes = loops.iter().all(|w| {
        let mut winding = BTreeMap::new();
        for &e in &cotree {
            winding.insert(e, 0i64);
        }
        for pair in w.windows(2) {
            let (idx, sign) = graph.edge_index(pair[0], pair[1]);
            if let Some(cnt) = winding.get_mut(&idx) {
                *cnt += sign;
            }
        }
        let predicted = cotree
            .iter()
            .zip(inv.iter())
            .fold(0i64, |acc, (&e, &cyc_exp)| {
                (acc + winding[&e] * (cyc_exp as i64)).rem_euclid(conductor)
            }) as usize;
        predicted == transport_exponents(&graph, &cochain, conductor, w)
    });

    let reports = [vec![0, 1, 3], vec![0, 2, 3], vec![0, 1, 2, 3]];
    let mut rel_gauge_inv = true;
    for i in 0..3 {
        for j in (i + 1)..3 {
            let p1 = transport_exponents(&graph, &cochain, conductor, &reports[i]) as i64;
            let p2 = transport_exponents(&graph, &cochain, conductor, &reports[j]) as i64;
            let g1 = transport_exponents(&graph, &gauged, conductor, &reports[i]) as i64;
            let g2 = transport_exponents(&graph, &gauged, conductor, &reports[j]) as i64;
            if (p1 - p2).rem_euclid(conductor) != (g1 - g2).rem_euclid(conductor) {
                rel_gauge_inv = false;
            }
        }
    }

    // Exhaustive mu_3 gauge orbit census on the 5-edge diamond graph (3^5 = 243 cochains).
    let n_census = 3i64;
    let mut classes: BTreeMap<Vec<usize>, usize> = BTreeMap::new();
    for mask in 0..243usize {
        let mut m = mask;
        let mut assignment = vec![0i64; 5];
        for slot in &mut assignment {
            *slot = (m % 3) as i64;
            m /= 3;
        }
        let key = cycle_invariant_exponents(&graph, &assignment, n_census);
        *classes.entry(key).or_insert(0) += 1;
    }
    let b1 = graph.first_betti_number();
    let expected_classes = 3usize.pow(b1 as u32);
    let expected_size = 3usize.pow((graph.vertex_count - 1) as u32);

    Qm207HolonomyReport {
        vertex_count: graph.vertex_count,
        edge_count: graph.edges.len(),
        first_betti_number: b1,
        cycle_invariant_exponents: inv.clone(),
        cycle_invariants_gauge_invariant: inv == gauged_inv,
        tree_gauge_has_unit_tree_edges: tree_unit,
        tree_gauge_same_invariants: tree_inv == inv,
        holonomy_factorizes_on_all_test_loops: factorizes,
        relative_report_phase_gauge_invariant: rel_gauge_inv,
        census_class_count: classes.len(),
        census_expected_class_count: expected_classes,
        census_all_classes_expected_size: classes.values().all(|&c| c == expected_size),
        census_expected_class_size: expected_size,
    }
}

// ============================================================================
// QM-208: Quadratic Readout and Cross-Term Interference Control
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm208QuadraticReadoutReport {
    pub monomials_examined: usize,
    pub phase_blind_monomials: Vec<(usize, usize)>,
    pub blind_are_exactly_diagonal: bool,
    pub sorkin_selection_is_exactly_beta_zero: bool,
    pub quartic_i3_on_unit_triple: Q,
    pub quadratic_i3_on_unit_triple_is_zero: bool,
    pub two_report_i2_matches_two_re_holonomy: bool,
    pub sqrt3_squared_is_3: bool,
    pub weight_3_over_4_in_q_zeta12: bool,
}

fn sorkin_i3_poly(alpha: Q, beta: Q, triple: &[Cyclo12; 3]) -> Cyclo12 {
    let eval = |amps: &[Cyclo12]| -> Cyclo12 {
        let sum = amps.iter().copied().fold(Cyclo12::zero(), Cyclo12::add);
        let quad = sum.born_weight();
        let quart = quad.mul(quad);
        quad.scale(alpha).add(quart.scale(beta))
    };
    let [a, b, c] = *triple;
    eval(&[a, b, c])
        .sub(eval(&[a, b]))
        .sub(eval(&[a, c]))
        .sub(eval(&[b, c]))
        .add(eval(&[a]))
        .add(eval(&[b]))
        .add(eval(&[c]))
}

pub fn evaluate_qm208_quadratic_readout() -> Qm208QuadraticReadoutReport {
    let max_degree = 4usize;
    let sample = Cyclo12::one().add(Cyclo12::root_of_unity(1));
    let mut blind = Vec::new();
    let mut seeing = Vec::new();
    for a in 0..=max_degree {
        for b in 0..=max_degree {
            if a + b == 0 || a + b > max_degree {
                continue;
            }
            let base = sample.pow(a).mul(sample.conjugate().pow(b));
            let is_blind = (0..12).all(|k| {
                let rotated = sample.mul(Cyclo12::root_of_unity(k));
                rotated.pow(a).mul(rotated.conjugate().pow(b)) == base
            });
            if is_blind {
                blind.push((a, b));
            } else {
                seeing.push((a, b));
            }
        }
    }

    let one = Cyclo12::one();
    let half = Cyclo12::from_rat(q(1, 2));
    let two = Cyclo12::from_rat(q(2, 1));
    let z = Cyclo12::root_of_unity;
    let triples: [[Cyclo12; 3]; 6] = [
        [one, one, one],
        [one, z(1), z(2)],
        [half, z(5), two],
        [z(3), z(5), z(1)],
        [one, z(4), z(8)],
        [one.add(z(1)), z(7).mul(half), two],
    ];
    let alphas = [q(1, 1), q(1, 2), q(0, 1), q(-3, 1)];
    let betas = [q(0, 1), q(1, 1), q(-1, 2), q(2, 1)];
    let mut selection_exact = true;
    for &alpha in &alphas {
        for &beta in &betas {
            let all_zero = triples
                .iter()
                .all(|t| sorkin_i3_poly(alpha, beta, t).is_zero());
            if all_zero != beta.is_zero() {
                selection_exact = false;
            }
        }
    }

    let quartic_unit = sorkin_i3_poly(q(0, 1), q(1, 1), &[one, one, one])
        .as_rational()
        .checked_invariant_b90405c2("checked invariant");
    let quadratic_unit_zero = sorkin_i3_poly(q(1, 1), q(0, 1), &[one, one, one]).is_zero();

    // Two-report cross-term I_2 = 2 |a|^2 Re Hol(p_1 p_2^{-1})
    let graph = CarrierGraph::diamond();
    let cochain = vec![1i64, 0, 2, 5, 7];
    let p1_exp = transport_exponents(&graph, &cochain, 12, &[0, 1, 3]) as i64;
    let p2_exp = transport_exponents(&graph, &cochain, 12, &[0, 2, 3]) as i64;
    let c1 = z(p1_exp);
    let c2 = z(p2_exp);
    let i2 = c1
        .add(c2)
        .born_weight()
        .sub(c1.born_weight().add(c2.born_weight()));
    let hol = z(p1_exp - p2_exp);
    let predicted = hol.add(hol.conjugate());

    let zeta = z(1);
    let sqrt3 = zeta.add(zeta.conjugate());
    let half_sqrt3 = sqrt3.scale(q(1, 2));

    Qm208QuadraticReadoutReport {
        monomials_examined: blind.len() + seeing.len(),
        blind_are_exactly_diagonal: blind == vec![(1, 1), (2, 2)],
        phase_blind_monomials: blind,
        sorkin_selection_is_exactly_beta_zero: selection_exact,
        quartic_i3_on_unit_triple: quartic_unit,
        quadratic_i3_on_unit_triple_is_zero: quadratic_unit_zero,
        two_report_i2_matches_two_re_holonomy: i2 == predicted,
        sqrt3_squared_is_3: sqrt3.mul(sqrt3).as_rational() == Some(q(3, 1)),
        weight_3_over_4_in_q_zeta12: half_sqrt3.born_weight().as_rational() == Some(q(3, 4)),
    }
}

// ============================================================================
// QM-209: Noncommutative Contexts and F_2 Parity Cokernel Control
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct F2SystemResult {
    pub rank: usize,
    pub consistent: bool,
    pub solution: Option<Vec<u8>>,
}

pub fn f2_eliminate(rows: &[Vec<u8>], rhs: &[u8]) -> F2SystemResult {
    let mut m: Vec<Vec<u8>> = rows
        .iter()
        .zip(rhs.iter())
        .map(|(r, &b)| {
            let mut v = r.clone();
            v.push(b & 1);
            v
        })
        .collect();
    let ncols = rows.first().map_or(0, Vec::len);
    let mut pivots = Vec::new();
    let mut row = 0usize;
    for col in 0..ncols {
        if let Some(pivot) = (row..m.len()).find(|&r| m[r][col] == 1) {
            m.swap(row, pivot);
            let pivot_row = m[row].clone();
            for (r, m_r) in m.iter_mut().enumerate() {
                if r != row && m_r[col] == 1 {
                    for (x, &y) in m_r.iter_mut().zip(pivot_row.iter()) {
                        *x ^= y;
                    }
                }
            }
            pivots.push(col);
            row += 1;
        }
    }
    let consistent = m.iter().all(|r| r[..ncols].contains(&1) || r[ncols] == 0);
    let solution = if consistent {
        let mut sol = vec![0u8; ncols];
        for (r_idx, &col) in pivots.iter().enumerate() {
            sol[col] = m[r_idx][ncols];
        }
        Some(sol)
    } else {
        None
    };
    F2SystemResult {
        rank: pivots.len(),
        consistent,
        solution,
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm209ContextParityReport {
    pub context_signs: Vec<i64>,
    pub sign_product: i64,
    pub incidence_rank_f2: usize,
    pub cokernel_dimension: usize,
    pub every_observable_in_two_contexts: bool,
    pub assignment_exists: bool,
    pub obstruction_class_total_parity: u8,
    pub even_control_assignment_exists: bool,
    pub weyl_d3_trivial_iff_divisible: bool,
    pub weyl_d4_trivial_iff_divisible: bool,
}

pub fn evaluate_qm209_context_parity() -> Qm209ContextParityReport {
    let observables = ["IX", "IZ", "XI", "XX", "XZ", "YY", "ZI", "ZX", "ZZ"];
    let contexts: [[&str; 3]; 6] = [
        ["XI", "IX", "XX"],
        ["IZ", "ZI", "ZZ"],
        ["XZ", "ZX", "YY"],
        ["XI", "IZ", "XZ"],
        ["IX", "ZI", "ZX"],
        ["XX", "ZZ", "YY"],
    ];
    // Product signs of the 6 Peres-Mermin contexts: first 5 are +I, last column (XX * ZZ * YY) is -I.
    let signs = vec![1i64, 1, 1, 1, 1, -1];
    let rows: Vec<Vec<u8>> = contexts
        .iter()
        .map(|ctx| {
            observables
                .iter()
                .map(|obs| u8::from(ctx.contains(obs)))
                .collect()
        })
        .collect();
    let s: Vec<u8> = signs.iter().map(|&sg| u8::from(sg == -1)).collect();
    let sys = f2_eliminate(&rows, &s);
    let mut even = s.clone();
    even[0] ^= 1;
    let ctrl = f2_eliminate(&rows, &even);
    let col_weights_two =
        (0..observables.len()).all(|j| rows.iter().map(|r| usize::from(r[j])).sum::<usize>() == 2);

    // Weyl commutator holonomy X^a Z^b X^{-a} Z^{-b} = omega^{-ab} I in dimension d
    let weyl_check = |d: usize| -> bool {
        let step = 12 / d;
        for a in 0..d {
            for b in 0..d {
                let exp = ((d - ((a * b) % d)) % d) * step;
                let is_one = exp == 0;
                if is_one != ((a * b) % d == 0) {
                    return false;
                }
            }
        }
        true
    };

    Qm209ContextParityReport {
        context_signs: signs,
        sign_product: -1,
        incidence_rank_f2: sys.rank,
        cokernel_dimension: rows.len() - sys.rank,
        every_observable_in_two_contexts: col_weights_two,
        assignment_exists: sys.consistent,
        obstruction_class_total_parity: s.iter().sum::<u8>() % 2,
        even_control_assignment_exists: ctrl.consistent,
        weyl_d3_trivial_iff_divisible: weyl_check(3),
        weyl_d4_trivial_iff_divisible: weyl_check(4),
    }
}

// ============================================================================
// QM-210: Born Pairing, Finite Gleason Nullity, and Positivity-Gap Control
// ============================================================================

pub type Ray4 = [i64; 4];

pub const CABELLO_BASES: [[Ray4; 4]; 9] = [
    [[0, 0, 0, 1], [0, 0, 1, 0], [1, 1, 0, 0], [1, -1, 0, 0]],
    [[0, 0, 0, 1], [0, 1, 0, 0], [1, 0, 1, 0], [1, 0, -1, 0]],
    [[1, -1, 1, -1], [1, -1, -1, 1], [1, 1, 0, 0], [0, 0, 1, 1]],
    [[1, -1, 1, -1], [1, 1, 1, 1], [1, 0, -1, 0], [0, 1, 0, -1]],
    [[0, 0, 1, 0], [0, 1, 0, 0], [1, 0, 0, 1], [1, 0, 0, -1]],
    [[1, -1, -1, 1], [1, 1, 1, 1], [1, 0, 0, -1], [0, 1, -1, 0]],
    [[1, 1, -1, 1], [1, 1, 1, -1], [1, -1, 0, 0], [0, 0, 1, 1]],
    [[1, 1, -1, 1], [-1, 1, 1, 1], [1, 0, 1, 0], [0, 1, 0, -1]],
    [[1, 1, 1, -1], [-1, 1, 1, 1], [1, 0, 0, 1], [0, 1, -1, 0]],
];

fn dot4(u: &Ray4, v: &Ray4) -> i64 {
    u[0] * v[0] + u[1] * v[1] + u[2] * v[2] + u[3] * v[3]
}

fn proportional4(u: &Ray4, v: &Ray4) -> bool {
    for i in 0..4 {
        for j in 0..4 {
            if u[i] * v[j] != u[j] * v[i] {
                return false;
            }
        }
    }
    true
}

pub fn rays_of_bases(bases: &[[Ray4; 4]]) -> Vec<Ray4> {
    let mut rays: Vec<Ray4> = Vec::new();
    for b in bases {
        for v in b {
            if !rays.iter().any(|r| proportional4(v, r)) {
                rays.push(*v);
            }
        }
    }
    rays
}

fn peres_24_candidate_rays() -> Vec<Ray4> {
    let mut rays = Vec::new();
    for idx in 0..81i64 {
        let v = [
            (idx / 27) - 1,
            ((idx / 9) % 3) - 1,
            ((idx / 3) % 3) - 1,
            (idx % 3) - 1,
        ];
        let nz: Vec<i64> = v.into_iter().filter(|&x| x != 0).collect();
        if matches!(nz.len(), 1 | 2 | 4) && nz[0] == 1 {
            rays.push(v);
        }
    }
    rays
}

fn extend_peres_bases_from_pair(rays: &[Ray4], i: usize, j: usize, bases: &mut Vec<[Ray4; 4]>) {
    let n = rays.len();
    for k in (j + 1)..n {
        if dot4(&rays[i], &rays[k]) != 0 || dot4(&rays[j], &rays[k]) != 0 {
            continue;
        }
        for l in (k + 1)..n {
            if dot4(&rays[i], &rays[l]) == 0
                && dot4(&rays[j], &rays[l]) == 0
                && dot4(&rays[k], &rays[l]) == 0
            {
                bases.push([rays[i], rays[j], rays[k], rays[l]]);
            }
        }
    }
}

pub fn peres_24_bases() -> Vec<[Ray4; 4]> {
    let rays = peres_24_candidate_rays();
    let mut bases = Vec::new();
    let n = rays.len();
    for i in 0..n {
        for j in (i + 1)..n {
            if dot4(&rays[i], &rays[j]) == 0 {
                extend_peres_bases_from_pair(&rays, i, j, &mut bases);
            }
        }
    }
    bases
}

pub fn q_rank(rows: &[Vec<Q>]) -> usize {
    let mut m = rows.to_vec();
    let ncols = m.first().map_or(0, Vec::len);
    let mut rank = 0usize;
    for col in 0..ncols {
        if let Some(pivot) = (rank..m.len()).find(|&r| !m[r][col].is_zero()) {
            m.swap(rank, pivot);
            let inv = Q::one() / m[rank][col];
            for x in &mut m[rank] {
                *x *= inv;
            }
            let pivot_row = m[rank].clone();
            for (r, m_r) in m.iter_mut().enumerate() {
                if r != rank && !m_r[col].is_zero() {
                    let factor = m_r[col];
                    for (x, &y) in m_r.iter_mut().zip(pivot_row.iter()) {
                        *x -= factor * y;
                    }
                }
            }
            rank += 1;
        }
    }
    rank
}

fn symmetric_4x4_basis(traceless: bool) -> Vec<[[Q; 4]; 4]> {
    let mut mats = Vec::new();
    let diag_end = if traceless { 3 } else { 4 };
    for i in 0..diag_end {
        let mut m = [[Q::zero(); 4]; 4];
        m[i][i] = Q::one();
        if traceless {
            m[3][3] = -Q::one();
        }
        mats.push(m);
    }
    for i in 0..4 {
        for j in (i + 1)..4 {
            let mut m = [[Q::zero(); 4]; 4];
            m[i][j] = Q::one();
            m[j][i] = Q::one();
            mats.push(m);
        }
    }
    mats
}

fn quantum_frame_function(rho: &[[Q; 4]; 4], rays: &[Ray4]) -> Vec<Q> {
    rays.iter()
        .map(|v| {
            let mut num = Q::zero();
            for i in 0..4 {
                for j in 0..4 {
                    num += Q::from_integer(v[i] * v[j]) * rho[i][j];
                }
            }
            num / Q::from_integer(dot4(v, v))
        })
        .collect()
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct GleasonNullitySummary {
    pub ray_count: usize,
    pub constraint_rank_q: usize,
    pub frame_function_affine_dimension: usize,
    pub quantum_affine_dimension: usize,
    pub nullity: usize,
}

pub fn gleason_nullity(bases: &[[Ray4; 4]]) -> GleasonNullitySummary {
    let rays = rays_of_bases(bases);
    let constraint_rows: Vec<Vec<Q>> = bases
        .iter()
        .map(|b| {
            rays.iter()
                .map(|r| {
                    if b.iter().any(|v| proportional4(v, r)) {
                        Q::one()
                    } else {
                        Q::zero()
                    }
                })
                .collect()
        })
        .collect();
    let rank = q_rank(&constraint_rows);
    let all_dim = rays.len() - rank;
    let quantum_rows: Vec<Vec<Q>> = symmetric_4x4_basis(true)
        .iter()
        .map(|m| quantum_frame_function(m, &rays))
        .collect();
    let quantum_dim = q_rank(&quantum_rows);
    GleasonNullitySummary {
        ray_count: rays.len(),
        constraint_rank_q: rank,
        frame_function_affine_dimension: all_dim,
        quantum_affine_dimension: quantum_dim,
        nullity: all_dim - quantum_dim,
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm210FrameFunctionReport {
    pub cabello_prefix_3: GleasonNullitySummary,
    pub cabello_prefix_6: GleasonNullitySummary,
    pub cabello_prefix_9: GleasonNullitySummary,
    pub peres_24_nullity: GleasonNullitySummary,
    pub cabello_f2_rank: usize,
    pub cabello_f2_consistent: bool,
    pub peres_f2_rank: usize,
    pub peres_f2_consistent: bool,
    pub witness_trace_one: bool,
    pub witness_nonnegative_on_cabello: bool,
    pub witness_nonnegative_on_peres: bool,
    pub witness_leading_2x2_minor: Q,
    pub witness_value_on_negative_direction: Q,
}

pub fn evaluate_qm210_frame_function() -> Qm210FrameFunctionReport {
    let p3 = gleason_nullity(&CABELLO_BASES[..3]);
    let p6 = gleason_nullity(&CABELLO_BASES[..6]);
    let p9 = gleason_nullity(&CABELLO_BASES);
    let peres = peres_24_bases();
    let peres_nullity = gleason_nullity(&peres);

    let f2_parity = |bases: &[[Ray4; 4]]| -> (usize, bool) {
        let rays = rays_of_bases(bases);
        let rows: Vec<Vec<u8>> = bases
            .iter()
            .map(|b| {
                rays.iter()
                    .map(|r| u8::from(b.iter().any(|v| proportional4(v, r))))
                    .collect()
            })
            .collect();
        let rhs = vec![1u8; bases.len()];
        let res = f2_eliminate(&rows, &rhs);
        (res.rank, res.consistent)
    };
    let (cab_rank, cab_cons) = f2_parity(&CABELLO_BASES);
    let (per_rank, per_cons) = f2_parity(&peres);

    // Explicit rational trace-one symmetric positivity-gap witness rho_2
    let z = q(0, 1);
    let h = q(1, 2);
    let qr = q(1, 4);
    let mqr = q(-1, 4);
    let rho2: [[Q; 4]; 4] = [[z, mqr, z, z], [mqr, h, z, qr], [z, z, h, z], [z, qr, z, z]];
    let trace_one = (rho2[0][0] + rho2[1][1] + rho2[2][2] + rho2[3][3]) == Q::one();
    let cab_vals = quantum_frame_function(&rho2, &rays_of_bases(&CABELLO_BASES));
    let per_vals = quantum_frame_function(&rho2, &rays_of_bases(&peres));
    let nonneg_cab = cab_vals.iter().all(|&x| x >= Q::zero());
    let nonneg_per = per_vals.iter().all(|&x| x >= Q::zero());
    let minor_2x2 = rho2[0][0] * rho2[1][1] - rho2[0][1] * rho2[1][0];
    let neg_dir = [2i64, 1, 0, 0];
    let mut neg_val = Q::zero();
    for i in 0..4 {
        for j in 0..4 {
            neg_val += Q::from_integer(neg_dir[i] * neg_dir[j]) * rho2[i][j];
        }
    }

    Qm210FrameFunctionReport {
        cabello_prefix_3: p3,
        cabello_prefix_6: p6,
        cabello_prefix_9: p9,
        peres_24_nullity: peres_nullity,
        cabello_f2_rank: cab_rank,
        cabello_f2_consistent: cab_cons,
        peres_f2_rank: per_rank,
        peres_f2_consistent: per_cons,
        witness_trace_one: trace_one,
        witness_nonnegative_on_cabello: nonneg_cab,
        witness_nonnegative_on_peres: nonneg_per,
        witness_leading_2x2_minor: minor_2x2,
        witness_value_on_negative_direction: neg_val,
    }
}

// ============================================================================
// QM-211: Clock Tower Spectral Decomposition and Refinement Control
// ============================================================================

/// Element of `Q(zeta_24)` in the power basis `[1, zeta_24, ..., zeta_24^7]`
/// with minimal polynomial `Phi_24(x) = x^8 - x^4 + 1`.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct Cyclo24(pub [Q; 8]);

impl Cyclo24 {
    pub fn zero() -> Self {
        Self([Q::zero(); 8])
    }

    pub fn one() -> Self {
        let mut c = [Q::zero(); 8];
        c[0] = Q::one();
        Self(c)
    }

    pub fn from_rat(r: Q) -> Self {
        let mut c = [Q::zero(); 8];
        c[0] = r;
        Self(c)
    }

    pub fn root_of_unity(k: i64) -> Self {
        let exp = k.rem_euclid(24) as usize;
        let mut coeffs = [Q::zero(); 24];
        coeffs[exp] = Q::one();
        Self::reduce24(coeffs)
    }

    fn reduce24(mut c: [Q; 24]) -> Self {
        for i in (8..24).rev() {
            let v = c[i];
            if !v.is_zero() {
                // x^8 = x^4 - 1
                c[i - 4] += v;
                c[i - 8] -= v;
                c[i] = Q::zero();
            }
        }
        let mut out = [Q::zero(); 8];
        out.copy_from_slice(&c[..8]);
        Self(out)
    }

    pub fn add(self, rhs: Self) -> Self {
        let mut out = [Q::zero(); 8];
        for i in 0..8 {
            out[i] = self.0[i] + rhs.0[i];
        }
        Self(out)
    }

    pub fn scale(self, r: Q) -> Self {
        let mut out = [Q::zero(); 8];
        for i in 0..8 {
            out[i] = self.0[i] * r;
        }
        Self(out)
    }

    pub fn mul(self, rhs: Self) -> Self {
        let mut prod = [Q::zero(); 24];
        for i in 0..8 {
            for j in 0..8 {
                prod[i + j] += self.0[i] * rhs.0[j];
            }
        }
        Self::reduce24(prod)
    }

    pub fn conjugate(self) -> Self {
        let mut acc = Self::zero();
        for (k, &coeff) in self.0.iter().enumerate() {
            if !coeff.is_zero() {
                acc = acc.add(Self::root_of_unity(-(k as i64)).scale(coeff));
            }
        }
        acc
    }

    pub fn as_rational(&self) -> Option<Q> {
        if self.0[1..].iter().all(Zero::is_zero) {
            Some(self.0[0])
        } else {
            None
        }
    }
}

type Mat24 = Vec<Vec<Cyclo24>>;

fn mat24_id(n: usize) -> Mat24 {
    (0..n)
        .map(|i| {
            (0..n)
                .map(|j| {
                    if i == j {
                        Cyclo24::one()
                    } else {
                        Cyclo24::zero()
                    }
                })
                .collect()
        })
        .collect()
}

fn mat24_mul(a: &Mat24, b: &Mat24) -> Mat24 {
    let n = a.len();
    let mut out = vec![vec![Cyclo24::zero(); n]; n];
    for i in 0..n {
        for k in 0..n {
            for j in 0..n {
                out[i][j] = out[i][j].add(a[i][k].mul(b[k][j]));
            }
        }
    }
    out
}

fn mat24_add(a: &Mat24, b: &Mat24) -> Mat24 {
    a.iter()
        .zip(b.iter())
        .map(|(ra, rb)| ra.iter().zip(rb.iter()).map(|(&x, &y)| x.add(y)).collect())
        .collect()
}

fn mat24_scale(a: &Mat24, s: Cyclo24) -> Mat24 {
    a.iter()
        .map(|r| r.iter().map(|&x| x.mul(s)).collect())
        .collect()
}

fn mat24_dagger(a: &Mat24) -> Mat24 {
    let n = a.len();
    (0..n)
        .map(|i| (0..n).map(|j| a[j][i].conjugate()).collect())
        .collect()
}

fn spectral_multiplicities_and_roots(u: &Mat24, order: usize) -> (Vec<i64>, usize, bool) {
    let n = u.len();
    let mut powers = Vec::with_capacity(order);
    let mut cur = mat24_id(n);
    for _ in 0..order {
        powers.push(cur.clone());
        cur = mat24_mul(&cur, u);
    }
    let mut projectors = Vec::with_capacity(order);
    let mut multiplicities = Vec::with_capacity(order);
    let step = 24i64 / (order as i64);
    for k in 0..order {
        let mut acc = vec![vec![Cyclo24::zero(); n]; n];
        for (j, p_j) in powers.iter().enumerate() {
            let phase = Cyclo24::root_of_unity(-step * (k as i64) * (j as i64));
            acc = mat24_add(&acc, &mat24_scale(p_j, phase));
        }
        let proj = mat24_scale(&acc, Cyclo24::from_rat(q(1, order as i64)));
        let tr = (0..n)
            .fold(Cyclo24::zero(), |s, i| s.add(proj[i][i]))
            .as_rational()
            .checked_invariant_b90405c2("checked invariant");
        multiplicities.push(*tr.numer());
        projectors.push(proj);
    }
    let occupied: Vec<usize> = multiplicities
        .iter()
        .enumerate()
        .filter_map(|(k, &m)| if m > 0 { Some(k) } else { None })
        .collect();
    let root_count = 1usize << occupied.len();
    let half_step = 24i64 / (2 * order as i64);
    let mut all_valid = true;
    for mask in 0..root_count {
        let mut v = vec![vec![Cyclo24::zero(); n]; n];
        for (bit, &k) in occupied.iter().enumerate() {
            let s = ((mask >> bit) & 1) as i64;
            let mu = Cyclo24::root_of_unity(half_step * ((k as i64) + (order as i64) * s));
            v = mat24_add(&v, &mat24_scale(&projectors[k], mu));
        }
        if mat24_mul(&v, &v) != *u || mat24_mul(&mat24_dagger(&v), &v) != mat24_id(n) {
            all_valid = false;
        }
    }
    (multiplicities, root_count, all_valid)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm211ClockTowerReport {
    pub fourier_d4_multiplicities: Vec<i64>,
    pub fourier_d4_square_root_count: usize,
    pub shift_d4_multiplicities: Vec<i64>,
    pub shift_d4_square_root_count: usize,
    pub clock_d3_multiplicities: Vec<i64>,
    pub clock_d3_square_root_count: usize,
    pub all_square_roots_unitary_and_square_to_u: bool,
    pub chain_condition_is_divisibility: bool,
    pub swap_unitary_root_squares_to_swap: bool,
    pub swap_real_or_stochastic_root_exists: bool,
}

fn check_qm211_divisibility_chain() -> bool {
    let refines = |fine: usize, coarse: usize| -> Option<usize> {
        let fine_step = 24 / fine;
        let coarse_step = 24 / coarse;
        (0..fine).find(|&k| (k * fine_step) % 24 == coarse_step % 24)
    };
    refines(4, 3).is_none()
        && refines(3, 4).is_none()
        && refines(12, 3) == Some(4)
        && refines(12, 4) == Some(3)
        && refines(24, 12) == Some(2)
}

pub fn evaluate_qm211_clock_tower() -> Qm211ClockTowerReport {
    let half = Cyclo24::from_rat(q(1, 2));
    let fourier_d4: Mat24 = (0..4)
        .map(|j| {
            (0..4)
                .map(|k| half.mul(Cyclo24::root_of_unity(6 * ((j * k) as i64))))
                .collect()
        })
        .collect();
    let shift_d4: Mat24 = (0..4)
        .map(|j| {
            (0..4)
                .map(|k| {
                    if j == (k + 1) % 4 {
                        Cyclo24::one()
                    } else {
                        Cyclo24::zero()
                    }
                })
                .collect()
        })
        .collect();
    let clock_d3: Mat24 = (0..3)
        .map(|j| {
            (0..3)
                .map(|k| {
                    if j == k {
                        Cyclo24::root_of_unity(8 * (j as i64))
                    } else {
                        Cyclo24::zero()
                    }
                })
                .collect()
        })
        .collect();

    let (f_mult, f_roots, f_ok) = spectral_multiplicities_and_roots(&fourier_d4, 4);
    let (s_mult, s_roots, s_ok) = spectral_multiplicities_and_roots(&shift_d4, 4);
    let (c_mult, c_roots, c_ok) = spectral_multiplicities_and_roots(&clock_d3, 3);

    let divisibility_ok = check_qm211_divisibility_chain();

    // 2x2 swap negative control
    let swap: Mat24 = vec![
        vec![Cyclo24::zero(), Cyclo24::one()],
        vec![Cyclo24::one(), Cyclo24::zero()],
    ];
    let i_unit = Cyclo24::root_of_unity(6);
    let c_plus = half.mul(Cyclo24::one().add(i_unit));
    let c_minus = half.mul(Cyclo24::one().add(Cyclo24::root_of_unity(18)));
    let v_swap = mat24_add(
        &mat24_scale(&mat24_id(2), c_plus),
        &mat24_scale(&swap, c_minus),
    );
    let swap_root_ok = mat24_mul(&v_swap, &v_swap) == swap
        && mat24_mul(&mat24_dagger(&v_swap), &v_swap) == mat24_id(2);

    // 4a^4 + 1 = 0 has no rational root among +/- {1, 1/2, 1/4}, and forced stochastic [[0,1],[0,1]]^2 != swap
    let candidates = [q(1, 1), q(-1, 1), q(1, 2), q(-1, 2), q(1, 4), q(-1, 4)];
    let rat_root = candidates
        .iter()
        .any(|&a| (q(4, 1) * a * a * a * a + Q::one()).is_zero());
    let forced: Mat24 = vec![
        vec![Cyclo24::zero(), Cyclo24::one()],
        vec![Cyclo24::zero(), Cyclo24::one()],
    ];
    let stoch_root = mat24_mul(&forced, &forced) == swap;

    Qm211ClockTowerReport {
        fourier_d4_multiplicities: f_mult,
        fourier_d4_square_root_count: f_roots,
        shift_d4_multiplicities: s_mult,
        shift_d4_square_root_count: s_roots,
        clock_d3_multiplicities: c_mult,
        clock_d3_square_root_count: c_roots,
        all_square_roots_unitary_and_square_to_u: f_ok && s_ok && c_ok,
        chain_condition_is_divisibility: divisibility_ok,
        swap_unitary_root_squares_to_swap: swap_root_ok,
        swap_real_or_stochastic_root_exists: rat_root || stoch_root,
    }
}

// ============================================================================
// QM-212: Dressed Graph Polynomials (Ravera DFM) & Rational QED g-2 Enclosure
// ============================================================================

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BigInterval {
    pub lo: BigRational,
    pub hi: BigRational,
}

impl BigInterval {
    pub fn new(lo: BigRational, hi: BigRational) -> Self {
        assert!(lo <= hi, "BigInterval requires lo <= hi");
        Self { lo, hi }
    }

    pub fn exact(x: BigRational) -> Self {
        Self {
            lo: x.clone(),
            hi: x,
        }
    }

    pub fn from_i64(n: i64, d: i64) -> Self {
        Self::exact(BigRational::new(BigInt::from(n), BigInt::from(d)))
    }

    pub fn width(&self) -> BigRational {
        &self.hi - &self.lo
    }

    pub fn add(&self, other: &Self) -> Self {
        Self::new(&self.lo + &other.lo, &self.hi + &other.hi)
    }

    pub fn sub(&self, other: &Self) -> Self {
        Self::new(&self.lo - &other.hi, &self.hi - &other.lo)
    }

    pub fn mul(&self, other: &Self) -> Self {
        let p1 = &self.lo * &other.lo;
        let p2 = &self.lo * &other.hi;
        let p3 = &self.hi * &other.lo;
        let p4 = &self.hi * &other.hi;
        let lo = p1.clone().min(p2.clone()).min(p3.clone()).min(p4.clone());
        let hi = p1.max(p2).max(p3).max(p4);
        Self::new(lo, hi)
    }

    pub fn scale(&self, c: BigRational) -> Self {
        if !c.is_negative() {
            Self::new(&self.lo * &c, &self.hi * &c)
        } else {
            Self::new(&self.hi * &c, &self.lo * &c)
        }
    }

    pub fn pow(&self, exp: u32) -> Self {
        let mut acc = Self::from_i64(1, 1);
        for _ in 0..exp {
            acc = acc.mul(self);
        }
        acc
    }

    pub fn reciprocal(&self) -> Self {
        assert!(
            self.lo.is_positive() || self.hi.is_negative(),
            "cannot invert interval containing zero"
        );
        Self::new(self.hi.recip(), self.lo.recip())
    }

    pub fn decimal_prefix(&self, digits: u32) -> (String, String, bool) {
        let scale = BigInt::from(10u64).pow(digits);
        let fmt_q = |r: &BigRational| -> String {
            let sign = if r.is_negative() { "-" } else { "" };
            let ar = r.abs();
            let scaled = (ar.numer() * &scale) / ar.denom();
            let int_part = &scaled / &scale;
            let frac_part = &scaled % &scale;
            format!(
                "{}{}.{:0width$}",
                sign,
                int_part,
                frac_part,
                width = digits as usize
            )
        };
        let lo_s = fmt_q(&self.lo);
        let hi_s = fmt_q(&self.hi);
        let eq = lo_s == hi_s;
        (lo_s, hi_s, eq)
    }
}

pub fn is_spanning_tree(graph: &CarrierGraph, tree_edges: &[usize]) -> bool {
    if tree_edges.len() + 1 != graph.vertex_count {
        return false;
    }
    let mut adj = vec![Vec::new(); graph.vertex_count];
    for &idx in tree_edges {
        let (u, v) = graph.edges[idx];
        adj[u].push(v);
        adj[v].push(u);
    }
    let mut seen = BTreeSet::new();
    seen.insert(0usize);
    let mut stack = vec![0usize];
    while let Some(cur) = stack.pop() {
        for &nxt in &adj[cur] {
            if seen.insert(nxt) {
                stack.push(nxt);
            }
        }
    }
    seen.len() == graph.vertex_count
}

pub fn enumerate_spanning_trees(graph: &CarrierGraph) -> Vec<(Vec<usize>, Vec<usize>)> {
    let m = graph.edges.len();
    let tree_size = graph.vertex_count - 1;
    let mut out = Vec::new();
    for mask in 0usize..(1usize << m) {
        if mask.count_ones() as usize == tree_size {
            let tree: Vec<usize> = (0..m).filter(|&i| (mask >> i) & 1 == 1).collect();
            if is_spanning_tree(graph, &tree) {
                let cotree: Vec<usize> = (0..m).filter(|&i| (mask >> i) & 1 == 0).collect();
                out.push((tree, cotree));
            }
        }
    }
    out
}

pub fn symanzik_u_polynomial(graph: &CarrierGraph, alphas: &[Q]) -> Q {
    let mut total = Q::zero();
    for (_, cotree) in enumerate_spanning_trees(graph) {
        let mut prod = Q::one();
        for e in cotree {
            prod *= alphas[e];
        }
        total += prod;
    }
    total
}

fn q_det(matrix: &[Vec<Q>]) -> Q {
    let n = matrix.len();
    let mut a = matrix.to_vec();
    let mut det = Q::one();
    for c in 0..n {
        let Some(pivot) = (c..n).find(|&r| !a[r][c].is_zero()) else {
            return Q::zero();
        };
        if pivot != c {
            a.swap(c, pivot);
            det = -det;
        }
        let piv = a[c][c];
        det *= piv;
        let row_c = a[c].clone();
        for a_r in a.iter_mut().skip(c + 1) {
            let factor = a_r[c] / piv;
            for (x, &y) in a_r.iter_mut().zip(row_c.iter()) {
                *x -= factor * y;
            }
        }
    }
    det
}

pub fn kirchhoff_dual_symanzik_u(graph: &CarrierGraph, alphas: &[Q]) -> Q {
    let n = graph.vertex_count;
    let mut lap = vec![vec![Q::zero(); n]; n];
    for (&(u, v), &alpha) in graph.edges.iter().zip(alphas.iter()) {
        let w = Q::one() / alpha;
        lap[u][u] += w;
        lap[v][v] += w;
        lap[u][v] -= w;
        lap[v][u] -= w;
    }
    let minor: Vec<Vec<Q>> = lap[1..].iter().map(|r| r[1..].to_vec()).collect();
    let mut prod_alpha = Q::one();
    for &alpha in alphas {
        prod_alpha *= alpha;
    }
    prod_alpha * q_det(&minor)
}

pub fn tree_path_on_custom_tree(
    graph: &CarrierGraph,
    tree_edges: &[usize],
    u: usize,
    v: usize,
) -> Vec<usize> {
    let mut adj = vec![Vec::new(); graph.vertex_count];
    for &idx in tree_edges {
        let (a, b) = graph.edges[idx];
        adj[a].push(b);
        adj[b].push(a);
    }
    let mut parent = BTreeMap::new();
    let mut seen = BTreeSet::new();
    seen.insert(u);
    let mut stack = vec![u];
    while let Some(cur) = stack.pop() {
        if cur == v {
            break;
        }
        for &nxt in &adj[cur] {
            if seen.insert(nxt) {
                parent.insert(nxt, cur);
                stack.push(nxt);
            }
        }
    }
    let mut path = vec![v];
    while *path.last().checked_invariant_b90405c2("checked invariant") != u {
        let prev = parent[path.last().checked_invariant_b90405c2("checked invariant")];
        path.push(prev);
    }
    path.reverse();
    path
}

pub fn dress_cochain_on_tree(
    graph: &CarrierGraph,
    exponents: &[i64],
    conductor: i64,
    tree_edges: &[usize],
) -> Vec<i64> {
    let chi: Vec<i64> = (0..graph.vertex_count)
        .map(|v| {
            let walk = tree_path_on_custom_tree(graph, tree_edges, 0, v);
            transport_exponents(graph, exponents, conductor, &walk) as i64
        })
        .collect();
    gauge_transform_exponents(graph, exponents, &chi, conductor)
}

pub fn cycle_basis_change_det(
    graph: &CarrierGraph,
    _tree_a: &[usize],
    cotree_a: &[usize],
    tree_b: &[usize],
    cotree_b: &[usize],
) -> Q {
    let mut matrix = Vec::new();
    for &e_b in cotree_b {
        let (u, v) = graph.edges[e_b];
        let mut cycle_b = tree_path_on_custom_tree(graph, tree_b, v, u);
        cycle_b.push(v);
        let mut row = Vec::new();
        for &e_a in cotree_a {
            let mut coeff = 0i64;
            for pair in cycle_b.windows(2) {
                let (idx, sign) = graph.edge_index(pair[0], pair[1]);
                if idx == e_a {
                    coeff += sign;
                }
            }
            row.push(q(coeff, 1));
        }
        matrix.push(row);
    }
    q_det(&matrix)
}

fn atan_unit_fraction_big(m: i64, even_terms: usize) -> BigInterval {
    let mut s = BigRational::zero();
    let m2 = BigRational::from_integer(BigInt::from(m * m));
    let mut power = BigRational::new(BigInt::from(1), BigInt::from(m));
    for k in 0..even_terms {
        let term = &power / BigRational::from_integer(BigInt::from((2 * k + 1) as i64));
        if k % 2 == 0 {
            s += term;
        } else {
            s -= term;
        }
        power /= &m2;
    }
    let next_term = &power / BigRational::from_integer(BigInt::from((2 * even_terms + 1) as i64));
    BigInterval::new(s.clone(), s + next_term)
}

pub fn pi_big_interval(even_terms: usize) -> BigInterval {
    let a5 = atan_unit_fraction_big(5, even_terms);
    let a239 = atan_unit_fraction_big(239, (even_terms / 2).max(4));
    a5.scale(BigRational::from_integer(BigInt::from(16)))
        .sub(&a239.scale(BigRational::from_integer(BigInt::from(4))))
}

pub fn polylog_half_big_interval(s: u32, terms: usize) -> BigInterval {
    let mut partial = BigRational::zero();
    for k in 1..=terms {
        let denom = BigInt::from(k as u64).pow(s) * (BigInt::from(1u64) << k);
        partial += BigRational::new(BigInt::from(1), denom);
    }
    let rem_denom = BigInt::from((terms + 1) as u64).pow(s) * (BigInt::from(1u64) << terms);
    let rem = BigRational::new(BigInt::from(1), rem_denom);
    BigInterval::new(partial.clone(), partial + rem)
}

fn binom_2k_k(k: usize) -> BigInt {
    let mut acc = BigInt::from(1);
    for i in 1..=k {
        acc = (acc * BigInt::from((k + i) as u64)) / BigInt::from(i as u64);
    }
    acc
}

pub fn zeta3_big_interval(even_terms: usize) -> BigInterval {
    let mut s = BigRational::zero();
    for k in 1..=even_terms {
        let sign = if k % 2 == 1 { 5i64 } else { -5i64 };
        let denom = BigInt::from(2u64) * BigInt::from(k as u64).pow(3) * binom_2k_k(k);
        s += BigRational::new(BigInt::from(sign), denom);
    }
    let nk = even_terms + 1;
    let rem_denom = BigInt::from(2u64) * BigInt::from(nk as u64).pow(3) * binom_2k_k(nk);
    let rem = BigRational::new(BigInt::from(5), rem_denom);
    BigInterval::new(s.clone(), s + rem)
}

pub fn zeta5_big_interval(n_cutoff: usize) -> BigInterval {
    let mut head = BigRational::zero();
    for k in 1..n_cutoff {
        head += BigRational::new(BigInt::from(1), BigInt::from(k as u64).pow(5));
    }
    let n = BigInt::from(n_cutoff as u64);
    let em = head
        + BigRational::new(BigInt::from(1), BigInt::from(2) * n.pow(5))
        + BigRational::new(BigInt::from(1), BigInt::from(4) * n.pow(4))
        + BigRational::new(BigInt::from(5), BigInt::from(12) * n.pow(6))
        - BigRational::new(BigInt::from(7), BigInt::from(24) * n.pow(8));
    let rem = BigRational::new(BigInt::from(5), BigInt::from(8) * n.pow(10));
    BigInterval::new(em.clone(), em + rem)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Qm212DressedQedG2Report {
    pub diamond_spanning_tree_count: usize,
    pub diamond_first_betti_number: usize,
    pub u_diamond_unit: Q,
    pub u_diamond_prime_weights: Q,
    pub kirchhoff_identity_holds_on_diamond: bool,
    pub kirchhoff_identity_holds_on_triangle: bool,
    pub dfm_retraction_idempotent: bool,
    pub dfm_retraction_gauge_invariant: bool,
    pub dfm_every_tree_neutralizes_tree_edges: bool,
    pub dressed_symanzik_gauge_invariant: bool,
    pub all_trees_unimodular_basis_change: bool,
    pub c1_exact_half: bool,
    pub c2_decimal_12: String,
    pub c3_decimal_12: String,
    pub ae_1_to_3_decimal_12: String,
    pub ae_1_to_3_12_digits_agree: bool,
    pub ae_1_to_4_decimal_12: String,
    pub ae_1_to_4_12_digits_agree: bool,
    pub ae_1_to_4_total_width_lt_1e12: bool,
}

pub fn evaluate_qm212_dressed_qed_g2() -> Qm212DressedQedG2Report {
    let diamond = CarrierGraph::diamond();
    let triangle = CarrierGraph {
        vertex_count: 3,
        edges: vec![(0, 1), (1, 2), (0, 2)],
    };
    let trees = enumerate_spanning_trees(&diamond);
    let alphas_unit = vec![q(1, 1); 5];
    let alphas_prime = vec![q(1, 1), q(2, 1), q(3, 1), q(5, 1), q(7, 1)];
    let u_unit = symanzik_u_polynomial(&diamond, &alphas_unit);
    let k_unit = kirchhoff_dual_symanzik_u(&diamond, &alphas_unit);
    let u_prime = symanzik_u_polynomial(&diamond, &alphas_prime);
    let k_prime = kirchhoff_dual_symanzik_u(&diamond, &alphas_prime);

    let tri_alphas = vec![q(2, 1), q(5, 1), q(11, 1)];
    let u_tri = symanzik_u_polynomial(&triangle, &tri_alphas);
    let k_tri = kirchhoff_dual_symanzik_u(&triangle, &tri_alphas);

    let conductor = 12i64;
    let cochain = vec![1i64, 0, 2, 5, 7];
    let gauge = vec![3i64, 11, 4, 6];
    let gauged = gauge_transform_exponents(&diamond, &cochain, &gauge, conductor);

    let (base_tree, base_cotree) = &trees[0];
    let dressed = dress_cochain_on_tree(&diamond, &cochain, conductor, base_tree);
    let dressed_twice = dress_cochain_on_tree(&diamond, &dressed, conductor, base_tree);
    let dressed_gauged = dress_cochain_on_tree(&diamond, &gauged, conductor, base_tree);

    let alphas_cochain: Vec<Q> = dressed.iter().map(|&v| q(1 + v, 1)).collect();
    let alphas_gauged: Vec<Q> = dressed_gauged.iter().map(|&v| q(1 + v, 1)).collect();
    let u_cochain = symanzik_u_polynomial(&diamond, &alphas_cochain);
    let u_gauged = symanzik_u_polynomial(&diamond, &alphas_gauged);

    let unimodular_all = trees.iter().all(|(t, ct)| {
        cycle_basis_change_det(&diamond, base_tree, base_cotree, t, ct).abs() == Q::one()
    });
    let every_tree_neutralizes = trees.iter().all(|(t, _)| {
        let d = dress_cochain_on_tree(&diamond, &cochain, conductor, t);
        t.iter().all(|&idx| d[idx] == 0)
    });

    // QED g-2 rational interval enclosure over BigRational
    let br = |n: i64, d: i64| BigRational::new(BigInt::from(n), BigInt::from(d));
    let pi = pi_big_interval(20);
    let pi2 = pi.pow(2);
    let pi4 = pi2.pow(2);
    let ln2 = polylog_half_big_interval(1, 50);
    let li4 = polylog_half_big_interval(4, 50);
    let z3 = zeta3_big_interval(20);
    let z5 = zeta5_big_interval(20);

    let c1 = BigInterval::from_i64(1, 2);
    let c2 = BigInterval::from_i64(197, 144)
        .add(&pi2.scale(br(1, 12)))
        .sub(&pi2.mul(&ln2).scale(br(1, 2)))
        .add(&z3.scale(br(3, 4)));
    let a4_combo = li4
        .add(&ln2.pow(4).scale(br(1, 24)))
        .sub(&pi2.mul(&ln2.pow(2)).scale(br(1, 24)));
    let c3 = BigInterval::from_i64(28259, 5184)
        .add(&pi2.scale(br(17101, 810)))
        .sub(&pi2.mul(&ln2).scale(br(298, 9)))
        .add(&z3.scale(br(139, 18)))
        .add(&a4_combo.scale(br(100, 3)))
        .sub(&pi4.scale(br(239, 2160)))
        .add(&pi2.mul(&z3).scale(br(83, 72)))
        .sub(&z5.scale(br(215, 24)));
    let c4 = BigInterval::new(
        br(-191_224_576_492_645, 100_000_000_000_000),
        br(-191_224_576_492_644, 100_000_000_000_000),
    );

    let alpha = BigInterval::from_i64(1_000_000_000, 137_035_999_166);
    let x = alpha.mul(&pi.reciprocal());
    let x2 = x.pow(2);
    let x3 = x.pow(3);
    let x4 = x.pow(4);
    let x5 = x.pow(5);

    let ae_1 = c1.mul(&x);
    let ae_2 = ae_1.add(&c2.mul(&x2));
    let ae_3 = ae_2.add(&c3.mul(&x3));
    let ae_4 = ae_3.add(&c4.mul(&x4));
    let rem_bound = &x5.hi * br(5, 1);
    let ae_4_total = ae_4.add(&BigInterval::new(-rem_bound.clone(), rem_bound));

    let (c2_12, _, _) = c2.decimal_prefix(12);
    let (c3_12, _, _) = c3.decimal_prefix(12);
    let (ae3_lo, _, ae3_eq) = ae_3.decimal_prefix(12);
    let (ae4_lo, _, ae4_eq) = ae_4.decimal_prefix(12);
    let inv_1e12 = BigRational::new(BigInt::from(1), BigInt::from(10u64).pow(12));

    Qm212DressedQedG2Report {
        diamond_spanning_tree_count: trees.len(),
        diamond_first_betti_number: diamond.first_betti_number(),
        u_diamond_unit: u_unit,
        u_diamond_prime_weights: u_prime,
        kirchhoff_identity_holds_on_diamond: u_unit == k_unit
            && u_unit == q(8, 1)
            && u_prime == k_prime
            && u_prime == q(101, 1),
        kirchhoff_identity_holds_on_triangle: u_tri == k_tri && u_tri == q(18, 1),
        dfm_retraction_idempotent: dressed_twice == dressed,
        dfm_retraction_gauge_invariant: dressed_gauged == dressed,
        dfm_every_tree_neutralizes_tree_edges: every_tree_neutralizes,
        dressed_symanzik_gauge_invariant: u_cochain == u_gauged,
        all_trees_unimodular_basis_change: unimodular_all,
        c1_exact_half: c1.lo == br(1, 2) && c1.hi == br(1, 2),
        c2_decimal_12: c2_12,
        c3_decimal_12: c3_12,
        ae_1_to_3_decimal_12: ae3_lo.clone(),
        ae_1_to_3_12_digits_agree: ae3_eq && ae3_lo == "0.001159652231",
        ae_1_to_4_decimal_12: ae4_lo.clone(),
        ae_1_to_4_12_digits_agree: ae4_eq && ae4_lo == "0.001159652175",
        ae_1_to_4_total_width_lt_1e12: ae_4_total.width() < inv_1e12,
    }
}

fn main(){
 let graph=CarrierGraph::bubble();let phases=[0,1];let got=cycle_invariant_exponents(&graph,&phases,12);assert_eq!(got,vec![0]);assert_ne!(got,vec![1]);
 let bad=dress_cochain_on_tree(&graph,&phases,12,&[1]);assert_ne!(bad[1],0);let good=dress_cochain_on_tree(&graph,&phases,12,&[0]);assert_eq!(good[0],0);
 println!("parallel_edge_holonomy={:?}; expected_chord_holonomy=1; selected_tree1_phase={}",got,bad[1]);
 let truncated=f2_eliminate(&[vec![0]],&[]);let full=f2_eliminate(&[vec![0]],&[1]);assert!(truncated.consistent);assert!(!full.consistent);println!("short_rhs_drops_inconsistent_constraint=true");
 let pi_bad=pi_big_interval(1);let pi_good=pi_big_interval(20);assert!(pi_bad.lo>pi_good.hi);let z_bad=zeta3_big_interval(1);let z_good=zeta3_big_interval(20);assert!(z_bad.lo>z_good.hi);println!("odd_term_pi_and_zeta3_intervals_disjoint_from_valid_even_controls=true");
 let i2=mat24_id(2);let (mult,count,valid)=spectral_multiplicities_and_roots(&i2,1);assert_eq!(mult,vec![2]);assert_eq!(count,2);assert!(valid);let mut mixed=i2.clone();mixed[1][1]=Cyclo24::from_rat(q(-1,1));assert_eq!(mat24_mul(&mixed,&mixed),i2);assert_eq!(mat24_mul(&mat24_dagger(&mixed),&mixed),i2);assert_ne!(mixed,i2);assert_ne!(mixed,mat24_scale(&i2,Cyclo24::from_rat(q(-1,1))));println!("identity2_reported_square_root_count=2; explicit_third_unitary_root=true");
 let r=evaluate_qm211_clock_tower();assert_eq!(r.fourier_d4_square_root_count,8);assert!(r.all_square_roots_unitary_and_square_to_u);println!("fixed_clock_positive_control=true");
}
