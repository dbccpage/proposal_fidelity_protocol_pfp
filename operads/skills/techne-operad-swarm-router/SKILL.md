---
name: techne-operad-swarm-router
description: "Find minimal-residual composition paths for multi-agent tasks and check type matching at each handoff."
families: [oecog, orchestration]
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
---

# techne-operad-swarm-router

**Status:** `NOT_SUPPORTED`  
**AuthorityEffect:** `None`  
**Council:** `L3_logos_techne`  
**Retirement Notice:** Standalone swarm routers are retired under `RULE_WOLAND_BASE_SWARM_SPECIALIZATION_001`. All multi-agent deliberation, routing, and task decomposition are executed via `OmegaEngineWolandSwarm` and `/woland` SPOE dispatch with narrowed specialization profiles.

## When to use (Deprecated)

This skill is deprecated. Use `/woland` with appropriate `--swarm-type` or `--specialization` profile instead.
transitions between distinct agent roles and artifact boundaries.

## Inputs

- Initial state colour $c_{\text{in}} \in \mathcal{C}$ from the 10 canonical colours.
- Target goal colour $c_{\text{goal}} \in \mathcal{C}$.
- Operad catalog and signature definitions from `operad_signature.json`.
- Residual weight threshold $\epsilon_{\text{max}}$.

## Protocol

1. Load the active operadic signature graph containing colours, identities, operations, and agent scope bindings.
2. Model the workflow request as a path search over the multicategory coloured operad graph.
3. Compute the composition chain $\mu = P_k \circ \dots \circ P_1$ minimizing cumulative residual cost.
4. Verify colour compatibility at each transition interface: $\text{target}(P_i) = \text{source}_j(P_{i+1})$.
5. Reject cyclic deadlock loops or ungrounded colour jumps.
6. Emit a structured execution receipt defining subagent routing order and typed artifact handoffs.

## Terminals

`PATH_FOUND`, `NO_ADMISSIBLE_PATH`, `TYPE_MISMATCH_OBSTRUCTION`.

## Nonclaims

Operadic routing establishes type compatibility and path admissibility under declared signatures;
it does not forecast runtime latency or ensure model convergence on open-ended creative tasks.
