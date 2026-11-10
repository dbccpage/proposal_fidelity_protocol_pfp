"""Independent tiny controls; do not import or execute retained skill programs."""
import argparse,hashlib,json,pathlib,re,sys
from fractions import Fraction
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(i,name,obs,limit):
    f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256'];out.append({'id':name,'status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':obs,'limitations':limit})
missing_catalog_is_dir=False;catalog_findings=[]
if missing_catalog_is_dir:catalog_findings.append('CATALOG_MISSING')
total_findings=len(catalog_findings);exit_code=1 if total_findings>0 else 0
assert exit_code==0
add(73,'OPSKILL-CHECK-008',{'catalog_is_dir':False,'findings':catalog_findings,'check_exit_code':exit_code},'Minimal reproduction of main catalog-dispatch logic, not a retained scanner run. Source audit separately establishes audit_catalog would emit CATALOG_MISSING if called.')
preceding='#[derive(PartialEq, Eq, PartialOrd)]';flag='#[derive('in preceding and 'Ord'not in preceding
assert flag is False
path='code/rust/core_types/src/example.rs';eligible='crates_rs'in path
add(73,'OPSKILL-CHECK-009',{'derive':preceding,'missing_Ord_flag':flag,'current_style_path':path,'path_eligible':eligible},'Exact string-predicate controls; does not compile Rust or prove every enum needs Ord.')
args=['segment-dialogue','--output','eis/antiskills/ooutwire/ok.json','--output','outside.json'];checked=args[args.index('--output')+1]
p=argparse.ArgumentParser();p.add_argument('mode');p.add_argument('--output');delegated=p.parse_args(args).output
assert checked!=delegated
add(78,'OPSKILL-CHECK-010',{'wrapper_checked':checked,'ordinary_argparse_output':delegated},'Demonstrates first-versus-last duplicate option ambiguity with standard argparse, not actual legacy runtime dispatch or an executed path escape.')
share=Fraction(2,5);diverse=share<=Fraction(1,2);concentrated=Fraction(35,100)<=share<=Fraction(1,2)
assert diverse and concentrated
add(67,'OPSKILL-CHECK-011',{'queue_counts':[2,2,1],'maximum_share':str(share),'DIVERSE':diverse,'CONCENTRATED':concentrated},'Finite overlap of declared terminal criteria; neither criterion proves cognitive capture.')
omega=Fraction(1);gauge=-omega;embedded=(omega,Fraction(0));assert abs(omega)==abs(gauge)==sum(abs(x)for x in embedded)==1
add(62,'OPSKILL-CHECK-012',{'carrier':'Q with repair image {0}','initial_obstruction':'1','invertible_coordinate_map':'x -> -x','transformed_obstruction':'-1','embedded_in_Q2':['1','0'],'L1_defect_in_each_case':'1'},'Finite exact countermodel to automatic zero-obstruction from coordinate change or embedding alone. It does not refute a separately specified effective repair or task-preserving quotient.')
a={'finding_id':'f','persona_id':'defect_hunter'};b={**a,'persona_id':None};encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode();ha=hashlib.sha256(encode(a)).hexdigest();hb=hashlib.sha256(encode(b)).hexdigest();assert ha!=hb
add(63,'OPSKILL-CHECK-013',{'persona_overlay_digest':ha,'removed_overlay_digest':hb,'byte_identical':encode(a)==encode(b)},'Declared FindingV1 permits persona_id, so byte identity needs an explicit excluded-field projection. This is a synthetic receipt shape, not a runtime ablation.')
Hmap=lambda c:c;Amap=lambda c:1;assert Amap(Hmap(0))==1
add(79,'OPSKILL-CHECK-014',{'Code':[0],'Witness':[0,1],'H':'identity','A':'constant 1','norm_A_H_at_0':1},'Countermodel to annihilation following from the displayed types alone. No implementation of the purported universal healthy repair is supplied by the skill.')
(H/(P+'_checks02.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
