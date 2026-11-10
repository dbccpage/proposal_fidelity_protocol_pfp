"""Static tracked-public-text reference census for proposed education moves."""
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREFIX='education_demo_classification'
rows=json.loads((HERE/(PREFIX+'_draft_rows.json')).read_text(encoding='utf-8'))
moves=[r for r in rows if r['disposition']=='move']
names=collections.defaultdict(list)
for row in moves:
    if Path(row['path']).name in {'README.md','__init__.py','conftest.py','validation_report.md','validation_receipt.json'}:
        names[row['path']].append(row['path'])
    else:
        names[Path(row['path']).name].append(row['path'])
    if row['path'].endswith('.py') and Path(row['path']).stem not in {'__init__','conftest'}:
        names[Path(row['path']).stem].append(row['path'])
pattern=re.compile('|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True)))
refs=[]; scanned=0; excluded=collections.Counter()
extensions={'.py','.md','.rst','.txt','.yaml','.yml','.json','.toml','.ini','.cfg','.ps1','.sh','.js','.cjs','.mjs','.ts','.rs','.lean','.ipynb','.html'}
for p in subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines():
    parts=Path(p).parts
    if any(v.startswith('.') for v in parts) or p.startswith('dag/benchmark/') or '.benchmark_private' in p or p.startswith('dag/migrations/education_demo_classification'):
        excluded['private_hidden_benchmark_or_own_report']+=1; continue
    if p.startswith(('dag/','pilots/anomalon_woland/')):
        excluded['historical_custody_or_large_imported_corpus_not_consumer_scan']+=1; continue
    if Path(p).suffix not in extensions: excluded['non_text_suffix']+=1; continue
    fp=ROOT/p
    if not fp.is_file(): excluded['absent_current_worktree']+=1; continue
    raw=fp.read_bytes()
    if len(raw)>4_000_000: excluded['over_4mb']+=1; continue
    try: text=raw.decode('utf-8-sig')
    except UnicodeDecodeError: excluded['binary_decode']+=1;continue
    scanned+=1
    if not any(n in text for n in names): continue
    found=[]
    for i,line in enumerate(text.splitlines(),1):
        hits=set(m.group() for m in pattern.finditer(line))
        if not hits: continue
        targets=set(t for h in hits for t in names[h])
        # Common file names alone are too ambiguous for an inferred dependency.
        if all(Path(t).name in {'README.md','__init__.py','conftest.py','validation_report.md','validation_receipt.json'} for t in targets) and not any(k in line for k in ['_how_to_play','v4_operad','004_oepfp','008_oeop','009_oeeis','010_oepciv']): continue
        targets={t for t in targets if t!=p}
        if not targets:continue
        found.append({'line':i,'text':line[:1200],'targets':sorted(targets),'match_kind':'static_literal_or_module_name_candidate'})
    if found:
        role='historical_audit_or_migration_custody' if p.startswith(('dag/reviews/','dag/migrations/','dag/pilot_triage/')) else 'runtime_or_build_consumer' if Path(p).suffix in {'.py','.rs','.js','.cjs','.mjs','.ts','.toml','.cfg','.ini','.sh','.ps1'} else 'notebook_consumer' if p.endswith('.ipynb') else 'documentation_or_configuration_consumer'
        refs.append({'id':f'EDREF-{len(refs)+1:04d}','path':p,'sha256':hashlib.sha256(raw).hexdigest(),'role':role,'occurrences':found})
out={'method':'Literal basename/module-name candidates, not proof of dynamic import resolution. Tracked public allowed text <=4MB; hidden directories, entire dag/, large incoming pilots/anomalon_woland custody corpus and private material excluded. Historical receipts must retain old source paths and hashes, with a migration map instead of in-place rewriting. Generic basename matches require manual disambiguation.','scanned_files':scanned,'excluded_counts':dict(excluded),'consumers':refs}
(HERE/(PREFIX+'_references_scoped.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('scanned',scanned,'consumers',len(refs),'roles',dict(collections.Counter(r['role'] for r in refs)))
for r in refs:
    if r['role']=='runtime_or_build_consumer':
        print(r['path'],[(x['line'],x['text'][:180]) for x in r['occurrences'][:8]])
