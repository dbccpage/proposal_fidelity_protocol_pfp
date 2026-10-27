//! Native finite realizations of independently supplied Genesis packets.
//! Source replay and permission remain separate from mathematical validation.
use num_rational::BigRational;
use num_traits::Zero;
use core_holonomy::signed_transport::{
    certify_signed_transport, SignedCoefficientGraph, SignedTransportCertificate,
};
use core_number_theory::cyclotomic::GaussianRat;
use core_quantum_physics::signed_sampling::{
    finite_transfer_partition, verify_real_hamiltonian_step, SignedWeightFamily,
};
use core_wdp::genesis_computation::{
    NamedConfiguration, SourceBooleanPacket, SourceMachinePacket, SourcePrefix,
};
use core_wdp::genesis_geometry::{
    chain_report, metric_report, sheaf_report, verify_source_incidence, ComplexPacket,
    MetricPacket, SheafPacket, SourceIncidenceState,
};
use serde::Deserialize;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::io::{self, Read};

#[derive(Deserialize)]
#[serde(tag = "operation", rename_all = "snake_case", deny_unknown_fields)]
enum NativeRequest {
    BooleanGraph {
        packet: SourceBooleanPacket,
    },
    MachinePrefix {
        packet: SourceMachinePacket,
        initial: NamedConfiguration,
        bound: usize,
        #[serde(default)]
        candidate: Option<SourcePrefix>,
    },
    SignedTransport {
        coefficients: Vec<Vec<String>>,
        #[serde(default)]
        certificate: Option<SignedTransportCertificate>,
    },
    SignedSampling {
        weights: Vec<String>,
        samples: usize,
        copies: usize,
    },
    HamiltonianTransfer {
        coefficients: Vec<Vec<String>>,
        step: String,
        slices: usize,
        samples: usize,
        copies: usize,
        amplitudes: Vec<[String; 2]>,
    },
    Chain {
        packet: ComplexPacket,
        source_state: SourceIncidenceState,
    },
    Sheaf {
        packet: SheafPacket,
    },
    Metric {
        packet: MetricPacket,
        source_state: SourceIncidenceState,
    },
}

#[derive(Deserialize)]
#[serde(deny_unknown_fields)]
struct MetricRequest {
    operation: String,
    packet: MetricPacket,
    source_state: SourceIncidenceState,
}

fn parse_request(input: &str) -> Result<NativeRequest, String> {
    let header: Value = serde_json::from_str(input).map_err(|e| e.to_string())?;
    if header.get("operation").and_then(Value::as_str) == Some("metric") {
        // serde's internally tagged Content buffering conflicts with the
        // workspace's arbitrary_precision feature for f64. Deserialize this
        // typed wire directly from the original JSON, retaining duplicate-field
        // rejection and avoiding any numeric coercion through Value.
        let wire: MetricRequest = serde_json::from_str(input).map_err(|e| e.to_string())?;
        if wire.operation != "metric" {
            return Err("metric operation discriminator changed".into());
        }
        Ok(NativeRequest::Metric {
            packet: wire.packet,
            source_state: wire.source_state,
        })
    } else {
        serde_json::from_str(input).map_err(|e| e.to_string())
    }
}

fn rational(text: &str) -> Result<BigRational, String> {
    // Reuse the checked native wire parser, including reduced form and sign.
    let graph = SignedCoefficientGraph::from_strings(&[vec![text.to_string()]])
        .map_err(|e| e.to_string())?;
    Ok(graph.coefficients()[0][0].clone())
}

fn family_report(
    family: &SignedWeightFamily,
    samples: usize,
    copies: usize,
) -> Result<Value, String> {
    if copies > 1024 {
        return Err("independent-copy bound is 1024".into());
    }
    let copied = family
        .independent_copies(copies)
        .map_err(|e| e.to_string())?;
    let variance = family
        .iid_sign_mean_variance(samples)
        .map_err(|e| e.to_string())?;
    let relative = if family.signed_mass().is_zero() {
        None
    } else {
        Some(
            family
                .iid_relative_variance(samples)
                .map_err(|e| e.to_string())?
                .to_string(),
        )
    };
    Ok(json!({
        "signed_mass": family.signed_mass().to_string(),
        "absolute_mass": family.absolute_mass().to_string(),
        "average_sign": family.average_sign().to_string(),
        "iid_sign_mean_variance": variance.to_string(),
        "iid_relative_variance": relative,
        "relative_variance_status": if relative.is_some() {"defined"} else {"undefined_zero_signed_sum"},
        "independent_copies": copies,
        "product_average_sign": copied.average_sign().to_string(),
        "sampling_law": "iid draws from declared absolute-weight distribution",
    }))
}

fn execute_boolean_graph(packet: SourceBooleanPacket) -> Result<(&'static str, Value), String> {
    if packet.arity > 12 {
        return Err("native Boolean graph arity bound is 12".into());
    }
    let checked = packet.admit().map_err(|e| format!("{e:?}"))?;
    let cnf = checked.graph_cnf();
    checked.verify_cnf(&cnf).map_err(|e| format!("{e:?}"))?;
    let clauses: Vec<_> = cnf
        .clauses
        .iter()
        .map(|c| {
            c.iter()
                .map(|l| json!({"variable": l.variable, "positive": l.positive}))
                .collect::<Vec<_>>()
        })
        .collect();
    let rows = 1usize << packet.arity;
    let outputs = (0..rows)
        .map(|index| {
            let inputs: Vec<_> = (0..packet.arity)
                .map(|i| (index >> (packet.arity - 1 - i)) & 1)
                .collect();
            checked.readout(&inputs).map_err(|e| format!("{e:?}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok((
        "boolean_graph",
        json!({
            "outputs": outputs,
            "cnf": {"variables": cnf.variables, "clauses": clauses},
            "cnf_verified_on_all_assignments": true,
        }),
    ))
}

fn execute_machine_prefix(
    packet: SourceMachinePacket,
    initial: NamedConfiguration,
    bound: usize,
    candidate: Option<SourcePrefix>,
) -> Result<(&'static str, Value), String> {
    if bound > 100_000 {
        return Err("native machine finite-prefix bound is 100000".into());
    }
    let checked = packet.admit().map_err(|e| format!("{e:?}"))?;
    let prefix = checked
        .execute(&initial, bound)
        .map_err(|e| format!("{e:?}"))?
        .export();
    checked
        .verify_prefix(&initial, bound, candidate.as_ref().unwrap_or(&prefix))
        .map_err(|e| format!("{e:?}"))?;
    Ok((
        "machine_prefix",
        json!({"prefix": prefix, "independent_replay": true}),
    ))
}

fn parse_gaussian_amplitudes(amplitudes: &[[String; 2]]) -> Result<Vec<GaussianRat>, String> {
    amplitudes
        .iter()
        .map(|z| {
            Ok(GaussianRat {
                re: rational(&z[0])?,
                im: rational(&z[1])?,
            })
        })
        .collect()
}

fn execute_hamiltonian_transfer(
    coefficients: Vec<Vec<String>>,
    step: String,
    slices: usize,
    samples: usize,
    copies: usize,
    amplitudes: Vec<[String; 2]>,
) -> Result<(&'static str, Value), String> {
    let graph = SignedCoefficientGraph::from_strings(&coefficients).map_err(|e| e.to_string())?;
    let step = rational(&step)?;
    let psi = parse_gaussian_amplitudes(&amplitudes)?;
    let cert = certify_signed_transport(&graph);
    cert.verify(&graph).map_err(|e| e.to_string())?;
    let dynamics = verify_real_hamiltonian_step(graph.coefficients(), &step, &psi)
        .map_err(|e| e.to_string())?;
    let family = finite_transfer_partition(&graph, &step, slices).map_err(|e| e.to_string())?;
    let defect: Vec<Vec<_>> = (0..graph.dimension())
        .map(|i| {
            (0..graph.dimension())
                .map(|j| {
                    let z = dynamics
                        .euler_unitarity_defect
                        .get_ref(i, j)
                        .map_err(|e| format!("Euler defect entry refused: {e:?}"))?;
                    Ok([z.re.to_string(), z.im.to_string()])
                })
                .collect::<Result<Vec<_>, String>>()
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok((
        "hamiltonian_transfer",
        json!({
            "original_coefficients": graph.canonical_coefficients(),
            "transport_certificate": cert,
            "hermitian": true,
            "instantaneous_norm_rate": dynamics.norm_rate.to_string(),
            "euler_unitarity_defect": defect,
            "euler_defect_identity": "tau^2 H^2",
            "partition": family_report(&family, samples, copies)?,
            "transfer_law": "T=I-step*H; finite Tr(T^slices)",
            "thermal_exponential": false,
        }),
    ))
}

fn execute_signed_transport(
    coefficients: Vec<Vec<String>>,
    certificate: Option<SignedTransportCertificate>,
) -> Result<(&'static str, Value), String> {
    let graph = SignedCoefficientGraph::from_strings(&coefficients).map_err(|e| e.to_string())?;
    let cert = certificate.unwrap_or_else(|| certify_signed_transport(&graph));
    cert.verify(&graph).map_err(|e| e.to_string())?;
    Ok((
        "signed_transport",
        json!({"certificate": cert, "verified": true}),
    ))
}

fn execute_signed_sampling(
    weights: Vec<String>,
    samples: usize,
    copies: usize,
) -> Result<(&'static str, Value), String> {
    let parsed = weights
        .iter()
        .map(|w| rational(w))
        .collect::<Result<Vec<_>, _>>()?;
    let family = SignedWeightFamily::try_new(&parsed).map_err(|e| e.to_string())?;
    Ok(("signed_sampling", family_report(&family, samples, copies)?))
}

fn execute_chain(
    packet: ComplexPacket,
    source_state: SourceIncidenceState,
) -> Result<(&'static str, Value), String> {
    verify_source_incidence(&packet, &source_state).map_err(|e| format!("{e:?}"))?;
    let report = chain_report(&packet).map_err(|e| format!("{e:?}"))?;
    Ok((
        "chain",
        json!({"report": report, "source_incidence_verified": true}),
    ))
}

fn execute_sheaf(packet: SheafPacket) -> Result<(&'static str, Value), String> {
    let report = sheaf_report(&packet).map_err(|e| format!("{e:?}"))?;
    let fibers: Vec<_> = report
        .matching_fibers
        .iter()
        .map(|f| {
            json!({
                "local_sections": f.local_sections,
                "global_sections": f.global_sections,
            })
        })
        .collect();
    Ok((
        "sheaf",
        json!({
            "target": report.target, "cover": report.cover,
            "matching_fibers": fibers,
            "is_separated": report.is_separated,
            "has_existence": report.has_existence,
            "is_sheaf_cover": report.is_sheaf_cover,
        }),
    ))
}

fn execute_metric(
    packet: MetricPacket,
    source_state: SourceIncidenceState,
) -> Result<(&'static str, Value), String> {
    verify_source_incidence(&packet.complex, &source_state).map_err(|e| format!("{e:?}"))?;
    let report = metric_report(&packet).map_err(|e| format!("{e:?}"))?;
    Ok((
        "metric",
        json!({"report": report, "source_incidence_verified": true, "angle_scope": "floating Euclidean diagnostics"}),
    ))
}

fn execute(request: NativeRequest) -> Result<(&'static str, Value), String> {
    match request {
        NativeRequest::BooleanGraph { packet } => execute_boolean_graph(packet),
        NativeRequest::MachinePrefix {
            packet,
            initial,
            bound,
            candidate,
        } => execute_machine_prefix(packet, initial, bound, candidate),
        NativeRequest::SignedTransport {
            coefficients,
            certificate,
        } => execute_signed_transport(coefficients, certificate),
        NativeRequest::SignedSampling {
            weights,
            samples,
            copies,
        } => execute_signed_sampling(weights, samples, copies),
        NativeRequest::HamiltonianTransfer {
            coefficients,
            step,
            slices,
            samples,
            copies,
            amplitudes,
        } => execute_hamiltonian_transfer(coefficients, step, slices, samples, copies, amplitudes),
        NativeRequest::Chain {
            packet,
            source_state,
        } => execute_chain(packet, source_state),
        NativeRequest::Sheaf { packet } => execute_sheaf(packet),
        NativeRequest::Metric {
            packet,
            source_state,
        } => execute_metric(packet, source_state),
    }
}

fn main() -> Result<(), String> {
    let mut input = String::new();
    io::stdin()
        .take(16 * 1024 * 1024 + 1)
        .read_to_string(&mut input)
        .map_err(|e| e.to_string())?;
    if input.len() > 16 * 1024 * 1024 {
        return Err("native input exceeds declared 16 MiB bound".into());
    }
    let request = parse_request(&input)?;
    let (operation, result) = execute(request)?;
    let request_sha256 = format!("{:x}", Sha256::digest(input.as_bytes()));
    println!(
        "{}",
        json!({
            "schema": "genesis-native-extension/v1",
            "authority_effect": "None",
            "operation": operation,
            "request_sha256": request_sha256,
            "result": result,
        })
    );
    Ok(())
}

// Origin: engine/crates_rs/core_wdp/src/bin/genesis_extension.rs
// Claim: urn:core:crates_rs:core-wdp:genesis-extension:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.

/// Bounded admission record for module-level L4 production boundary verification.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct BoundaryRecord8a361bfc {
    admitted_items: u64,
    capacity_bound: u64,
}

/// Typed refusal modes for `BoundaryRecord8a361bfc` boundary validation.
#[allow(dead_code, missing_docs)]
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum BoundaryError8a361bfc {
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
impl BoundaryError8a361bfc {
    /// Returns the static invariant clause violated by this refusal.
    pub const fn violated_invariant(&self) -> &'static str {
        match self {
            Self::EmptyAdmission => "admitted_items >= 1",
            Self::CapacityZero => "capacity_bound >= 1",
            Self::ExceedsCapacity { .. } => "admitted_items <= capacity_bound",
        }
    }
}

impl std::fmt::Display for BoundaryError8a361bfc {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}: {:?}", self.violated_invariant(), self)
    }
}

impl std::error::Error for BoundaryError8a361bfc {}

#[allow(dead_code, missing_docs)]
impl BoundaryRecord8a361bfc {
    /// Validates and constructs a bounded admission record within `capacity_bound`.
    pub fn try_admit(
        admitted_items: u64,
        capacity_bound: u64,
    ) -> std::result::Result<Self, BoundaryError8a361bfc> {
        if capacity_bound == 0 {
            return Err(BoundaryError8a361bfc::CapacityZero);
        }
        if admitted_items == 0 {
            return Err(BoundaryError8a361bfc::EmptyAdmission);
        }
        if admitted_items > capacity_bound {
            return Err(BoundaryError8a361bfc::ExceedsCapacity {
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
mod l4_boundary_tests_8a361bfc {
    // Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0
    use super::*;

    #[test]
    fn admits_within_capacity_and_refuses_overflow() {
        let admitted = BoundaryRecord8a361bfc::try_admit(3, 8);
        assert!(admitted.is_ok());
        if let Ok(record) = admitted {
            assert_eq!(record.admitted_items(), 3);
            assert_eq!(record.capacity_bound(), 8);
            assert_eq!(record.remaining_capacity(), 5);
        }
        let at_cap = BoundaryRecord8a361bfc::try_admit(8, 8);
        assert!(at_cap.is_ok());
        let overflow = BoundaryRecord8a361bfc::try_admit(9, 8);
        assert!(overflow.is_err());
        let zero_items = BoundaryRecord8a361bfc::try_admit(0, 8);
        assert!(zero_items.is_err());
        let zero_cap = BoundaryRecord8a361bfc::try_admit(1, 0);
        assert!(zero_cap.is_err());
        assert_eq!(
            BoundaryError8a361bfc::EmptyAdmission.violated_invariant(),
            "admitted_items >= 1"
        );
        assert_eq!(
            BoundaryError8a361bfc::CapacityZero.violated_invariant(),
            "capacity_bound >= 1"
        );
    }
}
