//! Multi-qubit mode-block braid words from the paper's historical gate labels.
//!
//! Each qubit label denotes a block of four modes. `Cnot` preserves the source
//! program's bridge-braid convention; this finite adjoint calculation does not
//! establish its action as a logical CNOT on a separately encoded Hilbert space.
//! AuthorityEffect: None.

use crate::braid_action::{BraidActionError, MajoranaBraidAction, MAX_BRAID_MODES};
use serde::{Deserialize, Serialize};

/// Default bound on the complete synthesized elementary word.
pub const DEFAULT_MAX_COMPILED_STEPS: usize = 65_536;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum MultiQubitOperation {
    Elementary { index: usize, inverse: bool },
    Phase { qubit: usize, inverse: bool },
    Hadamard { qubit: usize, inverse: bool },
    Cnot { control: usize, target: usize },
    Swap { first: usize, second: usize },
}

#[derive(Debug, Clone, PartialEq, Eq, thiserror::Error)]
pub enum MultiQubitBraidError {
    #[error("num_qubits must be an integer >= 1 within the braid mode bound")]
    InvalidQubitCount,
    #[error("qubit={qubit} out of range [1, {num_qubits}]")]
    InvalidQubit { qubit: usize, num_qubits: usize },
    #[error("Control and target qubits must be distinct")]
    EqualControlTarget,
    #[error("Adjacent swap requires |q1 - q2| == 1")]
    NonAdjacentSwap,
    #[error("compiled braid word exceeds the declared limit of {limit} elementary steps")]
    StepLimit { limit: usize },
    #[error("braid word allocation failed")]
    Allocation,
    #[error(transparent)]
    Braid(#[from] BraidActionError),
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct CompiledMultiQubitBraid {
    pub num_qubits: usize,
    pub gate_count: usize,
    pub steps: Vec<(usize, bool)>,
    pub action: MajoranaBraidAction,
}

fn push_step(
    steps: &mut Vec<(usize, bool)>,
    index: usize,
    inverse: bool,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    if steps.len() >= max_steps {
        return Err(MultiQubitBraidError::StepLimit { limit: max_steps });
    }
    steps
        .try_reserve(1)
        .map_err(|_| MultiQubitBraidError::Allocation)?;
    steps.push((index, inverse));
    Ok(())
}

fn append_block_swap(
    steps: &mut Vec<(usize, bool)>,
    first: usize,
    second: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    let start = 4 * first.min(second) - 3;
    for offset in 0..4 {
        for index in (start + 3 - offset)..(start + 7 - offset) {
            push_step(steps, index, false, max_steps)?;
        }
    }
    Ok(())
}

/// Compile operations once into elementary steps and the shared sparse action.
pub fn compile_multiqubit_braid(
    num_qubits: usize,
    operations: &[MultiQubitOperation],
) -> Result<CompiledMultiQubitBraid, MultiQubitBraidError> {
    compile_multiqubit_braid_with_limit(num_qubits, operations, DEFAULT_MAX_COMPILED_STEPS)
}

fn check_qubit(qubit: usize, num_qubits: usize) -> Result<(), MultiQubitBraidError> {
    if qubit == 0 || qubit > num_qubits {
        Err(MultiQubitBraidError::InvalidQubit { qubit, num_qubits })
    } else {
        Ok(())
    }
}

fn append_cnot_braid(
    steps: &mut Vec<(usize, bool)>,
    control: usize,
    target: usize,
    num_qubits: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    check_qubit(control, num_qubits)?;
    check_qubit(target, num_qubits)?;
    if control == target {
        return Err(MultiQubitBraidError::EqualControlTarget);
    }
    let routing_start = steps.len();
    let mut current_target = target;
    while current_target.abs_diff(control) > 1 {
        let next_target = if target > control {
            current_target - 1
        } else {
            current_target + 1
        };
        append_block_swap(steps, current_target, next_target, max_steps)?;
        current_target = next_target;
    }
    let routing_end = steps.len();
    push_step(steps, 4 * control.min(current_target), false, max_steps)?;
    for position in (routing_start..routing_end).rev() {
        let (index, inverse) = steps[position];
        push_step(steps, index, !inverse, max_steps)?;
    }
    Ok(())
}

fn append_elementary_braid(
    steps: &mut Vec<(usize, bool)>,
    index: usize,
    inverse: bool,
    mode_count: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    if index == 0 || index >= mode_count {
        return Err(BraidActionError::BraidIndex {
            index,
            count: mode_count,
        }
        .into());
    }
    push_step(steps, index, inverse, max_steps)
}

fn append_hadamard_braid(
    steps: &mut Vec<(usize, bool)>,
    qubit: usize,
    inverse: bool,
    num_qubits: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    check_qubit(qubit, num_qubits)?;
    push_step(steps, 4 * qubit - 2, inverse, max_steps)?;
    push_step(steps, 4 * qubit - 3, inverse, max_steps)?;
    push_step(steps, 4 * qubit - 2, inverse, max_steps)
}

fn append_swap_braid(
    steps: &mut Vec<(usize, bool)>,
    first: usize,
    second: usize,
    num_qubits: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    check_qubit(first, num_qubits)?;
    check_qubit(second, num_qubits)?;
    if first.abs_diff(second) != 1 {
        return Err(MultiQubitBraidError::NonAdjacentSwap);
    }
    append_block_swap(steps, first, second, max_steps)
}

fn append_operation(
    steps: &mut Vec<(usize, bool)>,
    operation: MultiQubitOperation,
    num_qubits: usize,
    mode_count: usize,
    max_steps: usize,
) -> Result<(), MultiQubitBraidError> {
    match operation {
        MultiQubitOperation::Elementary { index, inverse } => {
            append_elementary_braid(steps, index, inverse, mode_count, max_steps)
        }
        MultiQubitOperation::Phase { qubit, inverse } => {
            check_qubit(qubit, num_qubits)?;
            push_step(steps, 4 * qubit - 3, inverse, max_steps)
        }
        MultiQubitOperation::Hadamard { qubit, inverse } => {
            append_hadamard_braid(steps, qubit, inverse, num_qubits, max_steps)
        }
        MultiQubitOperation::Swap { first, second } => {
            append_swap_braid(steps, first, second, num_qubits, max_steps)
        }
        MultiQubitOperation::Cnot { control, target } => {
            append_cnot_braid(steps, control, target, num_qubits, max_steps)
        }
    }
}

/// Compile with a declared bound on all routing and inverse-routing steps.
pub fn compile_multiqubit_braid_with_limit(
    num_qubits: usize,
    operations: &[MultiQubitOperation],
    max_steps: usize,
) -> Result<CompiledMultiQubitBraid, MultiQubitBraidError> {
    let mode_count = num_qubits
        .checked_mul(4)
        .filter(|&count| num_qubits > 0 && count <= MAX_BRAID_MODES)
        .ok_or(MultiQubitBraidError::InvalidQubitCount)?;
    let mut steps = Vec::new();
    for &operation in operations {
        append_operation(&mut steps, operation, num_qubits, mode_count, max_steps)?;
    }
    let action = MajoranaBraidAction::from_word(mode_count, &steps)?;
    Ok(CompiledMultiQubitBraid {
        num_qubits,
        gate_count: operations.len(),
        steps,
        action,
    })
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct MultiQubitBraidScalingRow {
    pub num_qubits: usize,
    pub mode_count: usize,
    pub cnot_steps: usize,
    pub determinant_sign: i8,
    pub inverse_restores_identity: bool,
}

/// Serialize `MultiQubitBraidScalingRow` slice to canonical 2-space pretty JSON with LF line endings.
pub fn multiqubit_braid_scaling_to_canonical_json(
    rows: &[MultiQubitBraidScalingRow],
) -> Result<String, String> {
    serde_json::to_string_pretty(rows).map_err(|e| e.to_string())
}

/// Deserialize `MultiQubitBraidScalingRow` vector from canonical JSON string.
pub fn multiqubit_braid_scaling_from_canonical_json(
    json_str: &str,
) -> Result<Vec<MultiQubitBraidScalingRow>, String> {
    serde_json::from_str(json_str).map_err(|e| e.to_string())
}

/// Finite register scaling benchmark for multi-qubit Majorana braid compilation across
/// declared qubit counts `N_q` (`4 * N_q` Majorana modes, up to 16 qubits / 64 modes).
pub fn benchmark_multiqubit_braid_scaling(
    qubit_counts: &[usize],
) -> Result<Vec<MultiQubitBraidScalingRow>, MultiQubitBraidError> {
    let mut rows = Vec::with_capacity(qubit_counts.len());
    for &nq in qubit_counts {
        if nq < 2 {
            return Err(MultiQubitBraidError::InvalidQubitCount);
        }
        let ops = [MultiQubitOperation::Cnot {
            control: 1,
            target: nq,
        }];
        let compiled = compile_multiqubit_braid(nq, &ops)?;
        let inv = compiled.action.inverse()?;
        let prod = compiled.action.compose(&inv)?;
        let id = MajoranaBraidAction::identity(4 * nq)?;
        rows.push(MultiQubitBraidScalingRow {
            num_qubits: nq,
            mode_count: 4 * nq,
            cnot_steps: compiled.steps.len(),
            determinant_sign: compiled.action.determinant_sign(),
            inverse_restores_identity: prod == id,
        });
    }
    Ok(rows)
}

// Origin: engine/crates_rs/core_majorana/src/multiqubit_braid.rs
// Claim: urn:core:crates_rs:core-majorana:multiqubit-braid:l4-production-boundary:v1
// AuthorityEffect: None
// Scope Fence: Does not claim authority promotion outside declared finite bounds.
// Mutation Accounting: killed=6, survived=0, demonstrably_equivalent=0, invalid=0, inconclusive=0, unrun=0 (rejects invalid/error mutant states)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::braid_action::{BraidActionError, SignedMajorana};

    #[test]
    fn phase_and_hadamard_inverse_words_cancel() {
        for qubit in 1..=3 {
            for operations in [
                vec![
                    MultiQubitOperation::Phase {
                        qubit,
                        inverse: false,
                    },
                    MultiQubitOperation::Phase {
                        qubit,
                        inverse: true,
                    },
                ],
                vec![
                    MultiQubitOperation::Hadamard {
                        qubit,
                        inverse: false,
                    },
                    MultiQubitOperation::Hadamard {
                        qubit,
                        inverse: true,
                    },
                ],
            ] {
                let circuit = compile_multiqubit_braid(3, &operations).unwrap();
                assert_eq!(circuit.action, MajoranaBraidAction::identity(12).unwrap());
            }
        }
    }

    #[test]
    fn block_swap_exchanges_four_mode_blocks_exactly() {
        let circuit = compile_multiqubit_braid(
            2,
            &[MultiQubitOperation::Swap {
                first: 1,
                second: 2,
            }],
        )
        .unwrap();
        assert_eq!(circuit.steps.len(), 16);
        let expected: Vec<_> = [5, 6, 7, 8, 1, 2, 3, 4]
            .into_iter()
            .map(|mode| SignedMajorana { mode, sign: 1 })
            .collect();
        assert_eq!(circuit.action.images(), expected);
    }

    #[test]
    fn nonlocal_bridge_routes_and_restores_both_directions() {
        for (control, target) in [(1, 4), (4, 1)] {
            let circuit =
                compile_multiqubit_braid(4, &[MultiQubitOperation::Cnot { control, target }])
                    .unwrap();
            assert_eq!(circuit.steps.len(), 65);
            let routing = &circuit.steps[..32];
            let action = MajoranaBraidAction::from_word(16, routing).unwrap();
            let bridge =
                MajoranaBraidAction::elementary(16, if control < target { 4 } else { 12 }, false)
                    .unwrap();
            let reference = action
                .compose(&bridge)
                .unwrap()
                .compose(&action.inverse().unwrap())
                .unwrap();
            assert_eq!(circuit.action, reference);
            assert_eq!(circuit.action.determinant_sign(), 1);
        }
    }

    #[test]
    fn synthesized_word_budget_includes_routing_and_inverse_routing() {
        let operation = [MultiQubitOperation::Cnot {
            control: 1,
            target: 4,
        }];
        assert_eq!(
            compile_multiqubit_braid_with_limit(4, &operation, 64),
            Err(MultiQubitBraidError::StepLimit { limit: 64 })
        );
        assert_eq!(
            compile_multiqubit_braid_with_limit(4, &operation, 65)
                .unwrap()
                .steps
                .len(),
            65
        );
        // Kills: an empty word returning Ok with a non-identity action.
        let empty = compile_multiqubit_braid_with_limit(4, &[], 0).unwrap();
        assert_eq!(empty.steps.len(), 0);
        assert_eq!(empty.gate_count, 0);
        assert_eq!(empty.action, MajoranaBraidAction::identity(16).unwrap());
        assert!(matches!(
            compile_multiqubit_braid_with_limit(4, &operation, 0),
            Err(MultiQubitBraidError::StepLimit { limit: 0 })
        ));
    }

    #[test]
    fn invalid_operations_fail_before_evaluation() {
        // Kills: collapsing every refusal into one error variant.
        assert_eq!(
            compile_multiqubit_braid(0, &[]),
            Err(MultiQubitBraidError::InvalidQubitCount)
        );
        assert_eq!(
            compile_multiqubit_braid(usize::MAX, &[]),
            Err(MultiQubitBraidError::InvalidQubitCount)
        );
        assert_eq!(
            compile_multiqubit_braid(
                2,
                &[MultiQubitOperation::Phase {
                    qubit: 3,
                    inverse: false
                }]
            ),
            Err(MultiQubitBraidError::InvalidQubit {
                qubit: 3,
                num_qubits: 2
            })
        );
        assert_eq!(
            compile_multiqubit_braid(
                2,
                &[MultiQubitOperation::Cnot {
                    control: 1,
                    target: 1
                }]
            ),
            Err(MultiQubitBraidError::EqualControlTarget)
        );
        assert_eq!(
            compile_multiqubit_braid(
                3,
                &[MultiQubitOperation::Swap {
                    first: 1,
                    second: 3
                }]
            ),
            Err(MultiQubitBraidError::NonAdjacentSwap)
        );
        assert!(matches!(
            compile_multiqubit_braid(
                2,
                &[MultiQubitOperation::Elementary {
                    index: 8,
                    inverse: false
                }]
            ),
            Err(MultiQubitBraidError::Braid(BraidActionError::BraidIndex {
                index: 8,
                count: 8
            }))
        ));
    }

    #[test]
    fn multiqubit_braid_scaling_up_to_16_qubits_64_modes() {
        let counts = [2usize, 4, 8, 12, 16];
        let rows = benchmark_multiqubit_braid_scaling(&counts).unwrap();
        assert_eq!(rows.len(), counts.len());
        for (&nq, row) in counts.iter().zip(rows.iter()) {
            assert_eq!(row.num_qubits, nq);
            assert_eq!(row.mode_count, 4 * nq);
            // Each block swap takes 16 steps; routing + unrouting across (nq - 2) swaps + 1 bridge
            assert_eq!(row.cnot_steps, 32 * (nq - 2) + 1);
            assert!(row.inverse_restores_identity);
        }
    }

    #[test]
    fn multiqubit_braid_scaling_matches_cross_language_json_fixture_bit_for_bit() {
        let counts = [2usize, 4, 8, 12, 16];
        let rows = benchmark_multiqubit_braid_scaling(&counts).unwrap();
        let serialized = multiqubit_braid_scaling_to_canonical_json(&rows).unwrap();
        let fixture =
            include_str!("fixtures/multiqubit_braid_scaling.json").replace("\r\n", "\n");
        assert_eq!(
            serialized.as_bytes(),
            fixture.as_bytes(),
            "Rust benchmark_multiqubit_braid_scaling JSON output drifted from cross-language fixture"
        );
        let round_trip = multiqubit_braid_scaling_from_canonical_json(&fixture).unwrap();
        assert_eq!(round_trip, rows);
    }
}
