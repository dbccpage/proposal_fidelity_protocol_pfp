"""Read-vetted local documentation helper countercontrols in owned synthetic fixtures."""
import sys,ast,json,re,os
from pathlib import Path
from urllib.parse import urlparse,unquote
sys.dont_write_bytecode=True
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_documentation_strategy_doors.py';source='\n'.join(a.source(p))
constants={'_SKIP_DIR_NAMES','_LIVE_README_TAIL','_THEORY_RELATIVE','_AVOID_MARK','_FENCE_PHRASE','_FILE_EXTENSIONS','_INLINE_LINK','_REF_DEF','_BACKTICK','_TOPIC','_CORE_NEGATION'}
nodes=[]
for n in ast.parse(source).body:
    if isinstance(n,ast.FunctionDef) and not n.name.startswith('test_'):nodes.append(n)
    elif isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in constants:nodes.append(n)
g=dict(Path=Path,os=os,re=re,urlparse=urlparse,unquote=unquote)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<read-vetted documentation helpers>','exec'),g)
root=a.file('_probe29_inputs');assert not root.exists();root.mkdir()
index=root/'index';index.mkdir()
for dirname in ('a','b'):
    (index/dirname).mkdir();(index/dirname/'record.yaml').write_text('x: 1\n',encoding='utf-8')
(index/'README.md').write_text('[only a](a/record.yaml)\n',encoding='utf-8')
index_result=g['packet_index_drift'](index)
text='Cosmology is verified core; the picnic is not part of the verified core.'
claim_result=g['tower_fence_failures_from_text'](text)
tail=Path('education/the_symbol_game/lessons/how_to_play/readme.md')
live=root/'live'/tail;other=root/'foreign'/tail
for path in (live,other):path.parent.mkdir(parents=True);path.write_text('fixture\n',encoding='utf-8')
live_result=g['how_to_play_readme_problems']('[play]('+other.as_uri()+')',root,live)
assert index_result==[] and claim_result==[] and live_result==[]
result={'runtime':sys.version.split()[0],'source':{'path':p,'sha256':a.row(p)['sha256']},'method':'AST-extracted fullyread helper functions and namedconstants; stdlib only; newowned syntheticfixturetree.','index_control':{'actual_files':['a/record.yaml','b/record.yaml'],'only_cited':'a/record.yaml','reported_problems':index_result},'claim_control':{'text':text,'reported_problems':claim_result},'live_identity_control':{'designated_live':str(live.relative_to(a.ROOT)).replace('\\','/'),'linked_other':str(other.relative_to(a.ROOT)).replace('\\','/'),'different_absolute_paths':live.resolve()!=other.resolve(),'reported_problems':live_result},'limits':'No original documentation/owner imports or originaltree edits; demonstrates helper predicates only, not actual corpus defects.'}
a.write('_probe29.json',result);print(json.dumps(result))
