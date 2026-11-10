"""Bounded arithmetic, displayed-example and static checks; no repository imports."""
from pathlib import Path
from fractions import Fraction as F
import ast
import dataclasses
import datetime
import enum
import hashlib
import json
import re
import struct
import typing
import urllib.parse
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'dag/reviews/additional_operads_education_atlas'
scope=json.loads(Path(str(P)+'_scope.json').read_text())
def body(i):
    r=scope['files'][i]; b=(ROOT/r['path']).read_bytes()
    assert hashlib.sha256(b).hexdigest()==r['sha256']
    return b.decode().replace('\r\n','\n')
def block(i,lang):
    return re.findall(r'^```'+lang+r'\n(.*?)^```',body(i),re.M|re.S)
checks=[]
def add(name,result,limit): checks.append(dict(id=name,result=result,limit=limit))

# Literal published manifest and signatures, not a replacement production checker.
manifest=json.loads(block(48,'json')[0])
catalog={'nomos-law-contract-manager':(('State',),'Contract'),
         'meta-law-contract-enforcer':(('Contract','Code'),'Audit')}
def splice(a,i,b):
    if a[0][i]!=b[1]: return {'refusal':'COLOUR_MISMATCH','expected':a[0][i],'actual':b[1]}
    return (a[0][:i]+b[0]+a[0][i+1:],a[1])
a,b=(catalog[s['operation']] for s in manifest['pipeline'])
bad=splice(a,manifest['pipeline'][1]['slot'],b); good=splice(b,0,a)
assert bad['refusal']=='COLOUR_MISMATCH' and good==( ('State','Code'),'Audit')
add('OEA-T01',{'published_manifest_result':bad,'reversed_profile':good,'declared_inputs':manifest['source_colours']},
    'Pure ordered-profile arithmetic using the two displayed lesson signatures; no production validator or callback run.')

# Exact finite examples refuting implications, not testing repository effectful owners.
diag_norm=max(F(1,2),F(1)); assert diag_norm==1
add('OEA-T02',{'diagonal_operator':['1/2','1'],'l1_operator_norm':str(diag_norm),'sample_x':[2,0],'sample_after':[1,0]},
    'One strictly decreasing sample does not imply uniform metric contraction; fixed point/sample domain must be admitted.')
assert 1<2 and 100>0 and 101>2
add('OEA-T03',{'before_phi_gamma':[2,0],'after_phi_gamma':[1,100],'or_descent':True,'sum_increased':True,
    'mass_floor':1,'before_mass':1,'after_mass':100},'OR descent permits arbitrarily growing other component; positive lower bound is not conservation or task preservation.')
epsilon=F(1,100); x=F(1); y=x-epsilon/2; z=y-F(1,1000)
assert abs(y-x)<epsilon and y*y>0 and z*z<y*y
add('OEA-T04',{'epsilon':str(epsilon),'x':str(x),'y':str(y),'distance':str(abs(y-x)),
    'phi_y':str(y*y),'nearby_z':str(z),'phi_z':str(z*z),
    'integer_defect_graph':{'states':['A','B'],'neighbors':{'A':['B'],'B':['A']},'defect_count':{'A':1,'B':0},
        'observed_trajectory':['A','A'],'representation':{'A':[0],'B':[1]},'delta_D':0,'A_is_neighbor_local_minimum':False}},
    'The finite integer-defect graph satisfies the displayed stopping condition while having a lower-defect neighbor. The smooth Phi(x)=x^2 example independently shows the general residual implication fails.')

# These are reviewed teaching blocks; execute only the pure dataclass declarations.
snippet=block(47,'python')[0]
tree=ast.parse(snippet)
assert all(isinstance(n,ast.ClassDef) for n in tree.body)
ns={'enum':enum,'dataclass':dataclasses.dataclass,'field':dataclasses.field,'Any':typing.Any,
    'Dict':typing.Dict,'datetime':datetime.datetime,'timezone':datetime.timezone}
exec(compile(tree,'<reviewed-level06-receipt-snippet>','exec'),ns)
r=ns['EvidenceReceipt']('r',ns['EvidenceType'].COMPILATION,True)
r.metadata['changed_after_construction']=True
assert r.metadata['changed_after_construction']
add('OEA-T05',{'frozen_dataclass_metadata_mutable':True},'Literal displayed declaration only; no assertion of current production constructor behavior.')

receipt=json.loads(block(50,'json')[0]); expected=receipt['rfc8785_canonical_hash']
without={k:v for k,v in receipt.items() if k!='rfc8785_canonical_hash'}
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert expected==hashlib.sha256(b'').hexdigest() and expected not in (digest(receipt),digest(without))
add('OEA-T06',{'declared_digest':expected,'empty_bytes_digest':hashlib.sha256(b'').hexdigest(),
    'full_sorted_json_digest':digest(receipt),'without_self_field_digest':digest(without)},
    'Illustrative receipt is not a valid binding under either displayed sorted-JSON convention; no alternative undocumented canonicalization is inferred.')

assert F(2,5)==F(2,5) and not F(2,5)>F(2,5) and F(2,3)>F(2,5)
add('OEA-T07',{'2_of_5_unconfirmed_downgrades':False,'2_of_3_unconfirmed_downgrades':True,
    'three_unknown_labels_would_yield_toxicity':'1'},'Arithmetic of the displayed strict threshold only; unknown is not independently confirmed benign and no statistical guarantee follows.')

svg=[];png=[]
for i,r in enumerate(scope['files']):
    b=(ROOT/r['path']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
    if r['path'].endswith('.svg'):
        e=ET.fromstring(b); local=lambda q:q.rsplit('}',1)[-1]
        tags=[local(n.tag) for n in e.iter()]
        external=[v for n in e.iter() for k,v in n.attrib.items() if local(k)=='href' and not v.startswith('#')]
        assert 'script' not in tags and not external
        svg.append({'path':r['path'],'sha256':r['sha256'],'viewBox':e.attrib['viewBox'],
            'text_elements':sum(t=='text' for t in tags),'script_elements':0,'external_hrefs':external})
    if r['path'].endswith('.png'):
        assert b[:8]==b'\x89PNG\r\n\x1a\n' and b[12:16]==b'IHDR'
        w,h=struct.unpack('>II',b[16:24]);png.append({'path':r['path'],'sha256':r['sha256'],'width':w,'height':h,
            'inspection':'entire image visually inspected via view_image original; header dimensions parsed; no encoder/metadata/byte-by-byte human audit'})

links=[]
for r in scope['files']:
    if not r['path'].endswith('.md'):continue
    text=(ROOT/r['path']).read_text(encoding='utf-8')
    for m in re.finditer(r'\[[^\]\n]*\]\(([^)\n]+)\)',text):
        target=m.group(1).strip().split(' ',1)[0].strip('<>')
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',target) or target.startswith('#'):continue
        path=urllib.parse.unquote(target.split('#',1)[0]); dest=((ROOT/r['path']).parent/path).resolve()
        links.append({'source':r['path'],'line':text.count('\n',0,m.start())+1,'target':target,
            'exists':dest.exists(),'resolved':str(dest),'inside_repo':dest.is_relative_to(ROOT)})

ledger=body(22)
rows=[l for l in ledger.splitlines() if re.match(r'^\|\s*\d+\s*\|',l)]
# Preserve observed table shape rather than inferring a historical Git-tree match.
add('OEA-T08',{'numbered_ledger_rows':len(rows),'header_number_examples':rows[:1]},
    'Static historical-ledger row count, not a review or Git-object verification of its referenced files.')
out={'status':'complete','fresh_checks':checks,'svg_checks':svg,'png_metadata':png,
    'navigation':{'method':'Literal inline Markdown links; local target existence only, fragments and reference-style links not validated; no target body reading credit.',
        'occurrences':len(links),'missing':sum(not x['exists'] for x in links),'outside_repo':sum(not x['inside_repo'] for x in links),'links':links},
    'limits':['No production code imports, native/model/provider execution or original writes.','Arithmetic counterexamples concern stated implications, not hidden physical or model-performance claims.']}
Path(str(P)+'_checks.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'fresh_checks':len(checks),'svg':len(svg),'png':len(png),'navigation_occurrences':len(links),'missing':out['navigation']['missing'],'ledger_numbered_rows':len(rows)}))
