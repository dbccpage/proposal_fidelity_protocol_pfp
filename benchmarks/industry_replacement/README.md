# Industry replacement benchmark (offline verification + prepared live campaign)

This directory compares six ways of running a coding model on four non-physics engineering tasks.

| arm | context | calls | regulation |
|---|---|---|---|
| `direct_baseline` | task prompt | 1 | none |
| `industry_all_skills_and_rules` | `AGENTS.md` (31 rules) + all 10 `SKILL.md` (~5,650 estimated tokens) | 1 | `AGENTS.md` `deny:` guardrails as a pre-commit hard block |
| `industry_coder_reviewer_loop` | same | 2 (draft, review) | same guardrails on the reviewed output |
| `direct_with_public_checks` (control) | task prompt | 1 + at most 1 repair | the same public host checks as PFP |
| `industry_with_ci` (control) | industry context | 1 + at most 1 retry | public host checks + `AGENTS.md` guardrails as a CI gate; the retry is told what failed |
| `pfp_eis_pciv_regulated` | task prompt + host facts + the PCIV-chosen skill genome (offline: no skills) | 1 + at most 1 repair | `pfp_core`: thymus-screened guards (Signal 1), public host checks (Signal 2) from allowlisted host observers, two-signal disposition, byte fences, whole-run budget |

The two controls were added after the independent audit (`audit_report.json`, finding F1). Before that, PFP was the only arm with public checks and a repair, so its gains could not be credited to `pfp_core`.

## Tasks

Each task in `tasks/` has a public prompt, a public host check and a sealed post-freeze grader in `sealed_evaluator/`.

1. `t1_api_refactor_under_contract`: refactor a payments ledger under a byte-fenced contract block and fixed signatures. 15 sealed edge-case tests.
2. `t2_sql_security_and_analytics_migration`: convert five string-built SQLite endpoints to parameterized SQL. Sealed: equivalence on 8 datasets plus injection payloads.
3. `t3_bloated_skill_repository_triage`: a multi-file config migration, with the industry stack present.
   - The stack has 2 relevant skills, 5 unrelated ones, 2 duplicates and 1 stale skill whose formatting rules conflict with the task.
   - The unrelated skills add about 3,860 estimated tokens, not the 6,000 the brief asked for.
4. `t4_stateful_protocol_synthesis`: a circuit breaker plus an outbox.
   - The host checks the transition table on every state and event pair.
   - Probe exclusivity, clock skew and recovery stay open obligations, so `final_output_certified` is always False.

## Commands

```
python -m pytest pfp_core benchmarks/industry_replacement dag/benchmark/test_anthropic_provider.py -q
python benchmarks/industry_replacement/run_offline_matrix.py      # writes offline_matrix_results.json
python benchmarks/industry_replacement/build_manifests.py         # writes manifest_{anthropic,openrouter}.json
python benchmarks/industry_replacement/run_live.py --manifest manifest_anthropic.json --admit <sha256 of file> --out <new dir>
```

The live command spends money. Run it only after the user authorizes that exact manifest digest.

- Each digest can be dispatched once. The record is kept in `.campaigns/`, which git ignores.
- No live call was made while building this directory, and spend was USD 0.

## Offline results (status `offline_policy_verification_not_live_llm_evidence`)

The solver is a fixture policy, not a model. Every arm sees the same candidate tiers per task, plus one exposure slot:

- faithful, verbose and format-quirky;
- contract or table drift, and injection-vulnerable;
- truncated and subtly buggy.

Primary policy `follows_context_rules`:

| task: correct / runs (estimated tokens) | direct | industry 1-call | reviewer loop | direct + checks | industry + CI | pfp |
|---|---|---|---|---|---|---|
| t1 | 4/7 (12.9k) | 4/7 (52.3k) | 6/7 (111k) | 6/7 (17.9k) | 6/7 (76.9k) | 6/7 (17.9k) |
| t2 | 4/7 (8.5k) | 4/7 (48.0k) | 6/7 (101k) | 6/7 (11.5k) | 6/7 (62.3k) | 6/7 (11.5k) |
| t3 | 4/6 (6.1k) | 3/6 (39.9k) | 5/6 (82.8k) | 5/6 (7.3k) | 5/6 (53.6k) | 5/6 (7.7k) |
| t4 | 4/7 (8.0k) | 4/7 (47.4k) | 6/7 (100k) | 6/7 (11.2k) | 6/7 (61.9k) | 6/7 (11.2k) |

Read the accuracy columns as consequences of declared assumptions. Every second call uses one `REPAIRABLE` map, whether it is a review, a repair or a CI retry: it fixes defects that are visible from the public task or the host evidence, and leaves hidden semantic defects alone.

## What this supports

- **The lever is public host checks plus one bounded repair, not EIS or PCIV.** Offline, `pfp_eis_pciv_regulated` equals `direct_with_public_checks` on every task and both policies, and a test asserts this.
  - The audit's ablation came to the same conclusion. Replacing thymus screening with "admit every guard" or "no guards" changes no PFP number.
  - The reason is that `decide()` holds only on host danger, so Signal 1 is diagnostic and never changes a delivery.
- **Context size is the second lever.** At equal correct counts, the arms that do not load the industry stack use about 14 to 23 percent of the tokens of `industry_with_ci`, and 9 to 16 percent of those of the reviewer loop. This comes from leaving out about 5.6k tokens of rules and skills per call, and from skipping a second call when checks pass.
- **What the mechanisms do on real code, under the declared assumptions:**
  - The thymus kills the `\bf"` guardrail in the SQL domain against the author-written safe-SQL panel, and keeps it elsewhere.
  - It kills the stale skill's snake_case lint rule against the v2 examples.
  - Lineage taint excludes every genome containing that skill.
  - The trace quotient merges the two duplicate skills.
  - The ledger holds the full quote on an ambiguous delivery and stops the campaign.
  - The byte fence rejects one-byte and zero-width edits.
  - Danger signals from non-host observers are ignored.
  - The sealed grader refuses code that can reach the harness.
- **Guardrail sensitivity.** Under the sensitivity policy `ignores_context_rules`, the industry guardrail refuses every t2 answer: 4 of 7 runs for one call, and 6 of 7 for the reviewer loop and for CI.
  - Those answers use allowlisted f-strings that the sealed grader accepts.
  - They are "false" refusals only with respect to the functional grader. The repository owner's rule ("Never build SQL with f-strings") forbids them, so judged against the owner's policy they are rule-compliant refusals (audit F3).
  - PFP delivers them because its thymus overrides the owner's rule on the strength of an author-written panel. That is a policy choice, not a neutral fact.
- **Budget fit.** Both adapters' conservative quotes fit two calls of the largest industry context under USD 0.10 per run for the pinned models. This was checked offline against recorded endpoint metadata.

## What it does not support

- **Live results:** any claim about live model accuracy, token use, cost or wall time.
- **That EIS, PCIV or the OPERADS quotient improve any outcome:** offline they change no delivery.
- **Skill benefit:** this is unmeasured. Offline fixtures do not depend on skill content, so no skill is ever selected and the PFP arm runs with no skills, no `AGENTS.md` prose, and the generic base instruction. It also receives the host-computed key list in t3, which `direct_with_public_checks` does not (audit F11).
- **"PFP refuses fewer correct answers":** PFP refused nothing at all offline, correct or not, so its zero false-refusal count says nothing about its discrimination.
- **That PFP catches hidden semantic bugs:** subtly buggy answers pass every public host check in all four tasks. In t1, the industry `float(` guardrail refuses a float-rounding bug that PFP delivers.
- **That a certified intermediate carries over to the final answer:** in t4 the exhaustive table check passes for an answer whose recovery and clock-skew behaviour is wrong.
- **That the sealed grader resists adversarial candidates:** the static tamper gate narrows the in-process forgery route but does not close it, and the public smoke checks have no such gate (audit F2).
- **That the byte fence blocks shadowing:** the fence protects bytes, not meaning; a frozen name can be redefined later in the module (audit F12).

## Narrowest defensible claim

On these fixture sets, under the declared solver, repair and exposure assumptions:

- adding the public host checks and one bounded repair raises the correct count from 4 to 6 of 7 (5 of 6 in t3), whichever context is used;
- leaving the industry rule and skill context out cuts estimated tokens by roughly 4 to 11 times at equal correct counts;
- the EIS and PCIV layers in `pfp_core` add nothing measurable here.

## Next test needed

1. Run the live campaign, after the user authorizes a manifest digest. The 24 runs per provider cover all six arms in randomized order.
2. Run repetitions, at least 5 per task and arm, to get distributions.
3. Test a skill genome taken from the `Unmeasured` reserve, so that skill benefit is measured.
4. Find a task where Signal 1 changes a decision. Without one, the EIS layer has no effect to measure.
5. Write new sealed holdouts after these results, because this controller designed the fixtures and has seen the sealed tests.

## Notes

- Offline pricing and latency use a declared simulation tariff: 1 and 5 microUSD per input and output token. The live adapters quote from pinned or observed prices.
- At 3 and 15 microUSD per token with conservative quotes, the reviewer loop's second call exceeds the USD 0.10 cap on the full industry context. That is why the manifests pin `claude-haiku-5-5` and `deepseek/deepseek-v3.2`.
- Candidate code runs only in `python -I` subprocesses. Offline fixtures are batch-graded in one process for speed; live grading uses one process per delivery.
