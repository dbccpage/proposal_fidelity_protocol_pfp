"""Run unchanged public tests with a separate synthetic seed and denied network/real-seed access."""
import hashlib,json,os,pathlib,sys,platform
H=pathlib.Path(__file__).parent;R=H.parents[1]
original_seed=(H/'seed_prompt.txt').resolve()
def audit(event,args):
 if event=='open'and isinstance(args[0],(str,bytes,pathlib.Path))and pathlib.Path(args[0]).resolve()==original_seed:
  raise RuntimeError('REVIEW_FORBIDS_ACTUAL_SEED_ACCESS')
 if event.startswith('socket.'):raise RuntimeError('REVIEW_FORBIDS_NETWORK')
sys.addaudithook(audit);os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';sys.path.insert(0,str(H))
import reference_runner as rr
import live_campaign as lc
tag=sys.argv[1]if len(sys.argv)>1 else'initial';assert tag.isalnum()
box=H/('rational_panel_review_test_environment_'+tag);box.mkdir(exist_ok=False)
for name in rr.EXPERIMENTS['rational_blind_panel_v1']['source_pins']:
 (box/name).write_bytes((H/name).read_bytes())
seed=b'Public synthetic algebra control. No benchmark answer or actual seed.\n'
(box/'seed_prompt.txt').write_bytes(seed);(box/'commitment.json').write_text(json.dumps({'seed_sha256':rr.sha(seed)}))
rr.HERE=box;lc.HERE=box
import pytest
platform.node=lambda:'synthetic-review-no-hostname-query'
names=['test_rational_panel.py','test_rational_workflows.py','test_summarize_runs.py']
args=['--noconftest','-p','no:cacheprovider','-q',*[str(H/n)for n in names],'--junitxml='+str(H/('rational_panel_review_focused_tests_'+tag+'.xml'))]
exit_code=pytest.main(args)
receipt={'exit_code':int(exit_code),'arguments':args,'source_files':[{'path':(H/n).relative_to(R).as_posix(),'sha256':hashlib.sha256((H/n).read_bytes()).hexdigest()}for n in names+list(rr.EXPERIMENTS['rational_blind_panel_v1']['source_pins'])],'limits':'Unchanged test functions, redirected HERE to separate fabricated task and copied source pins; audit hook forbids real seed and sockets. JUnit platform.node replaced with synthetic fixed label so its local hostname query does not trip socket guard. Not original-seed validation or live provider performance; parent larger suite not counted.','initial_attempt':'All80 test bodies displayed success, but pytest session-finish JUnit tried socket.gethostname and review audit hook raised RuntimeError. Initial process failed before receipt completion; not counted as a passing suite. The second run avoids that local hostname query without relaxing network denial.'}
(H/('rational_panel_review_focused_tests_'+tag+'.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'exit_code':int(exit_code)}))
