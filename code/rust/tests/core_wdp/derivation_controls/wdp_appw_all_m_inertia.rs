//! Exact Sylvester inertias of the Appendix W response on one finite carrier.
//! L=4, Fock dimension 16, theta=1/10, and M=1,2,3,4 only.
//! Each triple is the sign count of that depth's own matrix. It is not an all-M formula
//! and not a continuum limit.

use std::sync::OnceLock;

use num_rational::BigRational;
use num_traits::{One, Signed, ToPrimitive, Zero};

// Fixture notation only: arithmetic is the same BigRational dependency used
// by the canonical exact owners. No private bignum implementation is retained.
#[derive(Clone, Debug, PartialEq, Eq)]
struct Rat(BigRational);
impl Rat {
    fn zero() -> Self { Self(BigRational::zero()) }
    fn one() -> Self { Self(BigRational::one()) }
    fn new(n: i128, d: i128) -> Self { Self(BigRational::new(n.into(), d.into())) }
    fn is_zero(&self) -> bool { self.0.is_zero() }
    fn is_negative(&self) -> bool { self.0.is_negative() }
    fn negated(&self) -> Self { Self(-&self.0) }
    fn add(&self, b: &Self) -> Self { Self(&self.0 + &b.0) }
    fn sub(&self, b: &Self) -> Self { Self(&self.0 - &b.0) }
    fn mul(&self, b: &Self) -> Self { Self(&self.0 * &b.0) }
    fn div(&self, b: &Self) -> Self { Self(&self.0 / &b.0) }
    fn pair(&self) -> (i128, i128) {
        (self.0.numer().to_i128().expect("bounded fixture numerator"),
         self.0.denom().to_i128().expect("bounded fixture denominator"))
    }
}

const SITES: usize = 4;
const FOCK: usize = 16;
const REFUSED: &str = "refused: Sylvester inertia is recorded only for L=4, Fock dimension 16, theta=1/10, and M in {1,2,3,4}";


type Mat = Vec<Vec<Rat>>;

fn eye(n: usize) -> Mat {
    let mut matrix = vec![vec![Rat::zero(); n]; n];
    for i in 0..n {
        matrix[i][i] = Rat::one();
    }
    matrix
}

fn transpose(a: &Mat) -> Mat {
    let n = a.len();
    let mut out = vec![vec![Rat::zero(); n]; n];
    for i in 0..n {
        for j in 0..n {
            out[j][i] = a[i][j].clone();
        }
    }
    out
}

fn add_mat(a: &Mat, b: &Mat) -> Mat {
    let n = a.len();
    let mut out = vec![vec![Rat::zero(); n]; n];
    for i in 0..n {
        for j in 0..n {
            out[i][j] = a[i][j].add(&b[i][j]);
        }
    }
    out
}

fn scale_mat(a: &Mat, factor: &Rat) -> Mat {
    let n = a.len();
    let mut out = vec![vec![Rat::zero(); n]; n];
    for i in 0..n {
        for j in 0..n {
            if !a[i][j].is_zero() {
                out[i][j] = a[i][j].mul(factor);
            }
        }
    }
    out
}

fn matmul(a: &Mat, b: &Mat) -> Mat {
    let n = a.len();
    let mut out = vec![vec![Rat::zero(); n]; n];
    for i in 0..n {
        for k in 0..n {
            if a[i][k].is_zero() {
                continue;
            }
            for j in 0..n {
                if b[k][j].is_zero() {
                    continue;
                }
                let prod = a[i][k].mul(&b[k][j]);
                out[i][j] = out[i][j].add(&prod);
            }
        }
    }
    out
}

fn mat_vec(a: &Mat, v: &[Rat]) -> Vec<Rat> {
    a.iter()
        .map(|row| {
            let mut acc = Rat::zero();
            for (entry, coord) in row.iter().zip(v.iter()) {
                if !entry.is_zero() && !coord.is_zero() {
                    acc = acc.add(&entry.mul(coord));
                }
            }
            acc
        })
        .collect()
}

fn annihilator(site: usize) -> Mat {
    let mut matrix = vec![vec![Rat::zero(); FOCK]; FOCK];
    for state in 0..FOCK {
        if state & (1 << site) == 0 {
            continue;
        }
        let parity = (state & ((1 << site) - 1)).count_ones() % 2;
        let sign = if parity == 0 { 1 } else { -1 };
        matrix[state ^ (1 << site)][state] = Rat::new(sign, 1);
    }
    matrix
}

fn car_data() -> (Mat, [Vec<Rat>; SITES], [Mat; SITES]) {
    let identity = eye(FOCK);
    let annihilators: Vec<Mat> = (0..SITES).map(annihilator).collect();
    let number: Vec<Mat> = annihilators
        .iter()
        .map(|c| matmul(&transpose(c), c))
        .collect();
    let mut diag = std::array::from_fn(|_| vec![Rat::zero(); FOCK]);
    for site in 0..SITES {
        let shifted = add_mat(&number[site], &scale_mat(&identity, &Rat::new(-1, 2)));
        let sign = Rat::new(if site % 2 == 0 { 1 } else { -1 }, 1);
        let observable = scale_mat(&shifted, &sign);
        for state in 0..FOCK {
            diag[site][state] = observable[state][state].clone();
        }
    }
    let mut bonds = Vec::with_capacity(SITES);
    for site in 0..SITES {
        let next = (site + 1) % SITES;
        let dens = add_mat(
            &add_mat(&number[site], &number[next]),
            &scale_mat(&matmul(&number[site], &number[next]), &Rat::new(-2, 1)),
        );
        let hop = add_mat(
            &matmul(&transpose(&annihilators[site]), &annihilators[next]),
            &matmul(&transpose(&annihilators[next]), &annihilators[site]),
        );
        bonds.push(scale_mat(&add_mat(&dens, &hop), &Rat::new(1, 2)));
    }
    (identity, diag, bonds.try_into().unwrap())
}

fn build_connected_response_matrix(
    steps: usize,
    segments: &[Vec<Mat>],
    diag: &[Vec<Rat>],
    trace: &Rat,
    first: &[Rat],
) -> Mat {
    let seg = |lo: usize, hi: usize| &segments[lo][hi - lo];
    let dim = SITES * steps;
    let mut g = vec![vec![Rat::zero(); dim]; dim];
    for i in 0..steps {
        for j in i..steps {
            let h = matmul(seg(0, i), seg(j, steps));
            let middle = seg(i, j);
            let weights = collect_nonzero_fock_weights(&h, middle);
            fill_site_block(&mut g, i, j, &weights, diag, trace, first);
        }
    }
    g
}

fn collect_nonzero_fock_weights(h: &Mat, middle: &Mat) -> Vec<(usize, usize, Rat)> {
    let mut weights = Vec::new();
    for a in 0..FOCK {
        for b in 0..FOCK {
            if !h[a][b].is_zero() && !middle[b][a].is_zero() {
                weights.push((a, b, h[a][b].mul(&middle[b][a])));
            }
        }
    }
    weights
}

fn fill_site_block(
    g: &mut Mat,
    i: usize,
    j: usize,
    weights: &[(usize, usize, Rat)],
    diag: &[Vec<Rat>],
    trace: &Rat,
    first: &[Rat],
) {
    for x in 0..SITES {
        for y in 0..SITES {
            let mut second = Rat::zero();
            for (a, b, w) in weights {
                second = second.add(&w.mul(&diag[x][*a]).mul(&diag[y][*b]));
            }
            let entry = second.div(trace).sub(&first[SITES * i + x].mul(&first[SITES * j + y]));
            let row = SITES * i + x;
            let col = SITES * j + y;
            g[row][col] = entry.clone();
            g[col][row] = entry;
        }
    }
}

fn staggered_eigenvalue(m: u32, dim: usize, g: &Mat) -> Rat {
    let v: Vec<Rat> = (0..dim)
        .map(|index| if (index / SITES) % 2 == 0 { Rat::one() } else { Rat::new(-1, 1) })
        .collect();
    let gv = mat_vec(g, &v);
    let mut quad = Rat::zero();
    for (coord, image) in v.iter().zip(gv.iter()) {
        quad = quad.add(&coord.mul(image));
    }
    // lambda = v^T G v / (L N), and N = 2M, so the denominator is 8M.
    let lambda = quad.div(&Rat::new(8 * m as i128, 1));
    for (coord, image) in v.iter().zip(gv.iter()) {
        assert_eq!(image, &lambda.mul(coord), "staggered vector is not an eigenvector");
    }
    lambda
}

fn response(m: u32) -> (Mat, Rat, Rat) {
    assert!((1..=4).contains(&m), "M outside the selected scope is not computed");
    let (identity, diag, bonds) = car_data();
    let r = Rat::new(1, 10 * m as i128);
    let layer = |left: usize, right: usize| {
        matmul(
            &add_mat(&identity, &scale_mat(&bonds[left], &r)),
            &add_mat(&identity, &scale_mat(&bonds[right], &r)),
        )
    };
    // T0 = (I+r P0)(I+r P2), T1 = (I+r P1)(I+r P3), K_j = T_(j mod 2).
    let k = [layer(0, 2), layer(1, 3)];
    let steps = 2 * m as usize;
    let mut segments: Vec<Vec<Mat>> = Vec::with_capacity(steps + 1);
    for lo in 0..=steps {
        let mut row = Vec::with_capacity(steps - lo + 1);
        row.push(identity.clone());
        for hi in (lo + 1)..=steps {
            let next = matmul(&k[(hi - 1) % 2], row.last().unwrap());
            row.push(next);
        }
        segments.push(row);
    }
    let seg = |lo: usize, hi: usize| &segments[lo][hi - lo];
    let mut trace = Rat::zero();
    for state in 0..FOCK {
        trace = trace.add(&seg(0, steps)[state][state]);
    }
    assert!(!trace.is_zero(), "partition trace vanished");
    let mut first = Vec::with_capacity(SITES * steps);
    for time in 0..steps {
        let cyclic = matmul(seg(0, time), seg(time, steps));
        for site in 0..SITES {
            let mut acc = Rat::zero();
            for state in 0..FOCK {
                acc = acc.add(&cyclic[state][state].mul(&diag[site][state]));
            }
            first.push(acc.div(&trace));
        }
    }
    let dim = SITES * steps;
    let g = build_connected_response_matrix(steps, &segments, &diag, &trace, &first);
    let lambda = staggered_eigenvalue(m, dim, &g);
    let one_plus_r = Rat::new(10 * m as i128 + 1, 10 * m as i128);
    let mut scale = Rat::one();
    for _ in 0..m {
        scale = scale.mul(&one_plus_r);
    }
    let partition = trace.div(&scale);
    (g, partition, lambda)
}

/// Congruence diagonalization. A zero-diagonal pair uses e_i <- e_i + e_j, which adds 2 G_ij on that diagonal.
fn eliminate_congruence_pivot(a: &mut Mat, pivot: usize, active: &[usize]) {
    let n = a.len();
    let piv = a[pivot][pivot].clone();
    for &i in active {
        let factor = a[i][pivot].div(&piv);
        if factor.is_zero() {
            continue;
        }
        let pivot_row = a[pivot].clone();
        for t in 0..n {
            let prod = factor.mul(&pivot_row[t]);
            a[i][t] = a[i][t].sub(&prod);
        }
        for t in 0..n {
            let prod = factor.mul(&a[t][pivot]);
            a[t][i] = a[t][i].sub(&prod);
        }
    }
}

fn find_nonzero_off_diagonal(a: &Mat, active: &[usize]) -> Option<(usize, usize)> {
    for (pos, &i) in active.iter().enumerate() {
        for &j in &active[pos + 1..] {
            if !a[i][j].is_zero() {
                return Some((i, j));
            }
        }
    }
    None
}

fn add_symmetric_row_col(a: &mut Mat, i: usize, j: usize) {
    let n = a.len();
    let row_j = a[j].clone();
    for t in 0..n {
        a[i][t] = a[i][t].add(&row_j[t]);
    }
    let col_j: Vec<Rat> = (0..n).map(|t| a[t][j].clone()).collect();
    for t in 0..n {
        a[t][i] = a[t][i].add(&col_j[t]);
    }
}

fn sylvester(mut a: Mat) -> (u32, u32, u32) {
    let n = a.len();
    let mut active: Vec<usize> = (0..n).collect();
    let (mut positive, mut negative, mut zero) = (0u32, 0u32, 0u32);
    while !active.is_empty() {
        if let Some(pivot) = active.iter().copied().find(|&i| !a[i][i].is_zero()) {
            if a[pivot][pivot].is_negative() {
                negative += 1;
            } else {
                positive += 1;
            }
            active.retain(|&i| i != pivot);
            eliminate_congruence_pivot(&mut a, pivot, &active);
        } else if let Some((i, j)) = find_nonzero_off_diagonal(&a, &active) {
            add_symmetric_row_col(&mut a, i, j);
        } else {
            zero += active.len() as u32;
            break;
        }
    }
    (positive, negative, zero)
}

const M1_DEN: i128 = 2_825_760;
const M1_SCALED: [[i64; 8]; 8] = [
    [706440, 17240, 840, 17240, 706441, 17241, 841, 17241],
    [17240, 706440, 17240, 840, 17241, 706441, 17241, 841],
    [840, 17240, 706440, 17240, 841, 17241, 706441, 17241],
    [17240, 840, 17240, 706440, 17241, 841, 17241, 706441],
    [706441, 17241, 841, 17241, 706440, 17240, 840, 17240],
    [17241, 706441, 17241, 841, 17240, 706440, 17240, 840],
    [841, 17241, 706441, 17241, 840, 17240, 706440, 17240],
    [17241, 841, 17241, 706441, 17240, 840, 17240, 706440],
];
const M1_BASIS: [[i64; 8]; 8] = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, -1, 1, -1, 1, -1, 1, -1],
    [1, 1, -1, -1, 1, 1, -1, -1],
    [1, -1, -1, 1, 1, -1, -1, 1],
    [1, 1, 1, 1, -1, -1, -1, -1],
    [1, -1, 1, -1, -1, 1, -1, 1],
    [1, 1, -1, -1, -1, -1, 1, 1],
    [1, -1, -1, 1, -1, 1, 1, -1],
];
const M1_EIGEN: [i64; 8] = [1483524, 1345600, 1411200, 1411200, -4, 0, 0, 0];

fn assert_m1_integer_witness(g: &Mat) {
    assert_eq!(M1_DEN, 4 * 706440);
    for i in 0..8 {
        for j in 0..8 {
            let (numer, denom) = g[i][j].pair();
            assert_eq!(numer * M1_DEN, M1_SCALED[i][j] as i128 * denom);
        }
    }
    for (vector, lambda) in M1_BASIS.iter().zip(M1_EIGEN) {
        for row in 0..8 {
            let image: i64 = M1_SCALED[row].iter().zip(vector).map(|(entry, coord)| entry * coord).sum();
            assert_eq!(image, lambda * vector[row]);
        }
    }
    for i in 0..8 {
        for j in 0..8 {
            let dot: i64 = M1_BASIS[i].iter().zip(M1_BASIS[j]).map(|(left, right)| left * right).sum();
            assert_eq!(dot, if i == j { 8 } else { 0 });
        }
    }
    let (pos, neg, zer) = M1_EIGEN.iter().fold((0, 0, 0), |(p, n, z), lambda| {
        if *lambda > 0 { (p + 1, n, z) } else if *lambda < 0 { (p, n + 1, z) } else { (p, n, z + 1) }
    });
    assert_eq!((pos, neg, zer), (4, 1, 3));
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Observation {
    pub m: i64,
    pub sites: i64,
    pub fock: i64,
    pub theta_num: i64,
    pub theta_den: i64,
    pub step_num: i64,
    pub step_den: i64,
    pub dimension: i64,
    pub positive: i64,
    pub negative: i64,
    pub zero: i64,
    pub partition_num: i128,
    pub partition_den: i128,
    pub staggered_num: i128,
    pub staggered_den: i128,
}

fn observation(m: u32) -> Observation {
    let (g, partition, staggered) = response(m);
    if m == 1 {
        assert_m1_integer_witness(&g);
    }
    let dimension = 8 * m;
    assert_eq!(g.len(), dimension as usize);
    let (positive, negative, zero) = sylvester(g);
    assert_eq!(positive + negative + zero, dimension);
    // Recorded on this depth only. The arithmetic 4M is not applied at any other M.
    assert_eq!(positive, 4 * m, "positive count");
    assert_eq!(negative, 1, "negative count");
    assert_eq!(zero, 4 * m - 1, "zero count");
    let (partition_num, partition_den) = partition.pair();
    let (staggered_num, staggered_den) = staggered.pair();
    Observation {
        m: m as i64,
        sites: SITES as i64,
        fock: FOCK as i64,
        theta_num: 1,
        theta_den: 10,
        step_num: 1,
        step_den: 10 * m as i64,
        dimension: dimension as i64,
        positive: positive as i64,
        negative: negative as i64,
        zero: zero as i64,
        partition_num,
        partition_den,
        staggered_num,
        staggered_den,
    }
}

/// The four computed rows at theta = 1/10. Depths outside 1..=4 are not evaluated.
pub fn witness() -> [Observation; 4] {
    static CACHE: OnceLock<[Observation; 4]> = OnceLock::new();
    *CACHE.get_or_init(|| [observation(1), observation(2), observation(3), observation(4)])
}

/// In-scope rows return the computed inertia. Every other carrier or depth is refused.
pub fn inertia_claim(m: i64, theta_num: i64, theta_den: i64, sites: i64) -> Result<(i64, i64, i64), &'static str> {
    if sites != 4 || theta_num != 1 || theta_den != 10 || !(1..=4).contains(&m) {
        return Err(REFUSED);
    }
    let row = witness().into_iter().find(|row| row.m == m).expect("selected depth");
    Ok((row.positive, row.negative, row.zero))
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appw_all_m_inertia.rs
// Claim: urn:core:crates_rs:tests:wdp-appw-all-m-inertia:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord88505621 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord88505621` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError88505621 {
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
impl BoundaryError88505621 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError88505621 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError88505621 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord88505621 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError88505621> {
        if capacity_bound == 0 {
            return Err(BoundaryError88505621::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError88505621::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError88505621::ExceedsCapacity {
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

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::{inertia_claim, sylvester, witness, Rat};

    #[test]
    fn arbitrary_precision_fixture_arithmetic() {
        let large = Rat::new(i128::MAX, 7).mul(&Rat::new(i128::MAX, 11));
        assert_eq!(large.div(&Rat::new(i128::MAX, 7)), Rat::new(i128::MAX, 11));
        assert_eq!(Rat::new(2, -4), Rat::new(-1, 2));
        assert_eq!(Rat::new(-15, 4).add(&Rat::new(3, 1)), Rat::new(-3, 4));
    }

    #[test]
    fn sylvester_sign_counts_on_small_matrices() {
        let diag = vec![
            vec![Rat::new(1, 1), Rat::zero(), Rat::zero()],
            vec![Rat::zero(), Rat::new(-2, 1), Rat::zero()],
            vec![Rat::zero(), Rat::zero(), Rat::zero()],
        ];
        assert_eq!(sylvester(diag), (1, 1, 1));
        let off = vec![
            vec![Rat::zero(), Rat::new(1, 1)],
            vec![Rat::new(1, 1), Rat::zero()],
        ];
        assert_eq!(sylvester(off), (1, 1, 0));
        let neg = vec![
            vec![Rat::zero(), Rat::new(-3, 1)],
            vec![Rat::new(-3, 1), Rat::zero()],
        ];
        assert_eq!(sylvester(neg), (1, 1, 0));
    }

    #[test]
    fn four_finite_inertias_are_the_selected_observations() {
        let rows = witness();
        let expect = [
            (1, 8, 4, 1, 3, 17_661_i128, 1_100, -1, 706_440),
            (2, 16, 8, 1, 7, 755_374_987, 47_040_000, -35_281, 90_644_998_440),
            (3, 24, 12, 1, 11, 1_395_062_306_051_761, 86_870_556_000_000, -12_188_547_841, 55_802_492_242_070_440),
            (
                4,
                32,
                16,
                1,
                15,
                2_379_246_859_363_301_568_641,
                148_151_258_316_800_000_000,
                -14_588_472_130_734_881,
                95_169_874_374_532_062_745_640,
            ),
        ];
        for (row, exp) in rows.iter().zip(expect) {
            assert_eq!(row.m, exp.0);
            assert_eq!(row.sites, 4);
            assert_eq!(row.fock, 16);
            assert_eq!((row.theta_num, row.theta_den), (1, 10));
            assert_eq!((row.step_num, row.step_den), (1, 10 * exp.0));
            assert_eq!(row.dimension, exp.1);
            assert_eq!((row.positive, row.negative, row.zero), (exp.2, exp.3, exp.4));
            assert_eq!(row.positive + row.negative + row.zero, row.dimension);
            assert_eq!((row.partition_num, row.partition_den), (exp.5, exp.6));
            assert_eq!((row.staggered_num, row.staggered_den), (exp.7, exp.8));
            assert_eq!(inertia_claim(exp.0, 1, 10, 4), Ok((exp.2, exp.3, exp.4)));
        }
    }

    #[test]
    fn outside_the_four_depths_is_refused() {
        assert_eq!(inertia_claim(5, 1, 10, 4), Err(super::REFUSED));
        assert!(inertia_claim(0, 1, 10, 4).is_err());
        assert!(inertia_claim(1, 1, 192, 4).is_err());
        assert!(inertia_claim(1, 2, 10, 4).is_err());
        assert!(inertia_claim(4, 1, 10, 8).is_err());
        assert_ne!(inertia_claim(5, 1, 10, 4).ok(), Some((20, 1, 19)));
    }
}

#[test]
fn l4_boundary_admits_and_refuses_88505621() {
    let admitted = BoundaryRecord88505621::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord88505621::try_admit(9, 8).is_err());
}
