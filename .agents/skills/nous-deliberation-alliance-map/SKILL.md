---
name: nous-deliberation-alliance-map
description: "Use before convening a simulated council. Reads the council social graph to flag echo chambers and capture risk."
families: [oecog]
operad_source_colours: ["Ledger", "Paper"]
operad_target_colour: "Ledger"
operad_arity: 2
operad_residual: "unknown"
---

# nous-deliberation-alliance-map

**Status:** `CANDIDATE`
**AuthorityEffect:** `None`
**Council:** `L2_nous`

## When to use

Before a simulated council session, bout, or review panel is convened, and
afterwards when a session produced suspiciously fast agreement.

## Inputs

- `.../_sap/ana_001_social_graph_v1.0.yaml` -- 1,952 edges: 556 `mentor`,
  313 `anti_mentor`, 490 `council_colleague`, 593 `role_guild`
- `.../_sap/ana_002_actor_skill_binding_v1.0.yaml`

## Protocol

1. Project the proposed seat list onto the graph.
2. Report three shapes:
   - **echo chamber** -- a seat majority sharing one mentor lineage;
   - **standing conflict** -- an `anti_mentor` pair seated together without a
     third party who is neutral to both;
   - **guild capture** -- one `role_guild` holding a blocking share.
3. Propose the minimal seat change that breaks the dominant shape.

## Why this exists

`social_graph.py` generates this file and **nothing consumes it.** A 1,952-edge
map of who mentored, opposed, and served beside whom is the strongest available
predictor of how a simulated deliberation will fail, and it has never been read.

The estate's `defense:disjoint_lineage_quorum_audit` and
`defense:anti_collusion_isolation` are exactly the countermeasures this map
would inform.

## Terminals

`INDEPENDENT`, `ECHO_CHAMBER`, `STANDING_CONFLICT`, `GUILD_CAPTURE`.

## Nonclaims

A clean map does not make a deliberation sound; a flagged one does not make it
wrong. This measures structure, not the quality of any argument made within it.
All actors are synthetic.
