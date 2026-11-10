import sys
sys.dont_write_bytecode=True
import additional_pfp_domain_remaining_audit as a
rows=[
('documentation_integrity/__init__.py',20,'Exports local request/receipt/ledger and path-classification policies; no file/process effect at import.'),
('documentation_integrity/models.py',61,'Passive command/request/receipt records and mutable findings ledger. ok means absence of accumulated error messages only, not completed checks. as_dict shares mutable list objects; no hash/source/exit-code consistency or authority validation.'),
('documentation_integrity/policies.py',44,'Extension classification and lexical relative-path predicate; rejects slash roots, backslashes, empty/dot/dotdot components but accepts Windows drive-qualified C:/x and colon schemes. This is not a resolved-containment or symlink policy. No filesystem access occurs here, and downstream escape is not established.'),
('documentation_integrity/ports.py',37,'Protocols delegate time, execution, filesystem and output. Atomic-write wording and Result types do not implement custody, containment, subprocess budgets or error handling.'),
('representation/__init__.py',13,'Exports TurnView and protocol only; no actual representation adapter.'),
('representation/models.py',99,'TurnView rejects bool/negative scalar counters and non-None authority but normalizes pair contents only for non-tuple inputs, leaving tuple element shapes/types unchecked. Canonical/information-complete label is a caller contract, not equivalence proof. Arm A/C config differs only representation; copies are returned but public global dicts mutable. No model intervention/experiment here.'),
('representation/ports.py',28,'Bidirectional render/parse protocol documents exact TurnView recovery but imposes no round-trip law or implementation; runtime structural check only confirms attribute availability.')]
for p,l,s in rows:a.record('pfp/domain/'+p,1,l,s)
n=a.read('_notes.json');n['controls'].extend(a.read('_policy_probes.json')['controls'])
def ev(path,*ranges):return {'path':path,'sha256':a.row(path)['sha256'],'lines':[list(x) for x in ranges]}
for id,title,s,e,control in [
('PFPDOMAIN-F028','Ensemble enforces per-member rather than declared total budget','Header promises <=70B total parameters for all ensemble members; constructor checks each member independently. Two70B members from different lineages are accepted for140B total. NaN also passes both positivity and ceiling comparisons. Lineage cap and parameter metadata remain caller-supplied.',ev('pfp/domain/ensemble/models.py',(3,7),(35,41),(57,85)),['PFPDOMAIN-C035']),
('PFPDOMAIN-F029','Reviewed promotion asserts unperformed holdout passes','CivilizationState.promote_to_reviewed requires only current CANDIDATE tier and returns a reason claiming passed negative-selection holdout banks; it accepts no receipt or test input. The subsequent ADMITTED method correctly refuses all signatures, so this finding concerns false review evidence, not an admitted-authority bypass.',ev('pfp/domain/civilization/models.py',(140,182)),['PFPDOMAIN-C036']),
('PFPDOMAIN-F030','Elenchus reports ten checked rules beyond its implemented predicate','Interrogation claims theorem laundering and re-export boundary laundering detection, but the body implements praise/urgency waiver regexes only and always fills all ten PRIME labels as checked. A synthetic text explicitly proposing a re-export shim and ungrounded theorem claim proceeds. This does not establish semantic defense or contradiction extraction.',ev('pfp/domain/civilization/elenchus.py',(40,50),(78,117)),['PFPDOMAIN-C037'])]:
 n['findings'].append({'id':id,'title':title,'statement':s,'evidence':[e['path']],'source_evidence':[e],'control_ids':control,'status':'confirmed_bounded_source_and_probe','limits':'Small synthetic local inputs; no provider, host authority, actual model-size or deployment behavior evaluated.'})
a.write('_notes.json',n);a.report()
