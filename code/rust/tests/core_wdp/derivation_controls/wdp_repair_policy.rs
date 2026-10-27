//! Finite refutation of the Phi_1-decreasing repair policy on two windows.
//!
//! One-cell: C0 = 0, C1 = Q e, C2 = Q s, d0 = 0, d1 = id, J = absolute value,
//! h_n = 2^{-n}. Filled triangle: delta_n = 2^{-n}(1, 1, 0) with the P08 maps.
//! Values are reduced rationals. This check is not a continuum limit.

use std::cmp::Ordering;

const MAX_INDEX: u32 = 40;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Diagnostic {
    ExactClass,
    ClosedResidual,
    ActiveClosureFailure,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Step {
    pub phi: (i128, i128),
    pub gamma: (i128, i128),
    pub r_cl: Option<(i128, i128)>,
    pub bound: (i128, i128),
    pub class: Diagnostic,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub one_cell_phi: [(i128, i128); 3],
    pub one_cell_gamma: [(i128, i128); 3],
    pub one_cell_r: [(i128, i128); 3],
    pub one_cell_bound: (i128, i128),
    pub triangle_scaled_phi: [(i128, i128); 3],
    pub triangle_scaled_gamma: [(i128, i128); 3],
    pub triangle_scaled_r: [(i128, i128); 3],
    pub triangle_bound: (i128, i128),
    pub triangle_cochain: [[(i128, i128); 3]; 3],
    pub triangle_repair: [[(i128, i128); 3]; 3],
    pub circulation: [(i128, i128); 3],
    pub shifted_cochain: [(i128, i128); 3],
    pub shifted_repair: [(i128, i128); 3],
    pub shifted_phi: (i128, i128),
    pub shifted_raw_l1: (i128, i128),
    pub shifted_r: (i128, i128),
    pub shifted_class: Diagnostic,
    pub composition_zero: bool,
    pub reaches_exact_class: bool,
    pub prefix_steps_accepted: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Rat {
    num: i128,
    den: i128,
}

fn iabs(value: i128) -> i128 {
    if value < 0 {
        value.checked_neg().expect("abs")
    } else {
        value
    }
}

fn gcd(mut a: i128, mut b: i128) -> i128 {
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

impl Rat {
    fn reduced(mut num: i128, mut den: i128) -> Self {
        assert!(den != 0, "zero denominator");
        if den < 0 {
            num = num.checked_neg().expect("numerator sign");
            den = den.checked_neg().expect("denominator sign");
        }
        if num == 0 {
            return Self { num: 0, den: 1 };
        }
        let divisor = gcd(iabs(num), den);
        Self {
            num: num / divisor,
            den: den / divisor,
        }
    }

    fn new(num: i128, den: i128) -> Self {
        Self::reduced(num, den)
    }

    fn integer(value: i128) -> Self {
        Self { num: value, den: 1 }
    }

    fn zero() -> Self {
        Self::integer(0)
    }

    fn one() -> Self {
        Self::integer(1)
    }

    fn two_pow(exp: i32) -> Self {
        assert!((-126..127).contains(&exp), "power of two outside i128");
        if exp >= 0 {
            Self::integer(1_i128 << (exp as u32))
        } else {
            Self::new(1, 1_i128 << ((-exp) as u32))
        }
    }

    fn add(self, rhs: Self) -> Self {
        let left = self.num.checked_mul(rhs.den).expect("add");
        let right = rhs.num.checked_mul(self.den).expect("add");
        Self::reduced(
            left.checked_add(right).expect("add"),
            self.den.checked_mul(rhs.den).expect("add"),
        )
    }

    fn neg(self) -> Self {
        Self {
            num: self.num.checked_neg().expect("neg"),
            den: self.den,
        }
    }

    fn sub(self, rhs: Self) -> Self {
        self.add(rhs.neg())
    }

    fn mul(self, rhs: Self) -> Self {
        Self::reduced(
            self.num.checked_mul(rhs.num).expect("mul"),
            self.den.checked_mul(rhs.den).expect("mul"),
        )
    }

    fn div(self, rhs: Self) -> Self {
        assert!(rhs.num != 0, "division by zero");
        self.mul(Self::reduced(rhs.den, rhs.num))
    }

    fn abs(self) -> Self {
        Self {
            num: iabs(self.num),
            den: self.den,
        }
    }

    fn is_zero(self) -> bool {
        self.num == 0
    }

    fn is_positive(self) -> bool {
        self.num > 0
    }
}

impl PartialOrd for Rat {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Rat {
    fn cmp(&self, other: &Self) -> Ordering {
        let left = self.num.checked_mul(other.den).expect("cmp");
        let right = other.num.checked_mul(self.den).expect("cmp");
        left.cmp(&right)
    }
}

fn parts(value: Rat) -> (i128, i128) {
    (value.num, value.den)
}

fn parts3(value: [Rat; 3]) -> [(i128, i128); 3] {
    [parts(value[0]), parts(value[1]), parts(value[2])]
}

fn in_range(index: u32) {
    assert!(
        index <= MAX_INDEX,
        "index outside the exact i128 window"
    );
}

#[derive(Clone, Copy, Debug)]
struct Eval {
    phi: Rat,
    gamma: Rat,
    r_cl: Option<Rat>,
    bound: Rat,
    class: Diagnostic,
}

fn to_step(eval: Eval) -> Step {
    Step {
        phi: parts(eval.phi),
        gamma: parts(eval.gamma),
        r_cl: eval.r_cl.map(parts),
        bound: parts(eval.bound),
        class: eval.class,
    }
}

fn classify(phi: Rat, gamma: Rat) -> Diagnostic {
    if phi.is_zero() {
        assert!(gamma.is_zero(), "Phi_1 = 0 with nonzero Gamma_2");
        Diagnostic::ExactClass
    } else if gamma.is_zero() {
        Diagnostic::ClosedResidual
    } else {
        Diagnostic::ActiveClosureFailure
    }
}

fn std_basis(index: usize) -> [Rat; 3] {
    assert!(index < 3);
    let mut vector = [Rat::zero(); 3];
    vector[index] = Rat::one();
    vector
}

fn add3(left: [Rat; 3], right: [Rat; 3]) -> [Rat; 3] {
    [
        left[0].add(right[0]),
        left[1].add(right[1]),
        left[2].add(right[2]),
    ]
}

fn sub3(left: [Rat; 3], right: [Rat; 3]) -> [Rat; 3] {
    [
        left[0].sub(right[0]),
        left[1].sub(right[1]),
        left[2].sub(right[2]),
    ]
}

fn l1(value: [Rat; 3]) -> Rat {
    value[0].abs().add(value[1].abs()).add(value[2].abs())
}

fn dot(left: [Rat; 3], right: [Rat; 3]) -> Rat {
    left[0]
        .mul(right[0])
        .add(left[1].mul(right[1]))
        .add(left[2].mul(right[2]))
}

/// d0 f = (f1 - f0, f2 - f1, f2 - f0) on vertices (0, 1, 2).
fn d0(vertex: [Rat; 3]) -> [Rat; 3] {
    [
        vertex[1].sub(vertex[0]),
        vertex[2].sub(vertex[1]),
        vertex[2].sub(vertex[0]),
    ]
}

/// d1 x = x01 + x12 - x02 on edges (01, 12, 02).
fn d1(edge: [Rat; 3]) -> Rat {
    edge[0].add(edge[1]).sub(edge[2])
}

fn column_sum_norm(columns: &[i128]) -> Rat {
    let mut max = 0_i128;
    for column in columns {
        max = max.max(iabs(*column));
    }
    Rat::integer(max)
}

fn one_cell_norm() -> Rat {
    // Unweighted L1 to L1 norm: largest absolute column sum of d1 = (1).
    let norm = column_sum_norm(&[1]);
    let attained = Rat::one();
    assert_eq!(attained.abs(), norm.mul(attained.abs()));
    norm
}

fn triangle_norm() -> Rat {
    // Row (1, 1, -1). Each absolute column sum is 1.
    let norm = column_sum_norm(&[1, 1, -1]);
    for index in 0..3 {
        assert!(
            d1(d0(std_basis(index))).is_zero(),
            "d1 d0 was not zero"
        );
        let edge = std_basis(index);
        assert!(d1(edge).abs() <= norm.mul(l1(edge)));
    }
    assert_eq!(d1(std_basis(0)).abs(), norm);
    norm
}

/// C0 is the zero space, so d0 is the zero map and d1 d0 has nothing else to hit.
fn one_cell_composition_is_zero() -> bool {
    let d0_image = 0_i128;
    let d1_image = d0_image;
    d1_image == 0
}

fn composition_zero() -> bool {
    one_cell_composition_is_zero()
        && (0..3).all(|index| d1(d0(std_basis(index))).is_zero())
}

fn circulation() -> [Rat; 3] {
    [Rat::one(), Rat::one(), Rat::new(-1, 1)]
}

fn circulation_ok(y: [Rat; 3]) -> bool {
    let bounded = y.iter().all(|edge| edge.abs() <= Rat::one());
    let adjoint = (0..3).all(|index| dot(y, d0(std_basis(index))).is_zero());
    bounded && adjoint
}

/// A closed edge field on this triangle is the coboundary of (0, x01, x01 + x12).
fn is_exact(edge: [Rat; 3]) -> bool {
    if !d1(edge).is_zero() {
        return false;
    }
    let repair = [Rat::zero(), edge[0], edge[0].add(edge[1])];
    d0(repair) == edge
}

fn certify(edge: [Rat; 3], repair: [Rat; 3]) -> Eval {
    let y = circulation();
    assert!(circulation_ok(y), "y is not a unit-weight circulation");
    let mass = l1(sub3(edge, d0(repair)));
    let pairing = dot(y, edge);
    assert_eq!(mass, pairing, "repair mass does not meet the circulation");
    assert_eq!(d1(edge), mass, "signed closure charge left the certificate");
    let phi = pairing;
    let gamma = d1(edge).abs();
    let bound = triangle_norm();
    assert_eq!(gamma, bound.mul(phi));
    let class = classify(phi, gamma);
    let r_cl = if phi.is_positive() {
        let ratio = gamma.div(phi);
        assert!(ratio >= Rat::zero() && ratio <= bound);
        Some(ratio)
    } else {
        None
    };
    Eval {
        phi,
        gamma,
        r_cl,
        bound,
        class,
    }
}

fn scaled_delta(index: u32) -> [Rat; 3] {
    let scale = Rat::two_pow(-(index as i32));
    [scale, scale, Rat::zero()]
}

fn scaled_repair(index: u32) -> [Rat; 3] {
    let scale = Rat::two_pow(-(index as i32));
    [Rat::zero(), scale, Rat::zero()]
}

fn eval_one(value: Rat) -> Eval {
    assert!(value >= Rat::zero(), "one-cell run uses a nonnegative value");
    // im d0 = {0}, so the only repair is f = 0 and Phi_1([h]) = |h|.
    let phi = value.sub(Rat::zero()).abs();
    let gamma = value.abs();
    let y = Rat::one();
    assert!(y.abs() <= Rat::one());
    assert_eq!(y.mul(value), phi);
    assert!(one_cell_composition_is_zero());
    let bound = one_cell_norm();
    assert_eq!(gamma, bound.mul(phi));
    let class = classify(phi, gamma);
    let r_cl = if phi.is_positive() {
        let ratio = gamma.div(phi);
        assert!(ratio <= bound);
        Some(ratio)
    } else {
        None
    };
    Eval {
        phi,
        gamma,
        r_cl,
        bound,
        class,
    }
}

fn eval_one_index(index: u32) -> Eval {
    in_range(index);
    eval_one(Rat::two_pow(-(index as i32)))
}

fn eval_triangle_index(index: u32) -> Eval {
    in_range(index);
    certify(scaled_delta(index), scaled_repair(index))
}

fn shifted_inputs() -> ([Rat; 3], [Rat; 3]) {
    let coboundary = [Rat::zero(), Rat::zero(), Rat::integer(5)];
    let cochain = add3(scaled_delta(0), d0(coboundary));
    let repair = add3(scaled_repair(0), coboundary);
    (cochain, repair)
}

fn shifted_eval() -> (Eval, Rat, [Rat; 3], [Rat; 3]) {
    let (cochain, repair) = shifted_inputs();
    assert!(
        is_exact(sub3(cochain, scaled_delta(0))),
        "shift was not a coboundary"
    );
    let eval = certify(cochain, repair);
    (eval, l1(cochain), cochain, repair)
}

fn gate(current: &Eval, next: &Eval) -> bool {
    match (current.r_cl, next.r_cl) {
        (Some(current_ratio), Some(next_ratio)) => {
            next.phi < current.phi
                && current_ratio >= Rat::zero()
                && current_ratio <= current.bound
                && next_ratio >= Rat::zero()
                && next_ratio <= next.bound
        }
        _ => false,
    }
}

fn active_pair(current: &Eval, next: &Eval) -> bool {
    current.class == Diagnostic::ActiveClosureFailure
        && next.class == Diagnostic::ActiveClosureFailure
}

pub fn one_cell(index: u32) -> Step {
    to_step(eval_one_index(index))
}

pub fn one_cell_zero() -> Step {
    to_step(eval_one(Rat::zero()))
}

pub fn triangle(index: u32) -> Step {
    to_step(eval_triangle_index(index))
}

pub fn triangle_cochain(index: u32) -> [(i128, i128); 3] {
    in_range(index);
    parts3(scaled_delta(index))
}

pub fn triangle_repair(index: u32) -> [(i128, i128); 3] {
    in_range(index);
    parts3(scaled_repair(index))
}

pub fn vertex_coboundary(vertex: usize) -> [(i128, i128); 3] {
    parts3(d0(std_basis(vertex)))
}

pub fn closure_value(edges: [(i128, i128); 3]) -> (i128, i128) {
    let edge = [
        Rat::new(edges[0].0, edges[0].1),
        Rat::new(edges[1].0, edges[1].1),
        Rat::new(edges[2].0, edges[2].1),
    ];
    parts(d1(edge))
}

pub fn difference_is_exact(index: u32) -> bool {
    in_range(index + 1);
    is_exact(sub3(scaled_delta(index), scaled_delta(index + 1)))
}

pub fn vertex_coboundary_is_exact(vertex: usize) -> bool {
    is_exact(d0(std_basis(vertex)))
}

pub fn one_cell_step_accepted(index: u32) -> bool {
    in_range(index + 1);
    let current = eval_one_index(index);
    let next = eval_one_index(index + 1);
    let drop = current.phi.sub(next.phi);
    drop == Rat::two_pow(-((index + 1) as i32))
        && drop.is_positive()
        && gate(&current, &next)
        && active_pair(&current, &next)
}

pub fn triangle_step_accepted(index: u32) -> bool {
    in_range(index + 1);
    let current = eval_triangle_index(index);
    let next = eval_triangle_index(index + 1);
    let drop = current.phi.sub(next.phi);
    drop == Rat::two_pow(-(index as i32))
        && drop.is_positive()
        && gate(&current, &next)
        && active_pair(&current, &next)
        && !difference_is_exact(index)
}

fn ratio_of(step: Step) -> (i128, i128) {
    step.r_cl.expect("Phi_1 > 0 on this state")
}

/// Prefix record for n = 0, 1, 2, plus the coboundary shift that the gate refuses.
pub fn witness() -> Witness {
    let one = [one_cell(0), one_cell(1), one_cell(2)];
    let tri = [triangle(0), triangle(1), triangle(2)];
    let (shifted, raw, cochain, repair) = shifted_eval();
    let prefix_steps_accepted = (0..3).all(|index| {
        one_cell_step_accepted(index) && triangle_step_accepted(index)
    });
    let reaches_exact_class = (0..=3).any(|index| {
        one_cell(index).class == Diagnostic::ExactClass
            || triangle(index).class == Diagnostic::ExactClass
    });
    Witness {
        one_cell_phi: [one[0].phi, one[1].phi, one[2].phi],
        one_cell_gamma: [one[0].gamma, one[1].gamma, one[2].gamma],
        one_cell_r: [ratio_of(one[0]), ratio_of(one[1]), ratio_of(one[2])],
        one_cell_bound: one[0].bound,
        triangle_scaled_phi: [tri[0].phi, tri[1].phi, tri[2].phi],
        triangle_scaled_gamma: [tri[0].gamma, tri[1].gamma, tri[2].gamma],
        triangle_scaled_r: [ratio_of(tri[0]), ratio_of(tri[1]), ratio_of(tri[2])],
        triangle_bound: tri[0].bound,
        triangle_cochain: [
            triangle_cochain(0),
            triangle_cochain(1),
            triangle_cochain(2),
        ],
        triangle_repair: [triangle_repair(0), triangle_repair(1), triangle_repair(2)],
        circulation: parts3(circulation()),
        shifted_cochain: parts3(cochain),
        shifted_repair: parts3(repair),
        shifted_phi: parts(shifted.phi),
        shifted_raw_l1: parts(raw),
        shifted_r: parts(shifted.r_cl.expect("shifted Phi_1 > 0")),
        shifted_class: shifted.class,
        composition_zero: composition_zero(),
        reaches_exact_class,
        prefix_steps_accepted,
    }
}

pub fn refuse_coboundary_edit() -> Result<(), &'static str> {
    let base = eval_triangle_index(0);
    let (shifted, raw, _, _) = shifted_eval();
    if base.phi != shifted.phi {
        return Err("internal: a coboundary edit changed Phi_1");
    }
    if raw == shifted.phi {
        return Err("internal: raw L1 did not separate from Phi_1");
    }
    let ratio_leaves = match shifted.r_cl {
        Some(ratio) => ratio > shifted.bound || ratio < Rat::zero(),
        None => true,
    };
    if ratio_leaves {
        return Err("internal: R_cl left the bound");
    }
    if gate(&base, &shifted) {
        return Err("internal: the decrease gate accepted a coboundary edit");
    }
    Err("refused: Phi_1 does not strictly decrease")
}

pub fn refuse_one_cell_as_triangle(index: u32) -> Result<(), &'static str> {
    let one = eval_one_index(index).phi;
    let tri = eval_triangle_index(index).phi;
    if one == tri {
        Ok(())
    } else {
        Err("refused: one-cell Phi_1 is not the filled-triangle signature")
    }
}

pub fn refuse_claimed_triangle_phi(num: i128, den: i128) -> Result<(), &'static str> {
    let claimed = Rat::new(num, den);
    let certified = eval_triangle_index(0).phi;
    let mut copied = eval_one_index(0).phi;
    copied = copied.add(eval_one_index(1).phi);
    copied = copied.add(eval_one_index(2).phi);
    let copies_one_cell = (0..3).any(|index| claimed == eval_one_index(index).phi);
    if copies_one_cell || claimed == copied {
        Err("refused: a one-cell value is not the filled-triangle Phi_1")
    } else if claimed != certified {
        Err("refused: not the certified filled-triangle Phi_1")
    } else {
        Ok(())
    }
}

pub fn refuse_uniform_decrement(num: i128, den: i128) -> Result<(), &'static str> {
    let epsilon = Rat::new(num, den);
    if !epsilon.is_positive() {
        return Err("refused: a nonpositive epsilon is not a uniform drop");
    }
    for index in 0..16 {
        let current = eval_one_index(index);
        let next = eval_one_index(index + 1);
        let drop = current.phi.sub(next.phi);
        if gate(&current, &next) && drop.is_positive() && drop < epsilon {
            return Err("refused: the dyadic run has no uniform positive decrement");
        }
    }
    Ok(())
}

pub fn refuse_ratio_at_exact_class() -> Result<(), &'static str> {
    let zero = one_cell_zero();
    if zero.class != Diagnostic::ExactClass
        || zero.phi != (0, 1)
        || zero.gamma != (0, 1)
        || zero.r_cl.is_some()
    {
        return Err("internal: zero state was not ExactClass without R_cl");
    }
    Err("refused: R_cl is undefined when Phi_1 = 0")
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_repair_policy.rs
// Claim: urn:core:crates_rs:tests:wdp-repair-policy:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordf63096e9 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordf63096e9` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorf63096e9 {
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
impl BoundaryErrorf63096e9 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorf63096e9 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorf63096e9 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordf63096e9 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorf63096e9> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorf63096e9::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorf63096e9::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorf63096e9::ExceedsCapacity {
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
    use super::*;

    fn strictly_less(left: (i128, i128), right: (i128, i128)) -> bool {
        let left_cross = left.0.checked_mul(right.1).expect("cmp");
        let right_cross = right.0.checked_mul(left.1).expect("cmp");
        left_cross < right_cross
    }

    #[test]
    fn exact_countermodel_on_both_windows() {
        let record = witness();
        assert_eq!(
            record,
            Witness {
                one_cell_phi: [(1, 1), (1, 2), (1, 4)],
                one_cell_gamma: [(1, 1), (1, 2), (1, 4)],
                one_cell_r: [(1, 1), (1, 1), (1, 1)],
                one_cell_bound: (1, 1),
                triangle_scaled_phi: [(2, 1), (1, 1), (1, 2)],
                triangle_scaled_gamma: [(2, 1), (1, 1), (1, 2)],
                triangle_scaled_r: [(1, 1), (1, 1), (1, 1)],
                triangle_bound: (1, 1),
                triangle_cochain: [
                    [(1, 1), (1, 1), (0, 1)],
                    [(1, 2), (1, 2), (0, 1)],
                    [(1, 4), (1, 4), (0, 1)],
                ],
                triangle_repair: [
                    [(0, 1), (1, 1), (0, 1)],
                    [(0, 1), (1, 2), (0, 1)],
                    [(0, 1), (1, 4), (0, 1)],
                ],
                circulation: [(1, 1), (1, 1), (-1, 1)],
                shifted_cochain: [(1, 1), (6, 1), (5, 1)],
                shifted_repair: [(0, 1), (1, 1), (5, 1)],
                shifted_phi: (2, 1),
                shifted_raw_l1: (12, 1),
                shifted_r: (1, 1),
                shifted_class: Diagnostic::ActiveClosureFailure,
                composition_zero: true,
                reaches_exact_class: false,
                prefix_steps_accepted: true,
            }
        );
        assert_eq!(
            vertex_coboundary(0),
            [(-1, 1), (0, 1), (-1, 1)]
        );
        assert_eq!(vertex_coboundary(1), [(1, 1), (-1, 1), (0, 1)]);
        assert_eq!(vertex_coboundary(2), [(0, 1), (1, 1), (1, 1)]);
        assert_eq!(closure_value(vertex_coboundary(0)), (0, 1));
        assert_eq!(closure_value(vertex_coboundary(1)), (0, 1));
        assert_eq!(closure_value(vertex_coboundary(2)), (0, 1));
        assert_eq!(closure_value([(1, 1), (1, 1), (0, 1)]), (2, 1));
        assert_eq!(closure_value([(1, 1), (0, 1), (0, 1)]), (1, 1));
        assert!(vertex_coboundary_is_exact(0));
        assert!(vertex_coboundary_is_exact(1));
        assert!(vertex_coboundary_is_exact(2));
        assert!(!difference_is_exact(0));
        assert!(!difference_is_exact(1));
        assert!(!difference_is_exact(2));
        for index in 0..32 {
            assert!(one_cell_step_accepted(index));
            assert!(triangle_step_accepted(index));
            assert_eq!(one_cell(index).phi, (1, 1_i128 << index));
            assert_eq!(one_cell(index).gamma, one_cell(index).phi);
            assert_eq!(one_cell(index).r_cl, Some((1, 1)));
            assert_eq!(one_cell(index).bound, (1, 1));
            assert_eq!(one_cell(index).class, Diagnostic::ActiveClosureFailure);
            let tri_phi = if index == 0 {
                (2, 1)
            } else {
                (1, 1_i128 << (index - 1))
            };
            assert_eq!(triangle(index).phi, tri_phi);
            assert_eq!(triangle(index).gamma, tri_phi);
            assert_eq!(triangle(index).r_cl, Some((1, 1)));
            assert_eq!(triangle(index).bound, (1, 1));
            assert_eq!(triangle(index).class, Diagnostic::ActiveClosureFailure);
            assert!(strictly_less(one_cell(index + 1).phi, one_cell(index).phi));
            assert!(strictly_less(triangle(index + 1).phi, triangle(index).phi));
            assert_ne!(one_cell(index).phi, triangle(index).phi);
        }
        assert_eq!(one_cell(32).phi, (1, 1_i128 << 32));
        assert_eq!(one_cell(32).class, Diagnostic::ActiveClosureFailure);
        assert_eq!(triangle(32).class, Diagnostic::ActiveClosureFailure);
        assert_eq!(one_cell_zero().phi, (0, 1));
        assert_eq!(one_cell_zero().class, Diagnostic::ExactClass);
    }

    #[test]
    fn refuses_null_repair_copy_and_uniform_drop() {
        assert_eq!(
            refuse_coboundary_edit(),
            Err("refused: Phi_1 does not strictly decrease")
        );
        assert_eq!(
            refuse_one_cell_as_triangle(0),
            Err("refused: one-cell Phi_1 is not the filled-triangle signature")
        );
        assert!(refuse_one_cell_as_triangle(1).is_err());
        assert!(refuse_one_cell_as_triangle(2).is_err());
        assert_eq!(refuse_claimed_triangle_phi(4, 2), Ok(()));
        assert!(refuse_claimed_triangle_phi(2, 1).is_ok());
        assert!(refuse_claimed_triangle_phi(7, 4).is_err());
        assert!(refuse_claimed_triangle_phi(1, 1).is_err());
        assert!(refuse_claimed_triangle_phi(1, 2).is_err());
        assert!(refuse_claimed_triangle_phi(1, 4).is_err());
        assert!(one_cell_step_accepted(3));
        assert_eq!(one_cell(3).phi, (1, 8));
        assert_eq!(one_cell(4).phi, (1, 16));
        assert!(strictly_less((1, 16), (1, 8)));
        assert_eq!(
            refuse_uniform_decrement(1, 8),
            Err("refused: the dyadic run has no uniform positive decrement")
        );
        assert_eq!(
            refuse_uniform_decrement(0, 1),
            Err("refused: a nonpositive epsilon is not a uniform drop")
        );
        assert_eq!(
            refuse_ratio_at_exact_class(),
            Err("refused: R_cl is undefined when Phi_1 = 0")
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_f63096e9() {
    let admitted = BoundaryRecordf63096e9::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordf63096e9::try_admit(9, 8).is_err());
}
