"""Freeze signal independence and ASCII match-set digests before the native port."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

from omega_engine_epistemic_immune_system.domain.danger_signals import (
    SignalIndependenceRefusal,
    assert_signals_independent,
    signal1_digest,
)
from omega_engine_epistemic_immune_system.domain.value_objects import Signal1Match, Signal2Danger


def projected_match(value):
    return {"epitope_name":value.epitope_name,"pattern_matched":value.pattern_matched,"offset":value.offset}


def projected_danger(value):
    return None if value is None else {key:getattr(value,key) for key in ("danger_type","observer_id","evidence_digest","defect_count","evidence_spans")}


def main():
    matches = [Signal1Match("fixture","proposal",offset=2)]
    danger = Signal2Danger(danger_type="REPLAY_FAILURE",observer_id="host.check",evidence_digest="sha256:"+"3"*64,evidence_spans=((20,25),))
    base = {"matches":matches,"danger":danger,"detector_id":"regex","detector_predicates":frozenset(),"offsets_are_content":True}
    cases = [base, {**base,"danger":None}, {**base,"danger":None,"detector_id":""},
        {**base,"detector_id":""}, {**base,"detector_id":" \t"},
        {**base,"danger":dataclasses.replace(danger,observer_id="")},
        {**base,"danger":dataclasses.replace(danger,observer_id=" \u001f")},
    ]
    for observer in ("MODEL"," model ","LLM","Agent","detector","MATCHER","Regex"," REGEX ","Host.Check","ß","\nMODEL\t","MODEL'","\"MODEL'\\","MODEL\u00a0","MODEL\u200b"):
        cases.append({**base,"danger":dataclasses.replace(danger,observer_id=observer)})
    cases.extend([
        {**base,"detector_id":"Straße","danger":dataclasses.replace(danger,observer_id="STRASSE")},
        {**base,"detector_id":"σ","danger":dataclasses.replace(danger,observer_id="ς")},
        {**base,"detector_id":"İ","danger":dataclasses.replace(danger,observer_id="i\u0307")},
        {**base,"danger":dataclasses.replace(danger,danger_type="unknown")},
        {**base,"danger":dataclasses.replace(danger,danger_type="bad'kind")},
        {**base,"danger":dataclasses.replace(danger,danger_type='bad\"kind')},
        {**base,"danger":dataclasses.replace(danger,danger_type="bad'\"\\\n\r\t\x00\x7f\u00a0\u200b")},
        {**base,"danger":dataclasses.replace(danger,danger_type="bad\u2028\U000e0001")},
        {**base,"detector_predicates":frozenset({"REPLAY_FAILURE"})},
        {**base,"danger":dataclasses.replace(danger,evidence_digest=signal1_digest(matches))},
        {**base,"matches":[],"danger":dataclasses.replace(danger,evidence_digest=signal1_digest([]))},
        {**base,"danger":dataclasses.replace(danger,defect_count=0)},
        {**base,"danger":dataclasses.replace(danger,defect_count=10**90)},
        {**base,"danger":dataclasses.replace(danger,evidence_digest="🦀"*30)},
        {**base,"matches":[Signal1Match("fixture","",offset=2)],"danger":dataclasses.replace(danger,evidence_spans=((2,3),))},
        {**base,"matches":[Signal1Match("fixture","🙂核",offset=10**90)],"danger":dataclasses.replace(danger,evidence_spans=((10**90+1,10**90+2),))},
    ])
    for span in ((0,2),(1,3),(2,9),(3,4),(8,9),(9,10),(20,25)):
        for offsets in (True,False):
            cases.append({**base,"danger":dataclasses.replace(danger,evidence_spans=(span,)),"offsets_are_content":offsets})
    cases.extend([
        {**base,"danger":dataclasses.replace(danger,evidence_digest=signal1_digest(matches),observer_id="MODEL",danger_type="unknown")},
        {**base,"danger":dataclasses.replace(danger,evidence_digest=signal1_digest(matches),danger_type="unknown")},
        {**base,"detector_predicates":frozenset({"REPLAY_FAILURE"}),"danger":dataclasses.replace(danger,evidence_digest=signal1_digest(matches))},
    ])
    rows = []
    for case in cases:
        try:
            expected = {"ok":assert_signals_independent(**case)}
        except (SignalIndependenceRefusal,ValueError) as exc:
            code = exc.code if isinstance(exc,SignalIndependenceRefusal) else "EIS_VALUE_ERROR"
            expected = {"error":{"code":code,"message":str(exc) if isinstance(exc,SignalIndependenceRefusal) else f"{code}: {exc}"}}
        rows.append({"input":{**case,"matches":[projected_match(value) for value in case["matches"]],"danger":projected_danger(case["danger"]),"detector_predicates":sorted(case["detector_predicates"])},"expected":expected})
    sets = [[],matches,list(reversed(matches)),[Signal1Match("é","核🙂",offset=10**90)],
        [Signal1Match("quote'\"\\","\n\r\t\b\f\x00\x1f\x7f\u0085\u200b",offset=0)],
        [Signal1Match("a","x",offset=10),Signal1Match("a","x",offset=2)],
        [Signal1Match("z","last",offset=0),Signal1Match("a","first",offset=1)],
    ]
    digest_rows = [{"input":[projected_match(value) for value in values],"expected":signal1_digest(values)} for values in sets]
    path=Path(__file__).resolve().parents[2]/"omega_engine/crates_rs/tests/omega_epistemic_immune_system/fixtures/python_independence_v1.json"
    path.write_text(json.dumps({"vectors":rows,"digests":digest_rows},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Frozen {len(rows)} independence and {len(digest_rows)} match-digest vectors before implementation.")


if __name__=="__main__":
    main()
