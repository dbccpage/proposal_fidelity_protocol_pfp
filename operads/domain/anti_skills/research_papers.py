"""Active Research Paper Anti-Skills Register.

AuthorityEffect: None.

Codifies the 86 active anti-skills enforced during automated research paper review
and Stage Ω republication gate inspection across research paper packages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class AntiSkillDefinition:
    """Definition of an active anti-skill."""

    number: int
    id: str
    name: str
    severity: str  # "BLOCKER", "MAJOR", "MINOR"
    description: str
    authority_effect: str = "None"

    def __post_init__(self) -> None:
        if self.authority_effect != "None":
            raise ValueError("AuthorityEffect must be 'None'")


ACTIVE_ANTI_SKILLS: Tuple[AntiSkillDefinition, ...] = (
    AntiSkillDefinition(
        1,
        "ANTI-MATRIX-PSD-FALLACY",
        "Matrix PSD Fallacy",
        "BLOCKER",
        "Checking only leading principal minors instead of all 2^d-1 principal minors or spectra.",
    ),
    AntiSkillDefinition(
        2,
        "ANTI-DISTANCE-NORM-CONFUSION",
        "Distance Norm Confusion",
        "BLOCKER",
        "Substituting Frobenius or l2 norms for Schatten-1/trace distances in density matrix bounds.",
    ),
    AntiSkillDefinition(
        3,
        "ANTI-EQUIVARIANCE-AS-CONSERVATION",
        "Equivariance as Conservation",
        "MAJOR",
        "Conflating commuting group invariant subspaces (P_H T = T P_H) with Hamiltonian time conservation.",
    ),
    AntiSkillDefinition(
        4,
        "ANTI-UNCHECKED-MORPHISM-SEARCH",
        "Unchecked Morphism Search",
        "BLOCKER",
        "Morphism searches omitting homomorphism composition and structure-preservation validation.",
    ),
    AntiSkillDefinition(
        5,
        "ANTI-GHOST-WITNESS",
        "Ghost Witness",
        "MAJOR",
        "Counterexample or torsion claims lacking explicit witness tables or generator code fixtures.",
    ),
    AntiSkillDefinition(
        6,
        "ANTI-DEGENERATE-AGGREGATION",
        "Degenerate Aggregation",
        "MAJOR",
        "Aggregation bounds failing when weights or values collapse to zero; requires nondegeneracy hypotheses.",
    ),
    AntiSkillDefinition(
        7,
        "ANTI-RANGE-RICHNESS-OMISSION",
        "Range Richness Omission",
        "MAJOR",
        "Surjectivity or universality claims omitting explicit range richness hypotheses.",
    ),
    AntiSkillDefinition(
        8,
        "ANTI-LEAN-STATEMENT-INFLATION",
        "Lean Statement Inflation",
        "MAJOR",
        "Discrepancies between informal paper claims and mechanized Lean 4 kernel theorems.",
    ),
    AntiSkillDefinition(
        9,
        "ANTI-NOTEBOOK-FALSE-EXACTNESS",
        "Notebook False Exactness",
        "BLOCKER",
        "Hardcoded outputs, mock calculations, or unpinned commands in reviewer notebooks.",
    ),
    AntiSkillDefinition(
        10,
        "ANTI-SCOPE-SCHIZOPHRENIA",
        "Scope Schizophrenia",
        "MAJOR",
        "Unhedged continuum or field theory extrapolations from finite toy models.",
    ),
    AntiSkillDefinition(
        11,
        "ANTI-BROKEN-INTERNAL-REFERENCES",
        "Broken Internal References",
        "MAJOR",
        "Unanchored numbering (Paper NNN), undefined label references, or broken citations.",
    ),
    AntiSkillDefinition(
        12,
        "ANTI-IDENTITY-MISMATCH",
        "Identity Mismatch",
        "BLOCKER",
        "Metadata mismatches between manuscript, TeX, PDF, change log, and Zenodo metadata.",
    ),
    AntiSkillDefinition(
        13,
        "ANTI-TOOLCHAIN-PLATFORM-LEAK",
        "Toolchain Platform Leak",
        "BLOCKER",
        "Committing platform target triples (windows-gnu/linux-gnu) into axiom reports.",
    ),
    AntiSkillDefinition(
        14,
        "ANTI-SYMLINK-ESCAPE",
        "Symlink Escape",
        "BLOCKER",
        "Filesystem symlinks or directory escapes in deposit trees; verifiers must fail closed.",
    ),
    AntiSkillDefinition(
        15,
        "ANTI-VACUOUS-MORPHISM-SUPPORT",
        "Vacuous Morphism Support",
        "BLOCKER",
        "Claiming support from searches testing zero valid morphisms; must type INCONCLUSIVE.",
    ),
    AntiSkillDefinition(
        16,
        "ANTI-UNCHECKED-NOTEBOOK-CELL",
        "Unchecked Notebook Cell",
        "BLOCKER",
        "Notebooks with unexecuted cells (execution_count is None) or missing replay.",
    ),
    AntiSkillDefinition(
        17,
        "ANTI-DERIVED-ARTIFACT-DESYNC-RACE",
        "Derived Artifact Desync Race",
        "BLOCKER",
        "Regenerating manifests when derived .tex/.pdf are stale relative to Markdown.",
    ),
    AntiSkillDefinition(
        18,
        "ANTI-MANIFEST-CIRCULARITY",
        "Manifest Circularity",
        "BLOCKER",
        "Listing .zip release archives inside SHA256SUMS or MANIFEST.sha256.",
    ),
    AntiSkillDefinition(
        19,
        "ANTI-CHECKLIST-OVERSPECIALIZATION",
        "Checklist Overspecialization",
        "BLOCKER",
        "Hardcoding single-paper filenames or theorems into general gate checklists.",
    ),
    AntiSkillDefinition(
        20,
        "ANTI-THREAD-DESCENT-CONFLATION",
        "Thread Descent Conflation",
        "MAJOR",
        "Conflating inverse-limit thread existence with original-carrier realization.",
    ),
    AntiSkillDefinition(
        21,
        "ANTI-TORSION-LIFT-RATIONAL-CONFLATION",
        "Torsion Lift Rational Conflation",
        "BLOCKER",
        "Conflating mod-p torsion cochain lifts with rational cocycles (delta^k c != 0).",
    ),
    AntiSkillDefinition(
        22,
        "ANTI-ARCHIVE-SYSTEM-DIVERGENCE",
        "Archive System Divergence",
        "MAJOR",
        "Omission of info.create_system = 3 in ZipInfo, causing Windows/Unix byte divergence.",
    ),
    AntiSkillDefinition(
        23,
        "ANTI-PUBLIC-METRIC-DESYNC",
        "Public Metric Desync",
        "MAJOR",
        "Drift between collected pytest test counts and public documentation surfaces.",
    ),
    AntiSkillDefinition(
        24,
        "ANTI-PDF-REPRODUCIBILITY-OVERCLAIM",
        "PDF Reproducibility Overclaim",
        "MAJOR",
        "Overclaiming byte-identical PDF builds without hermetic containerization.",
    ),
    AntiSkillDefinition(
        25,
        "ANTI-NOTEBOOK-PATH-ABSOLUTISM",
        "Notebook Path Absolutism",
        "MAJOR",
        "Repo-absolute paths in notebook commands; omission of headless execution in verifiers.",
    ),
    AntiSkillDefinition(
        26,
        "ANTI-GHOST-ARTIFACT-CITATION",
        "Ghost Artifact Citation",
        "MAJOR",
        "Citing excised internal review dossiers (*bulgakov*) as preserved docs.",
    ),
    AntiSkillDefinition(
        27,
        "ANTI-NOTEBOOK-INPROCESS-PYTEST-EXECUTION",
        "Notebook In-Process Pytest Execution",
        "BLOCKER",
        "In-process NotebookClient inside pytest shadowing code.py; decouple to subprocesses.",
    ),
    AntiSkillDefinition(
        28,
        "ANTI-MANIFEST-TREE-TRAVERSAL-STALL",
        "Manifest Tree Traversal Stall",
        "MAJOR",
        "Unpruned rglob into large caches (.lake, .venv); prune in-place via os.walk.",
    ),
    AntiSkillDefinition(
        29,
        "ANTI-ZIP-MEMBER-DUPLICATION",
        "Zip Member Duplication",
        "MAJOR",
        "Appending auxiliary files already in manifest entries, creating duplicate zip entries.",
    ),
    AntiSkillDefinition(
        30,
        "ANTI-UNBOUNDED-REGEX-SUBSTRING-COLLISION",
        "Unbounded Regex Substring Collision",
        "MAJOR",
        "Unbounded regex matching on short claim tags colliding with English words; enforce \\b.",
    ),
    AntiSkillDefinition(
        31,
        "ANTI-RENDERED-PDF-SOURCE-DESYNC",
        "Rendered PDF Source Desync",
        "BLOCKER",
        "Packaged PDF out of sync with current TeX/Markdown (stale date, version, or module names).",
    ),
    AntiSkillDefinition(
        32,
        "ANTI-NONUNIFORM-DUAL-BOX-RELAXATION",
        "Nonuniform Dual Box Relaxation",
        "BLOCKER",
        "In weighted l1 quotients, using ||z||_inf <= max_i w_i instead of |z_i| <= w_i.",
    ),
    AntiSkillDefinition(
        33,
        "ANTI-INSTANCE-CERTIFICATE-UNIVERSALITY-INFLATION",
        "Instance Certificate Universality Inflation",
        "MAJOR",
        "Claiming instance certificates prove universal duality, or omitting rational scope (Q).",
    ),
    AntiSkillDefinition(
        34,
        "ANTI-SURROGATE-NORM-MISLABELING",
        "Surrogate Norm Mislabeling",
        "MAJOR",
        "Conflating objective metric evaluation of surrogate repair with surrogate's own norm.",
    ),
    AntiSkillDefinition(
        35,
        "ANTI-CHECKSUM-SCHEME-DOC-DESYNC",
        "Checksum Scheme Doc Desync",
        "MAJOR",
        "Package documentation contradicting actual release checksum schema.",
    ),
    AntiSkillDefinition(
        36,
        "ANTI-CERTIFICATE-VERIFIER-FLOAT-LEAK",
        "Certificate Verifier Float Leak",
        "BLOCKER",
        "Verifiers running boundary arithmetic without validating exact rational scalars/shapes.",
    ),
    AntiSkillDefinition(
        37,
        "ANTI-FORGED-DIAGNOSTIC-ENUM-TRUST",
        "Forged Diagnostic Enum Trust",
        "BLOCKER",
        "Dispatchers trusting diagnostic enums without checking certificate consistency against inputs.",
    ),
    AntiSkillDefinition(
        38,
        "ANTI-MUTABLE-CERTIFICATE-PAYLOAD",
        "Mutable Certificate Payload",
        "MAJOR",
        "Frozen certificates exposing mutable matrices; defensively freeze into ImmutableMatrix.",
    ),
    AntiSkillDefinition(
        39,
        "ANTI-SHAPE-FLATTENING-VECTOR-CONVERSION",
        "Shape Flattening Vector Conversion",
        "MAJOR",
        "Conversions flattening 2D matrices into vectors or collapsing (0, 2) -> (0, 0).",
    ),
    AntiSkillDefinition(
        40,
        "ANTI-DISCONNECTED-REGIME-RECORD-SOUNDNESS",
        "Disconnected Regime Record Soundness",
        "MAJOR",
        "Conflating execution records with epistemic regime soundness without regime embeddings.",
    ),
    AntiSkillDefinition(
        41,
        "ANTI-ARCHIVE-ROOT-CHECKSUM-OMISSION",
        "Archive Root Checksum Omission",
        "MAJOR",
        "README checksum commands failing post-extraction due to missing manifests or conflated schemas.",
    ),
    AntiSkillDefinition(
        42,
        "ANTI-MEMBERSHIP-CERTIFICATE-DOMAIN-BYPASS",
        "Membership Certificate Domain Bypass",
        "BLOCKER",
        "Membership verifiers skipping rational domain (Q) checks, letting floats certify exactness.",
    ),
    AntiSkillDefinition(
        43,
        "ANTI-UNVALIDATED-COMPAT-AUTHORIZATION-GATE",
        "Unvalidated Compat Authorization Gate",
        "BLOCKER",
        "Authorization APIs bypassing .verify() or accepting truthy non-booleans in HaltGuards.",
    ),
    AntiSkillDefinition(
        44,
        "ANTI-UNBOUND-CANDIDATE-IDENTITY-EVIDENCE",
        "Unbound Candidate Identity Evidence",
        "MAJOR",
        "Guards falling back to counts without matching candidate IDs, or permitting zero counts.",
    ),
    AntiSkillDefinition(
        45,
        "ANTI-CIRCULAR-REEXPORT-IMPORT-ORDER-DEPENDENCE",
        "Circular Reexport Import Order Dependence",
        "MAJOR",
        "Circular re-exports swallowed by ImportError; use lazy __getattr__ or direct exports.",
    ),
    AntiSkillDefinition(
        46,
        "ANTI-CATEGORICAL-NO-MAP-FALLACY",
        "Categorical No-Map Fallacy",
        "BLOCKER",
        "Conflating coproduct disjointness with absence of natural transformations; restrictions are policy.",
    ),
    AntiSkillDefinition(
        47,
        "ANTI-ARCHIVE-POST-EXTRACTION-VERIFIER-DESYNC",
        "Archive Post-Extraction Verifier Desync",
        "MAJOR",
        "Packaging verifiers requiring omitted files; extraction must yield a self-verifiable deposit.",
    ),
    AntiSkillDefinition(
        48,
        "ANTI-PROBLEM-UNBOUND-TERMINAL-ROUTING",
        "Problem Unbound Terminal Routing",
        "BLOCKER",
        "Dispatchers accepting ExactRepair on certificates alone without problem-bound verification (x + d_0 f = 0).",
    ),
    AntiSkillDefinition(
        49,
        "ANTI-EMPTY-MATRIX-FABRICATED-ZERO-VECTOR",
        "Empty Matrix Fabricated Zero Vector",
        "BLOCKER",
        "Converting empty matrices with >1 rows (Matrix.zeros(2, 0)) into zero vectors instead of raising ValueError.",
    ),
    AntiSkillDefinition(
        50,
        "ANTI-NUMPY-DATACLASS-EQUALITY",
        "NumPy Dataclass Equality",
        "BLOCKER",
        "Dataclasses with ndarray fields using default equality, causing truth-value crashes; use np.array_equal.",
    ),
    AntiSkillDefinition(
        51,
        "ANTI-SPAN-CARRIER-ESCAPE",
        "Span Carrier Escape",
        "BLOCKER",
        "Spans with out-of-bounds indices silently truncating elements; validate indices against carriers.",
    ),
    AntiSkillDefinition(
        52,
        "ANTI-VACUOUS-GROUPOID-VALIDATION",
        "Vacuous Groupoid Validation",
        "BLOCKER",
        "Groupoid validation returning True on empty tables; verify composition, identity, and inverse axioms.",
    ),
    AntiSkillDefinition(
        53,
        "ANTI-DEPOSIT-FILE-DIR-CASE-COLLISION",
        "Deposit File Directory Case Collision",
        "BLOCKER",
        "Deposit validators missing file/directory collisions or case-folding conflicts across filesystems.",
    ),
    AntiSkillDefinition(
        54,
        "ANTI-PDF-LOCAL-LINK-LEAK",
        "PDF Local Link Leak",
        "BLOCKER",
        "Intra-manuscript cross-references pointing to local Markdown files inside compiled PDFs; must use \\hyperref[#anchor].",
    ),
    AntiSkillDefinition(
        55,
        "ANTI-UNPINNED-BUILD-TOOLCHAIN",
        "Unpinned Build Toolchain",
        "MAJOR",
        "Documenting verification commands citing 'recorded toolchain' without pinning versions in README or pyproject.toml.",
    ),
    AntiSkillDefinition(
        56,
        "ANTI-RIGID-TEX-DIFF-FAILURE",
        "Rigid TeX Diff Failure",
        "MAJOR",
        "Deposit verifiers requiring byte-exact character equality on pandoc-generated TeX across Pandoc versions.",
    ),
    AntiSkillDefinition(
        57,
        "ANTI-ZENODO-SINGLE-LICENSE-MISMATCH",
        "Zenodo Single License Mismatch",
        "MAJOR",
        "Declaring a single license in zenodo_metadata.json when the deposit separates text (CC BY 4.0) and code.",
    ),
    AntiSkillDefinition(
        58,
        "ANTI-UNRESERVED-DOI-DEPOSIT",
        "Unreserved DOI Deposit",
        "MAJOR",
        "Releasing deposit artifacts with 'DOI pending' placeholders instead of executing Zenodo pre-reservation protocol.",
    ),
    AntiSkillDefinition(
        59,
        "ANTI-PDF-LAYOUT-OVERFLOW-CLIPPING",
        "PDF Layout Overflow Clipping",
        "BLOCKER",
        "Overfull \\hbox warnings during TeX compilation or wide math displays exceeding page margins.",
    ),
    AntiSkillDefinition(
        60,
        "ANTI-TRIVIAL-SOLVER-DEPOSIT",
        "Trivial Solver Deposit",
        "BLOCKER",
        "Depositing mathematical solvers that return trivial constant results without exact mathematical checking.",
    ),
    AntiSkillDefinition(
        61,
        "ANTI-QUOTIENT-DESCENT-SUBSTITUTION",
        "Quotient Descent Substitution",
        "BLOCKER",
        "Evaluating progress against raw cochain norms instead of exact quotient potential Phi_1 = ||[h]||_Q1.",
    ),
    AntiSkillDefinition(
        62,
        "ANTI-UNCOMMITTED-OUTCOME-PAYLOAD",
        "Uncommitted Outcome Payload",
        "BLOCKER",
        "Cryptographic commitment tapes omitting canonical RFC 8785 JSON representation of step outcome payload.",
    ),
    AntiSkillDefinition(
        63,
        "ANTI-LEDGER-DECLARATION-AS-ENFORCEMENT",
        "Ledger Declaration As Enforcement",
        "BLOCKER",
        "Upgrading protocol definitions or rule lists to 'Finite theorem' in claim ledgers without executable checkers.",
    ),
    AntiSkillDefinition(
        64,
        "ANTI-BLANKET-MYPY-IMPORT-IGNORE",
        "Blanket Mypy Import Ignore",
        "BLOCKER",
        "Configuring global ignore_missing_imports = true under [tool.mypy] in pyproject.toml.",
    ),
    AntiSkillDefinition(
        65,
        "ANTI-MD034-BARE-URL-SUPPRESSION",
        "MD034 Bare URL Suppression",
        "BLOCKER",
        "Permitting bare unformatted URLs in Markdown documents or disabling/ignoring markdownlint rule MD034.",
    ),
    AntiSkillDefinition(
        66,
        "ANTI-NOTEBOOK-OUTPUT-DRIFT",
        "Notebook Output Drift",
        "BLOCKER",
        "Depositing companion Jupyter notebooks whose code cell outputs drift upon re-execution.",
    ),
    AntiSkillDefinition(
        67,
        "ANTI-DEPOSIT-VERIFIER-FAIL-OPEN",
        "Deposit Verifier Fail Open",
        "BLOCKER",
        "Deposit verification scripts accepting unmanifested files in deposit root or failing two-way sweep.",
    ),
    AntiSkillDefinition(
        68,
        "ANTI-STALE-ARCHIVE-DESYNC",
        "Stale Archive Desync",
        "BLOCKER",
        "Depositing or checking in a release ZIP archive whose member digests diverge from manifest-bound tree.",
    ),
    AntiSkillDefinition(
        69,
        "ANTI-LAKE-OFFLINE-NETWORK-CLONE",
        "Lake Offline Network Clone",
        "BLOCKER",
        "Lean Lake build configurations declaring external network git dependencies attempting live clones.",
    ),
    AntiSkillDefinition(
        70,
        "ANTI-POST-AUDIT-MUTATION-RACE",
        "Post-Audit Mutation Race",
        "BLOCKER",
        "Emitting audit or snapshot publication receipts based on pre-mutation collector passes.",
    ),
    AntiSkillDefinition(
        71,
        "ANTI-INCOMPLETE-STATE-DIGEST-OVERCLAIM",
        "Incomplete State Digest Overclaim",
        "MAJOR",
        "Promoting an event-history or partial state digest to an assertion of full host state commitment.",
    ),
    AntiSkillDefinition(
        72,
        "ANTI-NORMALIZED-TAIL-AS-RAW-CUSTODY",
        "Normalized Tail As Raw Custody",
        "MAJOR",
        "Conflating normalized append-only ledger receipts with exact byte-for-byte physical file custody.",
    ),
    AntiSkillDefinition(
        73,
        "ANTI-WIRE-INPUT-DOMAIN-CONFLATION",
        "Wire Input Domain Conflation",
        "MAJOR",
        "Conflating internal solver arithmetic capabilities with restricted transport wire input specifications.",
    ),
    AntiSkillDefinition(
        74,
        "ANTI-DUAL-OBJECTIVE-EQUALITY-WITHOUT-FEASIBILITY",
        "Dual Objective Equality Without Feasibility",
        "BLOCKER",
        "Declaring optimality from numerical equality of primal value and dual dot product without verifying feasibility.",
    ),
    AntiSkillDefinition(
        75,
        "ANTI-BROKEN-LAUNCHER-SCRIPT",
        "Broken Launcher Script",
        "BLOCKER",
        "Packaging companion launcher scripts that reference nonexistent notebook filenames or broken targets.",
    ),
    AntiSkillDefinition(
        76,
        "ANTI-STORED-OUTPUT-AS-EXECUTION-EVIDENCE",
        "Stored Output As Execution Evidence",
        "BLOCKER",
        "Mislabeling passive structural checks of existing notebook JSON cell outputs as active execution evidence.",
    ),
    AntiSkillDefinition(
        77,
        "ANTI-FIGURE-GENERATION-EXECUTION-OMISSION",
        "Figure Generation Execution Omission",
        "BLOCKER",
        "Omitting code/generate_figures.py execution from review pipelines, or demoting figure script crashes to warnings.",
    ),
    AntiSkillDefinition(
        78,
        "ANTI-SUBPROCESS-RUN-WITHOUT-EXPLICIT-CHECK",
        "Subprocess Run Without Explicit Check",
        "BLOCKER",
        "Invocations of subprocess.run(...) omitting explicit check argument (check=False or check=True).",
    ),
    AntiSkillDefinition(
        79,
        "ANTI-SINGLE-SHOT-REVIEW-RUNNER",
        "Single Shot Review Runner",
        "BLOCKER",
        "Implementing paper review swarms as non-looping single-shot passes without bounded self-healing iterations.",
    ),
    AntiSkillDefinition(
        80,
        "ANTI-CFF-SCHEMA-VIOLATION",
        "CFF Schema Violation",
        "MAJOR",
        "Declaring CITATION.cff compliant based on file existence alone without validating top-level type against CFF 1.2.0 schema (software or dataset only).",
    ),
    AntiSkillDefinition(
        81,
        "ANTI-ZERO-DIM-BOUNDARY-REJECTION",
        "Zero Dim Boundary Rejection",
        "MAJOR",
        "Linear algebra functions rejecting valid zero-dimensional domains or codomains; gauss_jordan_solve fails on 0xn matrices.",
    ),
    AntiSkillDefinition(
        82,
        "ANTI-MUTABLE-FROZEN-DATACLASS-FIELD",
        "Mutable Frozen Dataclass Field",
        "MAJOR",
        "Storing mutable SymPy Matrix objects inside frozen=True dataclasses; use ImmutableMatrix to prevent element-wise post-construction mutation.",
    ),
    AntiSkillDefinition(
        83,
        "ANTI-MISSING-MECHANISM-INVENTORY",
        "Missing Mechanism Inventory",
        "MAJOR",
        "Preprints lacking an explicit Compliance 5b ## Mechanism inventory section between Abstract and Section 1.",
    ),
    AntiSkillDefinition(
        84,
        "ANTI-FIREWALL-GLOBAL-NO-MAP-OVERSTATEMENT",
        "Firewall Global No-Map Overstatement",
        "MAJOR",
        "Docstrings or prose describing object-level firewall non-implications as global non-existence of maps or natural transformations.",
    ),
    AntiSkillDefinition(
        85,
        "ANTI-PASSIVE-STAGE-6-PACKAGING-STUB",
        "Passive Stage 6 Packaging Stub",
        "BLOCKER",
        "Implementing Stage 6 as a passive gate without actively executing the deterministic packaging, manifest synchronization, and release ZIP bundling.",
    ),
    AntiSkillDefinition(
        86,
        "ANTI-DEPENDENCY-TREE-LEAN-POLLUTION",
        "Dependency Tree Lean Pollution",
        "BLOCKER",
        "Lean AST and red-team scanners performing unpruned recursive file traversals into build caches and vendored package directories (.lake/packages/).",
    ),
    AntiSkillDefinition(
        87,
        "ANTI-MD004-ASTERISK-LIST-STYLE",
        "MD004 Asterisk List Style or Suppression",
        "BLOCKER",
        "Permitting asterisk unordered list items in Markdown documents violating MD004 (expected dash '-') or disabling/ignoring markdownlint rule MD004.",
    ),
)


_BY_ID: Dict[str, AntiSkillDefinition] = {item.id: item for item in ACTIVE_ANTI_SKILLS}
_BY_NUMBER: Dict[int, AntiSkillDefinition] = {item.number: item for item in ACTIVE_ANTI_SKILLS}


def get_anti_skill_by_id(skill_id: str) -> Optional[AntiSkillDefinition]:
    """Look up an anti-skill by its alphanumeric identifier."""
    return _BY_ID.get(skill_id)


def get_anti_skill_by_number(number: int) -> Optional[AntiSkillDefinition]:
    """Look up an anti-skill by its 1-indexed number."""
    return _BY_NUMBER.get(number)


def total_anti_skills_count() -> int:
    """Return the total number of registered anti-skills."""
    return len(ACTIVE_ANTI_SKILLS)
