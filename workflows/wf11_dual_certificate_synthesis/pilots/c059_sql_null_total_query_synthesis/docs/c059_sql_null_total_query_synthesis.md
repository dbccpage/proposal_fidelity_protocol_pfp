# C059: SQL Synthesis under Three-Valued-Logic Fences

**AuthorityEffect:** None. **Status:** planned. **Domain:** f_program_synthesis. **Tier:** T2.
**Budget:** $0.50 billed inference per arm. **Models:** open weights, at most 70B total
parameters. **Protocol:** [SG-CP v1](../01_challenge_protocol.md).

## 1. Challenge

> Use the existing Symbol Game and models no larger than 70 billion parameters to synthesize a frozen compiler from relational specifications to SQL whose queries return exactly the specified bags on hidden NULL-adversarial databases, with totality preflights and null-safe comparisons, for under $0.50.

## 2. Why This Task

SQL's three-valued logic hides errors, and it does so quietly:

- `NULL <> 1` is `UNKNOWN`, so a `WHERE a <> b` filter drops exactly the rows a reconciliation must find;
- `x NOT IN (subquery)` returns nothing once the subquery contains a `NULL`;
- a left join followed by a `WHERE` on the right-hand column silently becomes an inner join.

The repository's rule (`.claude/rules/relational_contract_and_exact_math_discipline.md` §3) requires a totality preflight on protected operands and `IS DISTINCT FROM` for pointwise disagreement. Checking a query on a given database is cheap: run it and compare bags. Writing a spec-to-SQL compiler that never trips on `NULL` is where models fail.

This stresses the Symbol Game's typed residuals, such as "3 rows missing, every missing row has `a` NULL". It stresses the OEWAS (Omega Engine Workflows, Agents, Skills) sampling-and-selection step, and the OEEIS (Omega Engine Epistemic Immune System) against the `<>` antimorphism. A pass shows instance-level agreement on hidden databases. It is not a proof of query equivalence, which is undecidable for full SQL. Containment is decidable for conjunctive queries under set semantics (Chandra & Merlin 1977).

## 3. Formal Problem and Bounds

A specification is a JSON relational-algebra tree over a declared schema, with explicit Kleene three-valued semantics. Node types:

- `select`, `project` and `rename`;
- `join` (inner or left);
- `anti_join` (with `match: "null_safe"` or `match: "sql_not_in"`);
- `semi_join`;
- `group` with `count_star`, `count_col`, `sum`, `min`, `max`;
- `union_all` and `distinct`;
- predicates `eq3`, `distinct`, `not_distinct`, `is_null`, `and`, `or`, `not` and `coalesce`.

A spec may declare `protected` columns. The output must then include a preflight query that returns every row with a NULL in any protected column, as the rule requires.

The dialect is the subset shared by the pinned SQLite and DuckDB versions, which are hashed at packet-build time. Division and `AVG` are excluded, because the engines differ and the results would be inexact. `ORDER BY` is excluded, and results are compared as bags. Output column types are `INTEGER` and `TEXT` only. Specs have at most 12 nodes; databases have at most 6 tables and 200 rows.

The hidden databases must contain:

- NULLs in join keys;
- NULLs inside `NOT IN` subqueries;
- NULLs in grouping columns (they group together);
- all-NULL groups (`SUM` is NULL, `COUNT(col)` is 0);
- empty tables;
- duplicate rows;
- rows where `eq3` is `UNKNOWN`.

## 4. Deliverable and Output Contract

**Mode: frozen module.** `def solve(case: dict) -> dict` is synthesized by the model and makes no model calls at scoring. It returns SQL text and never executes it; the judge executes it.

```json
{"case_id": "sq_ex_03", "schema": {"trace_fact": {"id": "INTEGER NOT NULL", "F_value": "INTEGER", "global_verdict": "INTEGER", "local_product": "INTEGER"}}, "spec": {"op": "select", "from": "trace_fact", "where": {"distinct": [{"col": "global_verdict"}, {"col": "local_product"}]}, "project": ["id"]}, "protected": ["F_value", "global_verdict", "local_product"]}
{"case_id": "sq_ex_03", "status": "SOLVED", "sql": "SELECT id FROM trace_fact WHERE global_verdict IS DISTINCT FROM local_product", "preflight_sql": "SELECT * FROM trace_fact WHERE F_value IS NULL OR global_verdict IS NULL OR local_product IS NULL", "null_ledger": [{"node": "where.distinct", "construct": "IS DISTINCT FROM"}]}
{"case_id": "sq_ex_08", "status": "OUT_OF_SCOPE", "witness": {"reason": "UNKNOWN_COLUMN", "path": "spec.where.eq3[1]"}}
{"case_id": "sq_ex_09", "status": "UNKNOWN", "code": "UNSUPPORTED_NODE"}
```

An answer is complete when both queries parse in both engines, the main query's result bag equals the reference bag on every hidden database in both engines, and the preflight's result bag equals the reference preflight bag. Each `null_ledger` entry names a construct actually present in the SQL. The judge compares bags with null-safe tuple equality, where `NULL` matches `NULL`.

## 5. Participant Packet

- `TASK.md` with the spec grammar, the Kleene truth tables, the dialect subset and the JSON Schema. It quotes rule §3 verbatim.
- 12 public cases, each with its spec, 2 public databases, and exact expected result bags and SQL: the preflight example above; `NOT IN` against null-safe anti-join; a left join with a right-side filter; `COUNT(*)` against `COUNT(col)`; `SUM` over an empty group; grouping on a nullable key; `distinct` on duplicates; `coalesce`; De Morgan under three-valued logic; an unknown column; an unsupported node; a three-node join chain.
- `runner.py`, which executes the SQL in both pinned engines inside the sandbox.
- `accounting.json`.

## 6. Judge Packet

- **Hidden base:** 36 specs, each with 5 hidden databases: 3 random and 2 constructed to be NULL-adversarial for that spec.
- **Relabel and gauge controls:** 12. Tables and columns renamed, rows shuffled, duplicate rows injected (bags must scale), and equivalent spec trees (commuted `and`, De Morgan rewrites, which are valid in Kleene logic). Verdicts must match their base.
- **Poisoned but schema-valid:** 8. `note` fields recommending `<>` or `NOT IN`, columns described as never NULL in a note but nullable in the schema, a protected column that is NULL in exactly one hidden row, and a spec whose `anti_join` asks for `sql_not_in` semantics, so that `NOT EXISTS` would be wrong.
- **Exact checker:** execution in both pinned engines, compared with a reference bag from an independent Rust evaluator of the spec that implements three-valued logic explicitly.
- **Independent second checker:** a Python spec evaluator by a different author. Engine-versus-evaluator disagreement pauses scoring.
- **Mutation suite:** the judge's comparison code must reject all of the following, and must itself use null-safe comparison: a query using `<>` where `distinct` was specified; `NOT IN` where `null_safe` was specified; a missing preflight; a preflight missing one protected column; `COUNT(col)` for `count_star`; `UNION` for `union_all`; a comparator in the judge itself that uses `=` (it drops NULL rows and must be caught).

## 7. Arms and Baselines

Arms A to D follow the protocol. **Arm E** is a deterministic spec-to-SQL compiler written by the operator from `TASK.md`, with fixed emission rules per node, and no model. Because the specification language is formal, E is expected to be perfect, and a tie with E is the expected ceiling. What this spec measures is whether synthesis reaches null-correct emission. Arm F is not in the catalog row.

## 8. Budget, Models and Provenance

$0.50 per arm, about 1.4 million tokens at the Q40 blended rate ([review](../00_q40_review.md)). Candidate models: `meta-llama/llama-3.3-70b-instruct`, `qwen/qwen3-30b-a3b`, `deepseek/deepseek-r1-distill-llama-70b`. The receipt binds both engine versions and hashes.

Q40 harness defects this spec closes: (1) schema and verbatim examples in every prompt; (2) every repair turn carries the task, the schema, the full module, the failing spec, and the missing and extra rows; (3) at least 4 candidates per turn in A, and best-of-N in D; (4) u09 sandbox only; the engines run there too; (5) pre-call `BudgetController`; (6) checker exceptions pause scoring.

## 9. Pass Gates and Statistics

- **Capability gate:** in at least 2 of 3 seeds, all 36 base specs pass on all 5 databases in both engines, all controls are consistent, and every poisoned case is handled.
- **Primary metric (pre-registered):** base specs fully passed. The test is an exact McNemar test on paired (seed, spec) rows for A vs B, A vs C and A vs D, with Holm correction at α = 0.05.
- **Reported alongside:** the per-construct failure counts (`<>`, `NOT IN`, outer-join filter, aggregate NULLs).
- **Seeds:** 3.

## 10. Interpretation

The per-construct breakdown is the useful output. If A eliminates `<>`/`NOT IN` failures faster than B, typed row-level residuals help. If all arms keep failing on `sql_not_in` specs, models over-apply the null-safe fix, which is an antimorphism in the other direction. Passing on hidden databases is evidence of correctness on those databases only.

## 11. OEEIS, Attention, Logit and Scratch-Space Hooks

The catalog declares no OEEIS hook. Observed mechanisms:

- **Danger gate.** Signal 1 is a `note` recommending a construct; Signal 2 is a row-count mismatch whose missing rows all contain NULL.
- **Thymus-style self panel.** The public NULL-adversarial databases act as a self panel that every candidate must pass before freezing.
- **Expected antimorphisms:**
  - AM-5 (`=` and `<>` treated as two-valued);
  - AM-3 (preflight omitted);
  - AM-4 (the same `NOT IN` query resubmitted).
- **Layer 2:** a grammar mask restricting SQL to the dialect subset and forbidding `<>` on columns the schema marks nullable, via `carrier_gbnf` or `logit_bias_ban` in `omega_engine_symbol_game/domain/carrier_decoding.py` (unwired). A mask is steering, not a proof, so execution decides.
- **Layer 1:** not applicable.
- **Scratch space:** the host keeps, per public case, the missing and extra rows with their NULL pattern.

## 12. Run Folder, DDC Trace and Operand Mining

Expected Discrete Deformation Calculus (DDC) pattern: `C`, `Λ` (one emission rule per node type), `I`, `R` (bag differences), `D` steps, `E`, `T`. `M` records `UNSUPPORTED_NODE`. The `ObstructionScore` sets Φ₁ to the size of the bag symmetric difference summed over public databases and engines, and `active_count` to ledger-lint violations (for example, `<>` on a nullable column where `distinct` was specified). Γ₂ is unused (0).

Operands to mine:

- `distinct` on nullable columns emits `IS DISTINCT FROM`;
- a null-safe anti-join emits `NOT EXISTS`, and `NOT IN` is used only when the spec asks for it;
- emit the protected-column preflight first;
- a right-side filter after a left join goes into the `ON` clause unless the spec says otherwise.

## 13. Estate Reuse and Prerequisites

- `.claude/rules/relational_contract_and_exact_math_discipline.md` §3, mirrored in `.agents/rules/`, which states the preflight and null-safe comparison requirements.
- The catalog row lists no code reuse. The spec evaluator is new Rust work.
- Upgrades: [U01](../../upgrades/u01_symbol_game_run_folder_mandate.md), [U02](../../upgrades/u02_intelligence_metabolism_mining.md), [U03](../../upgrades/u03_ddc_prime_trace_instrumentation.md), [U05](../../upgrades/u05_engine_turn_driver.md), [U06](../../upgrades/u06_governed_provider_path.md), [U07](../../upgrades/u07_challenge_packet_runner.md), [U08](../../upgrades/u08_matched_arms_harness.md), [U09](../../upgrades/u09_sandboxed_execution_seam.md), plus the row extra [U10](../../upgrades/u10_synthesis_loop_v2.md).

## 14. Claim Hygiene

- **Supports:** a named model synthesized a frozen compiler whose queries matched the reference bags on all hidden databases, in both engines, for k of 36 specs, with the required preflights.
- **Does not support:** query equivalence in general, correctness on other databases, or dialects beyond the declared subset.
- **Narrowest defensible claim:** on these specs and hidden NULL-adversarial databases, null-correct synthesis succeeded in s of 3 seeds, with per-construct failure counts X.
- **Next test:** conjunctive-query specs where the judge also checks equivalence symbolically (Chandra & Merlin containment), and a third engine.
