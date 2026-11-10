"""Bounded adapter controls with injected hosts; no native/provider execution."""
import sys,json,ast,itertools,dataclasses,types
sys.dont_write_bytecode=True
from additional_pfp_adapters_audit import ROOT,write
sys.path.insert(0,str(ROOT))
def capture(fn):
    try:return {'returned':fn()}
    except Exception as e:return {'exception':type(e).__name__,'message':str(e)}
class FakeOk:
    is_ok=True;is_err=False
    def __init__(self,value):self.value=value
    def unwrap(self):return self.value
class FakeErr:pass
class Host:
    def __init__(self,payload):self.payload=payload
    def __getattr__(self,name):return lambda *args,**kwargs:FakeOk(self.payload)
def extracted(path,names,namespace):
    tree=ast.parse((ROOT/path).read_text(encoding='utf8'));keep=[n for n in tree.body if isinstance(n,ast.ImportFrom) and n.module=='__future__' or isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in names]
    exec(compile(ast.Module(keep,type_ignores=[]),str(path),'exec'),namespace)
    return namespace
def main():
    from pfp.infrastructure.adapters.exact_rust_adapter import RustExactEngineAdapter
    from pfp.domain.exact.q import Q
    matrix=((Q(1,1),),)
    outcomes={}
    for method,result in [('is_positive_definite',{'is_positive_definite':'false'}),('rank',{'rank':1.9}),('verify_boundary_closed',{'boundary_closed':'false'}),('is_ordered_closure',{'is_closure':'false'})]:
        adapter=RustExactEngineAdapter(host=Host({'success':'false','action':'unrelated','result':result}))
        call=(lambda:adapter.is_ordered_closure([matrix],[])) if method=='is_ordered_closure' else (lambda:getattr(adapter,method)(matrix))
        outcomes[method]=capture(call)
    from pfp.infrastructure.adapters.representation.plain_text_representation import PlainTextRepresentation
    from pfp.infrastructure.adapters.representation.glyph_packet_representation import GlyphPacketRepresentation
    from pfp.domain.representation.models import TurnView
    original=TurnView(1,2,3,((' a=b ','first\nsecond'),),(('x',2),),(('m:n','reason'),),' standard ')
    plain=PlainTextRepresentation();glyph=GlyphPacketRepresentation()
    source=dataclasses.asdict(original);plain_result=plain.parse(plain.render(original));glyph_result=glyph.parse(glyph.render(original))
    coercion=json.loads(glyph.render(original));coercion['round_seq']=True;coercion['metrics']['phi1']=1.9
    evns={'json':json,'hashlib':__import__('hashlib'),'AuthorityEffect':types.SimpleNamespace(NONE=types.SimpleNamespace(value='None'))}
    extracted('pfp/infrastructure/adapters/oesos_evidence_adapter.py',{'OesosEvidenceAdapter'},evns)
    OesosEvidenceAdapter=evns['OesosEvidenceAdapter']
    event=types.SimpleNamespace(event_id='event',event_type='test',step=0,payload_digest='not-a-digest',previous_digest='broken-chain')
    evidence=OesosEvidenceAdapter();one=evidence.build_evidence_receipt([event],{'claim':'A'});two=evidence.build_evidence_receipt([event],{'claim':'B'});old=one['chain_sha256'];one['events'][0]['step']=99
    # Exact source class/method bodies, but replace unavailable imports with explicit stubs.
    ns={'Err':FakeErr,'StabilizerPort':object,'deepcopy':__import__('copy').deepcopy}
    extracted('pfp/infrastructure/adapters/stabilizer_rust_adapter.py',{'StabilizerRustAdapter'},ns)
    injected=ns['StabilizerRustAdapter'](Host({'success':True,'action':'unrelated','result':{'Pass':{'case_id':'other'}}}))
    stabilizer=injected.check({'case_id':'expected'},{})
    result={'exact_adapter_injected_malformed_outcomes':outcomes,'representation':{'original':source,'plain_roundtrip':dataclasses.asdict(plain_result),'plain_equal':plain_result==original,'glyph_equal':glyph_result==original,'plain_empty':dataclasses.asdict(plain.parse('')),'glyph_coercion':dataclasses.asdict(glyph.parse(json.dumps(coercion)))},'evidence_receipt':{'metadata_different_same_digest':one['chain_sha256']==two['chain_sha256'],'mutation_leaves_stale_digest':one['chain_sha256']==old,'malformed_chain_was_wrapped':True},'stabilizer_injected_other_action_and_id':stabilizer,'limits':['Exact adapter and representations used normal imports and injected data only.','Stabilizer and OESOS classes were extracted unchanged via AST because operating_system and governance.contracts imports are missing; dependency imports were stubbed, so these are method-boundary controls, not native-host or complete package tests.','Malformed injected native results demonstrate adapter acceptance conditions, not that the canonical native producer emits them.']}
    from pfp.infrastructure.adapters.finite_gauge import sign_graph as sg,frontier_search as fs
    vertices=('a','b','c');pairs=list(itertools.combinations_with_replacement(vertices,2));failures=[];checks=0
    for labels in itertools.product((-1,0,1),repeat=len(pairs)):
        edges=tuple(sg.SignedRewrite(u,v,p) for (u,v),p in zip(pairs,labels) if p!=-1)
        existence=any(all(bits[vertices.index(e.source)]^bits[vertices.index(e.target)]==e.odd for e in edges) for bits in itertools.product((0,1),repeat=3))
        witness=sg.classify_sign_graph(vertices,edges);valid=sg.verify_gauge(vertices,edges,witness) if isinstance(witness,sg.GaugeWitness) else sg.verify_odd_cycle(vertices,edges,witness);checks+=1
        if not valid or isinstance(witness,sg.GaugeWitness)!=existence:failures.append(labels)
    key=fs.PresentationKey('0'*64,'b','e','f','bd','r','est',('o',),'beta',(),fs.DIAGONAL_Z2_GRAMMAR,'0'*64,fs.CHECKER_VERSION)
    edges=(sg.SignedRewrite('a','b',1),sg.SignedRewrite('b','c',1),sg.SignedRewrite('c','a',1));prior=[];frontier=None;segments=[]
    while True:
        receipt=fs.search_sign_graph(vertices,edges,key,2,workers=1,frontier=frontier,prior_receipts=prior);segments.append({'status':receipt.status,'verified':fs.verify_search_receipt(vertices,edges,key,receipt,prior)})
        if receipt.status!='UNKNOWN':break
        prior.append(receipt);frontier=receipt.frontier
    changed=dataclasses.replace(receipt,receipt_sha256='0'*64)
    result['finite_gauge']={'graphs':checks,'independent_existence_mismatches':failures,'continuation_segments':segments,'tampered_digest_accepted':fs.verify_search_receipt(vertices,edges,key,changed,prior),'skipped_history_accepted':fs.verify_search_receipt(vertices,edges,key,receipt),'limits':'729 three-vertex undirected signed graphs including self-loops; graph-level diagonal Z2 gauges only, no Hamiltonian/physical model assertion.'}
    write('_core_probes.json',result);print(json.dumps(result,indent=2))
if __name__=='__main__':main()
