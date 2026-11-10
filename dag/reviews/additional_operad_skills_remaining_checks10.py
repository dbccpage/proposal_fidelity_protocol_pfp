"""Independent in-memory controls for scanner and test-runner predicates."""
import ast,hashlib,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,o,l):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':o,'limitations':l})
arch_only=pitfalls_only=True;ast_rules=()if arch_only else('rule',);run_arch=not pitfalls_only;assert not ast_rules and not run_arch
add(418,73,{'arch_only':arch_only,'pitfalls_only':pitfalls_only,'active_ast_rules':ast_rules,'architecture_pass_enabled':run_arch},'Exact Boolean orchestration predicates; syntax parsing still occurs. No source scanner invoked.')
node=ast.parse('from .. import infrastructure').body[0];record={'module':node.module or'','name':node.names[0].name,'is_relative':node.level>0};assert record['module']==''
add(414,74,{'source':'from .. import infrastructure','AST_level':node.level,'stored_record':record,'rule_resolution_key':record['module'],'relative_depth_preserved':False},'Source carrier retains a Boolean but loses depth; project rule resolves only empty module. No arbitrary Python import resolver implemented.')
line='assert valid, "# noqa"';m=re.search(r'#\s*noqa(?::\s*([A-Za-z0-9_,\s]+))?',line,re.I);assert m and m.group(1)is None
add(414,75,{'source_line':line,'suppression':'*','actual_comment_present':False},'Exact regex matches a string literal and suppresses the same-line assert rule. No retained program called.')
name='latest.py';assert'test'in name
add(426,76,{'production_filename':name,'test_substring_classifier':True,'architecture_rules_skip_is_test':True},'Pure filename predicate demonstrates overbroad test exemption. No claim this exact module exists in repository.')
call=ast.parse("pytest.raises(Exception, match=None)",mode='eval').body;has_match=any(k.arg=='match'and k.value is not None for k in call.keywords);assert has_match
add(432,77,{'source':'pytest.raises(Exception, match=None)','gate_has_match':has_match,'actual_match_value':None},'AST Constant(None) is a node, so the source kw.value is not None check does not reject a missing regex restriction.')
proc_returncode=0;findings=[{'code':'GATE_ERROR'}];status='PASS'if proc_returncode==0 else'FAIL';collection={'status':'FAIL','exit':2};focused={'exit':0};final=1 if status!='PASS'or focused['exit']!=0 else 0
add(431,78,{'malformed_stdout_process_exit':proc_returncode,'recorded_findings':findings,'gate_status':status,'collection':collection,'focused':focused,'overall_exit':final},'Exact status/exit selection with synthetic response values, no subprocess/provider/test invocation; it exposes missing failure propagation, not a claim current gate emitted malformed output.')
tree=ast.parse((R/fs[424]['path']).read_text());assignment=next(n for n in tree.body if isinstance(n,ast.AnnAssign)and isinstance(n.target,ast.Name)and n.target.id=='ALL_PITFALL_RULES');names=[n.id for n in assignment.value.elts];assert len(names)==24
add(424,79,{'active_default_pitfall_rule_classes':names,'count':len(names),'advertised_catalog_size':50},'Full source body separately reviewed. Structural count alone is not semantic completeness; some classes cover more than one surface, but numerous rubric entries have no corresponding predicate.')
(H/(P+'_checks10.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
