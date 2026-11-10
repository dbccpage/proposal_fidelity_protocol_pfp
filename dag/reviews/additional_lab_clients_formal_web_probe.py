"""Bound an existing offline TestClient run that stalled in the full suite."""
import json
from pathlib import Path
import subprocess
import sys
cmd=[sys.executable,'-B','-X','utf8','-m','pytest','pfp_lab/tests/test_web.py',
     'pfp_lab/tests/test_pins.py','-q','-p','no:cacheprovider',
     '--basetemp=dag/reviews/additional_lab_clients_formal_web_tmp','--tb=short']
try:
    p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',timeout=30)
    result=dict(command=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
except subprocess.TimeoutExpired as e:
    result=dict(command=cmd,timeout_seconds=30,
                stdout=(e.stdout or b'').decode('utf-8'),stderr=(e.stderr or b'').decode('utf-8'))
Path('dag/reviews/additional_lab_clients_formal_web_run.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
