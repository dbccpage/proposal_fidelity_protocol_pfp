"""Bounded structural, arithmetic and custody checks; never executes archived code."""
import sys,json,re,hashlib,collections,itertools,zipfile,struct,difflib
sys.dont_write_bytecode=True
import additional_paper_011_history_formal_receipts_audit as a
PAPER='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/'
HIST=PAPER+'docs/history_recovery/'
SCOPE=a.read('_scope.json')['files'];BY={r['path']:r for r in SCOPE}
INV={r['path']:r for r in json.loads((a.ROOT/'dag/file_inventory.json').read_text(encoding='utf8'))['files']}
RAW={p:(a.ROOT/p).read_bytes() for p in BY}
J={};DUPS={};MARKERS={};ARCH={};ARCHNAME={}
def digest(b):return hashlib.sha256(b).hexdigest()
def canon(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def parse(b):
    dup=[]
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:dup.append(k)
            d[k]=v
        return d
    x=json.loads(b.decode('utf-8-sig'),object_pairs_hook=pairs);return x,dup
def mapped(s,context):
    s=s.replace('\\','/')
    marker='011_recreated_demos_and_proposal_fidelity_evidence/'
    if marker in s:s=PAPER+s.split(marker,1)[1]
    elif s.startswith(('docs/','code/')):s=PAPER+s
    elif '/' not in s:s=context.rsplit('/',1)[0]+'/'+s
    # Only known original inventory paths within this paper. Never follow arbitrary historical paths.
    return s if s in INV and s.startswith(PAPER) else None
def evidence(path):return {'path':path,'sha256':BY[path]['sha256'] if path in BY else INV[path]['sha256']}
def compare_hash(target,want):
    if target not in RAW:
        b=(a.ROOT/target).read_bytes();assert digest(b)==INV[target]['sha256'];RAW[target]=b
    b=RAW[target]
    return {'target':target,'expected':want,'current':digest(b),'raw_match':digest(b)==want,'lf_match':digest(b.replace(b'\r\n',b'\n'))==want,'original_zip_match':target in ARCH and digest(ARCH[target])==want}
def hashlinks(x,context,at='$'):
    out=[]
    if isinstance(x,dict):
        for k,v in x.items():
            if isinstance(v,dict) and isinstance(v.get('sha256'),str):
                target=mapped(k,context)
                if target:out.append({'pointer':at+'/'+k+'/sha256',**compare_hash(target,v['sha256']),'recorded_bytes':v.get('bytes')})
            if isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v):
                target=mapped(k,context)
                if target:out.append({'pointer':at+'/'+k,**compare_hash(target,v)})
            if k in ('sha256','source_sha256','candidate_sha256','executable_sha256','stdout_sha256','stderr_sha256'):
                alternatives={'sha256':['path'],'source_sha256':['source_path'],'candidate_sha256':['candidate_path'],'executable_sha256':['executable'],'stdout_sha256':['stdout_path'],'stderr_sha256':['stderr_path']}[k]
                for pk in alternatives:
                    if isinstance(x.get(pk),str) and isinstance(v,str):
                        target=mapped(x[pk],context)
                        if target:out.append({'pointer':at+'/'+k,**compare_hash(target,v)})
            out.extend(hashlinks(v,context,at+'/'+str(k)))
    elif isinstance(x,list):
        for i,v in enumerate(x):out.extend(hashlinks(v,context,at+'/'+str(i)))
    return out
def markers(b):
    text=b.decode('utf8');out={};errors=[]
    for lineno,line in enumerate(text.splitlines(),1):
        m=re.search(r'\b(G(?:01|02|12)_[A-Z_]+)=(.*)',line)
        if m:
            try:out.setdefault(m[1],[]).append({'line':lineno,'value':json.loads(m[2])})
            except json.JSONDecodeError:errors.append({'line':lineno,'marker':m[1]})
    return out,errors
def scalars(x):return {k:v for k,v in x.items() if isinstance(v,(bool,int,float)) or v is None or isinstance(v,str) and k in ('schema','AuthorityEffect','scope','runtime_scope','computation','reason','outcome','representation')}
def check(rule,status,**kw):return {'rule':rule,'status':status,**kw}
def main():
    archive=a.ROOT/(PAPER+'021_recreated_demos_and_proposal_fidelity_evidence_2026-10-02.zip')
    assert a.sha(archive)=='8bf43405313439d05383552f1281eaec96442dac7eb733134bcae1394863d6b3'
    ar=[]
    with zipfile.ZipFile(archive) as z:
        names=set(z.namelist())
        for r in SCOPE:
            p=r['path'];member='021_recreated_demos_and_proposal_fidelity_evidence/'+p[len(PAPER):]
            candidates=[member] if member in names else [n for n in names if n.endswith('/'+p[len(PAPER):])]
            if len(candidates)!=1:ar.append({'path':p,'status':'not_uniquely_resolved','candidate_count':len(candidates)});continue
            member=candidates[0];b=z.read(member);ARCH[p]=b;ARCHNAME[p]=member
            item={'path':p,'sha256':r['sha256'],'member':member,'original_sha256':digest(b),'original_bytes':len(b),'current_bytes':len(RAW[p]),'byte_equal':b==RAW[p],'lf_equal':b.replace(b'\r\n',b'\n')==RAW[p].replace(b'\r\n',b'\n')}
            try:
                old=b.decode('utf-8-sig').splitlines();new=RAW[p].decode('utf-8-sig').splitlines()
                if old!=new and a.Path(p).suffix in a.SOURCETYPES:item['source_delta']=''.join(difflib.unified_diff([t+'\n' for t in old],[t+'\n' for t in new],n=2))
            except UnicodeDecodeError:pass
            ar.append(item)
    a.write('_archive_comparison.json',{'archive':str(archive.relative_to(a.ROOT)).replace('\\','/'),'archive_sha256':a.sha(archive),'limit':'Only exact frozen-scope members read; bounded custody comparison, no whole archive/source reading credit. No extraction or execution.','files':ar})
    for p,b in list(RAW.items()):
        if p.endswith('.json'):J[p],DUPS[p]=parse(b)
        if p.endswith(('.txt','.bin')):
            try:MARKERS[p]=markers(b)
            except UnicodeDecodeError:pass
    autos=[];cross=[];streams=[]
    for r in SCOPE:
        p=r['path'];ext=a.Path(p).suffix
        if ext in a.SOURCETYPES:continue
        b=RAW[p];checks=[check('frozen_inventory_sha256','matched',bytes=len(b),sha256=digest(b))];assessment='';info={}
        if ext=='.exe':
            peoff=struct.unpack_from('<I',b,0x3c)[0] if len(b)>=64 else 0
            pe=peoff+24<=len(b) and b[peoff:peoff+4]==b'PE\0\0'
            checks.append(check('inert_pe_header','observed',dos_magic=b[:2].hex(),pe_signature=pe,pe_offset=peoff,machine=hex(struct.unpack_from('<H',b,peoff+4)[0]) if pe else None))
            assessment='Retained native executable. Header, length and cryptographic custody assessed only; never loaded, executed, disassembled or promoted to a source/binary correspondence proof.'
        elif ext in ('.txt','.bin'):
            try:
                text=b.decode('utf8');mk,err=MARKERS[p];info={'text_lines':len(text.splitlines()),'empty':not b,'crlf_pairs':b.count(b'\r\n'),'double_crlf':b.count(b'\r\r\n'),'marker_counts':{k:len(v) for k,v in mk.items()},'marker_parse_errors':err,'diagnostic_counts':{k:len(re.findall(k,text,re.I)) for k in ['error:','warning:','DISALLOWED_AXIOM','STATEMENT_PIN','sorry','Classical.choice','unsolved goals']}}
                checks.append(check('stream_utf8_and_marker_parse','parsed',**info))
                if b.strip().startswith((b'{',b'[')):
                    try:x,dups=parse(b);J[p]=x;DUPS[p]=dups;checks.append(check('whole_stream_json','parsed',root_type=type(x).__name__,duplicates=dups))
                    except (ValueError,UnicodeDecodeError):pass
                assessment='Bounded historical subprocess tape: all bytes hashed, decoded, marker payloads parsed and diagnostic patterns counted. Text and any success marker remain historical claims until linked to the corresponding process/source custody; this is not fresh kernel or native execution.' if b else 'Empty historical subprocess stream: zero bytes and the standard empty SHA256 confirmed. Emptiness alone supplies no success or theorem evidence.'
                streams.append({'path':p,**info})
            except UnicodeDecodeError:
                checks.append(check('binary_stream_decode','not_utf8'));assessment='Opaque retained subprocess byte stream; length and SHA256 assessed only, no execution or semantic correctness claim.'
        elif ext=='.json':
            x=J[p];checks.append(check('json_structure','parsed',root_type=type(x).__name__,entries=len(x) if isinstance(x,(dict,list)) else None,duplicate_keys=DUPS[p]))
            if isinstance(x,dict) and len(x)>80 and all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in x.values()):
                checks.append(check('runtime_hash_map','observed',entries=len(x),all_values_sha256=True))
                assessment='Bounded complete parse of historical path-to-SHA256 custody map. Every entry has a digest shape; mapped original-paper files are compared separately. External installed toolchain/OS paths are not accessed and these recorded hashes do not authenticate their execution.'
            elif isinstance(x,dict) and 'returncode' in x and 'argv' in x:
                checks.append(check('process_receipt','observed',returncode=x['returncode'],argv_count=len(x['argv']),**{k:x[k] for k in ('representation','stdin_bytes','timeout_seconds') if k in x}))
                for side in ('stdout','stderr'):
                    target=mapped(x.get(side+'_path',''),p) if x.get(side+'_path') else None
                    if not target:
                        stem=p[:-len('_process.json')] if p.endswith('_process.json') else p.rsplit('/',1)[0]+'/'
                        cs=[stem+'_'+side+ext2 for ext2 in ('.bin','.txt')] if p.endswith('_process.json') else [stem+side+'.bin']
                        target=next((c for c in cs if c in BY),None)
                    if target and side+'_sha256' in x:checks.append(check(side+'_raw_binding','matched' if digest(RAW[target])==x[side+'_sha256'] else 'mismatch',**compare_hash(target,x[side+'_sha256'])))
                for before,after in [('inputs_before','inputs_after'),('direct_inputs_before','direct_inputs_after'),('compiler_inputs_before','compiler_inputs_after'),('dependencies_before','dependencies_after'),('libraries_before','libraries_after')]:
                    if before in x and after in x:checks.append(check(before+'_after_equality','matched' if x[before]==x[after] else 'different',before_entries=len(x[before]),after_entries=len(x[after])))
                assessment='Historical process record: bounded argv/return-code, available input before/after maps and exact stream binding checked. Zero return codes are retained observations; diagnostic failures and policy refusals are distinguished by paired tape analysis, not treated as mathematical falsity. No historical command executed.'
            elif isinstance(x,list):
                keysets=collections.Counter(tuple(sorted(v)) for v in x if isinstance(v,dict));checks.append(check('record_array_schema','parsed',row_keysets=[{'keys':k,'count':v} for k,v in keysets.items()]))
                assessment='Bounded complete parse of structured report/census/mutation rows, with schema-specific cross-artifact checks recorded below. Labels and emitted types are historical observations, not independently re-elaborated proofs.'
            else:
                checks.append(check('receipt_or_manifest_fields','observed',keys=list(x) if isinstance(x,dict) else [],declared=scalars(x) if isinstance(x,dict) else {}))
                assessment='Bounded complete JSON parse of historical manifest/result/request/receipt fields. Declared statuses and scope exclusions retained; available path-hash references and mathematical/census relations are checked separately. No authority follows merely from schema, status labels, or self-reported success.'
            links=hashlinks(x,p)
            if links:
                counts=collections.Counter('raw_match' if l['raw_match'] else 'original_zip_match' if l['original_zip_match'] else 'lf_only' if l['lf_match'] else 'unmatched' for l in links)
                checks.append(check('mapped_path_hash_links','observed',counts=dict(counts),links=links));cross.append({'path':p,'counts':dict(counts)})
        archive_row=next(q for q in ar if q['path']==p)
        checks.append(check('original_zip_member_custody','observed',**{k:v for k,v in archive_row.items() if k not in ('path','source_delta')}))
        autos.append({'path':p,'sha256':r['sha256'],'full_source_read':False,'assessment':assessment,'checks':checks,'limits':['Bounded parsed/custody disposition only; not a full body read, fresh toolchain run, independent build or external runtime authentication.']})
    a.write('_automated.json',autos);a.write('_data_diagnostics.json',{'archive_summary':dict(collections.Counter('byte_equal' if q.get('byte_equal') else 'lf_equal' if q.get('lf_equal') else 'different' for q in ar)),'source_deltas':[q['path'] for q in ar if 'source_delta' in q],'mapped_hash_link_summaries':cross,'streams':streams})
    print(json.dumps({'data_assessments':len(autos),'archive_summary':dict(collections.Counter('byte_equal' if q.get('byte_equal') else 'lf_equal' if q.get('lf_equal') else 'different' for q in ar)),'source_deltas':[q['path'].split('/history_recovery/')[1] for q in ar if 'source_delta' in q]},indent=2))
    # Do not mark the report complete until schema-specific follow-up checks and findings are reviewed.
if __name__=='__main__':main()
