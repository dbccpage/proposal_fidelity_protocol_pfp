"""Manifest-bounded source comparison; no seeds, hidden case data or dependencies read."""
import collections,difflib,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'pilots/anomalon_woland';OUT=Path(__file__).with_name('shared_runtime_inventory.json')
roots=['c051_exact_lp_solver_with_duals','c052_maxflow_mincut_certificates','c053_bareiss_fraction_free_matrix_inversion','c054_exact_linear_systems','c055_assignment_with_potentials','c059_sql_null_total_query_synthesis','challenge_suite','judge_packet_audit','certified_ladder','replay_runners','cot_miner.py','pilot_reply_kit.py','sqlite_pilot_store.py','offline_evaluator.py','live_evaluator.py']
manifest=json.loads((ROOT/'dag/migrations/anomalon_pilots_move.json').read_text(encoding='utf-8'))
index=json.loads((ROOT/'dag/file_inventory.json').read_text(encoding='utf-8'))['files']
def normalize(text):
    return text.replace('omega_engine_adversary','omega_engine_woland').replace('_ic/darpa/adversary','_ic/darpa/woland').replace('_adversary','_woland')
def eligible(e):
    p=Path(e['path']);s=p.as_posix().lower()
    return p.suffix in ('.py','.md','.yaml','.toml') and not any(x in s for x in ['seed','private','host-inputs','node_modules','site-packages','/cases/','hostile_mutations'])
rows=[]
for root in roots:
    entries=[e for e in manifest['entries'] if e['path']==root or e['path'].startswith(root+'/')];tracked=[e for e in entries if e['source_git_tracked']];extras=[e for e in entries if not e['source_git_tracked']]
    row={'id':root,'tracked_count':len(tracked),'extras_count':len(extras),'tracked_paths':[e['path'] for e in tracked],
      'unread_tracked_data':[e['path'] for e in tracked if not eligible(e)],'extras_categories':dict(collections.Counter('bytecode_cache' if '__pycache__' in e['path'] or Path(e['path']).suffix=='.pyc' else 'runtime_local_extra_unread' for e in extras)),'sources':[]}
    for e in tracked:
        if not eligible(e):continue
        p=BASE/e['path'];raw=p.read_bytes();txt=raw.decode('utf-8');digest=hashlib.sha256(raw).hexdigest();assert digest==e['sha256'],e['path']
        suffix=e['path']
        candidates=[x['path'] for x in index if x['path'].endswith('/'+suffix) and not x['path'].startswith('pilots/anomalon_woland/')]
        # Root files use the library owner rather than task-local copies.
        if '/' not in suffix:candidates=[x for x in candidates if x.startswith('workflows/library/pilot_estate/')]
        item={'path':p.relative_to(ROOT).as_posix(),'sha256':digest,'lines':[1,len(txt.splitlines())],'manifest_sha256_verified':True,'canonical_matches':[]}
        for target in candidates:
            q=ROOT/target
            if not q.is_file():continue
            qr=q.read_bytes();qt=qr.decode('utf-8');match={'path':target,'sha256':hashlib.sha256(qr).hexdigest(),'lines':[1,len(qt.splitlines())],'byte_identical':raw==qr,
              'namespace_only_difference':normalize(txt)==normalize(qt),'diff':'\n'.join(difflib.unified_diff(qt.splitlines(),txt.splitlines(),fromfile=target,tofile=item['path'],n=1))}
            item['canonical_matches'].append(match)
        row['sources'].append(item)
    rows.append(row)
OUT.write_text(json.dumps(rows,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for row in rows:
    print(row['id'], 'tracked',row['tracked_count'],'extras',row['extras_count'],'source files',len(row['sources']), 'unmatched',[Path(s['path']).name for s in row['sources'] if not s['canonical_matches']])
    for s in row['sources']:
        for m in s['canonical_matches']:
            if not m['namespace_only_difference']:print('NON_NAMESPACE_DIFF',s['path'],len(m['diff']))
