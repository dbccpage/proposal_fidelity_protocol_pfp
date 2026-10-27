Core DDA Agent Workflow Packet
===============================

packet_id: core_dda_agent_workflow
schema: core.agent_work.v1
evidence_ceiling: AuthorityEffect::None
status: operational finite-lane contract

Scope
-----

This packet governs watched agent proposals for fixed finite F2 cochain
carriers. It operationalizes GTOC/GTLA checks only inside the declared work
packet. It does not prove GTOC-1..8 globally.

The author proposes two bounded Symbol Game forms and a DDA trace. Trusted Rust
programs parse the forms, reconstruct the cochain segment, verify d1*d0=0,
recompute every per-defect diagnostic, check each operation law, render any Rust
test deterministically, and produce the terminal receipt. Model-requested
classification is advisory and never copied into trusted receipt fields.

Active DDA Operations
---------------------

V1 admits only fixed-carrier E, R, I, M, and T.

* E must land in Exact for the affected defect.
* R must preserve irreducible residual mass.
* I and M are inert on the carrier state.
* T is inert and requires zero closure defect.
* M is a typed refusal and mints no authority.

C, D, and Lambda are not licensed in v1. The current verifier checks that those
letters restructure a carrier but does not machine-check the GTOC-3
preservation, non-destruction, and terminalizer witnesses. Any such operation,
or any external import, therefore routes to OracleNeeded.

Packet Bundle
-------------

A work item declares packet_refs at queue time. The host compares the bundle
with the packet registry read from the base commit and emits sorted Packet-Ref
trailers. A model cannot add, remove, or replace packet references.

Review And Terminalization
--------------------------

Claude is an untrusted bounded author. Codex is an independent I3 reviewer.
P0-P2 findings in correctness, security, packet, GTOC, or GTLA categories
block terminalization and permit at most two repairs. P3 findings are recorded.

Trusted Rust maps results as follows:

| DDA result | Host state | authority_effect |
| --- | --- | --- |
| ExactRepair | PromotionReady | None |
| StabilizedSurvivor, when allowed | PromotionReady | None |
| OpenObstruction | Paused | None |
| Typed refusal | Refused | Refused |
| Import or unlicensed lift | OracleNeeded | None |

PromotionReady is not Completed. Dependencies remain blocked until a human
records PromotionRecorded for the exact commit.

Nonclaims
---------

* GTOC-1..8 are not globally proved.
* No CertifiedAuthority is minted.
* Agent artifacts have AuthorityEffect::None.
* A PromotionReady commit is evidence awaiting human promotion.
* Symbol admission proves grammar and budget conformance only.
