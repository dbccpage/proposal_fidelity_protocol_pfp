"""In-memory controls for reviewed repair/diagnostic code; no source mutation."""
import ast,hashlib,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,name,obs,limit):
    f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':name,'status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limit})
t=ast.parse((R/fs[87]['path']).read_text());action_reads=[n.lineno for n in ast.walk(t)if isinstance(n,ast.Attribute)and isinstance(n.value,ast.Name)and n.value.id=='args'and n.attr=='action'];assert action_reads==[]
add(87,'OPSKILL-CHECK-015',{'args_action_read_lines':action_reads,'declared_actions':['repair','check','inspect']},'Structural confirmation after full semantic source reading. No retained CLI invoked; ignored action still reaches execute_auto_learn_repair with only args.dry_run controlling writes.')
exit_code=2;parsed_findings=0;rollback=exit_code!=0 and parsed_findings>0;status='FAILED_RECHECK_ROLLED_BACK'if rollback else'VERIFIED_CLEAN';assert status=='VERIFIED_CLEAN'
add(87,'OPSKILL-CHECK-016',{'verifier_exit':exit_code,'parsed_file_findings':parsed_findings,'rollback':rollback,'result_status':status},'Minimal isolated branch reproduction; representative missing-parser/crash output. Does not launch linter or mypy.')
root=pathlib.PureWindowsPath('C:/repo');reported='C:/outside/file.md';norm=reported.replace('\\','/').lstrip('./');chosen=root/norm;assert not chosen.is_relative_to(root)
add(87,'OPSKILL-CHECK-017',{'root':str(root),'reported_file':reported,'normalized':norm,'selected_path':str(chosen),'within_root':chosen.is_relative_to(root)},'Pure path calculation only; no outside file is read, created or modified.')
raw=b'* item\n\xff';snapshot=raw.decode('utf-8',errors='replace');restored=snapshot.encode('utf-8');assert restored!=raw
add(87,'OPSKILL-CHECK-018',{'raw_hex':raw.hex(),'text_snapshot_roundtrip_hex':restored.hex(),'byte_exact':False},'In-memory counterexample to byte-exact rollback via replacement-decoded text; no source write.')
line='* \n';changed=re.sub(r'^(\s*)\*\s+',r'\1- ',line);assert changed=='- '
add(87,'OPSKILL-CHECK-019',{'original_line_repr':repr(line),'repaired_line_repr':repr(changed),'retains_line_ending':changed.endswith('\n')},'Exact regex control shows whitespace includes newline; the repair can concatenate an empty bullet with the following line. Not a full Markdown semantics test.')
B=[[-1,0,-1],[1,-1,0],[0,1,1]];cycle=[-1,-1,1];product=[sum(a*b for a,b in zip(row,cycle))for row in B];assert product==[0,0,0];minor=B[0][0]*B[1][1]-B[0][1]*B[1][0];assert minor==1
add(89,'OPSKILL-CHECK-020',{'edges':['A->B','B->C','A->C'],'directed_acyclic':True,'incidence_matrix':B,'nonzero_cycle':cycle,'boundary':product,'incidence_rank':2,'one_skeleton_H1_dimension_over_Q':1},'Exact finite graph counterexample separating absence of directed import cycles from vanishing simplicial H1. The wrapper never defines faces/differentials or the cochain whose exactness it labels; imported detector not executed.')
(H/(P+'_checks03.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
