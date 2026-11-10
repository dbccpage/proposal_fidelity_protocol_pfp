"""Prepare exact post-relocation navigation/path patches; never apply source edits.

Run before relocation. Parent first copies each source byte-for-byte, verifies its
custody hash, then may apply the separately reviewed patch and record post hashes.
Only this script's prefixed review artifacts are written.
"""
import collections
import base64
import difflib
import hashlib
import json
import posixpath
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREFIX='education_demo_classification'
rows=json.loads((HERE/(PREFIX+'_draft_rows.json')).read_text(encoding='utf-8'))
move={r['path']:r['proposed_destination'] for r in rows if r['disposition']=='move'}
tracked=set(subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines())
future={move.get(p,p) for p in tracked}
known={r['path']:r['sha256'] for r in rows}
link_re=re.compile(r'(?P<open>!?\[[^\]\n]*\]\()(?P<target>[^\s)]+)(?P<close>\))')
ref_link_re=re.compile(r'(?m)^(?P<open>\s*\[[^\]\n]+\]:\s*)(?P<target>[^\s]+)(?P<close>)')
changes=[]; issues=[]; repairs=[]

def sha(raw): return hashlib.sha256(raw).hexdigest()

def normalize_legacy(p):
    p=p.replace('education/documentation/','education/')
    p=p.replace('education/curriculum/3_the_symbol_game_proposal_fidelity_protocol_pfp/','education/004_oepfp/curriculum/')
    p=p.replace('education/curriculum/004_oepfp/','education/004_oepfp/curriculum/')
    p=p.replace('education/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_how_to_play_the_symbol_game/','education/004_oepfp/_how_to_play/')
    p=p.replace('education/3_the_symbol_game_proposal_fidelity_protocol_pfp/2_how_to_play_the_symbol_game/','education/004_oepfp/_how_to_play/')
    p=p.replace('education/notebooks/lessons/how_to_play/','education/004_oepfp/_how_to_play/')
    return p

def resolve(source, target):
    raw=unquote(target.strip('<>')).replace('\\','/')
    body,sep,anchor=raw.partition('#')
    if not body or body.startswith(('https:','http:','mailto:','data:','plugin:')): return None
    if body.startswith('file:'):
        marker='/education/'
        if marker not in body:return None
        body='education/'+body.split(marker,1)[1]
    candidates=[normalize_legacy(posixpath.normpath(posixpath.join(posixpath.dirname(source),body))),normalize_legacy(body.lstrip('/'))]
    for c in list(candidates):
        while c.startswith('../'): c=c[3:]
        candidates.append(c)
    for c in candidates:
        if c in tracked:return c,(('#'+anchor) if sep else '')
    return None

def md_text(source, dest, text):
    def repl(m):
        hit=resolve(source,m['target'])
        if hit is None:return m.group(0)
        original,frag=hit; final=move.get(original,original)
        if original not in move and source not in move:return m.group(0)
        target=posixpath.relpath(final,posixpath.dirname(dest))+frag
        if target!=m['target']:
            repairs.append({'source':source,'destination':dest,'old_link':m['target'],'new_link':target,'resolved_before':original,'resolved_after':final})
        return m['open']+target+m['close']
    updated=ref_link_re.sub(repl,link_re.sub(repl,text))
    # Explicit current command/module references, excluding archival result JSON.
    # Replacements of complete paths are safe even in code fences; directory-only
    # mixed-tree references are deliberately left untouched.
    for old,new in move.items():
        for alias in [old,old.replace('education/','education/documentation/',1)]:
            updated=updated.replace(alias,new)
    if source.startswith('education/'):
        for name in ['naked_prompt_launder','three_cycle_phi1','homoglyph_allowlist','seal_packet','eight_stages','collapse_manifold','antimorphism']:
            updated=updated.replace('education.notebooks.scenes.'+name,'pilots.education.track_a.scenes.'+name)
            updated=updated.replace('notebooks/scenes/'+name+'.py','pilots/education/track_a/scenes/'+name+'.py')
    return updated

def code_text(source,text):
    # Four local game launchers currently contain retired education/documentation paths.
    if source.startswith('education/004_oepfp/_how_to_play/') and source.endswith(('.py','.ipynb')):
        text=text.replace('education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/0_how_to_play_the_symbol_game','pilots/education/symbol_game')
        text=text.replace('education/documentation/004_oepfp/_how_to_play','pilots/education/symbol_game')
    if source=='pfp/tests/test_consistency_teaching.py':
        text=text.replace('education.documentation.004_oepfp.curriculum.scenes.naked_prompt_launder','pilots.education.track_a.scenes.naked_prompt_launder')
    for old,new in move.items():
        # Exact complete source paths only; no broad prefix replacement of mixed trees.
        for alias in [old,old.replace('education/','education/documentation/',1)]:
            if source in {'pfp/tests/finite_qm_workflow/test_finite_qm_reference_workflow.py','workflows/wf19_failure_derived_rule_transfer/pilots/challenge_suite/protocol_collation.py'}:
                text=text.replace(alias,new)
    return text

extras=['pfp/tests/test_consistency_teaching.py','pfp/tests/finite_qm_workflow/test_finite_qm_reference_workflow.py','workflows/wf19_failure_derived_rule_transfer/pilots/challenge_suite/protocol_collation.py']
for source in [r['path'] for r in rows]+extras:
    fp=ROOT/source
    if not fp.is_file():continue
    raw=fp.read_bytes()
    if source in known: assert sha(raw)==known[source],source
    try:text=raw.decode('utf-8')
    except UnicodeDecodeError:continue
    dest=move.get(source,source); new=text
    if source.endswith('.ipynb'):
        nb=json.loads(text); changed=False
        for cell in nb.get('cells',[]):
            old=''.join(cell.get('source',[]))
            val=md_text(source,dest,old) if cell.get('cell_type')=='markdown' else code_text(source,old) if cell.get('cell_type')=='code' else old
            if old!=val:cell['source']=val.splitlines(keepends=True);changed=True
        if changed:
            new=json.dumps(nb,ensure_ascii=False,indent=1)+'\n'
            if '\r\n' in text:new=new.replace('\n','\r\n')
    elif source.endswith('.md'):
        new=md_text(source,dest,text)
    elif source.endswith('.py'):
        new=code_text(source,text)
        if source in move and '/_how_to_play/build_' in source:new=md_text(source,dest,new)
    if new!=text:
        after=new.encode('utf-8')
        patch=''.join(difflib.unified_diff(text.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+dest,tofile='b/'+dest))
        changes.append({'original_path':source,'post_move_path':dest,'original_sha256':sha(raw),'post_adaptation_sha256':sha(after),'original_bytes':len(raw),'post_adaptation_bytes':len(after),'after_bytes_base64':base64.b64encode(after).decode('ascii'),'preservation':'Original is first relocated unchanged and custody-verified; this is a separate explicit post-move adaptation. Notebook outputs are retained as parsed values, not reexecuted.','patch':patch})

# The scan distinguishes literal occurrence candidates from known dependency owners.
for source in [r['path'] for r in rows if r['disposition']=='move']:
    if source.endswith('build_ten_routes_notebook.py'):
        issues.append({'path':source,'kind':'preexisting_stale_generator','detail':'Generated bootstrap still imports basic_packet_demo from a retired education/documentation/.../papers path. Checked-in notebook already embeds its own packet checker. Do not regenerate or execute this builder as a migration check; synchronizing generator semantics is separate work.'})
    if '/scenes/' in source and source.endswith('.py'):
        issues.append({'path':source,'kind':'preserved_runtime_dependency','detail':'Same-depth move preserves parents[4] for five renderers; repository .git/pixi search remains first. three_cycle_phi1 has a preexisting parents[3] archive fallback defect. Native adversary imports, optional render tools and legacy bench/packetization paths are not validated or repaired by a byte relocation; run no renderer as migration validation.'})
out={'schema_version':1,'status':'prepared_not_applied','changes':changes,'navigation_repairs':repairs,'unresolved_or_preexisting':issues,'limits':['Markdown inline links and notebook Markdown-cell links are resolved against tracked paths, including declared legacy education aliases. Reference-style Markdown links, dynamic string construction and untracked consumers need separate review.','No runtime execution, generator execution, notebook execution, native build, provider call or media render was performed.','Do not rewrite historical dag/reviews, migration custody or stored receipt hashes. Preserve original archival hashes and record every post-adaptation hash separately.']}
(HERE/(PREFIX+'_adaptation_plan.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/(PREFIX+'_adaptations.patch')).write_text(''.join(c['patch'] for c in changes),encoding='utf-8')
print('adaptation files',len(changes),'navigation links',len(repairs),'unresolved known items',len(issues))
print('runtime patches',[c['post_move_path'] for c in changes if c['post_move_path'].endswith('.py')])
