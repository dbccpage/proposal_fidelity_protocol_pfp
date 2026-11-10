"""Pinned public-source read ledger. Never loads benchmark or provider inputs."""
import ast,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
SCOPE=HERE/'additional_eis_pciv_remaining_scope.json'
LEDGER=HERE/'additional_eis_pciv_remaining_reads.json'
if not SCOPE.exists():
    coverage=json.loads((HERE/'coverage.json').read_text(encoding='utf-8'))
    rows=[x for x in coverage['files'] if x['path'].startswith(('eis/','pciv/')) and x['substantive_status']!='full_text_source_review_recorded']
    assert len(rows)==340
    SCOPE.write_text(json.dumps(dict(source_commit=coverage['source_commit'],files=rows),indent=2)+'\n',encoding='utf-8')
scope=json.loads(SCOPE.read_text(encoding='utf-8'))
allowed={x['path']:x for x in scope['files']}
records=json.loads(LEDGER.read_text(encoding='utf-8')) if LEDGER.exists() else []
for arg in sys.argv[1:]:
    path,*span=arg.split(':');assert path in allowed,path
    raw=(ROOT/path).read_bytes();digest=hashlib.sha256(raw).hexdigest();assert digest==allowed[path]['sha256'],path
    lines=raw.decode('utf-8').splitlines();bounds=[1,len(lines)] if not span else [int(x) for x in span[0].split('-')]
    assert not lines or 1<=bounds[0]<=bounds[1]<=len(lines)
    print('FILE',path,'SHA256',digest,'LINES',bounds,'TOTAL',len(lines))
    for n in range(bounds[0],bounds[1]+1):print(f'{n}: {lines[n-1]}')
    records.append(dict(path=path,sha256=digest,reviewed_lines=[bounds] if lines else [],full_source_read=not span,method='full_text_emitted' if not span else 'selected_text_emitted'))
LEDGER.write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
