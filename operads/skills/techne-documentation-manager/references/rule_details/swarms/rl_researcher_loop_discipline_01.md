# Detailed definition: Research Loop Discipline (WF_RESEARCH_PFP) (1)

**AuthorityEffect:** None.

Parent: [Research Loop Discipline (WF_RESEARCH_PFP)](../../../../../rules/swarms/rl_researcher_loop_discipline.md). Load for the matching predicate, not every task.

# Rule: Research Loop Discipline (WF_RESEARCH_PFP)

**AuthorityEffect:** None.

The research loop is controlled by the Rust module `omega_woland::research_loop`
and invoked via Woland swarm specialization (`/woland --specialization research` or `/woland`).
The workflow contract is
`omega_engine_education/documentation/004_oepfp/workflows/research/researcher_workflow.pfp.yaml`.
Each invariant below names the test that fails when it is broken; the rules-as-code register
records those tests.

---

## 1. The Host Decides (`RULE_RESEARCH_LOOP_HOST_DECISION_001`)

1. Stage 5 is evaluated by the host. No model or IDE agent occurrence may be reserved or
   recorded for it.
2. The disposition is computed from host facts: check records, review bindings, the stall
   key and the ledger. A stage 8 recommendation is advisory and is never read as a terminal.
3. Every disposition projects onto `omega_types::routing::RoutingTerminal`, and the
   projection is recorded because it loses the disposition's name.

## 2. One Budget, Never Reset (`RULE_RESEARCH_LOOP_BUDGET_CEILING_001`)

1. Every dispatch reserves its worst case before anything is sent, keyed by the
   occurrence's idempotency key. A failed attempt is charged; an unknown outcome stays
   charged; a request that never left the host returns tokens and cost but still counts.
2. Rounds, retries, child dispatches, resumes and prompt revisions never reset the ledger.
3. `max_cost_microusd = 0` disables paid dispatch: a priced reservation is refused, and the
   provider transport refuses a zero ceiling before reading a key or opening a socket.

## 3. Reviews Bind Exact Bytes (`RULE_RESEARCH_LOOP_REVIEW_BINDING_001`)

1. Stage 4 freezes the candidate by digest. The host evaluation and both critics bind that
   digest; a critic of other bytes is refused.
2. A route against a changed candidate, source snapshot or checker policy is stale and opens
   a recheck; stale green is never accepted.

## 4. Evidence Before PASS (`RULE_RESEARCH_LOOP_EVIDENCE_001`)

1. A host check is PASS, FAIL or UNKNOWN. PASS names at least one evidence reference.
2. Missing evidence is UNKNOWN; it is neither a PASS nor a counterexample.

## 5. Stalls End the Run (`RULE_RESEARCH_LOOP_STALL_001`)

1. The stall key is the required claims, the unresolved residuals and the verified evidence.
   Reformatting, longer prose or a new confidence score leave it unchanged.
2. The same key for `max_stalled_rounds` rounds ends the run as an open obstruction, ahead of
   budget exhaustion.

## 6. Raw Output Is Kept (`RULE_RESEARCH_LOOP_RAW_CUSTODY_001`)

1. Every provider reply, success or error, is written once to the run folder before it is
   parsed. A second write of different bytes under the same name is refused.
2. A response that fails to parse or fails its schema is recorded as a failed attempt, not
   dropped.

## 7. Contract and Controller Agree (`RULE_RESEARCH_LOOP_PACK_PARITY_001`)

1. The workflow folder's default limits, required mission fields, routing names, stage
   executors, nine-packet prompt family and response schemas match the controller.
2. The response-schema validator supports a closed keyword set and refuses any other keyword
   at compile time.

## 8. Hermetic Task Scope and Zero Cross-Task Evidence Borrowing (`RULE_RESEARCH_LOOP_HERMETIC_TASK_EVIDENCE_001`)

1. A task or evaluation loop must never borrow, inherit, or reuse test digests or pass receipts from a prior or foreign task; every candidate must execute the verification suite freshly against its own frozen candidate bytes.
2. A task that adopts an antecedent's PASS_TO_MASTER receipt or test digest without fresh local execution on the evaluated candidate bytes is refused and classified as `TASK_EVIDENCE_BORROWING_LEAK`.

---

## Cross-References

- Base swarm and model mediation: [`rl_woland_base_swarm_specialization.md`](../../../../../rules/swarms/rl_woland_base_swarm_specialization.md).
- Routing and authority axes: [`../authority/rl_gtla_rules_rubric.md`](../../../../../rules/authority/rl_gtla_rules_rubric.md).
- Antibody admission: [`../architecture/rl_immune_antibody_and_verification_hygiene.md`](../../../../../rules/architecture/rl_immune_antibody_and_verification_hygiene.md).
