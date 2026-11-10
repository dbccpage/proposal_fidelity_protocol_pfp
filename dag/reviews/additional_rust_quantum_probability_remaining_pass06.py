"""Freeze the fully read surface-complex owner before section-control grading."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent;P='additional_rust_quantum_probability_remaining'
np=H/(P+'_notes.json');n=json.loads(np.read_text())
n['20']={'assessment':'Full 564-line complexes owner read. Concrete triangle, square, prism and planar/periodic grid incidence matrices supply declared GF(2) cochain data (33-130,173-313), with exact/open/torus residual fixtures (132-170,315-342). Tests440-536 explicitly verify the five named constructors, planar quotient triviality and torus nonexact cocycles. The historical closed_residual_syndrome_example name/doc at142-149 is contradicted by the correct explicit test468-477: its filled-square all-ones vector is exact, not a nontrivial quotient class.',
 'limitations':['try_surface_grid accepts periodic dimensions of1, but endpoint assignment rather than XOR mishandles self-loops; a1x2 returned complex fails d1*d0=0 and a1x1 torus has wrong quotient dimension (RQPR-F010).','Public fields allow forged counts/matrices, and verify_boundary alone does not validate their consistency.','Positive-dimension admission does not check usize product/addition overflow or bound dense allocations. General grids retain names saying2x2.','No native execution; original tests cover named2x2 grids and zero dimensions, not admitted single-row periodic cases.']}
np.write_text(json.dumps(n,indent=2)+'\n');runpy.run_path(str(H/(P+'_checkpoint.py')))
rp=H/(P+'.json');r=json.loads(rp.read_text());f=json.loads((H/(P+'_scope.json')).read_text())['files'][20]
ev=lambda a,b:{'path':f['path'],'sha256':f['sha256'],'lines':[a,b]}
finding={'id':'RQPR-F010','severity':'medium','title':'Single-row periodic grids mishandle self-loop incidence',
 'finding':'try_surface_grid admits m,n>=1. build_surface_d0 assigns1 to both endpoints instead of XORing endpoint incidences. When a periodic extent is1, those endpoints coincide and a loop is incorrectly given a nonzero coboundary row. For m=1,n=2, the returned d1*d0 has rows[1,1], so the supposed complex is not boundary-valid. For1x1 it passes d1*d0=0 but has quotient dimension1 rather than2 for the declared torus.',
 'evidence':[ev(217,233),ev(254,308),ev(440,453)],
 'recommended_action':'XOR endpoint incidences so self-loops cancel, or explicitly refuse periodic extents below2. Validate the returned chain condition and test1x1,1x2,2x1 cases; retain checks for normal2x2 grids.',
 'validation':'Independent exact finite incidence reconstruction, no native execution.'}
r['findings']=[x for x in r['findings'] if x['id']!=finding['id']]+[finding]
def rank(a):
 a=[v[:] for v in a];k=0
 for j in range(len(a[0]) if a else 0):
  p=next((i for i in range(k,len(a)) if a[i][j]),None)
  if p is None:continue
  a[k],a[p]=a[p],a[k]
  for i in range(len(a)):
   if i!=k and a[i][j]:a[i]=[x^y for x,y in zip(a[i],a[k])]
  k+=1
 return k
def grid(m,n,xor_endpoints):
 vid=lambda row,col:(row%m)*n+(col%n)
 edges=[(vid(i,j),vid(i,j+1)) for i in range(m) for j in range(n)]+[(vid(i,j),vid(i+1,j)) for i in range(m) for j in range(n)]
 d0=[[0]*(m*n) for _ in edges]
 for row,(u,v) in zip(d0,edges):
  if xor_endpoints:row[u]^=1;row[v]^=1
  else:row[u]=1;row[v]=1
 d1=[]
 for i in range(m):
  for j in range(n):
   row=[0]*len(edges)
   for e in [vid(i,j),m*n+vid(i,j+1),vid(i+1,j),m*n+vid(i,j)]:row[e]^=1
   d1.append(row)
 product=[[sum(d1[i][k]*d0[k][j] for k in range(len(edges)))%2 for j in range(m*n)] for i in range(m*n)]
 return {'shape':[m,n],'boundary_product':product,'boundary_valid':not any(map(any,product)),'quotient_dimension_if_boundary_valid':len(edges)-rank(d0)-rank(d1)}
controls=[{'source_assignment':grid(m,n,False),'endpoint_xor_control':grid(m,n,True)} for m,n in [(1,1),(1,2),(2,1),(2,2)]]
assert controls[0]['source_assignment']['quotient_dimension_if_boundary_valid']==1
assert controls[0]['endpoint_xor_control']['quotient_dimension_if_boundary_valid']==2
assert controls[1]['source_assignment']['boundary_product']==[[1,1],[1,1]]
assert controls[2]['source_assignment']['boundary_valid'] is False
assert all(c['endpoint_xor_control']['boundary_valid'] for c in controls)
assert controls[3]['source_assignment']['boundary_valid']
cp=H/(P+'_surface_controls.json');cp.write_text(json.dumps({'method':'Independent exact finite incidence reconstruction; not original Rust execution','passed':True,'controls':controls},indent=2)+'\n')
r['validation']=[x for x in r['validation'] if x.get('id')!='RQPR-SURFACE-CONTROLS']
r['validation'].append({'id':'RQPR-SURFACE-CONTROLS','path':str(cp.relative_to(H.parents[1])).replace('\\','/'),'sha256':hashlib.sha256(cp.read_bytes()).hexdigest(),'passed':True,'native_execution':False})
r['audit_state']='frozen_for_section_control_post_freeze_evaluation'
rp.write_text(json.dumps(r,indent=2)+'\n')
with (H/(P+'.md')).open('a',encoding='utf-8') as md:md.write('\n\n## Frozen for section-control evaluation\n\nCoverage is35/51 full bodies,16pending. The564-line complexes owner was completed. RQPR-F010 and four independent incidence controls capture single-row periodic self-loop failures; ordinary2x2 remains boundary-valid. Audit reading is now frozen for priority post-freeze grading.\n')
print(json.dumps({'full':r['full_source_read_count'],'remaining':len(r['remaining_work']),'findings':len(r['findings']),'report_sha256':hashlib.sha256(rp.read_bytes()).hexdigest()}))
