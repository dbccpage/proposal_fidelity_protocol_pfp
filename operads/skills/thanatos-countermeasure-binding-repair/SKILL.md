---
name: thanatos-countermeasure-binding-repair
description: "Use when a countermeasure reference must resolve. Closes the gap between corpus defense uids and the registry."
families: [oecog]
operad_source_colours: ["Contract", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# thanatos-countermeasure-binding-repair

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L3_logos_thanatos`

## When to use

Before any `immune_countermeasures` declaration is trusted, and whenever a new
agent manifest is added -- every manifest must name countermeasures that
resolve, or the `REQUIRED` gate is checking spelling.

## Inputs

- `basis_cognitive_exploits.jsonl` `countermeasure_uids`
- `.../cognitive_warfare_defense_registry.json` (exactly 6 defenses)
- `cognitive_warfare_gate.py`

## Protocol

1. Collect every distinct `defense:*` uid the corpus references.
2. Resolve each against the registry.
3. For each unresolvable uid, produce **one** of two dispositions, never a
   silent third: a registry entry proposal carrying a real `evidence_path`, or
   an explicit `UNBOUND` record stating why no defense exists.
4. Emit the receipt. Registry admission is a human act.

## The finding

The corpus names **12 distinct `defense:*` uids. The registry holds 6. The two
sets are completely disjoint.** Every `countermeasure_uids` entry in a
12,398-record catalog currently resolves to nothing, while the gate that reads
them reports a total partition -- because it partitions manifests by whether
they *declare* the keys, not by whether the declarations resolve.

The six that do exist: `anti_collusion_isolation`,
`clean_architecture_inward_gate`, `disjoint_lineage_quorum_audit`,
`farkas_certificate_check`, `lean4_axiom_whitelist_gate`,
`rate_limiting_circuit_breaker`.

## Terminals

`BOUND`, `UNBOUND`, `PROPOSED_REGISTRY_ENTRY`, `EVIDENCE_MISSING`.

## Nonclaims

A bound countermeasure is not a working one. This checks that a reference
resolves to a declared defense, not that the defense defends.
