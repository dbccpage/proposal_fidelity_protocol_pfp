"""Host executors and anti-op detectors for the OEWAS resolver, registered by op id.

Only host code registers an executor; model output is data and cannot add one. An op with no
executor here is ``NOT_EXECUTABLE`` and ``run`` refuses before calling anything.

The five current skills have bounded explicit host adapters. The source-list
scanner keeps its path API. The remaining lexical/layout/purge adapters accept
explicit path-to-text mappings, at most128 documents/1MiB. Purging returns a
candidate and leaves source files untouched; receipt auditing checks byte
bindings and never certifies a general semantic claim.

AuthorityEffect: None.
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import io
import sys
import tokenize
from collections import Counter
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from types import MappingProxyType

from omega_engine_operations.use_cases.verification.silent_failure_hunter import (
    SilentFailureFinding,
    scan_directory,
    scan_file,
)

from .resolver import Detector, Executor, digest

_SOURCE_SUFFIXES = (".py", ".rs")


def _input_finding(path: str, message: str) -> dict[str, object]:
    return asdict(SilentFailureFinding("SFH-INPUT-000", path, 1, 0, message, ""))


def _scan(paths: object) -> list[dict[str, object]]:
    """Scan every target; a target that cannot be scanned is a finding, never silence."""
    if type(paths) is not list or any(type(path) is not str for path in paths):
        return [_input_finding(
            repr(paths)[:120], "Code slot must be a JSON list of path strings; scan incomplete"
        )]
    findings: list[dict[str, object]] = []
    for path in sorted(paths):
        target = Path(path)
        if target.is_dir():
            findings.extend(asdict(finding) for finding in scan_directory(target))
        elif target.suffix.lower() in _SOURCE_SUFFIXES:
            findings.extend(asdict(finding) for finding in scan_file(target))
        elif target.is_file():
            findings.append(
                _input_finding(path, "Target is not a .py or .rs source; scan incomplete")
            )
        else:
            findings.append(_input_finding(path, "Target unavailable; scan incomplete"))
    return findings


def _report(findings: list[dict[str, object]]) -> dict[str, object]:
    counts = Counter(str(finding["rule_id"]) for finding in findings)
    return {
        "skill": "techne-silent-failure-hunter",
        "status": "FAIL" if findings else "PASS",
        "findings_by_rule": dict(sorted(counts.items())),
        "authority_effect": "None",
    }


def _fires_on(rule_id: str) -> Detector:
    def detect(paths: list[str]) -> bool:
        return any(finding["rule_id"] == rule_id for finding in _scan(paths))

    return detect


def _documents(value):
    """Explicit bounded text documents; no recursive estate scan or file mutation."""
    if not isinstance(value, dict) or len(value)>128 or any(not isinstance(k,str) or not isinstance(v,str) for k,v in value.items()):
        raise ValueError("expected at most128 path-to-source strings")
    if sum(len(v.encode("utf8")) for v in value.values())>1048576:
        raise ValueError("source bound exceeded")
    return value


def _glossa_prose(value):
    from omega_engine_research_papers.use_cases.paper_iteration.paper_preflight import gate_hype
    return [asdict(hit) for name,body in sorted(_documents(value).items()) for hit in gate_hype(Path(name),body)]


def _glossa_code(value):
    docs={}
    for name,body in _documents(value).items():
        if not name.endswith(".py"):
            raise ValueError("code lexical audit supports Python comments/docstrings")
        tree=ast.parse(body)
        texts=[ast.get_docstring(n) for n in ast.walk(tree) if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
        texts += [t.string for t in tokenize.generate_tokens(io.StringIO(body).readline) if t.type==tokenize.COMMENT]
        docs[name]="\n".join(t for t in texts if t)
    return _glossa_prose(docs)


def _glossa_merge(left,right):
    return sorted(left+right,key=lambda h:(str(h.get("path","")),str(h.get("line",""))))


def _glossa_replacements(hits):
    return [{"finding":hit,"suggestion":"State the finite scope, assumptions and deciding check.","applied":False} for hit in hits]


def _glossa_report(suggestions):
    return {"status":"LINT_DIFF_PRODUCED" if suggestions else "COMPLIANT","suggestions":suggestions,"authority_effect":"None","scope":"lexical findings, not truth verification"}


def _claim_envelope_missing(value):
    required=("supports", "does not support", "narrowest claim", "next test")
    return any(any(part not in body.lower() for part in required) for body in _documents(value).values())


def _gti_shadow(value):
    docs=_documents(value)
    return [{"code":"STDLIB_SHADOW", "path":name} for name in docs if Path(name).stem in sys.stdlib_module_names]


def _gti_layout(value):
    docs=_documents(value)
    return [{"code":"UNSCOPED_TEST", "path":name} for name in docs if Path(name).name.startswith("test_") and "tests" not in Path(name).parts]


def _gti_receipt(left,right):
    return {"status":"FAIL" if left or right else "PASS", "findings":left+right,"scope":"supplied source files only","authority_effect":"None"}


def _gti_path_hack(value):
    for name,body in _documents(value).items():
        if not Path(name).name.startswith("test_") or not name.endswith(".py"):
            continue
        for node in ast.walk(ast.parse(body)):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id=="sys" and node.attr=="path":
                return True
    return False


def _gti_collision(value):
    names=[Path(p).name for p in _documents(value) if Path(p).name.startswith("test_")]
    return len(names)!=len(set(names))


def _ara_bind(value):
    if not isinstance(value,dict) or set(value)!={"paths","omitted_variables"} or not isinstance(value["paths"],list) or len(value["paths"])>128:
        raise ValueError("State requires bounded paths and explicit omitted_variables")
    sources={}
    for name in value["paths"]:
        path=Path(name)
        if path.stat().st_size>1048576:
            raise ValueError("source too large")
        sources[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    return {"sources":sources,"omitted_variables":value["omitted_variables"]}


def _ara_mutated(ledger):
    return any(not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha for p,sha in ledger["sources"].items())


def _ara_refute(ledger,audit):
    claims=audit.get("source_hashes") if isinstance(audit,dict) else None
    valid=claims==ledger["sources"] and bool(claims)
    return {"status":"SOURCE_BINDINGS_MATCH" if valid else "REFUTED", "ledger":ledger,"claim":audit,"scope":"source-byte equality only; semantic claims unverified"}


def _ara_receipt(value):
    if _ara_mutated(value["ledger"]):
        raise ValueError("source changed after audit")
    return dict(value,authority_effect="None")


def _ara_omissions(value):
    return not isinstance(value,dict) or "omitted_variables" not in value or not isinstance(value["omitted_variables"],list)


def _mnc_purge(value):
    docs=_documents(value)
    path=Path(__file__).resolve().parents[3]/"omega_engine_operads/skills/meta-no-comments/scripts/purge_comments.py"
    spec=importlib.util.spec_from_file_location("oewas_comment_owner",path.resolve())
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    output={}
    for name,body in docs.items():
        if module.is_doc_file(Path(name)) or module.is_test_file(Path(name)):
            output[name]=body
            continue
        if not name.endswith(".py"):
            raise ValueError("bounded executor supports Python; native-language purge needs its own semantic checker")
        cleaned=module.purge_python_comments(body)
        if ast.dump(ast.parse(body))!=ast.dump(ast.parse(cleaned)):
            raise ValueError("purge changes Python AST")
        output[name]=cleaned
    return {"sources":output,"input_digest":digest(docs),"output_digest":digest(output)}


def _mnc_gate(proposal,audit):
    if not isinstance(audit,dict) or audit.get("findings_count")!=0 or audit.get("input_digest")!=proposal["input_digest"] or audit.get("output_digest")!=proposal["output_digest"]:
        raise ValueError("bound zero-finding audit required")
    return proposal["sources"]


HOST_EXECUTORS: Mapping[str, Executor] = MappingProxyType({
    "sfh.scan": _scan, "sfh.report": _report,
    "glossa.scan_hype_prose":_glossa_prose,"glossa.scan_hype_code":_glossa_code,
    "glossa.merge_hits":_glossa_merge,"glossa.propose_replacements":_glossa_replacements,"glossa.report":_glossa_report,
    "gti.shadow_scan":_gti_shadow,"gti.layout_check":_gti_layout,"gti.receipt":_gti_receipt,
    "ara.bind_source_hashes":_ara_bind,"ara.refute":_ara_refute,"ara.receipt":_ara_receipt,
    "mnc.purge":_mnc_purge,"mnc.gate":_mnc_gate,
})
HOST_DETECTORS: Mapping[str, Detector] = MappingProxyType({
    "sfh.refuse_bare_except": _fires_on("SFH-PY-001"),
    "sfh.refuse_pass_handler": _fires_on("SFH-PY-002"),
    "sfh.refuse_rust_unwrap": _fires_on("SFH-RS-001"),
    "glossa.refuse_missing_claim_envelope":_claim_envelope_missing,
    "gti.refuse_sys_path_hack":_gti_path_hack,"gti.refuse_duplicate_test_basename":_gti_collision,
    "ara.refuse_unrecomputed_hash":_ara_mutated,"ara.refuse_undeclared_omission":_ara_omissions,
})


def executable_coverage(inventory):
    return {s.skill_id:all(o.op_id in HOST_EXECUTORS for o in s.ops) and all(a.op_id in HOST_DETECTORS for a in s.anti_ops) for s in inventory.skills}


class AdmittedAntiSkillDetector:
    """Bind existing typed anti-skill identity to OEEIS native activation.

    The selected host supplies the hit producer, danger sensor, current admission
    and health ports. A textual op label cannot grant detector authority.
    """
    def __init__(self, spec, hit_detector, *, profile_digest, subject_scope, sensor, guard_state, host_health):
        from omega_engine_operads.domain.anti_skills.anti_skill_v2 import AntiSkillSpecV2
        if type(spec) is not AntiSkillSpecV2:
            raise TypeError("existing AntiSkillSpecV2 required")
        self.spec_id=spec.spec_id
        self.hit_detector=hit_detector
        self.profile_digest=profile_digest
        self.subject_scope=subject_scope
        self.sensor=sensor
        self.guard_state=guard_state
        self.host_health=host_health
        self.last_activation=None

    def __call__(self,subject):
        from omega_engine_epistemic_immune_system.use_cases.guard_activation import activate_learned_guard
        if type(subject) is not str:
            raise TypeError("typed detector receives exact subject text")
        hit=self.hit_detector(subject)
        from omega_engine_epistemic_immune_system.domain.guard_activation import ActivationRefusal
        try:
            self.last_activation=activate_learned_guard(self.profile_digest,self.spec_id,hit,subject,subject_scope=self.subject_scope,sensor=self.sensor,guard_state=self.guard_state,host_health=self.host_health,disposition="REFUSE")
        except ActivationRefusal as exc:
            self.last_activation={"state":exc.code,"spec_id":self.spec_id,"subject_digest":hashlib.sha256(subject.encode("utf8")).hexdigest()}
            if exc.code in {"NO_DETECTOR_MATCH","NO_DANGER_SIGNAL","SUSPENDED"}:
                return False
            raise
        return hit is not None and self.last_activation.disposition == "REFUSE"
