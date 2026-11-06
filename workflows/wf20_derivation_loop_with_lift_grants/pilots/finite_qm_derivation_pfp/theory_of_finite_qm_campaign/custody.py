"""Exact filename-migration custody; never grants mathematical acceptance.

Historical pins stay historical. A migrated artifact must match both captured
versions and the canonical filename-only rewrite between them. No hash waiver,
arbitrary text replacement, rounding or status promotion is supported.
"""
import hashlib
import re
from pathlib import Path as _FilesystemPath
import sys as _contract_sys
_contract_sys.path.insert(0, str(_FilesystemPath(__file__).resolve().parents[2] / "scripts"))
from contract_scores import RecordPath as Path
from pathlib import PurePosixPath
from exact_json import load, require

SCHEMA = 'omega.pfp.filename-custody.v1'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def canonical_filename(name):
    stem, suffix = name.rsplit('.', 1)
    return re.sub('[^a-z0-9]+', '_', stem.lower()).strip('_') + '.' + suffix.lower()


def rewrite(data, renames):
    """Replace whole known basename tokens, not numbers, prose or arbitrary spans."""
    for before, after in renames.items():
        require(type(before) is str and type(after) is str, 'custody:filename_type')
        require(re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:md|yaml)', before) is not None,
                'custody:filename')
        require(before != after and canonical_filename(before) == after,
                'custody:noncanonical_rename')
    if not renames:
        return data
    mapping = {a.encode(): b.encode() for a, b in renames.items()}
    pattern = re.compile(rb'(?<![A-Za-z0-9_.-])(?:' +
                         b'|'.join(re.escape(x) for x in sorted(mapping, key=len, reverse=True)) +
                         rb')(?!(?:[A-Za-z0-9_-]|\.[A-Za-z0-9_.-]))')
    return pattern.sub(lambda m: mapping[m.group()], data)


def migrate(data, renames, line_endings):
    require(line_endings in ('preserve', 'crlf_to_lf'), 'custody:line_endings')
    result = rewrite(data, renames)
    if line_endings == 'crlf_to_lf':
        require(b'\r\n' in result, 'custody:no_crlf_to_convert')
        result = result.replace(b'\r\n', b'\n')
    return result


class Custody:
    def __init__(self, root):
        self.root = Path(root).resolve()
        ledger = load(self.root / 'dag/pfp/filename_custody.json')
        require(type(ledger) is dict and ledger.get('schema_id') == SCHEMA and
                ledger.get('authority_effect') == 'None', 'custody:schema')
        require(type(ledger.get('snapshot_root')) is str and
                ledger['snapshot_root'].startswith('dag/results/custody/'),
                'custody:snapshot_root')
        self.path(ledger['snapshot_root'])
        require(sha(self.path('dag/pfp/prompt_audit.json').read_bytes()) ==
                ledger['historical_audit_sha256'], 'custody:historical_audit_changed')
        self.entries, self.used = {}, {}
        require(type(ledger['artifacts']) is list and bool(ledger['artifacts']),
                'custody:artifacts')
        for entry in ledger['artifacts']:
            require(type(entry) is dict and entry.get('kind') in ('prompt', 'paper'),
                    'custody:artifact_kind')
            string_fields = {'kind', 'path', 'historical_path', 'historical_sha256',
                             'historical_git_blob', 'historical_snapshot', 'current_sha256',
                             'current_git_blob', 'current_snapshot', 'line_endings'}
            require(set(entry) == string_fields | {'uses', 'filename_renames'} and
                    all(type(entry[k]) is str for k in string_fields), 'custody:entry_shape')
            for field in ('historical_sha256', 'current_sha256', 'historical_git_blob',
                          'current_git_blob'):
                require(re.fullmatch('[0-9a-f]{' + ('40' if field.endswith('git_blob') else '64') +
                                     '}', entry[field]) is not None, 'custody:digest_type')
            self.path(entry['historical_path'])
            key = (entry['kind'], entry['path'])
            require(key not in self.entries, 'custody:duplicate_artifact')
            current = self.path(entry['path'])
            require(entry['path'].startswith('dag/prompts/' if entry['kind'] == 'prompt'
                                             else 'dag/derivations/'), 'custody:artifact_path')
            require(current.name == canonical_filename(PurePosixPath(entry['historical_path']).name),
                    'custody:canonical_path')
            require(PurePosixPath(entry['path']).parent ==
                    PurePosixPath(entry['historical_path']).parent, 'custody:path_parent')
            require(type(entry['uses']) is list and bool(entry['uses']) and
                    all(type(x) is str for x in entry['uses']) and
                    len(set(entry['uses'])) == len(entry['uses']), 'custody:uses')
            require(type(entry['filename_renames']) is dict,
                    'custody:rename_map')
            for name in ('historical_snapshot', 'current_snapshot'):
                require(entry[name].startswith(ledger['snapshot_root'] + '/'),
                        'custody:snapshot_scope')
            before = self.path(entry['historical_snapshot']).read_bytes()
            after = self.path(entry['current_snapshot']).read_bytes()
            require(sha(before) == entry['historical_sha256'] and
                    blob(before) == entry['historical_git_blob'], 'custody:historical_bytes')
            require(sha(after) == entry['current_sha256'] and
                    blob(after) == entry['current_git_blob'], 'custody:current_snapshot')
            require(before != after and
                    migrate(before, entry['filename_renames'], entry['line_endings']) == after,
                    'custody:not_filename_only')
            require(sha(current.read_bytes()) == entry['current_sha256'],
                    'custody:current_bytes')
            self.entries[key] = entry

    def path(self, name):
        require(type(name) is str and bool(name) and '\\' not in name,
                'custody:path_type')
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and '..' not in relative.parts and ':' not in name,
                'custody:path_escape')
        path = (self.root / name).resolve()
        require(path != self.root and self.root in path.parents, 'custody:path_escape')
        return path

    def matches(self, kind, path, historical_sha256, node):
        entry = self.entries.get((kind, path))
        if entry is None:
            source = self.path(path)
            return source.is_file() and sha(source.read_bytes()) == historical_sha256
        require(entry['historical_sha256'] == historical_sha256 and node in entry['uses'],
                'custody:historical_binding')
        self.used.setdefault((kind, path), set()).add(node)
        # Recheck live bytes: a file may change after construction of this object.
        return sha(self.path(path).read_bytes()) == entry['current_sha256']

    def finish(self):
        require(set(self.used) == set(self.entries), 'custody:unused_or_missing_artifact')
        for key, entry in self.entries.items():
            require(self.used[key] == set(entry['uses']), 'custody:use_coverage')
