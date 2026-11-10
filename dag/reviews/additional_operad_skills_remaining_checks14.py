"""Independent finite controls on final prose recipes; no retained workflow executed."""
import ast,hashlib,json,pathlib,sys
H=pathlib.Path(__file__).resolve().parent;R=H.parents[1];P='additional_operad_skills_remaining';fs=json.loads((H/(P+'_preparation.json')).read_text())['files'];out=[]
def add(n,i,observation,limits):
 f=fs[i];assert hashlib.sha256((R/f['path']).read_bytes()).hexdigest()==f['sha256']
 out.append({'id':f'OPSKILL-CHECK-{n:03}','status':'observed','source':{'path':f['path'],'sha256':f['sha256']},'observation':observation,'limitations':limits})
branch='sprint-108-0';derived=branch.split('-')[1]
try:int('108-0')
except ValueError:explicit_cleanup_rejected=True
else:explicit_cleanup_rejected=False
assert derived=='108'and explicit_cleanup_rejected
add(99,545,{'branch':branch,'derived_sprint_number':derived,'expected_cleanup_identity':'108-0','explicit_cleanup_int_conversion_raises_ValueError':explicit_cleanup_rejected},'Literal Python expressions from documentation reproduced independently; enclosing planning/review workflow is pseudocode and not invoked.')
text='Story Completion\nQuality Gates\n'
assert all(t in text for t in ['Story Completion','Quality Gates'])
add(100,541,{'completion_text':text,'documented_header_predicate_accepts':True,'story_rows':0,'test_results':0,'evidence_paths':0},'Tests the displayed substring predicate only; surrounding manual acceptance/evidence checks could reject this document if independently enforced. No actual sprint artifact written.')
# Edges producer -> consumer. Retro needs VP output, VP needs retro output.
edges=[('retrospective','vp_briefing'),('vp_briefing','retrospective')]
nodes={n for e in edges for n in e};ready=[n for n in nodes if not any(b==n for a,b in edges)]
assert not ready
add(101,552,{'prerequisite_edges':edges,'initial_artifacts':[],'ready_producers':ready,'cycle':True},'Finite dependency model of literal first-run pre-gates; precreated placeholder files can break existence deadlock without providing completed review evidence. No orchestrator executed.')
branch_reachable={'base','story1','story2'};head_reachable=set(branch_reachable);selection=head_reachable-branch_reachable
assert not selection
add(102,554,{'HEAD_equals_sprint_branch':True,'documented_two_dot_selection':sorted(selection),'sprint_story_commits_excluded':['story1','story2']},'Exact reachability-set meaning of A..B, not an actual Git log run. Author email/file-count heuristic also does not establish UI origin or CI execution.')
def substitutions(ops):return sorted((a,b)for a,(ain,aout)in ops.items()for b,(bin,bout)in ops.items()if ain==bout)
before={'A':('X','X'),'B':('Y','Y')};after={'A':('X','X'),'B':('X','Y')};left=substitutions(before);right=substitutions(after)
assert len(left)==len(right)==2 and left!=right
add(103,560,{'convention':'unary operations (input,output); outer accepts inner output','before':before,'after':after,'before_composable_pairs':left,'after_composable_pairs':right,'both_count_pairs':[2,2],'undetected_colour_change':True},'Finite independent colour-compatibility graph; refutes count-pair completeness/causal identification, not the usefulness of exact finite fixture census or source-bound inventories.')
sources={'test_a.py':'from target import check\ncheck()\n','production.py':'import importlib\nmod=importlib.import_module("target")\nmod.check()\n'}
static={name for name,body in sources.items()for node in ast.walk(ast.parse(body))if isinstance(node,ast.ImportFrom)and node.module=='target'}
assert static=={'test_a.py'}
add(104,563,{'programs':sources,'static_target_importers':sorted(static),'production_target_call_present_via_dynamic_import':True,'test_only_static_classification_is_false_positive':True},'Transparent static-import model matching declared limitation, not a replay of external operations detector. Code strings parsed only, never imported or executed.')
valid='x = 1\n';invalid='x =\n';ast.parse(valid)
try:ast.parse(invalid)
except SyntaxError:invalid_refused=True
else:invalid_refused=False
assert invalid_refused
add(105,564,{'criterion':'Python source parses successfully','explicit_Decisive_mutation_declaration':False,'valid_source':valid,'invalid_source':invalid,'criterion_can_fail':invalid_refused},'Syntax counterexample refutes inference from missing declared falsifier to unfalsifiability. It does not establish semantic adequacy of a build/test gate; no native compile or retained tool invoked.')
(H/(P+'_checks14.json')).write_text(json.dumps({'python':sys.version,'retained_owner_execution':False,'results':out},indent=2)+'\n');print(json.dumps({'observed':len(out)}))
