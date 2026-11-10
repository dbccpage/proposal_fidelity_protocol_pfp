"""Build the supplementary source-review ledger from explicit human/model reads."""
from __future__ import annotations
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "dag/reviews"
LEGACY = "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/"
STAGED = "workflows/wf20_derivation_loop_with_lift_grants/pilots/derivation_dag_pfp_staged_benchmark.py"
COMMIT = "8050c66900899771766f33e8f5fdd200b7dd9120"
assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == COMMIT

full = {
 "pfp/infrastructure/workflow_accounting.py": "All batch reservations and stable action claims are recorded in one transaction before threaded dispatch. Unknown outcomes retain liability. This is estimated accounting, not a provider-enforced spend ceiling.",
 "pfp/workflows/tests/test_standalone.py": "Read every test: offline preparation/ingress and family-specific schema/integer-sum behavior. Mocked-provider tests support bounded contracts only.",
 "pfp/workflows/wf0003/structured.py": "Source-bound operand metadata and IntegerList-to-Integer operation shape; model raw artifact retained separately from host checking projection. No solution total is inserted here. This is not a general QM specification.",
 LEGACY + "tests/test_finite_qm_derivation_pfp.py": "Tests require sibling-repository prompt/evidence layout, inspect historical ablation summaries, and feed generated expected answers to the benchmark gate. Not executed: default paths and import-time external reads are outside this probe scope.",
 "pfp/workflows/wf0005/workflow.py": "Checked source rewrite is required before prepare; exact integer-sum semantics and source binding are maintained. Reuse results explicitly remain reference reuse rather than causal learning evidence.",
 "pfp/workflows/wf0004/tests/test_wf0004.py": "Offline tests cover scripted miner/five solver calls, batch reservation, concurrency intervals, source/wire tampering, wrong unanimous sums, replay and continuation against one ledger. All selected tests passed.",
 "pfp/workflows/wf0004/runner.py": "Six-call integer-sum orchestration, fresh run roots, source snapshots, identity/custody gates and exact global check. Host invocation overlap does not observe provider computation parallelism. Default monetary policy is estimated.",
 "pfp/workflows/wf0004/workflow.py": "Screened/frozen mining and five solver candidates feed exact integer global checking. Structural local agreement can coexist with wrong answers; global checks reject wrong unanimous sums. Same unchanged graduate-QM seed needs a domain adapter.",
 "pfp/workflows/wf0005/tests/test_wf0005.py": "Tests cover exact source grammar, round-trip decoder, injected prefixes/suffixes, sign/operand and pin mutations, invalid-rewrite preflight, scripted six-call execution and unchanged budget custody. All selected tests passed.",
 "pfp/tests/test_operad_specification.py": "Strict shape, source span, tree/permutation and obligation tests. Explicit negative claims: declarations of matrices, bundles, DPO matches and relation witnesses are not mathematical verification. Selected suite passed these tests.",
 "pfp/domain/operad/specification.py": "Frozen strict models and validators check nominal signatures, arity, rooted connected single-use composition trees, bijective permutations, source spans and explicit obligation metadata. They do not establish operadic relation laws, PSD, DPO applicability/confluence, signatures, or native admission.",
 "pfp/tests/finite_qm_workflow/test_finite_qm_reference_workflow.py": "Tests bind prompts and repairs, reject labelled answer fields and numerical answer defaults, enforce source pins and registered checker use. Four nonnative selected tests fail on absent source assets; two native tests were deselected, not passed.",
 "pfp/infrastructure/finite_qm_prompt.py": "Public exact-data and witness-schema guards, four filled slots, selected operation signature binding, source-pin shape, bounded P1/P3 stages and failure-code vocabulary. Free text still needs semantic leakage review; nonempty composition-plan/predicate text does not verify a theorem or an operad relation.",
 "pfp/infrastructure/finite_qm_cochain_judge.py": "Exact reduced rational witness adapter to native cochain checking; binds supplied public complex/cochain and candidate potential/dual, checks reported phi/gamma. Explicitly checks cochains only, with no Hilbert/Born/tensor bridge. Native execution was not run.",
 "pfp/tests/test_estimated_gateway.py": "Full test source read; fixtures mock transport/pricing. Collection fails before tests run because an imported teamwork fixture depends on missing operating_system package. No claimed passes for this file.",
 LEGACY + "gates/gate_engine.py": "Expected-value comparison gates. Isolated actual function probes reproduce unchecked metadata fields, boolean/integer alias acceptance and answer-bearing failure strings. Distinct entrypoints have different strictness; the 18-field gate is not an exact typed/schema validator.",
 LEGACY + "prompts/prompt_compiler.py": "Explicitly requests JSON extraction and prints precomputed certificate values; not a blind derivation task. Coupled compiler calls a dictionary-typed expected_certificate field as a function, reproduced without importing legacy dependencies.",
 "pfp/domain/quantum/certificate_checker.py": "No Python algebra checker: requires explicit StabilizerPort and returns FAIL/NATIVE_PORT_UNBOUND when absent. Validity of a supplied port remains a separate dependency.",
 "pfp/entrypoints/cli/finite_qm_prompt.py": "Offline preparation/check only; verifies source bytes and root containment before dispatching a registered native checker. Prepared prompts are NOT_RUN; submitted bytes are not a live model run. Missing assets prevent the selected checkout fixture path.",
 "pfp/domain/cohomology/certificate_checker.py": "C011 independently verifies exact primal repair, bounded circulation dual, zero gap and reported optimum. Correctly refuses UNKNOWN and SOLVED C012-C020 without independent checks; supported out-of-scope claims require matching input defects.",
 "pfp/tests/test_cohomology_certificate_fail_closed.py": "50 offline tests pass: exact/sparse C011, mutations, canonical scalars, scope defects, unavailable C012-C020 checking and malformed inputs. Does not establish native solver correctness or QM applicability.",
 "pfp/domain/cohomology/validation.py": "Canonical exact rationals reject bool/float and noncanonical strings; identifiers/edge uniqueness and sparse coordinate checks prevent collapse; C011 and C012 scope defects are checked against input. No cohomology computation is claimed.",
 "pfp/domain/cohomology/solver.py": "Challenge routing and injected/default solver port only. No independent mathematics here; detect_challenge prioritizes explicit identifier then structural aliases, defaulting to C011.",
}
partial = {
 "pfp/infrastructure/estimated_gateway.py": ([[1,350],[588,912]], "Read factory/scoping prefix and complete EstimatedBudgetGateway class. Reserves 2x byte-based estimate, stops at 80%, holds unknown/over-estimate liabilities, durable action binding and original-wire recovery. DurableRunGateway internals and NativeAnthropicCampaign remain only partly/unread; no vendor billing guarantee."),
 LEGACY + "operad_mining/miner.py": ([[1,38],[650,715],[1180,1237],[1266,1412]], "Read imports/default paths, import-time spec expansion, expected certificate construction and entire appended rule/work-unit miner. Synthetic probes establish arity/signature mismatch, unrelated node-route pairing, hash arithmetic independent of statement and default PROVED_LEAN. Most original per-node mining code remains unread."),
 LEGACY + "run_finite_qm_pfp.py": ([[680,735]], "Read benchmark implementation: generates 1000 units and checks each against its own expected ground truth. It does not call a model. Other live/ablation/reporting runner code remains unread in this phase."),
 STAGED: ([[1,95],[176,239]], "Read import/default-layout prefix and CarrierDerivationProjection contract plus metadata loader prefix. expected_certificate is a dictionary field, incompatible with coupled prompt compiler's call syntax. Most mathematical projection and runner implementation remains unread."),
}

def record(path, assessment, ranges=None):
    raw = (ROOT/path).read_bytes()
    n = len(raw.decode("utf-8-sig").splitlines())
    lines = [[1,n]] if ranges is None else ranges
    reviewed = {i for a,b in lines for i in range(a,b+1)}
    assert reviewed <= set(range(1,n+1)), (path,n,lines)
    unread=[]
    start=None
    for i in range(1,n+2):
        missing = i <= n and i not in reviewed
        if missing and start is None: start=i
        if not missing and start is not None: unread.append([start,i-1]);start=None
    blob = subprocess.check_output(["git","rev-parse",f"{COMMIT}:{path}"], cwd=ROOT, text=True).strip()
    clean_blob = subprocess.check_output(["git","hash-object","--path",path,path], cwd=ROOT, text=True).strip()
    assert clean_blob == blob, path
    return dict(path=path,sha256=hashlib.sha256(raw).hexdigest(),git_blob=blob,source_commit=COMMIT,
        full_source_read=ranges is None,assessment=assessment,reviewed_lines=lines,total_lines=n,
        unread_lines=unread,review_method="Substantive source read; current tracked bytes checked against named commit (Git clean filters applied).")

reviews=[record(p,a) for p,a in full.items()]+[record(p,a,r) for p,(r,a) in partial.items()]

claims=[
 dict(id="AWS-C01",claim="Current WF4/WF5 demonstrate bounded integer-sum workflow and custody contracts, not general model improvement or QM correctness.",evidence=["pfp/workflows/wf0004/workflow.py","pfp/workflows/wf0004/runner.py","pfp/workflows/wf0005/workflow.py","validation:WF"],dependencies=["integer_sum_v1","screened source-bound mining","exact global judge","estimated gateway"],limitations=["All exercised provider responses were scripted/mocked.","No unchanged-seed QM checker was admitted.","Host call overlap is distinct from observed provider compute parallelism."]),
 dict(id="AWS-C02",claim="WF batch admission reserves shared estimated liabilities before threads dispatch and retains unresolved liabilities across attempts.",evidence=["pfp/infrastructure/workflow_accounting.py","pfp/infrastructure/estimated_gateway.py:588-912","validation:WF"],dependencies=["SqliteBudgetLedger transaction semantics","provider identity/usage observations","pinned model pricing"],limitations=["Byte/token and pricing estimates are not provider-enforced hard caps.","All transport scenarios exercised were offline.","Independent estimated-gateway test module could not collect."]),
 dict(id="AWS-C03",claim="The current operad specification checks typed finite tree syntax and obligation metadata; it does not certify operad laws or domain mathematics.",evidence=["pfp/domain/operad/specification.py","pfp/tests/test_operad_specification.py","validation:CONTRACT"],dependencies=["nominal colors/signatures","declared source spans","explicit relation/semantic checker adapters"],limitations=["PSD, DPO existence/confluence, quotient soundness and relation-law checking are not implied.","A typed composition is only admissible for the unchanged seed after hypotheses and semantic adapters are validated."]),
 dict(id="AWS-C04",claim="The current finite-QM reference wrapper separates preparation from registered checking and limits answer-bearing schema metadata and repair codes.",evidence=["pfp/infrastructure/finite_qm_prompt.py","pfp/entrypoints/cli/finite_qm_prompt.py","pfp/tests/finite_qm_workflow/test_finite_qm_reference_workflow.py","validation:CONTRACT"],dependencies=["task-specific source pins","selected operation catalog","four filled slots","registered native cochain judge"],limitations=["Free-text mathematical leakage still requires semantic review.","The supplied cochain judge checks cochains only.","Four required fixture/reference assets are absent and native checking was not exercised."]),
 dict(id="AWS-C05",claim="Legacy WF20 benchmark-1000 is a generated expected-answer self-consistency check, not 1000 independent model derivations.",evidence=[LEGACY+"run_finite_qm_pfp.py:695-722",LEGACY+"tests/test_finite_qm_derivation_pfp.py:120-125",LEGACY+"operad_mining/miner.py:1369-1412",LEGACY+"prompts/prompt_compiler.py:133-163","validation:PROBE"],dependencies=["source public DAG identifiers","host-generated hash arithmetic","exact expected-answer comparator"],limitations=["The complete historical runner and sibling evidence store were not executed/read.","This finding applies to the named legacy path, not automatically to the newer P0-P5 programme."]),
 dict(id="AWS-C06",claim="The legacy 18-field gate does not enforce its typed certificate contract and can disclose expected values in repair failures.",evidence=[LEGACY+"gates/gate_engine.py:345-454","validation:PROBE"],dependencies=["Python equality and shallow float checks","caller-provided expected ground truth"],limitations=["Probe used synthetic public fixtures with selected exact AST definitions.","No private answer key or benchmark seed solution was read or used.","Other gate entrypoints have different checks and must be assessed separately."]),
 dict(id="AWS-C07",claim="The legacy appended miner does not establish a well-typed mathematical operad or a theorem-to-witness map.",evidence=[LEGACY+"operad_mining/miner.py:1276-1412","validation:PROBE"],dependencies=["family route counts","fixed two source colors","ordinal/node/route hash"],limitations=["Node/route incidence is not checked by this generator.","Semantics of the original DAG theorems were not reassessed.","Changing statement text leaves the generated numerical witness unchanged for fixed identifiers."]),
 dict(id="AWS-C08",claim="C011 has a substantive exact independent primal-dual certificate check for a weighted L1 graph repair problem.",evidence=["pfp/domain/cohomology/certificate_checker.py","pfp/domain/cohomology/validation.py","pfp/tests/test_cohomology_certificate_fail_closed.py","validation:COHOMOLOGY"],dependencies=["positive exact rational edge weights","primal c-r=potential difference","dual circulation and absolute edge bounds","equal primal and dual objective"],limitations=["This certifies only the supplied C011 input/certificate.","It is not a proof of a Hilbert-space interpretation or the complete graduate-QM task.","C012-C020 SOLVED certificates remain unverified by this checker; scope refusals are distinct from solved certificates."]),
]
findings=[
 dict(id="AWS-F01",severity="high",scope="legacy WF20 18-field gate",finding="Six purportedly typed fields accept arbitrary nested objects while the gate passes; boolean/integer aliases also pass selected witness/count comparisons.",evidence=[LEGACY+"gates/gate_engine.py:345-454","additional_workflow_sources_probe_results.json"],recommendation="Validate complete exact field types, task/node identity, status and continuation policy before gate acceptance; add independent mutants for every field."),
 dict(id="AWS-F02",severity="high",scope="legacy WF20 blindness and feedback",finding="The compiler prints precomputed numeric solutions, the 1000-unit benchmark supplies its own expected answer, and mismatch strings include exp= values.",evidence=[LEGACY+"prompts/prompt_compiler.py:133-163",LEGACY+"run_finite_qm_pfp.py:695-722",LEGACY+"gates/gate_engine.py:394-415"],recommendation="Classify as extraction/self-consistency evidence. A blind benchmark needs a separate sealed judge channel and bounded non-answer-bearing repair residuals."),
 dict(id="AWS-F03",severity="high",scope="legacy WF20 appended miner",finding="Fixed two source colors disagree with route-derived arity; unrelated routes are paired with nodes; missing status becomes PROVED_LEAN; numerical witnesses are derived from identifiers rather than statement semantics.",evidence=[LEGACY+"operad_mining/miner.py:1344-1412","additional_workflow_sources_probe_results.json"],recommendation="Do not admit these rows as proved operations. Require exact input signatures, source incidence, explicit unknown status, and task-specific semantic witnesses."),
 dict(id="AWS-F04",severity="medium",scope="legacy coupled-slice prompt compiler",finding="compile_coupled_slice_prompt calls proj.expected_certificate(), but the imported CarrierDerivationProjection declares expected_certificate as dict; isolated invocation raises TypeError.",evidence=[LEGACY+"prompts/prompt_compiler.py:90",STAGED+":186-203","additional_workflow_sources_probe_results.json"],recommendation="Reconcile the declared projection/compiler interface and run a public fixture integration test before treating this path as runnable."),
 dict(id="AWS-F05",severity="medium",scope="current reference replay dependencies",finding="Four selected finite-QM tests fail because expected engine/education/.agents files are absent in this checkout. The separate estimated gateway test file fails collection through a missing operating_system dependency.",evidence=["additional_workflow_sources_contract_tests.xml","additional_workflow_sources_budget_tests.xml"],recommendation="Publish or explicitly supply versioned runtime/reference dependencies before claiming standalone replay; do not silently replace them with unpinned sibling files."),
]

validation=[]
for identifier,stem,selected,limits in [
 ("WF","wf_tests",["pfp/workflows/tests/test_standalone.py","pfp/workflows/wf0004/tests/test_wf0004.py","pfp/workflows/wf0005/tests/test_wf0005.py"],["Mocked providers only; 91 passes are contract tests, not measured model effects."]),
 ("CONTRACT","contract_tests",["pfp/tests/test_operad_specification.py","pfp/tests/finite_qm_workflow/test_finite_qm_reference_workflow.py"],["Two native tests deselected: native_certificate_positive_and_decisive_mutations; cli_prepares_and_checks_actual_fixture_bytes.","76 passed, 4 missing-asset failures; no native correctness result."]),
 ("BUDGET","budget_tests",["pfp/tests/test_estimated_gateway.py"],["Collection failed: ModuleNotFoundError operating_system through imported teamwork fixture; no tests from this file ran."]),
 ("COHOMOLOGY","cohomology_tests",["pfp/tests/test_cohomology_certificate_fail_closed.py"],["50 passes cover exact supplied certificate and refusal contracts only."]),
]:
    path=OUT/f"additional_workflow_sources_{stem}.xml"
    tree=ET.parse(path)
    suites=list(tree.getroot().iter("testsuite"))
    totals={key:sum(int(s.get(key,0)) for s in suites) for key in ("tests","failures","errors","skipped")}
    failures=[dict(name=c.get("name"),message=f.get("message","")) for c in tree.getroot().iter("testcase") for f in c if f.tag in ("failure","error")]
    validation.append(dict(id=identifier,kind="pytest_offline",python=".venv/Scripts/python.exe -X utf8",selected=selected,
        outcome=totals,failing_cases=failures,report=path.relative_to(ROOT).as_posix(),log=f"dag/reviews/additional_workflow_sources_{stem}.log",limitations=limits,
        artifact_policy="PYTHONDONTWRITEBYTECODE=1; -p no:cacheprovider; explicit --basetemp below dag/reviews/additional_workflow_sources_tmp_*. No historical evidence rewritten."))
validation.append(dict(id="PROBE",kind="isolated_source_reproduction",command=".venv/Scripts/python.exe -X utf8 dag/reviews/additional_workflow_sources_probes.py",result="All explicit reproduction assertions passed",report="dag/reviews/additional_workflow_sources_probe_results.json",limitations=["Exact selected AST class/functions execute on synthetic public fixtures only; this is not full legacy integration or a production fix.","No importing the legacy miner's sibling-dependent module; no model calls."]))

remaining=[
 "Complete unread ranges explicitly listed in the four partially reviewed source records.",
 "Review remaining WF1-WF5 runner/ingress/source-snapshot/global-check dependencies and downstream provider ledger/transport modules before a complete end-to-end claim.",
 "Audit current P0-P5 programme implementations and semantic predicates separately from the legacy finite_qm_derivation_pfp findings; read all supplied native checker and mathematical owner code.",
 "Supply/version missing public reference/runtime assets and rerun only dependency-blocked tests; native FFI and native exact cochain checks remain unexecuted here.",
 "Assess historical ablation claims from raw public design, independent task/checker, source/model identity and cost custody; a generated expected-answer fixture or stored pass count is not causal improvement evidence.",
 "Continue workflows corpus semantic backlog from workflows_audit.json; 12,380-file inventory is not 12,380 semantic reads. This supplement covers only its explicitly listed source files.",
 "For unchanged grad-QM seed: define a separate exact/symbolic certificate interface with hypotheses, branch/singular-case semantics and independent judges. No existing reviewed integer/cochain mechanism is certified for the complete seed.",
 "Finite composition grammar: bound generator set, depth/node count, repair fuel, verifier set and parameter grids; require exact color/arity, hypothesis and source-version compatibility, acyclic topology, finite unrolled loops, immutable task identity, separate private judge channel and canonical schedule/tree deduplication. Permute only valid compositions; operadic relation quotienting needs checked laws.",
]
report=dict(schema="pfp.additional_workflow_sources_review.v1",source_commit=COMMIT,generated_at_utc=datetime.now(timezone.utc).isoformat(),status="substantive_selected_source_audit_complete_corpus_audit_in_progress",
    scope="Supplement to workflows_audit.json; clean-main tracked source at named commit; no production source changes.",
    prohibitions_observed=["No paid/API provider calls","No private answer-key/storage read","No solving sealed seed","No historical evidence rewrites"],
    claims=claims,findings=findings,validation=validation,file_reviews=reviews,
    coverage=dict(full_source_files=len(full),partial_source_files=len(partial),total_source_files=len(reviews),reviewed_lines=sum(sum(b-a+1 for a,b in r["reviewed_lines"]) for r in reviews),unread_lines_in_listed_files=sum(sum(b-a+1 for a,b in r["unread_lines"]) for r in reviews),corpus_audit_complete=False),remaining_work=remaining)
(OUT/"additional_workflow_sources.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
md=["# Additional workflow source audit", "",f"Source: `{COMMIT}`. {len(full)} full source reads and {len(partial)} partial source reads, with hashes and exact unread ranges in the JSON ledger. The corpus audit remains in progress.","",
 "The reviewed current WF4/WF5 and C011 code supports bounded, explicit contracts. It does not establish improved model reasoning on the unchanged graduate-QM seed. Several legacy WF20 paths have concrete acceptance, typing and replay defects. No provider calls, private key access, seed solution or production edits occurred.","",
 "## Validation", "", "| Check | Observed result |", "| --- | --- |",
 "| Current standalone/WF4/WF5 | 91 passed; scripted providers, no live effects measured |",
 "| Operad and finite-QM contracts | 76 passed, 4 absent-asset failures, 2 native tests deselected |",
 "| Estimated gateway module | Collection error: missing `operating_system`; no tests executed |",
 "| C011/C012 refusal and certificate tests | 50 passed |",
 "| Synthetic legacy source probes | All reproductions asserted; not a full legacy import/replay |", "",
 "The four reference failures require `engine/crates_rs/core_quantum_physics/src/density_matrix.rs`, `engine/crates_rs/core_symbol_game_runtime/src/cochain.rs`, `education/documentation/004_oepfp/_how_to_play/v4_operad_container_and_p_star_loop/finite_qm_pfp_system_prompt.md`, and `.agents/skill_operads/operad_signature.json`. No absent asset was silently substituted.","", "## Findings", ""]
for f in findings: md += [f"- **{f['id']} ({f['severity']}):** {f['finding']} {f['recommendation']}"]
md += ["", "## Supported mechanisms and limits", ""]
for c in claims: md += [f"- **{c['id']}:** {c['claim']} {' '.join(c['limitations'])}"]
md += ["", "## Source review ledger", "", "| Source | Read depth | Assessment |", "| --- | --- | --- |"]
for r in reviews: md += [f"| `{r['path']}` | {'Full' if r['full_source_read'] else 'Partial: '+str(r['reviewed_lines'])} | {r['assessment']} |"]
md += ["", "## Remaining work", ""] + [f"- {x}" for x in remaining]
md += ["", "Reproduction helper: `additional_workflow_sources_probes.py`. Structured observations: `additional_workflow_sources_probe_results.json`. Pytest XML/logs share the `additional_workflow_sources_` prefix. No broad mathematical or empirical success claim is inferred from syntactic or historical checks.",""]
(OUT/"additional_workflow_sources.md").write_text("\n".join(md),encoding="utf-8")
print(json.dumps(report["coverage"],indent=2))
