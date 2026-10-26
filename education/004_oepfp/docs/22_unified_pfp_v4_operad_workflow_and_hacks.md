# Finite-QM PFP: prompt, stages and execution mode

AuthorityEffect: None. Revised 2026-10-18 after the initial registry-dump design
was rejected. These three linked YAML files are the delivery:

- [prompt_template.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/prompt_template.yaml): actual system and user prompts for doing a derivation, with the mathematical operad toolbox, four mining missions, certificate construction and output instructions.
- [workflow.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/workflow.yaml): stage instructions, inputs, outputs, checks, transitions and answer-free repair guidance.
- [mode.yaml](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm/mode.yaml): one `FINITE_QM_DERIVATION` mode with budgets, provider policy and six attached LLM techniques.

The [copyable system prompt](../_how_to_play/v4_operad_container_and_p_star_loop/finite_qm_pfp_system_prompt.md)
is rendered from the template. The source catalog remains a separate
lookup asset. It is never appended to the system prompt. Registered software
skills and mathematical operad families are distinct objects.

Source check (2026-10-22, pin `305b9690f97fc3f5c13e361cfe752a6d5dc7ad8d`): `workflow.yaml` declares six stages (`P0_MINE_OPERAD` to `P5_RECORD`, entry P0, terminal P5); `mode.yaml` sets `max_candidate_attempts: 2` and lists six techniques `H1_POPULATE_BEFORE_EXECUTE`, `H2_DECOY_EQUATIONS`, `H3_WITNESS_FIRST`, `H4_C4_DIAGNOSTIC`, `H5_FRESH_CONTEXT_RESIDUAL_REPAIR` and `H6_MASKED_SECOND_VIEW`; [finite_qm_operad_catalog.json](../../../../omega_engine_pfp/infrastructure/yaml/prompts/finite_qm_operad_catalog.json) has 744 `entries`. P1 lists H1 to H4. The 2026-10-20 figure of 584 is historical.

## Count one family, then the catalog

A **catalog entry** is one name recorded from a pinned source collection. It is a lookup row. It does not license a call, prove a theorem, or measure a model.

The file's `coverage.counts` lists twelve families. Read one family before the total. The family `qm_prompt_family` has 336 rows. The family `skill_operation` has 234 rows. Those two families are 336 + 234 = 570 rows.

The other ten families are `documented_name` 25, `host_guard` 8, `host_operation` 15, `identity` 10, `literature` 65, `native_type` 12, `pilot_family` 6, `qm_binding` 30, `runtime_operation` 1, and `template_family` 2. Their sum is 174. The catalog total is 570 + 174 = 744.

**Check.** A note that stops at 570, or that still says 584, fails. 570 leaves out ten families. 584 does not equal 744.

### Spoken segment

About 40 seconds. One idea: 336 and 234 are not the whole catalog. No screen is required.

"The prompt family has three hundred thirty-six entries. The skill family has two hundred thirty-four. Together that is five hundred seventy. The whole catalog has seven hundred forty-four entries. Five hundred seventy is not seven hundred forty-four. The old count of five hundred eighty-four fails the same check."

### Video beats

Worked example: 336 + 234, then the remaining 174.

| Time | On screen | Narration |
| --- | --- | --- |
| 00:00 | qm prompt family 336 | The prompt family has three hundred thirty-six entries. |
| 00:10 | skill operation 234 | The skill family has two hundred thirty-four. |
| 00:18 | sum 570 | Together that is five hundred seventy. |
| 00:26 | catalog 744 | The whole catalog has seven hundred forty-four entries. |
| 00:34 | 570 is not 744 | Five hundred seventy is not seven hundred forty-four. The old count of five hundred eighty-four fails the same check. |

## Stages

`P0_MINE_OPERAD -> P1_DERIVE -> P2_VERIFY -> P4_CHALLENGE -> P5_RECORD`

A repairable candidate failure goes through `P3_REPAIR -> P2_VERIFY`. The mode
allows two candidate attempts. A missing required checker, checker disagreement,
unresolved billing or exhausted budget stops dependent generation.

| Stage | Work performed |
| --- | --- |
| P0 Mine | Fill missing M1 carrier, M2 operations, M3 relations/decoys and M4 certificate contracts from the actual target and sources. |
| P1 Derive | Construct the mathematical witness or counterexample now; no inventory or plan as a substitute. |
| P2 Verify | Check bound raw bytes, applicable cochain conditions, domain witness, countermodel and import/anchor scope. |
| P3 Repair | Fresh request with the original inputs and bounded failing-invariant guidance; return a complete replacement certificate. |
| P4 Challenge | Attack the fragile step with a concrete near miss or reversible second representation; host-check the challenge and a valid control. |
| P5 Record | State the supported result, checked certificate, remaining obstruction and next mathematical step. |

The gate IDs in this workflow name local checking groups. Existing native and
numbered-runtime gate/stage identities are unchanged.

## Mode and LLM techniques

`FINITE_QM_DERIVATION` attaches:

1. **Populate before execute:** fill the four missions before a dependent derivation.
2. **Decoy equations:** expose a plausible wrong reduction and the mathematical law that rejects it, without printing the sought answer.
3. **Witness first:** request a small checkable construction and its required equations instead of an unconstrained essay.
4. **C4 diagnostic:** use a tree/chord calculation for an applicable cochain task or separately scored diagnostic.
5. **Fresh-context residual repair:** resend original public inputs plus whitelisted failing-invariant guidance; no raw judge secrets or chat-history accumulation.
6. **Masked second view:** when a reversible representation exists, solve and transport the same problem under different labels.

The mode defines attachment points, activation conditions and checks for each
technique. Their general effectiveness remains an experimental question. The
historical [M3 evidence audit](../_how_to_play/v4_operad_container_and_p_star_loop/m3_decoy_ablation_and_empirical_evidence.md)
explains why scaffolded extraction percentages are not clean derivation evidence.

## Focused integration

The existing shared PFP task-turn boundary compiles the template for P1 derivation
and P3 repair. The offline CLI selects those stages, fills the user prompt and
binds the selected operations. The native cochain adapter checks submitted
certificates; it does not compare them with a stored solution. Other domain
judges are supplied by their owners.

P0 mining/review and P4 challenge use the workflow as research instructions.
A new automatic six-stage live provider runner is not part of this focused
integration. Existing PFP provider, budget and stage owners remain responsible
for live dispatch. No provider call is made by these offline commands.

See the [practical guide](../_how_to_play/v4_operad_container_and_p_star_loop/how_to_play_v4_operad_pfp.md)
and [validation report](../_how_to_play/v4_operad_container_and_p_star_loop/validation_report.md).

## Claim hygiene

Supports: an actual prompt template, connected workflow and mode, and tested
preparation/repair/checking integration. Does not support: measured optimality,
automatic execution of every research stage, or derivation of QM foundations.
Narrowest claim: these artifacts direct candidate derivations and check the
submitted finite certificate. Next test: one unpaid finite-QM obligation with
an independent checker and a matched answer-free baseline.
