import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[1];P='additional_paper_011_aggregate_native_receipts'
def load(s,d):
 p=H/(P+s);return json.loads(p.read_text()) if p.exists() else d
n=load('_notes.json',{});ts=load('_transfers.json',[]);art=load('_artifact_reviews.json',[])
base='aggregate_recreated_run/original_recovery_v1/final_v3/source_files/research/mssn_sn_tower/demos/demo_2/'
notes={
'bqnf_zero.py':'Complete124-line source body read. Exact Fraction parsing rejects bool/float, validates rectangular d0/d1/c1 and d1*d0=0, then checks supplied alpha or a normalized left-null separating row. The retired functional entry point always refuses. CochainPacket is publicly constructible without validation, so standalone witness functions assume the checked factory invariant; only the gate enforces that path. No Hamiltonian-to-cochain adapter, functional minimization or general sign-freedom conclusion.',
'certificate_gate.py':'Complete82-line source body read. Requires a nonempty source_ref and validates the host packet, then replays explicit alpha or finite signed-sector pairing. Both successful finite replays still return admitted=false and RefusedFunctionalAdapterUnavailable; named Phi/Gamma/Xi scalar claims cannot be minted. source_ref is a label rather than cryptographic provenance by itself, and supplied sectors are not linked to the Hamiltonian or packet by a preservation theorem.',
'sign_switching.py':'Complete196-line source body read. Exact symmetric finite matrix parser supports rational strings/Fractions/finite Decimals and refuses bools/floats. A spanning forest solves XOR labels on nonzero off-diagonal edges; inconsistency yields a replayable simple odd-parity cycle. Root bits are deterministic conventions. This is a complete decision procedure for fixed-basis diagonal plus/minus-one gauge changes only, not general Hamiltonian sign freedom or path-integral cancellation.',
'meron_witness.py':'Complete174-line source body read. Validates unique host path IDs, exact nonnegative weights and plus/minus-one integer signs; Xi must be a total map exactly on declared S0 with no fixed points, involutive, equal-weight and sign-reversing. Every survivor is individually nonnegative and exact total cancellation is rechecked. Empty supplied populations can satisfy the identity vacuously; completeness of physical sectors and derivation from a Hamiltonian are explicitly outside scope.',
'test_sign_switching.py':'Complete122-line test body read. Seven tests include exact positive/negative/zero edge examples, malformed-domain and witness controls, and all3^6 four-vertex signed simple graphs compared with all2^4 gauges, checking a cycle certificate on each negative case. This is meaningful bounded oracle coverage for the declared family, not proof over arbitrary bases. No test executed in this audit.',
'test_run_demo2_r1.py':'Complete104-line test body read. Ten tests require restricted-repair terminal only, full manifest, exact matrix entries, distinct assertions, typed gauge and duplicate/nonfinite JSON refusal. Invalid batches roll back state; historical fake Xi remains UNKNOWN_NOT_CERTIFIED. Tests depend on run_demo2 import with bootstrap effects, so they were read without importing the original runner or accessing environment files.',
'test_run_demo2_r2.py':'Complete69-line test body read. Six tests preserve the seven-move historical response as format/manifest evidence while its named symmetry witness remains unchecked. Partial, duplicate, wrong, unhashable and NaN-bearing assertions refuse. These assert negative evidence boundaries, not a successful physical certificate; no original imports or tests executed.'}
for k,v in notes.items():n[base+k]=v
n['aggregate_recreated_run/affected_v3/aggregate_receipt.json']='Full one-line receipt read. Declares three families but process_exit1 and WORKER_FAILURE with empty result families. Its574 transport calls therefore cannot be counted as a completed aggregate outcome. Runtime startup-cache metadata and pre/post custody claim are historical. Initial canonical self-digest reconstruction differs; exact serialization/path-transformation provenance remains under investigation rather than treating this as a false mathematical result.'
n['fixture_replay_2026_10_03_meron_offline_mock/demo_meron_2d_gross_neveu/receipt.json']='Full one-line receipt read. CHECKED fixture result records lattice4x4, six clusters, two cancellations and partition sum150, but explicitly live=false, live_turn_proposer_called=false, transport=fixture and empty transcript. Scope prose names a physical model; the artifact itself supplies a finite mock replay, not independent physical completeness or actual model calls. Checker is null; trace/hash and actual fixture semantics require separate checks.'
n['native_mub_recreated_run/final_v1/mub6_conj2_verification.json']='Complete208-line result body read. Seven explicitly named triples each report three all-zero gamma1/gamma2 products and holds=true, with totals7/7/0. The firewall expressly excludes MUB(6)=3 or an upper-bound result. The stated serde_json ReportPayload digest is a distinct contract, not generic sorted-JSON self hashing; reconstructing it requires the exact payload fields/order. No fresh native computation or broad MUB claim is inferred.'
for r in load('_source_comparison.json',[]):
 rel=r['path'].split('/docs/',1)[1];method=r['method']
 accepted=method=='prior_exact' or method=='prior_delta_candidate' and ('failed_runner.py' in rel or rel.startswith('native_dossier_integral/'))
 if not accepted:continue
 base_raw=(R/r['base_path']).read_bytes();assert hashlib.sha256(base_raw).hexdigest()==r['base_sha256']
 t={'path':r['path'],'sha256':r['sha256'],'base_path':r['base_path'],'base_sha256':r['base_sha256'],'base_report':r['base_report'],'method':'prior_complete_body_plus_exact_equality' if method=='prior_exact' else 'prior_complete_body_plus_all_unified_differences','comparison_receipt':'dag/reviews/'+P+'_source_comparison.json','complete_diff_read':method!='prior_exact','context_assessment':'Captured historical machinery; runtime paths/imports and custody stage are assessed separately. No successful execution inferred from byte equality.'}
 if method=='prior_exact':
  assert (R/r['path']).read_bytes()==base_raw
  detail='Exact full-body transfer from pinned prior read, with captured-context review. '+r['base_assessment']+' This copy is a historical execution capture; its relocated __file__ paths do not make it a standalone currently runnable package.'
 elif 'failed_runner.py' in rel:
  ver=rel.split('/')[2]
  detail='Complete prior701-line baseline plus every unified difference read. '+ver+' lacks the historical float-hex metadata decoder and captured canonical/exception owners; it decodes historical float packets through the newer rejecting codec. '
  if ver=='final_v1':detail+='It also compares Windows cache paths as raw strings and inventories launcher sys.executable rather than the regular backing executable. '
  elif ver=='final_v2':detail+='The path comparison is repaired but it still inventories redirected sys.executable. '
  else:detail+='The path comparison and backing executable are repaired; codec refusal remains. '
  detail+='These versions are retained failed diagnostics, not closed successful reproductions. The inherited multiword-speaker parser defect remains as described in the core review.'
 elif 'build_v1' in rel:
  detail='Complete238-line Rust baseline plus every difference read. The failed222-line version compares owned BigInt values with borrowed BigInt references, explaining the retained type-error build. It also lacks declared-carrier-dimension and certificate-degree binding added later. Its mathematical transport intent does not establish a runnable native result; failure source bytes are valuable provenance.'
 else:
  detail='Complete240-line core baseline plus every difference read. '
  if 'run_v1' in rel:detail+='This194-line predecessor imports helper and YAML and parses sources before pinning their bytes; it also omits exact control-ID/error-family checks. '
  else:detail+='This228-line predecessor pins helper/YAML before use but still omits exact control-ID/error-family checks. '
  detail+='Both versions accept any failed negative control at these sites, narrower evidence than the current precise typed assertions. Original matrix/certificate outcomes need independent arithmetic and recorded-stream reconciliation.'
 n[rel]=detail
 ts=[x for x in ts if x['path']!=r['path']]+[t]
for d in load('_data.json',[]):
 p=d['path'];rel=p.split('/docs/',1)[1];kind=d['disposition']
 if kind not in {'opaque_encrypted_payload_metadata_only','opaque_executable_custody_only','empty_retained_stream'}:continue
 if kind=='opaque_encrypted_payload_metadata_only':
  m=d['metadata'];assessment=f"Historical encrypted provider artifact for {rel.split('/')[1]}; complete public envelope JSON metadata/base64 validation only. Schema={m['schema']}, artifact schema={m['artifact_schema']}, declared plaintext length={m['byte_length']}, decoded ciphertext length={d['decoded_ciphertext_bytes']}; filename matches the declared plaintext digest={d['filename_matches_plaintext_claim']}. Useful as retained payload-location/custody evidence, but ciphertext cannot establish response text, provider origin or authenticated plaintext. No decryption/key access attempted."
 elif kind=='opaque_executable_custody_only':assessment='Preserved native transport executable '+rel+'. Complete raw SHA/byte-size and MZ header check only; semantic body reading, machine-code verification and execution are not claimed. Build/source receipt binding is reviewed separately, and a matching binary hash does not establish its mathematical implementation.'
 else:assessment='Zero-byte retained stream '+rel+'. Exhaustive byte-length/hash check confirms emptiness. Useful for distinguishing absent output from reported success; an empty stderr is not execution proof, and an empty historical trace is not a completed model bout.'
 ar={'path':p,'sha256':d['sha256'],'full_source_read':False,'reviewed_lines':[],'review_level':kind,'assessment':assessment,'bounded_checks':d,'limits':'Custody/format only; no plaintext or executable semantics claimed.'}
 art=[x for x in art if x['path']!=p]+[ar]
for suffix,value in [('_notes.json',n),('_transfers.json',ts),('_artifact_reviews.json',art)]:
 (H/(P+suffix)).write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
print({'notes':len(n),'transfers':len(ts),'bounded_artifacts':len(art)})
