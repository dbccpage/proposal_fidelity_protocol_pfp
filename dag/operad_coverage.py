"""Operad coverage scan: where each operad concept appears across the PFP layers.

Counts files (and DAG nodes / archive claims) whose text names each concept, per layer:
workflow code and tests (WF1-WF5 in pfp/workflows, WF6-WF51 family classes in
pfp_core/workflow_families, other WFs in their folders; pilots and source snapshots
excluded), DAG derivation nodes, dag/derivations files, archive claims with their
review verdict, Lean 4 files, Rust source and test files, and Python test files.
Structural concepts (composition, associativity, unit, equivariance) count only in
files that also mention operads. A name match is a pointer to read, not evidence
that a law is checked. Prints a Markdown matrix; --json also dumps the file lists.

Run from the repository root: python dag/operad_coverage.py
AuthorityEffect: None.
"""
import re, json, glob, os, ast, sys
from collections import defaultdict
R=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(R)
SKIP=re.compile(r'/pilots/|source_snapshot|__pycache__')
OP=re.compile(r'operad|operand', re.I)
C={ # id: (label, regex, needs operad co-occurrence)
 'colour':('Colour typing of operations', r'OperadColour|operad_colour|compose_colour_signatures|ColourSignature|colou?red operad|source_colours', False),
 'compose':('Composition / substitution', r'compos(e|ition)|substitut|operation_tree|OperationTree|∘_i|circ_i', True),
 'assoc':('Associativity law', r'associativ', True),
 'unit':('Unit / identity law', r'unit law|identity law|left unit|right unit|neutral element|\bidentity\b', True),
 'equiv':('Symmetric / equivariance', r'equivarian|symmetric operad|\bPlanar\b|permutation action', True),
 'ddc':('DDC alphabet (E,R,C,I,Λ,D,M,T)', r'\bDDC\b|DdcOp|DdcLetter|ddc_letter|ddc_move|Discrete Deformation Calculus', False),
 'lift':('DDC lift licence (Λ)', r'lift[ _-]?(licen[cs]e|grant)|LiftGrant', False),
 'operand':('Registered operands / motifs', r'registered_operand|operand_ddc_motif|operand_carrier|obstruction_class|op_exact_cochain_coboundary_repair|op_f2_gauge_board|op_meron_surgery', False),
 'antibody':('Antibodies', r'antibod', False),
 'antiskill':('Anti-skills', r'anti[_-]skill|AntiSkill', False),
 'pharmacy':('Pharmacy failure classes', r'pharmacy|SELF_CERTIFICATION|FAKE_RECEIPT|CONCLUSION_PRELOAD|THEOREM_NAME_LAUNDERING', False),
 'twosig':('Two-signal guard dispositions', r'two[ _-]signal|TWO_SIGNAL|guard_disposition|DEFENSIVE_LOCKDOWN|danger_decision', False),
 'capab':('Typed capabilities / lifecycle', r'capability_kind|typed_capabilit|lifecycle_(admission|validation|declaration)|meta_skill_status', False),
 'sigfam':('Contractive meta-operads / X-to-Y verifiers', r'contractive_meta|x_to_y_verifier|meta-[a-z-]+-to-[a-z-]+-verifier|contractive meta', False),
 'prompt':('Prompt operad (colours, anti-ops)', r'prompt_colour|prompt_anti_op|prompt_hierarchy|AntiOpBinding|PromptTreeNode', False),
 'quot':('Operational trace quotient', r'quotient_workflows|operad_pipe|TypedOp\b|trace quotient', False),
}
CR={k:re.compile(v[1], re.I if k not in('equiv',) else 0) for k,v in C.items()}
def read(p):
    try: return open(p,encoding='utf-8',errors='ignore').read()
    except: return ''
def hits(text):
    op=bool(OP.search(text))
    return {k for k,(l,rx,need) in C.items() if CR[k].search(text) and (op or not need)}
# ---- workflows
wf=defaultdict(lambda: {'code':set(),'test':set(),'doc':set(),'files':defaultdict(set)})
folders={int(re.match(r'wf(\d+)',os.path.basename(d)).group(1)):d for d in glob.glob('workflows/wf[0-9]*')}
def add(n,path,kind):
    t=read(path); h=hits(t)
    for k in h: wf[n][kind].add(k); wf[n]['files'][k].add(path)
for n,d in folders.items():
    for p in glob.glob(d+'/**/*',recursive=True):
        if os.path.isdir(p) or SKIP.search(p): continue
        if p.endswith('.md'): add(n,p,'doc')
        elif p.endswith('.py'): add(n,p,'test' if '/test' in p or os.path.basename(p).startswith('test_') else 'code')
for n in range(1,6):
    for p in glob.glob(f'pfp/workflows/wf000{n}/**/*.py',recursive=True):
        add(n,p,'test' if 'test' in p else 'code')
# family classes
fam_src={}
for f in sorted(glob.glob('pfp_core/workflow_families/layer*.py')):
    s=read(f); tree=ast.parse(s)
    for node in tree.body:
        if isinstance(node,ast.ClassDef):
            seg=ast.get_source_segment(s,node); m=re.search(r"spec_from\('WF(\d+)'",seg)
            if m: fam_src[int(m.group(1))]=(f,seg,[b.id for b in node.bases if isinstance(b,ast.Name)])
cls2wf={}
for n,(f,seg,b) in fam_src.items(): cls2wf[re.search(r'class (\w+)',seg).group(1)]=n
for n,(f,seg,bases) in fam_src.items():
    for k in hits(seg): wf[n]['code'].add(k); wf[n]['files'][k].add(f+' (class)')
famtests=glob.glob('pfp_core/workflow_families/tests/*.py')
for p in famtests:
    t=read(p)
    for n in fam_src:
        if re.search(rf'\bWF{n}\b|wf{n}_|wf{n:02d}_',t):
            pass
# ---- other layers
def scan(paths):
    out=defaultdict(set)
    for p in paths:
        for k in hits(read(p)): out[k].add(p)
    return out
der=scan(glob.glob('dag/derivations/*.md'))
lean_paths=[p for p in glob.glob('**/*.lean',recursive=True) if not p.startswith('atlas/archive') and '.lake' not in p]
lean=scan(lean_paths)
rs=[p for p in glob.glob('code/rust/**/*.rs',recursive=True) if '/target/' not in p]
rs_test=[p for p in rs if '/tests/' in p or p.endswith('tests.rs')]
rs_src=[p for p in rs if p not in rs_test]
rust_src=scan(rs_src); rust_test=scan(rs_test)
# rust inline #[cfg(test)] counts as test
rust_inline=defaultdict(set)
for p in rs_src:
    t=read(p)
    if '#[cfg(test)]' in t:
        tt=t[t.index('#[cfg(test)]'):]
        for k in hits(tt): rust_inline[k].add(p)
py_tests=[p for p in glob.glob('**/test_*.py',recursive=True) if not p.startswith('atlas/archive') and not p.startswith('dag/reviews')]
pyt=scan(py_tests)
dag=json.load(open('dag/derivations_dag.json'))['nodes']
dagh=defaultdict(set)
for n in dag:
    if n.get('kind') in ('pinned_source_file','archive_claim'): continue
    for k in hits(json.dumps(n,ensure_ascii=False)): dagh[k].add(n['id'])
L=json.load(open('atlas/atlas_claim_ledger.json'))
V={r['atlas_id']:r['verdict'] for r in json.load(open('atlas/atlas_claim_matches.json'))['results']}
ath=defaultdict(lambda: defaultdict(set))
for c in L['archive_claims']:
    for k in hits(' '.join(str(c.get(x) or '') for x in ('statement','evidence_text','other_text'))): ath[k][V.get(c['atlas_id'],'?')].add(c['atlas_id'])
res={'concepts':{k:v[0] for k,v in C.items()},'wf':{n:{'code':sorted(d['code']),'test':sorted(d['test']),'doc':sorted(d['doc']),'files':{k:sorted(v) for k,v in d['files'].items()}} for n,d in sorted(wf.items())},
 'der':{k:sorted(v) for k,v in der.items()},'lean':{k:sorted(v) for k,v in lean.items()},'rust_src':{k:sorted(v) for k,v in rust_src.items()},
 'rust_test':{k:sorted(set(v)|rust_inline[k]) for k,v in list(rust_test.items())+[(k,set()) for k in rust_inline if k not in rust_test]},
 'pytest':{k:sorted(v) for k,v in pyt.items()},'dag':{k:sorted(v) for k,v in dagh.items()},'atlas':{k:{vv:sorted(s) for vv,s in d.items()} for k,d in ath.items()}}
LIVE={1,2,3,4,5,52}
def wfs(ns): return ', '.join(f'WF{n}'+('*' if n in LIVE else '') for n in sorted(ns)) or '—'
def n(d,k): return len(d.get(k,[]))
print('| Concept | Workflow code | Workflow tests | DAG nodes | Derivations | Archive claims m/p/g | Lean | Rust src / tests | Python test files |')
print('| --- | --- | --- | ---: | ---: | --- | ---: | --- | ---: |')
for k,(label,_,_) in C.items():
    wc=[int(x) for x in res['wf'] if k in res['wf'][x]['code']]; wt=[int(x) for x in res['wf'] if k in res['wf'][x]['test']]
    a=res['atlas'].get(k,{})
    print(f"| {label} | {wfs(wc)} | {wfs(wt)} | {n(res['dag'],k)} | {n(res['der'],k)} | {len(a.get('matched',[]))}/{len(a.get('partial',[]))}/{len(a.get('gap',[]))} | {n(res['lean'],k)} | {n(res['rust_src'],k)} / {n(res['rust_test'],k)} | {n(res['pytest'],k)} |")
if '--json' in sys.argv: json.dump(res,sys.stdout,indent=1,ensure_ascii=False)
