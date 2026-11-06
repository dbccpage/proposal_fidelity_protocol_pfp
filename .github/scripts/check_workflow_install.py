import argparse, hashlib, json, os, subprocess, sys, sysconfig, tempfile
from importlib.resources import files
from pathlib import Path

parser=argparse.ArgumentParser(description="Offline installed-wheel workflow smoke checks; no provider calls.")
parser.add_argument("--artifact-dir", type=Path)
parser.add_argument("--wheel", type=Path)
parser.add_argument("--report", type=Path)
parser.add_argument("--checkout", type=Path, help="Also check cold imports from this source checkout.")
args=parser.parse_args()
root=Path(tempfile.mkdtemp(prefix="installed-wf-",dir=args.artifact_dir))
import pfp
assert Path(pfp.__file__).resolve().is_relative_to(Path(sysconfig.get_paths()["purelib"]).resolve()), "Install a wheel in a clean environment; editable source cannot validate installed resources."
env={**os.environ,'CORE_CREDENTIAL_DISCOVERY':'off','PYTHONIOENCODING':'utf-8'}
env.pop('PYTHONPATH',None)
checks=[]
def run(label,args):
    done=subprocess.run(args,cwd=root,env=env,capture_output=True,text=True,encoding='utf-8')
    assert done.returncode==0,(label,done.stdout,done.stderr)
    checks.append({'name':label,'passed':True,'exit_status':done.returncode})
    return done

for i in range(1,6):
    module=f'pfp.workflows.wf{i:04}'
    run(f'WF{i} module help',[sys.executable,'-m',module,'--help'])
    run(f'WF{i} console help',[str(Path(sys.executable).parent/(f'pfp-wf{i}'+('.exe' if os.name=='nt' else ''))),'--help'])
    examples=root/f'examples/wf{i:04}'
    examples.mkdir(parents=True)
    for resource in files(module).joinpath('examples').iterdir():
        if resource.is_file() and resource.name.endswith('.json'):
            (examples/resource.name).write_bytes(resource.read_bytes())
    output=root/f'run{i}'
    task=examples/'integer_sum.task.json'
    cmd=[sys.executable,'-m',module]
    if i<4:
        run(f'WF{i} prepare outside checkout',cmd+['prepare',str(task),'--output',str(output)])
        if i==3:
            run('WF3 check mining fixture',cmd+['check-mining',str(output),str(examples/'mining.reply.fixture.json'),'--fixture'])
            reply=examples/'solver.reply.fixture.json'
        else:
            reply=examples/'integer_sum.reply.fixture.json'
        run(f'WF{i} check fixture',cmd+['check',str(output),str(reply),'--fixture'])
        before={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
        run(f'WF{i} replay outside checkout',cmd+['replay',str(output)])
        assert before=={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
    else:
        run(f'WF{i} prepare and snapshot outside checkout',cmd+['prepare','--task',str(task),'--output',str(output)])
        assert (output/'source_snapshot/manifest.json').is_file()
        assert not (output/'accounting.sqlite3').exists()
    checks[-1]['no_live_provider_calls']=True

if args.checkout:
    for number in range(1,6):
        done=subprocess.run([sys.executable,"-m",f"pfp.workflows.wf{number:04}","--help"],cwd=args.checkout,env=env,capture_output=True,text=True,encoding="utf-8")
        assert done.returncode==0,(number,done.stdout,done.stderr)
        checks.append({"name":f"WF{number} cold import from checkout with noneditable wheel","passed":True,"exit_status":0})
data={"kind":"INSTALLED_WHEEL_SMOKE_VALIDATION","installed_outside_checkout":True,"no_editable_install":True,"fresh_provider_calls":0,"fixture_origin":"HAND_AUTHORED_FIXTURE","checks":checks}
if args.wheel:
    data.update(wheel_sha256=hashlib.sha256(args.wheel.read_bytes()).hexdigest(),wheel_bytes=args.wheel.stat().st_size)
if args.report:
    args.report.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8",newline="\n")
print(json.dumps(data,indent=2))
