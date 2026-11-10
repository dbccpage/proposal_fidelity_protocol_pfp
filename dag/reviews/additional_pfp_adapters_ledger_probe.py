import sys,json,hashlib,importlib
sys.dont_write_bytecode=True
import additional_pfp_adapters_audit as a
sys.path.insert(0,str(a.ROOT))
out={'checks':[],'limits':'Actual ledger modules only, synthetic payloads and files confined to audit-owned temp prefix; no original/source/historical ledger writes.'}
try:
    c=importlib.import_module('pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_codec')
    r=importlib.import_module('pfp.infrastructure.adapters.mssn_research.contracts.grammar.ledger_repository')
except Exception as exc:
    out['import_error']={'type':type(exc).__name__,'message':str(exc)}
else:
    packet={'assertion_flags':{'flag_pi':True},'fence_audit':{},'raw_transcript':[],'shadow_type':'test','target_theorem':'synthetic','evidence_bound':'none'}
    result=c.dict_to_packet(packet);assert result.is_ok()
    parsed=result.unwrap()
    out['checks'].append({'rule':'missing_audit_defaults_clean_despite_violation','status':'observed','flag_pi':parsed.assertion_flags.flag_pi,'check_pi':parsed.fence_audit.check_pi,'quarantine_verdict':parsed.fence_audit.quarantine_verdict,'limits':'Packet remains permanently quarantined; clean label is not an allowed promotion.'})
    malformed={**packet,'assertion_flags':None}
    try: c.dict_to_packet(malformed)
    except Exception as exc:out['checks'].append({'rule':'malformed_flags_escape_typed_result','status':'observed','exception':type(exc).__name__})
    else:raise AssertionError('expected attribute error')
    nan=c.canonical_json_bytes({'x':float('nan')}).decode('utf8')
    out['checks'].append({'rule':'canonical_encoder_accepts_non_JSON_NaN','status':'observed','encoded':nan,'assessment':'Python deterministic dumps is not a strict canonical JSON encoder.'})
    ledger=c.EpistemicQuarantineLedger('synthetic',c.StageLevel(10),(parsed,parsed))
    lines=c.serialize_ledger_to_jsonl(ledger).splitlines()
    h=json.loads(lines[0]);h['entry_count']=1;h['head_digest']=json.loads(lines[1])['entry_digest'];h['ledger_id']='renamed'
    shortened=json.dumps(h)+'\n'+lines[1]+'\n'
    got=c.deserialize_ledger_from_jsonl(shortened);assert got.is_ok()
    out['checks'].append({'rule':'self_contained_header_rewrite_allows_truncation_and_rename','status':'observed','accepted_entry_count':got.unwrap().entry_count,'accepted_ledger_id':got.unwrap().ledger_id,'assessment':'No externally pinned head/id is required; detection covers inconsistent truncation, not coordinated header rewrite.'})
    temp=a.file('_ledger_temp');temp.mkdir(exist_ok=True)
    repo=r.EpistemicQuarantineRepository(temp)
    unsafe='a/b';digest=hashlib.sha256(unsafe.encode()).hexdigest()
    p1=repo._file_path(unsafe).unwrap();p2=repo._file_path(digest).unwrap();assert p1==p2
    out['checks'].append({'rule':'safe_id_collides_with_hashed_id_namespace','status':'observed','same_path':True,'unsafe_id':unsafe,'safe_id':digest,'assessment':'Literal safe hex digest name aliases the filename for a non-safe id. Repository does not verify requested id against loaded header. No save/overwrite performed.'})
a.write('_ledger_probes.json',out);print(json.dumps(out))
