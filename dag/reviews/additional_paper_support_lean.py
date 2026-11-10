"""Compile only reviewed Lean sources in an audit-owned copy; never fetch dependencies."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'dag/reviews/additional_paper_support_build'
DEST.mkdir(exist_ok=True)
LEAN=Path.home()/'.elan/bin/lean.exe'
sources=[('papers/non_pfp/002_l1_obstruction_framework/lean4',f) for f in ['lp_cochains.lean','lp_weak_duality.lean','lp_strict_convexity.lean','lp_hodge_helmholtz.lean','lp_general_certificate.lean','lp_core.lean']]
sources += [('papers/non_pfp/014_finite_authority_and_non_terminal_computation/lean4','FiniteAuthority.lean'),('papers/non_pfp/016_the_anomalon_boundary/lean4','FiniteBoundary.lean')]
report={'source_commit':'8050c66900899771766f33e8f5fdd200b7dd9120','toolchain':'leanprover/lean4:v4.35.0','scope':'Individually compiled reviewed source files in audit-owned copies; not full package builds. No network dependency installation.','results':[]}
env=dict(os.environ,LEAN_PATH=str(DEST))
for directory,name in sources:
    src=ROOT/directory/name
    dst=DEST/name
    shutil.copyfile(src,dst)
    cmd=[str(LEAN),'+leanprover/lean4:v4.35.0','-o',str(dst.with_suffix('.olean')),str(dst)]
    proc=subprocess.run(cmd,cwd=DEST,env=env,capture_output=True,text=True,timeout=90)
    report['results'].append({'path':src.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr})
    (ROOT/'dag/reviews/additional_paper_support_lean_results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(name,proc.returncode,flush=True)
