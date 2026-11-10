from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_operad_receipts_remaining'
rows=json.loads(Path(str(P)+'_inventory.json').read_text())['files'];N=json.loads(Path(str(P)+'_notes.json').read_text());notes=N['assessments']
data=json.loads(Path(str(P)+'_data_inspection.json').read_text())['files'];controls=json.loads(Path(str(P)+'_controls.json').read_text())
full={
271:'Complete71-line refused-manifest TDD auditor reviewed by full baseline180 and its sole changed default receipt filename at line15. Retains lexical marker/hash/count checks and explicitly false semantic-certification scope; this historical capture is not a new TDD run.',
272:'Complete165-line refused-manifest prior-art auditor reviewed by full baseline181 and sole changed default receipt filename at line13. Retains catalog/path/hash correspondence and older resolver, not retrieval or independent reading of the listed literature.',
334:'Complete two-line policy marks all files non-text and logs non-diff/non-whitespace. Supports preservation intent, not proof that pre-checkout historical bytes still match internal pins.',
340:'Complete three-line policy marks logs, baseline_bytes/** and snapshots non-text/non-diff. Useful custody configuration; does not establish origin or undo previous transformations.',
368:'Complete11-line source-finding record identifies legitimate HOLD with bounded-overclaim hit rejected by the captured native adapter. Actual offending owner was fully read at index367; no native reproduction. Its declared source hash does not equal current captured bytes, so historical-source binding remains unresolved separately from the readable branch defect.',
398:'Complete7-line receipt-selection history records snapshot tests mistakenly selected, first35-pass/3-failure result, one incorrect sorted-order oracle and two whole-tree failures. Later isolated oracle correction and gate restoration do not retroactively make that first attempt green; baseline PR gate remains distinct.',
403:'Complete6-line root mutation preflight records an anchor matching snapshot and decision branches and refusing before mutation: zero files mutated. This is harness ambiguity, not a killed production mutant or observed behavioral RED.',
440:'Complete18-line first mutation receipt contains one readback mutant, expected5 failures, killed=false and source restored. Its qualification mentions three bypasses although only one entry is retained; successor441 corrects evaluation without inventing a rerun.',
441:'Complete46-line verified successor records three guards, readback8 failures versus old expected5, source3 and catalog2. Readback same retained raw run is reinterpreted after oracle correction; three mutants reuse20 cases, not60 independent tests. Restored hashes bind declared snapshots subject to current custody limitations.',
508:'Complete38-line six-literal digest oracle body read. Fresh standalone hashlib recomputation matches all six UTF-8 literals, distinguishing raw lexical bytes, normalized version-preserving JSON and version-stripped semantic projection. This checks fixed literals only; no native encoder/parser was executed and historical base-source claim was not freshly reproduced.',
582:'Complete21-line source-drift preflight retains three changed owners with tested/current/captured identities. Earlier45-pass evidence remains confined to its tested bytes; this preflight is not final acceptance of replacements.',
583:'Complete7-line later test-drift record explicitly does not capture the current test hash. Five additional controls precede a separately frozen50-test replay; missing intermediate bytes are not reconstructed or promoted into a successful run.'}
for i,a in full.items():
 notes[str(i)]={'assessment':a}
 if i in [271,272]:notes[str(i)]['reading_method']='Complete hash-pinned baseline body plus all target differences; target-delta ledger records equal and changed intervals.'

special={
43:'Thirty-three command-navigation replacements change executable module routing only; path edits grant no research/lifecycle authority. Both before/after pins are declarations, not semantic equivalence proofs.',
79:'Despite green filename, stored exit_code is1. Retain failed historical attempt.',
90:'Initial RED includes a capture-helper hashlib failure; infrastructure failure is not evidence that the intended assertion detected the defect.',
100:'Integrated manifest run explicitly permits one expected manifest mutation; before/after mismatch here is not a covert drift claim.',
107:'Manifest write attempt failed and is retained separately from corrected108; writing before audit can leave changed bytes.',
108:'Corrected manifest-write success follows failed107; do not erase predecessor failure or infer transactionality.',
196:'Thirteen earlier input captures preserve predecessor context; current-byte equality checks do not establish original provenance.',
197:'Integrated planning receipt aggregates structural audits and historical source custody; its research links do not certify obstruction results or external literature reading.',
276:'First seal failed with list/dict AttributeError, no successful receipt; absent raw-log pin is not fabricated.',
280:'Current JSON contains one conflicting repeated adversary/entrypoints/cli.py key. Ordinary dict parsing discards one declaration. Root source-count/staged comparison claims are historical; no verified original transformation ledger exists.',
289:'Final handoff preserves separate14/9/1/33/11 batches and seven custody exceptions including overwritten early logs. These counts cannot simply be summed into independent cases; no SGT/semantic authorization follows.',
301:'Historical exit0 coexists with one recorded source_drift_after; successful process status alone does not establish unchanged-source custody.',
302:'Final successor records zero source drift; this strengthens only its own declared run, not301 retroactively.',
307:'Native build inventory has three conflicting repeated current path keys;3667 serialized path records collapse to3664 dictionary entries. Duplicate snapshots307/309/310 are one content population, not three independent builds.',
309:'Historical-lock inventory is byte-equal to307/310 and retains the same three conflicting repeated keys. Filename role is different; no independent evidence multiplication.',
310:'Build inventory is byte-equal to307/309 and retains the same three conflicting repeated keys. Current path normalization history is unknown.',
318:'C901 complexity command records exit1; adjacent format/import checks must not turn this into whole-lint success.',
319:'Final C901 command still records exit1; preserve negative result.',
320:'Historical-lock C901 command records exit1; preserve known limitation.',
321:'Final E/W lint records exit1; F/I success is a separate narrower predicate.',
322:'Historical E/W lint records exit1; retain baseline distinction.',
329:'Routed-pair regression records exit1; final summaries must retain its failure.',
336:'Canonical-source capture lists twelve byte records; locator/canonicalization declarations are not an original archive ledger for this receipt estate.',
358:'Sixteen baseline snapshots are retained contextual dependencies, not new executions.',
361:'Custody PASS is limited to the named historical capture predicate; current raw pins are checked separately and not silently substituted.',
362:'Nine historical canary records preserve negative/earlier input boundaries; not a new model campaign.',
365:'Manifest write permits one intended changed artifact; all other source custody remains separately bound.',
370:'Ninety-nine planning controls are structural finite checks, not empirical obstruction-proof results.',
371:'Three named planning REDs precede repair; their identities matter more than a generic red label.',
373:'Defect-hunter PASS covers scoped owner and51 artifacts with99 planning controls, not estate-wide adversarial robustness.',
375:'Root ingress99 and native31 are separately scoped populations, not independent evidence of arbitrary transfer.',
379:'Early foreign-task GREEN lacks later full source pins; retain narrower custody ceiling.',
381:'Foreign-task RED is historical and source-binding limited; later pins cannot retrospectively certify its exact prestate.',
385:'Adjacent ingress attempt records exit1; retained successor386 is separate.',
388:'Initial native-adapter RED exits2 due absent API, not the later HOLD semantic defect.',
389:'Native-composition green filename records exit1; corrected390 is the succeeding run.',
393:'Native HOLD RED is the targeted branch failure distinct from API absence in388.',
395:'Describe plus three native decision captures are historical request/response artifacts; no fresh native or binary provenance attestation.',
402:'Root report explicitly preserves overlapping test batches, early incomplete source pins and mock-gate versus actual offline-fixture distinctions. It is not a sum of independent native proofs.',
407:'Describe-only response identifies capability/schema, not successful execution of all actions.',
414:'Twelve public, three private and six fixture controls are distinct classifications, not additive independent tests. Compiler predicates and native semantic-ID generation retain separate trust boundaries.',
417:'First GREEN records exit101 infrastructure/lock failure; retry418 does not erase this attempt.',
419:'Unknown-action RED exit101 is a targeted historical refusal; inspect stated failure mechanism rather than equating all101 exits.',
425:'Later native-source inventory contains three conflicting repeated current path keys;3677 serialized records collapse to3674 dictionary entries. Original pre-transformation paths are unavailable.',
426:'rustfmt check exit1 is retained separately from final427 exit0.',
449:'Final42 cases comprise20 new and22 adjacent; catalog2F/2P→4P and readback8F/4P→12P are staged histories. Three mutants reuse20 cases and corrected readback oracle, not60 fresh independent cases.',
454:'Initial RED source capture is explicitly reconstructed from imports/current unchanged test, not an exact pre-RED byte capture. Later exact hash and recovered prefix improve a separate attempt; independent approval remains absent.',
456:'Five-artifact adversary custody bundle contains duplicate DDA/DDC data; copies and narrative wrappers are not independent observations.',
466:'Seven boundary-refinement GREENs ran after repair; refinement adds equal-concatenation framing oracle without replaying old RED or37-test baseline.',
468:'Seven RED/GREEN body-binding controls plus37 regressions concern ordered body encoding and typed graph fixtures, not behavioral task preservation.',
472:'Five declared batches total245 named cases with scoped source pins; host identity is not a fresh attestation.',
474:'Sixty-five application tests use injected graph replay; they do not establish live/native execution.',
476:'Thirty-seven body regressions preserve declared before/after source equality, bounded to selected pins.',
494:'Planning progression97P2F→98P1F→99P is retained.245+99 minus55 overlap yields289, not344 independent cases.',
496:'Large verification aggregate separates focused populations and frozen host from native source tests; retained wire_green gzip has20P2 environment errors, so its filename is not all-green evidence.',
499:'Workflow receipt records38Python/8Rust and251+39 fixture relations; compile-only first attempt is not a behavioral test.',
503:'SQLite recovery52/35/16 groups have overlapping purposes. Decoded mappings cannot recover duplicate raw JSON keys; event producer only constrains event_type in payload. No power-loss exactly-once theorem follows.',
504:'Bundle34primary/31adjacent controls check receipt shape and channels; lean4_proof_hash is syntax, not a freshly executed kernel proof. Hashes are not authentication; conditional fifth DDC channel differs from four legacy fields.',
505:'Raw-ingress17→33 controls distinguish compile error E0282 from five compiling killed mutants. Six literals independently checked here; stored host was not rebuilt.',
512:'Twenty-three narrowing controls were already green; three mutants test bounded guard sensitivity. Native base license/witness is not immediate-parent retirement or lifecycle admission.',
514:'Lifecycle final13 tests are distinct from earlier17; zero digest is metadata-only for named canonical SHA256 path, not arbitrary alias soundness.',
517:'Retains ordered exits0/101/101/0; failed intermediate native attempts are not discarded or added to passing counts.',
527:'C901 extraction leaves guard block semantics unchanged and retains15-test plus four-mutant evidence. Earlier49-test coverage predates extraction.',
531:'Coverage is stored instrumented line coverage, with133/135 and rounded99 percentage; neither exhaustive input coverage nor proof.',
542:'Final49 total includes15 audit controls; four mutation runs use a13-test prior snapshot. Some early guard bypasses still encounter REQUEST_MISMATCH downstream, limiting exploit claims.',
549:'File named red_recursion records exit0; review554 explicitly calls it exploratory GREEN, not an observed RED.',
550:'Relative-root actual RED1F/50deselected precedes51P then52 with junction control. Root-source changes are separate from earlier recursion-green exploration.',
554:'Compiler CLI review preserves exploratory3-case GREEN and later true relative-root RED distinction.',
567:'Two architecture failures also occur on unchanged baseline;69 source pins/71 git reads are historical comparison evidence, not newly full-read69 owners here.',
581:'Independent review uses negative inputs, not production guard mutation;45 before source/test drift and50 frozen successor cases are separate populations.',
584:'142/25/80 integration groups are not blindly summed. Old coverage belongs exact modules; two architecture baseline failures remain.',
586:'Preservation compares six drifted and one missing old catalog records against refreshed base; two new additive records do not validate arbitrary overwrite.',
587:'Projection refresh records eight new uncommitted outputs and selected source pins; this is explicit local regeneration scope, not authority to overwrite broader history.',
589:'Two baseline architecture failures remain qualified. Typed subset is not the entire language; host parity is not task behavior; signed instruction is not detector admission.',
607:'Application progression preserves initial stub failure, isolated pass,63P1 fixture-enum error,64P then65P body-binding suite. Three guard mutants remain scoped to injected graph execution.',
616:'Thirty-two primary plus12 adjacent YAML controls distinguish explicit duplicate keys from defined merge semantics. Mutants17/5 failures and zero-write/retry controls are finite, not all YAML-loader/native policy proof.',
619:'Nine channels and52 publication checks cover declared unique-YAML receipt scope, not the whole repository suite.'}

walks={174,191,263,264,353};maps={175,192,265,266,354};manifests={112,184,201,349}
def context(i,path):
 if i in walks:return ('Planning obstruction inventory','Sixty-one epic records and ten research-doc bindings preserve false obstruction-certification and TDD-stub status. Inherited research digests are not fresh external review.',[180])
 if i in maps:return ('Prior-art attachment inventory','Thirty-two epic records,26 prior entries and31 declared paths refer to15 systems within880 catalog rows. NOT_RETRIEVED attachments cannot substantiate literature comprehension or mathematical novelty.',[181])
 if i in manifests:return ('Captured epic manifest','Sixty-one epics and zero source snapshots form structural planning custody; an inventory hash is not semantic proof of the plans.',[179])
 if i<280:return ('Planning/default-IC historical check','Useful finite command routing, refusal, successor and source-custody evidence; lexical TDD/prior-art auditors certify structural correspondence only.',[179,180,181])
 if i<334:return ('Historical scope-guard/native command evidence','Interpret selected argv, exit status, pins and explicit exceptions in this scope-guard phase. Public/private labels, native runs and copied inventories do not establish independent judges or general detector efficacy.',[])
 if i<379:return ('Cross-engine defect-hunter capture','Separates captured baseline sources, planning inventory and later defect finding. Current snapshot identity is different from original internal pin custody; no native/program reproduction.',[342,343,344,367])
 if i<433:return ('Cross-engine ingress/native scope-guard record','Relevant to task/decision binding, native HOLD and guard bypass controls. Mock/injected gates, describe metadata, build completion and source semantic checks remain different predicates.',[346,347,348,367])
 if i<454:return ('Syntax-prefilter candidate publication record','Covers catalog admission shape, source pins and readback after candidate seeding. Candidate state and finite regex nonreaction are weaker than detector qualification; source/inventory writes are not one atomic transaction.',[443,444,445])
 if i<481:return ('Typed workflow/body-binding historical evidence','Binds ordered node bodies and finite graph fixtures; framed-byte distinctions preserve representation, not behavioral equivalence. Historical capture/command coverage is explicitly limited.',[464,465,467,477])
 if i<499:return ('Planar slot/planning/wire evidence','Ordered tuple-splice laws and count reconciliation concern finite typed boundaries. Do not promote signature witnesses, noisy test labels or overlap counts into executable semantic equivalence.',[485,486,488])
 if i<504:return ('Typed workflow/recovery receipt','Finite graph, fixture and SQLite rollback/retry controls have explicit evaluator/storage assumptions; no arbitrary provider execution or power-loss exactly-once conclusion.',[464,485])
 if i<513:return ('Bundle/raw-ingress/narrowing receipt','Distinguishes raw bytes, normalized values, semantic-version projection and declared lifecycle scope. Fixed hashes and compile/mutation outcomes do not authenticate historical authors or prove general parser/solver semantics.',[506,513])
 if i<523:return ('Native lifecycle evidence record','Tests metadata-only sentinel, historical native runs and narrowing scope under explicit host/source assumptions. Native response and lifecycle authority remain separate.',[515])
 if i<544:return ('Typed-contract audit receipt','Trusted compiler, exact bank, single predicate and optional signature boundary support unadmitted audit receipts. Coverage and fixture mutation sensitivity are not detector adequacy or signer trust.',[526,530,535,539])
 if i<590:return ('Typed-contract compiler/independent-review receipt','Finite subset grammar, encoding, tracked-resource and CLI-root checks retain baseline failures and source/test drift. Negative input controls and line coverage are not independent implementation proof.',[566,568,574,575])
 if i<610:return ('Typed workflow application record','Application facade tests use injected graph/replay and task/source guards. Captured GREEN/mutant commands do not attest actual model/native runtime or arbitrary task preservation.',[464,477])
 return ('Unique-YAML loading/publication receipt','Finite duplicate constructed-key, merge compatibility and rollback/retry evidence. These named declaration-loader paths do not prove all YAML readers enforce policy.',[617,621])

for x in data:
 i=x['index']
 if str(i) in notes:continue
 kind,ceiling,owners=context(i,x['path']);pins=x.get('pins',[]);res=[p for p in pins if 'current_path'in p]
 statuses=x.get('status_fields',[])[:15];arrays=x.get('arrays',[])[:12];commands=x.get('command_fields',[])[:1]
 facts=[]
 if statuses:facts.append('Selected retained scalar fields: '+ '; '.join(a['location']+'='+str(a['value']) for a in statuses)+'.')
 if commands:facts.append('Selected recorded command (not run): '+json.dumps(commands[0]['value'],ensure_ascii=False)+'.')
 if arrays:facts.append('Parsed array sizes: '+ '; '.join(a['location']+'='+str(a['length']) for a in arrays)+'.')
 if pins:facts.append(f"Whole parsed pin scan: {len(pins)} occurrences, {len(res)} resolve in frozen scope, {sum('raw' in p['hash_matches'] for p in res)} current raw matches; outside/unresolved pins not accessed. Raw/LF/CRLF mismatches do not reconstruct original historical bytes.")
 if x.get('before_after'):facts.append('Retained before/after equality checks: '+json.dumps(x['before_after'])+'.')
 if x.get('duplicate_decoded_keys'):facts.append('Conflicting duplicate keys are preserved in diagnostic ledger; dict-derived counts/values use last occurrence and must not erase earlier declarations.')
 notes[str(i)]={'full_source_read':False,'reviewed_lines':[],'review_level':'bounded_parsed_artifact_semantic_review','reading_method':'Complete JSON parse with duplicate/nonfinite diagnostics; selected scalar/array/command/prose fields displayed and semantically assessed; not full original text or all narrative/array elements.','assessment':kind+'. '+special.get(i,'')+' '+ceiling+' '+' '.join(facts),'artifact_review':{'diagnostic_path':P.relative_to(R).as_posix()+'_data_inspection.json','diagnostic_index':i,'parsed_node_counts':x.get('node_counts'),'selected_status_fields':statuses,'selected_array_shapes':arrays,'selected_command_fields':commands,'all_original_text_read':False,'historical_results_reexecuted':False},'related_owner_evidence':[{'path':rows[o]['path'],'sha256':rows[o]['sha256'],'relationship':'Source semantics/context only; not evidence this artifact was freshly executed.'} for o in owners]}
for x in controls['checksum_lists']:
 i=x['index'];s=x['summary'];notes[str(i)]={'full_source_read':False,'reviewed_lines':[[1,{335:15,341:12,432:12}[i]]],'review_level':'bounded_checksum_population_review','assessment':f"Complete checksum-line syntax/path population checked automatically: {s['lines']} records, no invalid lines/duplicate paths, {s['resolved_scoped']} scoped resolutions, {s['raw_match']} raw matches and {s['normalized_only_match']} normalized-only matches. Header/selected entries read; remaining checksum text parsed, not full prose review. Current differences do not establish historical failure without original byte/transform ledger; unresolved/outside-scope paths not accessed. Useful frozen locator/custody list, not authority or semantic validation.",'artifact_review':s}
notes['350']={'full_source_read':False,'reviewed_lines':[[1,55]],'review_level':'bounded_parsed_catalog_review','assessment':'Header and initial entry read; full YAML parsed and all880 rows checked for uniform five-field shape, unique/nonmissing file_location, folder population and relevance_score=5. Header category totals447+397+20+16=880 agree arithmetically; 11,138 reviewed-body claim is historical and not reproduced. All880 equal scores offer no discriminating efficacy evidence; 880 relevance descriptions and linked literature were not all read. Fifteen actual folder labels differ from wider folder-coverage declaration; references are pointers only. Useful prior-art locator, not literature proof or qualification authority.','artifact_review':{k:v for k,v in controls['prior_art_catalog'].items() if k not in ['sample_first','sample_last']}}
notes['497']={'full_source_read':False,'reviewed_lines':[],'review_level':'bounded_decompressed_log_review','assessment':'Gzip integrity/decompression succeeded to567675 UTF8 bytes/130 lines; compressed bytes not human-read. Selected setup/teardown traceback and final summary inspected, with huge repetitive parametrized IDs bounded. Despite wire_green name, retained result is20 passed/2 errors: PYTEST_CURRENT_TEST exceeds Windows32767-character environment limit. This is test infrastructure failure, not evidence malformed bytes were accepted or intended assertions killed a mutant. Native/provider/test execution was not repeated.','artifact_review':{k:v for k,v in controls['gzip_log'].items() if k not in ['first_lines','last_lines','error_lines']}}
Path(str(P)+'_notes.json').write_text(json.dumps(N,indent=2)+'\n',encoding='utf8')
print('dispositions',len(notes),'full',sum(n.get('full_source_read',True) for n in notes.values()),'bounded',sum(not n.get('full_source_read',True) for n in notes.values()))
