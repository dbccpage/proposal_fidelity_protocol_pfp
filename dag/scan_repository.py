"""Nonexecuting per-file structural scan; explicitly not a semantic proof audit."""
from pathlib import Path
import ast, collections, hashlib, json, re
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]
DAG=ROOT/'dag'
PATTERNS={
    'mathematical_claim':re.compile(r'\b(theorem|lemma|proposition|soundness|completeness|associativ|idempoten|guarantee|proof)\w*\b',re.I),
    'assumption_or_limit':re.compile(r'\b(assum|conditional|bounded|unverified|not.established|not.prov|TODO|FIXME|sorry|admit)\w*\b',re.I),
    'evaluation_claim':re.compile(r'\b(accuracy|p.value|confidence.interval|held.out|token.cost|cost.usd|success.rate|pass.rate)\b',re.I),
}

def main():
    inv=json.loads((DAG/'file_inventory.json').read_text(encoding='utf-8'))
    records=[]
    for f in inv['files']:
        rel=f['path']; p=ROOT/rel
        row={'path':rel,'sha256':f.get('sha256'),'review_level':'structural_only',
             'semantic_review_complete':False,'category':f['category']}
        if not p.is_file() or p.is_symlink():
            row['status']='missing_or_nonregular';records.append(row);continue
        if (p.name=='.env' or p.name.startswith('.env.')) and p.name not in {'.env.example','.env.sample','.env.template'}:
            row['status']='sensitive_content_not_read';records.append(row);continue
        raw=p.read_bytes()
        row['hash_matches_inventory']=hashlib.sha256(raw).hexdigest()==f.get('sha256')
        try:
            if b'\x00' in raw: raise UnicodeError('NUL bytes')
            text=raw.decode('utf-8-sig')
        except UnicodeError:
            row['status']='binary_or_non_utf8_metadata_only';records.append(row);continue
        lines=text.splitlines();row['line_count']=len(lines)
        row['status']='text_scanned_not_semantically_reviewed'
        suffix=p.suffix.lower()
        try:
            if suffix=='.py':
                tree=ast.parse(text,filename=rel)
                row['parse']='python_ast_ok'
                row['definitions']=[{'name':x.name,'line':x.lineno,'kind':type(x).__name__}
                                    for x in ast.walk(tree) if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
                row['imports']=[x.module for x in ast.walk(tree) if isinstance(x,ast.ImportFrom)]
            elif suffix=='.json':
                pairs=[]
                def obj(items):
                    seen=set()
                    for k,v in items:
                        if k in seen: pairs.append(k)
                        seen.add(k)
                    return dict(items)
                data=json.loads(text,object_pairs_hook=obj,
                                parse_constant=lambda value: (_ for _ in ()).throw(ValueError('Nonfinite JSON constant '+value)))
                row['parse']='json_ok';row['duplicate_keys']=sorted(set(pairs))
                row['top_level_type']=type(data).__name__
                if isinstance(data,dict): row['top_level_keys']=list(data)[:80]
                if isinstance(data,(list,dict)): row['top_level_items']=len(data)
            elif suffix=='.jsonl':
                count=0
                for line in lines:
                    if line.strip(): json.loads(line);count+=1
                row.update(parse='jsonl_ok',records=count)
            elif suffix=='.toml':
                import tomllib
                tomllib.loads(text);row['parse']='toml_ok'
        except (ValueError,SyntaxError,RecursionError) as e:
            row['parse']='parse_failed_requires_review';row['parse_error']=str(e)[:300]
        if suffix in {'.py','.rs','.lean','.md','.tex','.txt','.cs','.ts','.js','.yaml','.yml'}:
            row['review_cues']={name:[i+1 for i,line in enumerate(lines) if pat.search(line)]
                                for name,pat in PATTERNS.items()}
            row['review_cues']={k:v for k,v in row['review_cues'].items() if v}
        records.append(row)
    result={'schema_version':'1.0','generated_utc':datetime.now(timezone.utc).isoformat(),
            'source_commit':inv['local_head'],'scope':inv['scope'],
            'status':'structural_scan_complete_semantic_audit_in_progress',
            'limitations':['Parsing and claim-word detection do not validate mathematical assertions, program correctness, or empirical results.',
                           'Binary documents require separate format-specific review. Duplicate keys and parse failures need contextual assessment.'],
            'counts':dict(collections.Counter(x['status'] for x in records)),
            'parse_counts':dict(collections.Counter(x.get('parse','not_applicable') for x in records)),
            'files':records}
    (DAG/'structural_review.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['status','counts','parse_counts']},indent=2))

if __name__=='__main__':main()
