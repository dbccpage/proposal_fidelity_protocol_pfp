"""Actual reviewed Pydantic declarations with no provider imports."""
import ast,hashlib,json,pathlib,platform
from fractions import Fraction
from typing import List,Tuple
from pydantic import BaseModel,field_validator,model_validator
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_pfp_infrastructure_remaining';path='pfp/infrastructure/pilot_runners/mssn_models.py';b=(R/path).read_bytes();tree=ast.parse(b)
names={'ExactRational','NilpotentBoundaryOperator','QuantumStabilizerCheck'}
module=ast.Module(body=[ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0),*[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name in names]],type_ignores=[])
env=dict(__name__='pfp_infra_audit_synthetic',Fraction=Fraction,List=List,Tuple=Tuple,BaseModel=BaseModel,field_validator=field_validator,model_validator=model_validator);exec(compile(ast.fix_missing_locations(module),path,'exec'),env)
for name in names:env[name].model_rebuild(force=True,_types_namespace=env)
out=[]
def rec(id,name,observed):out.append({'id':id,'name':name,'observed':observed,'result':'reproduced','limit':'Actual isolated Pydantic class, synthetic DTO only; no claim that the stricter deciding seed checker accepts the same payload.'})
q=env['ExactRational'](num=True,den=2);before=q.model_dump();q.den=0;assert before['num']==1 and q.den==0;rec('PFPINFRA-P040','rational_model_coerces_boolean_and_allows_invalid_assignment',{'before':before,'after':q.model_dump()})
q=env['NilpotentBoundaryOperator'](d_k=[[0],[0,1]],d_k_minus_1=[[0,1]]);rec('PFPINFRA-P041','nilpotent_model_accepts_ragged_unchecked_column',q.model_dump())
q=env['QuantumStabilizerCheck'](h_x=[[0,0],[1]],h_z=[[0,0],[0,1]]);rec('PFPINFRA-P042','css_model_accepts_ragged_rows',q.model_dump())
(H/(P+'_checks08.json')).write_text(json.dumps({'python':platform.python_version(),'source_pins':{path:hashlib.sha256(b).hexdigest()},'method':'Full reviewed class AST plus existing Pydantic runtime, no production module imports/providers/native/private data.','controls':out},indent=2)+'\n');print(json.dumps({'controls':len(out),'all_reproduced':True}))
