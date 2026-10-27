PaperFOC000c Claim-Packet Boundary Evidence
===========================================

Evidence id: `PAPER000C-CLAIM-PACKET-AUTHORITY-BOUNDARY`

This table binds the same authority boundary across the four DDA alignment domains. The boundary is: representation-layer marks or traces have no authority unless they descend to Primitive Difference, Structure, or typed refusal.

| Obligation | Rust evidence | Lean evidence | Python evidence | Contract evidence | Paper evidence |
| --- | --- | --- | --- | --- | --- |
| Stable boundary id | `PAPER000C_CLAIM_PACKET_EVIDENCE_ID`; `test_claim_packet_evidence_id_is_stable` | `paper000cClaimPacketEvidenceId`; `paper000cClaimPacketEvidenceId_eq` | `PAPER000C_CLAIM_PACKET_EVIDENCE_ID` printed by the demo | `required_substrings` and `required_tests` in `discrete_deformation_algebra.contract.yaml` | PaperFOC000c Section 1 |
| Representation-only packets carry no authority | `ClaimPacket::require_authority`; `test_representation_only_claim_has_no_authority` | `primitive_claim_no_authority_without_descent` | `ClaimPacket.require_authority` refusal in `PaperFOC000c Claim Packet Boundary` demo section | L-DDA-37 | PaperFOC000c Section 1 and Section 5 |
| Typed refusal terminalizes without positive authority | `ClaimPacket::require_terminalized`; `test_typed_refusal_terminalizes_without_authority` | `refused_primitive_packet_terminalizes_as_typed_refusal`; `budget_unknown_primitive_packet_terminalizes_as_typed_refusal` | `typed_refusal_packet.require_terminalized()` and `has_authority == False` | L-DDA-38 and L-DDA-42 | PaperFOC000c Section 5 |
| Descent plus authoritative status grants authority | `ClaimPacket::require_authority`; `test_authority_requires_descent_and_authoritative_status` | `repaired_primitive_packet_claim_has_authority`; `stabilized_survivor_claim_has_authority_of_descent` | `descended_packet.require_authority()` and `has_authority == True` | L-DDA-39 and L-DDA-41 | PaperFOC000c Section 2 and Section 6 |
| Open no-rule primitive packet does not become ontology authority | no Rust minting path; non-authoritative terminal status branch | `open_no_rule_packet_has_no_authority` | refusal branch remains representation-layer only | L-DDA-43 | PaperFOC000c Section 5 |

Verification commands used for this evidence set:

```text
lake build PrimitiveAxiomatics SentinelBoundary
cargo test -p core_discrete_deformation_algebra --all-targets
cargo test -p core_contracts --test dda_file_contract_gate --quiet
python -m py_compile .\engine\.cosmology\lambda_interaction_demo.py
python .\engine\.cosmology\lambda_interaction_demo.py
```
