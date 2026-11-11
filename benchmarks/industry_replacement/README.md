# Industry replacement benchmark (offline verification + prepared live campaign)

This directory compares four ways of running a coding model on four non-physics engineering tasks:

| arm | context | calls | regulation |
|---|---|---|---|
| `direct_baseline` | task prompt | 1 | none |
| `industry_all_skills_and_rules` | `AGENTS.md` (31 rules) + all 10 `SKILL.md` (~5,650 estimated tokens) | 1 | `AGENTS.md` `deny:` guardrails as a pre-commit hard block |
| `industry_coder_reviewer_loop` | same | 2 (draft, review) | same guardrails on the reviewed output |
| `pfp_eis_pciv_regulated` | task prompt + host facts + PCIV-selected skills | 1 + at most 1 repair | `pfp_core`: thymus-screened guards (Signal 1), public host checks (Signal 2), two-signal disposition, byte fences, whole-run budget |

Tasks (`tasks/`), each with a public prompt, a public host check and a sealed post-freeze grader (`sealed_evaluator/`):

1. `t1_api_refactor_under_contract`: refactor a payments ledger under a byte-fenced contract block and fixed signatures. 15 sealed edge-case tests.
2. `t2_sql_security_and_analytics_migration`: five string-built SQLite endpoints to parameterized SQL. Sealed: equivalence on 8 datasets plus injection payloads.
3. `t3_bloated_skill_repository_triage`: multi-file config migration with the industry stack present (2 relevant skills, 5 unrelated, 2 duplicates, 1 stale skill with conflicting formatting rules). The unrelated skills add about 3,860 estimated tokens, not the 6,000 the brief asked for.
4. `t4_stateful_protocol_synthesis`: circuit breaker plus outbox. The host checks the transition table on every state and event pair. Probe exclusivity, clock skew and recovery stay open obligations, so `final_output_certified` is always False.

## Commands

```
python -m pytest pfp_core benchmarks/industry_replacement dag/benchmark/test_anthropic_provider.py -q
python benchmarks/industry_replacement/run_offline_matrix.py      # writes offline_matrix_results.json
python benchmarks/industry_replacement/build_manifests.py         # writes manifest_{anthropic,openrouter}.json
python benchmarks/industry_replacement/run_live.py --manifest manifest_anthropic.json --admit <sha256 of file> --out <new dir>
```

The live command spends money. Run it only after the user authorizes that exact manifest digest. No live call was made while building this directory, and spend was USD 0.

## Offline results (`offline_matrix_results.json`, status `offline_policy_verification_not_live_llm_evidence`)

The solver here is a fixture policy, not a model. Every arm sees the same candidate tiers per task: faithful, verbose, format-quirky, contract or table drift, injection-vulnerable, truncated and subtly buggy, plus one exposure slot. Under the primary policy `follows_context_rules`:

| task | direct | industry 1-call | industry reviewer | pfp |
|---|---|---|---|---|
| t1 correct / runs | 4/7 | 4/7 (1 correct refusal) | 6/7 | 6/7 |
| t2 | 4/7 | 4/7 | 6/7 | 6/7 |
| t3 | 4/6 | 3/6 | 5/6 | 5/6 |
| t4 | 4/7 | 4/7 | 6/7 | 6/7 |
| tokens, t1 (simulated tariff) | 12.9k | 52.3k | 111k | 17.9k |

Read the accuracy columns as consequences of declared assumptions, not as measurements. The reviewer and PFP repair both use one `REPAIRABLE` map: a second call fixes defects visible from the public task or host evidence, and leaves hidden semantic defects alone. Under that map the two arms reach the same accuracy by construction. Their difference in this setting is cost: the reviewer always spends a second call over the full skill context, while PFP spends one only on a host danger signal.

## What this supports

* The mechanisms run end to end on real code, under the declared assumptions:
  * the thymus kills the `f"` guardrail in the SQL domain, where it fires on safe allowlisted SQL, and keeps it in the other domains;
  * it kills the stale skill's snake_case lint rule against the v2 examples;
  * lineage taint excludes every genome containing that skill;
  * the trace quotient merges the two duplicate skills;
  * PCIV demotes arms dominated by the direct baseline;
  * the whole-run ledger holds the full quote on an ambiguous delivery and stops the campaign;
  * the byte fence rejects one-byte and zero-width edits.
* Under the sensitivity policy `ignores_context_rules`, the industry `f"` guardrail refuses correct SQL answers (4 false refusals out of 7 runs for one call, 6 for the reviewer loop). PFP has no false refusals in any task under either policy.
* Both adapters' conservative quotes fit two calls of the largest industry context under USD 0.10 per run for the pinned models. This was checked offline against the recorded endpoint metadata.

## What it does not support

* Any claim about live model accuracy, token use or cost. Skill benefit is unmeasured: the offline fixtures do not depend on skill content, so PCIV keeps the relevant skills in the `Unmeasured` reserve and runs PFP with no skills.
* That PFP catches hidden semantic bugs. It does not. Subtly buggy answers pass every public host check in all four tasks. In t1 the industry `float(` guardrail refuses a float-rounding bug that PFP delivers: the EIS rule match is diagnostic only, with no host danger.
* That a certified intermediate carries over to the final answer. In t4 the exhaustive table check passes for an answer whose recovery and clock-skew behaviour is wrong.

## Narrowest defensible claim

On these four fixture sets, under the declared solver, repair and exposure assumptions, `pfp_core` regulation:

* delivered the same correct-answer count as the industry reviewer loop with about 9 to 16 percent of its estimated tokens;
* had zero false refusals, against up to 6 of 7 runs in t2 for the static industry guardrails under the sensitivity policy;
* blocked no correct answer that the public host checks could tell apart.

## Next test needed

The live campaign, run only once the user authorizes a manifest digest: both manifests, all 16 runs each, randomized order, followed by repetitions (at least 5 per task and arm) to get distributions. After that, a PFP genome with the relevant skills drawn from the `Unmeasured` reserve, so that skill benefit is actually measured. Then new sealed holdouts written after these results, because this controller designed the fixtures and has seen the sealed tests.

## Notes

* Offline pricing and latency use a declared simulation tariff of 1 and 5 microUSD per input and output token. The live adapters quote from pinned or observed prices.
* At a tariff of 3 and 15 microUSD per token, with conservative quotes, the reviewer loop's second call exceeds the USD 0.10 cap on the full industry context. This is why the manifests pin `claude-haiku-5-5` and `deepseek/deepseek-v3.2`.
* Candidate code runs only in `python -I` subprocesses. Offline fixtures are batch-graded in one process for speed. Live grading uses one process per delivery.
