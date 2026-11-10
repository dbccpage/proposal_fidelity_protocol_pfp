"""Merge explicit new semantic notes; never infer semantics from emissions."""
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
PREFIX='additional_rust_pfp_foundations'
path=HERE/(PREFIX+'_notes.json')
notes=json.loads(path.read_text(encoding='utf-8'))
scope={row['path'] for row in json.loads((HERE/(PREFIX+'_scope.json')).read_text(encoding='utf-8'))['files']}
for filename in sys.argv[1:]:
    source=(HERE/filename).resolve()
    assert source.parent==HERE and source.name.startswith(PREFIX)
    additions=json.loads(source.read_text(encoding='utf-8'))
    assert set(additions)<=scope
    for key,value in additions.items():
        assert key not in notes or notes[key]==value, 'Conflicting preexisting semantic review: '+key
        assert isinstance(value,str) and value
        notes[key]=value
path.write_text(json.dumps(notes,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'full_source_reads':len(notes),'remaining':len(scope)-len(notes)}))
