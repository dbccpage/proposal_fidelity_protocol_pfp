---
title: "Governance Obstruction Packet — ODP adapter for governance / sprint work"
author: "Jeremy H. Carroll"
date: "2026-06-20"
status: "ADAPTER of core_obstruction_packet_standard.md for governance work."
---

packet_type: adapter
authority_effect: None
carrier: capabilities, people, tools, epics (C⁰)
primary_residual: unresolved residual backlog (Q¹)
in_scope_repairs: assign, schedule, route (d₀)
deferred_residuals: none
seal_condition: governance decision is a terminalized residual, lane-stamped `evidence_only`

Thesis
------

**Governance is not project management. It is obstruction routing.** A sprint item exists **only because it kills or routes a named residual** — never because "it seems like work to do."

Field mapping
-------------

| ODP field | Governance instance |
|-----------|---------------------|
| Carrier | the current program: capabilities, people, tools, epics |
| C⁰ | current capabilities, roles, tools, epics |
| d₀ | the permitted process move (assign, schedule, route) |
| C¹ | gaps, blockers, conflicts, missing validators |
| ZeroRel | "already covered by an existing capability/role" |
| B¹ = im(d₀) | gaps closable by an existing process/role |
| Q¹ = C¹/im(d₀) | the **unresolved residual backlog** |
| d₁ | cross-epic consistency |
| C² | the cross-epic coordination layer |
| Γ₂ | **coordination failure / cross-epic inconsistency** |
| Φ₁ | **irreducible priority mass** (what genuinely must be done) |
| observer / norm | the declared priority + capacity lens |
| Λ | add process, role, validator, contract, or sprint |
| DDA op | the recorded routing decision + what it preserved |
| terminal | **do** / **defer** / **refuse** / **split** / **escalate** |

Bindings
--------

* d₁ / Γ₂ exposers : `sentinel_councils` — Integrity Auditor (`judge`, abstain-when-blind), Adversary (`inspect`, adversarial revelation), Jester (entropy injection) are **operators that attempt to expose Q¹/Γ₂** — never judges of authority.
* closure check : `core_atlas_reconciliation::governance::check_governance_strict` (the 10-field `GovernanceRecord` — a distinct licensed-lift *type* with its own 10 fields, **not** the ODP's 15 fields — is a fully-declared Λ; role-power separation = the d₀/d₁ legality check).
* routing / enforcement : `Blackrod` routes a sealed residual to enforcement (defensive-only); it does not vote/waive — it moves an already-terminalized row.
* terminal seal : `core_sweep_kernel`/`core_certifiers` (a governance decision is a terminalized residual, lane-stamped `evidence_only` — NOT tower authority).

What a sprint item must declare (not a task)
--------------------------------------------

```text
residual:    <the named Q¹ / Γ₂ entry this item kills or routes>
move:        <d₀ repair | Λ lift (process/role/validator/contract/sprint)>
preserves:   <what the move does not break>
terminal:    do | defer | refuse | split | escalate
```

A canonical `GovernanceRecord` example of a sprint item is:

```yaml
residual: missing core_api /solve terminal row
move: add feature-gated Axum handler
preserves: no certifier path, no raw-text persistence
terminal: do
```

No item is admitted without a named residual. ("Make the first increment boring, executable, test-heavy" = keep d₀ small and the residual named.)

Terminal classification (governance)
------------------------------------

`do` = a residual with a licensed move now · `defer` = ClosedSurvivor routed to a later carrier · `split` = the residual decomposes (Q¹ factors) · `escalate` = OracleNeeded (needs operator/Council authority) · `refuse` = real obstruction, no licensed lift.

Promotion checklist (sprint epic / governance decision)
-------------------------------------------------------

carrier (program state)? · C⁰ (capabilities/roles)? · C¹ (gaps/blockers)? · d₀ (process move)? · ZeroRel? · Q¹ (residual backlog) declared/refused? · d₁/C² (cross-epic) or out-of-scope? · Φ₁/Γ₂ (priority/coordination mass, or estimate)? · Λ only if licensed? · terminal status? · DDA op (routing decision) recorded?
