"""Synthetic prompt schema and host-rendered in-memory SQLite controls only."""
import sys,types,json,hashlib,importlib.util,sqlite3
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];bindings=[];controls=[]
for name in ['pfp','pfp.domain','pfp.domain.prompt_representations']:
 m=types.ModuleType(name);m.__path__=[];sys.modules[name]=m
def load(short):
 p=ROOT/('pfp/domain/prompt_representations/'+short+'.py');name='pfp.domain.prompt_representations.'+short;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);bindings.append({'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});return m
def control(i,rule,status,**kw):controls.append({'id':'PFPDOMAIN-C'+str(i).zfill(3),'rule':rule,'status':status,**kw})
c=load('common');s=load('structured_prompt_representation');r=load('relational_prompt_representation');sym=load('symbolic_prompt_representation');op=load('operadic_prompt_representation');eg=load('egraph_prompt_representation');di=load('diagram_prompt_representation');co=load('cochain_prompt_representation')
base={'source_id':'synthetic','source_sha256':'a'*64,'proposal_sha256':'b'*64}
structured=s.StructuredPromptRepresentation.from_source_and_segments('synthetic','α','b'*64,[s.StructuredSegmentBinding(slot='s0',role='task',text='changed',start_byte=0,end_byte=2)]);assert structured.payload.segments[0].text!=structured.payload.source
split=s.StructuredPromptRepresentation.from_source_and_segments('synthetic','α','b'*64,[s.StructuredSegmentBinding(slot='s0',role='task',text='a',start_byte=0,end_byte=1),s.StructuredSegmentBinding(slot='s1',role='constraint',text='b',start_byte=1,end_byte=2)])
control(85,'structured_span_text_and_UTF8_binding','counterexample_observed',source='α',declared_complete_span=[0,2],accepted_segment_text='changed',accepted_middle_codepoint_boundary=1,limit='Source digest itself is recomputed correctly; segment content and UTF8 boundaries are not compared.')
symbolic=sym.SymbolicPromptRepresentation(**base,grammar_sha256='c'*64,legend='arbitrary changed legend',wire='<<p><v1><<q><s0>>>',bindings={'s0':'unrelated text'});assert symbolic.source_sha256!=c.sha256_digest('unrelated text')
rel=r.RelationalPromptRepresentation(**base,spans=[r.RelationalSpanRow(slot='s0',role='task',text='unrelated text')])
control(86,'symbolic_and_relational_source_digest_binding','counterexample_observed',arbitrary_source_digest_accepted=True,symbolic_changed_legend_accepted=True,relational_arbitrary_digest_accepted=True,limit='Caller may separately compare a protected ordered query; these representation models do not.')
egraph=eg.EgraphPromptRepresentation(**base,eclasses={'e9':['1','2'],'e10':['1']},spans=[eg.EgraphSpanBinding(slot='s0',role='task',eclass_id='e9',text='claim')]);assert len(egraph.eclasses)==2
control(87,'egraph_equivalence_disjointness_and_sequence','counterexample_observed',classes={'e9':['1','2'],'e10':['1']},accepted=True,limit='No equation proof, saturation run or constraint-before/after comparison is performed by this schema.')
diagram=di.DiagramPromptRepresentation(**base,colors=['C'],boxes=[di.DiagramBox(box_id='b0',label='f',inputs=['missing'],outputs=[])],wires=[di.DiagramWire(wire_id='w0',color='C',source='OUT',target='IN')],spans=[di.DiagramSpanBinding(slot='s0',role='task',box_id='b0',text='x')]);assert diagram.boxes[0].inputs==['missing']
control(88,'diagram_port_wiring_and_boundary_direction','counterexample_observed',accepted_undeclared_box_input='missing',accepted_wire=['OUT','IN'],limit='No planarity, acyclicity or morphism semantics inferred.')
cochain=co.CochainPromptRepresentation(**base,vertices=['v'],faces=[['v','v','v']],cochain_1={'absent->absent':'1'},cochain_2={'nonexistent_face':'3'},spans=[co.CochainSpanBinding(slot='s0',role='task',simplex='nonexistent_simplex',text='x')]);assert not cochain.edges and cochain.faces==[['v','v','v']]
control(89,'cochain_representation_carrier_and_reference_binding','counterexample_observed',accepted_degenerate_face=['v','v','v'],declared_edges=[],accepted_undeclared_edge_cochain=True,accepted_undeclared_face_cochain=True,accepted_undeclared_span_simplex=True,limit='Exact rational spelling is checked; coboundaries, nilpotency and harmonic equations are not computed.')
text="quote'\"; -- data\x00 α😀";sql=r.SqlitePromptRepresentation(**base,spans=[r.RelationalSpanRow(slot='s0',role='task',text=text)]).render()
with sqlite3.connect(':memory:') as conn:
 conn.executescript(sql);got=conn.execute('SELECT slot, role, text FROM prompt_spans').fetchall();assert got==[('s0','task',text)]
control(90,'host_rendered_sqlite_v2_lossless_text','bounded_positive_control_observed',quotes_unicode_NUL_preserved=True,rows=1,sqlite_version=sqlite3.sqlite_version,limit='Only host-rendered synthetic SQL executed in isolated memory database. No model SQL, external database or provider accessed.')
out={'runtime':sys.version,'source_bindings':bindings,'controls':controls};(ROOT/'dag/reviews/additional_pfp_domain_remaining_representation_probes.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'controls':len(controls),'ids':[x['id'] for x in controls]}))
