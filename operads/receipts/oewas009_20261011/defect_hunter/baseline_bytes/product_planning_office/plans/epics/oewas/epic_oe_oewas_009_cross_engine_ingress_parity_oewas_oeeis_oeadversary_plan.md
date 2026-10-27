# Epic: Cross-engine evidence routing and disconnected-port refusal

**Epic ID:** `EPIC-OE-OEWAS-009`
**AuthorityEffect:** None
**Status:** `RESEARCH_HOLD`
**Implementation slice:** `IMPLEMENTED_BOUNDED` canonical storage projection and development cutover; native admission remains held.
**Reviewed:** 2026-10-10
**Owner:** OEWAS maintainers and dependency owners named below.

The [shared-review reconciliation](../../../receipts/epic_design_review_20261010.md) records the readable review and unavailable attachments. Full-scope readiness is held. The storage slice below is implemented; its source-matched execution claims belong to [migration evidence](../../../../workflows_agents_skills/receipts/oewas007_20261010/). Existing disconnected/native-admission tests remain separate evidence obligations.

## Source inspection and repaired obstructions

OEEIS is Engine Epistemic Immune System, not estate intelligence storage. [OeeisImmuneAdapter](../../../../adversary/infrastructure/estates/oeeis_immune.py) emits CANDIDATE antibodies and reads human-admitted guidance. [OewasAntiSkillAdapter](../../../../adversary/infrastructure/estates/oewas_anti_skill.py) holds without a verified immutable runtime snapshot; its source records that the Python loader is retired and no native detector host action is exposed yet.

[AdversarySwarm.run_bout](../../../../adversary/use_cases/base_swarm/adversary_swarm.py) already composes estate ports. [runtime composition](../../../../adversary/runtime.py) and [bout service](../../../../adversary/use_cases/bout_service.py) now consume canonical `_ic` default routes without an opt-in activation gate. Present malformed migration metadata still refuses. [OEWAS007](epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md) owns the real OEOS lease-aware development migration and [cutover runbook](../../../../workflows_agents_skills/documentation/intelligence_migration_v1.md); current development-data relocation is part of this PR and its exact scope is bound by the cutover inventory/Git-blob crosswalk. Full native/admission parity does not follow from folder relocation.

## Bounded contract and dependency decisions

First public ports: `OewasAntiSkillAdapter.evaluate(stage, subject)` and `probe(scratch_root)`. Input: a PROPOSAL/NONE subject with distinct producer/verifier identities and no runtime. Output: HOLD/disconnected; missing keys produce ANTI_SKILL_SUBJECT_INVALID. Oracle: typed disposition/registry identity and independently observed zero bout/provider calls through production `run_bout`.

OEWAS009 owns PRE_DISPATCH/PRE_SEAL correlation and routing. OEWAS006/native detector owner must expose trusted runtime; governance binds registry/profile/checker trust; OEEIS owns human admission. Until then the positive native admission arm is blocked explicitly. The implemented storage projection pairs selected real producers with canonical default route selection and readers: Adversary bundles, SymbolGame run recording, durable collector state, OEOS custody composition and digestion discovery. Historical collector locators/event/work identities stay unchanged for verified inventoried bundles; new outputs use their canonical locators. Portable binding under `_ic/odni/migrations/oewas007` and exact snapshots under `_ic/nara/historical/oewas007` preserve old receipt bytes when current journals change or original directories move. See the [migration decision](../../decisions/adr_20261010_oewas_intelligence_migration.md). Full routing closure still requires every real producer/write and consumer/readback, failed-storage residuals and source-matched native execution; folder existence alone is insufficient.

## Obstruction review and TDD test plan

**Independent oracle for these slices:** typed disposition/registry identity and independently observed zero bout/provider calls through production `run_bout`.

Candidate: `adversary/tests/spine/test_cross_engine_disconnected_contract.py`.

1. **RED → minimal GREEN:** invoke actual adapter without runtime at both stages; require HOLD/disconnected and no registry claim. Missing keys require typed Err. Reuse existing GREEN hold behavior, never add a pass-through fallback; refactor only after the test.
2. **RED → minimal GREEN:** run the actual composed swarm with `fixture_mode=False` in temporary custody with no verified runtime. Require refusal/hold before provider dispatch. A call observer may count dispatches; a stub returning CLEAR cannot replace the real anti-skill evaluator. Change only a demonstrated composition bypass.
3. **RED → minimal GREEN:** after trusted native runtime exists, transplant runtimeA's registry/profile evidence to taskB and require refusal. Positive control uses B's independently verified evidence. Send an actual failure to OEEIS, read back CANDIDATE custody with matching run/task correlation; storage failure surfaces a residual without silently changing the bout verdict.

The delivered [test_ic_routed_producers.py](../../../../operations/tests/intelligence_digestion/test_ic_routed_producers.py) is the selected storage integration seam; reuse it instead of adding a duplicate generic cross-engine harness. It must cover canonical-default writer/reader pairs with no marker, old locator identity/idempotency, refusal on present malformed migration metadata and missing/tampered portable historical mappings. Readback after canonical-journal mutation must use the bound original snapshot, not substitute current bytes. Its first RED/GREEN records are retained in the migration evidence directory; final expanded/native evidence must pin the executed source and binary. Full three-engine admission and broader producer coverage remain residual acceptance work. An empty directory walk is not production evidence.

| Theoretical minimum | Obligation |
| --- | --- |
| INVARIANT | Disconnected or misbound evidence cannot create CLEAR/admission or native dispatch. |
| BREAK | Convert unbound HOLD to CLEAR or transplant another task's profile evidence. |
| WITNESS | Adapter/composed swarm retain hold with zero dispatch. |
| MUTATION | Linked adapter missing-runtime probe branch and `run_bout` PRE_DISPATCH decision are inspected targets. Bypass hold and require RED; no live mutation executed. |

Examiner controls: future bound-runtime positive (1), malformed subject (2), cross-task transplant (3), disconnected-as-CLEAR falsifier (4), real swarm/candidate persistence and mutation (5). Missing native support blocks the positive arm, never silently skips it.

### Execution and evidence discipline

Use the explicitly invoked [ext-mattpocock-tdd skill](../../../../.agents/skills/ext-mattpocock-tdd/SKILL.md). Its current entry declares a Code-to-Code operation; the concrete sequence above is this plan's local design. Observe one behavior test RED, implement minimal GREEN, then refactor with adjacent controls. Already-GREEN behavior is reuse, not fabricated RED. The disconnected/native-admission sequence above remains proposed acceptance work. The implemented storage slice has separate actual RED/GREEN evidence; do not relabel its finite routing controls as native admission.

Run from repository root after authoring the named candidate file:

```powershell
${env:PYTEST_DISABLE_PLUGIN_AUTOLOAD} = '1'
& 'C:/Users/a343o/.local/bin/uv.exe' run --offline --no-project --python 'C:/Users/a343o/AppData/Roaming/uv/python/cpython-3.13.11-windows-x86_64-none/python.exe' --with pytest==9.1.1 --with pyyaml==6.0.3 --with pydantic==2.13.5 --with numpy --with scipy --with networkx --with sympy --with blake3 python -X utf8 -m pytest -o 'addopts=' -o 'filterwarnings=' adversary/tests/spine/test_cross_engine_disconnected_contract.py --basetemp (Join-Path $env:TEMP ('oewas009-' + [guid]::NewGuid().ToString('N'))) -q
```

Four-stage route: DOC_MGR pins bytes/UTF-8/links; DEV_MGR with Syntax Prefilter/Scope Guard binds the public port and budget; QA_MGR/Inspector run one-to-three files per batch and at most three repair attempts; BUILDER checks invariant/falsifier and Adversary adjudicates recorded evidence, preserving Defect Hunter dissent. Rust work uses one crate and `-j 1`. SoftwareQaReceiptV1 requires its actual schema/writer; this Markdown is not one.

## Claim discipline

- Supports: implemented canonical defaults, selected storage relocation and historical identity/readback seams; separately specified disconnected/native-admission controls.
- Does not support: full implementation completion, arbitrary future-estate migration automation, complete producer/native parity, automatic detector admission or a mathematical theorem.
- Narrowest claim: selected storage routes now consume the OEWAS007 transition without changing detector custody; trusted native admission needs separate evidence.
- Next evidence: seal source-matched storage/native receipts and the actual development cutover/blob ledger; retain the unavailable positive admission arm until its trusted host and independent admission evidence exist. Preserve Defect Hunter dissent: containment metadata and selected writer tests cannot establish all-producer parity or grant CLEAR/admission.

Cross-epic ownership and retained custody follow the [integration decision](../../decisions/adr_20261010_epic_integration_ownership.md).
