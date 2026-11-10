"""Emit exact base text and lossless complete line changes for score review."""
import difflib
import hashlib
import json
import sys
from pathlib import Path
from additional_lab_clients_formal_read import ROOT, SCOPE, INDEX

families = {
    "cs": [r['path'] for r in SCOPE if r['path'].startswith('csharp/') and r['path'].endswith('.contract.score.json')],
    "lab": [r['path'] for r in SCOPE if r['path'].startswith('pfp_lab/') and r['path'].endswith('.contract.score.json')],
}
def show(group, start, end):
    paths = families[group]
    basepath = paths[0]
    base = (ROOT / basepath).read_bytes().decode('utf-8').splitlines(keepends=True)
    for path in paths[start:end]:
        raw = (ROOT / path).read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        assert sha == INDEX[path]['sha256']
        target = raw.decode('utf-8').splitlines(keepends=True)
        print('FILE',path,'SHA256',sha,'LINES',len(target),'BASE',basepath)
        if path == basepath:
            for i,line in enumerate(target,1): print(f'{i}: {line}',end='')
        else:
            out=[]
            for tag,i,j,k,l in difflib.SequenceMatcher(a=base,b=target,autojunk=False).get_opcodes():
                if tag == 'equal': out.extend(base[i:j])
                else:
                    print(f'REPLACE BASE {i+1}..{j} WITH TARGET {k+1}..{l}')
                    for n,line in enumerate(target[k:l],k+1): print(f'{n}: {line}',end='')
                    out.extend(target[k:l])
            assert ''.join(out).encode('utf-8') == raw
        print('END_FILE')
if __name__ == '__main__':
    show(sys.argv[1],int(sys.argv[2]),int(sys.argv[3]))
