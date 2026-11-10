"""Resolve OS-temp obstruction inside the review workspace, preserving first logs."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'dag/reviews/paper_010_support_inspection'
temp = OUT/'local_temp'
temp.mkdir(exist_ok=True)
code = ('import tempfile;from pathlib import Path;'
        f'tempfile.tempdir={str(temp)!r};'
        'import dag.reviews.additional_paper_010_validate as v;'
        "v.BASE=v.OUT/'archive';v.OUT=v.OUT/'archive_test_localtemp';v.OUT.mkdir(exist_ok=True);"
        'raise SystemExit(v.tests())')
done = subprocess.run([sys.executable,'-X','utf8=0','-c',code],cwd=ROOT,capture_output=True,timeout=60)
log = OUT/'archive_tests_localtemp.txt'
log.write_bytes(done.stdout+b'\nSTDERR\n'+done.stderr)
records = [{'kind':'archive_tests_workspace_temp','returncode':done.returncode,'log':log.relative_to(ROOT).as_posix()}]
for edition, base in [('archive',OUT/'archive'),('current',ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots')]:
    capstone = subprocess.run([sys.executable,'-X','utf8',str(base/'tools/study_capstone.py')],cwd=base,capture_output=True,timeout=60)
    path = OUT/f'{edition}_capstone.txt'
    path.write_bytes(capstone.stdout+b'\nSTDERR\n'+capstone.stderr)
    records.append({'kind':edition+'_capstone','returncode':capstone.returncode,'log':path.relative_to(ROOT).as_posix()})
result = {'checks':records,'limits':'Archive renderer test may invoke local Pandoc and uses a retained fake XeLaTeX batch executable. No real XeLaTeX/Lean/providers or source regeneration. First OS-temp failure preserved separately.'}
(ROOT/'dag/reviews/additional_paper_010_archive_replay.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
