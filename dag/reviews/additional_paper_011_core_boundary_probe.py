"""Pure synthetic boundaries only; no sealed sources, binaries or retained receipts."""
import sys,os,ast,json,hashlib,copy,datetime,importlib.util,itertools,contextlib,io
from pathlib import Path
from fractions import Fraction
sys.dont_write_bytecode=True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
import additional_paper_011_core_audit as a
code=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code'
temp=a.file('_boundary_temp_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));temp.mkdir()
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
m=load('paper011_pure_mechanisms',code/'mechanism_recreations.py')
g04=load('paper011_pure_g04',code/'genesis_g04_replay.py')
raw=b'import sys\nvalue = 0\nif True:\n    bootstrap = sys.path\n    value = 7\n'
tree,receipt=g04.relocate(raw,'synthetic.py');old={};new={};exec(compile(raw,'synthetic.py','exec'),old);exec(compile(tree,'synthetic.py','exec'),new)
assert old['value']==7 and new['value']==0
g03=ast.parse((code/'genesis_g03_replay.py').read_bytes());selected=[n for n in g03.body if isinstance(n,ast.FunctionDef) and n.name in {'check_calls','controls'}]
paper=temp/'g03';area=paper/'area';area.mkdir(parents=True);(paper/'code').mkdir();(paper/'code/genesis_g03_adapter.py').write_text('synthetic source',encoding='utf8')
case={'id':'synthetic:base','n':3,'i':1,'j':2,'reading':'L','measure':'mu1','variant':'base','target':[2,3],'state':{'insts':[]}}
call={k:case[k] for k in ('id','n','i','j','reading','measure','variant','target')};call.update({'predicate_domain':'canonical_classes','raw_count':2,'classes':[{'key':[0],'size':2,'members':[['a'],['b']],'representative':['a'],'fresh_mark':False}],'weak':False,'strong':False})
response={'calls':[call]}
reasons={'fixed_target_reuse':'FIXED_TARGET_REUSE','poisoned_collapse_adapter':'CANDIDATE_CARRIER_OR_COLLAPSE_ADAPTER_MISMATCH','predicates_not_on_classes':'PREDICATES_NOT_ON_CLASSES','duplicated_pair':'DUPLICATE_PAIR_CASE'}
def native(_exe,_request,stem):
 if stem=='restored_target':return response,{'returncode':0}
 (area/(stem+'_stderr.txt')).write_text(reasons[stem],encoding='utf8');return None,{'returncode':2}
ns={'Path':Path,'copy':copy,'PAPER':paper,'AREA':area,'wire':lambda v:json.dumps(v).encode(),'sha':lambda b:hashlib.sha256(b).hexdigest(),'native':native,'declaration':lambda:{'registered_files':{'code/genesis_g03_adapter.py':'a'*64}}}
exec(compile(ast.Module(body=selected,type_ignores=[]),'unchanged_g03_functions','exec'),ns)
try:ns['controls'](Path('not-executed'),{'cases':[case]},response,[case])
except AttributeError as exc:error=str(exc)
else:raise AssertionError('expected the source-variable shadow failure')
assert 'relative_to' in error
comparisons=0
for n in range(1,9):
 for successes in range(n+1):
  for k in range(1,n+1):
   subsets=list(itertools.combinations(range(n),k));observed=Fraction(sum(any(x<successes for x in sub) for sub in subsets),len(subsets))
   assert Fraction(m.coverage_at_k(n,successes,k))==observed;comparisons+=1
out={'runtime':{'python':sys.version,'executable':sys.executable,'scope':'Focused checks on available workspace interpreter; not reproduction of the declared Python3.12 runtime profile.'},'checks':[
 {'rule':'relocation_can_remove_computational_body','status':'observed','original_value':old['value'],'transformed_value':new['value'],'removed_top_level_nodes':len(receipt['removed_import_rails']),'declared_allowed_difference':receipt['allowed_difference'],'limits':'Independent synthetic mixed bootstrap/computation block. Does not assert an actual pinned historical module contains that pattern.'},
 {'rule':'g03_stale_control_path_shadow','status':'observed','error_type':'AttributeError','error':error,'limits':'Unchanged controls/check_calls AST; synthetic process responses and JSON serialization supplied to avoid importing unread/sealed dependencies. No binary executed.'},
 {'rule':'uniform_subset_coverage_formula','status':'verified_for_enumerated_finite_controls','comparisons':comparisons,'max_n':8,'limits':'Exact finite subset enumeration, not an empirical model result or independence claim.'}
]}
import pytest
config=a.file('_pytest.ini');config.write_text('[pytest]\n',encoding='utf8')
functions=['test_torch_floor_refuses_the_vulnerable_pin','test_bounded_grammar_rejects_noncanonical_and_wrong_arity','test_grammar_checks_emitted_bytes_and_retains_rejected_proposals','test_compaction_keeps_declared_content_and_refuses_restatements','test_ladder_preserves_paired_discordances_and_rejects_duplicate_cases','test_terminal_packet_and_cemetery_view_refuse_corrupt_bytes','test_source_bytes_and_duplicate_json_keys_fail_closed','test_controls_do_not_turn_empirical_obligations_into_success']
paths=[str(code/'tests/test_paper011_mechanisms.py')+'::'+f for f in functions]
paths += [str(code/'tests/test_paper011_genesis_g04.py')+'::'+f for f in ['test_same_mapping_must_preserve_every_prefix_range','test_form_mapping_is_independently_prefix_bound','test_token_signature_preserves_equality_and_non_token_event_fields','test_import_relocation_retains_function_and_exact_stake_expression']]
buffer=io.StringIO()
with contextlib.redirect_stdout(buffer),contextlib.redirect_stderr(buffer):status=pytest.main(['-q','-c',str(config),'--noconftest','-p','no:cacheprovider','--basetemp',str(temp/'pytest'),*paths])
a.file('_boundary_pytest.txt').write_text(buffer.getvalue(),encoding='utf8');out['pytest']={'exit_code':status,'log':'dag/reviews/additional_paper_011_core_boundary_pytest.txt','scope':'Only explicitly selected pure tests; no torch import, native fixture, original loader or historical receipt.'}
a.write('_boundary_probes.json',out)
prior=a.read('_custody_probes.json');prior['runtime']=out['runtime'];a.write('_custody_probes.json',prior)
notes=a.read('_notes.json')
for c in notes['controls']:
 if c['path'].endswith('_custody_probes.json'):c['sha256']=a.sha(a.file('_custody_probes.json'))
a.write('_notes.json',notes)
print(json.dumps({'checks':len(out['checks']),'comparisons':comparisons,'python':sys.version,'pytest_exit':status,'pytest_output':buffer.getvalue()}))
