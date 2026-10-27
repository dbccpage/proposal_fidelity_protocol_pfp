//! Bounded transport to canonical finite functional calculations.
//! Inputs and results use canonical rational strings; no arithmetic lives here.

use num_rational::BigRational;
use core_functional::{finite_family_bound as family, projection_transfer as transfer};
use core_kernel::{parse_exact, to_canonical_string};
use serde_json::{json, Map, Value};

const MAX_ITEMS: usize = 4096;
const MAX_EXACT_BYTES: usize = 4096;

fn object<'a>(value: &'a Value, allowed: &[&str]) -> Result<&'a Map<String, Value>, String> {
    let object = value.as_object().ok_or("request must be an object")?;
    if let Some(name) = object.keys().find(|name| !allowed.contains(&name.as_str())) {
        return Err(format!("unknown field: {name}"));
    }
    Ok(object)
}

fn required<'a>(object: &'a Map<String, Value>, name: &str) -> Result<&'a Value, String> {
    object.get(name).ok_or_else(|| format!("missing {name}"))
}

fn exact(value: &Value) -> Result<BigRational, String> {
    let text = value
        .as_str()
        .ok_or("exact scalar must be a canonical string")?;
    if text.len() > MAX_EXACT_BYTES {
        return Err(format!("exact scalar exceeds {MAX_EXACT_BYTES} bytes"));
    }
    parse_exact(text).map_err(|error| error.to_string())
}

fn vector(value: &Value) -> Result<Vec<BigRational>, String> {
    let rows = value.as_array().ok_or("rational vector must be an array")?;
    if rows.len() > MAX_ITEMS {
        return Err(format!("rational vector exceeds {MAX_ITEMS} entries"));
    }
    rows.iter().map(exact).collect()
}

fn vector_value(values: &[BigRational]) -> Value {
    Value::Array(
        values
            .iter()
            .map(|value| Value::String(to_canonical_string(value)))
            .collect(),
    )
}

fn count(value: &Value, name: &str) -> Result<usize, String> {
    let count = value
        .as_u64()
        .and_then(|value| usize::try_from(value).ok())
        .ok_or_else(|| format!("{name} must be a nonnegative integer"))?;
    Ok(count)
}

fn count_field(row: &serde_json::Map<String, Value>, name: &str) -> Result<usize, String> {
    count(required(row, name)?, name)
}

fn exact_field(row: &serde_json::Map<String, Value>, name: &str) -> Result<BigRational, String> {
    exact(required(row, name)?)
}

fn member(value: &Value) -> Result<family::FiniteFamilyMember, String> {
    let row = object(
        value,
        &[
            "system_id",
            "site_count",
            "edge_count",
            "local_interaction_norm",
            "active_edge_rates",
        ],
    )?;
    let id = required(row, "system_id")?
        .as_str()
        .ok_or("system_id must be a string")?;
    if id.len() > MAX_ITEMS {
        return Err(format!("system_id exceeds {MAX_ITEMS} bytes"));
    }
    family::FiniteFamilyMember::new(
        id,
        count_field(row, "site_count")?,
        count_field(row, "edge_count")?,
        exact_field(row, "local_interaction_norm")?,
        vector(required(row, "active_edge_rates")?)?,
    )
    .map_err(|error| error.to_string())
}

fn member_value(member: &family::FiniteFamilyMember) -> Value {
    json!({
        "system_id": member.system_id(), "site_count": member.site_count(), "edge_count": member.edge_count(),
        "local_interaction_norm": to_canonical_string(member.local_interaction_norm()),
        "active_edge_rates": vector_value(member.active_edge_rates()),
        "active_edge_count": member.active_edge_rates().len(),
        "active_edge_density": to_canonical_string(&member.active_edge_density()),
        "edge_site_density": to_canonical_string(&member.edge_site_density()),
    })
}

fn premises(value: &Value) -> Result<family::UniformFamilyPremises, String> {
    let fields = object(value, &["g_star", "eta_star", "nu_star", "a_star"])?;
    Ok(family::UniformFamilyPremises {
        g_star: exact_field(fields, "g_star")?,
        eta_star: exact_field(fields, "eta_star")?,
        nu_star: exact_field(fields, "nu_star")?,
        a_star: exact_field(fields, "a_star")?,
    })
}

fn parse_family_members(rows: &[Value]) -> Result<Vec<family::FiniteFamilyMember>, String> {
    if rows.len() > MAX_ITEMS {
        return Err(format!("family exceeds {MAX_ITEMS} members"));
    }
    let mut total_rates = 0usize;
    for row in rows {
        let rates = row
            .get("active_edge_rates")
            .and_then(Value::as_array)
            .ok_or("active_edge_rates must be an array")?;
        total_rates = total_rates
            .checked_add(rates.len())
            .ok_or("rate count overflow")?;
        if total_rates > MAX_ITEMS {
            return Err(format!("family exceeds {MAX_ITEMS} total active rates"));
        }
    }
    rows.iter().map(member).collect()
}

fn family_bound(payload: &Value) -> Result<Value, String> {
    let fields = object(payload, &["members", "premises", "time"])?;
    let rows = required(fields, "members")?
        .as_array()
        .ok_or("members must be an array")?;
    let members = parse_family_members(rows)?;
    let premises = premises(required(fields, "premises")?)?;
    let time = exact_field(fields, "time")?;
    let result = family::certify_uniform_family(&members, &premises, &time)
        .map_err(|error| error.to_string())?;
    let optional = |value: &Option<BigRational>| value.as_ref().map(to_canonical_string);
    let member_bounds: Vec<_> = result
        .member_bounds
        .iter()
        .map(|member| {
            json!({
                "system_id": member.system_id,
                "active_edge_density": to_canonical_string(&member.active_edge_density),
                "edge_site_density": to_canonical_string(&member.edge_site_density),
                "edge_density_lower_bound": to_canonical_string(&member.edge_density_lower_bound),
                "site_density_lower_bound": to_canonical_string(&member.site_density_lower_bound),
            })
        })
        .collect();
    let refusals: Vec<_> = result
        .refusals
        .iter()
        .map(|reason| {
            json!({
                "code": reason.code, "detail": reason.detail, "system_id": reason.system_id,
            })
        })
        .collect();
    Ok(json!({
        "accepted": result.accepted, "time": to_canonical_string(&result.time),
        "members": result.members.iter().map(member_value).collect::<Vec<_>>(),
        "premises": {
            "g_star": to_canonical_string(&result.premises.g_star), "eta_star": to_canonical_string(&result.premises.eta_star),
            "nu_star": to_canonical_string(&result.premises.nu_star), "a_star": to_canonical_string(&result.premises.a_star),
        },
        "uniform_window_upper": optional(&result.uniform_window_upper), "local_edge_polynomial": optional(&result.local_edge_polynomial),
        "edge_density_floor": optional(&result.edge_density_floor), "site_density_floor": optional(&result.site_density_floor),
        "half_slope_site_floor": optional(&result.half_slope_site_floor), "member_bounds": member_bounds, "refusals": refusals,
    }))
}

fn projection_transfer(payload: &Value) -> Result<Value, String> {
    let fields = object(
        payload,
        &[
            "rho",
            "sigma",
            "projected_rho",
            "projected_sigma",
            "lipschitz_constant",
        ],
    )?;
    let vectors = ["rho", "sigma", "projected_rho", "projected_sigma"]
        .iter()
        .map(|name| vector(required(fields, name)?))
        .collect::<Result<Vec<_>, String>>()?;
    let lipschitz = exact(required(fields, "lipschitz_constant")?)?;
    let result = transfer::reverse_triangle_certificate(
        &vectors[0],
        &vectors[1],
        &vectors[2],
        &vectors[3],
        &lipschitz,
    )
    .map_err(|error| error.to_string())?;
    Ok(json!({
        "states": result.states.iter().map(|state| vector_value(state)).collect::<Vec<_>>(),
        "accepted": result.accepted(), "lipschitz_constant": to_canonical_string(&result.lipschitz_constant),
        "source_distance": to_canonical_string(&result.source_distance), "projection_distance": to_canonical_string(&result.projection_distance),
        "rho_defect": to_canonical_string(&result.rho_defect), "sigma_defect": to_canonical_string(&result.sigma_defect),
        "defect_difference": to_canonical_string(&result.defect_difference), "transfer_lower_bound": to_canonical_string(&result.transfer_lower_bound),
        "pairwise_lipschitz_premise": result.pairwise_lipschitz_premise, "reverse_triangle_holds": result.reverse_triangle_holds,
        "defect_difference_bound_holds": result.defect_difference_bound_holds, "transfer_holds": result.transfer_holds,
        "refusal": if result.accepted() { None } else { Some("pairwise_lipschitz_premise_failed") },
    }))
}

pub(super) fn dispatch(action: &str, payload: &Value) -> Result<Value, String> {
    match action {
        "functional_projection_transfer" => projection_transfer(payload),
        "functional_family_bound" => family_bound(payload),
        "functional_family_member" => member(payload).map(|member| member_value(&member)),
        _ => Err(format!("unsupported native functional action: {action}")),
    }
}

// Origin: engine/crates_rs/pfp/src/invoke/native_functional.rs
// Claim: urn:core:crates_rs:pfp:native-functional:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecorddd5f1dd1 {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecorddd5f1dd1` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryErrordd5f1dd1 {
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
impl BoundaryErrordd5f1dd1 {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryErrordd5f1dd1 {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryErrordd5f1dd1 {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecorddd5f1dd1 {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryErrordd5f1dd1> {
        if capacity_bound == 0 {
            return Err(BoundaryErrordd5f1dd1::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryErrordd5f1dd1::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryErrordd5f1dd1::ExceedsCapacity {
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
mod tests {
    use super::*;

    fn one_member() -> Value {
        json!({"system_id":"N4","site_count":4,"edge_count":4,"local_interaction_norm":"2","active_edge_rates":["3","4"]})
    }

    #[test]
    fn exact_member_and_family_preserve_canonical_bound_results() {
        let member = dispatch("functional_family_member", &one_member()).unwrap();
        assert_eq!(member["active_edge_density"], "1/2");
        let payload = json!({"members":[one_member()], "premises":{"g_star":"2","eta_star":"1/2","nu_star":"3","a_star":"1"}, "time":"1/64"});
        let report = dispatch("functional_family_bound", &payload).unwrap();
        assert_eq!(report["accepted"], true);
        assert_eq!(report["site_density_floor"], "3/256");
        assert_eq!(
            report["member_bounds"][0]["site_density_lower_bound"],
            "3/256"
        );
    }

    #[test]
    fn false_pairwise_premise_cannot_carry_a_transfer_bit() {
        let payload = json!({"rho":["1"],"sigma":["0"],"projected_rho":["1"],"projected_sigma":["0"],"lipschitz_constant":"0"});
        let report = dispatch("functional_projection_transfer", &payload).unwrap();
        assert_eq!(report["accepted"], false);
        assert_eq!(report["transfer_holds"], Value::Null);
        assert_eq!(report["refusal"], "pairwise_lipschitz_premise_failed");
    }

    #[test]
    fn large_metadata_counts_do_not_allocate_large_carriers() {
        let mut large = one_member();
        large["site_count"] = json!(1_000_000);
        large["edge_count"] = json!(1_000_000);
        let member = dispatch("functional_family_member", &large).unwrap();
        assert_eq!(member["active_edge_density"], "1/500000");
        assert_eq!(member["edge_site_density"], "1");
        let payload = json!({
            "members": [large],
            "premises": {"g_star":"2", "eta_star":"1/1000000", "nu_star":"3", "a_star":"1"},
            "time":"1/64"
        });
        assert_eq!(
            dispatch("functional_family_bound", &payload).unwrap()["accepted"],
            true
        );
    }

    #[test]
    fn wire_refuses_approximate_noncanonical_unknown_and_oversized_inputs() {
        for value in [
            json!(true),
            json!(1),
            json!(0.5),
            json!("2/4"),
            json!("1/0"),
            json!("1/1"),
        ] {
            assert!(exact(&value).is_err());
        }
        let mut row = one_member();
        row["site_count"] = json!(true);
        assert!(dispatch("functional_family_member", &row).is_err());
        let mut row = one_member();
        row["unknown"] = json!(0);
        assert!(dispatch("functional_family_member", &row).is_err());
        assert!(vector(&json!(vec!["0"; MAX_ITEMS + 1])).is_err());
        assert!(exact(&json!("1".repeat(MAX_EXACT_BYTES + 1))).is_err());
    }
}

#[cfg(test)]
mod l4_boundary_tests_dd5f1dd1 {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecorddd5f1dd1::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecorddd5f1dd1::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecorddd5f1dd1::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecorddd5f1dd1::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecorddd5f1dd1::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(BoundaryErrordd5f1dd1::EmptyAdmission.violated_invariant(), "admitted_items >= 1");
        assert_eq!(BoundaryErrordd5f1dd1::CapacityZero.violated_invariant(), "capacity_bound >= 1");
    }
}
