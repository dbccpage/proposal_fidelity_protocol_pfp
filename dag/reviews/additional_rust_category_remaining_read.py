"""Display complete residual bodies; verify only repeated capacity boilerplate.

This tool grants no reading credit. A reviewer must read all displayed residual
lines and assess context before recording a full read in the checkpoint notes.
"""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews'
PREFIX='additional_rust_category_remaining'
BASE='code/rust/core_category_theory/src/natural_trans.rs'
sha=lambda b:hashlib.sha256(b).hexdigest()
scope=json.loads((REV/(PREFIX+'_scope.json')).read_text());pins={x['path']:x['sha256'] for x in scope['files']}
base_bytes=(ROOT/BASE).read_bytes();assert sha(base_bytes)==pins[BASE]
base_lines=base_bytes.decode().splitlines()
def capacity_blocks(lines):
    result=[]
    starts=[i for i,x in enumerate(lines) if x=='/// Bounded admission record for module-level L4 production boundary verification.']
    for start in starts:
        stop=next((i for i in range(start+1,len(lines)) if lines[i]=='#[cfg(test)]'),len(lines))
        result.append((start,stop))
    for i,x in enumerate(lines):
        if re.fullmatch(r'mod l4_boundary_tests_[0-9a-f]{8} \{',x) and i>0 and lines[i-1]=='#[cfg(test)]':
            result.append((i-1,len(lines)))
    return result
def normalized(lines):
    return re.sub(r'(?<=BoundaryRecord)[0-9a-f]{8}|(?<=BoundaryError)[0-9a-f]{8}|(?<=l4_boundary_tests_)[0-9a-f]{8}', 'HASH', '\n'.join(lines)).rstrip()
baseline=[(a,z,normalized(base_lines[a:z])) for a,z in capacity_blocks(base_lines)]
ledger_path=REV/(PREFIX+'_reading_transfers.json');ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else []
for name in sys.argv[1:]:
    rel='code/rust/core_category_theory/'+name;b=(ROOT/rel).read_bytes();assert sha(b)==pins[rel]
    lines=b.decode().splitlines();omitted=set();transfers=[]
    for a,z in capacity_blocks(lines):
        match=next(((ba,bz) for ba,bz,body in baseline if normalized(lines[a:z])==body),None)
        if match:
            ba,bz=match;omitted.update(range(a,z));transfers.append({'base_path':BASE,'base_sha256':pins[BASE],'base_lines':[ba+1,bz],
              'target_lines':[a+1,z],'method':'exact_lines_after_renaming_only_BoundaryRecord_BoundaryError_and_l4_boundary_tests_hex_suffixes_and_ignoring_trailing_blank_lines',
              'normalized_sha256':sha(normalized(lines[a:z]).encode()),'target_identifiers':sorted(set(re.findall(r'(?:BoundaryRecord|BoundaryError|l4_boundary_tests_)[0-9a-f]{8}', '\n'.join(lines[a:z]))))})
    print('\nFILE',rel,'SHA256',sha(b),'LINES',len(lines))
    print('VERIFIED_REPEATED_BLOCKS',json.dumps(transfers))
    for i,line in enumerate(lines):
        if i not in omitted:print(f'{i+1}: {line}')
    ledger=[x for x in ledger if x['path']!=rel]
    ledger.append({'path':rel,'sha256':sha(b),'lines':len(lines),'displayed_residual_line_numbers':[i+1 for i in range(len(lines)) if i not in omitted],
                   'transfers':transfers,'full_read_credit':False,'note':'Display and exact renaming bookkeeping only; substantive review must be separately recorded.'})
ledger_path.write_text(json.dumps(ledger,indent=2)+'\n')
