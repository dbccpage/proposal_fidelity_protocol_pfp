"""Small positive/negative controls for the audit's arithmetic and digest primitives."""
import copy
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pfp.infrastructure.tower_research.reach import canonical, transport


def module(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


audit = module('structured_audit_controls_target', 'dag/reviews/additional_structured_evidence_audit.py')
checker = module('structured_score_controls_target', 'governance/tools/checker.py')
outcomes = []


def check(name, condition):
    outcomes.append({'control': name, 'passed': bool(condition)})


def refuses(fn):
    try:
        fn()
    except Exception:
        return True
    return False


dup = []
audit.strict_json('{"a":1,"a":2}', dup)
check('duplicate JSON key reported before last-value collapse', dup == ['a'])
check('nonfinite JSON refused', refuses(lambda: audit.strict_json('{"a":NaN}', [])))
loader = audit.DuplicateLoader('a: 1\na: 2\n')
loader.get_data()
check('explicit duplicate YAML key reported', len(loader.duplicates) == 1)
loader.dispose()
loader = audit.DuplicateLoader('base: &b {a: 1}\nderived: {<<: *b, a: 2}\n')
loader.get_data()
check('intentional YAML merge override is not reported as repeated explicit key', not loader.duplicates)
loader.dispose()

score_path = 'code/rust/pfp_cli/src/catalog.contract.score.json'
companion = checker.Companion.model_validate_json((ROOT / score_path).read_bytes())
check('unmodified score arithmetic passes owning function', not checker.score_problems(companion.score, 'L4', 'D'))
changed = companion.score.model_copy(update={'score_token': 'L5A+'})
check('corrupted score token is rejected by owning function', bool(checker.score_problems(changed, 'L4', 'D')))
changed = companion.score.mutation_accounting.model_copy(update={'conservative_ratio': 0.5})
check('corrupted mutation ratio is rejected by owning function', bool(checker.mutation_problems(changed)))

obj = {'count': 2, 'rational': '1/2'}
check('audit canonical serializer matches owning canonical serializer', audit.canon(obj) == canonical.canonical_bytes(obj))
check('canonical positive round-trip', canonical.parse_canonical(audit.canon(obj)) == obj)
check('canonical duplicate control rejected by owning parser', refuses(lambda: canonical.strict_loads(b'{"count":1,"count":2}')))
check('canonical float control rejected by owning parser', refuses(lambda: canonical.strict_loads(b'{"count":1.0}')))

cert_path = 'pfp/infrastructure/tower_evidence/level_engine/v1/bindings/generated/certificates/L000.cert.json'
cert = json.loads((ROOT / cert_path).read_bytes())
check('v1 payload positive control agrees with actual receiving digest function', transport.payload_digest(cert) == cert['envelope']['payload_digest'])
changed = copy.deepcopy(cert)
changed['cost']['value'] = '999/1'
check('payload mutation invalidates actual receiving digest function', transport.payload_digest(changed) != cert['envelope']['payload_digest'])

receipt_path = 'workflows/wf20_derivation_loop_with_lift_grants/pilots/evidence/po035_derivations_20261012/pilot_0000199/loop_01/raw_reply.json'
reply = json.loads((ROOT / receipt_path).read_bytes())
usage = reply['usage']
check('provider usage positive sum control', usage['prompt_tokens'] + usage['completion_tokens'] == usage['total_tokens'])
changed = dict(usage, total_tokens=usage['total_tokens'] + 1)
check('one-token mutation breaks recorded usage equation', changed['prompt_tokens'] + changed['completion_tokens'] != changed['total_tokens'])

result = {'scope':'Read-only synthetic corruptions of loaded values; no historical bytes changed.',
          'passed':sum(row['passed'] for row in outcomes), 'total':len(outcomes), 'controls':outcomes}
(ROOT / 'dag/reviews/additional_structured_evidence_controls.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps({'passed':result['passed'],'total':result['total']}))
if not all(row['passed'] for row in outcomes):
    raise SystemExit(1)
