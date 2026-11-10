"""Vetted AST fragments with synthetic state, no original imports or provider dispatch."""
import ast,dataclasses,hashlib,json,pathlib,threading,types,urllib.error
from fractions import Fraction
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining';pins=[]
def fragments(path,names,env):
 raw=(R/path).read_bytes();tree=ast.parse(raw);nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))and n.name in names];assert {n.name for n in nodes}==set(names)
 pins.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'selected_nodes':[{'name':n.name,'lines':[n.lineno,n.end_lineno]}for n in nodes]})
 env=dict(env);module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*nodes],type_ignores=[]);exec(compile(ast.fix_missing_locations(module),path,'exec'),env);return env
e=fragments('pfp/use_cases/learning.py',['FreezeCorpusUseCase'],{'hashlib':hashlib,'FrozenCorpus':lambda **kw:types.SimpleNamespace(**kw),'AuthorityEffect':types.SimpleNamespace(NONE=types.SimpleNamespace(value='None'))})
a=e['FreezeCorpusUseCase']().execute('synthetic',['a,b','c']);b=e['FreezeCorpusUseCase']().execute('synthetic',['a','b,c']);assert a.sample_ids!=b.sample_ids and a.corpus_sha256==b.corpus_sha256
def timeout(_transport,_body):raise TimeoutError('synthetic uncertain dispatch')
e=fragments('pfp/use_cases/detector_adequacy/stage_b.py',['Budget','actual_usd','_one_call'],{'dataclass':dataclasses.dataclass,'field':dataclasses.field,'threading':threading,'Fraction':Fraction,'PRICE_IN':Fraction(1),'PRICE_OUT':Fraction(1),'urllib':urllib,'request_body':lambda _item:b'synthetic','worst_case_usd':lambda _body:Fraction(1),'dispatch':timeout})
budget=e['Budget'](Fraction(1));record,receipt=e['_one_call'](None,budget,{'item_id':'synthetic'},0);assert budget.spent==0 and budget.reserved==0 and record['cost_usd']=='0'and receipt is None
negative=e['actual_usd']({'usage':{'input_tokens':-2,'output_tokens':True}},b'x');missing=e['actual_usd']({'usage':{}},b'x');assert negative==-1 and missing==0
overspend=e['Budget'](Fraction(1));assert overspend.reserve(Fraction(1));overspend.settle(Fraction(1),Fraction(2));assert overspend.spent>overspend.cap
out={'source_pins':pins,'scope':'AST fragments from fully read owners; synthetic fake I/O only; no imported production package, network, provider, subprocess or source mutation','probes':[
 {'id':'APP-X001','name':'comma_framing_collision','first_ids':a.sample_ids,'second_ids':b.sample_ids,'same_digest':a.corpus_sha256,'result':'reproduced'},
 {'id':'APP-X002','name':'uncertain_timeout_releases_entire_hold','record':record,'spent':str(budget.spent),'reserved':str(budget.reserved),'has_receipt':receipt is not None,'result':'reproduced'},
 {'id':'APP-X003','name':'token_coercion_and_missing_usage','negative_plus_boolean_cost':str(negative),'empty_usage_cost':str(missing),'result':'reproduced'},
 {'id':'APP-X004','name':'settlement_accepts_above_reserved_cap','spent':str(overspend.spent),'cap':str(overspend.cap),'result':'reproduced'}]}
(H/(P+'_extra_probes.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
