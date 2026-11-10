"""Read-only identity and bounded parsed checks, plus isolated source-archive tests."""
import collections,hashlib,json,os,re,subprocess,sys,zipfile
from pathlib import Path
H=Path(__file__).resolve().parent; R=H.parents[1]; P='additional_paper_008_support'
B=R/'papers/pfp/008_pfp_mssn_tower_challenges_and_retraction_benchmarks'; O=H/'paper_008_support_inspection'
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(s,x):(H/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def lf(b):return b.decode('utf-8').replace('\r\n','\n').replace('\r','\n').encode()
def bindings():
 c=load(H/(P+'_custody.json')); archive=R/c['archive_path']; root=c['archive_root']; result={}
 index=load(B/'docs/source_archive/source_index.json')['entries']; rows=[]
 with zipfile.ZipFile(archive) as z:
  for e in index:
   raw=(B/e['path']).read_bytes(); old=z.read(root+'/'+e['path']);rows.append({'path':e['path'],'expected_sha256':e['sha256'],'expected_bytes':e['bytes'],'current_sha256':sha(raw),'current_bytes':len(raw),'raw_match':sha(raw)==e['sha256'],'lf_match':sha(lf(raw))==e['sha256'],'archive_sha256':sha(old),'archive_match':sha(old)==e['sha256'],'archive_bytes_match':len(old)==e['bytes']})
 result['source_index']=rows
 receipt=load(B/'docs/review_validation_2026_10_02.json')['retained_lean_bindings'];rows=[]
 for path,expected in receipt['protected_source_sha256'].items():
  rel='lean4/'+path.split('/lean4/',1)[1];raw=(B/rel).read_bytes();rows.append({'path':rel,'expected_sha256':expected,'current_sha256':sha(raw),'raw_match':sha(raw)==expected,'lf_match':sha(lf(raw))==expected})
 for key,rel in [('census_tool_sha256','tools/replay_full_axiom_census.py'),('full_axiom_report_sha256','lean4/full_axiom_report.txt'),('full_census_source_sha256','lean4/FullCensus.lean')]:
  raw=(B/rel).read_bytes();rows.append({'path':rel,'receipt_field':key,'expected_sha256':receipt[key],'current_sha256':sha(raw),'raw_match':sha(raw)==receipt[key],'lf_match':sha(lf(raw))==receipt[key]})
 result['lean_receipt_bindings']=rows
 raw=(B/'lean4/full_axiom_report.txt').read_bytes();decl=[];other=[]
 for n,line in enumerate(raw.decode().splitlines(),1):
  m=re.fullmatch(r"'(.*)' depends on axioms: \[(.*)\]",line)
  if m:decl.append({'line':n,'name':m[1],'axioms':m[2].split(', ') if m[2] else []})
  else:
   m=re.fullmatch(r"'(.*)' does not depend on any axioms",line)
   if m:decl.append({'line':n,'name':m[1],'axioms':[]})
   elif line.strip():other.append({'line':n,'text':line})
 assert len(decl)==576 and len({x['name'] for x in decl})==576
 assert all(set(x['axioms'])<={'propext','Quot.sound','Classical.choice'} for x in decl)
 save('_axiom_summary.json',{'path':(B/'lean4/full_axiom_report.txt').relative_to(R).as_posix(),'sha256':sha(raw),'declarations':len(decl),'headers':other,'axiom_sets':dict(collections.Counter(', '.join(x['axioms']) or '(none)' for x in decl)),'declaration_rows':decl,'parser_correction':'Complete quoted name matched greedily, retaining the prime-suffixed ExactRat.Frac.den_pos\' declaration omitted by the initial narrow regex. No source defect inferred.','limit':'Every line parsed and allowed-axiom/name uniqueness checked; not a manual full text read or new Lean execution.'})
 cov=load(H/'coverage.json');p=(B/'paper.md').relative_to(R).as_posix();r=next(x for x in cov['files'] if x['path']==p);result['prior_manuscript_reading']=r
 save('_binding_checks.json',result)
 print(json.dumps({'index':{'total':len(index),'raw_match':sum(x['raw_match'] for x in result['source_index']),'lf_match':sum(x['lf_match'] for x in result['source_index']),'archive_match':sum(x['archive_match'] for x in result['source_index'])},'lean_rows':result['lean_receipt_bindings'],'prior_md':r,'axiom_counts':dict(collections.Counter(', '.join(x['axioms']) or '(none)' for x in decl))},indent=2))
def pdfs():
 from PIL import Image
 inv=load(O/'pdf_inventory.json'); result=[];pix={}
 for i in (0,1):
  for page,path in enumerate(inv[i]['page_images'],1):
   with Image.open(R/path) as im:pix[(im.size,sha(im.convert('RGB').tobytes()))]=(i,page)
 for i,row in enumerate(inv):
  q={'path':row['path'],'sha256':row['sha256'],'pages':row['pages'],'full_source_read':False,'raw_pdf_bytes_read_as_text':False}
  if i in (0,1):q.update(method='All pages visually reviewed on complete contact sheets; combined companion page 5 additionally inspected at full resolution.',direct_visual_pages=list(range(1,row['pages']+1)),sheets=row['sheets'])
  elif i==5:
   assert (R/row['path']).read_bytes()==(R/inv[0]['path']).read_bytes();q.update(method='Exact raw PDF equality transfers all 15 visually reviewed manuscript pages.',equal_to=inv[0]['path'],equal_pages=list(range(1,16)))
  else:
   matches=[]
   for page,path in enumerate(row['page_images'],1):
    with Image.open(R/path) as im:k=(im.size,sha(im.convert('RGB').tobytes()))
    assert k in pix,(i,page);j,p=pix[k];matches.append({'page':page,'base_path':inv[j]['path'],'base_page':p,'rgb_sha256':k[1],'size':list(k[0])})
   q.update(method='All pages rendered with the same Poppler settings; complete RGB pixel equality transfers directly observed companion pages.',pixel_equality=matches)
  result.append(q)
 save('_pdf_review.json',{'pdfs':result,'total_pages':sum(r['pages'] for r in inv),'direct_visual_pages':24,'raw_equal_pages':15,'pixel_equal_pages':9,'findings':['Combined companion page 5 / separate study guide page 4: long reproduction commands visibly cross and are clipped at the right edge.','Combined ordering exposes worked study guide answers before the quiz; preface instructions also direct this order.','Retained renders use historical Landau and repository namespaces; raw PDFs were not regenerated after current source renaming.'],'limit':'Complete page-level visual review/equality transfer; not full PDF binary-source reading, PDF security validation, or new learner evaluation.'})
 print(json.dumps({'pages':48,'direct':24,'raw_equal':15,'pixel_equal':9}))
def archive_test():
 c=load(H/(P+'_custody.json')); root=c['archive_root']; dest=O/'archive_source_probe';dest.mkdir(exist_ok=True); idx=load(B/'docs/source_archive/source_index.json')['entries'];selected=[e['path'] for e in idx]+['docs/source_archive/source_index.json','code/retraction_benchmark_runner.py','code/tests/test_008_source_bound_examples.py','pyproject.toml']
 with zipfile.ZipFile(R/c['archive_path']) as z:
  for p in selected:
   target=dest/p;assert target.resolve().is_relative_to(dest.resolve());target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(root+'/'+p))
 env=os.environ.copy();temp=O/'temporary';env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONUTF8='1',TEMP=str(temp),TMP=str(temp))
 cmd=[sys.executable,'-B','-X','utf8','-m','pytest','code/tests/test_008_source_bound_examples.py','-c','pyproject.toml','--confcutdir=.','-o','addopts=','-q','-ra','-p','no:cacheprovider','--basetemp',str(O/'archive_source_pytest')]
 run=subprocess.run(cmd,cwd=dest,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
 result={'command':cmd,'cwd':str(dest),'archive_path':c['archive_path'],'archive_sha256':c['archive_sha256'],'extracted_files':[{'path':p,'sha256':sha((dest/p).read_bytes())} for p in selected],'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'limit':'Only pre-read source test, runner, historical parser owners and public data dependencies extracted; no providers, historical host or Lean replay.'};save('_archive_probe.json',result);print(json.dumps(result,indent=2))
def traces():
 rows=[];systems=set();users=set()
 for p in sorted((B/'docs/source_archive/k4_traces').glob('*.jsonl')):
  raw=p.read_bytes();data=[json.loads(x) for x in raw.decode().splitlines()];turns=[]
  for i,x in enumerate(data,1):
   assert x['turn']==i and json.loads(x['raw_response'])==x['parsed_move']
   assert x['functional_status']=='UNAVAILABLE' and x['admission_status']=='pending' and x['admitted'] is False
   assert all(x[k] is None for k in ['phi1_before','phi1_after','gamma2','xi'])
   assert all(v is None for v in x['unverified_functional_claims'].values())
   assert type(x['elapsed_s']) in (int,float) and 0<=x['elapsed_s']<float('inf')
   assert all(type(x[k]) is int and x[k]>=0 for k in ['input_tokens','output_tokens'])
   systems.add(sha(x['system_prompt'].encode()));users.add(sha(x['user_turn'].encode()))
   turns.append({'turn':i,'parsed_move':x['parsed_move'],'user_turn_sha256':sha(x['user_turn'].encode()),'raw_reply_json_equals_move':True})
  rows.append({'path':p.relative_to(R).as_posix(),'sha256':sha(raw),'rows':len(data),'all_turn_fields_checked':True,'all_raw_reply_json_equals_move':True,'all_functional_fields_unavailable_and_admission_pending':True,'token_and_elapsed_types_nonnegative_finite':True,'parsed_moves':turns})
 save('_trace_checks.json',{'files':rows,'total_rows':sum(r['rows'] for r in rows),'system_templates':len(systems),'unique_user_turns':len(users),'manually_read_prompt_scope':'One complete shared system prompt and Qwen turn-8 baseline, partially_masked, scratchpad and hinted full user prompts. All 90 parsed moves reviewed; other user-turn bodies bounded, not fully read.','limit':'Supplied provider/model/token metadata is not provider-authenticated; host messages inside subsequent prompts are historical assertions, not current replay. No final post-last-move host receipt is present in these top-level null fields.'});print(json.dumps({'files':len(rows),'rows':90,'systems':len(systems),'users':len(users)}))
if __name__=='__main__':{'bindings':bindings,'pdfs':pdfs,'archive_test':archive_test,'traces':traces}[sys.argv[1]]()
