"""Persist the parent's 28 completed source-body readings, retaining52 pending paths."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV/'additional_operads_education_remaining_scope.json').read_text())
frozen = {r['path']: r for r in scope['files']}
prefix = 'education/008_oeop/'
notes = {
 '00_index.md': 'Full index read. The 201dc8d inventory/test/mirror counts are explicitly historical, and the later live transport failure correctly makes no model-comparison claim. It distinguishes declared bindings from actual executors and admits absent identities, symmetric action and value-level law tests at that revision. This is useful provenance and claim hygiene, not a fresh reproduction of historical counts. The level table and linked production claims require their owners; conceptual images are explicitly not machine-checked specifications.',
 'mssn_learning_route.md': 'Full route read. It correctly distinguishes composition, detection, mutation and evaluation and says a detector is not thereby an inverse/antimorphism. Retired Python admission entrypoints are described as compatibility refusals, not activation of the planned lifecycle. Links into absent historical research roots are contextual references, not evidence read or run here.',
 'multi_agent_swarm_orchestration_and_operad.md': 'Full ten-colour and four-wing specification read. Ordered signatures are useful interface contracts but matching a coarse colour cannot establish semantic preservation, authenticity or recomputed binding. The frozen dataclass accepts empty participants/hash and an arbitrary effect and exposes mutation through its Mapping payload. The claim that a receipt proves every wing inspected all claims exceeds this representation. Regex lints are correctly scoped as phrase checks/questions later in the text; no production orchestrator was executed.',
 'lean4/README.md': 'Full Lean kernel index read. It accurately names unary/output identity facts and a factory receipt theorem, but the broader verified-kernel heading must be limited to the definitions/theorems actually present. No native elaboration was attempted in this review.',
 'lean4/WasOperads.lean': 'Full Lean source read. It defines profile data, unrestricted planar syntax, tree height/output, four host constructors and a receipt factory. The four rfl theorems establish properties of chosen constructors/list, not operad composition, associativity, mirror parity, wing capabilities or general authority safety. PlanarTree.node has no colour/arity proof field, and DeliberationReceipt permits arbitrary authorityEffect strings; the theorem covers emitDeliberationReceipt only. Source reading is not a successful Lean build.',
 'lean4/lakefile.lean': 'Full package declaration read. It configures the WasOperads library root and version; no theorem or successful build evidence is present.',
 'lean4/lean-toolchain': 'Full one-line Lean4 v4.35.0 toolchain pin read. It is a requested toolchain version, not installed-toolchain or elaboration evidence.',
 'normal_forms/README.md': 'Full contract index read. AONF is misnamed Agent Operad rather than Active Obstruction; GBQNF is misnamed Gauge Break rather than Generalized Boundary-Quotient; MUR is expanded as Multi-Unitary without that claim in the transport contract. Claimed associativity, consensus and atomic host parity do not follow from those linked specifications. Production/computed/gated metadata also exceeds two verification-absent contracts.',
 'normal_forms/nf.cochain.dhnf.yaml': 'Full Hodge contract read. Under a finite nilpotent complex and declared positive-definite rational inner products, the orthogonal exact/harmonic/coexact split and uniqueness of summands are meaningful linear algebra. It correctly requires gauge choice for unique potentials, treats harmonic residue as a successful component rather than automatic obstruction, and says this directory executes no decomposition. It does not by itself classify semantic failures or rate-limit a swarm.',
 'normal_forms/nf.coda.gbqnf.yaml': 'Full boundary-quotient repair contract read. Exactness, closure and quotient residuals are meaningful after a cochain complex, defect adapter and repair action are admitted. Semantic repair equivalence additionally needs that adapter/action to be sound; arbitrary state changes do not acquire faithful cochains merely by naming them. Replica convergence is explicitly disclaimed. Upstream proof references and executable metadata are not new checked evidence here.',
 'normal_forms/nf.coda.mur.transport.yaml': 'Full representation transport contract read. The declared comparison square, target verification and conditional loss logging are useful obligations. Equality, natural isomorphism and a bounded defect are distinct laws; loss logging does not make a projection invertible. No concrete categories, functors or target checker are implemented here, and the selected schema check flags the undeclared family value coda. No unitary representation or multi-host atomic synchronization theorem is supplied.',
 'normal_forms/nf.derivation.aonf.yaml': 'Full active-obstruction contract read. It requires recorded activity, declared repair/extension families, exhaustion and explicit tie selection, separating proposal from execution. Its two-arm menu is conditional on those definitions and upstream admissions, not a new universal classification of agent actions. Its name does not supply an operad, and cited upstream Lean theorems were not rebuilt.',
 'normal_forms/normal_form_contract_schema.yaml': 'Exact6691-byte transfer from the fully read EIS sibling meta-schema at SHA256 b7f991076733d9de27c6b5b772079929c0ed7566800a89f01740126cfcefa20a. This custom schema declares fields, status axes and routes; the parent checked all four local contracts for selected requirements, enums and route targets, without claiming a complete semantic validator.',
 'curriculum/README.md': 'Full two-track curriculum index read. The eight evidence labels and four-directory organization are useful conventions, but the promise of prediction gates and mathematical labs is not realized by the two preflight-only notebooks.',
}
for stem, title in [('900_was_operad_foundations','lesson_900_01_was_operadic_foundations'),('910_skill_multicategories','lesson_910_01_multicategories_and_skills')]:
    base = 'curriculum/'+stem+'/'
    notes[base+'README.md'] = 'Full track index read. It names a mathematical topic and four directory roles but contains no definitions, tests or observed workflow efficacy.'
    notes[base+'concepts/'+title+'.md'] = 'Full concept lesson read. It repeats generic boundary/claim-discipline text and asks about folder architecture and None tags; it defines no actual operadic composition or law. Production/verified metadata is unsupported by the preflight-only companion. Teaching scaffold rather than substantive mathematical lesson.'
    notes[base+'notebooks/'+title+'.ipynb'] = 'Complete raw notebook JSON read, including metadata and empty outputs. Its sole code cell prints an initialization message and returns True, then asserts that return. No composition, type checking, falsifier, prediction or mathematical result is exercised. Exclude from executable workflow evidence; no notebook execution was needed to determine this.'
    notes[base+'scripts/'+title+'.md'] = 'Full narration script read. It usefully separates plan composition, measurement, external admission, bout execution and genome write, and qualifies unknown residual labels and planned consolidation. Scenes nevertheless promise executed structures/falsifiers absent from the companion preflight-only notebook. The historical counts and foreign owner links are not fresh implementation validation.'
    for directory in ('scripts','videos'):
        notes[base+directory+'/.gitkeep'] = 'Full one-line directory placeholder read. No lesson, generated video, code or mathematical evidence.'
for directory in ('scripts','videos'):
    notes['curriculum/'+directory+'/.gitkeep'] = 'Full one-line curriculum directory placeholder read. No implementation or mathematical evidence.'
assert len(notes) == 28
rows = []
for relative, assessment in notes.items():
    path = prefix+relative
    raw = (ROOT/path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == frozen[path]['sha256']
    rows.append({'path': path, 'sha256': frozen[path]['sha256'], 'full_source_read': True,
                 'reviewed_lines': [[1, len(raw.decode('utf-8').splitlines())]], 'assessment': assessment})
assert set(r['path'] for r in rows) == set(scope['parent_initial_paths'])


def ev(relative):
    path = prefix+relative
    return {'path': path, 'sha256': frozen[path]['sha256']}


findings = [
 {'id': 'OET-F01', 'severity': 'medium', 'statement': 'The normal-form index assigns the wrong meanings to AONF, GBQNF and MUR, then claims operadic associativity, deterministic consensus and host parity from those links. The actual contracts concern active obstruction, boundary-quotient repair and representation transport; two explicitly have verification absent.',
  'evidence': [ev('normal_forms/README.md'), ev('normal_forms/nf.derivation.aonf.yaml'), ev('normal_forms/nf.coda.gbqnf.yaml'), ev('normal_forms/nf.coda.mur.transport.yaml')],
  'recommended_action': 'Correct names and adapters and separate proposed mechanisms from checked implementations.'},
 {'id': 'OET-F02', 'severity': 'medium', 'statement': 'WasOperads.lean provides no composition function or operad-law theorem. Its tree constructor has no child colour/arity condition, and its receipt authority theorem applies only to one factory. The unrestricted receipt structure and syntax cannot establish all the invariants promised in the file header or broader curriculum.',
  'evidence': [ev('lean4/WasOperads.lean'), ev('lean4/README.md')],
  'recommended_action': 'Scope the kernel claims to its actual definitional facts; add well-formedness, substitution and law proofs before treating it as an operad verifier. No fresh elaboration is claimed.'},
 {'id': 'OET-F03', 'severity': 'medium', 'statement': 'Both purported operadic laboratory notebooks contain only the same constant-True preflight. They provide no mathematical experiment, prediction gate or negative test despite verified/production lesson labels and storyboard promises of falsifiers.',
  'evidence': [ev('curriculum/900_was_operad_foundations/notebooks/lesson_900_01_was_operadic_foundations.ipynb'), ev('curriculum/910_skill_multicategories/notebooks/lesson_910_01_multicategories_and_skills.ipynb')],
  'recommended_action': 'Exclude these scaffolds from workflow/testing counts and replace their placeholders with a specified operation and a meaningful counterexample.'},
 {'id': 'OET-F04', 'severity': 'medium', 'statement': 'The swarm specification says colour matching eliminates hallucinated artifacts and its receipt proves every wing inspected all claims. Coarse labels and a dataclass cannot establish those facts. The literal frozen snippet accepts empty participants/hash and an explicit EXECUTE effect; its mutable verdict mapping can change after construction.',
  'evidence': [ev('multi_agent_swarm_orchestration_and_operad.md')],
  'validation': 'dag/reviews/additional_operads_education_checks.json',
  'recommended_action': 'Define separate semantic/artifact checks and authenticated receipt construction; keep structural compatibility and verification evidence distinct. This is a teaching snippet, not a production exploit.'},
 {'id': 'OET-F05', 'severity': 'low', 'statement': 'The local MUR contract uses identity.family=coda, which is absent from its adjacent custom meta-schema enum. All four contracts pass the selected required-field and terminal-map checks.',
  'evidence': [ev('normal_forms/nf.coda.mur.transport.yaml'), ev('normal_forms/normal_form_contract_schema.yaml')],
  'validation': 'dag/reviews/additional_operads_education_checks.json',
  'recommended_action': 'Choose an admitted family or intentionally revise the governing enum with its consumers; do not infer semantic conformance from shape alone.'}
]
claims = [
 {'id': 'OET-C01', 'statement': 'The Hodge contract states a meaningful conditional finite linear-algebra decomposition and correctly separates unique summands from gauge-dependent potentials and harmonic residue from a declared-law obstruction.', 'evidence': [ev('normal_forms/nf.cochain.dhnf.yaml')]},
 {'id': 'OET-C02', 'statement': 'The index and learning route preserve useful negative evidence: historical executor/law limits, unresolved live transport failure, retired compatibility boundaries, and the distinction between detectors and antimorphisms. These qualify proposals rather than supply model-efficacy evidence.', 'evidence': [ev('00_index.md'), ev('mssn_learning_route.md')]},
 {'id': 'OET-C03', 'statement': 'Boundary-quotient repair, declared transport squares and active-obstruction menus can contribute explicit workflow preconditions after their carriers, maps, witnesses and adapters are supplied. The YAML does not implement those obligations or establish independent authorization.', 'evidence': [ev('normal_forms/nf.coda.gbqnf.yaml'), ev('normal_forms/nf.coda.mur.transport.yaml'), ev('normal_forms/nf.derivation.aonf.yaml')]}
]
report = {'source_commit': scope['source_commit'], 'status': 'in_progress',
          'scope_manifest': 'dag/reviews/additional_operads_education_remaining_scope.json',
          'file_reviews': sorted(rows, key=lambda r:r['path']), 'claims': claims, 'findings': findings,
          'pending_paths': sorted(set(frozen)-{r['path'] for r in rows}),
          'validation': 'dag/reviews/additional_operads_education_checks.json',
          'limits': ['Parent28full bodies;52atlas/level/image sources still pending.',
                     'Seven migrated or reference-edited original paths are explicitly outside this unchanged-byte slice, not declared reviewed.',
                     'No Lean/native/runtime build, providers or private benchmark access.']}
(REV/'additional_operads_education_remaining.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'full':len(rows),'pending':len(report['pending_paths']),'claims':len(claims),'findings':len(findings)}))
