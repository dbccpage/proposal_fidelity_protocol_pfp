"""Bounded public Paper010 tests/probes; no providers or original source edits."""
import code  # Preserve stdlib code for pytest/pdb despite the deposit's package name.
import pdb
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots'
OUT = ROOT/'dag/reviews/paper_010_support_inspection'
OUT.mkdir(exist_ok=True)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def tests():
    import pytest
    return pytest.main(['-q', '-p', 'no:cacheprovider', '--import-mode=importlib',
                        '--basetemp', str(OUT/'pytest_temp'), str(BASE/'code/tests')])


def probes():
    sys.path.insert(0, str(BASE/'code'))
    h = module('holonomy', BASE/'code/holonomy.py')
    findings = []
    def observe(rule, fn):
        try: findings.append({'rule':rule, 'status':'returned', 'value':fn()})
        except Exception as exc: findings.append({'rule':rule, 'status':'raised', 'exception':type(exc).__name__, 'detail':str(exc)[:300]})
    group = h.symmetric_group_s3(); lattice = h.Lattice(2,2,False)
    connection = h.trivial_connection(group,lattice)
    observe('nonobject_case_boundary', lambda:h.connection_from_case(None))
    observe('oversized_digit_certificate_boundary', lambda:h.verify_claim(connection, {'verdict':h.NOT_FLAT,'plaquette':['9'*5000+',0','0,1','1,1','1,0'],'holonomy':group.identity}))
    links = {tuple(tuple(float(v) for v in vertex) for vertex in edge):value for edge,value in connection.links().items()}
    observe('direct_api_float_coordinate_alias', lambda:h.check_flatness(h.Connection(group,lattice,links)).verdict)
    recount = module('recount_pilots', BASE/'code/recount_pilots.py')
    for name in ('verify_source_bytes','verify_c017_extraction','table3','table4'):
        observe(name, getattr(recount,name))
    v = module('verify_deposit_010',BASE/'verify_deposit.py')
    observe('current_manifest',lambda:v.check_manifest(BASE/'SHA256SUMS'))
    render = module('render_010',BASE/'tools/render_paper.py')
    fake = OUT/'render_author_control'; fake.mkdir(exist_ok=True)
    (fake/'paper.md').write_text('# Public control\n\nJeremy Carroll\n\n2026-10-02\n\n</div>\n\nNo science solution.\n',encoding='utf-8')
    render.ROOT = fake
    observe('retained_render_test_author_boundary',lambda:render.render('UNUSED_PANDOC','UNUSED_XELATEX'))
    result = {'scope':'Direct source public inputs and historical custody only; no provider/private/Lean execution', 'checks':findings,
              'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (BASE/'code/holonomy.py',BASE/'code/recount_pilots.py',BASE/'verify_deposit.py',BASE/'tools/render_paper.py')}}
    (ROOT/'dag/reviews/additional_paper_010_probe_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(findings,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(tests() if '--tests' in sys.argv else probes())
