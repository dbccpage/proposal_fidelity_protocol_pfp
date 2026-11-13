"""Finish the bounded support partition; keep embedded/archive semantics open."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];REV=ROOT/'dag/reviews';OUT=REV/'paper_011_support_inspection'
PREFIX='papers/pfp/011_recreated_demos_and_proposal_fidelity_evidence/'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
scope=read(REV/'additional_paper_011_support_scope.json');frozen={x['path']:x for x in scope['files']}
report=read(REV/'additional_paper_011_support.json');rows={x['path']:x for x in report['file_reviews']}
checks=read(OUT/'bounded_data_checks.json');archive=read(OUT/'archive_inventory.json');pdf=read(OUT/'pdf_preparation.json')
def bounded(name,level,assessment,**fields):
    path=PREFIX+name
    rows[path]={'path':path,'sha256':sha(ROOT/path),'full_source_read':False,'reviewed_lines':[],
                'review_level':level,'assessment':assessment,**fields}
for name,data in checks['manifests'].items():
    bounded(name,'all_entry_custody_and_order_diagnostics',
            'Every digest/path record parsed and checked against current confined files, separately from LF diagnostics. Five ordering inversions reflect recorded renames; current verifier refuses before normal digest reporting. Thirteen paths are missing from checkout. Archive manifests pass separately; no checksum rewrite or source-body credit.',
            entries=data['entries'],raw_mismatches=data['raw_mismatches'],remaining_after_LF=data['remaining_after_lf'],missing=data['missing'],order_inversions=data['order_inversions'],detail_receipt='dag/reviews/paper_011_support_inspection/bounded_data_checks.json')
for name in ['current_closed_receipt_audit.json','current_closed_receipt_audit_v2.json']:
    data=checks['small_checks'][name]
    bounded('docs/'+name,'parsed_schema_all_local_digest_rows_and_declared_ceiling',
            'Historical audit explicitly limits itself to raw-file/output binding, not mathematical recomputation. All paper-relative rows mapped by explicit retained suffix and rehashed. Changed bytes remain after LF normalization. Historical external runtime paths were not accessed; provenance does not authenticate provider origin.',
            local_rows=data['count'],raw_matches=data['raw_matches'],matches_after_LF=data['matches_after_lf'],external_unverified=len(data['external_unverified']),detail_receipt='dag/reviews/paper_011_support_inspection/bounded_data_checks.json')
bounded('docs/findings_demo_inventory.json','parsed_schema_ID_sets_counts_and_readable_inventory_crosscheck',
        'All top-level fields/record schemas and exact C001-C060/G01-G25/13-family ID sets checked against the fully read readable inventory. Eleven historical CHECKED labels remain quarantined, thirteen OPEN and one analogy. Twenty source-note structures and attached spans/digests are catalog records, not fresh source-note or nested-source reading.',
        detail_receipt='dag/reviews/paper_011_support_inspection/bounded_data_checks.json')
bounded('docs/recreation_catalog.json','parsed_schema_ID_sets_and_capability_counts',
        'Exact sixty challenge IDs and27 unique dispatch IDs checked. Two mechanism recreations, eight specification-only items and fifty solver/checker packages remain distinct. Nested case/reference text has not received complete semantic review through this catalog parse; source/checker owners and run artifacts have separate partitions.',
        detail_receipt='dag/reviews/paper_011_support_inspection/bounded_data_checks.json')
bounded('docs/runtime_environment_v1.json','all_record_schema_digest_format_and_distribution_count',
        'All16497 declared file rows have well-formed entry/path/digest fields;26 distribution names/versions/counts and per-distribution uniqueness inspected. Captured Python3.12.10 and torch2.6.0+cu124 do not satisfy an assertion of a fresh current Python3.12/torch>=2.13 installation. External runtime files were not opened; this profile excludes OS/std-lib closure.',
        detail_receipt='dag/reviews/paper_011_support_inspection/bounded_data_checks.json')
bounded('paper.pdf','complete_extracted_text_and_rendered_page_review_not_binary_source_read',
        'All14 pages read through full extracted text and complete contact-sheet inspection alongside the full TeX body. No clipping/overlap observed at inspected resolution; formulas are visible. PDF retains old title/version, old paths and private engine name. The half-instanton parity contradiction appears on page14. It is not the13-page edition bound by manuscript inventory receipt.',
        page_review={'pages':14,'direct_visual_pages':list(range(1,15)),'sheets':pdf['sheets'],'extracted_text':'dag/reviews/paper_011_support_inspection/pdf_text.txt'})
zip_name=Path(archive['archive']).name
bounded(zip_name,'complete_safe_member_inventory_CRC_SHA_and_internal_manifest_checks',
        'All2587 members streamed for CRC/SHA and safe unique regular names. Internal2585/2586-entry manifests pass.42 member names lack same-name checkout paths:29 are corresponding recorded manifest renames and13 remain missing. Most renamed current bodies have also changed. This is archive custody only; embedded body semantics and current/archive deltas remain a separate explicit backlog.',
        members=2587,uncompressed_bytes=sum(x['bytes'] for x in archive['members']),raw_same_name_matches=sum(x['raw_equal'] for x in archive['members']),
        detail_receipt='dag/reviews/paper_011_support_inspection/archive_inventory.json',semantic_member_review_status='pending_separate_body_and_delta_accounting')

def evidence(name,lines=None):
    path=PREFIX+name;out={'path':path,'sha256':sha(ROOT/path)}
    if lines:out['lines']=lines
    return out
def finding(identifier,statement,sources,action,severity='reproducibility_gap'):
    return {'id':identifier,'statement':statement,'evidence':[PREFIX+p for p,_ in sources],
            'source_evidence':[evidence(p,r) for p,r in sources],'severity':severity,'recommended_action':action}
report['findings']=[
finding('PAPER011-SUPPORT-F01-PARITY-CANCELLATION','The appendix claims sigma=(-1)^(Nplus-Nminus) changes from negative to positive when the counts swap. For k=Nplus-Nminus, swapping gives -k, the same parity; (1,0) and(0,1) both have sign-1. Thus the proposed involution does not cancel equal-weight odd sectors. The SU2 subsection repeats the unsupported implication. This is a direct algebraic contradiction in TeX and PDF, irrespective of receipt status.',
        [('paper.tex',[[1107,1147]]),('paper.pdf',None)],'Retain as a negative control; withdraw the cancellation/physical sign claim until an actually sign-reversing, weight-preserving involution is specified and checked. Do not repair historical receipts to mask the contradiction.','mathematical_false_claim'),
finding('PAPER011-SUPPORT-F02-CURRENT-CUSTODY','Current verifier refuses both manifests for ordinal UTF8 ordering. Independent parsing finds five inversions each,1347/1348 raw mismatches,954/955 surviving LF diagnostics and13 missing paths. All2585/2586 embedded ZIP bindings pass.29 archive paths were renamed in current manifests without changing recorded digests, so a rename is not proof the renamed current body is unchanged.',
        [('MANIFEST.sha256',None),('SHA256SUMS',None),('verify_deposit.py',[[78,130]])],'Keep exact historical archive and explicit transformations; prepare any new edition with new provenance instead of relabeling old hashes.'),
finding('PAPER011-SUPPORT-F03-RENDERER','Current renderer searches for Bare Metal Anchor but the manuscript names Jeremy H Carroll. Guarded actual-source call raises StopIteration before any subprocess or temporary output. PDF/title/version/path drift is therefore not resolved by the current rendering command.',
        [('tools/render_paper.py',[[36,54]]),('paper.tex',[[120,140]])],'Use explicit author metadata in a future edit and verify rendering against the actual manuscript.'),
finding('PAPER011-SUPPORT-F04-AUXILIARY-BUILDER-RACE','Auxiliary build_deposit_zip checks hashes, then rereads payload bytes without matching the admitted digest. A synthetic concurrent mutation after admission produces changed archive payload under the original manifest. The canonical writer rejects the corresponding stale digest.',
        [('scripts/build_deposit_zip.py',[[45,74]]),('tools/rebuild_release.py',[[244,263]])],'Reuse a digest-checked read/write path; the observation assumes concurrent mutation and is not a hash forgery.','custody_boundary_gap'),
finding('PAPER011-SUPPORT-F05-OPTIONAL-ARCHIVE-CONTROL','Canonical validate expects SHA256SUMS inside a ZIP only when it is already present. Both full and omitted-control canonical synthetic archives return no errors. Payload and inner manifest remain bound, but this does not enforce the full builder two-tier archive membership.',
        [('tools/rebuild_release.py',[[317,349]])],'Make required control-file membership explicit in a future release contract, with both positive and omitted-control checks.','custody_boundary_gap'),
finding('PAPER011-SUPPORT-F06-EDITION-COUNTS','Current TeX says31 dispatch entries but lists32; the catalog and inventory receipt list27. The inventory receipt binds13 PDF pages while current PDF has14 and a different title/version from TeX. These overlapping catalogs are edition/scope records, not independent experiment totals.',
        [('paper.tex',[[1006,1054]]),('docs/manuscript_inventory_receipt.json',None),('docs/recreation_catalog.json',None),('paper.pdf',None)],'Bind reader-facing counts and edition metadata to a single explicit source revision; retain older records as historical.'),
finding('PAPER011-SUPPORT-F07-HISTORICAL-AUDIT-DRIFT','Historical current-closed audit v1 has87 local paper rows with51 raw and61 LF matches, plus32 unverified external runtime rows; v2 has148 local rows with86 raw and118 LF matches. No local row is missing. Thus dated audit receipts do not certify the present rewritten bytes even where labels still say closed.',
        [('docs/current_closed_receipt_audit.json',None),('docs/current_closed_receipt_audit_v2.json',None)],'Use fresh receipts for current bytes and preserve historical identities; do not infer mathematical replay from digest-only checks.'),
finding('PAPER011-SUPPORT-F08-RUNTIME-PROFILE','Captured runtime declares Python3.12.10 and torch2.6.0+cu124, while current package requires Python3.12 and torch>=2.13. Support synthetic controls ran on Python3.14.2, separately from historical replay. The26-distribution profile is neither a current environment pass nor OS/std-lib closure.',
        [('docs/runtime_dependencies.md',None),('docs/runtime_environment_v1.json',None),('pyproject.toml',None)],'For an actual replay, bind an admitted matching runtime and record its dependency checks separately from these portable pure-Python controls.'),
]
report['claims']=[
 {'id':'PAPER011-SUPPORT-L1-CERTIFICATE-BOUND','statement':'For a fixed finite directed graph, incidence B, edge vector w, any potential u and circulation q with B^T q=0 and |q_e|<=1 satisfy q dot w<=sum_e|w_e-(Bu)_e|. Equality of feasible primal and dual values certifies the displayed L1 minimum. This classical bound is the useful graph foundation, not a general natural-language or higher-degree guarantee.',
  'evidence':[PREFIX+'paper.tex'],'source_evidence':[evidence('paper.tex',[[244,257]])],'status':'written_conditional_mathematics_reviewed','dependencies':['Fixed finite graph and declared incidence convention','Feasible potential and dual circulation with unit box bounds'],
  'limits':'Direct weak-duality argument: q dot w=q dot(w-Bu), bounded termwise by absolute residual. No new native host validation or proof of every adapter here.'},
 {'id':'PAPER011-SUPPORT-PARITY-OBSTRUCTION','statement':'For every integer k, -k and k have the same parity, so (-1)^(-k)=(-1)^k. Therefore swapping the two nonnegative counts cannot be a sign-reversing involution for the appendix sign formula.',
  'evidence':[PREFIX+'paper.tex'],'source_evidence':[evidence('paper.tex',[[1115,1123]])],'status':'direct_algebraic_refutation_with_25_illustrative_controls',
  'dependencies':['The sign formula and swap map stated by the manuscript'],'limits':'Refutes that stated cancellation mechanism, not every possible meron representation or unrelated exact gauge certificate.'},
]
assert set(rows)==set(frozen)
for path,row in rows.items():
    assert sha(ROOT/path)==frozen[path]['sha256']==row['sha256']
    if row['full_source_read']:
        assert row['reviewed_lines']==[[1,len((ROOT/path).read_text(encoding='utf-8-sig').splitlines())]]
report.update(status='support_partition_complete_with_explicit_artifact_bounds',file_reviews=sorted(rows.values(),key=lambda x:x['path']),pending_paths=[],
              scope_summary={'assigned':41,'full_source_bodies':32,'bounded_artifacts':9,'pdf_pages_directly_read_and_seen':14,'archive_members_custody_only':2587},
              validation=[{'rule':'actual_custody_and_isolated_countercontrols','status':'completed_with_recorded_failures','receipt':'dag/reviews/additional_paper_011_support_probes.json'},
                          {'rule':'catalogue_manifest_and_parity_diagnostics','status':'completed_with_recorded_failures','receipt':'dag/reviews/paper_011_support_inspection/bounded_data_checks.json'},
                          {'rule':'all41_frozen_hashes','status':'unchanged'}],
              semantic_backlog=['Embedded archive bodies/differences are not fully reviewed.','666 history and1550 run-evidence original paths remain separate partitions.','Native249 and core51 reports retain their own current progress.'],
              limits=['No original source/manifest/PDF/receipt rewritten.','No private QM answer access, model call, native build or historical executable run.','Historical claims and archived task instructions are reviewed as data, not current authority.','Support partition completion is not a complete Paper011 or repository audit.'])
write(REV/'additional_paper_011_support.json',report)
markdown='''# Paper011 support audit

The paper is useful as an archive audit and collection of falsifiers. Its central distinctions—fixed mathematical task, checked witness, source identity, historical recount and empirical model trial—serve this program. The graph objective has a classical finite L1 primal/dual foundation. This is not a new general reasoning theorem.

The meron appendix contains a direct false mathematical claim: swapping N+ and N− negates their difference but preserves its parity, so the stated determinant sign cannot flip. The same cancellation implication recurs in its SU2 discussion. Receipt verification cannot establish that missing mathematical property. Retain this as a workflow negative control and withhold the physical cancellation claims.

All41 parent support paths have explicit dispositions:32 full bodies and9 bounded artifacts. All14 PDF pages were read and visually inspected; no clipping was observed at the inspected resolution. The PDF, TeX, metadata, dispatch catalog and historical inventory describe different editions. TeX lists32 dispatch entries while saying31; catalog has27.

The2587-member ZIP passes its2585/2586 embedded checksum bindings. Its bodies have not all been semantically reviewed. Of42 names absent at matching checkout paths,29 have recorded manifest renames;13 remain missing. Current manifests have1347/1348 raw failures,954/955 surviving LF diagnostics, and five ordering inversions. The actual verifier stops on ordering; an independent parser records the remaining diagnostics without rewriting hashes.

Isolated controls confirm the author-header rendering failure, auxiliary builder mutation gap, and canonical validator's acceptance of an archive omitting SHA256SUMS. The canonical writer rejects stale payload digests. Controls ran on Python3.14.2, not the paper's required3.12 runtime; no native rebuild or historical executable was run.

The broader Paper011 review is still in progress. Separate core/native reports and the666 history/1550 run-evidence partitions own their evidence. No original edits, private-answer reads or paid model calls occurred.
'''
(REV/'additional_paper_011_support.md').write_text(markdown,encoding='utf-8')
write(REV/'additional_paper_011_support_final_validation.json',{'status':'passed_support_accounting_only','source_hashes_unchanged':41,'full_bodies':32,'bounded_artifacts':9,'claims':2,'findings':8,
      'report_sha256':sha(REV/'additional_paper_011_support.json'),'markdown_sha256':sha(REV/'additional_paper_011_support.md'),'scope_sha256':sha(REV/'additional_paper_011_support_scope.json'),
      'archive_semantic_review_complete':False,'whole_paper_review_complete':False})
swarm=read(ROOT/'dag/swarm_manifest.json')
completed=swarm.setdefault('completed_followup_slices',[])
if 'dag/reviews/additional_paper_011_support.json' not in completed:completed.append('dag/reviews/additional_paper_011_support.json')
swarm['parent_active_slice'].update(status=report['status'])
write(ROOT/'dag/swarm_manifest.json',swarm)
print(json.dumps(report['scope_summary']))
