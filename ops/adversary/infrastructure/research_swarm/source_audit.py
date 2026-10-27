"""Repository reads and heuristic scanning for the audit squad port."""

import re
from pathlib import Path
from typing import List

from operations.domain.rop.result import Err, Ok, Result
from adversary.domain.research_swarm.models import FindingV1


class SourceAuditSquads:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.files_scanned_count = 0

    def _read_source(self, path: Path, category: str) -> Result[str, FindingV1]:
        try:
            return Ok(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError) as exc:
            return Err(
                FindingV1(
                    category,
                    "BLOCKER",
                    str(path.relative_to(self.repo_root)),
                    None,
                    f"AUDIT_SOURCE_UNREADABLE: {type(exc).__name__}: {exc}",
                    "Restore a readable UTF-8 source file before repeating this audit.",
                )
            )

    def audit_squad_alpha_rust(self) -> List[FindingV1]:
        """Squad alpha: Audits the sovereign Rust crates for exact math and authority gates."""
        findings: List[FindingV1] = []
        crates_dir = self.repo_root / "engine" / "crates_rs"
        if not crates_dir.is_dir():
            return findings

        # Check Authority Gap in the CODA module of core_wdp
        coda_fda_path = crates_dir / "core_wdp" / "src" / "coda" / "layer8_fda.rs"
        if coda_fda_path.is_file():
            self.files_scanned_count += 1
            result = self._read_source(coda_fda_path, "CODA")
            if isinstance(result, Err):
                findings.append(result.error)
            elif "EXTERNAL_GRANT_VERIFIER_UNAVAILABLE" not in result.value:
                findings.append(
                    FindingV1(
                        category="CODA",
                        severity="BLOCKER",
                        target_path=str(coda_fda_path.relative_to(self.repo_root)),
                        line_number=None,
                        description="core_wdp::coda layer8_fda does not enforce EXTERNAL_GRANT_VERIFIER_UNAVAILABLE, risking internal self-authorization.",
                        remediation_advice="Route any external grant verification inside core_wdp::coda to RouteRefused with EXTERNAL_GRANT_VERIFIER_UNAVAILABLE.",
                    )
                )

        # Check core_lggr for bare All-Green variant
        lggr_verdict_path = crates_dir / "core_local_green_global_red_lggr" / "src" / "verdict.rs"
        if lggr_verdict_path.is_file():
            self.files_scanned_count += 1
            result = self._read_source(lggr_verdict_path, "LGGR")
            if isinstance(result, Err):
                findings.append(result.error)
            elif "OracleNeeded" not in result.value:
                findings.append(
                    FindingV1(
                        category="LGGR",
                        severity="BLOCKER",
                        target_path=str(lggr_verdict_path.relative_to(self.repo_root)),
                        line_number=None,
                        description="core_local_green_global_red_lggr missing OracleNeeded variant; may allow uncertified green passes.",
                        remediation_advice="Ensure all-green without adequacy certificate routes to LggrVerdict::OracleNeeded.",
                    )
                )

        # Scan for floating point usage in sovereign math crates
        # CODA and DDC are modules of core_wdp; scan those modules, not the whole crate.
        math_sources = [
            ("core_wdp::coda", Path("core_wdp") / "src" / "coda"),
            ("core_local_green_global_red_lggr", Path("core_local_green_global_red_lggr") / "src"),
            ("core_wdp::ddc", Path("core_wdp") / "src" / "ddc"),
            ("core_homology", Path("core_homology") / "src"),
            ("core_functional", Path("core_functional") / "src"),
        ]

        float_re = re.compile(r"\b(f32|f64)\b")
        for crate_name, source_dir in math_sources:
            crate_src = crates_dir / source_dir
            if not crate_src.is_dir():
                continue
            for rs_file in crate_src.rglob("*.rs"):
                self.files_scanned_count += 1
                result = self._read_source(rs_file, "CODA")
                if isinstance(result, Err):
                    findings.append(result.error)
                    continue
                text = result.value
                for idx, line in enumerate(text.splitlines(), start=1):
                    # Ignore comments and attributes
                    clean_line = line.strip()
                    if (
                        clean_line.startswith("//")
                        or clean_line.startswith("/*")
                        or clean_line.startswith("*")
                    ):
                        continue
                    if float_re.search(clean_line) and "BigRational" not in clean_line:
                        findings.append(
                            FindingV1(
                                category="CODA",
                                severity="MAJOR",
                                target_path=str(rs_file.relative_to(self.repo_root)),
                                line_number=idx,
                                description=f"Floating-point type found in sovereign math crate {crate_name}: '{clean_line}'",
                                remediation_advice="Replace f32/f64 with exact rational num_rational::BigRational over Q.",
                            )
                        )

        return findings

    def audit_squad_beta_python(self) -> List[FindingV1]:
        """Squad beta: Audits Python operations and swarms for Adversary base inheritance and adapter hygiene."""
        findings: List[FindingV1] = []

        # Directories to scan
        py_dirs = [
            self.repo_root / "operations",
            self.repo_root / "adversary",
            self.repo_root / "pfp",
        ]

        # Scan for swarms and adapter bypasses
        swarm_class_re = re.compile(r"class\s+([A-Za-z0-9_]*Swarm[A-Za-z0-9_]*)\b(?:\(([^)]*)\))?:")
        bare_except_re = re.compile(r"^\s*except\s*:")

        for base_dir in py_dirs:
            if not base_dir.is_dir():
                continue
            for py_file in base_dir.rglob("*.py"):
                self.files_scanned_count += 1
                result = self._read_source(py_file, "CLEAN_ARCH")
                if isinstance(result, Err):
                    findings.append(result.error)
                    continue
                text = result.value

                # Check for swarm class inheritance
                for match in swarm_class_re.finditer(text):
                    class_name = match.group(1)
                    base_classes = match.group(2) or ""
                    # Skip base class definition itself
                    if class_name in ("AdversarySwarm", "SwarmRuntimeV1", "BaseSwarm"):
                        continue
                    if (
                        "AdversarySwarm" not in base_classes
                        and "AdversarySwarm" not in base_classes
                        and "BaseResearchSwarm" not in base_classes
                    ):
                        findings.append(
                            FindingV1(
                                category="CLEAN_ARCH",
                                severity="MAJOR",
                                target_path=str(py_file.relative_to(self.repo_root)),
                                line_number=None,
                                description=f"Swarm class '{class_name}' does not inherit from AdversarySwarm (inherits: {base_classes or 'None'}).",
                                remediation_advice="Inherit from AdversarySwarm to guarantee unified CODA/LGGR adapter access.",
                            )
                        )

                # Check for bare excepts (ROP strictness)
                for idx, line in enumerate(text.splitlines(), start=1):
                    if bare_except_re.match(line):
                        findings.append(
                            FindingV1(
                                category="CLEAN_ARCH",
                                severity="MINOR",
                                target_path=str(py_file.relative_to(self.repo_root)),
                                line_number=idx,
                                description=f"Bare except block violating ROP Result monad discipline: '{line.strip()}'",
                                remediation_advice="Specify explicit exception types or return Result.refusal(reason).",
                            )
                        )

        return findings

    def audit_squad_gamma_lean(self) -> List[FindingV1]:
        """Squad gamma: Audits Lean 4 proof kernels for sorry and axiom honesty."""
        findings: List[FindingV1] = []
        lean_dir = self.repo_root / "lean4"
        if not lean_dir.is_dir():
            return findings

        sorry_re = re.compile(r"\bsorry\b")
        axiom_re = re.compile(r"^axiom\s+([A-Za-z0-9_]+)")

        for lean_file in lean_dir.rglob("*.lean"):
            # Skip build artifact caches
            if ".lake" in lean_file.parts:
                continue
            self.files_scanned_count += 1
            result = self._read_source(lean_file, "THREE_ALGOS")
            if isinstance(result, Err):
                findings.append(result.error)
                continue
            text = result.value

            # First strip block comments /- ... -/ to avoid matching docstrings
            clean_code_text = re.sub(r"/-(?:[^-]|-(?!/))*-/", "", text, flags=re.DOTALL)

            for idx, line in enumerate(clean_code_text.splitlines(), start=1):
                clean_line = line.strip()
                if clean_line.startswith("--"):
                    continue
                # Also ignore inline comments -- ...
                if "--" in clean_line:
                    clean_line = clean_line.split("--", 1)[0].strip()

                # Ignore occurrences in prose describing sorry absence
                if re.search(
                    r"\b(sorry-free|0\s*sorry|zero\s*sorry|no\s*sorry)\b", clean_line, re.IGNORECASE
                ):
                    continue

                # Check for sorry in production proof files
                if sorry_re.search(clean_line):
                    findings.append(
                        FindingV1(
                            category="THREE_ALGOS",
                            severity="BLOCKER",
                            target_path=str(lean_file.relative_to(self.repo_root)),
                            line_number=idx,
                            description=f"'sorry' token in Lean 4 proof file: '{clean_line}'",
                            remediation_advice="Complete mechanization without sorry, or mark file as non-authoritative toy.",
                        )
                    )

                # Check for ungrounded custom axioms
                match_ax = axiom_re.match(clean_line)
                if match_ax:
                    ax_name = match_ax.group(1)
                    if ax_name not in ("propext", "Quot.sound"):
                        findings.append(
                            FindingV1(
                                category="THREE_ALGOS",
                                severity="MAJOR",
                                target_path=str(lean_file.relative_to(self.repo_root)),
                                line_number=idx,
                                description=f"Custom axiom declared outside whitelist: '{ax_name}'",
                                remediation_advice="Ground proof strictly in Lean 4 standard axioms {propext, Quot.sound}.",
                            )
                        )

        return findings

    def audit_squad_delta_atlas(self) -> List[FindingV1]:
        """Squad delta: Audits Atlas monographs and contracts for banned nomenclature."""
        findings: List[FindingV1] = []

        # Banned acronym patterns per RULE_CODA_NOMENCLATURE_CANONICAL_001
        banned_patterns = [
            (re.compile(r"\bGTOC\b"), "GTOC is a deprecated predecessor acronym; must use CODA."),
            (
                re.compile(
                    r"Constructive\s+Obstruction\s+and\s+Defect\s+Architecture", re.IGNORECASE
                ),
                "Banned hallucinated expansion of CODA.",
            ),
            (
                re.compile(r"Quantum\s+Enclosure", re.IGNORECASE),
                "Banned expansion of Layer 5; Layer 5 is strictly 'The Continuum' (coda_q).",
            ),
            (
                re.compile(r"Generalized\s+Tie-Loss\s+Aggregation", re.IGNORECASE),
                "Banned hallucinated expansion of GTLA; must be 'General Theory of Layered Authority'.",
            ),
        ]

        atlas_dir = self.repo_root / "atlas" / "coda_atlas"
        if not atlas_dir.is_dir():
            return findings

        for doc_file in atlas_dir.rglob("*.md"):
            self.files_scanned_count += 1
            result = self._read_source(doc_file, "LEXICON")
            if isinstance(result, Err):
                findings.append(result.error)
                continue
            text = result.value

            for pat, reason in banned_patterns:
                for idx, line in enumerate(text.splitlines(), start=1):
                    # Skip historical rule quotes
                    if "BANNED" in line or "STALE_RULE" in line or "prohibited" in line.lower():
                        continue
                    if pat.search(line):
                        findings.append(
                            FindingV1(
                                category="LEXICON",
                                severity="MAJOR",
                                target_path=str(doc_file.relative_to(self.repo_root)),
                                line_number=idx,
                                description=f"Banned nomenclature found: '{line.strip()}' - {reason}",
                                remediation_advice=f"Replace with canonical terminology: {reason}",
                            )
                        )

        return findings
