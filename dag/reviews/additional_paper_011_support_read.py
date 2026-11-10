"""Display public Paper011 support paths; record emissions, never reading credit."""
import hashlib
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence'
REV=ROOT/'dag/reviews'
scope={x['path'] for x in json.loads((REV/'additional_paper_011_support_scope.json').read_text())['files']}
log=REV/'additional_paper_011_support_emissions.json'
rows=json.loads(log.read_text()) if log.exists() else []
for argument in sys.argv[1:]:
    name,_,span=argument.partition('@')
    path=(BASE/name).resolve()
    assert path.is_relative_to(BASE.resolve()) and path.relative_to(ROOT).as_posix() in scope
    raw=path.read_bytes();lines=raw.decode('utf-8-sig').splitlines()
    first,last=map(int,span.split(':')) if span else (1,len(lines))
    assert 1<=first<=last+1 and last<=len(lines)
    print(f'FILE {name} lines {first}-{last} of {len(lines)}')
    for index in range(first-1,last): print(f'{index+1}: {lines[index]}')
    rows.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'emitted_lines':[first,last],'total_lines':len(lines),'limit':'Emission is not review credit; require untruncated reading and assessment.'})
log.write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
