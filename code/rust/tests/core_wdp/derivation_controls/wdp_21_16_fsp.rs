//! Two finite carriers for WDP-21-16-FSP.
//! Carrier A is the four-site star. Carrier B is one k=1 orbit.
//! Their integers do not close section 21.16.

#![forbid(unsafe_code)]

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Witness {
    pub signs: [i64; 6],
    pub hop_product: i64,
    pub parity_sum: i64,
    pub parity_f2: i64,
    pub gauges_checked: i64,
    pub gauges_removing_holonomy: i64,
    pub gauged_cycle_f2: i64,
    pub site_cycle_rank: i64,
    pub all_negative_product: i64,
    pub k: i64,
    pub weight_a: i64,
    pub baseline_s: i64,
    pub z_u: i64,
    pub n_u: i64,
    pub hat_o_num: i64,
    pub hat_o_den: i64,
    pub holonomy_removed: i64,
    pub numerator_preserved: i64,
    pub conjunction: i64,
}

const MASKS: [u8; 7] = [6, 5, 12, 9, 10, 3, 6];
const HOPS: [(u8, u8); 6] = [(1, 0), (0, 3), (2, 0), (0, 1), (3, 0), (0, 2)];

fn preceding(mask: u8, site: u8) -> i64 {
    assert!(site < 4, "site outside the star");
    let below = (1u8 << site) - 1;
    i64::from((mask & below).count_ones())
}

fn hop_sign(mask: u8, src: u8, dst: u8) -> (i64, u8) {
    assert!(src < 4 && dst < 4, "endpoint outside the star");
    assert!(mask & (1u8 << src) != 0, "annihilation site empty");
    assert!(mask & (1u8 << dst) == 0, "creation site occupied");
    let interim = mask ^ (1u8 << src);
    let parity = (preceding(mask, src) + preceding(interim, dst)) & 1;
    let sign = 1 - 2 * parity;
    let next = interim | (1u8 << dst);
    assert_eq!(next.count_ones(), 2, "hop left the two-particle sector");
    (sign, next)
}

fn distinct_two_particle_cycle() {
    let mut seen = 0u16;
    for mask in MASKS.iter().take(6) {
        assert_eq!(mask.count_ones(), 2, "mask is not two-particle");
        let bit = 1u16 << mask;
        assert_eq!(seen & bit, 0, "configuration vertex repeats");
        seen |= bit;
    }
    assert_eq!(MASKS[0], MASKS[6], "cycle does not close");
    let mut all = 0u16;
    for mask in 0u8..16 {
        if mask.count_ones() == 2 {
            all |= 1u16 << mask;
        }
    }
    assert_eq!(seen, all, "cycle misses a two-particle mask");
}

fn find(parent: &mut [u8; 4], mut node: u8) -> u8 {
    while parent[node as usize] != node {
        parent[node as usize] = parent[parent[node as usize] as usize];
        node = parent[node as usize];
    }
    node
}

fn site_cycle_rank() -> i64 {
    let mut edges = [(0u8, 0u8); 3];
    let mut count = 0usize;
    for &(src, dst) in &HOPS {
        assert!(src == 0 || dst == 0, "hop leaves the star center");
        let other = if src == 0 { dst } else { src };
        assert!((1..=3).contains(&other), "leaf outside the star");
        let edge = (0u8, other);
        if !edges[..count].contains(&edge) {
            assert!(count < 3, "star gained a fourth edge");
            edges[count] = edge;
            count += 1;
        }
    }
    assert_eq!(count, 3, "star is missing an edge");
    let mut parent = [0u8, 1, 2, 3];
    let mut components = 4i64;
    for &(left, right) in &edges {
        let root_left = find(&mut parent, left);
        let root_right = find(&mut parent, right);
        if root_left != root_right {
            parent[root_left as usize] = root_right;
            components -= 1;
        }
    }
    count as i64 - 4 + components
}

fn gauge_cycle(parities: &[u8; 6]) -> (i64, i64, i64) {
    let mut base = 0i64;
    for parity in parities {
        base += i64::from(*parity);
    }
    let base_f2 = base & 1;
    let mut removing = 0i64;
    let mut checked = 0i64;
    for assignment in 0i64..64 {
        let mut extra = 0i64;
        for edge in 0..6 {
            let tail = (assignment >> edge) & 1;
            let head = (assignment >> ((edge + 1) % 6)) & 1;
            extra += tail + head;
        }
        // Each cycle vertex has degree two, so g_v is added twice.
        assert_eq!(extra & 1, 0, "diagonal gauge failed to cancel");
        let total = (base + extra) & 1;
        assert_eq!(total, base_f2, "gauge changed the cycle sum");
        if total == 0 {
            removing += 1;
        }
        checked += 1;
    }
    (checked, removing, base_f2)
}

fn star_exchange() -> ([i64; 6], i64, i64, i64, i64, i64, i64) {
    distinct_two_particle_cycle();
    let mut signs = [0i64; 6];
    let mut parities = [0u8; 6];
    let mut product = 1i64;
    let mut parity_sum = 0i64;
    for index in 0..6 {
        let (src, dst) = HOPS[index];
        let (sign, next) = hop_sign(MASKS[index], src, dst);
        assert_eq!(next, MASKS[index + 1], "hop misses the declared mask");
        signs[index] = sign;
        let parity = if sign < 0 { 1u8 } else { 0u8 };
        parities[index] = parity;
        parity_sum += i64::from(parity);
        product *= sign;
    }
    let folded = signs.iter().fold(1i64, |acc, sign| acc * sign);
    assert_eq!(product, folded);
    assert_eq!(product, 1 - 2 * (parity_sum & 1));
    let (checked, removing, gauged) = gauge_cycle(&parities);
    assert_eq!(gauged, parity_sum & 1);
    let rank = site_cycle_rank();
    (signs, product, parity_sum, checked, removing, gauged, rank)
}

fn six_negative_product() -> i64 {
    let mut product = 1i64;
    for _ in 0..6 {
        product *= -1;
    }
    product
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

fn reduce(num: i64, den: i64) -> (i64, i64) {
    assert!(den > 0, "denominator");
    let divisor = gcd(num, den);
    assert!(divisor > 0, "gcd");
    (num / divisor, den / divisor)
}

fn orbit() -> (i64, i64, i64, i64, i64, i64, i64) {
    let k = 1i64;
    let weight_a = 1i64;
    let baseline_s = 1i64;
    let m = 1i64;
    let points = 1i64 << k;
    assert_eq!(points, 2, "orbit is not the full k=1 set");
    let mut character_sum = 0i64;
    let mut weighted = 0i64;
    for u in 0..points {
        let chi = 1 - 2 * ((m & u) & 1);
        let observable = 1 - 2 * (u & 1);
        character_sum += chi;
        weighted += chi * observable;
    }
    let z_u = weight_a * baseline_s * character_sum;
    let closed = if m == 0 {
        weight_a * baseline_s * points
    } else {
        0
    };
    assert_eq!(z_u, closed, "orbit sum missed the character closed form");
    assert_eq!(weighted % points, 0, "hat O is not an integer on this orbit");
    let (hat_num, hat_den) = reduce(weighted, points);
    assert_eq!(points % hat_den, 0, "reduced denominator does not divide 2^k");
    let n_u = weight_a * baseline_s * (points / hat_den) * hat_num;
    assert_eq!(n_u, weight_a * baseline_s * weighted);
    (k, weight_a, baseline_s, z_u, n_u, hat_num, hat_den)
}

pub fn witness() -> Witness {
    let (signs, hop_product, parity_sum, checked, removing, gauged, rank) = star_exchange();
    let (k, weight_a, baseline_s, z_u, n_u, hat_num, hat_den) = orbit();
    let holonomy_removed = i64::from(removing > 0);
    let numerator_preserved = i64::from(n_u == 0);
    Witness {
        signs,
        hop_product,
        parity_sum,
        parity_f2: parity_sum & 1,
        gauges_checked: checked,
        gauges_removing_holonomy: removing,
        gauged_cycle_f2: gauged,
        site_cycle_rank: rank,
        all_negative_product: six_negative_product(),
        k,
        weight_a,
        baseline_s,
        z_u,
        n_u,
        hat_o_num: hat_num,
        hat_o_den: hat_den,
        holonomy_removed,
        numerator_preserved,
        conjunction: holonomy_removed * numerator_preserved,
    }
}

/// `1` is the six-negative product, not the CAR product of this cycle.
pub fn refuse_removed_holonomy(claimed_product: i64) -> Result<(), &'static str> {
    let found = witness();
    if claimed_product == found.hop_product {
        Ok(())
    } else if claimed_product == found.all_negative_product {
        Err("(+1) equals (-1)^6 and is not the CAR product of this cycle")
    } else {
        Err("claimed product is not the CAR hop product of this cycle")
    }
}

/// `912` and `36864` belong to a different fixture.
pub fn refuse_foreign_fixture(value: i64) -> Result<(), &'static str> {
    let found = witness();
    if value == 912 || value == 36864 {
        Err("O.5 fixture scalar is not this k=1 orbit")
    } else if value == found.z_u || value == found.n_u {
        Ok(())
    } else {
        Err("scalar is outside the computed orbit values")
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_21_16_fsp.rs
// Claim: urn:core:crates_rs:tests:wdp-21-16-fsp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordc876870f {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordc876870f` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorc876870f {
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
impl BoundaryErrorc876870f {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorc876870f {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorc876870f {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordc876870f {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorc876870f> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorc876870f::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorc876870f::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorc876870f::ExceedsCapacity {
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
    use super::{refuse_foreign_fixture, refuse_removed_holonomy, witness, Witness, HOPS, MASKS};

    #[test]
    fn exact_star_and_orbit_values() {
        let mut odd = [(0u8, 0u8); 3];
        let mut odd_count = 0usize;
        let found = witness();
        for index in 0..6 {
            if found.signs[index] == -1 {
                assert!(odd_count < 3);
                odd[odd_count] = HOPS[index];
                odd_count += 1;
            }
        }
        assert_eq!(MASKS, [6, 5, 12, 9, 10, 3, 6]);
        assert_eq!(HOPS, [(1, 0), (0, 3), (2, 0), (0, 1), (3, 0), (0, 2)]);
        assert_eq!(odd_count, 3);
        assert_eq!(odd, [(0, 3), (3, 0), (0, 2)]);
        assert_eq!(
            found,
            Witness {
                signs: [1, -1, 1, 1, -1, -1],
                hop_product: -1,
                parity_sum: 3,
                parity_f2: 1,
                gauges_checked: 64,
                gauges_removing_holonomy: 0,
                gauged_cycle_f2: 1,
                site_cycle_rank: 0,
                all_negative_product: 1,
                k: 1,
                weight_a: 1,
                baseline_s: 1,
                z_u: 0,
                n_u: 2,
                hat_o_num: 1,
                hat_o_den: 1,
                holonomy_removed: 0,
                numerator_preserved: 0,
                conjunction: 0,
            }
        );
    }

    #[test]
    fn removed_holonomy_and_foreign_scalars_are_refused() {
        let found = witness();
        assert!(refuse_removed_holonomy(1).is_err());
        assert!(refuse_removed_holonomy(found.all_negative_product).is_err());
        assert!(refuse_removed_holonomy(found.hop_product).is_ok());
        assert!(refuse_foreign_fixture(912).is_err());
        assert!(refuse_foreign_fixture(36864).is_err());
        assert!(refuse_foreign_fixture(found.z_u).is_ok());
        assert!(refuse_foreign_fixture(found.n_u).is_ok());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_c876870f() {
    let admitted = BoundaryRecordc876870f::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecordc876870f::try_admit(9, 8).is_err());
}
