"""Record exact command navigation changes and scoped migration documentation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
ROOT = Path.cwd()
OUT = ROOT / 'workflows_agents_skills/receipts/oewas007_20261010/planning_default_ic'
OLD = b'product_planning_office.use_cases.prior_art_epic_audit'
NEW = b'product_planning_office.infrastructure.prior_art_sources'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def preserve(path, raw, family):
    target = OUT / family / path.relative_to(ROOT)
    assert not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return target.relative_to(ROOT).as_posix()
changes = []
for path in sorted((ROOT / 'product_planning_office/plans/epics').rglob('*.md')):
    raw = path.read_bytes()
    if OLD not in raw: continue
    before = preserve(path, raw, 'command_navigation_before')
    revised = raw.replace(OLD, NEW)
    path.write_bytes(revised)
    assert revised.replace(NEW, OLD) == raw
    changes.append({'path': path.relative_to(ROOT).as_posix(), 'before_path': before,
                    'before_sha256': sha(raw), 'after_sha256': sha(revised),
                    'replacement_count': raw.count(OLD), 'scope': 'Only the executable audit module path; no research, lifecycle or acceptance change.'})
assert len(changes) == 33 and sum(p['path'].endswith('/README.md') for p in changes) == 1
(OUT / 'command_navigation.json').write_bytes((json.dumps({'authority_effect':'None',
    'integrated_main_revision':'d47c98402a42fd189acd7cf6ccd23d7a0d09c120',
    'old_module':OLD.decode(), 'new_module':NEW.decode(), 'epic_documents':32,
    'index_documents':1, 'changes':changes}, indent=2, sort_keys=True)+'\n').encode())
def update(relative, old, new):
    path = ROOT / relative
    raw = path.read_bytes()
    assert raw.count(old.encode()) == 1, relative
    preserve(path, raw, 'integrated_documentation_before')
    revised = raw.replace(old.encode(), new.encode())
    assert b'\r' not in revised
    path.write_bytes(revised)
update('product_planning_office/plans/decisions/adr_20261010_oewas_intelligence_migration.md',
'Other explicit routes preserve `core_paper_reviews` under INR; `code_reviews`, `coverage` and `documentation` under NRO; `omc_dags` under NGA; and `blackrod` under FBI. A complete Adversary bundle is stored once under DARPA; agency placement does not create a confidentiality classification, actor license or detector admission. Consumers needing another view refer to the same stored bundle.',
'The final closed route map has 24 explicit keys. In addition to the table, `_adversary` and `symbol_game` use DARPA; `events` uses NSA; `narratives`, `unified_oe_trace.jsonl` and `universal_narrative_stream.md` use ODNI; `_vladimir_central`, `council_meetings` and `blackrod` use FBI; `red_team` and `stress_tests` use DIA; `morphisms` and `omc_dags` use NGA; `core_paper_reviews` uses INR; and `code_reviews`, `coverage` and `documentation` use NRO. These names retain their existing namespace except `_adversary` and `_vladimir_central`, which lose their leading underscore. Council, stress-test and morphism routes match their current producers. A complete Adversary bundle is stored once under DARPA; agency placement does not create a confidentiality classification, actor license or detector admission. Consumers needing another view refer to the same stored bundle.')
# Further edits to the same document keep its one exact pre-edit snapshot.
def append_before(relative, marker, text):
    path = ROOT / relative
    raw = path.read_bytes()
    assert raw.count(marker.encode()) == 1
    snap = OUT / 'integrated_documentation_before' / relative
    if not snap.exists(): preserve(path, raw, 'integrated_documentation_before')
    path.write_bytes(raw.replace(marker.encode(), (text + '\n\n' + marker).encode()))
append_before('product_planning_office/plans/decisions/adr_20261010_oewas_intelligence_migration.md',
'## Bounded migration safety',
'The prior-art registry retains all 880 original rows and its original byte pin, including the old PDF locator. The [PPO filesystem composition](../../../product_planning_office/infrastructure/prior_art_sources.py) injects a domain historical-source port into the auditor. Only a missing contained `_intelligence/` source may invoke the existing inventory-bound reader; it must return a contained regular file with matching bound bytes. Missing or inconsistent custody refuses instead of guessing a new canonical filename. Use-case code does not import the outward storage adapter. The [focused controls](../../../product_planning_office/tests/test_prior_art_historical_sources.py) cover missing or changed canonical bytes, immutable-snapshot readback, transplanted or malformed bindings and actual guard bypass/restoration.')
append_before('product_planning_office/plans/epics/oewas/epic_oe_oewas_007_american_ic_partition_and_typed_schema_plan.md',
'## Obstruction review and TDD test plan',
'The [PPO historical-source composition](../../../../product_planning_office/infrastructure/prior_art_sources.py) preserves the 880-row prior-art registry unchanged. It injects a domain port into the existing audit use case, resolving only missing contained `_intelligence/` sources through their frozen inventory and original-byte checks. Existing sources retain their established path behavior; ordinary missing paths, unlisted old locators, malformed bindings, unavailable matching bytes and escaping adapter outputs refuse. The executable audit CLI is `product_planning_office.infrastructure.prior_art_sources`; the use-case module remains dependency-injected and does not import the outward storage adapter. [Focused tests](../../../../product_planning_office/tests/test_prior_art_historical_sources.py) and the separate planning evidence record this real relocation integration defect, minimal repair and boundary mutations.\n\nThe final integrated source includes main revision `d47c98402a42fd189acd7cf6ccd23d7a0d09c120`. The original 6,672-file cutover and the five newly merged legacy bundle files have separate custody records; adding those five is an inventory amendment, not a replay of the public executor over the entire amended set. The final ledger and staged/committed blob check determine exact delivered parity.')
append_before('workflows_agents_skills/documentation/intelligence_migration_v1.md',
'## Verification and remaining work',
'## Audit prior-art navigation after relocation\n\nKeep the original prior-art registry and scientific source pins unchanged. Run the existing auditor through its filesystem composition, which injects the inventory-bound historical reader:\n\n```powershell\n& $uv @runtimeArgs python -X utf8 -m product_planning_office.infrastructure.prior_art_sources\n```\n\nOnly missing contained `_intelligence/` locators invoke historical readback. The adapter requires the bound inventory row and matching original/canonical/snapshot bytes; it does not guess a destination or weaken source hashes. Missing or malformed bindings, unlisted locators, unavailable matching bytes and escaping results refuse. The [18 focused controls](../../product_planning_office/tests/test_prior_art_historical_sources.py) and exact boundary-mutation outputs are separately recorded in [planning integration evidence](../receipts/oewas007_20261010/planning_default_ic/). The use-case module is still usable with an explicitly injected port; its bare CLI has no concrete historical reader.\n\nThe main integration at `d47c98402a42fd189acd7cf6ccd23d7a0d09c120` contributes five legacy Adversary bundle files after the original 6,672-file development cutover. Their separately bound inventory amendment preserves the original cutover evidence; it is not a new public-executor replay. Review the final combined inventory and both Git-blob families before claiming the amended repository transition is complete.')
print(json.dumps({'command_navigation_documents':len(changes),'documentation_files':3},sort_keys=True))