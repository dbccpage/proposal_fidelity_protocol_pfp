"""Prepare two active-document navigation changes; apply only when explicitly requested.

Historical demo source, captures, source commands and receipts are never targets.
"""
from __future__ import annotations
import argparse
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREFIX = HERE / 'woland_documentation_demo_classification_navigation'


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def plans(root: Path) -> list[dict]:
    inventory = json.loads((HERE / 'woland_support_inventory.json').read_text())
    pins = {r['source_relative_path']: r for r in inventory['entries']}
    rows = []
    for relative in ['omega_engine_woland/documentation/prompt_geometry.md',
                     'omega_engine_woland/documentation/shared_teamwork.md',
                     'omega_engine_woland/context.md']:
        path = root / relative
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        newline = '\r\n' if b'\r\n' in raw else '\n'
        old = text.replace('\r\n', '\n')
        new = old
        if relative.endswith('prompt_geometry.md'):
            if sha(raw) != pins[relative]['sha256']:
                raise ValueError(f'SOURCE_PIN_CHANGED: {relative}')
            changes = {
                '[collated actual example](prompt_geometry_ide_example.json)':
                    '[collated actual example in the local PFP checkout](../../../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation/prompt_geometry_ide_example.json)',
                '[runbook](pilot035_immune_fence.md)':
                    '[Pilot 035 runbook in the local PFP checkout](../../../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation/pilot035_immune_fence.md)',
                '[`pilot035 resume` successor](pilot035_immune_fence.md#continue-a-stopped-pilot)':
                    '[`pilot035 resume` successor in the local PFP checkout](../../../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation/pilot035_immune_fence.md#continue-a-stopped-pilot)',
            }
            for before, after in changes.items():
                if new.count(before) != 1:
                    raise ValueError(f'NAVIGATION_ANCHOR_COUNT: {before}')
                new = new.replace(before, after)
            anchor = '## Demonstration scope\n'
            note = ('\nThe demonstration artifacts now belong to the sibling local\n'
                    '`proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation`\n'
                    'checkout. These cross-repository links are filesystem navigation; the\n'
                    'relocated PFP files are currently local, with no published GitHub URL\n'
                    'asserted here. Historical source locators and captured commands below\n'
                    'retain their original meaning.\n')
            if new.count(anchor) != 1:
                raise ValueError('DEMONSTRATION_HEADING_CHANGED')
            new = new.replace(anchor, anchor + note)
            historical = ('python -B omega_engine_woland/documentation/compare_prompt_preparation.py '
                          '--report .scratch/woland-geometry/live-final/report-000.json '
                          '--output .scratch/woland-geometry/offline_preparation_final.json')
            anchor = historical + '\n```\n'
            if new.count(anchor) != 1:
                raise ValueError('CAPTURED_COMPARISON_COMMAND_CHANGED')
            # -c retains the current Anomalon checkout on Python's module search path;
            # the frozen helper's old parent-depth insertion is otherwise insufficient.
            note = ('\nThe command above is the retained historical invocation. For a new\n'
                    'offline comparison after relocation, run from the Anomalon repository\n'
                    'root with its existing runtime dependencies and selected native host:\n\n'
                    '```powershell\n'
                    'python -B -c "import runpy; runpy.run_path(\'../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation/compare_prompt_preparation.py\', run_name=\'__main__\')" --report PREPARED_REPORT.json --output NEW_COMPARISON.json\n'
                    '```\n\n'
                    'Replace the uppercase file arguments with an existing prepared report\n'
                    'and a new output path. This example was not executed during relocation\n'
                    'review; it does not replay or overwrite the historical measured output.\n')
            new = new.replace(anchor, anchor + note)
            if historical not in new:
                raise AssertionError('Historical command was altered')
        elif relative.endswith('shared_teamwork.md'):
            if sha(raw) != pins[relative]['sha256']:
                raise ValueError(f'SOURCE_PIN_CHANGED: {relative}')
            before = '--pricing-snapshot omega_engine_woland/program_profiles/calibration/anthropic_pricing_20261021.json'
            if new.count(before) != 1:
                raise ValueError('ACTIVE_PRICING_COMMAND_CHANGED')
            new = new.replace(before, '--pricing-snapshot CURRENT_PRICING_SNAPSHOT.json')
            anchor = '\n`entrypoints/calibration_cli.py` compares one prompt'
            if new.count(anchor) != 1:
                raise ValueError('PRICING_NOTE_ANCHOR_CHANGED')
            note = ('\nSupply `CURRENT_PRICING_SNAPSHOT.json` from a fresh operator-reviewed\n'
                    'pricing observation for the selected deployment. The dated calibration\n'
                    'snapshot moved with the historical PFP evidence and is not a current\n'
                    'live-pricing default. Preserve any snapshot already bound to an existing\n'
                    'run; do not refresh that frozen run in place.\n')
            new = new.replace(anchor, note + anchor)
            before = ('Review tasks under\n'
                      '`program_profiles/calibration/review_*` plant false and unsupported claims among\n'
                      'true ones; their checkers compute every claim\'s truth.')
            after = ('The historical review-task bank is in the local sibling PFP checkout at\n'
                     '`../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/program_profiles/calibration/review_*`\n'
                     '(path from the Anomalon repository root). These retained fixtures plant\n'
                     'false and unsupported claims among true ones; their checkers compute\n'
                     'every claim\'s truth. The relocated PFP bank is currently local; no\n'
                     'published GitHub destination is asserted.')
            if new.count(before) != 1:
                raise ValueError('HISTORICAL_BANK_ANCHOR_CHANGED')
            new = new.replace(before, after)
        else:
            before = '(_docs/retinue_gate_integration.md)'
            if new.count(before) != 1:
                raise ValueError('CONTEXT_GUIDE_LINK_CHANGED')
            new = new.replace(before, '(documentation/retinue_gate_integration.md)')
            anchor = 'Native transition composition and trusted-checker configuration remain explicit residuals.\n'
            if new.count(anchor) != 1:
                raise ValueError('CONTEXT_INSERTION_ANCHOR_CHANGED')
            new = new.replace(anchor, anchor +
                '\nPilot and demonstration evidence is held in the [local sibling PFP support collection]'
                '(../../proposal_fidelity_protocol_pfp/pilots/anomalon_woland_support/documentation/). '
                'Reusable Woland runtime guides remain here. The relocated PFP collection is currently local; '
                'this filesystem link does not assert a published GitHub destination.\n')
        proposed = new.replace('\n', newline).encode('utf-8')
        rows.append({'path': relative, 'source_sha256': sha(raw), 'proposed_sha256': sha(proposed),
                     'source_bytes': len(raw), 'proposed_bytes': len(proposed),
                     'old_text': old, 'new_text': new, 'proposed_raw': proposed,
                     'newline': 'CRLF' if newline == '\r\n' else 'LF'})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=Path('C:/Users/a343o/source/repos/anomalon'))
    parser.add_argument('--apply', action='store_true', help='Explicit root-owned application after review')
    args = parser.parse_args()
    rows = plans(args.source_root)
    metadata = {'status': 'prepared_not_applied', 'files': []}
    patch = []
    for r in rows:
        patch += list(difflib.unified_diff(r['old_text'].splitlines(keepends=True),
                                         r['new_text'].splitlines(keepends=True),
                                         fromfile='a/' + r['path'], tofile='b/' + r['path']))
        metadata['files'].append({k: v for k, v in r.items() if k not in ('old_text', 'new_text', 'proposed_raw')})
    # Both expected snapshots are checked again before any optional write.
    for r in rows:
        if sha((args.source_root / r['path']).read_bytes()) != r['source_sha256']:
            raise ValueError('SOURCE_CHANGED_DURING_PREPARATION')
    if args.apply:
        for r in rows:
            (args.source_root / r['path']).write_bytes(r['proposed_raw'])
        metadata['status'] = 'applied'
    Path(str(PREFIX) + '.patch').write_text(''.join(patch), encoding='utf-8', newline='\n')
    Path(str(PREFIX) + '_patch.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
