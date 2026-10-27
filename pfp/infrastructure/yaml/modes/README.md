# The Twenty Canonical Modes of The Symbol Game (PFP v0.2)

**AuthorityEffect:** None.

This directory formalizes the operational modalities of the Proposal Fidelity Protocol (PFP). Each mode represents an explicit substrate, verification contract, and set of rules governing how proposals are evaluated, rewritten, steered, or refused.

## Five Mode Clusters

```
                     ┌── Cluster I: Carrier & Representation (Modes 1, 2, 6, 15)
                     ├── Cluster II: Internal & Attention Steering (Modes 3, 4, 5)
The Twenty Modes ────┼── Cluster III: Group & Cochain Structure (Modes 7, 8, 12, 13)
                     ├── Cluster IV: Dialectical & Adversarial (Modes 10, 11, 14, 16, 17, 20)
                     └── Cluster V: Foundational Mechanization (Modes 9, 18, 19)
```

## Mode Catalog and Extended Specifications

| Mode ID | Name | Cluster | Primary Contract & Extended Specification |
|---|---|---|---|
| **01** | Hieroglyphics & Glyph Alphabets | Carrier & Representation | [`contract.yaml`](mode_01_hieroglyphics_and_glyph_alphabets/contract.yaml) · [`wire_representations.md`](mode_01_hieroglyphics_and_glyph_alphabets/wire_representations.md) |
| **02** | Packets & Sealed Envelopes | Carrier & Representation | [`contract.yaml`](mode_02_packets_and_sealed_envelopes/contract.yaml) · [`packet_architecture.md`](mode_02_packets_and_sealed_envelopes/packet_architecture.md) |
| **03** | Attention Head & Logit Steering | Internal Steering | [`contract.yaml`](mode_03_attention_head_and_logit_steering/contract.yaml) |
| **04** | Epistemic Antibody Injections | Internal Steering | [`contract.yaml`](mode_04_epistemic_antibody_injections/contract.yaml) |
| **05** | Skill Injection & Operad Morphisms | Internal Steering | [`contract.yaml`](mode_05_skill_injection_and_operad_morphisms/contract.yaml) |
| **06** | CoT Scratchpad Boundary Probes | Carrier & Representation | [`contract.yaml`](mode_06_cot_scratchpad_boundary_probes/contract.yaml) · [`boundary_probe_contracts.md`](mode_06_cot_scratchpad_boundary_probes/boundary_probe_contracts.md) |
| **07** | S(n) Permutation & Braid Equivariance | Group & Cochain Structure | [`contract.yaml`](mode_07_sn_permutation_and_braid_equivariance/contract.yaml) |
| **08** | Discrete Cochain Involutions | Group & Cochain Structure | [`contract.yaml`](mode_08_discrete_cochain_involutions/contract.yaml) |
| **09** | Lean 4 Proof Kernel Elaboration | Foundational Mechanization | [`contract.yaml`](mode_09_lean4_proof_kernel_elaboration/contract.yaml) |
| **10** | Cemetery DAG Mining (Playing the Dead) | Dialectical & Adversarial | [`contract.yaml`](mode_10_cemetery_dag_mining/contract.yaml) |
| **11** | Adversary Adversarial Tribunal | Dialectical & Adversarial | [`contract.yaml`](mode_11_adversarial_tribunal/contract.yaml) · [`collision_tribunal_spec.md`](mode_11_adversarial_tribunal/collision_tribunal_spec.md) |
| **12** | Simplicial Carrier Representation | Group & Cochain Structure | [`contract.yaml`](mode_12_simplicial_triangulation_and_regge/contract.yaml) · [`carrier_support_spec.md`](mode_12_simplicial_triangulation_and_regge/carrier_support_spec.md) |
| **13** | Normal Form Confluent Chase (0NF $\to$ 6NF) | Group & Cochain Structure | [`contract.yaml`](mode_13_normal_form_confluent_chase/contract.yaml) · [`relational_chase_and_saturation.md`](mode_13_normal_form_confluent_chase/relational_chase_and_saturation.md) |
| **14** | Fail-Closed Typed Refusal | Dialectical & Adversarial | [`contract.yaml`](mode_14_fail_closed_typed_refusal/contract.yaml) · [`typed_refusal_evidence.md`](mode_14_fail_closed_typed_refusal/typed_refusal_evidence.md) |
| **15** | Interactive TUI / REPL Live Board | Carrier & Representation | [`contract.yaml`](mode_15_interactive_tui_repl_board/contract.yaml) |
| **16** | 4E Cognitive Autopoiesis | Dialectical & Adversarial | [`contract.yaml`](mode_16_4e_cognitive_autopoiesis/contract.yaml) |
| **17** | Polygraph Confluence Consensus | Dialectical & Adversarial | [`contract.yaml`](mode_17_polygraph_confluence_consensus/contract.yaml) · [`polygraph_confluence_audit.md`](mode_17_polygraph_confluence_consensus/polygraph_confluence_audit.md) |
| **18** | MUB(6) Moduli Variety | Foundational Mechanization | [`contract.yaml`](mode_18_mub6_moduli_variety/contract.yaml) |
| **19** | Genesis First-Cut Marking | Foundational Mechanization | [`contract.yaml`](mode_19_genesis_first_cut_arb/contract.yaml) |
| **20** | Multi-Agent Debate & Oversight | Dialectical & Adversarial | [`contract.yaml`](mode_20_multi_agent_debate_oversight/contract.yaml) |

## Related Subsystems

- **Component Reuse ADR:** [`../rewriting/adr_reuse_decision.md`](../rewriting/adr_reuse_decision.md)
- **Demo 001 Benchmark Suite:** [`../demos/demo_001/README.md`](../demos/demo_001/README.md)
- **Manifest:** [`modes_manifest.yaml`](modes_manifest.yaml)
- **Schema Contracts:** [`mode_types.yaml`](mode_types.yaml) and [`mode_models.yaml`](mode_models.yaml)

## Typed Contracts

- [`mode_catalog.py`](mode_catalog.py): Typed twenty-mode catalog: `ModeCluster`, `ModeCatalogEntry`, `ModeCatalog` (ids 1..20 once, cluster-consistent); `load_mode_catalog` cross-checks every `contract.yaml`.
- [`mode_catalog.yaml`](mode_catalog.yaml): Register data matching the Pydantic model.
