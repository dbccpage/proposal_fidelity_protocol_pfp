import sys
sys.dont_write_bytecode=True
import additional_pfp_domain_remaining_audit as a
n=a.read('_notes.json');n['controls'].extend(a.read('_boundary_probes.json')['controls'])
def ev(path,*ranges):return {'path':path,'sha256':a.row(path)['sha256'],'lines':[list(x) for x in ranges]}
for id,title,statement,evidence,controls in [
('PFPDOMAIN-F019','Gate receipt factory default stores a dataclass Field','GateReceiptV1.create uses field(default_factory=dict) as a regular function default. Omitting retained_metrics creates a receipt with a Field object and to_dict raises Field object is not iterable. The dataclass constructor itself has a correct dict factory; failure is specific to the public create factory.',[ev('pfp/domain/entities/gate_receipt.py',(41,65))],['PFPDOMAIN-C024']),
('PFPDOMAIN-F020','Declared learning repository package export cannot resolve','pfp.domain.ports advertises ILearningRepository in __all__, but does not import it or list it in _LAZY_IMPORTS. Access raises AttributeError immediately. Separate typed and generic owner modules exist; neither is selected by this advertised package entry point.',[ev('pfp/domain/ports/__init__.py',(24,75))],['PFPDOMAIN-C025']),
('PFPDOMAIN-F021','V1 decode receipt omits its honored flag from wire identity','Two otherwise identical DecodeControlReceipt values with honored=True and honored=False serialize and hash identically because to_dict omits honored. Thus retained wire/digest cannot distinguish the objects own applied-control outcome flag. V1 remains metadata-only and V2 has a separate replay contract; this finding does not claim provider enforcement was measured.',[ev('pfp/domain/ports/decode_control_port.py',(77,108))],['PFPDOMAIN-C026'])]:
 n['findings'].append({'id':id,'title':title,'statement':statement,'evidence':[x['path'] for x in evidence],'source_evidence':evidence,'control_ids':controls,'status':'confirmed_bounded_source_and_probe','limits':'Focused Python3.14.2 controls over read-vetted local declaration modules; no provider, adapter, native process or storage execution.'})
a.write('_notes.json',n);a.report()
