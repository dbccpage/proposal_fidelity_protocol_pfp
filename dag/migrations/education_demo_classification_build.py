"""Prepare a reviewable education relocation classification, without moving sources."""
import collections
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PREFIX='education_demo_classification'
data=json.loads((HERE/(PREFIX+'_inventory.json')).read_text(encoding='utf-8'))
how='education/004_oepfp/_how_to_play/'
scenes='education/004_oepfp/curriculum/scenes/'
scene_names={'antimorphism.py','collapse_manifold.py','eight_stages.py','homoglyph_allowlist.py','naked_prompt_launder.py','seal_packet.py','three_cycle_phi1.py'}
runbooks={'13_review_findings_and_pilot_runbook.md','16_numbered_prompt_roles_and_po035_play.md','17_runtime_ownership_and_replay.md','18_original_challenge_play.md','19_bounded_mechanism_sessions.md','20_acsets_dpo_and_optional_backends.md','22_unified_pfp_v4_operad_workflow_and_hacks.md'}

def classify(r):
    p=r['path']; name=Path(p).name
    if p.startswith('education/004_oepfp/levels/') and 'findings' in name:
        return 'historical_challenge_findings','move','pilots/education/challenge_findings/'+name,'Historical model/challenge result report or empirical findings hub, with explicit correction/withdrawal notices and missing-evidence caveats. Its level_ prefix does not make it an ordinary lesson. Preserve the complete record; do not infer scientific validity or delete Atlas near-copies.'
    if p.startswith(how+'v4_operad_container_and_p_star_loop/'):
        return 'finite_qm_workflow_evidence','move','pilots/education/finite_qm_workflow/'+p.split('v4_operad_container_and_p_star_loop/',1)[1], 'Finite-QM prompt/runbook and historical validation/ablation evidence form a concrete worked workflow bundle; this is not a new sealed task or an efficacy certificate.'
    if p.startswith(how) and (r['suffix'] in {'.py','.ipynb'} or '/assets/' in p):
        return 'local_triangle_game_demo','move','pilots/education/symbol_game/'+p[len(how):], 'Executable local triangle game, notebook producer/consumer, companion scenario/exam tests or directly linked game diagrams; preserve the toy-runtime evidence ceiling and local dependency unit.'
    if '/code/' in p and p.split('/')[1] in {'008_oeop','009_oeeis','010_oepciv'}:
        tag={'008_oeop':'operad_simulation','009_oeeis':'eis_simulation','010_oepciv':'pciv_simulation'}[p.split('/')[1]]
        return tag,'move','pilots/education/'+tag+'/code/'+p.split('/code/',1)[1], 'Standalone educational simulation package and its tests. Its models are bounded/synthetic companions, not production owners or evidence of learned efficacy; retain source and negative-test context together.'
    if p.startswith(scenes) and (name in scene_names or '/_render/' in p):
        return 'track_a_demo_and_captures','move','pilots/education/track_a/scenes/'+p[len(scenes):], 'Track A finite host/codec/schema/filter demonstration, rendering owner, captured provider reply or directly produced video. Keep the captured bytes and renderer together; do not rerun providers or render media during migration.'
    if (p.startswith('education/004_oepfp/docs/') and name in runbooks) or p==how+'13_practical_pfp_and_discovery.md':
        return 'pilot_execution_runbook','move','pilots/education/runbooks/'+name, 'Execution/replay guide for concrete pilot or demo mechanisms and their historical findings; keep curriculum links pointing to this operational companion and preserve dated claims.'
    if '/curriculum/' in p:
        if '/media/' in p or ('/scenes/' in p and r['suffix']!='.py'):
            return 'curriculum_media','retain',None,'Lesson illustration, narration/caption/audio asset, or generated text-render cache belonging to retained curriculum. It is not a model-trial result; binary media was not rendered or listened to.'
        if r['suffix']=='.ipynb':
            return 'curriculum_notebook','retain',None,'Numbered lesson or system-integration practicum in an explicit curriculum sequence. Code cells teach bounded examples; demonstrations inside a lesson do not make the entire lesson an independent pilot campaign. Preserve embedded historical output and any missing-owner caveat.'
        if r['suffix']=='.json':
            return 'curriculum_inventory_or_validation','retain',None,'Manifest, research reading inventory or historical curriculum execution/review receipt. This documents curriculum custody and is not raw provider experiment evidence; recorded passing status is not freshly validated.'
        if r['suffix']=='.py':
            return 'curriculum_animation_owner','retain',None,'Manim lesson storyboard or curriculum media verifier; intended output is a teaching illustration, not a task/arm/judge experiment. Existing application references require separate repair, not speculative relocation.'
        return 'curriculum_prose','retain',None,'Lesson concept, narration script, track syllabus or curriculum index bound to the retained lesson sequence. Cross-links to demos are navigation, not ownership of their results.'
    if '/_images/' in p:
        return 'reference_diagram','retain',None,'Conceptual/architectural diagram and its guide, used by the reference curriculum; no independent pilot execution or result custody established.'
    if '/lean4/' in p:
        return 'formal_teaching_reference','retain',None,'Lean teaching model/build metadata supports the curriculum propositions. It is not a provider pilot and does not certify the separate simulation implementation.'
    if '/grammar/' in p:
        return 'grammar_reference_and_conformance','retain',None,'Grammar definitions, conformance cases and their local checker/type support are specification/reference infrastructure rather than a pilot campaign.'
    if p.startswith(how+'contracts/'):
        return 'archival_game_contract_reference','retain',None,'Declarative historical mode/stage contract reference preserved by the player syllabus; not a newly runnable experiment or current runtime capability guarantee.'
    if p.startswith(how):
        return 'player_curriculum_reference','retain',None,'Player manual, exam, mathematical rules or historical edition reference; retain teaching text and update its links to relocated runnable examples.'
    return 'ordinary_reference_curriculum','retain',None,'Architecture, mathematics, normal-form specification, level lesson, atlas/encyclopedia, or navigation reference. Mentioning demos/pilots does not turn this source into their runnable owner or raw evidence.'

rows=[]
ledger=json.loads((HERE/(PREFIX+'_read_ledger.json')).read_text(encoding='utf-8'))
for r in data['files']:
    p=r['path']; raw=(ROOT/p).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==r['sha256'],p
    group,disposition,dest,reason=classify(r)
    ranges=[q['reviewed_lines'] for q in ledger if q['path']==p and q['sha256']==r['sha256']]
    covered=set(i for a,b in ranges for i in range(a,b+1)); full=r.get('line_count',0)>0 and covered==set(range(1,r['line_count']+1))
    review='full_text_body' if full else 'selected_body_plus_static_inventory' if ranges else 'automated_content_inventory_with_group_semantic_review'
    content={'headings':r.get('headings',[]), 'opening_lines':r.get('first_nonempty',[]), 'definition_names':[d['name'] for d in r.get('definitions',[])], 'imports':r.get('imports',[])}
    if r['content_kind']=='binary_unrendered': review='binary_hash_and_owner_reference_only'; content={}
    if r['suffix']=='.ipynb':
        cs=r['notebook_cells']; content={'cells':len(cs),'code_cells':sum(c['type']=='code' for c in cs),'code_lines':sum(c['source_lines'] for c in cs if c['type']=='code'),'stored_output_cells':sum(bool(c['outputs']) for c in cs),'source_cell_hashes':[c['source_sha256'] for c in cs]}; review='all_cells_parsed_static_content_classification_not_full_manual_cell_review'
    if r['suffix']=='.json': content['json_shape']=r.get('json_shape'); review='full_text_body' if full else 'parsed_json_shape_and_role_classification'
    if r['suffix']=='.svg':
        try:
            tree=ET.fromstring(raw); content={'xml_root':tree.tag,'labels':[''.join(e.itertext()) for e in tree.iter() if e.tag.split('}')[-1] in {'title','desc','text'}]}; review='parsed_svg_labels_and_owner_references_not_visual_review'
        except ET.ParseError as e: content={'parse_error':str(e)}
    rows.append({'path':p,'sha256':r['sha256'],'bytes':r['bytes'],'line_count':r.get('line_count'),'group':group,'disposition':disposition,'proposed_destination':dest,'reason':reason,'review_depth':review,'full_source_read':full,'reviewed_lines':ranges,'content_evidence':content,'source_evidence':[{'path':p,'sha256':r['sha256'],'lines':[1,r.get('line_count',0)],'coverage':review}],'consumer_reference_ids':[]})

if __name__=='__main__':
    (HERE/(PREFIX+'_draft_rows.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('ROWS',len(rows),'DISPOSITIONS',dict(collections.Counter(r['disposition'] for r in rows)))
    print('GROUPS',dict(collections.Counter(r['group'] for r in rows)))
