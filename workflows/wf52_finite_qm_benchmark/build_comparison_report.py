"""Validate and combine all frozen benchmark attempts without hiding failures."""
from pathlib import Path
import json
from statistics import mean
from summarize_runs import summarize

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
experiments = [HERE/name for name in ('pilot_20261110', 'hamiltonian_pilot_20261110',
               'hamiltonian_large_model_20261110', 'length_control_20261110', 'section_control_20261110',
               'model_control_20261110', 'model_control_repaired_20261110', 'deepseek_critique_20261110',
               'charpoly_pilot_20261110')]
paths, grades, planned = [], {}, []
for folder in experiments:
    paths.extend(sorted((folder/'runs').glob('*/run.json')))
    paths.extend(sorted((folder/'repair_runs').glob('*/run.json')))
    grade_path = folder/'grades.json'
    if grade_path.exists():
        incoming = json.loads(grade_path.read_text(encoding='utf-8'))
        if set(grades) & set(incoming):
            raise ValueError('Duplicate grade identity')
        grades.update(incoming)
    for name in ('manifest.json', 'repair_manifest.json'):
        manifest_path = folder/name
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            planned.extend(item['run_id'] for item in manifest['runs'])
result = summarize(paths, grades)
observed = {row['run_id'] for row in result['raw_runs']}
result['planned_run_count'] = len(planned)
result['planned_runs_without_frozen_receipt'] = sorted(set(planned)-observed)
result['interpretation'] += ' Models/endpoints and workflow instructions differ across campaigns; comparisons across them are exploratory. Refusals receive zero delivered-solution points, distinct from false asserted answers.'
(HERE/'results_summary.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')

pilot = HERE/'hamiltonian_pilot_20261110'
specific = summarize(sorted((pilot/'runs').glob('*/run.json')), grades)
(pilot/'graded_results.json').write_text(json.dumps(specific, indent=2)+'\n', encoding='utf-8')
if len(specific['raw_runs']) != 8 or any(row['score'] is None for row in specific['raw_runs']):
    raise ValueError('Wiki comparison requires all eight graded frozen attempts')
table = []
for plan in ('direct', 'hamiltonian_checked_v1', 'hamiltonian_ungated_v1', 'hamiltonian_host_matrix_v1'):
    group = [row for row in specific['raw_runs'] if row['plan']==plan]
    scores = ', '.join(str(row['score']) for row in group)
    table.append(f"| `{plan}` | {scores} | ${mean(row['money_usd'] for row in group):.7f} | "
                 f"{mean(row['input_tokens'] for row in group):,.1f} / {mean(row['output_tokens'] for row in group):,.1f} | "
                 f"{mean(row['wall_time_seconds'] for row in group):.1f} | "
                 f"{sum(row['status']=='completed' for row in group)}/2 |")
section = '''## Measured eight-attempt pilot

All eight runs on `openai/gpt-4o-mini` through the `openai` OpenRouter endpoint are frozen and graded. Total recorded provider cost was **USD 0.007831**, with no unresolved charges. None delivered a complete solution.

| Plan | Scores /100 | Mean recorded cost | Mean input / output tokens | Mean wall seconds | Delivered answers |
| --- | --- | ---: | ---: | ---: | ---: |
'''+'\n'.join(table)+'''

Both checked attempts failed the exact matrix check, failed their one correction and refused synthesis. Their zero scores mean no delivered solution; they are not wrong mathematical assertions. Both ungated attempts continued from incorrect representations. The host-derived control supplied a correct representation, but the solver still produced incorrect or unfinished mathematics. All six delivered answers stopped normally, so their omissions cannot be blamed on truncation.

The checker demonstrated its narrow admission property in these runs. It did **not** establish a final-answer accuracy benefit. A correct intermediate artifact does not ensure that a model uses it correctly. Two samples on one problem, unequal total resources and the direct arm's different instruction do not support a general ranking.

The existing rubric was retained unchanged and applied to final answer text after freezing. Detailed criterion evidence and hash-bound grades are in `hamiltonian_pilot_20261110/grades.json`, `criterion_evidence.json` and `evaluation_validation.json`. This is a documented model-assisted mathematical review, not a formal or independent human certification. The private reference answer was not accessed. A separate larger-model comparison uses unchanged workflow prompts; it is exploratory and is retained separately from these eight runs.
'''
large = HERE/'hamiltonian_large_model_20261110'
large_result = summarize(sorted((large/'runs').glob('*/run.json')), grades)
if len(large_result['raw_runs']) == 3 and all(row['score'] is not None for row in large_result['raw_runs']):
    (large/'graded_results.json').write_text(json.dumps(large_result, indent=2)+'\n', encoding='utf-8')
    section += '''
## Exploratory larger-model comparison

Three further frozen attempts used `qwen/qwen3-235b-a22b-2507` through `deepinfra/fp8`, with unchanged workflow prompts and 4,000-token final-output ceilings. Total settled cost was **USD 0.005117**.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Outcome |
| --- | ---: | ---: | ---: | ---: | --- |
'''
    for row in large_result['raw_runs']:
        outcome = 'Refused representation' if row['status']=='representation_refused' else 'Length-truncated'
        section += f"| `{row['plan']}` | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} | {outcome} |\n"
    section += '''
The host-assisted answer preserved the correct Hamiltonian and eigenvalues, while the direct answer introduced an incorrect coupling. Both exhausted their output budget during the spectrum/projector section. The 16-versus-10 partial score difference is one observation, not a reproducible workflow advantage; neither completed the task.

Across both Hamiltonian experiments, three checked attempts refused synthesis after their one correction remained wrong. This confirms the observed gate behavior, not full-solution performance. The longer model responses also show that the 120-second transport setting is a socket timeout, not a total request deadline.

The harness accepts `live_campaign.py prepare --max-output-tokens N`; the USD0.10 ledger remains unchanged. Fixed adaptation-stage ceilings remain in force even when the campaign ceiling is higher. The configurable allowance passed the expanded 171-test suite plus 27 subtests. The original 4,000-token default is not a requirement of the problem.
'''
length_folder = HERE/'length_control_20261110'
length_result = summarize(sorted((length_folder/'runs').glob('*/run.json')), grades)
section += '\n## Output-allowance control\n\n'
if len(length_result['raw_runs']) == 1 and length_result['raw_runs'][0]['score'] is not None:
    (length_folder/'graded_results.json').write_text(json.dumps(length_result, indent=2)+'\n', encoding='utf-8')
    section += '''The direct workflow, exact public seed, Qwen235B model and DeepInfra endpoint are unchanged. The new run raises the requested output ceiling from 4,000 to 16,000 tokens. Both runs remain under the USD0.10 whole-run cap.

| Requested output ceiling | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Finish reasons |
| ---: | ---: | ---: | ---: | ---: | --- |
'''
    controls = [row for row in large_result['raw_runs'] if row['plan']=='direct'] + length_result['raw_runs']
    for row in controls:
        section += f"| {row['control_max_output_tokens']:,} | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} | {row['finish_reason_counts']} |\n"
    section += '''
The larger response earns 62/100 for substantial work on parts 1–3, compared with 10/100 in the earlier short attempt. It voluntarily requests another message before the thermal section and numerical example. It uses 11,241 tokens and stops normally, so this omission is not a provider-reported output cutoff. The final answer also retains parameter-branch defects.

This is one exploratory sample at each allowance, not a paired random-seed experiment or an established workflow advantage. The larger ceiling changes available resources; it is not evidence about PFP/EIS/PCIV/OPERADS efficacy. Grading uses the unchanged rubric after freezing, with no evaluator feedback. Criterion evidence and grade bindings are under `length_control_20261110/`. Combined summaries keep different control output allowances in separate groups. The later [five-part allocation control](Workflow-QM-Sections.md) scored 26/100 at greater recorded cost.
'''
else:
    section += 'The 16,000-token direct control has no published graded outcome yet. Its manifest and eventual frozen receipt are under `length_control_20261110/`; no improvement is inferred from preparation or dispatch.\n'
model_folder = HERE/'model_control_repaired_20261110'
model_result = summarize(sorted((model_folder/'runs').glob('*/run.json')), grades)
if len(model_result['raw_runs']) == 1 and model_result['raw_runs'][0]['score'] is not None:
    (model_folder/'graded_results.json').write_text(json.dumps(model_result, indent=2)+'\n', encoding='utf-8')
    section += '''
## Exploratory model capability control

The direct prompt and 16,000-token ceiling were retained while changing to DeepSeek V3.2 through AtlasCloud FP8. This tests another model/endpoint, not a new workflow. Availability and tariffs were checked against [OpenRouter's model listing](https://openrouter.ai/deepseek/deepseek-v3.2) and the frozen live endpoint metadata before dispatch.

| Model / endpoint | Score /100 | Recorded cost | Input / output tokens | Wall seconds |
| --- | ---: | ---: | ---: | ---: |
'''
    for label, rows in [('Qwen235B / DeepInfra FP8', length_result['raw_runs']),
                        ('DeepSeek V3.2 / AtlasCloud FP8', model_result['raw_runs'])]:
        for row in rows:
            section += f"| {label} | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} |\n"
    section += '''
The DeepSeek answer supplies the thermal calculation and numerical example, but retains an incorrect CHSH maximum and exceptional-case gaps. Neither answer is a complete correct solution. One sample cannot establish a model ranking; the changed endpoint and model defaults are part of this exploratory comparison.

An earlier infrastructure attempt made zero model dispatches and cost zero: its preflight provider instance retained an unused prepared request, so the guard refused reuse. That failure remains in `model_control_20261110/` with zero delivered-solution points and no assessed model mathematics. The corrected attempt used a fresh provider instance in a separately frozen campaign. Full accounting totals include both attempts; the table above compares delivered model answers only.
'''
page = ROOT/'wiki/Workflow-QM-Hamiltonian.md'
text = page.read_text(encoding='utf-8')
start, end = '<!-- BEGIN MEASURED RESULTS -->', '<!-- END MEASURED RESULTS -->'
before, rest = text.split(start, 1)
_, after = rest.split(end, 1)
page.write_text(before+start+'\n'+section+end+after, encoding='utf-8')
sections_folder = HERE/'section_control_20261110'
sections_result = summarize(sorted((sections_folder/'runs').glob('*/run.json')), grades)
if len(sections_result['raw_runs']) == 1 and sections_result['raw_runs'][0]['score'] is not None:
    (sections_folder/'graded_results.json').write_text(json.dumps(sections_result, indent=2)+'\n', encoding='utf-8')
    comparison = '''## Measured comparison

Both attempts use the same public seed, Qwen235B model and DeepInfra endpoint. The direct run permits 16,000 output tokens in one call; allocation reserves 3,200 for each of five isolated calls. Repeated input, actual output, time and money differ.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Truncated calls |
| --- | ---: | ---: | ---: | ---: | ---: |
'''
    for row in length_result['raw_runs'] + sections_result['raw_runs']:
        comparison += f"| `{row['plan']}` | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} | {row['truncated_call_count']} |\n"
    comparison += '''
One sample per procedure is exploratory evidence on this item. The final assembled answer receives the unchanged post-freeze rubric; headings, section presence and independent contexts certify no mathematics. Failures and truncated sections remain in the results. Detailed judgments, exact evidence and hash bindings are under `section_control_20261110/`. No evaluator or reference content was sent to any solver call.

This allocation attempt scored 26/100 versus 62/100 for the longer direct answer and cost more. All five calls reached their output ceiling. Independent sections used incompatible Hamiltonians and formulas; assigning a part did not ensure that its requested results were delivered. This observation does not support adopting the allocation control as an improvement.
'''
    page = ROOT/'wiki/Workflow-QM-Sections.md'
    contents = page.read_text(encoding='utf-8')
    contents = contents.replace('Its first live run is prepared but has not been dispatched.',
                                'Its first live run is frozen and independently graded below.')
    contents = contents.replace('Live cost, token, time and score fields remain unmeasured for this plan.',
                                'Live measurements are recorded below; software tests do not establish a performance advantage.')
    start, end = '<!-- BEGIN SECTION RESULTS -->', '<!-- END SECTION RESULTS -->'
    before, rest = contents.split(start, 1)
    _, after = rest.split(end, 1)
    page.write_text(before+start+'\n'+comparison+end+after, encoding='utf-8')
critique_folder = HERE/'deepseek_critique_20261110'
critique_result = summarize(sorted((critique_folder/'runs').glob('*/run.json')), grades)
if len(critique_result['raw_runs']) == 1 and critique_result['raw_runs'][0]['score'] is not None:
    (critique_folder/'graded_results.json').write_text(json.dumps(critique_result, indent=2)+'\n', encoding='utf-8')
    comparison = '''## DeepSeek direct versus self-critique

Both runs use the identical public seed, DeepSeek V3.2 and AtlasCloud FP8, with a 16,000-token ceiling per call and a USD0.10 whole-run cap. Self-critique generates its own new draft and revises that draft; it does not revise the separately scored direct answer. The private answer, grades and evaluator derivations are absent from both requests.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Finish reasons |
| --- | ---: | ---: | ---: | ---: | --- |
'''
    for row in model_result['raw_runs'] + critique_result['raw_runs']:
        comparison += f"| `{row['plan']}` | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} | {row['finish_reason_counts']} |\n"
    comparison += '''
Only the frozen final revised answer earns rubric credit. The unchanged 25-criterion rubric and exact supporting evidence are retained under `deepseek_critique_20261110/`. Grading is model-assisted mathematical review, not human or formal certification. Draft quality has not been independently scored in this comparison.

The revised answer scores 88/100 versus 83/100 for the separate direct run. It states a correct general CHSH maximum but contradicts it in its correlation-matrix derivation; an equality-case entanglement time is also wrong. Other special cases remain incomplete. Neither answer is fully correct. Self-critique costs about 84% more money, uses 109% more total tokens and takes 37% longer in these two observations.

One attempt per procedure cannot establish a reproducible advantage. Self-critique permits two calls and more total output; this is not a matched-resource ablation. It tests a generic revision procedure, not implemented PFP/EIS/PCIV/OPERADS integration. Compare correctness and actual money, tokens and time together.
'''
    page = ROOT/'wiki/Workflow-QM-Controls.md'
    contents = page.read_text(encoding='utf-8')
    contents = contents.replace('**Status: implemented, synthetic-tested and sampled once in the first live QM pilot.** Both controls hit their output limits. See the [measured results](Workflow-QM-Pilot-2026-11-10.md); a response retained with billing is not necessarily a complete solution.',
        '**Status: implemented and measured in the initial Qwen pilot and a later DeepSeek comparison.** The initial Qwen calls hit their output limits; the later DeepSeek calls stopped normally. See the comparison below and the [initial results](Workflow-QM-Pilot-2026-11-10.md).')
    old = 'The unchanged self-critique plan is now prepared for one DeepSeek attempt, with 16,000 tokens per call and a shared USD0.10 cap; it has not run.'
    contents = contents.replace(old, 'The unchanged self-critique plan has now completed one DeepSeek attempt, with 16,000 tokens per call and a shared USD0.10 cap; its graded comparison follows.')
    start, end = '<!-- BEGIN CRITIQUE RESULTS -->', '<!-- END CRITIQUE RESULTS -->'
    if start in contents:
        before, rest = contents.split(start, 1)
        _, after = rest.split(end, 1)
        contents = before+start+'\n'+comparison+end+after
    else:
        contents += '\n'+start+'\n'+comparison+end+'\n'
    page.write_text(contents, encoding='utf-8')
charpoly_folder = HERE/'charpoly_pilot_20261110'
charpoly_result = summarize(sorted((charpoly_folder/'runs').glob('*/run.json')), grades)
if len(charpoly_result['raw_runs']) == 2 and all(row['score'] is not None for row in charpoly_result['raw_runs']):
    (charpoly_folder/'graded_results.json').write_text(json.dumps(charpoly_result, indent=2)+'\n', encoding='utf-8')
    comparison = '''## First measured native-checker comparison

Two separately sampled attempts used the same public seed, DeepSeek V3.2 and AtlasCloud FP8. Each proposal permits 2,400 output tokens and synthesis 12,000. Only the checked arm permits one additional 2,400-token correction, under the same USD0.10 whole-run cap.

| Plan | Score /100 | Recorded cost | Input / output tokens | Wall seconds | Intermediate certified | Outcome |
| --- | ---: | ---: | ---: | ---: | --- | --- |
'''
    for row in charpoly_result['raw_runs']:
        certified = bool(row['encoded_claim_status_counts'].get('EXACT_INTERMEDIATE_CHARPOLY_IDENTITY'))
        comparison += f"| `{row['plan']}` | {row['score']:g} | ${row['money_usd']:.6f} | {row['input_tokens']:,} / {row['output_tokens']:,} | {row['wall_time_seconds']:.1f} | {certified} | {row['status']} |\n"
    comparison += '''
Only the frozen synthesis answer earns rubric credit. No intermediate certificate automatically earns points, and no proposal, evaluator content or earlier answer supplies grading credit. Full requests, native receipts, billing, final text and criterion evidence remain under `charpoly_pilot_20261110/`.

The checked attempt receives zero delivered-solution points: its initial proposal failed rational-format admission, and its only repair was malformed and length-truncated. The unchecked answer scores 47/100; it stops during the reduced-state calculation and omits the later entanglement and thermal results. Neither initial proposal reached native computation, so these runs demonstrate no live exact-polynomial certificate or final-answer advantage.

A separate post-run diagnostic applied a tested, value-preserving rational normalizer to both initial proposals. Both still failed the monic-leading-coefficient condition under the declared ascending-lambda interpretation. No model was called, and no original run or grade was changed. Normalization alone would not have admitted these proposals. The helper is not a registered workflow.

One attempt per procedure on one problem cannot establish a reliable benefit. Proposal and synthesis sampling can differ independently. If both initial proposals pass, the checked arm uses no repair and both arms apply the same procedure to their respective candidates; a score difference then does not isolate a checker effect. Native acceptance remains an intermediate polynomial guarantee only.
'''
    page = ROOT/'wiki/Workflow-QM-Charpoly.md'
    contents = page.read_text(encoding='utf-8')
    start, end = '<!-- BEGIN CHARPOLY RESULTS -->', '<!-- END CHARPOLY RESULTS -->'
    before, rest = contents.split(start, 1)
    _, after = rest.split(end, 1)
    page.write_text(before+start+'\n'+comparison+end+after, encoding='utf-8')
print(json.dumps({'frozen_runs':len(result['raw_runs']), 'graded':sum(row['score'] is not None for row in result['raw_runs']),
                  'pending_receipts':len(result['planned_runs_without_frozen_receipt'])}))
