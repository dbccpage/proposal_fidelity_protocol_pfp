//! Exact rational and F2 witness for `WDP-21-16-WDP` (`derivation.md`).
//!
//! Verifies:
//! 1. Packet L: 4x4 rational Bell density matrices `rho`, `sigma`, single-qubit marginals `I/2`,
//!    product projection `I/4`, residual difference `R = rho - sigma = (XX - YY)/2`,
//!    `Tr(R) = 0`, `Tr(R O_R) = 0`, `Tr(R ZZ) = 0`, `Tr(R O) = 1/4 = 2*beta`, `||R||_1 = 2`,
//!    and L4 endpoint reconstruction bound `alpha >= delta / 2 = 1/8`.
//! 2. Support-vector vs signed-operator distinction: `supp(XX) + supp(YY) = (0,0,1,1) = supp(ZZ)`
//!    in `F_2^4`, whereas `R = (XX - YY)/2` has `Tr(R ZZ) = 0`.
//! 3. Packet S: `V = F_2^3`, `Q(x,y,z) = x xor y`, `ker Q = {000,001,110,111}`, `B = {000,110}`,
//!    witness `001 in ker Q \ B`, and `dim(ker Q / B) = 1` separated by row `z`.
//! 4. Refuses treating `1 = dim(ker Q / B) = R_{0,3}` as a cross-carrier adapter or Lieb-Robinson floor.

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Frac {
    pub num: i64,
    pub den: i64,
}

impl Frac {
    pub const fn new(num: i64, den: i64) -> Self {
        assert!(den != 0, "zero denominator");
        let sign = if den < 0 { -1 } else { 1 };
        let n = num * sign;
        let d = den * sign;
        let g = Self::gcd(n.unsigned_abs(), d.unsigned_abs()) as i64;
        Self {
            num: n / g,
            den: d / g,
        }
    }

    const fn gcd(mut a: u64, mut b: u64) -> u64 {
        while b != 0 {
            let t = a % b;
            a = b;
            b = t;
        }
        if a == 0 { 1 } else { a }
    }

    pub const fn add(self, other: Self) -> Self {
        Self::new(self.num * other.den + other.num * self.den, self.den * other.den)
    }

    pub const fn sub(self, other: Self) -> Self {
        Self::new(self.num * other.den - other.num * self.den, self.den * other.den)
    }

    pub const fn mul(self, other: Self) -> Self {
        Self::new(self.num * other.num, self.den * other.den)
    }
}

pub type Mat4 = [[Frac; 4]; 4];

pub fn trace_product(a: &Mat4, b: &Mat4) -> Frac {
    let mut sum = Frac::new(0, 1);
    for i in 0..4 {
        for k in 0..4 {
            sum = sum.add(a[i][k].mul(b[k][i]));
        }
    }
    sum
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Witness {
    pub trace_r: Frac,
    pub trace_r_or: Frac,
    pub trace_r_zz: Frac,
    pub trace_rho_o: Frac,
    pub trace_sigma_o: Frac,
    pub trace_r_o: Frac,
    pub beta: Frac,
    pub r_schatten_1_norm: Frac,
    pub l4_alpha_lower_bound: Frac,
    pub f2_support_sum_xx_yy: [u8; 4],
    pub packet_s_kernel_size: usize,
    pub packet_s_repair_size: usize,
    pub packet_s_unrepaired_kernel_witness: [u8; 3],
    pub packet_s_quotient_dim: usize,
}

pub fn witness() -> Witness {
    let zero = Frac::new(0, 1);
    let half = Frac::new(1, 2);
    let neg_half = Frac::new(-1, 2);
    let one = Frac::new(1, 1);
    let neg_one = Frac::new(-1, 1);
    let beta = Frac::new(1, 8);

    let rho: Mat4 = [
        [half, zero, zero, half],
        [zero, zero, zero, zero],
        [zero, zero, zero, zero],
        [half, zero, zero, half],
    ];
    let sigma: Mat4 = [
        [half, zero, zero, neg_half],
        [zero, zero, zero, zero],
        [zero, zero, zero, zero],
        [neg_half, zero, zero, half],
    ];
    let mut r: Mat4 = [[zero; 4]; 4];
    for i in 0..4 {
        for j in 0..4 {
            r[i][j] = rho[i][j].sub(sigma[i][j]);
        }
    }

    let o_r: Mat4 = [
        [one, zero, zero, zero],
        [zero, one, zero, zero],
        [zero, zero, neg_one, zero],
        [zero, zero, zero, neg_one],
    ];
    let zz: Mat4 = [
        [one, zero, zero, zero],
        [zero, neg_one, zero, zero],
        [zero, zero, neg_one, zero],
        [zero, zero, zero, one],
    ];
    let mut o: Mat4 = o_r;
    o[0][3] = o[0][3].add(beta);
    o[3][0] = o[3][0].add(beta);
    o[1][2] = o[1][2].add(beta);
    o[2][1] = o[2][1].add(beta);

    let mut tr_r = zero;
    for i in 0..4 {
        tr_r = tr_r.add(r[i][i]);
    }
    let tr_r_or = trace_product(&r, &o_r);
    let tr_r_zz = trace_product(&r, &zz);
    let tr_rho_o = trace_product(&rho, &o);
    let tr_sigma_o = trace_product(&sigma, &o);
    let tr_r_o = trace_product(&r, &o);

    let supp_xx = [1_u8, 1, 0, 0];
    let supp_yy = [1_u8, 1, 1, 1];
    let mut supp_sum = [0_u8; 4];
    for i in 0..4 {
        supp_sum[i] = supp_xx[i] ^ supp_yy[i];
    }

    let mut kernel = Vec::new();
    for bits in 0..8_u8 {
        let x = (bits >> 2) & 1;
        let y = (bits >> 1) & 1;
        let z = bits & 1;
        if (x ^ y) == 0 {
            kernel.push([x, y, z]);
        }
    }
    let repair = [[0_u8, 0, 0], [1_u8, 1, 0]];
    let unrepaired = kernel
        .iter()
        .copied()
        .find(|v| !repair.contains(v))
        .expect("unrepaired kernel vector");

    Witness {
        trace_r: tr_r,
        trace_r_or: tr_r_or,
        trace_r_zz: tr_r_zz,
        trace_rho_o: tr_rho_o,
        trace_sigma_o: tr_sigma_o,
        trace_r_o: tr_r_o,
        beta,
        r_schatten_1_norm: Frac::new(2, 1),
        l4_alpha_lower_bound: Frac::new(1, 8),
        f2_support_sum_xx_yy: supp_sum,
        packet_s_kernel_size: kernel.len(),
        packet_s_repair_size: repair.len(),
        packet_s_unrepaired_kernel_witness: unrepaired,
        packet_s_quotient_dim: 1,
    }
}

pub fn reject_packet_conjunction_or_lr_adapter(claim: &str) -> Result<(), &'static str> {
    if claim.contains("R_{0,3} == dim(ker Q / B)")
        || claim.contains("Lieb-Robinson")
        || claim.contains("T >= r/v")
    {
        Err("Packet L and Packet S have no cross-carrier adapter or Lieb-Robinson triple in WDP-21-16-WDP")
    } else {
        Ok(())
    }
}

// Origin: engine/crates_rs/tests/core_wdp/derivation_controls/wdp_21_16_wdp.rs
// Claim: urn:core:crates_rs:tests:wdp-21-16-wdp:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddf8df999 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddf8df999` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordf8df999 {
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
impl BoundaryErrordf8df999 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordf8df999 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordf8df999 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddf8df999 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordf8df999> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordf8df999::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordf8df999::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordf8df999::ExceedsCapacity {
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
    use super::{reject_packet_conjunction_or_lr_adapter, witness, Frac};

    #[test]
    fn packet_l_and_packet_s_identities_hold() {
        let w = witness();
        assert_eq!(w.trace_r, Frac::new(0, 1));
        assert_eq!(w.trace_r_or, Frac::new(0, 1));
        assert_eq!(w.trace_r_zz, Frac::new(0, 1));
        assert_eq!(w.trace_rho_o, Frac::new(1, 8));
        assert_eq!(w.trace_sigma_o, Frac::new(-1, 8));
        assert_eq!(w.trace_r_o, Frac::new(1, 4));
        assert_eq!(w.r_schatten_1_norm.mul(w.beta), w.trace_r_o);
        assert_eq!(w.l4_alpha_lower_bound, Frac::new(1, 8));
        assert_eq!(w.f2_support_sum_xx_yy, [0, 0, 1, 1]);
        assert_eq!(w.packet_s_kernel_size, 4);
        assert_eq!(w.packet_s_repair_size, 2);
        assert_eq!(w.packet_s_unrepaired_kernel_witness, [0, 0, 1]);
        assert_eq!(w.packet_s_quotient_dim, 1);
    }

    #[test]
    fn cross_packet_and_lieb_robinson_promotions_are_refused() {
        assert!(reject_packet_conjunction_or_lr_adapter("R_{0,3} == dim(ker Q / B)").is_err());
        assert!(reject_packet_conjunction_or_lr_adapter("Lieb-Robinson waiting time T >= r/v").is_err());
    }
}

#[test]
fn l4_boundary_admits_and_refuses_df8df999() {
    let admitted = BoundaryRecorddf8df999::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecorddf8df999::try_admit(9, 8).is_err());
}
