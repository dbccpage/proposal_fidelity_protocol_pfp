"""Read-only algorithm probes; temporary event-log fixtures stay under reviews.

No implementation repair, external service, private benchmark, or answer key.
These are finite counterexamples, not general certification of the subsystems.
"""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def run() -> dict:
    from eis.domain.value_objects import DetectorRule, Signal1Match
    from eis.domain.pharmacy_seeder import PharmacySeeder
    from operads.skill_operad.domain.evidence import Residual
    from operads.skill_operad.domain.hott import Path as OperadicPath
    from pciv.domain.lamarckian import CochainResidualV1
    from pciv.domain.models import ProtectedSpanV1
    from pciv.infrastructure.event_log import DurableEventLogV1, PromptCivEventV1
    from pciv.use_cases.fitness import ParetoFrontSelectorV1, reduce_selected_attempt_outcome
    from pciv.use_cases.immunity import LineageTaintEngineV1
    from pciv.use_cases.lamarckian_loop import LamarckianLoopService

    results = {}
    results["default_pharmacy_root"] = {"expected": str(ROOT), "actual": str(PharmacySeeder().repo_root), "matches_repository": PharmacySeeder().repo_root.resolve() == ROOT}
    try:
        results["singleton_pareto"] = {"output": ParetoFrontSelectorV1().partition_fronts([{"id":"one","metrics":{"correctness":1,"cost":1}}])}
    except Exception as exc:
        results["singleton_pareto"] = {"error_type":type(exc).__name__,"error":str(exc)}
    a,b,c = [Residual(claims=(name,),risk=risk) for name,risk in [("a",1.0),("b",float("nan")),("c",2.0)]]
    results["nan_residual_associativity"] = {"left_risk":a.absorb(b).absorb(c).risk,"right_risk":a.absorb(b.absorb(c)).risk}
    for cls, kwargs, field in [(DetectorRule,{"rule_id":"r","target_epitope":"e","match_pattern":"x"},"affinity_score"),(Signal1Match,{"epitope_name":"e","pattern_matched":"x"},"confidence")]:
        a=cls(**kwargs,**{field:0.1234564999}); b=cls(**kwargs,**{field:0.1234565001})
        results[cls.__name__+"_hash_consistency"]={"equal":a==b,"same_hash":hash(a)==hash(b),"set_size":len({a,b})}
    results["string_endpoint_collision"]={"valid":OperadicPath(0,1).concat(OperadicPath("1","two")).is_valid}
    results["empty_mandatory_allowed_outcome"]={"result":reduce_selected_attempt_outcome([],"AllowedTask")}
    taint=[]
    for edges in [[("a","b"),("b","c")],[("b","c"),("a","b")]]:
        engine=LineageTaintEngineV1();engine.mark_tainted("a");engine.propagate_taint(edges)
        taint.append({"edges":edges,"tainted":{n:engine.is_tainted(n) for n in ("a","b","c")}})
    results["taint_order_dependence"]=taint
    probe_root=ROOT/"dag/reviews"
    with TemporaryDirectory(prefix="systems_probe_",dir=probe_root) as folder:
        resolved=Path(folder).resolve()
        assert resolved.is_relative_to(probe_root.resolve())
        log_path=resolved/"event_log.jsonl"; log_path.mkdir()
        first=DurableEventLogV1(log_file=log_path)
        first.append_event(PromptCivEventV1("p","ExecutionPass","r","o","s",1,{"prompt_id":"x"}))
        reopened=DurableEventLogV1(log_file=log_path)
        results["event_log_silent_write_failure"]={"append_returned_successfully":True,"first_count":first.event_count(),"reopened_count":reopened.event_count(),"log_is_directory":log_path.is_dir()}
    try:
        value=LamarckianLoopService().execute_loop(parent_prompt_bytes=b"xxCOREyy",parent_genome_id="sha256:"+"a"*64,protected_spans=(ProtectedSpanV1("core",2,6),),generation=0,falsification_witness_sha256="b"*64,cochain_residual=CochainResidualV1.from_fractions(),antibody_id="ab",guidance_text="guidance",edit_start_byte=0,edit_end_byte=0)
        results["pre_span_mutation"]={"mutation_applied":value.mutation_applied}
    except Exception as exc:
        results["pre_span_mutation"]={"error_type":type(exc).__name__,"error":str(exc)}
    return {"schema":"pfp.systems-audit-probes.v1","head":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),"results":results}


if __name__ == "__main__":
    result=run()
    (ROOT/"dag/reviews/systems_audit_probe_results.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
