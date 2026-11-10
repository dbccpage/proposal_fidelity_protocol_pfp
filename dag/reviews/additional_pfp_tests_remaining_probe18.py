"""Exercise two reviewed AST scanners on inert scoped text fixtures."""
import sys
sys.dont_write_bytecode=True
import ast
import unittest
from pathlib import Path
import additional_pfp_tests_remaining_audit as a
b='pfp/tests/'
def cls(name,classname):
 tree=ast.parse('\n'.join(a.source(b+name)))
 node=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name==classname)
 ns={'ast':ast,'Path':Path,'unittest':unittest}
 exec(compile(ast.Module(body=[node],type_ignores=[]),'<read-vetted architecture scanner>','exec'),ns)
 return ns[classname]()
root=Path('dag/reviews/additional_pfp_tests_remaining_probe18_inputs').resolve()
assert root.is_relative_to(Path('dag/reviews').resolve()) and root.name.startswith('additional_pfp_tests_remaining_')
domain=root/'pfp/domain';nested=domain/'cohomology';nested.mkdir(parents=True,exist_ok=True)
alias=nested/'alias.py';direct=nested/'direct.py'
assert not direct.exists(), 'fresh bounded fixture required'
alias.write_text('from pfp import infrastructure\nfrom ... import ffi\n',encoding='utf-8')
clean=cls('test_pfp_clean_arch.py','TestPfpCleanArchitecture');clean.pfp_dir=root/'pfp'
purity=cls('test_domain_layer_purity.py','TestDomainLayerPurity');purity.symbol_game_root=root/'pfp'
miss_clean=clean._import_violations(domain,('pfp.infrastructure','pfp.ffi'),('infrastructure',))
miss_purity=purity._check_forbidden_imports(nested)
assert miss_clean==miss_purity==[]
direct.write_text('from pfp.infrastructure import storage\n',encoding='utf-8')
hit_clean=clean._import_violations(domain,('pfp.infrastructure','pfp.ffi'),('infrastructure',))
hit_purity=purity._check_forbidden_imports(nested)
assert len(hit_clean)==len(hit_purity)==1
a.write('_probe18.json',{'runtime':sys.version,'sources':[{'path':b+name,'sha256':a.row(b+name)['sha256']} for name in ['test_pfp_clean_arch.py','test_domain_layer_purity.py']],'alias_source':alias.read_text(),'alias_violations':{'clean_arch':miss_clean,'layer_purity':miss_purity},'direct_source':direct.read_text(),'direct_violations':{'clean_arch':hit_clean,'layer_purity':hit_purity},'fixture_pins':[{'path':str(p.relative_to(Path.cwd())).replace('\\','/'),'sha256':a.sha(p)} for p in [alias,direct]],'limits':['Only two read-vetted local test classes executed; no scanned text imported.','All fixture writes confined to dedicated dag/reviews prefix, retained inertly; no original corpus scan, source edit or native execution.']})
print('both scanners miss imported submodule aliases; direct-module controls detected')
