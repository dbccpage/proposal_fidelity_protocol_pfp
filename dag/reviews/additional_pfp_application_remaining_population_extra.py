"""Independent summary/population joins; no execution of historical owners."""
import collections,gzip,hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_application_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files']
def load(i):
 b=(R/fs[i]['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==fs[i]['sha256'];d=gzip.decompress(b)if fs[i]['path'].endswith('.gz')else b
 x=[json.loads(l)for l in d.splitlines()]if '.jsonl'in fs[i]['path']else json.loads(d)
 return x.get('records',x)if isinstance(x,dict)else x
rows=load(9);summary=load(10);issues=[];checked=0
for detector,table in summary['table'].items():
 for family,expected in table.items():
  population=[r for r in rows if r['family']==family];observed={'n':len(population),'answer_correct':sum(r['answer_correct']is True for r in population)}
  observed.update(collections.Counter(r[detector]['status']for r in population))
  for k in ['n','answer_correct','green','red','noncertifying','crash']:
   checked+=1
   if expected[k]!=observed.get(k,0):issues.append([detector,family,k,expected[k],observed.get(k,0)])
traces=load(14);s=load(13);primary=[r for r in traces if r['call']==0];bissues=[]
for d in ['d2','d3','d4']:
 observed={status:{outcome:sum(r[d]['status']==status and bool(r['failure'])==(outcome=='failure')for r in primary)for outcome in ['failure','success']}for status in ['green','red','noncertifying']}
 if observed!=s[d+'_by_outcome']:bissues.append([d,observed,s[d+'_by_outcome']])
for k,v in [('n_items',len({r['item_id']for r in traces})),('n_primary',len(primary)),('failures',sum(r['failure']for r in primary))]:
 if s[k]!=v:bissues.append([k,s[k],v])
# Cross-document population agreement only; no attribution of the quoted source findings as fresh tests.
census=load(21);mub=load(31);outer=load(33);arch=load(29);adv=load(17);cs=census['summary'];checks={
 'curriculum_files':sum(len(t['files'])for t in load(22)['tracks'])+sum(len(t['file_inventory'])for t in load(24)['tracks'])==cs['curriculum_files'],
 'adversary_modules':len(adv['modules'])==cs['adversary_test_files']==len(census['adversary_modules']),
 'antibodies':len(load(19)['antibodies'])==len(census['antibodies'])==19,
 'numbered_pilot_partition':len(mub['pilots'])+len(outer['rows'])==len(census['pilots'])==75,
 'static_test_functions':sum(m['test_count']for m in adv['modules'])==cs['adversary_static_test_functions'],
 'static_assertions':sum(m['assert_count']for m in adv['modules'])==cs['adversary_static_assertions'],
 'architecture_python':len(arch['python_modules'])==arch['census']['python_modules'],
 'architecture_native':len(arch['native_owner_inventory'])==arch['census']['native_owner_rs_files'],
 'mub_verdicts':len(mub['model_receipt_rows'])==mub['summary']['stored_receipt_model_rows'],
 'outer_population':len(outer['rows'])==outer['summary']['requested_ids'],
}
suffixes=('adversary/__init__.py','adversary/domain/__init__.py','adversary/entrypoints/cli.py');contexts=[]
for i in [17,19,21,22,24,29,31,33]:
 def walk(v,loc='$'):
  if isinstance(v,dict):
   for k,z in v.items():
    if isinstance(z,str)and any(z.endswith(s)for s in suffixes):contexts.append({'file':fs[i]['path'],'location':loc,'field':k,'path_value':z,'sha256':v.get('sha256',v.get('source_sha256'))})
    walk(z,loc+'/'+str(k))
  elif isinstance(v,list):
   for j,z in enumerate(v):walk(z,loc+'/'+str(j))
 walk(load(i))
out={'scope':'Historical data summary consistency only; no providers, grading or source execution','stage_a_summary_comparisons':checked,'stage_a_issues':issues,'stage_b_issues':bissues,'cross_census_checks':checks,'duplicate_manifest_path_contexts':contexts,'historical_git_resolution':{'base_commit':'58a6a1ef92e155b1fa3783081becb41de3e07734','local_cat_file_exit':1,'result':'Not a valid local commit object; no network fetch attempted'},'all_consistency_checks_pass':not issues and not bissues and all(checks.values())}
(H/(P+'_population_extra.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
