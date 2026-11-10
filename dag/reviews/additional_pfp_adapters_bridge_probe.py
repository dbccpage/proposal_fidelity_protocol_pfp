import sys,json,ast,types,hashlib,dataclasses
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import additional_pfp_adapters_audit as a
source=a.ROOT/'pfp/infrastructure/adapters/retained_profile_cec_bridge.py'
tree=ast.parse(source.read_text(encoding='utf8'))
tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.module=='pfp.infrastructure.serialization')]
b=types.ModuleType('audit_bridge_unchanged_body');sys.modules[b.__name__]=b
class CanonicalizationError(ValueError): pass
def domain_digest(label,value):
    raw=json.dumps({'domain':label,'value':dataclasses.asdict(value)},sort_keys=True,separators=(',',':')).encode()
    return hashlib.sha256(raw).hexdigest()
b.CanonicalizationError=CanonicalizationError;b.domain_digest=domain_digest
exec(compile(tree,str(source),'exec'),b.__dict__)

def problem(label,states=('a','b'),policy=b.ClosurePolicy.EXPLICIT_PROTECTED_ONLY):
    p=b.PrimitiveCarrierV1(label,states,(b.RetainedDiffV1('a','b','w'),))
    o=b.ObserverPresentationV1(p.primitive_id,'sig',('o',),tuple(b.ProfileRowV1(s,('o',)) for s in sorted(states)),tuple(b.TransitionRowV1('o',s,s) for s in sorted(states)),(('a','b'),),policy)
    return b.BridgeProblemV1(p,o)

p=problem('parent')
cp=b.PrimitiveCarrierV1('child',('a','b'),(b.RetainedDiffV1('a','b','w'),))
co=b.ObserverPresentationV1(cp.primitive_id,'childsig',('o','p'),(b.ProfileRowV1('a',('o',)),b.ProfileRowV1('b',('o','p'))),tuple(b.TransitionRowV1(op,s,s) for op in ('o','p') for s in ('a','b')),(('a','b'),))
orbits=b.demand_orbits(p)
proposal=b.ConservativeExtensionProposalV1(p.problem_id,cp,co,tuple(b.StateMapRowV1(s,s) for s in ('a','b')),tuple(b.RetractionRowV1(s,s) for s in ('a','b')),(b.SignatureMapRowV1('o','o'),),(b.RetractionRowV1('o','o'),b.RetractionRowV1('p','o')),tuple(x.orbit_id for x in orbits),'synthetic-audit')
packet=b.CECChildPacketV1(p,orbits,proposal)
receipt=b.evaluate_cec_child_packet(packet)
other=problem('unrelated')
exhaustion=b.SearchExhaustionV1(True,True,(),(packet.packet_id,))
out=b.terminalize_declared_search(other,(),(packet,),exhaustion)
unchanged=b.SameLevelRepairCandidateV1(p.problem_id,p.primitive.carrier_id,p.observer.signature_id,p.observer.profiles,(),'synthetic-audit')
unsorted=problem('unsorted',('b','a'),b.ClosurePolicy.EXTERNAL_ALL_PAIRS)
try:
    b.active_obstructions(unsorted)
    unordered='returned'
except Exception as e: unordered=type(e).__name__+': '+str(e)
result={'method':'Unchanged full adapter AST with serialization import replaced by deterministic dataclass JSON SHA256 stub. Normal import fails because pfp.domain lacks BytePayload. No claim about production digest implementation. Synthetic two-state problems only; no supplied fixtures, native builds, providers or sealed material.','source_sha256':a.sha(source),'checks':[
{'rule':'valid_cec_control','status':'observed','accepted':receipt.accepted,'replay':b.replay_cec_child_packet(packet,receipt)},
{'rule':'controller_binds_cec_parent','status':'counterexample','controller_problem_id':other.problem_id,'packet_parent_id':p.problem_id,'returned_kind':b.terminal_kind(out).value,'accepted_unrelated_parent':type(out) is b.ConservativeExtensionProposal},
{'rule':'public_same_level_validator_binds_orbits','status':'counterexample','actual_active_orbits':len(orbits),'unchanged_profiles_empty_orbits_accepted':b.validate_same_level_repair(p,unchanged,())},
{'rule':'external_all_pairs_canonical_order','status':'counterexample','constructor_accepts_unsorted_states':True,'active_obstructions_result':unordered}
]}
a.write('_bridge_probes.json',result)
print(json.dumps(result,indent=2))
