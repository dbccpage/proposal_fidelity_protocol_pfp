"""Bounded current/archive smoke tests and isolated read-owner storage checks."""
import ast,hashlib,importlib.util,json,os,struct,subprocess,sys,types,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];P='additional_paper_006_support';PKG=ROOT/'papers/pfp/006_pfp_epistemic_immune_system_and_cemetery_dag_mining';OUT=HERE/(P+'_inspection');OUT.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def write(s,x):(HERE/(P+s)).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def load_module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
 parent,_,child=name.rpartition('.')
 if parent in sys.modules:setattr(sys.modules[parent],child,m)
 return m
def isolated():
 # Production package initializers are not executed. The port is a typing seam;
 # its behavior is excluded explicitly by replacing that base with object.
 for name in ['pfp','pfp.domain','pfp.domain.entities','pfp.domain.ports','pfp.infrastructure','pfp.infrastructure.persistence']:
  m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
  parent,_,child=name.rpartition('.')
  if parent in sys.modules:setattr(sys.modules[parent],child,m)
 ports=types.ModuleType('pfp.domain.ports.ports');ports.CemeterySinkPort=object;sys.modules[ports.__name__]=ports
 errors=load_module('pfp.domain.exceptions',ROOT/'pfp/domain/exceptions.py')
 entries=load_module('pfp.domain.entities.cemetery_entry',ROOT/'pfp/domain/entities/cemetery_entry.py')
 sink=load_module('pfp.infrastructure.persistence.cemetery_sink',ROOT/'pfp/infrastructure/persistence/cemetery_sink.py')
 nan_a=struct.unpack('>d',bytes.fromhex('7ff8000000000001'))[0];nan_b=struct.unpack('>d',bytes.fromhex('7ff8000000000002'))[0]
 probe={'nan_bits':[struct.pack('>d',x).hex() for x in [nan_a,nan_b]],'normalized':[sink._sanitize_for_cemetery(x) for x in [nan_a,nan_b]],'same_encoded':sink._canonical_json_bytes(sink._sanitize_for_cemetery(nan_a))==sink._canonical_json_bytes(sink._sanitize_for_cemetery(nan_b)),'finite_float_tag_alias':sink._sanitize_for_cemetery(0.5)==sink._sanitize_for_cemetery({'$float_hex':0.5.hex()})}
 write('_isolated_encoding_probe.json',{'method':'Fully read current owner modules loaded with namespace package placeholders and object port base; no package initialization, native seam or provider imports.','source_paths':['pfp/domain/exceptions.py','pfp/domain/entities/cemetery_entry.py','pfp/infrastructure/persistence/cemetery_sink.py'],'results':probe})
 import pytest
 os.chdir(PKG)
 return pytest.main(['-c',str(PKG/'pyproject.toml'),'--confcutdir',str(PKG),'-o','addopts=','-p','no:cacheprovider','-q','code/tests/test_006_worked_example.py','--basetemp',str(OUT/'isolated_storage_tmp')])

def main():
 env=dict(os.environ);env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
 results=[]
 def run(label,cmd,cwd,limit):
  r=subprocess.run(cmd,cwd=cwd,env=env,capture_output=True,text=True,encoding='utf-8',timeout=60)
  row={'id':label,'command':cmd,'cwd':str(cwd),'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'limit':limit};results.append(row);print(label,r.returncode,r.stdout[-300:].strip(),r.stderr[-200:].strip())
 def pytest_cmd(folder,temp):return [sys.executable,'-B','-X','utf8','-m','pytest','-c',str(folder/'pyproject.toml'),'--confcutdir',str(folder),'-o','addopts=','-p','no:cacheprovider','-q','code/tests/test_006_catalog_file.py','code/tests/test_006_epistemic_immune.py','--basetemp',str(OUT/temp)]
 run('current_pure_suites',pytest_cmd(PKG,'current_pure_tmp'),PKG,'Three toy and three catalog tests only; exact test source bodies read. Git object lookup local read-only.')
 run('current_worksheet',[sys.executable,'-B','-X','utf8','code/examiner_worksheet.py'],PKG,'Current unchanged worksheet should enforce the historical snapshot digest.')
 selected=['pyproject.toml','code/tests/test_006_catalog_file.py','code/tests/test_006_epistemic_immune.py','code/landau_worksheet.py','code/fixtures/pharmacy_catalog_52cb5457f6c4.json']
 dest=OUT/'historical_smoke';dest.mkdir(exist_ok=True);extract=[]
 archive=next(PKG.glob('*.zip'))
 with zipfile.ZipFile(archive) as z:
  root=z.namelist()[0].split('/')[0]
  for rel in selected:
   path=(dest/rel).resolve();assert path.is_relative_to(dest.resolve());b=z.read(root+'/'+rel);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b);assert sha(path.read_bytes())==sha(b);extract.append({'member':root+'/'+rel,'path':path.relative_to(ROOT).as_posix(),'sha256':sha(b)})
 run('historical_copy_pure_suites',pytest_cmd(dest,'historical_pure_tmp'),dest,'Fresh execution of five byte-identical selected historical ZIP members; no storage/native/model integration.')
 run('historical_copy_worksheet',[sys.executable,'-B','-X','utf8','code/landau_worksheet.py'],dest,'Fresh exact worksheet on original LF catalog; historical bytes copied unchanged under audit inspection directory.')
 run('current_isolated_storage',[sys.executable,'-B','-X','utf8',str(Path(__file__).resolve()),'isolated'],ROOT,'Eleven existing worked-example tests exercise fully read current sink/entry/error bodies with namespace initializers omitted and typing port replaced by object; not ordinary production import/integration or historical baseline replay.')
 current_catalog=json.loads((PKG/'code/fixtures/pharmacy_catalog_52cb5457f6c4.json').read_text(encoding='utf-8'));fixture=current_catalog['antibodies']['ab_q40_unterminated_string_syntax']['negative_fixture'];ast.parse(fixture)
 inputs=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in [PKG/'code/examiner_worksheet.py',PKG/'code/tests/test_006_catalog_file.py',PKG/'code/tests/test_006_epistemic_immune.py',PKG/'code/tests/test_006_worked_example.py',PKG/'paper.md',ROOT/'pfp/infrastructure/persistence/cemetery_sink.py',ROOT/'pfp/domain/entities/cemetery_entry.py',ROOT/'pfp/domain/exceptions.py']]
 write('_test_results.json',{'python':sys.version,'runs':results,'source_bindings':inputs,'archive_path':archive.relative_to(ROOT).as_posix(),'archive_sha256':sha(archive.read_bytes()),'historical_copy_members':extract,'catalog_syntax_control':{'entry':'ab_q40_unterminated_string_syntax','negative_fixture':fixture,'python_ast_parse':'passed','limit':'This displayed fixture is valid Python, not evidence of the named unterminated-string error; no fixture executed.'},'provider_calls':0,'native_builds':0,'private_storage_access':False,'production_writes':0})
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='isolated':raise SystemExit(isolated())
 main()
