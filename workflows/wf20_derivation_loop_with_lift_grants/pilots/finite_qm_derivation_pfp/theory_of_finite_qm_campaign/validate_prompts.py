"""Structural and provenance audit; this does not prove any mathematical target."""
from pathlib import Path as _FilesystemPath
import sys as _contract_sys
_contract_sys.path.insert(0, str(_FilesystemPath(__file__).resolve().parents[2] / "scripts"))
from contract_scores import RecordPath as Path
import hashlib
import json
import re
import yaml
_contract_sys.path.insert(0, str(_FilesystemPath(__file__).resolve().parent))
from custody import Custody

ROOT=Path(__file__).resolve().parents[2]
LOADER=getattr(yaml,'CSafeLoader',yaml.SafeLoader)


def load_yaml(data):
    return yaml.load(data,Loader=LOADER)
REJECT=re.compile(r'stage_route_shadow_invariant|quotient_reduced_countermodel_defect|Set cochain_d1_d0_exact_zero|Set should_continue|exact 18 keys|which equals|raw_candidate_rival_int|countermodel_expected_int|P\* Cycle C_4')


def has_legacy_contract(user_prompt: str, source_statement: str) -> bool:
    """Scan instructions, excluding one verbatim, unaccepted source-claim quote.

    Ordinary mathematical prose in the quoted target is not an answer contract.
    A second occurrence or an instruction outside that quote is still checked.
    """
    quoted = 'Research target (source claim; verify its scope before reuse):\n' + source_statement + '\n\n'
    # Only an entire, explicitly delimited target block is a source quote.
    instructions = '\n' + user_prompt
    if source_statement:
        instructions = instructions.replace('\n' + quoted, '', 1)
    return REJECT.search(instructions) is not None


def check_presentation(presentation):
    """Check declared arities/colours/graft slots; no semantic or coherence verdict."""
    errors=[]
    colours={c['id'] for c in presentation['colours']}
    generators={g['id']:g for g in presentation['generators']}
    relations={r['id'] for r in presentation['relations']}
    if len(generators)!=len(presentation['generators']): errors.append('duplicate generator')
    for generator in generators.values():
        if generator['arity']!=len(generator['ordered_inputs']): errors.append('arity mismatch')
        if not set(generator['ordered_inputs']+[generator['output']])<=colours: errors.append('unknown colour')
    def graft(outer,slot,inner):
        left,out=outer;right,received=inner
        if type(slot) is not int or not 0<=slot<len(left): raise ValueError('invalid graft slot')
        if left[slot]!=received: raise ValueError('graft colour mismatch')
        return left[:slot]+right+left[slot+1:],out
    def signature(tree):
        if isinstance(tree,str):
            g=generators[tree]
            return list(g['ordered_inputs']),g['output']
        return graft(signature(tree['outer']),tree['slot'],signature(tree['inner']))
    for composition in presentation['compositions']:
        try:
            graft(signature(composition['outer_operation']),composition['input_slot'],signature(composition['inner_operation']))
            if not set(composition['licensing_relations'])<=relations: errors.append('unknown licensing relation')
        except (KeyError,ValueError) as error: errors.append(str(error))
    for plan in presentation.get('composition_plans',[]):
        try:
            inputs,output=signature(plan['tree'])
            if inputs!=plan['ordered_inputs'] or output!=plan['output']: errors.append('composition plan signature mismatch')
        except (KeyError,ValueError) as error: errors.append(str(error))
    return errors


EXTENSION='dag/pfp/prompt_audit_extension.json'
EXTENSION_SCHEMA='omega.pfp.finite-qm.prompt-audit-extension.v1'


def load_extension(root,base_digest):
    """Rows of the generated-prompt audit extension; the sealed audit is never edited.

    Returns (rows keyed by node, errors). A missing extension is an empty one.
    """
    path=root/EXTENSION
    if not path.is_file(): return {},[]
    errors=[]
    extension=json.loads(path.read_bytes())
    if extension.get('schema_id')!=EXTENSION_SCHEMA or extension.get('authority_effect')!='None': errors.append('audit extension: schema')
    if extension.get('base_audit_sha256')!=base_digest: errors.append('audit extension: not bound to the sealed audit')
    rows={}
    for row in extension.get('nodes',[]):
        if row['node_id'] in rows: errors.append(row['node_id']+': duplicate extension row')
        rows[row['node_id']]=row
    if extension.get('prompts_reviewed')!=len(rows): errors.append('audit extension: count mismatch')
    return rows,errors


def validate(root=ROOT):
    root=Path(root)
    errors=[]
    files=sorted((root/'dag/prompts').glob('*.yaml'))
    index=json.loads((root/'dag/operads/index.json').read_text(encoding='utf-8'))
    indexed={row['node_id'] for row in index['nodes']}
    if len(indexed)!=len(index['nodes']): errors.append('duplicate index row')
    audit_path=root/'dag/pfp/prompt_audit.json'
    audit=json.loads(audit_path.read_text(encoding='utf-8'))
    audited={row['node_id']:row for row in audit['nodes']}
    if audit['prompts_reviewed']!=len(audit['nodes']) or len(audited)!=len(audit['nodes']): errors.append('sealed audit count mismatch')
    extended,extension_errors=load_extension(root,hashlib.sha256(audit_path.read_bytes()).hexdigest())
    errors.extend(extension_errors)
    if set(extended)&set(audited): errors.append('extension repeats a sealed audit node')
    expected=len(audited)+len(extended)
    try:
        custody=Custody(root)
    except (ValueError,KeyError,TypeError,OSError) as error:
        return {'prompts':len(files),'collections':len(indexed),'errors':['filename custody invalid: '+str(error)],'claim':'Custody failure; no mathematical acceptance.'}
    seen=set()
    for path in files:
        prompt=load_yaml(path.read_bytes())
        node=prompt['node_id']
        generated=node in extended
        if node in seen: errors.append(node+': duplicate node')
        seen.add(node)
        if prompt.get('default_stage')!='P0_MINE_OPERAD': errors.append(node+': entry stage')
        if prompt.get('authority_effect')!='None': errors.append(node+': authority')
        if 'response_schema' in prompt or 'user_prompt_without_m3_ablation' in prompt: errors.append(node+': legacy answer schema')
        for key in ('workflow','mode','stage_contracts','operad_record'):
            target=(path.parent/prompt[key]).resolve()
            if not target.is_file() or root.resolve() not in target.parents:
                errors.append(node+': broken or escaping '+key)
        record=load_yaml((path.parent/prompt['operad_record']).read_bytes())
        if has_legacy_contract(prompt['user_prompt'],record['target']['source_statement']):
            errors.append(node+': legacy fabricated contract')
        if record['node_id']!=node: errors.append(node+': wrong collection')
        if record['target']['source_statement'] not in prompt['user_prompt']: errors.append(node+': truncated target')
        if record['target']['statement_status']!='source_claim_to_scope_check_not_accepted_result': errors.append(node+': source status promoted')
        if record['collection_status']!='source_candidates_collected_semantic_mining_open': errors.append(node+': fabricated mining completion')
        for op in record['operation_candidates']:
            if not op.get('signature_excerpt') or not op.get('source_sha256') or op.get('status')!='source_candidate_requires_semantic_review':
                errors.append(node+': unsupported source candidate')
        errors.extend(node+': '+e for e in check_presentation(record['presentation']))
        for binding in record['source_bindings']:
            if binding['availability']=='local':
                p=root/binding['path']
                if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=binding['sha256']:
                    errors.append(node+': local source pin changed '+binding['path'])
        for pin in record['target'].get('paper_source_pins',[]):
            if generated:
                # Generated pins are current digests: they never enter the sealed filename-custody ledger.
                source=root/pin['path']
                if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=pin['sha256']:
                    errors.append(node+': local paper source pin changed '+pin['path'])
            elif not custody.matches('paper',pin['path'],pin['sha256'],node):
                errors.append(node+': local paper source pin changed '+pin['path'])
        row=extended[node] if generated else audited.get(node,{})
        if generated and (row.get('prompt')!=path.relative_to(root).as_posix() or row.get('operad_collection')!=(path.parent/prompt['operad_record']).resolve().relative_to(root.resolve()).as_posix()):
            errors.append(node+': extension row path mismatch')
        if not custody.matches('prompt',path.relative_to(root).as_posix(),row.get('after_sha256'),node): errors.append(node+': audit hash mismatch')
    if len(files)!=expected or seen!=indexed or seen!=set(audited)|set(extended): errors.append('corpus identity mismatch')
    try:
        custody.finish()
    except ValueError as error:
        errors.append(str(error))
    workflow=load_yaml((root/'dag/pfp/workflow.yaml').read_bytes())
    if workflow['entry_stage']!='P0_MINE_OPERAD': errors.append('workflow entry')
    if [s['id'] for s in workflow['stages']]!=['P0_MINE_OPERAD','P1_DERIVE','P2_VERIFY','P3_REPAIR','P4_CHALLENGE','P5_RECORD']:
        errors.append('stage sequence')
    if any('operad_delta' not in s['output'] for s in workflow['stages']): errors.append('missing per-stage collection')
    return {'prompts':len(files),'collections':len(indexed),'errors':errors,'claim':'Structural and local-source custody checks only; no operad or target theorem acceptance.'}


if __name__=='__main__':
    result=validate()
    print(json.dumps(result,indent=2))
    raise SystemExit(bool(result['errors']))
