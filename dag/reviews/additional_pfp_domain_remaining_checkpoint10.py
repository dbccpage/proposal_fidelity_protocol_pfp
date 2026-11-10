import sys
sys.dont_write_bytecode=True
import additional_pfp_domain_remaining_audit as a
rows=[
('validation/__init__.py',73,'Eager explicit re-exports of the validation owner; no additional guards. Read all imported/exported names; entry-point importing is distinct from validating data.'),
('validation/validation.py',247,'Exact builtin dict/string/int/bool and sorted unique tuple/list checks support bounded wire admission. Digest uses fullmatch and refuses the newline accepted by other nominal digest types. Forbidden authority keys are checked only at the supplied mapping level; recursive admission requires callers. UTF8 normalization performs byte substitutions without decoding, so it does not validate UTF8. Optional float accepts NaN/Infinity, and repository-path validation uses the weaker syntactic helper rather than filesystem ownership. MAX_BODY_BYTES is a constant, not enforced by these primitives. No proof/authority is supplied by syntax.'),
('errors/__init__.py',39,'Explicit refusal catalog exports; this surface contains no detectors or certificate checks.'),
('errors/errors.py',49,'Aliases CanonicalizationError from the previously reviewed exceptions owner and defines refusal strings plus four forbidden wire keys. Naming a refusal is not implementing its predicate; absence from this small key set is not authority approval.'),
('ports/scoring_port.py',40,'Protocol names the stronger entities.coboundary_score CandidateProposal and result, not the shared-kernel namesakes. Global registration accepts any injected object without runtime protocol verification; missing port fails explicitly. Native invocation/evaluator correctness remains an external contract, and a type annotation is not proof of its outputs.')]
for p,n,s in rows:a.record('pfp/domain/'+p,1,n,s)
a.report()
