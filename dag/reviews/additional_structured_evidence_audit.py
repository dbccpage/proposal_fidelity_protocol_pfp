"""Read-only bounded checks of original-inventory structured evidence.

No provider calls, database access, benchmark-seed access, or source writes.
Run: .venv/Scripts/python.exe -B -X utf8 dag/reviews/additional_structured_evidence_audit.py
Outputs are confined to this helper's additional_structured_evidence prefix.
"""
from __future__ import annotations

import collections
import copy
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING

import yaml

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "dag/reviews/additional_structured_evidence"
inventory = json.loads((ROOT / "dag/file_inventory.json").read_text("utf-8"))
INV = {row["path"]: row for row in inventory["files"]}
assert len(INV) == 32261
assert not any(p.startswith(("dag/", "pilots/")) for p in INV)
STRUCTURED = {p for p in INV if pathlib.PurePosixPath(p).suffix.lower() in {".json", ".jsonl", ".yaml", ".yml"}}
REVIEWS: dict[str, dict] = {}
OBJECTS: dict[str, object] = {}
STRUCTURAL: list[dict] = []
REFS: list[dict] = []
SUMMARY: dict[str, object] = {}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def raw_at(path):
    if path not in INV:
        raise ValueError("outside_original_inventory: " + path)
    return (ROOT / path).read_bytes()


def canon(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2, allow_nan=False) + "\n").encode("ascii")


def compact(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def tag(raw):
    return "sha256:" + sha(raw)


def record(path, rule, passed, detail=None, *, kind="schema_evidence"):
    row = REVIEWS.setdefault(path, {
        "path": path, "sha256": sha(raw_at(path)), "full_source_read": False,
        "semantic_review_complete": False, "checks": [], "evidence_ceiling": [],
    })
    entry = {"rule": rule, "status": "pass" if passed is True else "fail" if passed is False else "pending"}
    if detail is not None:
        entry["detail"] = detail
    row["checks"].append(entry)
    if kind not in row["evidence_ceiling"]:
        row["evidence_ceiling"].append(kind)


def load_module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class DuplicateLoader(yaml.SafeLoader):
    """Report explicit repeated keys; merge inheritance is not a duplicate declaration."""
    def __init__(self, stream):
        super().__init__(stream)
        self.duplicates = []

    def construct_mapping(self, node, deep=False):
        seen = {}
        for key_node, _ in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=deep)
            try:
                if key in seen:
                    self.duplicates.append({"key": str(key), "line": key_node.start_mark.line + 1,
                                            "first_line": seen[key]})
                seen[key] = key_node.start_mark.line + 1
            except TypeError:
                pass  # SafeLoader below reports unsupported unhashable mapping keys.
        return super().construct_mapping(node, deep=deep)


def strict_json(text, duplicates):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                duplicates.append(key)
            out[key] = value
        return out

    def constant(value):
        raise ValueError("nonfinite JSON literal " + value)

    def float_value(value):
        n = float(value)
        if not math.isfinite(n):
            raise ValueError("JSON number outside finite binary64 range")
        return n
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant, parse_float=float_value)


def structural_scan():
    for index, path in enumerate(sorted(STRUCTURED), 1):
        raw = raw_at(path)
        row = {"path": path, "sha256": sha(raw), "inventory_sha256_matches": sha(raw) == INV[path]["sha256"],
               "full_source_read": False, "semantic_review_complete": False,
               "rule": "STRUCT-1: strict finite JSON/JSONL or SafeLoader YAML with explicit duplicate-key detection",
               "evidence_ceiling": "syntax_and_duplicate_keys_only"}
        duplicates = []
        try:
            text = raw.decode("utf-8-sig")
            suffix = pathlib.PurePosixPath(path).suffix.lower()
            if suffix == ".json":
                obj = strict_json(text, duplicates)
                if isinstance(obj, dict):
                    # Retain only schemas selected below; avoid retaining every provider transcript.
                    schema = obj.get("schema", obj.get("schema_version"))
                    if (isinstance(schema, str) and (schema.startswith(("mssn.", "level-engine.", "challenge-evidence/", "pfp.derivation-"))
                            or schema in {"pfp.contract-score.v1", "pfp.evidence-run.v1"})) or path.endswith("/judge_packet/manifest.json"):
                        OBJECTS[path] = obj
            elif suffix == ".jsonl":
                lines = 0
                for lineno, line in enumerate(text.splitlines(), 1):
                    if not line.strip():
                        continue
                    local = []
                    strict_json(line, local)
                    duplicates.extend({"line": lineno, "key": k} for k in local)
                    lines += 1
                row["records"] = lines
            else:
                loader = DuplicateLoader(text)
                try:
                    docs = 0
                    while loader.check_data():
                        loader.get_data()
                        docs += 1
                    duplicates = loader.duplicates
                    row["documents"] = docs
                finally:
                    loader.dispose()
            row["status"] = "duplicate_keys_detected" if duplicates else "parse_pass_semantics_pending"
            if duplicates:
                row["duplicate_keys"] = duplicates
        except Exception as exc:
            row["status"] = "parse_failure_context_pending"
            row["error"] = type(exc).__name__ + ": " + str(exc)[:900]
        STRUCTURAL.append(row)
        if index % 2500 == 0:
            print("structural", index, flush=True)
    SUMMARY["structural_statuses"] = dict(collections.Counter(r["status"] for r in STRUCTURAL))


def resolve_ref(owner, target, expected, normalization="RAW", size=None, kind="declared_hash"):
    result = {"owner": owner, "target": target, "declared_sha256": expected, "normalization": normalization, "kind": kind}
    if target not in INV:
        result["status"] = "unresolved_outside_original_inventory"
        REFS.append(result)
        return result
    raw = raw_at(target)
    selected = raw.replace(b"\r\n", b"\n") if normalization == "CRLF_TO_LF" else raw
    actual = sha(selected)
    exp = str(expected).removeprefix("sha256:").lower()
    result.update(actual_sha256=actual, raw_sha256=sha(raw), hash_matches=actual == exp)
    if size is not None:
        result.update(declared_size_bytes=size, actual_size_bytes=len(selected), size_matches=size == len(selected))
    result["status"] = "pass" if result["hash_matches"] and result.get("size_matches", True) else "mismatch"
    REFS.append(result)
    record(target, "REF-1: bytes match referenced manifest/receipt", result["status"] == "pass",
           {"owner": owner, "normalization": normalization, "reference_index": len(REFS)-1}, kind="referenced_bytes_only")
    return result


def challenge_manifests():
    selected = [(p, d) for p, d in OBJECTS.items() if p.endswith("/judge_packet/manifest.json")]
    for path, data in selected:
        items = data.get("files", data.get("manifest", data.get("entries")))
        if isinstance(items, dict):
            entries = [{"path": p, **(v if isinstance(v, dict) else {"sha256": v})} for p, v in items.items()]
        elif isinstance(items, list):
            entries = items
        else:
            record(path, "MAN-1: supported file table", None, "unsupported file table")
            continue
        normalization = data.get("digest_normalization", "RAW")
        record(path, "MAN-1: declared normalization supported", normalization in {"RAW", "CRLF_TO_LF"}, normalization)
        paths = [v["path"] for v in entries]
        record(path, "MAN-2: unique declared target paths", len(paths) == len(set(paths)))
        count_fields = [k for k in ("file_count", "files_count", "declared_file_count", "total_files") if k in data]
        for key in count_fields:
            record(path, "MAN-3: file count equals file table length", type(data[key]) is int and data[key] == len(entries),
                   {"field": key, "declared": data[key], "counted": len(entries)})
        if "custodied_files" in data.get("counts", {}):
            record(path, "MAN-3: custodied_files equals file table length", data["counts"]["custodied_files"] == len(entries),
                   {"declared": data["counts"]["custodied_files"], "counted": len(entries)})
        # A table containing judge_packet/... names is challenge-relative as a whole.
        # Other tables name cases/... and checkers/... relative to judge_packet.
        challenge = str(pathlib.PurePosixPath(path).parent.parent)
        judge = str(pathlib.PurePosixPath(path).parent)
        base = challenge if any(p.startswith('judge_packet/') for p in paths) else judge
        outcomes = []
        for entry in entries:
            rel = entry["path"]
            target = str(pathlib.PurePosixPath(base) / rel)
            ref = resolve_ref(path, target, entry["sha256"], normalization, entry.get("size_bytes"), "challenge_manifest")
            outcomes.append(ref["status"])
        record(path, "MAN-4: all declared hashes and sizes resolve", all(v == "pass" for v in outcomes), dict(collections.Counter(outcomes)))
        if "manifest_sha256" in data:
            body = "".join(f"{e['sha256']}  {e['path']}\n" for e in entries).encode("utf-8")
            record(path, "MAN-5: declared ordered-lines manifest digest", sha(body) == data["manifest_sha256"])
        record(path, "MAN-6: provenance ceiling retained", None,
               {"manifest_status": data.get("manifest_status", "not_declared"),
                "limit": "No pre-run commitment, complete-directory coverage, checker soundness or fixture correctness is inferred."})
    SUMMARY["challenge_manifests"] = len(selected)


def score_records():
    checker = load_module("audit_governance_checker", "governance/tools/checker.py")
    repo = checker.Repository(ROOT)
    selected = [(p,d) for p,d in OBJECTS.items() if d.get("schema_version") == "pfp.contract-score.v1"]
    for path, d in selected:
        try:
            companion = checker.Companion.model_validate_json(raw_at(path))
            record(path, "SCORE-1: owning strict Companion model", True)
            artifact = companion.artifact
            if artifact not in INV:
                record(path, "SCORE-2: artifact in original inventory", None, artifact)
                continue
            score = companion.score
            refs = [r.path for r in score.evidence]
            if score.mutation_accounting is not None:
                refs.append(score.mutation_accounting.report.path)
            if any(p not in INV for p in refs):
                record(path, "SCORE-3: cited references in original inventory", None, [p for p in refs if p not in INV])
            else:
                problems = checker.check_source(repo, artifact)
                record(path, "SCORE-4: owning check_source without grandfathering", not problems, problems)
            _, min_level, min_grade = repo.floor_for(artifact)
            problems = checker.score_problems(score, min_level, min_grade)
            if score.mutation_accounting is not None:
                problems += checker.mutation_problems(score.mutation_accounting)
            record(path, "SCORE-5: weakest gate, score token, completeness, floor and mutation ratio", not problems, problems)
            for label, ref in [("contract", companion.contract.artifact), ("score", score.artifact)]:
                resolve_ref(path, ref.path, ref.sha256, kind=label + "_source")
            for ref in score.evidence:
                resolve_ref(path, ref.path, ref.sha256, kind="score_evidence")
            if score.mutation_accounting:
                r = score.mutation_accounting.report
                resolve_ref(path, r.path, r.sha256, kind="mutation_report")
        except Exception as exc:
            record(path, "SCORE-1: owning strict Companion model and check_source", False, type(exc).__name__ + ": " + str(exc)[:600])
    runs = [(p,d) for p,d in OBJECTS.items() if d.get("schema_version") == "pfp.evidence-run.v1"]
    for path, d in runs:
        try:
            run = checker.RunRecord.model_validate_json(raw_at(path))
            record(path, "RUN-1: owning strict RunRecord model", True)
            record(path, "RUN-2: chronological recorded timestamps", run.finished >= run.started)
            outcomes = [resolve_ref(path, ref.path, ref.sha256, kind="recorded_run_input") for ref in run.inputs]
            outcomes.append(resolve_ref(path, run.report.path, run.report.sha256, kind="recorded_run_report"))
            record(path, "RUN-3: recorded input and report hashes resolve to current bytes", all(o["status"] == "pass" for o in outcomes),
                   dict(collections.Counter(o["status"] for o in outcomes)))
            record(path, "RUN-4: execution claim remains historical", None,
                   {"recorded_exit_status": run.exit_status, "limit": "No command rerun, signature verification, or attestation of actual execution."})
        except Exception as exc:
            record(path, "RUN-1: owning strict RunRecord model", False, type(exc).__name__ + ": " + str(exc)[:500])
    SUMMARY.update(contract_scores=len(selected), evidence_runs=len(runs))


def get_json(path):
    return json.loads(raw_at(path).decode("utf-8-sig"))


def tower_records():
    sys.path.insert(0, str(ROOT))
    from pfp.infrastructure.tower_research.reach import schema as reach_schema, transport
    schemas = {"mssn.loss-ledger.v2", "mssn.witness-bundle.v1", "mssn.witness-bundle.v2",
               "challenge-evidence/1", "challenge-evidence/2", "mssn.transport-certificate.v2",
               "level-engine.checker-input.v1", "level-engine.bundle-index.v1"}
    chosen = [(p,d) for p,d in OBJECTS.items() if p.startswith("pfp/infrastructure/tower_evidence/level_engine/") and d.get("schema") in schemas]
    addressed = {}
    for p, d in chosen:
        if re.fullmatch(r"[0-9a-f]{64}(?:\.evidence|\.loss)?\.json", pathlib.PurePosixPath(p).name):
            addressed[(p.split('/bundles/')[0], pathlib.PurePosixPath(p).name[:64])] = p
    def link(owner, digest):
        base = owner.split('/bundles/')[0] if '/bundles/' in owner else owner.split('/bindings/')[0]
        target = addressed.get((base, str(digest).removeprefix('sha256:')))
        if not target:
            record(owner, "TOWER-2: linked content address resolves in same version", False, {"digest": digest})
        else:
            result = resolve_ref(owner, target, digest, kind="tower_content_address")
            record(owner, "TOWER-2: linked content address resolves in same version", result["status"] == "pass", target)
        return target
    def no_floats(value):
        if isinstance(value, float):
            return False
        if isinstance(value, list):
            return all(no_floats(v) for v in value)
        if isinstance(value, dict):
            return all(isinstance(k, str) and no_floats(v) for k,v in value.items())
        return value is None or isinstance(value, (str,int,bool))
    for path, d in chosen:
        try:
            raw = raw_at(path)
            schema = d['schema']
            record(path, "TOWER-1: declared sorted-ASCII two-space LF no-float bytes", raw == canon(d) and no_floats(d))
            if '/bundles/' in path and pathlib.PurePosixPath(path).name != 'INDEX.json':
                record(path, "TOWER-2: filename is exact raw-byte SHA-256", pathlib.PurePosixPath(path).name[:64] == sha(raw))
            if schema == "mssn.loss-ledger.v2":
                counts = dict(collections.Counter(row["classification"] for row in d['fields']))
                body = {k:v for k,v in d.items() if k not in {"authority_effect", "schema", "commitment"}}
                record(path, "TOWER-3: loss classification counts", d['count'] == counts, {"counted": counts})
                record(path, "TOWER-4: loss body commitment excludes schema/authority/commitment", d['commitment'] == tag(canon(body)))
                record(path, "TOWER-5: loss ceiling remains PROPOSED", d['status_ceiling'] == 'PROPOSED' and d['authority_effect'] == 'None')
            elif schema.startswith('mssn.witness-bundle.'):
                link(path, d['loss_ledger_sha256'])
                if schema.endswith('v1'):
                    for source in d['carrier']['sources']:
                        if source['path'].startswith('challenge-evidence:'):
                            link(path, source['sha256'])
                    record(path, "TOWER-6: v1 external source provenance unresolved", None,
                           "Vendor source digests and historical harness imports are not current installed-resource verification.")
                else:
                    link(path, d['evidence_sha256'])
                    impl = d['implementation']
                    record(path, "TOWER-6: installed implementation source table commitment", impl['source_manifest_sha256'] == tag(canon(impl['sources'])))
                    outcomes = []
                    for src in impl['sources']:
                        target = 'pfp/infrastructure/tower_research/level_engine/' + src['path']
                        outcomes.append(resolve_ref(path, target, src['sha256'], kind='installed_resource_current_bytes')['status'])
                    record(path, "TOWER-7: historical installed-resource hashes versus current source", all(o == 'pass' for o in outcomes), dict(collections.Counter(outcomes)))
                    carrier = d['carrier']
                    expected = (carrier.get('source_basis') == 'pinned_vendor_git' and bool(carrier.get('commit'))) if carrier['part'] == 'repo_content' else (
                        carrier.get('source_basis') == 'installed_package_resources' and carrier.get('commit') is None)
                    record(path, "TOWER-8: vendor commit and installed-resource provenance stay distinct", expected)
            elif schema.startswith('challenge-evidence/'):
                census = d['clause_census']
                # LevelResult.census_json maps each clause id to census/changed_on.
                classes = [row['census'] for row in census.values()]
                answer = 'M' if 'decoded' in classes else 'D' if 'derivability' in classes else 'A'
                record(path, "TOWER-9: answer-type and native-share from declared census", d['answer_type_computed'] == answer and d['native_share'] == f"{classes.count('derivability')} of {len(classes)}")
                expected = 'MISMATCH' if d['mismatches'] else 'UNRESOLVED' if d['missing_components'] else 'EXPECTED'
                record(path, "TOWER-10: status from declared mismatches/missing components", d['status'] == expected)
            elif schema == 'mssn.transport-certificate.v2':
                payload = {k:v for k,v in d.items() if k != 'envelope'}
                envelope = d['envelope']
                record(path, "TOWER-11: domain-separated payload digest", envelope['payload_digest'] == tag(b'mssn.transport-certificate\0' + canon(payload)))
                without = copy.deepcopy(d); without['envelope'].pop('record_digest')
                record(path, "TOWER-12: record digest excludes itself", envelope['record_digest'] == tag(canon(without)))
                target = link(path, d['c1_identity_custody']['source_manifest_sha256'])
                link(path, d['c6_loss_and_authority']['loss_ledger_sha256'])
                if target:
                    positive = get_json(target)['target_input']
                    record(path, "TOWER-13: payload and witness hash match linked bundle input", d['c1_identity_custody']['payload_sha256'] == d['c5_target_verification']['witness_sha256'] == tag(canon(positive)))
                record(path, "TOWER-14: proposed transport does not assert target replay", d['status'] == 'PROPOSED' and d['disposition'] == 'TARGET_REPLAY_REQUIRED' and d['c5_target_verification']['verdict'] == 'PENDING')
                try:
                    reach_schema.validate(d, transport.CERTIFICATE)
                    receiver_shape = True
                    receiver_detail = 'Schema only; independent expectation and mathematical transport criteria not replayed.'
                except reach_schema.SchemaError as exc:
                    receiver_shape = False
                    receiver_detail = {'code': exc.code, 'detail': exc.detail,
                                       'limit': 'Draft producer records and receiving runtime schema are distinct; no target admission asserted.'}
                record(path, "TOWER-17: receiving transport.CERTIFICATE closed schema", receiver_shape, receiver_detail)
            elif schema == 'level-engine.checker-input.v1':
                outcomes = [f['input_sha256'] == tag(canon(f['input'])) for f in d['fixtures']]
                record(path, "TOWER-15: every embedded fixture input digest", all(outcomes), {"fixtures": len(outcomes)})
                ids = [f['id'] for f in d['fixtures']]
                record(path, "TOWER-16: unique fixture IDs", len(ids) == len(set(ids)))
            elif schema == 'level-engine.bundle-index.v1':
                for group in d['records'].values():
                    for digest in group.values():
                        link(path, digest)
        except Exception as exc:
            record(path, "TOWER-UNSUPPORTED: schema condition not validated", None, type(exc).__name__ + ': ' + str(exc)[:300])
    SUMMARY['tower_records'] = len(chosen)


def derivation_records():
    selected = [(p,d) for p,d in OBJECTS.items() if d.get('schema') == 'pfp.derivation-run.v1']
    for path, config in selected:
        folder = str(pathlib.PurePosixPath(path).parent)
        try:
            terminal_path, snapshot_path = folder + '/terminal.json', folder + '/budget_snapshot.json'
            terminal, snapshot = get_json(terminal_path), get_json(snapshot_path)
            profile_path = folder + '/pricing_profile.json'
            profile = get_json(profile_path) if profile_path in INV else None
            rate = Decimal(profile['ceiling_usd_per_token']) if profile is not None else Decimal(0)
            record(path, "DERIV-1: v1 config/terminal identity and declared limits", terminal['pilot_id'] == config['pilot_id'] and terminal['limits'] == config['limits'])
            rows = []
            receipt_paths = sorted(p for p in INV if p.startswith(folder + '/loop_') and p.endswith('/provider_receipt.json'))
            for rp in receipt_paths:
                receipt = get_json(rp); loopdir = str(pathlib.PurePosixPath(rp).parent)
                raw_path, prompt_path, request_path = [loopdir + '/' + n for n in ('raw_reply.json','prompt.json','request.json')]
                raw, prompt, request = get_json(raw_path), get_json(prompt_path), raw_at(request_path)
                maximum = prompt.get('max_output_tokens', 2500) if 'experiment_decoding' in prompt else 2500
                usage = raw['usage']
                integer_usage = all(type(usage.get(k)) is int and usage[k] >= 0 for k in ('prompt_tokens','completion_tokens','total_tokens'))
                usage_ok = integer_usage and usage['total_tokens'] == usage['prompt_tokens'] + usage['completion_tokens'] and usage['completion_tokens'] <= maximum
                record(raw_path, "DERIV-2: exact nonnegative token sum and declared output cap", usage_ok)
                cost = Decimal(str(usage['cost']))
                cost_ok = cost.is_finite() and cost >= 0
                micro = int((cost * 1000000).to_integral_value(rounding=ROUND_CEILING)) if cost_ok else None
                fields = {'generation_id': raw['id'], 'tokens': usage['total_tokens'], 'usage': usage,
                          'cost_microusd': micro, 'finish_reason': raw['choices'][0].get('finish_reason')}
                record(rp, "DERIV-3: receipt agrees with raw provider fields and ceiling microusd", cost_ok and all(receipt.get(k) == v for k,v in fields.items()))
                record(rp, "DERIV-4: provider recorded model matches configured model", raw.get('model') == config['model'])
                resolve_ref(rp, raw_path, receipt['raw_sha256'], kind='provider_raw_response')
                resolve_ref(rp, request_path, receipt['request_sha256'], kind='provider_wire_request')
                record(rp, "DERIV-5: prompt digest uses declared v1 compact UTF8 canonicalization", receipt['prompt_sha256'] == sha(compact(prompt)))
                record(prompt_path, "DERIV-5: referenced v1 canonical prompt digest", receipt['prompt_sha256'] == sha(compact(prompt)), {'owner': rp})
                seq = int(pathlib.PurePosixPath(loopdir).name.split('_')[1]); attempt = snapshot['attempts'][str(seq)]
                hold = len(request) + 512 + maximum
                reserve = int((rate * hold * 1000000).to_integral_value(rounding=ROUND_CEILING))
                checks = (attempt['state'] == 'settled' and attempt['sequence'] == seq and attempt['actual'] == micro
                          and attempt['generation_id'] == raw['id'] and attempt['tokens'] == usage['total_tokens']
                          and attempt['prompt_sha256'] == receipt['prompt_sha256'] and attempt['request_sha256'] == receipt['request_sha256']
                          and attempt['token_hold'] == hold and attempt['reserved'] == reserve)
                record(snapshot_path, "DERIV-6: settled attempt agrees with receipt and v1 reservation", checks, {'sequence':seq})
                rows.append(receipt)
            attempts = snapshot['attempts']; unresolved = [a for a in attempts.values() if a['state'] != 'settled']
            expected_spent = sum(r['cost_microusd'] for r in rows) + sum(a['reserved'] for a in unresolved)
            record(snapshot_path, "DERIV-7: settled spend plus unresolved reservations", snapshot['spent'] == expected_spent)
            record(snapshot_path, "DERIV-8: attempt sequence and configured ceiling", set(attempts) == {str(i) for i in range(1,len(attempts)+1)} and len(attempts) <= config['limits']['loops'] and snapshot['limit'] == config['limits']['microusd'])
            expected = {'settled_calls': len(rows), 'provider_calls':len(attempts), 'tokens': sum(r['tokens'] for r in rows), 'cost_microusd':snapshot['spent']}
            record(terminal_path, "DERIV-9: terminal counts/tokens/cost reconcile with retained JSON records", all(terminal[k] == v for k,v in expected.items()), expected)
            record(terminal_path, "DERIV-10: sequence of settled generation IDs is unique", len({r['generation_id'] for r in rows}) == len(rows))
            record(terminal_path, "DERIV-11: analytical claims remain unverified", terminal.get('analytical_status') == 'UNVERIFIED')
            record(path, "DERIV-12: bounded replay scope", None,
                   "Read-only JSON cross-check only: database, source runtime imports, prompt lineage generator, observer, external provider authenticity and substantive proposal correctness not re-executed.")
        except Exception as exc:
            record(path, "DERIV-UNSUPPORTED: schema condition not validated", None, type(exc).__name__ + ': ' + str(exc)[:400])
    SUMMARY['derivation_runs_v1'] = len(selected)


def main():
    structural_scan()
    print('schema checks', flush=True)
    challenge_manifests()
    score_records()
    tower_records()
    derivation_records()
    for row in REVIEWS.values():
        statuses = {c['status'] for c in row['checks']}
        row['status'] = 'bounded_check_failure' if 'fail' in statuses else 'bounded_checks_pass_with_open_obligations' if 'pending' in statuses else 'bounded_checks_pass'
    unsupported = [{'path':p, 'sha256':INV[p]['sha256'], 'status':'semantic_and_schema_review_pending',
                    'reason':'No schema-specific arithmetic/validation rule executed; structural parsing and any referenced-byte checks do not discharge this obligation.'}
                   for p in sorted(STRUCTURED) if p not in REVIEWS or 'schema_evidence' not in REVIEWS[p]['evidence_ceiling']]
    SUMMARY.update(original_inventory_files=len(INV), structured_files=len(STRUCTURED), automated_files=len(REVIEWS),
        schema_specific_files=sum('schema_evidence' in r['evidence_ceiling'] for r in REVIEWS.values()),
        referenced_only_files=sum(r['evidence_ceiling'] == ['referenced_bytes_only'] for r in REVIEWS.values()),
        unsupported_structured_files=len(unsupported), reference_statuses=dict(collections.Counter(r['status'] for r in REFS)),
        automatic_statuses=dict(collections.Counter(r['status'] for r in REVIEWS.values())))
    for suffix, rows in [('_structural.jsonl', STRUCTURAL), ('_automated.jsonl', sorted(REVIEWS.values(),key=lambda r:r['path'])),
                         ('_references.jsonl', REFS), ('_unsupported.jsonl', unsupported)]:
        pathlib.Path(str(OUT)+suffix).write_text(''.join(json.dumps(row,ensure_ascii=True,separators=(',',':'))+'\n' for row in rows), encoding='utf-8', newline='\n')
    pathlib.Path(str(OUT)+'_counts.json').write_text(json.dumps(SUMMARY,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(SUMMARY,indent=2), flush=True)


if __name__ == '__main__':
    main()
