"""Emit exact public paper-support ranges and log emission, not reading credit."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'papers/pfp/010_pfp_holonomy_checks_and_model_pilots'
LOG = ROOT/'dag/reviews/additional_paper_010_emissions.json'
records = json.loads(LOG.read_text()) if LOG.exists() else []
for argument in sys.argv[1:]:
    name, _, interval = argument.partition('@')
    path = (BASE/name).resolve()
    assert path.is_relative_to(BASE.resolve()) and path.is_file()
    raw = path.read_bytes(); lines = raw.decode('utf-8-sig').splitlines()
    lower, upper = (map(int, interval.split(':')) if interval else (1, len(lines)))
    assert 1 <= lower <= upper + 1 and upper <= len(lines)
    print(f'FILE {path.relative_to(ROOT).as_posix()} lines {lower}-{upper} of {len(lines)}')
    for index in range(lower - 1, upper):
        print(f'{index+1}: {lines[index]}')
    records.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
                    'emitted_lines':[lower,upper], 'total_lines':len(lines),
                    'limit':'Emission log only; semantic review and tool-output completeness require separate assessment.'})
LOG.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
