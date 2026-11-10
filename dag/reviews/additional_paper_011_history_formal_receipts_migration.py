import sys,json,zipfile,re,collections
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_data as d
a=d.a;P=d.PAPER
replacements=[('omega_engine_atlas','atlas'),('omega_engine_symbol_game','symbol_game'),('omega_ooutwire_primitives','core_ooutwire_primitives'),('omega_kernel','core_kernel'),('omega_engine','engine'),('libomega_','libcore_'),('omega_mub','core_mub'),('Lean.Omega.','Lean.Core.'),('symbol_game/011_','pfp/011_'),('symbol_game\\011_','pfp\\011_'),('symbol_game\\\\011_','pfp\\\\011_')]
def norm(b):
    t=b.decode('utf8').replace('\r\n','\n')
    for old,new in replacements:t=t.replace(old,new)
    return t
results=[]
with zipfile.ZipFile(a.ROOT/(P+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip')) as z:
    for r in a.read('_archive_comparison.json')['files']:
        p=r['path'];old=z.read(r['member']);new=d.RAW[p]
        try:
            matched=norm(old)==norm(new)
            info={'path':p,'current_sha256':d.digest(new),'zip_member':r['member'],'original_sha256':d.digest(old),'normalized_equal':matched,'old_replacement_occurrences':{x:old.decode('utf8').count(x) for x,_ in replacements if x in old.decode('utf8')}}
            if not matched:
                info['limit']='Not explained by the declared normalization; no semantic equivalence inferred.'
        except UnicodeDecodeError:info={'path':p,'current_sha256':d.digest(new),'original_sha256':d.digest(old),'binary_byte_equal':new==old}
        results.append(info)
a.write('_migration_reconciliation.json',{'method':'Comparison only: fixed explicit path/crate/printed-symbol substitutions plus CRLF normalization applied in memory to both representations. Nothing changed on disk. Normalization equality is not raw custody equality or proof-symbol validity.','replacements':replacements,'files':results})
autos=a.read('_automated.json');by={r['path']:r for r in autos}
for r in results:
    if r['path'] in by:
        by[r['path']]['checks']=[c for c in by[r['path']]['checks'] if c['rule']!='migration_representation_comparison']
        by[r['path']]['checks'].append(d.check('migration_representation_comparison','observed',**r))
a.write('_automated.json',autos)
print(json.dumps({'normalized_equal':sum(r.get('normalized_equal',False) for r in results),'binary_equal':sum(r.get('binary_byte_equal',False) for r in results),'unexplained':[r['path'] for r in results if not(r.get('normalized_equal') or r.get('binary_byte_equal'))]},indent=2))
