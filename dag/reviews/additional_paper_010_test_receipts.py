"""Compare current and exact archived reviewed executable bodies offline."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'dag/reviews/paper_010_support_inspection'
records = []
for edition in ('current','archive'):
    code = 'import dag.reviews.additional_paper_010_validate as v;'
    if edition == 'archive':
        code += "v.BASE=v.OUT/'archive';v.OUT=v.OUT/'archive_test';v.OUT.mkdir(exist_ok=True);"
    code += 'raise SystemExit(v.tests())'
    command = [sys.executable,'-X','utf8=0','-c',code]
    done = subprocess.run(command,cwd=ROOT,capture_output=True,timeout=60)
    log = OUT/f'{edition}_tests.txt'
    log.write_bytes(done.stdout+b'\nSTDERR\n'+done.stderr)
    records.append({'edition':edition,'returncode':done.returncode,'command':command,
                    'log':log.relative_to(ROOT).as_posix(),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
                    'summary':done.stdout.decode(errors='replace').splitlines()[-1:]})
result = {'tests':records,'limits':'Fresh Python tests only. UTF-8 mode disabled to avoid known uncaptured-stdout recursive test branch; no Lean/provider/real Pandoc/XeLaTeX execution.'}
(ROOT/'dag/reviews/additional_paper_010_test_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
