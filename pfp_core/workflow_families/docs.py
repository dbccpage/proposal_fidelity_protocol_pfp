"""Generate the Wiki page and DAG records for every registered family.

    python -m pfp_core.workflow_families.docs        # write pages and records
    python -m pfp_core.workflow_families.docs --check  # fail if anything is stale

Pages are rendered from the family's spec and docstring, the DAG node's
process and mathematics, and a fresh offline run of its fixtures, so the page
cannot drift from the code. The command then:

* writes ``wiki/Workflow-WFn.md`` for each family and ``wiki/Workflow-Families.md``;
* pins each page's SHA-256 in ``dag/wiki/workflow_documentation.json``;
* marks the node ``implemented`` in ``dag/reviews/workflows_audit.json`` with its
  runner source and tests.

Run ``python dag/build_dags.py`` afterwards to rebuild ``dag/workflows_dag.json``.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
import textwrap
from pathlib import Path

from .. import REPO_ROOT
from .base import POSITIVE, run_fixture
from .registry import load

REPO_URL = 'https://github.com/dbccpage/proposal_fidelity_protocol_pfp'
WIKI_URL = REPO_URL + '/wiki/'
TESTS = 'pfp_core/workflow_families/tests/test_families.py'
AUDIT = REPO_ROOT / 'dag' / 'reviews' / 'workflows_audit.json'
DOCS = REPO_ROOT / 'dag' / 'wiki' / 'workflow_documentation.json'
HUB = 'Workflow-Families'


def _tree(path: str) -> str:
    kind = 'blob' if path.endswith('.py') else 'tree'
    return f'[`{path}`]({REPO_URL}/{kind}/main/{path})'


def _docstring(cls) -> tuple[str, str]:
    doc = inspect.cleandoc(cls.__doc__ or '')
    head, _, body = doc.partition('\n')
    head = head.split('. ', 1)[1] if head.startswith(cls.spec.wf_id + '. ') else head
    return head.strip(), textwrap.dedent(body).strip()


def _links(ids) -> str:
    return ', '.join(f'[{i}](Workflow-{i}.md)' for i in ids) or 'nothing'


def render(cls, node: dict, rows: list[dict]) -> str:
    s = cls.spec
    head, body = _docstring(cls)
    module = inspect.getmodule(cls).__name__.replace('.', '/') + '.py'
    positive = [r for r in rows if r['expected'] in POSITIVE]
    negative = [r for r in rows if r['expected'] not in POSITIVE]
    lines = [
        f'# {s.wf_id}: {s.name}',
        '',
        f'**Layer:** {s.layer} · **Builds on:** {_links(s.depends_on)} · '
        f'**Merges into:** {s.merge_into or "nothing"} · **Kind:** {node["kind"].replace("_", " ")}',
        '',
        f'**Code:** {_tree(module)} (`{cls.__name__}`) · **Folder:** {_tree(s.folder)} · **Tests:** {_tree(TESTS)}',
        '',
        f'> {head}',
        '',
        body,
        '',
        '## Procedure',
        '',
        *[f'{i}. {step}' for i, step in enumerate(node.get('process', []), 1)],
        '',
        '## Design mathematics',
        '',
        'From the DAG node. The runner checks the instance described above; items it does not exercise '
        'remain design.',
        '',
        *[f'- {m}' for m in node.get('math', [])],
        '',
        '## Host check',
        '',
        f'`{s.host_check_id}`. Only this check can certify. Proposers, detectors and adapters carry '
        "authority effect `None`; a reply is evidence for the check, never a verdict.",
        '',
        '## Run it offline',
        '',
        'No model call and no spend. From the repository root:',
        '',
        '```powershell',
        f'python -m pfp_core.workflow_families run {s.wf_id}',
        f'python -m pytest {TESTS} -q -k "{s.wf_id}-"',
        '```',
        '',
        '| Fixture | Expected | Observed | Code |',
        '| --- | --- | --- | --- |',
        *[f'| `{r["fixture"]}` | {r["expected"]} | {r["verdict"]} | `{r["code"]}` |' for r in rows],
        '',
        '## With a model',
        '',
        '`execute(bundle, budget=..., proposer=...)` takes any proposer. `CallableProposer(fn)` wraps a local '
        'open-weight runner or a provider client; every reply is reserved and settled against one '
        '`WholeRunBudget` before the host reads it, and a prompt that contains a sealed value is refused '
        'before dispatch. No live or local model run of this family is recorded yet.',
        '',
        '## Claim scope',
        '',
        f'- **Supports:** the host check certifies {len(positive)} positive fixture(s) and refuses '
        f'{len(negative)} adversarial fixture(s), deterministically, offline, at zero spend.',
        '- **Does not support:** any accuracy, cost or time advantage for a model run through this workflow.',
        f'- **Narrowest claim:** on these fixtures, `{s.host_check_id}` separates the accepted outcomes from '
        'the listed failure modes.',
        f'- **Next test:** a matched local or live campaign of {s.wf_id} against WF1 direct on held-out '
        'instances of the same family, with equal token and spend caps.',
        '',
        f'Back to [all workflow families]({HUB}.md).',
        '',
    ]
    return '\n'.join(lines)


def render_hub(registry, nodes) -> str:
    rows = [f'| [{w}](Workflow-{w}.md) | {c.spec.name} | {c.spec.layer} | {", ".join(c.spec.depends_on)} | '
            f'`{c.spec.host_check_id}` |' for w, c in sorted(registry.items(), key=lambda kv: (kv[1].spec.layer,
                                                                                              kv[1].spec.number))]
    return '\n'.join([
        '# Workflow families WF6-WF49',
        '',
        'Each family is one class in `pfp_core/workflow_families/` on a shared runtime: one spec, one '
        'budget per run, one host check that alone can certify, and offline fixtures that must be accepted or '
        'refused. WF1-WF5 keep their own runners (see [Workflows](Workflows.md)).',
        '',
        '```powershell',
        'python -m pfp_core.workflow_families list',
        'python -m pfp_core.workflow_families check-all',
        '```',
        '',
        '| WF | Family | Layer | Builds on | Host check |',
        '| --- | --- | ---: | --- | --- |',
        *rows,
        '',
        'Every page states what its fixtures support and what they do not. No family has a recorded live or '
        'local model campaign yet.',
        '',
    ])


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _encode(path: Path, text: str) -> bytes:
    """UTF-8 bytes, keeping CRLF where the existing file uses it (the audit JSON is pinned that way)."""
    data = text.encode('utf-8')
    if path.exists() and b'\r\n' in path.read_bytes()[:4096]:
        data = data.replace(b'\n', b'\r\n')
    return data


def build(check: bool) -> list[str]:
    registry = load()
    audit = json.loads(AUDIT.read_text(encoding='utf-8'))
    nodes = {n['id']: n for n in audit['registry']['family_nodes']}
    docs = json.loads(DOCS.read_text(encoding='utf-8'))
    pages: dict[Path, str] = {}
    entries = {e['node_id']: e for e in docs['entries']}
    for wf_id, cls in registry.items():
        fam = cls()
        rows = []
        for name, (_bundle, expected) in fam.fixtures().items():
            out = run_fixture(fam, name)
            rows.append({'fixture': name, 'expected': expected, 'verdict': out.verdict, 'code': out.code})
        text = render(cls, nodes[wf_id], rows)
        page = f'wiki/Workflow-{wf_id}.md'
        pages[REPO_ROOT / page] = text
        entries[wf_id] = {**entries.get(wf_id, {}), 'node_id': wf_id, 'page': page, 'page_sha256': _sha(text),
                          'wiki_url': WIKI_URL + f'Workflow-{wf_id}',
                          'evidence_status': 'offline_fixture_checks_only_no_model_campaign'}
        entries[wf_id].setdefault('publication_status', 'source_only_not_yet_published')
        node = nodes[wf_id]
        node.update(status='implemented', runner_source=inspect.getmodule(cls).__name__.replace('.', '/') + '.py',
                    runner_class=cls.__name__, tests=TESTS,
                    audited_availability='offline_family_runner_with_fixture_tests')
    pages[REPO_ROOT / 'wiki' / f'{HUB}.md'] = render_hub(registry, nodes)
    order = {e['node_id']: i for i, e in enumerate(docs['entries'])}
    docs['entries'] = sorted(entries.values(), key=lambda e: (order.get(e['node_id'], 10_000),
                                                              int(e['node_id'][2:]) if e['node_id'][2:].isdigit()
                                                              else 0))
    outputs = {**pages,
               DOCS: json.dumps(docs, indent=2, ensure_ascii=False) + '\n',
               AUDIT: json.dumps(audit, indent=2, ensure_ascii=False) + '\n'}
    encoded = {p: _encode(p, t) for p, t in outputs.items()}
    stale = [p.relative_to(REPO_ROOT).as_posix() for p, data in encoded.items()
             if not p.exists() or p.read_bytes() != data]
    if not check:
        for p, data in encoded.items():
            p.write_bytes(data)
    return stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog='python -m pfp_core.workflow_families.docs')
    parser.add_argument('--check', action='store_true', help='report stale outputs without writing')
    args = parser.parse_args(argv)
    stale = build(args.check)
    print(json.dumps({'stale' if args.check else 'written': stale}, indent=2))
    return 1 if args.check and stale else 0


if __name__ == '__main__':
    sys.exit(main())
