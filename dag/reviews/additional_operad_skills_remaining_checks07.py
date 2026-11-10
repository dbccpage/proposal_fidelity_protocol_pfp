"""Pure controls over admitted examples; never imports a retained skill program."""
import hashlib,json,pathlib,re,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,k,obs,limits):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':f'OPSKILL-CHECK-{k:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limits})
schema=json.loads((R/fs[240]['path']).read_text());pat=schema['properties']['tags']['items']['pattern'];assert re.fullmatch(pat,'SSS') is None
add(241,44,{'supplied_template_tag':'SSS','schema_pattern':pat,'matches':False,'global_required':schema['required'],'variation_missing_required':'section'},'Direct schema predicate and full source comparison; no importer executed, no schema proves pedagogical truth.')
txt=(R/fs[237]['path']).read_text();title=re.search(r'^## title: "(This is an extremely long title.*?)"$',txt,re.M).group(1);assert len(title)<=255
add(237,45,{'allegedly_overlong_title':title,'actual_characters':len(title),'schema_maximum':255,'actually_over_maximum':False},'Only title length evaluated; damaged Markdown heading/fence itself is a separate problem. This is not an executing invalid-fixture suite.')
P0=[[1,0],[0,0]];v=[1,0];after=[sum(a*b for a,b in zip(row,v))for row in P0];assert after==v
add(254,46,{'admitted_ideal_projective_measurement':P0,'eigenstate':v,'conditional_post_measurement_state':after,'changed':False},'Exact admitted finite quantum formalism counterexample to unconditional eigenstate-changes wording. It does not derive physical measurement assumptions or invoke a provider/native engine.')
examples=['const char *s = "a/*not a comment*/b";','int/*comment*/x;'];changed=[re.sub(r'/\*[\s\S]*?\*/','',s)for s in examples];assert changed==['const char *s = "ab";','intx;']
add(293,47,{'before':examples,'after_block_regex':changed,'string_value_changed':True,'identifier_tokens_merged':True},'Exact isolated regex used by owner, run only on in-memory synthetic source. No retained purge function or file write executed.')
test=pathlib.PurePosixPath('tests/fixtures/helper.rs');skip=test.name.lower().startswith('test')or test.name.lower().startswith('tests');assert not skip
add(293,48,{'test_tree_path':str(test),'owner_basename_skip':skip},'Pure path predicate; test directory ancestry is not checked. No files created/removed.')
F=lambda x:x-1 if 1<=x<=3 else 10
assert all(F(x)<x for x in(1,2,3)) and F(4)>4
add(261,49,{'three_observations':[[x,F(x)]for x in(1,2,3)],'unseen_input':[4,F(4)],'universal_decrease':False},'Finite countermodel to extrapolation from three observed runs, not a claim about the shared engine actual evaluator.')
(H/(P+'_checks07.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
