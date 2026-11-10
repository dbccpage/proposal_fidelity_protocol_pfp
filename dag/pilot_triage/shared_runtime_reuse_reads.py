"""Reuse only previous source reads whose exact imported bytes still match."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).with_name('shared_runtime_reads.json')
inventory=json.loads(Path(__file__).with_name('shared_runtime_inventory.json').read_text())
allowed={s['path']:s for row in inventory for s in row['sources']}
reads=json.loads(OUT.read_text())
for name in ('numbered_000_050_reads.json','numbered_051_101_reads.json'):
    source=OUT.with_name(name)
    for row in json.loads(source.read_text()):
        matches=[p for p,s in allowed.items() if s['sha256']==row['sha256'] and (p==row['path'] or any(m['path']==row['path'] and m['byte_identical'] for m in s['canonical_matches']))]
        for path in matches:
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=row['sha256']:continue
            if any(r['path']==path and r['lines']==row['lines'] for r in reads):continue
            reads.append(dict(row,path=path,review_level='prior_hash_bound_source_read_reused',prior_read_path=row['path'],prior_read_ledger=source.relative_to(ROOT).as_posix(),prior_review_level=row['review_level']))
OUT.write_text(json.dumps(reads,indent=2)+'\n')
print('reused',sum(r['review_level']=='prior_hash_bound_source_read_reused' for r in reads))
