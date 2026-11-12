export const meta = {
  name: 'wf50-repo-hygiene',
  description: 'WF50 repo hygiene: Sonnet surveys, Opus reviews and writes executor prompts, Fable executes one PR at a time',
  whenToUse: 'Rename files to snake_case, delete junk, refresh workflow docs, or write a gap report for this repository.',
  phases: [
    { title: 'Survey', detail: 'Sonnet agents read one slice each and report facts', model: 'sonnet' },
    { title: 'Review', detail: 'Opus agents check the survey and write one executor prompt per PR', model: 'opus' },
    { title: 'Execute', detail: 'Fable runs one prompt: edits, tests, commit', model: 'fable' },
  ],
}

// Usage (from the repository root, after `hygiene.py survey --out <run_dir>/plan.json`):
//   plan mode:    args = { mode: 'plan', run_dir: 'workflows/wf50_repo_hygiene/run' }
//   execute mode: args = { mode: 'execute', run_dir: '...', job: 'deletions' | 'renames' | 'docs' }
// Plan mode writes <run_dir>/survey/*.json, <run_dir>/prompt_<job>.md and <run_dir>/gap_report.md.
// Execute mode hands one prompt to one executor. Run the jobs in order, one PR each.

const A = args || {}
const RUN = A.run_dir || 'workflows/wf50_repo_hygiene/run'
const RULES = `House rules for this repository:
- Names: every file and folder except README.md is lowercase snake_case. Exemptions and their reasons are in workflows/wf50_repo_hygiene/naming_policy.json.
- papers/ keep their content byte for byte.
- Never write the words Omega, Anomalon, Woland or persona names in any file outside papers/, nor in commit messages.
- Do not rewrite git history. Do not touch uncommitted work you did not create. Keep the branch backup/main-folder-wip-20261106.
- Delete junk outright; do not archive it.
- Documentation is plain language first, short, no filler.`

const SLICES = [
  { key: 'pfp', paths: 'pfp/ (the pfp package, including pfp/infrastructure/tower_evidence and tower_research)' },
  { key: 'operads', paths: 'operads/' },
  { key: 'workflows', paths: 'workflows/ (wfNN folders, tasks/, library/, dag/)' },
  { key: 'records', paths: 'dag/, governance/, benchmarks/, .github/ and the files at the repository root' },
  { key: 'docs', paths: 'wiki/, docs/, education/, _ic/, contracts/' },
  { key: 'code', paths: 'code/, csharp/, lean4/, ops/, eis/, pciv/, pfp_core/, pfp_lab/' },
  { key: 'papers', paths: 'papers/ (renames only where nothing pins the name; content is never edited)' },
  { key: 'pilots', paths: 'pilots/ (approved for deletion; find the pilots dag/pilot_triage/catalog.json marks retain_mechanism or needs_more_evidence and say which workflows/wfNN_* folder each belongs in)' },
]
const SUBSYSTEMS = [
  { key: 'pfp', what: 'PFP, the proposal fidelity protocol (pfp/, pfp_core/, pfp_lab/, SCORING.md, wiki pages about it)' },
  { key: 'pciv', what: 'PCIV (pciv/ and its wiki pages)' },
  { key: 'eis', what: 'EIS (eis/ and its wiki pages)' },
  { key: 'operads', what: 'operads (operads/, code/rust operad crates, wiki Operads pages)' },
]

const SLICE_SCHEMA = {
  type: 'object',
  properties: {
    junk: { type: 'array', items: { type: 'object', properties: {
      path: { type: 'string' }, kind: { type: 'string' }, evidence: { type: 'string' }, referenced_by: { type: 'array', items: { type: 'string' } } },
      required: ['path', 'kind', 'evidence', 'referenced_by'] } },
    keep_name: { type: 'array', items: { type: 'object', properties: {
      path: { type: 'string' }, reason: { type: 'string' } }, required: ['path', 'reason'] } },
    rename_hazards: { type: 'array', items: { type: 'object', properties: {
      path: { type: 'string' }, hazard: { type: 'string' }, fix: { type: 'string' } }, required: ['path', 'hazard', 'fix'] } },
    secret_name_leaks: { type: 'array', items: { type: 'string' } },
    notes: { type: 'string' },
  },
  required: ['junk', 'keep_name', 'rename_hazards', 'secret_name_leaks', 'notes'],
}
const GAP_SCHEMA = {
  type: 'object',
  properties: {
    gaps: { type: 'array', items: { type: 'object', properties: {
      title: { type: 'string' }, evidence: { type: 'string' }, severity: { type: 'string', enum: ['high', 'medium', 'low'] } },
      required: ['title', 'evidence', 'severity'] } },
  },
  required: ['gaps'],
}
const DOCS_SCHEMA = {
  type: 'object',
  properties: {
    workflows: { type: 'array', items: { type: 'object', properties: {
      id: { type: 'string' }, folder: { type: 'string' }, status_in_code: { type: 'string' }, status_in_docs: { type: 'string' },
      doc_sources: { type: 'array', items: { type: 'string' } }, problems: { type: 'string' } },
      required: ['id', 'folder', 'status_in_code', 'status_in_docs', 'doc_sources', 'problems'] } },
    generators_and_pins: { type: 'string' },
  },
  required: ['workflows', 'generators_and_pins'],
}

if (A.mode === 'execute') {
  phase('Execute')
  const job = A.job
  if (!['deletions', 'renames', 'docs'].includes(job)) throw new Error('job must be deletions, renames or docs')
  const out = await agent(
    `You are the executor for the "${job}" job of the WF50 repo hygiene workflow. Read ${RUN}/prompt_${job}.md and carry it out completely, then commit on the current branch. ${RULES}\nReturn a short plain-text report: what changed, test and governance-checker results with numbers, and anything left undone.`,
    { label: `execute:${job}`, phase: 'Execute', model: 'fable' })
  return { job, report: out }
}

// ---------------------------------------------------------------- plan mode
phase('Survey')
const sliceTask = s => agent(
  `Survey one slice of this repository for the WF50 hygiene workflow. Slice: ${s.paths}.
The proposed renames are in ${RUN}/plan.json ("moves": old path -> new path). Read only; change nothing.
Report:
1. junk: files or folders that should be deleted outright: build output, caches, logs of one-off runs, generated files nothing reads, empty stubs, duplicates of content kept elsewhere, planned-but-never-run material. For each, give evidence and list what references it (grep). Do not list anything a test, import, CI step or pinned manifest needs unless you name that consumer.
2. keep_name: planned renames in your slice that must not happen because a tool, a hash pin, an external URL contract or generated code requires the exact name.
3. rename_hazards: planned renames that will break something the plain path rewrite cannot see (f-string or computed file names, globs, case-sensitive lookups, hashes over paths) and the code change that fixes it.
4. secret_name_leaks: files outside papers/ whose names or text contain Omega, Anomalon, Woland or persona names.
${RULES}`,
  { label: `survey:${s.key}`, phase: 'Survey', model: 'sonnet', schema: SLICE_SCHEMA })
const gapTask = g => agent(
  `Read ${g.what} and report where it is weak: missing tests, claims with no checker, stubs presented as features, broken or unreachable code, docs that disagree with code, missing pieces a user would need. Evidence must be file paths and concrete observations, not opinions. Read only.`,
  { label: `gap:${g.key}`, phase: 'Survey', model: 'sonnet', schema: GAP_SCHEMA })
const docsTask = () => agent(
  `List every workflow WF1-WF50 in this repository. For each: its workflows/wfNN_* folder, its real status in code (pfp/workflows for WF1-5, pfp_core/workflow_families for WF6-49, workflows/wf50_repo_hygiene for WF50), what its README and wiki page claim, which files its docs come from (some wiki pages are generated by pfp_core/workflow_families/docs.py; some READMEs are hash-pinned in dag/file_inventory.json), and what is wrong or missing. Also explain how generators and pins must be updated after a doc edit. Read only.`,
  { label: 'survey:docs', phase: 'Survey', model: 'sonnet', schema: DOCS_SCHEMA })

const [slices, gaps, docs] = await Promise.all([
  parallel(SLICES.map(s => () => sliceTask(s).then(r => ({ key: s.key, ...r })))),
  parallel(SUBSYSTEMS.map(g => () => gapTask(g).then(r => ({ key: g.key, ...r })))),
  docsTask(),
])
const found = slices.filter(Boolean)
log(`survey: ${found.length}/${SLICES.length} slices, ${found.reduce((n, s) => n + s.junk.length, 0)} junk candidates, ${found.reduce((n, s) => n + s.rename_hazards.length, 0)} rename hazards`)
const missing = SLICES.filter(s => !found.find(f => f.key === s.key)).map(s => s.key)
if (missing.length) log(`survey slices that returned nothing: ${missing.join(', ')}`)

phase('Review')
const packet = JSON.stringify({ slices: found, docs }, null, 1)
const REVIEW_COMMON = `You are a reviewer and prompt writer for the WF50 repo hygiene workflow. You do not edit repository files except the one prompt file you are asked to write. Verify survey claims yourself with grep and reads before accepting them; drop any claim you cannot confirm and say so in the prompt. ${RULES}
Survey results (JSON):\n${packet}`
const PROMPT_SHAPE = `Write a long-horizon executor prompt that a capable model can follow alone for hours without asking questions: goal, exact file lists or the commands that produce them, ordered steps, the checks to run after each step (pytest commands, \`python -m governance.tools.checker check\` (see governance/README.md; compare against the failures already on main), \`python dag/build_dags.py\`, \`python -m pfp_core.workflow_families.docs\`, operad catalog compiler), how to update hash pins and baselines honestly, what to do when a check fails, and a definition of done. End with: commit with a clear message; do not push.`

const reviews = await parallel([
  () => agent(`${REVIEW_COMMON}
Job: deletions. Decide the final list of junk to delete across all slices, including pilots/anomalon_woland and pilots/anomalon_woland_support (deletion approved by the owner), after the keeper pilots are moved into their workflows/wfNN_* folders with names scrubbed. Write the final list to ${RUN}/delete_list.txt (one path per line) and the executor prompt to ${RUN}/prompt_deletions.md. ${PROMPT_SHAPE} Return the two paths and the count of paths.`,
    { label: 'review:deletions', phase: 'Review', model: 'opus' }),
  () => agent(`${REVIEW_COMMON}
Job: renames. Starting from ${RUN}/plan.json, remove entries that must keep their name and write ${RUN}/plan_final.json in the same format. The executor will run \`python workflows/wf50_repo_hygiene/hygiene.py apply ${RUN}/plan_final.json\`, then \`residue\`, then fix each rename hazard and residue hit by hand. Renames run after deletions, so re-run \`hygiene.py survey --out ${RUN}/plan.json\` first and re-apply your removals if the tree changed. Write the executor prompt to ${RUN}/prompt_renames.md, covering imports, links, wiki page names (wiki/publish_wiki.py), CI files, pyproject packaging and package data. ${PROMPT_SHAPE} Return the paths and counts.`,
    { label: 'review:renames', phase: 'Review', model: 'opus' }),
  () => agent(`${REVIEW_COMMON}
Job: docs. Every workflow WF1-WF50 needs plain-language documentation in its workflows/wfNN_*/README.md and its wiki page: what it is for in one or two sentences, its true status, how to run it offline, what checks the answer, where the code is. Fix every status that disagrees with code. Edit generators rather than generated pages, and re-pin pinned files honestly. The pages must not mention any private engine or repository. Write the executor prompt to ${RUN}/prompt_docs.md. ${PROMPT_SHAPE} Return the path.`,
    { label: 'review:docs', phase: 'Review', model: 'opus' }),
  () => agent(`You are writing a short gap report on where PFP, PCIV, EIS and operads are weak in this repository. Verify each surveyed gap with a quick read before keeping it, rank by severity, and write plain language: one heading per subsystem, three to six bullets each, each bullet a concrete weakness with a file path and the next step that would fix it. No more than about 700 words. Write it to ${RUN}/gap_report.md and return the path. ${RULES}
Surveyed gaps (JSON):\n${JSON.stringify(gaps.filter(Boolean), null, 1)}`,
    { label: 'review:gap_report', phase: 'Review', model: 'opus' }),
])
return { survey: { slices: found.length, missing }, reviews }
