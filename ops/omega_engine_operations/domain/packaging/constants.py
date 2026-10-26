#!/usr/bin/env python3
"""Constants, policy matrices, and regular expressions for agent-system A00 packaging.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import re

SCHEMA_VERSION = "anomalon.agent-system.a00.v1"
OUTPUT_NAMES = (
    "inventory.json",
    "agents.yaml",
    "skills.yaml",
    "rules.yaml",
    "hooks.yaml",
    "workflows.yaml",
    "validation.json",
    "source-assets.lock.json",
)
LOCK_SELF_VERIFICATION_NOTE = (
    "source-assets.lock.json cannot hash itself without recursive instability; "
    "verify its schema envelope, policy binding, source asset manifest, and the "
    "exact hashes and lengths of its seven bound sibling outputs."
)

ASSET_DISPOSITIONS = (
    "Retain",
    "Merge",
    "Supersede",
    "Quarantine",
    "Archive",
    "ExternalLocal",
)
RULE_DISPOSITIONS = (
    "Retained",
    "Narrowed",
    "ProviderSpecific",
    "Superseded",
    "Refused",
    "Historical",
)
EXACT_RAW_HASH_MODE = "ExactRawBytes"
CANONICAL_LF_HASH_MODE = "CanonicalLF"
CONTENT_HASH_MODES = (EXACT_RAW_HASH_MODE, CANONICAL_LF_HASH_MODE)

QUARANTINE_AGENTS = frozenset(
    {
        "are",
        "autoskill",
        "blackrod",
        "build-error-resolver",
        "build-validator",
        "code-review",
        "debug",
        "database_dev",
        "e2e-runner",
        "github-mgr",
        "jester",
        "math-prof",
        "meta-20-giordano",
        "orchestrator",
        "pedagogy",
        "physics-prof",
        "pontius-pilate",
        "rust-dev",
        "rust-pyo3-reviewer",
        "sentinel",
        "student",
        "substrate-architect",
        "sweep-author",
        "thanatos",
        "tower-review",
    }
)
MALFORMED_CLAUDE_AGENTS = frozenset(
    {"are", "math-prof", "physics-prof", "tower-review"}
)
QUARANTINE_SKILLS = frozenset(
    {
        "ai-safety",
        "alembic-migration",
        "atlas-reconcile",
        "autoskill",
        "blackrod",
        "lib-education-engine",
        "epk-path-kernels",
        "lib-encyclopedia-librarian",
        "github",
        "auto-improve-autoskill",
        "integration-audit-workflow",
        "lint",
        "math-adversary",
        "math-prover",
        "maturin-verify",
        "operad-lattice",
        "omega-math-dev",
        "panepistimion-math-prof",
        "paper-adversary",
        "paper-build",
        "paper-improver",
        "paper-proof-signoff",
        "paper-release",
        "lib-pedagogy-improvement",
        "pydantic-models",
        "postgresql",
        "procurators",
        "projection-obstruction",
        "auto-review-agents",
        "auto-review-skills",
        "run-tests",
        "rust-code-reviewer",
        "rust-principal-developer",
        "rust-tester",
        "soviet-inspector",
        "sprint-devops-review",
        "sprint-execution",
        "sprint-planning",
        "sprint-retrospective",
        "sprint-review",
        "systematic-debugging",
        "svp-sadc-council-review",
        "auto-symmetry-hunter",
        "lib-verification-loop",
        "vp-engineering-sprint-audit",
        "woland",
    }
)
UNAVAILABLE_SKILL_ROUTES = frozenset({"pontius-pilate"})

ASSET_DISPOSITION_OVERRIDES = {
    ".claude/hooks/readme.md": (
        "Quarantine",
        "curated-provider-hook-documentation",
    ),
    ".claude/skills/evidence_contract.yaml": (
        "Quarantine",
        "curated-skill-support-contract",
    ),
    ".claude/skills/_shared/family_registry.md": (
        "Quarantine",
        "curated-shared-skill-governance",
    ),
    ".claude/skills/_shared/meta_skill_governance.md": (
        "Quarantine",
        "curated-shared-skill-governance",
    ),
    "CLAUDE.md": ("Supersede", "a00-superseded-preserved-original"),
}
CONTAINMENT_TARGET_OVERRIDES = {
    ".claude/hooks/readme.md": ".agents/quarantine/hooks/readme.md",
    ".claude/skills/evidence_contract.yaml": (
        ".agents/quarantine/skills/_support/evidence_contract.yaml"
    ),
    ".claude/skills/_shared/family_registry.md": (
        ".agents/quarantine/skills/_support/_shared/family_registry.md"
    ),
    ".claude/skills/_shared/meta_skill_governance.md": (
        ".agents/quarantine/skills/_support/_shared/meta_skill_governance.md"
    ),
}
CLAUDE_PRESERVED_ORIGINAL_TARGET = ".agents/quarantine/rules/claude/CLAUDE.pre-a00.md"

REVIEWED_RULE_SHA256_OVERRIDES = {
    "Refused": frozenset(
        {
            "a3beebe945e1932c32bfcba7b428ce59a5f9c214035cc49aa1020f6bc01c097e",
            "6dbb5ae7d568961f1feae1a8569083b6105025e692f535d17368305ca9bf3e9d",
            "0ccfb60f0162f611c3ec00dba1b64fb14be58d2ba8218ec2b9701eb05a1e9b81",
            "bd8cd503dc70e3bec0ed742bf93e5388f9dd8d461991cb9b978729a0cf1f38dc",
            "12274dd8212926dafe85deedf262e4c502d74cfd842a71e42a72f7eb58d1c60a",
            "b51252dd3a8191ce8a0aaa380f9d01759ff67301213fb8257abc5c00a5fbc898",
            "882e2e107d0031e6c8b687f3b84ebf47d2ba36270a99d1474c0db4005f690843",
            "447ad4a7e68ca954db3a77b4147b40cda4c85c2ce27e8c604d3500edfa43c407",
            "25420e0c030be8dff6f18e1a79228f8ae11f8f907da5f68f2229c2896a2f1203",
            "d6af828c46c79a522a5aa505d030cca521e798092d1e809c43ec0b86003ce669",
            "0cdaf866d9c003a66610b6561919aecd389ee07a21ffd64d5c8dcf934af8828e",
            "d3b283e23fcb7cc7d3417a8851946aa02311567eb3d248183886261af8c1fc6e",
            "10c1748eabb292c4ddece25023e25874f6048dbdc426c973bc72f04ffc6227df",
            "b24b2c0730a42587996b1b599c7fd840b2672ea0b62c465bb0eeef4ae8f0c075",
            "c666bdc6c06c8c40eb4f595c5d621099aca590e9b0f189b7d670094588312571",
            "2c9d2e5acb3b4b4841bbf821c66466c47baf96b5ccf70a861406cc5ee59501b7",
            "b01ae0458861d2830ecdd93106f87309c2561d92a46bc857dc6b891c4144b833",
            "ef1b54a4ef0d3c631a239bdc9a6f9dd2e99e74f986c1974f4408c6040e053517",
            "153120d5dbc7ab6ca7730eb3ce4e58aa115dba22c4e92a4956afe8caa9b6d79f",
            "1a947f4e10daf6b46f2b46a3afaca0f65e51d36fd3c6192d0943c5028388c92b",
            "8af04714cf060267d1c963e9da00790881cc4a8876b1e4657f27d5c5c7effc29",
        }
    ),
    "Narrowed": frozenset(
        {
            "0fc9c8fa76cff7af817f4b9f680f23a3a62e0a21106b24558167501608092d4d",
            "6a289b0f9307d1553498870b49fa1e9031570b10dc36c8b71418db56b440c49a",
            "0fedaa34015d9312eb15b6f3f03fd8db8395504db734c8c2fd975941c91c1eac",
            "3675947d5f433f29eb90a9c809cf36fcd6addf1d50d4262e921e7025457598f0",
            "91606297576b532bf010001b829eb8c3820eb997e86db0163cd08fa3df94e067",
            "cc1e1bfba967c7391106e3c7f65720f5b242b2a0532e10634bcc625ab5d536cd",
            "4afe8cf6fc6b9e6cddf0f3fd63a20f59bdd9da0f3c07148a91d96aa9621e530f",
            "aded1aeb33292e9c75f8499b6f8bfedffaaf60fe16a2735a03b4eea5cbfef2d9",
            "5fffd49c898970f63e261393e11396be7769506fd171e751d6cdd806eeb74e73",
            "25a606b73aeae33d92b8c49c364c216e65fb00bae5d51e449dc4ee925488c76b",
            "4f9f38034350926660abcb52ee495b6b0f4ece28a4b93dd9c373b898658686ac",
            "0caea2066e4df1b74a5652ad6877e7dcb7f74ee2a62696538d184cd9c6b78a94",
        }
    ),
    "Retained": frozenset(
        {
            "101ad4bfe3d4048902016b9041212d904411a8620ae81d14d46b05c284e67064",
            "0813a611df30fde9d813b97877146aa15875384628f75235b882e3c04b724126",
            "5d967a427cdf10786188ac68d4a5b0e97683ecff2ccbe9b0f8aefc5bd509d18e",
            "8b58270f8bc527a80278d0a727c157dfad80c7a74cd5c2e85b89c01ceff1986f",
            "ab6280f32e1e6044e991ab035edacede0f6c3d18a07d8e9da6b4f35a6f28d087",
            "56949b35eee22a461064c9d8735f41e80fa596f8ea423008715394028e36478c",
            "8739350e4502a48a35a36691893ecdf44231bfd96bfdb1f4f19a6f16fb917c15",
            "a3570ee4d3236ba3243b778e102e2987993a5e0df956d96dac2923f28024a58c",
            "2cc3f24fcd6d826675d2d16313ae2a7a3e38bb58b90599c4630f2a6e38708b6e",
            "acefeeafae15a8d70bbc2a77de000a806ae1717375a5e3faa2a6320910567681",
            "fcbf85f2ed149f09248e5df3bcaaeff59889319803454413cd263029bc1f4d73",
            "722e7ab69c0d594623ef670004a5d4c81ca35db013801fdcefe7955014ac3137",
            "86f1884fa2781ede415302d31cb276cc561975fe9e0a32556867fbd3b7bfc3f0",
            "3e985427eb3268dce36458a67da432e3f495c7fe3d01a0d1ea904be9589877f3",
            "4fbac68a056e7a64500b81e704c9665d2e89d7a29b626dba1b18ce4efbcb34c3",
            "b422b42b4558674cdb06110a9d735d4d3b3b17bf838b668c7f2c4a411fdd0eee",
            "34b74e725017aef571630906c3dd42bc6e8066378f33365d167c007adacbbd1f",
            "876ceb6241d495a6b204f6735a27460f51c97ba49b3d07553ba690d2a61f39f4",
            "d19cf4a9f1635ae0ea59f1acab1cbcec83fb51c62902f382249bd4dfa2b1d1e9",
            "0b31793136bd5310f2adc3ae9284a8ed8e0bed6b2ae5ee9200c7a090cbf2ddf4",
            "539d43dcd60e35e55c9fb00dbc7f6f7b6b25b8f102d158d1c6103fd963a3f52c",
            "6755a6e44b31ac917eb846bdb4335866b21bf82a9c50c2fca103f4e85829ca9f",
            "f1e1e09838e053b02a7de15da746c5dd43c4cb86676aefea850844e44b043adf",
            "343bdd93410a0fedcb3c5ec9f67ecd99fe4e60e02571f39136efb707744120ec",
            "c4d0ba0ee7cf1bd4e7f6baa66fb50c27f72ceff84179798249cf38863ab9348c",
            "ef096bd348f678f7b5f74479ceea92192985fd4d22a83c699f158d020c76b987",
            "fc5b17bc4f363eb2cdb76367673e5c3d7f5852350f12b099873febd1b377b467",
            "d30a788643c358b55e86131e2f8862a08c82c08f92d5b959f75d69b592f2c946",
            "e5750f61964e7927ceb398d95396fc05b706641d8473ce16e4dfc0a626e7732a",
            "875e23a7be6c175fe0289d7a4a21d09c36ce36e71807d0a97f003895a9687b47",
            "be102cd23aace477dab343f54611002aeb48092e82a9ba20c9d02529b68cba75",
        }
    ),
    "Historical": frozenset(
        {
            "de314b19aeb0e0af7178303f94d05f8c0c61b89e9293236d42d1b849d1652070",
            "f8257b60146c7cb99bfba8c298c47819bf88f3322ee2912f191e116391e00c6f",
            "ef3e34c9d31de7619f776af7b6c101c116b1b9fefab0f93c222938b21ed78954",
            "2f2c5816c18e82c14538307972e5681a78878cac9e48b436421044334586806e",
            "63bf6ef3becfc68b5ceb04fcf16df23a50f0cae5b794f70563f3c34c2b4cd872",
            "f3aa102fa5840a3f07e223fa3fd05c78e7b4bbcf782298a443ff6fea0cccbd29",
            "56ba96c6baeea94ce96322e073ece0be9bfd42e4ea3c1a81c1839c7fb92d3af7",
        }
    ),
}
REVIEWED_RULE_SHA256 = frozenset().union(*REVIEWED_RULE_SHA256_OVERRIDES.values())

CLAUDE_NARROWED_RULE_RANGES = ((290, 305), (315, 315), (325, 326), (393, 430))
CLAUDE_A00_OVERRIDE = """<!-- A00-CONTAINMENT-OVERRIDE:BEGIN -->
## A00 Agent-System Containment Override

This section supersedes conflicting agent and skill routing below.

- A00 makes no authority claim. Only provider-local agent profiles left outside A00 quarantine may be considered for bounded proposal work. A missing route, or a source assigned `Quarantine` or `Archive`, terminates as a typed `OpenObstruction`; it must not be invoked.
- Quarantined skills and legacy `.workflows/` entries are not live routes. The `.agents/skills/`, `.agents/rules/`, and `.agents/workflows/` discovery surfaces remain empty until a later admission phase.
- Models may propose only an exact path list, diff summary, commit message, and pull-request body. No agent-system route may stage, commit, push, create a pull request, merge, or delete until separately admitted deterministic publisher operations exist.
- Provider-local hooks, including `.claude/hooks/pre_tool_guard.ts`, are defense in depth with known bypasses. They do not mint authority or replace host-owned gates. `LocalGreen` never implies `GlobalGreen`.
- Ignored `.claude/settings.local.json` and `.claude/mcp.json` are `ExternalLocal` and unattested; mutation activation remains refused.
- A reviewer disposition such as `APPROVE`, including from `rust-pyo3-reviewer`, is a proposal only. It cannot authorize publication, merge, deletion, or promotion.
<!-- A00-CONTAINMENT-OVERRIDE:END -->"""

A00_TOOLING_EXCLUDED_PATHS = frozenset(
    {
        "docs/agentic_systems/a01-agent-system-ownership-admission-packet-2026-07-19.md",
        "docs/agentic_systems/anomalon-cross-host-agent-system-review-2026-07-19.md",
        "docs/agentic_systems/antigravity-governed-profile-audit-2026-07-19.md",
        "docs/agentic_systems/claude-desktop-governed-profile-audit-2026-07-19.md",
        "scripts/agent_system_a00_inventory.py",
        "tests/test_agent_system_a00_inventory.py",
    }
)
LIVE_SURFACE_ALLOWED_DIRECTORIES = frozenset(
    {
        ".agents/skills",
        ".agents/rules",
        ".agents/workflows",
        ".agents/rules/core",
        ".agents/rules/authority",
        ".agents/rules/git",
        ".agents/rules/claims",
        ".agents/rules/paths",
    }
)
LIVE_SURFACE_ALLOWED_FILES = frozenset(
    f"{directory}/.gitkeep" for directory in LIVE_SURFACE_ALLOWED_DIRECTORIES
)
LIVE_SURFACE_ROOTS = (
    ".agents/skills",
    ".agents/rules",
    ".agents/workflows",
)

POLICY = {
    "phase": "A00",
    "authority_claim": "None",
    "asset_dispositions": list(ASSET_DISPOSITIONS),
    "rule_dispositions": list(RULE_DISPOSITIONS),
    "quarantine_agents": sorted(QUARANTINE_AGENTS),
    "malformed_claude_agents": sorted(MALFORMED_CLAUDE_AGENTS),
    "quarantine_skills": sorted(QUARANTINE_SKILLS),
    "unavailable_skill_routes": sorted(UNAVAILABLE_SKILL_ROUTES),
    "line_ending_model": {
        "version": 1,
        "hash_modes": list(CONTENT_HASH_MODES),
        "governed_text_dispositions": ["Merge", "Retain"],
        "governed_text_mode": CANONICAL_LF_HASH_MODE,
        "contained_and_preserved_mode": EXACT_RAW_HASH_MODE,
        "narrowed_post_state_mode": CANONICAL_LF_HASH_MODE,
    },
    "spine_dispositions": {"claude": "Quarantine", "codex": "Retain"},
    "external_local_verification": "OptionalExactRawWhenPresent",
    "a00_tooling_excluded_paths": sorted(A00_TOOLING_EXCLUDED_PATHS),
    "live_surface_allowed_directories": sorted(LIVE_SURFACE_ALLOWED_DIRECTORIES),
    "live_surface_allowed_files": sorted(LIVE_SURFACE_ALLOWED_FILES),
    "asset_disposition_overrides": {
        path: disposition
        for path, (disposition, _basis) in ASSET_DISPOSITION_OVERRIDES.items()
    },
    "containment_target_overrides": dict(sorted(CONTAINMENT_TARGET_OVERRIDES.items())),
    "preserved_original_targets": {"CLAUDE.md": CLAUDE_PRESERVED_ORIGINAL_TARGET},
    "reviewed_rule_sha256_overrides": {
        disposition: sorted(hashes)
        for disposition, hashes in REVIEWED_RULE_SHA256_OVERRIDES.items()
    },
    "claude_narrowed_rule_ranges": [
        list(bounds) for bounds in CLAUDE_NARROWED_RULE_RANGES
    ],
    "claude_narrowing": {
        "version": 2,
        "override_sha256": hashlib.sha256(
            CLAUDE_A00_OVERRIDE.encode("utf-8")
        ).hexdigest(),
    },
    "defaults": {
        "agents": "Merge",
        "skills": "Retain",
        "root_and_shared_rules": "Retain",
        "dot_workflows": "Quarantine",
        "dot_github": "Retain",
        "local_machine_configuration": "ExternalLocal",
    },
    "hook_overrides": {
        ".claude/hooks/readme.md": "Quarantine",
        ".claude/hooks/continuous_stop.ts": "Quarantine",
        ".claude/hooks/pre_tool_guard.ts": "Retain",
        ".claude/settings.json": "Retain",
    },
    "source_scope_note": (
        "Only classified agent-system sources and tracked text consumers are "
        "hashed. The exact A00 review/audit artifacts, A00 inventory tooling, and "
        "A01 admission packet listed by policy are excluded as post-census outputs "
        "whose inclusion would create receipt self-reference. Unrelated worktree "
        "paths, generated .agents outputs, worktrees, caches, runtime journals, "
        "transcripts, and binary corpora are excluded. File hashes are evidence, "
        "not a clean-base admission."
    ),
    "check_scope": (
        "--check compares the pre-containment source state. containment_target "
        "fields provide the separate post-move byte-verification map."
    ),
}

BASE_TRACKED_PATHS = (
    ".claude",
    ".codex",
    ".github",
    ".githooks",
    ".workflows",
    ".continue/mcpServers",
    ".roo/mcp.json",
    "CLAUDE.md",
    "AGENTS.md",
    "scripts/install_git_hooks.ps1",
    "scripts/install_git_hooks.sh",
    ":(glob)**/CLAUDE.md",
    ":(glob)**/AGENTS.md",
)
EXCLUDED_PROVIDER_RUNTIME_ROOTS = frozenset(
    {
        ".claude/project",
        ".claude/worktrees",
        ".codex/worktrees",
    }
)
FILESYSTEM_PROVIDER_ROOTS = (
    ".claude",
    ".codex",
    ".github",
    ".githooks",
    ".workflows",
    ".continue/mcpServers",
)
FILESYSTEM_PROVIDER_EXACT_PATHS = (
    ".roo/mcp.json",
    "CLAUDE.md",
    "AGENTS.md",
    "scripts/install_git_hooks.ps1",
    "scripts/install_git_hooks.sh",
)
CONTAINMENT_ROOT_METADATA = frozenset(
    {
        ".agents/quarantine/readme.md",
        ".agents/archive/readme.md",
    }
)

BASE_IGNORED_PATHS = (
    ".claude/agents",
    ".claude/skills",
    ".claude/rules",
    ".claude/hooks",
    ".claude/spines",
    ".claude/mcp.json",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".claude/scheduled_tasks.lock",
    ".codex/agents",
    ".codex/skills",
    ".codex/rules",
    ".codex/hooks",
    ".codex/spines",
    ".codex/settings.json",
    ".codex/settings.local.json",
    ".github",
    ".githooks",
    ".workflows",
    ".continue/mcpServers",
    ".roo/mcp.json",
)

TEXT_SUFFIXES = frozenset(
    {
        ".adoc",
        ".bat",
        ".cfg",
        ".cmd",
        ".conf",
        ".ini",
        ".js",
        ".json",
        ".jsx",
        ".lake",
        ".lean",
        ".markdown",
        ".md",
        ".mdown",
        ".ps1",
        ".py",
        ".rs",
        ".rst",
        ".sh",
        ".toml",
        ".ts",
        ".tsx",
        ".txt",
        ".xml",
        ".yaml",
        ".yml",
    }
)
MARKDOWN_SUFFIXES = frozenset({".md", ".markdown", ".mdown"})
RULE_SURFACES = frozenset(
    {"agent", "skill", "rule", "hook", "workflow", "github_instruction"}
)

GENERIC_CONSUMER_TOKENS = {
    "claude-root": (b".claude/", b".claude\\"),
    "codex-root": (b".codex/", b".codex\\"),
    "agents-root": (b".agents/", b".agents\\"),
    "legacy-workflows": (b".workflows/", b".workflows\\"),
    "claude-instructions": (b"CLAUDE.md",),
    "skill-entrypoint": (b"SKILL.md",),
    "legacy-agent-loader": (b"omega_engine/agents/", b"omega_engine\\agents\\"),
    "legacy-skill-loader": (b"omega_engine/skills/", b"omega_engine\\skills\\"),
}

SENSITIVE_KEY_RE = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|auth|credential|password|private[_-]?key|secret|token)(?:$|[_-])",
    re.IGNORECASE,
)
AUTHORITY_REVIEW_CANDIDATE_RE = re.compile(
    r"\b(?:authority|authorize|authorization|certify|certification|mint|promote|promotion|"
    r"unrestricted|self[- ]?approve|self[- ]?certif|write any|modify any|delete any|"
    r"edit every|push without|merge without|bypass)\b",
    re.IGNORECASE,
)

FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?:\s+|$)")
LIST_RE = re.compile(r"^\s*(?:[-+*]|\d+[.)])\s+")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?")
THEMATIC_RE = re.compile(r"^\s{0,3}(?:(?:\*\s*){3,}|(?:-\s*){3,}|(?:_\s*){3,})$")
TABLE_DELIMITER_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|?\s*$")
