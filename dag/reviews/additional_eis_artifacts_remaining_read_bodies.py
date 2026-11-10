from pathlib import Path
import hashlib,json,sys
R=Path(__file__).resolve().parents[2];P=R/'dag/reviews/additional_eis_artifacts_remaining'
def h(b):return hashlib.sha256(b).hexdigest()
manifest=json.loads(Path(str(P)+'_body_transfer_manifest.json').read_text(encoding='utf8'))
for key in ('catalog','warning_logs'):
 row=manifest[key]['source'];assert h((R/row['path']).read_bytes())==row['sha256']
lp=Path(str(P)+'_body_read_ledger.json');ledger=json.loads(lp.read_text()) if lp.exists() else []
for arg in sys.argv[1:]:
 parts=arg.split(':');kind=parts[0]
 if kind=='catalog':file=R/manifest['catalog']['residual_artifact'];expected=manifest['catalog']['residual_sha256'];mode='lines'
 elif kind=='base221':file=R/manifest['warning_logs']['base_artifact'];expected=manifest['warning_logs']['base_decoded_sha256'];mode='characters'
 elif kind.startswith('delta'):
  d=next(x for x in manifest['warning_logs']['deltas'] if x['raw_line']==int(kind[5:]));file=R/d['delta_artifact'];expected=d['delta_sha256'];mode='lines'
 else:raise ValueError(kind)
 raw=file.read_bytes();assert h(raw)==expected;value=raw.decode();parts_data=value.splitlines() if mode=='lines' else value
 start=int(parts[1]) if len(parts)>1 else (1 if mode=='lines' else 0);end=int(parts[2]) if len(parts)>2 else len(parts_data)
 assert (1 if mode=='lines' else 0)<=start<=end<=len(parts_data)
 print(f'BODY {kind} SHA {expected} {mode} {start}..{end} total {len(parts_data)}')
 if mode=='lines':
  for n in range(start,end+1):print(f'{n}: {parts_data[n-1]}')
 else:print(value[start:end])
 ledger.append({'artifact':str(file.relative_to(R)).replace('\\','/'),'sha256':expected,'mode':mode,'range':[start,end],'range_convention':'inclusive 1-based lines' if mode=='lines' else 'half-open 0-based Unicode characters','total':len(parts_data),'review_credit':'Display only; substantive assessment and no truncation required before transfer credit.'})
lp.write_text(json.dumps(ledger,indent=2)+'\n')
