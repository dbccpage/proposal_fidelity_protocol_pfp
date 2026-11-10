"""Read-only workflow inventory; writes only its two named audit reports.

No project module is imported or executed. No provider is called. SQLite and
binary payloads are inventoried without opening them. Review depth is explicit.
"""
from __future__ import annotations

import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASE = "644d950a44c6387d7ebc669c098bf4de91168771"
REMOTE = "8050c66900899771766f33e8f5fdd200b7dd9120"
OUT = ROOT / "dag/reviews"
CAMPAIGN = "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/theory_of_finite_qm_campaign/"
BINARY = {".sqlite3", ".bin"}
SEMANTIC_LOCAL = {
    "workflows/README.md", "workflows/tasks/README.md", "workflows/library/README.md",
    "workflows/library/catalog.json", "workflows/library/pilot_estate/README.md",
    "workflows/tasks/certified_challenges/README.md", "workflows/dag/ORCHESTRATION.md",
    "workflows/wf07_typed_refusal/pilots/homological_objects/checker.py",
    "workflows/wf21_structural_prompt_rewriting/pilots/acset_cochain_rewriting/checker.py",
    "workflows/wf20_derivation_loop_with_lift_grants/pilots/pilot_0000199/run.py",
}
SEMANTIC_REMOTE = {CAMPAIGN + p for p in ["README.md", "workflow.yaml", "stage_contracts.yaml", "mode.yaml"]}
SEMANTIC_LOCAL.update(SEMANTIC_REMOTE)
SEMANTIC_LOCAL.update({
    "workflows/wf12_mechanism_control_arms/pilots/c001_attention_distractor_mask/pipeline.json",
    "workflows/wf12_mechanism_control_arms/pilots/c005_hosted_decode_controls/pipeline.json",
    "workflows/wf07_typed_refusal/pilots/homological_objects/contract.json",
    "workflows/wf14_immune_failure_classification/pilots/pilot035/task.json",
    "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/modes/finite_qm_modes.yaml",
    "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/stages/finite_qm_stages.yaml",
    "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/gates/gate_engine.py",
    "workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/prompts/prompt_compiler.py",
})
PARTIAL = {"workflows/dag/workflow_dag.json", "workflows/dag/README.md"}
for p in (ROOT / "workflows").glob("wf*/README.md"):
    SEMANTIC_LOCAL.add(p.relative_to(ROOT).as_posix())


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def visible(path: str) -> bool:
    return not any(part.startswith(".") for part in path.split("/")[:-1])


def secret(path: str) -> bool:
    # This audit is confined to public workflow assets; never inspect secret stores.
    return any(part.lower() in {"private", "private_storage", "answer_key", "answer_keys", "secrets"}
               for part in path.split("/"))


def text_features(path: str, raw: bytes, semantic: bool = False) -> dict:
    ext = Path(path).suffix.lower()
    row = {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    try:
        text = raw.decode("utf-8-sig")
        if "\x00" in text:
            raise UnicodeError("NUL-containing payload")
    except UnicodeError:
        row.update(review_level="byte_inventory_only", content_reviewed=False,
                   remainder="Binary/non-UTF8 payload not interpreted")
        return row
    row["lines"] = len(text.splitlines())
    row["review_level"] = "semantic_full_text" if semantic else "mechanical_text_inventory"
    row["content_reviewed"] = semantic
    if path in PARTIAL and not semantic:
        row["review_level"] = "semantic_selected_sections"
    row["remainder"] = None if semantic else "Substantive content not fully reviewed by the auditor; mechanical scan is not semantic certification"
    if ext == ".py":
        try:
            tree = ast.parse(text, filename=path)
            row["format_check"] = "python_ast_parse_pass"
            row["symbols"] = [{"name": n.name, "line": n.lineno, "end_line": n.end_lineno}
                              for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(n.name for n in node.names)
                if isinstance(node, ast.ImportFrom):
                    imports.append("." * node.level + (node.module or ""))
            row["imports"] = sorted(set(imports))
            row["historical_runtime_imports"] = [x for x in row["imports"] if x.startswith("omega_engine_")]
        except SyntaxError as e:
            row["format_check"] = f"python_ast_parse_failure:{e.lineno}:{e.msg}"
    elif ext == ".json":
        try:
            obj = json.loads(text)
            row["format_check"] = "json_parse_pass"
            row["top_level_type"] = type(obj).__name__
            if isinstance(obj, dict):
                row["top_level_keys"] = list(obj)[:24]
            if isinstance(obj, list):
                row["item_count"] = len(obj)
        except (ValueError, RecursionError) as e:
            row["format_check"] = f"json_parse_failure:{type(e).__name__}"
    elif ext == ".jsonl":
        try:
            items = [json.loads(line) for line in text.splitlines() if line.strip()]
            row.update(format_check="jsonl_parse_pass", item_count=len(items))
        except ValueError:
            row["format_check"] = "jsonl_parse_failure"
    elif ext in {".yaml", ".yml"}:
        row["format_check"] = "yaml_text_key_scan_only_no_yaml_parser"
        row["top_level_keys"] = re.findall(r"^([A-Za-z_][\w-]*):", text, flags=re.M)[:24]
    elif ext in {".xml", ".svg"}:
        try:
            node = ET.fromstring(text)
            row["format_check"] = "xml_parse_pass"
            row["root_tag"] = node.tag
        except ET.ParseError:
            row["format_check"] = "xml_parse_failure"
    else:
        row["format_check"] = "utf8_text_read"
    if ext == ".md":
        row["headings"] = re.findall(r"^#{1,3}\s+(.+)$", text, flags=re.M)[:16]
    if "/evidence/" in path or "/results/" in path or "/scores/" in path or Path(path).name in {"raw_reply.json", "response.yaml", "response.json"}:
        row["artifact_role"] = "historical_evidence_or_response"
    elif Path(path).name.startswith("test_") or "/tests/" in path:
        row["artifact_role"] = "test_or_fixture"
    elif ext == ".py":
        row["artifact_role"] = "source_implementation_or_wrapper"
    elif ext == ".md":
        row["artifact_role"] = "documentation_or_specification"
    else:
        row["artifact_role"] = "configuration_contract_or_data"
    return row


def inventory_local() -> tuple[dict, dict]:
    rows, contents = {}, {}
    pins = {}
    for line in git("ls-tree", "-r", REMOTE, "--", "workflows").decode().splitlines():
        meta, name = line.split("\t", 1)
        pins[name] = meta.split()[2]
    for p in sorted((ROOT / "workflows").rglob("*")):
        if not p.is_file():
            continue
        name = p.relative_to(ROOT).as_posix()
        if not visible(name):
            continue
        if secret(name) or p.suffix in BINARY:
            rows[name] = {"path": name, "bytes": p.stat().st_size,
                          "review_level": "metadata_only_not_opened", "content_reviewed": False,
                          "remainder": "Excluded private store or binary database; bytes not read"}
            continue
        raw = p.read_bytes()
        contents[name] = raw
        oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        rows[name] = text_features(name, raw, name in SEMANTIC_LOCAL and oid == pins.get(name))
        if rows[name]["content_reviewed"]:
            rows[name]["semantic_review_pin"] = {"commit": REMOTE, "git_blob": oid}
    return rows, contents


def inventory_remote(local: dict, content: dict) -> tuple[dict, dict]:
    entries = []
    for line in git("ls-tree", "-r", "-l", REMOTE, "--", "workflows").decode().splitlines():
        meta, name = line.split("\t", 1)
        if visible(name):
            mode, kind, oid, size = meta.split()
            entries.append((name, oid, int(size)))
    rows, remote_content, need = {}, {}, []
    for name, oid, size in entries:
        if secret(name) or Path(name).suffix in BINARY:
            rows[name] = {"path": name, "bytes": size, "git_blob": oid,
                          "review_level": "metadata_only_not_opened", "content_reviewed": False,
                          "remainder": "Excluded private store or binary database; bytes not read"}
            continue
        raw = content.get(name)
        local_oid = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() if raw is not None else None
        if local_oid == oid:
            rows[name] = {**local[name], "git_blob": oid, "same_as_worktree": True}
            remote_content[name] = raw
        else:
            need.append((name, oid))
    if need:
        output = subprocess.check_output(["git", "cat-file", "--batch"],
            input="".join(oid + "\n" for _, oid in need).encode(), cwd=ROOT)
        offset = 0
        for name, oid in need:
            end = output.index(b"\n", offset)
            header = output[offset:end].decode().split()
            size = int(header[2]); raw = output[end + 1:end + 1 + size]; offset = end + size + 2
            remote_content[name] = raw
            # Changed family docs received only a diff inspection; do not inherit full review.
            sem = name in SEMANTIC_REMOTE
            rows[name] = {**text_features(name, raw, sem), "git_blob": oid, "same_as_worktree": False}
            if name in SEMANTIC_LOCAL and not sem:
                rows[name]["review_level"] = "semantic_worktree_version_plus_remote_diff_scan"
                rows[name]["remainder"] = "Full worktree text reviewed; changed remote version structurally inventoried, semantic changes require follow-up"
    return rows, remote_content


QM_NOTES = {
1:("schema_transport_only", "Arbitrary seed can use schema_only; only integer_sum_v1 has a supplied mathematical judge. Add a QM certificate schema and pinned independent predicates before mathematical acceptance."),
2:("schema_transport_only", "Slot plumbing can preserve the seed; operation/slot schemas and exact QM judges need a domain adapter."),
3:("schema_transport_only", "Mining and frozen guidance can wrap the seed; integer-sum guidance and L2 checks do not certify QM. Screen for answer leakage and bind a QM contract."),
4:("unsupported_without_adapter", "Runner requires integer_sum_v1. Replace domain contract and global compatibility with independent checks of the same QM claims; consensus is insufficient."),
5:("unsupported_without_adapter", "Exact-sum source language and decoder refuse this seed. A complete reversible QM representation, protected-query map and independent decoder are required."),
6:("design_adaptable", "Use only reversible presentations of the identical seed and one fixed QM judge; one seed gives within-item evidence, not a cross-domain effect."),
7:("limited_diagnostic", "Separate missing-premise refusal from resource/checker refusal. Singular parameter cases in this seed are required obligations, not grounds to erase the task."),
8:("design_adaptable", "Map the five obligations to typed stages with unchanged target and hash-bound interfaces; custody does not validate the formulas."),
9:("design_adaptable", "Bounded repair applies after a QM checker and non-answer-bearing residual vocabulary are registered; cochain/parity residuals cannot be substituted."),
10:("domain_preset_inapplicable_as_is", "A generic cohomological obstruction certificate is not a spectral or thermal calculation. A claimed cochain encoding needs a task-preserving bridge and its own adequacy evidence."),
11:("certificate_adapter_required", "LP/flow/assignment/Farkas/Bareiss judges do not check this complete symbolic QM task. Design exact identity/branch certificates independently."),
12:("design_adaptable", "Fixed-seed mechanism ablations are possible with one QM judge; rank-difference carrier is not the QM task and a single seed does not measure transfer."),
13:("domain_battery_inapplicable_as_is", "The existing battery is many different problems. Add this seed as one explicitly scoped domain capsule; do not count other domain passes as QM checks."),
14:("calibration_adapter_required", "A QM-specific known-good/self and failure panel must precede detector admission; historical negative selection alone cannot establish adequacy."),
15:("design_adaptable", "Freeze opposing candidate arguments then check named QM claims. Finite modal/attack-graph checkers do not verify symbolic derivations."),
16:("translation_adapter_required", "Source-to-formal/symbolic translation needs relations, parameter assumptions and exceptional branches preserved; a finite table alone is insufficient."),
17:("research_protocol_only", "Witness/countermodel discipline is useful, but each QM equivalence and universal claim needs its own admissible certificate; this is not a universal runner."),
18:("campaign_adapter_required", "Replay plumbing can be adapted; the 5x5+5 finite-carrier campaign changes tasks and cannot be run as one unchanged-seed benchmark."),
19:("held_out_family_required", "One seed can generate exploratory failure rules, but disjoint held-out transfer cannot be measured by repeatedly solving the same seed."),
20:("research_protocol_adapter_required", "Existing finite-QM staged work has domain-specific controls and private-runtime/layout dependencies. It requires reviewed operations and task-applicable checkers, not generic C4 admission."),
21:("preservation_adapter_required", "Protected-byte graph rewrites can attach guidance while keeping seed bytes intact. Meaning preservation of transformed formulas requires a separate checked map."),
22:("campaign_adapter_required", "Use preregistered fixed-seed arms and explicit budgets; empirical population cost/accuracy conclusions need a declared item bank and repetitions."),
23:("custody_gate_adaptable", "Hash, version and leakage controls transfer to QM packets; audit metadata without exposing this benchmark's private key. Custody alone is not mathematical validity."),
24:("certificate_adapter_required", "Replace nonabelian-holonomy token grammar with the declared QM certificate grammar. Operational formatting is not a correctness proof."),
25:("inapplicable_without_new_problem_map", "The seed has two spins, not a large lattice of certified flat blocks. Hierarchical holonomy decimation has no declared semantics here."),
26:("repair_adapter_required", "Accumulate only non-answer-bearing typed failure constraints under a QM checker. Historical leaked-answer runs are plumbing evidence only."),
27:("repair_adapter_required", "A stationary-loop detector can compare typed QM failure signatures. The historical full-repair hint cannot be used in a fair unchanged-seed unassisted arm."),
28:("role_protocol_adapter_required", "Roles may review a frozen candidate, but l1 cochain descent needs a legitimate task-specific residual. No role or arbiter can self-certify QM."),
29:("checker_development_not_solver_arm", "Useful to audit a newly built QM checker using valid and adversarial branch cases; mutation survival is bounded evidence, not general checker soundness."),
30:("changes_task_unless_preregistered", "Adding forbidden steps or forced mathematical constraints changes the task. Such variants must be separate benchmarks, not unchanged-seed permutations."),
31:("held_out_adapter_required", "The supplied SO(4N) referee is a different problem. Define QM evaluation and an actually hidden split; one public symbolic seed alone has no held-out task sample."),
32:("receipt_adapter_required", "Directly useful as a claim ledger: independently checked claims, numerical examples and unverified prose receive distinct statuses."),
33:("budget_protocol_adapter_required", "Shared fuel and parent receipts transfer, but each re-entry must preserve the target via declared maps; loops are bounded and unrolled for a DAG."),
34:("state_model_required", "Future-faithful compression requires a finite declared state/transition model and retention of all branch obligations; equal diagnostics do not prove equal mathematical content."),
35:("channel_adapter_required", "A fixed QM oracle can compare prompt/grammar channels; unavailable attention/activation hooks are explicitly non-executable arms."),
36:("guard_adapter_required", "Replace the cochain syndrome with complete task-specific obligations and schema guards; stage completeness is distinct from correctness."),
37:("research_campaign_not_single_seed_arm", "Harness evolution needs fresh confirmation and untouched transfer panels. Tuning and grading on one seed cannot establish these claims."),
38:("diagnostic_adapter_required", "A cochain primal-dual/lexicographic diagnostic is not a QM derivation score. Define independently recomputed QM predicates before ranking repairs."),
39:("authority_gate_adaptable", "Bind exact candidate bytes to registered QM verifiers and all required guards; an authority firewall cannot repair an inadequate verifier."),
40:("termination_adapter_required", "Typed refusal/checkpoint/restart policy applies. A restart that changes Hamiltonian, assumptions or claim set is a different task and must leave the unchanged-seed arm."),
41:("calibration_required", "No detector was admitted by the described work. Calibrate each proposed QM detector over declared classes; finite calibration completeness needs its own class assumptions."),
42:("extractor_adapter_required", "A graph extractor's exact cochain result covers only its image. Establish extraction adequacy for the actual QM claims before using it as evidence."),
43:("leak_gate_adaptable", "Use answer-free refusals, empty objects and constant formulas to challenge the frozen QM judge without revealing the private answer key."),
44:("domain_preset_inapplicable_as_is", "Existing l1, pairing and DSL certificates are different tasks; new QM certificates require an explicit typed adapter and correctness argument."),
45:("finite_candidate_adapter_required", "Finite survivor selection can compare submitted formulas under declared tests; unique survivor is only relative to that family and does not prove universal validity."),
46:("compatibility_adapter_required", "Define cross-part consistency among spectral, dynamic, entanglement and thermal claims. NGD is undefined when no run has all local checks accepted."),
47:("bounded_search_adapter_required", "A finite QM candidate grammar and verifier must replace sign-gauge search; checkpoint keys bind the full task and representation, with UNKNOWN retained."),
48:("custody_mutation_gate_adaptable", "Commit candidate/checker versions before tests and mutations. Keep this benchmark's key private; historical reference self-scores are not model scores."),
49:("campaign_adapter_required", "Use explicitly typed stage/mode contracts and the unchanged QM query; existing proposal reports zero campaign cases, so it supplies no new effect estimate."),
}


def classify_manifest(path: str, raw: bytes) -> dict:
    """Classify data contracts by inspected identity/status fields and context."""
    name = Path(path).name
    text = raw.decode('utf-8-sig')
    if path == 'workflows/dag/workflow_dag.json':
        role, status = 'family_and_variation_design_registry', 'not_a_dispatch_manifest'
    elif path == 'workflows/library/catalog.json':
        role, status = 'recipe_availability_catalog', 'mixed_historical_and_current_recipes_not_a_runner'
    elif '/examples/' in path:
        role, status = 'public_task_fixture', 'input_to_WF1_WF5_not_an_independent_workflow'
    elif '/results/' in path or '/evidence/' in path:
        role = 'historical_run_record' if name == 'run.json' else 'historical_run_configuration' if name == 'config.json' else 'historical_catalog' if name == 'catalog.json' else 'historical_task_or_protocol_record'
        status = 'retained_evidence_not_current_dispatch_authority'
    elif name == 'matrix_manifest.yaml':
        role, status = 'estate_index_manifest', 'catalog_membership_explicitly_does_not_schedule_a_run'
    elif path.endswith('/homological_objects/contract.json'):
        role, status = 'clarification_contract', 'checker_acceptance_is_QUERY_USER_MORE_INFO_and_NOT_SOLVED'
    elif 'c001_attention_distractor_mask/pipeline.json' in path:
        role, status = 'local_model_pipeline_configuration', 'NOT_READY_tokenizer_and_prompt_digests_UNSET'
    elif 'c005_hosted_decode_controls/pipeline.json' in path:
        role, status = 'hosted_decode_experiment_configuration', 'legacy_model_routes_and_private_runtime_require_revalidation'
    elif path.endswith('/pilot035/task.json'):
        role, status = 'finite_Tao_phase_table_task', 'explicit_table_only_not_general_MUB_theorem'
    elif path.startswith(CAMPAIGN):
        role = 'typed_stage_response_contract' if name == 'stage_contracts.yaml' else 'bounded_mode_contract' if name == 'mode.yaml' else 'P0_P5_research_workflow_specification'
        status = 'retired_source_dependent_programme_domain_checkers_must_be_registered'
    elif '/finite_qm_derivation_pfp/modes/' in path or '/finite_qm_derivation_pfp/stages/' in path:
        role, status = 'legacy_extraction_mode_or_stage_profile', 'cochain_materialization_and_prefilled_certificates_not_general_QM_derivation'
    elif '/acset_' in path:
        role, status = 'offline_fixture_protocol', 'source_present_private_omega_engine_dependency_not_portability_tested'
    elif name == 'spec.yaml' and 'analytical_acceptance:' in text:
        role, status = 'bounded_derivation_pilot_protocol', 'historical_loops_analytical_acceptance_explicitly_UNVERIFIED'
    elif name == 'spec.yaml':
        role, status = 'historical_domain_pilot_specification', 'finite_domain_checker_reference_runtime_not_verified_here'
    else:
        role, status = 'data_contract_or_configuration', 'not_an_executable_entrypoint'
    fields = {}
    if name.endswith('.json'):
        obj = json.loads(text)
        for key in ['schema','schema_id','schema_version','workflow_id','challenge_id','task_id','pilot_id','mode_id','checker','status','terminal','execution']:
            if key in obj and isinstance(obj[key],(str,int,float,bool,type(None))): fields[key] = obj[key]
    else:
        for key, value in re.findall(r'^\s*(schema|schema_id|workflow_id|pilot_id|task_family|mode|mode_id|kind|checker_id|checker|terminal|execution|execution_terminal|analytical_acceptance):\s*([^\n]+)',text,re.M):
            fields[key] = value.strip()
    return {'classification':role,'substantive_status':status,'executable_file':False,
            'execution_note':'Manifest data can configure an executor; source presence and a path do not establish current executability.',
            'inspected_identity_and_contract_fields':fields,
            'semantic_review_scope':'Identity/status/domain fields and family context; historical payloads not independently replayed'}


def registry(rows: dict, contents: dict) -> dict:
    dag = json.loads(contents["workflows/dag/workflow_dag.json"])
    nodes = []
    for src in dag["nodes"]:
        n = int(src["id"][2:]); prefix = next(p.rsplit("/", 1)[0] for p in rows
            if re.fullmatch(rf"workflows/wf{n:02d}_[^/]+/README.md", p))
        files = [p for p in rows if p.startswith(prefix + "/")]
        runner = f"pfp/workflows/wf{n:04d}/" if n <= 5 else None
        status, note = QM_NOTES[n]
        definition_text = contents[prefix + '/README.md'].decode('utf-8')
        evidence_section = definition_text.split('## Where it comes from\n',1)[-1].split('\n## ',1)[0].strip() if '## Where it comes from\n' in definition_text else '\n'.join(x for x in definition_text.splitlines() if x.startswith('**Latest live run'))
        implementation_files = [p for p in files if p.endswith('.py') and Path(p).name != '__init__.py' and not Path(p).name.startswith('test_')]
        node = {**src, "path": prefix, "definition": prefix + "/README.md",
                "audited_availability": "public_family_runner_source_present_not_executed" if n <= 5 else "family_proposal_with_historical_pilot_source" if implementation_files else "family_proposal_with_documentation_or_data_only_in_own_folder",
                "substantive_evidence_status":{"family_definition_read":True,"source_evidence_statement":evidence_section,"status_scope":"Documentation claims preserved as claims, not independently reproduced results","execution_verified_in_this_audit":False},
                "runner_source": runner,
                "tests": runner + "tests/" if runner else None,
                "pilot_python_sources": [p for p in files if p.endswith('.py') and not Path(p).name.startswith('test_') and Path(p).name != '__init__.py'],
                "pilot_test_sources": [p for p in files if p.endswith('.py') and (Path(p).name.startswith('test_') or '/tests/' in p)],
                "file_count": len(files),
                "grad_qm_seed": {"status": status, "unchanged_seed_mathematically_supported_now": False, "reason": note}}
        nodes.append(node)
    task_roots = sorted({"/".join(p.split('/')[:3]) for p in rows if p.startswith('workflows/tasks/') and len(p.split('/')) >= 4})
    challenge_roots = sorted({"/".join(p.split('/')[:4]) for p in rows if re.match(r'workflows/tasks/certified_challenges/c\d{3}_',p)})
    pilot_roots = sorted({"/".join(p.split('/')[:4]) for p in rows if re.match(r'workflows/wf\d\d_[^/]+/pilots/[^/]+/',p)})
    components = []
    for path in task_roots + challenge_roots + pilot_roots:
        members = [p for p in rows if p.startswith(path + '/')]
        sources = [p for p in members if p.endswith('.py') and not Path(p).name.startswith('test_')]
        role = 'challenge_task_package' if path in challenge_roots else 'task_support_or_example' if path in task_roots else 'nested_pilot_or_evidence_group'
        components.append({"id": path, "kind": role, "file_count": len(members),
            "definition_docs": [p for p in members if Path(p).name in {'README.md','CHALLENGE.md','TASK.md','PROTOCOL.md'}],
            "runner_candidates": [p for p in sources if re.search(r'/(?:run[^/]*|runner|execute|main|__main__|commit_reveal[^/]*)\.py$',p)],
            "checker_candidates": [p for p in sources if re.search(r'(check|judge|verify|validator|gate)',Path(p).name)],
            "tests": [p for p in members if p.endswith('.py') and (Path(p).name.startswith('test_') or '/tests/' in p)],
            "historical_runtime_dependency_sources": [p for p in sources if rows[p].get('historical_runtime_imports')],
            "grad_qm_seed": "not_a_verified_general_QM_adapter; inspect declared task/domain before reuse",
            "review_level": "component_inventory_with_explicit_source_candidates_not_execution_validation"})
    manifest_names = {'workflow.yaml','workflow.json','pipeline.json','mode.yaml','modes.yaml','stage_contracts.yaml','contract.json','catalog.json','matrix_manifest.yaml','task.json','spec.yaml','run.json','config.json'}
    manifest_rows = []
    for p,row in rows.items():
        if Path(p).name not in manifest_names and not re.search(r'/(?:finite_qm_(?:modes|stages)|mode_\d+|workflow_[^/]+)\.(yaml|json)$',p):
            continue
        manifest_rows.append({"path":p,"role":"manifest_or_record_candidate_not_automatically_a_new_workflow", "top_level_keys":row.get('top_level_keys',[]),"review_level":row['review_level'], **classify_manifest(p,contents[p])})
    return {"family_nodes": nodes, "family_edges": [{**e,"audit_edge_semantics":"documented_design_dependency_not_execution_or_proof"} for e in dag['edges']],
            "recorded_variations": [{**v,"review_status":"current_registry_entry_read","audit_scope":"Historical or proposed setting; not independently reproduced, not a new workflow or general QM effect"} for v in dag.get('perturbations',[])], "component_nodes":components,
            "manifest_registry":manifest_rows,
            "component_containment_edges":[{"from":c['id'].split('/pilots/')[0] if '/pilots/' in c['id'] else 'workflows/tasks',"to":c['id'],"kind":"contains_not_execution_dependency"} for c in components]}


def main() -> None:
    head = git('rev-parse','HEAD').decode().strip()
    local, local_content = inventory_local()
    remote, remote_content = inventory_remote(local, local_content)
    reg = registry(remote, remote_content)
    coverage = {
        "worktree_files":len(local), "remote_files":len(remote),
        "worktree_bytes":sum(x['bytes'] for x in local.values()),
        "remote_bytes":sum(x['bytes'] for x in remote.values()),
        "worktree_review_levels":dict(Counter(x['review_level'] for x in local.values())),
        "remote_review_levels":dict(Counter(x['review_level'] for x in remote.values())),
        "remote_format_checks":dict(Counter(x.get('format_check','not_opened') for x in remote.values())),
        "family_count":len(reg['family_nodes']), "recorded_variation_count":len(reg['recorded_variations']),
        "component_count":len(reg['component_nodes']), "manifest_candidate_count":len(reg['manifest_registry']),
        "unread_substantive_remainder_count":sum(not x.get('content_reviewed',False) for x in remote.values()),
        "all_files_semantically_reviewed":False, "provider_calls":0,
    }
    report = {
        "schema":"pfp.workflows-audit.v1", "generated_utc":datetime.now(timezone.utc).isoformat(),
        "status":"inventory_complete_semantic_review_partial",
        "scope":"Every workflows/ file outside dot-prefixed directory ancestors inventoried; dot filenames included. Private stores and binary databases not opened. Public benchmark seed read only; not solved.",
        "snapshots":{"worktree_base":head,"audit_initial_checkout_before_parent_cleanup":BASE,"remote_main_verified_by_parent":REMOTE,
            "remote_source":"local Git objects, no checkout/reset/merge","worktree_may_include_preexisting_changes":True,"semantic_review_pins_commit":REMOTE},
        "review_depth_definitions":{
            "semantic_full_text":"Auditor received and read complete text; not executed and not a mathematical correctness certification",
            "semantic_selected_sections":"Selected passages inspected; remainder explicitly open",
            "semantic_worktree_version_plus_remote_diff_scan":"Worktree text read, remote changes mechanically scanned; full changed text not semantically certified",
            "mechanical_text_inventory":"UTF-8 decoded, hashed, structured parse/AST/key or heading scan as applicable; no claim of full semantic reading",
            "byte_inventory_only":"Nontext bytes hashed but not interpreted",
            "metadata_only_not_opened":"Path/size/Git identity only; private/binary content not opened"},
        "coverage":coverage, "registry":reg,
        "findings":[
            {"id":"WF-A01","severity":"scope","finding":"Only WF1-WF5 have public family runners; WF6-WF49 are documented proposals. Nested historical sources are not absent, but do not make the proposed family design executable as published.","sources":["workflows/README.md","workflows/library/pilot_estate/README.md"]},
            {"id":"WF-A02","severity":"benchmark_blocker","finding":"No inventoried existing workflow supplies a verified checker for every obligation of the unchanged grad-QM seed. WF1-WF3 can transport schema_only; WF4 demands integer_sum_v1 and WF5 recognizes only a complete finite exact-sum language.","sources":["pfp/infrastructure/workflow_tasks.py","pfp/workflows/wf0001/workflow.py","pfp/workflows/wf0004/workflow.py","pfp/workflows/wf0005/rewrite.py"]},
            {"id":"WF-A03","severity":"provenance","finding":"Historical pilot imports require omega_engine_* private/runtime owners; relabelled names and paths may invalidate retained hashes. Source presence and historical receipts do not prove portable replay.","sources":["workflows/library/pilot_estate/README.md",CAMPAIGN+'README.md']},
            {"id":"WF-A04","severity":"scope","finding":"The cleaned checkout includes the retired finite-QM programme, absent at the initial audit base. Its P0-P5 contracts explicitly retain unreviewed obligations and require task-applicable independent checkers; source/layout/provider dependencies remain.","sources":[CAMPAIGN+x for x in ['README.md','workflow.yaml','mode.yaml','stage_contracts.yaml']]},
            {"id":"WF-A05","severity":"checker_limits","finding":"Challenge documentation discloses C027 dual-check limit, C049 independent checker accepting 31/48 mutants, C041 external Lean dependency, C052 missing package tests, and C058 sampled rather than exhaustive checking above 8 bits. These are disclosed historical/current-source limits, not newly reproduced test results.","sources":["workflows/tasks/certified_challenges/README.md"]},
            {"id":"WF-A06","severity":"evidence_limits","finding":"WF26 and WF27 historical improvements used answer-leaking/full-repair hints; WF28 and WF48 include reference self-scores. Do not pool them with independent model accuracy.","sources":[f"workflows/{x}/README.md" for x in ['wf26_multi_round_antibody_dialogue','wf27_hinted_retraction_with_a_stationary_loop_detector','wf28_eight_role_audit_dialogue','wf48_commit_reveal_with_a_hostile_mutation_gate']]},
            {"id":"WF-A07","severity":"benchmark_blocker","finding":"The older finite-QM prompt compiler prints computed expected values and requests JSON extraction; its gate engine matches expected certificates and some failure strings include expected values. This is extraction/finite-control checking, not blind derivation, and cannot supply answer-free repair feedback unchanged. The nested v3 programme expressly supersedes the legacy exercises.","sources":["workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/prompts/prompt_compiler.py","workflows/wf20_derivation_loop_with_lift_grants/pilots/finite_qm_derivation_pfp/gates/gate_engine.py",CAMPAIGN+'README.md']},
            {"id":"WF-A08","severity":"configuration_blocker","finding":"C001 attention-mask pipeline declares tokenizer_json_sha256 and prompt_template_digest UNSET; its pin note explicitly says NOT_READY. A pipeline file is not evidence of a ready experiment.","sources":["workflows/wf12_mechanism_control_arms/pilots/c001_attention_distractor_mask/pipeline.json"]},
        ],
        "finite_composition_recommendation":{
            "principle":"Enumerate typed finite programmes, not all 49! orderings. A workflow family, task preset, checker-development activity, campaign and harness gate have different input/output types.",
            "types":["FrozenTask","ReviewedGuidance","TypedCandidate","CheckedCandidate","BoundedResidual","ClaimScopedReceipt","CampaignReport"],
            "production":"Programme := FreezeTask ; OptionalGuidance ; CandidateStage ; Check ; BoundedRepair? ; OptionalChallenge ; Record",
            "finite_controls":{"max_candidate_stages":"preregistered positive integer","max_repairs":"preregistered nonnegative integer","max_agents":"bounded; later ten research agents are planning roles, not automatic independent solvers","max_stage_orderings":"topological orders of selected typed dependency graph","max_wrappers_per_slot":1},
            "validity_constraints":[
                "Freeze seed bytes/hash, target semantics, assumptions, checker pins, evaluation policy and budgets before dispatch.",
                "Each composition edge matches complete input/output schemas and domain hypotheses; source_dependency edges do not by themselves license execution.",
                "Task-specific presets require a checked adapter; retain inapplicable statuses rather than silently translate the benchmark.",
                "Only checked reversible representations may count as same-seed dialects; constraint changes and changed claims are separate tasks.",
                "Keep schema acceptance, finite checks, symbolic identities, numerical sanity checks and mathematical proof review distinct.",
                "Mining/challenge proposals never see private answer keys; residual feedback uses bounded failure classes and excludes expected values.",
                "Freeze isolated proposals before sharing; agreement is not an independent mathematical judge.",
                "Unroll bounded repairs/re-entry into attempt-indexed DAG nodes; never reset the root budget or hide failed attempts.",
                "Normalize equivalent schedules and identity wrappers; require at least one substantive workflow difference to call a permutation nontrivial.",
                "Campaign/held-out/transfer claims require separate preregistered populations; repeated use of one seed supports only scoped within-item comparisons."
            ]},
        "verification":{"tests_run":[],"source_modules_executed":[],"mechanical_only":True,"no_paid_api_calls":True,
            "private_benchmark_key_accessed":False,"benchmark_solution_computed":False},
        "remaining_work":[
            "Semantic review remains for every file whose ledger content_reviewed is false; prioritize active runner/checker/test sources over historical raw replies.",
            "Resolve historical/private-runtime imports and source-layout dependencies before labelling any nested pilot portable or executable.",
            "Independently assess each candidate QM adapter and test plan without reading the benchmark private key.",
            "Complete remote campaign source/test review; the present pass fully read its top-level public contracts only.",
            "Check declared source references against owning papers/code and distinguish reproduced tests from documented receipts.",
        ],
        "file_reviews_worktree":{"same_content_as_remote_main":all(row.get('same_as_worktree',False) or row['review_level']=='metadata_only_not_opened' for row in remote.values()) and set(local)==set(remote),
            "canonical_file_records":"file_reviews_remote_main","differences":[row for p,row in local.items() if p not in remote or not remote[p].get('same_as_worktree',False) and row['review_level']!='metadata_only_not_opened']},
        "file_reviews_remote_main":list(remote.values()),
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'workflows_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    md = ['# Workflow audit: inventory complete, semantic review partial','',
          f'Remote snapshot: `{REMOTE}`. Current worktree: `{head}`. Initial pre-cleanup base: `{BASE}`. The parent updated the checkout; this audit did not change it.', '',
          f"Inventoried **{len(local):,} worktree files** and **{len(remote):,} remote-main files**, excluding dot-prefixed directory ancestors but including dot filenames. This is **not** a claim that all files received semantic review. The per-file ledger records the exact depth and unread remainder; binary databases/private stores were not opened.", '',
          'The public graduate-QM seed was read to assess interfaces only; it was not solved. No provider calls, tests, or project-source execution occurred.', '',
          '## What exists','',
          f"There are 49 named workflow families, {len(reg['recorded_variations'])} recorded setting variations, {len(reg['component_nodes'])} nested pilot/task/support component groups, and {len(reg['manifest_registry'])} manifest/record candidates. Manifest rows are not automatically new workflows. Each registry row retains its source paths and source/test/checker candidates.",'',
          'WF1–WF5 have public runner source. WF6–WF49 are proposed family designs with varying amounts of historical pilot code or evidence. Historical runtime imports, redacted names, omitted source snapshots and old paths constrain replay. The cleaned checkout contains the retired finite-QM P0–P5 programme under WF20; its public contracts were read, while most implementation remains queued for deeper review. All 49 current family documents and all 46 recorded variations were read.','',
          '## Same-seed compatibility','',
          'No supplied workflow checker has been established to verify the complete unchanged graduate-QM seed. WF1–WF3 offer schema-only transport for an arbitrary prompt; mathematical acceptance still requires a task-specific checker. WF4 only admits the integer-sum checker; WF5 only decodes the exact-sum sentence language. Integer arithmetic, cochain closure, hashes, or agent agreement do not prove the QM derivation.','',
          '| Family | Current availability | Seed assessment | Required adaptation / limit |','| --- | --- | --- | --- |']
    for n in reg['family_nodes']:
        md.append(f"| {n['id']}: {n['name']} | {'Public runner source' if n['runner_source'] else 'Family proposal / source-dependent pilots'} | {n['grad_qm_seed']['status']} | {n['grad_qm_seed']['reason']} |")
    md += ['', '## Dependencies and finite permutations','',
           'Existing family edges are **documented design dependencies**, not proof implications or executable dispatch edges. Containment edges place pilots and tasks in their owning groups. Retained variations remain settings on their original families. Exact source edges and all nodes are in the JSON registry.','',
           '`FreezeTask → OptionalGuidance → Candidate → Check → BoundedRepair? → OptionalChallenge → ClaimScopedRecord`','',
           'Use a preregistered finite grammar with typed ports, bounded agents/stages/repairs, and only topological schedules satisfying task/schema/hypothesis preservation. Unroll repair loops by attempt number. Reject incompatible task presets, missing checkers, changing target assumptions, answer-bearing feedback and identity-only permutations. Normalize equivalent schedules. A future ten-agent research round should propose and audit these typed adapters; it should not treat every family as a solver or every ordering as meaningful.','',
           '## Findings and coverage','']
    for f in report['findings']:
        md.append(f"- **{f['id']} ({f['severity']}):** {f['finding']}")
    md += ['', '| Remote review depth | Files |','| --- | ---: |']
    md += [f'| {k} | {v:,} |' for k,v in coverage['remote_review_levels'].items()]
    md += ['', 'The JSON stores one canonical per-file ledger when worktree and remote content match, with only differing worktree records separately retained. Full semantic reads are pinned to the reviewed commit/blob. It includes AST symbol/import indexes, structured-format results, family/domain mechanisms, source/checker/test candidates, and substantive roles/statuses for all 96 manifest candidates. Format parsing does not establish semantic correctness; intentionally malformed fixtures can legitimately fail it.','',
           '## Unfinished work','']
    md += ['- '+x for x in report['remaining_work']]
    md += ['', 'Audit data: [workflows_audit.json](workflows_audit.json). Reproducible inventory builder: [workflows_audit_builder.py](workflows_audit_builder.py).','']
    (OUT/'workflows_audit.md').write_text('\n'.join(md),encoding='utf-8')
    print(json.dumps(coverage,indent=2))


if __name__ == '__main__':
    main()
