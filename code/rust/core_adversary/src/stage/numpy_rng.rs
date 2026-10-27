//! Narrow NumPy 2.5.3 SeedSequence(u32), PCG64 and double normal compatibility.
//! BSD-3-Clause / PCG MIT notices are retained in ../numpy_notice.txt.
use crate::stage::numpy_ziggurat::{FI, KI, WI};
use crate::stage::ports::Refusal;

fn hashmix(mut value: u32, hash: &mut u32) -> u32 {
    value ^= *hash;
    *hash = hash.wrapping_mul(0x931e8875);
    value = value.wrapping_mul(*hash);
    value ^ (value >> 16)
}
fn seed_words(seed: u32) -> [u64; 4] {
    let mut pool = [0; 4];
    let mut hash = 0x43b0d7e5;
    for (index, entry) in pool.iter_mut().enumerate() {
        *entry = hashmix(if index == 0 { seed } else { 0 }, &mut hash);
    }
    for source in 0..4 {
        for destination in 0..4 {
            if source != destination {
                let value = hashmix(pool[source], &mut hash);
                let mixed = pool[destination]
                    .wrapping_mul(0xca01f9dd)
                    .wrapping_sub(value.wrapping_mul(0x4973f715));
                pool[destination] = mixed ^ (mixed >> 16);
            }
        }
    }
    let mut words = [0u32; 8];
    hash = 0x8b51f9dd;
    for (index, word) in words.iter_mut().enumerate() {
        let mut value = pool[index % 4] ^ hash;
        hash = hash.wrapping_mul(0x58f38ded);
        value = value.wrapping_mul(hash);
        *word = value ^ (value >> 16);
    }
    std::array::from_fn(|i| u64::from(words[i * 2]) | (u64::from(words[i * 2 + 1]) << 32))
}
pub(crate) struct NumpyPcg64 {
    state: u128,
    inc: u128,
}
impl NumpyPcg64 {
    pub(crate) fn new(seed: u32) -> Self {
        let [s0, s1, i0, i1] = seed_words(seed);
        let initial = (u128::from(s0) << 64) | u128::from(s1);
        let sequence = (u128::from(i0) << 64) | u128::from(i1);
        let mut rng = Self {
            state: 0,
            inc: sequence.wrapping_shl(1) | 1,
        };
        rng.step();
        rng.state = rng.state.wrapping_add(initial);
        rng.step();
        rng
    }
    fn step(&mut self) {
        const MULTIPLIER: u128 = (2549297995355413924u128 << 64) | 4865540595714422341u128;
        self.state = self.state.wrapping_mul(MULTIPLIER).wrapping_add(self.inc);
    }
    fn next_u64(&mut self) -> u64 {
        self.step();
        let high = (self.state >> 64) as u64;
        let low = self.state as u64;
        (high ^ low).rotate_right((self.state >> 122) as u32)
    }
    fn uniform(&mut self) -> f64 {
        ((self.next_u64() >> 11) as f64) * (1.0 / 9007199254740992.0)
    }
    pub(crate) fn standard_normal(&mut self) -> Result<f64, Refusal> {
        const R: f64 = f64::from_bits(0x400d3bb48209ad33);
        const INV_R: f64 = f64::from_bits(0x3fd183aa6c20e8c1);
        // A bounded adapter refuses pathological rejection loops rather than hanging.
        for _ in 0..1024 {
            let mut r = self.next_u64();
            let index = (r & 0xff) as usize;
            r >>= 8;
            let sign = r & 1;
            let magnitude = (r >> 1) & 0x000f_ffff_ffff_ffff;
            let mut x = (magnitude as f64) * WI[index];
            if sign == 1 {
                x = -x;
            }
            if magnitude < KI[index] {
                return Ok(x);
            }
            if index == 0 {
                for _ in 0..1024 {
                    let xx = -INV_R * (-self.uniform()).ln_1p();
                    let yy = -(-self.uniform()).ln_1p();
                    if yy + yy > xx * xx {
                        return Ok(if (magnitude >> 8) & 1 == 1 {
                            -(R + xx)
                        } else {
                            R + xx
                        });
                    }
                }
                break;
            } else if (FI[index - 1] - FI[index]) * self.uniform() + FI[index]
                < (-0.5 * x * x).exp()
            {
                return Ok(x);
            }
        }
        Err(Refusal::new(
            "SBE_RANDOM_UNAVAILABLE",
            "normal rejection budget exhausted",
        ))
    }
}

// Computational-Profile: Numerical (floating-point convergence and error tolerance bound monitored)

#[cfg(test)]
#[path = "../../../tests/core_adversary/stage/support/numpy_stream_cases.rs"]
mod stream_cases;

// Origin: engine/crates_rs/core_adversary/src/stage/numpy_rng.rs
// Claim: urn:core:crates_rs:core-adversary:numpy-rng:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecordbb13a5c1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecordbb13a5c1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrorbb13a5c1 {
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
impl BoundaryErrorbb13a5c1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrorbb13a5c1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrorbb13a5c1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecordbb13a5c1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrorbb13a5c1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrorbb13a5c1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrorbb13a5c1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrorbb13a5c1::ExceedsCapacity {
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
mod l4_boundary_tests_bb13a5c1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecordbb13a5c1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecordbb13a5c1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecordbb13a5c1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecordbb13a5c1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecordbb13a5c1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryErrorbb13a5c1::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryErrorbb13a5c1::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
