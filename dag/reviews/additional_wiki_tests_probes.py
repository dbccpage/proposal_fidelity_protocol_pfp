"""Bounded offline documentation controls; no original modules imported or snippets executed."""
import ast,collections,hashlib,itertools,json,pathlib,string
from fractions import Fraction as Q
H=pathlib.Path(__file__).resolve().parent
R=H.parents[1]
P='additional_wiki_tests'
sources=['workflows/tasks/paper_run_rules/test_paper_run_domain_purity.py',
         'workflows/tasks/oracle_fixture_freeze/freeze_json_acceptance.py',
         'workflows/tasks/paper_run_rules/paperrun/transition_event.py']
out={'source_pins':[{'path':p,'sha256':hashlib.sha256((R/p).read_bytes()).hexdigest()}for p in sources],
     'controls':[],'limits':['Only the reviewed scanner function is loaded through an AST extraction. Planted code is parsed, never executed.',
                            'Other controls are independent finite calculations, not new production verifier/test-suite replays.']}
# Extract exactly the reviewed scanner definition and its immutable name set.
source=(R/sources[0]).read_text();tree=ast.parse(source)
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='disk_io_calls')
ns={'ast':ast,'Path':pathlib.Path,'IO_METHODS':frozenset({'read_bytes','read_text','write_bytes','write_text'})}
exec(compile(ast.Module(body=[fn],type_ignores=[]),sources[0],'exec'),ns)
snippets={
 'positive_direct':"def f(p):\n    return open(p).read()\n",
 'alias_builtin':"def f(p):\n    reader = open\n    return reader(p).read()\n",
 'path_open':"from pathlib import Path\ndef f(p):\n    return Path(p).open().read()\n",
 'os_open':"import os\ndef f(p):\n    return os.open(p, os.O_RDONLY)\n",
 'io_alias':"from io import open as reader\ndef f(p):\n    return reader(p).read()\n",
}
results={}
for name,text in snippets.items():
 path=H/(P+'_probe_'+name+'.py.txt');path.write_text(text,encoding='utf-8')
 results[name]={'snippet':text,'scanner_result':ns['disk_io_calls'](path)}
assert results['positive_direct']['scanner_result']==[(2,'open')]
assert all(not v['scanner_result']for k,v in results.items()if k!='positive_direct')
out['controls'].append({'id':'WIKIT-P01','kind':'actual scanner, synthetic source only','results':results,
 'conclusion':'The name scanner detects its direct positive control and misses four file-I/O spellings. It does not prove absence of disk I/O.'})

# Reproduce the exact finite LCG bit sequence without invoking the fixture writer.
state=480;counts=collections.Counter()
for _ in range(262144):
 state=(state*6364136223846793005+1442695040888963407)%(2**64)
 exponent=(state>>52)&2047;fraction=state&((1<<52)-1)
 kind=('nan'if fraction else 'infinity')if exponent==2047 else ('normal'if exponent else ('subnormal'if fraction else 'negative_zero'if state>>63 else 'positive_zero'))
 counts[kind]+=1
assert counts['infinity']==counts['negative_zero']==counts['positive_zero']==0
out['controls'].append({'id':'WIKIT-P02','kind':'exact full seeded population classification','seed':480,'count':262144,
 'counts':dict(counts),'absent':['infinity','positive_zero','negative_zero'],
 'conclusion':'The seeded float stream contains NaNs and subnormals but neither infinity nor signed zero. Infinity has separate hard-coded special vectors; negative-zero truthiness is a separate RAWS example, not a float-rendering sample.'})

observed=[1]*64;good=observed+[1];bad=observed+[2]
assert all(observed[i+1]-observed[i]==0 for i in range(63))
assert good[64]-good[63]==0 and bad[64]-bad[63]==1
out['controls'].append({'id':'WIKIT-P03','kind':'finite-data nonidentifiability counterexample',
 'observed_terms':64,'candidate':'a(n+1)-a(n)=0','observed_residuals_all_zero':True,
 'extension_A_next_term':1,'extension_B_next_term':2,'extension_B_next_residual':1,
 'conclusion':'Any finite prefix/held-out agreement can be shared by an extension that violates the proposed all-n recurrence; additional generative premises are necessary.'})

def digest(x):return hashlib.sha256(x).hexdigest()
before=b'original answer';after=b'changed answer';pin=digest(before)
assert digest(after)!=pin and digest(after)==digest(after)
out['controls'].append({'id':'WIKIT-P04','kind':'unanchored digest counterexample',
 'frozen_external_pin_detects_change':digest(after)!=pin,'co_rewritten_receipt_consistent':True,
 'conclusion':'Changing data and its co-stored digest preserves local consistency. A hash detects drift relative to a separately retained expected digest; it does not prove historical immutability or time of origin.'})

template='Question: ${question}\nData: ${data}'
def render(question,data):return string.Template(template).substitute(question=question,data=data),template.replace('${data}',data).replace('${question}',question)
main=render('Q','literal ${question}');reverse=render('literal ${data}','D')
assert main[0]!=main[1]and reverse[0]==reverse[1]
out['controls'].append({'id':'WIKIT-P05','kind':'independent standard-library substitution control',
 'data_contains_question_placeholder_differs':main[0]!=main[1],
 'question_contains_data_placeholder_differs':reverse[0]!=reverse[1],
 'conclusion':'The page\'s second suggested exercise only exposes a problem if replacement order is reversed; data-first then question preserves the inserted ${data} in the question.'})

# Small mathematical examples from the pages, independently reconstructed.
edges=[(0,1),(1,2),(2,0)];rhs=[1,1,1]
solutions=[x for x in itertools.product(range(2),repeat=3)if all((x[u]^x[v])==b for(u,v),b in zip(edges,rhs))]
repairs=[]
for j in range(3):
 changed=rhs.copy();changed[j]^=1
 if any(all((x[u]^x[v])==b for(u,v),b in zip(edges,changed))for x in itertools.product(range(2),repeat=3)):repairs.append(j)
assert not solutions and repairs==[0,1,2]
assert min(abs(1-2*c)for c in range(-20,21))==1
minimizers=[c for c in range(-20,21)if abs(1-2*c)==1]
assert minimizers==[0,1]
assert 4*Q(1)*Q(1)-(Q(1)+Q(1)-Q(4))**2==0
out['controls'].append({'id':'WIKIT-P06','kind':'independent small exact worksheet controls',
 'odd_cycle_global_solutions':len(solutions),'all_unit_cost_edge_repairs':repairs,
 'integer_scalar_minimum':1,'integer_minimizers':minimizers,'rational_zero_residual_witness':'1/2',
 'equilateral_fan_deficits':{str(n):str(1-Q(n,6))for n in [5,6,7]},
 'squared_sides_1_1_4_H':'0',
 'limits':'Odd-cycle population is exhaustive. Integer optimality globally follows odd parity of 1-2c and witnesses0,1, not just the bounded enumeration. No production geometry or physics checker invoked.'})
(H/(P+'_probes.json')).write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'controls':len(out['controls']),'float_population':dict(counts),'scanner_missed_aliases':4,'result':'PASS (documented counterexamples reproduced)'}))
