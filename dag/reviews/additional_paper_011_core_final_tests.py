import sys,os,datetime,contextlib,io,ast
sys.dont_write_bytecode=True
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
import additional_paper_011_core_audit as a
code=a.ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/code'
temp=a.file('_final_test_temp_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'));temp.mkdir()
paths=[str(code/'tests/test_paper011_recreations.py'),str(code/'tests/test_paper011_native_mub.py')]
exclude={'test_paper011_aggregate_scope_contains_every_named_family','test_paper011_original_ast_data_uses_original_callback_without_controller_side_effects','test_paper011_original_ast_capture_refuses_executable_or_reinterpreted_fixture'}
test=code/'tests/test_paper011_aggregates.py'
paths += [str(test)+'::'+node.name for node in ast.parse(test.read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_') and node.name not in exclude]
paths += [str(code/'tests/test_paper011_history_recovery.py')+'::test_recovery_path_cannot_escape_paper']
paths += [str(code/'tests/test_paper011_original_recovery.py')+'::'+name for name in ['test_undeclared_top_level_side_effect_refused','test_unknown_sibling_import_refused','test_source_loader_refuses_corrupted_bytes_before_execution','test_existing_output_is_never_overwritten']]
config=a.file('_pytest.ini')
import pytest
out=io.StringIO()
with contextlib.redirect_stdout(out),contextlib.redirect_stderr(out):
    status=pytest.main(['-q','-c',str(config),'--noconftest','-p','no:cacheprovider','--basetemp',str(temp/'pytest'),*paths])
a.file('_final_pytest.txt').write_text(out.getvalue(),encoding='utf8')
a.write('_final_test_control.json',{'runtime':sys.executable,'python':sys.version,'status':'executed','pytest_exit_code':int(status),'selected_nodeids_or_modules':paths,'log':'dag/reviews/additional_paper_011_core_final_pytest.txt','log_sha256':a.sha(a.file('_final_pytest.txt')),'limits':'Read-vetted synthetic-only tests; original inventory/controller/trace/receipt tests excluded. Stubbed native processes only. No provider calls, historical/private data or native builds. Python3.14.2 available-runtime checks, not pinned3.12 reproduction.'})
print(out.getvalue())
