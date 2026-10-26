"""Use case service for intaking OMC DAGs, domain routing, and Woland obstruction farming.

Intakes OMC DAG records from JSONL files, classifies each record across the
four canonical domains (DDC, OEWAS, OEEIS, OEPRMPTCIV), extracts all failure
blockers and surviving invariants, and seals them into canonical Woland run
bundles under _ic/woland/runs/.

AuthorityEffect: None.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from omega_engine_governance.domain.intelligence_community import canonical_intelligence_route
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result
from omega_engine_woland.domain.native import NativeOperationPort
from omega_engine_woland.domain.omc_intake import (
    FarmedObstructionV1,
    FarmedSurvivingSkillV1,
    ObstructionSeverity,
    OmcDagRecordV1,
    OmcDomain,
    OmcHarvestResultV1,
    classify_omc_record,
    farm_obstructions_from_record,
    farm_surviving_skills_from_record,
)
from omega_engine_woland.use_cases.skill_run_persistence import persist_skill_run

_LOCUS = "omega_engine_woland.use_cases.omc_dag_intake"


def _refuse(code: str, message: str) -> Err[Refusal]:
    return Err(Refusal(code=code, message=message, locus=_LOCUS))


class OmcDagIntakeService:
    """Orchestrates ingestion of omc_dags JSONL files, domain classification, and Woland persistence."""

    def intake_line(
        self, raw_line: str, source_file: str, line_no: int
    ) -> Result[OmcDagRecordV1, Refusal]:
        line = raw_line.strip()
        if not line:
            return _refuse("EMPTY_LINE", f"{source_file}:{line_no} is empty")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError as exc:
            return _refuse("INVALID_JSON", f"{source_file}:{line_no}: {exc.msg}")

        if not isinstance(payload, dict):
            return _refuse("INVALID_RECORD_TYPE", f"{source_file}:{line_no}: expected JSON object")

        return self._intake_payload_dict(payload, source_file, line_no)

    def _intake_payload_dict(
        self, payload: dict[str, Any], source_file: str, line_no: int
    ) -> Result[OmcDagRecordV1, Refusal]:
        # Determine record type and record id
        if "audit_id" in payload:
            rec_id = str(payload["audit_id"])
            rec_type = "audit_report"
        elif "pr_number" in payload:
            rec_id = f"omc_pr_{payload['pr_number']}"
            rec_type = "pr_preflight"
        elif "finding_id" in payload:
            rec_id = str(payload["finding_id"])
            rec_type = "audit_finding"
        elif "module" in payload and "subsystem" in payload:
            rec_id = f"omc_{payload['module']}_{payload['subsystem']}"
            rec_type = "subsystem_audit"
        elif "gate_id" in payload or "stage" in payload or "package_name" in payload:
            rec_id = f"review_{payload.get('package_name', Path(source_file).stem)}_{line_no}"
            rec_type = "review_receipt"
        else:
            rec_id = f"omc_record_{Path(source_file).stem}_{line_no}"
            rec_type = "raw"

        target = str(payload.get("target", payload.get("branch", payload.get("module", payload.get("package_name", "")))))
        target_hash = str(payload.get("target_hash", payload.get("head_sha", "")))
        verdict = str(payload.get("verdict", payload.get("status", "UNKNOWN")))

        # Decisive blockers
        raw_blockers = payload.get("decisive_blockers", [])
        if not raw_blockers and payload.get("status") in ("FAIL", "BLOCKED", "NO_GO"):
            raw_blockers = payload.get("errors", []) or payload.get("failures", [])
        blockers = tuple(str(b) for b in raw_blockers) if isinstance(raw_blockers, list) else ()

        # Audited files
        raw_files = payload.get("audited_files", [])
        files = tuple(str(f) for f in raw_files) if isinstance(raw_files, list) else ()

        # Gates & Compliance
        raw_gates = payload.get("natural_science_gates", {})
        gates = dict(raw_gates) if isinstance(raw_gates, dict) else {}

        raw_comp = payload.get("code_compliance", {})
        comp = dict(raw_comp) if isinstance(raw_comp, dict) else {}

        # What survived
        raw_survived = payload.get("what_survived", [])
        survived = tuple(str(s) for s in raw_survived) if isinstance(raw_survived, list) else ()

        dual_witness = str(payload.get("dual_witness_status", "UNKNOWN"))

        rec = OmcDagRecordV1(
            record_id=rec_id,
            source_file=source_file,
            record_type=rec_type,
            raw_payload=payload,
            target=target,
            target_hash=target_hash,
            verdict=verdict,
            decisive_blockers=blockers,
            audited_files=files,
            natural_science_gates=gates,
            code_compliance=comp,
            what_survived=survived,
            dual_witness_status=dual_witness,
            authority_effect="None",
        )
        return Ok(rec)

    def intake_file(self, file_path: Path | str) -> Result[tuple[OmcDagRecordV1, ...], Refusal]:
        path = Path(file_path)
        if not path.is_file():
            return _refuse("FILE_NOT_FOUND", f"OMC DAG file not found: {path}")

        records: list[OmcDagRecordV1] = []
        try:
            content = path.read_text(encoding="utf-8")
        except Exception as exc:
            return _refuse("READ_ERROR", f"Failed to read {path}: {exc}")

        if path.suffix == ".json":
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    res = self._intake_payload_dict(data, source_file=path.name, line_no=1)
                    if res.is_ok:
                        records.append(res.unwrap())
                elif isinstance(data, list):
                    for idx, item in enumerate(data, start=1):
                        if isinstance(item, dict):
                            res = self._intake_payload_dict(item, source_file=path.name, line_no=idx)
                            if res.is_ok:
                                records.append(res.unwrap())
            except Exception:
                pass
            return Ok(tuple(records))

        for idx, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                continue
            res = self.intake_line(line, source_file=path.name, line_no=idx)
            if res.is_err:
                return Err(res.unwrap_err())
            records.append(res.unwrap())

        return Ok(tuple(records))

    def intake_directory(
        self, dir_path: Path | str, pattern: str = "*.jsonl"
    ) -> Result[OmcHarvestResultV1, Refusal]:
        p = Path(dir_path)
        if not p.is_dir():
            return _refuse("DIR_NOT_FOUND", f"Directory not found: {p}")

        files = sorted(p.glob(pattern), key=lambda x: x.name)
        all_records: list[OmcDagRecordV1] = []

        for f in files:
            f_res = self.intake_file(f)
            if f_res.is_err:
                return Err(f_res.unwrap_err())
            all_records.extend(f_res.unwrap())

        return Ok(self.farm_all(all_records))

    def farm_all(self, records: Sequence[OmcDagRecordV1]) -> OmcHarvestResultV1:
        """Classify records and farm obstructions & surviving skills."""
        domain_counts: dict[str, int] = {d.value: 0 for d in OmcDomain}
        all_obstructions: list[FarmedObstructionV1] = []
        all_skills: list[FarmedSurvivingSkillV1] = []

        for rec in records:
            matched_domains = classify_omc_record(rec)
            for d in matched_domains:
                domain_counts[d.value] = domain_counts.get(d.value, 0) + 1

            obstructions = farm_obstructions_from_record(rec)
            all_obstructions.extend(obstructions)

            skills = farm_surviving_skills_from_record(rec)
            all_skills.extend(skills)

        return OmcHarvestResultV1(
            total_records=len(records),
            records_by_domain=domain_counts,
            obstructions=tuple(all_obstructions),
            surviving_skills=tuple(all_skills),
            authority_effect="None",
        )

    def filter_by_domain(
        self, harvest: OmcHarvestResultV1, domain: OmcDomain | str
    ) -> OmcHarvestResultV1:
        """Filter harvest results to a specific domain (DDC, OEWAS, OEEIS, OEPRMPTCIV)."""
        target_domain = OmcDomain(domain) if isinstance(domain, str) else domain
        target_val = target_domain.value

        filtered_obs = tuple(
            obs for obs in harvest.obstructions if target_domain in obs.domains
        )
        filtered_skills = tuple(
            skill for skill in harvest.surviving_skills if target_domain in skill.domains
        )

        domain_counts = {target_val: harvest.records_by_domain.get(target_val, 0)}

        return OmcHarvestResultV1(
            total_records=domain_counts[target_val],
            records_by_domain=domain_counts,
            obstructions=filtered_obs,
            surviving_skills=filtered_skills,
            authority_effect="None",
        )

    def persist_woland_harvest_run(
        self,
        repo_root: Path | str,
        harvest: OmcHarvestResultV1,
        task_key: str | None = None,
        domain_filter: str | None = None,
    ) -> Result[Path, Refusal]:
        """Persist a canonical Woland five-file run bundle capturing the farmed harvest.

        Creates:
          - novella.md: Bulgakovian dialectical review of the farmed entrails
          - ddc.jsonl: Hash-chained tape with DDC alphabet letters (E, R, C, I, Λ, D, M, T)
          - ddc.jsonl: Byte-identical native copy of the DDA tape
          - summary.json: Census of intake records, domain partitions, and candidate anti-skills
          - receipt.json: Bound receipt via persist_skill_run (verdict: OPEN_RESIDUAL)
        """
        root = Path(repo_root)
        now_utc = datetime.now(timezone.utc).isoformat()
        if not task_key:
            ts_slug = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            dom_slug = f"_{domain_filter.lower()}" if domain_filter else ""
            task_key = f"woland_omc_harvest{dom_slug}_{ts_slug}"

        objective = (
            f"Woland Inquest & Obstruction Harvest: Intaking OMC DAGs across "
            f"DDC, OEWAS, OEEIS, OEPRMPTCIV ({harvest.total_records} records, "
            f"{len(harvest.obstructions)} obstructions, {len(harvest.surviving_skills)} surviving skills)"
        )

        # 1. Novella
        novella_md = self._render_harvest_novella(harvest, task_key, now_utc, domain_filter)

        # 2. DDA Actions Tape (using strictly valid DDC letters: E, R, C, I, Λ, D, M, T)
        dda_steps: list[dict[str, Any]] = [
            {
                "letter": "E",
                "phase": "ACT_I_INTAKE_CENSUS",
                "timestamp": now_utc,
                "payload": {
                    "total_records_ingested": harvest.total_records,
                    "target_domains": list(harvest.records_by_domain.keys()),
                },
            },
            {
                "letter": "C",
                "phase": "ACT_II_DOMAIN_PARTITION",
                "timestamp": now_utc,
                "payload": {
                    "domain_distribution": harvest.records_by_domain,
                },
            },
            {
                "letter": "R",
                "phase": "ACT_III_OBSTRUCTION_LOCALIZATION",
                "timestamp": now_utc,
                "payload": {
                    "farmed_obstruction_count": len(harvest.obstructions),
                    "blockers": [
                        {"id": o.obstruction_id, "class": o.failure_class, "anti_skill": o.suggested_anti_skill}
                        for o in harvest.obstructions[:20]
                    ],
                },
            },
            {
                "letter": "I",
                "phase": "ACT_IV_SURVIVING_INVARIANTS",
                "timestamp": now_utc,
                "payload": {
                    "surviving_skills_count": len(harvest.surviving_skills),
                    "top_skills": [
                        {"id": s.skill_id, "name": s.suggested_skill_name}
                        for s in harvest.surviving_skills[:10]
                    ],
                },
            },
            {
                "letter": "Λ",
                "phase": "ACT_V_GAUGE_BREAK_AND_ANTIBODIES",
                "timestamp": now_utc,
                "payload": {
                    "antibody_seeds_generated": len(harvest.obstructions),
                    "highest_severity": "BLOCKER" if any(o.severity == ObstructionSeverity.BLOCKER for o in harvest.obstructions) else "MAJOR",
                },
            },
            {
                "letter": "D",
                "phase": "ACT_VI_DESCENT_REDUCTION",
                "timestamp": now_utc,
                "payload": {
                    "residual_obstructions_open": len(harvest.obstructions),
                },
            },
            {
                "letter": "T",
                "phase": "ACT_VII_TERMINAL_HARVEST_SEAL",
                "timestamp": now_utc,
                "payload": {
                    "verdict": "OPEN_RESIDUAL",
                    "authority_effect": "None",
                    "next_action": "Farm remaining obstructions into candidate skills and antibodies",
                },
            },
        ]

        # 3. Summary
        summary_payload = {
            "schema_version": "omega.woland.omc-harvest-summary.v1",
            "task_key": task_key,
            "intake_timestamp_utc": now_utc,
            "domain_filter": domain_filter or "ALL",
            "total_records": harvest.total_records,
            "records_by_domain": harvest.records_by_domain,
            "total_obstructions": len(harvest.obstructions),
            "total_surviving_skills": len(harvest.surviving_skills),
            "top_obstructions": [obs.to_dict() for obs in harvest.obstructions[:30]],
            "surviving_skills_sample": [s.to_dict() for s in harvest.surviving_skills[:20]],
            "authority_effect": "None",
        }

        # 4. Call persist_skill_run into _intelligence/_woland
        woland_dir = root / canonical_intelligence_route("_intelligence/_woland")
        return persist_skill_run(
            woland_dir,
            task_key=task_key,
            objective=objective,
            verdict="OPEN_RESIDUAL",
            source="woland_omc_dag_intake",
            novella_md=novella_md,
            created_utc=now_utc,
            dda_steps=dda_steps,
            summary=summary_payload,
            native_support=self._native_support,
        )

    def _render_harvest_novella(
        self,
        harvest: OmcHarvestResultV1,
        task_key: str,
        now_utc: str,
        domain_filter: str | None,
    ) -> str:
        lines = [
            "# The Woland Inquest: Ingestion and Obstruction Farming of the OMC Entrails",
            "",
            "> *«Рукописи не горят, но всякий недоказанный нуль сгорает синим пламенем.»*",
            "> — Воланд, Заседание в Квартире № 50 на Садовой",
            "",
            f"- **Run Key:** `{task_key}`",
            f"- **Timestamp UTC:** `{now_utc}`",
            f"- **Domain Filter:** `{domain_filter or 'ALL'}`",
            "- **AuthorityEffect:** `None`",
            "",
            "---",
            "",
            "## Act I. The Gathering at Sadovaya 50",
            "",
            f"In the dim light of Apartment 50 on Sadovaya Street, Woland sat with his chessboard, cane in hand. Beside him, Koroviev sifted through the intake stack of {harvest.total_records} Operad Morphism Calculus (OMC) and Old Man Red Team audit receipts from `_intelligence/omc_dags/`.",
            "",
            "«Messire,» Koroviev bowed with a theatrical grin, twirling his broken pince-nez. «We have gathered the entire entrails of the department. The Old Man has struck without mercy, stripping away every markdown illusion and emitting purely immutable lines of JSONL.»",
            "",
            "Woland glanced at the records. «Good. Markdown is presentation; JSON lines are evidence. Tabulate the four quarters of the estate: DDC, OEWAS, OEEIS, and OEPRMPTCIV.»",
            "",
            "---",
            "",
            "## Act II. The Four Domains Partition",
            "",
            "Koroviev laid out the census:",
            "",
            f"- **DDC (Discrete Deformation Calculus):** `{harvest.records_by_domain.get('DDC', 0)}` records",
            f"- **OEWAS (Omega Engine Workflows, Agents & Skills):** `{harvest.records_by_domain.get('OEWAS', 0)}` records",
            f"- **OEEIS (Omega Engine Epistemic Immune System):** `{harvest.records_by_domain.get('OEEIS', 0)}` records",
            f"- **OEPRMPTCIV (Prompt Civilization):** `{harvest.records_by_domain.get('OEPRMPTCIV', 0)}` records",
            "",
            "«Look closely, Azazello,» Woland murmured. «Where the carrier boundaries hold, the algebra stands firm. Where the dual witness was omitted, the claim collapsed into a mere proposal.»",
            "",
            "---",
            "",
            "## Act III. The Obstruction Cemetery & Farmed Antibodies",
            "",
            f"Across the ingested corpus, Woland's retinue identified **{len(harvest.obstructions)} distinct obstructions** requiring antibody formation:",
            "",
        ]

        if harvest.obstructions:
            for obs in harvest.obstructions[:15]:
                dom_str = ", ".join(d.value for d in obs.domains)
                lines.append(f"- **[{obs.severity.value}] `{obs.obstruction_id}`** ({dom_str}):")
                lines.append(f"  - *Failure Class:* `{obs.failure_class}`")
                lines.append(f"  - *Description:* {obs.description}")
                lines.append(f"  - *Proposed Anti-Skill:* `{obs.suggested_anti_skill}`")
                lines.append(f"  - *Repair Obligation:* {obs.suggested_skill_repair}")
        else:
            lines.append("No active blockers detected in this subset. All audited gates registered clean passes.")

        lines.extend([
            "",
            "---",
            "",
            "## Act IV. The Living Estate: Surviving Invariants",
            "",
            f"Begemot blew on his primus stove and displayed the surviving invariants ({len(harvest.surviving_skills)} records):",
            "",
        ])

        if harvest.surviving_skills:
            for skill in harvest.surviving_skills[:10]:
                dom_str = ", ".join(d.value for d in skill.domains)
                lines.append(f"- **`{skill.skill_id}`** ({dom_str}):")
                lines.append(f"  - *Surviving Pattern:* {skill.surviving_pattern}")
                lines.append(f"  - *Proposed Skill:* `{skill.suggested_skill_name}`")
        else:
            lines.append("No explicit surviving invariant strings were extracted.")

        lines.extend([
            "",
            "---",
            "",
            "## Act V. Terminal Verdict: OPEN_RESIDUAL",
            "",
            "«Until every obstruction is resolved and paired with its dual certificate,» Woland announced, «we declare `OPEN_RESIDUAL`. We shall run these entrails through our Retinue Swarm as many times as necessary, farming every last obstruction into a typed antibody and every surviving proof into an immutable skill.»",
            "",
            "> *«Свежесть бывает только одна — первая, она же и последняя.»*",
            "",
        ])

        return "\n".join(lines)

    def __init__(self, *, native_support: NativeOperationPort) -> None:
        self._native_support = native_support
