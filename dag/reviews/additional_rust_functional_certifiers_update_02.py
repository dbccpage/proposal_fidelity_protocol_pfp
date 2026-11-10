"""Record substantive closure/counterfeit review and completed bounded probes."""
import json,pathlib
HERE=pathlib.Path(__file__).parent; P='additional_rust_functional_certifiers'
def load(s):return json.loads((HERE/(P+s)).read_text())
notes=load('_notes.json');supp=load('_supplement.json')
notes['code/rust/core_certifiers/src/closure_certificate.rs']='Full source read (270 lines). Exact constructor maps a typed exact Gamma2 zero to Closed, nonzero to Open. Diagnostic interval constructor rejects zero denominators, negative/inverted enclosures, distinguishes exact [0,0], positive, and zero-touch uncertainty using rational comparisons. ClosureCertificate and ClosureDiagnostic remain public-field Deserialize DTOs: constructor checks can be bypassed, and caller carrier/checker/replay metadata is not authenticated. A valid interval must be independently established as an enclosure; this module does not compute Gamma2 or prove its carrier. Tests cover negative/inverted/invalid endpoints and 1e-400 positive/zero-touch cases, read but not run here. Bounded classification checks are not a closure proof for external data.'
notes['code/rust/core_certifiers/src/counterfeit_detection.rs']='Full source read (640 lines; truncated initial emission completed by rereading 140-280). Exact and interval counterfeit predicates reject invalid denominators, negative mass/Gamma2, zero replay hashes, carrier mismatch, Closed with nonzero Gamma2, and ExactRepair with nonzero mass/Gamma2. Rational comparisons avoid floating underflow; diagnostic path uses exact endpoint semantics. Non-counterfeit means this bounded consistency predicate only: it neither loads hashed carrier/certificate bytes nor authenticates refs; it does not require equality of the two nonzero replay hashes. Open with Gamma2=0 is explicitly permitted by a test (513-520), so the predicate is not a complete closure-status validator. Capacity-record boilerplate proves only 1<=admitted<=bound, unrelated to authenticity. Tests include tiny rational fraud, negative intervals, invalid denominators, multiple reasons, and zero interval controls; read not executed here.'
for f in supp['findings']:
 if f['id']=='RFC-F001':
  f['status']='reproduced by unchanged-source native probe in both overflow-check modes'
  f['limits']='Synthetic 1x1 LP with BigRational::new_raw(1,0) panics in num-rational; panic is caught by the probe. No forged certificate or authority exploit claimed.'
  f['validation']='RFC-V002'
 if f['id']=='RFC-F002':
  f['status']='reproduced by unchanged-source native probe in both overflow-check modes'
  f['validation']='RFC-V002'
if not any(v['id']=='RFC-V002'for v in supp['validation']):
 supp['validation'].append({'id':'RFC-V002','kind':'bounded direct-source native counterexamples','details_file':'dag/reviews/'+P+'_validation_01.json','result':'Both rustc overflow-checks=yes/no builds and executions exit 0. Generic LP raw-denominator panic caught; full Phi1 denominator guard control refuses; finite MAX-valued matrix and dual give NaN boundary but reported zero boundary defect.','limits':'Unchanged phi1/binary_degree/phi1_certifier source plus hash-pinned cached offline dependencies. Synthetic public inputs only; not a full suite, physical claim, or authority exploit.'})
for suffix,data in [('_notes.json',notes),('_supplement.json',supp)]:
 (HERE/(P+suffix)).write_text(json.dumps(data,indent=2)+'\n')
