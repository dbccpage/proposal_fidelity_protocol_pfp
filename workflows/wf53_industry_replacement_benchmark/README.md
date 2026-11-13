# WF53: Industry replacement benchmark

**Status:** runnable offline (policy verification only); live campaign prepared, not run. **Kind:** experiment design. **Builds on:** [WF12](../wf12_mechanism_control_arms/README.md), [WF14](../wf14_immune_failure_classification/README.md).

**Goal:** Compare six ways of running a coding model (plain, industry skills and rules, coder-reviewer loop, public checks, CI gate, PFP with two-signal regulation) on four non-physics engineering tasks.

**The check:** each task's public host check online; a sealed grader in [`sealed_evaluator/`](sealed_evaluator/) after outputs are frozen.

**Run it offline:**

```powershell
python -m pytest pfp_core workflows/wf53_industry_replacement_benchmark workflows/wf52_finite_qm_benchmark/test_anthropic_provider.py -q
python workflows/wf53_industry_replacement_benchmark/run_offline_matrix.py
```

This folder was `benchmarks/industry_replacement/` until 2026-11-13; older records keep that path. `test_branch_touches_only_allowed_paths` fails on any branch that moves a file listed in `dag/file_inventory.json`.

## Details

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
python -m pytest pfp_core workflows/wf53_industry_replacement_benchmark workflows/wf52_finite_qm_benchmark/test_anthropic_provider.py -q
python workflows/wf53_industry_replacement_benchmark/run_offline_matrix.py      # writes offline_matrix_results.json
python workflows/wf53_industry_replacement_benchmark/build_manifests.py         # writes manifest_{anthropic,openrouter}.json
python workflows/wf53_industry_replacement_benchmark/run_live.py --manifest manifest_anthropic.json --admit <sha256 of file> --out <new dir>
```

**Live execution requires an isolated sandbox.** `run_live.LIVE_EXECUTION_ENABLED` is `True`.

A real campaign checks for a sandbox before anything is recorded, and refuses to start if neither is available:
- **Vercel Sandbox** is preferred. It needs a `VERCEL_TOKEN`.
- **Docker** with the pinned image is the fallback.

Once a sandbox is found, every candidate runs in it (see *Vercel Sandbox backend* and *Container backend* below).

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
- **That candidate execution is sandboxed at the OS level:** it is not. See "Candidate execution" below.
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
- Each offline matrix run starts with empty caches. The committed results are produced with parallel prewarming. The test suite recomputes them with `--no-prewarm` (sequential, one fresh process per check) and requires identical output.

## Candidate execution and grading (after the PR #62 review)

**One candidate per process (review finding 1).**
- Each candidate runs in its own fresh `python -I -B` process in its own temporary directory.
- The earlier single-process batch is gone: it could reuse a previous candidate's bytecode and attribute that candidate's result to the next one.
- Prewarming now means running independent processes in parallel.
- Recomputing the full matrix without prewarming gives byte-identical results, and no committed count changed against the previous commit.

**Jail (review finding 2).** The child process:
- gets a scrubbed environment, with no provider keys or user variables;
- runs under an audit-hook jail, installed before the candidate is imported, which refuses:
  - writes outside its directory;
  - reads outside its directory and the Python installation;
  - sockets, process creation and ctypes;
  - frame and garbage-collector introspection;
  - SQLite files;
- is killed, with its whole process tree, past a 1 MB output cap or a timeout.

This is an in-process boundary, not an OS sandbox:
- native code or interpreter bugs can defeat it;
- memory is not capped on Windows.

That is why live execution stays disabled.

**Verdicts outside the candidate (review finding 3).**
- Sealed tests are scenarios: the child receives inputs and operations only, and returns one observation per operation.
- The parent holds every expected value and builds the verdict.
- Patching `json`, `print`, `stdout` or `atexit`, or writing a second result line, can no longer produce a pass. The forgery from the review is a regression test.

**Typed failures (review finding 4).**
- A worker result is accepted only if it is exactly one `@@RESULT@@` line that parses and matches the caller's schema. Anything else becomes a typed error.
- A host-side exception inside a run is recorded as `HARNESS_FAILURE`, with its ledger spend, and stops the campaign. Freeze and summary files are still written.

**Output ceiling (review finding 5).**
- `max_output_tokens` must be an int in [1, 4000] at admission.
- That value is passed to every stage's request.

**Custody (review finding 6).** Manifests now bind:
- every repository file imported by the live path, computed in a fresh interpreter (pfp_core, both providers, the budget ledger, the EIS/PCIV/OPERADS modules, the harness and the sealed scenarios);
- the planning-time endpoint price observation.

## Second review of PR #62 (fixes on top of main)

1. **Result channel.**
   - The candidate's process no longer has a usable `emit`.
   - The driver body runs inside a function that receives a per-run key on stdin before the candidate is imported. The key stays in that function's frame and in a local closure that is never handed to candidate code.
   - Each result line carries an HMAC-SHA256 of its body, computed with `_hashlib.hmac_digest` and `repr`, both captured before import.
   - The parent accepts exactly one line that authenticates. Other result lines are counted as `forged_lines` and ignored.
   - Replacing `__main__.emit` or writing a fake result line no longer changes the observation.
   - Results are still labelled `observation_source: candidate_process`. Candidate code can still tamper with the driver's own helpers, for example builtins used to normalize values, so these are not independently certified host observations. An OS boundary remains the fix, and live execution stays disabled.
2. **Write detection.**
   - The jail now reads the integer `flags` of the `open` audit event: `O_WRONLY`, `O_RDWR`, `O_CREAT`, `O_TRUNC`, `O_APPEND`, `O_EXCL`.
   - A write through `os.open` inside a read-only root is refused. The test uses a synthetic read-allowed root.
3. **Admission custody.**
   - `build_manifests.py` is now inside the bound closure.
   - `run_live.verify_custody` hashes every file the manifest names directly, without running the discovery code.
   - It requires the admission files (`run_live.py`, `build_manifests.py`) to be bound.
   - It refuses any discovered dependency the manifest does not name.
4. **Timeout caching.** The timeout is now part of the cache key, and timeout outcomes are never cached.
5. **Authorization scope.**
   - A non-empty `pfp_skill_genome` is refused at admission.
   - There is one registry, `.campaigns/`, with no command-line override. A digest is dispatched at most once per checkout. That is not a cross-machine guarantee.

## Container backend (OS-enforced boundary)

You can run candidates in throwaway Docker containers instead of host processes. Set `PFP_SANDBOX=container`, or set `tasks.sandbox.BACKEND = 'container'`. The default is still `process`.

**What each candidate container gets:**
- the pinned image `python:3.12-slim`, referenced by digest in `CONTAINER_IMAGE` and never pulled during a run;
- no network: only the `lo` interface exists;
- a read-only root filesystem, every Linux capability dropped, `no-new-privileges`, and user `65534`;
- memory capped at 256 MB with no swap, 1 CPU, 64 processes, and 256 open files;
- the candidate's files mounted read-only, then copied into a 16 MB tmpfs `/work`, the only place it can write besides a 4 MB `/tmp`;
- no host environment: only the image's own variables plus `PYTHONHASHSEED` and `PYTHONIOENCODING`.

**Limits and cleanup:**
- The candidate is killed at the time limit inside the container (`timeout -s KILL`).
- If the container hangs, the host force-removes it.
- Every container runs with `--rm`, so none are left behind.

The audit-hook jail still runs inside the container as a second layer.

`tests/test_container_sandbox.py` runs the escape attempts with the jail switched off. This shows the container holds on its own. The tests cover:
- network access;
- host files, the Docker socket, and secret environment variables;
- writes outside `/work`;
- filling the scratch disk;
- fork bombs;
- a 1 GB allocation;
- hangs, including a check that no container is left behind;
- output floods.

They are skipped when Docker or the pinned image is not available.

**Measured on Windows 11 with Docker Desktop on WSL2:**
- about 0.6 s per candidate;
- the whole offline matrix (37 containers) runs in about 15 s;
- the results are byte-identical to the process backend.

`run_live.require_isolated_sandbox()` uses this backend for live campaigns when Vercel Sandbox is unavailable. Offline runs and tests keep the host `process` backend unless `PFP_SANDBOX` is set.

## Vercel Sandbox backend (cloud micro-VM)

Set `PFP_SANDBOX=vercel` to run each candidate in its own throwaway Vercel Sandbox VM. Live campaigns prefer this backend. Docker Desktop was too heavy to keep running on the development machine, so this backend moves the boundary off it entirely.

**What each candidate VM gets:**
- the pinned image `vercel/sandbox/universal@sha256:…`, which has Python 3.14;
- 1 vCPU and 2 GB, and it is non-persistent;
- `networkPolicy: deny-all`, so there is no outbound traffic at all, even as root inside the VM;
- shell limits: 512 MB address space per process, 32 MB per file, and 256 open files;
- a time limit enforced by Vercel, which kills the candidate with SIGKILL;
- an output cap enforced by the host, which stops reading;
- a stop in a `finally` block, with the VM's own timeout as the backstop.

**The token stays on the host:**
- The runner reads `VERCEL_TOKEN` from the environment, or from `PFP_ENV_FILE` or the repository's git-ignored `.env`.
- The token never enters the VM.
- Optional: `PFP_VERCEL_PROJECT` (default `pfp-sandbox`) and `PFP_VERCEL_TEAM`.

`tests/test_vercel_sandbox.py` runs the escape attempts against the cloud VM with the jail switched off. It covers:
- network access, including `sudo curl` to huggingface.co;
- secrets and host files;
- a fresh VM for every run;
- file size;
- memory;
- a fork bomb;
- hangs;
- output floods.

The tests are skipped without a token.

RLIMIT_NPROC is set but not enforced inside the VM. A fork bomb is contained by the 1-vCPU VM and the time limit instead.

**Measured:**
- about 2 s per candidate;
- the offline matrix runs in about 50 s, at 8 VMs at a time (Hobby allows 10 at once);
- the results are byte-identical to the process backend.
