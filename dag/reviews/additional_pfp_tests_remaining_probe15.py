"""Read-vetted authority-ceiling assertion control without contract imports."""
import sys
sys.dont_write_bytecode=True
import ast
import additional_pfp_tests_remaining_audit as a
p='pfp/tests/test_packet_contracts.py'
t=ast.parse('\n'.join(a.source(p)))
fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='test_every_contract_declares_its_authority_ceiling')
fn.decorator_list=[]
ns={};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<read authority assertion>','exec'),ns)
results={}
for label,contract in [('missing_descriptor',{}),('missing_authority',{'descriptor':{}}),('explicit_null',{'descriptor':{'authority_effect':None}}),('explicit_None_string',{'descriptor':{'authority_effect':'None'}}),('promoted',{'descriptor':{'authority_effect':'Promote'}})]:
 contract['contract_id']='synthetic'
 try:ns[fn.name]({'contract':contract})
 except AssertionError:results[label]='rejected'
 else:results[label]='accepted'
assert results=={'missing_descriptor':'accepted','missing_authority':'accepted','explicit_null':'accepted','explicit_None_string':'accepted','promoted':'rejected'}
a.write('_probe15.json',{'runtime':sys.version,'source':{'path':p,'sha256':a.row(p)['sha256'],'lines':[100,107]},'results':results,'limits':['One undecorated test assertion extracted only; no package imports, YAML contract reads or original source modifications.','This shows missing metadata does not fail the named test, not that actual contracts omit the field.']})
print('missing authority metadata passes the named declaration test')
