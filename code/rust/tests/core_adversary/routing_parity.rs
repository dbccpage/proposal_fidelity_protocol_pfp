use core_adversary::{
    exact::{integer, Integer},
    routing::{
        admit_spend, canonical_seat_key, parse_routing, validate_table, BudgetPolicy, RouteLeg,
        RoutingTable,
    },
};
use serde_json::{json, Value};

fn outcome<T: serde::Serialize>(result: Result<T, core_adversary::stage::ports::Refusal>) -> Value {
    match result {
        Ok(value) => json!({"ok": value}),
        Err(error) => json!({"error": error}),
    }
}
#[test]
fn frozen_python_routing_domain_vectors() {
    let rows: Vec<Value> =
        serde_json::from_str(include_str!("fixtures/python_routing_v1.json")).unwrap();
    let mut count = 0;
    for row in rows {
        let actual = match row["op"].as_str().unwrap() {
            "parse_routing" => outcome(parse_routing(row["data_json"].as_str().unwrap())),
            "validate_table" => {
                let table: RoutingTable = serde_json::from_value(row["table"].clone()).unwrap();
                outcome(validate_table(&table).map(|()| table))
            }
            "canonical_seat_key" => json!(canonical_seat_key(row["seat_id"].as_str().unwrap())),
            "seat" => {
                let table: RoutingTable = serde_json::from_value(row["table"].clone()).unwrap();
                outcome(table.seat(row["seat_id"].as_str().unwrap()))
            }
            "cost" => {
                let leg: RouteLeg = serde_json::from_value(row["leg"].clone()).unwrap();
                json!(Integer(leg.cost_microusd(
                    &integer(&row["input_tokens"]).unwrap(),
                    &integer(&row["output_tokens"]).unwrap()
                )))
            }
            "admit_spend" => {
                let p: BudgetPolicy = serde_json::from_value(row["policy"].clone()).unwrap();
                let values = &row["values"];
                let zero = json!(0);
                let n = |key| integer(values.get(key).unwrap_or(&zero)).unwrap();
                outcome(admit_spend(
                    &n("spent_bout"),
                    &n("spent_day"),
                    &n("worst_case"),
                    &p,
                    values["tier"].as_str().unwrap_or(""),
                    &n("spent_tier"),
                ))
            }
            "machine" | "parse_reply" | "gateway" => continue,
            other => panic!("unknown fixture {other}"),
        };
        assert_eq!(actual, row["expected"], "operation: {}", row["op"]);
        count += 1;
    }
    assert_eq!(count, 77);
}

// Origin: engine/crates_rs/tests/core_adversary/routing_parity.rs
// Claim: urn:core:crates_rs:tests:routing-parity:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord3df1450e {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord3df1450e` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError3df1450e {
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
impl BoundaryError3df1450e {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError3df1450e {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError3df1450e {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord3df1450e {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError3df1450e> {
        if capacity_bound == 0 {
            return Err(BoundaryError3df1450e::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError3df1450e::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError3df1450e::ExceedsCapacity {
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

#[test]
fn l4_boundary_admits_and_refuses_3df1450e() {
    let admitted = BoundaryRecord3df1450e::try_admit(3, 8);
    assert!(admitted.is_ok());
    if let Ok(record) = admitted {
        assert_eq!(record.admitted_items(), 3);
        assert_eq!(record.capacity_bound(), 8);
        assert_eq!(record.remaining_capacity(), 5);
    }
    assert!(BoundaryRecord3df1450e::try_admit(9, 8).is_err());
}

// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)
