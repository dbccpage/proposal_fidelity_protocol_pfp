"""Review the six relocated operad demo sources, retaining original-byte custody."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT/'dag/reviews'
migration = json.loads((ROOT/'dag/migrations/demo_support_verification.json').read_text())
locations = [r for r in migration['locations'] if r['source_repo']=='pfp' and '/008_oeop/code/' in r['original_path']]
assert len(locations) == 6
notes = {
 'README.md': 'Full original archive member and full current README read. The sole substantive adaptation is the test command location. Module list is a useful teaching index, but verification/simulation labels need limits from the actual miniature implementations; this is not a deployed runtime.',
 '__init__.py': 'Full export module read; all twelve teaching classes are re-exported from the local module. No new checker or runtime integration is supplied.',
 'tests/__init__.py': 'Full test-package docstring read. No executable or mathematical behavior.',
 'tests/conftest.py': 'Full test-path configuration read. It finds ancestor markers/fallbacks and adds the local code directory to sys.path. It supplies import plumbing, not model or mathematical validation.',
 'tests/test_was_operad_levels.py': 'Full ten-test source read. Positive/negative colour and package checks, capability membership, literal trigger, rate limit, scalar halving, string pipeline, dictionary parity and digest length are bounded examples. The associativity-named test only inspects tree shape and height; no unit or associativity equation is compared. No test suite rerun is credited here; migration checks remain separate historical evidence.',
 'was_operad_core.py': 'Full miniature module read. It implements signature splicing, size checks, unrestricted tree syntax, capability membership messages, case-insensitive substring detection, a caller-time sliding count, scalar multiplication, three callback chaining, four dictionaries and mutable hashed dictionaries. These are teaching mechanisms, not actual task execution, detector admission, certified contraction, atomic filesystem synchronization or authenticated review. Fresh countercontrols scope the law/guard gaps without changing source.'
}
rows = []
for location in locations:
    current = (ROOT/location['current_path']).read_bytes()
    assert hashlib.sha256(current).hexdigest() == location['current_sha256']
    if location['post_move_adaptation']:
        with zipfile.ZipFile(location['original_archive']) as archive:
            original = archive.read(location['archive_member'])
    else:
        original = current
    assert hashlib.sha256(original).hexdigest() == location['original_sha256']
    relative = location['original_path'].split('/code/',1)[1]
    rows.append({'path':location['original_path'],'sha256':location['original_sha256'],
                 'full_source_read':True,'reviewed_lines':[[1,len(original.decode('utf-8').splitlines())]],
                 'assessment':notes[relative], 'current_source':location,
                 'reading_basis':'Complete current body plus complete original README archive member; other five bodies are exactly unchanged.'})

owner = next(r for r in locations if r['current_path'].endswith('/was_operad_core.py'))
spec = importlib.util.spec_from_file_location('_reviewed_operad_teaching', ROOT/owner['current_path'])
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
C = module.Colour
op = module.ColouredOperad()
f,g,h = [module.OperadOp(i,name,(C.CODE,),C.CODE) for i,name in enumerate(('f','g','h'),1)]
left = op.partial_compose(op.partial_compose(f,g,0),h,0)
right = op.partial_compose(f,op.partial_compose(g,h,0),0)
assert left.inputs == right.inputs and left.output == right.output and left != right
unit = op.partial_compose(f,op.identity(C.CODE),0)
assert unit.inputs == f.inputs and unit.output == f.output and unit != f
try:
    op.partial_compose(f,module.OperadOp(9,'bad',(C.DELIBERATION,),C.DELIBERATION),0)
except TypeError:
    mismatch_refused = True
else:
    raise AssertionError('positive type-guard control failed')
malformed = module.PlanarTree(op=f, subtrees=(module.PlanarTree(colour=C.DELIBERATION),))
assert malformed.root_output() == C.CODE and malformed.leaf_colours() == [C.DELIBERATION]
ddc = module.DDCContractivityEngine(0.5)
assert ddc.verify_contractivity([0.0,100.0])
assert ddc.verify_contractivity([1.0,0.9])
assert not ddc.verify_contractivity([1.0,2.0])
assert ddc.verify_contractivity([1.0,0.5,0.25])
emitter = module.DeliberationReceiptEmitter()
receipt = emitter.emit_receipt(1,'','','',True)
old_digest = receipt['digest']
receipt['authority_effect'] = 'EXECUTE'
assert emitter.receipts[0]['authority_effect'] == 'EXECUTE' and receipt['digest'] == old_digest
controls = [
 {'id':'signature_vs_record_laws','left_name':left.name,'right_name':right.name,
  'same_profile':True,'associative_record_equality':False,'unit_record_equality':False,
  'mismatched_colour_refused':mismatch_refused,
  'limit':'No evaluation semantics or declared equality quotient is supplied; profile-splicing agreement is a narrower property than operation equality.'},
 {'id':'malformed_tree','declared_input':'CODE','child_output':'DELIBERATION','constructed':True,
  'limit':'This unrestricted toy tree has no well-formedness verifier. It is not a production tree bypass.'},
 {'id':'contraction_guard','zero_to_100_accepted':True,'factor_half_but_one_to_point9_accepted':True,
  'one_to_two_refused':True,'halving_sequence_accepted':True,
  'limit':'Thresholded adjacent comparison is not a nonnegative finite-norm or specified Lipschitz-factor certificate.'},
 {'id':'mutable_receipt_alias','empty_role_strings_accepted':True,'stored_effect_after_returned_dict_mutation':'EXECUTE',
  'digest_unchanged':True,'limit':'Local dictionary emitter only; a separate hash verifier could detect alteration but none is applied here.'}
]


def ev():
    return {'path':owner['current_path'],'sha256':owner['current_sha256']}


report = {'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120',
 'status':'complete_six_migrated_original_source_reviews','file_reviews':rows,
 'claims':[{'id':'MOT-C01','statement':'The relocated module offers reusable small demonstrations of ordered profile splicing, substring filtering, scalar halving and callback sequencing, with an actual incompatible-colour rejection. Its scope is teaching; it supplies no paid-model performance evidence.','evidence':[ev()]}],
 'findings':[
  {'id':'MOT-F01','severity':'medium','statement':'The teaching partial_compose preserves profiles in the tested unary associativity/unit cases, but resulting OperadOp records differ through name/id construction. Its unrestricted tree also accepts a child with the wrong colour. The associativity-named retained test checks only tree shape. No equality quotient, evaluator or well-formedness proof closes that gap.','evidence':[ev()],'recommended_action':'State profile-only semantics, or add a typed tree representation/equality and test genuine operad laws before reusing it as a workflow validator.'},
  {'id':'MOT-F02','severity':'medium','statement':'The teaching contraction verifier accepts a jump from0 to100 and accepts1 to0.9 when its declared contraction factor is0.5. It compares adjacent values above a threshold and does not check its advertised Lipschitz bound or finite nonnegative norm inputs.','evidence':[ev()],'recommended_action':'Admit the norm domain and verify the stated factor-bound for each transition, with explicit zero/nonfinite cases.'},
  {'id':'MOT-F03','severity':'medium','statement':'The teaching receipt emitter accepts empty role names and returns the same mutable dictionary stored in its history. Changing the returned authority_effect also changes stored history while retaining the old digest. The field and hash alone do not enforce immutable non-authoritative custody.','evidence':[ev()],'recommended_action':'Keep this a simulated receipt or use immutable records with verified bindings and independent custody. Do not count a stored digest as authenticated inspection.'}
 ], 'controls':controls,
 'workflow_disposition':'Retain as a scoped teaching reference; do not count its ten level labels as ten qualified workflows. Candidate adaptations need real semantic checkers and the identified guards.',
 'limits':['All six original bodies fully read; current README also read and its original recovered from the named archive member.',
           'Only the reviewed standard-library module and four public synthetic controls ran; no pytest/native/provider/private benchmark access.',
           'Migration and original source bytes unchanged; prior migration tests are not counted as new execution.']}
(REV/'additional_migrated_operad_teaching.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'original_full_reads':len(rows),'controls':len(controls),'claims':1,'findings':3,
                  'report_sha256':hashlib.sha256((REV/'additional_migrated_operad_teaching.json').read_bytes()).hexdigest()}))
