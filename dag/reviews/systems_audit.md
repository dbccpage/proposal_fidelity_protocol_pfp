Systems audit checkpoint at `8050c66900899771766f33e8f5fdd200b7dd9120`.

This audit remains in progress. EIS, PCIV and OPERADS provide bounded checks over supplied types, observations, signatures, fixtures and receipts; those checks do not establish detector completeness, observer independence, global equivalence or causal provenance. No implementation, test, catalog or historical receipt was changed.

The scope contains 2,529 Git-tracked files, excluding dot-prefixed directories and ignored caches. Full source-line semantic review covers 85 files: EIS 42, PCIV 26 and OPERADS 17. Another 2,443 files have mechanical structured content scans only; one binary has metadata review only. Parsing is not a semantic review. The JSON records each file's hash, actual level, declarations, dependencies and candidate evidence. All 2,444 remaining files are listed in `systems_semantic_backlog.json`.

Eight repair items are recorded, without fixes:

| ID | Priority | Finding and source |
| --- | --- | --- |
| SYS-BUG-001 | P2 | Singleton Pareto NameError: `pciv/use_cases/fitness.py:230-249,267-273`. |
| SYS-BUG-002 | P2 | NaN risk breaks residual associativity: `operads/skill_operad/domain/evidence.py:68-95,124-133`. |
| SYS-BUG-003 | P2 | Detector/signal equality disagrees with hashing: `eis/domain/value_objects.py:68-91,345-372`. |
| SYS-BUG-004 | P1 | Durable append silently succeeds after disk failure, losing the event on reopening: `pciv/infrastructure/event_log.py:245-303`. |
| SYS-BUG-005 | P2 | Lineage taint depends on edge input order: `pciv/use_cases/immunity.py:113-131`. |
| SYS-BUG-006 | P2 | Insertion before a protected span shifts only its end and falsely rejects preserved bytes: `pciv/use_cases/lamarckian_loop.py:203-217`. |
| SYS-BUG-007 | P2 | Default seeder root resolves above the repository: `eis/domain/pharmacy_seeder.py:45-50`. |
| SYS-BUG-008 | P2 | Five historical OPERADS receipt/source inventories contain conflicting duplicate JSON keys; exact occurrence lines are in the audit JSON. |

The first seven have normal-import finite reproductions in `systems_audit_probes.py` and `systems_audit_probe_results.json`. The eighth uses the parent's strict JSON scan in `duplicate_json_keys.json` plus source occurrence checks. Preserve original historical bytes; reconstruct custody and issue separately identified corrected records. Last-wins JSON parsing does not resolve the ambiguity.

EIS finite panel checks, exact allostery and finite support calculations depend on supplied observations and policy. Legacy admission and status queries differ from authenticated native custody; no authenticated-path bypass was demonstrated. Pharmacy templates are candidate strings, not measured repair witnesses.

PCIV cochain checking establishes the admitted exact matrix relation `d1*d0=0`, making admitted `phi1` zero; unmeasured curvature remains refused. Selection is metric-relative. Genealogy seals bind declarations without independently proving causality. Projection replay is an in-memory queue, and the current-prompt immunity adapter does not traverse ancestors. Elenchus checks selected lexical patterns, despite returning all PRIME rule identifiers on a pass.

OPERADS provides ordered colour-slot composition checks. Arbitrary callable behavior needs additional assumptions. HoTT-labelled paths are Python records, including string-representation endpoint collisions, not formal HoTT proofs. Residual/quotient records do not certify exactness, contractivity or promotion. Typed compilation checks declared source/capability/topology constraints, without executing or admitting a workflow. Realization checks are not a Rust compiler proof or remote signature scheme.

Validation is separated:

- Earlier HEAD `644d950a44c6387d7ebc669c098bf4de91168771`: four selected cochain/operad files, **36 passed in 1.57s**.
- Current HEAD: four selected EIS files, **50 passed, 1 failed in 0.72s**. Python 3.14 emits `PatternError:` where one test expects `error:`; the invalid pattern was safely refused.
- A separate current-head invocation had **two collection errors** from missing `operating_system` imports and provides no test outcomes.
- Interpreter: `.venv/Scripts/python.exe`. Current finite probes reproduce seven defects plus two limited observations. No full suite or native cryptographic/rank rerun was completed here.

The earlier-to-current scoped diff was 12 files, 32 insertions and 32 deletions; reviewed core algorithms were unchanged. Current hashes and resumed reads use the current HEAD. Remaining implementation, tests, catalog semantics, evaluator call paths and historical custody are explicit backlog, not completed review.
