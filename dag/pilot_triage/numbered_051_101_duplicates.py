"""Rehash public candidate matches from original PFP inventory; never inspect secrets/seeds."""
from pathlib import Path
import collections,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
def allowed(p):
    s=p.as_posix().lower()
    return 'benchmark' not in s and not any(x in p.name.lower() for x in ('seed','private','key')) and '.git' not in p.parts
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inventory=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))
lookup=collections.defaultdict(list)
for item in inventory['files']:
    p=Path(item['path'])
    if allowed(p) and not p.as_posix().startswith('pilots/anomalon_woland/'):
        lookup[item['sha256']].append(p)
rows=[]
for i in range(51,102):
    folder=ROOT/f'pilots/anomalon_woland/pilot_{i:07d}';matches=[];scanned=0
    for p in sorted(folder.rglob('*')):
        if not p.is_file() or not allowed(p):continue
        scanned+=1; digest=sha(p)
        targets=[q.as_posix() for q in lookup[digest] if (ROOT/q).is_file() and sha(ROOT/q)==digest]
        if targets:matches.append({'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'matches':targets})
    rows.append({'pilot':i,'public_files_hashed':scanned,'matched_imported_files':len(matches),'matches':matches})
out=Path(__file__).with_name('numbered_051_101_duplicates.json');out.write_text(json.dumps(rows,indent=2)+'\n')
for row in rows:print(row['pilot'],'hashed',row['public_files_hashed'],'exact matches',row['matched_imported_files'])
