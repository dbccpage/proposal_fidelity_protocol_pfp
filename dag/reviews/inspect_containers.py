"""Read bounded archive/notebook/database contents without executing embedded code.

These are format/custody observations, never retrospective proof of a live run.
No archive member is extracted, no notebook is executed and databases are read-only.
"""
from __future__ import annotations
import ast
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import sqlite3
import zipfile

ROOT = Path(__file__).resolve().parents[2]
DAG = ROOT / 'dag'
MAX_MEMBER = 64 * 1024 * 1024
MAX_ARCHIVE = 512 * 1024 * 1024

def main():
    inventory = json.loads((DAG / 'file_inventory.json').read_text(encoding='utf-8'))
    rows = []
    for entry in inventory['files']:
        path = ROOT / entry['path']
        if path.suffix.lower() not in ('.zip', '.gz', '.sqlite3', '.sqlite', '.db', '.ipynb'):
            continue
        row = {'path': entry['path'], 'sha256': entry['sha256'], 'semantic_review_complete': False}
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('source drift')
            if path.suffix == '.zip':
                members = []; consumed = 0
                with zipfile.ZipFile(path) as archive:
                    for item in archive.infolist():
                        normalized = item.filename.replace('\\', '/')
                        unsafe = normalized.startswith('/') or '..' in PurePosixPath(normalized).parts or ':' in normalized
                        m = {'name': item.filename, 'size_bytes': item.file_size, 'unsafe_extraction_path': unsafe}
                        if item.is_dir():
                            m['status'] = 'directory'
                        elif item.file_size > MAX_MEMBER or consumed + item.file_size > MAX_ARCHIVE:
                            m['status'] = 'not_read_size_bound'
                        else:
                            with archive.open(item) as stream:
                                data = stream.read(MAX_MEMBER + 1)
                            if len(data) > MAX_MEMBER:
                                raise ValueError('member exceeded declared bound')
                            consumed += len(data)
                            m.update(status='bytes_read_crc_checked', sha256=hashlib.sha256(data).hexdigest())
                        members.append(m)
                row.update(status='bounded_archive_custody_inspection', members=members, uncompressed_bytes_read=consumed)
            elif path.suffix == '.gz':
                with gzip.open(path, 'rb') as stream:
                    data = stream.read(MAX_MEMBER + 1)
                row.update(status='decompressed_bytes_read' if len(data) <= MAX_MEMBER else 'partial_size_bound', decompressed_bytes_read=len(data), decompressed_sha256=hashlib.sha256(data).hexdigest())
            elif path.suffix == '.ipynb':
                book = json.loads(path.read_text(encoding='utf-8'))
                cells = []
                for index, cell in enumerate(book.get('cells', [])):
                    source = cell.get('source', '')
                    if isinstance(source, list):
                        source = ''.join(source)
                    c = {'index': index, 'type': cell.get('cell_type'), 'source_sha256': hashlib.sha256(source.encode()).hexdigest(), 'lines': len(source.splitlines()), 'recorded_outputs': len(cell.get('outputs', []))}
                    if c['type'] == 'code':
                        try:
                            tree = ast.parse(source)
                            c['syntax'] = 'python_ast_ok'
                            c['definitions'] = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
                        except SyntaxError as exc:
                            c.update(syntax='not_python_or_syntax_error', line=exc.lineno)
                    cells.append(c)
                row.update(status='notebook_structure_and_all_cell_sources_read_not_executed', cells=cells)
            else:
                uri = path.resolve().as_uri() + '?mode=ro&immutable=1'
                with sqlite3.connect(uri, uri=True) as db:
                    db.execute('PRAGMA query_only=ON')
                    db.execute('PRAGMA trusted_schema=OFF')
                    integrity = [r[0] for r in db.execute('PRAGMA integrity_check')]
                    tables = []
                    for name, definition in db.execute("SELECT name,sql FROM sqlite_master WHERE type='table' ORDER BY name"):
                        quoted = '"' + name.replace('"', '""') + '"'
                        tables.append({'name': name, 'schema': definition, 'row_count': db.execute('SELECT COUNT(*) FROM ' + quoted).fetchone()[0]})
                row.update(status='read_only_integrity_schema_and_row_counts', integrity=integrity, tables=tables, record_values_semantically_reviewed=False)
        except Exception as exc:
            row.update(status='inspection_error', error_class=type(exc).__name__, error=str(exc)[:300])
        rows.append(row)
    from collections import Counter
    result = {'schema_version': '1.0', 'source_commit': inventory['local_head'], 'limits': 'Structural and custody inspection only. Historical outputs are not newly executed evidence. Archive members are not automatically added to the tracked-file review scope.', 'counts': dict(Counter(r['status'] for r in rows)), 'files': rows}
    (DAG / 'reviews' / 'container_artifacts.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps(result['counts']))

if __name__ == '__main__':
    main()
