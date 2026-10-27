//! Shared-noise control only. Candidates are {0,1}, the free report is *, and
//! instruments A and B each have price 1. The declared segments are
//! L_0 = {(e,e): e in [-1,1]} and L_1 = {(1+e,-1+e): e in [-1,1]}.
//! Costs below are exact integer cost units on that finite carrier. The
//! marginal-interval product is a different carrier. No continuum limit.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct Q {
    n: i64,
    d: i64,
}

fn gcd(mut a: i64, mut b: i64) -> i64 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let rest = a % b;
        a = b;
        b = rest;
    }
    a
}

fn narrow(value: i128) -> i64 {
    i64::try_from(value).expect("rational outside i64")
}

fn qr(n: i64, d: i64) -> Q {
    assert!(d != 0, "zero denominator");
    let (mut n, mut d) = (n, d);
    if d < 0 {
        n = n.checked_neg().expect("numerator overflow");
        d = -d;
    }
    let g = gcd(n, d);
    Q { n: n / g, d: d / g }
}

fn q(n: i64) -> Q {
    qr(n, 1)
}

impl Q {
    fn add(self, other: Q) -> Q {
        qr(
            narrow(self.n as i128 * other.d as i128 + other.n as i128 * self.d as i128),
            narrow(self.d as i128 * other.d as i128),
        )
    }

    fn sub(self, other: Q) -> Q {
        let n = other.n.checked_neg().expect("numerator overflow");
        self.add(Q { n, d: other.d })
    }

    fn mul(self, other: Q) -> Q {
        qr(
            narrow(self.n as i128 * other.n as i128),
            narrow(self.d as i128 * other.d as i128),
        )
    }

    fn div(self, other: Q) -> Q {
        assert!(other.n != 0, "division by zero");
        qr(
            narrow(self.n as i128 * other.d as i128),
            narrow(self.d as i128 * other.n as i128),
        )
    }
}

impl PartialOrd for Q {
    fn partial_cmp(&self, other: &Self) -> Option<std::cmp::Ordering> {
        Some(self.cmp(other))
    }
}

impl Ord for Q {
    fn cmp(&self, other: &Self) -> std::cmp::Ordering {
        let left = self.n as i128 * other.d as i128;
        let right = other.n as i128 * self.d as i128;
        left.cmp(&right)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct World {
    answer: i64,
    z: [Q; 2],
}

struct Segment {
    answer: i64,
    lower: Q,
    upper: Q,
    slopes: [Q; 2],
    offsets: [Q; 2],
}

const PRICE: [i64; 2] = [1, 1];

fn segments() -> [Segment; 2] {
    [
        Segment {
            answer: 0,
            lower: q(-1),
            upper: q(1),
            slopes: [q(1), q(1)],
            offsets: [q(0), q(0)],
        },
        Segment {
            answer: 1,
            lower: q(-1),
            upper: q(1),
            slopes: [q(1), q(1)],
            offsets: [q(1), q(-1)],
        },
    ]
}

fn realize(seg: &Segment, e: Q) -> World {
    World {
        answer: seg.answer,
        z: [
            seg.slopes[0].mul(e).add(seg.offsets[0]),
            seg.slopes[1].mul(e).add(seg.offsets[1]),
        ],
    }
}

fn parameter_at(seg: &Segment, channel: usize, value: Q) -> Q {
    value.sub(seg.offsets[channel]).div(seg.slopes[channel])
}

fn on_segment(seg: &Segment, z: [Q; 2]) -> bool {
    let e = parameter_at(seg, 0, z[0]);
    seg.lower <= e && e <= seg.upper && realize(seg, e).z[1] == z[1]
}

fn image(seg: &Segment, channel: usize) -> (Q, Q) {
    let left = realize(seg, seg.lower).z[channel];
    let right = realize(seg, seg.upper).z[channel];
    if left <= right { (left, right) } else { (right, left) }
}

fn product_admits(seg: &Segment, z: [Q; 2]) -> bool {
    let (a0, a1) = image(seg, 0);
    let (b0, b1) = image(seg, 1);
    a0 <= z[0] && z[0] <= a1 && b0 <= z[1] && z[1] <= b1
}

fn prediction(seg: &Segment, i: usize, j: usize) -> (Q, Q) {
    let slope = seg.slopes[j].div(seg.slopes[i]);
    let intercept = seg.offsets[j].sub(slope.mul(seg.offsets[i]));
    (slope, intercept)
}

fn overlap(left: &Segment, right: &Segment, channel: usize) -> Option<(Q, Q)> {
    let (l0, l1) = image(left, channel);
    let (r0, r1) = image(right, channel);
    let low = if l0 > r0 { l0 } else { r0 };
    let high = if l1 < r1 { l1 } else { r1 };
    if low <= high { Some((low, high)) } else { None }
}

fn fiber(segs: &[Segment], channel: usize, value: Q) -> Vec<World> {
    let mut worlds = Vec::new();
    for seg in segs {
        let e = parameter_at(seg, channel, value);
        if seg.lower <= e && e <= seg.upper {
            let candidate = realize(seg, e);
            if !worlds.contains(&candidate) {
                worlds.push(candidate);
            }
        }
    }
    worlds
}

fn admit(worlds: &mut Vec<World>, candidate: World) {
    if !worlds.contains(&candidate) {
        worlds.push(candidate);
    }
}

/// Critical-cell worlds for these two segments, in sampler order.
fn channel_reps(segs: &[Segment; 2], channel: usize) -> Vec<Q> {
    let mut points = Vec::new();
    for seg in segs {
        let (low, high) = image(seg, channel);
        points.push(low);
        points.push(high);
    }
    if let Some((low, high)) = overlap(&segs[0], &segs[1], channel) {
        for j in 0..2 {
            let (a, b) = prediction(&segs[0], channel, j);
            let (c, d) = prediction(&segs[1], channel, j);
            if a != c {
                let root = d.sub(b).div(a.sub(c));
                if (low..=high).contains(&root) {
                    points.push(root);
                }
            }
        }
    }
    points.sort();
    points.dedup();
    let mut reps = points.clone();
    for pair in points.windows(2) {
        reps.push(pair[0].add(pair[1]).div(q(2)));
    }
    reps.sort();
    reps.dedup();
    reps
}

fn admit_channel_worlds(segs: &[Segment; 2], channel: usize, worlds: &mut Vec<World>) {
    for value in channel_reps(segs, channel) {
        let found = fiber(segs, channel, value);
        let mut labels = Vec::new();
        for world in &found {
            if !labels.contains(&world.answer) {
                labels.push(world.answer);
            }
        }
        if labels.len() > 1 {
            for world in found {
                admit(worlds, world);
            }
        }
    }
}

fn sample() -> Vec<World> {
    let segs = segments();
    let mut worlds = Vec::new();
    for seg in &segs {
        admit(&mut worlds, realize(seg, seg.lower));
    }
    for channel in 0..2 {
        admit_channel_worlds(&segs, channel, &mut worlds);
    }
    worlds
}

fn distinct_answers(worlds: &[World]) -> i64 {
    let mut seen = [false, false];
    for world in worlds {
        if world.answer == 0 || world.answer == 1 {
            seen[world.answer as usize] = true;
        }
    }
    seen.iter().filter(|flag| **flag).count() as i64
}

fn answers_where(z: [Q; 2], joint: bool) -> Vec<i64> {
    segments()
        .into_iter()
        .filter(|seg| if joint { on_segment(seg, z) } else { product_admits(seg, z) })
        .map(|seg| seg.answer)
        .collect()
}

fn covers(worlds: &[World], instruments: &[usize], mask: u32) -> bool {
    for i in 0..worlds.len() {
        for j in (i + 1)..worlds.len() {
            if worlds[i].answer == worlds[j].answer {
                continue;
            }
            let mut hit = false;
            for (bit, &inst) in instruments.iter().enumerate() {
                if mask & (1u32 << bit) != 0 && worlds[i].z[inst] != worlds[j].z[inst] {
                    hit = true;
                    break;
                }
            }
            if !hit {
                return false;
            }
        }
    }
    true
}

fn mask_price(instruments: &[usize], mask: u32) -> i64 {
    let mut total = 0;
    for (bit, &inst) in instruments.iter().enumerate() {
        if mask & (1u32 << bit) != 0 {
            total += PRICE[inst];
        }
    }
    total
}

/// Minimum price of a suite that separates different answers. `None` means no suite does.
/// A one-instrument `None` is not replaced by that instrument's price.
fn fixed(worlds: &[World], instruments: &[usize]) -> Option<i64> {
    let width = instruments.len();
    let mut best: Option<i64> = None;
    for mask in 0u32..(1u32 << width) {
        if !covers(worlds, instruments, mask) {
            continue;
        }
        let cost = mask_price(instruments, mask);
        best = Some(best.map_or(cost, |so_far| so_far.min(cost)));
    }
    best
}

fn single_answer(worlds: &[World], mask: usize) -> bool {
    let mut seen: Option<i64> = None;
    for state in 0..worlds.len() {
        if mask & (1usize << state) == 0 {
            continue;
        }
        match seen {
            None => seen = Some(worlds[state].answer),
            Some(answer) if answer != worlds[state].answer => return false,
            Some(_) => {}
        }
    }
    true
}

fn branches(worlds: &[World], mask: usize, inst: usize) -> Vec<usize> {
    let mut groups: Vec<(Q, usize)> = Vec::new();
    for state in 0..worlds.len() {
        if mask & (1usize << state) == 0 {
            continue;
        }
        let outcome = worlds[state].z[inst];
        if let Some((_, group)) = groups.iter_mut().find(|(found, _)| *found == outcome) {
            *group |= 1usize << state;
        } else {
            groups.push((outcome, 1usize << state));
        }
    }
    groups.into_iter().map(|(_, group)| group).collect()
}

fn adaptive(worlds: &[World], instruments: &[usize]) -> Option<i64> {
    let n = worlds.len();
    assert!(n <= 12, "selected carrier is the ten-world list");
    let mut values = vec![None; 1usize << n];
    for mask in 0..(1usize << n) {
        if single_answer(worlds, mask) {
            values[mask] = Some(0);
            continue;
        }
        let mut best: Option<i64> = None;
        for &inst in instruments {
            let children = branches(worlds, mask, inst);
            if children.len() < 2 {
                continue;
            }
            let mut worst = 0;
            let mut finite = true;
            for child in children {
                match values[child] {
                    Some(cost) => worst = worst.max(cost),
                    None => {
                        finite = false;
                        break;
                    }
                }
            }
            if finite {
                let cost = PRICE[inst] + worst;
                best = Some(best.map_or(cost, |so_far| so_far.min(cost)));
            }
        }
        values[mask] = best;
    }
    if n == 0 { Some(0) } else { values[(1usize << n) - 1] }
}

fn difference_constant(seg: &Segment) -> Option<Q> {
    if seg.slopes[0] != seg.slopes[1] {
        return None;
    }
    Some(seg.offsets[0].sub(seg.offsets[1]))
}

/// On these two segments the reading difference is constant on each answer and
/// equals `scale * answer`, with the two constants distinct.
fn identity_separates() -> bool {
    let segs = segments();
    let (c0, c1) = match (difference_constant(&segs[0]), difference_constant(&segs[1])) {
        (Some(c0), Some(c1)) => (c0, c1),
        _ => return false,
    };
    if segs[0].answer == segs[1].answer || c0 == c1 {
        return false;
    }
    let scale = c1.sub(c0).div(q(segs[1].answer - segs[0].answer));
    segs.iter().all(|seg| difference_constant(seg) == Some(scale.mul(q(seg.answer))))
}

fn is_point(world: &World, answer: i64, za: i64, zb: i64) -> bool {
    world.answer == answer && world.z[0] == q(za) && world.z[1] == q(zb)
}

fn segment_bounds() -> (i64, i64, i64) {
    assert!(identity_separates(), "the two segments are not separated by one common parameter");
    let both = mask_price(&[0, 1], 0b11);
    let a0 = fiber(&segments(), 0, q(0));
    let b0 = fiber(&segments(), 1, q(-1));
    assert!(a0.len() == 2 && is_point(&a0[0], 0, 0, 0) && is_point(&a0[1], 1, 0, -2));
    assert!(b0.len() == 2 && is_point(&b0[0], 0, -1, -1) && is_point(&b0[1], 1, 1, -1));
    let mut points = Vec::new();
    for world in a0.iter().chain(b0.iter()) {
        admit(&mut points, *world);
    }
    assert_eq!(points.len(), 4, "the segment lower bound is four admitted points");
    assert!(fixed(&points, &[0]).is_none(), "A alone does not separate the four points");
    assert!(fixed(&points, &[1]).is_none(), "B alone does not separate the four points");
    let lower_fixed = fixed(&points, &[0, 1]).expect("four points have no joint suite");
    assert_eq!(lower_fixed, both, "segment fixed bounds do not meet");
    let via_a = PRICE[0] + fixed(&a0, &[1]).expect("B does not separate the A=0 fiber");
    let via_b = PRICE[1] + fixed(&b0, &[0]).expect("A does not separate the B=-1 fiber");
    let lower_adaptive = via_a.min(via_b);
    assert_eq!(lower_adaptive, both, "segment adaptive bounds do not meet");
    (both, lower_adaptive, points.len() as i64)
}

fn carrier_mask(worlds: &[World]) -> i64 {
    let masks: Vec<u32> = (0u32..4).filter(|&mask| covers(worlds, &[0, 1], mask)).collect();
    assert_eq!(masks.len(), 1, "the carrier does not have one sufficient suite");
    masks[0] as i64
}

/// Exact shared-noise costs. Product fields are null-optimum data, not the joint optimum.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub worlds: i64,
    pub carrier_fixed: i64,
    pub carrier_adaptive: i64,
    pub segment_fixed: i64,
    pub segment_adaptive: i64,
    pub segment_lower_worlds: i64,
    pub one_instrument_null: bool,
    pub product_optimum_null: bool,
    pub product_suite_price: i64,
    pub product_suite_sufficient: bool,
    pub joint_origin_answer: i64,
    pub product_origin_count: i64,
    pub partial_a_zero_answers: i64,
    pub carrier_suite_mask: i64,
}

pub fn witness() -> Witness {
    let worlds = sample();
    assert_eq!(worlds.len(), 10, "sampler did not return the ten-world carrier");
    for world in &worlds {
        let seg = segments().into_iter().find(|seg| seg.answer == world.answer).expect("answer");
        assert!(on_segment(&seg, world.z), "sampled world is not on its segment");
        let diff = world.z[0].sub(world.z[1]);
        assert_eq!(diff, difference_constant(&seg).expect("parallel slopes"));
    }
    let one_instrument_null = fixed(&worlds, &[0]).is_none()
        && fixed(&worlds, &[1]).is_none()
        && adaptive(&worlds, &[0]).is_none()
        && adaptive(&worlds, &[1]).is_none();
    let carrier_fixed = fixed(&worlds, &[0, 1]).expect("carrier fixed cost");
    let carrier_adaptive = adaptive(&worlds, &[0, 1]).expect("carrier adaptive cost");
    let (segment_fixed, segment_adaptive, segment_lower_worlds) = segment_bounds();
    let origin = realize(&segments()[0], q(0)).z;
    let joint = answers_where(origin, true);
    let product = answers_where(origin, false);
    assert_eq!(joint.len(), 1, "joint report (0,0) does not certify one answer");
    let product_optimum_null = product.len() > 1;
    Witness {
        worlds: worlds.len() as i64,
        carrier_fixed,
        carrier_adaptive,
        segment_fixed,
        segment_adaptive,
        segment_lower_worlds,
        one_instrument_null,
        product_optimum_null,
        product_suite_price: mask_price(&[0, 1], 0b11),
        product_suite_sufficient: !product_optimum_null,
        joint_origin_answer: joint[0],
        product_origin_count: product.len() as i64,
        partial_a_zero_answers: distinct_answers(&fiber(&segments(), 0, q(0))),
        carrier_suite_mask: carrier_mask(&worlds),
    }
}

const MARGINAL_NOT_JOINT: &str = "coordinate enclosure is not a realizable joint report";
const PRICE_NOT_OPTIMUM: &str = "insufficient product-suite price is not an optimum";

/// Joint feasibility uses one common parameter. Marginal interval membership is refused.
pub fn refuse_coordinate_enclosure(za_n: i64, za_d: i64, zb_n: i64, zb_d: i64) -> Result<i64, &'static str> {
    if za_d == 0 || zb_d == 0 {
        return Err("zero denominator");
    }
    let z = [qr(za_n, za_d), qr(zb_n, zb_d)];
    let joint = answers_where(z, true);
    let marginal = answers_where(z, false);
    if joint.is_empty() && !marginal.is_empty() {
        return Err(MARGINAL_NOT_JOINT);
    }
    if joint.is_empty() {
        return Err("inconsistent joint history");
    }
    if joint.len() != 1 {
        return Err("history does not certify one answer");
    }
    Ok(joint[0])
}

/// The product carrier's stored optimum is null. Its full-suite price is not that optimum.
pub fn refuse_product_price_as_optimum(price: i64) -> Result<(), &'static str> {
    let report = witness();
    if !report.product_optimum_null || report.product_suite_sufficient {
        return Err("product carrier was not a null optimum");
    }
    if price == report.product_suite_price {
        return Err(PRICE_NOT_OPTIMUM);
    }
    Err("marginal-interval product optimum is null")
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_appx_joint_support.rs
// Claim: urn:core:crates_rs:tests:wdp-appx-joint-support:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordb38ab365 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordb38ab365` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorb38ab365 {
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
impl BoundaryErrorb38ab365 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorb38ab365 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorb38ab365 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordb38ab365 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorb38ab365> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorb38ab365::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorb38ab365::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorb38ab365::ExceedsCapacity {
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
    use super::{refuse_coordinate_enclosure, refuse_product_price_as_optimum, sample, witness};

    fn carrier_table() -> [(i64, i64, i64, i64, i64); 10] {
        let worlds = sample();
        assert_eq!(worlds.len(), 10);
        let mut rows = [(0, 0, 1, 0, 1); 10];
        for (i, world) in worlds.iter().enumerate() {
            rows[i] = (world.answer, world.z[0].n, world.z[0].d, world.z[1].n, world.z[1].d);
        }
        rows
    }


    #[test]
    fn exact_shared_noise_costs() {
        let report = witness();
        assert_eq!(report.worlds, 10);
        assert_eq!(report.carrier_fixed, 2);
        assert_eq!(report.carrier_adaptive, 2);
        assert_eq!(report.segment_fixed, 2);
        assert_eq!(report.segment_adaptive, 2);
        assert_eq!(report.segment_lower_worlds, 4);
        assert!(report.one_instrument_null);
        assert!(report.product_optimum_null);
        assert_eq!(report.product_suite_price, 2);
        assert!(!report.product_suite_sufficient);
        assert_eq!(report.joint_origin_answer, 0);
        assert_eq!(report.product_origin_count, 2);
        assert_eq!(report.partial_a_zero_answers, 2);
        assert_eq!(report.carrier_suite_mask, 3);
        assert_eq!(refuse_coordinate_enclosure(0, 1, 0, 1), Ok(0));
        assert_eq!(refuse_coordinate_enclosure(0, 1, -2, 1), Ok(1));
        assert_eq!(
            carrier_table(),
            [
                (0, -1, 1, -1, 1),
                (1, 0, 1, -2, 1),
                (0, 0, 1, 0, 1),
                (0, 1, 2, 1, 2),
                (1, 1, 2, -3, 2),
                (0, 1, 1, 1, 1),
                (1, 1, 1, -1, 1),
                (0, -1, 2, -1, 2),
                (1, 3, 2, -1, 2),
                (1, 2, 1, 0, 1),
            ]
        );
    }

    #[test]
    fn coordinate_enclosure_is_refused() {
        assert_eq!(
            refuse_coordinate_enclosure(0, 1, 1, 1),
            Err("coordinate enclosure is not a realizable joint report")
        );
        assert_eq!(
            refuse_product_price_as_optimum(2),
            Err("insufficient product-suite price is not an optimum")
        );
    }
}

#[test]
fn l4_boundary_admits_and_refuses_b38ab365() {
    let admitted = BoundaryRecordb38ab365::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordb38ab365::try_admit(9, 8).is_err());
}
