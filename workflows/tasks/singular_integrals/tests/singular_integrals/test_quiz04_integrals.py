from collections import Counter
from copy import deepcopy
from fractions import Fraction as Q
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
from types import SimpleNamespace

import pytest

RUNNER = Path(os.environ.get("PFP_PILOT_000013_UNDER_TEST", Path(__file__).resolve().parents[2] / "run.py"))
spec = importlib.util.spec_from_file_location("quiz04_under_test", RUNNER)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def text(value):
    value = Q(value)
    return f"{value.numerator}/{value.denominator}"


def term(c, ratio):
    c, ratio = Q(c), Q(ratio)
    if not c or ratio == 1:
        return {"coefficient": "0/1", "log_argument": "1/1"}
    sign = 1 if ratio > 1 else -1
    return {"coefficient": text(c * sign), "log_argument": text(max(ratio, 1 / ratio))}


def task(a=0, pole=5, b=10, c=1, mode="ordinary", alpha=1, beta=1):
    value = {"task_id": "old1" if mode == "ordinary" else "new1",
             "integrand": {"family": "simple_pole", "residue": text(c), "pole": text(pole)},
             "interval": {"lo": text(a), "hi": text(b)},
             "carrier": "interval" if mode == "ordinary" else "punctured", "prescription": {"kind": mode}}
    if mode == "paired_limit":
        value["prescription"].update(left_scale=text(alpha), right_scale=text(beta))
    return value


POINTS = tuple(map(Q, (-2, -1, 0, "1/2", 1, 2)))
POLES = (*POINTS, Q(-3), Q(3))
RESIDUES = tuple(map(Q, (-2, "-1/2", "1/2", 2)))
CASES = [(a, pole, b, c) for a, b in itertools.combinations(POINTS, 2) for pole in POLES for c in RESIDUES]
INTERIOR = [row for row in CASES if row[0] < row[1] < row[2]]


def test_source_rows_routes_and_controls():
    report = p.exercise_report()
    rows = {row["id"]: row for row in report["exercises"]}
    assert len(report["exercises"]) == len(rows) == 9
    assert set(rows) == {f"P4.{i}" for i in range(1, 5)} | {f"DRILL4.{i}" for i in range(1, 6)}
    assert all(row["result"]["verdict"] == "MATCH" for row in rows.values())
    assert len(report["routes"]) == 2
    assert all(row["result"]["verdict"] == "MATCH" for row in report["routes"])
    assert {name for name, value in report["controls"].items() if value["verdict"] == "MISMATCH"} == {"forged_zero", "forged_stationarity"}
    assert report["counterexamples"]["asymmetric_pv"]["result"]["value"] == term(1, Q(3, 2))
    assert report["counterexamples"]["unequal_cutoffs"]["result"]["value"] == term(1, 2)
    assert report["counterexamples"]["excision_only"]["result"]["status"] == "ORDINARY_DIVERGENCE"
    assert report["counterexamples"]["unspecified_limit"]["result"]["status"] == "UNSPECIFIED_PRESCRIPTION"
    assert report["authority_effect"] == report["genesis_effect"] == "None"


def test_ordinary_finite_domain_oracle():
    counts = Counter()
    for a, pole, b, c in CASES:
        result = p.integral(task(a, pole, b, c))
        location = "outside" if pole < a or pole > b else "interior" if a < pole < b else "endpoint"
        counts[location] += 1
        assert result["defect_functional"] == "NOT_MEASURED" and result["authority_effect"] == "None"
        if location == "outside":
            assert result["status"] == "PROPER_INTEGRAL" and result["refusal"] is None
            assert result["value"] == term(c, abs(b - pole) / abs(a - pole))
            assert result["left_limit"] is result["right_limit"] is None
        else:
            assert result["status"] == "ORDINARY_DIVERGENCE" and result["refusal"] == "M"
            assert result["value"] is None and result["terminal"] == "REFUSED_SINGULAR_OBSERVED"
            assert result["left_limit"] == (None if pole == a else "-infinity" if c > 0 else "+infinity")
            assert result["right_limit"] == (None if pole == b else "+infinity" if c > 0 else "-infinity")
    assert len(CASES) == 480 and counts == {"outside": 280, "endpoint": 120, "interior": 80}


def test_pv_pairings_and_exact_cutoffs():
    pv_zeros = paired_count = cutoff_count = independent_count = 0
    scales = (Q(1, 2), Q(1), Q(2))
    for a, pole, b, c in INTERIOR:
        left, right = pole - a, b - pole
        pv = p.integral(task(a, pole, b, c, "symmetric_pv"))
        assert pv["status"] == "CAUCHY_PRINCIPAL_VALUE" and pv["value"] == term(c, right / left)
        pv_zeros += pv["value"]["coefficient"] == "0/1"
        for alpha, beta in itertools.product(scales, repeat=2):
            paired_count += 1
            current = task(a, pole, b, c, "paired_limit", alpha, beta)
            expected = term(c, alpha * right / (beta * left))
            result = p.integral(current)
            assert result["status"] == "PAIRED_CUTOFF_LIMIT" and result["value"] == expected
            for divisor in (2, 3, 5):
                epsilon = min(left / alpha, right / beta) / divisor
                dl, dr = alpha * epsilon, beta * epsilon
                cut = p.cutoff_integral(current, text(dl), text(dr))
                assert cut == {"status": "FINITE_TRUNCATION_ONLY", "left": term(c, dl / left),
                               "right": term(c, right / dr), "sum": expected, "matches_declared_pairing": True}
                cutoff_count += 1
        for u, v in itertools.product((Q(1, 4), Q(1, 2), Q(3, 4)), repeat=2):
            dl, dr = left * u, right * v
            cut = p.answer_for(task(a, pole, b, c), {"kind": "cutoffs", "left_cutoff": text(dl), "right_cutoff": text(dr)})
            assert cut["sum"] == term(c, u / v) and cut["matches_declared_pairing"] is None
            independent_count += 1
    assert (len(INTERIOR), pv_zeros, paired_count, cutoff_count, independent_count) == (80, 24, 720, 2160, 720)


def test_affine_sign_and_reflection():
    checked = 0
    for a, pole, b, c in CASES:
        original = p.integral(task(a, pole, b, c))
        for shift, scale in itertools.product((Q(-3, 2), Q(5, 3)), (Q(1, 2), Q(2))):
            transformed = p.integral(task(scale * a + shift, scale * pole + shift, scale * b + shift, c))
            assert transformed == original
            checked += 1
        negated = p.integral(task(a, pole, b, -c))
        if original["value"]:
            assert negated["value"] == term(-Q(original["value"]["coefficient"]), Q(original["value"]["log_argument"]))
        else:
            for field in ("left_limit", "right_limit"):
                assert negated[field] == {None: None, "+infinity": "-infinity", "-infinity": "+infinity"}[original[field]]
    assert checked == 1920
    for a, pole, b, c in INTERIOR:
        dl, dr = (pole - a) / 3, (b - pole) / 4
        original = p.cutoff_integral(task(a, pole, b, c), text(dl), text(dr))
        reflected = p.cutoff_integral(task(-b, -pole, -a, -c), text(dr), text(dl))
        assert reflected["left"] == original["right"] and reflected["right"] == original["left"]
        assert reflected["sum"] == original["sum"]
        for shift, scale in itertools.product((Q(-3, 2), Q(5, 3)), (Q(1, 2), Q(2))):
            assert p.cutoff_integral(task(scale*a+shift, scale*pole+shift, scale*b+shift, c), text(scale*dl), text(scale*dr)) == original


def test_cutoff_counterexamples_and_declared_format():
    ordinary = task(0, 1, 3)
    pv = task(0, 1, 3, mode="symmetric_pv")
    paired = task(0, 1, 3, mode="paired_limit", beta=2)
    assert p.integral(ordinary)["value"] is None
    assert p.integral(pv)["value"] == term(1, 2)
    assert p.integral(paired)["value"] == term(1, 1)
    assert p.answer_for(paired, {"kind": "claim_zero"})["zero_supported"] is True
    assert p.answer_for(pv, {"kind": "claim_zero"})["zero_supported"] is False
    for mode in ("ordinary", "unspecified"):
        value = task(mode=mode)
        value["carrier"] = "punctured"
        assert p.integral(value)["value"] is None
    assert p.cutoff_integral(pv, "1/4", "1/4")["matches_declared_pairing"] is True
    assert p.cutoff_integral(pv, "1/4", "1/2")["matches_declared_pairing"] is False
    assert p.cutoff_integral(paired, "1/4", "1/4")["matches_declared_pairing"] is False
    value = task(mode="unspecified")
    assert p.cutoff_integral(value, "1/2", "1/2")["matches_declared_pairing"] is None
    assert p.log_term(Q(0), Q(2)) == term(0, 2)
    with pytest.raises(p.InvalidInput):
        p.log_term(Q(1), Q(0))
    proper = task(0, -1, 3)
    expected = p.integral(proper)
    assert expected["value"] == term(1, 4)
    expected["value"] = term(2, 2)
    assert p.evaluate(p.submission(proper, {"kind": "integral"}, expected))["verdict"] == "MISMATCH"
    tiny = task(0, 1000000, Q(1, 1000000))
    assert p.answer_for(tiny, {"kind": "claim_zero"})["zero_supported"] is False
    assert len(p.integral(tiny)["value"]["log_argument"]) > 14


@pytest.mark.parametrize("mode,carrier,pole", itertools.product(("symmetric_pv", "paired_limit"), ("interval", "punctured"), (-1, 0, 5, 10, 11)))
def test_limit_geometry(mode, carrier, pole):
    value = task(pole=pole, mode=mode)
    value["carrier"] = carrier
    result = p.integral(value)
    valid = carrier == "punctured" and 0 < pole < 10
    assert (result["value"] is not None) is valid
    assert result["refusal"] == (None if valid else "ref<5>")


@pytest.mark.parametrize("dl,dr,pole", [("0/1", "1/1", 5), ("-1/1", "1/1", 5), ("5/1", "1/1", 5), ("1/1", "5/1", 5), ("1/1", "6/1", 5), ("1/1", "0/1", 5), ("1/1", "1/1", 0)])
def test_invalid_cutoffs(dl, dr, pole):
    with pytest.raises(p.InvalidInput):
        p.cutoff_integral(task(pole=pole), dl, dr)


def test_stationarity_all_declared_fields_and_missing():
    original = task()
    baseline = p.state(original, p.integral(original))
    variants = [baseline]
    for path, value in [(('task', 'task_id'), 'other'), (('task', 'carrier'), 'punctured'),
                        (('task', 'integrand', 'residue'), '-1/1'), (('task', 'integrand', 'pole'), '4/1'),
                        (('task', 'interval', 'lo'), '-1/1'), (('task', 'interval', 'hi'), '11/1'),
                        (('task', 'prescription', 'kind'), 'unspecified'), (('result', 'value'), {'new': True}),
                        (('result', 'refusal'), None), (('result', 'authority_effect'), 'GLOBAL')]:
        updated = deepcopy(baseline)
        location = updated
        for name in path[:-1]:
            location = location[name]
        location[path[-1]] = value
        variants.append(updated)
    for before, after in itertools.product(variants, repeat=2):
        event = p.event('M', before, after)
        got = p.stationary_refusal(original, event)
        assert got['state_equality'] == ('EQUAL' if before == after else 'DIFFERENT')
        bindings = before['task'] == after['task'] == original
        assert got['task_binding'] == ('CHECKED' if bindings else 'MISMATCH')
        assert got['stationary_refusal_verified'] is (before == after and bindings)
        assert got['semantic_replay'] == 'NOT_CHECKED'
    for before, after in ((None, baseline), (baseline, None), (None, None)):
        got = p.stationary_refusal(original, {'label':'M','task_sha256':p.digest(original),'before':before,'after':after})
        assert got == {'state_equality':'UNVERIFIED','task_binding':'UNVERIFIED','stationary_refusal_verified':False,'semantic_replay':'NOT_CHECKED'}
    event = p.event('M', baseline, baseline)
    event['task_sha256'] = '0'*64
    assert p.stationary_refusal(original, event)['task_binding'] == 'MISMATCH'
    fake = p.state(original, {'claimed_calculation': True})
    assert p.stationary_refusal(original, p.event('M', fake, fake))['stationary_refusal_verified'] is True
    with pytest.raises(p.InvalidInput):
        p.stationary_refusal(original, p.event('T', baseline, baseline))


def test_admission_and_fork_contract():
    old, new = task(), task(mode='symmetric_pv')
    original_bytes = p.encoded(old)
    assert p.fork_problem(old, new, None)['reason'] == 'NO_SUPPLIED_ADMISSION'
    admitted = p.admission_record(old, new)
    assert p.fork_problem(old, new, admitted)['accepted'] is True
    assert p.fork_problem(old, new, admitted)['admission_authenticity'] == 'NOT_CHECKED'
    for key in ('decision', 'scope', 'original_sha256', 'replacement_sha256'):
        bad = {**admitted, key:'wrong'}
        assert p.fork_problem(old, new, bad)['reason'] == 'ADMISSION_BINDING'
    for path, value in [(('task_id',),old['task_id']), (('integrand','residue'),'2/1'), (('interval','hi'),'11/1'),
                        (('carrier',),'interval'), (('prescription','kind'),'ordinary')]:
        bad = deepcopy(new)
        location = bad
        for name in path[:-1]:
            location = location[name]
        location[path[-1]] = value
        assert p.fork_problem(old,bad,p.admission_record(old,bad))['reason'] == 'NEW_PROBLEM_CONTRACT'
    wrong_old = task(mode='symmetric_pv')
    wrong_old['task_id'] = 'third'
    assert p.fork_problem(wrong_old,new,p.admission_record(wrong_old,new))['reason'] == 'NEW_PROBLEM_CONTRACT'
    endpoint_old, endpoint_new = task(pole=0), task(pole=0,mode='symmetric_pv')
    assert not p.fork_problem(endpoint_old,endpoint_new,p.admission_record(endpoint_old,endpoint_new))['accepted']
    changed = deepcopy(old)
    changed['task_id'] = 'renamed'
    assert p.fork_problem(changed,new,admitted)['reason'] == 'ADMISSION_BINDING'
    result = p.fork_problem(old,new,admitted)
    result['replacement']['task_id'] = 'not_shared'
    assert new['task_id'] == 'new1' and p.encoded(old) == original_bytes
    for bad in ({}, True, {**admitted,'extra':1}, {**admitted,'receipt_id':True}):
        with pytest.raises(p.InvalidInput):
            p.fork_problem(old,new,bad)


def test_routes_all_local_word_mutations():
    valid = {'CRMT','CDEIT'}
    neighbors = set()
    for word in valid:
        neighbors.update(word[:i]+word[i+1:] for i in range(len(word)))
        neighbors.update(word[:i]+letter+word[i+1:] for i in range(len(word)) for letter in 'CRMTDEI')
        neighbors.update(word[:i]+letter+word[i:] for i in range(len(word)+1) for letter in 'CRMTDEI')
        neighbors.update(word[:i]+word[i+1]+word[i]+word[i+2:] for i in range(len(word)-1))
    neighbors -= valid
    old = task()
    baseline = p.state(old)
    for word in neighbors:
        result = p.replay_trace(old,[p.event(letter,baseline,baseline) for letter in word],None,None)
        assert result['reason'] == 'ROUTE_SHAPE' and result['accepted'] is False
    assert len(neighbors) == 138


def test_trace_recomputation_binding_and_route_premises():
    old, new = task(), task(mode='symmetric_pv')
    receipt = p.admission_record(old,new)
    for replacement, admission in ((None,None),(new,receipt)):
        trace = p.expected_trace(old,replacement,admission)
        result = p.replay_trace(old,trace,replacement,admission)
        assert result['accepted'] is True
        final_task = old if replacement is None else new
        assert result['final_state'] == {'task':final_task,'result':p.integral(final_task)}
        for index in range(len(trace)):
            for side in ('before','after','task_sha256'):
                bad = deepcopy(trace)
                if side == 'task_sha256':
                    bad[index][side] = '0'*64
                else:
                    bad[index][side]['result'] = {'wrong':0}
                got = p.replay_trace(old,bad,replacement,admission)
                assert got['reason'] == 'EVENT_REPLAY' and got['bad_events'] == [index]
            bad = deepcopy(trace)
            bad[index]['before'] = None
            assert not p.replay_trace(old,bad,replacement,admission)['accepted']
        renamed_old, renamed_new = deepcopy(old), deepcopy(new)
        renamed_old['task_id'], renamed_new['task_id'] = 'renamed_old','renamed_new'
        assert p.replay_trace(renamed_old,trace,replacement,admission)['accepted'] is False
        other_new = None if replacement is None else renamed_new
        other_admission = None if replacement is None else p.admission_record(renamed_old,renamed_new)
        assert p.replay_trace(renamed_old,p.expected_trace(renamed_old,other_new,other_admission),other_new,other_admission)['accepted'] is True
        result['final_state']['task']['task_id'] = 'returned_mutation'
        assert trace[-1]['after']['task']['task_id'] == final_task['task_id']
    trace = p.expected_trace(old,new,receipt)
    for replacement, admission in ((None,None),(None,receipt),(new,None),(new,receipt)):
        result = p.replay_trace(old,trace,replacement,admission)
        assert result['accepted'] is (replacement is not None and admission is not None)
    assert p.replay_trace(old,p.expected_trace(old),new,receipt)['reason'] == 'ROUTE_DECLARATION'
    assert p.replay_trace(old,p.expected_trace(old),None,receipt)['reason'] == 'ROUTE_PRECONDITION'
    forged = deepcopy(trace)
    forged[1]['after']['result'] = p.integral(old)
    assert p.replay_trace(old,forged,new,receipt)['reason'] == 'EVENT_REPLAY'
    proper = task(pole=-1)
    assert p.replay_trace(proper,p.expected_trace(old),None,None)['reason'] == 'ROUTE_PRECONDITION'
    with pytest.raises(p.InvalidInput):
        p.expected_trace(old,new,None)
    for events in ([], {}, [trace[0]]*9):
        with pytest.raises(p.InvalidInput):
            p.replay_trace(old,events,new,receipt)


@pytest.mark.parametrize('value', [True,1,1.0,None,'1','1/0','01/1','1/-1','2/2','-0/1','+1/1','1/01','1000001/1','1/1000001','1/10000000'])
def test_bad_rationals(value):
    with pytest.raises(p.InvalidInput):
        p.rational(value)


@pytest.mark.parametrize('mutate', [
    lambda t:t.update(extra=1), lambda t:t.pop('integrand'), lambda t:t.update(task_id=True),
    lambda t:t.update(task_id='Bad'), lambda t:t['integrand'].update(family='anything'),
    lambda t:t['integrand'].update(residue='0/1'), lambda t:t['interval'].update(hi='0/1'),
    lambda t:t['interval'].update(hi='-1/1'), lambda t:t.update(carrier='invented'),
    lambda t:t.update(prescription=True), lambda t:t.update(prescription={'kind':True}),
    lambda t:t.update(prescription={'kind':'unknown'}), lambda t:t['prescription'].update(extra=True),
    lambda t:t.update(prescription={'kind':'paired_limit','left_scale':'0/1','right_scale':'1/1'}),
    lambda t:t.update(prescription={'kind':'paired_limit','left_scale':'1/1','right_scale':'-1/1'})])
def test_invalid_task_contracts(mutate):
    value = task()
    mutate(value)
    with pytest.raises(p.InvalidInput):
        p.integral(value)


def test_invalid_event_and_query_shapes():
    original = task()
    baseline = p.state(original)
    event = p.event('M',baseline,baseline)
    for change in ({'label':'Z'},{'task_sha256':True},{'task_sha256':'BAD'},{'before':{}},{'after':{'task':original,'result':[]}}):
        with pytest.raises(p.InvalidInput):
            p.stationary_refusal(original,{**event,**change})
    for query in ({},{'kind':True},{'kind':'unknown'},{'kind':'authority','extra':True},True):
        with pytest.raises(p.InvalidInput):
            p.answer_for(original,query)
    assert p.answer_for(original,{'kind':'authority'}) == {'refusal':'ref<2>','reason':'NO_GLOBAL_AUTHORITY'}


def test_proposal_binding_types_and_no_aliases():
    old, new = task(), task(mode='symmetric_pv')
    query = {'kind':'claim_zero'}
    answer = {'zero_supported':True,'refusal':None,'prescription':'symmetric_pv'}
    document = p.submission(new,query,answer)
    assert p.evaluate(document)['verdict'] == 'MATCH'
    snapshot = deepcopy(document)
    result = p.evaluate(document)
    document['task']['task_id'] = 'changed'
    assert result['original'] == snapshot
    result['original']['proposal']['answer']['zero_supported'] = False
    assert result['computed_answer']['zero_supported'] is True
    for surface in ('task','query','hash'):
        wrong = deepcopy(snapshot)
        if surface == 'task':
            wrong['task']['task_id'] = 'other'
        elif surface == 'query':
            wrong['query']['kind'] = 'integral'
        else:
            wrong['proposal']['problem_sha256'] = '0'*64
        with pytest.raises(p.InvalidInput):
            p.evaluate(wrong)
    wrong = deepcopy(snapshot)
    wrong['proposal']['answer']['zero_supported'] = 1
    assert p.evaluate(wrong)['verdict'] == 'MISMATCH'
    wrong = deepcopy(snapshot)
    wrong['proposal']['answer'] = True
    with pytest.raises(p.InvalidInput):
        p.evaluate(wrong)
    new = task(mode='symmetric_pv')
    admitted = p.admission_record(old,new)
    query = {'kind':'change','replacement':new,'admission':admitted}
    result = p.evaluate(p.submission(old,query,p.fork_problem(old,new,admitted)))
    result['original']['query']['replacement']['task_id'] = 'no_alias'
    assert result['computed_answer']['replacement']['task_id'] == 'new1'


@pytest.mark.parametrize('value', [1.0, float('nan'), 10**12+1,'x'*513,[0]*65,{str(i):0 for i in range(65)},{1:0},(1,), '\ud800'])
def test_json_value_guards(value):
    with pytest.raises(p.InvalidInput):
        p.json_value(value)


def test_json_depth_byte_limit_and_valid_values():
    p.json_value([None, True, False, -10**12, 'emoji \U0001f600', {'x':0}])
    value = 0
    for _ in range(14):
        value = [value]
    with pytest.raises(p.InvalidInput):
        p.json_value(value)
    document = p.submission(task(),{'kind':'integral'}, {str(i):['x'*500]*32 for i in range(5)})
    with pytest.raises(p.InvalidInput,match='byte limit'):
        p.evaluate(document)
    assert p.rational('1000000/1') == 1000000 and p.rational('1/1000000') == Q(1,1000000)


BAD_RAW = [b'',b'{}x',b'\xff',b'{"x":1,"x":2}',b'{"a":NaN}',b'{"a":Infinity}',b' '*65537]


@pytest.mark.parametrize('raw',BAD_RAW,ids=['empty','trailing','utf8','duplicate','nan','inf','oversize'])
def test_bad_raw_no_run(raw,tmp_path,capsys):
    source = tmp_path/'input'
    source.write_bytes(raw)
    with pytest.raises((ValueError,UnicodeError)):
        p.decode(raw)
    assert p.main(['--input',str(source),'--output-dir',str(tmp_path/'runs')]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'REFUSED'
    assert not (tmp_path/'runs').exists()


def test_decode_requires_bytes():
    for value in (None,'{}',bytearray(b'{}')):
        with pytest.raises(p.InvalidInput):
            p.decode(value)


def test_raw_receipt_hashes_and_no_overwrite(tmp_path,monkeypatch):
    monkeypatch.setattr(p,'uuid4',lambda:SimpleNamespace(hex='fixed'))
    raw = b' \n {"original":1}\t'
    folder = p.write_run(tmp_path,{'ok':True},raw,'MATCH')
    assert (folder/'input.bin').read_bytes() == raw
    receipt = json.loads((folder/'receipt.json').read_bytes())
    assert set(receipt['artifact_sha256']) == {'input.bin','result.json','summary.md'}
    assert receipt['code_sha256'] == hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    assert receipt['model_calls'] == 0 and receipt['cost_usd'] == '0'
    for name,expected in receipt['artifact_sha256'].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == expected
    with pytest.raises(FileExistsError):
        p.write_run(tmp_path,{'changed':True},b'changed','MATCH')
    assert (folder/'input.bin').read_bytes() == raw


@pytest.mark.parametrize('kind', ['default','proper','pv','paired_zero','missing_state','changed_state','no_admission','wrong','invalid','malformed'])
def test_actual_cli(kind,tmp_path):
    command = [sys.executable,str(RUNNER),'--output-dir',str(tmp_path/'runs')]
    raw = None
    if kind != 'default':
        current = task()
        query = {'kind':'integral'}
        if kind in ('proper','pv','paired_zero'):
            current = task(0,-1,3) if kind == 'proper' else task(0,1,3,mode='symmetric_pv' if kind == 'pv' else 'paired_limit',beta=2)
            answer = p.integral(current)
            assert answer['value'] == term(1,4 if kind == 'proper' else 2 if kind == 'pv' else 1)
        elif kind in ('missing_state','changed_state'):
            baseline = p.state(current)
            change = p.state(current, {'new':True})
            event = p.event('M',baseline,change)
            if kind == 'missing_state':
                event['after'] = None
            query = {'kind':'stationarity','event':event}
            answer = p.stationary_refusal(current,event)
            assert answer['stationary_refusal_verified'] is False
        elif kind == 'no_admission':
            replacement = task(mode='symmetric_pv')
            query = {'kind':'change','replacement':replacement,'admission':None}
            answer = p.fork_problem(current,replacement,None)
            assert answer['accepted'] is False
        else:
            answer = {}
        document = {} if kind == 'invalid' else p.submission(current,query,answer)
        raw = b' \n'+p.encoded(document)+b'\t' if kind != 'malformed' else b'bad json'
        source = tmp_path/'input.json'
        source.write_bytes(raw)
        command += ['--input',str(source)]
    result = subprocess.run(command,text=True,capture_output=True,timeout=20,check=False)
    assert result.returncode == (2 if kind == 'malformed' else 1 if kind in ('wrong','invalid') else 0), result.stderr
    message = json.loads(result.stdout)
    if kind == 'malformed':
        assert message['status'] == 'REFUSED' and not (tmp_path/'runs').exists()
        return
    folder = Path(message['output'])
    assert message['status'] == ('DEMONSTRATED' if kind == 'default' else 'REJECTED' if kind == 'invalid' else 'MISMATCH' if kind == 'wrong' else 'MATCH')
    if raw is not None:
        assert (folder/'input.bin').read_bytes() == raw
    else:
        assert json.loads((folder/'result.json').read_bytes()) == p.exercise_report()
    receipt = json.loads((folder/'receipt.json').read_bytes())
    for name,expected in receipt['artifact_sha256'].items():
        assert hashlib.sha256((folder/name).read_bytes()).hexdigest() == expected


def test_main_branches(tmp_path,capsys,monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert p.main([]) == 0
    assert json.loads(capsys.readouterr().out)['status'] == 'DEMONSTRATED'
    source = tmp_path/'input'
    for answer,expected in (({'refusal':'ref<2>','reason':'NO_GLOBAL_AUTHORITY'},'MATCH'),({},'MISMATCH')):
        source.write_bytes(p.encoded(p.submission(task(),{'kind':'authority'},answer)))
        assert p.main(['--input',str(source)]) == (0 if expected == 'MATCH' else 1)
        assert json.loads(capsys.readouterr().out)['status'] == expected
    source.write_bytes(b'{}')
    assert p.main(['--input',str(source)]) == 1
    assert json.loads(capsys.readouterr().out)['status'] == 'REJECTED'
    assert p.main(['--input',str(tmp_path/'missing')]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'REFUSED'
    assert p.main(['--output-dir',str(source)]) == 2
    assert json.loads(capsys.readouterr().out)['status'] == 'REFUSED'


MUTATIONS = (
    ('ordinary_is_pv','if kind != "ordinary":','if kind != "ordinary" or inside:', 'test_ordinary_finite'),
    ('endpoint_is_outside','if location == "outside":','if location != "interior":','test_ordinary_finite'),
    ('reverse_pv_ratio','ratio = (hi - pole) / (pole - lo)','ratio = (pole - lo) / (hi - pole)','test_pv_pairings'),
    ('swap_pairing_scales','ratio *= rational(task["prescription"]["left_scale"]) / rational(task["prescription"]["right_scale"])','ratio *= rational(task["prescription"]["right_scale"]) / rational(task["prescription"]["left_scale"])','test_pv_pairings'),
    ('omit_cutoff_factor','left * (hi - pole) / (right * (pole - lo))','(hi - pole) / (pole - lo)','test_pv_pairings'),
    ('lose_residue_sign','positive = "+infinity" if coefficient > 0 else "-infinity"','positive = "+infinity"','test_ordinary_finite'),
    ('approximate_zero','if coefficient == 0 or argument == 1:','if coefficient == 0 or abs(float(argument)-1) < 1e-8:','test_cutoff_counterexamples'),
    ('zero_residue_allowed','require(coefficient != 0,','require(True,','test_invalid_task_contracts'),
    ('carrier_only_equality','equal = encoded(before) == encoded(after) if present else None','equal = before["task"]["carrier"] == after["task"]["carrier"] if present else None','test_stationarity_all'),
    ('missing_states_equal','"UNVERIFIED" if not present else "EQUAL" if equal else "DIFFERENT"','"EQUAL" if not present else "EQUAL" if equal else "DIFFERENT"','test_stationarity_all'),
    ('unbound_m_event','value["task_sha256"] == digest(task) and all','True and all','test_stationarity_all'),
    ('no_admission_needed','if admission is None:\n        return {**refused, "reason": "NO_SUPPLIED_ADMISSION"}','if admission is None:\n        admission = admission_record(task, replacement)','test_admission_and'),
    ('unbound_admission','admission["original_sha256"] == digest(task)','True','test_admission_and'),
    ('unbound_replacement','admission["replacement_sha256"] == digest(replacement)','True','test_admission_and'),
    ('same_id_allowed','changed_id = task["task_id"] != replacement["task_id"]','changed_id = True','test_admission_and'),
    ('changed_bounds_allowed','same_bounds = encoded(task["interval"]) == encoded(replacement["interval"])','same_bounds = True','test_admission_and'),
    ('trace_labels_only','if encoded(actual) != encoded(wanted)','if False','test_trace_recomputation'),
    ('illegal_after_m','["C", "R", "M", "T"], ["C", "D", "E", "I", "T"]','["C", "R", "M", "T"], ["C", "R", "M", "E"], ["C", "D", "E", "I", "T"]','test_routes_all'),
    ('global_promotion','return {"refusal": "ref<2>", "reason": "NO_GLOBAL_AUTHORITY"}','return {"refusal": None, "reason": "GLOBAL_AUTHORITY"}','test_invalid_event'),
    ('unbound_query','snapshot["proposal"]["problem_sha256"] == problem','True','test_proposal_binding'),
    ('no_input_snapshot','snapshot = clone(document)','snapshot = document','test_proposal_binding'),
    ('boolean_number_equal','encoded(snapshot["proposal"]["answer"]) == encoded(computed)','snapshot["proposal"]["answer"] == computed','test_proposal_binding'),
    ('raw_bytes_stripped','"input.bin": raw_input','"input.bin": raw_input.strip()','test_raw_receipt'),
    ('overwrite_allowed','exist_ok=False','exist_ok=True','test_raw_receipt'),
    ('duplicate_keys_allowed','require(key not in result, "Duplicate JSON key")','require(True, "Duplicate JSON key")','test_bad_raw'),
    ('utf8_guard_removed','value.encode("utf-8")','None','test_json_value_guards'),
)


def test_implementation_mutations(tmp_path):
    original = RUNNER.read_bytes()
    source = RUNNER.read_text(encoding='utf-8')
    rows = []
    for name,anchor,replacement,selected in MUTATIONS:
        assert source.count(anchor) == 1, (name,source.count(anchor))
        mutant_text = source.replace(anchor,replacement)
        compile(mutant_text,name,'exec')
        mutant = tmp_path/(name+'.py')
        mutant.write_text(mutant_text,encoding='utf-8')
        environment = dict(os.environ,PFP_PILOT_000013_UNDER_TEST=str(mutant),PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
                           PYTHONDONTWRITEBYTECODE='1',NO_COLOR='1')
        for variable in ('PFP_PILOT_000013_MUTATION_OUTPUT','FORCE_COLOR','PY_COLORS'):
            environment.pop(variable,None)
        result = subprocess.run([sys.executable,'-m','pytest',str(Path(__file__)),'-q','--color=no','-p','no:cacheprovider','-o','addopts=',
                                 '--import-mode=importlib','--basetemp',str(tmp_path/(name+'_temp')),'-k',selected],
                                env=environment,text=True,capture_output=True,timeout=40,check=False)
        failures = [line for line in result.stdout.splitlines() if line.startswith('FAILED ')]
        assert result.returncode == 1 and failures, (name,result.returncode,result.stdout,result.stderr)
        assert RUNNER.read_bytes() == original
        rows.append({'name':name,'anchor':anchor,'replacement':replacement,'target':str(RUNNER.resolve()),
                     'applied':True,'exit_code':result.returncode,'failed_nodes':failures,'original_unchanged':True,
                     'original_sha256':hashlib.sha256(original).hexdigest(),'mutant_sha256':hashlib.sha256(mutant.read_bytes()).hexdigest()})
    if output := os.environ.get('PFP_PILOT_000013_MUTATION_OUTPUT'):
        with Path(output).open('x',encoding='utf-8') as stream:
            json.dump(rows,stream,indent=2)


def test_module_entry_point_in_process(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", [str(RUNNER), "--output-dir", str(tmp_path / "entry")])
    with pytest.raises(SystemExit) as raised:
        runpy.run_path(str(RUNNER), run_name="__main__")
    assert raised.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "DEMONSTRATED"


def test_default_output_root_is_beside_the_pilot():
    assert p.OUTPUT_ROOT == RUNNER.resolve().parent.parent / "pilot_output" / p.PILOT_ID


def test_demonstration_fails_when_a_row_mismatches(tmp_path, monkeypatch, capsys):
    computed = p.answer_for

    def drifted(task, query):
        answer = computed(task, query)
        return {**answer, "zero_supported": True} if query["kind"] == "claim_zero" else answer

    monkeypatch.setattr(p, "answer_for", drifted)
    report = p.exercise_report()
    assert [row["id"] for row in report["exercises"] if row["result"]["verdict"] == "MISMATCH"] == ["DRILL4.2"]
    assert p.demonstration_status(report) == "MISMATCH"
    assert p.main(["--output-dir", str(tmp_path / "mismatch")]) == 1
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "MISMATCH"
    assert json.loads((Path(output["output"]) / "receipt.json").read_bytes())["status"] == "MISMATCH"


def test_demonstration_fails_when_a_route_mismatches():
    report = p.exercise_report()
    assert p.demonstration_status(report) == "DEMONSTRATED"
    report["routes"][1]["result"]["verdict"] = "MISMATCH"
    assert p.demonstration_status(report) == "MISMATCH"
